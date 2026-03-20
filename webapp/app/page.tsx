import { getAllKommuner } from "@/lib/data";
import KommuneTable from "@/components/KommuneTable";

export default function Home() {
  const kommuner = getAllKommuner();

  // Serialize for client component
  const data = kommuner.map((k) => ({
    kode: k.kommune_kode,
    navn: k.kommune_navn,
    overall: k.overall_avg,
    social: k.social_avg,
  }));

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-900">
          Alle kommuner
        </h2>
        <p className="text-sm text-gray-500 mt-1">
          Doughnut Economics-score for alle 98 danske kommuner.
          Klik på en kommune for at se detaljer.
        </p>
      </div>
      <KommuneTable data={data} />
    </div>
  );
}
