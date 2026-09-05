# Rhinsk-Gyldenfod — the Danish Rhenish-gulden gold standard

> **Quick-reference dossier** for the `rhinsk_gylden_fod` Müntzfuß and,
> crucially, for telling the Danish **Rhinsk Gylden** (Rhenish, .75) apart
> from the **Ungersk Gylden / Dukat** (Hungarian, .986 → `reichsdukatenfuss`).
> Built 2026-06-12 after two specimens (Hans ~1497 N#355730, Frederik I 1527
> Galster 59) were found misrouted to `reichsdukatenfuss` because Numista's
> generic "Goldgulden" label hides the fineness distinction.
>
> Ordinance-level spec TABLES (Bruttovægt / Finvægt / stkr-per-mark for each
> issue) live in [`research/wilcke_1514_1541_specs.md`](research/wilcke_1514_1541_specs.md)
> §1-2 — this doc does NOT duplicate them; it adds the standard's definition,
> the classification method, the coinage chronology, and the sources.

## 1. The standard (academic source of record)

**Rhinsk Gylden = 18 Karat (.750) · 72 Stück je Cöllnische Marck rauh ·
3,249 g rauh / 2,437 g fein.** A trade-gold coin of the **Rhenish-Gulden
(Rheingulden) tradition** for the German / north-German market — distinct
from the higher-fineness Hungarian Dukat.

Source of record — **Wilcke 1950** (J. Wilcke, *Renæssancens Mønt- og
Pengeforhold 1481-1588*, København 1950; local cache
`scripts/cache/wilcke/renaessancens_moent_1950/pages/wilcke_7-*.txt`):

- **Frederik I Møntordning, 25 February 1524**, Wilcke **7-2 p. 184**,
  verbatim: «*Vi Fr. … at slaa, i Guld: Nobler (… 23½ Karat … 16 Stkr.),
  **Rinske Gylden (18 Karat, 72 Stkr.)** …*». → refs_pool key
  `wilcke-rhinsk-gylden-1524-standard`.
- **Christian II Møntordning, Sommeren 1514** (Dines Blicher Brev, Malmö),
  Wilcke **7-2 p. 152-153**: Rhinsk Gylden already listed at 72/Mark, 18
  Karat, .750. (Spec table in `wilcke_1514_1541_specs.md` §1.)
- Wilcke 7-2 p. 362-367 derives the fineness explicitly: «*… Gyldenens
  Finhed er derfor slet og ret 18 Karat*».
- Metric anchor: **Wormser Reichsabschied 1495** (Imperial Rhenish-Gulden
  norm, 770 ‰) — cited in the fuss prose as `denmark-ref29-no-url`.

## 2. Rhinsk vs Ungersk — the discriminator is FINENESS, not weight or name

| | **Rhinsk Gylden** (rhinsk_gylden_fod) | **Ungersk Gylden / Dukat** (reichsdukatenfuss) |
|---|---|---|
| Tradition | Rhenish (Rheingulden) | Hungarian-Venetian ducat |
| Fineness | **18 Karat = .750** | **23 Karat 8 Grän = .986** |
| Stk / Cölln. Marck | 72 | 67 |
| Brutto / Fein | 3,249 g / 2,437 g | 3,49 g / 3,44 g |
| Imperial codification | Wormser Rezeß 1495 | Augsburger Reichsmünzordnung 1559 |

The weights overlap enough (~3.2 vs ~3.5 g) that **weight alone does not
decide** a worn specimen; **fineness is the clean discriminator**, and
Numista's generic **"Goldgulden"** label does NOT carry it. **Do not route
a Danish gold gulden by the Numista name** — use the per-coin
**Galster / danskmoent** classification, which states "Rhinsk" vs "Ungersk"
explicitly. This is the trap that misrouted N#355730 and Galster 59.

**Classification recipe** (for the open ~58-coin seed_unsorted gold sweep):
1. Find the coin's **Galster** number (catalog.galster + galster_volume).
2. Open its danskmoent page (`danskmoent.dk/fr/<volume><number>.htm`, e.g.
   `hg27`, `f1g59`, `f1g46`) — the title says «… Rhinsk gylden» or
   «… Ungersk gylden».
3. Cross-check fineness if given: .75 → Rhinsk; .986 → Ungersk.
4. Route: Rhinsk → `rhinsk_gylden_fod`; Ungersk/Dukat → `reichsdukatenfuss`.

## 3. Danish Rhinsk Gylden coinage chronology (who struck it, with Galster)

| Ruler | Year | Galster | Note |
|---|---|---|---|
| **Hans** | **~1497** (undated) | **27A / 27B** | Malmø/København; «den ældste [guldmønt] i Skandinavien» — oldest gold coin in Scandinavia; struck for mercenary pay in the Sten-Sture war. N#355730, Sieg 10, Schou 1-7, Fr 4. |
| Frederik I | 1527 | 59 | Malmø, mintmaster Jørgen Kock. Sieg 35, Schou 1-3, Fr 10. |
| Christian III | 1536 (Roskilde) | 131 | danskmoent corrects Galster's "Gottorp" → Roskilde; .764. |
| Christian III | 1546 (Flensburg) | — | Hede c3h14/c3h15 (1 + 2 Rhinsk Gylden), .75; mintmark Reynold Junge. |
| Frederik II | 1563-1564 | — | Hede f2h3 / f2h6, .77, standardisation; 2,501 g fein. |
| Christian IV | 1625-1632 | — | Hede c4h29 (1625/27/28/32), .76 (wartime); end of the line. |

So the standard runs **~1497 (Hans) → 1632 (Christian IV)** with hiatuses;
Hans ~1497 is the documented start (corrected 2026-06-12 from the earlier
"Frederik I 1527" and the still-earlier wrong "reichsdukatenfuss de-facto
1481" that actually cited this Rhinsk coin).

## 4. The parallel Ungersk / Dukat line (for contrast → reichsdukatenfuss)

| Ruler | Year | Galster | Note |
|---|---|---|---|
| Christian II | 1513 | c2g-89 / c2g-90 | 1 + 2 Ungersk gylden — **earliest documented Danish Ungersk** = the reichsdukatenfuss de-facto anchor. |
| Frederik I | 1531 | 46 | «Ungersk gylden», .986, 3.49 g (danskmoent f1g46). |
| Christian III | 1557 | — | Hede c3h1 / c3h2 (1 + 2 Ungersk Gylden), København. |

De jure imperial codification of the Ungersk/Dukat standard: **Augsburger
Reichsmünzordnung, 19 August 1559**.

## 5. The END of the standard — two jurisdictions, two dates

Researched 2026-09-05 because the Schleswig-Holstein timeline needed a
`std_end.holstein`, and the fuss had none for either scope beyond an
approximate `std_end.anywhere: 1640` whose note read only «Christian IV does
not resume Rhinsk Gylden coinage».

### 5.1 Imperial track — 19 August 1559

The **Augsburger Reichsmünzordnung of 19 August 1559** recognises the Dukat as
the Reich's gold coin (23⅔ Karat, 102-104 Kreuzer) and forbids underweight
gulden; the Goldgulden then leaves circulation «*in den darauffolgenden
Jahrzehnten nach und nach*». The Rhenish Münzverein struck it «*bis zum Ende
des ersten Viertels des 17. Jahrhunderts*» (~1625); 18th-century pieces are
commemorative only, the last a Würzburg New-Year present of 1798.

**It named the Danish coins.** Wilcke 6 (`cache/danskmoent/wilcke/w6a.htm`,
raw page stored), verbatim:

> «Ved Kejser Ferdinands Møntedikt af 19. August 1559 blev med 6 Maaneders
> Varsel saavel Christian III.s som Kong Hans' Guldgylden, baade med 2
> Bjælker og med Stjerne, forbudte og erklæret ugyldige»

So 1559 is not a general displacement that happens to touch Denmark — it voids
the Danish issues by name, with six months' notice.

### 5.2 Danish track — 8 September 1602, and it outlived the edict

The Danish crown went on striking after 1559: Frederik II 1563-1564 and 1584,
Christian IV 1625-1632. The act that actually removes the coin from Danish law
is the **Forordning af 8. September 1602**, whose gold schedule (§3.1 of
`dk_dukat_portugaloeser_fod.md`) prescribes exactly two coins —

| | Stk./Mk. | Karat | Finvægt |
|---|---:|---|---:|
| Portugaløser | 6¾ | 23½ | 33,92 g |
| Ungersk Gylden | 67 | 23⅓ | 3,39 g |

— and **does not list the Rhinsk Gylden at all**. Danish gold is redefined on
the ducat grid; the Rhenish norm has no statutory place after it.

*Strength of the claim:* this is an argument from the silence of a schedule,
not an explicit ban. It is strong because the schedule is comprehensive, but it
is weaker than the 1559 edict's express wording, and should be stated as such.

### 5.3 The 1625-1632 revival was war finance, not a restoration

Harck (`cache/danskmoent/harck/c4guld.extract.txt`), verbatim: «*I dag kendes
den Rhinske Gylden fra følgende årstal: 1625, 1627, 1628 og 1632, og den er
mest almindelig fra 1625*»; «*Mønterne fra 1627 og 1628 er oplagt slået til
anvendelse i forbindelse med trediveårskrigen*». The 1632 issue he separates:
«*må have en ganske anden baggrund, idet Christian IV allerede i 1629 opnår en
særdeles gunstig separatfred med kejseren*».

lex.dk: «*Rhinske gylden blev udmøntet i Danmark ca. 1500-1632*».

### 5.4 Mintage — the coin was NOT rare when struck

Wilcke 6, after Hvitfeldt: «*Efter Hvitfeldt skal Kongen have ladet slaa
150,000 rhinske Gylden til Toget mod Sverige 1497*».

That matters for how the standard is read: the surviving specimens are ones and
twos (Christian III 1546 «unik», Gottorp 1619 «en unik guldgylden», Sonderburg
1619 two pieces), but survival is not mintage — gold was remelted. An argument
that the standard barely circulated, built on how few pieces survive, is
unsound.

**Mintage of the 1625-1632 revival, read from the accounts.** Harck's table
(`cache/danskmoent/harck/nr93_tab01.jpg`, stored) gives the coinage in Rigsdaler,
and the same paragraph gives the rate: «*1 Rhinsk Gylden regnedes for 1,25
Rigsdaler*».

| År (accounts) | Rdl. | → pieces |
|---|---:|---:|
| 1624 | 36.506 | 29.205 |
| 1627 | 2.710 | 2.168 |
| 1632 | 3.212 | 2.570 |
| **total** | **42.428** | **33.942** |

The accounting year runs ahead of the coin date — Harck reads the 1624 accounts
as the 1625-dated coins, «*fremdateret til 1625, da de oplagt er slået med
henblik på de forestående krigsudgifter*», and the 1627 accounts as covering
both the 1627 and 1628 coins.

So ~34.000 pieces, which settles the «~35.000» figure that circulates in
search-engine summaries of this article: approximately right, and now derived
from the source rather than repeated from a summary. The table is an IMAGE, and
neither curl nor WebFetch could reach it; it was retrieved by loading the page
in the in-app browser and fetching the image from the page's own context.

### 5.5 What this settles for the timeline

| Scope | first_adoption | first_mint | last_mint | std_end | demonetisation |
|---|---|---|---|---|---|
| `anywhere` (realm) | **1514** Møntordning Christian II | 1496 | 1632 | **1602** Forordning | ~1700 |
| `holstein` (duchies) | **1495** Wormser Reichsabschied | 1523 | 1664 | **1602** | ~1700 |

`std_end` before `last_mint` in both scopes is not an error: the crown and the
ducal lines both went on striking a standard the law had dropped. The schema
allows it (9_thaler holstein: std_end 1622 < last_mint 1629).

*The open alternative for `holstein`:* 1559 rather than 1602, on the ground that
the duchies were imperial fiefs. Rejected because the royal-Schleswig mints kept
striking under Danish law after the edict — Flensborg issued rhinske gylden
1545-1554 and Frederik II struck in 1563-1564 — so the imperial ban plainly did
not govern them.

## 6. Sources

- **Wilcke 1950**, *Renæssancens Mønt- og Pengeforhold 1481-1588* — ch. 7-1
  (Kong Hans, 1481-1513), 7-2 (Christian II + the 1514/1524 ordinances).
  Local cache `scripts/cache/wilcke/.../wilcke_7-{1,2}.txt`; PDFs at
  `danskmoent.dk/pdf2/Wilcke%207-{1,2}.pdf`. The 1524 standard quote is
  7-2 p. 184.
- **danskmoent.dk** per-coin pages — the authoritative Rhinsk-vs-Ungersk
  label: `fr/hg27.htm` (Hans Rhinsk), `fr/f1g59.htm` (Frederik I 1527
  Rhinsk), `fr/f1g46.htm` (Frederik I 1531 Ungersk), `chr/c3h15.htm`
  (Christian III 1546 Rhinsk). refs_pool keys
  `danskmoent-hans-rhinsk-gylden-1497`, `danskmoent-f1-rhinsk-gylden-1527`,
  `danskmoent-c3-rhinsk-gylden-1546`.
- **Galster**, *Unionstidens Udmøntninger* — the catalogue whose numbering
  (hg = Hans, f1g = Frederik I, c2g = Christian II, c3g = Christian III)
  fixes each coin's Rhinsk/Ungersk identity.
- Ordinance spec tables: [`research/wilcke_1514_1541_specs.md`](research/wilcke_1514_1541_specs.md) §1-2.

## 7. Known stale references to fix

- `docs/research/denomination_lineages.md` (≈L88-89, L143-155) still calls **Hans's
  1481-1513 gold "Ungersk Gylden (~3,49 g fein, .986)"** and uses it as the
  Goldgulden→Reichsdukat pattern exemplar. Per this dossier that is the
  **Rhinsk** coin (.75); the Ungersk exemplar should be Christian II 1513.
  Update when that doc is next touched.
