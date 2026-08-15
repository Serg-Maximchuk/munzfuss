# The Danish ducat standard — Ungersk Gylden, Dukat, Portugaløser

**Subject.** The parameters of Denmark's imperial-gold track — the Ungersk
Gylden / Dukat and its large multiple the Portugaløser — from Frederik II's
Bremerholm gold (1563) to Christian IV's late Copenhagen ducats (1648): what
each period's ordinance decreed, what the pieces actually weigh and assay, when
and by which instrument the parameters changed, and whether the Portugaløser
belongs to this standard or constitutes one of its own.

**Question this dossier settles.** Is the Portugaløser a fraction of the ducat
standard (a 10-ducat denomination) or a separate Münzfuß? Answered in §6:
**a fraction**, and the earlier finding that the 1:10 ratio drifts over time is
**retracted here** — it was an artefact of comparing a Portugaløser of one
period against a ducat of another (§6.2).

**Deliberately out of scope.**

- **The German Reichsdukatenfuß as a system** — the imperial standard's own
  founding, its Reichsmünzordnung basis, and the Gottorp / Rantzau / Lübeck
  issues that hold it. That deserves its own dossier; none exists yet. The
  German realm appears here only twice, both times because the Danish side
  *depends* on it: as the .986 imperial anchor the Danish gold was cut against
  (§1), and as the Hamburg Portugalöser that was the model for the Danish one
  (§5).
- **Schleswig-Holstein's ducal gold** as a jurisdiction. Haderslev 1591-93 (§2)
  is included because it is royal-regency issue in the duchy, on this standard.
- **The 1604 Daler-Klippen** — a separate standard, `115_5_daler_fod`; full
  treatment in `docs/research/daler_klippe_1604.md`. They appear here only in
  §3.2, where the same ordinance that governs them sets the ducat's parameters.
- **Rosenobel, Guldkrone, Rhinsk Gylden** — parallel gold tracks of the same
  reigns, covered in `docs/research/danish_royal_gold_1560_1648.md` §3.4-3.6,
  `nobel_fod.md`, `krone_muentzfuesse.md`, `rhinsk_gylden_fod.md`.

---

## 1. Frederik II, Bremerholm 1563-1588 — the .986 imperial anchor

**Instrument: none identified.** No Danish ordinance fixing these parameters has
been located. What is attested is the coins, via Hede.

| Hede | Nominal | Year | Mint | Brutto | Finhed | Finvægt |
|---|---|---|---|---:|---:|---:|
| f2h1 | 1 Ungersk Gylden | 1563 | København | 3,49 g | 0,986 | 3,442 g |
| f2h4 | 1 Dukat | 1564 | København | 3,49 g | 0,986 | 3,442 g |
| f2h7a | 1 Portugaløser | 1584 | København | 35,2 g | — | — |

**Recomputed.** 233,856 / 3,49 = 67,01 pieces per rough Cologne mark; 3,49 ×
0,986 = 3,4411 g fine. This is the imperial ducat: 67 per rough mark at 23⅔
Karat. The dependency on the German realm is direct — Denmark is not defining a
standard here, it is striking to one already in force in the Reich.

**Gap.** The 1584 Portugaløser (f2h7a) has a rough weight and no fineness in
Hede. At .986 it would be 34,71 g fine = 10,09 contemporary ducats; the piece is
0,32 g heavier rough than the 1592 Haderslev Portugaløser (§2) and 0,55 g
heavier than the 1602 ordinance figure (§3). Whether that reflects a different
standard, a different fineness, or Hede's rounding of a single specimen is
**open** — see §7.1.

---

## 2. Christian IV regency, Haderslev 1591-1593 — Queen Sophie's gold

**Instrument: none identified** — a regency issue in the duchy, mintmaster
Andreas Metzner.

| Hede | Nominal | Years | Brutto | Finhed |
|---|---|---|---:|---:|
| c4h1 | 1 og ½ Portugaløser | 1591, 1592 | — | — |
| c4h4 | 2 Portugaløser | 1592 | 69,74 g | — |
| c4h5 | 1 Portugaløser | 1592 | 34,88 g | — |
| c4h6 | ½ Portugaløser | 1592-1593 | — | — |
| c4h7 | ¼ Portugaløser | 1592-1593 | — | — |
| c4h8 | 1 Ungersk Gylden | 1591-1593 | — | 0,986 |

**Gap — and it is load-bearing.** Hede publishes **no fineness for any Haderslev
Portugaløser**; verified directly in `scripts/cache/hede/c4h5.json`, whose
`specs` block carries `bruttovægt_g: 34.88` and nothing else. Any fine weight
for these pieces is therefore inferred, not attested, and must be marked so —
including in `danish_royal_gold_1560_1648.md` §2.3, which computes 34,88 × 0,986
without flagging the .986 as an assumption.

**Recomputed both ways.** 34,88 × 0,986 = 34,392 g fine = **9,994** ducats of the
1563-64 standard. 34,88 × 0,979 = 34,148 g = 9,923. Under the higher fineness the
piece is exactly ten contemporary ducats; under the lower it is 0,8 % short.

**Open — the Haderslev fineness dispute.** Hede gives .986 for c4h8; three other
sources give .972 (recorded in `danish_royal_gold_1560_1648.md`). This would be
settled by **Ernst, Axel: «Guldudmøntningen i Haderslev 1591-1593», NNUM 1953,
s. 193-198** — named in c4h5's own `litteratur` field and not yet consulted. See
§7.2.

---

## 3. Christian IV, Copenhagen — the ordinance period

### 3.1 Forordning af 8. September 1602

The gold schedule, as printed on danskmoent's Wilcke page. **Provenance, and it
matters:** the page carries an explicit editorial note — «*[Note fra Dansk Mønt:
Nedenstående er vist **Galsters let bearbejdede version af Wilckes skema**]*».
The table below is therefore Galster's lightly reworked rendering of Wilcke's
scheme, not Wilcke's own layout, and citations must say so.

| | Lovbestemt Værdi | Stk. paa kølnsk Mk. | Raavægt | Finhed, Karat | Tusinddele | Finvægt |
|---|---|---|---:|---|---:|---:|
| Portugaløser | 17 Dlr. | 6¾ | 34,65 g | 23½ | 979 | 33,92 g |
| Ungersk Gylden | 1⅝ Dlr. | 67 | 3,49 g | 23⅓ | 972 | 3,39 g |

(The same table's three Daler-Klipping rows belong to `115_5_daler_fod`; the
silver and copper rows are out of scope here.)

**Recomputed.** 233,856 / 67 = 3,4904 g rough; × 23⅓/24 = **3,3934 g** fine —
Galster/Wilcke print 3,39. 233,856 / 6,75 = 34,6453 g; × 23½/24 = **33,9236 g** —
they print 33,92. Both reproduce to the printed precision.

**The change from §1, and it is decreed.** The ducat's fineness drops 23⅔ → 23⅓
Karat (.986 → .972) while the piece-count per rough mark stays at 67 — i.e. the
rough weight is untouched and the fine content falls 1,4 %. Wilcke frames the
ordinance as exactly that: «*Med disse Forhold for Øje er det forklarligt, om man
noget forringede Mønten*».

**Wilcke on what this gold was for**: «*De Guldmønter, der fremkom, kunde ikke
spille nogen virkelig Rolle for Handelssamkvemmet. Deres Forskelligartethed og
indbyrdes afvigende Forholdstal til Sølv viser ogsaa, at de snarere var at anse
for Skuemønt til festlig Lejlighed end som en konstant Handelsmønt*» (s. 73).

**The mutually deviating silver ratios he names, recomputed** against the daler
at 25,983 g fine:

| | ratio gold : silver |
|---|---:|
| Ungersk Gylden (1⅝ Dlr.) | 12,44 |
| 8 Daler Klipping | 12,56 |
| 4 / 6 Daler Klipping | 12,80 / 12,81 |
| Portugaløser (17 Dlr.) | **13,02** |

Wilcke's own figure for the Portugaløser is 13,021 — reproduced exactly. His
contemporary comparanda, same page: England 11,90; Holland 11,29-11,64; France
11,88; southern Germany 12,22-12,24; Sweden after its 1604 ordinance 13,35.

**Consequence for the Portugaløser.** By metal it is 9,997 contemporary ducats
(§6.1); by decreed value it is 17 / 1⅝ = **10,46**. The 4,6 % spread is a tariff
premium on the show-piece, not a difference of standard.

### 3.2 Forordning af 20. November 1604

Wilcke: «*enslydende med Møntordningen af 8. September 1602*», with these
changes — the Portugaløser reduced 17 → **16 Dlr.**, the Ungersk Gylden 1⅝ →
**1 9/16 Dlr.**, «*medens 4 Daler Guldklipping vedblev at have en Værdi af 4
Daler*» (s. 74). The 4-Daler Klipping was itself recut (24 → 24½ per mark, 20 →
20⅓ Karat) — that belongs to `daler_klippe_1604.md`.

**Note what is NOT changed:** the weight and fineness of the Portugaløser and
the Ungersk Gylden are untouched. The 1604 act moves only their **tariff** in
daler. The tariff ratio between them shifts 10,46 → 16 / (1+9/16) = **10,24**,
while the metal ratio stays at 9,997 — direct evidence that the two coins' tariff
and their weight standard are separate variables.

**Wilcke holds that 1602 remains the operative standard**: «*Guldmøntens Værdi er
beregnet efter den oprindelige Møntanordning af 8. September 1602 uanset det i
1604 gjorte Forsøg paa en Nedsættelse, der … næppe har haft varig Betydning*»
(s. 81).

### 3.3 What the struck coins show, 1603-1648

| Hede | Nominal | Years | Brutto | Finhed | Finvægt |
|---|---|---|---:|---:|---:|
| c4h14 | 1 Ungersk Gylden | 1603, 1604, 1607 | 3,49 g | 0,972 | 3,393 g |
| c4h15 | 1 Ungersk Gylden | 1604 | 3,49 g | 0,972 | 3,393 g |
| c4h17 | 1 Ungersk Gylden | 1608, 1611 | 3,49 g | 0,972 | 3,393 g |
| c4h18 | 2 Ungersk Gylden | 1608 | 6,98 g | 0,972 | 6,786 g |
| c4h9 | 1 Portugaløser u.år | 1605 | 34,645 g | 0,979 | 33,923 g |
| c4h30 | ¼ Portugaløser | 1629 | 8,661 g | 0,979 | 8,481 g |
| c4h32 | 2 Dukat | 1644-48 | 6,98 g | 0,979 | 6,835 g |
| c4h35 | ½ Dukat | 1644-46 | 1,745 g | 0,979 | 1,709 g |
| c4h36 | ¼ Dukat | 1646-48 | 0,873 g | 0,979 | 0,854 g |
| c4h37 | 1 Dukat | 1647 | 3,49 g | 0,979 | 3,418 g |
| c4h38, c4h40 | ½ Dukat | 1647 | 1,745 g | 0,979 | 1,709 g |

**The .972 → .979 step is NOT tied to any instrument known to this dossier.** It
is visible in the struck coins from the 1640s Dukat series onward (and already
in the 1605 and 1629 Portugaløsere, which never go to .972 at all) — but no
ordinance decreeing it has been located. Stated as what it is: an observed
change in the coins, undated as a legal act. See §7.3.

---

## 4. Parameter summary

| Period | Instrument | Ducat: stk/mark · Karat · ‰ · fine | Portugaløser: stk/mark · Karat · ‰ · fine |
|---|---|---|---|
| 1563-1588 | none identified | 67 · 23⅔ · 986 · 3,441 g | — · — · — · — (1584 piece: 35,2 g rough only) |
| 1591-1593 | none identified | — · — · 986 (Hede) · — | — · — · **no fineness published** · — (1592: 34,88 g rough) |
| 1602-1611 | Forordning 8.09.1602 | 67 · 23⅓ · 972 · 3,393 g | 6¾ · 23½ · 979 · 33,924 g |
| 1604 | Forordning 20.11.1604 | unchanged; tariff 1⅝ → 1 9/16 Dlr. | unchanged; tariff 17 → 16 Dlr. |
| c. 1629-1648 | none identified | 67 · — · 979 · 3,418 g | 6¾ · — · 979 · 33,92 g |

Cells reading «none identified» / «no fineness published» are gaps in the
sources, not omissions in this table.

---

## 5. What the literature calls the Portugaløser

- **danskmoent.dk** — «*1 Portugaløser har en værdi af 10 Dukat*».
- **Wikipedia (DE), «Portugaleser»** — «*Nachahmung der portugiesischen
  Goldmünze Portuguez*»; «*Es gab ganze, halbe und Viertel-Stücke*». On the
  German dependency: after the Augsburger Reichsmünzordnung of 1559 only Gulden
  and Dukaten were admissible gold coins in the Reich, so «*kamen die
  Portugaleser Mitte des 17. Jahrhunderts allmählich außer Gebrauch und wurden
  ab 1676 nur mehr als Medaillen … ausgeprägt*», those medals corresponding to
  the value of 10 ducats.
- **Auction description of the type outside Denmark** — Künker catalogues a
  Brandenburg piece of Joachim II, 1570, as «*Portugalöser zu 10 Dukaten … 35,21
  g*»; the Danish 1584 piece at 35,2 g rough sits on that German weight, which
  is the second point where the Danish side depends on the Reich.
- **Hamburg's own inscription**, «*nach Portugals Schrot und Korn*», names a
  standard — and names the **Portuguese** one, not the imperial ducat. This is
  the single strongest textual argument for treating the Portugaløser as
  independent, and it is a German-side inscription; no Danish equivalent has
  been found.

**Unverified.** The statement that the term came to denote any gold coin of
10-ducat weight regardless of design comes from a search-engine summary of
danskmoent / Galster pages, not from a page read directly. Not usable as a
citation until the page is opened. See §7.5.

**No source found in this search describes the Portugaløser as having a Münzfuß
of its own.** Every definition locates it by the ducat. That is an absence of a
claim, not a claim of absence.

---

## 6. Verdict: fraction, not a standard

### 6.1 Per-period ratio, recomputed

Each Portugaløser against the ducat **of its own period**:

| Portugaløser | ÷ contemporary ducat | = |
|---|---|---:|
| 1592 Haderslev, 34,88 g @ .986 *(fineness assumed)* | 1563-64, 3,441 g | **9,994** |
| 1602 ordinance, 33,924 g | 1602 ordinance, 3,393 g | **9,997** |
| 1605 struck, 33,918 g | 1603-11 struck, 3,392 g | **9,998** |
| 1629 ¼ ×4, 33,917 g | 1647 Dukat, 3,417 g | **9,927** |

Ten, to within 0,06 % wherever both sides are attested from the same period. The
1629/1647 row is the one cross-period pairing left in the table (no ducat of
1629 is attested) and is the only row below 9,99.

### 6.2 Retraction — the «drift» finding was wrong

An earlier analysis in this project (chat, 2026-08-15) reported the ratio moving
9,854 → 9,997 → 9,926 and concluded the Portugaløser was «about ten, and
drifting», i.e. evidence of independence. **That is withdrawn.** The computation
held the Portugaløser's 1602 fine weight (33,92 g) constant across all periods
and moved only the ducat's fineness. The Portugaløser's own rough weight in fact
changes with each period — 35,2 g (1584) → 34,88 g (1592) → 34,645 g (1602) —
and the two coins were re-cut together. Pairing a 1602 Portugaløser against a
1584 ducat produced a spread that no contemporary ever saw.

The error is recorded rather than deleted: the shape of it — comparing two
quantities from different periods and reading the difference as a trend — is
worth recognising again.

### 6.3 Why the near-identity does not by itself decide anything

Denmark's fuss cards contain many near-collisions of fine weight across
*different* standards — `kronemont` (10½-Krone) vs `kronemont_fine` (13-Krone)
differ by 0,13 %; `9_thaler` vs `8_daler_lybsk_fod` by 0,17 %; `courantdukatenfuss`
vs `guldkrone` (both gold) by 0,73 %; `9_25_thaler`[1] and `18_5_thaler`[2] are
exactly equal. Each of those pairs is two separate legal acts with independently
decreed piece-counts and finenesses whose fine weights happen to coincide.

So a small gap neither merges nor splits. What splits is a separate instrument —
and the Portugaløser and the Ungersk Gylden are **two rows of one table in one
ordinance**, re-tariffed together in 1604, re-cut together across periods.

### 6.4 Consequence for the data

The Portugaløser stays in `reichsdukatenfuss` as fraction `10` (½ = `5`, ¼ =
`5/2`, 2 = `20`). But the card's single `fineness_standard: .98611` is the
imperial anchor, and the Danish ordinance decrees fineness **per denomination**
— 23⅓ for the Gylden, 23½ for the Portugaløser — and changes it per period. Every
Danish gold coin of the 1602 ordinance consequently renders a structural −1,44 %
Δ that belongs to the card, not to the coin. `soll_fein_by_phase` (consumed at
`scripts/lib/compute.py:1027`) is the existing mechanism; it is keyed on phase
alone, so it covers the 1602-1611 phase cleanly but cannot express phase II's
split between Copenhagen .979 and Glückstadt/Tönning .986. Not yet implemented.

### 6.5 Our own data against the standard

44 entries carry `fuss: reichsdukatenfuss` with `year_first ≤ 1660` in
`data/v2/final/danish_realm.yml`. Checked against §4:

- **Fineness follows the periodisation correctly.** Phase I entries run .986
  (1531, 1557, 1563, 1564); phase `I-1602` runs .972 throughout (1603-1608);
  phase II runs .979 without exception (1629-1660). No entry contradicts the
  ordinance schedule.
- **Two entries have no fineness at all** and are correctly unmarked rather than
  filled: `unified-dk-hede-f2h7a` (1584 Portugaløser, 35,2 g) and
  `unified-dk-hede-f2h7c` / `f2h7e` (1584 2 Dukat / Ungersk Gylden). These are §7.1.
- **One divergence: `unified-dk-hede-c3h2`**, 2 Ungersk Gylden 1557, carries
  **.968** where its 1-Gylden sibling `c3h1` of the same year carries .986. Not
  investigated here; it predates the ordinance period and is flagged for a later
  pass rather than explained.
- **The Portugaløser fractions are consistent**: `10` on the 1584 and 1604 whole
  pieces, `5/2` on the 1629 quarter.
- **A confirming find.** `unified-dk-hede-f3h13` is a **10 Dukat of 1653**,
  34,904 g rough at .979 — and 10 × (233,856/67) = 34,904 g exactly. Denmark
  therefore struck, under its own explicit «10 Dukat» name, a piece at precisely
  ten times the ducat's rough weight — 34,171 g fine, i.e. 10 × the 3,417 g
  ducat of its own period. The 1602 Portugaløser is the same construction one
  ordinance earlier: 33,924 g fine = 10 × that period's 3,393 g ducat, reached
  through a different rough/fineness split (6¾ per mark at 23½ Karat rather than
  6,7 at 23⅓). The two pieces differ from each other by 0,7 % — the same amount
  their two periods' ducats differ — because each is ten of its own. The
  10-ducat weight class is the ducat standard's own; the Portugaløser is its
  named variant, not a separate grid.

---

## 7. Open questions

1. **The 1584 Portugaløser (f2h7a).** 35,2 g rough, no fineness, 0,55 g above the
   1602 figure. Would be settled by a fineness for the piece, or by a Frederik II
   gold ordinance if one exists.
2. **Haderslev 1591-93 fineness.** Hede .986 vs three sources .972; no fineness
   at all for the Portugaløsere. Would be settled by **Ernst, NNUM 1953,
   s. 193-198**, named in Hede's own literature list.
3. **The .972 → .979 step.** Visible in the coins, no instrument located. Would
   be settled by a Christian IV gold ordinance between 1611 and 1644, or by
   Wilcke II (1625-1670) treating the period.
4. **The Scharling footnote.** danskmoent prints, after the 1602 table: «*For
   Portugaløserens Vedkommende er der i Scharlings Gengivelse urigtigt anført
   6 39/47 Pf. for 3 39/47 Pf.*» What quantity «Pf.» denotes here is **not
   established** — neither reading maps onto the 6¾ pieces per mark of the table
   (6 39/47 ≈ 6,83; 3 39/47 ≈ 3,83). Would be settled by the surrounding
   paragraph in Wilcke, or by Scharling's own table.
5. **The «any 10-ducat gold coin» definition** (§5) — from a search summary, not
   a read page. Would be settled by opening the danskmoent / Galster page.
6. **Bruun's «6 Daler = 3½ Ungersk Gylden»** contradicts the 1602 ordinance's 1⅝
   Dlr. by 5,5 %. Recorded in `daler_klippe_1604.md`, not adjudicated.

---

## 8. Sources

- **Galster's reworked version of Wilcke's 1602 scheme**, via danskmoent.dk —
  <https://www.danskmoent.dk/wilcke/w1d.htm>. The gold and silver schedule of
  Forordning 8. September 1602 with the column «*Lovbestemt Værdi*». Cite as
  Galster-via-Wilcke, per the page's own editorial note; the underlying scheme is
  Wilcke, *Christian IV.s Møntpolitik 1588-1625* (København 1919), s. 69.
- **Wilcke, Julius**: *Christian IV.s Møntpolitik 1588-1625* (København 1919),
  s. 73 (Skuemønt verdict, comparative silver ratios), s. 74 (the 20.11.1604
  revision), s. 81 (1602 remains operative), via danskmoent.dk as above.
- **Hede** per-type specs, via the parser cache `scripts/cache/hede/*.json` and
  danskmoent's Hede pages (`danskmoent.dk/chr/c4hNN.htm`, `/fr/f2hNN.htm`).
- **Ernst, Axel**: «Guldudmøntningen i Haderslev 1591-1593», *NNUM* 1953,
  s. 193-198 — **not consulted**; named in Hede c4h5's `litteratur`.
- **Galster, Georg**: «Fremmed indflydelse på Danmarks møntvæsen i nyere tid»,
  *Nationalmuseets Arbejdsmark* 1959, s. 115 — named in Hede c4h5's `litteratur`;
  the 1959 paper is already cited at s. 108 in
  `danish_royal_gold_1560_1648.md` for the Guldkrone.
- **danskmoent.dk**, «1 Portugaløser» — <https://www.danskmoent.dk/1portug.htm>.
- **Wikipedia (DE)**, «Portugaleser» — <https://de.wikipedia.org/wiki/Portugaleser>.
- **Künker**, Joachim II 1570 Portugalöser zu 10 Dukaten —
  <https://www.kuenker.de/de/archiv/stueck/177867>.

### Companion dossiers

- `danish_royal_gold_1560_1648.md` — the full gold landscape of these reigns,
  including the parallel Guldkrone / Rhinsk Gylden / Rosenobel tracks.
- `daler_klippe_1604.md` — the Daler-Klippen of the same 1602/1604 ordinances.
- `denomination_lineages.md`, `hierarchical_metal_tiers.md` — cross-standard context.

---

*Opened 2026-08-15. Retraction in §6.2 supersedes the drift finding stated in
chat the same day.*
