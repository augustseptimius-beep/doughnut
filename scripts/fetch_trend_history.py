#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_trend_history.py

Henter historiske tidsserier (typisk 2010-2026) for de platform-indikatorer der
har en efterprøvet metode til at trække historik fra DST og Klimaregnskabet.dk.
Bruges til at beregne en retningspil (op/ned/stagneret) pr. indikator - se
webapp/lib/shared.ts KommuneData.trends og scripts/build_trends_csv.py.

Baggrund og efterprøvning: se docs/opgave-fjernvarme-net-mapping.md er IKKE
relevant her - se i stedet den plan der lå til grund for dette script
("PLAN retningsvisning i doughnut-platformen.md"), bilag A og B. De fem DST-
fælder (elimination-flag, ét tidspunkt pr. år for bestandstal, pin_ialt for
forholdstal, ordgrænser i "I alt"-match, kommuner tabellen ikke kender) er
alle håndteret i hentemotoren nedenfor.

Designprincip: en søgning der ikke rammer, SKAL fejle højlydt og springes over
- aldrig falde tilbage på et forkert tal. Derfor mangler nogle af de sværere
indikatorer (fx gini, poverty_relative) muligvis i output hvis DST har ændret
en tekst siden dette blev skrevet. Tjek loggen (trend_history_log.txt).

Output:
  data/trend_history_raw.csv   - kommune_kode,indicator_id,aar,vaerdi
  data/trend_history_log.txt   - fuld log, inkl. evt. fejlede indikatorer

Kør fra projektets rodmappe:
  python3 scripts/fetch_trend_history.py

Kalder til sidst auto_build_trends() (build_trends_csv.py), som regenererer
data/trend_indicators.csv - ligesom fetch-scripts allerede kalder
auto_build_master() for master_indicators.csv. De to skal altid opdateres
sammen, så de aldrig kan drive fra hinanden.
"""

from __future__ import annotations

import csv
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from api_noegler import (  # noqa: E402
    hent_noegle,
    kraev_noegle,
    KLIMA_HJAELP,
    UVM_HJAELP,
)

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_OUTPUT = DATA_DIR / "trend_history_raw.csv"
LOG_OUTPUT = DATA_DIR / "trend_history_log.txt"

DST_API = "https://api.statbank.dk/v1"
FRA_AAR = 2010
TIMEOUT = 90
CELLELOFT = 800_000
PAUSE = 0.35

KLIMAREGNSKABET_API = "https://klimaregnskabet.dk/api/municipality-data"
KLIMAREGNSKABET_KEY = hent_noegle("KLIMAREGNSKABET_API_KEY")
KLIMA_AAR = list(range(2018, 2025))

LOG: list[str] = []


def log(s: str) -> None:
    print(s)
    LOG.append(s)


# ─── Kommuneliste: læses fra master_indicators.csv, så den altid matcher platformen ──

def load_kommuner() -> dict[str, str]:
    path = DATA_DIR / "master_indicators.csv"
    if not path.exists():
        log(f"FEJL: {path} findes ikke - kan ikke hente kommuneliste.")
        sys.exit(1)
    ud: dict[str, str] = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            kode = (row.get("kommune_kode") or "").strip()
            navn = (row.get("kommune_navn") or "").strip()
            if kode and navn:
                ud[kode] = navn
    return ud


KOMMUNER = load_kommuner()
log(f"Kommuneliste: {len(KOMMUNER)} kommuner (fra master_indicators.csv)")


# ══════════════════════════════════════════════════════════════════════════
# HENTEMOTOR - ported fra det efterprøvede forarbejde (dst.py), udvidet til
# alle 98 kommuner i stedet for kun landkommunerne.
# ══════════════════════════════════════════════════════════════════════════

_ctx = ssl.create_default_context()


def _hent(url, data=None, forsoeg=4):
    hoveder = {"User-Agent": "Doughnut-trendhistorik/1.0", "Accept": "*/*"}
    if data is not None:
        hoveder["Content-Type"] = "application/json"
        anm = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=hoveder)
    else:
        anm = urllib.request.Request(url, headers=hoveder)
    sidste = None
    for n in range(forsoeg):
        time.sleep(PAUSE if n == 0 else PAUSE + 2 ** n)
        try:
            with urllib.request.urlopen(anm, timeout=TIMEOUT, context=_ctx) as sv:
                return sv.read().decode("utf-8")
        except urllib.error.HTTPError as ex:
            if ex.code == 429 or 500 <= ex.code < 600:
                sidste = ex
                log(f"   (DST svarede {ex.code}, venter og prøver igen)")
                continue
            raise
        except (urllib.error.URLError, TimeoutError, OSError) as ex:
            sidste = ex
            log("   (netværksfejl, venter og prøver igen)")
            continue
    raise sidste


def matcher(tekst, soegeord):
    t = (tekst or "").lower().strip()
    for s in soegeord:
        s = s.lower().strip()
        if s.startswith("="):
            if t == s[1:]:
                return True
        elif s in t:
            return True
    return False


AREAL = ["OMRÅDE", "BOPOMR", "KOMGRP", "KOMMUNEDK", "KOMK", "OMRADE", "KOMMUNE",
         "AMT", "ADMKOM", "BLSTKOM"]
IALT = [r"\bi alt\b", r"\balle\b", r"\btotal\b", r"\bi␣alt\b"]
TEST_KOMMUNE = "787"  # Thisted - bruges kun til debug-log, ikke til filtrering


def find_areal(info):
    for v in info.get("variables", []):
        if v.get("id", "").upper() in AREAL:
            if any(str(x.get("id")) in KOMMUNER for x in v.get("values", [])):
                return v
    for v in info.get("variables", []):
        koder = {str(x.get("id")) for x in v.get("values", [])}
        if len(koder & set(KOMMUNER)) > 50:
            return v
    return None


def find_tid(info):
    for v in info.get("variables", []):
        if v.get("time") or v.get("id", "").lower() in ("tid", "time"):
            return v
    return None


def vaelg_tid(var, tilstand):
    alle = [str(x.get("id")) for x in var.get("values", [])]
    aar = [t for t in alle if re.fullmatch(r"\d{4}", t)]
    if aar:
        return sorted(t for t in aar if int(t) >= FRA_AAR)

    if tilstand == "alle_kvartaler":
        valgt = [t for t in alle if re.fullmatch(r"\d{4}K\d", t)]
    else:
        valgt = [t for t in alle if re.fullmatch(r"\d{4}(K1|M01)", t)]
    if not valgt:
        log("   ADVARSEL: kunne ikke finde ét fast tidspunkt pr. år i tabellen.")
        valgt = [t for t in alle if re.match(r"\d{4}", t)]
    return sorted(t for t in valgt if int(t[:4]) >= FRA_AAR)


def ialt_vaerdi(vaerdier):
    for k, tx in vaerdier.items():
        if k.upper() in ("TOT", "IALT", "TOTAL"):
            return k
    for k, tx in vaerdier.items():
        if any(re.search(m, (tx or "").lower()) for m in IALT):
            return k
    return None


def beskriv_tabel(info, areal_id, tid_id):
    log("   Tabellen indeholder disse variabler og værdier:")
    for v in info.get("variables", []):
        if v["id"] in (areal_id, tid_id):
            continue
        tekster = [x.get("text") for x in v.get("values", [])]
        vis = tekster[:14] + (["..."] if len(tekster) > 14 else [])
        log(f"     {v['id']} ({len(tekster)} værdier): {vis}")


def hent(ind):
    log(f"\n→ {ind['navn']}  [{ind['tabel']}]")
    try:
        info = json.loads(_hent(f"{DST_API}/tableinfo/{ind['tabel']}?lang=da&format=JSON"))
    except Exception as ex:
        log(f"   FEJL: kunne ikke hente tabelinfo: {ex}")
        return []

    areal, tidsvar = find_areal(info), find_tid(info)
    if not areal or not tidsvar:
        log("   FEJL: fandt ikke kommune- eller tidsvariabel.")
        return []

    perioder = vaelg_tid(tidsvar, ind.get("tid", "aar"))
    if not perioder:
        log("   FEJL: ingen brugbare perioder.")
        return []
    pr_aar = len(perioder) / max(len({p[:4] for p in perioder}), 1)
    if pr_aar > 1.01 and not ind.get("kraev_hele_aar"):
        log(f"   ADVARSEL: {pr_aar:.0f} perioder pr. år lægges sammen. "
            f"For bestandstal giver det for høje tal.")

    oevrige = [v for v in info.get("variables", []) if v["id"] not in (areal["id"], tidsvar["id"])]

    noegle_id, noegle_valg = None, []
    if not ind.get("helhed"):
        soeg_kode = ind.get("soeg_kode")
        if soeg_kode:
            # Kode-match i stedet for tekst-match. Bruges når variablen er
            # hierarkisk (fx HFUDD), hvor en overkategoris tekst ("Gymnasiale
            # uddannelser") er en delstreng af dens egne underkategoriers tekst
            # ("Alment gymnasiale uddannelser") - tekstsøgning ville dobbelttælle.
            # soeg_var indsnævrer til én bestemt variabel, så en generisk
            # kodeliste (fx "0".."17") ikke ved et uheld rammer en anden
            # variabel med samme småtal-koder (fx KØN="1"/"2").
            soeg_var = ind.get("soeg_var")
            kandidater = [v for v in oevrige if v["id"].upper() == soeg_var.upper()] if soeg_var else oevrige
            for v in kandidater:
                koder = {str(x.get("id")) for x in v.get("values", [])}
                traef = [k for k in soeg_kode if k in koder]
                if traef and len(traef) < len(koder):
                    noegle_id, noegle_valg = v["id"], traef
                    log(f"   Nøgle (kode): {v['id']} = {traef}")
                    break
            if not noegle_id:
                log(f"   FEJL: fandt ingen af koderne {soeg_kode} i {ind['tabel']}. "
                    "Springes over i stedet for at hente et forkert tal.")
                beskriv_tabel(info, areal["id"], tidsvar["id"])
                return []
        else:
            soeg, undtag = ind["soeg"], ind.get("undtag", [])
            for v in oevrige:
                vaerdier = {str(x.get("id")): (x.get("text") or "") for x in v.get("values", [])}
                traef = [k for k, tx in vaerdier.items()
                         if matcher(tx, soeg) and not any(u.lower() in tx.lower() for u in undtag)]
                if traef and len(traef) < len(vaerdier):
                    noegle_id, noegle_valg = v["id"], traef
                    log(f"   Nøgle: {v['id']} = {[vaerdier[k] for k in traef]}")
                    break
        if not noegle_id:
            log(f"   FEJL: fandt ingen værdi der matcher {ind['soeg']} i {ind['tabel']}. "
                "Springes over i stedet for at hente et forkert tal.")
            beskriv_tabel(info, areal["id"], tidsvar["id"])
            return []

    findes = {str(x.get("id")) for x in areal.get("values", [])}
    koder = [k for k in KOMMUNER if k in findes]
    mangler_n = len(KOMMUNER) - len(koder)
    if mangler_n:
        log(f"   Tabellen kender ikke {mangler_n} af {len(KOMMUNER)} kommuner. De udelades.")
    if not koder:
        log("   FEJL: tabellen kender ingen af platformens kommuner.")
        return []
    valg = {areal["id"]: koder}
    brugte = set()
    if noegle_id:
        valg[noegle_id] = noegle_valg
        brugte.add(noegle_id)

    for ekstra in ind.get("ekstra", []):
        fundet = False
        for v in oevrige:
            if v["id"] in brugte:
                continue
            vaerdier = {str(x.get("id")): (x.get("text") or "") for x in v.get("values", [])}
            traef = [k for k, tx in vaerdier.items()
                     if matcher(tx, ekstra["soeg"])
                     and not any(u.lower() in tx.lower() for u in ekstra.get("undtag", []))]
            if traef and len(traef) < len(vaerdier):
                valg[v["id"]] = traef
                brugte.add(v["id"])
                log(f"   Filter: {v['id']} = {[vaerdier[k] for k in traef]}")
                fundet = True
                break
        if not fundet:
            log(f"   FEJL: fandt ingen værdi der matcher {ekstra['soeg']}.")
            beskriv_tabel(info, areal["id"], tidsvar["id"])
            return []

    udeladt = []
    for v in oevrige:
        if v["id"] in brugte:
            continue
        if v.get("elimination", True):
            if ind.get("pin_ialt"):
                vaerdier = {str(x.get("id")): (x.get("text") or "")
                            for x in v.get("values", [])}
                ia = ialt_vaerdi(vaerdier)
                if ia:
                    valg[v["id"]] = [ia]
                    log(f"   {v['id']} = {vaerdier[ia]} (pinnet, forholdstal)")
                    continue
                log(f"   ADVARSEL: {v['id']} har ingen I alt-værdi at pinne til.")
            udeladt.append(v["id"])
            continue
        vaerdier = {str(x.get("id")): (x.get("text") or "") for x in v.get("values", [])}
        ia = ialt_vaerdi(vaerdier)
        if ia:
            valg[v["id"]] = [ia]
            log(f"   {v['id']} = {vaerdier[ia]} (skal angives)")
        else:
            valg[v["id"]] = list(vaerdier)
            log(f"   {v['id']} = alle {len(vaerdier)} værdier lagt sammen (skal angives, ingen I alt)")
    if udeladt:
        log(f"   Udeladt, lægges sammen af DST: {', '.join(udeladt)}")

    pr_periode = len(koder)
    for k, v in valg.items():
        if k != areal["id"]:
            pr_periode *= len(v)
    pr_hold = max(1, CELLELOFT // max(pr_periode, 1))
    hold = [perioder[i:i + pr_hold] for i in range(0, len(perioder), pr_hold)]
    if len(hold) > 1:
        log(f"   Kaldet deles op i {len(hold)} bidder for at holde cellegrænsen.")

    navn2kode = {n: k for k, n in KOMMUNER.items()}
    saml = defaultdict(float)
    perioder_pr_aar = defaultdict(set)

    for bid in hold:
        krop = {"table": ind["tabel"], "format": "CSV", "lang": "da",
                "variables": [{"code": k, "values": v} for k, v in valg.items()]
                             + [{"code": tidsvar["id"], "values": bid}]}
        try:
            tekst = _hent(f"{DST_API}/data", data=krop)
        except urllib.error.HTTPError as ex:
            detalje = ex.read().decode("utf-8", "ignore")[:250] if hasattr(ex, "read") else ""
            log(f"   FEJL ved datakald ({ex.code}): {detalje}")
            return []
        except Exception as ex:
            log(f"   FEJL ved datakald: {ex}")
            return []

        raekker = list(csv.DictReader(StringIO(tekst), delimiter=";"))
        if not raekker:
            continue
        kol = list(raekker[0].keys())
        areal_kol = kol[0]
        tid_kol = next((k for k in kol if k.upper() in ("TID", "TIME")), None)
        val_kol = next((k for k in kol if k.upper() == "INDHOLD"), kol[-1])
        if not tid_kol:
            log("   FEJL: ingen TID-kolonne i svaret.")
            return []

        for r in raekker:
            omr = (r.get(areal_kol) or "").strip()
            felt = omr.split()
            kode = felt[0] if felt and felt[0].isdigit() else navn2kode.get(omr)
            if kode not in KOMMUNER:
                continue
            raa = (r.get(val_kol) or "").strip()
            if raa in ("", "..", ".", "x", "X", "-"):
                continue
            try:
                v = float(raa.replace(".", "").replace(",", ".")
                          if re.fullmatch(r"[\d.,\-]+", raa) else raa)
            except ValueError:
                continue
            periode = (r.get(tid_kol) or "").strip()
            aar = periode[:4]
            saml[(kode, aar)] += v
            perioder_pr_aar[aar].add(periode)

    if ind.get("kraev_hele_aar") and perioder_pr_aar:
        forventet = max(len(p) for p in perioder_pr_aar.values())
        ufulde = {a for a, p in perioder_pr_aar.items() if len(p) < forventet}
        if ufulde:
            log(f"   Frasorterer ufuldstændige år: {sorted(ufulde)}")
            saml = {k: v for k, v in saml.items() if k[1] not in ufulde}

    ud = [{"kommune_kode": k, "aar": a, "vaerdi": round(v, 4)} for (k, a), v in saml.items()]

    th = sorted((int(r["aar"]), r["vaerdi"]) for r in ud if r["kommune_kode"] == TEST_KOMMUNE)
    if th:
        log(f"   OK: Thisted {th[0][0]} = {th[0][1]:,.1f}  →  {th[-1][0]} = {th[-1][1]:,.1f}  "
            f"({len(ud)} kommune-år i alt)".replace(",", "."))
    else:
        log(f"   OK: {len(ud)} kommune-år hentet (ingen Thisted-tal - kan være normalt).")
    return ud


def serie(spec):
    """Henter én indikator og returnerer {(kommunekode, år): værdi}."""
    ind = dict(spec)
    ind.setdefault("tabel", "")
    ind.setdefault("navn", ind.get("id", "?"))
    return {(r["kommune_kode"], r["aar"]): r["vaerdi"] for r in hent(ind)}


# ══════════════════════════════════════════════════════════════════════════
# INDIKATORLISTE - de 42 platform-indikatorer med efterprøvet historik.
#
# platform-id matcher INDICATORS[].id i webapp/lib/shared.ts (sociale) eller
# ECO_SUB_INDICATORS[].id i scripts/build_master_csv.py (økologiske).
# "pr" normaliserer optællinger til pr. 1.000/100.000/10.000 indbyggere via
# den historiske folketalsserie, så en kommune med faldende befolkning ikke
# fejlagtigt ser ud til at forbedre sig.
# ══════════════════════════════════════════════════════════════════════════

FOLKETAL = {"id": "folketal", "navn": "Folketal", "tabel": "FOLK1A", "helhed": True}
# Master normaliserer underretninger pr. 1.000 0-17-årige, ikke hele befolkningen
# (fetch_udvidelse_data.py). ALDER-koderne i FOLK1A er enkeltårige "0".."17".
BOERNETAL = {"id": "boernetal", "navn": "Børnetal 0-17 år", "tabel": "FOLK1A",
             "soeg_kode": [str(a) for a in range(18)], "soeg_var": "ALDER"}

SIMPLE = [
    # --- Sundhed ---
    dict(id="hjemsyg", navn="Hjemmesygepleje-modtagere", tabel="HJEMSYG", helhed=True, pr=1000),
    dict(id="medicin", navn="Antidepressivt forbrug", tabel="MEDI1",
         soeg=["recepter pr. 100 borgere"], ekstra=[{"soeg": ["antidepres"]}], pin_ialt=True),
    dict(id="laegekontakt", navn="Andel med lægekontakt", tabel="SYGP1",
         soeg=["almen læge i alt"], pr=100),
    dict(id="boerneovervaeght", navn="Overvægt blandt 6-7-årige", tabel="LABY26",
         soeg=["6-7 år"], pin_ialt=True),
    dict(id="hospital_short_taeller", navn="Sygehusophold, alle varigheder", tabel="SBR01",
         soeg=["alle varigheder"]),
    dict(id="hospital_short_naevner", navn="Sygehusophold, personer i alt", tabel="SBR01",
         soeg=["=personer i alt"]),
    dict(id="hospital_long_taeller", navn="Sygehusophold 12+ timer", tabel="SBR01",
         soeg=["12 timer eller derover"]),

    # --- Uddannelse ---
    dict(id="class_size", navn="Klassekvotient i folkeskolen", tabel="KVOTIEN",
         soeg=["=i alt"], ekstra=[{"soeg": ["folkeskoler"]}], pin_ialt=True),
    dict(id="daycare_ratio", navn="Normering i daginstitution 3-5 år", tabel="BOERN8",
         soeg=["daginstitution 3-5"], pin_ialt=True),
    dict(id="educated_staff_taeller", navn="Pædagoguddannede", tabel="BOERN1",
         soeg=["=pædagog", "=pædagogisk leder"]),
    dict(id="educated_staff_naevner", navn="Personale i alt", tabel="BOERN1",
         soeg=["=i alt"]),
    # HFUDD er hierarkisk (H20 "Gymnasiale uddannelser" har underkoder som
    # H2010 "Alment gymnasiale uddannelser" hvis tekst også indeholder
    # "gymnasiale") - derfor kode-match (soeg_kode), ikke tekstsøgning, for
    # ikke at tælle en kategori både som overkategori og underkategori.
    dict(id="low_education_taeller", navn="25-29-årige med kun grundskole", tabel="HFUDD11",
         soeg_kode=["H10"], soeg_var="HFUDD", ekstra=[{"soeg": ["25-29"]}], pin_ialt=True),
    dict(id="low_education_naevner", navn="25-29-årige i alt", tabel="HFUDD11",
         soeg=["=i alt"], ekstra=[{"soeg": ["25-29"]}], pin_ialt=True),
    # HFUDD11, ikke HFUDD10: sidstnævnte er inaktiv hos DST og stopper ved 2019.
    dict(id="education_taeller", navn="30-34-årige med kompetencegivende uddannelse",
         tabel="HFUDD11",
         soeg_kode=["H20", "H30", "H35", "H40", "H50", "H60", "H70", "H80"],
         soeg_var="HFUDD", ekstra=[{"soeg": ["30-34"]}], pin_ialt=True),
    dict(id="education_naevner", navn="30-34-årige i alt", tabel="HFUDD11",
         soeg=["=i alt"], ekstra=[{"soeg": ["30-34"]}], pin_ialt=True),

    # --- Velfærd ---
    dict(id="vulnerable_children", navn="Udsatte børn og unge", tabel="BU43",
         soeg=["udsatte børn og unge i alt"], pin_ialt=True),
    dict(id="child_notifications", navn="Underretninger om børn", tabel="UND2",
         soeg=["=i alt"], pr=1000),
    dict(id="neet_taeller", navn="NEET - ikke-aktive", tabel="NEET1",
         soeg=["=ikke-aktive (neet)"]),
    dict(id="neet_naevner", navn="NEET - aktive og ikke-aktive i alt", tabel="NEET1",
         soeg=["aktive og ikke-aktive i alt"]),
    dict(id="poverty_relative", navn="Relativ fattigdom", tabel="IFOR12P",
         soeg=["60"], pin_ialt=True),
    dict(id="child_poverty", navn="Børnefattigdom 0-17 år", tabel="LABY07",
         soeg=["0-17"], pin_ialt=True),
    dict(id="gini", navn="Gini-koefficient", tabel="IFOR41",
         soeg=["gini"], pin_ialt=True),

    # --- Bolig ---
    dict(id="housing_area", navn="Boligareal pr. person", tabel="BOL106",
         soeg=["areal per person"], ekstra=[{"soeg": ["=i alt"]}], pin_ialt=True),
    dict(id="vacant_housing_taeller", navn="Ubeboede boliger", tabel="BOL101",
         soeg=["ubeboede"]),
    # BOL101's BEBO-variabel har ingen "I alt"-værdi (kun beboet/ubeboet/
    # fritidshus-ubeboet) - helhed=True lader DST summere alle tre selv.
    dict(id="vacant_housing_naevner", navn="Boliger i alt", tabel="BOL101", helhed=True),
    # BEBO har elimination=False i BOL102 - SKAL angives eksplicit (kan ikke
    # udelades), derfor pin via ekstra på hver af de tre specs nedenfor.
    dict(id="housing_no_wc_taeller", navn="Boliger uden eget toilet", tabel="BOL102",
         soeg=["wc udenfor boligen", "andet/intet toilet"],
         ekstra=[{"soeg": ["boliger med cpr tilmeldte personer"]}]),
    dict(id="housing_no_bath_taeller", navn="Boliger uden eget bad", tabel="BOL102",
         soeg=["ikke bad eller adgang til bad"],
         ekstra=[{"soeg": ["boliger med cpr tilmeldte personer"]}]),
    # helhed=True lader DST summere ALLE toilet-/bad-kategorier, inkl. "Uoplyst".
    # Master (fetch_udvidelse_data.py) udelader "Uoplyst" i sin nævner. Efterprøvet
    # på alle 98 kommuner 2010-2026: forskellen flytter trend-procenten med højst
    # 0,75 pp og vender retningen i NUL kommuner, fordi "Uoplyst" er promillestort.
    # Én fælles nævner til både toilet og bad er derfor valgt frem for to ekstra kald.
    dict(id="housing_beboede_total", navn="Beboede boliger i alt (nævner: toilet/bad)",
         tabel="BOL102", helhed=True,
         ekstra=[{"soeg": ["boliger med cpr tilmeldte personer"]}]),

    # --- Demokrati ---
    dict(id="voter_turnout_national", navn="Stemmedeltagelse folketingsvalg", tabel="LABY09",
         soeg=["=stemmeprocent"], pin_ialt=True),
    # LABY08 (kommunalvalg) - IKKE KVBPCT, som kun har landstal uden
    # kommune-opdeling. VALRES har elimination=False, "stemmeprocent" er
    # allerede den færdigberegnede andel, matcher direkte doughnut_scores.csv.
    dict(id="voter_turnout", navn="Stemmedeltagelse kommunalvalg", tabel="LABY08",
         soeg=["=stemmeprocent"]),

    # --- Kultur & fritid ---
    dict(id="music_school", navn="Musikskoleelever", tabel="SKOLM02B", helhed=True, pr=1000),
    # BIB3A, ikke BIB1: DST har gjort BIB1 inaktiv (stopper 2024). Tallene er
    # identiske, men BIB3A splitter på SAMLING (børn/voksne) - begge lægges
    # sammen af DST, fordi SAMLING har elimination=True og ikke pinnes her.
    dict(id="library_use", navn="Biblioteksudlån", tabel="BIB3A",
         soeg=["=udlån"], ekstra=[{"soeg": ["materialetyper i alt"]}], pr=1),
    # REGK31: FUNKTION-koder matcher fetch_doughnut_data.py's egen definition.
    # PRISENHED har elimination=False - SKAL angives eksplicit (Pr. indbygger).
    dict(id="kultur_spending", navn="Kommunale kulturudgifter pr. indb.", tabel="REGK31",
         soeg_kode=["33561", "33562", "33563", "33564"], soeg_var="FUNKTION",
         ekstra=[{"soeg": ["driftskonti"]}, {"soeg": ["=i alt (netto)"]},
                 {"soeg": ["pr. indbygger"]}]),

    # --- Lokalsamfund ---
    dict(id="civil_society", navn="Kommunal støtte til frivillige foreninger pr. indb.",
         tabel="REGK31", soeg_kode=["33873"], soeg_var="FUNKTION",
         ekstra=[{"soeg": ["driftskonti"]}, {"soeg": ["=i alt (netto)"]},
                 {"soeg": ["pr. indbygger"]}]),

    # --- Tryghed ---
    dict(id="traffic_accidents", navn="Trafikulykker", tabel="UHELDK1",
         soeg=["personskade i alt"], pr=100000),
    dict(id="crime_rate", navn="Anmeldte forbrydelser", tabel="STRAF11",
         soeg=["=overtrædelsens art i alt"], pin_ialt=True, pr=1000,
         tid="alle_kvartaler", kraev_hele_aar=True),

    # --- Foreningsliv ---
    dict(id="sports_facilities", navn="Idrætsfaciliteter", tabel="IDRFAC01",
         helhed=True, pr=10000),
    dict(id="sports_membership", navn="Idrætsmedlemskaber", tabel="IDRAKT02",
         helhed=True, pin_ialt=True),
    # DRANST "I alt" summerer drift OG anlæg - platformen bruger kun drift
    # (se planens bilag 3.4: anlæg medregnet giver ca. 17% for højt tal).
    dict(id="sports_spending", navn="Kommunale idrætsudgifter", tabel="IDRFIN02",
         soeg=["=i alt"], ekstra=[{"soeg": ["driftskonti"]}]),

    # --- Lighed ---
    dict(id="low_income", navn="Andel i lavindkomstgruppe", tabel="LABY07",
         soeg=["=alder i alt"]),
    dict(id="gender_leadership_taeller", navn="Kvinder i lederstillinger", tabel="RAS301",
         soeg=["=kvinder"], ekstra=[{"soeg": ["ledelsesarbejde"]}]),
    dict(id="gender_leadership_naevner", navn="Ledere i alt", tabel="RAS301",
         soeg=["ledelsesarbejde"]),
    dict(id="income_gender_gap_taeller", navn="Kvinders disponible indkomst", tabel="INDKP101",
         soeg=["=kvinder"],
         ekstra=[{"soeg": ["gennemsnit for alle personer"]},
                 {"soeg": ["=1 disponibel indkomst (2+30-31-32-35)"]}], pin_ialt=True),
    dict(id="income_gender_gap_naevner", navn="Mænds disponible indkomst", tabel="INDKP101",
         soeg=["=mænd"],
         ekstra=[{"soeg": ["gennemsnit for alle personer"]},
                 {"soeg": ["=1 disponibel indkomst (2+30-31-32-35)"]}], pin_ialt=True),
    dict(id="employment_origin_gap_taeller", navn="Beskæftigelse, ikke-vestlige", tabel="RAS200",
         soeg=["ikke-vestlige lande"], undtag=["efterkommere"],
         ekstra=[{"soeg": ["beskæftigelsesfrekvens"]}, {"soeg": ["=16-64 år"]}], pin_ialt=True),
    dict(id="employment_origin_gap_naevner", navn="Beskæftigelse, dansk oprindelse", tabel="RAS200",
         soeg=["dansk oprindelse"],
         ekstra=[{"soeg": ["beskæftigelsesfrekvens"]}, {"soeg": ["=16-64 år"]}], pin_ialt=True),
    dict(id="le_gender_gap_taeller", navn="Middellevetid kvinder", tabel="HISBK",
         soeg=["=kvinder"], pin_ialt=True),
    dict(id="le_gender_gap_naevner", navn="Middellevetid mænd", tabel="HISBK",
         soeg=["=mænd"], pin_ialt=True),

    # --- Sundhed/Velfærd: direkte platform-tal ---
    dict(id="life_expectancy", navn="Middellevetid", tabel="HISBK",
         soeg=["=i alt"], pin_ialt=True),
    dict(id="employment_taeller", navn="Beskæftigelsesfrekvens, i alt", tabel="RAS200",
         soeg=["=i alt"],
         ekstra=[{"soeg": ["beskæftigelsesfrekvens"]}, {"soeg": ["=16-64 år"]}], pin_ialt=True),
    dict(id="disposable_income", navn="Disponibel indkomst", tabel="INDKP101",
         soeg=["=mænd og kvinder i alt"],
         ekstra=[{"soeg": ["gennemsnit for alle personer"]},
                 {"soeg": ["=1 disponibel indkomst (2+30-31-32-35)"]}], pin_ialt=True),
    dict(id="commute_distance", navn="Pendlingsafstand", tabel="AFSTB4",
         soeg=["beskæftigede i alt"], pin_ialt=True),

    # --- Økologisk: næringsstoffer ---
    # Master normaliserer pr. 1.000 indbyggere (fetch_eco_new_data.py) - rå
    # VANDUD-tal er totaler i ton, derfor pr=1000 mod folketal.
    dict(id="naer_nitrogen", navn="Kvælstofudledning til vandmiljø", tabel="VANDUD",
         soeg=["kvælstof"], pr=1000),
    dict(id="naer_phosphorus", navn="Fosforudledning til vandmiljø", tabel="VANDUD",
         soeg=["fosfor"], pr=1000),

    # --- Økologisk: vand ---
    # Master bruger m³/person = mio_m³ × 1.000.000 / befolkning
    # (fetch_vandindvinding_data.py) - rå VANDIND-tal er totaler i mio. m³.
    dict(id="vandindvinding", navn="Vandindvinding, alment vandværk", tabel="VANDIND",
         soeg=["vand i alt"], ekstra=[{"soeg": ["alment vandværk"]}], pr=1_000_000),

    # --- Økologisk: arealanvendelse ---
    dict(id="areal_intensiv", navn="Intensivt landbrugsareal", tabel="AREALDK2",
         soeg=["intensivt landbrug (korn"], ekstra=[{"soeg": ["andel af samlet"]}], pin_ialt=True),
    dict(id="areal_bebygget", navn="Bebygget areal og infrastruktur", tabel="AREALDK2",
         soeg=["bebyggelse", "veje og jernbaner", "lufthavne", "sportsanlæg"],
         ekstra=[{"soeg": ["andel af samlet"]}], pin_ialt=True),

    # --- Økologisk: forurening (cirkularitet) ---
    dict(id="cirkularitet_waste", navn="Husholdningsaffald pr. person", tabel="LABY25",
         soeg=["kg. pr. indbygger"], pin_ialt=True),
    dict(id="cirkularitet_recycling", navn="Genanvendelse af husholdningsaffald", tabel="LABY25",
         soeg=["genanvend"], pin_ialt=True),
]

# Forhold: id_taeller / id_naevner slås sammen til platform-id, ratio = tæller/nævner*100
FORHOLD = {
    "hospital_short": ("hospital_short_taeller", "hospital_short_naevner"),
    "educated_staff": ("educated_staff_taeller", "educated_staff_naevner"),
    "low_education": ("low_education_taeller", "low_education_naevner"),
    "education": ("education_taeller", "education_naevner"),
    "neet": ("neet_taeller", "neet_naevner"),
    "vacant_housing": ("vacant_housing_taeller", "vacant_housing_naevner"),
    "gender_leadership": ("gender_leadership_taeller", "gender_leadership_naevner"),
    "income_gender_gap": ("income_gender_gap_taeller", "income_gender_gap_naevner"),
    "employment_origin_gap": ("employment_origin_gap_taeller", "employment_origin_gap_naevner"),
    "employment": ("employment_taeller", None),  # nævner er konstant 100 (allerede en frekvens)
    "hospital_long": ("hospital_long_taeller", "hospital_short_naevner"),
    "housing_no_wc": ("housing_no_wc_taeller", "housing_beboede_total"),
    "housing_no_bath": ("housing_no_bath_taeller", "housing_beboede_total"),
}

# Forskel (ikke forhold): kvinder minus mænd, ikke divideret
FORSKEL = {
    "le_gender_gap": ("le_gender_gap_taeller", "le_gender_gap_naevner"),
}

# Direkte platform-id'er der IKKE skal omregnes (allerede rå værdier fra SIMPLE)
DIREKTE = {
    "hjemsyg", "medicin", "laegekontakt", "boerneovervaeght", "class_size", "daycare_ratio",
    "vulnerable_children", "child_notifications", "poverty_relative", "child_poverty", "gini",
    "housing_area", "voter_turnout_national", "voter_turnout", "music_school", "library_use",
    "traffic_accidents", "crime_rate", "sports_facilities", "sports_membership", "sports_spending",
    "life_expectancy", "disposable_income", "commute_distance",
    "naer_nitrogen", "naer_phosphorus", "vandindvinding", "areal_intensiv", "areal_bebygget",
    "cirkularitet_waste", "cirkularitet_recycling",
    "kultur_spending", "civil_society", "low_income",
}


def fetch_dst_indicators() -> list[dict]:
    log("=" * 66)
    log(f"DST-historik, startet {datetime.now():%Y-%m-%d %H:%M}")
    log(f"{len(SIMPLE)} rå udtræk, {len(KOMMUNER)} kommuner, fra {FRA_AAR}")
    log("=" * 66)

    folk = serie(FOLKETAL)
    log(f"\nFolketal hentet for {len(folk)} kommune-år.\n")
    boern = serie(BOERNETAL)
    log(f"\nBørnetal 0-17 år hentet for {len(boern)} kommune-år.\n")

    raw: dict[str, dict] = {}
    fejlet = []
    for spec in SIMPLE:
        data = serie(spec)
        if not data:
            fejlet.append(spec["id"])
        raw[spec["id"]] = data

    ud = []

    def skriv(platform_id, per_kommune_aar):
        for (kode, aar), v in per_kommune_aar.items():
            ud.append({"kommune_kode": kode, "indicator_id": platform_id, "aar": aar, "vaerdi": v})

    # Direkte + normaliserede (pr-faktor)
    spec_by_id = {s["id"]: s for s in SIMPLE}
    for platform_id in DIREKTE:
        data = raw.get(platform_id)
        if not data:
            continue
        pr = spec_by_id[platform_id].get("pr")
        if pr:
            befolkning = boern if platform_id == "child_notifications" else folk
            normaliseret = {}
            for n, v in data.items():
                b = befolkning.get(n)
                if b:
                    normaliseret[n] = round(v / b * pr, 4)
            skriv(platform_id, normaliseret)
        else:
            skriv(platform_id, data)

    # Forhold (tæller/nævner*100), undtagen employment (nævner=None -> værdien ER frekvensen)
    for platform_id, (taeller_id, naevner_id) in FORHOLD.items():
        t = raw.get(taeller_id)
        if not t:
            log(f"FEJL: mangler tæller for {platform_id}, springes over.")
            continue
        if naevner_id is None:
            skriv(platform_id, t)
            continue
        n = raw.get(naevner_id)
        if not n:
            log(f"FEJL: mangler nævner for {platform_id}, springes over.")
            continue
        res = {}
        for k in set(t) & set(n):
            if n[k]:
                res[k] = round(t[k] / n[k] * 100, 4)
        skriv(platform_id, res)

    # Forskel (kvinder - mænd)
    for platform_id, (a_id, b_id) in FORSKEL.items():
        a, b = raw.get(a_id), raw.get(b_id)
        if not a or not b:
            log(f"FEJL: mangler data for {platform_id}, springes over.")
            continue
        res = {k: round(a[k] - b[k], 4) for k in set(a) & set(b)}
        skriv(platform_id, res)

    log("\n" + "=" * 66)
    log(f"DST-historik færdig. {len(fejlet)} rå udtræk fejlede: {fejlet}")
    return ud


# ══════════════════════════════════════════════════════════════════════════
# KLIMAREGNSKABET.DK - klimapaavirkning (territorial CO2, "Samlet" sektor)
# ══════════════════════════════════════════════════════════════════════════

def fetch_klimapaavirkning() -> list[dict]:
    log("\n" + "=" * 66)
    log("Klimaregnskabet.dk - klimapåvirkning (territorial CO2e/indb.)")
    log("=" * 66)

    ud = []
    mangler = 0
    for kode in sorted(KOMMUNER, key=int):
        for aar in KLIMA_AAR:
            u = KLIMAREGNSKABET_API + "?" + urllib.parse.urlencode(
                {"municipality": int(kode), "year": aar, "type": "Nøgletal"})
            anm = urllib.request.Request(u, headers={"x-api-key": KLIMAREGNSKABET_KEY,
                                                       "Accept": "application/json"})
            data = []
            for n in range(4):
                try:
                    with urllib.request.urlopen(anm, timeout=45, context=_ctx) as sv:
                        data = json.loads(sv.read()).get("data", [])
                    break
                except urllib.error.HTTPError as ex:
                    if ex.code in (429, 500, 502, 503, 504):
                        time.sleep(2 ** n)
                        continue
                    break
                except Exception:
                    time.sleep(2 ** n)
            if not data:
                mangler += 1
                continue
            traef = [x for x in data if x.get("type") == "Samlet CO2-udledning"
                     and x.get("sektor") == "Samlet" and x.get("enhed") == "Ton CO2e/indb."]
            if traef:
                ud.append({"kommune_kode": kode, "indicator_id": "klimapaavirkning",
                           "aar": str(aar), "vaerdi": round(sum(x["værdi"] for x in traef), 4)})
            time.sleep(0.15)
        log(f"  {KOMMUNER[kode]:20} færdig")

    log(f"\nKlimaregnskabet færdig: {len(ud)} kommune-år, {mangler} uden svar.")
    return ud


# ══════════════════════════════════════════════════════════════════════════
# UVM (api.uddannelsesstatistik.dk) - fuld historik i stedet for kun seneste
# år. fetch_udvidelse_data.py henter allerede disse fire nøgletal, men
# beholder kun det seneste skoleår (uvm_get_latest) - historikken ligger
# allerede i svaret, den bliver bare smidt væk. Her genbruges samme
# statistik-kald, men ALLE år gemmes i stedet for kun det seneste.
#
# apprenticeship (EUD/PRAK/SØG) er bevidst UDELADT: nøgletalsnavnet UVM
# forventer er ændret siden fetch_udvidelse_data.py blev skrevet - selv et
# enkelt-års opslag fejler nu ("Nøgletal ... kunne ikke findes"). Det er et
# fortilfælde for hele den indikator, ikke kun for historik, og løses ikke
# her - se ADVARSEL i loggen.
# ══════════════════════════════════════════════════════════════════════════

UVM_BASE = "https://api.uddannelsesstatistik.dk/Api/v1"
UVM_TOKEN = hent_noegle("UVM_API_TOKEN")

# Alias-udvidet navn→kode-mapping, så "Aarhus"/"Århus"-stavevarianter fra UVM
# også rammer, ligesom load_navn_to_kode() i fetch_udvidelse_data.py.
NAVN2KODE: dict[str, str] = {}
for _kode, _navn in KOMMUNER.items():
    NAVN2KODE[_navn] = _kode
    NAVN2KODE[_navn.replace("Å", "Aa").replace("å", "aa")] = _kode


def uvm_post(body: dict) -> list[dict]:
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    anm = urllib.request.Request(
        f"{UVM_BASE}/statistik", data=payload,
        headers={"Authorization": f"Bearer {UVM_TOKEN}",
                 "Content-Type": "application/json; charset=utf-8"})
    for n in range(4):
        time.sleep(PAUSE if n == 0 else PAUSE + 2 ** n)
        try:
            with urllib.request.urlopen(anm, timeout=60, context=_ctx) as sv:
                data = json.loads(sv.read().decode("utf-8"))
            return data if isinstance(data, list) else []
        except urllib.error.HTTPError as ex:
            if ex.code in (429, 500, 502, 503, 504):
                log(f"   (UVM svarede {ex.code}, venter og prøver igen)")
                continue
            log(f"   FEJL: UVM svarede {ex.code}: "
                f"{ex.read().decode('utf-8', 'ignore')[:200]}")
            return []
        except Exception as ex:
            log(f"   (UVM netværksfejl: {ex}, venter og prøver igen)")
            continue
    log("   FEJL: UVM svarede ikke efter flere forsøg.")
    return []


def _uvm_parse(s) -> float | None:
    if s is None:
        return None
    s = str(s).strip().rstrip("%").strip()
    if s in ("", "..", ".", "x", "X", "-", "nan"):
        return None
    try:
        return float(s.replace(".", "").replace(",", "."))
    except ValueError:
        return None


def _uvm_skoleaar_til_aar(periode: str) -> str | None:
    """'2019/2020' -> '2019'. Almindelige kalenderår ('2019') går igennem uændret."""
    m = re.match(r"(\d{4})", periode.strip())
    return m.group(1) if m else None


def uvm_serie(navn: str, body: dict, kom_key: str, aar_key: str,
              val_key: str) -> dict[tuple[str, str], float]:
    """
    Henter én UVM-indikators FULDE historik (ikke kun seneste år).

    Flere rækker pr. (kommune, år) GENNEMSNITTES altid. Det er det rigtige
    for wellbeing, hvor detaljeringen deler året op på trivselsindikatorer,
    og en nul-operation for de øvrige tre, hvor der kun er én række pr.
    kommune-år (verificeret: exam_grade 98×15, high_absence 98×6,
    youth_education 98×14 rækker). Tilføjes en indikator hvor flere rækker
    skal LÆGGES SAMMEN i stedet, skal den have sin egen sti her.
    """
    log(f"\n→ UVM: {navn}")
    rows = uvm_post(body)
    if not rows:
        log("   FEJL: intet svar fra UVM, springes over.")
        return {}

    grupper: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in rows:
        navn_kom = (row.get(kom_key) or "").strip()
        periode = (row.get(aar_key) or "").strip()
        val = _uvm_parse(row.get(val_key))
        if not navn_kom or not periode or val is None:
            continue
        aar = _uvm_skoleaar_til_aar(periode)
        if not aar or int(aar) < FRA_AAR:
            continue
        kode = NAVN2KODE.get(navn_kom)
        if not kode:
            continue
        grupper[(kode, aar)].append(val)

    ud = {k: round(sum(v) / len(v), 4) for k, v in grupper.items()}
    kommuner_dækket = len({k for k, _ in ud})
    log(f"   OK: {len(ud)} kommune-år, {kommuner_dækket} kommuner.")
    return ud


def fetch_uvm_historik() -> list[dict]:
    log("\n" + "=" * 66)
    log("UVM-historik (api.uddannelsesstatistik.dk)")
    log("=" * 66)

    serier = {
        "exam_grade": uvm_serie(
            "Karaktergennemsnit (GS/KARA/KARAGNS)",
            {"område": "GS", "emne": "KARA", "underemne": "KARAGNS",
             "nøgletal": ["Gennemsnit - Obl. prøver"],
             "detaljering": ["[Bopælskommune].[Bopælskommune]", "[Skoleår].[Skoleår]"],
             "side_størrelse": 20000},
            "[Bopælskommune].[Bopælskommune].[Bopælskommune]",
            "[Skoleår].[Skoleår].[Skoleår]", "Gennemsnit - Obl. prøver"),
        "high_absence": uvm_serie(
            "Elevfravær >10% (GS/ELEVFRAV/FRAVAAR)",
            {"område": "GS", "emne": "ELEVFRAV", "underemne": "FRAVAAR",
             "nøgletal": ["Over 10 procent"],
             "detaljering": ["[Institution].[Beliggenhedskommune]", "[Tid].[Skoleår]"],
             "side_størrelse": 20000},
            "[Institution].[Beliggenhedskommune].[Beliggenhedskommune]",
            "[Tid].[Skoleår].[Skoleår]", "Over 10 procent"),
        "wellbeing": uvm_serie(
            "Elevtrivsel (GS/TRIV/TRIVIND)",
            {"område": "GS", "emne": "TRIV", "underemne": "TRIVIND",
             "nøgletal": ["Indikatorsvar - Kommunetal"],
             "detaljering": ["[Institution].[Administrerende Kommune]", "[Skoleår].[Skoleår]",
                              "[Trivselsindikator].[Trivselsindikator]"],
             "side_størrelse": 40000},
            "[Institution].[Administrerende Kommune].[Administrerende Kommune]",
            "[Skoleår].[Skoleår].[Skoleår]", "Indikatorsvar - Kommunetal"),
        "youth_education": uvm_serie(
            "Ungdomsuddannelsesandel (GS/PROFMOD/PROFMOD)",
            {"område": "GS", "emne": "PROFMOD", "underemne": "PROFMOD",
             "nøgletal": ["Komp: Med mindst en ungdomsuddannelsekompetence"],
             "detaljering": ["[Bopælskommune].[Kommune]", "[År].[År]"],
             "side_størrelse": 5000},
            "[Bopælskommune].[Kommune].[Kommune]",
            "[År].[År].[År]", "Komp: Med mindst en ungdomsuddannelsekompetence"),
    }

    ud = []
    for platform_id, serie_data in serier.items():
        for (kode, aar), v in serie_data.items():
            ud.append({"kommune_kode": kode, "indicator_id": platform_id, "aar": aar, "vaerdi": v})

    log(f"\nUVM-historik færdig: {len(ud)} kommune-år i alt.")
    return ud


# ══════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════

def auto_build_trends():
    log("\n" + "=" * 55)
    log("AUTO-REBUILD af trend_indicators.csv")
    log("=" * 55)
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from build_trends_csv import auto_build_trends as _auto
        _auto()
    except Exception as e:
        log(f"✗ FEJL ved rebuild af trend-CSV: {e}")
        log("  Rådata er gemt OK. Kør manuelt: python3 scripts/build_trends_csv.py")


def main():
    kraev_noegle("KLIMAREGNSKABET_API_KEY", KLIMAREGNSKABET_KEY, KLIMA_HJAELP)
    kraev_noegle("UVM_API_TOKEN", UVM_TOKEN, UVM_HJAELP)

    alle = fetch_dst_indicators() + fetch_klimapaavirkning() + fetch_uvm_historik()

    if not alle:
        log("\nFEJL: ingen data hentet overhovedet.")
        return 1

    DATA_DIR.mkdir(exist_ok=True)
    with open(RAW_OUTPUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["kommune_kode", "indicator_id", "aar", "vaerdi"])
        w.writeheader()
        w.writerows(sorted(alle, key=lambda r: (r["indicator_id"], r["kommune_kode"], r["aar"])))
    log(f"\nSkrevet: {RAW_OUTPUT.name} ({len(alle)} rækker)")

    dækning = defaultdict(set)
    for r in alle:
        dækning[r["indicator_id"]].add(r["kommune_kode"])
    log("\nDækning pr. indikator (antal kommuner med mindst ét år):")
    for iid in sorted(dækning):
        log(f"  {iid:28} {len(dækning[iid])}/{len(KOMMUNER)} kommuner")

    LOG_OUTPUT.write_text("\n".join(LOG), encoding="utf-8")
    log(f"\nSkrevet: {LOG_OUTPUT.name}")

    auto_build_trends()
    return 0


if __name__ == "__main__":
    sys.exit(main())
