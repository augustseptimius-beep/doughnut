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
from pathlib import Path

BASE_DST = "https://api.statbank.dk/v1/data"
EDS_URL  = "https://api.energidataservice.dk/dataset/CapacityPerMunicipality"
OUTPUT_FIL = Path("data/ve_kapacitet_scores.csv")
DELAY = 0.6

KOMMUNER = {
    "101": "København", "147": "Frederiksberg", "151": "Ballerup",
    "153": "Brøndby", "155": "Dragør", "157": "Gentofte",
    "159": "Gladsaxe", "161": "Glostrup", "163": "Herlev",
    "165": "Albertslund", "167": "Hvidovre", "169": "Høje-Taastrup",
    "173": "Lyngby-Taarbæk", "175": "Rødovre", "183": "Ishøj",
    "185": "Tårnby", "187": "Vallensbæk", "190": "Furesø",
    "201": "Allerød", "210": "Fredensborg", "217": "Helsingør",
    "219": "Hillerød", "223": "Hørsholm", "230": "Rudersdal",
    "240": "Egedal", "250": "Frederikssund", "253": "Greve",
    "259": "Køge", "260": "Halsnæs", "265": "Roskilde",
    "269": "Solrød", "270": "Gribskov", "306": "Odsherred",
    "316": "Holbæk", "320": "Faxe", "326": "Kalundborg",
    "329": "Ringsted", "330": "Slagelse", "336": "Stevns",
    "340": "Sorø", "350": "Lejre", "360": "Lolland",
    "370": "Næstved", "376": "Guldborgsund", "390": "Vordingborg",
    "400": "Bornholm", "410": "Middelfart", "420": "Assens",
    "430": "Faaborg-Midtfyn", "440": "Kerteminde", "450": "Nyborg",
    "461": "Odense", "479": "Svendborg", "480": "Nordfyns",
    "482": "Langeland", "492": "Ærø", "510": "Haderslev",
    "530": "Billund", "540": "Sønderborg", "550": "Tønder",
    "561": "Esbjerg", "563": "Fanø", "573": "Varde",
    "575": "Vejen", "580": "Aabenraa", "607": "Fredericia",
    "615": "Horsens", "621": "Kolding", "630": "Vejle",
    "657": "Herning", "661": "Holstebro", "665": "Lemvig",
    "671": "Struer", "706": "Syddjurs", "707": "Norddjurs",
    "710": "Favrskov", "727": "Odder", "730": "Randers",
    "740": "Silkeborg", "741": "Samsø", "746": "Skanderborg",
    "751": "Aarhus", "756": "Ikast-Brande", "760": "Ringkøbing-Skjern",
    "766": "Hedensted", "773": "Morsø", "779": "Skive",
    "787": "Thisted", "791": "Viborg", "810": "Brønderslev",
    "813": "Frederikshavn", "820": "Vesthimmerlands", "825": "Læsø",
    "840": "Rebild", "846": "Mariagerfjord", "849": "Jammerbugt",
    "851": "Aalborg", "860": "Hjørring",
}


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
