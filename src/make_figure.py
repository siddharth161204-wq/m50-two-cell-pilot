#!/usr/bin/env python3
"""Pilot B figure (brief step 5).

Left: first time cell 2 reaches T_initial = 183.5 C against busbar conductance, lumped node against resolved
hottest point, median and maximum Databank energy, tau_rel = 30 s; cases with no crossing in 900 s sit on the
top strip, and cases where only the resolved model crosses are ringed.
Right: resolved hottest point minus resolved mean, at the moment the hottest point reaches 183.5 C (filled) or at
its peak where it never does (hollow), median energy, tau_rel = 30 s; marker shape gives the path heating it.
Usage: python3 make_figure.py --out ../results
"""
import argparse, csv, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import lumped_two_cell as LP

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="../results")
ap.add_argument("--tau", type=float, default=30.0)
args = ap.parse_args()

INK, INK2, MUTED, GRID, AXIS, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#ffffff"
BLUE, ORANGE = "#2a78d6", "#eb6834"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "axes.edgecolor": AXIS, "axes.labelcolor": INK2,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.linewidth": 0.8, "xtick.major.width": 0.8,
                     "ytick.major.width": 0.8, "figure.facecolor": SURF, "axes.facecolor": SURF})

rows = list(csv.DictReader(open(os.path.join(args.out, "resolved_results_two.csv"))))
E = sorted(LP.E_BODY_LIST)
G = LP.G_BUS_LIST


def get(e, tau, g):
    for r in rows:
        if abs(float(r["E_body_J"]) - round(e, 1)) < 0.5 and float(r["tau_rel_s"]) == tau and float(r["G_bus_WK"]) == g:
            return r
    raise KeyError((e, tau, g))


def val(x):
    return None if x in ("", None) else float(x)


fig, (axl, axr) = plt.subplots(1, 2, figsize=(7.4, 3.3), gridspec_kw={"width_ratios": [1.15, 1.0], "wspace": 0.34})
NEVER = 2000.0
for e, ls, fill, name in ((E[1], "-", True, "median"), (E[2], "--", False, "maximum")):
    for model, col, key, mk in (("lumped node", BLUE, "T_initial_mean_lumped_s", "o"),
                                ("resolved hottest point", ORANGE, "T_initial_mean_resolved_max_s", "^")):
        ys = [val(get(e, args.tau, g)[key]) for g in G]
        yplot = [y if y is not None else NEVER for y in ys]
        xs = np.array(G)
        ok = np.array([y is not None for y in ys])
        if ok.sum() > 1:
            axl.plot(xs[ok], np.array(yplot)[ok], ls=ls, color=col, lw=2, solid_capstyle="round", zorder=2)
        axl.scatter(xs, yplot, marker=mk, s=42, facecolor=col if fill else SURF, edgecolor=col, linewidth=1.6, zorder=3)
        if key.endswith("resolved_max_s"):
            for g, y in zip(G, ys):
                ly = val(get(e, args.tau, g)["T_initial_mean_lumped_s"])
                if y is not None and ly is None:
                    axl.scatter([g], [y], marker="o", s=170, facecolor="none", edgecolor=INK2, linewidth=0.9, zorder=4)
axl.set_xscale("log"); axl.set_yscale("log")
axl.set_xlim(0.0035, 0.7); axl.set_ylim(2, 3500)
axl.axhspan(1100, 3500, color="#f0efec", zorder=0, lw=0)
axl.text(0.0042, 1500, "no crossing within 900 s", color=INK2, fontsize=7.5, va="center")
axl.set_yticks([3, 10, 30, 100, 300, 900]); axl.set_yticklabels(["3", "10", "30", "100", "300", "900"])
axl.set_xticks(G); axl.set_xticklabels(["0.005", "0.01", "0.02", "0.05", "0.1", "0.2", "0.5"], rotation=0)
axl.minorticks_off()
axl.grid(True, which="major", color=GRID, lw=0.8); axl.set_axisbelow(True)
axl.set_xlabel("Busbar conductance G_bus (W/K)")
axl.set_ylabel("Time cell 2 reaches 183.5 C (s)")
for sp in ("top", "right"):
    axl.spines[sp].set_visible(False)
leg = [Line2D([], [], color=BLUE, marker="o", lw=2, label="Lumped node"),
       Line2D([], [], color=ORANGE, marker="^", lw=2, label="Resolved hottest point"),
       Line2D([], [], color=INK2, ls="-", lw=1.4, label=f"{E[1]/1e3:.1f} kJ (median)"),
       Line2D([], [], color=INK2, ls="--", lw=1.4, label=f"{E[2]/1e3:.1f} kJ (maximum)"),
       Line2D([], [], color=INK2, marker="o", ls="none", markerfacecolor="none", markersize=11, label="Only resolved crosses")]
axl.legend(handles=leg, loc="lower left", fontsize=7, frameon=False, ncol=1, handlelength=2.2, borderaxespad=0.2)
axl.set_title("a  Onset of self-heating in the neighbour", loc="left", fontsize=9, color=INK, fontweight="bold")

# right panel
e = E[1]
mk_of = {"terminal end": "^", "gap-facing surface": "o", "elsewhere": "s"}
for g in G:
    r = get(e, args.tau, g)
    dt_c = val(r["T_initial_mean_Tmax_minus_Tmean_K"])
    if dt_c is not None:
        y, lab, fill = dt_c, r["T_initial_mean_location"], True
    else:
        y = val(r["Tmax_resolved_peak_C"]) - val(r["Tmean_resolved_peak_C"])
        lab, fill = r["location_at_peak"], False
    axr.scatter([g], [y], marker=mk_of.get(lab, "s"), s=48, facecolor=ORANGE if fill else SURF, edgecolor=ORANGE, linewidth=1.6, zorder=3)
axr.set_xscale("log"); axr.set_xlim(0.0035, 0.7)
axr.set_xticks(G); axr.set_xticklabels(["0.005", "0.01", "0.02", "0.05", "0.1", "0.2", "0.5"])
axr.minorticks_off()
axr.grid(True, which="major", color=GRID, lw=0.8); axr.set_axisbelow(True)
axr.set_ylim(bottom=0)
axr.set_xlabel("Busbar conductance G_bus (W/K)")
axr.set_ylabel("Hottest point minus mean (K)")
for sp in ("top", "right"):
    axr.spines[sp].set_visible(False)
leg = [Line2D([], [], color=ORANGE, marker="^", ls="none", markersize=7, label="Heated by the strip (terminal end)"),
       Line2D([], [], color=ORANGE, marker="o", ls="none", markersize=7, label="Heated across the gap (gap-facing)"),
       Line2D([], [], color=ORANGE, marker="o", ls="none", markersize=7, markerfacecolor=SURF, label="At peak (never reaches 183.5 C)")]
axr.legend(handles=leg, loc="upper left", fontsize=7, frameon=False, borderaxespad=0.2)
axr.set_title("b  Where the hottest point is", loc="left", fontsize=9, color=INK, fontweight="bold")
fig.text(0.01, -0.02, f"Two LG M50 cells, cell 1 releasing the Databank cell-body energy over tau_rel = {args.tau:.0f} s; conduction and radiation only.",
         fontsize=7, color=MUTED)
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(args.out, f"pilot_b_figure_tau{int(args.tau)}.{ext}"), dpi=220, bbox_inches="tight")
print("wrote", os.path.join(args.out, f"pilot_b_figure_tau{int(args.tau)}.png"))
