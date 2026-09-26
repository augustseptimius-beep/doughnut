# Metodeartikler

To artikler, der forklarer metoden bag Danmarks 98 Doughnuts og gennemgår dens svagheder. De er skrevet til nysgerrige læsere. De er endnu ikke lagt på platformen; det sker først efter godkendelse.

- `metodeartikel-1-social-ring.docx`: den sociale ring (13 kategorier, 48 indikatorer).
- `metodeartikel-2-oekologisk-ring.docx`: den økologiske ring (7 dimensioner, 15 indikatorer).

Alle tal er beregnet på datafilerne ved commit bb573ec (26. september 2026), efter at Bolig blev målt som trangboethed, lavindkomst blev taget ud af Lighed, og UVM-indikatorernes landstal blev vægtet med elevtal. `analyse_artikler.py` genskaber tallene og figurerne i `figurer/`. Scriptet kræver numpy, pandas, scipy og matplotlib og køres fra rodmappen:

```bash
python3 docs/artikler/analyse_artikler.py
```

Opdateres data, passer tallene i artiklerne ikke længere. Kør scriptet og ret teksten, eller behold artiklerne som et øjebliksbillede af 26. september 2026.
