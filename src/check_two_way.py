#!/usr/bin/env python3
"""Check of the two-way coupling (D25): with the roll made nearly isothermal (conductivity 1e4 W/mK), the resolved
two-way run must reproduce the lumped pair of lumped_two_cell.py, cell 1 and cell 2 alike.
Usage: python3 check_two_way.py --out ../results
"""
import argparse, json, os
import numpy as np
import lumped_two_cell as LP
LP.K_RADIAL = LP.K_AXIAL = 1.0e4
from resolved_cell2 import Cell2Model

ap = argparse.ArgumentParser(); ap.add_argument("--out", default="../results"); args = ap.parse_args()
e, tau, g = sorted(LP.E_BODY_LIST)[2], 30.0, 0.5
m = Cell2Model(1.0)
r = m.run(lambda t: LP.T_AMB, g_pos=g / 2, g_neg=g / 2, cell1={"e_body": e, "tau": tau})
s = r["series"]
ref = np.loadtxt(os.path.join(args.out, "t1_series", LP.series_name(e, tau, g)), delimiter=",", skiprows=1)
idx = np.searchsorted(ref[:, 0], s[:, 0] - 1e-9)
d1 = s[:, 1] - 273.15 - ref[idx, 1]
d2 = s[:, 3] - 273.15 - ref[idx, 2]
out = {"case": [e, tau, g], "max_abs_T1_diff_K": float(np.abs(d1).max()), "max_abs_T2_diff_K": float(np.abs(d2).max()),
       "T1_peak_two_way_C": float(s[:, 1].max() - 273.15), "T1_peak_lumped_C": float(ref[:, 1].max()),
       "T2_peak_two_way_C": float(s[:, 3].max() - 273.15), "T2_peak_lumped_C": float(ref[:, 2].max()),
       "Tmax_minus_Tmean_max_K": float((s[:, 2] - s[:, 3]).max())}
json.dump(out, open(os.path.join(args.out, "check_two_way.json"), "w"), indent=2)
print(json.dumps(out, indent=1))
