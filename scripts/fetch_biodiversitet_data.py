#!/usr/bin/env python3
"""
Biodiversitetsscore pr. danske kommune
=======================================
Baseret på Miljøportalens biodiversitetskort (2021), AU/DCE rapport nr. 456.

Tærskelværdier (DCE/AU SR456):
  Bioscore >= 8  = "sandsynligvis væsentlige naturværdier"
  Bioscore >= 12 = "uerstattelige levesteder for rødlistede arter"

Planetary boundary-grænser:
  biodiversitet_ratio    = (pct natur >= 8  / 30%) × 100   [30x30-målet]
  uerstattelig_ratio     = (pct natur >= 12 / 10%) × 100   [EU 10%-mål]
  ratio > 100 = inden for grænsen, ratio < 100 = underskud

Krav:
  pip3 install geopandas rasterio rasterstats requests numpy

Brug:
  python3 fetch_biodiversitet_data.py --zip ../biodiversitet_2021.zip

Output:
  ../data/biodiversitet_scores.csv
"""

import argparse
import csv
import os
import sys
import subprocess

import numpy as np
import geopandas as gpd
from rasterstats import zonal_stats

# ── Konstanter ────────────────────────────────────────────────────────────────

RASTER_NAVN          = "Bioscore_tiff.tif"
ARBEJDSMAPPE         = "biodiversitet_tmp"
DAWA_URL             = "https://dawa.aws.dk/kommuner?format=geojson"

TÆRSKEL_VÆSENTLIG    = 8
TÆRSKEL_UERSTATTELIG = 12
MÅL_VASENTLIG        = 30.0   # 30x30-målet
MÅL_UERSTATTELIG     = 10.0   # EU strengt beskyttet

# ── Argument-parsing ──────────────────────────────────────────────────────────

parser = argparse.ArgumentParser(description="Hent biodiversitetsdata pr. kommune")
parser.add_argument("--zip",    default="../biodiversitet_2021.zip", help="Sti til ZIP-filen")
parser.add_argument("--output", default="../data/biodiversitet_scores.csv", help="Output CSV")
args = parser.parse_args()

ZIP_FIL    = args.zip
OUTPUT_FIL = args.output

# ── Trin 1: Udpak raster ──────────────────────────────────────────────────────

if not os.path.exists(ZIP_FIL):
    print(f"FEJL: Kan ikke finde '{ZIP_FIL}'")
    print(f"  Angiv stien med: --zip /sti/til/biodiversitet_2021.zip")
    sys.exit(1)

print("Trin 1/4: Finder Bioscore-raster...")

# Tjek kendte steder for allerede udpakket raster (fra biodiversitet_kommuner.py)
KENDTE_STEDER = [
    os.path.join("..", "biodiversitet_data", RASTER_NAVN),
    os.path.join(ARBEJDSMAPPE, RASTER_NAVN),
    RASTER_NAVN,
]
raster_sti = next((s for s in KENDTE_STEDER if os.path.exists(s)), None)

if raster_sti:
    print(f"  OK: Bruger eksisterende raster ({raster_sti})")
else:
    # Udpak fra ZIP
    if not os.path.exists(ZIP_FIL):
        print(f"FEJL: Kan ikke finde ZIP-filen '{ZIP_FIL}'")
        print(f"  Angiv stien med: --zip /sti/til/biodiversitet_2021.zip")
        sys.exit(1)
    os.makedirs(ARBEJDSMAPPE, exist_ok=True)
    raster_sti = os.path.join(ARBEJDSMAPPE, RASTER_NAVN)
    resultat = subprocess.run(
        ["unzip", "-j", ZIP_FIL, RASTER_NAVN, "-d", ARBEJDSMAPPE],
        capture_output=True, text=True
    )
    if resultat.returncode != 0:
        print(f"FEJL ved udpakning: {resultat.stderr}")
        sys.exit(1)
    print(f"  OK: {raster_sti}")

# ── Trin 2: Hent kommunegrænser ───────────────────────────────────────────────

print("Trin 2/4: Henter kommunegrænser fra DAWA...")
try:
    kommuner = gpd.read_file(DAWA_URL)
    kommuner = kommuner.to_crs(epsg=25832)
    print(f"  OK: {len(kommuner)} kommuner")
except Exception as e:
    print(f"FEJL: {e}")
    sys.exit(1)

# ── Trin 3: Beregn naturandele ────────────────────────────────────────────────

print("Trin 3/4: Beregner naturandele pr. kommune (2-8 min)...")

def pct_vasentlig(pixels):
    gyldige = pixels.compressed()
    if len(gyldige) == 0:
        return 0.0
    return float((gyldige >= TÆRSKEL_VÆSENTLIG).sum()) / len(gyldige) * 100

def pct_uerstattelig(pixels):
    gyldige = pixels.compressed()
    if len(gyldige) == 0:
        return 0.0
    return float((gyldige >= TÆRSKEL_UERSTATTELIG).sum()) / len(gyldige) * 100

try:
    stats = zonal_stats(
        kommuner,
        raster_sti,
        stats=["mean"],
        add_stats={
            "pct_vasentlig":    pct_vasentlig,
            "pct_uerstattelig": pct_uerstattelig,
        },
        nodata=-9999,
        all_touched=False,
    )
    print("  OK")
except Exception as e:
    print(f"FEJL: {e}")
    sys.exit(1)

# ── Trin 4: Gem CSV ───────────────────────────────────────────────────────────

print(f"Trin 4/4: Gemmer til {OUTPUT_FIL}...")

os.makedirs(os.path.dirname(OUTPUT_FIL), exist_ok=True)

with open(OUTPUT_FIL, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "kommune_kode",
        "kommune_navn",
        "pct_vasentlig_natur",
        "pct_uerstattelig_natur",
        "bioscore_mean",
        "biodiversitet_ratio",
        "uerstattelig_ratio",
    ])

    for i, row in kommuner.iterrows():
        s = stats[i]
        pct_v = round(s["pct_vasentlig"]    or 0.0, 2)
        pct_u = round(s["pct_uerstattelig"] or 0.0, 2)
        mean  = round(s["mean"]             or 0.0, 2)

        # Ratio: mål / faktisk andel × 100 - samme konvention som CO2:
        # ratio > 100 = under målet (shortfall/dårligt), ratio < 100 = over målet (godt)
        # Eks: 15% natur ud af 30% mål → ratio = (30/15)*100 = 200 (shortfall)
        #      45% natur ud af 30% mål → ratio = (30/45)*100 = 67  (inden for grænsen)
        bio_ratio = round(MÅL_VASENTLIG    / pct_v * 100, 2) if pct_v > 0 else 999.0
        uer_ratio = round(MÅL_UERSTATTELIG / pct_u * 100, 2) if pct_u > 0 else 999.0

        # Strip foranstillet nul fra kommunekode (DAWA: "0101" → "101")
        kode = str(int(row["kode"]))

        writer.writerow([
            kode,
            row["navn"],
            pct_v,
            pct_u,
            mean,
            bio_ratio,
            uer_ratio,
        ])

print(f"  OK: {OUTPUT_FIL}")
print("\nFærdig.")

# ───────────────────────────────────────────────────────────────
# AUTO-REBUILD af master_indicators.csv
# Tilføjet 2026: efter denne fetch er færdig, regenereres master-CSV'en
# automatisk så webapp viser de nye data uden manuel ekstra kommando.
# Hvis build fejler, gemmes rådata stadigvæk - kør manuelt:
#   python3 scripts/build_master_csv.py
# ───────────────────────────────────────────────────────────────
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_master_csv import auto_build_master
    auto_build_master()
except Exception as _e:
    print(f"\n⚠ Kunne ikke auto-rebuild master-CSV: {_e}")
    print("  Rådata er gemt. Kør manuelt: python3 scripts/build_master_csv.py")
