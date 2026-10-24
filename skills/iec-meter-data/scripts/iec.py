#!/usr/bin/env python3
"""Fetch Israel Electric Corporation smart-meter readings (15-minute intervals) into a local SQLite DB.

Subcommands: login, fetch, import, request-export, verify, status, plans.
Everything except login/fetch/request-export/verify is stdlib-only, so tests run without iec-api installed.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import csv
import email
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from email import policy
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Jerusalem")
UTC = timezone.utc
STEP = timedelta(minutes=15)
KEYCHAIN_SERVICE = "iec-meter"


def data_dir() -> Path:
    if os.environ.get("IEC_DATA_DIR"):
        return Path(os.environ["IEC_DATA_DIR"]).expanduser()
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/iec-meter"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "iec-meter"


def db_path() -> Path:
    return data_dir() / "iec.db"


# ---------------------------------------------------------------- secrets
# macOS Keychain via the `security` CLI. Items created by `security` are readable by it without a
# GUI prompt, which is what lets the launchd job run unattended. Elsewhere: a 0600 file in the data dir.

def _secrets_file() -> Path:
    return data_dir() / "secrets.json"


def secret_get(account: str) -> str | None:
    if shutil.which("security"):
        r = subprocess.run(["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-a", account, "-w"],
                           capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else None
    f = _secrets_file()
    return json.loads(f.read_text()).get(account) if f.exists() else None


def secret_set(account: str, value: str) -> None:
    if shutil.which("security"):
        subprocess.run(["security", "add-generic-password", "-U", "-s", KEYCHAIN_SERVICE, "-a", account, "-w", value],
                       check=True, capture_output=True)
        return
    f = _secrets_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    d = json.loads(f.read_text()) if f.exists() else {}
    d[account] = value
    f.touch(mode=0o600)
    f.write_text(json.dumps(d))


# ---------------------------------------------------------------- db

SCHEMA = """
CREATE TABLE IF NOT EXISTS readings (
  meter      TEXT NOT NULL,           -- '<meter code>-<meter serial>', as IEC prints it
  ts_utc     TEXT NOT NULL,           -- interval START, 'YYYY-MM-DDTHH:MM:SSZ'
  ts_local   TEXT NOT NULL,           -- interval start, Asia/Jerusalem wall clock 'YYYY-MM-DD HH:MM'
  kwh        REAL NOT NULL,           -- consumption in the 15 minutes
  kwh_export REAL NOT NULL DEFAULT 0, -- backstream to the grid (solar), 0 otherwise
  status     INTEGER,                 -- API status code; NULL for CSV rows
  source     TEXT NOT NULL,           -- 'csv' | 'api'
  fetched_at TEXT NOT NULL,
  PRIMARY KEY (meter, ts_utc)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS imports (
  id          INTEGER PRIMARY KEY,
  source      TEXT NOT NULL,
  ref         TEXT NOT NULL,           -- file name or 'api:YYYY-MM-DD'
  first_local TEXT,
  last_local  TEXT,
  rows        INTEGER NOT NULL,
  imported_at TEXT NOT NULL
);

CREATE VIEW IF NOT EXISTS hourly AS
  SELECT meter, substr(ts_local, 1, 13) || ':00' AS hour_local, SUM(kwh) AS kwh, COUNT(*) AS intervals
  FROM readings GROUP BY meter, hour_local;

CREATE VIEW IF NOT EXISTS daily AS
  SELECT meter, substr(ts_local, 1, 10) AS day, SUM(kwh) AS kwh, MAX(kwh) * 4 AS peak_kw, COUNT(*) AS intervals
  FROM readings GROUP BY meter, day;

CREATE VIEW IF NOT EXISTS monthly AS
  SELECT meter, substr(ts_local, 1, 7) AS month, SUM(kwh) AS kwh, COUNT(DISTINCT substr(ts_local, 1, 10)) AS days
  FROM readings GROUP BY meter, month;

-- Average load (kW) per weekday x hour. strftime('%w'): 0 = Sunday.
CREATE VIEW IF NOT EXISTS load_profile AS
  SELECT meter, CAST(strftime('%w', ts_local) AS INTEGER) AS weekday, CAST(substr(ts_local, 12, 2) AS INTEGER) AS hour,
         AVG(kwh) * 4 AS avg_kw, COUNT(*) AS samples
  FROM readings GROUP BY meter, weekday, hour;
"""


def connect(path: Path | None = None) -> sqlite3.Connection:
    path = path or db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    return con


@dataclass(frozen=True)
class Reading:
    meter: str
    ts_utc: datetime
    kwh: float
    kwh_export: float = 0.0
    status: int | None = None


def fmt_utc(t: datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def fmt_local(t: datetime) -> str:
    return t.astimezone(TZ).strftime("%Y-%m-%d %H:%M")


def upsert(con: sqlite3.Connection, readings: list[Reading], source: str, ref: str) -> int:
    """Insert or replace by (meter, ts_utc). Latest write wins, so re-fetching a day repairs it."""
    if not readings:
        return 0
    now = fmt_utc(datetime.now(UTC))
    con.executemany(
        """INSERT INTO readings (meter, ts_utc, ts_local, kwh, kwh_export, status, source, fetched_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT (meter, ts_utc) DO UPDATE SET
             ts_local = excluded.ts_local, kwh = excluded.kwh, kwh_export = excluded.kwh_export,
             status = excluded.status, source = excluded.source, fetched_at = excluded.fetched_at""",
        [(r.meter, fmt_utc(r.ts_utc), fmt_local(r.ts_utc), r.kwh, r.kwh_export, r.status, source, now)
         for r in readings],
    )
    first, last = min(r.ts_utc for r in readings), max(r.ts_utc for r in readings)
    con.execute("INSERT INTO imports (source, ref, first_local, last_local, rows, imported_at) VALUES (?, ?, ?, ?, ?, ?)",
                (source, ref, fmt_local(first), fmt_local(last), len(readings), now))
    con.commit()
    return len(readings)


# ---------------------------------------------------------------- time

def local_to_utc(naive: datetime) -> datetime | None:
    """Wall-clock Asia/Jerusalem -> UTC. None for times that don't exist (spring-forward hour).

    Ambiguous fall-back times resolve to the first occurrence (fold=0, still summer time).
    IEC's CSV only lists the repeated hour once, so the second 01:00-01:59 shows up as a gap.
    """
    aware = naive.replace(tzinfo=TZ, fold=0)
    if aware.astimezone(UTC).astimezone(TZ).replace(tzinfo=None, fold=0) != naive.replace(fold=0):
        return None
    return aware.astimezone(UTC)


# ---------------------------------------------------------------- CSV import

def parse_csv(text: str) -> tuple[list[Reading], int]:
    """Parse IEC's 'meter_LP_*.csv' export. Returns (readings, skipped_nonexistent).

    Layout: ~12 header/spacer rows (customer, address, contract, meter), then one row per interval:
      "<code>-<serial>", "צריכה", "DD/MM/YYYY", "HH:MM" (interval start), kWh, export kWh
    Data rows are found by shape, not by line number, so header changes don't break the parser.
    """
    out: list[Reading] = []
    skipped = 0
    for row in csv.reader(io.StringIO(text.lstrip("﻿"))):
        if len(row) < 5:
            continue
        meter, _kind, d, t, kwh = (c.strip() for c in row[:5])
        try:
            naive = datetime.strptime(f"{d} {t}", "%d/%m/%Y %H:%M")
            value = float(kwh)
        except ValueError:
            continue  # header or spacer row
        export = float(row[5]) if len(row) > 5 and row[5].strip() else 0.0
        ts = local_to_utc(naive)
        if ts is None:
            skipped += 1  # IEC pads the nonexistent spring-forward hour with zeros
            continue
        out.append(Reading(meter=meter, ts_utc=ts, kwh=value, kwh_export=export))
    return out, skipped


def csv_attachments(path: Path) -> list[tuple[str, str]]:
    """Return [(filename, text)] from a .csv, an .eml, or a Gmail API message JSON with a 'raw' field."""
    data = path.read_bytes()
    if path.suffix.lower() == ".csv":
        return [(path.name, data.decode("utf-8-sig"))]
    if data.lstrip()[:1] == b"{":
        raw = json.loads(data)["raw"]
        data = base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4))
    msg = email.message_from_bytes(data, policy=policy.default)
    found = []
    for part in msg.iter_attachments():
        name = part.get_filename() or ""
        if name.lower().endswith(".csv"):
            found.append((name, part.get_payload(decode=True).decode("utf-8-sig")))
    return found


def cmd_import(args) -> int:
    con = connect()
    archive = data_dir() / "raw/csv"
    archive.mkdir(parents=True, exist_ok=True)
    for p in map(Path, args.files):
        files = csv_attachments(p)
        if not files:
            print(f"{p}: no CSV attachment found", file=sys.stderr)
            return 1
        for name, text in files:
            readings, skipped = parse_csv(text)
            if not readings:
                print(f"{name}: no interval rows recognised", file=sys.stderr)
                return 1
            first, last = min(r.ts_utc for r in readings), max(r.ts_utc for r in readings)
            # The export header holds name/address/ID; it stays in the local data dir only.
            (archive / f"{fmt_local(first)[:10]}_{fmt_local(last)[:10]}.csv").write_text(text, encoding="utf-8")
            n = upsert(con, readings, "csv", name)
            print(f"{name}: {n} intervals {fmt_local(first)} .. {fmt_local(last)}"
                  + (f" (skipped {skipped} nonexistent DST slots)" if skipped else ""))
    return 0


# ---------------------------------------------------------------- IEC API

class AuthRequired(Exception):
    pass


def notify(msg: str) -> None:
    if shutil.which("osascript"):
        subprocess.run(["osascript", "-e", f'display notification "{msg}" with title "IEC meter"'], capture_output=True)


async def _client():
    """Logged-in IecClient from the stored token. Raises AuthRequired when a fresh OTP login is needed."""
    from iec_api.iec_client import IecClient
    from iec_api.models.jwt import JWT

    user_id, token = os.environ.get("IEC_USER_ID") or secret_get("user-id"), secret_get("token")
    if not user_id or not token:
        raise AuthRequired("no stored login")
    client = IecClient(user_id)
    try:
        await client.load_jwt_token(JWT.from_dict(json.loads(token)))  # refreshes when the id_token expired
    except Exception as e:
        await client._session.close()
        raise AuthRequired(f"stored token rejected: {e}") from e
    secret_set("token", json.dumps(client.get_token().to_dict()))  # Okta may rotate the refresh token
    return client


@dataclass
class Meter:
    contract_id: str
    serial: str
    code: str

    @property
    def key(self) -> str:
        return f"{self.code}-{self.serial}"


async def _meters(client) -> list[Meter]:
    customer = await client.get_customer()
    contract = await client.get_default_contract(customer.bp_number)
    devices = await client.get_devices(contract.contract_id) or []
    return [Meter(contract.contract_id, d.device_number, d.device_code) for d in devices if d.device_number]


async def _fetch_day(client, meter: Meter, day: date) -> tuple[list[Reading], dict]:
    """One DAILY request = that day's 15-minute intervals. Also returns the raw JSON for the archive."""
    import iec_api.commons as commons
    from iec_api.models.remote_reading import ReadingResolution

    captured: dict = {}
    original = commons.send_post_request

    async def capture(*a, **kw):
        captured["response"] = await original(*a, **kw)
        return captured["response"]

    commons.send_post_request = capture  # data.get_remote_reading calls it through the module
    try:
        start = datetime.combine(day, datetime.min.time())
        resp = await client.get_remote_reading("Consumption", meter.serial, int(meter.code), start, start,
                                               ReadingResolution.DAILY, meter.contract_id)
    finally:
        commons.send_post_request = original
    readings = []
    for m in (resp.meter_list if resp else []):
        for pc in m.period_consumptions or []:
            ts = pc.interval.astimezone(UTC)  # iec-api makes these tz-aware (Asia/Jerusalem)
            if ts.astimezone(TZ).date() == day:
                readings.append(Reading(meter.key, ts, pc.consumption, pc.back_stream or 0.0, pc.status))
    return readings, captured.get("response", {})


def _last_local_day(con: sqlite3.Connection) -> date | None:
    row = con.execute("SELECT MAX(ts_local) FROM readings").fetchone()
    return date.fromisoformat(row[0][:10]) if row and row[0] else None


async def _fetch(args) -> int:
    con = connect()
    today = datetime.now(TZ).date()
    end = date.fromisoformat(args.to) if args.to else (today if args.include_today else today - timedelta(days=1))
    if args.from_:
        start = date.fromisoformat(args.from_)
    else:
        last = _last_local_day(con)
        # Re-fetch a few recent days: IEC back-fills intervals the meter delivered late.
        start = last - timedelta(days=args.overlap) if last else end - timedelta(days=29)
    if start > end:
        print("nothing to fetch")
        return 0

    raw_dir = data_dir() / "raw/api"
    raw_dir.mkdir(parents=True, exist_ok=True)
    client = await _client()
    try:
        meters = await _meters(client)
        if not meters:
            print("no smart meter on the default contract", file=sys.stderr)
            return 1
        total, empty = 0, []
        for meter in meters:
            day = start
            while day <= end:
                readings, raw = await _fetch_day(client, meter, day)
                (raw_dir / f"{meter.key}_{day}.json").write_text(json.dumps(raw, ensure_ascii=False, default=str))
                n = upsert(con, readings, "api", f"api:{day}")
                total += n
                if n == 0:
                    empty.append(day)
                print(f"{meter.key} {day}: {n} intervals")
                day += timedelta(days=1)
                await asyncio.sleep(args.delay)
        print(f"done: {total} intervals stored" + (f"; {len(empty)} days returned nothing" if empty else ""))
    finally:
        await client._session.close()
    return 0


def cmd_fetch(args) -> int:
    try:
        return asyncio.run(_fetch(args))
    except AuthRequired as e:
        print(f"login required ({e}). Run: iec login", file=sys.stderr)
        notify("Login expired. Run: iec login")
        return 2


async def _login(args) -> int:
    from iec_api.iec_client import IecClient

    user_id = args.id or os.environ.get("IEC_USER_ID") or secret_get("user-id") or input("Israeli ID number (ת.ז.): ").strip()
    client = IecClient(user_id)
    try:
        factor = await client.login_with_id(prefer_sms=not args.email)
        code = input(f"Code sent by {factor or 'OTP'}. Enter it: ").strip()
        await client.verify_otp(code)
        secret_set("user-id", str(user_id))
        secret_set("token", json.dumps(client.get_token().to_dict()))
        meters = await _meters(client)
        print("logged in; meters: " + ", ".join(m.key for m in meters))
    finally:
        await client._session.close()
    return 0


def cmd_login(args) -> int:
    return asyncio.run(_login(args))


async def _request_export(args) -> int:
    client = await _client()
    try:
        for m in await _meters(client):
            ok = await client.send_consumption_report_to_mail(args.email, m.contract_id, m.serial, m.code)
            print(f"{m.key}: export {'requested' if ok else 'request failed'} -> {args.email}")
    finally:
        await client._session.close()
    return 0


def cmd_request_export(args) -> int:
    try:
        return asyncio.run(_request_export(args))
    except AuthRequired as e:
        print(f"login required ({e}). Run: iec login", file=sys.stderr)
        return 2


async def _verify(args) -> int:
    """Compare one API day against what is already stored (normally CSV) and detect a clock offset."""
    con = connect()
    day = date.fromisoformat(args.date)
    client = await _client()
    try:
        meters = await _meters(client)
        for m in meters:
            api, _ = await _fetch_day(client, m, day)
            stored = dict(con.execute("SELECT ts_utc, kwh FROM readings WHERE meter = ? AND substr(ts_local, 1, 10) = ?",
                                      (m.key, str(day))).fetchall())
            print(f"{m.key} {day}: api={len(api)} stored={len(stored)} intervals")
            if not api or not stored:
                continue
            best = None
            for shift in range(-12, 13):  # +-3h in 15-min steps
                pairs = [(r.kwh, stored.get(fmt_utc(r.ts_utc + shift * STEP))) for r in api]
                pairs = [(a, b) for a, b in pairs if b is not None]
                if pairs:
                    err = sum(abs(a - b) for a, b in pairs) / len(pairs)
                    if best is None or err < best[1]:
                        best = (shift, err, len(pairs))
            if best is None:
                print("  no overlapping intervals at any shift")
                continue
            shift, err, n = best
            verdict = "aligned" if shift == 0 and err < 1e-3 else f"OFFSET {shift * 15:+d} min" if err < 1e-3 else "MISMATCH"
            print(f"  best shift {shift * 15:+d} min, mean abs diff {err:.4f} kWh over {n} intervals -> {verdict}")
    finally:
        await client._session.close()
    return 0


def cmd_verify(args) -> int:
    try:
        return asyncio.run(_verify(args))
    except AuthRequired as e:
        print(f"login required ({e}). Run: iec login", file=sys.stderr)
        return 2


# ---------------------------------------------------------------- status (read-only)

def _repeated_hour(t: datetime) -> bool:
    """True for the second pass through the fall-back hour, which IEC's CSV never lists."""
    return local_to_utc(t.astimezone(TZ).replace(tzinfo=None, fold=0)) != t


def gaps(con: sqlite3.Connection, meter: str) -> list[tuple[str, str, int, bool]]:
    """Runs of missing 15-minute intervals between the first and last stored reading.

    Each run is (first_local, last_local, count, dst_only); dst_only marks the expected fall-back hour.
    """
    out, prev = [], None
    for (ts,) in con.execute("SELECT ts_utc FROM readings WHERE meter = ? ORDER BY ts_utc", (meter,)):
        t = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        if prev is not None and t - prev > STEP:
            missing = [prev + STEP * i for i in range(1, int((t - prev) / STEP))]
            out.append((fmt_local(missing[0]), fmt_local(missing[-1]), len(missing),
                        all(_repeated_hour(m) for m in missing)))
        prev = t
    return out


def _jwt_exp(token_json: str) -> str:
    try:
        payload = json.loads(token_json)["id_token"].split(".")[1]
        exp = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))["exp"]
        return fmt_local(datetime.fromtimestamp(exp, UTC))
    except Exception:
        return "unreadable"


def cmd_status(args) -> int:
    print(f"data dir : {data_dir()}")
    token = secret_get("token")
    print(f"login    : {'stored' if os.environ.get('IEC_USER_ID') or secret_get('user-id') else 'no ID stored'}; "
          f"{'id_token expires ' + _jwt_exp(token) + ' (auto-refreshed)' if token else 'no token'}")
    if not db_path().exists():
        print("db       : not created yet")
        return 0
    con = connect()
    for meter, n, first, last in con.execute(
            "SELECT meter, COUNT(*), MIN(ts_local), MAX(ts_local) FROM readings GROUP BY meter"):
        print(f"meter    : {meter}  {n} intervals  {first} .. {last}")
        g = [x for x in gaps(con, meter) if not x[3]]
        print(f"gaps     : {len(g)}" + ("" if not g else f" ({sum(x[2] for x in g)} intervals)")
              + "  (DST fall-back hours excluded)")
        for a, b, k, _ in g[-args.gaps:]:
            print(f"           {a} .. {b}  ({k} missing)")
    for src, ref, a, b, n, at in con.execute(
            "SELECT source, ref, first_local, last_local, rows, imported_at FROM imports ORDER BY id DESC LIMIT 1"):
        print(f"last run : {at} {src} {ref} ({n} rows {a} .. {b})")
    return 0


# ---------------------------------------------------------------- plans

def _in_window(local: datetime, w: dict) -> bool:
    if "days" in w and (local.isoweekday() % 7) not in w["days"]:  # 0 = Sunday, like strftime('%w')
        return False
    hm = local.strftime("%H:%M")
    s, e = w.get("start", "00:00"), w.get("end", "24:00")
    return s <= hm < e if s < e else hm >= s or hm < e  # windows may wrap midnight


def cmd_plans(args) -> int:
    """Effective discount of each time-of-use plan on your real 15-minute load."""
    plans = json.loads(Path(args.file).read_text())["plans"]
    con = connect()
    rows = [(datetime.strptime(t, "%Y-%m-%d %H:%M"), k) for t, k in con.execute(
        "SELECT ts_local, kwh FROM readings WHERE ts_local >= ? AND ts_local < ? ORDER BY ts_utc",
        (args.from_ or "0000", args.to or "9999"))]
    total = sum(k for _, k in rows)
    if not total:
        print("no readings in range")
        return 1
    print(f"{len(rows)} intervals, {total:.1f} kWh, {rows[0][0]:%Y-%m-%d} .. {rows[-1][0]:%Y-%m-%d}\n")
    result = []
    for plan in plans:
        saved = 0.0
        for t, k in rows:
            pct = max((w["discount"] for w in plan["windows"] if _in_window(t, w)), default=0)
            saved += k * pct / 100
        result.append((saved / total * 100, plan["name"]))
    for pct, name in sorted(result, reverse=True):
        print(f"  {pct:5.2f}%  {name}")
    return 0


# ---------------------------------------------------------------- cli

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="iec", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("login", help="interactive OTP login; stores ID + token in the Keychain")
    s.add_argument("--id", help="Israeli ID number (otherwise prompted, or reused from the Keychain)")
    s.add_argument("--email", action="store_true", help="prefer the email factor over SMS")
    s.set_defaults(fn=cmd_login)

    s = sub.add_parser("fetch", help="pull 15-min readings from the IEC API (non-interactive)")
    s.add_argument("--from", dest="from_", help="YYYY-MM-DD (default: last stored day minus --overlap)")
    s.add_argument("--to", help="YYYY-MM-DD (default: yesterday)")
    s.add_argument("--overlap", type=int, default=2, help="days to re-fetch before the last stored day")
    s.add_argument("--include-today", action="store_true", help="also store today's partial data")
    s.add_argument("--delay", type=float, default=1.0, help="seconds between requests")
    s.set_defaults(fn=cmd_fetch)

    s = sub.add_parser("import", help="import IEC CSV export(s): .csv, .eml, or Gmail message JSON")
    s.add_argument("files", nargs="+")
    s.set_defaults(fn=cmd_import)

    s = sub.add_parser("request-export", help="ask IEC to email the full CSV export")
    s.add_argument("--email", required=True)
    s.set_defaults(fn=cmd_request_export)

    s = sub.add_parser("verify", help="compare one API day with stored rows; detects clock offsets")
    s.add_argument("--date", required=True, help="YYYY-MM-DD, a day already imported from CSV")
    s.set_defaults(fn=cmd_verify)

    s = sub.add_parser("status", help="read-only summary: login, coverage, gaps")
    s.add_argument("--gaps", type=int, default=5, help="how many recent gaps to list")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("plans", help="effective discount per time-of-use plan on your load")
    s.add_argument("--file", default=str(Path(__file__).resolve().parent.parent / "references/plans.example.json"))
    s.add_argument("--from", dest="from_", help="local 'YYYY-MM-DD'")
    s.add_argument("--to", help="local 'YYYY-MM-DD' (exclusive)")
    s.set_defaults(fn=cmd_plans)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
