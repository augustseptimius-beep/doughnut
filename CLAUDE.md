# CLAUDE.md — Projekt-readme til Claude

> **Formål:** Dette er min egen onboarding-fil. Den skal læses i starten af hver ny session, så jeg hurtigt har det fulde overblik over projektet "Danmarks 98 Doughnuts" uden at skulle grave i koden hver gang. Den er skrevet til mig selv, ikke til menneskelige læsere.

## TL;DR (30 sekunder)

- **Projekt:** Doughnut Economics MVP for alle 98 danske kommuner - offentlig platform der viser hver kommunes status i forhold til socialt fundament og økologisk loft.
- **Stack:** Next.js 16 (`output: "export"`) + Tailwind 4 i `webapp/`, Python-scripts i `scripts/`, CSV-data i `data/`, Netlify deploy via GitHub Desktop push til main.
- **Bruger:** August, projektleder i klimateamet, Thisted Kommune. Noob til programmering - skal hjælpes til de enkleste/bedste beslutninger. Undgå terminal så meget som muligt.
- **Deploy:** Bruger IKKE terminal-git. Kun GitHub Desktop + Netlify.
- **Krav til mig:** Lav altid plan først, anbefal LLM-model (Opus/Sonnet/Haiku) til opgaven, skriv dansk uden em-dash.

## Projektstruktur

```
doughnut/
├── CLAUDE.md
├── netlify.toml             ← base = webapp, publish = out
├── data/
│   ├── master_indicators.csv      ← ★ KONSOLIDERET MASTER-FIL (webapp læser KUN herfra)
│   │                                Long format. Genereres af scripts/build_master_csv.py.
│   ├── README.md                  ← skema-dokumentation for master-filen
│   ├── CHANGELOG.md               ← log over data-ændringer
│   ├── methodology_note.md        ← CBA 2023-nutidsjustering
│   ├── klimatilpasning.md         ← metodenote for vejr_skader-indikatoren
│   ├── *_scores.csv               ← rådata-spor (~25 CSV'er). Se data/README.md for fuld liste.
│   └── sundhedsdatabank/
│       └── psyk_tilstande_pr_1000_2025.xlsx  ← Borgere med psykiatriske tilstande pr. 1.000 (Sundhedsdatabank 2025).
│                                               Ikke brugt som aktiv indikator (trækkes ikke automatisk).
│                                               Gemt til evt. fremtidig brug. Alternativ til medicin-indikatoren.
├── scripts/
│   ├── build_master_csv.py        ← ★ konsoliderer alle rådata-CSV'er til master_indicators.csv
│   ├── fetch_doughnut_data.py     ← hoved-script: sociale indikatorer + klima-fallback
│   └── fetch_*.py                 ← øvrige fetchers (~15). Se build_master_csv.py for fuld pipeline.
├── docs/                    ← API-guides og mappings (statbank, Energi Data Service m.fl.)
└── webapp/
    ├── package.json         ← next 16, react 19, tailwind 4
    ├── next.config.ts       ← output: "export" (static site)
    ├── app/
    │   ├── layout.tsx       ← header, footer, navigation, BaselineProvider
    │   ├── page.tsx         ← forside
    │   ├── kommune/[navn]/
    │   │   ├── page.tsx     ← server component
    │   │   └── client.tsx   ← client component (donut, scorebars, vurdering)
    │   ├── metode/page.tsx  ← metodeside
    │   └── om/page.tsx
    ├── components/
    │   ├── DoughnutRing.tsx     ← SVG doughnut-visualisering
    │   ├── ScoreBars.tsx        ← bar-visning af alle kategorier + sub-indikatorer
    │   ├── KommuneSearch.tsx    ← autocomplete-søgefelt på forsiden
    │   ├── BaselineToggle.tsx   ← skift mellem avg og top10 baseline
    │   ├── VurderingBoks.tsx    ← vurderingsboks pr. kommune
    │   ├── VurderingsBjaelke.tsx
    │   └── VurderingPrintView.tsx
    ├── lib/
    │   ├── shared.ts            ← INDICATORS, SOCIAL_CATEGORIES, ECOLOGICAL_DIMENSIONS, typer, compute-funktioner
    │   ├── data.ts              ← loadData(), getKommune(), getAllKommuner()
    │   └── baseline-context.tsx
    └── netlify/functions/
        └── klimaregnskabet.mts  ← proxy for klimaregnskabet.dk API (holder API-nøgle server-side)
```

## Stack og deploy

- **Frontend:** Next.js 16 med `output: "export"` → ren static site i `webapp/out/`. Ingen SSR i prod. Dynamiske routes pre-genereres via `generateStaticParams` for alle 98 kommuner.
- **Netlify:** `base = "webapp"`, `command = "npm run build"`, `publish = "out"`, functions i `webapp/netlify/functions/`.
- **Deploy-flow:** Gem ændringer → preview lokalt → GitHub Desktop commit + push til main → Netlify deployer automatisk.
- **Lokal preview:** Dobbeltklik på [`Start udviklerserver.command`](file:///Users/augustseptimiuskrogh/Documents/GitHub/doughnut/Start%20udviklerserver.command). Brug `http://127.0.0.1:3000` (ikke `localhost` - IPv6-problem på Mac).
- **Nuværende git-branch:** `claude/doughnut-economics-dashboard-IKiZe` (default-branch, fungerer som main for Netlify).

## Datamodel — sådan hænger det sammen

### Grundkoncept

Alle kommuner har et sæt **ratios** hvor `100 = niveau med landsgennemsnit` (sociale) eller `100 = på planetens grænse` (økologiske). For sociale indikatorer er højere bedre, for økologiske er lavere bedre. Inverse indikatorer (Gini, kriminalitet, o.l.) er allerede vendt i dataen.

### Sociale indikatorer og kategorier

Se `INDICATORS` og `SOCIAL_CATEGORIES` i `webapp/lib/shared.ts` for aktuel liste. Indikatorer har felter: id, navn, DST-tabel, kilde, inverse-flag, dataYear, baselineLevel (1=WHO/EU, 2=nationalt mål, 3=landsgennemsnit), rawUnit. Kategoriscorer beregnes som simpelt gennemsnit via `computeCategoryScores()`. Baseline-toggle (avg/top10) påvirker KUN sociale indikatorer - økologiske har absolutte grænser.

### Farvelogik (konsistent på tværs af UI)

**Sociale:** ≥100 grøn (`emerald`), 85-100 amber, <85 rød (`scoreColor` i shared.ts).
**Økologiske:** ≤85 grøn, 85-100 amber, >100 rød - overshoot (`ecoScoreColor` i ScoreBars.tsx).

### ECOLOGICAL_DIMENSIONS (8 planetære grænser)

Se `ECOLOGICAL_DIMENSIONS` i `webapp/lib/shared.ts` for aktuel liste. De fleste dimensioner er multi-indikator og bruger **worst-of logic** (max ratio) - hvis bare én sub-grænse overskrides, er hele dimensionen overskredet. Dette er bevidst planetary-boundary-logik, IKKE gennemsnit. Eksempler: klimapaavirkning (territorial + forbrugsbaseret CO₂), naeringsstoffer (N/P-belastning + vandområdernes økologiske tilstand VP3), biodiversitet (bioscore ≥8 mod 30% og ≥12 mod 10%), luftkvalitet, cirkularitet, vand, arealanvendelse. Kun forurening (pesticider) er single-indikator. **Designprincip:** én planetær grænse = én dimension; flere opgørelsesmetoder/indikatorer for samme grænse er sub-indikatorer, ikke separate dimensioner.

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

## Data pipeline - hvordan data opdateres

Datapipelinen er manuel og script-baseret. Der er IKKE CI/CD der henter data automatisk.

### Typisk flow når en indikator skal opdateres

1. **Kør relevant fetch-script** fra rodmappen:
   ```bash
   cd /sti/til/doughnut
   python3 scripts/fetch_XXX_data.py
   ```
2. Scriptet opdaterer rådata-CSV i `data/` og kalder `auto_build_master()` automatisk.
3. **Preview lokalt** → dobbeltklik [`Start udviklerserver.command`](file:///Users/augustseptimiuskrogh/Documents/GitHub/doughnut/Start%20udviklerserver.command).
4. **GitHub Desktop commit + push** → Netlify deployer.

**Tjek altid:** Scriptet skal printe "✓ Master-CSV opdateret" til sidst. Hvis ikke: kør `python3 scripts/build_master_csv.py` manuelt.

### Kritisk driftsregel

**`fetch_doughnut_data.py` SKAL køres fra projektets rodmappe:**
```bash
cd /sti/til/doughnut            # IKKE cd scripts/
python3 scripts/fetch_doughnut_data.py
```
Scriptet gemmer direkte til `data/doughnut_scores.csv`. Fra `scripts/` havner filen forkert.

### Tilføj en ny indikator

1. Skriv/udvid fetch-script med kolonner `kommune_kode, <id>_ratio, <id>_raw`. Tilføj `auto_build_master()`-blok (se eksisterende scripts som skabelon).
2. Tilføj entry i `scripts/build_master_csv.py` (id, csv-fil, kolonner, enhed, kilde, dimension).
3. Tilføj entry i `webapp/lib/shared.ts` under `INDICATORS` og `SOCIAL_CATEGORIES.indicatorIds` eller `ECOLOGICAL_DIMENSIONS.subIndicators`.
4. Ny eco-sub-indikator: tilføj rawKey-mapping i `webapp/lib/data.ts::ECO_RAW_KEY_MAP`.
5. Opdater `webapp/app/metode/page.tsx`.
6. Kør fetch-scriptet og commit.

### Klimaregnskabet DNS-fejl

`fetch_climate_data.py` fejler med DNS-fejl hvis VPN/offline. Det er netværksproblem, ikke kodefejl. Eksisterende `climate_scores.csv` bruges som fallback. Ingen handling nødvendig.

## Designet er MVP - "brilliant basics", ikke innovation

- Ingen database. Alt er statisk CSV + build-time generation.
- Ingen user accounts, ingen backend bortset fra klimaregnskabet-proxy.
- TypeScript strict, men mange "any"-undtagelser pga. CSV-parsing.
- Bevidst enkel CSV-parsing (split(",")) - brækker hvis felt indeholder komma. Acceptabelt fordi data er kontrolleret.

## Vigtigste pitfalls og ting at huske på

1. **Master-CSV SKAL committes** - den er ikke i .gitignore. Netlify læser fra den under build.
2. **Scripts fra rodmappen** - ikke fra `scripts/` (se kritisk driftsregel ovenfor).
3. **Worst-of, ikke gennemsnit** - øko-dimensioner med sub-indikatorer bruger max-ratio. Logikken bor i `build_master_csv.py`.
4. **Inverse ratio-konvention** - kildedata for forurenings-indikatorer (N, P, affald, pesticider, nitrat, vandindvinding) er `(national_avg / kommune_val) × 100`. Konverteres via `10000/inverse` i `build_master_csv.py`.
5. **cba_2023_estimate.csv** bruger `kommune`-navn som nøgle, ikke `kommune_kode`. Manglende match → `forbrug_co2 = null` (ingen fallback). Christiansø er filtreret fra.
6. **Farvelogik er OMVENDT:** sociale vil op (≥100 = grøn), økologiske vil ned (≤85 = grøn).
7. **GitHub Desktop** - aldrig terminal-git. Aldrig `git push` fra terminalen.
8. **Klimaregnskabet.dk kræver API-nøgle** - i Python-scriptet OG som Netlify env var (`KLIMAREGNSKABET_API_KEY`).

## Brugerens arbejdsstil og præferencer

- **August, projektleder klimateamet Thisted Kommune.** Noob til programmering, ønsker enkle løsninger og undgår terminal.
- **Brug dansk. Ingen em-dash (-), brug enkelt dash (-).**
- **"Brilliant basics" frem for innovation.** 80/20-mindset. Bedre-gjort-end-perfekt.
- **Direkte, ærlig sparring.** Ingen smiger eller blød pakning. Udfordr antagelser, påpeg blinde vinkler.
- **Lav altid plan for ændringer først** før jeg koder.
- **Anbefal altid LLM-model** (Opus/Sonnet/Haiku) og begrund valget.
- **Korte svar** som default, elaborer når bedt om det.

## LLM-model anbefalinger til dette projekt

- **Haiku:** smårettelser i tekster, simple CSV-tjek, formatering.
- **Sonnet:** de fleste kode-ændringer, indikator-tilføjelser, debugging, script-ændringer.
- **Opus:** arkitektur-beslutninger, komplekse dataflows, større refaktorering på tværs af filer, metodediskussioner.

Default til Sonnet hvis i tvivl.

## Hvor finder jeg ting?

- **Ny social indikator:** `shared.ts INDICATORS` + `SOCIAL_CATEGORIES.indicatorIds` + nyt fetch-script + ny CSV i `data/`.
- **Ny øko-dimension:** `shared.ts ECOLOGICAL_DIMENSIONS` + `data.ts ECO_RAW_KEY_MAP` + `build_master_csv.py` + metode-siden.
- **Farver/thresholds:** `shared.ts scoreColor/scoreBarColor` (sociale) og `ScoreBars.tsx ecoScoreColor/ecoBarColor` (økologiske).
- **Tekster:** `app/om/page.tsx`, `app/metode/page.tsx`, `app/layout.tsx` (header/footer).
- **Baseline-logik:** `lib/baseline-context.tsx` + `computeTop10Ratios()` i shared.ts.
- **Vurderingsfunktion:** `components/VurderingBoks.tsx`, `components/VurderingsBjaelke.tsx`, `lib/vurdering.ts`, `client.tsx`.

## Metodedokumentation

- **`data/methodology_note.md`** - CBA 2023-nutidsjustering (Osei-Owusu + ENS GA25). Vigtig for forbrugsbaseret CO2.
- **`data/README.md`** - skema-dokumentation for alle CSV'er i master-pipelinen.
- **`app/metode/page.tsx`** - brugervendt metode per dimension (scoring, grænser, kilder, begrænsninger).
- **`docs/statbank_doughnut_mapping.md`** - mapping mellem DST-tabeller og Doughnut-indikatorer.

## Vedligehold af denne fil

Opdater CLAUDE.md når ny dimension/kategori tilføjes, ratio-konvention ændres, deploy-flow ændres, eller nye kritiske driftsregler opdages. Hold den kort og til mig selv. Intet fluff.
