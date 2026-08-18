#!/usr/bin/env python3
"""
fetch_mobilitetsatlas.py

Henter kommune-scorer fra Dansk Mobilitetsatlas (mobilitetsatlas.dk, Beta Mobility).

STATUS: PROOF OF CONCEPT. Scriptet er IKKE koblet på master-pipelinen endnu -
det kalder bevidst ikke auto_build_master(), og indikatorerne står hverken i
build_master_csv.py eller shared.ts. Se docs/mobilitetsatlas-api.md for hvad
der skal besluttes først (licens og valg af indikator).

Atlasset har INGEN dokumenteret API. Til gengæld udstiller sitet sine data som
statiske GeoJSON-filer, som browseren selv henter. Scriptet bruger den kilde.

Kilder scriptet trækker fra:
  - https://mobilitetsatlas.dk/data/geojson/kommuner.geojson
      98 kommuner, punktgeometri, scorefelter i properties. Den primære kilde.
  - https://mobilitetsatlas.dk/udforsk (med HTTP-headeren "RSC: 1")
      Samme 98 kommuner, men 26 felter i stedet for 9 - herunder fordelingstal
      (gini, p10, unserved_pct) der ikke findes i GeoJSON-filen.

De to kilder er krydstjekket felt for felt på composite, kollektiv_kvalitet og
grade: nul afvigelser (aug. 2026). GeoJSON-filen er den stabile af de to;
RSC-ruten afhænger af Next.js' interne serialisering og kan brække ved et
framework-skifte hos dem. Derfor: hvis RSC-ruten fejler, skriver scriptet
alligevel CSV'en ud fra GeoJSON og markerer de manglende felter tomme.

LICENS: Atlasset er CC BY-SA 4.0. Genbrug kræver kreditering af Beta Mobility,
link til licensen, beskrivelse af ændringer OG at bearbejdelsen udgives på
samme licens. Det sidste er en beslutning for hele platformen, ikke for dette
script. Se docs/mobilitetsatlas-api.md.

Kør fra projektets rodmappe:
  python3 scripts/fetch_mobilitetsatlas.py
"""

from __future__ import annotations

import csv
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

BASE = "https://mobilitetsatlas.dk"
KOMMUNER_GEOJSON = f"{BASE}/data/geojson/kommuner.geojson"
UDFORSK_RSC = f"{BASE}/udforsk"

OUT_CSV = DATA_DIR / "mobilitetsatlas_scores.csv"

# Sitet lukker forbindelsen ved hurtige serieforespørgsler. Hold pausen.
REQUEST_DELAY = 2.0
MAX_RETRIES = 4

# Felter fra GeoJSON-filen (kernen i atlassets egen scoring).
GEOJSON_FIELDS = [
    "grade",               # A-G mærke
    "composite",           # mobilitetsfrihed 0-100 (= gennemsnit af de to nedenfor)
    "kollektiv_kvalitet",  # kollektiv rækkevidde, 0-100 relativt til de 98 kommuner
    "bevaegelsesfrihed",   # hverdagen uden bil, 0-100
    "bilbehov",            # bilens forspring
    "bil_skat_kr",         # beregnet årlig bilomkostning
    "tvunget_andel",       # andel af befolkningen der reelt er tvunget til bil
    "valgt_andel",         # andel der vælger bil
]

# Ekstrafelter der kun findes via RSC-ruten. Fordelingstallene er de interessante:
# gini og p10 siger noget om hvor UENS mobiliteten er fordelt inde i kommunen,
# unserved_pct hvor stor en del af befolkningen der reelt er uden betjening.
RSC_FIELDS = [
    "gini",           # ulighed i mobilitet internt i kommunen
    "p10",            # de 10 pct. dårligst stillede
    "cdi",            # car dependency index
    "o_pt",           # nåede destinationer med kollektiv trafik
    "o_car",          # nåede destinationer med bil
    "reach_ratio",    # o_car / o_pt
    "unserved_pct",   # andel af befolkning uden reel kollektiv betjening
]


def hent(url: str, rsc: bool = False) -> bytes:
    """Hent en URL med genforsøg. Sitet nulstiller forbindelser under pres."""
    headers = {"User-Agent": "doughnut-dk/1.0 (+https://github.com/augustseptimius-beep/doughnut)"}
    if rsc:
        headers["RSC"] = "1"
    sidste_fejl: Exception | None = None
    for forsoeg in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001 - vi vil genforsøge på alt netværksrelateret
            sidste_fejl = e
            print(f"  forsøg {forsoeg}/{MAX_RETRIES} fejlede: {e}")
            time.sleep(REQUEST_DELAY * forsoeg)
    raise RuntimeError(f"Kunne ikke hente {url}: {sidste_fejl}")


def hent_geojson() -> dict[str, dict]:
    """Kommunescorer fra den statiske GeoJSON-fil. Nøgle = kommune_kode uden nul."""
    print(f"Henter {KOMMUNER_GEOJSON}")
    data = json.loads(hent(KOMMUNER_GEOJSON))
    ud: dict[str, dict] = {}
    for f in data.get("features", []):
        p = f.get("properties", {})
        kode = p.get("kommune_code")
        if not kode:
            continue
        ud[str(int(kode))] = p
    print(f"  ✓ {len(ud)} kommuner")
    return ud


def hent_rsc() -> dict[str, dict]:
    """
    Ekstrafelter fra /udforsk. Siden serveres som en React-flight-payload, hvor
    datasættet ligger som ét JSON-array bag nøglen "data". Vi finder arrayets
    start og lader JSONDecoder læse præcis så langt som arrayet rækker.
    """
    print(f"Henter {UDFORSK_RSC} (RSC)")
    try:
        tekst = hent(UDFORSK_RSC, rsc=True).decode("utf-8", errors="replace")
    except RuntimeError as e:
        print(f"  ADVARSEL: RSC-ruten fejlede ({e}). Fortsætter uden ekstrafelter.")
        return {}

    noegle = '"data":[{"slug":"dk-'
    i = tekst.find(noegle)
    if i < 0:
        print("  ADVARSEL: fandt ikke datasættet i RSC-payloaden.")
        print("  Sandsynligvis har mobilitetsatlas.dk ændret sidestruktur.")
        print("  Fortsætter med kun GeoJSON-felterne.")
        return {}

    try:
        arr, _ = json.JSONDecoder().raw_decode(tekst[i + len('"data":'):])
    except ValueError as e:
        print(f"  ADVARSEL: kunne ikke parse RSC-payloaden ({e}). Fortsætter uden.")
        return {}

    ud: dict[str, dict] = {}
    for post in arr:
        kode = post.get("kommune_code")
        if not kode:
            continue
        ud[str(int(kode))] = post.get("values", {})
    print(f"  ✓ {len(ud)} kommuner med {len(RSC_FIELDS)} ekstrafelter")
    return ud


def kryds_tjek(geo: dict[str, dict], rsc: dict[str, dict]) -> None:
    """De to kilder skal være enige. Er de ikke det, har vi et datagrundlagsproblem."""
    if not rsc:
        return
    afvigelser = 0
    for kode, g in geo.items():
        r = rsc.get(kode)
        if r is None:
            print(f"  ADVARSEL: {g.get('name')} mangler i RSC-datasættet.")
            continue
        for felt in ("composite", "kollektiv_kvalitet"):
            if g.get(felt) != r.get(felt):
                afvigelser += 1
                print(f"  ADVARSEL: {g.get('name')} {felt}: geojson={g.get(felt)} rsc={r.get(felt)}")
    if afvigelser:
        print(f"  ADVARSEL: {afvigelser} afvigelser mellem de to kilder.")
    else:
        print("  ✓ De to kilder er enige på composite og kollektiv_kvalitet.")


def skriv_csv(geo: dict[str, dict], rsc: dict[str, dict]) -> None:
    kolonner = ["kommune_kode", "kommune_navn", "slug"] + GEOJSON_FIELDS + RSC_FIELDS
    raekker = []
    for kode in sorted(geo, key=int):
        g = geo[kode]
        r = rsc.get(kode, {})
        raekke = {
            "kommune_kode": kode,
            "kommune_navn": g.get("name", ""),
            "slug": g.get("slug", ""),
        }
        for felt in GEOJSON_FIELDS:
            raekke[felt] = g.get(felt, "")
        for felt in RSC_FIELDS:
            raekke[felt] = r.get(felt, "")
        raekker.append(raekke)

    DATA_DIR.mkdir(exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=kolonner)
        w.writeheader()
        w.writerows(raekker)
    print(f"✓ Skrevet {OUT_CSV.relative_to(ROOT)} ({len(raekker)} kommuner, {len(kolonner)} kolonner)")


def main() -> int:
    print("Dansk Mobilitetsatlas - kommunescorer")
    print("Kilde: Beta Mobility, mobilitetsatlas.dk, CC BY-SA 4.0")
    print()

    geo = hent_geojson()
    if len(geo) != 98:
        print(f"ADVARSEL: forventede 98 kommuner, fik {len(geo)}.")
    time.sleep(REQUEST_DELAY)
    rsc = hent_rsc()

    print("Krydstjekker de to kilder")
    kryds_tjek(geo, rsc)

    skriv_csv(geo, rsc)
    print()
    print("BEMÆRK: master-CSV'en er IKKE opdateret. Indikatoren er ikke besluttet endnu.")
    print("Se docs/mobilitetsatlas-api.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
