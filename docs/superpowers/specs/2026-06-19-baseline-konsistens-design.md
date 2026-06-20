# Design: konsistent og synlig baseline (absolut vs. relativ)

Dato: 19. juni 2026
Status: godkendt design, klar til implementeringsplan

## Problem

"Grøn" betyder noget forskelligt fra dimension til dimension:
- På nogle dimensioner = "inden for en absolut grænse" (luftkvalitet mod WHO, biodiversitet mod EU's
  30/10 %, pesticider mod 0 %, klima mod 3 ton, energi mod 0 % fossil).
- På andre = "bedre end landsgennemsnittet" (næringsstoffer, arealanvendelse, vandindvinding, og næsten
  alle sociale dimensioner).

Forskellen er i dag ikke synlig på det niveau hvor brugeren læser scoren (dimensions-bjælkerne og ringen).
`baselineLevel` findes i data men renderes ingen steder; økologiske dimensioner har kun fri-tekst i
`boundary`. Derudover er `education`'s badge "Mål: 95 %" kosmetisk: scoren er reelt beregnet mod
landsgennemsnit og omskaleres af baseline-toggle (mangler `absoluteScore`).

## Besluttet regel (godkendt)

**Scor mod målet (absolut), hvor der findes en meningsfuld per-kommune-grænse** - det gælder både
biofysiske/juridiske grænser (WHO, drikkevandsnorm) OG vedtagne politiske mål (EU 30/10 %, EU 65 %,
nationalt 95 %-uddannelsesmål, 0 % fossil, 3 ton Paris-budget). **Ellers landsgennemsnit.**

Dette matcher platformens eksisterende baseline-hierarki (Niveau 1/2 slår Niveau 3). Konsekvensen for
scoringen er minimal i praksis: kun `education` skifter (alt andet scorer allerede efter denne logik).
Hovedarbejdet er at gøre klassifikationen **struktureret og synlig**.

## Design

### 1. Klassifikationsmodel (data)

Et struktureret begreb `baselineType: "absolut" | "relativ"` per indikator, og en afledt type per
dimension/kategori.

- **Sociale indikatorer:** udledes direkte af scoringsadfærd - `absoluteScore === true` → "absolut",
  ellers "relativ". (Pt. absolut: `bolig_fossil`, og efter dette design også `education`.)
- **Økologiske sub-indikatorer:** nyt felt `baselineType` på hver `subIndicator` i
  `ECOLOGICAL_DIMENSIONS` (boundary-teksten siger det allerede; vi gør det maskinlæsbart).
- **Dimensions-/kategori-type (afledt):** alle indikatorer samme type → den type; ellers "blandet".

Resulterende klassifikation:

| Dimension | Type |
|---|---|
| Klimapåvirkning | absolut (3 ton) |
| Luftkvalitet | absolut (WHO) |
| Biodiversitet | absolut (EU 30/10 %) |
| Forurening | **blandet** (pesticider/nitrat/genanv. absolut + affald relativ) |
| Næringsstoffer | relativ |
| Vand | relativ |
| Arealanvendelse | relativ |
| Energi (social) | absolut (0 % fossil) |
| Uddannelse (social) | **blandet** (education absolut + 9 relative) |
| Øvrige sociale | relativ |

Kun to dimensioner bliver "blandet". Det er en lille, ærlig undtagelse, ikke reglen.

### 2. Synliggørelse (UI)

- **Dimensions-bjælke (ScoreBars):** et lille mæt mærke vises KUN på "absolut"- og "blandet"-dimensioner
  ("mod mål" hhv. "blandet"). Relative dimensioner får intet mærke (de er normen) og forklares i legenden.
  Dette holder visningen ren (kun ~6 af 20 bjælker får mærke).
- **Udfoldet indikator-visning:** ensartet markør for ALLE indikatorer. Sociale viser allerede
  "Mål: X" / "Baseline: landsgennemsnit". Økologiske sub-indikatorer får tilføjet samme
  "mod mål" / "mod landsgns"-markør (afledt af `baselineType`).
- **Ring-legende (DoughnutRing):** én linje: "Grøn betyder enten 'inden for et fast mål' eller 'bedre end
  landsgennemsnit'. Dimensioner mærket 'mod mål' har en absolut grænse; umærkede måles mod landsgennemsnit."
- **Ringen/donut-grafikken røres ikke** (kan ikke bære tekst pænt).

### 3. Education gøres ægte absolut (#2)

- Scores mod 95 %-målet: `ratio = raw / 95 × 100` (100 = målet nået), klippet ved 150 som øvrige sociale.
- Sættes `absoluteScore: true` så baseline-toggle (avg/top10/gruppe) ikke omskalerer den.
- `absoluteTarget: "95 % (nationalt uddannelsesmål)"` findes allerede → badgen bliver nu ærlig.
- Implementeres via et lille `abs_target`-felt på `education`-entry i `build_master_csv.py` (build'en
  beregner `raw/abs_target×100` når feltet er sat), så det store `fetch_doughnut_data.py` ikke skal røres.
  Feltet er genbrugeligt for fremtidige direkte sociale indikatorer med absolut mål.
- Konsekvens: education falder typisk til amber/rød (de fleste kommuner er under 95 %), og
  Uddannelse-kategorien bliver "blandet". Bevidst og ærligt - i tråd med den valgte regel.

## Filer der berøres

- `webapp/lib/shared.ts` - `baselineType` på øko-sub-indikatorer; `education` får `absoluteScore: true`;
  hjælpefunktion til at udlede dimensions-/kategori-type.
- `scripts/build_master_csv.py` - `abs_target`-håndtering for `education`.
- `data/master_indicators.csv` - regenereres.
- `webapp/components/ScoreBars.tsx` - dimensions-mærke + markør på øko-sub-indikatorer.
- `webapp/components/DoughnutRing.tsx` - legende-linje.
- `webapp/app/metode/page.tsx` - kort note om reglen; opdater education-metode/rationale.
- `CLAUDE.md` - note om `baselineType`-konventionen.

## Non-goals

- Omscore de relative dimensioner (de forbliver mod landsgennemsnit - bevidst, for differentiering).
- Ændre ringen/donut-grafikken.
- Løse at "blandede" dimensioner blander absolutte og relative ratioer i ét gennemsnit/worst-of
  (accepteret MVP-wart; "blandet"-mærket flagger det ærligt).

## Verifikation

Intet testframework i projektet. Verifikation = `npm run build` passerer (104 sider, TypeScript rent)
+ browser-DOM-tjek: education-score falder, dimensions-mærker renderer korrekt på absolutte/blandede
dimensioner, øko-sub-indikatorer viser markør, legende opdateret. Pålidelig metode til at se udfoldet
panel: midlertidig `useState(expanded)` default, reload, DOM-tjek, rul tilbage (jf. erfaring i
`docs/aabne-traade-juni-2026.md`).
