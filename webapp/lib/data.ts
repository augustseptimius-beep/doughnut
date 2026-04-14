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

// Loader til cba_2023_estimate.csv som bruger kommunenavn (ikke kommune_kode) som nøgle
function loadCbaCsv(): {
  ratioByName: Record<string, number | null>;
  rawByName: Record<string, number | null>;
} {
  const csvPath = path.join(process.cwd(), "..", "data", "cba_2023_estimate.csv");
  const CBA_BOUNDARY = 3; // ton CO2e/cap/år (Paris-budget, forbrugsbaseret)
  const ratioByName: Record<string, number | null> = {};
  const rawByName: Record<string, number | null> = {};
  try {
    if (!fs.existsSync(csvPath)) return { ratioByName, rawByName };
    const raw = fs.readFileSync(csvPath, "utf-8");
    const lines = raw.trim().split("\n");
    if (lines.length < 2) return { ratioByName, rawByName };
    const headers = lines[0].split(",");
    for (let i = 1; i < lines.length; i++) {
      const cols = lines[i].split(",");
      const row: Record<string, string> = {};
      headers.forEach((h, idx) => { row[h.trim()] = (cols[idx] || "").trim(); });
      const name = row["kommune"];
      const estimate = row["cba_2023_estimate"];
      if (name && estimate && estimate !== "") {
        const tonPerCap = parseFloat(estimate);
        rawByName[name] = tonPerCap;
        ratioByName[name] = parseFloat(((tonPerCap / CBA_BOUNDARY) * 100).toFixed(2));
      }
    }
  } catch { /* silent */ }
  return { ratioByName, rawByName };
}

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
  const climateRawData = loadEcoCsv("climate_scores.csv", "co2e_per_capita");
  // Load raw recycling percentage (not the old social-convention ratio)
  const recyclingPctData = loadEcoCsv("consumption_scores.csv", "recycling_pct");
  const landUseData = loadEcoCsv("land_use_scores.csv", "land_use_ratio");
  const landUseRawData = loadEcoCsv("land_use_scores.csv", "natur_pct");
  const biodiversitetData = loadEcoCsv("biodiversitet_scores.csv", "biodiversitet_ratio");
  const biodiversitetRawData = loadEcoCsv("biodiversitet_scores.csv", "pct_vasentlig_natur");

  // New ecological data (Næringsstoffer, Vand)
  const naerNitrogen = loadEcoCsv("naeringsstoffer_scores.csv", "nitrogen_ratio");
  const naerPhosphorus = loadEcoCsv("naeringsstoffer_scores.csv", "phosphorus_ratio");
  const naerNitrogenRaw = loadEcoCsv("naeringsstoffer_scores.csv", "nitrogen_per_1000");
  const naerPhosphorusRaw = loadEcoCsv("naeringsstoffer_scores.csv", "phosphorus_per_1000");
  // Landbrugs-N: N-loft pr. ha landbrugsjord fra VP3 (Vandområdeplan 3, 2025)
  const nLandbrug = loadEcoCsv("n_landbrug_scores.csv", "n_ratio");
  const vandWastewater = loadEcoCsv("vand_scores.csv", "wastewater_ratio");
  const vandExtraction = loadEcoCsv("vand_scores.csv", "water_extraction_ratio");
  const vandWastewaterRaw = loadEcoCsv("vand_scores.csv", "wastewater_per_1000");
  const vandExtractionRaw = loadEcoCsv("vand_scores.csv", "water_extraction_per_1000");
  // Affald flyttes til cirkularitet (waste_ratio er inverteret: lav score = mere affald)
  const wasteData = loadEcoCsv("forurening_scores.csv", "waste_ratio");
  const wasteRawData = loadEcoCsv("forurening_scores.csv", "waste_kg_per_capita");

  // Luftkvalitet: NO2 og PM2.5 ratio fra DCE/AU UBM-model 2023 (WHO 2021-grænser)
  const luftNo2Data    = loadEcoCsv("luftforurening_scores.csv", "no2_ratio");
  const luftPm25Data   = loadEcoCsv("luftforurening_scores.csv", "pm25_ratio");
  // Råværdier i µg/m³ til visning i sub-indikatorer
  const luftNo2RawData  = loadEcoCsv("luftforurening_scores.csv", "no2_ug_m3");
  const luftPm25RawData = loadEcoCsv("luftforurening_scores.csv", "pm25_ug_m3");

  // Forbrugsbaseret CO2 (kommunespecifik) - Osei-Owusu et al. (2020) nutidsjusteret med ENS GA25
  // Grænse: 3 ton CO2e/cap/år (Paris-budget). Ratio = (estimat / 3) * 100
  // Fallback til nationalt gennemsnit (11 ton) hvis kommunen ikke findes i CSV.
  const { ratioByName: cbaRatioByName, rawByName: cbaRawByName } = loadCbaCsv();
  const CONSUMPTION_CO2_RATIO_FALLBACK = parseFloat(((11 / 3) * 100).toFixed(2)); // 366.67

  // Load democracy data
  const democracyData = loadEcoCsv("democracy_scores.csv", "voter_turnout_ratio");
  const democracyRaw = loadEcoCsv("democracy_scores.csv", "voter_turnout_pct");

  // Load new social dimension data
  const faelleskaberSports = loadEcoCsv("faellesskaber_scores.csv", "sports_membership_ratio");
  const faelleskaberSportsRaw = loadEcoCsv("faellesskaber_scores.csv", "sports_membership_pct");
  const faelleskaberCrime = loadEcoCsv("faellesskaber_scores.csv", "crime_ratio");
  const faelleskaberCrimeRaw = loadEcoCsv("faellesskaber_scores.csv", "crime_per_1k");
  const faelleskaberAccidents = loadEcoCsv("faellesskaber_scores.csv", "traffic_accidents_ratio");
  const faelleskaberAccidentsRaw = loadEcoCsv("faellesskaber_scores.csv", "traffic_accidents_per_100k");
  const lokalsamfundLibrary = loadEcoCsv("lokalsamfund_scores.csv", "library_ratio");
  const lokalsamfundLibraryRaw = loadEcoCsv("lokalsamfund_scores.csv", "library_loans_per_cap");
  const lokalsamfundFacilities = loadEcoCsv("lokalsamfund_scores.csv", "facilities_ratio");
  const lokalsamfundFacilitiesRaw = loadEcoCsv("lokalsamfund_scores.csv", "facilities_per_10k");
  const mobilitetCommute = loadEcoCsv("mobilitet_scores.csv", "commute_ratio");
  const mobilitetCommuteRaw = loadEcoCsv("mobilitet_scores.csv", "commute_distance_km");
  const mobilitetCar = loadEcoCsv("mobilitet_scores.csv", "car_access_ratio");
  const mobilitetCarRaw = loadEcoCsv("mobilitet_scores.csv", "car_access_pct");
  const mobilitetTransport = loadEcoCsv("mobilitet_scores.csv", "public_transport_ratio");
  const mobilitetTransportRaw = loadEcoCsv("mobilitet_scores.csv", "public_transport_pct");
  const velfaerdChildren = loadEcoCsv("velfaerd_extra_scores.csv", "vulnerable_children_ratio");
  const velfaerdChildrenRaw = loadEcoCsv("velfaerd_extra_scores.csv", "vulnerable_children_pct");
  const velfaerdNeet = loadEcoCsv("velfaerd_extra_scores.csv", "neet_ratio");
  const velfaerdNeetRaw = loadEcoCsv("velfaerd_extra_scores.csv", "neet_pct");

  // Load extra social dimension data (round 2)
  const sundhedHospital = loadEcoCsv("sundhed_extra_scores.csv", "hospital_use_ratio");
  const sundhedHospitalRaw = loadEcoCsv("sundhed_extra_scores.csv", "hospital_use_pct");
  const sundhedGpDistance = loadEcoCsv("sundhed_extra_scores.csv", "gp_distance_ratio");
  const sundhedGpDistanceRaw = loadEcoCsv("sundhed_extra_scores.csv", "gp_distance_km");
  const uddannelseLow = loadEcoCsv("uddannelse_extra_scores.csv", "low_education_ratio");
  const uddannelseLowRaw = loadEcoCsv("uddannelse_extra_scores.csv", "low_education_pct");
  const boligArea = loadEcoCsv("bolig_extra_scores.csv", "housing_area_ratio");
  const boligAreaRaw = loadEcoCsv("bolig_extra_scores.csv", "housing_area_m2");
  const samskabelseMusic = loadEcoCsv("samskabelse_extra_scores.csv", "music_school_ratio");
  const samskabelseMusicRaw = loadEcoCsv("samskabelse_extra_scores.csv", "music_school_per_1k");
  const lokalClassSize = loadEcoCsv("lokalsamfund_extra_scores.csv", "class_size_ratio");
  const lokalClassSizeRaw = loadEcoCsv("lokalsamfund_extra_scores.csv", "class_size");
  const lokalDaycare = loadEcoCsv("lokalsamfund_extra_scores.csv", "daycare_ratio");
  const lokalDaycareRaw = loadEcoCsv("lokalsamfund_extra_scores.csv", "daycare_ratio_val");
  const lokalSportsSpend = loadEcoCsv("lokalsamfund_extra_scores.csv", "sports_spending_ratio");
  const lokalSportsSpendRaw = loadEcoCsv("lokalsamfund_extra_scores.csv", "sports_spending_kr");
  const lokalEduStaff = loadEcoCsv("lokalsamfund_extra_scores.csv", "educated_staff_ratio");
  const lokalEduStaffRaw = loadEcoCsv("lokalsamfund_extra_scores.csv", "educated_staff_pct");

  const data: KommuneData[] = [];
  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(",");
    const row: Record<string, string> = {};
    headers.forEach((h, idx) => {
      row[h.trim()] = (cols[idx] || "").trim();
    });

    const ratios: Record<string, number | null> = {};
    const rawValues: Record<string, number | null> = {};
    for (const ind of INDICATORS) {
      const ratioKey = `${ind.id}_ratio`;
      const rawKey = `${ind.id}_raw`;
      const ratioVal = row[ratioKey];
      const rawVal = row[rawKey];
      ratios[ind.id] = ratioVal && ratioVal !== "" ? parseFloat(ratioVal) : null;
      // Load raw value from CSV if present (added in script v4.5+)
      if (rawVal && rawVal !== "") {
        rawValues[ind.id] = parseFloat(rawVal);
      }
    }

    // Inject indicators from separate CSVs
    const kommuneKode = row["kommune_kode"] || "";

    if (democracyData[kommuneKode] !== undefined) {
      ratios["voter_turnout"] = democracyData[kommuneKode];
      rawValues["voter_turnout"] = democracyRaw[kommuneKode] ?? null;
    }
    // Fællesskaber
    if (faelleskaberSports[kommuneKode] !== undefined) {
      ratios["sports_membership"] = faelleskaberSports[kommuneKode];
      rawValues["sports_membership"] = faelleskaberSportsRaw[kommuneKode] ?? null;
    }
    if (faelleskaberCrime[kommuneKode] !== undefined) {
      ratios["crime_rate"] = faelleskaberCrime[kommuneKode];
      rawValues["crime_rate"] = faelleskaberCrimeRaw[kommuneKode] ?? null;
    }
    if (faelleskaberAccidents[kommuneKode] !== undefined) {
      ratios["traffic_accidents"] = faelleskaberAccidents[kommuneKode];
      rawValues["traffic_accidents"] = faelleskaberAccidentsRaw[kommuneKode] ?? null;
    }
    // Lokalsamfund
    if (lokalsamfundLibrary[kommuneKode] !== undefined) {
      ratios["library_use"] = lokalsamfundLibrary[kommuneKode];
      rawValues["library_use"] = lokalsamfundLibraryRaw[kommuneKode] ?? null;
    }
    if (lokalsamfundFacilities[kommuneKode] !== undefined) {
      ratios["sports_facilities"] = lokalsamfundFacilities[kommuneKode];
      rawValues["sports_facilities"] = lokalsamfundFacilitiesRaw[kommuneKode] ?? null;
    }
    // Mobilitet
    if (mobilitetCommute[kommuneKode] !== undefined) {
      ratios["commute_distance"] = mobilitetCommute[kommuneKode];
      rawValues["commute_distance"] = mobilitetCommuteRaw[kommuneKode] ?? null;
    }
    if (mobilitetCar[kommuneKode] !== undefined) {
      ratios["car_access"] = mobilitetCar[kommuneKode];
      rawValues["car_access"] = mobilitetCarRaw[kommuneKode] ?? null;
    }
    if (mobilitetTransport[kommuneKode] !== undefined) {
      ratios["public_transport"] = mobilitetTransport[kommuneKode];
      rawValues["public_transport"] = mobilitetTransportRaw[kommuneKode] ?? null;
    }
    // Velfærd (ekstra)
    if (velfaerdChildren[kommuneKode] !== undefined) {
      ratios["vulnerable_children"] = velfaerdChildren[kommuneKode];
      rawValues["vulnerable_children"] = velfaerdChildrenRaw[kommuneKode] ?? null;
    }
    if (velfaerdNeet[kommuneKode] !== undefined) {
      ratios["neet"] = velfaerdNeet[kommuneKode];
      rawValues["neet"] = velfaerdNeetRaw[kommuneKode] ?? null;
    }
    // Sundhed (ekstra)
    if (sundhedHospital[kommuneKode] !== undefined) {
      ratios["hospital_use"] = sundhedHospital[kommuneKode];
      rawValues["hospital_use"] = sundhedHospitalRaw[kommuneKode] ?? null;
    }
    if (sundhedGpDistance[kommuneKode] !== undefined) {
      ratios["gp_distance"] = sundhedGpDistance[kommuneKode];
      rawValues["gp_distance"] = sundhedGpDistanceRaw[kommuneKode] ?? null;
    }
    // Uddannelse (ekstra)
    if (uddannelseLow[kommuneKode] !== undefined) {
      ratios["low_education"] = uddannelseLow[kommuneKode];
      rawValues["low_education"] = uddannelseLowRaw[kommuneKode] ?? null;
    }
    // Bolig (ekstra)
    if (boligArea[kommuneKode] !== undefined) {
      ratios["housing_area"] = boligArea[kommuneKode];
      rawValues["housing_area"] = boligAreaRaw[kommuneKode] ?? null;
    }
    // Samskabelse (ekstra)
    if (samskabelseMusic[kommuneKode] !== undefined) {
      ratios["music_school"] = samskabelseMusic[kommuneKode];
      rawValues["music_school"] = samskabelseMusicRaw[kommuneKode] ?? null;
    }
    // Lokalsamfund (ekstra)
    if (lokalClassSize[kommuneKode] !== undefined) {
      ratios["class_size"] = lokalClassSize[kommuneKode];
      rawValues["class_size"] = lokalClassSizeRaw[kommuneKode] ?? null;
    }
    if (lokalDaycare[kommuneKode] !== undefined) {
      ratios["daycare_ratio"] = lokalDaycare[kommuneKode];
      rawValues["daycare_ratio"] = lokalDaycareRaw[kommuneKode] ?? null;
    }
    if (lokalSportsSpend[kommuneKode] !== undefined) {
      ratios["sports_spending"] = lokalSportsSpend[kommuneKode];
      rawValues["sports_spending"] = lokalSportsSpendRaw[kommuneKode] ?? null;
    }
    if (lokalEduStaff[kommuneKode] !== undefined) {
      ratios["educated_staff"] = lokalEduStaff[kommuneKode];
      rawValues["educated_staff"] = lokalEduStaffRaw[kommuneKode] ?? null;
    }
    // consumption_co2 er nu en økologisk dimension - se eco_ratios nedenfor

    // Ecological ratios
    const eco_ratios: Record<string, number | null> = {};
    const kode = row["kommune_kode"] || "";

    // TORUS miljøaspekter - data fra separate CSV-filer
    // NB: cirkularitet håndteres separat nedenfor (multi-indikator)
    const ecoSources: Record<string, Record<string, number | null>> = {
      klimapaavirkning: climateData,
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
    // Eco råværdier til visning i ScoreBars
    if (climateRawData[kode] != null)       rawValues["eco_klima_raw"]         = climateRawData[kode]!;
    if (landUseRawData[kode] != null)       rawValues["eco_areal_raw"]         = landUseRawData[kode]!;
    if (biodiversitetRawData[kode] != null) rawValues["eco_bio_raw"]           = biodiversitetRawData[kode]!;
    if (naerNitrogenRaw[kode] != null)      rawValues["eco_naer_n_raw"]        = naerNitrogenRaw[kode]!;
    if (naerPhosphorusRaw[kode] != null)    rawValues["eco_naer_p_raw"]        = naerPhosphorusRaw[kode]!;
    if (vandWastewaterRaw[kode] != null)    rawValues["eco_vand_ww_raw"]       = vandWastewaterRaw[kode]!;
    if (vandExtractionRaw[kode] != null)    rawValues["eco_vand_extr_raw"]     = vandExtractionRaw[kode]!;
    if (recyclingPctData[kode] != null)     rawValues["eco_cirkularitet_raw"]  = recyclingPctData[kode]!;
    if (wasteRawData[kode] != null)         rawValues["eco_affald_raw"]        = wasteRawData[kode]!;

    // Sub-ratios for single-indikator eco-dims (= dim-ratio)
    // Sættes EFTER eco_ratios udfyldes nedenfor

    // Forbrugsbaseret CO2 - kommunespecifikt fra cba_2023_estimate.csv (Osei-Owusu + ENS skalering)
    // Fallback til nationalt gennemsnit hvis kommunen ikke matcher
    const kommuneNavn = row["kommune_navn"] || "";
    const cbaRatio = cbaRatioByName[kommuneNavn];
    eco_ratios["forbrug_co2"] = cbaRatio !== undefined ? cbaRatio : CONSUMPTION_CO2_RATIO_FALLBACK;
    if (cbaRawByName[kommuneNavn] !== undefined) {
      rawValues["forbrug_co2"] = cbaRawByName[kommuneNavn];
    }

    // Multi-indicator eco dimensions (gennemsnit af flere indikatorer)
    // VIGTIGT: næringsstoffer, vand og forurening bruger ratio_inverse i CSV:
    //   ratio_inverse = (national_avg / kommune_val) * 100
    //   Lav score = MERE forurening = VÆRRE
    // Vi konverterer til direkte ratio: direct = 10000 / inverse
    //   Så høj forurening → score > 100 → overshoot (rød)
    //   Og lav forurening → score < 100 → inden for grænsen (grøn)
    function invertToDirectRatio(inverted: number | null): number | null {
      if (inverted === null || inverted === 0) return null;
      return parseFloat((10000 / inverted).toFixed(2));
    }

    // Multi-indikator eco-dimensioner: brug WORST-OF (max ratio) - planetary boundary-logik:
    // Hvis bare én sub-grænse er overskredet, er dimensionen overskredet. Et gennemsnit
    // ville skjule overskridelser bag bedre indikatorer.
    function worstOf(vals: (number | null)[]): number | null {
      const filtered = vals.filter((v): v is number => v !== null);
      return filtered.length > 0 ? parseFloat(Math.max(...filtered).toFixed(2)) : null;
    }

    // Næringsstoffer: kvælstof + fosfor + landbrugs-N loft
    const naerN = invertToDirectRatio(naerNitrogen[kode] ?? null);
    const naerP = invertToDirectRatio(naerPhosphorus[kode] ?? null);
    const naerLandbrug = nLandbrug[kode] ?? null;
    eco_ratios["naeringsstoffer"] = worstOf([naerN, naerP, naerLandbrug]);
    if (naerN !== null)         rawValues["eco_naer_n_ratio"]        = naerN;
    if (naerP !== null)         rawValues["eco_naer_p_ratio"]        = naerP;
    if (naerLandbrug !== null)  rawValues["eco_naer_landbrug_ratio"] = naerLandbrug;

    // Vand: spildevand + vandindvinding pr. capita
    const vandWW = invertToDirectRatio(vandWastewater[kode] ?? null);
    const vandEx = invertToDirectRatio(vandExtraction[kode] ?? null);
    eco_ratios["vand"] = worstOf([vandWW, vandEx]);
    if (vandWW !== null) rawValues["eco_vand_ww_ratio"]   = vandWW;
    if (vandEx !== null) rawValues["eco_vand_extr_ratio"] = vandEx;

    // Cirkularitet: genanvendelse + affald pr. capita
    const recyclingPct = recyclingPctData[kode] ?? null;
    const recyclingEco = recyclingPct !== null && recyclingPct > 0
      ? parseFloat(((65 / recyclingPct) * 100).toFixed(2))
      : null;
    const wasteInverted = wasteData[kode] ?? null;
    const wasteDirect = invertToDirectRatio(wasteInverted);
    eco_ratios["cirkularitet"] = worstOf([recyclingEco, wasteDirect]);
    if (recyclingEco !== null) rawValues["eco_cirkularitet_ratio"] = recyclingEco;
    if (wasteDirect !== null)  rawValues["eco_affald_ratio"]       = wasteDirect;

    // Forurening (novel entities): ingen pålidelig kommunal datakilde endnu
    eco_ratios["forurening"] = null;

    // Luftkvalitet: NO2 + PM2.5 fra DCE/AU UBM-model 2023 via Miljøportal WFS
    // Ratio = (koncentration / WHO 2021-grænse) × 100. Over 100 = over WHO-grænsen.
    // WHO 2021: NO2 = 10 µg/m³, PM2.5 = 5 µg/m³ (årsgennemsnit)
    const luftNo2 = luftNo2Data[kode] ?? null;
    const luftPm25 = luftPm25Data[kode] ?? null;
    eco_ratios["luftkvalitet"] = worstOf([luftNo2, luftPm25]);
    if (luftNo2 !== null)  rawValues["luftkvalitet_no2_ratio"]  = luftNo2;
    if (luftPm25 !== null) rawValues["luftkvalitet_pm25_ratio"] = luftPm25;
    // Gem µg/m³ råværdier (ikke ratio) til sub-indikator visning
    const luftNo2Raw  = luftNo2RawData[kode]  ?? null;
    const luftPm25Raw = luftPm25RawData[kode] ?? null;
    if (luftNo2Raw  !== null) rawValues["luftkvalitet_no2"]  = luftNo2Raw;
    if (luftPm25Raw !== null) rawValues["luftkvalitet_pm25"] = luftPm25Raw;

    // Sub-ratios for single-indikator dims = dim-ratio (så sub-bar matcher hovedbar)
    if (eco_ratios["klimapaavirkning"] != null) rawValues["klimapaavirkning_self"] = eco_ratios["klimapaavirkning"]!;
    if (eco_ratios["arealanvendelse"]  != null) rawValues["arealanvendelse_self"]  = eco_ratios["arealanvendelse"]!;
    if (eco_ratios["biodiversitet"]    != null) rawValues["biodiversitet_self"]    = eco_ratios["biodiversitet"]!;
    if (eco_ratios["forbrug_co2"]      != null) rawValues["forbrug_co2_self"]      = eco_ratios["forbrug_co2"]!;

    const socialAvg = row["social_avg"];
    const overallAvg = row["overall_avg"];

    data.push({
      kommune_kode: kode,
      kommune_navn: row["kommune_navn"] || "",
      ratios,
      top10_ratios: {}, // udfyldes af computeTop10Ratios nedenfor
      eco_ratios,
      rawValues,
      social_avg: socialAvg && socialAvg !== "" ? parseFloat(socialAvg) : null,
      overall_avg:
        overallAvg && overallAvg !== "" ? parseFloat(overallAvg) : null,
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
  return loadData().filter((k) => k.kommune_kode !== "000");
}
