"""
build_master_csv.py - Konsolider alle rådata-CSV'er til én master-fil i long format.

Kører efter alle fetch-scripts. Producerer data/master_indicators.csv som
webapp'en læser fra. Long format gør filen forsker-venlig (tidy data) og
fjerner behovet for 25+ separate CSV-loads i webapp/lib/data.ts.

Output-skema (én række pr. kommune × indikator):
  kommune_kode, kommune_navn, indicator_id, ratio, raw_value,
  unit, data_year, source, category, dimension

Kør:
  cd /sti/til/doughnut
  python3 scripts/build_master_csv.py

Driftsregel:
  1. Kør fetch-script(s) for de indikatorer du vil opdatere
  2. Kør DETTE script - opdaterer data/master_indicators.csv
  3. Commit + push via GitHub Desktop
"""

import re
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dst_aar import hentede_aar  # noqa: E402

# ─── data_year: kilden har forrang over den hårdkodede værdi ──────────────
# Fetch-scripterne registrerer i data/data_years.json hvilket år de FAKTISK
# hentede en DST-tabel på. Vi bruger det frem for "data_year" i tabellen
# nedenfor, fordi de to ellers driver fra hinanden: aug. 2026 mærkede
# masteren 2024-tal som 2022 for fire indikatorer, og 2019-tal som 2023 for
# education. Hårdkodet data_year bruges nu kun som fallback for kilder der
# ikke er DST-tabeller (Klimaregnskabet, VP3, manuelle filer).
_HENTEDE_AAR = hentede_aar()


def _data_year(ind: dict) -> str:
    """Årstal for indikatoren: registreret hentning > hårdkodet værdi."""
    kilde = ind.get("source") or ""
    m = re.match(r"DST\s+([A-ZÆØÅ0-9_]+)", kilde)
    if m:
        registreret = _HENTEDE_AAR.get(m.group(1))
        if registreret:
            return registreret
    return ind.get("data_year", "")


# ─── Stier ─────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUT = DATA_DIR / "master_indicators.csv"

# ─── INDIKATORER ───────────────────────────────────────────────────────
# Kommer fra data/indikatorer.json via scripts/indikatorregister.py. Det er
# den ENESTE liste der skal opdateres når en indikator tilføjes eller fjernes;
# webappen (shared.ts, data.ts) og build_trends_csv.py læser samme fil.
# Felterne build_master bruger: id, csv, ratio_col, raw_col, unit, data_year,
# source, category, dimension og særreglerne abs_target, navn_key,
# inverse_ratio, special og cap (se registrets "_om" og funktionerne nedenfor).
import indikatorregister as ir  # noqa: E402


# ─── HJÆLPEFUNKTIONER ──────────────────────────────────────────────────

def load_csv(filename):
    """Læs CSV til dict mapped på kommune_kode (eller første kolonne)."""
    path = DATA_DIR / filename
    if not path.exists():
        print(f"  ⚠ CSV mangler: {filename}", file=sys.stderr)
        return []
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_float(s):
    """Returnerer float eller None hvis tom/invalid."""
    if s is None or s == "":
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def invert_to_direct_ratio(inverted):
    """Konverter inverse-eco-ratio til direct: 10000 / inverse.
    Lav inverse = høj forurening = værre → høj direct = overshoot."""
    if inverted is None or inverted == 0:
        return None
    return round(10000 / inverted, 2)


def recycling_eu_target_ratio(pct):
    """Speciel logik for genanvendelse: ratio = (65% EU-mål / faktisk) * 100.
    Over 100 = genanvender for lidt."""
    if pct is None or pct == 0:
        return None
    return round((65 / pct) * 100, 2)


def cba_ratio(estimate):
    """Forbrugs-CO2 ratio = (estimat / 3 ton grænse) * 100."""
    if estimate is None:
        return None
    return round((estimate / 3) * 100, 2)


def worst_of(ratios):
    """Worst-of (max) for ikke-None værdier. Planetary boundary-logik."""
    valid = [r for r in ratios if r is not None]
    return round(max(valid), 2) if valid else None


def average_of(ratios):
    """Gennemsnit for ikke-None værdier. Bruges for forurening-dimensionen."""
    valid = [r for r in ratios if r is not None]
    return round(sum(valid) / len(valid), 2) if valid else None


# ─── HOVEDLOGIK ────────────────────────────────────────────────────────

def build_master():
    print(f"Læser fra {DATA_DIR}")
    print()

    SOCIAL_INDICATORS = ir.sociale()
    ECO_SUB_INDICATORS = ir.oekologiske()
    CONTEXT_INDICATORS = ir.kontekst()
    # Dimensioner der bruger gennemsnit i stedet for worst-of (i dag kun forurening)
    AVERAGE_DIMENSIONS = ir.gennemsnits_dimensioner()

    # Få liste af alle 98 kommuner fra hoved-CSV
    main_rows = load_csv("doughnut_scores.csv")
    if not main_rows:
        print("FEJL: doughnut_scores.csv mangler eller er tom", file=sys.stderr)
        sys.exit(1)

    kommuner = [(r["kommune_kode"], r.get("kommune_navn", "")) for r in main_rows]
    print(f"Fundet {len(kommuner)} kommuner")
    print()

    # Cache CSV-loads (undgå at læse samme fil 5 gange)
    csv_cache = {}
    def get_csv(filename):
        if filename not in csv_cache:
            csv_cache[filename] = load_csv(filename)
        return csv_cache[filename]

    # Output-rækker
    output_rows = []

    # Tæller for diagnostik
    indicator_coverage = {}

    # ─── Sociale indikatorer ────────────────────────────────────
    print("Sociale indikatorer:")
    for ind in SOCIAL_INDICATORS:
        rows = get_csv(ind["csv"])

        # Specialcase: indikatorer der bruger kommunenavn som nøgle (ikke kode)
        if ind.get("navn_key"):
            by_navn = {r.get("kommune_navn"): r for r in rows if r.get("kommune_navn")}
            n = 0
            for kode, navn in kommuner:
                r = by_navn.get(navn)
                if r is None:
                    continue
                ratio = parse_float(r.get(ind["ratio_col"]))
                # Samme 150-cap som kode-nøgle-grenen - ellers undslipper
                # navn-nøgle-indikatorer (vejr_skader) den dokumenterede cap.
                if ratio is not None and ratio > 150:
                    ratio = 150.0
                raw = parse_float(r.get(ind["raw_col"])) if ind["raw_col"] else None
                if ratio is None and raw is None:
                    continue
                output_rows.append({
                    "kommune_kode": kode,
                    "kommune_navn": navn,
                    "indicator_id": ind["id"],
                    "ratio": ratio if ratio is not None else "",
                    "raw_value": raw if raw is not None else "",
                    "unit": ind["unit"],
                    "data_year": _data_year(ind),
                    "source": ind["source"],
                    "category": ind["category"],
                    "dimension": ind["dimension"],
                })
                n += 1
            indicator_coverage[ind["id"]] = n
            print(f"  {ind['id']:25s}: {n}/98 kommuner (navn-nøgle)")
            continue

        # Standard: kommune_kode-nøgle
        by_kode = {}
        for r in rows:
            kode = r.get("kommune_kode")
            if kode and kode not in by_kode:
                by_kode[kode] = r

        n = 0
        for kode, navn in kommuner:
            r = by_kode.get(kode)
            if r is None:
                continue
            raw = parse_float(r.get(ind["raw_col"])) if ind["raw_col"] else None
            abs_target = ind.get("abs_target")
            if abs_target:
                # Absolut score mod fast mål: ratio = raw / mål * 100 (100 = mål nået).
                # Klippet ved 150 som øvrige sociale ratios.
                ratio = round(min((raw / abs_target) * 100, 150.0), 2) if raw is not None else None
            else:
                ratio = parse_float(r.get(ind["ratio_col"]))
                # Cap alle sociale ratios ved 150 for at undgå ekstreme inverse-værdier
                if ratio is not None and ratio > 150:
                    ratio = 150.0
            if ratio is None and raw is None:
                continue
            output_rows.append({
                "kommune_kode": kode,
                "kommune_navn": navn,
                "indicator_id": ind["id"],
                "ratio": ratio if ratio is not None else "",
                "raw_value": raw if raw is not None else "",
                "unit": ind["unit"],
                "data_year": _data_year(ind),
                "source": ind["source"],
                "category": ind["category"],
                "dimension": ind["dimension"],
            })
            n += 1
        indicator_coverage[ind["id"]] = n
        print(f"  {ind['id']:25s}: {n}/98 kommuner")

    # ─── Økologiske sub-indikatorer ──────────────────────────────
    print()
    print("Økologiske sub-indikatorer:")
    # Saml sub-ratios pr. dimension for at beregne worst-of dimension-scores
    eco_sub_ratios = {}  # {kommune_kode: {dimension: [ratios]}}

    for ind in ECO_SUB_INDICATORS:
        rows = get_csv(ind["csv"])

        # Specialcase: cba bruger navn-nøgle, ikke kommune_kode
        if ind.get("special") == "cba_navn_key":
            by_navn = {r.get("kommune"): r for r in rows if r.get("kommune")}
            n = 0
            for kode, navn in kommuner:
                r = by_navn.get(navn)
                if r is None:
                    continue
                raw = parse_float(r.get(ind["raw_col"]))
                if raw is None:
                    continue
                ratio = cba_ratio(raw)
                output_rows.append({
                    "kommune_kode": kode,
                    "kommune_navn": navn,
                    "indicator_id": ind["id"],
                    "ratio": ratio if ratio is not None else "",
                    "raw_value": raw,
                    "unit": ind["unit"],
                    "data_year": _data_year(ind),
                    "source": ind["source"],
                    "category": ind["category"],
                    "dimension": ind["dimension"],
                })
                eco_sub_ratios.setdefault(kode, {}).setdefault(ind["dimension"], []).append(ratio)
                n += 1
            indicator_coverage[ind["id"]] = n
            print(f"  {ind['id']:25s}: {n}/98 kommuner (navn-nøgle)")
            continue

        # Standard: kommune_kode-nøgle
        by_kode = {}
        for r in rows:
            kode = r.get("kommune_kode")
            if kode and kode not in by_kode:
                by_kode[kode] = r

        n = 0
        for kode, navn in kommuner:
            r = by_kode.get(kode)
            if r is None:
                continue

            raw = parse_float(r.get(ind["raw_col"])) if ind["raw_col"] else None

            # Beregn ratio efter speciallogik
            if ind.get("special") == "recycling_eu_target":
                ratio = recycling_eu_target_ratio(raw)
            else:
                csv_ratio = parse_float(r.get(ind["ratio_col"])) if ind["ratio_col"] else None
                if ind.get("inverse_ratio") and csv_ratio is not None:
                    ratio = invert_to_direct_ratio(csv_ratio)
                else:
                    ratio = csv_ratio

            # Cap ekstreme eco-ratioer (fx bioscore med pct nær 0 giver ratio i tusinder).
            # Baren klipper alligevel ved 200; cap holder det viste tal og validering pæn.
            cap = ind.get("cap")
            if cap is not None and ratio is not None and ratio > cap:
                ratio = float(cap)

            if ratio is None and raw is None:
                continue

            output_rows.append({
                "kommune_kode": kode,
                "kommune_navn": navn,
                "indicator_id": ind["id"],
                "ratio": ratio if ratio is not None else "",
                "raw_value": raw if raw is not None else "",
                "unit": ind["unit"],
                "data_year": _data_year(ind),
                "source": ind["source"],
                "category": ind["category"],
                "dimension": ind["dimension"],
            })
            if ratio is not None:
                eco_sub_ratios.setdefault(kode, {}).setdefault(ind["dimension"], []).append(ratio)
            n += 1
        indicator_coverage[ind["id"]] = n
        print(f"  {ind['id']:25s}: {n}/98 kommuner")

    # ─── Kontekst-indikatorer (råværdier, ingen score) ───────────
    print()
    print("Kontekst-indikatorer (vises, scores ikke):")
    for ind in CONTEXT_INDICATORS:
        rows = get_csv(ind["csv"])
        by_kode = {}
        for r in rows:
            kode = r.get("kommune_kode")
            if kode and kode not in by_kode:
                by_kode[kode] = r
        n = 0
        for kode, navn in kommuner:
            r = by_kode.get(kode)
            if r is None:
                continue
            raw = parse_float(r.get(ind["raw_col"]))
            if raw is None:
                continue
            output_rows.append({
                "kommune_kode": kode,
                "kommune_navn": navn,
                "indicator_id": ind["id"],
                "ratio": "",
                "raw_value": raw,
                "unit": ind["unit"],
                "data_year": _data_year(ind),
                "source": ind["source"],
                "category": "context",
                "dimension": ind["dimension"],
            })
            n += 1
        indicator_coverage[ind["id"]] = n
        print(f"  {ind['id']:25s}: {n}/98 kommuner")

    # ─── Worst-of dimension-aggregater ───────────────────────────
    # Skriv én række pr. (kommune, dimension) med dimension-score = worst-of
    # Bruges af webapp som eco_ratios[dimension].
    # Single-indicator dims (klimapaavirkning, biodiversitet, forbrug_co2) får dimension-score
    # = sub-indikatorens ratio. Multi-indicator dims (luftkvalitet, naeringsstoffer, cirkularitet)
    # får worst-of.
    print()
    print("Dimension-aggregater (worst-of):")
    dim_count = 0
    for kode, navn in kommuner:
        dims_for_kommune = eco_sub_ratios.get(kode, {})
        for dim, ratios in dims_for_kommune.items():
            score = average_of(ratios) if dim in AVERAGE_DIMENSIONS else worst_of(ratios)
            if score is None:
                continue
            output_rows.append({
                "kommune_kode": kode,
                "kommune_navn": navn,
                "indicator_id": f"_dim_{dim}",
                "ratio": score,
                "raw_value": "",
                "unit": "",
                "data_year": "",
                "source": "",
                "category": "ecological_dimension",
                "dimension": dim,
            })
            dim_count += 1
    print(f"  {dim_count} dimension-aggregat-rækker")

    # ─── Validering ──────────────────────────────────────────────
    print()
    print("Validering:")
    bad_ratios = [r for r in output_rows if r["ratio"] != "" and (float(r["ratio"]) < 0 or float(r["ratio"]) > 2000)]
    if bad_ratios:
        print(f"  ⚠ {len(bad_ratios)} ratio-værdier uden for forventet interval (0-2000)")
        for r in bad_ratios[:5]:
            print(f"     {r['kommune_navn']} / {r['indicator_id']}: ratio={r['ratio']}")
    else:
        print("  ✓ Alle ratios inden for forventet interval")

    kommuner_med_data = len({r["kommune_kode"] for r in output_rows})
    print(f"  Kommuner med mindst én indikator: {kommuner_med_data}/{len(kommuner)}")

    # ─── Skriv output ────────────────────────────────────────────
    fieldnames = ["kommune_kode", "kommune_navn", "indicator_id", "ratio",
                  "raw_value", "unit", "data_year", "source", "category", "dimension"]
    with open(OUTPUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(output_rows)

    print()
    print(f"✓ Skrev {len(output_rows)} rækker til {OUTPUT.relative_to(ROOT)}")
    print(f"  Filstørrelse: {OUTPUT.stat().st_size / 1024:.1f} KB")


def _tjek_konsistens_efter_build():
    """
    Kører scripts/tjek_konsistens.py efter en vellykket build og printer
    resultatet. Isoleret i egen funktion så en fejl i selve tjekket (fx en
    fremtidig omskrivning af shared.ts som regex'en ikke kan følge) aldrig
    kan vælte en build der ellers lykkedes.

    Lazy import (ikke i toppen af filen): fetch-scripts importerer
    auto_build_master fra dette modul, og en fejl i tjek-modulet må ikke
    vælte selve hentningen ved import.

    Returnerer True (ingen fejl), False (fejl fundet) eller None (tjekket
    kunne ikke køre). None er IKKE det samme som bestået: et tjek der
    crasher er præcis den tavse fejl CLAUDE.md pkt. 19 advarer imod.
    """
    try:
        from tjek_konsistens import main as tjek_main
        print()
        print("=" * 55)
        print("KONSISTENSTJEK (scripts/tjek_konsistens.py)")
        print("=" * 55)
        return tjek_main() == 0
    except Exception as e:
        print()
        print(f"  ✗ KONSISTENSTJEKKET KUNNE IKKE KØRE: {type(e).__name__}: {e}")
        print("    Det tæller IKKE som bestået. Kør: python3 scripts/tjek_konsistens.py")
        return None


def auto_build_master():
    """
    Helper-funktion til auto-rebuild fra fetch-scripts.

    Kaldes til sidst i alle fetch_*.py-scripts så master-CSV'en altid
    er opdateret efter en fetch. Isolerer fejl så build-problemer ikke
    crash'er det kaldende fetch-script (rådata er allerede gemt).

    Brug i fetch-scripts:
        from build_master_csv import auto_build_master
        # ... fetch-logik ...
        auto_build_master()
    """
    print()
    print("=" * 55)
    print("AUTO-REBUILD af master_indicators.csv")
    print("=" * 55)
    try:
        build_master()
        print()
        print("✓ Master-CSV opdateret. Klar til commit + push via GitHub Desktop.")
        # Printer altid, men rejser aldrig - se _tjek_konsistens_efter_build().
        # Et fetch-script skal ikke crashe fordi konsistenstjekket finder noget;
        # det skal bare stå tydeligt i outputtet, så man ser det før commit.
        _tjek_konsistens_efter_build()
    except Exception as e:
        print()
        print(f"✗ FEJL ved rebuild af master-CSV: {e}")
        print("  Rådata-CSV er gemt OK. Kør manuelt: python3 scripts/build_master_csv.py")
        # Vi raise IKKE - rådata er gemt og det er det vigtigste


if __name__ == "__main__":
    build_master()
    # Direkte kørsel (den vej CLAUDE.md instruerer at bruge når et
    # fetch-script IKKE selv printede "✓ Master-CSV opdateret") afbryder MED
    # exit 1 hvis konsistenstjekket finder fejl. Det er her fejlen skal
    # stoppes - før commit, ikke efter deploy.
    resultat = _tjek_konsistens_efter_build()
    if resultat is None:
        sys.exit(2)
    if resultat is False:
        sys.exit(1)
