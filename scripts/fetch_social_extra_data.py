#!/usr/bin/env python3
"""
fetch_social_extra_data.py

Henter supplerende sociale indikatorer for alle 98 kommuner fra Danmarks Statistik.

Opretter/opdaterer:
  ../data/sundhed_extra_scores.csv     (Sundhed)
  ../data/uddannelse_extra_scores.csv  (Uddannelse)
  ../data/bolig_extra_scores.csv       (Bolig)
  ../data/samskabelse_extra_scores.csv (Samskabelse & demokrati)
  ../data/lokalsamfund_extra_scores.csv (Lokalsamfund)

Indikatorer:
  SUNDHED:
    - SBR01: Sygehusbenyttelse (andel med ophold, inverteret - lavere er bedre)

  UDDANNELSE:
    - HFUDD11: Unge 25-29 med kun grundskole (inverteret - lavere er bedre)

  BOLIG:
    - BOL106: Gennemsnitlig boligareal pr. person (m2, direkte)

  SAMSKABELSE & DEMOKRATI:
    - SKOLM02B: Musikskoleelever pr. 1.000 indb. (proxy for kulturdeltagelse)

  LOKALSAMFUND:
    - KVOTIEN: Klassekvotient grundskole (inverteret - lavere er bedre)
    - BOERN8: Normering daginstitution 3-5 år (inverteret - lavere er bedre)
    - IDRFIN02: Kommunale idrætsudgifter pr. indb. (direkte)

Brug:
  python3 fetch_social_extra_data.py
"""

from __future__ import annotations

import csv
import io
import json
import sys
import time
import urllib.request
from pathlib import Path

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


def ratio_direct(val: float, nat: float) -> float:
    if nat == 0: return 0
    return round((val / nat) * 100, 2)


def ratio_inverse(val: float, nat: float) -> float:
    if val == 0: return 150
    return round((nat / val) * 100, 2)


def write_csv(filename: str, headers: list[str], rows: list[list]) -> None:
    filepath = OUTPUT_DIR / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
    print(f"  Gemt: {filepath} ({len(rows)} rækker)")


# ---------------------------------------------------------------------------
# SUNDHED: Sygehusbenyttelse
# ---------------------------------------------------------------------------

def fetch_hospital_use() -> tuple[dict[str, float], float | None]:
    """
    SBR01: Andel af befolkningen med ophold på sygehus.
    Inverteret: lavere er bedre (sundere befolkning).
    """
    print("Henter sygehusbenyttelse (SBR01)...")
    # Hent total personer og personer med ophold
    rows = api_post("SBR01", [
        {"code": "KOMMUNEDK", "values": ["*"]},
        {"code": "OPHOLD_PÅ_SYGEHUS", "values": ["200100", "200110"]},
        {"code": "ALDER", "values": ["TOT"]},
        {"code": "KØN", "values": ["00"]},
        {"code": "Tid", "values": ["2022"]},
    ])

    total: dict[str, float] = {}
    with_stay: dict[str, float] = {}
    for row in rows:
        kode = row.get("KOMMUNEDK", "").strip()
        ophold = row.get("OPHOLD_PÅ_SYGEHUS", "").strip()
        val = parse_value(row.get("INDHOLD", ""))
        if val is None:
            continue
        if kode not in VALID_CODES and kode != "000":
            continue
        if ophold == "200100":
            total[kode] = val
        elif ophold == "200110":
            with_stay[kode] = val

    result = {}
    for kode in with_stay:
        if kode in total and total[kode] > 0:
            result[kode] = round((with_stay[kode] / total[kode]) * 100, 2)

    national = result.pop("000", None)
    print(f"  {len(result)} kommuner, landsgennemsnit: {national}%")
    return result, national


# ---------------------------------------------------------------------------
# SUNDHED: Afstand til praktiserende læge
# ---------------------------------------------------------------------------

def fetch_gp_distance() -> tuple[dict[str, float], float | None]:
    """
    SUNDAF01: Gennemsnitlig afstand (km) til nærmeste praktiserende læge pr. kommune.
    BNØGLE='0010' = gennemsnitlig afstand i km.
    LIVSKONT='2005' = alle borgere (uanset kontaktform).
    Inverteret: kortere afstand er bedre.
    """
    print("Henter afstand til praktiserende læge (SUNDAF01)...")
    rows = api_post("SUNDAF01", [
        {"code": "KOMMUNEDK", "values": ["*"]},
        {"code": "BNØGLE", "values": ["0010"]},      # Gennemsnitlig afstand (km)
        {"code": "LIVSKONT", "values": ["2005"]},     # Alle borgere
        {"code": "KØN", "values": ["00"]},            # Begge køn
        {"code": "ALDER", "values": ["IALT"]},        # Alle aldre
        {"code": "Tid", "values": ["2024"]},
    ])
    result = {}
    national = None
    for row in rows:
        kode = row.get("KOMMUNEDK", "").strip()
        val = parse_value(row.get("INDHOLD", ""))
        if val is None:
            continue
        if kode == "000":
            national = val
        elif kode in VALID_CODES:
            result[kode] = val
    # Prøv 2023 hvis 2024 er tom
    if len(result) < 50:
        print("  Få resultater for 2024, prøver 2023...")
        rows = api_post("SUNDAF01", [
            {"code": "KOMMUNEDK", "values": ["*"]},
            {"code": "BNØGLE", "values": ["0010"]},
            {"code": "LIVSKONT", "values": ["2005"]},
            {"code": "KØN", "values": ["00"]},
            {"code": "ALDER", "values": ["IALT"]},
            {"code": "Tid", "values": ["2023"]},
        ])
        result = {}
        national = None
        for row in rows:
            kode = row.get("KOMMUNEDK", "").strip()
            val = parse_value(row.get("INDHOLD", ""))
            if val is None:
                continue
            if kode == "000":
                national = val
            elif kode in VALID_CODES:
                result[kode] = val
    print(f"  {len(result)} kommuner, landsgennemsnit: {national} km")
    return result, national


# ---------------------------------------------------------------------------
# UDDANNELSE: Unge med kun grundskole
# ---------------------------------------------------------------------------

def fetch_low_education() -> tuple[dict[str, float], float | None]:
    """
    HFUDD11: Andel af 25-29-årige med kun grundskole.
    Inverteret: lavere er bedre (flere uddannede).
    """
    print("Henter uddannelsesniveau 25-29 (HFUDD11)...")
    rows = api_post("HFUDD11", [
        {"code": "BOPOMR", "values": ["*"]},
        {"code": "HERKOMST", "values": ["TOT"]},
        {"code": "HFUDD", "values": ["TOT", "H10"]},  # Total + kun grundskole
        {"code": "ALDER", "values": ["25-29"]},
        {"code": "KØN", "values": ["TOT"]},
        {"code": "Tid", "values": ["2024"]},
    ])

    totals: dict[str, float] = {}
    grundskole: dict[str, float] = {}
    for row in rows:
        kode = row.get("BOPOMR", "").strip()
        udd = row.get("HFUDD", "").strip()
        val = parse_value(row.get("INDHOLD", ""))
        if val is None:
            continue
        if kode not in VALID_CODES and kode != "000":
            continue
        if udd == "TOT":
            totals[kode] = val
        elif udd == "H10":
            grundskole[kode] = val

    result = {}
    for kode in grundskole:
        if kode in totals and totals[kode] > 0:
            result[kode] = round((grundskole[kode] / totals[kode]) * 100, 2)

    national = result.pop("000", None)
    print(f"  {len(result)} kommuner, landsgennemsnit: {national}%")
    return result, national


# ---------------------------------------------------------------------------
# BOLIG: Boligareal pr. person
# ---------------------------------------------------------------------------

def fetch_housing_area() -> tuple[dict[str, float], float | None]:
    """
    BOL106: Gennemsnitligt boligareal pr. person (m2).
    Direkte: mere plads er bedre.
    """
    print("Henter boligareal pr. person (BOL106)...")
    rows = api_post("BOL106", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "ENHED", "values": ["GNSAP"]},
        {"code": "ANVENDELSE", "values": ["TOT"]},
        {"code": "Tid", "values": ["2025"]},
    ])

    result = {}
    national = None
    for row in rows:
        kode = row.get("OMRÅDE", "").strip()
        val = parse_value(row.get("INDHOLD", ""))
        if val is None:
            continue
        if kode == "000":
            national = val
        elif kode in VALID_CODES:
            result[kode] = val

    print(f"  {len(result)} kommuner, landsgennemsnit: {national} m2")
    return result, national


# ---------------------------------------------------------------------------
# SAMSKABELSE: Musikskoleelever
# ---------------------------------------------------------------------------

def fetch_music_school() -> tuple[dict[str, float], float | None]:
    """
    SKOLM02B: Musikskoleelever.
    Normaliseres pr. 1.000 indb. med FOLK1A.
    """
    print("Henter musikskoleelever (SKOLM02B)...")
    rows = api_post("SKOLM02B", [
        {"code": "KOMK", "values": ["*"]},
        {"code": "ALDER", "values": ["TOT"]},
        {"code": "KØN", "values": ["TOT"]},
        {"code": "Tid", "values": ["2023:2024"]},
    ])

    result = {}
    national = None
    for row in rows:
        kode = row.get("KOMK", "").strip()
        val = parse_value(row.get("INDHOLD", ""))
        if val is None:
            continue
        if kode == "000":
            national = val
        elif kode in VALID_CODES:
            result[kode] = val

    print(f"  {len(result)} kommuner, landssamlet: {national}")
    return result, national


# ---------------------------------------------------------------------------
# LOKALSAMFUND: Uddannet pædagogisk personale
# ---------------------------------------------------------------------------

def fetch_educated_staff() -> tuple[dict[str, float], float | None]:
    """
    BOERN1: Andel af pædagogisk personale med pædagoguddannelse (kode 460).
    UDDANNELSE='460' = Pædagoguddannelse (professionsbachelor, 2019-)
    UDDANNELSE='TOT' = I alt pædagogisk personale
    Direkte: højere andel uddannede er bedre.
    """
    print("Henter pædagogisk personale (BOERN1)...")
    rows = api_post("BOERN1", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "OVERENS", "values": ["TOT"]},      # Alle stillingskategorier
        {"code": "UDDANNELSE", "values": ["TOT", "460"]},  # Total + pædagoguddannelse
        {"code": "Tid", "values": ["2024"]},
    ])
    totals: dict[str, float] = {}
    paed: dict[str, float] = {}
    for row in rows:
        kode = row.get("OMRÅDE", "").strip()
        udd = row.get("UDDANNELSE", "").strip()
        val = parse_value(row.get("INDHOLD", ""))
        if val is None:
            continue
        if kode not in VALID_CODES and kode != "000":
            continue
        if udd == "TOT":
            totals[kode] = val
        elif udd == "460":
            paed[kode] = val
    # Prøv 2023 hvis 2024 er tom
    if len(totals) < 50:
        print("  Prøver 2023...")
        rows = api_post("BOERN1", [
            {"code": "OMRÅDE", "values": ["*"]},
            {"code": "OVERENS", "values": ["TOT"]},
            {"code": "UDDANNELSE", "values": ["TOT", "460"]},
            {"code": "Tid", "values": ["2023"]},
        ])
        totals = {}
        paed = {}
        for row in rows:
            kode = row.get("OMRÅDE", "").strip()
            udd = row.get("UDDANNELSE", "").strip()
            val = parse_value(row.get("INDHOLD", ""))
            if val is None:
                continue
            if kode not in VALID_CODES and kode != "000":
                continue
            if udd == "TOT":
                totals[kode] = val
            elif udd == "460":
                paed[kode] = val
    result: dict[str, float] = {}
    for kode in totals:
        if kode in paed and totals[kode] > 0:
            result[kode] = round(paed[kode] / totals[kode] * 100, 2)
    national = result.pop("000", None)
    print(f"  {len(result)} kommuner, landsgennemsnit: {national}% pædagoguddannede")
    return result, national


# ---------------------------------------------------------------------------
# LOKALSAMFUND: Klassekvotienter
# ---------------------------------------------------------------------------

def fetch_class_size() -> tuple[dict[str, float], float | None]:
    """
    KVOTIEN: Gennemsnitlig klassekvotient i grundskolen.
    Inverteret: færre elever pr. klasse er bedre.
    """
    print("Henter klassekvotienter (KVOTIEN)...")
    rows = api_post("KVOTIEN", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "KLASSE", "values": ["0000"]},  # Alle klassetrin
        {"code": "SKTPE", "values": ["ANTALSUM"]},  # Alle skoletyper
        {"code": "Tid", "values": ["2024"]},
    ])

    result = {}
    national = None
    for row in rows:
        kode = row.get("OMRÅDE", "").strip()
        val = parse_value(row.get("INDHOLD", ""))
        if val is None:
            continue
        if kode == "000":
            national = val
        elif kode in VALID_CODES:
            result[kode] = val

    # Prøv 2023 hvis 2024 er tom
    if len(result) < 50:
        print("  Prøver 2023...")
        rows = api_post("KVOTIEN", [
            {"code": "OMRÅDE", "values": ["*"]},
            {"code": "KLASSE", "values": ["0000"]},
            {"code": "SKTPE", "values": ["ANTALSUM"]},
            {"code": "Tid", "values": ["2023"]},
        ])
        result = {}
        national = None
        for row in rows:
            kode = row.get("OMRÅDE", "").strip()
            val = parse_value(row.get("INDHOLD", ""))
            if val is None:
                continue
            if kode == "000":
                national = val
            elif kode in VALID_CODES:
                result[kode] = val

    print(f"  {len(result)} kommuner, landsgennemsnit: {national}")
    return result, national


# ---------------------------------------------------------------------------
# LOKALSAMFUND: Daginstitutionsnormering
# ---------------------------------------------------------------------------

def fetch_daycare_ratio() -> tuple[dict[str, float], float | None]:
    """
    BOERN8: Normering i daginstitutioner (3-5 år) - børn pr. voksen.
    Inverteret: færre børn pr. voksen er bedre.
    """
    print("Henter daginstitutionsnormering (BOERN8)...")
    rows = api_post("BOERN8", [
        {"code": "KOMMUNEDK", "values": ["*"]},
        {"code": "PASKAT", "values": ["3"]},   # 3-5 år
        {"code": "Tid", "values": ["2024"]},
    ])

    result = {}
    national = None
    for row in rows:
        kode = row.get("KOMMUNEDK", "").strip()
        val = parse_value(row.get("INDHOLD", ""))
        if val is None:
            continue
        if kode == "000":
            national = val
        elif kode in VALID_CODES:
            result[kode] = val

    # Prøv 2023
    if len(result) < 50:
        print("  Prøver 2023...")
        rows = api_post("BOERN8", [
            {"code": "KOMMUNEDK", "values": ["*"]},
            {"code": "PASKAT", "values": ["3"]},
            {"code": "Tid", "values": ["2023"]},
        ])
        result = {}
        national = None
        for row in rows:
            kode = row.get("KOMMUNEDK", "").strip()
            val = parse_value(row.get("INDHOLD", ""))
            if val is None:
                continue
            if kode == "000":
                national = val
            elif kode in VALID_CODES:
                result[kode] = val

    print(f"  {len(result)} kommuner, landsgennemsnit: {national}")
    return result, national


# ---------------------------------------------------------------------------
# LOKALSAMFUND: Kommunale idrætsudgifter
# ---------------------------------------------------------------------------

def fetch_sports_spending() -> tuple[dict[str, float], float | None]:
    """
    IDRFIN02: Kommunale driftsudgifter til idræt pr. indbygger (kr).
    Direkte: mere er bedre (investering i lokalsamfund).
    """
    print("Henter kommunale idrætsudgifter (IDRFIN02)...")
    rows = api_post("IDRFIN02", [
        {"code": "AMT", "values": ["*"]},
        {"code": "FUNKTION", "values": ["TOT"]},
        {"code": "DRANST", "values": ["12"]},  # Drift
        {"code": "Tid", "values": ["2024"]},
    ])

    result = {}
    national = None
    for row in rows:
        kode = row.get("AMT", "").strip()
        val = parse_value(row.get("INDHOLD", ""))
        if val is None:
            continue
        if kode == "000":
            national = val
        elif kode in VALID_CODES:
            result[kode] = val

    # Prøv 2023
    if len(result) < 50:
        print("  Prøver 2023...")
        rows = api_post("IDRFIN02", [
            {"code": "AMT", "values": ["*"]},
            {"code": "FUNKTION", "values": ["TOT"]},
            {"code": "DRANST", "values": ["12"]},
            {"code": "Tid", "values": ["2023"]},
        ])
        result = {}
        national = None
        for row in rows:
            kode = row.get("AMT", "").strip()
            val = parse_value(row.get("INDHOLD", ""))
            if val is None:
                continue
            if kode == "000":
                national = val
            elif kode in VALID_CODES:
                result[kode] = val

    print(f"  {len(result)} kommuner, landsgennemsnit: {national} kr")
    return result, national


# ---------------------------------------------------------------------------
# Hovedprogram
# ---------------------------------------------------------------------------

def fetch_population() -> dict[str, float]:
    print("Henter befolkningstal (FOLK1A)...")
    rows = api_post("FOLK1A", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "KØN", "values": ["TOT"]},
        {"code": "ALDER", "values": ["IALT"]},
        {"code": "Tid", "values": ["2025K1"]},
    ])
    result = {}
    for row in rows:
        kode = row.get("OMRÅDE", "").strip()
        val = parse_value(row.get("INDHOLD", ""))
        if val is not None and (kode in VALID_CODES or kode == "000"):
            result[kode] = val
    print(f"  {len(result)} kommuner")
    return result


def main():
    print("=" * 60)
    print("Henter supplerende sociale indikatorer fra DST")
    print("=" * 60)

    population = fetch_population()
    nat_pop = population.get("000", 5_900_000)

    # === SUNDHED ===
    print("\n--- SUNDHED ---")
    hospital, hosp_nat = fetch_hospital_use()
    gp_dist, gp_nat = fetch_gp_distance()
    sundhed_rows = []
    for kode in sorted(VALID_CODES, key=int):
        h_val = hospital.get(kode)
        h_r = ratio_inverse(h_val, hosp_nat) if h_val is not None and hosp_nat else None
        g_val = gp_dist.get(kode)
        g_r = ratio_inverse(g_val, gp_nat) if g_val is not None and gp_nat else None
        sundhed_rows.append([
            kode,
            h_val if h_val is not None else "",
            h_r if h_r is not None else "",
            g_val if g_val is not None else "",
            g_r if g_r is not None else "",
        ])
    write_csv("sundhed_extra_scores.csv", [
        "kommune_kode",
        "hospital_use_pct", "hospital_use_ratio",
        "gp_distance_km", "gp_distance_ratio",
    ], sundhed_rows)

    # === UDDANNELSE ===
    print("\n--- UDDANNELSE ---")
    low_edu, low_edu_nat = fetch_low_education()
    udd_rows = []
    for kode in sorted(VALID_CODES, key=int):
        val = low_edu.get(kode)
        r = ratio_inverse(val, low_edu_nat) if val is not None and low_edu_nat else None
        udd_rows.append([kode, val or "", r or ""])
    write_csv("uddannelse_extra_scores.csv", [
        "kommune_kode", "low_education_pct", "low_education_ratio",
    ], udd_rows)

    # === BOLIG ===
    print("\n--- BOLIG ---")
    area, area_nat = fetch_housing_area()
    bolig_rows = []
    for kode in sorted(VALID_CODES, key=int):
        val = area.get(kode)
        r = ratio_direct(val, area_nat) if val is not None and area_nat else None
        bolig_rows.append([kode, val or "", r or ""])
    write_csv("bolig_extra_scores.csv", [
        "kommune_kode", "housing_area_m2", "housing_area_ratio",
    ], bolig_rows)

    # === SAMSKABELSE ===
    print("\n--- SAMSKABELSE ---")
    music, music_nat_total = fetch_music_school()
    # Normalisér pr. 1.000 indb.
    music_per_1k = {}
    music_nat_per_1k = None
    if music_nat_total and nat_pop:
        music_nat_per_1k = round(music_nat_total / nat_pop * 1000, 2)
    for kode, count in music.items():
        if kode in population and population[kode] > 0:
            music_per_1k[kode] = round(count / population[kode] * 1000, 2)

    samsk_rows = []
    for kode in sorted(VALID_CODES, key=int):
        val = music_per_1k.get(kode)
        r = ratio_direct(val, music_nat_per_1k) if val is not None and music_nat_per_1k else None
        samsk_rows.append([kode, val or "", r or ""])
    write_csv("samskabelse_extra_scores.csv", [
        "kommune_kode", "music_school_per_1k", "music_school_ratio",
    ], samsk_rows)

    # === LOKALSAMFUND (ekstra) ===
    print("\n--- LOKALSAMFUND (ekstra) ---")
    class_size, class_nat = fetch_class_size()
    daycare, daycare_nat = fetch_daycare_ratio()
    sports_spend, sports_nat = fetch_sports_spending()
    edu_staff, edu_staff_nat = fetch_educated_staff()

    lokal_rows = []
    for kode in sorted(VALID_CODES, key=int):
        cs_val = class_size.get(kode)
        cs_ratio = ratio_inverse(cs_val, class_nat) if cs_val is not None and class_nat else None
        dc_val = daycare.get(kode)
        dc_ratio = ratio_inverse(dc_val, daycare_nat) if dc_val is not None and daycare_nat else None
        sp_val = sports_spend.get(kode)
        sp_ratio = ratio_direct(sp_val, sports_nat) if sp_val is not None and sports_nat else None
        es_val = edu_staff.get(kode)
        es_ratio = ratio_direct(es_val, edu_staff_nat) if es_val is not None and edu_staff_nat else None
        lokal_rows.append([
            kode,
            cs_val or "", cs_ratio or "",
            dc_val or "", dc_ratio or "",
            sp_val or "", sp_ratio or "",
            es_val if es_val is not None else "",
            es_ratio if es_ratio is not None else "",
        ])
    write_csv("lokalsamfund_extra_scores.csv", [
        "kommune_kode",
        "class_size", "class_size_ratio",
        "daycare_ratio_val", "daycare_ratio",
        "sports_spending_kr", "sports_spending_ratio",
        "educated_staff_pct", "educated_staff_ratio",
    ], lokal_rows)

    print("\n" + "=" * 60)
    print("Alle supplerende indikatorer hentet!")
    print("=" * 60)


if __name__ == "__main__":
    main()
