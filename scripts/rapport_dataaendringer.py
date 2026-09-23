#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rapport_dataaendringer.py - hvad har en ny master_indicators.csv ændret?

Sammenligner data/master_indicators.csv med den committede version (git
HEAD) eller en anden fil, og viser hvad der er sket med tallene. Formålet er
at fange den slags fejl der ellers først opdages af en læser: Vejens
kvinder "fordoblede" deres gennemsnitsindkomst fra ét år til det næste, og
det stod i master i månedsvis, fordi ingen sammenlignede.

Rapporten viser:
  1. Rækker der er kommet til eller forsvundet.
  2. Ratios der har flyttet sig, pr. indikator, og de største enkeltspring.
  3. Råværdier der har flyttet sig mere end 25% for en kommune (spring der
     ofte betyder en ændret kilde eller definition, ikke en reel udvikling).
  4. Kategorier og dimensioner der skifter farve (rød/gul/grøn) med
     landsgennemsnittet som baseline.
  5. Ændrede dataår.

Ren diagnose: skriver ingen filer, fejler aldrig kørslen (exit 0).

Brug:
  python3 scripts/rapport_dataaendringer.py            # mod git HEAD
  python3 scripts/rapport_dataaendringer.py --mod FIL  # mod en anden master-fil

Kaldes også af build_master_csv.py efter hvert build (kort udgave).
"""

from __future__ import annotations

import argparse
import csv
import io
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "data" / "master_indicators.csv"
sys.path.insert(0, str(Path(__file__).resolve().parent))

RAA_SPRING = 0.25     # relativ ændring i råværdi der rapporteres pr. kommune
RATIO_SPRING = 5.0    # ratio-point der rapporteres som enkeltspring


def _f(x):
    try:
        return float(x) if x not in ("", None) else None
    except ValueError:
        return None


def _laes(tekst: str) -> dict:
    return {(r["kommune_kode"], r["indicator_id"]): r for r in csv.DictReader(io.StringIO(tekst))}


def _gammel_master(mod: str | None) -> tuple[str | None, str]:
    if mod:
        p = Path(mod)
        return (p.read_text(encoding="utf-8") if p.exists() else None), str(p)
    try:
        ud = subprocess.run(["git", "show", "HEAD:data/master_indicators.csv"], cwd=ROOT,
                            capture_output=True, text=True, check=True)
        return ud.stdout, "git HEAD"
    except Exception:
        return None, "git HEAD"


def _farve_social(x):
    return None if x is None else ("grøn" if x >= 100 else "gul" if x >= 85 else "rød")


def _farve_eco(x):
    return None if x is None else ("grøn" if x <= 85 else "gul" if x <= 100 else "rød")


def _kategoriscorer(rows: dict) -> dict:
    """{(kode, kategori): score} som simpelt gennemsnit af de scorede ratios."""
    import indikatorregister as ir
    ud = {}
    kommuner = {k for k, _ in rows}
    for kat in ir.sociale_kategorier():
        for kode in kommuner:
            vals = [_f(rows[(kode, i)]["ratio"]) for i in kat["indicators"] if (kode, i) in rows]
            vals = [v for v in vals if v is not None]
            ud[(kode, kat["id"])] = sum(vals) / len(vals) if vals else None
    return ud


def rapport(ny: dict, gl: dict, kort: bool = False) -> list[str]:
    linjer: list[str] = []
    navn = {k: r["kommune_navn"] for (k, _), r in ny.items()}
    navn.update({k: r["kommune_navn"] for (k, _), r in gl.items() if k not in navn})

    # 1. Tilføjede og fjernede rækker
    kun_ny = sorted(set(ny) - set(gl))
    kun_gl = sorted(set(gl) - set(ny))
    if kun_ny or kun_gl:
        linjer.append(f"Rækker: {len(kun_ny)} nye, {len(kun_gl)} fjernede")
        for titel, keys in (("  ny", kun_ny), ("  fjernet", kun_gl)):
            pr_ind = defaultdict(list)
            for k, i in keys:
                pr_ind[i].append(navn.get(k, k))
            for i, n in sorted(pr_ind.items()):
                linjer.append(f"{titel}: {i} ({len(n)}): {', '.join(n[:8])}{' ...' if len(n) > 8 else ''}")

    faelles = sorted(set(ny) & set(gl))

    # 2. Ratios
    pr_ind = defaultdict(list)
    for key in faelles:
        a, b = _f(gl[key]["ratio"]), _f(ny[key]["ratio"])
        if a != b:
            pr_ind[key[1]].append((key[0], a, b))
    if pr_ind:
        linjer.append(f"Ratios ændret i {sum(len(v) for v in pr_ind.values())} rækker, {len(pr_ind)} indikatorer:")
        for i, lst in sorted(pr_ind.items(), key=lambda kv: -max(abs((b or 0) - (a or 0)) for _, a, b in kv[1])):
            maks = max(abs((b or 0) - (a or 0)) for _, a, b in lst)
            linjer.append(f"  {i:26} {len(lst):3} kommuner, største ændring {maks:.2f}")
        spring = [(abs((b or 0) - (a or 0)), k, i, a, b) for i, lst in pr_ind.items() for k, a, b in lst
                  if a is None or b is None or abs(b - a) >= RATIO_SPRING]
        if spring and not kort:
            linjer.append(f"  Enkeltspring på mindst {RATIO_SPRING:g} point eller til/fra ingen værdi:")
            for _, k, i, a, b in sorted(spring, reverse=True)[:25]:
                linjer.append(f"    {navn.get(k, k):18} {i:24} {a} -> {b}")

    # 3. Råværdier
    raa = []
    for key in faelles:
        a, b = _f(gl[key]["raw_value"]), _f(ny[key]["raw_value"])
        if a and b is not None and abs(b - a) / abs(a) >= RAA_SPRING:
            raa.append((abs(b - a) / abs(a), key, a, b))
    if raa:
        linjer.append(f"Råværdier med spring på mindst {RAA_SPRING:.0%}: {len(raa)}")
        for rel, (k, i), a, b in sorted(raa, reverse=True)[: (5 if kort else 25)]:
            linjer.append(f"  {navn.get(k, k):18} {i:24} {a} -> {b} ({rel:+.0%})")

    # 4. Farveskift (landsgennemsnit som baseline)
    try:
        ks_ny, ks_gl = _kategoriscorer(ny), _kategoriscorer(gl)
        skift = []
        for key in sorted(set(ks_ny) & set(ks_gl)):
            fa, fb = _farve_social(ks_gl[key]), _farve_social(ks_ny[key])
            if fa != fb:
                skift.append(f"  {navn.get(key[0], key[0]):18} {key[1]:24} {fa} -> {fb} "
                             f"({ks_gl[key] and round(ks_gl[key], 2)} -> {ks_ny[key] and round(ks_ny[key], 2)})")
        for key in faelles:
            if key[1].startswith("_dim_"):
                a, b = _f(gl[key]["ratio"]), _f(ny[key]["ratio"])
                if _farve_eco(a) != _farve_eco(b):
                    skift.append(f"  {navn.get(key[0], key[0]):18} {key[1]:24} {_farve_eco(a)} -> {_farve_eco(b)} ({a} -> {b})")
        for key in set(ny) ^ set(gl):
            if key[1].startswith("_dim_"):
                skift.append(f"  {navn.get(key[0], key[0]):18} {key[1]:24} dimensionsscore {'ny' if key in ny else 'forsvundet'}")
        linjer.append(f"Farveskift på kategori/dimension (landsgns.-baseline): {len(skift)}")
        linjer.extend(skift[: (10 if kort else 100)])
    except Exception as e:  # registret kan være ugyldigt - rapporten må ikke vælte
        linjer.append(f"Farveskift: kunne ikke beregnes ({type(e).__name__}: {e})")

    # 5. Dataår
    aar = {}
    for key in faelles:
        if gl[key].get("data_year") != ny[key].get("data_year"):
            aar[key[1]] = (gl[key].get("data_year"), ny[key].get("data_year"))
    if aar:
        linjer.append("Dataår ændret: " + ", ".join(f"{i} {a}->{b}" for i, (a, b) in sorted(aar.items())))

    if not linjer:
        linjer.append("Ingen ændringer i tallene.")
    return linjer


def main(argv=None, kort: bool = False) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--mod", help="master-fil der sammenlignes med (standard: git HEAD)")
    args = ap.parse_args(argv)
    gl_tekst, kilde = _gammel_master(args.mod)
    if gl_tekst is None:
        print(f"Dataændringer: ingen sammenligning ({kilde} findes ikke)")
        return 0
    ny = _laes(MASTER.read_text(encoding="utf-8"))
    gl = _laes(gl_tekst)
    print(f"Dataændringer i master_indicators.csv mod {kilde}:")
    for linje in rapport(ny, gl, kort=kort):
        print(f"  {linje}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
