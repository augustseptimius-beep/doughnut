"use client";

import React, { useState } from "react";
import {
  type KommuneData,
  ECOLOGICAL_DIMENSIONS,
  SOCIAL_CATEGORIES,
  INDICATORS,
  computeCategoryScores,
} from "@/lib/shared";

interface DoughnutRingProps {
  kommune: KommuneData;
  ratios?: Record<string, number | null>; // override kommune.ratios (bruges til baseline-skift)
}

function describeArc(
  cx: number, cy: number,
  rOuter: number, rInner: number,
  startAngle: number, endAngle: number
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

/**
 * Create an arc path string for textPath usage.
 * For the bottom half of the circle, we reverse direction (counter-clockwise)
 * so text doesn't render upside down.
 */
function labelArcPath(
  cx: number, cy: number, r: number,
  startAngle: number, endAngle: number
): string {
  const midAngle = (startAngle + endAngle) / 2;

  // In SVG, Y-axis points DOWN.
  // sin(midAngle) > 0 means the midpoint is in the lower half of the screen.
  // On a clockwise arc, lower-half text goes right-to-left → appears upside down.
  // Fix: reverse to counter-clockwise for lower half.
  const isBottom = Math.sin(midAngle) > 0;

  if (isBottom) {
    // Counter-clockwise: swap endpoints, sweep=0
    const x1 = cx + r * Math.cos(endAngle);
    const y1 = cy + r * Math.sin(endAngle);
    const x2 = cx + r * Math.cos(startAngle);
    const y2 = cy + r * Math.sin(startAngle);
    const span = endAngle - startAngle;
    const largeArc = span <= Math.PI ? "0" : "1";
    return `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 0 ${x2} ${y2}`;
  } else {
    // Clockwise: normal direction
    const x1 = cx + r * Math.cos(startAngle);
    const y1 = cy + r * Math.sin(startAngle);
    const x2 = cx + r * Math.cos(endAngle);
    const y2 = cy + r * Math.sin(endAngle);
    const span = endAngle - startAngle;
    const largeArc = span <= Math.PI ? "0" : "1";
    return `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`;
  }
}

/* ── Layout constants ── */
const vbSize = 1000;
const center = vbSize / 2;
const innerLimit = 80;
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
const GRAY_NO_DATA = "#cbd5e1";
const GRAY_NO_DATA_STROKE = "#94a3b8";

/* ── Severity levels ── */
type SeverityLevel = "safe" | "exceeded" | "high" | "extreme";

const SEVERITY_LABELS_ECO: Record<SeverityLevel, string> = {
  safe:     "Inden for grænsen",
  exceeded: "Overskredet",
  high:     "Meget overskredet",
  extreme:  "Ekstremt overskredet",
};

const SEVERITY_LABELS_SOCIAL: Record<SeverityLevel, string> = {
  safe:     "Intet underskud",
  exceeded: "Underskud",
  high:     "Stort underskud",
  extreme:  "Ekstremt underskud",
};

const SEVERITY_TEXT_COLORS: Record<SeverityLevel, string> = {
  safe:     "text-emerald-600",
  exceeded: "text-orange-500",
  high:     "text-red-500",
  extreme:  "text-red-700",
};

function getEcoSeverity(score: number | null): SeverityLevel {
  if (score === null) return "safe";
  if (score <= 100) return "safe";
  if (score <= 250) return "exceeded";
  if (score <= 500) return "high";
  return "extreme";
}

function getSocialSeverity(score: number | null): SeverityLevel {
  if (score === null) return "safe";
  if (score >= 100) return "safe";
  if (score >= 50) return "exceeded";
  if (score >= 25) return "high";
  return "extreme";
}

function overshootRadius(score: number): number {
  if (score <= 100) return 0;
  const logVal = Math.log(score / 100);
  const logMax = Math.log(50);
  const normalized = Math.min(logVal / logMax, 1);
  const visual = Math.sqrt(normalized);
  return ecoCeiling + (outerMaxLimit - ecoCeiling) * visual;
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

export default function DoughnutRing({ kommune, ratios }: DoughnutRingProps) {
  const [active, setActive] = useState<ActiveInfo | null>(null);
  const [pinned, setPinned] = useState(false);

  const activeRatios = ratios ?? kommune.ratios;
  const categoryScores = computeCategoryScores(activeRatios);
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

  /* ── SOCIAL RING ── */
  const renderSocialRing = () => {
    const angleStep = (2 * Math.PI) / socialCount;
    return categoryScores.map((cat, i) => {
      const startAngle = i * angleStep - Math.PI / 2;
      const endAngle = (i + 1) * angleStep - Math.PI / 2;

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

      return (
        <g
          key={cat.categoryId}
          className="cursor-pointer"
          onClick={() => handleClick(info)}
          onMouseEnter={() => handleHover(info)}
          onMouseLeave={handleLeave}
        >
          <path d={safePath} fill={safeColor} stroke={safeStroke} strokeWidth="0.5" className="transition-colors duration-200" />
        </g>
      );
    });
  };

  /* ── SOCIAL SHORTFALL TEETH ── */
  const renderSocialShortfall = () => {
    const angleStep = (2 * Math.PI) / socialCount;
    return categoryScores.map((cat, i) => {
      if (!cat.hasData || cat.score === null || cat.score >= 100) return null;
      const startAngle = i * angleStep - Math.PI / 2;
      const endAngle = (i + 1) * angleStep - Math.PI / 2;
      const fraction = Math.min((100 - cat.score) / 100, 1);
      const rIn = socialBase - (socialBase - innerLimit) * Math.sqrt(fraction);
      const toothPath = describeArc(center, center, socialBase, rIn, startAngle, endAngle);
      return <path key={`sf-${cat.categoryId}`} d={toothPath} fill="url(#socialShortfallGrad)" opacity="0.9" />;
    });
  };

  /* ── ECOLOGICAL RING ── */
  const renderEcoRing = () => {
    const angleStep = (2 * Math.PI) / ecoCount;
    return ECOLOGICAL_DIMENSIONS.map((dim, i) => {
      const startAngle = i * angleStep - Math.PI / 2;
      const endAngle = (i + 1) * angleStep - Math.PI / 2;

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
            <path d={overshootPath} fill="url(#ecoOvershootGrad)" opacity="0.9" className="transition-all duration-300" />
          )}
        </g>
      );
    });
  };

  // Labels that should split across two lines: { id: [line1, line2] }
  const SPLIT_LABELS: Record<string, [string, string]> = {
    "samskabelse": ["Samskabelse &", "demokrati"],
  };

  /* ── textPath label definitions (in <defs>) ── */
  const renderLabelDefs = () => {
    const socialStep = (2 * Math.PI) / socialCount;
    const ecoStep = (2 * Math.PI) / ecoCount;
    const socialLabelR = (socialBase + commonBoundary) / 2;
    const ecoLabelR = (commonBoundary + ecoCeiling) / 2;
    const lineOffset = 9; // px between two lines

    const paths: React.ReactElement[] = [];

    // Social: one path for single-line, two paths (±offset) for split labels
    categoryScores.forEach((cat, i) => {
      const startAngle = i * socialStep - Math.PI / 2;
      const endAngle = (i + 1) * socialStep - Math.PI / 2;
      const isSplit = cat.categoryId in SPLIT_LABELS;

      if (isSplit) {
        const d1 = labelArcPath(center, center, socialLabelR - lineOffset, startAngle, endAngle);
        const d2 = labelArcPath(center, center, socialLabelR + lineOffset, startAngle, endAngle);
        paths.push(<path key={`sp1-${cat.categoryId}`} id={`slabel1-${cat.categoryId}`} d={d1} fill="none" stroke="none" />);
        paths.push(<path key={`sp2-${cat.categoryId}`} id={`slabel2-${cat.categoryId}`} d={d2} fill="none" stroke="none" />);
      } else {
        const d = labelArcPath(center, center, socialLabelR, startAngle, endAngle);
        paths.push(<path key={`sp-${cat.categoryId}`} id={`slabel-${cat.categoryId}`} d={d} fill="none" stroke="none" />);
      }
    });

    // Eco label paths (single line)
    ECOLOGICAL_DIMENSIONS.forEach((dim, i) => {
      const startAngle = i * ecoStep - Math.PI / 2;
      const endAngle = (i + 1) * ecoStep - Math.PI / 2;
      const d = labelArcPath(center, center, ecoLabelR, startAngle, endAngle);
      paths.push(<path key={`ep-${dim.id}`} id={`elabel-${dim.id}`} d={d} fill="none" stroke="none" />);
    });

    return paths;
  };

  /* ── Render segment dividers (white radial lines) ── */
  const renderSegmentDividers = () => {
    const dividers: React.ReactElement[] = [];

    // Social dividers: from innerLimit to commonBoundary
    const socialAngleStep = (2 * Math.PI) / socialCount;
    for (let i = 0; i < socialCount; i++) {
      const angle = i * socialAngleStep - Math.PI / 2;
      const x1 = center + innerLimit * Math.cos(angle);
      const y1 = center + innerLimit * Math.sin(angle);
      const x2 = center + commonBoundary * Math.cos(angle);
      const y2 = center + commonBoundary * Math.sin(angle);
      dividers.push(
        <line
          key={`social-divider-${i}`}
          x1={x1} y1={y1} x2={x2} y2={y2}
          stroke="white" strokeWidth="1.5" opacity="0.5"
        />
      );
    }

    // Eco dividers: from commonBoundary to outerMaxLimit + 50
    const ecoAngleStep = (2 * Math.PI) / ecoCount;
    for (let i = 0; i < ecoCount; i++) {
      const angle = i * ecoAngleStep - Math.PI / 2;
      const x1 = center + commonBoundary * Math.cos(angle);
      const y1 = center + commonBoundary * Math.sin(angle);
      const x2 = center + (outerMaxLimit + 50) * Math.cos(angle);
      const y2 = center + (outerMaxLimit + 50) * Math.sin(angle);
      dividers.push(
        <line
          key={`eco-divider-${i}`}
          x1={x1} y1={y1} x2={x2} y2={y2}
          stroke="white" strokeWidth="1.5" opacity="0.5"
        />
      );
    }

    return dividers;
  };

  /* ── Render curved text labels ── */
  const renderCurvedLabels = () => {
    const labels: React.ReactElement[] = [];

    // Social labels
    categoryScores.forEach((cat) => {
      const isNoData = !cat.hasData;
      const isActive = active?.id === cat.categoryId && active?.group === "social";
      const fill = isNoData ? "#64748b" : "#fff";
      const shadow = isNoData ? "none" : "0 1px 2px rgba(0,0,0,0.4)";
      const split = SPLIT_LABELS[cat.categoryId];

      if (split) {
        // Two-line label
        labels.push(
          <text key={`st1-${cat.categoryId}`} className="pointer-events-none select-none"
            style={{ fontSize: "13px", fontWeight: 800, fill, textShadow: shadow }}>
            <textPath href={`#slabel1-${cat.categoryId}`} startOffset="50%" textAnchor="middle" dominantBaseline="central">
              {split[0]}
            </textPath>
          </text>
        );
        labels.push(
          <text key={`st2-${cat.categoryId}`} className="pointer-events-none select-none"
            style={{ fontSize: "13px", fontWeight: 800, fill, textShadow: shadow }}>
            <textPath href={`#slabel2-${cat.categoryId}`} startOffset="50%" textAnchor="middle" dominantBaseline="central">
              {split[1]}
            </textPath>
          </text>
        );
      } else {
        labels.push(
          <text key={`st-${cat.categoryId}`} className="pointer-events-none select-none"
            style={{ fontSize: "14px", fontWeight: 800, fill, textShadow: shadow }}>
            <textPath href={`#slabel-${cat.categoryId}`} startOffset="50%" textAnchor="middle" dominantBaseline="central">
              {cat.categoryName}
            </textPath>
          </text>
        );
      }
    });

    // Eco labels
    ECOLOGICAL_DIMENSIONS.forEach((dim) => {
      const hasData = kommune.eco_ratios[dim.id] != null;
      const isActive = active?.id === dim.id && active?.group === "ecological";
      labels.push(
        <text
          key={`et-${dim.id}`}
          className="pointer-events-none select-none"
          style={{
            fontSize: "13px",
            fontWeight: 800,
            fill: hasData ? (isActive ? "#fff" : "#fff") : "#64748b",
            textShadow: hasData ? "0 1px 2px rgba(0,0,0,0.4)" : "none",
          }}
        >
          <textPath
            href={`#elabel-${dim.id}`}
            startOffset="50%"
            textAnchor="middle"
            dominantBaseline="central"
          >
            {dim.name}
          </textPath>
        </text>
      );
    });

    return labels;
  };

  /* ── Curved title arc path helper ── */
  const titleArcPath = (id: string, r: number, startDeg: number, endDeg: number) => {
    const s = (startDeg * Math.PI) / 180;
    const e = (endDeg * Math.PI) / 180;
    const x1 = center + r * Math.cos(s);
    const y1 = center + r * Math.sin(s);
    const x2 = center + r * Math.cos(e);
    const y2 = center + r * Math.sin(e);
    const la = endDeg - startDeg > 180 ? "1" : "0";
    return <path id={id} d={`M ${x1} ${y1} A ${r} ${r} 0 ${la} 1 ${x2} ${y2}`} fill="none" stroke="none" />;
  };

  const getStatusText = (info: ActiveInfo): string => {
    if (!info.hasData || info.score === null) return "Mangler data";
    if (info.group === "social") {
      const severity = getSocialSeverity(info.score);
      return SEVERITY_LABELS_SOCIAL[severity];
    }
    const severity = getEcoSeverity(info.score);
    return SEVERITY_LABELS_ECO[severity];
  };

  const getStatusColor = (info: ActiveInfo): string => {
    if (!info.hasData || info.score === null) return "text-gray-400";
    const severity = info.group === "social"
      ? getSocialSeverity(info.score)
      : getEcoSeverity(info.score);
    return SEVERITY_TEXT_COLORS[severity];
  };

  return (
    <div className="relative w-full">
      <div className="relative w-full aspect-square flex items-center justify-center">
        <svg viewBox={`-140 -140 ${vbSize + 280} ${vbSize + 280}`} className="w-full h-full" preserveAspectRatio="xMidYMid meet">
          <defs>
            {renderLabelDefs()}
            {titleArcPath("ecoTitleArc", ecoCeiling + 10, -150, -30)}
            {titleArcPath("socialTitleArc", socialBase - 18, 200, 340)}
            {/* Eco overshoot: gradient outward from ecoCeiling (yellow) to outerMaxLimit (dark red) */}
            <radialGradient id="ecoOvershootGrad" gradientUnits="userSpaceOnUse"
              cx={center} cy={center} r={outerMaxLimit}>
              <stop offset={`${ecoCeiling / outerMaxLimit}`} stopColor="#eab308" />
              <stop offset={`${(ecoCeiling + (outerMaxLimit - ecoCeiling) * 0.4) / outerMaxLimit}`} stopColor="#f97316" />
              <stop offset={`${(ecoCeiling + (outerMaxLimit - ecoCeiling) * 0.7) / outerMaxLimit}`} stopColor="#dc2626" />
              <stop offset="1" stopColor="#991b1b" />
            </radialGradient>
            {/* Social shortfall: gradient inward from socialBase (yellow) to innerLimit (dark red) */}
            <radialGradient id="socialShortfallGrad" gradientUnits="userSpaceOnUse"
              cx={center} cy={center} r={socialBase}>
              <stop offset={`${innerLimit / socialBase}`} stopColor="#991b1b" />
              <stop offset={`${(innerLimit + (socialBase - innerLimit) * 0.3) / socialBase}`} stopColor="#dc2626" />
              <stop offset={`${(innerLimit + (socialBase - innerLimit) * 0.6) / socialBase}`} stopColor="#f97316" />
              <stop offset="1" stopColor="#eab308" />
            </radialGradient>
          </defs>

          {/* 1. Eco ring */}
          {renderEcoRing()}

          {/* 2. Social ring */}
          {renderSocialRing()}

          {/* 2.5. Segment dividers */}
          {renderSegmentDividers()}

          {/* 3. Boundary lines */}
          <circle cx={center} cy={center} r={ecoCeiling} fill="none" stroke={GREEN_DARK_BAND} strokeWidth="3" opacity="0.5" />
          <circle cx={center} cy={center} r={commonBoundary} fill="none" stroke={GREEN_DARK_BAND} strokeWidth="2" opacity="0.3" />
          <circle cx={center} cy={center} r={socialBase} fill="none" stroke={GREEN_DARK_BAND} strokeWidth="3" opacity="0.5" />

          {/* 4. White center */}
          <circle cx={center} cy={center} r={socialBase - 1} fill="white" />

          {/* 5. Shortfall teeth */}
          {renderSocialShortfall()}

          {/* 6. Curved dimension labels */}
          {renderCurvedLabels()}

          {/* 7. Ring titles */}
          <text className="pointer-events-none select-none"
            style={{ fontSize: "18px", fontWeight: 900, fill: GREEN_DARK_BAND, letterSpacing: "0.3em" }}>
            <textPath href="#ecoTitleArc" startOffset="50%" textAnchor="middle">
              ØKOLOGISK LOFT
            </textPath>
          </text>
          <text className="pointer-events-none select-none"
            style={{ fontSize: "16px", fontWeight: 900, fill: GREEN_DARK_BAND, letterSpacing: "0.25em" }}>
            <textPath href="#socialTitleArc" startOffset="50%" textAnchor="middle">
              SOCIALT FUNDAMENT
            </textPath>
          </text>
        </svg>

        {/* Info card */}
        {active && (
          <div className={`absolute top-2 right-2 bg-white/95 backdrop-blur-md shadow-2xl p-3 rounded-2xl w-52 md:w-56 border border-gray-100 z-10 ${pinned ? "" : "pointer-events-none"}`}>
            <div className="flex items-center justify-between mb-2">
              <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full uppercase ${
                active.group === "social" ? "bg-emerald-100 text-emerald-700" : "bg-gray-100 text-gray-500"
              }`}>
                {active.group === "social" ? "Socialt fundament" : "Økologisk loft"}
              </span>
              {pinned && (
                <button onClick={() => { setPinned(false); setActive(null); }}
                  className="text-gray-300 hover:text-gray-500 text-xs">✕</button>
              )}
            </div>
            <h3 className="font-black text-base text-gray-800 leading-tight">{active.label}</h3>
            {active.description && (
              <p className="text-[11px] text-gray-500 mt-1.5 leading-snug line-clamp-2">{active.description}</p>
            )}
            <div className="mt-1.5">
              {active.hasData && active.score !== null ? (
                <p className={`text-base font-black uppercase tracking-wide ${getStatusColor(active)}`}>
                  {getStatusText(active)}
                </p>
              ) : (
                <p className="text-sm font-medium text-gray-400">Ingen data endnu</p>
              )}
            </div>
            {active.indicators && active.indicators.length > 0 && (
              <div className="mt-1.5 pt-2 border-t border-gray-100">
                <p className="text-[9px] font-semibold text-gray-400 uppercase mb-1">Indikatorer</p>
                {active.indicators.slice(0, 4).map((name) => (
                  <p key={name} className="text-[11px] text-gray-600 leading-snug">· {name}</p>
                ))}
                {active.indicators.length > 4 && (
                  <p className="text-[11px] text-gray-500 leading-snug italic">+ {active.indicators.length - 4} flere</p>
                )}
              </div>
            )}
            {active.boundary && (
              <div className="mt-1.5 pt-2 border-t border-gray-100">
                <p className="text-[9px] font-semibold text-gray-400 uppercase mb-1">Grænseværdi</p>
                <p className="text-[11px] text-gray-600 leading-snug">{active.boundary}</p>
              </div>
            )}
            {active.unit && (
              <p className="text-[10px] text-gray-400 mt-1.5">Enhed: {active.unit}</p>
            )}
            {active.hasData && active.score !== null && (() => {
              const isBad = active.group === "social" ? active.score < 100 : active.score > 100;
              const barColor = isBad ? "#dc2626" : "#22c55e";
              return (
                <div className="mt-1.5 h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full transition-all duration-500 rounded-full"
                    style={{ width: `${Math.min(active.score, 200) / 2}%`, backgroundColor: barColor }} />
                </div>
              );
            })()}
            <div className="flex items-center justify-between mt-1.5">
              <a href={`/metode#${active.id}`} className="text-[10px] text-blue-600 hover:underline pointer-events-auto">
                Se metode →
              </a>
              {!pinned && <p className="text-[9px] text-gray-300">Klik for at fastholde</p>}
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
          <div className="w-12 h-4 rounded" style={{ background: "linear-gradient(to right, #eab308, #f97316, #dc2626, #991b1b)" }} />
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
