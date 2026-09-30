"use client";

// Grafen ved retningspilen: kommunens og hele landets tal år for år.
//
// Grafen bygges FØRST, når nogen peger på pilen (ScoreBars.tsx, TrendMarker): komponenten monteres
// kun, mens tooltippen er åben. Siden rummer kun tal (TrendPost.serie, sat af data.ts::medTidsserier),
// aldrig tegninger, så der ikke er noget at holde ajour, når data opdateres.
//
// Farverne følger dataviz-reglerne: kommunen er det, siden handler om, og får den ene accentfarve;
// landet er sammenligningen og er grå og stiplet, så de to kan skelnes uden farve. Ingen af dem er en
// vurderingsfarve - grøn, gul og rød hører til pilen. Tekst har aldrig seriens farve: den står i
// tekstfarver, og en linjenøgle ved siden af bærer identiteten.

import {
  TREND_LABEL,
  formatTal,
  trendPilOpad,
  type TrendEndepunkter,
  type TrendKontekst,
  type TrendPost,
  type TrendSerie,
} from "@/lib/shared";
import { akseTicks, formatAendring, formatSerieVaerdi, linjeStykker } from "@/lib/graf";

const KOMMUNE = "#2a78d6";
const LAND = "#6b7280";
const GITTER = "#e5e7eb";
const AKSE = "#d1d5db";
const FLADE = "#ffffff";

const M = { b: 288, h: 108, l: 46, r: 12, t: 8, nede: 22 };

// Op til så mange punkter tegnes hvert år med en prik, så en kort serie (Sundhedsprofilens to bølger,
// valgene hvert fjerde år) viser, hvilke år der faktisk er målt, i stedet for en linje, der ligner en
// kontinuerlig udvikling.
const MAX_PUNKTER_MED_PRIK = 6;

const fmt = (v: number) => v.toFixed(1);

function Serie({
  aar, vaerdier, x, y, farve, stiplet, prikker,
}: {
  aar: number[];
  vaerdier: (number | null)[];
  x: (a: number) => number;
  y: (v: number) => number;
  farve: string;
  stiplet: boolean;
  prikker: boolean;
}) {
  const stykker = linjeStykker(aar, vaerdier, x, y);
  return (
    <>
      {stykker.map((st, i) =>
        st.length === 1 ? (
          <circle key={i} cx={fmt(st[0][0])} cy={fmt(st[0][1])} r={2.5} fill={farve} />
        ) : (
          <path
            key={i}
            d={st.map(([px, py], j) => `${j ? "L" : "M"}${fmt(px)} ${fmt(py)}`).join(" ")}
            fill="none" stroke={farve} strokeWidth={2} strokeLinejoin="round"
            strokeLinecap={stiplet ? "butt" : "round"}
            strokeDasharray={stiplet ? "4 3" : undefined}
          />
        )
      )}
      {prikker && stykker.filter((st) => st.length > 1).flat().map(([px, py], i) => (
        <circle key={`p${i}`} cx={fmt(px)} cy={fmt(py)} r={2.5} fill={farve} />
      ))}
    </>
  );
}

/** Slutpunktet af en serie: en prik med en ring i fladens farve, så den kan ses, hvor de to linjer krydser. */
function Slutpunkt({
  aar, vaerdier, x, y, farve,
}: {
  aar: number[];
  vaerdier: (number | null)[];
  x: (a: number) => number;
  y: (v: number) => number;
  farve: string;
}) {
  for (let i = vaerdier.length - 1; i >= 0; i--) {
    const v = vaerdier[i];
    if (v !== null) {
      return <circle cx={fmt(x(aar[i]))} cy={fmt(y(v))} r={4} fill={farve} stroke={FLADE} strokeWidth={2} />;
    }
  }
  return null;
}

/** Kommunens og landets serie som ét SVG: en akse, to linjer, runde akseværdier og årstal. Ingen tal
 *  ved hvert punkt - tallene står i forklaringen under grafen. */
function Graf({ serie }: { serie: TrendSerie }) {
  const { aar, kommune, land } = serie;
  const tal = [...kommune, ...(land ?? [])].filter((v): v is number => v !== null);
  const aarMedTal = aar.filter((_, i) => kommune[i] !== null || land?.[i] != null);
  if (tal.length < 2 || aarMedTal.length < 2) return null;

  const { ticks, dec } = akseTicks(Math.min(...tal), Math.max(...tal));
  const lo = ticks[0];
  const hi = ticks[ticks.length - 1];
  const plotB = M.b - M.l - M.r;
  const plotH = M.h - M.t - M.nede;
  const foerste = aarMedTal[0];
  const sidste = aarMedTal[aarMedTal.length - 1];
  const x = (a: number) => M.l + (plotB * (a - foerste)) / (sidste - foerste);
  const y = (v: number) => M.t + plotH * (1 - (v - lo) / (hi - lo));

  // Årstal: hvert målt år, når der er få; ellers første, sidste og et i midten.
  const aarsmaerker = new Set<number>(aarMedTal.length <= 5 ? aarMedTal : [foerste, sidste]);
  if (aarMedTal.length > 5 && sidste - foerste >= 6) aarsmaerker.add(Math.round((foerste + sidste) / 2));
  const prikker = kommune.filter((v) => v !== null).length <= MAX_PUNKTER_MED_PRIK;

  const beskrivelse = `${serie.kommuneNavn}${land ? " og hele landet" : ""}, ${foerste} til ${sidste}`;
  return (
    <svg
      viewBox={`0 0 ${M.b} ${M.h}`} width={M.b} height={M.h} role="img"
      aria-label={beskrivelse} className="block max-w-full"
    >
      <title>{beskrivelse}</title>
      {ticks.map((tk) => (
        <g key={tk}>
          <line x1={M.l} x2={M.b - M.r} y1={fmt(y(tk))} y2={fmt(y(tk))}
            stroke={tk === lo ? AKSE : GITTER} strokeWidth={1} />
          <text x={M.l - 6} y={fmt(y(tk) + 3.5)} textAnchor="end" fontSize={10} className="fill-gray-500">
            {formatTal(tk, dec)}
          </text>
        </g>
      ))}
      {[...aarsmaerker].map((a) => (
        <g key={a}>
          <line x1={fmt(x(a))} x2={fmt(x(a))} y1={M.t + plotH} y2={M.t + plotH + 3} stroke={AKSE} strokeWidth={1} />
          <text x={fmt(x(a))} y={M.t + plotH + 14} textAnchor="middle" fontSize={10} className="fill-gray-500">
            {a}
          </text>
        </g>
      ))}
      {land && <Serie aar={aar} vaerdier={land} x={x} y={y} farve={LAND} stiplet prikker={prikker} />}
      <Serie aar={aar} vaerdier={kommune} x={x} y={y} farve={KOMMUNE} stiplet={false} prikker={prikker} />
      {land && <Slutpunkt aar={aar} vaerdier={land} x={x} y={y} farve={LAND} />}
      <Slutpunkt aar={aar} vaerdier={kommune} x={x} y={y} farve={KOMMUNE} />
    </svg>
  );
}

/** En linjenøgle i forklaringen: en kort streg i seriens stil. Nøglen er en streg og ikke en firkant,
 *  fordi det er en linje, den står for. */
function Noegle({ farve, stiplet }: { farve: string; stiplet: boolean }) {
  return (
    <svg width={18} height={8} viewBox="0 0 18 8" aria-hidden="true" className="shrink-0">
      <line x1={1} x2={17} y1={4} y2={4} stroke={farve} strokeWidth={2}
        strokeLinecap={stiplet ? "butt" : "round"} strokeDasharray={stiplet ? "4 3" : undefined} />
    </svg>
  );
}

function Raekke({
  noegle, navn, e, enhed,
}: {
  noegle: React.ReactNode;
  navn: string;
  e: TrendEndepunkter;
  enhed: string;
}) {
  if (e.vaerdiStart === null || e.vaerdiSlut === null) return null;
  const aend = formatAendring(e.pct);
  return (
    <p className="flex items-baseline gap-1.5">
      <span className="self-center">{noegle}</span>
      <span className="text-gray-500">{navn}</span>
      <span className="font-semibold text-gray-900 tabular-nums">
        {formatSerieVaerdi(e.vaerdiStart, enhed)} &rarr; {formatSerieVaerdi(e.vaerdiSlut, enhed)}
      </span>
      {aend && <span className="text-gray-500 tabular-nums">{aend}</span>}
    </p>
  );
}

// Vurderingens farver følger pilen: form og tekst bærer den, farven forstærker.
const VURDERING: Record<TrendPost["retning"], { ikon: string; tekst: string }> = {
  rigtig: { ikon: "text-emerald-600", tekst: "text-emerald-800" },
  tempo: { ikon: "text-amber-500", tekst: "text-amber-800" },
  forkert: { ikon: "text-red-500", tekst: "text-red-700" },
  stagneret: { ikon: "text-gray-400", tekst: "text-gray-600" },
  kontekst: { ikon: "text-gray-400", tekst: "text-gray-600" },
  ingen: { ikon: "text-gray-300", tekst: "text-gray-500" },
};

function VurderingsIkon({ trend, kontekst }: { trend: TrendPost; kontekst: TrendKontekst }) {
  return (
    <svg width={12} height={12} viewBox="0 0 12 12" aria-hidden="true" className={`shrink-0 ${VURDERING[trend.retning].ikon}`}>
      {trend.retning === "stagneret" ? (
        <line x1={1.5} y1={6} x2={10.5} y2={6} stroke="currentColor" strokeWidth={2} strokeLinecap="round" />
      ) : (
        <path d={trendPilOpad(trend, kontekst) ? "M6 1.5 L10.5 9 L1.5 9 Z" : "M6 10.5 L1.5 3 L10.5 3 Z"} fill="currentColor" />
      )}
    </svg>
  );
}

/** Tekst til skærmlæsere: det samme som kortet viser, uden tegningen. Uden navn, hvor teksten
 *  ved siden af allerede nævner indikatoren (dimensionens "Bestemt af: ..."). */
export function trendSerieTekst(serie: TrendSerie, medNavn = true): string {
  const e = serie.kommuneEndepunkter;
  const del = (navn: string, p: TrendEndepunkter | null) =>
    p && p.vaerdiStart !== null && p.vaerdiSlut !== null
      ? ` ${navn}: ${formatSerieVaerdi(p.vaerdiStart, serie.enhed)} til ${formatSerieVaerdi(p.vaerdiSlut, serie.enhed)}.`
      : "";
  const hoved = `${e.periodeStart} til ${e.periodeSlut}.`;
  return `${medNavn ? `${serie.navn}, ` : ""}${hoved}${del(serie.kommuneNavn, e)}${del("Hele landet", serie.landEndepunkter)}`;
}

/**
 * Indholdet af tooltippen ved en pil, der har en tidsserie: indikatoren, grafen, kommunens og landets
 * tal, vurderingen og hvad den bygger på.
 */
export function TrendKort({ trend, kontekst }: { trend: TrendPost; kontekst: TrendKontekst }) {
  const serie = trend.serie;
  if (!serie) return null;
  const e = serie.kommuneEndepunkter;
  const l = serie.landEndepunkter;
  const foerste = serie.aar[0];
  const sidste = serie.aar[serie.aar.length - 1];
  const middel = /^\d{4}-\d{4}$/.test(e.periodeStart);
  const grundlag = middel
    ? `Tallene er middel af flere år i hver ende (${e.periodeStart} og ${e.periodeSlut}), så ét afvigende år ikke afgør retningen.`
    : `Tallene er første og sidste år (${e.periodeStart} og ${e.periodeSlut}).`;
  const landAndre = l && (l.periodeStart !== e.periodeStart || l.periodeSlut !== e.periodeSlut);

  return (
    <div className="w-[18.5rem] max-w-full text-[11px] leading-snug text-gray-700">
      <p className="text-xs font-semibold text-gray-900">{serie.navn}</p>
      <p className="text-gray-500">{serie.enhed} &middot; {foerste}-{sidste}</p>
      <div className="mt-1.5"><Graf serie={serie} /></div>
      <div className="mt-1.5 space-y-0.5">
        <Raekke noegle={<Noegle farve={KOMMUNE} stiplet={false} />} navn={serie.kommuneNavn} e={e} enhed={serie.enhed} />
        {l && <Raekke noegle={<Noegle farve={LAND} stiplet />} navn="Hele landet" e={l} enhed={serie.enhed} />}
      </div>
      {!serie.land && <p className="mt-1 text-gray-500">Ingen landsserie for denne indikator.</p>}
      <p className={`mt-1.5 flex items-start gap-1.5 font-medium ${VURDERING[trend.retning].tekst}`}>
        <span className="mt-[3px]"><VurderingsIkon trend={trend} kontekst={kontekst} /></span>
        <span>{TREND_LABEL[trend.retning]}</span>
      </p>
      {kontekst !== "indikator" && (
        <p className="mt-1 text-gray-500">Dimensionens pil følger denne indikator: den afgør dimensionens score.</p>
      )}
      <p className="mt-1 text-gray-500">{grundlag}</p>
      {landAndre && (
        <p className="mt-1 text-gray-500">Landets tal er middel af {l.periodeStart} og {l.periodeSlut}.</p>
      )}
      <p className="mt-1 text-gray-500">Kilde: {trend.kilde}.</p>
    </div>
  );
}
