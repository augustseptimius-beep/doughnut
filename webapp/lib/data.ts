import fs from "fs";
import path from "path";

// Re-export shared types and constants for server components
export {
  INDICATORS,
  scoreColor,
  scoreBgColor,
  scoreBarColor,
} from "./shared";
export type { Indicator, KommuneData } from "./shared";

import { INDICATORS, type KommuneData } from "./shared";

let cachedData: KommuneData[] | null = null;

export function loadData(): KommuneData[] {
  if (cachedData) return cachedData;

  const csvPath = path.join(process.cwd(), "..", "doughnut_scores.csv");
  const raw = fs.readFileSync(csvPath, "utf-8");
  const lines = raw.trim().split("\n");
  const headers = lines[0].split(",");

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

    const socialAvg = row["social_avg"];
    const overallAvg = row["overall_avg"];

    data.push({
      kommune_kode: row["kommune_kode"] || "",
      kommune_navn: row["kommune_navn"] || "",
      ratios,
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
