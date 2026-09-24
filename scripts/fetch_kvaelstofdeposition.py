#!/usr/bin/env python3
"""
fetch_kvaelstofdeposition.py - kvælstofnedfald fra luften pr. kommune (DCE)
============================================================================

Indikatoren `n_deposition` under Næringsstoffer: det gennemsnitlige nedfald af
kvælstof fra luften (tør- og våddeposition af NHx og NOy) i kg N pr. ha pr. år,
målt mod tålegrænsen for følsom dansk natur.

DATAKILDE
---------
DCE/Aarhus Universitets DEHM-modelberegninger, der offentliggøres hvert år med
NOVANA-rapporten "Atmosfærisk deposition" og som tabel pr. kommune:
  https://www2.dmu.dk/1_viden/2_Miljoe-tilstand/3_luft/4_spredningsmodeller/
  5_Depositionsberegninger/<år>/depositiontables/<år>.dk.ntot.kommuner.html
Kolonnen "Total deposition/areal" (kg N/ha). Tabellerne findes sammenhængende
fra 2014; 2010, 2011 og 2013 mangler hos DCE.

GRÆNSEN
-------
10 kg N/ha/år. Tålegrænser for kvælstof er empirisk fastsatte intervaller pr.
naturtype (UNECE-luftkonventionen; Bobbink m.fl. 2022, oversat til danske
naturtyper af DCE: Bak 2024, fagligt notat 2024|16). For de udbredte følsomme
naturtyper - heder, klitter og klithede - er intervallet 5-15 kg N/ha/år, og
10 er midten. DCE sammenholder selv gitterdepositionen (4-18 kg N/ha) med
netop disse intervaller i "Atmosfærisk deposition 2023" (SR626).
Med den nedre grænse (5) ville alle kommuner være langt over; med den øvre
(15) ville ingen være det. Valget er dokumenteret på metodesiden.

TRE ÅR
------
Nedfaldet svinger ca. 7 procent fra år til år med nedbøren (SR626). Scoren
er derfor gennemsnittet af de tre seneste år - samme periode som DCE's egne
treårskort på Miljøportalen (fx 2022-2024).

Brug (fra projektets rodmappe):
  python3 scripts/fetch_kvaelstofdeposition.py

Output:
  data/n_deposition_scores.csv
"""

from __future__ import annotations

import csv
import html
import re
import statistics
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kommuner import KOMMUNER, kode_for_navn  # noqa: E402
from dst import rullende  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "n_deposition_scores.csv"

URL = ("https://www2.dmu.dk/1_viden/2_Miljoe-tilstand/3_luft/4_spredningsmodeller/"
       "5_Depositionsberegninger/{aar}/depositiontables/{aar}.dk.ntot.kommuner.html")
FOERSTE_AAR = 2014          # første år i den sammenhængende række hos DCE
TAALEGRAENSE = 10.0         # kg N/ha/år, se docstring
AAR_I_SNIT = 3
TABEL = "DCE DEHM"          # nøgle i data/data_years.json

# DCE bruger enkelte gamle eller afvigende navne.
NAVNE = {
    "Københavns": "København",
    "Århus": "Aarhus",
    "Bogense": "Nordfyns",
    "Brønderslev-Dronninglund": "Brønderslev",
    "Vesthimmerland": "Vesthimmerlands",
}
IKKE_KOMMUNER = {"Christiansø", "Danmark"}


def _tal(s: str) -> float | None:
    s = s.strip().replace("%", "")
    if not s:
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def hent_aar(aar: int) -> dict[str, float] | None:
    """{kommune_kode: kg N/ha} for ét år, eller None hvis DCE ikke har tabellen."""
    req = urllib.request.Request(URL.format(aar=aar), headers={"User-Agent": "DoughnutDK/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            x = r.read().decode("latin-1", "ignore")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    ud: dict[str, float] = {}
    kolonne = None
    for raekke in re.findall(r"<tr[^>]*>(.*?)</tr>", x, re.S | re.I):
        celler = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                  for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", raekke, re.S | re.I)]
        if "Kommune" in celler:
            # Kolonnen hedder "Total deposition/areal" (enkelte år med ID-kolonne foran).
            kolonne = next(i for i, c in enumerate(celler) if "areal" in c.lower() and "deposition" in c.lower())
            navn_kol = celler.index("Kommune")
            continue
        if kolonne is None or len(celler) <= kolonne:
            continue
        navn = NAVNE.get(celler[navn_kol], celler[navn_kol])
        if not navn or navn in IKKE_KOMMUNER:
            continue
        v = _tal(celler[kolonne])
        if v is None:
            continue
        kode = kode_for_navn(navn)
        if kode is None:                    # ukendt navn: stop frem for et tavst hul (R5)
            raise SystemExit(f"FEJL: ukendt kommunenavn {navn!r} i DCE-tabellen for {aar}")
        ud[kode] = v
    if kolonne is None:
        raise SystemExit(f"FEJL: fandt ingen kolonne 'Total deposition/areal' i DCE-tabellen for {aar}")
    return ud


def _enkeltaar(fra: int, til: int) -> dict[tuple[str, str], float]:
    serie: dict[tuple[str, str], float] = {}
    for aar in range(fra, til + 1):
        d = hent_aar(aar)
        if d is None:
            continue
        for kode, v in d.items():
            serie[(kode, str(aar))] = v
    return serie


def seneste_dce_aar(start: int = 2024) -> int:
    """Nyeste år DCE har offentliggjort (prøver fremad fra `start`)."""
    aar = start
    while hent_aar(aar + 1) is not None:
        aar += 1
    while hent_aar(aar) is None:
        aar -= 1
    return aar


def serie_n_deposition(perioder: list[str]) -> dict[tuple[str, str], float]:
    """Treårsgennemsnit af kvælstofnedfaldet (kg N/ha) for hvert år i perioder,
    {(kommune_kode, år): værdi}. Intet landstal: indikatoren måles mod en fast
    tålegrænse. Bruges af både scoren og retningspilen (SAMME_SOM_SCOREN)."""
    aar = sorted(int(p) for p in perioder)
    enkelt = _enkeltaar(max(FOERSTE_AAR, aar[0] - (AAR_I_SNIT - 1)), aar[-1])
    ud = {k: v for k, v in rullende(enkelt, AAR_I_SNIT, "gennemsnit", 2).items()
          if int(k[1]) in aar}
    return ud


def trend_perioder(fra_aar: int) -> list[str]:
    """Årene retningspilen kan bruge: fra det første år med et helt treårsvindue
    i DCE's sammenhængende række til det nyeste offentliggjorte år."""
    return [str(a) for a in range(max(fra_aar, FOERSTE_AAR + AAR_I_SNIT - 1), seneste_dce_aar() + 1)]


def main() -> int:
    print("=" * 66)
    print("Kvælstofnedfald fra luften pr. kommune - DCE DEHM")
    print("=" * 66)
    sidste = seneste_dce_aar()
    serie = serie_n_deposition([str(sidste)])
    vaerdier = {k: v for (k, a), v in serie.items() if a == str(sidste)}
    mangler = sorted(set(KOMMUNER) - set(vaerdier))
    if mangler:
        print(f"  ADVARSEL: ingen værdi for {[KOMMUNER[k] for k in mangler]}")
    print(f"  {sidste - AAR_I_SNIT + 1}-{sidste}: {len(vaerdier)}/98 kommuner, "
          f"median {statistics.median(vaerdier.values()):.1f} kg N/ha, "
          f"spænd {min(vaerdier.values()):.1f}-{max(vaerdier.values()):.1f}")
    over = sum(1 for v in vaerdier.values() if v > TAALEGRAENSE)
    print(f"  Over tålegrænsen på {TAALEGRAENSE:g} kg N/ha: {over} kommuner")

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["kommune_kode", "kommune_navn", "n_deposition_kg_ha", "n_deposition_ratio"])
        for kode in sorted(KOMMUNER, key=int):
            v = vaerdier.get(kode)
            w.writerow([kode, KOMMUNER[kode], "" if v is None else v,
                        "" if v is None else round(v / TAALEGRAENSE * 100, 2)])
    print(f"✓ {OUTPUT.relative_to(ROOT)}")

    from dst_aar import registrer_aar
    registrer_aar(TABEL, str(sidste))
    t = vaerdier.get("787")
    print(f"  Thisted: {t} kg N/ha")
    return 0


if __name__ == "__main__":
    rc = main()
    # ───────────────────────────────────────────────────────────
    # AUTO-REBUILD af master_indicators.csv
    # ───────────────────────────────────────────────────────────
    try:
        from build_master_csv import auto_build_master
        auto_build_master()
    except Exception as _e:
        print(f"\n⚠ Kunne ikke auto-rebuild master-CSV: {_e}")
        print("  Rådata er gemt. Kør manuelt: python3 scripts/build_master_csv.py")
    sys.exit(rc)
