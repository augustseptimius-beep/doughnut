// Kildehenvisninger, refereret fra dimensions.ts via id.
// Oprettet af fase 1-konverteringen (migration/fase1/convert.mjs) fra det gamle site.
// Fra nu af er denne fil kilden: ret her (eller via Lovables chat), ikke i det gamle repo.
// Typer og felternes betydning: ./types.ts. Normativ beskrivelse: docs/lovable-migration-spec.md.

import type { Reference } from "./types.ts";

export const REFERENCES: Record<string, Reference> = {
  "fanning-et-al-2022-nature-sustainability": {
    label: "Fanning et al. (2022), Nature Sustainability",
    url: "https://www.nature.com/articles/s41893-021-00799-z",
  },
  "hot-or-cool-institute-2021-1-5-degree-lifestyles": {
    label: "Hot or Cool Institute (2021), 1.5-Degree Lifestyles",
    url: "https://hotorcool.org/1-5-degree-lifestyles-report/",
  },
  "energistyrelsen-global-afrapportering": { label: "Energistyrelsen, Global Afrapportering", url: "https://ens.dk/" },
  "who-air-quality-guidelines-2021": { label: "WHO Air Quality Guidelines 2021", url: "https://www.who.int/publications/i/item/9789240034228" },
  "dce-au-luftkvalitet-2022-sr580": { label: "DCE/AU - Luftkvalitet 2022 (SR580)", url: "https://dce2.au.dk/pub/SR580.pdf" },
  "miljoeportal-wfs-luftkoncentrationer": { label: "Miljøportal WFS - luftkoncentrationer", url: "https://arld-extgeo.miljoeportal.dk/geoserver/wfs" },
};
