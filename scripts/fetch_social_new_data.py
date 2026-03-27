#!/usr/bin/env python3
"""
fetch_social_new_data.py

Henter nye sociale indikatorer for alle 98 kommuner fra Danmarks Statistik.

Opretter/opdaterer:
  ../data/faellesskaber_scores.csv   (Fællesskaber)
  ../data/lokalsamfund_scores.csv    (Lokalsamfund)
  ../data/mobilitet_scores.csv       (Mobilitet)
  ../data/velfaerd_extra_scores.csv  (Ekstra velfærdsindikatorer)

Indikatorer:
  FÆLLESSKABER:
    - IDRAKT02: Idrætsmedlemskab (andel af befolkningen)
    - STRAF11:  Anmeldte forbrydelser pr. 1.000 indb. (inverteret)

  LOKALSAMFUND:
    - BIB1:     Biblioteksudlån pr. indbygger
    - IDRFAC01: Idrætsfaciliteter pr. 10.000 indb.

  MOBILITET:
    - AFSTB4:   Gennemsnitlig pendlingsafstand (inverteret - kortere er bedre)
    - BIL800:   Familier med bilrådighed (andel)

  VELFÆRD (ekstra):
    - BU43:     Udsatte børn og unge (andel, inverteret)
    - NEET1:    Unge uden for uddannelse/beskæftigelse (inverteret)

Brug:
  python3 fetch_social_new_data.py
"""

import csv
import io
import json
import sys
import time
import urllib.request
from pathlib import Path

API_URL = "https://api.statbank.dk/v1/data"
REQUEST_DELAY = 0.7  # sekunder mellem kald

OUTPUT_DIR = Path(__file__).parent.parent / "data"

# Alle 98 kommuner
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
    """Henter data fra StatBank API via POST (JSON-format med variabelselektion)."""
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


def parse_value(raw: str) -> float | None:
    """Parser en StatBank-værdi til float."""
    raw = raw.strip()
    if raw in ("", "..", ".", "x", "X", "-"):
        return None
    try:
        return float(raw.replace(".", "").replace(",", "."))
    except ValueError:
        return None


def ratio_direct(kommune_val: float, national_avg: float) -> float:
    """Direkte ratio: højere er bedre."""
    if national_avg == 0:
        return 0
    return round((kommune_val / national_avg) * 100, 2)


def ratio_inverse(kommune_val: float, national_avg: float) -> float:
    """Inverteret ratio: lavere er bedre."""
    if kommune_val == 0:
        return 150  # Cap: perfekt score
    return round((national_avg / kommune_val) * 100, 2)


# ---------------------------------------------------------------------------
# FÆLLESSKABER
# ---------------------------------------------------------------------------

def fetch_sports_membership() -> dict[str, float]:
    """
    IDRAKT02: Idrætsorganisationernes medlemskaber som andel af befolkningen.
    Returnerer {kommune_kode: andel_pct}.
    """
    print("Henter idrætsmedlemskab (IDRAKT02)...")
    rows = api_post("IDRAKT02", [
        {"code": "BLSTKOM", "values": ["*"]},
        {"code": "KON", "values": ["10"]},       # Køn i alt
        {"code": "ALDER1", "values": ["TOT"]},    # Alder i alt
        {"code": "Tid", "values": ["2024"]},       # Seneste
    ])
    result = {}
    national = None
    for row in rows:
        kode = row.get("BLSTKOM", "").strip()
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
        rows = api_post("IDRAKT02", [
            {"code": "BLSTKOM", "values": ["*"]},
            {"code": "KON", "values": ["10"]},
            {"code": "ALDER1", "values": ["TOT"]},
            {"code": "Tid", "values": ["2023"]},
        ])
        result = {}
        national = None
        for row in rows:
            kode = row.get("BLSTKOM", "").strip()
            val = parse_value(row.get("INDHOLD", ""))
            if val is None:
                continue
            if kode == "000":
                national = val
            elif kode in VALID_CODES:
                result[kode] = val
    print(f"  {len(result)} kommuner, landsgennemsnit: {national}")
    return result, national


def fetch_crime_rate() -> dict[str, float]:
    """
    STRAF11: Anmeldte forbrydelser pr. kommune (årligt).
    Vi henter alle 4 kvartaler og summerer.
    Returnerer {kommune_kode: antal_forbrydelser}.
    """
    print("Henter kriminalitetsdata (STRAF11)...")
    rows = api_post("STRAF11", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "OVERTRÆD", "values": ["TOT"]},   # I alt
        {"code": "Tid", "values": ["2024K1", "2024K2", "2024K3", "2024K4"]},
    ])
    # Sum kvartaler per kommune
    sums: dict[str, float] = {}
    for row in rows:
        kode = row.get("OMRÅDE", "").strip()
        val = parse_value(row.get("INDHOLD", ""))
        if val is None:
            continue
        if kode in VALID_CODES or kode == "000":
            sums[kode] = sums.get(kode, 0) + val
    # Prøv 2023 hvis 2024 er tom
    if len(sums) < 50:
        print("  Få resultater for 2024, prøver 2023...")
        rows = api_post("STRAF11", [
            {"code": "OMRÅDE", "values": ["*"]},
            {"code": "OVERTRÆD", "values": ["TOT"]},
            {"code": "Tid", "values": ["2023K1", "2023K2", "2023K3", "2023K4"]},
        ])
        sums = {}
        for row in rows:
            kode = row.get("OMRÅDE", "").strip()
            val = parse_value(row.get("INDHOLD", ""))
            if val is None:
                continue
            if kode in VALID_CODES or kode == "000":
                sums[kode] = sums.get(kode, 0) + val

    national = sums.pop("000", None)
    print(f"  {len(sums)} kommuner, landssamlet: {national}")
    return sums, national


def fetch_population() -> dict[str, float]:
    """FOLK1A: Folketal for alle kommuner (til normalisering)."""
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


# ---------------------------------------------------------------------------
# LOKALSAMFUND
# ---------------------------------------------------------------------------

def fetch_library_loans() -> dict[str, float]:
    """
    BIB1: Folkebibliotekernes udlån i alt.
    Returnerer {kommune_kode: antal_udlån}.
    """
    print("Henter biblioteksudlån (BIB1)...")
    rows = api_post("BIB1", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "BNØGLE", "values": ["15110"]},   # Udlån i alt
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
    # Prøv 2022 hvis 2023 er tom
    if len(result) < 50:
        print("  Få resultater for 2023, prøver 2022...")
        rows = api_post("BIB1", [
            {"code": "OMRÅDE", "values": ["*"]},
            {"code": "BNØGLE", "values": ["15110"]},
            {"code": "Tid", "values": ["2022"]},
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
    print(f"  {len(result)} kommuner, landssamlet: {national}")
    return result, national


def fetch_sports_facilities() -> dict[str, float]:
    """
    IDRFAC01: Antal idrætsfaciliteter pr. kommune (alle typer).
    Returnerer {kommune_kode: antal_faciliteter}.
    """
    print("Henter idrætsfaciliteter (IDRFAC01)...")
    rows = api_post("IDRFAC01", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "IDRFAC", "values": ["*"]},     # Alle typer
        {"code": "Tid", "values": ["2024"]},
    ])
    # Summer alle facilitetstyper per kommune
    sums: dict[str, float] = {}
    for row in rows:
        kode = row.get("OMRÅDE", "").strip()
        val = parse_value(row.get("INDHOLD", ""))
        if val is None:
            continue
        if kode in VALID_CODES or kode == "000":
            sums[kode] = sums.get(kode, 0) + val
    # Prøv 2023 hvis 2024 er tom
    if len(sums) < 50:
        print("  Få resultater for 2024, prøver 2023...")
        rows = api_post("IDRFAC01", [
            {"code": "OMRÅDE", "values": ["*"]},
            {"code": "IDRFAC", "values": ["*"]},
            {"code": "Tid", "values": ["2023"]},
        ])
        sums = {}
        for row in rows:
            kode = row.get("OMRÅDE", "").strip()
            val = parse_value(row.get("INDHOLD", ""))
            if val is None:
                continue
            if kode in VALID_CODES or kode == "000":
                sums[kode] = sums.get(kode, 0) + val

    national = sums.pop("000", None)
    print(f"  {len(sums)} kommuner, landssamlet: {national}")
    return sums, national


# ---------------------------------------------------------------------------
# MOBILITET
# ---------------------------------------------------------------------------

def fetch_commute_distance() -> tuple[dict[str, float], float | None]:
    """
    AFSTB4: Gennemsnitlig pendlingsafstand (km) for beskæftigede.
    Returnerer {kommune_kode: km}, national_avg.
    """
    print("Henter pendlingsafstand (AFSTB4)...")
    rows = api_post("AFSTB4", [
        {"code": "BOPOMR", "values": ["*"]},
        {"code": "SOCIO", "values": ["02"]},     # Beskæftigede i alt
        {"code": "KØN", "values": ["TOT"]},
        {"code": "Tid", "values": ["2023"]},
    ])
    result = {}
    national = None
    for row in rows:
        kode = row.get("BOPOMR", "").strip()
        val = parse_value(row.get("INDHOLD", ""))
        if val is None:
            continue
        if kode == "000":
            national = val
        elif kode in VALID_CODES:
            result[kode] = val
    # Prøv 2022 hvis 2023 er tom
    if len(result) < 50:
        print("  Få resultater for 2023, prøver 2022...")
        rows = api_post("AFSTB4", [
            {"code": "BOPOMR", "values": ["*"]},
            {"code": "SOCIO", "values": ["02"]},
            {"code": "KØN", "values": ["TOT"]},
            {"code": "Tid", "values": ["2022"]},
        ])
        result = {}
        national = None
        for row in rows:
            kode = row.get("BOPOMR", "").strip()
            val = parse_value(row.get("INDHOLD", ""))
            if val is None:
                continue
            if kode == "000":
                national = val
            elif kode in VALID_CODES:
                result[kode] = val
    print(f"  {len(result)} kommuner, landsgennemsnit: {national} km")
    return result, national


def fetch_car_access() -> dict[str, tuple[float, float]]:
    """
    BIL800: Familiernes bilrådighed.
    Returnerer {kommune_kode: (familier_med_bil, familier_total)}.
    """
    print("Henter bilrådighed (BIL800)...")
    rows = api_post("BIL800", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "RAADMOENS", "values": ["10000", "10210"]},  # I alt + med bil i alt
        {"code": "Tid", "values": ["2024"]},
    ])
    totals: dict[str, float] = {}
    with_car: dict[str, float] = {}
    for row in rows:
        kode = row.get("OMRÅDE", "").strip()
        raad = row.get("RAADMOENS", "").strip()
        val = parse_value(row.get("INDHOLD", ""))
        if val is None:
            continue
        if kode not in VALID_CODES and kode != "000":
            continue
        if raad == "10000":
            totals[kode] = val
        elif raad == "10210":
            with_car[kode] = val
    # Prøv 2023 hvis 2024 er tom
    if len(totals) < 50:
        print("  Få resultater for 2024, prøver 2023...")
        rows = api_post("BIL800", [
            {"code": "OMRÅDE", "values": ["*"]},
            {"code": "RAADMOENS", "values": ["10000", "10210"]},
            {"code": "Tid", "values": ["2023"]},
        ])
        totals = {}
        with_car = {}
        for row in rows:
            kode = row.get("OMRÅDE", "").strip()
            raad = row.get("RAADMOENS", "").strip()
            val = parse_value(row.get("INDHOLD", ""))
            if val is None:
                continue
            if kode not in VALID_CODES and kode != "000":
                continue
            if raad == "10000":
                totals[kode] = val
            elif raad == "10210":
                with_car[kode] = val

    result = {}
    for kode in totals:
        if kode in with_car and totals[kode] > 0:
            result[kode] = (with_car[kode], totals[kode])
    print(f"  {len(result)} kommuner")
    return result


# ---------------------------------------------------------------------------
# VELFÆRD (ekstra)
# ---------------------------------------------------------------------------

def fetch_vulnerable_children() -> tuple[dict[str, float], float | None]:
    """
    BU43: Udsatte børn og unge (andel af 0-22-årige).
    Returnerer {kommune_kode: andel_pct}, national_avg.
    """
    print("Henter udsatte børn (BU43)...")
    rows = api_post("BU43", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "FORANSTALT", "values": ["IALT"]},   # Udsatte i alt
        {"code": "ALDER", "values": ["TOT22"]},        # 0-22 år
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
        print("  Få resultater for 2024, prøver 2023...")
        rows = api_post("BU43", [
            {"code": "OMRÅDE", "values": ["*"]},
            {"code": "FORANSTALT", "values": ["IALT"]},
            {"code": "ALDER", "values": ["TOT22"]},
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
    print(f"  {len(result)} kommuner, landsgennemsnit: {national}%")
    return result, national


def fetch_neet() -> tuple[dict[str, float], float | None]:
    """
    NEET1: Unge 16-24 år uden for uddannelse og beskæftigelse.
    Returnerer antal NEET pr. kommune og nationalt.
    Skal normaliseres mod ungdomsbefolkningen.
    """
    print("Henter NEET-unge (NEET1)...")
    # Hent NEET-antal
    neet_rows = api_post("NEET1", [
        {"code": "STATUSNEET", "values": ["10"]},   # Ikke-aktive (NEET)
        {"code": "KØN", "values": ["TOT"]},
        {"code": "BOPOMR", "values": ["*"]},
        {"code": "SOCIO", "values": ["TOT"]},
        {"code": "Tid", "values": ["2023"]},
    ])
    neet: dict[str, float] = {}
    for row in neet_rows:
        kode = row.get("BOPOMR", "").strip()
        val = parse_value(row.get("INDHOLD", ""))
        if val is not None and (kode in VALID_CODES or kode == "000"):
            neet[kode] = val

    # Hent total 16-24 årige
    total_rows = api_post("NEET1", [
        {"code": "STATUSNEET", "values": ["00"]},   # Alle
        {"code": "KØN", "values": ["TOT"]},
        {"code": "BOPOMR", "values": ["*"]},
        {"code": "SOCIO", "values": ["TOT"]},
        {"code": "Tid", "values": ["2023"]},
    ])
    total: dict[str, float] = {}
    for row in total_rows:
        kode = row.get("BOPOMR", "").strip()
        val = parse_value(row.get("INDHOLD", ""))
        if val is not None and (kode in VALID_CODES or kode == "000"):
            total[kode] = val

    # Beregn NEET-andel
    result = {}
    for kode in neet:
        if kode in total and total[kode] > 0:
            result[kode] = round((neet[kode] / total[kode]) * 100, 2)

    national = result.pop("000", None)
    print(f"  {len(result)} kommuner, landsgennemsnit NEET-andel: {national}%")
    return result, national


# ---------------------------------------------------------------------------
# Hovedprogram
# ---------------------------------------------------------------------------

def write_csv(filename: str, headers: list[str], rows: list[list]) -> None:
    """Skriver CSV-fil til data-mappen."""
    filepath = OUTPUT_DIR / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
    print(f"  Gemt: {filepath} ({len(rows)} rækker)")


def main():
    print("=" * 60)
    print("Henter nye sociale indikatorer fra Danmarks Statistik")
    print("=" * 60)

    population = fetch_population()
    nat_pop = population.get("000", 5_900_000)

    # === FÆLLESSKABER ===
    print("\n--- FÆLLESSKABER ---")

    sports, sports_nat = fetch_sports_membership()
    crime_raw, crime_nat_total = fetch_crime_rate()

    # Kriminalitet pr. 1.000 indb.
    crime_per_1k = {}
    crime_nat_per_1k = None
    if crime_nat_total and nat_pop:
        crime_nat_per_1k = round(crime_nat_total / nat_pop * 1000, 2)
    for kode, count in crime_raw.items():
        if kode in population and population[kode] > 0:
            crime_per_1k[kode] = round(count / population[kode] * 1000, 2)

    faellesskab_rows = []
    for kode in sorted(VALID_CODES, key=int):
        s_val = sports.get(kode)
        s_ratio = ratio_direct(s_val, sports_nat) if s_val is not None and sports_nat else None
        c_val = crime_per_1k.get(kode)
        c_ratio = ratio_inverse(c_val, crime_nat_per_1k) if c_val is not None and crime_nat_per_1k else None
        faellesskab_rows.append([
            kode,
            s_val if s_val is not None else "",
            s_ratio if s_ratio is not None else "",
            c_val if c_val is not None else "",
            c_ratio if c_ratio is not None else "",
        ])

    write_csv("faellesskaber_scores.csv", [
        "kommune_kode",
        "sports_membership_pct", "sports_membership_ratio",
        "crime_per_1k", "crime_ratio",
    ], faellesskab_rows)

    # === LOKALSAMFUND ===
    print("\n--- LOKALSAMFUND ---")

    library_raw, library_nat_total = fetch_library_loans()
    facilities_raw, facilities_nat_total = fetch_sports_facilities()

    # Bibliotek pr. indbygger
    lib_per_cap = {}
    lib_nat_per_cap = None
    if library_nat_total and nat_pop:
        lib_nat_per_cap = round(library_nat_total / nat_pop, 2)
    for kode, count in library_raw.items():
        if kode in population and population[kode] > 0:
            lib_per_cap[kode] = round(count / population[kode], 2)

    # Faciliteter pr. 10.000 indb.
    fac_per_10k = {}
    fac_nat_per_10k = None
    if facilities_nat_total and nat_pop:
        fac_nat_per_10k = round(facilities_nat_total / nat_pop * 10000, 2)
    for kode, count in facilities_raw.items():
        if kode in population and population[kode] > 0:
            fac_per_10k[kode] = round(count / population[kode] * 10000, 2)

    lokal_rows = []
    for kode in sorted(VALID_CODES, key=int):
        l_val = lib_per_cap.get(kode)
        l_ratio = ratio_direct(l_val, lib_nat_per_cap) if l_val is not None and lib_nat_per_cap else None
        f_val = fac_per_10k.get(kode)
        f_ratio = ratio_direct(f_val, fac_nat_per_10k) if f_val is not None and fac_nat_per_10k else None
        lokal_rows.append([
            kode,
            l_val if l_val is not None else "",
            l_ratio if l_ratio is not None else "",
            f_val if f_val is not None else "",
            f_ratio if f_ratio is not None else "",
        ])

    write_csv("lokalsamfund_scores.csv", [
        "kommune_kode",
        "library_loans_per_cap", "library_ratio",
        "facilities_per_10k", "facilities_ratio",
    ], lokal_rows)

    # === MOBILITET ===
    print("\n--- MOBILITET ---")

    commute, commute_nat = fetch_commute_distance()
    car_data = fetch_car_access()

    # Bilrådighed - pct med bil
    car_pct = {}
    for kode, (with_car, total) in car_data.items():
        car_pct[kode] = round((with_car / total) * 100, 2)
    car_nat = car_pct.pop("000", None)

    mobil_rows = []
    for kode in sorted(VALID_CODES, key=int):
        d_val = commute.get(kode)
        d_ratio = ratio_inverse(d_val, commute_nat) if d_val is not None and commute_nat else None
        c_val = car_pct.get(kode)
        c_ratio = ratio_direct(c_val, car_nat) if c_val is not None and car_nat else None
        mobil_rows.append([
            kode,
            d_val if d_val is not None else "",
            d_ratio if d_ratio is not None else "",
            c_val if c_val is not None else "",
            c_ratio if c_ratio is not None else "",
        ])

    write_csv("mobilitet_scores.csv", [
        "kommune_kode",
        "commute_distance_km", "commute_ratio",
        "car_access_pct", "car_access_ratio",
    ], mobil_rows)

    # === VELFÆRD (ekstra) ===
    print("\n--- VELFÆRD (ekstra) ---")

    vulnerable, vuln_nat = fetch_vulnerable_children()
    neet_data, neet_nat = fetch_neet()

    velfaerd_rows = []
    for kode in sorted(VALID_CODES, key=int):
        v_val = vulnerable.get(kode)
        v_ratio = ratio_inverse(v_val, vuln_nat) if v_val is not None and vuln_nat else None
        n_val = neet_data.get(kode)
        n_ratio = ratio_inverse(n_val, neet_nat) if n_val is not None and neet_nat else None
        velfaerd_rows.append([
            kode,
            v_val if v_val is not None else "",
            v_ratio if v_ratio is not None else "",
            n_val if n_val is not None else "",
            n_ratio if n_ratio is not None else "",
        ])

    write_csv("velfaerd_extra_scores.csv", [
        "kommune_kode",
        "vulnerable_children_pct", "vulnerable_children_ratio",
        "neet_pct", "neet_ratio",
    ], velfaerd_rows)

    print("\n" + "=" * 60)
    print("Alle nye sociale indikatorer hentet!")
    print("=" * 60)


if __name__ == "__main__":
    main()
