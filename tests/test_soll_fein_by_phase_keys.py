"""A per-phase Δ target could not be given to a fuss that more than one page renders.

`Fraction.soll_fein_by_phase` re-targets the Δ computation for one phase — the
mechanism for «this ordinance set a different fine weight for this period».
Giving one to the Danish Dukatfod (Forordning af 8. september 1602, which drops
the Ungersk Gylden to 23⅓ Karat) ran into two separate walls, and this file pins
the fix to each.

**The false error.** `Location.validate_cross_refs` demanded that every key be a
phase of *the page being validated*. `reichsdukatenfuss` is rendered by denmark,
schleswig_holstein and lubeck, and lubeck declares only phase `I` — so a key any
other page used was reported as a defect on lubeck. Nothing was wrong with the
data: `compute` falls back to the scalar `soll_fein_g` on a page where the phase
does not match, which is the correct behaviour. The check has moved to
`audit_v2.check_i10_soll_phase_keys`, which can see every page at once.

**The real collision, which the first fix would have hidden.** Phase ids are
per-page, and after Denmark's phases were renumbered to I·II·III·IV both pages
declare `II` — denmark's is 1602-1611, schleswig_holstein's is 1726-1771. A
shared key `II` therefore measured the two Plön ducats of 1760 against the
Danish 1602 ordinance. So the target lives in the per-page override
(`FussPeriod.fractions`, merged by `categorize._merge_fractions`) and the shared
table keeps the imperial value for everyone else.

The lesson is in the second one: a phase id is not a global name, and anything
keyed on it has to say which page it means.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_v2  # noqa: E402
from lib.categorize import _merge_fractions  # noqa: E402


def _loc(name: str) -> dict:
    return yaml.safe_load((ROOT / f"data/v2/locations/{name}.yml").read_text())


class TheSharedTableStaysImperial(unittest.TestCase):
    def test_shared_fractions_carry_no_per_phase_target(self):
        """A per-phase key on the SHARED table would reach every page that
        renders the fuss, including the ones where that id means another
        period."""
        fuesse = yaml.safe_load((ROOT / "data/shared/fuesse.yml").read_text())
        for frac_id, frac in fuesse["reichsdukatenfuss"]["fractions"].items():
            self.assertIsNone(
                frac.get("soll_fein_by_phase"),
                f"fraction {frac_id!r} must keep the imperial target on the "
                f"shared table; Denmark's ordinance value belongs in its own "
                f"fuss_periods override",
            )

    def test_the_denmark_override_carries_it(self):
        dk = _loc("denmark")["fuss_periods"]["reichsdukatenfuss"]["fractions"]
        self.assertEqual({"II": 3.39343}, dk["1"]["soll_fein_by_phase"])
        self.assertEqual({"II": 6.78687}, dk["2"]["soll_fein_by_phase"])
        self.assertEqual({"II": 33.92356}, dk["10"]["soll_fein_by_phase"])

    def test_the_two_pages_disagree_on_what_II_means(self):
        """The reason the override has to exist at all."""
        def window(loc):
            return next((p["year_from"], p["year_to"])
                        for p in _loc(loc)["phases"]["reichsdukatenfuss"]
                        if p["id"] == "II")
        self.assertEqual((1602, 1611), window("denmark"))
        self.assertEqual((1726, 1771), window("schleswig_holstein"))


class MergeFractionsIsPerKey(unittest.TestCase):
    def test_named_fraction_replaces_and_the_rest_is_inherited(self):
        base = {"1": {"soll_fein_g": 3.44191}, "5": {"soll_fein_g": 17.20955}}
        over = {"1": {"soll_fein_g": 3.44191, "soll_fein_by_phase": {"II": 3.39343}}}
        merged = _merge_fractions(base, over)
        self.assertEqual({"II": 3.39343}, merged["1"]["soll_fein_by_phase"])
        self.assertEqual(base["5"], merged["5"], "unnamed fractions are inherited")
        self.assertNotIn("soll_fein_by_phase", base["1"], "base must not be mutated")


class I10CatchesAnInertKey(unittest.TestCase):
    def test_live_corpus_is_clean(self):
        self.assertEqual([], audit_v2.check_i10_soll_phase_keys())

    def test_a_key_no_page_declares_is_reported(self):
        """A typo'd key is inert at runtime — compute silently falls back to the
        scalar — so the audit is the only thing that can catch it."""
        real = audit_v2._load_yaml

        def fake(path):
            doc = real(path)
            if Path(path).name == "denmark.yml":
                doc = dict(doc)
                fp = dict(doc["fuss_periods"])
                rd = dict(fp["reichsdukatenfuss"])
                fr = dict(rd["fractions"])
                fr["1"] = {**dict(fr["1"]), "soll_fein_by_phase": {"1I": 3.39343}}
                rd["fractions"] = fr
                fp["reichsdukatenfuss"] = rd
                doc["fuss_periods"] = fp
            return doc

        audit_v2._load_yaml = fake
        try:
            errs = audit_v2.check_i10_soll_phase_keys()
        finally:
            audit_v2._load_yaml = real
        self.assertEqual(1, len(errs), errs)
        self.assertIn("1I", errs[0])
        self.assertIn("denmark.yml", errs[0])


if __name__ == "__main__":
    unittest.main()
