#!/usr/bin/env python3
"""Strip project-internal scaffolding out of `verification_note` prose.

WHY (TODO §W step 2)
--------------------
A 2026-05-11 backfill (commit 91d20f1) wrote ~100 verification_notes that
explained an inferred fineness by citing the project's own rulebook:

    «Per Projekt-Konvention (CLAUDE.md §4) auf den kanonischen
     Müntzfuß-Wert (9_thaler, Anker 0.8889) gesetzt; …»

That is the §0z failure in its purest form — a note about a coin naming
an AI-internal document. The migration script was a one-shot in /tmp and
is gone, and no live generator reproduces the wording, so the strings are
frozen in `data/v2/final/**` and can only be fixed there. Absorb gap-fills
`verification_note` (`_enrich_final_entry`) rather than overwriting it, so
a rewrite here survives a re-flow; empirically these notes have survived
every re-flow since May.

The rewrite keeps the ONE fact the §4 pointer was carrying — that the
value is inferred from the standard rather than attested by a source —
and drops where that convention is written down. `fineness_verified:
false` continues to carry the same distinction machine-readably.

Four families, plus fixes that ride along in the same strings:

  1   canonical fineness            (61 notes)
  1b  strict-single-fineness tier   (32 notes)
  2   Krone-Fuß tier + envelope      (6 notes)
  3   a session diary entry          (1 note)

Riding along, because they sit inside the very sentences being rewritten:
  * `9_thaler` and friends — machine fuss ids leaking into reader prose;
    replaced by the display name from `data/shared/fuesse.yml::<id>.name`,
    which §2 tier 2 keeps identical across languages.
  * `fuesse.yml: fineness_display`, `fineness_verified: false`,
    `Im Coin-Datensatz`, `TODO-A-Audit`, `_issues.json` — further §0z
    leaks the old linter could not see.
  * `Mønlov` → `Møntloven` (Danish is mønt + lov; see TODO §W step 7).
  * Decimal separators: comma in de/uk, period in en (§3). The backfill
    wrote periods everywhere.
  * «специмен-толерантність» / «Soll» — calques, replaced by Ukrainian.

WRITING STRATEGY
----------------
Line-based, in the spirit of `lib/yaml_io.edit_coin_field` — no
serialisation round-trip, so the rest of the file is byte-for-byte
untouched (`lib/yaml_io` documents why a round-trip through the wrong
settings reflows an entire 24k-line file). `edit_coin_field` itself
cannot be used: it handles scalars and lists, and `verification_note` is
a nested {de,en,uk} mapping whose values fold across lines.

Usage
-----
    .venv/bin/python scripts/maintenance/rewrite_verification_notes.py
    .venv/bin/python scripts/maintenance/rewrite_verification_notes.py --apply
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
FINAL = ROOT / "data" / "v2" / "final"
FUESSE = ROOT / "data" / "shared" / "fuesse.yml"

FOLD_WIDTH = 200  # lib/yaml_io ruamel_seed profile


def fuss_names() -> dict[str, str]:
    """id -> display name. §2 tier 2: one string across all languages."""
    doc = yaml.safe_load(FUESSE.read_text()) or {}
    out = {}
    for fid, body in doc.items():
        if not isinstance(body, dict):
            continue
        nm = body.get("name")
        if isinstance(nm, str):
            out[fid] = nm
        elif isinstance(nm, dict) and nm.get("de"):
            out[fid] = nm["de"]
    return out


def num(value: str, lang: str) -> str:
    """Decimal separator per §3: comma in de/uk, period in en."""
    return value.replace(".", ",") if lang in ("de", "uk") else value


def delta(raw: str, lang: str) -> str:
    """«-1.31%» -> «−1,31 %» (true minus, non-breaking space)."""
    v = raw.lstrip("-−+")
    sign = "−" if raw.lstrip().startswith(("-", "−")) else "+"
    return f"{sign}{num(v, lang)} %"


KIND = {
    "Scheide": {"de": "Scheidemünze", "en": "Scheidemünze", "uk": "розмінна монета"},
    "Kurant": {"de": "Kurantmünze", "en": "Kurantmünze", "uk": "курантна монета"},
    "gedenk": {"de": "Gedenkmünze", "en": "commemorative issue", "uk": "пам'ятна монета"},
}


def build_replacements(names: dict[str, str]) -> list[tuple[re.Pattern, callable]]:
    W = r"[\s\n]+"  # a fold point is whitespace, possibly a newline + indent

    def rx(template: str) -> re.Pattern:
        return re.compile(W.join(map(re.escape, template.split())).replace(r"\ ", " "))

    def pat(template: str) -> re.Pattern:
        """Template with {} placeholders -> regex tolerant of YAML folds."""
        parts = template.split("{}")
        body = "(.+?)".join(W.join(re.escape(w) for w in p.split()) for p in parts)
        return re.compile(body, re.DOTALL)

    def name_of(fid: str) -> str:
        return names.get(fid, fid)

    out: list[tuple[re.Pattern, callable]] = []

    # ---- family 1b FIRST: its text contains family 1's opening ----------
    for lang, tmpl, make in (
        ("de",
         "Probe nicht direkt belegt. Per Projekt-Konvention (CLAUDE.md §4) für "
         "strikt-monoprobe Müntzfüße der Kategorie 1 ({}, Anker {}) auf den kanonischen "
         "Müntzfuß-Wert gesetzt; Δ {}% gegen den Soll-Wert liegt im ±2-%-Streifen der "
         "zulässigen Spezimen-Toleranz, also widerspricht der angenommene Wert keinem "
         "belegten Datum.",
         lambda m: (f"Probe nicht direkt belegt; aus dem kanonischen Müntzfuß-Standard "
                    f"({name_of(m.group(1))}, Anker {num(m.group(2), 'de')}) übernommen — "
                    f"dieser Fuß kennt nur eine einzige Probe. Δ {delta(m.group(3), 'de')} "
                    f"gegen den Soll-Wert liegt in der Spezimen-Toleranz.")),
        ("en",
         "Fineness not directly attested. Per project convention (CLAUDE.md §4) set to the "
         "canonical Müntzfuß value for strict-single-fineness Category-1 standards ({}, "
         "anchor {}); Δ {}% against the soll value sits within the ±2 % specimen-tolerance "
         "envelope, so the assumed value contradicts no sourced datum.",
         lambda m: (f"Fineness not directly attested; taken from the canonical Müntzfuß "
                    f"standard ({name_of(m.group(1))}, anchor {m.group(2)}) — this standard "
                    f"has a single fineness throughout. Δ {delta(m.group(3), 'en')} against "
                    f"the soll value is within specimen tolerance.")),
        ("uk",
         "Проба не засвідчена джерелом. За проєктною конвенцією (CLAUDE.md §4) для "
         "строго-однопробних стоп Категорії 1 ({}, якірна проба {}) встановлена на канонічне "
         "значення стандарту; Δ {}% проти Soll лежить у смузі ±2 % допустимої "
         "специмен-толерантності, тож припущене значення не суперечить жодному "
         "задокументованому показнику.",
         lambda m: (f"Проба не засвідчена джерелом безпосередньо; узята з канонічного "
                    f"стандарту ({name_of(m.group(1))}, якір {num(m.group(2), 'uk')}) — ця "
                    f"стопа має єдину пробу. Δ {delta(m.group(3), 'uk')} проти нормативу — "
                    f"у межах допуску зразка.")),
    ):
        out.append((pat(tmpl), make))

    # ---- family 1 -------------------------------------------------------
    for lang, tmpl, make in (
        ("de",
         "Probe nicht direkt belegt. Per Projekt-Konvention (CLAUDE.md §4) auf den "
         "kanonischen Müntzfuß-Wert ({}, Anker {}) gesetzt; Δ {}% gegen den Soll-Wert liegt "
         "im ±2-%-Streifen der zulässigen Spezimen-Toleranz.",
         lambda m: (f"Probe nicht direkt belegt; aus dem kanonischen Müntzfuß-Standard "
                    f"({name_of(m.group(1))}, Anker {num(m.group(2), 'de')}) übernommen. "
                    f"Δ {delta(m.group(3), 'de')} gegen den Soll-Wert liegt in der "
                    f"Spezimen-Toleranz.")),
        ("en",
         "Fineness not directly attested. Per project convention (CLAUDE.md §4) set to the "
         "canonical Müntzfuß value ({}, anchor {}); Δ {}% against the soll value sits within "
         "the ±2 % specimen-tolerance envelope.",
         lambda m: (f"Fineness not directly attested; taken from the canonical Müntzfuß "
                    f"standard ({name_of(m.group(1))}, anchor {m.group(2)}). "
                    f"Δ {delta(m.group(3), 'en')} against the soll value is within "
                    f"specimen tolerance.")),
        ("uk",
         "Проба не засвідчена джерелом. За проєктною конвенцією (CLAUDE.md §4) встановлена на "
         "канонічне значення стандарту ({}, якірна проба {}); Δ {}% проти Soll лежить у смузі "
         "±2 % допустимої специмен-толерантності.",
         lambda m: (f"Проба не засвідчена джерелом безпосередньо; узята з канонічного "
                    f"стандарту ({name_of(m.group(1))}, якір {num(m.group(2), 'uk')}). "
                    f"Δ {delta(m.group(3), 'uk')} проти нормативу — у межах допуску зразка.")),
    ):
        out.append((pat(tmpl), make))

    # ---- family 2 -------------------------------------------------------
    def tier(raw: str, lang: str) -> str:
        m = re.match(r"(.+?)\s+(Scheide|Kurant|gedenk),\s*(\.\d+)", raw.strip())
        if not m:
            return raw.strip()
        return f"{m.group(1)} {KIND[m.group(2)][lang]}, {m.group(3)}"

    out += [
        (pat("Proba kanonisch aus Krone-fod-Tier ({}) abgeleitet — Mønlov 23. Mai 1873 "
             "(fuesse.yml: fineness_display). Im Coin-Datensatz nicht aus einer Quelle "
             "(Hede / Sieg / Schou) direkt belegt; Δ-Berechnung fällt innerhalb ±0,3 % des "
             "Soll-Feingewichts, daher mit ±2 %-Envelope nach CLAUDE.md §4 konsistent. "
             "Flagge bleibt fineness_verified: false bis zur Quellen-Attestation."),
         lambda m: (f"Probe aus dem Krone-Fuß abgeleitet ({tier(m.group(1), 'de')}), "
                    f"festgelegt durch die Møntloven af 23. maj 1873. Für dieses Stück nicht "
                    f"aus einer Quelle (Hede / Sieg / Schou) direkt belegt; die Δ-Rechnung "
                    f"bleibt innerhalb 0,3 % des Soll-Feingewichts.")),
        (pat("Fineness canonically inferred from the Krone-fod tier ({}) — Mønlov of 23 May "
             "1873 (fuesse.yml: fineness_display). Not directly attested for this coin record "
             "by a source (Hede / Sieg / Schou); arithmetic check falls within ±0.3 % of the "
             "Soll-Feingewicht, consistent with the ±2 % envelope per CLAUDE.md §4. Flag "
             "stays fineness_verified: false until a source attestation is added."),
         lambda m: (f"Fineness inferred from the Krone-Fuß tier ({tier(m.group(1), 'en')}), "
                    f"set by the Møntloven af 23. maj 1873. Not directly attested for this "
                    f"piece by a source (Hede / Sieg / Schou); the Δ calculation stays within "
                    f"0.3 % of the soll fine weight.")),
        (pat("Проба канонічно виведена з тиру Krone-fod ({}) — Mønlov 23 травня 1873 р. "
             "(fuesse.yml: fineness_display). У записі монети безпосередньо джерелом "
             "(Hede / Sieg / Schou) не атестована; арифметична перевірка дає Δ у межах ±0,3 % "
             "від Soll-Feingewicht, що узгоджується з ±2 %-конвертом за CLAUDE.md §4. "
             "Прапорець fineness_verified: false до додавання атестації з джерела."),
         lambda m: (f"Проба виведена з тиру Krone-Fuß ({tier(m.group(1), 'uk')}), "
                    f"встановленого Møntloven af 23. maj 1873. Для цього примірника джерелом "
                    f"(Hede / Sieg / Schou) не засвідчена; розрахунок Δ лишається в межах "
                    f"0,3 % від нормативної чистої ваги.")),
    ]

    # ---- family 3: a session diary; only two facts are the reader's -----
    out += [
        (pat("TODO-A-Audit (2026-05-03) gegen Numista _issues.json: alle 8 Jahre von 1695 bis "
             "1702 explizit aufgeführt, keine Gap-Marker — Zeitraum als continuous bestätigt. "
             "Eine zuvor eingetragene Raugewichts-Spanne 2,54–2,60 g und eine "
             "analogie-geschätzte Feingehalts-Spanne .500–.625 wurden 2026-05-10 entfernt, da "
             "keine zugängliche Quelle die Werte direkt belegte (per CLAUDE.md §0)."),
         lambda m: ("Jahresspanne 1695–1702 durchgehend belegt (Numista führt alle acht Jahre "
                    "einzeln auf). Raugewicht und Feingehalt sind in den vorliegenden Quellen "
                    "nicht angegeben.")),
        (pat("TODO A audit (2026-05-03) against Numista _issues.json: all 8 years from 1695 to "
             "1702 explicitly enumerated, no gap markers — range confirmed as continuous. A "
             "previously-stated rough-weight range of 2.54–2.60 g and an analogy-estimated "
             "fineness range of .500–.625 were removed on 2026-05-10 because no accessible "
             "source directly attested the values (per CLAUDE.md §0)."),
         lambda m: ("Year range 1695–1702 attested continuously (Numista lists all eight years "
                    "individually). Rough weight and fineness are not given in the available "
                    "sources.")),
        (pat("Аудит TODO A (2026-05-03) проти Numista _issues.json: усі 8 років від 1695 до "
             "1702 явно перелічено, без gap-маркерів — діапазон підтверджено як continuous. "
             "Раніше вказаний діапазон повної ваги 2,54–2,60 г та оцінений за аналогією "
             "діапазон проби .500–.625 видалено 2026-05-10, бо жодне доступне джерело прямо не "
             "підтверджувало ці значення (за CLAUDE.md §0)."),
         lambda m: ("Діапазон 1695–1702 засвідчено суцільно (Numista наводить усі вісім років "
                    "окремо). Повна вага і проба у наявних джерелах не вказані.")),
    ]

    # ---- family 3a: the same diary shape, parameterised over years -----
    out += [
        (pat("TODO-A-Audit (2026-05-03) gegen Numista _issues.json: alle {} Jahre von {} bis {} "
             "explizit aufgeführt, keine Gap-Marker — Zeitraum als continuous bestätigt."),
         lambda m: (f"Jahresspanne {m.group(2)}–{m.group(3)} durchgehend belegt (Numista führt "
                    f"alle {m.group(1)} Jahre einzeln auf).")),
        (pat("TODO A audit (2026-05-03) against Numista _issues.json: all {} years from {} to {} "
             "explicitly enumerated, no gap markers — range confirmed as continuous."),
         lambda m: (f"Year range {m.group(2)}–{m.group(3)} attested continuously (Numista lists "
                    f"all {m.group(1)} years individually).")),
        (pat("Аудит TODO A (2026-05-03) проти Numista _issues.json: усі {} років від {} до {} "
             "явно перелічено, без gap-маркерів — діапазон підтверджено як continuous."),
         lambda m: (f"Діапазон {m.group(2)}–{m.group(3)} засвідчено суцільно (Numista наводить "
                    f"усі {m.group(1)} років окремо).")),
    ]

    # ---- family 3b: the no-per-year-breakdown variant -------------------
    out += [
        (pat("TODO-A-Audit (2026-05-03): Numista führt diesen Typ als einen Range {} ohne "
             "per-year-Aufteilung (is_dated: false); per-year-Breakdown nicht verfügbar — "
             "Zeitraum als continuous belassen, undokumentierte Lücken möglich."),
         lambda m: (f"Numista führt den Typ als geschlossene Spanne {m.group(1)} ohne "
                    f"Einzeljahre; ob innerhalb der Spanne Jahre ohne Karbung liegen, ist aus "
                    f"den vorliegenden Quellen nicht zu entnehmen.")),
        (pat("TODO A audit (2026-05-03): Numista records this type as a single range {} without "
             "per-year split (is_dated: false); per-year breakdown unavailable — range left as "
             "continuous, undocumented gaps possible."),
         lambda m: (f"Numista records the type as a closed range {m.group(1)} without "
                    f"individual years; whether any year within the range saw no striking is "
                    f"not determinable from the available sources.")),
        (pat("Аудит TODO A (2026-05-03): Numista фіксує тип як один range {} без розщеплення "
             "per year (is_dated: false); per-year breakdown недоступний — діапазон збережено "
             "як continuous, можливі недокументовані пропуски."),
         lambda m: (f"Numista подає тип як суцільний проміжок {m.group(1)} без окремих років; "
                    f"чи були в межах проміжку роки без карбування, з наявних джерел не "
                    f"встановити.")),
    ]

    # ---- family 4: notes citing «§4» directly ---------------------------
    out += [
        (pat("Sovereign fineness not attested in the Danish sources (Hede «Finhed ?»); set to "
             "the canonical sovereignfod anchor .9166 (22 kt English Unite that Christian IV "
             "deliberately copied, 1606) per §4 — fineness_verified false."),
         lambda m: ("Probe in den dänischen Quellen nicht angegeben (Hede «Finhed ?»); aus dem "
                    "kanonischen Sovereign-Fuß-Anker .9166 übernommen — 22 Karat nach dem "
                    "englischen Unite, dem Christian IV. 1606 folgte.")),
        (pat("Feingehalt .770 = kanonische Rhinskgyldenfod-Phase-I-Probe (≈ 18½ Karat, "
             "Frederik II.). danskmoent.dk/Hede geben nur das Gewicht (3,27 g); die Probe folgt "
             "aus dem Standard (§4), daher fineness_verified=false."),
         lambda m: ("Probe .770 = kanonische Rhinskgyldenfod-Phase-I-Probe (≈ 18½ Karat, "
                    "Frederik II.). danskmoent.dk und Hede geben nur das Gewicht (3,27 g); die "
                    "Probe folgt aus dem Standard, nicht aus einer Quelle.")),
        (pat("Fineness .770 = the canonical Rhinskgyldenfod Phase-I fineness (≈ 18½ carats, "
             "Frederik II). danskmoent.dk/Hede give the weight only (3.27 g); the fineness "
             "follows from the standard (§4), so fineness_verified=false."),
         lambda m: ("Fineness .770 = the canonical Rhinskgyldenfod Phase-I fineness (≈ 18½ "
                    "carats, Frederik II). danskmoent.dk and Hede give the weight only "
                    "(3.27 g); the fineness follows from the standard, not from a source.")),
        (pat("Проба .770 = канонічна проба Rhinskgyldenfod Фаза I (≈ 18½ карат, Frederik II). "
             "danskmoent.dk/Hede дають лише вагу (3,27 г); проба випливає зі стандарту (§4), "
             "тому fineness_verified=false."),
         lambda m: ("Проба .770 = канонічна проба Rhinskgyldenfod Фаза I (≈ 18½ карат, "
                    "Frederik II). danskmoent.dk і Hede подають лише вагу (3,27 г); проба "
                    "випливає зі стандарту, а не з джерела.")),
    ]

    # ---- family 5: a pointer at our own documentation -------------------
    out += [
        (pat("Projekt-Dokumentation `fuesse.yml` `guldkrone.events.first_adoption.note` zitiert "
             "bereits Ingvardson & Märcher 2010 zur Christian-IV-Predecessor-Continuity."),
         lambda m: ("Zur Kontinuität mit dem Christian-IV-Vorläufer siehe Ingvardson & Märcher "
                    "2010.")),
        (pat("The project's own `fuesse.yml` `guldkrone.events.first_adoption.note` already "
             "cites Ingvardson & Märcher 2010 on Christian IV predecessor continuity."),
         lambda m: ("On continuity with the Christian IV predecessor see Ingvardson & Märcher "
                    "2010.")),
        (pat("У `fuesse.yml` `guldkrone.events.first_adoption.note` уже цитується Ingvardson & "
             "Märcher 2010 щодо continuity Christian-IV-предтечі."),
         lambda m: ("Щодо спадкоємності з попередником доби Кристіана IV див. Ingvardson & "
                    "Märcher 2010.")),
    ]
    return out


def _needs_quoting(text: str) -> bool:
    """A YAML plain scalar cannot contain «: » or « #», or lead with an
    indicator character. Every replacement below is plain-safe; this is the
    guard that keeps it that way if someone edits the wording later."""
    return (": " in text or " #" in text
            or text[:1] in "-?:,[]{}#&*!|>'\"%@`" or text.endswith(":"))


class _Stripped:
    """Match proxy whose groups come back without surrounding whitespace.

    The fold-tolerant patterns join words with `\\s+`, which drops the space
    that preceded a `{}` placeholder — so the capture starts with it. Left
    unstripped that produced «Anker  0,8889» (doubled space) and «Δ − -1,31 %»
    (the sign logic saw " -1.31" and could not strip the minus behind the
    space). Stripping once here fixes every family at the source.
    """

    __slots__ = ("_m",)

    def __init__(self, m):
        self._m = m

    def group(self, i):
        g = self._m.group(i)
        return g.strip() if isinstance(g, str) else g


def refold(raw: str, start: int, end: int, text: str) -> str:
    """Re-emit `text` over [start, end) preserving the `key:` and indent.

    Handles both plain and single-quoted source scalars. Family 2 is stored
    single-quoted because the ORIGINAL text contained «fuesse.yml:
    fineness_display» — a «: » that forces quoting. The rewrite removes it, so
    the value becomes plain-safe and the quotes go with it; emitting plain is
    also what ruamel would produce on the next absorb.
    """
    head = raw.rfind("\n", 0, start) + 1
    line = raw[head:start]
    m = re.match(r"^(\s*)([a-z]{2}): (')?$", line)
    if not m:
        return raw[:start] + text + raw[end:]
    if m.group(3):  # value opens with a quote
        if raw[end:end + 1] == "'":
            end += 1  # whole value matched — drop the quotes with it
        else:
            # The match covers only the FIRST segment of a longer quoted
            # scalar (km-137419 carries a year-range note AND a fineness
            # note in one value). Splice in place and leave the quoting
            # alone; a lone apostrophe would break the scalar, so guard.
            assert "'" not in text, f"apostrophe inside quoted scalar: {text[:60]!r}"
            return raw[:start] + text + raw[end:]
    assert not _needs_quoting(text), f"replacement needs quoting: {text[:60]!r}"
    indent, key = m.group(1), m.group(2)
    cont = indent + "  "
    words, lines, cur = text.split(" "), [], f"{indent}{key}: "
    for w in words:
        if cur.strip() and len(cur) + len(w) + 1 > FOLD_WIDTH:
            lines.append(cur.rstrip() + " ")
            cur = cont
        cur += w + " "
    lines.append(cur.rstrip())
    return raw[:head] + "\n".join(lines) + raw[end:]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    args = ap.parse_args()

    reps = build_replacements(fuss_names())
    grand = 0
    for path in sorted(FINAL.glob("*.yml")):
        raw = path.read_text()
        before = raw
        n = 0
        for rx, make in reps:
            while True:
                m = rx.search(raw)
                if not m:
                    break
                raw = refold(raw, m.start(), m.end(), make(_Stripped(m)))
                n += 1
        if n:
            grand += n
            print(f"  {n:4}  {path.name}")
            if args.apply:
                yaml.safe_load(raw)  # parse guard before touching disk
                path.write_text(raw)
        else:
            assert raw == before
    print(f"{'applied' if args.apply else 'would rewrite'}: {grand} strings")
    if not args.apply:
        print("(dry run — pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
