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
  // --- Fællesskaber ---
  {
    id: "sports_membership",
    name: "Idrætsmedlemskab (andel af befolkningen)",
    table: "IDRAKT02",
    source: "https://www.statistikbanken.dk/IDRAKT02",
    category: "social",
    inverse: false,
  },
  {
    id: "crime_rate",
    name: "Anmeldte forbrydelser pr. 1.000 indb.",
    table: "STRAF11",
    source: "https://www.statistikbanken.dk/STRAF11",
    category: "social",
    inverse: true,
  },
  // --- Lokalsamfund ---
  {
    id: "library_use",
    name: "Biblioteksudlån pr. indbygger",
    table: "BIB1",
    source: "https://www.statistikbanken.dk/BIB1",
    category: "social",
    inverse: false,
  },
  {
    id: "sports_facilities",
    name: "Idrætsfaciliteter pr. 10.000 indb.",
    table: "IDRFAC01",
    source: "https://www.statistikbanken.dk/IDRFAC01",
    category: "social",
    inverse: false,
  },
  // --- Mobilitet ---
  {
    id: "commute_distance",
    name: "Gennemsnitlig pendlingsafstand",
    table: "AFSTB4",
    source: "https://www.statistikbanken.dk/AFSTB4",
    category: "social",
    inverse: true,
  },
  {
    id: "car_access",
    name: "Familier med bilrådighed",
    table: "BIL800",
    source: "https://www.statistikbanken.dk/BIL800",
    category: "social",
    inverse: false,
  },
  // --- Velfærd (ekstra) ---
  {
    id: "vulnerable_children",
    name: "Udsatte børn og unge (andel 0-22 år)",
    table: "BU43",
    source: "https://www.statistikbanken.dk/BU43",
    category: "social",
    inverse: true,
  },
  {
    id: "neet",
    name: "Unge uden for uddannelse/beskæftigelse (NEET)",
    table: "NEET1",
    source: "https://www.statistikbanken.dk/NEET1",
    category: "social",
    inverse: true,
  },
  // --- Sundhed (ekstra) ---
  {
    id: "hospital_use",
    name: "Sygehusbenyttelse (andel med ophold)",
    table: "SBR01",
    source: "https://www.statistikbanken.dk/SBR01",
    category: "social",
    inverse: true,
  },
  // --- Uddannelse (ekstra) ---
  {
    id: "low_education",
    name: "Unge 25-29 med kun grundskole",
    table: "HFUDD11",
    source: "https://www.statistikbanken.dk/HFUDD11",
    category: "social",
    inverse: true,
  },
  // --- Bolig (ekstra) ---
  {
    id: "housing_area",
    name: "Boligareal pr. person (m²)",
    table: "BOL106",
    source: "https://www.statistikbanken.dk/BOL106",
    category: "social",
    inverse: false,
  },
  // --- Samskabelse (ekstra) ---
  {
    id: "music_school",
    name: "Musikskoleelever pr. 1.000 indb.",
    table: "SKOLM02B",
    source: "https://www.statistikbanken.dk/SKOLM02B",
    category: "social",
    inverse: false,
  },
  // --- Lokalsamfund (ekstra) ---
  {
    id: "class_size",
    name: "Klassekvotient grundskole",
    table: "KVOTIEN",
    source: "https://www.statistikbanken.dk/KVOTIEN",
    category: "social",
    inverse: true,
  },
  {
    id: "daycare_ratio",
    name: "Normering daginstitution (3-5 år)",
    table: "BOERN8",
    source: "https://www.statistikbanken.dk/BOERN8",
    category: "social",
    inverse: true,
  },
  {
    id: "sports_spending",
    name: "Kommunale idrætsudgifter pr. indb.",
    table: "IDRFIN02",
    source: "https://www.statistikbanken.dk/IDRFIN02",
    category: "social",
    inverse: false,
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
    indicatorIds: ["life_expectancy", "hospital_use"],
  },
  {
    id: "uddannelse",
    name: "Uddannelse",
    description: "Adgang til og gennemførelse af uddannelse for alle aldersgrupper - grundlag for personlig udvikling og samfundsdeltagelse.",
    indicatorIds: ["education", "low_education"],
  },
  {
    id: "velfaerd",
    name: "Velfærd",
    description: "Materiel levevilkår, indkomst, beskæftigelse og social sikring - de grundlæggende betingelser for et godt liv.",
    indicatorIds: ["disposable_income", "employment", "child_poverty", "gini", "vulnerable_children", "neet"],
  },
  {
    id: "bolig",
    name: "Bolig",
    description: "Adgang til gode, sunde og bæredygtige boliger i trygge nærmiljøer.",
    indicatorIds: ["vacant_housing", "housing_area"],
  },
  {
    id: "samskabelse",
    name: "Samskabelse & demokrati",
    description: "Borgernes deltagelse i demokrati og lokalsamfund, tillid til institutioner og civilt engagement.",
    indicatorIds: ["voter_turnout", "music_school"],
  },
  {
    id: "faellesskaber",
    name: "Fællesskaber",
    description: "Sociale netværk, fællesskaber og tilhørsforhold - modvirker ensomhed og styrker sammenhængskraft.",
    indicatorIds: ["sports_membership", "crime_rate"],
  },
  {
    id: "lokalsamfund",
    name: "Lokalsamfund",
    description: "Levende lokalsamfund med adgang til basale services, kultur og rekreative muligheder.",
    indicatorIds: ["library_use", "sports_facilities", "class_size", "daycare_ratio", "sports_spending"],
  },
  {
    id: "mobilitet",
    name: "Mobilitet",
    description: "Adgang til bæredygtig og effektiv transport for alle borgere uanset geografi og økonomi.",
    indicatorIds: ["commute_distance", "car_access"],
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
    description: "Husholdningsaffald pr. indbygger som proxy for materiel forurening - mindre affald pr. person indikerer lavere miljøbelastning.",
    source: "https://statbank.dk/LABY25",
    unit: "kg affald/person",
    boundary: "Landsgennemsnittet som reference (inverteret - lavere er bedre)",
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
    description: "Udledning af kvælstof og fosfor til vandmiljøet via spildevand - overgødskning der forårsager iltsvind og algeopblomstring.",
    source: "https://statbank.dk/VANDUD",
    unit: "ton N + ton P pr. 1.000 indb.",
    boundary: "Landsgennemsnittet som reference (inverteret - lavere udledning er bedre)",
  },
  {
    id: "vand",
    name: "Vand",
    shortName: "VAND",
    description: "Pres på vandressourcer målt via spildevandsudledning og vandindvinding pr. indbygger - højere pres indikerer større belastning af vandmiljøet.",
    source: "https://statbank.dk/VANDUD + https://statbank.dk/VANDIND",
    unit: "m³ spildevand + mio. m³ indvinding pr. 1.000 indb.",
    boundary: "Landsgennemsnittet som reference (inverteret - lavere pres er bedre)",
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
    source: "https://arealdata.miljoeportal.dk",
    unit: "% areal med bioscore ≥ 8",
    boundary: "30% af kommunens areal med væsentlige naturværdier (30x30-målet)",
  },
  {
    id: "forbrug_co2",
    name: "Forbrugsbaseret CO₂",
    shortName: "FORBRUG",
    description: "Kommunens forbrugsbaserede klimaaftryk - udledninger der sker uden for kommunens grænser som følge af borgernes forbrug.",
    source: "https://concito.dk",
    unit: "ton CO₂e/person",
    boundary: "3 ton CO₂e/person/år (Paris-budget, forbrugsbaseret)",
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
