"use client";

import type { KommuneData } from "@/lib/shared";
import { computeCategoryScores, ECOLOGICAL_DIMENSIONS } from "@/lib/shared";
import { useBaseline } from "@/lib/baseline-context";
import DoughnutRing from "@/components/DoughnutRing";
import ScoreBars from "@/components/ScoreBars";

interface Props {
  kommune: KommuneData;
  allKommuner: KommuneData[];
}

export default function KommuneClient({ kommune }: Props) {
  const { mode } = useBaseline();

  const activeRatios = mode === "top10" ? kommune.top10_ratios : kommune.ratios;

  const categoryScores = computeCategoryScores(activeRatios);
  const categoriesAboveThreshold = categoryScores.filter(
    (c) => c.hasData && c.score !== null && c.score >= 100
  ).length;
  const categoriesWithData = categoryScores.filter((c) => c.hasData).length;

  const baselineLabel = mode === "top10" ? "top 10%-niveauet" : "landsgennemsnittet";

  return (
    <div>
      {/* Donut ring */}
      <div className="max-w-3xl mx-auto mb-6">
        <DoughnutRing kommune={kommune} ratios={activeRatios} />
      </div>

      {/* Summary */}
      <div className="text-sm text-gray-600 bg-gray-50 rounded-lg p-4 space-y-1 mb-6 max-w-3xl mx-auto">
        <p>
          <span className="font-medium">Socialt fundament:</span>{" "}
          {categoriesAboveThreshold} af {categoriesWithData} kategorier
          {categoriesWithData < 6 && ` (${6 - categoriesWithData} mangler data)`}
          {" "}over {baselineLabel}.
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

      {/* Score bars */}
      <div>
        <h3 className="text-sm font-medium text-gray-500 mb-3">Kategorier</h3>
        <ScoreBars
          kommune={kommune}
          ratios={activeRatios}
        />
      </div>
    </div>
  );
}
