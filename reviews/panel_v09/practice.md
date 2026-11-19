# Critique of benchmark spec v0.9: practicality for one A10G and 7 to 9B models

Lens: a graduate student, one A10G (24 GB), open-weight 7 to 9B models, log-probability readout, goal is steering away from sycophancy without training. I read all 473 lines. I did not open any other file.

## Verdict

Stage B cannot start from this document alone. Stage A (the statistics) is described in great detail. Stage B and the steering test are not described at all. I could build the game kernel and the scoring maths from the text. I could not build one prompt, one steering vector or the pilot without inventing material parts.

Blockers, in short:
1. No prompt text exists (frame, value wording, seller script, pressure lines at three intensities, controls, information sentences, option format).
2. The steering method is absent (vector source, layer, coefficient, tuning rule, what "steered arm" means).
3. D28, the pilot, has no size, no procedure and no pass/fail rule.
4. The selected design is not fully specified (W5 and W6 are not stated, nor the cell list).
5. The spec itself says (6.7) it is "not ready for a pre-registered steering result": a red-team panel passed all 12 bad buyers and all 8 gaming steering pairs. Starting a GPU stage on a design that is known to be gameable is premature.

## Missing or ambiguous pieces

Blocking:
- **B1 Prompts.** W1 and W2 say "Fruitville verbatim" and "Concordia verbatim", but the text is not in the spec (only a source link). Only one example phrase per pressure family is given. The three intensity levels per family are "scripted" but not written. The neutral length-matched messages, the two irrelevant remarks, the neutral control sentence, the companion's lines and the information sentences ("quality down by 1/2", cost reveal, source labels "inspector" vs "seller") are not written. The finality statement, the stated prior with weights and the credibility rule text (1.8) are described, not given. The option list format (digits 1..9 plus a walk-away token), the chat template and the answer-prefix are not given. I would have to write all of it, and V9 (human raters) would then have to approve it.
- **B2 Steering method.** Nothing says how to build the steering vector (difference of means on pressure vs neutral pairs? which layer? which token position?), how strength is chosen from the 30% development contexts, or what is optimised. H2 to H4 are guard tests, but nothing tells me how to produce a vector that passes them. This is the actual project goal and it is one paragraph away from being specified.
- **B3 Pilot (D28).** It says "measure line, context and paraphrase SDs, the between-arm correlation, the option-distribution shape and width, the base model's yielding, then recompute N*". It gives no item count, no number of models, no definition of "calibration models", no rule for what happens if the measured values are worse (the lattice stops at W5=12, W6=36). The between-arm correlation needs a steered arm, so the pilot already needs B2. This is circular and unstated.
- **B4 Selected design.** Seller types, 5 values, p_max=9, prior and information types are named. The history, the cell list, the blocks, W5 and W6 are not. N*=106,488 equals 1,972 cells x 54 (W5=3, W6=12) or 2,958 cells x 36 (W5=2, W6=12); 6.7 lists three lattice points. The minimum rung-1 N* of 70,992 equals 1,972 cells x 36. I cannot tell which. The cell list is only in "stats_out/v09/rung1.jsonl", which I do not have.
- **B5 Code not provided.** kernel.py, stats_layer.py (Gauss-Newton GLS on a clipped-normal mean with a Woodbury covariance and REML), stage_a.py and share.py are cited, not supplied. The kernel can be rebuilt from section 1 and checked against the worked optima in Appendix B (good). The estimator (about 30 parameters, shared line, context and paraphrase effects through clipping, t degrees of freedom, REML) is a multi-week rewrite. The stage-B ordinal likelihood for log-probability data (D31) is named but not defined, and "has not been simulated" (weakness 13). So the estimator I would use on real data is untested.
- **B6 Which models.** "Several small open-weight families", EV5 "disjoint families", EV6 with a proprietary model. No model is named, no instruct vs base choice, no rule for V6/V7/V8 thresholds on real models beyond the listed ones. V7 needs two models at competence >= 0.5 with error <= 0.25, so a model failing V7 is silently useless.

Non-blocking:
- N1 W3 (anchor line), W4 (persona), W8 to W12 are listed as wording axes with no levels. The mixed-level optimal design for stage B is named, not specified. Fix them to one level each for a first run.
- N2 The label shift (W9) conflicts with the log-probability clause; labels 1..9 are forced anyway. Multi-digit tokens would break the readout for 10+.
- N3 The softmax shrinkage (0.82 at width 1, 0.64 at width 2) means expected-offer yielding on real models will likely be well below the latent value. Detecting a drop of 0.05 (0.4 of a grid step at p_max=9) on a readout that shrinks it to 0.64x is about 0.03. Not discussed as a power problem.
- N4 No check that 7 to 9B models yield at all. D28 mentions it, but a null base effect would end the project. This should be the first experiment, not part of a pilot.
- N5 The statistical stack has 38 decisions and 11 critiques of the same simulation. Everything in section 5 is about synthetic buyers, none of it about a real model.
- N6 The sampled readout (n=5 or 10) is only for the proprietary model. It multiplies cost by n and is not needed.
- N7 The guards (walk-away agreement, invalid rate, regret) say "not simulated in stage A", so their power is unknown.
- N8 "Per arm" count: the 106,488 includes the development contexts (a third), which only the base arm needs. Evaluation items are 70,992 per arm if W6=12. The spec text is not explicit about this, and the cost-in-calls line (6.4) says "about twice N* less the development contexts".

## Compute estimate

Assumptions (stated so you can change them):
- One forward pass per item with log-probability readout (read the next-token logits over digits 1 to 9 plus the walk-away token). No generation, no reasoning (the readout clause forbids it).
- Average prompt about 450 tokens (frame, values, seller script, one message, options). With hidden-state steering the cost per pass is the same as the base pass.
- 7 to 9B model in bf16 (about 15 to 17 GB, fits in 24 GB with batch 8 to 16). Sustained throughput on an A10G of about 4 prompts per second with prefix caching of the shared frame (vLLM or HF with a cached prefix). Plausible range 2 to 8 per second. Without prefix caching, about 2 per second. I did not measure this; it is arithmetic: 2 x 8e9 x 450 = 7 TFLOP per prompt against about 30 TFLOP/s sustained.
- Steering by adding a vector at one layer with a forward hook. No fine-tuning.

Full selected design (N* = 106,488, two arms):

| Item | Count | Time at 4 per second | Range (8 to 2 per second) |
| --- | --- | --- | --- |
| As requested: 2 x 106,488 | 212,976 passes | 14.8 h | 7.4 to 29.6 h |
| Strict need: evaluation, base 70,992 + steered 70,992 + development contexts for the vector 35,496 | 177,480 passes | 12.3 h | 6.2 to 24.6 h |
| Strength tuning: 4 candidate coefficients on the 35,496 development items | 141,984 passes | 9.9 h | 5 to 19.7 h |

So one model costs roughly 12 to 25 h of GPU time, about 1 day of wall-clock time. With 3 models (needed for V7, rotation and a held-out family) it is 3 to 4 days. About $1 per GPU hour on a cloud A10G gives $40 to $100 for one pass of everything. That is affordable on its own. What is not affordable is stage B, which repeats this per wording configuration: with, say, 16 wording configurations x 4 finalists x 3 calibration models x 12 h this is about 2,300 GPU hours (95 days). The spec gives no number of wording configurations, so this is my illustration.

Pilot (D28), my version, since the spec gives none: one model, the selected design at W5=2, W6=12 (47,328 evaluation items per arm, 23,664 development), base arm plus a crude steered arm, then the variance components. That is 47,328 x 2 + 23,664 = 118k passes, about 8 h. On two models, 16 h. A quarter of the blocks, as a first look, would be 2 to 4 h per model. Add 0.5 h for the yielding-exists check (N4).

Statistics compute: the synthetic gates are already run (the spec says rung 2 and 3 were split across 8 machines). Refitting on real data is minutes on a CPU.

One structural point that matters for cost. The yielding precision (SE 0.0195 at W5=2) is set mainly by the number of pressure lines (6 families x L intensities x W5 paraphrases) and the number of contexts (W6), by the spec's own variance components (line 0.05, context 0.05, residual 0.08). The extra cells (blocks, information items, history crossing) mainly serve the structure rules (D22, D15, K3, K5) and the w_S and credulity tests. So the cell count could be cut a lot while keeping the yielding test at about the same precision. I have not simulated this; the spec's rung-1 formula is closed-form, so the author can check it in minutes.

## Proportionality

For a resume project ("steer a model away from sycophancy without training") the plan is far too large. It is a benchmark-design research programme: 38 decisions, 11 critique rounds, seven evaluator families, a proprietary model, a human rater panel, a pre-registered selection step. Most of that protects against a benchmark being gamed by a search procedure, which is not what a steering project does. The compute for one design is fine; the engineering and the stage-B wording search are not. The spec's own red-team result (all gaming attempts pass) means that the added machinery does not buy the protection it is meant to.

## A minimal credible plan

Aim: show that a fixed steering vector lowers yielding to seller pressure on one 7 to 9B model, while keeping updating and offer level, with an honest interval.

1. **Check the effect exists (1 day).** One instruct model (e.g. a Llama 3.1 8B or Qwen 2.5 7B instruct; my example, not in the spec). Fruitville-style prompt, p_max=9, 5 values, no history, 3 seller types, stated disclosure, rational-heavy prior. Seller-ward pressure only, 6 families, 2 intensities, 12 contexts, 3 paraphrases. Compare expected offer with and without pressure and with neutral messages. If yielding on the offer scale is under about 0.03, stop and pick a stronger setting.
2. **Cut the design.** Drop: history, buyer-ward pressure (keep the companion as a later control), hidden disclosure, the sampled readout, the proprietary model, EV5/EV6, human V9 (use two authors), and the wording search (fix one level per axis). Keep: quality down from seller and inspector, quality up from seller (credulity item), one competing-offer item, a walk-away option, the six pressure families, two irrelevant remarks and neutral controls crossed with information. About 5 blocks x about 100 cells = roughly 500 cells, 36 answers per cell (W5=3, W6=12) is about 18,000 evaluation items per arm plus 9,000 development items. About 45,000 passes, 3 h on one A10G.
3. **Specify steering.** Difference of mean activations between pressure and matched neutral prompts on the 9,000 development items, one mid layer, add with 3 to 4 coefficients, pick the one with the largest drop in pressure yielding that keeps updating slope within 0.1 and mean offer within 0.05. Choose on development items only.
4. **Run the test once.** Base and steered arm on the 18,000 held-out items. Report Delta lambda-S, Delta w, Delta offer level and slope, Delta kappa, Delta nu and Delta mu with 95% intervals. Use the clipped-normal GLS (or simpler: a mixed model with random line and context effects on expected offers) rather than the full 30-parameter machinery. Use the spec's equivalence margins (0.1, 0.05) and H1/H4 as stated; they are reasonable.
5. **Replicate on a second model** (3 h plus 3 h). Total GPU time about 15 h, a week of calendar time, about $20.
6. **Report limits** as the spec does: one decision, stated rule, expected-offer shrinkage, averaged estimands.

What I would cut from the spec first: the search (stages A to C), the ensemble families, the 106k-item design, the size/recovery gates as a deliverable, the 38 decision table. What I would keep: the separation of yielding from updating, the neutral and irrelevant controls, the equivalence guards on updating and offer level, and the pilot to measure variance before choosing sizes.

Caveat: my time and cost figures are arithmetic from stated assumptions, not measurements. Throughput on an A10G could be a factor of two either way.
