# Doughnut Kommune Tool - Data

Datasæt over alle 98 danske kommuners performance på Doughnut Economics-rammen: socialt fundament og økologisk loft.

## Hovedfilen: `master_indicators.csv`

Dette er den **konsoliderede master-fil** som webapp'en læser fra. Genereres af `scripts/build_master_csv.py` ved at samle alle rådata-CSV'er.

**Format: long format (tidy data).** Én række pr. (kommune × indikator).

### Kolonner

| Kolonne | Beskrivelse | Eksempel |
|---|---|---|
| `kommune_kode` | DST-kommunekode (3 cifre, zero-padded) | `787` |
| `kommune_navn` | Kommunenavn | `Thisted` |
| `indicator_id` | Indikator-id (matcher `INDICATORS` i webapp). Specielle id'er der starter med `_dim_` er worst-of dimension-aggregater. | `life_expectancy`, `_dim_luftkvalitet` |
| `ratio` | Score 100 = grænseværdi (sociale: gennemsnit; økologiske: planetær grænse) | `98.9` |
| `raw_value` | Faktisk måleværdi i sin enhed | `80.4` |
| `unit` | Enhed for `raw_value` | `år`, `µg/m³`, `%` |
| `data_year` | År for senest data | `2023` |
| `source` | Kort kildebeskrivelse | `DST HISBK` |
| `category` | `social`, `ecological`, eller `ecological_dimension` (kun for `_dim_*` rækker) | `social` |
| `dimension` | Hvilken kategori/dimension indikatoren hører til | `sundhed`, `luftkvalitet` |

### Scoringskonventioner

**Sociale indikatorer:**
- `ratio = 100` = landsgennemsnit
- `ratio > 100` = bedre end gennemsnit
- `ratio < 100` = dårligere end gennemsnit
- Inverterede indikatorer (kriminalitet, fattigdom mv.) er allerede vendt - høj ratio = god performance

**Økologiske indikatorer:**
- `ratio = 100` = på den planetære grænse
- `ratio < 100` = inden for grænsen (godt)
- `ratio > 100` = overshoot (rødt)

**Dimension-aggregater (`_dim_*` rækker):**
- Multi-indikator dimensioner (luftkvalitet, næringsstoffer, cirkularitet) bruger **worst-of** (max ratio) - planetary boundary-logik: hvis bare én sub-grænse er overskredet, er dimensionen overskredet.
- Single-indikator dimensioner (klimapåvirkning, biodiversitet, forbrug_co2) får dimension-score = sub-indikatorens ratio.

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
- **Kun 42 af platformens indikatorer har historik.** Resten vises med et skraveret felt (`ingen`). DCE-luftkort, VP3-vandplaner og UVM-data (kræver MitID) findes ikke som årlige tidsserier.

Genereres af `scripts/fetch_trend_history.py` → `scripts/build_trends_csv.py`. **Skal genberegnes sammen med `master_indicators.csv`**, ellers kan pil og tal komme til at høre til forskellige årgange.

## Rådata-CSV'er (debug/transparens)

De 21 individuelle CSV-filer (`luftforurening_scores.csv`, `naeringsstoffer_scores.csv` mv.) er bevaret som **rådata-spor**. De genereres af deres respektive `scripts/fetch_*.py`-scripts og gør det muligt at debugge data-pipelinen tilbage til kilden.

Webapp'en læser **ikke** længere fra disse direkte - kun fra `master_indicators.csv`.

## Inaktive dimensioner

Følgende doughnut-dimensioner har endnu ingen kommunefordelt data og indgår ikke i master-filen:

- **Forurening (novel entities)** - PFAS, mikroplast, pesticider på kommuneniveau er ikke tilgængeligt
- **Vand** - tidligere metode er fravalgt som ikke fyldestgørende
- **Arealanvendelse** - ingen valideret kommunal datakilde endnu
- **Klimatilpasning** (social) - oversvømmelsesrisiko mv. afventer data

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
