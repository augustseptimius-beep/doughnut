#!/usr/bin/env python3
"""
statbank_fetcher.py
Henter doughnut-indikatorer for danske kommuner fra Danmarks Statistiks API.

Brug:
  python statbank_fetcher.py 787              # Én kommune (Thisted)
  python statbank_fetcher.py 787 461 751      # Flere kommuner
  python statbank_fetcher.py --alle           # Alle 98 kommuner
  python statbank_fetcher.py --test           # Test med Thisted uden at gemme

OBS: Ikke en del af datapipelinen. Scriptet skriver doughnut_data.json, som
hverken build_master_csv.py eller webappen læser, og det bruger gennemsnitlig
indkomst (INDKP101), hvor platformen bruger medianen (CLAUDE.md pkt. 29).
Beholdt som opslagsværktøj for enkelte kommuner.
"""

from __future__ import annotations  # kræves: maskinen kører Python 3.9,
# hvor 'float | None' i en signatur ellers fejler ved import (TypeError).

import requests
import csv
import json
import time
import sys
from io import StringIO
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kommuner import KOMMUNER  # noqa: E402  (de 98 kommuner, data/kommuner.json)

BASE_URL = "https://api.statbank.dk/v1/data"
REQUEST_DELAY = 0.6  # sekunder mellem kald (respekter rate limit)


# ---------------------------------------------------------------------------
# API-klient
# ---------------------------------------------------------------------------

def fetch_csv(table_id: str, params: dict) -> list[dict]:
    """
    Henter data fra Statbank som semikolon-separeret CSV.
    Returnerer liste af dicts (én dict per række).
    Kaster requests.HTTPError ved API-fejl.
    """
    url = f"{BASE_URL}/{table_id}/CSV"
    full_params = {"lang": "da", **params}

    time.sleep(REQUEST_DELAY)

    resp = requests.get(url, params=full_params, timeout=30)
    resp.raise_for_status()
    resp.encoding = "utf-8"

    reader = csv.DictReader(StringIO(resp.text), delimiter=";")
    return list(reader)


def extract_value(rows: list[dict]) -> float | None:
    """
    Udtrækker den numeriske INDHOLD-værdi fra første CSV-række.
    Statbank returnerer altid tallene i kolonnen 'INDHOLD'.
    """
    if not rows:
        return None
    first = rows[0]
    raw = first.get("INDHOLD", "")
    if raw in ("", "..", "x", "X"):
        return None
    try:
        return float(raw.replace(".", "").replace(",", "."))
    except ValueError:
        return None


def make_indicator(tabel, dimension, indikator, rows, enhed, periode):
    """Hjælpefunktion: pakker et resultat ind i standardformat."""
    return {
        "tabel": tabel,
        "dimension": dimension,
        "indikator": indikator,
        "værdi": extract_value(rows),
        "enhed": enhed,
        "periode": periode,
    }


# ---------------------------------------------------------------------------
# Individuelle indikatorer
# ---------------------------------------------------------------------------

def fetch_befolkning(kode: str) -> dict:
    """FOLK1A - Folketal (baseline til pr-capita-normalisering)"""
    rows = fetch_csv("FOLK1A", {
        "OMRÅDE": kode, "KØN": "TOT",
        "ALDER": "IALT", "CIVILSTAND": "TOT", "Tid": "2025K4",
    })
    return make_indicator("FOLK1A", "baseline", "Befolkningstal", rows, "personer", "2025K4")


def fetch_indkomst(kode: str) -> dict:
    """INDKP101 - Gennemsnitlig disponibel indkomst per person"""
    rows = fetch_csv("INDKP101", {
        "OMRÅDE": kode, "KOEN": "MOK",
        "INDKOMSTTYPE": "100",  # Disponibel indkomst
        "ENHED": "116",          # Gennemsnit alle personer (kr.)
        "Tid": "2023",
    })
    return make_indicator("INDKP101", "indkomst_arbejde", "Gns. disponibel indkomst", rows, "kr.", "2023")


def fetch_offentlig_forsorget(kode: str) -> dict:
    """AUK01 - Offentligt forsørgede, fuldtidsmodtagere i alt"""
    rows = fetch_csv("AUK01", {
        "OMRÅDE": kode, "YDELSESTYPE": "TOT",
        "KØN": "TOT", "ALDER": "TOT", "Tid": "2024K4",
    })
    return make_indicator("AUK01", "indkomst_arbejde", "Offentligt forsørgede (fuldtid)", rows, "fuldtidsmodtagere", "2024K4")


def fetch_uddannelse_lvu(kode: str) -> dict:
    """HFUDD11 - Antal personer med lang videregående uddannelse (LVU)"""
    rows = fetch_csv("HFUDD11", {
        "BOPOMR": kode, "HERKOMST": "TOT",
        "HFUDD": "H70",  # Lang videregående uddannelse
        "ALDER": "TOT", "KØN": "TOT", "Tid": "2024",
    })
    return make_indicator("HFUDD11", "uddannelse", "Antal med LVU", rows, "personer", "2024")


def fetch_uddannelse_grundskole(kode: str) -> dict:
    """HFUDD11 - Antal med grundskole som højeste uddannelse"""
    rows = fetch_csv("HFUDD11", {
        "BOPOMR": kode, "HERKOMST": "TOT",
        "HFUDD": "H10",  # Grundskole
        "ALDER": "TOT", "KØN": "TOT", "Tid": "2024",
    })
    return make_indicator("HFUDD11", "uddannelse", "Antal med kun grundskole", rows, "personer", "2024")


def fetch_neet(kode: str) -> dict:
    """NEET1 - Unge 16-24 år uden for uddannelse og beskæftigelse"""
    rows = fetch_csv("NEET1", {
        "BOPOMR": kode, "STATUSNEET": "10",  # Ikke-aktive (NEET)
        "KØN": "TOT", "SOCIO": "TOT", "Tid": "2023",
    })
    return make_indicator("NEET1", "uddannelse", "Unge i NEET (16-24 år)", rows, "personer", "2023")


def fetch_fattigdom(kode: str) -> dict:
    """LABY07 - Andel i relativ fattigdom"""
    rows = fetch_csv("LABY07", {
        "KOMGRP": kode, "ALDER": "IALT", "Tid": "2023",
    })
    return make_indicator("LABY07", "indkomst_arbejde", "Andel i relativ fattigdom", rows, "pct.", "2023")


def fetch_affald(kode: str) -> dict:
    """LABY25 - Husholdningsaffald, kg per indbygger"""
    rows = fetch_csv("LABY25", {
        "KOMGRP": kode, "BNØGLE": "AFFALDIND", "Tid": "2023",
    })
    return make_indicator("LABY25", "materialer", "Husholdningsaffald", rows, "kg/indbygger", "2023")


def fetch_genanvendelse(kode: str) -> dict:
    """LABY25 - Andel husholdningsaffald til genanvendelse"""
    rows = fetch_csv("LABY25", {
        "KOMGRP": kode, "BNØGLE": "GENPCT", "Tid": "2023",
    })
    return make_indicator("LABY25", "materialer", "Affald til genanvendelse", rows, "pct.", "2023")


# ---------------------------------------------------------------------------
# Samlet kald per kommune
# ---------------------------------------------------------------------------

INDIKATORER = [
    fetch_befolkning,
    fetch_indkomst,
    fetch_offentlig_forsorget,
    fetch_uddannelse_lvu,
    fetch_uddannelse_grundskole,
    fetch_neet,
    fetch_fattigdom,
    fetch_affald,
    fetch_genanvendelse,
]


def fetch_kommune(kode: str, verbose: bool = True) -> dict:
    """Henter alle doughnut-indikatorer for én kommune."""
    navn = KOMMUNER.get(kode, f"Ukendt ({kode})")
    if verbose:
        print(f"\n→ {navn} [{kode}]")

    resultater = []
    for fn in INDIKATORER:
        try:
            r = fn(kode)
            resultater.append(r)
            if verbose:
                v = r["værdi"]
                status = f"{v:,.0f} {r['enhed']}" if v is not None else "ingen data"
                print(f"  {'✓' if v is not None else '?'} {r['indikator']}: {status}")
        except Exception as e:
            fejl = {"tabel": fn.__name__, "fejl": str(e)}
            resultater.append(fejl)
            if verbose:
                print(f"  ✗ {fn.__name__}: {e}")

    return {
        "kommune_kode": kode,
        "kommune_navn": navn,
        "hentet": datetime.now().isoformat(),
        "indikatorer": resultater,
    }


def fetch_alle(output_fil: str = "doughnut_data.json") -> None:
    """Henter data for alle 98 kommuner og gemmer som JSON."""
    print(f"Henter data for {len(KOMMUNER)} kommuner...")
    alle = {}

    for kode in KOMMUNER:
        try:
            alle[kode] = fetch_kommune(kode, verbose=True)
        except Exception as e:
            print(f"  FEJL for {kode}: {e}")
        time.sleep(0.5)  # ekstra pause mellem kommuner

    Path(output_fil).write_text(
        json.dumps(alle, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nFærdigt. Data gemt i {output_fil}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or "--hjælp" in args or "--help" in args:
        print(__doc__)
        sys.exit(0)

    if "--alle" in args:
        fetch_alle()
    elif "--test" in args:
        # Test med Thisted - printer output, gemmer ikke
        data = fetch_kommune("787")
        print("\n" + json.dumps(data, ensure_ascii=False, indent=2))
    else:
        # Hent specifikke kommuner
        resultater = {}
        for kode in args:
            if kode not in KOMMUNER:
                print(f"Ukendt kommunekode: {kode}. Gyldige koder: {', '.join(sorted(KOMMUNER))}")
                continue
            resultater[kode] = fetch_kommune(kode)

        print("\n" + json.dumps(resultater, ensure_ascii=False, indent=2))
