// Hjælpefunktioner til grafen ved retningspilen (components/TrendGraf.tsx). Rene funktioner uden
// React, så de kan læses og prøves uden at tegne noget.

import { formatTal } from "./shared";

/**
 * Runde akseværdier: det mindste trin i 1, 2, 2,5 og 5 gange en tierpotens, der dækker værdierne
 * med højst fire intervaller. `dec` er antallet af decimaler, trinnet kræver.
 */
export function akseTicks(min: number, max: number): { ticks: number[]; trin: number; dec: number } {
  if (min === max) {
    const d = Math.abs(min) * 0.1 || 1;
    min -= d;
    max += d;
  }
  const span = max - min;
  const start = Math.floor(Math.log10(span / 8));
  for (let e = start; e < start + 6; e++) {
    for (const m of [1, 2, 2.5, 5]) {
      const trin = m * 10 ** e;
      const foerste = Math.floor(min / trin + 1e-9) * trin;
      const sidste = Math.ceil(max / trin - 1e-9) * trin;
      if (Math.round((sidste - foerste) / trin) <= 4) {
        const ticks: number[] = [];
        for (let t = foerste; t <= sidste + trin / 2; t += trin) ticks.push(Number(t.toPrecision(12)));
        const dec = Math.max(0, -Math.floor(Math.log10(trin) + 1e-9), m === 2.5 ? 1 - e : 0);
        return { ticks, trin, dec: Math.min(dec, 6) };
      }
    }
  }
  return { ticks: [min, max], trin: span, dec: 1 };
}

/** Et tal i grafens forklaring: dansk talformat, og færre decimaler jo større tallet er. */
export function formatSerieVaerdi(v: number, enhed: string): string {
  const dec = enhed.startsWith("kr.") || Math.abs(v) >= 1000 ? 0 : Math.abs(v) >= 10 ? 1 : 2;
  return formatTal(v, dec);
}

/** Ændringen i procent med fortegn, som den står i grafens forklaring. */
export function formatAendring(pct: number | null): string | null {
  if (pct === null) return null;
  return `${pct > 0 ? "+" : pct < 0 ? "-" : ""}${formatTal(Math.abs(pct), 1)} %`;
}

/** Linjestykker med huller: et år uden tal afbryder linjen, og et enkeltstående punkt bliver til
 *  et stykke på ét punkt, som tegnes som en prik, så det ikke forsvinder. */
export function linjeStykker(
  aar: number[],
  vaerdier: (number | null)[],
  x: (a: number) => number,
  y: (v: number) => number
): [number, number][][] {
  const stykker: [number, number][][] = [];
  let aktuelt: [number, number][] = [];
  aar.forEach((a, i) => {
    const v = vaerdier[i];
    if (v === null) {
      if (aktuelt.length) stykker.push(aktuelt);
      aktuelt = [];
    } else {
      aktuelt.push([x(a), y(v)]);
    }
  });
  if (aktuelt.length) stykker.push(aktuelt);
  return stykker;
}
