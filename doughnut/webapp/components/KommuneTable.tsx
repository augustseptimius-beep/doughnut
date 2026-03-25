"use client";

import { useState, useMemo } from "react";
import { scoreColor } from "@/lib/shared";

interface KommuneRow {
  kode: string;
  navn: string;
  overall: number | null;
  social: number | null;
}

type SortKey = "navn" | "overall" | "social";
type SortDir = "asc" | "desc";

export default function KommuneTable({ data }: { data: KommuneRow[] }) {
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("overall");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir(key === "navn" ? "asc" : "desc");
    }
  };

  const sorted = useMemo(() => {
    const filtered = data.filter((k) =>
      k.navn.toLowerCase().includes(search.toLowerCase()) ||
      k.kode.includes(search)
    );

    return filtered.sort((a, b) => {
      const dir = sortDir === "asc" ? 1 : -1;
      if (sortKey === "navn") {
        return dir * a.navn.localeCompare(b.navn, "da");
      }
      const av = a[sortKey] ?? -1;
      const bv = b[sortKey] ?? -1;
      return dir * (av - bv);
    });
  }, [data, search, sortKey, sortDir]);

  const arrow = (key: SortKey) => {
    if (sortKey !== key) return "↕";
    return sortDir === "asc" ? "↑" : "↓";
  };

  return (
    <div>
      {/* Search */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Søg kommune..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full max-w-sm px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-300"
        />
      </div>

      {/* Table */}
      <div className="overflow-x-auto border border-gray-200 rounded-lg">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-3 py-2 font-medium text-gray-500 w-12">
                #
              </th>
              <th
                className="text-left px-3 py-2 font-medium text-gray-500 cursor-pointer hover:text-gray-700 select-none"
                onClick={() => toggleSort("navn")}
              >
                Kommune {arrow("navn")}
              </th>
              <th
                className="text-right px-3 py-2 font-medium text-gray-500 cursor-pointer hover:text-gray-700 select-none"
                onClick={() => toggleSort("overall")}
              >
                Samlet {arrow("overall")}
              </th>
              <th
                className="text-right px-3 py-2 font-medium text-gray-500 cursor-pointer hover:text-gray-700 select-none"
                onClick={() => toggleSort("social")}
              >
                Social {arrow("social")}
              </th>
              <th className="px-3 py-2 w-40">
                <span className="sr-only">Score bar</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((k, i) => (
              <tr
                key={k.kode}
                className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
              >
                <td className="px-3 py-2 text-gray-400 text-xs">{i + 1}</td>
                <td className="px-3 py-2">
                  <a
                    href={`/kommune/${encodeURIComponent(k.navn)}`}
                    className="text-gray-900 hover:text-blue-600 font-medium no-underline hover:underline"
                  >
                    {k.navn}
                  </a>
                </td>
                <td className={`px-3 py-2 text-right font-semibold ${scoreColor(k.overall)}`}>
                  {k.overall !== null ? k.overall.toFixed(1) : "–"}
                </td>
                <td className={`px-3 py-2 text-right ${scoreColor(k.social)}`}>
                  {k.social !== null ? k.social.toFixed(1) : "–"}
                </td>
                <td className="px-3 py-2">
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden relative">
                    <div
                      className="absolute top-0 bottom-0 w-px bg-gray-300"
                      style={{ left: `${(100 / 150) * 100}%` }}
                    />
                    <div
                      className={`h-full rounded-full transition-all ${
                        (k.overall ?? 0) >= 100
                          ? "bg-emerald-500"
                          : (k.overall ?? 0) >= 85
                          ? "bg-amber-400"
                          : "bg-red-400"
                      }`}
                      style={{
                        width: `${Math.min(((k.overall ?? 0) / 150) * 100, 100)}%`,
                      }}
                    />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-2 text-xs text-gray-400">
        {sorted.length} kommuner vist
      </div>
    </div>
  );
}
