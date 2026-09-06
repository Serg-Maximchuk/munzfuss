# danskmoent.dk — Article & Digitised-Literature Index

> **What this file is.** A topic-keyed map of the scholarly article corpus
> transcribed on **danskmoent.dk** (Dansk Mønt, «world's largest website about a
> single country's coins»). It exists so a future session can answer «*which
> danskmoent link do I read to study topic X*» without re-crawling the site.
> Companion to `docs/SOURCES.md §2–§3` (per-source access + quirks); this file is
> the **navigation layer** on top of it.
>
> **How the site is organised (the key fact).** There is **no site-wide «list of
> articles» page.** The de-facto index is the **A–Z bibliography**:
> `https://www.danskmoent.dk/litt<letter>.htm` — `litta.htm … littx.htm`, plus
> `littoe.htm` (Æ/Ø/Å). Each author entry there carries a live link to the work
> transcribed **on the site** (`.htm`) or scanned as **PDF** (`/pdf/`, `/pdf2/`).
> To find everything by author Foo, open `litt<first-letter-of-surname>.htm`.
> (e.g. Wilcke → `littv.htm` under «VW»; Märcher / Moesgaard → `littm.htm`.)
>
> **Access (2026-09).** `WebFetch` is unreliable against this host. Working route:
> the in-app **Browser pane** — navigate to the site once, then run `fetch(url)`
> in `javascript_tool` (same-origin, no bot wall). Directory listing (`/wilcke/`)
> is `403`; individual `.htm`/`.pdf` files serve fine. PDFs: `pdf-viewer` MCP or
> download + `pypdf`.
>
> All paths below are relative to `https://www.danskmoent.dk/`.

---

## 0. Topic → link quick-lookup

| To study… | Read | Why |
|---|---|---|
| **Christian III's Møntreform 1541** (Danish lower-anchor lineage) | `pdf2/Wilcke 7-4.pdf` | Wilcke VII, the reform chapter |
| **Christian II Klippinge + first Møntvalvation** (1513-1523) | `pdf2/Wilcke 7-2.pdf` | Wilcke VII |
| **Kong Hans' Møntreformer / Gyldenregning** (pre-1513) | `pdf2/Wilcke 7-1.pdf` | Wilcke VII |
| **Rigsdaler skilling-count ladder 64→80 ß 1588-1618** (Christian IV phase dating) | `wilcke/w1b.htm … w1g.htm` | Wilcke I, each ß-step date-bounded |
| **Kronemønt (Corona Danica) 1618-1771** | `artikler/hedekron.htm` (Hede) + `wilcke/w6q.htm` (Trankebar) + `harck/NumisRapport97.pdf` (varianter 1618-21) | all three silver Krone-Füße |
| **Kurantmønten 1726-1788 / Kurantdukaten** | `wilcke/w3e.htm` (Kurantdukat), `wilcke/w3f.htm` (Tilløb til Specie), `ernst/kuduaxel.htm` | Wilcke III + Ernst |
| **Specie / Kurant / Rigsbankdaler 1788-1845** | `wilcke/w4a.htm … w4s.htm` | Wilcke IV (Altona / Kbh / Kongsberg mints) |
| **Sølv→Guld-møntfod transition 1845-1914** | `wilcke/w5a.htm … w5e.htm` (incl. `w5d` Møntlov-udkast 1858, `w5e` Tabet af S-H) + `w5.htm` book + `artikler/mm3teo.htm` (Guldmøntfod theory) | Wilcke V + Märcher |
| **Falling Rigsdaler value 1671-1726 (Specie vs Kurant vs Krone)** | `pdf2/AxelNielsen.pdf` | Axel Nielsen 1907, the core study |
| **Rigsmønt vs Courant / 1854 Mønt-Reform** | `pdf2/Collin.pdf` | Collin 1855 |
| **Legal instruments list (Forordninger, Møntlove)** | `artikler/aclove1.htm` (1813-1873), `artikler/aclove3.htm` (1873-1954), `artikler/mord.htm` (enevælden) | canonical instrument names for §1 tier-1 |
| **Slesvig-Holsten monetary history (system-level)** | `soemod/slesholst.htm`, `ernst/kobekraf.htm` (1226-1864 købekraft), `pdf/NR_169_Moesgaard_S-H.pdf` (2026) | overview articles |
| **Holstein-Gottorp mønthistorie** | `ernst/holstgot.htm`, `pdf2/JSJ_HdY.pdf` (Jensen, see SOURCES §3a) | ducal |
| **Altona mint (our S-H track)** | `wilcke/w4a-e.htm` + `wilcke/w4p-r.htm` (Wilcke IV), `artikler/mm2013altona.htm` (Märcher 1813-48), `soemod/somalto.htm`, `soemod/altofrem.htm` | mint-level |
| **Glückstadt mint** | `wilcke/w6s.htm` (Wilcke), `soemod/glueckst.htm`, `pdf/MMf3c5NNUM2015.pdf` (production 1671-73) | mint-level |
| **Speciedaler origin 1537/1563/1572** | `wilcke/w6c.htm` (3 Mark 1563), `wilcke/w6f.htm` (1572), `pdf/elfsborg1.pdf` + `pdf/elfsborg2.pdf` (Aagaard/Märcher 1572) | type monographs |
| **Kong Hans' rhinske Guldgylden / 18½-Karat gold** | `wilcke/w6a.htm` ⭐ (the article that started this index), `galster/galshans.htm`, `hansguld.htm` | Rhinskgyldenfod source |
| **Gyldenmyntordninger overview + skillingstal** | `artikler/skilltal.htm` (Eriksen) | early daler |
| **Medieval / Valdemar-era møntvæsen** | `kaaber1.htm`, `valdvalu.htm`, `artikler/kghvald.htm`, `artikler/ljung.htm` | pre-mission-scope background |

---

## 1. Julius Wilcke — the digitised corpus (I–VII, 1481-1914)

> **Correction to SOURCES.md's old §3:** Wilcke is **seven volumes covering
> 1481-1914**, not «three volumes 1588-1746». danskmoent digitises them
> chapter-by-chapter under `/wilcke/w<N><letter>.htm`, with a per-book cover/TOC
> page at `w<N>.htm` (root, not `/wilcke/`). The `<title>` tag on a chapter page
> is often just the generic book name — the real chapter title is the TOC link on
> the cover page (reproduced below) or the in-body heading.

Bibliography entry listing all of Wilcke's works with links: **`littv.htm`** (under «VW»).

### Wilcke I — *Christian IV's Møntpolitik 1588-1625* (Kbh 1919)
Cover/TOC: `w1.htm` · full PDF: `pdf2/Wilcke_1.pdf`
Chapters track the **rising skilling-count of the Rigsdaler** with exact date-boundaries — directly usable for Christian IV phase dating:

| Page | ß-step / topic | URL |
|---|---|---|
| `w1a` | II. Christian III og Frederik II (intro) | `wilcke/w1a.htm` |
| `w1b` | 4.04.1588–12.05.1602: Rigsdaler → **64 ß d.** | `wilcke/w1b.htm` |
| `w1c` | 12.05.1602–8.09.1602: **66 ß d.** I | `wilcke/w1c.htm` |
| `w1d` | 8.09.1602–3.02.1609: **66 ß d.** II | `wilcke/w1d.htm` |
| `w1e` | 3.02.1609–3.04.1610: **68 ß d.** | `wilcke/w1e.htm` |
| `w1f` | 3.04.1610–4.07.1616: **74 ß d.** | `wilcke/w1f.htm` |
| `w1g` | 4.07.1616–1.05.1618: **80 ß d.** | `wilcke/w1g.htm` |

### Wilcke II — *Møntvæsenet under Christian IV og Frederik III 1625-1670* (Kbh 1924)
Cover: `w2.htm`. Only one chapter transcribed as HTML:
- `wilcke/w2d.htm` — **D. Andre Møntsteder** (incl. Glückstadt), s. 261+

(SOURCES §3 «page-number trap» note: Wilcke II Anm. 53 quotes the «åbent Brev af 12. Juli 1618» introducing Corona Danica; patent text at Wilcke I pp. 156-157.)

### Wilcke III — *Kurantmønten 1726-1788* (Kbh 1927)
Cover: `w3.htm`
- `wilcke/w3a.htm` — Andet Kapitel: Udmøntningen 1726-1788
- `wilcke/w3b.htm` – `w3d.htm` — 1. Mønten i København
- `wilcke/w3e.htm` — **c. 1757-63: Kurantdukaten**
- `wilcke/w3f.htm` — **d. 1764-88: Tilløb til Speciemønt**
- `wilcke/w3g.htm` — 2. Bankens Mønt i København 1759-1764

### Wilcke IV — *Specie- Kurant- og Rigsbankdaler 1788-1845* (Kbh 1929)
Cover: `w4.htm` · review PDF: `pdf2/Wilcke_IV_Anm_Ernst.pdf`
- `wilcke/w4a.htm` – `w4e.htm` — **1. Mønten i Altona-Poppenbüttel 1786-1813**
- `wilcke/w4f.htm` – `w4k.htm` — 2. Mønten i København 1788-1813
- `wilcke/w4l.htm` – `w4m.htm` — 3. Mønten paa Kongsberg 1788-1813
- `wilcke/w4n.htm` — Andet Kapitel (later udmøntning)
- `wilcke/w4o.htm` — Mønten i København
- `wilcke/w4p.htm` – `w4r.htm` — **2. Mønten i Altona**
- `wilcke/w4s.htm` — 3. Mønten paa Kongsberg 1813-14

### Wilcke V — *Sølv- og Guldmøntfod 1845-1914* (Kbh 1930)
Cover: `w5.htm` · review PDF: `pdf2/Wilcke_V_Anm_Ernst.pdf`
- `wilcke/w5a.htm` — a) Christian 8.s sidste år
- `wilcke/w5b.htm` — b) Frederik 7. indtil 1854, Treårskrigen
- `wilcke/w5c.htm` — c) Frederik 7. 1854-1858
- `wilcke/w5d.htm` — **d) Udkast til Møntlov 19. Januar 1858**
- `wilcke/w5e.htm` — e) Frederik 7.s sidste / Christian 9.s første år — **Tabet af Slesvig-Holsten**

### Wilcke VI — *Daler, Mark og Kroner 1481-1914* (Kbh 1931)
Cover: `w6.htm` · review PDF: `pdf2/Wilcke_VI_Anm_Galster.pdf`
Type-monograph set (each `/wilcke/w6<letter>.htm`):

| | Topic | | Topic |
|---|---|---|---|
| `w6a` | **Kong Hans' rhinske Guldgylden** ⭐ | `w6k` | Festspecierne 1596-97 |
| `w6b` | Syvaarskrigen → Frederik II's Møntvæsen | `w6l` | Dansk Sovereign 1608 |
| `w6c` | **Speciedaleren (3 Mark) 1563** | `w6m` | Løvedaleren fra 1608 |
| `w6d` | 1575: 4 Skilling dansk = 4 Skilling lybsk | `w6n` | Danske Guldriddere 1611-13 |
| `w6e` | Frederik II's Flensborg-Mønt | `w6o` | **Dansk Piaster fra 1624** |
| `w6f` | **Speciedaleren 1572** | `w6p` | Møntmærket Viben |
| `w6g` | Frederik II's Guldmønt 1584 | `w6q` | Krone 1618 og Piaster 1624 i Trankebar |
| `w6h` | Stempelskærer Christoffer Angerer | `w6r` | Møntens Folk c. 1620 |
| `w6i` | Prinsens Daler 1590 | `w6s` | **Glückstadt Møntsted** |
| `w6j` | Dronning Sophias Guldmønt 1591-93 | `w6t` | Stempelskærer Jeremias Herclus |

### Wilcke VII — *Renæssancens Mønt- og Pengeforhold 1481-1588* (Kbh 1950)
Cover: `w7.htm`. **PDF-only** (`/pdf2/`). Foundational for the **Danish lower-anchor** period (Christian II Lovkompleks 1514, Christian III 1541):
- `pdf2/Wilcke 7-0.pdf` — Indledning
- `pdf2/Wilcke 7-1.pdf` — Kong Hans' «Møntreformer», Gyldenregning
- `pdf2/Wilcke 7-2.pdf` — **Christian II's Klippinge + første Møntvalvation**
- `pdf2/Wilcke 7-3.pdf` — Grevens Fejde + anden Møntvalvation
- `pdf2/Wilcke 7-4.pdf` — **Christian III's Møntreform** (1541 lineage)
- `pdf2/Wilcke 7-5.pdf` — Markregning; Frederik II's Klippinge + tredje Møntvalvation
- `pdf2/Wilcke 7-6.pdf` — Frederik II's Forsøg paa Møntreform; Dalerregning
- `pdf2/Wilcke 7-7.pdf` — Renæssancetidens Mønter vs Nutiden; Pristal 1875-1948
- `pdf2/Wilcke 7-8.pdf` — Varia

### Loose Wilcke articles (NFM / Numismatiska Meddelanden)
`wilcke/w1651f3.htm` (Kobber-Søsling+Hvid 1651) · `wilcke/wpor1629.htm` (Portugaløser 1629) · `wilcke/wapokryf.htm` (Apokryfe Mønter) · `wilcke/wf4tid.htm` (Fra Frederik IV's Tid) · `wilcke/wc4tid.htm` (Breddaler+Sovereign) · `wilcke/plagiat.htm` · `wilcke/hedeby.htm` (Nordens ældste Møntsted) · `wilcke/w6bkrig1.htm` (Borgerkrigsmønternes Ordning) · PDFs: `pdf2/NumFor_1885-1915.pdf`, `pdf2/PulsMetzner.pdf` (Haderslev møntforpagtere), `pdf2/F3 samler.pdf`, `pdf2/Asiatisk Comp 1749.pdf` (w/ Schou).

---

## 2. Other authors — relevant articles by theme

> Filtered (from ~1134 on-site links) to Møntfod / standards / fineness / reforms /
> named nominals within the project's scope. Specimen-level die-study notes are
> included where they carry standard/fineness data usable on a coin row.

### System-level standards & reforms
- `pdf2/AxelNielsen.pdf` — **Axel Nielsen, «Specier. Kroner. Kurant. En Studie over den faldende Rigsdalerværdi 1671-1726»** (1907) ⭐
- `pdf2/Collin.pdf` — Collin, «Om Rigsmønt og Courant … Mønt-Reformen» (1855)
- `artikler/mm3teo.htm` — Märcher, «Guldmøntfoden — en teoretisk introduktion»
- `artikler/hedekron.htm` — Hede, «Kronemønten 1618-1771»
- `ernst/kuduaxel.htm` — Ernst, «Kurantdukaten — en dansk Dukat»
- `artikler/skilltal.htm` — Eriksen, «De første norske skillingstall … gyldenmyntordningerne»
- `ernst/kobekraf.htm` — Ernst, «Mønt- og pengeforhold … Slesvig-Holsten 1226-1864»
- `ernst/f1g50ern.htm` — Ernst, «Dansk Halv-Sølvgylden»

### Legal-instrument catalogues (for §1 tier-1 instrument names)
- `artikler/aclove1.htm` — A. Christensen, love vedr. møntvæsen **1813-1873**
- `artikler/aclove3.htm` — A. Christensen, love vedr. møntvæsen **1873-1954**
- `artikler/mord.htm` — Mordhorst, oversigt over trykte forordninger (enevælden)

### Slesvig-Holsten / Gottorp / Altona / Glückstadt (German track)
- `soemod/slesholst.htm` — Sømod, Bidrag til Slesvig-Holstens ældre mønthistorie
- `soemod/c1holst.htm` — Sømod, Holstenske mønter fra Christiern I og Hans
- `pdf/NR_169_Moesgaard_S-H.pdf` — Moesgaard, «Lidt om Slesvig-Holsten og mønter» (NR 169, 2026)
- `ernst/holstgot.htm` — Ernst, Holsten-Gottorps ældre mønthistorie
- `ernst/erns1851.htm` — Ernst, den slesvig-holstenske schilling 1851
- `pdf/NumRap_170_PN.pdf` — P. Nielsen, Slesvig-Holsten Gottorp 1/32 taler 1595
- `soemod/somalto.htm` — Sømod, Mønten i Altona
- `soemod/altofrem.htm` — Sømod, Fremmede mønter præget i Altona
- `artikler/mm2013altona.htm` — Märcher, Kgl. Mønt i Altona 1813-1848
- `ernst/erns1795.htm` / `artikler/hatz1795.htm` — Speciedaler Altona 1795
- `artikler/c8h4bkgl.htm` — 1 rigsbankdaler 1847 Altona (variant)
- `soemod/glueckst.htm` / `wilcke/w6s.htm` — Glückstadt Møntsted
- `pdf/MMf3c5NNUM2015.pdf` — Märcher, møntproduktion Glückstadt 1671-73
- `harck/h156harck.htm`, `harck/h163harck.htm`, `soemod/c4h138so.htm` — Glückstad-specier / 16 Sk 1625 (specimen-level)

### Speciedaler / Krone / Piaster / dukat type-studies (specimen-level, standard-bearing)
- `pdf/elfsborg1.pdf` (Aagaard/Märcher) + `pdf/elfsborg2.pdf` — Frederik II speciedaler 1572
- `artikler/kbhspec1624.htm`, `pdf/Harck_NR_130_Sept.pdf` — Kbh specier 1624 / 1646-47
- `harck/NumisRapport97.pdf` — Christian IV kronemønt varianter 1618-1621
- `myst/sahebrae.htm`, `pdf/c4h175Aagaard.pdf`, `ernst/hebr1645.htm`, `pdf/Harck_NR_155_2022.pdf` — Hebræer mønt/dukat lødighed 1644-47 (Glückstadt)
- `c5dobduk.htm` (Hede, Chr V dobbeltdukat), `artikler/hededuka.htm` (Halvanden dukat), `brillekj.htm` (brilledukater)
- `pdf/Frank_Specie_1764.pdf`, `pdf/Frederik_V_MM_FP.pdf`, `artikler/f5h27jac.htm` — Frederik V speciedaler 1764-65
- `pdf/NNUM_2012_3_Spc_1704.pdf`, `artikler/mm15.htm`, `artikler/kgl216.htm` — Speciedaler / 5-dukat 1704
- `soemod/hcspec.htm`, `soemod/conrsom.htm`, `soemod/mordanm.htm` — 19th-c. speciedaler types
- Norwegian randskrift-specier 1687-1696: `myst/svenrand.htm`, `myst/sarand.htm`, `artikler/rand.htm`

### Rigsbank / small change 1813+
- `artikler/hedetegn.htm` — Hede, 12 skilling rigsbanktegn 1813
- `c8hede8c.htm`, `c8hede9.htm` — 4 Sk / 3⅕ Rigsbankskilling 1842 (Altona)
- `soemod/f6h35.htm`, `soemod/f6h38so.htm`, `pdf/FPspejlvendte.pdf`, `pdf/Unionsbladet_2023_2_FP.pdf` — rigsbankskilling / fractional specier

### Kong Hans' Sølvgylden / rhinske Guldgylden (Rhinskgyldenfod)
- `wilcke/w6a.htm` ⭐ (Wilcke), `galster/galshans.htm` (Galster), `hansguld.htm` (Nordbø, norsk gylden)

### Medieval / pre-mission background
- `kaaber1.htm` (Niels Stigsens møntreform 1234/35), `valdvalu.htm` (Valdemarstidens valuta), `artikler/kghvald.htm`, `artikler/ljung.htm`, `artikler/posselt1.htm` (underlødig mønt), `c2njj.htm` (Christian II unionstid), `pdf2/Soelv_guld_penninge.pdf` (Kræmmer, tidlig middelalder)

### Reduction machinery / minting technique
- `soemod/reduk.htm`, `pdf/RedMask_TekMus09.pdf` (Märcher, Kgl. Mønts første reduktionsmaskine)
- `pdf/JCM_datering_2020.pdf` — Moesgaard, møntdatering-metoder (segl, overpræg, vægt, lødighed)

### Concordance tables (fast Lange/Sieg/Sømod number lookup — see SOURCES §3a)
- `hdy.htm` (Hans den Yngre), `alexander.htm` (Alexander) — per-ruler tables.

---

## 3. Maintenance note

This index was built 2026-09-06 by crawling `litt<a-z>.htm` for on-site `.htm`/`.pdf`
links and filtering by Møntfod/standard/fineness/nominal keywords. To refresh or
widen it, re-crawl the A–Z bibliography (the site adds articles over time — e.g.
Numismatisk Rapport issues appear as new `pdf/` entries). When a link here becomes
a **cited** source in the rendered artefact, promote it to a real bibliography
entry per SOURCES §5a + the `<sup>[ref:KEY]</sup>` pool — this index is a
finding-aid, not a citation store.
