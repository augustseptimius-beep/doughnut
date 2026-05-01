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
  Tid     = 2024

Metode:
  1. Hent vandindvinding (mio. m³) pr. kommune fra VANDIND
  2. Hent befolkningstal fra FOLK1A (seneste kvartal)
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
  Kolonner: kommune_kode, kommune_navn, vandindvinding_m3_per_person, vandindvinding_ratio

Kør fra projektets rodmappe:
  python3 scripts/fetch_vandindvinding_data.py
"""

import csv
import time
import requests
from io import StringIO
from pathlib import Path

# ── Konstanter ────────────────────────────────────────────────────────────────

BASE_URL   = "https://api.statbank.dk/v1/data"
OUTPUT_FIL = Path("data/vandindvinding_scores.csv")
DELAY      = 0.6   # sekunder mellem API-kald

# Minimumsgrænse for m³/person - under dette er data et registreringsartefakt
MIN_M3_PER_PERSON = 10.0

# Alle 98 kommunekoder (samme liste som statbank_fetcher.py)
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


# ── API-hjælper ───────────────────────────────────────────────────────────────

def fetch_csv_raw_url(url: str) -> list[dict]:
    """Henter data fra en URL med bogstavelige kommaer (ingen URL-encoding).
    Statistikbanken kræver literal kommaer i OMRÅDE-parameteren."""
    time.sleep(DELAY)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    reader = csv.DictReader(StringIO(resp.text), delimiter=";")
    return list(reader)


def fetch_csv(table_id: str, params: dict) -> list[dict]:
    """Henter data fra Statistikbanken som CSV og returnerer liste af dicts."""
    time.sleep(DELAY)
    url = f"{BASE_URL}/{table_id}/CSV"
    resp = requests.get(url, params={"lang": "da", **params}, timeout=30)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    reader = csv.DictReader(StringIO(resp.text), delimiter=";")
    return list(reader)


def parse_float(s: str) -> float | None:
    """Konverterer Statistikbank-tal (dansk format, '..' = mangler) til float."""
    if not s or s.strip() in ("..", "x", "X", ""):
        return None
    try:
        return float(s.strip().replace(".", "").replace(",", "."))
    except ValueError:
        return None


# ── Trin 1: Vandindvinding (VANDIND) ─────────────────────────────────────────

def hent_vandindvinding() -> dict[str, float | None]:
    """
    Henter vandindvinding fra almene vandværker (mio. m³) pr. kommune.
    Returnerer {kommune_kode: mio_m3} - None hvis data mangler.
    """
    print("Henter vandindvinding (VANDIND, INDKAT=100, 2024)...")

    # Alle kommunekoder kommasepareret.
    # OBS: requests.get(params=...) URL-encoder kommaerne (101%2C147) hvilket
    # Statistikbanken ikke accepterer - vi bygger URL'en manuelt.
    koder = ",".join(KOMMUNER.keys())
    url = (
        f"{BASE_URL}/VANDIND/CSV?lang=da"
        f"&VANDTYP=TOTVAND&INDKAT=100&Tid=2024&OMRÅDE={koder}"
    )
    rows = fetch_csv_raw_url(url)

    # VANDIND returnerer kommunenavn i OMRÅDE-kolonnen, ikke kode.
    # Byg omvendt opslag: navn (lowercase) -> kode
    navn_til_kode = {v.lower(): k for k, v in KOMMUNER.items()}

    result = {}
    for row in rows:
        # Kolonnenavne kan variere - find den relevante
        omraade = (row.get("OMRÅDE") or row.get("område") or "").strip().lower()
        indhold = row.get("INDHOLD") or row.get("indhold") or ""

        # Match navn til kode (fuzzy: kommunenavn kan have æ/ø/å-varianter)
        kode = navn_til_kode.get(omraade)
        if not kode:
            # Prøv delvis match
            for navn, k in navn_til_kode.items():
                if navn in omraade or omraade in navn:
                    kode = k
                    break

        if kode:
            result[kode] = parse_float(indhold)

    print(f"  Modtaget data for {len(result)} kommuner")
    mangler = [k for k in KOMMUNER if k not in result]
    if mangler:
        print(f"  Ingen data for: {[KOMMUNER[k] for k in mangler[:5]]}")

    return result


# ── Trin 2: Befolkningstal (FOLK1A) ──────────────────────────────────────────

def hent_befolkning() -> dict[str, int | None]:
    """
    Henter befolkningstal pr. kommune fra FOLK1A (seneste kvartal).
    Returnerer {kommune_kode: befolkning}.
    """
    print("Henter befolkningstal (FOLK1A, 2025K1)...")

    koder = ",".join(KOMMUNER.keys())
    url = (
        f"{BASE_URL}/FOLK1A/CSV?lang=da"
        f"&KØN=TOT&ALDER=IALT&CIVILSTAND=TOT&Tid=2025K1&OMRÅDE={koder}"
    )
    rows = fetch_csv_raw_url(url)

    navn_til_kode = {v.lower(): k for k, v in KOMMUNER.items()}

    result = {}
    for row in rows:
        omraade = (row.get("OMRÅDE") or row.get("område") or "").strip().lower()
        indhold = row.get("INDHOLD") or row.get("indhold") or ""

        kode = navn_til_kode.get(omraade)
        if not kode:
            for navn, k in navn_til_kode.items():
                if navn in omraade or omraade in navn:
                    kode = k
                    break

        if kode:
            val = parse_float(indhold)
            result[kode] = int(val) if val is not None else None

    print(f"  Modtaget befolkningstal for {len(result)} kommuner")
    return result


# ── Trin 3: Beregn og gem ─────────────────────────────────────────────────────

def beregn_og_gem(
    vandind: dict[str, float | None],
    befolkning: dict[str, int | None],
) -> None:
    """Beregner m³/person og ratio, skriver CSV."""

    print("\nBeregner vandindvinding pr. person og ratio...")

    resultater = []

    for kode, navn in KOMMUNER.items():
        mio_m3 = vandind.get(kode)
        bef = befolkning.get(kode)

        # Beregn m³/person
        if mio_m3 is not None and bef and bef > 0:
            m3_per_person = (mio_m3 * 1_000_000) / bef
        else:
            m3_per_person = None

        # Filtrer data-artefakter (bykommuner med vandværk registreret andetsteds)
        if m3_per_person is not None and m3_per_person < MIN_M3_PER_PERSON:
            print(f"  ⚠ {navn}: {m3_per_person:.1f} m³/person - sætter til None (data-artefakt)")
            m3_per_person = None

        resultater.append({
            "kommune_kode": kode,
            "kommune_navn": navn,
            "vandindvinding_m3_per_person": m3_per_person,
            "vandindvinding_mio_m3": mio_m3,
            "befolkning": bef,
        })

    # Nationalt befolkningsvægtet gennemsnit (kun kommuner med gyldige data)
    valide = [r for r in resultater if r["vandindvinding_m3_per_person"] is not None]
    if not valide:
        print("FEJL: Ingen gyldige data til rådighed.")
        return

    total_m3 = sum(r["vandindvinding_m3_per_person"] * r["befolkning"] for r in valide)
    total_bef = sum(r["befolkning"] for r in valide)
    landssnit = total_m3 / total_bef
    print(f"  Nationalt gennemsnit (befolkningsvægtet): {landssnit:.1f} m³/person")
    print(f"  Kommuner med gyldige data: {len(valide)}/98")

    # Beregn ratio
    for r in resultater:
        if r["vandindvinding_m3_per_person"] is not None:
            r["vandindvinding_ratio"] = round(
                (r["vandindvinding_m3_per_person"] / landssnit) * 100, 2
            )
        else:
            r["vandindvinding_ratio"] = ""

    # Statistik
    ratios = [r["vandindvinding_ratio"] for r in resultater if r["vandindvinding_ratio"] != ""]
    print(f"  Ratio-range: {min(ratios):.0f} - {max(ratios):.0f}")
    over_100 = sum(1 for r in ratios if r > 100)
    print(f"  Kommuner over landsgennemsnit (>100): {over_100}/{len(ratios)}")

    # Thisted
    thisted = next((r for r in resultater if r["kommune_kode"] == "787"), None)
    if thisted:
        print(f"\n  Thisted Kommune:")
        print(f"    Vandindvinding: {thisted.get('vandindvinding_mio_m3')} mio. m³")
        print(f"    m³/person: {thisted['vandindvinding_m3_per_person']:.1f}" if thisted['vandindvinding_m3_per_person'] else "    m³/person: None")
        print(f"    Ratio: {thisted['vandindvinding_ratio']}")

    # Gem CSV
    OUTPUT_FIL.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "kommune_kode", "kommune_navn",
        "vandindvinding_m3_per_person", "vandindvinding_ratio",
    ]
    with open(OUTPUT_FIL, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(sorted(resultater, key=lambda r: r["kommune_kode"]))

    print(f"\n✓ Gemt: {OUTPUT_FIL} ({len(resultater)} kommuner)")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("Doughnut Economics - Vandindvinding pr. capita (DST VANDIND)")
    print("=" * 65)
    print(f"Kilde: Statistikbanken VANDIND, INDKAT=100 (alment vandværk), 2024")
    print(f"Min. grænse for gyldige data: {MIN_M3_PER_PERSON} m³/person")
    print()

    vandind    = hent_vandindvinding()
    befolkning = hent_befolkning()
    beregn_og_gem(vandind, befolkning)

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
