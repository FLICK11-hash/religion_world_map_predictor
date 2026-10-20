"""Charts for Step 5D and Step 5E as one HTML page: outputs/charts_step5/index.html.

Run from the step folder:  .\\.venv\\Scripts\\python.exe make_step5_charts.py
Needs only numpy and pandas (no extra packages). Open the HTML file in any browser (double-click).
Every chart has a table view underneath, so every number can be read without hovering.
Colours are the validated categorical palette from the dataviz reference: light and dark themes.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import step5d_diagnostics as dg
import wrp_history as H

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'data' / 'raw'
OUT = ROOT / 'outputs' / 'charts_step5'
SEARCH = [ROOT / 'data' / 'forecasts_step5d', ROOT / 'data' / 'hindcast_step5e', ROOT / 'results_step5']

CATS = ['Christianity', 'Islam', 'Hinduism', 'Buddhism', 'Judaism', 'Folk_Traditional', 'Other', 'Unaffiliated']
LABEL = {c: c for c in CATS}
LABEL['Folk_Traditional'] = 'Folk / traditional'
# Each religion keeps the same colour slot on every chart (colour follows the entity, never its rank).
SLOT = {c: f'f{i + 1}' for i, c in enumerate(CATS)}
SHORT = {'United States of America': 'USA', 'Russian Federation': 'Russia', 'Iran (Islamic Republic of)': 'Iran',
         'United Republic of Tanzania': 'Tanzania', 'Republic of Korea': 'South Korea',
         'Democratic Republic of the Congo': 'DR Congo', 'Bolivia (Plurinational State of)': 'Bolivia',
         'Venezuela (Bolivarian Republic of)': 'Venezuela'}
RAMP = ['#cde2fb', '#b7d3f6', '#9ec5f4', '#86b6ef', '#6da7ec', '#5598e7', '#3987e5', '#2a78d6',
        '#256abf', '#1c5cab', '#184f95', '#104281', '#0d366b']          # sequential, one hue (blue), 100 -> 700
DIV_GREY, DIV_BLUE, DIV_RED = '#f0efec', '#2a78d6', '#e34948'            # diverging pair with neutral midpoint
SURFACE, INK = '#fcfcfb', '#0b0b0b'

CSS = """
:root{color-scheme:light;--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--ink3:#898781;
--grid:#e1e0d9;--axis:#c3c2b7;--hair:rgba(11,11,11,.10);
--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--s4:#eda100;--s5:#e87ba4;--s6:#008300;--s7:#6250d6;--s8:#e34948}
@media (prefers-color-scheme: dark){:root:where(:not([data-theme="light"])){color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;
--ink:#f0efec;--ink2:#c3c2b7;--ink3:#898781;--grid:#2c2c2a;--axis:#383835;--hair:rgba(255,255,255,.10);
--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--s5:#d55181;--s6:#008300;--s7:#9085e9;--s8:#e66767}}
:root[data-theme="dark"]{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;
--ink:#f0efec;--ink2:#c3c2b7;--ink3:#898781;--grid:#2c2c2a;--axis:#383835;--hair:rgba(255,255,255,.10);
--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--s5:#d55181;--s6:#008300;--s7:#9085e9;--s8:#e66767}
body{margin:0;background:var(--page);color:var(--ink);font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:980px;margin:0 auto;padding:24px 16px 56px}
h1{font-size:24px;margin:0 0 6px} h2.section{font-size:13px;text-transform:uppercase;letter-spacing:.07em;color:var(--ink2);margin:32px 0 10px}
h3{font-size:16px;margin:0 0 4px} h4{font-size:13px;margin:0 0 2px;color:var(--ink)}
p.note{color:var(--ink2);font-size:13px;margin:4px 0 10px}
.card{background:var(--surface);border:1px solid var(--hair);border-radius:10px;padding:16px 18px;margin:0 0 16px}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:14px}
.panel{min-width:0}
svg{display:block;width:100%;height:auto;overflow:visible}
text{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;font-size:12px;fill:var(--ink2)}
.tick{fill:var(--ink3)} .cat{fill:var(--ink)} .val{fill:var(--ink)} .lab{fill:var(--ink2)}
.grid{stroke:var(--grid);stroke-width:1} .axis{stroke:var(--axis);stroke-width:1} .vline{stroke:var(--ink3);stroke-width:1}
.f1{fill:var(--s1)} .f2{fill:var(--s2)} .f3{fill:var(--s3)} .f4{fill:var(--s4)} .f5{fill:var(--s5)} .f6{fill:var(--s6)} .f7{fill:var(--s7)} .f8{fill:var(--s8)} .fn{fill:var(--ink3)}
.k1{stroke:var(--s1)} .k2{stroke:var(--s2)} .k3{stroke:var(--s3)} .k4{stroke:var(--s4)} .k5{stroke:var(--s5)} .k6{stroke:var(--s6)} .k7{stroke:var(--s7)} .k8{stroke:var(--s8)} .kn{stroke:var(--ink3)}
.sw1{background:var(--s1)} .sw2{background:var(--s2)} .sw3{background:var(--s3)} .sw4{background:var(--s4)} .sw5{background:var(--s5)} .sw6{background:var(--s6)} .sw7{background:var(--s7)} .sw8{background:var(--s8)} .swn{background:var(--ink3)}
.gap{stroke:var(--surface);stroke-width:2} .dot{stroke:var(--surface);stroke-width:2}
.line{fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round} .band{fill-opacity:.12;stroke:none}
.legend{list-style:none;padding:0;margin:4px 0 10px;display:flex;flex-wrap:wrap;gap:6px 18px;font-size:13px;color:var(--ink2)}
.legend .sw{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-1px}
details{margin-top:10px;font-size:12px;color:var(--ink2)} summary{cursor:pointer}
.tbl{overflow-x:auto} table{border-collapse:collapse;margin-top:6px;font-variant-numeric:tabular-nums}
th,td{padding:3px 10px;border-bottom:1px solid var(--grid);text-align:right;white-space:nowrap;color:var(--ink)}
th:first-child,td:first-child{text-align:left} th{color:var(--ink2);font-weight:600}
"""


# ----------------------------------------------------------------- data access
def find(name):
    for folder in SEARCH:
        p = folder / name
        if p.exists():
            return p
    return None


def load(name):
    p = find(name)
    return pd.read_csv(p, low_memory=False) if p else None


def load_json(name):
    p = find(name)
    return json.loads(p.read_text(encoding='utf8')) if p else {}


def country_names():
    p = RAW / 'WPP2024_Demographic_Indicators_Medium.csv.gz'
    if not p.exists():
        return {}
    w = pd.read_csv(p, usecols=['ISO3_code', 'Location'], low_memory=False).dropna().drop_duplicates('ISO3_code')
    return {r.ISO3_code: SHORT.get(r.Location, r.Location) for r in w.itertuples()}


def country_table():
    """Country x year means for the headline (needs mean_population for shares of world people)."""
    cu = load('country_year_uncertainty.csv')
    src = 'country_year_uncertainty.csv'
    if cu is None:
        cu = load('headline_country_shares.csv')
        src = 'headline_country_shares.csv'
    if cu is None:
        return None, None
    if 'mean_population' not in cu.columns:
        wpp = H.load_wpp(RAW)
        pop = wpp.drop_duplicates(['country_id', 'year']).set_index(['country_id', 'year'])['pop']
        keys = pd.MultiIndex.from_arrays([cu.country_id, cu.year])
        cu = cu.assign(mean_population=pop.reindex(keys).to_numpy(float))
        src += ' (population from WPP)'
    return cu, src


# ------------------------------------------------------------------ svg basics
_ids = [0]


def uid():
    _ids[0] += 1
    return f'g{_ids[0]}'


def esc(x):
    return html.escape(str(x), quote=True)


def fnum(v, d=1, sign=False):
    if v is None or not np.isfinite(v):
        return '–'
    s = f'{v:+.{d}f}' if sign else f'{v:.{d}f}'
    return s.replace('-', '−')


def nice_ticks(lo, hi, n=5):
    lo, hi = float(lo), float(hi)
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return [0.0, 1.0]
    if hi <= lo:
        hi = lo + 1.0
    span = hi - lo
    mag = 10 ** math.floor(math.log10(span / n))
    step = mag
    for m in (1, 2, 2.5, 5, 10):
        step = m * mag
        if span / step <= n:
            break
    start = math.floor(lo / step) * step
    stop = math.ceil(hi / step) * step
    ticks, t = [], start
    while t <= stop + step * 1e-9:
        ticks.append(round(t, 10))
        t += step
    return ticks


def tick_text(t, step):
    d = 0 if step >= 1 else (1 if step >= 0.1 else 2)
    return f'{t:.{d}f}'.replace('-', '−')


class Lin:
    def __init__(self, d0, d1, r0, r1):
        self.d0, self.d1, self.r0, self.r1 = float(d0), float(d1), float(r0), float(r1)
        if self.d1 == self.d0:
            self.d1 = self.d0 + 1.0

    def __call__(self, v):
        return self.r0 + (float(v) - self.d0) * (self.r1 - self.r0) / (self.d1 - self.d0)


def svg_open(w, h, title, desc):
    u = uid()
    return (f'<svg viewBox="0 0 {w} {h}" role="img" aria-labelledby="{u}t {u}d">'
            f'<title id="{u}t">{esc(title)}</title><desc id="{u}d">{esc(desc)}</desc>')


def hbar_path(xa, xb, ya, yb, r=4.0):
    """Bar from baseline xa to free end xb. Square at the baseline, rounded at the free end."""
    left, right = min(xa, xb), max(xa, xb)
    width, height = right - left, yb - ya
    rr = min(r, width / 2, height / 2) if (width >= 0.5 and height >= 0.5) else 0.0
    if rr <= 0:
        return f'M{left:.2f},{ya:.2f}H{right:.2f}V{yb:.2f}H{left:.2f}Z'
    if xb >= xa:
        return (f'M{left:.2f},{ya:.2f}H{right - rr:.2f}Q{right:.2f},{ya:.2f} {right:.2f},{ya + rr:.2f}'
                f'V{yb - rr:.2f}Q{right:.2f},{yb:.2f} {right - rr:.2f},{yb:.2f}H{left:.2f}Z')
    return (f'M{right:.2f},{ya:.2f}H{left + rr:.2f}Q{left:.2f},{ya:.2f} {left:.2f},{ya + rr:.2f}'
            f'V{yb - rr:.2f}Q{left:.2f},{yb:.2f} {left + rr:.2f},{yb:.2f}H{right:.2f}Z')


def hbars(categories, series, *, mode='group', title, desc, unit='', signed=False, w=900):
    """Horizontal bars. series: dicts with name, cls (f1..f8/fn) and values. mode: group | stack | single."""
    n, k = len(categories), len(series)
    vals = [np.nan_to_num(np.array(s['values'], float)) for s in series]
    if mode == 'stack':
        pos = np.sum([np.clip(v, 0, None) for v in vals], axis=0)
        neg = np.sum([np.clip(v, None, 0) for v in vals], axis=0)
        lo, hi = min(0.0, float(neg.min())), max(0.0, float(pos.max()))
    else:
        allv = np.concatenate(vals)
        lo, hi = min(0.0, float(allv.min())), max(0.0, float(allv.max()))
    span = (hi - lo) or 1.0
    top_end = hi + 0.14 * span                    # room for value labels past the longest bar
    if lo < 0:
        lo -= 0.14 * span                         # room for value labels left of negative bars
    share = unit.strip() == '%'
    if share:
        top_end = min(top_end, 100.0)             # a share axis stops at 100%
    ticks = nice_ticks(lo, top_end)
    if share:
        ticks = [t for t in ticks if t <= 100 + 1e-9]
    d0, d1 = ticks[0], ticks[-1]
    step = ticks[1] - ticks[0] if len(ticks) > 1 else 1
    lw = min(250, max(110, 7.2 * max(len(str(c)) for c in categories) + 12))
    bar_h = 16 if (mode == 'group' and k > 1) else 20
    if mode == 'group':
        band = max(30, k * (bar_h + 2) + 12)
    else:
        band = max(34, bar_h + 16)
    top, bottom = 8, 30
    plot_l, plot_r = 16 + lw + 12, w - 96
    H = top + n * band + bottom
    X = Lin(d0, d1, plot_l, plot_r)
    x0 = X(0)
    parts = [svg_open(w, H, title, desc)]
    for t in ticks:
        xx = X(t)
        cls = 'axis' if abs(t) < 1e-12 else 'grid'
        parts.append(f'<line x1="{xx:.1f}" y1="{top}" x2="{xx:.1f}" y2="{top + n * band}" class="{cls}"/>')
        parts.append(f'<text x="{xx:.1f}" y="{top + n * band + 16}" text-anchor="middle" class="tick">'
                     f'{tick_text(t, step)}{esc(unit)}</text>')
    for i, cat in enumerate(categories):
        y_top = top + i * band
        yc = y_top + band / 2
        parts.append(f'<text x="{16 + lw:.1f}" y="{yc:.1f}" text-anchor="end" dominant-baseline="middle" '
                     f'class="cat">{esc(cat)}</text>')
        if mode == 'stack':
            pos_i = float(sum(max(v[i], 0) for v in vals))
            neg_i = float(sum(min(v[i], 0) for v in vals))
            cum_p = cum_n = 0.0
            yy = y_top + (band - bar_h) / 2
            for s, v in zip(series, vals):
                val = float(v[i])
                if val == 0:
                    continue
                if val > 0:
                    a, b = cum_p, cum_p + val
                    cum_p = b
                else:
                    a, b = cum_n, cum_n + val
                    cum_n = b
                tip = f'{fnum(val, 2, signed)}{unit}'
                parts.append(f'<path d="{hbar_path(X(a), X(b), yy, yy + bar_h, r=0)}" class="{s["cls"]} gap">'
                             f'<title>{esc(cat)} · {esc(s["name"])}: {tip}</title></path>')
            tot = float(sum(v[i] for v in vals))
            if tot >= 0:
                tx, anchor = X(pos_i) + 6, 'start'
            else:
                tx, anchor = X(neg_i) - 6, 'end'
            parts.append(f'<text x="{tx:.1f}" y="{yc:.1f}" dominant-baseline="middle" text-anchor="{anchor}" '
                         f'class="val">{fnum(tot, 2, signed)}{esc(unit)}</text>')
        else:
            off = (band - k * (bar_h + 2) + 2) / 2
            for j, (s, v) in enumerate(zip(series, vals)):
                val = float(v[i])
                yy = y_top + off + j * (bar_h + 2)
                if val != 0:
                    parts.append(f'<path d="{hbar_path(x0, X(val), yy, yy + bar_h, r=4)}" class="{s["cls"]}">'
                                 f'<title>{esc(cat)} · {esc(s["name"])}: {fnum(val, 2, signed)}{esc(unit)}</title>'
                                 f'</path>')
                lx = X(val) + (6 if val >= 0 else -6)
                anchor = 'start' if val >= 0 else 'end'
                parts.append(f'<text x="{lx:.1f}" y="{yy + bar_h / 2:.1f}" dominant-baseline="middle" '
                             f'text-anchor="{anchor}" class="val">{fnum(val, 1 if abs(val) >= 10 else 2, signed)}'
                             f'{esc(unit)}</text>')
    parts.append('</svg>')
    return ''.join(parts)


def line_chart(x, series, *, title, desc, w=900, h=330, y_domain=None, x_ticks=None, unit='', bands=(),
               vlines=(), end_labels=True, x_name=''):
    """Line chart on one y-axis. series: dicts with name, cls (f1..f8/fn) and y. bands: lo/hi with cls."""
    xs = np.array(x, float)
    ys = [np.array(s['y'], float) for s in series]
    extra = [np.array(b[key], float) for b in bands for key in ('lo', 'hi')]
    allv = np.concatenate(ys + extra)
    allv = allv[np.isfinite(allv)]
    lo, hi = min(0.0, float(allv.min())), float(allv.max())
    if y_domain is not None:
        # A None bound means "fit to the data" on that side, e.g. y_domain=(0, None).
        lo = lo if y_domain[0] is None else float(y_domain[0])
        hi = hi if y_domain[1] is None else float(y_domain[1])
    yt = nice_ticks(lo, hi)
    ml, mr, mt, mb = 60, (118 if end_labels else 22), 14, 34
    X = Lin(xs.min(), xs.max(), ml, w - mr)
    Y = Lin(yt[0], yt[-1], h - mb, mt)
    spacing = (X(xs[1]) - X(xs[0])) if len(xs) > 1 else 40
    step = yt[1] - yt[0] if len(yt) > 1 else 1
    parts = [svg_open(w, h, title, desc)]
    for t in yt:
        yy = Y(t)
        cls = 'axis' if abs(t - yt[0]) < 1e-12 else 'grid'
        parts.append(f'<line x1="{ml}" y1="{yy:.1f}" x2="{w - mr}" y2="{yy:.1f}" class="{cls}"/>')
        parts.append(f'<text x="{ml - 8}" y="{yy + 4:.1f}" text-anchor="end" class="tick">'
                     f'{tick_text(t, step)}{esc(unit)}</text>')
    for vx, vtext in vlines:
        xx = X(vx)
        parts.append(f'<line x1="{xx:.1f}" y1="{mt}" x2="{xx:.1f}" y2="{h - mb}" class="vline"/>')
        parts.append(f'<text x="{xx + 5:.1f}" y="{mt + 11}" class="tick">{esc(vtext)}</text>')
    ticks = x_ticks if x_ticks is not None else [(v, f'{v:g}') for v in xs]
    for v, label in ticks:
        parts.append(f'<text x="{X(v):.1f}" y="{h - mb + 18}" text-anchor="middle" class="tick">{esc(label)}</text>')
    for b in bands:
        lo_v, hi_v = np.array(b['lo'], float), np.array(b['hi'], float)
        pts = [f'{X(a):.1f},{Y(v):.1f}' for a, v in zip(xs, hi_v)]
        pts += [f'{X(a):.1f},{Y(v):.1f}' for a, v in zip(xs[::-1], lo_v[::-1])]
        parts.append(f'<polygon points="{" ".join(pts)}" class="{b["cls"]} band"/>')
    for s, y in zip(series, ys):
        pts = [(X(a), Y(v)) for a, v in zip(xs, y) if np.isfinite(v)]
        if not pts:
            continue
        d = 'M' + ' L'.join(f'{px:.1f},{py:.1f}' for px, py in pts)
        parts.append(f'<path d="{d}" class="line k{s["cls"][1:]}"/>')
        px, py = pts[-1]
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" class="dot {s["cls"]}"/>')
        if end_labels:
            parts.append(f'<text x="{px + 9:.1f}" y="{py + 4:.1f}" class="lab">{esc(s["name"])}</text>')
    for a, row in zip(xs, zip(*ys)):
        text = '; '.join(f'{s["name"]} {fnum(v, 2)}{unit}' for s, v in zip(series, row))
        parts.append(f'<rect x="{X(a) - spacing / 2:.1f}" y="{mt}" width="{spacing:.1f}" height="{h - mb - mt}" '
                     f'fill="transparent"><title>{esc(x_name)}{esc(f"{a:g}")}: {esc(text)}</title></rect>')
    parts.append('</svg>')
    return ''.join(parts)


def _rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _hex(c):
    return '#' + ''.join(f'{round(v * 255):02x}' for v in c)


def _mix(a, b, t):
    ra, rb = _rgb(a), _rgb(b)
    return _hex(tuple(x + (y - x) * t for x, y in zip(ra, rb)))


def _lum(h):
    def ch(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in _rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(a, b):
    la, lb = _lum(a), _lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def text_on(bg):
    return INK if _contrast(INK, bg) >= _contrast(SURFACE, bg) else SURFACE


def heatmap(row_labels, col_labels, M, *, kind, title, desc, fmt_cell, w=900, cell_h=34, label_w=210):
    M = np.array(M, float)
    finite = M[np.isfinite(M)]
    vmin, vmax = float(finite.min()), float(finite.max())
    lim = float(np.max(np.abs(finite))) or 1.0

    def colour(v):
        if not np.isfinite(v):
            return '#e1e0d9'
        if kind == 'div':
            t = min(1.0, abs(v) / lim)
            return _mix(DIV_GREY, DIV_BLUE if v < 0 else DIV_RED, t)
        t = 0.0 if vmax == vmin else (v - vmin) / (vmax - vmin)
        return RAMP[int(round(min(1.0, max(0.0, t)) * (len(RAMP) - 1)))]

    cw = (w - label_w - 8) / len(col_labels)
    head = 46
    H = head + len(row_labels) * cell_h + 8
    parts = [svg_open(w, H, title, desc)]
    for j, c in enumerate(col_labels):
        cx = label_w + (j + 0.5) * cw
        words = c.split(' ')
        lines = [c] if len(words) == 1 else [' '.join(words[:1]), ' '.join(words[1:])]
        for li, txt in enumerate(lines[:2]):
            parts.append(f'<text x="{cx:.1f}" y="{18 + li * 14}" text-anchor="middle" class="cat">{esc(txt)}</text>')
    for i, r in enumerate(row_labels):
        y = head + i * cell_h
        parts.append(f'<text x="{label_w - 8}" y="{y + cell_h / 2:.1f}" text-anchor="end" dominant-baseline="middle" '
                     f'class="cat">{esc(r)}</text>')
        for j, c in enumerate(col_labels):
            v = M[i, j]
            col = colour(v)
            x = label_w + j * cw
            parts.append(f'<rect x="{x + 1:.1f}" y="{y + 1}" width="{cw - 2:.1f}" height="{cell_h - 2}" fill="{col}">'
                         f'<title>{esc(r)} · {esc(c)}: {esc(fmt_cell(v))}</title></rect>')
            parts.append(f'<text x="{x + cw / 2:.1f}" y="{y + cell_h / 2:.1f}" text-anchor="middle" '
                         f'dominant-baseline="middle" style="fill:{text_on(col)}">{esc(fmt_cell(v))}</text>')
    parts.append('</svg>')
    return ''.join(parts)


# ------------------------------------------------------------- page assembly
def legend_html(items):
    lis = ''.join(f'<li><span class="sw {"sw" + c[1:]}"></span>{esc(name)}</li>' for c, name in items)
    return f'<ul class="legend">{lis}</ul>'


def table_html(df, caption='Table view: every number in the chart'):
    t = df.to_html(index=False, border=0, float_format=lambda v: f'{v:.2f}', na_rep='–', escape=True)
    return f'<details><summary>{esc(caption)}</summary><div class="tbl">{t}</div></details>'


def card(title, note, body, legend=None, table=None):
    parts = [f'<section class="card"><h3>{esc(title)}</h3>']
    if note:
        parts.append(f'<p class="note">{note}</p>')
    if legend and len(legend) >= 2:
        parts.append(legend_html(legend))
    parts.append(body)
    if table is not None and len(table):
        parts.append(table_html(table))
    parts.append('</section>')
    return ''.join(parts)


def section(text):
    return f'<h2 class="section">{esc(text)}</h2>'


# ----------------------------------------------------------------- the charts
def card_hindcast_models(ctx):
    hs = load('hindcast_summary.csv')
    if hs is None:
        return None, 'hindcast_summary.csv missing'
    names = {'persistence': 'No change', 'demo': 'Demography (fertility, age)',
             'pool': 'Demography + migration pools', 'grav': 'Demography + migration gravity'}
    cats, train, test = [], [], []
    for r in hs.itertuples():
        m = str(r.model)
        if m.startswith('grav+momentum'):
            lam = re.search(r'lam=([0-9.]+)', m).group(1)
            name = f'Gravity + momentum (λ {lam})'
        else:
            name = names.get(m, m)
        cats.append(name)
        train.append(float(r.train_popw_tv_pp))
        test.append(float(r.test_popw_tv_pp))
    series = [dict(name='Training decades 1960–1980', cls='f1', values=train),
              dict(name='Test decades 1990–2000 (out of sample)', cls='f2', values=test)]
    body = hbars(cats, series, mode='group', title='Error by model, history tests',
                 desc='Population-weighted error in points for each model on training and test decades.')
    table = pd.DataFrame({'Model': cats, 'Training 1960–1980': train, 'Test 1990–2000': test})
    note = ('Population-weighted total-variation error in percentage points. Lower is better. Settings were chosen on '
            'the training decades only, so the test bars are out of sample. Demography helps a little; migration does '
            'not improve the test score; momentum helps early and hurts late.')
    return card('History tests: error by model (WRP shares, 1950–2010)', note, body,
                legend=[(s['cls'], s['name']) for s in series], table=table), None


def card_hindcast_decades(ctx):
    hd, hs = load('hindcast_by_decade.csv'), load('hindcast_summary.csv')
    if hd is None or hs is None:
        return None, 'hindcast_by_decade.csv or hindcast_summary.csv missing'
    hd = hd.copy()
    hd['decade'] = hd.decade.astype(int)

    def chosen(mech, model):
        cfg = json.loads(hs.loc[hs.model.eq(model), 'config'].iloc[0])
        d = hd[hd.mechanism.eq(mech)]
        for key in ('phi', 'psi', 'w_add', 'Hf', 'gamma', 'b_adj'):
            d = d[np.isclose(d[key].astype(float), float(cfg[key]))]
        return d.set_index('decade').popw_tv_pp.sort_index()

    pers = hd[hd.mechanism.eq('persistence')].set_index('decade').popw_tv_pp.sort_index()
    years = [int(y) for y in pers.index]
    demo = chosen('demo', 'demo').reindex(pers.index)
    grav = chosen('grav', 'grav').reindex(pers.index)
    mom = (hd[hd.mechanism.eq('momentum') & np.isclose(hd.lam.astype(float), 0.25)]
           .set_index('decade').popw_tv_pp.sort_index().reindex(pers.index))
    series = [dict(name='No change', cls='fn', y=pers.values),
              dict(name='Demography', cls='f1', y=demo.values),
              dict(name='Gravity migration', cls='f2', y=grav.values),
              dict(name='Gravity + momentum (λ 0.25)', cls='f3', y=mom.values)]
    svg = line_chart(years, series, title='Error by decade', desc='Population-weighted error by start decade and model.',
                     x_ticks=[(y, f'{y}s') for y in years], unit=' pp', y_domain=(0, None), end_labels=False,
                     x_name='Decade starting ')
    table = pd.DataFrame({'Decade start': years, **{s['name']: s['y'] for s in series}})
    note = ('Each point is a 10-year hindcast from that decade. Momentum (carrying the last decade\'s unexplained change '
            'forward) helps in 1960–1970 and hurts from 1980 on. That is why it is not in the headline.')
    return card('History tests: error by decade', note, svg, legend=[(s['cls'], s['name']) for s in series],
                table=table), None


def card_phi(ctx):
    phi = load('hindcast_phi_scan.csv')
    if phi is None:
        return None, 'hindcast_phi_scan.csv missing'
    x = phi.phi.astype(float).values
    series = [dict(name='Demography (fertility gap varied)', cls='f1', y=phi.pop_weighted_tv_pp.values),
              dict(name='No change', cls='fn', y=phi.persistence_pop_weighted_tv_pp.values)]
    svg = line_chart(x, series, title='Within-country fertility gap', desc='Error against the within-country gap fraction.',
                     x_ticks=[(0.0, '0'), (0.5, '0.5'), (1.0, '1')], unit=' pp', y_domain=(0, None), end_labels=False,
                     x_name='phi ')
    table = pd.DataFrame({'phi': x, **{s['name']: s['y'] for s in series}})
    spread = float(phi.pop_weighted_tv_pp.max() - phi.pop_weighted_tv_pp.min())
    note = (f'The error barely changes as the within-country fertility gap goes from 0 to 1 (a spread of {spread:.2f} '
            'points). So the 2010–2020 hindcast cannot say how big the gap is. The axis starts at zero to show that.')
    return card('Fertility gap: is it identified?', note, svg, legend=[(s['cls'], s['name']) for s in series],
                table=table), None


def card_pew_hindcast(ctx):
    d = load('hindcast_diagnostics.csv')
    if d is None:
        return None, 'hindcast_diagnostics.csv missing'
    cats = [LABEL[c] for c in d.religion]
    series = [dict(name='No change', cls='fn', values=d.persistence_error_pp.tolist()),
              dict(name='Demography only', cls='f1', values=d.demography_only_error_pp.tolist())]
    body = hbars(cats, series, mode='group', signed=True, unit=' pp', title='Pew 2010–2020 hindcast by religion',
                 desc='Global error in points by religion for no change and for demography only.')
    table = pd.DataFrame({'Religion': cats, 'No change (pp)': d.persistence_error_pp.values,
                          'Demography only (pp)': d.demography_only_error_pp.values})
    note = ('Error against Pew 2020, in points, global. Demography alone accounts for Islam\'s growth well. It does not '
            'explain Christianity\'s fall or the unaffiliated rise, which come from switching.')
    return card('Pew 2010 → 2020: demography against the 2020 data', note, body,
                legend=[(s['cls'], s['name']) for s in series], table=table), None


def card_world_shares(ctx):
    gsu = load('global_share_uncertainty.csv')
    if gsu is None:
        return None, 'global_share_uncertainty.csv missing'
    gsu = gsu[(gsu.year >= 2020) & (gsu.year <= 2200)]
    years = sorted(gsu.year.unique())
    panels, pivot = [], {'Year': [y for y in years if y in (2020, 2050, 2100, 2200)]}
    for c in CATS:
        g = gsu[gsu.religion.eq(c)].sort_values('year')
        mean, lo, hi = g['mean'].values * 100, g.q05.values * 100, g.q95.values * 100
        yr = g.year.astype(int).tolist()
        pick = {y: m for y, m in zip(yr, mean)}
        pivot[LABEL[c] + ' (%)'] = [pick.get(y) for y in pivot['Year']]
        svg = line_chart(yr, [dict(name=LABEL[c], cls=SLOT[c], y=mean)],
                         bands=[dict(lo=lo, hi=hi, cls=SLOT[c])], title=f'{LABEL[c]} world share',
                         desc=f'Mean world share of {LABEL[c]} with a 5–95% band, 2020 to 2200.', w=430, h=200,
                         x_ticks=[(2020, '2020'), (2050, '2050'), (2100, '2100'), (2200, '2200')],
                         unit='%', vlines=[(2100, 'assumptions')], end_labels=False, y_domain=None, x_name='Year ')
        a, b = pick.get(2020), pick.get(2050)
        head = f'{LABEL[c]}: {fnum(a, 1)}% in 2020 → {fnum(b, 1)}% in 2050'
        panels.append(f'<div class="panel"><h4>{esc(head)}</h4>{svg}</div>')
    body = f'<div class="grid2">{"".join(panels)}</div>'
    table = pd.DataFrame(pivot)
    note = (f'Headline scenario: {esc(ctx["headline"])}. Each religion has no conversion between groups, so its share '
            'moves only through fertility gaps and migration, plus population growth in each country. Lines are the '
            'mean over runs; bands are the 5–95% range. Each panel has its own scale. Years after 2100 rest on '
            'assumptions.')
    return card('World shares, headline forecast', note, body, table=table), None


def card_shift_share(ctx):
    cu, src = ctx['country']
    if cu is None:
        return None, 'country table missing'
    ss, _ = dg.shift_share(cu, CATS, 2020, 2050)
    ss = ss.set_index('religion').loc[CATS].reset_index()
    cats = [LABEL[c] for c in ss.religion]
    series = [dict(name='Within countries', cls='f1', values=ss.within_country_pp.tolist()),
              dict(name='Population weighting (which countries grow)', cls='f2',
                   values=ss.population_weighting_pp.tolist())]
    body = hbars(cats, series, mode='stack', signed=True, unit=' pp',
                 title='What changes each world share, 2020 to 2050',
                 desc='Within-country and population-weighting parts of each change, in percentage points.')
    table = pd.DataFrame({'Religion': cats, 'Total change (pp)': ss.change_pp.values,
                          'Within countries (pp)': ss.within_country_pp.values,
                          'Population weighting (pp)': ss.population_weighting_pp.values})
    note = (f'Source: {esc(src)}. A world share is an average of country shares, weighted by population. So a change '
            'splits into what happens inside countries and what happens because some countries grow faster than others. '
            'The total is shown at the bar tip. The unaffiliated decline is almost all population weighting.')
    return card('What changes each world share, 2020 to 2050', note, body,
                legend=[(s['cls'], s['name']) for s in series], table=table), None


def card_holders(ctx):
    cu, _ = ctx['country']
    if cu is None:
        return None, 'country table missing'
    h = dg.holders(cu, 2020, 'Unaffiliated').head(8)
    cats = [ctx['names'].get(i, i) for i in h.index]
    vals = (h.values * 100).tolist()
    series = [dict(name='Share of the world\'s unaffiliated people', cls='f1', values=vals)]
    body = hbars(cats, series, mode='single', unit='%', title='Who holds the world\'s unaffiliated people, 2020',
                 desc='Each country\'s share of the world\'s unaffiliated people in the 2020 start state.')
    table = pd.DataFrame({'Country': cats, 'Share of world unaffiliated people (%)': vals})
    note = ('Pew 2020 places most of China in "religiously unaffiliated". WRP history classifies much of the same '
            'population as folk religion. Which classification is right is a decision (see the classification charts '
            'at the end).')
    return card('Who holds the world\'s unaffiliated people, 2020', note, body, table=table), None


def card_decomposition(ctx):
    d = load('unaffiliated_decomposition.csv')
    if d is None:
        return None, 'unaffiliated_decomposition.csv missing'
    labels = ['Central (gaps, age offsets, migration)', 'No fertility gaps', 'No gaps, no migration',
              'No gaps, no migration, no age offsets']
    cats = labels[:len(d)]
    v20 = (d['Unaffiliated_2020'] * 100).tolist()
    v50 = (d['Unaffiliated_2050'] * 100).tolist()
    series = [dict(name='2020', cls='f1', values=v20), dict(name='2050', cls='f2', values=v50)]
    body = hbars(cats, series, mode='group', unit='%', title='Unaffiliated share with mechanisms switched off',
                 desc='Unaffiliated share in 2020 and 2050 for four single runs with mechanisms switched off.')
    table = pd.DataFrame({'Setting': cats, 'Unaffiliated 2020 (%)': v20, 'Unaffiliated 2050 (%)': v50})
    note = ('Single deterministic runs. The last row keeps every country\'s shares fixed, and the share still falls. So '
            'the fall comes from population weighting, not from change inside countries.')
    return card('Where the unaffiliated fall comes from', note, body,
                legend=[(s['cls'], s['name']) for s in series], table=table), None


def card_sensitivity(ctx):
    gbr, sp = load('global_share_by_run.csv'), load('scenario_parameters.csv')
    if gbr is None or sp is None:
        return None, 'global_share_by_run.csv or scenario_parameters.csv missing'
    head = ctx['headline']
    m = gbr[gbr.scenario.eq(head) & gbr.year.eq(2050)].merge(sp, on='run', suffixes=('', '_par'))
    names = [('psi', 'Age offset between groups (psi)'), ('phi', 'Within-country fertility gap (phi)'),
             ('w_add', 'Additive share of gaps (w_add)'), ('Hf', 'Years for gaps to converge (Hf)'),
             ('e0', 'Life expectancy (e0)'), ('tfr_shift', 'National fertility shift'),
             ('lam_nb', 'Neighbour weight in migration (lam_nb)'), ('lam_od', 'Matrix weight in migration (lam_od)'),
             ('lam', 'Continent weight in migration (lam)')]
    cols = ['Unaffiliated', 'Christianity', 'Islam']
    rows, M = [], []
    for key, label in names:
        if key in m and m[key].astype(float).nunique() > 1:
            rows.append(label)
            M.append([float(np.corrcoef(m[key].astype(float), m[c].astype(float))[0, 1]) for c in cols])
    svg = heatmap(rows, [LABEL[c] for c in cols], M, kind='div', title='Sensitivity of 2050 shares',
                  desc='Correlation of each parameter with each 2050 world share across headline runs.',
                  fmt_cell=lambda v: fnum(v, 2, sign=True), label_w=280)
    table = pd.DataFrame(M, columns=[LABEL[c] for c in cols])
    table.insert(0, 'Parameter', rows)
    n = int(m.run.nunique())
    note = (f'Correlation across the {n} headline runs. Blue = negative, red = positive. |r| below about 0.36 is within '
            'noise at this run count. Within-country fertility parameters move the unaffiliated share; migration weights '
            'barely do.')
    return card('Which settings move the 2050 shares', note, svg, table=table), None


def card_migration_religion(ctx):
    mig = load('migration_by_religion.csv')
    if mig is None:
        return None, 'migration_by_religion.csv missing'
    m = mig[mig.period.eq('2020-2100')].groupby('religion')[['inflow_persons', 'outflow_persons']].sum() / 1e6
    m = m.reindex(CATS)
    cats = [LABEL[c] for c in m.index]
    series = [dict(name='Inflow', cls='f1', values=m.inflow_persons.tolist()),
              dict(name='Outflow', cls='f2', values=m.outflow_persons.tolist())]
    body = hbars(cats, series, mode='group', unit=' M', title='Migration 2020–2100 by religion',
                 desc='Inflow and outflow by religion in millions of people, 2020 to 2100.')
    table = pd.DataFrame({'Religion': cats, 'Inflow (millions)': m.inflow_persons.values,
                          'Outflow (millions)': m.outflow_persons.values,
                          'Net (millions)': (m.inflow_persons - m.outflow_persons).values})
    note = ('Who moves, by religion. Leavers carry their own country\'s religious mix. Arrivals come from the gravity '
            'matrix (geography only, no bilateral table), so destination-level mixes are approximate.')
    return card('Migration by religion, 2020–2100', note, body,
                legend=[(s['cls'], s['name']) for s in series], table=table), None


def card_migration_countries(ctx):
    mig = load('migration_by_religion.csv')
    if mig is None:
        return None, 'migration_by_religion.csv missing'
    net = mig[mig.period.eq('2020-2100')].groupby('country_id').net_persons.sum() / 1e6
    down = net[net < 0].sort_values().head(8)
    up = net[net > 0].sort_values(ascending=False).head(8)
    sel = pd.concat([up, down]).sort_values(ascending=False)
    cats = [ctx['names'].get(i, i) for i in sel.index]
    series = [dict(name='Net immigration', cls='f1', values=[max(v, 0) for v in sel.values]),
              dict(name='Net emigration', cls='f8', values=[min(v, 0) for v in sel.values])]
    body = hbars(cats, series, mode='stack', signed=True, unit=' M', title='Largest net migration, 2020–2100',
                 desc='Largest net immigration and emigration by country, millions of people, 2020 to 2100.')
    table = pd.DataFrame({'Country': cats, 'Net migration 2020–2100 (millions)': sel.values})
    note = ('Net migration, millions of people, summed over religions. Blue = net immigration, red = net emigration. '
            'These totals come from the WPP projection, so they are not model choices.')
    return card('Largest net migration, 2020–2100', note, body,
                legend=[(s['cls'], s['name']) for s in series], table=table), None


def card_projection(ctx):
    proj = load('projection_2010_2050.csv')
    if proj is None:
        return None, 'projection_2010_2050.csv missing'
    wpp = H.load_wpp(RAW)
    p10 = wpp[wpp.year.eq(2010)].drop_duplicates('country_id').set_index('country_id')['pop']
    p50 = wpp[wpp.year.eq(2050)].drop_duplicates('country_id').set_index('country_id')['pop']
    countries = sorted(set(proj.country_id) & set(p10.index) & set(p50.index))
    proj = proj[proj.country_id.isin(countries)]
    w10 = p10.reindex(countries).values
    w50 = p50.reindex(countries).values
    w10, w50 = w10 / w10.sum(), w50 / w50.sum()
    s10, s50 = [], []
    for c in CATS:
        g = proj[proj.religion.eq(c)].set_index('country_id').reindex(countries)
        s10.append(float(np.sum(w10 * g.share_2010.fillna(0).values)) * 100)
        s50.append(float(np.sum(w50 * g.share_2050.fillna(0).values)) * 100)
    cats = [LABEL[c] for c in CATS]
    series = [dict(name='2010 (WRP start)', cls='f1', values=s10), dict(name='2050 (projection)', cls='f2', values=s50)]
    body = hbars(cats, series, mode='group', unit='%', title='WRP 2010 shares projected to 2050',
                 desc='World shares among WRP countries in 2010 and projected 2050.')
    table = pd.DataFrame({'Religion': cats, '2010 (%)': s10, '2050 (%)': s50})
    note = (f'Central settings, using WRP 2010 shares for the {len(countries)} countries WRP covers, weighted by WPP '
            'population. This projection uses WRP categories, so folk religion is larger than in the Pew start.')
    return card('Projection from WRP 2010 to 2050', note, body,
                legend=[(s['cls'], s['name']) for s in series], table=table), None


def card_group_tfr(ctx):
    g = load('group_tfr_predicted.csv')
    if g is None:
        return None, 'group_tfr_predicted.csv missing'
    g = g[g.phi.eq('central')]
    picks = ['IND', 'PAK', 'BGD', 'NGA', 'EGY', 'IDN', 'FRA', 'DEU', 'USA', 'ISR', 'CHN', 'BRA']
    picks = [c for c in picks if c in set(g.country_id)]
    rows = [ctx['names'].get(c, c) for c in picks]
    M = np.array([[float(g[(g.country_id.eq(c)) & g.religion.eq(r)].group_tfr.iloc[0]) for r in CATS] for c in picks])
    svg = heatmap(rows, [LABEL[c] for c in CATS], M, kind='seq', title='Predicted fertility by religion',
                  desc='Predicted children per woman by country and religion, central within-country gap.',
                  fmt_cell=lambda v: fnum(v, 2))
    table = pd.DataFrame(M, columns=[LABEL[c] for c in CATS])
    table.insert(0, 'Country', rows)
    note = ('Predicted children per woman by religion, central within-country gap. These are model assumptions: Pew\'s '
            'global group ratios, shrunk by the history tests. They are not measured group fertility. Buddhism, Other and '
            'Unaffiliated share one Pew input (1.7), so their columns match in every row. All group inputs are still '
            'unverified against the Pew report. Darker = higher.')
    return card('Predicted fertility by religion, selected countries', note, svg, table=table), None


def card_china(ctx):
    cu, _ = ctx['country']
    wrp = H.check_population_match(H.load_wrp(RAW), H.load_wpp(RAW))
    ch = wrp[wrp.country_id.eq('CHN') & wrp.valid & (wrp.year <= 2010)].sort_values('year')
    if cu is None or ch.empty:
        return None, 'China rows missing'
    row = ch.iloc[-1]
    pew = cu[(cu.country_id.eq('CHN')) & (cu.year.eq(2020))]
    if pew.empty:
        return None, 'China 2020 row missing'
    pew = pew.iloc[0]
    wv = [float(row[f'share_{c}']) * 100 for c in CATS]
    pv = [float(pew[f'mean_{c}']) * 100 for c in CATS]
    cats = [LABEL[c] for c in CATS]
    series = [dict(name='Pew 2020 (model start)', cls='f1', values=pv), dict(name=f'WRP {int(row.year)}', cls='f2', values=wv)]
    body = hbars(cats, series, mode='group', unit='%', title='China: two classifications',
                 desc='China shares in the Pew 2020 start state and in WRP 2010.')
    table = pd.DataFrame({'Religion': cats, 'Pew 2020 start state (%)': pv, f'WRP {int(row.year)} (%)': wv})
    note = ('The same population classified two ways. Pew 2020 puts most of China in "unaffiliated" and very little in '
            'folk religion. WRP puts a large share in folk religion. This choice drives the unaffiliated headline.')
    return card('China: Pew 2020 against WRP 2010', note, body,
                legend=[(s['cls'], s['name']) for s in series], table=table), None


def card_world_classification(ctx):
    d = load('hindcast_diagnostics.csv')
    if d is None:
        return None, 'hindcast_diagnostics.csv missing'
    wpp = H.load_wpp(RAW)
    wrp = H.check_population_match(H.load_wrp(RAW), wpp)
    use = wrp[wrp.valid & wrp.pop_ok & wrp.year.eq(2010) & wrp.country_id.notna()].drop_duplicates('country_id')
    pop = wpp[wpp.year.eq(2010)].drop_duplicates('country_id').set_index('country_id')['pop']
    w = np.nan_to_num(pop.reindex(use.country_id).values.astype(float))
    w = w / w.sum()

    def wrp_world(c):
        return float(np.sum(w * use[f'share_{c}'].fillna(0).values)) * 100

    rows = {'Folk_Traditional': 'Folk / traditional', 'Unaffiliated': 'Unaffiliated'}
    dd = d.set_index('religion')
    cats = list(rows.values())
    keys = list(rows.keys())
    p10 = [float(dd.loc[k, 'global_share_pew2010']) * 100 for k in keys]
    p20 = [float(dd.loc[k, 'global_share_pew2020']) * 100 for k in keys]
    wr = [wrp_world(k) for k in keys]
    series = [dict(name='Pew 2010', cls='f3', values=p10), dict(name='Pew 2020 (model start)', cls='f1', values=p20),
              dict(name=f'WRP 2010 ({len(use)} WRP countries)', cls='f2', values=wr)]
    body = hbars(cats, series, mode='group', unit='%', title='World folk religion and unaffiliated, two classifications',
                 desc='World shares of folk religion and unaffiliated in Pew 2010, Pew 2020 and WRP 2010.')
    table = pd.DataFrame({'Category': cats, 'Pew 2010 (%)': p10, 'Pew 2020 (%)': p20,
                          f'WRP 2010, {len(use)} countries (%)': wr})
    note = ('The two sources classify folk religion differently. WRP 2010 has about 11% folk religion and 11% unaffiliated. '
            'Pew has about 1% folk and 22–24% unaffiliated. Most of the gap is in China and a few East Asian and African '
            'countries. The 1950–2010 history tests use the WRP categories, so their findings do not carry over to the '
            'Pew start state.')
    return card('World classifications: Pew against WRP', note, body,
                legend=[(s['cls'], s['name']) for s in series], table=table), None


SECTIONS = [
    ('Step 5E: testing the mechanisms against history', [card_hindcast_models, card_hindcast_decades, card_phi,
                                                         card_pew_hindcast]),
    ('Step 5D: the headline forecast', [card_world_shares, card_shift_share, card_holders, card_decomposition,
                                        card_sensitivity]),
    ('Migration', [card_migration_religion, card_migration_countries]),
    ('Projection and fertility', [card_projection, card_group_tfr]),
    ('Classification: the decision still open', [card_china, card_world_classification]),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--from', dest='src', default=None, help='folder with the output CSV files (optional)')
    args = ap.parse_args()
    if args.src:
        SEARCH.insert(0, Path(args.src))
    OUT.mkdir(parents=True, exist_ok=True)
    report = load_json('step5d_report.json')
    p = find('step5d_report.json')
    cu, src = country_table()
    ctx = dict(headline=report.get('headline_scenario', 'demography_only'), names=country_names(),
               country=(cu, src), source=p.parent.name if p else 'no step5d output found')
    body, skipped, made = [], [], 0
    for title, builders in SECTIONS:
        body.append(section(title))
        for fn in builders:
            try:
                html_card, why = fn(ctx)
            except Exception as exc:                       # keep going: one missing file must not stop the page
                html_card, why = None, f'{type(exc).__name__}: {exc}'
            if html_card:
                body.append(html_card)
                made += 1
            else:
                skipped.append(f'{fn.__name__}: {why}')
    head = (f'<h1>Step 5 results: charts</h1><p class="note">Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC '
            f'from <code>{esc(ctx["source"])}</code>. Headline scenario: <code>{esc(ctx["headline"])}</code>. '
            'Shares are percentages of the world population unless a card says otherwise. Every chart has a table view '
            'underneath with the numbers. Each religion keeps its colour in the world-share charts. Elsewhere colour only '
            'tells series apart, and the legend names them. The dark theme follows your system setting.</p>')
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Step 5 results: charts</title><style>' + CSS + '</style></head><body><main>'
            + head + ''.join(body) + '</main></body></html>')
    target = OUT / 'index.html'
    target.write_text(page, encoding='utf-8')
    print(f'Wrote {made} charts to {target}')
    print(f'Open it with a double-click, or paste this path into your browser:\n  {target}')
    for s in skipped:
        print('Skipped -', s)


if __name__ == '__main__':
    main()
