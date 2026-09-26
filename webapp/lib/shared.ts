// Indikatorer, sociale kategorier og økologiske dimensioner kommer fra
// data/indikatorer.json - samme fil som build_master_csv.py og
// build_trends_csv.py læser (via scripts/indikatorregister.py). Ret dem dér,
// ikke her. Denne fil oversætter kun registrets felter til de typer UI'et
// bruger. Doughnut-udgave og dataår beregnes i data.ts fra master-CSV'en.
import registerJson from "../../data/indikatorer.json";
import noegletalJson from "../../data/noegletal.json";
import kommunerJson from "../../data/kommuner.json";

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
  cap?: number;
  formula?: "100_minus_raw" | "komplement";
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

// ─── Tal i tekster udfyldes fra data ─────────────────────────────────
// Registrets og metodesidens tekster skriver ikke landstal og dækning i
// hånden - de drev ved hver dataopdatering. I stedet står en pladsholder,
// som udfyldes fra data/noegletal.json (skrevet af build_master_csv.py
// sammen med master, og kontrolleret mod master i data.ts):
//   {ref:ID:D}     indikatorens reference (landstal/mål) med D decimaler
//   {daekning:ID}  antal kommuner med en værdi
//   {mangler:ID}   antal kommuner uden værdi
//   {aar:ID}       indikatorens dataår
//   {kommuner}     antal kommuner i alt
// En ukendt pladsholder stopper buildet i stedet for at stå rå på siden.
interface Noegletal {
  kommuner: number;
  // faa_tilfaelde: kommuner hvor tallet bygger på under 20 tilfælde (registrets smaa_tal)
  indikatorer: Record<string, { reference: number | null; daekning: number; data_year: string; faa_tilfaelde?: string[] }>;
}
export const NOEGLETAL = noegletalJson as unknown as Noegletal;

// Bygger kommunens tal på under 20 tilfælde? Så er forskellen til
// sammenligningsgrundlaget usikker (NCHS' grænse, arkitekturdokumentet R16).
export function faaTilfaelde(indikatorId: string, kommuneKode: string): boolean {
  return NOEGLETAL.indikatorer[indikatorId]?.faa_tilfaelde?.includes(kommuneKode) ?? false;
}

function formatTal(x: number, decimaler: number): string {
  const [hel, brok] = Math.abs(x).toFixed(decimaler).split(".");
  const tusinder = hel.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return (x < 0 ? "-" : "") + tusinder + (brok ? "," + brok : "");
}

export function udfyldTal(tekst: string): string;
export function udfyldTal(tekst: string | undefined): string | undefined;
export function udfyldTal(tekst: string | undefined): string | undefined {
  if (!tekst || !tekst.includes("{")) return tekst;
  return tekst.replace(/\{(ref|daekning|mangler|aar|kommuner)(?::(\w+))?(?::(\d))?\}/g, (hele, type, id, dec) => {
    if (type === "kommuner") return String(NOEGLETAL.kommuner);
    const tal = id ? NOEGLETAL.indikatorer[id] : undefined;
    if (!tal) throw new Error(`Ukendt indikator i pladsholderen ${hele} (data/noegletal.json)`);
    if (type === "daekning") return String(tal.daekning);
    if (type === "mangler") return String(NOEGLETAL.kommuner - tal.daekning);
    if (type === "aar") return tal.data_year;
    if (tal.reference === null) throw new Error(`${hele}: ${id} har ingen reference i data/noegletal.json`);
    return formatTal(tal.reference, dec === undefined ? 1 : Number(dec));
  });
}

/** Hele registret. Bruges af data.ts til at validere master-CSV'en ved build. */
export const INDIKATORREGISTER: Register = REGISTER;
export type { RegisterIndikator };
const REGISTER_BY_ID = new Map(REGISTER.indikatorer.map((i) => [i.id, i]));

export type BaselineLevel = 1 | 2 | 3;
// Niveau 1: Absolutte biofysiske/juridiske grænser (WHO, EU-direktiver)
// Niveau 2: Nationale politiske mål (lovmål, regeringsmål)
// Niveau 3: Landsgennemsnit (default når ingen absolut grænse findes)

/**
 * Loftet for sociale ratios (arkitekturdokumentet R1). build_master_csv.py
 * lægger det på landsgennemsnits-ratioen, og top 10%- og kommunegruppe-
 * baselinen lægger det på igen efter omskaleringen (R9, R10). Uden det andet
 * loft kunne én indikator løfte en hel kategori i standardvisningen: Svendborg
 * fik 338 på offentlig transport og 214,7 på Mobilitet (sep. 2026).
 * En indikator kan have et lavere loft i registret (`cap`), se Indicator.loft.
 */
export const SOCIAL_LOFT = 150;

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
  loft: number;               // Højeste ratio i alle visninger: SOCIAL_LOFT, eller registrets
                              // lavere 'cap' (kystrisiko: 100, ingen risiko er neutral).
}

// Sociale indikatorer i registrets rækkefølge (= master-CSV'ens). Hvad der
// scores, afgøres af SOCIAL_CATEGORIES[].indicatorIds.
export const INDICATORS: Indicator[] = REGISTER.indikatorer
  .filter((i) => i.category === "social")
  .map((i) => ({
    id: i.id,
    name: udfyldTal(i.name!),
    table: i.table!,
    source: i.source_url!,
    category: "social" as const,
    inverse: i.inverse!,
    dataYear: i.data_year,
    baselineLevel: i.baseline_level,
    absoluteTarget: i.target_label,
    absoluteScore: i.absolute_score,
    rawUnit: i.raw_unit ?? i.unit,
    loft: Math.min(i.cap ?? SOCIAL_LOFT, SOCIAL_LOFT),
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
  REGISTER.indikatorer.filter((i) => i.rationale).map((i) => [i.id, udfyldTal(i.rationale!)])
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
  description: udfyldTal(k.description),
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
  description: udfyldTal(d.description),
  source: d.source,
  sourceLabel: udfyldTal(d.source_label),
  unit: d.unit,
  boundary: udfyldTal(d.boundary),
  subIndicators: d.indicators.map((id) => {
    const i = REGISTER_BY_ID.get(id)!;
    return {
      rawKey: i.raw_key!,
      ratioKey: i.ratio_key,
      label: udfyldTal(i.name!),
      unit: i.raw_unit ?? i.unit,
      boundary: udfyldTal(i.boundary),
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

/**
 * Scoren som den vises: én decimal. Farver, tællinger ("N af 13 over
 * gennemsnittet") og ringens tænder skal bruge samme tal som teksten, ellers
 * kan en score på 99,96 stå som "100.0" og samtidig være farvet gul.
 */
export function visningsscore(score: number): number;
export function visningsscore(score: number | null): number | null;
export function visningsscore(score: number | null): number | null {
  return score === null ? null : Number(score.toFixed(1));
}

export function computeCategoryScores(
  ratios: Record<string, number | null>
): CategoryScore[] {
  return SOCIAL_CATEGORIES.map((cat) => {
    const indicators = cat.indicatorIds.map((id) => ({
      indicator: INDICATORS.find((ind) => ind.id === id)!,
      score: visningsscore(ratios[id] ?? null),
    }));

    // Gennemsnittet regnes på de uafrundede ratios og afrundes bagefter.
    const validScores = cat.indicatorIds
      .map((id) => ratios[id] ?? null)
      .filter((s): s is number => s !== null);

    const score =
      validScores.length > 0
        ? visningsscore(validScores.reduce((a, b) => a + b, 0) / validScores.length)
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
 * til denne nye baseline, højst indikatorens loft (SOCIAL_LOFT eller lavere).
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
        k.top10_ratios[ind.id] = Math.min(parseFloat(((ratio / top10Avg) * 100).toFixed(2)), ind.loft);
      }
    }
  }
}

// --- KOMMUNEGRUPPER (DST KOMMUNEGRUPPER_V1_2018) ---
// Fra data/kommuner.json, samme kommuneliste som Python-pipelinen bruger
// (scripts/kommuner.py). G1 Hovedstadskommuner (24), G2 Storbykommuner (3),
// G3 Provinsbykommuner (16), G4 Oplandskommuner (24), G5 Landkommuner (31).
export const KOMMUNEGRUPPE: Record<string, number> = Object.fromEntries(
  kommunerJson.kommuner.map((k) => [k.kode, k.gruppe]),
);

export const KOMMUNEGRUPPE_NAVNE: Record<number, string> = Object.fromEntries(
  Object.entries(kommunerJson.grupper).map(([gruppe, navn]) => [Number(gruppe), navn]),
);

export function kommunegruppeNavn(kode: string): string {
  const grp = KOMMUNEGRUPPE[kode];
  return grp ? KOMMUNEGRUPPE_NAVNE[grp] : "Kommunegruppe";
}

/**
 * Beregner kommunegruppe-baselines dynamisk fra eksisterende ratios.
 * For hver social indikator og hver gruppe (G1-G5): beregn gruppens uvægtede
 * gennemsnit, og omskaler alle kommuners ratio til denne baseline, højst
 * indikatorens loft. 100 = den gennemsnitlige kommune i gruppen.
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
        k.group_ratios[ind.id] = Math.min(parseFloat(((ratio / avg) * 100).toFixed(2)), ind.loft);
      }
    }
  }
}

export function scoreColor(score: number | null): string {
  const s = visningsscore(score);
  if (s === null) return "text-gray-400";
  if (s >= 100) return "text-emerald-600";
  if (s >= 85) return "text-amber-500";
  return "text-red-500";
}

export function scoreBarColor(score: number | null): string {
  const s = visningsscore(score);
  if (s === null) return "bg-gray-300";
  if (s >= 100) return "bg-emerald-500";
  if (s >= 85) return "bg-amber-400";
  return "bg-red-400";
}
