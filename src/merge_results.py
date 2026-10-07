#!/usr/bin/env python3
"""Merge the sweep workers' CSVs into one table per arrangement, sorted, one row per case.

Usage: python3 merge_results.py --out ../results
"""
import argparse, csv, glob, os

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="../results")
args = ap.parse_args()
for arr in ("two", "one"):
    rows, fields = {}, None
    for p in sorted(glob.glob(os.path.join(args.out, f"resolved_results_{arr}_*.csv"))):
        with open(p) as f:
            rd = csv.DictReader(f)
            fields = fields or rd.fieldnames
            for r in rd:
                rows.setdefault(r["case"], r)          # first finished copy wins; duplicates are identical runs
    if not rows:
        continue
    key = lambda r: (float(r["E_body_J"]), float(r["tau_rel_s"]), float(r["G_bus_WK"]))
    with open(os.path.join(args.out, f"resolved_results_{arr}.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(sorted(rows.values(), key=key))
    print(arr, len(rows), "cases")
