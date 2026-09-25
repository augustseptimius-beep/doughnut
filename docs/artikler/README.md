# Metodeartikler

To artikler, der forklarer metoden bag Danmarks 98 Doughnuts og gennemgår dens svagheder. De er skrevet til nysgerrige læsere og tænkt som bilag, man kan downloade fra platformen.

- `metodeartikel-1-social-ring.docx`: den sociale ring (13 kategorier, 50 indikatorer).
- `metodeartikel-2-oekologisk-ring.docx`: den økologiske ring (7 dimensioner, 15 indikatorer).

Alle tal er beregnet på datafilerne ved commit 80a914c (25. september 2026). `analyse_artikler.py` genskaber tallene og figurerne i `figurer/`. Scriptet kræver numpy, pandas, scipy og matplotlib og køres fra rodmappen:

```bash
python3 docs/artikler/analyse_artikler.py
```

Opdateres data, passer tallene i artiklerne ikke længere. Kør scriptet og ret teksten, eller behold artiklerne som et øjebliksbillede af 25. september 2026.
