# The Duchy of Schleswig as a V2 issuing entity — research basis

> Opened 2026-08-25 to answer the four historical questions the handoff brief
> «OPEN, BIG — an entity for the Duchy of Schleswig under the Danish crown»
> put before any implementation. Those questions have answers; this file
> records them with sources, and records the three things the research found
> that the brief did not know.
>
> **Status: research complete, implementation NOT started.** §5 below states
> why, and what the curator has to decide first.

## §1. The four questions, answered

### Q1 — From which year does the Duchy of Schleswig exist, and until when?

From about 1200 until 1864. Wikipedia DE «Herzogtum Schleswig»: the duchy
developed «ab etwa 1200 und existierte bis 1864»; the Danish article dates the
formal end of the ducal style to 1867 («ophørte hertugdømmet Slesvig med at
eksistere som hertugdømme»), the difference being the 1864-67 interval between
the war and the Prussian incorporation.

**The defining constitutional fact, and the one that separates Schleswig from
Holstein throughout:** Schleswig was a fief of the DANISH crown and lay outside
the Holy Roman Empire, where Holstein lay inside it. Wikipedia DA «Hertugdømmet
Slesvig»: «*Det var til 1864 et hertugdømme i personalunion med sine to naboer …
men var i modsætning til Holsten dansk lensområde*» («it was until 1864 a duchy
in personal union with its two neighbours … but was, unlike Holstein, Danish
fief territory»). Wikipedia DE puts the same fact on the 1474 event: Christian I
obtained ducal rank for Holstein from Emperor Friedrich III, «though Schleswig
remained outside the Holy Roman Empire».

This is why a Schleswig entity is not simply a second `royal_holstein`. A
Holstein coin of the Danish king is imperial coinage he strikes as a German
prince; a Schleswig coin is coinage he strikes inside his own kingdom's feudal
sphere.

### Q2 — Who ruled it 1523-1563, and from when was the territory Danish?

| Year | Event | Source |
|---|---|---|
| 1386 | After the Schleswig ducal line dies out, the Schauenburg counts receive the duchy in hereditary investiture from the Danish crown | Wikipedia DE «Herzogtum Schleswig» |
| 1460 | Treaty of Ribe — Christian I elected; «*se bliwen tosamende up ewig ungedelt*» | ibid. |
| 1474 | Friedrich III authorises Christian I, as Duke, to strike gold and silver | Wilcke 1950, 7-2 p. 184 (see §3) |
| 1490 | The duchies divided between Christian I's sons — King Hans and Duke Frederik | Wikipedia DA: «*hertugdømmerne i 1490 blev delt på kryds og tværs mellem Christian 1.'s to sønner … Hans, og dennes yngre bror, Frederik*» |
| 1523 | Duke Frederik accedes as King Frederik I — king AND duke in one person | Wilcke 7-2 p. 186-187 |
| 1533-1536 | Frederik I dies; interregnum and the Counts' Feud; Christian III prevails | — |
| 1544 | Rendsburg Landtag, 19 August — three shares | see Q4 |
| 1559 | Frederik II succeeds to the royal share | — |

So the Danish royal house holds the ducal title continuously from 1460, and the
territory is a Danish fief from long before that.

### Q3 — Interruptions?

None that put Schleswig under a foreign ruler within our window. The one real
discontinuity is the **Counts' Feud (Grevens Fejde) 1534-1536** — a succession
war inside the Oldenburg sphere, not a foreign occupation. No `year_overrides`
exception of the Altona kind is called for.

### Q4 — Where does 1544 leave the ROYAL share?

The Rendsburg Landtag of **19 August 1544** divided Schleswig and Holstein into
three shares among Frederik I's sons — Wikipedia DA: «*i 1544 kom den næste
deling mellem Frederik 1.'s tre sønner, kong Christian 3., Hans den Ældre og
Adolf*». Christian III took the royal share, Hans the Elder the Hadersleben
share, Adolf the Gottorf share. The shares were deliberately interleaved
(«*på kryds og tværs*») to be comparable in tax capacity, not contiguous.

**Adolf took Schloss Gottorf**, together with Husum and Apenrade in Schleswig
and the Holstein offices of Kiel, Oldenburg, Reinbek and Trittau. This is the
fact that governs the mint question in §4 below: from 1544 the seat at
Schleswig/Gottorp is ADOLF's, not the king's.

Later movements: 1580 Hans the Elder dies childless and his share is split
between Frederik II and Adolf; **1721** Frederik IV incorporates the Gottorp
share of Schleswig after the Great Northern War («*I 1721 blev de gottorpske
dele inkorporerede ved en række hyldninger af kongen Frederik IV*»); 1864 the
whole duchy passes to the Prussian-Austrian condominium.

**Terminology.** The established German term for the king's share is
«königlicher Anteil», against «herzoglicher Anteil» for Adolf's — Gesellschaft
für Schleswig-Holsteinische Geschichte, «Landesteilung»: «*Rosa: königlicher
Anteil; gelb: herzoglicher Anteil*». That is the same construction the project
already uses in `royal_holstein`'s German name, «Holsteinischer König-Antheil»,
so a Schleswig counterpart needs no coined term.

## §2. What the project's own research already established

`docs/research/sh_ducal_zone_husum_1514.md` §2-§3, from Wilcke 1950 7-2:

- p. 184 — «*I Aaret 1474 meddelte Kejser Friedrich III. Kong Christian I. som
  Hertug af Holsten Tilladelse til at slaa Guld- og Sølvmønt.*»
- p. 186-187 — after Frederik I's 1523 accession the ducal-zone mint moves from
  Husum to **Slesvig (Gottorp)**, and ducal-standard striking continues under
  him as king: 1526 and 1530 Doppelschilling, 1532 Gottorp klippinge.

So for **Frederik I, 1523-1532, a Slesvig ducal mint is documented.** That is
exactly the year range of the Frederik I records in §4.

## §3. Three findings that change the brief

### (a) The pre-1544 Gottorp routing is a standing curator decision, not a defect

The brief reads the registry's `schleswig → gottorp_duchy` as filing coins
«under a house that did not exist yet — a contradiction inside the committed
data». `trace_coin why` says otherwise. `data/v2/merge_decisions/_cross_entity.yml`
carries a curator call of **2026-07-16**:

> «Curator merge 2026-07-16 (Serhii): ONE coin — Friedrich I ducal Goldgulden
> (Gottorp mint), Galster 122, 1531 … its legends are the ducal type verbatim:
> «FRIDERICVS D HOLSACI» / «MO NOV AVREA SLESVICENSIS» … target_entity =
> gottorp_duchy: the cluster's home, mint Gottorp per f1g122.»

A 1531 coin was placed in `gottorp_duchy` deliberately, on legend evidence,
with the date in plain view. Under that reading `gottorp_duchy` denotes the
DUCAL SPHERE of the duchies, not only the sovereign line from 1544 — and there
is no contradiction in the data. What IS inconsistent is the entity's own
description in `data/i18n/issuing_entities.yml`, which says «Adolf I. 1544 →
Karl Peter Ulrich 1762» while the entity holds 14 finals dated 1543 or earlier.
That is a description to widen, not a routing to change (§0b-1).

Of the six pre-1544 coins with `mint: Schleswig`, one is that 2026-07-16 call,
one (`dk-numista-379084`) is moved to `danish_realm` by a 2026-07-14 split, and
the remaining four are not in `final` at all — they sit in
`classification_decisions/gottorp_duchy.yml` as `no_match_in_final`. **The
render impact of this whole strand is currently zero.**

### (b) The Danish-spelling records are no longer routed to Gottorp — they lost their region instead

The brief describes 48 KMM «Danmark - Slesvig» records being pulled into
`gottorp_duchy`. Measured 2026-08-25: all 52 Danish ones are in
`data/v2/seed/kmk/danish_realm.yml` with `issuing_entity: danish_realm` — the
correct entity — and `mint: None`. `Slesvig` is not an alias in
`mint_registry`, so the value is simply discarded. The defect today is a LOST
REGION, not a misrouting.

### (c) `place: Slesvig` in KMM is heterogeneous, and one third of it contradicts the literature

`place` in the KMM cache is normally a mint — København 3929, Malmø 3359,
Kongsberg 1227, Glückstadt 585, Rendsborg 147. But the Slesvig group does not
behave like a mint attribution: **46 of the 54 records sit on a single register
page, protocol III p. 129**, spanning 1523-1563 and three rulers.

| Ruler | n | Years | Literature |
|---|---:|---|---|
| Frederik 1 | 12 | 1523, 1526, 1527, 1532 | **Supported** — Wilcke 7-2 p. 186-187, ducal mint Husum → Slesvig at the 1523 accession |
| Christian 3 | 12 | 1534, 1536, 1537, 1545 | Plausible, not yet verified here |
| Frederik 2 | 28 | 1537, 1563 | **Contradicted** — see below |

For Frederik II no Slesvig mint is attested. danskmoent «Frederik 2. og hans
mønter» names Bremerholm at Copenhagen Castle for the war years from 1563 and
Dyrehaven at Frederiksborg 1582-1585, and no mint in the duchies. Wilcke's own
«Frederik II.s Flensborg-Mønt» puts the duchy mint at **Flensborg, 1566-1571**,
striking «*Schillinge, Søslinge, Blafferte og Penninge af Korn og Skrot som
Hamburgs og Lübecks*» «*for begge Hertugdømmer*» — three years AFTER the 1563
coins, and at a different town. And per §1 Q4, Gottorf had been Adolf's since
1544, so the king had no seat there to strike from.

The 28 Frederik II records are `nation: Danmark`, denominated 1 mark / 8
skilling / 1 skilling, and catalogued by Schou numbers in the Danish royal
series (117, 120, 140, 145, 152, 164, 165). Everything about them says royal
Danish coinage; only the shared register page says Slesvig.

This vindicates the brief's instinct to keep the value as `Slesvig?` with
`mint_verified: false` — but it also means the group must NOT be promoted
wholesale into a territorial entity, because for 28 of 46 records the sources
say the coin was not struck there.

## §4. What implementation would look like, once §5 is settled

- `data/i18n/issuing_entities.yml` — a new entity paralleling `royal_holstein`,
  German name on the attested «königlicher Anteil» pattern, with the §1 facts
  (Danish fief, outside the Empire, 1460 → 1864, royal share from 1544, Gottorp
  part absorbed 1721) in the de/en/uk description.
- `scripts/lib/mint_registry.py` — a `slesvig` entry kept region-level and
  deliberately NOT aliased onto `schleswig`, so the spelling does not drag the
  Gottorp entity along. The registry is already era-aware and every builder call
  site passes the year (handoff 2026-08-18, commit `1b38390`), so
  `year_overrides` are available if a date boundary is ever needed.
- `data/v2/locations/*.yml` — `consumes_entities` on Denmark and
  Schleswig-Holstein.
- The `year_to: 1543` cap on Denmark's `gottorp_duchy` consume is a SEPARATE
  question and should not be moved in the same change; per §3(a) it implements a
  standing decision.

## §5. What the curator has to decide before any of it

Two questions the sources cannot answer, because they are modelling choices:

1. **Scope of the new entity.** The historically clean unit is «the royal share
   of the Duchy of Schleswig». But per §3(c) the only coins that would populate
   it on present evidence are the 12 Frederik I records (1523-1532) and possibly
   the 12 Christian III ones — not the 28 Frederik II records, which the
   literature places elsewhere. An entity created for 46 coins that only 24 can
   honestly join is worth pausing over.

2. **What to do with the Frederik II 1563 group.** Options: leave them in
   `danish_realm` with no mint (today's state, and defensible); record
   `Slesvig?` as an unverified region without an entity change; or treat the
   register page as a collection-level attribution that our mint field should
   not carry at all. This is a §5-hierarchy call between a museum register and
   the specialist literature, and it is the curator's.

**Nothing has been implemented.** No entity added, no registry entry, no cap
touched.

## §6. Cross-references

- `docs/research/sh_ducal_zone_husum_1514.md` — the ducal-zone standard and the
  1523 Husum → Slesvig mint move
- `docs/handoff.md` «OPEN, BIG — an entity for the Duchy of Schleswig under the
  Danish crown» — the brief this file answers
- `data/v2/merge_decisions/_cross_entity.yml` — the 2026-07-16 and 2026-07-14
  curator calls quoted in §3(a)
