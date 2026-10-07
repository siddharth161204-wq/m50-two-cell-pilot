# Pilot B predictions

Written on 7 October 2026 after the lumped sweep (`results/lumped_results.csv`) and before any coupled run of the resolved cell-2 model. The resolved model had been run only on the checks in `results/verification_pre_refine1.json` and on code-path tests of at most 3 s of simulated time, all with synthetic inputs that carry no information about the 42 cases. This file is committed and pushed to a public repository before the resolved sweep; the commit hash is recorded in the README.

## Definitions used for scoring

Self-heating band: T_initial = 183.5 C with two-sigma edges 169.0 and 198.0 C. Internal-short band: T_onset = 278.9 C with edges 255.7 and 302.1 C (DECISIONS.md D1, D2). Lumped node: the script's cell-2 temperature (`lumped_results.csv`). Resolved local maximum: the hottest node of the resolved cell 2, two-strip arrangement (D7). Resolved mean: the heat-capacity-weighted mean of the resolved cell 2. A model "crosses" a level when its temperature first reaches it within 900 s. Location is the path label of D14: "terminal end" when the strips heat the hottest node more than the air gap and radiation do, "gap-facing surface" when the reverse holds, "elsewhere" when neither heats it.

## What the lumped sweep already shows (known when these were written)

The lumped node crosses a band edge in 2 of 42 cases, both at the maximum Databank energy (33.2 kJ) and G_bus = 0.5 W/K: it reaches 183.5 C at 69.6 s (tau_rel 10 s) and 79.2 s (tau_rel 30 s), and peaks at 211 to 212 C, below the internal-short band. At G_bus = 0.2 W/K and 33.2 kJ it peaks at 168.1 and 168.9 C, just under the lower self-heating edge. At the median energy (21.5 kJ) it peaks at 152.8 C at most. Cell 1 peaks at 150 to 165 C, 329 to 369 C and 490 to 554 C for the three energies.

## The predictions

P1. At G_bus = 0.005 W/K, in all six energy and duration combinations, neither the lumped node nor the resolved local maximum reaches 169.0 C. Central estimate: the resolved local maximum peaks below 110 C, on the gap-facing surface.

P2. At G_bus = 0.5 W/K, in both cases where the lumped node crosses 183.5 C (33.2 kJ, tau_rel 10 and 30 s), the resolved local maximum crosses 183.5 C earlier by more than half the lumped time, that is before 34.8 s and 39.6 s respectively. Central estimate: about 5 s and 15 s, roughly 93 % and 81 % earlier.

P3. There are cases in which the resolved local maximum crosses a band edge that the lumped node never reaches. Specifically: (a) the smallest G_bus at which the resolved local maximum crosses 183.5 C in some case while the lumped node does not cross it in that case is 0.1 or 0.2 W/K (central estimate 0.2 W/K, with 0.1 W/K close); (b) at G_bus = 0.5 W/K and 33.2 kJ, the resolved local maximum crosses the lower internal-short edge, 255.7 C, for at least one of the two durations, which the lumped node never reaches.

P4. At the median energy and tau_rel = 30 s, the hottest point of the resolved cell 2, taken at the moment it reaches its peak temperature, is labelled gap-facing surface at G_bus = 0.005 and 0.01 W/K and terminal end at G_bus = 0.1, 0.2 and 0.5 W/K, so the switch lies between 0.01 and 0.1 W/K. Central estimate: the switch falls between 0.02 and 0.05 W/K, and at the lowest conductances the hottest point may sit on the bottom rim of the gap-facing line, where the negative strip's annulus adds a few kelvin to the gap heating. The prediction holds if the label changes from gap-facing surface to terminal end once as G_bus rises and these five conductances fall as stated.

P5 (added to the brief's four). At G_bus = 0.5 W/K, in all six energy and duration combinations, the peak rise of the resolved mean above 25 C is at least 15 % smaller than the peak rise of the lumped node. Central estimate: 35 to 55 % smaller. Together with P2 this is the claim that a lumped neighbour errs in both directions at once: it runs its mean too hot and its hottest point too cool.

## Reasoning behind the central estimates (hand calculation, no resolved run)

The strip contact on the cap is a Robin patch of conductance G_bus/2 on an 8 mm disc. The field under a centred disc is axisymmetric, so the roll's azimuthal conductivity plays no part and the heat leaves through axial conduction (25 W/mK) down a column under the disc and weak radial conduction (1.3 W/mK) out of it, plus the end shell. The one-dimensional axial term A (k_ax rho c / (pi t))^0.5 is 0.22 t^-0.5 W/K, the steady anisotropic spreading term 4 a (k_ax k_rad)^0.5 is 0.09 W/K, and the end shell adds about 0.02 W/K, so the draw-away conductance is 0.1 to 0.2 W/K over the first 5 to 30 s. The patch therefore sits a fraction f = G_strip / (G_strip + 0.15) of the way from the bulk temperature to T1: about 0.6 at 0.5 W/K, 0.4 at 0.2 W/K, 0.25 at 0.1 W/K, 0.14 at 0.05 W/K and 0.06 at 0.02 W/K. With cell 1 at 490 to 554 C and the bulk near 40 C, f = 0.6 puts the cap region near 350 C (P3b) and through 183.5 C when T1 passes about 290 C, which cell 1 does at 5 s and 15 s (P2); f = 0.4 gives about 240 C and f = 0.25 about 170 C, which places the smallest conductance of P3a at 0.2 W/K with 0.1 W/K close. On the gap-facing side the air-gap and radiation flux at the line of centres is about 10 kW/m2 at the median energy, which raises the surface by 20 to 30 K over the first minute through the 1.3 W/mK radial conductivity once azimuthal spreading at 25 W/mK is allowed for; the cap patch matches that at about 0.02 W/K (f times 330 K), which places the switch of P4. Because the patches run hotter than the mean, the strips carry roughly (1 minus f) of the heat the lumped formula assumes, with f near 0.6 on the disc and 0.4 on the annulus at 0.5 W/K, which is P5.

## What would count against the pilot's thesis

If P2 and P3 fail, so that the resolved hottest point crosses no earlier than the lumped node, this pilot gives no support for resolving the conduction path at these conductances. If P5 fails, the lumped mean is adequate and the error is local only.
