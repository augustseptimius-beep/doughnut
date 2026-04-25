"use client";

interface Props {
  projektnavn: string;
  beskrivelse: string;
  vurderingerAntal: number;
  onProjektnavnChange: (val: string) => void;
  onBeskrivelseChange: (val: string) => void;
  onAfslut: () => void;
  onEksporter: () => void;
}

export default function VurderingsBjaelke({
  projektnavn,
  beskrivelse,
  vurderingerAntal,
  onProjektnavnChange,
  onBeskrivelseChange,
  onAfslut,
  onEksporter,
}: Props) {
  return (
    <div className="bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-3 mb-6 flex flex-wrap items-center gap-3">
      {/* Status-indikator */}
      <div className="flex items-center gap-2 shrink-0">
        <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
        <span className="text-sm font-bold text-emerald-700">Vurderingsmode</span>
        {vurderingerAntal > 0 && (
          <span className="text-xs text-emerald-700 bg-emerald-100 border border-emerald-200 px-2 py-0.5 rounded-full font-medium">
            {vurderingerAntal} vurderet
          </span>
        )}
      </div>

      {/* Projektnavn */}
      <div className="flex items-center gap-1.5">
        <label className="text-xs text-gray-500 shrink-0">Projekt:</label>
        <input
          value={projektnavn}
          onChange={(e) => onProjektnavnChange(e.target.value)}
          placeholder="Navn på projekt..."
          className="border border-gray-200 rounded-md px-2 py-1 text-sm w-44 focus:outline-none focus:ring-1 focus:ring-emerald-400"
        />
      </div>

      {/* Beskrivelse */}
      <div className="flex items-center gap-1.5 flex-1 min-w-0">
        <label className="text-xs text-gray-500 shrink-0">Beskrivelse:</label>
        <input
          value={beskrivelse}
          onChange={(e) => onBeskrivelseChange(e.target.value)}
          placeholder="Kort beskrivelse..."
          className="border border-gray-200 rounded-md px-2 py-1 text-sm flex-1 min-w-0 focus:outline-none focus:ring-1 focus:ring-emerald-400"
        />
      </div>

      {/* Handlingsknapper */}
      <div className="flex gap-2 shrink-0">
        <button
          onClick={onAfslut}
          className="px-3 py-1.5 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Afslut
        </button>
        <button
          onClick={onEksporter}
          className="px-3 py-1.5 text-xs font-semibold text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors"
        >
          Eksportér PDF
        </button>
      </div>
    </div>
  );
}
