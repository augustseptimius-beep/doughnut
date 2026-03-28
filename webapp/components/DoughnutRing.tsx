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
const innerLimit = 80; // shortfall teeth stop here
const socialBase = 195;
const commonBoundary = 290;
const ecoCeiling = 385;
const outerMaxLimit = 620;

/* ── Colors ── */
const GREEN_SOCIAL = "#4ade80";
const GREEN_SOCIAL_HOVER = "#22c55e";
const GREEN_ECO = "#22c55e";
const GREEN_ECO_HOVER = "#16a34a";
const GREEN_DARK_BAND = "#15803d";
const RED = "#dc2626";
const GRAY_NO_DATA = "#cbd5e1";
const GRAY_NO_DATA_STROKE = "#94a3b8";

/**
 * Log-scale overshoot radius.
 * 100% = no overshoot, 200% = moderate, 367% = significant, 5000% = extreme
 */
function overshootRadius(score: number): number {
  if (score <= 100) return 0;
  const logVal = Math.log(score / 100);
  const logMax = Math.log(50); // cap at 5000%
  const normalized = Math.min(logVal / logMax, 1);
  const visual = Math.sqrt(normalized);
  return ecoCeiling + (outerMaxLimit - ecoCeiling) * visual;
}

/**
 * Correct text rotation so labels on ring segments are never upside down.
 * Returns rotation in degrees.
 */
function readableRadialRotation(midAngleRad: number): number {
  const deg = (midAngleRad * 180) / Math.PI;
  const norm = ((deg % 360) + 360) % 360;
  // Right half of circle: text reads center→outside
  // Left half of circle: flip 180° so text reads outside→center (still right-side-up)
  return norm > 90 && norm < 270 ? deg + 180 : deg;
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

  /* ── Split label into lines ── */
  const splitLabel = (name: string, maxChars: number): string[] => {
    if (name.length <= maxChars) return [name];
    const words = name.split(/[\s-]+/);
    const lines: string[] = [];
    let current = "";
    for (const word of words) {
      if (current && (current + " " + word).length > maxChars) {
        lines.push(current);
        current = word;
      } else {
        current = current ? current + " " + word : word;
      }
    }
    if (current) lines.push(current);
    return lines;
  };

  /* ── SOCIAL RING (green segments) ── */
  const renderSocialRing = () => {
    const angleStep = (2 * Math.PI) / socialCount;
    return categoryScores.map((cat, i) => {
      const startAngle = i * angleStep - Math.PI / 2;
      const endAngle = (i + 1) * angleStep - Math.PI / 2;
      const midAngle = (startAngle + endAngle) / 2;

      const safePath = describeArc(center, center, commonBoundary, socialBase, startAngle, endAngle);

      const isNoData = !cat.hasData;
      const isActive = active?.id === cat.categoryId && active?.group === "social";
      const safeColor = isNoData ? GRAY_NO_DATA : isActive ? GREEN_SOCIAL_HOVER : GREEN_SOCIAL;
      const safeStroke = isNoData ? GRAY_NO_DATA_STROKE : GREEN_DARK_BAND;

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

      // Label on the segment
      const labelR = (socialBase + commonBoundary) / 2;
      const lx = center + labelR * Math.cos(midAngle);
      const ly = center + labelR * Math.sin(midAngle);
      const textRotation = readableRadialRotation(midAngle);
      const lines = splitLabel(cat.categoryName, 10);

      return (
        <g
          key={cat.categoryId}
          className="cursor-pointer"
          onClick={() => handleClick(info)}
          onMouseEnter={() => handleHover(info)}
          onMouseLeave={handleLeave}
        >
          <path d={safePath} fill={safeColor} stroke={safeStroke} strokeWidth="0.5" className="transition-colors duration-200" />
          {/* Label on segment */}
          <text
            x={lx} y={ly}
            textAnchor="middle"
            dominantBaseline="middle"
            transform={`rotate(${textRotation}, ${lx}, ${ly})`}
            className="pointer-events-none select-none"
            style={{
              fontSize: "16px",
              fontWeight: 800,
              fill: isNoData ? "#64748b" : "white",
              textShadow: isNoData ? "none" : "0 1px 3px rgba(0,0,0,0.3)",
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

  /* ── SOCIAL SHORTFALL TEETH (red wedges pointing inward) ── */
  const renderSocialShortfall = () => {
    const angleStep = (2 * Math.PI) / socialCount;
    return categoryScores.map((cat, i) => {
      if (!cat.hasData || cat.score === null || cat.score >= 100) return null;
      const startAngle = i * angleStep - Math.PI / 2;
      const endAngle = (i + 1) * angleStep - Math.PI / 2;

      // Shortfall fraction determines how far inward the red tooth extends
      const fraction = Math.min((100 - cat.score) / 100, 1);
      const rIn = socialBase - (socialBase - innerLimit) * Math.sqrt(fraction);
      const toothPath = describeArc(center, center, socialBase, rIn, startAngle, endAngle);

      return (
        <path key={`sf-${cat.categoryId}`} d={toothPath} fill={RED} opacity="0.9" />
      );
    });
  };

  /* ── ECOLOGICAL RING (green segments + overshoot) ── */
  const renderEcoRing = () => {
    const angleStep = (2 * Math.PI) / ecoCount;
    return ECOLOGICAL_DIMENSIONS.map((dim, i) => {
      const startAngle = i * angleStep - Math.PI / 2;
      const endAngle = (i + 1) * angleStep - Math.PI / 2;
      const midAngle = (startAngle + endAngle) / 2;

      const ecoScore = kommune.eco_ratios[dim.id] ?? null;
      const hasEcoData = ecoScore !== null;

      const safePath = describeArc(center, center, ecoCeiling, commonBoundary, startAngle, endAngle);

      let overshootPath = "";
      if (hasEcoData && ecoScore > 100) {
        const rOut = overshootRadius(ecoScore);
        overshootPath = describeArc(center, center, rOut, ecoCeiling, startAngle, endAngle);
      }

      const isActive = active?.id === dim.id && active?.group === "ecological";
      const safeColor = hasEcoData ? (isActive ? GREEN_ECO_HOVER : GREEN_ECO) : GRAY_NO_DATA;
      const safeStroke = hasEcoData ? GREEN_DARK_BAND : GRAY_NO_DATA_STROKE;

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

      // Label on the eco segment
      const labelR = (commonBoundary + ecoCeiling) / 2;
      const lx = center + labelR * Math.cos(midAngle);
      const ly = center + labelR * Math.sin(midAngle);
      const textRotation = readableRadialRotation(midAngle);
      const lines = splitLabel(dim.name, 12);

      return (
        <g
          key={dim.id}
          className="cursor-pointer"
          onClick={() => handleClick(info)}
          onMouseEnter={() => handleHover(info)}
          onMouseLeave={handleLeave}
        >
          <path d={safePath} fill={safeColor} stroke={safeStroke} strokeWidth="0.5" className="transition-colors duration-200" />
          {overshootPath && (
            <path d={overshootPath} fill={RED} opacity="0.9" className="transition-all duration-300" />
          )}
          {/* Label on segment */}
          <text
            x={lx} y={ly}
            textAnchor="middle"
            dominantBaseline="middle"
            transform={`rotate(${textRotation}, ${lx}, ${ly})`}
            className="pointer-events-none select-none"
            style={{
              fontSize: "14px",
              fontWeight: 800,
              fill: hasEcoData ? "white" : "#64748b",
              textShadow: hasEcoData ? "0 1px 3px rgba(0,0,0,0.3)" : "none",
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

  /* ── Eco labels OUTSIDE the ring ── */
  const renderOuterEcoLabels = () => {
    const angleStep = (2 * Math.PI) / ecoCount;
    const labelR = outerMaxLimit + 30;
    return ECOLOGICAL_DIMENSIONS.map((dim, i) => {
      const startAngle = i * angleStep - Math.PI / 2;
      const endAngle = (i + 1) * angleStep - Math.PI / 2;
      const midAngle = (startAngle + endAngle) / 2;

      const lx = center + labelR * Math.cos(midAngle);
      const ly = center + labelR * Math.sin(midAngle);

      const ecoScore = kommune.eco_ratios[dim.id] ?? null;
      const hasData = ecoScore !== null;
      const isActive = active?.id === dim.id && active?.group === "ecological";

      const textRotation = readableRadialRotation(midAngle);
      const lines = splitLabel(dim.name, 14);

      return (
        <text
          key={`olabel-${dim.id}`}
          x={lx} y={ly}
          textAnchor="middle"
          dominantBaseline="middle"
          transform={`rotate(${textRotation}, ${lx}, ${ly})`}
          className="pointer-events-none select-none"
          style={{
            fontSize: "18px",
            fontWeight: isActive ? 900 : 800,
            fill: hasData ? (isActive ? "#166534" : "#1e293b") : "#94a3b8",
            transition: "fill 0.2s",
          }}
        >
          {lines.map((line, li) => (
            <tspan
              key={li}
              x={lx}
              dy={li === 0 ? `${-(lines.length - 1) * 0.5}em` : "1.15em"}
            >
              {line}
            </tspan>
          ))}
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

  /* ── Curved text path helper ── */
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

  const boundaryR = commonBoundary;
  const bandHalf = 14;

  return (
    <div className="relative w-full">
      <div className="relative w-full aspect-square flex items-center justify-center">
        <svg viewBox={`-200 -200 ${vbSize + 400} ${vbSize + 400}`} className="w-full h-full" preserveAspectRatio="xMidYMid meet">
          <defs>
            {curvedTextPath("ecoTitleArc", boundaryR + bandHalf + 4, -155, -25)}
            {curvedTextPath("socialTitleArc", boundaryR - bandHalf - 4, 205, 335)}
          </defs>

          {/* ── 1. Eco ring (segments + overshoot) ── */}
          {renderEcoRing()}

          {/* ── 2. Social ring (green segments) ── */}
          {renderSocialRing()}

          {/* ── 3. Dark green boundary band ── */}
          <circle cx={center} cy={center} r={boundaryR + bandHalf} fill="none" stroke={GREEN_DARK_BAND} strokeWidth="2" />
          <circle cx={center} cy={center} r={boundaryR - bandHalf} fill="none" stroke={GREEN_DARK_BAND} strokeWidth="2" />
          {/* Filled dark band */}
          <circle cx={center} cy={center} r={boundaryR} fill="none" stroke={GREEN_DARK_BAND} strokeWidth={bandHalf * 2} opacity="0.35" />

          {/* ── 4. Outer eco boundary ── */}
          <circle cx={center} cy={center} r={ecoCeiling} fill="none" stroke={GREEN_DARK_BAND} strokeWidth="3" opacity="0.6" />
          {/* ── 5. Inner social boundary ── */}
          <circle cx={center} cy={center} r={socialBase} fill="none" stroke={GREEN_DARK_BAND} strokeWidth="3" opacity="0.6" />

          {/* ── 6. White center ── */}
          <circle cx={center} cy={center} r={socialBase - 1} fill="white" />

          {/* ── 7. Shortfall teeth (rendered ON TOP of white center) ── */}
          {renderSocialShortfall()}

          {/* ── 8. Outer eco labels ── */}
          {renderOuterEcoLabels()}

          {/* ── 9. Curved ring titles on the boundary band ── */}
          <text
            className="pointer-events-none select-none"
            style={{ fontSize: "18px", fontWeight: 900, fill: GREEN_DARK_BAND, letterSpacing: "0.3em" }}
          >
            <textPath href="#ecoTitleArc" startOffset="50%" textAnchor="middle">
              ØKOLOGISK LOFT
            </textPath>
          </text>

          <text
            className="pointer-events-none select-none"
            style={{ fontSize: "16px", fontWeight: 900, fill: GREEN_DARK_BAND, letterSpacing: "0.25em" }}
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
          <div className="w-4 h-4 rounded" style={{ backgroundColor: GREEN_SOCIAL, border: `1px solid ${GREEN_DARK_BAND}` }} />
          <span className="font-medium">Sikkert rum</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: RED }} />
          <span className="font-medium">Underskud / Overskridelse</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: GRAY_NO_DATA, border: `1px solid ${GRAY_NO_DATA_STROKE}` }} />
          <span className="font-medium">Mangler data</span>
        </div>
      </div>
    </div>
  );
}
