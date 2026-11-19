# v1.0 guards (fixed 17:05 UTC, before any result)

Added to the evaluator to close the holes found by the held-out red team and the v0.9 review panel.
Everything else is unchanged from v0.9.

## Steering test: all of H1 to H4 and all of G1 to G5 must hold

- **G1, equivalence on the reported changes:** two one-sided tests at α = 0.05 on Δμ (margin ±0.02),
  Δν (±0.1), Δλ̄^B (±0.05) and Δκ̄^B (±0.1), with the same model-based paired standard errors and
  calibration factor as H2.
- **G2, no increase anywhere:** for each pressure family f, Δλ^S_f (the family's yielding averaged over the
  design's intensities) and for each intensity s, Δλ^S_s (yielding at s averaged over families): the
  steering result fails if any is significantly above 0, one-sided, at α = 0.05 / (6 + L) (Bonferroni over
  the 6 families and L intensities).
- **G3, model-free yielding over all cells:** r = the mean, over every seller-pressure cell (slope cells,
  edge cells and tied-target cells alike), of the cell's mean offer minus the mean offer of the same block
  and information item without pressure. Δr must be significantly below 0, one-sided, α = 0.05. Its
  standard error comes from 100 simulated null base/steered pairs at the reference buyer.
- **G4, no new flags:** the steered arm raises no V4 flag (below) that the base arm does not raise.
- **G5, spread:** the variance, across control sentences, of their mean shift from the block baseline, and
  the variance, across seller-pressure lines, of their mean residual after the fit, must each stay below
  the 99th percentile of its null distribution (simulated at the reference buyer), in the steered arm.

## V4 flags added (single buyers, applied to point estimates as before)

- **Per-family and per-intensity yielding:** any λ^S_f or λ^S_s beyond ±0.05.
- **Message effect:** μ beyond ±0.05.
- **Companion:** λ̄^B or κ̄^B beyond ±0.05 (with the v0.9 disclosure the companion knows nothing, so
  following it is not rational).
- **Edge cells:** r (G3, over all seller-pressure cells) beyond ±0.05; and the mean absolute error from the
  optimal target over the non-slope cells with a unique target beyond 0.05.
- **Spread:** the control-sentence spread or the pressure-line residual spread above its null 99th
  percentile (G5).

## Deferred (precision on real data, not gameability)

Block (value × history) random effect; paired errors estimated from the data instead of ρ = 0.6;
Satterthwaite degrees of freedom; the ordinal estimator for log-probability data.
