// Globale indstillinger.
// Oprettet af fase 1-konverteringen (migration/fase1/convert.mjs) fra det gamle site.
// Fra nu af er denne fil kilden: ret her (eller via Lovables chat), ikke i det gamle repo.
// Typer og felternes betydning: ./types.ts. Normativ beskrivelse: docs/lovable-migration-spec.md.

// "Doughnut-år" er modellens edition. Standard-dataår er det seneste helårsdata.
// Regel: en 2024-Doughnut bruger seneste tilgængelige helårsdata (typisk 2023-tal).
export const DOUGHNUT_EDITION_YEAR = "2024";
export const DOUGHNUT_DEFAULT_DATA_YEAR = "2023";

export const KOMMUNEGRUPPE_NAVNE: Record<number, string> = {
  "1": "Hovedstadskommuner",
  "2": "Storbykommuner",
  "3": "Provinsbykommuner",
  "4": "Oplandskommuner",
  "5": "Landkommuner",
};

// Rækkefølgen af de generelle afsnit på metode-siden (content/metode/generelt/<id>.md).
export const METODE_GENERELT: string[] = ["intro", "baseline-hierarki", "scoring", "oekologiske-graenser", "databehandling"];
