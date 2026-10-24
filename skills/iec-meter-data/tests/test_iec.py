"""Stdlib-only tests: python3 -m unittest discover -s tests"""
import base64
import json
import os
import sys
import tempfile
import unittest
from argparse import Namespace
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import iec  # noqa: E402

FIXTURE = HERE / "fixtures/meter_LP_sample.csv"


class TimeTest(unittest.TestCase):
    def test_summer_and_winter_offsets(self):
        self.assertEqual(iec.fmt_utc(iec.local_to_utc(datetime(2026, 7, 1, 12, 0))), "2026-07-01T09:00:00Z")
        self.assertEqual(iec.fmt_utc(iec.local_to_utc(datetime(2026, 1, 1, 12, 0))), "2026-01-01T10:00:00Z")

    def test_spring_forward_hour_does_not_exist(self):
        self.assertIsNone(iec.local_to_utc(datetime(2026, 3, 27, 2, 30)))

    def test_fall_back_hour_takes_first_occurrence(self):
        self.assertEqual(iec.fmt_utc(iec.local_to_utc(datetime(2025, 10, 26, 1, 0))), "2025-10-25T22:00:00Z")


class CsvTest(unittest.TestCase):
    def setUp(self):
        self.readings, self.skipped = iec.parse_csv(FIXTURE.read_text(encoding="utf-8"))

    def test_rows_and_header_skipped(self):
        self.assertEqual(len(self.readings), 6 + 2 + 4)
        self.assertEqual(self.skipped, 4)
        self.assertEqual({r.meter for r in self.readings}, {"999-12345678"})

    def test_values_parse_leading_dot(self):
        self.assertAlmostEqual(self.readings[0].kwh, 0.261)

    def test_attachment_from_eml_and_gmail_json(self):
        msg = EmailMessage()
        msg["Subject"] = "export"
        msg.set_content("body")
        msg.add_attachment(FIXTURE.read_bytes(), maintype="text", subtype="csv", filename="meter_LP_x.csv")
        with tempfile.TemporaryDirectory() as d:
            eml = Path(d, "m.eml")
            eml.write_bytes(msg.as_bytes())
            gm = Path(d, "m.json")
            gm.write_text(json.dumps({"id": "1", "raw": base64.urlsafe_b64encode(msg.as_bytes()).decode().rstrip("=")}))
            for p in (eml, gm):
                files = iec.csv_attachments(p)
                self.assertEqual([f[0] for f in files], ["meter_LP_x.csv"])
                self.assertEqual(len(iec.parse_csv(files[0][1])[0]), 12)


class DbTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["IEC_DATA_DIR"] = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()
        os.environ.pop("IEC_DATA_DIR")

    def test_import_is_idempotent_and_gaps_ignore_dst(self):
        for _ in range(2):
            self.assertEqual(iec.cmd_import(Namespace(files=[str(FIXTURE)])), 0)
        con = iec.connect()
        self.assertEqual(con.execute("SELECT COUNT(*) FROM readings").fetchone()[0], 12)
        g = iec.gaps(con, "999-12345678")
        real = [x for x in g if not x[3]]
        dst = [x for x in g if x[3]]
        self.assertEqual(dst, [("2025-10-26 01:00", "2025-10-26 01:45", 4, True)])
        self.assertIn(("2026-06-01 10:30", "2026-06-01 10:45", 2, False), real)
        self.assertEqual(con.execute("SELECT kwh FROM hourly WHERE hour_local = '2026-06-01 10:00'").fetchone()[0], 2.1)

    def test_upsert_latest_wins(self):
        con = iec.connect()
        t = iec.local_to_utc(datetime(2026, 6, 1, 10, 0))
        iec.upsert(con, [iec.Reading("m", t, 0.0)], "api", "a")
        iec.upsert(con, [iec.Reading("m", t, 0.7, status=0)], "api", "b")
        self.assertEqual(con.execute("SELECT kwh, ts_local FROM readings").fetchall(), [(0.7, "2026-06-01 10:00")])

    def test_plan_windows(self):
        night = {"days": [0, 1, 2, 3, 4], "start": "23:00", "end": "07:00", "discount": 21}
        self.assertTrue(iec._in_window(datetime(2026, 10, 25, 23, 15), night))   # Sunday night
        self.assertTrue(iec._in_window(datetime(2026, 10, 25, 6, 45), night))    # Sunday early morning
        self.assertFalse(iec._in_window(datetime(2026, 10, 25, 7, 0), night))
        self.assertFalse(iec._in_window(datetime(2026, 10, 24, 23, 15), night))  # Saturday
        self.assertTrue(iec._in_window(datetime(2026, 10, 24, 3, 0), {"discount": 7}))


if __name__ == "__main__":
    unittest.main()
