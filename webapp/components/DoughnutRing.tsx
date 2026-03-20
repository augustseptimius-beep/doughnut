"use client";

import { useState } from "react";
import {
  type KommuneData,
  type CategoryScore,
  ECOLOGICAL_DIMENSIONS,
  computeCategoryScores,
  computeOverallFromCategories,
} from "@/lib/shared";

interface DoughnutRingProps {
  kommune: KommuneData;
}

// --- SVG ARC HELPER ---
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

// --- GEOMETRY ---
const vbSize = 1000;
const center = vbSize / 2;

// Radii
const innerLimit = 60; // Center of social shortfall bars
const socialBase = 220; // Inner edge of safe space (social foundation line)
const commonBoundary = 310; // Dividing line between social & ecological
const ecoCeiling = 400; // Outer edge of safe space (ecological ceiling line)
const outerLimit = 480; // Max extent of ecological overshoot bars

const gap = 0.04; // Gap between segments in radians

interface HoverInfo {
  label: string;
  group: "social" | "ecological";
  score: number | null;
  hasData: boolean;
}

export default function DoughnutRing({ kommune }: DoughnutRingProps) {
  const [hovered, setHovered] = useState<HoverInfo | null>(null);

  const categoryScores = computeCategoryScores(kommune.ratios);
  const overallScore = computeOverallFromCategories(categoryScores);
  const categoriesWithData = categoryScores.filter((c) => c.hasData).length;

  const socialCount = categoryScores.length;
  const ecoCount = ECOLOGICAL_DIMENSIONS.length;

  // --- RENDER SOCIAL RING (inner) ---
  const renderSocialRing = () => {
    const angleStep = (2 * Math.PI) / socialCount;
    return categoryScores.map((cat, i) => {
      const startAngle = i * angleStep - Math.PI / 2 + gap / 2;
      const endAngle = (i + 1) * angleStep - Math.PI / 2 - gap / 2;
      const midAngle = (startAngle + endAngle) / 2;

      // Safe space segment
      const safePath = describeArc(
        center,
        center,
        commonBoundary,
        socialBase,
        startAngle,
        endAngle
      );

      // Shortfall bar (stretches INWARD from socialBase when score < 100)
      let shortfallPath = "";
      if (cat.hasData && cat.score !== null && cat.score < 100) {
        const shortfallFraction = (100 - cat.score) / 100; // 0 to 1
        const rIn =
          socialBase - (socialBase - innerLimit) * Math.min(shortfallFraction, 1);
        shortfallPath = describeArc(
          center,
          center,
          socialBase,
          rIn,
          startAngle,
          endAngle
        );
      }

      // Label
      const labelRadius = (socialBase + commonBoundary) / 2;
      const lx = center + labelRadius * Math.cos(midAngle);
      const ly = center + labelRadius * Math.sin(midAngle);
      const rotDeg = (midAngle * 180) / Math.PI;
      const shouldFlip = rotDeg > 0 && rotDeg < 180;
      const finalRot = shouldFlip ? rotDeg - 90 : rotDeg + 90;

      const isNoData = !cat.hasData;
      const safeColor = isNoData ? "#e5e7eb" : "#e8f0e8";
      const safeStroke = isNoData ? "#d1d5db" : "#8faa8f";

      return (
        <g
          key={cat.categoryId}
          className="cursor-pointer"
          onMouseEnter={() =>
            setHovered({
              label: cat.categoryName,
              group: "social",
              score: cat.score,
              hasData: cat.hasData,
            })
          }
          onMouseLeave={() => setHovered(null)}
        >
          {/* Safe space segment */}
          <path
            d={safePath}
            fill={safeColor}
            stroke={safeStroke}
            strokeWidth="0.5"
            className="transition-colors hover:brightness-95"
          />
          {/* Shortfall bar (red, inward) */}
          {shortfallPath && (
            <path
              d={shortfallPath}
              fill="#dc2626"
              opacity="0.7"
              className="transition-all duration-300"
            />
          )}
          {/* Radial separator */}
          <line
            x1={center + innerLimit * Math.cos(startAngle - gap / 2)}
            y1={center + innerLimit * Math.sin(startAngle - gap / 2)}
            x2={center + commonBoundary * Math.cos(startAngle - gap / 2)}
            y2={center + commonBoundary * Math.sin(startAngle - gap / 2)}
            stroke="#94a3b8"
            strokeWidth="0.5"
            strokeOpacity="0.15"
          />
          {/* Label */}
          <text
            x={lx}
            y={ly}
            textAnchor="middle"
            dominantBaseline="middle"
            transform={`rotate(${finalRot}, ${lx}, ${ly})`}
            className="pointer-events-none select-none"
            style={{
              fontSize: "13px",
              fontWeight: 800,
              fill: isNoData ? "#9ca3af" : "#2d4a2d",
              textTransform: "uppercase",
              letterSpacing: "0.02em",
            }}
          >
            {cat.categoryName}
          </text>
        </g>
      );
    });
  };

  // --- RENDER ECOLOGICAL RING (outer) ---
  const renderEcoRing = () => {
    const angleStep = (2 * Math.PI) / ecoCount;
    return ECOLOGICAL_DIMENSIONS.map((dim, i) => {
      const startAngle = i * angleStep - Math.PI / 2 + gap / 2;
      const endAngle = (i + 1) * angleStep - Math.PI / 2 - gap / 2;
      const midAngle = (startAngle + endAngle) / 2;

      // No data yet — grey placeholder
      const safePath = describeArc(
        center,
        center,
        ecoCeiling,
        commonBoundary,
        startAngle,
        endAngle
      );

      // Label
      const labelRadius = (commonBoundary + ecoCeiling) / 2;
      const lx = center + labelRadius * Math.cos(midAngle);
      const ly = center + labelRadius * Math.sin(midAngle);
      const rotDeg = (midAngle * 180) / Math.PI;
      const shouldFlip = rotDeg > 0 && rotDeg < 180;
      const finalRot = shouldFlip ? rotDeg - 90 : rotDeg + 90;

      return (
        <g
          key={dim.id}
          className="cursor-pointer"
          onMouseEnter={() =>
            setHovered({
              label: dim.name,
              group: "ecological",
              score: null,
              hasData: false,
            })
          }
          onMouseLeave={() => setHovered(null)}
        >
          <path
            d={safePath}
            fill="#f3f4f6"
            stroke="#d1d5db"
            strokeWidth="0.5"
            className="transition-colors hover:brightness-95"
          />
          {/* Radial separator */}
          <line
            x1={center + commonBoundary * Math.cos(startAngle - gap / 2)}
            y1={center + commonBoundary * Math.sin(startAngle - gap / 2)}
            x2={center + outerLimit * Math.cos(startAngle - gap / 2)}
            y2={center + outerLimit * Math.sin(startAngle - gap / 2)}
            stroke="#94a3b8"
            strokeWidth="0.5"
            strokeOpacity="0.15"
          />
          <text
            x={lx}
            y={ly}
            textAnchor="middle"
            dominantBaseline="middle"
            transform={`rotate(${finalRot}, ${lx}, ${ly})`}
            className="pointer-events-none select-none"
            style={{
              fontSize: "12px",
              fontWeight: 800,
              fill: "#9ca3af",
              textTransform: "uppercase",
              letterSpacing: "0.02em",
            }}
          >
            {dim.name}
          </text>
        </g>
      );
    });
  };

  // Hover card status text
  const getStatusText = (info: HoverInfo): string => {
    if (!info.hasData) return "Mangler data";
    if (info.score === null) return "Mangler data";
    if (info.score >= 100) return "Mål nået";
    if (info.group === "social") return `Shortfall ${(100 - info.score).toFixed(1)}%`;
    return `Overshoot ${(info.score - 100).toFixed(1)}%`;
  };

  const getStatusColor = (info: HoverInfo): string => {
    if (!info.hasData || info.score === null) return "text-gray-400";
    if (info.score >= 100) return "text-emerald-600";
    return "text-red-500";
  };

  return (
    <div className="relative w-full">
      <div className="relative w-full aspect-square flex items-center justify-center">
        <svg
          viewBox={`0 0 ${vbSize} ${vbSize}`}
          className="w-full h-full"
          preserveAspectRatio="xMidYMid meet"
        >
          {/* Soft background */}
          <circle
            cx={center}
            cy={center}
            r={outerLimit + 10}
            fill="#fafafa"
            opacity="0.5"
          />

          {/* Ecological ring (outer) */}
          {renderEcoRing()}

          {/* Social ring (inner) */}
          {renderSocialRing()}

          {/* Threshold lines */}
          <circle
            cx={center}
            cy={center}
            r={ecoCeiling}
            fill="none"
            stroke="#166534"
            strokeWidth="2.5"
            opacity="0.6"
          />
          <circle
            cx={center}
            cy={center}
            r={socialBase}
            fill="none"
            stroke="#166534"
            strokeWidth="2.5"
            opacity="0.6"
          />

          {/* Center content */}
          <circle
            cx={center}
            cy={center}
            r={socialBase - 5}
            fill="white"
            opacity="0.9"
          />
          <text
            x={center}
            y={center - 30}
            textAnchor="middle"
            style={{ fontSize: "64px", fontWeight: 900, fill: "#1f2937" }}
          >
            {overallScore !== null ? Math.round(overallScore) : "–"}
          </text>
          <text
            x={center}
            y={center + 10}
            textAnchor="middle"
            style={{
              fontSize: "14px",
              fontWeight: 700,
              fill: "#6b7280",
              textTransform: "uppercase",
              letterSpacing: "0.15em",
            }}
          >
            samlet score
          </text>

          {/* Ring labels */}
          <text
            x={center}
            y={center - ecoCeiling - 30}
            textAnchor="middle"
            style={{
              fontSize: "12px",
              fontWeight: 800,
              fill: "#9ca3af",
              textTransform: "uppercase",
              letterSpacing: "0.2em",
            }}
          >
            Økologisk loft
          </text>
          <text
            x={center}
            y={center + ecoCeiling + 45}
            textAnchor="middle"
            style={{
              fontSize: "12px",
              fontWeight: 800,
              fill: "#6b7280",
              textTransform: "uppercase",
              letterSpacing: "0.2em",
            }}
          >
            Socialt fundament
          </text>
        </svg>

        {/* Hover card */}
        {hovered && (
          <div className="absolute bottom-4 right-4 md:top-4 md:right-4 bg-white/95 backdrop-blur-md shadow-2xl p-4 md:p-5 rounded-2xl w-48 md:w-56 border border-gray-100 pointer-events-none z-10">
            <span
              className={`text-[9px] font-bold px-2 py-0.5 rounded-full uppercase ${
                hovered.group === "social"
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-gray-100 text-gray-500"
              }`}
            >
              {hovered.group === "social"
                ? "Socialt fundament"
                : "Økologisk loft"}
            </span>
            <h3 className="font-black text-base md:text-lg text-gray-800 mt-2 leading-tight">
              {hovered.label}
            </h3>
            <div className="mt-2">
              {hovered.hasData && hovered.score !== null ? (
                <p className="text-2xl md:text-3xl font-black text-gray-900 tracking-tighter">
                  {hovered.score.toFixed(1)}%
                </p>
              ) : (
                <p className="text-sm font-medium text-gray-400">
                  Ingen data endnu
                </p>
              )}
              <p
                className={`text-xs font-bold uppercase tracking-widest mt-1 ${getStatusColor(hovered)}`}
              >
                {getStatusText(hovered)}
              </p>
            </div>
            {hovered.hasData && hovered.score !== null && (
              <div className="mt-3 h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 rounded-full ${
                    hovered.score >= 100 ? "bg-emerald-500" : "bg-red-400"
                  }`}
                  style={{
                    width: `${Math.min(hovered.score, 120) / 1.2}%`,
                  }}
                />
              </div>
            )}
          </div>
        )}
      </div>

      {/* Legend */}
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
