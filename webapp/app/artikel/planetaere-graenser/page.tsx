import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Planetære grænser og Danmark — Doughnut Economics Danmark",
  description:
    "En CONCITO-rapport omsætter de planetære grænser til danske tal. Her er hvad den viser, hvad platformen måler, og hvad der ikke kan måles på kommuneniveau.",
};

export default function PlanetaereGraenserPage() {
  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-8">
        <p className="text-xs font-semibold text-blue-600 uppercase tracking-wider mb-2">
          Baggrundsartikel
        </p>
        <h2 className="text-2xl font-bold text-gray-900 mb-3">
          Hvor langt er Danmark fra de planetære grænser?
        </h2>
        <p className="text-gray-600 text-base leading-relaxed">
          En rapport fra CONCITO (2025) omsætter de ni planetære grænser til danske tal. Her er hvad
          den viser, hvad vores platform allerede måler, og hvad der bevidst ikke kan måles på
          kommuneniveau.
        </p>
      </div>

      <div className="space-y-8">

        {/* 1. De planetære grænser */}
        <section>
          <h3 className="text-base font-semibold text-gray-900 mb-3 pb-2 border-b border-gray-200">
            De planetære grænser, kort fortalt
          </h3>
          <p className="text-sm text-gray-700 leading-relaxed">
            De planetære grænser er ni biofysiske tærskler for de systemer der holder Jorden stabil:
            klima, biodiversitet, arealsystemet, ferskvand, kvælstof og fosfor, havforsuring, ozonlaget,
            partikelforurening og nye kemiske stoffer. Rammen blev opdateret af Richardson m.fl. (2023).
            CONCITO-rapporten nedskalerer seks af dem til Danmark: klima, biodiversitet, arealsystem,
            ferskvand, næringsstoffer og luft.
          </p>
          <p className="text-sm text-gray-700 leading-relaxed mt-2">
            Hovedkonklusionen er ubehagelig men klar: Danmark overskrider de fleste af grænserne, og
            for flere af dem er vores andel af det globale budget reelt allerede brugt op, hvis man
            regner historisk ansvar med.
          </p>
        </section>

        {/* 2. Territorial vs forbrug */}
        <section>
          <h3 className="text-base font-semibold text-gray-900 mb-3 pb-2 border-b border-gray-200">
            Det vi udleder her - og det vi forbruger
          </h3>
          <p className="text-sm text-gray-700 leading-relaxed">
            En afgørende skelnen i rapporten er mellem det <strong>territoriale</strong> aftryk (det der
            sker inden for Danmarks grænser) og det <strong>forbrugsbaserede</strong> aftryk (inklusive
            alt det vi importerer). Det forbrugsbaserede aftryk er typisk to til fem gange højere.
          </p>
          <p className="text-sm text-gray-700 leading-relaxed mt-2">
            Et konkret eksempel: dansk import af soja lægger alene beslag på et areal svarende til
            cirka 18% af Danmarks samlede areal - ude i verden. Samlet optager dansk forbrug et areal
            på omkring 203% af landets eget. Vores platform måler mest territorialt, men har det
            forbrugsbaserede CO2-aftryk med som en selvstændig dimension.
          </p>
        </section>

        {/* 3. Biodiversitet og de 44% */}
        <section>
          <h3 className="text-base font-semibold text-gray-900 mb-3 pb-2 border-b border-gray-200">
            Biodiversitet: hvorfor de 44% ikke kan blive til kommunetal
          </h3>
          <p className="text-sm text-gray-700 leading-relaxed">
            Rapporten måler biodiversitet med Biodiversity Intactness Index (BII) - et estimat for hvor
            stor en andel af de oprindelige arter der er tilbage i et område. Danmark ligger på 44% mod
            en sikker planetær grænse på 90%. Det lyder som et præcist tal, men det er det ikke helt.
          </p>
          <p className="text-sm text-gray-700 leading-relaxed mt-2">
            De 44% er et globalt modelestimat fra Natural History Museum i London, beregnet i celler på
            0,25 grader - omkring 430 km² hver, altså større end mange danske kommuner. Det er en
            scenariefremskrivning, ikke en måling, og usikkerheden går fra 41% til 61%. Derfor kan
            tallet ikke meningsfuldt regnes ned på den enkelte kommune.
          </p>
          <p className="text-sm text-gray-700 leading-relaxed mt-2">
            I stedet bruger vi DCE&apos;s danske biodiversitetskort (bioscore), der vurderer hvor
            værdifuldt hvert areal er som levested for truede arter - i 10 meters opløsning. Det er
            lokalt forankret og bygget på rigtige danske artsdata. Men vi måler det mod EU&apos;s
            politiske mål (30% værdifuld natur, 10% strengt beskyttet), ikke mod den planetære grænse.
            En kommune kan altså nå målet og lyse grønt uden at være inden for den biofysiske grænse.
            De to ting skal ikke forveksles.
          </p>
        </section>

        {/* 4. Areal */}
        <section>
          <h3 className="text-base font-semibold text-gray-900 mb-3 pb-2 border-b border-gray-200">
            Arealet: en femdobbelt overskridelse
          </h3>
          <p className="text-sm text-gray-700 leading-relaxed">
            For arealsystemet sætter rapporten grænsen ved 15% antropiseret areal - altså areal
            mennesket har lagt beslag på til byer, veje og landbrug. Danmark ligger på 73-75%. Det er
            en femdobbelt overskridelse og en af de mest markante i hele rapporten.
          </p>
          <p className="text-sm text-gray-700 leading-relaxed mt-2">
            Vores arealdimension viser fordelingen mellem intensivt landbrug og bebygget areal for hver
            kommune. Vi måler den i dag mod landsgennemsnittet, så man kan se forskel på kommunerne -
            men 15%-grænsen er den biofysiske virkelighed bag tallene.
          </p>
        </section>

        {/* 5. Det vi ikke kan måle */}
        <section>
          <h3 className="text-base font-semibold text-gray-900 mb-3 pb-2 border-b border-gray-200">
            Det vi ikke kan måle - og hvorfor vi siger det højt
          </h3>
          <p className="text-sm text-gray-700 leading-relaxed">
            Nogle af rapportens vigtigste pointer kan ikke gøres op per kommune med de data der findes.
            Det forbrugsbaserede aftryk for areal, biodiversitet og næringsstoffer kræver globale
            input-output-modeller på nationalt niveau. Jordsundhed, drænede arealer og presset på
            kystnaturen mangler enten kommunedata helt eller findes kun som nationale estimater.
          </p>
          <p className="text-sm text-gray-700 leading-relaxed mt-2">
            Vi nævner dem alligevel her, så de ikke bliver glemt. En platform der kun viser det målbare,
            risikerer at give indtryk af at det målbare er det hele. Det er det ikke.
          </p>
        </section>

        {/* 6. Hvad du kan bruge platformen til */}
        <section>
          <h3 className="text-base font-semibold text-gray-900 mb-3 pb-2 border-b border-gray-200">
            Hvad du kan bruge platformen til
          </h3>
          <p className="text-sm text-gray-700 leading-relaxed">
            Platformen viser hver kommunes relative position: hvordan den ligger i forhold til de andre
            danske kommuner og i forhold til de grænser vi kan operationalisere. En grøn score betyder
            &quot;bedre end de fleste danske kommuner&quot; - ikke nødvendigvis &quot;inden for planetens
            grænser&quot;. De to ting er ikke det samme, og CONCITO-rapporten er en god påmindelse om at
            Danmark som helhed har lang vej igen.
          </p>
          <p className="text-sm text-gray-700 leading-relaxed mt-2">
            Brug den som udgangspunkt for dialog om grøn omstilling i din kommune - se også{" "}
            <a href="/metode" className="text-blue-600 hover:underline font-medium">
              Metode &amp; data
            </a>{" "}
            for hvordan hver enkelt dimension er beregnet.
          </p>
        </section>

        {/* Kilder */}
        <section className="pt-2">
          <h3 className="text-base font-semibold text-gray-900 mb-3 pb-2 border-b border-gray-200">
            Kilder
          </h3>
          <ul className="text-sm text-gray-600 leading-relaxed space-y-1.5 list-disc pl-5">
            <li>
              CONCITO (2025): Downscaling planetary boundaries to national level - the case of Denmark.
            </li>
            <li>
              Richardson m.fl. (2023): Earth beyond six of nine planetary boundaries. Science Advances.
            </li>
            <li>
              <a
                href="https://dce.au.dk/udgivelser/vr/nr-101-150/abstracts/nr-112-biodiversitetskort-for-danmark"
                target="_blank"
                rel="noopener"
                className="text-blue-600 hover:underline"
              >
                DCE / Aarhus Universitet: Biodiversitetskort for Danmark (bioscore)
              </a>
            </li>
            <li>
              Phillips m.fl. (2021): The Biodiversity Intactness Index, Natural History Museum (DOI
              10.5519/HE1EQMG1).
            </li>
          </ul>
        </section>

        <p className="text-xs text-gray-400 leading-relaxed pt-2">
          Denne artikel er en formidling af platformens egen analyse af CONCITO-rapporten. Den er
          udarbejdet med hjælp fra kunstig intelligens og skal læses som baggrund og inspiration, ikke
          som autoritativ videnskabelig kilde.
        </p>

      </div>
    </div>
  );
}
