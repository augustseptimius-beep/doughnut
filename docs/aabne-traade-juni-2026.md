# Åbne tråde og uudnyttede indsigter (19. juni 2026)

Opsamling efter den lange session 19. juni 2026 (CONCITO-opdateringer, Forurening/Vand-omlægning,
Energi-dimensionen). Listen er gode idéer der dukkede op undervejs, men som vi IKKE har handlet på
endnu. Prioriteret efter værdi. Læs den før næste større runde på modellen.

Hvad der ER gjort denne session er dokumenteret i CLAUDE.md (punkt 9-11), `concito-analyse-og-roadmap.md`
og metode-siden. Dette er kun de løse ender.

---

## Høj værdi

### 1. Scoringsfilosofi: absolut vs. relativ baseline mangler en konsistent regel
Gennem hele sessionen stødte vi gentagne gange på det samme valg uden en fast regel: skal en dimension
scores mod en **absolut grænse** (et mål) eller mod **landsgennemsnittet**?

- Absolut i dag: luftkvalitet (WHO), biodiversitet (EU 30/10 %), genanvendelse (EU 65 %), pesticider (0 %),
  nitrat (6 mg/L), klima (3 ton), og nu Energi (0 % fossil).
- Relativ (landsgennemsnit) i dag: næringsstoffer, arealanvendelse, vandindvinding, og de fleste sociale.

**Konsekvens:** "grøn" betyder noget forskelligt fra dimension til dimension. På en relativ dimension =
"bedre end de fleste kommuner". På en absolut = "inden for grænsen". Det svækker fortolkning og
sammenligning på tværs, og det er ikke synligt for brugeren hvilken slags grøn de kigger på.

**Anbefaling:** tag en bevidst runde hvor hver dimension klassificeres (absolut/relativ) med begrundelse,
og overvej at VISE det i UI (lille mærke "mod mål" vs "mod landsgns") så brugeren ved hvad grøn betyder.
Vi har nu `absoluteScore`-flaget som teknisk håndtag. Dette er den vigtigste uafklarede meta-beslutning.
**Effort:** medium (mest metode/beslutning, lidt UI).

### 2. Education's "95 %-mål" er kosmetisk
`education` viser badge "Mål: 95 % (nationalt mål)" og har baselineLevel 2, men dens ratio er reelt
beregnet mod landsgennemsnittet og omskaleres af baseline-toggle (den mangler `absoluteScore`). Badgen
lover altså en absolut grænse som scoren ikke leverer. Det er den eneste indikator med denne
uoverensstemmelse nu (bolig_fossil er gjort ægte absolut denne session).

**Anbefaling:** enten gør education ægte absolut (ratio mod 95 %, sæt `absoluteScore: true`) eller fjern
badgen. Et rent ærligheds-fix. **Effort:** lav.

---

## Medium værdi

### 3. Faktisk VE-dækning (REshare) er bedre end installeret kapacitet
Til Energi-konteksten bruger vi installeret VE-kapacitet (kW/indb.). Energi Data Service har
`ReCoverageMunicipality` = den andel af kommunens FAKTISKE elforbrug der dækkes af VE, time for time.
Det er et mere meningsfuldt mål (hvad bruges der reelt lokalt grønt) end "hvor mange møller står der".
Fravalgt nu fordi årsgennemsnit kræver aggregering af ~8.760 timer pr. kommune og er vejrafhængigt.

**Anbefaling:** overvej at supplere VE-kapacitet-konteksten med et REshare-årsgennemsnit. **Effort:** medium.

### 4. Energiforbrug pr. capita mangler som vinkel
Energi handler nu kun om KILDE (fossil/ren), ikke om MÆNGDE. En kommune kan have ren energi men højt
forbrug. Energistyrelsen har kommunefordelt energiforbrug (download, ikke API). Kunne være en
forbrugs-/effektivitetsvinkel.

**Anbefaling:** vurdér om forbrug pr. capita skal ind - men pas på social-vs-øko-framingen (forbrug er
nærmere klima/øko end socialt fundament). **Effort:** medium.

### 5. Fjernvarmens fossilandel for de 18 fælles-net-kommuner er kun et landssnit-estimat
Vi bruger TJ-vægtet landssnit (~13 %) for kommuner uden egen varmeproduktion. ENS' "Fjernvarmenet
2022-2024" (file 8519) har brændselsmix OG CO2-intensitet pr. NET. Med en net→kommune-mapping kunne
metro-kommunerne få deres reelle (typisk lave) fossilandel i stedet for landssnittet.

**Anbefaling:** hvis Energi bliver en kerne-dimension, lav net-mappingen. Ellers er landssnittet OK for MVP.
**Effort:** medium-høj.

---

## Lav værdi / noter

- **Worst-of vs. gennemsnit pr. dimension** mangler en nedskrevet regel. Vi gjorde Forurening til
  gennemsnit (4 forskellige forureningstyper), resten er worst-of. Princippet bør dokumenteres bevidst.
- **"Kontekst, ikke scoret"-mønsteret** (opfundet til Energi: VE + fjernvarme-mix) kan genbruges til
  15 %-arealgrænsen og BII-44 %, som i dag kun er tekst. Ville give en konsistent "absolut sandhed ved
  siden af den relative score".
- **Energi-farvetærskel:** med 0-mål når ingen kommune grøn (bedst ~96, amber). Bevidst valgt (ærligt).
  Hvis det opleves for hårdt, kan en blødere tærskel for netop denne dimension overvejes - men det bryder
  konsistensen. (Vurderet og fravalgt denne session.)
- **Varmepumpe-udbredelse** (EDS `PrivateConsumptionHeatingMonth`) og **biogas pr. kommune** er mulige
  fremtidige datakilder. Lav prioritet.
- **Forbrugsbaseret CO2** er fortsat et 2011-baseret nationalt-skaleret estimat (±10 %). Bedre kilde hvis
  en kommer.

---

## Operationelt (erfaring fra denne session)

- At køre `npm run build` mens preview/dev-serveren kører destabiliserede dev-serveren (delt `.next`).
  Løsning: stop dev før build, eller ryd `webapp/.next` og genstart dev bagefter.
- Programmatisk `.click()` via eval trigger ikke pålideligt React 19's event-system. Til browser-
  verifikation er `data-category`-attributter + et rigtigt CDP-klik mere robust. Den mest pålidelige måde
  at verificere et udfoldet panel var midlertidigt at sætte `useState(expanded)` default til dimensionen,
  reloade, DOM-tjekke, og rulle tilbage.
