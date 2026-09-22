# CLAUDE.md - teknisk onboarding

> **Formål:** Hurtigt overblik over projektet "Danmarks 98 Doughnuts" uden at skulle grave i koden. Læses i starten af en ny arbejdssession, af mennesker og af AI-assistenter.
>
> **Se også:** [`README.md`](README.md) for projektets formål og opsætning, og [`docs/arkitektur-og-beregningsregler.md`](docs/arkitektur-og-beregningsregler.md) for de normative beregningsregler. Denne fil er den praktiske driftsvejledning; arkitekturdokumentet er den faglige kontrakt.

## TL;DR (30 sekunder)

- **Projekt:** Doughnut Economics-platform for alle 98 danske kommuner - offentlig platform der viser hver kommunes status i forhold til socialt fundament og økologisk loft.
- **Ejerskab:** Thisted Kommune. Udviklet i klimateamet under EU-projektet LIFE ACT. Licens er ikke afklaret, se README.
- **Stack:** Next.js 16 (`output: "export"`) + Tailwind 4 i `webapp/`, Python-scripts i `scripts/`, CSV-data i `data/`, Netlify-deploy ved push til default-branchen.
- **Omfang:** 13 sociale kategorier, 7 økologiske dimensioner, 66 scorede indikatorer (49 sociale + 17 økologiske sub-indikatorer) og 16 kontekst-indikatorer.
- **Sprog i repoet:** dansk i dokumentation, kommentarer og UI. README er på engelsk af hensyn til eksterne læsere. Undgå em-dash, brug enkelt dash.

## Projektstruktur

```
doughnut/
├── CLAUDE.md
├── netlify.toml             ← base = webapp, publish = out
├── data/
│   ├── indikatorer.json           ← ★ INDIKATORREGISTER: alle indikatorer, kategorier og dimensioner.
│   │                                Læses af både Python-pipelinen og webappen (punkt 32).
│   ├── master_indicators.csv      ← ★ KONSOLIDERET MASTER-FIL (webapp læser KUN herfra)
│   │                                Long format. Genereres af scripts/build_master_csv.py.
│   ├── README.md                  ← skema-dokumentation for master-filen
│   ├── CHANGELOG.md               ← log over data-ændringer
│   ├── methodology_note.md        ← CBA 2023-nutidsjustering
│   ├── klimatilpasning.md         ← metodenote for vejr_skader-indikatoren
│   ├── sundhedsprofil_scores.csv  ← seneste bølge (2025), 8 indikatorer
│   ├── sundhedsprofil_historik.csv← alle fem bølger 2010-2025 (kun de scorede bruges)
│   ├── *_scores.csv               ← rådata-spor (~27 CSV'er). Se data/README.md for fuld liste.
│   └── sundhedsdatabank/
│       └── psyk_tilstande_pr_1000_2025.xlsx  ← Borgere med psykiatriske tilstande pr. 1.000 (Sundhedsdatabank 2025).
│                                               Ikke brugt som aktiv indikator (trækkes ikke automatisk).
│                                               Gemt til evt. fremtidig brug. Alternativ til medicin-indikatoren.
├── scripts/
│   ├── build_master_csv.py        ← ★ konsoliderer alle rådata-CSV'er til master_indicators.csv
│   ├── indikatorregister.py       ← læser og validerer data/indikatorer.json
│   ├── fetch_doughnut_data.py     ← hoved-script: sociale indikatorer + klima-fallback
│   ├── fetch_sundhedsprofil.py    ← Den Nationale Sundhedsprofil (survey, bølger hvert 4. år)
│   ├── fetch_kulturvaner.py       ← DST KV2GEO, kun 76 af 98 kommuner (se punkt 27)
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
    │   ├── BaselineToggle.tsx   ← skift mellem kommunegruppe (standard), landsgennemsnit og top10
    │   ├── VurderingBoks.tsx    ← vurderingsboks pr. kommune
    │   ├── VurderingsBjaelke.tsx
    │   └── VurderingPrintView.tsx
    ├── lib/
    │   ├── shared.ts            ← INDICATORS, SOCIAL_CATEGORIES, ECOLOGICAL_DIMENSIONS (udledt af data/indikatorer.json), typer, compute-funktioner
    │   ├── data.ts              ← loadData(), getKommune(), getAllKommuner()
    │   └── baseline-context.tsx
    └── netlify/functions/
        └── klimaregnskabet.mts  ← proxy for klimaregnskabet.dk API (holder API-nøgle server-side)
```

## Stack og deploy

- **Frontend:** Next.js 16 med `output: "export"` → ren static site i `webapp/out/`. Ingen SSR i prod. Dynamiske routes pre-genereres via `generateStaticParams` for alle 98 kommuner.
- **Netlify:** `base = "webapp"`, `command = "npm run build"`, `publish = "out"`, functions i `webapp/netlify/functions/`.
- **Deploy-flow:** Gem ændringer → preview lokalt → commit + push til default-branchen → Netlify deployer automatisk.
- **Lokal preview:** `cd webapp && npm run dev`, eller dobbeltklik på `Start udviklerserver.command` i projektets rodmappe (macOS). Brug `http://127.0.0.1:3000`, ikke `localhost` - sidstnævnte kan resolve til IPv6 og fejle.
- **Build-output:** `webapp/out/` genereres af `npm run build` og er git-ignoreret. Netlify kører det samme build selv, så outputtet skal ikke committes.

## Datamodel - sådan hænger det sammen

### Grundkoncept

Alle kommuner har et sæt **ratios** hvor `100 = niveau med landsgennemsnit` (sociale) eller `100 = på planetens grænse` (økologiske). For sociale indikatorer er højere bedre, for økologiske er lavere bedre. Inverse indikatorer (Gini, kriminalitet, o.l.) er allerede vendt i dataen.

### Sociale indikatorer og kategorier

Se `data/indikatorer.json` for aktuel liste (felterne er forklaret i filens `_om`). `shared.ts` oversætter registret til `INDICATORS` og `SOCIAL_CATEGORIES` med felterne id, name, table, source (URL), inverse, dataYear, baselineLevel (1=WHO/EU, 2=nationalt mål, 3=landsgennemsnit), absoluteScore, rawUnit. Kategoriscorer beregnes som simpelt gennemsnit via `computeCategoryScores()`. Baseline-toggle (kommunegruppe/avg/top10, standard kommunegruppe) påvirker KUN sociale indikatorer - økologiske har faste referencer (absolutte grænser eller landsgennemsnit) der aldrig omskaleres.

### Farvelogik (konsistent på tværs af UI)

**Sociale:** ≥100 grøn (`emerald`), 85-100 amber, <85 rød (`scoreColor` i shared.ts).
**Økologiske:** ≤85 grøn, 85-100 amber, >100 rød - overshoot (`ecoScoreColor` i ScoreBars.tsx).

### ECOLOGICAL_DIMENSIONS (7 planetære grænser)

Se `oekologiske_dimensioner` i `data/indikatorer.json` for den autoritative liste (`shared.ts` gør den til `ECOLOGICAL_DIMENSIONS`). Aktuel sammensætning:

| Dimension | Sub-indikatorer |
|---|---|
| `klimapaavirkning` | territorial CO₂e, forbrugsbaseret CO₂e |
| `forurening` | nitrat, pesticider, affald, genanvendelse |
| `luftkvalitet` | NO₂, PM2.5 |
| `naeringsstoffer` | N-udledning, P-udledning, tålegrænse for kvælstof pr. ha landbrug (VP3, id `naer_landbrug`), overfladevandets tilstand (VP3) |
| `vand` | vandindvinding |
| `arealanvendelse` | bebygget areal, intensivt dyrket areal |
| `biodiversitet` | bioscore ≥8 mod 30%, bioscore ≥12 mod 10% |

Alle multi-indikator-dimensioner bruger **worst-of** (max ratio): overskrides bare én sub-grænse, er hele dimensionen overskredet. Det er bevidst planetary-boundary-logik, ikke gennemsnit. **Eneste undtagelse er `forurening`, som bruger gennemsnit**, fordi dens fire indikatorer måler vidt forskellige forureningstyper. Kun `vand` er single-indikator.

**Designprincip:** én planetær grænse = én dimension. Flere opgørelsesmetoder for samme grænse er sub-indikatorer, ikke separate dimensioner. Derfor ligger cirkularitet (affald og genanvendelse) under `forurening` og ikke som egen dimension.

### KommuneData-type

```ts
interface KommuneData {
  kommune_kode: string;     // fx "787" (Thisted)
  kommune_navn: string;
  ratios: Record<string, number | null>;       // social indikator-ratios (avg-baseline)
  top10_ratios: Record<string, number | null>; // samme, men top10-baseline
  group_ratios: Record<string, number | null>; // samme, men kommunegruppe-baseline (standardvisning)
  eco_ratios: Record<string, number | null>;   // økologiske dimensions-ratios
  rawValues: Record<string, number | null>;    // faktiske råværdier til UI-visning
  trends: Record<string, TrendPost>;           // retningspile, nøglet på indicator_id og eco rawKey
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
3. **Preview lokalt** → `cd webapp && npm run dev`, eller dobbeltklik `Start udviklerserver.command` (macOS).
4. **Commit + push til default-branchen** → Netlify deployer automatisk.

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
2. Tilføj én post i `data/indikatorer.json` under `indikatorer` (id, category, dimension, name, csv, kolonner, enhed, kilde, retning, evt. `rationale` til metodesiden) og id'et i sin kategoris eller dimensions `indicators`-liste. Felterne er forklaret i filens `_om`; kopiér en eksisterende post af samme type. Python-scripts, `shared.ts` og `data.ts` læser registret, så intet andet sted skal rettes.
3. Opdater kategoriens eller dimensionens beregningstekst i `webapp/app/metode/page.tsx` (antal indikatorer, tabelnavn).
4. Kør fetch-scriptet. Build-trinnet validerer registret og kører `tjek_konsistens.py`, som fanger manglende felter, forkert fortegn og en metodetekst der ikke passer.
5. Commit.

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
3. **Worst-of (med én undtagelse)** - øko-dimensioner med sub-indikatorer bruger max-ratio (worst-of). UNDTAGELSE: Forurening bruger gennemsnit (`"aggregation": "gennemsnit"` i `data/indikatorer.json`), fordi dens 4 indikatorer er vidt forskellige forureningstyper. Logikken bor i `build_master_csv.py`.
4. **Inverse ratio-konvention** - kildedata for forurenings-indikatorer (N, P, affald, pesticider, nitrat, vandindvinding) er `(national_avg / kommune_val) × 100`. Konverteres via `10000/inverse` i `build_master_csv.py`.
5. **cba_2023_estimate.csv** bruger `kommune`-navn som nøgle, ikke `kommune_kode`. Manglende match → `forbrug_co2 = null` (ingen fallback). Christiansø er filtreret fra.
6. **Farvelogik er OMVENDT:** sociale vil op (≥100 = grøn), økologiske vil ned (≤85 = grøn).
7. **`master_indicators.csv`, `trend_indicators.csv` og `data_years.json` skal committes.** Netlify har ingen adgang til kildernes API'er under build, så sitet bygges udelukkende fra de committede CSV'er.
8. **API-nøgler læses KUN fra miljøvariabler. Skriv aldrig en nøgle ind i en fil der ligger i git.** To kilder kræver adgang:
    - `KLIMAREGNSKABET_API_KEY` (bemærk ET) - Klimaregnskabet.dk. Bruges af Netlify-funktionen, `fetch_climate_data.py`, `fetch_trend_history.py` og `probe_api.py`.
    - `UVM_API_TOKEN` - Uddannelsesstatistik. Bruges af `fetch_udvidelse_data.py` og `fetch_trend_history.py`. Det er et JWT bundet til den bruger der oprettede det, med flere års levetid.

    Lokalt: `export` i shell-profilen. I produktion: Netlify → Site configuration → Environment variables. Til webappen lokalt: kopiér `webapp/.env.example` til `webapp/.env` (git-ignoreret).

    Mekanikken bor i `scripts/api_noegler.py`. `hent_noegle()` fejler bevidst ALDRIG ved import, kun `kraev_noegle()` i `main()` afbryder. Årsag: et script der fejler ved import fejler tavst i `tjek_robusthed.py` og andre sammenhænge - se punkt 19.

    **Historik:** begge nøgler stod hårdkodet i `scripts/` indtil aug. 2026 i et offentligt repo. De blev tilbagekaldt hos udbyderne da det blev opdaget, så de værdier der stadig ligger i git-historikken er inerte. Reglen for fremtiden: en nøgle der én gang er pushet, kan ikke fjernes igen. Historik-omskrivning rammer hverken eksisterende kloner eller GitHubs cache, så tilbagekaldelse hos udbyderen er den eneste virkningsfulde reaktion.
9. **Kontekst-indikatorer (vises, scores IKKE)** - data der vises i UI men ikke indgår i nogen score.
    **Regel skærpet sep. 2026: en indikator der KUNNE scores, skal scores eller fjernes. Kontekst er kun til opdelinger af et tal der allerede er scoret.** Sektorfordelingen af CO2 er en opdeling af det territoriale tal; `ctx_fossil_direkte`/`ctx_fossil_via_fjv` er de to halvdele af `bolig_fossil`. De bliver stående, fordi der ikke findes et meningsfuldt mål at score dem imod. `medicin` var derimod en scorbar indikator vi var i tvivl om fortegnet på - den blev fjernet helt, ikke parkeret som kontekst. Resterende kandidater der stadig skal afgøres: `ctx_ve_*`, `ctx_energiforbrug`, `ctx_fritid_*`. Defineres i `data/indikatorer.json` med `"category": "context"`, skrives til master med `category="context"`, rutes i `data.ts` til `kommune.rawValues[indicator_id]`, og renderes af en dedikeret komponent (fx `EnergiKontekst`, `KlimaKontekst` i `ScoreBars.tsx`). Bruges til:
    - **Energi:** lokal VE-kapacitet (`ctx_ve_*`, EDS CapacityPerMunicipality) og fjernvarmens brændselsmix (`ctx_fjv_*`, Energistyrelsen EPT `ens.dk/media/7199/download`). Begrundelse: VE er national net-produktion; fjernvarme er overvejende afbrænding - se metode-siden.
    - **Klimapåvirkning:** sektorfordeling af territorial udledning (`ctx_klima_landbrug/energi/transport`), samlet energiforbrug (`ctx_energiforbrug`) og VE-el selvforsyningsgrad (`ctx_ve_selvforsyning`) - alle fra Klimaregnskabet.dk, samme API-kald som `klimapaavirkning` selv genbruges til (ingen ekstra kald, se `fetch_climate_data.py`). Begrundelse: sektorerne er en opdeling af det allerede scorede territoriale tal, ikke et nyt måltal. **Fælde:** `ve_selvforsyning` leveres som forhold (1.71), ikke procent - ganges med 100 i `_extract_kontekst()`.
    - **Fritidsboliger** (`ctx_fritid_fossil`, `ctx_fritid_andel`, fra `fetch_bolig_fossil.py`). Begrundelse: se punkt 10.
10. **Energi-dimensionen (social)** - scores KUN på `bolig_fossil`, som er kommunens SAMLEDE fossile varmeafhængighed = direkte olie/gas% + (fjernvarme-dækning% × fjernvarmens fossile andel). Scoret mod ABSOLUT mål 0% (ikke landsgennemsnit): `ratio = 100 − samlet_fossil%`, beregnet i `fetch_bolig_fossil.py`. Konsekvens: ingen kommune når grønt (fossilfri varme findes ikke endnu). VE + fjernvarme-mix + fritidsboliger er kontekst (punkt 9). Fetch-scripts: `fetch_ve_kapacitet.py`, `fetch_fjernvarme_mix.py`. **Kørselsrækkefølge:** `fetch_fjernvarme_mix.py` FØR `fetch_bolig_fossil.py` (sidstnævnte læser fjernvarmens fossil-andel fra førstnævntes CSV; bruger TJ-vægtet landssnit for de 18 fælles-net-kommuner).
    - **Grundlag er DST BYGB40, opvarmet AREAL i m² - ikke BOL202/personer** (skiftet aug. 2026, se `data/CHANGELOG.md`). Varmebehov skalerer med areal, ikke med hoveder.
    - **To afgrænsninger man SKAL huske ved ændringer i scriptet:** (1) BYGB40 dækker som udgangspunkt ALLE bygninger - fabrikker, avlsbygninger, garager, udhuse. Scoren afgrænses derfor eksplicit til `ANVEND_HELAARSBOLIG` (110-190). Udelader man ANVEND, måler indikatoren pludselig kommunens samlede bygningsmasse. (2) Fritidsboliger holdes UDE af scoren og vises kun som kontekst: sommerhuse er typisk elopvarmede (median ~7% fossil mod helårsboligernes ~20%), så medregning ville give sommerhuskommuner en kunstigt bedre social score - samme fejltype som den fjernede `car_access`.
11. **`absolute_score`-flag** (i `data/indikatorer.json`, bliver til `absoluteScore` i `INDICATORS`) - markerer en social indikator hvis ratio er en absolut score (fx `100 − fossil%` eller `andel/mål × 100`), ikke relativ til landsgennemsnit. Sådanne indikatorer omskaleres IKKE af baseline-toggle (avg/top10/gruppe) - `computeTop10Ratios`/`computeGroupRatios` springer dem over og beholder værdien. Pt. `bolig_fossil` og `education`. For direkte sociale indikatorer med absolut mål: sæt `abs_target` (build_master beregner `raw/mål × 100`, capped 150) og `absolute_score: true` på indikatorens post i registret.
12. **baselineType (absolut vs relativ)** - hver dimension klassificeres: absolut (scoret mod fast mål - WHO, EU, 0% fossil, 95% uddannelse) eller relativ (mod landsgennemsnit); ens type i alle sub-indikatorer → den type, ellers "blandet" (pt. kun Uddannelse + Forurening). Udledes i `shared.ts` (`indicatorBaselineType`/`categoryBaselineType`/`dimensionBaselineType`); øko-sub-indikatorer har felt `baselineType`, sociale udleder fra `absoluteScore`. ScoreBars viser mærke "mod mål"/"blandet" på dimensions-bjælken (relativ = intet mærke, forklaret i ringens legende). Regel: scor mod mål hvor en meningsfuld per-kommune-grænse findes, ellers landsgennemsnit.
13. **Retningsvisning (trends) - to filer skal følges ad.** `data/trend_indicators.csv` (retningspile) er et selvstændigt spor ved siden af `master_indicators.csv`, med sin egen pipeline: `fetch_trend_history.py` → `build_trends_csv.py` (kaldes automatisk via `auto_build_trends()`, ligesom `auto_build_master()`). **Begge filer skal committes, og de skal genberegnes sammen** - ellers viser platformen en pil der peger på et tal, den ikke længere hører til. Retningen beregnes ALTID på råværdier, aldrig på ratio: ratio afhænger af baseline-toggle (avg/top10/gruppe), så en ratio-baseret pil ville skifte retning når brugeren skifter baseline.
14. **Dimensionspilens regel (worst-of, ikke gennemsnit).** En øko-dimensions pil er retningen for den sub-indikator der bestemmer dimensionens score - altså den med højeste ratio. Tager man gennemsnittet af sub-retningerne, kan dimensionen vise grøn pil samtidig med at netop den overskredne grænse bliver værre. Undtagelse: Forurening bruger gennemsnit i scoren og derfor også i retningen (`AVERAGE_DIMENSIONS` findes BÅDE i `build_master_csv.py` og `build_trends_csv.py` - hold dem i sync). Sociale kategorier er simpelt gennemsnit begge steder. **Har den afgørende sub-indikator ingen tidsserie, får dimensionen INGEN pil** - der falles bevidst ikke tilbage på de øvrige. Derfor har fx `klimapaavirkning` kun pil i 11 af 98 kommuner (i de øvrige 87 afgøres scoren af forbrugsbaseret CO₂, som ikke findes som tidsserie). Det er korrekt opførsel, ikke manglende data.
15. **Pilens retning udledes af registret (fra sep. 2026).** `build_trends_csv.py` bruger `indikatorregister.op_er_godt()`, som er `not inverse` for sociale og `not lower_is_better` for økologiske indikatorer. Den tidligere håndskrevne `OP_ER_GODT`-konstant skulle holdes i sync med `shared.ts` og er væk. Et id i tidsserien som registret ikke kender, klassificeres som "kontekst" (pil uden vurdering); `tjek_konsistens.py` melder det som fejl.
16. **Pilens retning betyder to forskellige ting, og `pct` gør det samme.** Reglen bor i `trendPilOpad()` i `shared.ts`, som ALLE visninger skal bruge - lav aldrig `pct >= 0` direkte i en komponent.
    - **Enkelt-indikator:** pilen følger råværdiens FAKTISKE ændring, og `pct` i CSV'en er den rå ændring. Det giver det nuancerede billede: inden for Forurening peger genanvendelse op i grønt og affald op i rødt - samme retning, modsat vurdering.
    - **Dimension/kategori (`_dim_*`):** pilen følger doughnut-geometrien - sociale kategorier skal fyldes OP mod fundamentet, økologiske skal ned UNDER loftet. Så fremgang = pil op på social, pil ned på øko. `pct` er her MÅLRETTET (fortegn vendt for inverse indikatorer, positiv = fremgang), og `vaerdi_start`/`vaerdi_slut` er tomme, fordi der ikke er nogen fælles enhed.
    - **Fælden der allerede er ramt én gang:** worst-of-dimensioner kopierede oprindeligt sub-indikatorens rå `pct`, mens gennemsnits-dimensioner brugte den målrettede. Resultatet var at Forurening og Vand begge stod som "positiv retning", men med pile der pegede modsat. Hvis du ændrer i `aggreger_dimensioner()`, så sørg for at BEGGE grene målretter `pct`.
17. **11 indikatorer fik pil aug. 2026** (hospital_long, housing_no_wc/no_bath, voter_turnout, kultur_spending, civil_society, low_income, exam_grade, high_absence, wellbeing, youth_education) - se `fetch_trend_history.py`. **13 af de 66 scorede mangler stadig** og har det bevidst (sep. 2026): ingen tidsserie hos kilden (bolig_fossil, vejr_skader, forbrug_co2, luftkvalitet_no2/pm25, bio_*, naer_landbrug, overfladevand, nitrat, pesticider), kun kommunegruppe-niveau (public_transport), eller begge år indgår i målet (sport_tilskuer). **apprenticeship (EUD/PRAK/SØG) er i stykker hos UVM** - selv et enkelt-års opslag fejler nu ("Nøgletal ... kunne ikke findes"), formentlig omdøbt siden scriptet blev skrevet; gælder hele indikatoren, ikke kun historik. `voter_turnout`s kilde stod forkert som KVBPCT i `build_master_csv.py` (den tabel har slet ingen kommune-opdeling) - den rigtige er LABY08, som `fetch_democracy_data.py` allerede brugte korrekt.
18. **Master kan indeholde indikatorer platformen ikke scorer.** `housing_no_wc`/`housing_no_bath` står i master med `dimension=bolig`, men står IKKE i Bolig-kategoriens `indicators` i `data/indikatorer.json` - Bolig scorer og viser kun 2 indikatorer. Så længe de to manglede tidsserie, ramte Bolig-pilen rigtigt ved et TILFÆLDE (de blev sprunget over). Da de fik pil aug. 2026, begyndte pilen at gennemsnitte 4 indikatorer ved siden af et tal beregnet på 2 - og de to usynlige dominerede (`housing_no_bath` er faldet ~39% på landsplan). Derfor holdes de ude af aggregeringen via `indikatorregister.ikke_scoret()` (sociale indikatorer der ikke står i nogen kategori), men beholder deres egen indikator-række. **Regel: tilføjer du tidsserie til en indikator, så tjek at den faktisk står i sin kategoris `indicators`** - ellers holdes den ude af pilen uden at være synlig noget sted. Kontrol: kategoriens tooltip ("gennemsnit af N indikatorer") skal matche "N/N indikatorer" på bjælken, MEDMINDRE forskellen skyldes manglende tidsserie på en indikator der faktisk scores (fx Fællesskab 4 af 5, hvor `sport_tilskuer` ingen pil har - det er korrekt).

19. **Datapipelinens robusthed - kør `python3 scripts/tjek_robusthed.py` før en dataopdatering.** Ren diagnose, skriver ingen filer. Den tjekker fem fejlklasser vi alle er faldet i (aug. 2026), og som har samme signatur: platformen ser levende ud, men tallet er frosset, og INTET fejler højlydt.
    - **Scripts der ikke kan køre.** Fem brugte `float | None` uden `from __future__ import annotations` og fejlede ved import på maskinens Python 3.9. Derfor stod `voter_turnout` på kommunalvalget 2021 fire år efter valget.
    - **Omdøbte variabler.** LABY49's `OFFENTRANSPORT` hedder nu `SDGSERVICE`. DST svarede 400, og scriptet faldt TAVST tilbage på hårdkodede tal.
    - **Døde tabeller.** DST markerer tabeller inaktive uden at fjerne dem. HFUDD10 stoppede i 2019 (`education` viste 2019-tal mærket 2023), BIB1 er afløst af BIB3A. Tjek `active`-flaget - der findes næsten altid en afløser, og den har typisk samme tal tilbageberegnet.
    - **Hårdkodede årstal.** Den enkeltårsag der holdt flest indikatorer forældede. Brug `scripts/dst_aar.py`: `seneste_aar()`, `seneste_periode()` (5-års-intervaller som HISBK "2021:2025"), `seneste_kvartal()` (FOLK1A SKAL blive på K1, ellers skifter opgørelsesdatoen umærkeligt) og `hele_aar_kvartaler()` (STRAF11 kræver fire hele kvartaler).
    - **Årstal og data hvert sit sted.** `data_year` var hårdkodet i `build_master_csv.py` uafhængigt af hentningen, så masteren kunne mærke 2024-tal som 2022. Fetch-scripterne kvitterer nu i `data/data_years.json` via `dst_aar`, og build_master læser derfra. **`data_years.json` skal committes.**
20. **Manuelle kilder - hvad Miljøportal kan og ikke kan (undersøgt aug. 2026).** `bio_*`: datapakken har stabil URL og hentes nu automatisk, men bioscore udstilles kun som WMS (billedtjeneste), så der kan ikke trækkes værdier ud - ingen tidsserie mulig, pakken er uændret siden 2022. `nitrat`/`pesticider`: GEUS Jupiter WFS (`data.geus.dk/geusmap/ows/25832.jsp`) har analyser pr. vandværk med kommune, stof, værdi og prøvedato - nitrat er `stofnr_num=246`, og filtrering til `virktyp_over=VV` (vandværker) rammer nogenlunde Greenpeaces niveau. **Men det er et ANDET tal end det platformen viser**, fordi Greenpeace vægter efter vandindvinding og kobler til forsyningsområder. En omlægning ville være en ny indikatordefinition, ikke en opdatering. **Fælde: Jupiter-WFS'en ignorerer `CQL_FILTER` TAVST** og returnerer ufiltrerede data - brug OGC XML-`filter`. `vejr_skader` og `forbrug_co2` findes ikke på Miljøportal (forsikringsdata hhv. modelestimat).

21. **Nitrat og pesticider kommer nu fra GEUS Jupiter (aug. 2026), ikke fra PDF-udtræk.** `scripts/fetch_grundvand_jupiter.py` afløser `fetch_nitrat_data.py` og `fetch_pesticider_data.py`, som begge indeholdt hårdkodede tal. **Den gamle nitrat-kilde gav 80 af 98 kommuner den IDENTISKE pladsholderværdi 3,7 mg/L** - kun Greenpeaces top-20 havde rigtige tal. Derfor skiftede 36 kommuner farve på Forurening ved omlægningen; det er korrektioner, ikke støj. Fire ting man skal kende:
    - **Afgræns til `virktyp_over=VV`** (almene vandværker = behandlet drikkevand). Uden filteret blandes råvand fra enkeltboringer og erhvervsanlæg ind, og niveauet bliver markant højere end det borgerne drikker (Aalborg 32 mod 19 mg/L).
    - **Aktualitetsvindue på 10 år.** Jupiter gemmer SENESTE analyse pr. værk, men for sjældent prøvetagne værker kan den være 20 år gammel - 25% var ældre end 2020, og én analyse er dateret 2031.
    - **Vandværker uden registreret årsindvinding skal have MEDIANVÆGT, ikke vægten nul.** Manglende mængdedata er systematisk skævt: de 33% uden mængde har median 2,2 mg/L mod 1,5 for dem med. Med vægten nul forsvandt netop de mest belastede værker, og Thisted faldt kunstigt til 4,4 mg/L.
    - **Tallet er beslægtet med Greenpeaces, ikke identisk.** Vi vægter efter tilladt indvindingsmængde; Greenpeace/Schullehner kobler til faktiske forsyningsområder. Aalborg rammer næsten præcist (20,5 mod 20,7), men Thisted lander på 5,2 mod 13,9 - forskellen er metodisk, ikke en fejl. Pesticider skifter samtidig tælleenhed fra boringer til vandværker.
    - **Fælde: Jupiter-WFS'en ignorerer `CQL_FILTER` TAVST** og returnerer alle stoffer. Brug OGC XML-`filter`, og verificér at det udtrukne stof er det forventede (scriptet gør det selv og afbryder ellers).

22. **Sundhed er kategorien med seks af ni indikatorer fra én kilde.** Selvvurderet helbred, dårligt mentalt helbred, rygning, alkohol, kostskala og svær overvægt kommer alle fra Sundhedsprofilen, samme bølge, samme spørgeskema. Middellevetid, sygehusophold 12+ timer og hjemmesygepleje er de tre registerbaserede. Konsekvensen er at en ændret definition eller en udeblevet bølge hos SIF slår igennem på to tredjedele af kategorien på én gang, og at middellevetid kun vejer en niendedel. Levevaner lå kortvarigt som sin egen kategori, men er lagt ind under Sundhed efter beslutning sep. 2026.

23. **Sundhedsprofilen er survey, ikke register - fire ting man skal kende.** `scripts/fetch_sundhedsprofil.py` henter otte indikatorer fra internetdatabasen på danskernessundhed.dk (Sundhedsstyrelsen + SIF/SDU). Kilden opfører sig anderledes end DST på fire punkter:
    - **Bølger hvert 4. år** (2010, 2013, 2017, 2021, 2025). Kommunetallene står fast mellem bølger. Det er IKKE den frosne-tal-fejl fra punkt 19: `data_year` er korrekt sat til 2025, og metodesiden siger det. Men et fetch-kald giver samme tal år efter år, så brug ikke "tallet ændrer sig ikke" som tegn på at scriptet er i stykker.
    - **To API-fælder.** `/SASVisualAnalyticsTransport/onebi/services/*` svarer **401** indtil man har vekslet gæste-CAS-cookien (CASTGC) til en service ticket via `/SASLogon/rest/v1/tickets/<TGT>` og indløst den. Og `getData` svarer **400** hvis `reportDate` mangler - brug requery-URL'en fra `generateReport` som den kommer, frem for at bygge URL'en selv.
    - **Landsgennemsnittet beregnes af os**, som befolkningsvægtet gennemsnit af de 98 kommuneandele (DST FOLK1A, 16+). Databasen udstiller ikke et landstal pr. kommunetabel. Tallet afviger derfor en anelse fra SIF's eget vægtede landsestimat, og det skal stå i enhver formidling.
    - **DataDefinition-id'et varierer pr. rapport.** Hardkod det aldrig. Scriptet finder rapportens faneblad "Kommune", følger dets `<Visual ref>` til krydstabellen og læser `data="ddNNNN"` derfra, med validering på indholdet som fallback.

24. **Pil-vinduet for Sundhedsprofilen er 2017 → 2025, ikke hele serien.** `build_trends_csv.py` bruger første og sidste punkt når serien er kortere end 6 år. En fuld 2010-2025-serie ville derfor give en pil der beskriver 15 års udvikling og ikke er sammenlignelig med de øvrige indikatorers vinduer. 2021 er fravalgt som basis hvor 2017 findes, fordi dataindsamlingen det år lå under coronarestriktioner - især mental sundhed og alkohol var atypiske. `ensomhed` har nødvendigvis 2021 som basis. Styres af `TREND_BASIS_PRIORITET` i fetch-scriptet.

25. **`fysisk_aktivitet` hentes, men scores ikke - og det er ikke en kontekst-indikator.** Den korrelerer 0,90 med svær overvægt og 0,80 med kostskalaen. Med alle tre ville én underliggende konstruktion fylde tre af Sundheds ni pladser. Tallet står i `sundhedsprofil_scores.csv` og er markeret `kun_data=True` i INDIKATORER, så det hverken når master eller trend-historikken. Skal prioriteringen laves om, er det ét flag.

26. **`traffic_accidents` er et treårigt gennemsnit (fra sep. 2026).** UHELDK1 summeres over de tre nyeste år og divideres med tre. Baggrund: ét års tal er ren støj i små kommuner - Læsøs gamle score på 35 hvilede på omkring to tilskadekomne. Samme greb som `vejr_skader` (2023-2025). Ændrer man det tilbage til ét år, genindfører man støjen.

27. **`sport_tilskuer` dækker kun 76 af 98 kommuner, og hullet er systematisk.** DST's kulturvaneundersøgelse (KV2GEO) undertrykker tal hvor stikprøven er for lille. De 22 kommuner uden tal har median ca. 24.000 indbyggere mod ca. 53.000 for dem med tal, og Læsø, Fanø, Samsø, Ærø og Langeland er blandt dem. De får Fællesskab beregnet på fire indikatorer hvor de øvrige bruger fem. Det er en bevidst afvejning, ikke en fejl, men den skal stå på metodesiden hver gang kategorien ændres. Indikatoren får ingen retningspil, fordi tabellen kun har 2024 og 2025 og begge år indgår i det toårige gennemsnit.
    - **Fælde: KV2GEO's regionskoder er trecifrede** (081-085). Et filter på "tre cifre og ikke 000" tager regionerne med som var de kommuner og overvurderer dækningen med fem. `fetch_kulturvaner.py` slår op i master-CSV'ens kommuneliste i stedet. Samme fælde kan findes i andre DST-tabeller der blander kommuner, landsdele og regioner i én områdedimension.
    - **Fælde ved kørsel:** pipe aldrig et fetch-script gennem `head`. Scriptet dør på BrokenPipeError midt i `auto_build_master()`, og master-CSV'en står tilbage halvgammel uden at noget fejler synligt.

28. **Fællesskab måler nu udfald, ikke budget.** Ensomhed og begrænset social støtte er udfaldsmål, idrætsmedlemskab og tilskuerdeltagelse er deltagelse, og `civil_society` er det eneste tilbageværende input. Den beholdes bevidst, selvom den korrelerer svagt med resten: den er det eneste sted i modellen hvor kommunens egen indsats på foreningsområdet er synlig. `sports_facilities` og `sports_spending` er begge fjernet, fordi de korrelerede negativt med de øvrige og dermed udlignede kategoriens gennemsnit i stedet for at måle noget.

29. **Indkomst er median, beregnet af os (fra sep. 2026).** `disposable_income` og `income_gender_gap` bruger median disponibel indkomst fra INDKP106's indkomstintervaller (`scripts/indkomst_median.py`), fordi DST ikke udgiver medianen pr. kommune og køn, og gennemsnittet (INDKP101) blev flyttet af få ekstreme indkomster (Vejen). Hjælperen bruges både af `fetch_doughnut_data.py`, `fetch_ligestilling_data.py` og `fetch_trend_history.py` - skift aldrig kun ét af stederne tilbage, ellers peger pilen på et andet tal end scoren. Intervaltekster læses fra DST; ændrer DST inddelingen, fejler hjælperen i stedet for at gætte.

30. **Kør `python3 scripts/tjek_konsistens.py` før du committer en ændring i registret eller metodesiden.** Ren diagnose, samme princip som `tjek_robusthed.py` (punkt 19), men for konfigurationen i stedet for datapipelinen. Efter registret (punkt 32) er der ikke længere parallelle lister at holde i sync, så tjekket dækker det der stadig kan skride: registrets gyldighed, at master indeholder præcis registrets indikatorer, at fortegnet i dataen passer med `inverse`/`lower_is_better` (faktisk korrelation i master), at tidsseriens id'er kendes, og at metodesidens fritekst (antal indikatorer, tabelnavne, worst-of/gennemsnit) passer med registret. **Køres automatisk:** `auto_build_master()` printer altid resultatet efter en fetch (rejser aldrig, ligesom resten af den funktion), men `python3 scripts/build_master_csv.py` kørt direkte afbryder med exit 1 hvis der er fejl - det er her det skal stoppes, før commit. Metodesiden parses med regex, ikke en rigtig parser - se scriptets docstring.

31. **Dataår i UI'et beregnes fra master-CSV'en, ikke fra hårdkodede felter (fra sep. 2026).** Footeren (`DOUGHNUT_EDITION_YEAR`/`DOUGHNUT_DEFAULT_DATA_YEAR`), metode-sidens "Datatidspunkt" pr. kategori/dimension og kommunesidens "Data: åååå" pr. indikator kom tidligere fra tre uafhængigt vedligeholdte steder (shared.ts, metode/page.tsx, layout.tsx) og drev fra master-CSV'en og fra hinanden hver gang en indikator blev opdateret (sep. 2026: ca. 25 forkerte dataYear-felter + en footer der stod et helt år forkert). `webapp/lib/data.ts` beregner dem nu direkte fra `master_indicators.csv`'s `data_year`-kolonne: `getDimensionDataYears()` grupperer på `dimension`-feltet (samme id som SOCIAL_CATEGORIES/ECOLOGICAL_DIMENSIONS), `getIndicatorDataYears()` giver ét år pr. social indikator, og `getDoughnutEdition()` udleder footer-årstallene som *mode* (det hyppigste år blandt de sociale indikatorer), ikke max - ellers ville et enkelt fremadrettet registreringsår (fx `bolig_fossil` på BYGB40, mærket 2026) trække editionen et år frem uden grund. `INDICATORS[].dataYear` (registrets `data_year`) er kun et fallback-felt i `ScoreBars.tsx` (bruges hvis en indikator mangler helt i master), og `MethodInfo.dataYear` er fjernet fra metode-siden. **Regel: ret aldrig et forkert dataår ved at rette et hårdkodet felt - roden er altid `data/data_years.json` eller `data_year`-værdien i det pågældende fetch-script.**

32. **Indikatorregistret `data/indikatorer.json` er den ene liste over indikatorer (fra sep. 2026).** Før stod samme oplysning op til seks steder (`build_master_csv.py`s tre lister og `AVERAGE_DIMENSIONS`, `build_trends_csv.py`s `OP_ER_GODT`/`IKKE_SCORET`/`AVERAGE_DIMENSIONS`, `shared.ts`s `INDICATORS`/`SOCIAL_CATEGORIES`/`ECOLOGICAL_DIMENSIONS`, `data.ts`s `ECO_RAW_KEY_MAP` og metodesidens `INDICATOR_RATIONALES`/`csvFile`) og blev holdt i sync i hånden - den enkeltårsag der stod bag flest fejl i gennemgangene. Nu læser Python registret via `scripts/indikatorregister.py` (valideres ved første brug, rejser `RegisterFejl` med alle fejl på én gang), og `shared.ts` importerer JSON-filen direkte. Tre ting at vide: (1) **Rækkefølgen af `indikatorer` er rækkefølgen i master-CSV'en**; visningsrækkefølgen styres af kategoriens/dimensionens `indicators`-liste. Flyt ikke rundt på indikatorer uden grund - det ændrer master byte for byte, selvom tallene er de samme. (2) **Registret læses lazy**, ikke ved import: en fejl i JSON'en må ikke vælte et fetch-script der importerer `auto_build_master` (samme princip som punkt 8). (3) **`webapp/next.config.ts` sætter `turbopack.root` til repoets rod**, fordi `shared.ts` importerer en fil uden for `webapp/`. Sættes roden tilbage til `webapp/`, fejler buildet med "Module not found".

## Arbejdsprincipper for ændringer

- **"Brilliant basics" frem for innovation.** 80/20-mindset. Platformen er bevidst enkel, og enkelheden er en kvalitet, ikke en mangel.
- **Lav en plan før større ændringer**, særligt når de rører beregningsreglerne. Se `docs/arkitektur-og-beregningsregler.md`.
- **Ændrer du en beregning, ændrer du tal der er offentligt fremme.** Verificér mod master-CSV'en før commit, og noter ændringen i `data/CHANGELOG.md`.
- **Dokumentation og kode skal følges ad.** Afviger de, så skriv afvigelsen ned i arkitekturdokumentets afsnit 7 frem for at lade den ligge uregistreret.

## Hvor finder jeg ting?

- **Ny indikator (social, økologisk eller kontekst):** én post i `data/indikatorer.json` + nyt fetch-script + ny CSV i `data/` + metodesidens beregningstekst. Se "Tilføj en ny indikator".
- **Ny øko-dimension:** `oekologiske_dimensioner` i `data/indikatorer.json` + metode-siden (`ECO_METHODS`). UI-komponenterne der tegner dimensionen (fx `DoughnutRing`) skal tjekkes, fordi ringens geometri afhænger af antallet.
- **Farver/thresholds:** `shared.ts scoreColor/scoreBarColor` (sociale) og `ScoreBars.tsx ecoScoreColor/ecoBarColor` (økologiske).
- **Tekster:** `app/om/page.tsx`, `app/metode/page.tsx`, `app/layout.tsx` (header/footer).
- **Baseline-logik:** `lib/baseline-context.tsx` + `computeTop10Ratios()` i shared.ts.
- **Vurderingsfunktion:** `components/VurderingBoks.tsx`, `components/VurderingsBjaelke.tsx`, `lib/vurdering.ts`, `client.tsx`.

## Metodedokumentation

- **`data/methodology_note.md`** - CBA 2023-nutidsjustering (Osei-Owusu + ENS GA25). Vigtig for forbrugsbaseret CO2.
- **`data/README.md`** - skema-dokumentation for alle CSV'er i master-pipelinen.
- **`app/metode/page.tsx`** - brugervendt metode per dimension (scoring, grænser, kilder, begrænsninger).
- **`docs/statbank_doughnut_mapping.md`** - mapping mellem DST-tabeller og Doughnut-indikatorer.
- **`docs/concito-analyse-og-roadmap.md`** - hvad vi kan/ikke kan bruge fra CONCITO-rapporten + bevidste fravalg. Læs før øko-ændringer.
- **`docs/aabne-traade-juni-2026.md`** - prioriterede løse ender og uudnyttede indsigter (scoringsfilosofi, education-badge, REshare, energiforbrug m.m.). Læs før næste større runde.
- **`docs/arkitektur-og-beregningsregler.md`** - de normative beregningsregler (R1-R15), retningspilenes regler (T1-T8), kendte fælder og registrerede afvigelser mellem dokumentation og kode. Læs før enhver ændring i scoringen.

## Vedligehold af denne fil

Opdater CLAUDE.md når en ny dimension eller kategori tilføjes, når ratio-konventionen ændres, når deploy-flowet ændres, eller når en ny kritisk driftsregel opdages. Hold den kort og konkret, uden fluff.

Arbejdsdeling mellem de tre dokumenter:

- **README.md** - hvad projektet er, og hvordan man kommer i gang. Til nye læsere.
- **CLAUDE.md** - praktisk drift: filoversigt, pipeline, faldgruber ved dataopdatering.
- **docs/arkitektur-og-beregningsregler.md** - den faglige kontrakt. Reglerne der skal reproduceres præcist ved en port eller videreudvikling.
