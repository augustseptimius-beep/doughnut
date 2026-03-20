#!/usr/bin/env python3
"""
Doughnut Economics Dashboard — Data Fetcher v4.4

Fetches baseline scores for all 98 Danish municipalities from Danmarks Statistik API.
Metadata-driven: calls tableinfo FIRST for every table and adapts variable codes
to what actually exists, instead of hardcoding.

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
# "want_variables" maps semantic intent to candidate codes/values.
# The resolver tries each candidate against actual tableinfo metadata.
#
# area_var: which variable holds municipality codes (OMRÅDE, BOPOMR, etc.)
#           — resolved dynamically from tableinfo
# want_variables: list of { candidates: [{code, values}], purpose }
#   The resolver tries candidates in order, picks the first that matches.

INDICATORS = [
    {
        "id": "life_expectancy",
        "name": "Middellevetid",
        "table": "HISBK",
        "want_variables": [
            {"purpose": "køn", "candidates": [
                {"code": "KØN", "values": ["TOT"]},
                {"code": "KOEN", "values": ["TOT"]},
            ]},
        ],
        "inverse": False,
        "aggregate": "single",
        "category": "social",
    },
    {
        "id": "education",
        "name": "Kompetencegivende uddannelse (30-34 år)",
        "table": "HFUDD10",
        "want_variables": [
            {"purpose": "alder", "candidates": [
                {"code": "ALDER", "values": ["30-34"]},
            ]},
            {"purpose": "køn", "candidates": [
                {"code": "KØN", "values": ["TOT"]},
                {"code": "KOEN", "values": ["TOT"]},
            ]},
            {"purpose": "herkomst", "candidates": [
                {"code": "HERKOMST", "values": ["TOT"]},
            ]},
            {"purpose": "uddannelse", "candidates": [
                # H-prefixed codes (actual DST format)
                {"code": "HFUDD", "values": ["H20", "H30", "H35", "H40", "H50", "H60"]},
                # Fallback: numeric codes
                {"code": "HFUDD", "values": ["20", "25", "35", "40", "50", "60"]},
            ]},
        ],
        "area_candidates": ["BOPOMR", "OMRÅDE"],
        "inverse": False,
        "aggregate": "sum",
        "category": "social",
    },
    {
        "id": "disposable_income",
        "name": "Disponibel indkomst",
        "table": "INDKP101",
        "want_variables": [
            {"purpose": "køn", "candidates": [
                {"code": "KOEN", "values": ["MOK"]},
                {"code": "KØN", "values": ["MOK"]},
                {"code": "KOEN", "values": ["TOT"]},
                {"code": "KØN", "values": ["TOT"]},
            ]},
            {"purpose": "indkomsttype", "candidates": [
                # Try known codes for disponibel indkomst
                {"code": "INDKOMSTTYPE", "values": ["100"]},
                {"code": "ENESSION", "values": ["DISPONIB"]},
            ], "auto_discover": {
                "search_vars": ["INDKOMSTTYPE", "ENESSION"],
                "search_text": ["disponib", "disp"],
            }},
            {"purpose": "enhed", "candidates": [
                {"code": "ENHED", "values": ["110"]},  # Gennemsnit
                {"code": "ENHED", "values": ["100"]},
            ]},
        ],
        "inverse": False,
        "aggregate": "single",
        "category": "social",
    },
    {
        "id": "employment",
        "name": "Beskæftigelsesfrekvens",
        "table": "RAS200",
        "alt_tables": ["RAS301", "RAS302", "RAS201"],
        "want_variables": [
            {"purpose": "køn", "candidates": [
                {"code": "KØN", "values": ["TOT"]},
                {"code": "KOEN", "values": ["TOT"]},
            ]},
            {"purpose": "alder", "candidates": [
                {"code": "ALDER", "values": ["16-64"]},
                {"code": "ALDER", "values": ["15-64"]},
                {"code": "ALDER", "values": ["TOT"]},
            ]},
            {"purpose": "herkomst", "candidates": [
                {"code": "HERKOMST", "values": ["TOT"]},
                {"code": "HERKOMST", "values": ["00"]},  # RAS200 uses "00" for "I alt"
            ]},
            {"purpose": "frekvens", "candidates": [
                # RAS200 has BEREGNING variable (not FREKVENS)
                {"code": "BEREGNING", "values": ["BFK"]},  # Beskæftigelsesfrekvens
                {"code": "FREKVENS", "values": ["BESKFREKV"]},
                {"code": "FREKVENS", "values": ["ERHVFREKV"]},
            ], "auto_discover": {
                "search_vars": ["BEREGNING", "FREKVENS"],
                "search_text": ["beskæft", "erhverv"],
            }},
        ],
        "inverse": False,
        "aggregate": "single",
        "category": "social",
    },
    {
        "id": "child_poverty",
        "name": "Børnefattigdom (Gini-proxy)",
        "table": "IFOR41",
        "alt_tables": ["IFOR12", "IFOR51"],
        "want_variables": [
            {"purpose": "ulighedsmål", "candidates": [
                # IFOR41 uses ULLIG variable, "70" = Gini-koefficient
                {"code": "ULLIG", "values": ["70"]},
                {"code": "INDKOMSTYPE", "values": ["AEKVIDINGS"]},
            ]},
        ],
        "area_candidates": ["KOMMUNEDK", "OMRÅDE"],
        "inverse": True,
        "aggregate": "single",
        "category": "social",
        "note": "Uses Gini coefficient from IFOR41 as proxy for child poverty",
    },
    {
        "id": "gini",
        "name": "Gini-koefficient",
        "table": "IFOR41",
        "want_variables": [
            {"purpose": "ulighedsmål", "candidates": [
                {"code": "ULLIG", "values": ["70"]},  # Gini-koefficient
                {"code": "INDKOMSTYPE", "values": ["AEKVIDINGS"]},
            ]},
        ],
        "area_candidates": ["KOMMUNEDK", "OMRÅDE"],
        "inverse": True,
        "aggregate": "single",
        "category": "social",
    },
    {
        "id": "vacant_housing",
        "name": "Ubeboede boliger %",
        "table": "BOL101",
        "want_variables": [
            {"purpose": "beboelse", "candidates": [
                {"code": "BEBO", "values": ["2000"]},  # Ubeboede boliger
            ]},
            {"purpose": "anvendelse", "candidates": [
                {"code": "ANVENDELSE", "values": ["125", "130", "140"]},  # Parcelhuse + rækkehuse + etageboliger
            ]},
        ],
        "inverse": True,
        "aggregate": "sum",
        "category": "social",
    },
    {
        "id": "voter_turnout",
        "name": "Valgdeltagelse",
        "table": "VALGK3X",
        "alt_tables": ["VALGK3"],
        "want_variables": [
            {"purpose": "parti/stemmer", "candidates": [
                # Look for total/aggregate values
                {"code": "PARTI", "values": ["Stemme"]},
                {"code": "PARTI", "values": ["I alt"]},
            ], "auto_discover": {
                "search_vars": ["PARTI"],
                "search_text": ["i alt", "total", "stemme"],
            }},
            {"purpose": "stemmer/type", "candidates": [
                {"code": "STEMMER", "values": ["1"]},  # Gyldige stemmer
            ]},
        ],
        "inverse": False,
        "aggregate": "single",
        "category": "social",
    },
]


# ── API helpers ────────────────────────────────────────────────────────

def api_post(endpoint, payload, retries=3, delay=1.0):
    """POST JSON to DST API and return raw response text."""
    url = f"{API_BASE}/{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8")
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
        sample = ", ".join(f"{v['id']}({v.get('text','')})" for v in vals[:6])
        if len(vals) > 6:
            sample += f" ... ({len(vals)} i alt)"
        print(f"    {var['id']:20s}  [{sample}]")


def search_tables(search_text):
    """Search DST tables by text. Returns list of matching tables."""
    payload = {
        "lang": "da",
        "pastDays": 0,
        "includeInactive": False,
    }
    raw = api_post("tables", payload)
    tables = json.loads(raw)
    results = []
    for t in tables:
        text = (t.get("text", "") + " " + t.get("id", "")).lower()
        if search_text.lower() in text:
            results.append(t)
    return results


# ── Variable resolution ───────────────────────────────────────────────

def resolve_area_variable(info, area_candidates=None):
    """
    Find the municipality/area variable in table metadata.
    Tries candidates in order, falls back to heuristic detection.
    Returns (var_code, national_code) or (None, None).
    """
    var_map = {}
    for v in info.get("variables", []):
        var_map[v["id"]] = v

    # Try explicit candidates first
    if area_candidates:
        for candidate in area_candidates:
            if candidate in var_map:
                # Find the national average code (usually "000" or starts with "0")
                nat_code = find_national_code(var_map[candidate])
                return candidate, nat_code

    # Default: try OMRÅDE, BOPOMR, KOMMUNE, KOM
    for candidate in ["OMRÅDE", "BOPOMR", "KOMMUNE", "KOM"]:
        if candidate in var_map:
            nat_code = find_national_code(var_map[candidate])
            return candidate, nat_code

    # Heuristic: find a variable with 99+ values that has "000" or "Hele landet"
    for v in info.get("variables", []):
        vals = v.get("values", [])
        if len(vals) >= 90:
            nat_code = find_national_code(v)
            if nat_code:
                return v["id"], nat_code

    return None, None


def find_national_code(var_info):
    """Find the national average code in a variable's values."""
    for val in var_info.get("values", []):
        vid = val.get("id", "")
        text = val.get("text", "").lower()
        if vid == "000" or "hele landet" in text or "all denmark" in text:
            return vid
    # Fallback: code starting with "0" and 3 digits
    for val in var_info.get("values", []):
        vid = val.get("id", "")
        if vid == "000":
            return vid
    return "000"  # assume standard


def resolve_wanted_variables(want_list, info):
    """
    Resolve wanted variables against actual table metadata.
    Returns dict of {code: [values]} ready for the data API call.
    """
    var_map = {}
    for v in info.get("variables", []):
        var_map[v["id"]] = {val["id"]: val.get("text", "") for val in v.get("values", [])}

    resolved = {}
    for want in want_list:
        purpose = want["purpose"]
        found = False

        # Try candidates in order
        for candidate in want["candidates"]:
            code = candidate["code"]
            values = candidate["values"]

            # Check if code exists (case-insensitive)
            actual_code = None
            for vk in var_map:
                if vk.upper() == code.upper():
                    actual_code = vk
                    break

            if actual_code is None:
                continue

            # Check which values exist
            avail = set(var_map[actual_code].keys())
            matched = [v for v in values if v in avail]

            if matched:
                resolved[actual_code] = matched
                print(f"    ✓ {purpose}: {actual_code}={matched}")
                found = True
                break
            # If code exists but values don't match, try next candidate

        if not found:
            # Try auto_discover if available
            if "auto_discover" in want:
                ad = want["auto_discover"]
                for search_var in ad.get("search_vars", []):
                    actual_code = None
                    for vk in var_map:
                        if vk.upper() == search_var.upper():
                            actual_code = vk
                            break
                    if actual_code is None:
                        continue

                    # Search values by text
                    for search in ad.get("search_text", []):
                        for val_id, val_text in var_map[actual_code].items():
                            if search.lower() in val_text.lower():
                                resolved[actual_code] = [val_id]
                                print(f"    ✓ {purpose} (auto): {actual_code}=[{val_id}] "
                                      f"({val_text})")
                                found = True
                                break
                        if found:
                            break
                    if found:
                        break

        if not found:
            # Print what's available for debugging
            print(f"    ⚠ {purpose}: ingen match fundet")
            for candidate in want["candidates"]:
                code = candidate["code"]
                for vk in var_map:
                    if vk.upper() == code.upper():
                        avail_sample = list(var_map[vk].items())[:10]
                        print(f"      {vk} har: {avail_sample}")

    return resolved


def auto_fill_missing_variables(resolved, info, area_var):
    """
    DST API requires ALL variables to be specified.
    For any table variable not yet in resolved (and not area/Tid),
    try to auto-select a total/aggregate value.
    """
    resolved_upper = {k.upper() for k in resolved}
    skip = {area_var.upper(), "TID"} if area_var else {"TID"}

    for v in info.get("variables", []):
        vid = v["id"]
        if vid.upper() in skip or vid.upper() in resolved_upper:
            continue

        vals = v.get("values", [])
        # Try to find a total/aggregate value
        total_val = None
        for val in vals:
            val_id = val.get("id", "")
            val_text = val.get("text", "").lower()
            if val_id == "TOT" or "i alt" in val_text or "total" in val_text:
                total_val = val_id
                break
        if total_val is None:
            # Try common total codes
            for candidate in ["TOT", "IALT", "000", "0-9", "99"]:
                for val in vals:
                    if val.get("id", "") == candidate:
                        total_val = candidate
                        break
                if total_val:
                    break
        if total_val is None and len(vals) == 1:
            # If only one value exists, use it
            total_val = vals[0].get("id", "")

        if total_val:
            resolved[vid] = [total_val]
            val_text = next(
                (val.get("text", "") for val in vals if val.get("id") == total_val), ""
            )
            print(f"    ✓ auto-fill {vid}=[{total_val}] ({val_text})")
        else:
            # Use first value as last resort, but warn
            if vals:
                first_val = vals[0].get("id", "")
                resolved[vid] = [first_val]
                print(f"    ⚠ auto-fill {vid}=[{first_val}] (første værdi, ingen total fundet)")

    return resolved


# ── Data fetching ─────────────────────────────────────────────────────

def fetch_csv_data(table, variables_dict, area_var="OMRÅDE"):
    """
    Fetch data as semicolon-separated CSV. Returns list of dicts.
    area_var specifies which variable holds the municipality dimension.
    """
    variables = [
        {"code": area_var, "values": ["*"]},
    ]
    for code, values in variables_dict.items():
        variables.append({"code": code, "values": values})
    variables.append({"code": "Tid", "values": ["(1)"]})

    payload = {
        "table": table,
        "format": "CSV",
        "lang": "da",
        "valuePresentation": "CodeAndValue",
        "variables": variables,
    }
    raw = api_post("data", payload)

    reader = csv.DictReader(io.StringIO(raw), delimiter=";")
    return list(reader)


def extract_municipal_values(rows, aggregate="single"):
    """
    Parse CSV rows into {kommune_code: numeric_value}.
    Last column = value (INDHOLD). First column = area.
    Municipality code = first token before space.
    """
    if not rows:
        return {}

    fieldnames = list(rows[0].keys())
    value_col = fieldnames[-1]
    area_col = fieldnames[0]

    result = {}
    for row in rows:
        area = row[area_col].strip()
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
        print(f"  Warning: landsgennemsnit ikke fundet (kode={dk_code})", file=sys.stderr)
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


# ── Fetch one indicator (metadata-driven) ─────────────────────────────

def fetch_indicator(ind):
    """
    Fetch a single indicator: get tableinfo, resolve variables, fetch data.
    Returns (values_dict, national_code) or (None, None) on failure.
    """
    table = ind["table"]
    alt_tables = ind.get("alt_tables", [])
    tables_to_try = [table] + alt_tables

    for tbl in tables_to_try:
        print(f"\n  Prøver tabel {tbl}...")
        try:
            info = get_tableinfo(tbl)
        except Exception as e:
            print(f"  ✗ Tabel {tbl} ikke tilgængelig: {e}")
            continue

        print_tableinfo_summary(info)

        # Resolve area variable
        area_candidates = ind.get("area_candidates")
        area_var, nat_code = resolve_area_variable(info, area_candidates)
        if area_var is None:
            print(f"  ⚠ Ingen kommune-variabel fundet i {tbl}")
            continue

        print(f"    Område-variabel: {area_var}, landskode: {nat_code}")

        # Resolve wanted variables
        resolved_vars = resolve_wanted_variables(ind.get("want_variables", []), info)

        # Auto-fill any mandatory variables not yet resolved
        resolved_vars = auto_fill_missing_variables(resolved_vars, info, area_var)

        # Fetch data
        print(f"  → Henter data: {tbl} [{area_var}=*, {resolved_vars}, Tid=(1)]")
        try:
            rows = fetch_csv_data(tbl, resolved_vars, area_var=area_var)
            values = extract_municipal_values(rows, aggregate=ind.get("aggregate", "single"))
            print(f"  ✓ {len(values)} kommuner med data")
            if nat_code in values:
                print(f"    Landsgennemsnit ({nat_code}): {values[nat_code]}")
            return values, nat_code
        except Exception as e:
            print(f"  ✗ Data-fejl for {tbl}: {e}")
            continue

    return None, None


# ── Step 1 ─────────────────────────────────────────────────────────────

def step1():
    """Verify HISBK table and fetch life expectancy per municipality."""
    print("=" * 60)
    print("TRIN 1: Verificer HISBK (Middellevetid)")
    print("=" * 60)

    print("\n→ Henter tableinfo for HISBK...")
    info = get_tableinfo("HISBK")
    print_tableinfo_summary(info)

    var_map = {v["id"]: v for v in info.get("variables", [])}
    print(f"\n  Alle variabelkoder: {list(var_map.keys())}")

    # Resolve area and sex variables
    area_var, nat_code = resolve_area_variable(info)
    print(f"  Område-variabel: {area_var}, landskode: {nat_code}")

    # Find sex variable
    sex_vars = resolve_wanted_variables(
        [{"purpose": "køn", "candidates": [
            {"code": "KØN", "values": ["TOT"]},
            {"code": "KOEN", "values": ["TOT"]},
        ]}],
        info
    )

    # Auto-fill any remaining mandatory variables
    sex_vars = auto_fill_missing_variables(sex_vars, info, area_var)

    print(f"\n→ Henter data...")
    rows = fetch_csv_data("HISBK", sex_vars, area_var=area_var)
    values = extract_municipal_values(rows)

    print(f"\n  Antal kommuner med data: {len(values)}")
    sample_codes = sorted(values.keys())[:5]
    for code in sample_codes:
        print(f"    {code}: {values[code]}")
    if nat_code in values:
        print(f"    {nat_code} (DK landsgennemsnit): {values[nat_code]}")

    print("\n✓ HISBK verificeret succesfuldt.")
    return values


# ── Step 2 ─────────────────────────────────────────────────────────────

def step2():
    """Fetch all 8 indicators, verifying metadata first."""
    print("=" * 60)
    print("TRIN 2: Hent alle 8 indikatorer (metadata-drevet)")
    print("=" * 60)

    all_data = {}

    for ind in INDICATORS:
        print(f"\n{'━' * 55}")
        print(f"▶ {ind['id']}: {ind['name']}")
        if ind.get("note"):
            print(f"  ({ind['note']})")

        values, nat_code = fetch_indicator(ind)

        all_data[ind["id"]] = {
            "values": values or {},
            "nat_code": nat_code or "000",
            "inverse": ind["inverse"],
            "name": ind["name"],
            "category": ind["category"],
        }

        time.sleep(0.5)

    # Summary
    print(f"\n{'━' * 55}")
    print("Opsummering:")
    for ind_id, data in all_data.items():
        n = len(data["values"])
        status = "✓" if n > 0 else "✗"
        print(f"  {status} {ind_id}: {n} kommuner")

    return all_data


# ── Step 3 ─────────────────────────────────────────────────────────────

def step3(all_data, output_file="doughnut_scores.csv"):
    """Compute ratios and output CSV."""
    print("\n" + "=" * 60)
    print("TRIN 3: Beregn ratioer og gem CSV")
    print("=" * 60)

    # Compute ratios for each indicator
    ratios_by_indicator = {}
    for ind_id, data in all_data.items():
        if not data["values"]:
            print(f"  {ind_id}: ingen data — springes over")
            continue
        ratios = compute_ratios(
            data["values"],
            inverse=data["inverse"],
            dk_code=data["nat_code"],
        )
        ratios_by_indicator[ind_id] = ratios
        print(f"  {ind_id}: {len(ratios)} kommuner med ratio")

    # Collect all municipality codes
    all_codes = set()
    nat_codes = {d["nat_code"] for d in all_data.values()}
    for ratios in ratios_by_indicator.values():
        all_codes.update(ratios.keys())
    all_codes -= nat_codes

    # Get municipality names from HISBK data (already fetched)
    municipality_names = {}
    hisbk_data = all_data.get("life_expectancy", {}).get("values", {})
    if not hisbk_data:
        # Fetch names separately
        try:
            info = get_tableinfo("HISBK")
            area_var, _ = resolve_area_variable(info)
            sex_vars = resolve_wanted_variables(
                [{"purpose": "køn", "candidates": [
                    {"code": "KØN", "values": ["TOT"]},
                    {"code": "KOEN", "values": ["TOT"]},
                ]}], info)
            rows = fetch_csv_data("HISBK", sex_vars, area_var=area_var)
            fieldnames = list(rows[0].keys()) if rows else []
            area_col = fieldnames[0] if fieldnames else "OMRÅDE"
            for row in rows:
                area = row[area_col].strip()
                parts = area.split(maxsplit=1)
                if len(parts) == 2:
                    municipality_names[parts[0]] = parts[1]
        except Exception:
            pass
    else:
        # Re-fetch just to get names
        try:
            info = get_tableinfo("HISBK")
            area_var, _ = resolve_area_variable(info)
            sex_vars = resolve_wanted_variables(
                [{"purpose": "køn", "candidates": [
                    {"code": "KØN", "values": ["TOT"]},
                    {"code": "KOEN", "values": ["TOT"]},
                ]}], info)
            rows = fetch_csv_data("HISBK", sex_vars, area_var=area_var)
            fieldnames = list(rows[0].keys()) if rows else []
            area_col = fieldnames[0] if fieldnames else "OMRÅDE"
            for row in rows:
                area = row[area_col].strip()
                parts = area.split(maxsplit=1)
                if len(parts) == 2:
                    municipality_names[parts[0]] = parts[1]
        except Exception:
            pass

    # Build CSV
    indicator_ids = [ind["id"] for ind in INDICATORS]
    active_ids = [iid for iid in indicator_ids if iid in ratios_by_indicator]

    header = (["kommune_kode", "kommune_navn"]
              + [f"{iid}_ratio" for iid in active_ids]
              + ["social_avg", "overall_avg"])

    output_rows = []
    for code in sorted(all_codes):
        name = municipality_names.get(code, code)
        row = {"kommune_kode": code, "kommune_navn": name}

        social_scores = []
        all_scores = []

        for iid in active_ids:
            ind_def = next((i for i in INDICATORS if i["id"] == iid), None)
            ratio = ratios_by_indicator.get(iid, {}).get(code)
            row[f"{iid}_ratio"] = ratio if ratio is not None else ""
            if ratio is not None:
                all_scores.append(ratio)
                if ind_def and ind_def["category"] == "social":
                    social_scores.append(ratio)

        row["social_avg"] = (round(sum(social_scores) / len(social_scores), 2)
                             if social_scores else "")
        row["overall_avg"] = (round(sum(all_scores) / len(all_scores), 2)
                              if all_scores else "")
        output_rows.append(row)

    # Sort by overall score descending
    output_rows.sort(
        key=lambda r: r["overall_avg"] if isinstance(r["overall_avg"], float) else 0,
        reverse=True,
    )

    # Write CSV
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"\n✓ CSV gemt: {output_file}")
    print(f"  {len(output_rows)} kommuner, {len(active_ids)} indikatorer")

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

    all_data = None
    if args.step == 2 or args.step is None:
        all_data = step2()

    if args.step == 3 or args.step is None:
        if all_data is None:
            print("Henter data for alle indikatorer først...")
            all_data = step2()
        step3(all_data, args.output)

    if args.step is not None and args.step < 3:
        print(f"\n→ Kør næste trin med: python3 fetch_doughnut_data.py --step {args.step + 1}")


if __name__ == "__main__":
    main()
