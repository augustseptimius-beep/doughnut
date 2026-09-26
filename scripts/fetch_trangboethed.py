#!/usr/bin/env python3
"""
fetch_trangboethed.py - trangboethed pr. kommune (DST BOL103)
=============================================================

Indikatoren `trangboethed` under Bolig: andelen af beboerne i helårsboliger,
der bor i en bolig med flere personer end værelser.

HVORFOR (sep. 2026)
-------------------
Bolig bestod af ubeboede boliger og boligareal pr. person. De to korrelerede
-0,85 (-0,56 i kommunegruppevisningen): landkommuner blev straffet for tomme
boliger og belønnet for plads, så kategorien udlignede sig selv. Ubeboede
boliger måler desuden affolkning, ikke hvordan beboerne bor, og boligareal
belønner "jo mere, jo bedre", som strider mod rammen (samme fejl som den
fjernede bilrådighed). Trangboethed måler et underskud under en bundgrænse,
som et socialt fundament skal. Begge gamle indikatorer er fjernet (registrets
_fjernet); deres CSV'er og scripts står stadig.

DEFINITION
----------
Tæller: personer i beboede boliger (BEBO=1000) med flere personer end værelser.
Nævner: personer i beboede boliger med oplyst antal værelser.
Boligtyper: parcel-/stuehuse, række-/kædehuse og etageboliger (ANVENDELSE 125,
130, 140), samme afgrænsning som vacant_housing brugte. Kollegier,
døgninstitutioner og fritidshuse er ikke med.

Definitionen er platformens egen forenkling. Eurostats overbelægningsmål
tildeler rum efter husstandens alder og sammensætning, og de oplysninger findes
ikke i BOL103. To tilnærmelser følger af tabellens grupper: husstande på 7+
personer tælles som 7, og boliger med 6+ værelser som 6. En husstand på 7+ i
en bolig med 6+ værelser tælles derfor som trangboet; det er sjældent.

Landstallet er de 98 kommuner samlet (dst.andel(), arkitekturdokumentet R3).
Retningspilen bruger samme funktion (serie_trangboethed), og tabellen går
tilbage til 2010.

Brug (fra projektets rodmappe):
  python3 scripts/fetch_trangboethed.py

Output:
  data/trangboethed_scores.csv
"""

from __future__ import annotations

import csv
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kommuner import KOMMUNER, KODER  # noqa: E402
from dst import api_post, parse_value, andel  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "trangboethed_scores.csv"
TABEL = "BOL103"

VAERELSER = {"11": 1, "21": 2, "31": 3, "41": 4, "51": 5, "6-": 6}      # UOPL udelades
PERSONER = {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7-": 7}


def serie_trangboethed(perioder: list[str]) -> dict[tuple[str, str], float]:
    """Andel af beboerne (%) der bor med flere personer end værelser.
    {(kommune_kode, år): pct} inkl. hele landet (000) som de 98 kommuner samlet.
    Ét kald pr. år, fordi BOLIGSTØR ikke kan udelades, og et flerårigt kald
    overskrider DST's grænse for antal celler."""
    trange: dict[tuple[str, str], float] = {}
    alle: dict[tuple[str, str], float] = {}
    for aar in perioder:
        rows = api_post(TABEL, [
            {"code": "AMT", "values": ["*"]},
            {"code": "BEBO", "values": ["1000"]},
            {"code": "ANVENDELSE", "values": ["125", "130", "140"]},
            {"code": "ANTVÆR", "values": list(VAERELSER)},
            {"code": "BOLIGSTØR", "values": ["*"]},
            {"code": "HUSSTØR", "values": list(PERSONER)},
            {"code": "Tid", "values": [aar]},
        ], timeout=180)
        for r in rows:
            kode = (r.get("AMT") or "").strip()
            if kode not in KODER:
                continue
            boliger = parse_value(r.get("INDHOLD", ""))
            if not boliger:
                continue
            pers = PERSONER[r["HUSSTØR"]]
            noegle = (kode, str(aar))
            alle[noegle] = alle.get(noegle, 0.0) + boliger * pers
            if pers > VAERELSER[r["ANTVÆR"]]:
                trange[noegle] = trange.get(noegle, 0.0) + boliger * pers
    for k in alle:
        trange.setdefault(k, 0.0)
    return andel(trange, alle, 2)


def main() -> int:
    print("=" * 66)
    print("Trangboethed pr. kommune - DST BOL103")
    print("=" * 66)
    from dst_aar import seneste_aar, registrer_aar
    aar = seneste_aar(TABEL)
    serie = serie_trangboethed([aar])
    vaerdier = {k: v for (k, a), v in serie.items() if a == aar and k != "000"}
    land = serie.get(("000", aar))
    mangler = sorted(set(KOMMUNER) - set(vaerdier))
    if mangler:
        print(f"  ADVARSEL: ingen værdi for {[KOMMUNER[k] for k in mangler]}")
    print(f"  {aar}: {len(vaerdier)}/98 kommuner, landstal {land} %, "
          f"median {statistics.median(vaerdier.values()):.1f} %, "
          f"spænd {min(vaerdier.values()):.1f}-{max(vaerdier.values()):.1f} %")

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["kommune_kode", "kommune_navn", "trangboethed_raw",
                    "trangboethed_ratio", "trangboethed_ref"])
        for kode in sorted(KOMMUNER, key=int):
            v = vaerdier.get(kode)
            # Krydstjek til build_master_csv.py, som selv beregner scoren (R2, R4).
            ratio = "" if v is None else (150.0 if v == 0 else min(round(land / v * 100, 2), 150.0))
            w.writerow([kode, KOMMUNER[kode], "" if v is None else v, ratio, land])
    print(f"✓ {OUTPUT.relative_to(ROOT)}")
    registrer_aar(TABEL, aar)
    print(f"  Thisted: {vaerdier.get('787')} %")
    return 0


if __name__ == "__main__":
    rc = main()
    # ───────────────────────────────────────────────────────────
    # AUTO-REBUILD af master_indicators.csv
    # ───────────────────────────────────────────────────────────
    try:
        from build_master_csv import auto_build_master
        auto_build_master()
    except Exception as _e:
        print(f"\n⚠ Kunne ikke auto-rebuild master-CSV: {_e}")
        print("  Rådata er gemt. Kør manuelt: python3 scripts/build_master_csv.py")
    sys.exit(rc)
