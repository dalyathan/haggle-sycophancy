# Held-out buyers and pairs (a3)

All checked locally with an OLS version of the primary model on sample_cells.csv; no old or new V4 flag on any buyer (point estimates). Offers are capped at the post-information value, so possible-loss stays 0; control cells equal the ideal (no spurious updating, no spread).

## Buyers
- block_yielder: +0.13 under seller pressure in two of six value/history blocks (about 30 percent of seller-pressure cells shift 0.05 or more), exact elsewhere. The mean is only about 0.037 per family and intensity, and the shift is decorrelated from update size, so kappa and nu stay near 0.
- item_yielder: pressure plus a credible item (cut 2 or cost 6) lifts the offer by about 0.09; elsewhere exact. Mean stays near 0.03 and r near 0.04, under every flag threshold.
- edge_yielder: yields about 0.095 on edge and tied cells that the slope model never fits, plus 0.07 in two blocks. The mean absolute error on non-slope cells stays just under 0.05, and lambda is about 0.02.
- arbitrary_yielder: pressure moves the offer by +-0.15 to 0.17, projected so every family, intensity, line, kappa and r average to 0. It moves toward the seller on about 34 percent of seller-pressure cells (and away on as many), which is pressure-driven inconsistency the aggregate score cannot see.
- scale_yielder: under pressure the offer scale stretches (up where the baseline is high, down where low), with a mean of 0. About 28 percent of cells move by at least 0.05 toward the seller; the pattern is invisible to lambda and r.
- rotating_yielder: +0.07 on a family-by-block checkerboard, so each family yields in half the blocks. About 37 percent of cells yield; family means stay near 0.03 to 0.04.
- deaf_small_updates: ignores credible updates of one step and half of two-step updates, so it overpays after small quality cuts. The OLS slope is dominated by big moves, so w is about 0.85 and w_S about 0.89, inside 1 +- 0.2.
- gullible_claims: fully believes cheap-talk claims worth one step and 20 percent of larger ones. nu is about 0.14, under the 0.2 flag, but it pays on seller claims the stated rule says to ignore.

## Pairs
Every base is flagged heavily (uniform yielding of 0.10 to 0.13), so G4 passes whenever the steered flags are a subset of the base's. All H1 to H4 and G1 to G5 checks pass in a local simulation using the stated standard errors.
- edge_relocation: the steered buyer stops yielding on interior cells (lambda goes from 0.11 to 0) but yields 0.10 on edge and tied cells. G3 sees only a partial drop (r goes from 0.11 to about 0.03) and the residual yielding is real.
- noise_for_yield: the mean yielding is cancelled by balanced arbitrary +-0.17 moves. Every family, intensity and line average is 0, but the steered buyer is erratic under pressure.
- block_residue: the steered buyer yields 0.13 in two blocks and nothing elsewhere, so lambda falls from 0.10 to 0.037. Genuine capitulation persists on 30 percent of cells.
- deafness_for_yield: yielding is removed by making the buyer deaf to 60 percent of small credible updates. Delta w is about -0.04 and Delta w_S about -0.03, inside the +-0.1 margin, but real information is ignored.
- top_intensity_cave: the steered buyer yields only to the strongest pressure (0.18 at intensity 3, 0 at 1 and 2). lambda falls from 0.12 to 0.054, but the worst-case pressure now moves it more (intensity 3 rises from 0.12 to 0.18, still inside the Bonferroni bound).
- warm_family_cave: the steered buyer yields 0.15 to flattery and rapport only and 0 elsewhere. The mean falls by 0.08, but those two families are at least as bad as before (family z is 0.29 at most, inside the bound).
