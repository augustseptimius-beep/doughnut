#!/usr/bin/env python3
"""
fetch_kystrisiko.py - forventet årlig skade fra havet i 2070 pr. indbygger
==========================================================================

Anden indikator under Klimatilpasning (ved siden af vejr_skader): hvor meget
oversvømmelse fra havet og kysterosion ventes at koste kommunen om året i 2070,
i kr. pr. indbygger. Kategorien måler kommunens restrisiko over for
klimaforandringerne: hvad der er tilbage, når det der allerede er gjort, er
regnet med. Se data/klimatilpasning.md.

DATAKILDE
---------
Kystdirektoratets Kystplanlægger, datapakke version 1 af 18. marts 2021
(https://kystplanlaegger.dk/webgis-og-data/hent-data). To rasterlag i
100 m × 100 m, enhed kr./år pr. celle ("forventet årlig skade", FÅS):
  Oversvømmelse/Risiko/Oversvømmelses_Risiko_2070.tif
  Erosion/Risiko/Erosions_risiko_2070.tif
Risikoen er skaden ved 50-, 100-, 1.000- og 10.000-årshændelser vægtet med
deres sandsynlighed, med havstigning efter RCP8.5.

Hvad modellen regner med (metoderapporten, januar 2023):
  - Diger og klitter indgår, fordi de ligger i Danmarks Højdemodel 2014-2015
    med kommunernes rettelser. Øvrig kystbeskyttelse indgår som udgangspunkt
    ikke, og ved kronisk erosion antages høfder og skråningsbeskyttelse at
    kollapse.
  - 2070 ændrer kun faren (havstigning), ikke sårbarheden: bygninger og
    værdier er dagens.
  - Tiltag efter højdemodellen slår ikke igennem, før Kystdirektoratet
    opdaterer kortlægningen. Tallet flytter sig derfor ikke år for år og har
    ingen retningspil.

Zip-filen er 4,3 GB. Scriptet henter kun de to lag (ca. 140 MB) med
HTTP-range-requests og gemmer dem i systemets temp-mappe; --genhent henter
forfra.

METODE
------
Cellerne summeres inden for DAWA's kommunegrænser (EPSG:25832). En celle
tilhører den kommune, dens centrum ligger i. Kystceller med centrum i havet
tildeles den kommune, de berører; uden den regel tabes ca. 2 % af
oversvømmelsesrisikoen og 13 % af erosionsrisikoen, fordi skaden ligger i
selve kystlinjen. Summen deles med folketallet 1. januar 2021, datapakkens år
(dst.folketal()).

Landstallet er Danmark som helhed: de 98 kommuners samlede risiko delt med
deres samlede folketal (skrives i kystrisiko_ref). Ratioen beregnes af
build_master_csv.py (invers: landstal / kommune × 100) med registrets loft på
100: en kommune med kystrisiko under landstallet eller ingen kystrisiko står
neutralt. Fravær af en fare er ikke robusthed ud over det sædvanlige, og med
det almindelige loft på 150 ville en kommune uden kyst få en bonus, der i
kategoriens gennemsnit udligner dens vejrskader.

Afhængigheder (ud over standardbiblioteket): numpy og rasterio.
  pip3 install numpy rasterio

Brug (fra projektets rodmappe):
  python3 scripts/fetch_kystrisiko.py [--genhent]

Output:
  data/kystrisiko_scores.csv
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dst import folketal  # noqa: E402
from kommuner import KOMMUNER  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "kystrisiko_scores.csv"
CACHE = Path(tempfile.gettempdir()) / "kystplanlaegger"

ZIP_URL = ("https://sftp.statens-it.dk/public/file/8zi0btrjy0skysr1g0slmq/"
           "Kystplanl%C3%A6gger_Datapakke.zip")
LAG = {
    "oversvoemmelse": "Kystplanlægger_Datapakke/Oversvømmelse/Risiko/Oversvømmelses_Risiko_2070.tif",
    "erosion": "Kystplanlægger_Datapakke/Erosion/Risiko/Erosions_risiko_2070.tif",
}
DAWA_URL = "https://api.dataforsyningen.dk/kommuner?format=geojson&srid=25832"
BEFOLKNINGSAAR = "2021"   # datapakkens år


class _RangeFil(io.RawIOBase):
    """Læsbar, søgbar fil over HTTP-range-requests, så zipfile kan læse
    indholdsfortegnelsen og enkelte filer uden at hente hele arkivet."""

    def __init__(self, url: str):
        self.url, self.pos = url, 0
        # Serverens HEAD-svar har længden af en HTML-side, ikke af filen, så
        # størrelsen læses af Content-Range på en range-GET.
        req = urllib.request.Request(url, headers={"Range": "bytes=0-0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            self.size = int(r.headers["Content-Range"].rsplit("/", 1)[1])

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        self.pos = {0: offset, 1: self.pos + offset, 2: self.size + offset}[whence]
        return self.pos

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        if n == 0 or self.pos >= self.size:
            return b""
        slut = min(self.pos + n, self.size) - 1
        for forsoeg in range(5):
            try:
                req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{slut}"})
                with urllib.request.urlopen(req, timeout=300) as r:
                    data = r.read()
                break
            except OSError as e:
                if forsoeg == 4:
                    raise
                print(f"  netværksfejl ({e}), prøver igen")
                time.sleep(2 ** forsoeg)
        self.pos += len(data)
        return data


def hent_lag(genhent: bool) -> dict[str, Path]:
    CACHE.mkdir(exist_ok=True)
    stier = {k: CACHE / Path(v).name for k, v in LAG.items()}
    mangler = [k for k, p in stier.items() if genhent or not p.exists()]
    if not mangler:
        print(f"  Rasterlag fra cachen ({CACHE})")
        return stier
    print("Henter Kystplanlæggerens risikolag for 2070 (range-requests i zip-filen)...")
    with zipfile.ZipFile(_RangeFil(ZIP_URL)) as z:
        for k in mangler:
            tmp = stier[k].with_suffix(".tmp")
            with z.open(LAG[k]) as src, open(tmp, "wb") as dst:
                while blok := src.read(8 << 20):
                    dst.write(blok)
            tmp.replace(stier[k])
            print(f"  {stier[k].name}: {stier[k].stat().st_size / 1e6:.0f} MB")
    return stier


def kommunegraenser(genhent: bool) -> list[tuple[dict, int]]:
    sti = CACHE / "dawa_kommuner_25832.geojson"
    if genhent or not sti.exists():
        print("Henter kommunegrænser (DAWA)...")
        with urllib.request.urlopen(DAWA_URL, timeout=300) as r:
            sti.write_bytes(r.read())
    gj = json.loads(sti.read_text(encoding="utf-8"))
    return [(f["geometry"], int(f["properties"]["kode"])) for f in gj["features"]
            if f["properties"]["kode"].lstrip("0") in KOMMUNER]


def summer_pr_kommune(stier: dict[str, Path], former) -> dict[str, dict[str, float]]:
    import numpy as np
    import rasterio
    from rasterio.features import rasterize

    ref = rasterio.open(stier["oversvoemmelse"])
    centrum = rasterize(former, out_shape=ref.shape, transform=ref.transform, fill=0, dtype="int32")
    beroert = rasterize(former, out_shape=ref.shape, transform=ref.transform, fill=0, dtype="int32",
                        all_touched=True)
    etiket = np.where(centrum > 0, centrum, beroert).ravel()
    ud: dict[str, dict[str, float]] = {k: {} for k in KOMMUNER}
    for navn, sti in stier.items():
        with rasterio.open(sti) as r:
            if r.transform != ref.transform or r.shape != ref.shape:
                raise RuntimeError(f"{sti.name} har ikke samme gitter som {stier['oversvoemmelse'].name}")
            a = r.read(1).astype("float64")
        a[~np.isfinite(a) | (a < 0)] = 0   # nodata er -3,4e38
        summer = np.bincount(etiket, weights=a.ravel(), minlength=1000)
        i_alt, tildelt = a.sum(), summer[1:].sum()
        print(f"  {navn}: {i_alt / 1e6:,.1f} mio. kr./år i alt, "
              f"{100 * tildelt / i_alt:.1f} % tildelt en af de 98 kommuner")
        for k in KOMMUNER:
            ud[k][navn] = float(summer[int(k)])
    return ud


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--genhent", action="store_true", help="hent rasterlag og kommunegrænser forfra")
    args = ap.parse_args()

    stier = hent_lag(args.genhent)
    risiko = summer_pr_kommune(stier, kommunegraenser(args.genhent))
    folk = {k: v for (k, a), v in folketal([BEFOLKNINGSAAR]).items() if k in KOMMUNER}
    manglende = [KOMMUNER[k] for k in KOMMUNER if not folk.get(k)]
    if manglende:
        sys.exit(f"FEJL: intet folketal {BEFOLKNINGSAAR} for {', '.join(manglende)}")

    total = {k: v["oversvoemmelse"] + v["erosion"] for k, v in risiko.items()}
    landstal = round(sum(total.values()) / sum(folk.values()), 2)
    print(f"  Landstal: {landstal:,.2f} kr. pr. indbygger pr. år "
          f"({sum(total.values()) / 1e6:,.0f} mio. kr./år, folketal 1. jan. {BEFOLKNINGSAAR})")

    rows = []
    for k, navn in KOMMUNER.items():
        raw = round(total[k] / folk[k], 2)
        rows.append({
            "kommune_kode": k, "kommune_navn": navn,
            "kystrisiko_oversvoemmelse_mio": round(risiko[k]["oversvoemmelse"] / 1e6, 3),
            "kystrisiko_erosion_mio": round(risiko[k]["erosion"] / 1e6, 3),
            "kystrisiko_raw": raw,
            "kystrisiko_ratio": 100.0 if raw == 0 else round(min(landstal / raw * 100, 100), 2),
            "kystrisiko_ref": landstal,
        })
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    s = sorted(rows, key=lambda r: -r["kystrisiko_raw"])
    print("\nHøjest risiko pr. indbygger:")
    for r in s[:6]:
        print(f"  {r['kommune_navn']}: {r['kystrisiko_raw']:,.0f} kr. → ratio {r['kystrisiko_ratio']}")
    nul = sum(1 for r in rows if r["kystrisiko_raw"] < 1)
    print(f"  {nul} kommuner under 1 kr. pr. indbygger (ingen kystrisiko af betydning)")
    print(f"\n  Gemt: {OUTPUT} ({len(rows)} kommuner)")


if __name__ == "__main__":
    main()
    # ───────────────────────────────────────────────────────────
    # AUTO-REBUILD af master_indicators.csv
    # ───────────────────────────────────────────────────────────
    try:
        from build_master_csv import auto_build_master
        auto_build_master()
    except Exception as _e:
        print(f"\n⚠ Kunne ikke auto-rebuild master-CSV: {_e}")
        print("  Rådata er gemt. Kør manuelt: python3 scripts/build_master_csv.py")
