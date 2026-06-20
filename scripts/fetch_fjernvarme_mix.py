"""
fetch_fjernvarme_mix.py - Fjernvarmens brændselsmix pr. kommune.

KONTEKST under Energi-dimensionen (vises, men indgår IKKE i scoren).
Viser hvor "ren" en kommunes fjernvarme reelt er: andel biomasse, affald,
fossilt og reelt vedvarende (sol/varmepumpe/overskudsvarme). Bevidst ikke
scoret, fordi næsten al dansk fjernvarme er afbrænding - en absolut renheds-
score ville gøre alle kommuner røde, og at score biomasse som "grønt" er et
omdiskuteret værdivalg (se metode-siden).

Kilde:
  Energistyrelsen, Energiproducenttællingen (EPT)
  "Produktion og brændselsforbrug per anlæg 2022-2024"
  https://ens.dk/media/7199/download  (.xlsx, ~2,2 MB)

Metode:
  - Filtrér til seneste år (2024) og varmeproducerende anlæg (varmeprod_TJ > 0).
  - Vægt hvert anlægs brændselsforbrug med andel_varmelev, så kun den del af
    brændslet der går til VARME tælles med (kraftvarmeværkers el-del fjernes).
  - Aggregér pr. kommune (vaerk_kommune) og beregn fire andele der summer til 100%:
      biomasse  = skovflis + træpiller + halm + træ/biomasseaffald + bio-olie + biogas
      affald    = affald
      fossil    = kul + fuelolie + spildolie + gasolie + raffinaderigas + LPG + naturgas
      ren       = solenergi + omgivelsesvarme (varmepumper) + elektricitet + brændselsfrit
  - Kommuner med under MIN_TJ samlet varme-input markeres "fælles_net": deres
    egenproduktion er typisk kun en reservekedel (fx hovedstadskommuner på VEKS/
    CTR-nettet), så et eget mix ville være misvisende.

Output:
  data/fjernvarme_mix_scores.csv
  Kolonner: kommune_kode, kommune_navn, fjv_biomasse_pct, fjv_affald_pct,
            fjv_fossil_pct, fjv_ren_pct, fjv_total_tj, fjv_status

Kør fra projektets rodmappe:
  python3 scripts/fetch_fjernvarme_mix.py
"""

import csv
from collections import defaultdict
from pathlib import Path

import requests
import openpyxl

EPT_URL = "https://ens.dk/media/7199/download"
OUTPUT_FIL = Path("data/fjernvarme_mix_scores.csv")
TMP_XLSX = Path("/tmp/ept_fjernvarme.xlsx")
AAR = 2024
MIN_TJ = 100.0  # under dette: egenproduktion er reservekedel/fælles net

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

BIO = ["skovflis_TJ", "traepiller_TJ", "halm_TJ", "trae- og biomasseaffald_TJ", "bio-olie_TJ", "biogas_TJ"]
AFFALD = ["affald_TJ"]
FOSSIL = ["kul_TJ", "fuelolie_TJ", "spildolie_TJ", "gasolie_TJ", "raffinaderigas_TJ", "lpg_TJ", "naturgas_TJ"]
REN = ["solenergi_TJ", "omgivelsesvarme_TJ", "elektricitet_TJ", "braendselsfrit_TJ"]


def download():
    if TMP_XLSX.exists() and TMP_XLSX.stat().st_size > 1_000_000:
        print(f"Bruger cached fil: {TMP_XLSX}")
        return
    print(f"Henter EPT fra {EPT_URL} ...")
    resp = requests.get(EPT_URL, timeout=120)
    resp.raise_for_status()
    TMP_XLSX.write_bytes(resp.content)
    print(f"  Gemt: {TMP_XLSX} ({TMP_XLSX.stat().st_size/1024/1024:.1f} MB)")


def aggreger():
    wb = openpyxl.load_workbook(TMP_XLSX, read_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = ws.iter_rows(values_only=True)
    header = list(next(rows))
    idx = {h: i for i, h in enumerate(header) if h}

    def g(row, col):
        if col not in idx:
            return 0.0
        v = row[idx[col]]
        return float(v) if isinstance(v, (int, float)) else 0.0

    komm = defaultdict(lambda: defaultdict(float))
    for row in rows:
        if g(row, "aar") != AAR:
            continue
        if g(row, "varmeprod_TJ") <= 0:
            continue
        k = row[idx["vaerk_kommune"]]
        if k is None:
            continue
        k = str(int(k)) if isinstance(k, (int, float)) else str(k).strip()
        if k not in KOMMUNER:  # filtrerer bl.a. Christiansø (411)
            continue
        a = g(row, "andel_varmelev") or 1.0
        if a > 1:
            a /= 100.0
        komm[k]["bio"] += sum(g(row, c) for c in BIO) * a
        komm[k]["affald"] += sum(g(row, c) for c in AFFALD) * a
        komm[k]["fossil"] += sum(g(row, c) for c in FOSSIL) * a
        komm[k]["ren"] += sum(g(row, c) for c in REN) * a
    return komm


def beregn_og_gem(komm):
    resultater = []
    fælles = 0
    for kode, navn in KOMMUNER.items():
        v = komm.get(kode)
        total = (v["bio"] + v["affald"] + v["fossil"] + v["ren"]) if v else 0.0
        if not v or total < MIN_TJ:
            fælles += 1
            resultater.append({
                "kommune_kode": kode, "kommune_navn": navn,
                "fjv_biomasse_pct": "", "fjv_affald_pct": "",
                "fjv_fossil_pct": "", "fjv_ren_pct": "",
                "fjv_total_tj": round(total, 1) if v else 0,
                "fjv_status": "fælles_net",
            })
            continue
        resultater.append({
            "kommune_kode": kode, "kommune_navn": navn,
            "fjv_biomasse_pct": round(100 * v["bio"] / total, 1),
            "fjv_affald_pct": round(100 * v["affald"] / total, 1),
            "fjv_fossil_pct": round(100 * v["fossil"] / total, 1),
            "fjv_ren_pct": round(100 * v["ren"] / total, 1),
            "fjv_total_tj": round(total, 1),
            "fjv_status": "ok",
        })

    egne = [r for r in resultater if r["fjv_status"] == "ok"]
    if egne:
        nat_bio = sum(komm[r["kommune_kode"]]["bio"] for r in egne)
        nat_tot = sum(r["fjv_total_tj"] for r in egne)
        print(f"  Kommuner med egen varmeproduktion: {len(egne)}/98")
        print(f"  Kommuner på fælles net / uden egenproduktion: {fælles}/98")
        print(f"  Nationalt biomasse-andel (af egne producenter): {100*nat_bio/nat_tot:.1f}%")
    t = next((r for r in resultater if r["kommune_kode"] == "787"), None)
    if t:
        print(f"  Thisted: biomasse {t['fjv_biomasse_pct']}%  affald {t['fjv_affald_pct']}%  "
              f"fossil {t['fjv_fossil_pct']}%  ren {t['fjv_ren_pct']}%")

    OUTPUT_FIL.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["kommune_kode", "kommune_navn", "fjv_biomasse_pct", "fjv_affald_pct",
                  "fjv_fossil_pct", "fjv_ren_pct", "fjv_total_tj", "fjv_status"]
    with open(OUTPUT_FIL, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(resultater)
    print(f"\n✓ Gemt: {OUTPUT_FIL} ({len(resultater)} kommuner)")


def main():
    print("=" * 65)
    print("Doughnut - Fjernvarmens brændselsmix (Energistyrelsen EPT)")
    print("=" * 65)
    download()
    komm = aggreger()
    beregn_og_gem(komm)
    print("\nFærdig! Husk at køre build_master_csv.py.")


if __name__ == "__main__":
    main()
