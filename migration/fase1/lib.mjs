// Fælles hjælpefunktioner for fase 1 (convert.mjs og verify.mjs).

import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

export const sha256 = (data) => createHash("sha256").update(data).digest("hex");

/**
 * Indlæser metode-sidens datastrukturer (INDICATOR_RATIONALES, SOCIAL_METHODS, ECO_METHODS).
 * De står som ren TypeScript før JSX-delen i webapp/app/metode/page.tsx; den del skæres ud og importeres,
 * så teksterne hentes ordret uden at parse dem selv.
 */
export async function loadMetodeData(root) {
  const src = fs.readFileSync(path.join(root, "webapp", "app", "metode", "page.tsx"), "utf-8");
  const start = src.indexOf("interface MethodSource");
  const end = src.indexOf("function IndicatorCard");
  if (start < 0 || end < start) throw new Error("kunne ikke finde metode-datastrukturerne i metode/page.tsx");
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "fase1-"));
  try {
    const file = path.join(tmp, "metode_data.ts");
    fs.writeFileSync(file, src.slice(start, end) + "\nexport { INDICATOR_RATIONALES, SOCIAL_METHODS, ECO_METHODS };\n");
    return await import(pathToFileURL(file).href);
  } finally {
    fs.rmSync(tmp, { recursive: true });
  }
}

export const git = (cwd, args) => execFileSync("git", args, { cwd, encoding: "utf-8" });

/** Læser master_indicators.csv. Afviser rækker med forkert kolonneantal (felter må ikke indeholde komma). */
export function readMasterCsv(file) {
  const lines = fs.readFileSync(file, "utf-8").replace(/\r/g, "").trim().split("\n");
  const header = lines[0].split(",");
  return lines.slice(1).map((line, n) => {
    const cols = line.split(",");
    if (cols.length !== header.length) throw new Error(`${file} linje ${n + 2}: ${cols.length} kolonner, forventede ${header.length}`);
    return Object.fromEntries(header.map((h, i) => [h, cols[i]]));
  });
}

/** Læser en snapshot-fil (spec 4.1). Simpel parser er nok her: konverteringen skriver aldrig komma i felter. */
export function readSnapshot(file) {
  const lines = fs.readFileSync(file, "utf-8").split("\n");
  if (lines.at(-1) === "") lines.pop();
  if (lines[0] !== "kommune_kode,kommune_navn,raw_value,ratio") throw new Error(`${file}: forkert header`);
  return lines.slice(1).map((line) => {
    const [kommune_kode, kommune_navn, raw_value, ratio, ...rest] = line.split(",");
    if (rest.length > 0 || ratio === undefined) throw new Error(`${file}: forkert antal kolonner i "${line}"`);
    return { kommune_kode, kommune_navn, raw_value, ratio };
  });
}

// ─── Markdown: escape så en almindelig tekst renderes ordret, og så escapingen kan vendes præcist ───
// Escaper kun tegn der ellers ville blive fortolket. Enkelt-tilde escapes, fordi GFM (GitHub og
// remark-gfm) gennemstreger tekst mellem to "~", og metode-teksterne bruger "~" som "cirka".

export function mdEscape(text) {
  if (text.includes("\n")) throw new Error("mdEscape forventer tekst på én linje");
  let s = text
    .replace(/\\/g, "\\\\")
    .replace(/[*~`[\]<]/g, (c) => "\\" + c)
    .replace(/(?<![\p{L}\p{N}])_|_(?![\p{L}\p{N}])/gu, "\\_")
    .replace(/&(?=#?[A-Za-z0-9]+;)/g, "\\&");
  // Tegn der kun betyder noget i starten af en linje.
  s = s.replace(/^([#>+=-])/, "\\$1").replace(/^(\d+)([.)])/, "$1\\$2");
  return s;
}

export function mdUnescape(md) {
  return md.replace(/\\([!-/:-@[-`{-~])/g, "$1");
}
