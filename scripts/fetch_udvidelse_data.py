#!/usr/bin/env python3
"""
fetch_udvidelse_data.py

Henter 10 nye sociale indikatorer til Danmarks 98 Doughnuts.

UVM (api.uddannelsesstatistik.dk):
  - exam_grade:        Karaktergennemsnit, folkeskolens afgangseksamen (GS/KARA/KARAGNS)
  - high_absence:      Andel elever med >10% fravær (GS/ELEVFRAV/FRAVAAR)
  - low_wellbeing:     Gennemsnitlig trivselsscore (GS/TRIV/TRIVIND)
  - youth_education:   Andel der forventes at få ungdomsuddannelse (GS/PROFMOD/PROFMOD)

DST (api.statbank.dk):
  - poverty_relative:      Andel i relativ fattigdom 60%-grænse (IFOR12P)
  - gender_leadership:     Andel kvinder i lederstillinger (RAS301, SOCIO=15)
  - housing_no_wc:         Andel beboede boliger uden eget toilet (BOL102)
  - housing_no_bath:       Andel beboede boliger uden eget bad (BOL102)
  - child_notifications:   Underretninger om børn pr. 1.000 indb. 0-17 år (UND2)

Output CSV-filer (skrives til data/):
  uvm_scores.csv             - 5 UVM-indikatorer
  lighed_scores.csv          - relativ fattigdom + kønsbalance
  bolig_wc_scores.csv        - toilet + bad
  underretning_scores.csv    - underretninger

Kør:
  cd /sti/til/doughnut
  python3 scripts/fetch_udvidelse_data.py
"""

from __future__ import annotations

import csv
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dst_aar import registrer_aar, seneste_aar_liste  # noqa: E402
from dst import api_post, parse_value, pr_indbygger, pr_kommune_aar, seneste  # noqa: E402  (fælles DST-kald, scripts/dst.py)
from api_noegler import hent_noegle, kraev_noegle, UVM_HJAELP  # noqa: E402
from kommuner import KOMMUNER, KODER as VALID_CODES  # noqa: E402  (de 98 kommuner, data/kommuner.json)

# ─── Konstanter ────────────────────────────────────────────────────────────
UVM_TOKEN = hent_noegle("UVM_API_TOKEN")
UVM_BASE = "https://api.uddannelsesstatistik.dk/Api/v1"
DELAY    = 0.7  # sekunder mellem API-kald

ROOT       = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "data"


# ─── HJÆLPEFUNKTIONER ──────────────────────────────────────────────────────

def load_navn_to_kode() -> dict[str, str]:
    """
    Navn→kode-mapping fra data/kommuner.json.
    Bruges til at oversætte UVM-kommunenavne til DST-koder.
    """
    mapping = {}
    for kode, navn in KOMMUNER.items():
        mapping[navn] = kode
        # Alias: "Aarhus" / "Åarhus" mv.
        mapping[navn.replace("Å", "Aa").replace("å", "aa")] = kode
    return mapping


def _tom(v):
    """Tom celle for manglende værdi (men 0 bevares)."""
    return "" if v is None else v


def parse_float(s: str | None) -> float | None:
    """Parser UVM/DST streng til float - håndterer ',' decimal og '%'-suffix."""
    if s is None:
        return None
    s = str(s).strip().rstrip("%").strip()
    if s in ("", "..", ".", "x", "X", "-", "nan"):
        return None
    try:
        return float(s.replace(".", "").replace(",", "."))
    except ValueError:
        return None


def ratio_direct(val: float, avg: float) -> float | None:
    """Direkte ratio: højere er bedre. val/avg*100."""
    if avg == 0 or val is None:
        return None
    return round((val / avg) * 100, 2)


def ratio_inverse(val: float, avg: float) -> float | None:
    """Inverteret ratio: lavere er bedre. avg/val*100."""
    if val == 0 or val is None:
        return None
    return round((avg / val) * 100, 2)


# ─── UVM API ───────────────────────────────────────────────────────────────

def uvm_post(endpoint: str, body: dict) -> list[dict]:
    """POST til UVM statistik-endpoint med Bearer-token. Returnerer liste af rækker."""
    url = f"{UVM_BASE}/{endpoint}"
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload,
        headers={
            "Authorization": f"Bearer {UVM_TOKEN}",
            "Content-Type": "application/json; charset=utf-8",
        },
    )
    time.sleep(DELAY)
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        data = json.loads(resp.read().decode("utf-8"))
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"  UVM API fejl ({endpoint}): {e}", file=sys.stderr)
        return []


def uvm_get_latest(
    rows: list[dict],
    kommune_key: str,
    year_key: str,
    value_key: str,
    tabel: str | None = None,
) -> dict[str, tuple[str, float]]:
    """
    Finder den seneste årsværdi per kommune.
    Returnerer {kommune_navn: (år, float_value)}.
    Årstal sammenlignes som strenge - virker for "2023/2024" og "2023".
    Med `tabel` (fx "GS/KARA/KARAGNS", registrets table-felt) noteres året i
    data/data_years.json, så sitet viser det år tallet er fra. Skoleår mærkes
    med slutåret ("2024/2025" -> 2025), ligesom i retningspilen.
    """
    best: dict[str, tuple[str, float]] = {}
    for row in rows:
        navn = row.get(kommune_key, "").strip()
        år   = row.get(year_key, "").strip()
        val  = parse_float(row.get(value_key))
        if not navn or not år or val is None:
            continue
        if navn not in best or år > best[navn][0]:
            best[navn] = (år, val)
    if tabel and best:
        registrer_aar(tabel, max(år for år, _ in best.values()))
    return best


# ─── UVM: KARAGNS - Karaktergennemsnit ───────────────────────────────────

def fetch_exam_grade(navn_til_kode: dict[str, str]) -> tuple[dict[str, float], float | None]:
    """
    GS/KARA/KARAGNS: Gennemsnit af obligatoriske prøver (afgangseksamen).
    Returnerer {kommune_kode: gennemsnit}, national_avg.
    Højere er bedre (inverse=False).
    """
    print("Henter karaktergennemsnit (GS/KARA/KARAGNS)...")
    rows = uvm_post("statistik", {
        "område": "GS", "emne": "KARA", "underemne": "KARAGNS",
        "nøgletal": ["Gennemsnit - Obl. prøver"],
        "detaljering": [
            "[Bopælskommune].[Bopælskommune]",
            "[Skoleår].[Skoleår]",
        ],
        "side_størrelse": 3000,
    })

    KOM_KEY  = "[Bopælskommune].[Bopælskommune].[Bopælskommune]"
    ÅR_KEY   = "[Skoleår].[Skoleår].[Skoleår]"
    VAL_KEY  = "Gennemsnit - Obl. prøver"

    latest = uvm_get_latest(rows, KOM_KEY, ÅR_KEY, VAL_KEY, tabel="GS/KARA/KARAGNS")

    result: dict[str, float] = {}
    for navn, (år, val) in latest.items():
        kode = navn_til_kode.get(navn)
        if kode and kode in VALID_CODES:
            result[kode] = val

    nat_avg = None
    if result:
        nat_avg = round(sum(result.values()) / len(result), 4)

    print(f"  {len(result)} kommuner, seneste skoleår varierer, nat.gns.: {nat_avg}")
    return result, nat_avg


# ─── UVM: FRAVAAR - Elevfravær ────────────────────────────────────────────

def fetch_high_absence(navn_til_kode: dict[str, str]) -> tuple[dict[str, float], float | None]:
    """
    GS/ELEVFRAV/FRAVAAR: Andel elever med >10% fravær.
    Returnerer {kommune_kode: pct}, national_avg.
    Lavere er bedre (inverse=True).
    """
    print("Henter elevfravær >10% (GS/ELEVFRAV/FRAVAAR)...")
    rows = uvm_post("statistik", {
        "område": "GS", "emne": "ELEVFRAV", "underemne": "FRAVAAR",
        "nøgletal": ["Over 10 procent"],
        "detaljering": [
            "[Institution].[Beliggenhedskommune]",
            "[Tid].[Skoleår]",
        ],
        "side_størrelse": 3000,
    })

    KOM_KEY = "[Institution].[Beliggenhedskommune].[Beliggenhedskommune]"
    ÅR_KEY  = "[Tid].[Skoleår].[Skoleår]"
    VAL_KEY = "Over 10 procent"

    latest = uvm_get_latest(rows, KOM_KEY, ÅR_KEY, VAL_KEY, tabel="GS/ELEVFRAV/FRAVAAR")

    result: dict[str, float] = {}
    for navn, (år, val) in latest.items():
        kode = navn_til_kode.get(navn)
        if kode and kode in VALID_CODES:
            result[kode] = val

    nat_avg = None
    if result:
        nat_avg = round(sum(result.values()) / len(result), 4)

    print(f"  {len(result)} kommuner, nat.gns.: {nat_avg}%")
    return result, nat_avg


# ─── UVM: TRIVIND - Elevtrivsel ───────────────────────────────────────────

def fetch_wellbeing(navn_til_kode: dict[str, str]) -> tuple[dict[str, float], float | None]:
    """
    GS/TRIV/TRIVIND: Gennemsnitlig trivselsscore per kommune (alle indikatorer).
    Returnerer {kommune_kode: gns_score (1-5)}, national_avg.
    Højere er bedre (inverse=False).
    """
    print("Henter elevtrivsel (GS/TRIV/TRIVIND)...")
    rows = uvm_post("statistik", {
        "område": "GS", "emne": "TRIV", "underemne": "TRIVIND",
        "nøgletal": ["Indikatorsvar - Kommunetal"],
        "detaljering": [
            "[Institution].[Administrerende Kommune]",
            "[Skoleår].[Skoleår]",
            "[Trivselsindikator].[Trivselsindikator]",
        ],
        "side_størrelse": 10000,
    })

    KOM_KEY  = "[Institution].[Administrerende Kommune].[Administrerende Kommune]"
    ÅR_KEY   = "[Skoleår].[Skoleår].[Skoleår]"
    IND_KEY  = "[Trivselsindikator].[Trivselsindikator].[Trivselsindikator]"
    VAL_KEY  = "Indikatorsvar - Kommunetal"

    # Beregn gennemsnit over alle trivselsindikatorer per kommune per år
    # {(navn, år): [scores]}
    scores: dict[tuple[str, str], list[float]] = {}
    for row in rows:
        navn = row.get(KOM_KEY, "").strip()
        år   = row.get(ÅR_KEY, "").strip()
        val  = parse_float(row.get(VAL_KEY))
        if not navn or not år or val is None:
            continue
        key = (navn, år)
        scores.setdefault(key, []).append(val)

    # Seneste år per kommune
    latest_år: dict[str, str] = {}
    for (navn, år) in scores:
        if navn not in latest_år or år > latest_år[navn]:
            latest_år[navn] = år
    if latest_år:
        registrer_aar("GS/TRIV/TRIVIND", max(latest_år.values()))

    result: dict[str, float] = {}
    for navn, år in latest_år.items():
        key = (navn, år)
        vals = scores.get(key, [])
        if not vals:
            continue
        kode = navn_til_kode.get(navn)
        if kode and kode in VALID_CODES:
            result[kode] = round(sum(vals) / len(vals), 4)

    nat_avg = None
    if result:
        nat_avg = round(sum(result.values()) / len(result), 4)

    print(f"  {len(result)} kommuner, nat.gns. trivselsscore: {nat_avg}")
    return result, nat_avg


# ─── UVM: EUD/PRAK/SØG - Læreplads (PENSIONERET aug. 2026) ──────────────
# fetch_apprenticeship() er fjernet. UVM kender ikke længere nøgletallene
# "Lp-søgende med afsluttet grundforløb"/"Lp-søgende i alt" - et opslag
# fejler med 400 "kunne ikke findes", også for enkelte år. Indikatoren var
# desuden konceptuelt tvivlsom (se noten i webapp/lib/shared.ts).
# Skal lærepladser med igen, så brug praktikpladsgraden i stedet.


# ─── UVM: PROFMOD - Ungdomsuddannelse ─────────────────────────────────────

def fetch_youth_education(navn_til_kode: dict[str, str]) -> tuple[dict[str, float], float | None]:
    """
    GS/PROFMOD/PROFMOD: Andel der forventes at opnå ungdomsuddannelseskompetence.
    Returnerer {kommune_kode: pct}, national_avg.
    Højere er bedre (inverse=False).
    """
    print("Henter ungdomsuddannelsesandel (GS/PROFMOD/PROFMOD)...")
    rows = uvm_post("statistik", {
        "område": "GS", "emne": "PROFMOD", "underemne": "PROFMOD",
        "nøgletal": ["Komp: Med mindst en ungdomsuddannelsekompetence"],
        "detaljering": [
            "[Bopælskommune].[Kommune]",
            "[År].[År]",
        ],
        "side_størrelse": 5000,
    })

    KOM_KEY = "[Bopælskommune].[Kommune].[Kommune]"
    ÅR_KEY  = "[År].[År].[År]"
    VAL_KEY = "Komp: Med mindst en ungdomsuddannelsekompetence"

    latest = uvm_get_latest(rows, KOM_KEY, ÅR_KEY, VAL_KEY, tabel="GS/PROFMOD/PROFMOD")

    result: dict[str, float] = {}
    for navn, (år, val) in latest.items():
        kode = navn_til_kode.get(navn)
        if kode and kode in VALID_CODES:
            result[kode] = val

    nat_avg = None
    if result:
        nat_avg = round(sum(result.values()) / len(result), 4)

    print(f"  {len(result)} kommuner, nat.gns.: {nat_avg}%")
    return result, nat_avg


# ─── DST API ───────────────────────────────────────────────────────────────

# ─── DST: IFOR12P - Relativ fattigdom ─────────────────────────────────────

def fetch_relative_poverty() -> tuple[dict[str, float], float | None]:
    """
    IFOR12P: Andel i relativ fattigdom (indkomst <60% af median).
    Returnerer {kommune_kode: pct}, national_avg.
    Lavere er bedre (inverse=True).
    """
    print("Henter relativ fattigdom (IFOR12P)...")
    rows = api_post("IFOR12P", [
        {"code": "KOMMUNEDK", "values": ["*"]},
        {"code": "INDKN", "values": ["60"]},
        {"code": "Tid", "values": seneste_aar_liste("IFOR12P", 3, ["2024", "2023", "2022"])},
    ])

    # Brug seneste år per kommune
    latest: dict[str, tuple[str, float]] = {}
    for row in rows:
        kode = row.get("KOMMUNEDK", "").strip()
        år   = row.get("TID", "").strip()
        val  = parse_value(row.get("INDHOLD", ""))
        if not kode or val is None:
            continue
        if kode not in latest or år > latest[kode][0]:
            latest[kode] = (år, val)

    result = {}
    nat_val = None
    for kode, (_, val) in latest.items():
        if kode == "000":
            nat_val = val
        elif kode in VALID_CODES:
            result[kode] = val

    nat_avg = nat_val or (round(sum(result.values()) / len(result), 4) if result else None)
    print(f"  {len(result)} kommuner, nat.gns.: {nat_avg}%")
    return result, nat_avg


# ─── DST: RAS301 - Kønsbalance ledere ─────────────────────────────────────

def fetch_gender_leadership() -> tuple[dict[str, float], float | None]:
    """
    RAS301: Andel kvinder i lønmodtager-lederstillinger (SOCIO=15).
    Returnerer {kommune_kode: pct_kvinder}, national_pct.
    Højere er bedre - tættere på 50% = bedre ligestilling (inverse=False).
    NB: Baseline er national andel, ikke 50%.
    """
    print("Henter kønsbalance ledere (RAS301)...")

    # Hent mænd og kvinder separat, summer alle brancher og aldre
    gennemlopte_år = seneste_aar_liste("RAS301", 3, ["2024", "2023", "2022"])
    for år in gennemlopte_år:
        rows = api_post("RAS301", [
            {"code": "OMRÅDE", "values": ["*"]},
            {"code": "SOCIO", "values": ["15"]},          # Lønmodtager med ledelsesarbejde
            {"code": "BRANCHE07", "values": ["*"]},        # Alle brancher
            {"code": "ALDER", "values": ["*"]},            # Alle aldre
            {"code": "KOEN", "values": ["M", "K"]},
            {"code": "Tid", "values": [år]},
        ])
        if rows and not (len(rows) == 1 and "error" in str(rows[0]).lower()):
            print(f"  Bruger år {år}")
            break
        print(f"  Ingen data for {år}, prøver forrige år...")
        rows = []

    # Summer per (OMRÅDE, KOEN)
    sums: dict[tuple[str, str], float] = {}
    for row in rows:
        omr  = row.get("OMRÅDE", "").strip()
        koen = row.get("KOEN", "").strip()
        val  = parse_value(row.get("INDHOLD", ""))
        if val is None:
            continue
        if omr in VALID_CODES or omr == "000":
            key = (omr, koen)
            sums[key] = sums.get(key, 0) + val

    result: dict[str, float] = {}
    for kode in VALID_CODES:
        k = sums.get((kode, "K"), 0)
        m = sums.get((kode, "M"), 0)
        total = k + m
        if total > 0:
            result[kode] = round((k / total) * 100, 2)

    # National
    nat_k = sums.get(("000", "K"), 0)
    nat_m = sums.get(("000", "M"), 0)
    nat_total = nat_k + nat_m
    nat_avg = round((nat_k / nat_total) * 100, 2) if nat_total > 0 else None

    print(f"  {len(result)} kommuner, nat. andel kvinder i ledelse: {nat_avg}%")
    return result, nat_avg


# ─── DST: BOL102 - Boliger uden WC og bad ─────────────────────────────────

def fetch_housing_facilities() -> tuple[
    dict[str, float], float | None,
    dict[str, float], float | None,
]:
    """
    BOL102: Andel beboede boliger uden eget toilet + uden eget bad.
    Toilet-koder: 1000616=WC udenfor boligen, 1000617=Andet/intet toilet
    Bad-kode: 1000621=Ikke bad eller adgang til bad
    Returnerer: (no_wc_dict, no_wc_nat, no_bath_dict, no_bath_nat).
    Lavere er bedre (inverse=True).
    """
    print("Henter boligforhold (BOL102)...")
    aar_bol102 = seneste_aar_liste("BOL102", 2, ["2024", "2023"])

    # Hent alle toilet- og bad-koder + totalen for beboede boliger
    rows = api_post("BOL102", [
        {"code": "AMT", "values": ["*"]},
        {"code": "BEBO", "values": ["1000"]},          # Beboede boliger
        {"code": "TOILET", "values": ["1000616", "1000617", "1000618"]},
        {"code": "Tid", "values": aar_bol102},
    ])

    # Sum per (kode, toilet_type, år)
    toilet_sums: dict[tuple[str, str, str], float] = {}
    for row in rows:
        kode   = row.get("AMT", "").strip()
        toilet = row.get("TOILET", "").strip()
        år     = row.get("TID", "").strip()
        val    = parse_value(row.get("INDHOLD", ""))
        if val is None:
            continue
        if kode in VALID_CODES or kode == "000":
            key = (kode, toilet, år)
            toilet_sums[key] = toilet_sums.get(key, 0) + val

    # Brug seneste år per kommune
    def latest_yr(kode, typer):
        for år in aar_bol102:
            vals = [toilet_sums.get((kode, t, år), 0) for t in typer]
            if any(v > 0 for v in vals):
                return år
        return None

    no_wc: dict[str, float] = {}
    for kode in VALID_CODES:
        yr = latest_yr(kode, ["1000616", "1000617", "1000618"])
        if not yr:
            continue
        total = sum(toilet_sums.get((kode, t, yr), 0) for t in ["1000616", "1000617", "1000618"])
        bad   = sum(toilet_sums.get((kode, t, yr), 0) for t in ["1000616", "1000617"])
        if total > 0:
            no_wc[kode] = round((bad / total) * 100, 4)

    # National
    nat_yr = next((a for a in aar_bol102
                   if any(("000", t, a) in toilet_sums
                          for t in ["1000616", "1000617", "1000618"])), aar_bol102[-1])
    nat_total = sum(toilet_sums.get(("000", t, nat_yr), 0) for t in ["1000616","1000617","1000618"])
    nat_bad   = sum(toilet_sums.get(("000", t, nat_yr), 0) for t in ["1000616","1000617"])
    nat_no_wc = round((nat_bad / nat_total) * 100, 4) if nat_total > 0 else None

    # Bad - separat kald
    rows_bad = api_post("BOL102", [
        {"code": "AMT", "values": ["*"]},
        {"code": "BEBO", "values": ["1000"]},
        {"code": "BAD", "values": ["1000620", "1000621", "1000622"]},
        {"code": "Tid", "values": aar_bol102},
    ])

    bad_sums: dict[tuple[str, str, str], float] = {}
    for row in rows_bad:
        kode = row.get("AMT", "").strip()
        bad  = row.get("BAD", "").strip()
        år   = row.get("TID", "").strip()
        val  = parse_value(row.get("INDHOLD", ""))
        if val is None:
            continue
        if kode in VALID_CODES or kode == "000":
            bad_sums[(kode, bad, år)] = bad_sums.get((kode, bad, år), 0) + val

    no_bath: dict[str, float] = {}
    for kode in VALID_CODES:
        for yr in aar_bol102:
            total = sum(bad_sums.get((kode, b, yr), 0) for b in ["1000620","1000621","1000622"])
            if total > 0:
                no_b = bad_sums.get((kode, "1000621", yr), 0)
                no_bath[kode] = round((no_b / total) * 100, 4)
                break

    nat_total_b = sum(bad_sums.get(("000", b, nat_yr), 0) for b in ["1000620","1000621","1000622"])
    nat_no_b    = bad_sums.get(("000", "1000621", nat_yr), 0)
    nat_no_bath = round((nat_no_b / nat_total_b) * 100, 4) if nat_total_b > 0 else None

    print(f"  {len(no_wc)} kommuner uden-WC, nat.: {nat_no_wc}%")
    print(f"  {len(no_bath)} kommuner uden-bad, nat.: {nat_no_bath}%")
    return no_wc, nat_no_wc, no_bath, nat_no_bath


# ─── DST: UND2 - Underretninger om børn ───────────────────────────────────

def serie_child_notifications(aar: list[str]) -> dict[tuple[str, str], float]:
    """
    UND2: underretninger om børn og unge (i alt, alle aldre, begge køn) pr.
    1.000 indb. 0-17 år, med børnetallet 1. januar samme år (FOLK1A).
    {(kommune_kode, år): værdi} inkl. hele landet (000). Lavere er bedre.
    Bruges af både scoren og retningspilen (fetch_trend_history.py).

    Indtil sep. 2026 tog scoren det nyeste år pr. kommune for sig (så år
    kunne blandes) og delte med børnetallet i FOLK1A's allernyeste kvartal.
    """
    rows = api_post("UND2", [
        {"code": "ADMKOM", "values": ["*"]},
        {"code": "UNDERRET", "values": ["00"]},
        {"code": "ALDER1", "values": ["00"]},
        {"code": "KON", "values": ["0"]},
        {"code": "Tid", "values": aar},
    ])
    return pr_indbygger(pr_kommune_aar(rows, "ADMKOM"), 1000, 2,
                        alder=[str(a) for a in range(18)])


def fetch_child_notifications() -> tuple[dict[str, float], float | None]:
    """Underretninger pr. 1.000 børn i nyeste år med data, og landstallet."""
    print("Henter underretninger om børn (UND2)...")
    aar, result, nat_rate = seneste(serie_child_notifications(
        seneste_aar_liste("UND2", 2, ["2024", "2023"])), tabel="UND2")
    print(f"  {len(result)} kommuner ({aar}), nat. rate: {nat_rate} pr. 1.000")
    return result, nat_rate


# ─── CSV-output ────────────────────────────────────────────────────────────

def write_csv(filename: str, headers: list[str], rows: list[list]) -> None:
    filepath = OUTPUT_DIR / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
    print(f"  Gemt: {filepath} ({len(rows)} rækker)")


# ─── MAIN ──────────────────────────────────────────────────────────────────

def main():
    kraev_noegle("UVM_API_TOKEN", UVM_TOKEN, UVM_HJAELP)

    print("=" * 65)
    print("Henter nye sociale indikatorer - UVM + DST")
    print("=" * 65)

    # Navn→kode mapping til UVM-data
    print("\nLoader kommune-navne-mapping fra doughnut_scores.csv...")
    navn_til_kode = load_navn_to_kode()
    print(f"  {len(navn_til_kode)} navne indlæst")

    # ── UVM ──────────────────────────────────────────────────────
    print("\n--- UVM: Uddannelsesstatistik ---")

    exam, exam_nat         = fetch_exam_grade(navn_til_kode)
    absence, absence_nat   = fetch_high_absence(navn_til_kode)
    wellbeing, wb_nat      = fetch_wellbeing(navn_til_kode)
    youth_edu, ye_nat      = fetch_youth_education(navn_til_kode)

    uvm_rows = []
    for kode in sorted(VALID_CODES, key=int):
        eg  = exam.get(kode)
        ab  = absence.get(kode)
        wb  = wellbeing.get(kode)
        ye  = youth_edu.get(kode)

        eg_ratio  = ratio_direct(eg, exam_nat)     if eg  is not None and exam_nat   else None
        ab_ratio  = ratio_inverse(ab, absence_nat) if ab  is not None and absence_nat else None
        wb_ratio  = ratio_direct(wb, wb_nat)       if wb  is not None and wb_nat      else None
        ye_ratio  = ratio_direct(ye, ye_nat)       if ye  is not None and ye_nat      else None

        uvm_rows.append([
            kode,
            eg  if eg  is not None else "", eg_ratio  if eg_ratio  is not None else "",
            ab  if ab  is not None else "", ab_ratio  if ab_ratio  is not None else "",
            wb  if wb  is not None else "", wb_ratio  if wb_ratio  is not None else "",
            ye  if ye  is not None else "", ye_ratio  if ye_ratio  is not None else "",
        ])

    write_csv("uvm_scores.csv", [
        "kommune_kode",
        "exam_grade_avg", "exam_grade_ratio",
        "high_absence_pct", "high_absence_ratio",
        "wellbeing_score", "wellbeing_ratio",
        "youth_education_pct", "youth_education_ratio",
    ], uvm_rows)

    # ── DST ──────────────────────────────────────────────────────
    print("\n--- DST: Danmarks Statistik ---")

    poverty, pov_nat             = fetch_relative_poverty()
    gender_lead, gl_nat          = fetch_gender_leadership()
    no_wc, wc_nat, no_bath, bath_nat = fetch_housing_facilities()
    notifications, notif_nat     = fetch_child_notifications()

    # lighed_scores.csv
    lighed_rows = []
    for kode in sorted(VALID_CODES, key=int):
        pov  = poverty.get(kode)
        gl   = gender_lead.get(kode)
        pov_r = ratio_inverse(pov, pov_nat) if pov  is not None and pov_nat  else None
        gl_r  = ratio_direct(gl, gl_nat)   if gl   is not None and gl_nat   else None
        lighed_rows.append([
            kode,
            pov  if pov  is not None else "", pov_r  if pov_r  is not None else "",
            gl   if gl   is not None else "", gl_r   if gl_r   is not None else "",
            _tom(pov_nat), _tom(gl_nat),
        ])

    write_csv("lighed_scores.csv", [
        "kommune_kode",
        "poverty_relative_pct", "poverty_relative_ratio",
        "gender_leadership_pct", "gender_leadership_ratio",
        "poverty_relative_ref", "gender_leadership_ref",
    ], lighed_rows)

    # bolig_wc_scores.csv
    bolig_rows = []
    for kode in sorted(VALID_CODES, key=int):
        wc   = no_wc.get(kode)
        bath = no_bath.get(kode)
        wc_r   = ratio_inverse(wc, wc_nat)     if wc   is not None and wc_nat   else None
        bath_r = ratio_inverse(bath, bath_nat)  if bath is not None and bath_nat else None
        bolig_rows.append([
            kode,
            wc   if wc   is not None else "", wc_r   if wc_r   is not None else "",
            bath if bath is not None else "", bath_r if bath_r is not None else "",
            _tom(wc_nat), _tom(bath_nat),
        ])

    write_csv("bolig_wc_scores.csv", [
        "kommune_kode",
        "housing_no_wc_pct", "housing_no_wc_ratio",
        "housing_no_bath_pct", "housing_no_bath_ratio",
        "housing_no_wc_ref", "housing_no_bath_ref",
    ], bolig_rows)

    # underretning_scores.csv
    underretning_rows = []
    for kode in sorted(VALID_CODES, key=int):
        notif   = notifications.get(kode)
        notif_r = ratio_inverse(notif, notif_nat) if notif is not None and notif_nat else None
        underretning_rows.append([
            kode,
            notif  if notif  is not None else "",
            notif_r if notif_r is not None else "",
            _tom(notif_nat),
        ])

    write_csv("underretning_scores.csv", [
        "kommune_kode",
        "child_notifications_per_1k", "child_notifications_ratio",
        "child_notifications_ref",
    ], underretning_rows)

    print("\n" + "=" * 65)
    print("Alle nye indikatorer hentet!")
    print("=" * 65)


if __name__ == "__main__":
    main()

    # ── AUTO-REBUILD af master_indicators.csv ──────────────────────
    try:
        import sys as _sys
        from pathlib import Path as _Path
        _sys.path.insert(0, str(_Path(__file__).resolve().parent))
        from build_master_csv import auto_build_master
        auto_build_master()
    except Exception as _e:
        print(f"\n⚠ Kunne ikke auto-rebuild master-CSV: {_e}")
        print("  Rådata er gemt. Kør manuelt: python3 scripts/build_master_csv.py")
