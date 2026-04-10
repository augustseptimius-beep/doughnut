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

        {/* Hvordan læses tallene */}
        <section>
          <h3 className="text-base font-semibold text-gray-900 mb-3 pb-2 border-b border-gray-200">
            Hvordan læses tallene?
          </h3>
          <p className="text-sm text-gray-700 leading-relaxed">
            Hver indikator får en talværdi baseret på hvor kommunen ligger i forhold til landsgennemsnittet (sociale indikatorer) eller planetens grænser (økologiske indikatorer).
          </p>
          <p className="text-sm text-gray-700 leading-relaxed mt-3">
            <strong>Sociale dimensioner:</strong> Tallet er relativt til landsgennemsnittet, sat til 100. En værdi på 100 betyder at kommunen er på niveau med resten af Danmark. Under 100 betyder underskud, over 100 betyder bedre end gennemsnit.
          </p>
          <p className="text-sm text-gray-700 leading-relaxed mt-2">
            <strong>Økologiske dimensioner:</strong> Tallet viser hvor tæt kommunen er på planetens grænser. En værdi under 100 er godt (under grænsen), over 100 betyder overshoot (over grænsen).
          </p>
          <p className="text-xs text-gray-400 mt-3">
            Bemærk: For indikatorer hvor lavere er bedre (f.eks. Gini-koefficient og børnefattigdom) er værdierne inverteret, så høj værdi fortsat betyder bedre end gennemsnit.
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

        {/* Baggrund */}
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

        {/* Prototype og forbehold */}
        <section>
          <h3 className="text-base font-semibold text-gray-900 mb-3 pb-2 border-b border-gray-200">
            Prototype og forbehold
          </h3>
          <p className="text-sm text-gray-700 leading-relaxed">
            Denne platform er en prototype under aktiv udvikling. Data behandles delvist ved hjælp af kunstig intelligens, hvorfor der kan forekomme fejl eller uregelmæssigheder.
          </p>
          <p className="text-sm text-gray-700 leading-relaxed mt-2">
            Benyt platformen som inspirationskilde til dialog om grøn omstilling i din kommune - ikke som eneste grundlag for strategiske beslutninger. Der mangler stadig data for flere indikatorer.
          </p>
        </section>

      </div>
    </div>
  );
}
