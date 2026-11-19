# Readout pilot (fixed before data)

Why: the stage-B pilot (`PILOT.md`, results in `out/analysis_4b.txt`, blind review in `critique/postrun/report.md`) found that the 4B model's
one-digit answer is dominated by the digits named in the instruction (0, 1, 9) and by digits in the prompt; it loses to the rule
"offer half the resale value" and to uniform guessing. Before the benchmark's noise and behaviour assumptions can be measured, the
readout has to measure play. This pilot changes only how the answer is asked for and read. The game (system message), the model
(Qwen3.5-4B, base, bf16) and the cells are fixed.

## Revision history

- v1 (commit 0546eb1): first version.
- v2 (this version, before any R1 to R4 data): revised after the blind pre-run review (`critique/readout_prerun/report.md`). R0 was
  already running when the review came back; its rows were written but not inspected, and R0's prompts are unchanged. Changes: R3
  added; the "Answer:" reading widened (direct digit, number words, " " then "walk") and corrected for two-digit answers; kernel targets
  (walking away, ties) replace a recomputed optimum; acceptance rule tightened (A3 threshold, A5 slope only, A6 history, A7
  artefacts); a fast-path gate and a per-run self-check; R4 made diagnostic; dry runs and resumption made safe.

- v2.1 (before the R1 run): a 16-prompt dry run of R1 (written to a separate `.dry` file, not part of the results) showed the
  token " **" (the start of a markdown-bold answer) carrying 11 to 32% of the mass after "Answer:", which the v2 reading counted as
  lost coverage. The reading now follows " **" with the digit or "walk". Nothing else changed.

## Variants (`readout.py`)

| | Instruction | Read |
|---|---|---|
| R0 | the stage-B instruction (one digit, 0 = walk away) | digit after "{buyer} proposes " |
| R1 | no digits in the instruction; walk away is the word "walk" | after "Answer:" (below) |
| R2 | ten lettered options (nine prices, walk away); ascending in paraphrase 0, descending in paraphrase 1 | letter after "Answer:" |
| R3 | the R0 instruction | after "Answer:" (below): separates the frame from the instruction wording |
| R4 | R1 plus "think it through in at most two short sentences first"; greedy, at most 100 new tokens | after the reasoning, "Answer:" (below) |

Reading after "Answer:": walking = " walk" or " Walk", or " " then "walk"/"Walk"; price d = " " then the digit d, or the digit
directly, or the number word " one" to " nine" when those are single tokens, or " **" (markdown bold) then the digit or
"walk"/"Walk" (added in v2.1). The mass on 1 is multiplied by 1 - P(a digit follows
"Answer: 1"), since 1 may start 10 to 19. The tokenisation of "Answer: 5" and "Answer: walk" is asserted at start-up.

R2 confounds option order with the paraphrase; its paraphrase difference is order plus wording. R4 is greedy, so its option
distribution is close to a point mass: A2 is not informative for it and its spread is not comparable with the other variants.

## Cells

Every block of the selected design (5 values x history, 10 blocks) in 3 contexts x 2 paraphrases (R4: baselines only):
- baseline;
- each information item generated in the block (both sources), no pressure;
- the two irrelevant remarks of the stage-B pilot;
- two irrelevant remarks containing a number (3, 7): the number-copying check.

R0 reproduces 372 stage-B prompts exactly (the 8 untied baselines, information cells and irrelevant remarks).

## Fast-path gate

The fast path (`fastread.py`: system message cached and reused, prompts batched with right padding) must agree with full forward
passes. On the 372 prompts R0 shares with stage B: maximum absolute difference in any option probability at most 0.03 and SD of the
exp_u difference at most 0.005. In tests on 15 to 31 prompts before this rule was written, the cached path differed by at most 0.011 and
the batched path by at most 0.016 in probability, and exp_u by at most 0.006. R1 to R3 are run only if R0 passes the gate. Every run also
reads its first batch both ways and stops if any option probability differs by more than 0.03.

Targets are the kernel's (`kernel.cell`, `kernel.baseline`): walking away where the optimal offer is certainly rejected, and ties
(including ties with walking away) kept as sets.

## Acceptance rule (v2)

q is the answer distribution over {walk, 1..9}, normalised by its coverage. Baseline cells: all 10 blocks x 3 contexts x 2 paraphrases.

- A1 usability: median coverage over baseline prompts at least 0.9.
- A2 shape: median offer-distribution SD below 2.0 coins, and median end mass of the offer distribution (P(1)+P(9) among offers)
  below 0.4.
- A3 target: mean mass on the kernel target set (any tied answer, walking included when it is in the set) at least 0.25. Chance is
  about 0.13 with ties; always 5 scores 0.20.
- A4 competence: regret in coins (best expected payoff minus the model's; walking pays 0), averaged over the 10 block means, below
  both always-5 (0.78) and value-only (0.30). Regret is reported split into its walk part and offer part.
- A5 value tracking: least-squares slope of the 8 untied block means of exp_u on u0 at least 0.5 (tie-aware Spearman reported).
- A6 use of the history: at v = 10, 14 and 18 the expected offer with the history minus without (block means, coins) is positive in all
  three and at least 0.67 on average (half the optimal +1, +2, +1). Without A6, a rule that looks only at the value passes A1 to A5.
- A7 artefacts: irrelevant remarks against the baseline (same block, context, paraphrase): |mean exp_u shift| at most 0.03 and mean
  walk shift at most 0.05; number copying: P(3) and P(7) with a remark containing that number minus with the irrelevant remarks, at most
  0.05 each.

Synthetic checks before data (`analyze_readout.py` on generated rows): an optimal policy passes; value-only, value-only with noise
(SD 1), the no-history optimum everywhere, uniform and a stage-B-like policy (mass on 0, 1, 9) fail.

A fast variant (R0 to R3) passes if A1 to A7 all hold. Among passing variants the one with the lowest A4 regret is chosen. It is then
rerun on three fresh contexts (new names and scene openings, `CONTEXTS=fresh`), all cells, and must pass A1 to A7 again. The fresh
contexts guard against little: blocks, paraphrases and wording are the same.

R4 is diagnostic and cannot be chosen from this pilot. If it passes A1, A3 to A6 and no fast variant passes, the next step is R4 on all
cells (for A7 and updating) with sampled rather than greedy reasoning; if a fast variant passes, R4 is only reported.

If no variant passes, the conclusion is that this model does not play the selected game through these readouts. Next options, in
order: longer or sampled reasoning, the 9B model, a simpler game (fewer seller types, a steeper payoff surface).

## Reported for every variant (not part of the rule)

- the option distribution averaged by block; mass on 0/1/9; the digit echo of the resale value;
- number copying: the change in P(d) for d = 3, 7 between the number remarks and the irrelevant remarks without numbers;
- updating: mean shift and the within-item-type slope of exp_u on the optimal move, for each item type and source; the walk shift;
- the paraphrase difference and, for R2, the order effect (paraphrases 0 and 1 list the options in opposite orders);
- for R0: the difference from the stored stage-B outputs (max abs probability difference, SD of the exp_u difference).
