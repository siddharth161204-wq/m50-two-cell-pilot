#!/usr/bin/env python3
"""Addendum v1.1: the four computations of predictions_addendum.md and their scoring (DECISIONS.md D28 to D32).

1. Intake split: heat taken in by cell 2 through the strips, the air gap and radiation from cell 1, and the busbar
   share, over 0 to 900 s (archived accounts, 49 runs) and up to the hottest node's first 183.5 C crossing (reruns
   of the eight headline cases, D28, D29).
2. Error measure of Yao and Battiato: e_mean = |T_mean - T_lumped| / 240 K, e_hot = |T_max - T_lumped| / 240 K,
   their largest values and first exceedance of 0.05 (D30).
3. Their dimensionless numbers (arXiv:2504.10119v1, Eq. 9) for a two-by-four module in air, against Eq. 13, and the
   busbar conductance in their units (D31).
4. Internal Biot number of a strip patch (D32).
Then the scorecard of P1 to P4, with the rules fixed in predictions_addendum.md.

Usage: python3 addendum.py --out ../results   -> results/addendum_intake.csv, addendum_error.csv, addendum_module.json,
       addendum_biot.csv, addendum_scorecard.json, addendum_numbers.json, addendum_error_series.npz
"""
import argparse, csv, glob, json, math, os
import numpy as np

import lumped_two_cell as LP
from mesh_cell2 import R_DISC, R_ANN_IN

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="../results")
args = ap.parse_args()
OUT = args.out
RER = os.path.join(OUT, "addendum_rerun")

T_SCALE = 240.0         # K: T_a + T_s1 + T_b + T_s2 of Yao and Battiato, Table 3 (0 + 120 + 0 + 120), Eq. 5b, 5c, 6
EPS_YARDSTICK = 0.05    # their test cases' upscaling error (Section 4.1, 4.2); a yardstick, not a property of this module
LEVEL = LP.T_INITIAL_MEAN   # 183.5 C
E_HEAD = max(LP.E_BODY_LIST)
G_HEAD = (0.5, 0.2, 0.1, 0.05)
TAUS = (10.0, 30.0)


def f(x):
    return None if x in ("", None) else float(x)


def first_above(t, e, thr):
    """First time e exceeds thr, linear between samples (D14, D30); None if never."""
    idx = np.nonzero(e > thr)[0]
    if not len(idx):
        return None
    k = idx[0]
    if k == 0:
        return float(t[0])
    return float(t[k - 1] + (thr - e[k - 1]) / (e[k] - e[k - 1]) * (t[k] - t[k - 1]))


def rnd(x, n):
    return None if x is None else round(float(x), n)


rows = {}
for arr in ("two", "one"):
    for r in csv.DictReader(open(os.path.join(OUT, f"resolved_results_{arr}.csv"))):
        rows[r["case"]] = r
cases = sorted(rows, key=lambda c: (rows[c]["arrangement"] != "two", float(rows[c]["E_body_J"]), float(rows[c]["tau_rel_s"]),
                                    float(rows[c]["G_bus_WK"])))

# ---------------------------------------------------------------- reruns (D28): reproduction and per-step balance
rerun = {}
rerun_check_path = os.path.join(OUT, "addendum_rerun_check.json")
rerun_check = json.load(open(rerun_check_path)) if os.path.exists(rerun_check_path) else {}
for tau in TAUS:
    for g in G_HEAD:
        case = f"two_E{int(round(E_HEAD))}_tau{int(tau)}_G{g}"
        p = os.path.join(RER, f"addendum_flux_{case}.npz")
        if os.path.exists(p):
            rerun[case] = np.load(p)
reproduced = {c: (c in rerun_check and not rerun_check[c]["fields_differing_except_runtime"]) for c in rerun}

# ---------------------------------------------------------------- 1. intake split
intake_rows = []
for c in cases:
    r = rows[c]
    bus, gap, rad = f(r["E_in_bus_J"]), f(r["E_in_gap_J"]), f(r["E_in_rad_J"])
    conv, radout, stored = f(r["E_out_conv_J"]), f(r["E_out_rad_J"]), f(r["E_stored_J"])
    intake = bus + gap + rad
    row = {"case": c, "arrangement": r["arrangement"], "E_body_J": r["E_body_J"], "tau_rel_s": r["tau_rel_s"],
           "G_bus_WK": r["G_bus_WK"],
           "bus_900s_J": bus, "gap_900s_J": gap, "radiation_900s_J": rad, "intake_900s_J": round(intake, 2),
           "room_loss_900s_J": round(conv + radout, 2), "stored_900s_J": stored,
           "busbar_share_900s": round(bus / intake, 4), "gap_share_900s": round(gap / intake, 4),
           "radiation_share_900s": round(rad / intake, 4), "archived_residual_rel": r["energy_residual_rel"]}
    t_hot = f(r["T_initial_mean_resolved_max_s"])
    row["hottest_node_183.5C_s"] = t_hot
    for k in ("bus", "gap", "radiation", "room_loss", "stored", "intake", "busbar_share", "gap_share", "radiation_share",
              "balance_residual_rel_max_per_step"):
        row[f"{k}_to_crossing"] = None
    if c in rerun:
        z = rerun[c]
        cols = list(z["energy_columns"])
        es = z["energy"]
        col = {k: es[:, i] for i, k in enumerate(cols)}
        net = col["in_bus_J"] + col["in_gap_J"] + col["in_rad_J"] + col["in_vol_J"] - col["out_conv_J"] - col["out_rad_J"]
        gross = col["in_bus_J"] + col["in_gap_J"] + col["in_rad_J"] + col["in_vol_J"] + col["out_conv_J"] + col["out_rad_J"]
        row["balance_residual_rel_max_per_step_to_900s"] = float(np.abs(col["stored_J"] - net).max() / gross[-1])
        # crossing recomputed from the 0.1 s series exactly as the solver times it (linear within the step, D14)
        t, tm = z["t"], z["Tmax"]
        k = int(np.argmax(tm >= LEVEL)) if np.any(tm >= LEVEL) else None
        if k is not None:
            tc = float(t[k - 1] + (t[k] - t[k - 1]) * (LEVEL - tm[k - 1]) / (tm[k] - tm[k - 1]))
            w = (tc - es[k - 1, 0]) / (es[k, 0] - es[k - 1, 0])
            at = {kk: float(col[kk][k - 1] + w * (col[kk][k] - col[kk][k - 1])) for kk in cols}
            ib = at["in_bus_J"] + at["in_gap_J"] + at["in_rad_J"]
            row.update({"crossing_from_rerun_series_s": round(tc, 4), "bus_to_crossing": round(at["in_bus_J"], 3),
                        "gap_to_crossing": round(at["in_gap_J"], 3), "radiation_to_crossing": round(at["in_rad_J"], 3),
                        "room_loss_to_crossing": round(at["out_conv_J"] + at["out_rad_J"], 3),
                        "stored_to_crossing": round(at["stored_J"], 3), "intake_to_crossing": round(ib, 3),
                        "busbar_share_to_crossing": round(at["in_bus_J"] / ib, 4),
                        "gap_share_to_crossing": round(at["in_gap_J"] / ib, 4),
                        "radiation_share_to_crossing": round(at["in_rad_J"] / ib, 4)})
            kk = k
            row["balance_residual_rel_max_per_step_to_crossing"] = float(np.abs(col["stored_J"][:kk + 1] - net[:kk + 1]).max()
                                                                         / gross[kk])
        row["rerun_reproduces_archived_row"] = reproduced[c]
    intake_rows.append(row)
keys = []
for r in intake_rows:
    keys += [k for k in r if k not in keys]
with open(os.path.join(OUT, "addendum_intake.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=keys)
    w.writeheader()
    w.writerows(intake_rows)
IN = {r["case"]: r for r in intake_rows}

# ---------------------------------------------------------------- 2. error measure
err_rows, err_series = [], {}
for c in cases:
    r = rows[c]
    e, tau, g = float(r["E_body_J"]), float(r["tau_rel_s"]), float(r["G_bus_WK"])
    z = np.load(os.path.join(OUT, "resolved_series", c + ".npz"))
    lum = np.loadtxt(os.path.join(OUT, "t1_series", LP.series_name(e, tau, g)), delimiter=",", skiprows=1)
    idx = np.rint(z["t"] / 0.1).astype(int)                       # archived samples sit on the 0.1 s grid
    assert np.allclose(lum[idx, 0], z["t"], atol=1e-9)
    t1_check = float(np.abs(lum[idx, 1] + 273.15 - z["T1"]).max())   # same cell 1 history (CSV written to 1e-4 C)
    T_l = lum[idx, 2] + 273.15
    e_mean = np.abs(z["Tmean"] - T_l) / T_SCALE
    e_hot = np.abs(z["Tmax"] - T_l) / T_SCALE
    out = {"case": c, "arrangement": r["arrangement"], "E_body_J": r["E_body_J"], "tau_rel_s": r["tau_rel_s"],
           "G_bus_WK": r["G_bus_WK"], "sampling_s": 0.5,
           "e_mean_peak": rnd(e_mean.max(), 5), "t_e_mean_peak_s": float(z["t"][e_mean.argmax()]),
           "e_mean_first_above_0.05_s": rnd(first_above(z["t"], e_mean, EPS_YARDSTICK), 3),
           "e_hot_peak": rnd(e_hot.max(), 5), "t_e_hot_peak_s": float(z["t"][e_hot.argmax()]),
           "e_hot_first_above_0.05_s": rnd(first_above(z["t"], e_hot, EPS_YARDSTICK), 3),
           "hottest_node_183.5C_s": f(r["T_initial_mean_resolved_max_s"]),
           "lumped_183.5C_s": f(r["T_initial_mean_lumped_s"]),
           "T1_series_check_max_abs_K": t1_check}
    if c in rerun:                                                   # 0.1 s samples of the rerun (D30)
        zr = rerun[c]
        T_l1 = lum[:, 2] + 273.15
        n = min(len(zr["t"]), len(T_l1))
        assert np.allclose(lum[:n, 0], zr["t"][:n], atol=1e-9)
        em1 = np.abs(zr["Tmean"][:n] - T_l1[:n]) / T_SCALE
        eh1 = np.abs(zr["Tmax"][:n] - T_l1[:n]) / T_SCALE
        out.update({"e_mean_peak_0.1s": rnd(em1.max(), 5), "e_mean_first_above_0.05_s_0.1s": rnd(first_above(zr["t"][:n], em1, EPS_YARDSTICK), 3),
                    "e_hot_peak_0.1s": rnd(eh1.max(), 5), "e_hot_first_above_0.05_s_0.1s": rnd(first_above(zr["t"][:n], eh1, EPS_YARDSTICK), 3),
                    "rerun_reproduces_archived_row": reproduced[c]})
    if c.startswith(f"two_E{int(round(E_HEAD))}_") and g in G_HEAD:
        err_series[c] = (z["t"], e_mean, e_hot)
    err_rows.append(out)
keys = []
for r in err_rows:
    keys += [k for k in r if k not in keys]
with open(os.path.join(OUT, "addendum_error.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=keys)
    w.writeheader()
    w.writerows(err_rows)
np.savez_compressed(os.path.join(OUT, "addendum_error_series.npz"),
                    **{f"{c}__{k}": v for c, (tt, em, eh) in err_series.items() for k, v in (("t", tt), ("e_mean", em), ("e_hot", eh))})
ER = {r["case"]: r for r in err_rows}

# ---------------------------------------------------------------- 3. Yao and Battiato's numbers for a module (D31)
pitch = LP.D_CELL + LP.GAP
L_pack = 4 * pitch
eps_mod = pitch / L_pack
V_cell = math.pi * (LP.D_CELL / 2) ** 2 * LP.L_CELL
U_pc = LP.G_GAP / LP.A_FACE
Pi_burn = E_HEAD / (30.0 * V_cell)
Bi_p = U_pc * L_pack / LP.K_AIR
vs_rad, vs_ax = LP.K_RADIAL / LP.K_AIR, LP.K_AXIAL / LP.K_AIR
R_num = Pi_burn * L_pack ** 2 / (T_SCALE * LP.K_AIR)


def judge(value, k):
    n = int(round(math.log(value) / math.log(eps_mod)))
    return {"value": value, "required_order_power_of_epsilon": k, "nearest_power_of_epsilon": n, "violated": n != k,
            "factor_relative_to_condition": value / eps_mod ** k}


numbers = {
    "Bi_p (packing Biot number)": judge(Bi_p, 0),
    "varsigma (K_c / K_p), K_c across the layers 1.3 W/mK": judge(vs_rad, 0),
    "Bi_c (Bi_p / varsigma), K_c across the layers": judge(Bi_p / vs_rad, 0),
    "R (burn number), 33.2 kJ over 30 s": judge(R_num, -1),
    "varsigma, K_c along the layers 25 W/mK (reported beside)": judge(vs_ax, 0),
    "Bi_c, K_c along the layers (reported beside)": judge(Bi_p / vs_ax, 0),
}
no_burn_main = ["Bi_p (packing Biot number)", "varsigma (K_c / K_p), K_c across the layers 1.3 W/mK",
                "Bi_c (Bi_p / varsigma), K_c across the layers"]
bus_units = []
for g in LP.G_BUS_LIST:
    U_bus = g / LP.A_FACE
    Bi_bus = U_bus * L_pack / LP.K_AIR
    j = judge(Bi_bus, 0)
    bus_units.append({"G_bus_WK": g, "G_bus_over_G_gap": g / LP.G_GAP, "U_bus_W_m2K": U_bus, "Bi_bus": Bi_bus,
                      "nearest_power_of_epsilon": j["nearest_power_of_epsilon"], "factor_relative_to_order_1": Bi_bus})
module = {
    "source": "Y.N. Yao, I. Battiato, arXiv:2504.10119v1 (14 April 2025): Eq. 2, 3, 5b, 5c, 6, 9, 13; Table 3",
    "module": "two-by-four module of LG M50 cells (D 21.1 mm, L 70.1 mm) at 23.1 mm pitch in air (D31)",
    "inputs": {
        "unit cell side l_m (pitch, D_CELL + GAP)": pitch, "pack length max(L_x, L_y)_m (four pitches, Eq. 2)": L_pack,
        "epsilon (Eq. 3, l / max(L_x, L_y))": eps_mod, "K_p_W_mK (K_AIR)": LP.K_AIR,
        "K_c_W_mK across the layers (K_RADIAL)": LP.K_RADIAL, "K_c_W_mK along the layers (K_AXIAL)": LP.K_AXIAL,
        "U_pc_W_m2K (G_GAP / A_FACE = K_AIR / GAP)": U_pc, "G_GAP_WK": LP.G_GAP, "A_FACE_m2": LP.A_FACE,
        "T_max_K (Table 3, Eq. 5b, 5c)": T_SCALE, "V_cell_m3 (pi (D/2)^2 L)": V_cell,
        "Pi_burn_W_m3 (33,222.9 J over 30 s per cell volume)": Pi_burn,
        "rho_c C_c_J_m3K (C_CELL / V_cell)": LP.C_CELL / V_cell},
    "not_evaluated": {"varrho": "needs the packing's volumetric heat capacity, which v1.0.0 does not record (D31)",
                      "Q": "cooling-pipe flux; the module has no cooling pipe, so the term is absent (D31)"},
    "numbers": numbers,
    "violated_with_no_cell_burning": [k for k in no_burn_main if numbers[k]["violated"]],
    "violated_with_a_cell_burning_adds": [k for k in ["R (burn number), 33.2 kJ over 30 s"] if numbers[k]["violated"]],
    "busbar_in_their_units": bus_units,
    "rule": "a number required to be of order epsilon^k is violated when the integer nearest to ln(value)/ln(epsilon) is not k; "
            "factor = value / epsilon^k (predictions_addendum.md)",
}
json.dump(module, open(os.path.join(OUT, "addendum_module.json"), "w"), indent=2)

# ---------------------------------------------------------------- 4. internal Biot number of a strip patch (D32)
R_cell = LP.D_CELL / 2
A_disc = math.pi * R_DISC ** 2
A_ann = math.pi * (R_cell ** 2 - R_ANN_IN ** 2)
biot_rows = []
for g in LP.G_BUS_LIST:
    biot_rows.append({"G_bus_WK": g,
                      "Bi_cap_disc_two_strips": (g / 2 / A_disc) * R_cell / LP.K_RADIAL,
                      "Bi_annulus_two_strips": (g / 2 / A_ann) * R_cell / LP.K_RADIAL,
                      "Bi_annulus_one_strip": (g / A_ann) * R_cell / LP.K_RADIAL})
biot_cross = {"cap_disc_two_strips_G_bus_WK": 2 * LP.K_RADIAL * A_disc / R_cell,
              "annulus_two_strips_G_bus_WK": 2 * LP.K_RADIAL * A_ann / R_cell,
              "annulus_one_strip_G_bus_WK": LP.K_RADIAL * A_ann / R_cell,
              "A_disc_m2": A_disc, "A_annulus_m2": A_ann, "R_m": R_cell, "k_across_W_mK": LP.K_RADIAL}
with open(os.path.join(OUT, "addendum_biot.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(biot_rows[0].keys()))
    w.writeheader()
    w.writerows([{k: (f"{v:.4g}" if k != "G_bus_WK" else v) for k, v in r.items()} for r in biot_rows])

# ---------------------------------------------------------------- scorecard
def cases_at(g, arrangement="two", energy=None):
    return [c for c in cases if rows[c]["arrangement"] == arrangement and float(rows[c]["G_bus_WK"]) == g
            and (energy is None or abs(float(rows[c]["E_body_J"]) - round(energy, 1)) < 0.5)]


s500 = {c: IN[c]["busbar_share_900s"] for c in cases_at(0.5)}
s50 = {c: IN[c]["busbar_share_900s"] for c in cases_at(0.05)}
p1_miss = [c for c, v in s500.items() if not v > 0.80] + [c for c, v in s50.items() if not v < 0.50]
P1 = {"result": "Held" if not p1_miss else "Failed", "cases_missing": p1_miss,
      "busbar_share_900s_at_500mWK": s500, "busbar_share_900s_at_50mWK": s50,
      "range_500": [min(s500.values()), max(s500.values())], "range_50": [min(s50.values()), max(s50.values())],
      "central": {"500": 0.90, "50": 0.40}}


def decide(t_first, t_cross, c, key01):
    """t_first < t_cross with the 0.1 s samples deciding when the two lie within 0.5 s (D30)."""
    if t_first is None or t_cross is None:
        return t_first is not None and t_cross is None, "0.5 s"
    if abs(t_first - t_cross) < 0.5 and key01 in ER[c] and ER[c].get("rerun_reproduces_archived_row"):
        t01 = ER[c][key01]
        return (t01 is not None and t01 < t_cross), "0.1 s"
    return t_first < t_cross, "0.5 s"


p2 = {}
for c in cases_at(0.5, energy=E_HEAD):
    er = ER[c]
    before, basis = decide(er["e_mean_first_above_0.05_s"], er["hottest_node_183.5C_s"], c, "e_mean_first_above_0.05_s_0.1s")
    p2[c] = {"e_mean_peak": er["e_mean_peak"], "t_e_mean_peak_s": er["t_e_mean_peak_s"],
             "e_mean_first_above_0.05_s": er["e_mean_first_above_0.05_s"],
             "hottest_node_183.5C_s": er["hottest_node_183.5C_s"], "exceeds": er["e_mean_peak"] > EPS_YARDSTICK,
             "first_exceedance_before_hottest_node_crossing": before, "timing_basis": basis}
P2 = {"result": "Held" if all(v["exceeds"] and v["first_exceedance_before_hottest_node_crossing"] for v in p2.values()) else "Failed",
      "cases": p2, "central_peak": 0.08,
      "part_exceeds_0.05": all(v["exceeds"] for v in p2.values()),
      "part_first_before_hottest_node_183.5C": all(v["first_exceedance_before_hottest_node_crossing"] for v in p2.values())}

p3 = {}
for c in cases_at(0.1, energy=E_HEAD):
    er = ER[c]
    p3[c] = {"e_mean_peak": er["e_mean_peak"], "t_e_mean_peak_s": er["t_e_mean_peak_s"],
             "e_mean_first_above_0.05_s": er["e_mean_first_above_0.05_s"], "e_hot_peak": er["e_hot_peak"],
             "e_hot_first_above_0.05_s": er["e_hot_first_above_0.05_s"],
             "mean_never_above": er["e_mean_peak"] <= EPS_YARDSTICK, "hot_above": er["e_hot_peak"] > EPS_YARDSTICK}
P3 = {"result": "Held" if all(v["mean_never_above"] and v["hot_above"] for v in p3.values()) else "Failed", "cases": p3,
      "central_peak_mean": 0.03,
      "other_energies_reported_not_scored": {c: {"e_mean_peak": ER[c]["e_mean_peak"], "e_hot_peak": ER[c]["e_hot_peak"]}
                                             for c in cases_at(0.1) if c not in p3}}

viol = module["violated_with_no_cell_burning"]
a_ok = Bi_p > 10
bp_viol = "Bi_p (packing Biot number)" in viol
others = [k for k in viol if k != "Bi_p (packing Biot number)"]
P4 = {"result": ("Held" if a_ok and bp_viol and not others else "Held in part" if a_ok and bp_viol else "Failed"),
      "a_Bi_p": Bi_p, "a_holds": a_ok, "central": 40,
      "b_packing_condition_violated_with_no_cell_burning": bp_viol,
      "b_other_conditions_violated_with_no_cell_burning": others,
      "factors": {k: numbers[k]["factor_relative_to_condition"] for k in numbers}}

score = {"predictions_commit": "7b866bffd72b07b71521994ea5903fc1cb3c629d", "P1": P1, "P2": P2, "P3": P3, "P4": P4}
json.dump(score, open(os.path.join(OUT, "addendum_scorecard.json"), "w"), indent=2)

# ---------------------------------------------------------------- numbers quoted in the note and README
head = {c: IN[c] for c in IN if c in rerun}
numbers_out = {
    "busbar_share_900s_two_strips": {f"{g:g}": [min(IN[c]["busbar_share_900s"] for c in cases_at(g)),
                                                 max(IN[c]["busbar_share_900s"] for c in cases_at(g))] for g in LP.G_BUS_LIST},
    "busbar_share_900s_one_strip": {f"{float(rows[c]['G_bus_WK']):g}": IN[c]["busbar_share_900s"]
                                    for c in cases if rows[c]["arrangement"] == "one"},
    "headline_to_crossing": {c: {k: head[c].get(k) for k in ("crossing_from_rerun_series_s", "busbar_share_to_crossing",
                                                             "gap_share_to_crossing", "radiation_share_to_crossing",
                                                             "bus_to_crossing", "intake_to_crossing", "room_loss_to_crossing",
                                                             "busbar_share_900s")} for c in head},
    "error_headline": {c: {k: ER[c][k] for k in ("e_mean_peak", "t_e_mean_peak_s", "e_mean_first_above_0.05_s", "e_hot_peak",
                                                 "t_e_hot_peak_s", "e_hot_first_above_0.05_s", "hottest_node_183.5C_s")}
                       for c in ER if c.startswith(f"two_E{int(round(E_HEAD))}_") and float(rows[c]["G_bus_WK"]) in G_HEAD},
    "error_all_two_strip": {"e_mean_peak_max": max(ER[c]["e_mean_peak"] for c in ER if rows[c]["arrangement"] == "two"),
                            "e_mean_cases_above_0.05": sorted(c for c in ER if ER[c]["e_mean_peak"] > EPS_YARDSTICK),
                            "e_hot_cases_above_0.05": sorted(c for c in ER if ER[c]["e_hot_peak"] > EPS_YARDSTICK)},
    "module": {"epsilon": eps_mod, "Bi_p": Bi_p, "varsigma_across": vs_rad, "varsigma_along": vs_ax,
               "Bi_c_across": Bi_p / vs_rad, "Bi_c_along": Bi_p / vs_ax, "R": R_num, "R_condition_value": 1 / eps_mod,
               "R_factor": R_num * eps_mod, "U_pc": U_pc,
               "Bi_bus_range_50_500": [Bi_p * 0.05 / LP.G_GAP, Bi_p * 0.5 / LP.G_GAP],
               "G_bus_over_G_gap_50_500": [0.05 / LP.G_GAP, 0.5 / LP.G_GAP]},
    "biot": {"crossing": biot_cross, "per_conductance": biot_rows},
    "rerun_reproduction": {c: reproduced[c] for c in rerun},
}
json.dump(numbers_out, open(os.path.join(OUT, "addendum_numbers.json"), "w"), indent=2)
print(json.dumps({k: score[k]["result"] for k in ("P1", "P2", "P3", "P4")}))
