"use client";

import { useState } from "react";
import type { KommuneData } from "@/lib/shared";
import { computeCategoryScores, ECOLOGICAL_DIMENSIONS, kommunegruppeNavn } from "@/lib/shared";
import { useBaseline } from "@/lib/baseline-context";
import DoughnutRing from "@/components/DoughnutRing";
import ScoreBars from "@/components/ScoreBars";
import VurderingBoks from "@/components/VurderingBoks";
import VurderingsBjaelke from "@/components/VurderingsBjaelke";
import VurderingPrintView from "@/components/VurderingPrintView";
import type { VurderingScore, VurderingEntry } from "@/lib/vurdering";

interface Props {
  kommune: KommuneData;
  allKommuner: KommuneData[];
}

interface AktivDimension {
  id: string;
  navn: string;
  gruppe: "social" | "ecological";
}

export default function KommuneClient({ kommune }: Props) {
  const { mode } = useBaseline();

  const activeRatios =
    mode === "top10"
      ? kommune.top10_ratios
      : mode === "kommunegruppe"
      ? kommune.group_ratios
      : kommune.ratios;

  const categoryScores = computeCategoryScores(activeRatios);
  const categoriesAboveThreshold = categoryScores.filter(
    (c) => c.hasData && c.score !== null && c.score >= 100
  ).length;
  const categoriesWithData = categoryScores.filter((c) => c.hasData).length;

  const baselineLabel =
    mode === "top10"
      ? "top 10%-niveauet"
      : mode === "kommunegruppe"
      ? `gennemsnittet for ${kommunegruppeNavn(kommune.kommune_kode)}`
      : "landsgennemsnittet";

  // --- Vurderingsstate ---
  const [vurderingsMode, setVurderingsMode] = useState(false);
  const [projektnavn, setProjektnavn] = useState("");
  const [beskrivelse, setBeskrivelse] = useState("");
  const [vurderinger, setVurderinger] = useState<Record<string, VurderingEntry>>({});
  const [aktivDimension, setAktivDimension] = useState<AktivDimension | null>(null);

  const startVurdering = () => setVurderingsMode(true);

  const afslutVurdering = () => {
    const harData =
      projektnavn.trim() !== "" || Object.keys(vurderinger).length > 0;
    if (
      harData &&
      !window.confirm(
        "Er du sikker? Din vurdering forsvinder permanent."
      )
    ) {
      return;
    }
    setVurderingsMode(false);
    setProjektnavn("");
    setBeskrivelse("");
    setVurderinger({});
    setAktivDimension(null);
  };

  const handleVurderingKlik = (
    id: string,
    navn: string,
    gruppe: "social" | "ecological"
  ) => {
    setAktivDimension({ id, navn, gruppe });
  };

  const handleGem = (
    dimId: string,
    score: VurderingScore,
    argumentation: string
  ) => {
    setVurderinger((prev) => ({
      ...prev,
      [dimId]: { score, argumentation },
    }));
    setAktivDimension(null);
  };

  const handleEksporter = () => window.print();

  return (
    <>
      {/* ========= SKJAERMBILLEDE (skjult ved print) ========= */}
      <div className="no-print">
        {/* Vurderingsbjælke - kun i vurderingsmode */}
        {vurderingsMode && (
          <VurderingsBjaelke
            projektnavn={projektnavn}
            beskrivelse={beskrivelse}
            vurderingerAntal={Object.keys(vurderinger).length}
            onProjektnavnChange={setProjektnavn}
            onBeskrivelseChange={setBeskrivelse}
            onAfslut={afslutVurdering}
            onEksporter={handleEksporter}
          />
        )}

        {/* Doughnut ring */}
        <div className="max-w-3xl mx-auto mb-6">
          <DoughnutRing
            kommune={kommune}
            ratios={activeRatios}
            vurderingsMode={vurderingsMode}
            onVurderingKlik={handleVurderingKlik}
            vurderinger={vurderinger}
          />
        </div>

        {/* Summary */}
        <div className="text-sm text-gray-600 bg-gray-50 rounded-lg p-4 space-y-1 mb-6 max-w-3xl mx-auto">
          <p>
            <span className="font-medium">Socialt fundament:</span>{" "}
            {categoriesAboveThreshold} af {categoriesWithData} kategorier
            {categoriesWithData < 6 &&
              ` (${6 - categoriesWithData} mangler data)`}
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
                return (
                  <span className="text-gray-400">afventer data.</span>
                );
              }
              return (
                <span>
                  {ecoOvershoot.length} af {ecoWithData.length} dimensioner
                  overskredet
                  {ecoWithData.length < ECOLOGICAL_DIMENSIONS.length &&
                    ` (${ECOLOGICAL_DIMENSIONS.length - ecoWithData.length} afventer data)`}
                  .
                </span>
              );
            })()}
          </p>
        </div>

        {/* Score bars + "Start vurdering"-knap */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-gray-500">Kategorier</h3>
            {!vurderingsMode && (
              <button
                onClick={startVurdering}
                className="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-emerald-700 transition-colors"
              >
                Start vurdering →
              </button>
            )}
          </div>
          <ScoreBars
            kommune={kommune}
            ratios={activeRatios}
            vurderingsMode={vurderingsMode}
            vurderinger={vurderinger}
            onVurderingKlik={handleVurderingKlik}
          />
        </div>
      </div>

      {/* ========= PRINT-VIEW (skjult normalt, synlig ved print) ========= */}
      <div id="print-view">
        {vurderingsMode && (
          <VurderingPrintView
            projektnavn={projektnavn}
            beskrivelse={beskrivelse}
            kommune={kommune}
            ratios={activeRatios}
            vurderinger={vurderinger}
          />
        )}
      </div>

      {/* ========= VURDERINGSBOKS MODAL ========= */}
      {aktivDimension && (
        <div className="no-print">
          <VurderingBoks
            key={aktivDimension.id}
            dimId={aktivDimension.id}
            dimNavn={aktivDimension.navn}
            dimGruppe={aktivDimension.gruppe}
            eksisterende={vurderinger[aktivDimension.id]}
            onGem={handleGem}
            onLuk={() => setAktivDimension(null)}
          />
        </div>
      )}
    </>
  );
}
