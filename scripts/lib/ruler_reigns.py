"""Shared reign-window table for Danish-Norwegian kings, plus
helpers that normalise English/Danish/Roman/Arabic ruler-name
variants down to the canonical key. Used by seed builders to
flag ruler-attribution errors in source data (e.g. ucoin's
2026-05-22-discovered «1807 4 Skilling — Frederick VI» when
Christian VII actually reigned through 13 March 1808).

Sources for reign dates:
  * https://en.wikipedia.org/wiki/List_of_Danish_monarchs
  * https://en.wikipedia.org/wiki/List_of_Norwegian_monarchs
    (personal union 1380-1814; same kings 1514-1814)

Each entry is `(year_first, year_last)` — inclusive boundaries
in the calendar-year sense. The accession year counts as «in
reign» even if the king took the throne in December; same for
the death year. Real-month-of-death precision (e.g. Christian
VII died 13 March 1808 — so 1808 coins after that point are
Frederik VI's) sits in `ACCESSION_MONTH` for the rare cases
where it matters in our scope.
"""
from __future__ import annotations

import re


# Reign-year windows. Coin minted within [year_first, year_last]
# (inclusive both ends) is attributable to this ruler. Coins
# struck at the boundary year (accession or death) carry an extra
# month-level disambiguator in `_ACCESSION_MONTH` below — see
# `reign_covers_year_strict()`.
#
# Canonical key shape: «<Christian|Frederik> <Roman-numeral>» (no
# trailing period). Norwegian-only kings (rare in this project)
# would go under a separate table; we don't have any in scope
# 1514-1914 because the personal union kept Danish kings on the
# Norwegian throne until 1814.
RULER_REIGNS: dict[str, tuple[int, int]] = {
    # Pre-1514 — relevant for the `denmark/p0_pre_lovkompleks`
    # bucket (Erik VII → Hans 1396-1513).
    "Erik VII":      (1396, 1439),
    "Christoffer III": (1440, 1448),
    "Christian I":   (1448, 1481),
    "Hans I":        (1481, 1513),  # also written «John I» in English ucoin

    # Post-Lovkompleks Christian-II line.
    "Christian II":  (1513, 1523),
    "Frederik I":    (1523, 1533),
    # Civil-war / interregnum 1534-1536 — Christian III acclaimed
    # 1534, crowned 1537, sole king after Reformation 1537. For
    # reign-window purposes we use 1534 as start (de facto rule).
    "Christian III": (1534, 1559),
    "Frederik II":   (1559, 1588),
    "Christian IV":  (1588, 1648),
    "Frederik III":  (1648, 1670),
    "Christian V":   (1670, 1699),
    "Frederik IV":   (1699, 1730),
    "Christian VI":  (1730, 1746),
    "Frederik V":    (1746, 1766),
    # Christian VII formally reigned to his death on 13 March 1808.
    # Frederik VI was Regent from 1784 → king from Christian VII's
    # death. Coins dated 1808 ambiguous unless month known; pre-1808
    # is unambiguously Christian VII.
    "Christian VII": (1766, 1808),
    "Frederik VI":   (1808, 1839),
    "Christian VIII": (1839, 1848),
    "Frederik VII":  (1848, 1863),
    "Christian IX":  (1863, 1906),
    "Frederik VIII": (1906, 1912),
    "Christian X":   (1912, 1947),  # post-1914 OOS but kept for completeness
}


# ── Ducal houses ──────────────────────────────────────────────────────
#
# The table above is the Danish-Norwegian kings, and until now it was the
# whole world: `reign_window("Frederik 3")` answered 1648-1670 whoever asked.
# That is wrong for a Gottorp coin, whose Friedrich III ruled 1616-1659, and
# the two collide by name alone — as do Friedrich II and Friedrich IV. The
# only thing that separates them is WHICH HOUSE the coin belongs to, so the
# ducal tables are keyed by issuing entity and callers pass it explicitly.
# Without a house the kings' table answers, exactly as before.
#
# Ducal names are compound («Johann Adolf», «Christian Albrecht»), not
# name-plus-numeral, so they need their own alias map rather than the
# numeral regex.
#
# Source for the Gottorp line: en.wikipedia.org/wiki/Duchy_of_Holstein-Gottorp,
# «Dukes of Schleswig and Holstein at Gottorp» / «… at Kiel».
HOUSE_REIGNS: dict[str, dict[str, tuple[int, int]]] = {
    "gottorp_duchy": {
        "Adolf I":           (1544, 1586),
        "Friedrich II":      (1586, 1587),
        "Philipp":           (1587, 1590),
        "Johann Adolf":      (1590, 1616),
        "Friedrich III":     (1616, 1659),
        "Christian Albrecht": (1659, 1694),
        "Friedrich IV":      (1694, 1702),
        "Karl Friedrich":    (1702, 1739),
        "Karl Peter Ulrich": (1739, 1762),
        "Paul":              (1762, 1773),
    },
}

# Observed source spellings → canonical key inside a house table. Lowercased,
# punctuation-stripped on lookup. Forms taken from the KMM and NGC records
# actually in the cache («Christian Albrecht af Holsten-Gottorp», «Johan
# Adolph», «Karl Frederik»).
_HOUSE_ALIASES: dict[str, dict[str, str]] = {
    "gottorp_duchy": {
        "adolf": "Adolf I",
        "adolf i": "Adolf I",
        "friedrich ii": "Friedrich II", "frederik ii": "Friedrich II",
        "frederik 2": "Friedrich II",
        "philipp": "Philipp", "philip": "Philipp",
        "johann adolf": "Johann Adolf", "johan adolf": "Johann Adolf",
        "johan adolph": "Johann Adolf", "johann adolph": "Johann Adolf",
        "friedrich iii": "Friedrich III", "frederik iii": "Friedrich III",
        "frederik 3": "Friedrich III", "frederick iii": "Friedrich III",
        "christian albrecht": "Christian Albrecht",
        "christian albert": "Christian Albrecht",
        "friedrich iv": "Friedrich IV", "frederik iv": "Friedrich IV",
        "frederik 4": "Friedrich IV",
        "karl friedrich": "Karl Friedrich", "karl frederik": "Karl Friedrich",
        "carl frederik": "Karl Friedrich", "charles frederick": "Karl Friedrich",
        "karl peter ulrich": "Karl Peter Ulrich",
        "paul": "Paul",
    },
}

_HOUSE_SUFFIX_RE = re.compile(
    r"\s+(?:af|von|of)\s+.*$", re.IGNORECASE)


def house_reign_window(ruler_raw: str | None,
                       house: str | None) -> tuple[int, int] | None:
    """Reign window for a ruler of a named ducal house, or None.

    Strips a trailing territorial epithet — «Christian Albrecht af
    Holsten-Gottorp» is the same man as «Christian Albrecht» — then looks the
    remainder up in that house's alias map. Returns None when the house is
    unknown or the name does not resolve, so a caller can fall through to the
    kings' table rather than guess.
    """
    if not ruler_raw or not isinstance(ruler_raw, str) or not house:
        return None
    aliases = _HOUSE_ALIASES.get(house)
    if not aliases:
        return None
    name = _HOUSE_SUFFIX_RE.sub("", ruler_raw.strip())
    name = name.replace(".", "").strip().lower()
    key = aliases.get(name)
    if key is None:
        return None
    return HOUSE_REIGNS.get(house, {}).get(key)


# Accession month for boundary-year disambiguation. Keyed by ruler
# name; value = (year, month) of accession. Coin year falling in
# the accession year BEFORE this month belongs to the PREDECESSOR;
# from this month onward to the new ruler. Currently the only
# scope-relevant boundary that needs month precision is Frederik
# VI's accession after Christian VII's death 1808-03-13.
_ACCESSION_MONTH: dict[str, tuple[int, int]] = {
    "Frederik VI": (1808, 3),  # post-Christian-VII death 13 March 1808
}


# Name-normalisation table — maps ucoin / numismaster / Bruun /
# Galster name forms (English vs Danish spellings, with or without
# trailing period) to the canonical key in `RULER_REIGNS`.
#
# Forms observed in real source data (2026-05-22 survey of ucoin
# cache):
#   ucoin English: «Frederick II», «Christian VI», «Christian V /
#                  Frederick III» (joint attribution)
#   ucoin Danish:  «Frederik VI», «Frederik VII» (occasional)
#   Hede / Galster: «Christian 3.» (Arabic numeral + period),
#                  «Frederik V.» (Roman + period)
#   English first-name aliases: «John I» = «Hans I»
_NAME_NORMALISE: dict[str, str] = {
    # English «Frederick» → Danish «Frederik» (canonical key form).
    "Frederick": "Frederik",
    # English «John» → Danish «Hans» (only Hans I 1481-1513).
    "John I": "Hans I",
}

_ARABIC_TO_ROMAN = {
    "1": "I", "2": "II", "3": "III", "4": "IV", "5": "V",
    "6": "VI", "7": "VII", "8": "VIII", "9": "IX", "10": "X",
}

_RULER_RE = re.compile(
    r"\b(Christian|Frederik|Frederick|Hans|Erik|Christoffer|John)\b"
    r"\s*"
    r"(\d+|[IVX]+)"
    r"\.?",
    re.IGNORECASE,
)


def normalise_ruler_name(raw: str | None) -> str | None:
    """Map any ruler-name variant to a canonical key for `RULER_REIGNS`.

    Returns None when the input doesn't contain a recognisable
    ruler-name token (allowing the caller to no-op rather than
    fabricate a reign window).

    Handles:
      * English «Frederick X» → «Frederik X»
      * Trailing period «Christian VII.» → «Christian VII»
      * Arabic numeral «Christian 3.» → «Christian III»
      * Alias «John I» → «Hans I»
      * Joint attribution «Christian V / Frederick III» — returns
        the FIRST name only; caller can treat joint cases via the
        full string passed in if needed.
    """
    if not raw or not isinstance(raw, str):
        return None
    # Joint-attribution form: take the first half before « / » so
    # «Christian V / Frederick III» → «Christian V».
    head = raw.split("/", 1)[0].strip()
    m = _RULER_RE.search(head)
    if not m:
        return None
    name, numeral = m.group(1), m.group(2)
    # Capitalise first letter; rest as-is (handles «christian» etc.).
    name = name[0].upper() + name[1:].lower()
    # English → Danish form.
    name = _NAME_NORMALISE.get(name, name)
    # Arabic → Roman.
    if numeral.isdigit():
        numeral = _ARABIC_TO_ROMAN.get(numeral, numeral)
    else:
        numeral = numeral.upper()
    candidate = f"{name} {numeral}"
    # Alias-pass for combined «Name Numeral» forms.
    candidate = _NAME_NORMALISE.get(candidate, candidate)
    if candidate in RULER_REIGNS:
        return candidate
    return None


def reign_window(ruler_raw: str | None,
                 house: str | None = None) -> tuple[int, int] | None:
    """Return `(year_first, year_last)` for the named ruler, or None
    when the ruler name doesn't resolve to any known entry.

    `house` is an issuing-entity tag. When given and known, that house's
    ducal table is consulted FIRST — «Frederik 3» is the Danish king
    1648-1670 or the Gottorp duke 1616-1659 depending on it. Omitting it
    keeps the historical behaviour: the kings' table only.
    """
    ducal = house_reign_window(ruler_raw, house)
    if ducal is not None:
        return ducal
    key = normalise_ruler_name(ruler_raw)
    if key is None:
        return None
    return RULER_REIGNS.get(key)


def reign_covers_year(ruler_raw: str | None, year: int | None,
                        tolerance: int = 0) -> bool | None:
    """True/False/None: does the ruler's reign cover `year`?

    * True  — year falls within (year_first, year_last) inclusive
              ±`tolerance` years.
    * False — year is OUTSIDE the reign even with tolerance
              (e.g. 1807 vs Frederik VI 1808-1839 → False).
    * None  — ruler name unrecognised OR year is None (insufficient
              data to decide).

    `tolerance` is intended for documented boundary cases — most
    callers should pass 0 (strict). The accession-month table is
    NOT consulted here; use `reign_covers_year_strict()` for that.
    """
    win = reign_window(ruler_raw)
    if win is None or year is None:
        return None
    yf, yl = win
    return (yf - tolerance) <= int(year) <= (yl + tolerance)
