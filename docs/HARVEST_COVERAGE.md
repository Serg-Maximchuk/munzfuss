# Harvest coverage — polities × sources

> **GENERATED — do not hand-edit.** Regenerate with `python scripts/audit_harvest_coverage.py` after any harvest.
> Last generated: 2026-08-10

Tracks **which polity has been harvested from which source**, so a location nobody has touched yet is visible instead of being silently forgotten.

**A number is a presence-and-volume signal, NOT a completeness claim.** It counts what we currently hold for that pair. A non-zero cell does *not* mean the source was exhausted for that polity — verifying that needs a per-source enumeration walk and is deliberately out of scope here. Read a cell as «we have pulled some of this»; read a blank as «we have pulled none of this».

## 1. Seeded — `data/v2/seed/<source>/<entity>.yml`

Entity-keyed, so the polity attribution is the pipeline's own.

| polity | bruun | galster | hede | ikmk | kmk | numismaster | numista | ucoin | years |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `royal_holstein` | 127 | 7 | 153 | 5 | 933 | 188 | 154 | 108 | 1514–1863 |
| `gottorp_duchy` | 53 | 12 |  | 1 | 213 | 168 | 93 |  | 1506–1753 |
| `danish_realm` | 575 | 94 | 680 | 34 | 9800 | 805 | 512 | 592 | 1396–1947 |
| `danish_norway` | 281 | 16 | 267 | 22 | 2599 | 291 | 366 | 210 | 1481–1920 |
| `provisional_govt` |  |  |  |  |  |  |  | 2 | 1850–1851 |
| `schauenburg_pinneberg` | 17 |  |  | 2 |  | 149 | 84 |  | 1538–1640 |
| `sonderburg_duchy` | 7 |  |  |  | 20 | 25 | 11 |  | 1604–1627 |
| `norburg_plon_duchy` | 4 |  |  |  |  | 22 | 2 |  | 1625–1761 |
| `glucksburg_duchy` | 3 |  |  |  |  | 3 |  |  | 1632–1762 |
| `rantzau_county` | 6 |  |  |  |  |  |  |  | 1655–1689 |
| `hanseatic_hamburg` |  |  |  | 13 | 75 |  | 3 | 80 | 1553–1912 |
| `hanseatic_lubeck` | 2 |  |  | 22 | 88 |  |  | 79 | 1490–1801 |
| `fuerstbisthum_luebeck` | 5 |  |  |  |  |  | 17 |  | 1593–1776 |
| `erzbisthum_bremen_verden` | 6 |  |  | 26 | 35 |  | 34 | 133 | 1497–1906 |
| `landgrafschaft_hessen_kassel` | 2 |  |  | 6 | 9 |  | 13 | 412 | 1502–1899 |
| `hochstift_osnabrueck` | 1 |  |  |  |  |  | 60 | 174 | 1566–1805 |
| `german_empire` |  |  |  |  |  |  |  | 27 | 1873–1914 |
| `grafschaft_oldenburg` | 11 |  |  |  | 32 |  | 99 | 35 | 1538–1901 |
| `herzogtum_braunschweig_lueneburg` | 1 |  |  |  | 275 |  | 216 | 1070 | 1545–1875 |
| `herzogtum_sachsen_lauenburg` | 1 |  |  |  |  |  | 16 | 12 | 1610–1830 |
| `grafschaft_schaumburg` |  |  |  | 4 |  | 18 | 2 |  | 1567–1639 |

**Not in any seed (3):** `gesamtstaat`, `prussian_province`, `romania`

## 2. Harvested but NOT yet seeded

Raw Phase-1/2 cache for sources with no seed builder yet. Polity attribution here is **provisional** — mapped from the source's own scope names, not from the pipeline. `~` marks a scope covering several polities, counted once against each: splitting it is the seed builder's job, and presenting an exact per-polity figure before that would be invented precision.

A year span may overshoot a harvest's stated window (NGC was taken at 1480–1914, yet shows 1918). That is not a filter failure: a type whose issue range straddles the boundary is kept whole, because §4 forbids truncating a source's years to fit our own window.

*ngc* — no build_ngc_seed.py yet; polity mapped from NGC region name

| polity | ngc | years |
|---|---:|---|
| `royal_holstein` | ~1185 | 1514–1918 |
| `gottorp_duchy` | 182 | 1590–1753 |
| `danish_realm` | ~1105 | 1591–1918 |
| `danish_norway` | ~1105 | 1591–1918 |
| `provisional_govt` | ~80 | 1514–1851 |
| `schauenburg_pinneberg` | 170 | 1566–1640 |
| `sonderburg_duchy` | 25 | 1604–1627 |
| `norburg_plon_duchy` | 24 | 1625–1761 |
| `glucksburg_duchy` | 4 | 1632–1762 |
| `rantzau_county` | 5 | 1655–1689 |
| `prussian_province` | ~80 | 1514–1851 |
| `hanseatic_lubeck` | ~265 | 1600–1913 |
| `fuerstbisthum_luebeck` | ~265 | 1600–1913 |

## 3. Known gaps — deferred on purpose, not forgotten

An undocumented gap is indistinguishable from a deliberate choice, which is why these are written down rather than left to be rediscovered.

| source | polity | gap |
|---|---|---|
| ngc | `grafschaft_schaumburg` | NGC regions SCHAUMBURG-LIPPE + SCHAUMBURG-HESSEN never walked (post-1640 partition lines). Deferred 2026-08-10. |
| ngc | `hanseatic_lubeck` | NGC region LUBECK (no umlaut, 179 date-rows) never walked — it is a SEPARATE region from LÜBECK, see SOURCES.md §13.13(a). |
| ngc | *(several)* | Only Lübeck, Denmark and the Schleswig-Holstein polities walked. Hamburg (1112 rows), Bremen (607), Oldenburg (240), Lauenburg (17), Brunswick-Lüneburg cluster, Hesse-Cassel and Osnabrück all untouched. |

---

Per-source access notes, quirks and known issues: `docs/SOURCES.md`. How to add a new harvester: `docs/HARVEST_GUIDE.md`.
