"use client";

import DoughnutRing from "@/components/DoughnutRing";
import {
  type KommuneData,
  ECOLOGICAL_DIMENSIONS,
  SOCIAL_CATEGORIES,
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

// Badge med farve og tekst - inline styles til sikker print-rendering
function VurderingBadge({ score }: { score: NonNullable<VurderingScore> }) {
  const config: Record<NonNullable<VurderingScore>, { label: string; color: string; bg: string; border: string }> = {
    roed:  { label: "Negativ påvirkning",       color: "#991b1b", bg: "#fee2e2", border: "#fca5a5" },
    gul:   { label: "Ukendt / ingen påvirkning", color: "#92400e", bg: "#fef3c7", border: "#fcd34d" },
    groen: { label: "Positiv påvirkning",        color: "#065f46", bg: "#d1fae5", border: "#6ee7b7" },
  };
  const c = config[score];
  return (
    <span
      style={{
        display: "inline-block",
        color: c.color,
        backgroundColor: c.bg,
        border: `1px solid ${c.border}`,
        padding: "4px 14px",
        borderRadius: "9999px",
        fontSize: "13px",
        fontWeight: 700,
        letterSpacing: "0.01em",
      }}
    >
      {c.label}
    </span>
  );
}

export default function VurderingPrintView({
  projektnavn,
  beskrivelse,
  kommune,
  ratios,
  vurderinger,
}: Props) {
  const dato = new Date().toLocaleDateString("da-DK", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  // Byg lister over vurderede og ikke-vurderede dimensioner
  const categoryScores = computeCategoryScores(ratios);

  // Alle dimensioner i rækkefølge: sociale kategorier + okologiske dimensioner
  const alleDimensioner: Array<{
    id: string;
    navn: string;
    gruppe: "SOCIALT" | "ØKOLOGISK";
  }> = [
    ...SOCIAL_CATEGORIES.map((cat) => ({
      id: cat.id,
      navn: categoryScores.find((c) => c.categoryId === cat.id)?.categoryName ?? cat.name,
      gruppe: "SOCIALT" as const,
    })),
    ...ECOLOGICAL_DIMENSIONS.map((dim) => ({
      id: dim.id,
      navn: dim.name,
      gruppe: "ØKOLOGISK" as const,
    })),
  ];

  const vurderede = alleDimensioner.filter(
    (d) => vurderinger[d.id]?.score != null
  );
  const ikkeVurderede = alleDimensioner.filter(
    (d) => !vurderinger[d.id]?.score
  );

  return (
    <div
      style={{
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        color: "#111827",
        maxWidth: "800px",
        margin: "0 auto",
      }}
    >
      {/* ── SIDE 1: Header + Doughnut ── */}
      <div style={{ padding: "24px 24px 0 24px", pageBreakAfter: "always", breakAfter: "page" }}>
        {/* Projektheader */}
        <div
          style={{
            marginBottom: "24px",
            paddingBottom: "16px",
            borderBottom: "3px solid #16a34a",
          }}
        >
          <h1
            style={{
              fontSize: "26px",
              fontWeight: 900,
              margin: "0 0 6px 0",
              color: "#111827",
              lineHeight: 1.2,
            }}
          >
            {projektnavn || "Unavngivet projekt"}
          </h1>
          {beskrivelse && (
            <p style={{ fontSize: "14px", color: "#4b5563", margin: "0 0 10px 0", lineHeight: 1.5 }}>
              {beskrivelse}
            </p>
          )}
          <div style={{ display: "flex", gap: "28px", fontSize: "13px", color: "#6b7280" }}>
            <span>
              <strong style={{ color: "#374151" }}>Kommune:</strong>{" "}
              {kommune.kommune_navn}
            </span>
            <span>
              <strong style={{ color: "#374151" }}>Dato:</strong> {dato}
            </span>
            <span>
              <strong style={{ color: "#374151" }}>Vurderede dimensioner:</strong>{" "}
              {vurderede.length} af {alleDimensioner.length}
            </span>
          </div>
        </div>

        {/* Doughnut - stor, centreret, med vurderingsfarver */}
        <div style={{ maxWidth: "560px", margin: "0 auto" }}>
          <DoughnutRing
            kommune={kommune}
            ratios={ratios}
            vurderingsMode={true}
            vurderinger={vurderinger}
          />
        </div>
      </div>

      {/* ── SIDE 2+: Vurderingskort ── */}
      <div style={{ padding: "24px" }}>
        {vurderede.length === 0 ? (
          <p style={{ color: "#9ca3af", fontStyle: "italic", fontSize: "14px" }}>
            Ingen dimensioner er vurderet endnu.
          </p>
        ) : (
          <>
            <h2
              style={{
                fontSize: "12px",
                fontWeight: 700,
                color: "#6b7280",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                margin: "0 0 16px 0",
              }}
            >
              Vurderinger
            </h2>

            {/* Et kort per vurderet dimension */}
            {vurderede.map((dim) => {
              const v = vurderinger[dim.id];
              return (
                <div
                  key={dim.id}
                  style={{
                    marginBottom: "16px",
                    padding: "16px 20px",
                    border: "1px solid #e5e7eb",
                    borderRadius: "10px",
                    pageBreakInside: "avoid",
                    breakInside: "avoid",
                  }}
                >
                  {/* Gruppe-label */}
                  <p
                    style={{
                      fontSize: "10px",
                      fontWeight: 700,
                      color: "#9ca3af",
                      textTransform: "uppercase",
                      letterSpacing: "0.1em",
                      margin: "0 0 4px 0",
                    }}
                  >
                    {dim.gruppe}
                  </p>

                  {/* Dimensionsnavn + badge på samme linje */}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "16px",
                      marginBottom: v.argumentation ? "12px" : "0",
                      flexWrap: "wrap",
                    }}
                  >
                    <h3
                      style={{
                        fontSize: "17px",
                        fontWeight: 800,
                        color: "#111827",
                        margin: 0,
                        lineHeight: 1.3,
                      }}
                    >
                      {dim.navn}
                    </h3>
                    <VurderingBadge score={v.score!} />
                  </div>

                  {/* Argumentation */}
                  {v.argumentation && (
                    <p
                      style={{
                        fontSize: "14px",
                        color: "#374151",
                        lineHeight: 1.6,
                        margin: 0,
                        paddingTop: "8px",
                        borderTop: "1px solid #f3f4f6",
                      }}
                    >
                      {v.argumentation}
                    </p>
                  )}
                </div>
              );
            })}
          </>
        )}

        {/* Ikke-vurderede dimensioner - kompakt liste */}
        {ikkeVurderede.length > 0 && (
          <div
            style={{
              marginTop: "24px",
              paddingTop: "16px",
              borderTop: "1px solid #e5e7eb",
            }}
          >
            <p
              style={{
                fontSize: "11px",
                color: "#9ca3af",
                margin: "0 0 4px 0",
                fontWeight: 600,
                textTransform: "uppercase",
                letterSpacing: "0.06em",
              }}
            >
              Ikke vurderet
            </p>
            <p style={{ fontSize: "12px", color: "#6b7280", margin: 0, lineHeight: 1.6 }}>
              {ikkeVurderede.map((d) => d.navn).join(" · ")}
            </p>
          </div>
        )}

        {/* Metodenote */}
        <div
          style={{
            marginTop: "24px",
            padding: "12px 16px",
            backgroundColor: "#f9fafb",
            borderRadius: "8px",
            fontSize: "10px",
            color: "#6b7280",
            lineHeight: 1.7,
            pageBreakInside: "avoid",
            breakInside: "avoid",
          }}
        >
          <strong style={{ color: "#374151" }}>Metodenote:</strong>{" "}
          Doughnut-ringen viser kommunens faktiske status: score 100 = landsgennemsnit (socialt) eller planetær grænse (økologisk).
          Segmentfarverne i vurderingsmode afspejler projektlederens vurdering af projektets påvirkning - ikke kommunens data.
          Vurderingen er ikke automatisk beregnet. Se det fulde metodegrundlag på{" "}
          <span style={{ color: "#2563eb" }}>/metode</span>.
        </div>
      </div>
    </div>
  );
}
