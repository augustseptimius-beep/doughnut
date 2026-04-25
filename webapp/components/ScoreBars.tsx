"use client";

import { useState } from "react";
import {
  type KommuneData,
  ECOLOGICAL_DIMENSIONS,
  scoreColor,
  scoreBarColor,
  computeCategoryScores,
  DOUGHNUT_DEFAULT_DATA_YEAR,
} from "@/lib/shared";

interface ScoreBarsProps {
  kommune: KommuneData;
  compare?: KommuneData | null;
  ratios?: Record<string, number | null>; // override kommune.ratios (bruges til baseline-skift)
  compareRatios?: Record<string, number | null>; // override compare.ratios
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

export default function ScoreBars({ kommune, compare, ratios, compareRatios }: ScoreBarsProps) {
  const [expanded, setExpanded] = useState<string | null>(null);

  const activeRatios = ratios ?? kommune.ratios;
  const activeCompareRatios = compareRatios ?? compare?.ratios;

  const categoryScores = computeCategoryScores(activeRatios);
  const compareCategoryScores = compare
    ? computeCategoryScores(activeCompareRatios ?? compare.ratios)
    : null;

  return (
    <div className="space-y-4">
      {/* Socialt fundament */}
      <div>
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Socialt fundament</p>
        <div className="space-y-2">
          {categoryScores.map((cat) => {
            const isExpanded = expanded === cat.categoryId;
            const cmpCat = compareCategoryScores?.find(
              (c) => c.categoryId === cat.categoryId
            );
            // Datadækning: hvor mange af kategoriens indikatorer har faktisk en score for denne kommune?
            const indicatorsWithData = cat.indicators.filter((i) => i.score !== null).length;
            const totalIndicators = cat.indicatorCount;
            const isPartialData = totalIndicators > 0 && indicatorsWithData > 0 && indicatorsWithData < totalIndicators;

            return (
              <div
                key={cat.categoryId}
                className="border border-gray-200 rounded-lg overflow-hidden"
              >
                <button
                  onClick={() => setExpanded(isExpanded ? null : cat.categoryId)}
                  className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-gray-50 transition-colors text-left"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-gray-900 truncate">
                          {cat.categoryName}
                        </span>
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
                  {cat.indicatorCount > 0 && (
                    <svg className={`w-4 h-4 text-gray-400 transition-transform shrink-0 ${isExpanded ? "rotate-180" : ""}`}
                      fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  )}
                </button>

                {isExpanded && cat.indicators.length > 0 && (
                  <div className="border-t border-gray-100 bg-gray-50">
                    {cat.indicators.map(({ indicator: ind, score }) => {
                      const cmpScore = activeCompareRatios?.[ind.id] ?? compare?.ratios[ind.id] ?? null;
                      const rawVal = kommune.rawValues?.[ind.id] ?? null;
                      const cmpRawVal = compare?.rawValues?.[ind.id] ?? null;
                      // Brug original ratio (ikke top10-skaleret) til at back-beregne landsgennemsnit
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
                          {/* Råværdi + landsgennemsnit */}
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
                  </div>
                )}
                {isExpanded && cat.indicators.length === 0 && (
                  <div className="border-t border-gray-100 bg-gray-50 px-3 py-3 text-sm text-gray-400">
                    Ingen data tilgængelig endnu for denne kategori.
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Økologisk loft */}
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

            const formatRaw = (val: number, unit: string) => {
              const num = val % 1 === 0 ? val.toFixed(0) : val.toFixed(2);
              return unit === "%" ? `${num}%` : `${num} ${unit}`;
            };

            return (
              <div key={dim.id} className="border border-gray-200 rounded-lg overflow-hidden">
                <button
                  onClick={() => setExpanded(isExpanded ? null : dim.id)}
                  disabled={subCount === 0}
                  className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-gray-50 transition-colors text-left disabled:cursor-default disabled:hover:bg-transparent"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-gray-900 truncate">
                          {dim.name}
                        </span>
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
                  {subCount > 0 && (
                    <svg className={`w-4 h-4 text-gray-400 transition-transform shrink-0 ${isExpanded ? "rotate-180" : ""}`}
                      fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  )}
                </button>

                {isExpanded && availableSubs.length > 0 && (
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
                          {/* Sub-bar (samme stil som sociale) */}
                          {subRatio !== null && (
                            <div className="mt-1 h-1.5 bg-gray-100 rounded-full overflow-hidden relative">
                              <div className="absolute top-0 bottom-0 w-px bg-gray-300" style={{ left: "50%" }} />
                              <div className={`h-full rounded-full ${ecoBarColor(subRatio)} transition-all`}
                                style={{ width: `${Math.min((subRatio || 0) / 200, 1) * 100}%` }} />
                            </div>
                          )}
                          {/* Råværdi-chip + landsgennemsnit/grænse */}
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
                            <span>{sub.lowerIsBetter ? "Lavere er bedre" : "Højere er bedre"}</span>
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
