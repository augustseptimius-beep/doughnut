"use client";

import { useState } from "react";
import {
  type KommuneData,
  type CategoryScore,
  scoreColor,
  scoreBarColor,
  computeCategoryScores,
} from "@/lib/shared";

interface ScoreBarsProps {
  kommune: KommuneData;
  compare?: KommuneData | null;
}

export default function ScoreBars({ kommune, compare }: ScoreBarsProps) {
  const [expanded, setExpanded] = useState<string | null>(null);

  const categoryScores = computeCategoryScores(kommune.ratios);
  const compareCategoryScores = compare
    ? computeCategoryScores(compare.ratios)
    : null;

  return (
    <div className="space-y-2">
      {categoryScores.map((cat) => {
        const isExpanded = expanded === cat.categoryId;
        const cmpCat = compareCategoryScores?.find(
          (c) => c.categoryId === cat.categoryId
        );

        return (
          <div
            key={cat.categoryId}
            className="border border-gray-200 rounded-lg overflow-hidden"
          >
            {/* Category header */}
            <button
              onClick={() =>
                setExpanded(isExpanded ? null : cat.categoryId)
              }
              className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-gray-50 transition-colors text-left"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-gray-900 truncate">
                      {cat.categoryName}
                    </span>
                    <span className="text-xs text-gray-400">
                      {cat.hasData
                        ? `${cat.indicatorCount} indikator${cat.indicatorCount !== 1 ? "er" : ""}`
                        : "mangler data"}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 ml-2 shrink-0">
                    <span
                      className={`text-sm font-semibold ${
                        cat.hasData ? scoreColor(cat.score) : "text-gray-400"
                      }`}
                    >
                      {cat.hasData && cat.score !== null
                        ? cat.score.toFixed(1)
                        : "–"}
                    </span>
                    {compare && cmpCat && cmpCat.hasData && cmpCat.score !== null && (
                      <span className={`text-xs ${scoreColor(cmpCat.score)}`}>
                        ({cmpCat.score.toFixed(1)})
                      </span>
                    )}
                  </div>
                </div>
                {/* Category score bar */}
                {cat.hasData && (
                  <div className="mt-1.5">
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden relative">
                      <div
                        className="absolute top-0 bottom-0 w-px bg-gray-400"
                        style={{ left: `${(100 / 150) * 100}%` }}
                      />
                      <div
                        className={`h-full rounded-full ${scoreBarColor(cat.score)} transition-all`}
                        style={{
                          width: `${Math.min((cat.score || 0) / 150, 1) * 100}%`,
                        }}
                      />
                    </div>
                    {compare && cmpCat && cmpCat.hasData && (
                      <div className="mt-1">
                        <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden relative">
                          <div
                            className="absolute top-0 bottom-0 w-px bg-gray-400"
                            style={{ left: `${(100 / 150) * 100}%` }}
                          />
                          <div
                            className={`h-full rounded-full ${scoreBarColor(cmpCat.score)} opacity-60 transition-all`}
                            style={{
                              width: `${Math.min((cmpCat.score || 0) / 150, 1) * 100}%`,
                            }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                )}
                {!cat.hasData && (
                  <div className="mt-1.5 h-2 bg-gray-100 rounded-full" />
                )}
              </div>
              {cat.indicatorCount > 0 && (
                <svg
                  className={`w-4 h-4 text-gray-400 transition-transform shrink-0 ${
                    isExpanded ? "rotate-180" : ""
                  }`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              )}
            </button>

            {/* Expanded: individual indicators */}
            {isExpanded && cat.indicators.length > 0 && (
              <div className="border-t border-gray-100 bg-gray-50">
                {cat.indicators.map(({ indicator: ind, score }) => {
                  const cmpScore = compare?.ratios[ind.id] ?? null;
                  return (
                    <div
                      key={ind.id}
                      className="px-3 py-2.5 border-b border-gray-100 last:border-b-0"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-700">
                          {ind.name}
                        </span>
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-sm font-medium ${scoreColor(score)}`}
                          >
                            {score !== null ? score.toFixed(1) : "–"}
                          </span>
                          {compare && cmpScore !== null && (
                            <span
                              className={`text-xs ${scoreColor(cmpScore)}`}
                            >
                              ({cmpScore.toFixed(1)})
                            </span>
                          )}
                        </div>
                      </div>
                      {/* Indicator bar */}
                      <div className="mt-1 h-1.5 bg-gray-100 rounded-full overflow-hidden relative">
                        <div
                          className="absolute top-0 bottom-0 w-px bg-gray-300"
                          style={{ left: `${(100 / 150) * 100}%` }}
                        />
                        <div
                          className={`h-full rounded-full ${scoreBarColor(score)} transition-all`}
                          style={{
                            width: `${Math.min((score || 0) / 150, 1) * 100}%`,
                          }}
                        />
                      </div>
                      {/* Details */}
                      <div className="mt-1.5 flex items-center justify-between text-xs text-gray-500">
                        <span>
                          {ind.inverse
                            ? "Lavere er bedre (inverteret)"
                            : "Højere er bedre"}
                        </span>
                        <a
                          href={ind.source}
                          target="_blank"
                          rel="noopener"
                          className="text-blue-600 hover:underline"
                        >
                          {ind.table} ↗
                        </a>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* No-data category expanded */}
            {isExpanded && cat.indicators.length === 0 && (
              <div className="border-t border-gray-100 bg-gray-50 px-3 py-3 text-sm text-gray-400">
                Ingen data tilgængelig endnu for denne kategori.
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
