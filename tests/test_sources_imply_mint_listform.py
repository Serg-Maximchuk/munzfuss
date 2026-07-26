"""Regression: the sources-imply-mint rule must never promote a LIST-form mint.

Function under test:
    scripts/lib/v2_seed_writer.py — the «sources-imply-mint» rule, which flips
    `mint_verified` to True when a scalar mint is accompanied by a source URL
    (every source we harvest publishes mint metadata, so a False there is an
    under-claim).

The rule has an exclusion: a LIST-form mint is either a genuine joint mint or
an ambiguity split («København eller Malmø»), and neither may be auto-promoted
to verified (§4 — `*_verified: true` requires a source attesting THAT value).

The rule is implemented TWICE — once on the in-memory write path and once on
the pass that normalises seed YAMLs already on disk. `d934e4e` added the
list-form exclusion to the first copy only. The on-disk copy therefore still
flipped five `royal_holstein` entries carrying `mint: [Altona, Kopenhagen]`
from False to True on a plain regen — the mint value unchanged, only the claim
about it — which also made the regen non-idempotent. This test pins BOTH
copies so the pair cannot drift again (CLAUDE.md anti-pattern 2).

Added 2026-07-26.

Run:
    .venv/bin/python -m unittest tests.test_sources_imply_mint_listform -v
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

WRITER = PROJECT_ROOT / "scripts/lib/v2_seed_writer.py"


class TestBothCopiesGuardListForm(unittest.TestCase):
    def test_every_sources_imply_mint_site_excludes_list_form(self):
        """Each occurrence of the rule must carry the list-form exclusion.

        Matching on source text rather than behaviour because the two copies
        sit on different call paths (in-memory write vs on-disk normalisation)
        and the on-disk one is reachable only through a full builder run."""
        src = WRITER.read_text(encoding="utf-8")
        sites = [m.start() for m in re.finditer(
            r'and any\(isinstance\(s, dict\) and s\.get\("url"\) for s in sources\)',
            src)]
        self.assertGreaterEqual(len(sites), 2,
                                "expected both sources-imply-mint copies")
        for pos in sites:
            window = src[max(0, pos - 400):pos]
            self.assertIn('not isinstance(c.get("mint"), list)', window,
                          "a sources-imply-mint site is missing the list-form "
                          "exclusion — a joint / ambiguous mint would be "
                          "auto-promoted to verified")


class TestListFormMintStaysUnverified(unittest.TestCase):
    """Behavioural pin on the in-memory copy, which is directly callable."""

    def _hygiene(self, coin):
        from lib.v2_seed_writer import _apply_pre_write_hygiene
        kept, _ = _apply_pre_write_hygiene([coin])
        return kept[0]

    def _coin(self, mint):
        return {
            "id": "t", "nominal": "1 Speciedaler", "metal": "silver",
            "mint": mint, "mint_verified": False,
            "sources": [{"url": "https://www.danskmoent.dk/chr/c7h28.htm"}],
        }

    def test_joint_mint_list_is_not_promoted(self):
        out = self._hygiene(self._coin(["Altona", "Kopenhagen"]))
        self.assertFalse(out.get("mint_verified"))

    def test_scalar_mint_is_promoted(self):
        """The rule's normal case must keep working — this is the control that
        proves the guard didn't disable the rule outright."""
        out = self._hygiene(self._coin("Altona"))
        self.assertTrue(out.get("mint_verified"))


if __name__ == "__main__":
    unittest.main()
