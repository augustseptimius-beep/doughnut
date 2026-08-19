# Arkitektur og beregningsregler

Dette dokument beskriver de normative regler bag scoringen i "Danmarks 98
Doughnuts". Reglerne er projektets faglige kerne. En port til en anden platform,
en videreudvikling eller en regional tilpasning skal reproducere dem præcist,
ellers ændrer man tallene uden at opdage det.

Reglerne er implementeret i `scripts/build_master_csv.py` (datapipelinen),
`scripts/build_trends_csv.py` (retningspile) og `webapp/lib/shared.ts`
(frontendberegninger). Dokumentet angiver bevidst funktions- og feltnavne
frem for linjenumre, fordi linjenumre skrider ved hver ændring.

**Læs afsnit 5 og 6 før du ændrer noget.** Fælderne dér er alle sammen fejl
projektet allerede har begået én gang.

---

## 1. Grundlæggende talkonvention

Alle indikatorer udtrykkes som en **ratio** hvor 100 er referencepunktet:

- **Sociale indikatorer:** 100 = niveau med landsgennemsnittet (eller med et
  absolut mål, se R2). Højere er bedre.
- **Økologiske indikatorer:** 100 = på den planetære grænse. Lavere er bedre,
  og over 100 er overshoot.

Indikatorer hvor en høj råværdi er dårlig (Gini, kriminalitet, luftforurening)
er allerede vendt i kildedataene, så ratio-retningen er ensartet. Feltet
`inverse` i `INDICATORS` registrerer hvilke det gælder.

De to retninger er modsatrettede med vilje. Det er den hyppigste fejlkilde i
projektet, se R11.

---

## 2. Transformationsregler (datapipeline)

Reglerne herunder ligger i `scripts/build_master_csv.py` og udføres når
rådata-CSV'erne konsolideres til `data/master_indicators.csv`.

**R1 - Social ratio-cap.** Sociale ratios cappes ved 150,0. Formålet er at
forhindre at en enkelt ekstremværdi dominerer kategorigennemsnittet.

> **Kendt afvigelse (august 2026):** cappet håndhæves kun i den gren der slår
> kommuner op på `kommune_kode`. Indikatorer med `navn_key: True` (i dag kun
> `vejr_skader`) passerer uden cap. 27 kommuner har derfor `vejr_skader`-ratios
> over 150, den højeste er 431,29. Rettelsen ligger på branchen
> `claude/repo-audit-logic-review-4bj1i1` og er ikke merget. Indtil den er
> merget, beskriver R1 den ønskede tilstand, ikke koden.

**R2 - Absolut mål (`abs_target`).** Sætter en indikator feltet `abs_target`,
beregnes `ratio = min(raw / abs_target * 100, 150)` afrundet til 2 decimaler.
I dag bruges det kun af `education` med `abs_target: 95`.

`bolig_fossil` er også absolut scoret, men dens ratio (`100 - samlet fossil%`)
beregnes færdig i `fetch_bolig_fossil.py` og gemmes direkte. Den har derfor
ingen `abs_target` i pipelinen.

**R3 - Inverse økologisk ratio (`inverse_ratio: True`).** Kildedataene for
forureningsindikatorer leverer en inverteret ratio, hvor lav værdi betyder høj
forurening. `invert_to_direct_ratio()` konverterer:
`direct = round(10000 / inverse, 2)`. Er inputtet `None` eller `0`, bliver
resultatet `None`. Gælder `naer_nitrogen`, `naer_phosphorus` og
`cirkularitet_waste`.

**R4 - Genanvendelse (`special: "recycling_eu_target"`).** `recycling_eu_target_ratio()`
beregner `ratio = round((65 / pct) * 100, 2)` målt mod EU-målet på 65 procent.
`None` eller `0` giver `None`. Over 100 betyder at kommunen genanvender for
lidt. Gælder kun `cirkularitet_recycling`.

**R5 - Forbrugsbaseret CO2 (`special: "cba_navn_key"`).** `cba_ratio()` beregner
`ratio = round((raw / 3) * 100, 2)` mod en grænse på 3 ton CO2e pr. person.
Kildedataene slås op på kommunenavn, ikke kommunekode. Ved manglende match
bliver værdien `None`, og der er bevidst intet fallback. Christiansø filtreres
fra. Gælder kun `forbrug_co2`.

**R6 - Økologisk ratio-cap (`cap`).** Sætter en økologisk indikator feltet `cap`,
klippes ratio til den værdi. I dag har `overfladevand`, `bio_vasentlig` og
`bio_uerstattelig` alle `cap: 300`. Uden cappet giver bioscore-andele nær nul
ratios i tusindvis, som ville forstyrre valideringen i R14.

**R7 - Økologisk dimensionsscore.** Pr. kommune og dimension samles alle
ikke-`None` sub-ratios:

- **worst-of (standard):** `score = round(max(ratios), 2)`
- **gennemsnit:** `score = round(sum / len, 2)`, kun for dimensioner i
  `AVERAGE_DIMENSIONS`

`AVERAGE_DIMENSIONS` indeholder i dag **udelukkende `forurening`**. Begrundelsen
er at dens fire indikatorer måler vidt forskellige forureningstyper, hvor
worst-of ville lade den værste enkeltkilde definere hele dimensionen.

Alle andre dimensioner bruger worst-of. Det er bevidst planetary
boundary-logik: overskrides bare én delgrænse, er dimensionen overskredet.
Gennemsnit ville lade en god delindikator maskere en overskredet grænse.

Uden nogen sub-ratios er scoren `None`. Resultatet skrives til masterfilen som
rækker med `indicator_id = "_dim_<dimension>"`.

**R14 - Ratiovalidering.** Gyldigt interval er 0 til 2000. Værdier udenfor
rapporteres som en advarsel ved build, men klippes ikke. Intervallet er sat
bevidst bredt, så R6-cappet fanger de reelle udfald først.

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
   beregnes, og `ny ratio = parseFloat(((ratio / top10Avg) * 100).toFixed(2))`.
5. Er kommunens ratio `null`, eller er `top10Avg` nul, bliver resultatet `null`.

Højeste ratio er altid den bedste præstation, også for inverse indikatorer,
fordi de allerede er vendt i kildedataene.

**R10 - Kommunegruppe-baseline.** `computeGroupRatios()` fungerer som R9, men
med DST's kommunegrupper G1-G5 (`KOMMUNEGRUPPE`) som reference i stedet for
top 10. Gruppegennemsnittet er uvægtet. `absoluteScore`-indikatorer kopieres
uændret. Resultatet er `null` hvis kommunens ratio er `null`, hvis kommunen
ikke findes i gruppemappingen, eller hvis gruppegennemsnittet er nul.

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

I dag er kun Uddannelse og Forurening `blandet`. UI'et viser mærket "mod mål"
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
Økologiske dimensioner har absolutte planetære grænser og ændres aldrig af
toggle. `absoluteScore`-indikatorer omskaleres heller ikke, selvom de er
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
| `kontekst` | indikatoren mangler i `OP_ER_GODT`, så retning kan ikke vurderes |
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

**T5 - `OP_ER_GODT` skal holdes i sync med `INDICATORS[].inverse`.** Konstanten i
`build_trends_csv.py` afgør hvilken vej pilen peger. En manglende mapping bliver
til `kontekst` (pil uden vurdering), ikke til en fejl. Tjek scriptets
ADVARSEL-linjer efter hver kørsel.

**T6 - Dimensionspilen følger worst-of, ikke gennemsnittet.** En øko-dimensions
pil er retningen for den sub-indikator der bestemmer dimensionens score, altså
den med højeste ratio. Tager man gennemsnittet af sub-retningerne, kan
dimensionen vise grøn pil samtidig med at netop den overskredne grænse bliver
værre.

Undtagelsen er `forurening`, som bruger gennemsnit i scoren (R7) og derfor også
i retningen. `AVERAGE_DIMENSIONS` findes i **både** `build_master_csv.py` og
`build_trends_csv.py` og skal holdes ens.

Har den afgørende sub-indikator ingen tidsserie, får dimensionen **ingen pil**.
Der falles bevidst ikke tilbage på de øvrige. Derfor har `klimapaavirkning` kun
pil i 11 af 98 kommuner: i de øvrige 87 afgøres scoren af forbrugsbaseret CO2,
som ikke findes som tidsserie. Det er korrekt opførsel, ikke manglende data.

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

**T8 - Masteren kan indeholde indikatorer platformen ikke scorer.**
`housing_no_wc` og `housing_no_bath` står i masteren med `dimension=bolig`, men
er ikke med i `SOCIAL_CATEGORIES.bolig.indicatorIds`. Bolig scorer og viser kun
2 indikatorer. Konstanten `IKKE_SCORET` i `build_trends_csv.py` holder dem ude af
dimensionsaggregatet, men de beholder deres egen indikatorrække.

Uden det gennemsnitter Bolig-pilen 4 indikatorer ved siden af et tal beregnet på
2, og de to usynlige dominerer (`housing_no_bath` er faldet omkring 39 procent
på landsplan).

**Regel: tilføjer du tidsserie til en indikator, så tjek at den faktisk står i
`SOCIAL_CATEGORIES[].indicatorIds`.** Ellers forgifter den en dimensionspil uden
at være synlig noget sted.

Kontrol: kategoriens tooltip ("gennemsnit af N indikatorer") skal matche "N/N
indikatorer" på bjælken, medmindre forskellen skyldes manglende tidsserie på en
indikator der faktisk scores. Sundhed viser fx 7 af 8, fordi `gp_distance` ingen
serie har. Det er korrekt.

---

## 5. Kendte fælder

1. **Farvelogikken er omvendt** mellem social og økologisk (R11). Den hyppigste
   fejlkilde i projektet.
2. **Forurening er den eneste gennemsnitsdimension.** Alle andre økologiske
   dimensioner er worst-of (R7), og reglen skal spejles i retningspilene (T6).
3. **`forbrug_co2` og `vejr_skader` matcher på kommunenavn, ikke kode.**
   Manglende match giver `null` uden fallback. Christiansø filtreres fra.
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

---

## 6. Kendte afvigelser mellem dokumentation og kode

Opdateret 19. august 2026.

| Regel | Afvigelse | Status |
|---|---|---|
| R1 | `navn_key`-indikatorer omgår 150-cappet. `vejr_skader` har 27 kommuner over cap, højeste 431,29 | Rettelse ligger umerget på `claude/repo-audit-logic-review-4bj1i1` |
| R12 | Sub-indikatoren `eco_naer_landbrug` har `lowerIsBetter: true`, men scoringen i `fetch_naeringsstoffer_landbrug.py` er `(landssnit / råværdi) x 100`, hvilket svarer til `false` | Samme branch |

Begge er registreret, ingen af dem er rettet på hovedbranchen. Merges den
branch, bortfalder afsnittet her, og R1 bliver retvisende som skrevet.

---

## 7. Vedligehold

Opdater dette dokument når en beregningsregel ændres, når en ny dimension eller
kategori tilføjes, eller når en afvigelse i afsnit 6 lukkes. Reglerne skal kunne
læses uden adgang til koden, så undgå linjenumre og hold feltnavnene i
overensstemmelse med den faktiske implementering.

Se også:

- `data/README.md` for skemaet bag `master_indicators.csv`
- `data/methodology_note.md` for nutidsjusteringen af forbrugsbaseret CO2
- `docs/statbank_doughnut_mapping.md` for mapping mellem DST-tabeller og
  indikatorer
- `webapp/app/metode/page.tsx` for den brugervendte metodebeskrivelse
