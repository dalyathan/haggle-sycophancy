# Game ladder (fixed before data)

Why: the readout pilot (`READOUT.md`; blind review `critique/readout_postrun/report.md`) found that no single-pass readout makes
Qwen3.5-4B play the selected game: regret 2.2 to 2.5 coins against 0.30 for "offer half the value" and 1.93 for a uniform guess. The
game was held fixed, so the pilot cannot say whether the model cannot play in one step or the game is too hard. The ladder holds the
model and the readout fixed and varies the game, from trivial to the full one. Recommended by the blind post-run review.

## Fixed

Model Qwen3.5-4B (base, bf16, CPU, fast path of `fastread.py`). Readout R3 of the readout pilot: the stage-B instruction ("Answer with
one digit: 1 to 9 for a price in coins, or 0 to walk away without buying"), read after "Answer:" with the two-sequence reading (0 and
"walk" count as walking away). The stage-B system message up to the description of the sellers (premise, the buyer, prices 1 to 9,
the Concordia scene opening, the value, the companion); then the rung's seller description and the payoff sentence. Baseline prompts
only (the seller says "Welcome." / "Good morning."). Values 2, 6, 10, 14, 18; 3 contexts x 2 paraphrases.

## Revision history

- v1 (commit 8ed6b68): first version.
- v2 (this version, before any ladder data): revised after the blind pre-run review (`critique/ladder_prerun/report.md`): one rule at
  the same strictness for every rung (B1); history reported, not gated (B2); L3b added so that a half-value rule fails L3 (B3); cost 1
  added to L2 and a within-value walk contrast required (B4); second-person L1y and L2y added, undefined patterns read as "inspect" (B5);
  L3c added (L3 plus the credibility paragraph) to split L3 from L4; per-paraphrase results and mass on 0, 1, 9 reported; batching
  across prompts that share an opening.

- v2.1 (after L1 and L1y, before any other rung's data): the fast path's self-check failed on the first L2 batch (0.035 against the
  fixed limit 0.03; the L1 and L1y self-checks gave 0.023 and 0.010), which stopped the run before any L2 row was written. The limit
  is not changed; the remaining rungs (L2 onward) run on the exact path (`FULL=1`: one full forward pass per text, no cache, no
  batching), which is the reference the self-check compares against. L1 and L1y keep their fast-path rows.

## Rungs (`ladder.py`)

| Rung | Seller | Optimum | Prompts |
|---|---|---|---|
| L1 | accepts any price | offer 1 | 5 values (30) |
| L2 | paid a stated cost c in {1, 3, 5, 7, 9} and accepts any price at or above it | c if c < v; walk away if c > v | 5 x 5 (150) |
| L3 | every seller paid a cost uniform on 1..8 and accepts at or above it; with and without the history (1 was rejected) | 1, 3, 5, 7, 8 (with history: ties) | 5 x 2 (60) |
| L3b | as L3 with the cost uniform on 1..4; no history | 1, 3, 4, 4, 4 (not half the value) | 5 (30) |
| L3c | L3 plus the stage-B credibility paragraph | as L3 | 5 x 2 (60) |
| L4 | the full selected game, third person | as v0.9 | readout R3 baseline rows (60) |
| L4b | the full selected game, second person ("You are a travelling merchant ... What price will you propose?") | as v0.9 | 5 x 2 (60) |
| L1y, L2y | L1 and L2 in the second person | as L1, L2 | 30, 150 |

Targets are the kernel's (`kernel.optimal`, `kernel.no_trade`): a set of offers that is certainly rejected means walking away; ties are
kept as sets. In L2 the cost never equals the value.

## Pass rule (v2): the same for every rung

- P1: median coverage at least 0.9.
- P2: mean mass on the kernel target at least 0.5.
- P3: regret (mean over cells of best expected payoff minus the model's; walking pays 0) at most half that of a uniform guess over the
  ten answers (walk, 1..9), and below always-5.
- P4, a discrimination check only where a trivial rule would otherwise pass:
  - L2, L2y: the walk contrast (walk mass where the cost is above the value minus where it is below) at least 0.5 at both v = 2 and
    v = 6; and slope of the cell-mean expected offer on the cost, where the cost is below the value, at least 0.5. Copying the stated
    cost fails this.
  - L3: the expected offer with costs on 1..8 minus with costs on 1..4 (L3b) at least 1.5 coins at both v = 14 and v = 18 (optimal +3,
    +4). The half-value rule fails this.
- Reported, not gated: the history effect (L3, L3c); A2, A4, A5, A6 of the readout rule (L4, L4b); the paired regret difference L4b
  minus L4 with its range over the six context x paraphrase sets; per-paraphrase regret and target mass; the mass on 0, 1, 9 where
  they are not targets; for L2 the mass on the stated cost and on certainly rejected low offers where walking is optimal.

Strictness check before data (`analyze_ladder.py` on generated rows; the optimal policy mixed with a share of uniform noise): every rung
passes at 0.3; L4b fails at 0.4 and the others at 0.5, all at 0.6. Optimal (either tie), passes every rung; uniform fails every rung;
half-value fails L3 (P4), L1, L2, L3b; "copy the cost, walk iff v = 2" fails L2 (P4).

## Interpretation (fixed before data)

Framing: a conclusion "cannot do X in one step" needs the failure in both the third person and the second person where both exist
(L1 and L1y, L2 and L2y, L4 and L4b).

- Fails L1 and L2 (both framings): the model cannot follow even a stated acceptance rule in one step; single-pass readouts are finished
  for this model in this family of games. Next: the 9B, then reasoning on a GPU.
- Passes L1 and L2, fails L3: it follows stated rules but cannot weigh an uncertain seller in one step.
- Passes L3, fails L3c: the credibility paragraph alone breaks play.
- Passes L3 and L3c, fails L4 and L4b: the three-type mixture or the history is too much; simplify the game toward L3 and rerun the
  design search on the simplified family.
- Passes in the second person and fails in the third (any pair): the framing is the obstacle; the benchmark should address the buyer as
  "you".
- Any other pattern (for example fail L1 but pass L2, or pass L4 but fail L3): no conclusion; inspect the cells.

The ladder says nothing about yielding or updating (no messages), the 9B, or reasoning. Run order: L1, L1y, L2, L2y, L3, L3b, L3c, L4b
(570 prompts).

## Addendum RL: reasoning ladder (fixed before data; diagnostic only)

Written while L2y to L4b were running, after the L1, L1y and L2 results were known (all fail). The fixed reading of "fails L1 and L2"
names the 9B and then reasoning on a GPU as next steps. Neither is available here (no 9B weights, 8 GB of free disk, no GPU). RL is the
CPU-sized substitute: does the 4B play the two trivial rungs when it may reason first?

`reason_ladder.py`: L1 (5 values) and L2 at 10 (value, cost) cells: every value with a trade, and at v = 2 and v = 6 one trade cell and
two walk cells each; third person, context 0, paraphrase 0; the R3 instruction plus "First work it out briefly, then write Answer: followed
by one digit."; greedy, at most 512 new tokens. 15 prompts.

Reading (fixed): the model plays the trivial rungs with reasoning if its written answer equals the kernel target in at least 13 of
the 15 prompts, including walking away in at least 3 of the 4 cells where the cost exceeds the value. If it does, the benchmark's
readout has to be reasoning-based and the next step is L3 and the full game with reasoning (sampled, several answers per prompt) on a
GPU. If it does not, the 4B is not a usable subject for this family of games in any mode tested, and the spec's model range has to move
up (9B and larger) or the game has to change kind.

RL result (`out/reason_ladder.jsonl`): the written answer equals the target in 14 of 15 prompts and walking away is written in 3 of 4
walk cells (pass by the rule above); mean 288 generated tokens; the one miss, (6, 7), was cut off at 512. One context, one paraphrase,
third person, greedy.

## Addendum RL2: robustness of the reasoning ladder (fixed before its data; diagnostic only)

Written after 8 of the 15 RL prompts were known (all 8 correct, including both walk cells at v = 2) and after the blind post-run review
of the ladder (`critique/ladder_postrun/report.md`), which warned that one paraphrase in one framing can mislead either way.
`reason_ladder2.py`: the RL procedure on 20 cells (L1 at the five values; L2 at the 10 RL cells plus (6, 5), (10, 7), (14, 3), (14, 9),
(18, 3)) in four conditions: third person paraphrase 0 (the 5 new cells only, the rest is RL), third person paraphrase 1, second person
paraphrase 0, second person paraphrase 1. Context 0, greedy, at most 512 new tokens. 65 prompts.

Reading (fixed): in each of the four conditions (for third person paraphrase 0: RL plus the 5 new cells, 20 prompts), the written answer
equals the kernel target in at least 17 of 20 prompts and walking away is written in at least 3 of the 4 walk cells. The reasoning
readout is called robust on the trivial rungs only if all four conditions pass. Cut-off generations are counted as wrong and reported.
Greedy decoding and one context remain limits: a pass does not show stability under sampling.

RL2 result (`out/reason_ladder2.jsonl`; third person paraphrase 0 includes the 15 RL rows): **not robust; 2 of 4 conditions pass.**

| Condition | Correct (of 20) | Walk cells (of 4) | Cut at 512 | Mean tokens | Rule |
|---|---|---|---|---|---|
| third person, paraphrase 0 | 19 | 3 | 1 | 276 | pass |
| third person, paraphrase 1 | 10 | 0 | 8 | 452 | fail |
| second person, paraphrase 0 | 17 | 4 | 2 | 290 | pass |
| second person, paraphrase 1 | 11 | 1 | 2 | 289 | fail |

Correction (after the blind post-run review, `critique/reasoning_postrun/report.md`). The first version of this section blamed
paraphrase 1's "reaches c" wording and said the readout "plays the trivial rungs when the rule is stated plainly". It rested on an
unsaved keyword count that the review could not reproduce, and it softened a pre-registered failure after the fact. The review hand-coded
every text. What the texts show:
- Paraphrase matters and framing does not. Pooled, paraphrase 0 scores 36 of 40 and paraphrase 1 21 of 40 (Fisher p = 0.0004); third
  and second person score 29 and 28 of 40. Paraphrase 1 is a whole-prompt paraphrase (persona, aim, price line, payoff sentence,
  question and instruction all change), so no single sentence has been shown to cause the drop.
- Three failure modes, not one:
  - Misreading the rule as an upper bound ("accepts any P ≤ c"). This happens in 9 of 15 second-person and 3 of 15 third-person
    paraphrase-1 L2 texts, and in none in paraphrase 0. In 3 second-person cells it cancels against the next error and scores as correct.
  - Running out of tokens: 8 of 20 third-person paraphrase-1 generations are cut at 512, against 1 in paraphrase 0; 7 of the 8 are
    still debating whether "reaches" is ambiguous. Most third-person texts that finish read the rule correctly.
  - A wrong objective: "offer the highest price" the seller accepts. It appears in 11 of 15 second-person paraphrase-0 L2 texts and
    causes all 3 of that condition's failures. It also causes all four L1 paraphrase-1 failures, where the rule ("accepts whatever
    price is offered") is restated correctly.
- Walk-cell misses cost nothing (a certainly rejected offer pays what walking pays); the costly errors are offering 1 below the cost.
- n = 20 per condition with one context, greedy: 19 of 20 has a 95% interval of 0.76 to 0.99.

The pre-registered reading stands without qualification: the reasoning readout is not robust on the trivial rungs. The same "reaches
their cost" idiom is in paraphrase 1 of the selected game (`run_pilot.py`), used in stage B, R0 to R4 and L3, L3c, L4b; part of the
paraphrase effects measured there may be this sentence. The isolating test (swap only the acceptance clause between paraphrases),
more paraphrases and sampled answers are not yet run. The review's scoring scripts are in `critique/reasoning_postrun/work/`.

## Addendum TM: native thinking mode (fixed before its data; diagnostic only)

Every run so far set `enable_thinking=False`. `think_probe.py`: thinking mode on (the model writes its thinking, then the answer), second
person paraphrase 0, context 0, the plain R3 question, greedy, at most 1536 new tokens; 8 cells (L1y at v = 10, 18; L2y at (2, 1), (2, 3),
(6, 7), (10, 9), (14, 3), (18, 7)). Reading: the first digit or "walk" after the end of the thinking; thinking mode plays the trivial
rungs if that answer equals the target in at least 7 of 8, including both walk cells. Token counts are reported (they decide the cost
of a reasoning readout).

Run order after RL: R5 (queued earlier), RL2, TM.

TM result (`out/think_probe.jsonl`, scored by `score_reasoning.py`): **fail, 1 of 8.** 7 of 8 generations never close their thinking
within 1,536 tokens, so no answer is read; the one that does, L2y (10, 9), answers 9 (correct) after 738 tokens. The unfinished texts
repeatedly re-check a decision ("Wait, I should check if there's any hidden trap"): "Wait" occurs 6 to 12 times in each. Reported, not
part of the rule: in some cells the thinking states the target before the cut (for example "decision is 1" at L1y v = 18), but no
answer is written, so the rule scores it as missing. Thinking mode, greedy, is not a usable readout on this CPU: on the simplest rungs it
costs more than 1,536 tokens per item, against about 290 for the instructed reasoning in RL. Forcing the thinking to close at a budget
was not tested.

## Addendum CS: clause-swap test (fixed before its data; diagnostic only)

Why: RL2 passes paraphrase 0 and fails paraphrase 1 in both framings, but paraphrase 1 rewrites every sentence. The blind review
(`critique/reasoning_postrun/report.md`) found three failure modes: misreading the acceptance rule as an upper bound, running out of
tokens, and the objective "offer the highest price". The first two may come from the acceptance clause ("reaches c"), the third from
the rest of the wording. This test separates the two.

Part A (`clause_swap.py`): the same 20 cells as RL2 (L1 at v = 2, 6, 10, 14, 18; L2 at the 15 RL2 cells), context 0, both framings,
the RL2 procedure (reason first, greedy, at most 512 new tokens, the written answer). Only the seller's acceptance clause is swapped
between the two wordings:

| | Clause C0 | Clause C1 |
|---|---|---|
| L1 | "accepts any price at all." | "accepts whatever price is offered." |
| L2 | "accepts any price at or above c coins." | "accepts any price that reaches c coins." |

With W the rest of the wording, (W0, C0) and (W1, C1) are RL2's paraphrases 0 and 1 (third person W0 C0 includes the RL rows, as in
RL2). Part A runs (W0, C1) and (W1, C0): 2 framings x 2 x 20 = 80 prompts. The prompt hash now covers the final messages,
instruction included.

Reading (fixed), per framing, each 2 x 2 cell scored by the RL2 rule (written answer equals the target in at least 17 of 20, walking
away written in at least 3 of the 4 walk cells):
- (W1, C0) passes and (W0, C1) fails: **the clause** carries the paraphrase-1 failure.
- (W1, C0) fails and (W0, C1) passes: **the rest of the wording** carries it.
- Both fail: both contribute. Both pass: neither alone; the failure needs both (an interaction).

Reported, not part of the rule: correct counts for all four cells, with the clause effect (mean over W of C0 minus C1) and the wording
effect (mean over C of W0 minus W1), pooled and for L1 and L2 separately; cut-offs and mean tokens. After the run, a blind reviewer
codes every L2 text by how it states the acceptance condition and flags the "highest price" objective, with the codes of the previous
review.

Part B (`clause_swap.py` with `SAMPLE=1`), reported only: k = 3 sampled answers (temperature 0.7, top_p 0.8, top_k 20, the model's
recommended settings for non-thinking use; fixed seed) for the 40 (W0, C0) prompts, both framings. Reported: correct rate per sample,
the share of prompts on which all 3 samples agree, how often the samples' majority answer equals the greedy answer, tokens and
cut-offs. This is the first measure of per-answer noise under the reasoning readout. Part B runs after Part A. Scored by
`score_reasoning.py`.
