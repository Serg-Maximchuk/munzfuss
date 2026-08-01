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
    (a fold is recognised by the survivor listing it in `composed_of`, or by the
    survivor having absorbed its source URLs);
  * a scalar field that had a value at HEAD and is now empty;
  * a list field (sources / weight_rough_g / fineness / diameter_mm / catalog
    registers) that lost an entry;
  * a change of `fuss` or `phase` from a real assignment back to `seed_unsorted`.

Everything else — new coins, new readings, a scalar filling in, a catalogue
register gaining a value — is a GAIN and never blocks.

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
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
FINAL_REL = "data/v2/final"

# Fields whose disappearance or shrinkage is a real regression. `note` and the
# prose fields are excluded on purpose — they are curator-edited and a rewrite
# legitimately replaces them.
SCALAR_FIELDS = (
    "nominal", "ruler", "year_label", "year_first", "year_last",
    "mint", "metal", "kind", "fuss", "phase", "mintmaster",
)
LIST_FIELDS = ("sources", "weight_rough_g", "fineness", "diameter_mm", "year_ranges")


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
    return json.dumps(v, sort_keys=True, default=str)


def _catalog_registers(coin: dict) -> dict[str, set[str]]:
    """catalog → {register: {values}}, so a register losing a value is visible."""
    out: dict[str, set[str]] = {}
    for reg, val in (coin.get("catalog") or {}).items():
        out[reg] = {_key(x) for x in _as_list(val)}
    return out


def compare_entity(entity: str, base: str) -> dict:
    """Load both sides for `entity` and delegate to `compare_coins`."""
    rel = f"{FINAL_REL}/{entity}.yml"
    head = _coins(_git_show(base, rel))
    path = ROOT / rel
    cur = _coins(yaml.safe_load(path.read_text()) if path.exists() else None)
    return compare_coins(entity, head, cur)


def compare_coins(entity: str, head: dict[str, dict], cur: dict[str, dict]) -> dict:
    """Classify every difference between two {id: coin} maps as gain or loss.

    Split out from the loading so the classification — the part with judgement
    in it — is directly testable without a git tree or a filesystem.
    """
    losses: list[str] = []
    gains: list[str] = []
    changed: dict[str, dict] = {}

    # --- coins that vanished -------------------------------------------------
    # A vanished coin is fine ONLY if a survivor absorbed it: either it is named
    # in a survivor's composed_of, or a survivor carries all of its source URLs.
    # That is exactly the dedup_final_foundations fold, and exactly what makes a
    # deliberate dedup distinguishable from data quietly falling on the floor.
    for cid in sorted(set(head) - set(cur)):
        was = head[cid]
        absorbed_by = None
        for sid, sc in cur.items():
            if cid in (sc.get("composed_of") or []):
                absorbed_by = sid
                break
            u = _urls(was)
            if u and u <= _urls(sc):
                absorbed_by = sid
                break
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
            hl = {_key(x) for x in _as_list(h.get(f))}
            cl = {_key(x) for x in _as_list(c.get(f))}
            if hl == cl:
                continue
            moved[f] = (len(hl), len(cl))
            dropped = hl - cl
            if dropped:
                losses.append(f"LIST SHRANK  {cid}.{f}: lost {len(dropped)} "
                              f"({sorted(dropped)[0][:70]}…)")

        hcat, ccat = _catalog_registers(h), _catalog_registers(c)
        for reg in sorted(set(hcat) | set(ccat)):
            hv, cv = hcat.get(reg, set()), ccat.get(reg, set())
            if hv == cv:
                continue
            moved.setdefault("catalog", []).append(reg)
            if hv - cv:
                losses.append(f"CATALOG SHRANK  {cid}.catalog.{reg}: lost {sorted(hv - cv)}")

        if moved:
            changed[cid] = moved

    return {
        "entity": entity, "head": len(head), "cur": len(cur),
        "changed": changed, "losses": losses, "gains": gains,
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
    total_changed = total_gain = 0
    print(f"===== verify_reflow — working tree vs {args.base} =====\n")

    for ent in entities:
        r = compare_entity(ent, args.base)
        if not (r["changed"] or r["losses"] or r["gains"]):
            continue
        total_changed += len(r["changed"])
        total_gain += len(r["gains"])
        total_loss += [f"[{ent}] {m}" for m in r["losses"]]
        flag = "✗" if r["losses"] else "✓"
        print(f"{flag} {ent:38} coins {r['head']} → {r['cur']}   "
              f"changed {len(r['changed'])}   gains {len(r['gains'])}   "
              f"losses {len(r['losses'])}")
        if args.verbose:
            for cid, moved in r["changed"].items():
                print(f"      {cid}: {', '.join(sorted(moved))}")
            for g in r["gains"]:
                print(f"      + {g}")

    print(f"\nchanged coins: {total_changed}   gains: {total_gain}   "
          f"losses: {len(total_loss)}")

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
