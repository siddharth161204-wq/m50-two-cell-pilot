# Pilot B: a two-cell LG M50 string, resolved against lumped neighbour

A pilot study. Cell 1 is in thermal runaway; cell 2 is its neighbour, joined to it by busbar strips, a 2 mm air gap and radiation between the cans. Cell 2 is modelled twice with identical inputs, once as a single temperature (lumped) and once as a three-dimensional temperature field (resolved), to measure how much the lumped model mistimes and misplaces the onset of self-heating and internal short circuit in the neighbour. Conduction and radiation only: the ejecta and flame paths are excluded. One geometry, published inputs.

## Status

Predictions registered. `predictions.md` was written after the lumped sweep and before any coupled run of the resolved model, and this repository was made public at that point so the order can be checked. The resolved sweep, its verification against the brief's V1 to V3, the figure and the note follow in later commits.

## Contents

- `DECISIONS.md`: every analysis choice not fixed by the brief, with its reason, numbered.
- `predictions.md`: the pre-registered predictions and the hand reasoning behind them.
- `src/lumped_two_cell.py`: the lumped model; every constant both models share lives here. `python3 lumped_two_cell.py --out ../results`
- `src/resolved_cell2.py`, `src/mesh_cell2.py`: the resolved cell 2 (scikit-fem, half cylinder, anisotropic jelly roll, steel can shell, Robin strip contacts, gap-facing air conduction and radiation with the exact local view factor).
- `src/verify_pre.py`: checks run before the predictions (flux identity, conservation, analytic radial and axial conduction).
- `src/verify_post.py`, `src/run_resolved_sweep.py`: V1 to V3 and the resolved sweep, run after the predictions.
- `inputs/`: the band edges measured from Koenig, Zhao and Deng (2025) Fig. 7, the ORegan2022 property calculation, and the Battery Failure Databank rows for the LG 21700-M50 with their extraction script.
- `results/`: lumped results, cell 1 temperature histories (`t1_series/`, the boundary input of the resolved model), verification records.
- `provenance/`: the lumped script as received, before the changes listed in its header.

The study design (referred to as "the brief" in DECISIONS.md) fixed the geometry, the inputs to fetch, the sweep and the verification steps; DECISIONS.md records every choice it did not fix and every place this work departs from it.

## Running

Python 3.11 or newer. `pip install -r requirements.txt`. Then, from `src/`:

    python3 lumped_two_cell.py --out ../results
    python3 verify_pre.py --out ../results
    python3 verify_post.py --out ../results
    python3 run_resolved_sweep.py --out ../results --arrangement two
    python3 run_resolved_sweep.py --out ../results --arrangement one --energy median --tau 30

PARDISO (`pypardiso`) is used for the sparse solves when installed; SuperLU is the fallback and gives the same answers more slowly.

## Sources and credits

- Battery Failure Databank, revision 2 (February 2024), National Renewable Energy Laboratory (now National Laboratory of the Rockies), U.S. Department of Energy; described in D.P. Finegan et al., Journal of Power Sources 597 (2024) 234106. The rows used are in `inputs/databank/` with the Databank's notice, which must accompany every copy.
- B.C. Koenig, P. Zhao, S. Deng, Comprehensive thermal-kinetic uncertainty quantification of lithium-ion battery thermal runaway via Bayesian chemical reaction neural networks, Chemical Engineering Journal 507 (2025) 160402.
- K. O'Regan, F. Brosa Planella, W.D. Widanage, E. Kendrick, Thermal-electrochemical parameters of a high energy lithium-ion cylindrical battery, Electrochimica Acta 425 (2022) 140700, through the PyBaMM "ORegan2022" parameter set.
- View factor of parallel equal cylinders: F.P. Incropera et al., Fundamentals of Heat and Mass Transfer, two-dimensional view factor table.

## Licence

Code: MIT (see LICENSE). The Databank rows remain under the Databank's own notice (`inputs/databank/DATABANK_NOTICE.txt`).
