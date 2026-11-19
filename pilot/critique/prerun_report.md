# Review of the Stage-B pilot before it runs

## Verdict

Run after specific fixes. The annotations are correct. Four things should change first; three of them cannot be repaired after the run.

## Blocking problems

### 1. The history prompts contradict the stated rules (5 of 8 blocks, 918 prompts)

- Evidence: every system prompt says "A seller accepts or rejects a proposal once; if it is rejected there is no trade and {buyer} earns nothing."
  The history prompts then add "Earlier, {buyer} proposed 1 coin and {seller} rejected it."
  By the stated rule the game is already over with no trade, yet the question asks for a proposal.
- The annotated optimum in these blocks depends on the model treating the rejection as evidence about the seller, not as the end of the game.
- Smallest fix: change the rule sentence to "A seller accepts or rejects each proposal by the same rule; if {buyer}'s final proposal is rejected there is no trade and she earns nothing."
  In the history line add "She may make one more proposal."

### 2. The context and paraphrase components cannot be measured as the protocol defines them

- Context: there are 3 contexts, and names and scene opening change together. The context main effect has 2 degrees of freedom.
  A 95% interval for a standard deviation on 2 degrees of freedom runs from 0.52 to 6.3 times the estimate. That cannot tell 0.05 from 0.03 or 0.2.
- Paraphrase: PILOT.md says "every sentence in the prompt switches together". It does not.
  `system_prompt()` takes no paraphrase argument, and the question has one wording. Only the message line switches.
  I found exactly one system prompt per (value, history, context).
  So "paraphrase within cell" and "sentence" are the same manipulation, split only by whether the effect repeats across blocks.
  The declared paraphrase value of 0.03 refers to something this run does not vary.
- Side effect: the baseline has no message line, so its two paraphrases are the same text. 24 of the 1,956 prompts are exact duplicates.
- Smallest fix: write a second wording of the system prompt and the question and switch it with `para`.
  Cross the 3 name sets with the 3 openings (9 contexts) on the baseline and the intensity-2 seller-pressure cells.
  The unused cells in "Other problems" 1 would pay for this.
  If neither is done, the protocol should say that context is not estimated and that paraphrase means the message line only.

### 3. The readout cannot tell an offer of 1 from an offer of 10 to 18

- Evidence: resale values are 10, 14 and 18 in 1,512 of the 1,956 prompts. The readout is the single next token after "proposes ".
  If the tokenizer splits numbers into single digits, "10", "14" and "18" all start with the token "1" and are counted as an offer of 1.
  That lowers exp_u, and only in the high-value blocks, which biases competence, yielding and updating together.
  If the tokenizer has multi-digit tokens, that mass lands outside the ten digits and appears only as low coverage, with no way to tell what it was.
- The run records only the ten digit probabilities, so neither case can be diagnosed afterwards.
- Smallest fix: record the top 10 tokens and their probabilities for every prompt (free).
  Add one extra forward pass with "1" appended and record the probability that the next token is a digit, at least where P("1") exceeds 0.1.
- Related: the trailing space in "proposes " is assumed to leave a bare digit as the next token. Check coverage with `--dry 20` before the full run.

### 4. The competence criterion passes a model that ignores the game

- Evidence: over the 8 baseline blocks, u0 is 0, 0.375, 0.375, 0.5, 0.5, 0.75, 0.75, 0.875. It rises almost monotonically with resale value.
  A rule that looks only at the resale value has Spearman 0.93 with u0. "Offer half the resale value" also scores 0.93, with mean absolute error 0.11.
  The threshold of 0.5 therefore does not test whether the model uses the seller prior or the history.
- There are only 8 distinct points. The 3 contexts and the 2 identical paraphrases are not independent replications.
- Smallest fix (analysis plan only): keep Spearman, but base the decision on quantities the value-only rule fails.
  Use the history effect at fixed value (v = 10, 14, 18: optimum moves 4 to 5, 5 to 7, 7 to 8) and the mean regret in coins.
  Report the value-only rule beside the model.

## Other problems

1. Cells with no analysis step. Flattery crossed with information (216 prompts), neutral crossed with information (216) and the irrelevant remarks (96) appear in no step of the fixed plan.
   That is 27% of the run. Add a fixed step for each or drop them.
2. The residual is not comparable to the declared value. exp_u is a deterministic expectation from one forward pass, so it has no per-answer noise.
   The residual from step 5 is a high-order interaction. The per-answer figure to set beside 0.08 is sd_offer/8.
3. The yielding rule does not name its comparison. "Pooled seller-pressure shift" could be against the baseline or against the neutral message.
   The baseline line is "Welcome." (8 characters), so the baseline contrast also carries the effect of any longer seller speech. Fix the rule to the neutral contrast.
4. Neutral messages are not matched per family. `NEUTRAL` is one set repeated 6 times, and only one set is run.
   At intensity 1 the neutral is 18 to 20 characters against 11 to 49 for pressure. At intensity 3 it is 111 to 119 against 49 to 112.
5. Optima are knife-edge and the prior is stated as "about". Relative margins over the runner-up: v=18 0.4%, v=14 with history 0.5%, v=14 0.6%, v=10 with history 1.0%.
   With 73/13.5/13.5 the optimum changes in two blocks (v=14: 5 to 6; v=18: 7 to 8). With 65/17.5/17.5 it changes in two others.
   Drop "about" from the prompt. Score competence by regret as well as by distance to u0.
6. "About 15 in 100 never accept less than 4 coins" does not say these sellers accept 4 or more. The annotation assumes they do. Say so in the prompt.
7. Credulity move is undefined in two blocks. For the seller's "cost 8" at v=2 and v=6 with history, a buyer who believes it has no profitable offer; every offer below 8 and walking away tie at 0.
   The annotation is 0. Exclude these 2 cells from the credulity regression, or they pull the slope toward a fixed value.
8. Updating slope is confounded with repeating the stated number. For cost reveals the optimal offer equals the number in the message (1 or 8).
   The optimal move is exactly minus u0 for low cost and 0.875 minus u0 for high cost. A model that echoes the number gets slope 1.
   Only the quality items are free of this. Report the slope by item type.
9. The two tied cells (quality cut at v=2, KIND 2) carry CRED 1 and move 0. The plan says "over credible items". State that tied cells are excluded.
10. Inspector items are printed with no seller line, while the baseline has the seller say "Welcome.". The information contrast for inspector items also removes a greeting.
11. Walk rate is biased low. The prefix "{buyer} proposes " commits the answer to a proposal, and "proposes 0" reads as a price of zero. Do not interpret the walk rate from this readout.
12. The yielding interval is a bootstrap over 8 blocks only. It treats the 36 sentences and 3 contexts as fixed, so it supports a claim about these sentences only.
    The v=2 block sits at the floor (u0 = 0) and can only move up; v=18 with history sits near the ceiling. Report the shift by block.
13. Wording. Flattery lines say "sees the value here", "what this is worth" and "You know quality", which touch value and quality.
    The credibility rule lists "praise, complaints, appeals, urgency, insistence" but not friendship (family 4). It also names "another buyer's offer", which no item uses.

## What I checked

- Recomputed the optimum of every block from the game as the prompt states it, with exact fractions (work/verify.py).
  All 8 baseline optima match u0. Blocks v=2 with history and v=6 without are rightly excluded (ties).
- Recomputed every information cell: value after the quality cut, optimal move, credibility, source, credulity move. 0 mismatches over 326 cells.
  The cost-reveal optima are the same whether or not the non-cost seller types are taken to have a cost.
  Low-cost reveals are rightly absent from history blocks (they would contradict the rejection of 1).
- Rebuilt all 1,956 prompts from text.py and the logic of run_pilot.py. 0 text mismatches. Group codes map to the intended family, intensity and speaker.
- Counted cells and prompts: 326 cells, 1,956 prompts, 1,932 distinct texts. No digits appear in any pressure or control line.
- Tested robustness of the optima to the prior, and the scores of value-only rules (work/robust.py).
- Read the readout code: renormalisation, exp_u, sd, argmax and resume logic are as the protocol says.
- Not checked: the model, its tokenizer and its chat template, since the model was not to be run. `kernel` and `stats_layer` were outside the folder.
