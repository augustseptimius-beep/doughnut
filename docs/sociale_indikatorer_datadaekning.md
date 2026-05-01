# Sociale indikatorer - datadækning på kommuneniveau

Baseret på Københavns Doughnut 2025. Tilgængelighed vurderet via `api.statbank.dk`, `api.uddannelsesstatistik.dk` og søgning efter øvrige kilder.

**Legende - Status**
- ✅ Kommunalt opdelt data tilgængeligt via åben API
- ⚠️ Data findes, men kun via manuel download/PDF
- ❌ Ingen tilgængelig kommunal datakilde fundet

**Legende - Platform**
- 🟢 Implementeret i Danmarks 98 Doughnuts

---

## 1. Indflydelse

| # | Indikator | Status | Kilde | Platform |
|---|-----------|--------|-------|----------|
| 1 | Gennemsnitlig valgdeltagelse ved kommunalvalg | ✅ | DST: `KVBPCT` | 🟢 |
| 2 | Valgdeltagelse fordelt på herkomst | ❌ | Kun i forskningspublikationer | |
| 3 | Valgdeltagelse fordelt på alder | ❌ | Kun i forskningspublikationer | |
| 4 | Valgdeltagelse fordelt på uddannelsesniveau | ❌ | Kun i forskningspublikationer | |
| 5 | Valgdeltagelse ved folketingsvalg | ✅ | DST: `FVPANDEL` | |
| 6 | Antal medlemmer af borgerpanel | ❌ | Kommunalt system | |

> *Rettelse: Kilde for #1 er `KVBPCT` (kommunalvalg stemmetæller), ikke `KVRES`.*

---

## 2. Arbejde og indkomst

| # | Indikator | Status | Kilde | Platform |
|---|-----------|--------|-------|----------|
| 7 | Beskæftigelsesfrekvensen | ✅ | DST: `RAS200` | 🟢 |
| 8 | Kommunens placering på Beskæftigelsesministeriets benchmarkrangliste | ❌ | jobindsats.dk (ikke API) | |
| 9 | Andelen af borgere i relativ fattigdom | ✅ | DST: `IFOR12P` | 🟢 |
| 10 | Andelen af børn i relativ fattigdom | ✅ | DST: `IFOR12P` | |

---

## 3. Uddannelse

| # | Indikator | Status | Kilde | Platform |
|---|-----------|--------|-------|----------|
| 11 | Karaktergennemsnit ved folkeskolens afgangseksamen | ✅ | UVM: `GS/KARA/KARAGNS` | 🟢 |
| 12 | Karaktergennemsnit ift. socioøkonomisk reference | ✅ | UVM: `GS/SOCR/SOCREFEX` | |
| 13 | Andelen af elever med højt fravær | ✅ | UVM: `GS/ELEVFRAV/FRAVAAR` | 🟢 |
| 14 | Andelen af elever med lav elevtrivsel | ✅ | UVM: `GS/TRIV/TRIVIND` | 🟢 |
| 15 | Antal bogudlån pr. borger | ✅ | DST: `BIB1` | 🟢 |
| 16 | Andelen af unge lærepladssøgende med fuldførte grundforløb | ✅ | UVM: `EUD/PRAK/SØG` | 🟢 |
| 17 | Antal unge uden for uddannelse og beskæftigelse (NEET) | ✅ | DST: `NEET1` | 🟢 |
| 18 | Andelen af 25-årige der har gennemført en ungdomsuddannelse | ✅ | UVM: `GS/PROFMOD/PROFMOD` | 🟢 |

> *Rettelse: Kilde for #15 er `BIB1`, ikke `IBIB1A`.*

---

## 4. Bolig

| # | Indikator | Status | Kilde | Platform |
|---|-----------|--------|-------|----------|
| 19 | Antal hjemløse pr. 1.000 borgere | ❌ | VIVE kortlægning (hvert 2. år, PDF) | |
| 20 | Andelen af almene boliger | ❌ | Landsbyggefonden (Excel-download, ikke API) | |
| 21 | Andelen af boliger med energimærke E eller dårligere | ❌ | SparEnergi/Energistyrelsen (ikke kommunalt API) | |
| 22 | Ventetid i den boligsociale anvisning | ❌ | KMD Structura (kommunalt fagsystem) | |
| 23 | Andelen af stærkt støjbelastede boliger over 68 dB | ❌ | Miljøstyrelsen (5-årig kortlægning, WFS) | |

---

## 5. Sundhed

| # | Indikator | Status | Kilde | Platform |
|---|-----------|--------|-------|----------|
| 24 | Middellevetid | ✅ | DST: `HISBK` | 🟢 |
| 25 | Andelen med lav score på mental helbredsskala | ❌ | Regional sundhedsprofil (kun regionsniveau) | |
| 26 | Andelen med lav score på fysisk helbredsskala | ❌ | Regional sundhedsprofil (kun regionsniveau) | |
| 27 | Andelen der ryger dagligt | ❌ | Regional sundhedsprofil (kun regionsniveau) | |
| 28 | Andelen der rusdrikker ugentligt | ❌ | Regional sundhedsprofil (kun regionsniveau) | |
| 29 | Andelen med lav fysisk aktivitet i fritiden | ❌ | Regional sundhedsprofil (kun regionsniveau) | |
| 30 | Antal for tidlige dødsfald som følge af luftforurening | ❌ | DCE/Aarhus Universitet (ikke kommunalt API) | |
| 31 | Andelen med tegn på ensomhed | ❌ | Regional sundhedsprofil (kun regionsniveau) | |

---

## 6. Netværk

| # | Indikator | Status | Kilde | Platform |
|---|-----------|--------|-------|----------|
| 32 | Andelen der er medlem af en idrætsforening | ✅ | DST: `IDRAKT02` | 🟢 |
| 33 | Antal borgere pr. idrætsfacilitet | ✅ | DST: `IDRFAC01` | 🟢 |
| 34 | Andelen tilmeldt digital post | ❌ | Digitaliseringsstyrelsen (ikke kommunalt API) | |
| 35 | Andelen der oplever det nemt at komme rundt i byen | ❌ | Kommunalt borgerpanel | |
| 36 | Andelen af cyklister der føler sig trygge i trafikken | ❌ | Kommunalt borgerpanel | |
| 37 | Andelen tilfredse med mulighederne for cykelparkering | ❌ | Kommunalt borgerpanel | |
| 38 | Antal medlemskaber i seniorklubber med kommunalt tilskud | ❌ | Kommunalt system | |
| 39 | Antal dræbte og alvorligt tilskadekomne i trafikken | ✅ | DST: `UHELDK1` | 🟢 |

> *Rettelser: #32 kilde er `IDRAKT02` (idrætsaktivitet), ikke `IDRFOR01`. #33 er ✅ via `IDRFAC01`. #39 er ✅ via `UHELDK1`, ikke kun PDF-rapport.*

---

## 7. Energi

| # | Indikator | Status | Kilde | Platform |
|---|-----------|--------|-------|----------|
| 40 | Andelen af vedvarende energi i energiforsyningen | ❌ | Energidataservice (mulig via separat API - ikke verificeret) | |

---

## 8. Vand

| # | Indikator | Status | Kilde | Platform |
|---|-----------|--------|-------|----------|
| 41 | Antal boliger uden eget WC | ✅ | DST: `BOL102` | 🟢 |
| 42 | Antal boliger uden eget bad | ✅ | DST: `BOL102` | 🟢 |
| 43 | Andelen af elever der vurderer at have rene toiletforhold | ✅ | UVM: `GS/TRIV/TRIVSP` | |

---

## 9. Mad

| # | Indikator | Status | Kilde | Platform |
|---|-----------|--------|-------|----------|
| 44 | Andelen af elever (0., 5. og 8. klasse) med svær overvægt | ❌ | Sundhedsplejen/kommunalt system | |
| 45 | Andelen af voksne med svær overvægt | ❌ | Regional sundhedsprofil (kun regionsniveau) | |
| 46 | Andelen af voksne med undervægt | ❌ | Regional sundhedsprofil (kun regionsniveau) | |
| 47 | Andelen af voksne med usundt kostmønster | ❌ | Regional sundhedsprofil (kun regionsniveau) | |

---

## 10. Fred og retfærdighed

| # | Indikator | Status | Kilde | Platform |
|---|-----------|--------|-------|----------|
| 48 | Andelen af børn og unge der underrettes om bekymrende forhold | ✅ | DST: `UND2` | 🟢 |
| 49 | Antal anmeldelser af borgervendt kriminalitet pr. 1.000 borgere | ✅ | DST: `STRAF11` | 🟢 |
| 50 | Andelen der føler sig trygge i deres nabolag | ❌ | Tryghedsundersøgelse (Justitsministeriet/TrygFonden) | |
| 51 | Andelen trygge i aften- og nattetimerne (køn) | ❌ | Tryghedsundersøgelse (Justitsministeriet/TrygFonden) | |

---

## 11. Lighed

| # | Indikator | Status | Kilde | Platform |
|---|-----------|--------|-------|----------|
| 52 | Beskæftigelsesfrekvens fordelt på herkomst | ✅ | DST: `RAS200` | |
| 53 | Gini-koefficient | ✅ | DST: `IFOR41` | 🟢 |
| 54 | Forskel i restlevetid fordelt på uddannelsesniveau | ❌ | DST: `LIGEHI4` (kun nationalt niveau) | |
| 55 | Forskel i gennemsnitlig disponibel indkomst, mænd vs. kvinder | ✅ | DST: `INDKP101` | 🟢 |

---

## 12. Ligestilling

| # | Indikator | Status | Kilde | Platform |
|---|-----------|--------|-------|----------|
| 56 | Forskel i mænd og kvinders brug af barselsdagpengedage | ✅ | DST: `LIGEFI1` | |
| 57 | Kønsbalance blandt ledere på arbejdspladser i kommunen | ✅ | DST: `RAS301` | 🟢 |
| 58 | Karakterforskel mellem drenge og piger ved afgangseksamen | ✅ | UVM: `GS/KARA/KARAGNS` (Køn-dimension) | |
| 59 | Karakterforskel mellem elever med vestlig og ikke-vestlig baggrund | ✅ | UVM: `GS/KARA/KARAGNS` (Herkomst-dimension) | |
| 60 | Andelen af mænd og kvinder med lav mental helbredsskala | ❌ | Regional sundhedsprofil (kun regionsniveau) | |
| 61 | Andelen af unge med lav trivsel i skolen, opdelt på køn | ❌ | Ungeprofilen (ikke kommunalt API) | |
| 62 | Andelen der oplever forskelsbehandling, opdelt på køn | ❌ | Ungeprofilen (ikke kommunalt API) | |
| 63 | Forskel i restlevetid mellem køn | ✅ | DST: `HISBK` | |

---

## Opsummering (CPH-liste)

| Status | Antal | Andel |
|--------|-------|-------|
| ✅ API-adgang | 29 | 46 % |
| ⚠️ Manuel kilde | 0 | 0 % |
| ❌ Ingen kommunal kilde | 34 | 54 % |
| **Total** | **63** | **100 %** |

> *Opdateret fra original: #33 (idrætsfaciliteter) og #39 (trafikuheld) er ✅ via DST API, ikke ❌/⚠️. Samlet API-dækning stiger fra 27 til 29.*

---

## Indikatorer i platformen - ikke i CPH-listen

Disse indikatorer er implementeret i Danmarks 98 Doughnuts, men er ikke en del af Københavns Doughnut 2025-listen ovenfor.

| Indikator (id) | Kilde | Dimension |
|----------------|-------|-----------|
| Kompetencegivende uddannelse 30-34 år (`education`) | DST: `HFUDD10` | uddannelse |
| Unge 25-29 med kun grundskole (`low_education`) | DST: `HFUDD11` | uddannelse |
| Børnefattigdom 0-17 år (`child_poverty`) | DST: `LABY07` | velfaerd |
| Andel med lav indkomst (`low_income`) | DST: `LABY07` | velfaerd |
| Udsatte børn og unge (`vulnerable_children`) | DST: `BU43` | velfaerd |
| Tomme boliger (`vacant_housing`) | DST: `BOL101` | bolig |
| Boligareal pr. person (`housing_area`) | DST: `BOL106` | bolig |
| Sygehusbenyttelse (`hospital_use`) | DST: `SBR01` | sundhed |
| Afstand til egen læge (`gp_distance`) | DST: `SUNDAF01` | sundhed |
| Klassekvotient (`class_size`) | DST: `KVOTIEN` | lokalsamfund |
| Børn pr. voksen i daginstitution (`daycare_ratio`) | DST: `BOERN8` | lokalsamfund |
| Uddannede pædagoger (`educated_staff`) | DST: `BOERN1` | lokalsamfund |
| Kommunale idrætsudgifter (`sports_spending`) | DST: `IDRFIN02` | lokalsamfund |
| Civilt engagement/frivilligudgifter (`civil_society`) | DST: `REGK31` | lokalsamfund |
| Musikskoleelever (`music_school`) | DST: `SKOLM02B` | kultur_fritid |
| Kommunale kulturudgifter (`kultur_spending`) | DST: `REGK31` | kultur_fritid |
| Pendlingsafstand (`commute_distance`) | DST: `AFSTB4` | mobilitet |
| Brug af offentlig transport (`public_transport`) | DST: `LABY49` | mobilitet |

### Største strukturelle mangel

Den regionale sundhedsprofil (rygning, alkohol, mental sundhed, ensomhed, fysisk aktivitet, overvægt voksne) udgives kun på regionsniveau - ikke kommunalt. Det er 7-8 centrale sundhedsindikatorer der ikke kan hentes via nogen åben kilde på kommuneniveau.
