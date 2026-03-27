import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Om platformen — Doughnut Economics Danmark",
  description: "Metodik, datakilder og begrænsninger for Doughnut Economics-platformen for danske kommuner.",
};

export default function OmPage() {
  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Om platformen</h2>
        <p className="text-gray-500 text-sm">
          En åben platform der kortlægger doughnut economics-status for alle 98 danske kommuner.
        </p>
      </div>

      <div className="space-y-8">

        {/* Hvad er doughnut economics */}
        <section>
          <h3 className="text-base font-semibold text-gray-900 mb-3 pb-2 border-b border-gray-200">
            Hvad er Doughnut Economics?
          </h3>
          <p className="text-sm text-gray-700 leading-relaxed">
            Doughnut Economics er en ramme udviklet af økonom Kate Raworth. Idéen er enkel: et godt samfund
            befinder sig i "doughnut-zonen" — over et socialt fundament (som sikrer, at alle borgeres basisbehov
            er dækket) og under et økologisk loft (som respekterer planetens grænser).
          </p>
          <p className="text-sm text-gray-700 leading-relaxed mt-2">
            For mange er det sociale fundament og det økologiske loft i konflikt. Formålet med doughnut-
            tænkning er at finde veje til at løfte det sociale uden at overskride det økologiske.
          </p>
        </section>

        {/* Hvad betyder scoren */}
        <section>
          <h3 className="text-base font-semibold text-gray-900 mb-3 pb-2 border-b border-gray-200">
            Hvad betyder scoren?
          </h3>
          <p className="text-sm text-gray-700 leading-relaxed">
            Alle scores er <strong>relative til landsgennemsnittet</strong>, sat til 100. En score på 100 betyder
            at kommunen er på niveau med resten af Danmark — ikke at den er i doughnut-zonen absolut set.
          </p>
          <div className="mt-3 grid grid-cols-3 gap-3">
            <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 text-center">
              <div className="text-emerald-700 font-bold text-lg">≥ 100</div>
              <div className="text-xs text-emerald-700 mt-1">Over landsgennemsnit</div>
            </div>
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-center">
              <div className="text-amber-700 font-bold text-lg">85–99</div>
              <div className="text-xs text-amber-700 mt-1">Under, men tæt på</div>
            </div>
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-center">
              <div className="text-red-700 font-bold text-lg">&lt; 85</div>
              <div className="text-xs text-red-700 mt-1">Markant under gennemsnit</div>
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-3">
            Bemærk: For indikatorer hvor lavere er bedre (f.eks. Gini-koefficient og børnefattigdom) er
            scores inverteret, så høj score fortsat betyder bedre end gennemsnit.
          </p>
          <p className="text-xs text-gray-400 mt-2">
            For det økologiske loft gælder: en score under 100 er positiv (under grænsen), over 100 er
            negativ (overshoot).
          </p>
        </section>

        {/* Metode-link */}
        <section>
          <h3 className="text-base font-semibold text-gray-900 mb-3 pb-2 border-b border-gray-200">
            Metode, datakilder og begrænsninger
          </h3>
          <p className="text-sm text-gray-700 leading-relaxed">
            For en detaljeret gennemgang af beregningsmetoder, grænseværdier, datakilder og begrænsninger
            for hver enkelt dimension, se{" "}
            <a href="/metode" className="text-blue-600 hover:underline font-medium">
              Metode & data-siden
            </a>.
          </p>
          <p className="text-sm text-gray-700 leading-relaxed mt-2">
            Kort fortalt: sociale dimensioner scores relativt til landsgennemsnittet (100 = gennemsnit),
            mens økologiske dimensioner scores mod absolutte planetære grænser (over 100 = overshoot).
            Platformen er under aktiv udvikling - flere dimensioner mangler stadig data.
          </p>
        </section>

        {/* Kontakt / kildekode */}
        <section>
          <h3 className="text-base font-semibold text-gray-900 mb-3 pb-2 border-b border-gray-200">
            Baggrund
          </h3>
          <p className="text-sm text-gray-700 leading-relaxed">
            Platformen er udviklet som et åbent redskab til at understøtte grøn omstilling i danske kommuner.
            Inspireret af{" "}
            <a
              href="https://doughnuteconomics.org/tools-and-stories/11"
              target="_blank"
              rel="noopener"
              className="text-blue-600 hover:underline"
            >
              DEAL's Community Action Tool
            </a>{" "}
            og{" "}
            <a
              href="https://www.kateraworth.com/doughnut/"
              target="_blank"
              rel="noopener"
              className="text-blue-600 hover:underline"
            >
              Kate Raworths doughnut-ramme
            </a>.
          </p>
        </section>

      </div>
    </div>
  );
}
