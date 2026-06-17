# Kommunegruppe-baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tilføj "Kommunegruppe" som tredje baseline-mulighed i baseline-toggle, så sociale indikatorer sammenlignes med gennemsnittet af kommuner i samme DST-kommunegruppe (G1-G5) i stedet for alle 98 kommuner.

**Architecture:** Spejler den eksisterende `computeTop10Ratios`-funktion: ved loadData()-tid beregnes et nyt `group_ratios`-sæt pr. kommune ved at omskalere eksisterende ratios mod gruppens gennemsnit. DST-mapping (kode→gruppe) flyttes til shared.ts som TS-konstant. Baseline-context udvides med en tredje mode "kommunegruppe". Ingen ændringer i data-pipeline eller fetch-scripts.

**Tech Stack:** TypeScript/React, Next.js 16 (static export), Tailwind 4. Ingen nye afhængigheder.

---

## Filer

| Fil | Rolle |
|-----|-------|
| `webapp/lib/shared.ts` | Tilføj KOMMUNEGRUPPE-mapping, group_ratios i KommuneData, computeGroupRatios() |
| `webapp/lib/data.ts` | Kald computeGroupRatios() i loadData() |
| `webapp/lib/baseline-context.tsx` | Udvid BaselineMode med "kommunegruppe" |
| `webapp/components/BaselineToggle.tsx` | Tredje knap "Kommunegruppe" / "Gruppe" |
| `webapp/app/kommune/[navn]/client.tsx` | Vælg group_ratios når mode==="kommunegruppe", opdater label |

---

## Task 1: KOMMUNEGRUPPE-mapping + computeGroupRatios i shared.ts

**Filer:**
- Modify: `webapp/lib/shared.ts` (efter `computeTop10Ratios`, ca. linje 931)

- [ ] **Step 1: Tilføj KOMMUNEGRUPPE-konstant og helper til shared.ts**

Indsæt dette blok umiddelbart EFTER den eksisterende `computeTop10Ratios`-funktion (ca. linje 931), MEN INDEN `scoreColor`:

```typescript
// --- KOMMUNEGRUPPE-MAPPING (DST KOMMUNEGRUPPER_V1_2018) ---
// G1: Hovedstadskommuner (24), G2: Storbykommuner (3),
// G3: Provinsbykommuner (16), G4: Oplandskommuner (24), G5: Landkommuner (31)
export const KOMMUNEGRUPPE: Record<string, number> = {
  // G1: Hovedstadskommuner
  "101": 1, "147": 1, "151": 1, "153": 1, "155": 1, "157": 1, "159": 1, "161": 1,
  "163": 1, "165": 1, "167": 1, "169": 1, "173": 1, "175": 1, "183": 1, "185": 1,
  "187": 1, "190": 1, "201": 1, "223": 1, "230": 1, "240": 1, "253": 1, "269": 1,
  // G2: Storbykommuner
  "461": 2, "751": 2, "851": 2,
  // G3: Provinsbykommuner
  "217": 3, "219": 3, "259": 3, "265": 3, "330": 3, "370": 3, "561": 3, "607": 3,
  "615": 3, "621": 3, "630": 3, "657": 3, "661": 3, "730": 3, "740": 3, "791": 3,
  // G4: Oplandskommuner
  "210": 4, "250": 4, "260": 4, "270": 4, "316": 4, "320": 4, "329": 4, "336": 4,
  "340": 4, "350": 4, "410": 4, "420": 4, "430": 4, "440": 4, "450": 4, "480": 4,
  "575": 4, "706": 4, "710": 4, "727": 4, "746": 4, "756": 4, "766": 4, "840": 4,
  // G5: Landkommuner
  "306": 5, "326": 5, "360": 5, "376": 5, "390": 5, "400": 5, "479": 5, "482": 5,
  "492": 5, "510": 5, "530": 5, "540": 5, "550": 5, "563": 5, "573": 5, "580": 5,
  "665": 5, "671": 5, "707": 5, "741": 5, "760": 5, "773": 5, "779": 5, "787": 5,
  "810": 5, "813": 5, "820": 5, "825": 5, "846": 5, "849": 5, "860": 5,
};

export const KOMMUNEGRUPPE_NAVNE: Record<number, string> = {
  1: "Hovedstadskommuner",
  2: "Storbykommuner",
  3: "Provinsbykommuner",
  4: "Oplandskommuner",
  5: "Landkommuner",
};

export function kommunegruppeNavn(kode: string): string {
  const grp = KOMMUNEGRUPPE[kode];
  return grp ? KOMMUNEGRUPPE_NAVNE[grp] : "Kommunegruppe";
}

/**
 * Beregner kommunegruppe-baselines dynamisk fra eksisterende ratios.
 * For hver social indikator og hver gruppe (G1-G5): beregn gruppens uvægtede
 * gennemsnit, og omskaler alle kommuners ratio til denne baseline.
 * 100 = den gennemsnitlige kommune i gruppen.
 * Ekologiske indikatorer påvirkes ikke.
 */
export function computeGroupRatios(allData: KommuneData[]): void {
  const realKommuner = allData.filter((k) => k.kommune_kode !== "000");

  for (const k of allData) {
    k.group_ratios = {};
  }

  for (const ind of INDICATORS) {
    if (ind.category !== "social") continue;

    // Beregn gennemsnit pr. gruppe
    const groupSums: Record<number, number> = {};
    const groupCounts: Record<number, number> = {};

    for (const k of realKommuner) {
      const grp = KOMMUNEGRUPPE[k.kommune_kode];
      if (!grp) continue;
      const ratio = k.ratios[ind.id];
      if (ratio === null) continue;
      groupSums[grp] = (groupSums[grp] ?? 0) + ratio;
      groupCounts[grp] = (groupCounts[grp] ?? 0) + 1;
    }

    const groupAvg: Record<number, number> = {};
    for (const grp of Object.keys(groupSums).map(Number)) {
      if (groupCounts[grp] > 0) {
        groupAvg[grp] = groupSums[grp] / groupCounts[grp];
      }
    }

    // Skaler alle kommuners ratio mod gruppens gennemsnit
    for (const k of allData) {
      const grp = KOMMUNEGRUPPE[k.kommune_kode];
      const ratio = k.ratios[ind.id];
      const avg = grp ? groupAvg[grp] : undefined;

      if (ratio === null || avg === undefined || avg === 0) {
        k.group_ratios[ind.id] = null;
      } else {
        k.group_ratios[ind.id] = parseFloat(((ratio / avg) * 100).toFixed(2));
      }
    }
  }
}
```

- [ ] **Step 2: Tilføj `group_ratios` til KommuneData-interfacet i shared.ts**

Find interfacet `KommuneData` (ca. linje 876) og tilføj feltet efter `top10_ratios`:

```typescript
export interface KommuneData {
  kommune_kode: string;
  kommune_navn: string;
  ratios: Record<string, number | null>;
  top10_ratios: Record<string, number | null>;
  group_ratios: Record<string, number | null>;   // <-- tilføj denne linje
  eco_ratios: Record<string, number | null>;
  rawValues: Record<string, number | null>;
  social_avg: number | null;
  overall_avg: number | null;
}
```

- [ ] **Step 3: Verificer TypeScript kompilerer (ingen fejl)**

```bash
cd /Users/augustseptimiuskrogh/Documents/GitHub/doughnut/webapp
npx tsc --noEmit 2>&1 | head -30
```

Forventet: ingen fejl (eller kun fejl om manglende initialisering i data.ts, som løses i Task 2).

---

## Task 2: Kald computeGroupRatios i data.ts

**Filer:**
- Modify: `webapp/lib/data.ts`

- [ ] **Step 1: Importer computeGroupRatios og KOMMUNEGRUPPE_NAVNE**

Find import-linjen øverst i data.ts (linje 24):
```typescript
import { INDICATORS, ECOLOGICAL_DIMENSIONS, computeTop10Ratios, type KommuneData } from "./shared";
```

Erstat med:
```typescript
import { INDICATORS, ECOLOGICAL_DIMENSIONS, computeTop10Ratios, computeGroupRatios, type KommuneData } from "./shared";
```

- [ ] **Step 2: Initialiser group_ratios ved opbygning af KommuneData**

Find stedet i `loadData()` (ca. linje 185-199) hvor kommunen pushes til data-arrayet:

```typescript
    data.push({
      kommune_kode: kode,
      kommune_navn: navn,
      ratios,
      top10_ratios: {}, // udfyldes af computeTop10Ratios nedenfor
      eco_ratios,
      rawValues,
      social_avg: null,
      overall_avg: null,
    });
```

Erstat med:
```typescript
    data.push({
      kommune_kode: kode,
      kommune_navn: navn,
      ratios,
      top10_ratios: {},   // udfyldes af computeTop10Ratios nedenfor
      group_ratios: {},   // udfyldes af computeGroupRatios nedenfor
      eco_ratios,
      rawValues,
      social_avg: null,
      overall_avg: null,
    });
```

- [ ] **Step 3: Kald computeGroupRatios efter computeTop10Ratios**

Find (ca. linje 201-203):
```typescript
  // Beregn Top 10%-baselines dynamisk fra de indlæste ratios
  computeTop10Ratios(data);
```

Erstat med:
```typescript
  // Beregn Top 10%-baselines dynamisk fra de indlæste ratios
  computeTop10Ratios(data);
  // Beregn kommunegruppe-baselines
  computeGroupRatios(data);
```

- [ ] **Step 4: Verificer TypeScript kompilerer**

```bash
cd /Users/augustseptimiuskrogh/Documents/GitHub/doughnut/webapp
npx tsc --noEmit 2>&1 | head -30
```

Forventet: ingen fejl.

- [ ] **Step 5: Commit**

```bash
cd /Users/augustseptimiuskrogh/Documents/GitHub/doughnut
git add webapp/lib/shared.ts webapp/lib/data.ts
git commit -m "feat: tilføj kommunegruppe-mapping og computeGroupRatios"
```

---

## Task 3: Udvid BaselineMode i baseline-context.tsx

**Filer:**
- Modify: `webapp/lib/baseline-context.tsx`

- [ ] **Step 1: Tilføj "kommunegruppe" til BaselineMode og skift default**

Nuværende indhold af baseline-context.tsx:
```typescript
"use client";

import { createContext, useContext, useState } from "react";

export type BaselineMode = "avg" | "top10";

interface BaselineContextValue {
  mode: BaselineMode;
  setMode: (mode: BaselineMode) => void;
}

const BaselineContext = createContext<BaselineContextValue>({
  mode: "avg",
  setMode: () => {},
});

export function BaselineProvider({ children }: { children: React.ReactNode }) {
  const [mode, setMode] = useState<BaselineMode>("avg");
  return (
    <BaselineContext.Provider value={{ mode, setMode }}>
      {children}
    </BaselineContext.Provider>
  );
}

export function useBaseline() {
  return useContext(BaselineContext);
}
```

Erstat hele filen med (default ændres til "kommunegruppe"):
```typescript
"use client";

import { createContext, useContext, useState } from "react";

export type BaselineMode = "avg" | "top10" | "kommunegruppe";

interface BaselineContextValue {
  mode: BaselineMode;
  setMode: (mode: BaselineMode) => void;
}

const BaselineContext = createContext<BaselineContextValue>({
  mode: "kommunegruppe",
  setMode: () => {},
});

export function BaselineProvider({ children }: { children: React.ReactNode }) {
  const [mode, setMode] = useState<BaselineMode>("kommunegruppe");
  return (
    <BaselineContext.Provider value={{ mode, setMode }}>
      {children}
    </BaselineContext.Provider>
  );
}

export function useBaseline() {
  return useContext(BaselineContext);
}
```

- [ ] **Step 2: Verificer TypeScript kompilerer**

```bash
cd /Users/augustseptimiuskrogh/Documents/GitHub/doughnut/webapp
npx tsc --noEmit 2>&1 | head -30
```

Forventet: ingen fejl (men BaselineToggle og client.tsx kan give fejl om manglende håndtering af ny mode - løses i næste tasks).

---

## Task 4: Tredje knap i BaselineToggle.tsx

**Filer:**
- Modify: `webapp/components/BaselineToggle.tsx`

- [ ] **Step 1: Erstat hele BaselineToggle.tsx**

```typescript
"use client";

import { useBaseline, type BaselineMode } from "@/lib/baseline-context";

export default function BaselineToggle() {
  const { mode, setMode } = useBaseline();

  const options: { value: BaselineMode; label: string; short: string; title: string }[] = [
    {
      value: "kommunegruppe",
      label: "Kommunegruppe",
      short: "Gruppe",
      title: "Scorer sammenlignes med gennemsnittet af kommuner i samme kommunegruppe (Hoved-, Storby-, Provinsby-, Oplands- eller Landkommuner)",
    },
    {
      value: "avg",
      label: "Landsgennemsnit",
      short: "Gns",
      title: "Scorer sammenlignes med det nationale gennemsnit (100 = gennemsnittet af alle 98 kommuner)",
    },
    {
      value: "top10",
      label: "Top 10%",
      short: "Top 10%",
      title: "Scorer sammenlignes med de 10 bedst præsterende kommuner (100 = top 10%-niveauet)",
    },
  ];

  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="text-gray-400 text-xs hidden sm:inline">Baseline:</span>
      <div className="flex rounded-lg border border-gray-200 overflow-hidden">
        {options.map((opt, i) => (
          <button
            key={opt.value}
            onClick={() => setMode(opt.value)}
            title={opt.title}
            className={`px-2 sm:px-3 py-1.5 text-xs transition-colors ${
              mode === opt.value
                ? "bg-emerald-600 text-white font-medium"
                : "bg-white text-gray-600 hover:bg-gray-50"
            } ${i > 0 ? "border-l border-gray-200" : ""}`}
          >
            <span className="hidden sm:inline">{opt.label}</span>
            <span className="sm:hidden">{opt.short}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verificer TypeScript kompilerer**

```bash
cd /Users/augustseptimiuskrogh/Documents/GitHub/doughnut/webapp
npx tsc --noEmit 2>&1 | head -30
```

Forventet: ingen fejl.

---

## Task 5: Vælg group_ratios i client.tsx + opdater label

**Filer:**
- Modify: `webapp/app/kommune/[navn]/client.tsx`

- [ ] **Step 1: Importer kommunegruppeNavn**

Find import-linjen (linje 5):
```typescript
import { computeCategoryScores, ECOLOGICAL_DIMENSIONS } from "@/lib/shared";
```

Erstat med:
```typescript
import { computeCategoryScores, ECOLOGICAL_DIMENSIONS, kommunegruppeNavn } from "@/lib/shared";
```

- [ ] **Step 2: Opdater activeRatios og baselineLabel**

Find (linje 28-37):
```typescript
  const activeRatios = mode === "top10" ? kommune.top10_ratios : kommune.ratios;

  const categoryScores = computeCategoryScores(activeRatios);
  const categoriesAboveThreshold = categoryScores.filter(
    (c) => c.hasData && c.score !== null && c.score >= 100
  ).length;
  const categoriesWithData = categoryScores.filter((c) => c.hasData).length;

  const baselineLabel =
    mode === "top10" ? "top 10%-niveauet" : "landsgennemsnittet";
```

Erstat med:
```typescript
  const activeRatios =
    mode === "top10"
      ? kommune.top10_ratios
      : mode === "kommunegruppe"
      ? kommune.group_ratios
      : kommune.ratios;

  const categoryScores = computeCategoryScores(activeRatios);
  const categoriesAboveThreshold = categoryScores.filter(
    (c) => c.hasData && c.score !== null && c.score >= 100
  ).length;
  const categoriesWithData = categoryScores.filter((c) => c.hasData).length;

  const baselineLabel =
    mode === "top10"
      ? "top 10%-niveauet"
      : mode === "kommunegruppe"
      ? `gennemsnittet for ${kommunegruppeNavn(kommune.kommune_kode)}`
      : "landsgennemsnittet";
```

- [ ] **Step 3: Verificer TypeScript kompilerer - ingen fejl**

```bash
cd /Users/augustseptimiuskrogh/Documents/GitHub/doughnut/webapp
npx tsc --noEmit 2>&1 | head -30
```

Forventet: ingen fejl.

- [ ] **Step 4: Byg webappen for at verificere statisk build virker**

```bash
cd /Users/augustseptimiuskrogh/Documents/GitHub/doughnut/webapp
npm run build 2>&1 | tail -20
```

Forventet: `✓ Generating static pages (99/99)` eller lignende succesfuldt output uden fejl.

- [ ] **Step 5: Commit alle UI-ændringer**

```bash
cd /Users/augustseptimiuskrogh/Documents/GitHub/doughnut
git add webapp/lib/baseline-context.tsx webapp/components/BaselineToggle.tsx webapp/app/kommune/[navn]/client.tsx
git commit -m "feat: kommunegruppe-baseline som tredje toggle-mulighed"
```

---

## Manuel verifikation (efter build)

Start udviklerseveren (dobbeltklik `Start udviklerserver.command`) og åbn `http://127.0.0.1:3000/kommune/Thisted`.

Tjek:
1. Baseline-toggle har **tre knapper**: Kommunegruppe (aktiv/grøn som default), Landsgennemsnit, Top 10%.
2. Summary-teksten viser "over gennemsnittet for Landkommuner".
3. Skift til Landsgennemsnit: teksten skifter til "over landsgennemsnittet" og scorerne ændrer sig.
4. Mobilvisning (smal skærm): kortlabels vises - "Gruppe", "Gns", "Top 10%".
5. En kommune i G1 (fx København 101): label viser "Hovedstadskommuner".
