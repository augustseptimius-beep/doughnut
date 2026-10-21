# Migrationsspecifikation v2: Danmarks 98 Doughnuts til Lovable

**Status:** v2, godkendt princip. Implementering IKKE påbegyndt.
**Historik:** v1 godkendt 2026-08-06. v2 skrevet 2026-10-21 efter review (16 fund) og to nye beslutninger fra August: (1) kun Lovable som leverandør, ingen egne underleverandører, (2) git er sandheden, data skal altid kunne hentes på ny via scripts, og metode-tekster ligger som filer i repoet.
**Målgruppe:** AI-agenter (Claude, Lovables agent) der implementerer migreringen. Dokumentet er normativt. Afvigelser kræver eksplicit godkendelse fra August. Afsnit markeret [info] er baggrund.

---

## 0. Grundprincip

> **Git er sandheden. Alt andet kan smides væk og genskabes.**

Alle tal, al metadata og alle metode-tekster ligger som filer i ét git-repo. Det offentlige site læser direkte fra disse filer (bundlet ved build). Der er INGEN database med indikatordata. Datahentning sker via scripts (Lovable edge functions), som producerer nye filer, der committes til git.

Konsekvenser:
- Flytning mellem Lovable-workspaces er ikke en datarisiko: et nyt projekt fra repoet har alle data.
- Exit ved udbud: repoet er et almindeligt Vite + React-projekt med data som CSV.
- Ingen databaseadgang, RLS eller rækkegrænser på det offentlige site.
- Ændringshistorik på alt (tal, tekster, metadata) via git.

**Hvert faktum har præcis ét hjem** (se afsnit 3). Intet faktum må skrives to steder. Det er løsningen på at metode-siden går i utakt med data. Ved v2-review blev der konstateret to aktive eksempler: metode-siden angiver dataår "2022" for Lighed (reelt 2022-2024) og "2023" for Ligestilling (reelt 2023-2025), fordi dimensionsårstal er håndskrevet i `metode/page.tsx`.

---

## 1. Beslutningslog (låste beslutninger)

| # | Beslutning | Begrundelse |
|---|---|---|
| B1 | Appen genopbygges i Lovable som Vite + React + TypeScript + Tailwind + shadcn/ui. Hvis Lovable tilbyder prerendering/SSR ved oprettelse (V1), foretrækkes det | Lovable understøtter ikke Next.js. Prerendering ville løse SEO-trade-off |
| B2 | Lovable er eneste leverandør. Backend = Lovable Cloud. Ingen eget Supabase, Netlify eller andre underleverandører i målbilledet | Kommunen opretter ikke egne underleverandører. Lovable Cloud er dækket af Lovables databehandleraftale |
| B3 | Git er sandheden (afsnit 0). Indikatorværdier ligger som snapshot-filer i repoet, ikke i en database | Data altid genskabelig, uafhængig af workspace og flytning |
| B4 | Metadata ligger i et typet register i repoet. Metode-tekster ligger som markdown-filer. Redigering sker via Lovables chat, som committer til git | Godkendt af August (valg a). Giver versionshistorik og ét hjem pr. faktum |
| B5 | Dataår, kilde-tidspunkt og hentemetode skrives KUN af snapshot-commit-funktionen til et manifest, aldrig i hånden | Fjerner utakt mellem data og metode-side |
| B6 | Al dataskrivning sker som filer der ender i git. Ingen manuel redigering af enkeltværdier i admin. Rettelser sker via import af en fil | Ellers kan data ikke genskabes |
| B7 | Datahentning sker i to trin: (1) hent + valider + vis diff (skriver intet), (2) godkendt commit af snapshot til git i ét atomisk commit | Ingen halve opdateringer, menneskelig godkendelse |
| B8 | Kilder med API porteres til edge functions. Geodata- og manuelle kilder er "frosne": snapshot i git er kilden, opdateres via import | Se afsnit 9 |
| B9 | Edge functions udløses manuelt fra admin. Ingen cron i scope | Data opdateres sjældent |
| B10 | Øko-dimensionsscorer og baselines (top10, gruppe) beregnes i frontend ved indlæsning, som i dag | Uændret faglig logik |
| B11 | Kun nuværende værdier (ingen tidsserier i UI). Git-historikken bevarer tidligere værdier | Matcher nuværende funktionalitet |
| B12 | Persondata (rigtige brugerkonti, feedback) må KUN behandles i et kommunalt Lovable Business/Enterprise-workspace med databehandleraftale. I et privat workspace bruges kun offentlige data og en testkonto uden persondata | Lovable: "Free and Pro accounts have no data processing agreement" |
| B13 | Ét repo efter fase 2: Lovable-projektets repo rummer app, data, register, metode-tekster, edge functions, Python-opskrifter og denne spec. Det nuværende doughnut-repo arkiveres efter go-live | Én kilde, ingen tvivl om hvor noget bor |
| B14 | Python-scripts bevares urørt (flyttes til `tools/python/` i det nye repo) som opskrift og fallback | Frosne kilder kan genskabes af en Claude-session uden for Lovable |
| B15 | Det gamle site kører parallelt indtil go-live er godkendt. Rollback = peg domænet tilbage | Ingen nedetid |
| B16 | Migreringen er 1:1 på al faglig logik. Kendte uklarheder (fx housing_no_wc/no_bath uden kategori) bevares og listes til senere afklaring | Paritet før forbedring |

---

## 2. Målarkitektur

```
Lovable-projekt (ét repo, git sync begge veje)
├── src/                              Appen (Vite + React)
│   ├── pages/                        Forside, Kommune, Metode, Om, Artikel, Admin
│   ├── components/                   Porterede komponenter (afsnit 6)
│   └── lib/
│       ├── shared.ts                 Typer + compute-funktioner (porteret)
│       └── data.ts                   Loader: snapshots -> KommuneData[] (afsnit 7)
├── registry/                         ★ METADATA (typet TypeScript, eneste hjem)
│   ├── settings.ts                   DOUGHNUT_EDITION_YEAR m.m.
│   ├── kommuner.ts                   98 kommuner: kode, navn, kommunegruppe
│   ├── dimensions.ts                 Sociale kategorier + øko-dimensioner
│   ├── indicators.ts                 Alle indikatorer inkl. transform og hentekonfiguration
│   └── references.ts                 Kildehenvisninger (label + url), refereret via id
├── content/metode/                   ★ METODE-TEKSTER (markdown, eneste hjem)
│   ├── generelt/*.md                 Generelle afsnit (baseline-hierarki, scoring, grænser, databehandling)
│   ├── dimensioner/<dimension_id>.md
│   └── indikatorer/<indicator_id>.md
├── data/snapshots/                   ★ VÆRDIER (eneste hjem)
│   ├── <indicator_id>.csv            Én fil pr. indikator
│   └── _manifest.json                Dataår, kilde, tidspunkt, metode pr. indikator (skrives kun af commit-snapshot)
├── supabase/functions/               Edge functions (Lovable Cloud)
│   ├── _shared/                      Fælles: statbank-klient, transforms, validering, git-commit
│   ├── fetch-<kilde>/                Én funktion pr. kilde (afsnit 9), dry-run only
│   └── commit-snapshot/              Eneste funktion der skriver til git
├── tools/
│   ├── python/                       De gamle scripts (B14)
│   └── migration/                    Engangs-konvertering (fase 1)
└── docs/                             Denne spec + metodenoter fra data/
```

Det offentlige site bruger ingen database og ingen edge functions. Admin bruger Lovable Cloud Auth + edge functions. Fase 8 (bruger-features) indfører databasetabeller og specificeres separat.

Dataflow ved opdatering:
```
Admin: "Hent kilde X"  ->  fetch-X (dry-run)  ->  diff + validering vises
       August godkender ->  commit-snapshot   ->  ét git-commit (snapshots + manifest)
       Lovable git sync ->  August trykker Publicér  ->  nyt data live
```

---

## 3. Fakta og deres hjem (normativt)

| Faktum | Eneste hjem | Skrives af |
|---|---|---|
| Indikatornavn, enhed, kategori/dimension, transform, grænse, inverse, absoluteScore, baselineLevel, baselineType, DST-tabel, kilde-navn, kilde-URL, hentekonfiguration | `registry/indicators.ts` | Udvikler / Lovable-chat |
| Kategori- og dimensionsnavn, beskrivelse, aggregering, sortering, grænsetekst | `registry/dimensions.ts` | Udvikler / Lovable-chat |
| Kildehenvisninger med flere links (fx `boundarySources`) | `registry/references.ts` | Udvikler / Lovable-chat |
| Kommuner og kommunegrupper | `registry/kommuner.ts` | Udvikler |
| Doughnut-edition og standard-dataår | `registry/settings.ts` | Udvikler / Lovable-chat |
| Metode-prosa (scoring-forklaring, rationale, begrænsninger, generelle afsnit) | `content/metode/**/*.md` | Lovable-chat |
| Værdier (raw_value, ratio) pr. kommune × indikator | `data/snapshots/<id>.csv` | KUN `commit-snapshot` (og fase 1-konvertering) |
| Dataår, hentetidspunkt, hentemetode, referenceværdi, rækkeantal | `data/snapshots/_manifest.json` | KUN `commit-snapshot` (og fase 1-konvertering) |
| Dimensionens dataår-interval | INGEN, udledes altid (min-max af indikatorernes dataår fra manifest) | Ingen |
| Dimensionsscore (worst-of/gennemsnit), top10- og gruppe-baseline | INGEN, beregnes i frontend (R7, R9, R10) | Ingen |

Regel: metode-side, scorebars, tooltips og print-visning læser fra de samme hjem. Ingen komponent må have hårdkodede kopier af fakta fra tabellen.

**Konfliktregel for fase 1-konverteringen:** hvor `webapp/lib/shared.ts` og `scripts/build_master_csv.py` er uenige, vinder `shared.ts` (det er hvad UI viser i dag). Kendte konflikter (enheder): `child_notifications`, `bolig_fossil`, `le_gender_gap`, `income_gender_gap`, `employment_origin_gap`. Dataår er konsistente mellem de to filer pr. 2026-10-21. Alle konflikter listes i fase 1-rapporten.

---

## 4. Filformater (normative)

### 4.1 Snapshot: `data/snapshots/<indicator_id>.csv`
```
kommune_kode,kommune_navn,raw_value,ratio
101,København,81.2,98.45
```
- UTF-8, komma-separeret, header som vist, sorteret på `kommune_kode`.
- `ratio` er den FÆRDIGE ratio (alle transforms anvendt, samme semantik som `ratio` i nuværende `master_indicators.csv`). Tom celle = null.
- Kontekst-indikatorer: `ratio` er altid tom.
- Kun kommuner med mindst én værdi har en række. Kommune "000" og Christiansø forekommer aldrig.
- Tal skrives uden tusindtalsseparator, punktum som decimaltegn, uden afrunding ud over hvad kilden/transformen giver.
- Felter må ikke indeholde komma (kommunenavne gør ikke). Parseren skal alligevel være en rigtig CSV-parser (papaparse), ikke `split(",")`.

### 4.2 Manifest: `data/snapshots/_manifest.json`
```json
{
  "schema_version": 1,
  "indicators": {
    "life_expectancy": {
      "data_year": "2023",
      "method": "api",
      "source_ref": "fetch-statbank-social",
      "fetched_at": "2026-10-21T10:00:00Z",
      "row_count": 98,
      "reference_value": null,
      "sha256": "..."
    }
  }
}
```
- `method`: `api` (hentet af edge function), `import` (fil-import), `frozen` (fra fase 1-konvertering, ikke genhentet siden).
- `reference_value`: national referenceværdi brugt i ratio-beregningen, hvor relevant (afsnit 5, R20-R22). Gemmes så ratio kan efterprøves.
- `sha256`: hash af snapshot-filen. Loaderen i dev-mode advarer ved mismatch.

### 4.3 Register: `registry/indicators.ts`
Typet array. Felter (alle normative):
```ts
interface IndicatorDef {
  id: string;
  name: string;
  kind: "social" | "ecological" | "context";
  dimensionId: string;            // hører til denne kategori/dimension (visning, metode-side)
  scoredInCategory: boolean;      // social: indgår i kategoriscoren. false for housing_no_wc, housing_no_bath (B16)
  sortOrder: number;
  unit: string;
  dstTable?: string;
  sourceName: string;             // "DST HISBK"
  sourceUrl: string;
  inverse: boolean;
  absoluteScore?: boolean;
  baselineLevel?: 1 | 2 | 3;
  absoluteTarget?: string;        // visningstekst, fx "95% (nationalt uddannelsesmål)"
  // øko-sub:
  rawKey?: string; ratioKey?: string | null; boundary?: string; lowerIsBetter?: boolean;
  baselineType?: "absolut" | "relativ";
  // beregning og hentning:
  transform: Transform;            // afsnit 5
  ratioCap?: number;               // 150 for sociale, 300 hvor sat for eco
  nameKeyed?: boolean;             // matches på kommunenavn (vejr_skader, forbrug_co2)
  expectedCoverage: number;        // forventet antal kommuner (98, eller lavere hvor kilden mangler kommuner)
  update: { method: "api"; fn: string } | { method: "frozen"; recipe: string }; // recipe = sti i tools/python/
  active: boolean;
}
```
Fra registret genereres de konstanter, komponenterne bruger i dag (`INDICATORS`, `SOCIAL_CATEGORIES`, `ECOLOGICAL_DIMENSIONS`, `KOMMUNEGRUPPE`, `DOUGHNUT_*`), med PRÆCIS samme form og indhold. Da registret er statisk kode, forbliver konstanterne modul-konstanter, og compute-funktionerne i `shared.ts` kan porteres uændret.

### 4.4 Metode-tekster
- Markdown, ingen rå HTML. Renderes med react-markdown.
- Filnavn = id. Manglende fil = sektionen udelades (ingen fejl).
- Tekster må referere til fakta via pladsholdere i stedet for at gentage dem: `{{year:<indicator_id>}}`, `{{year:dim:<dimension_id>}}`, `{{unit:<id>}}`, `{{source:<id>}}`. Pladsholdere udfyldes fra registret/manifestet ved rendering. Ukendt pladsholder = byggefejl.
- Regel: årstal, enheder og kildelinks må ikke skrives som fri tekst i markdown, når en pladsholder findes.

---

## 5. Transform- og beregningsregler (normative invarianter)

R1-R15 er uændrede fra v1 og verificeret mod koden 2026-10-21. R16-R22 er nye: de er ratio-formlerne fra fetch-scripts, som skal bruges af edge functions og af import, så import virker med råværdier alene.

**R1 Social ratio-cap:** sociale ratios cappes ved 150.0 (`build_master_csv.py:351-353`), også efter abs_target.
**R2 abs_target:** `ratio = min(raw / abs_target * 100, 150)`, 2 decimaler. Kun `education` (95). `bolig_fossil` er absolut scoret, men dens ratio (100 - samlet fossil%) beregnes i hentningen (R23).
**R3 inverse_10000:** `direct = round(10000 / inverse, 2)`, null/0 -> null. `naer_nitrogen`, `naer_phosphorus`, `cirkularitet_waste`.
**R4 recycling_eu_target:** `ratio = round(65 / pct * 100, 2)`, null/0 -> null. `cirkularitet_recycling`.
**R5 cba_div3:** `ratio = round(raw / 3 * 100, 2)`. `forbrug_co2`, navn-nøglet, intet fallback.
**R6 Eco-cap:** klip til `ratioCap`. `overfladevand`, `bio_vasentlig`, `bio_uerstattelig` = 300.
**R7 Dimensionsscore:** ikke-null sub-ratios pr. kommune og dimension. `worst_of` = round(max, 2), `average` = round(gennemsnit, 2), ingen = null. Kun `forurening` er `average`. Beregnes i frontend.
**R8 Kategoriscore:** gennemsnit af ikke-null ratios for indikatorer med `scoredInCategory=true` (`computeCategoryScores`).
**R9 Top10:** absoluteScore kopieres. Ellers gennemsnit af de 10 højeste ratios, ny = `parseFloat((ratio/top10Avg*100).toFixed(2))`. Under 10 værdier: kopier (`computeTop10Ratios`).
**R10 Kommunegruppe:** absoluteScore kopieres. Ellers uvægtet gruppegennemsnit G1-G5, ny = `parseFloat((ratio/gruppeAvg*100).toFixed(2))` (`computeGroupRatios`).
**R11 Farver:** social >=100 grøn, >=85 amber, <85 rød. Eco <=85 grøn, <=100 amber, >100 rød. OMVENDT retning.
**R12 baselineType:** social = absolut hvis absoluteScore, ellers relativ. Dimension: alle ens = den type, ellers blandet, tom = relativ.
**R13 null vs. manglende:** alle aktive indikatorer har nøgle i `ratios` (null hvis ingen data), alle eco-dimensioner har nøgle i `eco_ratios` (null hvis ingen data).
**R14 Validering:** ratio uden for 0-2000 er en fejl (blokerer commit), ikke noget der klippes.
**R15 Baseline-toggle** påvirker kun sociale indikatorer.

**R16 abs_limit (luftkvalitet):** `ratio = round(raw / limit * 100, 1)`. NO2 limit 10 µg/m³, PM2.5 limit 5 µg/m³ (WHO 2021). Kilde: `fetch_luftforurening_data.py:155-156`.
**R17 abs_limit (nitrat):** `ratio = round(raw / 6.0 * 100, 1)` (mg/L). Kilde: `fetch_nitrat_data.py:119`.
**R18 target_over_pct (biodiversitet):** `ratio = round(target / pct * 100, 2)`, pct = 0 -> 999.0 (derefter cap 300 via R6). Target 30 for `bio_vasentlig`, 10 for `bio_uerstattelig`. Kilde: `fetch_biodiversitet_data.py:165-166`.
**R19 ref_over_raw (N-loft landbrug):** `ratio = round(reference / raw * 100, 2)`, hvor reference = arealvægtet landssnit (kg N/ha). Kilde: `fetch_naeringsstoffer_landbrug.py:194, 492`.
**R20 ref_over_pct, poolet (overfladevand VP3):** `ratio = round(min(reference / pct * 100, 300), 2)`, pct = 0 -> 300. reference = poolet national andel vandområder i god tilstand. Kilde: `fetch_vp3_vandkvalitet.py:210-227`.
**R21 pct_over_ref med gulv (pesticider):** pct = 0 -> ratio 0.0. pct > 0 -> `ratio = round(max(101.0, pct / reference * 100), 1)`. reference = poolet national andel boringer over 0,1 µg/l. BEMÆRK gulvet: enhver kommune med mindst én boring over grænsen får mindst 101 (overskredet), selv under landsgennemsnit. Kilde: `fetch_pesticider_data.py:215-227`.
**R22 Poolede referenceværdier:** for R19, R20, R21 kan referencen IKKE beregnes ud fra kommunernes råværdier (den er arealvægtet eller poolet over underliggende enheder). Ved import skal referenceværdien derfor angives sammen med filen og gemmes i manifestet. Er den ikke angivet, bruges manifestets seneste reference_value, og importen markeres med advarsel.
**R23 Relative sociale ratios:** formlen er normalt `(kommune/national)*100` (direkte) eller `(national/kommune)*100` (inverse), cap 150. "National" er pr. script enten DST's landstal (kode 000) eller et beregnet snit. Hvert scripts konkrete definition er normativ og dokumenteres i funktionens header ved porteringen (fase 6). `bolig_fossil` beregnes som `100 - (direkte_fossil% + fjv_dækning% × fjv_fossil_andel%)` med TJ-vægtet landssnit for de 18 fælles-net-kommuner, jf. `fetch_bolig_fossil.py`.

Transform-typen i registret er én af: `none` (ratio leveres færdig), `inverse_10000`, `recycling_eu_target`, `cba_div3`, `abs_target`, `abs_limit`, `target_over_pct`, `ref_over_raw`, `ref_over_pct_pooled`, `pct_over_ref_floor`, `relative_national`. Parametre (limit, target, cap) står i registret, ikke i funktionskoden.

---

## 6. Frontend-port: fil-for-fil

| Nuværende (`webapp/`) | Nyt | Handling |
|---|---|---|
| `lib/shared.ts` | `src/lib/shared.ts` | Typer og compute-funktioner kopieres ordret. Konstanterne genereres nu fra `registry/` (4.3) og re-eksporteres med samme navne. `computeCategoryScores` filtrerer på `scoredInCategory` (R8) |
| `lib/data.ts` | `src/lib/data.ts` | Omskrives til snapshot-loader (afsnit 7). `ECO_RAW_KEY_MAP` udgår (erstattet af `rawKey`/`ratioKey` i registret) |
| `lib/vurdering.ts`, `lib/baseline-context.tsx` | `src/lib/` | Kopieres. `"use client"` slettes |
| `components/*.tsx` (7 stk.) | `src/components/` | Kopieres. `"use client"` slettes. `next/link` -> `react-router-dom` Link (KommuneSearch.tsx) |
| `app/layout.tsx` | `src/App.tsx` + `src/components/Layout.tsx` | Visuelt identisk |
| `app/page.tsx`, `app/om/page.tsx`, `app/artikel/...` | `src/pages/` | Kopieres |
| `app/kommune/[navn]/page.tsx` + `client.tsx` | `src/pages/Kommune.tsx` | Opslag på navn (case-insensitivt, URL-dekodet) eller kode, som `getKommune` |
| `app/metode/page.tsx` | `src/pages/Metode.tsx` | Omskrives: genereres fra register + manifest + markdown (afsnit 8). Datastrukturerne `INDICATOR_RATIONALES`, `SOCIAL_METHODS`, `ECO_METHODS` udtrækkes mekanisk i fase 1 |
| `app/globals.css` | `src/index.css` | Overføres |
| `netlify/functions/klimaregnskabet.mts` | udgår | Kaldes ikke af frontenden. Nøglen bliver Lovable-secret til `fetch-klimaregnskabet` |

Routes: `/`, `/kommune/:navn`, `/metode`, `/om`, `/artikel/planetaere-graenser`, `/admin/*`. Ukendt kommune -> "ikke fundet"-side med link til forsiden. Titel og meta-beskrivelse sættes pr. rute.

**URL-kompatibilitet (acceptkriterium fase 7):** alle URL'er det nuværende site udgiver skal virke på det nye. Fase 0 udtrækker listen fra `webapp/out/` (inkl. evt. `.html`-varianter og URL-encodede navne som `K%C3%B8benhavn`). Afvigelser løses med redirects.

---

## 7. Loader-kontrakt (snapshots -> KommuneData[])

1. Indlæs alle snapshot-filer via `import.meta.glob('/data/snapshots/*.csv', { query: '?raw', eager: true })` og manifestet. Ét bundle, ingen netværkskald, ingen database.
2. Parse med papaparse. Kun indikatorer med `active=true` i registret indlæses. Snapshot uden registerpost = byggefejl. Aktiv registerpost uden snapshot = byggefejl.
3. Pr. kommune (fra `registry/kommuner.ts`) bygges KommuneData efter samme regler som `loadData()` i dag (`webapp/lib/data.ts:120-218`):
   - social: `ratios[id] = ratio`, `rawValues[id] = raw` hvis ikke null
   - context: `rawValues[id] = raw` hvis ikke null
   - ecological: `rawValues[rawKey] = raw` hvis ikke null, `rawValues[ratioKey] = ratio` hvis ratioKey og ratio ikke null
4. `eco_ratios[dimensionId]` beregnes efter R7.
5. Udfyld null efter R13.
6. Kør `computeTop10Ratios` og `computeGroupRatios` (uændrede).
7. `social_avg` og `overall_avg` = null.
8. Resultatet caches i modulet.

---

## 8. Metode-siden (genereret)

Bygges af: register (navne, kilder, tabeller, enheder, grænser, transform-forklaring), manifest (dataår, sidst opdateret, hentemetode), markdown (prosa). Indhold pr. dimension: navn, beskrivelse, grænse, aggregering (worst-of/gennemsnit), dataår-interval (udledt, aldrig håndskrevet), kildehenvisninger fra `references.ts`, prosa fra `content/metode/dimensioner/<id>.md`. Pr. indikator: navn, kilde-link, DST-tabel, dataår, enhed, baseline, inverse/direkte, "sidst opdateret" og "hentemetode" (api/import/frossen) fra manifest, rationale fra `content/metode/indikatorer/<id>.md`. Generelle afsnit fra `content/metode/generelt/` i fast rækkefølge (defineret i `registry/settings.ts`).

Kontekst-indikatorer vises i en markeret "vises, men scores ikke"-sektion. `scoredInCategory=false`-indikatorer vises med markering "indgår ikke i kategoriscoren".

---

## 9. Datakilder: disposition pr. script (normativ)

Verificeret mod koden 2026-10-21. "Producent" = scriptet der skriver CSV'en i dag. Hver indikator skal have præcis én edge function eller være frossen.

### 9.1 Porteres til edge functions (method = api)

| Edge function | Erstatter | Indikatorer | Kilde |
|---|---|---|---|
| `fetch-doughnut` | `fetch_doughnut_data.py` | life_expectancy, education, disposable_income, employment, child_poverty, gini, low_income, vacant_housing, kultur_spending, civil_society | api.statbank.dk |
| `fetch-social-new` | `fetch_social_new_data.py` | crime_rate, traffic_accidents, sports_membership, library_use, sports_facilities, commute_distance, public_transport, vulnerable_children, neet | api.statbank.dk |
| `fetch-social-extra` | `fetch_social_extra_data.py` | housing_area, class_size, daycare_ratio, sports_spending, educated_staff, music_school, hospital_short, hospital_long, gp_distance, low_education | api.statbank.dk |
| `fetch-sundhed` | `fetch_sundhed_extra.py` | medicin, laegekontakt, boerneovervaeght, hjemsyg | api.statbank.dk (Excel-delene fra Sundhedsdatastyrelsen bruges ikke af aktive indikatorer og porteres ikke) |
| `fetch-udvidelse` | `fetch_udvidelse_data.py` | exam_grade, high_absence, youth_education, apprenticeship, wellbeing, poverty_relative, gender_leadership, child_notifications, housing_no_wc, housing_no_bath | api.uddannelsesstatistik.dk + api.statbank.dk |
| `fetch-ligestilling` | `fetch_ligestilling_data.py` | le_gender_gap, income_gender_gap, employment_origin_gap | api.statbank.dk |
| `fetch-demokrati` | `fetch_democracy_data.py` | voter_turnout, voter_turnout_national | api.statbank.dk |
| `fetch-klimaregnskabet` | `fetch_climate_data.py` | klimapaavirkning | klimaregnskabet.dk (API-nøgle som Lovable-secret) |
| `fetch-klimatilpasning` | `fetch_klimatilpasning_data.py` | vejr_skader | datawrapper CSV (F&P), navn-nøglet |
| `fetch-arealanvendelse` | `fetch_dst_arealanvendelse.py` | areal_intensiv, areal_bebygget | api.statbank.dk AREALDK2 |
| `fetch-vandindvinding` | `fetch_vandindvinding_data.py` | vandindvinding | api.statbank.dk VANDIND |
| `fetch-eco-dst` | `fetch_eco_new_data.py` | naer_nitrogen, naer_phosphorus, cirkularitet_waste | api.statbank.dk VANDUD m.fl. |
| `fetch-ve` | `fetch_ve_kapacitet.py` | ctx_ve_kw_per_indb, ctx_ve_sol_mw, ctx_ve_vind_mw | api.energidataservice.dk |
| `fetch-fjernvarme` | `fetch_fjernvarme_mix.py` | ctx_fjv_biomasse, ctx_fjv_affald, ctx_fjv_fossil, ctx_fjv_ren | ens.dk Excel (SheetJS fra SheetJS' egen distribution, ikke npm `xlsx`, jf. CVE-2023-30533) |
| `fetch-bolig-fossil` | `fetch_bolig_fossil.py` | bolig_fossil, ctx_fossil_direkte, ctx_fossil_via_fjv | api.statbank.dk BOL202 + fjernvarme-snapshot fra git. SKAL køres efter `fetch-fjernvarme` (læser dens snapshot, ikke en CSV i data/) |

Uafklarede punkter, der skal afgøres i fase 6, før porteringen af den pågældende funktion:
- `doughnut_scores.csv` skrives i dag af tre scripts (`fetch_doughnut_data.py`, `fetch_land_use_data.py`, `fetch_udvidelse_data.py`). Kolonne-ejerskab fastlægges, så hver indikator har én producent.
- `forurening_scores.csv` skrives af både `fetch_eco_new_data.py` og `fetch_luftforurening_data.py`. Det afklares hvem der producerer `waste_ratio`.
- `fetch_land_use_data.py` og `fetch_arealanvendelse_data.py` bruges ikke af `build_master_csv.py` og porteres ikke (bekræftes i fase 6).

### 9.2 Frosne (method = frozen, opdateres via import)

| Indikatorer | Opskrift i `tools/python/` | Transform | Hvorfor frossen |
|---|---|---|---|
| luftkvalitet_no2, luftkvalitet_pm25 | `fetch_luftforurening_data.py` | abs_limit (R16) | WFS-geodata, punkt-i-polygon |
| bio_vasentlig, bio_uerstattelig | `fetch_biodiversitet_data.py` | target_over_pct (R18), cap 300 | DCE-raster, statiske 2021-data |
| naer_landbrug | `fetch_naeringsstoffer_landbrug.py` | ref_over_raw (R19) | VP3-geodata, arealvægtning |
| overfladevand | `fetch_vp3_vandkvalitet.py` | ref_over_pct_pooled (R20), cap 300 | VP3-shapefile |
| pesticider | `fetch_pesticider_data.py` | pct_over_ref_floor (R21) | Manuel kilde (DN/GEUS) |
| nitrat | `fetch_nitrat_data.py` | abs_limit (R17) | Manuel kilde (Greenpeace/GEUS) |
| forbrug_co2 | ingen (`cba_2023_estimate.csv`, se `docs/methodology_note.md`) | cba_div3 (R5) | Statisk metodeestimat |
| cirkularitet_recycling | INGEN SCRIPT FINDES. `consumption_scores.csv` har ukendt oprindelse (kildelabel: DST LABY25) | recycling_eu_target (R4) | Oprindelse skal dokumenteres i fase 1. Kan blive api-kilde senere, men det er ny udvikling, ikke en port |

---

## 10. Edge function-kontrakt (normativ)

### 10.1 `fetch-*` (dry-run, skriver aldrig)
- Kræver gyldigt Lovable Cloud Auth-JWT. Brugerens e-mail SKAL stå i secret `ADMIN_EMAILS` (kommasepareret), ellers 403. Ingen databasetabel til admins i MVP.
- Input: `{ indicator_ids?: string[] }` (default: alle funktionens indikatorer).
- Output pr. indikator: `{ rows, data_year, reference_value, validation: { errors[], warnings[] }, diff: [{ kommune_kode, felt, gammel, ny }] }`. Diff beregnes mod snapshot-filen i git.
- Fejl i én indikator stopper ikke de øvrige. Fejl rapporteres med konkret URL/tabel og HTTP-status.
- Kilde-forespørgsler (tabel, variabler, år) står i registret (`update`-konfiguration), ikke hårdkodet.

### 10.2 Validering (fælles for fetch og import)
Fejl (blokerer commit):
- Ukendt kommunekode eller -navn (Christiansø og "000" ignoreres med advarsel)
- Dubletter
- ratio uden for 0-2000 (R14), NaN eller ikke-numeriske værdier
- Færre kommuner end `expectedCoverage`
- Pooled transform uden referenceværdi og uden tidligere reference i manifestet

Advarsler (vises, blokerer ikke):
- Ændring over 25% i ratio for over 10 kommuner
- data_year ældre end manifestets nuværende
- Reference_value genbrugt fra manifest (R22)

### 10.3 `commit-snapshot` (eneste skrivende funktion)
- Samme adgangskrav som 10.1.
- Input: godkendte rows pr. indikator + metadata (data_year, method, source_ref, reference_value).
- Validerer igen (10.2). Skriver snapshot-filer + opdateret manifest i ÉT commit via GitHub API (fine-grained token begrænset til repoets contents, gemt som secret `GITHUB_TOKEN`). Commit-besked: `data: <indikatorer> (<source_ref>, dataår <år>)`.
- Fallback hvis IT ikke tillader en GitHub-token: funktionen returnerer en zip med de ændrede filer i korrekte stier. August committer dem med GitHub Desktop. Admin-UI viser trin-for-trin-vejledning.
- Efter commit: Lovable synkroniserer, og August publicerer.

### 10.4 Kørselsrækkefølge
Admin har "Hent alt" som kalder funktionerne én ad gangen fra browseren (ikke én samlet funktion, af hensyn til tidsgrænser): `fetch-fjernvarme` før `fetch-bolig-fossil`, resten i vilkårlig rækkefølge. Samlet diff vises, og ét commit dækker alle godkendte indikatorer.

---

## 11. Admin-modul

Adgang: Lovable Cloud Auth. Den reelle beskyttelse ligger i edge functions (`ADMIN_EMAILS`). Admin-sider skjules for ikke-admins, men det er kosmetisk. Selvregistrering slås fra hvis Lovable Cloud tillader det (V6). Ellers er det harmløst, fordi funktionerne kræver allowlist.

Sider:
- **/admin**: oversigt pr. indikator med dataår, hentemetode og sidst opdateret (fra manifest). Knapper: "Hent" pr. funktion og "Hent alt".
- **/admin/import**: 1) Upload CSV/Excel eller indsæt tabel (papaparse + SheetJS, klient-side). 2) Vælg indikator, auto-mapping af kommune-, raw- og evt. ratio-kolonne. Kender de gamle `*_scores.csv`-kolonnenavne. Leveres kun raw, beregnes ratio efter registrets transform (afsnit 5). For poolede transforms spørges der efter referenceværdi (R22). 3) Validering (10.2) + diff. 4) Commit via `commit-snapshot` med method = import.
- **/admin/paritet**: kører paritetstesten (afsnit 12) i browseren, så den kan køres uden Claude.
- **/admin/log**: viser git-historikken for `data/snapshots/` via GitHub API (eller link til GitHub, hvis ingen token).

Ingen redigering af enkeltværdier (B6). Ingen redigering af metode-tekster i admin (B4: sker via Lovable-chat).

---

## 12. Paritetstest (acceptkriterium)

Tre lag, alle med 0 afvigelser (numerisk tolerance 0,01, null = null):

1. **Værdier:** `KommuneData[]` fra ny loader sammenlignes med `parity_baseline.json` (fase 0) for alle 98 kommuner og alle nøgler i ratios, top10_ratios, group_ratios, eco_ratios og rawValues.
2. **Metadata:** de genererede `INDICATORS`, `SOCIAL_CATEGORIES`, `ECOLOGICAL_DIMENSIONS`, `KOMMUNEGRUPPE` og `DOUGHNUT_*` sammenlignes felt for felt med `metadata_baseline.json` (eksport af de nuværende konstanter, fase 0). Dokumenterede afvigelser (enhedskonflikter, afsnit 3) står på en eksplicit undtagelsesliste i testen.
3. **Afledte scorer:** `computeCategoryScores` for alle kommuner og alle tre baselines sammenlignes med baseline-eksporten.

Derudover visuel kontrol af Thisted (787), København (101), Aarhus (751) og Læsø (825): donut, scorebars, vurderingsboks, alle tre baseline-stillinger og print.

Testen indgår i repoet og kører både som script og på `/admin/paritet`.

---

## 13. Workspace, ejerskab og arbejdsform

### 13.1 Hvor bygges der
Fordi alt kan genskabes fra git (B3), er workspace-valget primært et spørgsmål om databehandleraftale og hvem der har adgang, ikke om data.

**Standardvej (anbefalet, B):** fase 2-6 bygges i Augusts private Lovable-workspace, hvor Claude har direkte adgang. Kun offentlige data og en testkonto uden persondata (B12). I fase 7 overføres projektet til det kommunale workspace. Virker Lovables overdragelse ikke (V7), oprettes et nyt kommunalt projekt fra repoet. Fordi alt ligger i git, mistes intet.

**Alternativ (A):** byg direkte i det kommunale workspace. Bruges hvis IT afviser privat byggeri. Claude arbejder så via GitHub (13.2). Faseplanen er den samme.

Afklares inden fase 2 (August):
- Lovable: kan et projekt flyttes fra et privat til et kommunalt Business/Enterprise-workspace med git sync bevaret? Bevares EU-region?
- IT: findes der (eller kommer der) et kommunalt Business/Enterprise-workspace? Accepteres privat byggeri af fase 2-6 med offentlige data? Må projektet synkronisere med et GitHub-repo, og må `commit-snapshot` få en GitHub-token?

### 13.2 Når Claude ikke har adgang til det kommunale workspace
Det er et varigt vilkår efter go-live.
1. **Foretrukket:** det kommunale projekt synkroniserer med et GitHub-repo, Claude har skriveadgang til. Claude pusher kode, register, markdown og snapshots. Lovable synkroniserer. August publicerer.
2. **Fallback:** Claude skriver færdige promptpakker, som August indsætter i Lovables chat. Lovables svar/diff sendes retur til Claude.
3. Paritetstesten og datahentning kan køres af August alene fra admin.
4. Opdatering af frosne kilder: en Claude-session kører Python-opskriften fra `tools/python/` og producerer en importfil, som August importerer i admin.

### 13.3 Workspace-indstillinger (kommunalt)
Fra Lovables vejledning til offentlig sektor: publiceringsblokering ved kritiske sikkerhedsfund slås til, EU-region bekræftes ved oprettelse, deling og connectors sættes restriktivt, sikkerhedsscanning planlægges månedligt.

---

## 14. Verifikationspunkter (fase 2-spike, FØR videre byggeri)

Hvert punkt verificeres i et testprojekt og resultatet noteres her. Et negativt svar udløser fallbacken.

| # | Spørgsmål | Fallback hvis nej |
|---|---|---|
| V1 | Kan Lovable oprette projektet med prerendering/SSR? | Vite SPA (accepteret SEO-trade-off) |
| V2 | Kan edge functions i Lovable Cloud lave udgående HTTP til statbank, EDS, uddannelsesstatistik, ens.dk, datawrapper og klimaregnskabet, og læse secrets? | Den pågældende kilde bliver frossen |
| V3 | Kan frontend og edge functions importere samme `registry/`-filer? | Registret placeres i `supabase/functions/_shared/registry/`, og frontend importerer derfra via alias |
| V4 | Kan edge functions verificere Auth-JWT og læse brugerens e-mail? | Admin-allowlist via Lovable Cloud-tabel med security definer-funktion `is_admin()` (aldrig en policy der slår op i sin egen tabel) |
| V5 | Deployes ændringer i `supabase/functions/`, der pushes via GitHub, automatisk? | August beder Lovables agent deploye efter push (promptpakke) |
| V6 | Kan selvregistrering slås fra? | Harmløst pga. allowlist (11) |
| V7 | Kan projektet flyttes fra privat til kommunalt workspace? | Nyt kommunalt projekt fra repoet |
| V8 | Rækker edge functions' tidsgrænse til den største kilde (`fetch-udvidelse`)? | Funktionen deles op pr. indikatorgruppe |
| V9 | Kan Vite bundle `data/snapshots/*.csv` via `import.meta.glob` i Lovables build? | Snapshots lægges i `public/data/` og hentes ved opstart (én samlet fil) |

---

## 15. Faseplan

Bindende rækkefølge. En fase starter først når den forriges acceptkriterium er opfyldt.

| Fase | Hvor | Indhold | Acceptkriterium | Model |
|---|---|---|---|---|
| 0 | doughnut-repo | Eksportér `parity_baseline.json` (værdier + kategoriscorer, alle baselines), `metadata_baseline.json` (alle konstanter) og URL-liste fra `webapp/out/` | Filerne findes, 98 kommuner | Sonnet |
| 1 | doughnut-repo, `migration/` | Engangskonvertering (`tools/migration/`): master-CSV -> snapshots + manifest (method=frozen), shared.ts + build-lister -> `registry/`, metode-datastrukturer -> markdown (mekanisk), dimensionsårstal udgår (udledes). Fase 1-rapport med konflikter og afvigelser. Oprindelsen af `consumption_scores.csv` dokumenteres | Rundtur: snapshots samlet = master-CSV minus `_dim_`-rækker, række for række. August har skimmet rapporten | Opus |
| 2 | Privat Lovable (eller kommunalt, 13.1) | Opret projekt (EU-region), git sync, spike V1-V9, flyt indholdet fra `migration/` ind i det nye repo, port app (afsnit 6) | V-punkter noteret i afsnit 14. App bygger og viser forside + én kommuneside | Opus (spike), Sonnet (port) |
| 3 | Lovable | Loader (afsnit 7), routing, paritetstest (afsnit 12) | 0 afvigelser i alle tre lag | Opus |
| 4 | Lovable | Metode-side (afsnit 8) med pladsholdere | August godkender. Ingen håndskrevne årstal/kilder tilbage i markdown | Sonnet |
| 5 | Lovable | Admin: auth, allowlist, import, `commit-snapshot`, paritetsside | August importerer en `*_scores.csv`, ser diff, committer, og ændringen ses efter publicering. Ikke-admin afvises af funktionerne | Sonnet |
| 6 | Lovable | Edge functions (9.1), én ad gangen. Start med `fetch-doughnut` som skabelon | Hver funktion i dry-run giver værdier identiske med nuværende snapshot (eller forklarede afvigelser pga. nyere kildedata) | Opus (skabelon, bolig-fossil), Sonnet (resten) |
| 7 | Kommunalt workspace | Overførsel (V7 eller nyt projekt fra repo), secrets genoprettes, domæne, URL-kompatibilitet, workspace-indstillinger (13.3) | Paritetstest grøn i kommunalt workspace. Alle URL'er fra fase 0 virker. August godkender go-live | Sonnet |
| 8 | Kommunalt workspace | Bruger-features | Specificeres separat. Indfører databasetabeller, RLS med `is_admin()`-mønster, og persondata kun her (B12) | - |

Efter fase 7 arkiveres doughnut-repoet (B13). Netlify-sitet fryses, slettes ikke.

---

## 16. Kendte fælder

1. Farvelogik er OMVENDT mellem social og eco (R11).
2. Kun `forurening` er gennemsnits-dimension (R7).
3. `forbrug_co2` og `vejr_skader` matcher på navn. Christiansø filtreres.
4. absoluteScore-indikatorer omskaleres aldrig af baseline-toggle.
5. `fetch-fjernvarme` før `fetch-bolig-fossil`.
6. null vs. undefined i eco_ratios er semantisk (R13).
7. Kommunenavne med æøå og bindestreg: URL-dekodning og case-insensitivt match.
8. Ingen kommune er grøn på bolig_fossil. Det er korrekt.
9. Pesticid-ratio har gulv på 101 for kommuner med mindst én overskridelse (R21). Det er bevidst, ikke en fejl.
10. Biodiversitet med pct = 0 giver 999, som cappes til 300 (R18 + R6).
11. `housing_no_wc` og `housing_no_bath` har data, men indgår ikke i nogen kategoriscore i dag (B16). Afklares med August efter migreringen, ikke under.
12. Python-scripts og data-CSV'er må ikke slettes under migreringen (B14).

---

## 17. Risici og accepterede trade-offs

| Risiko | Håndtering |
|---|---|
| Talregression | Paritetstest i tre lag, 0-tolerance (12) |
| Kilder ændrer sig (DST-revisioner, døde links) | Dry-run + diff + validering. Fejl falder tilbage til eksisterende snapshot. Forvent årligt vedligehold |
| Lovable-funktioner virker anderledes end antaget | Spike V1-V9 i fase 2, før der bygges videre |
| Overdragelse mellem workspaces fejler | Irrelevant for data (B3). Nyt projekt fra repo |
| IT afviser GitHub-token | Zip-fallback + GitHub Desktop (10.3) |
| SEO ved SPA | Accepteret hvis V1 er negativ. Titel/meta pr. rute |
| Lovable-credits (byg + hver tekstrettelse via chat) | Store, præcise beskeder ud fra denne spec. Privat i fase 2-6 |
| Publicering kræver manuelt klik efter data-commit | Accepteret. Svarer til i dag |

---

## 18. Sporbarhed: review-fund (2026-10-21) og hvor de er løst

| # | Fund | Løst i |
|---|---|---|
| 1 | Lovable Cloud giver ikke dashboard eller service role | B2, B3 (ingen database til data), V4, V6 |
| 2 | Supabase-API returnerer max 1.000 rækker (7.349 rækker) | B3: ingen database, data bundles (7, V9) |
| 3 | RLS-rekursion og åbne edge functions | Allowlist i funktioner (10.1). `is_admin()`-mønster for fase 8 |
| 4 | Paritetstest fangede ikke metadata/kategori-medlemskab | `scoredInCategory` (4.3), paritet lag 2 og 3 (12) |
| 5 | Compute-funktioner vs. fjernede konstanter | Registret er statisk kode, konstanterne består (4.3) |
| 6 | Dataår opdateres ikke ved hentning | B5, manifest (4.2), udledte dimensionsår (3, 8) |
| 7 | Metode-skema for tyndt | `references.ts`, generelle afsnit, markdown pr. id (2, 4.4, 8) |
| 8 | Import virkede ikke med råværdier | R16-R22, transform-typer (5), reference_value (4.2) |
| 9 | Fejl i kildedisposition | Komplet tabel (9), uafklarede punkter listet, genanvendelse frossen |
| 10 | Enhedskonflikter | Konfliktregel (3) + undtagelsesliste (12) |
| 11 | Uklar repo-strategi | B13, mappestruktur (2) |
| 12 | Gamle URL'er | Acceptkriterium fase 7, URL-liste i fase 0 (6) |
| 13 | Ikke-atomisk import | Ét git-commit pr. opdatering (10.3) |
| 14 | npm `xlsx` CVE | SheetJS' egen distribution (9.1) |
| 15 | Free tier pauser | Ikke relevant: det offentlige site bruger ingen database |
| 16 | SPA/SSR ukontrolleret | V1 |

---

## 19. Vedligehold af dette dokument

Opdateres når en fase afsluttes (acceptkriterium markeres med dato), når et V-punkt er afklaret (resultat noteres i afsnit 14), eller når en låst beslutning ændres af August (ny række i beslutningsloggen med begrundelse). Implementerende AI'er refererer til afsnitsnumre i commits, fx "implementerer afsnit 7, R7".
