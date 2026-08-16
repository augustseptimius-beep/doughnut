#!/usr/bin/env python3
"""
fetch_ligestilling_data.py

Henter ligestillings- og lighedsindikatorer for alle 98 kommuner fra Danmarks Statistik.

Output: data/ligestilling_scores.csv

Indikatorer:
  life_expectancy_gender_gap  - kønsgab i middellevetid i år (HISBK, 2021:2025)
                                inverteret: lavere gap = bedre score
  income_gender_gap           - kvinders andel af mænds disponible indkomst i %
                                (INDKP101, 2024), direkte: højere = bedre
  employment_origin_gap       - beskæftigelsesfrekvens ikke-vestlige / dansk oprindelse i %
                                (RAS200, 2024), direkte: højere = bedre

Bemærk: LIGEFI1 (barselsdagpengedage) er KUN på landsdel-niveau i DST,
        ikke kommuneniveau, og er derfor udeladt.

Kør fra projektets rodmappe:
  python3 scripts/fetch_ligestilling_data.py
"""

from __future__ import annotations

import csv
import io
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dst_aar import seneste_aar, seneste_periode  # noqa: E402

API_URL = "https://api.statbank.dk/v1/data"
REQUEST_DELAY = 0.7

OUTPUT_DIR = Path(__file__).parent.parent / "data"

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


def api_post(table: str, variables: list[dict]) -> list[dict]:
    payload = json.dumps({
        "table": table,
        "format": "CSV",
        "lang": "da",
        "valuePresentation": "Code",
        "variables": variables,
    }).encode("utf-8")
    req = urllib.request.Request(
        API_URL, data=payload,
        headers={"Content-Type": "application/json"},
    )
    time.sleep(REQUEST_DELAY)
    resp = urllib.request.urlopen(req, timeout=60)
    content = resp.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content), delimiter=";")
    return list(reader)


def parse_value(raw: str) -> float | None:
    raw = raw.strip()
    if raw in ("", "..", ".", "x", "X", "-"):
        return None
    try:
        return float(raw.replace(".", "").replace(",", "."))
    except ValueError:
        return None


def write_csv(filename: str, headers: list[str], rows: list[list]) -> None:
    filepath = OUTPUT_DIR / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
    print(f"  Gemt: {filepath} ({len(rows)} raekker)")


# ---------------------------------------------------------------------------
# 1. Kønsgab i middellevetid (HISBK)
# ---------------------------------------------------------------------------

def fetch_life_expectancy_by_gender() -> tuple[dict[str, float], float | None]:
    """
    HISBK: Middellevetid opdelt paa koen (5-aarig glidende gennemsnit).
    Beregner: gap = kvinder - maend pr. kommune.
    Inverteret: lavere gap = bedre score (mere lighed i sundhed).
    """
    print("Henter middellevetid pr. koen (HISBK)...")
    rows = api_post("HISBK", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "KØN", "values": ["M", "K"]},
        # HISBK's perioder ER 5-års-intervaller ("2021:2025"), så vi skal bruge
        # hele periode-id'et - ikke bygge en streng af et enkelt årstal.
        {"code": "Tid", "values": [seneste_periode("HISBK", fallback="2021:2025")]},
    ])

    male: dict[str, float] = {}
    female: dict[str, float] = {}

    for row in rows:
        kode = row.get("OMRÅDE", "").strip()
        kon = row.get("KØN", "").strip()
        val = parse_value(row.get("INDHOLD", ""))
        if val is None:
            continue
        if kode not in VALID_CODES and kode != "000":
            continue
        if kon == "M":
            male[kode] = val
        elif kon == "K":
            female[kode] = val

    # Gap = kvinders - maends middellevetid
    gaps: dict[str, float] = {}
    for kode in set(male) & set(female):
        gaps[kode] = round(female[kode] - male[kode], 2)

    national_gap = gaps.pop("000", None)
    print(f"  {len(gaps)} kommuner, national gap: {national_gap} aar (kvinder lever laengere)")
    return gaps, national_gap


# ---------------------------------------------------------------------------
# 2. Indkomstgab mænd/kvinder (INDKP101)
# ---------------------------------------------------------------------------

def fetch_income_by_gender() -> tuple[dict[str, float], float | None]:
    """
    INDKP101: Gennemsnitlig disponibel indkomst opdelt paa koen.
    Beregner: kvinders andel = (K / M) * 100 pr. kommune.
    Direkte: hoejere andel = bedre (mere lighed i indkomst).
    KOEN: M = maend, K = kvinder
    INDKOMSTTYPE: 100 = Disponibel indkomst
    ENHED: 116 = Gennemsnit for alle personer (kr.)
    """
    print("Henter disponibel indkomst pr. koen (INDKP101, 2024)...")
    rows = api_post("INDKP101", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "KOEN", "values": ["M", "K"]},
        {"code": "INDKOMSTTYPE", "values": ["100"]},
        {"code": "ENHED", "values": ["116"]},
        {"code": "Tid", "values": [seneste_aar("INDKP101", fallback="2024")]},
    ])

    # Prøv 2023 hvis 2024 er tom
    if len(rows) < 50:
        print("  Faa resultater for 2024, proever 2023...")
        rows = api_post("INDKP101", [
            {"code": "OMRÅDE", "values": ["*"]},
            {"code": "KOEN", "values": ["M", "K"]},
            {"code": "INDKOMSTTYPE", "values": ["100"]},
            {"code": "ENHED", "values": ["116"]},
            {"code": "Tid", "values": ["2023"]},
        ])

    male: dict[str, float] = {}
    female: dict[str, float] = {}

    for row in rows:
        kode = row.get("OMRÅDE", "").strip()
        kon = row.get("KOEN", "").strip()
        val = parse_value(row.get("INDHOLD", ""))
        if val is None:
            continue
        if kode not in VALID_CODES and kode != "000":
            continue
        if kon == "M":
            male[kode] = val
        elif kon == "K":
            female[kode] = val

    # Kvinders andel af maends indkomst (%)
    ratio: dict[str, float] = {}
    for kode in set(male) & set(female):
        if male[kode] > 0:
            ratio[kode] = round((female[kode] / male[kode]) * 100, 2)

    national = ratio.pop("000", None)
    print(f"  {len(ratio)} kommuner, nationalt: kvinder tjener {national}% af maend")
    return ratio, national


# ---------------------------------------------------------------------------
# 3. Beskæftigelse fordelt på herkomst (RAS200)
# ---------------------------------------------------------------------------

def fetch_employment_by_origin() -> tuple[dict[str, float], float | None]:
    """
    RAS200: Beskaeftigelsesfrekvens opdelt paa herkomst.
    HERKOMST: '10' = dansk oprindelse, '25' = ikke-vestlige indvandrere
    Beregner: BFK_ikkevestlig / BFK_dansk * 100 pr. kommune.
    Direkte: hoejere ratio = bedre integration / mere lighed.
    Alder: '1666' (16-66 aar, gaelder fra 2022).
    """
    print("Henter beskaeftigelse pr. herkomst (RAS200, 2024)...")
    rows = api_post("RAS200", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "HERKOMST", "values": ["10", "25"]},
        {"code": "ALDER", "values": ["1666"]},
        {"code": "KØN", "values": ["TOT"]},
        {"code": "BEREGNING", "values": ["BFK"]},
        {"code": "Tid", "values": [seneste_aar("RAS200", fallback="2024")]},
    ])

    # Prøv 2023 hvis 2024 er tom
    if len(rows) < 50:
        print("  Faa resultater for 2024, proever 2023 med 16-65...")
        rows = api_post("RAS200", [
            {"code": "OMRÅDE", "values": ["*"]},
            {"code": "HERKOMST", "values": ["10", "25"]},
            {"code": "ALDER", "values": ["16-65"]},
            {"code": "KØN", "values": ["TOT"]},
            {"code": "BEREGNING", "values": ["BFK"]},
            {"code": "Tid", "values": ["2023"]},
        ])

    dansk: dict[str, float] = {}
    ikkevestlig: dict[str, float] = {}

    for row in rows:
        kode = row.get("OMRÅDE", "").strip()
        herkomst = row.get("HERKOMST", "").strip()
        val = parse_value(row.get("INDHOLD", ""))
        if val is None:
            continue
        if kode not in VALID_CODES and kode != "000":
            continue
        if herkomst == "10":
            dansk[kode] = val
        elif herkomst == "25":
            ikkevestlig[kode] = val

    # Ratio: ikke-vestlig BFK / dansk BFK * 100
    ratio: dict[str, float] = {}
    for kode in set(dansk) & set(ikkevestlig):
        if dansk[kode] > 0:
            ratio[kode] = round((ikkevestlig[kode] / dansk[kode]) * 100, 2)

    national = ratio.pop("000", None)
    print(f"  {len(ratio)} kommuner, national ratio: {national}% (ikkevestlig vs. dansk BFK)")
    return ratio, national


# ---------------------------------------------------------------------------
# Beregn ratio (direkte og inverteret)
# ---------------------------------------------------------------------------

def ratio_direct(val: float, nat: float) -> float | None:
    if nat == 0:
        return None
    return round((val / nat) * 100, 2)


def ratio_inverse(val: float, nat: float) -> float | None:
    """Lavere val = bedre. Inverteret saa hoej score = god performance."""
    if val == 0:
        return 150.0
    return round((nat / val) * 100, 2)


# ---------------------------------------------------------------------------
# Hauptprogram
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Henter ligestillingsindikatorer fra Danmarks Statistik")
    print("=" * 60)

    print("\n--- MIDDELLEVETID (koensforskelle) ---")
    le_gaps, nat_le_gap = fetch_life_expectancy_by_gender()

    print("\n--- INDKOMST (koensforskelle) ---")
    income_gap, nat_income = fetch_income_by_gender()

    print("\n--- BESKAEFTIGELSE (herkomstforskelle) ---")
    emp_origin, nat_emp_origin = fetch_employment_by_origin()

    # Saml og gem
    rows = []
    for kode in sorted(VALID_CODES, key=int):
        # life_expectancy_gender_gap: inverteret (lavere gap = bedre)
        le_val = le_gaps.get(kode)
        le_ratio = ratio_inverse(le_val, nat_le_gap) if le_val is not None and nat_le_gap else ""

        # income_gender_gap: direkte (hoejere kvinde-andel = bedre)
        inc_val = income_gap.get(kode)
        inc_ratio = ratio_direct(inc_val, nat_income) if inc_val is not None and nat_income else ""

        # employment_origin_gap: direkte (hoejere ratio = mere lighed)
        emp_val = emp_origin.get(kode)
        emp_ratio = ratio_direct(emp_val, nat_emp_origin) if emp_val is not None and nat_emp_origin else ""

        rows.append([
            kode,
            le_val if le_val is not None else "",
            le_ratio,
            inc_val if inc_val is not None else "",
            inc_ratio,
            emp_val if emp_val is not None else "",
            emp_ratio,
        ])

    write_csv("ligestilling_scores.csv", [
        "kommune_kode",
        "le_gender_gap_years",       "le_gender_gap_ratio",
        "income_gender_gap_pct",     "income_gender_gap_ratio",
        "employment_origin_gap_pct", "employment_origin_gap_ratio",
    ], rows)

    # Vis eksempel
    print("\nEksempel-output (Thisted, kode 787):")
    for r in rows:
        if r[0] == "787":
            print(f"  le_gap={r[1]} aar, ratio={r[2]}")
            print(f"  income_gap={r[3]}%, ratio={r[4]}")
            print(f"  emp_gap={r[5]}%, ratio={r[6]}")

    print("\n" + "=" * 60)
    print("Ligestillingsindikatorer hentet!")
    print("=" * 60)


if __name__ == "__main__":
    main()

    # ───────────────────────────────────────────────────────────
    # AUTO-REBUILD af master_indicators.csv
    # ───────────────────────────────────────────────────────────
    try:
        import sys as _sys
        from pathlib import Path as _Path
        _sys.path.insert(0, str(_Path(__file__).resolve().parent))
        from build_master_csv import auto_build_master
        auto_build_master()
    except Exception as _e:
        print(f"\n Kunne ikke auto-rebuild master-CSV: {_e}")
        print("  Raadat er gemt. Koer manuelt: python3 scripts/build_master_csv.py")
