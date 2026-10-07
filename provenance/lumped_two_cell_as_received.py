#!/usr/bin/env python3
"""
Pilot B, reference model: two LG M50 cells, cell 1 in thermal runaway, cell 2 the neighbour.
Both cells are LUMPED nodes here. This is the baseline that the RESOLVED cell-2 model
(your 3D conduction solver, anisotropic jelly roll + can, busbar entering at the terminal,
gap-facing surface receiving conduction + radiation) must be compared against with
IDENTICAL inputs: same heat release in cell 1, same path conductances, same ambient losses,
same onset criteria. The only difference between the two models is whether cell 2 has
a temperature field or a single temperature.

Every parameter below marked FILL must be taken from the stated source before the runs;
the values given are placeholders of the right order of magnitude, not results.

Paths from cell 1 to cell 2:
  busbar  : strip conductance in series with two weld joints  -> G_bus  [W/K]  (swept)
  gap     : air conduction across the gap between the cans    -> G_gap  [W/K]
  radiation between the facing can surfaces (grey, view factor F)        [computed each step]
Losses from each cell to ambient: convection h*A + radiation eps*sigma*A*(T^4 - Tamb^4).

Heat release in cell 1: a triangular pulse of total energy E_body (the Battery Failure
Databank's "cell body" share of the corrected total energy yield for the LG M50 at the
chosen SOC and trigger) over a release duration tau_rel.

Onset criteria for cell 2 (from Koenig, Zhao and Deng, Chem. Eng. J. 507 (2025) 160402,
Table A.1 and Fig. 7): T_initial (exothermic self-heating, main cluster mean 183.5 C) and
T_onset (internal short circuit, 278.9 C), each with the 2-sigma band from the paper.
FILL the band edges from Fig. 7 before running.

Usage:  python3 lumped_two_cell.py            (runs the sweep and writes lumped_results.csv)
"""
import numpy as np, csv, math

# ---------------- cell (LG INR21700 M50) -- FILL from O'Regan et al. 2022 / PyBaMM "ORegan2022" ----------------
# Derived on 7 Oct 2026 from the ORegan2022 layer parameters in PyBaMM (layer-weighted):
#   jelly roll: density 2939 kg/m3; cp 842 J/kgK at 25 C, 999 at 60 C, 1110 at 100 C;
#   k radial (series) 1.2 to 1.4 W/mK; k axial and azimuthal (parallel) about 25 W/mK;
#   jelly-roll mass about 56 g (P2D volume 1.92e-5 m3) plus a steel can of about 9 g (cp 500 J/kgK).
#   Cell-average cp at 60 to 100 C is therefore about 950 J/kgK on 65 g.
M_CELL   = 0.065      # kg        jelly roll 56 g + can 9 g (datasheet total 68 g)
CP_CELL  = 950.0      # J/(kg K)  cell-average at 60 to 100 C (see note above); CONFIRM against O'Regan 2022 measured values
D_CELL   = 0.0211     # m
L_CELL   = 0.0701     # m
A_CELL   = math.pi * D_CELL * L_CELL + 2 * math.pi * (D_CELL / 2) ** 2   # m^2, total outer area
C_CELL   = M_CELL * CP_CELL   # J/K

# ---------------- ambient ----------------
T_AMB    = 25.0 + 273.15
H_CONV   = 10.0       # W/(m^2 K) natural convection, FILL/justify
EPS      = 0.8        # emissivity of the can wrap (PVC ~0.9; bare steel lower). FILL/justify
SIGMA    = 5.670e-8

# ---------------- gap between cans ----------------
GAP      = 0.002      # m (2 mm) FILL for the module geometry you choose
K_AIR    = 0.03       # W/(m K)
A_FACE   = 0.25 * math.pi * D_CELL * L_CELL     # m^2, effective facing area, FILL/justify (quarter of the lateral area)
G_GAP    = K_AIR * A_FACE / GAP                 # W/K
X        = 1.0 + GAP / D_CELL
F_VIEW   = (math.sqrt(X * X - 1.0) + math.asin(1.0 / X) - X) / math.pi   # infinite parallel equal cylinders

# ---------------- heat release in cell 1 -- FILL from the Battery Failure Databank (Finegan et al. 2024) ----------------
E_BODY_LIST  = [20e3, 35e3, 50e3]   # J, cell-body share of corrected total energy yield for LG M50 tests (min / median / max) FILL
TAU_REL_LIST = [10.0, 30.0]         # s, release duration of the exothermic pulse FILL/justify from FTRC heat-rate traces

# ---------------- busbar path -- swept over the design space ----------------
G_BUS_LIST = [0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5]   # W/K  (nickel strip ~0.01, copper plate ~0.1 to 0.5, wire bond < 0.005)

# ---------------- onset criteria for cell 2 (Koenig, Zhao, Deng 2025) -- FILL the band edges ----------------
T_INITIAL_MEAN = 183.5 + 273.15
T_INITIAL_BAND = (160.0 + 273.15, 210.0 + 273.15)   # FILL from Fig. 7 (2-sigma)
T_ONSET_MEAN   = 278.9 + 273.15
T_ONSET_BAND   = (250.0 + 273.15, 310.0 + 273.15)   # FILL from Fig. 7 (2-sigma)

T_END = 900.0   # s simulated
DT    = 0.01    # s


def q_release(t, e_body, tau):
    """Triangular pulse: rises to its peak at tau/2 and returns to zero at tau; integral = e_body."""
    if t < 0 or t > tau:
        return 0.0
    peak = 2.0 * e_body / tau
    return peak * (t / (tau / 2)) if t <= tau / 2 else peak * ((tau - t) / (tau / 2))


def loss_to_ambient(T):
    return H_CONV * A_CELL * (T - T_AMB) + EPS * SIGMA * A_CELL * (T ** 4 - T_AMB ** 4)


def coupling(T1, T2, g_bus):
    cond = (g_bus + G_GAP) * (T1 - T2)
    rad = EPS * SIGMA * F_VIEW * A_FACE * (T1 ** 4 - T2 ** 4)
    return cond + rad


def run(e_body, tau, g_bus, series=None, every=0.5):
    """If `series` is a list, (t, T1, T2) samples every `every` seconds are appended to it."""
    T1 = T2 = T_AMB
    t = 0.0
    next_sample = 0.0
    cross = {"T_initial_low": None, "T_initial_mean": None, "T_initial_high": None,
             "T_onset_low": None, "T_onset_mean": None, "T_onset_high": None}
    levels = {"T_initial_low": T_INITIAL_BAND[0], "T_initial_mean": T_INITIAL_MEAN, "T_initial_high": T_INITIAL_BAND[1],
              "T_onset_low": T_ONSET_BAND[0], "T_onset_mean": T_ONSET_MEAN, "T_onset_high": T_ONSET_BAND[1]}
    T1max = T2max = T_AMB
    while t < T_END:
        q12 = coupling(T1, T2, g_bus)
        dT1 = (q_release(t, e_body, tau) - loss_to_ambient(T1) - q12) / C_CELL
        dT2 = (q12 - loss_to_ambient(T2)) / C_CELL
        T1 += dT1 * DT
        T2 += dT2 * DT
        t += DT
        T1max = max(T1max, T1); T2max = max(T2max, T2)
        if series is not None and t >= next_sample:
            series.append((round(t, 3), T1 - 273.15, T2 - 273.15))
            next_sample += every
        for k, lv in levels.items():
            if cross[k] is None and T2 >= lv:
                cross[k] = round(t, 2)
    return T1max, T2max, cross


if __name__ == "__main__":
    import os
    os.makedirs("t1_series", exist_ok=True)
    rows = []
    for e in E_BODY_LIST:
        for tau in TAU_REL_LIST:
            for g in G_BUS_LIST:
                ser = []
                T1max, T2max, cross = run(e, tau, g, series=ser)
                # T1(t) is the boundary input for the resolved cell-2 model (one-way coupling, stated in the note)
                with open(os.path.join("t1_series", f"T1_E{int(e)}_tau{int(tau)}_G{g}.csv"), "w", newline="") as fs:
                    ws = csv.writer(fs); ws.writerow(["t_s", "T1_C", "T2_lumped_C"]); ws.writerows(ser)
                rows.append({"E_body_J": e, "tau_rel_s": tau, "G_bus_WK": g, "G_gap_WK": round(G_GAP, 5), "F_view": round(F_VIEW, 3),
                             "T1max_C": round(T1max - 273.15, 1), "T2max_C": round(T2max - 273.15, 1), **cross})
    with open("lumped_results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("wrote lumped_results.csv with", len(rows), "cases; G_gap =", round(G_GAP, 4), "W/K; view factor =", round(F_VIEW, 3))