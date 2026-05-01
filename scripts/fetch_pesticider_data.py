#!/usr/bin/env python3
"""
Pesticider i drikkevand pr. danske kommune
==========================================
Henter data fra DN's opgørelse (2019-2023), baseret på GEUS Jupiter-databasen.
Indikatoren: andel af aktive vandindvindingsboringer med pesticidfund OVER
grænseværdien for drikkevand (0,1 µg/l).

Doughnut-kontekst (novel entities / forurening):
  Planetær grænse: 0% boringer over drikkevandsnormen (0,1 µg/l).
  Ratio-konvention: ratio = (kommune_pct / national_gns_pct) × 100
    ratio > 100 = over nationalt gennemsnit = overshoot (rød)
    ratio < 100 = under nationalt gennemsnit = relativt bedre
    ratio = 0 = ingen boringer over grænseværdien

Kilde: Danmarks Naturfredningsforening / GEUS Jupiter (2019-2023)
  https://via.ritzau.dk/pressemeddelelse/13787633/...

Brug:
  cd /sti/til/doughnut
  python3 scripts/fetch_pesticider_data.py

Output:
  data/pesticider_scores.csv
"""

import requests
import pandas as pd
import sys
import os

# ── Rådata fra DN's pressemeddelse (GEUS Jupiter 2019-2023) ──────────────────
# Format: (kommune_navn, total_boringer, boringer_med_fund, boringer_over_graense)
# None = ikke oplyst i kilden (0 eller manglende data behandles ens)

RAW_DATA = [
    ("Albertslund",   3,   3,   1),
    ("Allerød",      33,  14,   2),
    ("Assens",       75,  36,  10),
    ("Ballerup",     25,  19,  13),
    ("Billund",      28,   1,   0),
    ("Bornholm",     13,   6,   0),
    ("Brøndby",      10,   9,   5),
    ("Brønderslev",  58,  22,   0),
    ("Dragør",        5,   5,   2),
    ("Egedal",       55,  38,   5),
    ("Esbjerg",      65,  25,   9),
    ("Fanø",         10,   1,   0),
    ("Favrskov",     86,  32,   7),
    ("Faxe",         43,   8,   1),
    ("Fredensborg",  28,   2,   0),
    ("Fredericia",   19,   8,   0),
    ("Frederiksberg", 4,   4,   0),
    ("Frederikshavn",99,  38,  13),
    ("Frederikssund",70,  40,  10),
    ("Furesø",       25,  14,   0),
    ("Faaborg-Midtfyn", 67, 44, 5),
    ("Gentofte",     18,  18,   3),
    ("Gladsaxe",     17,  15,   4),
    ("Glostrup",     16,  11,   0),
    ("Greve",        42,  16,   2),
    ("Gribskov",     55,  22,   3),
    ("Guldborgsund", 114, 37,  22),
    ("Haderslev",    50,  19,   3),
    ("Halsnæs",      37,  23,   4),
    ("Hedensted",    78,  23,   4),
    ("Helsingør",    28,   4,   2),
    ("Herlev",       None,None, None),  # Ingen data
    ("Herning",      57,  11,   0),
    ("Hillerød",     67,  15,   1),
    ("Hjørring",    146,  79,  32),
    ("Holbæk",      117,  20,   3),
    ("Holstebro",    47,   8,   1),
    ("Horsens",      74,  25,   1),
    ("Hvidovre",      3,   3,   2),
    ("Høje-Taastrup",25,  24,   4),
    ("Hørsholm",      8,   6,   1),
    ("Ikast-Brande", 37,  10,   1),
    ("Ishøj",        29,  29,   1),
    ("Jammerbugt",  120,  38,   3),
    ("Kalundborg",  128,  33,   6),
    ("Kerteminde",   18,  13,   8),
    ("Kolding",      87,  22,   5),
    ("København",     2,   2,   1),
    ("Køge",         78,  50,   2),
    ("Langeland",    34,  22,   2),
    ("Lejre",        89,  35,   1),
    ("Lemvig",       27,   1,   0),
    ("Lolland",      70,  16,   3),
    ("Lyngby-Taarbæk", 3,  3,   1),
    ("Læsø",         15,   0,   0),
    ("Mariagerfjord",59,  10,   1),
    ("Middelfart",   59,  33,   8),
    ("Morsø",        55,  33,   7),
    ("Norddjurs",    74,  21,   1),
    ("Nordfyns",     63,  23,   5),
    ("Nyborg",       43,  29,   4),
    ("Næstved",      86,  15,   2),
    ("Odder",        31,   3,   0),
    ("Odense",       86,  59,  27),
    ("Odsherred",    90,   4,   0),
    ("Randers",     101,  34,   4),
    ("Rebild",       45,   8,   2),
    ("Ringkøbing-Skjern", 70, 19, 0),
    ("Ringsted",     61,  27,   2),
    ("Roskilde",     70,  29,   4),
    ("Rudersdal",    31,  18,   2),
    ("Rødovre",       5,   5,   2),
    ("Samsø",        13,   5,   3),
    ("Silkeborg",    93,  52,   4),
    ("Skanderborg",  94,  28,   1),
    ("Skive",        68,  29,   6),
    ("Slagelse",     94,  33,   9),
    ("Solrød",       30,  19,   3),
    ("Sorø",         34,  16,   2),
    ("Stevns",       40,  26,   5),
    ("Struer",       34,  12,   2),
    ("Svendborg",    56,  49,  15),
    ("Syddjurs",    116,  34,   2),
    ("Sønderborg",   84,  15,   2),
    ("Thisted",      59,  30,   3),
    ("Tønder",       58,  28,  10),
    ("Tårnby",        6,   6,   1),
    ("Vallensbæk",    3,   2,   0),
    ("Varde",        79,  33,  10),
    ("Vejen",        69,  11,   3),
    ("Vejle",       129,  45,   4),
    ("Vesthimmerlands", 94, 31, 5),
    ("Viborg",      101,  39,   7),
    ("Vordingborg",  94,  19,   6),
    ("Ærø",          25,  25,  15),
    ("Aabenraa",     66,  15,   0),
    ("Aalborg",     200, 104,  15),
    ("Aarhus",      148,  48,   0),
]

print("\n" + "="*60)
print("  Pesticider i drikkevand (DN/GEUS Jupiter 2019-2023)")
print("="*60)

# ── Trin 1: Byg DataFrame ─────────────────────────────────────────────────────
print("\nTrin 1/4: Bygger datasæt...")
rows = []
for navn, total, fund, over in RAW_DATA:
    if total is None:
        rows.append({"kommune_navn": navn, "total": None, "over_graense": None, "pct_over": None})
    else:
        pct_over = round((over / total) * 100, 2) if total > 0 else 0.0
        rows.append({
            "kommune_navn": navn,
            "total": total,
            "over_graense": over,
            "pct_over": pct_over,
        })

df = pd.DataFrame(rows)
print(f"  OK: {len(df)} kommuner i rådata")

# ── Trin 2: Nationalt gennemsnit ─────────────────────────────────────────────
print("\nTrin 2/4: Beregner nationalt gennemsnit...")
df_valid = df.dropna(subset=["pct_over"])
total_boringer = df_valid["total"].sum()
total_over = df_valid["over_graense"].sum()
national_pct = (total_over / total_boringer) * 100
print(f"  Samlet: {int(total_over)} boringer over grænseværdi af {int(total_boringer)} boringer")
print(f"  Nationalt gennemsnit: {national_pct:.2f}% af boringer over 0,1 µg/l")

# ── Trin 3: Kommunekoder fra DAWA ────────────────────────────────────────────
print("\nTrin 3/4: Henter kommunekoder fra DAWA...")
try:
    r = requests.get("https://api.dataforsyningen.dk/kommuner?format=json", timeout=30)
    r.raise_for_status()
    kommuner_dawa = r.json()
    # Byg navn→kode mapping
    name_to_code = {}
    for k in kommuner_dawa:
        name_to_code[k["navn"]] = int(k["kode"])
    print(f"  OK: {len(name_to_code)} kommuner fra DAWA")
except Exception as e:
    print(f"  FEJL ved DAWA: {e}")
    sys.exit(1)

# Manuel korrektioner for navneforskelle
NAME_FIXES = {
    "Vesthimmerlands": "Vesthimmerlands",
    "Faaborg-Midtfyn": "Faaborg-Midtfyn",
    "Lyngby-Taarbæk": "Lyngby-Taarbæk",
}

# ── Trin 4: Match kommunenavne og beregn ratio ────────────────────────────────
print("\nTrin 4/4: Matcher kommunenavne og beregner ratio...")

results = []
missing = []

for _, row in df.iterrows():
    navn = row["kommune_navn"]
    kode = name_to_code.get(navn)
    if kode is None:
        # Prøv DAWA-opslag med fuzzy match
        for dawa_navn, dawa_kode in name_to_code.items():
            if navn.lower() in dawa_navn.lower() or dawa_navn.lower() in navn.lower():
                kode = dawa_kode
                break
    if kode is None:
        missing.append(navn)
        continue

    pct_over = row["pct_over"]
    total = row["total"]
    over = row["over_graense"]

    if pct_over is None:
        # Ingen data (Herlev) - sæt ratio til None
        ratio = None
        raw_val = None
    else:
        # Grænsen er 0% (drikkevandsnorm) - enhver >0% er overshoot.
        # ratio = 0 hvis ingen fund, ellers max(101, relativ ratio):
        #   - bevarer relativ rangering mellem kommuner med fund
        #   - sikrer at ALLE kommuner med fund vises som rød (overshoot)
        if pct_over == 0:
            ratio = 0.0
        elif national_pct > 0:
            ratio = round(max(101.0, (pct_over / national_pct) * 100), 1)
        else:
            ratio = 101.0
        raw_val = round(pct_over, 2)

    results.append({
        "kommune_kode": kode,
        "kommune_navn": navn,
        "pesticid_pct_over_graense": raw_val,     # råværdi: % boringer over 0,1 µg/l
        "pesticid_ratio": ratio,                   # doughnut-ratio
        "pesticid_total_boringer": int(total) if (total is not None and not pd.isna(total)) else None,
        "pesticid_over_graense_antal": int(over) if (over is not None and not pd.isna(over)) else None,
    })

if missing:
    print(f"  ⚠ Kunne ikke matche: {missing}")

result_df = pd.DataFrame(results).sort_values("kommune_kode").reset_index(drop=True)
print(f"  OK: {len(result_df)} kommuner matchet")

# ── Gem CSV ───────────────────────────────────────────────────────────────────
OUTPUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "pesticider_scores.csv")
result_df.to_csv(OUTPUT, index=False, encoding="utf-8")
print(f"\n  ✓ Gemt: {OUTPUT}")

# ── Opsummering ───────────────────────────────────────────────────────────────
valid = result_df.dropna(subset=["pesticid_ratio"])
print(f"\n{'='*60}")
print(f"  FÆRDIG! {len(result_df)} kommuner, {len(valid)} med data")
print(f"{'='*60}")
print(f"\nNationalt gennemsnit: {national_pct:.2f}% af boringer over grænseværdien")
print(f"\nVærste kommuner (% boringer over 0,1 µg/l):")
print(valid.nlargest(5, "pesticid_pct_over_graense")[["kommune_navn","pesticid_pct_over_graense","pesticid_ratio"]].to_string(index=False))
print(f"\nBedste kommuner (0% over grænseværdien):")
print(valid[valid["pesticid_pct_over_graense"]==0][["kommune_navn","pesticid_pct_over_graense"]].head(8).to_string(index=False))

thisted = result_df[result_df["kommune_navn"] == "Thisted"]
if not thisted.empty:
    t = thisted.iloc[0]
    print(f"\nThisted Kommune:")
    print(f"  {t['pesticid_pct_over_graense']}% af boringer over grænseværdien (ratio: {t['pesticid_ratio']})")

# ───────────────────────────────────────────────────────────────
# AUTO-REBUILD af master_indicators.csv
# ───────────────────────────────────────────────────────────────
try:
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_master_csv import auto_build_master
    auto_build_master()
except Exception as _e:
    print(f"\n⚠ Kunne ikke auto-rebuild master-CSV: {_e}")
    print("  Rådata er gemt. Kør manuelt: python3 scripts/build_master_csv.py")
