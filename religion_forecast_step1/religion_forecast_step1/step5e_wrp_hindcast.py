"""Step 5E: test the Step 5D cohort model against religion history (WRP 1950-2010).

Each test runs a 10-year hindcast from WRP shares and WPP demography at year y and compares the result
with the WRP shares at y+10. Mechanisms are added one at a time:
  persistence  no change (the benchmark every model must beat)
  demo         group fertility gaps and age structure, no migration
  pool         + migration from the neighbour/continent/world pools (Step 5D default when no table)
  grav         + migration from the gravity origin-destination matrix, balanced to WPP
  momentum     + the previous decade's unexplained change carried forward with weight lam
Configurations are chosen on TRAIN decades and scored on TEST decades, so the test is out of sample.
WRP is noisy and its population definitions differ from WPP. Read results as tests of mechanisms.

Run: .\\.venv\\Scripts\\python.exe step5e_wrp_hindcast.py
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

import migration_od as mod
import step5d_engine as eng
import wrp_history as H

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "hindcast_step5e"
CATS = H.RELIGIONS
RELIGIONS = CATS
K = len(CATS)
SHARES = [f"share_{c}" for c in CATS]
DECADES = list(range(1950, 2001, 10))   # start years; each run ends 10 years later
TRAIN = [1960, 1970, 1980]
TEST = [1990, 2000]
BASE_GRID = dict(phi=[0.0, 0.25, 0.5, 0.75, 1.0], psi=[0.0, 0.5, 1.0], w_add=[0.0, 1.0], Hf=[30.0, 80.0])
GRAV_GRID = dict(gamma=[1.0, 2.0], b_adj=[1.0, 3.0])
LAMBDAS = [0.0, 0.25, 0.5, 0.75, 1.0]


def load_prior():
    a = json.loads((ROOT / "step5d_assumptions.json").read_text(encoding="utf8"))
    rel = np.array([a["group_tfr_2010_15"][c] for c in CATS]) / a["world_tfr_2010_15"]
    off = np.array([a["group_median_age_2010"][c] for c in CATS], float) - a["world_median_age_2010"]
    return rel, off


def net_for(wpp, ids, year):
    f = wpp[wpp.year.eq(year)].drop_duplicates('country_id').set_index('country_id').reindex(ids)
    return np.nan_to_num(f.net_migrations.to_numpy(float))


def decade_inputs(y, wrp, wpp, geo, nbrs):
    """Countries with valid WRP shares at y and y+10 and WPP demography at y, y+5 and y+10."""
    use = wrp[wrp.use]
    a = use[use.year.eq(y)].set_index("country_id")
    b = use[use.year.eq(y + 10)].set_index("country_id")
    years = [y, y + 5, y + 10]
    w = wpp[wpp.year.isin(years)].drop_duplicates(["country_id", "year"]).set_index(["year", "country_id"])
    ids = sorted(set(a.index) & set(b.index) & set(geo.index))
    ids = [i for i in ids if all((t, i) in w.index for t in years)]
    if len(ids) < 10:
        return None
    dem = {}
    for t in years:
        sub = w.loc[t].reindex(ids)
        e0 = sub.e0.to_numpy(float)
        dem[t] = dict(tfr=sub.tfr.to_numpy(float), median_age=sub.median_age.to_numpy(float),
                      wpp_population=sub["pop"].to_numpy(float),
                      net_migrations=sub.net_migrations.to_numpy(float),
                      e0=np.where(np.isfinite(e0), e0, 65.0))
    net_by_year = {t: net_for(wpp, ids, t) for t in range(y + 1, y + 11)}
    net5 = {t: 5.0 * np.mean([net_by_year[s] for s in range(t - 4, t + 1)], axis=0) for t in (y + 5, y + 10)}
    geometry = geo.loc[ids]
    cont = geometry.continent.to_numpy()
    lat, lon = geometry.lat.to_numpy(float), geometry.lon.to_numpy(float)
    return dict(
        y=y, ids=ids, sh0=a.loc[ids, SHARES].to_numpy(float), sh1=b.loc[ids, SHARES].to_numpy(float), dem=dem, net5=net5,
        adj=np.array([[1.0 if j in nbrs[i] else 0.0 for j in ids] for i in ids]),
        same=(cont[:, None] == cont[None, :]).astype(float),
        dist=H.haversine_km(lat[:, None], lon[:, None], lat[None, :], lon[None, :]),
        cont=pd.Series(cont).astype("category").cat.codes.to_numpy())


def run(inp, cfg, mechanism, rel, off):
    """Predicted shares [n, K] at y+10 without momentum. mechanism: 'demo' | 'pool' | 'grav'."""
    y, dem = inp["y"], inp["dem"]
    pars = dict(phi=cfg["phi"], psi=cfg["psi"], Hf=cfg["Hf"], e0=dem[y]["e0"], lam=0.4, lam_nb=0.1,
                lam_od=1.0, w_add=cfg["w_add"], world_tfr=2.5, eps=None, equal_fertility=False)
    engine = eng.Engine(rel, off, inp["cont"], pars, adjacency=inp["adj"])
    P = eng.initial_population(dem[y]["wpp_population"], inp["sh0"], dem[y]["median_age"], engine.median_offset)
    kernel = mod.gravity_kernel(inp["dist"], inp["adj"], inp["same"], gamma=cfg["gamma"], b_adj=cfg["b_adj"])
    years = [y, y + 5, y + 10]
    for t_prev, t_cur in zip(years[:-1], years[1:]):
        od = None
        if mechanism == "grav":
            od = mod.balanced_od(inp["net5"][t_cur], kernel)[1]
        P, _ = engine.step(P, dem[t_prev], dem[t_cur], (t_cur - y) - 2.5, rho=None, switch_factor=0.0,
                           migration=mechanism != "demo", od=od)
    return eng.shares_of(P)


def add_momentum(base, inp, prev_inp, prev_base, lam):
    """Add lam x the previous decade's unexplained change (observed end minus its demographic prediction)."""
    if prev_inp is None or lam == 0.0:
        return base
    pos = {c: i for i, c in enumerate(prev_inp["ids"])}
    U = np.zeros_like(base)
    for j, c in enumerate(inp["ids"]):
        if c in pos:
            i = pos[c]
            U[j] = prev_inp["sh1"][i] - prev_base[i]
    pred = np.clip(base + lam * U, 0.0, None)
    return pred / pred.sum(axis=1, keepdims=True)


def score(pred, inp):
    obs, start = inp["sh1"], inp["sh0"]
    w = inp["dem"][inp["y"]]["wpp_population"]
    tv = 0.5 * np.abs(pred - obs).sum(axis=1)
    moved = np.abs(obs - start) > 0.005
    hit = np.sign(pred - start) == np.sign(obs - start)
    sign_acc = np.array([hit[moved[:, k], k].mean() if moved[:, k].any() else np.nan for k in range(len(CATS))])
    glob = np.sum(w[:, None] * (pred - obs), axis=0) / w.sum()
    out = dict(n_countries=len(tv), mean_tv_pp=100 * tv.mean(), popw_tv_pp=100 * np.sum(w * tv) / w.sum())
    out.update({f"sign_{c}": float(sign_acc[k]) for k, c in enumerate(CATS)})
    out.update({f"global_err_pp_{c}": 100 * float(glob[k]) for k, c in enumerate(CATS)})
    return out


def _key(cfg):
    return tuple(sorted(cfg.items()))


def project_2010_2050(wrp, wpp, geo, nbrs, rel, off, cfg, gravity):
    """Demographic and migration projection from WRP 2010 shares to 2050, using WPP demography.
    No Pew data needed. Returns per-country shares and migration flows by religion."""
    import step5d_cohort_forecast as F
    use = wrp[wrp.use & wrp.year.eq(2010)].drop_duplicates("country_id").set_index("country_id")
    years = list(range(2010, 2051, 5))
    w = wpp[wpp.year.isin(years)].drop_duplicates(["country_id", "year"]).set_index(["year", "country_id"])
    ids = sorted(c for c in use.index if c in geo.index and all((t, c) in w.index for t in years))
    dem = {}
    for t in years:
        sub = w.loc[t].reindex(ids)
        e0 = sub.e0.to_numpy(float)
        dem[t] = dict(tfr=sub.tfr.to_numpy(float), median_age=sub.median_age.to_numpy(float),
                      wpp_population=sub["pop"].to_numpy(float), net_migrations=sub.net_migrations.to_numpy(float),
                      e0=np.where(np.isfinite(e0), e0, 65.0))
    od_by_year, n_geo = F.gravity_od_by_year(ids, wpp, range(2015, 2051, 5), geo, nbrs, gravity)
    od_for = F.od_lookup(od_by_year)
    geometry = geo.loc[ids]
    cont = pd.Series(geometry.continent.to_numpy()).astype("category").cat.codes.to_numpy()
    adj = np.array([[1.0 if j in nbrs[i] else 0.0 for j in ids] for i in ids])
    pars = dict(phi=cfg["phi"], psi=cfg["psi"], Hf=cfg["Hf"], e0=dem[2010]["e0"], lam=0.4, lam_nb=0.1,
                lam_od=1.0, w_add=cfg["w_add"], world_tfr=2.5, eps=None, equal_fertility=False)
    engine = eng.Engine(rel, off, cont, pars, adjacency=adj)
    sh0 = use.loc[ids, SHARES].to_numpy(float)
    P = eng.initial_population(dem[2010]["wpp_population"], sh0, dem[2010]["median_age"], engine.median_offset)
    inflow = np.zeros((len(ids), K))
    outflow = np.zeros((len(ids), K))
    for y0, y1 in zip(years[:-1], years[1:]):
        engine.last_flows = None
        P, _ = engine.step(P, dem[y0], dem[y1], (y1 - 2010) - 2.5, None, 0.0, migration=True, od=od_for(y1))
        out_k, in_k = engine.last_flows
        outflow += out_k
        inflow += in_k
    return dict(ids=ids, sh0=sh0, sh2050=eng.shares_of(P), inflow=inflow, outflow=outflow, n_geo=n_geo)


def projection_table(res):
    rows = []
    for j, cid in enumerate(res["ids"]):
        for k, cat in enumerate(RELIGIONS):
            rows.append(dict(country_id=cid, religion=cat, share_2010=res["sh0"][j, k], share_2050=res["sh2050"][j, k],
                             inflow_2010_2050=res["inflow"][j, k], outflow_2010_2050=res["outflow"][j, k],
                             net_2010_2050=res["inflow"][j, k] - res["outflow"][j, k]))
    return pd.DataFrame(rows)


def group_tfr_table(wpp, rel, phis, w_add, shares_2010, year=2020):
    """Predicted fertility by religion for every country.

    Group TFR = national TFR x relative multiplier. Multiplier = blend of the multiplicative gap and the
    additive gap (w_add). Where 2010 WRP shares exist, multipliers are rescaled so the share-weighted
    average equals the national TFR, which keeps national births consistent. These are model
    assumptions shrunk by the hindcast, not measured group fertility."""
    w = wpp[wpp.year.eq(year)].drop_duplicates("country_id").set_index("country_id")
    rows = []
    for cid, r in w.iterrows():
        tfr = float(r.tfr)
        if not np.isfinite(tfr) or tfr <= 0:
            continue
        sh = shares_2010.get(cid)
        for label, phi in phis.items():
            gap = phi * (rel - 1.0)
            multiplicative = 1.0 + gap
            additive = 1.0 + gap * 2.5 / max(tfr, 0.8)
            mult = (1.0 - w_add) * multiplicative + w_add * additive
            if sh is not None and np.sum(sh * mult) > 0:
                group = tfr * mult / np.sum(sh * mult)
            else:
                group = tfr * mult
            for k, cat in enumerate(RELIGIONS):
                rows.append(dict(country_id=cid, religion=cat, phi=label, tfr_national=tfr,
                                 group_tfr=float(group[k]), normalised=sh is not None))
    return pd.DataFrame(rows)


def main():
    rel, off = load_prior()
    wrp, wpp, geo, nbrs = H.load_all(RAW, RAW / "ne_50m_admin_0_countries.zip")
    inputs = {}
    for y in DECADES:
        d = decade_inputs(y, wrp, wpp, geo, nbrs)
        if d is not None:
            inputs[y] = d
    print("Countries per decade start:", {y: len(v["ids"]) for y, v in inputs.items()})
    OUT.mkdir(parents=True, exist_ok=True)

    rows, cache = [], {}

    def record(mech, cfg, lam, y, pred):
        inp = inputs[y]
        rows.append(dict(decade=y, mechanism=mech, lam=lam, **cfg, **score(pred, inp)))

    for y, inp in inputs.items():                                  # persistence
        cache[("persistence", (), y)] = inp["sh0"]
        record("persistence", dict(phi=np.nan, psi=np.nan, w_add=np.nan, Hf=np.nan, gamma=np.nan, b_adj=np.nan),
               None, y, inp["sh0"])
    base_cfgs = [dict(zip(BASE_GRID, v), gamma=1.0, b_adj=1.0) for v in itertools.product(*BASE_GRID.values())]
    for cfg in base_cfgs:
        for mech in ("demo", "pool"):
            for y, inp in inputs.items():
                pred = run(inp, cfg, mech, rel, off)
                cache[(mech, _key(cfg), y)] = pred
                record(mech, cfg, None, y, pred)
    for vals in itertools.product(*BASE_GRID.values()):
        for gv in itertools.product(*GRAV_GRID.values()):
            cfg = dict(zip(BASE_GRID, vals), **dict(zip(GRAV_GRID, gv)))
            for y, inp in inputs.items():
                pred = run(inp, cfg, "grav", rel, off)
                cache[("grav", _key(cfg), y)] = pred
                record("grav", cfg, None, y, pred)
    res = pd.DataFrame(rows)

    def best_config(mech):
        d = res[(res.mechanism == mech) & res.decade.isin(TRAIN)]
        keys = list(BASE_GRID) + list(GRAV_GRID)
        means = d.groupby(keys).popw_tv_pp.mean()
        return dict(zip(keys, means.idxmin())) if mech != "persistence" else None

    chosen = {mech: best_config(mech) for mech in ("demo", "pool", "grav")}
    # momentum: on top of the chosen gravity model, pick lam on TRAIN, score on TEST
    g = chosen["grav"]
    mom_rows = []
    for lam in LAMBDAS:
        for y, inp in inputs.items():
            prev_inp = inputs.get(y - 10)
            prev_base = cache[("grav", _key(g), y - 10)] if prev_inp is not None else None
            pred = add_momentum(cache[("grav", _key(g), y)], inp, prev_inp, prev_base, lam)
            mom_rows.append(dict(decade=y, mechanism="momentum", lam=lam, **g, **score(pred, inp)))
    mom = pd.DataFrame(mom_rows)
    res = pd.DataFrame(rows + mom_rows)
    res.to_csv(OUT / "hindcast_by_decade.csv", index=False)

    def window(df, years):
        return df[df.decade.isin(years)]

    summary = []
    pers = res[res.mechanism == "persistence"]
    summary.append(dict(model="persistence", config="-",
                        train_popw_tv_pp=window(pers, TRAIN).popw_tv_pp.mean(),
                        test_popw_tv_pp=window(pers, TEST).popw_tv_pp.mean(),
                        test_mean_tv_pp=window(pers, TEST).mean_tv_pp.mean()))
    for mech in ("demo", "pool", "grav"):
        cfg = chosen[mech]
        d = res[res.mechanism == mech]
        m = np.ones(len(d), bool)
        for k, v in cfg.items():
            m &= np.isclose(d[k].to_numpy(float), v)
        d = d[m]
        summary.append(dict(model=mech, config=json.dumps({k: float(v) for k, v in cfg.items()}),
                            train_popw_tv_pp=window(d, TRAIN).popw_tv_pp.mean(),
                            test_popw_tv_pp=window(d, TEST).popw_tv_pp.mean(),
                            test_mean_tv_pp=window(d, TEST).mean_tv_pp.mean()))
    mm = mom.copy()
    lam_train = window(mm, TRAIN).groupby("lam").popw_tv_pp.mean().idxmin()
    for lam in (lam_train,):
        d = window(mom[mom.lam == lam], TEST)
        summary.append(dict(model=f"grav+momentum(lam={lam})", config=json.dumps(float(lam)),
                            train_popw_tv_pp=window(mom[mom.lam == lam], TRAIN).popw_tv_pp.mean(),
                            test_popw_tv_pp=d.popw_tv_pp.mean(), test_mean_tv_pp=d.mean_tv_pp.mean()))
    summary = pd.DataFrame(summary)
    summary.to_csv(OUT / "hindcast_summary.csv", index=False)
    print("Population-weighted total-variation error (pp), lower is better; chosen on TRAIN, scored on TEST")
    print(summary.round(3).to_string(index=False))
    lam_table = pd.DataFrame({lam: dict(train_popw=window(mom[mom.lam == lam], TRAIN).popw_tv_pp.mean(),
                                        test_popw=window(mom[mom.lam == lam], TEST).popw_tv_pp.mean())
                              for lam in LAMBDAS}).T.round(3)
    print("\nMomentum weight lam (on top of the chosen gravity model):")
    print(lam_table.to_string())
    gravity = json.loads((ROOT / "step5d_assumptions.json").read_text(encoding="utf8"))["gravity"]
    central = dict(phi=0.5, psi=0.0, w_add=0.0, Hf=50.0)
    proj = project_2010_2050(wrp, wpp, geo, nbrs, rel, off, central, gravity)
    ptab = projection_table(proj)
    ptab.to_csv(OUT / "projection_2010_2050.csv", index=False)
    shares_2010 = {r.country_id: np.array([getattr(r, f"share_{c}") for c in CATS])
                   for r in wrp[wrp.use & wrp.year.eq(2010)].itertuples()}
    gt = group_tfr_table(wpp, rel, {"low": 0.25, "central": 0.5, "high": 1.0}, 0.0, shares_2010)
    gt.to_csv(OUT / "group_tfr_predicted.csv", index=False)
    print(f"\nProjection 2010-2050 from WRP 2010 shares: {len(proj['ids'])} countries; "
          f"gravity arrivals for {proj['n_geo']} countries with geometry")
    tot = ptab.groupby("religion")[["inflow_2010_2050", "outflow_2010_2050", "net_2010_2050"]].sum() / 1e6
    print("Migration 2010-2050 by religion (millions of persons):")
    print(tot.round(2).sort_values("net_2010_2050").to_string())
    per = ptab.groupby("country_id").net_2010_2050.sum()
    losers = per.sort_values().head(8).index
    gainers = per.sort_values().tail(8).index[::-1]
    lead = (ptab.sort_values("outflow_2010_2050").groupby("country_id").tail(1).set_index("country_id"))
    print("Largest net emigration (persons) and religion most leaving:")
    print(pd.DataFrame({"net": per[losers].round(-3), "main_religion_leaving": lead.loc[losers, "religion"]}).to_string())
    print("Largest net immigration (persons) and religion most arriving:")
    arr = ptab.sort_values("inflow_2010_2050").groupby("country_id").tail(1).set_index("country_id")
    print(pd.DataFrame({"net": per[gainers].round(-3), "main_religion_arriving": arr.loc[gainers, "religion"]}).to_string())
    print("\nPredicted group TFR, central within-country gap (phi=0.5); national TFR 2020 from WPP:")
    show = gt[(gt.phi == "central") & gt.country_id.isin(["IND", "PAK", "NGA", "FRA", "USA", "IDN", "EGY", "ISR"])]
    print(show.pivot(index="country_id", columns="religion", values="group_tfr").round(2).to_string())
    print(f"\nWrote: {OUT / 'hindcast_summary.csv'}, {OUT / 'projection_2010_2050.csv'}, {OUT / 'group_tfr_predicted.csv'}")
    return res, summary, inputs, rel, off, chosen, cache


if __name__ == "__main__":
    main()
