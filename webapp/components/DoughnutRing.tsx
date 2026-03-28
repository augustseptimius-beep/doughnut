"use client";

import { useState } from "react";
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

/* ── Layout constants ── */
const vbSize = 1000;
const center = vbSize / 2;
const innerLimit = 55;
const socialBase = 195;
const commonBoundary = 290;
const ecoCeiling = 385;
const outerSoftLimit = 470;  // "normal" overshoot extends to here
const outerMaxLimit = 620;   // extreme overshoot can reach this far
const gap = 0.035;

/**
 * Maps an overshoot/shortfall score to a radius extension.
 * Uses log scale so 200% is visually different from 500% which is different from 5000%.
 * - score 100 = no overshoot (returns 0)
 * - score 200 = moderate overshoot
 * - score 367 = significant overshoot (forbrug_co2)
 * - score 5000 = extreme overshoot
 */
function overshootRadius(score: number, rBase: number, rSoft: number, rMax: number): number {
  if (score <= 100) return 0;
  // Log scale: log(1)=0, log(2)=0.69, log(3.67)=1.30, log(50)=3.91
  const overshootMultiple = score / 100; // e.g. 3.67 for 367%
  const logVal = Math.log(overshootMultiple); // 0 at 100%, grows unbounded
  const logMax = Math.log(50); // cap visual at 5000% (log(50)≈3.91)
  const normalized = Math.min(logVal / logMax, 1); // 0..1
  // Smooth curve: sqrt gives more visual range in the lower end
  const visual = Math.sqrt(normalized);
  return rBase + (rMax - rBase) * visual;
}

function shortfallRadius(score: number, rBase: number, rMin: number): number {
  if (score >= 100) return rBase;
  const shortfallPct = (100 - score) / 100; // 0..1 for 100..0%
  // sqrt for visual emphasis on moderate shortfalls
  const visual = Math.sqrt(Math.min(shortfallPct, 1));
  return rBase - (rBase - rMin) * visual;
}

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

  /* ── Helper: wrap text in arc for curved labels ── */
  const curvedTextPath = (id: string, r: number, startAngleDeg: number, endAngleDeg: number) => {
    const startRad = (startAngleDeg * Math.PI) / 180;
    const endRad = (endAngleDeg * Math.PI) / 180;
    const x1 = center + r * Math.cos(startRad);
    const y1 = center + r * Math.sin(startRad);
    const x2 = center + r * Math.cos(endRad);
    const y2 = center + r * Math.sin(endRad);
    const largeArc = endAngleDeg - startAngleDeg > 180 ? "1" : "0";
    return (
      <path
        id={id}
        d={`M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`}
        fill="none"
        stroke="none"
      />
    );
  };

  /* ── Helper: split label into lines that fit arc segment ── */
  const splitLabel = (name: string, maxCharsPerLine: number): string[] => {
    if (name.length <= maxCharsPerLine) return [name];
    const words = name.split(/[\s-]+/);
    const lines: string[] = [];
    let current = "";
    for (const word of words) {
      if (current && (current + " " + word).length > maxCharsPerLine) {
        lines.push(current);
        current = word;
      } else {
        current = current ? current + " " + word : word;
      }
    }
    if (current) lines.push(current);
    return lines;
  };

  /* ── SOCIAL RING ── */
  const renderSocialRing = () => {
    const angleStep = (2 * Math.PI) / socialCount;
    return categoryScores.map((cat, i) => {
      const startAngle = i * angleStep - Math.PI / 2 + gap / 2;
      const endAngle = (i + 1) * angleStep - Math.PI / 2 - gap / 2;
      const midAngle = (startAngle + endAngle) / 2;

      const safePath = describeArc(center, center, commonBoundary, socialBase, startAngle, endAngle);

      let shortfallPath = "";
      if (cat.hasData && cat.score !== null && cat.score < 100) {
        const rIn = shortfallRadius(cat.score, socialBase, innerLimit);
        shortfallPath = describeArc(center, center, socialBase, rIn, startAngle, endAngle);
      }

      // Label position - centered in the safe zone segment
      const labelRadius = (socialBase + commonBoundary) / 2;
      const lx = center + labelRadius * Math.cos(midAngle);
      const ly = center + labelRadius * Math.sin(midAngle);

      const isNoData = !cat.hasData;
      const isActive = active?.id === cat.categoryId && active?.group === "social";
      const safeColor = isNoData ? "#e5e7eb" : isActive ? "#6ee7b7" : "#86efac";
      const safeStroke = isNoData ? "#d1d5db" : "#16a34a";

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

      // Calculate rotation for text to follow the arc
      const midAngleDeg = (midAngle * 180) / Math.PI;
      const isBottom = midAngleDeg > 0 && midAngleDeg < 180;
      const textRotation = isBottom ? midAngleDeg + 90 : midAngleDeg - 90;

      const lines = splitLabel(cat.categoryName, 10);

      return (
        <g
          key={cat.categoryId}
          className="cursor-pointer"
          onClick={() => handleClick(info)}
          onMouseEnter={() => handleHover(info)}
          onMouseLeave={handleLeave}
        >
          <path d={safePath} fill={safeColor} stroke={safeStroke} strokeWidth="1" className="transition-colors duration-200" />
          {shortfallPath && (
            <path d={shortfallPath} fill="#dc2626" opacity="0.9" className="transition-all duration-300" />
          )}
          <line
            x1={center + innerLimit * Math.cos(startAngle - gap / 2)}
            y1={center + innerLimit * Math.sin(startAngle - gap / 2)}
            x2={center + commonBoundary * Math.cos(startAngle - gap / 2)}
            y2={center + commonBoundary * Math.sin(startAngle - gap / 2)}
            stroke="white" strokeWidth="2"
          />
          {/* Label directly on segment */}
          <text
            x={lx} y={ly}
            textAnchor="middle"
            dominantBaseline="middle"
            transform={`rotate(${textRotation}, ${lx}, ${ly})`}
            className="pointer-events-none select-none"
            style={{
              fontSize: "15px",
              fontWeight: 800,
              fill: isNoData ? "#9ca3af" : "#065f46",
              textShadow: "0 0 3px rgba(255,255,255,0.8)",
            }}
          >
            {lines.map((line, li) => (
              <tspan
                key={li}
                x={lx}
                dy={li === 0 ? `${-(lines.length - 1) * 0.5}em` : "1.1em"}
              >
                {line}
              </tspan>
            ))}
          </text>
        </g>
      );
    });
  };

  /* ── ECOLOGICAL RING ── */
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
        const rOut = overshootRadius(ecoScore, ecoCeiling, outerSoftLimit, outerMaxLimit);
        overshootPath = describeArc(center, center, rOut, ecoCeiling, startAngle, endAngle);
      }

      // Label position - centered in the eco segment
      const labelRadius = (commonBoundary + ecoCeiling) / 2;
      const lx = center + labelRadius * Math.cos(midAngle);
      const ly = center + labelRadius * Math.sin(midAngle);

      const isActive = active?.id === dim.id && active?.group === "ecological";
      const safeColor = hasEcoData ? (isActive ? "#6ee7b7" : "#86efac") : "#f3f4f6";
      const safeStroke = hasEcoData ? "#16a34a" : "#d1d5db";

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

      const midAngleDeg = (midAngle * 180) / Math.PI;
      const isBottom = midAngleDeg > 0 && midAngleDeg < 180;
      const textRotation = isBottom ? midAngleDeg + 90 : midAngleDeg - 90;

      const lines = splitLabel(dim.name, 12);

      return (
        <g
          key={dim.id}
          className="cursor-pointer"
          onClick={() => handleClick(info)}
          onMouseEnter={() => handleHover(info)}
          onMouseLeave={handleLeave}
        >
          <path d={safePath} fill={safeColor} stroke={safeStroke} strokeWidth="1" className="transition-colors duration-200" />
          {overshootPath && (
            <path d={overshootPath} fill="#dc2626" opacity="0.9" className="transition-all duration-300" />
          )}
          <line
            x1={center + commonBoundary * Math.cos(startAngle - gap / 2)}
            y1={center + commonBoundary * Math.sin(startAngle - gap / 2)}
            x2={center + outerMaxLimit * Math.cos(startAngle - gap / 2)}
            y2={center + outerMaxLimit * Math.sin(startAngle - gap / 2)}
            stroke="white" strokeWidth="2"
          />
          {/* Label directly on segment */}
          <text
            x={lx} y={ly}
            textAnchor="middle"
            dominantBaseline="middle"
            transform={`rotate(${textRotation}, ${lx}, ${ly})`}
            className="pointer-events-none select-none"
            style={{
              fontSize: "14px",
              fontWeight: 800,
              fill: hasEcoData ? "#065f46" : "#9ca3af",
              textShadow: "0 0 3px rgba(255,255,255,0.8)",
            }}
          >
            {lines.map((line, li) => (
              <tspan
                key={li}
                x={lx}
                dy={li === 0 ? `${-(lines.length - 1) * 0.5}em` : "1.1em"}
              >
                {line}
              </tspan>
            ))}
          </text>
        </g>
      );
    });
  };

  /* ── Eco labels OUTSIDE the ring (for overshoot readability) ── */
  const renderOuterEcoLabels = () => {
    const angleStep = (2 * Math.PI) / ecoCount;
    const labelR = outerMaxLimit + 25;
    return ECOLOGICAL_DIMENSIONS.map((dim, i) => {
      const startAngle = i * angleStep - Math.PI / 2 + gap / 2;
      const endAngle = (i + 1) * angleStep - Math.PI / 2 - gap / 2;
      const midAngle = (startAngle + endAngle) / 2;

      const lx = center + labelR * Math.cos(midAngle);
      const ly = center + labelR * Math.sin(midAngle);

      const ecoScore = kommune.eco_ratios[dim.id] ?? null;
      const hasData = ecoScore !== null;
      const isActive = active?.id === dim.id && active?.group === "ecological";

      const angleDeg = (midAngle * 180) / Math.PI;
      let anchor: "start" | "middle" | "end" = "middle";
      if (angleDeg > 20 && angleDeg < 160) anchor = "start";
      else if (angleDeg > 200 && angleDeg < 340) anchor = "end";

      return (
        <text
          key={`olabel-${dim.id}`}
          x={lx} y={ly}
          textAnchor={anchor}
          dominantBaseline="middle"
          className="pointer-events-none select-none"
          style={{
            fontSize: "14px",
            fontWeight: isActive ? 900 : 700,
            fill: hasData ? (isActive ? "#166534" : "#374151") : "#9ca3af",
            transition: "fill 0.2s",
          }}
        >
          {dim.name}
        </text>
      );
    });
  };

  const getStatusText = (info: ActiveInfo): string => {
    if (!info.hasData || info.score === null) return "Mangler data";
    if (info.group === "social") {
      return info.score >= 100 ? "Mål nået" : `Underskud ${(100 - info.score).toFixed(1)}%`;
    }
    return info.score <= 100 ? "Inden for grænsen" : `Overskridelse ${(info.score - 100).toFixed(1)}%`;
  };

  const getStatusColor = (info: ActiveInfo): string => {
    if (!info.hasData || info.score === null) return "text-gray-400";
    if (info.group === "social") return info.score >= 100 ? "text-emerald-600" : "text-red-500";
    return info.score <= 100 ? "text-emerald-600" : "text-red-500";
  };

  /* ── Curved ring title arc IDs ── */
  const ecoTitleArcR = ecoCeiling + 12;
  const socialTitleArcR = socialBase - 12;

  return (
    <div className="relative w-full">
      <div className="relative w-full aspect-square flex items-center justify-center">
        <svg viewBox={`-200 -200 ${vbSize + 400} ${vbSize + 400}`} className="w-full h-full" preserveAspectRatio="xMidYMid meet">
          {/* Defs for curved text paths */}
          <defs>
            {/* Eco title arc - top half, clockwise */}
            {curvedTextPath("ecoTitleArc", ecoTitleArcR, -160, -20)}
            {/* Social title arc - bottom half, clockwise */}
            {curvedTextPath("socialTitleArc", socialTitleArcR, 200, 340)}
          </defs>

          {/* Subtle background */}
          <circle cx={center} cy={center} r={outerSoftLimit + 10} fill="#fafafa" opacity="0.3" />

          {renderEcoRing()}
          {renderSocialRing()}

          {/* Boundary circles - the "safe and just space" borders */}
          <circle cx={center} cy={center} r={ecoCeiling} fill="none" stroke="#15803d" strokeWidth="3" opacity="0.7" />
          <circle cx={center} cy={center} r={socialBase} fill="none" stroke="#15803d" strokeWidth="3" opacity="0.7" />
          <circle cx={center} cy={center} r={commonBoundary} fill="none" stroke="#15803d" strokeWidth="1.5" opacity="0.3" />

          {/* Clean center */}
          <circle cx={center} cy={center} r={socialBase - 5} fill="white" opacity="0.92" />

          {/* Outer eco labels */}
          {renderOuterEcoLabels()}

          {/* ── Curved ring titles ── */}
          <text
            className="pointer-events-none select-none"
            style={{ fontSize: "16px", fontWeight: 900, fill: "#15803d", letterSpacing: "0.25em" }}
          >
            <textPath href="#ecoTitleArc" startOffset="50%" textAnchor="middle">
              ØKOLOGISK LOFT
            </textPath>
          </text>

          <text
            className="pointer-events-none select-none"
            style={{ fontSize: "14px", fontWeight: 900, fill: "#15803d", letterSpacing: "0.2em" }}
          >
            <textPath href="#socialTitleArc" startOffset="50%" textAnchor="middle">
              SOCIALT FUNDAMENT
            </textPath>
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
          <div className="w-4 h-4 rounded" style={{ backgroundColor: "#86efac", border: "1px solid #16a34a" }} />
          <span className="font-medium">Sikkert rum</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-red-600 opacity-90" />
          <span className="font-medium">Underskud / Overskridelse</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-gray-200 border border-gray-300" />
          <span className="font-medium">Mangler data</span>
        </div>
      </div>
    </div>
  );
}
