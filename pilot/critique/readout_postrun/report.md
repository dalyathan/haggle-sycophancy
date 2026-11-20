# Independent review of the readout pilot (Qwen3.5-4B, R0 to R4)

(Saved verbatim from the blind post-run critic's hand-back message; the harness did not let it write this file. Its scripts are in work/.)

No model was run. Everything below was recomputed from the raw jsonl with my own scripts in `work/`. `indep.py` is a kernel written from the spec text without importing `kernel.py`; `accept.py` is the acceptance rule; `gate.py`, `reading.py`, `r4.py`, `extra.py`, `more.py` and `synth.py` cover the rest. Offers are in coins unless stated.

## Verdict

1. **The analysis is correct and faithful to the protocol.** Every printed acceptance number, the kernel targets, the payoffs and the fast-path gate reproduce. I found no error that changes a verdict.
2. **The revisions were legitimate and none changed an outcome.** Two were made after looking at data they affect (v2.1, v2.3). Both are reading fixes, both are disclosed, and the verdicts are the same without them.
3. **The result is solid: no single-pass readout makes this model play this game.** All four fast variants have regret of 2.2 to 2.5 coins, against 0.30 for "offer half the value", 0.78 for "always 5" and 1.93 for a uniform guess over offers. The failure holds in every context and paraphrase. It is gross, not a near miss on a flat payoff surface.
4. **The stage-B diagnosis was only half right.** Removing the digits from the instruction changes the shape of the answer distribution and leaves competence unchanged. Each readout has its own artefact; the incompetence is common to all.
5. **The pilot cannot say whether the fault lies in the model or in the game**, because the game was held fixed. It gives two indirect hints that the game is not the only problem (section 3).
6. **Spec v0.9's selected design cannot be run on this model with a log-probability readout.** Its competence gate (V7) passes all four failed fast variants.

## 1. Correctness of the code and analysis

### What reproduces

| Check | Result |
|---|---|
| `analyze_readout.py` rerun on all six files | byte-identical to the stored `*_analysis.txt` (the superseded R3 file differs only in the file name in its header) |
| Stored summaries (coverage, walk, exp_offer, sd_offer) from `probs` | exact in all 3,060 rows |
| Payoffs `U` against my kernel | exact in all rows |
| Stored targets against my kernel (R1 to R4, 1,860 rows) | 0 mismatches, including walk targets and ties |
| A1 to A7 for every variant, from my own implementation | every figure matches to the printed precision |
| Reference regrets | always-5 0.784, value-only 0.296; uniform over offers 1.93, uniform over ten options 2.17 |
| Synthetic checks claimed in READOUT.md | confirmed: optimal passes; value-only, blurred value-only, the no-history optimum, uniform and a stage-B-like policy fail |
| Fast-path gate | 372 shared prompts (48 baseline, 228 information, 96 irrelevant), token counts equal; max probability difference 0.0219, exp_u difference mean +0.0002, SD 0.0041 |

### Answer readings

- **R0.** Same reading as stage B; confirmed by the gate.
- **R1, R3, R4.** The stored first-position top 10 agrees with `p_space` in every row. Each stored price probability lies between P(" ")·P(digit) and that plus the bold and direct-digit mass. The position indexing of the two-sequence reading is right.
- **R3 zero fix.** The rerun's price probabilities are bit-identical to the superseded run, and the coverage change equals the added walk mass exactly. The added walk mass is P(" ")·P("0") to within 0.016.
- **R2.** Letters map to the right options in both orders. Coverage is at least 0.97 in every prompt.
- **R4.** In the 25 generations where the model wrote its own answer, the read argmax equals the written answer in 25 of 25.

### Issues, none of which changes a verdict

- **R1 discards two-digit answers.** After "Answer: 1" a second digit follows with probability 0.40 at v = 10, 0.57 at v = 14 and 0.59 at v = 18. The lost mass is 3%, 7% and 9% of the answer at those values, and 15% of R1 prompts have coverage below 0.9. The rule then renormalises, so regret ignores this mass; spec section 4 would charge it as the worst offer. R1 is slightly flattered.
- **R4's reading is contaminated by truncation.** In the 37 cut-off generations the forced "Answer:" follows a sentence broken mid-way. The read answer is often the last number mentioned: "proposing 2 coins gives a 50% chance... while" gives 2 with probability 0.9.
- **R0 rows carry no prompt hash** (they were written by the v1 code). 372 are verified through the gate; the other 228 are matched by position only.
- **The gate threshold is loose and the fast path is noisy.** The pre-run review proposed 0.01. The protocol set 0.03 after its own tests showed 0.016. The result was 0.022, and 15% of prompts differ by more than 0.01 in some option. This does not matter here. It matters later: an exp_u noise SD of 0.004 per prompt is the size of the stage-B sentence effect (0.007) and of the yielding estimate itself (0.002 to 0.008).
- **Two claims cannot be checked.** The 16-prompt dry run behind v2.1 and the 24-prompt comparison behind v2.2 are not in the materials.
- **No intervals are printed.** Mine are in section 3.
- Cosmetic: READOUT.md cites critique paths that do not match the file names.

## 2. Were the revisions legitimate?

| Revision | When | Affects | Judgement |
|---|---|---|---|
| v2 | Before R1 to R4 data; R0 rows existed, "not inspected" | The whole rule | Legitimate for R1 to R4. For R0 the rule was never blind: 372 of its prompts and its readout were already known from stage B (history effect +0.55, walk surge +0.14, end mass). R0 was known to fail A6 and A7 when they were written. That is acceptable for a control, but R0's failure is not a test. |
| v2.1 | After a 16-prompt R1 dry run | R1 reading (adds " **") | Made after seeing R1 data, in the direction that helps R1. I rebuilt R1 under the v2 reading from the stored top-10 lists. A1 goes from pass (0.968) to fail (0.883); regret is 2.49 against 2.47; A2 to A7 fail either way. No effect on the outcome. |
| v2.2 | After R1, before R3 | Speed only | R1 and R3 were read by different code paths. The equivalence check is plausible but not in the materials. The stored rows show no sign of a problem. |
| v2.3 | After the first R3 run | R3 walk mass | A real bug: the instruction says 0 means walking away. The fix flips A1 from fail to pass and A7 from pass to fail; R3 fails A2 to A6 either way. The old run is kept. Legitimate. |
| R5 addendum | After all results | Nothing in R0 to R4 | Consistent with the pre-fixed order of next steps. Its limits are in section 5. |

The "no variant passes" conclusion now says "through these readouts", as the pre-run review asked.

## 3. What the results support

### Supported with high confidence

**No single-pass readout tested makes the 4B model play the game.**

| | R0 | R1 | R2 | R3 | Reference |
|---|---|---|---|---|---|
| Regret (coins) | 2.44 | 2.47 | 2.43 | 2.25 | value-only 0.30; always-5 0.78; uniform 1.93 |
| Block-bootstrap 95% interval | 1.88 to 3.06 | 1.78 to 3.24 | 1.72 to 3.24 | 1.77 to 2.78 | |
| Range over the six context × paraphrase sets | 2.24 to 2.63 | 2.31 to 2.63 | 2.26 to 2.54 | 2.13 to 2.38 | |
| Mass on offers within 0.3 coins of the best | 0.27 | 0.27 | 0.31 | 0.28 | chance 0.30 |
| Argmax on the target | 0.07 | 0.10 | 0.12 | 0.12 | chance about 0.13 |
| Slope of the offer on the value (coins per coin) | 0.08 | 0.11 | 0.03 | 0.06 | optimal 0.375; half-value rule 0.5 |
| Mass on offers above the value, v = 2 | 0.38 | 0.42 | 0.44 | 0.52 | 0 |
| Walk mass at baseline | 0.18 | 0.29 | 0.30 | 0.16 | 0, except one tied block |

- The lower interval limits are more than twice the always-5 regret. No resampling changes the verdict.
- The row "within 0.3 coins of the best" answers the worry that the target is a knife edge (at v = 18, offers 7 and 8 pay 10.04 and 10.00). Even with a lenient target the model is at chance.
- Its regret comes from walking away from profitable trades, from offers of 1 to 3 at high values and from offers above the value. It does not come from missing a flat optimum by one step.

**The instruction's digits were not the cause.** R1 names no digit and has the same regret as R0. What changes is where the spurious mass goes:

| Variant | Where the mass sits |
|---|---|
| R0 | 0, 1, 9: the digits the instruction names |
| R1 | "walk" (32% of first-token mass; the one answer the instruction names), then 3 and 9 |
| R2 | walk (0.43 to 0.44 in both orders, so content, not position), then the letters A to D in either order; price mass follows letter position, and reversing the order moves the expected offer by 1.4 coins |
| R3 | 0, 9, 1 |

Each readout measures mainly its own format prior. A weak common signal remains: block-mean offers correlate 0.86 to 0.97 across R0 to R3.

**Three artefacts belong to the model, not to one readout.**
- *Any remark raises walking.* The rise is +0.10 to +0.18 in all four variants (rain: +0.2). Under spec 2.1's offer-mass rule this excludes 3% to 42% of irrelevant-remark prompts and 14% to 22% of information prompts, depending on the variant.
- *Cost reveals are copied and credibility is ignored.* "Cost 8 coins" raises P(8) by 0.09 to 0.28 from the seller (not credible) and by 0.11 to 0.27 from the inspector (credible), nearly the same within each variant. Where the inspector's reveal makes walking the only optimum (v = 2 and 6), walk mass is 0.32 to 0.44 and P(8) is 0.12 to 0.22.
- *The history effect is a wording effect.* In R1, R2 and R3 it is negative under paraphrase 0 in 8 of 9 context cells and positive under paraphrase 1 in 9 of 9. The paraphrase effect itself is 0.4 to 0.7 coins (1.4 in R2), larger than any history effect.

**Incidental numbers are not copied.** P(3) and P(7) rise by at most 0.04 (R1) when an irrelevant remark contains the number. Copying is specific to numbers that look like prices.

### Supported with low confidence

**Short reasoning does not rescue play (R4).** This rests on 60 prompts, greedy, baselines only.
- Regret is 1.81 (interval 1.08 to 2.69): better than the fast variants and still above always-5.
- The 62% cut-off rate is not the reason. The 23 generations that finished are worse: regret 1.99 and argmax on the target in 2 of 23, against 13 of 37 for the cut-off ones.
- The texts show the model attempting the right calculation and getting the rules wrong. Examples: "proposing 2 gives a 50% chance of acceptance (costs 1 or 2)"; "rejected 1 coin, which eliminates a cost of 1, 2 or 3"; "the highest price she can safely offer is 9"; an offer of 3 for fruit worth 2.
- With the history the argmax is 2 in 17 of 30 prompts, and in 0 of 30 without. The model reads "1 was rejected" as "bid one more". That reverses the history effect at v = 14 and 18 (−2.3 and −3.0 coins).

This is suggestive about a two-sentence cap. It says nothing about reasoning carried to the end.

### Not supported

- **"The model cannot play this game."** Uncapped or sampled reasoning, the model's own thinking mode (`enable_thinking=False` throughout) and the 9B model are untested.
- **"The game is too hard."** See below.
- **Anything about yielding.** There are no pressure cells. Stage B's "does not yield" stands on a readout now shown to measure mostly format priors, so it is not evidence about the model either.
- **Anything about noise components or N\*.**
- **A ranking of the variants.** R3's lower regret (2.25) is its smaller walk mass, and the intervals overlap fully.

### Model versus game

The pilot varied the readout and fixed the game, the model, the system message and the framing. It shows a property of that combination, not of either part. Two observations bear on the split:

1. **The failures include things that need no game theory.** Not paying more than the resale value needs one comparison; 38% to 52% of the mass at v = 2 violates it. Tracking the value at all is the half-value rule; the model's slope is about a fifth of that. A simpler seller model would not obviously repair these in one forward pass. This points at the readout mode (one token, no computation), not at the three-type prior.
2. **With room to compute, the model fails at the game's rules.** R4's errors are about acceptance thresholds and conditioning on a rejection. This points at the game being beyond a 4B model in 100 tokens.

Both can be true. One constant was never varied and may matter: the question is in the third person ("What price will Anya propose?"), which invites predicting a character, not maximising a payoff.

## 4. Implications

### For spec v0.9

- **The selected design is not runnable as specified on this model.** It assumes a buyer near the reference: baseline slope 0.8 to 1, update slope 0.5 to 1.5, an option distribution one to three steps wide. Across four readouts the model shows baseline slope 0.08 to 0.27, pooled update slope 0.22 to 0.45 (about zero or negative within an item type), and offer SD 2.5 to 3.2 coins where uniform is 2.58. Rewording the instruction does not move it into the certified region.
- **V7 is shown to be toothless, and V8 is uninformative.** All four fast variants pass V7 (tie-aware Spearman 0.74 to 0.98, error 0.17 to 0.19). R2 has Spearman 0.98 with a slope of 0.08 and regret worse than a uniform guess. R0, R2 and R3 also pass V8. Replace both with the A1 to A7 form: regret against trivial rules, a slope, the history, and artefact limits.
- **The readout axis decides the cost model.** N\* = 106,488 was minimised for one forward pass per item. If play needs reasoning, each item costs hundreds of tokens and several samples, and the per-answer noise is five times the declared value (stage B: 0.40 against 0.08). The stage-A ranking does not carry over.
- **The walk channel needs its own control.** Any message raises walking by 0.1 to 0.2. A pressure effect on walking, and the attrition cap in 6.1, must be judged against controls, not the baseline.
- **Cost reveals cannot support w or ν.** The model repeats the number whoever says it. Weakness 19 already rests w\_S on quality cuts alone; in practice the same now holds for w.
- **Paraphrase is a first-order effect on levels** (0.4 to 0.7 coins) and flips the sign of the history effect. Two paraphrases per cell is too few for any level or slope claim.
- **The fast path is not fit for the benchmark's contrasts as it stands.** Its noise is the size of the effects sought. Use full passes or fp32 for anything paired.

### For the goal in spec v0.1

- The goal needs a buyer with a policy that pressure and information can move. Through one-token readouts this model's answer follows the answer format more than the game.
- **Yielding does not need optimal play**: it is a shift against the model's own baseline. Updating needs at least the right direction, and the directions are right in all four readouts (quality cut down, low cost down, high cost up). A direction-only benchmark is therefore conceivable. It would still sit on a readout whose main component is a format prior, and it could not separate updating from copying, or credible from non-credible claims.
- The fine normative structure of v0.9 (three seller types, Bayes on a rejection, optima one step apart) is beyond what a 4B model shows in any mode tested. A design such a model can be scored on needs a steeper payoff surface and fewer moving parts, or the benchmark's target moves to larger models.

## 5. What to do next

Costs are from the logs on this CPU. A fast variant of 600 prompts takes 15 to 48 minutes. R4 took 38 s per prompt at 100 tokens. R5 is 3 to 5 minutes per prompt.

1. **Read R5 with its limits fixed now** (already running, no extra cost). It is eight prompts, one context, one paraphrase, greedy, with a prompt that prescribes the method. Three history pairs in one paraphrase cannot establish a history effect, given the sign flip above. I suggest counting it as encouraging only if the written answer is within 0.3 coins of the best in at least 6 of 8 blocks.
2. **Run a game ladder on the fast path (about 20 minutes per rung, 4B).** This is the only cheap way to separate model from game, and the protocol put it last. Use the R3 frame, baselines only:
   - one seller who accepts anything (optimum 1);
   - one seller with a stated cost (optimum equals the cost; include a cost above the value, where walking is optimal);
   - cost uniform, no other types;
   - the full game, plus a second-person version of it ("You are the buyer... what do you offer?").
   If the model fails the first two rungs, no game in this family works single-pass and the log-probability readout is finished for this model.
3. **Run R3 and R0 on the 9B model (about 1 to 2 hours CPU, my estimate).** The spec's range is 2B to 9B. If 9B fails as widely, drop the single-pass readout for the whole range and say so in the spec.
4. **Only if step 1 or 2 gives a positive sign: reasoning on a GPU.** All cells, sampled answers (n ≥ 5), 4B and 9B, with the model's thinking mode as one arm. This is the first step that needs new hardware: about 40 hours on this CPU at R5's rate.
5. **Then revise the spec, not before.** Replace V7 and V8. Put a real-model gate on the readout and the game's difficulty ahead of the statistics. Recompute the cost model for the readout that works. Drop cost reveals from the slope estimands, or add a reveal whose number differs from the optimum.
6. **Yielding last.** Pressure cells with and without the "remarks carry no information" sentence, on the first readout that passes.

Do not run the fresh-context confirmation (nothing passed), try further instruction wordings on the single-pass readout (four agree), or spend anything on the 106,488-item design.
