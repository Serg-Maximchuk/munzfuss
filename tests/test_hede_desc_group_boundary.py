"""Where one catalogue group's refs stop is where the next group's year starts.

`_extract_desc_hede_groups` walks the descriptive section anchor by anchor and
gives each anchor the text back to the previous group's close. That close used
to be the ref-SEGMENT end — a heuristic that stops at the next «)» — and the
two are not the same thing. On a page whose groups aren't parenthesised, the
next «)» is the FOLLOWING row's rarity marker, so that row's text (year and
all) is swallowed by the group before it and the row itself is left with an
empty span.

Four sub-entries changed in the cache, every one of them GAINING a year that
danskmoent prints plainly, and no group's catalog_refs moved at all:

    c4h46  Hede 47  [1600]      → [1597, 1600]
    f3h82  Hede 81  reign-span  → [1669]
    f4h20  Hede 20  []          → [1702]
    nc5h13 Hede 14  [1673]      → [1673, 1678]

A dry-run over `raw_text` predicted two more (c5h15 Hede 16 and 17, both
gaining 1687) and was wrong: the parser feeds this function `descriptive` —
the text BEFORE the first «Bruttovægt» — and on that page rows 16 and 17 sit
after the first spec block, outside it entirely. The prediction and the
pipeline were reading different inputs (§9b). The cases below feed the
function directly, so they pin its behaviour rather than the corpus's. The trailing-edition-paren clause is not
cosmetic: without it the run stops before «Sieg (2017) 107.3» and c4h55's
55C/55D pick up 2017 as a mint year.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
_spec = importlib.util.spec_from_file_location(
    "parse_hede", ROOT / "scripts" / "parse_hede.py")
PH = importlib.util.module_from_spec(_spec)
sys.modules["parse_hede"] = PH
_spec.loader.exec_module(PH)


def years(text: str, hede: str) -> list[int]:
    g = PH._extract_desc_hede_groups(text)
    return [y["year"] for y in g.get(hede, {}).get("years", [])]


def refs(text: str, hede: str) -> dict:
    return PH._extract_desc_hede_groups(text).get(hede, {}).get("catalog_refs", {})


NC5H13 = ("Christian 5., Norge Hede 13 Christian 5. 2 og 3 Dukat 1673, Christiania "
          "Forside: portræt, bagside: elefant (Hede Norge 14, Schou 1) "
          "2 Dukat 1673 (RRR). Hede Norge 13, Schou 6 "
          "3 Dukat 1678 (unik). Hede Norge 14, Schou 1")

C4H46 = ("Christian 4., 1 og 2 speciedaler, København "
         "1 Speciedaler 1597 - Hede 46, Schou 2, Sieg 112. "
         "2 Speciedaler 1597 (R), 1600 (RR) - Hede 47, Schou 1,1, Sieg 113")

C5H15 = ("Christian 5. 2, 3 og 5 Dukat 1687, København "
         "2 Dukat 1687 (R) Hede 15, Schou 3, Sieg 120 "
         "3 Dukat 1687 (unik) Hede 16, Schou 2, Sieg 121 "
         "5 Dukat 1687 (unik) Hede 17, Schou 1, Sieg 122")

C4H55 = ("Christian 4., 1 speciedaler, København "
         "C) 1631, 1632, 1634; Møntmærke trekløver: , PG "
         "(Hede 55C, Schou 5-6, 6-7, 4, Sieg (2017) 107.3) "
         "D) 1646, 1647; Møntmærke glødehage: eller intet, HK "
         "(Hede 55D, Schou 17-25, 13-15, Sieg (2017) 107.4)")


class TestTheRowKeepsItsOwnYear(unittest.TestCase):
    def test_a_rarity_paren_no_longer_eats_the_next_row(self):
        # «(unik)» closes the PREVIOUS group's segment; 1678 is Hede 14's.
        self.assertIn(1678, years(NC5H13, "14"))

    def test_the_page_title_year_still_reaches_the_caption_group(self):
        # 1673 is what the page's own H1 claims for both nominals — the fix
        # ADDS the row's year, it does not adjudicate between them (§4).
        self.assertEqual(years(NC5H13, "14"), [1673, 1678])

    def test_a_two_year_row_keeps_both(self):
        self.assertEqual(years(C4H46, "47"), [1597, 1600])

    def test_rows_that_had_no_year_at_all_now_have_one(self):
        # In the real pipeline this page's rows 16/17 never reach this
        # function — see the note above. The behaviour is still worth pinning:
        # when such rows ARE inside `descriptive`, each keeps its own year.
        self.assertEqual(years(C5H15, "16"), [1687])
        self.assertEqual(years(C5H15, "17"), [1687])

    def test_the_first_row_is_unaffected(self):
        self.assertEqual(years(C5H15, "15"), [1687])
        self.assertEqual(years(C4H46, "46"), [1597])


class TestNothingElseMoves(unittest.TestCase):
    def test_refs_are_unchanged_by_the_boundary(self):
        self.assertEqual(refs(NC5H13, "13"), {"Schou": ["6"]})
        self.assertEqual(refs(C5H15, "16"), {"Schou": ["2"], "Sieg": ["121"]})
        self.assertEqual(refs(C4H46, "47"), {"Schou": ["1,1"], "Sieg": ["113"]})

    def test_a_sieg_edition_year_is_not_a_mint_year(self):
        for key in ("55C", "55D"):
            self.assertNotIn(2017, years(C4H55, key), key)
        self.assertEqual(years(C4H55, "55D"), [1646, 1647])


if __name__ == "__main__":
    unittest.main()
