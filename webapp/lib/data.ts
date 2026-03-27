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
} from "./shared";
export type {
  Indicator,
  KommuneData,
  SocialCategory,
  EcologicalDimension,
  CategoryScore,
} from "./shared";

import { INDICATORS, ECOLOGICAL_DIMENSIONS, type KommuneData } from "./shared";

let cachedData: KommuneData[] | null = null;

function loadEcoCsv(
  filename: string,
  ratioColumn: string
): Record<string, number | null> {
  const csvPath = path.join(process.cwd(), "..", "data", filename);
  try {
    if (!fs.existsSync(csvPath)) return {};
    const raw = fs.readFileSync(csvPath, "utf-8");
    const lines = raw.trim().split("\n");
    if (lines.length < 2) return {};

    const headers = lines[0].split(",");
    const result: Record<string, number | null> = {};

    for (let i = 1; i < lines.length; i++) {
      const cols = lines[i].split(",");
      const row: Record<string, string> = {};
      headers.forEach((h, idx) => {
        row[h.trim()] = (cols[idx] || "").trim();
      });

      const kode = row["kommune_kode"];
      const ratio = row[ratioColumn];
      if (kode) {
        result[kode] = ratio && ratio !== "" ? parseFloat(ratio) : null;
      }
    }
    return result;
  } catch {
    return {};
  }
}

export function loadData(): KommuneData[] {
  if (cachedData) return cachedData;

  const csvPath = path.join(process.cwd(), "..", "data", "doughnut_scores.csv");
  const raw = fs.readFileSync(csvPath, "utf-8");
  const lines = raw.trim().split("\n");
  const headers = lines[0].split(",");

  // Load ecological data
  const climateData = loadEcoCsv("climate_scores.csv", "climate_territorial_ratio");
  const consumptionData = loadEcoCsv("consumption_scores.csv", "recycling_ratio");
  const landUseData = loadEcoCsv("land_use_scores.csv", "land_use_ratio");

  // Forbrugsbaseret CO2 (national gennemsnit) - fast proxy for "Påvirkninger udenfor kommunen"
  // Kilde: CONCITO/Energistyrelsen. ~11 ton CO2e/person/år forbrugsbaseret.
  // Grænse: 3 ton (Paris-budget). Ratio = (3/11)*100 ≈ 27.3 (dvs. ~73% shortfall)
  const CONSUMPTION_CO2_RATIO = parseFloat(((3 / 11) * 100).toFixed(2)); // 27.27

  // Load democracy data
  const democracyData = loadEcoCsv("democracy_scores.csv", "voter_turnout_ratio");

  const data: KommuneData[] = [];
  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(",");
    const row: Record<string, string> = {};
    headers.forEach((h, idx) => {
      row[h.trim()] = (cols[idx] || "").trim();
    });

    const ratios: Record<string, number | null> = {};
    for (const ind of INDICATORS) {
      const key = `${ind.id}_ratio`;
      const val = row[key];
      ratios[ind.id] = val && val !== "" ? parseFloat(val) : null;
    }

    // Inject democracy indicators from separate CSV
    const kommuneKode = row["kommune_kode"] || "";
    if (democracyData[kommuneKode] !== undefined) {
      ratios["voter_turnout"] = democracyData[kommuneKode];
    }

    // Inject fixed national consumption CO2 ratio for all municipalities
    ratios["consumption_co2"] = CONSUMPTION_CO2_RATIO;

    // Ecological ratios
    const eco_ratios: Record<string, number | null> = {};
    const kode = row["kommune_kode"] || "";

    // TORUS miljøaspekter - data fra separate CSV-filer
    const ecoSources: Record<string, Record<string, number | null>> = {
      klimapaavirkning: climateData,
      cirkularitet: consumptionData,
      arealanvendelse: landUseData,
    };

    // Klimaregnskabet: kolonner direkte i doughnut_scores.csv (fallback)
    const ecoFromScoresCsv: Record<string, string> = {
      klimapaavirkning: "co2_per_capita_ratio",
    };

    for (const dim of ECOLOGICAL_DIMENSIONS) {
      const inlineCol = ecoFromScoresCsv[dim.id];
      if (inlineCol && row[inlineCol] && row[inlineCol] !== "") {
        eco_ratios[dim.id] = parseFloat(row[inlineCol]);
      } else {
        eco_ratios[dim.id] = ecoSources[dim.id]?.[kode] ?? null;
      }
    }

    const socialAvg = row["social_avg"];
    const overallAvg = row["overall_avg"];

    data.push({
      kommune_kode: kode,
      kommune_navn: row["kommune_navn"] || "",
      ratios,
      eco_ratios,
      social_avg: socialAvg && socialAvg !== "" ? parseFloat(socialAvg) : null,
      overall_avg:
        overallAvg && overallAvg !== "" ? parseFloat(overallAvg) : null,
    });
  }

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
  return loadData().filter((k) => k.kommune_kode !== "000");
}
