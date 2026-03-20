"use client";

import { useState } from "react";
import type { KommuneData } from "@/lib/shared";
import { computeCategoryScores } from "@/lib/shared";
import DoughnutRing from "@/components/DoughnutRing";
import ScoreBars from "@/components/ScoreBars";
import KommuneCompare from "@/components/KommuneCompare";

interface Props {
  kommune: KommuneData;
  allKommuner: KommuneData[];
}

export default function KommuneClient({ kommune, allKommuner }: Props) {
  const [compare, setCompare] = useState<KommuneData | null>(null);

  const categoryScores = computeCategoryScores(kommune.ratios);
  const categoriesAboveThreshold = categoryScores.filter(
    (c) => c.hasData && c.score !== null && c.score >= 100
  ).length;
  const categoriesWithData = categoryScores.filter((c) => c.hasData).length;

  return (
    <div>
      {/* Compare selector */}
      <div className="mb-6">
        <KommuneCompare
          allKommuner={allKommuner}
          current={kommune.kommune_navn}
          onSelect={setCompare}
        />
      </div>

      {/* Main content: Doughnut left, Categories right */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left: Doughnut ring(s) */}
        <div className="space-y-6">
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-2 text-center">
              {kommune.kommune_navn}
            </h3>
            <DoughnutRing kommune={kommune} />
          </div>

          {compare && (
            <div className="border-t border-gray-200 pt-4">
              <h3 className="text-sm font-medium text-gray-500 mb-2 text-center">
                {compare.kommune_navn}
              </h3>
              <DoughnutRing kommune={compare} />
            </div>
          )}

          {/* Summary text below doughnut */}
          <div className="text-sm text-gray-600 bg-gray-50 rounded-lg p-4 space-y-1">
            <p>
              <span className="font-medium">Socialt fundament:</span>{" "}
              {categoriesAboveThreshold} af {categoriesWithData} kategorier
              {categoriesWithData < 6 && ` (${6 - categoriesWithData} mangler data)`}
              {" "}over grænsen.
            </p>
            <p>
              <span className="font-medium">Økologisk loft:</span>{" "}
              <span className="text-gray-400">afventer data.</span>
            </p>
          </div>
        </div>

        {/* Right: Category list */}
        <div>
          <h3 className="text-sm font-medium text-gray-500 mb-3">
            Kategorier
            {compare && (
              <span className="text-gray-400">
                {" "}
                (parentes = {compare.kommune_navn})
              </span>
            )}
          </h3>
          <ScoreBars kommune={kommune} compare={compare} />
        </div>
      </div>
    </div>
  );
}
