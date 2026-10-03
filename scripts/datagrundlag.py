"""
datagrundlag.py - læs åbne grunddata fra datagrundlag.dk.

datagrundlag.dk (MapCentia, uofficiel) høster danske grunddata (DAGI, DAR, BBR
m.fl.) og lægger ugentlige snapshots som GeoParquet i en åben S3-bucket, uden
nøgler. Platformen bruger det som afløser for DAWA, der lukkede 1. juli 2026 og
nu svarer 410 Gone (CLAUDE.md pkt. 42).

Tre ting at vide:

1. Snapshots, ikke "seneste": hver kørsel finder det nyeste snapshot via
   STAC-kataloget, og scriptet der kalder, skal kvittere for datoen. En kørsel
   kan genskabes med `dato=` (det nyeste snapshot på eller før datoen).
2. Kilderne har hver deres vilkår. Angiv kilden (DAGI og DAR: Klimadatastyrelsen,
   via Datafordeleren) hvor tallene vises. Tjenesten kan være forsinket i
   forhold til kilden, og er ikke en myndighed.
3. DuckDB importeres først i forbindelse(), ikke ved import: et fetch-script der
   ikke bruger datagrundlag, må ikke fejle fordi pakken mangler (samme princip
   som indikatorregister.py og api_noegler.py).

Brug:
    from datagrundlag import snapshot, forbindelse
    url, dato = snapshot("dagi", "kommuneinddeling")
    con = forbindelse()
    con.execute(f"SELECT navn FROM read_parquet('{url}')")

Kræver `pip install duckdb`, kun til selve forespørgslen. På Python 3.9 er
den nyeste DuckDB 1.4.5; snapshot-forespørgslerne og GeoPackage-eksporten er
afprøvet på den.
"""

from __future__ import annotations

import json
import re
import urllib.request

BASE = "https://datagrundlag.s3.eu-west-1.amazonaws.com/filer/dk"
USER_AGENT = "DoughnutDK/1.0 (+https://github.com/augustseptimius-beep/doughnut)"
_SNAPSHOT = re.compile(r"_gc2_snapshot_date=(\d{4}-\d{2}-\d{2})")
_FILNAVN = re.compile(r"[A-Za-z0-9_.-]+\.parquet")


def _json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def snapshot(skema: str, relation: str, dato: str | None = None) -> tuple[str, str]:
    """(URL til GeoParquet-filen, snapshot-dato som ÅÅÅÅ-MM-DD).

    Uden `dato` det nyeste snapshot, ellers det nyeste på eller før datoen."""
    rod = f"{BASE}/schema={skema}/relation={relation}"
    samling = _json(f"{rod}/collection.json")
    datoer = sorted(m.group(1) for l in samling["links"] if l["rel"] == "item"
                    for m in [_SNAPSHOT.search(l["href"])] if m)
    if dato:
        datoer = [d for d in datoer if d <= dato]
    if not datoer:
        raise RuntimeError(f"datagrundlag.dk har intet snapshot af {skema}.{relation}"
                           + (f" på eller før {dato}" if dato else ""))
    valgt = datoer[-1]
    href = _json(f"{rod}/_gc2_snapshot_date={valgt}/item.json")["assets"]["data"]["href"]
    fil = href[2:] if href.startswith("./") else href
    # URL'en sættes ind i SQL hos den der kalder, så filnavnet fra kataloget
    # skal være et rent parquet-navn.
    if not _FILNAVN.fullmatch(fil):
        raise RuntimeError(f"Uventet filnavn i STAC-kataloget for {skema}.{relation}: {href!r}")
    return f"{rod}/_gc2_snapshot_date={valgt}/{fil}", valgt


def forbindelse(spatial: bool = True):
    """DuckDB-forbindelse der kan læse GeoParquet over HTTPS (og med `spatial`
    forstår geometrikolonnen, ST_Transform osv.)."""
    try:
        import duckdb
    except ImportError as e:
        raise SystemExit("FEJL: datagrundlag.dk læses med DuckDB. Installér: pip install duckdb") from e
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    if spatial:
        con.execute("INSTALL spatial; LOAD spatial;")
    return con
