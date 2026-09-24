#!/usr/bin/env python3
"""
fetch_offentlig_transport.py

Andel af befolkningen med god adgang til offentlig transport PR. KOMMUNE,
genskabt ud fra åbne data med DST's egen metode (FN's verdensmål 11.2.1).

HVORFOR: DST udgiver indikatoren (LABY49) kun for de fem kommunegrupper.
Platformens public_transport stempler derfor gruppetallet på alle kommuner i
gruppen: fem forskellige værdier fordelt på 98 kommuner. I kommunegruppe-
baselinen, som er standardvisningen, er hver kommune dermed lig med sit eget
gruppegennemsnit, og alle 98 får præcis 100. Indikatoren bærer ingen
information i den visning.

STATUS: IKKE koblet på master-pipelinen. Scriptet skriver
data/offentlig_transport_scores.csv, men registret (data/indikatorer.json)
peger stadig på LABY49, og scriptet kalder bevidst ikke auto_build_master().
Se docs/offentlig-transport-genskabt.md for validering og plan.

DST'S METODE (Boks 1 i DST's analyse "Har adgang til offentlig transport
betydning for om man har bil?", og verdensmålssiden for 11.2.1):
  - Alle bopælsadresser.
  - 500 m til fods ad vejnettet (GeoDanmark).
  - Afgange i timen på en typisk hverdag kl. 6-20 fra faste stoppesteder.
    Flextrafik, telebusser og vinkestrækninger tæller ikke.
  - Højt/meget højt: mindst 10 afgange i timen. Middel: 4-9. Lavt: under 4.
    Intet: intet stoppested inden for 500 m.
  Platformen bruger "højt + meget højt" som indikator.

GENSKABELSEN (valideret mod LABY49, se docs):
  - Afgange: Rejseplanens GTFS på én typisk hverdag (tirsdag-torsdag med et
    normalt antal ture, så ferieuger falder fra). Rutetype 715 (behovsstyret
    bus) udelades. Ingen afgang tælles fra endestationen eller fra stop med
    pickup_type=1.
  - Frekvensen for en adresse er SUMMEN af afgange i timen fra alle
    stoppesteder inden for rækkevidden. En tur tæller ved hvert stop den kører
    forbi. Det er den regel der reproducerer DST's tal. "Bedste stoppested" og
    "unikke ture" rammer begge systematisk for lavt, se docs.
  - Afstand: 340 m i fugleflugt som stedfortræder for 500 m ad vejnettet.
    Kalibreret alene på andelen UDEN stoppested ("Intet"), hvor frekvensreglen
    ikke spiller ind. 320-360 m giver samme rangorden (rangkorrelation 0,999).
  - Befolkning: DAR-adresser vægtet med Eurostats folketælling 2021 på
    1 km-grid (registerbaseret). Hver celles befolkning fordeles ligeligt på
    cellens adresser. Sommerhus- og erhvervsområder har få registrerede beboere
    og får derfor lav vægt. Uden vægtningen ville adresser i sommerhusområder
    tælle som beboere.

VALIDERING: scriptet summerer kommunetallene op på de fem kommunegrupper og
sammenligner med nyeste LABY49 ved hver kørsel. Afviger det i gennemsnit mere
end 3 procentpoint, så er noget ændret hos en af kilderne - se efter før tallene
bruges.

KILDER OG KREDITERING:
  - Rejseplanen GTFS, CC BY 4.0. "Indeholder kollektivtrafikdata fra Rejseplanen."
  - DAR-adresser fra Dataforsyningen (DAWA), frie data.
  - Eurostat, Census 2021 population grid (1 km), (c) European Union.
    Afledt fil: data/befolkning_1km_2021_dk.csv (kun danske celler).
  - DST LABY49, kun til validering.

Kører med standardbiblioteket alene (Python 3.9+). Første kørsel henter ca.
60 MB køreplaner og 4 mio. adresser (4-5 minutter). Det cachen genbruges.

Kør fra projektets rodmappe:
  python3 scripts/fetch_offentlig_transport.py
  python3 scripts/fetch_offentlig_transport.py --genhent        # hent alt forfra
  python3 scripts/fetch_offentlig_transport.py --dato 20260929  # bestemt hverdag
"""

from __future__ import annotations

import argparse
import csv
import io
import math
import re
import statistics
import sys
import tempfile
import time
import urllib.request
import zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dst import api_post  # noqa: E402
from kommuner import GRUPPE, KOMMUNER  # noqa: E402

GTFS_URL = "https://www.rejseplanen.info/labs/GTFS.zip"
DAWA_URL = "https://api.dataforsyningen.dk/adresser?kommunekode={:04d}&struktur=mini&format=csv"
GRID_URL = "https://gisco-services.ec.europa.eu/census/2021/Eurostat_Census-GRID_2021_V3.zip"
GRID_CSV_I_ZIP = "Eurostat_Census-GRID_2021_V3/ESTAT_Census_2021_V3.csv"

GRID_FIL = DATA_DIR / "befolkning_1km_2021_dk.csv"
UD_FIL = DATA_DIR / "offentlig_transport_scores.csv"
STANDARD_CACHE = Path(tempfile.gettempdir()) / "doughnut_offentlig_transport"

RADIUS_M = 340.0          # fugleflugt; svarer til DST's 500 m ad vejnettet (se docstring)
FRA_SEK, TIL_SEK = 6 * 3600, 20 * 3600
TIMER = 14
HOEJ, MIDDEL = 10.0, 4.0  # afgange i timen
BEHOVSSTYRET = {"715"}    # GTFS-rutetype "Demand and Response Bus Service" (flextrafik, telebus)
MAKS_AFVIGELSE = 3.0      # procentpoint, gennemsnit mod LABY49 før scriptet advarer

UGEDAGE = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
USER_AGENT = "doughnut-dk/1.0 (+https://github.com/augustseptimius-beep/doughnut)"


# ─── Projektion ────────────────────────────────────────────────────────
# ETRS89-LAEA (EPSG:3035), samme system som Eurostats grid. Formlerne er
# EPSG's ellipsoidiske udgave (Guidance Note 7-2). Afstande i Danmark er
# korrekte på ca. 0,1 %, hvilket er under en halv meter på 340 m.
_A = 6378137.0
_F = 1 / 298.257222101
_E2 = _F * (2 - _F)
_E = math.sqrt(_E2)


def _q(sin_phi: float) -> float:
    return (1 - _E2) * (sin_phi / (1 - _E2 * sin_phi * sin_phi)
                        - (1 / (2 * _E)) * math.log((1 - _E * sin_phi) / (1 + _E * sin_phi)))


_PHI0, _LAM0 = math.radians(52.0), math.radians(10.0)
_QP = _q(1.0)
_BETA0 = math.asin(_q(math.sin(_PHI0)) / _QP)
_RQ = _A * math.sqrt(_QP / 2)
_D = _A * (math.cos(_PHI0) / math.sqrt(1 - _E2 * math.sin(_PHI0) ** 2)) / (_RQ * math.cos(_BETA0))
_SB0, _CB0 = math.sin(_BETA0), math.cos(_BETA0)


def laea(lon: float, lat: float) -> tuple[float, float]:
    """Længde/bredde (WGS84/ETRS89) til LAEA-meter (øst, nord)."""
    beta = math.asin(_q(math.sin(math.radians(lat))) / _QP)
    dl = math.radians(lon) - _LAM0
    sb, cb, cdl = math.sin(beta), math.cos(beta), math.cos(dl)
    b = _RQ * math.sqrt(2 / (1 + _SB0 * sb + _CB0 * cb * cdl))
    return 4321000 + b * _D * cb * math.sin(dl), 3210000 + (b / _D) * (_CB0 * sb - _SB0 * cb * cdl)


# ─── Hentning ──────────────────────────────────────────────────────────
def aabn(url: str, timeout: int = 300):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": USER_AGENT}),
                                  timeout=timeout)


def hent_fil(url: str, mål: Path, genhent: bool) -> Path:
    if mål.exists() and mål.stat().st_size > 0 and not genhent:
        return mål
    mål.parent.mkdir(parents=True, exist_ok=True)
    tmp = mål.with_suffix(mål.suffix + ".tmp")
    for forsoeg in range(1, 5):
        try:
            print(f"  Henter {url}")
            with aabn(url, timeout=900) as r, open(tmp, "wb") as fh:
                while True:
                    blok = r.read(1 << 20)
                    if not blok:
                        break
                    fh.write(blok)
            tmp.replace(mål)
            return mål
        except Exception as e:  # noqa: BLE001 - genforsøg ved alle netværksfejl
            print(f"    forsøg {forsoeg}/4 fejlede: {e}")
            time.sleep(3 * forsoeg)
    raise RuntimeError(f"Kunne ikke hente {url}")


# ─── Køreplaner (GTFS) ─────────────────────────────────────────────────
def gtfs_tabel(zf: zipfile.ZipFile, navn: str):
    return csv.DictReader(io.TextIOWrapper(zf.open(navn), encoding="utf-8-sig"))


def tidssek(t: str) -> int | None:
    """'HH:MM:SS' til sekunder. GTFS tillader timer over 24."""
    dele = t.split(":")
    if len(dele) != 3 or not dele[0]:
        return None
    return int(dele[0]) * 3600 + int(dele[1]) * 60 + int(dele[2])


def aktive_services(kalender: list[dict], undtagelser: dict[str, list[tuple[str, str]]],
                    d: date) -> set[str]:
    ds, dag = d.strftime("%Y%m%d"), UGEDAGE[d.weekday()]
    aktive = {r["service_id"] for r in kalender
              if r["start_date"] <= ds <= r["end_date"] and r[dag] == "1"}
    for sid, typ in undtagelser.get(ds, []):
        if typ == "1":
            aktive.add(sid)
        elif typ == "2":
            aktive.discard(sid)
    return aktive


def vaelg_dato(zf: zipfile.ZipFile, fast: str | None) -> tuple[date, set[str], dict[str, str]]:
    """
    En typisk hverdag: den tirsdag, onsdag eller torsdag i feedens første otte
    uger hvis antal ture ligger tættest på medianen. Ferieuger har færre ture og
    falder dermed fra af sig selv.

    Returnerer datoen, de aktive ture og trip_id -> rutetype.
    """
    kalender = list(gtfs_tabel(zf, "calendar.txt"))
    undtagelser: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for r in gtfs_tabel(zf, "calendar_dates.txt"):
        undtagelser[r["date"]].append((r["service_id"], r["exception_type"]))
    rutetype = {r["route_id"]: r["route_type"] for r in gtfs_tabel(zf, "routes.txt")}
    ture_pr_service: dict[str, list[str]] = defaultdict(list)
    tur_type: dict[str, str] = {}
    for r in gtfs_tabel(zf, "trips.txt"):
        rt = rutetype.get(r["route_id"], "")
        if rt in BEHOVSSTYRET:
            continue
        ture_pr_service[r["service_id"]].append(r["trip_id"])
        tur_type[r["trip_id"]] = rt

    def antal(d: date) -> int:
        return sum(len(ture_pr_service.get(s, ())) for s in aktive_services(kalender, undtagelser, d))

    if fast:
        valgt = date(int(fast[:4]), int(fast[4:6]), int(fast[6:8]))
    else:
        start = min(date(int(r["start_date"][:4]), int(r["start_date"][4:6]), int(r["start_date"][6:]))
                    for r in kalender)
        kandidater = [start + timedelta(days=i) for i in range(1, 57)
                      if (start + timedelta(days=i)).weekday() in (1, 2, 3)]
        tal = {d: antal(d) for d in kandidater}
        median = statistics.median(tal.values())
        valgt = min(kandidater, key=lambda d: (abs(tal[d] - median), d))
        print(f"  Hverdage i feedens første 8 uger: median {median:.0f} ture, "
              f"spænd {min(tal.values())}-{max(tal.values())}")
    if (valgt.month, valgt.day) >= (6, 25) and (valgt.month, valgt.day) <= (8, 15):
        print("  ADVARSEL: datoen ligger i sommerkøreplanen. Resultatet bliver for lavt.")
        print("  Kør igen efter skolestart, eller vælg en dato med --dato.")
    aktive = aktive_services(kalender, undtagelser, valgt)
    ture = {t for s in aktive for t in ture_pr_service.get(s, ())}
    return valgt, ture, tur_type


def afgange_pr_stop(zf: zipfile.ZipFile, ture: set[str]) -> dict[str, int]:
    """Antal afgange kl. 6-20 pr. stop_id, uden endestationer og uden pickup_type=1."""
    pr_tur: dict[str, list[tuple[int, str, str, int | None]]] = defaultdict(list)
    for r in gtfs_tabel(zf, "stop_times.txt"):
        tid = r["trip_id"]
        if tid in ture:
            pr_tur[tid].append((int(r["stop_sequence"]), r["stop_id"], r.get("pickup_type", ""),
                                tidssek(r["departure_time"])))
    afgange: dict[str, int] = defaultdict(int)
    uden_tid = 0
    for stop in pr_tur.values():
        sidste = max(s[0] for s in stop)
        for seq, stop_id, pickup, sek in stop:
            if seq == sidste or pickup == "1":
                continue
            if sek is None:
                uden_tid += 1
                continue
            if FRA_SEK <= sek < TIL_SEK:
                afgange[stop_id] += 1
    if uden_tid:
        print(f"  ADVARSEL: {uden_tid} stop-tider uden afgangstid er sprunget over.")
    return afgange


def stoppesteder(zf: zipfile.ZipFile, afgange: dict[str, int]) -> list[tuple[float, float, float]]:
    ud = []
    for r in gtfs_tabel(zf, "stops.txt"):
        n = afgange.get(r["stop_id"])
        if n:
            x, y = laea(float(r["stop_lon"]), float(r["stop_lat"]))
            ud.append((x, y, n / TIMER))
    return ud


# ─── Adresser (DAR via DAWA) ───────────────────────────────────────────
def hent_kommune_adresser(kode: str, mappe: Path, genhent: bool) -> Path:
    """Gældende adresser for én kommune, samlet pr. adgangspunkt (x, y, antal enheder)."""
    ud = mappe / f"{int(kode):04d}.csv"
    if ud.exists() and ud.stat().st_size > 0 and not genhent:
        return ud
    sidste_fejl: Exception | None = None
    for forsoeg in range(1, 6):
        try:
            punkter: dict[str, list] = {}
            with aabn(DAWA_URL.format(int(kode))) as r:
                for a in csv.DictReader(io.TextIOWrapper(r, encoding="utf-8-sig")):
                    if a["status"] != "1":      # 1 = gældende, 3 = foreløbig (ikke bygget)
                        continue
                    p = punkter.get(a["adgangsadresseid"])
                    if p is None:
                        punkter[a["adgangsadresseid"]] = [a["x"], a["y"], 1]
                    else:
                        p[2] += 1
            tmp = ud.with_suffix(".tmp")
            with open(tmp, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(["x", "y", "enheder"])
                w.writerows(punkter.values())
            tmp.replace(ud)
            return ud
        except Exception as e:  # noqa: BLE001
            sidste_fejl = e
            time.sleep(3 * forsoeg)
    raise RuntimeError(f"Kunne ikke hente adresser for kommune {kode}: {sidste_fejl}")


def adresser(cache: Path, genhent: bool):
    mappe = cache / "adresser"
    mappe.mkdir(parents=True, exist_ok=True)
    koder = sorted(KOMMUNER, key=int)
    t0 = time.time()
    with ThreadPoolExecutor(4) as ex:
        filer = list(ex.map(lambda k: hent_kommune_adresser(k, mappe, genhent), koder))
    xs: list[float] = []
    ys: list[float] = []
    enheder: list[int] = []
    kommune: list[int] = []
    for i, fil in enumerate(filer):
        with open(fil, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                x, y = laea(float(r["x"]), float(r["y"]))
                xs.append(x)
                ys.append(y)
                enheder.append(int(r["enheder"]))
                kommune.append(i)
    med_adresser = set(kommune)
    tomme = [KOMMUNER[k] for i, k in enumerate(koder) if i not in med_adresser]
    if tomme:
        raise RuntimeError(f"Ingen adresser for: {', '.join(tomme)}")
    print(f"  {len(xs):,} adgangspunkter, {sum(enheder):,} adresser ({time.time() - t0:.0f}s)")
    return koder, xs, ys, enheder, kommune


# ─── Befolkning (Eurostat Census 2021, 1 km) ───────────────────────────
def byg_befolkningsgrid(cache: Path, genhent: bool) -> None:
    """Uddrager de danske celler fra Eurostats grid (566 MB) til en lille fil i data/."""
    zipsti = hent_fil(GRID_URL, cache / "Eurostat_Census-GRID_2021_V3.zip", genhent)
    raekker = []
    with zipfile.ZipFile(zipsti) as zf:
        laeser = csv.DictReader(io.TextIOWrapper(zf.open(GRID_CSV_I_ZIP), encoding="utf-8-sig"))
        for r in laeser:
            if "DK" not in (r.get("CNTR_ID") or ""):
                continue
            m = re.match(r"CRS3035RES1000mN(\d+)E(\d+)$", r["GRD_ID"])
            t = int(r["T"])
            if m and t > 0:   # -8888/-9999 = fortroligt/mangler; forekommer ikke for DK
                raekker.append((int(m.group(1)) // 1000, int(m.group(2)) // 1000, t))
    raekker.sort()
    with open(GRID_FIL, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["n_km", "e_km", "befolkning"])
        w.writerows(raekker)
    print(f"  Skrev {GRID_FIL.relative_to(ROOT)}: {len(raekker):,} celler, "
          f"{sum(r[2] for r in raekker):,} personer")


def befolkningsgrid() -> dict[tuple[int, int], int]:
    with open(GRID_FIL, encoding="utf-8") as fh:
        return {(int(r["n_km"]), int(r["e_km"])): int(r["befolkning"]) for r in csv.DictReader(fh)}


def vaegte(xs: list[float], ys: list[float], enheder: list[int],
           grid: dict[tuple[int, int], int]) -> list[float]:
    """Hver 1 km-celles befolkning fordelt ligeligt på cellens adresser."""
    celle = [(int(y // 1000), int(x // 1000)) for x, y in zip(xs, ys)]
    enh_pr_celle: dict[tuple[int, int], int] = defaultdict(int)
    for c, n in zip(celle, enheder):
        enh_pr_celle[c] += n
    w = [n * grid.get(c, 0) / enh_pr_celle[c] for c, n in zip(celle, enheder)]
    tabt = sum(t for c, t in grid.items() if c not in enh_pr_celle)
    print(f"  Befolkning fordelt på adresser: {sum(w):,.0f}. "
          f"I celler uden adresser: {tabt:,} ({100 * tabt / sum(grid.values()):.2f}%)")
    return w


# ─── Serviceniveau ─────────────────────────────────────────────────────
def frekvens(xs: list[float], ys: list[float], stop: list[tuple[float, float, float]],
             radius: float) -> list[float]:
    """Sum af afgange i timen fra alle stoppesteder inden for radius, pr. adgangspunkt."""
    spand: dict[tuple[int, int], tuple[list[int], list[float], list[float]]] = {}
    for i, (x, y) in enumerate(zip(xs, ys)):
        k = (int(x // radius), int(y // radius))
        s = spand.get(k)
        if s is None:
            s = spand[k] = ([], [], [])
        s[0].append(i)
        s[1].append(x)
        s[2].append(y)
    f = [0.0] * len(xs)
    r2 = radius * radius
    for sx, sy, afg in stop:
        ki, kj = int(sx // radius), int(sy // radius)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                s = spand.get((ki + di, kj + dj))
                if s is None:
                    continue
                for i, x, y in zip(*s):
                    dx, dy = x - sx, y - sy
                    if dx * dx + dy * dy <= r2:
                        f[i] += afg
    return f


def niveau(f: float) -> int:
    """0 = intet, 1 = lavt, 2 = middel, 3 = højt eller meget højt."""
    if f <= 0:
        return 0
    if f < MIDDEL:
        return 1
    if f < HOEJ:
        return 2
    return 3


# ─── Validering mod DST ────────────────────────────────────────────────
DST_NIVEAU = {"1345": 3, "1350": 3, "1355": 2, "1360": 1, "1365": 0}
NIVEAUNAVN = ["Intet", "Lavt", "Middel", "Højt+"]


def valider(grupper: dict[int, list[float]]) -> None:
    try:
        rows = api_post("LABY49", [
            {"code": "KOMGRP", "values": ["*"]},
            {"code": "SDGSERVICE", "values": ["*"]},
            {"code": "Tid", "values": ["*"]},
        ])
    except Exception as e:  # noqa: BLE001 - validering må ikke vælte kørslen
        print(f"  ADVARSEL: kunne ikke hente LABY49 til validering ({e}).")
        return
    aar = max(r["TID"] for r in rows)
    dst: dict[int, list[float]] = defaultdict(lambda: [0.0] * 4)
    for r in rows:
        if r["TID"] == aar and r["SDGSERVICE"] in DST_NIVEAU:
            dst[int(r["KOMGRP"])][DST_NIVEAU[r["SDGSERVICE"]]] += float(r["INDHOLD"].replace(",", "."))
    print(f"\n  Validering mod DST LABY49 {aar} (procent af befolkningen, genskabt / DST):")
    print("  gruppe   " + "".join(f"{n:>15}" for n in NIVEAUNAVN))
    fejl = []
    for g in sorted(grupper):
        linje = f"  {g:<8} "
        for n in range(4):
            fejl.append(abs(grupper[g][n] - dst[g][n]))
            linje += f"{grupper[g][n]:>8.1f} /{dst[g][n]:>5.1f}"
        print(linje)
    gns = sum(fejl) / len(fejl)
    print(f"  Gennemsnitlig afvigelse: {gns:.1f} procentpoint")
    if gns > MAKS_AFVIGELSE:
        print(f"  ADVARSEL: over {MAKS_AFVIGELSE} procentpoint. Tjek kilderne før tallene bruges.")


# ─── Hovedprogram ──────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(
        description="Adgang til offentlig transport pr. kommune (verdensmål 11.2.1), genskabt fra åbne data.")
    ap.add_argument("--dato", help="hverdag i GTFS-feedet, ÅÅÅÅMMDD (standard: vælges automatisk)")
    ap.add_argument("--genhent", action="store_true", help="hent køreplaner og adresser forfra")
    ap.add_argument("--cache", type=Path, default=STANDARD_CACHE, help="mappe til downloads")
    ap.add_argument("--radius", type=float, default=RADIUS_M, help="rækkevidde i meter, fugleflugt")
    args = ap.parse_args()
    t0 = time.time()

    print("Offentlig transport pr. kommune (genskabt DST-metode, verdensmål 11.2.1)")
    print("\n1/4 Køreplaner (Rejseplanen GTFS)")
    gtfs = hent_fil(GTFS_URL, args.cache / "GTFS.zip", args.genhent)
    with zipfile.ZipFile(gtfs) as zf:
        dato, ture, _ = vaelg_dato(zf, args.dato)
        print(f"  Hverdag: {dato.isoformat()} ({len(ture):,} ture uden behovsstyret kørsel)")
        afgange = afgange_pr_stop(zf, ture)
        stop = stoppesteder(zf, afgange)
    print(f"  {len(stop):,} stoppesteder med afgange kl. 6-20, "
          f"{sum(afgange.values()):,} afgange i alt")

    print("\n2/4 Adresser (DAR via DAWA)")
    koder, xs, ys, enheder, kommune = adresser(args.cache, args.genhent)

    print("\n3/4 Befolkning (Eurostat Census 2021, 1 km)")
    if not GRID_FIL.exists():
        byg_befolkningsgrid(args.cache, args.genhent)
    w = vaegte(xs, ys, enheder, befolkningsgrid())

    print(f"\n4/4 Serviceniveau (radius {args.radius:.0f} m fugleflugt)")
    f = frekvens(xs, ys, stop, args.radius)
    pr_kommune = [[0.0] * 4 for _ in koder]
    for wi, fi, ki in zip(w, f, kommune):
        pr_kommune[ki][niveau(fi)] += wi
    total = [sum(k[n] for k in pr_kommune) for n in range(4)]
    landstal = 100 * total[3] / sum(total)
    print(f"  Landstal (Danmark som helhed): {landstal:.1f}% med mindst 10 afgange i timen")

    grupper: dict[int, list[float]] = defaultdict(lambda: [0.0] * 4)
    for kode, niv in zip(koder, pr_kommune):
        for n in range(4):
            grupper[GRUPPE[kode]][n] += niv[n]
    valider({g: [100 * v / sum(niv) for v in niv] for g, niv in grupper.items()})

    with open(UD_FIL, "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["kommune_kode", "kommune_navn", "kommunegruppe", "public_transport_raw",
                     "public_transport_ref", "andel_middel", "andel_lavt", "andel_intet",
                     "befolkning_2021", "gtfs_dato"])
        for kode, niv in zip(koder, pr_kommune):
            b = sum(niv)
            wr.writerow([kode, KOMMUNER[kode], GRUPPE[kode], round(100 * niv[3] / b, 2),
                         round(landstal, 2), round(100 * niv[2] / b, 2), round(100 * niv[1] / b, 2),
                         round(100 * niv[0] / b, 2), round(b), dato.isoformat()])
    print(f"\n✓ Skrev {UD_FIL.relative_to(ROOT)} ({len(koder)} kommuner, {time.time() - t0:.0f}s)")
    print("BEMÆRK: master-CSV'en er IKKE opdateret. Se docs/offentlig-transport-genskabt.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
