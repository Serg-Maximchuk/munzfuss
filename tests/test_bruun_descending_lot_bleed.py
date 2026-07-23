"""TDD test for Bruun parser descending-lot ref bleed.

Function under test:
    scripts/bruun_parser/02_parse_lots.py :: parse_part (block boundary)

Bug (surfaced via lot 12088 ½ Dukat audit, 2026-07-23): a two-column PDF
layout places lot N-1/N-2 physically AFTER lot N in the extracted text.
The old block-boundary heuristic broke a lot's block only on an ASCENDING
next-lot number (`next_lot > lot_no`), so a descending neighbour never
ended the block and its whole text — including its catalogue refs — bled
into the preceding lot. Real case: lot 12088 (½ Dukat, gold, no Davenport
number) wrongly grabbed `Dav-3621` from the descending neighbour lot 12087
(Speciedaler, silver — Davenport catalogues silver crowns).

Fix: break the block on any REAL lot start — a lot-number line whose next
non-blank line is a region META line — regardless of ascending/descending
order. The META requirement keeps a stray in-body 4-5 digit number from
falsely ending the block.

Run via:
    .venv/bin/python -m unittest tests.test_bruun_descending_lot_bleed -v
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

_spec = importlib.util.spec_from_file_location(
    "bruun_parse_lots",
    str(PROJECT_ROOT / "scripts" / "bruun_parser" / "02_parse_lots.py"),
)
_parser = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_parser)


# A descending-order lot pair inside part3's declared range: lot 12088
# (½ Dukat, no Davenport) printed BEFORE its lower-numbered neighbour 12087
# (Speciedaler, carries Dav-3621). Mirrors the real two-column PDF layout.
_SYNTH_PAGE = (
    "12088\n"
    "NORWAY. 1/2 Dukat, 1666. Christiania Mint. Frederik III. NGC Unc "
    "Details. Fr-5; KM-80; Hede-4; Sieg-69; Schou-10; Aagaard-3.1; "
    "Bruun-9985. Weight: 1.72 gms.\n"
    "€30,000-€40,000\n"
    "From the L. E. Bruun Collection.\n"
    "12087\n"
    "NORWAY. Speciedaler, 1665. Christiania Mint. Frederik III. NGC AU. "
    "Dav-3621; KM-79; Hede-3; Sieg-68. Weight: 25.50 gms.\n"
    "€5,000\n"
    "From the L. E. Bruun Collection.\n"
)


class TestDescendingLotBleed(unittest.TestCase):
    def setUp(self):
        self._orig_split = _parser.split_pages
        _parser.split_pages = lambda slug: [(205, _SYNTH_PAGE)]

    def tearDown(self):
        _parser.split_pages = self._orig_split

    def _lot(self, lots, lot_no):
        return next((l for l in lots if l["lot_no"] == lot_no), None)

    def test_dav_does_not_bleed_into_gold_half_dukat(self):
        lots = _parser.parse_part("part3")
        lot = self._lot(lots, 12088)
        self.assertIsNotNone(lot, "lot 12088 must parse")
        refs = lot["refs"]
        # The descending neighbour's Davenport number must NOT be captured.
        self.assertNotIn(
            "Dav", refs,
            f"Dav-3621 bled from descending lot 12087 into 12088: {refs}",
        )

    def test_own_refs_preserved(self):
        """The fix must not strip lot 12088's own printed refs."""
        lots = _parser.parse_part("part3")
        refs = self._lot(lots, 12088)["refs"]
        self.assertEqual(refs.get("KM"), "80")
        self.assertEqual(refs.get("Hede"), "4")
        self.assertEqual(refs.get("Fr"), "5")
        self.assertEqual(refs.get("Schou"), "10")
        self.assertEqual(refs.get("Bruun"), "9985")


if __name__ == "__main__":
    unittest.main()
