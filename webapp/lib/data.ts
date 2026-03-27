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
  const biodiversitetData = loadEcoCsv("biodiversitet_scores.csv", "biodiversitet_ratio");

  // New ecological data (Næringsstoffer, Vand, Forurening)
  const naerNitrogen = loadEcoCsv("naeringsstoffer_scores.csv", "nitrogen_ratio");
  const naerPhosphorus = loadEcoCsv("naeringsstoffer_scores.csv", "phosphorus_ratio");
  const vandWastewater = loadEcoCsv("vand_scores.csv", "wastewater_ratio");
  const vandExtraction = loadEcoCsv("vand_scores.csv", "water_extraction_ratio");
  const forureningWaste = loadEcoCsv("forurening_scores.csv", "waste_ratio");

  // Forbrugsbaseret CO2 (national gennemsnit) - fast proxy for "Påvirkninger udenfor kommunen"
  // Kilde: CONCITO/Energistyrelsen. ~11 ton CO2e/person/år forbrugsbaseret.
  // Grænse: 3 ton (Paris-budget). Ratio = (11/3)*100 ≈ 366.7 (overshoot - samme konvention som øvrige eco)
  const CONSUMPTION_CO2_RATIO = parseFloat(((11 / 3) * 100).toFixed(2)); // 366.67

  // Load democracy data
  const democracyData = loadEcoCsv("democracy_scores.csv", "voter_turnout_ratio");

  // Load new social dimension data
  const faelleskaberSports = loadEcoCsv("faellesskaber_scores.csv", "sports_membership_ratio");
  const faelleskaberCrime = loadEcoCsv("faellesskaber_scores.csv", "crime_ratio");
  const lokalsamfundLibrary = loadEcoCsv("lokalsamfund_scores.csv", "library_ratio");
  const lokalsamfundFacilities = loadEcoCsv("lokalsamfund_scores.csv", "facilities_ratio");
  const mobilitetCommute = loadEcoCsv("mobilitet_scores.csv", "commute_ratio");
  const mobilitetCar = loadEcoCsv("mobilitet_scores.csv", "car_access_ratio");
  const velfaerdChildren = loadEcoCsv("velfaerd_extra_scores.csv", "vulnerable_children_ratio");
  const velfaerdNeet = loadEcoCsv("velfaerd_extra_scores.csv", "neet_ratio");

  // Load extra social dimension data (round 2)
  const sundhedHospital = loadEcoCsv("sundhed_extra_scores.csv", "hospital_use_ratio");
  const uddannelseLow = loadEcoCsv("uddannelse_extra_scores.csv", "low_education_ratio");
  const boligArea = loadEcoCsv("bolig_extra_scores.csv", "housing_area_ratio");
  const samskabelseMusic = loadEcoCsv("samskabelse_extra_scores.csv", "music_school_ratio");
  const lokalClassSize = loadEcoCsv("lokalsamfund_extra_scores.csv", "class_size_ratio");
  const lokalDaycare = loadEcoCsv("lokalsamfund_extra_scores.csv", "daycare_ratio");
  const lokalSportsSpend = loadEcoCsv("lokalsamfund_extra_scores.csv", "sports_spending_ratio");

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

    // Inject indicators from separate CSVs
    const kommuneKode = row["kommune_kode"] || "";
    if (democracyData[kommuneKode] !== undefined) {
      ratios["voter_turnout"] = democracyData[kommuneKode];
    }
    // Fællesskaber
    if (faelleskaberSports[kommuneKode] !== undefined) {
      ratios["sports_membership"] = faelleskaberSports[kommuneKode];
    }
    if (faelleskaberCrime[kommuneKode] !== undefined) {
      ratios["crime_rate"] = faelleskaberCrime[kommuneKode];
    }
    // Lokalsamfund
    if (lokalsamfundLibrary[kommuneKode] !== undefined) {
      ratios["library_use"] = lokalsamfundLibrary[kommuneKode];
    }
    if (lokalsamfundFacilities[kommuneKode] !== undefined) {
      ratios["sports_facilities"] = lokalsamfundFacilities[kommuneKode];
    }
    // Mobilitet
    if (mobilitetCommute[kommuneKode] !== undefined) {
      ratios["commute_distance"] = mobilitetCommute[kommuneKode];
    }
    if (mobilitetCar[kommuneKode] !== undefined) {
      ratios["car_access"] = mobilitetCar[kommuneKode];
    }
    // Velfærd (ekstra)
    if (velfaerdChildren[kommuneKode] !== undefined) {
      ratios["vulnerable_children"] = velfaerdChildren[kommuneKode];
    }
    if (velfaerdNeet[kommuneKode] !== undefined) {
      ratios["neet"] = velfaerdNeet[kommuneKode];
    }
    // Sundhed (ekstra)
    if (sundhedHospital[kommuneKode] !== undefined) {
      ratios["hospital_use"] = sundhedHospital[kommuneKode];
    }
    // Uddannelse (ekstra)
    if (uddannelseLow[kommuneKode] !== undefined) {
      ratios["low_education"] = uddannelseLow[kommuneKode];
    }
    // Bolig (ekstra)
    if (boligArea[kommuneKode] !== undefined) {
      ratios["housing_area"] = boligArea[kommuneKode];
    }
    // Samskabelse (ekstra)
    if (samskabelseMusic[kommuneKode] !== undefined) {
      ratios["music_school"] = samskabelseMusic[kommuneKode];
    }
    // Lokalsamfund (ekstra)
    if (lokalClassSize[kommuneKode] !== undefined) {
      ratios["class_size"] = lokalClassSize[kommuneKode];
    }
    if (lokalDaycare[kommuneKode] !== undefined) {
      ratios["daycare_ratio"] = lokalDaycare[kommuneKode];
    }
    if (lokalSportsSpend[kommuneKode] !== undefined) {
      ratios["sports_spending"] = lokalSportsSpend[kommuneKode];
    }

    // consumption_co2 er nu en økologisk dimension - se eco_ratios nedenfor

    // Ecological ratios
    const eco_ratios: Record<string, number | null> = {};
    const kode = row["kommune_kode"] || "";

    // TORUS miljøaspekter - data fra separate CSV-filer
    const ecoSources: Record<string, Record<string, number | null>> = {
      klimapaavirkning: climateData,
      cirkularitet: consumptionData,
      arealanvendelse: landUseData,
      biodiversitet: biodiversitetData,
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
    // Forbrugsbaseret CO2 er ens for alle kommuner (nationalt gennemsnit)
    eco_ratios["forbrug_co2"] = CONSUMPTION_CO2_RATIO;

    // Multi-indicator eco dimensions (gennemsnit af flere indikatorer)
    // Næringsstoffer: kvælstof + fosfor udledning pr. capita (inverteret)
    const naerN = naerNitrogen[kode] ?? null;
    const naerP = naerPhosphorus[kode] ?? null;
    const naerVals = [naerN, naerP].filter((v): v is number => v !== null);
    eco_ratios["naeringsstoffer"] = naerVals.length > 0
      ? parseFloat((naerVals.reduce((a, b) => a + b, 0) / naerVals.length).toFixed(2))
      : null;

    // Vand: spildevand + vandindvinding pr. capita (inverteret)
    const vandWW = vandWastewater[kode] ?? null;
    const vandEx = vandExtraction[kode] ?? null;
    const vandVals = [vandWW, vandEx].filter((v): v is number => v !== null);
    eco_ratios["vand"] = vandVals.length > 0
      ? parseFloat((vandVals.reduce((a, b) => a + b, 0) / vandVals.length).toFixed(2))
      : null;

    // Forurening: husholdningsaffald pr. capita (inverteret)
    eco_ratios["forurening"] = forureningWaste[kode] ?? null;

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
