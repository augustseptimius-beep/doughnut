#!/usr/bin/env python3
"""
fetch_democracy_data.py

Henter stemmedeltagelse ved kommunalvalget 2021 for alle 98 kommuner
via Danmarks Statistik Statistikbank API (tabel LABY08).

Opretter/opdaterer: ../data/democracy_scores.csv

Kilde: Danmarks Statistik, LABY08
Datakilde URL: https://www.statistikbanken.dk/LABY08
Valg: Kommunalvalget 2021
Indikator: Stemmeprocent (STEMPCT)
Scoremetode: Ratio ift. landsgennemsnit × 100 (højere er bedre)

Brug:
  python3 fetch_democracy_data.py
"""

import csv
import io
import sys
import urllib.request
import urllib.parse
from pathlib import Path

API_BASE = "https://api.statbank.dk/v1/data"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "democracy_scores.csv"

# Kommunekoder der er ægte kommuner (3-cifrede, > 100)
VALID_CODES = {
    "101", "147", "151", "153", "155", "157", "159", "161", "163", "165",
    "167", "169", "173", "175", "183", "185", "187", "190", "201", "210",
    "217", "219", "223", "230", "240", "250", "253", "259", "260", "265",
    "269", "270", "306", "316", "320", "326", "329", "330", "336", "340",
    "350", "360", "370", "376", "390", "400", "410", "420", "430", "440",
    "450", "461", "479", "480", "482", "492", "510", "530", "540", "550",
    "561", "563", "573", "575", "580", "607", "615", "621", "630", "657",
    "661", "665", "671", "706", "707", "710", "727", "730", "740", "741",
    "746", "751", "756", "760", "766", "773", "779", "787", "791", "810",
    "813", "820", "825", "840", "846", "849", "851", "860",
}


def fetch_voter_turnout(year: str = "2021") -> dict[str, float]:
    """
    Henter stemmeprocent for alle kommuner.
    Returnerer dict {kommune_kode: stemmepct}.
    """
    params = urllib.parse.urlencode({
        "KOMGRP": "*",
        "VALRES": "STEMPCT",
        "Tid": year,
        "lang": "da",
        "format": "CSV",
        "delimiter": "Semicolon",
        "valuePresentation": "Code",
    })
    url = f"{API_BASE}/LABY08/CSV?{params}"

    print(f"Henter stemmedeltagelse {year} fra DST (LABY08)...")
    req = urllib.request.urlopen(url, timeout=20)
    content = req.read().decode("utf-8-sig")

    reader = csv.DictReader(io.StringIO(content), delimiter=";")
    result = {}

    for row in reader:
        kode = row.get("KOMGRP", "").strip()
        raw = row.get("INDHOLD", "").strip()
        if kode not in VALID_CODES:
            continue
        if raw in ("", "..", "x", "X"):
            continue
        try:
            result[kode] = float(raw.replace(",", "."))
        except ValueError:
            pass

    print(f"  Modtaget data for {len(result)} kommuner")
    return result


def compute_scores(data: dict[str, float]) -> dict[str, float]:
    """
    Beregner ratio-score ift. landsgennemsnit (= 100).
    Henter landsgennemsnittet direkte fra DST (kode 000).
    """
    # Hent landsgennemsnit separat
    params = urllib.parse.urlencode({
        "KOMGRP": "000",
        "VALRES": "STEMPCT",
        "Tid": "2021",
        "lang": "da",
        "format": "CSV",
        "delimiter": "Semicolon",
        "valuePresentation": "Code",
    })
    url = f"{API_BASE}/LABY08/CSV?{params}"
    req = urllib.request.urlopen(url, timeout=20)
    content = req.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content), delimiter=";")
    rows = list(reader)

    national_avg = None
    for row in rows:
        if row.get("KOMGRP", "").strip() == "000":
            raw = row.get("INDHOLD", "").strip()
            national_avg = float(raw.replace(",", "."))
            break

    if national_avg is None or national_avg == 0:
        print("FEJL: Kunne ikke hente landsgennemsnit")
        sys.exit(1)

    print(f"  Landsgennemsnit stemmeprocent 2021: {national_avg:.2f}%")

    scores = {}
    for kode, val in data.items():
        scores[kode] = round((val / national_avg) * 100, 2)
    return scores, national_avg


def write_csv(data: dict[str, float], scores: dict[str, float], national_avg: float) -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "kommune_kode",
            "voter_turnout_pct",
            "voter_turnout_ratio",
            "national_avg_pct",
            "year",
        ])
        for kode in sorted(data.keys(), key=int):
            writer.writerow([
                kode,
                round(data[kode], 2),
                scores.get(kode, ""),
                round(national_avg, 2),
                "2021",
            ])
    print(f"  Gemt: {OUTPUT_FILE}")
    print(f"  Rækker: {len(data)}")


def main():
    data = fetch_voter_turnout("2021")
    scores, national_avg = compute_scores(data)

    # Vis top 5 og bund 5
    sorted_by_score = sorted(scores.items(), key=lambda x: x[1])
    print("\nLavest stemmedeltagelse (relativt):")
    for kode, score in sorted_by_score[:5]:
        print(f"  {kode}: {data[kode]:.1f}% → score {score:.1f}")
    print("Højest stemmedeltagelse (relativt):")
    for kode, score in sorted_by_score[-5:]:
        print(f"  {kode}: {data[kode]:.1f}% → score {score:.1f}")

    write_csv(data, scores, national_avg)
    print("\nFærdigt.")


if __name__ == "__main__":
    main()
