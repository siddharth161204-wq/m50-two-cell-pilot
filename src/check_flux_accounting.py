#!/usr/bin/env python3
"""Addendum v1.1, check of the flux accounting option (DECISIONS.md D28) on a synthetic input, before any archived
case is rerun: cell 1 held at 150 C from t = 0, two strips of 0.25 W/K each, 5 s.

1. The option changes nothing: the temperature field and the time series are bitwise identical with and without it.
2. The per-step record closes: stored energy = strips + gap + radiation from cell 1 - room convection - room radiation
   at every step, to round-off of the gross flow.
3. Its last row equals the run's own end-of-run account.

Usage: python3 check_flux_accounting.py --out ../results     -> results/addendum_flux_accounting_check.json
"""
import argparse, json, os
import numpy as np

from resolved_cell2 import Cell2Model

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="../results")
args = ap.parse_args()

model = Cell2Model(1.0)
t1f = lambda t: 273.15 + 150.0
kw = dict(t_end=5.0, dt=0.1, g_pos=0.25, g_neg=0.25)
a = model.run(t1f, **kw)
b = model.run(t1f, energy_series=True, **kw)
es = b["energy_series"]
cols = list(b["energy_series_columns"])
c = {k: es[:, i] for i, k in enumerate(cols)}
net = c["in_bus_J"] + c["in_gap_J"] + c["in_rad_J"] + c["in_vol_J"] - c["out_conv_J"] - c["out_rad_J"]
gross = c["in_bus_J"] + c["in_gap_J"] + c["in_rad_J"] + c["in_vol_J"] + c["out_conv_J"] + c["out_rad_J"]
resid = c["stored_J"] - net
keys = ("in_bus", "in_gap", "in_rad", "out_conv", "out_rad", "in_vol")
out = {
    "input": "synthetic: T1 = 150 C from t = 0, g_pos = g_neg = 0.25 W/K, 5 s at 0.1 s, refine 1",
    "field_identical_with_and_without_option": bool(np.array_equal(a["T_final"], b["T_final"])),
    "series_identical_with_and_without_option": bool(np.array_equal(a["series"], b["series"])),
    "rows_recorded": int(es.shape[0]),
    "columns": cols,
    "max_abs_residual_J": float(np.abs(resid).max()),
    "max_abs_residual_over_gross_flow": float(np.abs(resid[1:]).max() / gross[-1]),
    "last_row_equals_end_of_run_account": bool(all(es[-1, 1 + i] == b["energy"][k] for i, k in enumerate(keys))
                                               and es[-1, -1] == b["stored_J"]),
}
json.dump(out, open(os.path.join(args.out, "addendum_flux_accounting_check.json"), "w"), indent=2)
print(json.dumps(out, indent=2))
