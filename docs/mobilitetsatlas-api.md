# Dansk Mobilitetsatlas: findes der en API, og kan vi bruge data?

Undersøgt august 2026. Kilde: [mobilitetsatlas.dk](https://mobilitetsatlas.dk) af Beta Mobility.
Dette dokument er den durable hukommelse over hvad vi fandt, hvad der virker, og hvad der skal
besluttes før vi kobler noget på pipelinen.

## Kort svar

**Nej, der er ingen dokumenteret API.** Ingen `/api/*`-ruter, ingen OpenAPI, ingen download-knap,
ingen omtale af datasæt eller udtræk nogen steder på sitet.

**Ja, vi kan trække data alligevel.** Sitet er en Next.js-app der henter sine egne data fra
statiske GeoJSON-filer på faste stier. De ligger frit tilgængelige og er rene, komplette og
maskinlæsbare. `scripts/fetch_mobilitetsatlas.py` bruger dem og virker.

Det vigtige forbehold er ikke teknisk, det er licensen. Se afsnittet til sidst.

## Hvad de har lavet

Hver af de 98 kommuner får et mærke fra A til G for **mobilitetsfrihed** på en 0-100-skala.
Scoren er gennemsnittet af to lige tungt vejende dele:

- **Kollektiv kvalitet** (0-100): hvor mange hverdagsdestinationer man kan nå med gang og
  kollektiv trafik inden for rimelig rejsetid. Normeret mod de 98 kommuner, så 0 er den dårligste
  og 100 den bedste MÅLTE rækkevidde.
- **Bevægelsesfrihed** (0-100): hvor stor en del af hverdagen man kan nå uden bil, og hvor stort
  bilens forspring er.

Beregningen er en rigtig rejsetidsanalyse: Rejseplanens GTFS-køreplaner plus OpenStreetMaps
vej-, cykel- og gangnet, kørt gennem r5py, bundet på DST's 100 m kvadratnet og aggregeret via
H3-sekskanter. Rejser over 90 minutter tæller ikke med, korte rejser vægter tungere.

Det er markant tungere metodisk end noget vi selv kunne bygge, og det er grunden til at det er
interessant for os.

## Endpoints der virker

Alle er almindelige GET uden nøgle, uden token, uden cookie.

### Det vi primært skal bruge

| Endpoint | Indhold |
|---|---|
| `/data/geojson/kommuner.geojson` | **98 kommuner, punktgeometri.** `slug`, `name`, `kommune_code`, `grade`, `composite`, `kollektiv_kvalitet`, `bevaegelsesfrihed`, `bilbehov`, `bil_skat_kr`, `tvunget_andel`, `valgt_andel`. 37 KB. Komplet, ingen huller. |
| `/udforsk` med headeren `RSC: 1` | Samme 98 kommuner, men 26 felter. Ekstra: `gini`, `p10`, `cdi`, `o_pt`, `o_car`, `reach_ratio`, `unserved_pct` plus DST-kontekst (befolkning, alder, boligtyper, tæthed). Svartype `text/x-component`. |

`kommune_code` er nulpolstret firecifret i slug'en (`dk-thisted-0787`), men uden nul i selve
feltet (`787`). Det matcher vores egen `kommune_kode` direkte.

### Øvrige lag

| Endpoint | Indhold |
|---|---|
| `/data/geojson/sogne.geojson` | 2.097 sogne med `avg_score` og `total_pop`. Polygoner. 2 MB. |
| `/data/geojson/regioner.geojson` | 4 regioner (Østdanmark er slået sammen) med samme scorefelter. |
| `/data/cdi/{slug}.geojson` | **H3-sekskanter pr. kommune.** `grid_id`, `score`, `cdi`, `o_pt`, `o_car`, `population`, `estimated`. Thisted: 1.973 celler, 0,9 MB. Det er "beregnet ned til gaden"-laget. |
| `/data/pt/{slug}.geojson` | Kollektive ruter som linjer: `routeId`, `shortName`, `mode`, `depPerHour`. Thisted: 654 ruter. |
| `/data/pt/national-network.geojson` | Hele landets kollektive net. |
| `/data/byomraader/{slug}.geojson` | Byområder med kode og navn. |
| `/data/bymoenstre/{slug}.geojson` | Bymønstre (`bykerne` m.fl.). |

`{slug}` er formen `dk-thisted-0787`. Slugs for alle 98 findes i `kommuner.geojson`.

### Det der IKKE findes

`/api`, `/api/v1/*`, `/api/graphql`, `/api/trpc`, `/data.json`, `/download`, `/data/scores.json`.
Alle 404. Kommuneboundaries ligger ikke som fil, men er bagt ind i JS-bundlet
(`3g6ytch8rkpqc.js`, 2,8 MB GeoJSON). Dem har vi i forvejen fra DAGI.

## Driftsnoter

1. **Sitet nulstiller forbindelsen ved hurtige serieforespørgsler.** Vi ramte `SSL_ERROR_SYSCALL`
   og `Connection reset by peer` gentagne gange ved parallelle eller tætte kald. Scriptet holder
   2 sekunders pause og genforsøger fire gange. Behold det.
2. **GeoJSON-ruten er den stabile, RSC-ruten er den skrøbelige.** RSC-payloaden er Next.js'
   interne serialisering af React-komponenter. Den brækker uden varsel hvis de skifter framework
   eller sideopbygning. Derfor falder scriptet tilbage til kun GeoJSON-felterne og skriver CSV'en
   alligevel, med de manglende felter tomme, i stedet for at fejle.
3. **De to kilder er krydstjekket** felt for felt på `composite`, `kollektiv_kvalitet` og `grade`:
   nul afvigelser. Scriptet gentager tjekket ved hver kørsel og advarer hvis de skrider fra
   hinanden, hvilket ville betyde at den ene rute er blevet forældet.
4. **Ingen tidsserie.** Atlasset udstiller kun det aktuelle beregningsår. Der er intet
   arkiv-endpoint og ingen årstalsparameter. En indikator herfra får ALDRIG en retningspil,
   medmindre vi selv arkiverer hver kørsel. Se pitfall 13 i CLAUDE.md.
5. **Kollektiv kvalitet er relativ til de 98 kommuner**, og metodesiden siger eksplicit at når
   atlasset genberegnes, kan ændringer i ANDRE kommuner flytte vores tal. Det er samme logik som
   vores egen avg-baseline, men det betyder at et fald i Thisteds score ikke nødvendigvis er et
   fald i Thisteds busbetjening.

## Hvorfor det er relevant for os

Vores nuværende `public_transport`-indikator er svag. Målt på de faktiske data i
`data/mobilitet_scores.csv`:

- **5 unikke værdier fordelt på 98 kommuner.** Tallet fra DST LABY49 er opgjort på
  kommunegruppe, ikke enkeltkommune, og stemplet ud på alle kommuner i gruppen.
- **31 kommuner har nøjagtig samme tal som Thisted** (9,91 pct.). Indikatoren kan altså ikke
  skelne Thisted fra Skive, Hjørring, Bornholm eller Svendborg overhovedet.
- Det er samme indikator som CLAUDE.md pitfall 17 allerede noterer mangler tidsserie fordi den
  kun findes på gruppeniveau.

Mobilitetsatlassets `kollektiv_kvalitet` giver **95 unikke værdier på 98 kommuner** og er en
rigtig per-kommune-beregning. Korrelationen mellem de to er kun **0,43**, så det er ikke bare en
finere udgave af det samme tal, det måler noget andet og mere præcist.

Thisted til sammenligning:

| | nuværende | mobilitetsatlas |
|---|---|---|
| Værdi | 9,91 pct. (delt med 30 andre kommuner) | kollektiv kvalitet 2,22 af 100 |
| Samlet | - | mobilitetsfrihed 14,59, mærke **G** |
| Placering | - | nr. 88 af 98 |

## Det der skal besluttes før vi kobler på

### 1. Licensen er copyleft, og det er den reelle blokering

Atlasset er **CC BY-SA 4.0**. Licenssiden er utvetydig:

> "Du må kopiere og bearbejde atlaset, hvis du krediterer Beta Mobility, linker til licensen,
> beskriver dine ændringer og udgiver bearbejdelsen på samme licens."

De første tre krav er trivielle for os. Det fjerde er ikke. **ShareAlike betyder at en
bearbejdelse skal udgives under CC BY-SA 4.0.** Vores platform har i dag ingen erklæret licens.
Bruger vi deres tal som en indikator, skal vi tage stilling til om det, vi udgiver, er en
bearbejdelse af atlasset, og i givet fald sætte hele eller dele af platformen under BY-SA.

Bemærk også en uoverensstemmelse på deres eget site: sidefoden gengiver licensen langt snævrere
end licenssiden gør, som om den kun tillod skærmbilleder og henvisninger. Licenssiden er den
udførlige og den, der beskriver den faktiske CC BY-SA-ret. Det er værd at få bekræftet.

### 2. Spørg dem. De inviterer til det

Kontaktsiden skriver direkte at man kan skrive "hvis du vil tale om ... hvordan data kan bruges i
jeres organisation". Kontakt er Robert Joseph Martin, partner i Beta Mobility,
robert@betamobility.com.

Det er den rigtige vej før vi bygger noget. Tre ting at spørge om:

- Må en kommunal, ikke-kommerciel platform bruge kommunetallene med kreditering, og hvad opfatter
  I som ShareAlike-forpligtelsen i den situation?
- Er der planer om et egentligt datasæt eller en API, og er de statiske GeoJSON-stier noget I
  betragter som stabile?
- Genberegner I atlasset periodisk, og bliver tidligere årgange gemt? Det afgør om vi
  overhovedet kan få en retningspil.

### 3. Hvilken indikator, hvis vi går videre

Anbefaling: **erstat `public_transport` med atlassets `kollektiv_kvalitet`**, ikke med
`composite`. Begrundelsen er at `composite` er halvt bevægelsesfrihed, som belønner korte
afstande og tæt by. Det er reelt en bymæssighedsscore, og den ville give landkommuner et
strukturelt straftillæg oveni det, `commute_distance` allerede fanger. Det er den samme fejltype
som den fjernede `car_access`, bare med modsat fortegn.

`kollektiv_kvalitet` er derimod tæt på præcis det, den nuværende indikator FORSØGER at måle, og
den er allerede en 0-100-skala. Den ville skulle ind som `absoluteScore` i `shared.ts` og
dermed være undtaget baseline-toggle (CLAUDE.md pitfall 11), fordi 0-100-skalaen allerede er
normeret mod de 98 kommuner. En top10-omskalering af et allerede normeret tal ville være
dobbeltnormering.

`unserved_pct`, andelen af befolkningen uden reel kollektiv betjening, er et stærkt kandidat-tal
i sig selv og er lettere at kommunikere politisk end en indeksscore. Overvej den som alternativ.

## Hvad der ligger i repoet nu

- `scripts/fetch_mobilitetsatlas.py` - virker, henter begge kilder, krydstjekker og skriver CSV.
  **Kalder bevidst ikke `auto_build_master()`.**
- `data/mobilitetsatlas_scores.csv` - 98 kommuner, 18 kolonner.

Ingen af delene er koblet på master-pipelinen. Hverken `build_master_csv.py` eller `shared.ts`
kender til dem. Platformen er uændret. Det er med vilje: koblingen afventer licensafklaringen og
valget af indikator.
