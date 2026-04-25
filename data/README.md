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
