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
    lost_final, reclassified, fewer_sources = [], [], []
    moved_entity, renamed_class, promoted, adopted = [], [], [], []
    for s in sorted(set(before) & set(after)):
        b, a = before[s], after[s]
        if b["final"] and not a["final"]:
            lost_final.append((s, b["final"]))

        # A seed has no classification of its own — it reads the fuss/phase of
        # the final it belongs to. So «this seed's fuss changed» means one of
        # two entirely different things, and they must not share a bucket:
        #
        #   the seed stayed in the SAME final → that final was RECLASSIFIED.
        #       Nobody moved the coin; its class's own value changed. This is
        #       the real risk (absorb re-derived it, or a curator edit was
        #       overwritten) and it fails the run.
        #
        #   the seed moved to a DIFFERENT final → it ADOPTED the host class's
        #       classification. That is merge mechanics, not reclassification:
        #       the host already carried that value. Usually it is a
        #       correction (an unphased or misphased record joining the class
        #       that has it right), but a bad merge drags a coin into the
        #       wrong class the same way — so it is reported for review, not
        #       silenced, and not counted as a loss.
        same_final = bool(b["final"]) and b["final"] == a["final"]
        klass_b = (b["fuss"], str(b["phase"]))
        klass_a = (a["fuss"], str(a["phase"]))
        if b["fuss"] and a["fuss"] and klass_b != klass_a:
            if same_final:
                reclassified.append((s, b["final"], f"{klass_b[0]}/{klass_b[1]}",
                                     f"{klass_a[0]}/{klass_a[1]}"))
            elif b["fuss"] == "seed_unsorted":
                # Sub-case of adoption worth its own line: the record had no
                # classification at all and gained one.
                promoted.append((s, f"{klass_b[0]}/{klass_b[1]}",
                                 f"{klass_a[0]}/{klass_a[1]}"))
            else:
                adopted.append((s, f"{klass_b[0]}/{klass_b[1]}",
                                f"{klass_a[0]}/{klass_a[1]}",
                                f"{b['final']} → {a['final']}"))

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
    report("RECLASSIFIED IN PLACE (same final, its own fuss/phase changed)",
           reclassified)
    report("FEWER SOURCES ON THE FINAL", fewer_sources)
    # Gains and expected churn — informational only.
    report("promoted out of seed_unsorted (gain, not loss)", promoted)
    report("adopted the host class's fuss/phase on merging (review, not loss)",
           adopted)
    report("moved to another entity file (informational)", moved_entity)
    report("class renamed, same coin (informational — id churn)", renamed_class)
    report("new seeds (informational)", added)

    losses = len(gone) + len(lost_final) + len(reclassified) + \
        len(fewer_sources)
    print(f"\n=== real losses: {losses} "
          f"(entity moves and class renames are not losses) ===")
    if losses:
        print("Before reporting these as fact, cross-check with "
              "audit_lost_citations.py and audit_curation_loss.py — if they "
              "disagree, this tool is wrong until proven otherwise.")
    return 1 if losses else 0


def _phase_windows() -> tuple[dict, dict]:
    """({location: {fuss: {phase_id: (from, to)}}}, {location: {entities}}).

    Phases are per-LOCATION by design (CLAUDE.md §7: Füße are global, phases
    are local), so the same fuss carries different windows on different pages.

    The second map is what keeps the comparison meaningful: a coin may only be
    judged against a page that actually SHOWS it, i.e. one whose
    `consumes_entities` includes one of the coin's issuing entities. Without
    that scope the check compares a Danish 9-Thaler coin of 1608 against
    Lübeck's 9_thaler window of 1776-1776 and calls it a finding — 648 such
    non-findings on the first run, against 22 real ones."""
    windows: dict = {}
    consumes: dict = {}
    for p in sorted((V2 / "locations").glob("*.yml")):
        d = _load(p)
        # An entry is either a bare entity or {entity, year_to} — a page can
        # consume an entity only up to a year (Denmark takes royal_holstein
        # to 1864, danish_norway to 1814). Keep the cutoff: a page that stops
        # showing an entity in 1814 has no business judging an 1842 coin.
        ents: dict = {}
        for e in d.get("consumes_entities") or []:
            if isinstance(e, dict):
                if e.get("entity"):
                    ents[e["entity"]] = e.get("year_to")
            elif e:
                ents[e] = None
        consumes[p.stem] = ents
        phases = d.get("phases")
        if not isinstance(phases, dict):
            continue
        windows[p.stem] = {
            fuss: {x.get("id"): (x.get("year_from"), x.get("year_to"))
                   for x in lst if isinstance(x, dict)}
            for fuss, lst in phases.items() if isinstance(lst, list)
        }
    return windows, consumes


def cmd_check_phases(args) -> int:
    """Report coins whose first year sits outside the window of the phase they
    are assigned to — as a QUESTION about the periodisation, never as a verdict
    about the coin.

    The direction matters and is the whole point of this check. Coins and
    ordinances dictate the years of a phase; the phase does not dictate what a
    coin may be (curator, 2026-07-29). CLAUDE.md §4 says it outright: «Phases
    and Füße are OUR structural annotations; years are THE SOURCE's factual
    record … Never quietly clip.» So a coin older than its phase's start is
    not a defect in the coin — it is a candidate for widening the phase, or a
    sign the phase assignment is wrong. Both are curator calls.

    Three separate findings, deliberately not merged into one «outside window»
    bucket:

      BEFORE THE FIRST PHASE / AFTER THE LAST — the fuss's periodisation may
          need extending to cover this coin. Ask the curator.
      NOT IN THIS PHASE (but inside the fuss's overall span) — the phase
          ASSIGNMENT is the thing in question, not the periodisation.
      year_last overshooting the phase end — NOT REPORTED AT ALL. §8.2 makes
          the FIRST year decide the phase and §4 explicitly permits the tail
          to run past the boundary.

    Always exits 0. Nothing here is a build error, and the tool must never
    imply that a coin's years should be trimmed to fit our taxonomy.
    """
    win, consumes = _phase_windows()
    extend, assign = [], []
    for p in sorted((V2 / "final").glob("*.yml")):
        for c in _load(p).get("coins") or []:
            fuss, phase, yf = c.get("fuss"), c.get("phase"), c.get("year_first")
            if not fuss or fuss == "seed_unsorted" or yf is None:
                continue
            ie = c.get("issuing_entity")
            entities = set(ie if isinstance(ie, list) else [ie] if ie else [])
            # Only pages that actually show this coin may judge its phase.
            shown_on = [
                loc for loc, ents in consumes.items()
                if any(e in ents and (ents[e] is None or yf <= ents[e])
                       for e in entities)
            ] or [p.stem]
            # phase may be scalar or per-location dict; a dict already names
            # its locations, so it needs no scoping.
            pairs = (list(phase.items()) if isinstance(phase, dict)
                     else [(loc, phase) for loc in shown_on])
            for loc, ph in pairs:
                fmap = win.get(loc, {}).get(fuss)
                if not fmap or ph not in fmap:
                    continue
                lo, hi = fmap[ph]
                if (lo is None or yf >= lo) and (hi is None or yf <= hi):
                    continue
                starts = [v[0] for v in fmap.values() if v[0] is not None]
                ends = [v[1] for v in fmap.values() if v[1] is not None]
                row = (c.get("id"), fuss, ph, str(c.get("year_label")),
                       f"window {lo}-{hi}", loc)
                if starts and yf < min(starts):
                    extend.append(row + ("earlier than the fuss's first phase",))
                elif ends and yf > max(ends):
                    extend.append(row + ("later than the fuss's last phase",))
                else:
                    assign.append(row)

    def show(title, rows, note):
        print(f"\n{title}: {len(rows)}")
        print(f"  {note}")
        for r in rows[:args.show]:
            print("   ", *r)
        if len(rows) > args.show:
            print(f"    … and {len(rows) - args.show} more")

    show("PERIODISATION MAY NEED WIDENING", extend,
         "The coin predates (or outlives) every phase of its fuss. Coins and "
         "ordinances set the years — ask the curator whether to widen the "
         "phase, and never trim the coin's years to fit.")
    show("PHASE ASSIGNMENT IN QUESTION", assign,
         "The year sits inside the fuss's overall span but not in the phase "
         "the coin is assigned to. Here the assignment is what to re-examine, "
         "not the periodisation.")
    print("\n(informational — exits 0; both lists are questions for the "
          "curator, not defects)")
    return 0


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
    cp = sub.add_parser("check-phases",
                        help="coins whose first year falls outside their "
                             "phase's window — questions for the curator")
    cp.add_argument("--show", type=int, default=25)
    cp.set_defaults(func=cmd_check_phases)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
