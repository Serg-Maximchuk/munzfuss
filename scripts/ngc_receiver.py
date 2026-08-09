#!/usr/bin/env python3
"""Local receive-only HTTP endpoint for the NGC browser harvest.

NGC is behind a Cloudflare gate that no Python client can pass (urllib,
requests and Playwright in 7 configurations all blocked — docs/SOURCES.md
§13.13(c2)), so the fetching half of the harvest runs as an in-page fetch()
loop inside a real browser tab. This process is the receiving half: the page
POSTs each extracted record here and it lands in the cache directly, instead
of being relayed record-by-record through the agent's tool bridge.

Bound to 127.0.0.1 only. Accepts POST /ingest with a JSON array of records and
hands them to `fetch_ngc.py ingest` semantics; GET /todo reports what is still
missing so the browser loop can self-schedule. Chrome treats http://127.0.0.1
as a potentially-trustworthy origin, so a page served over HTTPS may POST to it
without tripping mixed-content blocking; the permissive CORS header below is
what allows the cross-origin call itself.

Run it in the background for the duration of a harvest, then stop it:

    python scripts/ngc_receiver.py --region 'LÜBECK' [--port 8899]
"""
from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_ngc import (  # noqa: E402
    _now,
    _validate,
    _write_json,
    region_dir,
)

STATE: dict = {}


class Handler(BaseHTTPRequestHandler):
    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

    def _json(self, code: int, obj) -> None:
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):  # noqa: N802
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):  # noqa: N802
        if self.path.startswith("/todo"):
            d = region_dir(STATE["region"])
            have = {p.stem.removeprefix("cuid_") for p in d.glob("cuid_*.json")} \
                if d.exists() else set()
            lp = d / "_listing.json"
            listing = json.loads(lp.read_text(encoding="utf-8"))["cuids"] \
                if lp.exists() else {}
            missing = {k: v for k, v in listing.items() if k not in have}
            return self._json(200, {"total": len(listing), "have": len(have),
                                    "missing": missing})
        if self.path.startswith("/ping"):
            return self._json(200, {"ok": True, "region": STATE["region"]})
        self._json(404, {"error": "not found"})

    def do_POST(self):  # noqa: N802
        if not self.path.startswith("/ingest"):
            return self._json(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(n) or b"[]")
        except json.JSONDecodeError as e:
            return self._json(400, {"error": f"bad json: {e}"})
        if isinstance(data, dict):
            data = [data]

        d = region_dir(STATE["region"])
        d.mkdir(parents=True, exist_ok=True)
        written = skipped = 0
        bad = []
        for rec in data:
            err = _validate(rec)
            if err:
                bad.append({"cuid": rec.get("cuid") if isinstance(rec, dict) else None,
                            "error": err})
                continue
            cuid = str(rec["cuid"])
            jp = d / f"cuid_{cuid}.json"
            if jp.exists():
                skipped += 1
                continue
            text = rec.pop("text")
            rec["region"] = STATE["region"]
            rec["country"] = STATE["country"]
            rec["_fetched_at"] = _now()
            rec["_text_chars"] = len(text)
            _write_json(jp, rec)
            (d / f"cuid_{cuid}.txt").write_text(text, encoding="utf-8")
            written += 1
        STATE["written"] = STATE.get("written", 0) + written
        print(f"  +{written} written, {skipped} dup, {len(bad)} bad "
              f"(total {STATE['written']})", flush=True)
        self._json(200, {"written": written, "skipped": skipped, "bad": bad,
                         "total_written": STATE["written"]})

    def log_message(self, *a):  # silence per-request noise
        pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--country", default="GERMAN STATES")
    ap.add_argument("--port", type=int, default=8899)
    args = ap.parse_args()
    STATE.update(region=args.region, country=args.country, written=0)
    srv = HTTPServer(("127.0.0.1", args.port), Handler)
    print(f"NGC receiver on http://127.0.0.1:{args.port} "
          f"region={args.region!r} -> {region_dir(args.region)}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    print(f"stopped; {STATE['written']} records written", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
