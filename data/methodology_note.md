# Metodenote: Nutidsjustering af forbrugsbaseret CO2 pr. indbygger (2011 -> 2023)

**Dato:** 12. april 2026
**Forfatter:** Klimateamet, Thisted Kommune (beregning assisteret af AI)
**Version:** 1.1 - Tier 1 (kun national skalering, korrigeret skaleringsfaktor)

---

## 1. Formål

Denne note dokumenterer metoden bag estimering af forbrugsbaseret CO2 (CBA) pr. indbygger for 97 danske kommuner i 2023, baseret på en nutidsjustering af 2011-data fra Osei-Owusu et al. (2020). Christiansø (0 i kildedata) er filtreret fra.

Resultatet er et estimat, ikke en måling. Det er beregnet til brug i Doughnut-platformens dimension "Forbrugsbaserede udledninger" og er mærket med eksplicitte forbehold.

**Vigtig metodisk pointe:** Skaleringsfaktoren beregnes udelukkende fra Energistyrelsens (ENS) egen tidsserie for forbrugsbaserede udledninger (2011 → 2023), ikke ved at blande Osei-Owusu's absolutte niveau med ENS's. De to modeller giver forskellige absolutte niveauer (15,71 vs. 14,07 ton/cap i 2011), men det er den relative ændring over tid - målt konsistent inden for én metode - der er relevant for nutidsjusteringen.

## 2. Datagrundlag

### 2.1 Baseline (2011)

**Kilde:** Osei-Owusu, K.A. et al. (2020). "Tracking the carbon emissions of Denmark's five regions from a producer and consumer perspective." *Ecological Economics*, 177, 106778.

**Metode i artiklen:** Forfatterne kombinerer LINE-modellen (kommunal interregional IO-model, 40 sektorer) med EXIOBASE v3.4 (global MRIO, 200 produkter, 49 regioner). Husholdningernes endelige efterspørgsel disaggregeres til 98 kommuner via forbrugsudgifter fra Danmarks Statistiks Forbrugsundersøgelse (46 forbrugskategorier). Direkte husholdningsemissioner (opvarmning, transport) hentes fra Region Syddanmarks data2go.dk-database og lægges oven i IO-beregningen.

**Nøgletal 2011:** Per capita = 15,71 ton CO2e/cap. Population = 5.579.204 (Osei-Owusu Table 1, afviger marginalt fra DST's 5.560.628 pr. 1.1.2011). Bemærk: Dette absolutte niveau afviger fra ENS's egen beregning (14,07 ton/cap i 2011) - forskellen skyldes modelforskelle (EXIOBASE-version, sektoraggregering, datakilder). Se afsnit 3.1 for hvorfor dette håndteres.

**Kommunal variation:** 13,08 - 24,06 ton/cap. Variationen drives primært af: (1) indkomstniveau (via forbrugsudgifter), (2) direkte husholdningsemissioner (opvarmning + transport), (3) regionale forbrugsmønstre. Rige forstadskommuner (Gentofte, Hørsholm, Rudersdal) ligger højest. Bykommuner med lav indkomst (Albertslund, Ishøj) ligger lavest.

### 2.2 Nationalt CBA-tal (2023)

**Kilde:** Energistyrelsen, "Danmarks globale klimapåvirkning - Global Afrapportering 2025" (publiceret 30. april 2025).

**Nøgletal 2023:** Danmarks forbrugsbaserede klimaaftryk = ca. 60 mio. ton CO2e. Ca. 10 ton CO2e per dansker. Fald på 3,3 mio. ton (5%) fra 2022 (ca. 63 mio. ton). 60% af udledningerne sker uden for Danmarks grænser.

**Metodisk sammenlignelighed:** ENS GA bruger ligeledes EXIOBASE-baseret MRIO inkl. importerede emissioner. Metoden er den tættest sammenlignelige med Osei-Owusu's tilgang. Der kan dog være forskelle i EXIOBASE-version (v3.4 i 2011 vs. nyere), sektoraggregering og datakilder til husholdningsforbrug. Denne usikkerhed er ikke kvantificeret.

### 2.3 Befolkningstal

**Kilde:** Danmarks Statistik, FOLK1A.
- 2011K1: 5.560.628
- 2023K1: 5.932.654

## 3. Justeringsmetode

### 3.1 Justering 1: National per-capita skaleringsfaktor

**Princip:** Skaleringsfaktoren beregnes fra ENS's egen CBA-tidsserie for at undgå at blande to forskellige modellers absolutte niveauer. Osei-Owusu (2020) og ENS Global Afrapportering bruger begge EXIOBASE-baseret MRIO, men giver forskellige absolutte niveauer for 2011 (15,71 vs. 14,07 ton/cap). Ved at bruge ENS's egne tal for både 2011 og 2023 isolerer vi den reelle ændring i forbrugsbaseret CO2 over tid - uden at en metodisk niveauforskel forveksles med en reel reduktion.

**Beregning:**

```
ENS_per_capita_2011 = 14,07 ton/cap  (ENS Global Afrapportering, egen tidsserie)
ENS_per_capita_2023 = 60.000.000 / 5.932.654 = 10,11 ton/cap  (ENS GA25 / DST FOLK1A)
skaleringsfaktor = 10,11 / 14,07 = 0,7186
```

**Anvendelse:** Faktoren ganges multiplikativt på alle 97 kommuners 2011-baseline fra Osei-Owusu:

```
cba_2023_estimate_k = cba_2011_k × 0,7186
```

**Hvorfor ikke bruge Osei-Owusu's 15,71 som divisor?** Det ville give en faktor på 0,6435 - en nedgang på 35,6%. Men ca. 7 procentpoint af den nedgang ville afspejle forskellen mellem de to modellers beregningsmetode, ikke en reel reduktion i forbrugsbaseret CO2. ENS-til-ENS-ratioen (0,7186, -28,1%) fanger kun den reelle ændring over tid.

### 3.2 Justering 2 og 3: Ikke gennemført

Justering 2 (kommunespecifik korrektion for direkte husholdningsemissioner) og Justering 3 (el- og fjernvarmemix) er ikke gennemført i denne version. Begrundelse:

1. **Klimaregnskabet.dk** opgør territorielle udledninger (scope 1+2), mens Osei-Owusu's tal er forbrugsbaserede (CBA, inkl. import). At trække territorielle delkomponenter ind i en forbrugsbaseret model kræver eksplicit isolation af den fælles komponent (direkte husholdningsemissioner) og en troværdig 2011-baseline for samme komponent - begge dele med betydelig usikkerhed.

2. **Risiko for falsk præcision:** Kommunespecifikke justeringer baseret på territorielle data kan flytte kommuner i en retning der ser ud som præcision, men reelt afspejler metodisk inkompatibilitet snarere end reelle ændringer i forbrugsmønster.

3. **80/20-vurdering:** Justering 1 fanger det væsentligste: det nationale fald i forbrugsbaseret CO2 (ca. 28%). Justering 2 og 3 ville primært ændre den relative rangorden mellem kommuner - en effekt der er svær at validere uden en fuld re-modellering.

## 4. Resultater

**Interval:** 9,40 - 17,29 ton CO2e/cap (alle inden for det forventede 6-22 interval).

**Gennemsnit:** 11,55 ton/cap (uvægtet kommunegennemsnit - højere end ENS's befolkningsvægtede nationale 10,11 fordi kommuner med lav befolkning og højt forbrug trækker op).

**Ændring:** -28,1% for alle kommuner (ensartet national skalering).

**Rangorden:** Uændret i forhold til 2011. Alle kommuner skaleres med samme faktor, så den relative spredning (max/min = 1,84) er identisk.

**Eksempel:** Thisted: 16,97 → 12,19 ton/cap (-28,1%).

## 5. Begrænsninger og forbehold

Disse forbehold skal kommunikeres sammen med tallene i platformen:

1. **Ensartet national skalering:** Alle kommuner nedskaleres ens. I virkeligheden har nogle kommuner (fx dem med oliefyr der er skiftet til varmepumper) reduceret mere end andre. Modellen fanger ikke denne differentiering.

2. **Forbrugsudgifter ikke opdateret:** Den kommunale variation i 2011-baselinen er primært drevet af indkomst og forbrugsmønstre. Disse mønstre kan have ændret sig fra 2011 til 2023 (fx ændret pendlingsmønster efter COVID, urbanisering, boligprisudvikling).

3. **Importerede emissioner i forbrugsvarer:** CO2-indholdet i importerede varer (mad, tøj, elektronik, flyrejser osv.) er nedskaleret nationalt - ikke opdateret pr. produktkategori eller handelspartner.

4. **Metodisk drift:** Osei-Owusu bruger EXIOBASE v3.4 (2011). ENS GA25 bruger sandsynligvis en nyere EXIOBASE-version. Ændringer i sektorklassifikation, emissionsfaktorer og handelsdata mellem versioner kan påvirke sammenligneligheden. Denne effekt er ikke kvantificeret.

5. **"Ca. 60 mio. ton":** ENS GA25 angiver tallet som tilnærmet. En afvigelse på +/- 2 Mt ville ændre per-capita fra 9,77 til 10,45 og skaleringsfaktoren fra ca. 0,69 til 0,74 - en usikkerhed på ca. +/- 3,5% på de endelige kommunetal.

6. **Christiansø** er filtreret fra (0 i kildedata, ca. 90 indbyggere).

## 6. Anbefalet mærkning i platformen

```
Forbrugsbaserede CO2-udledninger (estimat, 2023)
Kilde: Osei-Owusu et al. (2020), nutidsjusteret med Energistyrelsens 
Global Afrapportering 2025. National skalering - ikke kommunespecifikt opdateret.
```

## 7. Kilder

- Osei-Owusu, K.A., Nielsen, O.A., Birgisdottir, H. & Siemsen, T.I. (2020). "Tracking the carbon emissions of Denmark's five regions from a producer and consumer perspective." *Ecological Economics*, 177, 106778. https://doi.org/10.1016/j.ecolecon.2020.106778 (Kommunal CBA-baseline 2011)
- Energistyrelsen (2025). "Danmarks globale klimapåvirkning - Global Afrapportering 2025." (National CBA 2023 + historisk tidsserie inkl. 2011-værdi på 14,07 ton/cap)
- Danmarks Statistik, FOLK1A (befolkningstal).
