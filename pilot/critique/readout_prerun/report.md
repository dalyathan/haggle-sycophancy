# Pre-run review of the readout pilot (READOUT.md, readout.py, fastread.py)

No model was run. Checks were made with `work/a.py` (prompts, optima against the kernel, overlap with stage B) and `work/b.py` (regret of reference policies under the acceptance rule). Regret figures are in coins over the 10 baseline blocks.

## Verdict

Do not run yet. The design is a reasonable response to the stage-B finding, and the prompts, payoffs and R2 option mapping are correct. Four things must change first, because each either cannot be fixed after data without breaking the "fixed before data" claim or can silently corrupt results:

1. The acceptance rule can be passed by a policy that ignores the seller prior and the history, and it ignores the two artefacts stage B found (number copying, walk surge under remarks).
2. The rule is not implemented and is ambiguous in several places; there is no analysis script.
3. The fast path has no pass threshold and is only checked on R0.
4. The R1/R4 reading misses likely answer forms and cannot tell "1" from "10" to "18".

## What I verified

- R0 builds 600 prompts; exactly 372 are identical to stage-B prompts (48 baseline, 228 information, 96 irrelevant), as READOUT.md states.
- Baseline payoffs and single optima match the kernel in all 8 untied blocks. The two tied blocks (v = 2 with history, v = 6 without) are handled as ties.
- R2: letters map to the right offers in both orders; walk away is J in paraphrase 0 and A in paraphrase 1.
- Group boundaries, the hidden-state index on the padded batch (`s.shape[0] - 1`) and the pairing of the two R1 texts per prompt are correct.

## 1. Design

**Blocking**

- **D1. The acceptance rule does not test use of the game.** Reference regrets: always 5, 0.78; value-only (half the value), 0.30; half the value capped at 8, 0.10; the no-history optimum used in every block, 0.12; the best policy that looks only at the value, 0.014. All but the first pass A4, and all pass A5 (Spearman 0.89 to 0.93, slope 0.88 to 1.18). Nearly all of the value-only rule's regret comes from offering 9 at v = 18 (2.04 of 2.96 coins summed over blocks). A variant can therefore pass while ignoring the prior and the history. Add a history criterion, which stage B's plan had: the offer change at fixed value for v = 10, 14, 18 (optimum +1, +2, +1), for example positive in all three and at least half the optimal change on average.
- **D2. A blurred value-only rule beats the sharp one.** Half the value plus normal noise of SD 1 has regret 0.289, below the 0.296 of the rule itself, so "value-only with noise" passes A4. Compare against the best value-only reference, or require a margin.
- **D3. Acceptance uses baseline cells only.** Number copying and the walk surge under irrelevant remarks (+0.14 in stage B) are collected but only "reported". A variant that copies "3" or "7", or walks whenever the seller says anything, can be chosen. Add thresholds now for the number-copy shift in P(3) and P(7), and for the shift in exp_u and walk under irrelevant remarks.

**Non-blocking**

- R1 changes three things at once against R0 (no digits in the instruction, walk as a word, the "Answer:" frame). A failure or success cannot be attributed. R0 with the "Answer:" frame would separate the frame at 600 fast prompts.
- The system message still names digits ("from 1 to 9", "70 in 100", "4 coins", "proposed 1 coin", the value). R1 removes them only from the instruction.
- R1 names "walk" in the instruction and no digit. Stage B found that named answers attract mass, so the bias may move to walking. Walk mass of 7% alone uses up the whole A4 margin (0.07 x mean best payoff 4.27 = 0.30). Report regret split into its walk part and its offer part, so a walk leak is not read as "cannot play".
- R2 confounds option order with the whole-prompt paraphrase; the "order effect" is order plus wording. Stage B measured a paraphrase effect of 0.051.
- R4 is greedy, not sampled as the post-run review suggested. The distribution after one greedy reasoning will be nearly a point mass, so A2 is trivially met and sd_offer is not comparable with the other variants or with the benchmark's per-answer noise.
- R4 runs on baseline cells only, so it has no number-copy or updating evidence before it could be chosen.
- The post-run review also asked for the 9B model and a cost reveal whose number differs from the optimum. Neither is here.
- The "no variant passes" conclusion is too broad. Four readouts, one system message and a two-sentence reasoning cap do not show the model cannot play the game; say "not through these readouts" and keep longer reasoning and 9B as options beside a simpler game.

## 2. Acceptance rule

**Blocking**

- **A-1. No analysis script exists.** The rule is prose, and these choices are open: A2 end mass on q or on the offer distribution; A3 with or without walk in a tie; A5 on 8 block means or on 48 prompts; medians over which units; whether the fresh run's information cells have any criterion ("must pass A1 to A5 again" is defined only on baseline). Write `analyze_readout.py` and test it on synthetic records (optimal, value-only, uniform, stage-B-like) before any run.
- **A-2. "Clearly better" for R4 is undefined.** Fix a number (for example regret lower by a stated margin), or the choice between R4 and a fast variant is made after seeing results.

**Non-blocking**

- A3 is not binding. With ties, chance is 0.12 as coded (0.13 with walk counted), above the 0.10 threshold; always 5 scores 0.20. Raise it or drop it.
- A2's SD bound (2.0) is looser than A4 implies: optimal play with SD 1.5 already has regret 0.36 and fails. A4 is the binding width criterion; A2 adds only the end-mass check.
- No margins or intervals. Each criterion is a point estimate over 60 correlated prompts, and A4 is decided by differences of a few hundredths of a coin.
- The fresh-context rerun is a weak guard against picking the best of four. Blocks, paraphrases and wording are the same; only names and openings change, and stage B's context SD was 0.015. It will mostly reproduce the first run.
- A5 with 8 points: Spearman 0.5 is not distinguishable from 0. The slope criterion carries A5.

## 3. Code

**Blocking**

- **C1. The fast path has no gate.** READOUT.md says the R0 difference "measures the numerical effect" with no threshold. On a hybrid model the realistic failures are silent: a linear-attention layer that ignores or misuses its cached state for a multi-token suffix, positions restarting at 0 if the model does not honour `cache_position`, or `_repeat` mis-shaping a state. Fix a threshold before running (for example max absolute probability difference below 0.01 and SD of the exp_u difference below 0.005), and make R1, R2 conditional on it. Also add a self-check in every run: the first group read both batched and by full passes, abort on disagreement. The R0 comparison does not cover R1 and R2 texts.
- **C2. `_repeat` assumes every state tensor is batch-first with size 1 on dim 0, and that states live in `cache.layers`.** A state shaped otherwise, or a size-1 counter tensor, is repeated wrongly or not at all. I cannot check this without the model; C1's self-check is the test. Run it with BATCH above 1 and with unequal suffix lengths.
- **C3. R1/R4 reading is too narrow and unasserted.**
  - `walk_ids` may be empty if " walk" is not one token; then P(walk) is silently 0. Assert it.
  - Nothing asserts that "Answer: 5" tokenises as "Answer:" + " " + "5". The stage-B and capability-check code asserted the equivalent.
  - The instruction no longer says "one digit", so " five", a digit with no space, or a newline are plausible answers and count as lost coverage. Decide now whether number words and a direct digit are read.
  - "1" after "Answer: " may start 10 to 18 (the values 10, 14, 18 are in the prompt). Stage B sampled this; the new code dropped it. Add P(digit after "Answer: 1") for every R1/R4 prompt and record the second-step top 10.
- **C4. Walk targets are wrong in the stored annotations.** `walk_optimal` is `m < 0`, which never occurs. The kernel's walk and tie cases differ from `best` in 14 of the 100 cells per context and paraphrase:
  - inspector high-cost reveal at v = 2 and v = 6 (4 cells): kernel target is walk, code stores `best` = 1 to 7;
  - quality cut at v = 2 with history (2 cells): kernel target is walk, code stores `best` = [1], `u_star` = 0;
  - quality cut at v = 2 without history (2 cells): kernel says tied with walk, code stores `u_star` = 0 and it would enter the updating slope;
  - v = 2 with history, baseline, remarks and the seller's high-cost claim (6 cells): walk is a tied optimum and is missing from `best`, which lowers A3.
  Regret (A4) is unaffected. Store the kernel's `cell()` result instead of recomputing.

**Non-blocking**

- `--dry N` writes real rows to the real output file and the full run resumes after them. If the code changes after this review, stale rows stay. Store a hash of the prompt in each row and check it on resume, or write dry runs elsewhere.
- Resume counts lines; a partial last line after a crash is counted as done and corrupts the next record.
- R4 discards the model's own text after "Answer" and does not flag a 100-token cut-off. Record the raw generation, whether "Answer" appeared, and the generated answer, to compare with the forced reading. A "**Answer:**" format leaves a stray "**" before the forced frame.
- R4 `generate` inherits the checkpoint's generation config (a repetition penalty would apply to greedy decoding); set it explicitly.
- `one()` returns None for token id 0, and `pad_token_id or 0` treats id 0 as missing; harmless here.
- The readout.py docstring says "8 baseline blocks"; the code and READOUT.md use 10.
- Fresh context 3 opens "Late in the afternoon" and is followed by "Good morning." and morning remarks.

## 4. What would mislead

- A pass read as "the model plays the game", when the rule admits a capped value-only policy (D1, D2).
- A fail on A4 caused by a few percent of walk mass, read as "the model cannot play" and used to justify simplifying the game.
- A fast-path fault reported as a "numerical effect" (C1).
- Low R1 coverage from unread answer forms, read as an unusable readout (C3); or P(1) inflated by two-digit answers at v = 10, 14, 18.
- R4's narrow distribution taken as low answer noise.
- Updating and walk-shift reports built on the wrong targets in the 14 walk and tie cells (C4).
