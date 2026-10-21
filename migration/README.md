# migration/ - værktøjer til Lovable-migreringen

Hører til `docs/lovable-migration-spec.md` (fase 0 og 1). Intet her påvirker det nuværende site: Netlify bygger kun `webapp/`, og scriptene skriver kun i `migration/`.

| Mappe | Fase | Indhold |
|---|---|---|
| `baseline/` | 0 | "Fotografiet" af det nuværende site (facit) |
| `fase1/` | 1 | `convert.mjs` (konvertering), `verify.mjs` (verifikation), `lib.mjs`, **`rapport.md`** |
| `lovable/` | 1 | Frøet til det nye Lovable-repo: `data/snapshots/`, `registry/`, `content/metode/`. Flyttes ind i fase 2 |

## Fase 1: kør

Fra repo-roden, efter fase 0:

```
node --disable-warning=ExperimentalWarning --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --import ./migration/register-ts.mjs migration/fase1/convert.mjs
node --disable-warning=ExperimentalWarning --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --import ./migration/register-ts.mjs migration/fase1/verify.mjs
```

`convert.mjs` afviser at køre, hvis `data/master_indicators.csv`, `webapp/lib/shared.ts` eller `webapp/lib/data.ts` er ændret siden fase 0-baselinen. Den overskriver kun de genererede filer i `migration/lovable/`; de håndskrevne (`registry/types.ts`, `transforms.ts`, `legacy.ts`, `content/metode/generelt/`, `content/metode/README.md`) røres ikke. `verify.mjs` skal slutte med "A-E: 0 fejl". Resultater og fund: `fase1/rapport.md`.

Efter fase 1 er filerne i `migration/lovable/` kilden. Konverteringen køres kun igen, hvis data på det gamle site ændres før fase 2. I så fald køres fase 0 først.

## Fase 0: hvad er det

Et "fotografi" af det nuværende site, taget ved at køre den nuværende kode (`webapp/lib/data.ts` og `shared.ts`, uændret). Det nye system sammenlignes med fotografiet tal for tal (spec afsnit 12) og skal ramme det med 0 afvigelser.

| Fil | Indhold |
|---|---|
| `baseline/parity_baseline.json` | For alle 98 kommuner: `ratios`, `top10_ratios`, `group_ratios`, `eco_ratios`, `rawValues`, kommunegruppe og kategoriscorer i alle tre baselines (`avg`, `top10`, `kommunegruppe`). Én kommune pr. linje |
| `baseline/metadata_baseline.json` | `INDICATORS`, `SOCIAL_CATEGORIES`, `ECOLOGICAL_DIMENSIONS`, `KOMMUNEGRUPPE(_NAVNE)`, `DOUGHNUT_*`, de afledte baselineTypes (R12) og `eco_raw_key_map` (17 poster, læst ud af `data.ts`, hvor den ikke er eksporteret) |
| `baseline/url_liste.txt` | De 102 adresser sitet udgiver (4 sider + 98 kommuner), URL-encodede som sitets egne links, fx `/kommune/K%C3%B8benhavn` |
| `export_baseline.mjs` | Eksportscriptet |
| `register-ts.mjs`, `ts-resolve-hook.mjs` | Lader Node læse `webapp/lib/*.ts` uden at ændre dem (filerne importerer `./shared` uden endelse) |

Scorerne pr. indikator inde i en kategori gemmes ikke to gange: de er identiske med `ratios`/`top10_ratios`/`group_ratios` (verificeret, 0 afvigelser over 14.112 værdier). Kategorien gemmer kun `score`, `indicatorCount` og `hasData`.

## Fase 0: kør

Fra repo-roden. Kræver Node 22.18 eller nyere og python3 (fase 1 læser lister fra `scripts/build_master_csv.py`). Ingen installation.

```
node --disable-warning=ExperimentalWarning --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --import ./migration/register-ts.mjs migration/export_baseline.mjs
```

Output indeholder ingen tidsstempler: samme input giver byte-identiske filer (testet på tværs af to kørsler og to arbejdsmapper).

## Hvad scriptet tjekker, før det skriver noget

Afvises eksporten, skrives ingen filer, og scriptet slutter med fejlkode 1.

- Præcis 98 kommuner, og de er de samme som i `KOMMUNEGRUPPE`.
- Ingen `undefined` eller ikke-endelige tal (JSON ville tabe nøglen uden fejl).
- Afstemning mod `data/master_indicators.csv`: antal ratios, rawValues og dimensionsscorer i eksporten skal være lig antallet i CSV'en. Fanger at nuværende indlæsning stille taber data, fx en eco-indikator der mangler i `ECO_RAW_KEY_MAP`.
- Ingen dubletter, ingen ukendte kategorier og ingen rækker med forkert antal kolonner i CSV'en.
- `ECO_RAW_KEY_MAP` dækker præcis de nøgler, `ECOLOGICAL_DIMENSIONS.subIndicators` peger på.
- URL-listen fra koden er identisk med de sider, der ligger i `webapp/out/`.

Afstemningen er testet negativt: en planlagt dublet og en ukendt eco-indikator blev afvist med fire præcise fejl.

## Datafrysning

Baseline passer kun til den master-CSV, den er lavet fra. Hashen står i feltet `source.master_indicators_csv_sha256` i begge JSON-filer (fotografi taget 2026-10-21).

Skal `data/master_indicators.csv` ændres før fase 2, så kør fase 0 og derefter fase 1 igen, så baseline og konvertering bygger på samme version. `convert.mjs` nægter at køre, hvis de ikke passer sammen.
