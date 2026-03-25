#!/usr/bin/env python3
"""
Fetch territorial CO2e emissions per capita from klimaregnskabet.dk API
for all 98 Danish municipalities.

Requires:
  - KLIMAREGNSKAB_API_KEY environment variable (or .env file in project root)

Usage:
  python3 fetch_climate_data.py [--year 2023] [--output climate_scores.csv]

Output CSV columns:
  kommune_kode, kommune_navn, co2e_per_capita, climate_territorial_ratio

Ratio = (actual / Paris budget) * 100
Paris budget = 3 ton CO2e per person per year
> 100 means overshoot (exceeding planetary boundary)
"""

import argparse
import csv
import os
import sys
import time

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Try to load .env file
def load_dotenv():
    """Load .env file from project root if it exists."""
    env_paths = [
        os.path.join(os.path.dirname(__file__), ".env"),
        os.path.join(os.path.dirname(__file__), "webapp", ".env.local"),
    ]
    for env_path in env_paths:
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, _, value = line.partition("=")
                        key = key.strip()
                        value = value.strip().strip("'\"")
                        os.environ.setdefault(key, value)

load_dotenv()

API_BASE = "https://api.klimaregnskabet.dk/v1"
PARIS_BUDGET_TONS = 3.0  # ton CO2e per person per year

# All 98 Danish municipality codes
KOMMUNE_CODES = [
    101, 147, 151, 153, 155, 157, 159, 161, 163, 165, 167, 169, 173, 175,
    183, 185, 187, 190, 201, 210, 217, 219, 223, 230, 240, 250, 253, 259,
    260, 265, 269, 270, 306, 316, 320, 326, 329, 330, 336, 340, 350, 360,
    370, 376, 390, 400, 410, 420, 430, 440, 450, 461, 479, 480, 482, 492,
    510, 530, 540, 550, 561, 563, 573, 575, 580, 607, 615, 621, 630, 657,
    661, 665, 671, 706, 707, 710, 727, 730, 740, 741, 746, 751, 756, 760,
    766, 773, 779, 787, 791, 810, 813, 820, 825, 840, 846, 849, 851, 860,
]


def api_get(endpoint, params=None, retries=4):
    """GET request to klimaregnskabet API with exponential backoff."""
    api_key = os.environ.get("KLIMAREGNSKAB_API_KEY")
    if not api_key:
        print("FEJL: KLIMAREGNSKAB_API_KEY ikke fundet.", file=sys.stderr)
        print("Sæt den som environment variable eller i .env-filen.", file=sys.stderr)
        sys.exit(1)

    url = f"{API_BASE}/{endpoint}"

    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params,
                                headers={"x-api-key": api_key}, timeout=30,
                                verify=False)
            if resp.status_code == 401:
                print(f"  HTTP 401 for {url}: Ugyldig API-nøgle.", file=sys.stderr)
                sys.exit(1)
            if resp.status_code >= 400:
                print(f"  HTTP {resp.status_code} for {url} (forsøg {attempt+1}): {resp.text[:200]}",
                      file=sys.stderr)
                if attempt < retries - 1:
                    wait = 2 ** (attempt + 1)
                    print(f"  → Venter {wait}s...", file=sys.stderr)
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"  Netværksfejl for {url} (forsøg {attempt+1}): {e}",
                  file=sys.stderr)
            if attempt < retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"  → Venter {wait}s...", file=sys.stderr)
                time.sleep(wait)
            else:
                raise


def fetch_all_municipalities(year=2023):
    """
    Fetch CO2e emissions per capita for all municipalities.
    Returns dict of {kommune_code: {name, co2e_per_capita}}.
    """
    results = {}

    print(f"Henter klimadata for {len(KOMMUNE_CODES)} kommuner (år {year})...")
    print()

    for i, code in enumerate(KOMMUNE_CODES):
        try:
            data = api_get("emissions", {"kommune": code, "year": year})

            # Extract relevant fields from response
            # API response structure may vary — handle flexibly
            if isinstance(data, dict):
                # Try common field names for CO2e per capita
                co2e = None
                name = str(code)

                # Try to extract municipality name
                for key in ["kommune_navn", "municipality", "name", "kommune"]:
                    if key in data and isinstance(data[key], str):
                        name = data[key]
                        break

                # Try to extract per capita emissions (ton CO2e)
                for key in [
                    "co2e_per_capita",
                    "emissions_per_capita",
                    "ton_co2e_per_capita",
                    "per_capita",
                    "territorial_per_capita",
                    "co2_per_capita",
                ]:
                    if key in data and data[key] is not None:
                        co2e = float(data[key])
                        break

                # If nested structure, look deeper
                if co2e is None and "data" in data:
                    inner = data["data"]
                    if isinstance(inner, dict):
                        for key in ["co2e_per_capita", "emissions_per_capita",
                                    "ton_co2e_per_capita", "per_capita"]:
                            if key in inner and inner[key] is not None:
                                co2e = float(inner[key])
                                break
                    elif isinstance(inner, list) and len(inner) > 0:
                        item = inner[0]
                        if isinstance(item, dict):
                            for key in ["co2e_per_capita", "emissions_per_capita",
                                        "ton_co2e_per_capita", "per_capita"]:
                                if key in item and item[key] is not None:
                                    co2e = float(item[key])
                                    break

                # If still no per capita, try total emissions / population
                if co2e is None:
                    total = None
                    pop = None
                    for key in ["total_emissions", "total_co2e", "emissions"]:
                        if key in data and data[key] is not None:
                            total = float(data[key])
                            break
                    for key in ["population", "inhabitants", "befolkning"]:
                        if key in data and data[key] is not None:
                            pop = float(data[key])
                            break
                    if total is not None and pop is not None and pop > 0:
                        co2e = total / pop

                if co2e is not None:
                    results[str(code)] = {
                        "name": name,
                        "co2e_per_capita": round(co2e, 3),
                    }
                    status = "✓"
                else:
                    status = "⚠ (ingen per-capita data fundet)"
                    # Save raw response for debugging first municipality
                    if len(results) == 0:
                        print(f"  DEBUG: Rå API-svar for kommune {code}:")
                        print(f"  {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")

            elif isinstance(data, list):
                # If response is a list, take first item
                if len(data) > 0:
                    item = data[0]
                    co2e = None
                    name = str(code)
                    if isinstance(item, dict):
                        for key in ["kommune_navn", "municipality", "name"]:
                            if key in item and isinstance(item[key], str):
                                name = item[key]
                                break
                        for key in ["co2e_per_capita", "emissions_per_capita",
                                    "ton_co2e_per_capita", "per_capita"]:
                            if key in item and item[key] is not None:
                                co2e = float(item[key])
                                break
                    if co2e is not None:
                        results[str(code)] = {
                            "name": name,
                            "co2e_per_capita": round(co2e, 3),
                        }
                        status = "✓"
                    else:
                        status = "⚠"
                        if len(results) == 0:
                            print(f"  DEBUG: Rå API-svar for kommune {code}:")
                            print(f"  {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
                else:
                    status = "⚠ (tom liste)"
            else:
                status = "⚠ (uventet format)"

            print(f"  [{i+1:3d}/{len(KOMMUNE_CODES)}] {code} {status}"
                  + (f"  {results[str(code)]['co2e_per_capita']} ton/person"
                     if str(code) in results else ""))

        except Exception as e:
            print(f"  [{i+1:3d}/{len(KOMMUNE_CODES)}] {code} ✗ {e}")

        # Rate limit: be polite
        if i < len(KOMMUNE_CODES) - 1:
            time.sleep(0.3)

    return results


def compute_ratios(results):
    """
    Compute ecological ratio: actual / Paris budget * 100.
    > 100 = overshoot (bad)
    = 100 = at boundary
    < 100 = within safe space (good)
    """
    for code, data in results.items():
        co2e = data["co2e_per_capita"]
        ratio = round(co2e / PARIS_BUDGET_TONS * 100, 2)
        data["ratio"] = ratio
    return results


def save_csv(results, output_file):
    """Save results to CSV."""
    header = ["kommune_kode", "kommune_navn", "co2e_per_capita",
              "climate_territorial_ratio"]

    rows = []
    for code in sorted(results.keys(), key=lambda c: int(c)):
        data = results[code]
        rows.append({
            "kommune_kode": code,
            "kommune_navn": data["name"],
            "co2e_per_capita": data["co2e_per_capita"],
            "climate_territorial_ratio": data["ratio"],
        })

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✓ CSV gemt: {output_file}")
    print(f"  {len(rows)} kommuner")

    # Stats
    ratios = [r["climate_territorial_ratio"] for r in rows]
    if ratios:
        avg = sum(ratios) / len(ratios)
        over = sum(1 for r in ratios if r > 100)
        print(f"  Gennemsnit ratio: {avg:.1f}%")
        print(f"  Overshoot (>100%): {over} kommuner")
        print(f"  Paris-budget: {PARIS_BUDGET_TONS} ton CO2e/person/år")

    # Top 5 highest emitters
    rows.sort(key=lambda r: r["climate_territorial_ratio"], reverse=True)
    print(f"\n  Top 5 højeste udledere:")
    for r in rows[:5]:
        print(f"    {r['kommune_kode']} {r['kommune_navn']:25s} "
              f"{r['co2e_per_capita']:.1f} ton → {r['climate_territorial_ratio']}%")


def main():
    parser = argparse.ArgumentParser(
        description="Hent territorial CO2e-data fra klimaregnskabet.dk"
    )
    parser.add_argument("--year", type=int, default=2023,
                        help="Årstal at hente data for (default: 2023)")
    parser.add_argument("--output", default="climate_scores.csv",
                        help="Output CSV-fil (default: climate_scores.csv)")
    args = parser.parse_args()

    results = fetch_all_municipalities(year=args.year)

    if not results:
        print("\nIngen data hentet. Tjek API-nøgle og netværk.", file=sys.stderr)
        sys.exit(1)

    compute_ratios(results)
    save_csv(results, args.output)


if __name__ == "__main__":
    main()
