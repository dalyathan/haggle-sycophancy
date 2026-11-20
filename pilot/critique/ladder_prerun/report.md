# Pre-run review of the game ladder (LADDER.md, ladder.py, analyze_ladder.py)

(Saved verbatim from the blind pre-run critic's hand-back message. Its scripts are in work/.)

No model was run. I built every rung's prompts, read both paraphrases with and without history, and pushed synthetic policies through `analyze_ladder.report`. Scripts are in `work/` (`dump.py`, `sim.py`, `extra.py`).

## Verdict

The code is sound: I found no bug in prompt construction, kernel targets, payoffs, reading reuse or the L4/L4b path. The pass rules and the fixed interpretation are not ready. As written, the ladder can produce the pattern "passes L3, fails L4" or "fails L1, passes L2" from the thresholds alone. Fix the five blocking items first; all are cheap.

## Blocking

**B1. The rungs are not equally strict, so a pass/fail pattern across rungs is partly an artefact of the rule.**
I took the optimal policy mixed with a share of uniform noise and found the largest share that still passes:

| Rung | Largest passing noise share | Binding criterion |
|---|---|---|
| L1 | 0.16 | P4 (mass at or above the value) |
| L2 | 0.49 | P3 |
| L3 | 0.48 | P3 |
| L4b | 0.13 | A4 (regret below value-only, 0.296) |

- A buyer that plays every rung equally well with 20% to 45% noise gives "fail L1, pass L2, pass L3, fail L4".
- The protocol would read that as "the mixture is too much; simplify toward L3". It is only the stricter bar.
- Fix: judge all rungs on the same criteria at the same strictness (for example regret as a fraction of the uniform regret, and target mass). Either drop A2, A4-vs-value-only and A6 from the L4 verdict and report them, or add analogues to L1 to L3.

**B2. The L3 history criterion fails a zero-regret policy and is a coin flip otherwise.**
- After "1 was rejected" the L3 optima at v = 6, 10, 14 are the ties {3,4}, {5,6}, {7,8}. The no-history optima 3, 5, 7 stay optimal.
- A buyer that ignores the history has regret 0 and target mass 1.0, and fails P4 ("mean history effect above 0").
- The claim "the optimal policy passes every rung" holds only if ties are split; the lower-tie optimum fails L3.
- For a history-blind noisy model, "above 0" with no margin passes about half the time. The post-run review found the history effect flips sign with the paraphrase.
- Fix, either of:
  - Take the history out of the L3 pass rule and report it.
  - Use "2 was rejected": the optima become 4, 6, 8, an untied +1. Then require a positive effect in both paraphrases and a mean of at least 0.5.

**B3. L3 cannot tell "weighs an uncertain seller" from "offers half the value".**
- With cost uniform on 1..8 the optimum is half the value (1, 3, 5, 7, 8).
- The half-value rule scores target mass 0.8 and regret 0.2, with a slope of 1.1; it fails only on the broken history clause.
- A two-level step ("2 if v < 10, else 7; +1 after history") passes L3 outright.
- "Passes L3, fails L4" is therefore the expected signature of a half-value player, because L4's A4 is built to fail that rule.
- The fixed reading would then simplify the benchmark toward a game where a value-only heuristic is optimal.
- Fix: add a second cost distribution where the optimum leaves v/2. Cost uniform on 1..4 gives optima 1, 3, 4, 4, 4. Require the offers to differ between the two distributions at v = 14 and 18. That is 30 to 60 more prompts. Otherwise reword the L3 interpretation.

**B4. L2 is passable without comparing the cost with the value.**
- "Copy the stated cost, walk iff v = 2" passes all of P1 to P4 (walk mass 0.667, regret 0.2). So does "copy, walk iff v ≤ 6".
- Only v = 6 has cells on both sides of the comparison; v = 2 always walks and v = 10, 14, 18 never do.
- The model is known to copy price-like numbers and to walk more at v = 2, so this false pass is plausible.
- Fix: add c = 1, so that v = 2 also has a trade cell. Require the within-value walk contrast (cost above minus cost below the value) to be at least 0.5 at both v = 2 and v = 6.
- Optional: a strict variant ("accepts only prices above c") makes the target c + 1, not a number in the prompt.
- P2 at 0.4 is also loose for a deterministic rung: "cost + 2, walk iff c > v" passes with target mass 0.45.

**B5. The interpretation table has gaps, and its strongest conclusion is confounded with the third person.**
- Undefined patterns: fail L1 with pass L2 (likely under B1), pass L1 with fail L2, and pass L4 with fail L3.
- "Fails L1 and L2: single-pass readouts are finished for this model" would be drawn from third-person prompts only. The post-run review named the third person as the one constant never varied, and L4b tests it only at the hardest rung.
- Fix: add second-person L1 and L2 (150 cheap prompts), or condition that conclusion on framing. Define the non-monotone patterns as "no conclusion; inspect".

## Non-blocking

**Confounds and missing rungs**
- L3 to L4 changes three things at once: the three-type mixture, the credibility paragraph (about 110 words, absent from L1 to L3), and the size of the history shift. LADDER.md says so, but a failure cannot name which one. One extra rung (L3 plus the credibility paragraph, or L4 without it) would split them.
- An L1 pass is weak evidence. "Always 1" passes, and 1 is a digit the instruction names and the R3 format prior favours. L1 is informative only as a failure, and then only if it is not the B1 strictness artefact.
- The L4 against L4b reading is pass/fail only. A drop in regret from 2.25 to 1.0 would read "both fail, no framing effect". Report the paired per-cell differences with the range over the six context-by-paraphrase sets.
- There are only two paraphrases, and the known paraphrase effect is 0.4 to 0.7 coins. Print the verdict per paraphrase and require the rung-specific criterion in both.
- Everything is conditional on the R3 format prior (mass on 0, 9, 1). In L2, 0 and 9 are targets in 9 of 20 cells. The reported "mass on the stated cost" helps; also report the mass on 0, 1 and 9 where they are not targets.

**Rung texts**
- I found nothing wrong or leading. Kernel beliefs match the wording in every rung.
- L4b is a faithful second-person transcription of both paraphrases, and its payoffs and targets equal the R3 rows exactly.
- In history cells the seller still says "Welcome." after rejecting an offer, and "She may make one more proposal" follows a sentence about the seller. Both are inherited from L4; keep them for comparability.
- L2 states the threshold twice ("paid c … at or above c"), which maximises copy salience; see B4.
- Where the cost exceeds the value in L2, a certainly-rejected lowball pays 0, the same as walking, but counts against P2 and P4. This is the kernel convention; report that mass separately.

**Code**
- `analyze_ladder.py` P3 prints the full uniform regret under the label "half the uniform guess". For L4 it shows 2.165 where the threshold is 1.083. The logic is right; the label misleads.
- LADDER.md quotes a uniform regret of 1.93 (uniform over nine offers), while P3 uses uniform over ten answers (2.165). State which.
- `ladder.py` defaults silently to L1 when the rung argument is missing or mistyped, for example "L4". Make it an error.
- `ladder.py` drops readout.py's start-up asserts that the walk tokens exist and that "Answer: walk" and "Answer: **5" tokenise as expected. With the same tokenizer this is harmless, but an empty walk list would silently read 0.
- Every ladder prompt has its own system message (the value and cost sit in it), so each batch is one prompt and the prefix cache gives no speed-up. The self-check compares the cached and full paths on two texts only. Expect it to run slower than the estimate; correctness is unaffected.
- The synthetic checks cited in LADDER.md are not in the materials. My reruns confirm them: optimal passes (with ties split), uniform fails every rung, copy-cost fails L2 on P4 only, always-5 fails every rung.
- Checked and fine:
  - `head()` cuts at the right marker for both paraphrases.
  - `RO.torch` and `RO.VARIANT = "R3"` are set before `read_answer`, so 0 counts as walking.
  - The three-position reading is indexed correctly.
  - `u0` is rebuilt as in readout.py.
  - The R3 file loads as L4 with 60 rows and reproduces regret 2.246, failing on P2, P3, A2, A4, A5 and A6.
  - L4b rows carry every field `acceptance` needs.
  - Hashes are unique, and resume and dry-run are safe.

## What would mislead if run as is

1. "Passes L3, fails L4" read as "the game is too hard", when it follows from B1 and B3.
2. "Passes L2" read as "follows stated rules", when it is copying plus a value-only walk rule (B4).
3. "Fails L3" from the history clause alone, for a model with zero regret there (B2).
4. "Fails L1 and L2" read as the end of single-pass readouts, without a second-person L1 or L2 (B5).

With B1 to B5 fixed, about 200 to 250 extra prompts, the ladder does separate "cannot follow a deterministic rule in one step" from "cannot handle this game", for this readout and scene frame. It will still not say which L4 ingredient breaks play without the extra intermediate rung.
