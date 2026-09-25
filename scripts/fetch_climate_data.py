#!/usr/bin/env python3
"""
Hent territorial CO2e-udledning pr. indbygger fra klimaregnskabet.dk API
for alle 98 danske kommuner.

Krav:
  pip install requests

Brug:
  python3 fetch_climate_data.py [--year 2023] [--output ../data/climate_scores.csv]

Output CSV-kolonner (climate_scores.csv, scores klimapaavirkning-dimensionen):
  kommune_kode, kommune_navn, co2e_per_capita, climate_territorial_ratio, year

Ratio = (co2e_per_capita / Paris-budget) * 100
Grænse = 2,5 ton CO2e/person/år (1,5-graders-niveau for 2030, Hot or Cool Institute 2021;
  indtil sep. 2026 3 ton, som ingen kilde kunne underbygge)
  Besluttet 25. sep. 2026: 2,5 ton beholdes, fordi det er det eneste af de to
  tal med en kilde, og valget flytter ingen farver (alle 98 kommuner er røde
  med begge). Forbehold: Hot or Cool har udledt de 2,5 ton for husholdningernes
  forbrug, og grænsen bruges her også på det territoriale tal (produktion til
  eksport, landbrug). Det står på metodesiden. Gå kun tilbage til 3 ton, hvis
  nogen finder en kilde til det. Se docs/oekologisk-gennemgang-sep-2026.md.
> 100 = overshoot (overskrider planetær grænse)
< 100 = inden for sikker zone

Skriver desuden data/klimaregnskab_kontekst.csv - sektorfordeling af den
territoriale udledning (landbrug/energi/transport), samlet energiforbrug og
VE-el selvforsyningsgrad. Genbruger SAMME API-svar som ovenstående (58 rækker
pr. kald indeholder allerede alt dette) - ingen ekstra kald. Vises som
kontekst i UI'et (indgår ikke i nogen score), se CLAUDE.md punkt 9.
"""

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

import requests
import urllib3
from typing import Optional
urllib3.disable_warnings()

sys.path.insert(0, str(Path(__file__).resolve().parent))
from api_noegler import hent_noegle, kraev_noegle, KLIMA_HJAELP  # noqa: E402
from kommuner import KOMMUNER as _KOMMUNER  # noqa: E402  (de 98 kommuner, data/kommuner.json)

# (kode, navn) med heltalskode, som Klimaregnskabets API kaldes med.
KOMMUNER = [(int(kode), navn) for kode, navn in _KOMMUNER.items()]

API_KEY = hent_noegle("KLIMAREGNSKABET_API_KEY")
API_BASE = "https://klimaregnskabet.dk/api/municipality-data"
PARIS_BUDGET = 2.5  # ton CO2e/person/år (se docstring)


def fetch_kommune(kode: int, navn: str, year: int, debug: bool = False):
    """Henter API-svaret for én kommune og returnerer
    (co2e_per_capita, kontekst_dict). kontekst_dict er None hvis kaldet fejlede."""
    params = {
        "municipality": kode,
        "year": year,
        "type": "Nøgletal",
    }
    headers = {
        "x-api-key": API_KEY,
        "Accept": "application/json",
    }

    for attempt in range(3):
        try:
            r = requests.get(API_BASE, params=params, headers=headers,
                             timeout=20, verify=True)

            if debug and attempt == 0:
                print(f"\n--- DEBUG: API-svar for {navn} ({kode}) ---")
                print(f"URL: {r.url}")
                print(f"Status: {r.status_code}")
                try:
                    print(json.dumps(r.json(), indent=2, ensure_ascii=False)[:3000])
                except Exception:
                    print(r.text[:1000])
                print("--- END DEBUG ---\n")

            if r.status_code == 401:
                print("FEJL: Ugyldig API-nøgle (401).", file=sys.stderr)
                sys.exit(1)
            if r.status_code == 403:
                print("FEJL: Adgang nægtet (403).", file=sys.stderr)
                sys.exit(1)
            if r.status_code != 200:
                print(f"  HTTP {r.status_code} for {navn} (forsøg {attempt+1})", file=sys.stderr)
                time.sleep(2 ** attempt)
                continue

            payload = r.json()
            return _extract_co2_per_capita(payload), _extract_kontekst(payload)

        except requests.RequestException as e:
            print(f"  Netværksfejl for {navn}: {e} (forsøg {attempt+1})", file=sys.stderr)
            if attempt < 2:
                time.sleep(2 ** attempt)

    return None, None


def _extract_co2_per_capita(data) -> Optional[float]:
    """
    Trækker 'Samlet CO2-udledning, Ton CO2e/indb.' ud af API-svaret.
    API'et returnerer to identiske rækker (sektor=Samlet, enhed=Ton CO2e/indb.):
      - Den lille (~3.7 ton): uden landbrug
      - Den store (~11.1 ton): inkl. landbrug - DETTE er hvad klimaregnskabet.dk viser
    Vi tager den STØRSTE af de to for at matche klimaregnskabet.dk's frontside.
    """
    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        for key in ("data", "results", "items", "records"):
            if key in data and isinstance(data[key], list):
                items = data[key]
                break

    candidates = []
    for item in items:
        val = _match_co2_per_capita(item)
        if val is not None:
            candidates.append(val)

    return max(candidates) if candidates else None


def _match_co2_per_capita(item: dict) -> Optional[float]:
    """
    Matcher én record mod sektor=Samlet, type=Samlet CO2-udledning, enhed=Ton CO2e/indb.
    """
    if not isinstance(item, dict):
        return None

    sektor = str(item.get("sektor") or "").lower().strip()
    type_felt = str(item.get("type") or "").lower().strip()
    enhed = str(item.get("enhed") or "").lower().strip()
    vaerdi = item.get("værdi") or item.get("vaerdi") or item.get("value")

    if (sektor == "samlet" and
            "co2-udledning" in type_felt and
            "indb" in enhed and
            vaerdi is not None):
        try:
            return float(vaerdi)
        except (ValueError, TypeError):
            pass

    return None


# Kontekst-felter: (id, type, sektor, enhed). Efterprøvet mod API-svaret
# 11. august 2026 - alle fem findes, og de tre sektorer (Landbrug/Energi/
# Transport) plus Affaldsdeponi/Kemiske processer/Spildevand summerer til
# sektor=Samlet's totale udledning.
KONTEKST_FELTER = [
    ("klima_landbrug", "Samlet CO2-udledning", "Landbrug", "Ton CO2e/indb."),
    ("klima_energi", "Samlet CO2-udledning", "Energi", "Ton CO2e/indb."),
    ("klima_transport", "Samlet CO2-udledning", "Transport", "Ton CO2e/indb."),
    ("energiforbrug", "Samlet slutenergiforbrug", "Samlet", "GJ/indb."),
    ("ve_selvforsyning", "VE-el selvforsyningsgrad (Vind-, sol- og vandbaseret-elproduktion)",
     "Samlet", "%"),
]


def _extract_kontekst(data) -> dict:
    """Trækker sektorfordeling, energiforbrug og VE-selvforsyning ud af samme
    API-svar som _extract_co2_per_capita bruger. Returnerer {id: værdi}."""
    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        for key in ("data", "results", "items", "records"):
            if key in data and isinstance(data[key], list):
                items = data[key]
                break

    ud = {}
    for iid, typ, sektor, enhed in KONTEKST_FELTER:
        for item in items:
            if not isinstance(item, dict):
                continue
            if (str(item.get("type") or "").strip() == typ
                    and str(item.get("sektor") or "").strip() == sektor
                    and str(item.get("enhed") or "").strip() == enhed):
                vaerdi = item.get("værdi") or item.get("vaerdi") or item.get("value")
                if vaerdi is None:
                    continue
                try:
                    val = float(vaerdi)
                except (ValueError, TypeError):
                    continue
                # FÆLDE: ve_selvforsyning leveres som forhold (1.71), ikke
                # procent, selvom enheden hedder "%". Gang med 100.
                if iid == "ve_selvforsyning":
                    val *= 100
                ud[iid] = round(val, 4)
                break
    return ud


def main():
    kraev_noegle("KLIMAREGNSKABET_API_KEY", API_KEY, KLIMA_HJAELP)

    parser = argparse.ArgumentParser(
        description="Hent territorial CO2e pr. capita fra klimaregnskabet.dk"
    )
    parser.add_argument("--year", type=int, default=2023,
                        help="Årstal (2018-2023, default: 2023)")
    parser.add_argument("--output", default="../data/climate_scores.csv",
                        help="Output CSV-sti (default: ../data/climate_scores.csv)")
    parser.add_argument("--debug", action="store_true",
                        help="Print rå API-svar for første kommune")
    args = parser.parse_args()

    print(f"Klimaregnskabet.dk — henter CO2e/indb. for {len(KOMMUNER)} kommuner ({args.year})")
    print(f"Paris-budget: {PARIS_BUDGET} ton CO2e/person/år\n")

    results = []
    kontekst_results = []
    failed = []

    for i, (kode, navn) in enumerate(KOMMUNER):
        # Debug kun for første kommune
        show_debug = args.debug and i == 0
        co2e, kontekst = fetch_kommune(kode, navn, args.year, debug=show_debug)

        if co2e is not None:
            ratio = round(co2e / PARIS_BUDGET * 100, 2)
            results.append({
                "kommune_kode": str(kode),
                "kommune_navn": navn,
                "co2e_per_capita": round(co2e, 3),
                "climate_territorial_ratio": ratio,
                "year": args.year,
            })
            symbol = "🟢" if ratio <= 100 else "🔴"
            print(f"  [{i+1:3d}/{len(KOMMUNER)}] {kode:4d} {navn:25s} "
                  f"{co2e:.2f} ton → {ratio:.1f}% {symbol}")
        else:
            failed.append((kode, navn))
            print(f"  [{i+1:3d}/{len(KOMMUNER)}] {kode:4d} {navn:25s} — INGEN DATA")

        if kontekst:
            kontekst_results.append({
                "kommune_kode": str(kode),
                "kommune_navn": navn,
                "klima_landbrug": kontekst.get("klima_landbrug", ""),
                "klima_energi": kontekst.get("klima_energi", ""),
                "klima_transport": kontekst.get("klima_transport", ""),
                "energiforbrug": kontekst.get("energiforbrug", ""),
                "ve_selvforsyning": kontekst.get("ve_selvforsyning", ""),
                "year": args.year,
            })

        if i < len(KOMMUNER) - 1:
            time.sleep(0.2)

    if kontekst_results:
        kontekst_path = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/klimaregnskab_kontekst.csv"))
        with open(kontekst_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "kommune_kode", "kommune_navn", "klima_landbrug", "klima_energi",
                "klima_transport", "energiforbrug", "ve_selvforsyning", "year"])
            writer.writeheader()
            writer.writerows(kontekst_results)
        print(f"\n✓ Gemt: {kontekst_path} ({len(kontekst_results)} kommuner, kontekst - indgår ikke i score)")

    if results:
        out_path = os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)
        )
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f,
                fieldnames=["kommune_kode", "kommune_navn", "co2e_per_capita",
                            "climate_territorial_ratio", "year"])
            writer.writeheader()
            writer.writerows(results)

        ratios = [r["climate_territorial_ratio"] for r in results]
        avg = sum(ratios) / len(ratios)
        overshoot = sum(1 for r in ratios if r > 100)

        print(f"\n✓ Gemt: {out_path}")
        print(f"  {len(results)} kommuner med data, {len(failed)} uden")
        print(f"  Gennemsnitlig ratio: {avg:.1f}%")
        print(f"  Overshoot (>100% af Paris-budget): {overshoot} kommuner")

        top5 = sorted(results, key=lambda r: r["climate_territorial_ratio"], reverse=True)[:5]
        print(f"\n  Top 5 højeste udledere:")
        for r in top5:
            print(f"    {r['kommune_navn']:25s} {r['co2e_per_capita']:.2f} ton "
                  f"→ {r['climate_territorial_ratio']:.1f}%")
    else:
        print("\n✗ Ingen data hentet. Kør med --debug for at se rå API-svar.")
        sys.exit(1)


if __name__ == "__main__":
    main()

    # ───────────────────────────────────────────────────────────
    # AUTO-REBUILD af master_indicators.csv (tilføjet 2026)
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
