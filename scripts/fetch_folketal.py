#!/usr/bin/env python3
"""
fetch_folketal.py - folketal 1. januar pr. kommune (DST FOLK1A)
===============================================================

Bruges af build_master_csv.py til at markere tal, der bygger på få tilfælde
(registrets `smaa_tal`, se arkitekturdokumentets R16). Et tal pr. indbygger
ganges tilbage til et antal: antal = råværdi × folketal / pr × år. Under 20
tilfælde markeres kommunen med "få tilfælde" på kommunesiden, efter NCHS'
konvention: en rate på under 20 hændelser har en relativ standardfejl på
mindst 23 % og regnes for upålidelig (CDC WONDER, "Underlying Cause of
Death", afsnittet om upålidelige rater).

Folketallet er det seneste 1. januar. For trafikulykkernes treårige
gennemsnit er antallet derfor en tilnærmelse, som er god nok til en markering.

Brug (fra projektets rodmappe):
  python3 scripts/fetch_folketal.py

Output:
  data/folketal.csv (kommune_kode, kommune_navn, folketal, aar)
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kommuner import KOMMUNER  # noqa: E402
from dst import folketal  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "folketal.csv"


def main() -> int:
    from dst_aar import seneste_kvartal, registrer_aar
    aar = seneste_kvartal("FOLK1A")[:4]
    tal = folketal([aar])
    mangler = [KOMMUNER[k] for k in KOMMUNER if (k, aar) not in tal]
    if mangler:
        print(f"FEJL: intet folketal for {mangler}")
        return 1
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["kommune_kode", "kommune_navn", "folketal", "aar"])
        for kode in sorted(KOMMUNER, key=int):
            w.writerow([kode, KOMMUNER[kode], int(tal[(kode, aar)]), aar])
    registrer_aar("FOLK1A", f"{aar}K1")
    print(f"✓ {OUTPUT.relative_to(ROOT)}: 98 kommuner, 1. januar {aar}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
