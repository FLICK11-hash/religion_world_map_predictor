"""Step 7 maps without matplotlib or geopandas: SVG files plus one HTML gallery.

Run:  .\\.venv\\Scripts\\python.exe step7_maps_svg.py
Writes outputs/maps_step7_svg/ (git-ignored). Same map list and numbers as step7_make_maps.py (both use
step7_map_data.py); same colours and plate carree extent (-180..180, -59..85) as the Step 6 maps.
Open index.html in any browser.
"""
from __future__ import annotations

import html
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

import step7_map_data as MD
import wrp_history as H

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs' / 'maps_step7_svg'
W, HGT = 1400.0, 560.0
LAT_TOP, LAT_BOTTOM = 85.0, -59.0
MAP_CODE_FIXES = {'XKX': 'KOS'}
MISSING = '#E5E8EB'
CMAPS = {
    'YlGnBu': ['#ffffd9', '#edf8b1', '#c7e9b4', '#7fcdbb', '#41b6c4', '#1d91c0', '#225ea8', '#253494', '#081d58'],
    'Blues': ['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', '#2171b5', '#08519c', '#08306b'],
    'RdPu': ['#fff7f3', '#fde0dd', '#fcc5c0', '#fa9fb5', '#f768a1', '#dd3497', '#ae017e', '#7a0177', '#49006a'],
    'YlOrBr': ['#ffffe5', '#fff7bc', '#fee391', '#fec44f', '#fe9929', '#ec7014', '#cc4c02', '#993404', '#662506'],
    'viridis': ['#440154', '#482878', '#3e4989', '#31688e', '#26828e', '#1f9e89', '#35b779', '#6ece58', '#b5de2b', '#fde725'],
    'magma_r': ['#fcfdbf', '#fec287', '#fb8761', '#e55964', '#b5367a', '#812581', '#4f127b', '#1c1044', '#000004'],
    'RdBu_r': ['#053061', '#2166ac', '#4393c3', '#92c5de', '#d1e5f0', '#f7f7f7', '#fddbc7', '#f4a582', '#d6604d', '#b2182b', '#67001f'],
    'PuOr_r': ['#2d004b', '#542788', '#8073ac', '#b2abd2', '#d8daeb', '#f7f7f7', '#fee0b6', '#fdb863', '#e08214', '#b35806', '#7f3b08'],
    'PuOr': ['#7f3b08', '#b35806', '#e08214', '#fdb863', '#fee0b6', '#f7f7f7', '#d8daeb', '#b2abd2', '#8073ac', '#542788', '#2d004b'],
}


def _rgb(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def colour(cmap, t):
    stops = CMAPS[cmap]
    t = float(np.clip(t, 0, 1)) * (len(stops) - 1)
    i = min(int(t), len(stops) - 2)
    c = (1 - (t - i)) * _rgb(stops[i]) + (t - i) * _rgb(stops[i + 1])
    return '#' + ''.join(f'{int(round(v)):02x}' for v in c)


def load_shapes():
    """(map_id -> SVG path string with rings simplified to about a pixel, map_id -> country name)."""
    zp = ROOT / 'data' / 'raw' / 'ne_50m_admin_0_countries.zip'
    with zipfile.ZipFile(zp) as z:
        dbf = H._dbf_frame(z.read('ne_50m_admin_0_countries.dbf'))
        recs = H._shp_records(z.read('ne_50m_admin_0_countries.shp'))
    strip = lambda s: s.astype(str).str.replace('\x00', '', regex=False).str.strip()
    clean = lambda s: strip(s).str.upper()
    iso, adm = clean(dbf['ISO_A3']), clean(dbf['ADM0_A3'])
    cont = strip(dbf['CONTINENT'])
    ids = iso.where(iso.str.fullmatch('[A-Z]{3}'), adm)
    names = dict(zip(ids, strip(dbf['NAME'])))
    paths = {}
    for i, rings in enumerate(recs):
        if cont.iat[i] == 'Antarctica' or not rings:
            continue
        parts = paths.setdefault(ids.iat[i], [])
        for ring in rings:
            x = (ring[:, 0] + 180.0) / 360.0 * W
            y = (LAT_TOP - ring[:, 1]) / (LAT_TOP - LAT_BOTTOM) * HGT
            pts = np.round(np.column_stack([x, y]), 1)
            keep = np.ones(len(pts), bool)
            keep[1:] = np.any(np.abs(np.diff(pts, axis=0)) >= 0.6, axis=1)
            pts = pts[keep]
            if len(pts) < 3:
                continue
            parts.append('M' + ' L'.join(f'{a:.1f},{b:.1f}' for a, b in pts) + 'Z')
    return {k: ''.join(v) for k, v in paths.items() if v}, names


def _values_by_map_id(values):
    s = pd.Series(values).dropna()
    s.index = [MAP_CODE_FIXES.get(str(i), str(i)) for i in s.index]
    return s


def render(spec, shapes, names=None):
    vals = _values_by_map_id(spec['values'])
    esc = lambda x: html.escape(str(x))
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {HGT + 150:.0f}" role="img" '
           f'font-family="system-ui,-apple-system,Segoe UI,sans-serif">',
           f'<title>{esc(spec["title"])}</title>',
           f'<rect width="100%" height="100%" fill="white"/>',
           f'<text x="{W / 2}" y="30" text-anchor="middle" font-size="24" font-weight="700" fill="#111">{esc(spec["title"])}</text>',
           f'<text x="{W / 2}" y="54" text-anchor="middle" font-size="13" fill="#45545E">{esc(spec["subtitle"])}</text>',
           f'<g transform="translate(0,70)"><rect width="{W}" height="{HGT}" fill="#F5F8FB"/>']
    kind = spec['kind']
    for mid, d in shapes.items():
        v = vals.get(mid, None)
        if v is None or (isinstance(v, float) and not np.isfinite(v)):
            fill, tip = MISSING, 'no estimate'
        elif kind == 'categorical':
            fill = spec['colors'].get(str(v), MISSING)
            tip = MD.label(str(v))
        else:
            lo, hi = spec['vmin'], spec['vmax']
            fill = colour(spec['cmap'], (float(v) - lo) / (hi - lo))
            tip = f'{100 * float(v):.1f}%' if spec.get('percent') else f'{float(v):.3f}'
        name = (names or {}).get(mid, mid)
        out.append(f'<path d="{d}" fill="{fill}" stroke="#F3F4F5" stroke-width="0.4"><title>{esc(name)} ({esc(mid)}): '
                   f'{esc(tip)}</title></path>')
    out.append('</g>')
    y0 = HGT + 92
    if kind == 'categorical':
        cats = [c for c in spec['colors'] if c in set(vals.astype(str))] or list(spec['colors'])
        cats = cats + ['No estimate']
        colw = W / min(len(cats), 5)
        for i, c in enumerate(cats):
            x = (i % 5) * colw + 30
            yy = y0 + (i // 5) * 24
            col = spec['colors'].get(c, MISSING)
            out.append(f'<rect x="{x:.0f}" y="{yy - 12}" width="16" height="14" fill="{col}" stroke="#777" stroke-width="0.5"/>')
            out.append(f'<text x="{x + 24:.0f}" y="{yy}" font-size="14" fill="#222">{esc(MD.label(c))}</text>')
    else:
        x0, bw = W * 0.2, W * 0.6
        stops = ''.join(f'<stop offset="{t:.2f}" stop-color="{colour(spec["cmap"], t)}"/>' for t in np.linspace(0, 1, 21))
        out.append(f'<defs><linearGradient id="g">{stops}</linearGradient></defs>')
        out.append(f'<rect x="{x0}" y="{y0 - 14}" width="{bw}" height="16" fill="url(#g)" stroke="#999" stroke-width="0.5"/>')
        lo, hi = spec['vmin'], spec['vmax']
        for t in np.linspace(0, 1, 6):
            v = lo + t * (hi - lo)
            txt = f'{100 * v:.0f}' if spec.get('percent') else (f'{v:.2f}' if abs(hi - lo) < 5 else f'{v:.0f}')
            out.append(f'<text x="{x0 + t * bw:.0f}" y="{y0 + 20}" text-anchor="middle" font-size="13" fill="#333">{txt}</text>')
        out.append(f'<text x="{W / 2}" y="{y0 + 40}" text-anchor="middle" font-size="13" fill="#333">{esc(spec.get("colorbar", ""))}</text>')
    out.append(f'<text x="{W / 2}" y="{HGT + 145}" text-anchor="middle" font-size="12" fill="#58646F">{esc(spec.get("footnote", ""))}</text>')
    out.append('</svg>')
    return ''.join(out)


# --------------------------------------------------------------------------- world-shares chart
INK, INK2, GRID, DIVIDER, SURFACE = '#0b0b0b', '#52514e', '#e6e5e1', '#b9b8b2', '#ffffff'
REF_COLOUR, RANGE_COLOUR = '#2a78d6', '#8a8984'
KEY_YEARS = [2050, 2100, 2200, 2500, 3026]


def _xpos(year, x0, w):
    """Two-part time axis: 2020-2100 (WPP-based) takes 40% of the width, 2100-3030 (assumptions) 60%."""
    year = np.asarray(year, float)
    return x0 + w * np.where(year <= 2100, 0.4 * (year - 2020) / 80.0, 0.4 + 0.6 * (year - 2100) / 930.0)


def _ticks(top):
    """0..top in 3-6 equal steps of 1, 2 or 5 (then 2.5) x 10^k."""
    for allowed in ((1, 2, 5), (2.5,)):
        for n in (4, 5, 3, 6):
            step = top / n
            e = 10 ** np.floor(np.log10(step))
            if round(step / e, 6) in allowed:
                return np.linspace(0, top, n + 1)
    return np.linspace(0, top, 5)


def _nice_max(v):
    for m in (0.005, 0.01, 0.02, 0.03, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0):
        if v <= m:
            return m
    return 1.0


def world_chart(forecast=MD.FORECAST):
    """Small multiples: one panel per religion with the reference mean, its 5-95% band across runs and
    the range of all scenario means. Returns SVG text."""
    import json
    wt = pd.read_csv(forecast / 'global_share_by_scenario.csv')
    rep = json.loads((forecast / 'step7_report.json').read_text())
    ref, runs = rep.get('reference_scenario', 'stabilising'), rep.get('runs_per_scenario')
    nsc = wt.scenario.nunique()
    esc = lambda x: html.escape(str(x))
    Wc, Hc = 1400, 790
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {Wc} {Hc}" role="img" '
           f'font-family="system-ui,-apple-system,Segoe UI,sans-serif">',
           '<title>World religious composition by scenario, 2020-3030</title>',
           f'<rect width="100%" height="100%" fill="{SURFACE}"/>',
           f'<text x="30" y="36" font-size="24" font-weight="700" fill="{INK}">World religious composition, 2020-3030</text>',
           f'<text x="30" y="60" font-size="13.5" fill="{INK2}">Share of world population. Reference scenario ({esc(ref)}): '
           f'mean and 5-95% of {runs} runs. Grey: range of all {nsc} scenario means. Each panel has its own scale.</text>']
    lx, ly = 30, 90                                           # legend
    out += [f'<line x1="{lx}" y1="{ly}" x2="{lx + 26}" y2="{ly}" stroke="{REF_COLOUR}" stroke-width="2" stroke-linecap="round"/>',
            f'<text x="{lx + 34}" y="{ly + 4.5}" font-size="13" fill="{INK}">Reference mean</text>',
            f'<rect x="{lx + 160}" y="{ly - 7}" width="26" height="14" fill="{REF_COLOUR}" fill-opacity="0.16"/>',
            f'<text x="{lx + 194}" y="{ly + 4.5}" font-size="13" fill="{INK}">5-95% of runs (model and parameter uncertainty)</text>',
            f'<rect x="{lx + 520}" y="{ly - 7}" width="26" height="14" fill="{RANGE_COLOUR}" fill-opacity="0.22"/>',
            f'<text x="{lx + 554}" y="{ly + 4.5}" font-size="13" fill="{INK}">Range across scenarios (scenario uncertainty)</text>']
    pw, ph, gx, gy, top = 312.5, 300, 30, 26, 116
    ml, mr, mt, mb = 44, 52, 30, 40
    for k, g in enumerate(MD.GROUPS):
        col, row = k % 4, k // 4
        X0, Y0 = 30 + col * (pw + gx), top + row * (ph + gy)
        x0, y0, w, h = X0 + ml, Y0 + mt, pw - ml - mr, ph - mt - mb
        sub = wt[wt.religion.eq(g)]
        r = sub[sub.scenario.eq(ref)].sort_values('year')
        rng_ = sub.groupby('year')['mean'].agg(['min', 'max', 'idxmin', 'idxmax'])
        top_v = _nice_max(max(float(r.q95.max()), float(rng_['max'].max())) * 1.04)
        yv = lambda v: y0 + h * (1 - np.asarray(v, float) / top_v)
        out.append(f'<text x="{X0}" y="{Y0 + 16}" font-size="15" font-weight="600" fill="{INK}">{esc(MD.label(g))}</text>')
        for t in _ticks(top_v):
            yy = float(yv(t))
            out.append(f'<line x1="{x0}" y1="{yy:.1f}" x2="{x0 + w}" y2="{yy:.1f}" stroke="{GRID}" stroke-width="1"/>')
            out.append(f'<text x="{x0 - 6}" y="{yy + 4:.1f}" text-anchor="end" font-size="11" fill="{INK2}">'
                       f'{round(100 * t, 3):g}%</text>')
        xd = float(_xpos(2100, x0, w))
        out.append(f'<line x1="{xd:.1f}" y1="{y0}" x2="{xd:.1f}" y2="{y0 + h}" stroke="{DIVIDER}" stroke-width="1"/>')
        for yr in (2020, 2100, 2500, 3026):
            out.append(f'<text x="{float(_xpos(yr, x0, w)):.1f}" y="{y0 + h + 16}" text-anchor="middle" font-size="11" '
                       f'fill="{INK2}">{yr}</text>')
        yrs = rng_.index.to_numpy()
        xs = _xpos(yrs, x0, w)
        poly = lambda xa, lo, hi: ' '.join(f'{a:.1f},{b:.1f}' for a, b in zip(np.r_[xa, xa[::-1]], np.r_[yv(hi), yv(lo)[::-1]]))
        out.append(f'<polygon points="{poly(xs, rng_["min"].to_numpy(), rng_["max"].to_numpy())}" fill="{RANGE_COLOUR}" fill-opacity="0.22"/>')
        xr = _xpos(r.year.to_numpy(), x0, w)
        out.append(f'<polygon points="{poly(xr, r.q05.to_numpy(), r.q95.to_numpy())}" fill="{REF_COLOUR}" fill-opacity="0.16"/>')
        pts = ' '.join(f'{a:.1f},{b:.1f}' for a, b in zip(xr, yv(r['mean'].to_numpy())))
        out.append(f'<polyline points="{pts}" fill="none" stroke="{REF_COLOUR}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
        last = r.iloc[-1] if r.year.iloc[-1] != 3030 else r[r.year.eq(3026)].iloc[0]
        out.append(f'<text x="{float(_xpos(3026, x0, w)) + 6:.1f}" y="{float(yv(last["mean"])) + 4:.1f}" font-size="12" '
                   f'font-weight="600" fill="{INK}">{100 * last["mean"]:.1f}%</text>')
        for yr in KEY_YEARS:
            rr = r[r.year.eq(yr)]
            if rr.empty:
                continue
            rr = rr.iloc[0]
            lo_s, hi_s = sub.loc[rng_.loc[yr, 'idxmin'], 'scenario'], sub.loc[rng_.loc[yr, 'idxmax'], 'scenario']
            tip = (f'{MD.label(g)} {yr}: reference {100 * rr["mean"]:.1f}% (5-95% of runs {100 * rr.q05:.1f}-{100 * rr.q95:.1f}); '
                   f'scenario means {100 * rng_.loc[yr, "min"]:.1f}% ({lo_s}) to {100 * rng_.loc[yr, "max"]:.1f}% ({hi_s})')
            cx, cy = float(_xpos(yr, x0, w)), float(yv(rr['mean']))
            out.append(f'<g><circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="{REF_COLOUR}" stroke="{SURFACE}" stroke-width="2"/>'
                       f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="12" fill="transparent"><title>{esc(tip)}</title></circle></g>')
    out.append(f'<text x="30" y="{Hc - 34}" font-size="12" fill="{INK2}">Time axis in two parts: 2020-2100 (WPP-based demography) '
               f'uses 40% of the width; 2100-3030 (stated long-run assumptions) is compressed into 60%. The vertical line marks 2100.</text>')
    out.append(f'<text x="30" y="{Hc - 14}" font-size="12" fill="{INK2}">2500 and 3026 are speculative scenarios, not predictions. '
               f'Values: data/forecasts_step7/global_share_by_scenario.csv. Hover a dot for the numbers.</text>')
    out.append('</svg>')
    return ''.join(out)


def main():
    shapes, names = load_shapes()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'shares').mkdir(exist_ok=True)
    items = []
    for spec in MD.specs():
        svg = render(spec, shapes, names)
        path = OUT / f'{spec["name"]}.svg'
        path.write_text(svg, encoding='utf8')
        items.append((spec, path.relative_to(OUT).as_posix()))
    (OUT / 'world_shares_by_scenario.svg').write_text(world_chart(), encoding='utf8')
    # <object> (not <img>) keeps the hover titles working inside the gallery page
    fig = lambda p, t: (f'<figure><object type="image/svg+xml" data="{p}" aria-label="{html.escape(t)}"></object>'
                        f'<figcaption>{html.escape(t)}</figcaption></figure>')
    cards = fig('world_shares_by_scenario.svg', 'World religious composition by scenario, 2020-3030')
    cards += ''.join(fig(p, s['title']) for s, p in items if not p.startswith('shares/'))
    shares = ''.join(fig(p, s['title']) for s, p in items if p.startswith('shares/'))
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Step 7 maps</title><style>'
            'body{font:15px system-ui,-apple-system,Segoe UI,sans-serif;margin:24px;background:#fafafa;color:#111}'
            'figure{margin:0 0 28px;background:white;border:1px solid #e3e3e3;padding:8px}object{width:100%;height:auto;'
            'display:block;aspect-ratio:1400/710}figure:first-of-type object{aspect-ratio:1400/790}'
            'figcaption{font-size:13px;color:#555}h2{margin-top:36px}</style></head><body>'
            '<h1>Step 7 world maps</h1><p>Values are means over Monte Carlo runs from data/forecasts_step7. 2200 and later rest on '
            'long-run assumptions; 2500 and 3026 are speculative scenarios. Hover a country for its value.</p>'
            f'{cards}<h2>Religion shares</h2>{shares}</body></html>')
    (OUT / 'index.html').write_text(page, encoding='utf8')
    print(f'Wrote {len(items)} SVG maps, the world-shares chart and index.html to {OUT}')


if __name__ == '__main__':
    main()
