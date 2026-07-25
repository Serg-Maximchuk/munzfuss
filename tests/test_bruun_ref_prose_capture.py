"""Regression guards for Bruun ref patterns that captured PROSE, not indices.

Two REF_PATTERNS entries used a bare `(\\S+?)` value capture — any non-space
run — and so harvested whatever followed the catalogue name, even when the
lot carried no index at all:

  * lot 17035 (Bruun-4090, Frederik I 4 Skilling 1532) cites the study in
    running prose — "The most recent study, by Jensen & Skjoldager, again
    leans towards 4 Skilling" — with NO Skjoldager number. The parser
    captured ",", which reached the seed as the catalogue index
    "jensen_skjoldager: ', again leans towards 4 Skilling'".
  * `Schive` matched INSIDE the mintmaster surname "Schivern Knoph" and
    captured "rn" on four lots.

A third, opposite failure: lot 11156's real ref "Skjoldager-F- 53/F-57" was
truncated to "F-" by the old lookahead, losing the index.

Run:  .venv/bin/python -m unittest tests.test_bruun_ref_prose_capture -v
"""
import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "bruun_parse_lots", ROOT / "scripts" / "bruun_parser" / "02_parse_lots.py"
)
pl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pl)


def _skjoldager(text: str):
    m = pl.REF_PATTERNS["Skjoldager"].search(text)
    return re.sub(r"\s+", "", m.group(1)) if m else None


def _schive(text: str):
    m = pl.REF_PATTERNS["Schive"].search(text)
    return m.group(1) if m else None


class SkjoldagerProse(unittest.TestCase):
    def test_prose_mention_yields_no_ref(self):
        # Verbatim from lot 17035's body_excerpt.
        self.assertIsNone(_skjoldager(
            "Scholars and collectors have argued about the denomination of "
            "this coin for centuries. The most recent study, by Jensen & "
            "Skjoldager, again leans towards 4 Skilling."
        ))

    def test_dash_placeholder_yields_no_ref(self):
        self.assertIsNone(_skjoldager("Skjoldager-–; Bruun-4090;"))

    def test_wrapped_index_captured_in_full(self):
        # lot 11156 — the PDF line-wrap leaves a space inside the index.
        self.assertEqual(
            _skjoldager("Skjoldager-F- 53/F-57; Schou-5; Bruun-3978."),
            "F-53/F-57",
        )


class SkjoldagerRealIndices(unittest.TestCase):
    """Every distinct real value in the cache still parses unchanged."""

    def test_all_attested_shapes(self):
        for raw, expected in [
            ("Skjoldager-T21/25;", "T21/25"),
            ("Skjoldager-T-22/26;", "T-22/26"),
            ("Skjoldager-T-81/T-86;", "T-81/T-86"),
            ("Skjoldager-L-01/L-34;", "L-01/L-34"),
            ("Skjoldager-S-01/S-05;", "S-01/S-05"),
            ("Skjoldager-N-05;", "N-05"),
            ("Skjoldager-51/55;", "51/55"),
            ("Skjoldager-76B/83;", "76B/83"),
        ]:
            with self.subTest(raw=raw):
                self.assertEqual(_skjoldager(raw), expected)


class BuilderSideExtraction(unittest.TestCase):
    """The seed builder re-scans the lot body with its OWN Jensen-Skjoldager
    pattern. Both extractors must reject prose — otherwise the weaker one
    re-introduces the artefact on the next regen, which is how the bogus
    index survived a parser fix + full re-parse."""

    PAT = re.compile(
        r"Jensen\s*&?\s*Skjoldager[-:]?\s*"
        r"((?:[A-Z]-?\s*)?\d+[A-Za-z]*(?:\s*/\s*(?:[A-Z]-?\s*)?\d+[A-Za-z]*)*)"
    )

    def _cap(self, text):
        m = self.PAT.search(text)
        return re.sub(r"\s+", "", m.group(1)) if m else None

    def test_builder_pattern_matches_parser_pattern(self):
        src = (ROOT / "scripts" / "maintenance"
               / "build_bruun_denmark_seed.py").read_text()
        self.assertIn(
            r"((?:[A-Z]-?\s*)?\d+[A-Za-z]*(?:\s*/\s*(?:[A-Z]-?\s*)?\d+[A-Za-z]*)*)",
            src,
            "builder-side Jensen-Skjoldager capture drifted from the parser's",
        )

    def test_prose_rejected(self):
        self.assertIsNone(self._cap(
            "The most recent study, by Jensen & Skjoldager, again leans "
            "towards 4 Skilling."
        ))

    def test_real_indices_kept(self):
        self.assertEqual(self._cap("Jensen & Skjoldager-T21/25;"), "T21/25")
        self.assertEqual(self._cap("Jensen & Skjoldager-F- 53/F-57;"), "F-53/F-57")


class SchiveSurname(unittest.TestCase):
    def test_mintmaster_surname_is_not_a_ref(self):
        # lot 13235 — «Schivern Knoph» is the mintmaster, not the catalogue.
        self.assertIsNone(_schive("Mintmaster: Schivern Knoph. Engraver: Johan"))

    def test_real_plate_ref_still_parses(self):
        self.assertEqual(_schive("Schive-X:14; Bruun-8853;"), "X:14")


if __name__ == "__main__":
    unittest.main()
