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
def fig_world_composition(F, out):
    """Each religion's world share over time: the reference scenario with its run spread, and the
    range of all scenario means around it."""
    wt = pd.read_csv(F / 'global_share_by_scenario.csv')
    rep = json.loads((F / 'projection_report.json').read_text())
    ref, runs, nsc = rep['reference_scenario'], rep['runs_per_scenario'], wt.scenario.nunique()
    cv = Canvas(1380, 800, 'World religious composition, 2020-3030',
                f'Share of world population. Reference scenario ({ref}): mean and 5-95% of {runs} runs. '
                f'Grey: the range of all {nsc} scenario means. Each panel has its own scale.',
                'Time axis in two parts: 2020-2100 (WPP-based demography) takes 40% of the width, 2100-3030 '
                '(stated long-run assumptions) the remaining 60%; the vertical line marks 2100.\n'
                'The run spread is parameter uncertainty only. Backtests show it is far narrower than actual '
                'forecast error (see the interval-calibration figure). 2500 and 3026 are speculative scenarios.')
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
    return cv.save(out / 'world_composition.svg')


def fig_validation(V, out):
    """History-test skill against the persistence baseline, by model and window scope."""
    f = V / 'validation_summary.csv'
    if not f.exists():
        return None
    vs = pd.read_csv(f)
    keep = ['persistence', 'demography', 'demography_migration', 'switching_strength_0.5',
            'switching_strength_1', 'demography_migration_momentum']
    label = {'persistence': 'Persistence (no change)', 'demography': 'Births and deaths only',
             'demography_migration': '+ migration', 'switching_strength_0.5': '+ switching, half strength',
             'switching_strength_1': '+ switching, full strength',
             'demography_migration_momentum': 'Extrapolate the last decade'}
    scopes = [s for s in vs.scope.unique() if 'WRP' in s]
    cv = Canvas(1180, 190 + 250 * len(scopes), 'Forecast skill on historical decades',
                'Population-weighted total-variation error of country religious shares, in percentage points. '
                'Lower is better; the dashed line is the persistence baseline.',
                'Forward chaining: switching is fitted only on decades that end before the test decade begins, '
                'and the strength and residual weights are chosen on earlier test decades only.\n'
                'Source: data/validation/validation_summary.csv')
    for si, scope in enumerate(scopes):
        sub = vs[vs.scope.eq(scope) & vs.model.isin(keep)].set_index('model').reindex(keep).dropna(subset=['popw_tv_pp'])
        pers = float(vs[vs.scope.eq(scope) & vs.model.eq('persistence')].popw_tv_pp.iloc[0])
        lo, hi = min(sub.popw_tv_pp.min(), pers) * 0.97, max(sub.popw_tv_pp.max(), pers) * 1.02
        Y = 160 + si * 250
        p = Panel(cv, 300, Y, 790, 170, (lo, hi), (-0.6, len(sub) - 0.4), title=scope,
                  ylab='')
        p.grid_x(nice_ticks(lo, hi, 5), fmt='{:.2f}')
        for i, (m, row) in enumerate(sub.iterrows()):
            better = row.popw_tv_pp < pers
            colour = GOOD if better else (BAD if row.popw_tv_pp > pers * 1.002 else NEUTRAL)
            p.hbar(i, row.popw_tv_pp, colour, height=15, x_from=lo)
            cv.text(292, float(p.py(i)) + 4, label.get(m, m), size=12, fill=INK, anchor='end')
            cv.text(float(p.px(row.popw_tv_pp)) + 8, float(p.py(i)) + 4,
                    f'{row.popw_tv_pp:.3f}' + ('' if m == 'persistence' else
                                               f'  ({row.popw_tv_pp - pers:+.3f})'), size=11.5, fill=INK2)
        p.vline(pers, colour=INK2, dash='4 3')
        p.axis_line()
        cv.text(300, Y + 198, 'population-weighted total-variation error (percentage points)', size=11.5, fill=INK2)
    cv.legend(300, 92, [('Better than persistence', GOOD), ('Worse', BAD)])
    return cv.save(out / 'validation_skill.svg')


def fig_interval_calibration(V, out):
    """Do the stated uncertainty bands contain the truth as often as they claim?"""
    f = V / 'interval_calibration.csv'
    if not f.exists():
        return None
    cal = pd.read_csv(f)
    cw = pd.read_csv(V / 'interval_calibration_windows.csv') if (V / 'interval_calibration_windows.csv').exists() \
        else pd.DataFrame()
    cv = Canvas(1180, 580, 'Are the predictive intervals honest?',
                'Left: how often the observed share fell inside the model interval, against how often it should. '
                'Right: the error actually made at ten years, against the width the model claims.',
                'The intervals the model reports are PARAMETER uncertainty: the spread of outcomes over the drawn '
                'parameters. They do not include measurement error in the historical shares, nor country-level\n'
                'change the model has no mechanism for. Both left-hand lines being far below the diagonal is the '
                'main negative result of this work. Source: data/validation/interval_calibration*.csv')
    p = Panel(cv, 76, 168, 420, 310, (0, 1), (0, 1), title='Coverage against nominal level',
              ylab='share of observed country x religion cells inside the interval')
    p.grid_y([0, .25, .5, .75, 1.0], fmt='{:.0%}')
    p.grid_x([0.5, 0.8, 0.9], fmt='{:.0%}')
    p.axis_line()
    p.line([0, 1], [0, 1], INK3, width=1.5, dash='5 4')
    cv.text(float(p.px(0.62)), float(p.py(0.70)), 'perfect calibration', size=11, fill=INK3)
    for colour, col, name in ((BAD, 'coverage', 'model interval'),
                              (ACCENT, 'coverage_with_measurement_error', 'widened by measured data noise')):
        for win, g in cal.groupby('window'):
            g = g.sort_values('nominal')
            p.line(g.nominal.to_numpy(), g[col].to_numpy(), colour, width=2, opacity=0.85)
            for _, r in g.iterrows():
                p.dot(r.nominal, r[col], colour, r=4, tip=f'{win}: nominal {r.nominal:.0%}, covered {r[col]:.0%}')
    cv.legend(76, 96, [('Model interval', BAD), ('Widened by measured data noise', ACCENT)])

    if len(cw):
        g = cw.groupby('religion')[['abs_error_q90_pp', 'model_half_width_q90_pp', 'widening_needed']].mean()
        g = g.sort_values('abs_error_q90_pp', ascending=False)
        hi = float(g.abs_error_q90_pp.max()) * 1.25
        p2 = Panel(cv, 700, 168, 380, 310, (0, hi), (-0.6, len(g) - 0.4),
                   title='90th percentile of error at 10 years', ylab='percentage points')
        p2.grid_x(nice_ticks(0, hi, 5))
        p2.axis_line()
        for i, (rel, row) in enumerate(g.iterrows()):
            p2.hbar(i, row.abs_error_q90_pp, MD.COLORS.get(rel, NEUTRAL), height=13)
            p2.dot(row.model_half_width_q90_pp, i, INK, r=4,
                   tip=f'{rel}: model half-width {row.model_half_width_q90_pp:.2f} pp')
            cv.text(692, float(p2.py(i)) + 4, MD.label(rel), size=12, fill=INK, anchor='end')
            cv.text(float(p2.px(row.abs_error_q90_pp)) + 8, float(p2.py(i)) + 4,
                    f'{row.abs_error_q90_pp:.1f} pp  ({row.widening_needed:.0f}x wider than claimed)',
                    size=11, fill=INK2)
        cv.legend(700, 96, [('Error actually made', NEUTRAL), ('Width the model claims', INK)])
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
    years = [y for y in (2100, 3026) if y in set(sc.year)]
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
                'parameter uncertainty inside one scenario. Both understate total forecast uncertainty.\n'
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
    for fn, args in ((fig_world_composition, (config.PROJECTIONS,)), (fig_shift_share, (config.PROJECTIONS,)),
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
