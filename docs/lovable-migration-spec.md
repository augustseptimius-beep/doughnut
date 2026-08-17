# Migrationsspecifikation: Danmarks 98 Doughnuts til Lovable + Supabase

**Status:** Godkendt plan. Implementering IKKE påbegyndt.
**Godkendt af:** August, 2026-08-06.
**Målgruppe:** AI-agenter (Claude, Lovables agent) der skal implementere migreringen. Dokumentet er normativt: afvigelser fra dette dokument kræver eksplicit godkendelse fra August. Afsnit markeret [info] er baggrund, ikke krav.

---

## 0. Beslutningslog (låste beslutninger)

Disse beslutninger er truffet og skal IKKE genforhandles af implementerende agenter:

| # | Beslutning | Begrundelse |
|---|---|---|
| B1 | Platformen genopbygges i Lovable (Vite + React + shadcn/ui), ikke Next.js | Lovable understøtter ikke Next.js. SPA med React Router erstatter static export |
| B2 | Supabase er backend: Postgres + Auth + Edge Functions | Muliggør admin-UI, import, bruger-features |
| B3 | AL indikator- og dimensions-metadata flyttes til databasen fra dag 1 | Fjerner tre-steders-problemet (shared.ts + build_master_csv.py + metode-side) som har givet utakt |
| B4 | Metode-sidens prosa gemmes i databasen (markdown-felter), redigerbar i admin-UI | Godkendt af August inkl. trade-off: prosa versionsstyres ikke længere i git |
| B5 | Øko-dimensionsscorer (worst-of/gennemsnit) beregnes ved indlæsning i frontend, IKKE gemt i databasen | Fjerner risiko for forældede aggregater efter admin-redigering. Logikken er triviel (max/gennemsnit) |
| B6 | Kun nuværende værdier gemmes pr. (kommune, indikator). Historik over år er IKKE i scope | Matcher nuværende funktionalitet. Historik er en fremtidig mulighed, ikke MVP |
| B7 | Statbank/EDS/UVM-fetchere porteres til Supabase Edge Functions. Geodata- og manuelle kilder opdateres via admin-import | Se disposition i afsnit 11 |
| B8 | Edge functions udløses manuelt via "Opdater nu"-knapper i admin. Cron-planlægning er IKKE i scope for fase 6 | Holder scope stramt; data opdateres alligevel sjældent |
| B9 | Python-scripts i `scripts/` bevares urørt i repoet under hele migreringen | Reference og fallback indtil nyt system er verificeret |
| B10 | Gammelt Netlify-site kører parallelt indtil paritet er verificeret og August godkender go-live | Ingen nedetid, mulighed for rollback |

---

## 1. Mål og ikke-mål

### Mål
1. Funktionel paritet: det nye site viser samme tal, farver, scorer og tekster som det nuværende for alle 98 kommuner.
2. Admin-UI hvor August (uden kode/terminal) kan: redigere værdier, redigere indikator-metadata og metode-prosa, importere CSV/Excel, og udløse datahentning.
3. Metadata har ét hjem (databasen). Metode-siden genereres derfra og KAN ikke komme i utakt med data.
4. Fundament for senere bruger-features (konti, feedback, gemte sammenligninger).

### Ikke-mål (må IKKE implementeres uden ny godkendelse)
- Historiske tidsserier pr. indikator (B6).
- Cron-planlagt datahentning (B8).
- Ændringer i scoringsmetode, grænseværdier, farvetærskler eller indikatorlisten. Migreringen er 1:1 på al faglig logik.
- SSR/prerendering af kommunesider (accepteret trade-off, se afsnit 14).
- Bruger-features (fase 7) er IKKE en del af fase 1-6 og specificeres separat senere.

---

## 2. Målarkitektur

```
Lovable-projekt (Vite + React + TypeScript + Tailwind + shadcn/ui)
├── Offentligt site (ingen login)
│   ├── /                      Forside med kommunesøgning
│   ├── /kommune/:navn         Kommuneside (donut, scorebars, vurdering)
│   ├── /metode                GENERERET fra databasen (afsnit 9)
│   ├── /om                    Statisk tekst
│   └── /artikel/planetaere-graenser   Statisk tekst
├── Admin (bag Supabase Auth login)
│   ├── /admin                 Oversigt + "Opdater nu"-knapper (fase 6)
│   ├── /admin/vaerdier        Rediger indicator_values
│   ├── /admin/indikatorer     Rediger indicators + dimensions inkl. metode-prosa
│   ├── /admin/import          Import-funktionen (afsnit 10)
│   └── /admin/log             import_log-visning
└── Supabase
    ├── Postgres (skema i afsnit 3)
    ├── Auth (kun August har skriveadgang)
    └── Edge Functions (fase 6, afsnit 11)
```

Dataflow ved sidevisning: appen henter ved opstart (1) alle rækker fra `kommuner`, `dimensions`, `indicators` og (2) alle rækker fra `indicator_values`. Derfra bygges `KommuneData[]` i browseren efter kontrakten i afsnit 6. Ca. 6.000 værdirækker; sammenligneligt med nuværende 676 KB CSV. Ingen paginering nødvendig.

---

## 3. Databaseskema (normativt)

Kolonnenavne og typer er normative. Postgres/Supabase.

```sql
create table kommuner (
  kode           text primary key,          -- "101".."860", tre cifre som tekst
  navn           text not null unique,      -- "Thisted", "København"
  kommunegruppe  int  not null check (kommunegruppe between 1 and 5)
  -- Seedes fra KOMMUNEGRUPPE i webapp/lib/shared.ts (DST KOMMUNEGRUPPER_V1_2018)
);

create table dimensions (
  id            text primary key,           -- "sundhed", "klimapaavirkning", ...
  navn          text not null,              -- "Sundhed", "Klimapåvirkning"
  kind          text not null check (kind in ('social','ecological')),
  short_name    text,                       -- kun eco: label i SVG-ringen ("KLIMA")
  description   text,                       -- fra SOCIAL_CATEGORIES.description / ECOLOGICAL_DIMENSIONS.description
  boundary_text text,                       -- kun eco: ECOLOGICAL_DIMENSIONS.boundary
  unit          text,                       -- kun eco
  source_label  text,                       -- kun eco
  source_url    text,                       -- kun eco
  aggregation   text not null default 'worst_of'
                check (aggregation in ('worst_of','average')),
                -- eco: 'worst_of' for alle UNDTAGEN forurening='average'.
                -- social: feltet ignoreres (kategoriscore er altid gennemsnit)
  sort_order    int not null,
  metode_tekst  text,                       -- markdown, redigerbar i admin
  begraensninger text                       -- markdown, redigerbar i admin
);

create table indicators (
  id             text primary key,          -- "life_expectancy", "luftkvalitet_no2", "ctx_ve_sol_mw"
  navn           text not null,
  kind           text not null check (kind in ('social','ecological','context')),
  dimension_id   text not null references dimensions(id),
  unit           text,
  data_year      text,                      -- tekst, ikke int: "2023-2025" forekommer
  source_name    text,                      -- "DST HISBK", "DCE Biodiversitetskort (bioscore)"
  source_url     text,                      -- link vist på metode-siden
  dst_table      text,                      -- "HISBK", "GS/KARA/KARAGNS", null hvis ikke DST/UVM
  baseline_level int check (baseline_level in (1,2,3)),
  inverse        boolean not null default false,
  absolute_score boolean not null default false,  -- se afsnit 4, regel R7
  baseline_type  text check (baseline_type in ('absolut','relativ')),
  transform      text not null default 'none'
                 check (transform in ('none','inverse_10000','recycling_eu_target',
                                      'cba_div3','abs_target','social_cap')),
                 -- normativ transformregel for skriveveje, se afsnit 4
  abs_target     numeric,                   -- kun ved transform='abs_target' (education: 95)
  ratio_cap      numeric,                   -- 150 for sociale, 300 hvor sat for eco, ellers null
  lower_is_better boolean,                  -- kun eco-sub: styrer visning
  boundary_text  text,                      -- kun eco-sub: grænsetekst til UI
  raw_key        text,                      -- kun eco-sub: rawValues-nøgle (fra ECO_RAW_KEY_MAP)
  ratio_key      text,                      -- kun eco-sub: ratio-nøgle (fra ECO_RAW_KEY_MAP), kan være null
  name_keyed     boolean not null default false, -- true: kildedata matches på kommunenavn (vejr_skader, forbrug_co2)
  sort_order     int not null,
  active         boolean not null default true,
  metode_tekst   text,                      -- markdown, redigerbar i admin
  begraensninger text                       -- markdown, redigerbar i admin
);

create table indicator_values (
  kommune_kode  text not null references kommuner(kode),
  indicator_id  text not null references indicators(id),
  raw_value     numeric,                    -- null tilladt
  ratio         numeric,                    -- null tilladt; FÆRDIG direkte ratio (samme semantik som master-CSV)
  updated_at    timestamptz not null default now(),
  updated_by    text not null,              -- 'seed' | 'import' | 'edge:<funktionsnavn>' | 'admin'
  primary key (kommune_kode, indicator_id)
);

create table import_log (
  id          bigint generated always as identity primary key,
  created_at  timestamptz not null default now(),
  kind        text not null check (kind in ('seed','file_import','edge_function','manual_edit')),
  indicator_id text,                        -- null ved multi-indikator-kørsler
  source_ref  text,                         -- filnavn eller edge-funktionsnavn
  row_count   int,
  detail      jsonb                         -- diffs: [{kommune_kode, felt, gammel, ny}]
);

create table admin_users (
  user_id uuid primary key references auth.users(id)
);
```

### RLS-politikker (normative)
- `kommuner`, `dimensions`, `indicators`, `indicator_values`: SELECT for alle (anon + authenticated). INSERT/UPDATE/DELETE kun hvis `auth.uid()` findes i `admin_users`.
- `import_log`, `admin_users`: al adgang kun for `admin_users`.
- Edge functions bruger service role og logger til `import_log` med `kind='edge_function'`.
- Acceptkriterium: en anonym klient kan læse alle offentlige tabeller og kan IKKE skrive til nogen tabel. Testes eksplicit i fase 5.

### Semantik der SKAL bevares
- `ratio`-kolonnen indeholder den FÆRDIGE ratio, identisk med `ratio`-kolonnen i `data/master_indicators.csv` i dag. Alle transformationer (afsnit 4) sker på skrivetidspunktet, aldrig ved læsning.
- Sociale ratios: 100 = landsgennemsnit (eller absolut mål ved `absolute_score`), højere = bedre.
- Øko-ratios: 100 = grænsen, højere = værre (overshoot).
- Kontekst-indikatorer (`kind='context'`): kun `raw_value`, `ratio` er altid null.
- Kommune "000" (Danmark-aggregat) må ikke forekomme i `kommuner`. Christiansø er ikke en kommune og må ikke forekomme.

---

## 4. Transform- og beregningsregler (normative invarianter)

Disse regler er projektets faglige kerne. De er i dag implementeret i `scripts/build_master_csv.py` og `webapp/lib/shared.ts` (linjereferencer nedenfor). Enhver port SKAL reproducere dem præcist. Paritetstesten (afsnit 8) verificerer dem.

**R1 - Social ratio-cap:** alle sociale ratios cappes ved 150.0 (build_master_csv.py:351-353). Gælder også efter abs_target-beregning.

**R2 - Absolut mål (transform='abs_target'):** `ratio = min(raw / abs_target * 100, 150)`, afrundet til 2 decimaler (build_master_csv.py:346-348). Bruges i dag KUN af `education` (abs_target=95). `bolig_fossil` er OGSÅ absolut scoret, men dens ratio (100 - samlet fossil%) beregnes i fetch-scriptet og gemmes færdig; dens transform er 'none'.

**R3 - Inverse eco-ratio (transform='inverse_10000'):** kildedata leverer inverteret ratio (lav = værre). Konvertering: `direct = round(10000 / inverse, 2)`; null eller 0 giver null (build_master_csv.py:229-234). Gælder: `naer_nitrogen`, `naer_phosphorus`, `cirkularitet_waste`.

**R4 - Genanvendelse (transform='recycling_eu_target'):** `ratio = round((65 / pct) * 100, 2)`; null eller 0 giver null (build_master_csv.py:237-242). Over 100 = genanvender for lidt. Gælder kun `cirkularitet_recycling`.

**R5 - Forbrugs-CO2 (transform='cba_div3'):** `ratio = round((raw / 3) * 100, 2)` (build_master_csv.py:245-249). Gælder kun `forbrug_co2`. Kildedata er navn-nøglet (name_keyed=true), intet fallback ved manglende match.

**R6 - Eco ratio-cap:** hvor `ratio_cap` er sat, klippes ratio til cap-værdien (build_master_csv.py:436-440). I dag: `overfladevand`, `bio_vasentlig`, `bio_uerstattelig` = 300.

**R7 - Dimensionsscore (eco):** pr. kommune og dimension: saml alle ikke-null sub-ratios. `aggregation='worst_of'`: score = round(max, 2). `aggregation='average'`: score = round(gennemsnit, 2). Ingen sub-ratios = score er null (build_master_csv.py:252-265, 497-525). KUN `forurening` har 'average'. Beregnes ved indlæsning i frontend (beslutning B5), ikke gemt i DB.

**R8 - Social kategoriscore:** simpelt gennemsnit af ikke-null indikator-ratios i kategorien; ingen data = null (shared.ts:835-862, `computeCategoryScores`). Porteres uændret.

**R9 - Top10-baseline:** pr. social indikator: (a) hvis `absolute_score`: kopier ratio uændret; (b) ellers: sorter alle kommuners ratio faldende, tag gennemsnit af de 10 højeste, ny ratio = `parseFloat((ratio / top10Avg * 100).toFixed(2))`; (c) færre end 10 gyldige værdier: kopier ratio uændret (shared.ts:913-957, `computeTop10Ratios`). Porteres uændret.

**R10 - Kommunegruppe-baseline:** pr. social indikator og gruppe G1-G5: uvægtet gruppegennemsnit af ratio, ny ratio = `parseFloat((ratio / gruppeAvg * 100).toFixed(2))`; `absolute_score` kopieres uændret (shared.ts:1002-1049, `computeGroupRatios`). Gruppetilhør fra `kommuner.kommunegruppe`. Porteres uændret.

**R11 - Farvetærskler:** sociale: score >= 100 grøn (emerald), >= 85 amber, < 85 rød (shared.ts:1051-1063). Økologiske: <= 85 grøn, <= 100 amber, > 100 rød (`ecoScoreColor`/`ecoBarColor` i ScoreBars.tsx). OMVENDT retning - må ikke forveksles.

**R12 - baselineType-udledning:** social indikator: 'absolut' hvis `absolute_score`, ellers 'relativ'. Dimension/kategori: alle ens type = den type, ellers 'blandet'; tom liste = 'relativ' (shared.ts:864-890). Porteres uændret.

**R13 - null vs. manglende:** i `KommuneData` skal ALLE aktive indikatorer have en nøgle i `ratios` (null hvis ingen data), og ALLE eco-dimensioner en nøgle i `eco_ratios` (null hvis ingen data). client.tsx skelner mellem null og undefined ved optælling af "afventer data" (data.ts:178-192). Skal bevares.

**R14 - Ratio-validering:** gyldigt interval 0-2000; værdier udenfor er en fejl der skal rapporteres, ikke klippes (build_master_csv.py:530-536). Bruges i import-funktionen og paritetstesten.

**R15 - Baseline-toggle:** påvirker KUN sociale indikatorer. Øko-dimensioner har absolutte grænser og ændres aldrig af toggle (avg/top10/gruppe).

---

## 5. Frontend-port: fil-for-fil

Alle stier er relative til nuværende `webapp/` hhv. nyt Lovable-projekt `src/`.

| Nuværende fil | Ny fil | Handling |
|---|---|---|
| `lib/shared.ts` | `src/lib/shared.ts` | Typer + compute-funktioner (R8-R12) kopieres ORDRET. Konstant-arrays (INDICATORS, SOCIAL_CATEGORIES, ECOLOGICAL_DIMENSIONS, KOMMUNEGRUPPE) FJERNES - erstattes af DB-load, se afsnit 6 |
| `lib/data.ts` | `src/lib/data.ts` | Omskrives: Supabase-klient i stedet for fs/CSV. Kontrakt i afsnit 6. ECO_RAW_KEY_MAP udgår (erstattet af `indicators.raw_key`/`ratio_key`) |
| `lib/vurdering.ts` | `src/lib/vurdering.ts` | Kopieres ordret |
| `lib/baseline-context.tsx` | `src/lib/baseline-context.tsx` | Kopieres; `"use client"` slettes |
| `components/*.tsx` (alle 7) | `src/components/*.tsx` | Kopieres; `"use client"` slettes; `next/link` -> `react-router-dom` Link (kun KommuneSearch.tsx); imports af konstanter skiftes til metadata-context |
| `app/layout.tsx` | `src/App.tsx` + `src/components/Layout.tsx` | Header/footer/nav bevares visuelt identisk; BaselineProvider + MetadataProvider wrapper |
| `app/page.tsx` | `src/pages/Forside.tsx` | Kopieres |
| `app/kommune/[navn]/page.tsx` | `src/pages/Kommune.tsx` | `generateStaticParams` udgår. Route-param `:navn` afkodes med `decodeURIComponent`; opslag matcher navn (case-insensitivt) ELLER kode, som `getKommune` i dag (data.ts:220-228) |
| `app/kommune/[navn]/client.tsx` | del af `src/pages/Kommune.tsx` | Server/client-skel udgår; logik bevares |
| `app/metode/page.tsx` | `src/pages/Metode.tsx` | OMSKRIVES: genereret fra DB (afsnit 9). Prosa udtrækkes til DB i fase 1 |
| `app/om/page.tsx`, `app/artikel/...` | `src/pages/Om.tsx`, `src/pages/ArtikelPlanetaereGraenser.tsx` | Kopieres |
| `app/globals.css` | `src/index.css` | Tailwind 4-opsætning overføres |
| `netlify/functions/klimaregnskabet.mts` | udgår | Kaldes ikke af frontenden. API-nøglen (`KLIMAREGNSKABET_API_KEY`) flyttes til Supabase secret til brug i fase 6 |

Routing (react-router-dom): `/`, `/kommune/:navn`, `/metode`, `/om`, `/artikel/planetaere-graenser`, `/admin/*` (beskyttet). 404 renderer en "kommune ikke fundet"-side med link til forsiden.

---

## 6. Dataindlæsning i den nye app (loader-kontrakt)

### Metadata-load (erstatter konstant-arrays)
Ved app-opstart hentes `dimensions` og `indicators` (kun `active=true`) og der bygges objekter med PRÆCIS samme form som de nuværende konstanter:

- `INDICATORS: Indicator[]` fra `indicators` hvor kind='social' eller 'ecological', sorteret på `sort_order`.
- `SOCIAL_CATEGORIES: SocialCategory[]` fra `dimensions` hvor kind='social'; `indicatorIds` = sociale indikatorer med matchende `dimension_id`, sorteret på `sort_order`.
- `ECOLOGICAL_DIMENSIONS: EcologicalDimension[]` fra `dimensions` hvor kind='ecological'; `subIndicators` bygges fra eco-indikatorer med matchende `dimension_id` (rawKey, ratioKey, label=navn, unit, boundary=boundary_text, lowerIsBetter, baselineType).

Disse leveres via en React context (`MetadataProvider`) og en modul-level getter, så komponenterne kan beholde deres nuværende brugsmønster med minimale ændringer. Typerne i shared.ts ændres IKKE.

### Værdi-load (erstatter parseMasterCsv)
Hent alle rækker fra `indicator_values` (join på `indicators` for kind/raw_key/ratio_key). Byg `KommuneData[]` efter PRÆCIS de regler `loadData()` bruger i dag (data.ts:120-218):

1. Gruppér pr. kommune.
2. `kind='social'`: `ratios[indicator_id] = ratio`; `rawValues[indicator_id] = raw_value` hvis ikke null.
3. `kind='context'`: `rawValues[indicator_id] = raw_value` hvis ikke null.
4. `kind='ecological'`: `rawValues[raw_key] = raw_value` hvis ikke null; `rawValues[ratio_key] = ratio` hvis ratio_key ikke er null og ratio ikke null.
5. Beregn `eco_ratios[dimension_id]` pr. R7 (worst-of/average af sub-ratios) - NYT i loaderen, da `_dim_`-rækker ikke findes i DB.
6. Udfyld null for alle manglende indikatorer og dimensioner (R13).
7. Kør `computeTop10Ratios` og `computeGroupRatios` (uændrede).
8. `social_avg` og `overall_avg` sættes til null (bruges ikke af UI).

Resultatet caches i memory for sessionen (som `cachedData` i dag).

---

## 7. Fase 1: Seed-procedure

Seed sker fra det eksisterende repo og SKAL være reproducerbar:

1. Nyt script `scripts/generate_supabase_seed.py` læser:
   - `data/master_indicators.csv` -> `indicator_values` (kolonnerne ratio/raw_value overføres uændret; `_dim_`-rækker SPRINGES OVER, jf. B5) + kommuneliste -> `kommuner`.
   - `webapp/lib/shared.ts` er IKKE maskinlæsbar fra Python; metadata-seed for `dimensions` og `indicators` skrives i stedet som en manuelt gennemgået SQL/CSV-fil, genereret af den implementerende AI ud fra shared.ts + build_master_csv.py's tre lister (SOCIAL_INDICATORS, ECO_SUB_INDICATORS, CONTEXT_INDICATORS). Felterne transform/ratio_cap/name_keyed udfyldes efter reglerne i afsnit 4.
   - `KOMMUNEGRUPPE`-mapping fra shared.ts -> `kommuner.kommunegruppe`.
2. Output: `supabase/seed.sql` committes i repoet, så seed kan genkøres og reviewes.
3. Metode-prosa: teksterne i `app/metode/page.tsx` udtrækkes afsnit for afsnit til `dimensions.metode_tekst`/`begraensninger` og `indicators.metode_tekst`. Udtrækket samles i et gennemgangs-dokument som August godkender FØR det seedes (fejlbart, manuelt arbejde - skal reviewes).
4. Konsistenstjek efter seed: antal kommuner = 98; antal værdirækker = antal ikke-`_dim_`-rækker i master-CSV; stikprøve på 5 kommuner sammenlignes felt for felt.

---

## 8. Fase 3: Paritetstest (acceptkriterium for go-live)

1. FØR migrering: kør et lille script i det nuværende webapp (`webapp/scripts/export_parity_baseline.ts`, køres med tsx/node) der kalder `loadData()` og dumper HELE `KommuneData[]` (inkl. top10_ratios, group_ratios, eco_ratios, rawValues) til `data/parity_baseline.json`. Committes.
2. Det nye system implementerer en dev-side `/admin/paritet` (eller et script) der bygger `KommuneData[]` fra Supabase og sammenligner mod `parity_baseline.json`.
3. Sammenligning: ALLE 98 kommuner, ALLE nøgler i ratios/top10_ratios/group_ratios/eco_ratios/rawValues. Numerisk tolerance: absolut afvigelse <= 0.01 (afrundingsforskelle mellem Python og JS). null skal matche null.
4. Acceptkriterium: 0 afvigelser. Enhver afvigelse skal forklares og rettes; "tæt nok" findes ikke.
5. Derudover visuel kontrol af mindst: Thisted (787), København (101), Aarhus (751), Læsø (825) - donut, scorebars, vurderingsboks, baseline-toggle i alle tre stillinger, print-visning.

---

## 9. Metode 2.0 (genereret metode-side)

Metode-siden bygges af databasen, IKKE af håndskrevet JSX:

- Pr. dimension (begge kinds, sorteret på sort_order): navn, description, boundary_text, aggregation forklaret ("worst-of" / "gennemsnit"), metode_tekst (markdown), begraensninger (markdown).
- Pr. indikator under dimensionen: navn, kilde som link (source_name -> source_url), dst_table, data_year, unit, baseline (baseline_level, baseline_type, abs_target/boundary_text), inverse-markering, metode_tekst.
- "Sidst opdateret" pr. indikator: max(updated_at) fra indicator_values for den indikator.
- Markdown renderes med en let renderer (fx react-markdown); ingen rå HTML fra DB.
- Kontekst-indikatorer vises i en tydeligt markeret "vises, men scores ikke"-sektion under deres dimension.

Konsekvens: retter August et dataår, kildelink eller en tekst i admin, slår det igennem på metode-siden og i UI-tooltips samtidig. Det er hele pointen med B3.

---

## 10. Admin-modul

### Adgang
Supabase Auth, email + password, kun August. `admin_users`-tabellen styrer skriveadgang (RLS, afsnit 3). Ingen selvregistrering: signup slås fra; brugeren oprettes manuelt i Supabase-dashboardet.

### /admin/vaerdier
Tabel med filtrering på indikator og kommune. Inline-redigering af raw_value og ratio. Ved redigering af raw_value på en indikator med transform != 'none' tilbydes automatisk genberegning af ratio efter reglerne i afsnit 4 (vises som forhåndsvisning, August bekræfter). Hver gemning skriver `import_log` med kind='manual_edit' og diff i detail.

### /admin/indikatorer
CRUD for indicators og dimensions, inkl. markdown-editor for metode_tekst/begraensninger med preview. Nye indikatorer kan oprettes (id, kind, dimension, transform osv.); sletning er soft (active=false).

### /admin/import (import-funktionen)
Fire trin, alle i browseren:

1. **Upload/indsæt:** CSV-fil, Excel-fil (første ark) eller indsat tabeltekst (tab/komma-separeret). Parses klient-side (papaparse + SheetJS).
2. **Mapping:** brugeren vælger mål-indikator. Systemet foreslår kolonnemapping: kommune-kolonne (auto-detektér 'kommune_kode'/'kommune_navn'/'kommune'), raw-kolonne, evt. ratio-kolonne. Hvis kun raw leveres og indikatoren har transform != 'none', beregnes ratio efter afsnit 4. Understøtter de eksisterende `data/*_scores.csv`-formater direkte (kolonnenavne fra build_master_csv.py's lister vises som hint).
3. **Validering og diff:** kommunematch på kode, ellers navn (eksakt match mod kommuner.navn; name_keyed-indikatorer matcher altid på navn). Rapport: X/98 kommuner matchet, umatchede rækker listes (fx Christiansø -> ignoreres med advarsel), ratios uden for 0-2000 blokerer (R14), og en diff-tabel "kommune: gammel -> ny" for alle ændringer. Intet skrives endnu.
4. **Commit:** kræver eksplicit bekræftelse. Upsert til indicator_values, én import_log-række med kind='file_import', row_count og fuld diff i detail.

Import-funktionen er den permanente opdateringsvej for geodata/manuelle indikatorer (afsnit 11) og fallback for alt andet.

### /admin/log
Læsevisning af import_log, nyeste først, med udfoldelig diff.

---

## 11. Edge functions (fase 6): disposition pr. datakilde

Ratio-formlerne i de eksisterende fetch-scripts er normative; porten skal reproducere deres output. Generel social-formel: direkte `(kommune/landsgennemsnit)*100`, inverse `(landsgennemsnit/kommune)*100`, cap 150 (R1). Hver funktion logger til import_log og opdaterer KUN sine egne indikatorer.

### Porteres til Supabase Edge Functions (TypeScript/Deno)
| Funktion | Erstatter | Kilde | Bemærkning |
|---|---|---|---|
| `fetch-statbank-social` | fetch_doughnut_data.py m.fl. | api.statbank.dk | Største funktion; alle DST-sociale indikatorer. Kan opdeles pr. script-modstykke |
| `fetch-uvm` | fetch_udvidelse_data.py | api.uddannelsesstatistik.dk | |
| `fetch-eds-ve` | fetch_ve_kapacitet.py | api.energidataservice.dk CapacityPerMunicipality | Kontekst-indikatorer ctx_ve_* |
| `fetch-fjernvarme-mix` | fetch_fjernvarme_mix.py | ens.dk/media/7199/download (Excel) | SheetJS-parsing. SKAL køre før fetch-bolig-fossil |
| `fetch-bolig-fossil` | fetch_bolig_fossil.py | api.statbank.dk BOL202 + ctx_fjv_fossil fra DB | Læser fjernvarmens fossilandel fra indicator_values i stedet for CSV. TJ-vægtet landssnit for de 18 fælles-net-kommuner SKAL genimplementeres præcist - flag til grundig test |
| `fetch-klimaregnskabet` | fetch_climate_data.py | klimaregnskabet.dk API | API-nøgle som Supabase secret |
| `fetch-klimatilpasning` | fetch_klimatilpasning_data.py | datawrapper CSV (F&P) | name_keyed |
| `fetch-arealanvendelse` | fetch_dst_arealanvendelse.py | api.statbank.dk AREALDK2 | |
| `fetch-vandindvinding` | fetch_vandindvinding_data.py | api.statbank.dk VANDIND | |
| `fetch-naeringsstoffer-np` | del af fetch_eco_new_data/naeringsstoffer | api.statbank.dk VANDUD | transform inverse_10000 |
| `fetch-affald-genanvendelse` | del af forurening/consumption | api.statbank.dk | transforms inverse_10000 + recycling_eu_target |

Orkestrering: en `update-all`-funktion kalder ovenstående i korrekt rækkefølge (fjernvarme-mix før bolig-fossil; resten uafhængige). Admin har både "Opdater alt" og pr.-funktion-knapper.

### Porteres IKKE - opdateres via /admin/import
| Indikatorer | Nuværende script | Hvorfor ikke |
|---|---|---|
| luftkvalitet_no2, luftkvalitet_pm25 | fetch_luftforurening_data.py | WFS/geodata-beregning (geopandas) |
| bio_vasentlig, bio_uerstattelig | fetch_biodiversitet_data.py | DCE bioscore-raster; statisk 2021-data |
| naer_landbrug | fetch_naeringsstoffer_landbrug.py | VP3 geoserver/geodata |
| overfladevand | fetch_vp3_vandkvalitet.py | VP3 shapefile-zip |
| pesticider | fetch_pesticider_data.py | Manuel kilde (DN/GEUS) |
| nitrat | fetch_nitrat_data.py | Manuel kilde (Greenpeace/GEUS) |
| forbrug_co2 | cba_2023_estimate.csv | Statisk metodeestimat (se data/methodology_note.md) |

Disse ligger stille mellem sjældne opdateringer. Ved behov: kør det gamle Python-script lokalt (eller bed en Claude-session om det), tag den producerede CSV, og træk den ind via import-funktionen.

---

## 12. Faseplan med acceptkriterier

Rækkefølgen er bindende. En fase påbegyndes først når den forriges acceptkriterium er opfyldt. Efter fase 4 KAN sitet gå live (Augusts beslutning); fase 5-6 kan bygges på et kørende site.

| Fase | Indhold | Acceptkriterium | Anbefalet model |
|---|---|---|---|
| 0 | parity_baseline.json genereres og committes i DETTE repo (afsnit 8, trin 1) | Filen findes og indeholder 98 kommuner | Sonnet |
| 1 | Supabase-projekt, skema (afsnit 3), seed (afsnit 7), metode-prosa-udtræk godkendt af August | Konsistenstjek i 7.4 bestået; RLS-læsetest OK | Opus |
| 2 | Lovable-projekt, GitHub-kobling, fil-port (afsnit 5), MetadataProvider | Appen bygger og renderer forside + en kommuneside med DB-data | Sonnet |
| 3 | Loader-kontrakt (afsnit 6), routing, paritetstest | 0 afvigelser i paritetstesten (afsnit 8) | Opus |
| 4 | Metode 2.0 (afsnit 9) | Metode-siden viser samme faglige indhold som i dag, genereret fra DB; August godkender visuelt | Sonnet |
| 5 | Auth + admin-modul inkl. import (afsnit 10) | August kan uden hjælp: rette en værdi, rette en metode-tekst, importere en *_scores.csv og se diffen. RLS-skrivetest: anonym klient afvises | Sonnet |
| 6 | Edge functions (afsnit 11) | Hver funktion kørt mod produktion giver værdier identiske med seneste Python-kørsel (eller forklarede, godkendte afvigelser pga. friskere kildedata) | Opus (skabelon, bolig_fossil, beregninger); Sonnet (øvrige) |
| 7 | Bruger-features | Specificeres separat - IKKE dækket af dette dokument | - |
| 8 | Go-live: domæne peges om, gammelt Netlify-site fryses (ikke slettes) | August godkender. Rollback = peg domænet tilbage | Haiku |

---

## 13. Kendte fælder (arvet viden - SKAL respekteres)

1. Farvelogik er OMVENDT mellem social og eco (R11). Hyppigste fejlkilde.
2. Forurening er ENESTE gennemsnits-dimension; alle andre eco-dimensioner er worst-of (R7).
3. `forbrug_co2` og `vejr_skader` matcher på kommunenavn, ikke kode. Manglende match = null, intet fallback. Christiansø filtreres fra.
4. `absolute_score`-indikatorer (education, bolig_fossil) må ALDRIG omskaleres af baseline-toggle (R9, R10).
5. bolig_fossil afhænger af fjernvarme-mix-data; rækkefølgen er bindende (afsnit 11).
6. null vs. undefined-skelnen i eco_ratios er semantisk bærende i UI'et (R13).
7. Kommunenavne indeholder æ/ø/å og "Høje-Taastrup", "Ringkøbing-Skjern" m.fl. URL-encoding og navnematch skal håndtere dette; match er case-insensitivt.
8. Ingen kommune når grønt på bolig_fossil - det er korrekt og bevidst (absolut mål 0%), ikke en databug.
9. Python-scripts og data/-CSV'er må ikke slettes eller "ryddes op" under migreringen (B9).

---

## 14. Risici og accepterede trade-offs

| Risiko | Håndtering |
|---|---|
| Talregression ved port af beregninger | Paritetstest med 0-tolerance (afsnit 8); fuld matrix, ikke stikprøver |
| Metode-prosa-udtræk mister nuancer | Gennemgangs-dokument godkendes af August før seed (7.3) |
| SEO: SPA erstatter 98 pre-renderede statiske sider | ACCEPTERET trade-off for MVP. Kan senere afbødes med prerendering. Titel/meta sættes dynamisk pr. rute |
| Metode-prosa versionsstyres ikke i git | ACCEPTERET (B4). import_log giver ændringshistorik på data; prosa-historik findes ikke i MVP |
| Lovable-credits: porten koster beskeder til Lovables agent | Fase 2-3 er dyrest. Arbejd i store, veldefinerede beskeder ud fra dette dokument i stedet for mange små |
| RLS-fejl eksponerer skriveadgang | Eksplicit negativ test i fase 5-acceptkriteriet |
| Supabase free tier-grænser (DB-størrelse, edge-kald) | Datamængden er lille (<10 MB). Ved pause-varsler på free tier: opgradér eller acceptér ugentlig aktivitet |
| bolig_fossil-genimplementering (TJ-vægtning, 18 fælles-net-kommuner) | Udpeget som særskilt testpunkt i fase 6 |

---

## 15. Vedligehold af dette dokument

Dokumentet opdateres når en fase afsluttes (markér acceptkriterium som opfyldt med dato) eller en låst beslutning ændres af August (tilføj række i beslutningsloggen med begrundelse). Implementerende AI'er skal referere til afsnitsnumre herfra i commits og beskeder, fx "implementerer afsnit 6, R7".
