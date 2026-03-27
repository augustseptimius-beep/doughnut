#!/usr/bin/env python3
"""
====================================================================
  Biodiversitetsscore pr. danske kommune
  Baseret på Miljøportalens biodiversitetskort (2021)
====================================================================

HVAD SCRIPTET GIVER DIG:
  En Excel-fil der viser hvor stor en andel af hver kommunes areal
  der har væsentlige naturværdier (bioscore >= 8), sammenholdt med
  30x30-målet om 30% beskyttet natur i 2030.

  Tærskelværdier er baseret på DCE/AU's egen vejledning (SR456):
    < 4   = uvæsentlig i naturforvaltningsøjemed
    4-7   = potentielt interessant
    8-11  = sandsynligvis væsentlige naturværdier  ← vores grænse
    12-19 = uerstattelige levesteder for rødlistede arter

KRAV - installer disse pakker én gang i terminalen:
  pip3 install geopandas rasterio rasterstats openpyxl requests numpy

SÅDAN KØRER DU SCRIPTET:
  1. Placer biodiversitet_2021.zip i samme mappe som dette script
  2. Åbn en terminal i den samme mappe
  3. Skriv: python3 biodiversitet_kommuner.py
  4. Vent 3-8 minutter (afhænger af din computer)
  5. Åbn den nye fil: biodiversitet_kommuner.xlsx

====================================================================
"""

import os
import sys
import subprocess
import numpy as np
import geopandas as gpd
import pandas as pd
from rasterstats import zonal_stats

# ── Konfiguration ─────────────────────────────────────────────────────────────

ZIP_FIL      = "biodiversitet_2021.zip"
RASTER_NAVN  = "Bioscore_tiff.tif"
ARBEJDSMAPPE = "biodiversitet_data"
OUTPUT_FIL   = "biodiversitet_kommuner.xlsx"

# Planetary boundary-grænser (baseret på 30x30-målet og DCE's tærskelværdier)
TÆRSKEL_VÆSENTLIG    = 8     # Bioscore >= 8  = "sandsynligvis væsentlige naturværdier" (DCE/AU)
TÆRSKEL_UERSTATTELIG = 12    # Bioscore >= 12 = "uerstattelige levesteder for rødlistede arter" (DCE/AU)
MÅL_PROCENT          = 30.0  # 30x30-målet: 30% af arealet skal have væsentlig natur
KRITISK_PROCENT      = 15.0  # Under halvdelen af målet = kritisk
MÅL_UERSTATTELIG     = 10.0  # EU's mål: 10% strengt beskyttet natur (proxy for uerstattelig)

# Kommunegrænser fra DAWA (Danmarks Adressers Web API) - åbent og gratis
DAWA_URL = "https://dawa.aws.dk/kommuner?format=geojson"

# ── Tjek at ZIP-filen findes ──────────────────────────────────────────────────

if not os.path.exists(ZIP_FIL):
    print(f"\n❌ FEJL: Kan ikke finde filen '{ZIP_FIL}'")
    print(f"   Placer ZIP-filen i samme mappe som dette script og prøv igen.")
    sys.exit(1)

# ── Trin 1: Udpak Bioscore-raster fra ZIP ────────────────────────────────────

print("\n" + "="*60)
print("  Biodiversitet og planetary boundaries pr. kommune")
print("="*60)
print(f"\nTrin 1/4: Udpakker '{RASTER_NAVN}' fra ZIP-filen...")
print("  (Dette kan tage lidt tid - filen er ~1,7 GB)")

os.makedirs(ARBEJDSMAPPE, exist_ok=True)
raster_sti = os.path.join(ARBEJDSMAPPE, RASTER_NAVN)

if not os.path.exists(raster_sti):
    kørsels_resultat = subprocess.run(
        ["unzip", "-j", ZIP_FIL, RASTER_NAVN, "-d", ARBEJDSMAPPE],
        capture_output=True, text=True
    )
    if kørsels_resultat.returncode != 0:
        print(f"\n❌ FEJL ved udpakning:\n{kørsels_resultat.stderr}")
        sys.exit(1)
    print(f"  ✓ Raster udpakket til: {raster_sti}")
else:
    print(f"  ✓ Bruger allerede udpakket raster (springer over)")

# ── Trin 2: Hent kommunegrænser fra DAWA ─────────────────────────────────────

print("\nTrin 2/4: Henter kommunegrænser fra DAWA...")

try:
    kommuner = gpd.read_file(DAWA_URL)
    print(f"  ✓ {len(kommuner)} kommuner hentet")
except Exception as e:
    print(f"\n❌ FEJL ved hentning af kommunegrænser: {e}")
    print("   Tjek din internetforbindelse og prøv igen.")
    sys.exit(1)

kommuner = kommuner.to_crs(epsg=25832)

# ── Trin 3: Beregn naturandel pr. kommune ────────────────────────────────────

print("\nTrin 3/4: Beregner naturandel pr. kommune...")
print("  (Dette tager typisk 2-8 minutter afhængigt af din computer)")

# Definer funktioner der beregner naturandele for begge tærskelværdier
def pct_vasentlig(pixels):
    """Andel (%) af pixels med bioscore >= 8 (væsentlige naturværdier)."""
    gyldige = pixels.compressed()
    if len(gyldige) == 0:
        return 0.0
    return float((gyldige >= TÆRSKEL_VÆSENTLIG).sum()) / len(gyldige) * 100

def pct_uerstattelig(pixels):
    """Andel (%) af pixels med bioscore >= 12 (uerstattelige levesteder)."""
    gyldige = pixels.compressed()
    if len(gyldige) == 0:
        return 0.0
    return float((gyldige >= TÆRSKEL_UERSTATTELIG).sum()) / len(gyldige) * 100

try:
    stats = zonal_stats(
        kommuner,
        raster_sti,
        stats=["mean", "count"],
        add_stats={
            "pct_vasentlig":    pct_vasentlig,
            "pct_uerstattelig": pct_uerstattelig,
        },
        nodata=-9999,
        all_touched=False,
    )
    print("  ✓ Beregning færdig")
except Exception as e:
    print(f"\n❌ FEJL under beregning: {e}")
    sys.exit(1)

# ── Trin 4: Byg resultat-tabel med planetary boundary-status ─────────────────

print(f"\nTrin 4/4: Gemmer resultat til '{OUTPUT_FIL}'...")

navn_kolonne = "navn" if "navn" in kommuner.columns else kommuner.columns[1]
kode_kolonne = "kode" if "kode" in kommuner.columns else None

# Beregn status for hver kommune
def status_vasentlig(pct):
    """Status for andel med bioscore >= 8, målt mod 30x30-målet."""
    if pct >= MÅL_PROCENT:
        return "✅ Inden for grænsen"
    elif pct >= KRITISK_PROCENT:
        return "⚠️ Under målet"
    else:
        return "🔴 Kritisk"

def status_uerstattelig(pct):
    """Status for andel med bioscore >= 12, målt mod EU's 10%-mål."""
    if pct >= MÅL_UERSTATTELIG:
        return "✅ Inden for grænsen"
    elif pct >= MÅL_UERSTATTELIG / 2:
        return "⚠️ Under målet"
    else:
        return "🔴 Kritisk"

pct_v_liste = [round(s["pct_vasentlig"],    1) if s["pct_vasentlig"]    is not None else 0.0 for s in stats]
pct_u_liste = [round(s["pct_uerstattelig"], 1) if s["pct_uerstattelig"] is not None else 0.0 for s in stats]

resultat = pd.DataFrame({
    "Kommune":                       kommuner[navn_kolonne].values,
    "Natur >= 8 (%)":                pct_v_liste,
    "Status (30x30-mål)":            [status_vasentlig(p)    for p in pct_v_liste],
    "Uerstattelig natur >= 12 (%)":  pct_u_liste,
    "Status (EU 10%-mål)":           [status_uerstattelig(p) for p in pct_u_liste],
    "Bioscore gns.":                 [round(s["mean"], 2) if s["mean"] is not None else None for s in stats],
    "Antal pixels":                  [s["count"] for s in stats],
})

if kode_kolonne:
    resultat.insert(1, "Kommunekode", kommuner[kode_kolonne].values)

resultat = resultat.sort_values("Natur >= 8 (%)", ascending=False).reset_index(drop=True)
resultat.index += 1

# Gem til Excel
with pd.ExcelWriter(OUTPUT_FIL, engine="openpyxl") as writer:
    resultat.to_excel(
        writer,
        sheet_name="Biodiversitet",
        index=True,
        index_label="Rang",
    )
    ws = writer.sheets["Biodiversitet"]
    for kolonne in ws.columns:
        max_bredde = max(len(str(celle.value or "")) for celle in kolonne)
        ws.column_dimensions[kolonne[0].column_letter].width = max_bredde + 3

# ── Færdig - vis opsummering i terminalen ─────────────────────────────────────

inden_for_v = (resultat["Status (30x30-mål)"]  == "✅ Inden for grænsen").sum()
under_mål_v = (resultat["Status (30x30-mål)"]  == "⚠️ Under målet").sum()
kritisk_v   = (resultat["Status (30x30-mål)"]  == "🔴 Kritisk").sum()
inden_for_u = (resultat["Status (EU 10%-mål)"] == "✅ Inden for grænsen").sum()

print(f"\n{'='*60}")
print(f"  ✅ FÆRDIG! Fil gemt: {OUTPUT_FIL}")
print(f"{'='*60}")
print(f"\nOpsummering - Indicator 1: Natur >= 8 (30x30-målet, 30%):")
print(f"  ✅ Inden for grænsen (>= 30%): {inden_for_v} kommuner")
print(f"  ⚠️  Under målet (15-30%):      {under_mål_v} kommuner")
print(f"  🔴 Kritisk (< 15%):            {kritisk_v} kommuner")
print(f"\nOpsummering - Indicator 2: Uerstattelig natur >= 12 (EU 10%-mål):")
print(f"  ✅ Inden for grænsen (>= 10%): {inden_for_u} kommuner")
print(f"\nTop 10 kommuner efter naturandel (>= 8):\n")
print(resultat[["Kommune", "Natur >= 8 (%)", "Status (30x30-mål)", "Uerstattelig natur >= 12 (%)", "Status (EU 10%-mål)"]].head(10).to_string())

thisted = resultat[resultat["Kommune"] == "Thisted"]
if not thisted.empty:
    t = thisted.iloc[0]
    print(f"\nThisted Kommune (rang {thisted.index[0]}):")
    print(f"  Natur >= 8:  {t['Natur >= 8 (%)']}%  |  {t['Status (30x30-mål)']}")
    print(f"  Natur >= 12: {t['Uerstattelig natur >= 12 (%)']}%  |  {t['Status (EU 10%-mål)']}")
