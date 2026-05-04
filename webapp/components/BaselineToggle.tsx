"use client";

import { useBaseline, type BaselineMode } from "@/lib/baseline-context";

export default function BaselineToggle() {
  const { mode, setMode } = useBaseline();

  const options: { value: BaselineMode; label: string; title: string }[] = [
    {
      value: "avg",
      label: "Landsgennemsnit",
      title: "Scorer sammenlignes med det nationale gennemsnit (100 = gennemsnittet)",
    },
    {
      value: "top10",
      label: "Top 10%",
      title: "Scorer sammenlignes med de 10 bedst præsterende kommuner (100 = top 10%-niveauet)",
    },
  ];

  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="text-gray-400 text-xs hidden sm:inline">Baseline:</span>
      <div className="flex rounded-lg border border-gray-200 overflow-hidden">
        {options.map((opt) => (
          <button
            key={opt.value}
            onClick={() => setMode(opt.value)}
            title={opt.title}
            className={`px-2 sm:px-3 py-1.5 text-xs transition-colors ${
              mode === opt.value
                ? "bg-emerald-600 text-white font-medium"
                : "bg-white text-gray-600 hover:bg-gray-50"
            } ${opt.value === "top10" ? "border-l border-gray-200" : ""}`}
          >
            <span className="hidden sm:inline">{opt.label}</span>
            <span className="sm:hidden">{opt.value === "avg" ? "Gns" : "Top 10%"}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
