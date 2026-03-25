"use client";

import { useState } from "react";
import {
  INDICATORS,
  type KommuneData,
  scoreColor,
  scoreBarColor,
} from "@/lib/shared";

interface ScoreBarsProps {
  kommune: KommuneData;
  compare?: KommuneData | null;
}

export default function ScoreBars({ kommune, compare }: ScoreBarsProps) {
  const [expanded, setExpanded] = useState<string | null>(null);

  const indicators = INDICATORS.filter(
    (ind) => kommune.ratios[ind.id] !== null
  );

  return (
    <div className="space-y-2">
      {indicators.map((ind) => {
        const score = kommune.ratios[ind.id];
        const cmpScore = compare?.ratios[ind.id] ?? null;
        const isExpanded = expanded === ind.id;

        return (
          <div key={ind.id} className="border border-gray-200 rounded-lg overflow-hidden">
            {/* Header row */}
            <button
              onClick={() => setExpanded(isExpanded ? null : ind.id)}
              className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-gray-50 transition-colors text-left"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900 truncate">
                    {ind.name}
                  </span>
                  <div className="flex items-center gap-2 ml-2 shrink-0">
                    <span className={`text-sm font-semibold ${scoreColor(score)}`}>
                      {score !== null ? score.toFixed(1) : "–"}
                    </span>
                    {compare && cmpScore !== null && (
                      <span className={`text-xs ${scoreColor(cmpScore)}`}>
                        ({cmpScore.toFixed(1)})
                      </span>
                    )}
                  </div>
                </div>
                {/* Score bar */}
                <div className="mt-1.5 flex items-center gap-2">
                  <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden relative">
                    {/* 100 mark */}
                    <div
                      className="absolute top-0 bottom-0 w-px bg-gray-400"
                      style={{ left: `${(100 / 150) * 100}%` }}
                    />
                    <div
                      className={`h-full rounded-full ${scoreBarColor(score)} transition-all`}
                      style={{
                        width: `${Math.min((score || 0) / 150, 1) * 100}%`,
                      }}
                    />
                  </div>
                </div>
                {compare && cmpScore !== null && (
                  <div className="mt-1 flex items-center gap-2">
                    <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden relative">
                      <div
                        className="absolute top-0 bottom-0 w-px bg-gray-400"
                        style={{ left: `${(100 / 150) * 100}%` }}
                      />
                      <div
                        className={`h-full rounded-full ${scoreBarColor(cmpScore)} opacity-60 transition-all`}
                        style={{
                          width: `${Math.min((cmpScore || 0) / 150, 1) * 100}%`,
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>
              <svg
                className={`w-4 h-4 text-gray-400 transition-transform ${isExpanded ? "rotate-180" : ""}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {/* Expanded details */}
            {isExpanded && (
              <div className="px-3 pb-3 border-t border-gray-100 bg-gray-50">
                <table className="w-full text-sm mt-2">
                  <tbody>
                    <tr>
                      <td className="py-1 text-gray-500">Indikator</td>
                      <td className="py-1 text-right font-medium">{ind.name}</td>
                    </tr>
                    <tr>
                      <td className="py-1 text-gray-500">Ratio</td>
                      <td className="py-1 text-right font-medium">
                        {score !== null ? `${score.toFixed(2)}%` : "–"}
                      </td>
                    </tr>
                    <tr>
                      <td className="py-1 text-gray-500">Beregning</td>
                      <td className="py-1 text-right text-xs text-gray-600">
                        {ind.inverse
                          ? "landsgennemsnit / kommuneværdi × 100"
                          : "kommuneværdi / landsgennemsnit × 100"}
                      </td>
                    </tr>
                    <tr>
                      <td className="py-1 text-gray-500">Tabel</td>
                      <td className="py-1 text-right">
                        <a
                          href={ind.source}
                          target="_blank"
                          rel="noopener"
                          className="text-blue-600 hover:underline text-xs"
                        >
                          {ind.table} ↗
                        </a>
                      </td>
                    </tr>
                    <tr>
                      <td className="py-1 text-gray-500">Kategori</td>
                      <td className="py-1 text-right capitalize">{ind.category === "social" ? "Social" : "Økologisk"}</td>
                    </tr>
                    {ind.inverse && (
                      <tr>
                        <td className="py-1 text-gray-500">Invers</td>
                        <td className="py-1 text-right text-xs text-gray-600">
                          Lavere er bedre — ratio inverteret
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
