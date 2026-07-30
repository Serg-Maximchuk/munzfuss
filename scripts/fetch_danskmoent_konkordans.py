"""Harvest + parse danskmoent.dk's concordance page (konkord.htm).

A concordance, in the page's own words, is «en liste, der jaevnfoerer
katalognumrene i to forskellige kataloger - eller to forskellige udgaver af
samme katalog». The page carries two:

  1. **Hauberg / Mansfeld-Bullner**, 1241-1375, broken down per mint (Lund,
     Roskilde, Ribe, Slesvig, Noerrejylland, Halland). OUTSIDE our temporal
     scope (mission lower bound is 1514) — harvested for completeness, not
     consumed by any seed builder.
  2. **Sieg, Christian 7.** — «I Siegs kataloger 2001 er nummereringen af
     Christian 7.s moenter aendret», with the concordance lists compiled by
     Dansk Moent itself. This one IS in scope, and is the reason to harvest
     the page: we cite `sieg` on >1000 finals while recording the EDITION on
     only a few dozen, so a bare «Sieg 14» for a Christian VII coin is
     ambiguous between two numbering systems that genuinely disagree (old 5
     -> new 35, old 6 -> new 34, and old 1-6 map to the new 30s while old
     7+ shifts down by six).

The page is a single static HTML file, so fetch and parse live in one script
rather than the usual fetch_/parse_ pair.

Phase 1 (HARVEST) output: ``scripts/cache/danskmoent/konkordans/konkord.htm``
Phase 2 (SYNTHESIS) output: ``.../konkord.json``

The Sieg parse is self-checking: the page prints the mapping twice, once as
Gl.->Ny and once as Ny->Gl., so the two tables must be mutual inverses. Any
disagreement is reported rather than silently resolved — a transcription slip
on danskmoent's side would otherwise become a confident wrong edge in our data
(CLAUDE.md §0b).

Run::

    .venv/bin/python scripts/fetch_danskmoent_konkordans.py
    .venv/bin/python scripts/fetch_danskmoent_konkordans.py --parse-only
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import KONKORDANS_CACHE as CACHE_DIR  # noqa: E402

URL = "https://www.danskmoent.dk/konkord.htm"
RAW = CACHE_DIR / "konkord.htm"
OUT = CACHE_DIR / "konkord.json"
USER_AGENT = (
    "Mozilla/5.0 (research; muentzfuesse project; non-commercial scholarly register)"
)


def fetch() -> str:
    req = urllib.request.Request(URL, headers={"User-Agent": USER_AGENT})
    raw = urllib.request.urlopen(req, timeout=30).read()
    # danskmoent.dk serves latin-1 with HTML entities for the Danish letters.
    text = raw.decode("latin-1")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    RAW.write_text(text, encoding="utf-8")
    return text


def _clean(cell: str) -> str:
    """Strip tags/entities from one <TD>. Tolerates the page's typos.

    The source has malformed close tags in three places (`</1B>` for `</B>`),
    so tag stripping must be permissive rather than assume well-formedness.
    """
    txt = re.sub(r"<[^>]*>", "", cell)
    return html.unescape(txt).replace("\xa0", " ").strip()


def _rows(table_html: str) -> list[list[str]]:
    out: list[list[str]] = []
    for tr in re.findall(r"<TR>(.*?)</TR>", table_html, re.S | re.I):
        cells = [_clean(td) for td in re.findall(r"<TD[^>]*>(.*?)</TD>", tr, re.S | re.I)]
        if cells:
            out.append(cells)
    return out


def _pairs_from_table(table_html: str, first_label: str) -> dict[str, str]:
    """Read a danskmoent concordance table into {from: to}.

    Layout is a run of paired rows: a header row whose first cell is the
    label ('Gl.' or 'Ny') followed by ~19 numbers, then a value row with the
    counterpart label and the aligned numbers. Row width varies, so pair the
    cells positionally per row-pair instead of assuming a fixed column count.
    """
    mapping: dict[str, str] = {}
    rows = _rows(table_html)
    for i in range(0, len(rows) - 1, 2):
        head, val = rows[i], rows[i + 1]
        if head[0].rstrip(".").lower() != first_label.rstrip(".").lower():
            raise ValueError(f"unexpected row label {head[0]!r}, want {first_label!r}")
        keys, vals = head[1:], val[1:]
        if len(keys) != len(vals):
            raise ValueError(
                f"row-pair width mismatch: {len(keys)} keys vs {len(vals)} values"
            )
        for k, v in zip(keys, vals):
            if not k or not v:
                continue
            if k in mapping and mapping[k] != v:
                raise ValueError(f"duplicate key {k!r}: {mapping[k]!r} vs {v!r}")
            mapping[k] = v
    return mapping


def parse_sieg_c7(text: str) -> dict:
    """The Sieg 2001 Christian VII renumbering: both directions + a self-check."""
    anchor = text.find('<A NAME="c7">')
    if anchor < 0:
        raise ValueError("Christian VII anchor not found — page layout changed")
    section = text[anchor:]
    tables = re.findall(r"<TABLE[^>]*>(.*?)</table>", section, re.S | re.I)
    if len(tables) != 2:
        raise ValueError(f"expected 2 Sieg tables, found {len(tables)}")

    old_to_new = _pairs_from_table(tables[0], "Gl.")
    new_to_old = _pairs_from_table(tables[1], "Ny")

    # Both tables state the same mapping; disagreement means one of them is
    # mis-transcribed upstream. Report, never pick a side (§0b).
    disagreements = []
    for old, new in sorted(old_to_new.items()):
        back = new_to_old.get(new)
        if back != old:
            disagreements.append(
                {"old": old, "new": new, "reverse_table_gives_old": back}
            )
    for new, old in sorted(new_to_old.items()):
        if new not in old_to_new.get(old, new) and old_to_new.get(old) != new:
            entry = {"new": new, "old": old, "forward_table_gives_new": old_to_new.get(old)}
            if entry not in disagreements:
                disagreements.append(entry)

    return {
        "catalogue": "Sieg",
        "ruler": "Christian VII",
        "change": "Sieg 2001 renumbered Christian VII",
        "compiled_by": "Dansk Moent",
        "source_url": URL + "#c7",
        "old_to_new": old_to_new,
        "new_to_old": new_to_old,
        "self_check": {
            "old_numbers": len(old_to_new),
            "new_numbers": len(new_to_old),
            "mutually_inverse": not disagreements,
            "disagreements": disagreements,
        },
    }


def parse_hauberg_mb(text: str) -> list[dict]:
    """Hauberg / Mansfeld-Bullner, 1241-1375, per ruler and mint.

    Out of temporal scope (pre-1514) — captured verbatim as `Hbg/MB: 1/8-10,
    2/11, …` strings without expanding the ranges, since nothing consumes it.
    """
    start = text.find('<A NAME="hbgmb">')
    end = text.find('<A NAME="c7">')
    if start < 0 or end < 0:
        raise ValueError("Hauberg/MB block boundaries not found")
    block = text[start:end]
    out: list[dict] = []
    ruler = None
    for m in re.finditer(
        r'<LI><A HREF="([^"]+)">([^<]*)</[aA]>\s*:?\s*([^<\n]*)', block
    ):
        href, label, tail = m.group(1), _clean(m.group(2)), _clean(m.group(3))
        if href.startswith("tidl/"):
            ruler = label
            continue
        if "Hbg/MB" in tail or tail.strip() in {"Hauberg = MB", "Hauberg = MB "}:
            out.append(
                {
                    "ruler": ruler,
                    "mint": label.rstrip(":"),
                    "page": href,
                    "concordance": tail,
                }
            )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--parse-only",
        action="store_true",
        help="parse the cached konkord.htm instead of re-fetching",
    )
    args = ap.parse_args()

    if args.parse_only:
        if not RAW.exists():
            print(f"no cached page at {RAW} — run without --parse-only first")
            return 1
        text = RAW.read_text(encoding="utf-8")
    else:
        text = fetch()
        print(f"fetched {len(text)} chars -> {RAW}")

    sieg = parse_sieg_c7(text)
    hbg = parse_hauberg_mb(text)

    payload = {
        "source_url": URL,
        "definition": (
            "En konkordans er en liste, der jaevnfoerer katalognumrene i to "
            "forskellige kataloger - eller to forskellige udgaver af samme katalog."
        ),
        "sieg_christian_vii_2001": sieg,
        "hauberg_mansfeld_bullner": hbg,
    }
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    chk = sieg["self_check"]
    print(f"Sieg C7: {chk['old_numbers']} old -> {chk['new_numbers']} new numbers")
    print(f"  mutually inverse: {chk['mutually_inverse']}")
    for d in chk["disagreements"]:
        print(f"  DISAGREEMENT {d}")
    print(f"Hauberg/MB: {len(hbg)} ruler-mint rows (out of scope, informational)")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
