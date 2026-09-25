#!/usr/bin/env python3
"""
fetch_kvaelstof_kystvand.py - kvælstofbelastning af kystvandene mod målbelastningen
====================================================================================

Indikatoren `naer_kystvand` under Næringsstoffer: hvor meget kvælstof der i dag
løber fra land til de kystvande, kommunens areal afvander til, i procent af den
belastning kystvandene kan tåle og stadig nå god økologisk tilstand
(målbelastningen). 100 = præcis på grænsen. Det er en absolut grænse, ikke et
landsgennemsnit.

HVORFOR (sep. 2026)
-------------------
Målbelastningen er beregnet af DCE/DHI med mekanistiske modeller for hvert
kystvand, ud fra kravet om god økologisk tilstand i vandrammedirektivet. Den er
dermed den nedskalerede grænse for kvælstof, som planetary boundaries-
litteraturen efterlyser på regional skala (Steffen m.fl. 2015; Richardson m.fl.
2023), og som CONCITO (2025) bruger for Danmark samlet: 55.800 ton N mod en
målbelastning på 37.900 ton, en overskridelse på 1,5 gange.

Indikatoren afløser `naer_landbrug` (tålegrænsen pr. ha landbrug), der målte
hvor FØLSOMT kystvandet er, ikke hvor meget det belastes, og derfor ikke kunne
vise fremskridt. Den afløser også spildevandsindikatorerne `naer_nitrogen` og
`naer_phosphorus`: punktkilderne indgår allerede i statusbelastningen, og målt
pr. indbygger i den kommune renseanlægget ligger i, gav de et skævt billede
(Frederiksbergs spildevand renses i København).

DATAKILDER
----------
1. Tal: "Vandområdeplanerne 2021-2027 efter genbesøget", revideret april 2026
   (Styrelsen for Grøn Arealomlægning og Vandmiljø), bilag 1.1: pr. kystvand
   (helopland) statusbelastning, baselinebelastning 2027 og målbelastning,
   ton N/år. Statusbelastningen er afstrømningsnormaliseret og opdateret til og
   med 2021. Tabellen findes kun i PDF'en og udtrækkes her; resultatet gemmes i
   data/vp3_kvaelstof_kystvande.csv som kildespor.
2. Geometri: kystvandenes deloplande fra MiljøGIS (VP3 2. endelige 2025, lag
   vp3_2e2025_kystvand_opland_afg). Deloplandene overlapper ikke, og op_id er
   kystvandets id i bilag 1.1.
3. Kommunegrænser: DAWA.

METODE
------
- Pr. kystvand: statusbelastning / målbelastning × 100 for heloplandet.
- Kæden: et delopland afvander til sit eget kystvand og videre til alle
  kystvande nedstrøms (fx Roskilde Fjord indre → ydre → Kattegat,
  Nordsjælland). Deloplandet får den HØJESTE overskridelse i kæden - worst-of,
  samme logik som resten af de økologiske dimensioner. Kystvande uden
  målbelastning (åbent hav som Vesterhavet) springes over i kæden.
- Pr. kommune: arealvægtet gennemsnit over de dele af kommunen, der ligger i
  et delopland med en overskridelse.

HVORFOR KÆDEN (besluttet 25. sep. 2026)
---------------------------------------
Planens statusbelastning for et kystvand omfatter hele oplandet opstrøms:
Løgstør Bredning har et helopland på 5.088 km², som rummer både Thisted
Bredning og Nissum Bredning. Kvælstof fra Thy tæller altså med i Løgstørs
overskridelse (207%), og reduktioner dér hjælper Løgstør. Derfor får et
delopland den højeste overskridelse i sin kæde. Uden kæden ville Thisted
ligge på ca. 177 frem for 202,7.

TO FORBEHOLD VED FORMIDLING
---------------------------
- Tallet beskriver det vand kommunen afvander til, ikke kommunens eget
  bidrag. Arealvægtningen antager en jævn belastning pr. areal, men
  udvaskningen afhænger af jordtype og landbrug. Kommunerne omkring
  Limfjorden deler derfor langt hen ad vejen samme tal.
- Fanø, Varde og Tønder afvander delvist til Vesterhavet syd, der ikke har
  en målbelastning; de vægtes kun på resten af arealet
  (areal_andel_med_maal_pct, Fanø 73%).

Krav: pip install geopandas pypdf

Brug (fra projektets rodmappe):
  python3 scripts/fetch_kvaelstof_kystvand.py
  python3 scripts/fetch_kvaelstof_kystvand.py --pdf /sti/til/planen.pdf

Output:
  data/vp3_kvaelstof_kystvande.csv  (pr. kystvand, kildespor)
  data/n_kystvand_scores.csv        (pr. kommune)
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kommuner import KOMMUNER  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
KYSTVANDE_CSV = ROOT / "data" / "vp3_kvaelstof_kystvande.csv"
OUTPUT = ROOT / "data" / "n_kystvand_scores.csv"

PLAN_URL = ("https://sgavmst.dk/media/etsko0yf/"
            "vandomraadeplanerne-2021-2027-efter-genbesoeget-justeret.pdf")
WFS = ("https://wfs2-miljoegis.mim.dk/vp3_2endelig2025/ows?service=WFS&version=1.1.0"
       "&request=GetFeature&typeName=vp3_2e2025_kystvand_opland_afg&outputFormat=application/json")
DAWA_URL = "https://api.dataforsyningen.dk/kommuner?format=geojson"

# Kontrolrække: fanger en forskudt kolonne i PDF-udtrækket. Tallene står i
# planens eksempel side 197 og i bilag 1.1.
KONTROL = {"1": {"status": 986.9, "maal": 615.8}}

FARVANDE = r"(Nordsøen|Skagerrak|Kattegat|Nordlige Bælthav|Lillebælt|Storebælt|Sydlige Bælthav|Øresund|Østersøen)"
_START = re.compile(r"^(\d+) " + FARVANDE + r" (\d+)\s+(\d+)\s*(.*)$")
_STOP = re.compile(r"^(\*|Bilag|Kvælstof|Helopland|Delopland|Fosfor|Hovedfarvands|område|Netværk|kystvand|"
                   r"Areal|Status|Baseline|Mål|Brutto|Netto|Fordelt|ID Navn|\[\[side|\d{3}\s*$|"
                   r"med udgangspunkt|belastning|indsatsbehov|helopland)")
_TAL = re.compile(r"^-?\d{1,3}(\.\d{3})*(,\d+)?$|^-$")


def _pdf_tekst(sti: Path) -> str:
    import pypdf
    return "\n".join((p.extract_text() or "") for p in pypdf.PdfReader(str(sti)).pages)


def udtraek_bilag_1_1(tekst: str) -> dict[str, dict]:
    """Bilag 1.1 (kvælstof, helopland) som {kystvand_id: {...}}.

    Rækkerne har formen
      <farvands-id> <farvand> <netværk> <kystvand-id> <navn> [nedstrøms-id]
      <areal> <status> <baseline> [mål] [brutto] [netto] [fordelt] <3 × fosfor>
    hvor tomme felter mangler i teksten. Areal, status og baseline står altid.
    Målbelastningen afgøres af antallet af tal: 6 tal = intet mål (åbent hav);
    7 tal = mål hvis det 4. tal er mindst baseline (mål uden indsatsbehov),
    ellers et indsatstal uden mål; 8 eller flere = det 4. tal er målet."""
    start = tekst.find("Bilag 1.1: Beregning af fordelt indsatsbehov")
    if start < 0:
        raise SystemExit("FEJL: fandt ikke bilag 1.1 i planen - er PDF'en den rigtige?")
    linjer = tekst[start:].split("\n")
    raekker, cur = [], None
    for ln in linjer:
        s = ln.strip()
        if s.startswith("Bilag 2") or s.startswith("Bilag 3"):
            break
        m = _START.match(s)
        if m:
            if cur:
                raekker.append(cur)
            cur = {"id": m.group(4), "rest": m.group(5)}
        elif cur and s and not _STOP.match(s):
            cur["rest"] += " " + s
        elif cur and _STOP.match(s):
            raekker.append(cur)
            cur = None
    if cur:
        raekker.append(cur)

    ud: dict[str, dict] = {}
    for r in raekker:
        toks = r["rest"].replace("*", "").split()
        i = 0
        while i < len(toks) and not _TAL.match(toks[i]):
            i += 1
        navn, tal = " ".join(toks[:i]), toks[i:]
        ned = None
        if tal and re.fullmatch(r"\d+", tal[0]) and len(tal) > 1:
            ned, tal = tal[0], tal[1:]
        v = [None if t == "-" else float(t.replace(".", "").replace(",", ".")) for t in tal]
        if len(v) < 6 or None in v[:3]:
            raise SystemExit(f"FEJL: kan ikke læse bilag 1.1-rækken for kystvand {r['id']} ({navn}): {tal}")
        areal, status, baseline = v[0], v[1], v[2]
        if len(v) == 6:
            maal = None
        elif len(v) == 7:
            maal = v[3] if v[3] >= baseline else None
        else:
            maal = v[3]
        if r["id"] in ud:
            raise SystemExit(f"FEJL: kystvand {r['id']} står to gange i bilag 1.1")
        ud[r["id"]] = {"navn": navn, "ned": ned, "areal": areal, "status": status,
                       "baseline": baseline, "maal": maal}
    for kid, forventet in KONTROL.items():
        faktisk = ud.get(kid, {})
        if any(abs((faktisk.get(k) or 0) - x) > 0.05 for k, x in forventet.items()):
            raise SystemExit(f"FEJL: kontrolrækken for kystvand {kid} passer ikke ({faktisk}) - "
                             f"udtrækket af bilag 1.1 er forskudt, eller planen er revideret")
    return ud


def kaede_overskridelse(tab: dict[str, dict]) -> None:
    """Tilføjer 'pct' (status/mål) og 'kaede_pct' (højeste pct nedstrøms) pr. kystvand."""
    for t in tab.values():
        t["pct"] = round(t["status"] / t["maal"] * 100, 1) if t["maal"] else None

    def kaede(kid: str, set_: tuple[str, ...] = ()) -> list[float]:
        t = tab[kid]
        ud = [t["pct"]] if t["pct"] is not None else []
        if t["ned"] and t["ned"] in tab and t["ned"] not in set_:
            ud += kaede(t["ned"], set_ + (kid,))
        return ud

    for kid, t in tab.items():
        k = kaede(kid)
        t["kaede_pct"] = max(k) if k else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--pdf", help="Lokal kopi af planen (hentes ellers)")
    args = ap.parse_args()

    import geopandas as gpd

    print("=" * 66)
    print("Kvælstof til kystvande mod målbelastningen (VP3 efter genbesøget)")
    print("=" * 66)
    pdf = Path(args.pdf) if args.pdf else Path(tempfile.gettempdir()) / "vp3_efter_genbesoeget_2026.pdf"
    if not pdf.exists():
        print(f"  Henter planen: {PLAN_URL}")
        req = urllib.request.Request(PLAN_URL, headers={"User-Agent": "Mozilla/5.0 DoughnutDK/1.0"})
        with urllib.request.urlopen(req, timeout=300) as r, open(pdf, "wb") as f:
            f.write(r.read())
    tab = udtraek_bilag_1_1(_pdf_tekst(pdf))
    kaede_overskridelse(tab)
    med_maal = [t for t in tab.values() if t["maal"]]
    print(f"  {len(tab)} kystvande i bilag 1.1, {len(med_maal)} med målbelastning")
    over = sum(1 for t in med_maal if t["pct"] > 100)
    print(f"  {over} kystvande over målbelastningen")

    with open(KYSTVANDE_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["kystvand_id", "kystvand_navn", "nedstroems_id", "areal_helopland_km2",
                    "statusbelastning_ton_n", "baselinebelastning_2027_ton_n", "maalbelastning_ton_n",
                    "status_pct_af_maal", "kaede_pct_af_maal"])
        for kid in sorted(tab, key=int):
            t = tab[kid]
            # Navne fra PDF'en kan indeholde komma ("Roskilde Fjord, ydre"); csv-
            # modulet citerer dem, og filen læses ikke af webappen.
            w.writerow([kid, t["navn"], t["ned"] or "", t["areal"], t["status"], t["baseline"],
                        t["maal"] if t["maal"] is not None else "",
                        t["pct"] if t["pct"] is not None else "",
                        t["kaede_pct"] if t["kaede_pct"] is not None else ""])
    print(f"  ✓ {KYSTVANDE_CSV.relative_to(ROOT)}")

    print("  Henter deloplande (MiljøGIS) og kommunegrænser (DAWA)...")
    opl = gpd.read_file(WFS)
    if opl.crs is None or opl.crs.to_epsg() != 25832:
        opl = opl.set_crs(25832, allow_override=True) if opl.total_bounds[0] > 1000 else opl.to_crs(25832)
    opl["op_id"] = opl["op_id"].astype(str)
    uden = sorted(set(opl["op_id"]) ^ set(tab))
    if uden:
        raise SystemExit(f"FEJL: deloplande og bilag 1.1 passer ikke sammen: {uden}")
    opl["kaede_pct"] = opl["op_id"].map(lambda k: tab[k]["kaede_pct"])
    kom = gpd.read_file(DAWA_URL).to_crs(25832)
    kom["kode"] = kom["kode"].astype(int).astype(str)
    ov = gpd.overlay(opl[["op_id", "kaede_pct", "geometry"]], kom[["kode", "geometry"]], how="intersection")
    ov["a"] = ov.geometry.area

    rows = []
    for kode in sorted(KOMMUNER, key=int):
        g = ov[ov["kode"] == kode]
        m = g[g["kaede_pct"].notna()]
        if m["a"].sum() <= 0:
            rows.append([kode, KOMMUNER[kode], "", "", ""])
            continue
        pct = round(float((m["kaede_pct"] * m["a"]).sum() / m["a"].sum()), 1)
        andel = round(float(m["a"].sum() / g["a"].sum() * 100), 1)
        rows.append([kode, KOMMUNER[kode], pct, andel, pct])
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["kommune_kode", "kommune_navn", "n_belastning_pct_af_maal",
                    "areal_andel_med_maal_pct", "n_kystvand_ratio"])
        w.writerows(rows)
    vaerdier = [r[2] for r in rows if r[2] != ""]
    print(f"  ✓ {OUTPUT.relative_to(ROOT)}: {len(vaerdier)}/98 kommuner, "
          f"{min(vaerdier)}-{max(vaerdier)} % af målbelastningen, "
          f"{sum(1 for v in vaerdier if v > 100)} over")
    t = next(r for r in rows if r[0] == "787")
    print(f"  Thisted: {t[2]} % af målbelastningen")
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
