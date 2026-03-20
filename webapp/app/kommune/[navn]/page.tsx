import { notFound } from "next/navigation";
import { getKommune, getAllKommuner, scoreColor } from "@/lib/data";
import KommuneClient from "./client";

interface Props {
  params: Promise<{ navn: string }>;
}

export async function generateStaticParams() {
  const kommuner = getAllKommuner();
  return kommuner.map((k) => ({ navn: encodeURIComponent(k.kommune_navn) }));
}

export default async function KommunePage({ params }: Props) {
  const { navn } = await params;
  const kommune = getKommune(navn);
  if (!kommune) return notFound();

  const allKommuner = getAllKommuner();

  // Rank
  const sorted = [...allKommuner]
    .filter((k) => k.overall_avg !== null)
    .sort((a, b) => (b.overall_avg || 0) - (a.overall_avg || 0));
  const rank = sorted.findIndex(
    (k) => k.kommune_kode === kommune.kommune_kode
  ) + 1;

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <a href="/" className="text-sm text-blue-600 hover:underline">
          ← Alle kommuner
        </a>
        <div className="mt-2 flex items-baseline gap-3">
          <h2 className="text-2xl font-bold text-gray-900">
            {kommune.kommune_navn}
          </h2>
          <span className="text-sm text-gray-500">
            ({kommune.kommune_kode})
          </span>
        </div>
        <div className="mt-1 flex items-center gap-4 text-sm">
          <span className={`font-semibold ${scoreColor(kommune.overall_avg)}`}>
            Samlet: {kommune.overall_avg !== null ? kommune.overall_avg.toFixed(1) : "–"}
          </span>
          <span className="text-gray-500">
            Rang: {rank} af {sorted.length}
          </span>
          {kommune.social_avg !== null && (
            <span className={`${scoreColor(kommune.social_avg)}`}>
              Social: {kommune.social_avg.toFixed(1)}
            </span>
          )}
        </div>
      </div>

      <KommuneClient kommune={kommune} allKommuner={allKommuner} />
    </div>
  );
}
