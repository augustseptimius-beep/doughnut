"""
kommuner.py - de 98 kommuner, ét sted.

Læser data/kommuner.json, som webappen også bruger til kommunegrupperne
(shared.ts). Indtil sep. 2026 havde 15 scripts hver sin afskrevne liste over
kommunekoder og -navne. De var ens, men en ændring (en kommunesammenlægning,
et navn) skulle rettes 15 steder.

Brug:
    from kommuner import KOMMUNER, KODER, kode_for_navn
    for kode, navn in KOMMUNER.items(): ...
"""

from __future__ import annotations

import json
from pathlib import Path

_FIL = Path(__file__).resolve().parent.parent / "data" / "kommuner.json"

with open(_FIL, encoding="utf-8") as _f:
    _DATA = json.load(_f)

# kode -> navn, sorteret efter kode. Navnene er DST's stavemåde.
KOMMUNER: dict[str, str] = {k["kode"]: k["navn"] for k in _DATA["kommuner"]}

# Mængden af gyldige kommunekoder (tidligere VALID_CODES i hvert script).
KODER: set[str] = set(KOMMUNER)

# kode -> kommunegruppe 1-5 (DST KOMMUNEGRUPPER_V1_2018).
GRUPPE: dict[str, int] = {k["kode"]: k["gruppe"] for k in _DATA["kommuner"]}

_KODE_FOR_NAVN = {navn: kode for kode, navn in KOMMUNER.items()}

if len(KOMMUNER) != 98:
    raise ValueError(f"{_FIL.name} skal have 98 kommuner, har {len(KOMMUNER)}")


def kode_for_navn(navn: str) -> str | None:
    """Kommunekoden for et kommunenavn skrevet som DST skriver det, ellers None.

    Bruges til kilder der kun har navne (fx forsikringsskader fra F&P). Der
    gættes bevidst ikke på stavevarianter: et ukendt navn skal fanges, ikke
    matches forkert."""
    return _KODE_FOR_NAVN.get(navn.strip())
