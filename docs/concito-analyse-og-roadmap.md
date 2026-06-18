# CONCITO-rapporten: analyse, gennemførte forbedringer og fravalg

Kilde: CONCITO (2025), "Downscaling planetary boundaries to national level - the case of Denmark".
Analyse foretaget juni 2026. Dette dokument er den durable hukommelse over hvad vi kan/ikke kan
bruge fra rapporten på kommuneniveau, og hvilke bevidste fravalg vi har taget. Læs det før du
overvejer at tilføje eller ændre økologiske indikatorer baseret på rapporten.

## Hvad rapporten gør

Rapporten nedskalerer 6 af de 9 planetære grænser til dansk nationalt niveau: klima, biosfærens
integritet, arealsystem, ferskvand, biogeokemiske strømme (N+P) og aerosoler/luft. Konklusion:
Danmark overskrider de fleste grænser markant, og under et ansvarsprincip (historisk bidrag) er
flere budgetter allerede opbrugt - dvs. negativt restbudget for bl.a. klima, biodiversitet og N.

## Gennemført (på platformen)

- **Biodiversitet → bioscore**: skiftet fra rent naturareal (% arealdække fra AREALDK2) til DCE's
  biodiversitetskort (bioscore-raster, 10x10 m) med to tærskler: væsentlig naturværdi (bioscore ≥8)
  mod 30%-målet, og uerstattelig naturværdi (bioscore ≥12) mod 10%-målet. Worst-of afgør scoren.
  Mere lokalt forankret og kvalitetsvægtet end rent arealdække. Bemærk: projektet brugte engang
  bioscore, fravalgte det som "for upræcist/svært at kommunikere", men det skyldtes den rå
  bioscore-skala. Vi viser nu i stedet "% areal med naturværdi" mod konkrete mål - hvilket løser
  kommunikationsproblemet, og bioscore er reelt mere præcist end arealdække (10 m danske data).
  Ratioer cappes ved 300 i build_master_csv.py (ellers giver pct nær 0 ratioer i tusinder).
- **Metodenoter**: tydeliggjort at biodiversitetsgrænsen er et politisk mål (30%/10%), ikke den
  planetære grænse (BII 90%), og at DK samlet er i kraftig overskridelse. Generel note om absolutte
  vs relative grænser tilføjet metodesiden.
- **Artikel**: offentlig formidling af analysen på /artikel/planetaere-graenser.
- **Overfladevand (VP3) → Næringsstoffer**: vandområdernes økologiske tilstand lagt ind som effektmål
  under Næringsstoffer (ikke egen dimension), da det er eutrofieringens synlige effekt - som CONCITO
  netop måler under nærings-grænsen.
- **Forbrugsbaseret CO₂ → Klimapåvirkning**: territorial og forbrugsbaseret udledning samlet i én
  klimadimension med to indikatorer (worst-of), da begge måler samme planetære grænse (klima), bare
  med to opgørelsesmetoder. Klima-scoren afspejler nu den forbrugsbaserede (største) værdi. Ringen
  gik fra 9 til 8 dimensioner.

**Designprincip (etableret juni 2026):** Én planetær grænse = én dimension. Flere indikatorer eller
opgørelsesmetoder for samme grænse lægges som sub-indikatorer under den dimension (worst-of), ikke som
separate dimensioner. Det er begrundelsen bag begge ovenstående sammenlægninger.

## Kan implementeres senere (data findes)

- ~~VP3 vandkvalitet per kommune~~ [GENNEMFØRT som indikator under "Næringsstoffer"]: andel vandområder
  (vandløb, søer, kystvande) i mindst god økologisk tilstand. Lagt under Næringsstoffer (ikke egen
  dimension), fordi dårlig vandtilstand er eutrofieringens effekt - som CONCITO netop måler under
  nærings-grænsen (marine/freshwater eutrophication). Scriptet `fetch_vp3_vandkvalitet.py`
  henter VP3-zip (370 MB, til temp, ikke committet), bruger de indbyggede kom1-4-felter (ingen spatial
  join nødvendig), og skriver `data/vp3_vandkvalitet_scores.csv`. Nationalt: kun ~5,8% i god tilstand.
  Scoret mod landsgennemsnit, EU's 2027-mål (100%) vist som kontekst. Fremtidig vedligehold (flere år
  ude): når en ny vandområdeplan udkommer, kan en assistent opdatere kilden - August skal ikke selv
  køre scripts.
- **Absolut arealgrænse (15% antropiseret)** [GENNEMFØRT som kontekst]: rapportens arealsystem-grænse
  (Rockström 2009 / Dao et al. 2015) kan anvendes per kommune (intensiv + bebygget vs 15%). DK ligger
  på 73-75% = 5,2x overskridelse. Valgt løsning (juni 2026): vises som kontekst i metode + dimensionens
  boundary-tekst, men scoringen er fortsat mod landsgennemsnit, så man kan se forskel mellem kommuner.
  Hvis det senere ønskes som faktisk score: tilføj en tredje sub-indikator (intensiv+bebygget vs 15%)
  i build_master_csv.py - men det gør stort set alle kommuner dybrøde.
- **§3 beskyttet natur via WFS**: laget dai:bes_naturtyper findes på
  https://arealeditering-dist-geo.miljoeportal.dk/geoserver/wfs (GetCapabilities verificeret).
  Pt. fravalgt som redundant (se nedenfor), men datakilden er kortlagt hvis det ønskes senere.

## Fravalgt - med begrundelse (så det ikke genovervejes uden grund)

- **BII/MSA/HANPP per kommune**: UMULIGT. Globale modeller. BII (de 44% for DK) er 0,25° opløsning
  (~430 km²/celle, større end mange kommuner som fx Frederiksberg på 8,7 km²), et modelestimat ikke
  en måling, med usikkerhed 41-61%, og endda en SSP-scenariefremskrivning for 2024 (ikke en
  observation). Verificeret via direkte opslag i NHM's database (Phillips et al. 2021, datasæt
  DOI 10.5519/HE1EQMG1, area_code 001-150-154-DNK, SSP2 2024 = 43,7%). Hører til som national
  kontekst i artiklen, ikke som indikator per kommune.
- **§3 beskyttet natur som egen indikator**: REDUNDANT. Bioscore (gennemført) dækker reelt det samme
  (kvalitet/beskyttelsesværdi) bedre, og rammer CONCITO's to mål (30%/10%) direkte. §3-data findes
  via WFS hvis vi alligevel vil vise fredningsstatus separat senere.
- **Absolut N-grænse per kommune**: IKKE MULIGT rent. Rapportens N-grænse (37.900 ton N/år til kyst)
  er et nationalt budget; per-kommune kræver NOVANA-oplandsdata vi ikke har. Vores spildevands-N/P +
  VP3 N-loft (mod landsgennemsnit) er det vi kan gøre. Derfor frafalder "absolutte grænser" for
  næringsstoffer, selvom det indgik i den oprindelige ønskeliste.
- **Forbrugsbaseret areal/biodiversitet/N/vand**: IKKE PER KOMMUNE. Kræver EXIOBASE input-output på
  nationalt niveau. Vi har forbrugsbaseret CO2 som estimat; resten er uden for MVP. Vigtig pointe:
  DK's forbrugsbaserede aftryk er 2-5x det territoriale (sojaimport alene ~18% af DK's areal i
  udlandet) - hører til som framing i artiklen.
- **Jordsundhed (soil health)**: INGEN KOMMUNEDATA. Mangler også i rapporten selv. Kendt hul.
- **Drænede landbrugsarealer**: KUN NATIONALT ESTIMAT (~52%, Møller et al. 2018). Ingen ren
  kommuneopdeling.
- **Kystpres (coastal squeeze)**: INGEN INDIKATOR. Relevant for kystkommuner (havstigning +
  kystsikring presser unik kystnatur), men intet rent datagrundlag per kommune.
- **Fair-share / historisk ansvar**: FRAMING, IKKE INDIKATOR. Vigtig pointe (DK har negativt
  restbudget under ansvarsprincippet), hører til i artikel/metode, ikke som tal per kommune.

## Hvor vi er foran rapporten

- Vores `forurening`-dimension dækker novel entities (pesticider i grundvand), som rapporten helt
  sprang over som for umoden videnskab.
- Vores `forbrug_co2` er præcis den forbrugsbaserede linse rapporten efterlyser - bare på CO2.
- Vores worst-of-logik for multi-indikator-dimensioner svarer til rapportens "one-out-all-out".
