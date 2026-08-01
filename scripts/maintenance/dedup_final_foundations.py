#!/usr/bin/env python3
"""Fold confirmed Pattern-A duplicate FINAL foundations (§9a multi-specimen merge).

Background — why these duplicates exist
---------------------------------------
The cross-source MERGER folds seed → seed_unified, and ABSORB folds
seed_unified → final. Neither does **final-vs-final** dedup: once a
V1-bootstrap / hand-curated final entry AND its unified pipeline twin
both exist as top-level final foundations, no later run reconsiders
whether they are the same physical coin. They coexist forever.

This script takes an EXPLICIT, curator-confirmed list of (keep, drop)
pairs — never a blanket match_pair sweep (match_pair `confident` is too
permissive at the foundation level: numeric-core unions sub-letters, so
hundreds of genuinely-distinct sub-variants look «confident»). The pairs
here were confirmed by: same exact KM (or documented KM-typo) + same
danskmoent per-coin page + same nominal/ruler/metal/fuss/phase, verified
against the danskmoent hede cache (2026-06-26 audit).

The fold (§9a — preserve all per-specimen data, never collapse)
---------------------------------------------------------------
For each (keep, drop):
  - weight_rough_g  : union (multi-source list, dedup by value+source)
  - sources         : union (dedup by url+ref+type)
  - catalog         : union per-register via _deep_merge_catalog
  - year_ranges / year_first / year_last / year_label : union
  - composed_of     : keep ∪ {drop_id} ∪ drop.composed_of
  - fineness / diameter_mm : union ONLY if drop carries a value keep lacks
                             (warned; same-coin dups normally agree)
  - everything else (metal, *_verified, fuss, phase, kind, ruler,
    nominal) : keep the KEEPER's values untouched
Then the DROP foundation is removed from its final file.

Durability (verified 2026-06-26)
--------------------------------
Adding drop_id to keep.composed_of makes ABSORB's already-absorbed index
skip a seed_unified-resident drop on the next run (no resurrection).
`_revalidate_composed_of` evicts ONLY on nominal-identity mismatch — these
share nominal + KM, so the member is never evicted. The weight-tier-1
disambiguator (the reason match_pair returns no_match on a worn Bruun
specimen vs its type, e.g. bruun-5181 vs km-81) is DELIBERATELY not used
in revalidation, so the pin holds.

Usage:
    .venv/bin/python scripts/maintenance/dedup_final_foundations.py            # dry-run
    .venv/bin/python scripts/maintenance/dedup_final_foundations.py --apply
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

from lib import yaml_io  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "merge_seeds_cross_source",
    str(ROOT / "scripts" / "maintenance" / "merge_seeds_cross_source.py"))
_M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_M)

FINAL_DIR = ROOT / "data" / "v2" / "final"

# (entity, keep_id, drop_id) — curator-confirmed Pattern-A true duplicates.
PAIRS = [
    # --- APPLIED 2026-06-26 (kept for the record; ids no longer exist, and the
    # script hard-errors on missing pairs, so they are commented out): ---
    # ("danish_realm", "km-61-1-chr-iv-1618", "hede-105a-chr-iv-1618"),
    # ("danish_realm", "unified-dk-hede-f5h12", "unified-dk-hede-f5h12ab"),
    # ("royal_holstein", "unified-dk-hede-c7h13a", "km-651-1-chr-vii-1797"),
    # ("danish_realm", "unified-dk-hede-c9h13a", "km-798-1-chr-ix-1875"),
    # Hede 43 / KM 206 family: 1 Guldkrone Fr III 1655 Kopenhagen. The
    # 2026-07-17 §9.4 base-merge (guldkrone pass No. 3, merge_decisions/
    # danish_realm.yml) united the seeds [bruun-6175, bruun-6176,
    # numismaster-65599, -65600] into one unified cluster; BOTH old
    # foundation finals then matched it and got enriched — km-206 now
    # carries the full merged catalog (km [206,206.2,206.1], Hede 43A/B),
    # km-206-2 is a strict-subset duplicate (its bruun-6176 / Aagaard 17.1
    # citations already on the keeper). Keep the richer km-206.
    # APPLIED — km-206-2 no longer exists; commented out per the convention at
    # the top of this list so the missing-pair hard error does not fire.
    # ("danish_realm", "km-206-fr-iii-1655", "km-206-2-fr-iii-1655"),
    # --- Rigsbanktegn 1813-1815, six denominations (curator Serhii, 2026-08-01).
    #
    # These duplicates were MANUFACTURED by the KM-register-prefix fix (138c8ca):
    # ucoin, NumisMaster and Numista all already published `km: Tn1`…`Tn6` for
    # the copper Rigsbanktegn, but the Bruun refs regex allowed a single prefix
    # letter and dropped the two-letter token register, so the Bruun seed carried
    # no KM and never joined them. Once it did, the class re-anchored from the
    # Numista id to the Bruun one (Bruun outranks Numista), absorb minted a fresh
    # thin final under the new name, and the old rich foundation stayed behind —
    # two finals for one coin. Same physical piece on both sides: same year, same
    # copper, same Krause Tn number, same 18_5_thaler/I placement.
    #
    # KEEP the Bruun-anchored entry, whose id matches the LIVE unified class —
    # keeping the other would leave a final no unified id resolves to, which is
    # how this state arose in the first place. The keeper is also right on the
    # two fields that differ: `nominal` («12 Skilling Rigsbanktegn» over a bare
    # «12 Skilling») and `kind` (§6 — a copper token whose nominal exceeds its
    # metal value is scheide, not kurant).
    #
    # The fold is a genuine gain, not damage control: the two sides carry
    # COMPLEMENTARY registers. Bruun supplies Hede + Sieg, the commercial sources
    # supply the Krause Tn number and every weight reading. Neither side had both.
    ("danish_realm", "unified-dk-bruun-8027", "unified-dk-numista-18275"),  # 12 Sk 1813, Tn2, Hede 19
    ("danish_realm", "unified-dk-bruun-8028", "unified-dk-numista-40844"),  #  6 Sk 1813, Tn1, Hede 20
    ("danish_realm", "unified-dk-bruun-8031", "unified-dk-numista-42887"),  # 16 Sk 1814, Tn3, Hede 18
    ("danish_realm", "unified-dk-bruun-8032", "unified-dk-numista-56609"),  #  4 Sk 1815, Tn6, Hede 21
    ("danish_realm", "unified-dk-bruun-8033", "unified-dk-numista-43527"),  #  3 Sk 1815, Tn5, Hede 22
    ("danish_realm", "unified-dk-bruun-8034", "unified-dk-numista-37054"),  #  2 Sk 1815, Tn4, Hede 23
    # NOTE — c4h115 (km-81 / unified-dk-bruun-5181, both KM 81 4 Skilling)
    # is DELIBERATELY EXCLUDED: bruun-5181 carries a NumisMaster fineness
    # 0.437 + weight 1.462g that contradict the well-attested 4 Skilling
    # standard (0.859 / 1.051g per danskmoent c4h115 + hede + numista) by ~2×.
    # Either a bad NumisMaster record or a mis-catalogued different coin —
    # surfaced for curator decision, NOT auto-folded (§0b: no merge on a
    # contradicting measurement signal).
]


def _fineness_diameter_check(keep: dict, drop: dict) -> list[str]:
    """Return warnings if drop carries a fineness/diameter VALUE keep lacks."""
    warns = []
    for field in ("fineness", "diameter_mm"):
        kv = keep.get(field)
        dv = drop.get(field)
        if dv is None:
            continue

        def _vals(x):
            if isinstance(x, list):
                return {round(float(i["value"]), 5) for i in x
                        if isinstance(i, dict) and isinstance(i.get("value"), (int, float))}
            if isinstance(x, (int, float)):
                return {round(float(x), 5)}
            return set()
        new = _vals(dv) - _vals(kv)
        if new:
            warns.append(f"{field}: drop adds {sorted(new)} not in keep {sorted(_vals(kv))}")
    return warns


def _load_unified_ids(entity: str) -> list[dict]:
    """seed_unified entries for `entity` — the set the durability pin may cite."""
    path = ROOT / "data" / "v2" / "seed_unified" / f"{entity}.yml"
    if not path.exists():
        return []
    _, doc = yaml_io.load(path)
    return doc.get("coins") or []


def fold(entity: str, keep_id: str, drop_id: str, apply: bool) -> dict:
    path = FINAL_DIR / f"{entity}.yml"
    ctx, doc = yaml_io.load(path)
    coins = doc.get("coins") or []
    keep = next((c for c in coins if c.get("id") == keep_id), None)
    drop = next((c for c in coins if c.get("id") == drop_id), None)
    if keep is None or drop is None:
        raise SystemExit(f"[{entity}] missing keep={keep_id} ({keep is not None}) "
                         f"or drop={drop_id} ({drop is not None})")

    members = [keep, drop]
    report = {"entity": entity, "keep": keep_id, "drop": drop_id, "changes": {}}

    # weight_rough_g union
    w = _M._collect_field_list(members, "weight_rough_g")
    if w and w != keep.get("weight_rough_g"):
        report["changes"]["weight_rough_g"] = f"{len(keep.get('weight_rough_g') or [])} -> {len(w)}"
        if apply:
            keep["weight_rough_g"] = w

    # sources union
    srcs = _M._collect_sources(members)
    if srcs and srcs != keep.get("sources"):
        report["changes"]["sources"] = f"{len(keep.get('sources') or [])} -> {len(srcs)}"
        if apply:
            keep["sources"] = srcs

    # catalog union
    cat, _conf = _M._deep_merge_catalog(members, entity)
    if cat and cat != keep.get("catalog"):
        report["changes"]["catalog"] = f"{keep.get('catalog')} -> {cat}"
        if apply:
            keep["catalog"] = cat

    # year union
    yr = _M._union_year_ranges(members)
    if yr and yr != keep.get("year_ranges"):
        label = _M._format_year_label(yr)
        report["changes"]["year_ranges"] = f"{keep.get('year_ranges')} -> {yr}  (label: {label})"
        if apply:
            keep["year_ranges"] = yr
            keep["year_first"] = yr[0][0]
            keep["year_last"] = yr[-1][1]
            if label:
                keep["year_label"] = label

    # composed_of union (durability pin)
    #
    # The pin exists to stop ABSORB resurrecting a drop that still LIVES in
    # seed_unified: listing it in the keeper's composed_of puts it in the
    # already-absorbed index. When the drop id is NOT in seed_unified the pin
    # has nothing to catch — and it leaves a dangling reference that trips the
    # I2 invariant, which hard-blocks the commit.
    #
    # That is the normal shape for a fold that follows a class RENAME: the old
    # class was re-anchored (a higher-authority member joined it, §9b), so the
    # old id no longer names anything. The six Rigsbanktegn pairs of 2026-08-01
    # are exactly this — every drop id was a former `unified-dk-numista-*` class
    # name that the KM-register fix retired. Pin only what resolves.
    unified_ids = {c.get("id") for c in _load_unified_ids(entity)}
    comp = list(keep.get("composed_of") or [])
    add = [m for m in ([drop_id] + list(drop.get("composed_of") or []))
           if m in unified_ids]
    for m in add:
        if m and m not in comp:
            comp.append(m)
    if comp != (keep.get("composed_of") or []):
        report["changes"]["composed_of"] = f"+{[m for m in add if m not in (keep.get('composed_of') or [])]}"
        if apply:
            keep["composed_of"] = comp

    # fineness / diameter divergence guard
    report["warnings"] = _fineness_diameter_check(keep, drop)

    # remove drop foundation
    report["changes"]["remove_foundation"] = drop_id
    if apply:
        doc["coins"] = [c for c in coins if c.get("id") != drop_id]
        yaml_io.save(ctx, path, doc)

    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"===== dedup_final_foundations ({mode}) — {len(PAIRS)} pairs =====")
    for entity, keep_id, drop_id in PAIRS:
        r = fold(entity, keep_id, drop_id, args.apply)
        print(f"\n[{r['entity']}]  KEEP {r['keep']}  ⊕  DROP {r['drop']}")
        for k, v in r["changes"].items():
            print(f"    {k}: {v}")
        for w in r.get("warnings") or []:
            print(f"    ⚠ WARN {w}")
    if not args.apply:
        print("\n(dry-run — re-run with --apply to write)")


if __name__ == "__main__":
    main()
