// Omsætter en råværdi til den færdige ratio efter registrets transform (spec afsnit 5).
// Bruges af import og edge functions. Frontend bruger den ikke: snapshots gemmer færdige ratios.
//
// Afrunding: Python round() i de gamle scripts er "round half to even" på binære floats,
// JavaScript er "round half up". Forskellen ligger inden for én enhed på sidste decimal
// og opfanges af valideringens tolerance, ikke her.

import type { IndicatorDef } from "./types.ts";

const roundTo = (x: number, decimals: number) => {
  const f = 10 ** decimals;
  return Math.round(x * f) / f;
};

/**
 * @param reference manifestets reference_value. Kræves af relative_national,
 *   ref_over_raw, ref_over_pct_pooled og pct_over_ref_floor (R22).
 * @returns ratio, eller null hvis ratio ikke kan beregnes.
 */
export function applyTransform(def: IndicatorDef, raw: number | null, reference: number | null): number | null {
  if (raw === null || !Number.isFinite(raw)) return null;
  const t = def.transform;
  const needRef = () => {
    if (reference === null || reference === 0) throw new Error(`${def.id}: transform ${t.type} kræver en referenceværdi (R22)`);
    return reference;
  };

  let ratio: number | null;
  switch (t.type) {
    case "none":
      return null;
    case "relative_national": {
      const ref = needRef();
      // Invers med råværdi 0 giver uendelig ratio, som loftet klipper (det gamle sites adfærd, fx boerneovervaeght = 150).
      if (t.direction === "direct") ratio = (raw / ref) * 100;
      else ratio = raw === 0 ? Infinity : (ref / raw) * 100;
      break;
    }
    case "abs_target":
      ratio = (raw / t.target) * 100;
      break;
    case "abs_limit":
      ratio = (raw / t.limit) * 100;
      break;
    case "cba_div3":
      ratio = (raw / 3) * 100;
      break;
    case "recycling_eu_target":
      ratio = raw === 0 ? null : (t.target / raw) * 100;
      break;
    case "target_over_pct":
      ratio = raw === 0 ? t.zeroValue : (t.target / raw) * 100;
      break;
    case "ref_over_raw": {
      const ref = needRef();
      ratio = raw === 0 ? null : (ref / raw) * 100;
      break;
    }
    case "ref_over_pct_pooled": {
      const ref = needRef();
      ratio = raw === 0 ? t.zeroValue : (ref / raw) * 100;
      break;
    }
    case "pct_over_ref_floor": {
      const ref = needRef();
      ratio = raw === 0 ? 0 : Math.max(t.floor, (raw / ref) * 100);
      break;
    }
    case "complement_100":
      ratio = 100 - raw;
      break;
  }

  if (ratio === null) return null;
  if (def.ratioCap !== undefined && ratio > def.ratioCap) ratio = def.ratioCap;
  if (!Number.isFinite(ratio)) return null;
  return roundTo(ratio, def.decimals);
}

/** Om transformen bruger manifestets reference_value. */
export function usesReference(def: IndicatorDef): boolean {
  return ["relative_national", "ref_over_raw", "ref_over_pct_pooled", "pct_over_ref_floor"].includes(def.transform.type);
}
