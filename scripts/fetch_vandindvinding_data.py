#!/usr/bin/env python3
"""
Vandindvinding - Doughnut Economics indikator (vand-dimensionen)
================================================================
Grundvandsindvindingen i kommunen (almene vandværker, virksomheder med egen
indvinding og markvanding) i procent af kommunens andel af Danmarks
bæredygtige grundvandsressource, som treårsgennemsnit. 100 = kommunen
indvinder præcis sin andel af det, der kan indvindes bæredygtigt.

GRÆNSEN (fra sep. 2026)
-----------------------
GEUS har opgjort Danmarks bæredygtige grundvandsressource til ca. 1,1 mia. m³
om året (Henriksen m.fl. 2023, GEUS-rapport 2023/08, bilag 2, rækken HELE i
scenariet med alle indvindinger: 1.104 mio. m³). Opgørelsen bygger på ni
indikatorer, bl.a. vandområdeplanernes udnyttelsesgrad (højst 30% af
grundvandsdannelsen til de øvre magasiner, 50% til de primære) og krav til
vandløbenes vandføring, og det er det tal CONCITO (2025) bruger som Danmarks
sikre råderum for vand.

Ressourcen fordeles på kommunerne efter grundvandsdannelsen: DK-modellens
infiltration til mættet zone (HIP, gennemsnit 1991-2020) gange landarealet
(fetch_grundvandsdannelse.py). En kommune med sandjord og meget nedsivning
får altså en større andel end en kommune med lerjord og samme areal.

  ressource_k (mm/år) = infiltration_k × 1.104 mio. m³ / Σ(infiltration × landareal)
  udnyttelse_k (%)    = grundvandsindvinding_k (mm/år) / ressource_k × 100

Tælleren er grundvand (VANDIND, VANDTYP=GVAND), fordi ressourcen er
grundvand. DST's grundvandsindvinding 2017-2021 (737 mio. m³ om året i snit)
rammer GEUS' egen indvinding for samme periode (734 mio. m³), så de to
opgørelser har samme afgrænsning. Overfladevandet (ca. 240 mio. m³, især
virksomheder) indgik indtil denne ændring.

Forbehold, som også står på metodesiden:
- Fordelingen efter grundvandsdannelse er en forenkling. GEUS' ressource pr.
  område afhænger også af vandløb og magasinernes dybde; på Sjælland er den
  mindre i forhold til nedsivningen end i Jylland. Se kontrollen i
  docs/oekologisk-gennemgang-sep-2026.md.
- Samsø og Læsø ligger uden for DK-modellen og får ingen vand-score frem
  for et gæt.
- Indvindingen registreres hvor vandet pumpes op. Små bykommuner med egne
  kildepladser (Frederiksberg, Furesø, Ishøj) får meget høje tal, fordi
  grundvandsoplandet er større end kommunen, og en bykommune, hvis borgere
  bruger vand fra nabokommunen, får ikke forbruget tilskrevet.

HISTORIK
--------
Indtil sep. 2026 målte indikatoren almene vandværker pr. indbygger, hvilket i
praksis viste hvor HOFOR har kildepladser (Furesø, Ishøj og Lejre højest,
København filtreret fra), og 53% af indvindingen indgik ikke. Derefter kort
al indvinding (grund- og overfladevand) pr. landareal mod landsgennemsnittet
(besluttet 25. sep. 2026), og samme dag skiftet til den bæredygtige ressource
som nævner, da grundvandsdannelsen blev tilgængelig fra HIP.

Markvandingen svinger med sommerens nedbør, så scoren er gennemsnittet af de
tre seneste år.

Datakilde:
  Danmarks Statistik VANDIND (VANDTYP=GVAND, INDKAT 100, 105, 110) og
  AREALDK2 (samlet areal minus søer og vandløb); data/grundvandsdannelse_scores.csv.

Output:
  data/vandindvinding_scores.csv

Kør fra projektets rodmappe (efter fetch_grundvandsdannelse.py):
  python3 scripts/fetch_vandindvinding_data.py
"""

from __future__ import annotations  # kræves: maskinen kører Python 3.9,
# hvor 'float | None' i en signatur ellers fejler ved import (TypeError).

import csv
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kommuner import KOMMUNER  # noqa: E402  (de 98 kommuner, data/kommuner.json)
from dst import api_post, parse_value, pr_kommune_aar, rullende, seneste  # noqa: E402  (fælles DST-kald)
from dst_aar import perioder_fra, seneste_aar_liste  # noqa: E402

# ── Konstanter ────────────────────────────────────────────────────────────────

DATA = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FIL = DATA / "vandindvinding_scores.csv"
GRUNDVANDSDANNELSE_CSV = DATA / "grundvandsdannelse_scores.csv"

INDKAT_ALLE = ["100", "105", "110"]   # alment vandværk, virksomheder, markvanding
VANDTYP = "GVAND"                     # grundvand, samme afgrænsning som GEUS' ressource
AAR_I_SNIT = 3
RESSOURCE_DK_MIO_M3 = 1104            # GEUS 2023/08, bilag 2, HELE, alle indvindinger (ALT)


# ── Nævneren: kommunens andel af den bæredygtige ressource ───────────────────

def landareal_km2() -> dict[str, float]:
    """Landareal (samlet areal minus søer og vandløb) i km² pr. kommune fra
    AREALDK2's nyeste år. Arealet ændrer sig så lidt, at samme nævner bruges
    for alle år."""
    aar = seneste_aar_liste("AREALDK2", 1, fallback=["2024"])
    rows = api_post("AREALDK2", [
        {"code": "ARE1", "values": ["TOT", "G1", "G2"]},
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "ENHED", "values": ["8120"]},
        {"code": "Tid", "values": aar},
    ])
    km2: dict[str, float] = {}
    for r in rows:
        kode = (r.get("OMRÅDE") or "").strip()
        v = parse_value(r.get("INDHOLD", ""))
        if kode in KOMMUNER and v is not None:
            km2[kode] = km2.get(kode, 0.0) + (v if r["ARE1"] == "TOT" else -v)
    return km2


def infiltration_mm() -> dict[str, float]:
    """Infiltration til mættet zone (mm/år) pr. kommune fra
    fetch_grundvandsdannelse.py."""
    if not GRUNDVANDSDANNELSE_CSV.exists():
        raise SystemExit(f"FEJL: {GRUNDVANDSDANNELSE_CSV.name} mangler - kør "
                         "scripts/fetch_grundvandsdannelse.py først")
    with open(GRUNDVANDSDANNELSE_CSV, encoding="utf-8") as f:
        ud = {r["kommune_kode"]: float(r["infiltration_mm_aar"])
              for r in csv.DictReader(f) if r["infiltration_mm_aar"]}
    # Samsø og Læsø ligger uden for DK-modellen og har intet tal.
    if not set(ud) <= set(KOMMUNER) or len(ud) < 90:
        raise SystemExit(f"FEJL: {GRUNDVANDSDANNELSE_CSV.name} har {len(ud)} kommuner med værdi")
    return ud


def ressource_mm(land: dict[str, float]) -> dict[str, float]:
    """Kommunens andel af den bæredygtige ressource, udtrykt i mm/år over
    kommunens landareal: infiltrationen gange landets samlede forhold mellem
    ressource og infiltration."""
    infil = infiltration_mm()
    # mm × km² = 1.000 m³, så Σ(mm × km²) / 1.000 = mio. m³
    samlet_infil_mio_m3 = sum(infil[k] * land[k] for k in infil) / 1000
    andel = RESSOURCE_DK_MIO_M3 / samlet_infil_mio_m3
    return {k: infil[k] * andel for k in infil}


# ── Tæller og score (samme funktion til score og retningspil) ────────────────

def serie_indvinding_mm(aar: list[str], land: dict[str, float]) -> dict[tuple[str, str], float]:
    """
    Grundvandsindvinding (alle tre kategorier) i mm pr. år over kommunens
    landareal, treårsgennemsnit: værdien for år Y er gennemsnittet af Y-2, Y-1
    og Y. En kommune uden række i VANDIND et år har ingen registreret
    indvinding og tæller 0. mio. m³ / km² × 1000 = mm.
    """
    alle = sorted({str(y) for a in aar for y in range(int(a) - AAR_I_SNIT + 1, int(a) + 1)})
    findes = set(perioder_fra("VANDIND", int(alle[0])))
    hent = [a for a in alle if a in findes]
    rows = api_post("VANDIND", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "VANDTYP", "values": [VANDTYP]},
        {"code": "INDKAT", "values": INDKAT_ALLE},
        {"code": "Tid", "values": hent},
    ])
    mio_m3 = {k: v for k, v in pr_kommune_aar(rows).items() if k[0] != "000"}
    enkelt: dict[tuple[str, str], float] = {}
    for a in hent:
        for kode in land:
            enkelt[(kode, a)] = mio_m3.get((kode, a), 0.0)
    snit = rullende(enkelt, AAR_I_SNIT, "gennemsnit", 6)
    return {(k, a): snit[(k, a)] / land[k] * 1000 for (k, a) in snit if a in aar}


def serie_vandindvinding(aar: list[str]) -> dict[tuple[str, str], float]:
    """
    Grundvandsindvinding i procent af kommunens andel af den bæredygtige
    ressource, treårsgennemsnit. Landstallet (000) er Danmarks samlede
    indvinding i procent af 1.104 mio. m³.

    Bruges af både scoren og retningspilen (fetch_trend_history.py). Nævneren
    er fast, så pilen følger indvindingen.
    """
    land = landareal_km2()
    ress = ressource_mm(land)
    indv = serie_indvinding_mm(aar, land)
    ud: dict[tuple[str, str], float] = {}
    for a in aar:
        med = [k for k in land if (k, a) in indv]
        for k in med:
            if k in ress:
                ud[(k, a)] = round(indv[(k, a)] / ress[k] * 100, 2)
        if med:
            # Landstallet er Danmark samlet, inkl. Samsø og Læsø, mod hele ressourcen.
            samlet_mio_m3 = sum(indv[(k, a)] * land[k] for k in med) / 1000
            ud[("000", a)] = round(samlet_mio_m3 / RESSOURCE_DK_MIO_M3 * 100, 2)
    return ud


def beregn_og_gem() -> None:
    """Henter nyeste år og skriver CSV'en."""
    sidste = seneste_aar_liste("VANDIND", 1, fallback=["2024"])
    aar, vaerdier, landssnit = seneste(serie_vandindvinding(sidste), tabel="VANDIND")
    if not vaerdier:
        print("FEJL: Ingen gyldige data til rådighed.")
        return
    land = landareal_km2()
    ress = ressource_mm(land)
    indv = serie_indvinding_mm([aar], land)
    infil = infiltration_mm()
    print(f"  {int(aar) - AAR_I_SNIT + 1}-{aar}: {len(vaerdier)}/98 kommuner")
    print(f"  Danmark samlet: {landssnit:.1f}% af den bæredygtige ressource "
          f"({RESSOURCE_DK_MIO_M3} mio. m³/år)")

    OUTPUT_FIL.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FIL, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["kommune_kode", "kommune_navn", "udnyttelse_pct", "vandindvinding_ratio",
                         "grundvandsindvinding_mm_aar", "ressource_mm_aar", "infiltration_mm_aar",
                         "udnyttelse_dk_pct"])
        for kode in sorted(KOMMUNER):
            v = vaerdier.get(kode)
            writer.writerow([kode, KOMMUNER[kode], "" if v is None else v, "" if v is None else v,
                             round(indv.get((kode, aar), 0.0), 2),
                             "" if kode not in ress else round(ress[kode], 2),
                             infil.get(kode, ""), landssnit])
    t = vaerdier.get("787")
    print(f"\n  Thisted: {t}% af sin andel af ressourcen" if t is not None else "\n  Thisted: ingen værdi")
    over = sum(1 for v in vaerdier.values() if v > 100)
    print(f"  Over 100%: {over} kommuner")
    print(f"\n✓ Gemt: {OUTPUT_FIL} ({len(KOMMUNER)} kommuner)")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("Doughnut Economics - Grundvandsindvinding mod bæredygtig ressource")
    print("=" * 65)
    print("Kilde: DST VANDIND (grundvand) + GEUS 2023/08 + DK-modellen (HIP)")
    print()

    beregn_og_gem()

    print("\nFærdig!")


if __name__ == "__main__":
    main()

    # ───────────────────────────────────────────────────────────────
    # AUTO-REBUILD af master_indicators.csv
    # ───────────────────────────────────────────────────────────────
    try:
        import sys as _sys
        from pathlib import Path as _Path
        _sys.path.insert(0, str(_Path(__file__).resolve().parent))
        from build_master_csv import auto_build_master
        auto_build_master()
    except Exception as _e:
        print(f"\n⚠ Kunne ikke auto-rebuild master-CSV: {_e}")
        print("  Rådata er gemt. Kør manuelt: python3 scripts/build_master_csv.py")
