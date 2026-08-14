"use client";

import { useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  type KommuneData,
  type DimBaselineType,
  type TrendPost,
  ECOLOGICAL_DIMENSIONS,
  scoreColor,
  scoreBarColor,
  computeCategoryScores,
  categoryBaselineType,
  dimensionBaselineType,
  kommunegruppeNavn,
  TREND_LABEL,
  trendBeskrivelse,
  trendPilOpad,
  type TrendKontekst,
  DOUGHNUT_DEFAULT_DATA_YEAR,
} from "@/lib/shared";
import { useBaseline } from "@/lib/baseline-context";
import type { VurderingScore, VurderingEntry } from "@/lib/vurdering";

// Baseline-mærke vises kun for absolut og blandet; relativ er normen
// (intet mærke, forklaret i ringens legende).
function baselineTag(t: DimBaselineType): string | null {
  if (t === "absolut") return "mod mål";
  if (t === "blandet") return "blandet";
  return null;
}

interface ScoreBarsProps {
  kommune: KommuneData;
  compare?: KommuneData | null;
  ratios?: Record<string, number | null>; // override kommune.ratios (bruges til baseline-skift)
  compareRatios?: Record<string, number | null>; // override compare.ratios
  // Vurderingsmode
  vurderingsMode?: boolean;
  vurderinger?: Record<string, VurderingEntry>;
  onVurderingKlik?: (id: string, navn: string, gruppe: "social" | "ecological") => void;
}

function ecoScoreColor(score: number | null): string {
  if (score === null) return "text-gray-400";
  if (score <= 85) return "text-emerald-600";   // klart under grænsen = godt
  if (score <= 100) return "text-amber-500";    // tæt på grænsen
  return "text-red-500";                         // overshoot
}

function ecoBarColor(score: number | null): string {
  if (score === null) return "bg-gray-200";
  if (score <= 85) return "bg-emerald-500";
  if (score <= 100) return "bg-amber-400";
  return "bg-red-500";
}

// Retningsmarkør: viser om en indikators råværdi bevæger sig i positiv eller
// forkert retning over tid. Skal kunne skelnes uden farve (~8% af mænd er
// farveblinde), derfor bærer FORMEN retningen (pil op/ned/vandret streg/
// skraveret felt) og farven forstærker vurderingen.
// TREND_LABEL og trendBeskrivelse bor i shared.ts, så ScoreBars og
// DoughnutRing altid formulerer retningen ens.
function trendTitle(t: TrendPost, kontekst: TrendKontekst): string {
  const hoved = trendBeskrivelse(t, kontekst);
  return t.noegleIndikator ? `${hoved}. Bestemt af: ${t.noegleIndikator}` : hoved;
}

// Eget tooltip i stedet for SVG's indbyggede <title> - den native title-boks
// har en indbygget forsinkelse på typisk 0,5-1 sekund og opfører sig
// forskelligt fra browser til browser. Dette vises straks ved hover (og ved
// tastaturfokus), via en portal til <body> så det ikke bliver beskåret af
// kortenes egen overflow-hidden.
function TrendMarker({ trend, kontekst = "indikator" }: { trend?: TrendPost; kontekst?: TrendKontekst }) {
  const ref = useRef<SVGSVGElement>(null);
  const [pos, setPos] = useState<{ x: number; y: number; above: boolean } | null>(null);

  const label = !trend || trend.retning === "ingen" ? TREND_LABEL.ingen : trendTitle(trend, kontekst);

  const vis = () => {
    const r = ref.current?.getBoundingClientRect();
    if (!r) return;
    const above = r.top > 48;
    setPos({ x: r.left + r.width / 2, y: above ? r.top - 6 : r.bottom + 6, above });
  };
  const skjul = () => setPos(null);
  const handlers = { onMouseEnter: vis, onMouseLeave: skjul, onFocus: vis, onBlur: skjul };

  let inner: React.ReactNode;
  let farve: string;
  if (!trend || trend.retning === "ingen") {
    farve = "text-gray-300";
    inner = (
      <>
        <rect x="1" y="1" width="10" height="10" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1" />
        <line x1="1" y1="11" x2="11" y2="1" stroke="currentColor" strokeWidth="1" />
        <line x1="1" y1="6" x2="6" y2="1" stroke="currentColor" strokeWidth="1" />
        <line x1="6" y1="11" x2="11" y2="6" stroke="currentColor" strokeWidth="1" />
      </>
    );
  } else if (trend.retning === "stagneret") {
    farve = "text-gray-400";
    inner = <line x1="1.5" y1="6" x2="10.5" y2="6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />;
  } else {
    farve =
      trend.retning === "rigtig" ? "text-emerald-600" :
      trend.retning === "tempo" ? "text-amber-500" :
      trend.retning === "forkert" ? "text-red-500" :
      "text-gray-400"; // kontekst
    inner = trendPilOpad(trend, kontekst)
      ? <path d="M6 1.5 L10.5 9 L1.5 9 Z" fill="currentColor" />
      : <path d="M6 10.5 L1.5 3 L10.5 3 Z" fill="currentColor" />;
  }

  const halvBredde = 110; // halvdelen af max-w-[220px] herunder

  return (
    <>
      <svg
        ref={ref}
        width="12" height="12" viewBox="0 0 12 12"
        className={`${farve} shrink-0 cursor-help`}
        tabIndex={0}
        role="img"
        aria-label={label}
        {...handlers}
      >
        {inner}
      </svg>
      {pos && typeof document !== "undefined" && createPortal(
        <div
          role="tooltip"
          className={`fixed z-[100] -translate-x-1/2 ${pos.above ? "-translate-y-full" : ""} pointer-events-none w-max max-w-[220px] rounded-md bg-gray-900 px-2 py-1.5 text-[11px] leading-snug text-white shadow-lg`}
          style={{
            left: Math.min(Math.max(pos.x, halvBredde + 8), window.innerWidth - halvBredde - 8),
            top: pos.y,
          }}
        >
          {label}
        </div>,
        document.body
      )}
    </>
  );
}

// Kontekst-blok under Klimapåvirkning-dimensionen: sektorfordeling af den
// territoriale udledning, samlet energiforbrug og VE-el selvforsyningsgrad.
// Vises, men indgår IKKE i scoren - sektorerne er blot en opdeling af det
// allerede scorede territoriale tal (eco_klima_raw), ikke et nyt måltal.
function KlimaKontekst({ kommune }: { kommune: KommuneData }) {
  const rv = kommune.rawValues ?? {};
  const total = rv["eco_klima_raw"] ?? null;
  const landbrug = rv["ctx_klima_landbrug"] ?? null;
  const energi = rv["ctx_klima_energi"] ?? null;
  const transport = rv["ctx_klima_transport"] ?? null;
  const energiforbrug = rv["ctx_energiforbrug"] ?? null;
  const veSelvforsyning = rv["ctx_ve_selvforsyning"] ?? null;

  const harSektorer = total !== null && total > 0 && landbrug !== null && energi !== null && transport !== null;
  const segments = harSektorer
    ? [
        { label: "Landbrug", val: Math.max(landbrug as number, 0), color: "bg-amber-700" },
        { label: "Energi", val: Math.max(energi as number, 0), color: "bg-red-500" },
        { label: "Transport", val: Math.max(transport as number, 0), color: "bg-orange-400" },
      ]
    : [];
  const segSum = segments.reduce((s, x) => s + x.val, 0);
  const restPct = harSektorer ? Math.max(0, 100 - (segSum / (total as number)) * 100) : 0;

  if (!harSektorer && energiforbrug === null && veSelvforsyning === null) return null;

  return (
    <div className="px-3 py-3 bg-blue-50/40 border-t border-blue-100">
      <p className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-2">
        Kontekst <span className="font-normal normal-case text-gray-400">- indgår ikke i scoren</span>
      </p>

      {harSektorer && (
        <div className="mb-3">
          <span className="text-sm text-gray-700">Sektorfordeling af territorial udledning</span>
          <div className="mt-1.5 flex h-3 w-full overflow-hidden rounded-full bg-gray-100">
            {segments.map(
              (s) =>
                s.val > 0 && (
                  <div
                    key={s.label}
                    className={s.color}
                    style={{ width: `${(s.val / (total as number)) * 100}%` }}
                    title={`${s.label}: ${s.val.toFixed(1)} ton CO₂e/indb.`}
                  />
                )
            )}
            {restPct > 0.5 && (
              <div className="bg-gray-300" style={{ width: `${restPct}%` }}
                title={`Øvrigt (affald, spildevand, kemisk industri): ${restPct.toFixed(0)}%`} />
            )}
          </div>
          <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1">
            {segments.map((s) => (
              <span key={s.label} className="inline-flex items-center gap-1 text-[11px] text-gray-600">
                <span className={`inline-block w-2 h-2 rounded-sm ${s.color}`} />
                {s.label} {((s.val / (total as number)) * 100).toFixed(0)}%
              </span>
            ))}
            {restPct > 0.5 && (
              <span className="inline-flex items-center gap-1 text-[11px] text-gray-600">
                <span className="inline-block w-2 h-2 rounded-sm bg-gray-300" />
                Øvrigt {restPct.toFixed(0)}%
              </span>
            )}
          </div>
        </div>
      )}

      {(energiforbrug !== null || veSelvforsyning !== null) && (
        <div className="flex flex-wrap gap-x-4 gap-y-2">
          {energiforbrug !== null && (
            <div className="text-sm">
              <span className="text-gray-500">Samlet energiforbrug:</span>{" "}
              <span className="font-medium text-gray-700">{(energiforbrug as number).toFixed(0)} GJ/indb.</span>
            </div>
          )}
          {veSelvforsyning !== null && (
            <div className="text-sm">
              <span className="text-gray-500">VE-el selvforsyningsgrad:</span>{" "}
              <span className="font-medium text-gray-700">{(veSelvforsyning as number).toFixed(0)}%</span>
            </div>
          )}
        </div>
      )}
      <p className="mt-1.5 text-[11px] text-gray-400">
        Sektorfordelingen viser hvad der udgør den territoriale udledning ovenfor. VE-el selvforsyningsgrad kan
        overstige 100% - kommunen kan producere mere sol-/vindstrøm end den selv bruger og eksportere resten til
        nettet.
      </p>
    </div>
  );
}

// Lille farvet prik der viser vurderingsstatus på en dimension
function VurderingPrik({ score }: { score: VurderingScore | undefined }) {
  if (!score) return null;
  const farve =
    score === "groen"
      ? "bg-emerald-500"
      : score === "gul"
      ? "bg-amber-400"
      : "bg-red-500";
  return (
    <span
      className={`inline-block w-2 h-2 rounded-full shrink-0 ${farve}`}
      title={
        score === "groen"
          ? "Vurderet: Positiv påvirkning"
          : score === "gul"
          ? "Vurderet: Ukendt / ingen påvirkning"
          : "Vurderet: Negativ påvirkning"
      }
    />
  );
}

// Kontekst-blok under Energi-dimensionen: lokal VE + fjernvarmens brændselsmix.
// Vises, men indgår IKKE i scoren (se metode-siden for begrundelse).
function EnergiKontekst({ kommune }: { kommune: KommuneData }) {
  const rv = kommune.rawValues ?? {};
  const fossilSamlet = rv["bolig_fossil"] ?? null;
  const fossilDirekte = rv["ctx_fossil_direkte"] ?? null;
  const fossilViaFjv = rv["ctx_fossil_via_fjv"] ?? null;
  const veKw = rv["ctx_ve_kw_per_indb"] ?? null;
  const veSol = rv["ctx_ve_sol_mw"] ?? null;
  const veVind = rv["ctx_ve_vind_mw"] ?? null;
  const bio = rv["ctx_fjv_biomasse"] ?? null;
  const affald = rv["ctx_fjv_affald"] ?? null;
  const fossil = rv["ctx_fjv_fossil"] ?? null;
  const ren = rv["ctx_fjv_ren"] ?? null;
  const fritidFossil = rv["ctx_fritid_fossil"] ?? null;
  const fritidAndel = rv["ctx_fritid_andel"] ?? null;
  const harMix = bio !== null && affald !== null && fossil !== null && ren !== null;
  const harOpdeling = fossilDirekte !== null && fossilViaFjv !== null;
  const harFritid = fritidFossil !== null && fritidAndel !== null;

  const mixSegs = harMix
    ? [
        { label: "Biomasse", pct: bio as number, color: "bg-amber-500" },
        { label: "Affald", pct: affald as number, color: "bg-stone-400" },
        { label: "Fossil", pct: fossil as number, color: "bg-red-500" },
        { label: "Reelt vedvarende", pct: ren as number, color: "bg-emerald-500" },
      ]
    : [];

  return (
    <>
      {/* Opdeling af den scorede samlede fossile opvarmning */}
      {harOpdeling && (
        <div className="px-3 py-2.5 border-b border-gray-100 text-[11px] text-gray-500 leading-relaxed">
          Samlet fossil opvarmning{fossilSamlet !== null ? ` ${(fossilSamlet as number).toFixed(1)}%` : ""} ={" "}
          direkte olie/gas {(fossilDirekte as number).toFixed(1)}% + via fjernvarme {(fossilViaFjv as number).toFixed(1)}%.
          {" "}Målt som andel af helårsboligernes opvarmede areal (m²). Scoret mod målet 0% fossil.
        </div>
      )}
    <div className="px-3 py-3 bg-blue-50/40 border-t border-blue-100">
      <p className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-2">
        Kontekst <span className="font-normal normal-case text-gray-400">- indgår ikke i scoren</span>
      </p>

      {/* Fritidsboliger - holdt uden for scoren */}
      {harFritid && (
        <div className="mb-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-700">Fritidsboliger, fossil opvarmning</span>
            <span className="text-sm font-medium text-gray-700">{(fritidFossil as number).toFixed(1)}%</span>
          </div>
          <p className="mt-0.5 text-[11px] text-gray-400">
            Udgør {(fritidAndel as number).toFixed(1)}% af kommunens samlede boligareal. Holdes uden for scoren:
            sommerhuse er typisk elopvarmede og har derfor lavere fossilandel end helårsboliger. Hvis de talte med,
            ville sommerhuskommuner fremstå kunstigt bedre på et mål der handler om husstandes varmeregninger.
          </p>
        </div>
      )}

      {/* Lokal VE-kapacitet */}
      {veKw !== null && (
        <div className="mb-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-700">Lokal VE-kapacitet (sol + landvind)</span>
            <span className="text-sm font-medium text-gray-700">{veKw} kW/indb.</span>
          </div>
          <p className="mt-0.5 text-[11px] text-gray-400">
            Sol {veSol ?? "–"} MW + landvind {veVind ?? "–"} MW. Leveres til det nationale elnet, ikke kun til kommunens egne husstande.
          </p>
        </div>
      )}

      {/* Fjernvarmens brændselsmix */}
      <div>
        <span className="text-sm text-gray-700">Fjernvarmens brændselsmix</span>
        {harMix ? (
          <>
            <div className="mt-1.5 flex h-3 w-full overflow-hidden rounded-full bg-gray-100">
              {mixSegs.map(
                (s) =>
                  s.pct > 0 && (
                    <div
                      key={s.label}
                      className={s.color}
                      style={{ width: `${s.pct}%` }}
                      title={`${s.label}: ${s.pct}%`}
                    />
                  )
              )}
            </div>
            <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1">
              {mixSegs.map((s) => (
                <span key={s.label} className="inline-flex items-center gap-1 text-[11px] text-gray-600">
                  <span className={`inline-block w-2 h-2 rounded-sm ${s.color}`} />
                  {s.label} {s.pct}%
                </span>
              ))}
            </div>
            <p className="mt-1.5 text-[11px] text-gray-400">
              Biomasse og affald er afbrænding - ikke nødvendigvis CO₂-neutralt. Derfor vises mixet som kontekst, ikke som score.
            </p>
          </>
        ) : (
          <p className="mt-1 text-[11px] text-gray-400">
            Begrænset egen varmeproduktion - kommunen indgår typisk i et fælles fjernvarmenet eller bruger individuel opvarmning.
          </p>
        )}
      </div>
    </div>
    </>
  );
}

export default function ScoreBars({
  kommune,
  compare,
  ratios,
  compareRatios,
  vurderingsMode = false,
  vurderinger = {},
  onVurderingKlik,
}: ScoreBarsProps) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const { mode: baselineMode } = useBaseline();

  // Navnet på det sammenligningsgrundlag scoren faktisk bruger. Skal følge
  // baseline-toggle, ellers ser en score ud til at modsige det tal den står
  // ved siden af (fx 4,4% mod "Gns: 3,6%" men grøn score, fordi scoren i
  // virkeligheden var målt mod landkommunerne, ikke mod hele landet).
  const baselineNavn =
    baselineMode === "top10" ? "Top 10%"
    : baselineMode === "kommunegruppe" ? kommunegruppeNavn(kommune.kommune_kode)
    : "Landsgns";

  const activeRatios = ratios ?? kommune.ratios;
  const activeCompareRatios = compareRatios ?? compare?.ratios;

  const categoryScores = computeCategoryScores(activeRatios);
  const compareCategoryScores = compare
    ? computeCategoryScores(activeCompareRatios ?? compare.ratios)
    : null;

  // Klik-handler for sociale kategorier
  const handleSocialKlik = (categoryId: string, categoryName: string) => {
    if (vurderingsMode && onVurderingKlik) {
      onVurderingKlik(categoryId, categoryName, "social");
    } else {
      setExpanded(expanded === categoryId ? null : categoryId);
    }
  };

  // Klik-handler for okologiske dimensioner
  const handleEcoKlik = (dimId: string, dimName: string, subCount: number) => {
    if (vurderingsMode && onVurderingKlik) {
      onVurderingKlik(dimId, dimName, "ecological");
    } else if (subCount > 0) {
      setExpanded(expanded === dimId ? null : dimId);
    }
  };

  return (
    <div className="space-y-4">
      {/* Socialt fundament */}
      <div>
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Socialt fundament</p>
        <div className="space-y-2">
          {categoryScores.map((cat) => {
            const isExpanded = expanded === cat.categoryId;
            const blTag = baselineTag(categoryBaselineType(cat.indicators.map((i) => i.indicator)));
            const cmpCat = compareCategoryScores?.find(
              (c) => c.categoryId === cat.categoryId
            );
            const indicatorsWithData = cat.indicators.filter((i) => i.score !== null).length;
            const totalIndicators = cat.indicatorCount;
            const isPartialData = totalIndicators > 0 && indicatorsWithData > 0 && indicatorsWithData < totalIndicators;
            const harVurdering = vurderingsMode && vurderinger[cat.categoryId];

            return (
              <div
                key={cat.categoryId}
                data-category={cat.categoryId}
                className={`border rounded-lg overflow-hidden transition-colors ${
                  vurderingsMode
                    ? "border-emerald-200 hover:border-emerald-400 cursor-pointer"
                    : "border-gray-200"
                }`}
              >
                <button
                  onClick={() => handleSocialKlik(cat.categoryId, cat.categoryName)}
                  className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-gray-50 transition-colors text-left"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {/* Vurderingsprik - kun i vurderingsmode */}
                        {vurderingsMode && (
                          <VurderingPrik score={vurderinger[cat.categoryId]?.score} />
                        )}
                        <span className="text-sm font-semibold text-gray-900 truncate">
                          {cat.categoryName}
                        </span>
                        {!vurderingsMode && blTag && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 whitespace-nowrap">
                            {blTag}
                          </span>
                        )}
                        {/* Datadækning-badge - skjul i vurderingsmode for at undgå rod */}
                        {!vurderingsMode && (
                          <>
                            {totalIndicators === 0 ? (
                              <span className="text-xs text-gray-400">afventer data</span>
                            ) : !cat.hasData ? (
                              <span
                                className="text-xs text-gray-400"
                                title={`0 af ${totalIndicators} indikatorer har data for denne kommune`}
                              >
                                0/{totalIndicators} indikatorer
                              </span>
                            ) : (
                              <span
                                className={`text-xs ${isPartialData ? "text-amber-600 font-medium" : "text-gray-400"}`}
                                title={
                                  isPartialData
                                    ? `Bemærk: kun ${indicatorsWithData} af ${totalIndicators} indikatorer har data for denne kommune. Scoren er gennemsnit af de tilgængelige.`
                                    : `${indicatorsWithData} af ${totalIndicators} indikatorer har data`
                                }
                              >
                                {indicatorsWithData}/{totalIndicators} indikator{totalIndicators !== 1 ? "er" : ""}
                                {isPartialData && " ⓘ"}
                              </span>
                            )}
                          </>
                        )}
                        {/* Vurderingsmode hint */}
                        {vurderingsMode && !harVurdering && (
                          <span className="text-xs text-emerald-600">Klik for at vurdere</span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 ml-2 shrink-0">
                        <span className={`text-sm font-semibold ${cat.hasData ? scoreColor(cat.score) : "text-gray-400"}`}>
                          {cat.hasData && cat.score !== null ? cat.score.toFixed(1) : "–"}
                        </span>
                        {!vurderingsMode && (
                          <TrendMarker trend={kommune.trends?.[`_dim_${cat.categoryId}`]} kontekst="social" />
                        )}
                        {compare && cmpCat && cmpCat.hasData && cmpCat.score !== null && (
                          <span className={`text-xs ${scoreColor(cmpCat.score)}`}>
                            ({cmpCat.score.toFixed(1)})
                          </span>
                        )}
                      </div>
                    </div>
                    {cat.hasData && (
                      <div className="mt-1.5">
                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden relative">
                          <div className="absolute top-0 bottom-0 w-px bg-gray-400" style={{ left: `${(100 / 150) * 100}%` }} />
                          <div className={`h-full rounded-full ${scoreBarColor(cat.score)} transition-all`}
                            style={{ width: `${Math.min((cat.score || 0) / 150, 1) * 100}%` }} />
                        </div>
                        {compare && cmpCat && cmpCat.hasData && (
                          <div className="mt-1">
                            <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden relative">
                              <div className="absolute top-0 bottom-0 w-px bg-gray-400" style={{ left: `${(100 / 150) * 100}%` }} />
                              <div className={`h-full rounded-full ${scoreBarColor(cmpCat.score)} opacity-60 transition-all`}
                                style={{ width: `${Math.min((cmpCat.score || 0) / 150, 1) * 100}%` }} />
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                    {!cat.hasData && <div className="mt-1.5 h-2 bg-gray-100 rounded-full" />}
                  </div>
                  {/* Pil-ikon - kun i normal-mode */}
                  {!vurderingsMode && cat.indicatorCount > 0 && (
                    <svg className={`w-4 h-4 text-gray-400 transition-transform shrink-0 ${isExpanded ? "rotate-180" : ""}`}
                      fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  )}
                </button>

                {/* Udvidet sub-indikator panel - kun i normal-mode */}
                {!vurderingsMode && isExpanded && cat.indicators.length > 0 && (
                  <div className="border-t border-gray-100 bg-gray-50">
                    {cat.indicators.map(({ indicator: ind, score }) => {
                      const cmpScore = activeCompareRatios?.[ind.id] ?? compare?.ratios[ind.id] ?? null;
                      const rawVal = kommune.rawValues?.[ind.id] ?? null;
                      const cmpRawVal = compare?.rawValues?.[ind.id] ?? null;
                      // Sammenligningsværdien udledes af den AKTIVE score, ikke af
                      // avg-ratioen. Ellers ville tallet vise landsgennemsnittet,
                      // mens scoren måler mod kommunegruppen eller top 10% - og så
                      // ser en grøn score forkert ud ved siden af en dårligere råværdi.
                      const baselineAvg = (rawVal !== null && score !== null && score !== 0)
                        ? ind.inverse
                          ? (score * rawVal) / 100
                          : (rawVal * 100) / score
                        : null;
                      const formatRaw = (val: number, unit: string) => {
                        const num = unit === "kr./indb."
                          ? Math.round(val).toLocaleString("da-DK")
                          : val % 1 === 0
                            ? val.toFixed(0)
                            : val.toFixed(1);
                        return unit === "%" ? `${num}%` : `${num} ${unit}`;
                      };
                      return (
                        <div key={ind.id} className="px-3 py-2.5 border-b border-gray-100 last:border-b-0">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-700">{ind.name}</span>
                            <div className="flex items-center gap-2">
                              <span className={`text-sm font-medium ${scoreColor(score)}`}>
                                {score !== null ? score.toFixed(1) : "–"}
                              </span>
                              <TrendMarker trend={kommune.trends?.[ind.id]} />
                              {compare && cmpScore !== null && (
                                <span className={`text-xs ${scoreColor(cmpScore)}`}>({cmpScore.toFixed(1)})</span>
                              )}
                            </div>
                          </div>
                          <div className="mt-1 h-1.5 bg-gray-100 rounded-full overflow-hidden relative">
                            <div className="absolute top-0 bottom-0 w-px bg-gray-300" style={{ left: `${(100 / 150) * 100}%` }} />
                            <div className={`h-full rounded-full ${scoreBarColor(score)} transition-all`}
                              style={{ width: `${Math.min((score || 0) / 150, 1) * 100}%` }} />
                          </div>
                          {rawVal !== null && ind.rawUnit && (
                            <div className="mt-1.5 flex items-center gap-2 flex-wrap">
                              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 bg-gray-100 rounded text-[11px] text-gray-600 font-medium">
                                <span className="text-gray-400">Kommune:</span>
                                {formatRaw(rawVal, ind.rawUnit)}
                                {compare && cmpRawVal !== null && (
                                  <span className="text-gray-400 font-normal">
                                    {" "}vs. {formatRaw(cmpRawVal, ind.rawUnit)}
                                  </span>
                                )}
                                {baselineAvg !== null && !ind.absoluteTarget && (
                                  <span className="text-gray-400 font-normal before:content-['·'] before:mx-1">
                                    {baselineNavn}: {formatRaw(baselineAvg, ind.rawUnit)}
                                  </span>
                                )}
                              </span>
                            </div>
                          )}
                          <div className="mt-1.5 flex items-center justify-between text-xs text-gray-500">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span>{ind.inverse ? "Lavere er bedre" : "Højere er bedre"}</span>
                              {ind.absoluteTarget && (
                                <span className="px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded text-[10px] font-medium">
                                  Mål: {ind.absoluteTarget}
                                </span>
                              )}
                              {!ind.absoluteTarget && (
                                <span className="text-gray-400 text-[10px]">
                                  Baseline: {baselineMode === "top10" ? "top 10% af kommunerne"
                                    : baselineMode === "kommunegruppe" ? kommunegruppeNavn(kommune.kommune_kode).toLowerCase()
                                    : "landsgennemsnit"}
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-2 shrink-0">
                              <span className="text-gray-400 text-[10px]">Data: {ind.dataYear ?? DOUGHNUT_DEFAULT_DATA_YEAR}</span>
                              <a href={`/metode#${cat.categoryId}`} className="text-blue-600 hover:underline">
                                {ind.table} ↗
                              </a>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                    {cat.categoryId === "energi" && <EnergiKontekst kommune={kommune} />}
                  </div>
                )}
                {!vurderingsMode && isExpanded && cat.indicators.length === 0 && (
                  <div className="border-t border-gray-100 bg-gray-50 px-3 py-3 text-sm text-gray-400">
                    Ingen data tilgængelig endnu for denne kategori.
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Okologisk loft */}
      <div>
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Økologisk loft</p>
        <div className="space-y-2">
          {ECOLOGICAL_DIMENSIONS.map((dim) => {
            const score = kommune.eco_ratios[dim.id] ?? null;
            const cmpScore = compare ? (compare.eco_ratios[dim.id] ?? null) : null;
            const hasData = score !== null;
            const isExpanded = expanded === dim.id;
            const subs = dim.subIndicators ?? [];
            const availableSubs = subs.filter(s => (kommune.rawValues?.[s.rawKey] ?? null) !== null);
            const subCount = availableSubs.length;
            const totalSubs = subs.length;
            const isPartialEcoData = hasData && totalSubs > 1 && subCount > 0 && subCount < totalSubs;
            const harVurdering = vurderingsMode && vurderinger[dim.id];
            const blTag = baselineTag(dimensionBaselineType(dim));

            const formatRaw = (val: number, unit: string) => {
              const num = val % 1 === 0 ? val.toFixed(0) : val.toFixed(2);
              return unit === "%" ? `${num}%` : `${num} ${unit}`;
            };

            return (
              <div
                key={dim.id}
                className={`border rounded-lg overflow-hidden transition-colors ${
                  vurderingsMode
                    ? "border-emerald-200 hover:border-emerald-400 cursor-pointer"
                    : "border-gray-200"
                }`}
              >
                <button
                  onClick={() => handleEcoKlik(dim.id, dim.name, subCount)}
                  disabled={!vurderingsMode && subCount === 0}
                  className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-gray-50 transition-colors text-left disabled:cursor-default disabled:hover:bg-transparent"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {/* Vurderingsprik */}
                        {vurderingsMode && (
                          <VurderingPrik score={vurderinger[dim.id]?.score} />
                        )}
                        <span className="text-sm font-semibold text-gray-900 truncate">
                          {dim.name}
                        </span>
                        {!vurderingsMode && blTag && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 whitespace-nowrap">
                            {blTag}
                          </span>
                        )}
                        {/* Datadækning - kun i normal-mode */}
                        {!vurderingsMode && (
                          <>
                            {!hasData ? (
                              <span className="text-xs text-gray-400">afventer data</span>
                            ) : totalSubs > 1 ? (
                              <span
                                className={`text-xs ${isPartialEcoData ? "text-amber-600 font-medium" : "text-gray-400"}`}
                                title={
                                  isPartialEcoData
                                    ? `Bemærk: kun ${subCount} af ${totalSubs} sub-indikatorer har data. Worst-of-scoren er beregnet på de tilgængelige.`
                                    : `${subCount} af ${totalSubs} sub-indikatorer har data`
                                }
                              >
                                {subCount}/{totalSubs} indikator{totalSubs !== 1 ? "er" : ""}
                                {isPartialEcoData && " ⓘ"}
                              </span>
                            ) : (
                              <span className="text-xs text-gray-400">
                                {subCount} indikator{subCount !== 1 ? "er" : ""}
                              </span>
                            )}
                          </>
                        )}
                        {/* Vurderingsmode hint */}
                        {vurderingsMode && !harVurdering && (
                          <span className="text-xs text-emerald-600">Klik for at vurdere</span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 ml-2 shrink-0">
                        <span className={`text-sm font-semibold ${hasData ? ecoScoreColor(score) : "text-gray-400"}`}>
                          {hasData && score !== null ? score.toFixed(1) : "–"}
                        </span>
                        {!vurderingsMode && (
                          <TrendMarker trend={kommune.trends?.[`_dim_${dim.id}`]} kontekst="ecological" />
                        )}
                        {compare && cmpScore !== null && (
                          <span className={`text-xs ${ecoScoreColor(cmpScore)}`}>
                            ({cmpScore.toFixed(1)})
                          </span>
                        )}
                      </div>
                    </div>
                    {hasData && (
                      <div className="mt-1.5">
                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden relative">
                          <div className="absolute top-0 bottom-0 w-px bg-gray-400" style={{ left: "50%" }} />
                          <div className={`h-full rounded-full ${ecoBarColor(score)} transition-all`}
                            style={{ width: `${Math.min((score || 0) / 200, 1) * 100}%` }} />
                        </div>
                        {compare && cmpScore !== null && (
                          <div className="mt-1">
                            <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden relative">
                              <div className="absolute top-0 bottom-0 w-px bg-gray-400" style={{ left: "50%" }} />
                              <div className={`h-full rounded-full ${ecoBarColor(cmpScore)} opacity-60 transition-all`}
                                style={{ width: `${Math.min((cmpScore || 0) / 200, 1) * 100}%` }} />
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                    {!hasData && <div className="mt-1.5 h-2 bg-gray-100 rounded-full" />}
                  </div>
                  {/* Pil-ikon - kun i normal-mode */}
                  {!vurderingsMode && subCount > 0 && (
                    <svg className={`w-4 h-4 text-gray-400 transition-transform shrink-0 ${isExpanded ? "rotate-180" : ""}`}
                      fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  )}
                </button>

                {/* Sub-indikator panel - kun i normal-mode */}
                {!vurderingsMode && isExpanded && availableSubs.length > 0 && (
                  <div className="border-t border-gray-100 bg-gray-50">
                    {availableSubs.map((sub) => {
                      const raw = kommune.rawValues?.[sub.rawKey] ?? null;
                      const cmpRaw = compare?.rawValues?.[sub.rawKey] ?? null;
                      const subRatio = sub.ratioKey ? (kommune.rawValues?.[sub.ratioKey] ?? null) : null;
                      const cmpSubRatio = sub.ratioKey && compare ? (compare.rawValues?.[sub.ratioKey] ?? null) : null;
                      if (raw === null) return null;
                      return (
                        <div key={sub.rawKey} className="px-3 py-2.5 border-b border-gray-100 last:border-b-0">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-700">{sub.label}</span>
                            <div className="flex items-center gap-2 ml-2 shrink-0">
                              {subRatio !== null && (
                                <>
                                  <span className={`text-sm font-medium ${ecoScoreColor(subRatio)}`}>
                                    {subRatio.toFixed(1)}
                                  </span>
                                  {compare && cmpSubRatio !== null && (
                                    <span className={`text-xs ${ecoScoreColor(cmpSubRatio)}`}>({cmpSubRatio.toFixed(1)})</span>
                                  )}
                                </>
                              )}
                              <TrendMarker trend={kommune.trends?.[sub.rawKey]} />
                            </div>
                          </div>
                          {subRatio !== null && (
                            <div className="mt-1 h-1.5 bg-gray-100 rounded-full overflow-hidden relative">
                              <div className="absolute top-0 bottom-0 w-px bg-gray-300" style={{ left: "50%" }} />
                              <div className={`h-full rounded-full ${ecoBarColor(subRatio)} transition-all`}
                                style={{ width: `${Math.min((subRatio || 0) / 200, 1) * 100}%` }} />
                            </div>
                          )}
                          <div className="mt-1.5 flex items-center gap-2 flex-wrap">
                            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 bg-gray-100 rounded text-[11px] text-gray-600 font-medium">
                              <span className="text-gray-400">Kommune:</span>
                              {formatRaw(raw, sub.unit)}
                              {compare && cmpRaw !== null && (
                                <span className="text-gray-400 font-normal">
                                  {" "}vs. {formatRaw(cmpRaw, sub.unit)}
                                </span>
                              )}
                              {sub.boundary && (
                                <span className="text-gray-400 font-normal before:content-['·'] before:mx-1">
                                  {sub.boundary}
                                </span>
                              )}
                            </span>
                          </div>
                          <div className="mt-1.5 flex items-center justify-between text-xs text-gray-500">
                            <div className="flex items-center gap-2">
                              <span>{sub.lowerIsBetter ? "Lavere er bedre" : "Højere er bedre"}</span>
                              {sub.baselineType && (
                                <span className="text-gray-400 text-[10px]">
                                  {sub.baselineType === "absolut" ? "mod mål" : "mod landsgns"}
                                </span>
                              )}
                            </div>
                            <a href={`/metode#${dim.id}`} className="text-blue-600 hover:underline">
                              Se metode ↗
                            </a>
                          </div>
                        </div>
                      );
                    })}
                    {dim.id === "klimapaavirkning" && <KlimaKontekst kommune={kommune} />}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
