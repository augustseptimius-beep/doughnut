// Uafhængig verifikation af fase 1 (spec afsnit 15, fase 1-acceptkriterium + paritet lag 1-3 forskudt til nu).
//
// Læser KUN outputtet i migration/lovable/ og sammenligner med det gamle site:
//   A  Rundtur: snapshots + register + manifest genskaber master-CSV'en (uden _dim_) række for række, alle 10 kolonner
//   B  Metadata: registret genskaber INDICATORS, SOCIAL_CATEGORIES, ECOLOGICAL_DIMENSIONS m.fl. = fase 0-baseline
//   C  Værdier: en reference-loader efter spec afsnit 7 (inkl. R7 fra sub-ratios) genskaber parity_baseline.json
//   D  Metode-tekster: markdown giver ordret de gamle tekster tilbage; håndkonverterede afsnit har samme ordfølge
//   E  Integritet: alle filer, id'er, opdateringsmetoder og opskrifter hænger sammen
//   T  Transforms: registrets formel + manifestets reference genskaber den gemte ratio (informativt, ikke et krav)
//
// A-E skal give 0 fejl. Exit-kode 1 ved fejl.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { computeTop10Ratios, computeGroupRatios, computeCategoryScores } from "../../webapp/lib/shared.ts";
import { INDICATOR_DEFS } from "../lovable/registry/indicators.ts";
import { DIMENSION_DEFS } from "../lovable/registry/dimensions.ts";
import { KOMMUNER } from "../lovable/registry/kommuner.ts";
import { REFERENCES } from "../lovable/registry/references.ts";
import { DOUGHNUT_EDITION_YEAR, DOUGHNUT_DEFAULT_DATA_YEAR, KOMMUNEGRUPPE_NAVNE, METODE_GENERELT } from "../lovable/registry/settings.ts";
import { buildLegacyConstants } from "../lovable/registry/legacy.ts";
import { applyTransform, usesReference } from "../lovable/registry/transforms.ts";
import { readMasterCsv, readSnapshot, sha256, mdUnescape, loadMetodeData } from "./lib.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..", "..");
const lovable = path.join(root, "migration", "lovable");
const snapDir = path.join(lovable, "data", "snapshots");
const contentDir = path.join(lovable, "content", "metode");

const errors = [];
const info = [];
const check = (group, cond, msg) => cond || errors.push(`[${group}] ${msg}`);
const canon = (v) => JSON.stringify(v, (k, x) => (x && typeof x === "object" && !Array.isArray(x) ? Object.fromEntries(Object.keys(x).sort().map((key) => [key, x[key]])) : x));

const manifest = JSON.parse(fs.readFileSync(path.join(snapDir, "_manifest.json"), "utf-8"));
const metaBaseline = JSON.parse(fs.readFileSync(path.join(root, "migration", "baseline", "metadata_baseline.json"), "utf-8"));
const parityBaseline = JSON.parse(fs.readFileSync(path.join(root, "migration", "baseline", "parity_baseline.json"), "utf-8"));
const defById = new Map(INDICATOR_DEFS.map((d) => [d.id, d]));

// ─── E (først, så A-D kan stole på strukturen) ───
const snapFiles = fs.readdirSync(snapDir).filter((f) => f.endsWith(".csv")).map((f) => f.slice(0, -4)).sort();
const regIds = INDICATOR_DEFS.map((d) => d.id);
check("E", new Set(regIds).size === regIds.length, "dublet-id i registret");
check("E", canon(snapFiles) === canon([...regIds].sort()), "snapshot-filer og registerposter er ikke de samme id'er");
check("E", canon(Object.keys(manifest.indicators).sort()) === canon([...regIds].sort()), "manifest og register dækker ikke de samme id'er");
const dimIds = new Set(DIMENSION_DEFS.map((d) => d.id));
for (const d of INDICATOR_DEFS) {
  check("E", dimIds.has(d.dimensionId), `${d.id}: ukendt dimension ${d.dimensionId}`);
  if (d.update.method === "frozen" && d.update.recipe) {
    check("E", fs.existsSync(path.join(root, "scripts", path.basename(d.update.recipe))), `${d.id}: opskrift ${d.update.recipe} findes ikke i scripts/`);
  }
  if (d.kind !== "context") check("E", d.transform.type !== "none", `${d.id}: scoret indikator uden transform`);
  if (usesReference(d)) check("E", manifest.indicators[d.id].reference_value !== null, `${d.id}: transform kræver reference, manifest har ingen`);
}
const SPEC_FUNCTIONS = ["fetch-doughnut", "fetch-social-new", "fetch-social-extra", "fetch-sundhed", "fetch-udvidelse", "fetch-ligestilling", "fetch-demokrati",
  "fetch-klimaregnskabet", "fetch-klimatilpasning", "fetch-arealanvendelse", "fetch-vandindvinding", "fetch-eco-dst", "fetch-ve", "fetch-fjernvarme", "fetch-bolig-fossil"];
const usedFns = new Set(INDICATOR_DEFS.filter((d) => d.update.method === "api").map((d) => d.update.fn));
check("E", canon([...usedFns].sort()) === canon([...SPEC_FUNCTIONS].sort()), `edge functions i registret afviger fra spec 9.1: ${[...usedFns].sort()}`);
for (const ids of Object.values(DIMENSION_DEFS.map((d) => d.references ?? []))) for (const id of ids) check("E", REFERENCES[id], `ukendt reference ${id}`);
check("E", KOMMUNER.length === 98 && new Set(KOMMUNER.map((k) => k.kode)).size === 98, "registret har ikke 98 unikke kommuner");

// ─── A: rundtur til master-CSV ───
const master = readMasterCsv(path.join(root, "data", "master_indicators.csv")).filter((r) => !r.indicator_id.startsWith("_dim_"));
const kommuneNavn = new Map(KOMMUNER.map((k) => [k.kode, k.navn]));
const rebuilt = new Map();
for (const id of snapFiles) {
  const file = path.join(snapDir, `${id}.csv`);
  const m = manifest.indicators[id];
  const d = defById.get(id);
  check("A", sha256(fs.readFileSync(file)) === m.sha256, `${id}: snapshot-hash matcher ikke manifestet`);
  const rows = readSnapshot(file);
  check("A", rows.length === m.row_count, `${id}: ${rows.length} rækker, manifest siger ${m.row_count}`);
  for (const r of rows) {
    check("A", kommuneNavn.get(r.kommune_kode) === r.kommune_navn, `${id}: kommune ${r.kommune_kode} "${r.kommune_navn}" matcher ikke registret`);
    rebuilt.set(`${r.kommune_kode}|${id}`, {
      kommune_kode: r.kommune_kode, kommune_navn: r.kommune_navn, indicator_id: id, ratio: r.ratio, raw_value: r.raw_value,
      unit: d.unit, data_year: m.data_year, source: d.sourceName, category: d.kind, dimension: d.dimensionId,
    });
  }
}
// Kendte, godkendte afvigelser: enheden i registret er den UI'et viser (spec 3, konfliktregel), ikke build-scriptets.
const legacyDisplayUnit = new Map();
for (const i of metaBaseline.INDICATORS) legacyDisplayUnit.set(i.id, i.rawUnit);
for (const dim of metaBaseline.ECOLOGICAL_DIMENSIONS) {
  for (const s of dim.subIndicators ?? []) {
    const id = Object.entries(metaBaseline.eco_raw_key_map).find(([, k]) => k.rawKey === s.rawKey)?.[0];
    legacyDisplayUnit.set(id, s.unit);
  }
}
const unitConflicts = new Map();
check("A", rebuilt.size === master.length, `rundtur: ${rebuilt.size} rækker genskabt, master-CSV har ${master.length}`);
for (const r of master) {
  const key = `${r.kommune_kode}|${r.indicator_id}`;
  const x = rebuilt.get(key);
  if (!x) { check("A", false, `mangler i snapshots: ${key}`); continue; }
  for (const col of Object.keys(r)) {
    if (x[col] === r[col]) continue;
    if (col === "unit" && x.unit === legacyDisplayUnit.get(r.indicator_id)) {
      unitConflicts.set(r.indicator_id, { master: r.unit, registret: x.unit });
      continue;
    }
    check("A", false, `${key}.${col}: master "${r[col]}", genskabt "${x[col]}"`);
  }
}

// ─── B: metadata ───
const legacy = buildLegacyConstants({
  indicators: INDICATOR_DEFS, dimensions: DIMENSION_DEFS, kommuner: KOMMUNER, kommunegruppeNavne: KOMMUNEGRUPPE_NAVNE,
  editionYear: DOUGHNUT_EDITION_YEAR, defaultDataYear: DOUGHNUT_DEFAULT_DATA_YEAR, manifest,
});
const pairs = [
  ["INDICATORS", legacy.INDICATORS, metaBaseline.INDICATORS],
  ["SOCIAL_CATEGORIES", legacy.SOCIAL_CATEGORIES, metaBaseline.SOCIAL_CATEGORIES],
  ["ECOLOGICAL_DIMENSIONS", legacy.ECOLOGICAL_DIMENSIONS, metaBaseline.ECOLOGICAL_DIMENSIONS],
  ["KOMMUNEGRUPPE", legacy.KOMMUNEGRUPPE, metaBaseline.KOMMUNEGRUPPE],
  ["KOMMUNEGRUPPE_NAVNE", legacy.KOMMUNEGRUPPE_NAVNE, metaBaseline.KOMMUNEGRUPPE_NAVNE],
  ["ECO_RAW_KEY_MAP", legacy.ECO_RAW_KEY_MAP, metaBaseline.eco_raw_key_map],
  ["settings", { DOUGHNUT_EDITION_YEAR: legacy.DOUGHNUT_EDITION_YEAR, DOUGHNUT_DEFAULT_DATA_YEAR: legacy.DOUGHNUT_DEFAULT_DATA_YEAR }, metaBaseline.settings],
];
for (const [name, got, want] of pairs) {
  if (canon(got) === canon(want)) continue;
  // Find første afvigelse, så fejlen kan bruges til noget.
  const g = Array.isArray(got) ? got : Object.entries(got);
  const w = Array.isArray(want) ? want : Object.entries(want);
  const i = w.findIndex((x, n) => canon(x) !== canon(g[n]));
  check("B", false, `${name} afviger fra baseline (første forskel ved indeks ${i}: genskabt ${canon(g[i])?.slice(0, 200)} / baseline ${canon(w[i])?.slice(0, 200)})`);
}

// ─── C: reference-loader (spec afsnit 7) mod parity_baseline ───
const num = (s) => (s === "" ? null : parseFloat(s));
const ecoDims = DIMENSION_DEFS.filter((d) => d.kind === "ecological");
const loaded = KOMMUNER.map((k) => ({ kommune_kode: k.kode, kommune_navn: k.navn, ratios: {}, top10_ratios: {}, group_ratios: {}, eco_ratios: {}, rawValues: {}, social_avg: null, overall_avg: null }));
const byKode = new Map(loaded.map((k) => [k.kommune_kode, k]));
const subRatios = new Map(); // kode -> dimId -> [ratio]
for (const d of INDICATOR_DEFS.filter((x) => x.active)) {
  for (const r of readSnapshot(path.join(snapDir, `${d.id}.csv`))) {
    const k = byKode.get(r.kommune_kode);
    const raw = num(r.raw_value);
    const ratio = num(r.ratio);
    if (d.kind === "social") {
      k.ratios[d.id] = ratio;
      if (raw !== null) k.rawValues[d.id] = raw;
    } else if (d.kind === "context") {
      if (raw !== null) k.rawValues[d.id] = raw;
    } else {
      if (raw !== null) k.rawValues[d.rawKey] = raw;
      if (d.ratioKey && ratio !== null) k.rawValues[d.ratioKey] = ratio;
      if (ratio !== null) {
        if (!subRatios.has(k.kommune_kode)) subRatios.set(k.kommune_kode, new Map());
        const m = subRatios.get(k.kommune_kode);
        if (!m.has(d.dimensionId)) m.set(d.dimensionId, []);
        m.get(d.dimensionId).push(ratio);
      }
    }
  }
}
// R7, rækkefølge-uafhængig: worst-of = max (ingen afrunding nødvendig, sub-ratios har højst 2 decimaler).
// Gennemsnit summeres eksakt i hundrededele og afrundes halvt op. Det gamle site summerede floats i
// build-rækkefølge, så præcis på x,xx5 kan det afvige med 0,01. Den slags "ties" registreres og tillades i C.
const ties = new Set();
for (const k of loaded) {
  for (const dim of ecoDims) {
    const rs = subRatios.get(k.kommune_kode)?.get(dim.id) ?? [];
    if (rs.length === 0) k.eco_ratios[dim.id] = null;
    else if (dim.aggregation === "worst_of") k.eco_ratios[dim.id] = Math.max(...rs);
    else {
      const sum = rs.reduce((a, r) => a + Math.round(r * 100), 0);
      if ((2 * sum) % (2 * rs.length) === rs.length) ties.add(`${k.kommune_kode}.eco_ratios.${dim.id}`);
      k.eco_ratios[dim.id] = Math.floor((2 * sum + rs.length) / (2 * rs.length)) / 100;
    }
  }
  for (const i of legacy.INDICATORS) if (!(i.id in k.ratios)) k.ratios[i.id] = null;
}
computeTop10Ratios(loaded);
computeGroupRatios(loaded);

const FIELDS = ["ratios", "top10_ratios", "group_ratios", "eco_ratios", "rawValues"];
const MODES = { avg: "ratios", top10: "top10_ratios", kommunegruppe: "group_ratios" };
let compared = 0;
const tieDiffs = [];
const close = (a, b) => (a === null || b === null ? a === b : Math.abs(a - b) <= 0.01 + 1e-9);
check("C", parityBaseline.kommuner.length === loaded.length, "antal kommuner afviger fra parity_baseline");
for (const want of parityBaseline.kommuner) {
  const got = byKode.get(want.kommune_kode);
  if (!got) { check("C", false, `kommune ${want.kommune_kode} mangler`); continue; }
  check("C", got.kommune_navn === want.kommune_navn, `${want.kommune_kode}: navn afviger`);
  for (const f of FIELDS) {
    const keys = new Set([...Object.keys(want[f]), ...Object.keys(got[f])]);
    for (const key of keys) {
      compared++;
      const a = got[f][key];
      const b = want[f][key];
      if (a === undefined || b === undefined) { check("C", false, `${want.kommune_kode}.${f}.${key}: findes kun i ${a === undefined ? "baseline" : "genskabt"}`); continue; }
      if (a === b) continue;
      const id = `${want.kommune_kode}.${f}.${key}`;
      if (ties.has(id) && close(a, b)) tieDiffs.push({ id, genskabt: a, baseline: b });
      else check("C", false, `${id}: genskabt ${a}, baseline ${b} (skal være bit-identisk)`);
    }
  }
  for (const [mode, field] of Object.entries(MODES)) {
    const cs = computeCategoryScores(got[field]);
    const wantCs = want.category_scores[mode];
    check("C", cs.length === wantCs.length, `${want.kommune_kode}: antal kategorier afviger (${mode})`);
    cs.forEach((c, i) => {
      compared++;
      const w = wantCs[i];
      check("C", c.categoryId === w.categoryId && c.indicatorCount === w.indicatorCount && c.hasData === w.hasData && c.score === w.score,
        `${want.kommune_kode} ${mode} ${w.categoryId}: genskabt score ${c.score}, baseline ${w.score} (skal være bit-identisk)`);
    });
  }
}

// ─── D: metode-tekster ───
const { INDICATOR_RATIONALES, SOCIAL_METHODS, ECO_METHODS } = await loadMetodeData(root);
const METHODS = { ...SOCIAL_METHODS, ...ECO_METHODS };
const TITLES = { scoring: "Beregning", boundary: "Grænseværdi", limitations: "Begrænsninger" };
const dimFiles = fs.readdirSync(path.join(contentDir, "dimensioner")).map((f) => f.slice(0, -3)).sort();
check("D", canon(dimFiles) === canon(Object.keys(METHODS).sort()), "dimensioner/-filer dækker ikke præcis de gamle metode-poster");
for (const [id, m] of Object.entries(METHODS)) {
  const md = fs.readFileSync(path.join(contentDir, "dimensioner", `${id}.md`), "utf-8");
  const sections = Object.fromEntries(md.split(/^## /m).filter(Boolean).map((s) => {
    const nl = s.indexOf("\n");
    return [s.slice(0, nl), s.slice(nl).trim()];
  }));
  for (const [field, title] of Object.entries(TITLES)) {
    if (m[field] === undefined) check("D", !(title in sections), `${id}: ekstra afsnit ${title}`);
    else check("D", sections[title] !== undefined && mdUnescape(sections[title]) === m[field], `${id}.${field}: markdown giver ikke den gamle tekst ordret tilbage`);
  }
  if (m.csvFile) check("D", sections.Datafil === "`" + m.csvFile + "`", `${id}.csvFile afviger`);
  const refs = DIMENSION_DEFS.find((d) => d.id === id)?.references ?? [];
  check("D", canon(refs.map((r) => REFERENCES[r])) === canon(m.boundarySources ?? []), `${id}: kildehenvisninger afviger`);
}
const indFiles = fs.readdirSync(path.join(contentDir, "indikatorer")).map((f) => f.slice(0, -3)).sort();
check("D", canon(indFiles) === canon(Object.keys(INDICATOR_RATIONALES).sort()), "indikatorer/-filer dækker ikke præcis de gamle begrundelser");
for (const [id, text] of Object.entries(INDICATOR_RATIONALES)) {
  const md = fs.readFileSync(path.join(contentDir, "indikatorer", `${id}.md`), "utf-8").trim();
  check("D", mdUnescape(md) === text, `${id}: begrundelsen er ikke ordret`);
}
// Håndkonverterede generelle afsnit: samme ord i samme rækkefølge som JSX'en.
const jsx = fs.readFileSync(path.join(root, "webapp", "app", "metode", "page.tsx"), "utf-8");
const between = (a, b) => {
  const s = jsx.indexOf(a);
  const e = b ? jsx.indexOf(b, s + a.length) : jsx.length;
  if (s < 0 || e < 0) throw new Error(`markør ikke fundet: ${a}`);
  return jsx.slice(s + a.length, e);
};
const GENERELT_JSX = {
  intro: between("{/* MVP / prototype-banner */}", "{/* Baseline-hierarki */}"),
  "baseline-hierarki": between("{/* Baseline-hierarki */}", "{/* Quick navigation */}"),
  scoring: between("{/* General scoring explanation */}", "{/* Ærlig note: absolutte vs relative grænser */}"),
  "oekologiske-graenser": between("{/* Ærlig note: absolutte vs relative grænser */}", "{/* === SOCIALT FUNDAMENT === */}"),
  databehandling: between("{/* Data processing note */}", null),
};
const words = (s) => (s.toLowerCase().match(/[\p{L}\p{N}]+/gu) ?? []);
const jsxWords = (s) => words(s.replace(/\{\/\*[\s\S]*?\*\/\}/g, " ").replace(/\{" "\}/g, " ").replace(/<[^>]+>/g, " ")
  .replace(/&apos;/g, "'").replace(/&quot;/g, '"').replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">"));
const mdWords = (s) => words(mdUnescape(s).replace(/\[([^\]]+)\]\([^)]+\)/g, "$1"));
const genFiles = fs.readdirSync(path.join(contentDir, "generelt")).map((f) => f.slice(0, -3)).sort();
check("D", canon(genFiles) === canon([...METODE_GENERELT].sort()), "generelt/-filer matcher ikke METODE_GENERELT");
for (const id of METODE_GENERELT) {
  const a = jsxWords(GENERELT_JSX[id]);
  const b = mdWords(fs.readFileSync(path.join(contentDir, "generelt", `${id}.md`), "utf-8"));
  const i = a.findIndex((w, n) => w !== b[n]);
  check("D", a.length === b.length && i === -1, `generelt/${id}.md: ordfølgen afviger fra JSX ved ord ${i} ("${a[i]}" / "${b[i]}"), ${a.length} vs ${b.length} ord`);
}

// ─── T: transforms (informativt) ───
const decimalsOf = (s) => (s.includes(".") ? s.length - s.indexOf(".") - 1 : 0);
const transformResults = [];
for (const d of INDICATOR_DEFS.filter((x) => x.transform.type !== "none")) {
  const ref = manifest.indicators[d.id].reference_value;
  let ok = 0;
  let total = 0;
  let worst = 0;
  for (const r of readSnapshot(path.join(snapDir, `${d.id}.csv`))) {
    if (r.raw_value === "" || r.ratio === "") continue;
    total++;
    const raw = parseFloat(r.raw_value);
    const stored = parseFloat(r.ratio);
    const got = applyTransform(d, raw, ref);
    // Tolerance: afrunding af ratio + forplantet afrunding af råværdien + 10000/x-konvertering af gamle inverse ratios.
    const slope = d.transform.type === "complement_100" ? 1 : raw === 0 ? 0 : Math.abs(stored / raw);
    // + én enhed på sidste decimal: Pythons afrunding og referenceværdiens præcision (udledt af afrundede data).
    let tol = 1.5 * 10 ** -d.decimals + slope * 0.5 * 10 ** -decimalsOf(r.raw_value) + Math.abs(stored) * 1e-5 + 1e-9;
    if (d.legacy.ratioColIsInverse) tol += (stored * stored * 0.005) / 10000;
    const dev = got === null ? Infinity : Math.abs(got - stored);
    if (dev <= tol) ok++;
    worst = Math.max(worst, dev / tol);
  }
  transformResults.push({ id: d.id, type: d.transform.type, ok, total, worst });
}

// ─── Afledte dataår pr. dimension vs. de håndskrevne i den gamle metode-side (til rapporten) ───
const derivedYears = [];
for (const dim of DIMENSION_DEFS) {
  const years = INDICATOR_DEFS.filter((d) => d.dimensionId === dim.id && d.kind !== "context" && (d.kind === "ecological" || d.scoredInCategory))
    .map((d) => manifest.indicators[d.id].data_year);
  const all = years.flatMap((y) => y.split("-").map(Number)).filter(Number.isFinite);
  const range = all.length === 0 ? "-" : Math.min(...all) === Math.max(...all) ? `${Math.min(...all)}` : `${Math.min(...all)}-${Math.max(...all)}`;
  derivedYears.push({ id: dim.id, gammel: METHODS[dim.id]?.dataYear ?? "-", udledt: range });
}

// ─── Udskrift ───
console.log("Fase 1-verifikation");
console.log(`  A rundtur:     ${rebuilt.size} rækker genskabt mod ${master.length} i master-CSV, alle 10 kolonner`);
console.log(`    godkendte enhedskonflikter (registret bruger UI'ets enhed): ${unitConflicts.size}`);
for (const [id, u] of unitConflicts) console.log(`      ${id.padEnd(24)} master "${u.master}"  ->  registret "${u.registret}"`);
console.log(`  B metadata:    ${pairs.length} konstant-sæt sammenlignet med fase 0-baseline`);
console.log(`  C værdier:     ${compared} værdier sammenlignet med parity_baseline, bit-identiske undtagen ${tieDiffs.length} gennemsnit præcis på x,xx5 (±0,01):`);
console.log(`      ${tieDiffs.map((t) => `${t.id.replace(".eco_ratios.", " ")} ${t.baseline}->${t.genskabt}`).join(", ")}`);
console.log(`  D metode:      ${Object.keys(METHODS).length} dimensioner + ${Object.keys(INDICATOR_RATIONALES).length} begrundelser ordret, ${METODE_GENERELT.length} generelle afsnit ordfølge-tjekket`);
console.log(`  E integritet:  ${regIds.length} indikatorer, ${usedFns.size} edge functions, ${KOMMUNER.length} kommuner`);
const tFull = transformResults.filter((t) => t.ok === t.total);
console.log(`  T transforms:  ${tFull.length}/${transformResults.length} indikatorer genskabes fuldt fra råværdi + reference`);
for (const t of transformResults.filter((x) => x.ok !== x.total)) console.log(`      ${t.id.padEnd(24)} ${t.type.padEnd(22)} ${t.ok}/${t.total} rækker, værste afvigelse ${t.worst.toFixed(1)}x tolerance`);
console.log("  Dataår pr. dimension (håndskrevet i gammel metode-side -> udledt af manifest):");
for (const y of derivedYears) console.log(`      ${y.id.padEnd(18)} ${String(y.gammel).padEnd(72)} -> ${y.udledt}`);

if (errors.length > 0) {
  console.error(`\nVERIFIKATION FEJLET - ${errors.length} fejl:`);
  for (const g of ["A", "B", "C", "D", "E"]) {
    const ge = errors.filter((e) => e.startsWith(`[${g}]`));
    if (ge.length === 0) continue;
    console.error(`  ${g}: ${ge.length} fejl`);
    for (const e of ge.slice(0, 4)) console.error("    " + e);
    if (ge.length > 4) console.error(`    ... og ${ge.length - 4} mere`);
  }
  process.exit(1);
}
console.log("\nA-E: 0 fejl");
