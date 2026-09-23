#!/usr/bin/env python3
"""
fetch_vp3_vandkvalitet.py - Overfladevandets økologiske tilstand pr. kommune (VP3)
===================================================================================
Henter Vandområdeplan 3 (VP3, 2e2025) og beregner for hver kommune andelen af
vandområder (vandløb, søer og kystvande) i mindst god økologisk tilstand.

Datagrundlag:
  MiljøGIS VP3-shapefiler. Hvert vandområde har felterne:
    til_oko_sm  = samlet økologisk tilstand (tekst)
    kom1..kom4  = de kommuner vandområdet ligger i (op til 4, kommunenavne)
    ov_id       = vandområde-id
  Vi tæller et vandområde med for HVER kommune det berører (kom1-4).

Målopfyldelse (EU Vandrammedirektiv): et vandområde opfylder målet hvis tilstanden
er "Høj"/"God økologisk tilstand" eller "Maksimalt"/"Godt økologisk potentiale"
(potentiale bruges for kunstige/stærkt modificerede vandområder). "Ukendt" tælles
ikke med i nævneren.

Ratio-konvention (eco: høj = værre, konsistent med resten af platformen):
  pct_god        = andel af kommunens vandområder i god tilstand
  national_pct   = samme andel på landsplan (pooled)
  ratio          = (national_pct / pct_god) * 100   [høj pct = lav ratio = grøn]
  Cappes ved 300. pct_god = 0 → ratio = 300.
Vi scorer mod landsgennemsnittet (så kommuner kan skelnes). EU's mål er at ALLE
vandområder skal være i mindst god tilstand i 2027 - det vises som kontekst på
metodesiden, ikke som scoringsgrænse (samme tilgang som arealanvendelse).

Krav:
  pip3 install geopandas

Brug (fra projektets rodmappe):
  python3 scripts/fetch_vp3_vandkvalitet.py
  python3 scripts/fetch_vp3_vandkvalitet.py --zip /sti/til/vp3_2e2025.zip

Output:
  data/vp3_vandkvalitet_scores.csv
"""

import argparse
import csv
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import geopandas as gpd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kommuner import KOMMUNER  # noqa: E402  (de 98 kommuner, data/kommuner.json)

# ─── Stier og konstanter ──────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "vp3_vandkvalitet_scores.csv"

ZIP_URL = "https://files-miljoegis.mim.dk/vp3_2e2025/vp3_2e2025.zip"

# De tre "samlet"-lag med samlet økologisk tilstand pr. vandområde
LAG = [
    "vp3_2e2025_vandloeb_samlet",
    "vp3_2e2025_soe_samlet",
    "vp3_2e2025_marin_samlet",
]

STATUS_KOL = "til_oko_sm"
KOM_KOLONNER = ["kom1", "kom2", "kom3", "kom4"]

# Tilstande der opfylder EU's mål om mindst god tilstand
GOD_TILSTAND = {
    "Høj økologisk tilstand",
    "God økologisk tilstand",
    "Maksimalt økologisk potentiale",
    "Godt økologisk potentiale",
}
UKENDT = {"Ukendt", "", None}

CAP = 300.0

NAVN_TIL_KODE = {navn: kode for kode, navn in KOMMUNER.items()}


def find_eller_hent_shapefiles() -> Path:
    """Find mappen med VP3-shapefiler. Download + udpak hvis ikke til stede."""
    parser = argparse.ArgumentParser(description="VP3 vandkvalitet pr. kommune")
    parser.add_argument("--zip", default=None, help="Sti til vp3_2e2025.zip (downloades ellers)")
    parser.add_argument("--dir", default=None, help="Sti til allerede udpakket Shapefiler-mappe")
    args = parser.parse_args()

    # 1. Eksplicit udpakket mappe
    if args.dir:
        d = Path(args.dir)
        if (d / (LAG[0] + ".shp")).exists():
            return d

    # 2. Kendte cache-steder (fra tidligere kørsel)
    cache_base = Path(tempfile.gettempdir())
    for kandidat in [cache_base / "vp3_2e2025" / "Shapefiler", Path("/tmp/vp3/Shapefiler")]:
        if (kandidat / (LAG[0] + ".shp")).exists():
            print(f"Bruger eksisterende shapefiler: {kandidat}")
            return kandidat

    # 3. Download + udpak
    zip_sti = Path(args.zip) if args.zip else cache_base / "vp3_2e2025.zip"
    if not zip_sti.exists():
        print(f"Henter VP3 (~370 MB) fra {ZIP_URL} ...")
        urllib.request.urlretrieve(ZIP_URL, zip_sti)
        print(f"  Gemt: {zip_sti}")

    udpak_til = cache_base / "vp3_2e2025"
    print(f"Udpakker til {udpak_til} ...")
    with zipfile.ZipFile(zip_sti) as z:
        z.extractall(udpak_til)

    shp_dir = udpak_til / "Shapefiler"
    if not (shp_dir / (LAG[0] + ".shp")).exists():
        # Nogle zips har ikke en Shapefiler-undermappe - find filen rekursivt
        traef = list(udpak_til.rglob(LAG[0] + ".shp"))
        if traef:
            return traef[0].parent
        print("FEJL: Kunne ikke finde shapefiler efter udpakning", file=sys.stderr)
        sys.exit(1)
    return shp_dir


def er_god(status) -> bool:
    return status in GOD_TILSTAND


def main():
    shp_dir = find_eller_hent_shapefiles()
    print(f"Læser VP3-lag fra {shp_dir}")

    # Per kommune: [god, total]. Total ekskluderer "Ukendt".
    per_komm = {kode: [0, 0] for kode in KOMMUNER}  # kode -> [god, total]
    nat_god = 0
    nat_total = 0
    ukendte_navne = set()

    for lag in LAG:
        sti = shp_dir / (lag + ".shp")
        if not sti.exists():
            print(f"  ⚠ Mangler lag: {lag}")
            continue
        gdf = gpd.read_file(sti)
        print(f"  {lag}: {len(gdf)} vandområder")

        for _, row in gdf.iterrows():
            status = row.get(STATUS_KOL)
            if status in UKENDT:
                continue
            god = er_god(status)

            # National (pooled): hvert vandområde tælles én gang
            nat_total += 1
            if god:
                nat_god += 1

            # Kommune-tildeling: tæl med for hver kommune vandområdet berører
            komms = set()
            for kol in KOM_KOLONNER:
                navn = row.get(kol)
                if navn and str(navn).strip():
                    komms.add(str(navn).strip())
            for navn in komms:
                kode = NAVN_TIL_KODE.get(navn)
                if kode is None:
                    ukendte_navne.add(navn)
                    continue
                per_komm[kode][1] += 1
                if god:
                    per_komm[kode][0] += 1

    if ukendte_navne:
        print(f"  ⚠ Ukendte kommunenavne (ignoreret): {sorted(ukendte_navne)}")

    national_pct = (nat_god / nat_total * 100) if nat_total else 0.0
    print(f"\nLandsplan: {nat_god}/{nat_total} vandområder i god tilstand = {national_pct:.1f}%")

    # ─── Beregn ratio og skriv CSV ────────────────────────────────────────────
    rows_out = []
    for kode, navn in sorted(KOMMUNER.items()):
        god, total = per_komm[kode]
        if total == 0:
            rows_out.append({
                "kommune_kode": kode, "kommune_navn": navn,
                "pct_god_tilstand": "", "antal_vandomraader": 0, "vandkvalitet_ratio": "",
                "overfladevand_ref": round(national_pct, 4),
            })
            continue
        pct = round(god / total * 100, 2)
        if pct <= 0:
            ratio = CAP
        else:
            ratio = round(min((national_pct / pct) * 100, CAP), 2)
        rows_out.append({
            "kommune_kode": kode, "kommune_navn": navn,
            "pct_god_tilstand": pct, "antal_vandomraader": total, "vandkvalitet_ratio": ratio,
            "overfladevand_ref": round(national_pct, 4),
        })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["kommune_kode", "kommune_navn", "pct_god_tilstand", "antal_vandomraader", "vandkvalitet_ratio",
                  "overfladevand_ref"]
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows_out)

    med_data = [r for r in rows_out if r["pct_god_tilstand"] != ""]
    print(f"\nSkrev {len(rows_out)} kommuner ({len(med_data)} med data) til {OUTPUT.relative_to(ROOT)}")

    # Eksempler
    for kode in ["787", "851", "101"]:
        r = next((x for x in rows_out if x["kommune_kode"] == kode), None)
        if r and r["pct_god_tilstand"] != "":
            print(f"  {r['kommune_navn']}: {r['pct_god_tilstand']}% god ({r['antal_vandomraader']} vandområder), ratio {r['vandkvalitet_ratio']}")


if __name__ == "__main__":
    main()

    # ───────────────────────────────────────────────────────────
    # AUTO-REBUILD af master_indicators.csv
    # ───────────────────────────────────────────────────────────
    try:
        import sys as _sys
        from pathlib import Path as _Path
        _sys.path.insert(0, str(_Path(__file__).resolve().parent))
        from build_master_csv import auto_build_master
        auto_build_master()
    except Exception as _e:
        print(f"\n⚠ Kunne ikke auto-rebuild master-CSV: {_e}")
        print("  Rådata er gemt. Kør manuelt: python3 scripts/build_master_csv.py")
