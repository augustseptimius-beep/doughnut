"""
dst.py - fælles kald til Danmarks Statistiks StatBank-API.

Indtil sep. 2026 havde seks fetch-scripts hver sin kopi af api_post() og
parse_value(). Kopierne var ens bortset fra docstrings og en timeout, men en
rettelse (fx af hvordan DST's ".." for manglende værdier læses) skulle laves
seks steder.

Brug:
    from dst import api_post, parse_value
    rows = api_post("FOLK1A", [{"code": "OMRÅDE", "values": ["*"]}, ...])

Årstal slås op med scripts/dst_aar.py, ikke her.

Samme tal til score og retningspil (sep. 2026)
----------------------------------------------
En indikator med retningspil hentes af én funktion, serie_<id>(perioder), i
sit fetch-script. Scoren kalder den med den nyeste periode, og
fetch_trend_history.py kalder den med alle perioder. Før hentede de to spor
hver sin definition, og pilen beskrev i flere tilfælde et andet tal end
scoren (fx klassekvotient i folkeskolen mod alle skoletyper). Hjælperne her
er det de funktioner har til fælles: summering pr. kommune og år, folketal
pr. 1. januar i samme år, og valg af nyeste år med data.
"""

from __future__ import annotations

import csv
import io
import json
import time
import urllib.request

API_URL = "https://api.statbank.dk/v1/data"
REQUEST_DELAY = 0.7  # sekunder mellem kald, så DST ikke afviser os


def api_post(table: str, variables: list[dict], timeout: int = 90) -> list[dict]:
    """Henter en tabel som CSV med koder (ikke tekster) og returnerer rækkerne.

    variables er DST's variabelselektion, fx
    [{"code": "OMRÅDE", "values": ["*"]}, {"code": "Tid", "values": ["2024"]}].
    Kolonnenavnene i resultatet er variabelkoderne plus "INDHOLD"."""
    payload = json.dumps({
        "table": table,
        "format": "CSV",
        "lang": "da",
        "valuePresentation": "Code",
        "variables": variables,
    }).encode("utf-8")
    req = urllib.request.Request(API_URL, data=payload, headers={"Content-Type": "application/json"})
    time.sleep(REQUEST_DELAY)
    resp = urllib.request.urlopen(req, timeout=timeout)
    content = resp.read().decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(content), delimiter=";"))


def parse_value(raw: str) -> float | None:
    """DST-værdi som tal. DST skriver manglende eller diskretionerede værdier
    som "..", ".", "x" eller "-"; de bliver None. Tusindtals-punktum og
    decimalkomma håndteres."""
    raw = raw.strip()
    if raw in ("", "..", ".", "x", "X", "-"):
        return None
    try:
        return float(raw.replace(".", "").replace(",", "."))
    except ValueError:
        return None


def pr_kommune_aar(rows: list[dict], omraade: str = "OMRÅDE") -> dict[tuple[str, str], float]:
    """{(kommune_kode, år): sum af INDHOLD} for platformens 98 kommuner og hele
    landet (000). Året er slutåret for perioder ('2025K3' og '2024:2025' giver
    '2025'), og rækker med samme kommune og år lægges sammen - fx de fire
    kvartaler i STRAF11. Har tabellen flere rækker pr. kommune og år, som IKKE
    skal lægges sammen, skal kaldet vælge én værdi pr. variabel."""
    from dst_aar import aarstal
    from kommuner import KODER
    ud: dict[tuple[str, str], float] = {}
    for row in rows:
        kode = (row.get(omraade) or "").strip()
        if kode != "000" and kode not in KODER:
            continue
        val = parse_value(row.get("INDHOLD", ""))
        if val is None:
            continue
        noegle = (kode, aarstal((row.get("TID") or "").strip()))
        ud[noegle] = ud.get(noegle, 0.0) + val
    return ud


def folketal(aar: list[str], alder: list[str] | None = None) -> dict[tuple[str, str], float]:
    """Folketal 1. januar (FOLK1A, K1) i hvert af årene, {(kommune_kode, år): antal}
    inkl. hele landet (000). `alder` er FOLK1A's ALDER-koder ('0'..'17' for
    børn); uden den hele befolkningen.

    Et tal pr. indbygger for år Y deles med befolkningen 1. januar Y. Indtil
    sep. 2026 delte scoren med det nyeste K1 uanset hvilket år tallet gjaldt,
    mens retningspilen brugte samme år - derfor passede de ikke sammen."""
    from dst_aar import perioder
    findes = set(perioder("FOLK1A"))
    tider = [f"{a}K1" for a in sorted(set(aar)) if f"{a}K1" in findes]
    if not tider:
        return {}
    rows = api_post("FOLK1A", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "KØN", "values": ["TOT"]},
        {"code": "ALDER", "values": alder or ["IALT"]},
        {"code": "Tid", "values": tider},
    ])
    return pr_kommune_aar(rows)


def pr_indbygger(taeller: dict[tuple[str, str], float], faktor: float, decimaler: int,
                 alder: list[str] | None = None) -> dict[tuple[str, str], float]:
    """Tæller pr. `faktor` indbyggere (1.000, 100.000 ...) med folketallet 1. januar
    samme år, se folketal(). Kommune-år uden folketal udelades."""
    folk = folketal(sorted({a for _, a in taeller}), alder)
    return {(k, a): round(v / folk[(k, a)] * faktor, decimaler)
            for (k, a), v in taeller.items() if folk.get((k, a))}


def seneste(serie: dict[tuple[str, str], float], min_kommuner: int = 50,
            tabel: str | None = None) -> tuple[str | None, dict[str, float], float | None]:
    """Nyeste år i serien hvor mindst `min_kommuner` kommuner har en værdi.

    Returnerer (år, {kommune_kode: værdi}, landstal) - landstallet er hele
    landet (000), hvis serien har det. Et halvfærdigt nyeste år (fx kun
    enkelte kommuner indberettet) springes over i stedet for at give huller.
    Med `tabel` noteres det valgte år i data/data_years.json, så årstallet på
    sitet er det år der faktisk blev brugt, ikke bare tabellens nyeste."""
    for aar in sorted({a for _, a in serie}, reverse=True):
        vaerdier = {k: v for (k, a), v in serie.items() if a == aar and k != "000"}
        if len(vaerdier) >= min_kommuner:
            if tabel:
                from dst_aar import registrer_aar
                registrer_aar(tabel, aar)
            return aar, vaerdier, serie.get(("000", aar))
    return None, {}, None
