#!/usr/bin/env python3
"""Pilot B figure (brief step 5, with a context panel added).

a  Peak temperature of cell 2 against busbar conductance: lumped node, resolved mean and resolved hottest point,
   median and maximum Databank energy, with the two onset bands of Koenig, Zhao and Deng (2025).
b  First time cell 2 reaches T_initial = 183.5 C against busbar conductance (the brief's left panel), lumped node
   against resolved hottest point; cases where only the resolved model crosses are ringed.
c  Resolved hottest point minus resolved mean, at the moment the hottest point peaks (hollow) and at the moment it
   reaches 183.5 C (filled), median energy; marker shape gives the path that heats it (the brief's right panel).
All at tau_rel = 30 s, two-strip arrangement.
Usage: python3 make_figure.py --out ../results
"""
import argparse, csv, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import NullLocator

import lumped_two_cell as LP

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="../results")
ap.add_argument("--tau", type=float, default=30.0)
args = ap.parse_args()

INK, INK2, MUTED, GRID, AXIS, SURF, BAND = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#ffffff", "#f0efec"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.5, "axes.edgecolor": AXIS, "axes.labelcolor": INK2,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.linewidth": 0.8, "xtick.major.width": 0.8,
                     "ytick.major.width": 0.8, "figure.facecolor": SURF, "axes.facecolor": SURF,
                     "xtick.labelsize": 6.6, "ytick.labelsize": 6.6})
rows = list(csv.DictReader(open(os.path.join(args.out, "resolved_results_two.csv"))))
E = sorted(LP.E_BODY_LIST)
G = LP.G_BUS_LIST
GL = ["5", "10", "20", "50", "100", "200", "500"]


def get(e, g, tau=args.tau):
    for r in rows:
        if abs(float(r["E_body_J"]) - round(e, 1)) < 0.5 and float(r["tau_rel_s"]) == tau and float(r["G_bus_WK"]) == g:
            return r
    raise KeyError((e, g, tau))


def val(x):
    return None if x in ("", None) else float(x)


def series(r):
    return np.load(os.path.join(args.out, "resolved_series", r["case"] + ".npz"))


def style_axes(ax):
    ax.set_xscale("log"); ax.set_xlim(0.0036, 0.68)
    ax.set_xticks(G); ax.set_xticklabels(GL); ax.xaxis.set_minor_locator(NullLocator())
    ax.grid(True, which="major", color=GRID, lw=0.7); ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.set_xlabel("Busbar conductance (mW/K)")


fig, axs = plt.subplots(1, 3, figsize=(7.4, 2.45), gridspec_kw={"wspace": 0.42})
energies = ((E[1], "-", True), (E[2], "--", False))

# a: peak temperatures with onset bands
ax = axs[0]
lo, hi = LP.T_INITIAL_BAND[0] - 273.15, LP.T_INITIAL_BAND[1] - 273.15
ax.axhspan(lo, hi, color=BAND, lw=0, zorder=0)
ax.axhspan(LP.T_ONSET_BAND[0] - 273.15, LP.T_ONSET_BAND[1] - 273.15, color=BAND, lw=0, zorder=0)
ax.text(0.0039, 0.5 * (lo + hi), "T_in band", fontsize=6.3, color=INK2, va="center")
ax.text(0.0039, 0.5 * (LP.T_ONSET_BAND[0] + LP.T_ONSET_BAND[1]) - 273.15, "T_on band", fontsize=6.3, color=INK2, va="center")
for e, ls, fill in energies:
    for key, col, mk in (("T2max_lumped_C", BLUE, "o"), ("Tmean_resolved_peak_C", AQUA, "s"), ("Tmax_resolved_peak_C", ORANGE, "^")):
        y = [val(get(e, g)[key]) for g in G]
        ax.plot(G, y, ls=ls, color=col, lw=1.6, zorder=2)
        ax.scatter(G, y, marker=mk, s=22, facecolor=col if fill else SURF, edgecolor=col, linewidth=1.2, zorder=3)
style_axes(ax)
ax.set_ylim(20, 380)
ax.set_ylabel("Peak temperature of cell 2 (C)")
ax.set_title("a  How hot the neighbour gets", loc="left", fontsize=8, color=INK, fontweight="bold")

# b: time to 183.5 C
ax = axs[1]
ax.axvspan(0.0036, 0.14, color=BAND, lw=0, zorder=0)
ax.text(0.0042, 330, "neither model reaches\n183.5 C within 900 s\nbelow 200 mW/K", fontsize=6.3, color=INK2, va="top")
for e, ls, fill in energies:
    for key, col, mk in (("T_initial_mean_lumped_s", BLUE, "o"), ("T_initial_mean_resolved_max_s", ORANGE, "^")):
        pts = [(g, val(get(e, g)[key])) for g in G if val(get(e, g)[key]) is not None]
        if not pts:
            continue
        xs, ys = zip(*pts)
        if len(xs) > 1:
            ax.plot(xs, ys, ls=ls, color=col, lw=1.6, zorder=2)
        ax.scatter(xs, ys, marker=mk, s=26, facecolor=col if fill else SURF, edgecolor=col, linewidth=1.2, zorder=3)
        if key.endswith("resolved_max_s"):
            for g, y in pts:
                if val(get(e, g)["T_initial_mean_lumped_s"]) is None:
                    ax.scatter([g], [y], marker="o", s=120, facecolor="none", edgecolor=INK2, linewidth=0.8, zorder=4)
r_hl = get(E[2], 0.5)
ax.annotate(f"{float(r_hl['T_initial_mean_resolved_max_s']):.1f} s", (0.5, float(r_hl["T_initial_mean_resolved_max_s"])),
            xytext=(0, -11), textcoords="offset points", fontsize=6.6, color=INK, ha="center", va="center")
ax.annotate(f"{float(r_hl['T_initial_mean_lumped_s']):.1f} s", (0.5, float(r_hl["T_initial_mean_lumped_s"])),
            xytext=(-8, 0), textcoords="offset points", fontsize=6.6, color=INK, ha="right", va="center")
style_axes(ax)
ax.set_yscale("log"); ax.set_ylim(3, 400)
ax.set_yticks([3, 10, 30, 100, 300]); ax.set_yticklabels(["3", "10", "30", "100", "300"]); ax.yaxis.set_minor_locator(NullLocator())
ax.set_ylabel("Time to first reach 183.5 C (s)")
ax.set_title("b  When it first reaches 183.5 C", loc="left", fontsize=8, color=INK, fontweight="bold")

# c: hottest point minus mean, location
ax = axs[2]
e = E[1]
shape = {"terminal end": "^", "gap-facing surface": "o", "elsewhere": "s"}
for g in G:
    r = get(e, g)
    s = series(r)
    i = int(np.argmax(s["Tmax"]))
    ax.scatter([g], [s["Tmax"][i] - s["Tmean"][i]], marker=shape.get(r["location_at_peak"], "s"), s=30, facecolor=SURF,
               edgecolor=ORANGE, linewidth=1.3, zorder=3)
    dc = val(r["T_initial_mean_Tmax_minus_Tmean_K"])
    if dc is not None:
        ax.scatter([g], [dc], marker=shape.get(r["T_initial_mean_location"], "s"), s=30, facecolor=ORANGE, edgecolor=ORANGE, zorder=4)
style_axes(ax)
ax.set_yscale("log"); ax.set_ylim(0.8, 400)
ax.set_yticks([1, 3, 10, 30, 100, 300]); ax.set_yticklabels(["1", "3", "10", "30", "100", "300"]); ax.yaxis.set_minor_locator(NullLocator())
ax.set_ylabel("Hottest point minus mean (K)")
ax.set_title("c  Where the hottest point is", loc="left", fontsize=8, color=INK, fontweight="bold")

legend = [Line2D([], [], color=BLUE, marker="o", lw=1.6, markersize=4.5, label="Lumped node"),
          Line2D([], [], color=AQUA, marker="s", lw=1.6, markersize=4.5, label="Resolved mean"),
          Line2D([], [], color=ORANGE, marker="^", lw=1.6, markersize=5, label="Resolved hottest point"),
          Line2D([], [], color=INK2, ls="-", lw=1.3, label=f"{E[1] / 1e3:.1f} kJ, median (filled)"),
          Line2D([], [], color=INK2, ls="--", lw=1.3, label=f"{E[2] / 1e3:.1f} kJ, maximum (hollow)"),
          Line2D([], [], color=INK2, marker="o", ls="none", markerfacecolor="none", markersize=8.5, label="Only the resolved model crosses"),
          Line2D([], [], color=ORANGE, marker="o", ls="none", markerfacecolor=SURF, markersize=5, label="c: heated across the gap"),
          Line2D([], [], color=ORANGE, marker="^", ls="none", markerfacecolor=SURF, markersize=5.5, label="c: heated by the strip"),
          Line2D([], [], color=ORANGE, marker="^", ls="none", markersize=5.5, label="c: filled, at 183.5 C; hollow, at peak")]
fig.legend(handles=legend, loc="lower center", ncol=3, fontsize=6.6, frameon=False, bbox_to_anchor=(0.5, -0.25),
           columnspacing=1.6, handlelength=2.0)
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(args.out, f"pilot_b_figure.{ext}"), dpi=240, bbox_inches="tight")
print("wrote", os.path.join(args.out, "pilot_b_figure.png"))
