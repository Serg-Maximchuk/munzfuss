"""Regression tests for the «a plain re-seed deletes enriched fields» trap.

Diagnosed 2026-08-18. `build_kmk_seed.py` enriched year, mint and catalogue for
part of its corpus from the web-rådata cache, behind an OPT-IN `--raadata` flag.
The COMMITTED seed was built with it; the DEFAULT run was not. Because
`seed_merge.merge_one` deliberately drops an un-curated field the fresh entry no
longer carries, a default `--write` read as «the parser stopped emitting year»
and deleted it — 109 seed entries vanished, and at the end of the chain 232
losses, 25 finals stripped of their year outright.

The lesson generalises past kmk: any builder whose default flags do not
reproduce how the committed seed was built will silently delete the difference.
Two properties are pinned here.

Run: .venv/bin/python scripts/maintenance/test_seed_reseed_idempotent.py
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from ruamel.yaml.comments import CommentedMap

from lib.seed_merge import merge_one


# ---------------------------------------------------------------------------
# 1. The mechanism — merge_one drops what fresh omits. This is DELIBERATE
#    (a parser fix must be able to retire a stale value), so it is pinned as
#    behaviour, not filed as a bug. It is pinned precisely because it is what
#    makes a wrong default destructive rather than merely incomplete.
# ---------------------------------------------------------------------------

def test_omitted_field_is_dropped_not_preserved():
    existing = CommentedMap({"id": "x", "year_first": 1690, "ruler": "Johan Adolf"})
    fresh = CommentedMap({"id": "x", "ruler": "Johan Adolf"})
    out = merge_one(existing, fresh)
    assert "year_first" not in out, (
        "merge_one no longer drops omitted fields — if that is an intended "
        "change, this trap is gone and the test should be retired; if it is "
        "accidental, a parser fix can no longer retire a stale value"
    )


def test_curated_field_survives_omission():
    """The counterweight: curated decisions are exactly what the drop spares."""
    from lib.seed_merge import CURATED_FIELDS
    field = "fuss" if "fuss" in CURATED_FIELDS else sorted(CURATED_FIELDS)[0]
    existing = CommentedMap({"id": "x", field: "reichsdukatenfuss"})
    fresh = CommentedMap({"id": "x"})
    assert merge_one(existing, fresh).get(field) == "reichsdukatenfuss"


def test_curation_hold_survives_omission():
    existing = CommentedMap({"id": "x", "year_first": 1690,
                             "_curation_holds": ["year_first"]})
    fresh = CommentedMap({"id": "x"})
    assert merge_one(existing, fresh).get("year_first") == 1690


# ---------------------------------------------------------------------------
# 2. The kmk default — enrichment must be ON, because the committed seed is the
#    enriched artefact and a default re-run has to reproduce it.
# ---------------------------------------------------------------------------

def test_kmk_raadata_enrichment_is_on_by_default():
    from maintenance import build_kmk_seed as b
    assert b._USE_RAADATA is True, (
        "rådata enrichment is off by default again — a plain --write will "
        "delete the year/mint/catalogue it supplies from every enriched entry"
    )


def test_kmk_no_raadata_flag_exists_and_raadata_is_a_noop():
    """Opting out stays possible, and the old flag must not silently re-disable
    the enrichment for anyone who still passes it."""
    import argparse
    from maintenance import build_kmk_seed as b
    src = open(b.__file__, encoding="utf-8").read()
    assert '"--no-raadata"' in src, "the opt-out was removed"
    assert "_USE_RAADATA = not args.no_raadata" in src, (
        "the default is no longer wired to --no-raadata; check that passing "
        "the deprecated --raadata cannot turn enrichment OFF"
    )


def test_raadata_cache_path_in_help_matches_reality():
    """The help text used to advertise `web/<id>.html` while the cache holds
    `.json`. A wrong path in the help is how an operator concludes the
    enrichment is dead and re-runs without it."""
    from maintenance import build_kmk_seed as b
    src = open(b.__file__, encoding="utf-8").read()
    assert "web/<id>.html" not in src, "help still names a .html rådata cache"


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
