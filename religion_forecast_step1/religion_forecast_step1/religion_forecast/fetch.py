"""Download the optional datasets into data/raw/extra/.

Run from the step folder (Windows PowerShell):
    .\\.venv\\Scripts\\python.exe run.py fetch              # official sources, mirrors as fallback
    .\\.venv\\Scripts\\python.exe run.py fetch --mirrors    # GitHub mirrors only (git must be installed)
    .\\.venv\\Scripts\\python.exe run.py fetch --convert-only C:\\path\\to\\mirrors  # already-cloned mirrors

What it fetches (all optional; Step 7 runs without them and says so in its reports):
  UN DESA International Migrant Stock 2024, destination x origin (xlsx, CC BY 3.0 IGO)
  UN WPP 2024 population by 5-year age group and sex (csv.gz, CC BY 3.0 IGO), condensed to
      WPP2024_age5_condensed.csv.gz (years divisible by 5, ages 0-4 ... 80+, total and female)
  UNHCR refugee population statistics by origin and asylum (CC BY 4.0)
  World Bank WDI: GDP per capita PPP and urban share (CC BY 4.0), for covariate tests
  Pew Research Center 2015 country projections 2010-2050 (for comparison only; Pew terms of use)
Needs manual download (free Pew account; see docs/STEP7_DATA_SOURCES.md):
  Pew 'Religious Composition of the World's Migrants, 1990-2020' -> data/raw/extra/pew_migrants_religion.csv
  Pew 2024 Global Attitudes microdata (switching) -> tabulate to switching_lifetime_observed.csv
Every downloaded file's SHA-256 is written to data/raw/extra/manifest.json.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from religion_forecast import config

RAW7 = config.RAW_EXTRA
WPP_BASE = 'https://population.un.org/wpp/assets/Excel%20Files/1_Indicator%20(Standard)/CSV_FILES/'
OFFICIAL = {
    'ims2024': dict(
        url='https://www.un.org/development/desa/pd/sites/www.un.org.development.desa.pd/files/'
            'undesa_pd_2024_ims_stock_by_sex_destination_and_origin.xlsx',
        file='undesa_pd_2024_ims_stock_by_sex_destination_and_origin.xlsx',
        note='URL pattern inferred from the UN page; if it fails, download from '
             'https://www.un.org/development/desa/pd/content/international-migrant-stock'),
    'wpp_age5': dict(url=WPP_BASE + 'WPP2024_PopulationByAge5GroupSex_Medium.csv.gz',
                     file='WPP2024_PopulationByAge5GroupSex_Medium.csv.gz', note='about 90 MB'),
    'unhcr': dict(url='https://api.unhcr.org/population/v1/population/?yearFrom=1951&yearTo=2025'
                      '&coo_all=true&coa_all=true&download=true',
                  file='unhcr_population_api.zip', note='zip with the data CSV and footnotes'),
    'wdi_gdp': dict(url='https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.PP.KD?downloadformat=csv',
                    file='wdi_gdp_pc_ppp.zip', note=''),
    'wdi_urban': dict(url='https://api.worldbank.org/v2/country/all/indicator/SP.URB.TOTL.IN.ZS?downloadformat=csv',
                      file='wdi_urban.zip', note=''),
    'pew2015': dict(url='https://assets.pewresearch.org/wp-content/uploads/sites/11/2015/04/'
                        'Religious_Composition_by_Country_2010-2050.xlsx',
                    file='pew2015_religious_composition_2010_2050.xlsx', note='comparison only'),
}
MIRRORS = {
    'ims2024': ('https://github.com/tigi/2026-migrant-stock', ['undesa_pd_2024_ims_stock_by_sex_destination_and_origin.xlsx']),
    'wpp_age5': ('https://github.com/open-numbers/ddf--unpop--wpp_population', ['population_age5']),
    'unhcr': ('https://github.com/rfordatascience/tidytuesday', ['data/2023/2023-08-22']),
    'wdi': ('https://github.com/open-numbers/ddf--open_numbers--world_development_indicators', [
        'datapoints/ddf--datapoints--ny_gdp_pcap_pp_kd--by--geo--time.csv',
        'datapoints/ddf--datapoints--sp_urb_totl_in_zs--by--geo--time.csv']),
    'pew2015': ('https://github.com/datasets/world-religion-projections', ['rounded_population.csv']),
}
AGE_LABELS = [f'{5 * i}-{5 * i + 4}' for i in range(16)] + ['80+']


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def wpp_locations():
    """M49 LocID -> ISO3 from the WPP indicators file already in data/raw."""
    w = pd.read_csv(config.RAW / 'WPP2024_Demographic_Indicators_Medium.csv.gz',
                    usecols=['LocID', 'ISO3_code'], low_memory=False).dropna().drop_duplicates('LocID')
    return dict(zip(w.LocID.astype(int), w.ISO3_code))


# ----------------------------------------------------------------------------- download
def download(url, dest, timeout=180):
    import requests
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=timeout, headers={'User-Agent': 'religion-forecast'}) as r:
        r.raise_for_status()
        tmp = dest.with_suffix(dest.suffix + '.part')
        with open(tmp, 'wb') as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    tmp.replace(dest)
    return dest


def clone_sparse(repo, paths, where):
    """git clone --depth 1 --filter=blob:none --sparse, then check out only `paths`."""
    where.mkdir(parents=True, exist_ok=True)
    target = where / repo.rstrip('/').split('/')[-1]
    if not target.exists():
        subprocess.run(['git', 'clone', '--depth', '1', '--filter=blob:none', '--sparse', repo, str(target)], check=True)
    subprocess.run(['git', '-C', str(target), 'sparse-checkout', 'set', '--no-cone', *paths], check=True)
    return target


# ---------------------------------------------------------------------------- converters
def condense_wpp_official(src, dst):
    """Official WPP2024_PopulationByAge5GroupSex_Medium.csv.gz -> condensed table."""
    cols = ['ISO3_code', 'Time', 'AgeGrp', 'PopTotal', 'PopFemale']
    df = pd.read_csv(src, usecols=lambda c: c in cols, low_memory=False).dropna(subset=['ISO3_code'])
    df = df[df.Time % 5 == 0]
    lo = df.AgeGrp.astype(str).str.extract(r'(\d+)')[0].astype(int)
    df['AgeGrp'] = [AGE_LABELS[min(v // 5, 16)] for v in lo]
    out = df.groupby(['ISO3_code', 'Time', 'AgeGrp'], as_index=False)[['PopTotal', 'PopFemale']].sum()
    out.to_csv(dst, index=False, compression='gzip')
    return len(out)


def condense_wpp_open_numbers(folder, dst):
    """open-numbers ddf--unpop--wpp_population population_age5 (M49 codes, thousands) -> condensed table."""
    loc = wpp_locations()
    rows = []
    for f in sorted(Path(folder).glob('ddf--datapoints--population--by--country_area--time--age_group_5year-*--sex.csv')):
        d = pd.read_csv(f)
        d = d[d.time % 5 == 0]
        d['ISO3_code'] = d.country_area.map(loc)
        d = d.dropna(subset=['ISO3_code'])
        ag = str(d.age_group_5year.iloc[0])
        lo = int(ag.split('_')[0].replace('plus', ''))
        d['AgeGrp'] = AGE_LABELS[min(lo // 5, 16)]
        tot = d.groupby(['ISO3_code', 'time', 'AgeGrp']).population.sum()
        fem = d[d.sex.eq(2)].groupby(['ISO3_code', 'time', 'AgeGrp']).population.sum()
        rows.append(pd.DataFrame({'PopTotal': tot, 'PopFemale': fem}).reset_index())
    out = pd.concat(rows).rename(columns={'time': 'Time'})
    out = out.groupby(['ISO3_code', 'Time', 'AgeGrp'], as_index=False)[['PopTotal', 'PopFemale']].sum()
    out.to_csv(dst, index=False, compression='gzip')
    return len(out)


def unhcr_from_tidytuesday(src, dst):
    d = pd.read_csv(src)
    out = pd.DataFrame({'year': d.year, 'origin_iso3': d.coo_iso, 'asylum_iso3': d.coa_iso,
                        'refugees': pd.to_numeric(d.refugees, errors='coerce'),
                        'asylum_seekers': pd.to_numeric(d.asylum_seekers, errors='coerce')})
    out.to_csv(dst, index=False)
    return len(out)


def unhcr_from_api_zip(src, dst):
    with zipfile.ZipFile(src) as z:
        name = next(n for n in z.namelist() if n.lower().endswith('.csv') and 'footnote' not in n.lower())
        raw = z.read(name).decode('utf-8', 'replace')
    lines = raw.splitlines()
    start = next(i for i, l in enumerate(lines) if l.lower().startswith('year'))
    d = pd.read_csv(io.StringIO('\n'.join(lines[start:])), na_values=['-'])
    num = lambda c: pd.to_numeric(d[c], errors='coerce')
    out = pd.DataFrame({'year': d['Year'], 'origin_iso3': d['Country of origin (ISO)'],
                        'asylum_iso3': d['Country of asylum (ISO)'],
                        'refugees': num("Refugees under UNHCR's mandate"), 'asylum_seekers': num('Asylum-seekers')})
    out.to_csv(dst, index=False)
    return len(out)


def wdi_from_open_numbers(files, dst):
    frames = []
    for f in files:
        d = pd.read_csv(f)
        val = [c for c in d.columns if c not in ('geo', 'time')][0]
        frames.append(d.rename(columns={val: {'ny_gdp_pcap_pp_kd': 'gdp_pc_ppp', 'sp_urb_totl_in_zs': 'urban_pct'}.get(val, val)})
                      .set_index(['geo', 'time']))
    out = pd.concat(frames, axis=1).reset_index().rename(columns={'geo': 'iso3', 'time': 'year'})
    out['iso3'] = out.iso3.str.upper()
    out.to_csv(dst, index=False)
    return len(out)


# ------------------------------------------------------------------------------- main
def from_folder(mirror_root, manifest):
    """Convert already-cloned mirrors found anywhere under mirror_root."""
    root = Path(mirror_root)
    found = lambda pattern: sorted(root.rglob(pattern))
    ims = found('undesa_pd_2024_ims_stock_by_sex_destination_and_origin.xlsx')
    if ims:
        shutil.copy2(ims[0], RAW7 / ims[0].name)
        manifest[ims[0].name] = dict(source=str(ims[0]), sha256=sha256(RAW7 / ims[0].name))
    age = [p.parent for p in found('ddf--datapoints--population--by--country_area--time--age_group_5year-0_4--sex.csv')]
    if age:
        n = condense_wpp_open_numbers(age[0], RAW7 / 'WPP2024_age5_condensed.csv.gz')
        manifest['WPP2024_age5_condensed.csv.gz'] = dict(source=f'open-numbers ddf ({age[0]})', rows=n,
                                                         sha256=sha256(RAW7 / 'WPP2024_age5_condensed.csv.gz'))
    tt = [p for p in found('population.csv') if '2023-08-22' in str(p)]
    if tt:
        n = unhcr_from_tidytuesday(tt[0], RAW7 / 'unhcr_population.csv')
        manifest['unhcr_population.csv'] = dict(source=f'tidytuesday 2023-08-22 ({tt[0]})', rows=n)
    wdi = found('ddf--datapoints--ny_gdp_pcap_pp_kd--by--geo--time.csv') + \
        found('ddf--datapoints--sp_urb_totl_in_zs--by--geo--time.csv')
    if wdi:
        n = wdi_from_open_numbers(wdi, RAW7 / 'wdi_covariates.csv')
        manifest['wdi_covariates.csv'] = dict(source='open-numbers WDI', rows=n)
    pew = [p for p in found('rounded_population.csv') if 'religion' in str(p)]
    if pew:
        shutil.copy2(pew[0], RAW7 / 'pew2015_rounded_population.csv')
        manifest['pew2015_rounded_population.csv'] = dict(source=str(pew[0]), note='lossy rounding (<10,000 -> 10,000)')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--mirrors', action='store_true', help='use GitHub mirrors only')
    ap.add_argument('--convert-only', metavar='DIR', help='convert mirrors already cloned under DIR')
    args = ap.parse_args(argv)
    RAW7.mkdir(parents=True, exist_ok=True)
    mpath = RAW7 / 'manifest.json'
    manifest = json.loads(mpath.read_text()) if mpath.exists() else {}
    failed = []
    if args.convert_only:
        from_folder(args.convert_only, manifest)
    else:
        if not args.mirrors:
            for key, spec in OFFICIAL.items():
                dest = RAW7 / spec['file']
                try:
                    if not dest.exists():
                        print(f'downloading {key} ...')
                        download(spec['url'], dest)
                    manifest[spec['file']] = dict(source=spec['url'], sha256=sha256(dest),
                                                  downloaded_utc=datetime.now(timezone.utc).isoformat())
                except Exception as exc:                     # network, 404, proxy
                    print(f'  {key}: official download failed ({exc}); will try the GitHub mirror')
                    failed.append(key)
            if (RAW7 / 'WPP2024_PopulationByAge5GroupSex_Medium.csv.gz').exists():
                condense_wpp_official(RAW7 / 'WPP2024_PopulationByAge5GroupSex_Medium.csv.gz',
                                      RAW7 / 'WPP2024_age5_condensed.csv.gz')
            if (RAW7 / 'unhcr_population_api.zip').exists():
                unhcr_from_api_zip(RAW7 / 'unhcr_population_api.zip', RAW7 / 'unhcr_population.csv')
        todo = list(MIRRORS) if args.mirrors else [k for k in MIRRORS if k in failed or
                                                   (k == 'wdi' and {'wdi_gdp', 'wdi_urban'} & set(failed))]
        if todo:
            where = RAW7 / '_mirrors'
            for key in todo:
                repo, paths = MIRRORS[key]
                try:
                    clone_sparse(repo, paths, where)
                except Exception as exc:
                    print(f'  mirror {repo} failed: {exc}')
            from_folder(where, manifest)
    mpath.write_text(json.dumps(manifest, indent=2))
    print('data/raw/extra now holds:')
    for p in sorted(RAW7.iterdir()):
        if p.is_file():
            print(f'  {p.name:70s} {p.stat().st_size / 1e6:8.2f} MB')
    print('Manual (free Pew account): see docs/STEP7_DATA_SOURCES.md for the migrants-by-religion and switching data.')


if __name__ == '__main__':
    main()
