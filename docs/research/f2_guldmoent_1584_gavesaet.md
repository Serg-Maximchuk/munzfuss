# Frederik II's gold of 1584 — the seven-piece set, and whether it is coinage at all

> **Status: OPEN, no decision.** Opened 2026-08-19 while looking for
> `rosenobel_fod` merge/promote candidates. The evidence assembled below
> contradicts how six of the seven pieces are currently classified in
> `data/v2/final/danish_realm.yml`, so the question is larger than the one
> that started it. Nothing was changed in the data. Curator: «це складне
> питання але зараз я не бачу рішення» (2026-08-19).

## Scope

**In scope.** The seven gold pieces Frederik II had struck in 1584 at
Frederiksborg, all carrying the interlaced `F S` monogram, all catalogued by
Hede under the single number **f2h7** with letters A-G and all sharing
**Sieg 29** — the index of the set, not of a type. Their status as coinage or
as medals, and the Münzfuß each does or does not belong to.

**Out of scope.** Frederik II's circulating gold (the 1563-1564 Guldkrone
Klippinge, the Goldgulden line), Dronning Sophias Guldmønt 1591-93 (a separate
Wilcke chapter, `w6j.htm`), and Christian IV's 1611-1629 Rosenobel coinage —
that one is not in question here.

## What started it

`dk-hede-f2h7d` — **1 Engelot 1584**, 5,06 g, gold, Frederiksborg, sole source
danskmoent — sits in `seed_unsorted` and is the last unplaced member of the
set. The six siblings are already distributed across four füsse. The question
put to the sources was: does the Engelot belong to `rosenobel_fod` (as a
fraction of the Rosenobel) or does it need a standard of its own?

An initial weight signal pointed at `rosenobel_fod`: 5,06 / 7,69 = **0,658**,
against the English angel-to-rose-noble relation of exactly ⅔. **That signal
was real arithmetic and the wrong inference** — see §«The metric» below, where
the ⅔ turns out to fall out of Wilcke's own dukat multiples (1½ : 2¼) and to
say nothing about an English prototype.

## The primary source

Julius Wilcke, **«Frederik II.s Guldmønt 1584»**, in *Daler, Mark og Kroner
1481-1914*, København 1931, **pp. 85-90**. The printed volume is not in our
harvest; danskmoent.dk republishes this chapter in full as a standalone page:
<https://www.danskmoent.dk/wilcke/w6g.htm> (fetched 2026-08-19, signed at the
foot «J. Wilcke: Daler, Mark og Kroner 1481-1914, København 1931»).

Wilcke works from Christoffer Walkendorf's Rentemester accounts in
Rigsarkivet, quoted verbatim by him, not from the coins.

### The verdict, verbatim

> «Af det oplyste fremgaar videre, at det ikke var Prøvemønter, her var Tale
> om, end sige noget Forsøg paa at indføre en helt ny Handelsmønt.»

> «De paagældende Stykker kan kun betragtes som **Medailler til festlig Brug,
> ikke som Mønter, slaaede i Omsætningsøjemed**.»

> «**Møntbetegnelserne, der er hentede fra en Række udenlandske Mønter, som
> ikke havde nogen Forbindelse med den hjemlige Mønt i Datiden**, men højst var
> en Mindelse om, en Efterligning af den fornemme fremmede Guldmønt, der
> kursede ved Hoffet, har kun tjent som **Paaskud** til at forene et helt Sæt
> Skuepenge til Christian IV.s Hylding 1584 eller til at overrækkes
> Dronningen.»

So on Wilcke's reading the denomination names — Rosenobel, Engelot,
Portugaløser, Ungersk Gylden — are a pretext for assembling a presentation set,
not a monetary specification, and they carry no relation to the domestic
coinage of the day.

Wilcke also states this **against** an existing tradition, which he names: C. T.
Jørgensen (*Beskr.* p. 60, 1879) held them to be **Prøvemønter**, and Ramus and
Scharling built an argument on them about freeing Danish trade from the
Hanseatic yoke — «ganske forfejlede», says Wilcke.

### The metric — one unit, seven names

Wilcke prints the set's weights **in dukat multiples**, which is the detail that
settles the original question:

| Hede | Wilcke's name | Wilcke's weight | Beskr. | Jørgensen | our g | g per dukat |
|---|---|---|---|---|---:|---:|
| 7a | Portugaløser | 10⅛ Dukat | 158 | 1 | 35,20 | 3,477 |
| 7b | Rosenobel | 2¼ Dukat | 159 | 2 | 7,69 | 3,418 |
| 7c | Dobbelt Dukat | 2 Dukat | 160 | 3 | 6,91 | 3,455 |
| **7d** | **Engelot** | **1½ Dukat** | 161 | 4 | **5,06** | **3,373** |
| 7e | Ungersk-Gylden | 1 Dukat | 163 | 7 | 3,50 | 3,500 |
| 7f | Guld-Krone | 1 Dukat | 162 | 5 | 3,38 | 3,380 |
| 7g | Guld-Gylden | 15/16 Dukat | 164 | 6 | 3,27 | 3,488 |

Median 3,455 g per dukat; the spread 3,373-3,500 is 3,6 % end to end (computed
here from Hede's specimen weights against Wilcke's multiples — neither figure is
Wilcke's own arithmetic).

**The set is specified in a single unit.** Not seven standards, not two — one
dukat scale with foreign names laid over it. `1½ : 2¼ = ⅔` is why the
Engelot-to-Rosenobel ratio came out at the English angel relation; the English
pair is not needed to explain it.

Two catalogue keys we do not currently carry appear here: **Beskr. 158-164**
and **Jørgensen 1-7**.

### The metal

Angerer received **18 Rosenobler to melt** — seven on 22 May 1584, eleven more
on 4 June, both entries quoted by Wilcke from fol. 199 of the 1584/85 account.
Wilcke computes that 18 × 2¼ = 40½ dukat of rosenobel gold, losing something in
the melt, could not yield more than **two sets**.

So the alloy is re-melted English rose-noble gold. Wilcke gives no assay, and
neither does Hede — our records for all seven carry no fineness, correctly.

### Provenance of the surviving pieces

Wilcke traces them from the accounts, and the trail explains why the Engelot is
the odd one out:

- 1628 — Dowager Sophie hands Christian IV 40 000 Daler for the war; the
  Rentekammer receipt of 26 January lists **six** of Frederik's 1584 pieces.
  «**Kun et enkelt Stykke, Engelotten, har Dronningen gemt til Minde om sin
  Husbond.**»
- 1639/40, and repeatedly after — the same six recur in the chamber's stock
  lists, «allerede da betragtet som rene Kuriosa værd at gemme, og slet ikke
  som egentlig Mønt».
- 1652 — the six pass to Frederik III's Kunstkammer.
- Jacobæus, *Museum Regium*, describes and figures all the others but **does not
  know the 1584 Engelot** — so it entered the cabinet after that work, i.e.
  after the early 18th century and before the great Beskrivelse of 1791.

The whole set is «kun kendt i Møntkabinettets Eksemplarer».

## Our data as it stands

| Hede | our id | fuss / phase |
|---|---|---|
| 7a | `unified-dk-hede-f2h7a` | reichsdukatenfuss / I |
| **7b** | `unified-dk-hede-f2h7b` | **rosenobel_fod / I — the phase's only occupant** |
| 7c | `unified-dk-hede-f2h7c` | reichsdukatenfuss / I |
| **7d** | `unified-dk-hede-f2h7d` | **seed_unsorted / hede** |
| 7e | `unified-dk-hede-f2h7e` | reichsdukatenfuss / I |
| 7f | `unified-dk-hede-f2h7f` | f2_guldkrone_fod / II |
| 7g | `unified-dk-hede-f2h7g` | rhinsk_gylden_fod / II |

Every one is single-source (danskmoent / Hede), `verified: false`, no fineness.

`rosenobel_fod` is the exposed one: **its Phase I is 7b and nothing else**, and
the fuss card presently describes a two-phase lineage «Frederik II 1584 →
Christian IV 1611-1629». Phase II (Christian IV, .833, 8,994 g, 13 sources) is
untouched by any of this.

## The open question

Wilcke's verdict cannot be applied to the Engelot alone without applying it to
the set — the seven are one act, one account entry, one Sieg number.

1. **Accept Wilcke in full.** All seven → `exclusions` as `exonumia`
   (CLAUDE.md §9.2). `rosenobel_fod` loses Phase I and becomes a
   Christian IV-only standard; its card and its `events.first_adoption`
   anchor (currently 1584) both need rewriting. Cleanest under §0, and the
   largest change — it moves six already-placed coins.
2. **Exclude 7d only.** Minimal, but it treats seven pieces of one set by two
   different rules, and that asymmetry would have to be written down somewhere
   a reader can see.
3. **Leave as is and weigh the counter-tradition.** Hede and Galster do carry
   them under coin numbers in coin catalogues, and Jørgensen 1879 called them
   Prøvemønter — which Wilcke explicitly rejects, but the disagreement is
   between named authorities, not between a source and a guess.

**What would settle it** — in rough order of decisiveness:

- What Hede's own f2h7 page says about the set's status (our seed carries the
  weights but the page's framing has not been read for this question).
- Galster, *Fremmed indflydelse på Danmarks møntvæsen i nyere tid*,
  Nationalmuseets Arbejdsmark 1959, **p. 117**, cited by danskmoent on the
  Engelot page — Galster reworks Wilcke elsewhere, so his framing here matters.
- Jensen, Jørgen Steen, «Dronning Sophies gavesæt», *Møntsamlernyt* 1/1975,
  **p. XXIV** — a modern treatment of this exact set, also cited by danskmoent.
- Whether Sieg 29 is filed in the coin catalogue or the medal register.

Note on provenance chains (§0b): Jørgensen 1879 → Ramus/Scharling → Wilcke 1931
→ Galster 1959 → Jensen 1975 → Hede is **not** six independent witnesses.
Wilcke argues explicitly against Jørgensen and against Ramus/Scharling; anyone
downstream who follows Wilcke is repeating one reading, not corroborating it.

## Sources

- Wilcke, Julius: «Frederik II.s Guldmønt 1584», in *Daler, Mark og Kroner
  1481-1914* (København 1931), pp. 85-90 —
  <https://www.danskmoent.dk/wilcke/w6g.htm>. Quotes above are verbatim from
  that republication.
- Wilcke, Julius: *Renæssancens Mønt- og Pengeforhold 1481-1588* (København
  1950), Sjette Kapitel, PDF p. 36 (`scripts/cache/wilcke/renaessancens_moent_1950/pages/wilcke_7-6.txt`,
  line 1302) — the same author on the same set nineteen years earlier, calling
  it «det bekendte Sæt paa 7 Guldpenge» among «Skoupendinge og Contrafeyer»,
  by the die-cutter Christoffer Angerer, and referring the reader to «Daler,
  Mark og Kroner p. 85 ff.».
- danskmoent.dk, «Engelot» — <https://www.danskmoent.dk/engelot.htm>:
  «Frederik 2., Engelot 1584, Frederiksborg. (Unik). … Del af Dronning Sophies
  gavesæt. (Hede 7D, Schou 4, Sieg 29) • Vægt: 5,06g». No fineness, no standard.
- Wilcke 1950, Syvende Kapitel (`pages/wilcke_7-7.txt`, section «Engelsk Mønt»)
  — the ENGLISH standards, for contrast only: Rosenobel ca. 1510 = 7,776 g rå /
  7,736 g fin; Angel (Engelot) = 5,184 / 5,157. Not the Danish pieces.
