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
    - BIB3A:    Biblioteksudlån pr. indbygger (afløser BIB1, som DST har gjort inaktiv)
    - IDRFAC01: Idrætsfaciliteter pr. 10.000 indb.

  MOBILITET:
    - AFSTB4:   Gennemsnitlig pendlingsafstand (inverteret - kortere er bedre)
    - BIL800:   Familier med bilrådighed (andel, scores ikke - se shared.ts)
    Offentlig transport hentes af fetch_offentlig_transport.py (LABY49 findes
    kun pr. kommunegruppe, så platformen beregner tallet pr. kommune selv).

  VELFÆRD (ekstra):
    - BU43:     Udsatte børn og unge (andel, inverteret)
    - NEET3:    Unge 16-24 år uden for uddannelse/beskæftigelse (inverteret)

Brug:
  python3 fetch_social_new_data.py
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dst_aar import (seneste_aar, seneste_aar_liste, seneste_periode,  # noqa: E402
                     seneste_kvartal, hele_aar_kvartaler, perioder)
from dst import andel, api_post, parse_value, pr_indbygger, pr_kommune_aar, seneste  # noqa: E402  (fælles DST-kald, scripts/dst.py)
from kommuner import KODER as VALID_CODES  # noqa: E402  (de 98 kommuner, data/kommuner.json)


OUTPUT_DIR = Path(__file__).parent.parent / "data"


def _tom(v):
    """Tom celle for manglende værdi (men 0 bevares, modsat `v or ""`)."""
    return "" if v is None else v


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
        {"code": "Tid", "values": [seneste_aar("IDRAKT02", fallback="2024")]},       # Seneste
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


def serie_crime_rate(aar: list[str]) -> dict[tuple[str, str], float]:
    """STRAF11: anmeldte forbrydelser i alt pr. 1.000 indb., {(kommune_kode, år): værdi}
    inkl. hele landet (000). Årstallet er summen af fire kvartaler, og kun år
    med alle fire kvartaler tages med - et halvfærdigt år ville give et
    kunstigt lavt tal. Folketallet er 1. januar samme år. Bruges af både scoren
    og retningspilen (fetch_trend_history.py)."""
    findes = set(perioder("STRAF11"))
    hele = [a for a in aar if all(f"{a}K{k}" in findes for k in range(1, 5))]
    if not hele:
        return {}
    rows = api_post("STRAF11", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "OVERTRÆD", "values": ["TOT"]},   # I alt
        {"code": "Tid", "values": [f"{a}K{k}" for a in hele for k in range(1, 5)]},
    ])
    return pr_indbygger(pr_kommune_aar(rows), 1000, 2)


def fetch_crime_rate() -> tuple[dict[str, float], float | None]:
    """Anmeldte forbrydelser pr. 1.000 indb. i nyeste hele år, og landstallet."""
    print("Henter kriminalitetsdata (STRAF11)...")
    aar, _ = hele_aar_kvartaler("STRAF11")
    aar, result, national = seneste(serie_crime_rate([aar]), tabel="STRAF11")
    print(f"  {len(result)} kommuner ({aar}), landstal: {national} pr. 1.000")
    return result, national


def serie_traffic_accidents(aar: list[str]) -> dict[tuple[str, str], float]:
    """
    UHELDK1: tilskadekomne og dræbte i færdselsuheld (UHELD=0, personskade i
    alt, summeret over transportmidler, alder og køn) pr. 100.000 indb.

    TREÅRIGT GENNEMSNIT (indført sep. 2026). Ét års tal er ren støj i små
    kommuner: Læsø lå på 118,8 pr. 100.000 i 2024, hvilket med kommunens
    indbyggertal svarer til omkring to tilskadekomne. Én ulykke fra eller til
    flyttede scoren med titalls point, og kommunen kunne ikke gøre noget ved
    det. Samme greb som vejr_skader, der også bruger flere år.

    Værdien for år Y er gennemsnittet af raterne for Y-2, Y-1 og Y, hver med
    folketallet 1. januar samme år, så retningspilen (fetch_trend_history.py)
    følger præcis samme tal som scoren. Returnerer {(kommune_kode, Y): værdi}
    inkl. hele landet (000); år uden tre forudgående år med data udelades.
    """
    findes = {p for p in perioder("UHELDK1") if re.fullmatch(r"\d{4}", p)}
    alle = sorted({str(int(a) - d) for a in aar for d in range(3)} & findes)
    if not alle:
        return {}
    # INDBLAND, ALDER og KØN udelades, så DST lægger alle kategorier sammen
    # (ingen af dem har en "i alt"-værdi). Samme tal som at bede om "*" og
    # summere selv - efterprøvet 2023-2025 - men med "*" på alle tre bliver en
    # tidsserie fra 2010 for stor til DST's CSV-grænse (HTTP 400).
    rows = api_post("UHELDK1", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "UHELD", "values": ["0"]},       # Personskade i alt
        {"code": "Tid", "values": alle},
    ])
    rate = pr_indbygger(pr_kommune_aar(rows), 100_000, 4)
    ud: dict[tuple[str, str], float] = {}
    for kode in {k for k, _ in rate}:
        for a in aar:
            tre = [rate.get((kode, str(int(a) - d))) for d in range(3)]
            if all(v is not None for v in tre):
                ud[(kode, a)] = round(sum(tre) / 3, 2)
    return ud


def fetch_traffic_accidents() -> tuple[dict[str, float], float | None]:
    """Treårigt gennemsnit af tilskadekomne pr. 100.000 indb. og landstallet,
    se serie_traffic_accidents()."""
    aar = seneste_aar_liste("UHELDK1", 1, fallback=["2024"])
    print(f"Henter trafikulykker (UHELDK1, {int(aar[0]) - 2}-{aar[0]}, treårigt gennemsnit)...")
    aar, result, national = seneste(serie_traffic_accidents(aar), tabel="UHELDK1")
    print(f"  {len(result)} kommuner, landstal: {national} pr. 100.000")
    return result, national


def fetch_population() -> dict[str, float]:
    """FOLK1A: Folketal for alle kommuner (til normalisering)."""
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


# ---------------------------------------------------------------------------
# LOKALSAMFUND
# ---------------------------------------------------------------------------

def serie_library_use(aar: list[str]) -> dict[tuple[str, str], float]:
    """
    BIB3A: folkebibliotekernes udlån (alle materialetyper, børne- + voksensamling)
    pr. indbygger, {(kommune_kode, år): udlån pr. indb.} inkl. hele landet (000).
    Folketallet er 1. januar samme år. Bruges af både scoren og retningspilen.

    Skiftet fra BIB1 aug. 2026: DST har markeret BIB1 som INAKTIV (den stopper
    ved 2024). BIB3A er den aktive afløser og indeholder samme tal - efterprøvet
    på Thisted, København, Aalborg og Slagelse for 2022-2024: 0,0% afvigelse.
    BIB3A splitter på SAMLING (børn/voksne), så begge SKAL summeres for at
    ramme BIB1's "Udlån i alt".
    """
    rows = api_post("BIB3A", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "OPGOER1", "values": ["14"]},      # Udlån
        {"code": "MATER", "values": ["MTOT"]},      # Materialetyper i alt
        {"code": "SAMLING", "values": ["*"]},       # Børne- OG voksensamling
        {"code": "Tid", "values": aar},
    ])
    return pr_indbygger(pr_kommune_aar(rows), 1, 2)


def fetch_library_loans() -> tuple[dict[str, float], float | None]:
    """Udlån pr. indbygger i nyeste år hvor mindst 90 kommuner har tal (så et
    halvfærdigt år ikke vinder), og landstallet."""
    print("Henter biblioteksudlån (BIB3A)...")
    aar, result, national = seneste(
        serie_library_use(seneste_aar_liste("BIB3A", 2, fallback=["2024", "2023"])),
        min_kommuner=90, tabel="BIB3A")
    print(f"  {len(result)} kommuner (år {aar}), landstal: {national} udlån pr. indb.")
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
        {"code": "Tid", "values": [seneste_aar("IDRFAC01", fallback="2024")]},
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
        {"code": "Tid", "values": [seneste_aar("AFSTB4", fallback="2023")]},
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
        {"code": "Tid", "values": [seneste_aar("BIL800", fallback="2024")]},
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
        {"code": "Tid", "values": [seneste_aar("BU43", fallback="2024")]},
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


def serie_neet(aar: list[str]) -> dict[tuple[str, str], float]:
    """
    NEET3: andel af de 16-24-årige der hverken er i beskæftigelse eller
    uddannelse (NEET), i procent. {(kommune_kode, år): pct} inkl. landstallet
    (000, de 98 kommuner samlet). Bruges af både scoren og retningspilen
    (fetch_trend_history.py).

    NEET3 afløser NEET1, som DST satte inaktiv i maj 2025 (sidste år 2023).
    NEET3 dækker 16-29 år med aldersgrupperne som variabel; 16-24 år giver
    præcis NEET1's tal (efterprøvet: alle 3.168 kommune-år 2008-2023 ens).
    """
    rows = api_post("NEET3", [
        {"code": "STATUSNEET", "values": ["00", "10"]},   # alle / ikke-aktive (NEET)
        {"code": "KØN", "values": ["00"]},
        {"code": "BOPOMR", "values": ["*"]},
        {"code": "SOCIO", "values": ["TOT"]},
        {"code": "ALDER", "values": ["1624"]},
        {"code": "Tid", "values": aar},
    ])
    neet = pr_kommune_aar([r for r in rows if r.get("STATUSNEET") == "10"], "BOPOMR")
    alle = pr_kommune_aar([r for r in rows if r.get("STATUSNEET") == "00"], "BOPOMR")
    return andel(neet, alle, 2)


def fetch_neet() -> tuple[dict[str, float], float | None]:
    """NEET-andel af de 16-24-årige i nyeste år med data, og landstallet."""
    print("Henter NEET-unge (NEET3, 16-24 år)...")
    aar, result, national = seneste(serie_neet(
        seneste_aar_liste("NEET3", 2, fallback=["2024", "2023"])), tabel="NEET3")
    print(f"  {len(result)} kommuner ({aar}), landsgennemsnit NEET-andel: {national}%")
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
    # Begge er allerede pr. indbygger med folketallet 1. januar samme år
    # (serie_crime_rate, serie_traffic_accidents).
    crime_per_1k, crime_nat_per_1k = fetch_crime_rate()
    accidents_per_100k, accidents_nat_per_100k = fetch_traffic_accidents()

    faellesskab_rows = []
    for kode in sorted(VALID_CODES, key=int):
        s_val = sports.get(kode)
        s_ratio = ratio_direct(s_val, sports_nat) if s_val is not None and sports_nat else None
        c_val = crime_per_1k.get(kode)
        c_ratio = ratio_inverse(c_val, crime_nat_per_1k) if c_val is not None and crime_nat_per_1k else None
        a_val = accidents_per_100k.get(kode)
        a_ratio = ratio_inverse(a_val, accidents_nat_per_100k) if a_val is not None and accidents_nat_per_100k else None
        faellesskab_rows.append([
            kode,
            s_val if s_val is not None else "",
            s_ratio if s_ratio is not None else "",
            c_val if c_val is not None else "",
            c_ratio if c_ratio is not None else "",
            a_val if a_val is not None else "",
            a_ratio if a_ratio is not None else "",
            _tom(sports_nat), _tom(crime_nat_per_1k), _tom(accidents_nat_per_100k),
        ])

    write_csv("faellesskaber_scores.csv", [
        "kommune_kode",
        "sports_membership_pct", "sports_membership_ratio",
        "crime_per_1k", "crime_ratio",
        "traffic_accidents_per_100k", "traffic_accidents_ratio",
        "sports_membership_ref", "crime_rate_ref", "traffic_accidents_ref",
    ], faellesskab_rows)

    # === LOKALSAMFUND ===
    print("\n--- LOKALSAMFUND ---")

    lib_per_cap, lib_nat_per_cap = fetch_library_loans()   # allerede pr. indb.
    facilities_raw, facilities_nat_total = fetch_sports_facilities()

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
            _tom(lib_nat_per_cap),
        ])

    write_csv("lokalsamfund_scores.csv", [
        "kommune_kode",
        "library_loans_per_cap", "library_ratio",
        "facilities_per_10k", "facilities_ratio",
        "library_use_ref",
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
            _tom(commute_nat),
        ])

    write_csv("mobilitet_scores.csv", [
        "kommune_kode",
        "commute_distance_km", "commute_ratio",
        "car_access_pct", "car_access_ratio",
        "commute_distance_ref",
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
            _tom(vuln_nat), _tom(neet_nat),
        ])

    write_csv("velfaerd_extra_scores.csv", [
        "kommune_kode",
        "vulnerable_children_pct", "vulnerable_children_ratio",
        "neet_pct", "neet_ratio",
        "vulnerable_children_ref", "neet_ref",
    ], velfaerd_rows)

    print("\n" + "=" * 60)
    print("Alle nye sociale indikatorer hentet!")
    print("=" * 60)


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
