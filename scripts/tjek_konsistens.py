#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tjek_konsistens.py - krydstjek af konfiguration, kode og data.

Hvorfor den findes
------------------
Samme oplysning (om en indikator er inverteret, hvilket dataår den har,
hvilken DST-tabel den kommer fra, hvor mange indikatorer en kategori har)
står flere steder på tværs af Python og TypeScript, og de steder holdes ved
lige i hånden. To gennemgange (sep. 2026) fandt gentagne gange at de var
kommet ud af trit: `OP_ER_GODT` i build_trends_csv.py modsagde `inverse` i
shared.ts, N-loft havde omvendt fortegn, ca. 25 dataYear-felter var
forældede, ECO_RAW_KEY_MAP manglede en indikator. Ingen af de fejl gav en
synlig krascs - de viste bare et forkert tal eller en forkert pil.

Dette script krydstjekker de steder automatisk. Ren diagnose, skriver ingen
filer, ændrer ingen tal - ligesom tjek_robusthed.py.

Brug
----
  cd /sti/til/doughnut
  python3 scripts/tjek_konsistens.py

Exit-kode 1 hvis der er fejl, 0 hvis ikke. Kaldes automatisk fra
build_master_csv.py's auto_build_master() (printer altid, fejler aldrig
kørslen - se den funktions egen begrundelse) og fra build_master_csv.py's
__main__ (afbryder med exit 1, så en manuel køre-og-commit fanger fejlen
FØR push, i stedet for at den lander stille i master_indicators.csv).

Begrænsning
-----------
Scriptet parser shared.ts og metode/page.tsx med regex, ikke en rigtig
TypeScript-parser. Det er skrøbeligt over for større omskrivninger af de
filer, men projektets øvrige CSV-parsing er lige så bevidst enkel (se
CLAUDE.md "Designet er MVP") - en regex der fanger den faktiske struktur er
bedre end ingen kontrol.
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

import build_master_csv as bm  # noqa: E402
import build_trends_csv as bt  # noqa: E402


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
    3.10, og CLAUDE.md pkt. 19 dokumenterer at maskinen kører 3.9 - der ville
    tjekket crashe og (før rettelsen) blive tolket som bestået."""
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


# ─── Parsing af TypeScript-konfiguration (regex, se docstring) ──────────

def _parse_indicators(shared_ts: str) -> dict[str, dict]:
    blok = shared_ts[shared_ts.index("export const INDICATORS"): shared_ts.index("// --- SOCIAL CATEGORIES")]
    ud: dict[str, dict] = {}
    for m in re.finditer(r"\{\s*id: \"(\w+)\",([\s\S]*?)\n  \}", blok):
        krop = m.group(2)
        felt = lambda navn: (re.search(navn + r': "([^"]*)"', krop) or [None, None])[1]  # noqa: E731
        ud[m.group(1)] = dict(
            table=felt("table"),
            dataYear=felt("dataYear"),
            inverse="inverse: true" in krop,
            absolut="absoluteScore: true" in krop,
        )
    return ud


def _parse_social_categories(shared_ts: str) -> dict[str, list[str]]:
    blok = shared_ts[shared_ts.index("export const SOCIAL_CATEGORIES"): shared_ts.index("// --- ECOLOGICAL CEILING")]
    return {
        m.group(1): re.findall(r'"(\w+)"', m.group(2))
        for m in re.finditer(r'id: "(\w+)",\s*name: "[^"]+",[\s\S]*?indicatorIds: \[([^\]]*)\]', blok)
    }


def _parse_eco_subs(shared_ts: str) -> list[dict]:
    blok = shared_ts[shared_ts.index("export const ECOLOGICAL_DIMENSIONS"): shared_ts.index("// --- CATEGORY SCORE")]
    return [
        dict(rawKey=m.group(1), ratioKey=m.group(2), lavere_er_bedre=m.group(3) == "true")
        for m in re.finditer(
            r'rawKey: "(\w+)",\s*ratioKey: "(\w+)",\s*label: "[^"]+",[^}]*?lowerIsBetter: (true|false)', blok
        )
    ]


def _parse_eco_raw_key_map(data_ts: str) -> dict[str, tuple[str, str]]:
    return {
        m.group(1): (m.group(2), m.group(3))
        for m in re.finditer(r'(\w+):\s*\{ rawKey: "(\w+)",\s*ratioKey: "(\w+)" \}', data_ts)
    }


TAL_ORD = {"en": 1, "et": 1, "to": 2, "tre": 3, "fire": 4, "fem": 5, "seks": 6,
           "syv": 7, "otte": 8, "ni": 9, "ti": 10}


def _tjek_metodeside(fund: list[Fund], metode_tsx: str, indicators: dict, kategorier: dict[str, list[str]],
                     master_soc: dict, by_indicator: dict[str, list[dict]]) -> None:
    rationale_blok = metode_tsx[metode_tsx.index("INDICATOR_RATIONALES"): metode_tsx.index("const SOCIAL_METHODS")]
    rationaler = set(re.findall(r"^\s{2}(\w+): \"", rationale_blok, re.M))
    scoret = {i for ids in kategorier.values() for i in ids}
    for i in sorted(scoret - rationaler):
        _info(fund, f"intet rationale på metodesiden for {i}")
    for i in sorted(rationaler - set(indicators)):
        _f(fund, f"metodeside har rationale for ukendt/fjernet indikator {i}")

    for kat_id, ids in kategorier.items():
        m = re.search(kat_id + r": \{\s*id: \"" + kat_id + r"\",\s*scoring: \"([^\"]*)\"", metode_tsx)
        if not m:
            _f(fund, f"metodeside mangler SOCIAL_METHODS[{kat_id}]")
            continue
        scoring_tekst = m.group(1)
        antal_match = re.search(r"(?:Gennemsnit af (?:op til )?|^)(\w+) indikator", scoring_tekst)
        if antal_match and TAL_ORD.get(antal_match.group(1)) and TAL_ORD[antal_match.group(1)] != len(ids):
            _f(fund, f"metode {kat_id}: teksten siger {antal_match.group(1)} indikatorer, "
                     f"kategorien har faktisk {len(ids)}")
        for i in ids:
            tabel = indicators.get(i, {}).get("table")
            if tabel and tabel not in scoring_tekst and not tabel.startswith("GS/") \
                    and tabel != "Sundhedsprofilen" and "F&P" not in tabel:
                _f(fund, f"metode {kat_id}: tabellen {tabel} ({i}) nævnes ikke i beregningsteksten")
        csv_match = re.search(kat_id + r": \{[\s\S]*?csvFile: \"([^\"]*)\"", metode_tsx)
        if csv_match:
            for i in ids:
                if i in master_soc and master_soc[i]["csv"] not in csv_match.group(1):
                    _f(fund, f"metode {kat_id}: datafilen {master_soc[i]['csv']} ({i}) "
                             f"mangler i csvFile '{csv_match.group(1)}'")


def kryds_tjek() -> list[Fund]:
    """Kører alle krydstjek og returnerer fundlisten. Kalder ikke sys.exit."""
    fund: list[Fund] = []

    shared_ts = (ROOT / "webapp" / "lib" / "shared.ts").read_text(encoding="utf-8")
    data_ts = (ROOT / "webapp" / "lib" / "data.ts").read_text(encoding="utf-8")
    metode_tsx = (ROOT / "webapp" / "app" / "metode" / "page.tsx").read_text(encoding="utf-8")
    master_csv = ROOT / "data" / "master_indicators.csv"
    if not master_csv.exists():
        _f(fund, f"master_indicators.csv mangler ({master_csv}) - kør build_master_csv.py først")
        return fund

    indicators = _parse_indicators(shared_ts)
    kategorier = _parse_social_categories(shared_ts)
    eco_subs = _parse_eco_subs(shared_ts)
    eco_raw_key_map = _parse_eco_raw_key_map(data_ts)
    scoret = {i for ids in kategorier.values() for i in ids}

    by_indicator: dict[str, list[dict]] = {}
    for r in csv.DictReader(master_csv.open(encoding="utf-8")):
        by_indicator.setdefault(r["indicator_id"], []).append(r)

    master_soc = {i["id"]: i for i in bm.SOCIAL_INDICATORS}
    master_eco = {i["id"]: i for i in bm.ECO_SUB_INDICATORS}

    # 1. Id-mængder: scoret i shared.ts <-> defineret i build_master_csv.py
    for i in scoret - set(indicators):
        _f(fund, f"{i}: bruges i en SOCIAL_CATEGORIES.indicatorIds, men findes ikke i INDICATORS")
    for i in scoret - set(master_soc):
        _f(fund, f"{i}: scores i shared.ts, men mangler i build_master_csv.py SOCIAL_INDICATORS")
    for i in set(master_soc) - set(indicators):
        _f(fund, f"{i}: findes i build_master_csv.py, men mangler i shared.ts INDICATORS")
    for i in set(indicators) - scoret:
        _info(fund, f"INDICATORS[{i}] er ikke scoret i nogen kategori (ok hvis bevidst, se CLAUDE.md pkt. 9/18)")

    # Master-CSV'ens dimension-felt skal matche den kategori indikatoren rent faktisk ligger i
    for kat_id, ids in kategorier.items():
        for i in ids:
            if i in master_soc and master_soc[i]["dimension"] != kat_id:
                _f(fund, f"{i}: build_master_csv.py sætter dimension={master_soc[i]['dimension']!r}, "
                         f"men ligger i kategorien {kat_id!r} i shared.ts")

    # 2. Retning: inverse (shared.ts) vs. OP_ER_GODT (build_trends_csv.py)
    for i in scoret:
        if indicators[i]["absolut"] and i == "bolig_fossil":
            continue  # allerede vendt i selve scoren, se CLAUDE.md pkt. 10
        if i in bt.OP_ER_GODT and bt.OP_ER_GODT[i] == indicators[i]["inverse"]:
            _f(fund, f"{i}: OP_ER_GODT={bt.OP_ER_GODT[i]} i build_trends_csv.py modsiger "
                     f"inverse={indicators[i]['inverse']} i shared.ts (T5)")

    # 3. Retning vs. faktiske data: korrelation mellem råværdi og ratio skal
    #    have det fortegn `inverse`/`lowerIsBetter` foreskriver. Ratio=150 er
    #    klippet af R1 og udelades for ikke at forvrænge korrelationen.
    for i in scoret:
        par = [(_parse_float(r["raw_value"]), _parse_float(r["ratio"])) for r in by_indicator.get(i, [])
               if _parse_float(r["raw_value"]) is not None and _parse_float(r["ratio"]) not in (None, 150.0)]
        if len(par) > 10:
            raa, ratio = zip(*par)
            korr = _korrelation(raa, ratio)
            if (korr < 0) != indicators[i]["inverse"]:
                _f(fund, f"{i}: inverse={indicators[i]['inverse']} i shared.ts, men korrelation(rå, ratio)={korr:.2f} "
                         f"i master-CSV'en siger det modsatte")

    raw_key_til_id = {v[0]: k for k, v in eco_raw_key_map.items()}
    for sub in eco_subs:
        indicator_id = raw_key_til_id.get(sub["rawKey"])
        par = [(_parse_float(r["raw_value"]), _parse_float(r["ratio"])) for r in by_indicator.get(indicator_id, [])
               if _parse_float(r["raw_value"]) is not None and _parse_float(r["ratio"]) is not None]
        if len(par) > 10:
            raa, ratio = zip(*par)
            korr = _korrelation(raa, ratio)
            # Øko-konvention: høj ratio = værre. lowerIsBetter=True skal derfor give korr > 0.
            if (korr > 0) != sub["lavere_er_bedre"]:
                _f(fund, f"øko {indicator_id}: lowerIsBetter={sub['lavere_er_bedre']} i shared.ts, men "
                         f"korrelation(rå, ratio)={korr:.2f} i master-CSV'en siger det modsatte (R12)")

    # 4. INDICATORS[].dataYear (fallback-felt, se ScoreBars.tsx) vs. master
    for i in scoret:
        master_aar = {r["data_year"] for r in by_indicator.get(i, [])}
        angivet = indicators[i]["dataYear"]
        if angivet and angivet not in master_aar and not any(angivet.endswith(y) for y in master_aar if y):
            _f(fund, f"{i}: shared.ts INDICATORS[].dataYear={angivet!r}, men master-CSV'en har {master_aar} "
                     f"(kun et fallback-felt, men bør stadig stemme - se ScoreBars.tsx)")
        tabel = indicators[i]["table"]
        kilde = master_soc.get(i, {}).get("source", "")
        if tabel and kilde and tabel not in kilde:
            _f(fund, f"{i}: shared.ts table={tabel!r}, men build_master_csv.py source={kilde!r}")

    # 5. Øko-mapping: ECOLOGICAL_DIMENSIONS.subIndicators <-> data.ts ECO_RAW_KEY_MAP <-> build_master_csv.py
    for sub in eco_subs:
        indicator_id = raw_key_til_id.get(sub["rawKey"])
        if indicator_id is None:
            _f(fund, f"øko rawKey {sub['rawKey']!r} (shared.ts) mangler i data.ts ECO_RAW_KEY_MAP")
            continue
        if eco_raw_key_map[indicator_id][1] != sub["ratioKey"]:
            _f(fund, f"øko {indicator_id}: ratioKey {sub['ratioKey']!r} i shared.ts != "
                     f"{eco_raw_key_map[indicator_id][1]!r} i data.ts")
        if indicator_id not in master_eco:
            _f(fund, f"øko {indicator_id} mangler i build_master_csv.py ECO_SUB_INDICATORS")
    for indicator_id in eco_raw_key_map:
        if indicator_id not in master_eco:
            _f(fund, f"data.ts ECO_RAW_KEY_MAP har {indicator_id!r}, som build_master_csv.py ikke kender")

    # 6. AVERAGE_DIMENSIONS skal være identisk i begge scripts (T6, kendt fælde)
    trends_average = getattr(bt, "AVERAGE_DIMENSIONS", set())
    if set(bm.AVERAGE_DIMENSIONS) != set(trends_average):
        _f(fund, f"AVERAGE_DIMENSIONS forskellig: build_master_csv.py={bm.AVERAGE_DIMENSIONS}, "
                 f"build_trends_csv.py={trends_average}")

    # 7. Metodeside: antal indikatorer, tabelhenvisninger, datafiler
    _tjek_metodeside(fund, metode_tsx, indicators, kategorier, master_soc, by_indicator)

    # 8. Doughnut-udgave: footeren beregnes nu i webapp/lib/data.ts
    #    (getDoughnutEdition()) fra præcis samme master-CSV. Intet at
    #    krydstjekke her længere - det var netop pointen med at fjerne det
    #    hårdkodede årstal (se data.ts og shared.ts's kommentarer).

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
