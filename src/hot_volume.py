#!/usr/bin/env python3
"""Exploratory, not pre-registered (D23): how much of the resolved cell 2 lies above each onset level.

The onset criteria are whole-cell ARC thresholds; the resolved model applies them to its hottest point. This
script reruns chosen cases and records, every step, the fraction of the cell volume at or above 169.0, 183.5,
198.0 and 255.7 C, and the largest fraction reached.
Usage: python3 hot_volume.py --out ../results --cases max:30:0.5 median:30:0.5 max:30:0.2 ...
"""
import argparse, json, os, time
import numpy as np

import lumped_two_cell as LP
from resolved_cell2 import Cell2Model, t1_interpolator

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="../results")
ap.add_argument("--cases", nargs="+", required=True, help="energy:tau:G, energy in min/median/max")
ap.add_argument("--arrangement", choices=["two", "one"], default="two")
args = ap.parse_args()
E = dict(zip(("min", "median", "max"), sorted(LP.E_BODY_LIST)))
levels_C = [169.0, 183.5, 198.0, 255.7]
levels = [LP.T_INITIAL_BAND[0], LP.T_INITIAL_MEAN, LP.T_INITIAL_BAND[1], LP.T_ONSET_BAND[0]]
m = Cell2Model(1.0)
path = os.path.join(args.out, f"hot_volume_{args.arrangement}.json")
out = json.load(open(path)) if os.path.exists(path) else {}
for c in args.cases:
    en, tau, g = c.split(":")
    tau, g = float(tau), float(g)
    key = f"{args.arrangement}_{en}_tau{int(tau)}_G{g}"
    if key in out:
        continue
    t0 = time.time()
    t1f, _ = t1_interpolator(os.path.join(args.out, "t1_series", LP.series_name(E[en], tau, g)))
    gp, gn = (g / 2, g / 2) if args.arrangement == "two" else (0.0, g)
    r = m.run(t1f, g_pos=gp, g_neg=gn, volume_levels=levels)
    vs = r["vol_series"]
    rec = {"E_body_J": E[en], "tau_rel_s": tau, "G_bus_WK": g}
    for i, (lv, lc) in enumerate(zip(levels, levels_C)):
        frac = vs[:, 1 + i]
        rec[f"max_volume_percent_above_{lc}"] = 100 * r["vol_fraction_max"][lv]
        rec[f"seconds_with_any_volume_above_{lc}"] = float((frac > 0).sum() * (vs[1, 0] - vs[0, 0]))
        rec[f"max_mass_equivalent_g_above_{lc}"] = r["vol_fraction_max"][lv] * LP.M_CELL * 1e3
    rec["runtime_s"] = time.time() - t0
    out[key] = rec
    np.savez_compressed(os.path.join(args.out, "resolved_series", f"hot_volume_{key}.npz"), vol=vs, levels_C=np.array(levels_C))
    json.dump(out, open(path, "w"), indent=2)
    print(key, {k: round(v, 4) for k, v in rec.items() if k.startswith("max_volume")}, flush=True)
