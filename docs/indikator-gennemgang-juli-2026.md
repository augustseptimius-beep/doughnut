# Indikator-gennemgang juli 2026: kan hver indikator forsvares?

Kvantitativ og kritisk gennemgang af alle indikatorer, lavet fordi tilpasnings-funktionen
(dimensions-fravalg) kræver at de indikatorer der IKKE kan fravælges, kan forsvares over for
kritiske politikere. Spørgsmålene: Hvor meget siger hver indikator? Hvor stor betydning har
den for sin dimension? Giver få indikatorer for stort udfald - og udvander mange billedet?

Alle tal er beregnet på master_indicators.csv (98 kommuner, juli 2026). Beregningsscript
kan genkøres - se metodenoten nederst.

## Sådan læses tallene

- **indflydelse**: gennemsnitlig ændring i kategori-scoren hvis indikatoren fjernes.
  Ved 2 indikatorer flytter hver typisk ±20 point; ved 10 indikatorer under ±4.
- **%cap**: andel kommuner hvor ratioen er klippet ved 150. Høj cap = indikatoren er
  "mættet" og differentierer ikke længere mellem de gode kommuner.
- **korrelation (r)**: to indikatorer med r over ~0,7 måler i praksis det samme -
  fænomenet får dobbelt vægt uden at tilføre information.
- **binder-%** (øko, worst-of): hvor ofte sub-indikatoren er den værste og dermed afgør
  dimensions-scoren. 0% = indikatoren påvirker aldrig scoren (ren visning/vagthund).

## Hovedkonklusioner på tværs

1. **Få indikatorer giver stort udfald - og det er ikke altid forsvarligt.** I kategorierne
   med 2 indikatorer flytter hver enkelt ±17-23 point. Det er OK når de to måler samme
   fænomen i samme retning (Demokrati: to valgdeltagelser, r=0,76). Det er IKKE OK når de
   trækker modsat (Bolig: r=-0,85 - de udligner hinanden, og kategorien måler reelt ingenting).
2. **Mange indikatorer udvander.** Uddannelse har 10 indikatorer; kategori-spredningen er
   kun 6,3 point og alle kommuner ligner hinanden. Enkelte indikatorer (wellbeing, std 1,7)
   flytter under ±1 point og er reelt dekoration.
3. **150-cappen mætter flere indikatorer.** crime_rate er cappet for 44% af kommunerne -
   for næsten halvdelen af landet differentierer tryghedsindikatoren ikke. Cappen løfter
   også gennemsnittet kunstigt (crime_rate gns 131).
4. **Redundans er udbredt i Velfærd.** 9 indikator-par med r over 0,6; employment ×
   poverty_relative r=0,83. Kategorien måler i praksis "indkomstfattigdom" fire gange.
5. **I worst-of-dimensioner er flere subs aldrig bindende.** NO2 afgør luftkvalitets-scoren
   i 0% af kommunerne (PM2.5 binder altid). Det er ikke nødvendigvis forkert - en
   ikke-bindende sub fungerer som vagthund der slår ud hvis den forværres - men det skal
   siges højt at scoren i praksis er PM2.5.
6. **Fundet og rettet undervejs:** vejr_skader undslap 150-cappen (navn-nøgle-grenen i
   build_master_csv.py manglede cappen; ratios op til 431). Rettet - nu cappes 27 kommuner.

## Socialt fundament, kategori for kategori

### Sundhed (8 indikatorer) - slank eller gruppér

| indikator | gns | std | %cap | indflydelse |
|---|---|---|---|---|
| life_expectancy | 100,0 | 1,3 | 0% | 1,3 |
| hospital_short | 97,0 | 5,8 | 0% | 1,2 |
| hospital_long | 96,3 | 9,2 | 0% | 1,3 |
| gp_distance | 94,9 | 36,5 | 23% | 3,5 |
| medicin | 103,6 | 22,0 | 4% | 2,0 |
| laegekontakt | 98,9 | 2,4 | 0% | 1,6 |
| boerneovervaeght | 99,9 | 26,1 | 8% | 2,4 |
| hjemsyg | 92,8 | 25,9 | 4% | 2,2 |

Problemer: (1) life_expectancy og laegekontakt varierer næsten ikke mellem kommuner
(std 1,3 og 2,4) - de fylder i fortællingen men flytter intet. (2) gp_distance korrelerer
med hjemsyg (r=0,74) og medicin (r=0,66) - den er reelt en geografi-proxy. (3) laegekontakt
og hjemsyg trækker modsat (r=-0,63): landkommuner har færre lægekontakter men flere
hjemmesygepleje-modtagere. (4) hospital_short × hospital_long r=0,64.
Anbefaling: overvej at slanke til 5-6 (fx life_expectancy som anker trods lav varians,
ét sygehusmål, medicin, boerneovervaeght, hjemsyg) og drop laegekontakt (retning er
omdiskuterbar: er flere lægebesøg godt eller skidt?).

### Uddannelse (10 indikatorer) - udvandet, og tre måler det samme

apprenticeship: 24% cappet, std 45 - den mest støjende indikator i kategorien og den med
størst indflydelse (4,1). education × exam_grade × youth_education korrelerer r=0,75-0,82:
alle tre afspejler samme underliggende socioøkonomi, så den får tredobbelt vægt. wellbeing
har std 1,7 og flytter 0,6 point - dekoration.
Anbefaling: slank til 5-6. Behold education (absolut mål, politisk stærk), low_education
(fanger bunden), high_absence, apprenticeship (evt. med støj-forbehold), plus ÉN af
exam_grade/youth_education. Overvej at flytte class_size/daycare_ratio/educated_staff til
en evt. "kommunal service"-vinkel eller acceptér dem som input-mål med lille vægt.

### Velfærd (7 indikatorer) - konsolidér fattigdomsmålene

9 par med r over 0,6. Kernen: employment × poverty_relative r=0,83, child_poverty ×
poverty_relative r=0,75, disposable_income × child_poverty r=0,68. Dertil ligger low_income
(60%-median) i Lighed - så indkomstfattigdom tælles reelt 4-5 gange på tværs.
Anbefaling: vælg ÉT primært relativt fattigdomsmål (poverty_relative), behold child_poverty
kun hvis børnevinklen skal være eksplicit, og behold vulnerable_children +
child_notifications som social-indsats-vinkel (r=0,62 indbyrdes - acceptabelt).
Slank til 5: disposable_income, employment, poverty_relative, vulnerable_children, neet.

### Bolig (2 indikatorer) - kategorien måler reelt ingenting. GENTÆNK

vacant_housing × housing_area: **r = -0,85**. Landkommuner har mange tomme boliger (straf)
og meget boligareal (bonus) - de to udligner systematisk hinanden, så kategori-scoren
er næsten konstant støj. Oveni er vacant_housing cappet for 27% af kommunerne, og
housing_area's præmis ("mere plads = bedre") er tvivlsom i en bæredygtighedsramme
(samme logik som fik car_access fjernet).
Anbefaling (stærkest kandidat til handling): drop housing_area, og find 1-2 reelle
boligkvalitetsmål. housing_no_wc/housing_no_bath ligger klar i master (98/98) men er
næsten uden variation (49-56% cappet) - de kan vises men vil ikke differentiere.
Alternativ: boligbyrde (boligudgift ift. indkomst) hvis DST-kilde findes.

### Demokrati (2 indikatorer) - forsvarlig

r=0,76, men det er samme fænomen (valgdeltagelse) målt ved to valg - her er redundansen
en styrke (robusthed), ikke dobbelttælling. Behold.

### Kultur (3 indikatorer) - acceptabel, men spending er input

kultur_spending har størst indflydelse (12,1) og måler kommunens prioritering, ikke
borgernes kulturliv. music_school 20% cappet. Behold, men overvej om biblioteksudlån
(strukturelt faldende pga. digitalisering) skal suppleres med e-udlån.

### Tryghed (2 indikatorer) - crime_rate er mættet

crime_rate: **44% af kommunerne cappet ved 150** (gns 131). Indikatoren kan ikke skelne
mellem de 43 tryggeste kommuner, og hver indikator flytter ±22 point.
Anbefaling: overvej en højere cap eller log-skala specifikt for stærkt skæve indikatorer -
eller acceptér og dokumentér at "150 = blandt de tryggeste". Kategorien er ellers forsvarlig.

### Foreningsliv (4 indikatorer) - tre input, én effekt

sports_facilities, sports_spending og civil_society er alle kapacitet/udgifter (input);
kun sports_membership er faktisk deltagelse (og den har lavest indflydelse, 4,8).
Anbefaling: behold, men vær ærlig om at kategorien primært måler kommunal prioritering.
Hvis der skal slankes: facilities og spending overlapper konceptuelt.

### Lighed (3), Ligestilling (3) - forsvarlige

Moderate korrelationer, ingen alarmerende cap. NB: low_income (14% cappet) overlapper
med Velfærds fattigdomsmål - se Velfærd-anbefalingen.

### Mobilitet (2 indikatorer) - reelt en by/land-dummy

public_transport har kun 5 mulige værdier (kommunegruppe-data), 28% cappet, gns 80.
r=0,74 med commute_distance: kategorien belønner/straffer by/land-struktur dobbelt, og
kommunen kan ikke påvirke sin score. Kategori-spænd 48-150 - det største sociale udfald.
Anbefaling: næsthøjeste prioritet efter Bolig. Enten find kommune-specifik
kollektiv-trafik-data, eller acceptér åbent at Mobilitet måler geografisk struktur.

### Klimatilpasning (1 indikator) - eksperimentel, nu med cap

Én proxy-indikator (forsikringsskader). Efter cap-fixet: 27 kommuner cappet, std ~34.
Med kun én indikator ER kategorien indikatoren - stort udfald, ingen udligning.
Anbefaling: behold med tydelig "proxy"-mærkning (metodesiden har den), og hold udkig
efter et supplement (fx andel af kommunen i oversvømmelsesrisiko-zone, KAMP-data).

### Energi (1 indikator) - stærkest i klassen

bolig_fossil: god spredning (std 17), ingen cap, absolut mål, klar politisk logik.
At én indikator bærer dimensionen er her forsvarligt, fordi målet (0% fossil) er
entydigt og indikatoren dækker hele fænomenet.

## Økologisk loft: hvem afgør reelt scoren (worst-of)?

| dimension | sub | binder i % af kommunerne |
|---|---|---|
| Klimapåvirkning | forbrug_co2 | 88,8% |
| | territorial | 11,2% (landbrugs-/industrikommuner) |
| Luftkvalitet | PM2.5 | 100% |
| | NO2 | **0%** |
| Næringsstoffer | overfladevand (VP3) | 57,1% |
| | N-loft landbrug | 19,4% |
| | fosfor / kvælstof (spildevand) | 12,2% / 11,2% |
| Biodiversitet | bio_vasentlig | 95,9% |
| | bio_uerstattelig | 73,5% (ofte samtidig, begge cappet 300) |
| Arealanvendelse | bebygget / intensiv | 52,0% / 48,0% (by/land - by design) |

- **NO2 påvirker aldrig scoren.** Forsvar: worst-of gør den til vagthund - den slår ud
  hvis NO2 igen overstiger PM2.5-presset. Men det bør stå på metodesiden at luft-scoren
  i praksis er PM2.5.
- **Klimapåvirkning er i praksis forbrugs-CO2** for 9 af 10 kommuner - territorial binder
  kun i kommuner med tung industri/landbrug. Det er meningsfuldt, men værd at vide.
- **Forurening (gennemsnit, ikke worst-of): pesticider dominerer.** Std 180 (spænd 0-884)
  mod 35-38 for de tre andre; fjernes pesticider flytter dimensions-scoren i snit 27 point
  (de andre 11-16). Anbefaling: overvej en cap på pesticid-ratioen (fx 300 som VP3/bio),
  så én indikator ikke ejer dimensionen - 0/101-gulv-logikken bevares.

## Anbefalet regelsæt (svar på "hvor mange indikatorer er rigtigt?")

1. **2-6 indikatorer pr. kategori.** Under 3 kun hvis de måler samme fænomen i samme
   retning (Demokrati) eller fænomenet er entydigt med absolut mål (Energi).
2. **Redundans-regel:** r over ~0,7 mellem to indikatorer i samme kategori → slå dem
   sammen eller vælg én. Ellers får fænomenet skjult dobbeltvægt.
3. **Modsat-korrelations-regel:** r under ca. -0,5 i samme kategori → kategorien udligner
   sig selv og skal gentænkes (Bolig).
4. **Mætningsregel:** over ~25% af kommunerne cappet → indikatoren differentierer ikke;
   overvej skala eller dokumentér mætningen eksplicit.
5. **Variations-regel:** std under ~3 ratio-point → indikatoren flytter intet og er
   dekoration; behold kun hvis den har stærk kommunikationsværdi (middellevetid).
6. **Worst-of-ærlighed:** dokumentér hvilke subs der reelt binder; ikke-bindende subs
   er vagthunde, ikke drivere.

## Prioriteret handlingsliste (beslutninger til August)

1. **Bolig**: gentænk (r=-0,85 er ikke til at forsvare). Størst metodisk gevinst.
2. **Velfærd**: konsolidér fattigdomsmål (7 → ~5 indikatorer).
3. **Mobilitet**: beslut om public_transport (gruppe-data) kan forsvares, eller find bedre kilde.
4. **Uddannelse**: slank 10 → 5-6; drop wellbeing eller flet exam/youth_education.
5. **Forurening**: cap pesticid-ratioen så den ikke ejer dimensionen.
6. **Metodesiden**: tilføj binder-tabellen (worst-of-ærlighed) og mætningsforbehold for crime_rate.
7. **Sundhed**: slank 8 → 5-6 (drop laegekontakt, flet sygehusmålene).

## Metodenote

Indflydelse = gennemsnit over kommuner af |kategori-score med indikator - uden indikator|.
Korrelationer er Pearson på ratio-niveau på tværs af kommuner med data i begge indikatorer.
Binder-% = andel kommuner hvor sub'en er lig dimensionens max (ties tæller for begge,
derfor kan summen overstige 100% - især ved fælles cap på 300). Tallene kan genberegnes
fra master_indicators.csv; ingen eksterne afhængigheder.
