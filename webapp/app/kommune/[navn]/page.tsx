import { notFound } from "next/navigation";
import {
  getKommune,
  getAllKommuner,
} from "@/lib/data";
import KommuneClient from "./client";

interface Props {
  params: Promise<{ navn: string }>;
}

export async function generateStaticParams() {
  const kommuner = getAllKommuner();
  return kommuner.map((k) => ({ navn: k.kommune_navn }));
}

export default async function KommunePage({ params }: Props) {
  const { navn } = await params;
  const kommune = getKommune(navn);
  if (!kommune) return notFound();

  const allKommuner = getAllKommuner();

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <a href="/" className="text-sm text-blue-600 hover:underline">
          &larr; Søg kommuner
        </a>
        <div className="mt-2 flex items-baseline gap-3">
          <h2 className="text-2xl font-bold text-gray-900">
            {kommune.kommune_navn}
          </h2>
          <span className="text-sm text-gray-500">
            ({kommune.kommune_kode})
          </span>
        </div>
      </div>

      <KommuneClient kommune={kommune} allKommuner={allKommuner} />
    </div>
  );
}
