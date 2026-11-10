"""Publication charts, as SVG, from the files a run writes.

SVG rather than raster, because it is a vector format that journals accept directly and because it
needs no plotting library: the whole module is numpy, pandas and string formatting, so it runs
wherever the model runs. `mpl.py` draws the same maps as PNG for anyone who prefers matplotlib.

Design follows the project's data-visualisation reference: one hue per religion everywhere, a
legend whenever more than one series is drawn, values written as text rather than read off a
colour, hairline gridlines, no second y-axis. The religion palette and the colour-vision checks
behind it are documented in `specs.py`.
"""
from __future__ import annotations

import html
import json

import numpy as np
import pandas as pd

from religion_forecast import config
from religion_forecast.figures import specs as MD

INK, INK2, INK3 = '#0b0b0b', '#52514e', '#8a8984'
GRID, DIVIDER, SURFACE = '#e6e5e1', '#b9b8b2', '#ffffff'
ACCENT, NEUTRAL, GOOD, BAD = '#2a78d6', '#8a8984', '#1baf7a', '#a32a28'
CATS = MD.GROUPS


def esc(x) -> str:
    return html.escape(str(x))


class Canvas:
    """A minimal SVG page: a title block, then panels placed by hand."""

    def __init__(self, width: float, height: float, title: str, subtitle: str = '', footnote: str = ''):
        self.w, self.h = width, height
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" role="img" '
            f'font-family="system-ui,-apple-system,Segoe UI,sans-serif">',
            f'<title>{esc(title)}</title>',
            f'<rect width="100%" height="100%" fill="{SURFACE}"/>',
            f'<text x="30" y="34" font-size="22" font-weight="700" fill="{INK}">{esc(title)}</text>']
        if subtitle:
            self.parts.append(f'<text x="30" y="58" font-size="13.5" fill="{INK2}">{esc(subtitle)}</text>')
        self.footnote = footnote

    def add(self, s: str):
        self.parts.append(s)

    def text(self, x, y, s, size=12, fill=INK2, anchor='start', weight=None):
        w = f' font-weight="{weight}"' if weight else ''
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
                 f'text-anchor="{anchor}"{w}>{esc(s)}</text>')

    def legend(self, x, y, items, size=12.5):
        """items: (label, colour) pairs. Identity is never colour alone: every chart that uses this
        also writes its values as text."""
        for label, colour in items:
            self.add(f'<rect x="{x:.1f}" y="{y - 8:.1f}" width="13" height="13" rx="2" fill="{colour}"/>')
            self.text(x + 19, y + 3, label, size=size, fill=INK)
            x += 19 + 7.0 * len(str(label)) + 20
        return x

    def save(self, path):
        if self.footnote:
            for i, line in enumerate(self.footnote.split('\n')):
                self.text(30, self.h - 32 + 16 * i, line, size=11.5, fill=INK3)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(''.join(self.parts) + '</svg>', encoding='utf8')
        return path


class Panel:
    """A rectangular plot area with linear scales and the usual furniture."""

    def __init__(self, cv: Canvas, x, y, w, h, xlim, ylim, title='', xlab='', ylab=''):
        self.cv, self.x, self.y, self.w, self.h = cv, x, y, w, h
        self.x0, self.x1 = xlim
        self.y0, self.y1 = ylim
        if title:
            cv.text(x, y - 30, title, size=14, fill=INK, weight=600)
        if ylab:
            cv.text(x, y - 13, ylab, size=11.5, fill=INK2)
        self.xlab = xlab

    def px(self, v):
        return self.x + self.w * (np.asarray(v, float) - self.x0) / max(self.x1 - self.x0, 1e-12)

    def py(self, v):
        return self.y + self.h * (1 - (np.asarray(v, float) - self.y0) / max(self.y1 - self.y0, 1e-12))

    @staticmethod
    def _fmt(fmt, t):
        return fmt(t) if callable(fmt) else fmt.format(t)

    def grid_y(self, ticks, fmt='{:g}'):
        for t in ticks:
            yy = float(self.py(t))
            self.cv.add(f'<line x1="{self.x:.1f}" y1="{yy:.1f}" x2="{self.x + self.w:.1f}" y2="{yy:.1f}" '
                        f'stroke="{GRID}" stroke-width="1"/>')
            self.cv.text(self.x - 7, yy + 4, self._fmt(fmt, t), size=11, fill=INK2, anchor='end')

    def grid_x(self, ticks, fmt='{:g}'):
        for t in ticks:
            xx = float(self.px(t))
            self.cv.text(xx, self.y + self.h + 16, self._fmt(fmt, t), size=11, fill=INK2, anchor='middle')

    def axis_line(self):
        self.cv.add(f'<line x1="{self.x:.1f}" y1="{self.y + self.h:.1f}" x2="{self.x + self.w:.1f}" '
                    f'y2="{self.y + self.h:.1f}" stroke="{DIVIDER}" stroke-width="1"/>')

    def line(self, xs, ys, colour, width=2.0, opacity=1.0, dash=None):
        pts = ' '.join(f'{a:.1f},{b:.1f}' for a, b in zip(self.px(xs), self.py(ys)))
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.cv.add(f'<polyline points="{pts}" fill="none" stroke="{colour}" stroke-width="{width}" '
                    f'stroke-linejoin="round" stroke-linecap="round" opacity="{opacity}"{d}/>')

    def band(self, xs, lo, hi, colour, opacity=0.16):
        xa, = (np.asarray(xs, float),)
        pts = ' '.join(f'{a:.1f},{b:.1f}' for a, b in
                       zip(np.r_[self.px(xa), self.px(xa[::-1])], np.r_[self.py(hi), self.py(lo)[::-1]]))
        self.cv.add(f'<polygon points="{pts}" fill="{colour}" fill-opacity="{opacity}"/>')

    def dot(self, x, y, colour, r=4.5, tip=None):
        c = (f'<circle cx="{float(self.px(x)):.1f}" cy="{float(self.py(y)):.1f}" r="{r}" fill="{colour}" '
             f'stroke="{SURFACE}" stroke-width="2"/>')
        if tip:
            c = f'<g>{c}<circle cx="{float(self.px(x)):.1f}" cy="{float(self.py(y)):.1f}" r="{r + 7}" ' \
                f'fill="transparent"><title>{esc(tip)}</title></circle></g>'
        self.cv.add(c)

    def hbar(self, y, v, colour, height=11, x_from=0.0):
        a, b = sorted((float(self.px(x_from)), float(self.px(v))))
        self.cv.add(f'<rect x="{a:.1f}" y="{float(self.py(y)) - height / 2:.1f}" width="{max(b - a, 0.8):.1f}" '
                    f'height="{height}" rx="2" fill="{colour}"/>')

    def hrange(self, y, lo, hi, colour, width=2.0):
        self.cv.add(f'<line x1="{float(self.px(lo)):.1f}" y1="{float(self.py(y)):.1f}" '
                    f'x2="{float(self.px(hi)):.1f}" y2="{float(self.py(y)):.1f}" stroke="{colour}" '
                    f'stroke-width="{width}" stroke-linecap="round" opacity="0.55"/>')

    def vline(self, x, colour=DIVIDER, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.cv.add(f'<line x1="{float(self.px(x)):.1f}" y1="{self.y:.1f}" x2="{float(self.px(x)):.1f}" '
                    f'y2="{self.y + self.h:.1f}" stroke="{colour}" stroke-width="1"{d}/>')


def nice_ticks(lo, hi, n=5):
    span = hi - lo
    if span <= 0:
        return [lo]
    raw = span / n
    mag = 10 ** np.floor(np.log10(raw))
    step = min((m * mag for m in (1, 2, 2.5, 5, 10)), key=lambda s: abs(s - raw))
    start = np.ceil(lo / step) * step
    return [round(start + i * step, 10) for i in range(int((hi - start) / step) + 1)]


# ------------------------------------------------------------------------------- the figures
def fig_world_projection(F, out):
    """Each religion's world share 2020-2100: the reference scenario's mean, its parameter band and
    its predictive band, with the range of scenario means."""
    wt = pd.read_csv(F / 'global_share_by_scenario.csv')
    if 'pi05' not in wt or wt.pi05.isna().all():
        return None
    rep = json.loads((F / 'projection_report.json').read_text())
    ref, runs, nsc = rep['reference_scenario'], rep['runs_per_scenario'], wt.scenario.nunique()
    wt = wt[wt.year.le(2100)]
    cal_file = config.VALIDATION / 'predictive_calibration.csv'
    cover = ''
    if cal_file.exists():
        c = pd.read_csv(cal_file)
        c = c[c.method.eq('error-calibrated') & c.nominal.eq(0.9)].groupby('horizon').coverage.mean()
        if len(c):
            cover = (f'which covered {100 * c.min():.0f}-{100 * c.max():.0f}% of held-out observations at nominal 90% '
                     f'(horizons {c.index.min()}-{c.index.max()} years, leave one origin out).')
    cv = Canvas(1380, 800, 'World religious composition, 2020-2100',
                f'Share of world population. Reference scenario ({ref}): mean of {runs} runs, the 5-95% spread of the '
                f'runs, and the 90% predictive interval. Grey line: the range of all {nsc} scenario means.',
                'The run spread is parameter uncertainty. The predictive interval adds the forecast errors the model made '
                'on 1970-2010 (resampled by decade, scaled by horizon; religion_forecast/errors.py),\n'
                + cover + ' Both are conditional on WPP 2024 national demography. Each panel has its own scale.')
    cv.legend(30, 92, [('Reference mean', ACCENT), ('90% predictive interval', '#c9dcf5'),
                       ('5-95% of runs', '#7ea9e8'), ('Range of scenario means', INK3)])
    pw, ph, gx, gy, top = 312.0, 296.0, 30, 34, 136
    for k, g in enumerate(CATS):
        col, row = k % 4, k // 4
        X0, Y0 = 30 + col * (pw + gx), top + row * (ph + gy)
        sub = wt[wt.religion.eq(g)]
        r = sub[sub.scenario.eq(ref)].sort_values('year')
        rp = r.dropna(subset=['pi05'])
        rng_ = sub.groupby('year')['mean'].agg(['min', 'max'])
        hi = max(float(rp.pi95.max()) if len(rp) else 0.0, float(r.q95.max()), float(rng_['max'].max())) * 1.06
        p = Panel(cv, X0 + 44, Y0 + 34, pw - 92, ph - 62, (2020, 2100), (0, hi), title=MD.label(g))
        p.grid_y(nice_ticks(0, hi), fmt='{:.1%}' if hi < 0.05 else '{:.0%}')
        p.grid_x([2020, 2050, 2100], fmt='{:.0f}')
        p.axis_line()
        if len(rp):
            xs = np.r_[2020, rp.year.to_numpy()]
            m0 = float(r[r.year.eq(2020)]['mean'].iloc[0])
            p.band(xs, np.r_[m0, rp.pi05.to_numpy()], np.r_[m0, rp.pi95.to_numpy()], ACCENT, 0.15)
        p.band(r.year.to_numpy(), r.q05.to_numpy(), r.q95.to_numpy(), ACCENT, 0.35)
        p.line(rng_.index.to_numpy(), rng_['min'].to_numpy(), INK3, width=1.2, dash='3 3')
        p.line(rng_.index.to_numpy(), rng_['max'].to_numpy(), INK3, width=1.2, dash='3 3')
        p.line(r.year.to_numpy(), r['mean'].to_numpy(), ACCENT)
        for yr in (2050, 2100):
            rr = r[r.year.eq(yr)]
            if len(rr):
                rr = rr.iloc[0]
                p.dot(yr, float(rr['mean']), ACCENT,
                      tip=f'{MD.label(g)} {yr}: {100 * rr["mean"]:.1f}% (90% predictive '
                          f'{100 * rr.pi05:.1f}-{100 * rr.pi95:.1f}; runs {100 * rr.q05:.1f}-{100 * rr.q95:.1f})')
        last = r[r.year.eq(2100)]
        if len(last):
            v = float(last['mean'].iloc[0])
            cv.text(float(p.px(2100)) + 7, float(p.py(v)) + 4, f'{100 * v:.1f}%', size=12, fill=INK, weight=600)
    return cv.save(out / 'world_projection_2100.svg')


def fig_world_composition(F, out):
    """Each religion's world share 2020-3030 (exploratory beyond 2100): the reference scenario with
    its run spread, and the range of all scenario means around it."""
    wt = pd.read_csv(F / 'global_share_by_scenario.csv')
    rep = json.loads((F / 'projection_report.json').read_text())
    ref, runs, nsc = rep['reference_scenario'], rep['runs_per_scenario'], wt.scenario.nunique()
    cv = Canvas(1380, 800, 'World religious composition, 2020-3030 (exploratory beyond 2100)',
                f'Share of world population. Reference scenario ({ref}): mean and 5-95% of {runs} runs. '
                f'Grey: the range of all {nsc} scenario means. Each panel has its own scale.',
                'Time axis in two parts: 2020-2100 (WPP-based demography) takes 40% of the width, 2100-3030 '
                '(stated long-run assumptions) the remaining 60%; the vertical line marks 2100.\n'
                'Beyond 2100 the lines show what the stated assumptions imply, not forecasts; the run spread is parameter '
                'uncertainty only and there are no predictive intervals.')
    cv.legend(30, 92, [('Reference mean', ACCENT), ('5-95% of runs', '#9dc0ee'), ('Range across scenarios', '#cfcec9')])
    xpos = lambda yr: np.where(np.asarray(yr, float) <= 2100, 0.4 * (np.asarray(yr, float) - 2020) / 80.0,
                               0.4 + 0.6 * (np.asarray(yr, float) - 2100) / 930.0)
    pw, ph, gx, gy, top = 312.0, 296.0, 30, 34, 136
    for k, g in enumerate(CATS):
        col, row = k % 4, k // 4
        X0, Y0 = 30 + col * (pw + gx), top + row * (ph + gy)
        sub = wt[wt.religion.eq(g)]
        r = sub[sub.scenario.eq(ref)].sort_values('year')
        rng_ = sub.groupby('year')['mean'].agg(['min', 'max'])
        hi = max(float(r.q95.max()), float(rng_['max'].max())) * 1.05
        p = Panel(cv, X0 + 44, Y0 + 34, pw - 92, ph - 62, (0, 1), (0, hi), title=MD.label(g))
        p.grid_y(nice_ticks(0, hi), fmt='{:.1%}' if hi < 0.05 else '{:.0%}')
        p.vline(float(xpos(2100)))
        p.axis_line()
        for yr in (2020, 2100, 2500, 3026):
            p.grid_x([float(xpos(yr))], fmt=lambda _v, y=yr: str(y))
        xr = xpos(rng_.index.to_numpy())
        p.band(xr, rng_['min'].to_numpy(), rng_['max'].to_numpy(), NEUTRAL, 0.22)
        xq = xpos(r.year.to_numpy())
        p.band(xq, r.q05.to_numpy(), r.q95.to_numpy(), ACCENT, 0.16)
        p.line(xq, r['mean'].to_numpy(), ACCENT)
        last = r[r.year.eq(3026)]
        if len(last):
            v = float(last['mean'].iloc[0])
            cv.text(float(p.px(xpos(3026))) + 7, float(p.py(v)) + 4, f'{100 * v:.1f}%', size=12, fill=INK, weight=600)
        for yr in (2050, 2100, 2200, 2500):
            rr = r[r.year.eq(yr)]
            if len(rr):
                rr = rr.iloc[0]
                p.dot(float(xpos(yr)), float(rr['mean']), ACCENT,
                      tip=f'{MD.label(g)} {yr}: {100 * rr["mean"]:.1f}% (5-95% of runs '
                          f'{100 * rr.q05:.1f}-{100 * rr.q95:.1f}; scenario means '
                          f'{100 * rng_.loc[yr, "min"]:.1f}-{100 * rng_.loc[yr, "max"]:.1f})')
    return cv.save(out / 'world_composition_long_run.svg')


def fig_validation(V, out):
    """History-test skill relative to persistence, country by country, with bootstrap intervals."""
    f = V / 'inference.csv'
    if not f.exists():
        return None
    inf = pd.read_csv(f)
    order = ['trend', 'demography', 'demography_migration', 'switching_0.5', 'switching_1', 'switching_selected']
    label = {'trend': 'Trend: last decade repeated', 'demography': 'Births and deaths',
             'demography_migration': '+ migration', 'switching_0.5': '+ switching, half strength',
             'switching_1': '+ switching, full strength (as projected)',
             'switching_selected': '+ switching, strength chosen on earlier decades'}
    scopes = list(dict.fromkeys(inf.scope))
    cv = Canvas(1180, 200 + 262 * len(scopes), 'Forecast skill on historical decades, relative to assuming no change',
                'Population-weighted mean difference in total-variation error from persistence, over every country and '
                'test decade (percentage points). Left of zero is better. Line: 95% interval.',
                'Intervals from 4,000 bootstrap resamples of countries. Countries in the same decade share common shocks, '
                'which this interval does not capture; the decade-level sign-flip p-value on the right is the\n'
                'conservative test (with four decades it cannot fall below 0.125). Source: data/validation/inference.csv')
    for si, scope in enumerate(scopes):
        sub = inf[inf.scope.eq(scope)].set_index('model').reindex(order).dropna(subset=['mean_difference_pp'])
        lo = min(-0.3, float(sub.ci95_low_pp.min()) * 1.1)
        hi = max(0.3, float(sub.ci95_high_pp.max()) * 1.1)
        Y = 168 + si * 262
        n_cw = int(sub.country_windows.max())
        p = Panel(cv, 330, Y, 600, 170, (lo, hi), (-0.6, len(sub) - 0.4),
                  title=f'{scope} ({n_cw} country-decades)')
        p.grid_x(nice_ticks(lo, hi, 6), fmt='{:+.1f}')
        p.vline(0.0, colour=INK2, dash='4 3')
        p.axis_line()
        for i, (m, r) in enumerate(sub[::-1].iterrows()):
            colour = GOOD if r.ci95_high_pp < 0 else (BAD if r.ci95_low_pp > 0 else NEUTRAL)
            p.hrange(i, r.ci95_low_pp, r.ci95_high_pp, colour, width=3)
            p.dot(r.mean_difference_pp, i, colour, r=5,
                  tip=f'{label.get(m, m)}: {r.mean_difference_pp:+.3f} pp [{r.ci95_low_pp:+.3f}, {r.ci95_high_pp:+.3f}]')
            cv.text(322, float(p.py(i)) + 4, label.get(m, m), size=12, fill=INK, anchor='end')
            cv.text(1150, float(p.py(i)) + 4,
                    f'{r.mean_difference_pp:+.2f}  [{r.ci95_low_pp:+.2f}, {r.ci95_high_pp:+.2f}]   '
                    f'{int(r.windows_better)}/{int(r.windows)} decades, p = {r.p_window:.3f}' if np.isfinite(r.p_window)
                    else f'{r.mean_difference_pp:+.2f}  [{r.ci95_low_pp:+.2f}, {r.ci95_high_pp:+.2f}]',
                    size=11, fill=INK2, anchor='end')
        cv.text(330, Y + 210, 'difference from persistence, percentage points of total-variation error', size=11.5, fill=INK2)
    cv.legend(330, 96, [('Better than persistence (interval below 0)', GOOD), ('Worse (interval above 0)', BAD),
                        ('Not distinguishable', NEUTRAL)])
    return cv.save(out / 'validation_skill.svg')


def fig_interval_calibration(V, out):
    """Do the intervals contain the truth as often as they claim? Parameter-only against
    error-calibrated, held out by origin, with the growth of error with horizon."""
    f = V / 'predictive_calibration.csv'
    if not f.exists():
        return None
    cal = pd.read_csv(f)
    meta = json.loads((V / 'forecast_error_model.json').read_text()) if (V / 'forecast_error_model.json').exists() else {}
    cv = Canvas(1380, 600, 'Are the forecast intervals honest?',
                'Left: share of held-out observations inside the interval against its nominal level. Middle: interval '
                'score (lower is better). Right: how forecast error grows with horizon.',
                'Leave one origin out: the error model is re-estimated without the origin it is tested on; observations are '
                'country x religion shares of the World Religion Project, 1980-2010. Left: vertical strokes span the\n'
                'horizons (10-40 years). Parameter-only intervals are the spread of the model\'s Monte Carlo runs. Source: '
                'data/validation/predictive_calibration.csv, forecast_error_model.json')
    methods = [('model draws (parameter uncertainty)', BAD, 'Parameter uncertainty only'),
               ('error-calibrated', ACCENT, 'Error-calibrated (this paper)')]
    cv.legend(30, 96, [(lab, c) for _, c, lab in methods])
    p = Panel(cv, 76, 170, 360, 320, (0.45, 1.0), (0, 1), title='Coverage against nominal level',
              ylab='share of held-out cells inside (mean over horizons)')
    p.grid_y([0, .25, .5, .75, 1.0], fmt='{:.0%}')
    p.grid_x([0.5, 0.8, 0.9, 0.95], fmt='{:.0%}')
    p.axis_line()
    p.line([0.45, 1.0], [0.45, 1.0], INK3, width=1.5, dash='5 4')
    cv.text(float(p.px(0.56)), float(p.py(0.66)), 'nominal', size=11, fill=INK3)
    for m, colour, lab in methods:
        g = cal[cal.method.eq(m)]
        mean = g.groupby('nominal').coverage.mean()
        lo, hi = g.groupby(['nominal', 'horizon']).coverage.mean().groupby('nominal').agg(['min', 'max']).T.to_numpy()
        for x, a, b in zip(mean.index, lo, hi):
            p.cv.add(f'<line x1="{float(p.px(x)):.1f}" y1="{float(p.py(a)):.1f}" x2="{float(p.px(x)):.1f}" '
                     f'y2="{float(p.py(b)):.1f}" stroke="{colour}" stroke-width="3" opacity="0.35"/>')
        p.line(mean.index.to_numpy(), mean.to_numpy(), colour, width=2)
        for x, v in mean.items():
            p.dot(x, v, colour, r=4, tip=f'{lab}: nominal {x:.0%}, covered {v:.1%} (range over horizons '
                                         f'{lo[list(mean.index).index(x)]:.1%}-{hi[list(mean.index).index(x)]:.1%})')
            below = m.startswith('model')
            cv.text(float(p.px(x)) + (7 if below else -8), float(p.py(v)) + (14 if below else -9), f'{v:.0%}',
                    size=10.5, fill=INK2, anchor='start' if below else 'end')
    sc = cal[cal.nominal.eq(0.9)].groupby(['method', 'horizon']).interval_score_pp.mean().unstack('method')
    hi = float(sc.max().max()) * 1.15
    p2 = Panel(cv, 540, 170, 330, 320, (5, 45), (0, hi), title='Interval score, 90% intervals',
               ylab='percentage points (lower is better)')
    p2.grid_y(nice_ticks(0, hi, 5), fmt='{:.0f}')
    p2.grid_x(list(sc.index), fmt='{:.0f} yr')
    p2.axis_line()
    for m, colour, lab in methods:
        if m in sc:
            p2.line(sc.index.to_numpy(), sc[m].to_numpy(), colour)
            for h, v in sc[m].items():
                p2.dot(h, v, colour, r=4, tip=f'{lab}, {h} years: {v:.1f}')
                cv.text(float(p2.px(h)), float(p2.py(v)) - 11, f'{v:.0f}', size=10.5, fill=INK2, anchor='middle')
    ma = {int(k): v for k, v in meta.get('mean_abs_standardised_error', {}).items()}
    if ma:
        hs = sorted(ma)
        beta = float(meta.get('beta', 0.5))
        top = max(ma.values()) * 1.3
        p3 = Panel(cv, 980, 170, 330, 320, (5, 45), (0, top), title='Error growth with horizon',
                   ylab='mean |standardised error|')
        p3.grid_y(nice_ticks(0, top, 5), fmt='{:.2f}')
        p3.grid_x(hs, fmt='{:.0f} yr')
        p3.axis_line()
        xs = np.linspace(8, 45, 40)
        p3.line(xs, ma[10] * (xs / 10) ** beta, INK3, width=1.5, dash='5 4')
        p3.line(xs, ma[10] * (xs / 10) ** 0.5, '#cfcec9', width=1.2, dash='2 3')
        for h in hs:
            p3.dot(h, ma[h], INK, r=5, tip=f'{h} years: {ma[h]:.3f}')
        cv.text(float(p3.px(44)), float(p3.py(ma[10] * 4.4 ** beta)) - 8, f'fitted (h/10)^{beta:.2f}', size=11,
                fill=INK2, anchor='end')
        cv.text(float(p3.px(44)), float(p3.py(ma[10] * 4.4 ** 0.5)) - 8, 'random walk (h/10)^0.5', size=11,
                fill=INK3, anchor='end')
    return cv.save(out / 'interval_calibration.svg')


def fig_ablation(E, out):
    """What each mechanism contributes, measured by switching it off."""
    f = E / 'ablation_effects.csv'
    if not f.exists():
        return None
    eff = pd.read_csv(f)
    rels = ['world_Christianity', 'world_Islam', 'world_Unaffiliated', 'world_Hinduism']
    years = [2050, 2100]
    cv = Canvas(1180, 590, 'What each mechanism contributes to world religious shares',
                'The full model minus the same run with one mechanism switched off, paired run by run. '
                'Bars are the mean over runs, the line the 5-95% range.',
                'Identical random draws in both runs, so each difference is the mechanism and not sampling noise. '
                '"Fertility differences" means religions within a country differing in fertility;\n'
                'with it off every group has its country\'s rate. Source: data/experiments/ablation_effects.csv')
    mech = sorted(eff.mechanism.unique())
    colours = {'religious switching': '#a32a28', 'fertility differences': '#eb6834', 'migration': '#2a78d6',
               'demography only': INK3}
    cv.legend(76, 96, [(m.capitalize(), colours.get(m, NEUTRAL)) for m in mech if m != 'demography only'])
    for yi, year in enumerate(years):
        sub = eff[eff.year.eq(year) & eff.outcome.isin(rels) & eff.mechanism.ne('demography only')]
        if sub.empty:
            continue
        lo = min(-0.005, float(sub.contribution_q05.min()) * 1.2)
        hi = max(0.005, float(sub.contribution_q95.max()) * 1.2)
        X = 96 + yi * 560
        p = Panel(cv, X, 172, 440, 300, (lo, hi), (-0.5, len(rels) - 0.5),
                  title=f'By {year}', ylab='percentage points of world population')
        p.grid_x(nice_ticks(lo, hi, 5), fmt=lambda v: f'{100 * v:+.0f}')
        p.vline(0.0, colour=DIVIDER)
        p.axis_line()
        for ri, rel in enumerate(rels):
            for mi, m in enumerate([x for x in mech if x != 'demography only']):
                row = sub[sub.outcome.eq(rel) & sub.mechanism.eq(m)]
                if row.empty:
                    continue
                row = row.iloc[0]
                y = ri + (mi - 1) * 0.26
                p.hrange(y, row.contribution_q05, row.contribution_q95, colours.get(m, NEUTRAL))
                p.hbar(y, row.contribution_mean, colours.get(m, NEUTRAL), height=9)
                if abs(row.contribution_mean) > 0.004:
                    off = 10 if row.contribution_mean > 0 else -10
                    cv.text(float(p.px(row.contribution_mean)) + off, float(p.py(y)) + 4,
                            f'{100 * row.contribution_mean:+.1f}', size=10.5, fill=INK2,
                            anchor='start' if off > 0 else 'end')
            cv.text(X - 8, float(p.py(ri)) + 4, MD.label(rel.replace('world_', '')), size=12.5,
                    fill=INK, anchor='end')
    return cv.save(out / 'mechanism_ablation.svg')


def fig_sensitivity(E, out, outcomes=('world_Christianity', 'world_Islam', 'world_Unaffiliated',
                                      'diversity_within_pop_weighted')):
    """Which uncertain parameters move the results: one panel per outcome and horizon."""
    f = E / 'sensitivity_coefficients.csv'
    if not f.exists():
        return None
    sc = pd.read_csv(f)
    sc = sc[sc.basis.eq('rank')]
    years = [y for y in (2050, 2100) if y in set(sc.year)]
    rows, cols = len(outcomes), max(len(years), 1)
    pw, ph = 420, 190
    cv = Canvas(120 + cols * (pw + 150), 200 + rows * (ph + 76), 'Which assumptions move the results',
                'Standardised rank regression coefficients: how many standard deviations an outcome moves when '
                'one parameter moves by one, the others held still. The five largest are shown.',
                'Computed on a Monte Carlo design of the reference scenario, separate from the projection runs. '
                'R2 is how much of the spread this linear reading explains; a low R2 means the\n'
                'parameters interact. Source: data/experiments/sensitivity_coefficients.csv')
    cv.legend(150, 96, [('Raises the outcome', ACCENT), ('Lowers it', BAD)])
    nice = {'world_Christianity': 'Christian world share', 'world_Islam': 'Muslim world share',
            'world_Unaffiliated': 'Unaffiliated world share',
            'diversity_within_pop_weighted': 'Within-country diversity'}
    for ri, outcome in enumerate(outcomes):
        for ci, year in enumerate(years):
            sub = sc[sc.year.eq(year) & sc.outcome.eq(outcome)].nlargest(5, 'abs_coefficient')
            if sub.empty:
                continue
            sub = sub.sort_values('abs_coefficient')
            lim = max(0.1, float(sub.abs_coefficient.max()) * 1.5)
            X = 150 + ci * (pw + 150)
            Y = 176 + ri * (ph + 76)
            p = Panel(cv, X, Y, pw, ph, (-lim, lim), (-0.6, len(sub) - 0.4),
                      title=f'{nice.get(outcome, outcome)}, {year}')
            p.grid_x(nice_ticks(-lim, lim, 5), fmt='{:+.1f}')
            p.vline(0.0, colour=DIVIDER)
            p.axis_line()
            for i, (_, r) in enumerate(sub.iterrows()):
                p.hbar(i, r.coefficient, ACCENT if r.coefficient > 0 else BAD, height=13)
                cv.text(X - 8, float(p.py(i)) + 4, r.parameter, size=11.5, fill=INK, anchor='end')
                off = 9 if r.coefficient > 0 else -9
                cv.text(float(p.px(r.coefficient)) + off, float(p.py(i)) + 4, f'{r.coefficient:+.2f}',
                        size=10.5, fill=INK2, anchor='start' if off > 0 else 'end')
            cv.text(X + pw, Y - 30, f'R2 = {float(sub.model_r2.iloc[0]):.2f}', size=11,
                    fill=INK3, anchor='end')
    return cv.save(out / 'sensitivity.svg')


def fig_shift_share(F, out):
    """Is world religious change about people changing religion, or about where people live?"""
    f = F / 'world_share_shift_share.csv'
    if not f.exists():
        return None
    ss = pd.read_csv(f)
    year = 2100 if 2100 in set(ss.year) else int(ss.year.max())
    sub = ss[ss.year.eq(year)].set_index('religion').reindex(CATS)
    lo = min(-1.0, float(min(sub.within_country_pp.min(), sub.population_weighting_pp.min())) * 1.2)
    hi = max(1.0, float(max(sub.within_country_pp.max(), sub.population_weighting_pp.max())) * 1.2)
    cv = Canvas(1000, 600, f'Where world-share change comes from, 2020-{year}',
                'Each religion\'s change in world share, split into countries\' own shares changing and the '
                'populations of countries changing relative to each other.',
                'An exact decomposition: within-country + population weighting + a small interaction term\n'
                'equals the total change. For several groups the two parts point in opposite directions.\n'
                'Source: data/projections/world_share_shift_share.csv')
    cv.legend(300, 96, [('Countries\' own shares change', '#a32a28'),
                         ('Country populations grow at different rates', '#2a78d6'), ('Total change (dot)', INK)])
    cv.text(916, 160, 'total', size=11, fill=INK2, anchor='end')
    p = Panel(cv, 300, 176, 600, 320, (lo, hi), (-0.6, len(sub) - 0.4), ylab='percentage points of world population')
    p.grid_x(nice_ticks(lo, hi, 6), fmt='{:+.0f}')
    p.vline(0.0, colour=DIVIDER)
    p.axis_line()
    for i, (rel, r) in enumerate(sub.iterrows()):
        p.hrange(i, 0, 0, NEUTRAL)
        p.hbar(i + 0.19, r.within_country_pp, '#a32a28', height=11)
        p.hbar(i - 0.19, r.population_weighting_pp, '#2a78d6', height=11)
        p.dot(r.change_pp, i, INK, r=5, tip=f'{rel}: total {r.change_pp:+.2f} pp')
        cv.text(292, float(p.py(i)) + 4, MD.label(rel), size=12.5, fill=INK, anchor='end')
        cv.text(916, float(p.py(i)) + 4, f'{r.change_pp:+.1f}', size=11.5, fill=INK, anchor='end')
    cv.text(300, 528, 'percentage points', size=11.5, fill=INK2)
    return cv.save(out / 'shift_share.svg')


def fig_scenarios(F, out, year=2100):
    """How far apart the scenarios are, against the spread inside each one."""
    wt = pd.read_csv(F / 'global_share_by_scenario.csv')
    rep = json.loads((F / 'projection_report.json').read_text())
    ref = rep['reference_scenario']
    sub = wt[wt.year.eq(year)]
    rels = ['Christianity', 'Islam', 'Unaffiliated', 'Hinduism']
    order = list(dict.fromkeys(wt.scenario))
    cv = Canvas(1180, 740, f'World shares in {year} under every scenario',
                f'Dot: a scenario mean. Line: the 5-95% spread of runs inside that scenario. '
                f'The reference scenario ({ref}) is marked.',
                'Differences between dots are scenario uncertainty (the assumptions); the length of a line is '
                'parameter uncertainty inside one scenario. Neither includes forecast error; see world_projection_2100.\n'
                'Source: data/projections/global_share_by_scenario.csv')
    for ri, rel in enumerate(rels):
        s = sub[sub.religion.eq(rel)].set_index('scenario').reindex(order)
        lo, hi = float(s.q05.min()) * 0.9, float(s.q95.max()) * 1.08
        X = 250 + (ri % 2) * 560
        Y = 168 + (ri // 2) * 282
        p = Panel(cv, X, Y, 330, 215, (lo, hi), (-0.6, len(order) - 0.4), title=MD.label(rel))
        p.grid_x(nice_ticks(lo, hi, 4), fmt='{:.0%}')
        p.axis_line()
        for i, sc in enumerate(order):
            if sc not in s.index or not np.isfinite(s.loc[sc, 'mean']):
                continue
            r = s.loc[sc]
            colour = MD.COLORS.get(rel, ACCENT)
            p.hrange(i, r.q05, r.q95, colour)
            p.dot(r['mean'], i, colour, r=5, tip=f'{sc}: {100 * r["mean"]:.1f}% ({100 * r.q05:.1f}-{100 * r.q95:.1f})')
            if ri % 2 == 0:
                cv.text(X - 8, float(p.py(i)) + 4, sc + (' (reference)' if sc == ref else ''),
                        size=11, fill=INK if sc == ref else INK2, anchor='end',
                        weight=600 if sc == ref else None)
            cv.text(float(p.px(r.q95)) + 8, float(p.py(i)) + 4, f'{100 * r["mean"]:.1f}', size=10.5, fill=INK2)
    return cv.save(out / 'scenario_comparison.svg')


def fig_benchmark(F, out):
    """This model against Pew Research Center's own published projection."""
    f = F / 'benchmark_vs_pew2015.csv'
    if not f.exists():
        return None
    b = pd.read_csv(f)
    w = b[b.level.eq('world')].set_index('religion').reindex(CATS).dropna(subset=['this_model_change_pp'])
    lo = min(-1.0, float(min(w.this_model_change_pp.min(), w.pew2015_change_pp.min())) * 1.25)
    hi = max(1.0, float(max(w.this_model_change_pp.max(), w.pew2015_change_pp.max())) * 1.25)
    cv = Canvas(1060, 566, 'This model against Pew Research Center\'s own projection',
                'Change in world share from 2020 to 2050, as each projects it.',
                'Levels are not compared: the two sources disagree about 2020 itself, because Pew\'s 2015 report and '
                'its 2025 measurement classify some populations differently (China accounts for about\n'
                'two thirds of that gap). The comparison is therefore of the change each projects. '
                'Source: data/projections/benchmark_vs_pew2015.csv')
    cv.legend(300, 96, [('This model', ACCENT), ('Pew Research Center (2015)', INK3)])
    cv.text(968, 160, 'this', size=11, fill=ACCENT, anchor='end')
    cv.text(1022, 160, 'Pew', size=11, fill=INK3, anchor='end')
    p = Panel(cv, 300, 176, 560, 310, (lo, hi), (-0.6, len(w) - 0.4), ylab='change in world share, 2020-2050')
    p.grid_x(nice_ticks(lo, hi, 6), fmt='{:+.0f}')
    p.vline(0.0, colour=DIVIDER)
    p.axis_line()
    for i, (rel, r) in enumerate(w.iterrows()):
        p.hbar(i + 0.18, r.this_model_change_pp, ACCENT, height=11)
        p.hbar(i - 0.18, r.pew2015_change_pp, INK3, height=11)
        cv.text(292, float(p.py(i)) + 4, MD.label(rel), size=12.5, fill=INK, anchor='end')
        cv.text(968, float(p.py(i)) + 4, f'{r.this_model_change_pp:+.1f}', size=11.5, fill=ACCENT, anchor='end')
        cv.text(1022, float(p.py(i)) + 4, f'{r.pew2015_change_pp:+.1f}', size=11.5, fill=INK3, anchor='end')
    cv.text(300, 522, 'percentage points', size=11.5, fill=INK2)
    return cv.save(out / 'benchmark_vs_pew2015.svg')


def build_all(out=None, log=print):
    """Every chart whose input file exists."""
    out = out or config.FIGURES
    made = []
    for fn, args in ((fig_world_projection, (config.PROJECTIONS,)), (fig_world_composition, (config.PROJECTIONS,)),
                     (fig_shift_share, (config.PROJECTIONS,)),
                     (fig_scenarios, (config.PROJECTIONS,)), (fig_benchmark, (config.PROJECTIONS,)),
                     (fig_validation, (config.VALIDATION,)), (fig_interval_calibration, (config.VALIDATION,)),
                     (fig_ablation, (config.EXPERIMENTS,)), (fig_sensitivity, (config.EXPERIMENTS,))):
        try:
            p = fn(*args, out)
        except FileNotFoundError:
            p = None
        if p is not None:
            made.append(p.name)
    log(f'{len(made)} charts: {", ".join(made)}')
    return made
