#!/usr/bin/env python3
"""One V2 run: a single case at a chosen mesh refinement and time step (D17, D21).

Usage: python3 v2_case.py --out ../results --energy max --tau 30 --g 0.5 --refine 2 --dt 0.1
Writes results/v2_<energy>_tau<tau>_G<g>_refine<r>_dt<dt>.json with every crossing time, location and peak.
"""
import argparse, json, os, time
import numpy as np

import lumped_two_cell as LP
from resolved_cell2 import Cell2Model, t1_interpolator

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="../results")
ap.add_argument("--energy", choices=["min", "median", "max"], default="median")
ap.add_argument("--tau", type=float, default=30.0)
ap.add_argument("--g", type=float, default=0.05)
ap.add_argument("--refine", type=float, default=1.0)
ap.add_argument("--dt", type=float, default=0.1)
args = ap.parse_args()
e = dict(zip(("min", "median", "max"), sorted(LP.E_BODY_LIST)))[args.energy]
t0 = time.time()
t1f, _ = t1_interpolator(os.path.join(args.out, "t1_series", LP.series_name(e, args.tau, args.g)))
m = Cell2Model(args.refine)
r = m.run(t1f, dt=args.dt, g_pos=args.g / 2, g_neg=args.g / 2)
out = {"E_body_J": e, "tau_rel_s": args.tau, "G_bus_WK": args.g, "refine": args.refine, "dt_s": args.dt,
       "nodes": int(m.mesh.p.shape[1]), "cross_max": r["cross_max"], "cross_mean": r["cross_mean"], "at_cross": r["at_cross"],
       "peak_Tmax_C": r["peak"]["Tmax"] - 273.15, "t_peak_Tmax_s": r["peak"]["t_Tmax"], "loc_peak": r["peak"]["loc_peak"],
       "geom_peak": r["peak"]["geom_peak"], "peak_Tmean_C": r["peak"]["Tmean"] - 273.15,
       "energy_residual_rel": (r["stored_J"] - r["net_in_J"]) / r["net_in_J"], "runtime_s": time.time() - t0}
name = f"v2_{args.energy}_tau{int(args.tau)}_G{args.g}_refine{args.refine:g}_dt{args.dt:g}"
with open(os.path.join(args.out, name + ".json"), "w") as f:
    json.dump(out, f, indent=2, default=str)
np.savez_compressed(os.path.join(args.out, "resolved_series", name + ".npz"), t=r["series"][:, 0], T1=r["series"][:, 1],
                    Tmax=r["series"][:, 2], Tmean=r["series"][:, 3])
print(json.dumps({k: out[k] for k in ("cross_max", "cross_mean", "peak_Tmax_C", "peak_Tmean_C", "loc_peak", "runtime_s")}, indent=1, default=str))
