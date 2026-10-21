// Genskaber de konstanter, som komponenterne fra det gamle site bruger (webapp/lib/shared.ts),
// ud fra registret og manifestet. Spec 4.3: "PRÆCIS samme form og indhold".
// Verificeret mod migration/baseline/metadata_baseline.json i fase 1 (migration/fase1/verify.mjs).
//
// Manifestet gives som argument i stedet for at blive importeret her, så filen virker
// både i Vite og i Node uden JSON-import-attributter.

import type { IndicatorDef, DimensionDef, KommuneDef, Manifest, BaselineType } from "./types.ts";

export interface LegacyIndicator {
  id: string;
  name: string;
  table: string;
  source: string;
  category: "social" | "ecological";
  inverse: boolean;
  dataYear?: string;
  baselineLevel?: 1 | 2 | 3;
  absoluteTarget?: string;
  absoluteScore?: boolean;
  rawUnit?: string;
}

export interface LegacySocialCategory {
  id: string;
  name: string;
  description?: string;
  indicatorIds: string[];
}

export interface LegacySubIndicator {
  rawKey: string;
  ratioKey?: string;
  label: string;
  unit: string;
  boundary?: string;
  lowerIsBetter?: boolean;
  baselineType?: BaselineType;
}

export interface LegacyEcologicalDimension {
  id: string;
  name: string;
  shortName: string;
  description?: string;
  source?: string;
  sourceLabel?: string;
  unit?: string;
  boundary?: string;
  subIndicators?: LegacySubIndicator[];
}

export interface LegacyConstants {
  INDICATORS: LegacyIndicator[];
  SOCIAL_CATEGORIES: LegacySocialCategory[];
  ECOLOGICAL_DIMENSIONS: LegacyEcologicalDimension[];
  KOMMUNEGRUPPE: Record<string, number>;
  KOMMUNEGRUPPE_NAVNE: Record<number, string>;
  ECO_RAW_KEY_MAP: Record<string, { rawKey: string; ratioKey: string | null }>;
  DOUGHNUT_EDITION_YEAR: string;
  DOUGHNUT_DEFAULT_DATA_YEAR: string;
}

/** Sætter kun nøglen når værdien findes, så objekterne får samme nøgler som de gamle konstanter. */
function put<T extends object>(obj: T, key: string, value: unknown): void {
  if (value !== undefined) (obj as Record<string, unknown>)[key] = value;
}

export function buildLegacyConstants(input: {
  indicators: IndicatorDef[];
  dimensions: DimensionDef[];
  kommuner: KommuneDef[];
  kommunegruppeNavne: Record<number, string>;
  editionYear: string;
  defaultDataYear: string;
  manifest: Manifest;
}): LegacyConstants {
  const { indicators, dimensions, kommuner, manifest } = input;
  const active = indicators.filter((i) => i.active);
  const byDimension = (dimId: string, kind: IndicatorDef["kind"]) =>
    active.filter((i) => i.dimensionId === dimId && i.kind === kind).sort((a, b) => a.sortOrder - b.sortOrder);

  const INDICATORS: LegacyIndicator[] = active
    .filter((i) => i.kind === "social")
    .map((i) => {
      const o = {
        id: i.id,
        name: i.name,
        table: i.sourceTable ?? "",
        source: i.sourceUrl ?? "",
        category: "social" as const,
        inverse: i.inverse ?? false,
      } as LegacyIndicator;
      put(o, "dataYear", manifest.indicators[i.id]?.data_year);
      put(o, "baselineLevel", i.baselineLevel);
      put(o, "absoluteTarget", i.absoluteTarget);
      put(o, "absoluteScore", i.absoluteScore);
      put(o, "rawUnit", i.unit);
      return o;
    });

  const SOCIAL_CATEGORIES: LegacySocialCategory[] = dimensions
    .filter((d) => d.kind === "social")
    .sort((a, b) => a.sortOrder - b.sortOrder)
    .map((d) => {
      const o = { id: d.id, name: d.name } as LegacySocialCategory;
      put(o, "description", d.description);
      o.indicatorIds = byDimension(d.id, "social").filter((i) => i.scoredInCategory).map((i) => i.id);
      return o;
    });

  const ECOLOGICAL_DIMENSIONS: LegacyEcologicalDimension[] = dimensions
    .filter((d) => d.kind === "ecological")
    .sort((a, b) => a.sortOrder - b.sortOrder)
    .map((d) => {
      const o = { id: d.id, name: d.name, shortName: d.shortName ?? "" } as LegacyEcologicalDimension;
      put(o, "description", d.description);
      put(o, "source", d.sourceUrl);
      put(o, "sourceLabel", d.sourceLabel);
      put(o, "unit", d.unit);
      put(o, "boundary", d.boundary);
      const subs = byDimension(d.id, "ecological");
      if (subs.length > 0) {
        o.subIndicators = subs.map((s) => {
          const sub = { rawKey: s.rawKey ?? "" } as LegacySubIndicator;
          put(sub, "ratioKey", s.ratioKey ?? undefined);
          sub.label = s.name;
          sub.unit = s.unit;
          put(sub, "boundary", s.boundary);
          put(sub, "lowerIsBetter", s.lowerIsBetter);
          put(sub, "baselineType", s.baselineType);
          return sub;
        });
      }
      return o;
    });

  const KOMMUNEGRUPPE: Record<string, number> = {};
  for (const k of kommuner) KOMMUNEGRUPPE[k.kode] = k.gruppe;

  const ECO_RAW_KEY_MAP: LegacyConstants["ECO_RAW_KEY_MAP"] = {};
  for (const i of active) {
    if (i.kind === "ecological") ECO_RAW_KEY_MAP[i.id] = { rawKey: i.rawKey ?? "", ratioKey: i.ratioKey ?? null };
  }

  return {
    INDICATORS,
    SOCIAL_CATEGORIES,
    ECOLOGICAL_DIMENSIONS,
    KOMMUNEGRUPPE,
    KOMMUNEGRUPPE_NAVNE: input.kommunegruppeNavne,
    ECO_RAW_KEY_MAP,
    DOUGHNUT_EDITION_YEAR: input.editionYear,
    DOUGHNUT_DEFAULT_DATA_YEAR: input.defaultDataYear,
  };
}
