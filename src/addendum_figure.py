#!/usr/bin/env python3
"""The addendum figure (v1.1), in the style of the note's figure.

a  Busbar share of the resolved neighbour's heat intake against busbar conductance: over 900 s (33.2 kJ, 30 s, with
   the range over all six two-strip cases at each conductance), up to the hottest node's first 183.5 C crossing
   (headline reruns, where it crosses), and the one-strip runs.
b  Yao and Battiato's error measure against the resolved mean, |T_mean - T_lumped| / 240 K, against time, 33.2 kJ,
   500, 200, 100 and 50 mW/K, both release durations, with their test cases' 0.05.
c  The same against the resolved hottest node.
Usage: python3 addendum_figure.py --out ../results
"""
import argparse, csv, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import NullLocator

import lumped_two_cell as LP

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="../results")
args = ap.parse_args()

INK, INK2, MUTED, GRID, AXIS, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#ffffff"
ORANGE, AQUA = "#eb6834", "#1baf7a"
RAMP = {0.05: "#86b6ef", 0.1: "#3987e5", 0.2: "#1c5cab", 0.5: "#0d366b"}   # reference sequential blue, steps 250 to 700
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.5, "axes.edgecolor": AXIS, "axes.labelcolor": INK2,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.linewidth": 0.8, "xtick.major.width": 0.8,
                     "ytick.major.width": 0.8, "figure.facecolor": SURF, "axes.facecolor": SURF,
                     "xtick.labelsize": 6.6, "ytick.labelsize": 6.6})
G = LP.G_BUS_LIST
GL = ["5", "10", "20", "50", "100", "200", "500"]
EH = int(round(max(LP.E_BODY_LIST)))
intake = list(csv.DictReader(open(os.path.join(args.out, "addendum_intake.csv"))))
reg = {r["case"]: r for r in csv.DictReader(open(os.path.join(args.out, "resolved_results_two.csv")))}
es = np.load(os.path.join(args.out, "addendum_error_series.npz"))


def v(x):
    return None if x in ("", None) else float(x)


def clean(ax):
    ax.grid(True, which="major", color=GRID, lw=0.7); ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)


fig, axs = plt.subplots(1, 3, figsize=(7.4, 2.45), gridspec_kw={"wspace": 0.42})

# a: busbar share
ax = axs[0]
two = [r for r in intake if r["arrangement"] == "two"]
lo = [100 * min(v(r["busbar_share_900s"]) for r in two if float(r["G_bus_WK"]) == g) for g in G]
hi = [100 * max(v(r["busbar_share_900s"]) for r in two if float(r["G_bus_WK"]) == g) for g in G]
ax.fill_between(G, lo, hi, color=AQUA, alpha=0.18, lw=0, zorder=1)
head = {float(r["G_bus_WK"]): r for r in two if r["case"].startswith(f"two_E{EH}_tau30_")}
y = [100 * v(head[g]["busbar_share_900s"]) for g in G]
ax.plot(G, y, color=AQUA, lw=1.6, zorder=2)
ax.scatter(G, y, marker="s", s=22, facecolor=AQUA, edgecolor=AQUA, zorder=3)
one = sorted((float(r["G_bus_WK"]), 100 * v(r["busbar_share_900s"])) for r in intake if r["arrangement"] == "one")
ax.plot([a for a, _ in one], [b for _, b in one], color=INK2, ls="--", lw=1.2, zorder=2)
ax.scatter([a for a, _ in one], [b for _, b in one], marker="o", s=18, facecolor=SURF, edgecolor=INK2, lw=1.1, zorder=3)
for tau, fill, dx in (("30", True, 1.09), ("10", False, 0.92)):       # side by side: the two durations nearly coincide
    pts = [(float(r["G_bus_WK"]) * dx, 100 * v(r["busbar_share_to_crossing"])) for r in two
           if r["case"].startswith(f"two_E{EH}_tau{tau}_") and v(r.get("busbar_share_to_crossing")) is not None]
    if pts:
        ax.scatter([a for a, _ in pts], [b for _, b in pts], marker="^", s=30, facecolor=ORANGE if fill else SURF,
                   edgecolor=ORANGE, lw=1.2, zorder=4)
ax.axhline(50, color=MUTED, lw=0.8, ls=":", zorder=1)
ax.set_xscale("log"); ax.set_xlim(0.0036, 0.68)
ax.set_xticks(G); ax.set_xticklabels(GL); ax.xaxis.set_minor_locator(NullLocator())
ax.set_ylim(0, 100); ax.set_yticks([0, 20, 40, 60, 80, 100])
ax.set_xlabel("Busbar conductance (mW/K)"); ax.set_ylabel("Busbar share of the intake (%)")
clean(ax)
ax.set_title("a  How the heat arrives", loc="left", fontsize=8, color=INK, fontweight="bold")

# b, c: error measure against time
for ax, key, title in ((axs[1], "e_mean", "b  Lumped error, mean"),
                       (axs[2], "e_hot", "c  Lumped error, hottest node")):
    for g in (0.05, 0.1, 0.2, 0.5):
        for tau, ls in (("30", "-"), ("10", "--")):
            c = f"two_E{EH}_tau{tau}_G{g}"
            t, e = es[f"{c}__t"], es[f"{c}__{key}"]
            m = t > 0
            ax.plot(t[m], e[m], color=RAMP[g], ls=ls, lw=1.4, zorder=2)
            tc = v(reg[c]["T_initial_mean_resolved_max_s"])
            if tc is not None and key == "e_hot":
                ax.scatter([tc], [np.interp(tc, t, e)], marker="^", s=26, facecolor=ORANGE if tau == "30" else SURF,
                           edgecolor=ORANGE, lw=1.1, zorder=4)
            if tc is not None and key == "e_mean":
                ax.scatter([tc], [0.0], marker="^", s=26, facecolor=ORANGE if tau == "30" else SURF,
                           edgecolor=ORANGE, lw=1.1, zorder=4, clip_on=False)
    top = 0.27 if key == "e_mean" else 1.35
    ax.axhline(0.05, color=INK, lw=0.9, ls=":", zorder=3)
    ax.text(0.6, 0.05 + 0.012 * top, "0.05", fontsize=6.3, color=INK, va="bottom")
    ax.set_xscale("log"); ax.set_xlim(0.5, 900)
    ax.set_xticks([1, 10, 100, 900]); ax.set_xticklabels(["1", "10", "100", "900"]); ax.xaxis.set_minor_locator(NullLocator())
    ax.set_ylim(0, top)
    ax.set_yticks([0, 0.05, 0.1, 0.15, 0.2, 0.25] if key == "e_mean" else [0, 0.25, 0.5, 0.75, 1.0, 1.25])
    ax.set_xlabel("Time (s)"); ax.set_ylabel("|T - T_lumped| / 240 K")
    clean(ax)
    ax.set_title(title, loc="left", fontsize=8, color=INK, fontweight="bold")

legend = [Line2D([], [], color=AQUA, marker="s", lw=1.6, markersize=4.5, label="a: over 900 s, 33.2 kJ, 30 s"),
          Patch(facecolor=AQUA, alpha=0.18, label="a: range over the six two-strip cases"),
          Line2D([], [], color=INK2, ls="--", marker="o", markerfacecolor=SURF, lw=1.2, markersize=4, label="a: one strip, 21.5 kJ, 30 s"),
          Line2D([], [], color=ORANGE, marker="^", ls="none", markersize=5.5,
                 label="Hottest node first at 183.5 C (a: share to then)"),
          Line2D([], [], color=RAMP[0.05], lw=1.6, label="50 mW/K"), Line2D([], [], color=RAMP[0.1], lw=1.6, label="100 mW/K"),
          Line2D([], [], color=RAMP[0.2], lw=1.6, label="200 mW/K"), Line2D([], [], color=RAMP[0.5], lw=1.6, label="500 mW/K"),
          Line2D([], [], color=INK2, lw=1.3, label="b, c: 30 s release (filled)"),
          Line2D([], [], color=INK2, lw=1.3, ls="--", label="b, c: 10 s release (hollow)"),
          Line2D([], [], color=INK, lw=0.9, ls=":", label="b, c: 0.05, the test-case error of Yao and Battiato"),
          Line2D([], [], color=MUTED, lw=0.8, ls=":", label="a: half the intake")]
fig.legend(handles=legend, loc="lower center", ncol=3, fontsize=6.4, frameon=False, bbox_to_anchor=(0.5, -0.33),
           columnspacing=1.4, handlelength=2.0)
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(args.out, f"addendum_figure.{ext}"), dpi=240, bbox_inches="tight",
                metadata={"CreationDate": None} if ext == "pdf" else None)
print("wrote", os.path.join(args.out, "addendum_figure.png"))
