# CONCITO-opdateringer til Doughnut-platformen — implementeringsplan

> **STATUS (18. juni 2026):** ALLE faser (1-5) er GENNEMFØRT og verificeret (produktions-build består, alle sider rendrer, ingen konsolfejl). Fase 4 = mulighed 3 (15%-grænse som kontekst, ingen scoringsændring). Fase 5 = VP3 vandtilstand tilføjet som et effektmål-indikator UNDER "Næringsstoffer" (ikke egen dimension - flyttet efter Augusts spørgsmål om CONCITO-alignment: dårlig vandtilstand er eutrofieringens effekt, som rapporten måler under nærings-grænsen, ikke en selvstændig planetær grænse). Stadig 9 øko-dimensioner. Ændringer er IKKE committet endnu - klar til review + push via GitHub Desktop.

> **For den der udfører planen:** Følg faserne i rækkefølge. Hver fase er selvstændig og kan committes/deployes for sig. Projektet har INGEN automatisk testsuite - verifikation sker ved at køre Python-scriptet, inspicere master-CSV'en og se siden i preview (jf. CLAUDE.md). Steps bruger checkbox-syntaks (`- [ ]`).

**Mål:** Opdatere platformens biodiversitetsmål, tilføje ærlige metodenoter, udgive en offentlig artikel om CONCITO-rapporten, og dokumentere både gennemførte og fravalgte forbedringer - alt baseret på analysen af "Downscaling planetary boundaries to national level - the case of Denmark" (CONCITO 2025).

**Arkitektur:** Data-ændringer går gennem den eksisterende pipeline: rådata-CSV i `data/` → `scripts/build_master_csv.py` → `data/master_indicators.csv` → webapp læser via `webapp/lib/data.ts`. UI-definitioner ligger i `webapp/lib/shared.ts`. Tekst/artikel er nye eller ændrede Next.js-sider. Ingen ny backend, alt static export.

**Tech stack:** Python 3 (stdlib + geopandas til Fase 5), Next.js 16 static export, Tailwind 4, TypeScript.

**Deploy:** Som altid - gem, preview lokalt, commit + push via GitHub Desktop, Netlify deployer.

---

## Faseoversigt og anbefalet rækkefølge

| Fase | Indhold | Indsats | Risiko | Model |
|------|---------|---------|--------|-------|
| 1 | Biodiversitet → bioscore (2 tærskler) | ~1 time | Lav (data ligger klar) | Sonnet |
| 2 | Metode-side: ærlighedsnoter | ~30 min | Lav (kun tekst) | Haiku/Sonnet |
| 3 | Offentlig artikel + fravalgs-dokument | ~2 timer | Lav (indhold) | Sonnet |
| 4 | Absolutte grænser (areal; næring afklares) | Design-beslutning først | Mellem (påvirker mange scores) | Opus |
| 5 | VP3 vandkvalitet (ny indikator) | 3-5 timer | Mellem-høj (download + spatial join) | Sonnet |

**Anbefaling:** Tag Fase 1-3 først som én leverance (alt verificeret, lav risiko, høj formidlingsværdi). Fase 4 kræver en designbeslutning fra August før kodning. Fase 5 er det tungeste og kan vente.

---

## Vigtige fakta verificeret under analysen (læs før du går i gang)

1. **Bioscore-data ligger ALLEREDE i repoet**: `data/biodiversitet_scores.csv` har alle 98 kommuner med kolonnerne `pct_vasentlig_natur` (bioscore ≥8), `pct_uerstattelig_natur` (bioscore ≥12), `biodiversitet_ratio` og `uerstattelig_ratio`. Filen er bare ikke koblet på pipelinen - den nuværende `biodiversitet`-dimension bruger `land_use_scores.csv` (rent arealdække).
2. **Øko-baren klipper ved ratio 200** (`Math.min(score/200, 1)` i ScoreBars.tsx) og farven bliver rød ved >100. Men det viste TAL er `score.toFixed(1)`. Bioscore-ratioerne kan blive ekstreme (Morsø `uerstattelig_ratio` = 20000 fordi pct = 0,05%). **Derfor skal bio-ratioerne cappes** ved indlæsning, ellers viser UI'et "20000.0" og build-valideringen (>2000) brokker sig. Vi capper ved 300.
3. **`is_dimension_score`-flaget i build_master_csv.py bruges ikke** - dimension-scoren beregnes altid som worst-of (max) af alle sub-ratioer for dimensionen. For en dimension med to bioscore-tærskler bliver scoren altså worst-of automatisk.
4. **Arealsystem-grænsen er 15% antropiseret areal** (Rockström 2009 / Dao et al. 2015). DK ligger på 73-75% = 5,2x overskridelse. Antropiseret = cropland + bebygget = vores `intensiv_pct` + `bebygget_pct`. Denne grænse KAN anvendes per kommune.
5. **Næringsstof-grænsen kan IKKE downscales rent**: rapportens absolutte N-grænse (37.900 ton N/år til kyst) er et nationalt budget. Per-kommune kræver NOVANA-oplandsdata vi ikke har. Fase 4 dækker derfor reelt kun areal; næring forklares som fravalg.
6. **BII (de 44%) kan ikke laves per kommune**: NHM's data er 0,25° opløsning (~430 km²/celle, større end mange kommuner), et globalt modelestimat med usikkerhed 41-61%. Bekræftet ved direkte API-opslag i NHM's database. Hører til i artiklen/fravalgs-dokumentet, ikke som indikator.

---

## Fase 1: Biodiversitet → bioscore

**Mål:** Erstat den nuværende "% naturareal mod 30%"-indikator med DCE's bioscore i to tærskler: væsentlig naturværdi (≥8) mod 30%-målet og uerstattelig naturværdi (≥12) mod 10%-målet. Worst-of bestemmer dimensionsscoren.

**Filer:**
- Ændr: `scripts/build_master_csv.py` (erstat biodiversitet-entry, tilføj cap-logik)
- Ændr: `webapp/lib/shared.ts:803-815` (ECOLOGICAL_DIMENSIONS biodiversitet)
- Ændr: `webapp/lib/data.ts:50-51` (ECO_RAW_KEY_MAP)
- Verifikation: `data/master_indicators.csv` (genereret) + preview

- [ ] **Step 1: Tilføj cap-felt-håndtering i build_master_csv.py**

I `scripts/build_master_csv.py`, i den økologiske sub-indikator-løkke, find blokken der beregner `ratio` (omkring linje 379-384):

```python
            else:
                csv_ratio = parse_float(r.get(ind["ratio_col"])) if ind["ratio_col"] else None
                if ind.get("inverse_ratio") and csv_ratio is not None:
                    ratio = invert_to_direct_ratio(csv_ratio)
                else:
                    ratio = csv_ratio
```

Tilføj cap-logik LIGE EFTER denne blok (før `if ratio is None and raw is None:`):

```python
            # Cap ekstreme eco-ratioer (fx bioscore med pct nær 0 giver ratio i tusinder).
            # Baren klipper alligevel ved 200; cap holder det viste tal og validering pæn.
            cap = ind.get("cap")
            if cap is not None and ratio is not None and ratio > cap:
                ratio = float(cap)
```

- [ ] **Step 2: Erstat biodiversitet-entry i ECO_SUB_INDICATORS**

I `scripts/build_master_csv.py`, find den nuværende entry (linje 152-153):

```python
    # === Biodiversitet (single - bruger naturareal) ===
    {"id": "biodiversitet", "csv": "land_use_scores.csv", "ratio_col": "land_use_ratio", "raw_col": "natur_pct", "unit": "%", "data_year": "2022", "source": "DST AREALDK2 + ARE207", "category": "ecological", "dimension": "biodiversitet", "inverse_ratio": False, "is_dimension_score": True},
```

Erstat den med to entries (bioscore-tærskler, begge cappet ved 300):

```python
    # === Biodiversitet (worst-of: væsentlig + uerstattelig naturværdi, DCE bioscore) ===
    # Kilde: DCE Biodiversitetskort (Bioscore-raster, AU/DCE SR456). Måler habitatkvalitet,
    # ikke rent arealdække. To tærskler matcher CONCITO/EU's biodiversitetsmål:
    #   ≥8  = "væsentlige naturværdier"   → mod 30%-målet (biodiversitet_ratio)
    #   ≥12 = "uerstattelige levesteder"  → mod 10%-målet (uerstattelig_ratio)
    {"id": "bio_vasentlig",    "csv": "biodiversitet_scores.csv", "ratio_col": "biodiversitet_ratio", "raw_col": "pct_vasentlig_natur",    "unit": "%", "data_year": "2021", "source": "DCE Biodiversitetskort (bioscore)", "category": "ecological", "dimension": "biodiversitet", "inverse_ratio": False, "is_dimension_score": False, "cap": 300},
    {"id": "bio_uerstattelig", "csv": "biodiversitet_scores.csv", "ratio_col": "uerstattelig_ratio", "raw_col": "pct_uerstattelig_natur", "unit": "%", "data_year": "2021", "source": "DCE Biodiversitetskort (bioscore)", "category": "ecological", "dimension": "biodiversitet", "inverse_ratio": False, "is_dimension_score": False, "cap": 300},
```

- [ ] **Step 3: Kør build-scriptet**

Run (fra projektets rodmappe):
```bash
cd /Users/augustseptimiuskrogh/Documents/GitHub/doughnut
python3 scripts/build_master_csv.py
```
Forventet: scriptet printer `bio_vasentlig: 98/98` og `bio_uerstattelig: 98/98` (eller tæt på - 6 kommuner kan mangle), og til sidst `✓ Skrev ... rækker`. Valideringen skal IKKE vise ratio-værdier over 2000 (cap virker).

- [ ] **Step 4: Verificér master-CSV indeholder de nye rækker og at gammel er væk**

Run:
```bash
grep "787,Thisted,bio_" /Users/augustseptimiuskrogh/Documents/GitHub/doughnut/data/master_indicators.csv
grep "787,Thisted,_dim_biodiversitet" /Users/augustseptimiuskrogh/Documents/GitHub/doughnut/data/master_indicators.csv
```
Forventet: to `bio_vasentlig`/`bio_uerstattelig`-rækker for Thisted (raw 22.47 og 11.92), og en `_dim_biodiversitet`-række med worst-of (133.51, da det er den dårligste af 133.51 og 83.89). Ingen `biodiversitet`-sub-række med `natur_pct` længere.

- [ ] **Step 5: Opdater ECO_RAW_KEY_MAP i data.ts**

I `webapp/lib/data.ts`, find linje 50-51:

```typescript
  // Biodiversitet (single)
  biodiversitet: { rawKey: "eco_bio_raw", ratioKey: "biodiversitet_self" },
```

Erstat med:

```typescript
  // Biodiversitet (worst-of: væsentlig + uerstattelig naturværdi, DCE bioscore)
  bio_vasentlig:    { rawKey: "eco_bio_vasentlig_raw",    ratioKey: "bio_vasentlig_ratio" },
  bio_uerstattelig: { rawKey: "eco_bio_uerstattelig_raw", ratioKey: "bio_uerstattelig_ratio" },
```

- [ ] **Step 6: Opdater biodiversitet-dimensionen i shared.ts**

I `webapp/lib/shared.ts`, find biodiversitet-blokken (linje 803-815) og erstat hele objektet med:

```typescript
  {
    id: "biodiversitet",
    name: "Biodiversitet",
    shortName: "BIO",
    description: "Andel af kommunens areal med væsentlig og uerstattelig naturværdi for truede arter, målt med DCE's biodiversitetskort (bioscore). Worst-of logik. Måler habitatkvalitet, ikke rent arealdække - en biologisk fattig plantage tæller derfor ikke som høj natur. Grænserne er EU's politiske mål (30%/10%), ikke den planetære grænse - se metodesiden.",
    source: "https://dce.au.dk/udgivelser/vr/nr-101-150/abstracts/nr-112-biodiversitetskort-for-danmark",
    sourceLabel: "DCE Biodiversitetskort (bioscore)",
    unit: "% af areal med naturværdi",
    boundary: "30% væsentlig naturværdi + 10% uerstattelig (EU Biodiversitetsstrategi 2030)",
    subIndicators: [
      { rawKey: "eco_bio_vasentlig_raw",    ratioKey: "bio_vasentlig_ratio",    label: "Væsentlig naturværdi (bioscore ≥8)",    unit: "%", boundary: "Mål: 30% (EU Biodiversitetsstrategi 2030)", lowerIsBetter: false },
      { rawKey: "eco_bio_uerstattelig_raw", ratioKey: "bio_uerstattelig_ratio", label: "Uerstattelig naturværdi (bioscore ≥12)", unit: "%", boundary: "Mål: 10% strengt beskyttet (EU 2030)",     lowerIsBetter: false },
    ],
  },
```

- [ ] **Step 7: Start dev-server og verificér i preview**

Brug preview-værktøjet (eller dobbeltklik `Start udviklerserver.command`). Gå til en kommuneside, fx `http://127.0.0.1:3000/kommune/Thisted`. Klik på "Biodiversitet" under Økologisk loft. Forventet: to sub-indikatorer ("Væsentlig naturværdi (bioscore ≥8)" = 22,47%, "Uerstattelig naturværdi (bioscore ≥12)" = 11,92%), dimensionsscoren = worst-of, ingen ekstreme tal som 20000, og baren rendrer korrekt (rød/amber/grøn efter score).

- [ ] **Step 8: Commit**

Commit via GitHub Desktop (IKKE terminal-git). Filer: `scripts/build_master_csv.py`, `data/master_indicators.csv`, `webapp/lib/data.ts`, `webapp/lib/shared.ts`. Besked: `feat: biodiversitet bruger nu DCE bioscore (2 tærskler) i stedet for naturareal`.

---

## Fase 2: Metode-side - ærlighedsnoter

**Mål:** Tilføj tre korte, ærlige noter på metodesiden så besøgende forstår grænsernes karakter. Ingen kode, kun tekst.

**Filer:**
- Ændr: `webapp/app/metode/page.tsx` (biodiversitet-sektionen + en generel note)

- [ ] **Step 1: Læs metodesidens nuværende biodiversitet-sektion**

Run: åbn `webapp/app/metode/page.tsx` og find sektionen med `id="biodiversitet"` (eller teksten om naturareal/30%-målet). Noter den omkringliggende JSX-struktur (typisk en `<section>` med overskrift og `<p>`-afsnit).

- [ ] **Step 2: Erstat biodiversitet-sektionens brødtekst**

Erstat beskrivelsen i biodiversitet-sektionen med denne tekst (tilpas JSX-wrapping til sidens eksisterende mønster - typisk `<p className="...">`):

> Biodiversitet måles med DCE's biodiversitetskort (bioscore), der vurderer hvor værdifuldt hvert areal er som levested for truede arter. Vi bruger to tærskler: andelen af kommunen med væsentlig naturværdi (bioscore ≥8) holdt op mod EU's 30%-mål, og andelen med uerstattelig naturværdi (bioscore ≥12) holdt op mod 10%-målet for strengt beskyttet natur. Den dårligste af de to bestemmer dimensionens score (worst-of).
>
> **Vigtigt om grænsen:** De 30% og 10% er EU's politiske mål, ikke den planetære grænse. CONCITO-rapporten (2025) vurderer Danmarks samlede biodiversitet til et Biodiversity Intactness Index på 44% mod en sikker planetær grænse på 90%. En kommune kan altså nå 30%-målet og lyse grønt her uden at være inden for den biofysiske grænse. Den planetære grænse (BII) er et groft globalt modelestimat (0,25° opløsning, usikkerhed 41-61%) og kan ikke beregnes per kommune - derfor bruger vi det lokalt forankrede bioscore-kort i stedet. Læs mere i [artiklen om planetære grænser](/artikel/planetaere-graenser).

- [ ] **Step 3: Tilføj en generel note om absolutte vs. relative grænser**

Find toppen af metodesidens økologiske afsnit (eller et passende intro-sted). Tilføj en kort boks/afsnit:

> **Om grænserne i det økologiske loft:** Nogle dimensioner måles mod absolutte grænser (WHO's luftgrænser, EU's genanvendelsesmål, drikkevandsnormen). Andre måles mod landsgennemsnittet, fordi der ikke findes en meningsfuld absolut grænse på kommuneniveau. Det betyder at en grøn score på en relativ dimension viser "bedre end de fleste kommuner" - ikke nødvendigvis "bæredygtig". Danmark som helhed overskrider de fleste planetære grænser, jf. CONCITO-rapporten.

- [ ] **Step 4: Verificér i preview**

Gå til `http://127.0.0.1:3000/metode`. Bekræft at de nye afsnit vises korrekt, at linket til artiklen virker (eller peger på `/artikel/planetaere-graenser` som oprettes i Fase 3), og at der ingen em-dash er (kun enkelt dash).

- [ ] **Step 5: Commit**

Via GitHub Desktop. Fil: `webapp/app/metode/page.tsx`. Besked: `docs: ærlige metodenoter om politiske vs planetære grænser`.

---

## Fase 3: Offentlig artikel + fravalgs-dokument

**Mål:** (a) Udgiv en læsbar artikel på platformen der formidler CONCITO-analysen. (b) Gem et internt fravalgs-/roadmap-dokument så analysen og de bevidste fravalg ikke glemmes.

**Filer:**
- Opret: `docs/concito-analyse-og-roadmap.md` (internt dokument)
- Opret: `webapp/app/artikel/planetaere-graenser/page.tsx` (offentlig artikel)
- Ændr: `webapp/app/layout.tsx:35-46` (navigation - link til artiklen)

### Del A: Internt fravalgs-/roadmap-dokument

- [ ] **Step 1: Opret docs/concito-analyse-og-roadmap.md**

Opret filen med følgende indhold:

```markdown
# CONCITO-rapporten: analyse, gennemførte forbedringer og fravalg

Kilde: CONCITO (2025), "Downscaling planetary boundaries to national level - the case of Denmark".
Analyse foretaget juni 2026. Dette dokument er den durable hukommelse over hvad vi kan/ikke kan
bruge fra rapporten på kommuneniveau, og hvilke bevidste fravalg vi har taget.

## Hvad rapporten gør
Rapporten nedskalerer 6 af de 9 planetære grænser til dansk nationalt niveau: klima, biosfærens
integritet, arealsystem, ferskvand, biogeokemiske strømme (N+P) og aerosoler/luft. Konklusion:
Danmark overskrider de fleste grænser markant, og under et ansvarsprincip er flere budgetter
allerede opbrugt.

## Gennemført (på platformen)
- **Biodiversitet → bioscore**: skiftet fra rent naturareal (% arealdække) til DCE's biodiversitetskort
  med to tærskler (≥8 mod 30%, ≥12 mod 10%). Mere lokalt forankret og kvalitetsvægtet. Se Fase 1.
- **Metodenoter**: tydeliggjort at grænserne er politiske mål, ikke planetære grænser, og at DK
  samlet er i overskridelse.
- **Artikel**: offentlig formidling af analysen (/artikel/planetaere-graenser).

## Kan implementeres senere (data findes)
- **VP3 vandkvalitet per kommune**: andel vandområder i god økologisk tilstand. Shapefile bekræftet
  tilgængelig (https://files-miljoegis.mim.dk/vp3_2e2025/vp3_2e2025.zip, 387 MB). Kræver geopandas
  spatial join kommune × vandområde. Meget dansk og kommunikerbart (iltsvind). Se Fase 5.
- **Absolut arealgrænse (15% antropiseret)**: rapportens arealsystem-grænse kan anvendes per kommune
  (intensiv + bebygget vs 15%). DK på 73-75%. Designbeslutning udestår - se Fase 4.

## Fravalgt - med begrundelse (så det ikke genovervejes uden grund)
- **BII/MSA/HANPP per kommune**: UMULIGT. Globale modeller; BII er 0,25° opløsning (~430 km²/celle,
  større end mange kommuner), usikkerhed 41-61%, et modelestimat ikke en måling. Verificeret via
  NHM's database (Phillips et al. 2021, DOI 10.5519/HE1EQMG1). Hører til som national kontekst i
  artiklen, ikke som indikator.
- **§3 beskyttet natur som egen indikator**: REDUNDANT. Bioscore (gennemført) dækker reelt det samme
  (kvalitet/beskyttelsesværdi) bedre. §3-data findes dog via WFS (dai:bes_naturtyper) hvis ønsket.
- **Absolut N-grænse per kommune**: IKKE MULIGT rent. Rapportens N-grænse (37.900 ton N/år til kyst)
  er et nationalt budget; per-kommune kræver NOVANA-oplandsdata vi ikke har. Vores spildevands-N/P +
  VP3 N-loft (mod landsgennemsnit) er det vi kan gøre.
- **Forbrugsbaseret areal/biodiversitet/N/vand**: IKKE PER KOMMUNE. Kræver EXIOBASE-input-output på
  nationalt niveau. Vi har forbrugsbaseret CO2 som estimat; resten er uden for MVP.
- **Jordsundhed (soil health)**: INGEN KOMMUNEDATA. Mangler også i rapporten. Kendt hul.
- **Drænede landbrugsarealer**: KUN NATIONALT ESTIMAT (~52%). Ingen ren kommuneopdeling.
- **Kystpres (coastal squeeze)**: INGEN INDIKATOR. Relevant for kystkommuner, men intet rent datagrundlag.
- **Fair-share / historisk ansvar**: FRAMING, IKKE INDIKATOR. Vigtig pointe (DK har negativt restbudget
  under ansvarsprincippet), hører til i artikel/metode, ikke som tal per kommune.

## Hvor vi er foran rapporten
- Vores `forurening`-dimension dækker novel entities (pesticider i grundvand), som rapporten helt
  sprang over som for umoden. Vores `forbrug_co2` er præcis den forbrugsbaserede linse rapporten
  efterlyser.
```

- [ ] **Step 2: Verificér filen er gemt og læsbar**

Run:
```bash
head -20 /Users/augustseptimiuskrogh/Documents/GitHub/doughnut/docs/concito-analyse-og-roadmap.md
```
Forventet: indholdet vises.

### Del B: Offentlig artikel

- [ ] **Step 3: Opret artikel-siden**

Opret `webapp/app/artikel/planetaere-graenser/page.tsx`. Brug samme side-mønster som `webapp/app/om/page.tsx` (læs den først for at matche container/typografi-klasser). Artiklens indhold (dansk, ingen em-dash):

**Titel:** "Hvor langt er Danmark fra de planetære grænser?"

**Manchet:** En ny CONCITO-rapport omsætter de ni planetære grænser til danske tal. Her er hvad den viser, hvad vores platform allerede måler, og hvad der bevidst ikke kan måles på kommuneniveau.

**Afsnit 1 - De planetære grænser, kort:** Forklar de 9 grænser (Richardson et al. 2023) og at CONCITO nedskalerer 6 til Danmark: klima, biodiversitet, arealsystem, ferskvand, næringsstoffer (N+P) og luft. Pointe: Danmark overskrider de fleste.

**Afsnit 2 - Territorial vs. forbrug:** Forklar at det forbrugsbaserede aftryk (inkl. import) er 2-5x højere end det territoriale. Sojaimport alene lægger beslag på ~18% af DK's areal i udlandet; dansk forbrug optager 203% af DK's eget areal. Vores platform måler mest territorialt, men har forbrugsbaseret CO2 med.

**Afsnit 3 - Biodiversitet: hvorfor 44% ikke kan blive til kommunetal:** Forklar BII (Biodiversity Intactness Index) = andel oprindelige arter tilbage. DK = 44% mod en grænse på 90%. MEN: det er et groft globalt modelestimat (0,25° celler større end mange kommuner, usikkerhed 41-61%), ikke en dansk måling. Derfor bruger vi DCE's danske biodiversitetskort (bioscore) i stedet - lokalt forankret, men målt mod EU's politiske mål (30%/10%), ikke den planetære grænse.

**Afsnit 4 - Areal:** Rapportens grænse er 15% antropiseret areal (bebygget + landbrug). Danmark ligger på 73-75% - en 5-dobbelt overskridelse. Vores arealdimension viser fordelingen per kommune.

**Afsnit 5 - Det vi ikke kan måle (og hvorfor):** Ærligt afsnit. Forbrugsbaserede aftryk, jordsundhed, drænede arealer, kystpres og fair-share/historisk ansvar kan ikke gøres meningsfuldt op per kommune med eksisterende data. Vi nævner dem her, så de ikke glemmes.

**Afsnit 6 - Hvad du kan bruge platformen til:** Den viser hver kommunes relative position. En grøn score betyder "bedre end de fleste danske kommuner", ikke nødvendigvis "inden for planetens grænser". De to ting skal ikke forveksles.

**Kilde-fodnote:** Link til CONCITO-rapporten og DCE Biodiversitetskort.

Skriv hvert afsnit som færdig dansk brødtekst (2-4 sætninger pr. afsnit udover stikordene ovenfor). Tilføj `export const metadata = { title: "Planetære grænser og Danmark" }`.

- [ ] **Step 4: Tilføj artiklen til navigationen**

I `webapp/app/layout.tsx`, find `<nav>` (linje 35-46). Tilføj et link efter "Metode & data"-linket:

```tsx
                  <a href="/artikel/planetaere-graenser" className="text-gray-500 hover:text-gray-900 transition-colors">
                    <span className="sm:hidden">Artikel</span>
                    <span className="hidden sm:inline">Planetære grænser</span>
                  </a>
```

- [ ] **Step 5: Verificér i preview**

Gå til `http://127.0.0.1:3000/artikel/planetaere-graenser`. Bekræft at siden rendrer, navigationslinket virker, og at linket fra metodesiden (Fase 2) lander her. Tjek mobilvisning med preview_resize.

- [ ] **Step 6: Commit**

Via GitHub Desktop. Filer: `docs/concito-analyse-og-roadmap.md`, `webapp/app/artikel/planetaere-graenser/page.tsx`, `webapp/app/layout.tsx`. Besked: `feat: artikel om planetære grænser + internt fravalgs-dokument`.

---

## Fase 4: Absolutte grænser (areal) - KRÆVER DESIGNBESLUTNING FØRST

**Status:** Ikke klar til kodning. Der er en reel designbeslutning August skal tage, fordi den ændrer mange kommuners scores og platformens grundlogik.

**Fundet:** Rapportens arealgrænse er 15% antropiseret areal (intensiv + bebygget). DK ligger på 73-75%. Hvis vi indfører den som absolut grænse, vil stort set ALLE kommuner lyse dybrødt på areal - korrekt ift. den planetære virkelighed, men det fjerner forskellen mellem kommuner.

**Tre designmuligheder:**

1. **Tilføj som ekstra sub-indikator** "Antropiseret areal (mod 15%-grænse)" ved siden af de nuværende to (intensiv + bebygget mod landsgennemsnit). Worst-of vil så domineres af 15%-grænsen → alle røde. Ærligt, men udifferentieret.
2. **Erstat landsgennemsnit med 15%-grænsen** helt. Samme effekt: alle røde, ingen differentiering.
3. **Behold landsgennemsnit som score, vis 15%-grænsen som kontekst** i sub-indikatorens boundary-tekst og på metodesiden. Bevarer differentiering OG ærlighed. **Anbefalet.**

**Næringsstoffer:** Frafalder som absolut grænse - rapportens N-grænse er national (37.900 ton/år til kyst) og kan ikke downscales uden NOVANA-oplandsdata. Dokumenteres som fravalg (gjort i Fase 3).

- [x] **Step 1: August valgte mulighed 3 (18. juni 2026).** GENNEMFØRT: 15%-grænsen vises nu som kontekst i arealanvendelse-dimensionens `boundary` (shared.ts) og i metodesidens ECO_METHODS-entry. Ingen ændring i scoring - kommune-scores er uændrede. Næringsstoffer frafaldt som absolut grænse (nationalt N-budget, kan ikke downscales).

---

## Fase 5: VP3 vandkvalitet (ny indikator) - GENNEMFØRT

**Status (18. juni 2026): FÆRDIG.** Implementeret som et effektmål-indikator under "Næringsstoffer" (var først egen dimension "Overfladevand", men flyttet efter Augusts spørgsmål om alignment - vandtilstand er eutrofieringens synlige effekt, som CONCITO måler under nærings-grænsen, ikke en selvstændig planetær grænse). Spike afslørede at de tre `_samlet`-lag (vandløb/søer/marin) har `til_oko_sm` (økologisk tilstand) og `kom1-4` (kommunenavne), så ingen spatial join var nødvendig. Alle 98 kommunenavne matcher vores liste eksakt. Nationalt er kun ~5,8% af vandområder i god tilstand. Scoret mod landsgennemsnit (ratio = national_pct / kommune_pct × 100, cappet 300), EU's 2027-mål vist som kontekst. Datakilde-note: scriptet henter en 370 MB zip til systemets temp-mappe (IKKE committet) og skriver kun den lille `data/vp3_vandkvalitet_scores.csv` (committes).

**Mål:** Ny indikator/dimension: andel af kommunens vandområder (vandløb, søer, kystvande) i god økologisk tilstand iht. Vandområdeplan 3.

**Filer (forventet):**
- Opret: `scripts/fetch_vp3_vandkvalitet.py`
- Opret: `data/vp3_vandkvalitet_scores.csv` (genereret)
- Ændr: `scripts/build_master_csv.py` (ny entry)
- Ændr: `webapp/lib/shared.ts` (ny dimension eller sub-indikator)
- Ændr: `webapp/lib/data.ts` (ECO_RAW_KEY_MAP)
- Ændr: `webapp/app/metode/page.tsx`

- [ ] **Step 1 (SPIKE): Download og inspicér shapefilens struktur**

```bash
cd /Users/augustseptimiuskrogh/Documents/GitHub/doughnut
curl -o /tmp/vp3.zip "https://files-miljoegis.mim.dk/vp3_2e2025/vp3_2e2025.zip"
mkdir -p /tmp/vp3 && unzip -o /tmp/vp3.zip -d /tmp/vp3
python3 -c "import geopandas as gpd; import glob; [print(f, gpd.read_file(f).columns.tolist()) for f in glob.glob('/tmp/vp3/**/*.shp', recursive=True)]"
```
Forventet: liste af lag (vandløb, søer, kystvande) med kolonnenavne. Find kolonnen der angiver økologisk tilstand/målopfyldelse (typisk "tilstand", "samlet_til", "oekol_til" e.l.). NÅR strukturen er kendt, skriv resten af fasens steps (spatial join kommune × vandområde, beregn andel i god tilstand, ratio mod 100% god tilstand, gem CSV med auto_build_master). Geometri-CRS: transformér til EPSG:25832 og join mod DAWA-kommunegrænser (samme mønster som `fetch_biodiversitet_data.py:96-99`).

- [ ] **Step 2+:** Skrives efter spike. Mønster følger eksisterende eco-fetch-scripts: ratio-konvention hvor høj = dårlig (>100 overshoot), `auto_build_master()` til sidst, entry i build_master_csv.py, dimension/sub-indikator i shared.ts + data.ts, metodeside.

---

## Selv-review (udført ved skrivning)

- **Spec-dækning:** Alle fire brugervalgte dele dækket: biodiversitet (Fase 1), metodenoter (Fase 2), VP3 (Fase 5), absolutte grænser (Fase 4). Plus de to tilføjelser: fravalgs-dokument (Fase 3A) og artikel (Fase 3B). ✓
- **Type/navne-konsistens:** Nye indicator_ids `bio_vasentlig`/`bio_uerstattelig` bruges identisk i build_master_csv.py, data.ts (ECO_RAW_KEY_MAP-nøgle) og kobles til rawKeys `eco_bio_vasentlig_raw`/`eco_bio_uerstattelig_raw` og ratioKeys `bio_vasentlig_ratio`/`bio_uerstattelig_ratio` i både data.ts og shared.ts. ✓
- **Pladsholdere:** Fase 1-3 har konkret kode/tekst. Fase 4-5 er bevidst "beslutning/spike først" - ikke pladsholdere, men ærlig markering af at en beslutning/undersøgelse går forud for kodning. ✓
- **Verifikation:** Tilpasset projektets virkelighed (ingen pytest) - scriptkørsel + grep i master-CSV + preview. ✓
```
