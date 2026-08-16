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

from __future__ import annotations  # kræves: maskinen kører Python 3.9,
# hvor 'float | None' i en signatur ellers fejler ved import (TypeError).

import csv
import json
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


def seneste_valgaar(tabel: str) -> str:
    """
    Finder nyeste periode i en DST-valgtabel i stedet for at hårdkode årstallet.

    Kommunalvalg holdes hvert 4. år, så et hårdkodet år gør indikatoren forkert
    i op til fire år ad gangen - platformen viste KV2021 længe efter KV2025 var
    offentliggjort, netop fordi årstallet stod fast i koden.
    """
    url = f"https://api.statbank.dk/v1/tableinfo/{tabel}?lang=da&format=JSON"
    req = urllib.request.Request(url, headers={"User-Agent": "DoughnutDK/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        info = json.loads(resp.read().decode("utf-8"))
    tid = next(v for v in info["variables"] if v.get("time"))
    aar = sorted(str(x["id"]) for x in tid["values"])
    return aar[-1]


def fetch_national_voter_turnout(year: str = "2026") -> tuple[dict[str, float], float | None]:
    """
    Henter stemmeprocent ved FOLKETINGSVALG for alle kommuner.
    Kilde: DST LABY09, VALRES=STEMPCT.
    Returnerer (dict {kommune_kode: stemmepct}, landsgennemsnit).
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
    url = f"{API_BASE}/LABY09/CSV?{params}"

    print(f"Henter stemmedeltagelse folketingsvalg {year} fra DST (LABY09)...")
    req = urllib.request.urlopen(url, timeout=20)
    content = req.read().decode("utf-8-sig")

    reader = csv.DictReader(io.StringIO(content), delimiter=";")
    result = {}
    national_avg = None

    for row in reader:
        kode = row.get("KOMGRP", "").strip()
        raw = row.get("INDHOLD", "").strip()
        if raw in ("", "..", "x", "X"):
            continue
        try:
            val = float(raw.replace(",", "."))
        except ValueError:
            continue
        if kode == "000":
            national_avg = val
        elif kode in VALID_CODES:
            result[kode] = val

    print(f"  Modtaget data for {len(result)} kommuner, landsgennemsnit: {national_avg}%")
    return result, national_avg


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


def compute_scores(data: dict[str, float], year: str) -> dict[str, float]:
    """
    Beregner ratio-score ift. landsgennemsnit (= 100).
    Henter landsgennemsnittet direkte fra DST (kode 000).
    """
    # Hent landsgennemsnit separat
    params = urllib.parse.urlencode({
        "KOMGRP": "000",
        "VALRES": "STEMPCT",
        "Tid": year,
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

    print(f"  Landsgennemsnit stemmeprocent {year}: {national_avg:.2f}%")

    scores = {}
    for kode, val in data.items():
        scores[kode] = round((val / national_avg) * 100, 2)
    return scores, national_avg


def write_csv(
    data: dict[str, float],
    scores: dict[str, float],
    national_avg: float,
    nat_data: dict[str, float],
    nat_scores: dict[str, float],
    nat_national_avg: float,
) -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "kommune_kode",
            "voter_turnout_pct",
            "voter_turnout_ratio",
            "voter_turnout_national_pct",
            "voter_turnout_national_ratio",
        ])
        all_kodes = sorted(data.keys(), key=int)
        for kode in all_kodes:
            writer.writerow([
                kode,
                round(data[kode], 2),
                scores.get(kode, ""),
                round(nat_data[kode], 2) if kode in nat_data else "",
                nat_scores.get(kode, "") if kode in nat_data else "",
            ])
    print(f"  Gemt: {OUTPUT_FILE}")
    print(f"  Rækker: {len(data)}")


def main():
    # Kommunalvalg - nyeste tilgængelige valg (IKKE hårdkodet, se seneste_valgaar)
    kv_aar = seneste_valgaar("LABY08")
    print(f"Nyeste kommunalvalg i LABY08: {kv_aar}")
    data = fetch_voter_turnout(kv_aar)
    scores, national_avg = compute_scores(data, kv_aar)

    # Folketingsvalg - nyeste tilgængelige valg
    ft_aar = seneste_valgaar("LABY09")
    print(f"Nyeste folketingsvalg i LABY09: {ft_aar}")
    nat_data, nat_national_avg = fetch_national_voter_turnout(ft_aar)
    nat_scores = {}
    if nat_national_avg and nat_national_avg > 0:
        nat_scores = {k: round((v / nat_national_avg) * 100, 2) for k, v in nat_data.items()}

    # Vis top 5 og bund 5 for KV
    sorted_by_score = sorted(scores.items(), key=lambda x: x[1])
    print("\nLavest KV-stemmedeltagelse (relativt):")
    for kode, score in sorted_by_score[:5]:
        print(f"  {kode}: {data[kode]:.1f}% → score {score:.1f}")
    print("Højest KV-stemmedeltagelse (relativt):")
    for kode, score in sorted_by_score[-5:]:
        print(f"  {kode}: {data[kode]:.1f}% → score {score:.1f}")

    write_csv(data, scores, national_avg, nat_data, nat_scores, nat_national_avg or 0.0)
    print("\nFærdigt.")


if __name__ == "__main__":
    main()

    # ───────────────────────────────────────────────────────────
    # AUTO-REBUILD af master_indicators.csv (tilføjet 2026)
    # ───────────────────────────────────────────────────────────
    try:
        import sys as _sys
        from pathlib import Path as _Path
        _sys.path.insert(0, str(_Path(__file__).resolve().parent))
        from build_master_csv import auto_build_master
        auto_build_master()
    except Exception as _e:
        print(f"\n⚠ Kunne ikke auto-rebuild master-CSV: {_e}")
        print("  Rådata er gemt. Kør manuelt: python3 scripts/build_master_csv.py")
