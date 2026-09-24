# Offentlig transport pr. kommune, genskabt fra åbne data

Undersøgt september 2026. Script: `scripts/fetch_offentlig_transport.py`. Resultat: `data/offentlig_transport_scores.csv`.

Intet er koblet på platformen endnu. Planen står nederst og kræver en beslutning.

## Kort version

Platformens `public_transport` er DST's tal for fem kommunegrupper, stemplet på hver kommune i gruppen. Det giver fem forskellige værdier fordelt på 98 kommuner, og i standardvisningen (kommunegruppe-baselinen) får alle 98 kommuner præcis 100.

Vi har genskabt DST's metode pr. kommune med tre åbne kilder: Rejseplanens køreplaner, DAR-adresser og Eurostats befolkningsgrid. Lægger man kommunetallene sammen til de fem grupper, rammer de DST's egne tal med 1,2 procentpoint i gennemsnit.

## Problemet med den nuværende indikator

LABY49 findes kun for fem kommunegrupper. Alle 31 landkommuner står derfor til 9,91 %, og indikatoren kan ikke skelne Thisted fra Fanø eller Svendborg.

Det er værre i standardvisningen. `computeGroupRatios()` i `shared.ts` dividerer hver kommunes ratio med gruppens gennemsnit. Når alle i gruppen har samme tal, bliver resultatet 100,0 for hver eneste kommune (kontrolleret mod `master_indicators.csv`). Mobilitet er dermed reelt pendlingsafstand plus en konstant på 100.

## DST's metode

Fra DST's side om verdensmål 11.2.1 og boks 1 i analysen [Har adgang til offentlig transport betydning for om man har bil?](https://www.dst.dk/da/Statistik/nyheder-analyser-publ/Analyser/45984-har-adgang-til-offentlig-transport-betydning-for-om-man-har-bil):

- Beregnet fra alle bopælsadresser (CPR) sammen med Styrelsen for Dataforsyning og Effektivisering.
- 500 m til fods ad vejnettet (GeoDanmark).
- Afgange i timen på en typisk arbejdsdag kl. 6-20, fra Rejseplanens stoppestedsdata. Flextrafik, telebusser og vinkestrækninger tæller ikke med.
- Serviceniveauer: meget højt (mindst 10 afgange og mere end én transporttype), højt (mindst 10), middel (4-9), lavt (under 4), intet (intet stoppested inden for 500 m).

Platformen bruger højt + meget højt, altså mindst 10 afgange i timen.

DST bygger på EU-Kommissionens rapport [Measuring access to public transport in European cities](https://ec.europa.eu/regional_policy/sources/work/2015_01_publ_transp.pdf) (Poelman og Dijkstra, 2015). Hverken DST eller rapporten siger præcist, hvordan afgange fra flere stoppesteder tælles. Det måtte findes ved test.

## Sådan er det genskabt

| | DST | Genskabt |
|---|---|---|
| Bopæl | CPR-adresser | DAR-adresser vægtet med Eurostats folketælling 2021 på 1 km-grid |
| Afstand | 500 m ad vejnettet | 340 m i fugleflugt |
| Køreplan | Rejseplanen, typisk hverdag i marts | Rejseplanens GTFS, én typisk hverdag valgt af scriptet |
| Frekvens | afgange i timen kl. 6-20 | summen af afgange i timen fra alle stop inden for rækkevidden |
| Behovsstyret kørsel | udeladt | rutetype 715 udeladt (156 ruter i feedet) |

**Afgange.** Scriptet vælger den tirsdag, onsdag eller torsdag i feedens første otte uger, hvis antal ture ligger tættest på medianen. Ferieuger har færre ture og falder fra af sig selv (efterårsferien 2026 havde ca. 38.600 ture mod normalt 42.700). Endestationer tæller ikke som afgang, og det gør stop med `pickup_type=1` heller ikke.

**Afstand.** 340 m er kalibreret alene på andelen uden stoppested ("intet"), fordi frekvensreglen ikke spiller ind dér. Resten af valideringen er altså ikke tilpasset. Om man vælger 320 eller 360 m, ændrer næsten intet i kommunernes rækkefølge (rangkorrelation 0,999).

**Frekvensreglen.** Tre fortolkninger blev testet ved den radius, hvor "intet" passer:

| Regel | Højt+ i de fem grupper (DST: 68,4 / 53,1 / 30,8 / 13,9 / 9,9) | Gns. afvigelse, alle niveauer |
|---|---|---|
| Bedste stoppested (stop under 50 m slået sammen, som i EU-rapporten) | 51,2 / 32,4 / 10,7 / 3,3 / 1,7 | 9,5 pp |
| Unikke ture inden for rækkevidden | 59,9 / 43,7 / 16,0 / 4,6 / 2,2 | 6,1 pp |
| **Sum af afgange fra alle stop inden for rækkevidden** | **70,6 / 54,1 / 30,0 / 11,9 / 7,6** | **1,2 pp** |

Summen vinder klart. En bus tæller altså ved hvert stop, den kører forbi inden for 500 m af boligen. Det er sandsynligvis sådan DST's netværksberegning er bygget: hvert stops afgange lægges til alle adresser i stoppets gangzone.

**Befolkning.** 3,94 mio. gældende adresser giver 2,61 mio. adgangspunkter. Hver 1 km-celles registrerede befolkning (folketælling 2021) fordeles ligeligt på cellens adresser. Sommerhus- og erhvervsområder har få registrerede beboere og får derfor lav vægt. Kun 608 personer bor i celler uden adresser. 84 celler ved grænsen deles med Tyskland (3.377 personer); dem regner vi som danske.

Resultatet pr. kommune passer med DST's folketal: København 634.000, Aarhus 351.500, Aalborg 219.000.

## Validering

Scriptet gentager denne sammenligning ved hver kørsel og advarer, hvis den gennemsnitlige afvigelse overstiger 3 procentpoint.

| Kommunegruppe | Intet | Lavt | Middel | Højt+ |
|---|---|---|---|---|
| Hovedstad | 10,0 / 12,0 | 5,8 / 5,9 | 13,5 / 13,4 | 70,6 / 68,4 |
| Storby | 17,3 / 18,8 | 9,6 / 9,3 | 19,1 / 18,4 | 54,1 / 53,1 |
| Provinsby | 24,8 / 25,4 | 23,2 / 22,8 | 22,0 / 20,8 | 30,0 / 30,8 |
| Opland | 33,1 / 32,0 | 34,2 / 34,0 | 20,9 / 19,9 | 11,9 / 13,9 |
| Land | 36,6 / 33,2 | 39,3 / 38,5 | 16,6 / 18,3 | 7,6 / 9,9 |

Genskabt (køreplan 30. september 2026) / DST LABY49 2025. Procent af befolkningen.

Der er én systematisk rest. Hovedstaden ligger lidt for højt og landkommunerne lidt for lavt. Den sandsynlige årsag er fugleflugten: i byer er omvejen ad vejnettet større end i gennemsnittet (karréer, jernbaner), på landet mindre (boligen ligger ofte ved den vej, bussen kører på). Afstanden mellem by og land bliver dermed 2-3 procentpoint for stor i yderpunkterne. Rækkefølgen inden for en gruppe påvirkes ikke.

## Resultater

Landstallet for Danmark som helhed er 37,0 %. Kommunerne får 87 forskellige værdier mellem 0 % og 95,7 % (Frederiksberg).

| Gruppe | Lavest | Median | Højest |
|---|---|---|---|
| Hovedstad (24) | Egedal 16,9 | 57,9 | Frederiksberg 95,7 |
| Storby (3) | Odense 46,9 | 47,2 | Aarhus 62,6 |
| Provinsby (16) | Holstebro 2,0 | 29,9 | Helsingør 55,0 |
| Opland (24) | Vejen 1,6 | 8,6 | Ringsted 36,8 |
| Land (31) | Fanø 0,0 | 4,3 | Svendborg 19,6 |

Seks kommuner får 0 %: Ærø, Fanø, Lemvig, Norddjurs, Samsø og Læsø. Ingen bolig har mindst 10 afgange i timen inden for rækkevidde.

Thisted får 7,35 % mod 9,91 % i dag. Fordelingen er middel 13,7 %, lavt 40,3 % og intet 38,6 %. Thisted ligger over landkommunernes median.

Holstebro på 2,0 % er efterprøvet, fordi tallet virker lavt for en by med 37.000 indbyggere. Trafikterminalen har ca. 7 busafgange i timen fordelt på fire perroner, og stationen 4,9. Kun boliger tæt på centrum når over 10.

## Krydstjek mod Dansk Mobilitetsatlas

[Mobilitetsatlasset](https://mobilitetsatlas.dk) (Beta Mobility) beregner rejsetider med en rigtig ruteplanlægger. Deres tal ligner vores:

- Rangkorrelation 0,89 mellem vores andel med mindst 10 afgange og deres "kollektiv kvalitet".
- Rangkorrelation 0,95 mellem vores "intet" og deres andel uden kollektiv betjening. Thisted: 38,6 % mod deres 35,9 %.

Atlassets data kan stadig hentes via siden `/udforsk` med HTTP-headeren `RSC: 1`. De statiske GeoJSON-filer, vi fandt i august, svarede 404 både 19. august og 24. september. Vi bruger ikke atlassets tal:

1. **Metoden skifter.** Mellem august og september 2026 skiftede 74 af 98 kommuner mærke, og antallet af A-kommuner gik fra 1 til 22. Thisted gik fra G til E. I august var deres formel præcis denne (kontrolleret til 0,005): kollektiv kvalitet = min-max af `o_pt` over de 98 kommuner, og samlet score = gennemsnittet af kollektiv kvalitet og 100 × (1 − `cdi`). I september holder den ikke længere.
2. **Licensen er CC BY-SA 4.0**, og platformens licens er ikke afklaret (se README).
3. **Ingen tidsserie**, og ingen lovning på at stierne består.

At genskabe atlassets egen rejsetidsmodel ville kræve en ruteplanlægger (fx R5 via r5py) med køreplaner og vejnet for hele landet, plus et datasæt over hverdagsdestinationer. Det er flere timers beregning pr. kørsel og en Java-opsætning. Med en rangkorrelation på 0,89 til den enkle metode er det ikke pengene værd for platformen.

## Begrænsninger

- **Fugleflugt i stedet for vejnet.** Giver resten beskrevet under validering. Med GeoDanmarks eller OpenStreetMaps vejnet kunne man regne DST's 500 m direkte og droppe kalibreringen på 340 m.
- **Befolkningen er fra 2021** og fordeles ligeligt på adresserne i en celle. Blander en celle sommerhuse og helårsboliger, får sommerhusene for meget vægt.
- **Én hverdag om efteråret.** DST bruger marts. Scriptet advarer, hvis det vælger en dato i sommerkøreplanen (25. juni til 15. august), for så bliver tallene for lave.
- **Meget højt skilles ikke ud.** Det kræver en regel om flere transporttyper, og platformen bruger højt + meget højt samlet.
- **DAWA.** Adresserne hentes fra Dataforsyningens DAWA-API. Lukker det, findes de samme adresser i Datafordeleren (DAR), som kræver en gratis bruger.

## Kilder og kreditering

- Rejseplanen GTFS, CC BY 4.0. "Indeholder kollektivtrafikdata fra Rejseplanen."
- Danmarks Adresseregister (DAR) via Dataforsyningen, frie data.
- Eurostat, [Census 2021 population grid](https://ec.europa.eu/eurostat/web/gisco/geodata/population-distribution/population-grids), © European Union. `data/befolkning_1km_2021_dk.csv` er de danske celler (38.870 celler med beboere), udtrukket af scriptet.
- DST LABY49, kun til validering.

Alle fire kilder kræver kun kreditering.

## Plan for at koble det på

Kræver din beslutning. Intet af dette er gjort.

1. **Registret.** `public_transport` i `data/indikatorer.json` peger på `offentlig_transport_scores.csv` med `raw_col: public_transport_raw` og `reference: {type: landstal, col: public_transport_ref}`. Kilde og `rationale` opdateres, og `note` om kommunegrupperne fjernes. Scriptets kolonner er lavet til netop det.
2. **Dataår.** Scriptet skal kvittere i `data/data_years.json` (køreplanens år) og kalde `auto_build_master()`. Det er udeladt nu, så en kørsel ikke kan ændre sitet.
3. **`fetch_social_new_data.py`** holder op med at hente LABY49 til scoren. Tabellen bruges fortsat til validering i det nye script.
4. **Metodesiden** får ny beregningstekst for Mobilitet, og `data/CHANGELOG.md` en note.
5. **Forventede ændringer.** Med landsgennemsnits-baselinen skifter 16 kommuner farve. I kommunegruppe-baselinen går indikatoren fra 98 grønne til 47 grønne, 9 gule og 42 røde. De seks kommuner med 0 % får ratio 0.
6. **Retningspil senere.** Rejseplanen har et GTFS-arkiv siden december 2025. Fra 2027 kan scriptet køres på to årgange og give en pil.

Et åbent valg: tærsklen. Mindst 10 afgange i timen er DST's og FN's "god adgang" og det platformen måler i dag. Den giver 0 % i seks kommuner og skiller landkommunerne dårligt ad (median 4,3 %). En tærskel på 4 afgange ("middel eller bedre") ville skelne bedre på landet, men så afviger platformen fra DST's definition. Min anbefaling er at beholde 10 og vise fordelingen på alle fire niveauer, hvis kommunesiden en dag får plads til det.
