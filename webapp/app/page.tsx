import { getAllKommuner, computeCategoryScores, computeOverallFromCategories } from "@/lib/data";
import { ECOLOGICAL_DIMENSIONS } from "@/lib/shared";
import KommuneTable from "@/components/KommuneTable";

export default function Home() {
  const kommuner = getAllKommuner();

  const data = kommuner.map((k) => {
    // Avg-baseline kategorier
    const cats = computeCategoryScores(k.ratios);
    const overall = computeOverallFromCategories(cats);

    // Top 10%-baseline kategorier
    const top10Cats = computeCategoryScores(k.top10_ratios);
    const top10Overall = computeOverallFromCategories(top10Cats);

    const categoryMap: Record<string, number | null> = {};
    for (const cat of cats) {
      categoryMap[cat.categoryId] = cat.hasData ? cat.score : null;
    }

    const top10CategoryMap: Record<string, number | null> = {};
    for (const cat of top10Cats) {
      top10CategoryMap[cat.categoryId] = cat.hasData ? cat.score : null;
    }

    const ecoMap: Record<string, number | null> = {};
    for (const dim of ECOLOGICAL_DIMENSIONS) {
      ecoMap[dim.id] = k.eco_ratios[dim.id] ?? null;
    }

    return {
      kode: k.kommune_kode,
      navn: k.kommune_navn,
      overall,
      top10_overall: top10Overall,
      categories: categoryMap,
      top10_categories: top10CategoryMap,
      eco_categories: ecoMap,
    };
  });

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-900">Alle kommuner</h2>
        <p className="text-sm text-gray-500 mt-1">
          Doughnut Economics-score for alle 98 danske kommuner. Klik på en kommune for at se detaljer.
        </p>
      </div>
      <KommuneTable data={data} />
    </div>
  );
}
