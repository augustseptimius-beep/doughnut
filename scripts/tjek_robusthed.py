#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tjek_robusthed.py - sundhedstjek af hele datapipelinen. REN DIAGNOSE.

Henter kun metadata og skriver ingen datafiler. Kør den før en dataopdatering,
eller når noget ser mistænkeligt ud på platformen.

Fem kontroller, hver møntet på en fejl vi FAKTISK er faldet i (aug. 2026):

  1. KØRBARHED      Kan scriptet overhovedet importeres på maskinens Python?
                    Fem scripts brugte 'float | None' uden
                    'from __future__ import annotations' og fejlede på 3.9 -
                    derfor stod fx voter_turnout på kommunalvalget 2021.

  2. VARIABELNAVNE  Findes de variabler scriptet beder DST om stadig?
                    LABY49's OFFENTRANSPORT blev omdøbt til SDGSERVICE.
                    API'et svarede 400, og scriptet faldt TAVST tilbage på
                    hårdkodede tal - indikatoren så levende ud, men var frosset.

  3. DØDE TABELLER  Har DST markeret tabellen inaktiv? HFUDD10 stoppede i 2019,
                    men education viste den som "2023" i årevis. BIB1 er
                    ligeledes død (afløst af BIB3A).

  4. HÅRDKODEDE ÅR  Beder scriptet om et fast årstal? Så står indikatoren
                    stille uanset hvor mange gange den køres. Brug dst_aar.

  5. ÅRSTALS-SANDHED Svarer master_indicators.csv's data_year til det år
                    tabellen FAKTISK blev hentet på (data/data_years.json)?

Brug:
  python3 scripts/tjek_robusthed.py
"""

from __future__ import annotations

import ast
import csv
import json
import re

import ssl
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
DATA = ROOT / "data"
ctx = ssl.create_default_context()

FUND: list[tuple[str, str, str]] = []   # (alvor, emne, besked)
ALVOR = {"KRITISK": 0, "ADVARSEL": 1, "INFO": 2}


def fund(alvor: str, emne: str, besked: str) -> None:
    FUND.append((alvor, emne, besked))


# ══════════════════════════════════════════════════════════════════════
# 1. KØRBARHED
# ══════════════════════════════════════════════════════════════════════
def _har_future_annotations(træ: ast.Module) -> bool:
    for node in træ.body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            if any(a.name == "annotations" for a in node.names):
                return True
    return False


def _pipe_none_annotationer(træ: ast.Module) -> list[int]:
    """Linjenumre med 'X | None'-annotationer (PEP 604), som kræver 3.10+."""
    linjer = []

    def er_pipe(node) -> bool:
        return isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr)

    for node in ast.walk(træ):
        anns = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            anns = [a.annotation for a in node.args.args if a.annotation]
            anns += [a.annotation for a in node.args.kwonlyargs if a.annotation]
            if node.returns:
                anns.append(node.returns)
        elif isinstance(node, ast.AnnAssign) and node.annotation:
            anns = [node.annotation]
        for a in anns:
            if any(er_pipe(x) for x in ast.walk(a)):
                linjer.append(a.lineno)
    return sorted(set(linjer))


def tjek_koerbarhed() -> None:
    """
    Statisk kontrol - scripterne bliver IKKE eksekveret.

    (Et tidligere forsøg brugte runpy for at se om de kunne importeres. Flere
    scripts har al deres logik på modulniveau uden if __name__-værn, så det
    ville hente og overskrive datafiler midt i en "ren diagnose".)
    """
    py = (sys.version_info.major, sys.version_info.minor)
    print(f"1/5 Kørbarhed (statisk, Python {py[0]}.{py[1]})...", file=sys.stderr)
    for f in sorted(SCRIPTS.glob("*.py")):
        if f.name == "tjek_robusthed.py":
            continue
        kilde = f.read_text(encoding="utf-8")
        try:
            træ = ast.parse(kilde)
        except SyntaxError as e:
            fund("KRITISK", f.name, f"syntaksfejl linje {e.lineno}: {e.msg}")
            continue
        if py < (3, 10) and not _har_future_annotations(træ):
            linjer = _pipe_none_annotationer(træ)
            if linjer:
                vis = ", ".join(str(x) for x in linjer[:5])
                fund("KRITISK", f.name,
                     f"bruger 'X | None' i annotationer (linje {vis}) uden "
                     f"'from __future__ import annotations'. Fejler ved import "
                     f"på Python {py[0]}.{py[1]}.")


# ══════════════════════════════════════════════════════════════════════
# Hjælp: hvilke DST-tabeller og variabler bruger hvert script?
# ══════════════════════════════════════════════════════════════════════
def kald_i_scripts() -> dict[str, dict]:
    """{tabel: {"scripts": {navn}, "variabler": {kode}, "faste_aar": [(script, aar)]}}"""
    ud: dict[str, dict] = defaultdict(
        lambda: {"scripts": set(), "variabler": set(), "faste_aar": [],
                 "dynamisk": False})
    for f in sorted(SCRIPTS.glob("fetch_*.py")):
        s = f.read_text(encoding="utf-8")
        for m in re.finditer(
                r'(?:api_post|dst_post|hent_tabel)\(\s*"(\w+)"\s*,\s*\[(.*?)\]\s*\)',
                s, re.S):
            tabel, blok = m.group(1), m.group(2)
            ud[tabel]["scripts"].add(f.name)
            for km in re.finditer(r'\{"code":\s*"([^"]+)"', blok):
                kode = km.group(1)
                if kode.lower() != "tid":
                    ud[tabel]["variabler"].add(kode)
            for tm in re.finditer(
                    r'\{"code":\s*"Tid",\s*"values":\s*\[\s*"(\d{4}[^"]*)"', blok):
                ud[tabel]["faste_aar"].append((f.name, tm.group(1)))
            # Bruger scriptet et dynamisk opslag for SAMME tabel? Så er de
            # hårdkodede år fallback-grene ("prøv ældre år hvis nyeste er tom"),
            # ikke den primære kilde til forældelse.
            if re.search(r'seneste_(?:aar|periode|kvartal|aar_liste)\(\s*"' + tabel + r'"',
                         s) or re.search(r'hele_aar_kvartaler\(\s*"' + tabel + r'"', s):
                ud[tabel]["dynamisk"] = True
        # "table": "XXX"-stilen (fetch_doughnut_data.py)
        for m in re.finditer(r'"table":\s*"(\w+)"', s):
            ud[m.group(1)]["scripts"].add(f.name)
    return ud


def tabelinfo(tabel: str):
    u = f"https://api.statbank.dk/v1/tableinfo/{tabel}?lang=da&format=JSON"
    req = urllib.request.Request(u, headers={"User-Agent": "DoughnutDK/1.0"})
    with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
        return json.loads(r.read().decode("utf-8"))


# ══════════════════════════════════════════════════════════════════════
# 2-4. VARIABELNAVNE, DØDE TABELLER, HÅRDKODEDE ÅR
# ══════════════════════════════════════════════════════════════════════
def tjek_tabeller(brug: dict[str, dict]) -> dict[str, str]:
    print(f"2-4/5 Tjekker {len(brug)} DST-tabeller...", file=sys.stderr)
    nyeste: dict[str, str] = {}
    for tabel, info in sorted(brug.items()):
        scripts = ", ".join(sorted(info["scripts"]))
        try:
            d = tabelinfo(tabel)
        except urllib.error.HTTPError as e:
            fund("KRITISK", tabel, f"DST svarer {e.code} ({scripts}) - findes tabellen?")
            continue
        except Exception as e:
            fund("ADVARSEL", tabel, f"kunne ikke hentes: {type(e).__name__} ({scripts})")
            continue

        findes = {v["id"].upper() for v in d["variables"]}
        mangler = sorted(k for k in info["variabler"] if k.upper() not in findes)
        if mangler:
            fund("KRITISK", tabel,
                 f"scriptet beder om variabler der IKKE findes: {mangler}. "
                 f"Findes: {sorted(findes)} ({scripts})")

        if d.get("active") is False:
            fund("KRITISK", tabel,
                 f"DST har markeret tabellen INAKTIV - den opdateres aldrig igen. "
                 f"Find afløser ({scripts})")

        tid = next((v for v in d["variables"] if v.get("time")), None)
        if tid:
            aar = [m.group(0) for x in tid["values"]
                   if (m := re.match(r"\d{4}", str(x["id"])))]
            if aar:
                nyeste[tabel] = max(aar)

        for script, fast in info["faste_aar"]:
            n = nyeste.get(tabel)
            if not n:
                continue
            forældet = bool(re.match(r"\d{4}", fast)) and fast[:4] < n
            if info.get("dynamisk"):
                # Tabellen hentes dynamisk andetsteds i scriptet - det faste år
                # er en fallback-gren, ikke indikatorens primære årstal.
                if forældet:
                    fund("INFO", tabel,
                         f"{script}: fallback-gren med fast år {fast} "
                         f"(primær hentning er dynamisk, kilden har {n})")
            elif forældet:
                fund("ADVARSEL", tabel,
                     f"{script} beder om fast år {fast}, kilden har {n}. "
                     "Brug dst_aar.seneste_aar().")
            else:
                fund("INFO", tabel, f"{script} har hårdkodet år {fast} (kilden: {n})")
        time.sleep(0.2)
    return nyeste


# ══════════════════════════════════════════════════════════════════════
# 5. ÅRSTALS-SANDHED
# ══════════════════════════════════════════════════════════════════════
def tjek_aarstal(nyeste: dict[str, str]) -> None:
    print("5/5 Sammenholder master-årstal med registret...", file=sys.stderr)
    reg = {}
    p = DATA / "data_years.json"
    if p.exists():
        reg = json.loads(p.read_text(encoding="utf-8"))

    master = DATA / "master_indicators.csv"
    if not master.exists():
        fund("KRITISK", "master_indicators.csv", "findes ikke")
        return
    set_: dict[str, tuple[str, str]] = {}
    for r in csv.DictReader(master.open(encoding="utf-8")):
        if r["category"] == "context" or not r.get("data_year"):
            continue
        set_.setdefault(r["indicator_id"], (r["data_year"], r["source"]))

    for iid, (dy, src) in sorted(set_.items()):
        m = re.match(r"DST\s+([A-ZÆØÅ0-9_]+)", src or "")
        if not m:
            continue
        tabel = m.group(1)
        hentet = reg.get(tabel)
        if hentet and dy != hentet:
            fund("ADVARSEL", iid,
                 f"master siger {dy}, men {tabel} blev hentet på {hentet}")
        n = nyeste.get(tabel)
        if n and dy < n:
            fund("INFO", iid, f"{tabel} har nu {n}, platformen viser {dy}")


def main() -> int:
    tjek_koerbarhed()
    brug = kald_i_scripts()
    nyeste = tjek_tabeller(brug)
    tjek_aarstal(nyeste)

    FUND.sort(key=lambda f: (ALVOR.get(f[0], 9), f[1]))
    optal = defaultdict(int)
    for a, _, _ in FUND:
        optal[a] += 1

    print()
    print("=" * 100)
    print("ROBUSTHEDSTJEK AF DATAPIPELINEN")
    print("=" * 100)
    print("  " + "   ".join(f"{k}: {optal[k]}" for k in ("KRITISK", "ADVARSEL", "INFO")))
    print()
    for alvor, emne, besked in FUND:
        print(f"[{alvor:8}] {emne}")
        print(f"             {besked}")
    if not FUND:
        print("  Ingen fund. Pipelinen ser sund ud.")
    print()
    return 1 if optal["KRITISK"] else 0


if __name__ == "__main__":
    sys.exit(main())
