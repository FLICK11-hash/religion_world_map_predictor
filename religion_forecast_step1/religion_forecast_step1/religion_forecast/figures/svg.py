"""Step 7 maps without matplotlib or geopandas: SVG files plus one HTML gallery.

Run:  .\\.venv\\Scripts\\python.exe run.py figures
Writes outputs/figures/ (git-ignored). Same map list and numbers as run.py figures --png (both use
religion_forecast/figures/specs.py); same colours and plate carree extent (-180..180, -59..85) as the Step 6 maps.
Open index.html in any browser.
"""
from __future__ import annotations

import html
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from religion_forecast.figures import charts as CH
from religion_forecast.figures import specs as MD
from religion_forecast import sources as H
from religion_forecast import config

OUT = config.FIGURES
W, HGT = 1400.0, 560.0
LAT_TOP, LAT_BOTTOM = 85.0, -59.0
MAP_CODE_FIXES, MISSING = MD.MAP_CODE_FIXES, MD.MISSING
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
    """Returns (paths, names, dots).

    paths  map_id -> an SVG path, rings simplified to about a pixel
    names  map_id -> country name, for the hover text
    dots   map_id -> (x, y) for countries too small to survive simplification. Singapore, Malta,
           Mauritius and twenty-odd other small states are well under a pixel across at this
           width, so they would silently vanish from every map. They are drawn as a marked point
           instead, which is what a printed atlas does, so that every modelled country is visible.
    """
    zp = config.RAW / 'ne_50m_admin_0_countries.zip'
    with zipfile.ZipFile(zp) as z:
        dbf = H._dbf_frame(z.read('ne_50m_admin_0_countries.dbf'))
        recs = H._shp_records(z.read('ne_50m_admin_0_countries.shp'))
    strip = lambda s: s.astype(str).str.replace('\x00', '', regex=False).str.strip()
    clean = lambda s: strip(s).str.upper()
    iso, adm = clean(dbf['ISO_A3']), clean(dbf['ADM0_A3'])
    cont = strip(dbf['CONTINENT'])
    ids = iso.where(iso.str.fullmatch('[A-Z]{3}'), adm)
    names = dict(zip(ids, strip(dbf['NAME'])))
    paths, centre = {}, {}
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
        big = max(rings, key=lambda r: len(r))
        centre.setdefault(ids.iat[i], (float((big[:, 0].mean() + 180.0) / 360.0 * W),
                                       float((LAT_TOP - big[:, 1].mean()) / (LAT_TOP - LAT_BOTTOM) * HGT)))
    out = {k: ''.join(v) for k, v in paths.items() if v}
    dots = {k: xy for k, xy in centre.items() if k not in out}
    return out, names, dots


def _values_by_map_id(values):
    s = pd.Series(values).dropna()
    s.index = [MAP_CODE_FIXES.get(str(i), str(i)) for i in s.index]
    return s


def render(spec, shapes, names=None, dots=None):
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

    def fill_for(v):
        """Colour and hover text for one country's value."""
        if v is None or (isinstance(v, float) and not np.isfinite(v)):
            return MISSING, 'no estimate'
        if kind == 'categorical':
            return spec['colors'].get(str(v), MISSING), MD.label(str(v))
        lo, hi = spec['vmin'], spec['vmax']
        return (colour(spec['cmap'], (float(v) - lo) / (hi - lo)),
                f'{100 * float(v):.1f}%' if spec.get('percent') else f'{float(v):.3f}')

    for mid, d in shapes.items():
        fill, tip = fill_for(vals.get(mid, None))
        name = (names or {}).get(mid, mid)
        out.append(f'<path d="{d}" fill="{fill}" stroke="#F3F4F5" stroke-width="0.4"><title>{esc(name)} ({esc(mid)}): '
                   f'{esc(tip)}</title></path>')
    for mid, (cx, cy) in sorted((dots or {}).items()):
        if mid not in vals.index:
            continue
        fill, tip = fill_for(vals.get(mid))
        name = (names or {}).get(mid, mid)
        out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="3.2" fill="{fill}" stroke="#52514e" '
                   f'stroke-width="0.7"><title>{esc(name)} ({esc(mid)}): {esc(tip)} - too small to draw to '
                   f'scale, marked as a point</title></circle>')
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


def main(argv=None):
    shapes, names, dots = load_shapes()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'shares').mkdir(exist_ok=True)
    items = []
    for spec in MD.specs():
        svg = render(spec, shapes, names, dots)
        path = OUT / f'{spec["name"]}.svg'
        path.write_text(svg, encoding='utf8')
        items.append((spec, path.relative_to(OUT).as_posix()))
    charts = CH.build_all(OUT, log=lambda *_: None)
    # <object> (not <img>) keeps the hover titles working inside the gallery page
    fig = lambda p, t: (f'<figure><object type="image/svg+xml" data="{p}" aria-label="{html.escape(t)}"></object>'
                        f'<figcaption>{html.escape(t)}</figcaption></figure>')
    cards = ''.join(fig(c, c.replace('_', ' ')[:-4].capitalize()) for c in charts)
    cards += ''.join(fig(p, s['title']) for s, p in items if not p.startswith('shares/'))
    shares = ''.join(fig(p, s['title']) for s, p in items if p.startswith('shares/'))
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Step 7 maps</title><style>'
            'body{font:15px system-ui,-apple-system,Segoe UI,sans-serif;margin:24px;background:#fafafa;color:#111}'
            'figure{margin:0 0 28px;background:white;border:1px solid #e3e3e3;padding:8px}object{width:100%;height:auto;'
            'display:block;aspect-ratio:1400/710}figure:first-of-type object{aspect-ratio:1400/790}'
            'figcaption{font-size:13px;color:#555}h2{margin-top:36px}</style></head><body>'
            '<h1>Religious composition: figures</h1><p>Values are means over Monte Carlo runs from data/projections. 2200 and later rest on '
            'long-run assumptions; 2500 and 3026 are speculative scenarios. Hover a country for its value.</p>'
            f'{cards}<h2>Religion shares</h2>{shares}</body></html>')
    (OUT / 'index.html').write_text(page, encoding='utf8')
    print(f'Wrote {len(items)} maps and {len(charts)} charts to {OUT}')


if __name__ == '__main__':
    main()
