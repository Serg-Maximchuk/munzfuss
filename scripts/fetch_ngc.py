#!/usr/bin/env python3
"""NGC World Coin Price Guide — Phase 1 HARVEST (cache writer + resume manager).

**This script does NOT touch the network, by design.** NGC sits behind a
Cloudflare JS challenge that blocks every non-browser client: urllib, requests,
and Playwright in seven separate configurations (bundled Chromium and real
``channel="chrome"``, headless and headed, with stealth patches, with a warm
persistent profile) were ALL blocked, while a control ``fetch()`` in an ordinary
browser tab succeeded at the same moment. Cloudflare fingerprints the automation
layer itself — see ``docs/SOURCES.md`` §13.13(c2) for the full evidence table.
Do not re-litigate that by adding a headless-browser dependency.

So the network half runs as an in-page ``fetch()`` loop inside a real browser
session (Browser pane / Chrome MCP), and this script is the other half: it
ingests the JSON that loop produces, writes the cache tree, and reports what is
still missing so the next browser batch knows exactly what to ask for.

Usage::

    # 1. record the region taxonomy (captured once from the search form)
    python scripts/fetch_ngc.py regions < regions.json

    # 2. record a listing walk: {"cuid": "<detail href>", ...}
    python scripts/fetch_ngc.py listing --region LÜBECK < listing.json

    # 3. ingest a batch of extracted detail records (a JSON array)
    python scripts/fetch_ngc.py ingest --region LÜBECK < batch.json

    # 4. ask what is still missing (feeds the next browser batch)
    python scripts/fetch_ngc.py todo --region LÜBECK [--limit 20]

    # 5. progress summary
    python scripts/fetch_ngc.py status [--region LÜBECK]

Every record is written as ``cuid_<N>.json`` plus a ``cuid_<N>.txt`` sidecar
holding the page's visible text, which is the provenance artefact standing in
for raw HTML (the browser bridge cannot move 150 kB pages at volume; the text
carries every field we parse and stays diffable).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.paths import NGC_CACHE  # noqa: E402

CUID_RE = re.compile(r"cuid-(\d+)-duid-(\d+)")
# Region names reach the filesystem, so fold anything that would surprise a
# shell or a case-insensitive filesystem. LÜBECK and LUBECK are DIFFERENT
# regions upstream (§13.13(a)) and must NOT collapse onto one directory, so the
# umlaut is transliterated rather than stripped.
_SLUG_MAP = {"Ü": "UE", "Ö": "OE", "Ä": "AE", "ß": "SS"}


def region_slug(region: str) -> str:
    out = region.upper()
    for k, v in _SLUG_MAP.items():
        out = out.replace(k, v)
    out = re.sub(r"[^A-Z0-9]+", "_", out).strip("_")
    return out.lower()


def region_dir(region: str) -> Path:
    return NGC_CACHE / region_slug(region)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_stdin_json():
    raw = sys.stdin.read().strip()
    if not raw:
        sys.exit("ERROR: no JSON on stdin")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: stdin is not valid JSON: {e}")


def _write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------- commands


def cmd_regions(args: argparse.Namespace) -> int:
    data = _read_stdin_json()
    path = NGC_CACHE / "_regions.json"
    payload = {
        "_schema": "NGC region taxonomy per country, captured from the "
                   "price-guide search form's uxRegions select.",
        "_captured_at": _now(),
        "countries": data,
    }
    _write_json(path, payload)
    n = sum(len(v) for v in data.values()) if isinstance(data, dict) else len(data)
    print(f"wrote {path} — {n} region entries")
    return 0


def cmd_listing(args: argparse.Namespace) -> int:
    data = _read_stdin_json()
    if not isinstance(data, dict):
        sys.exit("ERROR: listing expects a JSON object {cuid: href}")
    d = region_dir(args.region)
    path = d / "_listing.json"

    prior = {}
    if path.exists():
        prior = json.loads(path.read_text(encoding="utf-8")).get("cuids", {})

    merged = {**prior, **{str(k): v for k, v in data.items()}}
    _write_json(path, {
        "_schema": "cuid -> detail-page href, from the NGC pager walk. "
                   "Rows upstream are per-date (duid); this map is already "
                   "collapsed to TYPES (cuid) — see SOURCES.md §13.13(b).",
        "region": args.region,
        "country": args.country,
        "_walked_at": _now(),
        "count": len(merged),
        "cuids": merged,
    })
    added = len(merged) - len(prior)
    print(f"wrote {path} — {len(merged)} types ({added:+d} new)")
    return 0


def _validate(rec: dict) -> str | None:
    if not isinstance(rec, dict):
        return "not an object"
    if not rec.get("cuid"):
        return "missing cuid"
    if not str(rec["cuid"]).isdigit():
        return f"non-numeric cuid {rec['cuid']!r}"
    if not rec.get("url"):
        return "missing url"
    if rec.get("status") not in (200, "200", None):
        return f"non-200 status {rec.get('status')!r}"
    if not rec.get("text"):
        return "missing page text (provenance sidecar would be empty)"
    return None


def cmd_ingest(args: argparse.Namespace) -> int:
    data = _read_stdin_json()
    if isinstance(data, dict):
        data = [data]
    d = region_dir(args.region)
    d.mkdir(parents=True, exist_ok=True)

    written = skipped = 0
    bad: list[str] = []
    for rec in data:
        err = _validate(rec)
        if err:
            bad.append(f"  cuid={rec.get('cuid') if isinstance(rec, dict) else '?'}: {err}")
            continue
        cuid = str(rec["cuid"])
        jpath = d / f"cuid_{cuid}.json"
        if jpath.exists() and not args.force:
            skipped += 1
            continue
        text = rec.pop("text")
        rec.setdefault("region", args.region)
        rec.setdefault("country", args.country)
        rec["_fetched_at"] = _now()
        rec["_text_chars"] = len(text)
        _write_json(jpath, rec)
        (d / f"cuid_{cuid}.txt").write_text(text, encoding="utf-8")
        written += 1

    print(f"[{args.region}] ingested {written}, skipped {skipped} (already cached)"
          + (f", REJECTED {len(bad)}" if bad else ""))
    if bad:
        print("rejected records:", file=sys.stderr)
        for b in bad:
            print(b, file=sys.stderr)
        return 1
    return 0


def _listing_cuids(region: str) -> dict:
    path = region_dir(region) / "_listing.json"
    if not path.exists():
        sys.exit(f"ERROR: no listing walk for {region!r} yet — run `listing` first")
    return json.loads(path.read_text(encoding="utf-8"))["cuids"]


def _cached_cuids(region: str) -> set[str]:
    d = region_dir(region)
    if not d.exists():
        return set()
    return {p.stem.removeprefix("cuid_") for p in d.glob("cuid_*.json")}


def cmd_todo(args: argparse.Namespace) -> int:
    listing = _listing_cuids(args.region)
    have = _cached_cuids(args.region)
    missing = {k: v for k, v in listing.items() if k not in have}
    out = dict(list(missing.items())[: args.limit]) if args.limit else missing
    if args.json:
        print(json.dumps(out, ensure_ascii=False))
    else:
        print(f"[{args.region}] {len(missing)} of {len(listing)} types still missing"
              f"{f'; next {len(out)}:' if out else ''}")
        for k, v in out.items():
            print(f"  {k}\t{v}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    if not NGC_CACHE.exists():
        print("NGC cache is empty (nothing harvested yet)")
        return 0
    regions = [args.region] if args.region else [
        p.name for p in sorted(NGC_CACHE.iterdir())
        if p.is_dir() and not p.name.startswith("_")
    ]
    print(f"{'region':<28}{'types':>7}{'cached':>8}{'todo':>7}")
    for r in regions:
        d = NGC_CACHE / region_slug(r) if args.region else NGC_CACHE / r
        lp = d / "_listing.json"
        total = len(json.loads(lp.read_text(encoding="utf-8"))["cuids"]) if lp.exists() else 0
        have = len(list(d.glob("cuid_*.json")))
        print(f"{d.name:<28}{total:>7}{have:>8}{max(total - have, 0):>7}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_region(p, required=True):
        p.add_argument("--region", required=required)
        p.add_argument("--country", default="GERMAN STATES")

    p = sub.add_parser("regions", help="record the region taxonomy (stdin JSON)")
    p.set_defaults(fn=cmd_regions)

    p = sub.add_parser("listing", help="record a pager walk (stdin {cuid: href})")
    add_region(p)
    p.set_defaults(fn=cmd_listing)

    p = sub.add_parser("ingest", help="ingest extracted detail records (stdin array)")
    add_region(p)
    p.add_argument("--force", action="store_true", help="overwrite cached records")
    p.set_defaults(fn=cmd_ingest)

    p = sub.add_parser("todo", help="list types not yet cached")
    add_region(p)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_todo)

    p = sub.add_parser("status", help="progress summary")
    add_region(p, required=False)
    p.set_defaults(fn=cmd_status)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
