# Gennemgang af de økologiske dimensioner (september 2026)

Gennemgang af de syv økologiske dimensioner med fokus på svagheder i data og metode, og en
omlægning hvor der fandtes en bedre kilde eller en metode med belæg i litteraturen. Hvor der
ikke fandtes noget bedre, er indikatoren beholdt, og hullet står i afsnit 5.

Alle tal er beregnet på master-CSV'en efter omlægningen (24.-25. september 2026). "Før" er den
master, der lå på main før gennemgangen.

## 1. Kort fortalt

| Dimension | Største svaghed før | Hvad er ændret | Belæg |
|---|---|---|---|
| Klimapåvirkning | Grænsen på 3 ton havde ingen kilde. Forbrugs-CO₂ byggede på en håndberegnet faktor | Grænse 2,5 ton. Forbrugs-CO₂ nutidsjusteret til 2024 med Energistyrelsens reviderede tidsserie, hentet af et script | Hot or Cool Institute 2021; ENS Global Afrapportering 2026 |
| Forurening | Pesticider talte nedlagte vandværker og værker under kravværdien som "over"; 1 af 1 vandværk gav 100%. Nitrat medregnede nedlagte værker. Affald 2023 havde fejlindberetninger | Kun aktive værker; pesticider som andel med fund, empirisk Bayes-udglattet; affald og genanvendelse som treårsmedian | GEUS Jupiter; Kleinman 1973; Clayton & Kaldor 1987 |
| Luftkvalitet | Metodesiden lovede befolkningsvægtning, koden tog arealgennemsnit | Befolkningsvægtet med Eurostats 1 km-grid | WHO; FN's verdensmålsindikator 11.6.2 |
| Næringsstoffer | Ingen absolut grænse. Spildevand pr. indbygger i renseanlæggets kommune. "Tålegrænse pr. ha" målte følsomhed, ikke belastning. Vandområder: 28 kommuner på loftet 300 | Kvælstof til kystvande mod målbelastningen (absolut); kvælstofnedfald mod tålegrænsen (absolut); vandområder med komplement-formlen | Vandområdeplanerne efter genbesøget (2026); CONCITO 2025; DCE 2024; Bobbink m.fl. 2022 |
| Vand | Almene vandværker pr. indbygger viste hvor HOFOR har kildepladser; 53% af indvindingen var udeladt; ingen grænse | Grundvandsindvinding i procent af kommunens andel af den bæredygtige grundvandsressource, fordelt efter grundvandsdannelsen (absolut) | GEUS 2023; DK-modellen (HIP) |
| Arealanvendelse | Worst-of af to spejlvendte relative andele gjorde 82 af 98 røde af konstruktionsmæssige grunde | Ét tal: antropiseret areal | Dao m.fl. 2015; EEA 2020; CONCITO 2025 |
| Biodiversitet | Formlen mål/andel eksploderede; over halvdelen af kommunerne stod på loftet 300 | Komplement-formlen, intet loft | Fanning m.fl. 2022; Richardson m.fl. 2023 |

## 2. Svagheder og ændringer pr. dimension

### Klimapåvirkning

- **Grænsen.** Platformen målte mod 3 ton CO₂e pr. person og kaldte det "Paris-budgettet". Ingen
  af de tre kilder på metodesiden angiver 3 ton, og tallet findes ikke i repoets historik med en
  kilde. Grænsen er nu 2,5 ton: det niveau pr. person, Hot or Cool Institute (2021) angiver for
  2030 i et 1,5-graders-forløb (1,4 ton i 2040, 0,7 i 2050). Det ændrer ingen farver (alle 98
  kommuner var og er røde), men alle klimaratios stiger 20%.
- **Forbeholdet ved 2,5 ton.** Målet er udledt for husholdningernes forbrug. Det forbrugsbaserede
  tal på platformen omfatter også offentligt forbrug og investeringer, og det territoriale også
  produktion til eksport. Det står nu på metodesiden. Et alternativ med samme afgrænsning findes
  ikke som ét årstal pr. person; CONCITO (2025) opgør kun samlede restbudgetter.
- **Forbrugs-CO₂.** Estimatet er stadig Tier 1 (2011-mønsteret fra Osei-Owusu m.fl. 2020, skaleret
  nationalt). Faktoren hentes nu af `fetch_forbrug_co2.py` fra Energistyrelsens datafil. Global
  Afrapportering 2026 har revideret 2011 fra 14,07 til 13,46 ton pr. indbygger, så estimatet
  gælder nu 2024 (faktor 0,7226). Se `data/methodology_note.md`.

### Forurening

- **Pesticider, to fejl.** (1) Jupiter indeholder nedlagte vandværker; 844 af 3.033 anlæg var ikke
  aktive. (2) Status "Aktuelt fund og tidl. over kravværdi" blev talt som over kravværdien, men
  seneste analyse er under (fx Gentofte: 0,064 µg/l, stod som 100% over). Af de aktive værker er
  kun 33 aktuelt over kravværdien, for få til at skelne kommuner.
- **Ny definition.** Andelen af aktive almene vandværker, hvor seneste analyse (højst 10 år) har
  fund af pesticider eller nedbrydningsprodukter. Fund er GEUS' egen hovedindikator, og for
  stoffer der ikke hører hjemme i grundvandet er tilstedeværelsen selv signalet. Landsandel 30,5%.
- **Småtal.** 18 kommuner havde under 5 vandværker. Andelen udglattes nu med empirisk Bayes
  (beta-binomial, momentmetoden, Kleinman 1973): kommuner med få værker trækkes mod landsandelen.
  Prioren svarer til ca. 13 vandværkers vægt. Pesticid-ratioen går nu fra 37 til 184 mod før 0 til
  1.092, og indikatoren ejer ikke længere gennemsnittet i dimensionen.
- **Nitrat.** Kun aktive værker. Thisted går fra 5,2 til 14,5 mg/L. Mod Greenpeace/Schullehners
  top 20 stiger korrelationen fra 0,80 til 0,93, og den gennemsnitlige afvigelse falder fra 1,7 til
  1,2 mg/L. Den forskel, CLAUDE.md før kaldte metodisk, var de nedlagte vandværker.
- **Affald og genanvendelse.** LABY25 2023 har tydelige fejlindberetninger (Hørsholm 589 → 57 kg,
  Allerød 623 → 258, Fredensborg 661 → 1.379). Begge bruger nu medianen af de tre seneste år.
  Genanvendelsen blev læst fra en fil, intet script skrev; den skrives nu af `fetch_eco_new_data.py`.

### Luftkvalitet

- Kommunens tal er nu den befolkningsvægtede middelkoncentration, som metodesiden altid har
  sagt. PM2.5 ændrer sig højst 0,13 µg/m³, NO₂ op til ca. 0,6 µg/m³ i byer. Ingen farveskift.
- Svagheden der står tilbage: PM2.5 binder i alle kommuner, og en stor del er langtransport.

### Næringsstoffer

- **Kvælstof til kystvandene (`naer_kystvand`, ny).** Statusbelastningen (afstrømningsnormaliseret,
  2017-2021) i procent af målbelastningen for de kystvande kommunens areal afvander til.
  Målbelastningen er den belastning kystvandet kan tåle og stadig nå god økologisk tilstand; den er
  beregnet med modeller for hvert kystvand. Tallene står i bilag 1.1 i "Vandområdeplanerne
  2021-2027 efter genbesøget" (april 2026). Et areal afvander til sit eget kystvand og videre
  nedstrøms, og det får den højeste overskridelse i kæden. Resultat: 84-256%, 94 af 98 kommuner
  over. Det er præcis den bottom-up-grænse CONCITO (2025) bruger for Danmark (55.800 mod 37.900
  ton N), nu pr. kommune. Rapporten vurderede det som ikke muligt; det var det, fordi tallene
  ligger i planens bilag og deloplandene på MiljøGIS.
- **Kvælstofnedfald (`n_deposition`, ny).** DCE's beregnede nedfald pr. kommune (treårsgennemsnit)
  mod en tålegrænse på 10 kg N/ha/år, midten af 5-15 for heder, klitter og klithede (Bobbink m.fl.
  2022, oversat af DCE i notat 2024|16). Årlige tal fra 2014 giver retningspile. Placeret under
  Næringsstoffer efter princippet én grænse = én dimension (kvælstofkredsløbet).
- **Fjernet:** spildevandets kvælstof og fosfor pr. indbygger (en del af statusbelastningen; pr.
  indbygger i renseanlæggets kommune gav et skævt billede; som relativ worst-of-indikator kunne en
  kilde på ca. 5% af kvælstoffet afgøre dimensionen) og tålegrænsen pr. ha landbrug (målte
  kystvandets følsomhed, kunne ikke vise fremskridt).
- **Vandområder.** Ratioen landsandel/andel eksploderede ved 0% (28 kommuner på loftet 300), og en
  kommune med 10% i god tilstand blev grøn. Nu komplement-formlen: den andel der ikke er i god
  tilstand, mod landets andel.
- **Resultat:** alle 98 kommuner er røde (før 91). Det svarer til den nationale overskridelse.

### Vand

- Almene vandværker pr. indbygger målte hvor vandet pumpes op, delt med beboere der ikke bruger
  det: Furesø, Ishøj, Ringsted, Roskilde, Køge og Lejre lå i top, Rødovre, Brøndby og
  Frederiksberg i bund, og seks kommuner var filtreret fra. Industri og markvanding (53% af
  indvindingen) var udeladt.
- **Nu (25. sep. 2026):** grundvandsindvindingen (almene vandværker, virksomheder og markvanding,
  treårsgennemsnit) i procent af kommunens andel af Danmarks bæredygtige grundvandsressource. GEUS'
  nationale ressource (1.104 mio. m³ om året, rapport 2023/08, bilag 2) fordeles efter
  DK-modellens infiltration til mættet zone (HIP, 1991-2020) gange landarealet, hentet med
  `fetch_grundvandsdannelse.py`. 100 = kommunen indvinder hele sin andel. Danmark samlet ligger på
  63% (2022-2024).
- **Kontrol mod GEUS' egne tal pr. modelområde:** fordelingen rammer ressourcen på Sjælland (110
  mod 113 mio. m³), Fyn (66 mod 68-81) og Jylland (895 mod 930-1.113) inden for ca. 20%.
  Lolland-Falster (20 mod 12) og Bornholm (14 mod 2) får for stor en andel, men samme farve som hos
  GEUS. Sjælland er over 100% i begge opgørelser (144% hos os, 116% hos GEUS).
- **Kun grundvand:** DST's grundvandsindvinding 2017-2021 (737 mio. m³ om året) rammer GEUS' egen
  (734). Overfladevandet (ca. 240 mio. m³, især virksomheder som dambrug, der leder vandet tilbage)
  indgik i mellemversionen og gjorde fx Vejle og Silkeborg røde.
- **Kendte skævheder:** indvindingen registreres, hvor vandet pumpes op, så små bykommuner med
  kildepladser står meget højt (Ishøj ca. 1.430, Frederiksberg ca. 1.310) og Herlev uden indvinding
  på 0. Lokale problemer, som GEUS finder i dele af Vestjylland på grund af vandløbene, fanges kun
  delvist, fordi fordelingen følger nedsivningen. Samsø og Læsø ligger uden for DK-modellen og har
  ingen værdi.

### Arealanvendelse

- Worst-of af landbrugsandel og bebygget andel, hver mod sit landsgennemsnit, er strukturelt skævt:
  de to er hinandens spejlbillede, så næsten alle kommuner ligger over på den ene. 82 af 98 var
  røde, Frederiksberg 637.
- **Nu:** ét tal, antropiseret areal (intensivt landbrug + befæstet, pct. af landarealet uden søer
  og vandløb), den definition CONCITO bruger (Dao m.fl. 2015; EEA 2020). Danmark samlet 70,4%.
  Ratio 23-127, 56 røde, 16 grønne. Grænsen på 15% står stadig som kontekst.

### Biodiversitet

- Formlen 30/andel eksploderede ved andele nær nul og var cappet ved 300; over halvdelen af
  kommunerne stod på loftet uden indbyrdes rangorden.
- **Nu komplement-formlen:** "mindst 30% natur" er det samme som "højst 70% uden", så ratioen er
  (100 − andel)/70. Samme farver som før (4 grønne, 1 gul, 93 røde), men ingen lofter og fuld
  rangorden. 0% natur giver 143 på væsentlig og 111 på uerstattelig naturværdi.

## 3. Fælles metodegreb

- **Komplement-formlen (R2a).** Alle økologiske ratios har nu nul ved ingen belastning og 100 ved
  grænsen. Fanning m.fl. (2022) og O'Neill m.fl. (2018) normaliserer biofysiske indikatorer som
  værdi/grænse, og Richardson m.fl. (2023) tegner grænserne med Holocæn i centrum og grænsen i
  samme afstand for alle. For en andel hvor højere er bedre, er belastningen den manglende andel.
  Gælder natur, genanvendelse og vandområder. Ingen økologisk indikator har længere et loft.
- **Empirisk Bayes for andele i små områder** (pesticider). Standardgreb fra sygdomskortlægning
  (Clayton & Kaldor 1987; Marshall 1991), her som beta-binomial med momentmetoden (Kleinman 1973).
- **Treårsværdier.** Median hvor enkeltår har fejlindberetninger (affald, genanvendelse),
  gennemsnit hvor variationen er reel men vejrbestemt (markvanding, kvælstofnedfald). Samme
  funktion (`dst.rullende`) bruges af scoren og pilen.
- **Befolkningsvægtning** af eksponering (luft).

## 4. Konsekvenser

Farvefordeling (grøn/gul/rød) pr. dimension før og efter:

| Dimension | Før | Efter | Farveskift |
|---|---|---|---|
| Klimapåvirkning | 0/0/98 | 0/0/98 | 0 |
| Luftkvalitet | 0/0/98 | 0/0/98 | 0 |
| Forurening | 38/17/43 | 24/35/39 | 49 |
| Næringsstoffer | 2/5/91 | 0/0/98 | 7 |
| Biodiversitet | 4/1/93 | 4/1/93 | 0 |
| Vand | 38/15/39 (92 kommuner) | 59/7/30 (96 kommuner) | 52 |
| Arealanvendelse | 2/14/82 | 16/26/56 | 28 |

Thisted: Forurening 121 → 155 (nitrat 14,5 mg/L), Næringsstoffer 120 → 203 (Limfjorden, 203% af
målbelastningen), Vand 140 → 17 (af sin andel af ressourcen), Biodiversitet 134 → 111, Arealanvendelse 86 → 83.

Retningspile: nye pile for antropiseret areal og kvælstofnedfald (98 kommuner hver); pilene for
spildevand, intensivt og bebygget areal er væk. Næringsstoffer har kun pil i 8 kommuner, hvor
kvælstofnedfaldet afgør scoren.

## 5. Hvad der ikke kunne løses

1. **Vand: grænsen er nedskaleret, ikke GEUS' egen pr. kommune.** GEUS' ressource pr. delopland
   står i rapportens bilag 2, men deloplandenes geometri er ikke offentliggjort, og Miljøstyrelsen
   vurderer tallene usikre på den skala. Platformen fordeler derfor det nationale tal efter
   grundvandsdannelsen (se afsnit 2). **Forslag:** bed GEUS om deloplandene som GIS-lag; så kan
   ressourcen pr. delopland fordeles på kommunerne i stedet for landstallet. Grundvandsforekomsternes
   kvantitative tilstand (VP3) kan ikke bruges: kun 9 af ca. 2.000 forekomster er i ringe tilstand.
2. **Forbrugs-CO₂ er stadig et 2011-mønster.** Der findes ingen kommunefordelt forbrugsbaseret
   opgørelse efter 2011. Forskellene mellem kommuner er derfor 15 år gamle.
3. **Tålegrænsen for kvælstofnedfald er én værdi.** Den rigtige grænse afhænger af naturtypen, og
   nedfaldet er et snit over hele kommunen. Den bedre version er §3-kortet og Natura 2000-typerne
   koblet til DCE's intervaller og nedfaldet på selve naturarealerne (Miljøportalens lag
   `ID13_Luft_Deposition_2020_TotN_natur`, 400 m). Det er GIS-arbejde og kræver et valg af værdi
   inden for hvert interval.
4. **Fosfor indgår ikke.** Kystvandenes målbelastning for fosfor er sat lig baseline. Søernes
   fosformålbelastning i VP3 (`vp3_2e2025_soeoplande_inds`) er en kandidat.
5. **Statusbelastningen for kvælstof er fra 2017-2021** og opdateres først med vandområdeplan 4
   (2027). Den har ingen pil.
6. **Biodiversitet er stadig kun tilstand og politiske mål.** Bioscore-kortet er fra 2021, BII kan
   ikke nedskaleres (0,25° celler, se `docs/concito-analyse-og-roadmap.md`), og der er ingen
   presindikator for arter. Kvælstofnedfaldet dækker en del af presset, men står under
   Næringsstoffer.
7. **Vandområdernes tilstand tælles pr. styk**, ikke vægtet med længde eller areal. EEA rapporterer
   også pr. styk, men et lille vandløbsstræk tæller som en fjord.
8. **Pesticider og vandområder er relative.** Målet (nul fund, alle i god tilstand) kan ikke bruges
   som nævner.
9. **Kendte huller fra før** står uændret: jordsundhed, drænede arealer, kystpres, PFAS.

## 6. Beslutninger (25. september 2026)

Projektlederen har fulgt anbefalingerne nedenfor. Hvert valg kan vendes med én linje i registret,
men argumenterne står her, i registrets `note`-felter og i de berørte fetch-scripts, så de ikke skal
genopfindes.

- **Klimagrænsen er 2,5 ton, ikke 3.** 2,5 ton har en kilde (Hot or Cool Institute 2021:
  1,5-graders-niveauet for 2030), det har 3 ton ikke. Valget flytter ingen farver, fordi alle 98
  kommuner er røde med begge tal. Forbeholdet er, at målet er udledt for husholdningernes forbrug og
  her også bruges på det territoriale tal. Det står på metodesiden. Gå kun tilbage til 3 ton, hvis
  nogen finder en kilde til det tal.
- **Spildevandet forbliver fjernet, også som kontekst.** Spildevandet tæller stadig med, fordi det
  indgår i kystvandenes statusbelastning. Pr. indbygger i renseanlæggets kommune viser tallet, hvor
  anlægget ligger, og ikke hvem der udleder (Frederiksbergs spildevand renses i København). Kontekst
  er kun til opdelinger af et scoret tal (CLAUDE.md pkt. 9), og kommunens spildevand er ikke en
  opdeling af kystvandets samlede belastning. Skal kommunens handlerum vises, er vejen en
  kildeopdeling af belastningen pr. opland (landbrug, spildevand, regnvand); det er ikke undersøgt,
  om en sådan findes offentligt.
- **Pesticider måles som fund.** Kun 33 aktive vandværker er aktuelt over kravværdien, så med den
  afgrænsning ville næsten alle kommuner få 0, og indikatoren kunne ikke skelne dem. Fund er GEUS'
  egen hovedindikator. Et fund kan ligge under eller over kravværdien (0,1 µg/l pr. stof); et fund
  over er en overskridelse af drikkevandskravet, men de fleste fund ligger under. Kravværdien er
  fastsat politisk ud fra et forsigtighedsprincip, ikke ud fra stoffernes giftighed (Miljøstyrelsen,
  januar 2025). Det står nu på metodesiden.
- **Vand måles pr. areal og siden mod den bæredygtige ressource.** Pr. indbygger viste, hvor de
  store forsyninger har kildepladser, og udelod 53% af indvindingen. Pr. areal måler presset, hvor
  vandet pumpes op. Samme dag blev næste skridt taget: nævneren er nu kommunens andel af GEUS'
  bæredygtige grundvandsressource, fordelt efter grundvandsdannelsen i DK-modellen, frem for
  landsgennemsnittet (afsnit 2). Et 30%-kriterium direkte på DK-modellens nedsivning blev fravalgt:
  vandområdeplanernes 30% gælder grundvandsdannelsen til magasinerne, som er langt mindre end
  nedsivningen (GEUS: 104 mm/år til magasin 1 på Sjælland), så kriteriet ville have givet en for
  lempelig grænse. Landstallet fordelt efter nedsivningen svarer til ca. 7% af nedsivningen. Prisen
  er uændret de små bykommuner: Herlev har ingen indvinding og får 0, mens Ishøj, Frederiksberg og
  Furesø får ekstreme tal.
- **Tålegrænsen er 10 kg N/ha/år, og nedfaldet står under Næringsstoffer.** Valget betyder meget
  for indikatoren (5 kg: 98 kommuner over, 10: 62, 15: 2) og næsten intet for dimensionen, fordi
  kystvandet afgør Næringsstoffer i 80 kommuner og nedfaldet kun i 8. Planetary boundaries sorterer
  efter presset: kvælstofkredsløbet hører under de biogeokemiske strømme, uanset om skaden sker i
  havet eller på heden, mens biodiversitetsgrænsen måler naturens tilstand. Det følger også
  platformens princip om én grænse pr. dimension. Under Biodiversitet ville 2 kommuner skifte farve
  dér (Lyngby-Taarbæk og Fanø fra grøn til gul) og 1 på Næringsstoffer (Bornholm fra rød til gul).
- **Kystvandets kæde-regel beholdes.** Det var et valg, der ikke stod på listen. Planens
  statusbelastning for et kystvand omfatter hele oplandet opstrøms (Løgstør Bredning: 5.088 km²
  inkl. Thisted Bredning og Nissum Bredning), så kvælstof fra Thy tæller med i Løgstørs
  overskridelse. Derfor får et delopland den højeste overskridelse i sin kæde. Uden kæden ville
  Thisted ligge på ca. 177 frem for 202,7. Tallet beskriver det vand, kommunen afvander til, ikke
  kommunens eget bidrag.

## 7. Kilder

- Bak, J. (2024). Opdatering af empirisk baserede tålegrænser. DCE, fagligt notat 2024|16.
- Bobbink, R. m.fl. (2022). Review and revision of empirical critical loads of nitrogen for Europe (UNECE-luftkonventionen). Oversat til danske naturtyper i Bak (2024).
- Clayton, D. & Kaldor, J. (1987). Empirical Bayes estimates of age-standardized relative risks for use in disease mapping. Biometrics 43:671.
- CONCITO (2025). Downscaling the planetary boundaries to national level - the case of Denmark.
- Dao, H. m.fl. (2015). Environmental limits and Swiss footprints based on Planetary Boundaries. UNEP/GRID-Geneva og Université de Genève.
- DCE (2024). Atmosfærisk deposition 2023. Videnskabelig rapport nr. 626.
- DCE, depositionsberegninger pr. kommune (DEHM), www2.dmu.dk.
- European Environment Agency (2020). Is Europe living within the limits of our planet? (CONCITO's reference 2020a), https://www.eea.europa.eu/en/analysis/publications/is-europe-living-within-the-planets-limits.
- Energistyrelsen (2026). Danmarks globale klimapåvirkning - Global afrapportering 2026, datafil "Forbrug".
- Fanning, A.L., O'Neill, D.W., Hickel, J. & Roux, N. (2022). The social shortfall and ecological overshoot of nations. Nature Sustainability 5:26-36.
- GEUS: Henriksen, H.J., Ondracek, M. & Troldborg, L. (2023). Vandressourceopgørelse - datarapport. GEUS rapport 2023/08.
- GEUS Jupiter (WFS `jupiter_anlaegsanalyser`, `jupiter_grp_anlaegsanalyser`).
- Hot or Cool Institute (2021). 1.5-Degree Lifestyles: Towards a Fair Consumption Space for All.
- Hydrologisk Informations- og Prognosesystem (HIP), Klimadatastyrelsen og GEUS: DK-modellen version 2023, infiltration til mættet zone 1991-2020 (WMS `hip_boundary_conditions_period_mean`, lag `infiltration`). https://hip.dataforsyningen.dk
- Kleinman, J.C. (1973). Proportions with extraneous variance: single and independent samples. Journal of the American Statistical Association 68:46-54.
- Marshall, R.J. (1991). Mapping disease and mortality rates using empirical Bayes estimators. Applied Statistics 40:283.
- Miljøstyrelsen (2023). Forvaltning af fremtidens drikkevandsressource.
- Miljøstyrelsen (2025). Befolkningen kan have tillid til den danske vandforsyning. Nyhed, januar 2025. https://mst.dk/nyheder/2025/januar/befolkningen-kan-have-tillid-til-den-danske-vandforsyning
- O'Neill, D.W., Fanning, A.L., Lamb, W.F. & Steinberger, J.K. (2018). A good life for all within planetary boundaries. Nature Sustainability 1:88-95.
- Richardson, K. m.fl. (2023). Earth beyond six of nine planetary boundaries. Science Advances 9:eadh2458.
- Styrelsen for Grøn Arealomlægning og Vandmiljø (2026). Vandområdeplanerne 2021-2027 efter genbesøget, revideret april 2026, bilag 1.1.
- WHO (2021). Global air quality guidelines.
