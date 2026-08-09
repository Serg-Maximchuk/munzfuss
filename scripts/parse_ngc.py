#!/usr/bin/env python3
"""NGC World Coin Price Guide — Phase 2 SYNTHESIS.

Reads the Phase-1 harvest records (``scripts/cache/ngc/<region>/cuid_<N>.json``,
written by the browser loop via ``ngc_receiver.py``) and emits a typed sidecar
``cuid_<N>.parsed.json`` per coin type.

The whole point of this phase is the **``Note:`` field**, which is where NGC's
real value for this project sits. It is free text, but highly patterned, and it
carries the catalogue keys the rest of our sources do not give us:

    Ref. B-805a; Dav. 623. Varieties exist.
    Ref. B-136e; Dav. LS328. Prev. KM#16. Broad flan. Arms of Mayor Gotthard...
    Ref. B#317-25, 326b,c.
    Ref. B-471, 472. Varieties exist. Previous KM#9. Dreiling.

**Behrens** (``B-###`` / ``B####``) is the load-bearing Lübeck catalogue key we
otherwise hold only on paper, and ``Previous KM#`` is an explicit Krause
renumbering trail that feeds the §9.4 index-graph work and the §13.6
KM#-inflation problem.

**Nothing is discarded.** Every span the parser does not claim is preserved
verbatim in ``note_residual``, and ``note_raw`` always keeps the original. A
parser that silently drops what it does not understand would quietly corrupt
the record (CLAUDE.md §0b); an honest leftover is auditable.

Usage::

    python scripts/parse_ngc.py --region 'LÜBECK' [--force] [--stats]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_ngc import region_dir  # noqa: E402

# --- Note-field patterns -------------------------------------------------
# Behrens: "B-471, 472" / "B-805b,c" / "B#317-25, 326b,c" / "B-186. 187"
_BEHRENS_HEAD = re.compile(r"\bB[-#]\s?(\d[\w,.\-\s]*?)(?=(?:;|$|\.\s+[A-Z(]|\bDav\b|\bFr\b|\bPrev))",
                           re.IGNORECASE)
_DAV = re.compile(r"\bDav\.?\s*#?\s*((?:LS)?[A-Z]?\d+[A-Z]?)", re.IGNORECASE)
_FR = re.compile(r"\bFr\.?\s*(\d+[A-Za-z]?)")
_PREV_KM = re.compile(r"\bPrev(?:ious)?\.?\s*KM\s*#?\s*([\w.]+)", re.IGNORECASE)
_PREV_FR = re.compile(r"\bPrev(?:ious)?\.?\s*Fr\.?\s*#?\s*([\w.]+)", re.IGNORECASE)
_BARE_KM = re.compile(r"(?<!Prev)(?<!Previous)\bKM\s*#\s*([\w.]+)", re.IGNORECASE)

# Descriptive flags that matter for §9 (fabric / strike) and §9.4 (variants).
# These are SIGNALS for the curator's §9 pass, never verdicts on their own —
# §9.1 is explicit that a marker alone does not exclude a coin.
_FLAGS = {
    "varieties_exist": re.compile(r"\bVarieties exist\b", re.I),
    "klippe": re.compile(r"\bKlippe\b", re.I),
    "broad_flan": re.compile(r"\bBroad flan\b", re.I),
    "thick_flan": re.compile(r"\bThick flan\b", re.I),
    "restrike": re.compile(r"\bRestrike\b", re.I),
    "joint_issue": re.compile(r"\b(?:Issued for use in both|struck for use in both)\b", re.I),
    # §9.3 off-metal strike — the Guldafslag / Sølvafslag class
    "off_metal_strike": re.compile(r"\boff[- ]metal strike\b", re.I),
    "mule": re.compile(r"\bMule\b", re.I),
    "uniface": re.compile(r"\bUniface\b", re.I),
    "wire_money": re.compile(r"\bWire money\b", re.I),
    # §9.5 off-nominal presentation: a normal-diameter piece struck on a
    # multiple-thickness planchet (piedfort). NGC writes it as
    # "Size as 1/2 Ducat, 4 times thickness" / "but double thickness".
    "multiple_thickness": re.compile(r"\b(?:double|triple|\d+\s*times)\s+thickness\b", re.I),
    # dual-denominated pieces — bears on §1 (what goes in `nominal`)
    "dual_denominated": re.compile(r"\bDual denominated?\b", re.I),
}
# "Struck at Altona" / "Struck in Copenhagen for the Danish West Indies Company"
_STRUCK_AT = re.compile(r"\bStruck (?:at|in)\s+([A-ZÆØÅÄÖÜ][\w.\-]*(?:\s+[A-ZÆØÅÄÖÜ][\w.\-]*)*)")
# Mayor attributions carry abbreviated nobiliary particles ("Gotthard v. Höveln"),
# so the name span must tolerate a '.' — stopping at the first period loses ~1 in 5.
_MAYOR = re.compile(
    r"\bArms of (?:Mayor\s+)?((?:[^.;()]|\.(?=\s*[A-ZÄÖÜ]))+?)\s*\((\d{4})\s*-\s*(\d{2,4})\)")

_YEAR = re.compile(r"\b(1[3-9]\d{2})\b")


def _split_behrens(blob: str) -> list[str]:
    """Expand a Behrens blob into individual index tokens.

    "471, 472"        -> [471, 472]
    "805b,c"          -> [805b, 805c]      (letter suffixes share the number)
    "317-25, 326b,c"  -> [317-25, 326b, 326c]  (ranges kept verbatim)
    "186. 187"        -> [186, 187]        (source uses '.' as a separator)
    """
    out: list[str] = []
    last_num: str | None = None
    for tok in re.split(r"[,\s]+|(?<=\d)\.\s+", blob):
        tok = tok.strip(" .,;")
        if not tok:
            continue
        if re.fullmatch(r"\d+[a-z]?(?:-\d+[a-z]?)?", tok, re.I):
            out.append(tok)
            m = re.match(r"(\d+)", tok)
            last_num = m.group(1) if m else last_num
        elif re.fullmatch(r"[a-z]", tok, re.I) and last_num:
            # bare letter continuation: "805b,c" -> the 'c' means 805c
            out.append(f"{last_num}{tok}")
        else:
            out.append(tok)
    return out


def parse_note(note: str | None) -> dict:
    if not note:
        return {"note_raw": None, "catalog_refs": {}, "flags": {}, "note_residual": None}
    residual = note
    refs: dict[str, list[str]] = {}

    def claim(pattern: re.Pattern, key: str, expand=None) -> None:
        # Scan the REMAINING text, not the original: "Prev. KM#16" must be
        # claimed once as previous_km, not a second time as a bare KM
        # cross-reference. Matching against `note` throughout double-counted
        # every renumbering note (98 phantom km_cross_ref on the Lübeck pilot).
        nonlocal residual
        vals: list[str] = []
        while True:
            m = pattern.search(residual)
            if not m:
                break
            raw = m.group(1)
            vals.extend(expand(raw) if expand else [raw.strip(" .,;")])
            residual = residual[:m.start()] + " " + residual[m.end():]
        vals = [v for v in dict.fromkeys(vals) if v]
        if vals:
            refs[key] = vals

    claim(_BEHRENS_HEAD, "behrens", _split_behrens)
    claim(_DAV, "dav")
    claim(_FR, "fr")
    claim(_PREV_KM, "previous_km")
    claim(_PREV_FR, "previous_fr")
    claim(_BARE_KM, "km_cross_ref")

    flags: dict[str, object] = {}
    for name, pat in _FLAGS.items():
        m = pat.search(residual)
        if m:
            flags[name] = True
            residual = residual[:m.start()] + " " + residual[m.end():]
    m = _STRUCK_AT.search(residual)
    if m:
        flags["struck_at"] = m.group(1).strip()
        residual = residual[:m.start()] + " " + residual[m.end():]
    m = _MAYOR.search(residual)
    if m:
        flags["mayor_arms"] = {"name": m.group(1).strip(),
                               "from": int(m.group(2)),
                               "to": int(m.group(3)) if len(m.group(3)) == 4
                               else int(m.group(2)[:2] + m.group(3))}
        residual = residual[:m.start()] + " " + residual[m.end():]

    residual = re.sub(r"\bRef\.?\s*", " ", residual)
    residual = re.sub(r"[\s.;,]+", " ", residual).strip(" .,;")
    return {"note_raw": note, "catalog_refs": refs, "flags": flags,
            "note_residual": residual or None}


def parse_years(rec: dict) -> dict:
    """Year span from the date table, falling back to the heading date line.

    NGC writes partially-legible dates as "(1)604" and illegible digits as
    "16z0" / "166z"; the 'z' forms are deliberately NOT resolved into a year —
    guessing the missing digit would be invention (§0).
    """
    raw = [d.get("year_mint") or "" for d in (rec.get("dates") or [])]
    if not raw and rec.get("date_line"):
        raw = [rec["date_line"]]
    years, illegible = [], False
    for s in raw:
        s2 = s.replace("(1)", "1")
        if re.search(r"\d[a-z]|\bz\b|\dz", s2, re.I):
            illegible = True
        years.extend(int(y) for y in _YEAR.findall(s2))
    out = {"year_first": min(years) if years else None,
           "year_last": max(years) if years else None,
           "years_all": sorted(set(years)) or None}
    if illegible:
        out["year_partially_illegible"] = True
    return out


def parse_record(rec: dict) -> dict:
    out = {k: rec.get(k) for k in (
        "cuid", "url", "region", "country", "heading", "date_line",
        "catalog_scheme", "catalog_number", "composition", "fineness",
        "weight_g", "asw_oz", "agw_oz", "diameter_raw", "obverse",
        "obverse_legend", "obverse_inscription", "reverse", "reverse_legend",
        "reverse_inscription", "edge", "ruler", "subject", "mint", "designer",
        "dates")}
    for k in ("fineness", "weight_g", "asw_oz", "agw_oz"):
        if out.get(k) is not None:
            try:
                out[k] = float(out[k])
            except (TypeError, ValueError):
                pass
    out.update(parse_years(rec))
    out.update(parse_note(rec.get("note")))
    # the coin's own catalogue index, from the heading
    if rec.get("catalog_scheme") and rec.get("catalog_number"):
        out["catalog_own"] = {rec["catalog_scheme"].lower(): rec["catalog_number"]}
    out["is_pattern_number"] = bool(
        re.match(r"pn", str(rec.get("catalog_number") or ""), re.I))
    out["_parsed_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--stats", action="store_true")
    args = ap.parse_args()

    d = region_dir(args.region)
    srcs = sorted(d.glob("cuid_*.json"))
    srcs = [p for p in srcs if not p.name.endswith(".parsed.json")]
    if not srcs:
        sys.exit(f"no harvest records under {d}")

    n = 0
    stats: Counter = Counter()
    residuals: Counter = Counter()
    for p in srcs:
        outp = p.with_suffix(".parsed.json")
        if outp.exists() and not args.force:
            continue
        rec = json.loads(p.read_text(encoding="utf-8"))
        parsed = parse_record(rec)
        outp.write_text(json.dumps(parsed, ensure_ascii=False, indent=1,
                                   sort_keys=True) + "\n", encoding="utf-8")
        n += 1
        for k in parsed.get("catalog_refs", {}):
            stats[k] += 1
        for k in parsed.get("flags", {}):
            stats[f"flag:{k}"] += 1
        if parsed.get("note_residual"):
            residuals[parsed["note_residual"][:60]] += 1
    print(f"[{args.region}] parsed {n} records -> *.parsed.json")
    if args.stats:
        print("\ncatalog-ref / flag coverage:")
        for k, c in stats.most_common():
            print(f"  {k:<24}{c:>5}")
        print(f"\nunclaimed note residuals ({len(residuals)} distinct, "
              f"kept verbatim in note_residual):")
        for s, c in residuals.most_common(20):
            print(f"  {c:>3}  {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
