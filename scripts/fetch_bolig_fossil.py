#!/usr/bin/env python3
"""
fetch_bolig_fossil.py

Beregner kommunens SAMLEDE fossile varmeafhængighed pr. kommune - scoret mod
et absolut mål på 0% fossil (ikke landsgennemsnit), da udfasning af olie/gas er
dansk politik. Score = 100 - samlet_fossil%.

Samlet fossil% = direkte fossil opvarmning (olie+gas)
              + fjernvarme-dækning% × fjernvarmens fossile brændselsandel

Kilder:
  - DST BOL202 (Personer efter opvarmningstype): giver BÅDE direkte fossil
    (CO=olie, CN=naturgas) OG fjernvarme-dækning (FJ) på samme befolkningsbasis.
  - data/fjernvarme_mix_scores.csv (Energistyrelsen EPT): fjernvarmens fossile
    brændselsandel pr. kommune. For de 18 fælles-net-kommuner uden lokalt mix
    bruges landsgennemsnittet.

VIGTIGT: fjernvarme_mix_scores.csv skal være genereret FØR dette script køres
(kør fetch_fjernvarme_mix.py først).

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


def load_fjernvarme_fossil() -> tuple[dict[str, float], float]:
    """Læser fjernvarmens fossile brændselsandel pr. kommune fra
    fjernvarme_mix_scores.csv. Returnerer ({kode: fjv_fossil_pct}, landssnit).
    Landssnit beregnes over kommuner med egen produktion (status=ok) og bruges
    for de 18 fælles-net-kommuner uden lokalt mix."""
    path = DATA_DIR / "fjernvarme_mix_scores.csv"
    if not path.exists():
        print("  ADVARSEL: fjernvarme_mix_scores.csv mangler - kør fetch_fjernvarme_mix.py først.")
        print("  Fortsætter uden fjernvarme-bidrag (kun direkte fossil).")
        return {}, 0.0
    # NB: denne CSV er skrevet af Python med "." som DECIMAL-separator.
    # Brug derfor almindelig float(), IKKE parse_value (som fjerner "." som
    # dansk tusind-separator og ville lave 7.9 om til 79).
    def csv_float(s: str) -> float | None:
        s = (s or "").strip()
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None

    per_kommune: dict[str, float] = {}
    w_sum = 0.0  # sum(fossil_pct * tj)
    tj_sum = 0.0
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            kode = (row.get("kommune_kode") or "").strip()
            val = csv_float(row.get("fjv_fossil_pct") or "")
            tj = csv_float(row.get("fjv_total_tj") or "") or 0.0
            if (row.get("fjv_status") or "").strip() == "ok" and val is not None:
                per_kommune[kode] = val
                w_sum += val * tj
                tj_sum += tj
    # TJ-vægtet landssnit: domineres af de store værker (typisk affald/biomasse,
    # lav fossil), hvilket er mest retvisende for de fælles-net-kommuner der
    # forsynes af netop de store metro-net.
    nat_avg = round(w_sum / tj_sum, 2) if tj_sum else 0.0
    print(f"  Fjernvarme-fossil: {len(per_kommune)} kommuner med eget mix, "
          f"TJ-vægtet landssnit {nat_avg:.1f}% (bruges for fælles-net-kommuner)")
    return per_kommune, nat_avg


def fetch_bolig_fossil():
    print("\n" + "=" * 60)
    print("Samlet fossil varmeafhængighed pr. kommune (mål: 0%)")
    print("=" * 60)

    fjv_fossil_pct, fjv_fossil_nat = load_fjernvarme_fossil()

    # Forsøg 2026, derefter 2025
    year_used = None
    rows = None
    for year in ["2026", "2025"]:
        print(f"  Forsøger BOL202 {year}...")
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

    # Aggregér pr. kommune: direkte fossil (CO=olie, CN=naturgas),
    # fjernvarme (FJ) og total - alt på befolkningsbasis fra BOL202.
    fossil_persons: dict[str, float] = defaultdict(float)
    fjernvarme_persons: dict[str, float] = defaultdict(float)
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
        elif opvarmning == "FJ":
            fjernvarme_persons[kode] += val

    kommuner_med_data = [k for k in VALID_CODES if total_persons.get(k, 0) > 0]
    if not kommuner_med_data:
        print("  FEJL: Ingen kommuner med data.")
        return

    # Skriv CSV: score = 100 - samlet_fossil% (mål 0)
    output_path = DATA_DIR / "bolig_fossil_scores.csv"
    samlet_pcts = []
    thisted_dbg = None
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "kommune_kode", "bolig_fossil_ratio", "bolig_fossil_raw",
            "fossil_direkte_pct", "fossil_via_fjv_pct",
        ])
        for kode in sorted(VALID_CODES):
            if total_persons.get(kode, 0) == 0:
                writer.writerow([kode, "", "", "", ""])
                continue
            direkte_pct = fossil_persons[kode] / total_persons[kode] * 100
            fjv_daekning = fjernvarme_persons[kode] / total_persons[kode] * 100
            fjv_andel = fjv_fossil_pct.get(kode, fjv_fossil_nat)
            via_fjv_pct = fjv_daekning * fjv_andel / 100
            samlet = direkte_pct + via_fjv_pct
            # Score mod absolut mål 0%: 100 = ingen fossil. Klippes ved 0 (kan ikke gå negativt
            # før samlet > 100%, hvilket ikke forekommer).
            ratio = round(max(0.0, 100 - samlet), 2)
            writer.writerow([
                kode, ratio, round(samlet, 2),
                round(direkte_pct, 2), round(via_fjv_pct, 2),
            ])
            samlet_pcts.append(samlet)
            if kode == "787":
                thisted_dbg = (direkte_pct, fjv_daekning, fjv_andel, via_fjv_pct, samlet, ratio)

    print(f"  Kommuner med data: {len(kommuner_med_data)}")
    if samlet_pcts:
        print(f"  Samlet fossil%: min {min(samlet_pcts):.1f} / snit {sum(samlet_pcts)/len(samlet_pcts):.1f} / max {max(samlet_pcts):.1f}")
    if thisted_dbg:
        d, dk, fa, vf, s, r = thisted_dbg
        print(f"  Thisted: direkte {d:.1f}% + fjernvarme-dækning {dk:.0f}% × {fa:.1f}% fossil "
              f"= via fjv {vf:.1f}% → samlet {s:.1f}% → score {r}")
    print(f"  Gemt: {output_path}")


if __name__ == "__main__":
    fetch_bolig_fossil()
    print()
    auto_build_master()
