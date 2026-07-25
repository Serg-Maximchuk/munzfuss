#!/usr/bin/env python3
"""Detect final entries carrying PHANTOM source citations (the inverse of
`audit_lost_citations.py`).

WHY THIS EXISTS — absorb DELIBERATELY unions the foundation entry's own
`sources` list rather than re-deriving purely from `composed_of` (see the
comment above the `_collect_sources(members)` call in
`absorb_seeds_into_final_v2.py`). That preserves V1-curator citations with no
seed equivalent (an earlier `skip_first_list=True` attempt dropped 471 of them
across 224 entries and was reverted) — at the cost of letting a citation
SURVIVE a split: when the curator splits seed X out of a merge group, X's URL
stays in the final's `sources` forever. Confirmed case: `unified-dk-hede-f3h39`
kept `en.ucoin.net/…?tid=145589` after `dk-tid-145589` was split out
(commit f0e4982).

DETECTION — a citation is a phantom CANDIDATE when:
  * its URL is owned by exactly ONE seed entry across `data/v2/seed/*/*.yml`,
  * that owner seed is NOT in the flagged final's cluster
    (composed_of → seed_unified.composed_of → seed ids),
  * some OTHER final legitimately owns it (the owner seed IS in that final's
    cluster) — i.e. the citation has a rightful home elsewhere.

THIS IS A HEURISTIC, NOT A VERDICT. Several classes of legitimate citation
match the raw shape; each is recognised and reported separately (see
`--explain`). Read the class notes before acting on anything.

Usage:
    .venv/bin/python scripts/maintenance/audit_phantom_citations.py
    .venv/bin/python scripts/maintenance/audit_phantom_citations.py --json
    .venv/bin/python scripts/maintenance/audit_phantom_citations.py --entity danish_norway
    .venv/bin/python scripts/maintenance/audit_phantom_citations.py --class suspect --samples 5
    .venv/bin/python scripts/maintenance/audit_phantom_citations.py --explain

    # catalog-index mode — the SAME absorb-union strands catalogue numbers,
    # not only URLs (see the block comment above `CAT_FIELDS`):
    .venv/bin/python scripts/maintenance/audit_phantom_citations.py --catalog
    .venv/bin/python scripts/maintenance/audit_phantom_citations.py --catalog \
        --entity danish_norway --class suspect --json

READ-ONLY. There is deliberately no `--apply`: a wrong deletion destroys
provenance and silently regresses CLAUDE.md §0. Remediation is surgical and
curator-approved, per-entry.
Exit 0 always (report tool).
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

_L = getattr(yaml, "CSafeLoader", yaml.SafeLoader)

# Hosts where one URL == one cited record (mirrors `_collect_sources`'s
# `_SINGLE_PAGE_HOSTS` in merge_seeds_cross_source.py). Only these can be
# reasoned about as «owned by one seed»; a multi-record source (Bruun PDF —
# one URL, hundreds of lots) legitimately appears under many finals.
SINGLE_PAGE_HOSTS = (
    "danskmoent.dk",
    "en.numista.com",
    "en.ucoin.net",
    "numismaster.com",
    "ikmk.smb.museum",
)

# Museum specimen hosts — a §9a multi-specimen type entry legitimately carries
# many specimen URLs without each specimen being its own seed id.
MUSEUM_HOSTS = ("natmus.dk", "samlinger.natmus.dk", "ikmk.smb.museum")

CLASSES = ("suspect", "fp_self_named", "fp_museum_specimen",
           "fp_multi_record", "fp_shared_owner", "undecidable")


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def _load_seeds() -> tuple[dict, dict, dict]:
    """→ (url → {seed_id}, seed_id → source_dir, seed_id → catalog dict)."""
    url_owners: dict[str, set] = defaultdict(set)
    seed_src: dict[str, str] = {}
    seed_cat: dict[str, dict] = {}
    for path in sorted(glob.glob(str(ROOT / "data/v2/seed/*/*.yml"))):
        src = Path(path).parent.name
        doc = yaml.load(open(path), Loader=_L) or {}
        for c in doc.get("coins") or []:
            cid = c.get("id")
            if not cid:
                continue
            seed_src[cid] = src
            seed_cat[cid] = c.get("catalog") or {}
            for s in c.get("sources") or []:
                if isinstance(s, dict) and s.get("url"):
                    url_owners[s["url"]].add(cid)
    return url_owners, seed_src, seed_cat


def _load_unified() -> dict:
    out = {}
    for path in sorted(glob.glob(str(ROOT / "data/v2/seed_unified/*.yml"))):
        for c in (yaml.load(open(path), Loader=_L) or {}).get("coins", []):
            if c.get("id"):
                out[c["id"]] = c
    return out


def _load_finals() -> list[tuple[str, dict]]:
    """ALWAYS every entity.

    `--entity` filters the REPORT, never the load: the «does another final
    rightfully own this?» index must be built over the whole corpus. Scoping
    the index to one entity produced a false `undecidable` on
    `unified-dk-hede-nc5h16` / ucoin tid-101249, whose rightful home
    (`unified-dk-bruun-6808`) lives in danish_realm.
    """
    out = []
    for path in sorted(glob.glob(str(ROOT / "data/v2/final/*.yml"))):
        ent = Path(path).stem
        for c in (yaml.load(open(path), Loader=_L) or {}).get("coins", []):
            out.append((ent, c))
    return out


def _load_no_merges() -> dict:
    """entity → set of frozenset PAIRS recorded in a `no_merges` block.

    PAIRWISE on purpose. An earlier version keyed on «owner seed appears
    anywhere in no_merges», which mislabels the `km-68-chr-iv-1619` class:
    `dk-numista-142850` IS blocked — but from `dk-hede-c4h116a/b`, NOT from
    the KM-68 final it is cited on. The block says nothing about that final,
    so the citation is not evidenced as stale.
    """
    out: dict[str, set] = defaultdict(set)
    for path in sorted(glob.glob(str(ROOT / "data/v2/merge_decisions/*.yml"))):
        ent = Path(path).stem
        doc = yaml.load(open(path), Loader=_L) or {}
        for key in ("no_merges", "splits"):
            for item in (doc.get(key) or []):
                if not isinstance(item, dict):
                    continue
                ms = [v for v in (item.get("members") or []) if isinstance(v, str)]
                for i, a in enumerate(ms):
                    for b in ms[i + 1:]:
                        out[ent].add(frozenset((a, b)))
    return out


def _split_evidenced(owner: str, cluster: set, pairs: set) -> bool:
    """True when a no_merges block blocks the owner from THIS final's cluster."""
    return any(frozenset((owner, m)) in pairs for m in cluster)


# ---------------------------------------------------------------------------
# Cluster derivation
# ---------------------------------------------------------------------------

def _cluster(coin: dict, uni: dict) -> set:
    """Seed ids legitimately backing this final entry."""
    seeds: set = set()
    for m in coin.get("composed_of") or []:
        seeds.add(m)
        if m.startswith("unified-"):
            seeds.add(m[len("unified-"):])
        mu = uni.get(m)
        if mu:
            for sm in mu.get("composed_of") or []:
                seeds.add(sm)
    return seeds


_ID_TAIL = re.compile(r"[a-z]*-?(\d{4,})$")


def _self_named(final_id: str, owner_seed: str) -> bool:
    """FP class (a): the final's own id encodes the owner specimen.

    V1-carryover finals are named after the specimen they ARE
    (`hs-ikmk-18285754`, `bruun-14681-christian-glb-1672`,
     `km-651-1`, `dk-tid-97535`). The composed_of-derived cluster does not
    contain the same-named seed id, so the raw scan flags them — wrongly.
    Recognised by a shared numeric token of >=4 digits.
    """
    fin_nums = set(re.findall(r"\d{4,}", final_id))
    own_nums = set(re.findall(r"\d{4,}", owner_seed))
    if fin_nums & own_nums:
        return True
    # short-token forms: `km-651-1` vs `km-651-1-…`
    return final_id in owner_seed or owner_seed in final_id


def classify(url: str, owners: set, cluster: set, final_id: str,
             has_rightful_home: bool) -> str:
    if url.lower().endswith(".pdf"):
        return "fp_multi_record"
    if len(owners) > 1:
        return "fp_shared_owner"
    owner = next(iter(owners))
    if owner in cluster:
        return None  # not flagged at all
    if _self_named(final_id, owner):
        return "fp_self_named"
    if any(h in url for h in MUSEUM_HOSTS):
        return "fp_museum_specimen"
    if not any(h in url for h in SINGLE_PAGE_HOSTS):
        return "fp_multi_record"
    if not has_rightful_home:
        return "undecidable"
    return "suspect"


# ---------------------------------------------------------------------------
# Catalog-field scan (`--catalog`)
# ---------------------------------------------------------------------------
#
# WHY — the same absorb-union that strands a `sources[]` URL also strands a
# CATALOG INDEX: `_enrich_final_entry` unions the foundation's stored catalog
# with the cluster's, so a value that entered the final under an EARLIER merge
# state survives every regeneration. Confirmed cases (commit 5cd6961):
# `unified-dk-hede-nc5h11` carried `km: ['119','121']` where its cluster has
# only `121`; `unified-dk-hede-nc5h13` carried `['121','122']` for cluster
# `122`. A stranded index is WORSE than a stranded URL — it silently changes
# what coin the entry claims to BE.
#
# FALSE-POSITIVE CLASSES excluded before anything is flagged:
#   fp_curation_hold  — the field is listed in the entry's `_curation_holds`;
#                       a held field is curator-authoritative (may come from a
#                       paper source with no seed equivalent). NEVER a phantom.
#   fp_no_seed_backing— the entry's whole cluster carries NO value for this
#                       field: the value is curator-added, not stranded.
#   fp_subvariant     — the value is a sub-index of a base the cluster does
#                       carry (`138.2` under `138`, `16A` under `16`), i.e.
#                       exactly the §9.4 item-4 / §9a accumulation the project
#                       mandates.
#   fp_dict_form      — dict-form `km` (cross-Krause-volume accumulation, the
#                       c5h125 / c7h13 pattern, `_merge_km_field`). Correct
#                       data by construction.
#   undecidable       — absent from the cluster, but NO other final in the SAME
#                       entity owns it as its own index. A bare absence is a
#                       weak signal (a §9a fold whose donor foundation is gone
#                       leaves exactly this shape). Not actionable alone.
#   suspect           — absent from the cluster AND another final in the same
#                       entity carries it. That «someone else owns this as
#                       their index» test is the strong signal — the nc5h11 /
#                       nc5h13 / nc5h16 shape.
#
# Cross-entity ownership is NOT counted: per §9.4's caveat, Krause numbering
# restarts per volume, so `KM 120` in danish_norway and `KM 120` in
# gottorp_duchy are unrelated coins, not evidence of anything.

CAT_FIELDS = ("km", "hede", "sieg", "schou", "fr", "nmd", "numista",
              "bruun_collection_id", "others")

# Builders disagree on a few field names; treat each group as one field when
# unioning the cluster, so `fr` on a final is backed by `friedberg` on a seed.
CAT_ALIASES = {"fr": ("fr", "friedberg"), "dav": ("dav", "davenport")}

CAT_CLASSES = ("suspect", "undecidable", "fp_subvariant", "fp_dict_form",
               "fp_curation_hold", "fp_no_seed_backing")


def _vals(cat: dict, field: str) -> list[str]:
    """Scalar/list catalog value → list of normalised strings ('' if absent)."""
    out: list[str] = []
    for name in CAT_ALIASES.get(field, (field,)):
        v = cat.get(name)
        if v is None:
            continue
        if isinstance(v, dict):          # cross-volume dict-form
            for sub in v.values():
                out += [str(x).strip() for x in
                        (sub if isinstance(sub, list) else [sub]) if x is not None]
            continue
        out += [str(x).strip() for x in
                (v if isinstance(v, list) else [v]) if x is not None]
    return [x for x in out if x]


_BASE = re.compile(r"^(\d+)")


def _shares_base(value: str, cluster_vals: list[str]) -> bool:
    """`138.2` vs `138` / `16A` vs `16` — sub-variant of a base the cluster has."""
    m = _BASE.match(value)
    if not m:
        return False
    base = m.group(1)
    for cv in cluster_vals:
        cm = _BASE.match(cv)
        if not cm:
            continue
        if cm.group(1) != base:
            continue
        # same numeric base, one is a strict extension of the other
        if value.startswith(cv) or cv.startswith(value):
            return True
    return False


def _cat_cluster_vals(coin: dict, uni: dict, seed_cat: dict,
                      field: str) -> list[str]:
    """Union of `field` across seed_unified members + their member seeds."""
    out: list[str] = []
    for m in coin.get("composed_of") or []:
        mu = uni.get(m)
        if mu:
            out += _vals(mu.get("catalog") or {}, field)
            for sm in mu.get("composed_of") or []:
                out += _vals(seed_cat.get(sm) or {}, field)
        out += _vals(seed_cat.get(m) or {}, field)
        if m.startswith("unified-"):
            out += _vals(seed_cat.get(m[len("unified-"):]) or {}, field)
    return out


def scan_catalog(finals: list, uni: dict, seed_cat: dict) -> dict:
    # Pass 1 — per entity, which final(s) carry each (field, value).
    owners: dict[tuple, list[str]] = defaultdict(list)
    for ent, c in finals:
        cat = c.get("catalog") or {}
        for f in CAT_FIELDS:
            for v in _vals(cat, f):
                owners[(ent, f, v)].append(c.get("id") or "")

    findings: dict[str, list] = defaultdict(list)
    for ent, c in finals:
        cat = c.get("catalog") or {}
        holds = set(c.get("_curation_holds") or [])
        for f in CAT_FIELDS:
            fin_vals = _vals(cat, f)
            if not fin_vals:
                continue
            cl_vals = _cat_cluster_vals(c, uni, seed_cat, f)
            for v in fin_vals:
                if v in cl_vals:
                    continue
                if f in holds or "catalog" in holds:
                    k = "fp_curation_hold"
                elif isinstance(cat.get(f), dict):
                    k = "fp_dict_form"
                elif not cl_vals:
                    k = "fp_no_seed_backing"
                elif _shares_base(v, cl_vals):
                    k = "fp_subvariant"
                else:
                    other = [o for o in owners[(ent, f, v)]
                             if o != (c.get("id") or "")]
                    k = "suspect" if other else "undecidable"
                findings[k].append({
                    "entity": ent, "final_id": c.get("id"), "field": f,
                    "value": v, "final_values": fin_vals,
                    "cluster_values": sorted(set(cl_vals)),
                    "other_owners": [o for o in owners[(ent, f, v)]
                                     if o != (c.get("id") or "")],
                    "nominal": c.get("nominal"),
                    "year_label": c.get("year_label"),
                })
    return findings


def report_catalog(findings: dict, klass: str | None, samples: int) -> None:
    for k in CAT_CLASSES:
        print(f"{k:24s} {len(findings.get(k, [])):5d}")
    print()
    for k in ([klass] if klass else ["suspect", "undecidable"]):
        rows = findings.get(k, [])
        if not rows:
            continue
        by_field = defaultdict(int)
        for r in rows:
            by_field[r["field"]] += 1
        print(f"--- {k} ({len(rows)}) by field: "
              + ", ".join(f"{f}={n}" for f, n in
                          sorted(by_field.items(), key=lambda x: -x[1])))
        for r in rows[:samples]:
            print(f"    [{r['entity']}] {r['final_id']}  "
                  f"{r['nominal']} {r['year_label']}")
            print(f"      {r['field']}: final={r['final_values']}  "
                  f"cluster={r['cluster_values']}")
            print(f"      phantom value {r['value']!r}; "
                  f"also carried by: {', '.join(r['other_owners']) or '(none)'}")
        print()


# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--entity")
    ap.add_argument("--class", dest="klass")
    ap.add_argument("--catalog", action="store_true",
                    help="scan catalog index fields instead of sources[]")
    ap.add_argument("--samples", type=int, default=3)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--explain", action="store_true")
    args = ap.parse_args()

    if args.explain:
        print(__doc__)
        return 0

    url_owners, seed_src, seed_cat = _load_seeds()
    uni = _load_unified()
    finals = _load_finals()
    no_merges = _load_no_merges()

    if args.catalog:
        findings = scan_catalog(finals, uni, seed_cat)
        if args.entity:
            findings = {k: [r for r in v if r["entity"] == args.entity]
                        for k, v in findings.items()}
        if args.json:
            print(json.dumps(findings if not args.klass
                             else {args.klass: findings.get(args.klass, [])},
                             indent=2, ensure_ascii=False))
            return 0
        print(f"finals scanned: {len(finals)}   "
              f"fields: {', '.join(CAT_FIELDS)}\n")
        report_catalog(findings, args.klass, args.samples)
        return 0

    # Pass 1 — cluster per final; then which finals rightfully own each seed.
    clusters: list[tuple[str, dict, set]] = []
    seed_home: dict[str, list[str]] = defaultdict(list)
    for ent, c in finals:
        cl = _cluster(c, uni)
        clusters.append((ent, c, cl))
        for s in cl:
            seed_home[s].append(f"{ent}:{c.get('id')}")

    findings: dict[str, list] = defaultdict(list)
    for ent, c, cl in clusters:
        fid = c.get("id") or ""
        for s in c.get("sources") or []:
            if not isinstance(s, dict):
                continue
            url = s.get("url") or ""
            if not url:
                continue
            owners = url_owners.get(url)
            if not owners:
                continue  # curator-added, no seed equivalent → NEVER flagged
            if any(o in cl for o in owners):
                continue
            owner = next(iter(owners)) if len(owners) == 1 else None
            k = classify(url, owners, cl, fid,
                         bool(owner and seed_home.get(owner)))
            if not k:
                continue
            findings[k].append({
                "entity": ent, "final_id": fid, "url": url,
                "ref": s.get("ref"), "type": s.get("type"),
                "owner_seed": owner, "owner_src": seed_src.get(owner or ""),
                "owners_n": len(owners),
                "rightful_home": seed_home.get(owner or "") or [],
                "split_recorded": bool(
                    owner and _split_evidenced(owner, cl, no_merges.get(ent, set()))),
            })

    if args.entity:  # filter the REPORT only — the index stays corpus-wide
        findings = {k: [r for r in v if r["entity"] == args.entity]
                    for k, v in findings.items()}

    if args.json:
        print(json.dumps(findings if not args.klass
                         else {args.klass: findings.get(args.klass, [])},
                         indent=2, ensure_ascii=False))
        return 0

    print(f"finals scanned: {len(finals)}   seeds indexed: {len(seed_src)}   "
          f"single-owner urls: {sum(1 for v in url_owners.values() if len(v)==1)}")
    print()
    for k in CLASSES:
        rows = findings.get(k, [])
        print(f"{k:24s} {len(rows):5d}")
    print()
    show = [args.klass] if args.klass else ["suspect", "undecidable"]
    for k in show:
        rows = findings.get(k, [])
        if not rows:
            continue
        by_host = defaultdict(int)
        for r in rows:
            by_host[r["url"].split("/")[2] if "//" in r["url"] else "?"] += 1
        print(f"--- {k} ({len(rows)}) by host: "
              + ", ".join(f"{h}={n}" for h, n in sorted(by_host.items(),
                                                        key=lambda x: -x[1])))
        n_split = sum(1 for r in rows if r["split_recorded"])
        print(f"    with a recorded split in merge_decisions: {n_split}")
        for r in rows[: args.samples]:
            print(f"    [{r['entity']}] {r['final_id']}")
            print(f"      url        {r['url']}")
            print(f"      owner seed {r['owner_seed']}  ({r['owner_src']})")
            print(f"      rightful   {', '.join(r['rightful_home'][:3]) or '(none)'}")
            print(f"      split rec. {r['split_recorded']}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
