"use client";

import DoughnutRing from "@/components/DoughnutRing";
import {
  type KommuneData,
  ECOLOGICAL_DIMENSIONS,
  computeCategoryScores,
} from "@/lib/shared";
import type { VurderingScore, VurderingEntry } from "@/lib/vurdering";

interface Props {
  projektnavn: string;
  beskrivelse: string;
  kommune: KommuneData;
  ratios: Record<string, number | null>;
  vurderinger: Record<string, VurderingEntry>;
}

// Inline badge til print - undgaar Tailwind-klasser der maaskje er purged
function VurderingBadge({ score }: { score: VurderingScore }) {
  if (!score) {
    return (
      <span style={{ color: "#9ca3af", fontSize: "11px" }}>Ikke vurderet</span>
    );
  }
  const config: Record<
    NonNullable<VurderingScore>,
    { label: string; color: string; bg: string }
  > = {
    roed: { label: "Negativ", color: "#dc2626", bg: "#fee2e2" },
    gul: { label: "Ukendt / ingen", color: "#d97706", bg: "#fef3c7" },
    groen: { label: "Positiv", color: "#059669", bg: "#d1fae5" },
  };
  const c = config[score];
  return (
    <span
      style={{
        color: c.color,
        backgroundColor: c.bg,
        padding: "2px 8px",
        borderRadius: "9999px",
        fontSize: "11px",
        fontWeight: 700,
        whiteSpace: "nowrap",
      }}
    >
      {c.label}
    </span>
  );
}

function socialScoreColor(score: number | null): string {
  if (score === null) return "#9ca3af";
  if (score >= 100) return "#059669";
  if (score >= 85) return "#d97706";
  return "#dc2626";
}

function ecoScoreColor(score: number | null): string {
  if (score === null) return "#9ca3af";
  if (score <= 85) return "#059669";
  if (score <= 100) return "#d97706";
  return "#dc2626";
}

export default function VurderingPrintView({
  projektnavn,
  beskrivelse,
  kommune,
  ratios,
  vurderinger,
}: Props) {
  const categoryScores = computeCategoryScores(ratios);
  const dato = new Date().toLocaleDateString("da-DK", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div
      style={{
        fontFamily:
          "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        padding: "24px",
        maxWidth: "800px",
        color: "#111827",
      }}
    >
      {/* --- Projektheader --- */}
      <div
        style={{
          marginBottom: "20px",
          paddingBottom: "16px",
          borderBottom: "3px solid #16a34a",
        }}
      >
        <h1
          style={{
            fontSize: "22px",
            fontWeight: 900,
            margin: "0 0 4px 0",
            color: "#111827",
          }}
        >
          {projektnavn || "Unavngivet projekt"}
        </h1>
        {beskrivelse && (
          <p style={{ fontSize: "13px", color: "#6b7280", margin: "0 0 8px 0" }}>
            {beskrivelse}
          </p>
        )}
        <div
          style={{
            display: "flex",
            gap: "24px",
            fontSize: "12px",
            color: "#6b7280",
          }}
        >
          <span>
            <strong style={{ color: "#374151" }}>Kommune:</strong>{" "}
            {kommune.kommune_navn}
          </span>
          <span>
            <strong style={{ color: "#374151" }}>Dato:</strong> {dato}
          </span>
        </div>
      </div>

      {/* --- Doughnut --- */}
      <div style={{ maxWidth: "280px", margin: "0 auto 24px" }}>
        <DoughnutRing kommune={kommune} ratios={ratios} />
      </div>

      {/* --- Vurderingstabel --- */}
      <h2
        style={{
          fontSize: "14px",
          fontWeight: 700,
          color: "#111827",
          margin: "0 0 8px 0",
          textTransform: "uppercase",
          letterSpacing: "0.05em",
        }}
      >
        Vurderinger per dimension
      </h2>

      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          fontSize: "12px",
        }}
      >
        <thead>
          <tr style={{ backgroundColor: "#f3f4f6" }}>
            <th
              style={{
                textAlign: "left",
                padding: "8px 10px",
                fontWeight: 700,
                color: "#374151",
                borderBottom: "2px solid #e5e7eb",
              }}
            >
              Dimension
            </th>
            <th
              style={{
                textAlign: "left",
                padding: "8px 10px",
                fontWeight: 700,
                color: "#374151",
                borderBottom: "2px solid #e5e7eb",
                whiteSpace: "nowrap",
              }}
            >
              Vurdering
            </th>
            <th
              style={{
                textAlign: "left",
                padding: "8px 10px",
                fontWeight: 700,
                color: "#374151",
                borderBottom: "2px solid #e5e7eb",
              }}
            >
              Argumentation
            </th>
            <th
              style={{
                textAlign: "right",
                padding: "8px 10px",
                fontWeight: 700,
                color: "#374151",
                borderBottom: "2px solid #e5e7eb",
                whiteSpace: "nowrap",
              }}
            >
              Nuv. score
            </th>
          </tr>
        </thead>
        <tbody>
          {/* Sociale kategorier */}
          {categoryScores.map((cat) => {
            const v = vurderinger[cat.categoryId];
            return (
              <tr
                key={cat.categoryId}
                style={{ borderBottom: "1px solid #e5e7eb" }}
              >
                <td style={{ padding: "8px 10px", verticalAlign: "top" }}>
                  <div
                    style={{
                      fontSize: "10px",
                      color: "#9ca3af",
                      marginBottom: "2px",
                      textTransform: "uppercase",
                      letterSpacing: "0.04em",
                    }}
                  >
                    Socialt
                  </div>
                  <span style={{ fontWeight: 600, color: "#111827" }}>
                    {cat.categoryName}
                  </span>
                </td>
                <td style={{ padding: "8px 10px", verticalAlign: "top" }}>
                  <VurderingBadge score={v?.score ?? null} />
                </td>
                <td
                  style={{
                    padding: "8px 10px",
                    color: "#6b7280",
                    verticalAlign: "top",
                    fontStyle: v?.argumentation ? "normal" : "italic",
                  }}
                >
                  {v?.argumentation || ""}
                </td>
                <td
                  style={{
                    padding: "8px 10px",
                    textAlign: "right",
                    fontWeight: 700,
                    color: socialScoreColor(cat.score),
                    verticalAlign: "top",
                  }}
                >
                  {cat.hasData && cat.score !== null
                    ? cat.score.toFixed(1)
                    : "–"}
                </td>
              </tr>
            );
          })}

          {/* Okologiske dimensioner */}
          {ECOLOGICAL_DIMENSIONS.map((dim) => {
            const score = kommune.eco_ratios[dim.id] ?? null;
            const v = vurderinger[dim.id];
            return (
              <tr key={dim.id} style={{ borderBottom: "1px solid #e5e7eb" }}>
                <td style={{ padding: "8px 10px", verticalAlign: "top" }}>
                  <div
                    style={{
                      fontSize: "10px",
                      color: "#9ca3af",
                      marginBottom: "2px",
                      textTransform: "uppercase",
                      letterSpacing: "0.04em",
                    }}
                  >
                    Okologisk
                  </div>
                  <span style={{ fontWeight: 600, color: "#111827" }}>
                    {dim.name}
                  </span>
                </td>
                <td style={{ padding: "8px 10px", verticalAlign: "top" }}>
                  <VurderingBadge score={v?.score ?? null} />
                </td>
                <td
                  style={{
                    padding: "8px 10px",
                    color: "#6b7280",
                    verticalAlign: "top",
                    fontStyle: v?.argumentation ? "normal" : "italic",
                  }}
                >
                  {v?.argumentation || ""}
                </td>
                <td
                  style={{
                    padding: "8px 10px",
                    textAlign: "right",
                    fontWeight: 700,
                    color: ecoScoreColor(score),
                    verticalAlign: "top",
                  }}
                >
                  {score !== null ? score.toFixed(1) : "–"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {/* --- Metodenote --- */}
      <div
        style={{
          marginTop: "20px",
          padding: "12px 16px",
          backgroundColor: "#f9fafb",
          borderRadius: "8px",
          fontSize: "10px",
          color: "#6b7280",
          lineHeight: "1.6",
        }}
      >
        <strong style={{ color: "#374151" }}>Metodenote:</strong> Score 100 =
        landsgennemsnit for sociale indikatorer. Score 100 = planetaer graense
        for okologiske indikatorer (lavere er bedre). Vurderingen af projektets
        pavirkning er foretaget af projektlederen og er ikke automatisk
        beregnet. Se fuldt metodegrundlag pa{" "}
        <span style={{ color: "#2563eb" }}>/metode</span>.
      </div>
    </div>
  );
}
