# Review panel on spec v0.9: merged findings

Four independent blind critics, each given only spec v0.9 and a different lens (statistics: Opus; gaming:
Fable; construct validity: Fable; practicality: Sonnet). None saw the others' reports. Full reports beside
this file. Unanimous verdict: not ready for a steering result; ready, at most, for a small real-model pilot.

| Finding | Raised by | Blocking for a steering result | Smallest fix |
| --- | --- | --- | --- |
| Pressure comes from the counterparty, not the user; "sycophancy" in the literature is deference to the user | construct | yes (framing) | rename to "yielding to counterparty pressure", or put the pressure in the user's/principal's voice; state the principal and objective in every prompt |
| Averages cancel: per-family and per-intensity yielding, edge cells and walk-away cells are not checked | gaming, stats, held-out panel | yes | per-family/intensity guards; model-free raw pressure-minus-no-pressure difference over all cells |
| Message effect: Δμ untested, and a saturating (non-additive) message reaction manufactures an H1 pass | gaming, stats, held-out panel | yes | raw cell-difference contrast as primary; test Δμ; separate two-message term |
| Reported-only changes (Δν, Δλ̄^B, Δκ̄^B) let yielding be traded for credulity or obedience to the companion | gaming, held-out panel | yes | equivalence tests, and the steered arm must raise no new V4 flag |
| Between-arm correlation fixed at 0.6 and equal arm variances; never estimated | stats, gaming | yes | paired errors from the actual item-level differences; size runs at ρ = 0.3 |
| No block (value × history) effect: α1, level and w standard errors understated | stats | yes | block random intercept correlated across arms |
| Steering vector can learn the benchmark's lines; no held-out family, frame or transfer task | gaming | yes | hold out 2 families and 1 frame from steering development; one transfer set outside the game |
| No limit on vectors/strengths tried on evaluation items; no minimum effect | gaming | yes | pre-register one steered configuration; interval-based or minimum-effect claim |
| Stage-B ordinal estimator for log-probabilities undefined and unsimulated; width change ungated | stats, practicality | yes | specify and simulate it, or gate the width change |
| Belief vs preference channels not separated; risk-averse or prosocial buyers scored as errors | construct | yes (interpretation) | belief probe; non-social source control; state the objective; score w against the model's own baseline |
| No prior commitment, so "caving to pushback" is not tested | construct | no | two-step cell: own offer, content-free reply, revision |
| df rule gives z quantiles where effective df are small (level, w_S) | stats | yes (cheap) | Satterthwaite or Kenward–Roger df per contrast |
| No prompt text, steering method, pilot procedure, named models or explicit cell list | practicality | yes for stage B | write them |
| Plan disproportionate for a resume project; stage-B wording search costs thousands of GPU hours | practicality | no | minimal plan: one 7–9B model, ~500 cells, difference-of-means vector, ~15 GPU hours |
| Prior art missing: BASIL, SycEval, Sharma et al., NegotiationArena | construct | no | cite and position |

What the panel says is sound: the kernel and conventions; the power target arithmetic (SE 0.0195); the
size-gate false-fail figure (0.277); the novelty of the exact payoff target, the pressure × credible
information crossing and the equivalence guards.
