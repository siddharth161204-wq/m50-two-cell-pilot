# Pilot B: a two-cell LG M50 string, resolved against lumped neighbour

A pilot study. Cell 1 is in thermal runaway; cell 2 is its neighbour, joined to it by busbar strips, a 2 mm air gap and radiation between the cans. Cell 2 is modelled twice with identical inputs, once as a single temperature (lumped) and once as a three-dimensional temperature field (resolved), to measure how much the lumped model mistimes and misplaces the onset of self-heating and internal short circuit in the neighbour. Conduction and radiation only: the ejecta and flame paths are excluded. One geometry, published inputs.

The one-page note is `note/pilot_b_note.pdf` (source `note/pilot_b_note.md`).

## Status and order of work

- Predictions: `predictions.md`, commit `c57ccb87e699d3dbb1230122cdba3785293627e0`, pushed to this public repository at 2026-10-07 06:42:35 UTC (the repository's `pushed_at` time), after the lumped sweep and before any coupled run of the resolved model. The file has not changed since that commit.
- Coupled resolved runs began after the push: V1 at 06:44 UTC, V2 and V3 by 07:11 UTC, the 42-case sweep from 07:15 UTC, the 7 one-strip cases from 09:38 UTC.
- Everything after the predictions commit is in later commits, including the decisions added after the predictions were public (DECISIONS.md D21 to D27) and a later rewording of D1 and D2, which D2 records; no band edge changed.

## Results

Every number below is computed from the result files by `src/note_numbers.py` (`results/note_numbers.json`).

1. With busbars of 500 mW/K in all (two copper plates of 15 mm2 section, D24) and the largest Databank cell-body energy (33.2 kJ), the hottest point of the resolved cell 2 first reaches 183.5 C, the mean T_initial of Koenig, Zhao and Deng, at 5.70 s and 15.51 s (release over 10 and 30 s); the lumped node reaches it at 69.64 s and 79.17 s, 63.9 s and 63.7 s later. The hottest 1 % of the resolved cell reaches it at 11.6 s and 25.0 s. The resolved mean never reaches 183.5 C in any case; in these two cases the lumped node peaks 44 K above the resolved mean (30 K when cell 1 is coupled two-way).
2. The smallest busbar conductance at which only the resolved model reaches 183.5 C is 200 mW/K (100 mW/K for the band's lower edge, 169.0 C). In each of the four cases where only the resolved model reaches 183.5 C, at most 0.52 % of the cell volume (0.33 g) gets above it.
3. At its peak, the hottest point of cell 2 is heated mainly across the gap only at 5 mW/K; from 10 mW/K the strips dominate it (two strips, every energy and duration).

| Prediction | Statement (short form) | Result | Measured |
|---|---|---|---|
| P1 | At 5 mW/K neither model reaches 169.0 C | Held | Peaks of 39.3 to 77.0 C |
| P2 | At 500 mW/K and 33.2 kJ the resolved hottest point reaches 183.5 C more than 50 % earlier than the lumped node | Held | 91.8 % and 80.4 % earlier (central estimate 93 % and 81 %) |
| P3 | Only-resolved crossings of 183.5 C begin at 100 or 200 mW/K; at 500 mW/K and 33.2 kJ the hottest point reaches 255.7 C | Held | From 200 mW/K; 255.7 C reached at 7.13 s and 19.24 s |
| P4 | Hottest point on the gap-facing side at 5 and 10 mW/K, at a terminal end from 100 mW/K | Failed | The switch lies between 5 and 10 mW/K, one step lower |
| P5 | At 500 mW/K the resolved mean rises at least 15 % less than the lumped node | Held | 22.4 to 23.7 % less (central estimate 35 to 55 %, too high) |

Exploratory runs, not pre-registered (DECISIONS.md D23, D25, D26; `results/hot_volume_two.json`, `results/sensitivity_two_way.json`, `results/sensitivity_isotropic.json`):

- Two-way coupling, with cell 1 a lumped state inside the resolved loop, in four cases: cell 1 peaks 4 to 16 K hotter, the hottest point reaches 183.5 C up to 0.26 s earlier (up to 0.44 s earlier at the other levels), and the resolved mean peaks 6 to 14 K higher (181.4 and 182.2 C at 33.2 kJ and 500 mW/K, just under 183.5 C, crossing 169.0 C at 123 and 131 s). The mean-rise reduction of P5 becomes 14.7 to 16.1 % in the three 500 mW/K cases rerun, one of them under the 15 % of P5.
- An isotropic roll (through-layer conductivity raised to 25 W/mK) at 33.2 kJ, 30 s and 500 mW/K lowers the peak of the hottest point from 348.3 C to 247.9 C, below the internal-short band, so the second part of P3 rests on the low through-layer conductivity; it delays the 183.5 C crossing from 15.5 s to 19.3 s, while the mean peaks 14.8 K higher: the strip patches run cooler and so draw more heat from cell 1.
- One strip at the negative end only (series-string arrangement, median energy, 30 s): the hottest point moves to the gap-facing rim of the negative end and first reaches 183.5 C at 25.04 s at 500 mW/K, against 20.07 s with two strips.

## Verification

| Check | Result |
|---|---|
| V0, flux identity: every boundary operator on a uniform field against the lumped formula | Equal to round-off (relative difference at most 5e-16) for every path |
| V1a, conservation with no paths and a uniform internal heat input | Resolved mean equals the lumped node to 3e-13 of the rise |
| Analytic steady radial and axial conduction in the anisotropic roll | Within 0.53 % (radial) and 0.07 % (axial) of the analytic rise |
| V1, radiation heating only (median energy history) | Resolved mean within 0.98 % of the lumped rise; energy residual 2.3e-11 |
| Energy account, all 49 sweep cases | Residual at most 1.2e-11 of the net heat taken in |
| V2, time step halved to 0.05 s, 33.2 kJ, 500 mW/K | Hottest-point crossing times move by at most 0.0033 s (30 s release) and 0.0050 s (10 s release), against unrounded reruns of the base cases (D21) |
| V2, every mesh spacing halved (297,057 nodes), 33.2 kJ, 500 mW/K, 30 s | Hottest-point crossing times move by at most 0.085 s (0.020 s at 183.5 C); peak of the hottest point +1.41 K |
| V2, every mesh spacing halved, 33.2 kJ, 500 mW/K, 10 s | Hottest-point crossing times move by at most 0.020 s (0.0001 s at 183.5 C); peak of the hottest point +1.49 K |
| V2, median case (21.5 kJ, 30 s, 50 mW/K), where neither model crosses a level | Time step halved: peaks change by less than 0.001 K. Mesh refined: hottest point +0.21 K, mean -0.02 K, same location |
| V3, median case | Lumped peak 85.70 C, resolved mean 82.96 C, resolved hottest point 96.72 C |
| Two-way coupling check: roll at 1e4 W/mK, where cell 2 is nearly isothermal | Coupled pair within 0.31 K (cell 1) and 0.17 K (cell 2) of the lumped pair |
| Rerun of the 33.2 kJ, 30 s, 500 mW/K case with the final code (`results/rerun_check.json`) | Identical to the registered row and time series |

Two of the 42 cases were run twice by parallel workers and gave identical rows in every field but the run time; `src/merge_results.py` keeps one copy of each case.

## Contents

- `DECISIONS.md`: every analysis choice not fixed by the brief, with its reason, numbered; D21 to D27 were added after the predictions were public.
- `predictions.md`: the pre-registered predictions and the hand reasoning behind them.
- `src/lumped_two_cell.py`: the lumped model; every constant both models share lives here.
- `src/resolved_cell2.py`, `src/mesh_cell2.py`: the resolved cell 2 (scikit-fem, half cylinder, anisotropic jelly roll, steel can shell, Robin strip contacts, gap-facing air conduction and radiation with the exact local view factor), with the optional two-way coupling of D25.
- `src/verify_pre.py`, `src/verify_post.py`, `src/v2_case.py`, `src/check_two_way.py`, `src/check_rerun.py`: the checks.
- `src/run_resolved_sweep.py`, `src/merge_results.py`: the resolved sweep and the merge of the workers' tables.
- `src/hot_volume.py`, `src/sensitivity.py`: the exploratory runs.
- `src/score_predictions.py`, `src/note_numbers.py`, `src/make_figure.py`, `src/make_workbook.py`: scoring, the numbers quoted in the note, the figure and the results workbook.
- `inputs/`: the band edges measured from Koenig, Zhao and Deng (2025) Fig. 7, the ORegan2022 property calculation, and the Battery Failure Databank rows for the LG 21700-M50 with their extraction script.
- `results/`: `lumped_results.csv`; `resolved_results_two.csv` (42 cases) and `resolved_results_one.csv` (7 cases); `resolved_summary.csv`; `prediction_scorecard.json`; `pilot_b_figure.png` and `.pdf`; `pilot_b_results.xlsx` (all tables in one workbook); the verification and exploratory records; `t1_series/` (cell 1 histories, the boundary input of the resolved model); `resolved_series/` (time series of every resolved run); the run logs.
- `note/`: the note, its Markdown source, stylesheet and render script (pandoc and headless Chromium).
- `provenance/`: the lumped script as received, before the changes listed in its header.

The study design (called the brief in DECISIONS.md) fixed the geometry, the inputs to fetch, the sweep and the verification steps; DECISIONS.md records every choice it did not fix and every place this work departs from it.

## Running

Python 3.11 or newer. `pip install -r requirements.txt`. Then, from `src/`, with `MKL_NUM_THREADS=1` (D22):

    python3 lumped_two_cell.py --out ../results
    python3 verify_pre.py --out ../results
    python3 verify_post.py --out ../results --skip-refined
    python3 verify_post.py --out ../results --only-refined
    python3 run_resolved_sweep.py --out ../results --arrangement two --tag a
    python3 run_resolved_sweep.py --out ../results --arrangement one --energy median --tau 30 --tag d
    python3 merge_results.py --out ../results
    python3 v2_case.py --out ../results --energy max --tau 30 --g 0.5 --refine 2
    python3 v2_case.py --out ../results --energy max --tau 30 --g 0.5 --dt 0.05
    python3 v2_case.py --out ../results --energy max --tau 10 --g 0.5 --refine 2
    python3 v2_case.py --out ../results --energy max --tau 10 --g 0.5 --dt 0.05
    python3 v2_case.py --out ../results --energy max --tau 30 --g 0.5
    python3 v2_case.py --out ../results --energy max --tau 10 --g 0.5
    python3 hot_volume.py --out ../results --cases max:30:0.5 max:10:0.5 median:30:0.5 max:30:0.2 median:30:0.2 max:30:0.1 max:10:0.2 median:10:0.5
    python3 sensitivity.py --out ../results --mode two-way --cases max:30:0.5 max:10:0.5 median:30:0.5 max:30:0.2
    python3 sensitivity.py --out ../results --mode isotropic --cases max:30:0.5
    python3 check_two_way.py --out ../results
    python3 run_resolved_sweep.py --out <rerun dir> --arrangement two --energy max --tau 30 --g 0.5 --tag r
    python3 check_rerun.py --out ../results --rerun <rerun dir>
    python3 score_predictions.py --out ../results
    python3 note_numbers.py --out ../results
    python3 make_figure.py --out ../results
    python3 make_workbook.py --out ../results
    cd ../note && ./render_note.sh

Several sweep workers can run at once with different `--tag` values; each skips the cases already in any worker's table. A base-mesh case takes about 4 to 5 minutes on one core, a refined-mesh case about 85 minutes. PARDISO (`pypardiso`) is used for the sparse solves when installed; SuperLU is the fallback and gives the same answers more slowly. `pybamm` is needed only for `inputs/oregan2022_properties.py`.

## Sources and credits

- Battery Failure Databank, revision 2 (February 2024), National Renewable Energy Laboratory (now National Laboratory of the Rockies), U.S. Department of Energy; described in D.P. Finegan et al., Journal of Power Sources 597 (2024) 234106. The rows used are in `inputs/databank/` with the Databank's notice, which must accompany every copy.
- B.C. Koenig, P. Zhao, S. Deng, Comprehensive thermal-kinetic uncertainty quantification of lithium-ion battery thermal runaway via Bayesian chemical reaction neural networks, Chemical Engineering Journal 507 (2025) 160402.
- K. O'Regan, F. Brosa Planella, W.D. Widanage, E. Kendrick, Thermal-electrochemical parameters of a high energy lithium-ion cylindrical battery, Electrochimica Acta 425 (2022) 140700, through the PyBaMM parameter set ORegan2022.
- View factor of parallel equal cylinders: F.P. Incropera et al., Fundamentals of Heat and Mass Transfer, two-dimensional view factor table.

## Licence

Code: MIT (see LICENSE). The Databank rows remain under the Databank's own notice (`inputs/databank/DATABANK_NOTICE.txt`).
