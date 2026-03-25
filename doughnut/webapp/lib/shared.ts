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

  // ── Økologiske indikatorer (Klimaregnskabet + Energi Data Service) ──
  {
    id: "co2_per_capita",
    name: "CO2-udledning pr. indb. (ton CO2e)",
    table: "klimaregnskabet/emissions",
    source: "https://klimaregnskabet.dk",
    category: "ecological",
    inverse: true,   // lavere er bedre
  },
  {
    id: "co2_energy",
    name: "CO2 fra energisektoren pr. indb.",
    table: "klimaregnskabet/emissions",
    source: "https://klimaregnskabet.dk",
    category: "ecological",
    inverse: true,
  },
  {
    id: "co2_transport",
    name: "CO2 fra transport pr. indb.",
    table: "klimaregnskabet/emissions",
    source: "https://klimaregnskabet.dk",
    category: "ecological",
    inverse: true,
  },
  {
    id: "ve_share",
    name: "VE-andel af endeligt energiforbrug (%)",
    table: "klimaregnskabet/emissions",
    source: "https://klimaregnskabet.dk",
    category: "ecological",
    inverse: false,  // højere er bedre
  },
  {
    id: "ve_capacity_mw",
    name: "Installeret VE-kapacitet (MW)",
    table: "energidataservice/CapacityPerMunicipality",
    source: "https://api.energidataservice.dk/dataset/CapacityPerMunicipality",
    category: "ecological",
    inverse: false,
  },
];

export interface KommuneData {
  kommune_kode: string;
  kommune_navn: string;
  ratios: Record<string, number | null>;
  social_avg: number | null;
  ecological_avg: number | null;
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
