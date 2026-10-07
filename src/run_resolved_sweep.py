#!/usr/bin/env python3
"""Resolved cell-2 sweep, driven by the lumped run's T1(t) files (one-way coupling).

Each case appends one row to <out>/resolved_results_<arrangement>.csv and writes its time series to
<out>/resolved_series/<case>.npz. Cases already present in the CSV are skipped, so the sweep can be resumed.
The conductance loop is outermost, so each factorisation serves every energy and duration at that conductance.

Usage:
  python3 run_resolved_sweep.py --out ../results --arrangement two           (all 42 cases, two strips, D7)
  python3 run_resolved_sweep.py --out ../results --arrangement one --energy median --tau 30   (series-string check)
"""
import argparse, csv, json, math, os, time
import numpy as np

import lumped_two_cell as LP
from resolved_cell2 import Cell2Model, lumped_one_way, t1_interpolator

LEVEL_KEYS = list(LP.LEVELS.keys())


def read_lumped(out):
    rows = {}
    with open(os.path.join(out, "lumped_results.csv")) as f:
        for r in csv.DictReader(f):
            rows[(float(r["E_body_J"]), float(r["tau_rel_s"]), float(r["G_bus_WK"]))] = r
    return rows


def fmt(x, nd=2):
    return "" if x is None else f"{x:.{nd}f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="../results")
    ap.add_argument("--arrangement", choices=["two", "one"], default="two")
    ap.add_argument("--energy", default="all", help="all, min, median, max")
    ap.add_argument("--tau", type=float, default=None)
    ap.add_argument("--g", type=float, nargs="*", default=None)
    ap.add_argument("--refine", type=float, default=1.0)
    ap.add_argument("--dt", type=float, default=0.1)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    energies = sorted(LP.E_BODY_LIST)
    if args.energy != "all":
        energies = [{"min": energies[0], "median": energies[1], "max": energies[2]}[args.energy]]
    taus = [args.tau] if args.tau is not None else LP.TAU_REL_LIST
    gs = args.g if args.g else LP.G_BUS_LIST
    lumped = read_lumped(args.out)
    os.makedirs(os.path.join(args.out, "resolved_series"), exist_ok=True)
    name = f"resolved_results_{args.arrangement}{args.tag}.csv"
    path = os.path.join(args.out, name)
    done = set()
    if os.path.exists(path):
        with open(path) as f:
            for r in csv.DictReader(f):
                done.add(r["case"])
    model = Cell2Model(args.refine)
    np.savez_compressed(os.path.join(args.out, "resolved_series", f"mesh_nodes_refine{args.refine:g}.npz"),
                        r=model.r_node, theta=model.th_node, z=model.z_node)
    log = open(os.path.join(args.out, f"sweep_{args.arrangement}{args.tag}.log"), "a")
    fields = None
    for g in gs:
        for e in energies:
            for tau in taus:
                case = f"{args.arrangement}_E{int(round(e))}_tau{int(tau)}_G{g}{args.tag}"
                if case in done:
                    continue
                t0 = time.time()
                t1f, _ = t1_interpolator(os.path.join(args.out, "t1_series", LP.series_name(e, tau, g)))
                g_pos, g_neg = (g / 2, g / 2) if args.arrangement == "two" else (0.0, g)
                res = model.run(t1f, t_end=LP.T_END, dt=args.dt, g_pos=g_pos, g_neg=g_neg)
                c_be, s_be = lumped_one_way(t1f, t_end=LP.T_END, dt=args.dt, g_bus=g)
                lrow = lumped[(round(e, 1), tau, g)]
                row = {"case": case, "arrangement": args.arrangement, "E_body_J": round(e, 1), "tau_rel_s": tau, "G_bus_WK": g,
                       "refine": args.refine, "dt_s": args.dt}
                for k in LEVEL_KEYS:
                    ls = lrow[k]
                    row[f"{k}_lumped_s"] = ls
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
                en = res["energy"]
                row.update({f"E_{k}_J": f"{v:.2f}" for k, v in en.items()})
                row["E_stored_J"] = f"{res['stored_J']:.2f}"
                row["energy_residual_rel"] = f"{(res['stored_J'] - res['net_in_J']) / max(abs(res['net_in_J']), 1e-9):.2e}"
                row["runtime_s"] = f"{time.time() - t0:.0f}"
                ser = res["series"]
                np.savez_compressed(os.path.join(args.out, "resolved_series", case + ".npz"),
                                    t=ser[:, 0], T1=ser[:, 1], Tmax=ser[:, 2], Tmean=ser[:, 3], imax=ser[:, 4].astype(int),
                                    t_be=s_be[::5, 0], T2_be=s_be[::5, 1])
                new = not os.path.exists(path)
                if fields is None:
                    fields = list(row.keys())
                with open(path, "a", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=fields)
                    if new:
                        w.writeheader()
                    w.writerow(row)
                msg = (f"{time.strftime('%H:%M:%S')} {case}: Tmax peak {pk['Tmax'] - 273.15:.1f} C at {pk['loc_peak']}, "
                       f"Tmean peak {pk['Tmean'] - 273.15:.1f} C, lumped peak {lrow['T2max_C']} C, {time.time() - t0:.0f} s")
                print(msg, flush=True)
                log.write(msg + "\n"); log.flush()


if __name__ == "__main__":
    main()
