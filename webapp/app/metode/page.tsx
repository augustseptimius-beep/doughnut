import type { Metadata } from "next";
import { SOCIAL_CATEGORIES, INDICATORS, ECOLOGICAL_DIMENSIONS } from "@/lib/shared";

export const metadata: Metadata = {
  title: "Metode & datakilder — Doughnut Economics Danmark",
  description: "Detaljeret dokumentation af metodik, indikatorer, grænseværdier og datakilder for alle dimensioner.",
};

/* ─── Method metadata per dimension ─── */

interface MethodInfo {
  id: string;
  scoring: string;         // how the score/ratio is calculated
  boundary?: string;       // what the planetary boundary / social floor is
  dataYear?: string;
  limitations?: string;
  csvFile?: string;
}

const SOCIAL_METHODS: Record<string, MethodInfo> = {
  sundhed: {
    id: "sundhed",
    scoring: "Gennemsnit af to indikatorer: (1) Middellevetid (0-årige) sammenholdt med landsgennemsnittet. (2) Sygehusbenyttelse - andel af befolkningen med ophold på sygehus (SBR01, inverteret - lavere er bedre). Score 100 = landsgennemsnit.",
    boundary: "Socialt fundament: alle borgere bør have en forventet levetid der som minimum matcher landsgennemsnittet.",
    dataYear: "2022-2023",
    limitations: "Middellevetid er en gennemsnitsbetragtning. Sygehusbenyttelse kan afspejle både dårligt helbred og god adgang til sundhedsvæsenet.",
    csvFile: "doughnut_scores.csv + sundhed_extra_scores.csv",
  },
  uddannelse: {
    id: "uddannelse",
    scoring: "Gennemsnit af to indikatorer: (1) Andel af 30-34-årige med kompetencegivende uddannelse (HFUDD10, direkte). (2) Andel af 25-29-årige med kun grundskole (HFUDD11, inverteret - lavere er bedre). Score 100 = landsgennemsnit.",
    boundary: "Socialt fundament: alle borgere bør have adgang til uddannelse. EU-mål: 45% af 25-34-årige med videregående uddannelse i 2030.",
    dataYear: "2023-2024",
    limitations: "De to indikatorer måler komplementære aspekter: højtuddannede og lavtuddannede. Fanger ikke uddannelseskvalitet eller frafald undervejs.",
    csvFile: "doughnut_scores.csv + uddannelse_extra_scores.csv",
  },
  velfaerd: {
    id: "velfaerd",
    scoring: "Gennemsnit af seks indikatorer: disponibel indkomst, beskæftigelsesfrekvens, børnefattigdom (inverteret), Gini-koefficient (inverteret), udsatte børn og unge (inverteret, BU43) og unge uden for uddannelse/beskæftigelse - NEET (inverteret, NEET1). Hver indikator normaliseres mod landsgennemsnittet (score 100 = gennemsnit). For inverterede indikatorer bruges formlen: (landsgennemsnit / kommune) * 100.",
    boundary: "Socialt fundament: materielle levevilkår der sikrer værdigt liv for alle. Ingen absolut grænse - relativ til landsgennemsnit.",
    dataYear: "2022-2024",
    limitations: "Gini og børnefattigdom kommer fra samme DST-tabel (IFOR41) og kan korrelere. Disponibel indkomst justerer ikke for købekraft mellem kommuner. BU43 og NEET dækker forskellige aldersgrupper (0-22 og 16-24).",
    csvFile: "doughnut_scores.csv + velfaerd_extra_scores.csv",
  },
  bolig: {
    id: "bolig",
    scoring: "Gennemsnit af to indikatorer: (1) Andel ubeboede boliger (BOL101, inverteret - lavere er bedre). (2) Gennemsnitligt boligareal pr. person i m² (BOL106, direkte - mere plads er bedre). Score 100 = landsgennemsnit.",
    boundary: "Socialt fundament: alle borgere bør have adgang til en god og rummelig bolig.",
    dataYear: "2023-2025",
    limitations: "Ubeboede boliger fanger ikke boligkvalitet eller pris. Boligareal pr. person er et gennemsnit og skjuler ulighed.",
    csvFile: "doughnut_scores.csv + bolig_extra_scores.csv",
  },
  samskabelse: {
    id: "samskabelse",
    scoring: "Gennemsnit af to indikatorer: (1) Stemmedeltagelse ved kommunalvalget 2021 (LABY08, direkte). (2) Musikskoleelever pr. 1.000 indbyggere (SKOLM02B, direkte - proxy for kulturdeltagelse og samskabelse). Score 100 = landsgennemsnit.",
    boundary: "Socialt fundament: aktivt demokratisk medborgerskab og kulturel deltagelse.",
    dataYear: "2021-2024",
    limitations: "Stemmedeltagelse fanger kun formel demokratisk deltagelse. Musikskoleelever er en proxy for kulturelt engagement, men dækker primært børn og unge.",
    csvFile: "democracy_scores.csv + samskabelse_extra_scores.csv",
  },
  faellesskaber: {
    id: "faellesskaber",
    scoring: "Gennemsnit af to indikatorer: (1) Idrætsmedlemskab som andel af befolkningen (IDRAKT02) - direkte ratio til landsgennemsnit. (2) Anmeldte forbrydelser pr. 1.000 indbyggere (STRAF11) - inverteret ratio (lavere kriminalitet = højere score). Score 100 = landsgennemsnit.",
    boundary: "Socialt fundament: stærke fællesskaber med aktivt foreningsliv og tryghed.",
    dataYear: "2024",
    limitations: "Idrætsmedlemskab dækker kun organiseret idræt (DIF/DGI), ikke andre foreninger. Kriminalitet som tryghedsindikator fanger kun anmeldte forbrydelser og afspejler ikke nødvendigvis oplevet tryghed.",
    csvFile: "faellesskaber_scores.csv",
  },
  lokalsamfund: {
    id: "lokalsamfund",
    scoring: "Gennemsnit af fem indikatorer: (1) Biblioteksudlån pr. indbygger (BIB1, direkte). (2) Idrætsfaciliteter pr. 10.000 indb. (IDRFAC01, direkte). (3) Klassekvotient grundskole (KVOTIEN, inverteret - færre elever pr. klasse er bedre). (4) Normering daginstitution 3-5 år (BOERN8, inverteret - færre børn pr. voksen er bedre). (5) Kommunale idrætsudgifter pr. indb. (IDRFIN02, direkte). Score 100 = landsgennemsnit.",
    boundary: "Socialt fundament: levende lokalsamfund med gode services, faciliteter og kulturtilbud.",
    dataYear: "2023-2024",
    limitations: "Proxyer for serviceadgang. Dækker ikke alle vigtige services (læger, butikker). Normering og klassekvotienter fanger ikke kvaliteten af tilbuddene.",
    csvFile: "lokalsamfund_scores.csv + lokalsamfund_extra_scores.csv",
  },
  mobilitet: {
    id: "mobilitet",
    scoring: "Gennemsnit af to indikatorer: (1) Gennemsnitlig pendlingsafstand i km (AFSTB4) - inverteret ratio (kortere afstand = højere score). (2) Familier med bilrådighed (BIL800) - direkte ratio til landsgennemsnit. Score 100 = landsgennemsnit.",
    boundary: "Socialt fundament: adgang til mobilitet uanset geografi og økonomi.",
    dataYear: "2023-2024",
    limitations: "Bilrådighed er en proxy for transportadgang - i bykommuner er lav bilrådighed et tegn på god kollektiv trafik, i landkommuner det modsatte. Pendlingsafstand fanger kun beskæftigedes transport, ikke ældre eller unges.",
    csvFile: "mobilitet_scores.csv",
  },
  klimatilpasning: {
    id: "klimatilpasning",
    scoring: "Ingen data endnu. Potentielle indikatorer: oversvømmelsesrisiko, klimatilpasningsplaner, grønne arealer til regnvandshåndtering.",
    limitations: "Afventer tilgængelige kommunefordelte data.",
  },
};

const ECO_METHODS: Record<string, MethodInfo> = {
  klimapaavirkning: {
    id: "klimapaavirkning",
    scoring: "Territoriale CO2e-udledninger pr. indbygger. Ratio = (faktisk udledning / grænseværdi) * 100. Over 100 = overshoot (udleder mere end budgettet tillader).",
    boundary: "3 ton CO2e pr. person pr. år (Paris-aftalens budget for territorial udledning, IPCC 1.5°C-scenarie).",
    dataYear: "2023",
    limitations: "Dækker ca. 70 af 98 kommuner. Territorialt regnskab fanger ikke forbrug - se Forbrugsbaseret CO2.",
    csvFile: "climate_scores.csv",
  },
  forurening: {
    id: "forurening",
    scoring: "Ingen pålidelig kommunal datakilde endnu. Dækker den planetære grænse for 'novel entities' - kemisk forurening, mikroplast, PFAS, pesticider mv. Affaldsdata (tidligere brugt som proxy her) er flyttet til Cirkularitet-dimensionen, da affaldsmængde er en bedre indikator for materialeforbrug end for kemisk forurening.",
    limitations: "Direkte forureningsdata (PFAS, pesticider, tungmetaller) er ikke kommunefordelt i StatBank. Potentielle fremtidige kilder: NOVANA-overvågning (Miljøstyrelsen), jordforureningsdata (regionerne), DCE luftkvalitetsmålinger.",
  },
  luftkvalitet: {
    id: "luftkvalitet",
    scoring: "Ingen data endnu. Potentielle indikatorer: PM2.5-koncentration, NOx, ozon-dage over grænseværdi.",
    limitations: "DCE/Aarhus Universitet har modelberegninger, men de er ikke let tilgængelige som kommunalt datasæt.",
  },
  cirkularitet: {
    id: "cirkularitet",
    scoring: "Gennemsnit af to indikatorer: (1) Genanvendelsesprocent for husholdningsaffald - eco-ratio = (65% EU-mål / faktisk %) * 100. Over 100 = genanvender for lidt. (2) Husholdningsaffald i kg pr. indbygger (inverteret - lavere er bedre). Over 100 = producerer mere affald end landsgennemsnittet.",
    boundary: "65% genanvendelse (EU Affaldsdirektiv 2035) + lavest muligt affald pr. capita (landsgennemsnit som reference).",
    dataYear: "2023",
    limitations: "Reel genanvendelse kan afvige fra indsamlet til genanvendelse. Omfatter kun husholdningsaffald, ikke erhvervsaffald.",
    csvFile: "consumption_scores.csv + forurening_scores.csv",
  },
  naeringsstoffer: {
    id: "naeringsstoffer",
    scoring: "Gennemsnit af to indikatorer: (1) Kvælstof-udledning (ton total-N) pr. 1.000 indbyggere via spildevand. (2) Fosfor-udledning (ton total-P) pr. 1.000 indbyggere via spildevand. Eco-konvention: score over 100 = kommunen udleder mere end landsgennemsnittet (overshoot). Under 100 = udleder mindre (inden for grænsen).",
    boundary: "Landsgennemsnittet som reference. Lavere næringsstofudledning er bedre for vandmiljøet.",
    dataYear: "2024",
    limitations: "Dækker kun punktkilder via spildevand (renseanlæg, dambrug, havbrug, industri, spredt bebyggelse, regnbetinget). Fanger ikke diffus udledning fra landbrug, som er den største kvælstofkilde i Danmark.",
    csvFile: "naeringsstoffer_scores.csv",
  },
  vand: {
    id: "vand",
    scoring: "Gennemsnit af to indikatorer: (1) Spildevandsudledning (1.000 m³) pr. 1.000 indbyggere. (2) Vandindvinding (mio. m³) pr. 1.000 indbyggere. Eco-konvention: score over 100 = kommunen bruger/udleder mere vand end landsgennemsnittet (overshoot). Under 100 = lavere pres på vandressourcer (inden for grænsen).",
    boundary: "Landsgennemsnittet som reference. Lavere vandforbrug og spildevandsudledning er bedre.",
    dataYear: "2024",
    limitations: "Måler kvantitativt pres på vandressourcer, ikke kvalitet (nitrat, pesticider, PFAS i grundvand). Grundvandskvalitetsdata er ikke kommunefordelt i StatBank. Vandindvinding til markvanding varierer kraftigt mellem kommuner.",
    csvFile: "vand_scores.csv",
  },
  arealanvendelse: {
    id: "arealanvendelse",
    scoring: "Andel af kommunens areal der er naturområder (skov, hede, mose, eng, strandeng). Ratio = (grænseværdi / faktisk naturandel) * 100. Over 100 = under grænsen (for lidt natur).",
    boundary: "30% naturområder (EU Biodiversitetsstrategi 2030, 30x30-målet).",
    dataYear: "2022",
    limitations: "Arealstatistik skelner ikke mellem naturkvalitet - en plantage tæller som skov. Se Biodiversitet for kvalitetsvurdering.",
    csvFile: "land_use_scores.csv (afventer generering)",
  },
  biodiversitet: {
    id: "biodiversitet",
    scoring: "Baseret på DCE/Aarhus Universitets Bioscore (rapport SR456). Bioscore er 0-19 og sammensættes af Artsscore (0-9, dokumenterede arter) + Proxyscore (0-10, landskabsstruktur). Vi bruger andelen af kommunens areal med bioscore >= 8 (DCE's kategori 'væsentlige naturværdier'). Ratio = (30% mål / faktisk andel) * 100. Over 100 = under grænsen (for lidt kvalitetsnatur).",
    boundary: "30% af kommunens areal med bioscore >= 8 (operationalisering af 30x30-målet med kvalitetskrav via DCE's tærskelværdier: <4 uvæsentlig, 4-7 potentielt interessant, 8-11 væsentlige naturværdier, 12-19 uerstattelige levesteder).",
    dataYear: "2021",
    limitations: "Bioscore er baseret på kortlægning fra 2021 og opdateres ikke løbende. Artsscore kræver at arealet er besøgt af biologer - ubesøgte arealer scorer lavt selv hvis de har høj naturværdi. Proxyscore kompenserer delvist for dette.",
    csvFile: "biodiversitet_scores.csv",
  },
  forbrug_co2: {
    id: "forbrug_co2",
    scoring: "Nationalt gennemsnit for forbrugsbaseret CO2e pr. person (inkl. import). Ratio = (faktisk udledning / grænseværdi) * 100. Samme værdi for alle kommuner da data ikke er kommunefordelt. Aktuelt: ca. 11 ton CO2e/person, grænse 3 ton, dvs. ratio ca. 367 (kraftig overshoot).",
    boundary: "3 ton CO2e pr. person pr. år (Paris-budget, forbrugsbaseret - inkluderer importerede udledninger).",
    dataYear: "2022 (seneste CONCITO/Energistyrelsen-opgørelse)",
    limitations: "Ikke kommunefordelt - alle kommuner får samme ratio. Det reelle forbrugsaftryk varierer med indkomst og livsstil. Forventes differentieret i fremtidige versioner.",
    csvFile: "Hardkodet i data.ts (nationalt gennemsnit)",
  },
};

function IndicatorCard({ id }: { id: string }) {
  const ind = INDICATORS.find((i) => i.id === id);
  if (!ind) return null;
  return (
    <div className="flex items-center justify-between py-1.5 px-3 bg-gray-50 rounded text-sm">
      <span className="text-gray-700">{ind.name}</span>
      <div className="flex items-center gap-3 text-xs text-gray-400">
        <span>{ind.inverse ? "inverteret" : "direkte"}</span>
        <a href={ind.source} target="_blank" rel="noopener" className="text-blue-600 hover:underline">
          {ind.table} ↗
        </a>
      </div>
    </div>
  );
}

function StatusBadge({ hasData }: { hasData: boolean }) {
  return hasData ? (
    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 uppercase">
      Aktiv
    </span>
  ) : (
    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-500 uppercase">
      Afventer data
    </span>
  );
}

export default function MetodePage() {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Metode & datakilder</h2>
        <p className="text-gray-500 text-sm">
          Detaljeret dokumentation af hvordan hver dimension beregnes, hvilke data der bruges, og hvilke begrænsninger der er.
        </p>
      </div>

      {/* Quick navigation */}
      <nav className="mb-8 p-4 bg-white border border-gray-200 rounded-xl">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Gå til</p>
        <div className="grid grid-cols-2 gap-x-8 gap-y-1">
          <div>
            <p className="text-xs font-semibold text-emerald-700 mb-1">Socialt fundament</p>
            {SOCIAL_CATEGORIES.map((cat) => (
              <a key={cat.id} href={`#${cat.id}`} className="block text-sm text-blue-600 hover:underline py-0.5">
                {cat.name}
                {cat.indicatorIds.length === 0 && <span className="text-gray-400 ml-1">(ingen data)</span>}
              </a>
            ))}
          </div>
          <div>
            <p className="text-xs font-semibold text-red-600 mb-1">Økologisk loft</p>
            {ECOLOGICAL_DIMENSIONS.map((dim) => {
              const method = ECO_METHODS[dim.id];
              const hasData = !!dim.source;
              return (
                <a key={dim.id} href={`#${dim.id}`} className="block text-sm text-blue-600 hover:underline py-0.5">
                  {dim.name}
                  {!hasData && <span className="text-gray-400 ml-1">(ingen data)</span>}
                </a>
              );
            })}
          </div>
        </div>
      </nav>

      {/* General scoring explanation */}
      <section className="mb-10 p-5 bg-amber-50 border border-amber-200 rounded-xl">
        <h3 className="text-base font-semibold text-gray-900 mb-2">Generelt om scoring</h3>
        <p className="text-sm text-gray-700 leading-relaxed mb-2">
          Platformen bruger to forskellige scoringskonventioner:
        </p>
        <p className="text-sm text-gray-700 leading-relaxed">
          <strong>Socialt fundament:</strong> Score 100 = landsgennemsnit. Over 100 er bedre end gennemsnit (grønt), under 100 er dårligere (rødt).
          Røde segmenter i den indre ring viser &quot;shortfall&quot; - kommunen lever ikke op til det sociale minimum.
        </p>
        <p className="text-sm text-gray-700 leading-relaxed mt-2">
          <strong>Økologisk loft:</strong> Score 100 = grænseværdi. Under 100 er godt (inden for grænsen), over 100 er &quot;overshoot&quot; (rødt).
          Røde segmenter i den ydre ring viser overskridelse af den planetære grænse.
        </p>
        <p className="text-sm text-gray-700 leading-relaxed mt-4">
          <strong>Vægtning:</strong> Hver kategori (f.eks. Sundhed, Velfærd, Bolig) beregnes som et simpelt gennemsnit af sine indikatorer.
          Det samlede sociale gennemsnit er et gennemsnit af kategorierne - ikke af de individuelle indikatorer.
          Det betyder at kategorier med få indikatorer (f.eks. Bolig med 2) vægter lige så tungt som kategorier med mange (f.eks. Velfærd med 6).
          Dette er et bevidst valg: hver dimension i doughnut-modellen anses for lige vigtig, uanset hvor mange indikatorer der måler den.
        </p>
        <p className="text-sm text-gray-700 leading-relaxed mt-2">
          <strong>Inverterede indikatorer:</strong> For indikatorer hvor lavere er bedre (f.eks. kriminalitet, affald, børnefattigdom)
          beregnes ratioen inverteret: (landsgennemsnit / kommune) × 100. Kommuner med en værdi på 0 tildeles en score på 150 (cap)
          for at undgå division med nul, og fordi manglende data ikke bør fortolkes som perfekt score.
        </p>
      </section>

      {/* === SOCIALT FUNDAMENT === */}
      <div className="mb-12">
        <h3 className="text-lg font-bold text-gray-900 mb-6 pb-2 border-b-2 border-emerald-200">
          Socialt fundament
        </h3>

        <div className="space-y-6">
          {SOCIAL_CATEGORIES.map((cat) => {
            const method = SOCIAL_METHODS[cat.id];
            const hasData = cat.indicatorIds.length > 0;

            return (
              <section
                key={cat.id}
                id={cat.id}
                className="p-5 bg-white border border-gray-200 rounded-xl scroll-mt-20"
              >
                <div className="flex items-center gap-3 mb-3">
                  <h4 className="text-base font-semibold text-gray-900">{cat.name}</h4>
                  <StatusBadge hasData={hasData} />
                </div>

                {cat.description && (
                  <p className="text-sm text-gray-600 mb-4">{cat.description}</p>
                )}

                {method && (
                  <div className="space-y-3 text-sm">
                    <div>
                      <p className="font-medium text-gray-800 mb-1">Beregning</p>
                      <p className="text-gray-600">{method.scoring}</p>
                    </div>

                    {method.boundary && (
                      <div>
                        <p className="font-medium text-gray-800 mb-1">Grænseværdi</p>
                        <p className="text-gray-600">{method.boundary}</p>
                      </div>
                    )}

                    {method.dataYear && (
                      <div>
                        <p className="font-medium text-gray-800 mb-1">Datatidspunkt</p>
                        <p className="text-gray-600">{method.dataYear}</p>
                      </div>
                    )}

                    {method.limitations && (
                      <div>
                        <p className="font-medium text-gray-800 mb-1">Begrænsninger</p>
                        <p className="text-gray-600">{method.limitations}</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Indicator list */}
                {cat.indicatorIds.length > 0 && (
                  <div className="mt-4">
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                      Indikatorer ({cat.indicatorIds.length})
                    </p>
                    <div className="space-y-1">
                      {cat.indicatorIds.map((id) => (
                        <IndicatorCard key={id} id={id} />
                      ))}
                    </div>
                  </div>
                )}
              </section>
            );
          })}
        </div>
      </div>

      {/* === ØKOLOGISK LOFT === */}
      <div className="mb-12">
        <h3 className="text-lg font-bold text-gray-900 mb-6 pb-2 border-b-2 border-red-200">
          Økologisk loft
        </h3>

        <div className="space-y-6">
          {ECOLOGICAL_DIMENSIONS.map((dim) => {
            const method = ECO_METHODS[dim.id];
            const hasData = !!dim.source;

            return (
              <section
                key={dim.id}
                id={dim.id}
                className="p-5 bg-white border border-gray-200 rounded-xl scroll-mt-20"
              >
                <div className="flex items-center gap-3 mb-3">
                  <h4 className="text-base font-semibold text-gray-900">{dim.name}</h4>
                  <StatusBadge hasData={hasData} />
                </div>

                {dim.description && (
                  <p className="text-sm text-gray-600 mb-4">{dim.description}</p>
                )}

                {method && (
                  <div className="space-y-3 text-sm">
                    <div>
                      <p className="font-medium text-gray-800 mb-1">Beregning</p>
                      <p className="text-gray-600">{method.scoring}</p>
                    </div>

                    {method.boundary && (
                      <div>
                        <p className="font-medium text-gray-800 mb-1">Grænseværdi</p>
                        <p className="text-gray-600">{method.boundary}</p>
                      </div>
                    )}

                    {dim.unit && (
                      <div>
                        <p className="font-medium text-gray-800 mb-1">Enhed</p>
                        <p className="text-gray-600">{dim.unit}</p>
                      </div>
                    )}

                    {method.dataYear && (
                      <div>
                        <p className="font-medium text-gray-800 mb-1">Datatidspunkt</p>
                        <p className="text-gray-600">{method.dataYear}</p>
                      </div>
                    )}

                    {dim.source && (
                      <div>
                        <p className="font-medium text-gray-800 mb-1">Datakilde</p>
                        <p className="text-gray-600">
                          <a href={dim.source} target="_blank" rel="noopener" className="text-blue-600 hover:underline">
                            {dim.source} ↗
                          </a>
                        </p>
                      </div>
                    )}

                    {method.csvFile && (
                      <div>
                        <p className="font-medium text-gray-800 mb-1">Datafil</p>
                        <p className="text-gray-600 font-mono text-xs">{method.csvFile}</p>
                      </div>
                    )}

                    {method.limitations && (
                      <div>
                        <p className="font-medium text-gray-800 mb-1">Begrænsninger</p>
                        <p className="text-gray-600">{method.limitations}</p>
                      </div>
                    )}
                  </div>
                )}
              </section>
            );
          })}
        </div>
      </div>

      {/* Data processing note */}
      <section className="p-5 bg-gray-50 border border-gray-200 rounded-xl mb-8">
        <h3 className="text-base font-semibold text-gray-900 mb-3">Databehandling og kildekode</h3>
        <p className="text-sm text-gray-600 leading-relaxed">
          Al databehandling sker via Python-scripts i <code className="bg-gray-200 px-1 py-0.5 rounded text-xs">scripts/</code>-mappen
          i projektets GitHub-repo. CSV-filer i <code className="bg-gray-200 px-1 py-0.5 rounded text-xs">data/</code>-mappen
          indeholder de beregnede ratioer der vises på platformen. Webappen er bygget med Next.js og deployet på Netlify.
        </p>
        <p className="text-sm text-gray-600 leading-relaxed mt-2">
          Platformen er open source og under aktiv udvikling. Bidrag og feedback er velkomne.
        </p>
      </section>
    </div>
  );
}
