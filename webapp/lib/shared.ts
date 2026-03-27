export interface Indicator {
  id: string;
  name: string;
  table: string;
  source: string;
  category: "social" | "ecological";
  inverse: boolean;
}

export const INDICATORS: Indicator[] = [
  {
    id: "life_expectancy",
    name: "Middellevetid",
    table: "HISBK",
    source: "https://www.statistikbanken.dk/HISBK",
    category: "social",
    inverse: false,
  },
  {
    id: "education",
    name: "Kompetencegivende uddannelse (30-34 år)",
    table: "HFUDD10",
    source: "https://www.statistikbanken.dk/HFUDD10",
    category: "social",
    inverse: false,
  },
  {
    id: "disposable_income",
    name: "Disponibel indkomst",
    table: "INDKP101",
    source: "https://www.statistikbanken.dk/INDKP101",
    category: "social",
    inverse: false,
  },
  {
    id: "employment",
    name: "Beskæftigelsesfrekvens",
    table: "RAS200",
    source: "https://www.statistikbanken.dk/RAS200",
    category: "social",
    inverse: false,
  },
  {
    id: "child_poverty",
    name: "Børnefattigdom (Gini-proxy)",
    table: "IFOR41",
    source: "https://www.statistikbanken.dk/IFOR41",
    category: "social",
    inverse: true,
  },
  {
    id: "gini",
    name: "Gini-koefficient",
    table: "IFOR41",
    source: "https://www.statistikbanken.dk/IFOR41",
    category: "social",
    inverse: true,
  },
  {
    id: "vacant_housing",
    name: "Ubeboede boliger",
    table: "BOL101",
    source: "https://www.statistikbanken.dk/BOL101",
    category: "social",
    inverse: true,
  },
  {
    id: "voter_turnout",
    name: "Stemmedeltagelse kommunalvalg",
    table: "LABY08",
    source: "https://www.statistikbanken.dk/LABY08",
    category: "social",
    inverse: false,
  },
];

// --- SOCIAL CATEGORIES ---

export interface SocialCategory {
  id: string;
  name: string;
  indicatorIds: string[];
}

export const SOCIAL_CATEGORIES: SocialCategory[] = [
  { id: "health", name: "Sundhed", indicatorIds: ["life_expectancy"] },
  { id: "education_cat", name: "Uddannelse", indicatorIds: ["education"] },
  {
    id: "income_work",
    name: "Indkomst & arbejde",
    indicatorIds: ["disposable_income", "employment", "child_poverty"],
  },
  { id: "social_equality", name: "Social lighed", indicatorIds: ["gini"] },
  {
    id: "housing_infra",
    name: "Bolig & infrastruktur",
    indicatorIds: ["vacant_housing"],
  },
  { id: "democracy", name: "Demokrati & fællesskab", indicatorIds: ["voter_turnout"] },
];

// --- ECOLOGICAL CEILING ---

export interface EcologicalDimension {
  id: string;
  name: string;
  shortName: string; // Abbreviated label for SVG ring
  source?: string;
  unit?: string;
  boundary?: string; // Description of the planetary boundary
}

export const ECOLOGICAL_DIMENSIONS: EcologicalDimension[] = [
  {
    id: "climate_territorial",
    name: "Territorial CO2 pr. indbygger",
    shortName: "KLIMA",
    source: "https://klimaregnskabet.dk",
    unit: "ton CO₂e/person",
    boundary: "3 ton CO₂e/person/år (Paris-budget, territorial)",
  },
  {
    id: "water",
    name: "Vandmiljø",
    shortName: "VAND",
  },
  {
    id: "biodiversity",
    name: "Biodiversitet",
    shortName: "BIO",
  },
  {
    id: "land_use",
    name: "Arealanvendelse",
    shortName: "AREAL",
    source: "DST AREALDK2 + ARE207",
    unit: "% naturområder",
    boundary: "30% naturområder (EU Biodiversity Strategy 2030)",
  },
  {
    id: "waste_resources",
    name: "Affald & ressourcer",
    shortName: "AFFALD",
    source: "Miljøstyrelsen, Affaldsstatistik 2023",
    unit: "% reelt genanvendt",
    boundary: "65% genanvendelse (EU-målsætning 2035)",
  },
];

// --- CATEGORY SCORE COMPUTATION ---

export interface CategoryScore {
  categoryId: string;
  categoryName: string;
  score: number | null; // 0-100 scale (ratio score), null if no data
  indicatorCount: number;
  hasData: boolean;
  indicators: {
    indicator: Indicator;
    score: number | null;
  }[];
}

export function computeCategoryScores(
  ratios: Record<string, number | null>
): CategoryScore[] {
  return SOCIAL_CATEGORIES.map((cat) => {
    const indicators = cat.indicatorIds.map((id) => ({
      indicator: INDICATORS.find((ind) => ind.id === id)!,
      score: ratios[id] ?? null,
    }));

    const validScores = indicators
      .map((i) => i.score)
      .filter((s): s is number => s !== null);

    const score =
      validScores.length > 0
        ? validScores.reduce((a, b) => a + b, 0) / validScores.length
        : null;

    return {
      categoryId: cat.id,
      categoryName: cat.name,
      score,
      indicatorCount: cat.indicatorIds.length,
      hasData: validScores.length > 0,
      indicators,
    };
  });
}

export function computeOverallFromCategories(
  categoryScores: CategoryScore[]
): number | null {
  const withData = categoryScores.filter((c) => c.hasData && c.score !== null);
  if (withData.length === 0) return null;
  return withData.reduce((a, b) => a + b.score!, 0) / withData.length;
}

// --- HELPERS ---

export interface KommuneData {
  kommune_kode: string;
  kommune_navn: string;
  ratios: Record<string, number | null>;
  eco_ratios: Record<string, number | null>; // ecological dimension ratios
  social_avg: number | null;
  overall_avg: number | null;
}

export function scoreColor(score: number | null): string {
  if (score === null) return "text-gray-400";
  if (score >= 100) return "text-emerald-600";
  if (score >= 85) return "text-amber-500";
  return "text-red-500";
}

export function scoreBgColor(score: number | null): string {
  if (score === null) return "bg-gray-100";
  if (score >= 100) return "bg-emerald-50";
  if (score >= 85) return "bg-amber-50";
  return "bg-red-50";
}

export function scoreBarColor(score: number | null): string {
  if (score === null) return "bg-gray-300";
  if (score >= 100) return "bg-emerald-500";
  if (score >= 85) return "bg-amber-400";
  return "bg-red-400";
}
