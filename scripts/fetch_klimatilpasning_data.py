#!/usr/bin/env python3
"""
fetch_klimatilpasning_data.py

Henter F&P's (Forsikring & Pension) vejrrelaterede skadestatistik
pr. 1.000 indbyggere for alle 98 kommuner.

Datakilde: Datawrapper-kort publiceret af F&P i november 2025.
Analyse: "Sådan er Danmark blevet ramt af vejrrelaterede skader de seneste år"
URL: https://fogp.dk/tal-og-analyser/saadan-er-danmark-blevet-ramt-af-vejrrelaterede-skader-de-seneste-aar/

Tidsperiode: Q1 2023 - Q4 2025 (2,5 år akkumuleret)
Dækning: ~90% af forsikringsmarkedet

OBS: Indikatoren er en PROXY for vejrrelateret sårbarhed, ikke en direkte
målestok for klimatilpasningskapacitet. Se data/klimatilpasning.md for fuld
metodediskussion og fremtidige forbedringer.

Output: data/klimatilpasning_scores.csv
Kolonner: kommune_navn, vejr_skader_raw, vejr_skader_ratio

Ratio-konvention: INVERS social indikator.
  ratio = (landsgennemsnit / kommune_val) * 100
  100 = på landsgennemsnit, >100 = bedre end snit (færre skader), <100 = værre

Kør fra projektets rodmappe:
  python3 scripts/fetch_klimatilpasning_data.py
"""

import csv
import statistics
import sys
import urllib.request
from pathlib import Path

DATA_URL = "https://datawrapper.dwcdn.net/NDLlA/4/dataset.csv"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "klimatilpasning_scores.csv"

# Navne-mapping: Datawrapper-navne → kanoniske kommunenavne i projektet
# Kun nødvendig hvis der er uoverensstemmelser. Her er navnene direkte brugbare.
NAME_CORRECTIONS = {
    # "Datawrapper-navn": "Projektnavn",
    # Ingen korrektioner nødvendige per maj 2026
}


def fetch_data() -> list[dict]:
    """Henter CSV fra Datawrapper og returnerer liste af dicts."""
    print(f"Henter vejrskadedata fra F&P (Datawrapper)...")
    request = urllib.request.Request(
        DATA_URL,
        headers={"User-Agent": "Mozilla/5.0 (compatible; doughnut-data-fetcher/1.0)"},
    )
    req = urllib.request.urlopen(request, timeout=20)
    content = req.read().decode("utf-8")
    reader = csv.DictReader(content.splitlines())
    rows = list(reader)
    print(f"  Modtaget {len(rows)} kommuner")
    return rows


def compute_scores(rows: list[dict]) -> tuple[list[dict], float]:
    """
    Beregner inverse ratio: (landsgennemsnit / kommune_val) * 100.
    Lavere skader = højere score = bedre.
    """
    values = []
    for row in rows:
        try:
            val = float(row["antal skader pr 1000"])
            values.append(val)
        except (ValueError, KeyError):
            pass

    if not values:
        print("FEJL: Ingen gyldige værdier fundet", file=sys.stderr)
        sys.exit(1)

    national_avg = statistics.mean(values)
    print(f"  Landsgennemsnit: {national_avg:.2f} skader pr. 1.000 indb.")

    results = []
    for row in rows:
        navn = row["kom"].strip()
        navn = NAME_CORRECTIONS.get(navn, navn)
        try:
            raw = float(row["antal skader pr 1000"])
        except (ValueError, KeyError):
            raw = None

        if raw is not None and raw > 0:
            ratio = round((national_avg / raw) * 100, 2)
        else:
            ratio = None

        results.append({
            "kommune_navn": navn,
            "vejr_skader_raw": raw,
            "vejr_skader_ratio": ratio,
        })

    return results, national_avg


def write_csv(results: list[dict]) -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["kommune_navn", "vejr_skader_raw", "vejr_skader_ratio"])
        writer.writeheader()
        writer.writerows(results)
    print(f"  Gemt: {OUTPUT_FILE}")
    print(f"  Rækker: {len(results)}")


def main():
    rows = fetch_data()
    results, national_avg = compute_scores(rows)

    # Vis top 5 hårdest og mindst ramt
    sorted_by_raw = sorted(results, key=lambda x: x["vejr_skader_raw"] or 0)
    print("\nMindst ramt (lavest råværdi → højest score):")
    for r in sorted_by_raw[:5]:
        print(f"  {r['kommune_navn']}: {r['vejr_skader_raw']} skader/1.000 → score {r['vejr_skader_ratio']}")
    print("Hårdest ramt (højest råværdi → lavest score):")
    for r in sorted_by_raw[-5:]:
        print(f"  {r['kommune_navn']}: {r['vejr_skader_raw']} skader/1.000 → score {r['vejr_skader_ratio']}")

    write_csv(results)
    print("\nFærdigt.")


if __name__ == "__main__":
    main()

    # ───────────────────────────────────────────────────────────
    # AUTO-REBUILD af master_indicators.csv
    # ───────────────────────────────────────────────────────────
    try:
        import sys as _sys
        from pathlib import Path as _Path
        _sys.path.insert(0, str(_Path(__file__).resolve().parent))
        from build_master_csv import auto_build_master
        auto_build_master()
    except Exception as _e:
        print(f"\n⚠ Kunne ikke auto-rebuild master-CSV: {_e}")
        print("  Rådata er gemt. Kør manuelt: python3 scripts/build_master_csv.py")
