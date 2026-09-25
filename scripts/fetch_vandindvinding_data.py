#!/usr/bin/env python3
"""
Vandindvinding - Doughnut Economics indikator (vand-dimensionen)
================================================================
Al indvinding af grund- og overfladevand i kommunen (almene vandværker,
virksomheder med egen indvinding og markvanding) i mm pr. år over
kommunens landareal, som treårsgennemsnit, målt mod Danmark som helhed.

HVORFOR PR. AREAL OG ALLE KATEGORIER (fra sep. 2026)
----------------------------------------------------
Indtil sep. 2026 målte indikatoren indvinding fra almene vandværker pr.
indbygger. Men indvindingen registreres hvor vandet pumpes op, ikke hvor det
bruges, så tallet viste i praksis hvor HOFOR har kildepladser: Furesø, Ishøj,
Ringsted, Roskilde, Køge og Lejre lå i top, Rødovre, Brøndby og Frederiksberg i
bund, og København var filtreret fra. Og 53 procent af indvindingen (industri
og markvanding) indgik slet ikke.

Presset på grundvandet sker hvor vandet tages. GEUS' opgørelse af den
bæredygtige grundvandsressource (Henriksen m.fl. 2023), som CONCITO (2025)
bruger som Danmarks sikre råderum for vand, regner netop med al indvinding
(ALT-scenariet) og udtrykker både ressource og indvinding i mm pr. år. Denne
indikator bruger samme enhed og afgrænsning. Den ideelle nævner ville være
den bæredygtige ressource pr. område, men GEUS' tal pr. delopland findes kun
som kort, og Miljøstyrelsen vurderer dem ikke-autoritative på den skala.
Derfor måles der mod landsgennemsnittet.

Markvandingen svinger med sommerens nedbør (286 mio. m³ i 2023, 92 mio. m³ i
2024), så scoren er gennemsnittet af de tre seneste år.

BESLUTNING 25. SEP. 2026: PR. AREAL, IKKE PR. INDBYGGER
--------------------------------------------------------
Pr. areal måler presset der, hvor vandet pumpes op, og følger logikken i
EEA's vandudnyttelsesindeks (WEI+), hvor indvindingen sættes i forhold til
den tilgængelige ressource i området. Prisen er de små bykommuner, hvor
arealet er lille i forhold til kildepladserne eller der slet ingen er:
Herlev har ingen indvinding og får 0, Albertslund står grøn, mens
Frederiksberg (ca. 1.260), Ishøj (ca. 1.000) og Furesø (ca. 930) får
ekstreme tal. Tallene er fysisk rigtige, men grundvandsoplandet er større
end kommunen, så de skal formidles forsigtigt. En bykommune, hvis borgere
bruger vand fra nabokommunen, får ikke det forbrug tilskrevet.
Næste skridt: måle indvindingen mod grundvandsdannelsen i kommunen frem for
mod landsgennemsnittet, med vandområdeplanernes screeningskriterium som
grænse (højst 30% af grundvandsdannelsen, GEUS 2023/08 s. 28). Data og
forbehold: docs/oekologisk-gennemgang-sep-2026.md afsnit 5, punkt 1.

Datakilde:
  Danmarks Statistik VANDIND (VANDTYP=TOTVAND, INDKAT 100, 105, 110) og
  AREALDK2 (samlet areal minus søer og vandløb).

Output:
  data/vandindvinding_scores.csv
  Kolonner: kommune_kode, kommune_navn, vandindvinding_mm_aar, vandindvinding_ratio,
            vandindvinding_ref (landstallet), plus det gamle mål pr. indbygger
            (almene vandværker, seneste år) som kildespor.

Kør fra projektets rodmappe:
  python3 scripts/fetch_vandindvinding_data.py
"""

from __future__ import annotations  # kræves: maskinen kører Python 3.9,
# hvor 'float | None' i en signatur ellers fejler ved import (TypeError).

import csv
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kommuner import KOMMUNER  # noqa: E402  (de 98 kommuner, data/kommuner.json)
from dst import api_post, folketal, parse_value, pr_kommune_aar, rullende, seneste  # noqa: E402  (fælles DST-kald)
from dst_aar import perioder_fra, seneste_aar_liste  # noqa: E402

# ── Konstanter ────────────────────────────────────────────────────────────────

OUTPUT_FIL = Path(__file__).resolve().parent.parent / "data" / "vandindvinding_scores.csv"

INDKAT_ALLE = ["100", "105", "110"]   # alment vandværk, virksomheder, markvanding
AAR_I_SNIT = 3


# ── Vandindvinding pr. areal (samme funktion til score og retningspil) ───────

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


def serie_vandindvinding(aar: list[str]) -> dict[tuple[str, str], float]:
    """
    Al vandindvinding (VANDIND, TOTVAND, alle tre kategorier) i mm pr. år over
    kommunens landareal, treårsgennemsnit: værdien for år Y er gennemsnittet af
    Y-2, Y-1 og Y. En kommune uden række i VANDIND et år har ingen registreret
    indvinding og tæller 0. Landstallet (000) er de 98 kommuner samlet.

    mio. m³ / km² = m, så mm = mio. m³ / km² × 1000.

    Bruges af både scoren og retningspilen (fetch_trend_history.py).
    """
    alle = sorted({str(y) for a in aar for y in range(int(a) - AAR_I_SNIT + 1, int(a) + 1)})
    findes = set(perioder_fra("VANDIND", int(alle[0])))
    hent = [a for a in alle if a in findes]
    rows = api_post("VANDIND", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "VANDTYP", "values": ["TOTVAND"]},
        {"code": "INDKAT", "values": INDKAT_ALLE},
        {"code": "Tid", "values": hent},
    ])
    mio_m3 = {k: v for k, v in pr_kommune_aar(rows).items() if k[0] != "000"}
    land = landareal_km2()
    enkelt: dict[tuple[str, str], float] = {}
    for a in hent:
        for kode, km2 in land.items():
            enkelt[(kode, a)] = mio_m3.get((kode, a), 0.0)
    snit = rullende(enkelt, AAR_I_SNIT, "gennemsnit", 6)
    ud: dict[tuple[str, str], float] = {}
    for a in aar:
        med = [k for k in land if (k, a) in snit]
        for kode in med:
            ud[(kode, a)] = round(snit[(kode, a)] / land[kode] * 1000, 2)
        if med:
            ud[("000", a)] = round(sum(snit[(k, a)] for k in med) / sum(land[k] for k in med) * 1000, 2)
    return ud


def serie_vandindvinding_pr_person(aar: list[str]) -> dict[tuple[str, str], float]:
    """Det tidligere mål: almene vandværker (INDKAT=100) i m³ pr. indbygger,
    folketallet 1. januar. Skrives stadig til CSV'en som kildespor, men scores
    ikke (registreringsstedet gør det misvisende, se docstring)."""
    rows = api_post("VANDIND", [
        {"code": "OMRÅDE", "values": ["*"]},
        {"code": "VANDTYP", "values": ["TOTVAND"]},
        {"code": "INDKAT", "values": ["100"]},
        {"code": "Tid", "values": aar},
    ])
    mio_m3 = {k: v for k, v in pr_kommune_aar(rows).items() if k[0] != "000"}
    folk = folketal(sorted({a for _, a in mio_m3}))
    return {(k, a): round(mio * 1_000_000 / folk[(k, a)], 2)
            for (k, a), mio in mio_m3.items() if folk.get((k, a))}


def beregn_og_gem() -> None:
    """Henter nyeste år, beregner ratio (til krydstjek) og skriver CSV'en."""
    sidste = seneste_aar_liste("VANDIND", 1, fallback=["2024"])
    aar, vaerdier, landssnit = seneste(serie_vandindvinding(sidste), tabel="VANDIND")
    if not vaerdier:
        print("FEJL: Ingen gyldige data til rådighed.")
        return
    print(f"  {int(aar) - AAR_I_SNIT + 1}-{aar}: {len(vaerdier)}/98 kommuner")
    print(f"  Danmark samlet: {landssnit:.1f} mm/år (al indvinding over landarealet)")
    pr_person = {k: v for (k, a), v in serie_vandindvinding_pr_person([aar]).items()}

    OUTPUT_FIL.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FIL, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["kommune_kode", "kommune_navn", "vandindvinding_mm_aar",
                         "vandindvinding_ratio", "vandindvinding_ref",
                         "almen_m3_pr_person_seneste_aar"])
        for kode in sorted(KOMMUNER):
            v = vaerdier.get(kode)
            writer.writerow([kode, KOMMUNER[kode], "" if v is None else v,
                             "" if v is None else round(v / landssnit * 100, 2), landssnit,
                             pr_person.get(kode, "")])
    t = vaerdier.get("787")
    print(f"\n  Thisted: {t} mm/år" if t is not None else "\n  Thisted: ingen værdi")
    print(f"\n✓ Gemt: {OUTPUT_FIL} ({len(KOMMUNER)} kommuner)")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("Doughnut Economics - Vandindvinding pr. areal (DST VANDIND)")
    print("=" * 65)
    print("Kilde: Statistikbanken VANDIND, alle indvindingskategorier, treårsgennemsnit")
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
