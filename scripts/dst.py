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
