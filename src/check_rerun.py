#!/usr/bin/env python3
"""Reproducibility check: compare a rerun of registered cases, made with the final code into a separate directory,
against the registered results (row by row and time series by time series).

Usage: python3 run_resolved_sweep.py --out <rerun dir> --arrangement two --energy max --tau 30 --g 0.5 --tag r
       python3 check_rerun.py --out ../results --rerun <rerun dir>      -> results/rerun_check.json
The rerun directory needs t1_series/ (a link to results/t1_series) and lumped_results.csv.
"""
import argparse, csv, glob, json, os
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="../results")
ap.add_argument("--rerun", required=True)
args = ap.parse_args()
reg = {}
for arr in ("two", "one"):
    p = os.path.join(args.out, f"resolved_results_{arr}.csv")
    if os.path.exists(p):
        reg.update({r["case"]: r for r in csv.DictReader(open(p))})
out = {}
for p in sorted(glob.glob(os.path.join(args.rerun, "resolved_results_*.csv"))):
    for r in csv.DictReader(open(p)):
        o = reg[r["case"]]
        fields = [k for k in r if k != "runtime_s" and r[k] != o[k]]
        a = np.load(os.path.join(args.rerun, "resolved_series", r["case"] + ".npz"))
        b = np.load(os.path.join(args.out, "resolved_series", r["case"] + ".npz"))
        out[r["case"]] = {"fields_differing_except_runtime": fields,
                          "max_abs_series_difference": {k: float(np.abs(a[k] - b[k]).max()) for k in a.files},
                          "rerun_row": r}
json.dump(out, open(os.path.join(args.out, "rerun_check.json"), "w"), indent=2)
for k, v in out.items():
    print(k, "differing fields:", v["fields_differing_except_runtime"], "series:", v["max_abs_series_difference"])
