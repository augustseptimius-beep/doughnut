// Indikatorer, sociale kategorier og økologiske dimensioner kommer fra
// data/indikatorer.json - samme fil som build_master_csv.py og
// build_trends_csv.py læser (via scripts/indikatorregister.py). Ret dem dér,
// ikke her. Denne fil oversætter kun registrets felter til de typer UI'et
// bruger. Doughnut-udgave og dataår beregnes i data.ts fra master-CSV'en.
import registerJson from "../../data/indikatorer.json";

interface RegisterIndikator {
  id: string;
  category: "social" | "ecological" | "context";
  dimension: string;
  name?: string;
  table?: string;
  source: string;
  source_url?: string;
  unit: string;
  raw_unit?: string;
  data_year: string;
  csv?: string;
  inverse?: boolean;
  baseline_level?: BaselineLevel;
  absolute_score?: boolean;
  target_label?: string;
  lower_is_better?: boolean;
  baseline_type?: "absolut" | "relativ";
  boundary?: string;
  raw_key?: string;
  ratio_key?: string;
  rationale?: string;
}

interface Register {
  sociale_kategorier: { id: string; name: string; description: string; indicators: string[] }[];
  oekologiske_dimensioner: {
    id: string;
    name: string;
    short_name: string;
    description: string;
    source: string;
    source_label: string;
    unit: string;
    boundary: string;
    aggregation: "worst-of" | "gennemsnit";
    indicators: string[];
  }[];
  indikatorer: RegisterIndikator[];
}

const REGISTER = registerJson as unknown as Register;
const REGISTER_BY_ID = new Map(REGISTER.indikatorer.map((i) => [i.id, i]));

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

// Sociale indikatorer i registrets rækkefølge (= master-CSV'ens), inkl. de to
// der står i master uden at blive scoret (housing_no_wc/no_bath). Hvad der
// scores, afgøres af SOCIAL_CATEGORIES[].indicatorIds.
export const INDICATORS: Indicator[] = REGISTER.indikatorer
  .filter((i) => i.category === "social")
  .map((i) => ({
    id: i.id,
    name: i.name!,
    table: i.table!,
    source: i.source_url!,
    category: "social" as const,
    inverse: i.inverse!,
    dataYear: i.data_year,
    baselineLevel: i.baseline_level,
    absoluteTarget: i.target_label,
    absoluteScore: i.absolute_score,
    rawUnit: i.raw_unit ?? i.unit,
  }));

/**
 * Datafilerne bag en kategori eller dimension: først de scorede indikatorers
 * filer i visningsrækkefølge, derefter kontekst-indikatorernes. Vises på
 * metodesiden i stedet for en håndskrevet liste, der kunne glemme en fil.
 */
export function dimensionCsvFiles(dimensionId: string): string[] {
  const scorede =
    REGISTER.oekologiske_dimensioner.find((d) => d.id === dimensionId)?.indicators ??
    REGISTER.sociale_kategorier.find((k) => k.id === dimensionId)?.indicators ??
    [];
  const kontekst = REGISTER.indikatorer
    .filter((i) => i.category === "context" && i.dimension === dimensionId)
    .map((i) => i.id);
  const filer = [...scorede, ...kontekst].map((id) => REGISTER_BY_ID.get(id)?.csv).filter((f): f is string => !!f);
  return Array.from(new Set(filer));
}

/** Metodesidens begrundelse pr. indikator (registrets "rationale"). */
export const INDICATOR_RATIONALES: Record<string, string> = Object.fromEntries(
  REGISTER.indikatorer.filter((i) => i.rationale).map((i) => [i.id, i.rationale!])
);

// --- SOCIAL CATEGORIES (TORUS trivselsaspekter) ---

export interface SocialCategory {
  id: string;
  name: string;
  description?: string;
  indicatorIds: string[];
}

export const SOCIAL_CATEGORIES: SocialCategory[] = REGISTER.sociale_kategorier.map((k) => ({
  id: k.id,
  name: k.name,
  description: k.description,
  indicatorIds: k.indicators,
}));

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

export const ECOLOGICAL_DIMENSIONS: EcologicalDimension[] = REGISTER.oekologiske_dimensioner.map((d) => ({
  id: d.id,
  name: d.name,
  shortName: d.short_name,
  description: d.description,
  source: d.source,
  sourceLabel: d.source_label,
  unit: d.unit,
  boundary: d.boundary,
  subIndicators: d.indicators.map((id) => {
    const i = REGISTER_BY_ID.get(id)!;
    return {
      rawKey: i.raw_key!,
      ratioKey: i.ratio_key,
      label: i.name!,
      unit: i.raw_unit ?? i.unit,
      boundary: i.boundary,
      lowerIsBetter: i.lower_is_better,
      baselineType: i.baseline_type,
    };
  }),
}));

/**
 * Master-CSV'ens indicator_id for en økologisk sub-indikator → de nøgler i
 * kommune.rawValues, som ScoreBars og DoughnutRing læser råværdi og ratio fra.
 * Bruges af data.ts (tidligere den håndskrevne ECO_RAW_KEY_MAP).
 */
export const ECO_INDICATOR_KEYS: Record<string, { rawKey: string; ratioKey: string | null }> =
  Object.fromEntries(
    REGISTER.indikatorer
      .filter((i) => i.category === "ecological")
      .map((i) => [i.id, { rawKey: i.raw_key!, ratioKey: i.ratio_key ?? null }])
  );

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

// --- RETNINGSVISNING (trend) ---
// En pil pr. indikator der viser om kommunen bevæger sig mod eller væk fra
// målet, beregnet på råværdier (ikke ratio) over en flerårig periode.
// Data kommer fra data/trend_indicators.csv (scripts/build_trends_csv.py).
// Dækker kun de indikatorer der har en efterprøvet historisk kilde - resten
// får retning "ingen" (ikke fejl, bare ingen tidsserie endnu).
export type TrendDirection = "rigtig" | "tempo" | "stagneret" | "forkert" | "kontekst" | "ingen";

export interface TrendPost {
  retning: TrendDirection;
  pct: number | null;        // procentvis ændring fra periodeStart til periodeSlut
  periodeStart: string;
  periodeSlut: string;
  vaerdiStart: number | null;  // null for _dim_*-aggregater (ingen fælles enhed)
  vaerdiSlut: number | null;
  nAar: number;
  kilde: string;
  // Kun sat på _dim_*-aggregater: hvilken sub-indikator retningen kommer fra
  // (worst-of), eller "gennemsnit af N indikatorer". Vises i tooltip, så
  // brugeren kan se hvad pilen faktisk beskriver.
  noegleIndikator?: string;
}

// Ét sted for retningsteksterne, så ScoreBars og DoughnutRing altid siger det
// samme. Bevidst formuleret som positiv/forkert retning UDEN at nævne et
// konkret mål: retningen måles på råværdier og holdes op mod de øvrige
// kommuners udvikling, ikke mod en fastsat målsætning. "Mod målet" ville
// derfor være misvisende, især for de mange indikatorer der scores relativt.
export const TREND_LABEL: Record<TrendDirection, string> = {
  rigtig: "Bevæger sig i positiv retning",
  tempo: "Bevæger sig i positiv retning, men langsommere end de fleste kommuner",
  stagneret: "Stort set uændret",
  forkert: "Bevæger sig i forkert retning",
  kontekst: "Ingen entydig positiv eller negativ retning",
  ingen: "Ingen tidsserie endnu",
};

// Hvor pilen sidder afgør hvad den skal betyde:
//   "indikator"  - en enkelt måling. Pilen følger RÅVÆRDIENS faktiske retning,
//                  så man ser det nuancerede billede: inden for Forurening skal
//                  affald ned og genanvendelse op, og begge dele er positivt.
//                  Farven fortæller om det er godt eller skidt.
//   "social"     - en kategori i det sociale fundament. Underskud skal fyldes
//                  OP mod fundamentet, så op = fremgang.
//   "ecological" - en dimension under det økologiske loft. Overskridelse skal
//                  ned UNDER loftet, så ned = fremgang.
// De to sidste følger doughnut-geometrien: pilen peger mod det grønne bånd
// når det går fremad, uanset hvad den underliggende råværdi gør.
export type TrendKontekst = "indikator" | "social" | "ecological";

/** Peger pilen opad? Se TrendKontekst for reglerne bag. */
export function trendPilOpad(t: TrendPost, kontekst: TrendKontekst): boolean {
  if (kontekst === "indikator") return (t.pct ?? 0) >= 0;
  const fremgang = t.retning === "rigtig" || t.retning === "tempo";
  return kontekst === "social" ? fremgang : !fremgang;
}

/** Fuld beskrivelse med periode og ændring i procent. Bruges i tooltip og panel. */
export function trendBeskrivelse(t: TrendPost, kontekst: TrendKontekst = "indikator"): string {
  const label = TREND_LABEL[t.retning];
  const hoved = `${t.periodeStart} → ${t.periodeSlut}`;
  if (t.pct === null) return `${hoved} (${label.charAt(0).toLowerCase()}${label.slice(1)})`;

  if (kontekst === "indikator") {
    // Råværdiens faktiske ændring - fortegnet er meningsfuldt i sig selv.
    const pctTxt = `${t.pct > 0 ? "+" : ""}${t.pct.toFixed(1)}%`;
    return `${hoved}: ${pctTxt} (${label.charAt(0).toLowerCase()}${label.slice(1)})`;
  }
  // Dimensionsniveau: pct er målrettet, så et negativt tal ville læses som
  // "faldt" i stedet for "gik den forkerte vej". Skriv det ud i stedet.
  const stoerrelse = Math.abs(t.pct).toFixed(1);
  if (t.retning === "stagneret") return `${hoved}: stort set uændret`;
  const vej = t.pct >= 0 ? "i positiv retning" : "i forkert retning";
  return `${hoved}: ${stoerrelse}% ${vej}`;
}

export interface KommuneData {
  kommune_kode: string;
  kommune_navn: string;
  ratios: Record<string, number | null>;
  top10_ratios: Record<string, number | null>; // same indicators, top-10%-kommune som baseline
  group_ratios: Record<string, number | null>; // same indicators, kommunegruppe-gennemsnit som baseline
  eco_ratios: Record<string, number | null>; // ecological dimension ratios
  rawValues: Record<string, number | null>;   // faktiske råværdier (til visning i UI)
  // Nøglet på BÅDE indicator_id (sociale) og eco sub-indikatorens rawKey
  // (økologiske), så ScoreBars kan slå op uden en ekstra mapping-tabel.
  trends: Record<string, TrendPost>;
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
