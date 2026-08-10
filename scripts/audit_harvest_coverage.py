#!/usr/bin/env python3
"""Harvest-coverage matrix — which POLITY has been harvested from which SOURCE.

Answers the question that is otherwise easy to lose track of across sessions:
*which locations have we actually pulled from each source, and which have we
silently never touched?* Sources arrive location-by-location over many sessions,
and a gap left behind in one session looks identical to a deliberate exclusion
in the next unless it is written down.

Regenerate (never hand-edit the output — it goes stale immediately)::

    python scripts/audit_harvest_coverage.py            # rewrite docs/HARVEST_COVERAGE.md
    python scripts/audit_harvest_coverage.py --stdout   # print, don't write

**What the numbers mean, and what they do NOT.** A cell counts the coin entries
this project currently holds for that (polity, source) pair. It is a presence
and volume signal — NOT a completeness claim. A non-zero cell does not mean the
source was exhausted for that polity, and this script deliberately does not try
to establish that: verifying exhaustiveness needs a per-source enumeration walk
and is a separate, much more expensive job. Read a cell as «we have pulled some
of this», and a blank as «we have pulled none of this».

Two layers are reported because the pipeline has two, and conflating them would
hide real work:

1. **Seeded** — `data/v2/seed/<source>/<entity>.yml`. Entity-keyed, so the
   polity attribution is the pipeline's own and needs no guessing here.
2. **Harvested but not yet seeded** — raw Phase-1/2 cache for sources that have
   no seed builder yet. The polity attribution for those is provisional, mapped
   from the source's own scope names, and is flagged as such in the output.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import NGC_CACHE, PROJECT_ROOT  # noqa: E402

SEED_ROOT = PROJECT_ROOT / "data" / "v2" / "seed"
ENTITIES_YML = PROJECT_ROOT / "data" / "i18n" / "issuing_entities.yml"
OUT = PROJECT_ROOT / "docs" / "HARVEST_COVERAGE.md"

# Sources harvested but NOT yet through a seed builder. The scope->entity map is
# PROVISIONAL — it records the walk's own region names, which is the provenance a
# future seed builder will route on. Delete a block once its builder exists and
# the source starts showing up in the seeded matrix instead.
UNSEEDED = {
    "ngc": {
        "cache_root": NGC_CACHE,
        "note": "no build_ngc_seed.py yet; polity mapped from NGC region name",
        "scopes": {
            "luebeck": ["hanseatic_lubeck", "fuerstbisthum_luebeck"],
            "denmark": ["danish_realm", "danish_norway", "royal_holstein"],
            "schleswig_holstein": ["royal_holstein", "provisional_govt",
                                   "prussian_province"],
            "schleswig_holstein_gottorp": ["gottorp_duchy"],
            "schleswig_holstein_sonderburg": ["sonderburg_duchy"],
            "schleswig_holstein_ploen": ["norburg_plon_duchy"],
            "schleswig_holstein_norburg": ["norburg_plon_duchy"],
            "schleswig_holstein_glucksburg": ["glucksburg_duchy"],
            "schaumburg_pinneberg": ["schauenburg_pinneberg"],
            "rantzau": ["rantzau_county"],
        },
    },
}

# Gaps we KNOW about and have consciously deferred. Listing them is the point of
# this file: an undocumented gap is indistinguishable from a deliberate choice.
KNOWN_GAPS = [
    ("ngc", "grafschaft_schaumburg",
     "NGC regions SCHAUMBURG-LIPPE + SCHAUMBURG-HESSEN never walked "
     "(post-1640 partition lines). Deferred 2026-08-10."),
    ("ngc", "hanseatic_lubeck",
     "NGC region LUBECK (no umlaut, 179 date-rows) never walked — it is a "
     "SEPARATE region from LÜBECK, see SOURCES.md §13.13(a)."),
    ("ngc", "*",
     "Only Lübeck, Denmark and the Schleswig-Holstein polities walked. Hamburg "
     "(1112 rows), Bremen (607), Oldenburg (240), Lauenburg (17), "
     "Brunswick-Lüneburg cluster, Hesse-Cassel and Osnabrück all untouched."),
]


def load_entities() -> list[str]:
    d = yaml.safe_load(ENTITIES_YML.read_text(encoding="utf-8"))
    return list((d.get("entities") or d).keys())


def _years(coins) -> tuple[int | None, int | None]:
    lo = hi = None
    for c in coins:
        for k, cmpf in (("year_first", min), ("year_last", max)):
            v = c.get(k)
            if isinstance(v, int):
                if k == "year_first":
                    lo = v if lo is None else min(lo, v)
                else:
                    hi = v if hi is None else max(hi, v)
    return lo, hi


def scan_seeded() -> tuple[dict, dict, list[str]]:
    counts: dict[tuple[str, str], int] = {}
    span: dict[str, tuple[int | None, int | None]] = {}
    sources = sorted(p.name for p in SEED_ROOT.iterdir() if p.is_dir())
    for src in sources:
        for f in sorted((SEED_ROOT / src).glob("*.yml")):
            ent = f.stem
            d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
            coins = d.get("coins") or []
            if not coins:
                continue
            counts[(ent, src)] = len(coins)
            lo, hi = _years(coins)
            plo, phi = span.get(ent, (None, None))
            span[ent] = (min(x for x in (lo, plo) if x is not None) if (lo or plo) else None,
                         max(x for x in (hi, phi) if x is not None) if (hi or phi) else None)
    return counts, span, sources


def scan_unseeded() -> tuple[dict, dict]:
    counts: dict[tuple[str, str], int] = defaultdict(int)
    span: dict[str, tuple[int | None, int | None]] = {}
    for src, cfg in UNSEEDED.items():
        root: Path = cfg["cache_root"]
        if not root.exists():
            continue
        for scope, ents in cfg["scopes"].items():
            files = sorted((root / scope).glob("cuid_*.parsed.json")) \
                if (root / scope).exists() else []
            if not files:
                continue
            recs = [json.loads(p.read_text(encoding="utf-8")) for p in files]
            lo = min((r["year_first"] for r in recs if r.get("year_first")), default=None)
            hi = max((r["year_last"] for r in recs if r.get("year_last")), default=None)
            for ent in ents:
                # A scope covering several polities is counted once per polity and
                # marked '~' in the output — the split is the seed builder's job,
                # so presenting it as an exact per-polity figure would be a lie.
                counts[(ent, src)] += len(recs)
                plo, phi = span.get(ent, (None, None))
                span[ent] = (min(x for x in (lo, plo) if x is not None) if (lo or plo) else None,
                             max(x for x in (hi, phi) if x is not None) if (hi or phi) else None)
    return dict(counts), span


def _span_str(sp) -> str:
    lo, hi = sp if sp else (None, None)
    if lo is None and hi is None:
        return "—"
    return f"{lo or '?'}–{hi or '?'}"


def render() -> str:
    ents = load_entities()
    seeded, sspan, sources = scan_seeded()
    unseeded, uspan = scan_unseeded()
    usources = sorted(UNSEEDED)

    multi = {s for cfg in UNSEEDED.values() for s, e in cfg["scopes"].items() if len(e) > 1}

    L: list[str] = []
    A = L.append
    A("# Harvest coverage — polities × sources")
    A("")
    A("> **GENERATED — do not hand-edit.** Regenerate with "
      "`python scripts/audit_harvest_coverage.py` after any harvest.")
    A(f"> Last generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
    A("")
    A("Tracks **which polity has been harvested from which source**, so a location "
      "nobody has touched yet is visible instead of being silently forgotten.")
    A("")
    A("**A number is a presence-and-volume signal, NOT a completeness claim.** It "
      "counts what we currently hold for that pair. A non-zero cell does *not* mean "
      "the source was exhausted for that polity — verifying that needs a per-source "
      "enumeration walk and is deliberately out of scope here. Read a cell as «we "
      "have pulled some of this»; read a blank as «we have pulled none of this».")
    A("")
    A("## 1. Seeded — `data/v2/seed/<source>/<entity>.yml`")
    A("")
    A("Entity-keyed, so the polity attribution is the pipeline's own.")
    A("")
    A("| polity | " + " | ".join(sources) + " | years |")
    A("|---|" + "---:|" * len(sources) + "---|")
    for e in ents:
        row = [f"`{e}`"]
        tot = 0
        for s in sources:
            n = seeded.get((e, s), 0)
            tot += n
            row.append(str(n) if n else "")
        row.append(_span_str(sspan.get(e)))
        if tot:
            A("| " + " | ".join(row) + " |")
    A("")
    never = [e for e in ents if not any(seeded.get((e, s)) for s in sources)]
    if never:
        A(f"**Not in any seed ({len(never)}):** " + ", ".join(f"`{e}`" for e in never))
        A("")

    A("## 2. Harvested but NOT yet seeded")
    A("")
    A("Raw Phase-1/2 cache for sources with no seed builder yet. Polity attribution "
      "here is **provisional** — mapped from the source's own scope names, not from "
      "the pipeline. `~` marks a scope covering several polities, counted once "
      "against each: splitting it is the seed builder's job, and presenting an exact "
      "per-polity figure before that would be invented precision.")
    A("")
    A("A year span may overshoot a harvest's stated window (NGC was taken at "
      "1480–1914, yet shows 1918). That is not a filter failure: a type whose "
      "issue range straddles the boundary is kept whole, because §4 forbids "
      "truncating a source's years to fit our own window.")
    A("")
    for s in usources:
        A(f"*{s}* — {UNSEEDED[s]['note']}")
    A("")
    A("| polity | " + " | ".join(usources) + " | years |")
    A("|---|" + "---:|" * len(usources) + "---|")
    for e in ents:
        if not any(unseeded.get((e, s)) for s in usources):
            continue
        row = [f"`{e}`"]
        for s in usources:
            n = unseeded.get((e, s), 0)
            if not n:
                row.append("")
                continue
            shared = any(e in v and len(v) > 1
                         for sc, v in UNSEEDED[s]["scopes"].items() if sc in multi)
            row.append(f"~{n}" if shared else str(n))
        row.append(_span_str(uspan.get(e)))
        A("| " + " | ".join(row) + " |")
    A("")
    A("## 3. Known gaps — deferred on purpose, not forgotten")
    A("")
    A("An undocumented gap is indistinguishable from a deliberate choice, which is "
      "why these are written down rather than left to be rediscovered.")
    A("")
    A("| source | polity | gap |")
    A("|---|---|---|")
    for src, ent, why in KNOWN_GAPS:
        A(f"| {src} | {'*(several)*' if ent == '*' else f'`{ent}`'} | {why} |")
    A("")
    A("---")
    A("")
    A("Per-source access notes, quirks and known issues: `docs/SOURCES.md`. "
      "How to add a new harvester: `docs/HARVEST_GUIDE.md`.")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stdout", action="store_true")
    args = ap.parse_args()
    text = render()
    if args.stdout:
        print(text)
    else:
        OUT.write_text(text, encoding="utf-8")
        print(f"wrote {OUT.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
