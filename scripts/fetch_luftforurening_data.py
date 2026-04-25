#!/usr/bin/env python3
"""
Luftforurening pr. danske kommune - NO2 og PM2.5
=================================================
Henter 1x1 km koncentrationsraster fra Danmarks Miljøportals WFS
(DCE/Aarhus Universitets UBM-modelberegninger, 2023).

Grænseværdier (doughnut-kontekst):
  WHO 2021 retningslinjer (videnskabeligt baserede):
    NO2:  10 µg/m³ (årsgennemsnit)
    PM2.5: 5 µg/m³ (årsgennemsnit)

  EU grænseværdier 2008 (politisk kompromis, til sammenligning):
    NO2:  40 µg/m³
    PM2.5: 25 µg/m³

Ratio-konvention (samme som resten af platformen):
  ratio = (faktisk konc. / WHO-grænse) × 100
  ratio > 100 = over grænsen (dårligt)
  ratio < 100 = under grænsen (godt)
  Eksempel: 8 µg/m³ PM2.5 → ratio = (8/5) × 100 = 160

Krav:
  pip install geopandas requests numpy --break-system-packages

Brug:
  python3 fetch_luftforurening_data.py

Output:
  ../data/luftforurening_scores.csv
"""

import sys
import time
import requests
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# ── Konfiguration ─────────────────────────────────────────────────────────────

WFS_BASE   = "https://arld-extgeo.miljoeportal.dk/geoserver/wfs"
DAWA_URL   = "https://api.dataforsyningen.dk/kommuner?format=geojson"
OUTPUT_FIL = "../data/luftforurening_scores.csv"

# WHO 2021 Annual Mean Guidelines (årsgennemsnit)
WHO_NO2  = 10.0  # µg/m³
WHO_PM25 =  5.0  # µg/m³

# WFS lag-navne og property-nøgler
LAG_NO2  = "luft:ID6_Luft_Koncentration_2023_NO2"
LAG_PM25 = "luft:ID7_Luft_Koncentration_2023_PM2_5"

# ── Hjælpefunktioner ──────────────────────────────────────────────────────────

def hent_wfs_lag(lag_navn: str, value_key: str) -> gpd.GeoDataFrame:
    """
    Henter et komplet WFS-lag og returnerer GeoDataFrame med centroid-punkter.
    Geometrien er 1x1 km polygoner - vi bruger centroider for spatial join.
    """
    print(f"  Henter {lag_navn}...")
    params = {
        "service":      "WFS",
        "version":      "2.0.0",
        "request":      "GetFeature",
        "typeNames":    lag_navn,
        "outputFormat": "application/json",
    }
    r = requests.get(
        WFS_BASE, params=params, timeout=120,
        headers={"User-Agent": "DoughnutDK/1.0"}
    )
    r.raise_for_status()
    features = r.json()["features"]
    print(f"    {len(features)} grid-celler, {len(r.content)/1024/1024:.1f} MB")

    xs, ys, vals = [], [], []
    for f in features:
        coords   = f["geometry"]["coordinates"][0]
        x_coords = [c[0] for c in coords]
        y_coords = [c[1] for c in coords]
        xs.append((min(x_coords) + max(x_coords)) / 2)
        ys.append((min(y_coords) + max(y_coords)) / 2)
        vals.append(f["properties"][value_key])

    return gpd.GeoDataFrame(
        {value_key: vals},
        geometry=[Point(x, y) for x, y in zip(xs, ys)],
        crs="EPSG:25832",
    )


def aggreger_per_kommune(grid_gdf: gpd.GeoDataFrame,
                          kommuner: gpd.GeoDataFrame,
                          value_key: str) -> pd.DataFrame:
    """Spatial join og gennemsnit pr. kommune."""
    joined = gpd.sjoin(
        grid_gdf, kommuner[["kode", "navn", "geometry"]],
        how="left", predicate="within"
    )
    return (
        joined.groupby(["kode", "navn"])[value_key]
        .mean()
        .reset_index()
    )

# ── Trin 1: Kommunegrænser ────────────────────────────────────────────────────

print("\n" + "="*60)
print("  Luftforurening (NO2 + PM2.5) pr. kommune - DCE/AU 2023")
print("="*60)

print("\nTrin 1/4: Henter kommunegrænser fra Dataforsyningen...")
try:
    r_kom = requests.get(DAWA_URL, timeout=30, headers={"User-Agent": "DoughnutDK/1.0"})
    r_kom.raise_for_status()
    kommuner = gpd.GeoDataFrame.from_features(r_kom.json()["features"])
    kommuner.crs = "EPSG:4326"
    kommuner = kommuner.to_crs(epsg=25832)
    print(f"  OK: {len(kommuner)} kommuner")
except Exception as e:
    print(f"  FEJL: {e}")
    sys.exit(1)

# ── Trin 2: Hent koncentrationsdata fra WFS ───────────────────────────────────

print("\nTrin 2/4: Henter luftkoncentrationer fra Miljøportalens WFS (DCE/AU 2023)...")
start = time.time()
try:
    no2_gdf  = hent_wfs_lag(LAG_NO2,  "NO2")
    pm25_gdf = hent_wfs_lag(LAG_PM25, "PM2_5")
    print(f"  OK: Download færdig på {time.time()-start:.1f} sek")
except Exception as e:
    print(f"  FEJL: {e}")
    sys.exit(1)

# ── Trin 3: Spatial join og aggregering ──────────────────────────────────────

print("\nTrin 3/4: Spatial join og kommuneaggregering...")
try:
    no2_agg  = aggreger_per_kommune(no2_gdf,  kommuner, "NO2")
    pm25_agg = aggreger_per_kommune(pm25_gdf, kommuner, "PM2_5")
    result   = no2_agg.merge(pm25_agg, on=["kode", "navn"])
    result["NO2"]   = result["NO2"].round(2)
    result["PM2_5"] = result["PM2_5"].round(2)
    print(f"  OK: {len(result)} kommuner aggregeret")
except Exception as e:
    print(f"  FEJL: {e}")
    sys.exit(1)

# ── Trin 4: Beregn doughnut-ratio og gem CSV ──────────────────────────────────

print(f"\nTrin 4/4: Beregner doughnut-ratio og gemmer til {OUTPUT_FIL}...")

result["no2_ratio"]  = (result["NO2"]   / WHO_NO2  * 100).round(1)
result["pm25_ratio"] = (result["PM2_5"] / WHO_PM25 * 100).round(1)

# Rens kommunekode (fjern foranstillet nul: "0101" → "101")
result["kommune_kode"] = result["kode"].astype(str).str.lstrip("0").astype(int)

output = result[[
    "kommune_kode", "navn",
    "NO2", "PM2_5",
    "no2_ratio", "pm25_ratio"
]].rename(columns={
    "navn":  "kommune_navn",
    "NO2":   "no2_ug_m3",
    "PM2_5": "pm25_ug_m3",
})

output = output.sort_values("kommune_kode").reset_index(drop=True)

import os
os.makedirs(os.path.dirname(OUTPUT_FIL), exist_ok=True)
output.to_csv(OUTPUT_FIL, index=False, encoding="utf-8")
print(f"  OK: {OUTPUT_FIL}")

# ── Opsummering ───────────────────────────────────────────────────────────────

print(f"\n{'='*60}")
print(f"  FÆRDIG! Resultat: {len(output)} kommuner")
print(f"{'='*60}")

print(f"\nStatistik NO2 (WHO-grænse: {WHO_NO2} µg/m³):")
print(f"  Min:  {output['no2_ug_m3'].min():.2f} µg/m³")
print(f"  Maks: {output['no2_ug_m3'].max():.2f} µg/m³")
print(f"  Gns:  {output['no2_ug_m3'].mean():.2f} µg/m³")
print(f"  Over WHO-grænse: {(output['no2_ug_m3'] > WHO_NO2).sum()}/{len(output)} kommuner")

print(f"\nStatistik PM2.5 (WHO-grænse: {WHO_PM25} µg/m³):")
print(f"  Min:  {output['pm25_ug_m3'].min():.2f} µg/m³")
print(f"  Maks: {output['pm25_ug_m3'].max():.2f} µg/m³")
print(f"  Gns:  {output['pm25_ug_m3'].mean():.2f} µg/m³")
print(f"  Over WHO-grænse: {(output['pm25_ug_m3'] > WHO_PM25).sum()}/{len(output)} kommuner")

thisted = output[output["kommune_navn"] == "Thisted"]
if not thisted.empty:
    t = thisted.iloc[0]
    print(f"\nThisted Kommune:")
    print(f"  NO2:   {t['no2_ug_m3']} µg/m³  (ratio: {t['no2_ratio']}%)")
    print(f"  PM2.5: {t['pm25_ug_m3']} µg/m³  (ratio: {t['pm25_ratio']}%)")

print(f"\nTop 5 mest forurenede kommuner (PM2.5):")
print(output.nlargest(5, 'pm25_ug_m3')[["kommune_navn","no2_ug_m3","pm25_ug_m3","pm25_ratio"]].to_string(index=False))

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
