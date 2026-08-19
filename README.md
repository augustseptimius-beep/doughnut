# Denmark's 98 Doughnuts

A public platform that places every Danish municipality inside the Doughnut
Economics framework: how well the social foundation is met, and how far the
ecological ceiling is exceeded.

The project was built by the climate team at Thisted Municipality under the
EU-funded LIFE ACT programme. It covers all 98 Danish municipalities using
open public data only.

**Live site:** built and deployed from this repository via Netlify.

---

## What the platform does

For each municipality the platform computes and displays:

- **13 social categories** (health, education, welfare, housing, democracy,
  culture, safety, civil society, equality, mobility, gender equality, climate
  adaptation, energy) built from **66 scored indicators**.
- **7 ecological dimensions** (climate impact, pollution, air quality,
  nutrients, water, land use, biodiversity), each downscaled from a planetary
  boundary to the municipal level.
- **16 context indicators** that are shown but deliberately not scored, because
  they describe a scored number rather than adding a new one.

Data comes from roughly 60 distinct public sources, chiefly Statistics Denmark
(Statistikbanken), the Danish Environmental Portal, GEUS Jupiter (groundwater),
the Danish Energy Agency, Energi Data Service, and Klimaregnskabet.dk.

## How the scoring works

Everything is expressed as a **ratio where 100 is the reference point**:

| | Meaning of 100 | Direction |
|---|---|---|
| Social indicators | national average, or an absolute target where a meaningful one exists | higher is better |
| Ecological indicators | the planetary boundary | lower is better, above 100 is overshoot |

Three properties are worth knowing before reading any number:

1. **The two halves run in opposite directions.** A social score of 110 is good;
   an ecological score of 110 means the boundary is exceeded. Colour thresholds
   are mirrored accordingly.
2. **Ecological dimensions use worst-of, not averages.** If any one
   sub-boundary within a dimension is exceeded, the whole dimension counts as
   exceeded. This is deliberate planetary-boundary logic. Pollution is the sole
   exception and uses an average, because its four sub-indicators measure
   unrelated pollution types.
3. **Social baselines are switchable, ecological ones are not.** The user can
   compare a municipality against the national average, the top ten
   municipalities, or its own DST municipality group. Ecological boundaries are
   absolute and never rescale.

Indicators scored against a fixed target rather than the national average are
flagged, and the interface labels them, so a reader can tell "better than
average" apart from "meets the target".

**The full normative rules live in
[`docs/arkitektur-og-beregningsregler.md`](docs/arkitektur-og-beregningsregler.md).**
Read that document before porting, forking, or changing any calculation. It is
written in Danish, as is most documentation in this repository.

## Repository layout

```
data/          CSV data. master_indicators.csv is the consolidated file the
               web app reads; the other CSVs are the per-source raw track.
               trend_indicators.csv holds the direction-of-travel arrows.
scripts/       Python fetchers, one or more per data source, plus the two
               build scripts that consolidate them.
docs/          Architecture, methodology and data-source mapping.
webapp/        Next.js 16 static site (App Router, Tailwind 4).
netlify.toml   Build configuration.
```

There is no database and no backend, apart from one Netlify function that
proxies the Klimaregnskabet.dk API so its key stays server-side. The site is a
fully static export; all 98 municipality pages are pre-rendered at build time.

## Running it locally

### Web app

Requires Node.js 20 or newer.

```bash
cd webapp
npm install
npm run dev
```

Open `http://127.0.0.1:3000`. Use the IP rather than `localhost`; on macOS the
latter can resolve to IPv6 and fail to connect.

To reproduce the production build:

```bash
cd webapp
npm run build      # static export to webapp/out/
```

`webapp/out/` is generated output and is not tracked in git. Netlify runs this
same build itself on every push.

If you need the Klimaregnskabet proxy function locally, copy
`webapp/.env.example` to `webapp/.env` and add your own API key. In production
the key is set as a Netlify environment variable.

### Data pipeline

Requires Python 3.9 or newer. The scripts use only the standard library.

**Scripts must be run from the repository root, not from `scripts/`.** They
write to `data/` using paths relative to the working directory.

Two sources need credentials, read from the environment and never stored in the
repository:

| Variable | Source | Used by |
|---|---|---|
| `KLIMAREGNSKABET_API_KEY` | Klimaregnskabet.dk | `fetch_climate_data.py`, `fetch_trend_history.py` |
| `UVM_API_TOKEN` | Uddannelsesstatistik | `fetch_udvidelse_data.py`, `fetch_trend_history.py` |

```bash
export KLIMAREGNSKABET_API_KEY="..."
export UVM_API_TOKEN="..."
```

Every other source is open and needs no key. A script that needs a missing
variable exits with a message naming the variable and where to obtain it; see
`scripts/api_noegler.py`.

```bash
python3 scripts/fetch_<source>_data.py    # fetch one source
python3 scripts/build_master_csv.py       # consolidate into master_indicators.csv
python3 scripts/build_trends_csv.py       # recompute direction arrows
```

Most fetchers call the consolidation step automatically and print
`✓ Master-CSV opdateret` when they do. If that line is missing, run
`build_master_csv.py` by hand.

`master_indicators.csv`, `trend_indicators.csv` and `data_years.json` are all
committed deliberately: the build reads from them, so the site can be rebuilt
without network access to any upstream API.

Before a data update, run the diagnostic:

```bash
python3 scripts/tjek_robusthed.py
```

It writes nothing and checks for five failure modes that all look identical from
the outside, where the platform appears healthy but a number is silently frozen:
scripts that no longer import, renamed source variables, discontinued source
tables, hard-coded years, and a year label that has drifted away from the data
it describes.

## Project status

This is a working MVP, in production and publicly reachable. It is deliberately
simple: static CSV plus build-time generation, no database, no user accounts, no
test framework. Verification is done through the production build, spot checks
against the master CSV, and browser inspection.

Two consequences a contributor should know about:

- CSV parsing is intentionally naive (`split(",")`) and breaks if a field
  contains a comma. This is acceptable only because the data is controlled.
- TypeScript runs in strict mode, but CSV parsing carries a number of `any`
  escapes.

Known gaps and open threads are tracked in
[`docs/aabne-traade-juni-2026.md`](docs/aabne-traade-juni-2026.md), and known
divergences between documentation and code are listed in section 6 of the
architecture document.

## Data sources and licensing

All indicator data comes from public Danish sources. Each row in
`data/master_indicators.csv` carries its own `source` and `data_year`, and
[`docs/statbank_doughnut_mapping.md`](docs/statbank_doughnut_mapping.md) maps
Statistics Denmark tables to indicators. Reuse of the underlying data is
governed by each publisher's own terms, not by this repository.

## Copyright and licence

Copyright belongs to **Thisted Municipality** (Thisted Kommune). The code was
developed by municipal staff as part of a EU-supportet LIFE ACT
project.

**No licence has been granted yet.** The terms of reuse are an open decision for
the municipality, and until it is made, no permission to copy, modify or
redistribute this code should be inferred from its public visibility. The
`package.json` `license` field is set to `UNLICENSED` to reflect this and does
not indicate an intention to withhold a licence permanently.

If you want to build on this work, please get in touch rather than assuming a
licence. Interest from other municipalities and from research projects is
welcome, and is part of why the decision is being taken deliberately.

## Contact

Climate team, Thisted Municipality.
