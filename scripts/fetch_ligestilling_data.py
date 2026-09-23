#!/usr/bin/env python3
"""
fetch_ligestilling_data.py

Henter ligestillings- og lighedsindikatorer for alle 98 kommuner fra Danmarks Statistik.

Output: data/ligestilling_scores.csv

Indikatorer:
  life_expectancy_gender_gap  - kønsgab i middellevetid i år (HISBK, 2021:2025)
                                inverteret: lavere gap = bedre score
  income_gender_gap           - kvinders median disponible indkomst i % af mænds
                                (INDKP106, median beregnet af intervaller), direkte: højere = bedre
  employment_origin_gap       - beskæftigelsesfrekvens ikke-vestlige / dansk oprindelse i %
                                (RAS200, 2024), direkte: højere = bedre

Bemærk: LIGEFI1 (barselsdagpengedage) er KUN på landsdel-niveau i DST,
        ikke kommuneniveau, og er derfor udeladt.

Kør fra projektets rodmappe:
  python3 scripts/fetch_ligestilling_data.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dst_aar import seneste_aar, seneste_aar_liste, seneste_periode  # noqa: E402
from indkomst_median import median_disponibel  # noqa: E402
from dst import api_post, parse_value, pr_kommune_aar, seneste  # noqa: E402  (fælles DST-kald, scripts/dst.py)
from kommuner import KODER as VALID_CODES  # noqa: E402  (de 98 kommuner, data/kommuner.json)


OUTPUT_DIR = Path(__file__).parent.parent / "data"


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
# 2. Indkomstgab mænd/kvinder (INDKP106, median)
# ---------------------------------------------------------------------------

def fetch_income_by_gender() -> tuple[dict[str, float], float | None]:
    """
    Kvinders MEDIAN disponible indkomst i procent af mænds, pr. kommune.
    Direkte: hoejere andel = bedre (mere lighed i indkomst).

    Median, ikke gennemsnit (INDKP101 ENHED 116, brugt indtil sep. 2026):
    gennemsnittet blev flyttet af enkelte meget høje indkomster, så Vejen
    fik kvinder der "tjente" 142 % af mændene. DST udgiver ikke medianen pr.
    kommune og køn, så den beregnes ud fra INDKP106's indkomstintervaller -
    se indkomst_median.py.
    """
    aar = seneste_aar("INDKP106", fallback="2024")
    print(f"Henter median disponibel indkomst pr. koen (INDKP106, {aar})...")
    med = median_disponibel([aar], ["M", "K"])

    # Kvinders andel af maends medianindkomst (%)
    ratio: dict[str, float] = {}
    for kode in VALID_CODES | {"000"}:
        m, k = med.get((kode, "M", aar)), med.get((kode, "K", aar))
        if m and k is not None:
            ratio[kode] = round((k / m) * 100, 2)

    national = ratio.pop("000", None)
    print(f"  {len(ratio)} kommuner, nationalt: kvinders median er {national}% af maends")
    return ratio, national


# ---------------------------------------------------------------------------
# 3. Beskæftigelse fordelt på herkomst (RAS200)
# ---------------------------------------------------------------------------

def serie_employment_origin_gap(aar: list[str]) -> dict[tuple[str, str], float]:
    """
    RAS200: beskæftigelsesfrekvens for indvandrere fra ikke-vestlige lande
    (HERKOMST=25) i procent af frekvensen for personer med dansk oprindelse
    (HERKOMST=10), 16-64 år. {(kommune_kode, år): pct} inkl. hele landet (000).
    Højere = mere lighed. Bruges af både scoren og retningspilen.

    16-64 år, ikke 16-66 (sep. 2026): DST har kun 16-66 fra 2022, så en
    retningspil på den aldersgruppe ville have tre år. 16-64 findes fra 2008 og
    er også den aldersgruppe `employment` bruger. Scoren flyttede sig med
    median 0,7% ved skiftet.
    """
    rows = api_post("RAS200", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "HERKOMST", "values": ["10", "25"]},
        {"code": "ALDER", "values": ["16-64"]},
        {"code": "KØN", "values": ["TOT"]},
        {"code": "BEREGNING", "values": ["BFK"]},
        {"code": "Tid", "values": aar},
    ])
    dansk = pr_kommune_aar([r for r in rows if r.get("HERKOMST") == "10"])
    ikkevestlig = pr_kommune_aar([r for r in rows if r.get("HERKOMST") == "25"])
    return {k: round(ikkevestlig[k] / dansk[k] * 100, 2)
            for k in ikkevestlig if dansk.get(k)}


def fetch_employment_by_origin() -> tuple[dict[str, float], float | None]:
    """Beskæftigelsesgab efter herkomst i nyeste år med data, og landstallet."""
    print("Henter beskaeftigelse pr. herkomst (RAS200)...")
    aar, ratio, national = seneste(serie_employment_origin_gap(
        seneste_aar_liste("RAS200", 2, fallback=["2024", "2023"])), tabel="RAS200")
    print(f"  {len(ratio)} kommuner ({aar}), national ratio: {national}% (ikkevestlig vs. dansk BFK)")
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
            nat_le_gap if nat_le_gap is not None else "",
            nat_income if nat_income is not None else "",
            nat_emp_origin if nat_emp_origin is not None else "",
        ])

    write_csv("ligestilling_scores.csv", [
        "kommune_kode",
        "le_gender_gap_years",       "le_gender_gap_ratio",
        "income_gender_gap_pct",     "income_gender_gap_ratio",
        "employment_origin_gap_pct", "employment_origin_gap_ratio",
        "le_gender_gap_ref", "income_gender_gap_ref", "employment_origin_gap_ref",
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
