# Kommunegruppe-baseline for sociale indikatorer

**Dato:** 2026-06-17
**Status:** Til godkendelse

## Formål

I dag sammenlignes alle sociale indikatorer med landsgennemsnittet (100 = gennemsnit
af alle 98 kommuner). Det betyder at Thisteds "grænse" trækkes skævt af kommuner som
København, Aarhus og Aalborg, der er strukturelt meget forskellige fra en landkommune.

Vi tilføjer en ny baseline: **gennemsnittet af kommuner i samme kommunegruppe**
(KOMMUNEGRUPPER_V1_2018). Thisted (kode 787) er en Landkommune (G5, 31 kommuner) og
sammenlignes dermed kun med andre landkommuner.

## Omfang

**Kun sociale indikatorer.** De økologiske dimensioner forbliver uændrede med deres
absolutte planetære grænser (WHO, EU, Paris). Begrundelse: det økologiske loft skal
være absolut - planeten har ét budget, ikke ét pr. kommunegruppe. At give en landkommune
grønt lys på kvælstof "fordi det er normalt for en landkommune" ville skjule netop den
overskridelse modellen skal afsløre.

## Tilgang

Vi genbruger nøjagtig samme teknik som den eksisterende "Top 10%"-baseline: vi tager de
allerede beregnede ratios og omskalerer dem mod en ny reference. Ingen ændringer i
fetch-scripts, data-pipeline eller master-CSV.

For hver social indikator og hver kommunegruppe:
1. Beregn gruppens gennemsnitlige ratio (kun kommuner i gruppen, med data).
2. For hver kommune i gruppen: `gruppe_ratio = ratio / gruppe_gennemsnit * 100`.

Resultat: 100 = den gennemsnitlige kommune i din gruppe. Landsgennemsnittet falder ud
af regnestykket matematisk, så definitionen bliver "det uvægtede gennemsnit af kommunerne
i din gruppe".

Dette er den samme tekniske og metodiske tilgang som Top 10% allerede bruger (inkl. den
lille forenkling at inverse indikatorer omskaleres på deres allerede-vendte ratio).

## Datakilde

Den officielle DST-mapping (kommune_kode → gruppe 1-5) findes allerede i
`scripts/fetch_social_new_data.py` (KOMMUNEGRUPPE-dict). Vi porterer den til en TypeScript-
konstant i `webapp/lib/shared.ts`, så webappen kan beregne gruppe-baseline ved build-time.

Grupper: G1 Hovedstad (24), G2 Storby (3), G3 Provinsby (16), G4 Opland (24), G5 Land (31).

## Berøringspunkter (5 filer)

1. **`webapp/lib/shared.ts`**
   - Tilføj `KOMMUNEGRUPPE` (kode→nr) og `KOMMUNEGRUPPE_NAVNE` (nr→navn) + helper `kommunegruppeNavn(kode)`.
   - Tilføj `group_ratios` til `KommuneData`-interfacet.
   - Tilføj `computeGroupRatios(allData)` (spejler `computeTop10Ratios`).
2. **`webapp/lib/data.ts`**
   - Initialiser `group_ratios: {}` på hver kommune.
   - Kald `computeGroupRatios(data)` i `loadData()` efter `computeTop10Ratios`.
3. **`webapp/lib/baseline-context.tsx`**
   - Udvid `BaselineMode` til `"avg" | "top10" | "kommunegruppe"`.
   - Sæt default-mode (se Produktbeslutning).
4. **`webapp/components/BaselineToggle.tsx`**
   - Tredje knap: "Kommunegruppe" (mobil-kort: "Gruppe"). Juster border/short-labels.
5. **`webapp/app/kommune/[navn]/client.tsx`**
   - `activeRatios`: vælg `group_ratios` når mode === "kommunegruppe".
   - `baselineLabel`: "gennemsnittet for <gruppenavn>" (fx "Landkommuner").

## Produktbeslutning (skal bekræftes)

**Default-baseline = Kommunegruppe.** Brugeren bad om dette gennemsnit "i stedet" for
landsgennemsnittet, så det bliver standardvisningen. Landsgennemsnit og Top 10% bevares
som valg i toggle. Kan vendes med ét ord hvis du hellere vil beholde Landsgennemsnit som
default.

## Vigtig konsekvens (ærlig note)

Med en gruppe-relativ baseline graderes Thisted "på en kurve" mod de 30 andre landkommuner.
Cirka halvdelen af en gruppes kommuner vil per konstruktion ligge over 100 og halvdelen
under. Det er præcis den ønskede fairness (Thisted straffes ikke for fx svag kollektiv
transport hvis alle landkommuner har det), men baseline afspejler så ikke længere en
absolut national standard. Derfor bevarer vi Landsgennemsnit som valgmulighed.

## Test / verifikation

- Build webappen (`npm run build`) - ingen type-fejl.
- Lokal preview: tjek at toggle har tre valg, at Thisted-siden defaulter til Kommunegruppe,
  og at label viser "Landkommuner".
- Sanity-tjek: en kommune der ligger præcis på sin gruppes gennemsnit får ratio ≈ 100.
