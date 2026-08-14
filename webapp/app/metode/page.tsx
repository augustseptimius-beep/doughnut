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
  hospital_short: "Andel af befolkningen med kortvarigt sygehusophold (under 12 timer, SBR01). Akutte og ambulante besøg - høj andel kan signalere høj sygelighed eller lavt forebyggelsesniveau. Inverteret: lavere andel er bedre.",
  hospital_long: "Andel af befolkningen med indlæggelse på 12 timer eller derover (SBR01). Længere ophold indikerer alvorligere sygdomsforløb og er et stærkere signal om befolkningens helbredstilstand end kortere ophold. Inverteret: lavere andel er bedre.",
  // Uddannelse
  education: "Andel af 30-34-årige med erhvervskompetencegivende uddannelse er det primære politiske måleparameter for uddannelsesniveau. Absolut baseline: nationalt mål på 95% (Børne- og Undervisningsministeriet). Scoren beregnes nu mod dette mål (100 = 95% nået), ikke mod landsgennemsnittet.",
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
  bolig_fossil: "Kommunens samlede fossile varmeafhængighed: direkte olie-/gasopvarmning PLUS den fossile andel af fjernvarmen (fjernvarme-dækning × fjernvarmens fossile brændselsandel fra Energistyrelsens EPT). Opgøres på helårsboligernes OPVARMEDE AREAL i m² (DST BYGB40), ikke på antal beboere - varmebehov skalerer med kvadratmeter, ikke med hoveder. Scoret mod et absolut mål på 0% fossil, ikke landsgennemsnit, da udfasning af olie/gas er dansk politik. Inverteret: lavere andel er bedre. Værst er Nordsjællands gasområder (fx Furesø, Rudersdal); bedst er biomasse-fjernvarmebyer som Aarhus.",
  // Demokrati
  voter_turnout: "Stemmedeltagelse ved kommunalvalg er det mest direkte og sammenlignelige mål for demokratisk engagement på lokalt plan. God datadækning for alle 98 kommuner (valg 2021).",
  voter_turnout_national: "Stemmedeltagelse ved folketingsvalg 2026 (DST LABY09). Supplerer kommunalvalget med et nationalpolitisk mål for demokratisk engagement - de to valg trækker ikke altid i samme retning kommunerne imellem.",
  // Kultur & fritid
  music_school: "Musikskoleelever pr. 1.000 indb. måler kulturel deltagelse og adgang til musikuddannelse for børn og unge. Et unikt dansk måleparameter for kommunal kultursatsning.",
  library_use: "Biblioteksudlån pr. indbygger er en anerkendt proxy for kulturel aktivitet, læring og brug af offentlige kulturinstitutioner. God datakvalitet (BIB1) og lang tidsserie.",
  sports_membership: "Andel af befolkningen med aktivt idrætsforeningsmedlemskab (DIF/DGI). Foreningsidræt er en central del af dansk civilsamfund og en proxy for frivilligt foreningsliv generelt.",
  kultur_spending: "Kommunale nettodriftsudgifter til biografer, teatre, musikarrangementer og kulturinstitutioner pr. indbygger (REGK31). Måler kommunens prioritering og investering i kulturlivet - uafhængigt af borgernes faktiske brug.",
  civil_society: "Kommunale udgifter til frivilligt folkeoplysende foreningsarbejde pr. indbygger (REGK31 funktion 33873). Proxy for kommunens investering i civilsamfund og det lokale foreningsliv - en central del af dansk demokratisk kultur.",
  // Tryghed
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
  public_transport: "Andel af borgere med god adgang til offentlig transport (Meget højt + Højt serviceniveau), LABY49. Metodenote: data er kun tilgængeligt på kommunegruppe-niveau (5 grupper) - alle kommuner i samme gruppe tildeles identisk score. Landkommuner (G5) scorer konsekvent lavt uanset lokale forskelle.",
  // Sundhed
  gp_distance: "Gennemsnitlig afstand (km) til nærmeste praktiserende læge (SUNDAF01). Stor afstand er en adgangsbarriere for primær sundhedsydelse, særligt for ældre og ikke-bilister. Inverteret: kortere afstand er bedre.",
  medicin: "Recepter pr. 100 borgere på psykoanaleptika (DST MEDI1, ATC-gruppe N06: antidepressiva, ADHD-medicin og demens-medicin). Anvendes som proxy for mental sundhed. Inverteret: lavere forbrug er bedre. NB: Højt forbrug kan også afspejle bedre adgang til diagnose og behandling, ikke kun ringere mental sundhed.",
  laegekontakt: "Andel af befolkningen med mindst én kontakt til almen praktiserende læge i løbet af året (DST SYGP1). Måler adgang til og brug af primær sundhedsydelse. Direkte: højere andel er bedre, da det signalerer at borgerne kommer til lægen.",
  boerneovervaeght: "Andel af 6-7-årige børn med overvægt ved skolestart (DST LABY26, baseret på skolesundhedsplejens målinger). Tidlig indikator for folkesundhed og social ulighed. Inverteret: lavere andel er bedre. Begrænsning: data går kun til 2018 - DST opdaterer ikke længere tabellen.",
  hjemsyg: "Antal modtagere af hjemmesygepleje pr. 1.000 indbyggere (DST HJEMSYG). Proxy for sygelighed og plejebyrde, særligt blandt ældre. Inverteret: lavere antal er bedre. Begrænsning: 2025-tallene er foreløbige (baseret på første halvår) og kan ændre sig.",
};

const SOCIAL_METHODS: Record<string, MethodInfo> = {
  sundhed: {
    id: "sundhed",
    scoring: "Gennemsnit af otte indikatorer: (1) Middellevetid (0-årige) sammenholdt med landsgennemsnittet (HISBK). (2) Andel med kortvarigt sygehusophold under 12 timer (SBR01, inverteret). (3) Andel med indlæggelse 12 timer eller derover (SBR01, inverteret). (4) Afstand til nærmeste praktiserende læge i km (SUNDAF01, inverteret). (5) Antidepressivt forbrug, recepter pr. 100 borgere (MEDI1 N06, inverteret). (6) Andel med mindst én lægekontakt pr. år (SYGP1, direkte). (7) Overvægt blandt 6-7-årige (LABY26, inverteret). (8) Hjemmesygepleje-modtagere pr. 1.000 indb. (HJEMSYG, inverteret). Score 100 = landsgennemsnit.",
    boundary: "Socialt fundament: alle borgere bør have en forventet levetid der som minimum matcher landsgennemsnittet, rimelig adgang til primær sundhedsydelse og en lav forekomst af kroniske helbredsproblemer.",
    dataYear: "2018-2025",
    limitations: "Middellevetid er en gennemsnitsbetragtning. Sygehusbenyttelse kan afspejle både dårligt helbred og god adgang til sundhedsvæsenet. Korte og lange ophold er begge inverterede - dvs. høj score = lavt ophold. Lægeafstand dækker ikke kapacitet eller ventetider. Antidepressivt forbrug er proxy for mental sundhed, men kan også afspejle bedre adgang til behandling. Børneovervægt-data går kun til 2018. Hjemmesygepleje 2025-tal er foreløbige.",
    csvFile: "doughnut_scores.csv + sundhed_extra_scores.csv + medicin_scores.csv + laegekontakt_scores.csv + boerneovervaeght_scores.csv + hjemsyg_scores.csv",
  },
  uddannelse: {
    id: "uddannelse",
    scoring: "Gennemsnit af ti indikatorer: (1) Andel af 30-34-årige med kompetencegivende uddannelse (HFUDD10, scoret absolut mod det nationale 95 %-mål: ratio = andel/95 × 100). (2) Andel af 25-29-årige med kun grundskole (HFUDD11, inverteret). (3) Karaktergennemsnit folkeskolens afgangseksamen (UVM GS/KARA/KARAGNS, direkte). (4) Andel elever med >10% fravær (UVM GS/ELEVFRAV/FRAVAAR, inverteret). (5) Forventet ungdomsuddannelseskompetence (UVM GS/PROFMOD/PROFMOD, direkte). (6) Læreplads-søgende med afsluttet grundforløb (UVM EUD/PRAK/SØG, direkte). (7) Elevtrivsel i folkeskolen, gennemsnit (UVM GS/TRIV/TRIVIND, direkte). (8) Klassekvotient grundskole (KVOTIEN, inverteret). (9) Normering daginstitution 3-5 år (BOERN8, inverteret). (10) Andel pædagoguddannede i daginstitutioner (BOERN1 kode 460, direkte). Score 100 = landsgennemsnit (undtagen indikator 1, der scores mod 95 %-målet - derfor er kategorien 'blandet').",
    boundary: "Socialt fundament: alle borgere bør have adgang til uddannelse og et kvalitetsfuldt læringsmiljø. EU-mål: 45% af 25-34-årige med videregående uddannelse i 2030.",
    dataYear: "2022-2024",
    limitations: "Karaktergennemsnit afspejler ikke kun skolekvalitet men også socioøkonomisk baggrund. Klassekvotienter og normering fanger kvantitative mål, ikke undervisningskvalitet. UVM-data dækker skoleår 2023/2024 som seneste.",
    csvFile: "doughnut_scores.csv + uddannelse_extra_scores.csv + uvm_scores.csv + lokalsamfund_extra_scores.csv",
  },
  velfaerd: {
    id: "velfaerd",
    scoring: "Gennemsnit af syv indikatorer: disponibel indkomst, beskæftigelsesfrekvens, børnefattigdom (inverteret, LABY07), udsatte børn og unge (inverteret, BU43), NEET (inverteret, NEET1), relativ fattigdom (inverteret, IFOR12P) og underretninger om børn (inverteret, UND2). Score 100 = landsgennemsnit. NB: Gini og lavindkomst er flyttet til dimensionen Lighed.",
    boundary: "Socialt fundament: materielle levevilkår der sikrer værdigt liv for alle. Ingen absolut grænse - relativ til landsgennemsnit.",
    dataYear: "2022-2024",
    limitations: "Børnefattigdom (LABY07) og relativ fattigdom (IFOR12P) overlapper. Disponibel indkomst justerer ikke for købekraft mellem kommuner. BU43 og NEET dækker forskellige aldersgrupper (0-22 og 16-24).",
    csvFile: "doughnut_scores.csv + velfaerd_extra_scores.csv + lighed_scores.csv + underretning_scores.csv",
  },
  bolig: {
    id: "bolig",
    scoring: "Gennemsnit af to indikatorer: (1) Andel ubeboede boliger (BOL101, inverteret). (2) Gennemsnitligt boligareal pr. person i m² (BOL106, direkte). Score 100 = landsgennemsnit. NB: Fossil opvarmning er flyttet til dimensionen Energi, da opvarmningskilde er et energispørgsmål, ikke boligstandard.",
    boundary: "Socialt fundament: alle borgere bør have adgang til en god, rummelig og bæredygtig bolig.",
    dataYear: "2023",
    limitations: "Ubeboede boliger fanger ikke boligkvalitet eller pris. Boligareal pr. person er et gennemsnit og skjuler ulighed.",
    csvFile: "doughnut_scores.csv + bolig_extra_scores.csv",
  },
  demokrati: {
    id: "demokrati",
    scoring: "Gennemsnit af 2 indikatorer: (1) Stemmedeltagelse ved kommunalvalget 2021 (LABY08/KVBPCT, direkte ratio til landsgennemsnit). (2) Stemmedeltagelse ved folketingsvalget 2026 (LABY09, direkte ratio til landsgennemsnit). Score 100 = landsgennemsnit. NB: Kønsbalance i ledelse er flyttet til dimensionen Ligestilling.",
    boundary: "Socialt fundament: aktivt demokratisk medborgerskab. Alle borgere bør have mulighed for og lyst til at deltage i den demokratiske proces.",
    dataYear: "2021, 2026",
    limitations: "Måler kun formel valgdeltagelse - ikke bredere politisk deltagelse som borgermøder, lokalt engagement eller civilsamfundsaktivitet. Valgdeltagelse varierer strukturelt: højere i kommuner med velstillet, ældre befolkning. Kommunalvalg opdateres hvert 4. år; folketingsvalg efter behov.",
    csvFile: "democracy_scores.csv",
  },
  kultur_fritid: {
    id: "kultur_fritid",
    scoring: "Gennemsnit af tre indikatorer: (1) Musikskoleelever pr. 1.000 indb. (SKOLM02B, direkte). (2) Biblioteksudlån pr. indb. (BIB1, direkte). (3) Kommunale kulturudgifter pr. indb. - nettodriftsudgifter til biografer, teatre, musikarrangementer og anden kultur (REGK31 funktion 33561-33564, direkte). Score 100 = landsgennemsnit.",
    boundary: "Socialt fundament: adgang til kulturliv og fritidsaktiviteter er en forudsætning for trivsel, social deltagelse og levende lokalsamfund.",
    dataYear: "2022-2024",
    limitations: "Musikskoleelever dækker primært børn og unge. Biblioteksudlån afspejler ikke digitale udlån fuldt ud. Kulturudgifter eksluderer biblioteksudgifter (separat indikator) og idrætsudgifter (separat indikator i Lokalsamfund). Idrætsmedlemskab indgår i Lokalsamfund som mål for foreningsliv og social kapital.",
    csvFile: "lokalsamfund_scores.csv + samskabelse_extra_scores.csv + doughnut_scores.csv (kultur_spending)",
  },
  tryghed: {
    id: "tryghed",
    scoring: "Gennemsnit af to indikatorer: (1) Anmeldte forbrydelser pr. 1.000 indb. (STRAF11, inverteret). (2) Trafikulykker - tilskadekomne og dræbte pr. 100.000 indb. (UHELDK1, inverteret). Score 100 = landsgennemsnit.",
    boundary: "Socialt fundament: borgere skal kunne leve trygt - i det offentlige rum og i trafikken.",
    dataYear: "2024",
    limitations: "Anmeldt kriminalitet afspejler ikke oplevet tryghed eller mørketallet. Politiets tilstedeværelse og anmeldelseskultur varierer. Trafikulykker varierer med vejnet og pendlingsforhold.",
    csvFile: "faellesskaber_scores.csv",
  },
  lokalsamfund: {
    id: "lokalsamfund",
    scoring: "Gennemsnit af fire indikatorer: (1) Idrætsfaciliteter pr. 10.000 indb. (IDRFAC01, direkte). (2) Kommunale idrætsudgifter pr. indb. (IDRFIN02, direkte). (3) Udgifter til frivillige foreninger pr. indb. (REGK31 funktion 33873, direkte). (4) Idrætsmedlemskab som andel af befolkningen (IDRAKT02, direkte - proxy for foreningsliv og social kapital). Score 100 = landsgennemsnit. NB: Klassekvotient, normering og pædagoguddannede er flyttet til dimensionen Uddannelse.",
    boundary: "Socialt fundament: nærhed til velfungerende basale services og levende foreningsliv er en forudsætning for et godt hverdagsliv - uanset om man bor i by eller på land.",
    dataYear: "2022-2024",
    limitations: "Dækker ikke alle relevante services (indkøb). Idrætsudgifter og idrætsfaciliteter kan korrelere. Udgifter til frivillige foreninger er en proxy for kommunens investering i civilsamfund, ikke for faktisk foreningsaktivitet. Idrætsmedlemskab dækker kun foreningsidræt, ikke selvorganiseret motion.",
    csvFile: "lokalsamfund_scores.csv + lokalsamfund_extra_scores.csv + faellesskaber_scores.csv",
  },
  lighed: {
    id: "lighed",
    scoring: "Gennemsnit af to indikatorer: (1) Gini-koefficient (IFOR41, inverteret - lavere ulighed er bedre). (2) Andel med indkomst under 60% af medianindkomsten (LABY07, inverteret). Score 100 = landsgennemsnit.",
    boundary: "Socialt fundament: en rimelig fordeling af ressourcer og muligheder er grundlaget for et sammenhængende samfund.",
    dataYear: "2022",
    limitations: "Begge indikatorer er fra DST og baseret på skatteregistre. Gini og lavindkomst er korrelerede mål - kommuner med høj ulighed har typisk også høj andel lavindkomst. Data er 2 år forsinket.",
    csvFile: "doughnut_scores.csv",
  },
  ligestilling: {
    id: "ligestilling",
    scoring: "1 indikator: Andel kvinder i lønmodtager-lederstillinger (RAS301 SOCIO=15, direkte ratio til landsgennemsnit). Score 100 = landsgennemsnit. Baseline er national andel (~36%), ikke 50%.",
    boundary: "Socialt fundament: lige muligheder uanset køn på arbejdsmarkedet og i ledelse.",
    dataYear: "2023",
    limitations: "Måler kun kønsdimensionen i ledelse - ikke løngab, branchefordeling eller andre ligestillingsmål. Andelen af kvinder i ledelse afhænger af kommunens erhvervsstruktur (fx industritunge kommuner har typisk færre kvinder i ledelse).",
    csvFile: "lighed_scores.csv",
  },
  mobilitet: {
    id: "mobilitet",
    scoring: "Gennemsnit af to indikatorer: (1) Gennemsnitlig pendlingsafstand i km (AFSTB4, inverteret). (2) Andel med god adgang til offentlig transport (LABY49, direkte - % med Meget højt + Højt serviceniveau). Score 100 = landsgennemsnit.",
    boundary: "Socialt fundament: adgang til mobilitet uanset geografi og økonomi - med vægt på bæredygtige transportformer.",
    dataYear: "2023-2025",
    limitations: "Pendlingsafstand fanger kun beskæftigedes transport. METODENOTE for offentlig transport (LABY49): data er KUN tilgængeligt på kommunegruppe-niveau (5 grupper) - alle kommuner i samme gruppe tildeles identisk score uanset lokale forskelle. Landkommuner (G5, herunder Thisted) scorer lavt som gruppe. Indikatoren er medtaget da retningen er korrekt og dataene er officielle DST-nøgletal. NB: Familier med bilrådighed (BIL800) er bevidst fjernet som scoring-indikator i 2026, da 'flere biler = bedre' er konceptuelt skævt i en doughnut/bæredygtighedsramme. Rådata er fortsat tilgængelig.",
    csvFile: "mobilitet_scores.csv",
  },
  klimatilpasning: {
    id: "klimatilpasning",
    scoring: "Ingen data endnu. Potentielle indikatorer: oversvømmelsesrisiko, klimatilpasningsplaner, grønne arealer til regnvandshåndtering.",
    limitations: "Afventer tilgængelige kommunefordelte data.",
  },
  energi: {
    id: "energi",
    scoring: "Scores på kommunens SAMLEDE fossile varmeafhængighed, mod et absolut mål på 0% (ikke landsgennemsnit). Samlet fossil% = direkte fossil opvarmning (andel af helårsboligernes opvarmede areal med oliefyr, oliekaminer eller naturgas, DST BYGB40) + fjernvarme-dækning% × fjernvarmens fossile brændselsandel (Energistyrelsens EPT). Score = 100 − samlet fossil%, så 100 = ingen fossil opvarmning og afstanden ned til 100 svarer til den fossile andel. Eksempel: 19% samlet fossil → score 81. Fritidsboliger, lokal VE-kapacitet og fjernvarmens fulde brændselsmix vises som kontekst, men indgår ikke i scoren - se Begrænsninger.",
    boundary: "Absolut mål: 0% fossil opvarmning (Niveau 2 - dansk politik om udfasning af olie- og gasfyr). Bemærk: fordi næsten alle kommuner har en vis fossil andel, når ingen kommune helt i grønt endnu - de bedste (fx Aarhus med biomasse-fjernvarme, ~4% fossil) ligger tæt på. Det er bevidst: målet er 0, ikke at være gennemsnitlig.",
    dataYear: "2026 (opvarmet areal, BYGB40), 2024 (fjernvarmemix), 2024 (VE-kapacitet)",
    limitations: "Kun fossil afhængighed indgår i scoren. (1) Lokal VE-kapacitet er bevidst holdt ude: en kommune kan have mange vindmøller OG mange oliefyr, og strømmen går til det nationale net - ikke til kommunens egne husstande. At gennemsnitte de to ville udvande scoren og antyde at vindmøller kompenserer for oliefyr. (2) Kun den FOSSILE del af fjernvarmen tælles med - biomasse og affald regnes hverken som grønt eller sort (det undgår det omdiskuterede værdivalg om biomasse). Fjernvarmens fulde mix vises som kontekst. (3) Fjernvarmens fossilandel stammer fra EPT, der opgøres ved produktionsstedet; for de 18 kommuner uden egen varmeproduktion (fx hovedstadskommuner på fælles net) bruges det TJ-vægtede landsgennemsnit (~13%). (4) Direkte fossil og fjernvarme-dækning er begge fra BYGB40 på arealbasis, så de er konsistente. (5) FRITIDSBOLIGER er bevidst holdt ude af scoren og vises kun som kontekst. Sommerhuse er typisk elopvarmede og har markant lavere fossilandel end helårsboliger (median ca. 7% mod ca. 20%). Hvis de indgik, ville sommerhuskommuner som Odsherred, Gribskov og Fanø fremstå kunstigt bedre på et mål der handler om HUSSTANDES varmeregninger - og sommerhusene ejes typisk af folk fra andre kommuner. (6) Erhvervs- og avlsbygninger, garager og udhuse indgår ikke: indikatoren måler boliger, ikke kommunens samlede bygningsmasse.",
    csvFile: "bolig_fossil_scores.csv + ve_kapacitet_scores.csv + fjernvarme_mix_scores.csv",
  },
};

const ECO_METHODS: Record<string, MethodInfo> = {
  klimapaavirkning: {
    id: "klimapaavirkning",
    scoring: "Worst-of af to indikatorer for samme klimagrænse: (1) Territoriale CO2e-udledninger pr. indbygger (udledninger inden for kommunens grænser, Klimaregnskabet.dk). (2) Forbrugsbaseret CO2e pr. indbygger (borgernes samlede aftryk inkl. importerede varer). For begge: ratio = (faktisk udledning / 3 ton) × 100; over 100 = overshoot. Dimensionens samlede score er den værste af de to - i praksis typisk den forbrugsbaserede, da danskeres forbrugsaftryk (ca. 10-17 ton) er markant større end det territoriale.",
    boundary: "3 ton CO2e pr. person pr. år (Paris-aftalens 1.5°C-budget). Gælder både territorialt og forbrugsbaseret. Til sammenligning er den gennemsnitlige danskers forbrugsbaserede aftryk ca. 10 ton - over tre gange budgettet.",
    boundarySources: [
      { label: "Fanning et al. (2022), Nature Sustainability", url: "https://www.nature.com/articles/s41893-021-00799-z" },
      { label: "Hot or Cool Institute (2021), 1.5-Degree Lifestyles", url: "https://hotorcool.org/1-5-degree-lifestyles-report/" },
      { label: "Energistyrelsen, Global Afrapportering", url: "https://ens.dk/" },
    ],
    dataYear: "2023 (territorial: ca. 70/98 kommuner; forbrugsbaseret: estimat for alle)",
    limitations: "Territorialt regnskab (Klimaregnskabet.dk) dækker ca. 70 af 98 kommuner og fanger ikke importerede udledninger. Forbrugsbaseret er et Tier 1-estimat: alle kommuner skaleres med samme nationale faktor (Osei-Owusu et al. 2020 nutidsjusteret med ENS GA25), så lokale ændringer siden 2011 er ikke indregnet (usikkerhed ca. ±10%). De to tal er ikke additive - det er to måder at opgøre samme klimapåvirkning.",
    csvFile: "climate_scores.csv + cba_2023_estimate.csv",
  },
  forurening: {
    id: "forurening",
    scoring: "Gennemsnit af fire indikatorer (ikke worst-of): (1) Pesticider: andel af aktive vandindvindingsboringer over drikkevandsnormen (0,1 µg/l) - ratio = (kommunens % / nationalt gennemsnit %) × 100. (2) Nitrat i drikkevand: ratio = (kommunalt gennemsnit mg/L / 6 mg/L) × 100. (3) Genanvendelse: ratio = (65% EU-mål / faktisk %) × 100 - over 100 = genanvender for lidt. (4) Affald: husholdningsaffald kg/person, inverteret ratio mod landsgennemsnit. Dimensionens score er det uvægtede gennemsnit af de fire.",
    boundary: "Pesticider: 0% over drikkevandsnormen (0,1 µg/l). Nitrat: 6 mg/L (ekspertgruppens anbefaling 2025). Genanvendelse: 65% (EU Affaldsdirektiv 2035). Affald: landsgennemsnit som reference.",
    dataYear: "2019-2025",
    limitations: "Pesticidata dækker 97/98 kommuner (Herlev mangler). Nitratdata er kun præcist for de 20 mest belastede kommuner - øvrige 78 estimeret til 3,7 mg/L. Reel genanvendelse kan afvige fra indsamlet til genanvendelse. Affald dækker kun husholdningsaffald. Dimensionen bruger gennemsnit, ikke worst-of, da de fire indikatorer adresserer vidt forskellig forureningskilder - en kommune kan excellere på affald men fejle på pesticider.",
    csvFile: "pesticider_scores.csv + nitrat_scores.csv + consumption_scores.csv + forurening_scores.csv",
  },
  luftkvalitet: {
    id: "luftkvalitet",
    scoring: "Worst-of af to indikatorer: (1) NO2-koncentration (kvælstofdioxid, µg/m³ årsgennemsnit) og (2) PM2.5-koncentration (fine partikler, µg/m³ årsgennemsnit). Begge sammenholdes med WHO's retningslinjer fra 2021. Ratio = (kommunens koncentration / WHO-grænse) × 100. Ratio over 100 = over WHO-grænsen. Dimensionens samlede score er den højeste (værste) af de to sub-indikatorer - planetary boundary-logik: hvis bare én grænse er overskredet, er dimensionen overskredet. Beregnet som befolkningsvægtet gennemsnit af 1×1 km modelceller inden for kommunegrænsen via spatial join.",
    boundary: "WHO 2021 Air Quality Guidelines (årsgennemsnit): NO2 = 10 µg/m³, PM2.5 = 5 µg/m³. WHO-grænsen er valgt frem for EU's grænseværdier (NO2: 40 µg/m³, PM2.5: 25 µg/m³) fordi WHO-grænsen er videnskabeligt baseret på sundhedseffekter, mens EU-grænsen er et politisk kompromis.",
    boundarySources: [
      { label: "WHO Air Quality Guidelines 2021", url: "https://www.who.int/publications/i/item/9789240034228" },
      { label: "DCE/AU - Luftkvalitet 2022 (SR580)", url: "https://dce2.au.dk/pub/SR580.pdf" },
      { label: "Miljøportal WFS - luftkoncentrationer", url: "https://arld-extgeo.miljoeportal.dk/geoserver/wfs" },
    ],
    dataYear: "2023",
    limitations: "Modelberegnet baggrundskoncentration (UBM, 1×1 km grid) - ikke målte værdier. Fanger ikke lokale hotspots ved travle gadestrækninger (OSPM-model dækker dette, men kun i store byer). Kommunegennemsnittet inkluderer landlige arealer med lav forurening, hvilket trækker byernes reelle eksponering ned. PM2.5 i Danmark er i høj grad påvirket af langtransport fra kontinentet og hav - ikke kun lokale kilder.",
    csvFile: "luftforurening_scores.csv",
  },
  naeringsstoffer: {
    id: "naeringsstoffer",
    scoring: "Worst-of af fire indikatorer - tre presmål og ét effektmål. Presmål: (1) Kvælstof-udledning (ton total-N) pr. 1.000 indbyggere via spildevand. (2) Fosfor-udledning (ton total-P) pr. 1.000 indbyggere via spildevand. (3) Landbrugets N-loft pr. ha landbrugsjord fra Vandområdeplan 3 (VP3): max bæredygtig N-tilførsel til kysten divideret med landbrugsarealet i oplandet - jo lavere N-loft pr. ha, jo mere N-presset er kommunen. Effektmål: (4) Andel af kommunens vandområder (vandløb, søer, kystvande) i mindst god økologisk tilstand (VP3) - den synlige eutrofiering de tre presmål forårsager; her er højere andel bedre, ratio = (landsgennemsnit / andel) × 100, cappet ved 300. Eco-konvention: score over 100 = mere belastet end landsgennemsnittet. Dimensionens samlede score er den værste af de fire sub-indikatorer (planetary boundary-logik).",
    boundary: "Landsgennemsnittet som reference for alle fire indikatorer. For vandområdernes tilstand er EU's Vandrammedirektiv-mål (alle vandområder i mindst god tilstand i 2027) vist som kontekst - nationalt opfylder kun ca. 6% målet. Lavere næringsstofbelastning og flere vandområder i god tilstand er bedre.",
    dataYear: "2024 (spildevand), 2025 (VP3 N-loft + økologisk tilstand), 2026 (markblokke)",
    limitations: "Spildevand dækker kun punktkilder (renseanlæg, dambrug, havbrug, industri, spredt bebyggelse). Landbrugs-N viser det maksimale tilladte N-loft pr. ha - ikke den faktiske udvaskning. Vandområdernes tilstand tælles pr. styk (ikke vægtet efter længde/areal); kystvande er næsten alle i dårlig tilstand pga. iltsvind, hvilket trækker kystkommuner ned. Grænseværdierne er landsgennemsnittet (relativ baseline), ikke absolutte planetære grænser.",
    csvFile: "naeringsstoffer_scores.csv + n_landbrug_scores.csv + vp3_vandkvalitet_scores.csv",
  },
  vand: {
    id: "vand",
    scoring: "Enkelt indikator: Vandindvinding fra almene vandværker (INDKAT=100) pr. person. Ratio = (kommunens m³/person / nationalt gennemsnit) × 100. Over 100 = bruger mere end landsgennemsnittet. Nitrat er flyttet til Forurening-dimensionen (kemisk forurening af drikkevand).",
    boundary: "Landsgennemsnit (72,9 m³/person, 2024) som reference. Den egentlige planetære grænse (Rockström/Steffen: 4.000-6.000 km³/år globalt) dækker alt konsumtivt blåt vandforbrug inkl. landbrug og er ikke direkte operationaliserbar på kommuneniveau med tilgængeligt data.",
    dataYear: "2024",
    limitations: "Data registreres ved vandværkets fysiske placering, ikke ved forbrugsstedet. Bykommuner der forsynes af vandværker beliggende i nabokommuner (fx HOFOR for storkøbenhavn) får kunstigt lave tal og er filtreret fra (6 kommuner uden data). Dækker kun almene vandværker - industri og markvanding er ikke inkluderet.",
    csvFile: "vandindvinding_scores.csv",
  },
  arealanvendelse: {
    id: "arealanvendelse",
    scoring: "To sub-indikatorer med worst-of logik (dimensionsscoren = den højeste ratio): (1) Andel intensivt landbrug (korn, rodfrugter, permanente afgrøder, ikke-klassificeret - DST kategorier D1+D2+D4): ratio = (andel / 54,7%) × 100 mod nationalt gennemsnit 2024. (2) Andel bebygget og befæstet areal (veje, jernbaner, lufthavne, bebyggelse, råstofgrave - A1+A2+B1+B2+C1): ratio = (andel / 14,2%) × 100 mod nationalt gennemsnit 2024. Naturkvalitet måles separat i biodiversitetsdimensionen (DCE bioscore).",
    boundary: "Nationalt gennemsnit 2024 som reference: intensivt landbrug ~54,7%, bebygget og befæstet ~14,2% (DST AREALDK2). Over gennemsnittet = over grænsen. Til kontekst: CONCITO-rapportens planetære grænse for arealsystemet er max 15% antropiseret areal (landbrug + bebygget tilsammen, Rockström 2009). Danmark ligger på 73-75% - en femdobbelt overskridelse. Vi scorer bevidst mod landsgennemsnittet i stedet for de 15%, så man kan se forskel mellem kommuner; ellers ville næsten alle lyse dybrødt.",
    dataYear: "2024",
    limitations: "Begge indikatorer er målt mod nationalt gennemsnit (niveau 3 baseline), ikke absolutte planetære grænser. Bykommuner scorer typisk dårligt på bebygget men godt på landbrug - og omvendt for landkommuner. Det er bevidst: worst-of logikken fanger det dominerende pres for den enkelte kommunes arealtype. Dimensionen dækker ikke naturkvalitet (se biodiversitet) eller fragmentering af levesteder.",
    csvFile: "arealanvendelse_scores.csv",
  },
  biodiversitet: {
    id: "biodiversitet",
    scoring: "Worst-of af to tærskler fra DCE's biodiversitetskort (bioscore-raster, 10x10 m). Bioscore vurderer hvor værdifuldt hvert areal er som levested for truede arter. (1) Andel af kommunen med væsentlig naturværdi (bioscore ≥8): ratio = (30% / faktisk andel) × 100 mod EU's 30%-mål. (2) Andel med uerstattelig naturværdi (bioscore ≥12): ratio = (10% / faktisk andel) × 100 mod 10%-målet for strengt beskyttet natur. Over 100 = under målet (for lidt). Dimensionsscoren er den dårligste (højeste ratio) af de to. I modsætning til rent arealdække vægter bioscore naturkvalitet - en biologisk fattig plantage tæller derfor lavt.",
    boundary: "30% væsentlig naturværdi + 10% uerstattelig naturværdi (EU Biodiversitetsstrategi 2030, 30x30-målet). VIGTIGT: Dette er EU's politiske mål, ikke den planetære grænse. CONCITO-rapporten (2025) vurderer Danmarks samlede biodiversitet til et Biodiversity Intactness Index på 44% mod en sikker planetær grænse på 90%. En kommune kan altså nå 30%-målet og lyse grønt uden at være inden for den biofysiske grænse.",
    dataYear: "2021",
    limitations: "Grænserne er politiske mål (30%/10%), ikke den planetære grænse. Den planetære BII-grænse (44% for DK) er et groft globalt modelestimat (0,25° opløsning, usikkerhed 41-61%) og kan ikke beregnes meningsfuldt per kommune - derfor bruges det lokalt forankrede danske bioscore-kort i stedet. Bioscore måler habitatkvalitet, ikke fredningsstatus: et areal kan have høj naturværdi uden at være beskyttet, og omvendt.",
    csvFile: "biodiversitet_scores.csv (DCE Biodiversitetskort, bioscore-raster 2021)",
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

        {/* MVP / prototype-banner */}
        <div className="p-4 bg-amber-50 border-2 border-amber-300 rounded-xl mb-4">
          <div className="flex items-start gap-3">
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-200 text-amber-900 uppercase whitespace-nowrap mt-0.5">
              MVP / prototype
            </span>
            <div className="text-sm text-amber-900 leading-relaxed">
              <p className="font-semibold mb-1">Platformen er under udvikling.</p>
              <p>
                Danmarks 98 Doughnuts er en prototype - en første version til at afprøve, om Doughnut Economics-rammen kan bruges
                til alle danske kommuner. Indikatorvalg, grænseværdier, beregningslogik og datadækning er stadig under udvikling og
                kan ændre sig. Tal og scores skal læses som indikative pejlemærker, ikke som autoritativ måling. Feedback og kritik
                er velkommen - se kontakt nederst.
              </p>
            </div>
          </div>
        </div>

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
          Det betyder at kategorier med få indikatorer (f.eks. Bolig med 3) vægter lige så tungt som kategorier med mange (f.eks. Velfærd med 6).
          Dette er et bevidst valg: hver dimension i doughnut-modellen anses for lige vigtig, uanset hvor mange indikatorer der måler den.
        </p>
        <p className="text-sm text-gray-700 leading-relaxed mt-2">
          <strong>Inverterede indikatorer:</strong> For indikatorer hvor lavere er bedre (f.eks. kriminalitet, affald, børnefattigdom)
          beregnes ratioen inverteret: (landsgennemsnit / kommune) × 100, så højere ratio fortsat betyder bedre performance.
          Kommuner med en værdi på 0 (typisk manglende data eller ingen registreret aktivitet) sættes til ratio 0, ikke perfekt score - dette er for at undgå at databrist
          fejlagtigt fremstår som topscore. For multi-indikator økologiske dimensioner (luftkvalitet, næringsstoffer, forurening) bruges en specialregel: ratio 150 anvendes
          som loft for sub-indikatorer hvor data mangler eller hvor ingen aktivitet registreres (f.eks. kommuner uden markblokke i N-loft-beregningen).
        </p>
      </section>

      {/* Ærlig note: absolutte vs relative grænser */}
      <section className="mb-10 p-5 bg-blue-50 border border-blue-200 rounded-xl">
        <h3 className="text-base font-semibold text-gray-900 mb-2">Om grænserne i det økologiske loft</h3>
        <p className="text-sm text-gray-700 leading-relaxed">
          Nogle dimensioner måles mod absolutte grænser (WHO&apos;s luftgrænser, EU&apos;s genanvendelsesmål, drikkevandsnormen for pesticider). Andre måles mod landsgennemsnittet, fordi der ikke findes en meningsfuld absolut grænse på kommuneniveau. Det betyder at en grøn score på en relativ dimension viser &quot;bedre end de fleste danske kommuner&quot; - ikke nødvendigvis &quot;inden for planetens grænser&quot;. Danmark som helhed overskrider de fleste planetære grænser markant.
        </p>
        <p className="text-sm text-gray-700 leading-relaxed mt-2">
          Læs mere om hvordan de planetære grænser ser ud for Danmark, og hvad der bevidst ikke kan måles på kommuneniveau, i{" "}
          <a href="/artikel/planetaere-graenser" className="text-blue-600 hover:underline font-medium">
            artiklen om planetære grænser
          </a>.
        </p>
        <p className="text-sm text-gray-700 leading-relaxed mt-2">
          Hver dimension er mærket efter hvad den måles imod: <strong>mod mål</strong> (en fast absolut grænse - WHO, EU-mål, drikkevandsnorm, 0 % fossil, 95 %-uddannelsesmål) eller <strong>mod landsgennemsnit</strong> (umærket - relativ til de øvrige kommuner). Et par dimensioner er <strong>blandet</strong>. På en &quot;mod mål&quot;-dimension betyder grøn &quot;inden for grænsen&quot;; på en relativ betyder grøn &quot;bedre end de fleste kommuner&quot;.
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
