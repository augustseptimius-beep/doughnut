# Metode- og logik-anbefalinger juli 2026

Mine bedste anbefalinger til at gøre metoden stærk nok til at forsvare over for kritiske
politikere. Bygger på den kvantitative indikator-gennemgang (`indikator-gennemgang-juli-2026.md`)
og audit-rapporten (`audit-juli-2026.md`). Dette dokument er beslutningsoplæg, ikke implementering -
implementering gemmes til Sonnet 5 / Opus.

Bemærk: research af nye datakilder blev påbegyndt med tre subagenter men afbrudt af et spend-loft,
så datakilde-afsnittet (D) hviler på domæneviden og er markeret med konfidensniveau. Kun
Sundhedsprofilen er web-verificeret i denne omgang. Alle datakilde-forslag skal verificeres
(kommuneniveau + adgang + opdateringsfrekvens) før implementering.

---

## A. Fem metodiske principper (fundamentet)

Disse gør vurderingen konsistent og gør det muligt at svare klart når en politiker spørger
"hvorfor tæller I det, og hvorfor på den måde?". Foreslås skrevet ind på metodesiden som et
selvstændigt "Kvalitetskrav til indikatorer"-afsnit.

1. **Antalsregel: 3-6 indikatorer pr. dimension.** Under 3 kun hvis (a) de måler samme fænomen
   i samme retning (redundans som robusthed, fx Demokrati), eller (b) fænomenet er entydigt med
   et absolut mål (Energi). Over 6 kræver at hver ekstra indikator kan vise selvstændig variation.

2. **Redundansregel: r > 0,7 i samme dimension → slå sammen eller vælg én.** Ellers får ét
   fænomen skjult dobbeltvægt. (Gælder også på tværs af dimensioner - se C3.)

3. **Modsatrettethedsregel: r < -0,5 i samme dimension → gentænk dimensionen.** To indikatorer
   der systematisk udligner hinanden gør kategori-scoren til støj (Bolig i dag: r = -0,85).

4. **Variationsregel: std < ~3 ratio-point → indikatoren differentierer ikke.** Behold kun hvis
   den har stærk kommunikationsværdi og et anker-formål (middellevetid). Ellers er den dekoration.

5. **Mætningsregel: > 25 % af kommunerne kappet ved 150 → indikatoren er mættet.** Enten hæv
   loftet/brug log-skala for den indikator, eller dokumentér mætningen eksplicit ("150 = blandt
   de bedste"). En mættet indikator kan ikke skelne toppen fra hinanden.

Princippet bag: **scor mod et absolut mål hvor et meningsfuldt per-kommune-mål findes; ellers mod
landsgennemsnit - og sig tydeligt hvad grøn betyder.** (Allerede delvist implementeret via
baselineType-mærkning.)

---

## B. Anbefalinger pr. social kategori

Rangeret efter hvor meget metoden vinder. "Foreslået sæt" er mit konkrete bud - ikke hugget i sten.

### 1. Bolig - GENTÆNK (højeste prioritet)
Problem: de 2 indikatorer korrelerer r = -0,85 og udligner hinanden; kategorien måler reelt intet.
housing_area's præmis ("mere plads = bedre") er desuden tvivlsom i en bæredygtighedsramme (samme
logik som fik car_access fjernet).
- **Fjern** housing_area.
- **Behold** vacant_housing kun hvis der tilføjes et reelt boligkvalitets- eller boligbyrdemål.
- **Tilføj** 1-2 af: boligbyrde (boligudgift/indkomst), energimærke-fordeling, hjemløshed pr.
  1.000 indb. Se D1.
- Foreslået sæt (3): boligbyrde, energimærke-andel (D/E/F/G), vacant_housing. Alle med klar retning
  og lav indbyrdes korrelation.

### 2. Velfærd + Lighed - KONSOLIDÉR fattigdomsklyngen (høj prioritet)
Ny analyse i denne runde: fattigdomssignalet tælles på tværs af to kategorier.
- low_income (Lighed) × child_poverty (Velfærd): **r = 0,87**
- low_income (Lighed) × poverty_relative (Velfærd): **r = 0,78**
- employment × poverty_relative: r = 0,83
- child_poverty × poverty_relative: r = 0,75

Dertil er **Lighed internt inkohærent**: gini × low_income er kun r = -0,18. gini fanger reelt
"rig forstad med stor spredning" (gini × disposable_income = -0,75), mens low_income fanger
"få fattige". De to måler noget forskelligt og bør ikke gennemsnittes råt.

Anbefaling:
- **Flyt low_income ud af Lighed.** Lighed skal måle strukturel ulighed (gini +
  employment_origin_gap), ikke fattigdomsniveau.
- **Vælg ÉT primært relativt fattigdomsmål i Velfærd** (poverty_relative anbefales - det bredeste).
  Behold child_poverty kun hvis børnevinklen skal være eksplicit politisk.
- Foreslået Velfærd (5): disposable_income, employment, poverty_relative, vulnerable_children, neet.
- Foreslået Lighed (2-3): gini, employment_origin_gap (+ evt. et formuemål hvis kilde findes).
  NB: 2 indikatorer er OK her hvis de er konceptuelt distinkte - men overvej et tredje ulighedsmål.

### 3. Uddannelse - SLANK 10 → 6 (høj prioritet)
education × exam_grade × youth_education korrelerer r = 0,75-0,82 (samme socioøkonomi tredobbelt).
wellbeing har std 1,7 (flytter < 1 point).
- **Behold**: education (absolut 95%-mål, politisk stærk), low_education (fanger bunden),
  high_absence, apprenticeship, + ÉN af {exam_grade, youth_education}.
- **Fjern/nedgradér**: wellbeing (dekoration), og den overflødige af exam/youth.
- **Overvej**: at flytte class_size + daycare_ratio + educated_staff til en separat
  "kommunal service/normering"-vinkel - de er input-mål, ikke uddannelses-outcomes, og de hører
  tematisk sammen. Alternativt behold med lav vægt og vær ærlig om at de er inputs.

### 4. Sundhed - TILFØJ outcome, slank input (høj prioritet, stærk datakilde findes)
I dag mangler et mål for *oplevet* sundhed. life_expectancy (std 1,3) og laegekontakt (std 2,4)
differentierer næsten ikke; gp_distance er en geografi-proxy (r = 0,74 med hjemsyg).
- **Tilføj**: dårligt mentalt helbred + selvvurderet helbred fra Sundhedsprofilen (D3 - verificeret).
  Dette er det vigtigste enkelt-løft i hele modellen: et ægte outcome-mål for befolkningens sundhed.
- **Fjern/flet**: laegekontakt (retning omdiskuterbar), ét af de to sygehusmål (r = 0,64).
- Foreslået sæt (6): selvvurderet helbred, dårligt mentalt helbred, middellevetid (anker),
  ét sygehusmål, medicin (N06), boerneovervaeght.

### 5. Mobilitet - BESLUT (medium prioritet)
public_transport har kun 5 mulige værdier (kommunegruppe-data), 28 % kappet, og kommunen kan
ikke påvirke sin score. r = 0,74 med commute_distance → kategorien straffer by/land dobbelt.
- Enten **erstat** med kommune-specifik tilgængelighedsdata (D2), eller **acceptér åbent** at
  Mobilitet i praksis er en by/land-strukturindikator og skriv det på metodesiden.
- Fjern IKKE uden erstatning - retningen er korrekt, det er opløsningen der er grov.

### 6. Tryghed - HÅNDTÉR mætning (medium prioritet)
crime_rate er kappet for 44 % af kommunerne (kan ikke skelne de tryggeste).
- Foretruk­ken løsning: **snævrere gerningstype** (borgervendt kriminalitet: indbrud + vold +
  tyveri i stedet for alle overtrædelser) - mindre mættet og mere trygheds-relevant. Se D2.
- Alternativ: hæv cappen specifikt for crime_rate eller brug log-skala.

### 7. Foreningsliv, Kultur - MINDRE justeringer (lav prioritet)
- Foreningsliv: 3 af 4 indikatorer er input (udgifter/faciliteter); kun idrætsmedlemskab er
  deltagelse. Overvej CFR-medlemstal bredere (D4) som ægte deltagelsesmål. facilities × spending
  overlapper konceptuelt.
- Kultur: OK. kultur_spending × sports_spending er kun r = 0,13 (godt - Kultur og Foreningsliv
  overlapper ikke). Overvej e-udlån som supplement til biblioteksudlån (strukturelt faldende).

### 8. Demokrati, Ligestilling, Klimatilpasning, Energi - forsvarlige
Demokrati (r = 0,76 er robusthed, ikke dobbelttælling). Ligestilling OK. Energi er modellens
stærkeste dimension (absolut mål, god spredning, ingen mætning). Klimatilpasning: behold den ene
proxy med tydelig mærkning, søg supplement (D5).

---

## C. Struktur- og logik-anbefalinger (på tværs)

### C1. 150-cappen: gør den ærlig og indikator-specifik
I dag klippes ALLE sociale ratios hårdt ved 150. Det mætter crime_rate (44 %), public_transport
(28 %), vacant_housing (27 %) m.fl. og løfter deres gennemsnit kunstigt.
Anbefaling: (a) behold cappen som standard, men (b) tillad et højere loft eller en blød
kompression (fx sqrt over 150) for stærkt højreskæve indikatorer, og (c) vis "150+" i UI så
brugeren ved at værdien er afskåret. Alternativt: log-transformér de få skæve indikatorer før
ratio-beregning. Dette er et bevidst afvejningsvalg mellem robusthed og opløsning.

### C2. Worst-of-ærlighed: vis hvad der reelt binder
I flere øko-dimensioner afgør én sub reelt scoren: PM2.5 binder i 100 % af kommunerne (NO2 i 0 %),
forbrugs-CO2 i 89 %, bio_vasentlig i 96 %. Det er ikke forkert (worst-of = vagthundslogik), men
det bør stå på metodesiden hvilke subs der driver, og hvilke der er vagthunde. Konkret: tilføj
binder-tabellen fra indikator-gennemgangen til metodesiden.

### C3. Redundansregel skal gælde PÅ TVÆRS af dimensioner
Fattigdomsklyngen (B2) viser at r = 0,87 kan optræde mellem to forskellige kategorier. Kør
korrelationstjekket globalt, ikke kun inden for hver kategori, som fast del af metode-review.

### C4. Forurening: cap pesticid-ratioen
Forurening er et gennemsnit af 4, men pesticider har std 180 (spænd 0-884) mod 35-38 for de
andre. Fjernes pesticider flytter dimensionen 27 point (de andre 11-16) - én indikator ejer
dimensionen. Anbefaling: cap pesticid-ratioen ved fx 300 (som VP3/biodiversitet allerede er),
så vægtningen bliver reel. 0/101-gulv-logikken bevares.

### C5. Baseline-konsistens (allerede delvist løst)
baselineType-mærkningen ("mod mål"/"mod landsgennemsnit") er på plads. Sidste skridt: en
eksplicit begrundelse pr. relativ dimension for HVORFOR der ikke findes et absolut mål - så en
politiker ikke kan sige "I valgte landsgennemsnit for at skjule at Danmark er over grænsen".
For næringsstoffer/areal/vand: skriv den planetære grænse som kontekst ved siden af (findes
allerede for areal og biodiversitet - udbred mønsteret).

### C6. Vægtning inden for dimensioner
I dag: simpelt gennemsnit af indikatorer. Det betyder at redundante indikatorer (fx tre
uddannelses-proxies) giver fænomenet ekstra vægt. Når dimensionerne er slanket (B), er simpelt
gennemsnit forsvarligt. Undgå eksplicitte vægte - de er svære at forsvare politisk ("hvorfor
vægter I X dobbelt?"). Løs redundans ved at fjerne indikatorer, ikke ved at nedvægte dem.

---

## D. Datakilde-kandidater (KONFIDENS-MÆRKET - skal verificeres før brug)

Kun D3 er web-verificeret i denne runde. Resten hviler på domæneviden; konfidens angivet.

### D1. Bolig-kvalitet/-byrde
- **Boligbyrde** (boligudgift ift. disponibel indkomst): DST har husstandsindkomst og
  boligudgiftsdata - sandsynligt at et kommunefordelt mål kan konstrueres. *Konfidens: middel.*
- **Energimærke-fordeling** pr. kommune (andel boliger i D-G): Energistyrelsens
  energimærkedatabase / SparEnergi + BBR. Kommunefordelt statistik findes sandsynligt.
  *Konfidens: middel. Verificér adgang.*
- **Hjemløshed** pr. 1.000 indb.: VIVE's nationale hjemløsetælling er kommunefordelt, men kun
  hvert 2. år og med usikkerhed i små kommuner. *Konfidens: middel-høj på eksistens, lav på
  årlig opdatering.*

### D2. Mobilitet + Tryghed (kommune-opløsning)
- **Kollektiv trafik-tilgængelighed** kommune-specifik: Rejseplanen/Trafikstyrelsens åbne data,
  eller DST-tabel over afstand til nærmeste station/stoppested. *Konfidens: lav - skal verificeres
  om noget findes på ægte kommuneniveau (ikke gruppe).*
- **Borgervendt kriminalitet** (undergruppe af STRAF11): Statistikbankens STRAF-tabeller har en
  gerningstype-variabel - man kan sandsynligt vælge indbrud/vold/tyveri i stedet for alle
  overtrædelser. *Konfidens: høj på at variablen findes; kræver test af mætning.* Dette er et
  billigt fix (samme API, snævrere udtræk).

### D3. Sundhed-outcome (VERIFICERET)
- **Sundhedsprofilen "Hvordan har du det?"** (Den Nationale Sundhedsprofil, SST/regionerne):
  kommunefordelt selvvurderet helbred, dårligt mentalt helbred (lav score på mental helbredsskala),
  ensomhed, svær overvægt. Store bølger hvert 4. år (2021, midtvejs 2023, næste 2025).
  Aggregerede kommunetal publiceres; mikrodata kræver ansøgning. *Konfidens: høj.*
  Forbehold: survey-baseret (stikprøvestørrelse i små kommuner), opdateres hvert 4. år - dvs.
  samme kommunetal i flere Doughnut-editioner. Klart det stærkeste enkelt-løft; bør prioriteres.

### D4. Foreningsliv-deltagelse
- **Centralt ForeningsRegister (CFR)** / medlemstal: kommunefordelte medlemstal for DIF/DGI/
  Firmaidrætten. *Konfidens: middel - verificér om data er offentligt tilgængeligt uden aftale.*
  Idrætsmedlemskab (IDRAKT02) dækker allerede en del af dette; CFR kunne give bredere foreningsliv.

### D5. Klimatilpasning-supplement
- **Oversvømmelsesrisiko** (areal/bygninger i risikozone for hav/skybrud/grundvand): Danmarks
  Miljøportal / Miljøstyrelsens KAMP / klimatilpasning.dk kortdata. *Konfidens: middel på
  eksistens, lav på let kommune-aggregering (ofte rasterkort der kræver GIS-arbejde som
  luftkvalitet og biodiversitet).* Vil kræve samme type spatial join som luft/bio.
- **DK2020-klimaplaner** status pr. kommune (har kommunen en vedtaget klimatilpasningsplan):
  binær/kategorisk, let at skaffe, men svag som kvantitativ indikator.

### D6. Økologiske supplementer (fra afbrudt research - alle ubekræftede)
- PFAS/jordforurening pr. kommune (regionernes V1/V2-kortlægning, DKjord/Miljøportal WFS).
- Nyere forbrugs-CO2 end 2011-estimatet (CONCITO kommune-forbrugsregnskaber hvis de findes).
- Energi Data Service REshare/ReCoverageMunicipality (lokal VE-dækning af elforbrug) - allerede
  noteret i åbne-tråde-dokumentet.

---

## E. Foreslået rækkefølge for Sonnet 5 / Opus-implementering

Fase 1 - billige, høj-værdi fixes (ingen ny dataindsamling):
1. C4: cap pesticid-ratioen ved 300 (ét tal i build_master_csv.py).
2. B2-delvist: flyt low_income fra Lighed, konsolidér Velfærds fattigdomsmål (kun konfig i
   shared.ts + metodeside, data findes allerede).
3. B3: slank Uddannelse (fjern wellbeing + én uddannelses-proxy).
4. C2: tilføj binder-tabel + worst-of-ærlighed til metodesiden.
5. D2-Tryghed: test snævrere STRAF-udtræk mod mætning.

Fase 2 - kræver dataverifikation + nyt fetch-script:
6. D3: Sundhedsprofilen mental/selvvurderet helbred → Sundhed (størst løft).
7. B1: Bolig gentænkes med boligbyrde/energimærke.
8. B5/D2: Mobilitet - beslut kilde eller dokumentér som strukturmål.

Fase 3 - større/eksperimentelt:
9. D5: Klimatilpasning-supplement (GIS-arbejde).
10. C1: indikator-specifik cap-håndtering.

Modelanbefaling: Fase 1 er Sonnet 5-arbejde (afgrænsede ændringer med klar test). Fase 2-3's
metodebeslutninger (hvilke indikatorer ind/ud, hvordan vægtes) er Opus/sparring - de er
politisk-metodiske valg, ikke tekniske. Al ny indikator følger CLAUDE.md's "tilføj indikator"-flow.
