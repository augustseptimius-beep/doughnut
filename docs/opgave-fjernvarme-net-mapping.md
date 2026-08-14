# Opgave: Fjernvarme-fossilandel via net→kommune-mapping (de 18 fælles-net-kommuner)

> Selvstændig opgavebeskrivelse til en ny session. Forudsætter ingen kontekst ud over dette dokument
> og kodebasen. Skrevet 19. juni 2026. Datakilder og join er allerede verificeret (se nedenfor).

## Formål (én linje)

Giv de 18 "fælles-net"-kommuner deres FAKTISKE fjernvarme-fossilandel (fra det net der forsyner dem)
i stedet for det TJ-vægtede landsgennemsnit (~13,3 %) de bruger i dag.

## Baggrund: hvad findes i dag

`scripts/fetch_fjernvarme_mix.py` beregner fjernvarmens brændselsmix pr. kommune ud fra Energistyrelsens
EPT-anlægsfil (`ens.dk/media/7199/download`), aggregeret på `vaerk_kommune` (hvor ANLÆGGET står).
- 80 kommuner har egen varmeproduktion (status `ok`) og får deres lokale mix.
- 18 kommuner har ingen/ubetydelig egen produktion (status `fælles_net`, under 100 TJ) og får tom mix.

`scripts/fetch_bolig_fossil.py` beregner kommunens samlede fossile varmeafhængighed:
`direkte olie/gas% + (fjernvarme-dækning% × fjernvarme-fossil%)`. For de 18 fælles-net-kommuner bruger
den **det TJ-vægtede landsgennemsnit (~13,3 %)** som fjernvarme-fossil%, fordi der ikke er et lokalt mix.

## Problemet

EPT 7199 er opgjort ved PRODUKTIONSSTEDET. De 18 kommuner er reelt forsynet af store fælles net
(især "Storkøbenhavns Fjernvarme") der er overvejende affald + biomasse + varmepumper med LAV fossilandel.
Landsgennemsnittet (13,3 %) OVERVURDERER derfor deres fossilafhængighed.

**Konkret (verificeret):** Net 2 "Storkøbenhavns Fjernvarme" har i 2024 en fossilandel på **6,2 %**
(kul+olie+ledningsgas), ikke 13,3 %. Vægtet med ~60-95 % fjernvarme-dækning betyder det at metro-
kommunerne i dag fremstår ~4-6 procentpoint mere fossile end de er.

## Datakilden der løser det (allerede undersøgt)

**ENS "Fjernvarmenet 2022-2024": `https://ens.dk/media/8519/download`** (.xlsx, ~310 KB).
- Ark der skal bruges: **`125% metode`** (der er også `200% metode` og `Anvendte CO2 faktorer`).
- **Række 0 er en titel; den rigtige header er række 1 (0-indekseret); data fra række 2.**
- Nøglekolonne: **`Fvnet_nr`** = samme net-id som `fv_net` i EPT 7199 (verificeret: 2 = "Storkøbenhavns
  Fjernvarme" i begge filer). Dette er join'et.
- Indeholder pr. (net × år): `Fjernvarmenet_navn`, `År` (brug 2024), `Varmelevering til net samlet [TJ]`,
  `CO2-emission [kg/GJ(leveret til net)]`, og brændselsandele som **fraktioner 0-1** (skal ×100):
  `Kul`, `Olieprodukter`, `Ledningsgas1`, `Affald`, `Træ- og biomasseaffald`, `Halm`, `Skovflis`,
  `Træpiller`, `Biogas`, `Bioolie`, `Overskudsvarme`, `Solvarme`, `Geotermi`, `Omgivelsesvarme`, `Elektricitet`.
- VIGTIGT: Dette er fordelingen af LEVERET varme (forbrugssiden) - præcis det vi vil have, ikke produktion.

**EPT 7199** (`ens.dk/media/7199/download`, allerede brugt af `fetch_fjernvarme_mix.py`) har kolonnerne
`fv_net` (net-nr) og `fv_net_navn` på hver anlægsrække. Det er herfra vi finder hvilket net en kommunes
(reserve)kedel hænger på. NB: brug fv_net fra ENHVER anlægsrække for kommunen (også rækker med
`varmeprod_TJ = 0`), ikke kun produktionsrækker.

## Brændsels-kategori-mapping (8519 → projektets skema)

Hold det konsistent med `fetch_fjernvarme_mix.py`'s nuværende firdeling:
- **fossil** = `Kul` + `Olieprodukter` + `Ledningsgas1`
- **affald** = `Affald`
- **biomasse** = `Træ- og biomasseaffald` + `Halm` + `Skovflis` + `Træpiller` + `Biogas` + `Bioolie`
- **ren** = `Overskudsvarme` + `Solvarme` + `Geotermi` + `Omgivelsesvarme` + `Elektricitet`

## De 18 kommuner og deres net (allerede kortlagt fra 7199, 2024)

| Kode | Kommune | Net fra reservekedel (fv_net) | Tier |
|---|---|---|---|
| 147 | Frederiksberg | 2 Storkøbenhavns Fjernvarme | 1 |
| 151 | Ballerup | 2 Storkøbenhavn | 1 |
| 153 | Brøndby | 2 Storkøbenhavn | 1 |
| 157 | Gentofte | 2 Storkøbenhavn | 1 |
| 165 | Albertslund | 2 Storkøbenhavn | 1 |
| 185 | Tårnby | 2 Storkøbenhavn (+ 481 lokal) | 1 |
| 253 | Greve | 2 Storkøbenhavn | 1 |
| 269 | Solrød | 2 Storkøbenhavn (+ 339 Havdrup lokal) | 1 |
| 201 | Allerød | 17 Nordøstsjælland / 18 Hillerød-Farum-Værløse | 1 |
| 210 | Fredensborg | 17 Nordøstsjælland / 383 Humlebæk | 1 |
| 440 | Kerteminde | 79 Fjernvarme Fyn | 1 |
| 563 | Fanø | 126 Esbjerg-Varde Fjernvarme | 1 |
| 825 | Læsø | 359 Byrum Fjernvarme | 1 |
| 155 | Dragør | ingen plant → manuelt: 2 Storkøbenhavn | 2 |
| 163 | Herlev | ingen plant → manuelt: 2 Storkøbenhavn | 2 |
| 175 | Rødovre | ingen plant → manuelt: 2 Storkøbenhavn | 2 |
| 187 | Vallensbæk | ingen plant → manuelt: 2 Storkøbenhavn | 2 |
| 336 | Stevns | net = tomt i 7199 → undersøg i 8519 på navn, ellers behold landssnit | 3 |

13 kommuner er Tier 1 (net følger automatisk af reservekedlen). 4 er Tier 2 (lille manuel mapping til net 2).
1 (Stevns, ubetydelig) er uafklaret - behold landssnit hvis den ikke kan findes.

## Fremgangsmåde

1. **Verificér 8519 først** (de-risk): hent filen, åbn `125% metode`, bekræft header-rækken, at `Fvnet_nr=2`
   findes for 2024, og at fossilandel (kul+olie+ledningsgas) ≈ 6,2 %. Hvis ENS har ændret filen, stop og afklar.
2. **Byg `{net_nr: mix}` fra 8519** for 2024: for hvert net beregn fossil/affald/biomasse/ren-andel via
   kategori-mappingen ovenfor (andele er allerede 0-1, kræver ikke division).
3. **Byg kommune→net-mapping:**
   - Tier 1: i `fetch_fjernvarme_mix.py`, for hver fælles-net-kommune, læs fv_net fra dens anlægsrækker i 7199
     (enhver række, også varmeprod=0). Hvis flere net: vælg det med størst `Varmelevering til net samlet [TJ]`
     i 8519 (proxy for hvilket net der dominerer), ELLER metro-net 2 hvis et af dem er 2.
   - Tier 2: hardcode `{155:2, 163:2, 175:2, 187:2}` (Storkøbenhavns Fjernvarme).
   - Stevns (336): forsøg opslag i 8519 på navn; ellers behold landssnit-fallback.
4. **Udfyld mixet for de 18:** i stedet for tom mix, sæt deres `fjv_fossil_pct` (+ gerne hele firdelingen
   biomasse/affald/fossil/ren) fra det forsynende nets 8519-mix. Sæt evt. en ny status `net` (i stedet for
   `fælles_net`) så man kan se at tallet kommer fra nettet, ikke egen produktion.
5. **`fetch_bolig_fossil.py`:** ingen logikændring nødvendig - den læser allerede `fjv_fossil_pct` pr.
   kommune og falder kun tilbage på landssnit hvis den er tom. Når de 18 nu har en værdi, bruges den
   automatisk. Bekræft at landssnit-fallbacken stadig findes for evt. resterende huller (Stevns).
6. **Regenerér** `python3 scripts/build_master_csv.py` og verificér.

## Metodevalg (vigtigt - hold linjen fra denne uge)

- Brug **fossilandelen** (kul+olie+ledningsgas), IKKE 8519's `CO2-emission [kg/GJ]`. CO2-tallet tæller
  biomasse som ~0 (officiel opgørelse), hvilket strider mod projektets bevidste stance om ikke at kalde
  biomasse "grøn". Vi tæller kun det utvetydigt fossile. (CO2-kolonnen kan evt. vises som ekstra kontekst,
  men ikke i scoren.)
- Resultatet skal stadig fodre den ABSOLUTTE 0-mål-score i `bolig_fossil` (`100 − samlet_fossil%`).

## Scope-valg

- **Anbefalet (MVP):** ret KUN de 18 fælles-net-kommuner. De 80 "ok"-kommuner beholder deres lokale
  produktions-mix (for isolerede net er produktion ≈ levering, så forskellen er ubetydelig). Lille, sikker.
- **Ideelt (større):** flyt ALLE 98 kommuner til 8519's leverings-mix (forbrugsside) via fv_net. Renere og
  mere korrekt, men kræver net-mapping for alle (de fleste følger af 7199's fv_net) og håndtering af
  multi-net-kommuner. Overvej kun hvis Energi bliver en kerne-dimension.

## Filer der berøres (MVP-scope)

- `scripts/fetch_fjernvarme_mix.py` - hent + parse 8519; byg net-mix; map de 18 kommuner; udfyld deres mix.
- `data/fjernvarme_mix_scores.csv` - regenereres (de 18 får nu værdier).
- `data/bolig_fossil_scores.csv` + `data/master_indicators.csv` - regenereres (kører automatisk via pipelinen).
- Evt. `webapp/components/ScoreBars.tsx` - hvis status skifter fra `fælles_net` til `net`, så
  `EnergiKontekst` viser nettets mix i stedet for "Begrænset egen varmeproduktion"-noten.
- `webapp/app/metode/page.tsx` + `CLAUDE.md` - kort note om at fælles-net-kommuner nu bruger forsynende
  nets faktiske mix (8519) i stedet for landssnit.

## Verifikation

- Net 2's fossilandel ≈ 6,2 % (2024) - sanity-check mod dette tal.
- De 4 Tier-2-kommuner (Dragør, Herlev, Rødovre, Vallensbæk) får ~6 % fjernvarme-fossil (ikke 13,3 %).
- Deres samlede fossil-score i `bolig_fossil` falder tilsvarende (lidt højere score = mindre rød).
- `npm run build` (fra `webapp/`, dev stoppet): 104 sider, TypeScript rent.
- Browser-DOM på fx `/kommune/Dragør`: Energi-kontekstens fjernvarme-mix viser nettets fordeling.

## Køreregler (projektspecifikt)

- Kør scripts fra rodmappen; `npm run build` fra `webapp/`. Kør ikke build mens dev-server kører (delt `.next`).
- Aldrig terminal-git. Efterlad ændringer til Augusts GitHub Desktop.
- August kører ikke selv scripts - assistenten håndterer hele pipelinen.

## Effort

Medium. Selve net-mappingen er lille (13 auto + 4 manuelle + 1 valgfri). Hovedarbejdet er at parse 8519
korrekt (titel-række + fraktioner) og vælge net for multi-net-kommuner. Anbefalet model: **Sonnet**
(standard fetch/parse-arbejde; arkitektur og datakilder er allerede afklaret her).
