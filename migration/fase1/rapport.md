# Fase 1-rapport: konvertering til "git er sandheden"

**Dato:** 2026-10-21. **Spec:** `docs/lovable-migration-spec.md` afsnit 15, fase 1.
**Resultat:** Acceptkriteriet er opfyldt. Rundturen genskaber master-CSV'en række for række. Afventer kun, at August har skimmet afsnit 1-3.

Det gamle site er ikke rørt. Alt nyt ligger i `migration/`.

---

## 1. Kort fortalt (til August)

Alle tal, al metadata og alle metode-tekster er flyttet over i det nye format. De ligger i `migration/lovable/`, klar til at blive flyttet ind i Lovable-repoet i fase 2. Konverteringen er bevist at være tabsfri: ud fra de nye filer kan hele det gamle datasæt genskabes, og alle 28.209 tal, sitet viser, bliver de samme. Der er én bevidst undtagelse på ±0,01, se 3e.

Undervejs dukkede **tre faglige uoverensstemmelser** op i det nuværende site (afsnit 2) og **en række forældede metode-tekster** (afsnit 3). Ingen af dem er rettet, fordi migreringen skal være 1:1 (spec B16). De er listet her, så du kan beslutte, hvad der skal ske med dem.

---

## 2. Faglige fund, der kræver din beslutning

Alle tre findes på det live site i dag. Anbefaling: beslut efter migreringen, ikke under. Den kan alle tre rettes i registret med én linje, når det nye site kører.

**2a. `vejr_skader` (Klimatilpasning) har intet loft på 150.**
Alle andre sociale indikatorer klippes ved 150. Men `build_master_csv.py` springer klipningen over for indikatorer, der matches på kommunenavn, og det er kun `vejr_skader`. Resultat: 27 af 98 kommuner ligger over 150, højest Albertslund med 431. Da Klimatilpasning kun har denne ene indikator, bliver kategoriscoren for de kommuner tilsvarende høj. Det ligner en fejl i den gamle kode. Thisted rammes ikke (53,91).
*Spørgsmål:* Skal loftet på 150 også gælde her?

**2b. Råværdi 0 giver topscore for `boerneovervaeght`.**
Faxe, Ærø, Sønderborg og Læsø har 0% overvægt registreret og får ratio 150 (højeste mulige). Metode-siden lover det modsatte: "Kommuner med en værdi på 0 (typisk manglende data ...) sættes til ratio 0, ikke perfekt score". 0% overvægt blandt 6-7-årige er næppe virkeligt, så det er formentlig manglende data, der vises som topscore.
*Spørgsmål:* Skal 0 her behandles som manglende data?

**2c. Pesticider vises som "absolut, grænse 0%", men regnes relativt.**
UI'et mærker indikatoren "mod mål" med grænse 0% (drikkevandsnormen). Formlen er dog `kommunens andel / landsgennemsnittet (7,55%) × 100`, med et gulv på 101 for enhver kommune med mindst én overskridelse. Mærkningen og beregningen siger altså to forskellige ting.
*Spørgsmål:* Skal mærket ændres til "mod landsgennemsnit", eller skal formlen ændres?

(Allerede kendt: `housing_no_wc` og `housing_no_bath` har data, men indgår ikke i Bolig-scoren. Uændret.)

---

## 3. Forældede metode-tekster (rettes i fase 4)

Teksterne er flyttet ordret. Følgende passer ikke med data og bliver rettet, når metode-siden genbygges i fase 4. Her bliver dataår og indikatorantal udledt automatisk, så de ikke kan gå i utakt igen.

**Indikatorantal og indhold**
- *Lighed:* "Gennemsnit af to indikatorer". Har tre (`employment_origin_gap` mangler i teksten).
- *Ligestilling:* "1 indikator: Andel kvinder i lønmodtager-lederstillinger". Har tre (`le_gender_gap` og `income_gender_gap` mangler).
- *Klimatilpasning:* "Ingen data endnu". `vejr_skader` er aktiv med data for alle 98 kommuner.
- *Generelt om scoring:* "Bolig med 3" (har 2) og "Velfærd med 6" (har 7).
- *Generelt om scoring:* "ratio 150 anvendes som loft for sub-indikatorer hvor data mangler". I koden er loftet 300 for biodiversitet og overfladevand. Påstanden er ikke verificeret for de øvrige.
- *Generelt om scoring:* "værdi 0 sættes til ratio 0". Passer ikke for `boerneovervaeght` (fund 2b).
- *Hierarki for baseline-valg:* Niveau 3 beskrives som "Frontløber-metoden (Top 10% decilen)". I koden (`baselineLevel: 3`) betyder niveau 3 landsgennemsnit, og sitets standard-baseline er kommunegruppen.
- *Databehandling og kildekode:* beskriver Python-scripts, Next.js og Netlify. Skal omskrives ved go-live.
- *Begrundelser:* 14 af 50 sociale indikatorer har ingen begrundelse på metode-siden: `apprenticeship`, `child_notifications`, `employment_origin_gap`, `exam_grade`, `gender_leadership`, `high_absence`, `housing_no_bath`, `housing_no_wc`, `income_gender_gap`, `le_gender_gap`, `poverty_relative`, `vejr_skader`, `wellbeing`, `youth_education`.

**Dataår (håndskrevet -> udledt af data)**

| Dimension | Står på siden i dag | Udledt af data |
|---|---|---|
| Lighed | 2022 | 2022-2024 |
| Ligestilling | 2023 | 2023-2025 |
| Klimatilpasning | (intet) | 2023-2025 |
| Velfærd, Kultur, Foreningsliv | 2022-2024 | 2022-2023 |
| Forurening | 2019-2025 | 2023-2025 (2019 er starten på pesticid-måleperioden, ikke et dataår) |
| Næringsstoffer | 2024, 2025, 2026 (markblokke) | 2024-2025 |
| Energi | 2026, 2024, 2024 | 2026 for scoren. Kontekst-tallene (2024) er ikke med i intervallet |

De øvrige 11 dimensioner stemmer.

**3e. Teknisk: 14 forurenings-scorer flytter 0,01.**
Forurening er et gennemsnit af fire tal. For 14 kommuner ligger gennemsnittet præcis på en grænse (fx 71,675), og det gamle site rundede tilfældigt op eller ned, afhængigt af rækkefølgen tallene blev lagt sammen i. Det nye system runder altid halvt op. Forskellen er 0,01 og kan ikke ses i farverne. Kommunerne: 161, 187, 223, 316, 350, 400, 540, 630, 707, 730, 741, 773, 779, 849.

---

## 4. Hvad der er produceret

`migration/lovable/` er frøet til det nye repo (spec afsnit 2):

| Del | Indhold |
|---|---|
| `data/snapshots/` | 76 CSV-filer (én pr. indikator), 7.349 rækker, plus `_manifest.json` med dataår, kilde, tidspunkt, referenceværdi og hash |
| `registry/` | `indicators.ts` (76: 50 sociale, 17 økologiske, 9 kontekst), `dimensions.ts` (13 + 7), `kommuner.ts` (98), `references.ts` (6), `settings.ts`. Håndskrevet: `types.ts`, `transforms.ts`, `legacy.ts` |
| `content/metode/` | 20 dimensionstekster, 36 indikator-begrundelser, 5 generelle afsnit, `README.md` |

Opdatering: 66 indikatorer får en edge function (15 funktioner, præcis listen i spec 9.1), 10 er frosne.

Scripts: `migration/fase1/convert.mjs` (konvertering), `verify.mjs` (verifikation) og `lib.mjs`. Kørsel: se `migration/README.md`.

---

## 5. Verifikation

`verify.mjs` læser kun det nye output og sammenligner det med det gamle site:

| Kontrol | Resultat |
|---|---|
| **A** Rundtur: snapshots + register + manifest genskaber master-CSV'en (uden `_dim_`), alle 10 kolonner | 7.349/7.349 rækker. Eneste afvigelse er 6 godkendte enhedskonflikter (afsnit 6) |
| **B** Registret genskaber `INDICATORS`, `SOCIAL_CATEGORIES`, `ECOLOGICAL_DIMENSIONS`, `KOMMUNEGRUPPE(_NAVNE)`, `ECO_RAW_KEY_MAP` og årstal | 7/7 identiske med fase 0-baselinen |
| **C** Reference-loader efter spec afsnit 7 (dimensionsscorer beregnet fra sub-ratios, ikke læst) mod `parity_baseline.json` | 28.209 værdier bit-identiske, undtagen de 14 gennemsnit i 3e. Kategoriscorer i alle tre baselines er bit-identiske |
| **D** Markdown giver de gamle tekster ordret tilbage. De 5 håndkonverterede afsnit har samme ord i samme rækkefølge som JSX'en | 20 + 36 ordret, 5/5 ordfølge |
| **E** Integritet: filer, id'er, manifest, edge functions, opskrifter, referencer | 0 fejl |
| **T** Registrets formel + manifestets reference genskaber den gemte ratio fra råværdien (informativt) | 66/67 indikatorer fuldt. `naer_phosphorus`: 92/93 rækker, den sidste lige på grænsen pga. dobbelt afrunding i den gamle pipeline |

**Testet negativt.** Seks plantede fejl blev hver fanget af den rette kontrol:

| Plantet fejl | Fanget af |
|---|---|
| Ét tal | A + C (inkl. følgefejl i gruppe-baselines) |
| En enhed | A + B |
| En indikator ind i en kategori | B |
| Et ord i en dimensionstekst | D |
| En sætning fjernet i et håndkonverteret afsnit | D |
| Et dataår | A + B |

**Andre kontroller:**
- Outputtet er gendannet byte-identisk efter de negative tests.
- To kørsler (efter sletning og fra en anden mappe) giver 147 byte-identiske filer.
- De håndskrevne filer røres ikke af konverteringen.

**Kendte grænser for verifikationen:**
- C beregner kategoriscorer med det gamle sites egne konstanter. At registret giver de samme konstanter, er bevist af B. I fase 3 bruger loaderen registrets konstanter direkte, og paritetstesten dækker det dér.
- For de 5 håndkonverterede afsnit er ordene verificeret, men ikke formateringen: boksen er blevet til et blokcitat, og niveauerne til en punktliste. Det ses visuelt i fase 4.

---

## 6. Valg truffet under konverteringen

Til gennemsyn. Ingen af dem ændrer, hvad sitet viser.

1. **Enhedskonflikter:** registret bruger den enhed, UI'et viser i dag (spec 3). Seks konflikter med build-scriptets enheder:
   - `child_notifications`
   - `bolig_fossil`
   - `le_gender_gap`
   - `income_gender_gap`
   - `employment_origin_gap`
   - `pesticider` (spec'en kendte de første fem; `pesticider` er ny)
2. **Kontekst-indikatorer** havde ingen navne i registret, kun hårdkodede labels i `ScoreBars.tsx`. De 9 har fået navne, fx "Fjernvarmens brændselsmix: fossil".
3. **Referenceværdier:** 57 indikatorer regnes relativt til et nationalt tal eller en poolet reference. Tallet er udledt af data (median, 6 betydende cifre) og står i manifestet, fx middellevetid 81,60 år og pesticider 7,55%. Det gør import med kun råværdier mulig for alle 67 scorede indikatorer, ikke kun de 10 frosne.
4. **Formler i registret** (spec afsnit 5 opdateret tilsvarende):
   - Ny transform `complement_100` (R24) til `bolig_fossil` (100 minus råværdi).
   - `inverse_10000` (R3) er nu en importregel for gamle CSV-filer (`legacy.ratioColIsInverse`), ikke en transform, fordi snapshots gemmer den færdige ratio.
   - Invers med råværdi 0 rammer loftet (gengiver 2b).
   - `vejr_skader` har intet loft (gengiver 2a).
5. **Afrunding af gennemsnit** (R7): eksakt sum, halvt op. Se 3e.
6. **`fetched_at`** i manifestet er datoen for seneste commit af den gamle kildefil. Det er en tilnærmelse: det præcise hentetidspunkt kendes ikke for frosne data.
7. **Antal frosne:** 10 indikatorer. Spec 9.2 har 8 rækker, fordi to rækker dækker to indikatorer hver.
8. **Felt-navn:** `dstTable` i spec 4.3 hedder `sourceTable` i registret, fordi feltet også indeholder ikke-DST-tabeller som "GS/KARA/KARAGNS" og "F&P skadesstatistik". Spec'en er rettet.

---

## 7. Oprindelsen af `consumption_scores.csv` (genanvendelse)

Spec'en krævede, at oprindelsen blev dokumenteret. Det kunne kun delvist lade sig gøre:

- **Intet script producerer filen.** Den blev tilføjet manuelt af August i commit `f9eba2c` (2026-05-01, "Opdateringer").
- **Indhold:** 98 kommuner og 36 forskellige værdier, alle hele procenter (fx 60, 66, 67). Landsgennemsnittet er 58% og året 2023.
- **Kildeangivelsen er tvivlsom.** I `build_master_csv.py` står kilden som "DST LABY25". Men `docs/statbank_doughnut_mapping.md` beskriver LABY25 som nøgletal for husholdningsaffald (kg/indbygger), ikke genanvendelsesprocent.

*Spørgsmål til August:* Ved du, hvor genanvendelsestallene kommer fra? Hele procenter tyder på en manuel kilde, fx Miljøstyrelsens affaldsstatistik. Indtil det er afklaret, er indikatoren frossen, og kildeangivelsen bør rettes på metode-siden.

---

## 8. Næste skridt

- **August:** skim afsnit 1-3. Fund 2a-2c og afsnit 7 kan besvares nu eller efter migreringen.
- **Fase 2** (Lovable-projekt, spike V1-V9, port af app) kræver svar fra Lovable og IT på spørgsmålene i spec 13.1.
- **Datafrysning gælder fortsat:** ændres `data/master_indicators.csv` på det gamle site, skal fase 0 og fase 1 køres igen (to kommandoer, se `migration/README.md`).
