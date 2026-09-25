#!/usr/bin/env python3
"""
fetch_grundvandsdannelse.py - vandressourcen pr. kommune fra DK-modellen (HIP)
=============================================================================

Nævneren til vand-dimensionen: hvor meget vand der i gennemsnit siver ned til
grundvandet (infiltration til mættet zone) i kommunen, i mm pr. år.
fetch_vandindvinding_data.py sætter indvindingen i forhold til den.

DATAKILDE
---------
Hydrologisk Informations- og Prognosesystem (HIP), Klimadatastyrelsen og GEUS:
DK-modellen (version 2023), lag "infiltration" i WMS-tjenesten
hip_boundary_conditions_period_mean: "Infiltration til mættet zone (mm/år),
periodemidlet værdi for referenceperioden 1991-2020". Tallet er statisk og
skal kun hentes igen, når GEUS udgiver en ny modelversion.

Tjenesten kræver et gratis token fra Dataforsyningen. Det læses fra
miljøvariablen DATAFORSYNINGEN_TOKEN og må aldrig skrives ind i en fil i
repoet (CLAUDE.md pkt. 8). Filerne bag (GeoTIFF i 100 m) ligger på
Dataforsyningens FTP, som ikke kan nås fra alle miljøer. Derfor bruges WMS'ens
GetFeatureInfo, der giver modelværdien i ét punkt.

METODE
------
Kommunens gennemsnit er middelværdien af punkter i et regelmæssigt gitter
inden for kommunegrænsen (DAWA). Gitteret er tættere i små kommuner, så også
Frederiksberg får et stabilt tal: 2 km i kommuner på mindst 200 km², 1 km fra
50 km², ellers 500 m. Punkter uden modelværdi (søer, kyst) springes over.
Samsø og Læsø ligger uden for DK-modellen og får intet tal.
Punktværdierne gemmes i systemets temp-mappe, så en afbrudt kørsel kan
genoptages; --genhent henter forfra.

HVORFOR INFILTRATION TIL MÆTTET ZONE
------------------------------------
GEUS' egen udnyttelsesgrad (Henriksen m.fl. 2023, GEUS 2023/08) regnes mod
grundvandsdannelsen til det enkelte magasin, men HIP udstiller kun seks
sammenlagte modellag, og lagenes vertikale flow har ikke en dokumenteret
enhed i tjenesten. Infiltration til mættet zone er den vandmængde der
fornyes hvert år, og svarer til nævneren i EEA's vandudnyttelsesindeks
(WEI+: vandforbrug i forhold til den fornybare ferskvandsressource).
Se fetch_vandindvinding_data.py for grænsen og forbeholdene.

Brug (fra projektets rodmappe):
  DATAFORSYNINGEN_TOKEN=... python3 scripts/fetch_grundvandsdannelse.py

Output:
  data/grundvandsdannelse_scores.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import tempfile
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from api_noegler import hent_noegle, kraev_noegle  # noqa: E402
from kommuner import KOMMUNER  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "grundvandsdannelse_scores.csv"
CACHE = Path(tempfile.gettempdir()) / "hip_infiltration_punkter.json"

WMS = "https://api.dataforsyningen.dk/wms/hip_boundary_conditions_period_mean"
LAG = "infiltration"
DAWA_URL = "https://api.dataforsyningen.dk/kommuner?format=geojson"
PERIODE = "1991-2020"

TOKEN = hent_noegle("DATAFORSYNINGEN_TOKEN")
TOKEN_HJAELP = (
    "Token'et oprettes gratis under 'Min bruger' på https://dataforsyningen.dk. "
    "Sæt det som miljøvariabel; skriv det aldrig ind i en fil i repoet."
)


def gitter_m(areal_km2: float) -> int:
    if areal_km2 >= 200:
        return 2000
    if areal_km2 >= 50:
        return 1000
    return 500


def vaerdi(x: float, y: float) -> float | None:
    """Modelværdien i punktet (mm/år), eller None uden for modellen."""
    url = (f"{WMS}?token={TOKEN}&service=WMS&version=1.3.0&request=GetFeatureInfo"
           f"&layers={LAG}&query_layers={LAG}&styles=&crs=EPSG:25832"
           f"&bbox={x - 5000},{y - 5000},{x + 5000},{y + 5000}&width=101&height=101&i=50&j=50"
           f"&info_format=text/plain&format=image/png")
    for forsoeg in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                tekst = r.read().decode("utf-8", "replace")
            break
        except Exception:
            if forsoeg == 3:
                raise
            time.sleep(2 ** forsoeg)
    m = re.search(r"value_0 = '([-0-9.eE]+)'", tekst)
    if not m:
        return None
    v = float(m.group(1))
    return None if v <= -9990 else v


def punkter(geom, afstand: int) -> list[tuple[int, int]]:
    from shapely.geometry import Point
    from shapely.prepared import prep
    minx, miny, maxx, maxy = geom.bounds
    p = prep(geom)
    ud = []
    x0 = int(minx // afstand) * afstand + afstand // 2
    y0 = int(miny // afstand) * afstand + afstand // 2
    for x in range(x0, int(maxx) + afstand, afstand):
        for y in range(y0, int(maxy) + afstand, afstand):
            if p.contains(Point(x, y)):
                ud.append((x, y))
    return ud


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--genhent", action="store_true", help="Ignorér cachede punktværdier")
    ap.add_argument("--traade", type=int, default=6)
    args = ap.parse_args()
    kraev_noegle("DATAFORSYNINGEN_TOKEN", TOKEN, TOKEN_HJAELP)

    import geopandas as gpd
    kom = gpd.read_file(DAWA_URL).to_crs(25832)
    kom["kode"] = kom["kode"].astype(int).astype(str)
    kom = kom[kom["kode"].isin(KOMMUNER)].dissolve(by="kode")
    if len(kom) != 98:
        raise SystemExit(f"FEJL: fandt {len(kom)} kommuner i DAWA, ikke 98")

    cache: dict[str, float | None] = {}
    if CACHE.exists() and not args.genhent:
        cache = json.loads(CACHE.read_text())
        print(f"  {len(cache)} punktværdier fra cachen ({CACHE})")

    plan: dict[str, tuple[int, list[tuple[int, int]]]] = {}
    for kode, r in kom.iterrows():
        afstand = gitter_m(r.geometry.area / 1e6)
        plan[kode] = (afstand, punkter(r.geometry, afstand))
    alle = {f"{x},{y}" for _, pk in plan.values() for x, y in pk}
    mangler = sorted(alle - set(cache))
    print(f"  {len(alle)} punkter i alt, {len(mangler)} skal hentes")

    def hent(noegle: str) -> tuple[str, float | None]:
        x, y = map(int, noegle.split(","))
        return noegle, vaerdi(x, y)

    with ThreadPoolExecutor(max_workers=args.traade) as ex:
        for i, (k, v) in enumerate(ex.map(hent, mangler), 1):
            cache[k] = v
            if i % 500 == 0:
                CACHE.write_text(json.dumps(cache))
                print(f"    {i}/{len(mangler)}")
    CACHE.write_text(json.dumps(cache))

    rows = []
    for kode in sorted(KOMMUNER, key=int):
        afstand, pk = plan[kode]
        v = [cache[f"{x},{y}"] for x, y in pk if cache.get(f"{x},{y}") is not None]
        if len(v) < 5:
            # Samsø og Læsø ligger uden for DK-modellen. De får intet tal
            # frem for et gæt, og vand-dimensionen mangler for dem.
            print(f"  ⚠ {KOMMUNER[kode]}: {len(v)} punkter med værdi - uden for DK-modellen, springes over")
            rows.append([kode, KOMMUNER[kode], "", len(v), afstand, PERIODE])
            continue
        rows.append([kode, KOMMUNER[kode], round(sum(v) / len(v), 1), len(v), afstand, PERIODE])
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["kommune_kode", "kommune_navn", "infiltration_mm_aar", "punkter", "gitter_m", "periode"])
        w.writerows(rows)
    vals = [r[2] for r in rows if r[2] != ""]
    if len(vals) < 90:
        raise SystemExit(f"FEJL: kun {len(vals)} kommuner med værdi - er tjenesten ændret?")
    print(f"✓ {OUTPUT.relative_to(ROOT)}: {len(vals)}/98 kommuner, {min(vals)}-{max(vals)} mm/år")
    t = next(r for r in rows if r[0] == "787")
    print(f"  Thisted: {t[2]} mm/år ({t[3]} punkter)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
