#!/usr/bin/env python3
"""
fetch_eco_new_data.py

Henter nye økologiske indikatorer for alle 98 kommuner fra Danmarks Statistik.

Opretter/opdaterer:
  ../data/naeringsstoffer_scores.csv  (Næringsstoffer)
  ../data/vand_scores.csv             (Vand)
  ../data/forurening_scores.csv       (Forurening)

Indikatorer:
  NÆRINGSSTOFFER:
    - VANDUD (KV): Kvælstof-udledning (ton total-N) pr. 1.000 indb. (inverteret - lavere er bedre)
    - VANDUD (FO): Fosfor-udledning (ton total-P) pr. 1.000 indb. (inverteret - lavere er bedre)

  VAND:
    - VANDUD (SP): Spildevandsudledning (1.000 m³) pr. 1.000 indb. (inverteret - lavere er bedre)
    - VANDIND:     Vandindvinding (mio. m³) pr. 1.000 indb. (inverteret - lavere er bedre)

  FORURENING:
    - LABY25 (AFFALDIND): Husholdningsaffald kg pr. indbygger (inverteret - lavere er bedre)

Brug:
  python3 fetch_eco_new_data.py
"""

import csv
import io
import json
import sys
import time
import urllib.request
from pathlib import Path

API_URL = "https://api.statbank.dk/v1/data"
REQUEST_DELAY = 0.7  # sekunder mellem kald

OUTPUT_DIR = Path(__file__).parent.parent / "data"

# Alle 98 kommuner
VALID_CODES = {
    "101", "147", "151", "153", "155", "157", "159", "161", "163", "165",
    "167", "169", "173", "175", "183", "185", "187", "190", "201", "210",
    "217", "219", "223", "230", "240", "250", "253", "259", "260", "265",
    "269", "270", "306", "316", "320", "326", "329", "330", "336", "340",
    "350", "360", "370", "376", "390", "400", "410", "420", "430", "440",
    "450", "461", "479", "480", "482", "492", "510", "530", "540", "550",
    "561", "563", "573", "575", "580", "607", "615", "621", "630", "657",
    "661", "665", "671", "706", "707", "710", "727", "730", "740", "741",
    "746", "751", "756", "760", "766", "773", "779", "787", "791", "810",
    "813", "820", "825", "840", "846", "849", "851", "860",
}


def api_post(table: str, variables: list[dict]) -> list[dict]:
    """Henter data fra StatBank API via POST (JSON-format med variabelselektion)."""
    payload = json.dumps({
        "table": table,
        "format": "CSV",
        "lang": "da",
        "valuePresentation": "Code",
        "variables": variables,
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    time.sleep(REQUEST_DELAY)

    resp = urllib.request.urlopen(req, timeout=60)
    content = resp.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content), delimiter=";")
    return list(reader)


def parse_value(raw: str) -> float | None:
    """Parser en StatBank-værdi til float."""
    raw = raw.strip()
    if raw in ("", "..", ".", "x", "X", "-"):
        return None
    try:
        return float(raw.replace(".", "").replace(",", "."))
    except ValueError:
        return None


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
        {"code": "Tid", "values": ["2025K1"]},
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
# FORURENING - LABY25 (husholdningsaffald)
# ---------------------------------------------------------------------------

def fetch_laby25() -> dict[str, dict]:
    """
    LABY25: Husholdningsaffald nøgletal pr. kommune.
    Returnerer {kommune_kode: {affald_kg: float, genanvendelse_pct: float}}.
    """
    print("Henter husholdningsaffald (LABY25)...")

    for year in ["2023", "2022"]:
        rows = api_post("LABY25", [
            {"code": "KOMGRP", "values": ["*"]},
            {"code": "BNØGLE", "values": ["AFFALDIND", "GENPCT"]},
            {"code": "Tid", "values": [year]},
        ])
        if len(rows) > 10:
            print(f"  Bruger data fra {year}")
            break

    result: dict[str, dict] = {}
    for row in rows:
        kode = row.get("KOMGRP", "").strip()
        noegle = row.get("BNØGLE", "").strip()
        val = parse_value(row.get("INDHOLD", ""))

        if kode not in result:
            result[kode] = {"affald_kg": None, "genanvendelse_pct": None}

        if val is not None:
            if noegle == "AFFALDIND":
                result[kode]["affald_kg"] = val
            elif noegle == "GENPCT":
                result[kode]["genanvendelse_pct"] = val

    valid = {k: v for k, v in result.items() if k in VALID_CODES}
    print(f"  LABY25: {len(valid)} kommuner med data")
    return result


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
    vandud = fetch_vandud()
    national_kv = vandud.get("000", {}).get("kv", 0)
    national_fo = vandud.get("000", {}).get("fo", 0)

    # Per capita pr. 1.000 indb.
    nat_kv_pc = (national_kv / national_pop) * 1000 if national_pop else 0
    nat_fo_pc = (national_fo / national_pop) * 1000 if national_pop else 0
    print(f"  National kvælstof: {national_kv:.0f} ton = {nat_kv_pc:.3f} ton/1.000 indb.")
    print(f"  National fosfor: {national_fo:.0f} ton = {nat_fo_pc:.3f} ton/1.000 indb.")

    naer_rows = []
    for kode in sorted(VALID_CODES):
        kommune_pop = pop.get(kode)
        kommune_data = vandud.get(kode, {})
        kv = kommune_data.get("kv", 0)
        fo = kommune_data.get("fo", 0)

        if kommune_pop and kommune_pop > 0:
            kv_pc = (kv / kommune_pop) * 1000
            fo_pc = (fo / kommune_pop) * 1000
            kv_ratio = ratio_inverse(kv_pc, nat_kv_pc)
            fo_ratio = ratio_inverse(fo_pc, nat_fo_pc)
        else:
            kv_pc = fo_pc = 0
            kv_ratio = fo_ratio = None

        naer_rows.append({
            "kommune_kode": kode,
            "nitrogen_per_1000": round(kv_pc, 3) if kv_pc else "",
            "phosphorus_per_1000": round(fo_pc, 3) if fo_pc else "",
            "nitrogen_ratio": kv_ratio if kv_ratio else "",
            "phosphorus_ratio": fo_ratio if fo_ratio else "",
        })

    outfile = OUTPUT_DIR / "naeringsstoffer_scores.csv"
    with open(outfile, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["kommune_kode", "nitrogen_per_1000", "phosphorus_per_1000", "nitrogen_ratio", "phosphorus_ratio"])
        w.writeheader()
        w.writerows(naer_rows)
    valid_naer = [r for r in naer_rows if r["nitrogen_ratio"] != ""]
    print(f"  => Skrev {outfile.name}: {len(valid_naer)} kommuner")

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
    laby25 = fetch_laby25()
    national_affald = laby25.get("000", {}).get("affald_kg")

    if not national_affald:
        print("  ADVARSEL: Ingen national affaldsdata!")
        national_affald = 543  # Fallback fra vores test

    print(f"  National affald: {national_affald:.0f} kg/indb.")

    foru_rows = []
    for kode in sorted(VALID_CODES):
        data = laby25.get(kode, {})
        affald = data.get("affald_kg")

        if affald is not None and national_affald:
            affald_ratio = ratio_inverse(affald, national_affald)
        else:
            affald_ratio = None

        foru_rows.append({
            "kommune_kode": kode,
            "waste_kg_per_capita": affald if affald is not None else "",
            "waste_ratio": affald_ratio if affald_ratio is not None else "",
        })

    outfile = OUTPUT_DIR / "forurening_scores.csv"
    with open(outfile, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["kommune_kode", "waste_kg_per_capita", "waste_ratio"])
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
