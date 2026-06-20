"use client";

import { useState } from "react";
import {
  type KommuneData,
  type DimBaselineType,
  ECOLOGICAL_DIMENSIONS,
  scoreColor,
  scoreBarColor,
  computeCategoryScores,
  categoryBaselineType,
  dimensionBaselineType,
  DOUGHNUT_DEFAULT_DATA_YEAR,
} from "@/lib/shared";
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
  const harMix = bio !== null && affald !== null && fossil !== null && ren !== null;
  const harOpdeling = fossilDirekte !== null && fossilViaFjv !== null;

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
          {" "}Scoret mod målet 0% fossil.
        </div>
      )}
    <div className="px-3 py-3 bg-blue-50/40 border-t border-blue-100">
      <p className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-2">
        Kontekst <span className="font-normal normal-case text-gray-400">- indgår ikke i scoren</span>
      </p>

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
                      const originalRatio = kommune.ratios[ind.id] ?? null;
                      const nationalAvg = (rawVal !== null && originalRatio !== null && originalRatio !== 0)
                        ? ind.inverse
                          ? (originalRatio * rawVal) / 100
                          : (rawVal * 100) / originalRatio
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
                                {nationalAvg !== null && !ind.absoluteTarget && (
                                  <span className="text-gray-400 font-normal before:content-['·'] before:mx-1">
                                    Gns: {formatRaw(nationalAvg, ind.rawUnit)}
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
                                <span className="text-gray-400 text-[10px]">Baseline: landsgennemsnit</span>
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
                            {subRatio !== null && (
                              <div className="flex items-center gap-2 ml-2 shrink-0">
                                <span className={`text-sm font-medium ${ecoScoreColor(subRatio)}`}>
                                  {subRatio.toFixed(1)}
                                </span>
                                {compare && cmpSubRatio !== null && (
                                  <span className={`text-xs ${ecoScoreColor(cmpSubRatio)}`}>({cmpSubRatio.toFixed(1)})</span>
                                )}
                              </div>
                            )}
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
