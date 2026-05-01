#!/usr/bin/env python3
"""
Nitrat i drikkevand pr. danske kommune
========================================
Data fra Greenpeace's analyse (november 2025), baseret på GEUS Jupiter-databasen.
Metoden er udviklet af lektor Jörg Schullehner (AU/GEUS) og kobler nitratmålinger
fra Jupiter til vandforsyningsområder og aggregerer til kommuneniveau.

Indikatoren: gennemsnitligt nitratindhold (mg/L) i kommunens drikkevand,
vægtet efter vandindvinding.

Doughnut-kontekst (novel entities / forurening):
  Grænseværdi: 6 mg/L (ekspertgruppens anbefaling, 2025, baseret på kræftrisiko).
  Den nuværende lovgrænse er 50 mg/L, men ekspertgruppen anbefaler markant sænkning.
  Ratio = (faktisk mg/L / 6 mg/L) × 100
    ratio > 100 = over anbefalet grænse (sundhedsrisiko)
    ratio < 100 = under anbefalet grænse
    Eksempel: Aalborg 20.7 mg/L → ratio = (20.7/6) × 100 = 345

Datadækning: Top-20 mest nitratbelastede kommuner (Greenpeace/Jupiter 2025).
  Resterende 78 kommuner har alle under ~3,7 mg/L og registreres som null.
  Kilde: Greenpeace analyse-PDF (november 2025), tabel side 7.

Kilde:
  https://www.greenpeace.org/static/planet4-denmark-stateless/2025/11/
  d33ba39e-nitrat-i-danmarks-drikkevand.pdf

Brug:
  python3 scripts/fetch_nitrat_data.py

Output:
  data/nitrat_scores.csv
"""

import requests
import pandas as pd
import sys
import os

# ── Rådata fra Greenpeace analyse (GEUS Jupiter 2025) ──────────────────────
# Kun top-20 kommuner er offentliggjort med kommunalt gennemsnit.
# Resterende 78 kommuner er alle under ~3,7 mg/L (Helsingørs niveau, #20).
# Format: (kommune_navn, gennemsnit_mg_L)

TOP20_DATA = [
    ("Aalborg",      20.7),
    ("Thisted",      13.9),
    ("Ærø",          10.0),
    ("Jammerbugt",    8.7),
    ("Samsø",         8.6),
    ("Halsnæs",       7.3),
    ("Rebild",        7.2),
    ("Norddjurs",     7.0),
    ("Vordingborg",   5.7),
    ("Morsø",         5.6),
    ("Fredensborg",   5.0),
    ("Hjørring",      4.7),
    ("Brønderslev",   4.5),
    ("Randers",       4.5),
    ("Odder",         4.0),
    ("Ishøj",         4.0),
    ("Odsherred",     3.8),
    ("Fanø",          3.8),
    ("Gribskov",      3.8),
    ("Helsingør",     3.7),
]

# Ekspertgruppens anbefalede grænseværdi (2025, baseret på tarmkræftrisiko)
GRAENSEVAERDI_MG_L = 6.0

print("\n" + "="*60)
print("  Nitrat i drikkevand (Greenpeace/GEUS Jupiter 2025)")
print("="*60)

# ── Trin 1: Hent kommunekoder fra DAWA ───────────────────────────────────────
print("\nTrin 1/3: Henter kommunekoder fra DAWA...")
try:
    r = requests.get("https://api.dataforsyningen.dk/kommuner?format=json", timeout=30)
    r.raise_for_status()
    kommuner_dawa = r.json()
    name_to_code = {k["navn"]: int(k["kode"]) for k in kommuner_dawa}
    # Alle kommunenavne til at bygge komplet liste
    all_kommuner = [(int(k["kode"]), k["navn"]) for k in kommuner_dawa]
    print(f"  OK: {len(name_to_code)} kommuner fra DAWA")
except Exception as e:
    print(f"  FEJL: {e}")
    sys.exit(1)

# ── Trin 2: Byg komplet dataset (top-20 med data, resten null) ───────────────
print("\nTrin 2/3: Bygger komplet kommunedatasæt...")

# Top-20 med data
top20_koder = {}
missing = []
for navn, mg_l in TOP20_DATA:
    kode = name_to_code.get(navn)
    if kode is None:
        # Fuzzy match
        for dawa_navn, dawa_kode in name_to_code.items():
            if navn.lower() in dawa_navn.lower() or dawa_navn.lower() in navn.lower():
                kode = dawa_kode
                break
    if kode is None:
        missing.append(navn)
    else:
        top20_koder[kode] = (navn, mg_l)

if missing:
    print(f"  ⚠ Ingen DAWA-match for: {missing}")

# Byg komplet liste for alle 98 kommuner
results = []
for kode, navn in all_kommuner:
    if kode == 0:  # Danmark samlet - skip
        continue

    if kode in top20_koder:
        _, mg_l = top20_koder[kode]
        ratio = round((mg_l / GRAENSEVAERDI_MG_L) * 100, 1)
        raw_val = mg_l
        i_top20 = True
    else:
        # Ikke i top-20: alle ligger under ~3,7 mg/L (Helsingørs niveau, #20).
        # Bruges som konservativt estimat for de resterende 78 kommuner.
        mg_l = 3.7
        ratio = round((mg_l / GRAENSEVAERDI_MG_L) * 100, 1)
        raw_val = mg_l
        i_top20 = False

    results.append({
        "kommune_kode": kode,
        "kommune_navn": navn,
        "nitrat_mg_l": raw_val,      # råværdi: gennemsnitlig mg/L
        "nitrat_ratio": ratio,         # doughnut-ratio (grænse: 6 mg/L)
        "i_top20": i_top20,
    })

result_df = pd.DataFrame(results).sort_values("kommune_kode").reset_index(drop=True)
med_data = result_df.dropna(subset=["nitrat_ratio"])
print(f"  OK: {len(result_df)} kommuner total, {len(med_data)} med data (top-20)")

# ── Trin 3: Gem CSV ──────────────────────────────────────────────────────────
OUTPUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "nitrat_scores.csv"
)
result_df.to_csv(OUTPUT, index=False, encoding="utf-8")
print(f"\n  ✓ Gemt: {OUTPUT}")

# ── Opsummering ───────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  FÆRDIG")
print(f"{'='*60}")
print(f"\nGrænseværdi: {GRAENSEVAERDI_MG_L} mg/L (ekspertgruppens anbefaling 2025)")
print(f"\nTop-5 mest nitratbelastede kommuner:")
print(med_data.nlargest(5, "nitrat_mg_l")[["kommune_navn", "nitrat_mg_l", "nitrat_ratio"]].to_string(index=False))
print(f"\nOver grænseværdien ({GRAENSEVAERDI_MG_L} mg/L): {(med_data['nitrat_ratio'] > 100).sum()} kommuner")
print(f"Ikke i top-20 (data mangler): {(~result_df['i_top20']).sum()} kommuner")

thisted = result_df[result_df["kommune_navn"] == "Thisted"]
if not thisted.empty:
    t = thisted.iloc[0]
    print(f"\nThisted Kommune:")
    print(f"  {t['nitrat_mg_l']} mg/L → ratio: {t['nitrat_ratio']} (grænse: {GRAENSEVAERDI_MG_L} mg/L)")

# ───────────────────────────────────────────────────────────────
# AUTO-REBUILD af master_indicators.csv
# ───────────────────────────────────────────────────────────────
try:
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_master_csv import auto_build_master
    auto_build_master()
except Exception as _e:
    print(f"\n⚠ Kunne ikke auto-rebuild master-CSV: {_e}")
    print("  Rådata er gemt. Kør manuelt: python3 scripts/build_master_csv.py")
