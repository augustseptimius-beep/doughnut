"use client";

import { useState } from "react";
import type { KommuneData } from "@/lib/shared";
import { computeCategoryScores, ECOLOGICAL_DIMENSIONS } from "@/lib/shared";
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

      {/* Donut ring(s): side by side when comparing, single centered when not */}
      <div className={compare ? "grid grid-cols-2 gap-6 mb-8" : "grid grid-cols-1 lg:grid-cols-2 gap-8 mb-0"}>
        <div>
          {compare && (
            <h3 className="text-sm font-medium text-gray-500 mb-2 text-center">
              {kommune.kommune_navn}
            </h3>
          )}
          <DoughnutRing kommune={kommune} />

          {/* Summary - only show under primary donut when not comparing */}
          {!compare && (
            <div className="text-sm text-gray-600 bg-gray-50 rounded-lg p-4 space-y-1 mt-4">
              <p>
                <span className="font-medium">Socialt fundament:</span>{" "}
                {categoriesAboveThreshold} af {categoriesWithData} kategorier
                {categoriesWithData < 6 && ` (${6 - categoriesWithData} mangler data)`}
                {" "}over landsgennemsnit.
              </p>
              <p>
                <span className="font-medium">Økologisk loft:</span>{" "}
                {(() => {
                  const ecoWithData = ECOLOGICAL_DIMENSIONS.filter(
                    (d) => kommune.eco_ratios[d.id] !== null
                  );
                  const ecoOvershoot = ecoWithData.filter(
                    (d) => (kommune.eco_ratios[d.id] ?? 0) > 100
                  );
                  if (ecoWithData.length === 0) {
                    return <span className="text-gray-400">afventer data.</span>;
                  }
                  return (
                    <span>
                      {ecoOvershoot.length} af {ecoWithData.length} dimensioner
                      overskredet
                      {ecoWithData.length < ECOLOGICAL_DIMENSIONS.length &&
                        ` (${ECOLOGICAL_DIMENSIONS.length - ecoWithData.length} afventer data)`}.
                    </span>
                  );
                })()}
              </p>
            </div>
          )}
        </div>

        {/* Comparison donut or score bars */}
        {compare ? (
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-2 text-center">
              {compare.kommune_navn}
            </h3>
            <DoughnutRing kommune={compare} />
          </div>
        ) : (
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-3">
              Kategorier
            </h3>
            <ScoreBars kommune={kommune} compare={null} />
          </div>
        )}
      </div>

      {/* When comparing: show score bars below both donuts */}
      {compare && (
        <div className="mt-2">
          <h3 className="text-sm font-medium text-gray-500 mb-3">
            Kategorier{" "}
            <span className="text-gray-400">(parentes = {compare.kommune_navn})</span>
          </h3>
          <ScoreBars kommune={kommune} compare={compare} />
        </div>
      )}
    </div>
  );
}
