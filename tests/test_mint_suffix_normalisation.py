"""Trailing «Mint» / «mint» descriptor must never survive into the
`mint` field.

Functions under test:
    scripts/lib/mint_registry.py    :: strip_mint_suffix
    scripts/lib/v2_seed_writer.py   :: _canonicalise_mint
    scripts/maintenance/merge_seeds_cross_source.py :: _normalise_mints

Bug (verified live 2026-07-25): Bruun auction meta lines name the mint
as «Christiania mint» / «Copenhagen Mint» — capitalisation varies. The
suffix-strip existed but was CASE-SENSITIVE (`\\s+Mint\\s*$`), so the
lowercase spelling passed through untouched. Two consequences, both
observed in live data:

  1. The cross-source comparator saw «Christiania mint» vs
     «Christiania» as a real mint disagreement, recording
     `dk-bruun-6811` + `dk-numista-445275` in match_uncertainty with
     `mint: false` despite all four primary signals agreeing.
  2. `unified-dk-hede-nc5h16` in data/v2/final/danish_norway.yml stored
     `mint: [Christiania, Christiania mint]` — one town listed twice,
     rendering to the reader as a two-mint coin.

Run:
    .venv/bin/python -m pytest tests/test_mint_suffix_normalisation.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "maintenance"))

from lib.mint_registry import strip_mint_suffix  # noqa: E402
from lib.v2_seed_writer import _canonicalise_mint  # noqa: E402
from merge_seeds_cross_source import _normalise_mints  # noqa: E402


class TestStripMintSuffix(unittest.TestCase):
    """The bare helper — the rule both call sites share."""

    def test_lowercase_suffix_stripped(self):
        # The exact live-data case that slipped past the old
        # case-sensitive regex.
        self.assertEqual(strip_mint_suffix("Christiania mint"), "Christiania")

    def test_capitalised_suffix_stripped(self):
        self.assertEqual(strip_mint_suffix("Copenhagen Mint"), "Copenhagen")

    def test_bare_mint_name_untouched(self):
        # No suffix to strip — value passes through unchanged.
        self.assertEqual(strip_mint_suffix("Christiania"), "Christiania")
        self.assertEqual(strip_mint_suffix("Glückstadt"), "Glückstadt")

    def test_name_ending_in_non_descriptor_word_untouched(self):
        # A mint whose name genuinely ends in another word must not be
        # damaged — only the standalone «Mint» descriptor is a suffix.
        self.assertEqual(strip_mint_suffix("Frankfurt am Main"),
                         "Frankfurt am Main")
        self.assertEqual(strip_mint_suffix("Kongsberg"), "Kongsberg")

    def test_substring_not_a_suffix(self):
        # «mint» embedded in a longer trailing word is not the
        # descriptor — the \\s+ guard must keep it.
        self.assertEqual(strip_mint_suffix("Minturno"), "Minturno")

    def test_bare_descriptor_not_annihilated(self):
        # Stripping would leave the empty string, silently dropping the
        # field. Keep the original rather than destroy the value.
        self.assertEqual(strip_mint_suffix("Mint"), "Mint")

    def test_non_string_passthrough(self):
        self.assertIsNone(strip_mint_suffix(None))


class TestSeedWriterCanonicalisation(unittest.TestCase):
    """Phase-3 seed writer — freshly built seeds must be clean."""

    def test_lowercase_suffix_canonicalised(self):
        self.assertEqual(_canonicalise_mint("Christiania mint"), "Christiania")

    def test_capitalised_suffix_canonicalised(self):
        # «Copenhagen» also folds to the project-canonical «Kopenhagen»
        # via the alias registry.
        self.assertEqual(_canonicalise_mint("Copenhagen Mint"), "Kopenhagen")

    def test_list_form_dedups_to_scalar(self):
        # The polluted live shape: same town twice, one carrying the
        # descriptor. Collapses to a single scalar — per CLAUDE.md §9a
        # list-form is for genuine multi-mint coins only.
        self.assertEqual(
            _canonicalise_mint(["Christiania", "Christiania mint"]),
            "Christiania",
        )

    def test_genuine_joint_mint_stays_list(self):
        # Two DIFFERENT towns must survive as a list — the dedup must
        # not over-collapse.
        self.assertEqual(
            _canonicalise_mint(["Christiania", "Copenhagen Mint"]),
            ["Christiania", "Kopenhagen"],
        )

    def test_suffix_on_comma_token(self):
        self.assertEqual(_canonicalise_mint("Denmark, Copenhagen mint"),
                         "Kopenhagen")


class TestMergerComparator(unittest.TestCase):
    """The matcher must stop seeing a false mint disagreement."""

    def test_lowercase_suffix_normalises_to_same_token(self):
        self.assertEqual(_normalise_mints("Christiania mint"), {"christiania"})

    def test_suffixed_and_bare_forms_overlap(self):
        # The dk-bruun-6811 / dk-numista-445275 case: Bruun's suffixed
        # form and Numista's bare form are the SAME mint.
        bruun = _normalise_mints("Christiania mint")
        numista = _normalise_mints("Christiania")
        self.assertTrue(bruun & numista)

    def test_distinct_mints_still_disagree(self):
        # The fix must not make every mint pair overlap.
        self.assertFalse(
            _normalise_mints("Christiania mint") & _normalise_mints("Kopenhagen")
        )


if __name__ == "__main__":
    unittest.main()
