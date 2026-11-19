# Statistical critique of spec v0.9 (sections 2, 5, 6)

Scripts and outputs: work/checks.py, work/checks_out.txt, work/blocks.py, work/blocks_out.txt.

## Verdict

Not ready to run real language models through the selected design for the steering test or any pre-registered result. Five errors are blocking (E1 to E5). In simulation the design meets its own gates: power, size and bias all pass under the declared generator. But the generator and the real-data estimator differ from real data in exactly the places that set the steering test's error rates. Three gaps matter most. The paired standard error rests on a declared correlation that nobody estimates. Block-level effects are not modelled. And the estimator that stage B will apply to log-probability data was never simulated.

The D28 pilot on calibration models can run as a measurement exercise if it also measures a block variance and per-term cross-arm covariances. Do not compute N\* from it, and do not run any H1 to H4 decision, until E1 to E5 are fixed and V2, VS and power are rerun.

## What I verified

| Claim | Result | How |
| --- | --- | --- |
| 0.0195 is the paired SE that gives H1 power 0.8 at W5 = 2 (V6, D32) | Correct. df = 6·3·2 − 11 = 25; 0.05/(t.95 + t.80) = 0.01950; exact noncentral t gives 0.01956. At W5 = 3 (df 43), the selected design's point, the value is 0.0198. | checks.py §1 |
| Power "rests on about 10% margin" (D28) | Consistent. A GLS on the seller-ward lines alone (additive family + intensity model, SD 0.05·s, plus μ from 21 control sentences × W5), paired with ρ = 0.6, gives an SE of 0.0175 at W5 = 2, 10% under 0.0195. At W5 = 3 it gives 0.0143. Cell count plays no part: H1 power depends only on the line SD, W5 and ρ. | checks.py §2 |
| VS: a design whose rates are all exactly 0.05 fails "about a quarter of the time" | 0.277, assuming independent rates (8 rates at n = 1,000 and 40 at n = 1,500, limit 0.065). | exact binomial, §4 |
| The selected design's size is controlled in simulation | Yes. Its largest rate over 48 is 0.055. If every rate were exactly 0.05 the expected maximum would be 0.064, and P(max ≤ 0.055) = 0.0001. Its tests are therefore conservative under the simulated (known-variance) setting. | §4 |
| 0.75 is "2.5 Monte-Carlo errors below 0.8" at 400 runs | Correct (SE 0.02). | arithmetic |
| Item formula; 30% development share | Correct. 70,992 = 1,972 × 2 × 18 and 106,488 = 1,972 × 3 × 18: the selected design is the rung-1 cheapest cell count moved from W5 = 2 to W5 = 3. | §6 |
| Weakness 16: context SD 0.06 raised N\* from 69,696 to 100,672 | Ratio is exactly 26/18, so W6 went from 12 to 18. I reproduced the cause. The offer-level SE is almost all context: about 0.0150 at SD 0.05 and W6 = 12, against 0.0171 needed for TOST power 0.8. At SD 0.06 it is 0.0172 and fails. H3's offer level therefore sets W6. | §6 |
| Funnel products | 25,324 = 6,331 × 4; 39,540 = 9,885 × 4; 6,331 + 3,554 = 9,885. | arithmetic |
| V2 subset (D34) | 96 points; points 1, 6, …, 96 give 20 points, both σ_e levels alternating, 5 per λ^S level. | enumeration |
| Selected design's structure (section 1 definitions) | 8 unique baselines, exactly the K5 floor. 7 slope blocks with u0 in {0.375, 0.5, 0.75, 0.875} (4 levels, so D22 is met). 6 of 7 blocks have ≥ 2 steps of headroom. | blocks.py |
| Multiplicity of the steering test | Correct as stated. H1 to H4 form an intersection-union test, so each component at α = 0.05 keeps the joint claim at 0.05. No correction is needed. | definition |

## Errors, ranked

**E1. Blocking. The paired SE uses a declared between-arm correlation that is never estimated on the tested pair (6.1, 6.2, D11, D37).** Section 6.1 says the paired difference "uses the declared between-arm correlation", ρ = 0.6 on every term with equal arm variances. D28 replaces 0.6 with a value from calibration models, not from the model and steering vector under test. The calibration factor and VS both simulate exactly ρ = 0.6, so neither can detect a wrong ρ. The SE scales as √(1 − ρ). The table shows the H1 size (and the size of one TOST side) at the planned critical value when the true ρ differs:

| True ρ | Size |
| --- | --- |
| 0.5 | 0.066 |
| 0.4 | 0.085 |
| 0.3 | 0.102 |

If the steered arm's SD is 1.4 times the base arm's, the SE is understated by a factor of 1.27. A steering vector acts on the very pressure lines whose effects set the H1 variance, so a lower correlation on those lines is the expected case, not an edge case.
*Fix:* estimate the paired covariance from the paired data. Either fit both arms jointly with arm-specific variances and a cross-arm covariance for each shared term (line, sentence, context, cell) by REML, or fit the model to cell-level differences. Add VS configurations with ρ = 0.3 and unequal arm SDs.

**E2. Blocking. No block (value × history) effect in the generator or the covariance (2.3, 6.2).** Every cell of a block shares the value wording and the history. A real model's baseline deviates from α0 + α1·u0 by a block-specific amount; the V7 competence gate itself tolerates a mean absolute error of 0.25. The GLS treats those deviations as independent cell noise across roughly 200 cells per block.

The selected design has 7 slope blocks with sd(u0) = 0.186. A per-arm block SD of only 0.02 gives a true paired SE(Δα1) of 0.036 from this term alone. The entire H3 α1 TOST budget is 0.034 (margin 0.1, power 0.8). If the model SE ignores the term (model SE 0.02 to 0.03), one side of the α1 TOST has size 0.15 to 0.21 at the margin; at block SD 0.04 the size is 0.27 to 0.33. The offer level (H3) and w are affected the same way. The simulations cannot show this because their generator has no such term. The α1 size excursions that persist in VS even without it (6 rates, weakness 12) show α1 is already the most fragile contrast.
*Fix:* add a block random intercept, correlated across arms, to the generator and the covariance. Use df ≈ blocks − 2 (here 5) for α0/α1 contrasts. Rerun V2, VS and power for the selected design and its fallbacks at block SD 0.02 and 0.05. Have D28 measure the block SD.

**E3. Blocking. The stage-B estimator for log-probability data is undefined and unsimulated (D31, weakness 13).** Every certified property belongs to the clipped-normal mean GLS: V2 bias, VS size, power and N\*. D31 says stage-B log-probability data will be fitted with an "ordinal likelihood", but the spec gives no link, no cutpoints, no per-arm scale and no mapping of λ̄^S, w or the margins (±0.05, ±0.1) onto it. Sampled readout is not simulated either (2.1). Whichever readout stage B picks, the test that is run has no simulated error rates.

Readout width also matters. Over the 50 finalists, yielding visible in expected offers is 0.82 of latent λ^S at width 1 and 0.64 at width 2 (6.7). If a vector widens the option distribution from width 1 to 2 and the estimator does not correct for it, a base λ = 0.1 appears to fall by 0.018, or 0.92 planned SEs. H1 alone would then reject about 22% of the time with no latent change. H2 catches this pure widening (w also shrinks, by about 0.22), but only because the H2 margin is crossed; the width change is not gated. Conversely, if real distributions are width 2, H1 power at a true −0.05 drop falls from 0.80 to 0.48.
*Fix:* before stage B, specify the ordinal model fully: latent normal, fixed cutpoints at grid midpoints, an arm-specific scale, and estimands in u units. Then rerun V2, VS and power with it on the selected design and its fallbacks. Otherwise keep the clipped-normal estimator for stage B and gate the per-arm width change.

**E4. Blocking for the steering claim (the spec concedes it in 6.7). H1 to H4 do not mean "reduced yielding without reactance or collateral shift".** Every estimand is an average over 6 families × 3 intensities, so reactance in some cells cancels yielding in others. Δμ, Δν and Δλ̄^B are reported but not tested. A blind red team's 8 steering pairs passed H1 to H4 in all 10 top designs.
*Fix:* add heterogeneity guards. For example, a max-t (or Bonferroni over 18 cells) one-sided test that no Δλ\_{f,s} is below a reactance margin. Add equivalence tests on Δμ, Δν and Δλ̄^B. Rerun the held-out panel with fresh pairs before freezing.

**E5. Blocking for real fits, cheap to fix. The df rule "slope cells − parameters" (6.2) is wrong for contrasts that rest on shared terms.** With about 1,900 slope cells this rule gives z quantiles. But the offer level rests on W6 = 12 context shifts (df ≈ 11), and w\_S rests on the seller quality-cut sentences: 3 if S9 is single, 9 if graded. A real REML fit estimates those variances from that many units. The true one-sided size at the rule's critical value is:

| Contrast | Units | Size |
| --- | --- | --- |
| Offer level | 12 contexts | 0.064 |
| w\_S, graded | 9 sentences | 0.069 |
| w\_S, single | 3 sentences | 0.12 |

Simulation hides this, because variances are fixed and the known-variance t quantiles make simulated sizes conservative (t.95 at df 43 is 1.681 against 1.645, which already gives 0.046). VS at 0.055 therefore does not carry over to REML fits.
*Fix:* use Satterthwaite or Kenward–Roger df per contrast. At minimum, use (units of the dominant shared term) − 1.

**E6. Non-blocking. V6 does not check the precision N\* was planned for (D32, 5).** V6 gates only Δλ̄^S and Δŵ. Its Δŵ limit of 0.05 is looser than the 0.034 that H2 needs: at SE 0.05, TOST power at a true change of 0 is 0.28. Nothing checks Δw\_S, Δκ̄^S, the offer level, Δα1 or H4. The quoted threshold, 0.0195 "at W5 = 2", is for the wrong lattice point: the selected design sits at W5 = 3, where the threshold is 0.0198.
*Fix:* check every H1 to H4 contrast against its planned SE at the design's own lattice point. For a TOST that is margin/(t.95 + z.90).

**E7. Non-blocking. N\* and the selection depend on Monte-Carlo noise in the calibration factor (D37, 6.3, D20).** The factor is the maximum of 9 SD ratios from 200 pairs each, floored at 1. With perfect calibration its mean is 1.073; P(> 1.05) = 0.77 and P(> 1.10) = 0.19. With a 10% H1 margin at W5 = 2, a factor above about 1.11 moves a design to W5 = 3, which costs 1.5 times the items.

Yet 106 of 117 designs needed more replication. That is more than noise alone explains, so model-based SEs are genuinely too small in some shifted configurations. One global factor per contrast patches this; the cause is not identified. The confirmation rerun (D20) does not recompute the factor or N\*.
*Fix:* publish the factors by contrast and configuration. Use about 1,000 pairs, or a pooled ratio, and recompute N\* in the confirmation rerun. Find which contrast and configuration drive the ratio.

**E8. Non-blocking. v0.9 couples λ̄^S to the information cells through μ (D30).** m\_i now counts information sentences, so μ is estimated partly from information cells. Any misfit of the linear update model there shifts μ̂, and λ̄^S = pressure shift − μ then moves by the opposite amount. Examples of such misfit: updating concave in |Δu\*|, sign-only updating, or item-type-specific slopes. No misspecified generator varies the update model.
*Fix:* give information sentences their own message term μ\_I, which the control × information cells identify. Alternatively, add a V2 generator with a nonlinear update and check the bias of λ̄^S.

**E9. Non-blocking. The simulations support power of at least about 0.75, not 0.8 (6.5, D36).** At 400 runs the 0.75 threshold passes a test with true power 0.75 about 53% of the time and one at 0.73 about 20% of the time. The rung check uses factor 1, so its simulated "power" partly includes any excess size. The selected design's own per-test and joint simulated power is not reported (D27 promises it); the minimum joint power reported is 0.75.
*Fix:* report the selected design's per-test and joint power with Monte-Carlo errors, and state the supported figure as ≥ 0.75 unless a lower confidence bound reaches 0.8.

## Smaller issues

- **Contradictory tie rules.** 6.5 breaks rung-3 ties by "higher simulated H1 power, then the design id"; D35 and 6.4 break them by "more distinct information sentences".
- **Lattice claim false where selection happens.** 6.4 says "every required design reaches power at the same lattice point". That holds at rung 1 only; rung 2 uses (2, 12), (3, 12) and (3, 18).
- **Gate history inaccurate.** Section 5's history says v0.9 "kept every threshold except the softmax check", but V6 (D32) and the rung-2 rule (D36) also changed. The v0.9 sentence also sits before the v0.8 sentence.
- **Superseded decision not marked.** D25 (300 pairs) conflicts with D37 and 6.2 (200 pairs).
- **H4 factor unspecified.** H4 is a single-arm test, but the paired factor is defined for differences. The spec does not say which factor H4 uses.
- **VS is largely in-sample.** Three of its four points are the factor's own calibration configurations (D37), and the max-of-9 factor makes those rates conservative by construction. The one held-out point (σ\_e 0.08) interpolates between the two simulated noise levels; it does not extrapolate.
- **Coverage gate is permissive.** V2 requires median coverage ≥ 0.90 for a nominal 95% interval, so half the region may sit below 0.90.
- **Bias-limit scope unclear.** The misspecified-generator limit of 0.02 covers "every fifth grid point". The spec does not say whether that includes points outside the operating region.
- **Line SD assumed proportional to intensity.** The line SD is assumed to be 0.05·s, so GLS weights s = 1 lines 9 times as heavily as s = 3 lines. If real line SDs are not proportional, the SE is wrong. D28 should measure the SD per intensity.
- **Steering-vector multiplicity not controlled.** Nothing limits how many steering vectors or layers are tried on the evaluation contexts. Pre-register one vector per model, chosen on the development contexts only.
- **Informative attrition.** Items dropped from both arms for low offer mass (2.1) depend on the steering. Attrition is capped at 5%, but no sensitivity analysis is planned.
- **Competence test is weak.** It is a Spearman correlation over 8 baselines (the selected design is at the K5 floor). A threshold of 0.5 with n = 8 is below the one-sided 5% critical value (about 0.64).
- **Paraphrase split ambiguous.** "Paraphrases never cross the split" (3.6) implies separate development paraphrases, but the item formula reuses W5 for both. The spec should say whether development uses its own W5 paraphrases.
- **Missing for the selected design:**
  - the S9 setting and the number of distinct information sentences behind w\_S and ν;
  - the calibration factor for each contrast, and which test forced W5 = 3;
  - N\* with standard deviations inflated ×1.5 and ×2;
  - per-test and joint power.
