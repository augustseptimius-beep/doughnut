// Typer for registret. Normativ beskrivelse: docs/lovable-migration-spec.md afsnit 3 og 4.3.
// Registret er det ENESTE hjem for metadata om indikatorer, dimensioner og kommuner.
// Dataår, hentetidspunkt og referenceværdier bor IKKE her, men i data/snapshots/_manifest.json.

export type IndicatorKind = "social" | "ecological" | "context";
export type DimensionKind = "social" | "ecological";
export type BaselineType = "absolut" | "relativ";

/**
 * Hvordan en råværdi omsættes til den færdige ratio (spec afsnit 5).
 * Bruges af import og edge functions. Snapshots gemmer altid den færdige ratio,
 * så frontend aldrig selv anvender en transform.
 * Felter mærket "reference" henter deres tal fra manifestets reference_value.
 */
export type Transform =
  | { type: "none" }                                                    // ratio kan ikke udledes af råværdien (kontekst)
  | { type: "relative_national"; direction: "direct" | "inverse" }      // direct: raw/ref*100, inverse: ref/raw*100. ref = nationalt tal (R23)
  | { type: "abs_target"; target: number }                              // raw/target*100 (R2)
  | { type: "abs_limit"; limit: number }                                // raw/limit*100 (R16, R17)
  | { type: "cba_div3" }                                                // raw/3*100 (R5)
  | { type: "recycling_eu_target"; target: number }                     // target/raw*100, raw=0 -> null (R4)
  | { type: "target_over_pct"; target: number; zeroValue: number }      // target/raw*100, raw=0 -> zeroValue (R18)
  | { type: "ref_over_raw" }                                            // ref/raw*100, ref poolet (R19)
  | { type: "ref_over_pct_pooled"; zeroValue: number }                  // ref/raw*100, raw=0 -> zeroValue, ref poolet (R20)
  | { type: "pct_over_ref_floor"; floor: number }                       // raw=0 -> 0, ellers max(floor, raw/ref*100), ref poolet (R21)
  | { type: "complement_100" };                                         // 100 - raw (R24)

/** Hvordan indikatoren opdateres (spec afsnit 9). */
export type UpdateMethod =
  | { method: "api"; fn: string }          // edge function i supabase/functions/<fn>
  | { method: "frozen"; recipe: string | null }; // opskrift i tools/python/, null = ingen opskrift findes

/** Hvor indikatoren lå i den gamle pipeline. Bruges af import til at genkende gamle *_scores.csv-filer. */
export interface LegacySource {
  csv: string;                        // filnavn i det gamle data/
  ratioCol: string | null;
  rawCol: string;
  keyColumn: "kommune_kode" | "kommune_navn" | "kommune";
  ratioColIsInverse?: boolean;        // ratio-kolonnen er invers og konverteres med 10000/x (R3)
}

export interface IndicatorDef {
  id: string;                         // = snapshot-filnavn
  name: string;
  kind: IndicatorKind;
  dimensionId: string;
  scoredInCategory: boolean;          // social: indgår i kategoriscoren (R8). Andre kinds: false
  sortOrder: number;                  // rækkefølge inden for dimensionen
  unit: string;
  sourceName: string;                 // kort kildetekst, fx "DST HISBK"
  sourceUrl?: string;
  sourceTable?: string;               // fx "HISBK", "GS/KARA/KARAGNS"
  inverse?: boolean;                  // social: lavere råværdi er bedre
  absoluteScore?: boolean;            // social: omskaleres ikke af baseline-toggle (R9, R10)
  baselineLevel?: 1 | 2 | 3;
  absoluteTarget?: string;            // visningstekst
  rawKey?: string;                    // ecological: nøgle i KommuneData.rawValues
  ratioKey?: string | null;           // ecological: nøgle for sub-ratio i rawValues
  boundary?: string;                  // ecological: grænsetekst
  lowerIsBetter?: boolean;            // ecological
  baselineType?: BaselineType;        // ecological
  transform: Transform;
  ratioCap?: number;                  // klip ratio hertil (R1, R6)
  decimals: number;                   // afrunding af ratio
  nameKeyed?: boolean;                // kildedata matches på kommunenavn
  expectedCoverage: number;           // forventet antal kommuner med data
  update: UpdateMethod;
  legacy: LegacySource;
  active: boolean;
}

export interface DimensionDef {
  id: string;
  kind: DimensionKind;
  name: string;
  shortName?: string;                 // ecological: label i SVG-ringen
  description?: string;
  sourceUrl?: string;                 // ecological
  sourceLabel?: string;               // ecological
  unit?: string;                      // ecological
  boundary?: string;                  // ecological
  aggregation: "worst_of" | "average"; // ecological: R7. social: altid "average" (R8)
  sortOrder: number;
  references?: string[];              // id'er i REFERENCES
}

export interface Reference {
  label: string;
  url: string;
}

export interface KommuneDef {
  kode: string;
  navn: string;
  gruppe: 1 | 2 | 3 | 4 | 5;          // DST KOMMUNEGRUPPER_V1_2018
}

/** data/snapshots/_manifest.json (spec 4.2) */
export interface ManifestEntry {
  data_year: string;
  method: "api" | "import" | "frozen";
  source_ref: string;
  fetched_at: string;
  row_count: number;
  reference_value: number | null;
  sha256: string;
}

export interface Manifest {
  schema_version: number;
  indicators: Record<string, ManifestEntry>;
}
