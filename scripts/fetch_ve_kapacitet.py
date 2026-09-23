"""
fetch_ve_kapacitet.py - Lokal VE-kapacitet (sol + landvind) pr. kommune.

KONTEKST-indikator under Energi-dimensionen (vises, men indgår IKKE i scoren).
Måler kommunens installerede vedvarende elproduktion - et udtryk for lokalt
bidrag til den grønne omstilling. Bevidst ikke scoret, fordi strømmen leveres
til det nationale net, ikke til kommunens egne husstande (se metode-siden).

Kilder:
  - Energi Data Service: CapacityPerMunicipality (installeret MW pr. kommune)
    https://api.energidataservice.dk/dataset/CapacityPerMunicipality
  - Danmarks Statistik FOLK1A (befolkning, til kW/indb.)

Beregning:
  ve_kw_per_indb = (sol_MW + landvind_MW) * 1000 / befolkning
  Offshore vind holdes ude af hovedtallet (er ikke "lokal" energi for borgerne),
  men gemmes separat.

Output:
  data/ve_kapacitet_scores.csv
  Kolonner: kommune_kode, kommune_navn, ve_kw_per_indb,
            ve_sol_mw, ve_vind_mw, ve_offshore_mw, befolkning

Kør fra projektets rodmappe:
  python3 scripts/fetch_ve_kapacitet.py
"""

import csv
import time
import requests
from io import StringIO
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kommuner import KOMMUNER  # noqa: E402  (de 98 kommuner, data/kommuner.json)

BASE_DST = "https://api.statbank.dk/v1/data"
EDS_URL  = "https://api.energidataservice.dk/dataset/CapacityPerMunicipality"
OUTPUT_FIL = Path("data/ve_kapacitet_scores.csv")
DELAY = 0.6


def parse_float(s):
    if not s or str(s).strip() in ("..", "x", "X", ""):
        return None
    try:
        return float(str(s).strip().replace(".", "").replace(",", "."))
    except ValueError:
        return None


def hent_kapacitet():
    """Henter seneste måneds installerede kapacitet pr. kommune fra EDS.
    Returnerer {kode: {sol, vind, offshore}} i MW."""
    print("Henter VE-kapacitet (EDS CapacityPerMunicipality, seneste måned)...")
    # Ét kald: seneste 3 måneder for alle kommuner, vælg nyeste måned.
    params = {"start": "now-P3M", "limit": "500", "sort": "Month DESC"}
    resp = requests.get(EDS_URL, params=params, timeout=60)
    resp.raise_for_status()
    records = resp.json().get("records", [])
    if not records:
        raise RuntimeError("EDS returnerede ingen data (rate-limit? prøv igen om 1 min).")

    nyeste_maaned = max(r["Month"] for r in records)
    print(f"  Nyeste måned i data: {nyeste_maaned}")

    result = {}
    for r in records:
        if r["Month"] != nyeste_maaned:
            continue
        kode = str(r.get("MunicipalityNo") or "").strip()
        if kode not in KOMMUNER:
            continue
        sol = float(r.get("SolarPowerCapacity") or 0)
        vind = float(r.get("OnshoreWindCapacity") or 0)
        offshore = float(r.get("OffshoreWindCapacity") or 0)
        result[kode] = {"sol": sol, "vind": vind, "offshore": offshore}

    print(f"  Modtaget kapacitet for {len(result)} kommuner")
    return result


def hent_befolkning():
    """Henter befolkning pr. kommune fra FOLK1A (seneste kvartal)."""
    print("Henter befolkningstal (FOLK1A, 2025K1)...")
    koder = ",".join(KOMMUNER.keys())
    url = (
        f"{BASE_DST}/FOLK1A/CSV?lang=da"
        f"&KØN=TOT&ALDER=IALT&CIVILSTAND=TOT&Tid=2025K1&OMRÅDE={koder}"
    )
    time.sleep(DELAY)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    rows = list(csv.DictReader(StringIO(resp.text), delimiter=";"))

    navn_til_kode = {v.lower(): k for k, v in KOMMUNER.items()}
    result = {}
    for row in rows:
        omraade = (row.get("OMRÅDE") or row.get("område") or "").strip().lower()
        indhold = row.get("INDHOLD") or row.get("indhold") or ""
        kode = navn_til_kode.get(omraade)
        if not kode:
            for navn, k in navn_til_kode.items():
                if navn in omraade or omraade in navn:
                    kode = k
                    break
        if kode:
            result[kode] = parse_float(indhold)
    print(f"  Modtaget befolkningstal for {len(result)} kommuner")
    return result


def beregn_og_gem(kapacitet, befolkning):
    print("\nBeregner kW/indb...")
    resultater = []
    for kode, navn in KOMMUNER.items():
        kap = kapacitet.get(kode, {"sol": 0, "vind": 0, "offshore": 0})
        bef = befolkning.get(kode)
        lokal_mw = kap["sol"] + kap["vind"]  # sol + landvind = lokal VE
        kw_per_indb = round((lokal_mw * 1000) / bef, 1) if bef and bef > 0 else None
        resultater.append({
            "kommune_kode": kode,
            "kommune_navn": navn,
            "ve_kw_per_indb": kw_per_indb if kw_per_indb is not None else "",
            "ve_sol_mw": round(kap["sol"], 1),
            "ve_vind_mw": round(kap["vind"], 1),
            "ve_offshore_mw": round(kap["offshore"], 1),
            "befolkning": bef or "",
        })

    valide = [r for r in resultater if r["ve_kw_per_indb"] != ""]
    if valide:
        snit = sum(r["ve_kw_per_indb"] for r in valide) / len(valide)
        top = sorted(valide, key=lambda r: r["ve_kw_per_indb"], reverse=True)[:3]
        print(f"  Gennemsnit: {snit:.1f} kW/indb ({len(valide)} kommuner)")
        print(f"  Top 3: " + ", ".join(f"{r['kommune_navn']} {r['ve_kw_per_indb']}" for r in top))
    thisted = next((r for r in resultater if r["kommune_kode"] == "787"), None)
    if thisted:
        print(f"  Thisted: {thisted['ve_kw_per_indb']} kW/indb "
              f"(sol {thisted['ve_sol_mw']} MW + landvind {thisted['ve_vind_mw']} MW, "
              f"offshore {thisted['ve_offshore_mw']} MW)")

    OUTPUT_FIL.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["kommune_kode", "kommune_navn", "ve_kw_per_indb",
                  "ve_sol_mw", "ve_vind_mw", "ve_offshore_mw", "befolkning"]
    with open(OUTPUT_FIL, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(resultater)
    print(f"\n✓ Gemt: {OUTPUT_FIL} ({len(resultater)} kommuner)")


def main():
    print("=" * 65)
    print("Doughnut - Lokal VE-kapacitet (EDS CapacityPerMunicipality)")
    print("=" * 65)
    kapacitet = hent_kapacitet()
    befolkning = hent_befolkning()
    beregn_og_gem(kapacitet, befolkning)
    print("\nFærdig! Husk at køre build_master_csv.py.")


if __name__ == "__main__":
    main()
