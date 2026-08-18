"""Regression tests for the «classified but invisible» defect (2026-08-18).

108 finals carried a REAL Müntzfuß beside `phase: 'ngc'` — the NGC seed-source
tag — and rendered on no page at all, while `build.py --validate-only` exited 0.

Two independent halves are pinned here, because the defect needed both to occur:

  1. THE CAUSE — the curator-migration applier in `absorb_seeds_into_final_v2`
     moved a purged foundation's `fuss` onto its new unified host but refused to
     move the `phase`, because the placeholder-phase list it consulted was a
     hand-written literal that nobody extended when the NGC harvest landed.
     Pinned by asserting the tag set is DERIVED from the seed tree, so a source
     added tomorrow is covered without an edit.

  2. THE REASON IT WENT UNSEEN — `schema.validate_cross_refs` does carry a
     «phase must be declared by its fuss» check, but the render's per-coin
     pre-filter drops such a coin BEFORE the `Location` is built, so the
     validator only ever sees survivors. `audit_v2.check_i9_phase_declared`
     states the rule on the DATA, where nothing can filter it away first.

Run: .venv/bin/python scripts/maintenance/test_phase_declared.py
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS = os.path.dirname(_HERE)
sys.path.insert(0, _SCRIPTS)

from maintenance.absorb_seeds_into_final_v2 import (
    _SEED_TAG_PHASES, _discover_seed_tag_phases, V2_SEED,
)
import audit_v2


# --------------------------------------------------------------------------
# 1. The cause: the seed-source tag set must be derived, not hand-listed.
# --------------------------------------------------------------------------

def test_ngc_is_a_recognised_seed_tag():
    """The literal that was missing. Kept as its own assertion so the specific
    regression is named, not merely implied by the derivation test."""
    assert "ngc" in _SEED_TAG_PHASES


def test_every_seed_source_directory_is_a_recognised_tag():
    """Each per-source builder writes `phase: <source>` with the source name
    equal to its directory. If a directory exists and its name is not a
    recognised placeholder, a promotion through that source strands the phase
    exactly as NGC did."""
    if not V2_SEED.is_dir():
        return  # nothing to check in a bare checkout
    for d in V2_SEED.iterdir():
        if d.is_dir():
            assert d.name in _SEED_TAG_PHASES, (
                f"seed source {d.name!r} is not in _SEED_TAG_PHASES — a "
                f"foundation migrating onto a {d.name} host would keep the "
                f"placeholder phase and vanish from the render"
            )


def test_discovery_never_narrows_the_static_set():
    """A missing or empty seed tree must not make the check WEAKER than the
    known-static list — otherwise a fresh clone silently loses the guard."""
    from maintenance.absorb_seeds_into_final_v2 import _STATIC_SEED_TAG_PHASES
    assert _discover_seed_tag_phases() >= _STATIC_SEED_TAG_PHASES


# --------------------------------------------------------------------------
# 2. The reason it went unseen: state the rule on the data.
# --------------------------------------------------------------------------

def _declared(monkey):
    """Install a fixed {entity → {fuss → {phase}}} table so the invariant is
    tested against a known periodisation, not against live project data."""
    audit_v2._declared_phases_by_entity = lambda: {
        "danish_realm": {"reichsdukatenfuss": {"I", "II", "III"}},
    }


def test_seed_tag_phase_beside_a_real_fuss_is_a_violation():
    _declared(None)
    errs = audit_v2.check_i9_phase_declared([
        ("danish_realm", {"id": "unified-ngc-1", "fuss": "reichsdukatenfuss",
                          "phase": "ngc"}),
    ])
    assert len(errs) == 1
    assert "unified-ngc-1" in errs[0]
    # The message must name the repair: a seed tag means «never classified».
    assert "seed-source tag" in errs[0]


def test_declared_phase_passes():
    _declared(None)
    assert audit_v2.check_i9_phase_declared([
        ("danish_realm", {"id": "x", "fuss": "reichsdukatenfuss", "phase": "II"}),
    ]) == []


def test_seed_unsorted_is_exempt():
    """An un-triaged coin is not defective — its «phases» are the synthetic
    per-source buckets the seed_unsorted page does declare."""
    _declared(None)
    assert audit_v2.check_i9_phase_declared([
        ("danish_realm", {"id": "x", "fuss": "seed_unsorted", "phase": "ngc"}),
    ]) == []


def test_unknown_phase_that_is_not_a_seed_tag_is_still_a_violation():
    """A phase pointing at a window that was renamed or removed drops the coin
    just as surely; only the suggested repair differs."""
    _declared(None)
    errs = audit_v2.check_i9_phase_declared([
        ("danish_realm", {"id": "x", "fuss": "reichsdukatenfuss", "phase": "IV"}),
    ])
    assert len(errs) == 1
    assert "not declared by this fuss" in errs[0]


def test_fuss_with_no_declared_phases_is_not_an_i9():
    """Different defect, different repair (a location-yaml decision) — I9-info
    carries it so I9 stays precisely about the phase."""
    _declared(None)
    assert audit_v2.check_i9_phase_declared([
        ("danish_realm", {"id": "x", "fuss": "rhinsk_gylden_fod", "phase": "I"}),
    ]) == []
    assert len(audit_v2.check_i9info_fuss_unpaged([
        ("danish_realm", {"id": "x", "fuss": "rhinsk_gylden_fod", "phase": "I"}),
    ])) == 1


def test_per_page_derived_fuss_is_exempt():
    """18½-Thaler's phase is COMPUTED per page from year_first, so a stored id
    the page does not declare is a tiebreaker miss, not a drop. Pinning this
    keeps the check from firing on the coins that do render."""
    from build import _DERIVE_PHASE_FROM_YEAR
    assert _DERIVE_PHASE_FROM_YEAR, "exemption set is empty — test is vacuous"
    fuss = sorted(_DERIVE_PHASE_FROM_YEAR)[0]
    audit_v2._declared_phases_by_entity = lambda: {"danish_realm": {fuss: {"I"}}}
    assert audit_v2.check_i9_phase_declared([
        ("danish_realm", {"id": "x", "fuss": fuss, "phase": "III"}),
    ]) == []


def test_live_project_data_has_no_stranded_phase():
    """The end-to-end assertion: no final in the repository may carry a phase
    its fuss does not declare. This is what would have failed on 2026-08-18."""
    import importlib
    importlib.reload(audit_v2)
    coins = audit_v2._all_v2_final_coins()
    errs = audit_v2.check_i9_phase_declared(coins)
    assert errs == [], f"{len(errs)} stranded phase(s), first: {errs[0]}"


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
