# migration/ - værktøjer til Lovable-migreringen

Hører til `docs/lovable-migration-spec.md` (fase 0). Intet her påvirker det nuværende site: Netlify bygger kun `webapp/`, og scriptet ændrer ikke en eneste fil udenfor `migration/baseline/`.

## Hvad er det

Et "fotografi" af det nuværende site, taget ved at køre den nuværende kode (`webapp/lib/data.ts` og `shared.ts`, uændret). Det nye system sammenlignes med fotografiet tal for tal (spec afsnit 12) og skal ramme det med 0 afvigelser.

| Fil | Indhold |
|---|---|
| `baseline/parity_baseline.json` | For alle 98 kommuner: `ratios`, `top10_ratios`, `group_ratios`, `eco_ratios`, `rawValues`, kommunegruppe og kategoriscorer i alle tre baselines (`avg`, `top10`, `kommunegruppe`). Én kommune pr. linje |
| `baseline/metadata_baseline.json` | `INDICATORS`, `SOCIAL_CATEGORIES`, `ECOLOGICAL_DIMENSIONS`, `KOMMUNEGRUPPE(_NAVNE)`, `DOUGHNUT_*`, de afledte baselineTypes (R12) og `eco_raw_key_map` (17 poster, læst ud af `data.ts`, hvor den ikke er eksporteret) |
| `baseline/url_liste.txt` | De 102 adresser sitet udgiver (4 sider + 98 kommuner), URL-encodede som sitets egne links, fx `/kommune/K%C3%B8benhavn` |
| `export_baseline.mjs` | Eksportscriptet |
| `register-ts.mjs`, `ts-resolve-hook.mjs` | Lader Node læse `webapp/lib/*.ts` uden at ændre dem (filerne importerer `./shared` uden endelse) |

Scorerne pr. indikator inde i en kategori gemmes ikke to gange: de er identiske med `ratios`/`top10_ratios`/`group_ratios` (verificeret, 0 afvigelser over 14.112 værdier). Kategorien gemmer kun `score`, `indicatorCount` og `hasData`.

## Kør

Fra repo-roden. Kræver Node 22.18 eller nyere. Ingen installation.

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

Skal `data/master_indicators.csv` ændres, før fase 1 er afsluttet, så kør eksporten igen, så baseline og fase 1-konverteringen bygger på samme version. Kontrol: `sha256sum data/master_indicators.csv`.
