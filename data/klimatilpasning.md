# Klimatilpasning - metodenote og fremtidigt arbejde

**Opdateret:** September 2026 (undersøgelse af Kystplanlægger og HIP, se nedenfor)
**Status:** To indikatorer implementeret: forsikringsskader (`vejr_skader`) og kystrisiko i 2070 (`kystrisiko`, fra sep. 2026). Kategorien måler restrisiko: hvor udsat kommunen er, når det der allerede er gjort, er regnet med. Kategorien er gennemsnittet af de to, og kystrisikoen tæller højst 100, så fravær af kyst ikke udligner vejrskader (CHANGELOG 25. sep. 2026). På sigt er den rigtige løsning at lægge skaderne sammen i kroner pr. indbygger, hvis F&P kan levere udbetalinger pr. kommune.

---

## Implementeret indikator

### vejr_skader - Vejrrelaterede forsikringsskader pr. 1.000 indb.

| Felt | Værdi |
|------|-------|
| Kilde | F&P (Forsikring & Pension) |
| URL | https://fogp.dk/tal-og-analyser/saadan-er-danmark-blevet-ramt-af-vejrrelaterede-skader-de-seneste-aar/ |
| Data-URL | https://datawrapper.dwcdn.net/NDLlA/4/dataset.csv |
| Tidsperiode | Q1 2023 - Q4 2025 (2,5 år akkumuleret) |
| Dækning | ~90% af forsikringsmarkedet |
| Nøgle | Kommunenavn (ikke kommunekode) |
| Landsgennemsnit | befolkningsvægtet, ca. 22 skader pr. 1.000 indb. (sep. 2026; indtil da uvægtet, ca. 26) |
| Ratio-type | Invers social: (landsgennemsnit / kommune_val) × 100 |

**Inkluderer:** Storm, skybrud, hagl, sne/frost, stormvand.
**Ekskluderer:** Stormflodsskader (håndteres af Naturskaderådet separat).

### Centrale forbehold

1. **Eksponering vs. kapacitet:** Indikatoren måler outcome (faktisk skade), ikke hvad kommunen HAR gjort for at beskytte borgerne. Høj skadesfrekvens kan skyldes geografisk eksponering snarere end dårlig lokal tilpasning.

2. **Strukturel geografisk bias:** Vestkystkommuner (Lemvig, Fanø, Varde m.fl.) og ø-kommuner er strukturelt mere udsat for storm. De vil altid score lavt selv med fremragende klimatilpasning. Kommuner i Storkøbenhavn scorer højt pga. lav stormeksponering, ikke fordi de er bedre tilpasset.

3. **Stormflod mangler:** Naturskaderådets stormflodsskader er IKKE inkluderet i F&P's tal. For kystnære kommuner (inkl. Thisted) undervurderer indikatoren dermed den reelle klimarisiko. Naturskaderådet udgiver årsrapporter med skadestatistik, men det er uklart om kommunefordelt data er offentligt tilgængeligt.

4. **Kort tidsserie:** Kun 2,5 år (2023-2025). Et enkelt ekstremt vejrår kan dominere resultatet for en lille kommune. Fanø og Lemvig topper listen (66 pr. 1.000) - delvist pga. de er lille og udsat.

5. **Forsikringsmarkedsdækning:** ~10% af markedet mangler. Kan give skævhed hvis udfaldende selskaber er geografisk koncentrerede.

---

## Fremtidige indikator-kandidater

### Tier 1 - Fri data, kommuneniveau, realistisk at hente

**DMI Klimaatlas** (dmi.dk/klimaatlas - fri download som Excel/GIS):
- Ændring i 10-årsregn 2071-2100 vs. 1991-2020 (%) - eksponerings-indikator
- Fremtidig havniveaustigning cm (RCP8.5) - eksponerings-indikator
- Fremtidig sommertemperaturstigning - relevant for varmestress

OBS: Disse er fremtidige klimaprojektioner, ikke observerede data. Velegnet som risikoeksponering, ikke som tilpasningskapacitet.

**Kystdirektoratets risikokortlægning (december 2024):**
- 51 kommuner udpeget med "væsentlig oversvømmelsesrisiko" (binær variabel)
- Ikke særlig differentieret - kan bruges som kontekst, ikke score
- Kystplanlæggerens datapakke giver derimod et kontinuert tal pr. kommune, se "Undersøgt sep. 2026" nedenfor

### Tier 2 - Kræver GIS-behandling

**KAMP (Danmarks Miljøportal - kamp.klimatilpasning.dk):**
- Andel bebygget areal i bluespot-zone (skybrudssøer)
- GIS-baseret, kræver Python + geopandas-behandling pr. kommune
- Stærkere indikator fordi den skelner by/land eksponering

**Naturskaderådets stormflodsskader:**
- Årsrapporter tilgængelige (naturskaderaadet.dk/regler-viden-og-vejledning/publikationer)
- Uklart om kommunefordelt data er offentligt. Kræver evt. aktindsigt/kontakt til rådet.
- URL årsrapport 2024: https://naturskaderaadet.dk/media/fapd3j1h/aarsrapport_2024_naturskaderaadet.pdf

### Tier 3 - Kapacitets-indikatorer (svære at operationalisere)

Disse måler hvad kommunen GØR, ikke hvad der sker. Langt mere relevant for Doughnut-rammen, men data er svær at finde på kommuneniveau:

- **DK2020 ambitionsniveau:** Alle 98 kommuner har nu plan (ingen variation), men kvalitet varierer. CONCITO har vurderet planerne.
- **Grøn infrastruktur/permeable overflader:** SDFI's befæstelseskort findes (nævnt i KL's vejviser og vist som støttelag i HIP, lavet på forårsortofoto, skråfoto og højdedata). Ikke undersøgt om det er landsdækkende og kan summeres pr. kommune. Befæstelse er desuden et tilstandsmål, ikke en indsats.
- **Kommunale klimatilpasningsinvesteringer:** Budget/regnskabsdata via DST REGK, men svær at isolere klimatilpasning fra øvrige anlæg.

### Alternativ tilgang: Komposit-sårbarhedsindeks

En mere retfærdig indikator ville kombinere:
1. Klimaeksponering (DMI Klimaatlas)
2. Sårbarhed (andel ældre/lavindkomst i risikozone)
3. Tilpasningskapacitet (grøn infrastruktur, investeringer)

Dette er komplekst men fagligt korrekt. Se CONCITO (2024): "Adaptation approaches in Danish municipalities' climate action plans" for metodiske tilgange.

---

## Undersøgt sep. 2026: Kystplanlægger og HIP pr. kommune

Anledning: KL's "Data- og værktøjsoversigt fra 5 webinarer om GIS-DATA-Klimatilpasning" (v1.0, 2023). Af kilderne i oversigten var Kystplanlægger og HIP de to, der kunne give et sammenligneligt tal for alle 98 kommuner. Kystplanlæggerens risiko for 2070 blev derefter indført som indikatoren `kystrisiko` (`scripts/fetch_kystrisiko.py`, se CHANGELOG 25. sep. 2026). Tallene for 2020 nedenfor er prøveberegningen; indikatoren bruger 2070, fordi kategorien skal måle robusthed over for klimaforandringerne. HIP-tallene er kun en prøveberegning.

### Kystplanlægger (Kystdirektoratet) - oversvømmelse og erosion fra havet

| Felt | Værdi |
|------|-------|
| Kilde | Kystplanlæggerens datapakke, version 1 af 18. marts 2021 |
| URL | https://kystplanlaegger.dk/webgis-og-data/hent-data (zip på sftp.statens-it.dk, 4,3 GB, frit tilgængelig) |
| Anvendte lag | `Oversvømmelse/Risiko/Oversvømmelses_Risiko_{2020,2070}.tif` og `Erosion/Risiko/Erosions_risiko_{2020,2070}.tif` |
| Enhed | Forventet skade i kr./år pr. 100 m-celle (risiko = skade vægtet med sandsynligheden for 50-, 100-, 1.000- og 10.000-årshændelser) |
| Scenarie | RCP8.5 for 2070 og 2120 |

**Metode i prøveberegningen:** Kun de fire risikofiler blev hentet (ca. 70 MB hver, via range-requests i zip-filen). Cellerne blev summeret inden for DAWA's kommunegrænser (EPSG:25832). En celle tildeles den kommune, dens centrum ligger i, og kystceller med centrum i havet tildeles den kommune, de berører. Uden den regel tabes 3 % af oversvømmelsesrisikoen og 25 % af erosionsrisikoen, fordi skaden ligger i kystlinjen. Tallet pr. indbygger bruger folketallet 1. januar 2025.

**Resultat (2020):**
- Landstotal: 2.612 mio. kr./år fra oversvømmelse og 150 mio. kr./år fra erosion, i alt ca. 460 kr. pr. indbygger. I 2070 bliver det 4.091 hhv. 1.919 mio. kr./år.
- Højest pr. indbygger: Fanø (2.888 kr.), Lemvig (2.143), Dragør (2.103), Læsø (2.098), Tårnby (2.013), Hvidovre (2.003) og Skive (1.720).
- Thisted: 20,6 mio. kr./år fra oversvømmelse og 3,9 mio. fra erosion, 574 kr. pr. indbygger. I 2070 bliver det 1.811 kr., fordi erosionen vokser fra 3,9 til 41,8 mio. kr./år.
- 19 kommuner ligger under 1 kr. pr. indbygger (indlandskommuner) og 21 under 10 kr. Medianen er ca. 400 kr.

**Forbehold:**
- Datapakken er fra 2021 og ikke opdateret siden. Kystdirektoratet skriver selv, at skadesberegningerne bygger på nationale datasæt, hvoraf nogle ikke er af nyeste dato, og at data ikke kan bruges til detailanalyser. Formålet er ifølge Kystdirektoratet overblik "i den enkelte kommune som på tværs af kommunegrænser", hvilket svarer til platformens brug.
- Det er modelberegnet restrisiko. Ifølge metoderapporten (januar 2023, afsnit 2 og 7) indgår diger og klitter, fordi de ligger i Danmarks Højdemodel fra 2014-2015 med kommunernes rettelser. Anden kystbeskyttelse indgår som udgangspunkt ikke, og for den kroniske erosion antages eksisterende høfder og skråningsbeskyttelse at kollapse. Tiltag efter højdemodellen og datapakken fra 2021 slår derfor ikke igennem, før Kystdirektoratet opdaterer kortlægningen.
- Metoderapporten oplyser ikke et landstal i kr./år, så landstotalen ovenfor kan ikke kontrolleres direkte mod den.
- De 19 kommuner uden kystrisiko giver et scoringsproblem: med en invers ratio mod landsgennemsnittet (som `vejr_skader`) deles der med nul, og de ender alle på loftet 150.

### HIP - terrænnært grundvand

| Felt | Værdi |
|------|-------|
| Kilde | HIP (Klimadatastyrelsen og GEUS), offentlig download uden token |
| URL | https://cdn.dataforsyningen.dk/HIP/historiske_modelberegninger/ |
| Afprøvet 100 m | `terraennaert_grundvand_100m/statistik_1991-2020.zip` (3,4 GB): `annual_t10`, `annual_probability_depth_less_than_1m` |
| Afprøvet 10 m | `terraennaert_grundvand_10m.zip` (3,2 GB): `shallow_groundwater_depth_statistics_10m_winter_p10_1991_2025.tif` (int16, dybde i cm, nedskaleret fra 100 m med maskinlæring) |
| Adresser | Alle adgangsadresser fra DAWA (ca. 2,5 mio.), ikke vægtet med beboere |

HIP har ikke et færdigt lag med "berørte bygninger" til download, så prøveberegningen lagde adgangsadresserne ned over rasteret.

**100 m-modellen kan ikke bruges til formålet.** Ved en 10-årshændelse står grundvandet højere end 0,5 m under terræn ved medianen 71 % af kommunens adresser, og Albertslund, Glostrup, Brøndby og Hvidovre ligger øverst. Opløsningen er for grov til at skelne bebyggelse fra lavbund i samme celle.

**10 m-versionen giver plausible tal.** Målt som andelen af adresser, hvor grundvandet i de 10 % vådeste vinterdage står højere end 50 cm under terræn:
- Medianen er 3,7 % (kvartiler 1,5 % og 7,9 %).
- Højest ligger Lemvig (36,5 %), Læsø (34,8 %), Samsø (24,6 %), Fanø (19,1 %), Nordfyns (16,6 %) og Frederikshavn (16,3 %).
- Lavest ligger Frederiksberg, Brøndby, Albertslund og Hvidovre, alle under 0,2 %.
- Thisted ligger på 7,8 %. Med en grænse på 1 m bliver det 47 %, og så skelner målet dårligt, fordi medianen er 40 %.

**Forbehold:** 10 m-versionen er nedskaleret med maskinlæring og ikke valideret mod pejlinger i denne undersøgelse. Adgangsadresserne omfatter også sommerhuse og erhverv. Grænsen på 50 cm og vinterens 10 %-fraktil er valgt til prøven, ikke fagligt begrundet.

### Hvad de to kilder tilføjer i forhold til `vejr_skader`

Rangkorrelationen (Spearman, 98 kommuner) er 0,62 mellem Kystplanlægger og `vejr_skader`, 0,67 mellem terrænnært grundvand og `vejr_skader` og 0,53 mellem de to nye. De tre mål fanger i høj grad den samme geografiske udsathed: lave kyster, Vestjylland og øerne. Kystplanlæggeren tilføjer det, `vejr_skader` mangler (stormflod og erosion, jf. "Centrale forbehold" punkt 3 under den implementerede indikator). Terrænnært grundvand tilføjer mindre, er modelberegnet i to led og er ikke valideret.

Ingen af de to kilder måler tilpasningsevne (Tier 3). Den grundlæggende svaghed ved dimensionen, at den måler geografi frem for indsats, er derfor ikke løst.

---

## Datakvalitetsvurdering (nuværende indikator)

| Kriterie | Vurdering |
|----------|-----------|
| Tilgængelighed | ★★★★★ Fri download |
| Dækning | ★★★★☆ 98/98 kommuner, ~90% marked |
| Aktualitet | ★★★★☆ 2023-2025, opdateres kvartalsvis |
| Validitet | ★★☆☆☆ Proxy - måler eksponering, ikke kapacitet |
| Fairness | ★★☆☆☆ Strukturelt biased mod vestkyst/øer |

**Samlet:** Acceptabel MVP-indikator. Bør på sigt suppleres eller erstattes af kapacitets-indikatorer.

---

## Opdateringsflow

Datawrapper-kortet hos F&P opdateres løbende. For at opdatere indikatoren:

```bash
cd /sti/til/doughnut
python3 scripts/fetch_klimatilpasning_data.py
```

Scriptet henter automatisk nyeste data fra Datawrapper-URL og rebuild master-CSV.

**OBS:** Datawrapper-URL'en (NDLlA/4/) kan ændre sig når F&P opdaterer analysen. Tjek om URL'en stadig virker ved næste dataopdatering. Alternativt kan data hentes direkte fra F&P's kvartalsvise Excel-statistik, men det kræver manuel aggregering pr. kommune.
