"use client";

import { useState } from "react";
import { INDICATORS, type KommuneData } from "@/lib/shared";

interface DoughnutRingProps {
  kommune: KommuneData;
  size?: number;
}

function arcColor(score: number | null): string {
  if (score === null) return "#d1d5db";
  if (score >= 100) return "#059669";
  if (score >= 85) return "#d97706";
  return "#dc2626";
}

function arcBg(score: number | null): string {
  if (score === null) return "#f3f4f6";
  if (score >= 100) return "#d1fae5";
  if (score >= 85) return "#fef3c7";
  return "#fee2e2";
}

interface ArcPath {
  id: string;
  name: string;
  score: number | null;
  safeD: string;
  barD: string;
  boundaryD: string;
  labelX: number;
  labelY: number;
  labelAngle: number;
}

function buildArcs(
  indicators: typeof INDICATORS,
  kommune: KommuneData,
  cx: number,
  cy: number,
  innerR: number,
  outerR: number
): ArcPath[] {
  const n = indicators.length;
  if (n === 0) return [];

  const gap = 0.03;
  const segAngle = (2 * Math.PI - n * gap) / n;
  const arcs: ArcPath[] = [];

  indicators.forEach((ind, i) => {
    const score = kommune.ratios[ind.id];
    const startAngle = i * (segAngle + gap) - Math.PI / 2;
    const endAngle = startAngle + segAngle;
    const midAngle = (startAngle + endAngle) / 2;

    // Safe space boundary at 100 mark
    const safeR = innerR + ((outerR - innerR) * 100) / 150;

    // Bar height scaled by score (clamped 0-150)
    const clampedScore = Math.min(Math.max(score || 0, 0), 150);
    const barR = innerR + ((outerR - innerR) * clampedScore) / 150;

    const largeArc = segAngle > Math.PI ? 1 : 0;

    // Safe space fill (always shown, light green background up to 100-mark)
    const safeD = arcPathD(cx, cy, innerR, safeR, startAngle, endAngle, largeArc);

    // Bar fill (actual score)
    const barD = arcPathD(cx, cy, innerR, barR, startAngle, endAngle, largeArc);

    // Outer boundary
    const boundaryD = arcPathD(cx, cy, innerR, outerR, startAngle, endAngle, largeArc);

    // Label position
    const labelR = outerR + 14;
    const labelX = cx + labelR * Math.cos(midAngle);
    const labelY = cy + labelR * Math.sin(midAngle);
    let labelAngle = (midAngle * 180) / Math.PI;
    if (labelAngle > 90 && labelAngle < 270) labelAngle += 180;
    if (labelAngle < -90 && labelAngle > -270) labelAngle += 180;

    arcs.push({
      id: ind.id,
      name: ind.name,
      score,
      safeD,
      barD,
      boundaryD,
      labelX,
      labelY,
      labelAngle,
    });
  });

  return arcs;
}

function arcPathD(
  cx: number,
  cy: number,
  innerR: number,
  outerR: number,
  startAngle: number,
  endAngle: number,
  largeArc: number
): string {
  const x1o = cx + outerR * Math.cos(startAngle);
  const y1o = cy + outerR * Math.sin(startAngle);
  const x2o = cx + outerR * Math.cos(endAngle);
  const y2o = cy + outerR * Math.sin(endAngle);
  const x1i = cx + innerR * Math.cos(endAngle);
  const y1i = cy + innerR * Math.sin(endAngle);
  const x2i = cx + innerR * Math.cos(startAngle);
  const y2i = cy + innerR * Math.sin(startAngle);

  return [
    `M ${x2i} ${y2i}`,
    `A ${innerR} ${innerR} 0 ${largeArc} 1 ${x1i} ${y1i}`,
    `L ${x2o} ${y2o}`,
    `A ${outerR} ${outerR} 0 ${largeArc} 0 ${x1o} ${y1o}`,
    `Z`,
  ].join(" ");
}

export default function DoughnutRing({ kommune, size = 340 }: DoughnutRingProps) {
  const [hovered, setHovered] = useState<string | null>(null);

  const indicators = INDICATORS.filter(
    (ind) => kommune.ratios[ind.id] !== null
  );
  const n = indicators.length;
  if (n === 0) return null;

  const cx = size / 2;
  const cy = size / 2;
  const outerR = size / 2 - 30;
  const innerR = outerR * 0.5;
  const safeMarkR = innerR + ((outerR - innerR) * 100) / 150;

  const arcs = buildArcs(indicators, kommune, cx, cy, innerR, outerR);

  const hoveredArc = arcs.find((a) => a.id === hovered);

  return (
    <div className="relative">
      <svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${size} ${size}`}
        className="max-w-[340px] mx-auto"
      >
        {/* Inner circle fill */}
        <circle cx={cx} cy={cy} r={innerR} fill="white" stroke="#e5e7eb" strokeWidth="1" />

        {/* Safe space mark (dashed circle at 100) */}
        <circle
          cx={cx}
          cy={cy}
          r={safeMarkR}
          fill="none"
          stroke="#9ca3af"
          strokeWidth="0.5"
          strokeDasharray="3 3"
        />

        {/* Outer boundary */}
        <circle cx={cx} cy={cy} r={outerR} fill="none" stroke="#e5e7eb" strokeWidth="0.5" />

        {/* Arc segments */}
        {arcs.map((arc) => (
          <g
            key={arc.id}
            onMouseEnter={() => setHovered(arc.id)}
            onMouseLeave={() => setHovered(null)}
            className="cursor-pointer"
          >
            {/* Boundary outline */}
            <path d={arc.boundaryD} fill="none" stroke="#e5e7eb" strokeWidth="0.5" />

            {/* Safe space background (light) */}
            <path d={arc.safeD} fill={arcBg(arc.score)} opacity="0.4" />

            {/* Actual score bar */}
            <path
              d={arc.barD}
              fill={arcColor(arc.score)}
              opacity={hovered === arc.id ? 0.95 : 0.75}
              className="transition-opacity duration-150"
            />

            {/* Hover hit area (invisible) */}
            <path d={arc.boundaryD} fill="transparent" />
          </g>
        ))}

        {/* Labels around the ring */}
        {arcs.map((arc) => (
          <text
            key={`label-${arc.id}`}
            x={arc.labelX}
            y={arc.labelY}
            textAnchor="middle"
            dominantBaseline="middle"
            transform={`rotate(${arc.labelAngle}, ${arc.labelX}, ${arc.labelY})`}
            className="fill-gray-500 pointer-events-none"
            style={{ fontSize: "6.5px" }}
          >
            {arc.name.length > 18 ? arc.name.substring(0, 16) + "…" : arc.name}
          </text>
        ))}

        {/* Center text */}
        <text
          x={cx}
          y={cy - 10}
          textAnchor="middle"
          className="fill-gray-900 font-bold"
          style={{ fontSize: "28px" }}
        >
          {kommune.overall_avg !== null ? Math.round(kommune.overall_avg) : "–"}
        </text>
        <text
          x={cx}
          y={cy + 10}
          textAnchor="middle"
          className="fill-gray-500"
          style={{ fontSize: "10px" }}
        >
          samlet score
        </text>
      </svg>

      {/* Hover tooltip */}
      {hoveredArc && (
        <div className="absolute top-2 left-1/2 -translate-x-1/2 bg-white border border-gray-200 rounded-lg shadow-lg px-3 py-2 text-sm z-10 whitespace-nowrap">
          <div className="font-medium text-gray-900">{hoveredArc.name}</div>
          <div className="flex items-center gap-2 mt-1">
            <div
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: arcColor(hoveredArc.score) }}
            />
            <span className="text-gray-700">
              {hoveredArc.score !== null ? `${hoveredArc.score.toFixed(1)}%` : "Ingen data"}
            </span>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="flex justify-center gap-4 mt-2 text-xs text-gray-500">
        <div className="flex items-center gap-1">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-600" />
          <span>≥ 100 (Safe)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2.5 h-2.5 rounded-full bg-amber-500" />
          <span>85–99</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
          <span>&lt; 85</span>
        </div>
      </div>
    </div>
  );
}
