#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
indkomst_median.py - fælles hjælper: median disponibel indkomst pr. kommune
og køn, beregnet ud fra DST INDKP106.

Hvorfor den findes
------------------
disposable_income og income_gender_gap byggede på GENNEMSNITLIG disponibel
indkomst (INDKP101, ENHED 116). Et gennemsnit flyttes af få meget høje
indkomster: i Vejen steg kvindernes gennemsnit fra 217.000 kr. (2022) til
438.000 kr. (2023), så kommunen fik topscore på ligestilling, fordi kvinderne
"tjente" 142 % af mændene. Medianen er upåvirket af den slags.

DST udgiver ikke medianen pr. kommune og køn. INDKP106 har til gengæld antal
personer (15 år+) i hvert indkomstinterval pr. kommune og køn. Medianen findes
ved lineær interpolation i det interval hvor den kumulerede andel passerer
50 % (gruppert median). Intervallerne er 25.000 kr. brede op til 250.000 kr.
og 50.000 kr. brede derover, så fejlen er højst en brøkdel af intervalbredden.

Brug:

    from indkomst_median import median_disponibel
    med = median_disponibel(["2024"], ["MOK"])   # {(kode, "MOK", "2024"): kr}

Kode "000" er hele landet og bruges som reference i ratioen.
"""

from __future__ import annotations

import csv
import io
import json
import re
import ssl
import time
import urllib.request

TABEL = "INDKP106"
API_DATA = "https://api.statbank.dk/v1/data"
API_INFO = "https://api.statbank.dk/v1/tableinfo/INDKP106?lang=da&format=JSON"
_ctx = ssl.create_default_context()


def _intervalgraenser() -> dict[str, tuple[float, float | None]]:
    """Kode -> (nedre, øvre) i kr. ud fra tabellens egne intervaltekster.

    Teksterne læses fra DST frem for at blive hårdkodet, så en ændret
    inddeling giver en fejl i stedet for et tavst forkert tal.
    """
    req = urllib.request.Request(API_INFO, headers={"User-Agent": "DoughnutDK/1.0"})
    with urllib.request.urlopen(req, timeout=45, context=_ctx) as r:
        info = json.loads(r.read().decode("utf-8"))
    var = next(v for v in info["variables"] if v["id"] == "INDKINTB")
    graenser: dict[str, tuple[float, float | None]] = {}
    for v in var["values"]:
        kode, tekst = v["id"], v["text"].lower()
        tal = [float(t.replace(".", "")) for t in re.findall(r"\d[\d.]*", tekst)]
        if kode == "000":
            continue                                   # "Alle"
        if tekst.startswith("under") and len(tal) == 1:
            graenser[kode] = (0.0, tal[0])             # inkl. negative indkomster
        elif "derover" in tekst and len(tal) == 1:
            graenser[kode] = (tal[0], None)            # åbent øverste interval
        elif len(tal) == 2:
            graenser[kode] = (tal[0], tal[1] + 1)      # "25.000 - 49.999" -> [25000, 50000)
        else:
            raise ValueError(f"Ukendt intervaltekst i {TABEL}: {v['text']!r}")
    return graenser


def _hent(aar: list[str], koen: list[str]) -> list[dict]:
    payload = json.dumps({
        "table": TABEL, "format": "CSV", "lang": "da", "valuePresentation": "Code",
        "variables": [
            {"code": "OMRÅDE", "values": ["*"]},
            {"code": "ENHED", "values": ["103"]},      # personer i gruppen (antal)
            {"code": "KOEN", "values": koen},
            {"code": "ALDER1", "values": ["00"]},      # alle aldre (15 år+)
            {"code": "INDKINTB", "values": ["*"]},
            {"code": "Tid", "values": aar},
        ],
    }).encode("utf-8")
    req = urllib.request.Request(API_DATA, data=payload,
                                 headers={"Content-Type": "application/json"})
    time.sleep(0.5)
    with urllib.request.urlopen(req, timeout=120, context=_ctx) as r:
        tekst = r.read().decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(tekst), delimiter=";"))


def grupperet_median(antal: dict[str, float],
                     graenser: dict[str, tuple[float, float | None]]) -> float | None:
    """Median ved lineær interpolation i det interval der rummer 50 %-punktet."""
    intervaller = sorted((graenser[k][0], graenser[k][1], n)
                         for k, n in antal.items() if k in graenser)
    total = sum(n for _, _, n in intervaller)
    if total <= 0:
        return None
    halvdel = total / 2
    kum = 0.0
    for nedre, oevre, n in intervaller:
        if n > 0 and kum + n >= halvdel:
            if oevre is None:
                return None                            # median i åbent interval: kan ikke bestemmes
            return round(nedre + (halvdel - kum) / n * (oevre - nedre))
        kum += n
    return None


def median_disponibel(aar: list[str], koen: list[str]) -> dict[tuple[str, str, str], float]:
    """{(områdekode, køn, år): median disponibel indkomst i kr.} for alle områder."""
    graenser = _intervalgraenser()
    fordeling: dict[tuple[str, str, str], dict[str, float]] = {}
    # Et år ad gangen holder hvert kald et godt stykke under DST's cellegrænse.
    for a in aar:
        for row in _hent([a], koen):
            v = row.get("INDHOLD", "").strip()
            if v in ("", "..", "."):
                continue
            noegle = (row["OMRÅDE"].strip(), row["KOEN"].strip(), row["TID"].strip())
            fordeling.setdefault(noegle, {})[row["INDKINTB"].strip()] = float(v)
    ud = {}
    for noegle, antal in fordeling.items():
        m = grupperet_median(antal, graenser)
        if m is not None:
            ud[noegle] = m
    return ud


if __name__ == "__main__":
    import sys
    aar = sys.argv[1:] or ["2024"]
    med = median_disponibel(aar, ["MOK", "M", "K"])
    for kode in ("000", "575", "787"):
        for a in aar:
            print(kode, a, {k: med.get((kode, k, a)) for k in ("MOK", "M", "K")})
