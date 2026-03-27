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
    name: "Børnefattigdom",
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
  {
    id: "consumption_co2",
    name: "Forbrugsbaseret CO₂ (nationalt gennemsnit)",
    table: "CONCITO/Energistyrelsen",
    source: "https://concito.dk",
    category: "social",
    inverse: true, // lavere er bedre
  },
];

// --- SOCIAL CATEGORIES (TORUS trivselsaspekter) ---

export interface SocialCategory {
  id: string;
  name: string;
  description?: string;
  indicatorIds: string[];
}

export const SOCIAL_CATEGORIES: SocialCategory[] = [
  {
    id: "sundhed",
    name: "Sundhed",
    description: "Borgernes fysiske og mentale sundhed, herunder livslængde, sygelighed og adgang til sundhedsydelser.",
    indicatorIds: ["life_expectancy"],
  },
  {
    id: "uddannelse",
    name: "Uddannelse",
    description: "Adgang til og gennemførelse af uddannelse for alle aldersgrupper - grundlag for personlig udvikling og samfundsdeltagelse.",
    indicatorIds: ["education"],
  },
  {
    id: "velfaerd",
    name: "Velfærd",
    description: "Materiel levevilkår, indkomst, beskæftigelse og social sikring - de grundlæggende betingelser for et godt liv.",
    indicatorIds: ["disposable_income", "employment", "child_poverty", "gini"],
  },
  {
    id: "bolig",
    name: "Bolig",
    description: "Adgang til gode, sunde og bæredygtige boliger i trygge nærmiljøer.",
    indicatorIds: ["vacant_housing"],
  },
  {
    id: "samskabelse",
    name: "Samskabelse & demokrati",
    description: "Borgernes deltagelse i demokrati og lokalsamfund, tillid til institutioner og civilt engagement.",
    indicatorIds: ["voter_turnout"],
  },
  {
    id: "paavirkninger_udenfor",
    name: "Påvirkninger udenfor kommunen",
    description: "Kommunens forbrugsbaserede klimaaftryk - de udledninger der sker uden for kommunens grænser som følge af borgernes forbrug.",
    indicatorIds: ["consumption_co2"],
  },
  {
    id: "faellesskaber",
    name: "Fællesskaber",
    description: "Sociale netværk, fællesskaber og tilhørsforhold - modvirker ensomhed og styrker sammenhængskraft.",
    indicatorIds: [],
  },
  {
    id: "lokalsamfund",
    name: "Lokalsamfund",
    description: "Levende lokalsamfund med adgang til basale services, kultur og rekreative muligheder.",
    indicatorIds: [],
  },
  {
    id: "mobilitet",
    name: "Mobilitet",
    description: "Adgang til bæredygtig og effektiv transport for alle borgere uanset geografi og økonomi.",
    indicatorIds: [],
  },
  {
    id: "klimatilpasning",
    name: "Klimatilpasning",
    description: "Kommunens robusthed over for klimaforandringer: oversvømmelse, hedebølger, tørke og ekstremvejr.",
    indicatorIds: [],
  },
];

// --- ECOLOGICAL CEILING (TORUS miljøaspekter) ---

export interface EcologicalDimension {
  id: string;
  name: string;
  shortName: string; // Abbreviated label for SVG ring
  description?: string;
  source?: string;
  unit?: string;
  boundary?: string; // Description of the planetary boundary
}

export const ECOLOGICAL_DIMENSIONS: EcologicalDimension[] = [
  {
    id: "klimapaavirkning",
    name: "Klimapåvirkning",
    shortName: "KLIMA",
    description: "Territoriale drivhusgasudledninger fra energi, transport, landbrug og industri inden for kommunens grænser.",
    source: "https://klimaregnskabet.dk",
    unit: "ton CO₂e/person",
    boundary: "3 ton CO₂e/person/år (Paris-budget, territorial)",
  },
  {
    id: "forurening",
    name: "Forurening (kemi & plastik)",
    shortName: "FORUR",
    description: "Udledning af skadelige kemikalier, mikroplast og giftstoffer til jord, vand og luft.",
  },
  {
    id: "luftkvalitet",
    name: "Luftkvalitet",
    shortName: "LUFT",
    description: "Koncentration af skadelige partikler og gasser (PM2.5, NOx, ozon) der påvirker folkesundhed og natur.",
  },
  {
    id: "cirkularitet",
    name: "Cirkularitet (materialer)",
    shortName: "CIR",
    description: "Genanvendelse og ressourceeffektivitet - andelen af affald der reelt genanvendes frem for deponeres eller forbrændes.",
    source: "https://mst.dk/erhverv/groen-produktion-og-affald/affald-og-genanvendelse/affaldshaandtering/affaldsdata-og-affaldsdatasystemet/find-affaldsstatistikker-og-kortlaegning",
    unit: "% reelt genanvendt",
    boundary: "65% genanvendelse (EU-målsætning 2035)",
  },
  {
    id: "naeringsstoffer",
    name: "Næringsstoffer",
    shortName: "NÆR",
    description: "Næringsstofbelastning fra landbrug og spildevand - kvælstof og fosfor der forurener vandmiljøet.",
  },
  {
    id: "vand",
    name: "Vand",
    shortName: "VAND",
    description: "Kvalitet og tilgængelighed af ferskvand - grundvand, vandløb, søer og kystvande.",
  },
  {
    id: "arealanvendelse",
    name: "Arealanvendelse",
    shortName: "AREAL",
    description: "Andel af kommunens areal der er natur, skov og grønne arealer - modvirker tab af levesteder og fremmer biodiversitet.",
    source: "DST AREALDK2 + ARE207",
    unit: "% naturområder",
    boundary: "30% naturområder (EU Biodiversitetsstrategi 2030)",
  },
  {
    id: "biodiversitet",
    name: "Biodiversitet",
    shortName: "BIO",
    description: "Tilstand og udvikling for lokale bestande af planter, dyr og insekter - indikatorer for naturkvalitet.",
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
