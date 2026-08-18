"""Regression tests for the year-blind mint→entity call sites (2026-08-18).

`classify_mint_to_entity(mint, year=None)` is ERA-AWARE: `mint_registry`
lets a mint carry `year_overrides`, so the same mint resolves to different
entities in different periods (today: Altona before 1640 →
`schauenburg_pinneberg`, otherwise `royal_holstein`; `year_to` is
EXCLUSIVE).

Three call sites passed no year and therefore silently took the DEFAULT
era — `build_galster_denmark_seed.detect_issuing_entity`,
`build_hede_denmark_seed._classify_hede_entity`, and the entity invariant
check in `v2_seed_writer._check_entity_invariant`. The last was the worst:
being year-blind there made the guard fire BACKWARDS — reporting a
correctly-routed pre-1640 Altona coin as a mismatch, and staying silent on
a wrongly-routed one.

The defect was LATENT when fixed (zero seeds changed: galster has no Altona
coins, hede's 75 are all 1640+). Its whole value is in the future — a
`year_overrides` rule added for Gottorp on 2026-08-18 was invisible to both
builders — so the property is pinned here rather than left to a data diff.

Run: .venv/bin/python scripts/maintenance/test_mint_entity_year_aware.py
"""
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_SCRIPTS)
sys.path.insert(0, _SCRIPTS)

from lib.v2_entity_classify import classify_mint_to_entity
from lib.v2_seed_writer import _check_entity_invariant
from maintenance.build_galster_denmark_seed import detect_issuing_entity
from maintenance.build_hede_denmark_seed import _classify_hede_entity

# The one era rule that exists today, used as the probe throughout.
_MINT = "Altona"
_EARLY, _LATE = 1620, 1650
_EARLY_ENTITY = "schauenburg_pinneberg"


# --------------------------------------------------------------------------
# 0. The resolver really is era-aware — otherwise every test below is vacuous.
# --------------------------------------------------------------------------

def test_resolver_is_era_aware():
    early = classify_mint_to_entity(_MINT, _EARLY)
    late = classify_mint_to_entity(_MINT, _LATE)
    assert early != late, (
        f"{_MINT} resolves to {early!r} in both {_EARLY} and {_LATE} — the "
        "era rule is gone, so these tests no longer prove anything"
    )
    assert early == _EARLY_ENTITY, early


# --------------------------------------------------------------------------
# 1-3. The year actually REACHES the resolver at each of the three call sites.
# --------------------------------------------------------------------------

def test_galster_builder_passes_year():
    assert detect_issuing_entity(None, _MINT, _EARLY) == _EARLY_ENTITY


def test_hede_builder_passes_year():
    assert _classify_hede_entity(_MINT, None, _EARLY) == _EARLY_ENTITY


def test_seed_writer_invariant_passes_year():
    """The guard must accept a CORRECTLY-routed pre-1640 Altona coin…"""
    stats = _check_entity_invariant(
        [{"id": "t1", "mint": _MINT, "year_first": _EARLY,
          "issuing_entity": _EARLY_ENTITY}],
        "test",
    )
    assert stats["entity_mismatch"] == 0, stats


def test_seed_writer_invariant_still_catches_wrong_routing():
    """…and still flag a WRONGLY-routed one. Year-blind, it did the reverse."""
    wrong = classify_mint_to_entity(_MINT, _LATE)
    stats = _check_entity_invariant(
        [{"id": "t2", "mint": _MINT, "year_first": _EARLY,
          "issuing_entity": wrong}],
        "test",
    )
    assert stats["entity_mismatch"] == 1, stats


# --------------------------------------------------------------------------
# 4. No NEW year-blind call site may appear in the builders.
# --------------------------------------------------------------------------

# Benign year-blind calls, allow-listed BY NAME so a third one fails.
_ALLOWED_YEAR_BLIND = {
    # «is this string a known mint at all?» membership test — the year is
    # irrelevant to the question being asked.
    ("scripts/maintenance/build_kmk_seed.py", 167),
    # Prose: a module-docstring mention, not a call.
    ("scripts/maintenance/build_numista_seed.py", 17),
}

_CALL_RE = re.compile(r"classify_mint_to_entity\(([^)]*)")


def test_no_new_year_blind_builder_call_sites():
    import glob

    offenders = []
    for path in sorted(glob.glob(os.path.join(_SCRIPTS, "maintenance",
                                              "build_*_seed.py"))):
        rel = os.path.relpath(path, _ROOT)
        for lineno, line in enumerate(open(path), start=1):
            m = _CALL_RE.search(line)
            if not m:
                continue
            if (rel, lineno) in _ALLOWED_YEAR_BLIND:
                continue
            args = m.group(1)
            if "year" not in args:
                offenders.append(f"{rel}:{lineno}: {line.strip()}")
    assert not offenders, (
        "year-blind classify_mint_to_entity call(s) — pass the coin's year, "
        "or allow-list by name with a reason:\n  " + "\n  ".join(offenders)
    )


def test_allow_list_entries_still_exist():
    """A stale allow-list would silently excuse a real offender at that line."""
    for rel, lineno in sorted(_ALLOWED_YEAR_BLIND):
        lines = open(os.path.join(_ROOT, rel)).readlines()
        assert lineno <= len(lines), f"{rel}:{lineno} is past end of file"
        assert "classify_mint_to_entity" in lines[lineno - 1], (
            f"{rel}:{lineno} no longer mentions classify_mint_to_entity — "
            "the allow-list has drifted; re-check and update it"
        )


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ✓ {name}")
            except AssertionError as e:
                failed += 1
                print(f"  ✗ {name}: {e}")
    print(f"\n{'FAILED' if failed else 'OK'} — {failed} failure(s)")
    sys.exit(1 if failed else 0)
