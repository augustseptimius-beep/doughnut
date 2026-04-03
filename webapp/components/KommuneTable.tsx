"use client";

import { useState, useMemo } from "react";
import { SOCIAL_CATEGORIES, ECOLOGICAL_DIMENSIONS, scoreColor } from "@/lib/shared";
import { useBaseline } from "@/lib/baseline-context";

function ecoScoreColor(score: number | null): string {
  if (score === null) return "text-gray-400";
  if (score <= 85) return "text-emerald-600";   // klart under grænsen = godt
  if (score <= 100) return "text-amber-500";    // tæt på grænsen
  return "text-red-500";                         // overshoot
}

interface KommuneRow {
  kode: string;
  navn: string;
  overall: number | null;
  top10_overall: number | null;
  categories: Record<string, number | null>;
  top10_categories: Record<string, number | null>;
  eco_categories?: Record<string, number | null>;
}

type SortKey = "navn" | "overall" | string;
type SortDir = "asc" | "desc";
type ViewMode = "social" | "eco";

const REGION_MAP: Record<string, string> = {
  "101": "Hovedstaden", "147": "Hovedstaden", "151": "Hovedstaden",
  "153": "Hovedstaden", "155": "Hovedstaden", "157": "Hovedstaden",
  "159": "Hovedstaden", "161": "Hovedstaden", "163": "Hovedstaden",
  "165": "Hovedstaden", "167": "Hovedstaden", "169": "Hovedstaden",
  "173": "Hovedstaden", "175": "Hovedstaden", "183": "Hovedstaden",
  "185": "Hovedstaden", "187": "Hovedstaden", "190": "Hovedstaden",
  "201": "Hovedstaden", "210": "Hovedstaden", "217": "Hovedstaden",
  "219": "Hovedstaden", "223": "Hovedstaden", "230": "Hovedstaden",
  "240": "Hovedstaden", "250": "Hovedstaden", "260": "Hovedstaden",
  "270": "Hovedstaden", "400": "Hovedstaden",
  "253": "Sjælland", "259": "Sjælland", "265": "Sjælland",
  "269": "Sjælland", "306": "Sjælland", "316": "Sjælland",
  "320": "Sjælland", "326": "Sjælland", "329": "Sjælland",
  "330": "Sjælland", "336": "Sjælland", "340": "Sjælland",
  "350": "Sjælland", "360": "Sjælland", "370": "Sjælland",
  "376": "Sjælland", "390": "Sjælland",
  "410": "Syddanmark", "420": "Syddanmark", "430": "Syddanmark",
  "440": "Syddanmark", "450": "Syddanmark", "461": "Syddanmark",
  "479": "Syddanmark", "480": "Syddanmark", "482": "Syddanmark",
  "492": "Syddanmark", "510": "Syddanmark", "530": "Syddanmark",
  "540": "Syddanmark", "550": "Syddanmark", "561": "Syddanmark",
  "563": "Syddanmark", "573": "Syddanmark", "575": "Syddanmark",
  "580": "Syddanmark", "607": "Syddanmark", "621": "Syddanmark",
  "630": "Syddanmark",
  "615": "Midtjylland", "657": "Midtjylland", "661": "Midtjylland",
  "665": "Midtjylland", "671": "Midtjylland", "706": "Midtjylland",
  "707": "Midtjylland", "710": "Midtjylland", "727": "Midtjylland",
  "730": "Midtjylland", "740": "Midtjylland", "741": "Midtjylland",
  "746": "Midtjylland", "751": "Midtjylland", "756": "Midtjylland",
  "760": "Midtjylland", "766": "Midtjylland", "779": "Midtjylland",
  "791": "Midtjylland",
  "773": "Nordjylland", "787": "Nordjylland", "810": "Nordjylland",
  "813": "Nordjylland", "820": "Nordjylland", "825": "Nordjylland",
  "840": "Nordjylland", "846": "Nordjylland", "849": "Nordjylland",
  "851": "Nordjylland", "860": "Nordjylland",
};

const REGIONS = ["Alle regioner", "Hovedstaden", "Sjælland", "Syddanmark", "Midtjylland", "Nordjylland"];

// Vis alle økologiske dimensioner - dem uden data viser bare "–"
const ECO_DIMS_WITH_DATA = ECOLOGICAL_DIMENSIONS;

export default function KommuneTable({ data }: { data: KommuneRow[] }) {
  const { mode } = useBaseline();
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("overall");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [region, setRegion] = useState("Alle regioner");
  const [view, setView] = useState<ViewMode>("social");

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir(key === "navn" ? "asc" : "desc");
    }
  };

  const sorted = useMemo(() => {
    const filtered = data.filter((k) => {
      const matchSearch =
        k.navn.toLowerCase().includes(search.toLowerCase()) ||
        k.kode.includes(search);
      const matchRegion =
        region === "Alle regioner" || REGION_MAP[k.kode] === region;
      return matchSearch && matchRegion;
    });
    return filtered.sort((a, b) => {
      const dir = sortDir === "asc" ? 1 : -1;
      if (sortKey === "navn") return dir * a.navn.localeCompare(b.navn, "da");
      if (sortKey === "overall") {
        const aVal = mode === "top10" ? (a.top10_overall ?? -1) : (a.overall ?? -1);
        const bVal = mode === "top10" ? (b.top10_overall ?? -1) : (b.overall ?? -1);
        return dir * (aVal - bVal);
      }
      const aCats = mode === "top10" ? a.top10_categories : a.categories;
      const bCats = mode === "top10" ? b.top10_categories : b.categories;
      const av = aCats[sortKey] ?? a.eco_categories?.[sortKey] ?? -1;
      const bv = bCats[sortKey] ?? b.eco_categories?.[sortKey] ?? -1;
      return dir * (av - bv);
    });
  }, [data, search, sortKey, sortDir, region, mode]);

  const arrow = (key: SortKey) => {
    if (sortKey !== key) return <span className="text-gray-300 ml-0.5">↕</span>;
    return <span className="text-gray-600 ml-0.5">{sortDir === "asc" ? "↑" : "↓"}</span>;
  };

  const activeColumns = view === "social" ? SOCIAL_CATEGORIES : ECO_DIMS_WITH_DATA;

  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-3 items-center">
        <input
          type="text"
          placeholder="Søg kommune..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 w-48"
        />
        <select
          value={region}
          onChange={(e) => setRegion(e.target.value)}
          className="px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-200"
        >
          {REGIONS.map((r) => <option key={r} value={r}>{r}</option>)}
        </select>
        <div className="ml-auto flex rounded-lg border border-gray-200 overflow-hidden text-sm">
          <button
            onClick={() => { setView("social"); setSortKey("overall"); }}
            className={`px-3 py-2 transition-colors ${view === "social" ? "bg-emerald-600 text-white" : "bg-white text-gray-600 hover:bg-gray-50"}`}
          >
            Socialt fundament
          </button>
          <button
            onClick={() => { setView("eco"); setSortKey("overall"); }}
            className={`px-3 py-2 transition-colors border-l border-gray-200 ${view === "eco" ? "bg-emerald-600 text-white" : "bg-white text-gray-600 hover:bg-gray-50"}`}
          >
            Økologisk loft
          </button>
        </div>
      </div>

      <div className="overflow-x-auto border border-gray-200 rounded-lg">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-3 py-2 font-medium text-gray-500 w-10">#</th>
              <th className="text-left px-3 py-2 font-medium text-gray-500 cursor-pointer hover:text-gray-700 select-none" onClick={() => toggleSort("navn")}>
                Kommune {arrow("navn")}
              </th>
              <th className="text-left px-2 py-2 font-medium text-gray-400 text-xs w-28">Region</th>
              <th className="text-right px-3 py-2 font-medium text-gray-500 cursor-pointer hover:text-gray-700 select-none" onClick={() => toggleSort("overall")}>
                Samlet {arrow("overall")}
              </th>
              {activeColumns.map((col) => (
                <th
                  key={col.id}
                  className="text-right px-2 py-2 font-medium text-gray-500 cursor-pointer hover:text-gray-700 select-none text-xs min-w-[72px]"
                  onClick={() => toggleSort(col.id)}
                  title={col.name}
                >
                  <span className="block truncate max-w-[80px] text-right">{col.name}</span>
                  {arrow(col.id)}
                </th>
              ))}
              <th className="px-3 py-2 w-28"><span className="sr-only">Score bar</span></th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((k, i) => (
              <tr key={k.kode} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                <td className="px-3 py-2 text-gray-400 text-xs">{i + 1}</td>
                <td className="px-3 py-2">
                  <a href={`/kommune/${encodeURIComponent(k.navn)}`} className="text-gray-900 hover:text-blue-600 font-medium no-underline hover:underline">
                    {k.navn}
                  </a>
                </td>
                <td className="px-2 py-2 text-xs text-gray-400">{REGION_MAP[k.kode] ?? "–"}</td>
                {(() => {
                  const overallVal = view === "eco"
                    ? k.overall
                    : (mode === "top10" ? k.top10_overall : k.overall);
                  return (
                    <td className={`px-3 py-2 text-right font-semibold ${view === "eco" ? ecoScoreColor(overallVal) : scoreColor(overallVal)}`}>
                      {overallVal !== null ? overallVal.toFixed(1) : "–"}
                    </td>
                  );
                })()}
                {activeColumns.map((col) => {
                  const cats = mode === "top10" ? k.top10_categories : k.categories;
                  const val = view === "social"
                    ? (cats[col.id] ?? null)
                    : (k.eco_categories?.[col.id] ?? null);
                  return (
                    <td key={col.id} className={`px-2 py-2 text-right text-xs ${view === "eco" ? ecoScoreColor(val) : scoreColor(val)}`}>
                      {val !== null ? val.toFixed(1) : "–"}
                    </td>
                  );
                })}
                <td className="px-3 py-2">
                  {(() => {
                    const barVal = view === "eco"
                      ? (k.overall ?? 0)
                      : (mode === "top10" ? (k.top10_overall ?? 0) : (k.overall ?? 0));
                    return (
                      <div className="h-2 bg-gray-100 rounded-full overflow-hidden relative">
                        <div className="absolute top-0 bottom-0 w-px bg-gray-300" style={{ left: `${(100 / 150) * 100}%` }} />
                        <div
                          className={`h-full rounded-full transition-all ${
                            view === "eco"
                              ? (barVal <= 85 ? "bg-emerald-500" : barVal <= 100 ? "bg-amber-400" : "bg-red-500")
                              : (barVal >= 100 ? "bg-emerald-500" : barVal >= 85 ? "bg-amber-400" : "bg-red-400")
                          }`}
                          style={{ width: `${Math.min((barVal / 150) * 100, 100)}%` }}
                        />
                      </div>
                    );
                  })()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-2 text-xs text-gray-400 flex items-center gap-3">
        <span>{sorted.length} kommuner vist</span>
        {view === "eco" && (
          <span className="text-gray-300">Scorer under 100 = inden for grænsen &middot; over 100 = overshoot</span>
        )}
      </div>
    </div>
  );
}
