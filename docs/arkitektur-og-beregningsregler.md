# Arkitektur og beregningsregler

Dette dokument beskriver de normative regler bag scoringen i "Danmarks 98
Doughnuts". Reglerne er projektets faglige kerne. En port til en anden platform,
en videreudvikling eller en regional tilpasning skal reproducere dem præcist,
ellers ændrer man tallene uden at opdage det.

Reglerne er implementeret i `scripts/build_master_csv.py` (datapipelinen),
`scripts/build_trends_csv.py` (retningspile) og `webapp/lib/shared.ts`
(frontendberegninger). Hvilke indikatorer der findes, og deres egenskaber
(retning, kategori, mål, særregler), står ét sted: `data/indikatorer.json`.
Alle tre læser derfra, Python via `scripts/indikatorregister.py`. Dokumentet
angiver bevidst funktions- og feltnavne frem for linjenumre, fordi linjenumre
skrider ved hver ændring.

**Læs afsnit 6 og 7 før du ændrer noget.** Fælderne dér er alle sammen fejl
projektet allerede har begået én gang.

---

## 1. Grundlæggende talkonvention

Alle indikatorer udtrykkes som en **ratio** hvor 100 er referencepunktet:

- **Sociale indikatorer:** 100 = niveau med landsgennemsnittet (eller med et
  absolut mål, se R3). Højere er bedre.
- **Økologiske indikatorer:** 100 = på grænsen, enten en absolut grænse eller
  landsgennemsnittet hvor der ikke findes en meningsfuld grænse pr. kommune
  (se R12). Lavere er bedre, og over 100 er overshoot.

Indikatorer hvor en høj råværdi er dårlig (Gini, kriminalitet, luftforurening)
vendes af formlen i R2, så ratio-retningen er ensartet. Feltet
`inverse` (sociale) og `lower_is_better` (økologiske) i registret registrerer
hvilke det gælder.

De to retninger er modsatrettede med vilje. Det er den hyppigste fejlkilde i
projektet, se R11.

---

## 2. Transformationsregler (datapipeline)

Reglerne herunder ligger i `scripts/build_master_csv.py` og udføres når
rådata-CSV'erne konsolideres til `data/master_indicators.csv`.

**R1 - Social ratio-cap.** Sociale ratios cappes ved 150,0. Formålet er at
forhindre at en enkelt ekstremværdi dominerer kategorigennemsnittet. Cappet
gælder alle sociale indikatorer, også dem der slås op på kommunenavn (R5).
Top 10%- og kommunegruppe-baselinen lægger samme loft på igen efter
omskaleringen (R9, R10), så en social ratio er højst 150 i alle tre visninger.

En social indikator kan have et lavere loft i registret (`cap`, fra sep. 2026).
Det bruges kun, hvor fravær af en belastning ellers ville blive belønnet:
`kystrisiko` har loftet 100, så en kommune uden eller med lav kystrisiko står
neutralt. Med 150 ville en kommune uden kyst få en bonus, der i Klimatilpasnings
gennemsnit udligner dens vejrskader (Holstebro gik fra rød til grøn). Loftet
gælder i alle tre visninger (`Indicator.loft` i `shared.ts`, `_loft()` i
`build_master_csv.py` og kontrolkopien i `data.ts`), og registret afviser et
socialt `cap` over 150.

Konsekvens for visningen: for en kappet kommune kan referenceværdien ikke
udledes baglæns af ratio og råværdi. `ScoreBars` viser derfor ikke
"Landsgns"/gruppe-værdien ved indikatorer hvor kommunens ratio er 150, hverken
i pipelinen eller efter omskaleringen til den valgte baseline.
Referencen står i masterfilens `reference`-kolonne (R3).

**R2 - Ratio beregnes ét sted, med én formel.** `beregn_ratio()` i
`build_master_csv.py` beregner alle sociale og økologiske ratios ud fra
råværdien og indikatorens reference i `data/indikatorer.json`. Retningen
følger registret:

| Indikator | Formel |
|---|---|
| social, `inverse: false` | `raw / ref × 100` |
| social, `inverse: true` | `ref / raw × 100` |
| økologisk, `lower_is_better: true` | `raw / ref × 100` |
| økologisk, `lower_is_better: false` | `ref / raw × 100` (bruges ikke længere, se R2a) |
| økologisk, `formula: "komplement"` | `(100 - raw) / (100 - ref) × 100` |
| `formula: "100_minus_raw"` (kun `bolig_fossil`) | `100 - raw` (mål 0 procent fossil) |

Resultatet klippes (R1, R6) og afrundes til 2 decimaler. Indtil sep. 2026
regnede hvert fetch-script sin egen ratio, og `build_master_csv.py` havde tre
særregler oveni: `10000/x` for økologiske ratios leveret på inverteret skala
(N, P, affald), `65/pct` for genanvendelse og `raw/3` for forbrugs-CO2. De er
alle erstattet af tabellen ovenfor. Fetch-scriptets egen ratio (`ratio_col`)
indgår ikke længere i scoren; den bruges til krydstjek (build advarer ved
afvigelser over 0,5 point) og til R3's rekonstruktion.

**R2a - Økologiske andele hvor højere er bedre regnes om til det der mangler
(fra sep. 2026).** Alle økologiske ratios skal have nul ved ingen belastning og
100 ved grænsen. Det er Fanning m.fl.s (2022) og O'Neills m.fl.s (2018)
normalisering, værdi/grænse, for størrelser med et naturligt nulpunkt, og
Richardson m.fl. (2023) tegner de planetære grænser på samme måde (Holocæn i
centrum, grænsen i samme afstand for alle). For en andel hvor højere er bedre
(natur, genanvendelse, vandområder i god tilstand) er belastningen den
manglende andel. Målet "mindst 30 procent natur" er det samme som "højst 70
procent uden", og ratioen er den manglende andel målt mod det målet tillader:
`(100 - raw) / (100 - ref) × 100`. Med en landstal-reference (vandområder) er
det den manglende andel mod landets manglende andel.

Indtil sep. 2026 brugte de fire indikatorer `ref / raw × 100`. Den eksploderer,
når andelen nærmer sig nul, og måtte cappes ved 300 (R6): over halvdelen af
kommunerne stod på loftet på biodiversitet, 28 kommuner på vandområder, og en
kommune med 10 procent vandområder i god tilstand blev grøn, selv om 90
procent ikke var det. Formlen gælder `bio_vasentlig`, `bio_uerstattelig`,
`cirkularitet_recycling` og `overfladevand`. Registret afviser `komplement` på
andet end økologiske indikatorer med `lower_is_better: false`.

**R3 - Referencen.** Feltet `reference` i registret har tre typer:

- `maal`: et fast mål (`value`). Uddannelse 95 procent, WHO's
  luftkvalitetsgrænser, 2,5 ton CO2e (indtil sep. 2026 3 ton, uden kilde), EU's
  65 procent genanvendelse og 30/10 procent natur, 6 mg/L nitrat, 0 procent
  fossil varme, kystvandenes målbelastning for kvælstof (100 procent),
  tålegrænsen for kvælstofnedfald (10 kg N/ha/år) og kommunens andel af den
  bæredygtige grundvandsressource (100 procent, se afsnit 5).
- `kommunegennemsnit`: uvægtet gennemsnit af kommunernes råværdier, beregnet
  ved build. Bruges i dag af ingen indikator. De fire UVM-indikatorer brugte
  typen indtil sep. 2026 og vægtes nu med folkeskoleelever efter
  bopælskommune (DST UDDAKT20).
- `landstal`: fetch-scriptets referenceværdi. Feltet `definition` siger hvordan
  den er fundet. Scriptet skriver den i kolonnen `col`. Mangler kolonnen (en
  CSV der ikke er hentet siden sep. 2026), rekonstrueres landstallet ved
  hvert build fra scriptets egen ratio: medianen af `raw × 100 / ratio`
  (eller `raw × ratio / 100` for omvendt retning) over kommunerne, afrundet
  til færrest mulige decimaler uden at ramme færre af scriptets ratios. Det
  genskaber publicerede landstal som 81,6 år eksakt.

Referencen skrives til masterfilens `reference`-kolonne for hver række.

**Landsgennemsnit betyder Danmark som helhed (besluttet sep. 2026).** Et
landstal er de 98 kommuner samlet, vægtet med indikatorens egen nævner:
samlet antal delt med samlet befolkning for tal pr. indbygger, samlet areal for
arealandele, osv. Det er ikke et uvægtet gennemsnit af kommunerne, og ikke
kildens hele-landet-række, hvis den indeholder tal uden kommune. Tal pr.
indbygger regnes i `dst.pr_indbygger()`, som danner landstallet af kommunerne
selv. Det betyder noget for kriminalitet, hvor 8,7 procent af anmeldelserne
(2025) ikke har en kendt gerningskommune, og underretninger, hvor DST's landstal
tæller 3,1 procent færre end kommunerne tilsammen. For andele og gennemsnit fra
DST (fx fattigdom, klassekvotient) bruges DST's hele-landet-tal, som for de
undersøgte tabeller er det samme som kommunerne samlet.

Begrundelse: standardvisningen (kommunegruppe) og top 10 dividerer med et
uvægtet gennemsnit af ratioerne, så landstallet påvirker dem ikke. Det har kun
betydning i landsgennemsnit-visningen og for de økologiske indikatorer, der
måles mod gennemsnit. Landsgennemsnit-visningen skal derfor være den anden
sammenligning, altså Danmark som helhed, og ikke en variant af den typiske
kommune. Det er også det tal en læser kan slå op hos kilden.

**R4 - Nul i nævneren.** Er råværdien 0 for en indikator med `ref / raw`,
er det for en social indikator det bedst mulige og giver loftet 150. For en
økologisk er det det værst mulige og giver indikatorens `cap`, eller ingen
værdi hvis den ikke har et. Mangler råværdien, er der ingen ratio.

**R5 - Kommunenøgle.** Alle kilde-CSV'er slås op på `kommune_kode`, og
platformens kommuner er de 98 i `data/kommuner.json` (Christiansø er ikke
med). To kilder har kun navne: `forbrug_co2` (`cba_2023_estimate.csv`,
håndlavet) og `vejr_skader` (`klimatilpasning_scores.csv`). Indtil sep. 2026
blev de slået op på navn i build-trinnet, så en stavevariant gav et tavst hul.
Nu har begge CSV'er en `kommune_kode`-kolonne; fetch-scriptet slår koden op
med `kommuner.kode_for_navn()` og stopper ved et ukendt navn. En kommune uden
række i CSV'en får ingen værdi, og der er bevidst intet fallback.

**R6 - Økologisk ratio-cap (`cap`).** Sætter en økologisk indikator feltet `cap`,
klippes ratio til den værdi. Fra sep. 2026 har ingen indikator et cap: de tre
der havde (`overfladevand`, `bio_vasentlig`, `bio_uerstattelig`, alle 300), bruger
nu komplement-formlen (R2a), som ikke kan eksplodere. Mekanismen er bevaret i
koden til en fremtidig indikator, men et loft som over halvdelen af kommunerne
rammer, er et tegn på en forkert formel, ikke på et manglende loft.

**R7 - Økologisk dimensionsscore.** Pr. kommune og dimension samles alle
ikke-`None` sub-ratios:

- **worst-of (standard):** `score = round(max(ratios), 2)`
- **gennemsnit:** `score = round(sum / len, 2)`, kun for dimensioner med
  `"aggregation": "gennemsnit"` i registret

Det gælder i dag **udelukkende `forurening`**. Begrundelsen
er at dens fire indikatorer måler vidt forskellige forureningstyper, hvor
worst-of ville lade den værste enkeltkilde definere hele dimensionen.

Alle andre dimensioner bruger worst-of. Det er bevidst planetary
boundary-logik: overskrides bare én delgrænse, er dimensionen overskredet.
Gennemsnit ville lade en god delindikator maskere en overskredet grænse.

Uden nogen sub-ratios er scoren `None`. Resultatet skrives til masterfilen som
rækker med `indicator_id = "_dim_<dimension>"`.

**R14 - Ratiovalidering.** Gyldigt interval er 0 til 2000. Værdier udenfor
rapporteres som en advarsel ved build, men klippes ikke. Intervallet er sat
bevidst bredt. Enkelte kommuner ligger højt over 100 af reelle grunde
(grundvandsindvindingen i Ishøj og på Frederiksberg er 13-14 gange kommunens
andel af den bæredygtige ressource, fordi kildepladserne ligger på et lille
areal).

---

## 3. Frontendberegninger

Reglerne herunder ligger i `webapp/lib/shared.ts` og udføres ved indlæsning i
browseren, ikke i pipelinen.

**R8 - Social kategoriscore.** `computeCategoryScores()` tager et simpelt,
uvægtet gennemsnit af de ikke-`null` indikator-ratios i kategorien. Har ingen
indikator data, er scoren `null`, og `hasData` bliver `false`.

Bemærk at kategorien altid rapporterer `indicatorCount` som antallet af
indikator-id'er i definitionen, uanset hvor mange der faktisk havde data.

**R9 - Top10-baseline.** `computeTop10Ratios()` omskalerer sociale indikatorer
så 100 svarer til gennemsnittet af de ti bedste kommuner:

1. Kommuner med `kommune_kode === "000"` udelades af beregningen. Koden er
   reserveret til et Danmark-aggregat.
2. Har indikatoren `absoluteScore: true`, kopieres ratio uændret (se R15).
3. Findes der færre end 10 gyldige værdier, kopieres ratio uændret.
4. Ellers sorteres alle ratios faldende, gennemsnittet af de 10 højeste
   beregnes, og `ny ratio = Math.min(parseFloat(((ratio / top10Avg) * 100).toFixed(2)), 150)`.
   Loftet er R1's (`SOCIAL_LOFT` i `shared.ts`). Det ændrer ingen tal i dag,
   hvor den højeste top 10-ratio er 124,2, men holder reglen ens i de tre visninger.
5. Er kommunens ratio `null`, eller er `top10Avg` nul, bliver resultatet `null`.

Højeste ratio er altid den bedste præstation, også for inverse indikatorer,
fordi de allerede er vendt i kildedataene.

**R10 - Kommunegruppe-baseline.** `computeGroupRatios()` fungerer som R9, men
med DST's kommunegrupper G1-G5 (`KOMMUNEGRUPPE`) som reference i stedet for
top 10. Gruppegennemsnittet er uvægtet. `absoluteScore`-indikatorer kopieres
uændret. Resultatet er `null` hvis kommunens ratio er `null`, hvis kommunen
ikke findes i gruppemappingen, eller hvis gruppegennemsnittet er nul.

Loftet på 150 gælder også her (fra sep. 2026) og lægges på efter
omskaleringen. En ratio kan altså være klippet to gange: mod landsgennemsnittet
i pipelinen (R1) og mod gruppesnittet her. Uden det andet loft kunne en kommune
langt over sit gruppesnit komme over 300: landkommunernes snit for offentlig
transport er ca. 6 %, så Svendborg fik 338 på indikatoren og 214,7 på hele
Mobilitet, mens ingen kategori kan nå over 150 i landsgennemsnit-visningen.

**R11 - Farvetærskler.** Retningen er modsat mellem de to halvdele af
doughnutten, og det er den fejl der oftest bliver begået:

| | Grøn | Amber | Rød |
|---|---|---|---|
| **Social** (`scoreColor`, `scoreBarColor`) | `>= 100` | `>= 85` | `< 85` |
| **Økologisk** (`ecoScoreColor`, `ecoBarColor` i `ScoreBars.tsx`) | `<= 85` | `<= 100` | `> 100` |

Sociale scorer skal op mod fundamentet. Økologiske skal ned under loftet.

**R12 - Baselinetype.** Hver indikator klassificeres som scoret mod et absolut
mål eller mod landsgennemsnittet:

- Social indikator: `absolut` hvis `absoluteScore`, ellers `relativ`
  (`indicatorBaselineType`).
- Økologisk sub-indikator: læses fra feltet `baselineType`.
- Dimension eller kategori: er alle underliggende typer ens, arves den type.
  Ellers `blandet`. En tom liste giver `relativ`
  (`categoryBaselineType`, `dimensionBaselineType`).

I dag er Uddannelse, Forurening og Næringsstoffer `blandet` (Næringsstoffer:
kvælstof til kystvande og kvælstofnedfald mod faste grænser, vandområdernes
tilstand mod landsgennemsnittet). UI'et viser mærket "mod mål"
eller "blandet" på dimensionsbjælken. Relativ vises uden mærke og forklares i
ringens legende.

Reglen for hvornår man vælger hvad: scor mod et fast mål hvor der findes en
meningsfuld grænse pr. kommune (WHO, EU, 0 procent fossil, 95 procent
uddannelse), ellers mod landsgennemsnittet.

**R13 - `null` betyder noget andet end manglende nøgle.** I `KommuneData` skal
**alle** aktive indikatorer have en nøgle i `ratios`, og **alle**
øko-dimensioner en nøgle i `eco_ratios`, med værdien `null` hvor der ikke er
data. `webapp/lib/data.ts` initialiserer dem eksplicit.

UI'et skelner mellem `null` (indikatoren findes, men afventer data) og
`undefined` (indikatoren findes ikke) når det tæller "afventer data". Fjerner
man initialiseringen, forsvinder tællingen lydløst.

**R15 - Baseline-toggle rammer kun den sociale halvdel.** Skift mellem
gennemsnit, top 10 og kommunegruppe påvirker udelukkende sociale indikatorer.
Økologiske dimensioner har faste referencer, enten en absolut grænse eller
landsgennemsnittet, og ændres aldrig af toggle. `absoluteScore`-indikatorer omskaleres heller ikke, selvom de er
sociale.

---

## 4. Retningspile

Retningspilene er et selvstændigt dataspor ved siden af scoringen, med sin egen
pipeline: `fetch_trend_history.py` henter tidsserier, `build_trends_csv.py`
beregner retninger til `data/trend_indicators.csv`. Sporet kom til i august
2026, efter at reglerne i afsnit 2 og 3 var etableret.

**Begge filer skal genberegnes og committes sammen.** Opdaterer man
`master_indicators.csv` uden `trend_indicators.csv`, viser platformen en pil der
peger på et tal den ikke længere hører til.

**T1 - Retning beregnes altid på råværdier, aldrig på ratio.** Ratio afhænger af
baseline-toggle, så en ratio-baseret pil ville skifte retning når brugeren
skiftede baseline.

**T2 - Endepunkter.** `endepunkter()` bruger de enkelte start- og slutår hvis
serien er kortere end `MIN_AAR_FOR_GENNEMSNIT` (6 år). Ellers midles de første
og sidste `N_ENDEPUNKT` år, så et enkelt afvigende år ikke definerer retningen.

**T3 - Klassifikation.** `klassificer()` returnerer én af seks værdier:

| Retning | Betingelse |
|---|---|
| `ingen` | ingen procentændring kunne beregnes |
| `stagneret` | ændringen er ubetydelig, se T4 |
| `kontekst` | indikatoren har ingen retning i registret (kontekst-indikator eller ukendt id), så retning kan ikke vurderes |
| `forkert` | den målrettede ændring er nul eller negativ |
| `rigtig` | målrettet ændring mindst lige så god som medianen af alle 98 kommuner |
| `tempo` | rigtig vej, men langsommere end medianen |

Sammenligningen med medianen sker **med fortegn** på den målrettede skala. Med
absolutte tal ville en kommune der forbedrer sig 5 procent, mens landets median
forværres 8 procent, blive stemplet "tempo" for langsom, selvom den bevæger sig
den rigtige vej og de fleste andre den forkerte.

**T4 - Ubetydelig ændring.** `ubetydelig()` er sand når niveauet er mindst 10 og
den absolutte ændring er under 1 i indikatorens egen enhed. Derudover
klassificeres alt under 1 procents relativ ændring som `stagneret`.

**T5 - Pilens retning udledes af scoringens retning.** `op_er_godt` (om en
stigende råværdi er fremgang) er `not inverse` for sociale og
`not lower_is_better` for økologiske indikatorer, udledt af registret i
`indikatorregister.op_er_godt()`. Indtil sep. 2026 var det en separat,
håndvedligeholdt konstant (`OP_ER_GODT`) der skulle holdes i sync med
`inverse`, og den skred. Et id i tidsserien som registret ikke kender, bliver
til `kontekst` (pil uden vurdering); `tjek_konsistens.py` melder det som fejl,
og `build_trends_csv.py` skriver en ADVARSEL-linje.

**T6 - Dimensionspilen følger worst-of, ikke gennemsnittet.** En øko-dimensions
pil er retningen for den sub-indikator der bestemmer dimensionens score, altså
den med højeste ratio. Tager man gennemsnittet af sub-retningerne, kan
dimensionen vise grøn pil samtidig med at netop den overskredne grænse bliver
værre.

Undtagelsen er `forurening`, som bruger gennemsnit i scoren (R7) og derfor også
i retningen. Begge scripts læser `aggregation` fra registret, så score og pil
ikke kan komme ud af trit.

Har den afgørende sub-indikator ingen tidsserie, får dimensionen **ingen pil**.
Der falles bevidst ikke tilbage på de øvrige. Derfor har `klimapaavirkning` kun
pil i 11 af 98 kommuner: i de øvrige 87 afgøres scoren af forbrugsbaseret CO2,
som ikke findes som tidsserie. Det er korrekt opførsel, ikke manglende data.
Tilsvarende har `naeringsstoffer` kun pil, hvor kvælstofnedfaldet afgør scoren
(8 kommuner, sep. 2026): statusbelastningen af kystvandene kommer fra
vandområdeplanen og har ingen tidsserie, og det samme gælder vandområdernes
tilstand.

**T7 - Pilens retning betyder to forskellige ting, og `pct` gør det samme.**
Reglen bor i `trendPilOpad()` i `shared.ts`. Alle visninger skal bruge den. Lav
aldrig `pct >= 0` direkte i en komponent.

- **Enkeltindikator:** pilen følger råværdiens faktiske ændring, og `pct` er den
  rå ændring. Det giver det nuancerede billede: inden for Forurening peger
  genanvendelse op i grønt og affald op i rødt, samme retning, modsat vurdering.
- **Dimension eller kategori (`_dim_*`):** pilen følger doughnut-geometrien.
  Sociale kategorier skal fyldes op mod fundamentet, økologiske skal ned under
  loftet. Fremgang er derfor pil op på social og pil ned på øko. Her er `pct`
  **målrettet** via `maalrettet()`, altså med fortegnet vendt for inverse
  indikatorer, så positiv altid betyder fremgang. `vaerdi_start` og
  `vaerdi_slut` er tomme, fordi der ikke er nogen fælles enhed.

Denne fælde er allerede trådt i én gang: worst-of-dimensioner kopierede
oprindeligt sub-indikatorens rå `pct`, mens gennemsnitsdimensioner brugte den
målrettede. Resultatet var at Forurening og Vand begge stod som positiv retning,
men med pile der pegede modsat. Ændrer du i `aggreger_dimensioner()`, så sørg
for at **begge** grene målretter `pct`.

**T8 - En social indikator uden kategori er en fejl.** Enhver social indikator i
registret skal stå i en kategoris `indicators`-liste. `housing_no_wc` og
`housing_no_bath` stod i masteren uden at blive scoret, indtil de blev fjernet i
sep. 2026, og `tjek_konsistens.py` melder nu tilfældet som fejl.
`indikatorregister.ikke_scoret()` holder en sådan indikator ude af
dimensionsaggregatet i `build_trends_csv.py` som sikkerhedsnet.

Uden det gennemsnitter kategoriens pil flere indikatorer end det tal, den står
ved siden af. Det skete for Bolig, hvor de to usynlige dominerede
(`housing_no_bath` faldt omkring 39 procent på landsplan).

**Regel: tilføjer du tidsserie til en indikator, så tjek at den faktisk står i
sin kategoris `indicators` i registret.** Ellers holdes den ude af pilen, og den
er ikke synlig noget sted.

Kontrol: kategoriens tooltip ("gennemsnit af N indikatorer") skal matche "N/N
indikatorer" på bjælken, medmindre forskellen skyldes manglende tidsserie på en
indikator der faktisk scores. Fællesskab viser fx 4 af 5, fordi `sport_tilskuer`
ingen pil har. Det er korrekt.

**T9 - Pilen og scoren er samme tal (fra sep. 2026).** Tidsseriens værdi for
scorens år skal være scorens råværdi. Indikatorer med en defineret
beregning (tal pr. indbygger, andele, treårsgennemsnit) hentes af én funktion,
`serie_<id>(perioder)` i fetch-scriptet, som scoren kalder med det nyeste år
og `fetch_trend_history.py` med alle år (`SAMME_SOM_SCOREN`). Tre konventioner
gælder begge steder:

- Et tal pr. indbygger for år Y deles med folketallet 1. januar Y
  (`dst.folketal()`), ikke med det nyeste kvartal.
- En periode mærkes med slutåret (`dst_aar.aarstal()`): HISBK's "2021:2025"
  er 2025, skoleåret "2024/2025" er 2025.
- Et treårsgennemsnit for Y er gennemsnittet af raterne for Y-2, Y-1 og Y.

`tjek_konsistens.py` sammenligner serie og score for alle indikatorer med pil
og melder fejl, når mere end 10 procent af kommunerne afviger over 1 procent.
Første kørsel fandt 14 indikatorer, hvor pilen beskrev et andet tal end
scoren: andre kategorier (klassekvotient kun i folkeskolen, ubeboede boliger
inkl. fritidshuse, sportsanlæg talt med i bebygget areal), en anden
aldersgruppe, et andet folketal og en anden udtræksregel for Klimaregnskabet.

---

## 5. Designbeslutninger bag reglerne

Reglerne ovenfor siger hvad koden gør. Dette afsnit siger hvorfor, for de valg der er
lette at rulle tilbage ved en uheldig videreudvikling.

### Hvorfor det økologiske loft aldrig følger baseline-toggle

Baseline-toggle (R15) giver brugeren tre referencer for sociale indikatorer:
landsgennemsnit, top 10 og egen kommunegruppe. Det er fristende at lade
økologiske dimensioner følge med, så en landkommune sammenlignes med andre
landkommuner.

Det er bevidst fravalgt. **Planeten har ét budget, ikke ét pr. kommunegruppe.** At
give en landkommune grønt lys på kvælstof "fordi det er normalt for en
landkommune" ville skjule netop den overskridelse modellen findes for at afsløre.
Det sociale fundament kan meningsfuldt måles mod hvad sammenlignelige kommuner
opnår; det økologiske loft kan ikke.

For en regional eller europæisk tilpasning er det her den centrale
designbeslutning: nedskaler grænsen til området, ikke referencen til
nabolagsgennemsnittet.

### Hvornår scores der mod mål, og hvornår mod gennemsnit

Reglen bag R12: **scor mod målet, hvor der findes en meningsfuld grænse pr.
kommune.** Det gælder både biofysiske og juridiske grænser (WHO's
luftkvalitetsretningslinjer, ekspertgruppens 6 mg/L for nitrat) og vedtagne
politiske mål (EU's 30/10-procentmål for natur, EU's 65 procent genanvendelse,
det nationale 95-procentmål for uddannelse, 0 procent fossil varme, 2,5 ton
CO2e pr. person). Fra sep. 2026 også tre nedskalerede biofysiske grænser:
kystvandenes målbelastning for kvælstof fra vandområdeplanerne, tålegrænsen for
kvælstofnedfald på følsom natur og Danmarks bæredygtige grundvandsressource
(GEUS 2023), fordelt på kommunerne efter grundvandsdannelsen i DK-modellen.
Findes ingen sådan grænse, bruges landsgennemsnittet.

Pesticider er scoret mod landsgennemsnittet. Indikatoren er andelen af aktive
vandværker med fund, og målet ville være nul fund, som ikke kan bruges som
nævner i en ratio, så `baselineType` er `relativ`. Det samme gælder
vandområdernes tilstand (målet er 100 procent i god tilstand, altså nul der
mangler).

For areal findes en grænse (15 procent antropiseret areal), men ikke pr.
kommune: en bykommune kan ikke være 85 procent natur. Arealet måles derfor mod
landsgennemsnittet, og grænsen står som kontekst.

Vand blev målt på samme måde indtil 25. sep. 2026. Nu fordeles GEUS' nationale
ressource (1.104 mio. m³/år) efter DK-modellens infiltration til mættet zone
gange landareal. Fordelingen er en nedskalering, ikke GEUS' egen opgørelse pr.
område, men den er kontrolleret mod GEUS' ressource pr. modelområde: Sjælland
110 mod 113 mio. m³, Fyn og Jylland inden for ca. 20 procent. GEUS' tal pr.
delopland (bilag 2 i rapporten) bruges ikke direkte, fordi deloplandenes
geometri ikke er offentliggjort.

Resultatet er at tre dimensioner ender som `blandet` (Forurening, Næringsstoffer
og Uddannelse).

Klassifikationen blev gjort maskinlæsbar (`baselineType`) frem for at leve i
fritekst, fordi "grøn" ellers betyder to forskellige ting fra dimension til
dimension uden at brugeren kan se hvilken. Før det havde `education` et badge med
"Mål: 95 %", mens scoren reelt blev beregnet mod landsgennemsnittet og omskaleret
af baseline-toggle. Badge og beregning sagde hver sit.

### Hvorfor gruppe-baseline genbruger de færdige ratios

R10 omskalerer de allerede beregnede ratios i frontenden i stedet for at beregne
en ny ratio i pipelinen. Det holder `master_indicators.csv` uafhængig af
baselinevalget: én værdi pr. kommune og indikator, tre måder at læse den på.
Samme teknik som top10-baselinen (R9). Konsekvensen er at inverse indikatorer
omskaleres på deres allerede vendte ratio, hvilket er en bevidst forenkling.

---

## 6. Kendte fælder

1. **Farvelogikken er omvendt** mellem social og økologisk (R11). Den hyppigste
   fejlkilde i projektet.
2. **Forurening er den eneste gennemsnitsdimension.** Alle andre økologiske
   dimensioner er worst-of (R7), og reglen skal spejles i retningspilene (T6).
3. **Kilder med kun kommunenavne får koden slået op i fetch-scriptet**
   (`kommuner.kode_for_navn()`), ikke i build-trinnet. Et ukendt navn stopper
   scriptet (R5). Christiansø er ikke blandt de 98.
4. **`absoluteScore`-indikatorer må aldrig omskaleres af baseline-toggle**
   (R9, R10, R15). I dag `education` og `bolig_fossil`.
5. **`bolig_fossil` afhænger af fjernvarmedata, og rækkefølgen er bindende:**
   `fetch_fjernvarme_mix.py` skal køre før `fetch_bolig_fossil.py`, som læser
   fjernvarmens fossilandel fra førstnævntes CSV.
6. **`null` mod `undefined` i `eco_ratios` er semantisk bærende i UI'et** (R13).
7. **Kommunenavne indeholder æ, ø og å**, og former som "Høje-Taastrup" og
   "Ringkøbing-Skjern". URL-encoding og navnematch skal håndtere det. Match er
   ikke versalfølsomt.
8. **Ingen kommune når grønt på `bolig_fossil`.** Det er korrekt og bevidst,
   fordi målet er absolut 0 procent fossil varme, og fossilfri varme ikke findes
   endnu. Det er ikke en databug.
9. **`bolig_fossil` afgrænses til helårsboliger.** Grundlaget er DST BYGB40,
   opvarmet areal i m2. To afgrænsninger er nødvendige: `ANVEND_HELAARSBOLIG`
   (110-190), ellers måler indikatoren kommunens samlede bygningsmasse inklusive
   fabrikker og udhuse. Og fritidsboliger holdes ude af scoren, fordi sommerhuse
   typisk er elopvarmede (median omkring 7 procent fossil mod helårsboligernes
   omkring 20), så medregning ville give sommerhuskommuner en kunstigt bedre
   social score.
10. **Python-scripts og CSV-filer i `data/` er kildesporet.** De må ikke slettes
    eller ryddes op ved en migrering. Masterfilen kan altid genskabes fra dem,
    men ikke omvendt.
11. **En økologisk andel hvor højere er bedre, skal have `formula: "komplement"`**
    (R2a). Uden den falder den tilbage på `ref / raw × 100`, som eksploderer ved
    andele nær nul. Registret afviser formlen på andre indikatortyper.
12. **Jupiter har nedlagte vandværker med.** `aktiv_num = 1` er et aktivt anlæg.
    Uden filteret talte 844 nedlagte værker med i pesticidandelen og 935 analyser
    i nitraten, og Thisted stod med 5,2 mg/L nitrat mod 14,5 for de aktive værker.
    Stof-status "Aktuelt fund og tidl. over kravværdi" betyder at seneste analyse
    er UNDER kravværdien.
13. **Kystvandstabellen udtrækkes af en PDF.** `fetch_kvaelstof_kystvand.py`
    læser bilag 1.1 i vandområdeplanen og tjekker en kendt række (Roskilde Fjord,
    ydre). Rækker med manglende felter tolkes efter antallet af tal (se
    scriptets docstring); fejler kontrolrækken, er udtrækket forskudt. Resultatet
    ligger i `data/vp3_kvaelstof_kystvande.csv`, så en ny plan kan sammenlignes
    med den gamle række for række.
14. **Treårs-værdier: median eller gennemsnit er et valg.** Affald og
    genanvendelse bruger medianen (enkeltår med fejlindberetninger), vandindvinding
    og kvælstofnedfald gennemsnittet (reel, men vejrbestemt variation).
    `dst.rullende()` tager valget som parameter, og pilen bruger samme funktion.
15. **Vand: grundvand, ikke alt vand, og to øer uden model.** Tælleren er
    VANDIND med `VANDTYP=GVAND`, fordi GEUS' ressource er grundvand. Med
    `TOTVAND` kommer ca. 240 mio. m³ overfladevand med, især fra virksomheder
    (fx dambrug, der leder vandet tilbage), og Vejle og Silkeborg blev røde af
    den grund. Samsø og Læsø ligger uden for DK-modellen og har ingen
    grundvandsdannelse; de får ingen vand-score frem for et gæt.
    `grundvandsdannelse_scores.csv` er statisk (1991-2020) og hentes kun igen ved
    en ny version af DK-modellen; det kræver `DATAFORSYNINGEN_TOKEN`.

---

## 7. Kendte afvigelser mellem dokumentation og kode

Opdateret 26. september 2026. To rækker er lukket: Sundhedsprofilens rekonstruerede landstal (`sundhedsprofil_scores.csv` har nu landstallene i egne kolonner) og UVM-indikatorernes uvægtede kommunegennemsnit (vægtes nu med elevtal fra DST UDDAKT20).

Før det: opdateret 24. september 2026. R1 (`navn_key` omgik cappet), R12
(`eco_naer_landbrug` havde `lowerIsBetter: true`) og R3 for `public_transport`
(uvægtet gennemsnit af kommunegruppe-tal) er lukket og fjernet fra tabellen.
`public_transport` beregnes nu pr. kommune af `fetch_offentlig_transport.py`
og måles mod Danmark som helhed.

| Regel | Afvigelse | Status |
|---|---|---|
| R3 | Landsgennemsnittet for de otte Sundhedsprofil-indikatorer beregnes af os som et befolkningsvægtet gennemsnit af de 98 kommuneandele (DST FOLK1A, 16+), ikke hentet fra kilden. Databasen udstiller ikke et landstal pr. kommunetabel. Reglen forudsætter ellers et landstal fra kilden | Bevidst, dokumenteret i `data/README.md` og på metodesiden |
| T1 | Retningen for Sundhedsprofilens indikatorer beregnes 2017 → 2025 (2021 → 2025 for `ensomhed` og `fysisk_aktivitet`), ikke over hele den tilgængelige serie 2010-2025. Reglen siger ellers hele serien | Bevidst, se punkt 23 i CLAUDE.md |

Rækkerne er bevidste eller overgange og er dokumenterede.

---

## 8. Vedligehold

Opdater dette dokument når en beregningsregel ændres, når en ny dimension eller
kategori tilføjes, eller når en afvigelse i afsnit 7 lukkes. Reglerne skal kunne
læses uden adgang til koden, så undgå linjenumre og hold feltnavnene i
overensstemmelse med den faktiske implementering.

Se også:

- `data/README.md` for skemaet bag `master_indicators.csv`
- `data/methodology_note.md` for nutidsjusteringen af forbrugsbaseret CO2
- `docs/statbank_doughnut_mapping.md` for mapping mellem DST-tabeller og
  indikatorer
- `webapp/app/metode/page.tsx` for den brugervendte metodebeskrivelse
