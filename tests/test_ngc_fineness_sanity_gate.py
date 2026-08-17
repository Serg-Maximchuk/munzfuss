"""Regression: an impossible NGC «Fineness» must not reach the seed as a reading.

NGC's own specification table prints, on some pattern pages, a number in
``Fineness:`` that cannot be a fineness. The Norwegian gold off-strikes struck
from Speciedaler dies are the whole affected family: cuid 1099232 (10 Ducat,
KM PnD20) reads «Fineness: 35.5000», two different nominals both read 58.0, and
FOUR read 40.7 — a 12-Ducat, a 3-Ducat and two 2-Ducats alike. A value shared
across nominals of different size is not a per-piece weight either, so what the
field holds on those pages cannot be determined from the page.

The parser is NOT at fault here and the earlier reading of this as a mapping bug
was wrong: the page really does print it, and the parser captured it faithfully.
Per §0b the fix therefore does NOT reinterpret the number — that would be a
hypothesis shipped as data. It only refuses to pass an impossible fineness
downstream, and preserves the raw value under ``fineness_unusable_raw`` with a
flag, so the record stays auditable (§0b: an honest leftover beats a silent drop).

Karat is deliberately not an accepted encoding: the only two values in that band
across the whole 4406-record corpus are 14.65 and 17.5, and both belong to this
same defective family. Widen the gate if a genuine karat-bearing record appears.

Added 2026-08-17.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from parse_ngc import parse_record, sift_fineness  # noqa: E402


class TestSiftFineness(unittest.TestCase):
    def test_fraction_is_kept(self):
        for v in (0.979, 0.875, 0.5, 1.0):
            self.assertEqual(sift_fineness(v), (v, None), msg=f"{v!r} is a fraction")

    def test_per_mille_is_kept(self):
        for v in (979, 875.0, 500, 1000):
            usable, unusable = sift_fineness(v)
            self.assertEqual(usable, float(v))
            self.assertIsNone(unusable)

    def test_the_off_strike_values_are_refused_and_preserved(self):
        # every distinct value observed on the Norwegian Pn* off-strike pages
        for v in (35.5, 35.0, 33.8, 28.0, 40.7, 58.0, 17.5, 14.65):
            usable, unusable = sift_fineness(v)
            self.assertIsNone(usable, msg=f"{v!r} must not pass as a fineness")
            self.assertEqual(unusable, v, msg=f"{v!r} must be preserved verbatim")

    def test_gap_between_the_two_encodings_is_refused(self):
        for v in (24, 100, 499):
            self.assertIsNone(sift_fineness(v)[0])

    def test_absent_stays_absent(self):
        self.assertEqual(sift_fineness(None), (None, None))

    def test_unparseable_is_preserved_not_crashed(self):
        self.assertEqual(sift_fineness("n/a"), (None, "n/a"))


class TestParseRecordAppliesTheGate(unittest.TestCase):
    def _rec(self, fineness):
        return {"cuid": 1099232, "country": "NORWAY", "catalog_scheme": "KM",
                "catalog_number": "PnD20", "composition": "Gold",
                "date_line": "1668 Rare", "fineness": fineness,
                "note": "Struck with Speciedaler dies, KM#83."}

    def test_impossible_value_is_moved_aside_with_a_flag(self):
        out = parse_record(self._rec(35.5000))
        self.assertIsNone(out["fineness"])
        self.assertEqual(out["fineness_unusable_raw"], 35.5)
        self.assertTrue(out["flags"]["fineness_unusable"])

    def test_a_real_fineness_survives_untouched_and_sets_no_flag(self):
        out = parse_record(self._rec(0.979))
        self.assertEqual(out["fineness"], 0.979)
        self.assertNotIn("fineness_unusable_raw", out)
        self.assertNotIn("fineness_unusable", out.get("flags") or {})

    def test_the_rest_of_the_record_is_unaffected(self):
        out = parse_record(self._rec(35.5000))
        self.assertEqual(out["catalog_own"], {"km": "PnD20"})
        self.assertTrue(out["is_pattern_number"])
        self.assertEqual(out["catalog_refs"], {"km_cross_ref": ["83"]})
        self.assertEqual(out["year_first"], 1668)


if __name__ == "__main__":
    unittest.main()
