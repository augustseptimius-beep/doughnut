import type { Metadata } from "next";
import { SOCIAL_CATEGORIES, INDICATORS, ECOLOGICAL_DIMENSIONS } from "@/lib/shared";

export const metadata: Metadata = {
  title: "Metode & datakilder — Doughnut Economics Danmark",
  description: "Detaljeret dokumentation af metodik, indikatorer, grænseværdier og datakilder for alle dimensioner.",
};

/* ─── Method metadata per dimension ─── */

interface MethodSource {
  label: string;
  url: string;
}

interface MethodInfo {
  id: string;
  scoring: string;         // how the score/ratio is calculated
  boundary?: string;       // what the planetary boundary / social floor is
  boundarySources?: MethodSource[];  // clickable references for the boundary
  dataYear?: string;
  limitations?: string;
  csvFile?: string;
}

/* ─── Rationale per indicator ─── */
const INDICATOR_RATIONALES: Record<string, string> = {
  // Sundhed
  life_expectancy: "Det mest direkte og internationalt sammenlignelige mål for befolkningens generelle sundhedstilstand. Langt tidsserie i DST (HISBK) giver høj datakvalitet.",
  hospital_use: "Hyppig sygehusbenyttelse signalerer dårlig forebyggelse og høj sygelighed i befolkningen. Inverteret: kommuner med lavere benyttelse end landsgennemsnittet scorer bedre.",
  // Uddannelse
  education: "Andel af 30-34-årige med erhvervskompetencegivende uddannelse er det primære politiske måleparameter for uddannelsesniveau. Absolut baseline: nationalt mål på 95% (Børne- og Undervisningsministeriet).",
  low_education: "Andel af 25-29-årige med kun grundskole som højeste uddannelse. Fanger den sårbare ende af uddannelsesspektret og er særligt vigtig som indikator i landdistrikter og socialt belastede områder.",
  // Velfærd
  disposable_income: "Disponibel indkomst pr. person er det bredeste mål for materiel levestandard - inkluderer løn, overførsler og kapitalindkomst minus skat og bidrag.",
  employment: "Beskæftigelsesfrekvens afspejler adgang til arbejde, som er centralt for både indkomst, selvforsørgelse og social deltagelse.",
  child_poverty: "Andel af børn 0-17 år i relativ fattigdom (LABY07). Relativ fattigdom defineres som disponibel indkomst under 50% af medianen. Børnefattigdom er en direkte indikator for social ulighed og risiko for negativ social arv.",
  gini: "Gini-koefficient måler den samlede indkomstulighed i kommunen. Høj ulighed underminerer social sammenhæng, tillid og fælles institutioner.",
  low_income: "Andel af befolkningen med indkomst under 60% af medianindkomsten - det internationale standardmål for relativ fattigdom (DST LABY07).",
  vulnerable_children: "Andel udsatte børn og unge med anbringelse eller forebyggende foranstaltninger (BU43) er en stærk indikator for social belastning og kommunens udfordringer med social arv.",
  neet: "Andel unge (16-24 år) uden for uddannelse og beskæftigelse (NEET) signalerer risiko for langsigtet social eksklusion og er et anerkendt EU-måleparameter.",
  // Bolig
  vacant_housing: "Høj andel tomme boliger signalerer fraflytning og lavt boligmarked. Inverteret: kommuner med færre tomme boliger scorer bedre.",
  housing_area: "Boligareal pr. person afspejler boligstandard og -træthed. Mere plads er generelt forbundet med bedre livskvalitet.",
  // Demokrati
  voter_turnout: "Stemmedeltagelse ved kommunalvalg er det mest direkte og sammenlignelige mål for demokratisk engagement på lokalt plan. God datadækning for alle 98 kommuner (valg 2021).",
  // Kultur & fritid
  music_school: "Musikskoleelever pr. 1.000 indb. måler kulturel deltagelse og adgang til musikuddannelse for børn og unge. Et unikt dansk måleparameter for kommunal kultursatsning.",
  library_use: "Biblioteksudlån pr. indbygger er en anerkendt proxy for kulturel aktivitet, læring og brug af offentlige kulturinstitutioner. God datakvalitet (BIB1) og lang tidsserie.",
  sports_membership: "Andel af befolkningen med aktivt idrætsforeningsmedlemskab (DIF/DGI). Foreningsidræt er en central del af dansk civilsamfund og en proxy for frivilligt foreningsliv generelt.",
  kultur_spending: "Kommunale nettodriftsudgifter til biografer, teatre, musikarrangementer og kulturinstitutioner pr. indbygger (REGK31). Måler kommunens prioritering og investering i kulturlivet - uafhængigt af borgernes faktiske brug.",
  civil_society: "Kommunale udgifter til frivilligt folkeoplysende foreningsarbejde pr. indbygger (REGK31 funktion 33873). Proxy for kommunens investering i civilsamfund og det lokale foreningsliv - en central del af dansk demokratisk kultur.",
  // Tryghed & fællesskab
  crime_rate: "Anmeldte forbrydelser pr. 1.000 indb. er den bedst tilgængelige kvantitative indikator for tryghed på kommuneniveau. Lav kriminalitet er en forudsætning for social tillid og aktivt deltagelse i det offentlige rum.",
  traffic_accidents: "Tilskadekomne og dræbte i færdselsuheld pr. 100.000 indb. (UHELDK1). Trafiksikkerhed er en direkte indikator for fysisk tryghed i det offentlige rum og for kvaliteten af infrastruktur og hastighedszoner. Inverteret: færre ulykker er bedre.",
  // Lokalsamfund
  sports_facilities: "Idrætsfaciliteter pr. 10.000 indb. (IDRFAC01) måler den fysiske kapacitet for idræt og aktivt foreningsliv - det grundlæggende anlægsgrundlag for et aktivt lokalmiljø.",
  class_size: "Klassekvotient i grundskolen er en anerkendt kvalitetsindikator. Mindre klasser muliggør mere individuel opmærksomhed og er et politisk prioriteret mål.",
  daycare_ratio: "Normering i daginstitutioner (børn pr. voksen) er et grundlæggende kvalitetsmål for det tidlige barndomsmiljø. Lav normering gavner børns trivsel og personalets arbejdsmiljø.",
  sports_spending: "Kommunale idrætsudgifter pr. indb. (IDRFIN02) afspejler den samlede kommunale prioritering af idræt og fritid - og dermed forudsætningerne for foreningsliv og aktivt medborgerskab.",
  educated_staff: "Andel af pædagogisk personale i kommunale og selvejende daginstitutioner med pædagoguddannelse (professionsbachelor, BOERN1 kode 460). Nationalt har 42% af personalet INGEN pædagogisk uddannelse - stor variation kommunerne imellem (18%-58%). Et rent kvalitetsmål: komplement til normering (BOERN8), der kun måler kvantitet.",
  // Mobilitet
  commute_distance: "Gennemsnitlig pendlingsafstand afspejler tilgængelighed til arbejdsmarkedet. Lang pendling belaster livskvalitet og er typisk forbundet med lavere kollektiv trafikdækning.",
  car_access: "Familier med bilrådighed er en proxy for transportmuligheder. I bykommuner signalerer lav bilrådighed god kollektiv trafik; i landkommuner kan det betyde manglende mobilitetsmuligheder.",
  public_transport: "Andel af borgere med god adgang til offentlig transport (Meget højt + Højt serviceniveau), LABY49. Metodenote: data er kun tilgængeligt på kommunegruppe-niveau (5 grupper) - alle kommuner i samme gruppe tildeles identisk score. Landkommuner (G5) scorer konsekvent lavt uanset lokale forskelle.",
  // Sundhed
  gp_distance: "Gennemsnitlig afstand (km) til nærmeste praktiserende læge (SUNDAF01). Stor afstand er en adgangsbarriere for primær sundhedsydelse, særligt for ældre og ikke-bilister. Inverteret: kortere afstand er bedre.",
};

const SOCIAL_METHODS: Record<string, MethodInfo> = {
  sundhed: {
    id: "sundhed",
    scoring: "Gennemsnit af tre indikatorer: (1) Middellevetid (0-årige) sammenholdt med landsgennemsnittet. (2) Sygehusbenyttelse - andel af befolkningen med ophold på sygehus (SBR01, inverteret). (3) Afstand til nærmeste praktiserende læge i km (SUNDAF01, inverteret - kortere er bedre). Score 100 = landsgennemsnit.",
    boundary: "Socialt fundament: alle borgere bør have en forventet levetid der som minimum matcher landsgennemsnittet og have rimelig adgang til primær sundhedsydelse.",
    dataYear: "2022-2024",
    limitations: "Middellevetid er en gennemsnitsbetragtning. Sygehusbenyttelse kan afspejle både dårligt helbred og god adgang til sundhedsvæsenet. Lægeafstand dækker ikke kapacitet eller ventetider.",
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
    scoring: "Gennemsnit af syv indikatorer: disponibel indkomst, beskæftigelsesfrekvens, børnefattigdom (inverteret, LABY07), Gini-koefficient (inverteret), lavindkomst (inverteret, LABY07), udsatte børn og unge (inverteret, BU43) og unge uden for uddannelse/beskæftigelse - NEET (inverteret, NEET1). Hver indikator normaliseres mod landsgennemsnittet (score 100 = gennemsnit). For inverterede indikatorer bruges formlen: (landsgennemsnit / kommune) * 100.",
    boundary: "Socialt fundament: materielle levevilkår der sikrer værdigt liv for alle. Ingen absolut grænse - relativ til landsgennemsnit.",
    dataYear: "2022-2024",
    limitations: "Børnefattigdom (LABY07) og lavindkomst (LABY07) kommer fra samme DST-tabel og kan korrelere. Disponibel indkomst justerer ikke for købekraft mellem kommuner. BU43 og NEET dækker forskellige aldersgrupper (0-22 og 16-24).",
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
  demokrati: {
    id: "demokrati",
    scoring: "1 indikator: Stemmedeltagelse ved kommunalvalget 2021 (LABY08/KVBPCT, direkte ratio til landsgennemsnit). Score 100 = landsgennemsnit.",
    boundary: "Socialt fundament: aktivt demokratisk medborgerskab. Alle borgere bør have mulighed for og lyst til at deltage i den demokratiske proces.",
    dataYear: "2021",
    limitations: "Måler kun formel valgdeltagelse - ikke bredere politisk deltagelse som borgermøder, lokalt engagement eller civilsamfundsaktivitet. Valgdeltagelse varierer strukturelt: højere i kommuner med velstillet, ældre befolkning. Opdateres kun hvert 4. år ved kommunalvalg.",
    csvFile: "democracy_scores.csv",
  },
  kultur_fritid: {
    id: "kultur_fritid",
    scoring: "Gennemsnit af tre indikatorer: (1) Musikskoleelever pr. 1.000 indb. (SKOLM02B, direkte). (2) Biblioteksudlån pr. indb. (BIB1, direkte). (3) Kommunale kulturudgifter pr. indb. - nettodriftsudgifter til biografer, teatre, musikarrangementer og anden kultur (REGK31 funktion 33561-33564, direkte). Score 100 = landsgennemsnit.",
    boundary: "Socialt fundament: adgang til kulturliv og fritidsaktiviteter er en forudsætning for trivsel, social deltagelse og levende lokalsamfund.",
    dataYear: "2022-2024",
    limitations: "Musikskoleelever dækker primært børn og unge. Biblioteksudlån afspejler ikke digitale udlån fuldt ud. Kulturudgifter eksluderer biblioteksudgifter (separat indikator) og idrætsudgifter (separat indikator i Lokalsamfund). Idrætsmedlemskab er flyttet til Tryghed & fællesskab som mål for social kapital.",
    csvFile: "lokalsamfund_scores.csv + samskabelse_extra_scores.csv + doughnut_scores.csv (kultur_spending)",
  },
  tryghed: {
    id: "tryghed",
    scoring: "Gennemsnit af tre indikatorer: (1) Anmeldte forbrydelser pr. 1.000 indb. (STRAF11, inverteret). (2) Trafikulykker - tilskadekomne og dræbte pr. 100.000 indb. (UHELDK1, inverteret). (3) Idrætsmedlemskab som andel af befolkningen (IDRAKT02, direkte - proxy for social kapital og foreningsliv). Score 100 = landsgennemsnit.",
    boundary: "Socialt fundament: borgere skal kunne leve trygt - i det offentlige rum, i trafikken og med social sammenhæng i lokalsamfundet.",
    dataYear: "2022-2024",
    limitations: "Anmeldt kriminalitet afspejler ikke oplevet tryghed eller mørketallet. Politiets tilstedeværelse og anmeldelseskultur varierer. Trafikulykker varierer med vejnet og pendlingsforhold. Idrætsmedlemskab er en proxy for social kapital, ikke en direkte trygheds-indikator.",
    csvFile: "faellesskaber_scores.csv",
  },
  lokalsamfund: {
    id: "lokalsamfund",
    scoring: "Gennemsnit af seks indikatorer: (1) Idrætsfaciliteter pr. 10.000 indb. (IDRFAC01, direkte). (2) Klassekvotient grundskole (KVOTIEN, inverteret). (3) Normering daginstitution 3-5 år (BOERN8, inverteret). (4) Kommunale idrætsudgifter pr. indb. (IDRFIN02, direkte). (5) Udgifter til frivillige foreninger pr. indb. (REGK31 funktion 33873, direkte). (6) Andel pædagoguddannede i daginstitutioner (BOERN1 kode 460, direkte). Score 100 = landsgennemsnit.",
    boundary: "Socialt fundament: nærhed til velfungerende basale services er en forudsætning for et godt hverdagsliv - uanset om man bor i by eller på land.",
    dataYear: "2022-2024",
    limitations: "Dækker ikke alle relevante services (indkøb). BOERN8 (normering) og BOERN1 (uddannelse) er komplementære mål for daginstitutionskvalitet - normering dækker kvantitet, uddannelse dækker personalekvalitet. Klassekvotienter fanger ikke undervisningskvalitet.",
    csvFile: "lokalsamfund_extra_scores.csv",
  },
  mobilitet: {
    id: "mobilitet",
    scoring: "Gennemsnit af tre indikatorer: (1) Gennemsnitlig pendlingsafstand i km (AFSTB4, inverteret). (2) Familier med bilrådighed (BIL800, direkte). (3) Andel med god adgang til offentlig transport (LABY49, direkte - % med Meget højt + Højt serviceniveau). Score 100 = landsgennemsnit.",
    boundary: "Socialt fundament: adgang til mobilitet uanset geografi og økonomi.",
    dataYear: "2023-2025",
    limitations: "Bilrådighed er en proxy for transportadgang - i bykommuner er lav bilrådighed et tegn på god kollektiv trafik, i landkommuner det modsatte. Pendlingsafstand fanger kun beskæftigedes transport. METODENOTE for offentlig transport (LABY49): data er KUN tilgængeligt på kommunegruppe-niveau (5 grupper) - alle kommuner i samme gruppe tildeles identisk score uanset lokale forskelle. Landkommuner (G5, herunder Thisted) scorer lavt som gruppe. Indikatoren er medtaget da retningen er korrekt og dataene er officielle DST-nøgletal.",
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
    scoring: "Gennemsnit af to indikatorer: (1) NO2-koncentration (kvælstofdioxid, µg/m³ årsgennemsnit) og (2) PM2.5-koncentration (fine partikler, µg/m³ årsgennemsnit). Begge sammenholdes med WHO's retningslinjer fra 2021. Ratio = (kommunens koncentration / WHO-grænse) × 100. Ratio over 100 = over WHO-grænsen. Beregnet som befolkningsvægtet gennemsnit af 1×1 km modelceller inden for kommunegreænsen via spatial join.",
    boundary: "WHO 2021 Air Quality Guidelines (årsgennemsnit): NO2 = 10 µg/m³, PM2.5 = 5 µg/m³. WHO-grænsen er valgt frem for EU's grænseværdier (NO2: 40 µg/m³, PM2.5: 25 µg/m³) fordi WHO-grænsen er videnskabeligt baseret på sundhedseffekter, mens EU-grænsen er et politisk kompromis. I 2023 overskrider alle 98 kommuner WHO-grænsen for PM2.5, og 6 kommuner overskrider NO2-grænsen.",
    boundarySources: [
      { label: "WHO Air Quality Guidelines 2021", url: "https://www.who.int/publications/i/item/9789240034228" },
      { label: "DCE/AU - Luftkvalitet 2022 (SR580)", url: "https://dce2.au.dk/pub/SR580.pdf" },
      { label: "Miljøportal WFS - luftkoncentrationer", url: "https://arld-extgeo.miljoeportal.dk/geoserver/wfs" },
    ],
    dataYear: "2023",
    limitations: "Modelberegnet baggrundskoncentration (UBM, 1×1 km grid) - ikke målte værdier. Fanger ikke lokale hotspots ved travle gadestrækninger (OSPM-model dækker dette, men kun i store byer). Kommunegennemsnittet inkluderer landlige arealer med lav forurening, hvilket trækker byernes reelle eksponering ned. PM2.5 i Danmark er i høj grad påvirket af langtransport fra kontinentet og hav - ikke kun lokale kilder.",
    csvFile: "luftforurening_scores.csv",
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
    scoring: "Gennemsnit af tre indikatorer: (1) Kvælstof-udledning (ton total-N) pr. 1.000 indbyggere via spildevand. (2) Fosfor-udledning (ton total-P) pr. 1.000 indbyggere via spildevand. (3) Landbrugets N-loft pr. ha landbrugsjord beregnet fra Vandområdeplan 3 (VP3, 2025): malbelas_n (max bæredygtig N-tilførsel til kysten i tons) divideret med det faktiske landbrugsareal i oplandet pr. kommune - jo lavere N-loft pr. ha, jo mere N-presset er kommunen. Eco-konvention: score over 100 = kommunen er mere belastet end landsgennemsnittet (overshoot). Under 100 = lavere pres end gennemsnit.",
    boundary: "Landsgennemsnittet som reference for alle tre indikatorer. Lavere næringsstofbelastning og strengere N-loft er bedre for vandmiljøet.",
    dataYear: "2024 (spildevand), 2025 (VP3 N-loft), 2026 (markblokke)",
    limitations: "Spildevand dækker kun punktkilder (renseanlæg, dambrug, havbrug, industri, spredt bebyggelse). Landbrugs-N viser det maksimale tilladte N-loft pr. ha - ikke den faktiske udvaskning, som kræver DCE's NLES5-model (kun tilgængeligt i PDF-rapporter). Grænseværdien er landsgennemsnittet, ikke en absolut planetær grænse.",
    csvFile: "naeringsstoffer_scores.csv + n_landbrug_scores.csv",
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
    scoring: "Kommunespecifikt estimat for forbrugsbaseret CO2e pr. person (inkl. import). Ratio = (estimat / grænseværdi) * 100. Kilde: Osei-Owusu et al. (2020) kommunebaseline (2011) nutidsjusteret med ENS Global Afrapportering 2025 (ENS-til-ENS skalering, faktor 0,7186). Interval: 9,4-17,3 ton CO2e/person. Grænse: 3 ton.",
    boundary: "3 ton CO2e/borger/år - et forskningsbaseret pejlemærke for forbrug foreneligt med Parisaftalens 1,5°C-mål. Ikke en officiel dansk eller EU-målsætning, men understøttet af tre uafhængige videnskabelige kilder: (1) Fanning et al. (2022) i Nature Sustainability analyserer 150 landes overshoot ift. per-capita planetære grænser og udgør det mest opdaterede grundlag for downscaled doughnut-modeller. (2) Hot or Cool Institute (2021) opstiller en tidstrappe: 2,5 ton (2030) - 1,4 ton (2040) - 0,7 ton (2050) baseret på IPCC's resterende kulstofbudget for 1,5°C. (3) Danske forskere (Tilsted, Bjørn, Lund m.fl.) anbefaler 3 ton i 2030 ud fra forsigtighedsprincippet og Danmarks historiske ansvar. Til sammenligning: den gennemsnitlige danskers forbrugsbaserede klimaaftryk er ca. 10 ton CO2e/år (ENS Global Afrapportering) - ca. 3 gange grænsen.",
    boundarySources: [
      { label: "Fanning et al. (2022), Nature Sustainability", url: "https://www.nature.com/articles/s41893-021-00799-z" },
      { label: "O'Neill et al. (2018), Nature Sustainability", url: "https://doi.org/10.1038/s41893-018-0021-4" },
      { label: "Good Life For All - interaktiv dataplatform (University of Leeds)", url: "https://goodlife.leeds.ac.uk/" },
      { label: "Hot or Cool Institute (2021), 1.5-Degree Lifestyles", url: "https://hotorcool.org/1-5-degree-lifestyles-report/" },
      { label: "Tilsted et al. - debatindlæg, Politiken (dec. 2023)", url: "https://samf.ku.dk/presse/kronikker-og-debat/2023/danmark-boer-indfoere-et-maal-for-vores-klimaaftryk-fra-forbrug" },
      { label: "Energistyrelsen, Global Afrapportering", url: "https://ens.dk/" },
    ],
    dataYear: "2023-estimat baseret på Osei-Owusu et al. 2020 + ENS GA 2025",
    limitations: "Tier 1-estimat: alle kommuner skaleres med samme nationale faktor (ensartet -28,1%). Den relative rangorden fra 2011 er bevaret, men lokale ændringer (f.eks. udfasning af oliefyr, pendlingsmønster) er ikke indregnet. Hverken el- eller fjernvarmemix er opdateret kommunespecifikt. Usikkerhedsmargen ca. ±10%.",
    csvFile: "cba_2023_estimate.csv (Osei-Owusu et al. 2020, DOI: 10.1016/j.ecolecon.2020.106778 + ENS Global Afrapportering 2025)",
  },
};

function IndicatorCard({ id }: { id: string }) {
  const ind = INDICATORS.find((i) => i.id === id);
  if (!ind) return null;
  const rationale = INDICATOR_RATIONALES[id];
  return (
    <div className="py-2 px-3 bg-gray-50 rounded text-sm">
      <div className="flex items-center justify-between">
        <span className="text-gray-700 font-medium">{ind.name}</span>
        <div className="flex items-center gap-3 text-xs text-gray-400">
          <span>{ind.inverse ? "inverteret" : "direkte"}</span>
          <a href={ind.source} target="_blank" rel="noopener" className="text-blue-600 hover:underline">
            {ind.table} ↗
          </a>
        </div>
      </div>
      {rationale && (
        <p className="mt-1 text-xs text-gray-500 leading-relaxed">{rationale}</p>
      )}
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
        <p className="text-gray-600 text-sm leading-relaxed mb-4">
          Danmarks 98 Doughnuts anvender Kate Raworths Doughnut Economics-ramme til at vurdere alle danske kommuners præstation på to linser: det <strong>sociale fundament</strong> (opfylder vi borgernes basale behov?) og det <strong>økologiske loft</strong> (respekterer vi naturens grænser?). Modellen er politisk neutral - den måler, ikke rangordner.
        </p>

        {/* Baseline-hierarki */}
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl mb-2">
          <h3 className="font-bold text-emerald-900 mb-3">Hierarki for baseline-valg</h3>
          <p className="text-sm text-emerald-800 mb-3">
            For alle indikatorer defineres et "100-punkt" - grænsen for hvornår en kommune lever op til standarden. Vi vælger altid den højest mulige kategori:
          </p>
          <div className="space-y-2">
            <div className="flex gap-3">
              <span className="text-xs font-bold text-white bg-emerald-700 rounded px-2 py-0.5 h-fit whitespace-nowrap">Niveau 1</span>
              <div>
                <p className="text-sm font-semibold text-emerald-900">Absolutte biofysiske og juridiske grænser</p>
                <p className="text-xs text-emerald-700">Naturen forhandler ikke. Eksempel: WHO&apos;s grænseværdi for partikelforurening (5 µg/m³) eller EU&apos;s Vandrammedirektiv.</p>
              </div>
            </div>
            <div className="flex gap-3">
              <span className="text-xs font-bold text-white bg-emerald-600 rounded px-2 py-0.5 h-fit whitespace-nowrap">Niveau 2</span>
              <div>
                <p className="text-sm font-semibold text-emerald-900">Nationale politiske målsætninger</p>
                <p className="text-xs text-emerald-700">Demokratisk vedtagne mål. Eksempel: 95%-målet for kompetencegivende uddannelse eller klimalovens 70%-reduktionsmål.</p>
              </div>
            </div>
            <div className="flex gap-3">
              <span className="text-xs font-bold text-white bg-emerald-500 rounded px-2 py-0.5 h-fit whitespace-nowrap">Niveau 3</span>
              <div>
                <p className="text-sm font-semibold text-emerald-900">Frontløber-metoden (Top 10% decilen)</p>
                <p className="text-xs text-emerald-700">Gennemsnittet af de 10 bedst præsterende danske kommuner. Logik: hvad 10 kommuner kan opnå, er empirisk muligt i en dansk kontekst.</p>
              </div>
            </div>
          </div>
        </div>
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
                        {method.boundarySources && method.boundarySources.length > 0 && (
                          <div className="mt-2 space-y-1">
                            <p className="text-xs font-medium text-gray-500">Kilder:</p>
                            <ul className="list-none space-y-0.5">
                              {method.boundarySources.map((src, idx) => (
                                <li key={idx} className="text-xs">
                                  <a href={src.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                                    {src.label} ↗
                                  </a>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
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
                        {method.boundarySources && method.boundarySources.length > 0 && (
                          <div className="mt-2 space-y-1">
                            <p className="text-xs font-medium text-gray-500">Kilder:</p>
                            <ul className="list-none space-y-0.5">
                              {method.boundarySources.map((src, idx) => (
                                <li key={idx} className="text-xs">
                                  <a href={src.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                                    {src.label} ↗
                                  </a>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
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
