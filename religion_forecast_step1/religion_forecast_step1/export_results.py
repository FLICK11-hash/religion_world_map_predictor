"""Collect the small results of a local Step 5 run into results_step5/, so they can be pushed to GitHub.

Run from this folder:  .\\.venv\\Scripts\\python.exe export_results.py
Only summaries and tables are copied. data/ and outputs/ stay out of git (they are git-ignored, and large).
Missing files are reported and skipped, so the script works after any subset of steps has run.
It also saves the output of verify_step5d.py and the git commit the results came from.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
SOURCES = {
    "data/hindcast_step5e": ["hindcast_summary.csv", "hindcast_by_decade.csv",
                             "projection_2010_2050.csv", "group_tfr_predicted.csv"],
    "data/forecasts_step5d": ["step5d_report.json", "scenario_change_summary.csv", "global_share_uncertainty.csv",
                              "global_share_by_run.csv", "global_vs_pew2015_2050.csv", "hindcast_diagnostics.csv",
                              "hindcast_phi_scan.csv", "scenario_parameters.csv", "migration_by_religion.csv",
                              "unaffiliated_decomposition.csv"],
}
PURPOSE = {
    "hindcast_summary.csv": "Step 5E history tests: error by model, chosen on 1960-1980, scored on 1990 and 2000",
    "hindcast_by_decade.csv": "Step 5E every decade, model and setting, with per-religion errors and sign accuracy",
    "projection_2010_2050.csv": "WRP 2010 shares projected to 2050 with migration by religion (central settings)",
    "group_tfr_predicted.csv": "Predicted fertility by religion for every country (low/central/high within-country gap)",
    "step5d_report.json": "Step 5D run settings, assumptions and counts",
    "scenario_change_summary.csv": "Step 5D: countries whose dominant group changes, by scenario and year",
    "global_share_uncertainty.csv": "Step 5D: world shares by year, headline scenario (mean and 5-95% band)",
    "global_share_by_run.csv": "Step 5D: world shares for every run, scenario and year (for the sensitivity table)",
    "global_vs_pew2015_2050.csv": "Step 5D: global shares in 2050 by scenario, against the Pew 2015 projection",
    "hindcast_diagnostics.csv": "Step 5D: Pew 2010-2020 hindcast by religion",
    "hindcast_phi_scan.csv": "Step 5D: Pew 2010-2020 hindcast error by within-country gap (phi)",
    "scenario_parameters.csv": "Step 5D: the drawn parameters for every run",
    "unaffiliated_decomposition.csv": "Step 5D: headline mechanisms switched off one at a time (where a share change comes from)",
    "migration_by_religion.csv": "Step 5D: inflow, outflow and net by country and religion, 2020-2050 and 2020-2100",
    "headline_country_shares.csv": "Step 5D headline: country shares and population in selected years (mean over runs)",
    "verify_step5d_output.txt": "Output of verify_step5d.py on this run (integrity checks and diagnostics)",
}


def git_commit():
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown (not run inside a git checkout)"


def headline_shares(dest: Path):
    src = ROOT / "data" / "forecasts_step5d" / "country_year_uncertainty.csv"
    if not src.exists():
        return False
    df = pd.read_csv(src, low_memory=False)
    df = df[df.year.isin([2020, 2050, 2100, 2200, 3026])]
    cols = ["country_id", "year", "most_likely_dominant", "dominant_agreement_fraction", "mean_population"]
    cols += [c for c in df.columns if c.startswith("mean_")]
    df[cols].to_csv(dest / "headline_country_shares.csv", index=False)
    return True


def run_verify(dest: Path):
    proc = subprocess.run([sys.executable, "verify_step5d.py"], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf8", errors="replace")
    text = proc.stdout + (("\nSTDERR:\n" + proc.stderr) if proc.stderr.strip() else "")
    (dest / "verify_step5d_output.txt").write_text(text, encoding="utf8")
    return proc.returncode


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dest", default="results_step5", help="output folder (inside this step folder)")
    args = ap.parse_args()
    dest = ROOT / args.dest
    dest.mkdir(parents=True, exist_ok=True)
    copied, missing = [], []
    for folder, names in SOURCES.items():
        for name in names:
            src = ROOT / folder / name
            if src.exists():
                shutil.copy2(src, dest / name)
                copied.append(name)
            else:
                missing.append(f"{folder}/{name}")
    if headline_shares(dest):
        copied.append("headline_country_shares.csv")
    code = run_verify(dest)
    copied.append("verify_step5d_output.txt")

    lines = ["# Step 5 results: index", "",
             f"- Exported: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
             f"- Code version (git commit): {git_commit()}",
             f"- verify_step5d.py exit code: {code} (0 means all integrity checks passed)", "",
             "| file | size (KB) | what it is |", "|---|---|---|"]
    for name in sorted(copied):
        size = (dest / name).stat().st_size / 1024
        lines.append(f"| {name} | {size:,.0f} | {PURPOSE.get(name, '')} |")
    if missing:
        lines += ["", "Not found (that step has not been run on this machine):"] + [f"- {m}" for m in missing]
    (dest / "RESULTS_INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    total = sum(f.stat().st_size for f in dest.iterdir()) / 1024 / 1024
    print(f"Wrote {len(copied)} files to {dest} ({total:.1f} MB). verify exit code {code}.")
    if missing:
        print("Missing (skipped):", *missing, sep="\n  ")


if __name__ == "__main__":
    main()
