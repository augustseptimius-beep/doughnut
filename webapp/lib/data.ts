import fs from "fs";
import path from "path";

// Re-export shared types and constants for server components
export {
  INDICATORS,
  SOCIAL_CATEGORIES,
  ECOLOGICAL_DIMENSIONS,
  scoreColor,
  scoreBarColor,
  computeCategoryScores,
  computeTop10Ratios,
} from "./shared";
// DOUGHNUT_EDITION_YEAR og DOUGHNUT_DEFAULT_DATA_YEAR beregnes her fra
// master-CSV'en (getDoughnutEdition()), ikke hårdkodet - se nedenfor.
export type {
  Indicator,
  KommuneData,
  SocialCategory,
  EcologicalDimension,
  CategoryScore,
} from "./shared";

import { INDICATORS, ECOLOGICAL_DIMENSIONS, ECO_INDICATOR_KEYS, INDIKATORREGISTER, NOEGLETAL, visningsscore, computeTop10Ratios, computeGroupRatios, type KommuneData, type RegisterIndikator, type TrendPost, type TrendDirection } from "./shared";

let cachedData: KommuneData[] | null = null;

// ─── Mapping fra master-CSV indicator_id til rawValues-nøgler ───────
// Master-CSV'en bruger korte indicator_ids (fx "luftkvalitet_no2"), mens
// ScoreBars og DoughnutRing læser økologiske sub-indikatorer fra bestemte
// nøgler i kommune.rawValues (subIndicators[].rawKey/ratioKey). Mappingen
// står i data/indikatorer.json (raw_key/ratio_key) og kommer via shared.ts.
const ECO_RAW_KEY_MAP = ECO_INDICATOR_KEYS;

// ─── Master-CSV loader ───────────────────────────────────────────────
// Long format: én række pr. (kommune × indikator). Genereret af
// scripts/build_master_csv.py. Erstatter de tidligere 25+ separate
// loadEcoCsv-kald.
//
// Specielle indicator_id'er:
//   _dim_<dimension>  →  worst-of dimension-score (eco_ratios[dimension])

interface MasterRow {
  kommune_kode: string;
  kommune_navn: string;
  indicator_id: string;
  ratio: string;
  raw_value: string;
  unit: string;
  data_year: string;
  source: string;
  category: string;
  dimension: string;
  reference: string;
}

let cachedMasterRows: MasterRow[] | null = null;

function parseMasterCsv(): MasterRow[] {
  if (cachedMasterRows) return cachedMasterRows;
  const rows = laesMasterCsv();
  validerMaster(rows);
  cachedMasterRows = rows;
  return rows;
}

// ─── Gate: master skal passe med registret ────────────────────────────
// Kører ved hvert build (også på Netlify) og i dev. Et master der ikke er
// bygget med det aktuelle register - fx fordi indikatorer.json er rettet uden
// at build_master_csv.py er kørt bagefter - stopper buildet med en fejl i
// stedet for at deploye tal der modsiger metoden. Netlify beholder så den
// forrige version online. Formlen er en kontrol-kopi af beregn_ratio() i
// scripts/build_master_csv.py (arkitekturdokumentet R2-R4).
function kontrolRatio(ind: RegisterIndikator, raw: number | null, ref: number | null): number | null {
  if (raw === null) return null;
  let x: number;
  if (ind.formula === "100_minus_raw") {
    x = 100 - raw;
  } else if (ind.formula === "komplement") {
    if (ref === null || ref >= 100) return null;
    x = ((100 - raw) / (100 - ref)) * 100;
  } else {
    if (!ref) return null;
    const rawOverRef = ind.category === "social" ? !ind.inverse : !!ind.lower_is_better;
    if (rawOverRef) x = (raw / ref) * 100;
    else if (raw === 0) x = Infinity;
    else x = (ref / raw) * 100;
  }
  const cap = ind.category === "social" ? Math.min(ind.cap ?? 150, 150) : ind.cap;
  if (cap !== undefined && x > cap) x = cap;
  if (!Number.isFinite(x)) return null;
  return Math.round(x * 100) / 100;
}

function validerMaster(rows: MasterRow[]): void {
  const fejl: string[] = [];
  const register = new Map(INDIKATORREGISTER.indikatorer.map((i) => [i.id, i]));
  const iMaster = new Set<string>();
  for (const r of rows) {
    if (r.indicator_id.startsWith("_dim_")) continue;
    iMaster.add(r.indicator_id);
    const ind = register.get(r.indicator_id);
    if (!ind) {
      fejl.push(`${r.indicator_id} står i master_indicators.csv, men ikke i data/indikatorer.json`);
      continue;
    }
    if (ind.category === "context") continue;
    const ratio = parseFloatOrNull(r.ratio);
    const forventet = kontrolRatio(ind, parseFloatOrNull(r.raw_value), parseFloatOrNull(r.reference));
    const passer =
      ratio === null ? forventet === null : forventet !== null && Math.abs(forventet - ratio) <= 0.011;
    if (!passer) {
      fejl.push(`${r.indicator_id} (${r.kommune_navn}): ratio ${r.ratio || "tom"} passer ikke med råværdi ${r.raw_value || "tom"} og reference ${r.reference || "tom"}`);
    }
  }
  const scorede = [
    ...INDIKATORREGISTER.sociale_kategorier.flatMap((k) => k.indicators),
    ...INDIKATORREGISTER.oekologiske_dimensioner.flatMap((d) => d.indicators),
  ];
  for (const id of scorede) {
    if (!iMaster.has(id)) fejl.push(`${id} scores, men har ingen rækker i master_indicators.csv`);
  }
  // noegletal.json (tal i metodeteksterne) skal være bygget sammen med master.
  const iMasterTal = new Map<string, { reference: number | null; daekning: number; data_year: string }>();
  for (const r of rows) {
    if (r.indicator_id.startsWith("_dim_")) continue;
    const t = iMasterTal.get(r.indicator_id) ?? { reference: null, daekning: 0, data_year: r.data_year };
    if (r.reference !== "") t.reference = parseFloatOrNull(r.reference);
    if (r.ratio !== "" || (r.category === "context" && r.raw_value !== "")) t.daekning += 1;
    iMasterTal.set(r.indicator_id, t);
  }
  for (const [id, t] of iMasterTal) {
    const n = NOEGLETAL.indikatorer[id];
    const refPasser = n && (n.reference === null ? t.reference === null
      : t.reference !== null && Math.abs(n.reference - t.reference) < 1e-9);
    if (!n || !refPasser || n.daekning !== t.daekning || n.data_year !== t.data_year) {
      fejl.push(`data/noegletal.json passer ikke med master for ${id} - er den committet sammen med master?`);
    }
  }

  if (fejl.length > 0) {
    throw new Error(
      `master_indicators.csv passer ikke med data/indikatorer.json (${fejl.length} fejl). ` +
      `Kør 'python3 scripts/build_master_csv.py' i projektets rodmappe og commit master-filen.\n  ` +
      fejl.slice(0, 15).join("\n  ") + (fejl.length > 15 ? "\n  ..." : "")
    );
  }
}

function laesMasterCsv(): MasterRow[] {
  const csvPath = path.join(process.cwd(), "..", "data", "master_indicators.csv");
  if (!fs.existsSync(csvPath)) {
    throw new Error(
      `master_indicators.csv mangler på sti: ${csvPath}\n` +
      `Kør 'python3 scripts/build_master_csv.py' i projektets rodmappe og commit filen.`
    );
  }
  const raw = fs.readFileSync(csvPath, "utf-8");
  const lines = raw.trim().split("\n");
  if (lines.length < 2) return [];

  const headers = lines[0].split(",");
  const rows: MasterRow[] = [];

  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(",");
    const obj: Record<string, string> = {};
    headers.forEach((h, idx) => {
      obj[h.trim()] = (cols[idx] || "").trim();
    });
    rows.push(obj as unknown as MasterRow);
  }
  return rows;
}

function parseFloatOrNull(s: string): number | null {
  if (!s || s === "") return null;
  const n = parseFloat(s);
  return isNaN(n) ? null : n;
}

// ─── Dataår afledt af master-CSV'en ────────────────────────────────────
// Metode-siden og footeren viste tidligere hårdkodede dataYear-strenge
// (shared.ts INDICATORS[].dataYear, MethodInfo.dataYear i metode/page.tsx,
// DOUGHNUT_EDITION_YEAR/DOUGHNUT_DEFAULT_DATA_YEAR). De tre levede hver sit
// sted og drev fra hinanden og fra master-CSV'ens egen data_year-kolonne
// hver gang en indikator blev opdateret uden at alle tre blev rettet med
// (sep. 2026: ca. 25 forkerte dataYear-felter + en footer der stod ét år
// forkert). Beregnes nu herfra i stedet, så der kun er ét sted at opdatere:
// data_years.json → build_master_csv.py → master_indicators.csv.

function extractYears(dataYear: string): number[] {
  return Array.from(dataYear.matchAll(/\d{4}/g)).map((m) => Number(m[0]));
}

function yearRange(years: number[]): string {
  if (years.length === 0) return "";
  const min = Math.min(...years);
  const max = Math.max(...years);
  return min === max ? String(min) : `${min}-${max}`;
}

let cachedDimensionYears: Record<string, string> | null = null;

/**
 * Dataårs-interval pr. kategori/dimension, nøglet på master-CSV'ens
 * `dimension`-kolonne (identisk med SOCIAL_CATEGORIES- og
 * ECOLOGICAL_DIMENSIONS-id'er). Dækker sociale, økologiske OG
 * kontekst-rækker - alt der vises under den pågældende overskrift på
 * metode-siden, ikke kun det der indgår i scoren.
 */
export function getDimensionDataYears(): Record<string, string> {
  if (cachedDimensionYears) return cachedDimensionYears;
  const years: Record<string, number[]> = {};
  for (const r of parseMasterCsv()) {
    if (r.indicator_id.startsWith("_dim_") || !r.data_year || !r.dimension) continue;
    (years[r.dimension] ??= []).push(...extractYears(r.data_year));
  }
  const result: Record<string, string> = {};
  for (const [dim, ys] of Object.entries(years)) result[dim] = yearRange(ys);
  cachedDimensionYears = result;
  return result;
}

let cachedIndicatorYears: Record<string, string> | null = null;

/** Dataår pr. social indikator, nøglet på indicator_id (samme id som INDICATORS[].id). */
export function getIndicatorDataYears(): Record<string, string> {
  if (cachedIndicatorYears) return cachedIndicatorYears;
  const result: Record<string, string> = {};
  for (const r of parseMasterCsv()) {
    if (r.category !== "social" || !r.data_year) continue;
    if (!(r.indicator_id in result)) result[r.indicator_id] = r.data_year;
  }
  cachedIndicatorYears = result;
  return result;
}

let cachedEdition: { edition: string; defaultYear: string } | null = null;

/**
 * "Doughnut-udgave" udledt af de sociale indikatorers dataår - ikke et
 * hårdkodet årstal. Seneste helårsdata = det år FLEST sociale indikatorer
 * faktisk har (mode, ikke max): et par indikatorer registrerer et
 * fremadrettet år (fx bolig_fossil på DST BYGB40, mærket 2026 fordi det er
 * hentningsåret for et opvarmet-areal-udtræk, ikke et helårsregnskab for
 * 2026) og ville ellers trække editionen et år frem uden grund. Udgaveåret
 * er dette år + 1, ligesom "en 2026-Doughnut bruger 2025-tal".
 */
export function getDoughnutEdition(): { edition: string; defaultYear: string } {
  if (cachedEdition) return cachedEdition;
  const counts = new Map<number, number>();
  for (const dataYear of Object.values(getIndicatorDataYears())) {
    const years = extractYears(dataYear);
    const last = years[years.length - 1]; // seneste år i en evt. periode/interval
    if (last !== undefined) counts.set(last, (counts.get(last) ?? 0) + 1);
  }
  let mode = new Date().getFullYear() - 1;
  let best = -1;
  for (const [year, n] of counts) {
    // Står to år lige, vinder det seneste - ellers afhænger footeren af
    // rækkefølgen i master-CSV'en, som ingen tænker over når de tilføjer rækker.
    if (n > best || (n === best && year > mode)) {
      best = n;
      mode = year;
    }
  }
  cachedEdition = { edition: String(mode + 1), defaultYear: String(mode) };
  return cachedEdition;
}

export const DOUGHNUT_EDITION_YEAR = getDoughnutEdition().edition;
export const DOUGHNUT_DEFAULT_DATA_YEAR = getDoughnutEdition().defaultYear;

// ─── Trend-CSV loader ─────────────────────────────────────────────────
// data/trend_indicators.csv (scripts/build_trends_csv.py). Samme simple
// split(",")-parsing som master-CSV'en - felter indeholder ikke komma.
interface TrendRow {
  kommune_kode: string;
  indicator_id: string;
  periode_start: string;
  periode_slut: string;
  vaerdi_start: string;
  vaerdi_slut: string;
  pct: string;
  retning: string;
  n_aar: string;
  kilde: string;
  noegle_indikator: string;
}

function parseTrendsCsv(): TrendRow[] {
  const csvPath = path.join(process.cwd(), "..", "data", "trend_indicators.csv");
  if (!fs.existsSync(csvPath)) return [];
  const raw = fs.readFileSync(csvPath, "utf-8");
  const lines = raw.trim().split("\n");
  if (lines.length < 2) return [];

  const headers = lines[0].split(",");
  const rows: TrendRow[] = [];
  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(",");
    const obj: Record<string, string> = {};
    headers.forEach((h, idx) => {
      obj[h.trim()] = (cols[idx] || "").trim();
    });
    rows.push(obj as unknown as TrendRow);
  }
  return rows;
}

// Økologiske sub-indikatorer nøgles i UI'et på rawKey (fx "eco_klima_raw"),
// ikke på master indicator_id (fx "klimapaavirkning"). Byg den omvendte
// mapping af ECO_RAW_KEY_MAP så trends kan slås op med samme nøgle.
const RAW_KEY_BY_INDICATOR_ID: Record<string, string> = Object.fromEntries(
  Object.entries(ECO_RAW_KEY_MAP).map(([indicatorId, keys]) => [indicatorId, keys.rawKey])
);

// Master indicator_id → menneskeligt navn, så tooltip på en dimensionspil kan
// sige "bestemt af Kvælstofnedfald fra luften" i stedet for "n_deposition".
const LABEL_BY_INDICATOR_ID: Record<string, string> = (() => {
  const m: Record<string, string> = {};
  for (const ind of INDICATORS) m[ind.id] = ind.name;
  const labelByRawKey: Record<string, string> = {};
  for (const dim of ECOLOGICAL_DIMENSIONS) {
    for (const sub of dim.subIndicators ?? []) labelByRawKey[sub.rawKey] = sub.label;
  }
  for (const [indicatorId, keys] of Object.entries(ECO_RAW_KEY_MAP)) {
    const label = labelByRawKey[keys.rawKey];
    if (label) m[indicatorId] = label;
  }
  return m;
})();

function loadTrendsByKommune(): Map<string, Record<string, TrendPost>> {
  const rows = parseTrendsCsv();
  const byKommune = new Map<string, Record<string, TrendPost>>();

  for (const r of rows) {
    if (!r.retning) continue;

    const noegle = r.noegle_indikator || "";
    const post: TrendPost = {
      retning: r.retning as TrendDirection,
      pct: parseFloatOrNull(r.pct),
      periodeStart: r.periode_start,
      periodeSlut: r.periode_slut,
      // _dim_*-aggregater har bevidst tomme værdier (ingen fælles enhed
      // på tværs af sub-indikatorer) - derfor null, ikke frasortering.
      vaerdiStart: parseFloatOrNull(r.vaerdi_start),
      vaerdiSlut: parseFloatOrNull(r.vaerdi_slut),
      nAar: parseInt(r.n_aar, 10) || 0,
      kilde: r.kilde,
      noegleIndikator: LABEL_BY_INDICATOR_ID[noegle] ?? noegle,
    };

    if (!byKommune.has(r.kommune_kode)) byKommune.set(r.kommune_kode, {});
    const trends = byKommune.get(r.kommune_kode)!;
    trends[r.indicator_id] = post;

    const rawKey = RAW_KEY_BY_INDICATOR_ID[r.indicator_id];
    if (rawKey) trends[rawKey] = post;
  }

  return byKommune;
}

export function loadData(): KommuneData[] {
  if (cachedData) return cachedData;

  const rows = parseMasterCsv();
  const trendsByKommune = loadTrendsByKommune();

  // Group rows by kommune_kode
  const byKommune = new Map<string, { navn: string; rows: MasterRow[] }>();
  for (const r of rows) {
    if (!byKommune.has(r.kommune_kode)) {
      byKommune.set(r.kommune_kode, { navn: r.kommune_navn, rows: [] });
    }
    byKommune.get(r.kommune_kode)!.rows.push(r);
  }

  // Build KommuneData for each kommune
  const data: KommuneData[] = [];
  for (const [kode, { navn, rows: kommuneRows }] of byKommune.entries()) {
    const ratios: Record<string, number | null> = {};
    const rawValues: Record<string, number | null> = {};
    const eco_ratios: Record<string, number | null> = {};

    for (const r of kommuneRows) {
      const ratio = parseFloatOrNull(r.ratio);
      const rawVal = parseFloatOrNull(r.raw_value);

      // Dimension-aggregat-rækker (worst-of scores)
      if (r.indicator_id.startsWith("_dim_")) {
        const dimId = r.indicator_id.substring(5);
        // Én decimal, som den vises - så ringen, farven og tællingen af
        // overskredne grænser bruger samme tal som teksten (visningsscore()).
        eco_ratios[dimId] = visningsscore(ratio);
        continue;
      }

      // Kontekst-råværdier (vises, scores ikke): rutes til rawValues[indicator_id]
      if (r.category === "context") {
        if (rawVal !== null) rawValues[r.indicator_id] = rawVal;
        continue;
      }

      // Sociale indikatorer: ratios + rawValues nøglet på indicator_id (matcher INDICATORS-id)
      if (r.category === "social") {
        ratios[r.indicator_id] = ratio;
        if (rawVal !== null) {
          rawValues[r.indicator_id] = rawVal;
        }
        continue;
      }

      // Økologiske sub-indikatorer: skriv til de specifikke rawValues-nøgler
      // som ScoreBars/DoughnutRing forventer (jf. EcologicalDimension.subIndicators)
      if (r.category === "ecological") {
        const keys = ECO_RAW_KEY_MAP[r.indicator_id];
        if (keys) {
          if (rawVal !== null) rawValues[keys.rawKey] = rawVal;
          if (keys.ratioKey && ratio !== null) rawValues[keys.ratioKey] = ratio;
        }
      }
    }

    // Sørg for at alle INDICATORS er repræsenteret (null hvis ingen data)
    for (const ind of INDICATORS) {
      if (!(ind.id in ratios)) {
        ratios[ind.id] = null;
      }
    }

    // Sørg for at alle ECOLOGICAL_DIMENSIONS er repræsenteret (null hvis ingen data)
    // Vigtigt: client.tsx skelner mellem null og undefined når den tæller "afventer data"-dimensioner.
    // Inaktive dimensioner (forurening, vand, arealanvendelse) skal være eksplicit null.
    for (const dim of ECOLOGICAL_DIMENSIONS) {
      if (!(dim.id in eco_ratios)) {
        eco_ratios[dim.id] = null;
      }
    }

    data.push({
      kommune_kode: kode,
      kommune_navn: navn,
      ratios,
      top10_ratios: {},  // udfyldes af computeTop10Ratios nedenfor
      group_ratios: {},  // udfyldes af computeGroupRatios nedenfor
      eco_ratios,
      rawValues,
      trends: trendsByKommune.get(kode) ?? {},
      // social_avg og overall_avg er pre-computed i den gamle CSV men
      // bruges ikke længere af UI'et (det beregnes via computeCategoryScores).
      // Vi sætter dem til null - hvis en gammel side stadig læser dem, vil de
      // blot vise '–'.
      social_avg: null,
      overall_avg: null,
    });
  }

  // Beregn Top 10%-baselines dynamisk fra de indlæste ratios
  computeTop10Ratios(data);
  // Beregn kommunegruppe-baselines
  computeGroupRatios(data);

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
  // Kode "000" = Danmark-aggregat (ikke i master-CSV pt., men holdes ude for sikkerhed)
  return loadData().filter((k) => k.kommune_kode !== "000");
}
