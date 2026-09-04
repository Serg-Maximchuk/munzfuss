"""A source's reading may be disbelieved, but it may not be deleted.

The Krause Schleswig-Holstein volume prints 3,5 g / .986 for five ducal
Goldgulden that Jensen 1971 weighs at 3,08-3,22 g. The figure is the volume's
blanket gold default, not a measurement (docs/SOURCES.md §13.15) — but it IS
what a widely-used catalogue says, and deleting it loses that fact and lets the
next harvest re-propose it with no memory of why it went (curator direction
2026-09-04).

So `FieldValue.suspect` is a third state beside the two that already existed:

    verified: false   we could not confirm a value       → «(?)»
    suspect           a source prints it, we disbelieve  → «(!)»
    display: false    a redundant duplicate              → nothing

The whole mechanism is one invariant, and it is what this file pins: a suspect
reading reaches the READER and never reaches the ARITHMETIC.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.compute import normalise_field, primary_value, suspect_readings  # noqa: E402
from lib.schema import FieldValue  # noqa: E402


def _reason(text="volume default"):
    """The reason is reader-facing prose, so it is an I18nText triple."""
    return {"de": text, "en": text, "uk": text}


def _fv(value, source, **kw):
    if isinstance(kw.get("suspect"), str):
        kw["suspect"] = _reason(kw["suspect"])
    return FieldValue(value=value, source=source, **kw)


class SuspectIsWithheldFromEveryComputation(unittest.TestCase):
    def test_normalise_field_drops_it(self):
        got = normalise_field([_fv(3.15, "jensen"), _fv(3.5, "ngc", suspect="volume default")])
        self.assertEqual([(3.15, "jensen")], got)

    def test_it_cannot_become_the_primary_reading(self):
        """The ordering matters: a suspect entry listed FIRST must not win the
        primary slot, which drives the rendered Δ."""
        self.assertEqual(
            3.15,
            primary_value([_fv(3.5, "ngc", suspect="volume default"), _fv(3.15, "jensen")]),
        )

    def test_a_field_whose_only_reading_is_suspect_computes_nothing(self):
        """No Δ at all is the honest outcome — better than a Δ measured against
        a number we do not believe."""
        self.assertEqual([], normalise_field([_fv(3.5, "ngc", suspect="volume default")]))
        self.assertIsNone(primary_value([_fv(3.5, "ngc", suspect="volume default")]))


class SuspectStillReachesTheReader(unittest.TestCase):
    def test_it_is_offered_for_rendering_with_its_reason(self):
        got = suspect_readings([_fv(3.15, "jensen"), _fv(3.5, "ngc", suspect="volume default")])
        self.assertEqual(1, len(got))
        value, source, why = got[0]
        self.assertEqual((3.5, "ngc"), (value, source))
        self.assertEqual("volume default", why.uk)

    def test_accepted_readings_are_not_in_that_channel(self):
        self.assertEqual([], suspect_readings([_fv(3.15, "jensen")]))

    def test_display_false_stays_hidden_even_when_suspect(self):
        """`display:false` means «redundant». A redundant duplicate does not
        become interesting by also being wrong."""
        entries = [_fv(3.5, "ngc", suspect="volume default", display=False)]
        self.assertEqual([], suspect_readings(entries))
        self.assertEqual([], normalise_field(entries))


class TheReasonIsMandatory(unittest.TestCase):
    """A bare flag would be an unexplained accusation against a source, so the
    reason is what makes the mark legitimate. `I18nText` does not itself forbid
    an empty string, so the guard that actually holds is the audit — which is
    where this is pinned rather than at the schema."""

    def test_absent_is_the_default(self):
        self.assertIsNone(_fv(3.15, "jensen").suspect)

    def test_the_audit_reports_a_blank_reason(self):
        import audit_v2
        coins = [("test_entity", {
            "id": "x", "weight_rough_g": [{"value": 3.5, "source": "ngc", "suspect": "  "}]})]
        errs = audit_v2.check_i11_suspect_readings(coins)
        self.assertEqual(1, len(errs), errs)
        self.assertIn("no reason", errs[0])

    def test_the_audit_reports_a_verified_flag_over_only_suspect_readings(self):
        """The state the NGC seed builder left behind: every reading withheld,
        yet the coin still claiming a verified value."""
        coins = [("test_entity", {
            "id": "y",
            "fineness": [{"value": 0.986, "source": "ngc", "suspect": {"en": "default"}}],
            "fineness_verified": True})]
        import audit_v2
        errs = audit_v2.check_i11_suspect_readings(coins)
        self.assertEqual(1, len(errs), errs)
        self.assertIn("fineness_verified is true", errs[0])

    def test_the_live_corpus_is_clean(self):
        import audit_v2
        coins = []
        for entity in ("sonderburg_duchy", "gottorp_duchy"):
            doc = yaml.safe_load((ROOT / f"data/v2/final/{entity}.yml").read_text())
            coins += [(entity, c) for c in doc["coins"]]
        self.assertEqual([], audit_v2.check_i11_suspect_readings(coins))


class TheFiveGoldguldenKeepTheCatalogueValue(unittest.TestCase):
    """The case the mechanism was built for. Read from the live corpus: the
    catalogue's 3,5 g and .986 must still be PRESENT on all five, and must all
    be marked."""

    IDS = {
        "sonderburg_duchy": ["unified-ngc-1161408", "unified-ngc-1206707"],
        "gottorp_duchy": ["unified-ngc-1156100", "unified-ngc-1157533",
                          "unified-ngc-1156101"],
    }

    def _coins(self):
        for entity, ids in self.IDS.items():
            doc = yaml.safe_load((ROOT / f"data/v2/final/{entity}.yml").read_text())
            by = {c.get("id"): c for c in doc["coins"]}
            for cid in ids:
                yield cid, by[cid]

    def test_the_template_value_was_not_deleted(self):
        for cid, c in self._coins():
            with self.subTest(cid):
                vals = [e["value"] for e in c["weight_rough_g"]]
                self.assertIn(3.5, vals, "the catalogue's 3,5 g must stay on record")
                fins = [e["value"] for e in (c.get("fineness") or [])]
                self.assertIn(0.986, fins, "the catalogue's .986 must stay on record")

    def test_and_every_template_reading_is_marked_with_a_reason(self):
        for cid, c in self._coins():
            with self.subTest(cid):
                for f, bad in (("weight_rough_g", 3.5), ("fineness", 0.986)):
                    for e in c.get(f) or []:
                        if e["value"] == bad:
                            self.assertTrue(e.get("suspect"),
                                            f"{cid}.{f} {bad} must carry a reason")

    def test_the_1624_type_still_computes_from_the_real_weighings(self):
        """The point of excluding rather than deleting: the accepted readings
        are untouched and still drive the arithmetic."""
        doc = yaml.safe_load((ROOT / "data/v2/final/sonderburg_duchy.yml").read_text())
        c = next(x for x in doc["coins"] if x["id"] == "unified-ngc-1206707")
        kept = sorted(e["value"] for e in c["weight_rough_g"] if not e.get("suspect"))
        self.assertEqual([3.08, 3.16, 3.16, 3.19, 3.22], kept)


if __name__ == "__main__":
    unittest.main()
