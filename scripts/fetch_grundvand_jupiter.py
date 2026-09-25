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

PESTICIDER: FUND, IKKE OVER KRAVVÆRDIEN (besluttet 25. sep. 2026)
----------------------------------------------------------------
Indikatoren er andelen af aktive almene vandværker med FUND i seneste
analyse. Kun 33 aktive vandværker er aktuelt over kravværdien, så med den
afgrænsning ville næsten alle kommuner få 0, og indikatoren kunne ikke skelne
dem. Fund er GEUS' egen hovedindikator for pesticider i grundvandet.
Ved formidling: et fund kan ligge under eller over kravværdien (0,1 µg/l pr.
stof, 0,5 µg/l i alt). Et fund OVER kravværdien er en overskridelse af
drikkevandskravet; de fleste fund ligger under. Kravværdien er fastsat
politisk ud fra et forsigtighedsprincip, ikke ud fra stoffernes giftighed
(Miljøstyrelsen, jan. 2025), så en overskridelse er ikke i sig selv det
samme som en sundhedsrisiko.

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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kommuner import KOMMUNER  # noqa: E402  (de 98 kommuner, data/kommuner.json)

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

    # Kun aktive vandværker (fra sep. 2026): et nedlagt værk leverer ikke det
    # drikkevand borgerne får, og dets seneste analyse kan være fra lukningen.
    ialt = len(blokke)
    blokke = [b for b in blokke if er_aktiv(b)]
    print(f"    {ialt - len(blokke)} analyser fra nedlagte eller inaktive vandværker udeladt.")
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

# stof_status for "fund i seneste analyse", uanset niveau. Jupiter har fem
# værdier: "Intet nu og intet tidligere", "Tidligere fund", "Aktuelt fund under
# kravværdi", "Aktuelt fund og tidl. over kravværdi" og "Aktuelt over kravværdi".
AKTUELT_FUND = {
    "Aktuelt fund under kravværdi",
    "Aktuelt fund og tidl. over kravværdi",
    "Aktuelt over kravværdi",
}

# aktiv_num: 1 = aktivt anlæg. Nedlagte vandværker (2) leverer ikke drikkevand.
AKTIV = "1"


def er_aktiv(blok: str) -> bool:
    return felt(blok, "aktiv_num") == AKTIV


def eb_beta_binomial(tal: dict[str, tuple[int, int]]) -> tuple[float, float, float]:
    """Empirisk Bayes for andele: (alfa, beta, landsandel) for en Beta-prior
    estimeret med momentmetoden (Kleinman 1973, Journal of the American
    Statistical Association 68:46-54), ud fra
    {kommune: (fund, antal)}.

    Kommunens andel skønnes så som (fund + alfa) / (antal + alfa + beta): med
    mange vandværker er det næsten den observerede andel, med få trækkes den
    mod landsandelen. Det er standardgrebet for rater i små områder
    (Clayton & Kaldor 1987, Biometrics 43:671; Marshall 1991, Applied
    Statistics 40:283) og fjerner, at én ud af ét
    vandværk gav en kommune 100 procent."""
    N = sum(n for _, n in tal.values())
    p = sum(x for x, _ in tal.values()) / N
    k = len(tal)
    S = sum(n * (x / n - p) ** 2 for x, n in tal.values())
    # E[S] = (k-1)·p(1-p) + tau2·(N - Σn²/N - (k-1)) med vægte n_i (Kleinman
    # 1973). Leddet -(k-1) i nævneren manglede før 25. sep. 2026 og gav en
    # ca. 5% for lille tau2, altså lidt for meget udglatning.
    naevner = N - sum(n * n for _, n in tal.values()) / N - (k - 1)
    tau2 = (S - p * (1 - p) * (k - 1)) / naevner
    if tau2 <= 0:                       # ingen variation ud over tilfældigheden
        return 1e6 * p, 1e6 * (1 - p), p
    ab = p * (1 - p) / tau2 - 1
    return p * ab, (1 - p) * ab, p


def beregn_pesticider() -> tuple[dict[str, dict], float]:
    """Andel af kommunens AKTIVE almene vandværker, hvor seneste analyse (højst
    10 år gammel) har fund af pesticider eller nedbrydningsprodukter.

    Til og med sep. 2026 talte indikatoren "over kravværdien", men medregnede
    både nedlagte vandværker og "Aktuelt fund og tidl. over kravværdi", hvor
    den seneste analyse er UNDER kravværdien. Gentofte stod derfor med 100%
    over normen, selv om det eneste aktive værks seneste analyse var 0,064 µg/l.
    Kun 33 aktive værker er aktuelt over kravværdien; det er for få til at
    skelne kommuner. Fund er GEUS' egen primære overvågningsindikator, og for
    stoffer der ikke hører hjemme i grundvandet (novel entities) er
    tilstedeværelsen selv signalet."""
    print("  Henter pesticidstatus (stofgruppe 50, almene vandværker)...")
    blokke = hent("jupiter_grp_anlaegsanalyser",
                  _filter(("stofgruppe_num", STOFGRUPPE_PESTICID),
                          ("virktyp_over", VANDVAERK)))

    grupper = {felt(b, "stofgruppe") for b in blokke[:200]}
    if not all("Pesticider" in g for g in grupper if g):
        print(f"  FEJL: filteret ramte forkert - fik {sorted(grupper)[:5]}", file=sys.stderr)
        sys.exit(1)
    kendte = {felt(b, "stof_status") for b in blokke} - {""}
    ukendte_status = kendte - AKTUELT_FUND - {"Intet nu og intet tidligere", "Tidligere fund"}
    if ukendte_status:
        print(f"  FEJL: ukendte stof_status-værdier {sorted(ukendte_status)} - "
              f"GEUS har ændret klassifikationen, tjek AKTUELT_FUND", file=sys.stderr)
        sys.exit(1)

    ialt = len(blokke)
    blokke = [b for b in blokke if er_aktiv(b)]
    print(f"    {ialt - len(blokke)} nedlagte eller inaktive vandværker udeladt.")
    n0 = len(blokke)
    blokke = [b for b in blokke if aktuel(b)]
    if n0 != len(blokke):
        print(f"    {n0 - len(blokke)} analyser uden for aktualitetsvinduet "
              f"({AKTUALITET_AAR} år) udeladt.")

    total: dict[str, int] = defaultdict(int)
    fund: dict[str, int] = defaultdict(int)
    for b in blokke:
        kode = kommunekode(felt(b, "kommune"))
        status = felt(b, "stof_status")
        if not kode or not status:
            continue
        total[kode] += 1
        if status in AKTUELT_FUND:
            fund[kode] += 1

    tal = {k: (fund[k], n) for k, n in total.items() if n}
    alfa, beta, p = eb_beta_binomial(tal)
    print(f"    {sum(x for x, _ in tal.values())}/{sum(n for _, n in tal.values())} aktive "
          f"vandværker med fund = {p * 100:.2f}%; Beta-prior alfa={alfa:.2f}, beta={beta:.2f} "
          f"(svarer til {alfa + beta:.0f} vandværkers vægt)")
    ud = {k: {"pct": round((x + alfa) / (n + alfa + beta) * 100, 2),
              "pct_observeret": round(x / n * 100, 2), "fund": x, "total": n}
          for k, (x, n) in tal.items()}
    print(f"    {len(ud)} kommuner.")
    return ud, p * 100


# ── Skrivning ─────────────────────────────────────────────────────────────

def kommunenavne() -> dict[str, str]:
    return dict(KOMMUNER)


def main() -> int:
    print("=" * 66)
    print("Nitrat og pesticider i drikkevand - GEUS Jupiter")
    print("=" * 66)

    navne = kommunenavne()

    maengder = hent_maengder()
    nitrat = beregn_nitrat(maengder)
    pesticid, nat_pct = beregn_pesticider()

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
    # Råværdien er den empirisk Bayes-udglattede andel (se eb_beta_binomial),
    # referencen landsandelen: alle aktive vandværker med fund / alle aktive.
    raekker = []
    for kode in sorted(navne, key=int):
        d = pesticid.get(kode)
        if not d:
            raekker.append([kode, navne[kode], "", "", "", "", "", round(nat_pct, 4)])
            continue
        ratio = round(d["pct"] / nat_pct * 100, 1) if nat_pct else ""
        raekker.append([kode, navne[kode], d["pct"], d["pct_observeret"], ratio,
                        d["total"], d["fund"], round(nat_pct, 4)])
    sti = DATA / "pesticider_scores.csv"
    with open(sti, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["kommune_kode", "kommune_navn", "pesticid_pct_fund", "pesticid_pct_fund_observeret",
                    "pesticid_ratio", "pesticid_aktive_anlaeg", "pesticid_anlaeg_med_fund",
                    "pesticider_ref"])
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
