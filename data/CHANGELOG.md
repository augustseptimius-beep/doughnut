# Data CHANGELOG

Log over større ændringer i datapipeline og master-fil.

## 2026-09-24 (loft på 150 i standardvisningen)

- **Kommunegruppe-baselinen har fået samme loft på 150 som landsgennemsnit-visningen** (arkitekturdokumentet R10). Loftet lægges på efter omskaleringen til gruppesnittet. Før kunne én indikator løfte en hel kategori: Svendborg fik 338 på `public_transport` og 214,7 på Mobilitet. Nu får Svendborg 150 og 120,5.
- **Top 10%-baselinen har fået samme loft** (R9). Det ændrer ingen tal i dag, fordi den højeste top 10-ratio er 124,2, men reglen er nu den samme i alle tre visninger.
- **Konsekvens i standardvisningen:** 68 indikatorværdier i 44 kommuner lå over 150 og står nu på 150. Flest for `public_transport` (16) og `civil_society` (11), og 16 indikatorer er ramt i alt. 63 kategoriscorer ændres. Tre skifter farve: Kultur går fra grøn til gul i Odder (102,4 til 99,3), Læsø (100,6 til 93,6) og Samsø (106,7 til 98,5), fordi én indikator over 150 trak gennemsnittet op over 100. Den højeste kategoriscore er nu 150 mod før 214,7.
- **Masterfilen og retningspilene er uændrede.** Loftet ligger i webappen (`computeGroupRatios()` og `computeTop10Ratios()` i `shared.ts`), ikke i pipelinen.
- **Sammenligningsværdien vises ikke ved en indikator på loftet.** Kommunesiden udleder gruppesnittet baglæns af råværdi og score, og det kan ikke lade sig gøre, når scoren er klippet. Samme regel gjaldt allerede for ratios klippet i pipelinen (R1).

## 2026-09-24 (offentlig transport pr. kommune)

- **`public_transport` beregnes nu pr. kommune af `fetch_offentlig_transport.py`.** DST's LABY49 findes kun for fem kommunegrupper, så indikatoren havde fem værdier, og i standardvisningen fik alle 98 kommuner præcis 100. Scriptet genskaber DST's metode (verdensmål 11.2.1) med Rejseplanens GTFS, DAR-adresser og Eurostats befolkningsgrid 2021: andelen af befolkningen, der bor højst 500 m gang fra stoppesteder med tilsammen mindst 10 afgange i timen en typisk hverdag kl. 6-20. Lagt sammen til kommunegrupper rammer tallene LABY49 2025 med 1,2 procentpoint i gennemsnit. Metode og validering: `docs/offentlig-transport-genskabt.md`.
- **Referencen er nu Danmark som helhed:** 37,01 % mod før et uvægtet gennemsnit af gruppetallene på 30,02 %. Det lukker afvigelsen for `public_transport` i arkitekturdokumentets afsnit 7.
- **Dataår 2025 til 2026** (køreplanen for 30. september 2026).
- **Konsekvens:** 85 ratios ændret; de 13 øvrige lå på loftet 150 både før og efter. 87 forskellige værdier mellem 0 % og 95,7 %. Seks kommuner får 0 %: Ærø, Fanø, Lemvig, Norddjurs, Samsø og Læsø. Thisted går fra 9,91 % til 7,35 %.
- **Farveskift på Mobilitet:** 56 i standardvisningen (grøn/gul/rød fra 51/46/1 til 46/15/37), 16 med landsgennemsnit og 9 med top 10%. Standardvisningen flytter mest, fordi indikatoren før var 100 for alle.
- **Standardvisningen får høje toppe.** Landkommunernes gruppesnit er ca. 6 %, og kommunegruppe-baselinen har intet loft (R10). Svendborg får derfor 338 på indikatoren og 214,7 på Mobilitet. Ingen anden kategori kommer over 177. Rettet samme dag med loftet ovenfor.
- **`mobilitet_scores.csv`** har mistet kolonnerne `public_transport_pct` og `public_transport_ratio`, og `fetch_social_new_data.py` henter ikke længere LABY49. Tabellen bruges kun til valideringen i det nye script.
- **Ingen retningspile ændret.** Indikatoren har stadig ingen pil, fordi Rejseplanens køreplanarkiv kun går tilbage til december 2025.

## 2026-09-24 (NEET: NEET3 afløser NEET1)

- **`neet` hentes nu fra DST NEET3.** DST satte NEET1 inaktiv i maj 2025 med 2023 som sidste år, så indikatoren stod stille. NEET3 dækker 16-29 år med alder som variabel; 16-24 år giver præcis NEET1's tal (alle 3.168 kommune-år 2008-2023 er ens), og tabellen har 2024. Nævneren var desuden hårdkodet til 2023 i det gamle script.
- **Scoren og pilen hentes af samme funktion** (`serie_neet()`), og landstallet er de 98 kommuner samlet (9,14% i 2024 mod 9,64% i 2023).
- **Konsekvens:** alle 98 NEET-tal er nu fra 2024. Små kommuner svinger mest (Samsø 14,1% til 9,6%, Kerteminde 11,7% til 8,1%). Velfærd skifter farve i 3 kommuner i standardvisningen (Kolding og Ikast-Brande gul til grøn, Hjørring grøn til gul), 5 med landsgennemsnit og 1 med top 10%. 4 NEET-pile vender retning; pilen går nu til 2024.

## 2026-09-24 (landsgennemsnit betyder Danmark som helhed)

- **Beslutning:** et landsgennemsnit er de 98 kommuner samlet, vægtet med indikatorens egen nævner. Det er ikke et uvægtet gennemsnit af kommunerne og ikke en hele-landet-række med tal uden kommune (arkitekturdokumentet R3).
- **Tre referencer ændret:**
  - Kriminalitet: 69,24 til 63,22 pr. 1.000 indb. 8,7% af anmeldelserne i 2025 har ingen kendt gerningskommune og talte med i DST's landstal, men hos ingen kommune.
  - Vejrskader: 25,88 til 21,92 pr. 1.000 indb. Referencen var et uvægtet gennemsnit af kommunerne; nu er den vægtet med folketallet.
  - Underretninger: 89,53 til 92,33 pr. 1.000 børn. DST's landstal tæller 3,1% færre underretninger end kommunerne tilsammen.
  - Ubetydelige ændringer (højst 0,3%) for kvælstof, biblioteksudlån og musikskole, fordi alle tal pr. indbygger nu danner landstallet af kommunerne selv (`dst.pr_indbygger()`). For spildevand tæller alle 98 kommuners indbyggere med, også Frederiksberg, hvis spildevand renses i København.
- **Ingen råværdier eller retningspile er ændret.**
- **Farveskift:** 41 i landsgennemsnit-visningen (Klimatilpasning 33, Tryghed 6, Velfærd 2), 14 i standardvisningen (Klimatilpasning 8, Tryghed 6) og 28 med top 10%. Standardvisningen påvirkes kun gennem loftet på 150: færre kommuner rammer loftet (vejrskader 27 til 15, kriminalitet 39 til 25), og gruppesnittet beregnes af de afskårne værdier.
- **Ikke ændret:** de fire UVM-indikatorer (mangler elevtal pr. kommune, kræver UVM-nøglen) og `public_transport` (data kun pr. kommunegruppe). Begge står i arkitekturdokumentets afsnit 7.

## 2026-09-23 (retningspilen og scoren er samme tal)

- **Retningspilen beskrev et andet tal end scoren for 14 indikatorer.** Tidsserien (`fetch_trend_history.py`) havde sin egen definition af hver indikator. Eksempler: klassekvotient kun i folkeskolen mod scorens alle skoletyper (Samsø 17,1 mod 12,6), ubeboede boliger inkl. fritidshuse (Thisted 24% mod 11,5%), sportsanlæg talt med i bebygget areal, 16-64 år mod scorens 16-66 år, og Klimaregnskabets to "Samlet"-rækker lagt sammen i stedet for den største (Læsø -5,2 mod 4,7 ton). `education`s serie sluttede i 2019. Nu hentes 15 indikatorer af én funktion (`serie_<id>()` i fetch-scriptet), som både scoren og pilen bruger, og `tjek_konsistens.py` fejler, hvis serie og score afviger (CLAUDE.md pkt. 37).
- **To definitioner er ændret, så de kan bruges til begge dele.** Tal pr. indbygger deles nu med folketallet 1. januar i tallets eget år, ikke det nyeste kvartal (kriminalitet, trafikulykker, biblioteksudlån, musikskole, hjemmesygepleje, underretninger, kvælstof, fosfor, vandindvinding; median 0,7-1,4%, højst 4-9%). `employment_origin_gap` bruger 16-64 år, fordi DST kun har 16-66 fra 2022 (median 0,7%, højst 4,1%).
- **Data hentet på ny 23. sep. for alle DST-indikatorer, både værdi og tidsserie**, så de er fra samme dag. Ny i data: trafikulykker 2025 (vinduet er nu 2023-2025) og underretninger 2025. UVM og Klimaregnskabet er ikke hentet (kræver nøgler); deres tidsserier er beholdt.
- **Konsekvens for scoren:** 984 ratios i 12 indikatorer ændret. I standardvisningen (kommunegruppe) skifter 20 kategorier farve (Tryghed 10, Velfærd 6, Lighed 4), med landsgennemsnit 11, med top 10% 16. To økologiske dimensioner skifter: Greve (Næringsstoffer gul til rød) og Sønderborg (Vand gul til grøn). Trafikulykkerne står for det meste af Tryghed, og her er årsagen de nye 2025-tal, ikke definitionen.
- **Konsekvens for pilene:** 173 pile vender retning, og 316 skifter vurdering. De største er `education` (54, serien sluttede i 2019), Bolig (30, ubeboede boliger), pædagoguddannede (17) og klassekvotient (15). 14 pile er fjernet: 9 for klimapåvirkning, hvor den gamle serie lagde to rækker sammen (kommer igen ved næste hentning med Klimaregnskabet-nøglen), 4 for tal der ikke har en score (Københavns vandindvinding, Frederiksbergs kvælstof og fosfor, Fanøs fosfor) og Glostrups fosfor, hvor serien før 2024 kun bestod af nuller, som nu behandles som manglende data ligesom i scoren.
- **Dataår:** perioder og skoleår mærkes med slutåret i både score og pil. Elevtrivsel 2024 til 2026 (skoleåret 2025/26), karakterer og fravær 2024 til 2025 (2024/25), ungdomsuddannelse 2024 til 2023. UVM-scriptet registrerede ikke sit år, så sitet viste registrets faste år; værdierne i `data_years.json` er sat ud fra at scoren er lig tidsseriens punkt for det år, og scriptet skriver dem selv fremover. Middellevetidens pil hedder nu "... → 2021-2025" i stedet for startåret.
- **Landstallet skrives af fetch-scripterne** (`<id>_ref`) for 41 af de 52 landstal. De 11 der stadig rekonstrueres (Sundhedsprofilen, VP3, landbrugskvælstof, pesticider), kommer fra scripts der ikke er kørt her; de skriver det ved næste kørsel.
- `data/trend_history_log.txt` er fra den seneste fulde kørsel og ikke opdateret.

## 2026-09-23 (én kommuneliste og ét DST-kald)

- **Ny fil `data/kommuner.json`** med de 98 kommuner (kode, navn, kommunegruppe). Fetch-scripterne, `build_master_csv.py` og webappens kommunegruppe-baseline læser den i stedet for hver sin kopi. Master, noegletal og alle 104 sider på sitet er uændrede.
- **`cba_2023_estimate.csv` og `klimatilpasning_scores.csv` har fået kolonnen `kommune_kode`** og slås nu op på kode i stedet for navn. Værdierne er uændrede. `fetch_klimatilpasning_data.py` skriver koden selv og stopper ved et ukendt kommunenavn.
- **Rettet før den nåede sitet: `fetch_doughnut_data.py` ville have tilføjet 11 landsdele som kommuner.** Median-indkomsten fra PR #9 hentede alle områder i INDKP106 uden filter, så en fuld kørsel skrev 109 rækker (landsdelene 01-11 med kun indkomst). Den committede fil havde 98, fordi scriptet ikke var kørt fuldt siden. Fundet ved at køre scriptet i en kopi; `build_master_csv.py` stopper nu, hvis kommunerne ikke er præcis de 98.

## 2026-09-23 (farve følger viste score)

- **Farven følger nu den viste score.** Scores vises med én decimal, men farven blev afgjort af den uafrundede værdi, så fx Aalborgs Ligestilling stod som "100.0" i gult (99,963). Nu afrundes scoren én gang (`visningsscore()` i `shared.ts`), og tekst, farve, ringens tænder og tællingen "N af 13 kategorier over gennemsnittet" bruger samme tal. Ingen tal i master er ændret. I standardvisningen (kommunegruppe) skifter 9 kategorier farve: Herlev, Ærø og Syddjurs (Lighed), Ringsted (Velfærd og Fællesskab), Vejen (Mobilitet), Randers (Uddannelse), Skive (Demokrati) og Aalborg (Ligestilling). Alle lå under 0,05 fra grænsen på 85 eller 100.

## 2026-09-22 (rettelse: indkomstlighed manglede på sitet)

- **`income_gender_gap` (Indkomstlighed mænd/kvinder) blev ikke vist i nogen kommune** fra median-omlægningen samme dag (PR #9) til denne rettelse. Enheden blev ændret til `% (kvinder/mænd, median)`, og kommaet forskød kolonnerne i webappens `split(",")`-parsing af master, så rækkerne ikke blev genkendt som sociale. Tallene i master var korrekte; kun visningen manglede. Ligestilling blev i perioden regnet på 2 af 3 indikatorer.
  - Enheden hedder nu `% (kvinders medianindkomst af mænds)`.
  - **Konsekvens:** Ligestilling regnes igen på alle tre indikatorer. Med kommunegruppe som baseline (standardvisningen) skifter 8 kommuner farve: København, Tårnby, Helsingør og Svendborg går fra gul til grøn; Furesø, Rudersdal, Skanderborg og Aalborg fra grøn til gul. Alle otte lå i forvejen inden for 1,1 point af grænsen på 100. Med landsgennemsnit skifter 11, med top 10% 14.
  - **Så det ikke sker igen:** registret afviser komma i felter der skrives til master, `build_master_csv.py` fejler hvis et felt indeholder komma, og webappen stopper buildet hvis en række i master ikke passer med registret (se CLAUDE.md pkt. 34).

## 2026-09-22 (ratio beregnes ét sted)

- **Alle ratios beregnes nu i `build_master_csv.py`** ud fra råværdi og reference (fast mål, kommunegennemsnit eller landstal) i `data/indikatorer.json`, med én formel for retning, loft og værdien 0. Fetch-scripternes egne ratios indgår ikke længere i scoren. Master har fået en ny sidste kolonne, `reference`.
  - **7 rækker fjernet:** kvælstof fra spildevand for Frederiksberg og Fanø, fosfor for Frederiksberg, Herlev, Rødovre, Ærø og Fanø. De stod med ratio 66,67 uden råværdi. VANDUD har ingen udledning registreret for dem, og `fetch_eco_new_data.py` gjorde "ingen udledning" til topscore 150 på sin inverterede skala, som build_master derefter vendte til 10000/150 = 66,67. Tallet svarede hverken til 0 eller til manglende data. Nu har de ingen værdi, ligesom vandindvinding for kommuner hvor vandværket ligger i nabokommunen. Næringsstoffer-dimensionens score er uændret for alle fem kommuner, fordi den afgøres af en anden sub-indikator.
  - **534 ratios flyttet med højst 0,45 point**, fordi de nu regnes fra den råværdi der står i CSV'en i stedet for scriptets uafrundede tal. Størst for fosfor (råværdi med 3 decimaler, fx 0,025 ton pr. 1.000 indb.), derefter kvælstof (0,08), pesticider (0,06), nitrat (0,03, scriptet afrundede ratioen til 1 decimal) og klimapåvirkning (0,02). Resten er 0,01. Ingen kategori eller dimension skifter farve under nogen af de tre baselines; største ændring i en kategoriscore er 0,0025.
  - **Landstallene rekonstrueres** ved hvert build fra scriptets egen ratio, indtil scripterne selv skriver dem. Rekonstruktionen genskaber de publicerede tal (fx middellevetid 81,6 år, lederandel 32,11%, disponibel indkomst 246.098 kr.).
  - Retningspilene er uændrede.
- **Ny genereret fil `data/noegletal.json`** (reference, dækning og dataår pr. indikator). Metodesidens og registrets tekster henter landstal og dækning derfra via pladsholdere i stedet for håndskrevne tal. Ingen tal på siden er ændret af det; eneste synlige forskel er "de 3 uden data" i stedet for "de tre".

## 2026-09-22 (indikatorregister)

- **Indikatorerne står nu ét sted, `data/indikatorer.json`.** Build-scripts, retningspile og webappen læser alle derfra. Ingen tal i master eller trend-CSV er ændret af omlægningen; begge filer er byte-identiske før og efter.
- **Dataår for periodetal skrives som perioden.** `life_expectancy` og `le_gender_gap` (HISBK, femårige intervaller) står nu som 2021-2025, og `traffic_accidents` (treårigt gennemsnit af UHELDK1) som 2022-2024. Siden 22. sep. stod de som 2025 og 2024, fordi `data_years.json` kun gemmer slutåret. Styres af `period_years` i registret. Kun `data_year`-kolonnen er ændret, ingen ratios eller råværdier.

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
