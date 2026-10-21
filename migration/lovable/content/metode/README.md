# Metode-tekster

Eneste hjem for metode-sidens prosa (spec afsnit 3, 4.4 og 8). Ret teksterne her, fx via Lovables chat: "ret begrænsningsteksten for luftkvalitet til ...".

| Mappe | Indhold | Filnavn |
|---|---|---|
| `generelt/` | Generelle afsnit. Rækkefølge: `METODE_GENERELT` i `registry/settings.ts` | id fra `METODE_GENERELT` |
| `dimensioner/` | Pr. kategori/dimension: afsnittene `## Beregning`, `## Grænseværdi`, `## Begrænsninger`, `## Datafil` (de der findes) | `<dimension_id>.md` |
| `indikatorer/` | Pr. indikator: begrundelse for valget (ét afsnit) | `<indicator_id>.md` |

Regler:
- Ren markdown, ingen HTML. `>`-blokcitat i `generelt/intro.md` renderes som fremhævet boks.
- `~` skrives `\~`, ellers gennemstreger GitHub og remark-gfm teksten mellem to tilder.
- Manglende fil = afsnittet udelades.
- Dataår, enheder og kildelinks skal ikke stå som fri tekst. De kommer fra registret og manifestet. Pladsholdere (`{{year:<id>}}` m.fl., spec 4.4) indføres i fase 4. Indtil da er teksterne en 1:1-kopi af det gamle site, inklusive de forældede steder, der er listet i `migration/fase1/rapport.md`.
