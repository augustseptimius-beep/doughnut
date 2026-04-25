// --- DOUGHNUT-ÅR KONFIGURATION ---
// "Doughnut-år" = den edition af modellen. Data-år = det seneste helårsdata.
// Regel: en 2024-Doughnut bruger seneste tilgængelige helårsdata (typisk 2023-tal).
// Indikatorer med særlige år (f.eks. kommunalvalg 2021) er markeret eksplicit.
export const DOUGHNUT_EDITION_YEAR = "2024";
export const DOUGHNUT_DEFAULT_DATA_YEAR = "2023";

export type BaselineLevel = 1 | 2 | 3;
// Niveau 1: Absolutte biofysiske/juridiske grænser (WHO, EU-direktiver)
// Niveau 2: Nationale politiske mål (lovmål, regeringsmål)
// Niveau 3: Landsgennemsnit (default når ingen absolut grænse findes)

export interface Indicator {
  id: string;
  name: string;
  table: string;
  source: string;
  category: "social" | "ecological";
  inverse: boolean;
  dataYear?: string;          // Årstal for seneste data, f.eks. "2023" eller "2021"
  baselineLevel?: BaselineLevel; // Hierarki-niveau for baseline
  absoluteTarget?: string;    // Beskrivelse af absolut mål, f.eks. "95% (nationalt mål)"
  rawUnit?: string;           // Enhed for råværdi, f.eks. "pr. 1.000 indb.", "%", "km"
}

export const INDICATORS: Indicator[] = [
  {
    id: "life_expectancy",
    name: "Middellevetid",
    table: "HISBK",
    source: "https://www.statistikbanken.dk/HISBK",
    category: "social",
    inverse: false,
    dataYear: "2023",
    baselineLevel: 3,
    rawUnit: "år",
  },
  {
    id: "education",
    name: "Kompetencegivende uddannelse (30-34 år)",
    table: "HFUDD10",
    source: "https://www.statistikbanken.dk/HFUDD10",
    category: "social",
    inverse: false,
    dataYear: "2023",
    baselineLevel: 2,
    absoluteTarget: "95% (nationalt uddannelsesmål)",
    rawUnit: "%",
  },
  {
    id: "disposable_income",
    name: "Disponibel indkomst",
    table: "INDKP101",
    source: "https://www.statistikbanken.dk/INDKP101",
    category: "social",
    inverse: false,
    dataYear: "2022",
    baselineLevel: 3,
    rawUnit: "kr./indb.",
  },
  {
    id: "employment",
    name: "Beskæftigelsesfrekvens",
    table: "RAS200",
    source: "https://www.statistikbanken.dk/RAS200",
    category: "social",
    inverse: false,
    dataYear: "2023",
    baselineLevel: 3,
    rawUnit: "%",
  },
  {
    id: "child_poverty",
    name: "Børnefattigdom (0-17 år)",
    table: "LABY07",
    source: "https://www.statistikbanken.dk/LABY07",
    category: "social",
    inverse: true,
    dataYear: "2022",
    baselineLevel: 3,
    rawUnit: "%",
  },
  {
    id: "gini",
    name: "Gini-koefficient",
    table: "IFOR41",
    source: "https://www.statistikbanken.dk/IFOR41",
    category: "social",
    inverse: true,
    dataYear: "2022",
    baselineLevel: 3,
    rawUnit: "point",
  },
  {
    id: "low_income",
    name: "Andel i lavindkomstgruppe",
    table: "LABY07",
    source: "https://www.statistikbanken.dk/LABY07",
    category: "social",
    inverse: true,
    dataYear: "2022",
    baselineLevel: 3,
    rawUnit: "%",
  },
  {
    id: "vacant_housing",
    name: "Ubeboede boliger",
    table: "BOL101",
    source: "https://www.statistikbanken.dk/BOL101",
    category: "social",
    inverse: true,
    dataYear: "2023",
    baselineLevel: 3,
    rawUnit: "%",
  },
  {
    id: "voter_turnout",
    name: "Stemmedeltagelse kommunalvalg",
    table: "KVBPCT",
    source: "https://www.statistikbanken.dk/KVBPCT",
    category: "social",
    inverse: false,
    dataYear: "2021",  // Kommunalvalg afholdes hvert 4. år — næste: 2025
    baselineLevel: 3,
    rawUnit: "%",
  },
  // --- Fællesskaber ---
  {
    id: "sports_membership",
    name: "Idrætsmedlemskab (andel af befolkningen)",
    table: "IDRAKT02",
    source: "https://www.statistikbanken.dk/IDRAKT02",
    category: "social",
    inverse: false,
    dataYear: "2022",
    baselineLevel: 3,
    rawUnit: "%",
  },
  {
    id: "crime_rate",
    name: "Anmeldte forbrydelser pr. 1.000 indb.",
    table: "STRAF11",
    source: "https://www.statistikbanken.dk/STRAF11",
    category: "social",
    inverse: true,
    dataYear: "2024",
    baselineLevel: 3,
    rawUnit: "pr. 1.000 indb.",
  },
  {
    id: "traffic_accidents",
    name: "Trafikulykker (tilskadekomne pr. 100.000 indb.)",
    table: "UHELDK1",
    source: "https://www.statistikbanken.dk/UHELDK1",
    category: "social",
    inverse: true,
    dataYear: "2024",
    baselineLevel: 3,
    rawUnit: "pr. 100.000 indb.",
  },
  // --- Lokalsamfund ---
  {
    id: "library_use",
    name: "Biblioteksudlån pr. indbygger",
    table: "BIB1",
    source: "https://www.statistikbanken.dk/BIB1",
    category: "social",
    inverse: false,
    dataYear: "2023",
    baselineLevel: 3,
    rawUnit: "udlån/indb.",
  },
  {
    id: "sports_facilities",
    name: "Idrætsfaciliteter pr. 10.000 indb.",
    table: "IDRFAC01",
    source: "https://www.statistikbanken.dk/IDRFAC01",
    category: "social",
    inverse: false,
    dataYear: "2022",
    baselineLevel: 3,
    rawUnit: "pr. 10.000 indb.",
  },
  // --- Mobilitet ---
  {
    id: "commute_distance",
    name: "Gennemsnitlig pendlingsafstand",
    table: "AFSTB4",
    source: "https://www.statistikbanken.dk/AFSTB4",
    category: "social",
    inverse: true,
    dataYear: "2023",
    baselineLevel: 3,
    rawUnit: "km",
  },
  // car_access (familier med bilrådighed) er fjernet 2026 - i en doughnut/bæredygtighedsramme
  // er "flere biler = bedre" konceptuelt skævt. Indikatoren gav landdistrikter en kunstig høj
  // mobilitets-score som kompenserede for dårlig kollektiv transport. Råværdier og CSV-data
  // er bevaret i mobilitet_scores.csv så indikatoren kan genaktiveres hvis logikken revurderes.
  {
    id: "public_transport",
    name: "God adgang til offentlig transport",
    table: "LABY49",
    source: "https://www.statistikbanken.dk/LABY49",
    category: "social",
    inverse: false,
    dataYear: "2025",
    baselineLevel: 3,
    rawUnit: "%",
  },
  // --- Velfærd (ekstra) ---
  {
    id: "vulnerable_children",
    name: "Udsatte børn og unge (andel 0-22 år)",
    table: "BU43",
    source: "https://www.statistikbanken.dk/BU43",
    category: "social",
    inverse: true,
    dataYear: "2022",
    baselineLevel: 3,
    rawUnit: "%",
  },
  {
    id: "neet",
    name: "Unge uden for uddannelse/beskæftigelse (NEET)",
    table: "NEET1",
    source: "https://www.statistikbanken.dk/NEET1",
    category: "social",
    inverse: true,
    dataYear: "2022",
    baselineLevel: 3,
    rawUnit: "%",
  },
  // --- Sundhed (ekstra) ---
  {
    id: "hospital_use",
    name: "Sygehusbenyttelse (andel med ophold)",
    table: "SBR01",
    source: "https://www.statistikbanken.dk/SBR01",
    category: "social",
    inverse: true,
    dataYear: "2023",
    baselineLevel: 3,
    rawUnit: "%",
  },
  {
    id: "gp_distance",
    name: "Afstand til praktiserende læge",
    table: "SUNDAF01",
    source: "https://www.statistikbanken.dk/SUNDAF01",
    category: "social",
    inverse: true,
    dataYear: "2024",
    baselineLevel: 3,
    rawUnit: "km",
  },
  // --- Uddannelse (ekstra) ---
  {
    id: "low_education",
    name: "Unge 25-29 med kun grundskole",
    table: "HFUDD11",
    source: "https://www.statistikbanken.dk/HFUDD11",
    category: "social",
    inverse: true,
    dataYear: "2023",
    baselineLevel: 3,
    rawUnit: "%",
  },
  // --- Bolig (ekstra) ---
  {
    id: "housing_area",
    name: "Boligareal pr. person (m²)",
    table: "BOL106",
    source: "https://www.statistikbanken.dk/BOL106",
    category: "social",
    inverse: false,
    dataYear: "2023",
    baselineLevel: 3,
    rawUnit: "m²",
  },
  // --- Kultur & fritid ---
  {
    id: "music_school",
    name: "Musikskoleelever pr. 1.000 indb.",
    table: "SKOLM02B",
    source: "https://www.statistikbanken.dk/SKOLM02B",
    category: "social",
    inverse: false,
    dataYear: "2022",
    baselineLevel: 3,
    rawUnit: "pr. 1.000 indb.",
  },
  {
    id: "kultur_spending",
    name: "Kommunale kulturudgifter pr. indb. (kr.)",
    table: "REGK31",
    source: "https://www.statistikbanken.dk/REGK31",
    category: "social",
    inverse: false,
    dataYear: "2023",
    baselineLevel: 3,
    rawUnit: "kr./indb.",
  },
  {
    id: "civil_society",
    name: "Udgifter til frivillige foreninger pr. indb. (kr.)",
    table: "REGK31",
    source: "https://www.statistikbanken.dk/REGK31",
    category: "social",
    inverse: false,
    dataYear: "2023",
    baselineLevel: 3,
    rawUnit: "kr./indb.",
  },
  // --- Lokalsamfund (ekstra) ---
  {
    id: "class_size",
    name: "Klassekvotient grundskole",
    table: "KVOTIEN",
    source: "https://www.statistikbanken.dk/KVOTIEN",
    category: "social",
    inverse: true,
    dataYear: "2023",
    baselineLevel: 3,
    rawUnit: "elever/klasse",
  },
  {
    id: "daycare_ratio",
    name: "Normering daginstitution (3-5 år)",
    table: "BOERN8",
    source: "https://www.statistikbanken.dk/BOERN8",
    category: "social",
    inverse: true,
    dataYear: "2022",
    baselineLevel: 3,
    rawUnit: "børn/voksen",
  },
  {
    id: "sports_spending",
    name: "Kommunale idrætsudgifter pr. indb.",
    table: "IDRFIN02",
    source: "https://www.statistikbanken.dk/IDRFIN02",
    category: "social",
    inverse: false,
    dataYear: "2022",
    baselineLevel: 3,
    rawUnit: "kr./indb.",
  },
  {
    id: "educated_staff",
    name: "Uddannede pædagoger i daginstitutioner",
    table: "BOERN1",
    source: "https://www.statistikbanken.dk/BOERN1",
    category: "social",
    inverse: false,
    dataYear: "2024",
    baselineLevel: 3,
    rawUnit: "%",
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
    indicatorIds: ["life_expectancy", "hospital_use", "gp_distance"],
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
    indicatorIds: ["disposable_income", "employment", "child_poverty", "gini", "low_income", "vulnerable_children", "neet"],
  },
  {
    id: "bolig",
    name: "Bolig",
    description: "Adgang til gode, sunde og bæredygtige boliger i trygge nærmiljøer.",
    indicatorIds: ["vacant_housing", "housing_area"],
  },
  {
    id: "demokrati",
    name: "Demokrati",
    description: "Borgernes deltagelse i det formelle demokrati og kommunalpolitik. Valgdeltagelse er det mest direkte mål for demokratisk engagement på lokalt niveau.",
    indicatorIds: ["voter_turnout"],
  },
  {
    id: "kultur_fritid",
    name: "Kultur & fritid",
    description: "Adgang til og investering i kulturliv, fritidsaktiviteter og civile fællesskaber - biblioteker, musik, idræt og kommunal kultursatsning.",
    indicatorIds: ["music_school", "library_use", "kultur_spending"],
  },
  {
    id: "tryghed",
    name: "Tryghed & fællesskab",
    description: "Tryghed og social sammenhæng i lokalsamfundet - kriminalitet, trafiksikkerhed og social kapital målt via idrætsdeltagelse.",
    indicatorIds: ["crime_rate", "traffic_accidents", "sports_membership"],
  },
  {
    id: "lokalsamfund",
    name: "Lokalsamfund",
    description: "Nærhed til velfungerende basale services: pasning, undervisning, idrætsfaciliteter, kommunal investering i nærområdet og støtte til det lokale foreningsliv.",
    indicatorIds: ["sports_facilities", "class_size", "daycare_ratio", "sports_spending", "civil_society", "educated_staff"],
  },
  {
    id: "mobilitet",
    name: "Mobilitet",
    description: "Adgang til bæredygtig og effektiv transport for alle borgere uanset geografi og økonomi.",
    indicatorIds: ["commute_distance", "public_transport"],
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
  sourceLabel?: string; // Short label for source link
  unit?: string;
  boundary?: string; // Description of the planetary boundary
  // Sub-indikatorer til visning i ScoreBars (rawValues-nøgle + label + enhed)
  subIndicators?: {
    rawKey: string;       // nøgle i kommune.rawValues for råværdi (µg/m³, %, kg, ...)
    ratioKey?: string;    // nøgle i kommune.rawValues for sub-ratio (0-200) til at tegne bar
    label: string;        // visningsnavn
    unit: string;         // enhed
    boundary?: string;    // grænseværdi for denne sub-indikator
    lowerIsBetter?: boolean; // true = lavere er bedre (inverteret)
  }[];
}

export const ECOLOGICAL_DIMENSIONS: EcologicalDimension[] = [
  {
    id: "klimapaavirkning",
    name: "Klimapåvirkning",
    shortName: "KLIMA",
    description: "Territoriale drivhusgasudledninger fra energi, transport, landbrug og industri inden for kommunens grænser.",
    source: "https://klimaregnskabet.dk",
    sourceLabel: "Klimaregnskabet.dk",
    unit: "ton CO₂e/person",
    boundary: "3 ton CO₂e/person/år (Paris-budget, territorial)",
    subIndicators: [
      { rawKey: "eco_klima_raw", ratioKey: "klimapaavirkning_self", label: "Territoriale udledninger", unit: "ton CO₂e/person", boundary: "Mål: 3 ton CO₂e/person/år", lowerIsBetter: true },
    ],
  },
  {
    id: "forurening",
    name: "Forurening (novel entities)",
    shortName: "FORUR",
    description: "Kemisk forurening, mikroplast og persistent organisk forurening - den planetære grænse for 'novel entities'. Ingen pålidelig kommunal datakilde endnu.",
    unit: "Ingen indikator endnu",
    boundary: "Planetær grænse for novel entities (allerede overskredet globalt)",
  },
  {
    id: "luftkvalitet",
    name: "Luftkvalitet",
    shortName: "LUFT",
    description: "Modelberegnet årsgennemsnit af NO2 og PM2.5 pr. kommune (DCE/AU UBM-model 2023) sammenholdt med WHO's retningslinjer fra 2021.",
    unit: "µg/m³ (årsgennemsnit, WHO 2021)",
    boundary: "WHO 2021: NO2 = 10 µg/m³, PM2.5 = 5 µg/m³",
    source: "https://arld-extgeo.miljoeportal.dk/geoserver/wfs",
    sourceLabel: "Miljøportal WFS (DCE/AU)",
    subIndicators: [
      { rawKey: "luftkvalitet_no2",  ratioKey: "luftkvalitet_no2_ratio",  label: "NO₂ (kvælstofdioxid)",  unit: "µg/m³", boundary: "WHO 2021: 10 µg/m³", lowerIsBetter: true },
      { rawKey: "luftkvalitet_pm25", ratioKey: "luftkvalitet_pm25_ratio", label: "PM2.5 (fine partikler)", unit: "µg/m³", boundary: "WHO 2021: 5 µg/m³",  lowerIsBetter: true },
    ],
  },
  {
    id: "cirkularitet",
    name: "Cirkularitet (materialer)",
    shortName: "CIR",
    description: "Ressourceeffektivitet målt via genanvendelsesprocent og affaldsmængde pr. indbygger - lavt affald og høj genanvendelse indikerer en cirkulær økonomi.",
    source: "https://statbank.dk/LABY25",
    sourceLabel: "DST LABY25 + MST",
    unit: "% genanvendt + kg affald/person",
    boundary: "65% genanvendelse (EU 2035) + lavest muligt affald pr. capita",
    subIndicators: [
      { rawKey: "eco_cirkularitet_raw", ratioKey: "eco_cirkularitet_ratio", label: "Genanvendelsesprocent", unit: "%", boundary: "Mål: 65% (EU Affaldsdirektiv 2035)", lowerIsBetter: false },
      { rawKey: "eco_affald_raw",       ratioKey: "eco_affald_ratio",       label: "Affald pr. person",    unit: "kg/person", boundary: "Lavere end landsgennemsnittet er bedre", lowerIsBetter: true },
    ],
  },
  {
    id: "naeringsstoffer",
    name: "Næringsstoffer",
    shortName: "NÆR",
    description: "Kvælstof- og fosforbelastning af vandmiljøet fra to kilder: (1) spildevand (punktkilder) og (2) landbrugets N-loft pr. ha fra Vandområdeplan 3 - overgødskning der forårsager iltsvind og algeopblomstring.",
    source: "https://statbank.dk/VANDUD",
    sourceLabel: "DST VANDUD + VP3",
    unit: "ton N/P pr. 1.000 indb. + kg N/ha loft (VP3)",
    boundary: "Landsgennemsnittet som reference - lavere belastning og strengere N-loft er bedre for vandmiljøet",
    subIndicators: [
      { rawKey: "eco_naer_n_raw",        ratioKey: "eco_naer_n_ratio",        label: "Kvælstofudledning (spildevand)", unit: "ton N/1.000 indb.", boundary: "Lavere end landsgennemsnittet er bedre", lowerIsBetter: true },
      { rawKey: "eco_naer_p_raw",        ratioKey: "eco_naer_p_ratio",        label: "Fosforudledning (spildevand)",   unit: "ton P/1.000 indb.", boundary: "Lavere end landsgennemsnittet er bedre", lowerIsBetter: true },
      { rawKey: "eco_naer_landbrug_raw", ratioKey: "eco_naer_landbrug_ratio", label: "N-loft landbrug (VP3)",          unit: "kg N/ha",           boundary: "Lavere N-loft pr. ha = mere presset end landsgennemsnit", lowerIsBetter: true },
    ],
  },
  {
    id: "vand",
    name: "Vand",
    shortName: "VAND",
    description: "Pres på ferskvandsressourcer og vandkredsløb. Ingen kommunal indikator er endnu aktiveret for denne dimension.",
    unit: "Ingen indikator endnu",
    boundary: "Planetær grænse for ferskvand",
  },
  {
    id: "arealanvendelse",
    name: "Arealanvendelse",
    shortName: "AREAL",
    description: "Arealanvendelse og landskabsintegritet - tab af naturarealer og fragmentering af levesteder. Ingen kommunal indikator er endnu aktiveret for denne dimension.",
    unit: "Ingen indikator endnu",
    boundary: "Planetær grænse for arealanvendelse",
  },
  {
    id: "biodiversitet",
    name: "Biodiversitet",
    shortName: "BIO",
    description: "Andel af kommunens areal der er natur, skov og grønne arealer (inkl. skove, søer, enge og heder) - målt mod EU Biodiversitetsstrategiens 30%-mål for 2030.",
    source: "https://statbank.dk/AREALDK2",
    sourceLabel: "DST AREALDK2 + ARE207",
    unit: "% naturområder",
    boundary: "30% naturområder (EU Biodiversitetsstrategi 2030)",
    subIndicators: [
      { rawKey: "eco_bio_raw", ratioKey: "biodiversitet_self", label: "Andel naturområder", unit: "%", boundary: "Mål: 30% (EU Biodiversitetsstrategi 2030)", lowerIsBetter: false },
    ],
  },
  {
    id: "forbrug_co2",
    name: "Forbrugsbaseret CO₂",
    shortName: "FORBRUG",
    description: "Kommunens forbrugsbaserede klimaaftryk - udledninger der sker uden for kommunens grænser som følge af borgernes forbrug.",
    source: "https://concito.dk",
    sourceLabel: "Osei-Owusu et al. + ENS GA25",
    unit: "ton CO₂e/person",
    boundary: "3 ton CO₂e/person/år (Paris-budget, forbrugsbaseret)",
    subIndicators: [
      { rawKey: "forbrug_co2", ratioKey: "forbrug_co2_self", label: "Forbrugsbaseret CO₂ (estimat 2023)", unit: "ton CO₂e/person", boundary: "Mål: 3 ton CO₂e/person/år", lowerIsBetter: true },
    ],
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
  top10_ratios: Record<string, number | null>; // same indicators, top-10%-kommune som baseline
  eco_ratios: Record<string, number | null>; // ecological dimension ratios
  rawValues: Record<string, number | null>;   // faktiske råværdier (til visning i UI)
  social_avg: number | null;
  overall_avg: number | null;
}

/**
 * Beregner Top 10%-baselines dynamisk fra eksisterende ratios.
 * For hver social indikator: find de 10 bedste kommuner (højest ratio),
 * brug deres gennemsnit som ny baseline, og rescale alle kommuners ratio
 * til denne nye baseline.
 * Ekologiske indikatorer har absolutte grænser og påvirkes ikke.
 */
export function computeTop10Ratios(allData: KommuneData[]): void {
  const TOP_N = 10;
  const realKommuner = allData.filter((k) => k.kommune_kode !== "000");

  for (const k of allData) {
    k.top10_ratios = {};
  }

  for (const ind of INDICATORS) {
    if (ind.category !== "social") continue;

    const vals = realKommuner
      .map((k) => ({ kode: k.kommune_kode, ratio: k.ratios[ind.id] }))
      .filter((v): v is { kode: string; ratio: number } => v.ratio !== null);

    if (vals.length < TOP_N) {
      // Ikke nok data - brug avg-ratio som fallback
      for (const k of allData) {
        k.top10_ratios[ind.id] = k.ratios[ind.id];
      }
      continue;
    }

    // Højest ratio = bedste performer (gælder for både normale og inverse,
    // da inverse-indikatorer allerede er vendt i compute_ratios)
    vals.sort((a, b) => b.ratio - a.ratio);
    const top10Avg = vals.slice(0, TOP_N).reduce((s, v) => s + v.ratio, 0) / TOP_N;

    for (const k of allData) {
      const ratio = k.ratios[ind.id];
      if (ratio === null || top10Avg === 0) {
        k.top10_ratios[ind.id] = null;
      } else {
        k.top10_ratios[ind.id] = parseFloat(((ratio / top10Avg) * 100).toFixed(2));
      }
    }
  }
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
