#!/usr/bin/env python3
"""
Vandindvinding pr. capita - Doughnut Economics indikator (vand-dimensionen)
===========================================================================
Henter vandindvinding fra almene vandværker (INDKAT=100) fra DST VANDIND
og beregner m³ pr. person pr. kommune.

Datakilde:
  Danmarks Statistik - Statistikbanken VANDIND (Indvinding af vand)
  VANDTYP = TOTVAND (vand i alt)
  INDKAT  = 100 (alment vandværk)
  Tid     = nyeste år med data

Metode:
  1. Hent vandindvinding (mio. m³) pr. kommune fra VANDIND
  2. Hent befolkningstal fra FOLK1A (1. januar samme år)
  3. Beregn vandindvinding_m3_per_person = (mio_m3 * 1_000_000) / befolkning
  4. Sæt None for kommuner < 10 m³/person (data-artefakt: KBH's vandværk
     er fysisk registreret i andre kommuner, fx via HOFOR)
  5. Beregn nationalt vægtet gennemsnit (befolkningsvægtet)
  6. Ratio = (kommune / landsgennemsnit) * 100
     Høj ratio = mere pres på grundvand = overshoot

Scoring:
  ratio > 100 = bruger mere end landsgennemsnit = øget grundvandspres
  ratio < 100 = bruger mindre = under landsgennemsnit
  Baseline: Niveau 3 (landsgennemsnit). Ingen global planetær grænse der
  er direkte operationaliserbar på kommuneniveau.

Begrænsninger:
  - Data registreres ved indvindingspunktet (vandværkets placering),
    ikke ved forbrugsstedet. Store vandforsyningsselskaber der dækker
    flere kommuner kan give kunstigt lave tal i bykommuner.
  - Kun alment vandværk (INDKAT=100) - industri og markvanding er udeladt
    for at sikre sammenlignelighed på tværs af kommuner.

Output:
  data/vandindvinding_scores.csv
  Kolonner: kommune_kode, kommune_navn, vandindvinding_m3_per_person, vandindvinding_ratio,
            vandindvinding_ref (landstallet)

Kør fra projektets rodmappe:
  python3 scripts/fetch_vandindvinding_data.py
"""

from __future__ import annotations  # kræves: maskinen kører Python 3.9,
# hvor 'float | None' i en signatur ellers fejler ved import (TypeError).

import csv
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kommuner import KOMMUNER  # noqa: E402  (de 98 kommuner, data/kommuner.json)
from dst import api_post, folketal, pr_kommune_aar, seneste  # noqa: E402  (fælles DST-kald)
from dst_aar import seneste_aar_liste  # noqa: E402

# ── Konstanter ────────────────────────────────────────────────────────────────

OUTPUT_FIL = Path(__file__).resolve().parent.parent / "data" / "vandindvinding_scores.csv"

# Minimumsgrænse for m³/person - under dette er data et registreringsartefakt
MIN_M3_PER_PERSON = 10.0


# ── Vandindvinding pr. person (samme funktion til score og retningspil) ──────

def serie_vandindvinding(aar: list[str]) -> dict[tuple[str, str], float]:
    """
    VANDIND (VANDTYP=TOTVAND, INDKAT=100 alment vandværk) i m³ pr. person med
    folketallet 1. januar samme år. {(kommune_kode, år): m³/person}; landstallet
    (000) er det befolkningsvægtede gennemsnit af kommunerne med gyldige data.
    Under MIN_M3_PER_PERSON udelades kommunen som registreringsartefakt (fx
    København, hvis vandværker ligger i nabokommunerne).

    Bruges af både scoren og retningspilen (fetch_trend_history.py). Indtil
    sep. 2026 var året (2024) og folketallet (2025K1) hårdkodet, og kommunerne
    blev fundet ved at matche navne, også på delstrenge.
    """
    rows = api_post("VANDIND", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "VANDTYP", "values": ["TOTVAND"]},
        {"code": "INDKAT", "values": ["100"]},
        {"code": "Tid", "values": aar},
    ])
    mio_m3 = {k: v for k, v in pr_kommune_aar(rows).items() if k[0] != "000"}
    folk = folketal(sorted({a for _, a in mio_m3}))
    ud: dict[tuple[str, str], float] = {}
    sum_m3: dict[str, float] = {}
    sum_bef: dict[str, float] = {}
    for (kode, a), mio in mio_m3.items():
        bef = folk.get((kode, a))
        if not bef:
            continue
        m3 = mio * 1_000_000 / bef
        if m3 < MIN_M3_PER_PERSON:
            continue
        ud[(kode, a)] = round(m3, 2)
        sum_m3[a] = sum_m3.get(a, 0.0) + mio * 1_000_000
        sum_bef[a] = sum_bef.get(a, 0.0) + bef
    for a in sum_m3:
        ud[("000", a)] = round(sum_m3[a] / sum_bef[a], 2)
    return ud


def beregn_og_gem() -> None:
    """Henter nyeste år, beregner ratio (til krydstjek) og skriver CSV'en."""
    aar, vaerdier, landssnit = seneste(
        serie_vandindvinding(seneste_aar_liste("VANDIND", 2, fallback=["2024", "2023"])),
        tabel="VANDIND")
    if not vaerdier:
        print("FEJL: Ingen gyldige data til rådighed.")
        return
    print(f"  År {aar}: {len(vaerdier)}/98 kommuner med gyldige data")
    print(f"  Nationalt gennemsnit (befolkningsvægtet): {landssnit:.1f} m³/person")
    for kode in KOMMUNER:
        if kode not in vaerdier:
            print(f"  ⚠ {KOMMUNER[kode]}: ingen gyldig værdi (under {MIN_M3_PER_PERSON} m³/person eller ingen data)")

    OUTPUT_FIL.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FIL, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["kommune_kode", "kommune_navn", "vandindvinding_m3_per_person",
                         "vandindvinding_ratio", "vandindvinding_ref"])
        for kode in sorted(KOMMUNER):
            v = vaerdier.get(kode)
            writer.writerow([kode, KOMMUNER[kode], "" if v is None else v,
                             "" if v is None else round(v / landssnit * 100, 2), landssnit])
    t = vaerdier.get("787")
    print(f"\n  Thisted: {t} m³/person" if t else "\n  Thisted: ingen værdi")
    print(f"\n✓ Gemt: {OUTPUT_FIL} ({len(KOMMUNER)} kommuner)")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("Doughnut Economics - Vandindvinding pr. capita (DST VANDIND)")
    print("=" * 65)
    print("Kilde: Statistikbanken VANDIND, INDKAT=100 (alment vandværk), nyeste år")
    print(f"Min. grænse for gyldige data: {MIN_M3_PER_PERSON} m³/person")
    print()

    beregn_og_gem()

    print("\nFærdig!")


if __name__ == "__main__":
    main()

    # ───────────────────────────────────────────────────────────────
    # AUTO-REBUILD af master_indicators.csv
    # ───────────────────────────────────────────────────────────────
    try:
        import sys as _sys
        from pathlib import Path as _Path
        _sys.path.insert(0, str(_Path(__file__).resolve().parent))
        from build_master_csv import auto_build_master
        auto_build_master()
    except Exception as _e:
        print(f"\n⚠ Kunne ikke auto-rebuild master-CSV: {_e}")
        print("  Rådata er gemt. Kør manuelt: python3 scripts/build_master_csv.py")
