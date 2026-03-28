# Statbank-tabeller til Doughnut Kommune-platformen

*Kortlægning af Danmarks Statistiks API-tabeller til doughnut-dimensioner. Opdateret marts 2026.*

---

## SOCIALE DIMENSIONER (den indre ring)

### 1. Mad og ernæring
**Dækning: Delvis** - ingen direkte data om madfattigdom på kommuneniveau

| Tabel-ID | Titel | Kommuneniveau |
|---|---|---|
| SILC100 | Uopfyldt behov for læge og tandlæge (proxy for materiel afsavn) | Nej |
| SILC20 | Husstandenes økonomiske afsavn | Nej |
| OEKO11 | Økologiske bedrifter og arealer | Ja |
| SDG12031 | Madaffald fordelt på de fem led | Nej |

*Mangler: Direkte indikatorer for madfattigdom eller fødevaresikkerhed på kommuneniveau. Proxy via SILC (lavindkomst).*

---

### 2. Sundhed
**Dækning: God**

| Tabel-ID | Titel | Kommuneniveau |
|---|---|---|
| HISB7 | Middellevetid ved fødslen | Ja (delvis) |
| DOD | Dødsfald efter alder og køn | Ja |
| SILC60 | Helbredsproblemer (selvvurderet helbred) | Nej |
| SILC100 | Uopfyldt behov for læge og tandlæge | Nej |
| MEDI1 | Køb af receptpligtig medicin | Ja |
| HJEMSYG | Modtagere af hjemmesygepleje | Ja |
| SBR07 | Hospitalsindlæggelser efter socioøkonomisk status | Nej |

---

### 3. Uddannelse
**Dækning: God**

| Tabel-ID | Titel | Kommuneniveau |
|---|---|---|
| HFUDD11 | Befolkningens højest fuldførte uddannelse (15-69 år) | Ja |
| HFUDD21 | Befolkningens højest fuldførte uddannelse (15-29 år) | Ja |
| LABY19A | Uddannelsesniveau, andel i procent | Ja |
| NEET1 | Unge (16-24 år) uden for uddannelse og beskæftigelse | Ja |
| GENMF10 | Gennemførelse af uddannelsesgrupper | Nej |

---

### 4. Indkomst og arbejde
**Dækning: Meget god**

| Tabel-ID | Titel | Kommuneniveau |
|---|---|---|
| INDKP101 | Personindkomster (efter region) | Ja |
| INDKF201 | Familieindkomster | Ja |
| IFOR10 | Lavindkomstgrænse og berørte | Ja (delvis) |
| LABY07 | Relativ fattigdomsandel efter kommunegruppe | Kommunegruppe |
| AUK01 | Offentligt forsørgede (fuldtidsmodtagere) | Ja |
| SILC10 | Økonomisk sårbare (andel personer) | Nej |
| SILC1A | Andel i relativ fattigdom | Nej |
| AKU210K | Beskæftigelse efter alder og køn | Nej (landsplan) |
| RAS200 | Beskæftigelse efter erhverv og uddannelse | Ja |

---

### 5. Fred og retfærdighed
**Dækning: Delvis**

| Tabel-ID | Titel | Kommuneniveau |
|---|---|---|
| STRAF10 | Anmeldte forbrydelser | Ja |
| STRAF24 | Anmeldte forbrydelser pr. 100.000 indbyggere | Ja |
| STRAF5 | Ofre for anmeldte forbrydelser | Nej |
| KRISE1 | Ophold på krisecentre | Ja |
| HERFOR1 | Personer på herberger og forsorgshjem | Ja |

*Mangler: Tillid til institutioner, oplevelse af retssikkerhed.*

---

### 6. Politisk stemme
**Dækning: Svag**

*Statbank dækker ikke dette godt. Valgdeltagelse kan evt. hentes via KMD valgdata eller Danmarks Statistiks særpublikationer. Overvej ekstern kilde.*

---

### 7. Social lighed
**Dækning: God via indkomstdata**

| Tabel-ID | Titel | Kommuneniveau |
|---|---|---|
| IFOR20 | Indkomstfordeling og decilgrænser | Nej |
| SILC1B | Boligbyrde (andel personer) | Nej |
| LIGEIB5 | Offentligt forsørgede (ligestillingsindikator) | Ja |
| BU43 | Børn med sociale støtteforanstaltninger | Ja |
| ANB5 | Anbragte børn og unge | Ja |

---

### 8. Ligestilling
**Dækning: God**

| Tabel-ID | Titel | Kommuneniveau |
|---|---|---|
| LIGEII5 | Ligestillingsindikator, offentligt forsørgede | Ja |
| LIGEII6 | Ligestillingsindikator, offentligt forsørgede | Ja |
| LIGEFI1 | Ligestillingsindikator, barselsdagpenge | Nej |
| LIGEPB1 | Ofre for personfarlig kriminalitet (køn) | Nej |
| LIGEHI12 | Ligestillingsindikator, hjemmehjælp | Ja |

---

### 9. Bolig
**Dækning: God**

| Tabel-ID | Titel | Kommuneniveau |
|---|---|---|
| BOL101 | Boliger efter type og ejerforhold | Ja |
| BOST63 | Boligstøttemodtagere | Ja |
| SILC1B | Boligbyrde (for høj husleje ift. indkomst) | Nej |
| SILC2B | Boligbyrde | Nej |
| HERFOR1 | Hjemløse på herberger | Ja |
| LABY46 | Gennemsnitlig boligareal | Ja |

---

### 10. Netværk og fællesskab
**Dækning: Svag**

| Tabel-ID | Titel | Kommuneniveau |
|---|---|---|
| SILC50 | Generel livstilfredshed | Nej |
| SILC52 | Tillid til fremmede | Nej |

*Statbank dækker ikke foreningsliv, frivillighed eller social kapital direkte. Overvej survey-data fra fx Den Nationale Sundhedsprofil.*

---

### 11. Energi
**Dækning: God på nationalt niveau, begrænset kommunalt**

| Tabel-ID | Titel | Kommuneniveau |
|---|---|---|
| SDG07021 | Vedvarende energis andel af bruttoenergiforbrug | Nej |
| ENE2HO | Energiregnskab i GJ (oversigt) | Nej |
| LABY33 | Nøgletal for energiforbrug og -produktion | Nej |
| ENERGI1 | Priser på elektricitet for husholdninger | Nej |
| BRANDE01 | Boliger med brændeovn og forbrug | Ja (delvis) |

*Kommunalt energiforbrug findes bedre i Energistyrelsens kommunefordelte statistik (energiforbrug.dk) - bør supplere Statbank.*

---

### 12. Vand
**Dækning: Delvis**

| Tabel-ID | Titel | Kommuneniveau |
|---|---|---|
| VANDIND | Indvinding af vand | Nej |
| VANDRG1 | Indvinding af vand (fysisk vandregnskab) | Nej |
| VANDRG2 | Forbrug af vand | Nej |
| VANDUD | Spildevandsudledning | Nej |

*Kommunalt vandforbrug og kvalitet findes bedre via DANVA/vandforsyningsselskaberne.*

---

## PLANETÆRE GRÆNSER (den ydre ring)

### 1. Klimaforandringer
**Dækning: God på nationalt niveau**

| Tabel-ID | Titel | Kommuneniveau |
|---|---|---|
| DRIVHUS | Drivhusgasregnskab (CO2-ækvivalenter) | Nej |
| TEMA9005 | Udledning af drivhusgas | Nej |
| TEMA9008 | Drivhusgasser pr. indbygger | Nej |
| AFTRYK1 | Klimaaftryk (eksperimentel statistik) | Nej |
| AFTRYK2 | Klimaaftryk (eksperimentel statistik) | Nej |
| LABY34 | Nøgletal for drivhusgasudledning | Nej |

*Kommunale CO2-data findes i DK2020-kortlægninger og Klimakompasset. Bør være primær kilde for kommuneniveau.*

---

### 2. Luftforurening
**Dækning: Delvis**

| Tabel-ID | Titel | Kommuneniveau |
|---|---|---|
| MRU1 | Emissionsregnskab | Nej |
| EMM1MU1N | Direkte og indirekte luftemissioner | Nej |
| TEMA9001 | Vækst og drivhusgasudledning | Nej |

*Luftkvalitetsmålinger findes hos DCE (Aarhus Universitet) og DMI - ikke i Statbank.*

---

### 3. Arealanvendelse og natur
**Dækning: Delvis**

| Tabel-ID | Titel | Kommuneniveau |
|---|---|---|
| AREALAN1 | Arealanvendelse | Ja |
| ARE207 | Areal 1. januar | Ja |
| SKOVRG03 | Skovareal (Kyoto) | Nej |
| SKOVRG04 | Skovareal | Nej |
| OEKO11 | Økologiske bedrifter og arealer | Ja |

---

### 4. Ferskvand
Se under social dimension 12 (Vand) ovenfor.

---

### 5. Biodiversitet
**Dækning: Svag i Statbank**

| Tabel-ID | Titel | Kommuneniveau |
|---|---|---|
| FISK33 | Fritlevende fisk og skaldyr (fysisk balance) | Nej |
| SKOVRG05 | Vedmasse (fysisk balance) | Nej |

*Biodiversitetsdata findes primært i Naturstyrelsens og DCE's registre (Naturdata.dk, Artsdatabanken). Statbank dækker ikke dette tilstrækkeligt.*

---

### 6. Kvælstof- og fosforbelastning
**Dækning: Svag**

| Tabel-ID | Titel | Kommuneniveau |
|---|---|---|
| TEMA9010 | Udledning fra landbrug, skovbrug og fiskeri | Nej |
| VANDUD | Spildevandsudledning | Nej |

*Næringsstofbelastning af vandmiljø følges bedst via Miljøstyrelsen og vandområdeplaner.*

---

### 7. Cirkularitet (materialestrømme og affald)
**Dækning: God på kommunalt niveau**
**Status: Implementeret** - to indikatorer: genanvendelsesprocent + affaldsmængde pr. capita

| Tabel-ID | Titel | Kommuneniveau | Indikator |
|---|---|---|---|
| LABY25 | Nøgletal for husholdningsaffald | Ja | Affald kg/capita (inverteret - lavere er bedre) |
| AFFALD | Affaldsproduktion | Ja (delvis) | - |
| LABY24 | Husholdningsaffald | Ja | - |
| MRM2 | Materialestrømsregnskab | Nej | - |

*Genanvendelsesprocent hentes fra consumption_scores.csv (recycling_ratio). Affaldsdata (waste_ratio) er flyttet hertil fra den tidligere "Forurening"-dimension, da affald er en cirkularitetsindikator, ikke novel entities.*

---

### 8. Forurening (novel entities)
**Dækning: Ingen - ingen pålidelig kommunal kilde**

*Den planetære grænse "novel entities" dækker kemisk forurening, mikroplast, persistent organisk forurening (POP), pesticider mv. Denne grænse er allerede overskredet globalt (Persson et al., 2022). Statbank har ingen kommunale data. Mulige fremtidige proxyer:*
- *Pesticidbelastning (Bekæmpelsesmiddel-indikator, Miljøstyrelsen) - primært nationalt*
- *Grundvandsboringer med pesticid-fund (GEUS/Jupiter) - usikkert på kommuneniveau*
- *PFAS-forurening (regionale data fra Region Syddanmark/Nordjylland)*

*Dimensionen vises som "ingen data" (grå) indtil en pålidelig kommunal kilde identificeres.*

---

### 9. Ozonlaget og havforsuring
**Dækning: Ingen**

*Disse dimensioner dækkes ikke af Statbank og er primært nationale/internationale indikatorer. Marginalt relevante på kommuneniveau.*

---

## SAMLET VURDERING

| Dimension | Statbank-dækning | Kommuneniveau | Supplerende kilde |
|---|---|---|---|
| Mad | Svag | Nej | - |
| Sundhed | God | Delvis | Den Nationale Sundhedsprofil |
| Uddannelse | God | Ja | - |
| Indkomst/arbejde | Meget god | Ja | - |
| Fred/retfærdighed | Delvis | Ja | - |
| Politisk stemme | Svag | Nej | KMD Valgdata |
| Social lighed | God | Delvis | - |
| Ligestilling | God | Delvis | - |
| Bolig | God | Ja | - |
| Netværk | Svag | Nej | Sundhedsprofil, frivilligdata |
| Energi | God (nationalt) | Nej | energiforbrug.dk |
| Vand | Delvis | Nej | DANVA |
| Klima/CO2 | God (nationalt) | Nej | DK2020/Klimakompasset |
| Luftforurening | Delvis | Nej | DCE/DMI |
| Areal/natur | Delvis | Ja | - |
| Biodiversitet | Svag | Nej | Naturdata.dk |
| Kvælstof/fosfor | Svag | Nej | Miljøstyrelsen |
| Cirkularitet/affald | God | Ja | Genanvendelse + kg affald/capita |
| Novel entities (kemi) | Ingen | Nej | Miljøstyrelsen, GEUS |
| Ozon/havforsuring | Ingen | Nej | Nationale/EU-kilder |

**Konklusion:** Statbank er en stærk kilde til sociale dimensioner (ca. 8/12 dækkes godt). De planetære grænser er svagest dækket - her er kommuneniveauet generelt fraværende, og platformen bør supplere med DK2020-data, Klimakompasset og Miljøstyrelsens databaser.
