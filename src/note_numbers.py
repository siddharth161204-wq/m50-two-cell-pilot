#!/usr/bin/env python3
"""Every number quoted in the note, computed from the result files (so none is transcribed by hand).

Usage: python3 note_numbers.py --out ../results   -> results/note_numbers.json
"""
import argparse, csv, json, os, glob
import numpy as np

import lumped_two_cell as LP

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="../results")
args = ap.parse_args()
O = args.out
two = list(csv.DictReader(open(os.path.join(O, "resolved_results_two.csv"))))
E = sorted(LP.E_BODY_LIST)
f = lambda x: None if x in ("", None) else float(x)


def row(rows, e, tau, g):
    return next(r for r in rows if abs(float(r["E_body_J"]) - round(e, 1)) < 0.5 and float(r["tau_rel_s"]) == tau and float(r["G_bus_WK"]) == g)


N = {}
# headline 1: copper plate, maximum energy
for tau in (10.0, 30.0):
    r = row(two, E[2], tau, 0.5)
    tl, tr = f(r["T_initial_mean_lumped_s"]), f(r["T_initial_mean_resolved_max_s"])
    N[f"copper_maxE_tau{int(tau)}"] = {"lumped_s": tl, "resolved_max_s": tr, "difference_s": tl - tr, "ratio": tl / tr,
                                        "earlier_percent": 100 * (1 - tr / tl),
                                        "resolved_onset_low_s": f(r["T_onset_low_resolved_max_s"]),
                                        "resolved_onset_mean_s": f(r["T_onset_mean_resolved_max_s"]),
                                        "resolved_onset_high_s": f(r["T_onset_high_resolved_max_s"]),
                                        "dT_at_crossing_K": f(r["T_initial_mean_Tmax_minus_Tmean_K"]),
                                        "peak_lumped_C": f(r["T2max_lumped_C"]), "peak_resolved_mean_C": f(r["Tmean_resolved_peak_C"]),
                                        "peak_resolved_max_C": f(r["Tmax_resolved_peak_C"])}
    r = row(two, E[1], tau, 0.5)
    N[f"copper_medianE_tau{int(tau)}"] = {"lumped_peak_C": f(r["T2max_lumped_C"]), "resolved_max_s": f(r["T_initial_mean_resolved_max_s"]),
                                          "dT_at_crossing_K": f(r["T_initial_mean_Tmax_minus_Tmean_K"]),
                                          "peak_resolved_max_C": f(r["Tmax_resolved_peak_C"]), "peak_resolved_mean_C": f(r["Tmean_resolved_peak_C"])}
# headline 2: smallest conductance with only-resolved crossing, per level
only = {}
for k in LP.LEVELS:
    gs = sorted({float(r["G_bus_WK"]) for r in two if r[f"{k}_resolved_max_s"] and not r[f"{k}_lumped_s"]})
    only[k] = gs
N["only_resolved_G_by_level"] = only
N["only_resolved_case_count"] = {k: sum(1 for r in two if r[f"{k}_resolved_max_s"] and not r[f"{k}_lumped_s"]) for k in LP.LEVELS}
N["lumped_cross_case_count"] = {k: sum(1 for r in two if r[f"{k}_lumped_s"]) for k in LP.LEVELS}
N["resolved_max_cross_case_count"] = {k: sum(1 for r in two if r[f"{k}_resolved_max_s"]) for k in LP.LEVELS}
N["resolved_mean_cross_case_count"] = {k: sum(1 for r in two if r[f"{k}_resolved_mean_s"]) for k in LP.LEVELS}
for tau in (10.0, 30.0):
    r = row(two, E[2], tau, 0.2)
    N[f"G200_maxE_tau{int(tau)}"] = {"resolved_max_s": f(r["T_initial_mean_resolved_max_s"]), "lumped_peak_C": f(r["T2max_lumped_C"]),
                                     "peak_resolved_max_C": f(r["Tmax_resolved_peak_C"])}
    r = row(two, E[2], tau, 0.1)
    N[f"G100_maxE_tau{int(tau)}"] = {"resolved_low_s": f(r["T_initial_low_resolved_max_s"]), "lumped_peak_C": f(r["T2max_lumped_C"]),
                                     "peak_resolved_max_C": f(r["Tmax_resolved_peak_C"])}
# P5 reductions and the lumped-mean overestimate at 0.5 W/K
red = []
for e in E:
    for tau in (10.0, 30.0):
        r = row(two, e, tau, 0.5)
        rl, rm = f(r["T2max_lumped_C"]) - 25, f(r["Tmean_resolved_peak_C"]) - 25
        red.append({"E": e, "tau": tau, "reduction_percent": 100 * (1 - rm / rl), "lumped_minus_mean_K": rl - rm})
N["P5"] = red
# hottest point minus mean at peak, median energy tau 30, all G
dts = {}
for g in LP.G_BUS_LIST:
    r = row(two, E[1], 30.0, g)
    s = np.load(os.path.join(O, "resolved_series", r["case"] + ".npz"))
    i = int(np.argmax(s["Tmax"]))
    dts[g] = {"dT_at_peak_K": float(s["Tmax"][i] - s["Tmean"][i]), "t_peak_s": float(s["t"][i]), "location": r["location_at_peak"],
              "geometry": r["geometry_at_peak"]}
N["median_tau30_dT_at_peak"] = dts
# verification
vp = json.load(open(os.path.join(O, "verification_post.json")))
N["V1"] = {"max_rel_dev_percent": 100 * vp["V1"]["max_rel_dev_of_rise"], "max_abs_dev_K": vp["V1"]["max_abs_dev_K"],
           "max_rise_K": vp["V1"]["max_rise_lumped_K"], "energy_residual": vp["V1"]["energy_residual_rel"]}
N["V2_median_dt_half_peak_changes_K"] = vp["V2_peak_changes_K"]
N["V3"] = {k: vp["V3"][k] for k in ("peak_lumped_C", "peak_resolved_mean_C", "peak_resolved_max_C")}
for name in glob.glob(os.path.join(O, "v2_*.json")):
    v = json.load(open(name))
    base = row(two, v["E_body_J"], v["tau_rel_s"], v["G_bus_WK"])
    ch = {k: (None if (v["cross_max"][k] is None or not base[f"{k}_resolved_max_s"]) else v["cross_max"][k] - float(base[f"{k}_resolved_max_s"]))
          for k in LP.LEVELS}
    N[os.path.basename(name)[:-5]] = {"nodes": v["nodes"], "dt_s": v["dt_s"], "cross_max_changes_s": ch,
                                      "peak_Tmax_change_K": v["peak_Tmax_C"] - float(base["Tmax_resolved_peak_C"]),
                                      "peak_Tmean_change_K": v["peak_Tmean_C"] - float(base["Tmean_resolved_peak_C"])}
pr = os.path.join(O, "verification_post_refined.json")
if os.path.exists(pr):
    v = json.load(open(pr))
    N["V2_median_refined"] = {"nodes": v["nodes"], "peak_Tmax_change_K": v["peak_Tmax_C"] - vp["V2_base"]["peak_Tmax_C"],
                              "peak_Tmean_change_K": v["peak_Tmean_C"] - vp["V2_base"]["peak_Tmean_C"]}
N["V2_max_abs_change_hottest_crossing_s"] = {k: max(abs(x) for x in v["cross_max_changes_s"].values() if x is not None)
                                             for k, v in N.items() if k.startswith("v2_")}
N["energy_residual_max_abs"] = max(abs(float(r["energy_residual_rel"])) for r in two)
one = os.path.join(O, "resolved_results_one.csv")
if os.path.exists(one):
    ones = list(csv.DictReader(open(one)))
    N["one_strip"] = {float(r["G_bus_WK"]): {"Tmax_peak_C": f(r["Tmax_resolved_peak_C"]), "Tmean_peak_C": f(r["Tmean_resolved_peak_C"]),
                                              "t_183_s": f(r["T_initial_mean_resolved_max_s"]), "location": r["location_at_peak"],
                                              "geometry": r["geometry_at_peak"],
                                              "two_strip_Tmax_peak_C": f(row(two, E[1], 30.0, float(r["G_bus_WK"]))["Tmax_resolved_peak_C"]),
                                              "two_strip_t_183_s": f(row(two, E[1], 30.0, float(r["G_bus_WK"]))["T_initial_mean_resolved_max_s"])}
                      for r in ones}
hv = os.path.join(O, "hot_volume_two.json")
if os.path.exists(hv):
    N["hot_volume"] = json.load(open(hv))
    # first time a given share of the cell is at or above 183.5 C, interpolated linearly between the 0.5 s records (D23)
    for key, rec in N["hot_volume"].items():
        p = os.path.join(O, "resolved_series", f"hot_volume_{key}.npz")
        if not os.path.exists(p):
            continue
        d = np.load(p)
        vs, lv = d["vol"], [float(x) for x in d["levels_C"]]
        t, fr = vs[:, 0], vs[:, 1 + lv.index(183.5)]
        for pct in (0.1, 1.0):
            idx = np.nonzero(fr >= pct / 100)[0]
            if len(idx) == 0:
                rec[f"t_{pct:g}pct_above_183.5_s"] = None
                continue
            i = int(idx[0])
            rec[f"t_{pct:g}pct_above_183.5_s"] = float(t[i]) if i == 0 else \
                float(t[i - 1] + (pct / 100 - fr[i - 1]) / (fr[i] - fr[i - 1]) * (t[i] - t[i - 1]))
for mode in ("two_way", "isotropic"):
    p = os.path.join(O, f"sensitivity_{mode}.json")
    if not os.path.exists(p):
        continue
    S = json.load(open(p))
    N[f"sensitivity_{mode}"] = {}
    for key, v in S.items():
        b = row(two, v["E_body_J"], v["tau_rel_s"], v["G_bus_WK"])
        lum_rise = f(b["T2max_lumped_C"]) - 25
        N[f"sensitivity_{mode}"][key] = {
            "t183_hottest_s": v["cross_max_s"]["T_initial_mean"], "t183_hottest_one_way_s": f(b["T_initial_mean_resolved_max_s"]),
            "t169_mean_s": v["cross_mean_s"]["T_initial_low"], "peak_mean_C": v["peak_Tmean_C"], "peak_mean_one_way_C": f(b["Tmean_resolved_peak_C"]),
            "peak_hottest_C": v["peak_Tmax_C"], "peak_hottest_one_way_C": f(b["Tmax_resolved_peak_C"]), "lumped_peak_C": f(b["T2max_lumped_C"]),
            "lumped_minus_mean_K": f(b["T2max_lumped_C"]) - v["peak_Tmean_C"],
            "mean_rise_reduction_percent": 100 * (1 - (v["peak_Tmean_C"] - 25) / lum_rise),
            "T1_peak_C": v["T1_peak_C"], "T1_peak_lumped_pair_C": f(b["T1max_C"]), "dT_at_183_K": v["dT_at_183_K"],
            "location_at_peak": v["location_at_peak"], "energy_residual_rel": v["energy_residual_rel"]}
json.dump(N, open(os.path.join(O, "note_numbers.json"), "w"), indent=2)
print(json.dumps(N, indent=1)[:6000])
