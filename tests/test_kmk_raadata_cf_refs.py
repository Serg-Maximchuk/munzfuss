"""A «cf.» reference is a pointer at a DIFFERENT coin, and KMM prints it inline
next to the object's own index.

KMM's Bech-protocol records routinely read «Protokolnr. 60; B 188c, cfr. B 188b»
— a protocol number, an own index, and a cf-index in one line. CLAUDE.md
anti-pattern 5 forbids any «cf.» / «cfr.» value reaching a `catalog` field: it
names the nearest comparable type, not this coin.

`_raadata_catalog` never actually leaked one — but only by accident. Its `B`
branch is `re.match(r"B\\s+(\\d+\\w*(?:\\.\\w+)?)$")`, and the cf-forms survived
purely because the `$` anchor rejects a trailing «, cfr. …» and `re.match`
rejects a leading «cfr. ». Both are incidental properties of a regex written for
another purpose; loosening either — dropping the anchor to catch «B 188c 2», say
— would silently start writing cf-indices into `others[]`, and nothing would
have complained. This pins the behaviour as intended rather than incidental.

Corpus at the time of writing: 19 cached rådata sidecars carry a cf-form, 0 leak.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

_spec = importlib.util.spec_from_file_location(
    "build_kmk_seed_for_test", ROOT / "scripts" / "maintenance" / "build_kmk_seed.py"
)
bks = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bks)


class CfReferencesNeverReachCatalog(unittest.TestCase):
    def test_real_kmm_lines_yield_no_catalogue(self):
        # Verbatim `beskrivelser` from cached sidecars 635302 / 635206 / 635416.
        for line in (
            "Protokolnr. 60; B 188c, cfr. B 188b",
            "Protokolnr. 113; cfr. B 290b 2(?)",
            "Protokolnr. 1; cfr. B 8",
        ):
            with self.subTest(line=line):
                self.assertEqual(bks._raadata_catalog(["mark", line]), {})

    def test_cf_segment_dropped_while_clean_sibling_survives(self):
        out = bks._raadata_catalog(["dukat", "Bech nr. 977; cfr. B 8"])
        self.assertEqual(out.get("others"), ["Bech# 977"])

    def test_cf_forms_are_rejected_for_every_catalogue_branch(self):
        for seg in (
            "cf. Sch 3a",
            "cfr. Sch 3a",
            "cf. Bech nr. 876",
            "cfr. LEB 12",
            "cf. Schubart 40",
            "cfr. Auk. Kat. no. 5",
            "cf. B 783.a",
        ):
            with self.subTest(seg=seg):
                self.assertEqual(bks._raadata_catalog([seg]), {})

    def test_clean_lines_still_parse(self):
        out = bks._raadata_catalog(["to mark", "Bech nr. 876; B 783.a; Sch 3a"])
        self.assertEqual(out.get("schou"), "3a")
        self.assertEqual(out.get("others"), ["Bech# 876", "B# 783.a"])


if __name__ == "__main__":
    unittest.main()
