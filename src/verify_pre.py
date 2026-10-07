#!/usr/bin/env python3
"""Checks that carry no information about the coupled cases, run before the predictions are written (D15).

V0  flux identity: each resolved boundary operator on a uniform field against the lumped formula for the same path.
V1a conservation: no paths, no room losses, the same uniform internal heat input in both models.
A1  steady radial conduction with uniform generation and a lateral Robin condition (analytic).
A2  steady axial conduction with uniform generation and near-isothermal ends (analytic).
Usage: python3 verify_pre.py --out ../results
"""
import argparse, json, math, os, time
import numpy as np
import scipy.sparse as sp

import lumped_two_cell as LP
from resolved_cell2 import Cell2Model, lumped_one_way, R, LZ, _Solver

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="../results")
ap.add_argument("--refine", type=float, default=1.0)
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)
t0 = time.time()
m = Cell2Model(args.refine)
res = {"mesh": {"nodes": int(m.mesh.p.shape[1]), "tets": int(m.mesh.t.shape[1]), **{k: v for k, v in m.mesh_info.items()}},
       "geometry_mesh_vs_exact": {k: v for k, v in m.geom.items()}}

# ---------------- V0 ----------------
Ta = LP.T_AMB
T1, T2 = 700.0, 350.0
Tu = np.full(m.C.shape, T2)
g = 0.1
v0 = {}
v0["busbar_two_strip"] = (2 * float(((g / 2) * m.d_pos_unit + (g / 2) * m.d_neg_unit) @ (T1 - Tu)), g * (T1 - T2))
v0["busbar_one_strip"] = (2 * float((g * m.d_neg_unit) @ (T1 - Tu)), g * (T1 - T2))
v0["air_gap"] = (2 * float(m.d_gap_unit @ (T1 - Tu)), LP.G_GAP * (T1 - T2))
v0["radiation_gain"] = (2 * float(m.g_rad.sum()) * (T1 ** 4 - Ta ** 4), LP.EPS ** 2 * LP.SIGMA * LP.F_VIEW * LP.A_LAT * (T1 ** 4 - Ta ** 4))
v0["room_convection"] = (2 * float(m.d_conv_unit @ (Tu - Ta)), LP.H_CONV * LP.A_CONV * (T2 - Ta))
v0["room_radiation"] = (2 * float(m.w_rad @ (Tu ** 4 - Ta ** 4)), LP.EPS * LP.SIGMA * LP.A_CELL * (T2 ** 4 - Ta ** 4))
net_res = (v0["busbar_two_strip"][0] + v0["air_gap"][0] + v0["radiation_gain"][0] - v0["room_convection"][0] - v0["room_radiation"][0])
net_script = LP.coupling(T1, T2, g) - LP.loss_to_ambient(T2)        # the lumped script's exchange form
v0["net_into_cell2_vs_script"] = (net_res, net_script)
res["V0"] = {k: {"resolved_W": a, "lumped_W": b, "rel_diff": (a - b) / b} for k, (a, b) in v0.items()}
res["V0_pass"] = all(abs(d["rel_diff"]) < 1e-3 for d in res["V0"].values())

# ---------------- V1a ----------------
def pulse(t, E=20e3, tau=30.0):
    return LP.q_release(t, E, tau)

no_t1 = lambda t: Ta
r = m.run(no_t1, t_end=300.0, dt=0.1, gap_on=False, rad_gain_on=False, conv_on=False, rad_loss_on=False,
          q_vol=pulse, q_shape="volume", record_every=0.5)
cl, sl = lumped_one_way(no_t1, t_end=300.0, dt=0.1, gap_on=False, rad_gain_on=False, conv_on=False, rad_loss_on=False, q_vol=pulse)
ts = r["series"]
idx = (ts[:, 0] / 0.1).round().astype(int)
rise = sl[idx, 1] - Ta
dev = np.abs(ts[:, 3] - sl[idx, 1])
res["V1a"] = {"max_abs_dev_K": float(dev.max()), "max_rel_dev_of_rise": float((dev[1:] / rise[1:]).max()),
              "final_rise_K": float(rise[-1]), "stored_J": r["stored_J"], "net_in_J": r["net_in_J"],
              "energy_residual_rel": (r["stored_J"] - r["net_in_J"]) / r["net_in_J"],
              "peak_Tmax_minus_Tmean_K": float((ts[:, 2] - ts[:, 3]).max())}
res["V1a_pass"] = res["V1a"]["max_rel_dev_of_rise"] < 1e-4

# ---------------- A1, steady radial ----------------
q3 = 2.0e5                    # W/m3, uniform in the roll
h = 100.0                     # W/m2K on the whole lateral surface, ends adiabatic
w_lat = m.w["lateral"]
A = (m.K_roll + sp.diags(h * w_lat)).tocsr()          # roll operator alone: the analytic solution has no can
x = _Solver(A).solve(q3 * m.w_vol + h * w_lat * Ta)
ana = Ta + q3 * R / (2 * h) + q3 * (R ** 2 - m.r_node ** 2) / (4 * LP.K_RADIAL)
res["A1_radial"] = {"max_rise_analytic_K": float(ana.max() - Ta), "max_abs_err_K": float(np.abs(x - ana).max()),
                    "rel_err": float(np.abs(x - ana).max() / (ana.max() - Ta))}

# ---------------- A2, steady axial ----------------
h_end = 1e7
w_end = m.w["top"] + m.w["bottom"]
A = (m.K_roll + sp.diags(h_end * w_end)).tocsr()
x = _Solver(A).solve(q3 * m.w_vol + h_end * w_end * Ta)
k_eff = LP.K_AXIAL
z = m.z_node
ana = Ta + q3 * z * (LZ - z) / (2 * k_eff) + q3 * LZ / (2 * h_end)
res["A2_axial"] = {"k_eff": k_eff, "max_rise_analytic_K": float(ana.max() - Ta), "max_abs_err_K": float(np.abs(x - ana).max()),
                   "rel_err": float(np.abs(x - ana).max() / (ana.max() - Ta))}
res["runtime_s"] = time.time() - t0
with open(os.path.join(args.out, f"verification_pre_refine{args.refine:g}.json"), "w") as f:
    json.dump(res, f, indent=2)
print(json.dumps({k: v for k, v in res.items() if k not in ("geometry_mesh_vs_exact",)}, indent=2))
