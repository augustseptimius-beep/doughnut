"use client";

import { useState } from "react";
import type { KommuneData } from "@/lib/shared";
import DoughnutRing from "@/components/DoughnutRing";
import ScoreBars from "@/components/ScoreBars";
import KommuneCompare from "@/components/KommuneCompare";

interface Props {
  kommune: KommuneData;
  allKommuner: KommuneData[];
}

export default function KommuneClient({ kommune, allKommuner }: Props) {
  const [compare, setCompare] = useState<KommuneData | null>(null);

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

      {/* Main content */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Left: Doughnut ring(s) */}
        <div className="space-y-4">
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
        </div>

        {/* Right: Score bars */}
        <div>
          <h3 className="text-sm font-medium text-gray-500 mb-3">
            Indikatorer
            {compare && (
              <span className="text-gray-400">
                {" "}(parentes = {compare.kommune_navn})
              </span>
            )}
          </h3>
          <ScoreBars kommune={kommune} compare={compare} />
        </div>
      </div>
    </div>
  );
}
