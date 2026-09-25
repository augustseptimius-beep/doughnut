# Data CHANGELOG

Log over større ændringer i datapipeline og master-fil.

## 2026-09-25 (lavindkomst fjernet fra Lighed, Netlify bygger ved dataændringer)

- **`low_income` er fjernet.** Andelen under 50 % af medianindkomsten (LABY07, alle aldre) kom fra samme tabel som børnefattigdom under Velfærd og korrelerede 0,87 med den og 0,78 med relativ fattigdom (IFOR12P). Fattigdomsniveauet talte dermed både i Velfærd og i Lighed. Lighed er nu gennemsnittet af Gini og beskæftigelsesgabet efter herkomst. De to korrelerer 0,09, så hver bestemmer halvdelen af kategorien.
- **Konsekvens for Lighed:** landsgennemsnitsvisningen går fra 84/14/0 til 86/10/2 (grøn/gul/rød) med 17 skift, kommunegruppevisningen fra 42/55/1 til 58/36/4 med 41 skift. Velstående forstadskommuner falder, fordi lav fattigdom trak dem op (Rudersdal -18,5, Hørsholm -16,8, Gentofte -15,6 i gruppevisningen), mens Brøndby (+18,6), Ishøj (+17,5) og Høje-Taastrup (+14,7) stiger. Thisted 102,9 → 102,4.
- Tidsserien er slettet af `trend_history_raw.csv`, og `fetch_trend_history.py` henter den ikke længere. Kun Lighed-pilen er ændret. Rådata ligger stadig i `doughnut_scores.csv`.
- **Netlify bygger nu også ved ændringer i `data/`.** Med `base = "webapp"` sprang Netlify buildet over, når intet under `webapp/` var ændret ("Canceled build due to no content change"), så en ren dataopdatering blev ikke lagt ud. `netlify.toml` har fået en `ignore`-kommando, der også ser på `data/` og `netlify.toml`, og som bygger, når den forrige commit er ukendt.

## 2026-09-25 (kystrisiko under Klimatilpasning)

- **Ny social indikator `kystrisiko`:** forventet årlig skade fra oversvømmelse fra havet og kysterosion i 2070 (RCP8.5) i kr. pr. indbygger, fra Kystdirektoratets Kystplanlægger (datapakke v1, marts 2021). Risikolagene (kr./år pr. 100 m-celle) summeres pr. kommune og deles med folketallet 1. januar 2021. Nyt script `fetch_kystrisiko.py`, ny fil `data/kystrisiko_scores.csv`.
- **Landstal 1.029 kr. pr. indbygger pr. år** (6,0 mia. kr./år, heraf 4,1 mia. fra oversvømmelse og 1,9 mia. fra erosion). Højest: Lemvig 6.597 kr., Hvidovre 5.102, Fanø 4.926, Læsø 4.494, Samsø 4.357. Thisted 1.792 kr. (ratio 57,4). Loftet er 100 (registrets `cap`, R1): ingen eller lav kystrisiko er neutral, ikke en fordel. 51 kommuner står på 100.
- **Klimatilpasning er nu gennemsnittet af `vejr_skader` og `kystrisiko`.** Farver fra 40/16/42 til 33/26/39 (grøn/gul/rød), 22 skift. Kystkommuner med få forsikringsskader falder (Hvidovre 137,0 → 78,6, Helsingør 121,8 → 76,5), og kommuner uden kystrisiko får kystrisikoen som neutral 100 (Holstebro 51,0 → 75,5, Frederiksberg 150 → 125). Thisted 45,7 → 51,6.
- **Nyt: socialt loft pr. indikator.** Registrets `cap` kan nu sænke R1's loft på 150 for en social indikator; det lægges på i pipelinen og igen efter omskaleringen i kommunegruppe- og top10-visningen. Gennemsnit med loftet 150 (Holstebro blev grøn på fraværet af kyst) og worst-of (skjuler vejrskaderne, som er det eneste mål der reagerer på tiltag) blev fravalgt.
- Begrundelse og forbehold: `data/klimatilpasning.md`.

## 2026-09-25 (UVM og Klimaregnskabet hentet med nye nøgler)

- **Første hentning med de nye API-nøgler** efter tilbagekaldelsen i august: `fetch_udvidelse_data.py` og `fetch_trend_history.py` (fuld kørsel).
- **UVM har omdøbt karaktergennemsnittet** fra "Gennemsnit - Obl. prøver" til "Gennemsnit i obl. 9.-klasseprøver" (GS/KARA/KARAGNS). Det gamle navn gav HTTP 400, og scriptet skrev tavst en tom `uvm_scores.csv`, så `exam_grade` forsvandt fra master. Rettet i begge scripts. Samme tal som før (Thisted 6,8 i 2024/25); nyt skoleår 2025/26. Nye navne findes med `POST /Api/v1/skema`.
- **Konsekvens:** ét farveskift (Vesthimmerland, Uddannelse gul → grøn, 99,89 → 100,12). Karakter-pilen skifter vurdering i 22 kommuner, Uddannelse-pilen i 2. Klimapåvirkning får pil i 9 nye kommuner og skifter vurdering i 4.
- **Fælde:** `fetch_trend_history.py` skriver `trend_history_raw.csv` forfra og sletter dermed de rækker `fetch_sundhedsprofil.py` har lagt der (8 indikatorer, 784 pile). Løst her ved at køre `fetch_sundhedsprofil.py` bagefter; sundhedsprofilens ratios flytter sig derved 0,01 (afrunding, råværdier uændrede). Rettet i samme omgang: en fuld kørsel af `fetch_trend_history.py` bevarer nu sundhedsprofilens serier (listen læses fra `fetch_sundhedsprofil.INDIKATORER`).

## 2026-09-25 (vand mod den bæredygtige grundvandsressource)

- **Vand måles nu mod en absolut grænse.** `vandindvinding` er grundvandsindvindingen (VANDIND, `VANDTYP=GVAND`, alle tre kategorier, treårsgennemsnit 2022-2024) i procent af kommunens andel af Danmarks bæredygtige grundvandsressource. GEUS' nationale ressource (1.104 mio. m³/år, rapport 2023/08, bilag 2) fordeles efter DK-modellens infiltration til mættet zone (HIP, 1991-2020) gange landarealet. Ny fil `data/grundvandsdannelse_scores.csv` fra nyt script `fetch_grundvandsdannelse.py` (kræver `DATAFORSYNINGEN_TOKEN`).
- **Kun grundvand.** Overfladevandet (ca. 240 mio. m³/år, især virksomheder som dambrug) indgik i dagen før; det gjorde bl.a. Vejle (408 → 57) og Silkeborg (116 → 31) røde. DST's grundvandsindvinding 2017-2021 (737 mio. m³) rammer GEUS' egen (734).
- **Konsekvens:** Danmark samlet 63% af ressourcen. Farver fra 49/5/44 (98 kommuner) til 59/7/30 (96 kommuner), 20 skift. Samsø og Læsø ligger uden for DK-modellen og har ingen vand-score. Thisted 16,8%.
- Kontrol mod GEUS' ressource pr. modelområde og forbehold: `docs/oekologisk-gennemgang-sep-2026.md` afsnit 2.

## 2026-09-24 (gennemgang af de økologiske dimensioner)

Samlet begrundelse, kilder og det der ikke kunne løses: `docs/oekologisk-gennemgang-sep-2026.md`.

- **Ny formel for økologiske andele hvor højere er bedre** (`formula: "komplement"`, arkitekturdokumentet R2a): ratio = (100 − andel)/(100 − mål) × 100, altså den manglende andel mod det målet tillader. Gælder biodiversitet, genanvendelse og vandområder. Den gamle formel (mål/andel) eksploderede ved andele nær nul og var cappet ved 300; over halvdelen af kommunerne stod på loftet på biodiversitet og 28 på vandområder. Ingen økologisk indikator har længere et loft.
- **Næringsstoffer:** ny `naer_kystvand` (kvælstofbelastningen af de kystvande kommunens areal afvander til, i procent af målbelastningen; bilag 1.1 i "Vandområdeplanerne 2021-2027 efter genbesøget", april 2026) og ny `n_deposition` (DCE's kvælstofnedfald pr. kommune mod en tålegrænse på 10 kg N/ha/år). Fjernet: `naer_nitrogen`, `naer_phosphorus` (spildevand pr. indbygger) og `naer_landbrug` (tålegrænse pr. ha landbrug), se registrets `_fjernet`. Alle 98 kommuner er nu røde (før 91); kystvandene ligger på 84-256% af målbelastningen.
- **Arealanvendelse:** ét tal, antropiseret areal (intensivt landbrug + befæstet, pct. af landarealet uden søer og vandløb; Dao m.fl. 2015), i stedet for worst-of af de to andele hver for sig. Danmark samlet 70,4%. Farver fra 2/14/82 til 16/26/56 (grøn/gul/rød), 28 skift; Frederiksberg går fra 637 til 127.
- **Vand:** al indvinding (almene vandværker, virksomheder, markvanding) i mm/år over landarealet, treårsgennemsnit 2022-2024, i stedet for almene vandværker pr. indbygger. Nu 98 kommuner (før 92). Farver fra 38/15/39 til 49/5/44, 51 skift. Afløst dagen efter af målingen mod den bæredygtige grundvandsressource (se 2026-09-25).
- **Forurening:** pesticider er nu andelen af AKTIVE almene vandværker med fund i seneste analyse, empirisk Bayes-udglattet (landsandel 30,5%). Før talte nedlagte værker og værker under kravværdien som "over". Nitrat bruger kun aktive værker (Thisted 5,2 → 14,5 mg/L; korrelation med Greenpeaces top 20 fra 0,80 til 0,93). Affald og genanvendelse er treårsmedianer 2021-2023 (fejlindberetninger i 2023). Dragør har ingen aktive almene vandværker med analyse og mister nitrat og pesticider. Farver fra 38/17/43 til 24/35/39, 49 skift.
- **Luftkvalitet:** befolkningsvægtet med Eurostats 1 km-grid, som metodesiden altid har sagt. Ingen farveskift.
- **Klimapåvirkning:** grænsen er 2,5 ton CO₂e pr. person (Hot or Cool Institute 2021) i stedet for 3 ton, som ingen kilde underbyggede. Forbrugs-CO₂ er nutidsjusteret til 2024 med Energistyrelsens reviderede tidsserie (`fetch_forbrug_co2.py`, faktor 0,7226). Alle kommuner var og er røde; ratioerne stiger ca. 20%.
- **Biodiversitet:** samme farver som før (4/1/93), men ingen kommuner på et loft; median 300 → 136.
- **Data hentet 24. sep.:** GEUS Jupiter, DST (LABY25, VANDIND, AREALDK2, VANDUD), Miljøportalens luftkort 2024, VP3-pakken, DCE's depositionstabeller 2014-2024 og Energistyrelsens datafil. Klimaregnskabet og UVM er ikke hentet (kræver nøgler); `climate_scores.csv`'s egen krydstjek-ratio er genberegnet med 2,5 ton, og `biodiversitet_scores.csv`'s med komplement-formlen, uden at råværdierne er rørt.
- **Retningspile:** nye serier for `areal_antropiseret` og `n_deposition`; `vandindvinding`, `cirkularitet_waste` og `cirkularitet_recycling` er genberegnet med scorens nye definition. Serierne for de fjernede indikatorer er slettet. Hentet med den nye `fetch_trend_history.py --kun ... --fjern ...`, der ikke kræver API-nøgler. Næringsstoffer har kun pil i 8 kommuner (hvor kvælstofnedfaldet afgør scoren).
- **Ingen sociale tal er ændret.**

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
