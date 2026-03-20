import { getAllKommuner, computeCategoryScores, computeOverallFromCategories } from "@/lib/data";
import KommuneTable from "@/components/KommuneTable";

export default function Home() {
  const kommuner = getAllKommuner();

  const data = kommuner.map((k) => {
    const cats = computeCategoryScores(k.ratios);
    const overall = computeOverallFromCategories(cats);

    const categoryMap: Record<string, number | null> = {};
    for (const cat of cats) {
      categoryMap[cat.categoryId] = cat.hasData ? cat.score : null;
    }

    return {
      kode: k.kommune_kode,
      navn: k.kommune_navn,
      overall: overall,
      categories: categoryMap,
    };
  });

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-900">Alle kommuner</h2>
        <p className="text-sm text-gray-500 mt-1">
          Doughnut Economics-score for alle 98 danske kommuner. Klik på en
          kommune for at se detaljer.
        </p>
      </div>
      <KommuneTable data={data} />
    </div>
  );
}
