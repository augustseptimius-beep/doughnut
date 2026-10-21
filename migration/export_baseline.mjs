// Fase 0 i docs/lovable-migration-spec.md: "fotografiet" af det nuværende site.
//
// Kører den NUVÆRENDE kode (webapp/lib/data.ts og shared.ts, uændret) og gemmer hvad den
// producerer, så det nye system kan sammenlignes tal for tal (spec afsnit 12).
//
//   migration/baseline/parity_baseline.json   alle værdier, baselines og kategoriscorer
//   migration/baseline/metadata_baseline.json alle konstanter + afledte typer + ECO_RAW_KEY_MAP
//   migration/baseline/url_liste.txt          alle adresser sitet udgiver
//
// Kør fra repo-roden (se migration/README.md). Ingen installation, ingen tidsstempler:
// samme input giver byte-identisk output.

import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { loadData, getAllKommuner } from "../webapp/lib/data.ts";
import {
  INDICATORS,
  SOCIAL_CATEGORIES,
  ECOLOGICAL_DIMENSIONS,
  KOMMUNEGRUPPE,
  KOMMUNEGRUPPE_NAVNE,
  DOUGHNUT_EDITION_YEAR,
  DOUGHNUT_DEFAULT_DATA_YEAR,
  computeCategoryScores,
  indicatorBaselineType,
  categoryBaselineType,
  dimensionBaselineType,
} from "../webapp/lib/shared.ts";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const outDir = path.join(here, "baseline");
const webappDir = path.join(root, "webapp");

// data.ts finder master-CSV'en via process.cwd()/../data, så vi står i webapp/.
process.chdir(webappDir);

const problems = [];
const fail = (msg) => problems.push(msg);
const sha256 = (buf) => createHash("sha256").update(buf).digest("hex");
const sortKeys = (o) => Object.fromEntries(Object.keys(o).sort().map((k) => [k, o[k]]));

function assertPlain(value, where) {
  if (value === undefined) fail(`undefined i ${where} (JSON ville tabe nøglen)`);
  else if (typeof value === "number" && !Number.isFinite(value)) fail(`ikke-endeligt tal i ${where}`);
  else if (Array.isArray(value)) value.forEach((v, i) => assertPlain(v, `${where}[${i}]`));
  else if (value && typeof value === "object") {
    for (const [k, v] of Object.entries(value)) assertPlain(v, `${where}.${k}`);
  }
}

// ─── Kilder og hashes (viser senere om baseline stadig passer til master-CSV'en) ───
const csvPath = path.join(root, "data", "master_indicators.csv");
const csvBytes = fs.readFileSync(csvPath);
const sharedSrc = fs.readFileSync(path.join(webappDir, "lib", "shared.ts"));
const dataSrcBytes = fs.readFileSync(path.join(webappDir, "lib", "data.ts"));
const dataSrc = dataSrcBytes.toString("utf-8");

// ─── 1. Værdier: præcis hvad loadData() leverer i dag ───
loadData(); // varmer cachen; getAllKommuner() filtrerer "000" fra som generateStaticParams
const kommuner = [...getAllKommuner()].sort((a, b) => (a.kommune_kode < b.kommune_kode ? -1 : 1));

const MODES = { avg: "ratios", top10: "top10_ratios", kommunegruppe: "group_ratios" };

// Kun kategoriens samlede resultat. Scorerne pr. indikator inde i kategorien er identiske med
// ratios/top10_ratios/group_ratios (verificeret: 0 afvigelser over 14.112 værdier) og gemmes ikke to gange.
function categoryScoresFor(ratios) {
  return computeCategoryScores(ratios).map((c) => ({
    categoryId: c.categoryId,
    categoryName: c.categoryName,
    score: c.score,
    indicatorCount: c.indicatorCount,
    hasData: c.hasData,
  }));
}

const kommuneRecords = kommuner.map((k) => ({
  kommune_kode: k.kommune_kode,
  kommune_navn: k.kommune_navn,
  kommunegruppe: KOMMUNEGRUPPE[k.kommune_kode] ?? null,
  ratios: sortKeys(k.ratios),
  top10_ratios: sortKeys(k.top10_ratios),
  group_ratios: sortKeys(k.group_ratios),
  eco_ratios: sortKeys(k.eco_ratios),
  rawValues: sortKeys(k.rawValues),
  social_avg: k.social_avg,
  overall_avg: k.overall_avg,
  category_scores: Object.fromEntries(
    Object.entries(MODES).map(([mode, field]) => [mode, categoryScoresFor(k[field])])
  ),
}));
assertPlain(kommuneRecords, "kommuner");

if (kommuneRecords.length !== 98) fail(`forventede 98 kommuner, fandt ${kommuneRecords.length}`);
const koderIData = new Set(kommuneRecords.map((k) => k.kommune_kode));
const koderIGrupper = new Set(Object.keys(KOMMUNEGRUPPE));
for (const kode of koderIData) if (!koderIGrupper.has(kode)) fail(`kommune ${kode} mangler i KOMMUNEGRUPPE`);
for (const kode of koderIGrupper) if (!koderIData.has(kode)) fail(`KOMMUNEGRUPPE-kode ${kode} har ingen data`);

// ─── 2. ECO_RAW_KEY_MAP (ikke eksporteret fra data.ts, læses ud af kildeteksten) ───
const mapStart = dataSrc.indexOf("const ECO_RAW_KEY_MAP");
const mapEnd = dataSrc.indexOf("\n};", mapStart);
if (mapStart < 0 || mapEnd < 0) fail("kunne ikke finde ECO_RAW_KEY_MAP i data.ts");
const ecoRawKeyMap = {};
const entryRe = /^\s*([a-z0-9_]+):\s*\{\s*rawKey:\s*"([^"]+)",\s*ratioKey:\s*(null|"[^"]+")\s*\}/gm;
for (const m of dataSrc.slice(mapStart, mapEnd).matchAll(entryRe)) {
  ecoRawKeyMap[m[1]] = { rawKey: m[2], ratioKey: m[3] === "null" ? null : m[3].slice(1, -1) };
}

// Krydstjek: kortet skal dække præcis de nøgler ECOLOGICAL_DIMENSIONS.subIndicators peger på.
const subs = ECOLOGICAL_DIMENSIONS.flatMap((d) => d.subIndicators ?? []);
const mapRaw = new Set(Object.values(ecoRawKeyMap).map((e) => e.rawKey));
const mapRatio = new Set(Object.values(ecoRawKeyMap).map((e) => e.ratioKey).filter(Boolean));
for (const s of subs) {
  if (!mapRaw.has(s.rawKey)) fail(`subIndicator rawKey "${s.rawKey}" findes ikke i ECO_RAW_KEY_MAP`);
  if (s.ratioKey && !mapRatio.has(s.ratioKey)) fail(`subIndicator ratioKey "${s.ratioKey}" findes ikke i ECO_RAW_KEY_MAP`);
}
const subRaw = new Set(subs.map((s) => s.rawKey));
for (const k of mapRaw) if (!subRaw.has(k)) fail(`ECO_RAW_KEY_MAP rawKey "${k}" bruges ikke af nogen subIndicator`);

// ─── 3. Afstemning mod master-CSV: taber indlæsningen noget i dag? ───
const lines = csvBytes.toString("utf-8").replace(/\r/g, "").trim().split("\n");
const header = lines[0].split(",").map((h) => h.trim());
const csvRows = lines.slice(1).map((line, n) => {
  const cols = line.split(",");
  if (cols.length !== header.length) fail(`CSV linje ${n + 2}: ${cols.length} kolonner, forventede ${header.length} (komma i felt?)`);
  return Object.fromEntries(header.map((h, i) => [h, (cols[i] ?? "").trim()]));
});
const num = (s) => (s === "" || Number.isNaN(parseFloat(s)) ? null : parseFloat(s));

const seen = new Set();
let expectRatios = 0;
let expectRaw = 0;
let expectDim = 0;
const unmappedEco = new Map();
const categories = new Map();
for (const r of csvRows) {
  categories.set(r.category, (categories.get(r.category) ?? 0) + 1);
  const key = `${r.kommune_kode}|${r.indicator_id}`;
  if (seen.has(key)) fail(`dublet i CSV: ${key}`);
  seen.add(key);

  if (r.indicator_id.startsWith("_dim_")) {
    if (num(r.ratio) !== null) expectDim++;
  } else if (r.category === "context") {
    if (num(r.raw_value) !== null) expectRaw++;
  } else if (r.category === "social") {
    if (num(r.ratio) !== null) expectRatios++;
    if (num(r.raw_value) !== null) expectRaw++;
  } else if (r.category === "ecological") {
    const keys = ecoRawKeyMap[r.indicator_id];
    if (!keys) {
      unmappedEco.set(r.indicator_id, (unmappedEco.get(r.indicator_id) ?? 0) + 1);
      continue;
    }
    if (num(r.raw_value) !== null) expectRaw++;
    if (keys.ratioKey && num(r.ratio) !== null) expectRaw++;
  } else {
    fail(`ukendt category i CSV: "${r.category}" (indikator ${r.indicator_id})`);
  }
}
for (const [id, n] of unmappedEco) fail(`eco-indikator "${id}" (${n} rækker) mangler i ECO_RAW_KEY_MAP og tabes stille af loadData()`);

const nonNull = (objs) => objs.reduce((n, o) => n + Object.values(o).filter((v) => v !== null).length, 0);
const actual = {
  ratios: nonNull(kommuneRecords.map((k) => k.ratios)),
  rawValues: nonNull(kommuneRecords.map((k) => k.rawValues)),
  eco_ratios: nonNull(kommuneRecords.map((k) => k.eco_ratios)),
};
if (actual.ratios !== expectRatios) fail(`ratios: ${actual.ratios} værdier i eksport, ${expectRatios} forventet fra CSV`);
if (actual.rawValues !== expectRaw) fail(`rawValues: ${actual.rawValues} værdier i eksport, ${expectRaw} forventet fra CSV`);
if (actual.eco_ratios !== expectDim) fail(`eco_ratios: ${actual.eco_ratios} værdier i eksport, ${expectDim} forventet fra CSV`);

// ─── 4. Metadata ───
const source = {
  master_indicators_csv_sha256: sha256(csvBytes),
  master_indicators_csv_data_rows: csvRows.length,
  lib_shared_ts_sha256: sha256(sharedSrc),
  lib_data_ts_sha256: sha256(dataSrcBytes),
};

const metadata = {
  schema_version: 1,
  source,
  settings: { DOUGHNUT_EDITION_YEAR, DOUGHNUT_DEFAULT_DATA_YEAR },
  INDICATORS,
  SOCIAL_CATEGORIES,
  ECOLOGICAL_DIMENSIONS,
  KOMMUNEGRUPPE,
  KOMMUNEGRUPPE_NAVNE,
  eco_raw_key_map: ecoRawKeyMap,
  derived: {
    indicator_baseline_type: Object.fromEntries(INDICATORS.map((i) => [i.id, indicatorBaselineType(i)])),
    category_baseline_type: Object.fromEntries(
      SOCIAL_CATEGORIES.map((c) => [
        c.id,
        categoryBaselineType(c.indicatorIds.map((id) => INDICATORS.find((i) => i.id === id)).filter(Boolean)),
      ])
    ),
    dimension_baseline_type: Object.fromEntries(ECOLOGICAL_DIMENSIONS.map((d) => [d.id, dimensionBaselineType(d)])),
  },
};
assertPlain(metadata, "metadata");

// Kategori-indikatorer uden INDICATORS-post ville give undefined i computeCategoryScores.
for (const c of SOCIAL_CATEGORIES) {
  for (const id of c.indicatorIds) if (!INDICATORS.some((i) => i.id === id)) fail(`kategori ${c.id}: indikator "${id}" findes ikke i INDICATORS`);
}

// ─── 5. URL-liste: fra koden (som generateStaticParams), krydstjekket mod webapp/out/ ───
const STATIC_PAGES = ["/", "/metode", "/om", "/artikel/planetaere-graenser"];
const urlsFromCode = [...STATIC_PAGES, ...kommuner.map((k) => `/kommune/${encodeURIComponent(k.kommune_navn)}`)];

const outDir2 = path.join(webappDir, "out");
const urlsFromOut = [];
const notes = [];
if (fs.existsSync(outDir2)) {
  const walk = (dir) =>
    fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
      const p = path.join(dir, e.name);
      return e.isDirectory() ? (e.name === "_next" ? [] : walk(p)) : [p];
    });
  for (const file of walk(outDir2)) {
    const rel = path.relative(outDir2, file).split(path.sep).join("/");
    if (!rel.endsWith(".html") || rel === "404.html" || rel === "_not-found.html") continue;
    const segs = rel.slice(0, -5).split("/");
    if (segs[segs.length - 1] === "index") segs.pop();
    const name = segs.map((s) => s.normalize("NFC") === s ? s : (notes.push(`out/ filnavn ikke NFC-normaliseret: ${rel}`), s));
    urlsFromOut.push("/" + name.map(encodeURIComponent).join("/"));
  }
  const a = new Set(urlsFromCode);
  const b = new Set(urlsFromOut);
  for (const u of a) if (!b.has(u)) fail(`URL fra koden findes ikke i webapp/out/: ${u}`);
  for (const u of b) if (!a.has(u)) fail(`URL i webapp/out/ findes ikke i koden: ${u}`);
} else {
  notes.push("webapp/out/ findes ikke, URL-listen er ikke krydstjekket mod et build");
}
const urlList = [...new Set(urlsFromCode)].sort((x, y) => (x < y ? -1 : x > y ? 1 : 0));

// ─── Skriv ───
if (problems.length > 0) {
  console.error(`\nEKSPORT AFVIST - ${problems.length} problem(er):`);
  for (const p of problems) console.error("  - " + p);
  process.exit(1);
}

fs.mkdirSync(outDir, { recursive: true });
const write = (name, content) => {
  const file = path.join(outDir, name);
  fs.writeFileSync(file, content);
  return { name, bytes: Buffer.byteLength(content), sha256: sha256(content).slice(0, 16) };
};
const json = (o) => JSON.stringify(o, null, 2) + "\n";

// Gyldig JSON, men én kommune pr. linje: kompakt nok til at ligge i browser-bundlet,
// og en ændring i én kommune giver én ændret linje i git.
const parityJson =
  `{\n"schema_version": 1,\n"source": ${JSON.stringify(source)},\n"modes": ${JSON.stringify(Object.keys(MODES))},\n` +
  `"kommuner": [\n${kommuneRecords.map((r) => JSON.stringify(r)).join(",\n")}\n]\n}\n`;
JSON.parse(parityJson); // fanger fejl i den håndlavede serialisering

const written = [
  write("parity_baseline.json", parityJson),
  write("metadata_baseline.json", json(metadata)),
  write("url_liste.txt", urlList.join("\n") + "\n"),
];

console.log("Baseline eksporteret");
console.log(`  kommuner:        ${kommuneRecords.length}`);
console.log(`  master-CSV:      ${csvRows.length} rækker, sha256 ${source.master_indicators_csv_sha256.slice(0, 16)}...`);
console.log(`  afstemt mod CSV: ratios ${actual.ratios}, rawValues ${actual.rawValues}, eco_ratios ${actual.eco_ratios} (ingen differens)`);
console.log(`  categories i CSV: ${[...categories].map(([c, n]) => `${c}=${n}`).join(", ")}`);
console.log(`  ECO_RAW_KEY_MAP: ${Object.keys(ecoRawKeyMap).length} poster, dækker ${subs.length} subIndicators`);
console.log(`  URL'er:          ${urlList.length} (${STATIC_PAGES.length} sider + ${urlList.length - STATIC_PAGES.length} kommuner)`);
for (const n of notes) console.log(`  note: ${n}`);
for (const w of written) console.log(`  ${w.name.padEnd(24)} ${String(w.bytes).padStart(8)} bytes  ${w.sha256}`);
