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
  absoluteScore?: boolean;    // true = ratio er en absolut score (fx 100-fossil%), ikke relativ
                              // til landsgennemsnit. Påvirkes IKKE af baseline-toggle (avg/top10/gruppe).
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
    absoluteScore: true,
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
    id: "bolig_fossil",
    name: "Fossil opvarmning (inkl. fjernvarme)",
    table: "BOL202",
    source: "https://www.statistikbanken.dk/BOL202",
    category: "social",
    inverse: true,
    dataYear: "2026",
    baselineLevel: 2,
    absoluteTarget: "0% fossil (udfasningsmål)",
    absoluteScore: true,
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
  {
    id: "voter_turnout_national",
    name: "Stemmedeltagelse folketingsvalg",
    table: "LABY09",
    source: "https://www.statistikbanken.dk/LABY09",
    category: "social",
    inverse: false,
    dataYear: "2026",
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
  // --- Klimatilpasning ---
  {
    id: "vejr_skader",
    name: "Vejrrelaterede forsikringsskader pr. 1.000 indb.",
    table: "F&P skadesstatistik",
    source: "https://fogp.dk/tal-og-analyser/saadan-er-danmark-blevet-ramt-af-vejrrelaterede-skader-de-seneste-aar/",
    category: "social",
    inverse: true,
    dataYear: "2023-2025",
    baselineLevel: 3,
    rawUnit: "skader pr. 1.000 indb.",
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
    id: "hospital_short",
    name: "Sygehusophold under 12 timer (andel)",
    table: "SBR01",
    source: "https://www.statistikbanken.dk/SBR01",
    category: "social",
    inverse: true,
    dataYear: "2023",
    baselineLevel: 3,
    rawUnit: "%",
  },
  {
    id: "hospital_long",
    name: "Sygehusophold 12+ timer (andel)",
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
  {
    id: "medicin",
    name: "Antidepressivt forbrug",
    table: "MEDI1",
    source: "https://www.statistikbanken.dk/MEDI1",
    category: "social",
    inverse: true,
    dataYear: "2024",
    baselineLevel: 3,
    rawUnit: "recepter/100 borgere",
  },
  {
    id: "laegekontakt",
    name: "Andel med lægekontakt",
    table: "SYGP1",
    source: "https://www.statistikbanken.dk/SYGP1",
    category: "social",
    inverse: false,
    dataYear: "2024",
    baselineLevel: 3,
    rawUnit: "%",
  },
  {
    id: "boerneovervaeght",
    name: "Overvægt blandt 6-7-årige",
    table: "LABY26",
    source: "https://www.statistikbanken.dk/LABY26",
    category: "social",
    inverse: true,
    dataYear: "2018",
    baselineLevel: 3,
    rawUnit: "%",
  },
  {
    id: "hjemsyg",
    name: "Hjemmesygepleje-modtagere",
    table: "HJEMSYG",
    source: "https://www.statistikbanken.dk/HJEMSYG",
    category: "social",
    inverse: true,
    dataYear: "2025",
    baselineLevel: 3,
    rawUnit: "pr. 1.000 indb.",
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
  // --- UVM: Uddannelse ---
  {
    id: "exam_grade",
    name: "Karaktergennemsnit, folkeskolens afgangseksamen",
    table: "GS/KARA/KARAGNS",
    source: "https://api.uddannelsesstatistik.dk",
    category: "social",
    inverse: false,
    dataYear: "2024",
    baselineLevel: 3,
    rawUnit: "karakter",
  },
  {
    id: "high_absence",
    name: "Elever med højt fravær (>10%)",
    table: "GS/ELEVFRAV/FRAVAAR",
    source: "https://api.uddannelsesstatistik.dk",
    category: "social",
    inverse: true,
    dataYear: "2024",
    baselineLevel: 3,
    rawUnit: "%",
  },
  {
    id: "youth_education",
    name: "Forventet ungdomsuddannelseskompetence",
    table: "GS/PROFMOD/PROFMOD",
    source: "https://api.uddannelsesstatistik.dk",
    category: "social",
    inverse: false,
    dataYear: "2024",
    baselineLevel: 3,
    rawUnit: "%",
  },
  {
    id: "apprenticeship",
    name: "Læreplads-søgende med afsluttet grundforløb",
    table: "EUD/PRAK/SØG",
    source: "https://api.uddannelsesstatistik.dk",
    category: "social",
    inverse: false,
    dataYear: "2024",
    baselineLevel: 3,
    rawUnit: "%",
  },
  // --- UVM: Trivsel ---
  {
    id: "wellbeing",
    name: "Elevtrivsel i folkeskolen (gennemsnit)",
    table: "GS/TRIV/TRIVIND",
    source: "https://api.uddannelsesstatistik.dk",
    category: "social",
    inverse: false,
    dataYear: "2024",
    baselineLevel: 3,
    rawUnit: "score (1-5)",
  },
  // --- DST: Lighed & velfærd ---
  {
    id: "poverty_relative",
    name: "Relativ fattigdom (indkomst <60% af median)",
    table: "IFOR12P",
    source: "https://www.statistikbanken.dk/IFOR12P",
    category: "social",
    inverse: true,
    dataYear: "2023",
    baselineLevel: 3,
    rawUnit: "%",
  },
  {
    id: "child_notifications",
    name: "Underretninger om børn pr. 1.000 indb. 0-17 år",
    table: "UND2",
    source: "https://www.statistikbanken.dk/UND2",
    category: "social",
    inverse: true,
    dataYear: "2023",
    baselineLevel: 3,
    rawUnit: "pr. 1.000 indb.",
  },
  // --- DST: Boligforhold ---
  {
    id: "housing_no_wc",
    name: "Boliger uden eget toilet (%)",
    table: "BOL102",
    source: "https://www.statistikbanken.dk/BOL102",
    category: "social",
    inverse: true,
    dataYear: "2023",
    baselineLevel: 3,
    rawUnit: "%",
  },
  {
    id: "housing_no_bath",
    name: "Boliger uden eget bad (%)",
    table: "BOL102",
    source: "https://www.statistikbanken.dk/BOL102",
    category: "social",
    inverse: true,
    dataYear: "2023",
    baselineLevel: 3,
    rawUnit: "%",
  },
  // --- DST: Ligestilling ---
  {
    id: "gender_leadership",
    name: "Kvinder i lederstillinger (%)",
    table: "RAS301",
    source: "https://www.statistikbanken.dk/RAS301",
    category: "social",
    inverse: false,
    dataYear: "2023",
    baselineLevel: 3,
    rawUnit: "% kvinder",
  },
  {
    id: "le_gender_gap",
    name: "Kønsgab i middellevetid (år)",
    table: "HISBK",
    source: "https://www.statistikbanken.dk/HISBK",
    category: "social",
    inverse: true,
    dataYear: "2025",
    baselineLevel: 3,
    rawUnit: "år (kvinder - mænd)",
  },
  {
    id: "income_gender_gap",
    name: "Indkomstlighed mænd/kvinder (%)",
    table: "INDKP101",
    source: "https://www.statistikbanken.dk/INDKP101",
    category: "social",
    inverse: false,
    dataYear: "2024",
    baselineLevel: 3,
    rawUnit: "% (kvinders andel af mænds indkomst)",
  },
  {
    id: "employment_origin_gap",
    name: "Beskæftigelse ikke-vestlige vs. dansk (%)",
    table: "RAS200",
    source: "https://www.statistikbanken.dk/RAS200",
    category: "social",
    inverse: false,
    dataYear: "2024",
    baselineLevel: 3,
    rawUnit: "% (ikke-vestlig BFK / dansk BFK)",
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
    indicatorIds: ["life_expectancy", "hospital_short", "hospital_long", "gp_distance", "medicin", "laegekontakt", "boerneovervaeght", "hjemsyg"],
  },
  {
    id: "uddannelse",
    name: "Uddannelse",
    description: "Adgang til og gennemførelse af uddannelse for alle aldersgrupper - grundlag for personlig udvikling og samfundsdeltagelse.",
    indicatorIds: ["education", "low_education", "exam_grade", "high_absence", "youth_education", "apprenticeship", "wellbeing", "class_size", "daycare_ratio", "educated_staff"],
  },
  {
    id: "velfaerd",
    name: "Velfærd",
    description: "Materiel levevilkår, indkomst, beskæftigelse og social sikring - de grundlæggende betingelser for et godt liv.",
    indicatorIds: ["disposable_income", "employment", "child_poverty", "vulnerable_children", "neet", "poverty_relative", "child_notifications"],
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
    indicatorIds: ["voter_turnout", "voter_turnout_national"],
  },
  {
    id: "kultur_fritid",
    name: "Kultur",
    description: "Adgang til og investering i kulturlivet - biblioteker, musikskoler og kommunens samlede kulturudgifter.",
    indicatorIds: ["music_school", "library_use", "kultur_spending"],
  },
  {
    id: "tryghed",
    name: "Tryghed",
    description: "Tryghed i lokalsamfundet målt via kriminalitetsniveau og trafiksikkerhed.",
    indicatorIds: ["crime_rate", "traffic_accidents"],
  },
  {
    id: "lokalsamfund",
    name: "Foreningsliv",
    description: "Det lokale foreningsliv og idræt - idrætsfaciliteter, idrætsmedlemskab, kommunens idrætsudgifter og støtte til frivillige foreninger.",
    indicatorIds: ["sports_facilities", "sports_spending", "civil_society", "sports_membership"],
  },
  {
    id: "lighed",
    name: "Lighed",
    description: "Fordelingen af indkomst og materielle ressourcer i kommunen - et mål for strukturel ulighed og sociale skel.",
    indicatorIds: ["gini", "low_income", "employment_origin_gap"],
  },
  {
    id: "mobilitet",
    name: "Mobilitet",
    description: "Adgang til bæredygtig og effektiv transport for alle borgere uanset geografi og økonomi.",
    indicatorIds: ["commute_distance", "public_transport"],
  },
  {
    id: "ligestilling",
    name: "Ligestilling",
    description: "Kønsbalance og lige muligheder i kommunen - herunder repræsentation på arbejdsmarkedet og i ledelse.",
    indicatorIds: ["gender_leadership", "le_gender_gap", "income_gender_gap"],
  },
  {
    id: "klimatilpasning",
    name: "Klimatilpasning",
    description: "Kommunens robusthed over for klimaforandringer: oversvømmelse, hedebølger, tørke og ekstremvejr.",
    indicatorIds: ["vejr_skader"],
  },
  {
    id: "energi",
    name: "Energi",
    description: "Husstandenes fossile energiafhængighed - andel boliger opvarmet med olie eller naturgas. Fossil opvarmning belaster klimaet og udsætter husstande for høje, svingende varmeregninger. Lokal VE-produktion og fjernvarmens brændselsmix vises som kontekst, men indgår ikke i scoren.",
    indicatorIds: ["bolig_fossil"],
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
    baselineType?: "absolut" | "relativ"; // mod fast mål vs mod landsgennemsnit
  }[];
}

export const ECOLOGICAL_DIMENSIONS: EcologicalDimension[] = [
  {
    id: "klimapaavirkning",
    name: "Klimapåvirkning",
    shortName: "KLIMA",
    description: "Drivhusgasudledninger målt på to måder: territorialt (udledninger inden for kommunens grænser) og forbrugsbaseret (borgernes samlede aftryk, inkl. importerede varer). Worst-of logik. Begge holdes op mod et Paris-budget på 3 ton CO₂e/person/år.",
    source: "https://klimaregnskabet.dk",
    sourceLabel: "Klimaregnskabet.dk + CONCITO/ENS",
    unit: "ton CO₂e/person",
    boundary: "3 ton CO₂e/person/år (Paris-budget) - gælder både territorialt og forbrugsbaseret",
    subIndicators: [
      { rawKey: "eco_klima_raw", ratioKey: "klimapaavirkning_self", label: "Territoriale udledninger",        unit: "ton CO₂e/person", boundary: "Mål: 3 ton CO₂e/person/år (territorial)",     lowerIsBetter: true, baselineType: "absolut" },
      { rawKey: "forbrug_co2",   ratioKey: "forbrug_co2_self",      label: "Forbrugsbaseret CO₂ (inkl. import)", unit: "ton CO₂e/person", boundary: "Mål: 3 ton CO₂e/person/år (forbrugsbaseret)", lowerIsBetter: true, baselineType: "absolut" },
    ],
  },
  {
    id: "forurening",
    name: "Forurening",
    shortName: "FORUR",
    description: "Kemisk forurening og materialecyklusser - fire indikatorer vægtet ens (gennemsnit, ikke worst-of): pesticider i grundvand, nitrat i drikkevand, husholdningsaffald og genanvendelse. Pesticider og nitrat dækker CONCITO-rapportens 'novel entities'-grænse; affald og genanvendelse dækker materialecyklusser.",
    source: "https://www.dn.dk/nyheder/tjek-din-kommune-sa-ofte-er-der-giftrester-i-grundvandet/",
    sourceLabel: "DN/GEUS + Greenpeace/GEUS + DST",
    unit: "% boringer, mg/L, kg/person, %",
    boundary: "Pesticider: 0% over drikkevandsnormen. Nitrat: 6 mg/L. Affald + genanvendelse: mod landsgennemsnit og EU's 65%-mål.",
    subIndicators: [
      { rawKey: "eco_pesticid_raw",     ratioKey: "pesticider_self",       label: "Pesticider i grundvand",      unit: "% boringer > 0.1 µg/l", boundary: "Grænse: 0% (drikkevandsnorm)", lowerIsBetter: true,  baselineType: "absolut" },
      { rawKey: "eco_nitrat_raw",       ratioKey: "nitrat_self",           label: "Nitrat i drikkevand",         unit: "mg/L",                  boundary: "Grænse: 6 mg/L (ekspertgruppe 2025)", lowerIsBetter: true, baselineType: "absolut" },
      { rawKey: "eco_cirkularitet_raw", ratioKey: "eco_cirkularitet_ratio", label: "Genanvendelse (husholdning)", unit: "%",                     boundary: "Mål: 65% (EU Affaldsdirektiv 2035)", lowerIsBetter: false, baselineType: "absolut" },
      { rawKey: "eco_affald_raw",       ratioKey: "eco_affald_ratio",      label: "Affald pr. person",           unit: "kg/person",             boundary: "Lavere end landsgennemsnittet er bedre", lowerIsBetter: true, baselineType: "relativ" },
    ],
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
      { rawKey: "luftkvalitet_no2",  ratioKey: "luftkvalitet_no2_ratio",  label: "NO₂ (kvælstofdioxid)",  unit: "µg/m³", boundary: "WHO 2021: 10 µg/m³", lowerIsBetter: true, baselineType: "absolut" },
      { rawKey: "luftkvalitet_pm25", ratioKey: "luftkvalitet_pm25_ratio", label: "PM2.5 (fine partikler)", unit: "µg/m³", boundary: "WHO 2021: 5 µg/m³",  lowerIsBetter: true, baselineType: "absolut" },
    ],
  },
  {
    id: "naeringsstoffer",
    name: "Næringsstoffer",
    shortName: "NÆR",
    description: "Næringsstofbelastning af vandmiljøet og den eutrofiering det forårsager. Tre presmål: kvælstof og fosfor fra spildevand (punktkilder) samt landbrugets N-loft pr. ha (VP3). Plus ét effektmål: andelen af kommunens vandområder i god økologisk tilstand (VP3) - den synlige skade (iltsvind, algeopblomstring). Worst-of logik.",
    source: "https://statbank.dk/VANDUD",
    sourceLabel: "DST VANDUD + VP3",
    unit: "ton N/P pr. 1.000 indb., kg N/ha, % vandområder i god tilstand",
    boundary: "Landsgennemsnittet som reference - lavere belastning og strengere N-loft er bedre for vandmiljøet",
    subIndicators: [
      { rawKey: "eco_naer_n_raw",        ratioKey: "eco_naer_n_ratio",        label: "Kvælstofudledning (spildevand)", unit: "ton N/1.000 indb.", boundary: "Lavere end landsgennemsnittet er bedre", lowerIsBetter: true, baselineType: "relativ" },
      { rawKey: "eco_naer_p_raw",        ratioKey: "eco_naer_p_ratio",        label: "Fosforudledning (spildevand)",   unit: "ton P/1.000 indb.", boundary: "Lavere end landsgennemsnittet er bedre", lowerIsBetter: true, baselineType: "relativ" },
      { rawKey: "eco_naer_landbrug_raw", ratioKey: "eco_naer_landbrug_ratio", label: "N-loft landbrug (VP3)",          unit: "kg N/ha",           boundary: "Lavere N-loft pr. ha = mere presset end landsgennemsnit", lowerIsBetter: true, baselineType: "relativ" },
      { rawKey: "eco_overfladevand_raw", ratioKey: "overfladevand_ratio",     label: "Vandområder i god økologisk tilstand (VP3)", unit: "%",  boundary: "EU-mål: 100% i god tilstand (2027) - nationalt langtfra opfyldt. Scoret mod landsgennemsnit.", lowerIsBetter: false, baselineType: "relativ" },
    ],
  },
  {
    id: "vand",
    name: "Vand",
    shortName: "VAND",
    description: "Vandindvinding fra almene vandværker pr. person - et indirekte mål for pres på grundvandsressourcerne. Nitrat i drikkevand er flyttet til Forurening-dimensionen, da det er et forureningsspørgsmål (novel entities).",
    source: "https://www.statistikbanken.dk/VANDIND",
    sourceLabel: "DST VANDIND (2024)",
    unit: "m³/person",
    boundary: "Landsgennemsnit (72,9 m³/person, 2024) som reference. Jo lavere vandindvinding pr. person, jo mindre pres på grundvandet.",
    subIndicators: [
      { rawKey: "eco_vandindvinding_raw", ratioKey: "vandindvinding_self", label: "Vandindvinding (alment vandværk)", unit: "m³/person", boundary: "Lavere end landsgennemsnittet er bedre. OBS: bykommuner kan mangle data pga. vandværkets registreringssted.", lowerIsBetter: true, baselineType: "relativ" },
    ],
  },
  {
    id: "arealanvendelse",
    name: "Arealanvendelse",
    shortName: "AREAL",
    description: "Pres på det fysiske landskab fra to menneskeskabte arealanvendelser: intensivt landbrug og kunstigt befæstet areal (veje, bebyggelse). Worst-of logik - den dårligste afgør dimensionsscoren. Naturkvalitet måles separat i biodiversitetsdimensionen.",
    source: "https://www.statistikbanken.dk/AREALDK2",
    sourceLabel: "DST AREALDK2 (2024)",
    unit: "% af kommunens areal",
    boundary: "Nationalt gennemsnit 2024 som reference (intensivt landbrug ~55%, bebygget ~14%). Til kontekst: den planetære grænse er max 15% antropiseret areal (landbrug + bebygget tilsammen, Rockström 2009) - Danmark ligger på 73-75%, en femdobbelt overskridelse. Vi scorer mod landsgennemsnittet for at vise forskel mellem kommuner.",
    subIndicators: [
      { rawKey: "eco_areal_intensiv_raw", ratioKey: "areal_intensiv_ratio", label: "Intensivt landbrug", unit: "%", boundary: "Nationalt snit: ~55%", lowerIsBetter: true, baselineType: "relativ" },
      { rawKey: "eco_areal_bebygget_raw", ratioKey: "areal_bebygget_ratio", label: "Bebygget + veje",    unit: "%", boundary: "Nationalt snit: ~14%", lowerIsBetter: true, baselineType: "relativ" },
    ],
  },
  {
    id: "biodiversitet",
    name: "Biodiversitet",
    shortName: "BIO",
    description: "Andel af kommunens areal med væsentlig og uerstattelig naturværdi for truede arter, målt med DCE's biodiversitetskort (bioscore). Worst-of logik. Måler habitatkvalitet, ikke rent arealdække - en biologisk fattig plantage tæller derfor ikke som høj natur. Grænserne er EU's politiske mål (30%/10%), ikke den planetære grænse - se metodesiden.",
    source: "https://dce.au.dk/udgivelser/vr/nr-101-150/abstracts/nr-112-biodiversitetskort-for-danmark",
    sourceLabel: "DCE Biodiversitetskort (bioscore)",
    unit: "% af areal med naturværdi",
    boundary: "30% væsentlig naturværdi + 10% uerstattelig (EU Biodiversitetsstrategi 2030)",
    subIndicators: [
      { rawKey: "eco_bio_vasentlig_raw",    ratioKey: "bio_vasentlig_ratio",    label: "Væsentlig naturværdi (bioscore ≥8)",    unit: "%", boundary: "Mål: 30% (EU Biodiversitetsstrategi 2030)", lowerIsBetter: false, baselineType: "absolut" },
      { rawKey: "eco_bio_uerstattelig_raw", ratioKey: "bio_uerstattelig_ratio", label: "Uerstattelig naturværdi (bioscore ≥12)", unit: "%", boundary: "Mål: 10% strengt beskyttet (EU 2030)",     lowerIsBetter: false, baselineType: "absolut" },
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

// --- BASELINE-TYPE: absolut (mod fast mål) vs relativ (mod landsgennemsnit) ---
export type BaselineType = "absolut" | "relativ";
export type DimBaselineType = BaselineType | "blandet";

// En social indikators type følger dens scoringsadfærd.
export function indicatorBaselineType(ind: Indicator): BaselineType {
  return ind.absoluteScore ? "absolut" : "relativ";
}

function combineBaselineTypes(types: BaselineType[]): DimBaselineType {
  if (types.length === 0) return "relativ";
  if (types.every((t) => t === "absolut")) return "absolut";
  if (types.every((t) => t === "relativ")) return "relativ";
  return "blandet";
}

// Tager listen af indikatorer (fx fra CategoryScore.indicators eller en SocialCategory).
export function categoryBaselineType(indicators: Indicator[]): DimBaselineType {
  return combineBaselineTypes(indicators.map(indicatorBaselineType));
}

export function dimensionBaselineType(dim: EcologicalDimension): DimBaselineType {
  const types = (dim.subIndicators ?? [])
    .map((s) => s.baselineType)
    .filter((t): t is BaselineType => !!t);
  return combineBaselineTypes(types);
}

// --- HELPERS ---

export interface KommuneData {
  kommune_kode: string;
  kommune_navn: string;
  ratios: Record<string, number | null>;
  top10_ratios: Record<string, number | null>; // same indicators, top-10%-kommune som baseline
  group_ratios: Record<string, number | null>; // same indicators, kommunegruppe-gennemsnit som baseline
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

    // Absolutte scorer (fx fossil opvarmning mod mål 0) omskaleres ikke - de er
    // ikke relative til andre kommuner. Behold den absolutte værdi uændret.
    if (ind.absoluteScore) {
      for (const k of allData) k.top10_ratios[ind.id] = k.ratios[ind.id];
      continue;
    }

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

// --- KOMMUNEGRUPPE-MAPPING (DST KOMMUNEGRUPPER_V1_2018) ---
// G1: Hovedstadskommuner (24), G2: Storbykommuner (3),
// G3: Provinsbykommuner (16), G4: Oplandskommuner (24), G5: Landkommuner (31)
export const KOMMUNEGRUPPE: Record<string, number> = {
  // G1: Hovedstadskommuner
  "101": 1, "147": 1, "151": 1, "153": 1, "155": 1, "157": 1, "159": 1, "161": 1,
  "163": 1, "165": 1, "167": 1, "169": 1, "173": 1, "175": 1, "183": 1, "185": 1,
  "187": 1, "190": 1, "201": 1, "223": 1, "230": 1, "240": 1, "253": 1, "269": 1,
  // G2: Storbykommuner
  "461": 2, "751": 2, "851": 2,
  // G3: Provinsbykommuner
  "217": 3, "219": 3, "259": 3, "265": 3, "330": 3, "370": 3, "561": 3, "607": 3,
  "615": 3, "621": 3, "630": 3, "657": 3, "661": 3, "730": 3, "740": 3, "791": 3,
  // G4: Oplandskommuner
  "210": 4, "250": 4, "260": 4, "270": 4, "316": 4, "320": 4, "329": 4, "336": 4,
  "340": 4, "350": 4, "410": 4, "420": 4, "430": 4, "440": 4, "450": 4, "480": 4,
  "575": 4, "706": 4, "710": 4, "727": 4, "746": 4, "756": 4, "766": 4, "840": 4,
  // G5: Landkommuner
  "306": 5, "326": 5, "360": 5, "376": 5, "390": 5, "400": 5, "479": 5, "482": 5,
  "492": 5, "510": 5, "530": 5, "540": 5, "550": 5, "563": 5, "573": 5, "580": 5,
  "665": 5, "671": 5, "707": 5, "741": 5, "760": 5, "773": 5, "779": 5, "787": 5,
  "810": 5, "813": 5, "820": 5, "825": 5, "846": 5, "849": 5, "860": 5,
};

export const KOMMUNEGRUPPE_NAVNE: Record<number, string> = {
  1: "Hovedstadskommuner",
  2: "Storbykommuner",
  3: "Provinsbykommuner",
  4: "Oplandskommuner",
  5: "Landkommuner",
};

export function kommunegruppeNavn(kode: string): string {
  const grp = KOMMUNEGRUPPE[kode];
  return grp ? KOMMUNEGRUPPE_NAVNE[grp] : "Kommunegruppe";
}

/**
 * Beregner kommunegruppe-baselines dynamisk fra eksisterende ratios.
 * For hver social indikator og hver gruppe (G1-G5): beregn gruppens uvægtede
 * gennemsnit, og omskaler alle kommuners ratio til denne baseline.
 * 100 = den gennemsnitlige kommune i gruppen.
 */
export function computeGroupRatios(allData: KommuneData[]): void {
  const realKommuner = allData.filter((k) => k.kommune_kode !== "000");

  for (const k of allData) {
    k.group_ratios = {};
  }

  for (const ind of INDICATORS) {
    if (ind.category !== "social") continue;

    // Absolutte scorer omskaleres ikke mod kommunegruppen - behold værdien.
    if (ind.absoluteScore) {
      for (const k of allData) k.group_ratios[ind.id] = k.ratios[ind.id];
      continue;
    }

    const groupSums: Record<number, number> = {};
    const groupCounts: Record<number, number> = {};

    for (const k of realKommuner) {
      const grp = KOMMUNEGRUPPE[k.kommune_kode];
      if (!grp) continue;
      const ratio = k.ratios[ind.id];
      if (ratio === null) continue;
      groupSums[grp] = (groupSums[grp] ?? 0) + ratio;
      groupCounts[grp] = (groupCounts[grp] ?? 0) + 1;
    }

    const groupAvg: Record<number, number> = {};
    for (const grp of Object.keys(groupSums).map(Number)) {
      if (groupCounts[grp] > 0) {
        groupAvg[grp] = groupSums[grp] / groupCounts[grp];
      }
    }

    for (const k of allData) {
      const grp = KOMMUNEGRUPPE[k.kommune_kode];
      const ratio = k.ratios[ind.id];
      const avg = grp ? groupAvg[grp] : undefined;

      if (ratio === null || avg === undefined || avg === 0) {
        k.group_ratios[ind.id] = null;
      } else {
        k.group_ratios[ind.id] = parseFloat(((ratio / avg) * 100).toFixed(2));
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

export function scoreBarColor(score: number | null): string {
  if (score === null) return "bg-gray-300";
  if (score >= 100) return "bg-emerald-500";
  if (score >= 85) return "bg-amber-400";
  return "bg-red-400";
}
