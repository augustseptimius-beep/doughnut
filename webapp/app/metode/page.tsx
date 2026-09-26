import type { Metadata } from "next";
import { SOCIAL_CATEGORIES, INDICATORS, ECOLOGICAL_DIMENSIONS, INDICATOR_RATIONALES, dimensionCsvFiles, udfyldTal } from "@/lib/shared";
import { getDimensionDataYears } from "@/lib/data";

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
  // Intet dataYear-felt: "Datatidspunkt" beregnes af getDimensionDataYears()
  // fra master-CSV'ens egen data_year-kolonne. Et hårdkodet felt her drev
  // gentagne gange fra den faktiske hentning (sep. 2026, ca. 20 forkerte
  // dataYear-strenge på tværs af kategorier og dimensioner).
  limitations?: string;
  // Intet csvFile-felt: datafilerne udledes af registret (dimensionCsvFiles).
}

/* Begrundelsen pr. indikator (INDICATOR_RATIONALES) står i data/indikatorer.json
   ("rationale"), så en ny indikator er én post dér. */

const SOCIAL_METHODS: Record<string, MethodInfo> = {
  sundhed: {
    id: "sundhed",
    scoring: "Gennemsnit af ni indikatorer. Helbredstilstand: (1) Andel med godt selvvurderet helbred (Den Nationale Sundhedsprofil 2025, direkte). (2) Andel med lav score på den mentale helbredsskala (Sundhedsprofilen 2025, inverteret). (3) Middellevetid for 0-årige (HISBK, direkte). (4) Andel med indlæggelse 12 timer eller derover (SBR01, inverteret). (5) Hjemmesygepleje-modtagere pr. 1.000 indb. (HJEMSYG, inverteret). Levevaner, alle fra Sundhedsprofilen 2025 og alle inverterede: (6) Andel der ryger dagligt. (7) Andel der drikker over 10 genstande om ugen. (8) Andel med lav score på kostskalaen. (9) Andel med svær overvægt, BMI 30+. Score 100 = landsgennemsnit.",
    boundary: "Socialt fundament: alle borgere bør opleve deres eget fysiske og mentale helbred som mindst på niveau med landsgennemsnittet, have en forventet levetid der matcher det, og ikke være mere udsat for de påvirkelige risikofaktorer end danskere i øvrigt.",
    limitations: "Seks af de ni indikatorer er selvrapporterede og kommer fra samme spørgeskemaundersøgelse, som gennemføres hvert fjerde år. Kommunetallene står derfor fast indtil næste bølge, og en fejl i kilden ville slå igennem på to tredjedele af kategorien på én gang. Stikprøven er designet til kommuneniveau (314.500 udsendte skemaer i 2025), men er tyndest i de mindste ø-kommuner. Landsgennemsnittet er beregnet som et befolkningsvægtet gennemsnit af de 98 kommuneandele, ikke SIF's eget vægtede landsestimat, og afviger derfor en anelse fra den nationale rapport. Der er en kendt underrapportering af både alkoholforbrug og vægt i surveydata. Alkohol peger modsat de øvrige levevaner: forbruget er højest i velstillede kommuner, hvor rygning og overvægt er lavest, så en kommune med lavt rygeniveau og højt alkoholforbrug lander midt i feltet. Middellevetid varierer kun godt tre point mellem kommunerne og differentierer derfor svagt. Sygehusbenyttelse kan afspejle både dårligt helbred og god adgang. Hjemmesygepleje følger alderssammensætningen lige så meget som sundheden og er kategoriens svageste indikator. Fysisk aktivitet hentes fra samme kilde, men indgår ikke: den korrelerer 0,90 med svær overvægt og 0,80 med kostskalaen og ville lade den samme underliggende konstruktion fylde tre af ni pladser.",
  },
  uddannelse: {
    id: "uddannelse",
    scoring: "Gennemsnit af ni indikatorer: (1) Andel af 30-34-årige med kompetencegivende uddannelse (HFUDD11, scoret absolut mod det nationale 95 %-mål: ratio = andel/95 × 100). (2) Andel af 25-29-årige med kun grundskole (HFUDD11, inverteret). (3) Karaktergennemsnit folkeskolens afgangseksamen (UVM GS/KARA/KARAGNS, direkte). (4) Andel elever med >10% fravær (UVM GS/ELEVFRAV/FRAVAAR, inverteret). (5) Forventet ungdomsuddannelseskompetence (UVM GS/PROFMOD/PROFMOD, direkte). (6) Elevtrivsel i folkeskolen, gennemsnit (UVM GS/TRIV/TRIVIND, direkte). (7) Klassekvotient grundskole (KVOTIEN, inverteret). (8) Normering daginstitution 3-5 år (BOERN8, inverteret). (9) Andel pædagoguddannede i daginstitutioner (BOERN1 kode 460, direkte). Score 100 = landsgennemsnit (undtagen indikator 1, der scores mod 95 %-målet - derfor er kategorien 'blandet').",
    boundary: "Socialt fundament: alle borgere bør have adgang til uddannelse og et kvalitetsfuldt læringsmiljø. EU-mål: 45% af 25-34-årige med videregående uddannelse i 2030.",
    limitations: "Karaktergennemsnit afspejler ikke kun skolekvalitet men også socioøkonomisk baggrund. Klassekvotienter og normering fanger kvantitative mål, ikke undervisningskvalitet. UVM-data dækker skoleår 2023/2024 som seneste.",
  },
  velfaerd: {
    id: "velfaerd",
    scoring: "Gennemsnit af syv indikatorer: median disponibel indkomst (INDKP106), beskæftigelsesfrekvens (RAS200), børnefattigdom (inverteret, LABY07), udsatte børn og unge (inverteret, BU43), NEET (inverteret, NEET3), relativ fattigdom (inverteret, IFOR12P) og underretninger om børn (inverteret, UND2). Score 100 = landsgennemsnit. NB: Gini er flyttet til Lighed. Andelen med lavindkomst (LABY07, alle aldre) er fjernet i sep. 2026, fordi den var næsten samme tal som børnefattigdom fra samme tabel (korrelation 0,87).",
    boundary: "Socialt fundament: materielle levevilkår der sikrer værdigt liv for alle. Ingen absolut grænse - relativ til landsgennemsnit.",
    limitations: "Børnefattigdom (LABY07) og relativ fattigdom (IFOR12P) overlapper. Disponibel indkomst justerer ikke for købekraft mellem kommuner. DST udgiver ikke medianen pr. kommune; den er beregnet ud fra antal personer i DST's indkomstintervaller (INDKP106) med en usikkerhed på typisk under 1.000 kr. BU43 og NEET dækker forskellige aldersgrupper (0-22 og 16-24).",
  },
  bolig: {
    id: "bolig",
    scoring: "Enkelt indikator: andelen af beboerne i helårsboliger (parcel-, række- og etageboliger), der bor i en bolig med flere personer end værelser (BOL103, inverteret). Beregnet af platformen ud fra DST's opgørelse af boliger efter antal værelser og husstandsstørrelse. Score 100 = landsgennemsnit ({ref:trangboethed:1}% for Danmark som helhed). NB: Fossil opvarmning er flyttet til dimensionen Energi, da opvarmningskilde er et energispørgsmål, ikke boligstandard.",
    boundary: "Socialt fundament: alle borgere bør have en bolig med plads nok til husstanden.",
    limitations: "Definitionen, flere personer end værelser, er en forenkling af Eurostats overbelægningsmål, der tager højde for husstandens alder og sammensætning; de oplysninger findes ikke pr. kommune. Et par i en etværelseslejlighed tæller derfor som trangboet. Husstande på 7 personer eller flere tælles som 7, og boliger med 6 værelser eller flere som 6. Trangboethed er størst i hovedstadens omegn og mindst på øerne og i landkommunerne, og mange land- og økommuner står på loftet på 150 med landsgennemsnittet som sammenligning. Boligudgifter og hjemløshed indgår ikke, fordi der ikke er fundet kommunetal, der kan bruges; DST opgør boligbyrden kun på landsplan. Kategorien har kun én indikator og er derfor følsom over for fejl i den ene kilde. Indtil september 2026 bestod den af ubeboede boliger (BOL101) og boligareal pr. person (BOL106). De to korrelerede -0,85: landkommuner blev straffet for tomme boliger og belønnet for plads, så kategorien udlignede sig selv. Boligareal belønnede desuden jo mere plads, jo bedre, hvor trangboethed kun måler, om der er for lidt.",
  },

  demokrati: {
    id: "demokrati",
    scoring: "Gennemsnit af 2 indikatorer: (1) Stemmedeltagelse ved kommunalvalget 2025 (LABY08, direkte ratio til landsgennemsnit). (2) Stemmedeltagelse ved folketingsvalget 2026 (LABY09, direkte ratio til landsgennemsnit). Score 100 = landsgennemsnit. NB: Kønsbalance i ledelse er flyttet til dimensionen Ligestilling.",
    boundary: "Socialt fundament: aktivt demokratisk medborgerskab. Alle borgere bør have mulighed for og lyst til at deltage i den demokratiske proces.",
    limitations: "Måler kun formel valgdeltagelse - ikke bredere politisk deltagelse som borgermøder, lokalt engagement eller civilsamfundsaktivitet. Valgdeltagelse varierer strukturelt: højere i kommuner med velstillet, ældre befolkning. Kommunalvalg opdateres hvert 4. år; folketingsvalg efter behov.",
  },
  kultur_fritid: {
    id: "kultur_fritid",
    scoring: "Gennemsnit af tre indikatorer: (1) Musikskoleelever pr. 1.000 indb. (SKOLM02B, direkte). (2) Biblioteksudlån pr. indb. (BIB3A, direkte). (3) Kommunale kulturudgifter pr. indb. - nettodriftsudgifter til biografer, teatre, musikarrangementer og anden kultur (REGK31 funktion 33561-33564, direkte). Score 100 = landsgennemsnit.",
    boundary: "Socialt fundament: adgang til kulturliv og fritidsaktiviteter er en forudsætning for trivsel, social deltagelse og levende lokalsamfund.",
    limitations: "Musikskoleelever dækker primært børn og unge. Biblioteksudlån afspejler ikke digitale udlån fuldt ud. Kulturudgifterne omfatter ikke biblioteker og idræt: biblioteker indgår via udlån, og idrætsmedlemskab indgår i Fællesskab.",
  },
  tryghed: {
    id: "tryghed",
    scoring: "Gennemsnit af to indikatorer: (1) Anmeldte forbrydelser pr. 1.000 indb. (STRAF11, inverteret). (2) Trafikulykker - tilskadekomne og dræbte pr. 100.000 indb., treårigt gennemsnit (UHELDK1, inverteret). Score 100 = landsgennemsnit.",
    boundary: "Socialt fundament: borgere skal kunne leve trygt - i det offentlige rum og i trafikken.",
    limitations: "Anmeldt kriminalitet afspejler ikke oplevet tryghed eller mørketallet. Politiets tilstedeværelse og anmeldelseskultur varierer, og kriminalitetsscoren rammer 150-loftet i en stor del af de tyndt befolkede kommuner, så den kan ikke skelne mellem dem. Trafikulykker varierer med vejnet og pendlingsforhold og opgøres fra sep. 2026 som et treårigt gennemsnit, fordi ét års tal i de mindste kommuner hviler på en håndfuld personer. Selv med tre år er grundlaget i ø-kommunerne tyndt.",
  },
  lokalsamfund: {
    id: "lokalsamfund",
    scoring: "Gennemsnit af op til fem indikatorer: (1) Andel med tegn på ensomhed (Den Nationale Sundhedsprofil 2025, inverteret). (2) Andel der aldrig eller næsten aldrig har nogen at tale med ved problemer (Sundhedsprofilen 2025, inverteret). (3) Idrætsmedlemskab som andel af befolkningen (IDRAKT02, direkte). (4) Andel der har overværet en sportsbegivenhed som tilskuer (KV2GEO, toårigt gennemsnit 2024-2025, direkte). (5) Udgifter til frivillige foreninger pr. indb. (REGK31 funktion 33873, direkte). Score 100 = landsgennemsnit. Indikator 4 findes kun for {daekning:sport_tilskuer} af {kommuner} kommuner; de øvrige {mangler:sport_tilskuer} får kategoriscoren beregnet på fire indikatorer.",
    boundary: "Socialt fundament: ingen bør stå uden for fællesskabet. Ensomhed og manglende social støtte er kategoriens grænser; deltagelse og foreningsstøtte beskriver det der skal til for at holde folk inde i fællesskabet.",
    limitations: "Kategorien hed indtil sep. 2026 Foreningsliv og bestod udelukkende af kommunale udgifter og faciliteter, altså input. Den havde ingen indbyrdes sammenhæng: idrætsfaciliteter pr. indbygger korrelerede -0,35 med idrætsudgifter og -0,32 med foreningsstøtte, så gennemsnittet af de fire udlignede hinanden frem for at måle noget. Idrætsfaciliteter og idrætsudgifter er derfor taget ud, og to udfaldsmål samt et deltagelsesmål er kommet ind. Tilskuerindikatoren mangler for {mangler:sport_tilskuer} kommuner, fordi DST's stikprøve i kulturvaneundersøgelsen er for lille til at offentliggøre et tal. De manglende kommuner er ikke tilfældigt fordelt: deres median er ca. 24.000 indbyggere mod ca. 53.000 for dem med tal, og blandt dem er Læsø, Fanø, Samsø, Ærø og Langeland. Konsekvensen er dobbelt. Dels sammenlignes de {mangler:sport_tilskuer} kommuner på et andet indikatorgrundlag end de øvrige {daekning:sport_tilskuer}. Dels er det netop de små kommuner, hvor et lokalt idrætsfællesskab kan fylde mest i hverdagen, der ikke kan måles på det. Vi viser indikatoren alligevel, fordi alternativet var intet deltagelsesmål overhovedet, men forskellen skal læses med. Tilskuerindikatoren har ingen retningspil: tabellen findes kun for 2024 og 2025, og begge år indgår i gennemsnittet. Ensomhed og social støtte er selvrapporterede og opdateres hvert fjerde år. Idrætsmedlemskab dækker kun foreningsidræt, ikke selvorganiseret motion. Foreningsstøtten måler kommunens prioritering, ikke resultatet af den.",
  },
  lighed: {
    id: "lighed",
    scoring: "Gennemsnit af to indikatorer: (1) Gini-koefficient (IFOR41, inverteret - lavere ulighed er bedre). (2) Beskæftigelsesfrekvensen for indvandrere fra ikke-vestlige lande i procent af frekvensen for personer med dansk oprindelse, 16-64 år (RAS200, direkte). Score 100 = landsgennemsnit.",
    boundary: "Socialt fundament: en rimelig fordeling af ressourcer og muligheder er grundlaget for et sammenhængende samfund.",
    limitations: "Kategorien måler fordelingen, ikke fattigdomsniveauet, som indgår i Velfærd. Indtil sep. 2026 indgik også andelen med lavindkomst (LABY07), men den var næsten samme tal som børnefattigdom under Velfærd (korrelation 0,87), så fattigdom talte to gange. De to tilbageværende indikatorer måler forskellige sider af ulighed og hænger næsten ikke sammen (korrelation 0,09), så hver af dem bestemmer halvdelen af kategorien. Gini afspejler både lave og meget høje indkomster, og velstående forstadskommuner har typisk en høj Gini. I kommuner med få indvandrere fra ikke-vestlige lande bygger beskæftigelsesgabet på få personer. Indkomstdata er 2 år forsinket.",
  },
  ligestilling: {
    id: "ligestilling",
    scoring: "Gennemsnit af tre indikatorer: (1) Andel kvinder i lønmodtager-lederstillinger (RAS301 SOCIO=15, direkte). (2) Kønsgab i middellevetid, kvinder minus mænd i år (HISBK, inverteret - mindre gab er bedre). (3) Kvinders median disponible indkomst i procent af mænds (INDKP106, direkte). Score 100 = landsgennemsnit. For lederandelen er baseline den nationale andel (ca. {ref:gender_leadership:0}%), ikke 50%.",
    boundary: "Socialt fundament: lige muligheder uanset køn på arbejdsmarkedet og i ledelse.",
    limitations: "Indkomstindikatoren bruger medianen, så enkelte meget høje indkomster ikke flytter tallet. DST udgiver ikke medianen pr. kommune og køn; den er beregnet ud fra antal personer i DST's indkomstintervaller (INDKP106), og usikkerheden på kønsforholdet er typisk under 1 procentpoint. Andelen af kvinder i ledelse afhænger af kommunens erhvervsstruktur (fx industritunge kommuner har typisk færre kvinder i ledelse).",
  },
  mobilitet: {
    id: "mobilitet",
    scoring: "Gennemsnit af to indikatorer: (1) Gennemsnitlig pendlingsafstand i km (AFSTB4, inverteret). (2) Andel af befolkningen med god adgang til offentlig transport (direkte): bopælen ligger højst 500 m gang fra stoppesteder med tilsammen mindst 10 afgange i timen på en typisk hverdag kl. 6-20. Det svarer til DST's serviceniveau højt og meget højt (verdensmål 11.2.1). DST udgiver kun tallet for fem kommunegrupper, så platformen beregner det pr. kommune med DST's metode ud fra køreplaner fra Rejseplanen GTFS, adresser fra Danmarks Adresseregister og Eurostats befolkningsgrid fra folketællingen 2021. Score 100 = landsgennemsnit (Danmark som helhed; for offentlig transport har {ref:public_transport:1}% af befolkningen god adgang).",
    boundary: "Socialt fundament: adgang til mobilitet uanset geografi og økonomi - med vægt på bæredygtige transportformer.",
    limitations: "Pendlingsafstand fanger kun beskæftigedes transport. Offentlig transport beregnes af platformen, fordi DST's egen opgørelse (LABY49) kun findes for fem kommunegrupper. Indtil september 2026 fik alle kommuner i en gruppe derfor samme tal. Beregningen følger DST's metode så tæt, som åbne data tillader. Afgangene tælles fra Rejseplanens køreplaner for én typisk hverdag uden for ferier; flextrafik og telebusser tæller ikke med. Afgange fra alle stoppesteder inden for gåafstand lægges sammen, så en bus tæller ved hvert stop, den kører forbi. DST måler 500 m ad vejnettet, mens platformen bruger 340 m i fugleflugt, kalibreret på andelen af befolkningen uden stoppested i gåafstand. Befolkningen fordeles på adresser med Eurostats 1 km-grid fra folketællingen 2021, så sommerhus- og erhvervsområder vejer lidt. Lagt sammen til de fem kommunegrupper rammer tallene DST's med ca. 1 procentpoint i gennemsnit. Hovedstadsområdet ligger lidt over DST og landkommunerne lidt under, sandsynligvis fordi omvejen ad vejnettet er større i byer end på landet. Tærsklen på 10 afgange i timen er platformens valg blandt DST's fem serviceniveauer: DST har vist, at andelen af familier med bil stiger mest, når betjeningen falder under 10 afgange i timen. I landkommuner, hvor få bor så tæt på en travl rute, kan ændringer på en enkelt buslinje i en bymidte flytte scoren mærkbart, og kommuner uden sådanne ruter får 0. Indikatoren har endnu ingen retningspil, fordi Rejseplanens køreplanarkiv først går tilbage til december 2025. Indeholder kollektivtrafikdata fra Rejseplanen (CC BY 4.0) og befolkningsdata fra Eurostat (© EU). Metode og validering: docs/offentlig-transport-genskabt.md. NB: Familier med bilrådighed (BIL800) er bevidst fjernet som scoring-indikator i 2026, da 'flere biler = bedre' er konceptuelt skævt i en doughnut/bæredygtighedsramme. Rådata er fortsat tilgængelig.",
  },
  klimatilpasning: {
    id: "klimatilpasning",
    scoring: "Gennemsnit af to indikatorer: (1) Vejrrelaterede forsikringsskader pr. 1.000 indbyggere (F&P skadesstatistik, akkumuleret Q1 2023 - Q4 2025, inverteret - færre skader er bedre). (2) Forventet årlig skade fra oversvømmelse fra havet og kysterosion i 2070 i kr. pr. indbygger (Kystdirektoratets Kystplanlægger, inverteret - lavere risiko er bedre). Ratio = (landsgennemsnit / kommunens værdi) × 100. Score 100 = landsgennemsnit (landet som helhed: for forsikringsskaderne kommunernes tal vægtet med indbyggertallet, for kystrisikoen {ref:kystrisiko:0} kr. pr. indbygger om året). Kystrisikoen tæller højst 100: en kommune uden eller med lav kystrisiko står neutralt i stedet for at få en fordel, så fraværet af en kyst ikke kan udligne vejrskader.",
    boundary: "Socialt fundament: borgere og bygninger skal være robuste over for klimarelateret ekstremvejr (skybrud, storm, oversvømmelse). Ingen absolut grænse - relativ til landsgennemsnit.",
    limitations: "Kategorien måler restrisiko: hvor udsat kommunen er, når det der allerede er gjort, er regnet med. Forsikringsskaderne fanger realiserede skader fra storm, skybrud, hagl og frost, men ikke stormflod, og påvirkes af bygningsmasse, forsikringsdækning og tilfældige vejrhændelser i perioden. Kystrisikoen er Kystdirektoratets modelberegning (datapakke fra 2021) med havstigning efter klimascenariet RCP8.5. Kun faren er fremskrevet til 2070; bygninger og værdier er dagens. Diger og klitter i Danmarks Højdemodel 2014-2015 er regnet med, men anden kystbeskyttelse som udgangspunkt ikke, og nye tiltag slår først igennem, når Kystdirektoratet opdaterer kortlægningen. Kystrisikoen har derfor ingen retningspil. Skybrud, vandløb og højtstående grundvand indgår kun gennem forsikringsskaderne. Se data/klimatilpasning.md for metodediskussion.",
  },
  energi: {
    id: "energi",
    scoring: "Scores på kommunens SAMLEDE fossile varmeafhængighed, mod et absolut mål på 0% (ikke landsgennemsnit). Samlet fossil% = direkte fossil opvarmning (andel af helårsboligernes opvarmede areal med oliefyr, oliekaminer eller naturgas, DST BYGB40) + fjernvarme-dækning% × fjernvarmens fossile brændselsandel (Energistyrelsens EPT). Score = 100 − samlet fossil%, så 100 = ingen fossil opvarmning og afstanden ned til 100 svarer til den fossile andel. Eksempel: 19% samlet fossil → score 81. Fritidsboliger, lokal VE-kapacitet og fjernvarmens fulde brændselsmix vises som kontekst, men indgår ikke i scoren - se Begrænsninger.",
    boundary: "Absolut mål: 0% fossil opvarmning (Niveau 2 - dansk politik om udfasning af olie- og gasfyr). Bemærk: fordi næsten alle kommuner har en vis fossil andel, når ingen kommune helt i grønt endnu - de bedste (fx Aarhus med biomasse-fjernvarme, ~4% fossil) ligger tæt på. Det er bevidst: målet er 0, ikke at være gennemsnitlig.",
    limitations: "Datagrundlaget har forskellig alder: opvarmet areal (BYGB40) er fra 2026, fjernvarmemix og VE-kapacitet fra 2024. Kun fossil afhængighed indgår i scoren. (1) Lokal VE-kapacitet er bevidst holdt ude: en kommune kan have mange vindmøller OG mange oliefyr, og strømmen går til det nationale net - ikke til kommunens egne husstande. At gennemsnitte de to ville udvande scoren og antyde at vindmøller kompenserer for oliefyr. (2) Kun den FOSSILE del af fjernvarmen tælles med - biomasse og affald regnes hverken som grønt eller sort (det undgår det omdiskuterede værdivalg om biomasse). Fjernvarmens fulde mix vises som kontekst. (3) Fjernvarmens fossilandel stammer fra EPT, der opgøres ved produktionsstedet; for de 18 kommuner uden egen varmeproduktion (fx hovedstadskommuner på fælles net) bruges det TJ-vægtede landsgennemsnit (~13%). (4) Direkte fossil og fjernvarme-dækning er begge fra BYGB40 på arealbasis, så de er konsistente. (5) FRITIDSBOLIGER er bevidst holdt ude af scoren og vises kun som kontekst. Sommerhuse er typisk elopvarmede og har markant lavere fossilandel end helårsboliger (median ca. 7% mod ca. 20%). Hvis de indgik, ville sommerhuskommuner som Odsherred, Gribskov og Fanø fremstå kunstigt bedre på et mål der handler om HUSSTANDES varmeregninger - og sommerhusene ejes typisk af folk fra andre kommuner. (6) Erhvervs- og avlsbygninger, garager og udhuse indgår ikke: indikatoren måler boliger, ikke kommunens samlede bygningsmasse.",
  },
};

const ECO_METHODS: Record<string, MethodInfo> = {
  klimapaavirkning: {
    id: "klimapaavirkning",
    scoring: "Worst-of af to indikatorer for samme klimagrænse: (1) Territoriale CO2e-udledninger pr. indbygger (udledninger inden for kommunens grænser, Klimaregnskabet.dk). (2) Forbrugsbaseret CO2e pr. indbygger (borgernes samlede aftryk inkl. importerede varer). For begge: ratio = (faktisk udledning / 2,5 ton) × 100; over 100 = overshoot. Dimensionens samlede score er den værste af de to - i praksis typisk den forbrugsbaserede, da danskeres forbrugsaftryk (ca. 9-17 ton) er markant større end det territoriale.",
    boundary: "2,5 ton CO2e pr. person pr. år: det aftryk pr. person, som et 1,5-graders-forløb kræver i 2030, udledt af 1,5-gradersforløbene og fordelt ligeligt pr. indbygger (Hot or Cool Institute 2021, der angiver 1,4 ton i 2040 og 0,7 ton i 2050). Gælder både territorialt og forbrugsbaseret. Til sammenligning er den gennemsnitlige danskers forbrugsbaserede aftryk ca. 9,7 ton (Energistyrelsen, 2024) - næsten fire gange grænsen. Indtil september 2026 brugte platformen 3 ton, som ingen af de angivne kilder underbyggede.",
    boundarySources: [
      { label: "Hot or Cool Institute (2021), 1.5-Degree Lifestyles", url: "https://hotorcool.org/1-5-degree-lifestyles-report/" },
      { label: "Energistyrelsen, Global Afrapportering (forbrugsbaseret klimaaftryk)", url: "https://ens.dk/analyser-og-statistik/danmarks-globale-klimapaavirkning-global-afrapportering" },
      { label: "CONCITO (2025), Downscaling the planetary boundaries to national level", url: "https://concito.dk/en/udgivelser/downscaling-the-planetary-boundaries-to-national-level-the-case-of-denmark" },
    ],
    limitations: "Territorialt regnskab (Klimaregnskabet.dk, alle 98 kommuner) fanger ikke importerede udledninger. Forbrugsbaseret er et Tier 1-estimat: kommunernes aftryk i 2011 fra Osei-Owusu et al. (2020), ganget med Energistyrelsens nationale udvikling pr. indbygger fra 2011 til {aar:forbrug_co2} (Global Afrapportering, hentet direkte). Alle kommuner skaleres med samme faktor, så lokale ændringer siden 2011 er ikke med. Målet på 2,5 ton er udledt for husholdningernes forbrug; det forbrugsbaserede tal omfatter også offentligt forbrug og investeringer, og det territoriale også produktion til eksport. Grænsen er derfor et fælles niveau pr. person, ikke et præcist budget for hver opgørelse. De to tal er ikke additive - det er to måder at opgøre samme klimapåvirkning.",
  },
  forurening: {
    id: "forurening",
    scoring: "Gennemsnit af fire indikatorer (ikke worst-of): (1) Pesticider: andel af kommunens aktive almene vandværker, hvor seneste analyse (højst 10 år gammel) har fund af pesticider eller nedbrydningsprodukter. Andelen udglattes med empirisk Bayes (beta-binomial), så en kommune med få vandværker trækkes mod landsgennemsnittet - ratio = (kommunens andel / landsgennemsnit) × 100. (2) Nitrat i drikkevand: gennemsnit over kommunens aktive almene vandværker, vægtet efter anlæggenes tilladte årsindvinding - ratio = (mg/L / 6 mg/L) × 100. (3) Genanvendelse: den andel af husholdningsaffaldet, der ikke indsamles til genanvendelse, målt mod de 35%, som EU's 65%-mål tillader - ratio = ((100 − genanvendt %) / 35) × 100. (4) Affald: husholdningsaffald kg/person, inverteret ratio mod landsgennemsnittet. Affald og genanvendelse er medianen af de tre seneste år. Dimensionens score er det uvægtede gennemsnit af de fire.",
    boundary: "Pesticider: landsgennemsnittet, hvor {ref:pesticider:1}% af de aktive almene vandværker har fund. Nitrat: 6 mg/L, som en international ekspertgruppe nedsat af Miljøministeriet anbefalede i 2025 som ny sundhedsbaseret grænseværdi (i dag 50 mg/L). Genanvendelse: 65% (EU Affaldsdirektiv 2035). Affald: landsgennemsnit som reference.",
    boundarySources: [
      { label: "Miljøministeriet (2025): ekspertvurdering af grænseværdien for nitrat i drikkevandet", url: "https://mim.dk/nyheder/pressemeddelelser/2025/december/miljoeministeren-igangsaetter-indsats-efter-ekspertvurdering-af-graensevaerdien-for-nitrat-i-drikkevandet" },
      { label: "Kleinman (1973), Proportions with extraneous variance, JASA 68:46-54 (empirisk Bayes-udglatning)", url: "https://doi.org/10.1080/01621459.1973.10481332" },
      { label: "GEUS, Jupiter - national boringsdatabase", url: "https://www.geus.dk/produkter-ydelser-og-faciliteter/data-og-kort/national-boringsdatabase-jupiter" },
      { label: "Miljøstyrelsen (2025): kravværdien for pesticider er fastsat politisk ud fra et forsigtighedsprincip", url: "https://mst.dk/nyheder/2025/januar/befolkningen-kan-have-tillid-til-den-danske-vandforsyning" },
    ],
    limitations: "Affald og genanvendelse er fra {aar:cirkularitet_waste} (Danmarks Statistik LABY25). Medianen af tre år bruges, fordi enkeltår indeholder fejlindberetninger: i 2023 faldt Hørsholm fra 589 til 57 kg husholdningsaffald pr. indbygger, mens Fredensborg næsten fordoblede sit tal. Medianen følger en stigende genanvendelse med cirka ét års forsinkelse. Nitrat og pesticider hentes direkte fra GEUS Jupiter (seneste analyse pr. vandværk, højst 10 år gammel) og dækker {daekning:nitrat}/{kommuner} kommuner - de {mangler:nitrat} uden data har ingen aktive almene vandværker med aktuel analyse. Fra september 2026 indgår kun aktive vandværker: nedlagte værker leverer ikke drikkevand, og med dem stod Thisted med 5,2 mg/L nitrat, mod 14,5 mg/L for de aktive værker (Greenpeace/Schullehner: 13,9). Pesticidindikatoren talte indtil da 'over kravværdien', men medregnede nedlagte værker og værker hvor seneste analyse var under kravværdien; kun 33 aktive vandværker er i dag over kravværdien, for få til at skelne kommunerne. Fund er GEUS' egen hovedindikator for pesticider i grundvandet. Et fund kan ligge under eller over kravværdien på 0,1 µg/l pr. stof. Et fund over kravværdien er en overskridelse af drikkevandskravet, men de fleste fund ligger under. Kravværdien er fastsat politisk ud fra et forsigtighedsprincip og ikke ud fra stoffernes giftighed (Miljøstyrelsen), så indikatoren viser, hvor udbredt pesticidrester er i drikkevandsressourcen, og er ikke en sundhedsvurdering. Vandværker uden registreret årsindvinding vægtes med medianen frem for nul. Reel genanvendelse kan afvige fra indsamlet til genanvendelse. Affald dækker kun husholdningsaffald, og sommerhuskommuners affald deles med de fastboende. Dimensionen bruger gennemsnit, ikke worst-of, da de fire indikatorer adresserer vidt forskellige forureningskilder.",
  },
  luftkvalitet: {
    id: "luftkvalitet",
    scoring: "Worst-of af to indikatorer: (1) NO2-koncentration (kvælstofdioxid, µg/m³ årsgennemsnit) og (2) PM2.5-koncentration (fine partikler, µg/m³ årsgennemsnit). Begge sammenholdes med WHO's retningslinjer fra 2021. Ratio = (kommunens koncentration / WHO-grænse) × 100. Ratio over 100 = over WHO-grænsen. Dimensionens samlede score er den højeste (værste) af de to sub-indikatorer - planetary boundary-logik: hvis bare én grænse er overskredet, er dimensionen overskredet. Kommunens tal er befolkningsvægtet: hver beboet km-celle i Eurostats befolkningsgrid (2021) får koncentrationen i den 1×1 km modelcelle den ligger i, og kommunens tal er gennemsnittet vægtet med antal beboere - samme metode som WHO, EEA og FN's verdensmålsindikator 11.6.2 bruger for eksponering.",
    boundary: "WHO 2021 Air Quality Guidelines (årsgennemsnit): NO2 = 10 µg/m³, PM2.5 = 5 µg/m³. WHO-grænsen er valgt frem for EU's grænseværdier (NO2: 40 µg/m³, PM2.5: 25 µg/m³) fordi WHO-grænsen er videnskabeligt baseret på sundhedseffekter, mens EU-grænsen er et politisk kompromis.",
    boundarySources: [
      { label: "WHO Air Quality Guidelines 2021", url: "https://www.who.int/publications/i/item/9789240034228" },
      { label: "DCE/AU - Luftkvalitet 2022 (SR580)", url: "https://dce2.au.dk/pub/SR580.pdf" },
      { label: "Miljøportal WFS - luftkoncentrationer", url: "https://arld-extgeo.miljoeportal.dk/geoserver/wfs" },
    ],
    limitations: "Modelberegnet baggrundskoncentration (UBM, 1×1 km grid) - ikke målte værdier. Fanger ikke lokale hotspots ved travle gadestrækninger (OSPM-model dækker dette, men kun i store byer). Befolkningsgridet er fra 2021. Indtil september 2026 var kommunens tal et simpelt gennemsnit af alle modelceller, selv om denne side sagde befolkningsvægtet; forskellen er lille for PM2.5, der er jævnt fordelt, og størst for NO2 i byer. PM2.5 i Danmark er i høj grad påvirket af langtransport fra kontinentet og hav - ikke kun lokale kilder.",
  },
  naeringsstoffer: {
    id: "naeringsstoffer",
    scoring: "Worst-of af tre indikatorer - to presmål med absolutte grænser og ét effektmål. (1) Kvælstof til kystvandene: statusbelastningen (afstrømningsnormaliseret, 2017-2021) i procent af målbelastningen, altså den kvælstofmængde kystvandet kan tåle og stadig nå god økologisk tilstand, beregnet med modeller for hvert kystvand. Et areal afvander til sit eget kystvand og videre til alle kystvande nedstrøms og får den højeste overskridelse i kæden. Kommunens tal er det arealvægtede gennemsnit over dens deloplande. Ratio = (status / målbelastning) × 100. (2) Kvælstofnedfald fra luften: DCE's beregnede deposition i kg N pr. ha (gennemsnit af tre år) mod en tålegrænse på 10 kg N/ha/år - ratio = (nedfald / 10) × 100. (3) Vandområder i god økologisk tilstand (VP3): den andel af kommunens vandløb, søer og kystvande, der ikke er i god tilstand, målt mod samme andel for hele landet - ratio = ((100 − andel god) / (100 − landsandel god)) × 100. Dimensionens samlede score er den værste af de tre (planetary boundary-logik).",
    boundary: "Målbelastningen er den nedskalerede kvælstofgrænse for hvert kystvand, fastlagt i vandområdeplanerne ud fra kravet om god økologisk tilstand. For Danmark samlet svarer det til en overskridelse på ca. 1,5 gange (CONCITO 2025: 55.800 mod 37.900 ton N om året). Tålegrænsen på 10 kg N/ha/år er midten af intervallet 5-15 kg N/ha, som DCE angiver for heder, klitter og klithede (Bobbink m.fl. 2022; Bak 2024), og DCE sammenholder selv det beregnede nedfald (4-18 kg N/ha i modellens gitterfelter) med disse intervaller. Vandområdernes tilstand måles mod landsgennemsnittet; EU's mål er at alle vandområder er i god tilstand, og nationalt er det kun ca. {ref:overfladevand:0}%.",
    boundarySources: [
      { label: "Vandområdeplanerne 2021-2027 efter genbesøget (2026), bilag 1.1", url: "https://sgavmst.dk/vandmiljoe/vandomraadeplaner/overblik-vandomraadeplanerne-2021-2027/vandomraadeplanerne-2021-2027-efter-genbesoeget" },
      { label: "DCE (2024), Opdatering af empirisk baserede tålegrænser, notat 2024|16", url: "https://dce.au.dk/fileadmin/dce.au.dk/Udgivelser/Notater_2024/N2024_16.pdf" },
      { label: "DCE, Atmosfærisk deposition 2023 (SR626)", url: "https://dce.au.dk/fileadmin/dce.au.dk/Udgivelser/Videnskabelige_rapporter_600-699/SR626.pdf" },
      { label: "CONCITO (2025), Downscaling the planetary boundaries to national level", url: "https://concito.dk/en/udgivelser/downscaling-the-planetary-boundaries-to-national-level-the-case-of-denmark" },
    ],
    limitations: "Statusbelastningen stammer fra vandområdeplanerne efter genbesøget (april 2026) og er opdateret til og med 2021; den ændres først ved næste plan. Målbelastningen er et modelresultat med usikkerhed, og kystvande i åbent hav (fx Vesterhavet) har ingen; arealer der kun afvander dertil, indgår ikke. Tålegrænsen er en forenkling: den rigtige grænse afhænger af naturtypen, og nedfaldet er et gennemsnit over hele kommunen, ikke kun naturarealerne. Fosfor indgår ikke: målbelastningen for fosfor til kystvandene er sat lig baseline, så der er ingen grænse at måle den mod. Spildevandets kvælstof og fosfor pr. indbygger, som indgik indtil september 2026, er en del af statusbelastningen; målt pr. indbygger i renseanlæggets kommune gav de et skævt billede. Tålegrænsen for kvælstof pr. ha landbrug (også fjernet) målte kystvandets følsomhed, ikke belastningen. Vandområdernes tilstand tælles pr. styk og er fra 2025.",
  },
  vand: {
    id: "vand",
    scoring: "Enkelt indikator: grundvandsindvindingen i kommunen - almene vandværker, virksomheder med egen indvinding og markvanding (DST VANDIND, grundvand) - i procent af kommunens andel af Danmarks bæredygtige grundvandsressource, som gennemsnit af de tre seneste år. Ressourcen er GEUS' opgørelse for hele landet, 1.104 mio. m³ om året, fordelt på kommunerne efter grundvandsdannelsen: DK-modellens nedsivning til grundvandet (infiltration til mættet zone, gennemsnit 1991-2020) gange kommunens landareal. En sandjordskommune med meget nedsivning får dermed en større andel end en lerjordskommune af samme størrelse. Ratio = udnyttelsen i procent. Over 100 = kommunen indvinder mere end sin andel af det, der kan indvindes bæredygtigt.",
    boundary: "100% af kommunens andel af den bæredygtige grundvandsressource (GEUS 2023). GEUS' opgørelse bygger på ni indikatorer, bl.a. vandområdeplanernes krav om højst 30% udnyttelse af grundvandsdannelsen til de øvre magasiner og højst 10% reduktion af grundvandets tilstrømning til vandløbene, og CONCITO (2025) bruger den som Danmarks sikre råderum for vand. Danmark samlet udnyttede ca. 66% i 2017-2021 ifølge GEUS, med størst overudnyttelse omkring København og Aarhus.",
    boundarySources: [
      { label: "GEUS (2023), Vandressourceopgørelse - datarapport (Henriksen m.fl.), bilag 2", url: "https://data.geus.dk/pure-pdf/GEUS-R_2023_08_web.pdf" },
      { label: "Hydrologisk Informations- og Prognosesystem (HIP): DK-modellens infiltration til mættet zone", url: "https://hip.dataforsyningen.dk/pages/documentation.html" },
      { label: "Miljøstyrelsen (2023), Forvaltning af fremtidens drikkevandsressource", url: "https://www2.mst.dk/Udgiv/publikationer/2023/12/978-87-7038-569-5.pdf" },
    ],
    limitations: "Fordelingen efter grundvandsdannelse er en nedskalering, ikke GEUS' egen opgørelse pr. område: GEUS' ressource afhænger også af vandløbene og magasinernes dybde. Kontrolleret mod GEUS' tal pr. modelområde rammer fordelingen Sjælland (110 mod 113 mio. m³), Fyn og Jylland inden for ca. 20%, mens Lolland-Falster og Bornholm får en for stor andel. Lokale problemer, som GEUS finder i dele af Vestjylland på grund af vandløbene, fanges derfor kun delvist. Indvindingen registreres hvor vandet pumpes op, så små bykommuner med egne kildepladser (Ishøj, Frederiksberg, Furesø) får meget høje tal, fordi grundvandsoplandet er større end kommunen, mens en bykommune uden indvinding (Herlev) står på 0. Samsø og Læsø ligger uden for DK-modellen og har ingen værdi. Kun grundvand tæller: overfladevand (ca. en fjerdedel af al indvinding, især virksomheder som dambrug, der leder vandet tilbage) indgår ikke. Markvandingen svinger med sommerens nedbør; treårsgennemsnittet udjævner det. Indtil september 2026 målte indikatoren almene vandværker pr. indbygger og viste i praksis, hvor HOFOR har kildepladser, og derefter kortvarigt al indvinding pr. areal mod landsgennemsnittet.",
  },
  arealanvendelse: {
    id: "arealanvendelse",
    scoring: "Enkelt indikator: antropiseret areal - intensivt landbrug (korn, rodfrugter, permanente afgrøder og ikke-klassificeret landbrug, DST-kategorierne D1+D2+D4) plus befæstet og bebygget areal (veje, jernbaner, lufthavne, bebyggelse og råstofgrave, A1+A2+B1+B2+C1) i procent af landarealet uden søer og vandløb (DST AREALDK2). Ratio = (andel / {ref:areal_antropiseret:1}%) × 100 mod Danmark samlet {aar:areal_antropiseret}. Definitionen følger Dao m.fl. (2015) og EEA (2020), som CONCITO (2025) bruger for Danmark. Naturkvalitet måles separat i biodiversitetsdimensionen (DCE bioscore).",
    boundary: "Danmark samlet {aar:areal_antropiseret} som reference: ~{ref:areal_antropiseret:0}% af landarealet er antropiseret. Til kontekst: den planetære grænse for arealsystemet er højst 15% antropiseret areal (Dao m.fl. 2015; CONCITO 2025) - Danmark ligger næsten fem gange over. Vi scorer bevidst mod landsgennemsnittet i stedet for de 15%, så man kan se forskel mellem kommuner; ellers ville alle lyse dybrødt, og en bykommune kan ikke være 85% natur.",
    boundarySources: [
      { label: "Dao m.fl. (2015), Environmental limits and Swiss footprints based on Planetary Boundaries", url: "https://archive-ouverte.unige.ch/unige:74873" },
      { label: "CONCITO (2025), Downscaling the planetary boundaries to national level", url: "https://concito.dk/en/udgivelser/downscaling-the-planetary-boundaries-to-national-level-the-case-of-denmark" },
    ],
    limitations: "Måles mod landsgennemsnittet (niveau 3 baseline), ikke den absolutte grænse. Mark og by tæller ens: et hektar vej og et hektar kornmark er begge taget fra naturen. Ekstensivt landbrug (permanent græs), parker og idrætsanlæg tæller ikke med. Indtil september 2026 var dimensionen worst-of af landbrugsandel og bebygget andel, hver for sig mod deres landsgennemsnit. Fordi de to er hinandens spejlbillede (by mod land), var 82 af 98 kommuner røde af konstruktionsmæssige grunde, og Frederiksberg fik 637. Dimensionen dækker ikke fragmentering af levesteder.",
  },
  biodiversitet: {
    id: "biodiversitet",
    scoring: "Worst-of af to tærskler fra DCE's biodiversitetskort (bioscore-raster, 10x10 m). Bioscore vurderer hvor værdifuldt hvert areal er som levested for truede arter. (1) Væsentlig naturværdi (bioscore ≥8) mod EU's 30%-mål. (2) Uerstattelig naturværdi (bioscore ≥12) mod 10%-målet for strengt beskyttet natur. Målet 'mindst 30% natur' er det samme som 'højst 70% uden', så ratioen er den del af kommunen der mangler naturværdi, målt mod det målet tillader: ratio = ((100 − andel) / 70) × 100 for væsentlig og ((100 − andel) / 90) × 100 for uerstattelig naturværdi. Over 100 = under målet. Dimensionsscoren er den dårligste (højeste ratio) af de to. I modsætning til rent arealdække vægter bioscore naturkvalitet - en biologisk fattig plantage tæller derfor lavt.",
    boundary: "30% væsentlig naturværdi + 10% uerstattelig naturværdi (EU Biodiversitetsstrategi 2030, 30x30-målet). VIGTIGT: Dette er EU's politiske mål, ikke den planetære grænse. CONCITO-rapporten (2025) vurderer Danmarks samlede biodiversitet til et Biodiversity Intactness Index på 44% mod en sikker planetær grænse på 90%. En kommune kan altså nå 30%-målet og lyse grønt uden at være inden for den biofysiske grænse.",
    boundarySources: [
      { label: "Fanning m.fl. (2022), The social shortfall and ecological overshoot of nations", url: "https://www.nature.com/articles/s41893-021-00799-z" },
      { label: "Richardson m.fl. (2023), Earth beyond six of nine planetary boundaries", url: "https://www.science.org/doi/10.1126/sciadv.adh2458" },
    ],
    limitations: "Grænserne er politiske mål (30%/10%), ikke den planetære grænse. Den planetære BII-grænse (44% for DK) er et groft globalt modelestimat (0,25° opløsning, usikkerhed 41-61%) og kan ikke beregnes meningsfuldt per kommune - derfor bruges det lokalt forankrede danske bioscore-kort i stedet. Bioscore måler habitatkvalitet, ikke fredningsstatus: et areal kan have høj naturværdi uden at være beskyttet, og omvendt. Kortet er fra 2021 og opdateres sjældent, så dimensionen har ingen retningspil. Indtil september 2026 var ratioen mål/andel med et loft på 300; andele nær nul gav tusinder, og over halvdelen af kommunerne stod på loftet uden indbyrdes rangorden. Med den nuværende formel giver 0% natur 143 på væsentlig og 111 på uerstattelig naturværdi, fordi målene tillader henholdsvis 70% og 90% uden.",
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
  const dimensionDataYears = getDimensionDataYears();
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

        {/* Metodeartikler til download (docs/artikler/, kopieret til public/artikler/) */}
        <div className="p-4 bg-white border border-gray-200 rounded-xl mb-4">
          <h3 className="font-bold text-gray-900 mb-1">Metodeartikler</h3>
          <p className="text-sm text-gray-600 leading-relaxed mb-2">
            To artikler forklarer metoden mere udførligt, tester hvor følsomme resultaterne er over for metodens valg, og gennemgår svaghederne.
            Tallene er et øjebliksbillede af data fra 26. september 2026.
          </p>
          <ul className="text-sm space-y-1">
            <li>
              <a href="/artikler/metodeartikel-1-social-ring.docx" download className="text-blue-600 hover:underline font-medium">
                Et socialt fundament for 98 kommuner
              </a>{" "}
              <span className="text-gray-400">(Word, 230 kB)</span>
            </li>
            <li>
              <a href="/artikler/metodeartikel-2-oekologisk-ring.docx" download className="text-blue-600 hover:underline font-medium">
                Et økologisk loft for 98 kommuner
              </a>{" "}
              <span className="text-gray-400">(Word, 250 kB)</span>
            </li>
          </ul>
        </div>

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
                <p className="text-sm font-semibold text-emerald-900">Sammenligning med andre kommuner</p>
                <p className="text-xs text-emerald-700">Bruges hvor der ikke findes et meningsfuldt absolut mål. Standard er gennemsnittet i kommunens egen kommunegruppe. Landsgennemsnittet og top 10 % (gennemsnittet af de 10 bedste kommuner - det der er empirisk muligt i Danmark) kan vælges på kommunesiden.</p>
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
          <strong>Socialt fundament:</strong> Score 100 = sammenligningsgrundlaget. Som standard er det gennemsnittet i kommunens egen kommunegruppe
          (DST&apos;s fem grupper: hovedstads-, storby-, provinsby-, oplands- og landkommuner). Det kan skiftes til landsgennemsnittet eller top 10 % øverst
          på kommunesiden. Indikatorer der scores mod et fast mål (95 %-uddannelsesmålet og 0 % fossil opvarmning), påvirkes ikke af skiftet.
          100 eller derover er grønt, 85-100 gult og under 85 rødt. Segmenter i den indre ring viser &quot;shortfall&quot; - kommunen ligger under sammenligningsgrundlaget.
        </p>
        <p className="text-sm text-gray-700 leading-relaxed mt-2">
          <strong>Økologisk loft:</strong> Score 100 = grænseværdi. 85 eller derunder er grønt, 85-100 gult (tæt på grænsen), og over 100 er &quot;overshoot&quot; (rødt).
          Røde segmenter i den ydre ring viser overskridelse af grænsen. Det økologiske loft påvirkes ikke af valget af sammenligningsgrundlag.
        </p>
        <p className="text-sm text-gray-700 leading-relaxed mt-4">
          <strong>Vægtning:</strong> Hver kategori (f.eks. Sundhed, Velfærd, Bolig) beregnes som et simpelt gennemsnit af sine indikatorer.
          Det samlede sociale gennemsnit er et gennemsnit af kategorierne - ikke af de individuelle indikatorer.
          Det betyder at kategorier med få indikatorer (f.eks. Bolig og Energi med 1) vægter lige så tungt som kategorier med mange (f.eks. Sundhed og Uddannelse med 9).
          Dette er et bevidst valg: hver dimension i doughnut-modellen anses for lige vigtig, uanset hvor mange indikatorer der måler den.
        </p>
        <p className="text-sm text-gray-700 leading-relaxed mt-2">
          <strong>Inverterede indikatorer:</strong> For indikatorer hvor lavere er bedre (f.eks. kriminalitet, affald, børnefattigdom)
          beregnes ratioen inverteret: (landsgennemsnit / kommune) × 100, så højere ratio fortsat betyder bedre performance.
          Sociale ratioer er klippet ved 150, så én ekstremværdi ikke dominerer kategoriens gennemsnit. Loftet gælder i alle tre sammenligninger:
          en score kan højst blive 150, også når den regnes om til kommunegruppen eller top 10 %. Kommunerne
          på loftet er derfor ikke indbyrdes rangordnet på den pågældende indikator. Økologiske andele hvor højere er bedre
          (natur, genanvendelse, vandområder i god tilstand) regnes om til den manglende andel, målt mod det målet tillader
          - &quot;mindst 30 % natur&quot; er det samme som &quot;højst 70 % uden&quot;. Så har alle økologiske ratios nul ved ingen
          belastning, som Fanning m.fl. (2022) og Richardson m.fl. (2023) normaliserer, og ingen af dem har brug for et loft.
        </p>
      </section>

      {/* Ærlig note: absolutte vs relative grænser */}
      <section className="mb-10 p-5 bg-blue-50 border border-blue-200 rounded-xl">
        <h3 className="text-base font-semibold text-gray-900 mb-2">Om grænserne i det økologiske loft</h3>
        <p className="text-sm text-gray-700 leading-relaxed">
          Nogle dimensioner måles mod absolutte grænser (WHO&apos;s luftgrænser, EU&apos;s genanvendelses- og naturmål, nitratgrænsen på 6 mg/L, 2,5 ton CO₂e pr. person, kystvandenes målbelastning for kvælstof, tålegrænsen for kvælstofnedfald og den bæredygtige grundvandsressource). Andre måles mod landsgennemsnittet, fordi der ikke findes en meningsfuld absolut grænse på kommuneniveau. Det betyder at en grøn score på en relativ dimension viser &quot;bedre end de fleste danske kommuner&quot; - ikke nødvendigvis &quot;inden for planetens grænser&quot;. Danmark som helhed overskrider de fleste planetære grænser markant.
        </p>
        <p className="text-sm text-gray-700 leading-relaxed mt-2">
          Læs mere om hvordan de planetære grænser ser ud for Danmark, og hvad der bevidst ikke kan måles på kommuneniveau, i{" "}
          <a href="/artikel/planetaere-graenser" className="text-blue-600 hover:underline font-medium">
            artiklen om planetære grænser
          </a>.
        </p>
        <p className="text-sm text-gray-700 leading-relaxed mt-2">
          Hver dimension er mærket efter hvad den måles imod: <strong>mod mål</strong> (en fast absolut grænse - WHO, EU-mål, nitratgrænse, målbelastning, grundvandsressource, 0 % fossil, 95 %-uddannelsesmål) eller <strong>mod landsgennemsnit</strong> (umærket - relativ til de øvrige kommuner). Et par dimensioner er <strong>blandet</strong>. På en &quot;mod mål&quot;-dimension betyder grøn &quot;inden for grænsen&quot;; på en relativ betyder grøn &quot;bedre end de fleste kommuner&quot;.
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
                      <p className="text-gray-600">{udfyldTal(method.scoring)}</p>
                    </div>

                    {method.boundary && (
                      <div>
                        <p className="font-medium text-gray-800 mb-1">Grænseværdi</p>
                        <p className="text-gray-600">{udfyldTal(method.boundary)}</p>
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

                    {dimensionDataYears[cat.id] && (
                      <div>
                        <p className="font-medium text-gray-800 mb-1">Datatidspunkt</p>
                        <p className="text-gray-600">{dimensionDataYears[cat.id]}</p>
                      </div>
                    )}

                    {method.limitations && (
                      <div>
                        <p className="font-medium text-gray-800 mb-1">Begrænsninger</p>
                        <p className="text-gray-600">{udfyldTal(method.limitations)}</p>
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
                      <p className="text-gray-600">{udfyldTal(method.scoring)}</p>
                    </div>

                    {method.boundary && (
                      <div>
                        <p className="font-medium text-gray-800 mb-1">Grænseværdi</p>
                        <p className="text-gray-600">{udfyldTal(method.boundary)}</p>
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

                    {dimensionDataYears[dim.id] && (
                      <div>
                        <p className="font-medium text-gray-800 mb-1">Datatidspunkt</p>
                        <p className="text-gray-600">{dimensionDataYears[dim.id]}</p>
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

                    {dimensionCsvFiles(dim.id).length > 0 && (
                      <div>
                        <p className="font-medium text-gray-800 mb-1">Datafil</p>
                        <p className="text-gray-600 font-mono text-xs">{dimensionCsvFiles(dim.id).join(" + ")}</p>
                      </div>
                    )}

                    {method.limitations && (
                      <div>
                        <p className="font-medium text-gray-800 mb-1">Begrænsninger</p>
                        <p className="text-gray-600">{udfyldTal(method.limitations)}</p>
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
          Koden ligger offentligt på GitHub, men der er endnu ikke givet en licens til genbrug; den beslutning ligger hos Thisted Kommune. Platformen er under aktiv udvikling, og feedback er velkommen.
        </p>
      </section>
    </div>
  );
}
