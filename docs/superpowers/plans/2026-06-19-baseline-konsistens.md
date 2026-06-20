# Baseline-konsistens Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gør absolut-vs-relativ baseline konsistent og synlig på tværs af alle doughnut-dimensioner, og gør `education`'s 95 %-mål ægte absolut.

**Architecture:** Et struktureret `baselineType` ("absolut"/"relativ") udledes per indikator (socialt: fra `absoluteScore`; økologisk: nyt felt på sub-indikatorer). Dimensioner/kategorier får en afledt type (ens → den type, ellers "blandet"), som ScoreBars viser som et lille mærke. `education` scores mod 95 % via et nyt `abs_target`-felt i build-pipelinen.

**Tech Stack:** Next.js 16 (static export), TypeScript, Tailwind 4, Python 3 (build_master_csv.py). INGEN testframework - verifikation sker via `npm run build` (fra `webapp/`), data-spot-checks i master-CSV, og browser-DOM-tjek via preview-serveren.

**Projektregler der gælder for ALLE tasks:**
- Kør ALDRIG terminal-git. Hver task slutter med verifikation; ændringer efterlades ucommitteret til Augusts GitHub Desktop.
- Kør Python-scripts fra projektets rodmappe. Kør `npm run build` fra `webapp/`.
- Kør IKKE `npm run build` mens preview/dev-serveren kører (delt `.next` destabiliserer dev-serveren). Stop dev først, eller ryd `webapp/.next` og genstart bagefter.
- Pålidelig måde at se et udfoldet panel i browseren: sæt midlertidigt `useState(expanded)` default til dimensionen i ScoreBars, reload, DOM-tjek, rul tilbage.

---

## File Structure

- `scripts/build_master_csv.py` - `abs_target`-felt på `education` + håndtering i social-loop.
- `webapp/lib/shared.ts` - `education.absoluteScore`; `baselineType` på øko-sub-indikatorer + interface; hjælpefunktioner til at udlede type.
- `data/master_indicators.csv` - regenereres (ikke redigeret manuelt).
- `webapp/components/ScoreBars.tsx` - dimensions-mærke (social + øko) + markør på øko-sub-indikatorer.
- `webapp/components/DoughnutRing.tsx` - legende-linje.
- `webapp/app/metode/page.tsx` - note om reglen + education-metode/rationale.
- `CLAUDE.md` - note om `baselineType`-konventionen.

---

## Task 1: Education scores mod 95 % (absolut)

**Files:**
- Modify: `scripts/build_master_csv.py` (education-entry + social-loop)
- Modify: `webapp/lib/shared.ts` (education-indikator)
- Regenerate: `data/master_indicators.csv`

- [ ] **Step 1: Tilføj `abs_target` til education-entry i build_master**

I `scripts/build_master_csv.py`, find education-linjen i `SOCIAL_INDICATORS` og tilføj `"abs_target": 95`:

```python
    {"id": "education", "csv": "doughnut_scores.csv", "ratio_col": "education_ratio", "raw_col": "education_raw", "unit": "%", "data_year": "2023", "source": "DST HFUDD10", "category": "social", "dimension": "uddannelse", "abs_target": 95},
```

- [ ] **Step 2: Håndtér `abs_target` i social-loopet**

I `scripts/build_master_csv.py`, find blokken i social-loopet der starter med `ratio = parse_float(r.get(ind["ratio_col"]))` (det sted hvor raw og ratio beregnes pr. kommune) og erstat den med:

```python
            raw = parse_float(r.get(ind["raw_col"])) if ind["raw_col"] else None
            abs_target = ind.get("abs_target")
            if abs_target:
                # Absolut score mod fast mål: ratio = raw / mål * 100 (100 = mål nået).
                # Klippet ved 150 som øvrige sociale ratios.
                ratio = round(min((raw / abs_target) * 100, 150.0), 2) if raw is not None else None
            else:
                ratio = parse_float(r.get(ind["ratio_col"]))
                # Cap alle sociale ratios ved 150 for at undgå ekstreme inverse-værdier
                if ratio is not None and ratio > 150:
                    ratio = 150.0
            if ratio is None and raw is None:
                continue
```

(Dette erstatter den eksisterende `ratio = ...` + cap + `raw = ...` rækkefølge. Sørg for at den efterfølgende `output_rows.append({...})` er uændret.)

- [ ] **Step 3: Sæt `absoluteScore: true` på education i shared.ts**

I `webapp/lib/shared.ts`, find education-indikatoren og tilføj `absoluteScore: true` (feltet `absoluteTarget: "95% (nationalt uddannelsesmål)"` findes allerede):

```typescript
  {
    id: "education",
    name: "Kompetencegivende uddannelse (30-34 år)",
    table: "HFUDD10",
    source: "https://www.statistikbanken.dk/HFUDD10",
    category: "social",
    inverse: false,
    dataYear: "2023",
    baselineLevel: 2,
    absoluteTarget: "95% (nationalt uddannelsesmål)",
    absoluteScore: true,
    rawUnit: "%",
  },
```

- [ ] **Step 4: Regenerér master-CSV**

Run (fra rodmappen): `python3 scripts/build_master_csv.py`
Expected: "✓ Alle ratios inden for forventet interval" og "✓ Skrev ... rækker".

- [ ] **Step 5: Verificér education-ratio er absolut**

Run: `grep "education" data/master_indicators.csv | head -3`
Expected: for hver kommune skal `ratio ≈ raw/95*100`. Fx en kommune med raw 80.0 skal have ratio ≈ 84.21. Bekræft manuelt at ratio IKKE længere er ~100-centreret (avg-baseret).

- [ ] **Step 6: Checkpoint**

Ingen terminal-git. Ændringer i `build_master_csv.py`, `shared.ts`, `master_indicators.csv` er klar til GitHub Desktop. Noter at education nu falder mod amber/rød - det er forventet.

---

## Task 2: baselineType-datamodel

**Files:**
- Modify: `webapp/lib/shared.ts` (interface + øko-sub-indikator-værdier + hjælpefunktioner)

- [ ] **Step 1: Udvid EcologicalDimension.subIndicators-interface**

I `webapp/lib/shared.ts`, i `EcologicalDimension`-interfacet, tilføj `baselineType` til `subIndicators`-objektet:

```typescript
  subIndicators?: {
    rawKey: string;
    ratioKey?: string;
    label: string;
    unit: string;
    boundary?: string;
    lowerIsBetter?: boolean;
    baselineType?: "absolut" | "relativ"; // mod fast mål vs mod landsgennemsnit
  }[];
```

- [ ] **Step 2: Sæt baselineType på hver øko-sub-indikator**

I `webapp/lib/shared.ts`, tilføj `baselineType` til hver sub-indikator efter denne klassifikation:

- `klimapaavirkning`: begge sub → `"absolut"`
- `forurening`: `eco_pesticid_raw` → `"absolut"`, `eco_nitrat_raw` → `"absolut"`, `eco_cirkularitet_raw` (genanvendelse) → `"absolut"`, `eco_affald_raw` → `"relativ"`
- `luftkvalitet`: begge sub → `"absolut"`
- `naeringsstoffer`: alle fire sub → `"relativ"`
- `vand`: `eco_vandindvinding_raw` → `"relativ"`
- `arealanvendelse`: begge sub → `"relativ"`
- `biodiversitet`: begge sub → `"absolut"`

Eksempel (luftkvalitet):

```typescript
      { rawKey: "luftkvalitet_no2",  ratioKey: "luftkvalitet_no2_ratio",  label: "NO₂ (kvælstofdioxid)",  unit: "µg/m³", boundary: "WHO 2021: 10 µg/m³", lowerIsBetter: true, baselineType: "absolut" },
      { rawKey: "luftkvalitet_pm25", ratioKey: "luftkvalitet_pm25_ratio", label: "PM2.5 (fine partikler)", unit: "µg/m³", boundary: "WHO 2021: 5 µg/m³",  lowerIsBetter: true, baselineType: "absolut" },
```

Eksempel (forurening - bemærk affald er relativ):

```typescript
      { rawKey: "eco_pesticid_raw",     ratioKey: "pesticider_self",       label: "Pesticider i grundvand",      unit: "% boringer > 0.1 µg/l", boundary: "Grænse: 0% (drikkevandsnorm)", lowerIsBetter: true,  baselineType: "absolut" },
      { rawKey: "eco_nitrat_raw",       ratioKey: "nitrat_self",           label: "Nitrat i drikkevand",         unit: "mg/L",                  boundary: "Grænse: 6 mg/L (ekspertgruppe 2025)", lowerIsBetter: true, baselineType: "absolut" },
      { rawKey: "eco_cirkularitet_raw", ratioKey: "eco_cirkularitet_ratio", label: "Genanvendelse (husholdning)", unit: "%",                     boundary: "Mål: 65% (EU Affaldsdirektiv 2035)", lowerIsBetter: false, baselineType: "absolut" },
      { rawKey: "eco_affald_raw",       ratioKey: "eco_affald_ratio",      label: "Affald pr. person",           unit: "kg/person",             boundary: "Lavere end landsgennemsnittet er bedre", lowerIsBetter: true, baselineType: "relativ" },
```

Anvend samme mønster på de resterende dimensioner (klimapaavirkning, naeringsstoffer, vand, arealanvendelse, biodiversitet) med værdierne fra listen ovenfor.

- [ ] **Step 3: Tilføj hjælpefunktioner til typeudledning**

I `webapp/lib/shared.ts`, tilføj efter `computeCategoryScores`-funktionen:

```typescript
// --- BASELINE-TYPE: absolut (mod fast mål) vs relativ (mod landsgennemsnit) ---
export type BaselineType = "absolut" | "relativ";
export type DimBaselineType = BaselineType | "blandet";

// En social indikators type følger dens scoringsadfærd.
export function indicatorBaselineType(ind: Indicator): BaselineType {
  return ind.absoluteScore ? "absolut" : "relativ";
}

function combineBaselineTypes(types: BaselineType[]): DimBaselineType {
  if (types.length === 0) return "relativ";
  if (types.every((t) => t === "absolut")) return "absolut";
  if (types.every((t) => t === "relativ")) return "relativ";
  return "blandet";
}

export function categoryBaselineType(cat: SocialCategory): DimBaselineType {
  const types = cat.indicatorIds
    .map((id) => INDICATORS.find((i) => i.id === id))
    .filter((i): i is Indicator => !!i)
    .map(indicatorBaselineType);
  return combineBaselineTypes(types);
}

export function dimensionBaselineType(dim: EcologicalDimension): DimBaselineType {
  const types = (dim.subIndicators ?? [])
    .map((s) => s.baselineType)
    .filter((t): t is BaselineType => !!t);
  return combineBaselineTypes(types);
}
```

- [ ] **Step 4: Verificér typer kompilerer**

Run (fra `webapp/`, med dev-server stoppet): `npm run build`
Expected: "✓ Compiled successfully", "Finished TypeScript", 104 sider. Ingen effekt i UI endnu.

- [ ] **Step 5: Checkpoint** - ændringer klar til GitHub Desktop.

---

## Task 3: ScoreBars - dimensions-mærke + øko-sub-markør

**Files:**
- Modify: `webapp/components/ScoreBars.tsx`

- [ ] **Step 1: Importér hjælpefunktioner + tilføj tag-helper**

I `webapp/components/ScoreBars.tsx`, udvid importen fra `@/lib/shared` med `categoryBaselineType`, `dimensionBaselineType`, og typen `DimBaselineType`. Tilføj derefter en lille UI-helper øverst i filen (efter importerne):

```typescript
// Mærke vises kun for absolut og blandet; relativ er normen (intet mærke, forklaret i legenden).
function baselineTag(t: DimBaselineType): string | null {
  if (t === "absolut") return "mod mål";
  if (t === "blandet") return "blandet";
  return null;
}
```

- [ ] **Step 2: Vis mærke på sociale kategori-bjælker**

I den sociale kategori-`map` i ScoreBars, beregn typen i toppen af callbacken (sammen med de øvrige `const`-beregninger som `isExpanded`):

```typescript
            const blTag = baselineTag(categoryBaselineType(cat));
```

Tilføj derefter mærket lige efter `<span ...>{cat.categoryName}</span>` i kategori-headeren:

```tsx
                        {!vurderingsMode && blTag && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 whitespace-nowrap">
                            {blTag}
                          </span>
                        )}
```

- [ ] **Step 3: Vis mærke på økologiske dimensions-bjælker**

I den økologiske dimensions-`map`, beregn typen i toppen af callbacken:

```typescript
            const blTag = baselineTag(dimensionBaselineType(dim));
```

Tilføj mærket lige efter `<span ...>{dim.name}</span>` i dimensions-headeren:

```tsx
                        {!vurderingsMode && blTag && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 whitespace-nowrap">
                            {blTag}
                          </span>
                        )}
```

- [ ] **Step 4: Tilføj markør på øko-sub-indikator-rækker**

I den udfoldede øko-sub-indikator-visning, find rækken med `{sub.lowerIsBetter ? "Lavere er bedre" : "Højere er bedre"}` og erstat den enkelte `<span>` med en gruppe der også viser baseline-markøren:

```tsx
                          <div className="mt-1.5 flex items-center justify-between text-xs text-gray-500">
                            <div className="flex items-center gap-2">
                              <span>{sub.lowerIsBetter ? "Lavere er bedre" : "Højere er bedre"}</span>
                              {sub.baselineType && (
                                <span className="text-gray-400 text-[10px]">
                                  {sub.baselineType === "absolut" ? "mod mål" : "mod landsgns"}
                                </span>
                              )}
                            </div>
                            <a href={`/metode#${dim.id}`} className="text-blue-600 hover:underline">
                              Se metode ↗
                            </a>
                          </div>
```

- [ ] **Step 5: Verificér build**

Run (fra `webapp/`, dev stoppet): `npm run build`
Expected: kompilerer, 104 sider, TypeScript rent.

- [ ] **Step 6: Browser-verifikation**

Start preview, gå til `/kommune/Thisted` (vent til htmlLen er stor = fuldt renderet). Tjek via DOM:
- Sociale bjælker: `Energi` har mærke "mod mål"; `Uddannelse` har "blandet"; fx `Sundhed` har intet mærke.
- Øko-bjælker: `Klimapåvirkning`/`Luftkvalitet`/`Biodiversitet` har "mod mål"; `Forurening` har "blandet"; `Næringsstoffer`/`Vand`/`Arealanvendelse` har intet mærke.
- Fold en øko-dimension ud (fx via midlertidig default-expand): sub-rækker viser "mod mål"/"mod landsgns".

- [ ] **Step 7: Checkpoint** - ændringer klar til GitHub Desktop.

---

## Task 4: DoughnutRing - legende-linje

**Files:**
- Modify: `webapp/components/DoughnutRing.tsx`

- [ ] **Step 1: Tilføj forklarende linje under normal-mode-legenden**

I `webapp/components/DoughnutRing.tsx`, find normal-mode-legenden (blokken efter `/* Legende i normal-mode: kommunedata-farver */`). Wrap legende-`<div>` og en ny `<p>` i en fragment:

```tsx
        /* Legende i normal-mode: kommunedata-farver */
        <>
        <div className="flex flex-wrap justify-center gap-4 md:gap-6 mt-2 text-xs text-gray-500">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: GREEN_SOCIAL, border: `1px solid ${GREEN_DARK_BAND}` }} />
            <span className="font-medium">Sikkert rum</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-12 h-4 rounded" style={{ background: "linear-gradient(to right, #eab308, #f97316, #dc2626, #991b1b)" }} />
            <span className="font-medium">Underskud / Overskridelse</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: GRAY_NO_DATA, border: `1px solid ${GRAY_NO_DATA_STROKE}` }} />
            <span className="font-medium">Mangler data</span>
          </div>
        </div>
        <p className="text-center text-[11px] text-gray-400 mt-2 max-w-md mx-auto px-2">
          Dimensioner mærket &quot;mod mål&quot; måles mod en fast grænse (fx WHO, EU-mål, 0 % fossil); umærkede måles mod landsgennemsnittet.
        </p>
        </>
```

- [ ] **Step 2: Verificér build**

Run (fra `webapp/`): `npm run build`
Expected: kompilerer, 104 sider.

- [ ] **Step 3: Browser-verifikation** - legende-linjen vises under ringens farveforklaring på en kommuneside.

- [ ] **Step 4: Checkpoint** - klar til GitHub Desktop.

---

## Task 5: Metode-siden - regel + education

**Files:**
- Modify: `webapp/app/metode/page.tsx`

- [ ] **Step 1: Tilføj note om reglen i "Om grænserne i det økologiske loft"-boksen**

I `webapp/app/metode/page.tsx`, find den blå boks med overskriften "Om grænserne i det økologiske loft". Tilføj et nyt afsnit til sidst i boksen (efter det eksisterende link-afsnit):

```tsx
        <p className="text-sm text-gray-700 leading-relaxed mt-2">
          Hver dimension er mærket efter hvad den måles imod: <strong>mod mål</strong> (en fast absolut grænse - WHO, EU-mål, drikkevandsnorm, 0 % fossil, 95 %-uddannelsesmål) eller <strong>mod landsgennemsnit</strong> (umærket - relativ til de øvrige kommuner). Et par dimensioner er <strong>blandet</strong>. På en &quot;mod mål&quot;-dimension betyder grøn &quot;inden for grænsen&quot;; på en relativ betyder grøn &quot;bedre end de fleste kommuner&quot;.
        </p>
```

- [ ] **Step 2: Opdater uddannelse-metoden så education-scoringen er korrekt beskrevet**

I `SOCIAL_METHODS.uddannelse.scoring`, ret beskrivelsen af indikator (1) fra "(HFUDD10, direkte)" til at nævne den absolutte scoring. Find sætningen der starter "Gennemsnit af ti indikatorer: (1) Andel af 30-34-årige med kompetencegivende uddannelse (HFUDD10, direkte)." og erstat parentesen:

```
(1) Andel af 30-34-årige med kompetencegivende uddannelse (HFUDD10, scoret absolut mod det nationale 95 %-mål: ratio = andel/95 × 100).
```

- [ ] **Step 3: Bekræft education-rationale er korrekt**

`INDICATOR_RATIONALES.education` siger allerede "Absolut baseline: nationalt mål på 95%". Tilføj en kort præcisering til sidst: " Scoren beregnes nu mod dette mål (100 = 95 % nået), ikke mod landsgennemsnittet."

- [ ] **Step 4: Verificér build**

Run (fra `webapp/`): `npm run build`
Expected: kompilerer, 104 sider.

- [ ] **Step 5: Checkpoint** - klar til GitHub Desktop.

---

## Task 6: CLAUDE.md-note + endelig verifikation

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Tilføj note om baselineType-konventionen**

I `CLAUDE.md`, tilføj et nyt punkt under "Vigtigste pitfalls og ting at huske på" (efter det sidste eksisterende punkt):

```markdown
12. **baselineType (absolut vs relativ)** - hver dimension klassificeres: absolut (scoret mod fast mål - WHO, EU, 0 % fossil, 95 % uddannelse) eller relativ (mod landsgennemsnit). Udledes i `shared.ts` (`indicatorBaselineType`/`categoryBaselineType`/`dimensionBaselineType`); øko-sub-indikatorer har felt `baselineType`, sociale udleder fra `absoluteScore`. ScoreBars viser mærke "mod mål"/"blandet" (relativ = intet mærke). Regel: scor mod mål hvor en meningsfuld per-kommune-grænse findes, ellers landsgennemsnit.
```

- [ ] **Step 2: Endelig fuld verifikation**

Run (fra `webapp/`, dev stoppet): `npm run build`
Expected: "✓ Compiled successfully", TypeScript rent, 104/104 sider.

- [ ] **Step 3: Samlet browser-DOM-tjek** (start frisk preview, `/kommune/Thisted`):
- Education-relateret: Uddannelse-kategoriens score er faldet (education nu mod 95 %), og Uddannelse har "blandet"-mærke.
- Energi har "mod mål"; Forurening har "blandet"; relative dimensioner (Sundhed, Næringsstoffer, Vand, Areal) har intet mærke.
- Ring-legenden viser den nye forklaringslinje.
- Skift baseline-toggle (Kommunegruppe/Landsgennemsnit/Top 10%): education- og energi-scoren ændrer sig IKKE (absoluteScore virker).

- [ ] **Step 4: Checkpoint** - hele ændringssættet klar til Augusts GitHub Desktop-commit.

---

## Self-Review (udfyldt af planforfatter)

**Spec-dækning:**
- Regel (absolut hvor muligt) → Task 1 (education) + Task 2 (klassifikation). ✓
- Klassifikationsmodel (baselineType) → Task 2. ✓
- Synlighed: dimensions-mærke → Task 3; øko-sub-markør → Task 3; legende → Task 4. ✓
- Education ægte absolut → Task 1. ✓
- "Blandet" kun Uddannelse + Forurening → følger af Task 2-klassifikationen (verificeres i Task 3 Step 6 + Task 6 Step 3). ✓
- Metode-note + CLAUDE.md → Task 5 + Task 6. ✓

**Placeholder-scan:** Ingen TBD/TODO; alle kode-steps har konkret kode. ✓

**Type-konsistens:** `DimBaselineType`/`BaselineType` defineret i Task 2 og brugt i Task 3. `baselineType`-felt defineret i interface (Task 2 Step 1) før brug (Task 2 Step 2, Task 3 Step 4). `categoryBaselineType`/`dimensionBaselineType`/`indicatorBaselineType` defineret i Task 2 Step 3, importeret/brugt i Task 3. ✓

**Bevidst afvigelse fra writing-plans-skabelonen:** ingen pytest/TDD (intet testframework i projektet) og ingen `git commit`-steps (CLAUDE.md forbyder terminal-git) - erstattet af build + DOM-verifikation og GitHub Desktop-checkpoints.
