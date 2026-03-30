#!/usr/bin/env python3
"""
Arealanvendelse pr. danske kommune — §3-natur + markblokke
===========================================================
Henter to datasæt fra Landbrugs- og Fiskeristyrelsen WFS:
  1. Paragraf3: §3-beskyttede naturarealer (hede, eng, mose, overdrev, strandeng, sø)
  2. Markblokke: landbrugsarealer under dyrkning

Kilde: geodata.fvm.dk (LFST). Åbent, ingen login krævet.

Metode:
  1. Hent alle Paragraf3-polygoner fra LFST WFS (pagineret)
  2. Hent alle Markblokke-polygoner fra LFST WFS (pagineret)
  3. Hent kommunegrænser fra DAWA
  4. Spatial join: summer §3-areal og markblok-areal pr. kommune
  5. Score §3-natur mod EU Biodiversitetsstrategi 30%-mål

Grænseværdi (natur): 30% §3-naturarealer (30x30-målet, EU 2030)
Ratio > 100 = for lidt natur (overshoot). < 100 = over målet (godt).

Markblokke bruges som informationsdata (ikke direkte scoring endnu),
men danner grundlag for fremtidig N/P-intensitetsberegning pr. ha landbrugsareal.

Krav:
  pip install geopandas

Brug:
  cd scripts/
  python3 fetch_arealanvendelse_data.py

Output:
  ../data/land_use_scores.csv
"""

import csv
import json
import math
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

import geopandas as gpd
from shapely.geometry import shape

# ── Konstanter ────────────────────────────────────────────────────────────────

LFST_WFS     = "https://geodata.fvm.dk/geoserver/ows"
DAWA_URL     = "https://dawa.aws.dk/kommuner?format=geojson"
DST_API      = "https://api.statbank.dk/v1"
OUTPUT_FIL   = Path("../data/land_use_scores.csv")

TARGET_PCT   = 30.0   # EU 30x30-mål
PAGE_SIZE    = 10000  # Features pr. request


# ── Hjælpefunktioner ──────────────────────────────────────────────────────────

def fetch_json(url: str, timeout: int = 60, retries: int = 3) -> dict:
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


def fetch_dst_table(table: str, variables: list) -> list:
    """Hent data fra Danmarks Statistik API."""
    url = f"{DST_API}/data"
    payload = json.dumps({
        "table": table, "format": "JSON", "lang": "da",
        "variables": variables
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ── Trin 1: Hent §3-arealer fra LFST WFS ────────────────────────────────────

def find_layer_navn(substring: str, lag_type: str = "lag") -> str:
    """
    Henter capabilities og finder det korrekte lag-navn.

    Args:
        substring: Del af lagnavnet at søge efter (case-insensitive)
        lag_type: Navn på lagtype for fejlmeddelser (f.eks. "Paragraf3", "Markblokke")

    Returns:
        Fuld lagnavn fra capabilities
    """
    import xml.etree.ElementTree as ET
    print(f"  Finder korrekt lag-navn for {lag_type}...")
    url = f"{LFST_WFS}?service=WFS&version=2.0.0&request=GetCapabilities"
    req = urllib.request.Request(url, headers={"User-Agent": "DoughnutDK/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw_bytes = resp.read()
        xml_raw = raw_bytes.decode("utf-8", errors="replace") or raw_bytes.decode("iso-8859-1")

    root = ET.fromstring(xml_raw)
    ns = {"wfs": "http://www.opengis.net/wfs/2.0"}
    kandidater = []
    for ft in root.findall(".//wfs:FeatureType/wfs:Name", ns):
        if ft.text and substring.lower() in ft.text.lower():
            kandidater.append(ft.text)

    if not kandidater:
        # Vis alle tilgængelige lag hvis ingen match
        alle = [ft.text for ft in root.findall(".//wfs:FeatureType/wfs:Name", ns)]
        print(f"  ADVARSEL: Ingen {lag_type}-lag fundet. Tilgængelige lag ({len(alle)}):")
        for navn in sorted(alle):
            print(f"    {navn}")
        raise SystemExit(f"Kan ikke finde {lag_type}-lag med '{substring}'. Se listen ovenfor.")

    # Sortér kandidater og vælg den nyeste (antager årstal i navnets slutning)
    kandidater_sorteret = sorted(kandidater)
    valgt = kandidater_sorteret[-1]
    print(f"  Fandt lag: {valgt}")
    if len(kandidater_sorteret) > 1:
        andre = [k for k in kandidater_sorteret if k != valgt]
        print(f"  (Andre kandidater: {andre})")
    return valgt


def hent_paragraf3() -> gpd.GeoDataFrame:
    """
    Henter alle Paragraf3-features fra LFST WFS i sider.
    Returnerer GeoDataFrame i EPSG:25832.
    """
    print("\nTrin 1/4: Henter §3-naturarealer fra LFST WFS...")
    print(f"  Kilde: {LFST_WFS}")

    # Søg efter "paragraf3_i_imk" for at undgå "_soer_"-varianten
    lag_navn = find_layer_navn("paragraf3_i_imk", "Paragraf3")

    alle_features = []
    start = 0

    while True:
        url = (
            f"{LFST_WFS}?service=WFS&version=2.0.0&request=GetFeature"
            f"&typeName={lag_navn}"
            f"&outputFormat=application/json"
            f"&count={PAGE_SIZE}&startIndex={start}"
        )
        print(f"  Henter features {start} - {start + PAGE_SIZE}...", end=" ", flush=True)

        try:
            data = fetch_json(url, timeout=120)
        except Exception as e:
            print(f"FEJL: {e}")
            sys.exit(1)

        features = data.get("features", [])
        print(f"modtog {len(features)}")

        if not features:
            break

        alle_features.extend(features)
        start += PAGE_SIZE

        # Tjek om vi fik færre end PAGE_SIZE (dvs. sidste side)
        if len(features) < PAGE_SIZE:
            break

        time.sleep(0.5)  # Vær pæn mod serveren

    print(f"  Total: {len(alle_features)} §3-polygoner hentet")

    if not alle_features:
        print("FEJL: Ingen §3-data modtaget. Tjek netværksforbindelsen.")
        sys.exit(1)

    # Debug: vis rå geometri fra første feature
    if alle_features:
        f0 = alle_features[0]
        geom0 = f0.get("geometry", {})
        coords = geom0.get("coordinates", [])
        # Find første koordinatpar (kan være nested)
        sample = coords
        for _ in range(5):
            if sample and isinstance(sample[0], list):
                sample = sample[0]
            else:
                break
        print(f"  Første feature koordinater (sample): {sample[:2] if sample else 'ingen'}")
        print(f"  Geometry type: {geom0.get('type', 'ukendt')}")

    # Konverter til GeoDataFrame
    try:
        gdf = gpd.GeoDataFrame.from_features(alle_features)
    except Exception as e:
        print(f"FEJL ved konvertering til GeoDataFrame: {e}")
        sys.exit(1)

    print(f"  GeoDataFrame CRS efter from_features: {gdf.crs}")
    print(f"  Gyldige geometrier: {gdf.geometry.is_valid.sum()} / {len(gdf)}")
    print(f"  Tomme geometrier: {gdf.geometry.is_empty.sum()}")

    # Bestem CRS ud fra koordinaternes størrelsesorden
    # EPSG:4326 (WGS84): koordinater ~(8-15, 54-58) for Danmark
    # EPSG:25832 (UTM):  koordinater ~(450000-900000, 6050000-6400000) for Danmark
    if not gdf.geometry.is_empty.all():
        sample_geom = gdf.geometry[~gdf.geometry.is_empty].iloc[0]
        sample_coord = list(sample_geom.centroid.coords)[0]
        print(f"  Sample koordinat (rå): {sample_coord}")

        if abs(sample_coord[0]) > 1000:
            # Koordinater er i UTM (store tal) - allerede EPSG:25832
            print("  Detekteret: koordinater er i UTM (EPSG:25832)")
            gdf = gdf.set_crs(epsg=25832)
        else:
            # Koordinater er i WGS84 (lille tal) - konverter til EPSG:25832
            print("  Detekteret: koordinater er i WGS84 (EPSG:4326) → konverterer")
            gdf = gdf.set_crs(epsg=4326).to_crs(epsg=25832)
    else:
        print("  ADVARSEL: Alle geometrier er tomme!")
        gdf = gdf.set_crs(epsg=4326).to_crs(epsg=25832)

    # Vis hvilke naturtyper der er med
    if "naturtype" in gdf.columns:
        typer = gdf["naturtype"].value_counts()
        print(f"\n  Naturtyper:")
        for t, n in typer.items():
            print(f"    {t}: {n:,}")
    elif "naturbeskyttelseslovens_paragraf3" in gdf.columns:
        typer = gdf["naturbeskyttelseslovens_paragraf3"].value_counts()
        print(f"\n  §3-typer:")
        for t, n in typer.items():
            print(f"    {t}: {n:,}")

    return gdf


# ── Trin 2: Hent kommunegrænser ──────────────────────────────────────────────

def hent_kommuner() -> gpd.GeoDataFrame:
    """Henter kommunegrænser fra DAWA API."""
    print("\nTrin 2/4: Henter kommunegrænser fra DAWA...")
    try:
        kommuner = gpd.read_file(DAWA_URL)
        kommuner = kommuner.to_crs(epsg=25832)
        # Beregn totalareal pr. kommune (i km²)
        kommuner["total_km2"] = kommuner.geometry.area / 1_000_000
        # Normaliser kommunekode (fjern foranstillede nuller)
        kommuner["kode"] = kommuner["kode"].apply(lambda k: str(int(k)))
        print(f"  OK: {len(kommuner)} kommuner hentet")
        return kommuner
    except Exception as e:
        print(f"FEJL: {e}")
        sys.exit(1)


# ── Trin 3: Spatial join ─────────────────────────────────────────────────────

def beregn_naturandel(p3: gpd.GeoDataFrame, kommuner: gpd.GeoDataFrame) -> dict:
    """
    Beregner §3-naturandel pr. kommune via centroid spatial join.
    Returnerer {kommunekode: natur_km2}.
    """
    print("\nTrin 3/4: Beregner §3-areal pr. kommune...")
    print("  Dette kan tage 2-5 minutter afhængig af din computer...")

    # Debug: vis CRS for begge lag
    print(f"  §3 CRS: {p3.crs}")
    print(f"  Kommuner CRS: {kommuner.crs}")
    print(f"  §3 polygoner: {len(p3)}")

    # Fjern tomme geometrier
    p3 = p3[~p3.geometry.is_empty & p3.geometry.notna()].copy()
    print(f"  §3 polygoner efter filtrering: {len(p3)}")

    # Beregn areal af hvert §3-polygon FØR vi ændrer geometri
    p3["areal_km2"] = p3.geometry.area / 1_000_000
    print(f"  Total §3-areal: {p3['areal_km2'].sum():.0f} km²")

    # Brug centroid til spatial join (hurtigere og mere robust end overlay)
    p3_cent = p3.copy()
    p3_cent.geometry = p3_cent.geometry.centroid

    # Spatial join: find hvilken kommune hvert centroid ligger i
    joined = gpd.sjoin(
        p3_cent[["geometry", "areal_km2"]],
        kommuner[["kode", "geometry"]],
        how="left",
        predicate="within"
    )

    matched = joined["kode"].notna().sum()
    print(f"  Matchede polygoner: {matched} af {len(p3)} ({matched/len(p3)*100:.1f}%)")

    if matched == 0:
        print("  ADVARSEL: Ingen match - tjekker CRS...")
        print(f"  Sample §3 koordinater: {p3.geometry.iloc[0].centroid}")
        print(f"  Sample kommune bbox: {kommuner.geometry.iloc[0].bounds}")
        raise SystemExit("CRS-mismatch. Kontakt support.")

    # Summer areal pr. kommune
    natur_pr_kommune = (
        joined.dropna(subset=["kode"])
        .groupby("kode")["areal_km2"]
        .sum()
        .to_dict()
    )

    print(f"  §3-areal beregnet for {len(natur_pr_kommune)} kommuner")
    return natur_pr_kommune


# ── Markblokke ───────────────────────────────────────────────────────────────

def hent_markblokke() -> gpd.GeoDataFrame:
    """
    Henter alle Markblokke-features fra LFST WFS i sider.
    Returnerer GeoDataFrame i EPSG:25832.
    NB: Markblokke er et stort datasæt (~300.000 polygoner) - tager 10-20 min.
    """
    print("\n(Markblokke): Henter landbrugsarealer fra LFST WFS...")

    try:
        # Søg efter "Markblokke:Markblokke_" for at undgå "MarkblokkeSogn"-aggregater
        lag_navn = find_layer_navn("markblokke:markblokke_", "Markblokke")
    except SystemExit:
        print("  ADVARSEL: Ingen Markblokke-lag fundet - springer over.")
        return None

    alle_features = []
    start = 0

    while True:
        url = (
            f"{LFST_WFS}?service=WFS&version=2.0.0&request=GetFeature"
            f"&typeName={lag_navn}"
            f"&outputFormat=application/json"
            f"&count={PAGE_SIZE}&startIndex={start}"
        )
        print(f"  Henter features {start} - {start + PAGE_SIZE}...", end=" ", flush=True)

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
        start += PAGE_SIZE

        if len(features) < PAGE_SIZE:
            break

        time.sleep(0.5)

    print(f"  Total: {len(alle_features)} markblok-polygoner hentet")

    if not alle_features:
        return None

    gdf = gpd.GeoDataFrame.from_features(alle_features)
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()].copy()

    # Bestem CRS
    if len(gdf) > 0:
        sample_coord = list(gdf.geometry.iloc[0].centroid.coords)[0]
        if abs(sample_coord[0]) > 1000:
            gdf = gdf.set_crs(epsg=25832)
        else:
            gdf = gdf.set_crs(epsg=4326).to_crs(epsg=25832)

    return gdf


def beregn_landbrugsareal(markblokke: gpd.GeoDataFrame, kommuner: gpd.GeoDataFrame) -> dict:
    """
    Beregner markblok-areal pr. kommune via centroid spatial join.
    Returnerer {kommunekode: markblok_km2}.
    """
    if markblokke is None or len(markblokke) == 0:
        print("  Ingen markblokke-data - springer over.")
        return {}

    print("\n(Markblokke): Beregner landbrugsareal pr. kommune...")

    markblokke = markblokke.copy()
    markblokke["areal_km2"] = markblokke.geometry.area / 1_000_000
    print(f"  Total markblok-areal: {markblokke['areal_km2'].sum():.0f} km²")

    mb_cent = markblokke.copy()
    mb_cent.geometry = mb_cent.geometry.centroid

    joined = gpd.sjoin(
        mb_cent[["geometry", "areal_km2"]],
        kommuner[["kode", "geometry"]],
        how="left",
        predicate="within"
    )

    landbrug_pr_kommune = (
        joined.dropna(subset=["kode"])
        .groupby("kode")["areal_km2"]
        .sum()
        .to_dict()
    )

    print(f"  Landbrugsareal beregnet for {len(landbrug_pr_kommune)} kommuner")
    return landbrug_pr_kommune


# ── Trin 4: Gem CSV ──────────────────────────────────────────────────────────

def gem_csv(kommuner: gpd.GeoDataFrame, natur_pr_kommune: dict, landbrug_pr_kommune: dict = None):
    """Beregner scores og skriver land_use_scores.csv."""
    print(f"\nTrin 4/4: Gemmer til {OUTPUT_FIL}...")

    OUTPUT_FIL.parent.mkdir(parents=True, exist_ok=True)

    har_landbrug = bool(landbrug_pr_kommune)

    resultater = []
    for _, row in kommuner.iterrows():
        kode = row["kode"]
        navn = row["navn"]
        total_km2 = row["total_km2"]
        natur_km2 = natur_pr_kommune.get(kode, 0.0)
        markblok_km2 = landbrug_pr_kommune.get(kode, 0.0) if har_landbrug else None

        natur_pct = round((natur_km2 / total_km2) * 100, 2) if total_km2 > 0 else 0.0
        markblok_pct = round((markblok_km2 / total_km2) * 100, 2) if (har_landbrug and total_km2 > 0) else None

        # Eco-ratio for natur: (30% mål / faktisk %) × 100. Over 100 = for lidt natur.
        ratio = round((TARGET_PCT / natur_pct) * 100, 2) if natur_pct > 0 else 999.0

        rec = {
            "kommune_kode": kode,
            "kommune_navn": navn,
            "natur_km2": round(natur_km2, 1),
            "total_km2": round(total_km2, 1),
            "natur_pct": natur_pct,
            "target_pct": TARGET_PCT,
            "land_use_ratio": ratio,
        }
        if har_landbrug:
            rec["markblok_km2"]  = round(markblok_km2, 1)
            rec["markblok_pct"]  = markblok_pct

        resultater.append(rec)

    fieldnames = ["kommune_kode", "kommune_navn", "natur_km2", "total_km2",
                  "natur_pct", "target_pct", "land_use_ratio"]
    if har_landbrug:
        fieldnames += ["markblok_km2", "markblok_pct"]

    with open(OUTPUT_FIL, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sorted(resultater, key=lambda r: r["kommune_kode"]))

    print(f"  OK: {len(resultater)} kommuner skrevet")

    # Vis statistik
    pctscore = [r["natur_pct"] for r in resultater if r["natur_pct"] > 0]
    over_mål = sum(1 for r in resultater if r["natur_pct"] >= TARGET_PCT)

    if pctscore:
        print(f"\n  §3-naturandel: {min(pctscore):.1f}% - {max(pctscore):.1f}% (snit: {sum(pctscore)/len(pctscore):.1f}%)")
        print(f"  Kommuner der opfylder 30%-målet: {over_mål}/{len(resultater)}")
    else:
        print("\n  ADVARSEL: Ingen naturandele beregnet - tjek spatial join ovenfor")

    if har_landbrug:
        mbpct = [r["markblok_pct"] for r in resultater if r.get("markblok_pct")]
        if mbpct:
            print(f"  Landbrugsandel: {min(mbpct):.1f}% - {max(mbpct):.1f}% (snit: {sum(mbpct)/len(mbpct):.1f}%)")

    # Thisted
    thisted = next((r for r in resultater if "thisted" in r["kommune_navn"].lower()), None)
    if thisted:
        print(f"\n  Thisted Kommune:")
        print(f"    §3-natur:   {thisted['natur_km2']} km² ({thisted['natur_pct']}%) — mål: {TARGET_PCT}%")
        if har_landbrug:
            print(f"    Landbrug:   {thisted.get('markblok_km2', '?')} km² ({thisted.get('markblok_pct', '?')}%)")
            rest = round(thisted["total_km2"] - thisted["natur_km2"] - thisted.get("markblok_km2", 0), 1)
            print(f"    Andet:      {rest} km² (by, vej, vand mv.)")
        print(f"    Ratio:      {thisted['land_use_ratio']}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Doughnut Economics — Arealanvendelse (§3-natur + markblokke)")
    print("=" * 60)
    print(f"Kilde: {LFST_WFS}")
    print(f"Grænseværdi natur: {TARGET_PCT}% (EU 30x30-mål)")
    print("=" * 60)

    p3           = hent_paragraf3()
    kommuner     = hent_kommuner()
    natur        = beregn_naturandel(p3, kommuner)

    markblokke   = hent_markblokke()
    landbrug     = beregn_landbrugsareal(markblokke, kommuner)

    gem_csv(kommuner, natur, landbrug)

    print("\nFærdig! Land use scores gemt i ../data/land_use_scores.csv")
    print("Markblok-data er inkluderet som markblok_km2 og markblok_pct kolonner.")
    print("Kør derefter din normale deploy-process for at opdatere platformen.")


if __name__ == "__main__":
    main()
