# Doughnut Kommune Tool - Data

Datasæt over alle 98 danske kommuners performance på Doughnut Economics-rammen: socialt fundament og økologisk loft.

## Indikatorregistret: `indikatorer.json`

Den ene liste over indikatorer, sociale kategorier og økologiske dimensioner. `scripts/build_master_csv.py` bestemmer ud fra den hvilke CSV-kolonner der læses, og webappen (`webapp/lib/shared.ts`) viser indikatorerne ud fra samme fil. Felterne er forklaret i filens `_om`-nøgle. En ny indikator er én post her plus et fetch-script, se CLAUDE.md "Tilføj en ny indikator".

## `noegletal.json`

Reference, dækning (antal kommuner med værdi) og dataår pr. indikator, skrevet af `build_master_csv.py` sammen med master. Webappen udfylder tal i tekster herfra (pladsholdere som `{ref:pesticider:1}`), og buildet stopper hvis filen ikke passer med master. Ret den ikke i hånden.

## `kommuner.json`

De 98 kommuner med DST-kode, navn og kommunegruppe (DST KOMMUNEGRUPPER_V1_2018). Fetch-scripterne læser den via `scripts/kommuner.py`, og webappen bruger grupperne til kommunegruppe-baselinen. Christiansø (411) er ikke med. Alle rådata-CSV'er er nøglet på `kommune_kode`; de to kilder der kun har navne (`cba_2023_estimate.csv`, `klimatilpasning_scores.csv`) har fået koden slået op herfra.

## Hovedfilen: `master_indicators.csv`

Dette er den **konsoliderede master-fil** som webapp'en læser fra. Genereres af `scripts/build_master_csv.py` ved at samle alle rådata-CSV'er.

**Format: long format (tidy data).** Én række pr. (kommune × indikator).

### Kolonner

| Kolonne | Beskrivelse | Eksempel |
|---|---|---|
| `kommune_kode` | DST-kommunekode (3 cifre, zero-padded) | `787` |
| `kommune_navn` | Kommunenavn | `Thisted` |
| `indicator_id` | Indikator-id (matcher `id` i `indikatorer.json`). Specielle id'er der starter med `_dim_` er økologiske dimensionsscorer (worst-of eller gennemsnit). | `life_expectancy`, `_dim_luftkvalitet` |
| `ratio` | Score 100 = grænseværdi (sociale: gennemsnit; økologiske: planetær grænse) | `98.9` |
| `raw_value` | Faktisk måleværdi i sin enhed | `80.4` |
| `unit` | Enhed for `raw_value` | `år`, `µg/m³`, `%` |
| `data_year` | År for senest data | `2023` |
| `source` | Kort kildebeskrivelse | `DST HISBK` |
| `category` | `social`, `ecological`, `context` (vises, scores ikke) eller `ecological_dimension` (kun for `_dim_*` rækker) | `social` |
| `dimension` | Hvilken kategori/dimension indikatoren hører til | `sundhed`, `luftkvalitet` |
| `reference` | Værdien `ratio` er målt mod, i råværdiens enhed: målet, kommunegennemsnittet eller landstallet (se `reference` i `indikatorer.json`). Tom for kontekst- og `_dim_*`-rækker | `81.6`, `95.0` |

### Scoringskonventioner

**Sociale indikatorer:**
- `ratio = 100` = landsgennemsnit (undtagen `education` og `bolig_fossil`, der scores mod et fast mål). Masteren gemmer altid ratio mod landsgennemsnittet; webappens baseline-toggle (kommunegruppe/top 10) omskalerer ved visning
- `ratio > 100` = bedre end gennemsnit
- `ratio < 100` = dårligere end gennemsnit
- Inverterede indikatorer (kriminalitet, fattigdom mv.) vendes af `build_master_csv.py` (`ratio = reference / raw × 100`) - høj ratio = god performance. Alle ratios beregnes dér ud fra `raw_value` og `reference`, ikke i fetch-scripterne

**Økologiske indikatorer:**
- `ratio = 100` = på grænsen: en absolut grænse (WHO, EU-mål, Paris-budget, 6 mg/L nitrat) eller landsgennemsnittet for de relative sub-indikatorer (fx næringsstoffer, vandindvinding, arealanvendelse, affald, pesticider)
- `ratio < 100` = inden for grænsen (godt)
- `ratio > 100` = overshoot (rødt)

**Dimension-aggregater (`_dim_*` rækker):**
- Multi-indikator dimensioner (klimapåvirkning, luftkvalitet, næringsstoffer, arealanvendelse, biodiversitet) bruger **worst-of** (max ratio) - planetary boundary-logik: hvis bare én sub-grænse er overskredet, er dimensionen overskredet.
- Forurening er eneste undtagelse og bruger gennemsnit af sine fire sub-indikatorer.
- Vand er single-indikator og får dimension-score = sub-indikatorens ratio.

### Eksempel: Pandas-import

```python
import pandas as pd

df = pd.read_csv("master_indicators.csv")

# Hvad er Thisteds score på luftkvalitet?
df.query("kommune_navn == 'Thisted' and indicator_id == '_dim_luftkvalitet'")

# Hvilke kommuner har værst forbrugsbaseret CO2?
df.query("indicator_id == 'forbrug_co2'").nlargest(10, 'ratio')

# Sammenlign alle dimensioner for én kommune
df.query("kommune_navn == 'København' and indicator_id.str.startswith('_dim_')")[
    ["dimension", "ratio"]
]
```

## Retningsvisning: `trend_indicators.csv`

Viser hvilken **vej** en kommune bevæger sig, ikke kun hvor den ligger. Én række pr. (kommune × indikator), plus `_dim_*`-rækker med én samlet retning pr. dimension/kategori.

| Kolonne | Beskrivelse | Eksempel |
|---|---|---|
| `kommune_kode` | DST-kommunekode | `787` |
| `indicator_id` | Matcher `master_indicators.csv`. `_dim_*` = dimensions-aggregat | `gini`, `_dim_sundhed` |
| `periode_start` / `periode_slut` | Sammenlignede perioder. Treårsgennemsnit i begge ender når serien har mindst 6 år, så et enkelt ekstremår ikke afgør billedet | `2010-2012`, `2022-2024` |
| `vaerdi_start` / `vaerdi_slut` | Råværdier i indikatorens egen enhed. Tomme for `_dim_*` (ingen fælles enhed) | `31.0`, `59.0` |
| `pct` | Procentvis ændring. For `_dim_*`: gennemsnitlig **målrettet** ændring (positiv = mod målet) | `+29.54` |
| `retning` | Se klasser nedenfor | `forkert` |
| `n_aar` | Antal år i serien | `15` |
| `noegle_indikator` | Kun på `_dim_*`: hvilken sub-indikator retningen kommer fra | `naer_nitrogen` |

### Retningsklasser

| Klasse | Betydning |
|---|---|
| `rigtig` | Mod målet, mindst lige så hurtigt som medianen af alle 98 kommuner |
| `tempo` | Mod målet, men langsommere end medianen |
| `stagneret` | Under 1 % ændring, eller under 1 procentpoint når niveauet er over 10 % |
| `forkert` | Væk fra målet |
| `kontekst` | Måles, men har ingen ønsket retning |
| `ingen` | Ingen tidsserie - kan ikke vurderes |

### Metode (vigtigt)

- **Retningen beregnes på råværdier, aldrig på ratio.** Ratio er relativ til en baseline, og platformen har en baseline-toggle (avg/top10/gruppe). En ratio-baseret pil ville skifte retning når brugeren skifter baseline.
- **Øko-dimensioner bruger worst-of:** pilen følger den sub-indikator der bestemmer dimensionens score (højeste ratio). Undtagelse: Forurening bruger gennemsnit, ligesom i scoren.
- **Ingen fallback.** Har den score-afgørende sub-indikator ingen tidsserie, får dimensionen ingen pil. Ellers ville pilen beskrive noget andet end tallet ved siden af.
- **53 af de 66 scorede indikatorer har historik** (sep. 2026). De 13 uden vises med et skraveret felt (`ingen`): DCE-luftkort, bioscore, VP3-vandplaner, Jupiter-analyser, forbrugsbaseret CO₂, forsikringsskader og fossil opvarmning findes ikke som årlige tidsserier pr. kommune, `public_transport` beregnes fra køreplaner, og Rejseplanens arkiv går kun tilbage til december 2025, og `sport_tilskuer` bruger begge tilgængelige år i selve målet.

Genereres af `scripts/fetch_trend_history.py` → `scripts/build_trends_csv.py`. **Skal genberegnes sammen med `master_indicators.csv`**, ellers kan pil og tal komme til at høre til forskellige årgange.

## Rådata-CSV'er (debug/transparens)

De individuelle CSV-filer (`luftforurening_scores.csv`, `naeringsstoffer_scores.csv` mv.) er bevaret som **rådata-spor**. De genereres af deres respektive `scripts/fetch_*.py`-scripts og gør det muligt at debugge data-pipelinen tilbage til kilden.

### `kulturvaner_scores.csv`

Fra DST's kulturvaneundersøgelse (KV2GEO), hentet af `scripts/fetch_kulturvaner.py`.
Kolonner: `kommune_kode`, `sport_tilskuer_pct`, `sport_tilskuer_ratio`.

**Dækker kun 76 af 98 kommuner.** DST undertrykker tal hvor stikprøven er for
lille, og hullet er systematisk: de 22 kommuner uden tal har median ca. 24.000
indbyggere mod ca. 53.000 for dem med tal. Værdien er et toårigt gennemsnit af
2024 og 2025. Landsgennemsnittet kommer fra tabellens eget landstal (kode 000).

### `sundhedsprofil_scores.csv` og `sundhedsprofil_historik.csv`

Fra Den Nationale Sundhedsprofil, hentet af `scripts/fetch_sundhedsprofil.py`.

`sundhedsprofil_scores.csv` - seneste bølge (2025), én række pr. kommune:

| Kolonne | Indhold |
|---|---|
| `kommune_kode` | 3-cifret kommunekode |
| `<id>_pct` | Råandel i procent, som databasen viser den |
| `<id>_ratio` | Ratio mod befolkningsvægtet landsgennemsnit, cappet ved 150 |

`sundhedsprofil_historik.csv` - alle fem bølger 2010-2025 i long format
(`kommune_kode, indicator_id, aar, raw_value`). Kun de scorede indikatorers
2017- og 2025-tal skrives videre til `trend_history_raw.csv` - se punkt 23 i
CLAUDE.md for hvorfor vinduet ikke er hele serien.

Ni indikatorer hentes: `selvvurderet_helbred`, `mentalt_helbred`, `rygning`,
`alkohol`, `fysisk_aktivitet`, `kost`, `svaer_overvaegt`, `ensomhed`,
`social_stoette`.
`fysisk_aktivitet` scores ikke (r = 0,90 med `svaer_overvaegt`), men bevares i
filen.

**Landsgennemsnittet er beregnet af os**, som et befolkningsvægtet gennemsnit af
de 98 kommuneandele (DST FOLK1A, 16+). Databasen udstiller ikke et landstal pr.
kommunetabel. Tallet afviger derfor en anelse fra SIF's eget vægtede
landsestimat, og det skal fremgå ved formidling.

Webapp'en læser **ikke** længere fra disse direkte - kun fra `master_indicators.csv`.

### `offentlig_transport_scores.csv` og `befolkning_1km_2021_dk.csv`

Adgang til offentlig transport pr. kommune (verdensmål 11.2.1), genskabt fra
åbne data af `scripts/fetch_offentlig_transport.py` med DST's metode. Kilden til
`public_transport` fra sep. 2026; DST's LABY49 findes kun pr. kommunegruppe og
bruges kun til validering. Metode og validering:
`docs/offentlig-transport-genskabt.md`.

`offentlig_transport_scores.csv`: `public_transport_raw` er andelen af
befolkningen med mindst 10 afgange i timen inden for gåafstand,
`public_transport_ref` landstallet for Danmark som helhed og
`public_transport_ratio` scriptets egen ratio (kun krydstjek). `andel_middel`,
`andel_lavt` og `andel_intet` er de øvrige serviceniveauer. `gtfs_dato` er den
hverdag køreplanen er talt på.

`befolkning_1km_2021_dk.csv`: de danske celler fra Eurostats Census 2021
population grid (`n_km`, `e_km` er cellens nederste venstre hjørne i
ETRS89-LAEA, km). Bruges til at vægte adresser med registrerede beboere.
© European Union.

## Inaktive dimensioner

Ingen (sep. 2026). Alle 13 sociale kategorier og 7 økologiske dimensioner har data. Kendte huller inden for dimensionerne: PFAS og mikroplast findes ikke på kommuneniveau (Forurening), og Klimatilpasning måles kun på realiserede forsikringsskader, ikke på fremtidig oversvømmelsesrisiko.

## Driftsregel ved opdatering

1. Kør relevant `scripts/fetch_*.py` for at opdatere rådata-CSV
2. Kør `python3 scripts/build_master_csv.py` for at regenerere master-filen
3. Commit og push - Netlify deployer automatisk

## Licens og citation

Data er sammensat af offentligt tilgængelige kilder (primært Danmarks Statistik, DCE/AU, Klimaregnskabet.dk, Vandområdeplaner og forskningspublikationer). Brug følger kildedataens licens.

Foreslået citation:
> Krogh, A. (2026). *Danmarks 98 Doughnuts: Doughnut Economics-platform for danske kommuner*. [URL]

## Kontakt

Platformen vedligeholdes af projektleder August Krogh, klimateamet, Thisted Kommune.
Feedback og fejlrapporter er velkomne.
