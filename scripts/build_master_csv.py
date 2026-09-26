"""
build_master_csv.py - Konsolider alle rådata-CSV'er til én master-fil i long format.

Kører efter alle fetch-scripts. Producerer data/master_indicators.csv som
webapp'en læser fra. Long format gør filen forsker-venlig (tidy data) og
fjerner behovet for 25+ separate CSV-loads i webapp/lib/data.ts.

Output-skema (én række pr. kommune × indikator):
  kommune_kode, kommune_navn, indicator_id, ratio, raw_value,
  unit, data_year, source, category, dimension, reference

Alle ratios beregnes her ud fra råværdien og indikatorens reference i
data/indikatorer.json (se "RATIO: ÉN FORMEL" nedenfor). reference er den
værdi ratio er målt mod: målet, kommunegennemsnittet eller landstallet.

Kør:
  cd /sti/til/doughnut
  python3 scripts/build_master_csv.py

Driftsregel:
  1. Kør fetch-script(s) for de indikatorer du vil opdatere
  2. Kør DETTE script - opdaterer data/master_indicators.csv
  3. Commit + push via GitHub Desktop
"""

import re
import csv
import json
import math
import os
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dst_aar import hentede_aar  # noqa: E402

# ─── data_year: kilden har forrang over den hårdkodede værdi ──────────────
# Fetch-scripterne registrerer i data/data_years.json hvilket år de FAKTISK
# hentede en DST-tabel på. Vi bruger det frem for "data_year" i tabellen
# nedenfor, fordi de to ellers driver fra hinanden: aug. 2026 mærkede
# masteren 2024-tal som 2022 for fire indikatorer, og 2019-tal som 2023 for
# education. Hårdkodet data_year bruges nu kun som fallback for kilder der
# ikke er DST-tabeller (Klimaregnskabet, VP3, manuelle filer).
_HENTEDE_AAR = hentede_aar()


def _data_year(ind: dict) -> str:
    """Årstal for indikatoren: registreret hentning > registrets data_year.

    data_years.json gemmer kun slutåret (dst_aar._aarstal). For indikatorer
    der dækker en periode (period_years i registret: HISBK's femårige
    intervaller, trafikulykkernes treårige gennemsnit) skrives perioden ud,
    så UI'et viser "2021-2025" og ikke et enkelt år tallet ikke dækker.
    """
    aar = ind.get("data_year", "")
    kilde = ind.get("source") or ""
    m = re.match(r"DST\s+([A-ZÆØÅ0-9_]+)", kilde)
    if m and _HENTEDE_AAR.get(m.group(1)):
        aar = _HENTEDE_AAR[m.group(1)]
    elif _HENTEDE_AAR.get(ind.get("table") or ""):
        # Ikke-DST-kilder der registrerer året under registrets table-navn,
        # fx UVM's "GS/TRIV/TRIVIND" (fetch_udvidelse_data.py).
        aar = _HENTEDE_AAR[ind["table"]]
    n = ind.get("period_years")
    if n and re.fullmatch(r"\d{4}", aar):
        aar = f"{int(aar) - n + 1}-{aar}"
    return aar


# ─── Stier ─────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUT = DATA_DIR / "master_indicators.csv"
NOEGLETAL = DATA_DIR / "noegletal.json"

# ─── INDIKATORER ───────────────────────────────────────────────────────
# Kommer fra data/indikatorer.json via scripts/indikatorregister.py. Det er
# den ENESTE liste der skal opdateres når en indikator tilføjes eller fjernes;
# webappen (shared.ts, data.ts) og build_trends_csv.py læser samme fil.
# Felterne build_master bruger: id, csv, raw_col, reference, inverse/
# lower_is_better, formula, cap, ratio_col(_invers), unit, data_year,
# period_years, source, category og dimension (se registrets "_om").
import indikatorregister as ir  # noqa: E402


# ─── HJÆLPEFUNKTIONER ──────────────────────────────────────────────────

def load_csv(filename):
    """Læs CSV til dict mapped på kommune_kode (eller første kolonne)."""
    path = DATA_DIR / filename
    if not path.exists():
        print(f"  ⚠ CSV mangler: {filename}", file=sys.stderr)
        return []
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_float(s):
    """Returnerer float eller None hvis tom/invalid."""
    if s is None or s == "":
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


# ─── RATIO: ÉN FORMEL FOR ALLE INDIKATORER ─────────────────────────────
# Indtil sep. 2026 regnede hvert fetch-script sin egen ratio, med sin egen
# regel for værdien 0 (fem scripts gav topscore 150, ét gav 0), og
# build_master havde tre særregler oveni (10000/x for inverterede
# øko-ratios, 65/pct for genanvendelse, raw/3 for forbrugs-CO2). Nu regnes
# alle ratios her, ud fra råværdien og indikatorens reference i registret.
# Fetch-scriptets egen ratio bruges kun til krydstjek og til at
# rekonstruere landstallet, hvis CSV'en endnu ikke har en landstal-kolonne.

SOCIAL_CAP = 150.0


def _loft(ind):
    """Indikatorens loft for ratio. Sociale: 150 (R1), eller lavere hvis
    registret sætter 'cap' (kystrisiko: 100, så ingen risiko er neutral og
    ikke en fordel). Økologiske: 'cap' hvis sat (R6), ellers intet loft."""
    if ind["category"] == "social":
        return min(float(ind.get("cap", SOCIAL_CAP)), SOCIAL_CAP)
    return ind.get("cap")


def _raw_over_ref(ind):
    """True: ratio = raw/ref×100. False: ratio = ref/raw×100.

    Sociale: højere ratio er bedre, så inverse indikatorer (lavere råværdi
    er bedre) vendes. Økologiske: højere ratio er værre, så indikatorer hvor
    lavere råværdi er bedre, skal IKKE vendes."""
    if ind["category"] == "social":
        return not ind["inverse"]
    return ind["lower_is_better"]


def beregn_ratio(ind, raw, ref):
    """Indikatorens ratio for én kommune, afrundet til 2 decimaler.

    raw = 0 i nævneren (ref/raw) er grænsetilfældet: for en social indikator
    er det bedst mulige (fx ingen kriminalitet) og giver loftet 150; for en
    økologisk er det værst mulige (fx ingen natur) og giver 'cap', eller
    ingen værdi hvis indikatoren ikke har et loft."""
    if raw is None:
        return None
    if ind.get("formula") == "100_minus_raw":
        x = 100 - raw
    elif ind.get("formula") == "komplement":
        # Økologisk andel hvor højere er bedre (natur, genanvendelse, vand i god
        # tilstand). Målet "mindst ref %" er det samme som loftet "højst
        # 100 - ref % uden", og ratioen er den manglende andel målt mod loftet
        # (R2a). Så har alle økologiske ratios nul ved ingen belastning, og en
        # andel nær 0 giver ikke længere ratios i tusindvis.
        if ref is None or ref >= 100:
            return None
        x = (100 - raw) / (100 - ref) * 100
    else:
        if not ref:
            return None
        if _raw_over_ref(ind):
            x = raw / ref * 100
        elif raw == 0:
            x = math.inf
        else:
            x = ref / raw * 100
    cap = _loft(ind)
    if cap is not None and x > cap:
        x = float(cap)
    if math.isinf(x):
        return None
    return round(x, 2)


def _script_ratio(ind, r):
    """Fetch-scriptets egen ratio for en CSV-række (til krydstjek/rekonstruktion)."""
    col = ind.get("ratio_col")
    if not col or r is None:
        return None
    v = parse_float(r.get(col))
    if v is not None and ind.get("ratio_col_invers"):
        v = round(10000 / v, 2) if v else None
    return v


def _rekonstruer_landstal(ind, raekker, raws):
    """Landstallet fetch-scriptet brugte, udledt af dets egen ratio.

    Overgangsløsning, indtil scriptet skriver landstallet i sin egen kolonne
    (reference.col). Hver kommune giver et bud (raw×100/ratio eller
    raw×ratio/100); medianen er robust over for afrunding. Derefter vælges
    den kortest afrundede værdi der reproducerer mindst lige så mange af
    scriptets ratios som medianen - landstal som 81,6 år er typisk
    publiceret med få decimaler, og så genskabes de eksakt. Klippede ratios
    (150/cap) udelades, fordi de ikke siger noget om referencen.
    Beregnes ved hvert build fra den aktuelle CSV, så værdien aldrig er
    ældre end dataen."""
    cap = _loft(ind)
    par = []
    for kode, r in raekker.items():
        raw, sr = raws.get(kode), _script_ratio(ind, r)
        if raw in (None, 0) or not sr or (cap is not None and sr >= cap):
            continue
        par.append((raw, sr))
    if not par:
        return None
    if ind.get("formula") == "komplement":
        # ratio = (100 - raw) / (100 - ref) × 100  →  ref = 100 - (100 - raw) × 100 / ratio
        bud = [100 - (100 - raw) * 100 / sr for raw, sr in par if raw < 100]
        if not bud:
            return None
    else:
        bud = [raw * 100 / sr if _raw_over_ref(ind) else raw * sr / 100 for raw, sr in par]
    median = statistics.median(bud)

    def traeffere(ref):
        return sum(1 for raw, sr in par if beregn_ratio(ind, raw, ref) == round(sr, 2))

    bedst, bedst_n = median, traeffere(median)
    for d in range(0, 7):
        kandidat = round(median, d)
        n = traeffere(kandidat)
        if n >= bedst_n:
            return kandidat
    return bedst


def _csv_raekker(ind, kommuner, get_csv):
    """{kommune_kode: CSV-række eller None} for platformens kommuner."""
    rows = get_csv(ind["csv"])
    # Alle kilde-CSV'er er nøglet på kommune_kode. De to kilder der kun har
    # navne (forbrug_co2, vejr_skader) fik koden tilføjet sep. 2026 ud fra
    # data/kommuner.json, så en stavevariant ikke længere giver et tavst hul.
    by_kode = {}
    for r in rows:
        kode = r.get("kommune_kode")
        if kode and kode not in by_kode:
            by_kode[kode] = r
    return {kode: by_kode.get(kode) for kode, _ in kommuner}


def beregn_indikator(ind, kommuner, get_csv):
    """Råværdi, ratio og reference for én indikator i alle kommuner.

    Returnerer (poster, reference, kilde) hvor poster er
    [(kode, navn, raw, ratio)] for kommuner med data."""
    raekker = _csv_raekker(ind, kommuner, get_csv)
    raws = {kode: parse_float(r.get(ind["raw_col"])) if r else None
            for kode, r in raekker.items()}

    spec = ind["reference"]
    if spec["type"] == "maal":
        ref, kilde = float(spec["value"]), "mål"
    elif spec["type"] == "kommunegennemsnit":
        vals = [v for v in raws.values() if v is not None]
        ref, kilde = (sum(vals) / len(vals) if vals else None), "kommunegennemsnit"
    else:
        vals = {parse_float(r.get(spec["col"])) for r in raekker.values() if r} - {None}
        if vals:
            if max(vals) - min(vals) > 1e-9:
                print(f"  ⚠ {ind['id']}: {spec['col']} har forskellige værdier i CSV'en - bruger medianen")
            ref, kilde = statistics.median(sorted(vals)), "landstal"
        else:
            ref, kilde = _rekonstruer_landstal(ind, raekker, raws), "landstal, rekonstrueret"

    navne = dict(kommuner)
    cap = _loft(ind)
    poster = []
    afvigelser = []
    for kode, _ in kommuner:
        raw = raws.get(kode)
        ratio = beregn_ratio(ind, raw, ref)
        if ratio is None and raw is None:
            continue
        poster.append((kode, navne[kode], raw, ratio))
        # Krydstjek mod scriptets egen ratio. Scripterne klipper ikke selv ved
        # 150, så loftet lægges på her før sammenligningen.
        sr = _script_ratio(ind, raekker.get(kode))
        if sr is not None and cap is not None:
            sr = min(sr, float(cap))
        if sr is not None and ratio is not None and abs(sr - ratio) > 0.5:
            afvigelser.append(abs(sr - ratio))
    if afvigelser:
        print(f"  ⚠ {ind['id']}: {len(afvigelser)} kommuner afviger mere end 0,5 fra fetch-scriptets "
              f"egen ratio (max {max(afvigelser):.2f}) - tjek retning og reference")
    return poster, ref, kilde


def worst_of(ratios):
    """Worst-of (max) for ikke-None værdier. Planetary boundary-logik."""
    valid = [r for r in ratios if r is not None]
    return round(max(valid), 2) if valid else None


def average_of(ratios):
    """Gennemsnit for ikke-None værdier. Bruges for forurening-dimensionen."""
    valid = [r for r in ratios if r is not None]
    return round(sum(valid) / len(valid), 2) if valid else None


# ─── HOVEDLOGIK ────────────────────────────────────────────────────────

def build_master():
    print(f"Læser fra {DATA_DIR}")
    print()

    SOCIAL_INDICATORS = ir.sociale()
    ECO_SUB_INDICATORS = ir.oekologiske()
    CONTEXT_INDICATORS = ir.kontekst()
    # Dimensioner der bruger gennemsnit i stedet for worst-of (i dag kun forurening)
    AVERAGE_DIMENSIONS = ir.gennemsnits_dimensioner()

    # Få liste af alle 98 kommuner fra hoved-CSV
    main_rows = load_csv("doughnut_scores.csv")
    if not main_rows:
        print("FEJL: doughnut_scores.csv mangler eller er tom", file=sys.stderr)
        sys.exit(1)

    kommuner = [(r["kommune_kode"], r.get("kommune_navn", "")) for r in main_rows]
    print(f"Fundet {len(kommuner)} kommuner")

    # Platformens kommuner er de 98 i data/kommuner.json. doughnut_scores.csv
    # bestemmer kun rækkefølgen i master. Mangler en kommune her, ville den
    # ellers forsvinde fra sitet uden fejl. Importeres først her, så en fejl i
    # JSON-filen ikke vælter auto_build_master-importen (samme princip som registret).
    from kommuner import KOMMUNER
    afvigelser = sorted(set(kommuner) ^ set(KOMMUNER.items()))
    if afvigelser or len(kommuner) != len(KOMMUNER):
        print(f"FEJL: kommunerne i doughnut_scores.csv passer ikke med data/kommuner.json: "
              f"{afvigelser or 'dubletter'}", file=sys.stderr)
        sys.exit(1)
    print()

    # Cache CSV-loads (undgå at læse samme fil 5 gange)
    csv_cache = {}
    def get_csv(filename):
        if filename not in csv_cache:
            csv_cache[filename] = load_csv(filename)
        return csv_cache[filename]

    # Output-rækker
    output_rows = []

    # Tæller for diagnostik
    indicator_coverage = {}

    def skriv(ind, poster, ref):
        for kode, navn, raw, ratio in poster:
            output_rows.append({
                "kommune_kode": kode,
                "kommune_navn": navn,
                "indicator_id": ind["id"],
                "ratio": ratio if ratio is not None else "",
                "raw_value": raw if raw is not None else "",
                "unit": ind["unit"],
                "data_year": _data_year(ind),
                "source": ind["source"],
                "category": ind["category"],
                "dimension": ind["dimension"],
                "reference": round(ref, 6) if ref is not None else "",
            })

    # ─── Sociale indikatorer ────────────────────────────────────
    print("Sociale indikatorer:")
    for ind in SOCIAL_INDICATORS:
        poster, ref, kilde = beregn_indikator(ind, kommuner, get_csv)
        skriv(ind, poster, ref)
        indicator_coverage[ind["id"]] = len(poster)
        print(f"  {ind['id']:25s}: {len(poster)}/98 kommuner  ref={ref if ref is None else f'{ref:.6g}'} ({kilde})")

    # ─── Økologiske sub-indikatorer ──────────────────────────────
    print()
    print("Økologiske sub-indikatorer:")
    # Saml sub-ratios pr. dimension for at beregne worst-of dimension-scores
    eco_sub_ratios = {}  # {kommune_kode: {dimension: [ratios]}}
    for ind in ECO_SUB_INDICATORS:
        poster, ref, kilde = beregn_indikator(ind, kommuner, get_csv)
        skriv(ind, poster, ref)
        for kode, _, _, ratio in poster:
            if ratio is not None:
                eco_sub_ratios.setdefault(kode, {}).setdefault(ind["dimension"], []).append(ratio)
        indicator_coverage[ind["id"]] = len(poster)
        print(f"  {ind['id']:25s}: {len(poster)}/98 kommuner  ref={ref if ref is None else f'{ref:.6g}'} ({kilde})")

    # ─── Kontekst-indikatorer (råværdier, ingen score) ───────────
    print()
    print("Kontekst-indikatorer (vises, scores ikke):")
    for ind in CONTEXT_INDICATORS:
        rows = get_csv(ind["csv"])
        by_kode = {}
        for r in rows:
            kode = r.get("kommune_kode")
            if kode and kode not in by_kode:
                by_kode[kode] = r
        n = 0
        for kode, navn in kommuner:
            r = by_kode.get(kode)
            if r is None:
                continue
            raw = parse_float(r.get(ind["raw_col"]))
            if raw is None:
                continue
            output_rows.append({
                "kommune_kode": kode,
                "kommune_navn": navn,
                "indicator_id": ind["id"],
                "ratio": "",
                "raw_value": raw,
                "unit": ind["unit"],
                "data_year": _data_year(ind),
                "source": ind["source"],
                "category": "context",
                "dimension": ind["dimension"],
                "reference": "",
            })
            n += 1
        indicator_coverage[ind["id"]] = n
        print(f"  {ind['id']:25s}: {n}/98 kommuner")

    # ─── Worst-of dimension-aggregater ───────────────────────────
    # Skriv én række pr. (kommune, dimension) med dimension-score = worst-of
    # Bruges af webapp som eco_ratios[dimension].
    # Single-indicator dims (klimapaavirkning, biodiversitet, forbrug_co2) får dimension-score
    # = sub-indikatorens ratio. Multi-indicator dims (luftkvalitet, naeringsstoffer, cirkularitet)
    # får worst-of.
    print()
    print("Dimension-aggregater (worst-of):")
    dim_count = 0
    for kode, navn in kommuner:
        dims_for_kommune = eco_sub_ratios.get(kode, {})
        for dim, ratios in dims_for_kommune.items():
            score = average_of(ratios) if dim in AVERAGE_DIMENSIONS else worst_of(ratios)
            if score is None:
                continue
            output_rows.append({
                "kommune_kode": kode,
                "kommune_navn": navn,
                "indicator_id": f"_dim_{dim}",
                "ratio": score,
                "raw_value": "",
                "unit": "",
                "data_year": "",
                "source": "",
                "category": "ecological_dimension",
                "dimension": dim,
                "reference": "",
            })
            dim_count += 1
    print(f"  {dim_count} dimension-aggregat-rækker")

    # ─── Validering ──────────────────────────────────────────────
    print()
    print("Validering:")
    bad_ratios = [r for r in output_rows if r["ratio"] != "" and (float(r["ratio"]) < 0 or float(r["ratio"]) > 2000)]
    if bad_ratios:
        print(f"  ⚠ {len(bad_ratios)} ratio-værdier uden for forventet interval (0-2000)")
        for r in bad_ratios[:5]:
            print(f"     {r['kommune_navn']} / {r['indicator_id']}: ratio={r['ratio']}")
    else:
        print("  ✓ Alle ratios inden for forventet interval")

    # Webappen parser master med split(","). Et komma i et felt forskyder
    # kolonnerne, og rækken forsvinder tavst fra siden - derfor en hård fejl.
    med_komma = [(r["indicator_id"], k, v) for r in output_rows for k, v in r.items()
                 if isinstance(v, str) and "," in v]
    if med_komma:
        raise ValueError(f"{len(med_komma)} felter indeholder komma, som webappens CSV-parser ikke "
                         f"kan håndtere, fx {med_komma[0]}")

    kommuner_med_data = len({r["kommune_kode"] for r in output_rows})
    print(f"  Kommuner med mindst én indikator: {kommuner_med_data}/{len(kommuner)}")

    # ─── Skriv output ────────────────────────────────────────────
    # reference er tilføjet sidst (sep. 2026), så eksisterende læsere der
    # bruger kolonneposition, ikke påvirkes.
    fieldnames = ["kommune_kode", "kommune_navn", "indicator_id", "ratio",
                  "raw_value", "unit", "data_year", "source", "category", "dimension",
                  "reference"]
    with open(OUTPUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(output_rows)

    print()
    print(f"✓ Skrev {len(output_rows)} rækker til {OUTPUT.relative_to(ROOT)}")
    print(f"  Filstørrelse: {OUTPUT.stat().st_size / 1024:.1f} KB")
    _skriv_noegletal(output_rows, len(kommuner))


FAA_TILFAELDE = 20  # NCHS: under 20 hændelser giver en relativ standardfejl på mindst 23 %


def _faa_tilfaelde(output_rows):
    """{indikator: [kommunekoder]} hvor tallet bygger på under FAA_TILFAELDE
    tilfælde. Antallet regnes tilbage fra raten med folketallet i
    data/folketal.csv (fetch_folketal.py): råværdi × folketal / pr × aar.
    Ændrer ikke scoren; kommunesiden viser et mærke (arkitekturdokumentet R16).
    Mangler folketalsfilen, markeres intet, og der advares."""
    reg = {i["id"]: i for i in ir.register()["indikatorer"] if i.get("smaa_tal")}
    if not reg:
        return {}
    sti = DATA_DIR / "folketal.csv"
    if not sti.exists():
        print("  ADVARSEL: data/folketal.csv mangler - ingen 'få tilfælde'-markering. "
              "Kør python3 scripts/fetch_folketal.py")
        return {}
    with open(sti, newline="", encoding="utf-8") as f:
        folk = {r["kommune_kode"]: float(r["folketal"]) for r in csv.DictReader(f)}
    ud = {}
    for r in output_rows:
        ind = reg.get(r["indicator_id"])
        if not ind or r["raw_value"] == "" or r["kommune_kode"] not in folk:
            continue
        st = ind["smaa_tal"]
        antal = float(r["raw_value"]) * folk[r["kommune_kode"]] / st["pr"] * st["aar"]
        if antal < FAA_TILFAELDE:
            ud.setdefault(r["indicator_id"], []).append(r["kommune_kode"])
    for iid, koder in ud.items():
        print(f"  Få tilfælde (under {FAA_TILFAELDE}): {iid} i {len(koder)} kommuner")
    return ud


def _skriv_noegletal(output_rows, antal_kommuner):
    """data/noegletal.json: reference, dækning og dataår pr. indikator.

    Metodesiden og registrets tekster henviser til tal som landstallet for
    pesticider eller antal kommuner med tilskuertal. De stod før som
    håndskrevne tal i teksten og drev ved hver dataopdatering. Nu skriver
    teksterne en pladsholder ({ref:pesticider:1}, {mangler:sport_tilskuer}),
    og webappen udfylder den herfra (udfyldTal() i webapp/lib/shared.ts).
    Filen skrives sammen med master og skal committes sammen med den;
    webappen stopper buildet hvis de to ikke passer sammen."""
    pr_ind = {}
    for r in output_rows:
        iid = r["indicator_id"]
        if iid.startswith("_dim_"):
            continue
        d = pr_ind.setdefault(iid, {"reference": None, "daekning": 0, "data_year": r["data_year"]})
        if r["reference"] != "":
            d["reference"] = r["reference"]
        if r["ratio"] != "" or (r["category"] == "context" and r["raw_value"] != ""):
            d["daekning"] += 1
    for iid, koder in _faa_tilfaelde(output_rows).items():
        pr_ind[iid]["faa_tilfaelde"] = koder
    ud = {
        "_om": "Genereres af scripts/build_master_csv.py sammen med master_indicators.csv. "
               "Ret den ikke i hånden. daekning = antal kommuner med en værdi. "
               "faa_tilfaelde = kommuner hvor tallet bygger på under 20 tilfælde (registrets smaa_tal).",
        "kommuner": antal_kommuner,
        "indikatorer": pr_ind,
    }
    # Én linje pr. indikator, så en dataopdatering giver en læsbar diff.
    linjer = [f' "_om": {json.dumps(ud["_om"], ensure_ascii=False)},',
              f' "kommuner": {antal_kommuner},',
              ' "indikatorer": {']
    poster = [f'  {json.dumps(iid)}: {json.dumps(d, ensure_ascii=False)}' for iid, d in pr_ind.items()]
    linjer.append(",\n".join(poster))
    linjer.append(" }")
    with open(NOEGLETAL, "w", encoding="utf-8") as f:
        f.write("{\n" + "\n".join(linjer) + "\n}\n")
    print(f"✓ Skrev {NOEGLETAL.relative_to(ROOT)} ({len(pr_ind)} indikatorer)")


def _tjek_konsistens_efter_build():
    """
    Kører scripts/tjek_konsistens.py efter en vellykket build og printer
    resultatet. Isoleret i egen funktion så en fejl i selve tjekket (fx en
    fremtidig omskrivning af shared.ts som regex'en ikke kan følge) aldrig
    kan vælte en build der ellers lykkedes.

    Lazy import (ikke i toppen af filen): fetch-scripts importerer
    auto_build_master fra dette modul, og en fejl i tjek-modulet må ikke
    vælte selve hentningen ved import.

    Returnerer True (ingen fejl), False (fejl fundet) eller None (tjekket
    kunne ikke køre). None er IKKE det samme som bestået: et tjek der
    crasher er præcis den tavse fejl CLAUDE.md pkt. 19 advarer imod.
    """
    try:
        from tjek_konsistens import main as tjek_main
        print()
        print("=" * 55)
        print("KONSISTENSTJEK (scripts/tjek_konsistens.py)")
        print("=" * 55)
        return tjek_main() == 0
    except Exception as e:
        print()
        print(f"  ✗ KONSISTENSTJEKKET KUNNE IKKE KØRE: {type(e).__name__}: {e}")
        print("    Det tæller IKKE som bestået. Kør: python3 scripts/tjek_konsistens.py")
        return None


def _rapport_efter_build():
    """Kort rapport over hvad buildet ændrede i forhold til den committede
    master (scripts/rapport_dataaendringer.py). Ren information: en fejl
    her må aldrig vælte et build der ellers lykkedes."""
    try:
        from rapport_dataaendringer import main as rapport_main
        print()
        print("=" * 55)
        print("DATAÆNDRINGER (scripts/rapport_dataaendringer.py)")
        print("=" * 55)
        rapport_main([], kort=True)
    except Exception as e:
        print(f"  (rapporten over dataændringer kunne ikke køre: {type(e).__name__}: {e})")


def auto_build_master():
    """
    Helper-funktion til auto-rebuild fra fetch-scripts.

    Kaldes til sidst i alle fetch_*.py-scripts så master-CSV'en altid
    er opdateret efter en fetch. Isolerer fejl så build-problemer ikke
    crash'er det kaldende fetch-script (rådata er allerede gemt).

    Brug i fetch-scripts:
        from build_master_csv import auto_build_master
        # ... fetch-logik ...
        auto_build_master()
    """
    print()
    print("=" * 55)
    print("AUTO-REBUILD af master_indicators.csv")
    print("=" * 55)
    try:
        build_master()
        print()
        print("✓ Master-CSV opdateret. Klar til commit + push via GitHub Desktop.")
        _rapport_efter_build()
        # Printer altid, men rejser aldrig - se _tjek_konsistens_efter_build().
        # Et fetch-script skal ikke crashe fordi konsistenstjekket finder noget;
        # det skal bare stå tydeligt i outputtet, så man ser det før commit.
        _tjek_konsistens_efter_build()
    except Exception as e:
        print()
        print(f"✗ FEJL ved rebuild af master-CSV: {e}")
        print("  Rådata-CSV er gemt OK. Kør manuelt: python3 scripts/build_master_csv.py")
        # Vi raise IKKE - rådata er gemt og det er det vigtigste


if __name__ == "__main__":
    build_master()
    _rapport_efter_build()
    # Direkte kørsel (den vej CLAUDE.md instruerer at bruge når et
    # fetch-script IKKE selv printede "✓ Master-CSV opdateret") afbryder MED
    # exit 1 hvis konsistenstjekket finder fejl. Det er her fejlen skal
    # stoppes - før commit, ikke efter deploy.
    resultat = _tjek_konsistens_efter_build()
    if resultat is None:
        sys.exit(2)
    if resultat is False:
        sys.exit(1)
