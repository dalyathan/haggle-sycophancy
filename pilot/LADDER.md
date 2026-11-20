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

## Rungs (`ladder.py`)

| Rung | Seller | Optimum | Cells |
|---|---|---|---|
| L1 | accepts any price | offer 1 | 5 values (30 prompts) |
| L2 | paid a stated cost c in {3, 5, 7, 9} and accepts any price at or above it | c if c < v; walk away if c > v | 5 values x 4 costs (120) |
| L3 | every seller paid a cost uniform on 1..8 and accepts at or above it; with and without the history (1 was rejected) | about half the value | 5 values x 2 (60) |
| L4 | the full selected game, third person | as v0.9 | existing readout R3 baseline rows (60) |
| L4b | the full selected game, second person ("You are a travelling merchant ... What price will you propose?") | as v0.9 | 5 values x 2 (60) |

Targets are the kernel's (`kernel.optimal`, `kernel.no_trade`): a set of offers that is certainly rejected means walking away; ties are
kept as sets. In L2 the cost is never equal to the value.

## Pass rule per rung (all prompts of the rung)

- P1: median coverage at least 0.9.
- P2: mean mass on the kernel target at least 0.4.
- P3: regret (mean over cells of best expected payoff minus the model's; walking pays 0) at most half that of a uniform guess over the
  ten answers, and below always-5.
- P4, rung-specific:
  - L1: mass on offers at or above the value, at v = 2 and 6, at most 0.1.
  - L2: mean walk mass in the cells where the cost exceeds the value at least 0.5, and slope of the cell-mean expected offer on the cost,
    in the cells where the cost is below the value, at least 0.5. (Copying the stated cost passes P1 to P3 and fails this.)
  - L3: slope of the cell-mean expected offer on the optimum (no history) at least 0.5, and mean history effect at v = 6, 10, 14 above 0.
  - L4, L4b: the readout rule's baseline criteria A2, A4, A5, A6 (`READOUT.md`), in addition to P1 to P3.

Synthetic checks before data (`analyze_ladder.py` on generated rows): the optimal policy passes every rung; uniform fails every rung;
"always offer the stated cost (or 5)" fails every rung, L2 on P4 only.

## Interpretation (fixed before data)

- Fails L1 and L2: the model cannot follow even deterministic acceptance rules in one step; single-pass readouts are finished for this
  model in this family of games. Next: the 9B, then reasoning on a GPU.
- Passes L1 and L2, fails L3: it follows stated rules but cannot weigh an uncertain seller in one step. A benchmark on this model in one
  step would need a deterministic or nearly deterministic seller.
- Passes L3, fails L4 and L4b: the three-type mixture, the history or the credibility rules are too much. The game should be simplified
  toward L3 and the design search rerun on the simplified family.
- L4b passes where L4 fails: the third-person framing is the obstacle; the benchmark should address the buyer as "you".
- Passing every rung: contradicts the readout pilot; check for a fault before anything else.

The ladder says nothing about yielding or updating (no messages), the 9B, or reasoning. Run order: L1, L2, L3, L4b (about 270 prompts,
roughly 10 minutes).
