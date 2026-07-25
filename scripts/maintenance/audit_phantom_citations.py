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

def _load_seeds() -> tuple[dict, dict]:
    """→ (url → {seed_id}, seed_id → source_dir)."""
    url_owners: dict[str, set] = defaultdict(set)
    seed_src: dict[str, str] = {}
    for path in sorted(glob.glob(str(ROOT / "data/v2/seed/*/*.yml"))):
        src = Path(path).parent.name
        doc = yaml.load(open(path), Loader=_L) or {}
        for c in doc.get("coins") or []:
            cid = c.get("id")
            if not cid:
                continue
            seed_src[cid] = src
            for s in c.get("sources") or []:
                if isinstance(s, dict) and s.get("url"):
                    url_owners[s["url"]].add(cid)
    return url_owners, seed_src


def _load_unified() -> dict:
    out = {}
    for path in sorted(glob.glob(str(ROOT / "data/v2/seed_unified/*.yml"))):
        for c in (yaml.load(open(path), Loader=_L) or {}).get("coins", []):
            if c.get("id"):
                out[c["id"]] = c
    return out


def _load_finals(entity: str | None) -> list[tuple[str, dict]]:
    out = []
    for path in sorted(glob.glob(str(ROOT / "data/v2/final/*.yml"))):
        ent = Path(path).stem
        if entity and ent != entity:
            continue
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

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--entity")
    ap.add_argument("--class", dest="klass", choices=CLASSES)
    ap.add_argument("--samples", type=int, default=3)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--explain", action="store_true")
    args = ap.parse_args()

    if args.explain:
        print(__doc__)
        return 0

    url_owners, seed_src = _load_seeds()
    uni = _load_unified()
    finals = _load_finals(args.entity)
    no_merges = _load_no_merges()

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
