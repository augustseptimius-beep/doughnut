"use client";

import { useState, useEffect } from "react";
import type { VurderingScore, VurderingEntry } from "@/lib/vurdering";

interface Props {
  dimId: string;
  dimNavn: string;
  dimGruppe: "social" | "ecological";
  eksisterende?: VurderingEntry;
  onGem: (dimId: string, score: VurderingScore, argumentation: string) => void;
  onLuk: () => void;
}

const SCORE_CONFIG = {
  roed: {
    label: "Negativ",
    emoji: "🔴",
    active: "bg-red-500 text-white border-red-500",
    inactive: "bg-white text-red-600 border-red-200 hover:border-red-400",
  },
  gul: {
    label: "Ukendt / ingen",
    emoji: "🟡",
    active: "bg-amber-400 text-white border-amber-400",
    inactive: "bg-white text-amber-600 border-amber-200 hover:border-amber-400",
  },
  groen: {
    label: "Positiv",
    emoji: "🟢",
    active: "bg-emerald-500 text-white border-emerald-500",
    inactive: "bg-white text-emerald-600 border-emerald-200 hover:border-emerald-400",
  },
} as const;

export default function VurderingBoks({
  dimId,
  dimNavn,
  dimGruppe,
  eksisterende,
  onGem,
  onLuk,
}: Props) {
  const [score, setScore] = useState<VurderingScore>(eksisterende?.score ?? null);
  const [argumentation, setArgumentation] = useState(
    eksisterende?.argumentation ?? ""
  );

  // Luk modal ved Esc-tryk
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onLuk();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onLuk]);

  return (
    // Klik på backdrop lukker modal
    <div
      className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4"
      onClick={onLuk}
    >
      <div
        className="bg-white rounded-xl shadow-2xl w-full max-w-md p-6"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div>
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
              {dimGruppe === "social" ? "Socialt fundament" : "Økologisk loft"}
            </p>
            <h3 className="text-lg font-bold text-gray-900">{dimNavn}</h3>
          </div>
          <button
            onClick={onLuk}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none ml-4 mt-0.5"
            aria-label="Luk"
          >
            ✕
          </button>
        </div>

        <p className="text-sm text-gray-600 mb-3">
          Hvad er projektets sandsynlige påvirkning på denne dimension?
        </p>

        {/* Vurderingsknapper */}
        <div className="flex gap-2 mb-4">
          {(["roed", "gul", "groen"] as const).map((s) => {
            const cfg = SCORE_CONFIG[s];
            return (
              <button
                key={s}
                onClick={() => setScore(s)}
                className={`flex-1 py-2.5 rounded-lg text-xs font-semibold border-2 transition-all flex flex-col items-center gap-1 ${
                  score === s ? cfg.active : cfg.inactive
                }`}
              >
                <span className="text-base">{cfg.emoji}</span>
                <span>{cfg.label}</span>
              </button>
            );
          })}
        </div>

        {/* Argumentationstekst */}
        <textarea
          value={argumentation}
          onChange={(e) => setArgumentation(e.target.value)}
          placeholder="Kort argumentation (valgfrit)..."
          rows={3}
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-emerald-400 resize-none"
        />

        {/* Handlingsknapper */}
        <div className="flex gap-2 mt-4">
          <button
            onClick={onLuk}
            className="flex-1 py-2 rounded-lg text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 transition-colors"
          >
            Annuller
          </button>
          <button
            onClick={() => onGem(dimId, score, argumentation)}
            disabled={score === null}
            className="flex-1 py-2 rounded-lg text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Gem vurdering
          </button>
        </div>
      </div>
    </div>
  );
}
