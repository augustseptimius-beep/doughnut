"""
Henter deltagelse i lokale sportsbegivenheder fra DST's kulturvaneundersøgelse
(KV2GEO) som indikator under Fællesskab.

KØR FRA PROJEKTETS RODMAPPE:
    python3 scripts/fetch_kulturvaner.py

Hvorfor netop "overværet sportsbegivenhed som tilskuer"
------------------------------------------------------
KV2GEO har 17 kulturaktiviteter. De blev alle testet mod Fællesskabs øvrige
indikatorer, og de fleste måler en by- og uddannelsesgradient vi allerede har:
biblioteksbesøg, museum og billedkunst korrelerer 0,34-0,41 med kommunens
udgifter til frivillige foreninger. Tilskuer-indikatoren er den eneste der
korrelerer positivt med idrætsmedlemskab (0,25) og nul med udgiftsmålene
(-0,04), altså den eneste der tilføjer noget nyt om det lokale fællesskab.
Medieforbrug (film, musik, sociale medier) ligger på 90-99 procent overalt og
skelner ikke mellem kommuner.

VIGTIGT - dækningen er ufuldstændig OG systematisk skæv
-------------------------------------------------------
Undersøgelsen er en stikprøve, og DST undertrykker tal for kommuner med for få
svar. Kun 78 kommuner har tal for et enkelt år. Toårigt gennemsnit af 2024 og
2025 løfter det til 81 og dæmper samtidig støjen (spredning 5,3 mod 6,3, og
laveste værdi går fra 22 til 29 procent, så en del af yderpunkterne var
stikprøvestøj).

De 17 kommuner uden tal er IKKE tilfældigt fordelt: deres median er ca. 24.500
indbyggere mod ca. 55.000 for dem med tal. Læsø, Fanø, Samsø, Ærø og Langeland
er blandt dem. Konsekvensen er at små kommuner får Fællesskab beregnet på fire
indikatorer hvor større kommuner bruger fem, og at netop de kommuner hvor et
lokalt idrætsfællesskab kunne fylde mest, ikke kan måles på det. Det skal stå
på metodesiden, og det er en bevidst afvejning: hellere et rigtigt tal for 81
kommuner end intet deltagelsesmål overhovedet.
"""
from __future__ import annotations

import csv
import json
import sys
import urllib.request
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
API = "https://api.statbank.dk/v1/data"

TABEL = "KV2GEO"
AKTIVITET = "20700"      # Har overværet sportsbegivenhed som tilskuer
AAR = ["2024", "2025"]   # toårigt gennemsnit, se modulets docstring


def api_post(body: dict) -> dict:
    req = urllib.request.Request(API, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def gyldige_kommunekoder() -> set[str]:
    """
    De 98 kommunekoder, læst fra master-CSV'en.

    FÆLDE: KV2GEO's områdeliste blander kommuner, landsdele og regioner, og
    REGIONERNE har også trecifrede koder (081-085 for Nordjylland, Midtjylland,
    Syddanmark, Hovedstaden og Sjælland). Et filter på "tre cifre og ikke 000"
    tager dem derfor med og overvurderer dækningen med fem. Slå altid op i den
    rigtige kommuneliste.
    """
    with open(DATA / "master_indicators.csv", encoding="utf-8") as f:
        return {row["kommune_kode"] for row in csv.DictReader(f)}


def hent() -> tuple[dict[str, float], float, list[str]]:
    """Returnerer ({kommune_kode: andel_pct}, landsgennemsnit, brugte_aar)."""
    print(f"Henter kulturvaner ({TABEL}, aktivitet {AKTIVITET}, {AAR[0]}-{AAR[-1]})...")
    d = api_post({
        "table": TABEL, "format": "JSONSTAT", "lang": "da",
        "variables": [
            {"code": "KULTUR", "values": [AKTIVITET]},
            {"code": "KOMMUNEDK", "values": ["*"]},
            {"code": "Tid", "values": AAR},
        ],
    })["dataset"]

    kom = d["dimension"]["KOMMUNEDK"]["category"]["index"]
    tid = d["dimension"]["Tid"]["category"]["index"]
    n_tid = len(tid)
    vals = d["value"]

    def serie(kode: str) -> list[float]:
        i = kom.get(kode)
        if i is None:
            return []
        return [vals[i * n_tid + t] for t in tid.values() if vals[i * n_tid + t] is not None]

    gyldige = gyldige_kommunekoder()
    pr_kommune: dict[str, float] = {}
    for kode in kom:
        if kode not in gyldige:
            continue
        s = serie(kode)
        if s:
            pr_kommune[kode] = round(mean(s), 2)

    nat = serie("000")
    if not nat:
        raise RuntimeError("Fandt ikke landstal (kode 000) i KV2GEO")
    landsgennemsnit = mean(nat)
    print(f"  {len(pr_kommune)} kommuner med tal, landsgennemsnit {landsgennemsnit:.1f}%")
    return pr_kommune, landsgennemsnit, list(tid)


def ratio_direct(kommune_val: float, national_avg: float) -> float:
    """Direkte ratio: højere andel er bedre."""
    if national_avg == 0:
        return 0
    return round(min((kommune_val / national_avg) * 100, 150.0), 2)


def main() -> None:
    pr_kommune, nat, aar = hent()

    # Hvilke kommuner mangler, og hvor store er de? Skrives til konsollen, så
    # skævheden er synlig ved hver kørsel og ikke kun i dokumentationen.
    mangler = sorted(gyldige_kommunekoder() - set(pr_kommune))
    if mangler:
        print(f"  ⚠ {len(mangler)} kommuner uden tal (for lille stikprøve hos DST):")
        print(f"    {', '.join(mangler)}")

    ud = DATA / "kulturvaner_scores.csv"
    with open(ud, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["kommune_kode", "sport_tilskuer_pct", "sport_tilskuer_ratio"])
        for kode in sorted(pr_kommune, key=int):
            pct = pr_kommune[kode]
            w.writerow([kode, pct, ratio_direct(pct, nat)])
    print(f"✓ Skrev {ud.relative_to(ROOT)} ({len(pr_kommune)} kommuner, {aar[0]}-{aar[-1]})")

    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from build_master_csv import auto_build_master
        auto_build_master()
    except Exception as e:
        print(f"\n⚠ Kunne ikke auto-rebuild master-CSV: {e}")
        print("  Rådata er gemt. Kør manuelt: python3 scripts/build_master_csv.py")


if __name__ == "__main__":
    main()
