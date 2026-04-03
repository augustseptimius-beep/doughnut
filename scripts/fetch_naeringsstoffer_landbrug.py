#!/usr/bin/env python3
"""
Kvælstof-loft (økologisk grænse) pr. danske kommune
====================================================
Henter max bæredygtig N-tilførsel (malbelas_n) pr. kystvandopland fra
Vandområdeplan 3 (VP3) WFS og beregner N-loft pr. ha LANDBRUGSJORD
i oplandet - ikke pr. ha totalt landareal.

Datakilde:
  MiljøGIS VP3 2. endelig 2025 - lag: vp3_2e2025_opl_marin_inds
  WFS: wfs2-miljoegis.mim.dk/vp3_2endelig2025/ows
  Feltet `malbelas_n` = max bæredygtig N-tilførsel i tons N pr. kystvandopland.

  LFST Markblokke - lag: Markblokke:Markblokke_*
  WFS: geodata.fvm.dk/geoserver/ows
  ~300.000 markblok-polygoner dækkende hele Danmark.

Datakontekst:
  - VP3 WFS indeholder IKKE faktisk N-belastning (belast_n = -9999 overalt).
  - Faktisk N-udvaskning modelleres af DCE (NLES5) og publiceres kun i PDF.
  - `malbelas_n` er den bedste tilgængelige maskinlæsbare indikator.
  - For Doughnut Economics ER dette den relevante grænse (planetary boundary).

Metode:
  1. Hent ~108 kystvandoplande med malbelas_n fra VP3 WFS
  2. Hent alle markblokke fra LFST WFS (~300.000 polygoner, 10-20 min)
  3. Overlay markblokke × kystvandoplande → markblok_ha pr. opland
  4. Beregn n_ceiling_kg_per_ha pr. opland = malbelas_n×1000 / markblok_ha
  5. Hent kommunegrænser fra DAWA
  6. Overlay kystvandoplande × kommuner, vægtet af markblok-overlap
  7. Beregn kommunens N-loft som markblok-vægtet snit af oplandenes ceiling

Scoring (Doughnut-ratio):
  ratio > 100 = mere presset end landsgennemsnit (strengere N-loft pr. ha)
  ratio < 100 = mindre presset end landsgennemsnit (mere N-plads pr. ha)

Krav:
  pip install geopandas

Brug:
  cd scripts/
  python3 fetch_naeringsstoffer_landbrug.py
  NB: Tager 15-25 minutter pga. markblok-hentning.

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

VP3_WFS      = "https://wfs2-miljoegis.mim.dk/vp3_2endelig2025/ows"
VP3_LAYER    = "vp3_2e2025_opl_marin_inds"
LFST_WFS     = "https://geodata.fvm.dk/geoserver/ows"
DAWA_URL     = "https://dawa.aws.dk/kommuner?format=geojson"
OUTPUT_FIL   = Path("../data/n_landbrug_scores.csv")

VP3_PAGE     = 200    # VP3 har ~108 features
MB_PAGE      = 10000  # Markblokke: hent 10.000 ad gangen
NULL_VALUE   = -9999  # MiljøGIS null-markør
N_CAP        = 300.0  # Max kg N/ha - over dette er dataartifakt


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
            f"&maxFeatures={VP3_PAGE}&startIndex={start}"
        )
        print(f"  Henter features {start} - {start + VP3_PAGE}...", end=" ", flush=True)

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
        start += VP3_PAGE

        if len(features) < VP3_PAGE:
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


# -- Trin 2: Hent markblokke fra LFST WFS -------------------------------------

def find_markblok_lag() -> str:
    """Finder det aktuelle markblok-lagnavn fra LFST WFS capabilities."""
    import xml.etree.ElementTree as ET
    print("  Finder markblok-lag fra LFST capabilities...")
    url = f"{LFST_WFS}?service=WFS&version=2.0.0&request=GetCapabilities"
    req = urllib.request.Request(url, headers={"User-Agent": "DoughnutDK/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        xml_raw = resp.read().decode("utf-8", errors="replace")
    root = ET.fromstring(xml_raw)
    ns = {"wfs": "http://www.opengis.net/wfs/2.0"}
    kandidater = [
        ft.text for ft in root.findall(".//wfs:FeatureType/wfs:Name", ns)
        if ft.text and "markblokke:markblokke_" in ft.text.lower()
    ]
    if not kandidater:
        raise SystemExit("FEJL: Ingen Markblokke-lag fundet i LFST capabilities.")
    valgt = sorted(kandidater)[-1]
    print(f"  Lag valgt: {valgt}")
    return valgt


def hent_markblokke() -> gpd.GeoDataFrame:
    """
    Henter alle markblok-polygoner fra LFST WFS i sider.
    ~300.000 polygoner - tager 10-20 minutter.
    Returnerer GeoDataFrame i EPSG:25832 med areal_ha.
    """
    print("\nTrin 2/6: Henter markblokke fra LFST WFS (10-20 min)...")
    print(f"  Kilde: {LFST_WFS}")

    lag_navn = find_markblok_lag()
    alle_features = []
    start = 0

    while True:
        url = (
            f"{LFST_WFS}?service=WFS&version=2.0.0&request=GetFeature"
            f"&typeName={lag_navn}"
            f"&outputFormat=application/json"
            f"&count={MB_PAGE}&startIndex={start}"
        )
        print(f"  Henter features {start:,} - {start + MB_PAGE:,}...", end=" ", flush=True)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DoughnutDK/1.0"})
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"FEJL: {e}")
            break
        features = data.get("features", [])
        print(f"modtog {len(features)}")
        if not features:
            break
        alle_features.extend(features)
        start += MB_PAGE
        if len(features) < MB_PAGE:
            break
        time.sleep(0.3)

    print(f"  Total: {len(alle_features):,} markblok-polygoner hentet")
    if not alle_features:
        raise SystemExit("FEJL: Ingen markblok-data modtaget.")

    gdf = gpd.GeoDataFrame.from_features(alle_features)
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()].copy()

    sample_coord = list(gdf.geometry.iloc[0].centroid.coords)[0]
    if abs(sample_coord[0]) > 1000:
        gdf = gdf.set_crs(epsg=25832)
    else:
        gdf = gdf.set_crs(epsg=4326).to_crs(epsg=25832)

    gdf["mb_areal_ha"] = gdf.geometry.area / 10_000
    print(f"  Samlet markblok-areal: {gdf['mb_areal_ha'].sum():,.0f} ha")
    return gdf


# -- Trin 3: Markblok-areal pr. kystvandopland --------------------------------

def beregn_markblok_pr_opland(
    markblokke: gpd.GeoDataFrame,
    oplande: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    """
    Beregner markblok-areal (ha) pr. kystvandopland via centroid spatial join.
    Bruger centroid-metoden (hurtig og robust) frem for overlay.
    Returnerer oplande GeoDataFrame med ny kolonne markblok_ha.
    """
    print("\nTrin 3/6: Beregner markblok-areal pr. kystvandopland...")
    print("  Metode: centroid spatial join (hurtig)")

    markblokke = markblokke.copy()
    markblokke["geometry"] = markblokke.geometry.buffer(0)
    oplande = oplande.copy()
    oplande["geometry"] = oplande.geometry.buffer(0)

    # Centroider for alle markblokke
    mb_cent = markblokke[["mb_areal_ha"]].copy()
    mb_cent["geometry"] = markblokke.geometry.centroid

    # Spatial join: find hvilket kystvandopland hvert markblok-centroid ligger i
    joined = gpd.sjoin(
        gpd.GeoDataFrame(mb_cent, geometry="geometry", crs=markblokke.crs),
        oplande[["geometry", "op_id"]],
        how="left",
        predicate="within"
    )

    matchede = joined["op_id"].notna().sum()
    print(f"  Matchede markblokke: {matchede:,} af {len(markblokke):,} "
          f"({matchede/len(markblokke)*100:.1f}%)")

    # Summer markblok-areal pr. opland
    mb_pr_opland = (
        joined.dropna(subset=["op_id"])
        .groupby("op_id")["mb_areal_ha"]
        .sum()
        .reset_index()
        .rename(columns={"mb_areal_ha": "markblok_ha"})
    )

    oplande = oplande.merge(mb_pr_opland, on="op_id", how="left")
    oplande["markblok_ha"] = oplande["markblok_ha"].fillna(0)

    gyldige = (oplande["markblok_ha"] > 0).sum()
    print(f"  Oplande med markblok-data: {gyldige} af {len(oplande)}")
    print(f"  Total markblok-areal i oplande: {oplande['markblok_ha'].sum():,.0f} ha")

    # Beregn N-loft pr. ha LANDBRUGSJORD i hvert opland
    oplande["n_ceiling_kg_per_ha"] = oplande.apply(
        lambda r: min((r["malbelas_n"] * 1000) / r["markblok_ha"], N_CAP)
        if r["markblok_ha"] > 0 else 0.0,
        axis=1
    )

    print(f"\n  N-loft pr. ha landbrugsjord pr. opland:")
    gyldige_oplande = oplande[oplande["n_ceiling_kg_per_ha"] > 0]
    print(f"    Min: {gyldige_oplande['n_ceiling_kg_per_ha'].min():.1f} kg N/ha")
    print(f"    Max: {gyldige_oplande['n_ceiling_kg_per_ha'].max():.1f} kg N/ha")
    print(f"    Snit: {gyldige_oplande['n_ceiling_kg_per_ha'].mean():.1f} kg N/ha")

    return oplande


# -- Trin 4: Hent kommunegrænser -----------------------------------------------

def hent_kommuner() -> gpd.GeoDataFrame:
    """Henter kommunegrænser fra DAWA API."""
    print("\nTrin 4/6: Henter kommunegrænser fra DAWA...")
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


# -- Trin 5: N-loft pr. kommune (markblok-vægtet) -----------------------------

def beregn_n_pr_kommune(
    oplande: gpd.GeoDataFrame,
    kommuner: gpd.GeoDataFrame
) -> list:
    """
    Beregner markblok-vægtet N-loft pr. ha pr. kommune.

    Metode:
      - Overlay kystvandoplande × kommuner
      - For hvert skæringsstykke: markblok-areal i skæringen
        (estimeret som andel af oplandets markblok-areal × skæringsandel)
      - Vægtet snit af n_ceiling_kg_per_ha, vægtet af markblok-areal i skæringen
    """
    print("\nTrin 5/6: Beregner markblok-vægtet N-loft pr. kommune...")

    oplande_clean = oplande[
        oplande.geometry.is_valid & ~oplande.geometry.is_empty &
        (oplande["n_ceiling_kg_per_ha"] > 0)
    ].copy()
    oplande_clean["geometry"] = oplande_clean.geometry.buffer(0)

    kommuner_clean = kommuner[
        kommuner.geometry.is_valid & ~kommuner.geometry.is_empty
    ].copy()
    kommuner_clean["geometry"] = kommuner_clean.geometry.buffer(0)

    # Overlay
    try:
        overlay = gpd.overlay(
            oplande_clean[["geometry", "op_id", "malbelas_n",
                           "markblok_ha", "n_ceiling_kg_per_ha"]],
            kommuner_clean[["geometry", "kode", "navn"]],
            how="intersection"
        )
    except Exception as e:
        print(f"  FEJL: {e}. Prøver simplify...")
        oplande_clean["geometry"] = oplande_clean.geometry.simplify(10)
        overlay = gpd.overlay(
            oplande_clean[["geometry", "op_id", "malbelas_n",
                           "markblok_ha", "n_ceiling_kg_per_ha"]],
            kommuner_clean[["geometry", "kode", "navn"]],
            how="intersection"
        )

    print(f"  Overlay: {len(overlay)} skæringsstykker")

    # Beregn markblok-areal i hvert skæringsstykke
    overlay["intersection_ha"] = overlay.geometry.area / 10_000
    overlay["opland_areal_ha"] = overlay.geometry.apply(
        lambda g: g.area / 10_000
    )

    # Estimer markblok i skæringen: andel af oplandets totale areal ×
    # oplandets markblok_ha giver en approksimation
    overlay["andel_af_opland"] = (
        overlay["intersection_ha"] /
        overlay.groupby("op_id")["intersection_ha"].transform("sum")
    )
    overlay["mb_ha_i_skaering"] = overlay["andel_af_opland"] * overlay["markblok_ha"]

    # Aggreger pr. kommune: markblok-vægtet snit af n_ceiling_kg_per_ha
    result = []
    grouped = overlay.groupby("kode")

    for kode, gruppe in grouped:
        total_mb = gruppe["mb_ha_i_skaering"].sum()
        if total_mb > 0:
            # Vægtet snit
            vægtet_ceiling = (
                (gruppe["n_ceiling_kg_per_ha"] * gruppe["mb_ha_i_skaering"]).sum()
                / total_mb
            )
        else:
            vægtet_ceiling = 0.0
        result.append({
            "kode": kode,
            "n_ceiling_kg_per_ha": round(min(vægtet_ceiling, N_CAP), 1),
            "mb_ha_i_opland": round(total_mb, 1)
        })

    print(f"  N-loft beregnet for {len(result)} kommuner")
    return result


# -- Trin 6: Byg resultater og gem CSV ----------------------------------------

def beregn_og_gem(
    n_pr_kommune: list,
    kommuner: gpd.GeoDataFrame
) -> list:
    """Bygger resultater, beregner ratio og skriver CSV."""
    print(f"\nTrin 6/6: Beregner ratio og gemmer til {OUTPUT_FIL}...")

    # Indeks over n-data
    n_idx = {r["kode"]: r for r in n_pr_kommune}

    resultater = []
    for _, row in kommuner.iterrows():
        kode = row["kode"]
        navn = row["navn"]
        n_data = n_idx.get(kode, {})
        n_kg_per_ha = n_data.get("n_ceiling_kg_per_ha", 0.0)
        mb_ha = n_data.get("mb_ha_i_opland", 0.0)

        resultater.append({
            "kommune_kode": kode,
            "kommune_navn": navn,
            "n_ceiling_kg_per_ha": n_kg_per_ha,
            "markblok_ha_i_opland": round(mb_ha, 1),
            "n_ratio": 0.0
        })

    # Vægtet landsgennemsnit
    med_data = [r for r in resultater if r["n_ceiling_kg_per_ha"] > 0]
    if med_data:
        total_n = sum(r["n_ceiling_kg_per_ha"] * r["markblok_ha_i_opland"]
                      for r in med_data)
        total_mb = sum(r["markblok_ha_i_opland"] for r in med_data)
        landssnit = total_n / total_mb if total_mb > 0 else 0
        print(f"  Vægtet landsgennemsnit N-loft: {landssnit:.1f} kg N/ha landbrug")
    else:
        landssnit = 0
        print("  ADVARSEL: Ingen kommuner med N-data!")

    # Ratio: landssnit / kommune × 100
    for r in resultater:
        if r["n_ceiling_kg_per_ha"] > 0 and landssnit > 0:
            r["n_ratio"] = round((landssnit / r["n_ceiling_kg_per_ha"]) * 100, 2)
        elif r["markblok_ha_i_opland"] == 0:
            r["n_ratio"] = 150.0
        else:
            r["n_ratio"] = ""

    # Statistik
    ceilings = [r["n_ceiling_kg_per_ha"] for r in resultater
                if r["n_ceiling_kg_per_ha"] > 0]
    if ceilings:
        print(f"  N-loft range: {min(ceilings):.1f} - {max(ceilings):.1f} kg N/ha")
        under_snit = sum(1 for c in ceilings if c < landssnit)
        print(f"  Kommuner under landsgennemsnit (mere presset): "
              f"{under_snit}/{len(ceilings)}")

    # Gem CSV
    OUTPUT_FIL.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["kommune_kode", "kommune_navn", "n_ceiling_kg_per_ha",
                  "markblok_ha_i_opland", "n_ratio"]
    with open(OUTPUT_FIL, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sorted(resultater, key=lambda r: r["kommune_kode"]))

    print(f"  OK: {len(resultater)} kommuner skrevet")

    # Thisted
    thisted = next(
        (r for r in resultater if "thisted" in r["kommune_navn"].lower()), None
    )
    if thisted:
        print(f"\n  Thisted Kommune:")
        print(f"    N-loft pr. ha landbrug: {thisted['n_ceiling_kg_per_ha']} kg N/ha")
        print(f"    Markblok i oplande:     {thisted['markblok_ha_i_opland']} ha")
        print(f"    Ratio:                  {thisted['n_ratio']} (>100 = mere presset)")

    return resultater


# -- Main ----------------------------------------------------------------------

def main():
    print("=" * 65)
    print("Doughnut Economics - Kvælstof-loft pr. ha landbrug (VP3 + LFST)")
    print("=" * 65)
    print(f"VP3 WFS:  {VP3_WFS}")
    print(f"LFST WFS: {LFST_WFS}")
    print(f"Metode: malbelas_n / markblok_ha pr. kystvandopland")
    print("=" * 65)
    print()
    print("NB: Tager 15-25 minutter pga. ~300.000 markblok-polygoner.")
    print("    malbelas_n = max baeredygtig N-tilfoersel fra VP3 (2025).")
    print("    Naevner = faktisk landbrugsareal i hvert kystvandopland.")

    oplande    = hent_kystvandoplande()
    markblokke = hent_markblokke()
    oplande    = beregn_markblok_pr_opland(markblokke, oplande)
    kommuner   = hent_kommuner()
    n_data     = beregn_n_pr_kommune(oplande, kommuner)
    beregn_og_gem(n_data, kommuner)

    print(f"\nFaerdig! N-scores gemt i {OUTPUT_FIL}")


if __name__ == "__main__":
    main()
