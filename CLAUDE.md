# CLAUDE.md — Projekt-readme til Claude

> **Formål:** Dette er min egen onboarding-fil. Den skal læses i starten af hver ny session, så jeg hurtigt har det fulde overblik over projektet "Danmarks 98 Doughnuts" uden at skulle grave i koden hver gang. Den er skrevet til mig selv, ikke til menneskelige læsere.

## TL;DR (30 sekunder)

- **Projekt:** Doughnut Economics MVP for alle 98 danske kommuner - offentlig platform der viser hver kommunes status i forhold til socialt fundament og økologisk loft.
- **Stack:** Next.js 16 (static export) + Tailwind 4 i `webapp/`, Python-scripts i `scripts/`, CSV-data i `data/`, Netlify deploy via GitHub Desktop push til main.
- **Bruger:** August, projektleder i klimateamet, Thisted Kommune. Noob til programmering - skal hjælpes til de enkleste/bedste beslutninger. Undgå terminal så meget som muligt.
- **Deploy:** Bruger IKKE terminal-git. Kun GitHub Desktop + Netlify.
- **Krav til mig:** Lav altid plan først, anbefal LLM-model (Opus/Sonnet/Haiku) til opgaven, skriv dansk uden em-dash.
- **Data-arkitektur (apr 2026):** Webapp læser nu kun fra `data/master_indicators.csv` (long format, genereret af `scripts/build_master_csv.py`). Rådata-CSV'er er bevaret som debug-spor.

## Projektstruktur

```
doughnut/
├── CLAUDE.md                ← denne fil
├── netlify.toml             ← base = webapp, publish = out, functions dir
├── .gitignore               ← ignorerer store zip-filer, biodiversitet_* mapper, node_modules
├── data/                    ← CSV-data
│   ├── master_indicators.csv      ← ★ KONSOLIDERET MASTER-FIL (webapp læser KUN herfra)
│   │                                Long format. Genereres af scripts/build_master_csv.py.
│   ├── README.md                  ← dokumentation af master-skemaet (til forskere/partnere)
│   ├── CHANGELOG.md               ← log over data-ændringer
│   ├── doughnut_scores.csv        ← rådata-spor: sociale indikatorer fra fetch_doughnut_data.py
│   ├── climate_scores.csv         ← CO2e territorialt (klimaregnskabet.dk)
│   ├── luftforurening_scores.csv  ← NO2 + PM2.5 (Miljøportal WFS, DCE/AU)
│   ├── biodiversitet_scores.csv
│   ├── land_use_scores.csv
│   ├── n_landbrug_scores.csv      ← N-loft fra VP3 (Vandområdeplan 3)
│   ├── naeringsstoffer_scores.csv ← N+P fra spildevand (VANDUD)
│   ├── vand_scores.csv
│   ├── forurening_scores.csv      ← affald kg/person
│   ├── consumption_scores.csv     ← genanvendelse
│   ├── cba_2023_estimate.csv      ← forbrugsbaseret CO2 (Osei-Owusu + ENS GA25)
│   ├── democracy_scores.csv       ← valgdeltagelse KV21
│   ├── faellesskaber_scores.csv   ← idræt, kriminalitet, trafik
│   ├── lokalsamfund_scores.csv    ← bibliotek, idrætsfaciliteter
│   ├── lokalsamfund_extra_scores.csv ← klassekvotient, daginst., idrætsudg., pædagoger
│   ├── mobilitet_scores.csv       ← pendling, bilrådighed, offentlig transport
│   ├── velfaerd_extra_scores.csv  ← udsatte børn, NEET
│   ├── sundhed_extra_scores.csv   ← sygehusbenyttelse, afstand læge
│   ├── uddannelse_extra_scores.csv ← kun grundskole (25-29 år)
│   ├── bolig_extra_scores.csv     ← m² pr. person
│   ├── samskabelse_extra_scores.csv ← musikskole
│   └── methodology_note.md        ← metodenote om CBA 2023-justering
├── scripts/                 ← Python fetchers, kør fra rodmappen (ikke fra scripts/)
│   ├── build_master_csv.py        ← ★ konsoliderer alle rådata-CSV'er til master_indicators.csv
│   │                                Skal køres efter ENHVER fetch-scriptkørsel.
│   ├── fetch_doughnut_data.py     ← "hoved-scriptet", henter sociale + klima-fallback
│   ├── fetch_climate_data.py      ← klimaregnskabet.dk (kræver API-nøgle)
│   ├── fetch_luftforurening_data.py
│   ├── fetch_biodiversitet_data.py
│   ├── fetch_land_use_data.py
│   ├── fetch_arealanvendelse_data.py
│   ├── fetch_naeringsstoffer_landbrug.py
│   ├── fetch_democracy_data.py
│   ├── fetch_eco_new_data.py
│   ├── fetch_social_extra_data.py
│   ├── fetch_social_new_data.py
│   ├── statbank_fetcher.py        ← helper til DST API
│   ├── probe_api.py
│   └── check_wfs_layers.py
├── docs/                    ← eksterne API-guides og mappings
│   ├── API_datapunkt_oversigt_v4.1.3.xlsx
│   ├── Energi_Data_Service_API_Guide.pdf
│   └── statbank_doughnut_mapping.md
└── webapp/                  ← Next.js app (base = webapp/ i Netlify)
    ├── netlify.toml         ← (nej, den ligger i root) - Netlify functions ligger her
    ├── package.json         ← next 16, react 19, tailwind 4
    ├── next.config.ts       ← output: "export" (static site)
    ├── app/
    │   ├── layout.tsx       ← header, footer, BaselineProvider, navigation
    │   ├── page.tsx         ← forside: søgefelt + 6 eksempel-kommuner
    │   ├── providers.tsx    ← BaselineProvider wrapper
    │   ├── kommune/[navn]/  ← dynamisk route, static generated for alle 98 kommuner
    │   │   ├── page.tsx     ← server component, fetch kommune-data
    │   │   └── client.tsx   ← client component med donut + compare + scorebars
    │   ├── metode/page.tsx  ← detaljeret metodeside (indikatorer, grænser, kilder)
    │   └── om/page.tsx      ← intro til Doughnut Economics-rammen
    ├── components/
    │   ├── DoughnutRing.tsx     ← SVG doughnut-visualisering (hovedvisuelt element)
    │   ├── ScoreBars.tsx        ← bar-visning af alle kategorier + sub-indikatorer
    │   ├── KommuneCompare.tsx   ← dropdown til at vælge sammenligningskommune
    │   ├── KommuneSearch.tsx    ← autocomplete-søgefelt på forsiden
    │   ├── KommuneTable.tsx     ← (findes men ikke nødvendigvis brugt)
    │   └── BaselineToggle.tsx   ← skift mellem "avg" og "top10" baseline
    ├── lib/
    │   ├── shared.ts            ← INDICATORS, SOCIAL_CATEGORIES, ECOLOGICAL_DIMENSIONS, typer, compute-funktioner
    │   ├── data.ts              ← loadData(), getKommune(), getAllKommuner() - læser CSV'er
    │   └── baseline-context.tsx ← React context for baseline-mode
    └── netlify/functions/
        └── klimaregnskabet.mts  ← proxy-function til klimaregnskabet.dk API (server-side API-nøgle)
```

## Stack og deploy

- **Frontend:** Next.js 16 med `output: "export"` → ren static site i `webapp/out/`. Ingen server-side rendering i prod. Dynamiske routes (kommune-sider) pre-genereres via `generateStaticParams` for alle 98 kommuner.
- **Styling:** Tailwind 4 (med `@tailwindcss/postcss`).
- **Node:** Next.js, React 19, TypeScript 5.
- **Netlify:** `base = "webapp"`, `command = "npm run build"`, `publish = "out"`, functions i `webapp/netlify/functions/`.
- **Netlify function:** `klimaregnskabet.mts` er en proxy der holder `KLIMAREGNSKABET_API_KEY` serverside (sat som env var i Netlify dashboard).
- **Deploy-flow:** Bruger gemmer ændringer → **preview lokalt** → GitHub Desktop commit + push til `main` → Netlify deployer automatisk. Ingen CLI-git, ingen manuel deploy.
- **Lokal preview FØR push:** Dobbeltklik på [`Start udviklerserver.command`](file:///Users/augustseptimiuskrogh/Documents/GitHub/doughnut/Start%20udviklerserver.command) i projektmappen - åbner automatisk `http://127.0.0.1:3000` i browseren. Bemærk: `localhost` virker IKKE (IPv6-problem på Mac), brug altid `127.0.0.1:3000`.

**Nuværende git-branch:** `claude/doughnut-economics-dashboard-IKiZe` (default-branch i repo, fungerer som main for Netlify).

## Datamodel — sådan hænger det sammen

### Grundkoncept

Alle kommuner har et sæt **ratios** hvor `100 = niveau med landsgennemsnit` (sociale) eller `100 = på planetens grænse` (økologiske). For sociale indikatorer er højere bedre, for økologiske er lavere bedre. Inverse indikatorer (Gini, kriminalitet, o.l.) er allerede vendt i dataen så høj værdi = god performance.

### Farvelogik (konsistent på tværs af UI)

**Sociale:** ≥100 grøn (`emerald`), 85-100 amber, <85 rød (`scoreColor` i shared.ts).
**Økologiske:** ≤85 grøn (klart under grænsen), 85-100 amber, >100 rød (overshoot) (`ecoScoreColor` i ScoreBars.tsx).

### INDICATORS (sociale, i shared.ts)

Liste af alle sociale indikatorer med id, navn, DST-tabel, kilde, kategori, inverse-flag, dataYear, baselineLevel (1=WHO/EU, 2=nationalt mål, 3=landsgennemsnit), rawUnit. **~27 sociale indikatorer** per april 2026.

### SOCIAL_CATEGORIES (10 TORUS-trivselsaspekter)

`sundhed`, `uddannelse`, `velfaerd`, `bolig`, `demokrati`, `kultur_fritid`, `tryghed`, `lokalsamfund`, `mobilitet`, `klimatilpasning` (sidstnævnte har ingen indikatorer endnu, er placeholder). Hver kategori har en liste af `indicatorIds` som aggregeres (simpelt gennemsnit) til en kategoriscore via `computeCategoryScores()`.

### ECOLOGICAL_DIMENSIONS (9 planetære grænser, i shared.ts)

`klimapaavirkning`, `forurening` (novel entities - INGEN data endnu), `luftkvalitet`, `cirkularitet`, `naeringsstoffer`, `vand`, `arealanvendelse`, `biodiversitet`, `forbrug_co2`. Multi-indikator-dimensioner (næringsstoffer, vand, cirkularitet, luftkvalitet) bruger **worst-of logic** (max ratio) - hvis bare én sub-grænse overskrides, er hele dimensionen overskredet. Dette er bevidst planetary-boundary-logik, IKKE gennemsnit.

### Ratio-konvention for "forurenings-indikatorer"

Kildedata i CSV'er som `naeringsstoffer_scores.csv`, `vand_scores.csv`, `forurening_scores.csv` gemmer `ratio_inverse = (national_avg / kommune_val) × 100` (lav score = værre). `data.ts::invertToDirectRatio()` konverterer til direkte ratio (`10000 / inverse`) før det vises. **Vær opmærksom på dette når du tilføjer eller fejlfinder nye forurenings-indikatorer.**

### Baseline-toggle (avg vs. top10)

Bruger kan skifte mellem:
- **avg:** ratio mod landsgennemsnit (default)
- **top10:** ratio mod gennemsnittet af de 10 bedste kommuner på den indikator (beregnes dynamisk i browseren via `computeTop10Ratios()`)

Top10 gælder KUN sociale indikatorer. Økologiske har absolutte grænser og ændres ikke.

### KommuneData-type

```ts
interface KommuneData {
  kommune_kode: string;     // fx "787" (Thisted)
  kommune_navn: string;
  ratios: Record<string, number | null>;       // social indikator-ratios (avg-baseline)
  top10_ratios: Record<string, number | null>; // samme, men top10-baseline
  eco_ratios: Record<string, number | null>;   // økologiske dimensions-ratios
  rawValues: Record<string, number | null>;    // faktiske råværdier til UI-visning
  social_avg: number | null;
  overall_avg: number | null;
}
```

### Specialcases i build_master_csv.py

Disse håndteres centralt i build-scriptet (ikke længere i `data.ts`):

- **`cba_2023_estimate.csv`** bruger `kommune` (navn) som nøgle, ikke `kommune_kode`. Hvis en kommune ikke findes i CBA-data, sættes `forbrug_co2 = null` (vises som "data mangler"). Fallback-værdien (366.67) er bevidst fjernet i 2026 for transparens.
- **`kommune_kode === "000"`** er et "Danmark samlet"-aggregat der ikke skal komme i master-CSV (filtreres ved indlæsning af kommunelisten).
- **Worst-of dimension-aggregater** (`_dim_*`-rækker): luftkvalitet, naeringsstoffer, cirkularitet bruger max-ratio på sub-indikatorer. Single-indikator dims får dimension-score = sub-indikatorens ratio.
- **Inverse eco-ratio-konvention** (waste, N, P): kildedata er `(national_avg / kommune_val) × 100`, konverteres til direct via `10000 / inverse` så høj=overshoot.

## Data pipeline - hvordan data opdateres

Datapipelinen er manuel og script-baseret. Der er IKKE CI/CD der henter data automatisk.

### Typisk flow når en indikator skal opdateres

1. **Kør relevant fetch-script** fra rodmappen:
   ```bash
   cd /sti/til/doughnut
   python3 scripts/fetch_XXX_data.py
   ```
2. **Scriptet opdaterer rådata-CSV** i `data/` (eller rodmappen for `fetch_doughnut_data.py` - se kritisk regel nedenfor).
3. **Master-CSV regenereres AUTOMATISK** efter fetchet. Alle 11 fetch-scripts kalder `build_master_csv.auto_build_master()` til sidst. Du behøver IKKE køre build-scriptet manuelt længere.
4. **Preview lokalt** før push: dobbeltklik [`Start udviklerserver.command`](file:///Users/augustseptimiuskrogh/Documents/GitHub/doughnut/Start%20udviklerserver.command) → tjek `http://127.0.0.1:3000`.
5. **Git commit + push via GitHub Desktop** → Netlify bygger og deployer.

**Hvis auto-build fejler:** Rådata-CSV er allerede gemt OK. Kør manuelt:
```bash
python3 scripts/build_master_csv.py
```

### Kritisk driftsregel

**`fetch_doughnut_data.py` SKAL køres fra projektets rodmappe:**

```bash
cd /sti/til/doughnut            # IKKE cd scripts/
python3 scripts/fetch_doughnut_data.py
```

Hvorfor: scriptet gemmer `doughnut_scores.csv` relativt til working directory. Fra `scripts/` havner den et forkert sted og build-scriptet finder den ikke.

**Efter kørsel kopieres hoved-CSV'en altid:**

```bash
cp doughnut_scores.csv data/doughnut_scores.csv
# Master-CSV regenereres automatisk - ingen ekstra kommando
```

**Tjek altid:** Scriptet printer "AUTO-REBUILD af master_indicators.csv" til sidst. Verificer at "Skrev 4402 rækker" (eller flere) og "✓ Master-CSV opdateret" ses i outputtet. Hvis ikke: kør `python3 scripts/build_master_csv.py` manuelt.

### Tilføj en ny indikator (efter april 2026)

1. **Skriv eller udvid et fetch-script** der genererer en CSV med kolonner `kommune_kode, <din_indikator>_ratio, <din_indikator>_raw`. Hvis det er et nyt script: husk at tilføje `auto_build_master()`-blokken til sidst (se eksisterende fetch-scripts som skabelon).
2. **Tilføj entry i `scripts/build_master_csv.py`** under SOCIAL_INDICATORS eller ECO_SUB_INDICATORS med id, csv-filnavn, kolonnenavne, enhed, kilde, dimension
3. **Tilføj entry i `webapp/lib/shared.ts`** under INDICATORS med samme id, samt under SOCIAL_CATEGORIES.indicatorIds eller ECOLOGICAL_DIMENSIONS.subIndicators
4. **For nye eco-sub-indikatorer**: tilføj rawKey-mapping i `webapp/lib/data.ts::ECO_RAW_KEY_MAP`
5. **Opdater metode-siden** (`webapp/app/metode/page.tsx`)
6. Kør fetch-scriptet - master-CSV opdateres automatisk
7. Commit + push

### Klimaregnskabet DNS-fejl

`fetch_climate_data.py` fejler med DNS-fejl hvis VPN/offline. Det er **netværksproblem, ikke kodefejl**. Eksisterende `climate_scores.csv` bruges automatisk som fallback. Ingen handling nødvendig - spild ikke tid på at debugge.

### Hoved-CSV'ens kolonnestruktur (doughnut_scores.csv)

```
kommune_kode, kommune_navn,
<indicator>_ratio × N,
<indicator>_raw × N,
social_avg, ecological_avg, overall_avg
```

Scriptets version (v4.5+) inkluderer `_raw`-kolonner med råværdier til UI-visning. Ældre versioner havde ikke dette.

## Forsiden (`app/page.tsx`)

Hero med titlen "Danmarks 98 Doughnuts", kort forklaring, søgefelt (autocomplete på kommune-navn) og 6 eksempel-kommuner alfabetisk. Alt server-rendered fra `getAllKommuner()`.

## Kommuneside (`app/kommune/[navn]/`)

- **page.tsx (server):** slår kommunen op, henter alle kommuner (til compare-dropdown), sender til client.
- **client.tsx (client):** state for compare-valg + baseline-mode, renderer en eller to doughnuts side-om-side, scoresummary, scorebars.

## Designet er MVP - "brilliant basics", ikke innovation

- Ingen database. Alt er statisk CSV + build-time generation.
- Ingen user accounts, ingen backend bortset fra klimaregnskabet-proxy.
- Ingen tests (hvis der kommer tests, er det enhed/integration, ikke e2e).
- TypeScript strict, men mange "any"-undtagelser pga. CSV-parsing.
- Bevidst enkel CSV-parsing (split(",")) - brækker hvis et felt indeholder komma. Acceptabelt fordi data er kontrolleret.

## Vigtigste pitfalls og ting at huske på

1. **Master-CSV regenereres automatisk** efter alle fetch-scripts (kalder `auto_build_master()`). Du behøver IKKE huske at køre build manuelt. Hvis auto-build fejler: kør `python3 scripts/build_master_csv.py` manuelt.
2. **Scripts skal køres fra rodmappen**, ikke fra `scripts/` (se kritisk driftsregel ovenfor).
3. **Worst-of vs. gennemsnit:** multi-indikator øko-dimensioner bruger max-ratio (planetary boundary-logik), IKKE gennemsnit. Logikken bor nu i `build_master_csv.py`, ikke i TS.
4. **Ratio-konvention for forurenings-indikatorer:** kildedata er `ratio_inverse`, konverteres i build_master_csv.py med `invert_to_direct_ratio()` (10000/inverse).
5. **Farvelogik er OMVENDT for øko vs. social:** sociale vil op, økologiske vil ned.
6. **`kommune_kode === "000"`** er Danmark-aggregat, kommer ikke i master-CSV.
7. **cba_2023_estimate.csv** bruger `kommune`-navn som nøgle, ikke `kommune_kode`. Manglende match → `forbrug_co2 = null` (ingen fallback).
8. **Christiansø** er filtreret fra i CBA-data (0 i kildedata, ~90 indbyggere).
9. **Klimaregnskabet.dk** kræver API-nøgle - både Python-scriptet og Netlify-funktionen. Uden nøgle: DNS-fejl / 500.
10. **Next.js 16 med `output: "export"`** - ingen SSR, ingen runtime API-routes i app/. Alt skal kunne statisk-genereres eller være en Netlify function.
11. **Baseline-mode (avg/top10)** beregnes client-side, men påvirker KUN sociale indikatorer. Økologiske er altid absolutte.
12. **Store filer** som `biodiversitet_2021.zip` (~570 MB) og `.fuse_hidden*` filer er ignoreret i `.gitignore` - MÅ ikke committes.
13. **Deploy:** bruger GitHub Desktop, ikke terminal-git. Tilbyd aldrig at køre `git push` fra terminalen uden først at foreslå Desktop-flow.
14. **Master-CSV'en SKAL committes** - den er ikke i .gitignore. Netlify læser fra den under build.

## Brugerens arbejdsstil og præferencer

- **August, projektleder klimateamet Thisted Kommune.** Noob til programmering, ønsker enkle løsninger og undgår terminal.
- **Brug dansk. Ingen em-dash (-), brug enkelt dash (-).**
- **"Brilliant basics" frem for innovation.** 80/20-mindset. Bedre-gjort-end-perfekt.
- **Direkte, ærlig sparring.** Ingen smiger eller blød pakning. Udfordr antagelser, påpeg blinde vinkler, kald det ud hvis ræsonnement er svagt.
- **Skeln mellem fakta, fortolkning og antagelser** når der er tvivl.
- **Lav altid plan for ændringer først** før jeg koder.
- **Anbefal altid LLM-model** (Opus/Sonnet/Haiku) til opgaven og begrund hvorfor (pris vs. kompleksitet).
- **Korte svar** som default, elaborer når bedt om det.

## LLM-model anbefalinger til dette projekt (rule of thumb)

- **Haiku:** små tekstrettelser, omformuler tekster på about-siden, simple CSV-tjek, formatering.
- **Sonnet:** de fleste kode-ændringer (nye komponenter, indikator-tilføjelser, refaktorering, debugging), mindre script-ændringer, skrivning af dagsordenspunkter/notater.
- **Opus:** arkitektur-beslutninger, komplekse dataflows (nye multi-indikator-dimensioner), større refaktorering på tværs af filer, metodediskussioner om Doughnut-modellen.

Default til Sonnet hvis i tvivl. Nævn altid model-anbefaling før jeg går i gang.

## Hvor finder jeg ting?

- **Ny indikator skal tilføjes:** shared.ts `INDICATORS` + evt. `SOCIAL_CATEGORIES.indicatorIds` + data.ts `loadEcoCsv()`-kald + evt. nyt Python-fetch-script + ny CSV i `data/`.
- **Ny økologisk dimension:** shared.ts `ECOLOGICAL_DIMENSIONS` + data.ts `eco_ratios[...]` + evt. worst-of logik + metode-siden.
- **Ændre farver/thresholds:** shared.ts `scoreColor/scoreBgColor/scoreBarColor` (sociale) og ScoreBars.tsx `ecoScoreColor/ecoBarColor` (økologiske).
- **Tekstrettelser om-siden/metode:** `app/om/page.tsx`, `app/metode/page.tsx`.
- **Header/footer/navigation:** `app/layout.tsx`.
- **Baseline-logik:** `webapp/lib/baseline-context.tsx` + `computeTop10Ratios()` i shared.ts.
- **Compare-funktion:** `components/KommuneCompare.tsx` og state i `client.tsx`.

## Metodedokumentation

- **`data/methodology_note.md`** - CBA 2023-nutidsjustering (Osei-Owusu + ENS GA25). Vigtig for forbrugsbaseret CO2.
- **`app/metode/page.tsx`** - user-facing metode per dimension (scoring, grænser, kilder, begrænsninger).
- **`docs/statbank_doughnut_mapping.md`** - mapping mellem DST-tabeller og Doughnut-indikatorer.
- **`docs/API_datapunkt_oversigt_v4.1.3.xlsx`** - oversigtsskema over API-datapunkter.
- **`docs/Energi_Data_Service_API_Guide.pdf`** - guide til Energi Data Service.

## Vedligehold af denne fil

Opdater CLAUDE.md når:
- Ny dimension eller kategori tilføjes.
- Ratio-konvention ændres.
- Deploy-flow ændres.
- Nye kritiske driftsregler opdages.
- Brugerens præferencer ændres.

Hold den **kort, struktureret og til mig selv**. Intet fluff. Tilføj ikke generel Next.js-dokumentation - jeg kan det.
