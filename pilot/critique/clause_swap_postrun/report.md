# Blind post-run coding of the clause-swap texts (R4)

(Saved verbatim from the blind coder's hand-back message. Scripts and tables are in `work/`.)

No model was run. I did not open `clause_swap_sampled.*` or `repro_check.*`, did not read the "CS Part A result" section of `LADDER.md`, did not run `score_reasoning.py`, and changed no tracked file. (`git status` shows `clause_swap_sampled.*` as modified. That is the Part B run writing to it, not me.) All my files are in `pilot/critique/clause_swap_postrun/work/`.

## Verdict

1. **The coding supports the clause hypothesis in both framings.** Upper-bound misreadings (LE), unsettled readings (AMB) and cut-offs that stop mid-debate over the clause occur in both C1 ("reaches c") cells under both wordings. They are absent from all 60 C0 ("at or above c") L2 texts.
   - Third person: LE+AMB is 0 / 3 / 0 / 3 and ambiguity cut-offs are 0 / 2 / 0 / 3 (W0C0 / W0C1 / W1C0 / W1C1).
   - Second person: LE+AMB is 0 / 5 / 0 / 11 and ambiguity cut-offs are 0 / 1 / 0 / 1.
   - Pooled, LE+AMB is 22 of 60 C1 texts against 0 of 60 C0 texts (Fisher p = 4e-8). Ambiguity cut-offs are 7 of 60 against 0 of 60 (p = 0.013).
2. **The wording hypothesis is not supported for misreading.** Under W1 with the plain clause (W1C0), no text in either framing adopts or ends on an upper bound.
3. **In the third person, the wording carries a different failure that the pre-registered codes do not measure: running out of tokens.**
   - W1 texts are cut at 512 tokens in 12 of 30 cases, against 4 of 30 for W0 (p = 0.04).
   - W1C0 has 5 cut-offs. None is debating the clause when cut, and 2 of them stop one word before the answer.
   - The third-person drop in correct L2 answers (14 / 11 / 9 / 7 of 15) is therefore larger along W than along C. The misreading signal goes with C, but the token cost goes with W.
   - A reading by counts that blames the wording in the third person is about verbosity, not about understanding the rule.
4. **In the second person, the clause is enough to cause misreading, and W1 makes it worse.**
   - LE+AMB is 11 of 15 under W1C1 against 5 of 15 under W0C1 (p = 0.07).
   - W1 alone does nothing: W1C0 scores 15 of 15 correct with no LE.
5. **Correct for the wrong reason.** In L2 this happens only in the second person:
   - 4 of the 8 correct answers in W1C1: (2,1), (6,5), (10,7), (18,7);
   - 1 of 10 in W0C1: (18,9);
   - 1 of 12 in W0C0: (2,1), where the wrong objective is harmless because v = 2.

   Counting only answers backed by a correct reading of the rule, the second-person cells score 11 / 9 / 15 / 4 rather than 12 / 10 / 15 / 8. No third-person L2 text is correct for the wrong reason.
6. **The "highest price" objective comes from the second-person framing, not from the clause or the wording.**
   - It is stated in 10 to 11 of 15 texts in every second-person L2 cell, mostly in the opening sentence, and usually dropped in favour of minimising P.
   - It decides the answer in 3 / 1 / 0 / 4 second-person texts and in 0 / 0 / 1 / 1 third-person texts (W0C0 / W0C1 / W1C0 / W1C1).
7. **L1: no text misreads the rule.** Every L1 text restates it correctly (3 waver, 5 do not mention it).
   - All 4 finished L1 errors are "highest price" answers of 9.
   - Where "highest price" is adopted (decisive or self-corrected), it follows C1 in the second person (W0C1 4 texts, W1C1 2, both C0 cells 0) and W1 in the third person (W1C0 1, W1C1 2, both W0 cells 0). With n = 5 per cell this is only descriptive.
8. **My codes agree with the previous coder's on 57 of the 60 reused (W0C0, W1C1) texts.** The 3 disagreements are all third-person W1C1 cut-offs on the GE\*/AMB/LE boundary. None crosses a C0/C1 line, so none affects the test.

## Method

- `collect.py` pooled the 160 rows: RL with 15 rows; RL2 with para 0 as W0C0 and para 1 as W1C1; CS with `wording` and `clause`.
- It shuffled them with a fixed seed, gave them opaque ids (T000 to T159), and wrote `dump_L2.txt` and `dump_L1.txt`. These show only v, c, token count, cut flag and written answer above each raw text.
- I read all 120 L2 texts and all 40 L1 texts in full, in that shuffled order. I wrote `codes_L2.tsv` and `codes_L1.tsv` before joining them to the cell key (`items.json`, which I did not open while coding).
- `analyze.py` then joined codes to cells, giving `table_L2.tsv` and `table_L1.tsv`: cell, v, c, target, answer, tokens, cut, correct, codes, flags, id and a short quote.
- A mechanical check confirms the labels: "reach" appears in 44 of 60 C1 texts and 0 of 60 C0 texts; "at or above" appears in 37 of 60 C0 texts and 0 of 60 C1 texts.

**What I could and could not blind.**
- The clause cannot be hidden, because texts quote it. Framing is visible ("I" against "Anya").
- W was partly visible. All 30 third-person W1 texts open with "To determine the best price Anya should propose…". No opening is unique to second-person W1.
- I had read the previous review, which reports codes for W0C0 and W1C1, before coding. I looked at its per-text codes (`reasoning_postrun/work/classify.py`) only after my coding was complete.
- There was a single coder.

**Codes.**
- Acceptance condition, as in the previous review:
  - **GE**: states the correct floor and keeps it.
  - **GE\***: settles on ≥ only after weighing ≤ (or an equivalent upper bound).
  - **LE**: adopts "P ≤ c" or "up to c".
  - **AMB**: deliberates or flips and never settles.
- **HP**, the "highest price" objective:
  - **N**: absent.
  - **S**: stated (usually "find the highest price Aiden will accept…") or a slip in the conclusion, while the decision is made by minimising P.
  - **C**: acted on, then self-corrected.
  - **D**: decides the answer.
- **Cut-offs**:
  - **D**: debating the clause's meaning when cut ("ambiguous", "re-read", Interpretation A/B).
  - **E**: debated the clause earlier, but was past it (tabulating) when cut.
  - **O**: wavering about something else when cut (the objective, or walking away against a rejected offer).
  - **N**: no debate; just ran out of tokens.
- **CWR** (correct for the wrong reason): a correct finished answer reached through LE or AMB, or through HP = D.

## L2: counts per framing and cell (15 texts each)

| Cell | Correct | Walk ok /4 | Cut | GE | GE\* | AMB | LE | HP S / C / D | Cut-offs D / E / O / N | CWR | Mean tokens |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 3p W0C0 | 14 | 3 | 1 | 15 | 0 | 0 | 0 | 0 / 0 / 0 | 0 / 0 / 0 / 1 | 0 | 288 |
| 3p W0C1 | 11 | 1 | 3 | 12 | 0 | 2 | 1 | 1 / 0 / 0 | 2 / 0 / 0 / 1 | 0 | 366 |
| 3p W1C0 | 9 | 2 | 5 | 15 | 0 | 0 | 0 | 1 / 0 / 1 | 0 / 1 / 1 / 3 | 0 | 441 |
| 3p W1C1 | 7 | 0 | 7 | 8 | 4 | 1 | 2 | 2 / 0 / 1 | 3 / 2 / 1 / 1 | 0 | 467 |
| 2p W0C0 | 12 | 4 | 2 | 15 | 0 | 0 | 0 | 7 / 1 / 3 | 0 / 0 / 1 / 1 | 1 | 314 |
| 2p W0C1 | 10 | 1 | 1 | 9 | 1 | 0 | 5 | 9 / 0 / 1 | 1 / 0 / 0 / 0 | 1 | 292 |
| 2p W1C0 | 15 | 4 | 0 | 14 | 1 | 0 | 0 | 9 / 2 / 0 | – | 0 | 257 |
| 2p W1C1 | 8 | 1 | 1 | 4 | 0 | 2 | 9 | 6 / 0 / 4 | 1 / 0 / 0 / 0 | 4 | 294 |

The correct counts for the two reused cells match the RL2 figures (third person 14 and 7, second person 12 and 8).

### Non-GE texts, errors and cut-offs per cell, as (v, c) → answer

**3p W0C0.** All 15 texts are GE. The only miss is (6,7), cut while writing a correct walk-away argument (N).

**3p W0C1.**
- AMB, cut mid-debate: (2,9) "This phrasing is slightly ambiguous … Interpretation B: … P ≤ 9"; (6,9), which leans to ≥ but is still conditional when cut.
- LE: (14,9) → 1, "he is willing to sell it for 9 or less".
- Also cut: (2,3), a GE text that ran out while listing losses.

**3p W1C0.** All 15 texts are GE.
- Wrong among finished texts: (10,7) → 9, HP-D: "choose the highest possible price that still allows her to make a profit, which is 9".
- Cut-offs:
  - (2,1): N, a two-sided payoff analysis ending at "Conclusion: An".
  - (2,3): O, weighing walking away (0) against proposing a price that will be rejected.
  - (6,9): E. It re-reads "at or above 9" and never considers ≤.
  - (18,3): N, cut at "The lowest acceptable price is".
  - (18,9): N, cut at "the optimal strategy is to propose".

**3p W1C1.**
- GE\*: (2,3), (2,9), (6,5), (6,9), all cut.
- AMB: (6,7). It adopts "P ≤ 7" and reasons to 1, then "**Wait, let's re-read carefully** … slightly ambiguous" at the cut. The previous coder coded it LE.
- LE: (10,7) → 1; (18,3), cut while the objective is unsettled ("Is there a reason to bid lower?").
- Also cut: (14,9), GE (N).

**2p W0C0.** All 15 texts are GE.
- HP-D: (14,9) → 13 ("the highest price I can pay is 13"); (18,9), cut after "the highest price I can offer is 17", which the price cap brings back to 9; (2,1) → 1 (CWR, harmless at v = 2).
- (6,3): cut (O) while correcting its own "offer 6".

**2p W0C1.**
- LE: (2,3) → 1, (2,9) → 1, (6,5) → 1, (14,9) → 1, and (18,9) → 9 (CWR: "offer the highest possible price … The maximum price he accepts is 9").
- (2,9) gets there through explicit doubt: "likely a translation quirk for 'accepts any price up to 9'".
- GE\*: (6,9), cut mid-debate (D).

**2p W1C0.** 15 of 15 correct.
- GE\*: (6,3). While chasing the highest price it writes "7, 8, or 9: Aiden rejects (price > 3)", then "Wait, let me re-read the constraint carefully" and settles on 3. This is the only ≤-type statement in any C0 L2 text that touches the decision, and it is self-corrected.
- HP-C: (10,7) offers 9 at first, then corrects itself to 7.

**2p W1C1.**
- LE: (2,1) → 1 (CWR), (2,3) → 1, (6,5) → 5 (CWR), (6,7) → 1, (10,3) → 1, (10,7) → 7 (CWR), (14,9) → 1, (18,3) → 1, (18,9) → 1.
- AMB: (6,9), cut mid-debate; (18,7) → 7 (CWR). That text holds both bounds at once: "P ≤ 7 … implying he has a floor of 7 … If I propose 8, 9, or higher, he rejects".

### The pre-registered test, per framing

| | Clause hypothesis: LE / AMB / ambiguity cut-offs present in both C1 cells, absent in both C0 cells | Wording hypothesis: they follow W1 | What the coding supports |
|---|---|---|---|
| Third person | Yes. W0C1 has 1 LE, 2 AMB and 2 D cut-offs; W1C1 has 2 LE, 1 AMB and 3 D cut-offs (4 GE\*). Both C0 cells have none. | No for these codes: W1C0 has none. | **The clause**, for misreading and ambiguity. Separately, W1 roughly triples cut-offs (W1 12 of 30, W0 4 of 30; W1C0 has 5 cut-offs with no clause debate). That is a wording-driven token-budget failure outside the R4 codes, and it explains most of the drop in correct answers along W. |
| Second person | Yes. W0C1 has 5 LE and 1 D cut-off (1 GE\*); W1C1 has 9 LE, 2 AMB and 1 D cut-off. Both C0 cells have no LE or AMB. | No: W1C0 is 15 of 15 correct with no LE or AMB. | **The clause**. W1 roughly doubles the clause effect (11 against 5 LE+AMB), an amplification or interaction that is not significant at n = 15. "Highest price" is a framing effect present in every second-person cell. |

Using the previous coder's three alternative codes for the third-person W1C1 texts (LE 3, AMB 2, GE\* 2) changes no row of this table.

## L1 (5 texts per cell)

| Cell | Correct | Cut | Rule restated: correct / wavers / not mentioned | HP S / C / D | Wrong or cut |
|---|---|---|---|---|---|
| 3p W0C0 | 5 | 0 | 4 / 0 / 1 | 0 / 0 / 0 | – |
| 3p W0C1 | 5 | 0 | 3 / 0 / 2 | 0 / 0 / 0 | – |
| 3p W1C0 | 4 | 1 | 4 / 1 / 0 | 1 / 1 / 0 | v=18 cut while reconsidering the rule (D): first "offer the highest possible amount to secure the deal", then "might imply he accepts *up to* a certain point" |
| 3p W1C1 | 3 | 1 | 4 / 1 / 0 | 1 / 0 / 2 | v=10 → 9 (HP-D); v=18 cut (E), past its doubt; v=2 → 1 is CWR ("offer the maximum possible price … This maximizes the chance of acceptance") |
| 2p W0C0 | 5 | 0 | 5 / 0 / 0 | 0 / 0 / 0 | – |
| 2p W0C1 | 4 | 0 | 5 / 0 / 0 | 0 / 2 / 2 | v=10 → 9 (HP-D); v=2 → 1 is CWR |
| 2p W1C0 | 5 | 0 | 4 / 1 / 0 | 0 / 0 / 0 | – |
| 2p W1C1 | 3 | 1 | 4 / 0 / 1 | 0 / 1 / 1 | v=14 → 9 (HP-D); v=18 cut (D) after self-correcting from 9 ("Is there any trick?") |

- No L1 text reads "any price at all" or "whatever price is offered" as a bound.
- The three wavering texts (all under W1) bring in a belief that higher offers are more likely to be accepted, or that rejection is still possible, despite the rule.
- Every L1 error is the "highest price" objective or a cut-off.

## What a careful skeptic should know

1. **The R4 codes miss the main third-person W1 failure.** In 3p W1C0, 5 of 15 texts are cut at 512 tokens, and none of them is debating the clause when cut. Two stop one word before the answer: (18,3) at "The lowest acceptable price is" and (18,9) at "…is to propose". Two more were plainly heading to the right answer: (2,1) at "Conclusion: An", and (6,9), tabulating correctly.

   The third-person W1 wording ("analyze the trade-off between the profit she makes and the risk of rejection", enumerating every price) costs about 150 extra tokens on average whatever the clause. A larger token budget would probably remove most of the third-person wording effect on correct counts but not the C1 misreadings. That is a guess; it was not tested.
2. **Correct counts overstate understanding in second-person C1 cells.** Misreading the clause as an upper bound combines with the "highest price" objective to land exactly on c. Half of second-person W1C1's correct answers are of this kind. In walk cells an LE reading gives 1, which is rejected and pays the same as walking, so it costs nothing; that also hides misreadings.
3. **LE is one stable template, not noise.** 12 of the 17 LE texts state it as "accepts any price that reaches c coins. This means he will accept any offer P where P ≤ c". Two LE texts first call the clause ambiguous and then choose ≤: (2,9) in 2p W0C1 and (6,7) in 3p W1C1. Some texts read "reaches" as "exactly c", for example (14,9) in 2p W1C1, "threshold is exactly 9 … P ≤ 9". At c = 9 the price cap makes ≥ 9 and = 9 the same, so several C1 cells with c = 9 cannot tell the two readings apart.
4. **A failure mode not covered by the codes: bounding the seller's acceptance by the buyer's resale value or by the price cap.**
   - Examples: "3 ≤ P ≤ 6", "7 or higher: Aiden rejects (since 7 > 6)", "accepts 1 ≤ P ≤ 2 … he won't accept more than he paid", "he only accepts ≤ 9 effectively".
   - It appears in about 12 L2 texts, almost all in the second person (C0 cells as well as C1).
   - In this game it changed no answer, because it never touches the floor. It would matter in a game where the buyer should pay above the seller's cost.
5. **"Highest price" usually stays words.** In the second person, "To maximize my profit, I need to find the highest price Aiden … will accept" opens 19 of 30 W0 texts and 21 of 30 W1 texts, and most of them then minimise P. The decisive cases are few: 3 / 1 / 0 / 4 in the second person and 2 in the third person (both W1). A keyword count of "highest price" therefore overstates the failure by about 3 times.
6. **A keyword count of "ambiguous / re-read / Wait" is not specific.** It hits 1 / 2 / 2 / 6 third-person and 1 / 2 / 2 / 1 second-person L2 texts. The C0 hits re-read the profit rule or the objective, not the clause. Only hand coding separates "debating the clause" (D, present only in C1) from the rest.
7. **There is one ≤-type slip under C0:** (6,3) in 2p W1C0, self-corrected (coded GE\*). Strictly, the clause hypothesis as pre-registered names only LE and AMB, and those are absent from C0. A skeptic may still count this slip against "C0 is clean".
8. **Stray objective failures:**
   - (2,3) in 3p W1C0 is cut while arguing whether walking away (0) beats proposing a price that will be rejected.
   - (10,7) in 3p W1C0 answers 9 under a plainly worded C0 clause, so the third-person W1 wording can trigger "highest price" without "reaches".
9. **Limits:**
   - n = 15 L2 and 5 L1 texts per cell, one context, greedy decoding, one coder.
   - Neither W nor the clause was hidden (see Method).
   - The R3 reproducibility check was not read, so differences between new and reused cells could include run drift.
   - The W1 amplification in the second person (p = 0.07) and the L1 patterns are descriptive only.

## Files

All in `/home/user/haggle-sycophancy/pilot/critique/clause_swap_postrun/work/`:
- `collect.py`: pools the rows and writes the shuffled dumps `dump_L1.txt` and `dump_L2.txt` and the key `items.json`.
- `codes_L2.tsv`, `codes_L1.tsv`: hand codes with one quote each, written before the join.
- `analyze.py`: joins codes and key, prints the tables above, and writes the per-text tables.
- `table_L2.tsv`, `table_L1.tsv`: per text, with cell, v, c, target, answer, tokens, cut, correct, codes, flags, id and quote.
