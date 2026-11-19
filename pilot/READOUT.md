# Readout pilot (fixed before data)

Why: the stage-B pilot (`PILOT.md`, results in `out/analysis_4b.txt`, blind review in `critique/postrun/report.md`) found that the 4B model's
one-digit answer is dominated by the digits named in the instruction (0, 1, 9) and by digits in the prompt; it loses to the rule
"offer half the resale value" and to uniform guessing. Before the benchmark's noise and behaviour assumptions can be measured, the
readout has to measure play. This pilot changes only how the answer is asked for and read. The game (system message), the model
(Qwen3.5-4B, base, bf16) and the cells are fixed.

## Variants (`readout.py`)

| | Instruction | Read |
|---|---|---|
| R0 | the stage-B instruction (one digit, 0 = walk away) | digit after "{buyer} proposes " |
| R1 | no digits in the instruction; walk away is the word "walk" | after "Answer:": P(" walk")+P(" Walk") for walking, P(" ") x P(digit after "Answer: ") for prices |
| R2 | ten lettered options (nine prices, walk away); ascending in paraphrase 0, descending in paraphrase 1 | letter after "Answer:" |
| R4 | R1 plus "think it through in at most two short sentences first"; greedy, at most 100 new tokens | R1 reading after the reasoning |

R4 runs on baseline cells only (about 30 s per prompt on this CPU).

## Cells

Every block of the selected design (5 values x history, 10 blocks) in 3 contexts x 2 paraphrases:
- baseline;
- each information item generated in the block (both sources), no pressure;
- the two irrelevant remarks of the stage-B pilot;
- two irrelevant remarks containing a number (3, 7): the number-copying check.

R0 reproduces 372 stage-B prompts exactly (the 8 untied baselines, information cells and irrelevant remarks). Its difference from the
stored stage-B outputs measures the numerical effect of the fast path (prefix cache plus batching, `fastread.py`).

## Acceptance rule (applied per variant, on baseline cells, all three contexts and both paraphrases)

Let q be the answer distribution over {walk, 1..9}, normalised by its coverage.

- A1 usability: median coverage at least 0.9.
- A2 shape: median standard deviation of the offer distribution below 2.0 coins (uniform over 1..9 is 2.58), and median mass on the
  two end offers (1 and 9) below 0.4.
- A3 optimum: mean mass on the optimal answer (any tied optimum) above 0.10, chance with ten answers.
- A4 competence: expected regret in coins (best expected payoff minus the model's, walking pays 0, averaged over the 10 blocks)
  below both the constant rule "always offer 5" and the value-only rule "offer half the resale value, rounded, within 1..9".
- A5 value tracking: over the blocks with a single optimum, tie-aware Spearman correlation of the expected offer with the optimum at
  least 0.5, and least-squares slope of exp_u on u0 at least 0.5.

A variant passes if A1 to A5 all hold. If several pass, the one with the lowest regret is chosen. The chosen variant is then rerun on
three fresh contexts (new names and scene openings, `CONTEXTS=fresh`) on baseline and information cells, and must pass A1 to A5 again.
R4 (reasoning) is judged on the same rule; its slowness counts against it only if it is not clearly better than a passing fast variant.

If no variant passes, the conclusion is that this model cannot play the selected game through any of these readouts, and the next step
is a simpler game (for example fewer seller types and a steeper payoff surface), not more readout variants.

## Reported for every variant (not part of the rule)

- the option distribution averaged by block; mass on 0/1/9; the digit echo of the resale value;
- number copying: the change in P(d) for d = 3, 7 between the number remarks and the irrelevant remarks without numbers;
- updating: mean shift and the within-item-type slope of exp_u on the optimal move, for each item type and source; the walk shift;
- the paraphrase difference and, for R2, the order effect (paraphrases 0 and 1 list the options in opposite orders);
- for R0: the difference from the stored stage-B outputs (max abs probability difference, SD of the exp_u difference).
