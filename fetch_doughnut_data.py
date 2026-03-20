#!/usr/bin/env python3
"""
Doughnut Economics Dashboard — Data Fetcher v4.1

Fetches baseline scores for all 98 Danish municipalities from Danmarks Statistik API.
Methodology:
  - 8 API indicators across social/ecological categories
  - Social: ratio = kommune/DK * 100 (higher is better)
  - Inverse indicators (poverty, Gini, vacant housing): ratio = DK/kommune * 100
  - Ecological: ratio = current load / scientific boundary (100% = boundary)

Usage:
  python3 fetch_doughnut_data.py [--step 1|2|3] [--output results.csv]

  Step 1: Verify HISBK table structure and fetch life expectancy data
  Step 2: Fetch all 8 indicators (verifies each table's metadata first)
  Step 3: Compute ratios and output CSV with all 98 municipalities
  Default (no --step): runs all steps
"""

import argparse
import csv
import io
import json
import sys
import time
import urllib.request
import urllib.error

API_BASE = "https://api.statbank.dk/v1"

# ── Indicator definitions ──────────────────────────────────────────────
# Each indicator:
#   table      — DST table code
#   variables  — dict of variable filters (OMRÅDE and Tid added automatically)
#   value_col  — which column holds the numeric value (usually "INDHOLD")
#   inverse    — if True, ratio = DK/kommune (lower raw value is better)
#   aggregate  — "sum" to sum multiple rows per municipality, else "single"
#   category   — social or ecological
#   name       — human-readable name

INDICATORS = [
    {
        "id": "life_expectancy",
        "name": "Middellevetid",
        "table": "HISBK",
        "variables": {"KØN": ["TOT"]},
        "inverse": False,
        "aggregate": "single",
        "category": "social",
    },
    {
        "id": "education",
        "name": "Kompetencegivende uddannelse (30-34 år)",
        "table": "HFUDD10",
        "variables": {
            "ALDER": ["30-34"],
            "KØN": ["TOT"],
            "HFUDD": ["20", "25", "35", "40", "50", "60"],
        },
        "inverse": False,
        "aggregate": "sum",
        "category": "social",
    },
    {
        "id": "disposable_income",
        "name": "Disponibel indkomst",
        "table": "INDKP101",
        "variables": {"ENESSION": ["DISPONIB"]},
        "inverse": False,
        "aggregate": "single",
        "category": "social",
    },
    {
        "id": "employment",
        "name": "Beskæftigelsesfrekvens",
        "table": "RAS300",
        "variables": {"KØN": ["TOT"], "SOCIO": ["11"]},
        "inverse": False,
        "aggregate": "single",
        "category": "social",
    },
    {
        "id": "child_poverty",
        "name": "Børnefattigdom",
        "table": "IFOR12",
        "variables": {"ALDER": ["0-17 ÅR"]},
        "inverse": True,
        "aggregate": "single",
        "category": "social",
    },
    {
        "id": "gini",
        "name": "Gini-koefficient",
        "table": "IFOR41",
        "variables": {"INDKOMSTYPE": ["AEKVIDINGS"]},
        "inverse": True,
        "aggregate": "single",
        "category": "social",
    },
    {
        "id": "vacant_housing",
        "name": "Ubeboede boliger %",
        "table": "BOL101",
        "variables": {},
        "inverse": True,
        "aggregate": "single",
        "category": "social",
    },
    {
        "id": "voter_turnout",
        "name": "Valgdeltagelse",
        "table": "VALGK3",
        "variables": {"PARTI": ["Stemme"]},
        "inverse": False,
        "aggregate": "single",
        "category": "social",
    },
]


def api_post(endpoint, payload, retries=3, delay=1.0):
    """POST JSON to DST API and return parsed response."""
    url = f"{API_BASE}/{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
                return raw
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"  HTTP {e.code} for {endpoint} (attempt {attempt+1}): {body}",
                  file=sys.stderr)
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))
            else:
                raise
        except urllib.error.URLError as e:
            print(f"  Network error for {endpoint} (attempt {attempt+1}): {e}",
                  file=sys.stderr)
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))
            else:
                raise


def get_tableinfo(table):
    """Fetch table metadata and return parsed JSON."""
    raw = api_post("tableinfo", {"table": table, "lang": "da"})
    return json.loads(raw)


def print_tableinfo_summary(info):
    """Print a compact summary of a table's variables."""
    print(f"\n  Tabel: {info.get('id', '?')} — {info.get('text', '?')}")
    for var in info.get("variables", []):
        vals = var.get("values", [])
        sample = ", ".join(v["id"] for v in vals[:8])
        if len(vals) > 8:
            sample += f" ... ({len(vals)} total)"
        print(f"    {var['id']:20s}  [{sample}]")


def fetch_csv_data(table, extra_variables):
    """Fetch data as semicolon-separated CSV. Returns list of dicts."""
    variables = [
        {"code": "OMRÅDE", "values": ["*"]},
    ]
    for code, values in extra_variables.items():
        variables.append({"code": code, "values": values})
    variables.append({"code": "Tid", "values": ["(1)"]})

    payload = {
        "table": table,
        "format": "CSV",
        "lang": "da",
        "variables": variables,
    }
    raw = api_post("data", payload)

    reader = csv.DictReader(io.StringIO(raw), delimiter=";")
    rows = list(reader)
    return rows


def extract_municipal_values(rows, aggregate="single"):
    """
    Parse CSV rows into {kommune_code: numeric_value}.
    The last column is assumed to be the value (INDHOLD).
    OMRÅDE column contains municipality codes/names.
    """
    # Find the value column (last column) and OMRÅDE column
    if not rows:
        return {}

    fieldnames = list(rows[0].keys())
    value_col = fieldnames[-1]  # INDHOLD is always last
    area_col = fieldnames[0]  # OMRÅDE is always first

    result = {}
    for row in rows:
        area = row[area_col].strip()
        # Extract municipality code — first token before space
        code = area.split()[0] if area else ""
        if not code:
            continue

        raw_val = row[value_col].strip().replace(",", ".")
        if raw_val in ("", "..", "-"):
            continue
        try:
            val = float(raw_val)
        except ValueError:
            continue

        if aggregate == "sum":
            result[code] = result.get(code, 0.0) + val
        else:
            result[code] = val

    return result


def compute_ratios(values, inverse=False, dk_code="000"):
    """
    Compute ratio of each municipality vs national average.
    Normal:  ratio = kommune / DK * 100
    Inverse: ratio = DK / kommune * 100
    """
    dk_val = values.get(dk_code)
    if dk_val is None or dk_val == 0:
        print(f"  Warning: no national average found (code={dk_code})", file=sys.stderr)
        return {}

    ratios = {}
    for code, val in values.items():
        if code == dk_code:
            continue
        if val == 0:
            ratios[code] = 0.0
            continue
        if inverse:
            ratios[code] = round(dk_val / val * 100, 2)
        else:
            ratios[code] = round(val / dk_val * 100, 2)
    return ratios


# ── Step 1 ─────────────────────────────────────────────────────────────

def step1():
    """Verify HISBK table and fetch life expectancy per municipality."""
    print("=" * 60)
    print("TRIN 1: Verificer HISBK (Middellevetid)")
    print("=" * 60)

    print("\n→ Henter tableinfo for HISBK...")
    info = get_tableinfo("HISBK")
    print_tableinfo_summary(info)

    # Check which variable codes actually exist
    var_codes = {v["id"] for v in info.get("variables", [])}
    print(f"\n  Tilgængelige variabelkoder: {var_codes}")

    print("\n→ Henter data (KØN=TOT, seneste år)...")
    rows = fetch_csv_data("HISBK", {"KØN": ["TOT"]})
    values = extract_municipal_values(rows)

    print(f"\n  Antal kommuner med data: {len(values)}")
    # Show a few samples
    sample_codes = sorted(values.keys())[:5]
    for code in sample_codes:
        print(f"    {code}: {values[code]}")
    if "000" in values:
        print(f"    000 (DK landsgennemsnit): {values['000']}")

    print("\n✓ HISBK verificeret succesfuldt.")
    return values


# ── Step 2 ─────────────────────────────────────────────────────────────

def step2():
    """Fetch all 8 indicators, verifying metadata first."""
    print("=" * 60)
    print("TRIN 2: Hent alle 8 indikatorer")
    print("=" * 60)

    all_values = {}

    for ind in INDICATORS:
        table = ind["table"]
        name = ind["name"]
        print(f"\n{'─' * 50}")
        print(f"→ {ind['id']}: {name} (tabel {table})")

        # Verify metadata
        print(f"  Henter tableinfo for {table}...")
        info = get_tableinfo(table)
        print_tableinfo_summary(info)

        available_vars = {v["id"]: [val["id"] for val in v.get("values", [])]
                         for v in info.get("variables", [])}

        # Verify requested variables exist
        final_vars = {}
        for var_code, var_values in ind["variables"].items():
            # Try exact match first, then case-insensitive
            if var_code in available_vars:
                # Verify values exist
                avail_vals = set(available_vars[var_code])
                valid_vals = [v for v in var_values if v in avail_vals]
                if not valid_vals:
                    print(f"  ⚠ Variabel {var_code}: ingen af {var_values} fundet i {list(avail_vals)[:10]}")
                    # Try to find similar values
                    print(f"    Tilgængelige værdier: {sorted(avail_vals)[:15]}")
                else:
                    final_vars[var_code] = valid_vals
            else:
                # Search case-insensitively
                matched = None
                for av in available_vars:
                    if av.upper() == var_code.upper():
                        matched = av
                        break
                if matched:
                    print(f"  Note: bruger '{matched}' i stedet for '{var_code}'")
                    avail_vals = set(available_vars[matched])
                    valid_vals = [v for v in var_values if v in avail_vals]
                    if valid_vals:
                        final_vars[matched] = valid_vals
                    else:
                        print(f"  ⚠ Ingen matchende værdier for {matched}")
                        print(f"    Tilgængelige: {sorted(avail_vals)[:15]}")
                else:
                    print(f"  ⚠ Variabel '{var_code}' findes ikke. Tilgængelige: {list(available_vars.keys())}")

        print(f"  Henter data med variabler: {final_vars}")
        try:
            rows = fetch_csv_data(table, final_vars)
            values = extract_municipal_values(rows, aggregate=ind["aggregate"])
            print(f"  Antal kommuner med data: {len(values)}")
            if "000" in values:
                print(f"  DK-gennemsnit (000): {values['000']}")
            all_values[ind["id"]] = {
                "values": values,
                "inverse": ind["inverse"],
                "name": ind["name"],
                "category": ind["category"],
            }
        except Exception as e:
            print(f"  ✗ Fejl ved hentning af {table}: {e}", file=sys.stderr)
            all_values[ind["id"]] = {
                "values": {},
                "inverse": ind["inverse"],
                "name": ind["name"],
                "category": ind["category"],
            }

        # Be polite to the API
        time.sleep(0.5)

    return all_values


# ── Step 3 ─────────────────────────────────────────────────────────────

def step3(all_values, output_file="doughnut_scores.csv"):
    """Compute ratios and output CSV."""
    print("\n" + "=" * 60)
    print("TRIN 3: Beregn ratioer og gem CSV")
    print("=" * 60)

    # Compute ratios for each indicator
    ratios_by_indicator = {}
    for ind_id, data in all_values.items():
        ratios = compute_ratios(data["values"], inverse=data["inverse"])
        ratios_by_indicator[ind_id] = ratios
        print(f"  {ind_id}: {len(ratios)} kommuner med ratio")

    # Collect all municipality codes
    all_codes = set()
    for ratios in ratios_by_indicator.values():
        all_codes.update(ratios.keys())

    # Get municipality names from first indicator's raw data
    # We'll use codes for now and add names from the data
    municipality_names = {}
    first_ind = INDICATORS[0]
    try:
        rows = fetch_csv_data(first_ind["table"], {"KØN": ["TOT"]})
        fieldnames = list(rows[0].keys()) if rows else []
        area_col = fieldnames[0] if fieldnames else "OMRÅDE"
        for row in rows:
            area = row[area_col].strip()
            parts = area.split(maxsplit=1)
            if len(parts) == 2:
                code, name = parts
                municipality_names[code] = name
            elif len(parts) == 1:
                municipality_names[parts[0]] = parts[0]
    except Exception:
        pass

    # Build CSV
    indicator_ids = [ind["id"] for ind in INDICATORS]
    header = ["kommune_kode", "kommune_navn"] + \
             [f"{iid}_ratio" for iid in indicator_ids] + \
             ["social_avg", "overall_avg"]

    output_rows = []
    for code in sorted(all_codes):
        if code == "000":
            continue
        name = municipality_names.get(code, code)
        row = {"kommune_kode": code, "kommune_navn": name}

        social_scores = []
        all_scores = []

        for ind in INDICATORS:
            iid = ind["id"]
            ratio = ratios_by_indicator.get(iid, {}).get(code)
            row[f"{iid}_ratio"] = ratio if ratio is not None else ""
            if ratio is not None:
                all_scores.append(ratio)
                if ind["category"] == "social":
                    social_scores.append(ratio)

        row["social_avg"] = round(sum(social_scores) / len(social_scores), 2) if social_scores else ""
        row["overall_avg"] = round(sum(all_scores) / len(all_scores), 2) if all_scores else ""
        output_rows.append(row)

    # Sort by overall score descending
    output_rows.sort(key=lambda r: r.get("overall_avg", 0) if r.get("overall_avg", "") != "" else 0, reverse=True)

    # Write CSV
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"\n✓ CSV gemt: {output_file}")
    print(f"  {len(output_rows)} kommuner, {len(indicator_ids)} indikatorer")

    # Show top 10
    print(f"\n  Top 10 kommuner (samlet gennemsnit):")
    for i, row in enumerate(output_rows[:10], 1):
        print(f"    {i:2d}. {row['kommune_kode']} {row['kommune_navn']:25s} "
              f"score={row['overall_avg']}")

    return output_file


# ── Main ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Doughnut Economics — Hent danske kommunedata fra DST"
    )
    parser.add_argument("--step", type=int, choices=[1, 2, 3],
                        help="Kør kun ét trin (default: alle)")
    parser.add_argument("--output", default="doughnut_scores.csv",
                        help="Output CSV-fil (default: doughnut_scores.csv)")
    args = parser.parse_args()

    if args.step == 1 or args.step is None:
        step1()

    if args.step == 2 or args.step is None:
        all_values = step2()

    if args.step == 3 or args.step is None:
        if args.step == 3:
            # Need to fetch data first
            print("Henter data for alle indikatorer...")
            all_values = step2()
        step3(all_values, args.output)

    if args.step is not None and args.step < 3:
        print("\n→ Kør næste trin med: python3 fetch_doughnut_data.py --step", args.step + 1)


if __name__ == "__main__":
    main()
