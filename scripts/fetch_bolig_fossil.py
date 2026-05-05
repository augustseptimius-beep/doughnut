#!/usr/bin/env python3
"""
fetch_bolig_fossil.py

Henter andel af befolkning der bor i fossilopvarmet bolig (gas + olie) pr. kommune.
Kilde: DST BOL202 (Personer efter opvarmningstype).
Forsøger 2026-data, falder tilbage på 2025 hvis 2026 mangler.

Kør fra projektets rodmappe:
  python3 scripts/fetch_bolig_fossil.py
"""

from __future__ import annotations

import csv
import io
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

API_URL = "https://api.statbank.dk/v1/data"
REQUEST_DELAY = 0.7

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

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


def parse_value(raw: str) -> float | None:
    raw = raw.strip()
    if raw in ("", "..", ".", "x", "X", "-"):
        return None
    try:
        return float(raw.replace(".", "").replace(",", "."))
    except ValueError:
        return None


def api_post(table: str, variables: list[dict]) -> list[dict]:
    payload = json.dumps({
        "table": table,
        "format": "CSV",
        "lang": "da",
        "valuePresentation": "Code",
        "variables": variables,
    }).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    time.sleep(REQUEST_DELAY)
    resp = urllib.request.urlopen(req, timeout=60)
    content = resp.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content), delimiter=";")
    return list(reader)


def auto_build_master():
    build_script = ROOT / "scripts" / "build_master_csv.py"
    if not build_script.exists():
        print("  ADVARSEL: build_master_csv.py ikke fundet - spring over.")
        return
    import subprocess
    result = subprocess.run(
        [sys.executable, str(build_script)],
        capture_output=True, text=True, cwd=str(ROOT)
    )
    if result.returncode == 0:
        print("  ✓ Master-CSV opdateret")
    else:
        print("  FEJL i build_master_csv.py:")
        print(result.stderr[-800:])


def fetch_bolig_fossil():
    print("\n" + "=" * 60)
    print("BOL202: Fossil opvarmning (gas + olie) pr. kommune")
    print("=" * 60)

    # Forsøg 2026, derefter 2025
    year_used = None
    rows = None
    for year in ["2026", "2025"]:
        print(f"  Forsøger {year}...")
        try:
            rows = api_post("BOL202", [
                {"code": "AMT", "values": ["*"]},
                {"code": "OPVARMNING", "values": ["*"]},
                {"code": "ANVENDELSE", "values": ["*"]},
                {"code": "Tid", "values": [year]},
            ])
            # Tjek om vi har data for mere end bare Hele landet
            kommuner_fundet = {r.get("AMT", "").strip() for r in rows if r.get("AMT", "").strip() in VALID_CODES}
            if len(kommuner_fundet) >= 90:
                year_used = year
                print(f"  Bruger {year}-data ({len(kommuner_fundet)} kommuner fundet)")
                break
            else:
                print(f"  {year}: kun {len(kommuner_fundet)} kommuner - prøver ældre år")
        except Exception as e:
            print(f"  {year} fejlede: {e}")

    if not rows or not year_used:
        print("  FEJL: Ingen brugbar data fundet.")
        return

    # Aggregér: fossil (CO=olie, CN=naturgas) og total pr. kommune
    fossil_persons: dict[str, float] = defaultdict(float)
    total_persons: dict[str, float] = defaultdict(float)
    FOSSIL_CODES = {"CO", "CN"}

    for row in rows:
        kode = row.get("AMT", "").strip()
        if kode not in VALID_CODES:
            continue
        opvarmning = row.get("OPVARMNING", "").strip()
        val = parse_value(row.get("INDHOLD", "") or "")
        if val is None or val < 0:
            continue
        total_persons[kode] += val
        if opvarmning in FOSSIL_CODES:
            fossil_persons[kode] += val

    # Beregn landsgennemsnit (uvægtet af de 98 kommuner)
    kommuner_med_data = [k for k in VALID_CODES if total_persons.get(k, 0) > 0]
    if not kommuner_med_data:
        print("  FEJL: Ingen kommuner med data.")
        return

    nat_pcts = [fossil_persons[k] / total_persons[k] * 100 for k in kommuner_med_data]
    nat_avg = sum(nat_pcts) / len(nat_pcts)
    print(f"  Landsgennemsnit fossil%: {nat_avg:.1f}%")
    print(f"  Kommuner med data: {len(kommuner_med_data)}")

    # Skriv CSV
    output_path = DATA_DIR / "bolig_fossil_scores.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["kommune_kode", "bolig_fossil_ratio", "bolig_fossil_raw"])
        for kode in sorted(VALID_CODES):
            if total_persons.get(kode, 0) == 0:
                writer.writerow([kode, "", ""])
                continue
            fossil_pct = fossil_persons[kode] / total_persons[kode] * 100
            # Inverse: lavere fossil% = bedre → ratio = (nat_avg / fossil_pct) * 100
            # Maksimalt 150 for at undgå ekstreme værdier (fx Frederiksberg med 0,2%)
            if fossil_pct == 0:
                ratio = 150.0
            else:
                ratio = min(round((nat_avg / fossil_pct) * 100, 2), 150.0)
            writer.writerow([kode, ratio, round(fossil_pct, 2)])

    print(f"  Gemt: {output_path} ({len(kommuner_med_data)} kommuner)")


if __name__ == "__main__":
    fetch_bolig_fossil()
    print()
    auto_build_master()
