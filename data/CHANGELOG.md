# Data CHANGELOG

Log over større ændringer i datapipeline og master-fil.

## 2026-09-17

- **Den Nationale Sundhedsprofil taget i brug som kilde.** Nyt script `scripts/fetch_sundhedsprofil.py` henter kommunetal fra internetdatabasen på danskernessundhed.dk (Sundhedsstyrelsen + SIF/SDU). Otte indikatorer, alle 98 kommuner, bølge 2025. Nye rådata-filer: `sundhedsprofil_scores.csv` (seneste bølge) og `sundhedsprofil_historik.csv` (alle fem bølger 2010-2025).
  - **Forudsætningen i `docs/sociale_indikatorer_datadaekning.md` var forkert.** Dokumentet anførte at sundhedsprofilen "udgives kun på regionsniveau" og markerede 7-8 indikatorer som utilgængelige af den grund. Internetdatabasen har kommune som baggrundsvariabel for samtlige ca. 70 indikatorer. Dokumentet er rettet.
  - **Teknisk:** viewerens SAS-transportlag kaldes direkte. Gæste-login via CAS, derefter generateReport og getData. To fælder er dokumenteret i scriptet: /services/* svarer 401 uden en indløst service ticket, og getData svarer 400 hvis reportDate mangler.
  - **Landsgennemsnit** beregnes som befolkningsvægtet gennemsnit af de 98 kommuneandele (DST FOLK1A, 16+, undersøgelsens målgruppe). Databasen udstiller ikke et landstal pr. kommunetabel. Tallet afviger derfor en anelse fra SIF's eget vægtede landsestimat.
  - **Kadence:** bølger hvert fjerde år. Kommunetallene står fast indtil næste bølge, og `data_year` er sat til 2025 for alle otte.

- **Sundhed omlagt fra otte til ni indikatorer.** Fem tilstandsmål og fire levevaner. Ind: `selvvurderet_helbred`, `mentalt_helbred`. Ud: `hospital_short`, `gp_distance`, `medicin`, `laegekontakt`, `boerneovervaeght`. Tilbage: `life_expectancy`, `hospital_long`, `hjemsyg`.
  - `laegekontakt` havde standardafvigelse 2,3 og et spænd fra p10 til p90 på 6,5 point, altså stort set ingen differentiering, og korrelerede -0,64 med hjemmesygepleje og -0,59 med lægeafstand. Den målte tilgængelighed, ikke sundhed.
  - `gp_distance` ramte 150-loftet for hele den øverste tiendedel og korrelerede 0,74 med pendlingsafstand. Den straffede landkommuner for geografi, og Mobilitet måler allerede afstand.
  - `hospital_short` korrelerede 0,60 med `hospital_long`, som har dobbelt så stor spredning.
  - `medicin` korrelerer **-0,01** med det direkte mål for dårligt mentalt helbred. Antidepressivt forbrug måler altså ikke mental sundhed, men behandlingsintensitet. Den er fjernet helt, ikke flyttet til kontekst.
  - `boerneovervaeght` byggede på 2018-tal og er afløst af voksenovervægt fra 2025.

- **Levevaner lagt ind under Sundhed.** `rygning`, `alkohol`, `kost` og `svaer_overvaegt` ligger i Sundhed sammen med de fem tilstandsmål, så kategorien har ni indikatorer i ét simpelt gennemsnit. Den sociale ring bliver på 13 kategorier. Levevaner var kortvarigt sin egen kategori i udviklingen af denne ændring; det blev fravalgt, fordi en fjortende kile ville have givet sundhedsområdet knap dobbelt vægt i den sociale score.
  - **Konsekvens der skal kendes:** seks af Sundheds ni indikatorer kommer nu fra Sundhedsprofilen, samme bølge og samme spørgeskema. En ændret definition eller en udeblevet bølge hos SIF rammer to tredjedele af kategorien på én gang, og middellevetid vejer en niendedel.
  - **`fysisk_aktivitet` hentes, men scores ikke.** Korrelation 0,90 med svær overvægt og 0,80 med kostskalaen. Med alle tre ville én underliggende konstruktion fylde tre af de ni pladser. Tallet står i `sundhedsprofil_scores.csv`.

- **Foreningsliv omdøbt til Fællesskab og givet et udfaldsmål.** Ind: `ensomhed`. Ud: `sports_facilities`. Den gamle kategori bestod udelukkende af kommunale udgifter og faciliteter og havde ingen indbyrdes sammenhæng: idrætsfaciliteter korrelerede -0,35 med idrætsudgifter og -0,32 med foreningsstøtte. Gennemsnittet af de fire udlignede hinanden frem for at måle noget. `ensomhed` korrelerer 0,12 med Sundhed og 0,17 med den gamle Foreningsliv-score og tilfører dermed information ingen anden indikator har.

- **`traffic_accidents` lagt om til treårigt gennemsnit** (UHELDK1 2022-2024). Ét års tal er ren støj i små kommuner: Læsøs score på 35 hvilede på omkring to tilskadekomne, Samsøs på 18,9 på omkring otte. Én ulykke fra eller til flyttede scoren med titalls point, og kommunen kunne ikke påvirke det. Efter omlægningen: Læsø 76,5, Samsø 41,1. Samme greb som `vejr_skader`, der allerede bruger 2023-2025. Kriminalitetsscoren er urørt, men bemærk at den rammer 150-loftet i en stor del af de tyndt befolkede kommuner og derfor ikke kan skelne mellem dem.

- **Retningspile for de nye indikatorer.** Sundhedsprofilens serie skrives ind i `trend_history_raw.csv` med 2017 som basisår og 2025 som slutår. 2010 fravalgt, fordi en pil over 15 år ikke er sammenlignelig med de øvrige indikatorers vinduer. 2021 fravalgt som basis hvor 2017 findes, fordi dataindsamlingen det år lå under coronarestriktioner. `ensomhed` har nødvendigvis 2021 som basis, da spørgsmålet først blev stillet da. `OP_ER_GODT` i `build_trends_csv.py` er synkroniseret med `shared.ts`, og rækkerne for de fem fjernede indikatorer er ryddet ud af `trend_history_raw.csv`.

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
