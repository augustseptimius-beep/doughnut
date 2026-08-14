#!/usr/bin/env python3
"""
fetch_bolig_fossil.py

Beregner kommunens SAMLEDE fossile varmeafhængighed pr. kommune - scoret mod
et absolut mål på 0% fossil (ikke landsgennemsnit), da udfasning af olie/gas er
dansk politik. Score = 100 - samlet_fossil%.

Samlet fossil% = direkte fossil opvarmning (olie+gas)
              + fjernvarme-dækning% × fjernvarmens fossile brændselsandel

Grundlaget er OPVARMET AREAL (m²), ikke antal beboere. Varmebehov skalerer med
areal: en oliefyret firelænget gård med to beboere fylder mere i varmeregnskabet
end tre lejligheder med seks beboere, men ville tælle mindre på beboerbasis.
Skiftet fra BOL202 (personer) til BYGB40 (m²) blev truffet august 2026 - se
data/CHANGELOG.md. Konsekvensen er beskeden (korrelation 0,998 med den gamle
metode), men den retter en systematisk skævhed hvor landkommuner fremstod ca.
1,7 pct.point for pænt og storbykommuner kun 0,1.

AFGRÆNSNING: kun helårsbeboelse (ANVEND 110-190). Fritidsboliger opgøres
separat som KONTEKST (scores ikke), fordi de har markant lavere fossilandel
(median 6,9% mod 20,0%) og derfor ville give sommerhuskommuner en kunstigt
bedre score på et mål der handler om husstandes varmeregninger. Erhvervs- og
avlsbygninger, garager og udhuse holdes helt ude - indikatoren måler boliger.

Kilder:
  - DST BYGB40 (Bygninger og deres opvarmede areal): giver BÅDE direkte fossil
    (oliefyr, oliekaminer, naturgas) OG fjernvarme-dækning på samme arealbasis.
  - data/fjernvarme_mix_scores.csv (Energistyrelsen EPT): fjernvarmens fossile
    brændselsandel pr. kommune. For de 18 fælles-net-kommuner uden lokalt mix
    bruges TJ-vægtet landsgennemsnit.

VIGTIGT: fjernvarme_mix_scores.csv skal være genereret FØR dette script køres
(kør fetch_fjernvarme_mix.py først).

Kør fra projektets rodmappe:
  python3 scripts/fetch_bolig_fossil.py
"""

from __future__ import annotations

import csv
import io
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

API_URL = "https://api.statbank.dk/v1/data"
REQUEST_DELAY = 0.7

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

# ─── BYGB40-koder ──────────────────────────────────────────────────────
# MÆNGDE4: 45 = Bygninger (antal), 50 = Kvadratmeter (1000 m2)
MAENGDE_KVADRATMETER = "50"

# OPVARM (10 værdier i alt)
OPVARM_FJERNVARME = {"1"}
OPVARM_FOSSIL = {
    "2",  # Centralvarme med oliefyr
    "3",  # Centralvarme med naturgas
    "6",  # Ovne med olie eller petroleum
}
# NB: "4 Centralvarme med fast brændsel" regnes IKKE som fossil - det er
# overvejende træ/biomasse. Samme afgrænsning som den tidligere BOL202-baserede
# opgørelse, hvor kun CO (olie) og CN (naturgas) talte som fossil.

# ANVEND: helårsbeboelse. Fritidsformål holdes ude af scoren, se docstring.
ANVEND_HELAARSBOLIG = [
    "110",  # Stuehuse til landbrugsejendomme
    "120",  # Parcelhuse
    "130",  # Række-, kæde- og dobbelthuse
    "140",  # Etageboliger
    "150",  # Kollegier
    "160",  # Døgninstitutioner
    "190",  # Anden helårsbeboelse
]
ANVEND_FRITIDSBOLIG = [
    "510",  # Sommerhuse
    "520",  # Uspecificeret ferieformål
    "540",  # Kolonihavehuse
    "590",  # Uspecificeret fritidsformål
]

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


def parse_value(raw: str) -> float | None:
    raw = raw.strip()
    if raw in ("", "..", ".", "x", "X", "-"):
        return None
    try:
        return float(raw.replace(".", "").replace(",", "."))
    except ValueError:
        return None


def api_post(table: str, variables: list[dict]) -> list[dict]:
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
    resp = urllib.request.urlopen(req, timeout=90)
    content = resp.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content), delimiter=";")
    return list(reader)


def auto_build_master():
    build_script = ROOT / "scripts" / "build_master_csv.py"
    if not build_script.exists():
        print("  ADVARSEL: build_master_csv.py ikke fundet - spring over.")
        return
    import subprocess
    result = subprocess.run(
        [sys.executable, str(build_script)],
        capture_output=True, text=True, cwd=str(ROOT)
    )
    if result.returncode == 0:
        print("  ✓ Master-CSV opdateret")
    else:
        print("  FEJL i build_master_csv.py:")
        print(result.stderr[-800:])


def load_fjernvarme_fossil() -> tuple[dict[str, float], float]:
    """Læser fjernvarmens fossile brændselsandel pr. kommune fra
    fjernvarme_mix_scores.csv. Returnerer ({kode: fjv_fossil_pct}, landssnit).
    Landssnit beregnes over kommuner med egen produktion (status=ok) og bruges
    for de 18 fælles-net-kommuner uden lokalt mix."""
    path = DATA_DIR / "fjernvarme_mix_scores.csv"
    if not path.exists():
        print("  ADVARSEL: fjernvarme_mix_scores.csv mangler - kør fetch_fjernvarme_mix.py først.")
        print("  Fortsætter uden fjernvarme-bidrag (kun direkte fossil).")
        return {}, 0.0
    # NB: denne CSV er skrevet af Python med "." som DECIMAL-separator.
    # Brug derfor almindelig float(), IKKE parse_value (som fjerner "." som
    # dansk tusind-separator og ville lave 7.9 om til 79).
    def csv_float(s: str) -> float | None:
        s = (s or "").strip()
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None

    per_kommune: dict[str, float] = {}
    w_sum = 0.0  # sum(fossil_pct * tj)
    tj_sum = 0.0
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            kode = (row.get("kommune_kode") or "").strip()
            val = csv_float(row.get("fjv_fossil_pct") or "")
            tj = csv_float(row.get("fjv_total_tj") or "") or 0.0
            if (row.get("fjv_status") or "").strip() == "ok" and val is not None:
                per_kommune[kode] = val
                w_sum += val * tj
                tj_sum += tj
    # TJ-vægtet landssnit: domineres af de store værker (typisk affald/biomasse,
    # lav fossil), hvilket er mest retvisende for de fælles-net-kommuner der
    # forsynes af netop de store metro-net.
    nat_avg = round(w_sum / tj_sum, 2) if tj_sum else 0.0
    print(f"  Fjernvarme-fossil: {len(per_kommune)} kommuner med eget mix, "
          f"TJ-vægtet landssnit {nat_avg:.1f}% (bruges for fælles-net-kommuner)")
    return per_kommune, nat_avg


def fetch_bygb40(year: str, anvend: list[str], label: str) -> dict[str, dict]:
    """Henter opvarmet areal (1.000 m²) pr. kommune fordelt på opvarmningsform.
    Returnerer {kode: {'fossil': m2, 'fjernvarme': m2, 'total': m2}}."""
    rows = api_post("BYGB40", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "MÆNGDE4", "values": [MAENGDE_KVADRATMETER]},
        {"code": "OPVARM", "values": ["*"]},
        {"code": "ANVEND", "values": anvend},
        {"code": "Tid", "values": [year]},
    ])
    ud: dict[str, dict] = {}
    for row in rows:
        kode = (row.get("OMRÅDE") or "").strip()
        if kode not in VALID_CODES:
            continue
        opvarm = (row.get("OPVARM") or "").strip()
        val = parse_value(row.get("INDHOLD", "") or "")
        if val is None or val < 0:
            continue
        d = ud.setdefault(kode, {"fossil": 0.0, "fjernvarme": 0.0, "total": 0.0})
        d["total"] += val
        if opvarm in OPVARM_FOSSIL:
            d["fossil"] += val
        elif opvarm in OPVARM_FJERNVARME:
            d["fjernvarme"] += val
    print(f"  {label}: {len(ud)} kommuner")
    return ud


def fetch_bolig_fossil():
    print("\n" + "=" * 60)
    print("Samlet fossil varmeafhængighed pr. kommune (mål: 0%)")
    print("Grundlag: DST BYGB40, opvarmet areal i m²")
    print("=" * 60)

    fjv_fossil_pct, fjv_fossil_nat = load_fjernvarme_fossil()

    # Forsøg nyeste år først
    year_used = None
    helaars: dict[str, dict] = {}
    for year in ["2026", "2025", "2024"]:
        print(f"  Forsøger BYGB40 {year}...")
        try:
            helaars = fetch_bygb40(year, ANVEND_HELAARSBOLIG, f"Helårsboliger {year}")
            if len(helaars) >= 90:
                year_used = year
                break
            print(f"  {year}: kun {len(helaars)} kommuner - prøver ældre år")
        except Exception as e:
            print(f"  {year} fejlede: {e}")

    if not year_used:
        print("  FEJL: Ingen brugbar data fundet.")
        return

    # Fritidsboliger til kontekst-visning (scores IKKE)
    try:
        fritid = fetch_bygb40(year_used, ANVEND_FRITIDSBOLIG, f"Fritidsboliger {year_used}")
    except Exception as e:
        print(f"  ADVARSEL: kunne ikke hente fritidsboliger: {e}")
        fritid = {}

    output_path = DATA_DIR / "bolig_fossil_scores.csv"
    samlet_pcts = []
    thisted_dbg = None
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "kommune_kode", "bolig_fossil_ratio", "bolig_fossil_raw",
            "fossil_direkte_pct", "fossil_via_fjv_pct",
            "fritid_fossil_pct", "fritid_andel_pct",
        ])
        for kode in sorted(VALID_CODES):
            h = helaars.get(kode)
            if not h or h["total"] <= 0:
                writer.writerow([kode, "", "", "", "", "", ""])
                continue
            total = h["total"]
            direkte_pct = h["fossil"] / total * 100
            fjv_daekning = h["fjernvarme"] / total * 100
            fjv_andel = fjv_fossil_pct.get(kode, fjv_fossil_nat)
            via_fjv_pct = fjv_daekning * fjv_andel / 100
            samlet = direkte_pct + via_fjv_pct
            # Score mod absolut mål 0%: 100 = ingen fossil.
            ratio = round(max(0.0, 100 - samlet), 2)

            # Kontekst: fritidsboligernes fossilandel og deres andel af boligarealet
            fr = fritid.get(kode)
            if fr and fr["total"] > 0:
                fritid_fossil = round(fr["fossil"] / fr["total"] * 100, 2)
                fritid_andel = round(fr["total"] / (total + fr["total"]) * 100, 2)
            else:
                fritid_fossil = ""
                fritid_andel = ""

            writer.writerow([
                kode, ratio, round(samlet, 2),
                round(direkte_pct, 2), round(via_fjv_pct, 2),
                fritid_fossil, fritid_andel,
            ])
            samlet_pcts.append(samlet)
            if kode == "787":
                thisted_dbg = (direkte_pct, fjv_daekning, fjv_andel, via_fjv_pct,
                               samlet, ratio, fritid_fossil, fritid_andel)

    print(f"\n  År anvendt: {year_used}")
    print(f"  Kommuner med data: {len(samlet_pcts)}")
    if samlet_pcts:
        print(f"  Samlet fossil%: min {min(samlet_pcts):.1f} / snit "
              f"{sum(samlet_pcts)/len(samlet_pcts):.1f} / max {max(samlet_pcts):.1f}")
    if thisted_dbg:
        d, dk, fa, vf, s, r, ff, fan = thisted_dbg
        print(f"  Thisted: direkte {d:.1f}% + fjernvarme-dækning {dk:.0f}% × {fa:.1f}% fossil "
              f"= via fjv {vf:.1f}% → samlet {s:.1f}% → score {r}")
        print(f"           fritidsboliger: {ff}% fossil, udgør {fan}% af boligarealet (kontekst)")
    print(f"  Gemt: {output_path}")


if __name__ == "__main__":
    fetch_bolig_fossil()
    print()
    auto_build_master()
