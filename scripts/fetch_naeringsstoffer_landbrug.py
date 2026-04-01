#!/usr/bin/env python3
"""
Kvælstof-loft (økologisk grænse) pr. danske kommune
====================================================
Henter max bæredygtig N-tilførsel (malbelas_n) pr. kystvandopland fra
Vandområdeplan 3 (VP3) WFS og aggregerer til kommuneniveau.

Datakilde:
  MiljøGIS VP3 2. endelig 2025 - lag: vp3_2e2025_opl_marin_inds
  WFS: wfs2-miljoegis.mim.dk/vp3_2endelig2025/ows
  Feltet `malbelas_n` = max bæredygtig N-tilførsel i tons N pr. kystvandopland.
  Dette er det "økologiske loft" fra vandområdeplanerne - den N-grænse
  vandmiljøet kan tåle for at opnå god økologisk tilstand.

Datakontekst:
  - VP3 WFS indeholder IKKE faktisk N-belastning (belast_n = -9999 overalt).
  - Faktisk N-udvaskning modelleres af DCE (NLES5) og publiceres kun i PDF.
  - `malbelas_n` er den bedste tilgængelige maskinlæsbare indikator.
  - For Doughnut Economics ER dette den relevante grænse (planetary boundary).

Metode:
  1. Hent ~108 kystvandoplande med malbelas_n og polygon-geometri fra VP3 WFS
  2. Hent kommunegrænser fra DAWA
  3. Overlay (intersection): fordel malbelas_n arealmæssigt til kommuner
  4. Kombiner med markblok_km2 fra land_use_scores.csv
  5. Beregn N-loft pr. ha landbrugsjord (kg N/ha)
  6. Beregn ratio (vægtet landssnit / kommune-ceiling × 100)

Scoring (Doughnut-ratio):
  ratio > 100 = mere presset end landsgennemsnit (strengere N-loft)
  ratio < 100 = mindre presset end landsgennemsnit (mere N-plads)
  Kommuner med lavere ceiling/ha har strengere vandmiljøkrav.

Krav:
  pip install geopandas

Brug:
  cd scripts/
  python3 fetch_naeringsstoffer_landbrug.py

Output:
  ../data/n_landbrug_scores.csv
"""

import csv
import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

import geopandas as gpd

# -- Konstanter ---------------------------------------------------------------

VP3_WFS    = "https://wfs2-miljoegis.mim.dk/vp3_2endelig2025/ows"
VP3_LAYER  = "vp3_2e2025_opl_marin_inds"
DAWA_URL   = "https://dawa.aws.dk/kommuner?format=geojson"
LAND_USE_CSV = Path("../data/land_use_scores.csv")
OUTPUT_FIL = Path("../data/n_landbrug_scores.csv")

PAGE_SIZE  = 200   # VP3 har ~108 features, 200 er rigeligt
NULL_VALUE = -9999  # MiljøGIS bruger -9999 som null-markør


# -- Hjælpefunktioner ---------------------------------------------------------

def fetch_json(url: str, timeout: int = 120, retries: int = 3) -> dict:
    """GET en URL og returner parsed JSON."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DoughnutDK/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")[:500]
            print(f"  HTTP {e.code}: {url[:80]}")
            print(f"  Fejlbesked: {body}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise
        except Exception as e:
            if attempt < retries - 1:
                print(f"  Fejl (forsøg {attempt+1}): {e}. Prøver igen...")
                time.sleep(2 ** attempt)
            else:
                raise


def parse_n_value(val) -> float:
    """Parse N-værdi fra WFS (kan være string, None, eller -9999)."""
    if val is None:
        return 0.0
    try:
        v = float(val)
        return v if v > 0 else 0.0
    except (ValueError, TypeError):
        return 0.0


# -- Trin 1: Hent VP3 kystvandoplande med N-loft ------------------------------

def hent_kystvandoplande() -> gpd.GeoDataFrame:
    """
    Henter kystvandoplande med N-målbelastning fra VP3 WFS.
    Returnerer GeoDataFrame i EPSG:25832 med malbelas_n (tons N).
    """
    print("\nTrin 1/5: Henter kystvandoplande fra VP3 WFS...")
    print(f"  Kilde: {VP3_WFS}")
    print(f"  Lag: {VP3_LAYER}")

    alle_features = []
    start = 0

    while True:
        url = (
            f"{VP3_WFS}?service=WFS&version=1.1.0&request=GetFeature"
            f"&typeName={VP3_LAYER}"
            f"&outputFormat=application/json"
            f"&maxFeatures={PAGE_SIZE}&startIndex={start}"
        )
        print(f"  Henter features {start} - {start + PAGE_SIZE}...", end=" ", flush=True)

        try:
            data = fetch_json(url)
        except Exception as e:
            print(f"FEJL: {e}")
            sys.exit(1)

        features = data.get("features", [])
        print(f"modtog {len(features)}")

        if not features:
            break

        alle_features.extend(features)
        start += PAGE_SIZE

        if len(features) < PAGE_SIZE:
            break

        time.sleep(0.5)

    print(f"  Total: {len(alle_features)} kystvandoplande hentet")

    if not alle_features:
        print("FEJL: Ingen VP3-data modtaget.")
        sys.exit(1)

    # Konverter til GeoDataFrame
    gdf = gpd.GeoDataFrame.from_features(alle_features)

    # Debug: vis felter
    print(f"  Kolonner: {list(gdf.columns)}")

    # Fjern tomme geometrier
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()].copy()

    # Bestem CRS fra koordinater
    if len(gdf) > 0:
        sample_coord = list(gdf.geometry.iloc[0].centroid.coords)[0]
        if abs(sample_coord[0]) > 1000:
            gdf = gdf.set_crs(epsg=25832)
            print("  CRS: EPSG:25832 (UTM)")
        else:
            gdf = gdf.set_crs(epsg=4326).to_crs(epsg=25832)
            print("  CRS: konverteret fra WGS84 til EPSG:25832")

    # Parse malbelas_n (WFS returnerer det som string)
    gdf["malbelas_n"] = gdf["malbelas_n"].apply(parse_n_value)

    # Beregn opland-areal fra geometri (mere præcist end WFS areal-felt)
    gdf["opland_ha"] = gdf.geometry.area / 10_000

    # Filtrer: kun features med gyldigt N-loft
    before = len(gdf)
    gdf = gdf[gdf["malbelas_n"] > 0].copy()
    after = len(gdf)
    if before != after:
        print(f"  Filtreret: {before - after} oplande uden N-data")
    print(f"  Gyldige oplande: {after}")

    # Statistik
    print(f"  Total malbelas_n: {gdf['malbelas_n'].sum():.0f} tons N")
    print(f"  Samlet opland-areal: {gdf['opland_ha'].sum():,.0f} ha")
    snit_per_ha = (gdf["malbelas_n"].sum() * 1000) / gdf["opland_ha"].sum()
    print(f"  Gennemsnit N-loft: {snit_per_ha:.1f} kg N/ha opland")

    return gdf


# -- Trin 2: Hent kommunegrænser -----------------------------------------------

def hent_kommuner() -> gpd.GeoDataFrame:
    """Henter kommunegrænser fra DAWA API."""
    print("\nTrin 2/5: Henter kommunegrænser fra DAWA...")
    try:
        kommuner = gpd.read_file(DAWA_URL)
        kommuner = kommuner.to_crs(epsg=25832)
        kommuner["kode"] = kommuner["kode"].apply(lambda k: str(int(k)))
        kommuner["total_km2"] = kommuner.geometry.area / 1_000_000
        print(f"  OK: {len(kommuner)} kommuner hentet")
        return kommuner
    except Exception as e:
        print(f"FEJL: {e}")
        sys.exit(1)


# -- Trin 3: Overlay og aggregering -------------------------------------------

def beregn_n_pr_kommune(oplande: gpd.GeoDataFrame,
                        kommuner: gpd.GeoDataFrame) -> dict:
    """
    Fordeler N-loft fra kystvandoplande til kommuner via overlay (intersection).

    Metode: For hvert skæringsstykke (opland x kommune) beregnes:
      - skæringsareal i ha
      - N-bidrag = (skæringsareal / opland-areal) × malbelas_n (tons)
    Summeres pr. kommune.

    Returnerer {kommune_kode: {"n_tons": float, "overlap_ha": float}}
    """
    print("\nTrin 3/5: Fordeler N-loft til kommuner via areal-overlay...")
    print("  Dette kan tage 1-3 minutter...")

    # Sikr valide geometrier
    oplande = oplande[oplande.geometry.is_valid & ~oplande.geometry.is_empty].copy()
    kommuner_clean = kommuner[kommuner.geometry.is_valid & ~kommuner.geometry.is_empty].copy()

    # Fix eventuelle ugyldige geometrier
    oplande["geometry"] = oplande.geometry.buffer(0)
    kommuner_clean["geometry"] = kommuner_clean.geometry.buffer(0)

    # Overlay: intersection af oplande med kommuner
    try:
        overlay = gpd.overlay(
            oplande[["geometry", "malbelas_n", "opland_ha"]],
            kommuner_clean[["geometry", "kode", "navn"]],
            how="intersection"
        )
    except Exception as e:
        print(f"  FEJL ved overlay: {e}")
        print("  Prøver med reduceret geometri-præcision...")
        oplande["geometry"] = oplande.geometry.simplify(10)
        overlay = gpd.overlay(
            oplande[["geometry", "malbelas_n", "opland_ha"]],
            kommuner_clean[["geometry", "kode", "navn"]],
            how="intersection"
        )

    print(f"  Overlay producerede {len(overlay)} skæringsstykker")

    # Beregn areal af hvert skæringsstykke
    overlay["intersection_ha"] = overlay.geometry.area / 10_000

    # Beregn N-bidrag: proportional andel af oplandets N-loft
    overlay["andel"] = overlay["intersection_ha"] / overlay["opland_ha"]
    overlay["n_tons_bidrag"] = overlay["andel"] * overlay["malbelas_n"]

    # Aggreger pr. kommune
    result = {}
    grouped = overlay.groupby("kode").agg(
        n_tons_total=("n_tons_bidrag", "sum"),
        overlap_ha=("intersection_ha", "sum")
    )

    for kode, row in grouped.iterrows():
        result[kode] = {
            "n_tons": round(row["n_tons_total"], 2),
            "overlap_ha": round(row["overlap_ha"], 1)
        }

    matched = len(result)
    print(f"  N-loft fordelt til {matched} kommuner")

    total_fordelt = sum(v["n_tons"] for v in result.values())
    print(f"  Total fordelt N: {total_fordelt:.0f} tons")

    # Vis top 5
    sorted_by_n = sorted(result.items(), key=lambda x: x[1]["n_tons"], reverse=True)
    print(f"\n  Top 5 kommuner (tons N-loft):")
    for kode, vals in sorted_by_n[:5]:
        print(f"    {kode}: {vals['n_tons']:.0f} tons N ({vals['overlap_ha']:.0f} ha opland)")

    return result


# -- Trin 4: Læs markblok-data og beregn N-loft pr. ha ------------------------

def beregn_intensitet(n_pr_kommune: dict, kommuner: gpd.GeoDataFrame) -> list:
    """
    Kombinerer N-loft med markblok-areal og beregner kg N/ha landbrug.

    Læser markblok_km2 fra land_use_scores.csv.
    Beregner ratio mod vægtet landsgennemsnit (snit/kommune × 100).
    """
    print(f"\nTrin 4/5: Beregner N-loft pr. ha landbrug...")

    # Læs markblok-data
    if not LAND_USE_CSV.exists():
        print(f"FEJL: {LAND_USE_CSV} ikke fundet. Kør fetch_arealanvendelse_data.py først.")
        sys.exit(1)

    markblok = {}
    with open(LAND_USE_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            kode = row["kommune_kode"]
            try:
                markblok[kode] = float(row["markblok_km2"])
            except (ValueError, KeyError):
                markblok[kode] = 0.0

    print(f"  Markblok-data for {len(markblok)} kommuner indlæst")

    # Byg resultater
    resultater = []
    for _, row in kommuner.iterrows():
        kode = row["kode"]
        navn = row["navn"]

        n_data = n_pr_kommune.get(kode, {"n_tons": 0, "overlap_ha": 0})
        n_tons = n_data["n_tons"]
        markblok_km2 = markblok.get(kode, 0.0)

        # Beregn kg N / ha landbrugsareal
        if markblok_km2 > 0:
            markblok_ha = markblok_km2 * 100
            n_kg_per_ha = round((n_tons * 1000) / markblok_ha, 1)
        else:
            n_kg_per_ha = 0.0

        resultater.append({
            "kommune_kode": kode,
            "kommune_navn": navn,
            "n_tons": n_tons,
            "markblok_km2": markblok_km2,
            "n_kg_per_ha": n_kg_per_ha,
        })

    # Beregn vægtet landsgennemsnit
    med_data = [r for r in resultater if r["n_kg_per_ha"] > 0]
    if med_data:
        total_n_kg = sum(r["n_tons"] * 1000 for r in med_data)
        total_markblok_ha = sum(r["markblok_km2"] * 100 for r in med_data)
        landssnit = total_n_kg / total_markblok_ha if total_markblok_ha > 0 else 0
        print(f"  Vægtet landsgennemsnit N-loft: {landssnit:.1f} kg N/ha")
    else:
        landssnit = 0
        print("  ADVARSEL: Ingen kommuner med N-data!")

    # Beregn ratio (invers: landssnit / kommune × 100)
    # ratio > 100 = strengere N-loft (mere presset)
    # ratio < 100 = mildere N-loft (mindre presset)
    for r in resultater:
        if r["n_kg_per_ha"] > 0 and landssnit > 0:
            r["n_ratio"] = round((landssnit / r["n_kg_per_ha"]) * 100, 2)
        elif r["markblok_km2"] == 0:
            r["n_ratio"] = 150.0  # Ingen landbrug = ikke relevant
        else:
            r["n_ratio"] = ""

    # Statistik
    ceilings = [r["n_kg_per_ha"] for r in resultater if r["n_kg_per_ha"] > 0]
    if ceilings:
        print(f"  N-loft range: {min(ceilings):.1f} - {max(ceilings):.1f} kg N/ha")
        over_snit = sum(1 for c in ceilings if c < landssnit)
        print(f"  Kommuner under landsgennemsnit (mere presset): {over_snit}/{len(ceilings)}")

    return resultater


# -- Trin 5: Gem CSV -----------------------------------------------------------

def gem_csv(resultater: list):
    """Skriver n_landbrug_scores.csv."""
    print(f"\nTrin 5/5: Gemmer til {OUTPUT_FIL}...")

    OUTPUT_FIL.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["kommune_kode", "kommune_navn", "n_tons", "markblok_km2",
                  "n_kg_per_ha", "n_ratio"]

    with open(OUTPUT_FIL, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sorted(resultater, key=lambda r: r["kommune_kode"]))

    print(f"  OK: {len(resultater)} kommuner skrevet")

    # Vis Thisted
    thisted = next((r for r in resultater if "thisted" in r["kommune_navn"].lower()), None)
    if thisted:
        print(f"\n  Thisted Kommune:")
        print(f"    N-loft:        {thisted['n_tons']} tons N")
        print(f"    Landbrugsareal: {thisted['markblok_km2']} km2")
        print(f"    N-loft/ha:     {thisted['n_kg_per_ha']} kg N/ha landbrug")
        print(f"    Ratio:         {thisted['n_ratio']} (>100 = mere presset)")


# -- Main ----------------------------------------------------------------------

def main():
    print("=" * 65)
    print("Doughnut Economics - Kvælstof-loft pr. kommune (VP3)")
    print("=" * 65)
    print(f"Kilde: {VP3_WFS}")
    print(f"Lag: {VP3_LAYER}")
    print(f"Indikator: malbelas_n (max baeredygtig N-tilfoersel, tons)")
    print("=" * 65)
    print()
    print("NB: malbelas_n er det OEKOLOGISKE LOFT - max baeredygtig N-tilfoersel")
    print("    pr. kystvandopland ifoelge Vandomraadeplan 3 (2025).")
    print("    Lavere loft/ha = strengere krav = mere belastet vandmiljoe.")
    print("    Faktisk N-udvaskning publiceres ikke maskinlaesbart (kun DCE PDF).")

    oplande    = hent_kystvandoplande()
    kommuner   = hent_kommuner()
    n_data     = beregn_n_pr_kommune(oplande, kommuner)
    resultater = beregn_intensitet(n_data, kommuner)
    gem_csv(resultater)

    print(f"\nFaerdig! N-scores gemt i {OUTPUT_FIL}")


if __name__ == "__main__":
    main()
