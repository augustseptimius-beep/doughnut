"use client";

import { useState } from "react";
import type { KommuneData } from "@/lib/shared";

interface KommuneCompareProps {
  allKommuner: KommuneData[];
  current: string;
  onSelect: (kommune: KommuneData | null) => void;
}

export default function KommuneCompare({ allKommuner, current, onSelect }: KommuneCompareProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<KommuneData | null>(null);

  const filtered = allKommuner
    .filter(
      (k) =>
        k.kommune_navn.toLowerCase() !== current.toLowerCase() &&
        k.kommune_navn.toLowerCase().includes(search.toLowerCase())
    )
    .slice(0, 20);

  return (
    <div className="relative">
      {selected ? (
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Sammenligner med:</span>
          <span className="text-sm font-medium text-gray-900">{selected.kommune_navn}</span>
          <button
            onClick={() => {
              setSelected(null);
              onSelect(null);
              setSearch("");
            }}
            className="text-xs text-red-500 hover:text-red-700"
          >
            ✕
          </button>
        </div>
      ) : (
        <button
          onClick={() => setOpen(!open)}
          className="text-sm text-blue-600 hover:text-blue-800 border border-blue-200 rounded-lg px-3 py-1.5 hover:bg-blue-50 transition-colors"
        >
          + Sammenlign med anden kommune
        </button>
      )}

      {open && !selected && (
        <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-20">
          <div className="p-2">
            <input
              type="text"
              placeholder="Søg kommune..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full px-2 py-1.5 text-sm border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-blue-300"
              autoFocus
            />
          </div>
          <div className="max-h-48 overflow-y-auto">
            {filtered.map((k) => (
              <button
                key={k.kommune_kode}
                onClick={() => {
                  setSelected(k);
                  onSelect(k);
                  setOpen(false);
                  setSearch("");
                }}
                className="w-full text-left px-3 py-1.5 text-sm hover:bg-gray-50 transition-colors"
              >
                {k.kommune_navn}
              </button>
            ))}
            {filtered.length === 0 && (
              <div className="px-3 py-2 text-sm text-gray-400">Ingen resultater</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
