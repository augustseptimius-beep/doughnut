# Data CHANGELOG

Log over større ændringer i datapipeline og master-fil.

## 2026-09-22

- **Indkomst måles på median, ikke gennemsnit.** Gælder `disposable_income` (Velfærd) og `income_gender_gap` (Ligestilling), både i master og i retningspilene. Kilde skiftet fra INDKP101 (ENHED 116, gennemsnit for alle personer) til INDKP106.
  - **Anledning: Vejen.** Kvindernes gennemsnitlige disponible indkomst steg fra 217.000 kr. (2022) til 438.000 kr. (2023), formentlig pga. meget få personer med ekstreme indkomster. Vejen fik dermed topscore på ligestilling (kvinder "tjente" 142 % af mænd, score 150) og en disponibel indkomst 25 % over landsniveau. Med median: 80,1 % (score 93,7) og 97,0.
  - **DST udgiver ikke medianen pr. kommune og køn.** Den beregnes af `scripts/indkomst_median.py` ud fra antal personer (15 år+) i INDKP106's indkomstintervaller, ved lineær interpolation i intervallet hvor den kumulerede andel passerer 50 %. Kontrolleret mod en tæthedsmodel der bruger DST's gennemsnit inden for intervallet: afvigelsen er typisk under 1.000 kr. og under 0,6 procentpoint på kønsforholdet (højst 0,8 for Læsø).
  - **Konsekvens for scoren:** alle 98 kommuner har nye tal på de to indikatorer. Ingen kommune rammer længere 150-loftet på nogen af dem (før: Gentofte, Rudersdal og Hørsholm på indkomst, Vejen på kønsforhold). Landsniveauet er 246.098 kr. og 85,5 %.
  - **Retningspilene** er genberegnet på medianserier 2010-2024. Kun rækkerne for de to indikatorer i `trend_history_raw.csv` er udskiftet; de øvrige er uændrede. Kvinders indkomst i forhold til mænds falder på landsplan over perioden, både målt på median (90,3 til 85,5 %) og på gennemsnit (85,3 til 80,0 %), så de mange røde pile på indikatoren er ikke et produkt af omlægningen.
  - Gini (IFOR41) er uændret. Den er et fordelingsmål, og få meget høje indkomster øger den målte ulighed reelt; Vejen ligger fortsat højt.

## 2026-09-17 (anden runde)

- **Fællesskab: udgiftsmål erstattet af udfaldsmål og deltagelse.** Ud: `sports_spending` (kommunale idrætsudgifter pr. indb.). Ind: `social_stoette` (Sundhedsprofilen) og `sport_tilskuer` (DST KV2GEO). Kategorien er nu ensomhed, begrænset social støtte, idrætsmedlemskab, tilskuerdeltagelse og foreningsstøtte - to udfald, to deltagelsesmål og ét input, mod tidligere ét udfald og tre input.
  - `sports_spending` var rent budget og korrelerede nær nul med alt andet i kategorien. Idrætsudgifter er desuden delvist fanget via medlemskabstallet.
  - `civil_society` beholdes bevidst, selvom den også er et udgiftstal: den er det eneste sted i modellen hvor kommunens egen indsats på området er synlig.
  - `social_stoette` = andel der aldrig eller næsten aldrig har nogen at tale med ved problemer. Korrelerer 0,50 med ensomhed, altså beslægtet men ikke overlappende, og har hele serien 2010-2025.

- **`sport_tilskuer` fra kulturvaneundersøgelsen (KV2GEO), med ufuldstændig dækning.** Andel der har overværet en sportsbegivenhed som tilskuer, toårigt gennemsnit 2024-2025. Valgt blandt undersøgelsens 17 aktiviteter, fordi den som den eneste korrelerer positivt med idrætsmedlemskab (0,25) og nul med foreningsudgifterne (-0,04). Biblioteks-, museums- og kunstbesøg korrelerer 0,34-0,41 med foreningsudgifterne og måler dermed samme by- og uddannelsesgradient som vi har i forvejen; medieforbrug ligger på 90-99 procent overalt og skelner ikke.
  - **Dækker kun 76 af 98 kommuner.** DST undertrykker tal hvor stikprøven er for lille. Toårigt gennemsnit blev valgt frem for ét år, fordi det både løfter dækningen og dæmper støjen (laveste værdi går fra 22 til 29 procent, så en del af yderpunkterne var stikprøvestøj).
  - **Den manglende dækning er systematisk skæv.** De 22 kommuner uden tal har median ca. 24.000 indbyggere mod ca. 53.000 for dem med tal. Læsø, Fanø, Samsø, Ærø og Langeland er blandt dem. De får Fællesskab beregnet på fire indikatorer hvor de øvrige bruger fem, og det er netop de små kommuner hvor et lokalt idrætsfællesskab kan fylde mest, der ikke kan måles på det. Indikatoren er taget med alligevel efter beslutning, fordi alternativet var intet deltagelsesmål, men forskellen står eksplicit på metodesiden.
  - **Ingen retningspil.** Tabellen findes kun for 2024 og 2025, og begge år indgår i gennemsnittet, så der er ingen uafhængig start- og slutværdi.
  - **Fælde fundet under udviklingen:** KV2GEO's områdeliste blander kommuner, landsdele og regioner, og regionerne har OGSÅ trecifrede koder (081-085). Et filter på "tre cifre og ikke 000" tager dem med og overvurderer dækningen med fem. `fetch_kulturvaner.py` slår derfor op i master-CSV'ens kommuneliste.

- **Fravalgte alternativer** (undersøgt, ikke brugt): `LABY58` frivilligt arbejde findes kun på kommunegruppeniveau med fem grupper, samme problem som `public_transport`. `FOHOJ04` højskolekursister er opgjort på landsdele. `KV2FR2` frivilligt arbejde har ingen geografi. `IDRFOR01` antal idrætsforeninger pr. indbygger findes for alle 98 med tolv års historik, men korrelerer -0,35 med idrætsudgifter, altså samme fortegnsproblem som det fjernede `sports_facilities`.

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
