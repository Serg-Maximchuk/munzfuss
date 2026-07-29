#!/usr/bin/env python3
"""trace_coin.py — where is a coin RIGHT NOW, and what moved across a re-flow.

The V2 pipeline has three layers of ids and only ONE of them is stable:

  seed id      data/v2/seed/<src>/<entity>.yml     STABLE — never changes
  unified id   data/v2/seed_unified/<entity>.yml   DERIVED — rebuilt every merge
  final id     data/v2/final/<entity>.yml          DERIVED — follows the unified

A unified class is named `unified-<its top-authority member>` (V2_PIPELINE §5.2),
so the moment a merge decision adds a higher-authority member the class RENAMES:
`unified-dk-bruun-7749` becomes `unified-dk-hede-c7h8` while describing the very
same coin. Any before/after comparison keyed on unified or final ids is therefore
measuring with a ruler that changes length during the measurement — it reports
coins as "lost" that merely moved into a renamed class.

This tool exists because that mistake was made repeatedly (most recently
2026-07-29, three times in one session, each time from a fresh ad-hoc script in a
shell heredoc, each time producing a confident and WRONG loss report that a
dedicated auditor immediately contradicted). It keys everything on seed ids.

Usage
-----
  # Where is this coin? (accepts seed ids; several at once)
  trace_coin.py trace dk-tid-70716 dk-hede-c7h8

  # Before a re-flow:
  trace_coin.py snapshot /tmp/before.json
  #   ... run merge_seeds_cross_source.py --apply, absorb_seeds_into_final_v2.py --apply ...
  trace_coin.py snapshot /tmp/after.json
  trace_coin.py diff /tmp/before.json /tmp/after.json

Exit codes: 0 clean, 1 real losses found (seed vanished / final lost /
classification changed / sources dropped), 2 usage error.

NO SILENT FALLBACKS. A lookup that misses is reported as a miss; it never
degrades to "treat the id as its own member", which is exactly how the earlier
ad-hoc versions manufactured plausible nonsense.

Cross-check before believing a loss report: `audit_lost_citations.py` and
`audit_curation_loss.py` cover citations and field-level curation. If this tool
disagrees with them, assume THIS tool is wrong until proven otherwise.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
V2 = PROJECT_ROOT / "data" / "v2"


def _load(path: Path) -> dict:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:  # surface, never swallow
        raise SystemExit(f"cannot read {path}: {exc}")


def build_index() -> dict:
    """Read the three layers and return the seed-keyed placement index.

    Returns {seed_id: {source, seed_entity, unified, final, final_entity,
                       fuss, phase, sources}}.
    A seed with no unified class, or a unified class no final references, keeps
    None in that slot — that is a fact about the pipeline, not a lookup failure.
    """
    seeds: dict[str, dict] = {}
    for src_dir in sorted((V2 / "seed").iterdir()):
        if not src_dir.is_dir():
            continue
        for p in sorted(src_dir.glob("*.yml")):
            for c in _load(p).get("coins") or []:
                cid = c.get("id")
                if cid:
                    seeds[cid] = {"source": src_dir.name, "seed_entity": p.stem,
                                  "unified": None, "final": None,
                                  "final_entity": None, "fuss": None,
                                  "phase": None, "sources": None}

    # unified: seed -> class
    unified_members: dict[str, set[str]] = {}
    for p in sorted((V2 / "seed_unified").glob("*.yml")):
        for c in _load(p).get("coins") or []:
            uid = c.get("id")
            if not uid:
                continue
            members = set(c.get("composed_of") or [])
            unified_members[uid] = members
            for m in members:
                if m in seeds:
                    seeds[m]["unified"] = uid

    # final: composed_of holds unified ids, and sometimes seed ids directly
    for p in sorted((V2 / "final").glob("*.yml")):
        for c in _load(p).get("coins") or []:
            fid = c.get("id")
            if not fid:
                continue
            reached: set[str] = set()
            for ref in c.get("composed_of") or []:
                if ref in unified_members:
                    reached |= unified_members[ref]
                elif ref in seeds:
                    reached.add(ref)
            for s in reached:
                seeds[s].update(final=fid, final_entity=p.stem,
                                fuss=c.get("fuss"), phase=c.get("phase"),
                                sources=len(c.get("sources") or []))
    return seeds


def cmd_trace(args) -> int:
    idx = build_index()
    missing = [i for i in args.ids if i not in idx]
    for i in args.ids:
        rec = idx.get(i)
        if rec is None:
            print(f"{i}\n    NOT A SEED ID — not present in any "
                  f"data/v2/seed/<src>/<entity>.yml.")
            print("    (unified-* and final ids are derived and unstable; "
                  "trace by seed id)")
            continue
        print(f"{i}")
        print(f"    seed     {rec['source']} / {rec['seed_entity']}.yml")
        print(f"    unified  {rec['unified'] or '— none —'}")
        print(f"    final    {rec['final'] or '— none —'}"
              + (f"  [{rec['final_entity']}]" if rec['final_entity'] else ""))
        print(f"    class    {rec['fuss']}/{rec['phase']}"
              f"   sources={rec['sources']}")
    return 1 if missing else 0


def cmd_snapshot(args) -> int:
    idx = build_index()
    Path(args.out).write_text(json.dumps(idx, ensure_ascii=False, indent=1))
    placed = sum(1 for r in idx.values() if r["final"])
    print(f"snapshot → {args.out}   seeds={len(idx)}  with a final={placed}")
    return 0


def cmd_diff(args) -> int:
    before = json.loads(Path(args.before).read_text())
    after = json.loads(Path(args.after).read_text())

    gone = sorted(set(before) - set(after))
    added = sorted(set(after) - set(before))
    lost_final, fuss_changed, phase_changed, fewer_sources = [], [], [], []
    moved_entity, renamed_class = [], []
    for s in sorted(set(before) & set(after)):
        b, a = before[s], after[s]
        if b["final"] and not a["final"]:
            lost_final.append((s, b["final"]))
        if b["fuss"] and a["fuss"] and b["fuss"] != a["fuss"]:
            fuss_changed.append((s, b["fuss"], a["fuss"]))
        if b["phase"] and a["phase"] and b["phase"] != a["phase"]:
            phase_changed.append((s, b["phase"], a["phase"]))
        if (b["sources"] or 0) > (a["sources"] or 0) and a["final"]:
            fewer_sources.append((s, b["sources"], a["sources"]))
        if b["final_entity"] and a["final_entity"] and \
                b["final_entity"] != a["final_entity"]:
            moved_entity.append((s, b["final_entity"], a["final_entity"]))
        if b["final"] and a["final"] and b["final"] != a["final"]:
            renamed_class.append((s, b["final"], a["final"]))

    def report(title, rows, limit=args.show):
        print(f"\n{title}: {len(rows)}")
        for r in rows[:limit]:
            # rows are either a bare id or a tuple of columns; never splat a
            # str — that prints it one character at a time.
            print("   ", *(r if isinstance(r, tuple) else (r,)))
        if len(rows) > limit:
            print(f"    … and {len(rows) - limit} more")

    print(f"seeds: {len(before)} → {len(after)}")
    # Real losses — these fail the run.
    report("SEED VANISHED (no longer in any seed yaml)", gone)
    report("LOST ITS FINAL (had one, now none)", lost_final)
    report("FUSS CHANGED", fuss_changed)
    report("PHASE CHANGED", phase_changed)
    report("FEWER SOURCES ON THE FINAL", fewer_sources)
    # Expected churn — informational only.
    report("moved to another entity file (informational)", moved_entity)
    report("class renamed, same coin (informational — id churn)", renamed_class)
    report("new seeds (informational)", added)

    losses = len(gone) + len(lost_final) + len(fuss_changed) + \
        len(phase_changed) + len(fewer_sources)
    print(f"\n=== real losses: {losses} "
          f"(entity moves and class renames are not losses) ===")
    if losses:
        print("Before reporting these as fact, cross-check with "
              "audit_lost_citations.py and audit_curation_loss.py — if they "
              "disagree, this tool is wrong until proven otherwise.")
    return 1 if losses else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("trace", help="locate coins by SEED id")
    t.add_argument("ids", nargs="+")
    t.set_defaults(func=cmd_trace)
    s = sub.add_parser("snapshot", help="write the seed-keyed placement index")
    s.add_argument("out")
    s.set_defaults(func=cmd_snapshot)
    d = sub.add_parser("diff", help="compare two snapshots (seed-keyed)")
    d.add_argument("before")
    d.add_argument("after")
    d.add_argument("--show", type=int, default=15)
    d.set_defaults(func=cmd_diff)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
