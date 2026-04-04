"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { SearchIcon } from "lucide-react";

interface Kommune {
  kommune_navn: string;
  kommune_kode: string;
}

interface KommuneSearchProps {
  kommuner: Kommune[];
  exampleKommuner: Kommune[];
}

export default function KommuneSearch({
  kommuner,
  exampleKommuner,
}: KommuneSearchProps) {
  const [searchTerm, setSearchTerm] = useState("");

  const filteredKommuner = useMemo(() => {
    if (!searchTerm.trim()) return [];
    return kommuner.filter((k) =>
      k.kommune_navn.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [searchTerm, kommuner]);

  const displayedKommuner = searchTerm.trim() ? filteredKommuner : exampleKommuner;

  return (
    <div className="w-full">
      {/* Search Box */}
      <div className="mb-8">
        <div className="relative">
          <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Søg efter en kommune..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-600 focus:border-transparent"
          />
        </div>
        {searchTerm.trim() && (
          <p className="text-sm text-gray-600 mt-2">
            Fandt {filteredKommuner.length} kommuner
          </p>
        )}
      </div>

      {/* Results Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {displayedKommuner.map((kommune) => (
          <Link
            key={kommune.kommune_kode}
            href={`/kommune/${encodeURIComponent(kommune.kommune_navn)}`}
            className="block p-4 border border-gray-200 rounded-lg hover:border-green-600 hover:shadow-md transition-all hover:bg-green-50"
          >
            <h3 className="text-lg font-semibold text-gray-900">
              {kommune.kommune_navn}
            </h3>
            <p className="text-sm text-gray-500 mt-1">
              Kommunekode: {kommune.kommune_kode}
            </p>
          </Link>
        ))}
      </div>

      {searchTerm.trim() && filteredKommuner.length === 0 && (
        <div className="text-center py-8">
          <p className="text-gray-500">
            Ingen kommuner fundet for "{searchTerm}"
          </p>
        </div>
      )}
    </div>
  );
}
