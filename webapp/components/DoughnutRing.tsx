"use client";

import { useState, useRef, useEffect } from "react";
import {
  type KommuneData,
  ECOLOGICAL_DIMENSIONS,
  SOCIAL_CATEGORIES,
  INDICATORS,
  computeCategoryScores,
} from "@/lib/shared";

interface DoughnutRingProps {
  kommune: KommuneData;
}

function describeArc(
  cx: number,
  cy: number,
  rOuter: number,
  rInner: number,
  startAngle: number,
  endAngle: number
): string {
  const x1 = cx + rOuter * Math.cos(startAngle);
  const y1 = cy + rOuter * Math.sin(startAngle);
  const x2 = cx + rOuter * Math.cos(endAngle);
  const y2 = cy + rOuter * Math.sin(endAngle);
  const x3 = cx + rInner * Math.cos(endAngle);
  const y3 = cy + rInner * Math.sin(endAngle);
  const x4 = cx + rInner * Math.cos(startAngle);
  const y4 = cy + rInner * Math.sin(startAngle);
  const largeArc = endAngle - startAngle <= Math.PI ? "0" : "1";
  return `M ${x1} ${y1} A ${rOuter} ${rOuter} 0 ${largeArc} 1 ${x2} ${y2} L ${x3} ${y3} A ${rInner} ${rInner} 0 ${largeArc} 0 ${x4} ${y4} Z`;
}

const vbSize = 1000;
const center = vbSize / 2;
const innerLimit = 60;
const socialBase = 200;
const commonBoundary = 290;
const ecoCeiling = 380;
const outerLimit = 460;
const gap = 0.04;

/* Label radius for placing text outside the ring */
const ecoLabelRadius = outerLimit + 40;
const socialLabelRadius = innerLimit - 15;

interface ActiveInfo {
  id: string;
  label: string;
  group: "social" | "ecological";
  score: number | null;
  hasData: boolean;
  description?: string;
  indicators?: string[];
  unit?: string;
  boundary?: string;
}

/* ── Emoji/symbol map for eco dimensions ── */
const ECO_SYMBOLS: Record<string, string> = {
  klimapaavirkning: "🌡",
  forurening: "🧪",
  luftkvalitet: "💨",
  cirkularitet: "♻️",
  naeringsstoffer: "🌾",
  vand: "💧",
  arealanvendelse: "🌳",
  biodiversitet: "🦋",
  forbrug_co2: "🛒",
};

const SOCIAL_SYMBOLS: Record<string, string> = {
  sundhed: "❤️",
  uddannelse: "📚",
  velfaerd: "💰",
  bolig: "🏠",
  samskabelse: "🗳",
  faellesskaber: "🤝",
  lokalsamfund: "🏘",
  mobilitet: "🚲",
  klimatilpasning: "🛡",
};

export default function DoughnutRing({ kommune }: DoughnutRingProps) {
  const [active, setActive] = useState<ActiveInfo | null>(null);
  const [pinned, setPinned] = useState(false);

  const categoryScores = computeCategoryScores(kommune.ratios);
  const socialCount = categoryScores.length;
  const ecoCount = ECOLOGICAL_DIMENSIONS.length;

  const handleClick = (info: ActiveInfo) => {
    if (pinned && active?.id === info.id && active?.group === info.group) {
      setPinned(false);
      setActive(null);
    } else {
      setActive(info);
      setPinned(true);
    }
  };

  const handleHover = (info: ActiveInfo) => {
    if (!pinned) setActive(info);
  };

  const handleLeave = () => {
    if (!pinned) setActive(null);
  };

  /* ── Render labels around the outside of eco ring ── */
  const renderEcoLabels = () => {
    const angleStep = (2 * Math.PI) / ecoCount;
    return ECOLOGICAL_DIMENSIONS.map((dim, i) => {
      const startAngle = i * angleStep - Math.PI / 2 + gap / 2;
      const endAngle = (i + 1) * angleStep - Math.PI / 2 - gap / 2;
      const midAngle = (startAngle + endAngle) / 2;

      const lx = center + ecoLabelRadius * Math.cos(midAngle);
      const ly = center + ecoLabelRadius * Math.sin(midAngle);

      const ecoScore = kommune.eco_ratios[dim.id] ?? null;
      const hasData = ecoScore !== null;
      const isActive = active?.id === dim.id && active?.group === "ecological";

      // Determine text anchor based on position
      const angleDeg = (midAngle * 180) / Math.PI;
      let anchor: "start" | "middle" | "end" = "middle";
      if (angleDeg > 20 && angleDeg < 160) anchor = "start";
      else if (angleDeg > 200 && angleDeg < 340) anchor = "end";

      return (
        <text
          key={`label-${dim.id}`}
          x={lx}
          y={ly}
          textAnchor={anchor}
          dominantBaseline="middle"
          className="pointer-events-none select-none"
          style={{
            fontSize: "11px",
            fontWeight: isActive ? 900 : 600,
            fill: hasData ? (isActive ? "#166534" : "#374151") : "#9ca3af",
            transition: "fill 0.2s",
          }}
        >
          {dim.name}
        </text>
      );
    });
  };

  const renderSocialRing = () => {
    const angleStep = (2 * Math.PI) / socialCount;
    return categoryScores.map((cat, i) => {
      const startAngle = i * angleStep - Math.PI / 2 + gap / 2;
      const endAngle = (i + 1) * angleStep - Math.PI / 2 - gap / 2;
      const midAngle = (startAngle + endAngle) / 2;

      const safePath = describeArc(center, center, commonBoundary, socialBase, startAngle, endAngle);

      let shortfallPath = "";
      if (cat.hasData && cat.score !== null && cat.score < 100) {
        const shortfallFraction = (100 - cat.score) / 100;
        const amplified = Math.max(Math.pow(Math.min(shortfallFraction, 1), 0.35), 0.18);
        const rIn = socialBase - (socialBase - innerLimit) * amplified;
        shortfallPath = describeArc(center, center, socialBase, rIn, startAngle, endAngle);
      }

      // Symbol inside the segment
      const symbolRadius = (socialBase + commonBoundary) / 2;
      const sx = center + symbolRadius * Math.cos(midAngle);
      const sy = center + symbolRadius * Math.sin(midAngle);

      const isNoData = !cat.hasData;
      const isActive = active?.id === cat.categoryId && active?.group === "social";
      const safeColor = isNoData ? "#e5e7eb" : isActive ? "#bbf7d0" : "#e8f0e8";
      const safeStroke = isNoData ? "#d1d5db" : "#8faa8f";

      const catDef = SOCIAL_CATEGORIES.find((c) => c.id === cat.categoryId);
      const indicatorNames = cat.indicators.map((ind) => ind.indicator.name);

      const info: ActiveInfo = {
        id: cat.categoryId,
        label: cat.categoryName,
        group: "social",
        score: cat.score,
        hasData: cat.hasData,
        description: catDef?.description,
        indicators: indicatorNames.length > 0 ? indicatorNames : undefined,
      };

      return (
        <g
          key={cat.categoryId}
          className="cursor-pointer"
          onClick={() => handleClick(info)}
          onMouseEnter={() => handleHover(info)}
          onMouseLeave={handleLeave}
        >
          <path d={safePath} fill={safeColor} stroke={safeStroke} strokeWidth="0.5" className="transition-colors" />
          {shortfallPath && (
            <path d={shortfallPath} fill="#dc2626" opacity="0.85" className="transition-all duration-300" />
          )}
          <line
            x1={center + innerLimit * Math.cos(startAngle - gap / 2)}
            y1={center + innerLimit * Math.sin(startAngle - gap / 2)}
            x2={center + commonBoundary * Math.cos(startAngle - gap / 2)}
            y2={center + commonBoundary * Math.sin(startAngle - gap / 2)}
            stroke="#94a3b8" strokeWidth="0.5" strokeOpacity="0.15"
          />
          {/* Symbol */}
          <text
            x={sx} y={sy} textAnchor="middle" dominantBaseline="middle"
            className="pointer-events-none select-none"
            style={{ fontSize: "18px" }}
          >
            {SOCIAL_SYMBOLS[cat.categoryId] || "●"}
          </text>
        </g>
      );
    });
  };

  const renderSocialLabels = () => {
    const angleStep = (2 * Math.PI) / socialCount;
    return categoryScores.map((cat, i) => {
      const startAngle = i * angleStep - Math.PI / 2 + gap / 2;
      const endAngle = (i + 1) * angleStep - Math.PI / 2 - gap / 2;
      const midAngle = (startAngle + endAngle) / 2;

      // Place labels in the inner "hole" area
      const lr = socialBase - 25;
      const lx = center + lr * Math.cos(midAngle);
      const ly = center + lr * Math.sin(midAngle);

      const isNoData = !cat.hasData;
      const isActive = active?.id === cat.categoryId && active?.group === "social";

      const angleDeg = (midAngle * 180) / Math.PI;
      let anchor: "start" | "middle" | "end" = "middle";
      if (angleDeg > 20 && angleDeg < 160) anchor = "start";
      else if (angleDeg > 200 && angleDeg < 340) anchor = "end";

      // Truncate long names for inside labels
      const name = cat.categoryName.length > 16
        ? cat.categoryName.slice(0, 14) + "…"
        : cat.categoryName;

      return (
        <text
          key={`slabel-${cat.categoryId}`}
          x={lx} y={ly}
          textAnchor={anchor}
          dominantBaseline="middle"
          className="pointer-events-none select-none"
          style={{
            fontSize: "9px",
            fontWeight: isActive ? 800 : 600,
            fill: isNoData ? "#9ca3af" : (isActive ? "#166534" : "#4b5563"),
            transition: "fill 0.2s",
          }}
        >
          {name}
        </text>
      );
    });
  };

  const renderEcoRing = () => {
    const angleStep = (2 * Math.PI) / ecoCount;
    return ECOLOGICAL_DIMENSIONS.map((dim, i) => {
      const startAngle = i * angleStep - Math.PI / 2 + gap / 2;
      const endAngle = (i + 1) * angleStep - Math.PI / 2 - gap / 2;
      const midAngle = (startAngle + endAngle) / 2;

      const ecoScore = kommune.eco_ratios[dim.id] ?? null;
      const hasEcoData = ecoScore !== null;

      const safePath = describeArc(center, center, ecoCeiling, commonBoundary, startAngle, endAngle);

      let overshootPath = "";
      if (hasEcoData && ecoScore > 100) {
        const overshootFraction = (ecoScore - 100) / 100;
        const amplified = Math.max(Math.pow(Math.min(overshootFraction, 1), 0.35), 0.18);
        const rOut = ecoCeiling + (outerLimit - ecoCeiling) * amplified;
        overshootPath = describeArc(center, center, rOut, ecoCeiling, startAngle, endAngle);
      }

      // Symbol inside the eco segment
      const symbolRadius = (commonBoundary + ecoCeiling) / 2;
      const sx = center + symbolRadius * Math.cos(midAngle);
      const sy = center + symbolRadius * Math.sin(midAngle);

      const isActive = active?.id === dim.id && active?.group === "ecological";
      const safeColor = hasEcoData ? (isActive ? "#bbf7d0" : "#e8f0e8") : "#f3f4f6";
      const safeStroke = hasEcoData ? "#8faa8f" : "#d1d5db";

      const info: ActiveInfo = {
        id: dim.id,
        label: dim.name,
        group: "ecological",
        score: ecoScore,
        hasData: hasEcoData,
        description: dim.description,
        unit: dim.unit,
        boundary: dim.boundary,
      };

      return (
        <g
          key={dim.id}
          className="cursor-pointer"
          onClick={() => handleClick(info)}
          onMouseEnter={() => handleHover(info)}
          onMouseLeave={handleLeave}
        >
          <path d={safePath} fill={safeColor} stroke={safeStroke} strokeWidth="0.5" className="transition-colors" />
          {overshootPath && (
            <path d={overshootPath} fill="#dc2626" opacity="0.85" className="transition-all duration-300" />
          )}
          <line
            x1={center + commonBoundary * Math.cos(startAngle - gap / 2)}
            y1={center + commonBoundary * Math.sin(startAngle - gap / 2)}
            x2={center + outerLimit * Math.cos(startAngle - gap / 2)}
            y2={center + outerLimit * Math.sin(startAngle - gap / 2)}
            stroke="#94a3b8" strokeWidth="0.5" strokeOpacity="0.15"
          />
          {/* Symbol */}
          <text
            x={sx} y={sy} textAnchor="middle" dominantBaseline="middle"
            className="pointer-events-none select-none"
            style={{ fontSize: "18px" }}
          >
            {ECO_SYMBOLS[dim.id] || "●"}
          </text>
        </g>
      );
    });
  };

  const getStatusText = (info: ActiveInfo): string => {
    if (!info.hasData || info.score === null) return "Mangler data";
    if (info.group === "social") {
      return info.score >= 100 ? "Mål nået" : `Shortfall ${(100 - info.score).toFixed(1)}%`;
    }
    return info.score <= 100 ? "Inden for grænsen" : `Overshoot ${(info.score - 100).toFixed(1)}%`;
  };

  const getStatusColor = (info: ActiveInfo): string => {
    if (!info.hasData || info.score === null) return "text-gray-400";
    if (info.group === "social") return info.score >= 100 ? "text-emerald-600" : "text-red-500";
    return info.score <= 100 ? "text-emerald-600" : "text-red-500";
  };

  return (
    <div className="relative w-full">
      <div className="relative w-full aspect-square flex items-center justify-center">
        <svg viewBox={`-80 -80 ${vbSize + 160} ${vbSize + 160}`} className="w-full h-full" preserveAspectRatio="xMidYMid meet">
          <circle cx={center} cy={center} r={outerLimit + 10} fill="#fafafa" opacity="0.5" />

          {renderEcoRing()}
          {renderSocialRing()}

          {/* Boundary circles */}
          <circle cx={center} cy={center} r={ecoCeiling} fill="none" stroke="#166534" strokeWidth="2.5" opacity="0.6" />
          <circle cx={center} cy={center} r={socialBase} fill="none" stroke="#166534" strokeWidth="2.5" opacity="0.6" />

          {/* Clean center */}
          <circle cx={center} cy={center} r={socialBase - 5} fill="white" opacity="0.9" />

          {/* Labels around outside */}
          {renderEcoLabels()}
          {renderSocialLabels()}

          {/* Ring labels at top/bottom */}
          <text x={center} y={center - ecoCeiling - 55} textAnchor="middle"
            style={{ fontSize: "11px", fontWeight: 800, fill: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.2em" }}>
            Økologisk loft
          </text>
          <text x={center} y={center + ecoCeiling + 65} textAnchor="middle"
            style={{ fontSize: "11px", fontWeight: 800, fill: "#6b7280", textTransform: "uppercase", letterSpacing: "0.2em" }}>
            Socialt fundament
          </text>
        </svg>

        {/* Info card */}
        {active && (
          <div className={`absolute bottom-2 right-2 md:top-2 md:right-2 bg-white/95 backdrop-blur-md shadow-2xl p-4 rounded-2xl w-56 md:w-64 border border-gray-100 z-10 ${pinned ? "" : "pointer-events-none"}`}>
            <div className="flex items-center justify-between mb-2">
              <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full uppercase ${
                active.group === "social" ? "bg-emerald-100 text-emerald-700" : "bg-gray-100 text-gray-500"
              }`}>
                {active.group === "social" ? "Socialt fundament" : "Økologisk loft"}
              </span>
              {pinned && (
                <button
                  onClick={() => { setPinned(false); setActive(null); }}
                  className="text-gray-300 hover:text-gray-500 text-xs"
                >
                  ✕
                </button>
              )}
            </div>
            <h3 className="font-black text-base text-gray-800 leading-tight">
              {active.label}
            </h3>

            {active.description && (
              <p className="text-[11px] text-gray-500 mt-1 leading-snug line-clamp-3">
                {active.description}
              </p>
            )}

            <div className="mt-2">
              {active.hasData && active.score !== null ? (
                <p className="text-2xl font-black text-gray-900 tracking-tighter">
                  {active.score.toFixed(1)}%
                </p>
              ) : (
                <p className="text-sm font-medium text-gray-400">Ingen data endnu</p>
              )}
              <p className={`text-xs font-bold uppercase tracking-widest mt-0.5 ${getStatusColor(active)}`}>
                {getStatusText(active)}
              </p>
            </div>

            {/* Indicator list for social categories */}
            {active.indicators && active.indicators.length > 0 && (
              <div className="mt-2 pt-2 border-t border-gray-100">
                <p className="text-[9px] font-semibold text-gray-400 uppercase mb-1">Indikatorer</p>
                {active.indicators.map((name) => (
                  <p key={name} className="text-[11px] text-gray-600 leading-snug">
                    · {name}
                  </p>
                ))}
              </div>
            )}

            {/* Boundary info for eco dimensions */}
            {active.boundary && (
              <div className="mt-2 pt-2 border-t border-gray-100">
                <p className="text-[9px] font-semibold text-gray-400 uppercase mb-1">Grænseværdi</p>
                <p className="text-[11px] text-gray-600 leading-snug">{active.boundary}</p>
              </div>
            )}

            {active.unit && (
              <p className="text-[10px] text-gray-400 mt-1">Enhed: {active.unit}</p>
            )}

            {active.hasData && active.score !== null && (
              <div className="mt-2 h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 rounded-full ${
                    active.group === "social"
                      ? active.score >= 100 ? "bg-emerald-500" : "bg-red-400"
                      : active.score <= 100 ? "bg-emerald-500" : "bg-red-400"
                  }`}
                  style={{ width: `${Math.min(active.score, 200) / 2}%` }}
                />
              </div>
            )}

            <div className="flex items-center justify-between mt-2">
              <a
                href={`/metode#${active.id}`}
                className="text-[10px] text-blue-600 hover:underline pointer-events-auto"
              >
                Se metode →
              </a>
              {!pinned && (
                <p className="text-[9px] text-gray-300">Klik for at fastholde</p>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="flex flex-wrap justify-center gap-4 md:gap-6 mt-2 text-xs text-gray-500">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-[#e8f0e8] border border-[#8faa8f]" />
          <span className="font-medium">Safe space</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-red-500 opacity-70" />
          <span className="font-medium">Shortfall / Overshoot</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-gray-200 border border-gray-300" />
          <span className="font-medium">Mangler data</span>
        </div>
      </div>
    </div>
  );
}
