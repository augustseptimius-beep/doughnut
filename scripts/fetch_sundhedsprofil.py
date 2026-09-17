"""
Henter kommunetal fra Den Nationale Sundhedsprofil ("Hvordan har du det?")
via internetdatabasen på danskernessundhed.dk.

Kilde: Sundhedsstyrelsen + Statens Institut for Folkesundhed (SDU).
Undersøgelsesbølger: 2010, 2013, 2017, 2021, 2025 (hvert 4. år).

KØR FRA PROJEKTETS RODMAPPE:
    python3 scripts/fetch_sundhedsprofil.py

Teknisk baggrund
----------------
Internetdatabasen er en SAS Visual Analytics 7.5-viewer. Der findes ikke et
offentligt dokumenteret API, men viewerens eget transport-lag kan kaldes
direkte, og gæsteadgangen er åben. Flowet er:

  1. GET gæste-JSP'en. Den udsteder et CAS ticket-granting-cookie (CASTGC).
  2. Veksl CASTGC til en service ticket for SASVisualAnalyticsTransport via
     CAS' REST-endpoint, og indløs den. Uden dette svarer alle /services/*
     med 401.
  3. POST generateReport. Svaret indeholder en "requery"-URL med den
     session-nøgle og reportDate som getData kræver. FÆLDE: getData svarer
     400 hvis reportDate mangler - brug requery-URL'en som den kommer.
  4. GET report.xml og find den DataDefinition der hører til rapportens
     Kommune-faneblad (én pr. rapport, id'et varierer).
  5. POST getData med den DataDefinition. Svaret er CSV i CDATA plus en
     StringTable med kommunenavne, som datarækkerne indekserer ind i.

Landsgennemsnit
---------------
Databasen udstiller ikke et landstal pr. kommunetabel. Vi beregner det som
et befolkningsvægtet gennemsnit af de 98 kommuneandele, vægtet med DST
FOLK1A befolkning 16+ (undersøgelsens målgruppe). Det er ikke identisk med
SIF's egen vægtede landsestimat, men det er den korrekte reference for
netop de kommunetal vi scorer imod.
"""
from __future__ import annotations

import csv
import html
import os
import re
import sys
import urllib.parse
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
BASE = "https://proxy.danskernessundhed.dk"
REPORT_PATH = "/Produktion/Danskernes_Sundhed/"

# Seneste bølge. Opdateres når en ny undersøgelse offentliggøres (hvert 4. år).
SENESTE_BOELGE = 2025

# Retningspilens sammenligningsår. Vi bruger 2017 frem for 2010, selvom hele
# serien hentes: en pil beregnet 2010-2025 ville beskrive 15 års udvikling og
# ikke være sammenlignelig med de øvrige indikatorers ~10-årige vinduer.
# 2021 undgås som startår hvor 2017 findes, fordi dataindsamlingen i 2021 lå
# under coronarestriktioner - især mental sundhed og alkohol var atypiske det
# år, så en 2021-basis ville måle normalisering frem for udvikling.
# Indikatorer der først blev stillet i 2021 (ensomhed, fysisk aktivitet) får
# nødvendigvis 2021 som basis.
TREND_BASIS_PRIORITET = [2017, 2021]


# --- Indikatorer vi henter -------------------------------------------------
# inverse=True betyder at en høj andel er dårlig (ratio = land/kommune * 100).
INDIKATORER = [
    # Sundhed (tilstand)
    dict(id="selvvurderet_helbred", rapport="Andel med godt selvvurderet helbred",
         inverse=False, navn="Godt selvvurderet helbred"),
    dict(id="mentalt_helbred", rapport="Daarligt mentalt helbred",
         inverse=True, navn="Dårligt mentalt helbred"),
    # Levevaner (samme kategori: Sundhed)
    dict(id="rygning", rapport="Andel der ryger dagligt",
         inverse=True, navn="Daglig rygning"),
    dict(id="alkohol", rapport="Drikker mere end 10 genstande om ugen",
         inverse=True, navn="Drikker over 10 genstande om ugen"),
    # Hentes, men scores IKKE. Korrelationen med svær overvægt er 0,90 og med
    # kostskalaen 0,80: de tre måler reelt samme bagvedliggende forhold, og med
    # alle tre i et gennemsnit ville den ene konstruktion fylde tre af ni pladser i
    # Sundhed. Svær overvægt er beholdt som udfaldet, kostskalaen som den
    # bredeste adfærdsmåling. Tallet står i sundhedsprofil_scores.csv hvis
    # prioriteringen skal laves om.
    dict(id="fysisk_aktivitet", rapport="Opfylder ikke WHOs anbefalinger for fysisk aktivitet",
         inverse=True, navn="Opfylder ikke WHO's anbefaling for fysisk aktivitet",
         kun_data=True),
    dict(id="kost", rapport="Usundt kostmonster",
         inverse=True, navn="Lav score på kostskalaen"),
    dict(id="svaer_overvaegt", rapport="Svaer overvaegt",
         inverse=True, navn="Svær overvægt (BMI over 30)"),
    # Fællesskab
    dict(id="ensomhed", rapport="Ensomhed",
         inverse=True, navn="Ensomhed"),
    # Begrænset social støtte. Erstatter sports_spending i Fællesskab sep. 2026:
    # et udfaldsmål frem for et budgettal. Korrelerer 0,50 med ensomhed, altså
    # beslægtet men ikke overlappende, og har hele serien 2010-2025.
    dict(id="social_stoette", rapport=" Aldrig nogen at tale med",
         inverse=True, navn="Begrænset social støtte"),
]


# --- SAS Visual Analytics-klient ------------------------------------------

class SundhedsprofilClient:
    """Minimal klient til internetdatabasens SAS-transportlag."""

    def __init__(self) -> None:
        self.s = requests.Session()
        self.s.headers["User-Agent"] = (
            "Danmarks98Doughnuts/1.0 (Thisted Kommune; klimateam) "
            "python-requests"
        )
        self._authed_for: str | None = None

    def _login(self, rapport: str) -> None:
        """Gæstelogin via CAS. Skal gøres én gang pr. session."""
        jsp = (f"{BASE}/SASVisualAnalyticsViewer/VisualAnalyticsViewer_guest.jsp"
               f"?reportName={urllib.parse.quote(rapport)}"
               f"&reportPath={REPORT_PATH}&reportViewOnly=true")
        self.s.get(jsp, timeout=60).raise_for_status()
        tgt = self.s.cookies.get("CASTGC")
        if not tgt:
            raise RuntimeError("Fik ikke CASTGC fra gæste-login - er sitet ændret?")
        svc = f"{BASE}/SASVisualAnalyticsTransport/onebi/services/getUserCapabilities"
        r = self.s.post(f"{BASE}/SASLogon/rest/v1/tickets/{tgt}",
                        data={"service": svc}, timeout=60)
        r.raise_for_status()
        st = r.text.strip()
        if not st.startswith("ST-"):
            raise RuntimeError(f"Uventet service ticket: {st[:60]!r}")
        self.s.get(f"{svc}?ticket={st}", timeout=60).raise_for_status()
        self._authed_for = rapport

    def _generate(self, rapport: str) -> tuple[str, str]:
        """Returnerer (requery_url, cache_key)."""
        loc = f"SBIP://METASERVER/Produktion/Danskernes_Sundhed/{rapport}(Report)"
        r = self.s.post(f"{BASE}/SASVisualAnalyticsTransport/onebi/services/generateReport",
                        params={"bypassCache": "true", "dataLevel": "nodata",
                                "location": loc}, timeout=240)
        r.raise_for_status()
        m = re.search(r'<url type="requery">(.*?)</url>', r.text)
        c = re.search(r"<cacheKey>(.*?)</cacheKey>", r.text)
        if not m or not c:
            raise RuntimeError(f"Kunne ikke finde requery/cacheKey for {rapport!r}")
        return BASE + html.unescape(m.group(1)), c.group(1)

    def _report_xml(self, cache_key: str) -> str:
        key = cache_key.rsplit("/", 1)[0] + "/report.xml"
        r = self.s.get(f"{BASE}/SASVisualAnalyticsTransport/onebi/services/getReportFile",
                       params={"key": key}, timeout=180)
        r.raise_for_status()
        return r.text

    def _get_data(self, requery: str, dd: str) -> str:
        body = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?> '
                "<SASReportState><Data><queryRequests>"
                f'<queryRequest data="{dd}" dataLevel="interactive"/>'
                "</queryRequests></Data></SASReportState>")
        r = self.s.post(requery, data=body.encode("utf-8"),
                        headers={"Content-Type": "application/xml"}, timeout=240)
        r.raise_for_status()
        return r.text

    @staticmethod
    def _kommune_dds(report_xml: str) -> list[str]:
        """
        DataDefinitions der kan indeholde kommunetabellen, mest lovende først.

        Rapporterne har et faneblad der hedder "Kommune". Dets krydstabel
        peger via data="ddNNNN" på den tabel vi vil have. Id'et varierer fra
        rapport til rapport, så vi slår det op frem for at hardkode det.
        Kortfanebladene ("Kommunekort procent/OR") bruger samme tal, men
        krydstabellen er det enkleste udtræk. Fallback er alle
        DataDefinitions, som så valideres på indholdet.
        """
        foretrukne: list[str] = []
        sektioner = list(re.finditer(r'<Section\b[^>]*label="([^"]*)"[^>]*>', report_xml))
        for m in sektioner:
            if not m.group(1).startswith("Kommune"):
                continue
            start = m.end()
            nxt = report_xml.find("<Section ", start)
            krop = report_xml[start:nxt if nxt > 0 else len(report_xml)]
            for ref in re.findall(r'<Visual ref="(\w+)"', krop):
                el = re.search(r'<\w+[^>]*name="' + ref + r'"[^>]*>', report_xml)
                if not el:
                    continue
                dd = re.search(r'\bdata="(dd\d+)"', el.group(0))
                if dd and dd.group(1) not in foretrukne:
                    foretrukne.append(dd.group(1))
        alle = re.findall(r'<DataDefinition[^>]*name="(dd\d+)"', report_xml)
        return foretrukne + [d for d in alle if d not in foretrukne]

    @staticmethod
    def _parse(xml: str) -> tuple[list[str], list[list[str]], list[str]] | None:
        """Returnerer (variabel-labels, datarækker, stringtable) eller None."""
        labels = re.findall(r'<(?:Numeric|String)Variable\b[^>]*label="([^"]*)"', xml)
        data = re.search(r"<Data[^>]*><!\[CDATA\[(.*?)\]\]></Data>", xml, re.S)
        st = re.search(r"<StringTable[^>]*><!\[CDATA\[(.*?)\]\]></StringTable>", xml, re.S)
        if not data or not st:
            return None
        rows = [r.split(",") for r in data.group(1).strip().splitlines() if r.strip()]
        strings = [s.strip().strip('"') for s in st.group(1).strip().splitlines() if s.strip()]
        return labels, rows, strings

    def hent_kommunetal(self, rapport: str) -> tuple[dict[int, dict[str, float]], str]:
        """
        Returnerer ({aar: {kommunenavn: andel_pct}}, maalenavn).
        Andele returneres i procent (databasen leverer dem som brøk).
        """
        if self._authed_for is None:
            self._login(rapport)
        requery, cache = self._generate(rapport)
        rx = self._report_xml(cache)

        for dd in self._kommune_dds(rx):
            parsed = self._parse(self._get_data(requery, dd))
            if not parsed:
                continue
            labels, rows, strings = parsed
            # Kommunetabellen kendes på: en Kommune-kolonne, en År-kolonne og
            # et procentmål. OR-kolonnen findes ved siden af og springes over.
            if "Kommune" not in labels or "År" not in labels:
                continue
            pct_idx = next((i for i, lab in enumerate(labels)
                            if "OR" not in lab and lab not in ("Kommune", "År", "Region", "Frequency")),
                           None)
            if pct_idx is None:
                continue
            kom_idx, aar_idx = labels.index("Kommune"), labels.index("År")
            ud: dict[int, dict[str, float]] = {}
            for row in rows:
                if max(kom_idx, aar_idx, pct_idx) >= len(row):
                    continue
                try:
                    navn = strings[int(float(row[kom_idx]))]
                    aar = int(float(row[aar_idx]))
                    pct = float(row[pct_idx]) * 100
                except (ValueError, IndexError):
                    continue
                if navn.startswith("Region "):
                    continue
                ud.setdefault(aar, {})[navn] = round(pct, 2)
            if ud and max(len(v) for v in ud.values()) >= 90:
                return ud, labels[pct_idx]
        raise RuntimeError(f"Fandt ingen kommunetabel i rapporten {rapport!r}")


# --- DST: befolkning 16+ til vægtning -------------------------------------

def hent_befolkning_16plus() -> dict[str, float]:
    """FOLK1A: folketal 16 år og derover pr. kommune (undersøgelsens målgruppe)."""
    print("Henter befolkning 16+ (DST FOLK1A) til vægtning...")
    sys.path.insert(0, str(ROOT / "scripts"))
    from dst_aar import seneste_kvartal  # noqa: E402

    aldre = [str(a) for a in range(16, 126)]
    body = {
        "table": "FOLK1A", "format": "JSONSTAT", "lang": "da",
        "variables": [
            {"code": "OMRÅDE", "values": ["*"]},
            {"code": "KØN", "values": ["TOT"]},
            {"code": "ALDER", "values": aldre},
            {"code": "Tid", "values": [seneste_kvartal("FOLK1A", "K1", fallback="2025K1")]},
        ],
    }
    r = requests.post("https://api.statbank.dk/v1/data", json=body, timeout=180)
    r.raise_for_status()
    js = r.json()["dataset"]
    omr = js["dimension"]["OMRÅDE"]
    idx = omr["category"]["index"]
    labels = omr["category"]["label"]
    n_alder = len(js["dimension"]["ALDER"]["category"]["index"])
    values = js["value"]

    ud: dict[str, float] = {}
    for kode, i in idx.items():
        if not (kode.isdigit() and len(kode) == 3 and kode != "000"):
            continue
        start = i * n_alder
        total = sum(v for v in values[start:start + n_alder] if v)
        ud[labels[kode]] = float(total)
    print(f"  {len(ud)} kommuner")
    return ud


# --- Hjælpere --------------------------------------------------------------

def ratio_direct(kommune_val: float, national_avg: float) -> float:
    """Direkte ratio: højere er bedre."""
    if national_avg == 0:
        return 0
    return round((kommune_val / national_avg) * 100, 2)


def ratio_inverse(kommune_val: float, national_avg: float) -> float:
    """Inverteret ratio: lavere er bedre."""
    if kommune_val == 0:
        return 150
    return round((national_avg / kommune_val) * 100, 2)


def kommune_koder() -> dict[str, str]:
    """
    Navn -> kommunekode, læst fra master-CSV'en, som er repoets autoritative
    kommuneliste. Sundhedsprofilen bruger enkelte andre stavemåder; de
    oversættes her.
    """
    kort: dict[str, str] = {}
    with open(DATA / "master_indicators.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            kort[row["kommune_navn"]] = row["kommune_kode"]
    alias = {
        "Bornholm": "Bornholms Regionskommune",
        "Vesthimmerlands": "Vesthimmerlands Kommune",
        "Faaborg-Midtfyn": "Faaborg-Midtfyn",
        "Aabenraa": "Aabenraa",
        "Ærø": "Ærø",
    }
    for kilde_navn, master_navn in alias.items():
        if master_navn in kort:
            kort.setdefault(kilde_navn, kort[master_navn])
    return kort


def vaegtet_landsgennemsnit(andele: dict[str, float], vaegte: dict[str, float]) -> float:
    """Befolkningsvægtet gennemsnit af kommuneandele."""
    num = den = 0.0
    for navn, pct in andele.items():
        w = vaegte.get(navn)
        if w is None:
            continue
        num += pct * w
        den += w
    if den == 0:
        raise RuntimeError("Ingen vægte matchede kommunenavnene")
    return num / den


def opdater_trend_historik(historik: list[dict], ids: list[str]) -> None:
    """
    Skriver Sundhedsprofilens serie ind i data/trend_history_raw.csv, som
    build_trends_csv.py læser. Vores egne indikator-rækker erstattes; alt
    andet i filen bevares.

    Kun to bølger skrives: TREND_BASIS_PRIORITET-året og seneste bølge.
    build_trends_csv bruger første og sidste punkt i serien når den er
    kortere end 6 år, så en fuld 2010-2025-serie ville give en pil der
    beskriver 15 år. Se kommentaren ved TREND_BASIS_PRIORITET.
    """
    raw = DATA / "trend_history_raw.csv"
    if not raw.exists():
        print(f"\n⚠ {raw.name} findes ikke - springer trend-historik over")
        return

    pr_ind: dict[str, dict[int, dict[str, float]]] = {}
    for r in historik:
        pr_ind.setdefault(r["indicator_id"], {}).setdefault(r["aar"], {})[r["kommune_kode"]] = r["raw_value"]

    nye: list[dict] = []
    for i in ids:
        aar_map = pr_ind.get(i, {})
        basis = next((a for a in TREND_BASIS_PRIORITET if a in aar_map), None)
        if basis is None or SENESTE_BOELGE not in aar_map:
            print(f"  ⚠ {i}: ingen brugbar basisbølge - får ingen retningspil")
            continue
        for a in (basis, SENESTE_BOELGE):
            for kode, v in aar_map[a].items():
                nye.append({"kommune_kode": kode, "indicator_id": i,
                            "aar": str(a), "vaerdi": v})
        print(f"  {i}: retning beregnes {basis} -> {SENESTE_BOELGE}")

    with open(raw, encoding="utf-8") as f:
        beholdt = [r for r in csv.DictReader(f) if r["indicator_id"] not in ids]
    with open(raw, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["kommune_kode", "indicator_id", "aar", "vaerdi"])
        w.writeheader()
        w.writerows(beholdt + nye)
    print(f"✓ Opdaterede {raw.name} ({len(nye)} nye rækker)")


# --- Main ------------------------------------------------------------------

def main() -> None:
    client = SundhedsprofilClient()
    befolkning = hent_befolkning_16plus()
    koder = kommune_koder()

    # navn -> vægt, oversat til Sundhedsprofilens stavemåder hvor de afviger
    navn_til_kode = koder
    vaegte_pr_navn: dict[str, float] = {}
    for master_navn, pop in befolkning.items():
        vaegte_pr_navn[master_navn] = pop
    for kilde_navn, kode in koder.items():
        for master_navn, pop in befolkning.items():
            if navn_til_kode.get(master_navn) == kode:
                vaegte_pr_navn[kilde_navn] = pop
                break

    seneste: dict[str, dict[str, float]] = {}   # id -> {kode: pct}
    historik: list[dict] = []
    landstal: dict[str, float] = {}
    umatchede: set[str] = set()

    for ind in INDIKATORER:
        print(f"\nHenter {ind['navn']!r} ({ind['rapport']})...")
        try:
            pr_aar, maal = client.hent_kommunetal(ind["rapport"])
        except Exception as e:
            print(f"  ⚠ FEJL: {e}")
            continue
        aar_liste = sorted(pr_aar)
        print(f"  bølger: {aar_liste}, måletal: {maal!r}")
        if SENESTE_BOELGE not in pr_aar:
            print(f"  ⚠ Ingen {SENESTE_BOELGE}-tal, bruger {aar_liste[-1]}")
        aar = SENESTE_BOELGE if SENESTE_BOELGE in pr_aar else aar_liste[-1]

        andele = pr_aar[aar]
        nat = vaegtet_landsgennemsnit(andele, vaegte_pr_navn)
        landstal[ind["id"]] = nat
        print(f"  {len(andele)} kommuner, vægtet landsgennemsnit {nat:.1f}%")

        pr_kode: dict[str, float] = {}
        for navn, pct in andele.items():
            kode = koder.get(navn)
            if not kode:
                umatchede.add(navn)
                continue
            pr_kode[kode] = pct
        seneste[ind["id"]] = pr_kode

        for a in aar_liste:
            for navn, pct in pr_aar[a].items():
                kode = koder.get(navn)
                if kode:
                    historik.append({"kommune_kode": kode, "indicator_id": ind["id"],
                                     "aar": a, "raw_value": pct})

    if umatchede:
        print(f"\n⚠ Kommunenavne uden match i master: {sorted(umatchede)}")

    # --- skriv scores-CSV ---
    ids = [i["id"] for i in INDIKATORER if i["id"] in seneste]
    inverse = {i["id"]: i["inverse"] for i in INDIKATORER}
    alle_koder = sorted({k for i in ids for k in seneste[i]})

    ud = DATA / "sundhedsprofil_scores.csv"
    with open(ud, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        header = ["kommune_kode"]
        for i in ids:
            header += [f"{i}_pct", f"{i}_ratio"]
        w.writerow(header)
        for kode in alle_koder:
            row = [kode]
            for i in ids:
                pct = seneste[i].get(kode)
                if pct is None:
                    row += ["", ""]
                    continue
                r = (ratio_inverse(pct, landstal[i]) if inverse[i]
                     else ratio_direct(pct, landstal[i]))
                row += [pct, min(r, 150)]
            w.writerow(row)
    print(f"\n✓ Skrev {ud.relative_to(ROOT)} ({len(alle_koder)} kommuner, {len(ids)} indikatorer)")

    hist = DATA / "sundhedsprofil_historik.csv"
    with open(hist, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["kommune_kode", "indicator_id", "aar", "raw_value"])
        w.writeheader()
        w.writerows(sorted(historik, key=lambda r: (r["indicator_id"], r["kommune_kode"], r["aar"])))
    print(f"✓ Skrev {hist.relative_to(ROOT)} ({len(historik)} rækker)")

    scorede = [i["id"] for i in INDIKATORER if not i.get("kun_data") and i["id"] in seneste]
    opdater_trend_historik(historik, scorede)

    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from build_master_csv import auto_build_master
        auto_build_master()
    except Exception as e:
        print(f"\n⚠ Kunne ikke auto-rebuild master-CSV: {e}")
        print("  Rådata er gemt. Kør manuelt: python3 scripts/build_master_csv.py")
    try:
        from build_trends_csv import auto_build_trends
        auto_build_trends()
    except Exception as e:
        print(f"\n⚠ Kunne ikke auto-rebuild trend-CSV: {e}")
        print("  Kør manuelt: python3 scripts/build_trends_csv.py")


if __name__ == "__main__":
    if Path.cwd() != ROOT and not (Path.cwd() / "data").is_dir():
        print(f"⚠ Kør fra projektets rodmappe: cd {ROOT}")
    main()
