import { getAllKommuner } from "@/lib/data";
import KommuneSearch from "@/components/KommuneSearch";

export default function Home() {
  const kommuner = getAllKommuner();

  // Get first 6 municipalities alphabetically for the example grid
  const exampleKommuner = [...kommuner]
    .sort((a, b) => a.kommune_navn.localeCompare(b.kommune_navn))
    .slice(0, 6);

  return (
    <div className="max-w-6xl mx-auto">
      {/* Hero Section */}
      <div className="mb-12 text-center">
        <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
          Danmarks 98 Doughnuts
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Doughnut Economics er en ramme der måler, om et samfund sikrer alle borgernes basisbehov uden at overskride planetens grænser. Dette værktøj visualiserer, hvordan danske kommuner performer på tværs af sociale og økologiske dimensioner.
        </p>
      </div>

      {/* Search Section */}
      <div className="mb-12">
        <KommuneSearch kommuner={kommuner} exampleKommuner={exampleKommuner} />
      </div>

      {/* Footer info */}
      <div className="mt-16 pt-8 border-t border-gray-200 text-center text-sm text-gray-500">
        <p>
          Udforsk sociale og økologiske dimensioner på tværs af alle danske kommuner
        </p>
      </div>
    </div>
  );
}
