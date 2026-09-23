#!/usr/bin/env python3
"""
fetch_dst_arealanvendelse.py - Arealanvendelse pr. danske kommune (DST AREALDK2)
=================================================================================
Henter arealdækningsdata fra Danmarks Statistiks Statistikbank (AREALDK2, nyeste år).
Ingen GIS eller spatial join - ren API.

Tre sub-indikatorer pr. kommune:
  1. natur_pct       = skov + lysåben natur + søer (E + F1 + F2 + G1)
  2. intensiv_pct    = intensivt landbrug (D1 + D2 + D4)
  3. bebygget_pct    = veje + lufthavne + bebyggelse + råstof (A1 + A2 + B1 + B2 + C1)

Ratio-logik (eco-konvention: >100 = overshoot):
  natur_ratio    = (30 / natur_pct) * 100  [grænse: 30% EU 30x30-mål]
  intensiv_ratio = (intensiv_pct / NATIONAL_AVG_INTENSIV) * 100  [grænse: nationalt snit]
  bebygget_ratio = (bebygget_pct / NATIONAL_AVG_BEBYGGET) * 100  [grænse: nationalt snit]

De nationale gennemsnit hentes fra DST (OMRÅDE=95, hele landet) for samme år.
Scriptet skriver dem i areal_intensiv_ref og areal_bebygget_ref.

serie_areal_intensiv() og serie_areal_bebygget() bruges også af
fetch_trend_history.py, så retningspilen følger samme kategorier som scoren
(indtil sep. 2026 talte pilen fx sportsanlæg med i bebygget og ikke
ikke-klassificeret landbrug med i intensivt).

Output:
  data/arealanvendelse_scores.csv

Kilde:
  Danmarks Statistik AREALDK2 - https://www.statistikbanken.dk/AREALDK2

Brug:
  cd /sti/til/doughnut
  python3 scripts/fetch_dst_arealanvendelse.py
"""

from __future__ import annotations  # kræves: maskinen kører Python 3.9,
# hvor 'float | None' i en signatur ellers fejler ved import (TypeError).

import csv
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kommuner import KOMMUNER  # noqa: E402  (de 98 kommuner, data/kommuner.json)
from dst import api_post, parse_value, pr_kommune_aar, seneste  # noqa: E402  (fælles DST-kald)
from dst_aar import aarstal, seneste_aar_liste  # noqa: E402

# ─── Stier ───────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "arealanvendelse_scores.csv"

# ─── Arealkategorier (AREALDK2, variablen ARE1) ──────────────────────────────
NATUR_KODER    = ["E", "F1", "F2", "G1"]          # skov, lysåben natur, søer
INTENSIV_KODER = ["D1", "D2", "D4"]               # intensivt landbrug + ikke-klassificeret
BEBYGGET_KODER = ["A1", "A2", "B1", "B2", "C1"]   # veje, lufthavne, bebyggelse, råstof

HELE_LANDET = "95"     # AREALDK2's kode for hele landet
NATUR_GRÆNSE = 30.0    # EU 30x30-mål 2030 (%)


def _serie_andel(koder: list[str], aar: list[str]) -> dict[tuple[str, str], float]:
    """Summen af ARE1-kategoriernes andel af kommunens samlede areal (pct.),
    {(kommune_kode, år): pct} inkl. hele landet som '000'."""
    rows = api_post("AREALDK2", [
        {"code": "ARE1", "values": koder},
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "ENHED", "values": ["8140"]},   # Andel af samlet område (pct.)
        {"code": "Tid", "values": aar},
    ])
    ud = pr_kommune_aar(rows)
    for r in rows:
        if r.get("OMRÅDE") == HELE_LANDET:
            v = parse_value(r.get("INDHOLD", ""))
            if v is not None:
                noegle = ("000", aarstal(r.get("TID", "")))
                ud[noegle] = ud.get(noegle, 0.0) + v
    return {k: round(v, 2) for k, v in ud.items()}


def serie_areal_intensiv(aar: list[str]) -> dict[tuple[str, str], float]:
    """Intensivt landbrug i pct. af arealet (D1+D2+D4). Bruges af både scoren
    og retningspilen."""
    return _serie_andel(INTENSIV_KODER, aar)


def serie_areal_bebygget(aar: list[str]) -> dict[tuple[str, str], float]:
    """Bebygget areal og infrastruktur i pct. af arealet (A1+A2+B1+B2+C1).
    Bruges af både scoren og retningspilen."""
    return _serie_andel(BEBYGGET_KODER, aar)


def _tom(v):
    return "" if v is None else v


def ratio_natur(pct: float | None) -> float:
    """Natur-ratio: (30 / pct) * 100. Cap ved 999 hvis pct = 0."""
    if pct is None or pct <= 0:
        return 999.0
    return round((NATUR_GRÆNSE / pct) * 100, 2)


def ratio_mod_snit(pct: float | None, national_avg: float | None) -> float | None:
    """Ratio mod nationalt snit: (pct / national_avg) * 100 (kun til krydstjek)."""
    if pct is None or not national_avg:
        return None
    return round((pct / national_avg) * 100, 2)


def main():
    print("=" * 60)
    print("Doughnut Economics — Arealanvendelse (DST AREALDK2)")
    print("=" * 60)

    perioder = seneste_aar_liste("AREALDK2", 2, fallback=["2024", "2021"])
    aar, intensiv, nat_intensiv = seneste(serie_areal_intensiv(perioder), tabel="AREALDK2")
    _, bebygget, nat_bebygget = seneste(serie_areal_bebygget(perioder))
    _, natur, _ = seneste(_serie_andel(NATUR_KODER, perioder))
    print(f"  År {aar}: {len(intensiv)} kommuner")
    print(f"  Hele landet: intensivt landbrug {nat_intensiv}%, bebygget {nat_bebygget}%")

    rows = []
    for kode, navn in sorted(KOMMUNER.items()):
        i, b, n = intensiv.get(kode), bebygget.get(kode), natur.get(kode)
        rows.append({
            "kommune_kode": kode, "kommune_navn": navn,
            "natur_pct": "" if n is None else n,
            "intensiv_pct": "" if i is None else i,
            "bebygget_pct": "" if b is None else b,
            "natur_ratio": "" if n is None else ratio_natur(n),
            "intensiv_ratio": _tom(ratio_mod_snit(i, nat_intensiv)),
            "bebygget_ratio": _tom(ratio_mod_snit(b, nat_bebygget)),
            "areal_intensiv_ref": "" if nat_intensiv is None else nat_intensiv,
            "areal_bebygget_ref": "" if nat_bebygget is None else nat_bebygget,
        })
    mangler = [r["kommune_navn"] for r in rows if r["intensiv_pct"] == ""]
    if mangler:
        print(f"  ADVARSEL: Ingen data for {len(mangler)} kommuner: {', '.join(mangler)}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    t = next(r for r in rows if r["kommune_kode"] == "787")
    print(f"  Thisted: natur {t['natur_pct']}%, intensiv {t['intensiv_pct']}%, bebygget {t['bebygget_pct']}%")
    print(f"\nFærdig! Data gemt i {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

    # ───────────────────────────────────────────────────────────
    # AUTO-REBUILD af master_indicators.csv
    # ───────────────────────────────────────────────────────────
    try:
        import sys as _sys
        from pathlib import Path as _Path
        _sys.path.insert(0, str(_Path(__file__).resolve().parent))
        from build_master_csv import auto_build_master
        auto_build_master()
    except Exception as _e:
        print(f"\n Kunne ikke auto-rebuild master-CSV: {_e}")
        print("  Rådata er gemt. Kør manuelt: python3 scripts/build_master_csv.py")
