#!/usr/bin/env python3
"""
fetch_eco_new_data.py

Henter nye økologiske indikatorer for alle 98 kommuner fra Danmarks Statistik.

Opretter/opdaterer:
  ../data/naeringsstoffer_scores.csv  (Næringsstoffer)
  ../data/vand_scores.csv             (Vand)
  ../data/forurening_scores.csv       (Forurening)

Indikatorer (platformen scorer fra sep. 2026 kun affald og genanvendelse herfra;
kvælstof og fosfor fra spildevand er fjernet, se data/indikatorer.json's
_fjernet, men skrives stadig til naeringsstoffer_scores.csv som kildespor.
Besluttet 25. sep. 2026: de kommer heller ikke tilbage som kontekst. Spildevandet
tæller allerede med i kystvandenes statusbelastning (naer_kystvand), tallet pr.
indbygger viser hvor renseanlægget ligger og ikke hvem der udleder, og kontekst
er kun til opdelinger af et scoret tal (CLAUDE.md pkt. 9)):
  NÆRINGSSTOFFER:
    - VANDUD (KV): Kvælstof-udledning (ton total-N) pr. 1.000 indb. (inverteret - lavere er bedre)
    - VANDUD (FO): Fosfor-udledning (ton total-P) pr. 1.000 indb. (inverteret - lavere er bedre)

  VAND:
    - VANDUD (SP): Spildevandsudledning (1.000 m³) pr. 1.000 indb. (inverteret - lavere er bedre)
    - VANDIND:     Vandindvinding (mio. m³) pr. 1.000 indb. (inverteret - lavere er bedre)

  FORURENING:
    - LABY25 (AFFALDIND): Husholdningsaffald kg pr. indbygger, treårsmedian (inverteret - lavere er bedre)
    - LABY25 (GENPCT): Husholdningsaffald indsamlet til genanvendelse, pct., treårsmedian

Brug:
  python3 fetch_eco_new_data.py
"""

from __future__ import annotations  # kræves: maskinen kører Python 3.9,
# hvor 'float | None' i en signatur ellers fejler ved import (TypeError).

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dst_aar import perioder_fra, seneste_aar_liste, seneste_kvartal  # noqa: E402
from dst import api_post, parse_value, pr_indbygger, pr_kommune_aar, rullende, seneste  # noqa: E402  (fælles DST-kald, scripts/dst.py)
from kommuner import KODER as VALID_CODES  # noqa: E402  (de 98 kommuner, data/kommuner.json)


OUTPUT_DIR = Path(__file__).parent.parent / "data"


def ratio_inverse(kommune_val: float, national_avg: float) -> float:
    """Inverteret ratio: lavere er bedre. national_avg/kommune_val * 100."""
    if kommune_val == 0:
        return 150  # Cap: perfekt score
    return round((national_avg / kommune_val) * 100, 2)


# ---------------------------------------------------------------------------
# Hent befolkningstal for per-capita beregninger
# ---------------------------------------------------------------------------

def fetch_population() -> dict[str, float]:
    """
    FOLK1A: Befolkning pr. kommune (seneste kvartal).
    Returnerer {kommune_kode: antal_personer}.
    """
    print("Henter befolkningstal (FOLK1A)...")
    rows = api_post("FOLK1A", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "KØN", "values": ["TOT"]},
        {"code": "ALDER", "values": ["IALT"]},
        {"code": "Tid", "values": [seneste_kvartal("FOLK1A", "K1", fallback="2025K1")]},
    ])
    result = {}
    for row in rows:
        kode = row.get("OMRÅDE", "").strip()
        val = parse_value(row.get("INDHOLD", ""))
        if val is not None:
            result[kode] = val
    print(f"  Befolkning: {len([k for k in result if k in VALID_CODES])} kommuner")
    return result


# ---------------------------------------------------------------------------
# NÆRINGSSTOFFER - VANDUD (kvælstof + fosfor)
# ---------------------------------------------------------------------------

def fetch_vandud() -> dict[str, dict]:
    """
    VANDUD: Spildevandsudledning pr. kommune.
    Henter kvælstof (KV), fosfor (FO) og spildevand (SP), alle anlægstyper summeret.
    Returnerer {kommune_kode: {kv: ton, fo: ton, sp: 1000m3}}.
    """
    print("Henter spildevandsudledning (VANDUD)...")

    # Hent seneste år med data - brug 2024 først, fallback til 2023
    for year in ["2024", "2023"]:
        rows = api_post("VANDUD", [
            {"code": "OMRÅDE", "values": ["*"]},
            {"code": "UDL", "values": ["KV", "FO", "SP"]},
            {"code": "ANLAEG", "values": ["*"]},
            {"code": "Tid", "values": [year]},
        ])
        if len(rows) > 10:
            print(f"  Bruger data fra {year}")
            break
    else:
        print("  FEJL: Ingen data fundet!")
        return {}

    # Aggreger per kommune (summér alle anlægstyper)
    result: dict[str, dict] = {}
    for row in rows:
        kode = row.get("OMRÅDE", "").strip()
        udl = row.get("UDL", "").strip()
        val = parse_value(row.get("INDHOLD", ""))

        if kode not in result:
            result[kode] = {"kv": 0, "fo": 0, "sp": 0}

        if val is not None:
            if udl == "KV":
                result[kode]["kv"] += val
            elif udl == "FO":
                result[kode]["fo"] += val
            elif udl == "SP":
                result[kode]["sp"] += val

    valid = {k: v for k, v in result.items() if k in VALID_CODES}
    print(f"  VANDUD: {len(valid)} kommuner med data")
    return result


def _serie_vandud(udl: str, aar: list[str]) -> dict[tuple[str, str], float]:
    """VANDUD: udledning (UDL=KV kvælstof, FO fosfor) summeret over alle
    anlægstyper, i ton pr. 1.000 indb. med folketallet 1. januar samme år.
    {(kommune_kode, år): værdi} inkl. hele landet (000). Ingen registreret
    udledning (0) giver ingen kommuneværdi: det behandles som manglende data,
    ikke som topscore (se data/CHANGELOG.md 22. sep. 2026)."""
    rows = api_post("VANDUD", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "UDL", "values": [udl]},
        {"code": "ANLAEG", "values": ["*"]},
        {"code": "Tid", "values": aar},
    ])
    antal = pr_kommune_aar(rows)
    # alle_i_naevner: en kommune uden række (Frederiksberg) har sit spildevand
    # renset i nabokommunen, så dens indbyggere hører med i landstallet.
    per_1000 = pr_indbygger(antal, 1000, 3, alle_i_naevner=True)
    # Kommuner uden udledning får ingen værdi selv.
    return {k: v for k, v in per_1000.items() if k[0] == "000" or antal.get(k)}


def serie_naer_nitrogen(aar: list[str]) -> dict[tuple[str, str], float]:
    """Kvælstof fra spildevand, ton pr. 1.000 indb. Bruges af både scoren og
    retningspilen (fetch_trend_history.py)."""
    return _serie_vandud("KV", aar)


def serie_naer_phosphorus(aar: list[str]) -> dict[tuple[str, str], float]:
    """Fosfor fra spildevand, ton pr. 1.000 indb. Bruges af både scoren og
    retningspilen (fetch_trend_history.py)."""
    return _serie_vandud("FO", aar)


# ---------------------------------------------------------------------------
# VAND - VANDIND (vandindvinding)
# ---------------------------------------------------------------------------

def fetch_vandind() -> dict[str, float]:
    """
    VANDIND: Vandindvinding pr. kommune (mio. m³).
    Summerer alle vandtyper og indvindingskategorier.
    Returnerer {kommune_kode: mio_m3}.
    """
    print("Henter vandindvinding (VANDIND)...")

    for year in ["2024", "2023"]:
        rows = api_post("VANDIND", [
            {"code": "OMRÅDE", "values": ["*"]},
            {"code": "VANDTYP", "values": ["TOTVAND"]},
            {"code": "INDKAT", "values": ["*"]},
            {"code": "Tid", "values": [year]},
        ])
        if len(rows) > 10:
            print(f"  Bruger data fra {year}")
            break

    # Aggreger per kommune
    result: dict[str, float] = {}
    for row in rows:
        kode = row.get("OMRÅDE", "").strip()
        val = parse_value(row.get("INDHOLD", ""))
        if val is not None:
            result[kode] = result.get(kode, 0) + val

    valid = {k: v for k, v in result.items() if k in VALID_CODES}
    print(f"  VANDIND: {len(valid)} kommuner med data")
    return result


# ---------------------------------------------------------------------------
# FORURENING - LABY25 (husholdningsaffald og genanvendelse)
# ---------------------------------------------------------------------------

# Treårsmedian (fra sep. 2026). LABY25's enkeltår indeholder tydelige
# fejlindberetninger: i 2023 faldt Hørsholm fra 589 til 57 kg husholdningsaffald
# pr. indbygger og Allerød fra 623 til 258, mens Fredensborg, Norddjurs og Ærø
# næsten fordoblede deres tal. Med ét år gav det Hørsholm en affaldsratio på 10
# og Fredensborg 254. Medianen af de tre seneste år ignorerer ét afvigende år.
LABY25_AAR = 3


def _laby25(noegle: str, aar: list[str]) -> dict[tuple[str, str], float]:
    """LABY25-nøgletal (AFFALDIND kg pr. indbygger, GENPCT pct. til genanvendelse)
    pr. (kommune_kode, år) inkl. hele landet (000)."""
    rows = api_post("LABY25", [
        {"code": "KOMGRP", "values": ["*"]},
        {"code": "BNØGLE", "values": [noegle]},
        {"code": "Tid", "values": aar},
    ])
    return pr_kommune_aar(rows, omraade="KOMGRP")


def _laby25_median(noegle: str, perioder: list[str]) -> dict[tuple[str, str], float]:
    """Treårsmedian for år Y = medianen af Y-2, Y-1 og Y. Henter selv de to
    foregående år, så funktionen kan kaldes med de år man vil have tal for."""
    alle = [str(a) for a in range(int(min(perioder)) - (LABY25_AAR - 1), int(max(perioder)) + 1)]
    findes = set(perioder_fra("LABY25", int(alle[0])))
    return {k: v for k, v in rullende(_laby25(noegle, [a for a in alle if a in findes]),
                                       LABY25_AAR, "median", 1).items()
            if k[1] in perioder}


def serie_cirkularitet_waste(perioder: list[str]) -> dict[tuple[str, str], float]:
    """Husholdningsaffald, kg pr. indbygger, treårsmedian. Bruges af både scoren
    og retningspilen (fetch_trend_history.py, SAMME_SOM_SCOREN)."""
    return _laby25_median("AFFALDIND", perioder)


def serie_cirkularitet_recycling(perioder: list[str]) -> dict[tuple[str, str], float]:
    """Husholdningsaffald indsamlet til genanvendelse, pct., treårsmedian. Bruges
    af både scoren og retningspilen."""
    return _laby25_median("GENPCT", perioder)


# ---------------------------------------------------------------------------
# BEREGN OG SKRIV CSV-FILER
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Henter økologiske indikatorer fra Danmarks Statistik")
    print("=" * 60)

    # Hent befolkningstal
    pop = fetch_population()
    national_pop = pop.get("000")
    if not national_pop:
        print("FEJL: Kan ikke hente national befolkning!")
        sys.exit(1)
    print(f"  National befolkning: {national_pop:,.0f}")

    # ─── NÆRINGSSTOFFER ───
    # Samme funktioner som retningspilen bruger (serie_naer_*), med folketallet
    # 1. januar i udledningsåret.
    naer_aar = seneste_aar_liste("VANDUD", 2, fallback=["2024", "2023"])
    aar_kv, kv_pc, nat_kv_pc = seneste(serie_naer_nitrogen(naer_aar), tabel="VANDUD")
    aar_fo, fo_pc, nat_fo_pc = seneste(serie_naer_phosphorus(naer_aar), tabel="VANDUD")
    print(f"  Kvælstof {aar_kv}: landstal {nat_kv_pc} ton/1.000 indb.")
    print(f"  Fosfor {aar_fo}: landstal {nat_fo_pc} ton/1.000 indb.")

    naer_rows = []
    for kode in sorted(VALID_CODES):
        kv, fo = kv_pc.get(kode), fo_pc.get(kode)
        naer_rows.append({
            "kommune_kode": kode,
            "nitrogen_per_1000": kv if kv is not None else "",
            "phosphorus_per_1000": fo if fo is not None else "",
            "nitrogen_ratio": ratio_inverse(kv, nat_kv_pc) if kv and nat_kv_pc else "",
            "phosphorus_ratio": ratio_inverse(fo, nat_fo_pc) if fo and nat_fo_pc else "",
            "naer_nitrogen_ref": nat_kv_pc if nat_kv_pc is not None else "",
            "naer_phosphorus_ref": nat_fo_pc if nat_fo_pc is not None else "",
        })

    outfile = OUTPUT_DIR / "naeringsstoffer_scores.csv"
    with open(outfile, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["kommune_kode", "nitrogen_per_1000", "phosphorus_per_1000",
                                          "nitrogen_ratio", "phosphorus_ratio",
                                          "naer_nitrogen_ref", "naer_phosphorus_ref"])
        w.writeheader()
        w.writerows(naer_rows)
    valid_naer = [r for r in naer_rows if r["nitrogen_ratio"] != ""]
    print(f"  => Skrev {outfile.name}: {len(valid_naer)} kommuner")

    # vand_scores.csv (spildevand og vandindvinding pr. indb.) bruges ikke af
    # platformen, men skrives stadig som kildespor. Den har sin egen hentning.
    vandud = fetch_vandud()

    # ─── VAND ───
    vandind = fetch_vandind()
    national_sp = vandud.get("000", {}).get("sp", 0)
    national_vind = vandind.get("000", 0)

    nat_sp_pc = (national_sp / national_pop) * 1000 if national_pop else 0
    nat_vind_pc = (national_vind / national_pop) * 1000 if national_pop else 0
    print(f"  National spildevand: {national_sp:.0f} x1.000 m³ = {nat_sp_pc:.3f} x1.000 m³/1.000 indb.")
    print(f"  National vandindvinding: {national_vind:.1f} mio. m³ = {nat_vind_pc:.4f} mio. m³/1.000 indb.")

    vand_rows = []
    for kode in sorted(VALID_CODES):
        kommune_pop = pop.get(kode)
        sp = vandud.get(kode, {}).get("sp", 0)
        vind = vandind.get(kode, 0)

        if kommune_pop and kommune_pop > 0:
            sp_pc = (sp / kommune_pop) * 1000
            vind_pc = (vind / kommune_pop) * 1000
            sp_ratio = ratio_inverse(sp_pc, nat_sp_pc)
            vind_ratio = ratio_inverse(vind_pc, nat_vind_pc)
        else:
            sp_pc = vind_pc = 0
            sp_ratio = vind_ratio = None

        vand_rows.append({
            "kommune_kode": kode,
            "wastewater_per_1000": round(sp_pc, 3) if sp_pc else "",
            "water_extraction_per_1000": round(vind_pc, 4) if vind_pc else "",
            "wastewater_ratio": sp_ratio if sp_ratio else "",
            "water_extraction_ratio": vind_ratio if vind_ratio else "",
        })

    outfile = OUTPUT_DIR / "vand_scores.csv"
    with open(outfile, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["kommune_kode", "wastewater_per_1000", "water_extraction_per_1000", "wastewater_ratio", "water_extraction_ratio"])
        w.writeheader()
        w.writerows(vand_rows)
    valid_vand = [r for r in vand_rows if r["wastewater_ratio"] != ""]
    print(f"  => Skrev {outfile.name}: {len(valid_vand)} kommuner")

    # ─── FORURENING ───
    # Samme funktioner som retningspilen (serie_cirkularitet_*): treårsmedian.
    affald_aar = seneste_aar_liste("LABY25", 1, fallback=["2023"])
    aar_af, affald, nat_affald = seneste(serie_cirkularitet_waste(affald_aar), tabel="LABY25")
    _, genanv, nat_genanv = seneste(serie_cirkularitet_recycling(affald_aar))
    print(f"  Husholdningsaffald {aar_af} (treårsmedian): landstal {nat_affald} kg/indb., "
          f"genanvendelse {nat_genanv}%")

    foru_rows = []
    for kode in sorted(VALID_CODES):
        af, ge = affald.get(kode), genanv.get(kode)
        foru_rows.append({
            "kommune_kode": kode,
            "waste_kg_per_capita": af if af is not None else "",
            "waste_ratio": ratio_inverse(af, nat_affald) if af is not None and nat_affald else "",
            "cirkularitet_waste_ref": nat_affald if nat_affald is not None else "",
            "recycling_pct": ge if ge is not None else "",
            # Krydstjek-ratio med komplement-formlen (R2a): andel IKKE genanvendt
            # målt mod de 35%, EU's 65%-mål tillader.
            "recycling_ratio": round((100 - ge) / 35 * 100, 2) if ge is not None else "",
        })

    outfile = OUTPUT_DIR / "forurening_scores.csv"
    with open(outfile, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["kommune_kode", "waste_kg_per_capita", "waste_ratio",
                                          "cirkularitet_waste_ref", "recycling_pct", "recycling_ratio"])
        w.writeheader()
        w.writerows(foru_rows)
    valid_foru = [r for r in foru_rows if r["waste_ratio"] != ""]
    print(f"  => Skrev {outfile.name}: {len(valid_foru)} kommuner")

    # ─── OPSUMMERING ───
    print("\n" + "=" * 60)
    print("OPSUMMERING")
    print("=" * 60)

    # Vis Thisted-tal
    for label, rows, cols in [
        ("Næringsstoffer", naer_rows, ["nitrogen_ratio", "phosphorus_ratio"]),
        ("Vand", vand_rows, ["wastewater_ratio", "water_extraction_ratio"]),
        ("Forurening", foru_rows, ["waste_ratio"]),
    ]:
        thisted = [r for r in rows if r["kommune_kode"] == "787"]
        if thisted:
            vals = {c: thisted[0][c] for c in cols}
            print(f"  Thisted ({label}): {vals}")

    print("\nFærdig!")


if __name__ == "__main__":
    main()

    # ───────────────────────────────────────────────────────────
    # AUTO-REBUILD af master_indicators.csv (tilføjet 2026)
    # ───────────────────────────────────────────────────────────
    try:
        import sys as _sys
        from pathlib import Path as _Path
        _sys.path.insert(0, str(_Path(__file__).resolve().parent))
        from build_master_csv import auto_build_master
        auto_build_master()
    except Exception as _e:
        print(f"\n⚠ Kunne ikke auto-rebuild master-CSV: {_e}")
        print("  Rådata er gemt. Kør manuelt: python3 scripts/build_master_csv.py")
