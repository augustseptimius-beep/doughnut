"""
indikatorregister.py - læser data/indikatorer.json, platformens ene liste
over indikatorer, sociale kategorier og økologiske dimensioner.

Før registret stod samme oplysning op til seks steder (build_master_csv.py,
build_trends_csv.py's OP_ER_GODT/IKKE_SCORET/AVERAGE_DIMENSIONS, shared.ts,
data.ts's ECO_RAW_KEY_MAP og metodesiden) og blev holdt i sync i hånden. Nu
udleder Python-scripterne deres lister herfra, og webappen importerer samme
JSON-fil (webapp/lib/shared.ts).

Registret læses først når en funktion kaldes, ikke ved import. Et fetch-script
importerer auto_build_master, og en fejl i registret må ikke vælte selve
hentningen - samme princip som api_noegler.py (CLAUDE.md pkt. 8).

Brug:
    import indikatorregister as ir
    for ind in ir.sociale(): ...
"""

from __future__ import annotations

import json
from pathlib import Path

REGISTER = Path(__file__).resolve().parent.parent / "data" / "indikatorer.json"

KATEGORIER = ("social", "ecological", "context")
AGGREGERINGER = ("worst-of", "gennemsnit")

# Felter hver indikatortype skal have. Resten er valgfrie.
_KRAEVEDE = {
    "social": ("id", "category", "dimension", "name", "table", "source", "source_url",
               "unit", "data_year", "csv", "raw_col", "reference", "inverse", "baseline_level"),
    "ecological": ("id", "category", "dimension", "name", "source", "unit", "data_year",
                   "csv", "raw_col", "reference", "lower_is_better", "baseline_type", "boundary",
                   "raw_key", "ratio_key"),
    "context": ("id", "category", "dimension", "source", "unit", "data_year", "csv", "raw_col"),
}


class RegisterFejl(ValueError):
    """Registret er ugyldigt. Beskeden lister alle fejl på én gang."""


_cache: dict | None = None


def valider(reg: dict) -> list[str]:
    """Returnerer en liste af fejl (tom hvis registret er gyldigt)."""
    fejl: list[str] = []
    indikatorer = reg.get("indikatorer", [])
    set_ids: set[str] = set()
    for ind in indikatorer:
        iid = ind.get("id", "?")
        if iid in set_ids:
            fejl.append(f"{iid}: id findes to gange")
        set_ids.add(iid)
        kat = ind.get("category")
        if kat not in KATEGORIER:
            fejl.append(f"{iid}: ukendt category {kat!r}")
            continue
        for felt in _KRAEVEDE[kat]:
            if felt not in ind:
                fejl.append(f"{iid}: mangler feltet {felt!r}")
        # Et socialt loft kan kun sænke R1's 150 (kystrisiko: 100).
        if kat == "social" and "cap" in ind and not (
                isinstance(ind["cap"], (int, float)) and 0 < ind["cap"] <= 150):
            fejl.append(f"{iid}: cap for en social indikator skal være et tal over 0 og højst 150")
        # Felter der skrives til master_indicators.csv. Webappen parser den med
        # split(","), så et komma forskyder kolonnerne og rækken forsvinder
        # tavst (sep. 2026: income_gender_gap manglede i alle 98 kommuner).
        for felt in ("id", "unit", "source", "data_year", "dimension"):
            if "," in str(ind.get(felt, "")):
                fejl.append(f"{iid}: feltet {felt!r} indeholder komma ({ind.get(felt)!r})")

    for ind in indikatorer:
        ref = ind.get("reference")
        if ref is None:
            continue
        iid, typ = ind.get("id"), ref.get("type")
        if typ == "maal":
            if not isinstance(ref.get("value"), (int, float)):
                fejl.append(f"{iid}: reference type maal kræver et tal i 'value'")
        elif typ == "landstal":
            if not ref.get("col"):
                fejl.append(f"{iid}: reference type landstal kræver 'col'")
            if not ind.get("ratio_col"):
                fejl.append(f"{iid}: reference type landstal kræver ratio_col (til rekonstruktion)")
        elif typ != "kommunegennemsnit":
            fejl.append(f"{iid}: ukendt reference-type {typ!r}")
        if ind.get("formula") not in (None, "100_minus_raw", "komplement"):
            fejl.append(f"{iid}: ukendt formula {ind.get('formula')!r}")
        if ind.get("formula") == "komplement" and not (
                ind.get("category") == "ecological" and ind.get("lower_is_better") is False):
            fejl.append(f"{iid}: formula 'komplement' gælder kun økologiske andele hvor "
                        f"højere er bedre (lower_is_better: false)")

    by_id = {i.get("id"): i for i in indikatorer}
    kat_ids = [k["id"] for k in reg.get("sociale_kategorier", [])]
    dim_ids = [d["id"] for d in reg.get("oekologiske_dimensioner", [])]
    for navn, ids in (("sociale_kategorier", kat_ids), ("oekologiske_dimensioner", dim_ids)):
        if len(ids) != len(set(ids)):
            fejl.append(f"{navn}: et id findes to gange")

    brugt: dict[str, str] = {}
    for kat in reg.get("sociale_kategorier", []):
        for iid in kat.get("indicators", []):
            ind = by_id.get(iid)
            if ind is None:
                fejl.append(f"kategori {kat['id']}: ukendt indikator {iid}")
            elif ind.get("category") != "social":
                fejl.append(f"kategori {kat['id']}: {iid} er ikke en social indikator")
            elif ind.get("dimension") != kat["id"]:
                fejl.append(f"kategori {kat['id']}: {iid} har dimension={ind.get('dimension')!r}")
            if iid in brugt:
                fejl.append(f"{iid}: står i både {brugt[iid]} og {kat['id']}")
            brugt[iid] = kat["id"]
    for dim in reg.get("oekologiske_dimensioner", []):
        if dim.get("aggregation") not in AGGREGERINGER:
            fejl.append(f"dimension {dim['id']}: ukendt aggregation {dim.get('aggregation')!r}")
        for iid in dim.get("indicators", []):
            ind = by_id.get(iid)
            if ind is None:
                fejl.append(f"dimension {dim['id']}: ukendt indikator {iid}")
            elif ind.get("category") != "ecological":
                fejl.append(f"dimension {dim['id']}: {iid} er ikke en økologisk indikator")
            elif ind.get("dimension") != dim["id"]:
                fejl.append(f"dimension {dim['id']}: {iid} har dimension={ind.get('dimension')!r}")
            if iid in brugt:
                fejl.append(f"{iid}: står i både {brugt[iid]} og {dim['id']}")
            brugt[iid] = dim["id"]

    for ind in indikatorer:
        kat, iid, dim = ind.get("category"), ind.get("id"), ind.get("dimension")
        if kat == "social" and dim not in kat_ids:
            fejl.append(f"{iid}: dimension {dim!r} er ikke en social kategori")
        if kat == "ecological" and iid not in brugt:
            fejl.append(f"{iid}: økologisk indikator der ikke står i sin dimensions liste")
        if kat == "context" and dim not in kat_ids and dim not in dim_ids:
            fejl.append(f"{iid}: dimension {dim!r} findes ikke")
    return fejl


def register() -> dict:
    """Hele registret, valideret. Rejser RegisterFejl hvis det er ugyldigt."""
    global _cache
    if _cache is None:
        with open(REGISTER, encoding="utf-8") as f:
            reg = json.load(f)
        fejl = valider(reg)
        if fejl:
            raise RegisterFejl(f"{REGISTER.name} er ugyldigt:\n  " + "\n  ".join(fejl))
        _cache = reg
    return _cache


def _af_type(kategori: str) -> list[dict]:
    return [i for i in register()["indikatorer"] if i["category"] == kategori]


def sociale() -> list[dict]:
    """Sociale indikatorer i master-rækkefølge, inkl. dem der ikke scores."""
    return _af_type("social")


def oekologiske() -> list[dict]:
    return _af_type("ecological")


def kontekst() -> list[dict]:
    return _af_type("context")


def sociale_kategorier() -> list[dict]:
    return register()["sociale_kategorier"]


def oekologiske_dimensioner() -> list[dict]:
    return register()["oekologiske_dimensioner"]


def scorede_sociale() -> set[str]:
    """Id'er på sociale indikatorer der står i en kategori og dermed scores."""
    return {i for k in sociale_kategorier() for i in k["indicators"]}


def ikke_scoret() -> set[str]:
    """Sociale indikatorer der står i master, men ikke scores (CLAUDE.md pkt. 18)."""
    return {i["id"] for i in sociale()} - scorede_sociale()


def gennemsnits_dimensioner() -> set[str]:
    """Økologiske dimensioner der scores som gennemsnit i stedet for worst-of."""
    return {d["id"] for d in oekologiske_dimensioner() if d["aggregation"] == "gennemsnit"}


def op_er_godt() -> dict[str, bool]:
    """Om en stigende råværdi er fremgang. Udledt af 'inverse' (sociale) og
    'lower_is_better' (økologiske); kontekst-indikatorer har ingen retning."""
    ud = {i["id"]: not i["inverse"] for i in sociale()}
    ud.update({i["id"]: not i["lower_is_better"] for i in oekologiske()})
    return ud


if __name__ == "__main__":
    reg = register()
    print(f"✓ {REGISTER.name}: {len(sociale())} sociale ({len(scorede_sociale())} scoret), "
          f"{len(oekologiske())} økologiske, {len(kontekst())} kontekst, "
          f"{len(sociale_kategorier())} kategorier, {len(oekologiske_dimensioner())} dimensioner")
