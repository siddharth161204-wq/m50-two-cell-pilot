#!/usr/bin/env python3
"""Measure the current-study bars of Fig. 7 in Koenig, Zhao and Deng, Chem. Eng. J. 507 (2025) 160402 (D1, D2).

Usage: python3 measure_deng_fig7.py <path to the paper PDF>
Extracts the Fig. 7 image from page 12 with pdfimages (poppler), finds the y-axis ticks (0 to 45 % in steps of 5)
and the top outline of each teal bar, and converts pixel rows to percent of the mean.
"""
import sys, subprocess, tempfile, os
import numpy as np
from PIL import Image

pdf = sys.argv[1]
tmp = tempfile.mkdtemp()
subprocess.run(["pdfimages", "-f", "12", "-l", "12", "-j", pdf, os.path.join(tmp, "fig")], check=True)
im = np.asarray(Image.open(os.path.join(tmp, "fig-001.jpg")).convert("RGB")).astype(int)
lum = im.sum(axis=2)
dark = lum < 200
spine = max(range(0, 200), key=lambda x: dark[:, x].sum())
rows = [y for y in range(im.shape[0]) if dark[y, spine - 10:spine - 2].sum() >= 6]
groups = []
for y in rows:
    if groups and y - groups[-1][-1] <= 1:
        groups[-1].append(y)
    else:
        groups.append([y])
ticks = [float(np.mean(g)) for g in groups]          # 45, 40, ..., 0 from top to bottom
y45, y0 = ticks[0], ticks[-1]
px_per_pct = (y0 - y45) / 45.0
r, g, b = im[..., 0], im[..., 1], im[..., 2]
teal = (r < 60) & (g > 100) & (g < 160) & (b > 100) & (b < 160)
bars = {"T_in": (180, 235), "T_on": (610, 685), "T_max": (1085, 1135)}
out = {}
for name, (x0, x1) in bars.items():
    fill_top = int(np.where(teal[:, x0:x1].sum(axis=1) > 0.5 * (x1 - x0))[0].min())
    prof = lum[fill_top - 6:fill_top, x0:x1].mean(axis=1)
    # outline rows: clearly darker than the white background (765); take the luminance-weighted centre
    idx = np.arange(fill_top - 6, fill_top)
    wts = np.clip(765 - prof, 0, None)
    y_edge = float((idx * wts).sum() / wts.sum())
    out[name] = (y0 - y_edge) / px_per_pct
print(f"ticks: 45% at row {y45:.1f}, 0% at row {y0:.1f}, {px_per_pct:.3f} px per %")
for k, v in out.items():
    print(f"{k}: {v:.2f} % of mean (full two-sigma width)")
for k, mean in (("T_in", 183.5), ("T_on", 278.9)):
    w = out[k] / 100 * mean
    print(f"{k}: mean {mean} C, band {mean - w/2:.1f} to {mean + w/2:.1f} C")
