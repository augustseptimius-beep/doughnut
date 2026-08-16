#!/usr/bin/env python3
"""
fetch_sundhed_extra.py

Henter supplerende sundhedsindikatorer til Doughnut-webapp'en.

  Del 1: Downloader og inspicerer Excel-filer fra Sundhedsdatabank.dk
          (gemmer til data/sundhedsdatabank/ og printer kommuneniveau-rapport)
  Del 2: Henter antidepressiva-forbrug pr. kommune (DST MEDI1 N06)
  Del 3: Henter lægekontaktrate pr. kommune (DST SYGP1)
  Del 4: Opdaterer data/master_indicators.csv automatisk

Kør fra projektets rodmappe:
  python3 scripts/fetch_sundhed_extra.py
"""

from __future__ import annotations

import csv
import io
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dst_aar import seneste_kvartal  # noqa: E402

API_URL = "https://api.statbank.dk/v1/data"
REQUEST_DELAY = 0.7

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SUNDHED_DIR = DATA_DIR / "sundhedsdatabank"
OUTPUT_DIR = DATA_DIR

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

# Sundhedsdatabank.dk Excel-filer der er værd at inspicere
SUNDHEDSDATABANK_FILES = [
    {
        "filename": "selvmord_monitoring_2016-2023.xlsx",
        "url": (
            "https://cdn1.gopublic.dk/sundhedsdatastyrelsen/Media/639044950725012172/"
            "Monitorering%20af%20selvmord%20og%20selvmordsforso%CC%88g%20"
            "%28udgivet%2020.%20januar%202026%29.xlsx"
        ),
        "beskrivelse": "Monitorering af selvmord og selvmordsforsøg 2016-2023",
    },
    {
        "filename": "ruks_kroniske_sygdomme_2010-2025.xlsx",
        "url": (
            "https://cdn1.gopublic.dk/sundhedsdatastyrelsen/Media/"
            "638834834539375609/RUKS-2010-2025-udgivet-28-november-2025.xlsx"
        ),
        "beskrivelse": "Kroniske sygdomme og svære psykiske lidelser (RUKS) 2010-2025",
    },
]


# ---------------------------------------------------------------------------
# Hjælpefunktioner
# ---------------------------------------------------------------------------

def parse_value(raw: str) -> float | None:
    raw = raw.strip()
    if raw in ("", "..", ".", "x", "X", "-"):
        return None
    try:
        return float(raw.replace(".", "").replace(",", "."))
    except ValueError:
        return None


def ratio_direct(val: float, nat: float) -> float:
    if nat == 0:
        return 0
    return round((val / nat) * 100, 2)


def ratio_inverse(val: float, nat: float) -> float:
    if val == 0:
        return 150
    return round((nat / val) * 100, 2)


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


def write_csv(filename: str, headers: list[str], rows: list[list]) -> None:
    filepath = OUTPUT_DIR / filename
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
    print(f"  Gemt: {filepath} ({len(rows)} rækker)")


# ---------------------------------------------------------------------------
# DEL 1: Sundhedsdatabank.dk - download og inspicér Excel-filer
# ---------------------------------------------------------------------------

def download_and_inspect_sundhedsdatabank():
    print("\n" + "=" * 60)
    print("DEL 1: Sundhedsdatabank.dk Excel-filer")
    print("=" * 60)

    SUNDHED_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Mappe: {SUNDHED_DIR}")

    try:
        import openpyxl
    except ImportError:
        print("\n⚠  openpyxl er ikke installeret. Springer Excel-inspektion over.")
        print("  Installer med: pip3 install openpyxl")
        print("  Download-del springes over, men DST-data hentes stadig.\n")
        _download_only()
        return

    for fil in SUNDHEDSDATABANK_FILES:
        dest = SUNDHED_DIR / fil["filename"]
        print(f"\n--- {fil['beskrivelse']} ---")

        if dest.exists():
            print(f"  Allerede downloadet: {dest.name}")
        else:
            print(f"  Downloader {fil['filename']}...")
            try:
                req = urllib.request.Request(
                    fil["url"],
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = resp.read()
                with open(dest, "wb") as f:
                    f.write(data)
                print(f"  Gemt: {dest} ({len(data):,} bytes)")
            except Exception as e:
                print(f"  ✗ Download fejlede: {e}")
                continue

        # Inspicér Excel-filen
        try:
            wb = openpyxl.load_workbook(dest, read_only=True, data_only=True)
            print(f"  Sheets ({len(wb.sheetnames)}): {wb.sheetnames}")

            kommune_fund = []
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                headers = []
                for row in ws.iter_rows(min_row=1, max_row=5, values_only=True):
                    for cell in row:
                        if isinstance(cell, str):
                            headers.append(cell.lower())
                header_tekst = " ".join(headers)
                if any(k in header_tekst for k in ["kommune", "komm", "kode"]):
                    kommune_fund.append(sheet_name)

            if kommune_fund:
                print(f"  ✓ KOMMUNENIVEAU-DATA FUNDET i sheets: {kommune_fund}")
            else:
                print(f"  ✗ Ingen kommuneniveau-kolonner fundet i nogen sheets")

            wb.close()
        except Exception as e:
            print(f"  ✗ Kunne ikke åbne Excel-fil: {e}")


def _download_only():
    for fil in SUNDHEDSDATABANK_FILES:
        dest = SUNDHED_DIR / fil["filename"]
        if dest.exists():
            print(f"  Allerede downloadet: {dest.name}")
            continue
        print(f"  Downloader {fil['filename']}...")
        try:
            req = urllib.request.Request(
                fil["url"],
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            with open(dest, "wb") as f:
                f.write(data)
            print(f"  Gemt: {dest} ({len(data):,} bytes)")
        except Exception as e:
            print(f"  ✗ Download fejlede: {e}")


# ---------------------------------------------------------------------------
# DEL 2: DST MEDI1 - Antidepressiva-forbrug pr. kommune (N06)
# ---------------------------------------------------------------------------

def fetch_antidepressiva() -> tuple[dict[str, float], float | None]:
    """
    MEDI1: Psykoanaleptika (N06 = antidepressiva + ADHD-medicin + demens-medicin)
    BNØGLE 1100 = Recepter pr. 100 borgere - allerede en rate, ingen normalisering nødvendig.
    Returnerer {kommune_kode: recepter_pr_100}, national_avg.
    """
    print("Henter antidepressiva-forbrug (MEDI1 N06)...")
    for year in ["2024", "2023"]:
        rows = api_post("MEDI1", [
            {"code": "KOMMUNEDK", "values": ["*"]},
            {"code": "BNØGLE", "values": ["1100"]},        # Recepter pr. 100 borgere
            {"code": "MEDICINTYPE", "values": ["N06"]},    # Psykoanaleptika
            {"code": "ALERAMS", "values": ["0000"]},       # Alle aldre i alt
            {"code": "Tid", "values": [year]},
        ])
        result: dict[str, float] = {}
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
        if len(result) >= 50:
            print(f"  {len(result)} kommuner (år: {year}), landsgennemsnit: {national} recepter/100 borgere")
            return result, national
        print(f"  Kun {len(result)} kommuner for {year}, prøver ældre...")
    print(f"  ⚠  Kun {len(result)} kommuner - fortsætter med ufuldstændig data")
    return result, national


# ---------------------------------------------------------------------------
# DEL 3: DST SYGP1 - Lægekontaktrate pr. kommune
# ---------------------------------------------------------------------------

def fetch_population() -> dict[str, float]:
    print("Henter befolkningstal (FOLK1A)...")
    rows = api_post("FOLK1A", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "KØN", "values": ["TOT"]},
        {"code": "ALDER", "values": ["IALT"]},
        {"code": "Tid", "values": [seneste_kvartal("FOLK1A", "K1", fallback="2025K1")]},
    ])
    result = {}
    for row in rows:
        kode = row.get("OMRÅDE", "").strip()
        val = parse_value(row.get("INDHOLD", ""))
        if val is not None and (kode in VALID_CODES or kode == "000"):
            result[kode] = val
    print(f"  {len(result)} kommuner")
    return result


def fetch_laegekontakt(population: dict[str, float]) -> tuple[dict[str, float], float | None]:
    """
    SYGP1: Antal personer med kontakt til almen læge (YDELSESART=130).
    Beregner andel af befolkning med mindst én lægekontakt.
    Returnerer {kommune_kode: andel_pct}, national_avg.
    """
    print("Henter lægekontaktrate (SYGP1)...")
    nat_pop = population.get("000", 5_900_000)

    for year in ["2024", "2023"]:
        rows = api_post("SYGP1", [
            {"code": "OMRÅDE", "values": ["*"]},
            {"code": "YDELSESART", "values": ["130"]},    # Almen læge i alt
            {"code": "ALERAMS", "values": ["IALT"]},       # Alle aldre
            {"code": "KØN", "values": ["TOT"]},
            {"code": "Tid", "values": [year]},
        ])
        persons: dict[str, float] = {}
        for row in rows:
            kode = row.get("OMRÅDE", "").strip()
            val = parse_value(row.get("INDHOLD", ""))
            if val is not None and (kode in VALID_CODES or kode == "000"):
                persons[kode] = val

        if len(persons) < 50:
            print(f"  Kun {len(persons)} kommuner for {year}, prøver ældre...")
            continue

        # Beregn andel af befolkning
        result: dict[str, float] = {}
        national = None
        nat_persons = persons.get("000")
        if nat_persons and nat_pop:
            national = round((nat_persons / nat_pop) * 100, 2)
        for kode in VALID_CODES:
            if kode in persons and kode in population and population[kode] > 0:
                result[kode] = round((persons[kode] / population[kode]) * 100, 2)

        print(f"  {len(result)} kommuner (år: {year}), landsgennemsnit: {national}%")
        return result, national

    print(f"  ⚠  Ikke nok data - fortsætter med ufuldstændig data")
    return {}, None


# ---------------------------------------------------------------------------
# DEL 4: DST LABY26 - Børneovervægt pr. kommune (6-7-årige, 2018)
# ---------------------------------------------------------------------------

def fetch_boerneovervaeght() -> tuple[dict[str, float], float | None]:
    """
    LABY26: Overvægt blandt børn 6-7 år, køn i alt.
    Data kun tilgængeligt til 2018. KOMGRP-variablen indeholder både
    kommunegrupper og individuelle kommunekoder.
    Returnerer {kommune_kode: andel_pct}, national_avg.
    """
    print("Henter børneovervægt (LABY26, 6-7 år, 2018)...")
    rows = api_post("LABY26", [
        {"code": "KOMGRP", "values": ["*"]},
        {"code": "KØN", "values": ["00"]},          # Køn i alt
        {"code": "ALDER", "values": ["6-7IND"]},    # 6-7-årige (skolestart)
        {"code": "Tid", "values": ["2018"]},         # Seneste tilgængelige år
    ])
    result: dict[str, float] = {}
    national = None
    for row in rows:
        kode = row.get("KOMGRP", "").strip()
        val = parse_value(row.get("INDHOLD", ""))
        if val is None:
            continue
        if kode == "000":
            national = val
        elif kode in VALID_CODES:
            result[kode] = val
    print(f"  {len(result)} kommuner (år: 2018), landsgennemsnit: {national}%")
    return result, national


# ---------------------------------------------------------------------------
# DEL 5: DST HJEMSYG - Hjemmesygepleje-modtagere pr. kommune
# ---------------------------------------------------------------------------

def fetch_hjemsyg(population: dict[str, float]) -> tuple[dict[str, float], float | None]:
    """
    HJEMSYG: Modtagere af hjemmesygepleje (eget hjem), alle aldre.
    Normaliseres til pr. 1.000 indbyggere vha. FOLK1A-befolkningstal.
    Returnerer {kommune_kode: modtagere_pr_1000}, national_avg.
    """
    print("Henter hjemmesygepleje-modtagere (HJEMSYG)...")
    nat_pop = population.get("000", 5_900_000)

    for year in ["2025", "2024", "2023"]:
        rows = api_post("HJEMSYG", [
            {"code": "OMRÅDE", "values": ["*"]},
            {"code": "ALDER1", "values": ["050"]},   # Alder i alt
            {"code": "KOEN", "values": ["100"]},      # Mænd og kvinder i alt
            {"code": "Tid", "values": [year]},
        ])
        counts: dict[str, float] = {}
        for row in rows:
            kode = row.get("OMRÅDE", "").strip()
            val = parse_value(row.get("INDHOLD", ""))
            if val is not None and kode in VALID_CODES:
                counts[kode] = val

        if len(counts) < 50:
            print(f"  Kun {len(counts)} kommuner for {year}, prøver ældre...")
            continue

        result: dict[str, float] = {}
        nat_count = sum(counts.values())
        national = round(nat_count / nat_pop * 1000, 2) if nat_pop else None
        for kode, count in counts.items():
            if kode in population and population[kode] > 0:
                result[kode] = round(count / population[kode] * 1000, 2)

        print(f"  {len(result)} kommuner (år: {year}), landsgennemsnit: {national} pr. 1.000 indb.")
        return result, national

    print("  ⚠  Ikke nok data")
    return {}, None


# ---------------------------------------------------------------------------
# Hovedprogram
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Henter supplerende sundhedsindikatorer")
    print("=" * 60)

    # DEL 1
    download_and_inspect_sundhedsdatabank()

    # DEL 2
    print("\n" + "=" * 60)
    print("DEL 2: Antidepressivt forbrug (DST MEDI1)")
    print("=" * 60)
    medicin_data, medicin_nat = fetch_antidepressiva()

    # DEL 3
    print("\n" + "=" * 60)
    print("DEL 3: Lægekontaktrate (DST SYGP1)")
    print("=" * 60)
    population = fetch_population()
    laege_data, laege_nat = fetch_laegekontakt(population)

    # DEL 4
    print("\n" + "=" * 60)
    print("DEL 4: Børneovervægt (DST LABY26)")
    print("=" * 60)
    overvaeght_data, overvaeght_nat = fetch_boerneovervaeght()

    # DEL 5
    print("\n" + "=" * 60)
    print("DEL 5: Hjemmesygepleje (DST HJEMSYG)")
    print("=" * 60)
    hjemsyg_data, hjemsyg_nat = fetch_hjemsyg(population)

    # Skriv CSV'er
    print("\n--- Gemmer CSV'er ---")

    medicin_rows = []
    for kode in sorted(VALID_CODES, key=int):
        val = medicin_data.get(kode)
        ratio = ratio_inverse(val, medicin_nat) if val is not None and medicin_nat else ""
        medicin_rows.append([kode, val if val is not None else "", ratio])
    write_csv("medicin_scores.csv", [
        "kommune_kode", "medicin_raw", "medicin_ratio",
    ], medicin_rows)

    laege_rows = []
    for kode in sorted(VALID_CODES, key=int):
        val = laege_data.get(kode)
        ratio = ratio_direct(val, laege_nat) if val is not None and laege_nat else ""
        laege_rows.append([kode, val if val is not None else "", ratio])
    write_csv("laegekontakt_scores.csv", [
        "kommune_kode", "laegekontakt_raw", "laegekontakt_ratio",
    ], laege_rows)

    overvaeght_rows = []
    for kode in sorted(VALID_CODES, key=int):
        val = overvaeght_data.get(kode)
        ratio = ratio_inverse(val, overvaeght_nat) if val is not None and overvaeght_nat else ""
        overvaeght_rows.append([kode, val if val is not None else "", ratio])
    write_csv("boerneovervaeght_scores.csv", [
        "kommune_kode", "boerneovervaeght_raw", "boerneovervaeght_ratio",
    ], overvaeght_rows)

    hjemsyg_rows = []
    for kode in sorted(VALID_CODES, key=int):
        val = hjemsyg_data.get(kode)
        ratio = ratio_inverse(val, hjemsyg_nat) if val is not None and hjemsyg_nat else ""
        hjemsyg_rows.append([kode, val if val is not None else "", ratio])
    write_csv("hjemsyg_scores.csv", [
        "kommune_kode", "hjemsyg_raw", "hjemsyg_ratio",
    ], hjemsyg_rows)

    print("\n" + "=" * 60)
    print("Alle sundhedsdata hentet!")
    print("=" * 60)


if __name__ == "__main__":
    main()

    try:
        import sys as _sys
        from pathlib import Path as _Path
        _sys.path.insert(0, str(_Path(__file__).resolve().parent))
        from build_master_csv import auto_build_master
        auto_build_master()
    except Exception as _e:
        print(f"\n⚠ Kunne ikke auto-rebuild master-CSV: {_e}")
        print("  Kør manuelt: python3 scripts/build_master_csv.py")
