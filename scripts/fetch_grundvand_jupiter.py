#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_grundvand_jupiter.py - nitrat og pesticider i drikkevand, direkte fra GEUS Jupiter
========================================================================================

Afløser fetch_nitrat_data.py og fetch_pesticider_data.py, som begge indeholdt
HÅRDKODEDE tal aftrykt fra en PDF:

  - nitrat:     Greenpeace-analyse nov. 2025, kun de 20 mest belastede kommuner.
                De øvrige 78 stod som null.
  - pesticider: DN's pressemeddelelse (Jupiter 2019-2023), ét samlet 5-års-tal.

Begge er nu erstattet af direkte opslag i GEUS Jupiter, så tallene kan
opdateres ved at køre scriptet, dækker alle kommuner med vandværker, og ikke
forældes uden at nogen opdager det.

DATAKILDE
---------
GEUS Jupiter via WFS: https://data.geus.dk/geusmap/ows/25832.jsp
  jupiter_anlaegsanalyser       - seneste analyse pr. (anlæg, stof)
  jupiter_grp_anlaegsanalyser   - seneste analyse pr. (anlæg, stofgruppe) + status
  jupiter_bor_vandfors_almen_ws - boringer m. anlæggets tilladte årsindvinding

AFGRÆNSNING (vigtig)
--------------------
Begge indikatorer afgrænses til `virktyp_over = VV` = almene vandværker, altså
BEHANDLET drikkevand. Udelader man den, blandes råvand fra enkeltboringer,
erhvervsanlæg og markvandingsanlæg ind, og nitratniveauet bliver markant
højere end det borgerne faktisk drikker (Aalborg: 32 mg/L uden filteret mod
19 mg/L med).

METODEFORSKEL FRA DEN GAMLE KILDE
---------------------------------
Nitrat vægtes her efter anlæggets tilladte årsindvinding (m³/år), så et
vandværk der forsyner 50.000 mennesker tæller mere end et der forsyner 200.
Det er samme princip som Greenpeace/Schullehner bruger, men koblingen til
forsyningsområder er en anden, så tallene er beslægtede - ikke identiske.
Efterprøvet mod Greenpeaces top-20: samme størrelsesorden og rangorden,
afvigelser på enkeltkommuner op til nogle mg/L.

Pesticider skifter tælleenhed fra BORINGER (DN) til VANDVÆRKER. Jupiter har
stof_status færdigklassificeret pr. anlæg, mens en borings-opgørelse ville
kræve at vi selv genskabte DN's udvælgelse af "aktive indvindingsboringer".
Vandværksniveauet er desuden tættere på det borgerne får ud af hanen.

FÆLDE
-----
Jupiter-WFS'en IGNORERER `CQL_FILTER` uden at fejle og returnerer så alle
stoffer. Brug OGC XML-`filter` som nedenfor - og tjek altid at det udtrukne
stof/gruppe er det forventede.

Brug (fra projektets rodmappe):
  python3 scripts/fetch_grundvand_jupiter.py

Output:
  data/nitrat_scores.csv
  data/pesticider_scores.csv
"""

from __future__ import annotations

import csv
import re
import ssl
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

WFS = ("https://data.geus.dk/geusmap/ows/25832.jsp"
       "?whoami=doughnut-platform&service=WFS&version=1.1.0&request=GetFeature")
SIDE = 4000            # MapServer leverer max ~4000 ad gangen
TIMEOUT = 300
_ctx = ssl.create_default_context()

STOFNR_NITRAT = "246"          # "246 - Nitrat"
STOFGRUPPE_PESTICID = "50"     # "50 - Pesticider, nedbrydningsprodukter og beslægtede stoffer"
VANDVAERK = "VV"               # virktyp_over: almene vandværker

# stof_status-værdier der betyder "over kravværdien lige nu" (0,1 µg/l for pesticider)
OVER_KRAVVAERDI = {
    "Aktuelt over kravværdi",
    "Aktuelt fund og tidl. over kravværdi",
}

# Ekspertgruppens anbefalede nitratgrænse, 2025. IKKE lovgrænsen på 50 mg/L -
# se den oprindelige metodenote i fetch_nitrat_data.py's dokumentation.
NITRAT_GRAENSE = 6.0

# Aktualitetsvindue. Jupiter gemmer den SENESTE analyse pr. anlæg, men for
# sjældent prøvetagne (ofte små eller halvsovende) vandværker kan "seneste"
# være 20 år gammel: 25% af nitratanalyserne er ældre end 2020, og enkelte går
# tilbage til 2001. Et tal fra 2001 siger intet om nutidens drikkevand, så
# analyser uden for vinduet udelades. Databasen indeholder desuden enkelte
# umulige årstal (en analyse er dateret 2031), som filtreret fra samme sted.
AKTUALITET_AAR = 10


# ── WFS-hjælp ─────────────────────────────────────────────────────────────

def _filter(*par: tuple[str, str]) -> str:
    inner = "".join(
        f"<PropertyIsEqualTo><PropertyName>{f}</PropertyName>"
        f"<Literal>{v}</Literal></PropertyIsEqualTo>" for f, v in par)
    if len(par) > 1:
        inner = f"<And>{inner}</And>"
    return f'<Filter xmlns="http://www.opengis.net/ogc">{inner}</Filter>'


def hent(lag: str, filt: str | None = None) -> list[str]:
    """Alle features fra et lag som rå XML-blokke. Sideinddelt."""
    ud: list[str] = []
    start = 0
    while True:
        u = f"{WFS}&typeName={lag}&maxFeatures={SIDE}&startIndex={start}"
        if filt:
            u += "&filter=" + urllib.parse.quote(filt)
        req = urllib.request.Request(u, headers={"User-Agent": "DoughnutDK/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=_ctx) as r:
            x = r.read().decode("utf-8", "ignore")
        if "ExceptionReport" in x:
            print(f"  FEJL: WFS afviste kaldet for {lag}", file=sys.stderr)
            print("  " + x[:300], file=sys.stderr)
            sys.exit(1)
        blokke = re.findall(r"<gml:featureMember>(.*?)</gml:featureMember>", x, re.S)
        ud.extend(blokke)
        print(f"    {len(ud)} features hentet...", end="\r", flush=True)
        if len(blokke) < SIDE:
            break
        start += SIDE
    print(f"    {len(ud)} features hentet.      ")
    return ud


def felt(blok: str, navn: str) -> str:
    m = re.search(rf"<ms:{navn}>([^<]*)</ms:{navn}>", blok)
    return m.group(1).strip() if m else ""


def _nu() -> int:
    import datetime
    return datetime.date.today().year


def aktuel(blok: str) -> bool:
    """
    Er analysen inden for aktualitetsvinduet?

    Udelader både for gamle prøver og umulige fremtidige årstal - begge dele
    findes i Jupiter. Mangler årstallet helt, beholdes rækken (den er sjælden,
    og et manglende år er ikke i sig selv et tegn på forældelse).
    """
    raa = felt(blok, "proeveaar_num")
    if not raa.isdigit():
        return True
    aar = int(raa)
    nu = _nu()
    return (nu - AKTUALITET_AAR) <= aar <= nu


def kommunekode(raa: str) -> str | None:
    """'  190 - Furesø' -> '190'."""
    m = re.match(r"\s*(\d{3})\s*-", raa or "")
    return m.group(1) if m else None


# ── Indvindingsmængder pr. anlæg (vægte til nitrat) ───────────────────────

def hent_maengder() -> dict[str, float]:
    print("  Henter anlæggenes tilladte årsindvinding...")
    ud: dict[str, float] = {}
    for b in hent("jupiter_bor_vandfors_almen_ws"):
        aid = felt(b, "anlaegid")
        raa = felt(b, "anlaeg_maengde_pr_aar")
        if not aid or not raa:
            continue
        try:
            v = float(raa)
        except ValueError:
            continue
        if v > 0:
            ud[aid] = v        # samme anlæg optræder pr. boring - mængden er anlæggets
    print(f"    {len(ud)} anlæg med kendt årsindvinding.")
    return ud


# ── Nitrat ────────────────────────────────────────────────────────────────

def beregn_nitrat(maengder: dict[str, float]) -> dict[str, dict]:
    print("  Henter nitratanalyser (stofnr 246, almene vandværker)...")
    blokke = hent("jupiter_anlaegsanalyser",
                  _filter(("stofnr_num", STOFNR_NITRAT), ("virktyp_over", VANDVAERK)))

    # Kontrollér at filteret faktisk bed (CQL-fælden, se docstring)
    stoffer = {felt(b, "stof") for b in blokke[:200]}
    if not all("Nitrat" in s for s in stoffer if s):
        print(f"  FEJL: filteret ramte forkert - fik {sorted(stoffer)[:5]}", file=sys.stderr)
        sys.exit(1)

    ialt = len(blokke)
    blokke = [b for b in blokke if aktuel(b)]
    if ialt != len(blokke):
        print(f"    {ialt - len(blokke)} analyser uden for aktualitetsvinduet "
              f"({AKTUALITET_AAR} år) udeladt.")

    pr_kom: dict[str, list[tuple[float, float]]] = defaultdict(list)   # (værdi, vægt)
    aar: list[int] = []
    for b in blokke:
        kode = kommunekode(felt(b, "kommune"))
        raa = felt(b, "maengde_num")
        if not kode or not raa:
            continue
        try:
            vaerdi = float(raa)
        except ValueError:
            continue
        anlaeg = felt(b, "anlaegid_num")
        vaegt = maengder.get(anlaeg, 0.0)
        pr_kom[kode].append((vaerdi, vaegt))
        try:
            aar.append(int(felt(b, "proeveaar_num")))
        except ValueError:
            pass

    # Vandværker uden kendt årsindvinding får MEDIANVÆGTEN, ikke vægten nul.
    #
    # Det er ikke en detalje. Manglende mængdedata er systematisk skævt: de 33%
    # af analyserne uden mængde har median 2,2 mg/L mod 1,5 mg/L for dem med.
    # Gav man dem vægten nul, ville netop de mest nitratbelastede vandværker
    # forsvinde ud af gennemsnittet - Thisted faldt fx til 4,4 mg/L, fordi
    # Hillerslev (49,6) og Skjoldborg (38,0) begge mangler mængde og dermed
    # blev vejet væk, mens to store lavnitrat-værker fik lov at dominere.
    kendte = sorted(w for _, par in pr_kom.items() for _, w in par if w > 0)
    median_vaegt = kendte[len(kendte) // 2] if kendte else 1.0

    ud: dict[str, dict] = {}
    imputeret = 0
    for kode, par in pr_kom.items():
        vaegte = []
        for _, w in par:
            if w > 0:
                vaegte.append(w)
            else:
                vaegte.append(median_vaegt)
                imputeret += 1
        sum_w = sum(vaegte)
        snit = sum(v * w for (v, _), w in zip(par, vaegte)) / sum_w
        ud[kode] = {"mg_l": round(snit, 2), "n": len(par)}
    if imputeret:
        print(f"    {imputeret} analyser uden kendt årsindvinding fik "
              f"medianvægt ({median_vaegt:,.0f} m³/år).")
    if aar:
        print(f"    prøveår {min(aar)}-{max(aar)}, {len(ud)} kommuner.")
    return ud


# ── Pesticider ────────────────────────────────────────────────────────────

def beregn_pesticider() -> dict[str, dict]:
    print("  Henter pesticidstatus (stofgruppe 50, almene vandværker)...")
    blokke = hent("jupiter_grp_anlaegsanalyser",
                  _filter(("stofgruppe_num", STOFGRUPPE_PESTICID),
                          ("virktyp_over", VANDVAERK)))

    grupper = {felt(b, "stofgruppe") for b in blokke[:200]}
    if not all("Pesticider" in g for g in grupper if g):
        print(f"  FEJL: filteret ramte forkert - fik {sorted(grupper)[:5]}", file=sys.stderr)
        sys.exit(1)

    ialt = len(blokke)
    blokke = [b for b in blokke if aktuel(b)]
    if ialt != len(blokke):
        print(f"    {ialt - len(blokke)} analyser uden for aktualitetsvinduet "
              f"({AKTUALITET_AAR} år) udeladt.")

    total: dict[str, int] = defaultdict(int)
    over: dict[str, int] = defaultdict(int)
    ukendt = 0
    for b in blokke:
        kode = kommunekode(felt(b, "kommune"))
        if not kode:
            continue
        status = felt(b, "stof_status")
        if not status:
            ukendt += 1
            continue
        total[kode] += 1
        if status in OVER_KRAVVAERDI:
            over[kode] += 1

    ud = {k: {"pct": round(over[k] / n * 100, 2), "over": over[k], "total": n}
          for k, n in total.items() if n}
    if ukendt:
        print(f"    {ukendt} anlæg uden status - udeladt.")
    print(f"    {len(ud)} kommuner.")
    return ud


# ── Skrivning ─────────────────────────────────────────────────────────────

def kommunenavne() -> dict[str, str]:
    p = DATA / "master_indicators.csv"
    ud: dict[str, str] = {}
    if p.exists():
        with open(p, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("kommune_kode") and r.get("kommune_navn"):
                    ud[r["kommune_kode"]] = r["kommune_navn"]
    return ud


def main() -> int:
    print("=" * 66)
    print("Nitrat og pesticider i drikkevand - GEUS Jupiter")
    print("=" * 66)

    navne = kommunenavne()
    if not navne:
        print("FEJL: kan ikke læse kommunenavne fra master_indicators.csv", file=sys.stderr)
        return 1

    maengder = hent_maengder()
    nitrat = beregn_nitrat(maengder)
    pesticid = beregn_pesticider()

    # ── nitrat_scores.csv ──
    raekker = []
    for kode in sorted(navne, key=int):
        d = nitrat.get(kode)
        if not d:
            raekker.append([kode, navne[kode], "", "", ""])
            continue
        ratio = round(d["mg_l"] / NITRAT_GRAENSE * 100, 1)
        raekker.append([kode, navne[kode], d["mg_l"], ratio, d["n"]])
    sti = DATA / "nitrat_scores.csv"
    with open(sti, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["kommune_kode", "kommune_navn", "nitrat_mg_l", "nitrat_ratio",
                    "nitrat_antal_anlaeg"])
        w.writerows(raekker)
    med = sum(1 for r in raekker if r[2] != "")
    print(f"\n✓ {sti.name}: {med}/{len(raekker)} kommuner med data")

    # ── pesticider_scores.csv ──
    # Ratio-konventionen bevares: kommunens andel ift. landsgennemsnittet.
    alle_over = sum(d["over"] for d in pesticid.values())
    alle_tot = sum(d["total"] for d in pesticid.values())
    nat_pct = (alle_over / alle_tot * 100) if alle_tot else 0.0
    print(f"  Landsplan: {alle_over}/{alle_tot} vandværker over kravværdi = {nat_pct:.2f}%")

    raekker = []
    for kode in sorted(navne, key=int):
        d = pesticid.get(kode)
        if not d:
            raekker.append([kode, navne[kode], "", "", "", ""])
            continue
        ratio = round(d["pct"] / nat_pct * 100, 1) if nat_pct else ""
        raekker.append([kode, navne[kode], d["pct"], ratio, d["total"], d["over"]])
    sti = DATA / "pesticider_scores.csv"
    with open(sti, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["kommune_kode", "kommune_navn", "pesticid_pct_over_graense",
                    "pesticid_ratio", "pesticid_total_anlaeg", "pesticid_over_graense_antal"])
        w.writerows(raekker)
    med = sum(1 for r in raekker if r[2] != "")
    print(f"✓ {sti.name}: {med}/{len(raekker)} kommuner med data")

    # ── auto-rebuild ──
    print("\n" + "=" * 55)
    print("AUTO-REBUILD af master_indicators.csv")
    print("=" * 55)
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from build_master_csv import auto_build_master
        auto_build_master()
    except Exception as e:
        print(f"✗ FEJL ved rebuild: {e}")
        print("  Kør manuelt: python3 scripts/build_master_csv.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
