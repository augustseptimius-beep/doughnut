#!/usr/bin/env python3
"""
hent_kommunegraenser.py - genskab data/kommunegraenser_25832.gpkg fra DAGI.

Kommunegrænserne bruges af otte scripts til rumlige analyser (kystrisiko,
luftkvalitet, biodiversitet, grundvandsdannelse m.fl.). De hentede dem indtil
juli 2026 fra DAWA, som er lukket. Grænserne ændres sjældent (sidste
kommunesammenlægning 2007), så de ligger nu som en afledt fil i git, ligesom
data/befolkning_1km_2021_dk.csv, og scripterne læser den via
scripts/kommunegraenser.py. Kør dette script kun, når en kommunegrænse er
ændret.

Kilde: DAGI (Danmarks Administrative Geografiske Inddeling), Klimadatastyrelsen
via Datafordeleren, læst fra datagrundlag.dk (scripts/datagrundlag.py).
Kolonnerne er de samme som DAWA's: kode (fire cifre, "0787"), navn og geometri
i EPSG:25832. Christiansø (0411) ligger uden for kommuneinddelingen og er ikke
med. Scriptet stopper, hvis resultatet ikke er præcis de 98 kommuner i
data/kommuner.json.

Kør fra projektets rodmappe (kræver `pip install duckdb`):
  python3 scripts/hent_kommunegraenser.py
  python3 scripts/hent_kommunegraenser.py --dato 2026-09-27   # bestemt snapshot
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from datagrundlag import forbindelse, snapshot  # noqa: E402
from kommunegraenser import FIL, KVITTERING  # noqa: E402
from kommuner import KODER  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dato", help="snapshot på eller før denne dato (ÅÅÅÅ-MM-DD)")
    args = ap.parse_args()

    url, snap = snapshot("dagi", "kommuneinddeling", args.dato)
    print(f"DAGI kommuneinddeling, snapshot {snap}")
    con = forbindelse()
    tmp = FIL.with_suffix(".tmp.gpkg")
    tmp.unlink(missing_ok=True)
    con.execute(f"""
        COPY (SELECT kommunekode AS kode, navn, the_geom AS geom
              FROM read_parquet('{url}')
              WHERE coalesce(udenforkommuneinddeling, 0) = 0
              ORDER BY kommunekode)
        TO '{tmp}' WITH (FORMAT GDAL, DRIVER 'GPKG', SRS 'EPSG:25832', LAYER_NAME 'kommuner')""")

    koder = {k for (k,) in con.execute(
        f"SELECT kommunekode FROM read_parquet('{url}') WHERE coalesce(udenforkommuneinddeling, 0) = 0").fetchall()}
    koder = {k.lstrip("0") for k in koder}
    if koder != KODER:
        tmp.unlink(missing_ok=True)
        raise SystemExit(f"FEJL: DAGI har {len(koder)} kommuner. Mangler {sorted(KODER - koder)}, "
                         f"ekstra {sorted(koder - KODER)}. Filen er ikke skrevet.")
    tmp.replace(FIL)
    KVITTERING.write_text(json.dumps({
        "kilde": "DAGI kommuneinddeling, Klimadatastyrelsen via Datafordeleren, læst fra datagrundlag.dk",
        "snapshot": snap,
        "hentet": date.today().isoformat(),
        "kommuner": len(koder),
        "crs": "EPSG:25832",
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"  ✓ {FIL.name}: {len(koder)} kommuner, {FIL.stat().st_size / 1e6:.0f} MB")


if __name__ == "__main__":
    main()
