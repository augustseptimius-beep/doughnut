"""Tal, tabeller og figurer til metodeartiklerne om den sociale og den økologiske ring.

Læser data/master_indicators.csv, data/indikatorer.json og data/kommuner.json og
genskaber alle tal i de to artikler. Replikerer shared.ts' beregninger af
kategoriscorer og af kommunegruppe- og top 10-visningen.

Kræver numpy, pandas, scipy og matplotlib (i modsætning til datapipelinen, som
kun bruger standardbiblioteket). Køres fra projektets rodmappe:

    python3 docs/artikler/analyse_artikler.py

Skriver en tekstrapport til stdout og figurerne til docs/artikler/figurer/.
Artiklerne er skrevet på data ved commit 80a914c (25. september 2026).
"""
import json
import os

import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIGDIR = os.path.join(ROOT, "docs", "artikler", "figurer")

reg = json.load(open(os.path.join(ROOT, "data", "indikatorer.json")))
kom = json.load(open(os.path.join(ROOT, "data", "kommuner.json")))
m = pd.read_csv(os.path.join(ROOT, "data", "master_indicators.csv"), dtype={"kommune_kode": str})

IND = {i["id"]: i for i in reg["indikatorer"]}
CATS = reg["sociale_kategorier"]
DIMS = reg["oekologiske_dimensioner"]
CATNAVN = {c["id"]: c["name"] for c in CATS}
DIMNAVN = {d["id"]: d["name"] for d in DIMS}
SOC = [i for c in CATS for i in c["indicators"]]
ECO = [i for d in DIMS for i in d["indicators"]]

R = m.pivot(index="kommune_kode", columns="indicator_id", values="ratio")
RAW = m.pivot(index="kommune_kode", columns="indicator_id", values="raw_value")
REF = m.pivot(index="kommune_kode", columns="indicator_id", values="reference")
GRP = pd.Series({k["kode"]: k["gruppe"] for k in kom["kommuner"]}).loc[R.index]
D = pd.DataFrame({d["id"]: R["_dim_" + d["id"]] for d in DIMS})


def loft(i):
    return min(IND[i].get("cap", 150), 150)


def vis(x):
    return x.round(1)


def socfarve(s):
    s = vis(s)
    return pd.Series(np.where(s.isna(), "na", np.where(s >= 100, "g", np.where(s >= 85, "a", "r"))), index=s.index)


def ecofarve(s):
    s = vis(s)
    return pd.Series(np.where(s.isna(), "na", np.where(s <= 85, "g", np.where(s <= 100, "a", "r"))), index=s.index)


def gar(f):
    return f"{(f == 'g').sum()}/{(f == 'a').sum()}/{(f == 'r').sum()}"


def omskaler(mode):
    """computeGroupRatios() og computeTop10Ratios() fra shared.ts."""
    out = R[SOC].copy()
    for i in SOC:
        if IND[i].get("absolute_score"):
            continue
        col = R[i]
        if mode == "top10":
            base = col.dropna().sort_values(ascending=False).iloc[:10].mean()
            out[i] = np.minimum((col / base * 100).round(2), loft(i))
        else:
            out[i] = np.minimum((col / GRP.map(col.groupby(GRP).mean()) * 100).round(2), loft(i))
    return out


def kategorier(Rs):
    """computeCategoryScores(): simpelt gennemsnit af indikatorerne med data."""
    return pd.DataFrame({c["id"]: Rs[c["indicators"]].mean(axis=1) for c in CATS})


def eta2(y, g):
    y = y.dropna()
    g = g.loc[y.index]
    return ((y.groupby(g).transform("mean") - y.mean()) ** 2).sum() / ((y - y.mean()) ** 2).sum()


def trekant(cm):
    return cm.where(np.triu(np.ones(cm.shape), 1).astype(bool)).stack().dropna()


def alfa(df):
    df = df.dropna()
    k = df.shape[1]
    return k / (k - 1) * (1 - df.var(ddof=1).sum() / df.sum(axis=1).var(ddof=1))


VIS = {"landsgns": R[SOC], "gruppe": omskaler("gruppe"), "top10": omskaler("top10")}
CS = {k: kategorier(v) for k, v in VIS.items()}


def overskrift(t):
    print("\n== " + t)


# ---------------------------------------------------------------- social
def social():
    overskrift("Dækning og dataår (social)")
    print("værdier:", int(R[SOC].notna().sum().sum()), "af", 98 * len(SOC))
    print("mangler:", {i: int(98 - R[i].notna().sum()) for i in SOC if R[i].notna().sum() < 98})
    print("grundlag:", pd.Series([IND[i]["reference"]["type"] for i in SOC]).value_counts().to_dict())
    print("dataår:", m[m.indicator_id.isin(SOC)].drop_duplicates("indicator_id")["data_year"].value_counts().to_dict())

    overskrift("Figur 2: farver pr. kategori i de tre visninger (grøn/gul/rød)")
    for c in CATS:
        print(f"{c['name']:16s}", "  ".join(f"{b}={gar(socfarve(CS[b][c['id']]))}" for b in CS))
    print("andel grønne:", {b: round((vis(CS[b]) >= 100).sum().sum() / CS[b].notna().sum().sum(), 3) for b in CS})
    print("gns. kategoriscore:", {b: round(CS[b].stack().mean(), 1) for b in CS})
    for b in CS:
        n = (vis(CS[b]) >= 100).sum(axis=1)
        print(f"antal grønne kategorier ({b}): median {n.median()}, min {n.min()}, max {n.max()}, nul: {(n == 0).sum()}")
    n1 = (vis(CS["landsgns"]) >= 100).sum(axis=1)
    n2 = (vis(CS["gruppe"]) >= 100).sum(axis=1)
    print("rangkorrelation antal grønne, landsgns mod gruppe:", round(stats.spearmanr(n1, n2).statistic, 2))
    skift = 0
    for c in CATS:
        s = int((socfarve(CS["landsgns"][c["id"]]) != socfarve(CS["gruppe"][c["id"]])).sum())
        skift += s
        rho = stats.spearmanr(CS["landsgns"][c["id"]], CS["gruppe"][c["id"]], nan_policy="omit").statistic
        rho10 = stats.spearmanr(CS["landsgns"][c["id"]], CS["top10"][c["id"]], nan_policy="omit").statistic
        print(f"{c['name']:16s} farveskift landsgns->gruppe {s:3d}  rho {rho:.2f}  rho top10 {rho10:.2f}")
    print("farveskift i alt:", skift, "af", 98 * len(CATS))

    overskrift("Figur 1: eta^2 for kommunegruppe")
    e = pd.Series({CATNAVN[c["id"]]: eta2(CS["landsgns"][c["id"]], GRP) for c in CATS}).sort_values()
    print(e.round(2).to_dict())
    ei = pd.Series({i: eta2(R[i], GRP) for i in SOC})
    print("indikatorer: median", round(ei.median(), 2), " over 0,5:", ei[ei > 0.5].round(2).to_dict())
    print("i gruppevisningen:", {CATNAVN[c["id"]]: round(eta2(CS["gruppe"][c["id"]], GRP), 2) for c in CATS})

    overskrift("Principalkomponenter (standardiserede scorer, manglende = gennemsnit)")
    X = R[SOC].fillna(R[SOC].mean())
    w, V = np.linalg.eigh(np.corrcoef(((X - X.mean()) / X.std()).T.values))
    w, V = w[::-1], V[:, ::-1]
    print("andel varians, komponent 1-3:", (w[:3] / w.sum()).round(3), " egenværdi > 1:", int((w > 1).sum()))
    lad = pd.Series(V[:, 0] * np.sqrt(w[0]), index=SOC)
    lad = lad if lad["disposable_income"] > 0 else -lad
    print("højeste ladninger:", lad.sort_values(ascending=False).head(8).round(2).to_dict())

    overskrift("Tabel 2: intern sammenhæng")
    for c in CATS:
        ids = c["indicators"]
        if len(ids) < 2:
            continue
        tri = trekant(R[ids].corr())
        a = f"{alfa(R[ids]):.2f}" if len(ids) >= 3 else ""
        print(f"{c['name']:16s} k={len(ids)} gns r={tri.mean():.2f} alfa={a:5s} negative par {(tri < 0).sum()} af {len(tri)}")

    overskrift("Overlap mellem indikatorer")
    tri = trekant(R[SOC].corr())
    kat = {i: c["id"] for c in CATS for i in c["indicators"]}
    staerk = tri[tri.abs() > 0.7]
    print("par i alt", len(tri), " |r|>0,7:", len(staerk), " heraf på tværs af kategorier:",
          sum(kat[a] != kat[b] for a, b in staerk.index))
    tk = trekant(CS["landsgns"].corr())
    print("kategorier: median |r|", round(tk.abs().median(), 2), " over 0,6:",
          {f"{CATNAVN[a]}~{CATNAVN[b]}": round(v, 2) for (a, b), v in tk[tk.abs() > 0.6].items()})

    overskrift("Loftet på 150")
    paa = pd.Series({i: int((R[i] >= loft(i) - 1e-9).sum()) for i in SOC})
    print("andel på 150:", round((R[SOC] >= 149.999).sum().sum() / R[SOC].notna().sum().sum(), 3))
    print("flest på loftet:", paa.sort_values(ascending=False).head(10).to_dict())

    def uden_loft(i):
        ind = IND[i]
        if ind.get("formula") == "100_minus_raw":
            return 100 - RAW[i]
        r = REF[i] / RAW[i] * 100 if ind.get("inverse") else RAW[i] / REF[i] * 100
        r = r.replace(np.inf, 150)
        return np.minimum(r, ind["cap"]) if ind.get("cap", 150) < 150 else r

    CU = kategorier(pd.DataFrame({i: uden_loft(i) for i in SOC}))
    skift = 0
    for c in CATS:
        s = int((socfarve(CS["landsgns"][c["id"]]) != socfarve(CU[c["id"]])).sum())
        skift += s
        d = CU[c["id"]] - CS["landsgns"][c["id"]]
        rho = stats.spearmanr(CU[c["id"]], CS["landsgns"][c["id"]], nan_policy="omit").statistic
        print(f"{c['name']:16s} skift {s}  gns. løft {d.mean():.1f}  maks {CU[c['id']].max():.1f}  rho {rho:.2f}")
    print("farveskift uden loft i alt:", skift)

    overskrift("Tabel 3: fjern én indikator ad gangen")
    for c in CATS:
        ids = c["indicators"]
        if len(ids) < 2:
            continue
        hel = CS["landsgns"][c["id"]]
        for i in ids:
            rest = R[[j for j in ids if j != i]].mean(axis=1)
            print(f"{c['name']:16s} {i:24s} gns {(rest - hel).abs().mean():5.1f}  farveskift {(socfarve(hel) != socfarve(rest)).sum()}")

    overskrift("Afstand til farvegrænser (inden for 5 point af 85 eller 100)")
    for b in ("landsgns", "gruppe"):
        x = CS[b]
        naer = ((x - 100).abs() < 5) | ((x - 85).abs() < 5)
        print(b, round(naer.sum().sum() / x.notna().sum().sum(), 3))


# ---------------------------------------------------------------- økologisk
def oekologisk():
    overskrift("Dækning (økologisk)")
    print("værdier:", int(R[ECO].notna().sum().sum()), "af", 98 * len(ECO))
    print("grundlag:", pd.Series([IND[i]["reference"]["type"] for i in ECO]).value_counts().to_dict())

    overskrift("Figur 1: dimensioner (grøn/gul/rød, min, median, maks)")
    for d in DIMS:
        s = D[d["id"]]
        print(f"{d['name']:16s} {gar(ecofarve(s))}  {s.min():.1f} {s.median():.1f} {s.max():.1f}")
    over = (vis(D) > 100).sum(axis=1)
    print("antal overskredne dimensioner pr. kommune:", over.value_counts().sort_index().to_dict())

    overskrift("Tabel 3: den indikator, der afgør dimensionen")
    for d in DIMS:
        if len(d["indicators"]) > 1:
            print(d["name"], R[d["indicators"]].dropna(how="all").idxmax(axis=1).value_counts().to_dict())

    overskrift("Figur 2: worst-of mod gennemsnit")
    for d in DIMS:
        if len(d["indicators"]) > 1:
            sub = R[d["indicators"]]
            fw, fa = ecofarve(sub.max(axis=1)), ecofarve(sub.mean(axis=1))
            print(f"{d['name']:16s} worst-of {gar(fw)}  gennemsnit {gar(fa)}  skift {(fw != fa).sum()}")

    overskrift("Tabel 4: andre grænser (antal kommuner over)")
    for t in (2.5, 3, 5, 10):
        print(f"klima {t} ton: territorial {(RAW['klimapaavirkning'] > t).sum()}, forbrug {(RAW['forbrug_co2'] > t).sum()}")
    for t in (5, 7.5, 10, 12.5, 15):
        alt = R[["naer_kystvand", "overfladevand"]].copy()
        alt["n"] = RAW["n_deposition"] / t * 100
        print(f"kvælstofnedfald {t} kg: {(RAW['n_deposition'] > t).sum()} over, dimension {gar(ecofarve(alt.max(axis=1)))}")
    for t in (6, 10, 50):
        print(f"nitrat {t} mg/L: {(RAW['nitrat'] > t).sum()} af {RAW['nitrat'].notna().sum()}")
    for no2, pm in ((10, 5), (20, 10)):
        print(f"NO2 > {no2}: {(RAW['luftkvalitet_no2'] > no2).sum()}   PM2.5 > {pm}: {(RAW['luftkvalitet_pm25'] > pm).sum()}")
    ar = RAW["areal_antropiseret"]
    print(f"antropiseret areal: {ar.min()}-{ar.max()} %, over 15 %: {(ar > 15).sum()}")

    overskrift("Sammenhæng")
    print("median |r| mellem dimensioner:", round(trekant(D.corr()).abs().median(), 2),
          " areal~bio:", round(D["arealanvendelse"].corr(D["biodiversitet"]), 2))
    print("eta^2 kommunegruppe:", {DIMNAVN[d]: round(eta2(D[d], GRP), 2) for d in D})
    gronne = (vis(CS["gruppe"]) >= 100).sum(axis=1)
    print("rangkorrelation antal grønne sociale (gruppe) og antal overskredne:", round(stats.spearmanr(gronne, over).statistic, 2))
    print("rangkorrelation forbrugs-CO2 og medianindkomst:", round(stats.spearmanr(RAW["forbrug_co2"], RAW["disposable_income"]).statistic, 2))


# ---------------------------------------------------------------- figurer
def figurer():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    os.makedirs(FIGDIR, exist_ok=True)
    plt.rcParams.update({"font.family": "Liberation Sans", "font.size": 9, "axes.edgecolor": "#8a8984",
                         "axes.labelcolor": "#52514e", "xtick.color": "#52514e", "ytick.color": "#0b0b0b",
                         "axes.spines.top": False, "axes.spines.right": False})
    G, A, RD, INK, INK2, GRID = "#0ca30c", "#fab219", "#d03b3b", "#0b0b0b", "#52514e", "#e4e3df"

    def akse(ax):
        ax.tick_params(axis="y", length=0)
        ax.spines["left"].set_visible(False)
        ax.xaxis.grid(True, color=GRID, linewidth=0.6)
        ax.set_axisbelow(True)

    def stak(ax, y, g, a, r, minlabel):
        left = 0
        for n, col in ((g, G), (a, A), (r, RD)):
            if n:
                ax.barh(y, n, left=left, color=col, height=0.72, edgecolor="white", linewidth=1.2)
                if n >= minlabel:
                    ax.text(left + n / 2, y, str(n), ha="center", va="center", fontsize=7, color=INK if col == A else "white")
            left += n

    def taelle(f):
        return (f == "g").sum(), (f == "a").sum(), (f == "r").sum()

    # Social figur 1: eta^2
    e = pd.Series({CATNAVN[c["id"]]: eta2(CS["landsgns"][c["id"]], GRP) for c in CATS}).sort_values()
    fig, ax = plt.subplots(figsize=(6.3, 3.6))
    ax.barh(range(len(e)), e.values, color="#2a78d6", height=0.62)
    for y, v in enumerate(e.values):
        ax.text(v + 0.01, y, f"{v:.2f}".replace(".", ","), va="center", fontsize=8, color=INK2)
    ax.set_yticks(range(len(e)))
    ax.set_yticklabels(e.index)
    ax.set_xlim(0, 0.9)
    ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8])
    ax.set_xticklabels(["0", "0,2", "0,4", "0,6", "0,8"])
    ax.set_xlabel("Andel af variationen mellem kommuner forklaret af kommunegruppen (η²)", color=INK2)
    akse(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "social_eta2.png"), dpi=220)
    plt.close(fig)

    # Social figur 2: farver i tre visninger
    fig, axes = plt.subplots(1, 3, figsize=(7.1, 4.3), sharey=True)
    orden = [c["id"] for c in CATS][::-1]
    for ax, (b, titel) in zip(axes, (("landsgns", "Landsgennemsnit"), ("gruppe", "Kommunegruppe (standard)"), ("top10", "Top 10"))):
        for y, cid in enumerate(orden):
            stak(ax, y, *taelle(socfarve(CS[b][cid].dropna())), 12)
        ax.set_title(titel, fontsize=9, color=INK, loc="left", pad=6)
        ax.set_xlim(0, 98)
        ax.set_xticks([0, 49, 98])
        akse(ax)
    axes[0].set_yticks(range(len(orden)))
    axes[0].set_yticklabels([CATNAVN[c] for c in orden])
    axes[1].set_xlabel("Antal kommuner", color=INK2)
    fig.legend(handles=[Patch(color=G, label="Grøn: 100 eller derover"), Patch(color=A, label="Gul: 85 til under 100"),
                        Patch(color=RD, label="Rød: under 85")], loc="lower center", ncol=3, frameon=False, fontsize=8,
               bbox_to_anchor=(0.55, -0.01))
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(os.path.join(FIGDIR, "social_farver.png"), dpi=220)
    plt.close(fig)

    # Økologisk figur 1: dimensionsscorer på logaritmisk akse
    fig, ax = plt.subplots(figsize=(6.6, 3.9))
    rng = np.random.default_rng(7)
    dims = [d["id"] for d in DIMS][::-1]
    for y, did in enumerate(dims):
        v = D[did].dropna()
        col = np.where(vis(v) <= 85, G, np.where(vis(v) <= 100, A, RD))
        ax.scatter(v.clip(lower=10), y + rng.uniform(-0.22, 0.22, len(v)), s=16, c=col, edgecolors="white", linewidths=0.5, zorder=3)
    ax.axvline(85, color=INK2, linewidth=0.9, linestyle=":", zorder=2)
    ax.axvline(100, color=INK2, linewidth=0.9, zorder=2)
    ax.text(100, len(dims) - 0.35, " 100 = grænsen", fontsize=7.5, color=INK2, va="bottom")
    ax.set_xscale("log")
    ax.set_xlim(9, 2000)
    ax.set_xticks([10, 30, 100, 300, 1000])
    ax.set_xticklabels(["10", "30", "100", "300", "1.000"])
    ax.set_yticks(range(len(dims)))
    ax.set_yticklabels([DIMNAVN[d] for d in dims])
    ax.set_xlabel("Dimensionsscore (logaritmisk akse). Værdier under 10 er vist ved 10.", color=INK2)
    akse(ax)
    ax.legend(handles=[Patch(color=G, label="Grøn: 85 eller derunder"), Patch(color=A, label="Gul: over 85 til 100"),
                       Patch(color=RD, label="Rød: over 100 (overskridelse)")], loc="lower center", ncol=3, frameon=False,
              fontsize=7.5, bbox_to_anchor=(0.45, -0.32))
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "eco_dim.png"), dpi=220)
    plt.close(fig)

    # Økologisk figur 2: worst-of mod gennemsnit
    fig, ax = plt.subplots(figsize=(6.6, 3.2))
    rk = []
    for d in DIMS:
        if len(d["indicators"]) > 1:
            sub = R[d["indicators"]]
            rk.append((d["name"], "worst-of", sub.max(axis=1)))
            rk.append((d["name"], "gennemsnit", sub.mean(axis=1)))
    rk = rk[::-1]
    for y, (_, _, s) in enumerate(rk):
        stak(ax, y, *taelle(ecofarve(s.dropna())), 9)
    ax.set_yticks(range(len(rk)))
    ax.set_yticklabels([f"{n}, {a}" + (" (platformen)" if (a == "gennemsnit") == (n == "Forurening") else "") for n, a, _ in rk], fontsize=8)
    ax.set_xlim(0, 98)
    ax.set_xticks([0, 49, 98])
    ax.set_xlabel("Antal kommuner", color=INK2)
    akse(ax)
    ax.legend(handles=[Patch(color=G, label="Grøn"), Patch(color=A, label="Gul"), Patch(color=RD, label="Rød")],
              loc="lower center", ncol=3, frameon=False, fontsize=7.5, bbox_to_anchor=(0.35, -0.36))
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "eco_worstof.png"), dpi=220)
    plt.close(fig)
    print("\nfigurer skrevet til", FIGDIR)


if __name__ == "__main__":
    social()
    oekologisk()
    figurer()
