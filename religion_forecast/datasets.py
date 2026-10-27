"""Step 7 data layer: every input the model reads, with a record of what was found.

Required (already used by earlier steps)
  data/raw/WPP2024_Demographic_Indicators_Medium.csv.gz   UN WPP 2024 national indicators 1950-2100
  data/raw/WRP_national.csv                                World Religion Project 1945-2010
  data/raw/ne_50m_admin_0_countries.zip                    Natural Earth (distances, borders, maps)
  start state: data/processed/pew_harmonized.csv (Step 2, Pew 2010 and 2020, eight groups) or, if
               absent, results_step5/headline_country_shares.csv (Pew 2020 start state exported by
               Step 5D; no Pew 2010, so the 2010-2020 test cannot run)
Optional (Step 7 uses them when present; see docs/DATA.md and run.py fetch)
  data/raw/extra/WPP2024_PopulationByAge5GroupSex_Medium.csv.gz   national age structure
  data/raw/extra/undesa_pd_2024_ims_stock_by_sex_destination_and_origin.xlsx  bilateral stocks
     or data/raw/extra/migrant_stock_bilateral.csv (origin_iso3, dest_iso3, year, migrants)
  data/raw/extra/pew_migrants_religion.csv   religion of migrants (tidy format, see loader)
  data/raw/extra/switching_lifetime_observed.csv  survey raised-vs-current tables (tidy format)
  data/raw/extra/religion_fertility_observed.csv  TFR by religion within countries
  data/raw/extra/unhcr_population.csv        UNHCR refugees by origin and asylum
  inputs/*.csv                         published figures transcribed with citations (tracked)
Nothing here invents data: a missing optional file means the model uses its labelled fallback.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from religion_forecast import engine as E
from religion_forecast import sources as H
from religion_forecast import config

RAW = config.RAW
PROCESSED = config.PROCESSED


def _extra_file(name):
    """An optional downloaded file, from whichever data/raw subfolder holds it."""
    hits = config.find_extra(name)
    return hits[0] if hits else config.RAW_EXTRA / name

RESULTS5 = config.LEGACY_RESULTS
TRACKED = config.INPUTS
CATS, K = E.CATS, E.K
SHARE_COLS = [f'share_{c}' for c in CATS]
FOUND: dict = {}


def _note(key, status, detail=''):
    FOUND[key] = {'status': status, 'detail': detail}


# ------------------------------------------------------------------------------- WPP
def wpp_table():
    """National WPP indicators: country_id, locid, year, tfr, e0, q5 (probability), mac, median_age,
    pop (persons), female_share, net_migrations (persons per year)."""
    p = RAW / 'WPP2024_Demographic_Indicators_Medium.csv.gz'
    w = pd.read_csv(p, low_memory=False)
    w = w[w.ISO3_code.notna() & w.Variant.astype(str).str.lower().eq('medium')]
    num = lambda s: pd.to_numeric(s, errors='coerce')
    out = pd.DataFrame({
        'country_id': w.ISO3_code.astype(str), 'locid': num(w.LocID).astype('Int64'),
        'name': w.Location.astype(str), 'year': num(w.Time).astype(int),
        'tfr': num(w.TFR), 'e0': num(w.LEx), 'q5': num(w.Q5) / 1000.0, 'mac': num(w.MAC),
        'median_age': num(w.MedianAgePop), 'pop': num(w.TPopulation1July) * 1000.0,
        'female_share': num(w.TPopulationFemale1July) / num(w.TPopulation1July),
        'net_migrations': num(w.NetMigrations) * 1000.0, 'cbr': num(w.CBR), 'cdr': num(w.CDR)})
    out = out[out.year <= 2100].reset_index(drop=True)
    _note('wpp_indicators', 'used', f'{out.country_id.nunique()} countries, {out.year.min()}-{out.year.max()}')
    return out


def m49_to_iso3(wpp):
    x = wpp.dropna(subset=['locid']).drop_duplicates('country_id')
    return dict(zip(x.locid.astype(int), x.country_id))


def wpp_age_cube(ids):
    """WPP population by 5-year age group (condensed by run.py fetch): returns
    (years [Y], total [Y, n, A], female [Y, n, A]) with NaN where a country is missing, or None."""
    p = _extra_file('WPP2024_age5_condensed.csv.gz')
    if not p.exists():
        _note('wpp_age', 'missing', 'national age pyramids approximated from WPP median age; '
                                    'female share of reproductive ages = national female share')
        return None
    df = pd.read_csv(p)
    df = df[df.ISO3_code.isin(ids)]
    df['g'] = df.AgeGrp.astype(str).str.extract(r'(\d+)')[0].astype(int) // 5
    df['g'] = df.g.clip(upper=E.A - 1)
    years = sorted(df.Time.unique())
    yi = {y: i for i, y in enumerate(years)}
    idx = {c: i for i, c in enumerate(ids)}
    tot = np.full((len(years), len(ids), E.A), np.nan)
    fem = np.full((len(years), len(ids), E.A), np.nan)
    agg = df.groupby(['Time', 'ISO3_code', 'g'], as_index=False)[['PopTotal', 'PopFemale']].sum()
    r, c, g = agg.Time.map(yi).to_numpy(int), agg.ISO3_code.map(idx).to_numpy(int), agg.g.to_numpy(int)
    tot[r, c, g] = agg.PopTotal.to_numpy(float)
    fem[r, c, g] = agg.PopFemale.to_numpy(float)
    covered = int(np.isfinite(tot[0]).all(1).sum())
    _note('wpp_age', 'used', f'{covered} of {len(ids)} countries, {years[0]}-{years[-1]} (5-year points)')
    return np.array(years), tot, fem


# ----------------------------------------------------------------------- start state
def start_state():
    """Religious composition in 2020 (and 2010 when available).
    Returns dict: s2020 DataFrame(country_id, share_*), s2010 DataFrame or None, source text,
    folk_method Series (how Pew's 'Other religions' was split) or None."""
    pew = PROCESSED / 'pew_harmonized.csv'
    if pew.exists():
        df = pd.read_csv(pew, low_memory=False)
        if 'quality_pass' in df:
            df = df[df.quality_pass.astype(bool)]
        df = df[df.country_id.notna()]
        s20 = df[df.year.eq(2020)].drop_duplicates('country_id')
        s10 = df[df.year.eq(2010)].drop_duplicates('country_id')
        _note('start_state', 'used', f'Pew 2010/2020 via Step 2 ({len(s20)} countries in 2020, {len(s10)} in 2010)')
        fm = s20.set_index('country_id')['folk_split_method'] if 'folk_split_method' in s20 else None
        return dict(s2020=s20[['country_id'] + SHARE_COLS].reset_index(drop=True),
                    s2010=s10[['country_id'] + SHARE_COLS].reset_index(drop=True),
                    source='data/processed/pew_harmonized.csv (Pew 2010 and 2020; Folk/Other split by WRP proxy)',
                    folk_method=fm)
    fb = RESULTS5 / 'headline_country_shares.csv'
    if not fb.exists():
        raise FileNotFoundError('Need data/processed/pew_harmonized.csv (run Step 2) or results_step5/')
    df = pd.read_csv(fb)
    df = df[df.year.eq(2020)].copy()
    out = df[['country_id']].copy()
    for c in CATS:
        out[f'share_{c}'] = df[f'mean_{c}'].to_numpy(float)
    tot = out[SHARE_COLS].sum(1)
    out[SHARE_COLS] = out[SHARE_COLS].div(tot, axis=0)
    _note('start_state', 'fallback', f'results_step5 2020 start state ({len(out)} countries); Pew 2010 unavailable')
    return dict(s2020=out.reset_index(drop=True), s2010=None,
                source='results_step5/headline_country_shares.csv (Pew 2020 start state of Step 5D)',
                folk_method=None)


# --------------------------------------------------------------------- WRP and maps
def wrp_and_geography():
    wrp, wpp_h, geo, nbrs = H.load_all(RAW, RAW / 'ne_50m_admin_0_countries.zip')
    _note('wrp', 'used', f'{int(wrp.use.sum())} usable country-years of {len(wrp)}')
    _note('natural_earth', 'used', f'{len(geo)} map units')
    return wrp, geo, nbrs


# ------------------------------------------------------------------ bilateral stocks
_IMS_MEMO = {}


def ims_bilateral(wpp):
    """Bilateral migrant stocks: DataFrame(origin_iso3, dest_iso3, year, migrants) or None.
    Reads the UN DESA IMS 2024 workbook (both-sexes block) or a tidy CSV."""
    tidy = _extra_file('migrant_stock_bilateral.csv')
    old = RAW / 'migrant_bilateral.csv'
    for p in (tidy, old):
        if p.exists():
            df = pd.read_csv(p, dtype=str)
            if 'year' not in df:
                df['year'] = '2020'
            df['migrants'] = pd.to_numeric(df.migrants.str.replace(',', ''), errors='coerce')
            df['year'] = pd.to_numeric(df.year, errors='coerce')
            df = df.dropna(subset=['migrants', 'year'])
            _note('bilateral_stock', 'used', f'{p.name}: {len(df)} rows')
            return df[['origin_iso3', 'dest_iso3', 'year', 'migrants']]
    xl = config.find_extra('undesa_pd_*ims_stock_by_sex_destination_and_origin*.xlsx')
    if not xl:
        _note('bilateral_stock', 'missing', 'migration pattern = gravity (geography only)')
        return None
    # Parsing the workbook takes minutes on some machines and validation builds many contexts, so the
    # parsed table is kept in memory and in a cache file that is rebuilt whenever the workbook is newer.
    cache = xl[-1].with_name('ims_bilateral_parsed.csv.gz')
    key = (str(xl[-1]), xl[-1].stat().st_mtime)
    if _IMS_MEMO.get('key') == key:
        _note('bilateral_stock', 'used', _IMS_MEMO['note'])
        return _IMS_MEMO['df'].copy()
    if cache.exists() and cache.stat().st_mtime >= xl[-1].stat().st_mtime:
        df = pd.read_csv(cache)
        note = f'{xl[-1].name}: {len(df)} country pairs x years, years {sorted(df.year.unique().astype(int))} (cached parse)'
        _IMS_MEMO.update(key=key, df=df, note=note)
        _note('bilateral_stock', 'used', note)
        return df.copy()
    print(f'Reading {xl[-1].name} (slow the first time; the parsed table is cached) ...', flush=True)
    raw = pd.read_excel(xl[-1], sheet_name=None, header=None)
    sheet = next((s for s in raw.values() if s.astype(str).apply(
        lambda c: c.str.contains('code of destination', case=False, na=False)).any().any()), None)
    if sheet is None:
        raise ValueError(f'{xl[-1].name}: no sheet with a "Location code of destination" header')
    hdr = int(np.flatnonzero(sheet.astype(str).apply(
        lambda r: r.str.contains('code of destination', case=False, na=False).any(), axis=1))[0])
    head = sheet.iloc[hdr].astype(str).str.strip()
    body = sheet.iloc[hdr + 1:].reset_index(drop=True)
    c_dest = int(np.flatnonzero(head.str.contains('code of destination', case=False))[0])
    c_orig = int(np.flatnonzero(head.str.contains('code of origin', case=False))[0])
    years = [(j, int(float(h))) for j, h in enumerate(head) if re.fullmatch(r'(19|20)\d\d(\.0)?', h)]
    seen, both = set(), []
    for j, y in years:              # first block of year columns = both sexes
        if y in seen:
            break
        seen.add(y)
        both.append((j, y))
    m = m49_to_iso3(wpp)
    dest = pd.to_numeric(body[c_dest], errors='coerce').map(m)
    orig = pd.to_numeric(body[c_orig], errors='coerce').map(m)
    rows = []
    for j, y in both:
        v = pd.to_numeric(body[j].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce')
        rows.append(pd.DataFrame({'origin_iso3': orig, 'dest_iso3': dest, 'year': y, 'migrants': v}))
    df = pd.concat(rows, ignore_index=True).dropna()
    df = df[df.migrants > 0]
    note = f'{xl[-1].name}: {len(df)} country pairs x years, years {sorted(seen)}'
    df.to_csv(cache, index=False, compression='gzip')
    _IMS_MEMO.update(key=key, df=df, note=note)
    _note('bilateral_stock', 'used', note)
    return df


def stock_matrix(df, ids, year):
    """[origin, destination] bilateral stock for the latest year <= `year`, or None."""
    if df is None:
        return None, None
    ys = sorted(int(y) for y in df.year.unique() if y <= year)
    if not ys:
        return None, None
    d = df[df.year.eq(ys[-1])]
    idx = {c: i for i, c in enumerate(ids)}
    d = d[d.origin_iso3.isin(idx) & d.dest_iso3.isin(idx)]
    S = np.zeros((len(ids), len(ids)))
    np.add.at(S, (d.origin_iso3.map(idx).to_numpy(int), d.dest_iso3.map(idx).to_numpy(int)), d.migrants.to_numpy(float))
    return S, ys[-1]


# -------------------------------------------------------------- religion of migrants
PEW7 = {'christian': 'Christianity', 'muslim': 'Islam', 'hindu': 'Hinduism', 'buddhist': 'Buddhism',
        'jew': 'Judaism', 'unaffiliated': 'Unaffiliated', 'other': 'Other'}


def pew_migrants(ids, folk_ratio):
    """Religion of migrants (Pew, 'Religious Composition of the World's Migrants, 1990-2020').
    Tidy CSV columns: country_iso3, side ('emigrants' = people born in the country living abroad,
    'immigrants' = foreign-born residents), year, and one column per Pew group (Christians, Muslims,
    Hindus, Buddhists, Jews, Other religions, Religiously unaffiliated; counts or shares).
    Pew's 'Other religions' includes folk religions; it is split with each country's Folk/Other
    ratio from the start state. Returns dict side -> [n, K] shares (NaN rows where absent) or None."""
    p = _extra_file('pew_migrants_religion.csv')
    if not p.exists():
        _note('migrant_religion', 'missing', 'no country-level Pew migrant file; religion of migrants from the '
              'affinity model calibrated to Pew published aggregates (inputs/migrant_religion_published.csv)')
        return None
    df = pd.read_csv(p)
    lower = {c: c.lower() for c in df.columns}
    out = {}
    for side in ('emigrants', 'immigrants'):
        sub = df[df[[c for c in df.columns if lower[c] == 'side'][0]].astype(str).str.lower().eq(side)]
        if sub.empty:
            continue
        ycol = [c for c in df.columns if lower[c] == 'year']
        if ycol:
            sub = sub[sub[ycol[0]] == sub[ycol[0]].max()]
        cc = [c for c in df.columns if lower[c] in ('country_iso3', 'iso3', 'country_id')][0]
        arr = np.full((len(ids), E.K), np.nan)
        idx = {c: i for i, c in enumerate(ids)}
        for _, r in sub.iterrows():
            if r[cc] not in idx:
                continue
            v = np.zeros(E.K)
            for col in df.columns:
                key = next((k for k in PEW7 if k in lower[col]), None)
                if key:
                    v[CATS.index(PEW7[key])] += float(r[col]) if pd.notna(r[col]) else 0.0
            i = idx[r[cc]]
            fo = v[CATS.index('Other')]
            v[CATS.index('Folk_Traditional')] = fo * folk_ratio[i]
            v[CATS.index('Other')] = fo * (1 - folk_ratio[i])
            if v.sum() > 0:
                arr[i] = v / v.sum()
        out[side] = arr
    _note('migrant_religion', 'used', f'{p.name}: sides {sorted(out)}')
    return out


# ------------------------------------------------------------------ survey switching
def _tracked_or_raw(name):
    frames = []
    for folder, label in [(TRACKED, 'tracked')] + [(d, 'user') for d in config.extra_dirs()]:
        p = folder / name
        if p.exists():
            f = pd.read_csv(p, comment='#')
            f['file'] = f'{label}:{name}'
            frames.append(f)
    return pd.concat(frames, ignore_index=True) if frames else None


def switching_observations(ids):
    """Survey lifetime switching cells: country_iso3, raised, current, percent (of adults raised in
    `raised`), n_raised (optional), source, url, verified (yes/no). Only verified rows are used.
    Returns DataFrame with columns country (index), raised (k), current (k), p, neff, source."""
    df = _tracked_or_raw('switching_lifetime_observed.csv')
    if df is None or df.empty:
        _note('switching_survey', 'missing', 'switching rates from the hierarchical model and net changes only')
        return None
    df = df[df.get('verified', 'yes').astype(str).str.lower().isin(['yes', 'true', '1'])]
    idx = {c: i for i, c in enumerate(ids)}
    name = {c.lower(): c for c in CATS} | {'unaffiliated': 'Unaffiliated', 'none': 'Unaffiliated',
                                           'folk': 'Folk_Traditional', 'jewish': 'Judaism', 'muslim': 'Islam',
                                           'christian': 'Christianity', 'hindu': 'Hinduism', 'buddhist': 'Buddhism'}
    rows = []
    for _, r in df.iterrows():
        c, ra, cu = r['country_iso3'], name.get(str(r['raised']).lower()), name.get(str(r['current']).lower())
        if c not in idx or ra is None or cu is None or not np.isfinite(r['percent']):
            continue
        rows.append({'country': idx[c], 'country_id': c, 'raised': CATS.index(ra), 'current': CATS.index(cu),
                     'p': float(r['percent']) / 100.0,
                     'neff': float(r['n_raised']) if 'n_raised' in r and pd.notna(r['n_raised']) else 300.0,
                     'source': r.get('source', ''), 'survey_year': r.get('survey_year', np.nan)})
    out = pd.DataFrame(rows)
    _note('switching_survey', 'used' if len(out) else 'empty',
          f'{len(out)} verified cells, {out.country_id.nunique() if len(out) else 0} countries')
    return out if len(out) else None


# Pew Research Center's six regions. A country's region is its Natural Earth continent, except that
# Pew separates the Middle East and North Africa from Africa and Asia, and splits the Americas.
MENA = {'DZA', 'BHR', 'EGY', 'IRN', 'IRQ', 'ISR', 'JOR', 'KWT', 'LBN', 'LBY', 'MAR', 'OMN', 'PSE',
        'QAT', 'SAU', 'SYR', 'TUN', 'ARE', 'YEM', 'ESH'}
NORTH_AMERICA = {'USA', 'CAN', 'BMU', 'GRL', 'SPM'}
_CONTINENT_REGION = {'Europe': 'Europe', 'Africa': 'Sub-Saharan Africa', 'Asia': 'Asia-Pacific',
                     'Oceania': 'Asia-Pacific', 'Seven seas (open ocean)': 'Asia-Pacific',
                     'North America': 'Latin America-Caribbean', 'South America': 'Latin America-Caribbean'}


def pew_regions(ids, continents):
    """Pew region name for each country [n], from its ISO3 code and Natural Earth continent."""
    out = []
    for c, cont in zip(ids, continents):
        if c in MENA:
            out.append('Middle East-North Africa')
        elif c in NORTH_AMERICA:
            out.append('North America')
        else:
            out.append(_CONTINENT_REGION.get(str(cont), 'Unknown'))
    return np.array(out, dtype=object)


def fertility_by_religion(ids, continents):
    """Published fertility by religious group, as ratios to the same source's own reference TFR.

    inputs/fertility_by_religion.csv holds world, regional and country rows (see its header). Only
    rows with verified=yes are used. Ratios, not levels, are returned, because the model multiplies
    a national TFR: a level from one source divided by a reference from another period would be
    wrong. Returns a dict with
        world      [K] ratio to the world TFR (nan where no figure exists)
        region     {region name: [K] ratios to that region's TFR}
        country    [n, K] ratios to the country's own national TFR (nan where none)
        measure    [n, K] the measure behind each country ratio ('' where none)
        region_of  [n] each country's Pew region
        rows       the rows actually used, for the provenance table
    """
    path = TRACKED / 'fertility_by_religion.csv'
    if not path.exists():
        raise FileNotFoundError(f'{path} is required (it is tracked in git)')
    df = pd.read_csv(path, comment='#')
    used = df[df.verified.astype(str).str.lower().isin(['yes', 'true', '1'])].copy()
    used['ratio'] = used.tfr / used.reference_tfr
    used = used[used.religion.isin(CATS)]
    idx = {c: i for i, c in enumerate(ids)}

    world = np.full(K, np.nan)
    for _, r in used[used.scope.eq('world')].iterrows():
        world[CATS.index(r.religion)] = r.ratio
    region: dict[str, np.ndarray] = {}
    for name, grp in used[used.scope.eq('region')].groupby('area'):
        arr = np.full(K, np.nan)
        for _, r in grp.iterrows():
            arr[CATS.index(r.religion)] = r.ratio
        region[name] = arr
    country = np.full((len(ids), K), np.nan)
    measure = np.full((len(ids), K), '', dtype=object)
    for _, r in used[used.scope.eq('country')].iterrows():
        if r.area in idx:
            country[idx[r.area], CATS.index(r.religion)] = r.ratio
            measure[idx[r.area], CATS.index(r.religion)] = r.measure
    n_country = int(np.isfinite(country).sum())
    _note('religion_fertility', 'used',
          f'{int(np.isfinite(world).sum())} world, {sum(int(np.isfinite(v).sum()) for v in region.values())} regional '
          f'({len(region)} regions), {n_country} country figures '
          f'({used[used.scope.eq("country")].area.nunique()} countries); {len(df) - len(used)} rows held back')
    return dict(world=world, region=region, country=country, measure=measure,
                region_of=pew_regions(ids, continents), rows=used)


def pew_2015_projection():
    """Pew Research Center's own 2010-2050 projection (The Future of World Religions, 2015).

    An independent published projection of the same quantity, in the same eight groups, used two
    ways: as an external benchmark for 2050, and as a yardstick for forecast skill, because Pew's
    2020 figure was a ten-year-ahead projection that can be scored against the measured 2020 start
    state. Returns a long DataFrame (year, level, area, religion, people) or None.

    The copy on disk is Pew's ROUNDED country table, so small populations are coarse; world and
    regional totals are unaffected."""
    p = _extra_file('pew2015_rounded_population.csv')
    if not p.exists():
        _note('pew_2015_projection', 'missing', 'no external benchmark comparison')
        return None
    df = pd.read_csv(p)
    cols = {'Christians': 'Christianity', 'Muslims': 'Islam', 'Hindus': 'Hinduism', 'Buddhists': 'Buddhism',
            'Jews': 'Judaism', 'Folk Religions': 'Folk_Traditional', 'Other Religions': 'Other',
            'Unaffiliated': 'Unaffiliated'}
    df['Country'] = df.Country.astype(str).str.strip()
    df['Region'] = df.Region.astype(str).str.strip()
    out = df.melt(id_vars=['Year', 'Region', 'Country'], value_vars=list(cols), var_name='pew_group',
                  value_name='people')
    out['religion'] = out.pew_group.map(cols)
    out['level'] = np.where(out.Country.eq('All Countries'),
                            np.where(out.Region.eq('World'), 'world', 'region'), 'country')
    out['area'] = np.where(out.level.eq('country'), out.Country,
                           np.where(out.level.eq('world'), 'WORLD', out.Region))
    out = out.rename(columns={'Year': 'year'})[['year', 'level', 'area', 'religion', 'people']]
    out['people'] = pd.to_numeric(out.people, errors='coerce')
    _note('pew_2015_projection', 'used', f'{out.year.nunique()} years, {out[out.level.eq("country")].area.nunique()} countries')
    return out.dropna(subset=['people'])


def unhcr_population(ids):
    """UNHCR refugee stocks by origin and asylum (Refugee Data Finder CSV). Returns DataFrame
    (year, origin_iso3, asylum_iso3, refugees) or None."""
    p = _extra_file('unhcr_population.csv')
    if not p.exists():
        _note('unhcr', 'missing', 'no separate displacement component (refugees are inside migrant stocks)')
        return None
    df = pd.read_csv(p, comment='#', low_memory=False)
    low = {c.lower().strip(): c for c in df.columns}
    pick = lambda *keys: next((low[k] for k in low if all(x in k for x in keys)), None)
    yc, oc, ac = pick('year'), pick('origin', 'iso'), pick('asylum', 'iso')
    rc = pick('refugees')
    if None in (yc, oc, ac, rc):
        raise ValueError(f'{p.name}: need year, origin ISO, asylum ISO and refugees columns; got {list(df.columns)}')
    out = pd.DataFrame({'year': pd.to_numeric(df[yc], errors='coerce'), 'origin_iso3': df[oc],
                        'asylum_iso3': df[ac], 'refugees': pd.to_numeric(df[rc], errors='coerce')}).dropna()
    _note('unhcr', 'used', f'{len(out)} rows {int(out.year.min())}-{int(out.year.max())}')
    return out


def catalogue():
    return dict(FOUND)
