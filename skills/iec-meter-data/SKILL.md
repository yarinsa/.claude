---
name: iec-meter-data
description: Fetch Israel Electric Corporation (IEC, חברת החשמל) smart-meter readings at 15-minute resolution and keep them in a local SQLite DB for analysis. Pulls daily from IEC's customer API (OTP login, token in the macOS Keychain, launchd job), imports IEC's emailed CSV export (meter_LP_*.csv, also straight from Gmail), reports gaps, and compares time-of-use supplier plans against real load. Use for anything about home electricity usage, the IEC smart meter (מונה חכם), consumption exports, load profiles, or choosing a private electricity supplier plan (מסלול הנחה).
---

# IEC meter data

Local history of 15-minute consumption from an IEC smart meter. Two sources feed one table:

- **API**, the unofficial customer API used by the IEC app (`iecapi.iec.co.il`), through [`iec-api`](https://pypi.org/project/iec-api) (pinned). Automated and daily.
- **CSV**, IEC's official export, emailed on request. Covers about 2 years and is used for backfill or when the API breaks.

## Layout

| Path | What |
|---|---|
| `scripts/iec.py` | The CLI. Storage, CSV and status code is stdlib only; API commands need the venv. |
| `scripts/setup.sh` | Creates the venv with pinned `iec-api` and writes the `iec` wrapper. Idempotent. |
| `scripts/install-launchd.sh` | Daily `iec fetch` LaunchAgent (`--uninstall` removes it). |
| `scripts/diagnose.sh` | Read-only: install, Keychain items, data coverage, schedule, last log. |
| `references/analysis.md` | Schema, views and ready SQL for common questions. |
| `references/plans.example.json` | Time-of-use plan shapes for `iec plans`. |

Data lives outside the repo in `IEC_DATA_DIR`, default `~/Library/Application Support/iec-meter/`:
`iec.db`, `raw/api/*.json` (every API response), `raw/csv/*.csv` (every imported export), `logs/fetch.log`, `venv/`, and the `iec` wrapper.
The ID number and Okta token are Keychain items under service `iec-meter` (accounts `user-id`, `token`).

## First-time setup

```sh
scripts/setup.sh
IEC="$HOME/Library/Application Support/iec-meter/iec"
"$IEC" login                         # asks for ID number, then the SMS code (--email for email OTP)
"$IEC" import ~/Downloads/meter_LP_*.csv   # backfill history, if you have an export
"$IEC" verify --date <a day that is in the CSV>   # confirms API timestamps line up with the CSV
"$IEC" fetch                         # continues from the last stored day
scripts/install-launchd.sh           # daily at 07:13
scripts/diagnose.sh
```

`login` is the only interactive step, and the user has to type the OTP. Never try to obtain or guess it.
After login, `fetch` refreshes and saves the token itself, so the daily job runs unattended.
When the refresh token dies, `fetch` exits with code 2, prints `login required`, and shows a macOS notification. The fix is `iec login`.

## Commands

| Command | Does |
|---|---|
| `iec fetch [--from D] [--to D] [--overlap 2] [--include-today]` | One API request per day per meter. Without `--from` it re-fetches the last 2 stored days (IEC fills in late intervals) and runs up to yesterday. On an empty DB it fetches the last 30 days. |
| `iec import FILE...` | Accepts a `.csv`, an `.eml`, or a Gmail API message JSON (`{"raw": ...}`). Idempotent. |
| `iec request-export --email ADDR` | Asks IEC to email the full CSV export (arrives within minutes). |
| `iec verify --date D` | Compares an API day with stored rows and reports `aligned`, `OFFSET ±N min` or `MISMATCH`. |
| `iec status` | Read-only coverage, gaps and token expiry. |
| `iec plans [--file F] [--from D] [--to D]` | Effective % discount of each plan on the stored load. |

## Importing the export from Gmail

IEC sends it from `noreplys@dpd.iec.co.il` with the subject `פירוט שנתי של נתוני הצריכה במונה קריאה מרחוק` and an attachment named `meter_LP_<hash>_<email>.csv`. With the Gmail connector:

1. `search_threads` with `from:noreplys@dpd.iec.co.il subject:(נתוני הצריכה) has:attachment`.
2. `get_message` with `messageFormat: RAW`. The result is too large for context, so the harness saves it to a file and prints the path.
3. Run `iec import <that path>`. It decodes the MIME and imports every CSV attachment.

If there is no recent export, run `iec request-export --email <user's address>`, wait a few minutes, then repeat the steps above.

## Facts about the data

These were established from a real export (2025-05 to 2026-10) and the `iec-api` and Home Assistant source. They explain the parser's choices.

1. **CSV layout.** The file is UTF-8 with a BOM and CRLF line endings. About 12 header rows hold the customer name, address, contract number, meter type, code and serial. They are followed by data rows: `"<code>-<serial>","צריכה","DD/MM/YYYY","HH:MM",kWh,export_kWh`. kWh values can have a leading dot (`.155`). The parser finds data rows by their shape, not by line number.
2. **Timestamps are the start of the interval** (`מועד תחילת הפעימה`), in Israel wall-clock time.
3. **Daylight saving time.** Every day has exactly 96 rows, even on transition days:
   - **Spring forward:** the nonexistent 02:00–02:45 slots are present but zero. The parser drops them.
   - **Fall back:** the repeated 01:00 hour is listed once. It is stored as the first occurrence (summer time), so the second pass shows up as a 4-interval gap, which `status` hides.
4. **Storage key.** Rows are keyed on `(meter, ts_utc)`, and `ts_local` is stored next to it for grouping. Always group by `ts_local`, and order or compute durations by `ts_utc`.
5. **One API day.** A `DAILY` request (`POST Consumption/RemoteReadingRange/{contract}`, `resolution=1`) returns that day's 15-minute `periodConsumptions` (`interval`, `consumption`, `backStream`, `status`). `iec-api` attaches Asia/Jerusalem to naive timestamps. The exact semantics are unconfirmed, which is why `verify` exists, and every raw response is archived for reprocessing.
6. **Lag.** Data runs about 1 day behind, and IEC fills in late intervals afterwards. Hence the daily run plus the 2-day overlap. On conflict, the latest write wins.
7. **History.** The export starts when the meter was installed, not two years back.
8. **Unofficial API.** It can change without notice. If `fetch` starts failing on anything other than login, check for a newer `iec-api` and the Home Assistant integration's issue tracker, bump `PIN`, and re-run `setup.sh`. Use `request-export` plus `import` as the fallback.

## Privacy

The CSV header and the raw files contain the customer's name, address and contract number. They stay in `IEC_DATA_DIR`, which is mode 700. Never copy them into the repo or paste them into shared output. The skill's `.gitignore` blocks `*.csv` except the synthetic test fixture.

## Tests

```sh
python3 -m unittest discover -s tests                                   # stdlib only; API tests skip
"$HOME/Library/Application Support/iec-meter/venv/bin/python" -m unittest discover -s tests   # all
```
