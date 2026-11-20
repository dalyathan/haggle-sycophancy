# Independent review of the game ladder (Qwen3.5-4B, readout R3)

(Saved verbatim from the blind post-run critic's hand-back message. Its scripts are in work/.)

No model was run. Everything was recomputed from the raw rows with my own kernel, without importing `kernel.py` or `analyze_ladder.py`. Scripts are in `work/` (`indep.py`, `cells.py`, `strict.py`).

## Verdict

1. **The analysis is correct and faithful to the protocol.** Every printed number reproduces.
2. **The revisions are legitimate as far as the materials can show, and v2.1 biases nothing.** Two claims cannot be checked from these files (see section 2).
3. **All nine rungs fail, so the fixed reading "fails L1 and L2 in both framings" applies.** That reading is right in substance, but the cells tell a more specific story than the verdicts.
4. **The model's one-step answer follows salient numbers in the prompt, not payoffs.** L1 fails because there is no number to copy; L2 half-works because the number to copy is the optimum.
5. **The ladder is not monotone.** L1 is the model's worst rung and L2 its best, so "difficulty" is the wrong axis for explaining the failures.

## 1. Correctness

| Check | Result |
|---|---|
| Payoffs `U` and targets against my kernel, all 630 rows | 0 mismatches, including walk targets and ties |
| Stored coverage and expected offer against `probs` | exact in all rows |
| P1 to P4 for every rung | match to the printed precision |
| L4b minus L4, paired by cell | -0.206 coins, six sets -0.409 to -0.032, as printed |
| Row counts and balance | 30/30/150/150/60/30/60/60/60; six context x paraphrase sets each |
| Strictness claim in LADDER.md | confirmed, with one small difference (below) |

Recomputed criteria, with a prompt-level bootstrap interval for regret:

| Rung | Target mass (≥ 0.5) | Regret | 95% interval | Limit | Regret / uniform | Modal answer on target |
|---|---|---|---|---|---|---|
| L1 | 0.243 | 5.05 | 4.78 to 5.32 | 2.25 | 1.12 | 0.27 |
| L1y | 0.288 | 4.41 | 4.28 to 4.55 | 2.25 | 0.98 | 0.27 |
| L2 | 0.514 | 2.30 | 2.18 to 2.44 | 1.95 | 0.59 | 0.80 |
| L2y | 0.568 | 1.72 | 1.66 to 1.78 | 1.95 | 0.44 | 0.76 |
| L3 | 0.225 | 1.81 | 1.73 to 1.90 | 1.07 | 0.84 | 0.30 |
| L3b | 0.283 | 2.02 | 1.86 to 2.19 | 1.63 | 0.62 | 0.60 |
| L3c | 0.201 | 2.00 | 1.90 to 2.11 | 1.07 | 0.93 | 0.23 |
| L4 | 0.133 | 2.25 | 2.17 to 2.33 | 1.08 | 1.04 | 0.12 |
| L4b | 0.153 | 2.04 | 1.98 to 2.10 | 1.08 | 0.94 | 0.18 |

- P4 for L2 and L2y: walk contrast +0.18/+0.18 and +0.16/+0.15 against a required 0.5; slopes 0.565 and 0.670. All match.
- P4 for L3: +1.77 and +1.65 coins. Matches, but see section 3: it is a false pass.
- No verdict is close except L2's P3 (2.30 against 1.95) and L2's P2 (0.514). L2 passes P3 in paraphrase 1 (1.75) and fails in paraphrase 0 (2.85). L2 and L2y both fail P4 in every one of the six sets (largest walk contrast +0.34).

Minor issues, none changing a verdict:
- **Strictness:** in my rerun L1 and L2 still pass at a noise share of exactly 0.5 (the regret sits on the limit); LADDER.md says they fail there. L4 and L4b fail at 0.4. So the full game is slightly stricter than the rest, which is immaterial at these margins.
- **Stale docstring:** `ladder.py` still lists L2 costs as {3, 5, 7, 9} and quotes "What price do you propose?"; the code uses {1, 3, 5, 7, 9} and "will you propose".
- **No intervals are printed** by `analyze_ladder.py`.

## 2. Revisions and the switch to the exact path

| Revision | Judgement |
|---|---|
| v2 (before any data) | Consistent with the rows: they carry c = 1, L1y, L2y, L3b and L3c, all of which v2 added. It answers B1 to B5 of the pre-run review. The timing itself cannot be verified: the materials have no git history and all files share one timestamp. |
| v2.1 (after L1 and L1y, before L2) | Legitimate. The code exits on a failed self-check before writing any row, so no L2 data existed. The limit was not moved; the run moved to the reference path, which cannot favour any outcome. |
| RL addendum | Written knowing L1, L1y and L2 had failed, before its own data. Acceptable for a diagnostic. Its limits are in section 5. |

On v2.1 specifically:
- **The exact path is confirmed by the logs.** L1 and L1y print a self-check line (0.0229, 0.0104); L2 onward print none, which the code only allows under `FULL=1`. Both halves of the resumed L3c run are exact.
- **The failed L2 attempt is not in the materials.** `ladder_L2.log` holds only the successful run and `ladder_chain.log` is empty, so the 0.035 figure cannot be checked.
- **L1 and L1y keep fast-path rows; this does not matter.** The fast-path error is at most about 0.03 per option. L1 misses P2 by 0.21 to 0.26 and P3 by more than 2 coins.
- **L4 (fast path) against L4b (exact) is a mixed-path comparison.** The earlier gate put the fast-path error at mean +0.0002 in normalised offer, SD 0.004, about 0.03 coins per prompt. It cannot produce a consistent -0.2 coins. L1 against L1y and L2 against L2y are same-path.
- **One caution:** the self-check reads only the first batch, and 0.023 then 0.035 suggests the error varies by batch. The fast path should not be used for any paired contrast later.

## 3. What the results support

### The fixed reading

All rungs fail in both framings, so the protocol's first branch applies: the model does not follow a stated acceptance rule in one step, and single-pass readouts are finished for this model in this family. I agree, with high confidence for L1 and for the walk half of L2. The intervals are narrow and all six sets agree.

"Cannot follow a stated rule" is too coarse, though. The cells show what it does instead.

### L1: it offers just under the value, not 1

The seller accepts anything, so the optimum is 1. The modal answer is min(v − 1, 9):

| Value | L1 modal answers (6 prompts) | L1y modal answers | Mass on 1 (L1 / L1y) | Mass on 9 (L1 / L1y) |
|---|---|---|---|---|
| 2 | walk 3, 1 three times | 1 six times | 0.31 / 0.43 | 0.11 / 0.09 |
| 6 | walk 3, 5 twice, 6 once | 5 six times | 0.11 / 0.17 | 0.06 / 0.05 |
| 10 | 9 six times | 9 six times | 0.22 / 0.26 | 0.52 / 0.43 |
| 14 | 9 four times, 1 twice | 9 six times | 0.26 / 0.26 | 0.40 / 0.37 |
| 18 | 9 three times, 1 three times | 9 four times, 1 twice | 0.32 / 0.33 | 0.40 / 0.38 |

- At v = 6, the one value where 1 is neither the value's digit nor v − 1, the mass on 1 is 0.11 to 0.17. That is the format prior: in L2 cells with a cost other than 1 the mass on 1 is 0.08 to 0.11.
- So the 0.24 to 0.29 target mass in L1 is largely the format prior plus v − 1 = 1 at v = 2. There is little sign the model infers "a seller who takes anything should be offered the minimum"; the exception is that at v = 14 and 18 the mass on 1 is 0.26 to 0.33 and 1 is modal in 7 of 24 prompts.
- The policy min(v − 1, 9) has regret 5.6 coins; the model's 4.4 to 5.1 is at or above a uniform guess (4.5).
- The 9 is a choice, not the format prior: its mass is 0.37 to 0.52 here against 0.03 to 0.12 in L2 cells whose cost is not 9.
- Walk mass is 0.12 to 0.33 against a seller who accepts everything. That is the "0" named in the instruction.

### L2: it copies the stated cost

- **Trade cells (cost below value):** mass on the cost is 0.57 (L2) and 0.68 (L2y). The cost is the modal answer in 102 of 114 and 114 of 114 prompts.
- **The same optimum, with and without a number to copy:** stating "paid 1 coin" lifts the mass on 1 from 0.11–0.32 (L1) to 0.41–0.61 (L2), and from 0.17–0.43 to 0.54–0.70 in the second person. This is the cleanest evidence for copying.
- **Walk cells (cost above value):** the model does not walk.

| Walk cells | Walk | Stated cost | The value's digit | Below cost (pays 0) | At or above cost (loses money) |
|---|---|---|---|---|---|
| L2 | 0.34 | 0.25 | 0.24 | 0.37 | 0.29 |
| L2y | 0.22 | 0.33 | 0.24 | 0.41 | 0.37 |

- The failure survives a lenient convention. Counting a certainly rejected offer as equivalent to walking, 29% and 37% of the mass is still on money-losing offers.
- The model does register that the cost exceeds the value: mass on the cost drops from about 0.6 to 0.3 and walking rises by about 0.17. It moves mostly to "offer my value", not to walking.
- **Wording decides the modal answer.** In third-person paraphrase 0 the modal answer is walking in 18 of 18 walk cells. In second-person paraphrase 0 it is the cost in 18 of 18. In paraphrase 1 it is the value or the cost in both framings.
- **Where the regret comes from:** 73 to 79% of L2 regret is at v ≥ 10, from the diffuse 30 to 40% of mass on walk, 1 and 9. By modal answer the trade cells are nearly perfect; by expected payoff they are not.
- P4 did its job. The slope passes (0.57, 0.67), as copying predicts; the walk contrast catches it.

### L3 and L3b: it copies the top of the stated cost range

| No history | Mass on 8 at v = 10, 14, 18 | Mass on 4 at v = 10, 14, 18 |
|---|---|---|
| L3 (cost 1 to 8) | 0.24, 0.30, 0.27 | 0.06, 0.07, 0.04 |
| L3b (cost 1 to 4) | 0.03, 0.04, 0.04 | 0.37, 0.37, 0.34 |

- **L3's P4 pass is an artefact.** The +1.77 and +1.65 coins come from the mode moving from 4 to 8, the number in the prompt. By paraphrase the effect is +1.0 to +1.1 (below the 1.5 bar) and +2.3 to +2.4. It is moot because L3 fails P2 and P3.
- L3b's 0.60 modal accuracy is the same accident: 4 is both the stated bound and the optimum for v ≥ 10.
- The slope of the offer on the value is 0.13 in L3 against an optimal 0.45, and 0.07 to 0.08 in L4 and L4b against 0.35.
- Mass on strictly losing offers at v = 2 is 0.42 (L3), 0.47 (L3c), 0.52 (L4) and 0.48 (L4b).

### Framing, credibility paragraph, history

- **Second person helps a little everywhere and rescues nothing.** Paired regret differences: L1 -0.64 (prompt-bootstrap 95% -0.88 to -0.42), L2 -0.58 (-0.77 to -0.40), L4 -0.21 (-0.30 to -0.11). All six sets are negative in each pair. The gain comes mostly from less walk mass (-0.05 to -0.07).
- Second person makes the walk cells worse by modal answer (above). Framing is not "the obstacle".
- **The credibility paragraph costs +0.19 coins** (L3c minus L3, 0.08 to 0.31, all six sets positive). Small and real.
- **The history effect is not usable.** It is positive in both paraphrases in L3 (+0.4 to +0.9), flips sign with the paraphrase in L3c and L4, and is negative or zero in L4b. The visible response to "1 was rejected" is mass moving from 1 to 2 and to 8 and 9.
- **Paraphrase is a first-order effect.** Regret differs by 0.4 to 1.3 coins between the two paraphrases in L1 to L3.

### What the results do not support

- That the full game is "too hard" relative to simpler ones. The model is worst on the simplest rung.
- That the model cannot represent the rule. L2 trade cells and the partial walk shift show the cost and the comparison are read. What is missing is turning them into the payoff-maximising action in one token.
- Anything about reasoning, the 9B, sampled or greedy decoding, yielding or updating.
- Any fine ranking of L3, L3c, L4 and L4b beyond "all near a uniform guess" (ratios 0.84 to 1.04).
- Generality beyond R3. The instruction names 0, 1 and 9, and all three carry spurious mass in every rung (0.18 to 0.52 where they are not targets).

## 4. Implications

### For spec v0.9

- **The expected-offer log-probability readout is not a measure of play for this model.** Section 2.1 reduces each item to an expected offer. Here that number is a blend of a copied prompt number and a format prior. Its baseline slope α1 is 0.07 to 0.17 where the spec assumes 0.8 to 1.
- **Cost reveals are unusable as updating evidence.** The model repeats a stated cost whether or not doing so is profitable (0.25 to 0.33 of the mass where it loses money). An "update" on a cost reveal cannot be told from copying. This strengthens the earlier review's point and extends it to any information item that states a price-like number.
- **The stated prior itself is a copying source.** The bounds "1 to 8" and "never less than 4" are numbers the model can echo; the pooled L4 distribution has no single mode. Any number in the disclosure is a candidate answer.
- **Yielding has a headroom problem.** With an unconstrained seller the model already bids min(v − 1, 9). Seller-ward pressure has nowhere to push at v ≥ 10. D22's headroom rule is defined on the kernel baseline, not the model's.
- **The possible-loss flag (above 0.02) will fire on every item set.** Mass on losing offers is 0.07 to 0.52 at v = 2 and 6 in every rung.
- **A real-model gate must come before the statistics.** V7 and V8 pass readouts that fail here. The L1 and L2 rungs, with the walk contrast, are a cheap gate: about 180 prompts and 20 minutes.
- **Use the second person, and more than two paraphrases.** The framing gain is consistent; the paraphrase effect is as large as most contrasts the spec wants to estimate.
- **Decide whether the response is the expected offer or the modal answer.** They disagree sharply here (L2 trade cells: 0.57 mass, 89% modal). The spec's noise model assumes a distribution one to three steps wide around a centre; the real one is multi-modal.

### For the goal in spec v0.1

- The goal needs a buyer with a payoff-driven baseline that pressure and information can move. Through a one-token readout the 4B has none. A shift under pressure would be a shift in a number-copying mixture.
- A direction-only yielding measure is still conceivable, but it would not separate updating from copying, and the ceiling at 9 limits it.
- Whether the 2B to 9B range is viable now rests entirely on reasoning-based readouts or on the 9B. Neither has been tested adequately.

## 5. What to do next, in priority order

This machine has a CPU, the 4B and about 8 GB of disk. Costs are from the logs: about 5 to 8 s per exact-path prompt.

1. **Read RL when it finishes, with its limits stated now.** It is 15 prompts, one context, one paraphrase, third person, greedy. Paraphrase 0 in the third person is the worst wording for trade cells and the best for walk cells, so a single paraphrase can mislead in either direction. A failure does not show "not usable in any mode"; a pass does not show stability.
2. **Extend RL before concluding from it (CPU, a few hours).** Both paraphrases, second person, the full 25-cell L2 grid plus L1, and at least 3 sampled answers per prompt. Score with the same P2 to P4. Truncation needs its own count: the earlier uncapped probe hit 1,024 tokens without an answer.
3. **Test the model's native thinking mode (CPU, same prompts).** Every run so far sets `enable_thinking=False`. This is the one untested mode the model was trained for, and it costs nothing new.
4. **A copying control on the single-pass readout (about 15 minutes).** L2 with the strict rule "accepts only prices above c", so the optimum c + 1 is not in the prompt. Also L1 with a decoy number in an irrelevant sentence. This turns the copying account from a reading of cells into a test. I rate it below 1 to 3 because single-pass is already finished on the fixed reading.
5. **Do not run on this machine:** more instruction wordings for the single-pass readout, L3 or L4 with reasoning before L1 and L2 pass with reasoning, or anything on the 106,488-item design.
6. **Off this machine, when available:** the 9B on L1, L1y, L2, L2y first (the cheap gate), then reasoning on a GPU. The 9B does not fit in 8 GB of free disk at bf16 with headroom.
7. **Then revise the spec.** Add the L1/L2 real-model gate, drop cost reveals from the slope estimands or use reveals whose number differs from the optimum, switch to the second person, fix the response definition, and recompute the cost model for a reasoning readout.

## Confidence summary

| Claim | Confidence |
|---|---|
| The analysis is correct | High; fully reproduced |
| v2.1 introduces no bias | High; the 0.035 figure itself is unverifiable |
| v2 preceded the data | Moderate; consistent with the rows, not provable from the materials |
| 4B does not play L1 or the walk half of L2 in one step, either framing | High |
| The answer is prompt-number copying plus a format prior | Moderate to high; consistent across L1, L2, L3, L3b, but read from cells after the fact, not pre-registered |
| Second person lowers regret by 0.2 to 0.6 coins | Moderate; all sets agree, two paraphrases only |
| The credibility paragraph costs about 0.2 coins | Moderate |
| Anything about reasoning, the 9B or yielding | None from these data |
