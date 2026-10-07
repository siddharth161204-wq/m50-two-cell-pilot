#!/usr/bin/env python3
"""V1 to V3 as the brief defines them; run only after the predictions commit is public (D16, D17).

V1  busbar strips and air-gap conduction off, radiation from cell 1 on (median energy, tau 30 s): the resolved
    mean against the lumped node at every time, and the resolved model's own energy account.
V2  median case (median energy, tau 30 s, G_bus 0.05 W/K): one mesh refinement (every spacing halved) and one
    time-step halving; the change in every crossing time and in the peaks.
V3  the same coupled case: resolved mean against the lumped node; that gap is the spatial effect, to be compared
    with the V2 changes, which are numerical.
Usage: python3 verify_post.py --out ../results [--skip-refined]
"""
import argparse, json, os, time
import numpy as np

import lumped_two_cell as LP
from resolved_cell2 import Cell2Model, lumped_one_way, t1_interpolator

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="../results")
ap.add_argument("--skip-refined", action="store_true")
ap.add_argument("--only-refined", action="store_true", help="run only the refined-mesh V2 case; writes verification_post_refined.json")
args = ap.parse_args()
Ta = LP.T_AMB
e_med = sorted(LP.E_BODY_LIST)[1]
tau, g = 30.0, 0.05
t1f, _ = t1_interpolator(os.path.join(args.out, "t1_series", LP.series_name(e_med, tau, g)))
res = {"case": {"E_body_J": e_med, "tau_rel_s": tau, "G_bus_WK": g}}
if args.only_refined:
    t0 = time.time()
    fine = Cell2Model(2.0)
    rf = fine.run(t1f, g_pos=g / 2, g_neg=g / 2)
    out = {"case": res["case"], "nodes": int(fine.mesh.p.shape[1]), "cross_max": rf["cross_max"], "cross_mean": rf["cross_mean"],
           "peak_Tmax_C": rf["peak"]["Tmax"] - 273.15, "peak_Tmean_C": rf["peak"]["Tmean"] - 273.15,
           "loc_peak": rf["peak"]["loc_peak"], "geom_peak": rf["peak"]["geom_peak"], "at_cross": rf["at_cross"],
           "energy_residual_rel": (rf["stored_J"] - rf["net_in_J"]) / rf["net_in_J"], "runtime_s": time.time() - t0}
    np.savez_compressed(os.path.join(args.out, "resolved_series", "V2_refined_median_case.npz"), t=rf["series"][:, 0],
                        T1=rf["series"][:, 1], Tmax=rf["series"][:, 2], Tmean=rf["series"][:, 3])
    with open(os.path.join(args.out, "verification_post_refined.json"), "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(json.dumps(out, indent=1, default=str))
    raise SystemExit(0)
base = Cell2Model(1.0)

# ---------------- V1 ----------------
t0 = time.time()
r = base.run(t1f, g_pos=0.0, g_neg=0.0, gap_on=False, rad_gain_on=True)
cl, sl = lumped_one_way(t1f, g_bus=0.0, gap_on=False, rad_gain_on=True)
ts = r["series"]
idx = (ts[:, 0] / 0.1).round().astype(int)
rise = sl[idx, 1] - Ta
dev = ts[:, 3] - sl[idx, 1]
ok = rise > 1.0
res["V1"] = {"max_rise_lumped_K": float(rise.max()), "max_abs_dev_K": float(np.abs(dev).max()),
             "max_rel_dev_of_rise": float(np.abs(dev[ok] / rise[ok]).max()),
             "dev_at_lumped_peak_K": float(dev[np.argmax(rise)]),
             "energy_in_rad_J": r["energy"]["in_rad"], "stored_J": r["stored_J"], "net_in_J": r["net_in_J"],
             "energy_residual_rel": (r["stored_J"] - r["net_in_J"]) / r["net_in_J"],
             "peak_Tmax_C": float(ts[:, 2].max() - 273.15), "peak_Tmean_C": float(ts[:, 3].max() - 273.15),
             "runtime_s": time.time() - t0}
res["V1_pass"] = res["V1"]["max_rel_dev_of_rise"] < 0.01 and abs(res["V1"]["energy_residual_rel"]) < 1e-3
os.makedirs(os.path.join(args.out, "resolved_series"), exist_ok=True)
np.savez_compressed(os.path.join(args.out, "resolved_series", "V1_radiation_only_median.npz"), t=ts[:, 0], T1=ts[:, 1],
                    Tmax=ts[:, 2], Tmean=ts[:, 3], T_lumped=sl[idx, 1])
print("V1", json.dumps(res["V1"], indent=1), flush=True)


def summary(rr):
    return {"cross_max": rr["cross_max"], "cross_mean": rr["cross_mean"],
            "peak_Tmax_C": rr["peak"]["Tmax"] - 273.15, "peak_Tmean_C": rr["peak"]["Tmean"] - 273.15,
            "loc_peak": rr["peak"]["loc_peak"], "at_cross": rr["at_cross"]}


# ---------------- V2 and V3 ----------------
t0 = time.time()
r_base = base.run(t1f, g_pos=g / 2, g_neg=g / 2)
c_be, s_be = lumped_one_way(t1f, g_bus=g)
res["V2_base"] = summary(r_base)
r_dt = base.run(t1f, dt=0.05, g_pos=g / 2, g_neg=g / 2)
res["V2_dt_half"] = summary(r_dt)
print("V2 base and dt/2 done", round(time.time() - t0), "s", flush=True)
ts = r_base["series"]
idx = (ts[:, 0] / 0.1).round().astype(int)
np.savez_compressed(os.path.join(args.out, "resolved_series", "V3_median_case.npz"), t=ts[:, 0], T1=ts[:, 1],
                    Tmax=ts[:, 2], Tmean=ts[:, 3], T_lumped=s_be[idx, 1])
res["V3"] = {"lumped_cross": c_be, "resolved_mean_cross": r_base["cross_mean"], "resolved_max_cross": r_base["cross_max"],
             "max_lumped_minus_resolved_mean_K": float((s_be[idx, 1] - ts[:, 3]).max()),
             "min_lumped_minus_resolved_mean_K": float((s_be[idx, 1] - ts[:, 3]).min()),
             "peak_lumped_C": float(s_be[:, 1].max() - 273.15), "peak_resolved_mean_C": float(ts[:, 3].max() - 273.15),
             "peak_resolved_max_C": float(ts[:, 2].max() - 273.15),
             "busbar_heat_resolved_J": r_base["energy"]["in_bus"]}
del base
if not args.skip_refined:
    t0 = time.time()
    fine = Cell2Model(2.0)
    r_fine = fine.run(t1f, g_pos=g / 2, g_neg=g / 2)
    res["V2_refined"] = summary(r_fine)
    res["V2_refined"]["nodes"] = int(fine.mesh.p.shape[1])
    print("V2 refined done", round(time.time() - t0), "s", flush=True)


def diff(a, b):
    return None if (a is None or b is None) else b - a


res["V2_changes_s"] = {}
for k in LP.LEVELS:
    d = {"dt_half_max": diff(res["V2_base"]["cross_max"][k], res["V2_dt_half"]["cross_max"][k]),
         "dt_half_mean": diff(res["V2_base"]["cross_mean"][k], res["V2_dt_half"]["cross_mean"][k])}
    if "V2_refined" in res:
        d["refined_max"] = diff(res["V2_base"]["cross_max"][k], res["V2_refined"]["cross_max"][k])
        d["refined_mean"] = diff(res["V2_base"]["cross_mean"][k], res["V2_refined"]["cross_mean"][k])
    res["V2_changes_s"][k] = d
res["V2_peak_changes_K"] = {"dt_half_Tmax": res["V2_dt_half"]["peak_Tmax_C"] - res["V2_base"]["peak_Tmax_C"],
                            "dt_half_Tmean": res["V2_dt_half"]["peak_Tmean_C"] - res["V2_base"]["peak_Tmean_C"]}
if "V2_refined" in res:
    res["V2_peak_changes_K"].update({"refined_Tmax": res["V2_refined"]["peak_Tmax_C"] - res["V2_base"]["peak_Tmax_C"],
                                     "refined_Tmean": res["V2_refined"]["peak_Tmean_C"] - res["V2_base"]["peak_Tmean_C"]})
with open(os.path.join(args.out, "verification_post.json"), "w") as f:
    json.dump(res, f, indent=2, default=str)
print(json.dumps({k: res[k] for k in ("V1_pass", "V2_changes_s", "V2_peak_changes_K", "V3")}, indent=1, default=str))
