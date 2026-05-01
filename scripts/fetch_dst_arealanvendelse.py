#!/usr/bin/env python3
"""
fetch_dst_arealanvendelse.py - Arealanvendelse pr. danske kommune (DST AREALDK2)
=================================================================================
Henter arealdækningsdata fra Danmarks Statistiks Statistikbank (AREALDK2, 2024).
Ingen GIS eller spatial join - ren API.

Tre sub-indikatorer pr. kommune:
  1. natur_pct       = skov + lysåben natur + søer (E + F1 + F2 + G1)
  2. intensiv_pct    = intensivt landbrug (D1 + D2 + D4)
  3. bebygget_pct    = veje + lufthavne + bebyggelse + råstof (A1 + A2 + B1 + B2 + C1)

Ratio-logik (eco-konvention: >100 = overshoot):
  natur_ratio    = (30 / natur_pct) * 100  [grænse: 30% EU 30x30-mål]
  intensiv_ratio = (intensiv_pct / NATIONAL_AVG_INTENSIV) * 100  [grænse: nationalt snit]
  bebygget_ratio = (bebygget_pct / NATIONAL_AVG_BEBYGGET) * 100  [grænse: nationalt snit]

De nationale gennemsnit hentes live fra DST (OMRÅDE=95, matrikuleret areal 2024).

Output:
  data/arealanvendelse_scores.csv

Kilde:
  Danmarks Statistik AREALDK2 - https://www.statistikbanken.dk/AREALDK2

Brug:
  cd /sti/til/doughnut
  python3 scripts/fetch_dst_arealanvendelse.py
"""

import csv
import io
import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# ─── Stier ───────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "arealanvendelse_scores.csv"
DST_API = "https://api.statbank.dk/v1/data"
DST_TABLEINFO = "https://api.statbank.dk/v1/tableinfo"

# ─── Arealkategorier ─────────────────────────────────────────────────────────
# Fra DST AREALDK2 (2024). Koder bruges i API-kald; labels bruges til at matche
# CSV-svar (DST returnerer tekstlabels i INDHOLD-output, ikke koder).
NATUR_KODER    = ["E", "F1", "F2", "G1"]
INTENSIV_KODER = ["D1", "D2", "D4"]
BEBYGGET_KODER = ["A1", "A2", "B1", "B2", "C1"]
ALLE_KODER     = NATUR_KODER + INTENSIV_KODER + BEBYGGET_KODER

# DST returnerer ARE1 som tekstlabels i CSV. Her mappes label → kode-gruppe.
ARE1_LABEL_TIL_GRUPPE: dict[str, str] = {
    "Skov":                                                                        "natur",
    "Tør lysåben natur (heder, klitter o.lign.)":                                  "natur",
    "Våd lysåben natur (enge, moser o.lign.)":                                     "natur",
    "Søer":                                                                        "natur",
    "Intensivt landbrug (korn, rodfrugter, og andre midlertidige afgrøder)":       "intensiv",
    "Intensivt landbrug (frugt- og juletræer, bærbuske og andre permanente afgrøder)": "intensiv",
    "Ikke-klassificeret landbrug (uden oplysning om afgrødetype)":                 "intensiv",
    "Veje og jernbaner":                                                           "bebygget",
    "Lufthavne og landingsbaner":                                                  "bebygget",
    "Bebyggelse (undtagen erhvervsområder)":                                       "bebygget",
    "Bebyggelse kun med erhverv":                                                  "bebygget",
    "Råstofudvindingsområder (grusgrave o.lign.)":                                 "bebygget",
}

NATUR_GRÆNSE = 30.0   # EU 30x30-mål 2030 (%)

# ─── Alle 98 kommuner (kode → navn) ──────────────────────────────────────────
KOMMUNER = {
    "101": "København", "147": "Frederiksberg", "151": "Ballerup",
    "153": "Brøndby", "155": "Dragør", "157": "Gentofte",
    "159": "Gladsaxe", "161": "Glostrup", "163": "Herlev",
    "165": "Albertslund", "167": "Hvidovre", "169": "Høje-Taastrup",
    "173": "Lyngby-Taarbæk", "175": "Rødovre", "183": "Ishøj",
    "185": "Tårnby", "187": "Vallensbæk", "190": "Furesø",
    "201": "Allerød", "210": "Fredensborg", "217": "Helsingør",
    "219": "Hillerød", "223": "Hørsholm", "230": "Rudersdal",
    "240": "Egedal", "250": "Frederikssund", "253": "Greve",
    "259": "Køge", "260": "Halsnæs", "265": "Roskilde",
    "269": "Solrød", "270": "Gribskov", "306": "Odsherred",
    "316": "Holbæk", "320": "Faxe", "326": "Kalundborg",
    "329": "Ringsted", "330": "Slagelse", "336": "Stevns",
    "340": "Sorø", "350": "Lejre", "360": "Lolland",
    "370": "Næstved", "376": "Guldborgsund", "390": "Vordingborg",
    "400": "Bornholm", "410": "Middelfart", "420": "Assens",
    "430": "Faaborg-Midtfyn", "440": "Kerteminde", "450": "Nyborg",
    "461": "Odense", "479": "Svendborg", "480": "Nordfyns",
    "482": "Langeland", "492": "Ærø", "510": "Haderslev",
    "530": "Billund", "540": "Sønderborg", "550": "Tønder",
    "561": "Esbjerg", "563": "Fanø", "573": "Varde",
    "575": "Vejen", "580": "Aabenraa", "607": "Fredericia",
    "615": "Horsens", "621": "Kolding", "630": "Vejle",
    "657": "Herning", "661": "Holstebro", "665": "Lemvig",
    "671": "Struer", "706": "Syddjurs", "707": "Norddjurs",
    "710": "Favrskov", "727": "Odder", "730": "Randers",
    "740": "Silkeborg", "741": "Samsø", "746": "Skanderborg",
    "751": "Aarhus", "756": "Ikast-Brande", "760": "Ringkøbing-Skjern",
    "766": "Hedensted", "773": "Morsø", "779": "Skive",
    "787": "Thisted", "791": "Viborg", "810": "Brønderslev",
    "813": "Frederikshavn", "820": "Vesthimmerlands", "825": "Læsø",
    "840": "Rebild", "846": "Mariagerfjord", "849": "Jammerbugt",
    "851": "Aalborg", "860": "Hjørring",
}


# ─── Hjælpefunktioner ─────────────────────────────────────────────────────────

def dst_post(variables: list, omraade_koder: list) -> list[dict]:
    """POST til DST API og returnér parsed CSV som liste af dicts."""
    payload = json.dumps({
        "table": "AREALDK2",
        "format": "CSV",
        "lang": "da",
        "variables": [
            {"code": "ARE1",    "values": variables},
            {"code": "OMRÅDE",  "values": omraade_koder},
            {"code": "ENHED",   "values": ["8140"]},   # Andel af samlet område (pct.)
            {"code": "Tid",     "values": ["2024"]},
        ]
    }).encode("utf-8")

    req = urllib.request.Request(
        DST_API, data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "DoughnutDK/1.0"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8-sig")  # strip BOM

    reader = csv.DictReader(io.StringIO(raw), delimiter=";")
    return list(reader)


def dst_tableinfo_omraade() -> dict[str, str]:
    """Hent OMRÅDE code→label mapping fra tableinfo. Returnér {kode: label}."""
    payload = json.dumps({"table": "AREALDK2", "lang": "da"}).encode("utf-8")
    req = urllib.request.Request(
        DST_TABLEINFO, data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "DoughnutDK/1.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        info = json.load(resp)

    for var in info.get("variables", []):
        if var["id"] == "OMRÅDE":
            return {v["id"]: v["text"] for v in var["values"]}
    return {}


def parse_pct(s: str) -> float | None:
    """Parse dansk decimalformat ('53,9' → 53.9). Returnér None ved manglende data."""
    if not s or s.strip() in ("", "..", "x", "X"):
        return None
    try:
        return float(s.strip().replace(".", "").replace(",", "."))
    except ValueError:
        return None


def ratio_natur(pct: float | None) -> float:
    """Natur-ratio: (30 / pct) * 100. Cap ved 999 hvis pct = 0."""
    if pct is None or pct <= 0:
        return 999.0
    return round((NATUR_GRÆNSE / pct) * 100, 2)


def ratio_mod_snit(pct: float | None, national_avg: float) -> float | None:
    """Ratio mod nationalt snit: (pct / national_avg) * 100."""
    if pct is None or national_avg <= 0:
        return None
    return round((pct / national_avg) * 100, 2)


# ─── Trin 1: Byg OMRÅDE label→kode mapping ────────────────────────────────────

def byg_label_til_kode() -> dict[str, str]:
    """Byg reverse-mapping: DST-label → vores kommunekode."""
    print("Henter OMRÅDE-mapping fra DST tableinfo...")
    try:
        kode_til_label = dst_tableinfo_omraade()
    except Exception as e:
        print(f"  ADVARSEL: Kunne ikke hente tableinfo ({e}) - bruger KOMMUNER-dict som fallback")
        # Brug KOMMUNER-dict direkte
        return {v: k for k, v in KOMMUNER.items()}

    label_til_kode = {}
    for dst_kode, label in kode_til_label.items():
        # Kun rigtige kommunekoder: 3 cifre, ikke startende med '0'
        if dst_kode.isdigit() and len(dst_kode) == 3 and not dst_kode.startswith("0"):
            label_til_kode[label] = dst_kode

    print(f"  Fundet {len(label_til_kode)} kommuner i DST AREALDK2")
    return label_til_kode


# ─── Trin 2: Hent nationale referenceværdier ──────────────────────────────────

def hent_nationale_referencevaerdier() -> dict[str, float]:
    """Hent nationale gennemsnit (OMRÅDE=95) til brug som grænseværdi for intensiv + bebygget."""
    print("Henter nationale referenceværdier (OMRÅDE=95)...")
    try:
        rows = dst_post(ALLE_KODER, ["95"])
    except Exception as e:
        print(f"  ADVARSEL: Kunne ikke hente nationale tal ({e})")
        print("  Bruger hardkodede 2024-værdier: intensiv=54.7%, bebygget=14.2%")
        return {"intensiv": 54.7, "bebygget": 14.2}

    natur_sum = intensiv_sum = bebygget_sum = 0.0
    for row in rows:
        # DST returnerer ARE1 som tekstlabel i CSV-svar
        label = row.get("ARE1", "")
        gruppe = ARE1_LABEL_TIL_GRUPPE.get(label)
        pct = parse_pct(row.get("INDHOLD", "")) or 0.0
        if gruppe == "natur":
            natur_sum += pct
        elif gruppe == "intensiv":
            intensiv_sum += pct
        elif gruppe == "bebygget":
            bebygget_sum += pct

    # Sanity check - fald tilbage til hardkodede værdier hvis noget er galt
    if intensiv_sum == 0.0 or bebygget_sum == 0.0:
        print("  ADVARSEL: Nationale tal er 0 - bruger hardkodede 2024-værdier")
        return {"intensiv": 54.7, "bebygget": 14.2}

    print(f"  Nationale værdier 2024:")
    print(f"    Natur + skov:        {natur_sum:.1f}%  (grænse: {NATUR_GRÆNSE}%)")
    print(f"    Intensivt landbrug:  {intensiv_sum:.1f}%  (bruges som grænseværdi)")
    print(f"    Bebygget + veje:     {bebygget_sum:.1f}%  (bruges som grænseværdi)")

    return {"intensiv": intensiv_sum, "bebygget": bebygget_sum}


# ─── Trin 3: Hent kommunedata ─────────────────────────────────────────────────

def hent_kommunedata(label_til_kode: dict) -> dict[str, dict]:
    """
    Hent alle kategorier for alle 98 kommuner i ét API-kald.
    Returnerer {kommune_kode: {ARE1-kode: pct}}.
    """
    print("\nHenter kommunedata fra DST AREALDK2 (alle 98 kommuner, 2024)...")

    # Brug kommunekoder fra vores eget KOMMUNER-dict som primær reference
    alle_koder = list(KOMMUNER.keys())

    try:
        rows = dst_post(ALLE_KODER, alle_koder)
        print(f"  Modtog {len(rows)} datarækker fra API")
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:500]
        print(f"  HTTP {e.code}: {body}")
        print("  Prøver med label-baseret tilgang...")
        # Fallback: brug labels fra tableinfo-mappingen som OMRÅDE-værdier
        dst_koder = [k for k, v in label_til_kode.items()]
        rows = dst_post(ALLE_KODER, list(label_til_kode.values()))

    # Byg reverse: DST-label → vores kode
    # DST returnerer OMRÅDE som label (fx "Thisted"), vi matcher til "787"
    # Primær: match via label_til_kode
    # Fallback: match via KOMMUNER (vores eget navn → kode)
    navn_til_kode = {v: k for k, v in KOMMUNER.items()}
    # Merge med label_til_kode (DST-navne kan afvige lidt)
    for dst_label, kode in label_til_kode.items():
        navn_til_kode[dst_label] = kode

    # Gruppe rækker pr. kommune
    data: dict[str, dict] = {}  # {kode: {ARE1-kode: pct}}

    for row in rows:
        omraade_label = row.get("OMRÅDE", "")
        kode = navn_til_kode.get(omraade_label)
        if kode is None:
            continue  # spring nationale/regionale aggregater over

        are1_label = row.get("ARE1", "")
        pct = parse_pct(row.get("INDHOLD", ""))

        if kode not in data:
            data[kode] = {}

        # Match ARE1-label til vores koder via tableinfo
        # DST returnerer ARE1 som label, vi bruger en simpel heuristik:
        # Se hvilken gruppe labelen hører til
        data[kode][are1_label] = pct

    print(f"  Data fundet for {len(data)} kommuner")
    return data


# ─── Trin 4: Beregn og gem ────────────────────────────────────────────────────

def beregn_og_gem(raw_data: dict, nationale: dict):
    """Beregn sub-indikatorer og skriv CSV."""
    print(f"\nBeregner sub-indikatorer og gemmer til {OUTPUT.relative_to(ROOT)}...")

    resultater = []
    mangler = []

    for kode, navn in sorted(KOMMUNER.items()):
        pct_data = raw_data.get(kode, {})  # {are1_label: pct}

        if not pct_data:
            mangler.append(f"{navn} ({kode})")
            resultater.append({
                "kommune_kode": kode, "kommune_navn": navn,
                "natur_pct": "", "intensiv_pct": "", "bebygget_pct": "",
                "natur_ratio": "", "intensiv_ratio": "", "bebygget_ratio": "",
            })
            continue

        # Summer pct for hver gruppe via ARE1_LABEL_TIL_GRUPPE
        natur_pct = intensiv_pct = bebygget_pct = 0.0
        for label, pct in pct_data.items():
            if pct is None:
                continue
            gruppe = ARE1_LABEL_TIL_GRUPPE.get(label)
            if gruppe == "natur":
                natur_pct += pct
            elif gruppe == "intensiv":
                intensiv_pct += pct
            elif gruppe == "bebygget":
                bebygget_pct += pct

        # Ratios
        natur_ratio    = ratio_natur(natur_pct)
        intensiv_ratio = ratio_mod_snit(intensiv_pct, nationale["intensiv"])
        bebygget_ratio = ratio_mod_snit(bebygget_pct, nationale["bebygget"])

        resultater.append({
            "kommune_kode":   kode,
            "kommune_navn":   navn,
            "natur_pct":      round(natur_pct, 2),
            "intensiv_pct":   round(intensiv_pct, 2),
            "bebygget_pct":   round(bebygget_pct, 2),
            "natur_ratio":    natur_ratio,
            "intensiv_ratio": intensiv_ratio if intensiv_ratio is not None else "",
            "bebygget_ratio": bebygget_ratio if bebygget_ratio is not None else "",
        })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["kommune_kode", "kommune_navn", "natur_pct", "intensiv_pct",
                  "bebygget_pct", "natur_ratio", "intensiv_ratio", "bebygget_ratio"]
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(resultater)

    print(f"  Skrevet {len(resultater)} kommuner til CSV")

    if mangler:
        print(f"  ADVARSEL: Ingen data for {len(mangler)} kommuner: {', '.join(mangler)}")

    # Statistik
    med_data = [r for r in resultater if r["natur_pct"] != ""]
    if med_data:
        natur_pcts = [r["natur_pct"] for r in med_data]
        intensiv_pcts = [r["intensiv_pct"] for r in med_data]
        bebygget_pcts = [r["bebygget_pct"] for r in med_data]
        over_maal = sum(1 for v in natur_pcts if v >= NATUR_GRÆNSE)
        print(f"\n  Natur + skov:       {min(natur_pcts):.1f}% - {max(natur_pcts):.1f}% (snit: {sum(natur_pcts)/len(natur_pcts):.1f}%)")
        print(f"  Kommuner >= 30%:    {over_maal}/{len(med_data)}")
        print(f"  Intensivt landbrug: {min(intensiv_pcts):.1f}% - {max(intensiv_pcts):.1f}% (snit: {sum(intensiv_pcts)/len(intensiv_pcts):.1f}%)")
        print(f"  Bebygget + veje:    {min(bebygget_pcts):.1f}% - {max(bebygget_pcts):.1f}% (snit: {sum(bebygget_pcts)/len(bebygget_pcts):.1f}%)")

    # Thisted
    thisted = next((r for r in resultater if r["kommune_kode"] == "787"), None)
    if thisted and thisted["natur_pct"] != "":
        print(f"\n  Thisted Kommune:")
        print(f"    Natur + skov:       {thisted['natur_pct']}% (grænse: 30%, ratio: {thisted['natur_ratio']})")
        print(f"    Intensivt landbrug: {thisted['intensiv_pct']}% (ratio: {thisted['intensiv_ratio']})")
        print(f"    Bebygget + veje:    {thisted['bebygget_pct']}% (ratio: {thisted['bebygget_ratio']})")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Doughnut Economics — Arealanvendelse (DST AREALDK2 2024)")
    print("=" * 60)
    print(f"Output: {OUTPUT.relative_to(ROOT)}")
    print(f"Naturgrænse: {NATUR_GRÆNSE}% (EU 30x30-mål 2030)")
    print("=" * 60)
    print()

    # Trin 1: Byg label→kode mapping
    label_til_kode = byg_label_til_kode()

    # Trin 2: Hent nationale referenceværdier
    nationale = hent_nationale_referencevaerdier()

    # Trin 3: Hent kommunedata
    raw_data = hent_kommunedata(label_til_kode)

    # Trin 4: Beregn og gem (ARE1-label matching via ARE1_LABEL_TIL_GRUPPE)
    beregn_og_gem(raw_data, nationale)

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
