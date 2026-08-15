#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_trends_csv.py

Beregner en retningsklasse (pil) pr. kommune pr. indikator ud fra den
historiske tidsserie i data/trend_history_raw.csv (skrevet af
scripts/fetch_trend_history.py). Se "PLAN retningsvisning i doughnut-
platformen.md" afsnit 4 og 5 for den fulde begrundelse - kort resumé her:

- Retningen beregnes på RÅVÆRDIER, aldrig på ratio (ratio er relativ til en
  baseline der kan skifte - så ville pilen kunne pege forkert vej).
- Treårsgennemsnit i hver ende af serien (hvis mindst 6 år findes), så et
  enkelt ekstremår ikke afgør billedet.
- Ændringer under 1 procentpoint tælles ikke, når niveauet allerede er over
  10 procent (måleusikkerhed på små andele af et stort tal).
- Referencen for "rigtig" vs. "tempo" er medianen af ALLE 98 kommuners
  ændring i procent for samme indikator - ikke et fast mål.

Output: data/trend_indicators.csv, kommasepareret (samme konvention som
master_indicators.csv - se CLAUDE.md pitfall om split(",")-parsing).

VIGTIGT - `pct` betyder to forskellige ting, afhængigt af rækketype:

  Enkelt-indikator (fx "crime_rate")
      pct = råværdiens FAKTISKE ændring. Kriminalitet -30% betyder at
      antallet faldt 30%. Fortegnet siger hvad tallet gjorde, ikke om det
      var godt. UI'et lader pilen følge dette fortegn, så man kan se det
      nuancerede billede: affald ned og genanvendelse op er begge positivt,
      men de peger hver sin vej.

  Dimensions-/kategori-aggregat ("_dim_*")
      pct = MÅLRETTET ændring: fortegnet er vendt for inverse indikatorer,
      så POSITIV altid betyder positiv retning. Nødvendigt for at kunne
      gennemsnitte indikatorer der vil hver sin vej, og for at to
      dimensioner med samme vurdering ikke får pile der peger modsat.
      `vaerdi_start`/`vaerdi_slut` er tomme her - der er ingen fælles enhed.
      UI'et udleder pilens retning af `retning` + doughnut-geometrien
      (sociale kategorier: op = fremgang; økologiske: ned = fremgang),
      IKKE af dette fortegn.

Kør fra projektets rodmappe:
  python3 scripts/build_trends_csv.py

Driftsregel: kaldes automatisk af scripts/fetch_trend_history.py via
auto_build_trends(), ligesom fetch-scripts allerede kalder auto_build_master()
for master_indicators.csv. De to filer opdateres altid sammen.
"""

from __future__ import annotations

import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_INPUT = DATA_DIR / "trend_history_raw.csv"
MASTER_INPUT = DATA_DIR / "master_indicators.csv"
OUTPUT = DATA_DIR / "trend_indicators.csv"

# Dimensioner hvis score er et GENNEMSNIT af sub-indikatorerne i stedet for
# worst-of. SKAL matche AVERAGE_DIMENSIONS i build_master_csv.py, ellers vil
# pilen pege på noget andet end det tal den står ved siden af.
AVERAGE_DIMENSIONS = {"forurening"}

# ─── op_er_godt pr. indikator ────────────────────────────────────────────
# Kilde: INDICATORS[].inverse i webapp/lib/shared.ts (sociale) og den faste
# konvention "for økologiske indikatorer er lavere altid bedre" (CLAUDE.md),
# undtagen cirkularitet_recycling hvor højere genanvendelse er bedre.
# HOLD DENNE I SYNC med shared.ts, ligesom build_master_csv.py's egen
# indikator-liste allerede skal holdes i sync manuelt.
OP_ER_GODT = {
    # --- Sociale (fra shared.ts INDICATORS[].inverse) ---
    "hjemsyg": False, "medicin": False, "laegekontakt": True, "boerneovervaeght": False,
    "hospital_short": False, "class_size": False, "daycare_ratio": False,
    "educated_staff": True, "low_education": False, "education": True,
    "vulnerable_children": False, "child_notifications": False, "neet": False,
    "poverty_relative": False, "child_poverty": False, "gini": False,
    "housing_area": True, "vacant_housing": False, "voter_turnout_national": True,
    "music_school": True, "library_use": True, "traffic_accidents": False,
    "crime_rate": False, "sports_facilities": True, "sports_membership": True,
    "sports_spending": True, "gender_leadership": True, "income_gender_gap": True,
    "employment_origin_gap": True, "le_gender_gap": False, "life_expectancy": True,
    "employment": True, "disposable_income": True, "commute_distance": False,
    "hospital_long": False, "housing_no_wc": False, "housing_no_bath": False,
    "voter_turnout": True, "kultur_spending": True, "civil_society": True,
    "low_income": False, "exam_grade": True, "high_absence": False,
    "wellbeing": True, "youth_education": True,
    # --- Økologiske (lavere raw = bedre, undtagen genanvendelse) ---
    "naer_nitrogen": False, "naer_phosphorus": False, "vandindvinding": False,
    "areal_intensiv": False, "areal_bebygget": False, "klimapaavirkning": False,
    "cirkularitet_waste": False, "cirkularitet_recycling": True,
}

KILDE = {
    "klimapaavirkning": "Klimaregnskabet.dk",
}
KILDE_DEFAULT = "Danmarks Statistik"

N_ENDEPUNKT = 3  # antal år der gennemsnittes i hver ende, hvis serien er lang nok
MIN_AAR_FOR_GENNEMSNIT = 6


def endepunkter(serie: dict) -> tuple[str, str, float, float, int]:
    """serie er {år: værdi}. Returnerer (start_label, slut_label, start, slut, n_aar)."""
    aar = sorted(serie)
    n = len(aar)
    if n < MIN_AAR_FOR_GENNEMSNIT:
        return aar[0], aar[-1], serie[aar[0]], serie[aar[-1]], n
    f, s = aar[:N_ENDEPUNKT], aar[-N_ENDEPUNKT:]
    f_label = f"{f[0]}-{f[-1]}" if f[0] != f[-1] else f[0]
    s_label = f"{s[0]}-{s[-1]}" if s[0] != s[-1] else s[-1]
    return (f_label, s_label,
            sum(serie[a] for a in f) / len(f), sum(serie[a] for a in s) / len(s), n)


def ubetydelig(start: float, slut: float) -> bool:
    """Sandt hvis niveauet er over 10 og ændringen er under 1 (i indikatorens
    egen enhed - typisk procentpoint for andele). Se planens afsnit 4.3."""
    if start is None or slut is None:
        return False
    return abs(slut - start) < 1.0 and max(abs(start), abs(slut)) >= 10.0


def pct_aendring(start: float, slut: float) -> float | None:
    if start is None or start == 0:
        return None
    return (slut - start) / abs(start) * 100


def maalrettet(pct: float | None, op_er_godt: bool | None) -> float | None:
    """Vender fortegnet så POSITIV altid betyder 'bevæger sig mod målet',
    uanset om indikatoren ønskes op (middellevetid) eller ned (kriminalitet).
    Gør det muligt at sammenligne og gennemsnitte indikatorer med modsat retning."""
    if pct is None or op_er_godt is None:
        return None
    return pct if op_er_godt else -pct


def klassificer(pct: float | None, op_er_godt: bool | None, ref_pct: float | None,
                 er_ubetydelig: bool) -> str:
    if pct is None:
        return "ingen"
    if er_ubetydelig or abs(pct) < 1.0:
        return "stagneret"
    if op_er_godt is None:
        return "kontekst"
    # Sammenlign med FORTEGN på den målrettede skala, ikke på absolutte tal.
    # Med abs() ville en kommune der forbedrer sig 5%, mens landets median
    # forværres 8%, blive stemplet "tempo" (for langsom) - selvom den bevæger
    # sig den rigtige vej og de fleste andre den forkerte.
    m = maalrettet(pct, op_er_godt)
    m_ref = maalrettet(ref_pct, op_er_godt)
    if m <= 0:
        return "forkert"
    if m_ref is None or m >= m_ref:
        return "rigtig"
    return "tempo"


def laes_master_struktur():
    """Læser master_indicators.csv og returnerer to strukturer:

      eco: {kommune_kode: {dimension: [(indicator_id, ratio)]}}  - kun økologiske subs
      social: {dimension: [indicator_id]}                        - sociale kategorier

    eco har ratios med, fordi worst-of-reglen kræver at vi ved HVILKEN
    sub-indikator der bestemmer dimensionens score (den med højeste ratio).
    """
    eco = defaultdict(lambda: defaultdict(list))
    social = defaultdict(set)
    if not MASTER_INPUT.exists():
        print(f"  ADVARSEL: {MASTER_INPUT.name} mangler - springer dimensions-pile over.")
        return eco, social
    with open(MASTER_INPUT, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            iid, dim, kat = r["indicator_id"], r["dimension"], r["category"]
            if iid.startswith("_dim_") or not dim:
                continue
            if kat == "ecological":
                try:
                    ratio = float(r["ratio"])
                except (ValueError, TypeError):
                    continue
                eco[r["kommune_kode"]][dim].append((iid, ratio))
            elif kat == "social":
                social[dim].add(iid)
    return eco, {d: sorted(ids) for d, ids in social.items()}


def aggreger_dimensioner(poster, eco_struktur, social_struktur):
    """Beregner én retning pr. kommune pr. dimension/kategori.

    Økologiske dimensioner scores worst-of: den værste sub-indikator afgør
    tallet. Derfor SKAL pilen følge netop den sub-indikator - ikke et
    gennemsnit. Ellers kan dimensionen vise grøn pil, samtidig med at netop
    den grænse der er overskredet bliver værre. Undtagelsen er Forurening,
    som bruger gennemsnit i scoren og derfor også i retningen.

    Sociale kategorier er et simpelt gennemsnit, så gennemsnittet af
    sub-retningerne er konsistent med tallet.

    Har den afgørende sub-indikator ingen tidsserie, får dimensionen ingen
    retning. Vi falder bevidst IKKE tilbage på de øvrige - så ville pilen
    beskrive noget andet end det tal den står ved siden af.
    """
    # {(kommune, indicator_id): post} til hurtigt opslag
    per_indikator = {(p["kommune_kode"], p["indicator_id"]): p for p in poster}
    ud = []

    # ─── Økologiske dimensioner ──────────────────────────────────────
    # Saml først målrettet pct pr. kommune, så gruppemedianen kan beregnes.
    eco_kandidater = defaultdict(dict)   # {dimension: {kommune: dict}}
    for kode, dims in eco_struktur.items():
        for dim, subs in dims.items():
            if dim in AVERAGE_DIMENSIONS:
                # Gennemsnit af sub-indikatorernes målrettede ændring.
                # Økologiske indikatorer vil ned, undtagen genanvendelse.
                maal = []
                perioder = []
                for iid, _ratio in subs:
                    p = per_indikator.get((kode, iid))
                    if not p or p["pct"] == "":
                        continue
                    m = maalrettet(float(p["pct"]), OP_ER_GODT.get(iid))
                    if m is not None:
                        maal.append(m)
                        perioder.append((p["periode_start"], p["periode_slut"], p["n_aar"]))
                if not maal:
                    continue
                eco_kandidater[dim][kode] = {
                    "maalrettet": sum(maal) / len(maal),
                    "periode_start": min(p[0] for p in perioder),
                    "periode_slut": max(p[1] for p in perioder),
                    "n_aar": max(p[2] for p in perioder),
                    "noegle": f"gennemsnit af {len(maal)} indikatorer",
                }
            else:
                # Worst-of: den sub-indikator med HØJESTE ratio bestemmer scoren.
                afgorende_id, _ = max(subs, key=lambda s: s[1])
                p = per_indikator.get((kode, afgorende_id))
                if not p or p["pct"] == "":
                    continue  # ingen tidsserie for den afgørende → ingen pil
                # VIGTIGT: pct målrettes også her, så ALLE _dim_*-rækker har
                # samme betydning (positiv = positiv retning). Uden det ville
                # worst-of-dimensioner bære råværdiens fortegn, mens
                # gennemsnits-dimensioner bar det målrettede - og så ville to
                # dimensioner med samme vurdering kunne få pile der peger
                # modsat. Se skema-noten øverst i filen.
                m = maalrettet(float(p["pct"]), OP_ER_GODT.get(afgorende_id))
                if m is None:
                    continue
                ud.append({
                    **p,
                    "indicator_id": f"_dim_{dim}",
                    "pct": round(m, 2),
                    "vaerdi_start": "",   # ingen fælles enhed på dimensionsniveau
                    "vaerdi_slut": "",
                    "noegle_indikator": afgorende_id,
                })

    # Klassificér gennemsnits-dimensionerne mod deres egen gruppemedian.
    for dim, per_kommune in eco_kandidater.items():
        ref = statistics.median(v["maalrettet"] for v in per_kommune.values())
        for kode, v in per_kommune.items():
            m = v["maalrettet"]
            # maalrettet er allerede vendt så positiv = mod målet, derfor
            # klassificeres med op_er_godt=True.
            ud.append({
                "kommune_kode": kode,
                "indicator_id": f"_dim_{dim}",
                "periode_start": v["periode_start"],
                "periode_slut": v["periode_slut"],
                "vaerdi_start": "",
                "vaerdi_slut": "",
                "pct": round(m, 2),
                "retning": klassificer(m, True, ref, False),
                "n_aar": v["n_aar"],
                "kilde": KILDE_DEFAULT,
                "noegle_indikator": v["noegle"],
            })

    # ─── Sociale kategorier (simpelt gennemsnit, som scoren) ─────────
    social_kandidater = defaultdict(dict)
    kommuner = {p["kommune_kode"] for p in poster}
    for dim, ids in social_struktur.items():
        for kode in kommuner:
            maal, perioder = [], []
            for iid in ids:
                p = per_indikator.get((kode, iid))
                if not p or p["pct"] == "":
                    continue
                m = maalrettet(float(p["pct"]), OP_ER_GODT.get(iid))
                if m is not None:
                    maal.append(m)
                    perioder.append((p["periode_start"], p["periode_slut"], p["n_aar"]))
            if not maal:
                continue
            social_kandidater[dim][kode] = {
                "maalrettet": sum(maal) / len(maal),
                "periode_start": min(p[0] for p in perioder),
                "periode_slut": max(p[1] for p in perioder),
                "n_aar": max(p[2] for p in perioder),
                "antal": len(maal),
            }

    for dim, per_kommune in social_kandidater.items():
        ref = statistics.median(v["maalrettet"] for v in per_kommune.values())
        for kode, v in per_kommune.items():
            m = v["maalrettet"]
            ud.append({
                "kommune_kode": kode,
                "indicator_id": f"_dim_{dim}",
                "periode_start": v["periode_start"],
                "periode_slut": v["periode_slut"],
                "vaerdi_start": "",
                "vaerdi_slut": "",
                "pct": round(m, 2),
                "retning": klassificer(m, True, ref, False),
                "n_aar": v["n_aar"],
                "kilde": KILDE_DEFAULT,
                "noegle_indikator": f"gennemsnit af {v['antal']} indikatorer",
            })

    return ud


def build_trends():
    if not RAW_INPUT.exists():
        print(f"FEJL: {RAW_INPUT} findes ikke. Kør scripts/fetch_trend_history.py først.",
              file=sys.stderr)
        sys.exit(1)

    # {indicator_id: {kommune_kode: {aar: vaerdi}}}
    per_indikator: dict[str, dict[str, dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
    with open(RAW_INPUT, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            iid, kode, aar = r["indicator_id"], r["kommune_kode"], r["aar"]
            try:
                v = float(r["vaerdi"])
            except (ValueError, TypeError):
                continue
            per_indikator[iid][kode][aar] = v

    print(f"Læste {len(per_indikator)} indikatorer fra {RAW_INPUT.name}")

    output_rows = []
    for iid, per_kommune in sorted(per_indikator.items()):
        op_er_godt = OP_ER_GODT.get(iid)
        if iid not in OP_ER_GODT:
            print(f"  ADVARSEL: {iid} har ingen op_er_godt-mapping - klassificeres som kontekst.")

        # Beregn endepunkter og pct-ændring for alle kommuner med mindst 2 år,
        # så gruppemedianen (referencen) kan beregnes på tværs af alle 98.
        pr_kommune_pct: dict[str, float] = {}
        pr_kommune_data: dict[str, tuple] = {}
        for kode, serie in per_kommune.items():
            if len(serie) < 2:
                continue
            f_lab, s_lab, start, slut, n_aar = endepunkter(serie)
            pct = pct_aendring(start, slut)
            pr_kommune_data[kode] = (f_lab, s_lab, start, slut, n_aar, pct)
            if pct is not None:
                pr_kommune_pct[kode] = pct

        if not pr_kommune_pct:
            continue
        ref_pct = statistics.median(pr_kommune_pct.values())

        n_rigtig = n_tempo = n_stagneret = n_forkert = 0
        for kode, (f_lab, s_lab, start, slut, n_aar, pct) in pr_kommune_data.items():
            er_ubetydelig = ubetydelig(start, slut)
            retning = klassificer(pct, op_er_godt, ref_pct, er_ubetydelig)
            if retning == "rigtig":
                n_rigtig += 1
            elif retning == "tempo":
                n_tempo += 1
            elif retning == "stagneret":
                n_stagneret += 1
            elif retning == "forkert":
                n_forkert += 1
            output_rows.append({
                "kommune_kode": kode,
                "indicator_id": iid,
                "periode_start": f_lab,
                "periode_slut": s_lab,
                "vaerdi_start": round(start, 4),
                "vaerdi_slut": round(slut, 4),
                "pct": round(pct, 2) if pct is not None else "",
                "retning": retning,
                "n_aar": n_aar,
                "kilde": KILDE.get(iid, KILDE_DEFAULT),
                "noegle_indikator": "",
            })

        print(f"  {iid:28} {len(pr_kommune_data):3}/98 kommuner  "
              f"(rigtig={n_rigtig} tempo={n_tempo} stagneret={n_stagneret} forkert={n_forkert})  "
              f"ref={ref_pct:+.1f}%")

    # ─── Dimensions- og kategori-aggregater (_dim_*) ─────────────────
    print()
    print("Dimensions-aggregater:")
    eco_struktur, social_struktur = laes_master_struktur()
    dim_rows = aggreger_dimensioner(output_rows, eco_struktur, social_struktur)
    pr_dim = defaultdict(list)
    for r in dim_rows:
        pr_dim[r["indicator_id"]].append(r["retning"])
    for dim_id in sorted(pr_dim):
        retninger = pr_dim[dim_id]
        t = {k: retninger.count(k) for k in ("rigtig", "tempo", "stagneret", "forkert")}
        metode = "gennemsnit" if (dim_id[5:] in AVERAGE_DIMENSIONS
                                   or dim_id[5:] in social_struktur) else "worst-of"
        print(f"  {dim_id:28} {len(retninger):3}/98 kommuner  "
              f"(rigtig={t['rigtig']} tempo={t['tempo']} stagneret={t['stagneret']} "
              f"forkert={t['forkert']})  [{metode}]")
    output_rows.extend(dim_rows)

    DATA_DIR.mkdir(exist_ok=True)
    fieldnames = ["kommune_kode", "indicator_id", "periode_start", "periode_slut",
                  "vaerdi_start", "vaerdi_slut", "pct", "retning", "n_aar", "kilde",
                  "noegle_indikator"]
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(sorted(output_rows, key=lambda r: (r["indicator_id"], r["kommune_kode"])))

    print(f"\n✓ Skrev {len(output_rows)} rækker til {OUTPUT.relative_to(ROOT)}")
    print(f"  Filstørrelse: {OUTPUT.stat().st_size / 1024:.1f} KB")


def auto_build_trends():
    """Kaldes fra fetch_trend_history.py efter en ny hentning, ligesom
    auto_build_master() kaldes fra de øvrige fetch-scripts."""
    print()
    print("=" * 55)
    print("AUTO-REBUILD af trend_indicators.csv")
    print("=" * 55)
    try:
        build_trends()
        print()
        print("✓ Trend-CSV opdateret. Klar til commit + push via GitHub Desktop.")
    except Exception as e:
        print()
        print(f"✗ FEJL ved rebuild af trend-CSV: {e}")
        print("  Kør manuelt: python3 scripts/build_trends_csv.py")


if __name__ == "__main__":
    build_trends()
