# Repo-audit juli 2026: logik, data og metodesidens sandfærdighed

Fuld gennemgang af webapp-logik, data-pipeline, rådata og metodesiden - med fokus på om
metodesiden faktisk beskriver den logik og de kilder der ligger bag. Udført juli 2026.
Rettelserne i sektion 1-2 er implementeret i samme commit som denne rapport.

## Hvad der blev verificeret som korrekt

- Worst-of-logikken (max ratio) for øko-dimensioner og gennemsnit for Forurening matcher metodesiden.
- Inverse-konverteringen `10000/inverse` i build_master_csv.py er matematisk korrekt.
- Formlerne for nitrat (mg/L / 6 × 100, top-20 + 3,7 mg/L for resten), VP3 (national/pct × 100, cap 300,
  0% → 300), luftkvalitet (konc/WHO × 100), bolig_fossil (100 − samlet fossil%) matcher metodesiden 1:1.
- TJ-vægtet fjernvarme-landssnit er reelt 13,3% ("~13%"-påstanden er sand). 18 fælles-net-kommuner (98−80) ✓.
- Vandindvinding: 92/98 kommuner ("6 filtreret fra"-påstanden er sand).
- build_master_csv.py genskaber committed master 1:1 fra committed rådata (deterministisk pipeline).
- BII 44%/90% og 15%-arealgrænsen er konsistente mellem metodesiden og artiklen.
- TypeScript-tjek uden fejl; ingen komma-quoting-problemer i master-CSV (naiv split er OK for nuværende data).

## 1. Rettet i denne runde: metodesidens usandheder

1. **Klimatilpasning stod som "Ingen data endnu"** - kategorien scorer aktivt på vejr_skader (98/98).
   Metodeteksten beskriver nu den faktiske metode (F&P-skadesdata 2023-2025, inverteret mod landsgennemsnit).
2. **Ligestilling stod som "1 indikator"** - der er 3 (ledelse, kønsgab i levetid, indkomstlighed). Rettet inkl. datafiler.
3. **Lighed stod som "to indikatorer"** - der er 3 (Gini, lavindkomst, beskæftigelsesgab ikke-vestlig/dansk). Rettet.
4. **Klimapåvirkning påstod "territorial dækker ca. 70/98"** - climate_scores.csv dækker nu alle 98. Rettet.
5. **Pesticid-formlen var forkert beskrevet** - koden giver ratio 0 ved nul fund og et gulv på 101 ved ethvert
   fund (relativ skalering derover). Metodeteksten beskriver nu den faktiske regel.
6. **Hierarki-boksen kaldte Niveau 3 for "Frontløber-metoden (Top 10%)"** - i koden er Niveau 3
   landsgennemsnittet; Top 10% er en baseline-toggle. Rettet, og boksen dokumenterer nu også at
   default-baselinen i UI'et er Kommunegruppe.
7. **Vægtnings-afsnittet havde forkerte indikatortal** (Bolig "3"/reelt 2, Velfærd "6"/reelt 7) og beskrev
   et samlet socialt gennemsnit som UI'et ikke viser. Rettet.
8. **150-cappen på sociale ratios var udokumenteret** - alle sociale ratios klippes ved 150 i
   build_master_csv.py (rammer ~30 indikatorer, fx crime_rate for 43 kommuner). Nu dokumenteret under
   "Generelt om scoring".
9. **Om-siden overdrev** ("økologiske dimensioner scores mod absolutte planetære grænser") - nuanceret,
   så den matcher metodesidens ærlige skelnen mellem absolutte og relative grænser.
10. **Medicin-indikatoren hed "Antidepressivt forbrug"** men MEDI1 N06 omfatter også ADHD- og demensmedicin.
    Omdøbt til "Medicin mod depression, ADHD og demens (N06)".
11. Manglende indikator-begrundelser tilføjet for vejr_skader, gender_leadership, le_gender_gap,
    income_gender_gap og employment_origin_gap.

## 2. Rettet i denne runde: fejl i logik og data

1. **Herlev blev straffet på pesticider uden data.** pesticider_scores.csv havde Herlev med tom råværdi men
   ratio 101,0 (overshoot) - en rest fra før fetch-scriptet blev rettet. Rækken er nulstillet og master
   genbygget: Herlevs forurening-score korrigeret fra 94,51 til 92,34, og dækningen er nu reelt 97/98 som
   metodesiden påstår.
2. **"Gns:"-visningen i ScoreBars var forkert for alle kappede ratios.** Den regnede landsgennemsnittet
   baglæns fra kommunens egen ratio - men ratioen er klippet ved 150, så fx Dragørs kriminalitet viste
   "Gns: 58,1" hvor det reelle landsgennemsnit er ~73,7. Rammer ca. 350 celler på tværs af 30 indikatorer.
   Fix: `computeNationalAverages()` i shared.ts rekonstruerer gennemsnittet fra ukappede ratios på tværs af
   alle kommuner (median); client.tsx sender det til ScoreBars.
3. **Hardcoded "6" i client.tsx** ("X mangler data"-teksten) - der er 13 sociale kategorier. Bruger nu det
   faktiske antal.
4. Forældede kommentarer i data.ts (Vand beskrev nitrat som sub-indikator; Forurening stod som worst-of).

## 3. Rettet i denne runde: hygiejne

- `CLAUDE 2.md` (forældet duplikat) slettet.
- `webapp/.env` fjernet fra git-tracking og tilføjet til .gitignore (indeholdt kun placeholder, men den dag
  en rigtig nøgle indsættes lokalt, ville den ryge med op). NB: filen hed desuden `KLIMAREGNSKAB_API_KEY`
  mens Netlify-funktionen læser `KLIMAREGNSKABET_API_KEY`.
- `doughnut_scores.csv`-linjen fjernet fra rod-.gitignore - filen er pipelinens kommuneliste og SKAL være
  tracked; en ignore-regel for den var en fælde.
- `webapp/tsconfig.tsbuildinfo` fjernet fra tracking (stod allerede i .gitignore).
- `webapp/out/` (bygget site, ~900 filer) fjernet fra tracking og tilføjet til .gitignore. Netlify bygger
  selv fra kildekoden og bruger aldrig den committede version - den gav kun kæmpe støj-diffs i GitHub
  Desktop efter hver lokal build.
- Åbne tråde-dokumentet opdateret: punkt 1 (baselineType) og 2 (education 95%-mål) er løst.

## 4. Åbne beslutninger (IKKE rettet - kræver et valg)

1. **housing_no_wc og housing_no_bath er forældreløse.** De findes i INDICATORS og bygges ind i master
   (98/98 rækker) men er ikke med i nogen kategori - de vises og scores aldrig. Enten aktivér dem i Bolig
   (som kun har 2 indikatorer) eller fjern dem fra INDICATORS + build. OBS: aktivering ændrer Bolig-scoren
   for alle kommuner. Bemærk også at mange kommuner er kappet på dem (56 hhv. 49 ved ratio 150).
2. **Nul-reglen trækker i to retninger i øko-pipelinen.** Kommune uden markblokke → n_ratio 150 (straf);
   kommune med 0 spildevands-udledning → inverse 150 → direkte 66,7 (belønning). Bør besluttes og
   dokumenteres bevidst (metodediskussion).
3. **Netlify-funktionen klimaregnskabet.mts bruges ikke** af webappen (kun Python-scriptet kalder API'et
   direkte). Behold hvis der er planer om klient-side opslag, ellers slet.
4. **Footer siger "2024-Doughnut"** mens flere indikatorer har dataår 2025-2026. Overvej at opdatere
   DOUGHNUT_EDITION_YEAR.
5. **vand_scores.csv og land_use_scores.csv** bruges ikke af build-pipelinen (legacy). vand_scores.csv
   genereres stadig af fetch_eco_new_data.py.
6. **compare-funktionaliteten i ScoreBars** er fuldt bygget men har ingen UI-indgang - mulighed for
   kommune-sammenligning næsten gratis.
7. **Søgning:** "århus" matcher ikke "Aarhus" - lille alias-normalisering i KommuneSearch ville hjælpe.
8. **Baseline-valget nulstilles ved reload** - kunne gemmes i localStorage.
9. Fra åbne tråde-dokumentet: REshare (faktisk VE-dækning), net→kommune-mapping for fjernvarme,
   energiforbrug pr. capita.

## Konsekvens for top10-baselinen (til orientering)

Top 10%-baselinen beregnes af kappede ratios. For indikatorer hvor mange kommuner er kappet (fx
public_transport, crime_rate) er top10-gennemsnittet præcis 150, og alle kappede kommuner får præcis 100 i
top10-mode. Det er en direkte konsekvens af cappen - acceptabelt, men værd at kende.
