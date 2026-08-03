#!/usr/bin/env python3
"""Field-diff every `data/v2/final/*.yml` against git HEAD, and call the losses.

WHY THIS EXISTS
---------------
Every other auditor in this project measures INSIDE the working tree:

    audit_curation_loss    final  vs  recomputed-from-unified  (what the NEXT apply would change)
    audit_lost_citations   final  vs  its own current members
    audit_v2               invariants within one state
    trace_coin             snapshot vs snapshot — both taken by hand

None of them answers the one question that actually gates a commit: **is the
rendered data worse than what is already committed?** That measurement had no
tool, so it got hand-rolled in a shell heredoc each time — and on 2026-08-01
four such hand-rolled baselines were each wrong in a different way:

  * an inventory keyed on the cached `body_excerpt`, which is `body[:600]` — a
    truncation — reported 25 suppressed lots and a table of 17 that included
    ordinary silver Speciedaler. The real figure, read from the full body, was 5.
  * a dangling-`composed_of` sweep resolved ids against ONE entity's
    seed_unified; cross-entity members live in other files, so it flagged six
    healthy records as dead and was one keystroke from writing that to disk.
  * a `trace_coin` snapshot taken with seeds updated but seed_unified/final
    stale measured a MIXTURE of two changes and reported «16 coins lost their
    final» where a comparison against real HEAD showed none.
  * a one-line merge change that looked obviously right rewrote 872 of 1695
    lines across 23 seed files into a wrong scalar shape, caught only by
    reading the diff.

The pattern is single: the comparison BASELINE was not what the author assumed.
Prose cannot fix that — CLAUDE.md §0b already demands verification from real
data, and all four happened anyway. A committed baseline is the one reference
that cannot be half-applied, mid-flight or silently truncated, so this tool
takes it from `git show HEAD:` and nothing else.

WHAT IT REPORTS
---------------
Per entity and in total: coins added, coins removed, coins changed, and for each
changed coin which fields moved — classified as a GAIN or a LOSS.

A LOSS is any of:
  * a coin present at HEAD that is gone now and was NOT folded into a survivor
    (a fold is recognised by the survivor listing it in `composed_of`, by one
    survivor having absorbed its source URLs, or by the survivors between them
    covering every one of those URLs — see REDISTRIBUTION below);
  * a scalar field that had a value at HEAD and is now empty;
  * a list field (sources / weight_rough_g / fineness / diameter_mm / catalog
    registers) that lost an entry NOTHING in the entity attests any more;
  * a change of `fuss` or `phase` from a real assignment back to `seed_unsorted`.

Everything else — new coins, new readings, a scalar filling in, a catalogue
register gaining a value — is a GAIN and never blocks.

A list entry is matched on its IDENTITY (a source's url, a reading's source
label), not on its whole content, so a CORRECTED value under an unchanged
identity is reported as a change and never as a loss. Keying on content cannot
tell the two apart: on 2026-08-02 that reported km-82-chr-iv-1640 as losing a
source and a weight while the coin had gained both — one kmk specimen's weight
had merely been corrected to 0.932. The gate's errors are safe in direction
(false alarm, never a missed loss), which is exactly why they must stay rare:
a gate that cries loss over a non-loss trains its reader to skim past it.

REDISTRIBUTION — why «gone from this coin» is not «gone»
--------------------------------------------------------
The unit that carries data through the pipeline is the SEED, and a merge
decision re-assigns seeds between classes (CLAUDE.md §9b: seed ids are the only
stable handle). When a seed changes class it takes its citations, weights and
catalogue indices with it: the old class shrinks, the new one grows, and the
project has lost nothing. Judged strictly per coin that reads as a loss on
every such move — which is how this tool first reported 56 «losses» for a
re-flow that, measured across the entity, dropped not one citation, not one
catalogue index (case-folded, as absorb folds them) and not one attested year.

So a dropped value blocks only when NOTHING in the entity attests it any more.
Values that merely changed owner are counted separately as `moved`, kept
visible in the summary rather than silently swallowed. Two normalisations are
likewise not losses: a `display: false` flip (absorb HIDES a surplus museum
citation, the citation stays) and a `year_ranges` de-overlap (the tuple
[1813,1813] folding into [1813,1815] loses the tuple, not the year).

Exit 0 = no losses. Exit 1 = at least one loss (the commit should not go out).

USAGE
-----
    .venv/bin/python scripts/maintenance/verify_reflow.py                # all entities
    .venv/bin/python scripts/maintenance/verify_reflow.py --entity danish_realm
    .venv/bin/python scripts/maintenance/verify_reflow.py --verbose      # list every changed coin
    .venv/bin/python scripts/maintenance/verify_reflow.py --base <ref>   # baseline other than HEAD
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
FINAL_REL = "data/v2/final"
EXCLUSIONS_REL = "data/v2/exclusions"
UNIFIED_REL = "data/v2/seed_unified"

# Fields whose disappearance or shrinkage is a real regression. `note` and the
# prose fields are excluded on purpose — they are curator-edited and a rewrite
# legitimately replaces them.
SCALAR_FIELDS = (
    "nominal", "ruler", "year_label", "year_first", "year_last",
    "mint", "metal", "kind", "fuss", "phase", "mintmaster",
)
LIST_FIELDS = ("sources", "weight_rough_g", "fineness", "diameter_mm", "year_ranges")

# Keys on a list entry that carry RENDER VISIBILITY, not data. `display: false`
# is set by absorb's `_suppress_weightless_museum_overcollection` to hide — not
# delete — surplus weightless KMM specimen citations; the citation stays in the
# YAML in full. Keying a list entry on the whole dict therefore reads a pure
# visibility flip as «lost 1, gained 1» and blocks a re-flow that lost nothing.
# (Observed 2026-08-02: km-82-chr-iv-1640 was reported as losing KMM 693125,
# which the very same file demonstrably still carried, one key richer.)
PRESENTATION_KEYS = frozenset({"display"})

# What makes one list entry THE SAME entry across the two sides, independent of
# its value. Keying an entry on its whole serialisation — which is what the
# set-difference below used to do — cannot tell a CORRECTED reading from a
# DROPPED one: both read as «one key vanished». On 2026-08-02 that reported
# km-82-chr-iv-1640 as losing a source and a weight while the coin had in fact
# gained both (sources 7 → 8, weights 6 → 7); one kmk specimen's weight had
# merely been corrected to 0.932. An entry whose IDENTITY is still present is a
# modification, never a loss — reported, but it does not block.
IDENTITY_KEYS: dict[str, tuple[str, ...]] = {
    "sources": ("url", "ref"),              # url; ref when the source has no url
    "weight_rough_g": ("source",),
    "fineness": ("source",),
    "diameter_mm": ("source",),
}


def _ident(field: str, v) -> str:
    """Identity of one list entry — what it IS, not what it says.

    Falls back to the full value key when the entry is not a dict or carries
    none of the field's identity keys: then content is all the identity there
    is, and the old strict behaviour applies.
    """
    if isinstance(v, dict):
        for k in IDENTITY_KEYS.get(field, ()):
            got = v.get(k)
            if got not in (None, ""):
                return f"{k}={got}"
    return _key(v)


def _git_show(ref: str, rel: str) -> dict | None:
    """Parse `<ref>:<rel>` as YAML; None when the path does not exist there."""
    r = subprocess.run(["git", "show", f"{ref}:{rel}"],
                       capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        return None
    return yaml.safe_load(io.StringIO(r.stdout)) or {}


def _coins(doc: dict | None) -> dict[str, dict]:
    return {c["id"]: c for c in (doc or {}).get("coins") or [] if c.get("id")}


def _urls(coin: dict) -> set[str]:
    return {s.get("url") for s in (coin.get("sources") or []) if isinstance(s, dict) and s.get("url")}


def _as_list(v) -> list:
    if v is None:
        return []
    return list(v) if isinstance(v, list) else [v]


def _key(v) -> str:
    """Identity of a value for set-difference purposes.

    Dict entries drop `PRESENTATION_KEYS` first, so a render-visibility flip is
    not mistaken for a dropped reading.
    """
    if isinstance(v, dict):
        v = {k: x for k, x in v.items() if k not in PRESENTATION_KEYS}
    return json.dumps(v, sort_keys=True, default=str)


def _covered_years(ranges) -> set[str]:
    """Every individual year a `year_ranges` list attests, as comparable keys."""
    out: set[str] = set()
    for r in _as_list(ranges):
        try:
            lo, hi = int(r[0]), int(r[1])
        except (TypeError, ValueError, IndexError, KeyError):
            out.add(_key(r))
            continue
        if hi < lo:
            lo, hi = hi, lo
        out.update(str(y) for y in range(lo, hi + 1))
    return out


def _catalog_key(v) -> str:
    """Case-folded identity of one catalogue index value.

    Absorb's `_fold_catalog_indices` de-dups list-form catalogue values
    case-insensitively («Hede 55c» + «55C» → one «55C»). A case-sensitive
    comparison therefore reads that normalisation as a lost index: seed
    kmk-348205's Hede «75a» merging into unified-dk-hede-c5h75, which carries
    «75A», is the SAME index in the catalogue's own casing, not a loss.
    """
    return str(v).strip().upper()


def _catalog_registers(coin: dict) -> dict[str, set[str]]:
    """catalog → {register: {values}}, so a register losing a value is visible."""
    out: dict[str, set[str]] = {}
    for reg, val in (coin.get("catalog") or {}).items():
        out[reg] = {_catalog_key(x) for x in _as_list(val)}
    return out


def _excluded_ids(entity: str) -> set[str]:
    """Seed ids the curator has excluded for `entity` (data/v2/exclusions/).

    A curator exclusion is the one REMOVAL this project sanctions that is not a
    fold: the coin is deliberately dropped from the render with a recorded
    reason (§9 + PB-12), and by construction no survivor absorbs it. Without
    this the gate reports every exclusion as data falling on the floor and hard-
    blocks the very commit that records the decision — which is how the check
    would teach people to reach for --no-verify.
    """
    path = ROOT / EXCLUSIONS_REL / f"{entity}.yml"
    if not path.exists():
        return set()
    doc = yaml.safe_load(path.read_text()) or {}
    raw = {e["id"] for e in (doc.get("exclusions") or []) if e.get("id")}
    if not raw:
        return set()

    # An exclusion names a SEED id; a final's `composed_of` names the UNIFIED
    # classes it was built from. Bridge the two through seed_unified, which is
    # the only place that maps a unified class to its member seeds — the
    # `unified-<head member>` naming is a convention, not something to parse.
    unified_path = ROOT / UNIFIED_REL / f"{entity}.yml"
    if unified_path.exists():
        udoc = yaml.safe_load(unified_path.read_text()) or {}
        for c in udoc.get("coins") or []:
            if c.get("id") and raw & set(c.get("composed_of") or []):
                raw.add(c["id"])
    return raw


def compare_entity(entity: str, base: str) -> dict:
    """Load both sides for `entity` and delegate to `compare_coins`."""
    rel = f"{FINAL_REL}/{entity}.yml"
    head = _coins(_git_show(base, rel))
    path = ROOT / rel
    cur = _coins(yaml.safe_load(path.read_text()) if path.exists() else None)
    return compare_coins(entity, head, cur, excluded=_excluded_ids(entity))


def _attestation_index(coins: dict[str, dict]) -> dict[str, set[str]]:
    """Every value the entity still attests, per comparison dimension.

    A re-flow moves MEMBERS between classes, and a member takes its readings
    with it: when a seed leaves `unified-kmk-131360` for another class, that
    class's `year_ranges` shrink and the destination's grow. Judged per coin
    that reads as a loss; judged across the entity nothing was lost at all.
    Since the members that move live a layer below `final` (inside a
    seed_unified class that can shrink while the final's own `composed_of` is
    unchanged), the final layer cannot attribute the move to a destination —
    so retention is measured entity-wide, which is the question the gate
    actually asks: is anything no longer attested anywhere?
    """
    idx: dict[str, set[str]] = {f: set() for f in LIST_FIELDS}
    idx["catalog"] = set()
    for coin in coins.values():
        for f in LIST_FIELDS:
            if f == "year_ranges":
                idx[f] |= _covered_years(coin.get(f))
            else:
                idx[f] |= {_key(x) for x in _as_list(coin.get(f))}
        for reg, vals in _catalog_registers(coin).items():
            idx["catalog"] |= {f"{reg}={v}" for v in vals}
    return idx


def compare_coins(entity: str, head: dict[str, dict], cur: dict[str, dict],
                  excluded: set[str] | frozenset = frozenset()) -> dict:
    """Classify every difference between two {id: coin} maps as gain or loss.

    Split out from the loading so the classification — the part with judgement
    in it — is directly testable without a git tree or a filesystem.

    `excluded` carries the curator's exclusion ids for this entity; a coin that
    vanished because one of them names it is a recorded decision, not a loss.
    """
    losses: list[str] = []
    dropped: list[str] = []
    gains: list[str] = []
    changed: dict[str, dict] = {}
    changes: list[str] = []
    moved_only = 0
    attested = _attestation_index(cur)

    # --- coins that vanished -------------------------------------------------
    # A vanished coin is fine ONLY if a survivor absorbed it: either it is named
    # in a survivor's composed_of, or a survivor carries all of its source URLs.
    # That is exactly the dedup_final_foundations fold, and exactly what makes a
    # deliberate dedup distinguishable from data quietly falling on the floor.
    for cid in sorted(set(head) - set(cur)):
        was = head[cid]
        # A curator exclusion removes the coin ON PURPOSE, with a recorded
        # reason, and nothing absorbs it. Match on the vanished id itself or on
        # any of its members, since an exclusion names a SEED id (§9b) while the
        # final that disappears is keyed by its unified id.
        hit = ({cid} | set(was.get("composed_of") or [])) & set(excluded)
        if hit:
            dropped.append(f"{cid} ({was.get('nominal')} {was.get('year_label')}) "
                           f"— curator exclusion: {', '.join(sorted(hit))}")
            continue
        absorbed_by = None
        for sid, sc in cur.items():
            if cid in (sc.get("composed_of") or []):
                absorbed_by = sid
                break
            u = _urls(was)
            if u and u <= _urls(sc):
                absorbed_by = sid
                break
        if absorbed_by is None:
            # REDISTRIBUTION. A merge decision can DISSOLVE a class rather than
            # fold it whole: when the seeds of a `unified-*` foundation join
            # different new classes, each survivor receives only its share, so
            # no single survivor is a superset and the two tests above both
            # miss. That is not data falling on the floor — every citation is
            # still cited, just by more than one coin. Accept it only when the
            # survivors COVER the URL set completely; any URL that no survivor
            # carries is a real loss and still reports.
            # (Observed 2026-08-02: unified-kmk-155180's 13 KMM citations split
            # 6/7 between km-x005-chr-iv-1620 and km-82-chr-iv-1640 after the
            # abstain fix legitimately unblocked the merges.)
            want = _urls(was)
            if want:
                carriers = sorted(
                    sid for sid, sc in cur.items() if want & _urls(sc)
                )
                covered: set[str] = set()
                for sid in carriers:
                    covered |= _urls(cur[sid]) & want
                if covered == want:
                    absorbed_by = ", ".join(carriers)
        if absorbed_by:
            gains.append(f"{cid} folded into {absorbed_by}")
        else:
            losses.append(f"COIN GONE  {cid} ({was.get('nominal')} {was.get('year_label')}) "
                          f"— no survivor lists it in composed_of and none carries its sources")

    for cid in sorted(set(cur) - set(head)):
        gains.append(f"{cid} new")

    # --- field-level ---------------------------------------------------------
    for cid in sorted(set(head) & set(cur)):
        h, c = head[cid], cur[cid]
        moved: dict[str, tuple] = {}

        for f in SCALAR_FIELDS:
            hv, cv = h.get(f), c.get(f)
            if _key(hv) == _key(cv):
                continue
            moved[f] = (hv, cv)
            if hv not in (None, "", []) and cv in (None, "", []):
                losses.append(f"FIELD EMPTIED  {cid}.{f}: {hv!r} → empty")
            elif f in ("fuss", "phase") and cv == "seed_unsorted":
                losses.append(f"DEMOTED  {cid}.{f}: {hv!r} → seed_unsorted")

        for f in LIST_FIELDS:
            if f == "year_ranges":
                # Compare COVERED YEARS, not range tuples. The merger unions and
                # de-overlaps ranges across members (D19), so [1813,1813] joining
                # a class that also attests 1814-1815 legitimately re-shapes into
                # [1813,1815]: the tuple is gone, the year is not. Only a year
                # that nothing attests any more is a loss.
                hl = _covered_years(h.get(f))
                cl = _covered_years(c.get(f))
            else:
                hl = {_key(x) for x in _as_list(h.get(f))}
                cl = {_key(x) for x in _as_list(c.get(f))}
            if hl == cl:
                continue
            moved[f] = (len(hl), len(cl))
            dropped = hl - cl
            if dropped:
                if f == "year_ranges":
                    modified: set[str] = set()
                else:
                    # An entry whose identity is still here in the same number
                    # only had its VALUE corrected — a modification, not a loss.
                    hi = Counter(_ident(f, x) for x in _as_list(h.get(f)))
                    ci = Counter(_ident(f, x) for x in _as_list(c.get(f)))
                    ident_of = {_key(x): _ident(f, x) for x in _as_list(h.get(f))}
                    modified = {k for k in dropped
                                if ci[ident_of.get(k, k)] >= hi[ident_of.get(k, k)]}
                    for k in sorted(modified):
                        changes.append(
                            f"{cid}.{f}: value changed under {ident_of.get(k, k)[:60]}")
                gone = (dropped - modified) - attested[f]
                if gone:
                    losses.append(f"LIST SHRANK  {cid}.{f}: lost {len(gone)} "
                                  f"({sorted(gone)[0][:70]}…)")
                elif dropped - modified:
                    moved_only += 1

        hcat, ccat = _catalog_registers(h), _catalog_registers(c)
        for reg in sorted(set(hcat) | set(ccat)):
            hv, cv = hcat.get(reg, set()), ccat.get(reg, set())
            if hv == cv:
                continue
            moved.setdefault("catalog", []).append(reg)
            dropped = hv - cv
            if dropped:
                gone = {v for v in dropped if f"{reg}={v}" not in attested["catalog"]}
                if gone:
                    losses.append(
                        f"CATALOG SHRANK  {cid}.catalog.{reg}: lost {sorted(gone)}")
                else:
                    moved_only += 1

        if moved:
            changed[cid] = moved

    return {
        "entity": entity, "head": len(head), "cur": len(cur),
        "changed": changed, "losses": losses, "gains": gains,
        "moved": moved_only, "changes": changes, "dropped": dropped,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entity", help="single entity (default: every final yaml)")
    ap.add_argument("--base", default="HEAD", help="baseline git ref (default: HEAD)")
    ap.add_argument("--verbose", action="store_true", help="list every changed coin")
    args = ap.parse_args()

    final_dir = ROOT / FINAL_REL
    entities = ([args.entity] if args.entity
                else sorted(p.stem for p in final_dir.glob("*.yml")))

    total_loss: list[str] = []
    total_dropped: list[str] = []
    total_changed = total_gain = total_moved = 0
    total_changes: list[str] = []
    print(f"===== verify_reflow — working tree vs {args.base} =====\n")

    for ent in entities:
        r = compare_entity(ent, args.base)
        if not (r["changed"] or r["losses"] or r["gains"] or r.get("dropped")):
            continue
        total_changed += len(r["changed"])
        total_gain += len(r["gains"])
        total_loss += [f"[{ent}] {m}" for m in r["losses"]]
        total_dropped += [f"[{ent}] {m}" for m in r.get("dropped") or []]
        total_moved += r["moved"]
        total_changes += [f"[{ent}] {m}" for m in r.get("changes") or []]
        flag = "✗" if r["losses"] else "✓"
        print(f"{flag} {ent:38} coins {r['head']} → {r['cur']}   "
              f"changed {len(r['changed'])}   gains {len(r['gains'])}   "
              f"losses {len(r['losses'])}"
              + (f"   excluded {len(r['dropped'])}" if r.get("dropped") else "")
              + (f"   moved {r['moved']}" if r["moved"] else ""))
        if args.verbose:
            for cid, moved in r["changed"].items():
                print(f"      {cid}: {', '.join(sorted(moved))}")
            for g in r["gains"]:
                print(f"      + {g}")

    print(f"\nchanged coins: {total_changed}   gains: {total_gain}   "
          f"losses: {len(total_loss)}   moved: {total_moved}")
    if total_moved:
        print("  (moved = a value that left one coin and is still attested by "
              "another — a member changed class, not a loss)")

    if total_dropped:
        # Deliberate removals, printed so the gate still SHOWS what left the
        # render even though it does not block on it.
        print(f"\n----- CURATOR EXCLUSIONS ({len(total_dropped)}) — not losses -----")
        for m in total_dropped:
            print(f"  {m}")

    if total_changes:
        # Not a loss — the entry is still here, its reading was corrected. Worth
        # SEEING all the same: a measurement that silently changed value is the
        # kind of thing a re-flow should be deliberate about.
        print(f"\n----- CHANGED VALUES ({len(total_changes)}) — not losses -----")
        for m in total_changes:
            print(f"  {m}")

    if total_loss:
        print("\n----- LOSSES -----")
        for m in total_loss:
            print(f"  {m}")
        print("\nThe working tree is WORSE than the baseline on the lines above.")
        print("Fix them, or — if a removal is deliberate — make it a recognised")
        print("fold: the survivor must list the removed id in composed_of")
        print("(dedup_final_foundations.py does this).")
        return 1

    print("\n✓ no losses — every change is an addition or a recognised fold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
