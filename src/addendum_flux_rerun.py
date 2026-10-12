#!/usr/bin/env python3
"""Addendum v1.1: rerun the eight headline cases with the flux accounting of DECISIONS.md D28.

Cases: 33.2 kJ, tau_rel 10 and 30 s, G_bus 500, 200, 100 and 50 mW/K, two strips, refine 1, dt 0.1 s, exactly as in
the registered sweep. The row is built as src/run_resolved_sweep.py builds it (same fields, same formats), so every
field can be compared with the archived row. Each case writes, into the rerun directory, one row of
resolved_results_two_<tag>.csv and addendum_flux_<case>.npz with the series every 0.1 s and the per-step energy record.

Run (workers split by conductance; MKL_NUM_THREADS=1, D22):
  python3 addendum_flux_rerun.py --out ../results --rerun ../results/addendum_rerun --g 0.5 0.2 --tag A
  python3 addendum_flux_rerun.py --out ../results --rerun ../results/addendum_rerun --g 0.1 0.05 --tag B
Compare with the archive (writes results/addendum_rerun_check.json):
  python3 addendum_flux_rerun.py --out ../results --rerun ../results/addendum_rerun --compare
"""
import argparse, csv, glob, json, math, os, time
import numpy as np

import lumped_two_cell as LP
from resolved_cell2 import Cell2Model, lumped_one_way, t1_interpolator

LEVEL_KEYS = list(LP.LEVELS.keys())
E_HEAD = max(LP.E_BODY_LIST)
TAUS = (10.0, 30.0)
G_HEAD = (0.5, 0.2, 0.1, 0.05)


def case_name(tau, g):
    return f"two_E{int(round(E_HEAD))}_tau{int(tau)}_G{g}"


def fmt(x, nd=2):
    return "" if x is None else f"{x:.{nd}f}"


def read_lumped(out):
    with open(os.path.join(out, "lumped_results.csv")) as f:
        return {(float(r["E_body_J"]), float(r["tau_rel_s"]), float(r["G_bus_WK"])): r for r in csv.DictReader(f)}


def run_cases(args):
    os.makedirs(args.rerun, exist_ok=True)
    lumped = read_lumped(args.out)
    path = os.path.join(args.rerun, f"resolved_results_two_{args.tag}.csv")
    model = Cell2Model(1.0)
    fields = None
    for g in args.g:
        for tau in TAUS:
            case = case_name(tau, g)
            if os.path.exists(os.path.join(args.rerun, f"addendum_flux_{case}.npz")):
                continue
            t0 = time.time()
            t1f, _ = t1_interpolator(os.path.join(args.out, "t1_series", LP.series_name(E_HEAD, tau, g)))
            res = model.run(t1f, t_end=LP.T_END, dt=0.1, g_pos=g / 2, g_neg=g / 2, record_every=0.1, energy_series=True)
            c_be, s_be = lumped_one_way(t1f, t_end=LP.T_END, dt=0.1, g_bus=g)
            lrow = lumped[(round(E_HEAD, 1), tau, g)]
            # --- row, as in src/run_resolved_sweep.py ---
            row = {"case": case, "arrangement": "two", "E_body_J": round(E_HEAD, 1), "tau_rel_s": tau, "G_bus_WK": g,
                   "refine": 1.0, "dt_s": 0.1}
            for k in LEVEL_KEYS:
                row[f"{k}_lumped_s"] = lrow[k]
                row[f"{k}_lumped_be_s"] = fmt(c_be[k])
                row[f"{k}_resolved_max_s"] = fmt(res["cross_max"][k])
                row[f"{k}_resolved_mean_s"] = fmt(res["cross_mean"][k])
                a = res["at_cross"][k]
                row[f"{k}_location"] = "" if a is None else a["loc"]
                row[f"{k}_geometry"] = "" if a is None else a["geom"]
                row[f"{k}_r_mm"] = "" if a is None else f"{a['r_mm']:.2f}"
                row[f"{k}_theta_deg"] = "" if a is None else f"{a['theta_deg']:.1f}"
                row[f"{k}_z_mm"] = "" if a is None else f"{a['z_mm']:.2f}"
                row[f"{k}_Tmax_minus_Tmean_K"] = "" if a is None else f"{a['Tmax_minus_Tmean_K']:.2f}"
            pk = res["peak"]
            row.update({"T1max_C": lrow["T1max_C"], "T2max_lumped_C": lrow["T2max_C"],
                        "T2max_lumped_be_C": f"{s_be[:, 1].max() - 273.15:.2f}",
                        "Tmax_resolved_peak_C": f"{pk['Tmax'] - 273.15:.2f}", "t_Tmax_peak_s": f"{pk['t_Tmax']:.1f}",
                        "location_at_peak": pk["loc_peak"], "geometry_at_peak": pk["geom_peak"],
                        "r_mm_at_peak": f"{1e3 * model.r_node[pk['imax']]:.2f}",
                        "theta_deg_at_peak": f"{math.degrees(model.th_node[pk['imax']]):.1f}",
                        "z_mm_at_peak": f"{1e3 * model.z_node[pk['imax']]:.2f}",
                        "Tmean_resolved_peak_C": f"{pk['Tmean'] - 273.15:.2f}"})
            row.update({f"E_{k}_J": f"{v:.2f}" for k, v in res["energy"].items()})
            row["E_stored_J"] = f"{res['stored_J']:.2f}"
            row["energy_residual_rel"] = f"{(res['stored_J'] - res['net_in_J']) / max(abs(res['net_in_J']), 1e-9):.2e}"
            row["runtime_s"] = f"{time.time() - t0:.0f}"
            # --- outputs ---
            ser, es = res["series"], res["energy_series"]
            np.savez_compressed(os.path.join(args.rerun, f"addendum_flux_{case}.npz"),
                                t=ser[:, 0], T1=ser[:, 1], Tmax=ser[:, 2], Tmean=ser[:, 3], imax=ser[:, 4].astype(int),
                                t_be=s_be[::5, 0], T2_be=s_be[::5, 1],
                                energy=es, energy_columns=np.array(res["energy_series_columns"]))
            new = not os.path.exists(path)
            fields = fields or list(row.keys())
            with open(path, "a", newline="") as f:
                w = csv.DictWriter(f, fieldnames=fields)
                if new:
                    w.writeheader()
                w.writerow(row)
            print(f"{time.strftime('%H:%M:%S')} {case}: hottest node 183.5 C at {row['T_initial_mean_resolved_max_s'] or 'none'} s, "
                  f"residual {row['energy_residual_rel']}, {row['runtime_s']} s", flush=True)


def compare(args):
    reg = {r["case"]: r for r in csv.DictReader(open(os.path.join(args.out, "resolved_results_two.csv")))}
    out = {}
    for p in sorted(glob.glob(os.path.join(args.rerun, "resolved_results_two_*.csv"))):
        for r in csv.DictReader(open(p)):
            o = reg[r["case"]]
            a = np.load(os.path.join(args.rerun, f"addendum_flux_{r['case']}.npz"))
            b = np.load(os.path.join(args.out, "resolved_series", r["case"] + ".npz"))
            n = len(b["t"])
            sub = {k: a[k][::5][:n] for k in ("t", "T1", "Tmax", "Tmean", "imax")}
            out[r["case"]] = {
                "fields_differing_except_runtime": [k for k in r if k != "runtime_s" and r[k] != o[k]],
                "hottest_node_183.5C_crossing_archived_s": o["T_initial_mean_resolved_max_s"],
                "hottest_node_183.5C_crossing_rerun_s": r["T_initial_mean_resolved_max_s"],
                "series_samples_compared": int(n),
                "max_abs_difference_at_archived_0.5s_samples": {k: float(np.abs(sub[k] - b[k]).max()) for k in ("t", "T1", "Tmax", "Tmean")},
                "imax_identical": bool(np.array_equal(sub["imax"], b["imax"])),
                "lumped_be_max_abs_difference": float(np.abs(a["T2_be"] - b["T2_be"]).max()),
                "runtime_s": r["runtime_s"],
            }
    json.dump(out, open(os.path.join(args.out, "addendum_rerun_check.json"), "w"), indent=2)
    for k, v in out.items():
        print(k, "differing:", v["fields_differing_except_runtime"], "series:", v["max_abs_difference_at_archived_0.5s_samples"],
              "imax identical:", v["imax_identical"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="../results")
    ap.add_argument("--rerun", default="../results/addendum_rerun")
    ap.add_argument("--g", type=float, nargs="*", default=list(G_HEAD))
    ap.add_argument("--tag", default="A")
    ap.add_argument("--compare", action="store_true")
    args = ap.parse_args()
    compare(args) if args.compare else run_cases(args)
