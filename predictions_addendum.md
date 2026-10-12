# Predictions for the addendum (v1.1)

Written and committed before any number of the addendum is computed. The addendum adds four computations to the published two-cell study (v1.0.0, doi.org/10.5281/zenodo.23253738), from its archived results and the dimensionless definitions of Y.N. Yao and I. Battiato, Non-intrusive auto-detecting and adaptive hybrid scheme for multiscale heat transfer: thermal runaway in a battery pack, arXiv:2504.10119v1 (14 April 2025). Equation, table and section numbers below are those of that version. Their fine-scale pack couples cells only through the packing material, treats each cell as an isotropic disk with the packing's conductivity (3 W/mK), uses an error-function heat source and has no busbar and no radiation; this study's archived results say how much of the neighbour's heat arrives by the busbar, and how large the lumped neighbour's error is in their own measure. Nothing in v1.0.0 is changed: the addendum adds files and sections.

What the archive holds, read before this file was written: for every one of the 49 resolved runs, the run's energy account over 0 to 900 s (heat in through the strips, the air gap and radiation from cell 1; heat out to the room; heat stored), time series every 0.5 s of the resolved hottest node and mean, and the lumped cell 2 every 0.1 s. It holds no time series of the heat through each path, so the eight headline cases are rerun with flux accounting for the window up to the hottest node's first 183.5 C crossing (DECISIONS.md D28).

## The predictions

As set in the study design, with "her" replaced by the authors' names:

- P1. At 500 mW/K the busbar carries more than 80 % of the neighbour's intake over 900 s (central 90 %); at 50 mW/K less than 50 % (central 40 %).
- P2. At 33.2 kJ and 500 mW/K the lumped neighbour's error in Yao and Battiato's measure, against the resolved mean, exceeds 0.05 (central peak 0.08) and first exceeds it before the hottest node reaches 183.5 C.
- P3. At 100 mW/K the error against the resolved mean never exceeds 0.05 (central peak 0.03), while against the hottest node it does.
- P4. For the module in air, Yao and Battiato's packing Biot number is above 10 (central 40), so the first condition violated is the packing one, before any cell burns.

## The quantities (definitions in DECISIONS.md D28 to D32)

1. Intake split (D29): the heat cell 2 takes in through the busbar strips, through the air gap and by radiation from cell 1, as the resolved model's energy account books them, over 0 to 900 s and up to the hottest node's first 183.5 C crossing where it occurs; busbar share = strips / (strips + gap + radiation).
2. Error measure (D30): e_mean(t) = |T_mean(t) - T_lumped(t)| / 240 K and e_hot(t) = |T_max(t) - T_lumped(t)| / 240 K, with 240 K the temperature scale of their Table 3 and Eq. 6, against their test cases' 0.05.
3. Module numbers (D31): Eq. 9 for a two-by-four module of M50 cells at 23.1 mm pitch in air, each compared with Eq. 13, and the busbar conductance in their units.
4. Internal Biot number of the neighbour with a strip as the heat source (D32).

## How each prediction is scored, fixed now

- P1. The two-strip arrangement, the registered one: all six cases at 500 mW/K and all six at 50 mW/K (three energies, two release durations), shares from the archived energy accounts over 0 to 900 s. Held if every 500 mW/K case is above 80 % and every 50 mW/K case is below 50 %; otherwise failed, naming the cases that miss. The seven one-strip runs are reported and not scored.
- P2. The two cases at 33.2 kJ and 500 mW/K (two strips, 10 and 30 s). Held if in both the largest e_mean over 0 to 900 s exceeds 0.05 and e_mean first exceeds 0.05 before the hottest node first reaches 183.5 C (archived: 5.70 s and 15.51 s); otherwise failed. The peak is reported against the central 0.08.
- P3. The two cases at 33.2 kJ and 100 mW/K (two strips, 10 and 30 s), the energy of P2 and of the headline cases. Held if in both the largest e_mean over 0 to 900 s is at most 0.05 and the largest e_hot exceeds 0.05; otherwise failed. The peak e_mean is reported against the central 0.03. The 100 mW/K cases at the other two energies are reported and not scored.
- P4. (a) The packing Biot number Bi_p of D31 is above 10. (b) With no cell burning, the packing condition, Bi_p of order 1, is violated, and it is the only condition of Eq. 13 that is. The burn number R is set aside for (b), because its source acts only in a burning cell; varrho is not evaluated (D31) and Q has no counterpart in the module. A condition that a number DN be of order epsilon^k counts as violated when the integer nearest to ln(DN) / ln(epsilon) differs from k, since Eq. 13 states the conditions in integer powers of epsilon; the factor reported is DN / epsilon^k. Held if (a) and (b) hold. Held in part if (a) holds and Bi_p of order 1 is violated with no cell burning, but another condition is violated too; the scorecard names it. Failed if (a) fails or the packing condition is not violated.

First-exceedance and crossing times are interpolated linearly between samples, as in v1.0.0 (D14, D30).
