"""`why` must surface every layer that can make a value differ from its source.

A seed value is not always what the source printed, and the difference is nearly
always a decision someone already recorded. Those records live in at least four
places, none of which points at the others:

  * `_source_errata` / `_curation_holds` — in the seed entry itself
  * `_KNOWN_HEDE_TYPOS`, `_INVERTED_TAG_PAGES` — in parse_hede, keyed by PAGE
  * `exclusions/`, `merge_decisions/`, `classification_decisions/`
  * `_retracted_refs.yml`

dk-hede-c5h39 is the regression case, and it is here because it was declared
defective TWICE on 2026-08-08 — once for a «phantom Schou 4», once for «swapped
Hede numbers» — each time by comparing the seed against danskmoent and against
the parser cache. Both verdicts were wrong. Bruun's lot 13186 prints
«Hede-39; Sieg-106; Schou-4» on the physical specimen, the curator called it for
Bruun on 2026-07-16, and the call is implemented as an erratum in the seed plus
a typo map in the parser. Two attempted «repairs» of that working construction
followed before anyone read either.

The parser layer is the one these tests care about most: nothing in the data
points at it, and the cache a reader compares against is ALREADY the corrected
artefact, so it still differs from the printed page.
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "scripts" / "maintenance" / "trace_coin.py"


_CACHE: dict[tuple, subprocess.CompletedProcess] = {}


def why(*args) -> subprocess.CompletedProcess:
    """Memoised: every call re-reads ~12 MB of seed yaml, and these tests would
    otherwise spend a minute doing it eight times over."""
    if args not in _CACHE:
        _CACHE[args] = subprocess.run([sys.executable, str(TOOL), "why", *args],
                                      capture_output=True, text=True, cwd=ROOT)
    return _CACHE[args]


class TestTheRegressionCase(unittest.TestCase):
    def setUp(self):
        self.out = why("dk-hede-c5h39").stdout

    def test_the_erratum_is_shown(self):
        self.assertIn("_source_errata", self.out)
        self.assertIn("was OVERRULED", self.out)

    def test_the_phantom_schou_is_explained_not_hidden(self):
        # «Schou 4» was called a value appearing nowhere. The reason names its
        # source; seeing this text is what stops the third wrong verdict.
        self.assertIn("Bruun lot 13186", self.out)
        self.assertIn("serg", self.out)

    def test_the_parser_typo_map_is_shown(self):
        # The layer with no pointer to it from the data.
        self.assertIn("_KNOWN_HEDE_TYPOS", self.out)
        self.assertIn("SWAPPED", self.out)

    def test_the_suppression_is_shown(self):
        self.assertIn("_INVERTED_TAG_PAGES", self.out)

    def test_what_the_page_actually_prints_is_shown(self):
        # Both readings side by side, so the difference is legible rather than
        # looking like corruption.
        self.assertIn("Hede 40, Schou 3, Sieg 107", self.out)

    def test_field_narrows_the_errata(self):
        out = why("dk-hede-c5h39", "--field", "schou").stdout
        self.assertIn("schou: printed", out)
        self.assertNotIn("sieg: printed", out)


class TestTheQuietCase(unittest.TestCase):
    def test_a_coin_with_no_decisions_says_so(self):
        out = why("dk-hede-c4h18").stdout
        self.assertNotIn("OVERRULED", out)
        self.assertIn("Nothing printed above means no recorded decision", out)


class TestIdDiscipline(unittest.TestCase):
    def test_a_derived_id_is_rejected_not_guessed(self):
        r = why("unified-dk-hede-c5h39")
        self.assertEqual(r.returncode, 1)
        self.assertIn("not a seed id", r.stdout)

    def test_a_seed_id_exits_clean(self):
        self.assertEqual(why("dk-hede-c5h39").returncode, 0)


if __name__ == "__main__":
    unittest.main()
