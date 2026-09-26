#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tjek_konsistens.py - krydstjek af indikatorregistret, dataen og metodesiden.

Hvorfor den findes
------------------
Indtil sep. 2026 stod samme oplysning (retning, dimension, tabel, antal
indikatorer) op til seks steder i Python og TypeScript og blev holdt i sync i
hånden. To gennemgange fandt gentagne gange at de var kommet ud af trit, og
ingen af fejlene gav en synlig krasch - de viste bare et forkert tal eller en
forkert pil.

Nu står indikatorerne ét sted, data/indikatorer.json, og både Python og
webappen læser derfra. Det fjerner selve sync-problemet, men tre ting kan
stadig skride, og dem tjekker dette script:

  1. Registret selv (dubletter, manglende felter, kategorier der peger forkert)
     og at master har præcis kommunerne i data/kommuner.json.
  2. Registret mod dataen: at master-CSV'en indeholder præcis registrets
     indikatorer, og at fortegnet i dataen passer med 'inverse' og
     'lower_is_better' (en fejl her vender en pil og en farve).
  3. Registret mod metodesidens fritekst: antal indikatorer, nævnte tabeller
     og worst-of/gennemsnit. Den tekst skrives stadig i hånden.
  4. Retningspilen mod scoren: tidsseriens værdi for scorens år skal være
     scorens råværdi, ellers beskriver pilen et andet tal end det der vises.

Ren diagnose, skriver ingen filer - ligesom tjek_robusthed.py.

Brug
----
  cd /sti/til/doughnut
  python3 scripts/tjek_konsistens.py

Exit-kode 1 hvis der er fejl, 0 hvis ikke. Kaldes automatisk af
build_master_csv.py (se _tjek_konsistens_efter_build() dér).

Begrænsning
-----------
Metodesiden parses med regex, ikke en rigtig TypeScript-parser. Det er
skrøbeligt over for større omskrivninger af den fil, men en regex der fanger
den faktiske struktur er bedre end ingen kontrol.
"""

from __future__ import annotations

import csv
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import indikatorregister as ir  # noqa: E402


@dataclass
class Fund:
    niveau: str  # "fejl" eller "info"
    tekst: str


def _f(fund: list[Fund], tekst: str) -> None:
    fund.append(Fund("fejl", tekst))


def _info(fund: list[Fund], tekst: str) -> None:
    fund.append(Fund("info", tekst))


def _korrelation(xs, ys) -> float:
    """Pearson-korrelation. statistics.correlation findes først fra Python
    3.10, og CLAUDE.md pkt. 19 dokumenterer at maskinen kører 3.9."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return 0.0
    return sxy / math.sqrt(sxx * syy)


def _parse_float(s: str) -> float | None:
    try:
        return float(s) if s not in ("", None) else None
    except ValueError:
        return None


TAL_ORD = {"en": 1, "et": 1, "enkelt": 1, "to": 2, "tre": 3, "fire": 4, "fem": 5,
           "seks": 6, "syv": 7, "otte": 8, "ni": 9, "ti": 10}


def _metode_scoring(metode_tsx: str, blok_navn: str) -> dict[str, str]:
    """{id: scoring-tekst} fra SOCIAL_METHODS eller ECO_METHODS."""
    start = metode_tsx.index(f"const {blok_navn}")
    slut = metode_tsx.index("\n};", start)
    blok = metode_tsx[start:slut]
    return {m.group(1): m.group(2)
            for m in re.finditer(r'id: "(\w+)",\s*scoring: "((?:[^"\\]|\\.)*)"', blok)}


def _antal_i_tekst(tekst: str) -> int | None:
    """Antal indikatorer som teksten selv angiver ('Gennemsnit af ni indikatorer',
    'Worst-of af to', 'Enkelt indikator', '1 indikator'). None hvis intet."""
    m = re.search(r"(?:af (?:op til )?|^)(\w+) (?:indikator|sub-indikator)", tekst, re.I) \
        or re.search(r"(?:Worst-of|Gennemsnit) af (\w+)", tekst, re.I) \
        or re.search(r"^(\w+) sub-indikatorer", tekst, re.I)
    if not m:
        return None
    ord_ = m.group(1).lower()
    return int(ord_) if ord_.isdigit() else TAL_ORD.get(ord_)


def _tjek_metodeside(fund: list[Fund], metode_tsx: str) -> None:
    by_id = {i["id"]: i for i in ir.register()["indikatorer"]}

    social = _metode_scoring(metode_tsx, "SOCIAL_METHODS")
    for kat in ir.sociale_kategorier():
        tekst = social.get(kat["id"])
        if tekst is None:
            _f(fund, f"metodeside mangler SOCIAL_METHODS[{kat['id']}]")
            continue
        antal = _antal_i_tekst(tekst)
        if antal is not None and antal != len(kat["indicators"]):
            _f(fund, f"metode {kat['id']}: teksten siger {antal} indikatorer, "
                     f"registret har {len(kat['indicators'])}")
        for iid in kat["indicators"]:
            tabel = by_id[iid].get("table", "")
            if tabel and tabel not in tekst and not tabel.startswith("GS/") \
                    and tabel != "Sundhedsprofilen" and "F&P" not in tabel:
                _f(fund, f"metode {kat['id']}: tabellen {tabel} ({iid}) nævnes ikke i beregningsteksten")

    eco = _metode_scoring(metode_tsx, "ECO_METHODS")
    for dim in ir.oekologiske_dimensioner():
        tekst = eco.get(dim["id"])
        if tekst is None:
            _f(fund, f"metodeside mangler ECO_METHODS[{dim['id']}]")
            continue
        antal = _antal_i_tekst(tekst)
        if antal is not None and antal != len(dim["indicators"]):
            _f(fund, f"metode {dim['id']}: teksten siger {antal} indikatorer, "
                     f"registret har {len(dim['indicators'])}")
        if len(dim["indicators"]) > 1:
            siger_worst = "worst-of" in tekst.lower() and "ikke worst-of" not in tekst.lower()
            if (dim["aggregation"] == "worst-of") != siger_worst:
                _f(fund, f"metode {dim['id']}: registret siger aggregation={dim['aggregation']!r}, "
                         f"men beregningsteksten siger {'worst-of' if siger_worst else 'noget andet'}")


# Pil mod score: en kommune "afviger" når seriens værdi for scorens år er mere
# end PIL_TOLERANCE (relativt) fra scorens råværdi. Er det mere end
# PIL_ANDEL_FEJL af kommunerne, beskriver pilen et andet tal end scoren (en
# anden definition, et andet folketal) - det er en fejl. Færre afvigere er
# typisk revisioner hos kilden mellem to hentninger og meldes som info.
PIL_TOLERANCE = 0.01
PIL_ANDEL_FEJL = 0.10


def _tjek_pil_mod_score(fund: list[Fund], by_indicator: dict[str, list[dict]], raw: Path) -> None:
    serie: dict[tuple[str, str], dict[str, float]] = {}
    with open(raw, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            v = _parse_float(r["vaerdi"])
            if v is not None:
                serie.setdefault((r["indicator_id"], r["kommune_kode"]), {})[r["aar"]] = v
    for iid in sorted({i for i, _ in serie}):
        rows = [r for r in by_indicator.get(iid, []) if _parse_float(r["raw_value"]) is not None]
        if not rows:
            continue
        aarene = [r["data_year"] for r in rows]
        aar = max(set(aarene), key=aarene.count).split("-")[-1]   # slutåret
        par = []
        for r in rows:
            s_v = serie.get((iid, r["kommune_kode"]), {}).get(aar)
            if s_v is not None:
                par.append((r["kommune_navn"], _parse_float(r["raw_value"]), s_v))
        if not par:
            slut = max((a for (i, _), d in serie.items() if i == iid for a in d), default="?")
            _info(fund, f"{iid}: pilens serie slutter i {slut}, scoren er fra {aar} - "
                        f"kør fetch_trend_history.py, så pil og score er fra samme hentning")
            continue
        afviger = [(n, m, v) for n, m, v in par
                   if abs(v - m) > PIL_TOLERANCE * max(abs(m), 1e-9)]
        if not afviger:
            continue
        n, m, v = max(afviger, key=lambda t: abs(t[2] - t[1]) / max(abs(t[1]), 1e-9))
        tekst = (f"{iid}: pilens serie afviger fra scoren i {len(afviger)} af {len(par)} "
                 f"kommuner i {aar} (størst: {n} {m} i scoren, {v} i serien)")
        if len(afviger) > PIL_ANDEL_FEJL * len(par):
            _f(fund, tekst + " - pilen beskriver et andet tal end scoren")
        else:
            _info(fund, tekst)


def kryds_tjek() -> list[Fund]:
    """Kører alle krydstjek og returnerer fundlisten. Kalder ikke sys.exit."""
    fund: list[Fund] = []

    # 1. Registret selv. Er det ugyldigt, giver resten ingen mening.
    try:
        reg = ir.register()
    except ir.RegisterFejl as e:
        _f(fund, str(e))
        return fund

    master_csv = ROOT / "data" / "master_indicators.csv"
    if not master_csv.exists():
        _f(fund, f"master_indicators.csv mangler ({master_csv}) - kør build_master_csv.py først")
        return fund
    by_indicator: dict[str, list[dict]] = {}
    with open(master_csv, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            by_indicator.setdefault(r["indicator_id"], []).append(r)

    by_id = {i["id"]: i for i in reg["indikatorer"]}
    scoret = ir.scorede_sociale()

    # 1b. Master har præcis de 98 kommuner i data/kommuner.json.
    from kommuner import KOMMUNER
    master_kommuner = {(r["kommune_kode"], r["kommune_navn"]) for rs in by_indicator.values() for r in rs}
    for kode, navn in sorted(master_kommuner - set(KOMMUNER.items())):
        _f(fund, f"master har kommunen {kode} {navn!r}, som ikke står i data/kommuner.json")
    for kode, navn in sorted(set(KOMMUNER.items()) - master_kommuner):
        _f(fund, f"kommunen {kode} {navn} fra data/kommuner.json mangler i master")

    # 2. Master indeholder præcis registrets indikatorer.
    master_ids = {i for i in by_indicator if not i.startswith("_dim_")}
    for i in sorted(master_ids - set(by_id)):
        _f(fund, f"{i}: står i master_indicators.csv, men ikke i registret (gammel master?)")
    for i in sorted(set(by_id) - master_ids):
        niveau = _f if (i in scoret or by_id[i]["category"] == "ecological") else _info
        niveau(fund, f"{i}: står i registret, men har ingen rækker i master (mangler CSV'en {by_id[i]['csv']}?)")
    for i in sorted(ir.ikke_scoret()):
        _f(fund, f"{i}: social indikator uden kategori - scor den eller flyt den til _fjernet (CLAUDE.md pkt. 9 og 18)")

    # 3. Retning mod dataen: fortegnet på korrelationen mellem råværdi og ratio
    #    skal passe med 'inverse' (sociale) og 'lower_is_better' (økologiske).
    #    Sociale ratios på 150 er klippet (R1) og udelades.
    for ind in reg["indikatorer"]:
        kat = ind["category"]
        if kat == "context":
            continue
        par = [(_parse_float(r["raw_value"]), _parse_float(r["ratio"])) for r in by_indicator.get(ind["id"], [])]
        par = [(a, b) for a, b in par if a is not None and b is not None and not (kat == "social" and b == 150.0)]
        if len(par) <= 10:
            continue
        raa, ratio = zip(*par)
        korr = _korrelation(raa, ratio)
        if kat == "social" and (korr < 0) != ind["inverse"]:
            _f(fund, f"{ind['id']}: inverse={ind['inverse']} i registret, men korrelation(rå, ratio)="
                     f"{korr:.2f} i master-CSV'en siger det modsatte")
        # Øko-konvention: høj ratio = værre. lower_is_better=True skal give korr > 0.
        if kat == "ecological" and (korr > 0) != ind["lower_is_better"]:
            _f(fund, f"øko {ind['id']}: lower_is_better={ind['lower_is_better']} i registret, men "
                     f"korrelation(rå, ratio)={korr:.2f} i master-CSV'en siger det modsatte (R12)")

    # 4. Tabelnavnet på metodesiden (table) skal passe med kildeteksten i master (source).
    for ind in reg["indikatorer"]:
        tabel = ind.get("table")
        if tabel and tabel not in ind["source"] and not tabel.startswith("GS/") \
                and tabel != "Sundhedsprofilen":
            _f(fund, f"{ind['id']}: table={tabel!r}, men source={ind['source']!r}")

    # 5. Retningspilene: alle id'er i tidsserien skal kendes af registret,
    #    ellers klassificeres de tavst som "kontekst".
    raw = ROOT / "data" / "trend_history_raw.csv"
    if raw.exists():
        with open(raw, encoding="utf-8") as f:
            trend_ids = {r["indicator_id"] for r in csv.DictReader(f)}
        for i in sorted(trend_ids - set(ir.op_er_godt())):
            _f(fund, f"{i}: har tidsserie i trend_history_raw.csv, men ingen retning i registret")

    # 5b. Pilen og scoren skal beskrive samme tal. Tidsseriens værdi for
    #     scorens år skal være scorens råværdi (CLAUDE.md pkt. 13 og 37).
    if raw.exists():
        _tjek_pil_mod_score(fund, by_indicator, raw)

    # 6. Metodesidens fritekst mod registret.
    metode_tsx = (ROOT / "webapp" / "app" / "metode" / "page.tsx").read_text(encoding="utf-8")
    _tjek_metodeside(fund, metode_tsx)

    # 7. Pladsholdere i teksterne ({ref:pesticider:1} osv., udfyldes af
    #    udfyldTal() i shared.ts) skal pege på en indikator der findes i master.
    #    Webappens build fejler ellers - her fanges det før commit.
    register_tekst = ir.REGISTER.read_text(encoding="utf-8")
    for kilde, tekst in (("indikatorer.json", register_tekst), ("metodesiden", metode_tsx)):
        for m in re.finditer(r"\{(ref|daekning|mangler|aar)(?::(\w+))?(?::\d)?\}", tekst):
            iid = m.group(2)
            if iid not in master_ids:
                _f(fund, f"{kilde}: pladsholderen {m.group(0)} peger på en indikator der ikke er i master")
            elif m.group(1) == "ref" and not any(r.get("reference") for r in by_indicator[iid]):
                _f(fund, f"{kilde}: pladsholderen {m.group(0)} - {iid} har ingen reference i master")

    return fund


def main() -> int:
    fund = kryds_tjek()
    fejl = [f for f in fund if f.niveau == "fejl"]
    info = [f for f in fund if f.niveau == "info"]
    for f in info:
        print(f"info: {f.tekst}")
    if fejl:
        print(f"\n{'=' * 60}\nKONSISTENSFEJL ({len(fejl)}):\n{'=' * 60}")
        for f in fejl:
            print(f"  ✗ {f.tekst}")
    else:
        print("\n✓ Ingen konsistensfejl fundet")
    print(f"\n{len(fejl)} fejl, {len(info)} infomeldinger")
    return 1 if fejl else 0


if __name__ == "__main__":
    sys.exit(main())
