#!/usr/bin/env python3
"""Score predictions.md against the results, exactly as the predictions define each test.

Reads results/lumped_results.csv, results/resolved_results_two.csv and writes results/prediction_scorecard.json
and results/resolved_summary.csv (one row per case, the columns the note and figure use).
Usage: python3 score_predictions.py --out ../results
"""
import argparse, csv, json, os

import lumped_two_cell as LP

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="../results")
args = ap.parse_args()


def f(x):
    return None if x in ("", None) else float(x)


res = list(csv.DictReader(open(os.path.join(args.out, "resolved_results_two.csv"))))
E = sorted(LP.E_BODY_LIST)
Emin, Emed, Emax = (round(e, 1) for e in E)
key = lambda r: (float(r["E_body_J"]), float(r["tau_rel_s"]), float(r["G_bus_WK"]))
R = {key(r): r for r in res}
assert len(R) == 42, f"expected 42 two-strip cases, found {len(R)}"
Ta = 25.0
score = {}

# P1
p1 = []
for e in (Emin, Emed, Emax):
    for tau in (10.0, 30.0):
        r = R[(e, tau, 0.005)]
        p1.append({"E": e, "tau": tau, "lumped_peak_C": f(r["T2max_lumped_C"]), "resolved_max_peak_C": f(r["Tmax_resolved_peak_C"]),
                   "location_at_peak": r["location_at_peak"]})
edge = LP.T_INITIAL_BAND[0] - 273.15
held = all(x["lumped_peak_C"] < edge and x["resolved_max_peak_C"] < edge for x in p1)
score["P1"] = {"held": held, "cases": p1}

# P2
p2 = []
for tau in (10.0, 30.0):
    r = R[(Emax, tau, 0.5)]
    tl, tr = f(r["T_initial_mean_lumped_s"]), f(r["T_initial_mean_resolved_max_s"])
    p2.append({"tau": tau, "lumped_s": tl, "resolved_max_s": tr,
               "earlier_fraction": None if (tl is None or tr is None) else 1 - tr / tl})
held = all(x["lumped_s"] is not None and x["resolved_max_s"] is not None and x["resolved_max_s"] < 0.5 * x["lumped_s"] for x in p2)
score["P2"] = {"held": held, "cases": p2}

# P3
only = []
for (e, tau, g), r in sorted(R.items()):
    for k in LP.LEVELS:
        if r[f"{k}_resolved_max_s"] and not r[f"{k}_lumped_s"]:
            only.append({"E": e, "tau": tau, "G": g, "level": k, "resolved_max_s": f(r[f"{k}_resolved_max_s"])})
g_only_mean = sorted({x["G"] for x in only if x["level"] == "T_initial_mean"})
p3a = g_only_mean[0] if g_only_mean else None
p3b = any(R[(Emax, tau, 0.5)]["T_onset_low_resolved_max_s"] for tau in (10.0, 30.0))
score["P3"] = {"held": bool(only) and p3a in (0.1, 0.2) and p3b, "any_only_resolved": bool(only),
               "smallest_G_only_resolved_T_initial_mean": p3a, "P3a_held": p3a in (0.1, 0.2),
               "P3b_held": bool(p3b), "only_resolved_cases": only}

# P4
labels = {g: R[(Emed, 30.0, g)]["location_at_peak"] for g in LP.G_BUS_LIST}
geoms = {g: R[(Emed, 30.0, g)]["geometry_at_peak"] for g in LP.G_BUS_LIST}
seq = [labels[g] for g in LP.G_BUS_LIST]
switches = sum(1 for a, b in zip(seq[:-1], seq[1:]) if a != b)
held = (labels[0.005] == "gap-facing surface" and labels[0.01] == "gap-facing surface" and
        all(labels[g] == "terminal end" for g in (0.1, 0.2, 0.5)) and switches == 1)
switch_at = next((g for g, a, b in zip(LP.G_BUS_LIST[1:], seq[:-1], seq[1:]) if a != b), None)
score["P4"] = {"held": held, "labels_at_peak": labels, "geometry_at_peak": geoms, "first_G_with_new_label": switch_at,
               "number_of_label_changes": switches}

# P5
p5 = []
for e in (Emin, Emed, Emax):
    for tau in (10.0, 30.0):
        r = R[(e, tau, 0.5)]
        rl, rr = f(r["T2max_lumped_C"]) - Ta, f(r["Tmean_resolved_peak_C"]) - Ta
        p5.append({"E": e, "tau": tau, "lumped_rise_K": rl, "resolved_mean_rise_K": rr, "reduction": 1 - rr / rl})
score["P5"] = {"held": all(x["reduction"] >= 0.15 for x in p5), "cases": p5}

with open(os.path.join(args.out, "prediction_scorecard.json"), "w") as fo:
    json.dump(score, fo, indent=2)

# compact per-case table
cols = ["E_body_J", "tau_rel_s", "G_bus_WK", "T1max_C", "T2max_lumped_C", "Tmean_resolved_peak_C", "Tmax_resolved_peak_C",
        "t_Tmax_peak_s", "location_at_peak", "geometry_at_peak"]
with open(os.path.join(args.out, "resolved_summary.csv"), "w", newline="") as fo:
    w = csv.writer(fo)
    head = cols + [f"{k}_{m}" for k in LP.LEVELS for m in ("lumped_s", "resolved_max_s", "resolved_mean_s", "location", "Tmax_minus_Tmean_K")]
    w.writerow(head)
    for kk in sorted(R):
        r = R[kk]
        w.writerow([r[c] for c in cols] + [r[f"{k}_{m}"] if r[f"{k}_{m}"] != "" else "never"
                                           for k in LP.LEVELS for m in ("lumped_s", "resolved_max_s", "resolved_mean_s", "location", "Tmax_minus_Tmean_K")])
print(json.dumps({k: v["held"] for k, v in score.items()}, indent=1))
print("P2", score["P2"]["cases"]); print("P3a smallest G", p3a, "P3b", p3b); print("P4", labels, "switch at", switch_at)
print("P5", [(x["E"], x["tau"], round(x["reduction"], 3)) for x in p5])
