"use client";

import { useBaseline, type BaselineMode } from "@/lib/baseline-context";

export default function BaselineToggle() {
  const { mode, setMode } = useBaseline();

  const options: { value: BaselineMode; label: string; short: string; title: string }[] = [
    {
      value: "kommunegruppe",
      label: "Kommunegruppe",
      short: "Gruppe",
      title: "Scorer sammenlignes med gennemsnittet af kommuner i samme kommunegruppe (Hoved-, Storby-, Provinsby-, Oplands- eller Landkommuner)",
    },
    {
      value: "avg",
      label: "Landsgennemsnit",
      short: "Gns",
      title: "Scorer sammenlignes med det nationale gennemsnit (100 = gennemsnittet af alle 98 kommuner)",
    },
    {
      value: "top10",
      label: "Top 10%",
      short: "Top 10%",
      title: "Scorer sammenlignes med de 10 bedst præsterende kommuner (100 = top 10%-niveauet)",
    },
  ];

  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="text-gray-400 text-xs hidden sm:inline">Baseline:</span>
      <div className="flex rounded-lg border border-gray-200 overflow-hidden">
        {options.map((opt, i) => (
          <button
            key={opt.value}
            onClick={() => setMode(opt.value)}
            title={opt.title}
            className={`px-2 sm:px-3 py-1.5 text-xs transition-colors ${
              mode === opt.value
                ? "bg-emerald-600 text-white font-medium"
                : "bg-white text-gray-600 hover:bg-gray-50"
            } ${i > 0 ? "border-l border-gray-200" : ""}`}
          >
            <span className="hidden sm:inline">{opt.label}</span>
            <span className="sm:hidden">{opt.short}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
