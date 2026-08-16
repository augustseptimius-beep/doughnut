#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dst_aar.py - fælles hjælper: find NYESTE tilgængelige år i en DST-tabel.

Hvorfor den findes
------------------
Fetch-scripterne hårdkodede tidligere årstal ({"code": "Tid", "values": ["2023"]}).
Det er den enkeltårsag der har holdt flest indikatorer forældede: scriptet kan
køres igen og igen og henter trofast det samme gamle år, så det ser ud som om
alt virker. Diagnosen aug. 2026 fandt 12 indikatorer i den tilstand - og
voter_turnout stod på kommunalvalget 2021 fire år efter.

Brug i stedet:

    from dst_aar import seneste_aar
    aar = seneste_aar("BOL106")                 # fx "2026"
    rows = api_post("BOL106", [..., {"code": "Tid", "values": [aar]}])

Resultatet caches pr. proceskørsel, så mange indikatorer fra samme tabel kun
koster ét ekstra kald.

Kør fra projektets rodmappe som resten af pipelinen.
"""

from __future__ import annotations

import json
import re
import ssl
import urllib.request
from pathlib import Path

DST_TABELINFO = "https://api.statbank.dk/v1/tableinfo/{}?lang=da&format=JSON"
_ctx = ssl.create_default_context()
_cache: dict[str, list[str]] = {}

# Kvittering for hvilket år en tabel FAKTISK blev hentet på.
# build_master_csv.py læser filen og bruger den frem for sit eget hårdkodede
# data_year. Uden den opstår den fejl vi ryddede op i aug. 2026: masteren
# mærkede 2024-tal som 2022, fordi label og hentning levede hver sit sted.
AAR_REGISTER = Path(__file__).resolve().parent.parent / "data" / "data_years.json"

# Sættes af __main__ nedenfor: et diagnostisk opslag må ikke skrive i registret,
# for så kommer master til at påstå et år ingen fetch faktisk har hentet.
_SKRIV_IKKE = False


def _aarstal(periode: str) -> str:
    """
    Årstallet en periode repræsenterer.

    DST bruger flere formater: "2025", "2025K3" og 5-års-intervaller som
    "2021:2025" (fx HISBK middellevetid). For et interval er det SLUTåret der
    beskriver hvor nyt tallet er - tager man startåret, kommer indikatoren til
    at se fire år ældre ud end den er.
    """
    p = str(periode)
    if ":" in p:
        dele = [d for d in p.split(":") if re.match(r"^\d{4}$", d)]
        if dele:
            return dele[-1]
    m = re.match(r"\d{4}", p)
    return m.group(0) if m else p


def registrer_aar(tabel: str, aar: str) -> None:
    """Noterer at `tabel` blev hentet på `aar`. Fejler aldrig kørslen."""
    if _SKRIV_IKKE:
        return
    aar = _aarstal(aar)
    try:
        d = {}
        if AAR_REGISTER.exists():
            d = json.loads(AAR_REGISTER.read_text(encoding="utf-8"))
        if d.get(tabel) == str(aar):
            return
        d[tabel] = str(aar)
        AAR_REGISTER.parent.mkdir(exist_ok=True)
        AAR_REGISTER.write_text(
            json.dumps(dict(sorted(d.items())), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
    except Exception as e:
        print(f"  ADVARSEL: kunne ikke registrere år for {tabel}: {e}")


def hentede_aar() -> dict[str, str]:
    """Læser registret. Tom dict hvis filen ikke findes endnu."""
    try:
        if AAR_REGISTER.exists():
            return json.loads(AAR_REGISTER.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _perioder(tabel: str) -> list[str]:
    """Alle perioder i tabellen, sorteret stigende. Caches pr. kørsel."""
    if tabel in _cache:
        return _cache[tabel]
    req = urllib.request.Request(DST_TABELINFO.format(tabel),
                                 headers={"User-Agent": "DoughnutDK/1.0"})
    with urllib.request.urlopen(req, timeout=45, context=_ctx) as resp:
        info = json.loads(resp.read().decode("utf-8"))
    tid = next((v for v in info["variables"] if v.get("time")), None)
    perioder = sorted(str(x["id"]) for x in tid["values"]) if tid else []
    _cache[tabel] = perioder
    return perioder


def seneste_aar(tabel: str, fallback: str | None = None) -> str:
    """
    Nyeste ÅR (4 cifre) i tabellen, som streng.

    Kvartals-/månedstabeller (fx "2025K3") reduceres til årstallet. Vil man
    have selve perioden, så brug seneste_periode().

    fallback bruges kun hvis DST ikke svarer - så fejler en enkelt indikator
    frem for hele kørslen. Undlad den hvis du hellere vil se fejlen.
    """
    try:
        perioder = _perioder(tabel)
        aar = [m.group(0) for p in perioder if (m := re.match(r"\d{4}", p))]
        if aar:
            registrer_aar(tabel, max(aar))
            return max(aar)
    except Exception as e:
        print(f"  ADVARSEL: kunne ikke slå seneste år op for {tabel}: {e}")
    if fallback:
        print(f"  Bruger fallback-år {fallback} for {tabel}")
        return fallback
    raise RuntimeError(f"Kunne ikke bestemme seneste år for {tabel}")


def seneste_periode(tabel: str, fallback: str | None = None) -> str:
    """Nyeste PERIODE som den står i tabellen (fx '2025K3' eller '2026')."""
    try:
        perioder = _perioder(tabel)
        if perioder:
            registrer_aar(tabel, perioder[-1])
            return perioder[-1]
    except Exception as e:
        print(f"  ADVARSEL: kunne ikke slå seneste periode op for {tabel}: {e}")
    if fallback:
        return fallback
    raise RuntimeError(f"Kunne ikke bestemme seneste periode for {tabel}")


def seneste_aar_liste(tabel: str, antal: int = 3,
                      fallback: list[str] | None = None) -> list[str]:
    """
    De `antal` nyeste år, NYESTE FØRST - fx ["2026", "2025", "2024"].

    Til de scripts der beder om flere år og selv vælger det nyeste med data
    pr. kommune. Mønsteret er fornuftigt, men listen var hårdkodet og fulgte
    derfor ikke med når DST lagde et nyt år op.
    """
    try:
        perioder = _perioder(tabel)
        aar = sorted({m.group(0) for p in perioder if (m := re.match(r"\d{4}", p))},
                     reverse=True)
        if aar:
            registrer_aar(tabel, aar[0])
            return aar[:antal]
    except Exception as e:
        print(f"  ADVARSEL: kunne ikke slå årsliste op for {tabel}: {e}")
    if fallback:
        return fallback
    raise RuntimeError(f"Kunne ikke bestemme årsliste for {tabel}")


def seneste_kvartal(tabel: str, kvartal: str = "K1",
                    fallback: str | None = None) -> str:
    """
    Nyeste periode med et BESTEMT kvartal, fx '2026K1'.

    Bestandstal som FOLK1A opgøres pr. kvartal, og platformen bruger
    konsekvent K1 (1. januar). Tager man bare den absolut nyeste periode,
    skifter man umærkeligt opgørelsestidspunkt fra 1. januar til fx 1. juli,
    og så er befolkningstallet ikke længere sammenligneligt med de historiske
    tal i trend-sporet (som vælger K1, se vaelg_tid i fetch_trend_history.py).
    """
    try:
        perioder = _perioder(tabel)
        traef = [p for p in perioder if p.endswith(kvartal)]
        if traef:
            valgt = max(traef)
            registrer_aar(tabel, valgt[:4])
            return valgt
    except Exception as e:
        print(f"  ADVARSEL: kunne ikke slå seneste {kvartal} op for {tabel}: {e}")
    if fallback:
        return fallback
    raise RuntimeError(f"Kunne ikke bestemme seneste {kvartal} for {tabel}")


def hele_aar_kvartaler(tabel: str) -> tuple[str, list[str]]:
    """
    Nyeste år hvor ALLE fire kvartaler findes, plus kvartalslisten.

    Til tabeller som STRAF11 hvor et årstal skal summeres af kvartaler - et
    halvfærdigt år ville ellers give et kunstigt lavt tal.
    """
    perioder = _perioder(tabel)
    pr_aar: dict[str, list[str]] = {}
    for p in perioder:
        m = re.fullmatch(r"(\d{4})K([1-4])", p)
        if m:
            pr_aar.setdefault(m.group(1), []).append(p)
    hele = [a for a, ks in pr_aar.items() if len(ks) == 4]
    if not hele:
        raise RuntimeError(f"{tabel}: fandt intet år med fire hele kvartaler")
    aar = max(hele)
    registrer_aar(tabel, aar)
    return aar, sorted(pr_aar[aar])


if __name__ == "__main__":
    import sys
    _SKRIV_IKKE = True   # rent opslag - rør ikke data_years.json
    for t in sys.argv[1:] or ["BOL106", "SBR01", "STRAF11", "IDRFAC01"]:
        try:
            print(f"{t:12} seneste år={seneste_aar(t):8} periode={seneste_periode(t)}")
        except Exception as e:
            print(f"{t:12} FEJL: {e}")
