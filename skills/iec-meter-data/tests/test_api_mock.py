"""API path against the real iec-api models, network mocked. Skipped when iec-api isn't installed.

Run with the skill venv: "$IEC_DATA_DIR/venv/bin/python" -m unittest discover -s tests
"""
import asyncio
import json
import os
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import iec  # noqa: E402

try:
    import iec_api.commons as commons
    from iec_api.models.jwt import JWT
except ImportError:  # pragma: no cover
    commons = None


def day_response(day: str, values: list[float]) -> dict:
    """Shape of POST Consumption/RemoteReadingRange (see iec_api/models/remote_reading.py)."""
    pcs = [{"interval": f"{day}T{i // 4:02d}:{i % 4 * 15:02d}:00", "consumption": v, "backStream": 0, "status": 0}
           for i, v in enumerate(values)]
    return {"reportStatus": 0, "contractNumber": "C1", "taozList": [],
            "meterList": [{"meterKind": 1, "meterSerial": "12345678", "meterCode": "999", "periodConsumptions": pcs}]}


class FakeClient:
    def __init__(self):
        self._session = mock.AsyncMock()
        self.calls = []

    async def get_customer(self):
        return mock.Mock(bp_number="BP")

    async def get_default_contract(self, bp):
        return mock.Mock(contract_id="C1")

    async def get_devices(self, contract_id):
        return [mock.Mock(device_number="12345678", device_code="999")]

    async def get_remote_reading(self, kind, serial, code, last_invoice, from_date, resolution, contract_id):
        from iec_api.models.remote_reading import RemoteReadingResponse
        self.calls.append(from_date.date().isoformat())
        raw = await commons.send_post_request(session=None, url="x", headers={}, json_data={})
        return RemoteReadingResponse.from_dict(raw)


@unittest.skipIf(commons is None, "iec-api not installed")
class ApiTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["IEC_DATA_DIR"] = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()
        os.environ.pop("IEC_DATA_DIR")

    def test_fetch_day_parses_naive_local_intervals_and_archives_raw(self):
        client = FakeClient()

        async def fake_post(**kw):
            return day_response("2026-07-01", [0.25] * 96)

        with mock.patch.object(commons, "send_post_request", fake_post):
            readings, raw = asyncio.run(iec._fetch_day(client, iec.Meter("C1", "12345678", "999"),
                                                       iec.date(2026, 7, 1)))
            self.assertIs(commons.send_post_request, fake_post)  # capture hook removed again
        self.assertEqual(len(readings), 96)
        self.assertEqual(iec.fmt_local(readings[0].ts_utc), "2026-07-01 00:00")
        self.assertEqual(iec.fmt_utc(readings[0].ts_utc), "2026-06-30T21:00:00Z")
        self.assertEqual(raw["meterList"][0]["meterSerial"], "12345678")

    def test_fetch_resumes_from_last_day_with_overlap(self):
        con = iec.connect()
        t = iec.local_to_utc(iec.datetime(2026, 7, 3, 12, 0))
        iec.upsert(con, [iec.Reading("999-12345678", t, 1.0)], "csv", "seed")
        client = FakeClient()

        async def fake_post(**kw):
            return day_response(client.calls[-1], [0.1] * 96)

        async def fake_client():
            return client

        with mock.patch.object(commons, "send_post_request", fake_post), \
             mock.patch.object(iec, "_client", fake_client), \
             mock.patch.object(iec, "datetime", wraps=iec.datetime) as dt:
            dt.now.return_value = iec.datetime(2026, 7, 6, 8, 0, tzinfo=iec.TZ)
            rc = asyncio.run(iec._fetch(Namespace(from_=None, to=None, overlap=2, include_today=False, delay=0)))
        self.assertEqual(rc, 0)
        self.assertEqual(client.calls, ["2026-07-01", "2026-07-02", "2026-07-03", "2026-07-04", "2026-07-05"])
        self.assertEqual(con.execute("SELECT COUNT(*) FROM readings").fetchone()[0], 5 * 96)
        self.assertEqual(len(list(Path(self.tmp.name, "raw/api").glob("*.json"))), 5)

    def test_auth_required_exit_code(self):
        with mock.patch.object(iec, "secret_get", return_value=None):
            rc = iec.cmd_fetch(Namespace(from_=None, to=None, overlap=2, include_today=False, delay=0))
        self.assertEqual(rc, 2)

    def test_token_roundtrip_shape(self):
        tok = JWT(access_token="a", refresh_token="r", token_type="Bearer", expires_in=3600, scope="s", id_token="x.e30.y")
        self.assertEqual(JWT.from_dict(json.loads(json.dumps(tok.to_dict()))).refresh_token, "r")


if __name__ == "__main__":
    unittest.main()
