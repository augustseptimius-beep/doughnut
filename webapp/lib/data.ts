import fs from "fs";
import path from "path";

// Re-export shared types and constants for server components
export {
  INDICATORS,
  SOCIAL_CATEGORIES,
  ECOLOGICAL_DIMENSIONS,
  scoreColor,
  scoreBgColor,
  scoreBarColor,
  computeCategoryScores,
  computeOverallFromCategories,
  computeTop10Ratios,
  DOUGHNUT_EDITION_YEAR,
  DOUGHNUT_DEFAULT_DATA_YEAR,
} from "./shared";
export type {
  Indicator,
  KommuneData,
  SocialCategory,
  EcologicalDimension,
  CategoryScore,
} from "./shared";

import { INDICATORS, ECOLOGICAL_DIMENSIONS, computeTop10Ratios, type KommuneData } from "./shared";

let cachedData: KommuneData[] | null = null;

// ─── Mapping fra master-CSV indicator_id til rawValues-nøgler ───────
// ScoreBars og DoughnutRing forventer specifikke nøgler i kommune.rawValues
// for at vise sub-indikatorer korrekt. Disse nøgler er defineret af
// EcologicalDimension.subIndicators.rawKey/ratioKey i shared.ts.
//
// Master-CSV bruger korte indicator_ids (f.eks. "luftkvalitet_no2"). Her
// mapper vi dem til de rawValues-nøgler som UI-komponenterne læser fra.
//
// Format: master_id → { rawKey: nøgle for råværdi, ratioKey: nøgle for ratio (kan være null) }
const ECO_RAW_KEY_MAP: Record<string, { rawKey: string; ratioKey: string | null }> = {
  // Klimapåvirkning
  klimapaavirkning: { rawKey: "eco_klima_raw", ratioKey: "klimapaavirkning_self" },
  // Luftkvalitet
  luftkvalitet_no2: { rawKey: "luftkvalitet_no2", ratioKey: "luftkvalitet_no2_ratio" },
  luftkvalitet_pm25: { rawKey: "luftkvalitet_pm25", ratioKey: "luftkvalitet_pm25_ratio" },
  // Cirkularitet
  cirkularitet_recycling: { rawKey: "eco_cirkularitet_raw", ratioKey: "eco_cirkularitet_ratio" },
  cirkularitet_waste: { rawKey: "eco_affald_raw", ratioKey: "eco_affald_ratio" },
  // Næringsstoffer
  naer_nitrogen: { rawKey: "eco_naer_n_raw", ratioKey: "eco_naer_n_ratio" },
  naer_phosphorus: { rawKey: "eco_naer_p_raw", ratioKey: "eco_naer_p_ratio" },
  naer_landbrug: { rawKey: "eco_naer_landbrug_raw", ratioKey: "eco_naer_landbrug_ratio" },
  // Biodiversitet (single)
  biodiversitet: { rawKey: "eco_bio_raw", ratioKey: "biodiversitet_self" },
  // Forbrug CO2 (single)
  forbrug_co2: { rawKey: "forbrug_co2", ratioKey: "forbrug_co2_self" },
  // Forurening - pesticider (worst-of)
  pesticider: { rawKey: "eco_pesticid_raw", ratioKey: "pesticider_self" },
  // Vand (worst-of: nitrat + vandindvinding)
  nitrat:          { rawKey: "eco_nitrat_raw",         ratioKey: "nitrat_self" },
  vandindvinding:  { rawKey: "eco_vandindvinding_raw", ratioKey: "vandindvinding_self" },
  // Arealanvendelse (worst-of: intensivt landbrug + bebygget)
  areal_intensiv: { rawKey: "eco_areal_intensiv_raw", ratioKey: "areal_intensiv_ratio" },
  areal_bebygget: { rawKey: "eco_areal_bebygget_raw", ratioKey: "areal_bebygget_ratio" },
};

// ─── Master-CSV loader ───────────────────────────────────────────────
// Long format: én række pr. (kommune × indikator). Genereret af
// scripts/build_master_csv.py. Erstatter de tidligere 25+ separate
// loadEcoCsv-kald.
//
// Specielle indicator_id'er:
//   _dim_<dimension>  →  worst-of dimension-score (eco_ratios[dimension])

interface MasterRow {
  kommune_kode: string;
  kommune_navn: string;
  indicator_id: string;
  ratio: string;
  raw_value: string;
  unit: string;
  data_year: string;
  source: string;
  category: string;
  dimension: string;
}

function parseMasterCsv(): MasterRow[] {
  const csvPath = path.join(process.cwd(), "..", "data", "master_indicators.csv");
  if (!fs.existsSync(csvPath)) {
    throw new Error(
      `master_indicators.csv mangler på sti: ${csvPath}\n` +
      `Kør 'python3 scripts/build_master_csv.py' i projektets rodmappe og commit filen.`
    );
  }
  const raw = fs.readFileSync(csvPath, "utf-8");
  const lines = raw.trim().split("\n");
  if (lines.length < 2) return [];

  const headers = lines[0].split(",");
  const rows: MasterRow[] = [];

  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(",");
    const obj: Record<string, string> = {};
    headers.forEach((h, idx) => {
      obj[h.trim()] = (cols[idx] || "").trim();
    });
    rows.push(obj as unknown as MasterRow);
  }
  return rows;
}

function parseFloatOrNull(s: string): number | null {
  if (!s || s === "") return null;
  const n = parseFloat(s);
  return isNaN(n) ? null : n;
}

export function loadData(): KommuneData[] {
  if (cachedData) return cachedData;

  const rows = parseMasterCsv();

  // Group rows by kommune_kode
  const byKommune = new Map<string, { navn: string; rows: MasterRow[] }>();
  for (const r of rows) {
    if (!byKommune.has(r.kommune_kode)) {
      byKommune.set(r.kommune_kode, { navn: r.kommune_navn, rows: [] });
    }
    byKommune.get(r.kommune_kode)!.rows.push(r);
  }

  // Build KommuneData for each kommune
  const data: KommuneData[] = [];
  for (const [kode, { navn, rows: kommuneRows }] of byKommune.entries()) {
    const ratios: Record<string, number | null> = {};
    const rawValues: Record<string, number | null> = {};
    const eco_ratios: Record<string, number | null> = {};

    for (const r of kommuneRows) {
      const ratio = parseFloatOrNull(r.ratio);
      const rawVal = parseFloatOrNull(r.raw_value);

      // Dimension-aggregat-rækker (worst-of scores)
      if (r.indicator_id.startsWith("_dim_")) {
        const dimId = r.indicator_id.substring(5);
        eco_ratios[dimId] = ratio;
        continue;
      }

      // Sociale indikatorer: ratios + rawValues nøglet på indicator_id (matcher INDICATORS-id)
      if (r.category === "social") {
        ratios[r.indicator_id] = ratio;
        if (rawVal !== null) {
          rawValues[r.indicator_id] = rawVal;
        }
        continue;
      }

      // Økologiske sub-indikatorer: skriv til de specifikke rawValues-nøgler
      // som ScoreBars/DoughnutRing forventer (jf. EcologicalDimension.subIndicators)
      if (r.category === "ecological") {
        const keys = ECO_RAW_KEY_MAP[r.indicator_id];
        if (keys) {
          if (rawVal !== null) rawValues[keys.rawKey] = rawVal;
          if (keys.ratioKey && ratio !== null) rawValues[keys.ratioKey] = ratio;
        }
      }
    }

    // Sørg for at alle INDICATORS er repræsenteret (null hvis ingen data)
    for (const ind of INDICATORS) {
      if (!(ind.id in ratios)) {
        ratios[ind.id] = null;
      }
    }

    // Sørg for at alle ECOLOGICAL_DIMENSIONS er repræsenteret (null hvis ingen data)
    // Vigtigt: client.tsx skelner mellem null og undefined når den tæller "afventer data"-dimensioner.
    // Inaktive dimensioner (forurening, vand, arealanvendelse) skal være eksplicit null.
    for (const dim of ECOLOGICAL_DIMENSIONS) {
      if (!(dim.id in eco_ratios)) {
        eco_ratios[dim.id] = null;
      }
    }

    data.push({
      kommune_kode: kode,
      kommune_navn: navn,
      ratios,
      top10_ratios: {}, // udfyldes af computeTop10Ratios nedenfor
      eco_ratios,
      rawValues,
      // social_avg og overall_avg er pre-computed i den gamle CSV men
      // bruges ikke længere af UI'et (det beregnes via computeCategoryScores).
      // Vi sætter dem til null - hvis en gammel side stadig læser dem, vil de
      // blot vise '–'.
      social_avg: null,
      overall_avg: null,
    });
  }

  // Beregn Top 10%-baselines dynamisk fra de indlæste ratios
  computeTop10Ratios(data);

  cachedData = data;
  return data;
}

export function getKommune(navn: string): KommuneData | undefined {
  const data = loadData();
  const decoded = decodeURIComponent(navn);
  return data.find(
    (k) =>
      k.kommune_navn.toLowerCase() === decoded.toLowerCase() ||
      k.kommune_kode === decoded
  );
}

export function getAllKommuner(): KommuneData[] {
  // Kode "000" = Danmark-aggregat (ikke i master-CSV pt., men holdes ude for sikkerhed)
  return loadData().filter((k) => k.kommune_kode !== "000");
}
