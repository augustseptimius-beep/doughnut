"use client";

import { useState } from "react";
import {
  type KommuneData,
  ECOLOGICAL_DIMENSIONS,
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
const socialBase = 220;
const commonBoundary = 310;
const ecoCeiling = 400;
const outerLimit = 480;
const gap = 0.04;

interface ActiveInfo {
  label: string;
  group: "social" | "ecological";
  score: number | null;
  hasData: boolean;
}

export default function DoughnutRing({ kommune }: DoughnutRingProps) {
  const [active, setActive] = useState<ActiveInfo | null>(null);

  const categoryScores = computeCategoryScores(kommune.ratios);
  const socialCount = categoryScores.length;
  const ecoCount = ECOLOGICAL_DIMENSIONS.length;

  const handleToggle = (info: ActiveInfo) => {
    setActive((prev) =>
      prev?.label === info.label && prev?.group === info.group ? null : info
    );
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
        // Amplify small shortfalls so even 5% under is clearly visible
        const shortfallFraction = (100 - cat.score) / 100;
        const amplified = Math.max(Math.pow(Math.min(shortfallFraction, 1), 0.35), 0.18);
        const rIn = socialBase - (socialBase - innerLimit) * amplified;
        shortfallPath = describeArc(center, center, socialBase, rIn, startAngle, endAngle);
      }

      const labelRadius = (socialBase + commonBoundary) / 2;
      const lx = center + labelRadius * Math.cos(midAngle);
      const ly = center + labelRadius * Math.sin(midAngle);

      const isNoData = !cat.hasData;
      const isActive = active?.label === cat.categoryName && active?.group === "social";
      const safeColor = isNoData ? "#e5e7eb" : isActive ? "#bbf7d0" : "#e8f0e8";
      const safeStroke = isNoData ? "#d1d5db" : "#8faa8f";

      const info: ActiveInfo = {
        label: cat.categoryName,
        group: "social",
        score: cat.score,
        hasData: cat.hasData,
      };

      return (
        <g
          key={cat.categoryId}
          className="cursor-pointer"
          onClick={() => handleToggle(info)}
          onMouseEnter={() => setActive(info)}
          onMouseLeave={() => setActive(null)}
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
          <text
            x={lx} y={ly} textAnchor="middle" dominantBaseline="middle"
            className="pointer-events-none select-none"
            style={{ fontSize: "13px", fontWeight: 800, fill: isNoData ? "#9ca3af" : "#2d4a2d", textTransform: "uppercase", letterSpacing: "0.02em" }}
          >
            {cat.categoryName}
          </text>
        </g>
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
        // Amplify small overshoots: cube root scaling so even 5% overshoot is clearly visible
        const overshootFraction = (ecoScore - 100) / 100;
        const amplified = Math.max(Math.pow(Math.min(overshootFraction, 1), 0.35), 0.18);
        const rOut = ecoCeiling + (outerLimit - ecoCeiling) * amplified;
        overshootPath = describeArc(center, center, rOut, ecoCeiling, startAngle, endAngle);
      }

      const labelRadius = (commonBoundary + ecoCeiling) / 2;
      const lx = center + labelRadius * Math.cos(midAngle);
      const ly = center + labelRadius * Math.sin(midAngle);

      const isActive = active?.label === dim.name && active?.group === "ecological";
      const safeColor = hasEcoData ? (isActive ? "#bbf7d0" : "#e8f0e8") : "#f3f4f6";
      const safeStroke = hasEcoData ? "#8faa8f" : "#d1d5db";

      const info: ActiveInfo = {
        label: dim.name,
        group: "ecological",
        score: ecoScore,
        hasData: hasEcoData,
      };

      return (
        <g
          key={dim.id}
          className="cursor-pointer"
          onClick={() => handleToggle(info)}
          onMouseEnter={() => setActive(info)}
          onMouseLeave={() => setActive(null)}
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
          <text
            x={lx} y={ly} textAnchor="middle" dominantBaseline="middle"
            className="pointer-events-none select-none"
            style={{ fontSize: "14px", fontWeight: 800, fill: hasEcoData ? "#2d4a2d" : "#9ca3af", textTransform: "uppercase", letterSpacing: "0.02em" }}
          >
            {dim.shortName}
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
        <svg viewBox={`0 0 ${vbSize} ${vbSize}`} className="w-full h-full" preserveAspectRatio="xMidYMid meet">
          <circle cx={center} cy={center} r={outerLimit + 10} fill="#fafafa" opacity="0.5" />

          {renderEcoRing()}
          {renderSocialRing()}

          <circle cx={center} cy={center} r={ecoCeiling} fill="none" stroke="#166534" strokeWidth="2.5" opacity="0.6" />
          <circle cx={center} cy={center} r={socialBase} fill="none" stroke="#166534" strokeWidth="2.5" opacity="0.6" />

          {/* Clean center - no score number */}
          <circle cx={center} cy={center} r={socialBase - 5} fill="white" opacity="0.9" />

          {/* Ring labels */}
          <text x={center} y={center - ecoCeiling - 30} textAnchor="middle"
            style={{ fontSize: "12px", fontWeight: 800, fill: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.2em" }}>
            Økologisk loft
          </text>
          <text x={center} y={center + ecoCeiling + 45} textAnchor="middle"
            style={{ fontSize: "12px", fontWeight: 800, fill: "#6b7280", textTransform: "uppercase", letterSpacing: "0.2em" }}>
            Socialt fundament
          </text>
        </svg>

        {/* Info card - visible when segment is active */}
        {active && (
          <div className="absolute bottom-4 right-4 md:top-4 md:right-4 bg-white/95 backdrop-blur-md shadow-2xl p-4 md:p-5 rounded-2xl w-48 md:w-56 border border-gray-100 pointer-events-none z-10">
            <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full uppercase ${
              active.group === "social" ? "bg-emerald-100 text-emerald-700" : "bg-gray-100 text-gray-500"
            }`}>
              {active.group === "social" ? "Socialt fundament" : "Økologisk loft"}
            </span>
            <h3 className="font-black text-base md:text-lg text-gray-800 mt-2 leading-tight">
              {active.label}
            </h3>
            <div className="mt-2">
              {active.hasData && active.score !== null ? (
                <p className="text-2xl md:text-3xl font-black text-gray-900 tracking-tighter">
                  {active.score.toFixed(1)}%
                </p>
              ) : (
                <p className="text-sm font-medium text-gray-400">Ingen data endnu</p>
              )}
              <p className={`text-xs font-bold uppercase tracking-widest mt-1 ${getStatusColor(active)}`}>
                {getStatusText(active)}
              </p>
            </div>
            {active.hasData && active.score !== null && (
              <div className="mt-3 h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
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
            <p className="text-[9px] text-gray-300 mt-3">Tryk på segment for at fastholde</p>
          </div>
        )}
      </div>

      <div className="flex flex-wrap justify-center gap-4 md:gap-6 mt-3 text-xs text-gray-500">
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
