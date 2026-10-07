#!/usr/bin/env python3
"""Exploratory sensitivity runs, not pre-registered (D25, D26).

--two-way    cell 1 is a lumped state inside the resolved time loop, so it loses exactly what the resolved cell 2 draws
             (the pre-registered runs drive cell 2 with T1(t) from the lumped pair, which loses what a lumped cell 2 draws)
--isotropic  the jelly roll's through-layer conductivity is raised to its in-plane value (25 W/mK), to test whether the
             low through-layer conductivity is what keeps the strip's heat at the terminal
Usage: python3 sensitivity.py --out ../results --mode two-way --cases max:10:0.5 max:30:0.5 median:30:0.5 max:30:0.2
"""
import argparse, json, os, time
import numpy as np

import lumped_two_cell as LP

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="../results")
ap.add_argument("--mode", choices=["two-way", "isotropic"], required=True)
ap.add_argument("--cases", nargs="+", required=True)
args = ap.parse_args()
if args.mode == "isotropic":
    LP.K_RADIAL = LP.K_AXIAL
from resolved_cell2 import Cell2Model, t1_interpolator   # imported after the conductivity is set

E = dict(zip(("min", "median", "max"), sorted(LP.E_BODY_LIST)))
m = Cell2Model(1.0)
path = os.path.join(args.out, f"sensitivity_{args.mode.replace('-', '_')}.json")
out = json.load(open(path)) if os.path.exists(path) else {}
for c in args.cases:
    en, tau, g = c.split(":")
    tau, g = float(tau), float(g)
    key = f"{en}_tau{int(tau)}_G{g}"
    if key in out:
        continue
    t0 = time.time()
    if args.mode == "two-way":
        r = m.run(lambda t: LP.T_AMB, g_pos=g / 2, g_neg=g / 2, cell1={"e_body": E[en], "tau": tau})
    else:
        t1f, _ = t1_interpolator(os.path.join(args.out, "t1_series", LP.series_name(E[en], tau, g)))
        r = m.run(t1f, g_pos=g / 2, g_neg=g / 2)
    s = r["series"]
    rec = {"E_body_J": E[en], "tau_rel_s": tau, "G_bus_WK": g, "mode": args.mode,
           "cross_max_s": r["cross_max"], "cross_mean_s": r["cross_mean"],
           "dT_at_183_K": None if r["at_cross"]["T_initial_mean"] is None else r["at_cross"]["T_initial_mean"]["Tmax_minus_Tmean_K"],
           "peak_Tmax_C": r["peak"]["Tmax"] - 273.15, "peak_Tmean_C": r["peak"]["Tmean"] - 273.15,
           "location_at_peak": r["peak"]["loc_peak"], "T1_peak_C": float(s[:, 1].max() - 273.15),
           "energy_residual_rel": (r["stored_J"] - r["net_in_J"]) / r["net_in_J"], "runtime_s": time.time() - t0}
    out[key] = rec
    np.savez_compressed(os.path.join(args.out, "resolved_series", f"sensitivity_{args.mode}_{key}.npz"),
                        t=s[:, 0], T1=s[:, 1], Tmax=s[:, 2], Tmean=s[:, 3])
    json.dump(out, open(path, "w"), indent=2, default=str)
    print(key, {k: rec[k] for k in ("peak_Tmax_C", "peak_Tmean_C", "T1_peak_C", "location_at_peak")},
          "183.5 at", rec["cross_max_s"]["T_initial_mean"], flush=True)
