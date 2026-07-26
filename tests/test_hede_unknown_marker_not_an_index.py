"""Regression: the parser's «unattributed spec» marker must never become a
catalogue index.

`parse_hede._extract_specs` falls back to `by_hede["unknown_<charpos>"]` when a
spec block carries no Hede attribution and the page's primary number is already
taken. That is a PARSE-FAILURE marker, deliberately kept so the measurements
are not silently lost — not a catalogue number.

The seed builder derives the set of Hede sub-numbers a page canonically owns
from the aggregate index's composite keys via `^n?[cf]\\d+h(.+)$`. The composite
key for such a marker reads `nf3hunknown_324`, which that regex matches, so the
marker was treated as an owned sub-number and emitted as a coin with
`catalog.hede: 'unknown_324'`. It reached the rendered page as
«Hede Norge# 3, unknown_324» — a fabricated index on a reader-facing surface
(§0).

The pre-`b8aab75` Norwegian-infix bug produced two such entries. Removing them
did not close the PATH: any future attribution gap — a new page shape, a source
reformatting — would recreate them. This pins the guard.

Added 2026-07-26.

Run:
    .venv/bin/python -m unittest tests.test_hede_unknown_marker_not_an_index -v
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "maintenance"))

BUILDER = PROJECT_ROOT / "scripts/maintenance/build_hede_denmark_seed.py"


class TestOwnedSubsExcludesTheMarker(unittest.TestCase):
    """Reproduce the builder's canonical_subs derivation over a synthetic
    aggregate index and assert the marker is dropped while real sub-numbers
    (including Norwegian ones and letter variants) survive."""

    def _canonical_subs(self, index: dict) -> dict:
        subs: dict[str, set] = {}
        for composite_key, summary in index.items():
            m = re.match(r"^n?[cf]\d+h(.+)$", composite_key)
            if not m:
                continue
            sub_num = m.group(1).lower()
            if sub_num.startswith("unknown_"):
                continue
            subs.setdefault(summary["file"], set()).add(sub_num)
        return subs

    def test_marker_is_not_an_owned_sub_number(self):
        idx = {
            "nf3h2": {"file": "nf3h2"},
            "nf3h3": {"file": "nf3h2"},
            "nf3hunknown_324": {"file": "nf3h2"},
        }
        self.assertEqual(self._canonical_subs(idx), {"nf3h2": {"2", "3"}})

    def test_real_sub_numbers_are_unaffected(self):
        idx = {
            "c8h11aa": {"file": "c8h11a"},
            "c8h11ab": {"file": "c8h11a"},
            "nf5h3a": {"file": "nf5h3"},
            "nf5h3b": {"file": "nf5h3"},
        }
        self.assertEqual(
            self._canonical_subs(idx),
            {"c8h11a": {"11aa", "11ab"}, "nf5h3": {"3a", "3b"}})

    def test_a_page_whose_only_key_is_a_marker_owns_nothing(self):
        """`owned_subs` empty → the builder skips the page as non-canonical
        rather than emitting a fabricated index."""
        idx = {"nf5hunknown_387": {"file": "nf5h3"}}
        self.assertEqual(self._canonical_subs(idx), {})


class TestGuardIsPresentInTheBuilder(unittest.TestCase):
    def test_builder_skips_unknown_prefixed_sub_numbers(self):
        src = BUILDER.read_text(encoding="utf-8")
        self.assertIn('if sub_num.startswith("unknown_"):', src)


class TestNoMarkerSurvivesInTheLiveSeed(unittest.TestCase):
    def test_no_hede_seed_entry_carries_a_marker_index(self):
        import yaml
        seed_dir = PROJECT_ROOT / "data/v2/seed/hede"
        offenders = []
        for f in sorted(seed_dir.glob("*.yml")):
            doc = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
            for c in doc.get("coins") or []:
                hede = (c.get("catalog") or {}).get("hede")
                vals = hede if isinstance(hede, list) else [hede]
                if any("unknown_" in str(v) for v in vals if v is not None):
                    offenders.append(f"{f.name}::{c.get('id')}")
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
