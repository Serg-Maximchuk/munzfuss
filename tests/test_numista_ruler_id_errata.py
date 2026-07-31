"""Numista ruler record 4713 is Frederik VI, not «Frederick IX».

Numista's ruler table gives id 4713 the name «Frederick IX» while every other
part of the same record says Frederik VI: the coin titles read «… - Frederik
VI», the Ruler field prints the reign «1808-1839», and the record's wikidata_id
Q155002 is «Frederick VI of Denmark» (king 13 Mar 1808 - 3 Dec 1839). Frederik
IX reigned 1947-1972, more than a century after every affected coin
(N#19531, 61491, 142102, 152374 — dated 1809-1839).

Our builder copied `ruler[0].name` faithfully, so a «Frederick IX» cell reached
the rendered Schleswig-Holstein page. Verified against the live Numista page and
Wikidata 2026-07-30, then corrected by ruler ID in build_numista_seed.

Run:
    .venv/bin/python -m unittest tests.test_numista_ruler_id_errata -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "maintenance"))

import build_numista_seed as B  # noqa: E402


class TestRulerIdErrata(unittest.TestCase):
    def test_4713_becomes_frederik_vi(self):
        kings = [{"id": 4713, "name": "Frederick IX", "wikidata_id": "Q155002"}]
        self.assertEqual(B._resolve_ruler(kings), "Frederik VI")

    def test_correction_keys_on_the_id_not_the_name(self):
        # Same broken name under a DIFFERENT ruler id is left alone: the
        # erratum asserts one record is wrong, not that the string always is.
        kings = [{"id": 9999, "name": "Frederick IX"}]
        self.assertEqual(B._resolve_ruler(kings), "Frederick IX")

    def test_a_renamed_4713_is_still_corrected(self):
        # If Numista fixes the name upstream the erratum must stay harmless.
        kings = [{"id": 4713, "name": "Frederick VI"}]
        self.assertEqual(B._resolve_ruler(kings), "Frederik VI")

    def test_multi_ruler_join_applies_the_erratum_per_member(self):
        kings = [{"id": 4713, "name": "Frederick IX"},
                 {"id": 1, "name": "Christian VIII"}]
        self.assertEqual(B._resolve_ruler(kings), "Frederik VI / Christian VIII")

    def test_existing_hans_canonicalisation_survives(self):
        self.assertEqual(B._resolve_ruler([{"id": 2, "name": "John I (Hans I)"}]),
                         "Hans")
        self.assertEqual(B._resolve_ruler([{"id": 3, "name": "John (Hans)"}]), "Hans")

    def test_untouched_rulers_pass_through(self):
        self.assertEqual(B._resolve_ruler([{"id": 5, "name": "Christian IV"}]),
                         "Christian IV")
        self.assertIsNone(B._resolve_ruler([]))
        self.assertIsNone(B._resolve_ruler(None))


if __name__ == "__main__":
    unittest.main()
