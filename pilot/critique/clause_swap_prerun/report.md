# Blind pre-run review: Addendum CS (clause-swap test)

(Saved verbatim from the blind pre-run critic's hand-back message. Its scripts are in work/.)

Reviewer did not run any model and did not open `pilot/out/clause_swap*.jsonl` or their logs. Checks used only prompt building, the tokenizer and the existing RL/RL2 rows. Scratch scripts are in `pilot/critique/clause_swap_prerun/work/`:
- `check_swap.py`: prompt identity and swap checks.
- `fake_scorer_test.py`: runs the scorer on synthetic CS rows written to a temporary folder, which was deleted afterwards.
- `threshold_sim.py`: a rough estimate of how often the threshold reading misclassifies.

## Verdict

1. **Implementation matches the protocol: yes.** Exactly the acceptance clause is swapped. All 80 prompts round-trip to the RL2 prompt byte for byte, and the user message and the kernel target are identical. The reused RL and RL2 rows match the prompts the current code builds (0 hash mismatches in 80). Decoding, token limit, token counting, cut-off and parsing are the same. The scorer assembles and reads the 2 x 2 correctly.
2. **The design can answer its question in principle**, because each swap cell is a minimal pair with an anchor. As scored, though, it has two structural weaknesses:
   - It reads absolute pass/fail at 17 of 20 when one anchor already sits at 17 (second person, W0C0). In that framing a pure clause effect would be read as "both contribute" roughly a third of the time.
   - It pools two different clause manipulations (L1 and L2).
3. **The reading is fixed, committed and not tunable after the fact.** It is fragile and mis-scoped, though, and should be strengthened now. The run need not restart, because every recommended Part A change is to the scorer or adds rows.
4. **Part B is mostly correct** (seeding, batching and prompts are right). Token counts are off by one against Part A. Sampled text after `<|im_end|>` is not truncated, which can inflate cut-offs. Some reported statistics are under-specified. Fix this before Part B starts: `run_queue4.sh` launches it as soon as Part A ends, about 2.3 h after the 16:38 start.

## 1. Does the implementation do what the protocol says?

**Swap (`pilot/clause_swap.py` lines 21-33, 36-49).**
- `swap()` asserts that the clause occurs exactly once in the system message and replaces it.
- `check_swap.py` confirms, for all 80 prompts:
  - Undoing the swap restores the RL2 system message exactly.
  - The user message, which includes the reasoning instruction `ASK`, is identical to RL2's.
  - The inserted clause is the one that occurs in the other paraphrase's prompt.
  - The targets are unchanged.
  - The cell sets per (framing, W) are identical to RL2's 20 cells.
- `c = 1` gets "1 coin" in both clauses (cell (2, 1)).
- The swapped sentences read naturally in both wordings. For example: "Aiden Riversong paid 3 coins for the fruit and accepts any price that reaches 3 coins." and "Anya Blossomwood knows this about Aiden Riversong: … accepts any price at or above 3 coins." No naturalness confound was found.

**Comparability with the reused cells.**
- Context 0, the same `ASK`, greedy with `repetition_penalty=1.0`, `MAX_NEW=512`, the same interpreter and venv (`run_queue4.sh`, as in `run_queue2.sh`), torch 2.15 and transformers 5.23 installed before RL2, and the same `Reader`.
- Token count: Part A uses `ids.shape[0]` and RL2 uses `o.shape[1]-x.shape[1]`, which are the same quantity.
- Cut-off is `n_new >= MAX_NEW` in both, and the answer regex is identical (`clause_swap.py` line 53; `reason_ladder2.py` line 77).
- What CS drops is RL2's forced "Answer:" reading. It is not used by the rule.
- The stored RL2 hash (from `ladder.build`) excludes the instruction, while the CS hash includes it. The protocol says so, and it does no harm.
- One assumption is untested: that greedy generation in this run is bitwise reproducible against the RL/RL2 runs. RL and RL2 share no prompt, so there is no existing evidence of reproducibility. Without it, a difference between new and reused cells could in principle be run drift (thread count, numerics). See R3.

**Stopping and token counting (verified with the tokenizer).**
- The generation EOS is `<|endoftext|>` (248044), from `text_config`; there is no `generation_config.json`. The tokenizer's EOS is `<|im_end|>` (248046) and its pad is `<|endoftext|>`.
- Greedy texts end in `<|im_end|>\n<|endoftext|>`: `n_new` equals the re-tokenized raw text plus exactly those 3 tokens in all 53 finished RL2 rows.
- This is identical for RL2 and Part A, so it does no harm there. It matters for Part B (section 4).

**Scorer (`pilot/score_reasoning.py` lines 47-73).**
- (W0,C0) is RL plus RL2 third-person paraphrase 0 (15 + 5 rows), or RL2 second-person paraphrase 0. (W1,C1) is RL2 paraphrase 1. Swap cells are filtered by `wording` and `clause`. Every cell is checked to hold 20 rows.
- The mapping `(p10, p01)` gives the four outcomes as LADDER specifies. On synthetic rows ("W1C0 all correct, W0C1 all wrong") the scorer prints "the clause" for both framings.
- Clause effect and wording effect follow the protocol's definitions.
- Small points:
  - A cut row that contains a parsed answer would be scored on that answer. RL2's text says cut-offs count as wrong. No existing row has both, so this is moot unless it occurs.
  - The interaction term is not printed.

## 2. Can the design answer its question? Confounds and blind spots

Anchors from the existing rows (correct of 20; L1 of 5 and L2 of 15 in parentheses):

| | W0C0 | W1C1 |
|---|---|---|
| third person | 19 (5 + 14), walk 3/4 | 10 (3 + 7), walk 0/4, 8 cut |
| second person | **17** (5 + 12), walk 4/4 | 11 (3 + 8), walk 1/4 |

**B1. The absolute threshold makes the second-person reading close to a coin flip.**
- Under "clause only", (W1,C0) should look like W0C0. In the second person that is 17/20, exactly at the bar. Under "wording only", (W0,C1) should also look like W0C0.
- So in that framing a single extra error turns either clean hypothesis into "both contribute".
- Rough binomial heuristic (`threshold_sim.py`): if the true rate is 0.85, P(at least 17/20) = 0.65. P(reading = "the clause" | clause only) is about 0.64 in the second person and about 0.98 in the third.
- If the two factors share the effect, both swap cells sit near 14/20, and "both fail" follows with probability 0.7 to 0.8.
- The categorical reading is therefore biased toward "both contribute" in the second person.

**B2. L1 and L2 are different manipulations pooled under one rule.**
- Only L2's clause contains "reaches". L1 swaps "any price at all" for "whatever price is offered".
- W1C1's L1 errors are 2 per framing. In each framing, one is the "highest price" objective (answer 9) and one is a cut-off at v = 18 that the prior review judged was heading to the right answer.
- If those 2 errors persist in (W1,C0) because of the wording, that cell passes only with at most 1 L2 error. The second-person W0C0 anchor itself has 3 L2 errors.
- So "the clause carries the L2 failure" plus "the wording carries the L1 failure" is read as "both contribute". That is technically true, but it does not answer the "reaches" question. The scorer prints L1 and L2 separately, but the fixed reading uses only the pooled cell.

**B3. Correctness can hide the clause effect in the second person.**
- The prior review found that the upper-bound misreading ("≤ c") combines with the "highest price" objective ("max price accepted"). Together they give the target c in trade cells: 3 of the 11 correct answers in second-person W1C1 were correct for the wrong reason.
- Only the 4 walk cells discriminate there. A (W0,C1) cell in the second person can therefore score well despite misreading the rule, which pushes toward "the rest of the wording" or "interaction".
- The planned post-run coding is the only guard. It is not tied to the reading.

**B4. The failure-mode mapping in the protocol does not match the prior review.**
- LADDER says the first two modes "may come from the acceptance clause, the third from the rest of the wording". The review found "highest price" in 11/15 second-person **W0** L2 texts and 10/15 second-person W1, against 0/15 and 2/15 in the third person. In L2 it is mainly a second-person effect present under both wordings, not a W1 effect. Only in L1 (3/5 and 2/5 in W1, 0 in W0) does it go with W1.
- Also, the third-person W1C1 failure is mostly cut-offs (8), not misreadings (3 LE). The clause and token-budget hypotheses predict different things for C1 cells: longer texts and more AMB codes versus more LE codes.

**B5. Regression to the mean and one context.**
- The 2 x 2 was built after the anchors were seen to fail, and each anchor is one greedy draw per cell in one context. If W1C1's 10 to 11 was partly a chance low, both swap cells will look better, which favours "both pass (interaction)", the outcome most exposed to this.
- Greedy reruns cannot give a fresh draw. Only a nuisance change (contexts 1 and 2 exist) can.

**B6. Other limits, correctly stated or minor.**
- n = 20 per cell. Greedy single answers, so "noise" is sensitivity to nuisance wording, not sampling noise. Part B does not measure that (section 4).
- If the wording is the cause, it is still a bundle: persona, aim, price line, lead-in, payoff, greeting, question and the "Reply with…" instruction. A further split would be needed.
- The answer regex takes the first `Answer:` match. No existing row has two `Answer:` occurrences, but nothing flags it if one appears.
- Coding blind to the clause is impossible, because texts quote "reaches". Coding blind to W is partly possible.

## 3. Is the fixed reading sound and untunable?

- **Untunable: yes.** The rule, the mapping and the scorer were committed in 304dfcb before any CS data. The anchors are fixed.
- **Sound: partly.** Its four outcomes are logically right for the 2 x 2. Its operationalization is fragile in the second person (B1) and mis-scoped for the "reaches" question (B2, B3).
- **Missing from the report:**
  - The interaction term.
  - Paired, per-cell flips for each minimal pair. The same 20 cells appear in all four conditions, so a paired comparison is the natural test.
  - A sensitivity statement: how many answers would have to change to flip the reading.
  - Cut-off and "wrong among finished" counts split by cell inside the effect summary.
  - A per-cell table of the 20 cells by 4 conditions, for the post-run reviewer.

## 4. Part B (sampled)

- **Prompts are correct.** All 40 are identical to the RL/RL2 W0C0 prompts (`check_swap.py`).
- **Seeding is correct and safe to resume.** `torch.manual_seed(SEED + i)` (line 79) uses the absolute prompt index `i`, which survives resume. The three samples come from one RNG stream in one batch, so they are independent draws. They are reproducible at a fixed thread count.
- **Batching is correct.**
  - Inputs are `x.repeat(3, 1)`, so there is no input padding and the attention mask is all ones. The prompt contains no 248044 token.
  - Finished rows are padded with `pad_token_id`. That is None in the config, so transformers sets it to EOS, which is 248044.
- **Token count is off by one (line 90).** Counting `ids != tok.pad_token_id` (248044) also drops the final `<|endoftext|>`, which greedy counts. So sampled `n_new` is greedy-style minus 1 for finished rows. A row that ends at exactly token 512 is "cut" under A and not under B. This is negligible in size, but the token comparison with greedy is not like for like.
- **Text after `<|im_end|>` is sampled (more important).** Greedy always emits `\n<|endoftext|>` after `<|im_end|>`. At temperature 0.7 a sample can instead continue: for example `<|im_start|>`, then an invented next turn. That inflates `n_new`, can mark an answered sample as `cut_off`, and leaves extra text in `raw` (special tokens are stripped, the words are not).
- **Statistics (`score_reasoning.py` lines 74-91).**
  - "Correct rate per sample" is reported only pooled (x/60). There is no per-sample-index x/20 or walk x/4, so the RL2 rule cannot be applied to each sample.
  - "All 3 agree" counts three `None` answers (cut-offs) as agreement.
  - "Majority = greedy" counts prompts with no majority as mismatches without reporting them, and counts `None == None` as a match.
- **What Part B measures.** It is sampling variability at the passing W0C0 cell only. It says nothing about the swap cells, about W1C1, or about the wording sensitivity that drives Part A. The write-up should say so, and Part B must not be used to re-read Part A.

## Recommended changes before the data are read

None of the required changes alters a Part A prompt, so the rows already being written stay valid.

**Required**

- **R1. Add a sensitivity flag and a paired reading to the scorer, and state both in LADDER.** Keep the four-outcome reading as primary. Additionally:
  - Print, per framing, the flips cell by cell for both minimal pairs: W0C0 against W0C1 (clause in W0) and W1C1 against W1C0 (clause in W1). Give the exact McNemar (sign-test) p for each, and pooled over the two framings (40 pairs).
  - Label the categorical reading **fragile** if changing one answer, or one walk cell, in either swap cell would change it. With the second-person anchor at 17, a fragile reading must be reported as inconclusive at n = 20, not as a finding.
- **R2. Give the "reaches" question its own L2-only reading.**
  - Apply the same four outcomes to the 15 L2 cells, at a pass of at least 13 of 15 with walk at least 3 of 4. This is the same 85% bar as 17 of 20. For reference, the anchors at that bar are third person 14 (pass) and 7, second person 12 (fail) and 8. The second-person W0C0 anchor fails it, so this reading is defined for the third person only, and the second person is reported descriptively. State this before data.
  - State that the pooled reading also mixes in the L1 clause swap, which is a different manipulation.
- **R3. Add a reproducibility check of the reused cells.** Before or after Part A, in the same environment, regenerate 4 to 6 RL/RL2 prompts. For example: third-person W1C1 at (6, 7) and (2, 9), second-person W0C0 at (14, 9), and one L1 cell. Write them to a separate file and report whether `raw` is byte-identical. This is about 10 minutes of CPU and is the only direct evidence that new and reused cells are comparable. If the texts differ, report it before interpreting the 2 x 2.
- **R4. Pre-register what the blind coding must show for each reading.** The coding uses the prior review's GE / GE\* / AMB / LE codes plus the "highest price" flag. Clause hypothesis: LE and AMB codes and the "ambiguous / re-read" cut-offs appear in C1 cells under both wordings and are absent in C0 cells. Wording hypothesis: they follow W1. Name the "correct for the wrong reason" cells (LE plus highest price) and report them alongside the correct counts. Also correct the LADDER sentence that assigns "highest price" to the rest of the wording. In L2 it is mainly second person under both wordings (B4).
- **R5 (Part B, before it starts).**
  - Truncate each sample at its first `<|im_end|>` (id 248046) for `raw`, parsing and `n_new`. Count `n_new` the way greedy does: tokens up to `<|im_end|>` plus 2, or report the convention used.
  - Optionally pass `eos_token_id=[248046, 248044]` to save compute. The content before `<|im_end|>` is unchanged.
  - If Part B has already started when this lands, apply the same truncation in the scorer instead.

**Optional**

- O1. Print the interaction term, `n00 - n01 - n10 + n11`, and the clause and wording effects computed separately on cut-offs and on wrong answers among finished texts. The clause and token-budget hypotheses predict different splits.
- O2. Print the 20 cells x 4 conditions table: written answer, tokens, cut.
- O3. Part B statistics:
  - per-sample-index correct x/20 and walk x/4, with the RL2 rule applied to each sample;
  - the distribution of prompts by 0 to 3 correct samples;
  - agreement among parsed answers only;
  - the count of prompts with no majority;
  - `None` excluded from "majority = greedy".
- O4. Extend Part B to the 40 W1C1 prompts, or state plainly that sampling noise is measured only at a passing cell.
- O5. Replicate the full 2 x 2 in context 1 (160 prompts, about 4.7 h). This addresses one context and regression to the mean (B5) and gives a fresh draw of the anchors.
- O6. Make `clause_swap.py` check stored row hashes on resume, as `ladder.py` does. Today it resumes by line count, so a changed prompt list would misalign rows without any warning. Also flag rows with more than one `Answer:` match.
- O7. If any cut row has a parsed answer, score it as wrong, as RL2's text says (scorer line 14), or report it.
