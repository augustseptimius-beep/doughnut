"""
kommunegraenser.py - kommunernes grænser, ét sted.

Læser data/kommunegraenser_25832.gpkg. Otte scripts hentede indtil juli 2026
grænserne fra DAWA (api.dataforsyningen.dk/kommuner). DAWA lukkede 1. juli 2026
og svarer nu 410 Gone, så filen er hentet én gang fra DAGI via datagrundlag.dk
(scripts/hent_kommunegraenser.py) og ligger i git. Se CLAUDE.md pkt. 42.

Samme kolonner som DAWA's GeoJSON, så scripterne kun skifter hentningen ud:
  kode      fire cifre som tekst, "0787" (brug int(kode) eller lstrip("0"))
  navn      kommunenavn som DAGI skriver det (ens med DST's stavemåde)
  geometry  MultiPolygon

Brug:
    from kommunegraenser import hent_kommunegraenser
    kommuner = hent_kommunegraenser()          # EPSG:25832 (meter)
    kommuner = hent_kommunegraenser(crs=4326)  # længde/bredde

geopandas importeres først i funktionen, så et script der ikke bruger
grænserne, ikke fejler ved import (samme princip som indikatorregister.py).
"""

from __future__ import annotations

from pathlib import Path

from kommuner import KODER

FIL = Path(__file__).resolve().parent.parent / "data" / "kommunegraenser_25832.gpkg"
KVITTERING = FIL.with_suffix(".json")


def hent_kommunegraenser(crs: int = 25832):
    """GeoDataFrame med de 98 kommuner (kode, navn, geometry) i `crs`."""
    import geopandas as gpd

    kom = gpd.read_file(FIL)
    koder = {k.lstrip("0") for k in kom["kode"]}
    if koder != KODER:
        raise ValueError(f"{FIL.name} skal have præcis de 98 kommuner i data/kommuner.json. "
                         f"Mangler {sorted(KODER - koder)}, ekstra {sorted(koder - KODER)}. "
                         f"Genskab den med scripts/hent_kommunegraenser.py.")
    return kom if crs == 25832 else kom.to_crs(crs)
