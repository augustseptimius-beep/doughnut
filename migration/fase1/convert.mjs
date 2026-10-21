// Fase 1 i docs/lovable-migration-spec.md: engangskonvertering til "git er sandheden".
//
// Læser det nuværende site og skriver frøet til det nye Lovable-repo i migration/lovable/:
//   data/snapshots/<id>.csv + _manifest.json   fra data/master_indicators.csv
//   registry/{indicators,dimensions,kommuner,references,settings}.ts
//                                              fra webapp/lib/shared.ts + scripts/build_master_csv.py
//   content/metode/{dimensioner,indikatorer}/*.md
//                                              fra datastrukturerne i webapp/app/metode/page.tsx
//
// Håndskrevne filer røres ikke: registry/{types,transforms,legacy}.ts og content/metode/generelt/.
// Indhold konverteres 1:1. Fejl og forældede tekster rettes IKKE her, de listes i rapporten.
//
// Kør fra repo-roden (se migration/README.md). Samme input giver byte-identisk output.

import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { INDICATORS, SOCIAL_CATEGORIES, ECOLOGICAL_DIMENSIONS, KOMMUNEGRUPPE, KOMMUNEGRUPPE_NAVNE, DOUGHNUT_EDITION_YEAR, DOUGHNUT_DEFAULT_DATA_YEAR } from "../../webapp/lib/shared.ts";
import { mdEscape, sha256, readMasterCsv, git, loadMetodeData } from "./lib.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..", "..");
const out = path.join(root, "migration", "lovable");
const baseline = JSON.parse(fs.readFileSync(path.join(root, "migration", "baseline", "metadata_baseline.json"), "utf-8"));

const fail = (msg) => {
  console.error(`\nKONVERTERING AFVIST: ${msg}`);
  process.exit(1);
};
const assert = (cond, msg) => cond || fail(msg);

// ─── 0. Datafrysning: kilderne skal være de samme som fotografiet fra fase 0 ───
const frozen = [
  ["data/master_indicators.csv", "master_indicators_csv_sha256"],
  ["webapp/lib/shared.ts", "lib_shared_ts_sha256"],
  ["webapp/lib/data.ts", "lib_data_ts_sha256"],
];
for (const [file, key] of frozen) {
  const actual = sha256(fs.readFileSync(path.join(root, file)));
  assert(actual === baseline.source[key], `${file} er ændret siden fase 0-baseline. Kør migration/export_baseline.mjs igen først.`);
}

// ─── 1. Kilder ───
const master = readMasterCsv(path.join(root, "data", "master_indicators.csv"));
const valueRows = master.filter((r) => !r.indicator_id.startsWith("_dim_"));
const rowsById = new Map();
for (const r of valueRows) {
  if (!rowsById.has(r.indicator_id)) rowsById.set(r.indicator_id, []);
  rowsById.get(r.indicator_id).push(r);
}
const one = (id, col) => {
  const vals = new Set(rowsById.get(id).map((r) => r[col]));
  assert(vals.size === 1, `${id}: kolonnen ${col} har flere værdier i master-CSV (${[...vals].join(" | ")})`);
  return [...vals][0];
};

const build = JSON.parse(
  execFileSync(
    "python3",
    ["-I", "-c", "import sys,json; sys.path.insert(0, sys.argv[1]); import build_master_csv as b; print(json.dumps({'social': b.SOCIAL_INDICATORS, 'eco': b.ECO_SUB_INDICATORS, 'context': b.CONTEXT_INDICATORS, 'average': sorted(b.AVERAGE_DIMENSIONS)}))", path.join(root, "scripts")],
    { encoding: "utf-8" }
  )
);
const buildById = new Map([...build.social, ...build.eco, ...build.context].map((b) => [b.id, b]));
const ecoRawKeyMap = baseline.eco_raw_key_map;

const { INDICATOR_RATIONALES, SOCIAL_METHODS, ECO_METHODS } = await loadMetodeData(root);

// ─── 2. Faste tabeller (de eneste manuelle beslutninger i konverteringen, jf. spec afsnit 5 og 9) ───

// Spec 9.1/9.2: gammel CSV -> edge function (api) eller Python-opskrift (frozen).
const UPDATE_BY_CSV = {
  "doughnut_scores.csv": { method: "api", fn: "fetch-doughnut" },
  "faellesskaber_scores.csv": { method: "api", fn: "fetch-social-new" },
  "lokalsamfund_scores.csv": { method: "api", fn: "fetch-social-new" },
  "mobilitet_scores.csv": { method: "api", fn: "fetch-social-new" },
  "velfaerd_extra_scores.csv": { method: "api", fn: "fetch-social-new" },
  "bolig_extra_scores.csv": { method: "api", fn: "fetch-social-extra" },
  "lokalsamfund_extra_scores.csv": { method: "api", fn: "fetch-social-extra" },
  "samskabelse_extra_scores.csv": { method: "api", fn: "fetch-social-extra" },
  "sundhed_extra_scores.csv": { method: "api", fn: "fetch-social-extra" },
  "uddannelse_extra_scores.csv": { method: "api", fn: "fetch-social-extra" },
  "medicin_scores.csv": { method: "api", fn: "fetch-sundhed" },
  "laegekontakt_scores.csv": { method: "api", fn: "fetch-sundhed" },
  "boerneovervaeght_scores.csv": { method: "api", fn: "fetch-sundhed" },
  "hjemsyg_scores.csv": { method: "api", fn: "fetch-sundhed" },
  "uvm_scores.csv": { method: "api", fn: "fetch-udvidelse" },
  "lighed_scores.csv": { method: "api", fn: "fetch-udvidelse" },
  "underretning_scores.csv": { method: "api", fn: "fetch-udvidelse" },
  "bolig_wc_scores.csv": { method: "api", fn: "fetch-udvidelse" },
  "ligestilling_scores.csv": { method: "api", fn: "fetch-ligestilling" },
  "democracy_scores.csv": { method: "api", fn: "fetch-demokrati" },
  "climate_scores.csv": { method: "api", fn: "fetch-klimaregnskabet" },
  "klimatilpasning_scores.csv": { method: "api", fn: "fetch-klimatilpasning" },
  "arealanvendelse_scores.csv": { method: "api", fn: "fetch-arealanvendelse" },
  "vandindvinding_scores.csv": { method: "api", fn: "fetch-vandindvinding" },
  "naeringsstoffer_scores.csv": { method: "api", fn: "fetch-eco-dst" },
  "forurening_scores.csv": { method: "api", fn: "fetch-eco-dst" },
  "ve_kapacitet_scores.csv": { method: "api", fn: "fetch-ve" },
  "fjernvarme_mix_scores.csv": { method: "api", fn: "fetch-fjernvarme" },
  "bolig_fossil_scores.csv": { method: "api", fn: "fetch-bolig-fossil" },
  "luftforurening_scores.csv": { method: "frozen", recipe: "tools/python/fetch_luftforurening_data.py" },
  "biodiversitet_scores.csv": { method: "frozen", recipe: "tools/python/fetch_biodiversitet_data.py" },
  "n_landbrug_scores.csv": { method: "frozen", recipe: "tools/python/fetch_naeringsstoffer_landbrug.py" },
  "vp3_vandkvalitet_scores.csv": { method: "frozen", recipe: "tools/python/fetch_vp3_vandkvalitet.py" },
  "pesticider_scores.csv": { method: "frozen", recipe: "tools/python/fetch_pesticider_data.py" },
  "nitrat_scores.csv": { method: "frozen", recipe: "tools/python/fetch_nitrat_data.py" },
  "cba_2023_estimate.csv": { method: "frozen", recipe: null },
  "consumption_scores.csv": { method: "frozen", recipe: null },
};

// Spec afsnit 5: transform pr. øko-indikator. Formlerne er verificeret mod data i verify.mjs.
const ECO_TRANSFORM = {
  klimapaavirkning: { type: "abs_limit", limit: 3 },
  luftkvalitet_no2: { type: "abs_limit", limit: 10 },
  luftkvalitet_pm25: { type: "abs_limit", limit: 5 },
  cirkularitet_recycling: { type: "recycling_eu_target", target: 65 },
  cirkularitet_waste: { type: "relative_national", direction: "direct" },
  naer_nitrogen: { type: "relative_national", direction: "direct" },
  naer_phosphorus: { type: "relative_national", direction: "direct" },
  naer_landbrug: { type: "ref_over_raw" },
  overfladevand: { type: "ref_over_pct_pooled", zeroValue: 300 },
  bio_vasentlig: { type: "target_over_pct", target: 30, zeroValue: 999 },
  bio_uerstattelig: { type: "target_over_pct", target: 10, zeroValue: 999 },
  forbrug_co2: { type: "cba_div3" },
  pesticider: { type: "pct_over_ref_floor", floor: 101 },
  nitrat: { type: "abs_limit", limit: 6 },
  vandindvinding: { type: "relative_national", direction: "direct" },
  areal_intensiv: { type: "relative_national", direction: "direct" },
  areal_bebygget: { type: "relative_national", direction: "direct" },
};

// Kontekst-indikatorer har ingen navne i shared.ts (UI'et har dem hårdkodet i ScoreBars.tsx). Nye navne.
const CONTEXT_NAMES = {
  ctx_ve_kw_per_indb: "Lokal VE-kapacitet (sol + landvind)",
  ctx_ve_sol_mw: "Solcellekapacitet",
  ctx_ve_vind_mw: "Landvindkapacitet",
  ctx_fjv_biomasse: "Fjernvarmens brændselsmix: biomasse",
  ctx_fjv_affald: "Fjernvarmens brændselsmix: affald",
  ctx_fjv_fossil: "Fjernvarmens brændselsmix: fossil",
  ctx_fjv_ren: "Fjernvarmens brændselsmix: reelt vedvarende",
  ctx_fossil_direkte: "Direkte fossil opvarmning (olie/gas)",
  ctx_fossil_via_fjv: "Fossil opvarmning via fjernvarme",
};

const GENERELT = ["intro", "baseline-hierarki", "scoring", "oekologiske-graenser", "databehandling"];

// ─── 3. Afledte tal fra data: afrunding og referenceværdier ───
const decimalsOf = (s) => (s.includes(".") ? s.length - s.indexOf(".") - 1 : 0);
const median = (xs) => {
  const s = [...xs].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
};

/** Referenceværdien der ligger bag ratioerne, udledt fra rækker hvor ratio ikke er klippet eller sat. */
function inferReference(id, transform, cap) {
  const pts = rowsById
    .get(id)
    .filter((r) => r.ratio !== "" && r.raw_value !== "")
    .map((r) => [parseFloat(r.raw_value), parseFloat(r.ratio)])
    .filter(([raw, ratio]) => raw > 0 && ratio > 0 && ratio !== cap);
  let refs;
  switch (transform.type) {
    case "relative_national":
      refs = pts.map(([raw, ratio]) => (transform.direction === "direct" ? (raw * 100) / ratio : (raw * ratio) / 100));
      break;
    case "ref_over_raw":
    case "ref_over_pct_pooled":
      refs = pts.map(([raw, ratio]) => (raw * ratio) / 100);
      break;
    case "pct_over_ref_floor":
      refs = pts.filter(([, ratio]) => ratio > transform.floor).map(([raw, ratio]) => (raw * 100) / ratio);
      break;
    default:
      return null;
  }
  assert(refs.length >= 10, `${id}: for få rækker (${refs.length}) til at udlede referenceværdi`);
  return Number(median(refs).toPrecision(6));
}

// ─── 4. Indikatorer ───
const defs = [];
const kommuneNavn = new Map();
for (const r of valueRows) kommuneNavn.set(r.kommune_kode, r.kommune_navn);

function common(id, b) {
  const rows = rowsById.get(id);
  assert(rows, `${id}: ingen rækker i master-CSV`);
  const update = UPDATE_BY_CSV[b.csv];
  assert(update, `${id}: ingen opdateringsmetode for ${b.csv}`);
  const keyColumn = b.navn_key ? "kommune_navn" : b.special === "cba_navn_key" ? "kommune" : "kommune_kode";
  const legacy = { csv: b.csv, ratioCol: b.ratio_col ?? null, rawCol: b.raw_col, keyColumn };
  if (b.inverse_ratio) legacy.ratioColIsInverse = true;
  return {
    decimals: Math.max(0, ...rows.filter((r) => r.ratio !== "").map((r) => decimalsOf(r.ratio))),
    expectedCoverage: rows.length,
    update,
    legacy,
  };
}

// Social: i INDICATORS-rækkefølge.
const categoryOf = new Map();
for (const c of SOCIAL_CATEGORIES) c.indicatorIds.forEach((id, i) => categoryOf.set(id, { cat: c.id, pos: i }));
const socialBuildIds = new Set(build.social.map((b) => b.id));
assert(INDICATORS.length === socialBuildIds.size && INDICATORS.every((i) => socialBuildIds.has(i.id)), "INDICATORS og SOCIAL_INDICATORS i build_master_csv.py dækker ikke de samme id'er");
let unscoredPos = 1000;
for (const ind of INDICATORS) {
  const b = buildById.get(ind.id);
  const inCat = categoryOf.get(ind.id);
  if (inCat) assert(inCat.cat === b.dimension, `${ind.id}: kategori ${inCat.cat} i shared.ts, dimension ${b.dimension} i build`);
  assert(one(ind.id, "data_year") === ind.dataYear, `${ind.id}: dataår ${ind.dataYear} i shared.ts, ${one(ind.id, "data_year")} i master-CSV`);
  const transform = ind.id === "education" ? { type: "abs_target", target: b.abs_target }
    : ind.id === "bolig_fossil" ? { type: "complement_100" }
    : { type: "relative_national", direction: ind.inverse ? "inverse" : "direct" };
  if (ind.id === "education") assert(b.abs_target === 95, "education: abs_target forventes 95");
  defs.push({
    id: ind.id,
    name: ind.name,
    kind: "social",
    dimensionId: b.dimension,
    scoredInCategory: !!inCat,
    sortOrder: inCat ? inCat.pos : unscoredPos++,
    unit: ind.rawUnit,
    sourceName: b.source,
    sourceUrl: ind.source,
    sourceTable: ind.table,
    inverse: ind.inverse,
    absoluteScore: ind.absoluteScore,
    baselineLevel: ind.baselineLevel,
    absoluteTarget: ind.absoluteTarget,
    transform,
    // R1: build_master_csv.py capper sociale ratios ved 150, MEN ikke i navn-nøgle-grenen (vejr_skader).
    // Gengives 1:1; uoverensstemmelsen står i fase 1-rapporten.
    ratioCap: b.navn_key ? undefined : 150,
    ...common(ind.id, b),
    nameKeyed: b.navn_key ? true : undefined,
    active: true,
  });
}

// Økologisk: i ECOLOGICAL_DIMENSIONS-rækkefølge, sub-indikatorer i deres rækkefølge.
const idByRawKey = new Map(Object.entries(ecoRawKeyMap).map(([id, k]) => [k.rawKey, id]));
for (const dim of ECOLOGICAL_DIMENSIONS) {
  (dim.subIndicators ?? []).forEach((s, pos) => {
    const id = idByRawKey.get(s.rawKey);
    assert(id, `subIndicator ${s.rawKey} har ingen post i ECO_RAW_KEY_MAP`);
    const b = buildById.get(id);
    assert(b && b.category === "ecological", `${id}: mangler i ECO_SUB_INDICATORS`);
    assert(b.dimension === dim.id, `${id}: dimension ${dim.id} i shared.ts, ${b.dimension} i build`);
    assert((ecoRawKeyMap[id].ratioKey ?? undefined) === s.ratioKey, `${id}: ratioKey afviger mellem ECO_RAW_KEY_MAP og subIndicators`);
    assert(ECO_TRANSFORM[id], `${id}: ingen transform defineret`);
    defs.push({
      id,
      name: s.label,
      kind: "ecological",
      dimensionId: dim.id,
      scoredInCategory: false,
      sortOrder: pos,
      unit: s.unit,
      sourceName: b.source,
      rawKey: s.rawKey,
      ratioKey: s.ratioKey ?? null,
      boundary: s.boundary,
      lowerIsBetter: s.lowerIsBetter,
      baselineType: s.baselineType,
      transform: ECO_TRANSFORM[id],
      ratioCap: b.cap,
      ...common(id, b),
      nameKeyed: b.special === "cba_navn_key" ? true : undefined,
      active: true,
    });
  });
}
assert(defs.filter((d) => d.kind === "ecological").length === build.eco.length, "ikke alle ECO_SUB_INDICATORS er dækket af subIndicators");

// Kontekst.
build.context.forEach((b, pos) => {
  assert(CONTEXT_NAMES[b.id], `${b.id}: intet navn i CONTEXT_NAMES`);
  defs.push({
    id: b.id,
    name: CONTEXT_NAMES[b.id],
    kind: "context",
    dimensionId: b.dimension,
    scoredInCategory: false,
    sortOrder: pos,
    unit: b.unit,
    sourceName: b.source,
    transform: { type: "none" },
    ...common(b.id, b),
    decimals: 0,
    active: true,
  });
});

const defIds = new Set(defs.map((d) => d.id));
for (const id of rowsById.keys()) assert(defIds.has(id), `${id}: findes i master-CSV men ikke i registret`);
assert(defIds.size === defs.length, "dublet-id i registret");

// ─── 5. Dimensioner og referencer ───
const slug = (s) =>
  s.toLowerCase().replace(/æ/g, "ae").replace(/ø/g, "oe").replace(/å/g, "aa").normalize("NFKD").replace(/[^\x00-\x7f]/g, "")
    .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 48).replace(/-+$/, "");
const REFERENCES = {};
const METHODS = { ...SOCIAL_METHODS, ...ECO_METHODS };
const refIdsFor = (dimId) => {
  const srcs = METHODS[dimId]?.boundarySources;
  if (!srcs?.length) return undefined;
  return srcs.map((src) => {
    const id = slug(src.label);
    assert(!REFERENCES[id] || REFERENCES[id].url === src.url, `reference-id ${id} kolliderer`);
    REFERENCES[id] = { label: src.label, url: src.url };
    return id;
  });
};

const dimensions = [
  ...SOCIAL_CATEGORIES.map((c, i) => ({
    id: c.id, kind: "social", name: c.name, description: c.description, aggregation: "average", sortOrder: i, references: refIdsFor(c.id),
  })),
  ...ECOLOGICAL_DIMENSIONS.map((d, i) => ({
    id: d.id, kind: "ecological", name: d.name, shortName: d.shortName, description: d.description,
    sourceUrl: d.source, sourceLabel: d.sourceLabel, unit: d.unit, boundary: d.boundary,
    aggregation: build.average.includes(d.id) ? "average" : "worst_of", sortOrder: i, references: refIdsFor(d.id),
  })),
];
for (const d of defs) assert(dimensions.some((x) => x.id === d.dimensionId), `${d.id}: ukendt dimension ${d.dimensionId}`);

// ─── 6. Kommuner ───
const kommuner = [...kommuneNavn.entries()]
  .sort(([a], [b]) => (a < b ? -1 : 1))
  .map(([kode, navn]) => {
    assert(KOMMUNEGRUPPE[kode], `kommune ${kode} mangler kommunegruppe`);
    return { kode, navn, gruppe: KOMMUNEGRUPPE[kode] };
  });
assert(kommuner.length === 98, `forventede 98 kommuner, fandt ${kommuner.length}`);

// ─── 7. Snapshots og manifest ───
const snapDir = path.join(out, "data", "snapshots");
fs.rmSync(snapDir, { recursive: true, force: true });
fs.mkdirSync(snapDir, { recursive: true });

const gitInfo = new Map();
const lastCommit = (csv) => {
  if (!gitInfo.has(csv)) {
    const [sha, date] = git(root, ["log", "-1", "--format=%h %cI", "--", `data/${csv}`]).trim().split(" ");
    assert(sha && date, `ingen git-historik for data/${csv}`);
    gitInfo.set(csv, { sha, date });
  }
  return gitInfo.get(csv);
};

const manifest = { schema_version: 1, indicators: {} };
for (const d of defs) {
  const rows = [...rowsById.get(d.id)].sort((a, b) => (a.kommune_kode < b.kommune_kode ? -1 : 1));
  const csv = "kommune_kode,kommune_navn,raw_value,ratio\n" + rows.map((r) => `${r.kommune_kode},${r.kommune_navn},${r.raw_value},${r.ratio}`).join("\n") + "\n";
  fs.writeFileSync(path.join(snapDir, `${d.id}.csv`), csv);
  const { sha, date } = lastCommit(d.legacy.csv);
  manifest.indicators[d.id] = {
    data_year: one(d.id, "data_year"),
    method: "frozen",
    source_ref: `fase1:data/${d.legacy.csv}@${sha}`,
    fetched_at: date,
    row_count: rows.length,
    reference_value: inferReference(d.id, d.transform, d.ratioCap),
    sha256: sha256(csv),
  };
}
fs.writeFileSync(path.join(snapDir, "_manifest.json"), JSON.stringify(manifest, null, 2) + "\n");

// ─── 8. Registret som TypeScript ───
const IDENT = /^[A-Za-z_$][A-Za-z0-9_$]*$/;
function ts(value, indent = "") {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  const inner = indent + "  ";
  if (Array.isArray(value)) {
    if (value.every((v) => v === null || typeof v !== "object")) return `[${value.map((v) => ts(v)).join(", ")}]`;
    return `[\n${value.map((v) => inner + ts(v, inner)).join(",\n")},\n${indent}]`;
  }
  const entries = Object.entries(value).filter(([, v]) => v !== undefined);
  const key = (k) => (IDENT.test(k) ? k : JSON.stringify(k));
  const flat = entries.every(([, v]) => v === null || typeof v !== "object");
  const oneLine = `{ ${entries.map(([k, v]) => `${key(k)}: ${ts(v)}`).join(", ")} }`;
  if (flat && oneLine.length <= 110) return oneLine;
  return `{\n${entries.map(([k, v]) => `${inner}${key(k)}: ${ts(v, inner)}`).join(",\n")},\n${indent}}`;
}
const header = (what) =>
  `// ${what}\n// Oprettet af fase 1-konverteringen (migration/fase1/convert.mjs) fra det gamle site.\n// Fra nu af er denne fil kilden: ret her (eller via Lovables chat), ikke i det gamle repo.\n// Typer og felternes betydning: ./types.ts. Normativ beskrivelse: docs/lovable-migration-spec.md.\n\n`;

const regDir = path.join(out, "registry");
fs.mkdirSync(regDir, { recursive: true });
const writeReg = (file, body) => fs.writeFileSync(path.join(regDir, file), body);

// Nøglerækkefølge pr. indikator: identitet, visning, kilde, social, øko, beregning, drift.
const ORDER = ["id", "name", "kind", "dimensionId", "scoredInCategory", "sortOrder", "unit", "sourceName", "sourceUrl", "sourceTable",
  "inverse", "absoluteScore", "baselineLevel", "absoluteTarget", "rawKey", "ratioKey", "boundary", "lowerIsBetter", "baselineType",
  "transform", "ratioCap", "decimals", "nameKeyed", "expectedCoverage", "update", "legacy", "active"];
const ordered = (d) => {
  const keys = Object.keys(d);
  assert(keys.every((k) => ORDER.includes(k)), `ukendt felt i ${d.id}: ${keys.filter((k) => !ORDER.includes(k))}`);
  return Object.fromEntries(ORDER.filter((k) => k in d).map((k) => [k, d[k]]));
};

writeReg("indicators.ts",
  header("Alle indikatorer: sociale (i INDICATORS-rækkefølge), økologiske sub-indikatorer og kontekst.") +
  `// Historik fra det gamle register (shared.ts):\n` +
  `// - car_access (familier med bilrådighed) blev fjernet i 2026: "flere biler = bedre" er skævt i en doughnut-ramme.\n` +
  `//   Rådata ligger i det gamle repo (data/mobilitet_scores.csv).\n` +
  `// - bolig_fossil blev flyttet fra Bolig til Energi i 2026 (opvarmning er et energispørgsmål).\n` +
  `// - housing_no_wc og housing_no_bath har data men indgår ikke i Bolig-scoren (scoredInCategory: false). Uafklaret (spec B16).\n\n` +
  `import type { IndicatorDef } from "./types.ts";\n\nexport const INDICATOR_DEFS: IndicatorDef[] = ${ts(defs.map(ordered))};\n`);

writeReg("dimensions.ts",
  header("Sociale kategorier og økologiske dimensioner.") +
  `import type { DimensionDef } from "./types.ts";\n\nexport const DIMENSION_DEFS: DimensionDef[] = ${ts(dimensions)};\n`);

writeReg("kommuner.ts",
  header("De 98 kommuner. Gruppe = DST KOMMUNEGRUPPER_V1_2018 (1 Hovedstad, 2 Storby, 3 Provinsby, 4 Opland, 5 Land).") +
  `import type { KommuneDef } from "./types.ts";\n\nexport const KOMMUNER: KommuneDef[] = [\n${kommuner.map((k) => "  " + ts(k)).join(",\n")},\n];\n`);

writeReg("references.ts",
  header("Kildehenvisninger, refereret fra dimensions.ts via id.") +
  `import type { Reference } from "./types.ts";\n\nexport const REFERENCES: Record<string, Reference> = ${ts(REFERENCES)};\n`);

writeReg("settings.ts",
  header("Globale indstillinger.") +
  `// "Doughnut-år" er modellens edition. Standard-dataår er det seneste helårsdata.\n` +
  `// Regel: en 2024-Doughnut bruger seneste tilgængelige helårsdata (typisk 2023-tal).\n` +
  `export const DOUGHNUT_EDITION_YEAR = ${JSON.stringify(DOUGHNUT_EDITION_YEAR)};\n` +
  `export const DOUGHNUT_DEFAULT_DATA_YEAR = ${JSON.stringify(DOUGHNUT_DEFAULT_DATA_YEAR)};\n\n` +
  `export const KOMMUNEGRUPPE_NAVNE: Record<number, string> = ${ts(KOMMUNEGRUPPE_NAVNE)};\n\n` +
  `// Rækkefølgen af de generelle afsnit på metode-siden (content/metode/generelt/<id>.md).\n` +
  `export const METODE_GENERELT: string[] = ${ts(GENERELT)};\n`);

// ─── 9. Metode-tekster ───
const contentDir = path.join(out, "content", "metode");
for (const sub of ["dimensioner", "indikatorer"]) {
  fs.rmSync(path.join(contentDir, sub), { recursive: true, force: true });
  fs.mkdirSync(path.join(contentDir, sub), { recursive: true });
}
const SECTIONS = [["scoring", "Beregning"], ["boundary", "Grænseværdi"], ["limitations", "Begrænsninger"]];
for (const [dimId, m] of Object.entries(METHODS)) {
  assert(dimensions.some((d) => d.id === dimId), `metode-tekst for ukendt dimension ${dimId}`);
  const parts = SECTIONS.filter(([f]) => m[f]).map(([f, title]) => `## ${title}\n\n${mdEscape(m[f])}\n`);
  if (m.csvFile) {
    assert(!m.csvFile.includes("`"), `${dimId}: csvFile indeholder backtick`);
    parts.push(`## Datafil\n\n\`${m.csvFile}\`\n`);
  }
  fs.writeFileSync(path.join(contentDir, "dimensioner", `${dimId}.md`), parts.join("\n"));
}
for (const [id, text] of Object.entries(INDICATOR_RATIONALES)) {
  assert(defIds.has(id), `rationale for ukendt indikator ${id}`);
  fs.writeFileSync(path.join(contentDir, "indikatorer", `${id}.md`), mdEscape(text) + "\n");
}

// ─── Opsummering ───
const count = (k) => defs.filter((d) => d.kind === k).length;
console.log("Fase 1-konvertering skrevet til migration/lovable/");
console.log(`  indikatorer:  ${defs.length} (${count("social")} sociale, ${count("ecological")} økologiske, ${count("context")} kontekst)`);
console.log(`  snapshots:    ${defs.length} filer, ${valueRows.length} rækker (master-CSV uden ${master.length - valueRows.length} _dim_-rækker)`);
console.log(`  dimensioner:  ${dimensions.length} (${SOCIAL_CATEGORIES.length} sociale, ${ECOLOGICAL_DIMENSIONS.length} økologiske), referencer: ${Object.keys(REFERENCES).length}`);
console.log(`  kommuner:     ${kommuner.length}`);
console.log(`  metode-tekst: ${Object.keys(METHODS).length} dimensioner, ${Object.keys(INDICATOR_RATIONALES).length} indikatorer`);
console.log(`  opdatering:   ${defs.filter((d) => d.update.method === "api").length} api, ${defs.filter((d) => d.update.method === "frozen").length} frosne`);
console.log(`  referencer i manifest: ${Object.values(manifest.indicators).filter((m) => m.reference_value !== null).length} indikatorer`);
