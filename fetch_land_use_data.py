#!/usr/bin/env python3
"""
Doughnut Economics Dashboard — Land Use Data Fetcher

Strategy:
  1. ARE207: Kommunernes samlede areal (km²) - giver os total areal pr. kommune
  2. AREALDK2: Arealdække (skov, landbrug, natur osv.) - kun regionsniveau
  3. Vi fordeler regionalt arealdække proportionalt til kommunerne via ARE207

Methodology:
  - Henter regionalt arealdække fra AREALDK2
  - Henter kommunearealer fra ARE207
  - Fordeler arealdække proportionalt (kommune_areal / region_areal * region_naturandel)
  - Scorer mod EU Biodiversity Strategy 2030 target: 30% naturområder

Begrænsning: Proportional fordeling antager ensartet fordeling inden for regionen.
Det er en proxy - ikke eksakt kommunedata. For præcise tal kræves BASEMAP04 GIS-analyse.

Output: land_use_scores.csv

Usage:
  python3 fetch_land_use_data.py
"""

import csv
import json
import sys
import time
import urllib.request
import urllib.error

API_BASE = "https://api.statbank.dk/v1"

# Region-til-kommune mapping (alle 98 kommuner)
# DST region codes for landsdele
REGION_KOMMUNE_MAP = {
    # Region Nordjylland (1081)
    "1081": ["773", "787", "810", "813", "820", "825", "840", "846", "849", "851", "860"],
    # Region Midtjylland (1082)
    "1082": ["615", "657", "661", "665", "671", "706", "707", "710", "727", "730", "740", "741", "746", "751", "756", "760", "766", "779", "791"],
    # Region Syddanmark (1083)
    "1083": ["410", "420", "430", "440", "450", "461", "479", "480", "482", "492", "510", "530", "540", "550", "561", "563", "573", "575", "580", "607", "621", "630"],
    # Region Hovedstaden (1084)
    "1084": ["101", "147", "151", "153", "155", "157", "159", "161", "163", "165", "167", "169", "173", "175", "183", "185", "187", "190", "201", "210", "217", "219", "223", "230", "240", "250", "260", "270"],
    # Region Sjælland (1085)
    "1085": ["253", "259", "265", "269", "306", "316", "320", "326", "329", "330", "336", "340", "350", "360", "370", "376", "390"],
}


def api_post(endpoint, payload):
    """POST to DST API with retry."""
    url = f"{API_BASE}/{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                url, data=data, headers={"Content-Type": "application/json"}
            )
            resp = urllib.request.urlopen(req, timeout=60)
            raw = resp.read().decode("utf-8")
            # Try JSON first, fall back to CSV
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            if attempt < 2:
                time.sleep(2)
            else:
                raise


def fetch_table_info(table_id):
    """Get table metadata and print structure."""
    print(f"\nFetching metadata for {table_id}...")
    info = api_post("tableinfo", {"table": table_id, "lang": "da"})
    print(f"  Table: {info.get('text', '?')}")
    print(f"  Updated: {info.get('updated', '?')}")
    for v in info.get("variables", []):
        vals = v.get("values", [])
        print(f"  Variable '{v['id']}': {v['text']} ({len(vals)} values)")
        if len(vals) <= 20:
            for val in vals:
                print(f"    {val['id']} = {val['text']}")
    return info


def fetch_kommune_areas():
    """Fetch total area per municipality from ARE207."""
    print("\n" + "=" * 60)
    print("Step 1: Fetching municipal areas (ARE207)")
    print("=" * 60)

    info = fetch_table_info("ARE207")

    # Find variable codes
    var_codes = {v["id"]: v for v in info["variables"]}

    # Build request
    payload = {
        "table": "ARE207",
        "format": "JSON",
        "lang": "da",
        "variables": [
            {"code": "OMRÅDE", "values": ["*"]},
            {"code": "Tid", "values": ["*"]},
        ],
    }

    print("\nFetching data...")
    data = api_post("data", payload)
    print(f"  Received {len(data)} rows")

    # Parse: find latest year per municipality
    kommune_areas = {}
    for row in data:
        kode = row.get("OMRÅDE", "")
        # Extract numeric code
        if " " in kode:
            code_part = kode.split(" ")[0]
        else:
            code_part = kode

        try:
            code_int = int(code_part)
            if not (100 <= code_int <= 860):
                continue
        except ValueError:
            continue

        value = row.get("INDHOLD", "")
        try:
            area = float(value)
        except (ValueError, TypeError):
            continue

        year = row.get("TID", "")
        code_str = str(code_int)

        # Keep latest year
        if code_str not in kommune_areas or year > kommune_areas[code_str]["year"]:
            kommune_areas[code_str] = {"area_km2": area, "year": year, "name": kode}

    print(f"  Parsed {len(kommune_areas)} municipalities")
    return kommune_areas


def fetch_regional_land_cover():
    """Fetch land cover by region from AREALDK2."""
    print("\n" + "=" * 60)
    print("Step 2: Fetching regional land cover (AREALDK2)")
    print("=" * 60)

    info = fetch_table_info("AREALDK2")

    # Find variable codes
    var_codes = {v["id"]: v for v in info["variables"]}

    # We need to understand the land cover categories
    cover_var = None
    region_var = None
    unit_var = None
    for vid, vdata in var_codes.items():
        vtext = vdata["text"].lower()
        if vid == "Tid" or vid == "TID":
            continue
        if "dæk" in vtext or "arealtype" in vtext:
            cover_var = vid
        elif "region" in vtext or "omr" in vtext or "landsdel" in vtext or vid == "OMRÅDE":
            region_var = vid
        elif "enhed" in vtext or vid == "ENHED":
            unit_var = vid

    if not cover_var:
        # Try all non-standard vars
        for vid, vdata in var_codes.items():
            if vid not in ("Tid", "TID", "ENHED", "OMRÅDE"):
                cover_var = vid
                break

    print(f"\n  Cover variable: {cover_var}")
    print(f"  Region variable: {region_var or 'OMRÅDE'}")

    # Get latest year
    tid_var = var_codes.get("Tid") or var_codes.get("TID")
    latest_year = tid_var["values"][-1]["id"] if tid_var else "*"
    print(f"  Latest year: {latest_year}")

    # Build request - get km2 if possible
    variables = [
        {"code": region_var or "OMRÅDE", "values": ["*"]},
        {"code": cover_var, "values": ["*"]},
        {"code": tid_var["id"] if tid_var else "Tid", "values": [latest_year]},
    ]

    if unit_var:
        # Prefer km2
        unit_vals = var_codes[unit_var]["values"]
        km2_ids = [v["id"] for v in unit_vals if "km" in v["text"].lower()]
        if km2_ids:
            variables.append({"code": unit_var, "values": [km2_ids[0]]})
        else:
            variables.append({"code": unit_var, "values": [unit_vals[0]["id"]]})

    payload = {
        "table": "AREALDK2",
        "format": "JSON",
        "lang": "da",
        "variables": variables,
    }

    print("\nFetching data...")
    data = api_post("data", payload)
    print(f"  Received {len(data)} rows")

    # Parse: region -> {cover_category -> area}
    region_covers = {}
    all_cover_types = set()

    for row in data:
        region = row.get(region_var or "OMRÅDE", "")
        cover = row.get(cover_var, "")
        value = row.get("INDHOLD", "")

        try:
            area = float(value)
        except (ValueError, TypeError):
            continue

        # Extract region code
        if " " in region:
            region_code = region.split(" ")[0]
        else:
            region_code = region

        all_cover_types.add(cover)

        if region_code not in region_covers:
            region_covers[region_code] = {}
        region_covers[region_code][cover] = area

    print(f"\n  Regions found: {list(region_covers.keys())}")
    print(f"  Land cover types:")
    for ct in sorted(all_cover_types):
        print(f"    - {ct}")

    return region_covers, all_cover_types, latest_year


def classify_cover(cover_text):
    """Classify DST land cover text into: nature, agriculture, urban, water, other."""
    t = cover_text.lower()

    # Nature (counts toward 30% target)
    if any(kw in t for kw in ["skov", "natur", "hede", "mose", "eng", "overdrev",
                               "klit", "strandeng", "våd", "tør", "grøn"]):
        return "nature"
    # Agriculture
    if any(kw in t for kw in ["landbrug", "dyrk", "mark", "gartn", "jordbrug"]):
        return "agriculture"
    # Urban/built
    if any(kw in t for kw in ["bebyg", "befæst", "vej", "bane", "infrastruktur",
                               "erhverv", "bolig", "by"]):
        return "urban"
    # Water
    if any(kw in t for kw in ["vand", "sø", "vandløb", "hav"]):
        return "water"
    return "other"


def compute_kommune_scores(kommune_areas, region_covers, cover_types, year):
    """Distribute regional land cover proportionally to municipalities."""
    print("\n" + "=" * 60)
    print("Step 3: Computing municipal nature ratios")
    print("=" * 60)

    # First classify all cover types
    print("\nLand cover classification:")
    classification = {}
    for ct in cover_types:
        cat = classify_cover(ct)
        classification[ct] = cat
        print(f"  {ct} -> {cat}")

    # Compute region totals and nature shares
    region_nature_shares = {}
    for region_code, covers in region_covers.items():
        total = sum(covers.values())
        nature = sum(v for k, v in covers.items() if classification.get(k) == "nature")
        if total > 0:
            region_nature_shares[region_code] = nature / total
            print(f"\n  Region {region_code}: {nature:.0f} km² natur / {total:.0f} km² total = {nature/total*100:.1f}%")

    # Map each municipality to its region and apply proportional share
    # For proportional distribution, we use the region's nature percentage
    # applied to the municipality's total area
    kommune_names = {}
    try:
        with open("doughnut_scores.csv") as f:
            reader = csv.DictReader(f)
            for row in reader:
                kommune_names[row["kommune_kode"]] = row["kommune_navn"]
    except FileNotFoundError:
        pass

    # Build kommune -> region lookup
    kommune_to_region = {}
    for region, kommuner in REGION_KOMMUNE_MAP.items():
        for k in kommuner:
            kommune_to_region[k] = region

    TARGET = 0.30  # EU Biodiversity Strategy 2030

    results = []
    unmatched = []

    for kode, area_info in sorted(kommune_areas.items()):
        region = kommune_to_region.get(kode)
        if not region:
            unmatched.append(kode)
            continue

        nature_share = region_nature_shares.get(region)
        if nature_share is None:
            # Try without leading zeros etc
            for r_code, r_share in region_nature_shares.items():
                if r_code in region or region in r_code:
                    nature_share = r_share
                    break

        if nature_share is None:
            unmatched.append(kode)
            continue

        total_area = area_info["area_km2"]
        nature_km2 = total_area * nature_share
        ratio = round(nature_share / TARGET * 100, 1)

        name = kommune_names.get(kode, area_info.get("name", f"Kommune {kode}"))
        # Clean name (remove code prefix)
        if " " in name:
            parts = name.split(" ", 1)
            try:
                int(parts[0])
                name = parts[1]
            except ValueError:
                pass

        results.append({
            "kommune_kode": kode,
            "kommune_navn": name,
            "nature_km2": round(nature_km2, 1),
            "total_km2": round(total_area, 1),
            "nature_share_pct": round(nature_share * 100, 1),
            "target_pct": 30.0,
            "land_use_ratio": ratio,
            "region_code": region,
            "data_year": year,
            "method": "proportional_from_region",
        })

    if unmatched:
        print(f"\n  WARNING: {len(unmatched)} municipalities could not be matched to a region:")
        for k in unmatched[:10]:
            print(f"    {k}")

    return results


def main():
    print("=" * 60)
    print("Doughnut Economics — Land Use Data Fetcher")
    print("=" * 60)
    print("Note: Arealdække er kun tilgængeligt på regionsniveau (AREALDK2).")
    print("Kommunefordelingen er proportional - en proxy, ikke eksakte tal.")
    print("For præcise data kræves GIS-analyse af BASEMAP04 + DAGI.")
    print("=" * 60)

    # Step 1: Get municipal areas
    kommune_areas = fetch_kommune_areas()

    # Step 2: Get regional land cover
    region_covers, cover_types, year = fetch_regional_land_cover()

    # Step 3: Compute scores
    results = compute_kommune_scores(kommune_areas, region_covers, cover_types, year)

    # Write output
    output_file = "land_use_scores.csv"
    fieldnames = [
        "kommune_kode", "kommune_navn", "nature_km2", "total_km2",
        "nature_share_pct", "target_pct", "land_use_ratio",
        "region_code", "data_year", "method",
    ]

    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nWrote {len(results)} municipalities to {output_file}")

    # Summary
    if results:
        ratios = [r["land_use_ratio"] for r in results]
        shares = [r["nature_share_pct"] for r in results]
        print(f"\n  Nature share range: {min(shares):.1f}% - {max(shares):.1f}% (mean: {sum(shares)/len(shares):.1f}%)")
        print(f"  Ratio vs 30% target: {min(ratios):.1f} - {max(ratios):.1f} (mean: {sum(ratios)/len(ratios):.1f})")
        print(f"  Municipalities at/above 30% target: {sum(1 for r in ratios if r >= 100)}/{len(ratios)}")

        # Show Thisted
        for r in results:
            if "thisted" in r["kommune_navn"].lower():
                print(f"\n  Thisted Kommune:")
                print(f"    Natur: ~{r['nature_km2']} km² af {r['total_km2']} km² ({r['nature_share_pct']}%)")
                print(f"    Ratio: {r['land_use_ratio']} (vs 30% target)")
                print(f"    Metode: {r['method']} (Region {r['region_code']})")


if __name__ == "__main__":
    main()
