# Klimatilpasning - metodenote og fremtidigt arbejde

**Opdateret:** Maj 2026
**Status:** Én indikator implementeret (proxy). Dimensionen er underudviklet.

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
| Landsgennemsnit (maj 2026) | ~26 skader pr. 1.000 indb. |
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
- **Grøn infrastruktur/permeable overflader:** Ingen offentlig datakilde på kommuneniveau.
- **Kommunale klimatilpasningsinvesteringer:** Budget/regnskabsdata via DST REGK, men svær at isolere klimatilpasning fra øvrige anlæg.

### Alternativ tilgang: Komposit-sårbarhedsindeks

En mere retfærdig indikator ville kombinere:
1. Klimaeksponering (DMI Klimaatlas)
2. Sårbarhed (andel ældre/lavindkomst i risikozone)
3. Tilpasningskapacitet (grøn infrastruktur, investeringer)

Dette er komplekst men fagligt korrekt. Se CONCITO (2024): "Adaptation approaches in Danish municipalities' climate action plans" for metodiske tilgange.

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
