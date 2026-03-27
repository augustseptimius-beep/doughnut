#!/usr/bin/env python3
"""
Hent territorial CO2e-udledning pr. indbygger fra klimaregnskabet.dk API
for alle 98 danske kommuner.

Krav:
  pip install requests

Brug:
  python3 fetch_climate_data.py [--year 2023] [--output ../data/climate_scores.csv]

Output CSV-kolonner:
  kommune_kode, kommune_navn, co2e_per_capita, climate_territorial_ratio, year

Ratio = (co2e_per_capita / Paris-budget) * 100
Paris-budget = 3 ton CO2e/person/år
> 100 = overshoot (overskrider planetær grænse)
< 100 = inden for sikker zone
"""

import argparse
import csv
import json
import os
import sys
import time

import requests
import urllib3
from typing import Optional
urllib3.disable_warnings()

API_KEY = "72549c4a2b417163ccc0edd32e9d09221e86c178478adb6bedc69fd350b7b0f5"
API_BASE = "https://klimaregnskabet.dk/api/municipality-data"
PARIS_BUDGET = 3.0  # ton CO2e/person/år

# Alle 98 kommunekoder + navne
KOMMUNER = [
    (101, "København"), (147, "Frederiksberg"), (151, "Ballerup"), (153, "Brøndby"),
    (155, "Dragør"), (157, "Gentofte"), (159, "Gladsaxe"), (161, "Glostrup"),
    (163, "Herlev"), (165, "Albertslund"), (167, "Hvidovre"), (169, "Høje-Taastrup"),
    (173, "Lyngby-Taarbæk"), (175, "Rødovre"), (183, "Ishøj"), (185, "Tårnby"),
    (187, "Vallensbæk"), (190, "Furesø"), (201, "Allerød"), (210, "Fredensborg"),
    (217, "Helsingør"), (219, "Hillerød"), (223, "Hørsholm"), (230, "Rudersdal"),
    (240, "Egedal"), (250, "Frederikssund"), (253, "Greve"), (259, "Køge"),
    (260, "Halsnæs"), (265, "Roskilde"), (269, "Solrød"), (270, "Gribskov"),
    (306, "Odsherred"), (316, "Holbæk"), (320, "Faxe"), (326, "Kalundborg"),
    (329, "Ringsted"), (330, "Slagelse"), (336, "Stevns"), (340, "Sorø"),
    (350, "Lejre"), (360, "Lolland"), (370, "Næstved"), (376, "Guldborgsund"),
    (390, "Vordingborg"), (400, "Bornholm"), (410, "Middelfart"), (420, "Assens"),
    (430, "Faaborg-Midtfyn"), (440, "Kerteminde"), (450, "Nyborg"), (461, "Odense"),
    (479, "Svendborg"), (480, "Nordfyn"), (482, "Langeland"), (492, "Ærø"),
    (510, "Haderslev"), (530, "Billund"), (540, "Sønderborg"), (550, "Tønder"),
    (561, "Esbjerg"), (563, "Fanø"), (573, "Varde"), (575, "Vejen"),
    (580, "Aabenraa"), (607, "Fredericia"), (615, "Horsens"), (621, "Kolding"),
    (630, "Vejle"), (657, "Herning"), (661, "Holstebro"), (665, "Lemvig"),
    (671, "Struer"), (706, "Syddjurs"), (707, "Norddjurs"), (710, "Favrskov"),
    (727, "Odder"), (730, "Randers"), (740, "Silkeborg"), (741, "Samsø"),
    (746, "Skanderborg"), (751, "Aarhus"), (756, "Ikast-Brande"), (760, "Ringkøbing-Skjern"),
    (766, "Hedensted"), (773, "Morsø"), (779, "Skive"), (787, "Thisted"),
    (791, "Viborg"), (810, "Brønderslev"), (813, "Frederikshavn"), (820, "Vesthimmerlands"),
    (825, "Læsø"), (840, "Rebild"), (846, "Mariagerfjord"), (849, "Jammerbugt"),
    (851, "Aalborg"), (860, "Hjørring"),
]


def fetch_kommune(kode: int, navn: str, year: int, debug: bool = False) -> Optional[float]:
    """Henter Samlet CO2-udledning (Ton CO2e/indb.) for én kommune."""
    params = {
        "municipality": kode,
        "year": year,
        "type": "Nøgletal",
    }
    headers = {
        "x-api-key": API_KEY,
        "Accept": "application/json",
    }

    for attempt in range(3):
        try:
            r = requests.get(API_BASE, params=params, headers=headers,
                             timeout=20, verify=True)

            if debug and attempt == 0:
                print(f"\n--- DEBUG: API-svar for {navn} ({kode}) ---")
                print(f"URL: {r.url}")
                print(f"Status: {r.status_code}")
                try:
                    print(json.dumps(r.json(), indent=2, ensure_ascii=False)[:3000])
                except Exception:
                    print(r.text[:1000])
                print("--- END DEBUG ---\n")

            if r.status_code == 401:
                print("FEJL: Ugyldig API-nøgle (401).", file=sys.stderr)
                sys.exit(1)
            if r.status_code == 403:
                print("FEJL: Adgang nægtet (403).", file=sys.stderr)
                sys.exit(1)
            if r.status_code != 200:
                print(f"  HTTP {r.status_code} for {navn} (forsøg {attempt+1})", file=sys.stderr)
                time.sleep(2 ** attempt)
                continue

            return _extract_co2_per_capita(r.json())

        except requests.RequestException as e:
            print(f"  Netværksfejl for {navn}: {e} (forsøg {attempt+1})", file=sys.stderr)
            if attempt < 2:
                time.sleep(2 ** attempt)

    return None


def _extract_co2_per_capita(data) -> Optional[float]:
    """
    Trækker 'Samlet CO2-udledning, Ton CO2e/indb.' ud af API-svaret.
    Håndterer liste- og dict-strukturer.
    """
    if isinstance(data, list):
        for item in data:
            val = _match_co2_per_capita(item)
            if val is not None:
                return val
    elif isinstance(data, dict):
        val = _match_co2_per_capita(data)
        if val is not None:
            return val
        for key in ("data", "results", "items", "records"):
            if key in data and isinstance(data[key], list):
                for item in data[key]:
                    val = _match_co2_per_capita(item)
                    if val is not None:
                        return val
    return None


def _match_co2_per_capita(item: dict) -> Optional[float]:
    """
    Matcher én record mod Nøgletal / Samlet / CO2 / Ton CO2e/indb.
    """
    if not isinstance(item, dict):
        return None

    sektor = str(item.get("sektor") or item.get("Sektor") or item.get("sector") or "").lower()
    kategori = str(item.get("type") or item.get("Type") or item.get("kategori") or
                   item.get("Kategori") or item.get("category") or "").lower()
    enhed = str(item.get("enhed") or item.get("Enhed") or item.get("unit") or "").lower()
    vaerdi = item.get("vaerdi") or item.get("Vaerdi") or item.get("value") or item.get("Value")

    # Primær match: Samlet sektor, CO2-udledning, per indbygger
    if "samlet" in sektor and "co2" in kategori and "indb" in enhed and vaerdi is not None:
        try:
            return float(vaerdi)
        except (ValueError, TypeError):
            pass

    # Bredere fallback
    if "indb" in enhed and "co2" in kategori and vaerdi is not None:
        try:
            return float(vaerdi)
        except (ValueError, TypeError):
            pass

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Hent territorial CO2e pr. capita fra klimaregnskabet.dk"
    )
    parser.add_argument("--year", type=int, default=2023,
                        help="Årstal (2018-2023, default: 2023)")
    parser.add_argument("--output", default="../data/climate_scores.csv",
                        help="Output CSV-sti (default: ../data/climate_scores.csv)")
    parser.add_argument("--debug", action="store_true",
                        help="Print rå API-svar for første kommune")
    args = parser.parse_args()

    print(f"Klimaregnskabet.dk — henter CO2e/indb. for {len(KOMMUNER)} kommuner ({args.year})")
    print(f"Paris-budget: {PARIS_BUDGET} ton CO2e/person/år\n")

    results = []
    failed = []

    for i, (kode, navn) in enumerate(KOMMUNER):
        # Debug kun for første kommune
        show_debug = args.debug and i == 0
        co2e = fetch_kommune(kode, navn, args.year, debug=show_debug)

        if co2e is not None:
            ratio = round(co2e / PARIS_BUDGET * 100, 2)
            results.append({
                "kommune_kode": str(kode),
                "kommune_navn": navn,
                "co2e_per_capita": round(co2e, 3),
                "climate_territorial_ratio": ratio,
                "year": args.year,
            })
            symbol = "🟢" if ratio <= 100 else "🔴"
            print(f"  [{i+1:3d}/{len(KOMMUNER)}] {kode:4d} {navn:25s} "
                  f"{co2e:.2f} ton → {ratio:.1f}% {symbol}")
        else:
            failed.append((kode, navn))
            print(f"  [{i+1:3d}/{len(KOMMUNER)}] {kode:4d} {navn:25s} — INGEN DATA")

        if i < len(KOMMUNER) - 1:
            time.sleep(0.2)

    if results:
        out_path = os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)
        )
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f,
                fieldnames=["kommune_kode", "kommune_navn", "co2e_per_capita",
                            "climate_territorial_ratio", "year"])
            writer.writeheader()
            writer.writerows(results)

        ratios = [r["climate_territorial_ratio"] for r in results]
        avg = sum(ratios) / len(ratios)
        overshoot = sum(1 for r in ratios if r > 100)

        print(f"\n✓ Gemt: {out_path}")
        print(f"  {len(results)} kommuner med data, {len(failed)} uden")
        print(f"  Gennemsnitlig ratio: {avg:.1f}%")
        print(f"  Overshoot (>100% af Paris-budget): {overshoot} kommuner")

        top5 = sorted(results, key=lambda r: r["climate_territorial_ratio"], reverse=True)[:5]
        print(f"\n  Top 5 højeste udledere:")
        for r in top5:
            print(f"    {r['kommune_navn']:25s} {r['co2e_per_capita']:.2f} ton "
                  f"→ {r['climate_territorial_ratio']:.1f}%")
    else:
        print("\n✗ Ingen data hentet. Kør med --debug for at se rå API-svar.")
        sys.exit(1)


if __name__ == "__main__":
    main()
