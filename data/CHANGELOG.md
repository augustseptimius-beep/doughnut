# Data CHANGELOG

Log over større ændringer i datapipeline og master-fil.

## 2026-08-12

- **`bolig_fossil` skiftet fra DST BOL202 (personer) til DST BYGB40 (opvarmet areal i m²).** Varmebehov skalerer med areal, ikke med antal beboere: en oliefyret gård med to beboere fylder mere i varmeregnskabet end tre lejligheder med seks beboere, men talte tidligere mindre.
  - **Konsekvens er beskeden:** korrelation 0,998 med den gamle metode, median rangeringsflytning 1 plads. Men den retter en systematisk skævhed: landkommuner fremstod ca. 1,7 pct.point for pænt, storbykommuner kun 0,1. Landsgennemsnittet går fra 29,3% til 30,4% fossil. Thisted: score 83,0 → 80,8.
  - **Afgrænset til helårsbeboelse** (BYGB40 ANVEND 110-190). BYGB40 dækker som udgangspunkt ALLE bygninger, inkl. fabrikker, avlsbygninger, garager og udhuse. Uden afgrænsning ville indikatoren måle kommunens samlede bygningsmasse i stedet for boliger (gennemsnit ville stige til 33,6% og median rangeringsflytning til 4 pladser).
  - **Fanger nu også oliekaminer** (BYGB40 OPVARM 6 "Ovne med olie eller petroleum"), som BOL202 ikke havde som separat kategori.
  - **Fritidsboliger tilføjet som kontekst** (`ctx_fritid_fossil`, `ctx_fritid_andel`), ikke som scoret indikator. Begrundelse: sommerhuse er typisk elopvarmede og har median ca. 7% fossilandel mod helårsboligernes ca. 20%. Hvis de indgik i scoren, ville sommerhuskommuner (Fanø 54% af boligarealet, Odsherred 50%, Gribskov 38%) fremstå kunstigt bedre på et mål der handler om husstandes varmeregninger - samme fejltype som den allerede fjernede `car_access`.
- **Retningsvisning (trends)** indført: `data/trend_indicators.csv`, ny pipeline `scripts/fetch_trend_history.py` → `scripts/build_trends_csv.py`. Historik for 42 af platformens indikatorer, 2010-2026, alle 98 kommuner. Viser en pil pr. sub-indikator og pr. dimension/kategori (worst-of-regel for øko-dimensioner, gennemsnit for sociale kategorier og for Forurening). Se `data/README.md` for skema og metode.
- **Klimaregnskabet.dk udvidet**: `scripts/fetch_climate_data.py` skriver nu også `data/klimaregnskab_kontekst.csv` (sektorfordeling landbrug/energi/transport, samlet energiforbrug, VE-el selvforsyningsgrad) - genbruger samme API-svar som den eksisterende territoriale CO2-hentning, ingen ekstra kald. Registreret som kontekst-indikatorer (`ctx_klima_*`, `ctx_energiforbrug`, `ctx_ve_selvforsyning`) i `build_master_csv.py`, vist under Klimapåvirkning-dimensionen. Scores ikke - er en opdeling af det allerede scorede territoriale tal.

## 2026-04-25

- **Indført long format master-fil** (`master_indicators.csv`). Konsoliderer 21 separate rådata-CSV'er til én tidy data-fil. Genereres af `scripts/build_master_csv.py`.
- Webapp læser nu kun fra master-filen. Rådata-CSV'er bevares som debug-spor.
- **Auto-rebuild**: alle 11 fetch-scripts kalder nu `build_master_csv.auto_build_master()` til sidst, så master-CSV altid er opdateret efter en fetch. Ingen manuel ekstra kommando nødvendig.
- Fjernet `car_access` (familier med bilrådighed) som scoring-indikator i Mobilitet. Konceptuelt skævt i bæredygtighedsramme. Rådata fortsat tilgængelig i `mobilitet_scores.csv`.
- Fjernet `ve_capacity_mw` (installeret VE-kapacitet) som død data fra `doughnut_scores.csv`. Blev ikke brugt i webapp.
- Fjernet fallback for `forbrug_co2` (tidligere 11 ton national gennemsnit). Kommuner uden CBA-data vises nu som "data mangler" i stedet for misvisende fallback-score.
