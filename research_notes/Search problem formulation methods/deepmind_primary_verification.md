# Primary-source verification: FunSearch, AlphaProof, AlphaGeometry (DeepMind)

Access notes (checked 2026-11-19): nature.com loaded through curl with a cookie jar, and deepmind.google loaded with plain curl. I opened the full open-access text of all three Nature papers, two Nature table pages and three DeepMind blog posts. I cross-checked against the AlphaGeometry2 arXiv HTML. Status tags: **[VERIFIED]** means I read the claim in the cited primary source. **[CORRECTED]** means the earlier note was wrong or imprecise, and the primary source says what follows. **[UNVERIFIED]** means I did not find the claim in any source I opened. The earlier notes (`llm_program_search.md`, `theorem_proving_search.md`) were not edited.

Primary sources opened:
- FunSearch: Romera-Paredes et al., "Mathematical discoveries from program search with large language models", Nature 625 (2024; online Dec 2023), https://www.nature.com/articles/s41586-023-06924-6. Its Table 1 is at https://www.nature.com/articles/s41586-023-06924-6/tables/1.
- FunSearch blog: https://deepmind.google/discover/blog/funsearch-making-new-discoveries-in-mathematical-sciences-using-large-language-models/
- AlphaProof: Hubert, Mehta et al., "Olympiad-level formal mathematical reasoning with reinforcement learning", Nature 651, 607–613 (2026; published online 12 Nov 2025; open access), https://www.nature.com/articles/s41586-025-09833-y. Its Table 1 is at https://www.nature.com/articles/s41586-025-09833-y/tables/1.
- IMO 2024 blog (July 25, 2024; updated with a note on Nov 12, 2025): https://deepmind.google/discover/blog/ai-solves-imo-problems-at-silver-medal-level/
- AlphaGeometry: Trinh et al., "Solving olympiad geometry without human demonstrations", Nature 625 (2024), https://www.nature.com/articles/s41586-023-06747-5. The correction at https://www.nature.com/articles/s41586-024-07115-7 only fixes a name in the Acknowledgements.
- AlphaGeometry blog: https://deepmind.google/discover/blog/alphageometry-an-olympiad-level-ai-system-for-geometry/
- AlphaGeometry2: https://arxiv.org/html/2502.03544

---

## Q1. FunSearch: problem formulation, evaluator, programs database/islands, prompts, LLM, samples/compute, results, limitations

### Takeaway
All the headline FunSearch claims flagged as UNVERIFIED are confirmed by the Nature paper:
- the 512-cap in n=8;
- Codey built on PaLM 2;
- a total of about 10^6 samples;
- bin-packing gains over first fit and best fit on OR-Library and Weibull instances;
- an evolved `priority` function inside a greedy skeleton.

Two small corrections. The paper states 10^6 as the *total* number of samples behind the results, not explicitly "per run". It also says 150 CPU evaluators, while the released config defaults to 140. The paper gives the n=8 cap set as its hardest case: only 4 of 140 runs found the 512-cap.

### Cited Findings
**Problem formulation / candidate representation**
- [VERIFIED] The target class is problems that are "'easy to evaluate', despite being typically 'hard to solve'". The goal is "to generate a 'solve' program, such that its outputs receive high scores from the 'evaluate' function (when executed on inputs of interest)". — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6)
- [VERIFIED] The input is "a specification of the problem in the form of an 'evaluate' function, an initial implementation of the function to evolve, which can be trivial, and potentially a skeleton". — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6)
- [VERIFIED] Skeleton rationale: "Whereas a fixed skeleton may constrain the space of programs that can be discovered, we find it improves overall results because it focuses the LLM resources on only evolving the critical part, instead of also using the LLM to recreate already known program structures (with more opportunities for mistakes that would render the entire program incorrect)." — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6)
- [VERIFIED] Cap set: the skeleton "starts with an empty set and iteratively adds the vector x ∈ Z_3^n with the highest priority that does not violate the cap set constraint". The function evolved is `priority`: Z_3^n → R, "Starting from a trivial constant function". — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6)
- [VERIFIED] Bin packing: "a heuristic [is] a program that takes as input an item and an array of bins (containing the remaining capacity of each bin) and returns a priority score for each bin. The 'solve' function picks the bin with the highest score". The function is called `heuristic`, and evolution starts "from best fit". — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6)

**Evaluator**
- [VERIFIED] Programs are "scored on a set of inputs" (for cap sets, the dimensions n; for bin packing, the instances). Scores "are then combined into an overall score of the program using an aggregation function, such as the mean". Programs "that did not execute within the imposed time and memory limits, or produced invalid outputs" are discarded. — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6)
- [VERIFIED] The evaluator "guards against confabulations and incorrect ideas". — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6)
- [VERIFIED] Sandboxing: "a sandbox for safely executing generated code on our internal distributed system [was] used" (Code availability). The sandbox was not released. — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6)
- Paper vs code discrepancy: the paper says the cluster score is "an aggregation (for example, mean) of all the scores in the signature". The earlier note found that the released `_reduce_score` uses the last test's score instead. — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6); [programs_database.py](https://raw.githubusercontent.com/google-deepmind/funsearch/main/implementation/programs_database.py) (as reported in llm_program_search.md; not re-opened here)

**Programs database / islands**
- [VERIFIED] "we split the population into m separate groups or islands. Each island is initialized with a copy of the user-provided initial program and is evolved separately". Programs generated from a prompt are "stored in the same island". — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6)
- [VERIFIED] Reset: "Every 4 h, we discard all the programs from the m/2 islands whose best instances have the lowest score". Each reset island is seeded with the highest-scoring program of a uniformly chosen surviving island ("breaking ties in favour of older programs"). — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6)
- [VERIFIED] Within an island, programs are clustered by "signature", the "tuple containing the program's scores on each of the inputs". The paper describes this as related to Lexicase and fitness uniform optimization. Clusters are sampled by Boltzmann selection P_i ∝ exp(s_i/T_cluster), with T_cluster = T_0(1 − (n mod N)/N). Within a cluster, shorter programs are favoured via exp(normalized negative length / T_program). — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6)

**Prompt construction**
- [VERIFIED] "best-shot prompting": sample k programs from one island, sort them by score, and rename them `priority_v0`, `priority_v1`, .... The header `priority_vk` is appended for the LLM to complete. "In practice, we set k = 2, as two functions lead to better results compared to just one, with diminishing returns beyond that." Functions that appear before `priority_v0` in the skeleton are removed from the prompt. — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6)

**LLM, sample count, compute**
- [VERIFIED] "We use Codey, an LLM built on top of the PaLM2 model family… fine-tuned on a large corpus of code and… publicly accessible through its API." The model was not fine-tuned on the problems. — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6). The blog says "FunSearch uses Google's PaLM 2". — [FunSearch blog](https://deepmind.google/discover/blog/funsearch-making-new-discoveries-in-mathematical-sciences-using-large-language-models/)
- [VERIFIED, with precision note] "we have chosen to work with a fast-inference model (rather than slower-inference, higher-quality), and the results in the paper are obtained using a total number of samples on the order of 10^6." Results "are not too sensitive to the exact choice of LLM, as long as it has been trained on a large enough corpus of code". StarCoder is the comparison in SI Appendix A. — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6)
- [CORRECTED] The earlier note had "about 10^6 samples per run". The paper's wording is "a total number of samples on the order of 10^6", which does not say "per run".
- [VERIFIED] Infrastructure: "we typically use 15 samplers and 150 CPU evaluators (can be served on five CPU servers each running 32 evaluators in parallel)". The released `config.py` defaults to `num_evaluators = 140` (per llm_program_search.md). — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6)
- [VERIFIED] Later update: the blog says that for the December 2024 competitive-programming follow-up, "we no longer require code-specialised models and can build on Gemini 1.5 Flash". — [FunSearch blog](https://deepmind.google/discover/blog/funsearch-making-new-discoveries-in-mathematical-sciences-using-large-language-models/)

**Results**
- [VERIFIED] "in dimension n = 8, FunSearch found a larger cap set than what was previously known… we do not just discover the set of 512 eight-dimensional vectors in itself, but a program that generates it". — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6)
- [VERIFIED] Robustness: "the case of cap set by direct construction in n = 8 dimensions is particularly challenging, with only four out of 140 experiments discovering a cap set of size 512". Admissible-set runs always beat the previous bound, and "60% of experiments on I(12,7) finding a full-size admissible set". — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6)
- [VERIFIED] Capacity lower bound: an I(12,7) admissible set raises the bound from 2.2180 to 2.2184. After humans noticed a symmetry in the evolved code, a restricted search found I(15,10) (C ≥ 2.219486) and a partial A(24,17) set of size 237,984, which gives C ≥ 2.2202. The paper calls this "the largest improvement in 20 years to the asymptotic lower bound". — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6)
- [VERIFIED] Bin packing, Table 1 (fraction of excess bins over the L2 lower bound; lower is better):

  | | OR1 | OR2 | OR3 | OR4 | Weibull 5k | Weibull 10k | Weibull 100k |
  |---|---|---|---|---|---|---|---|
  | First fit | 6.42% | 6.45% | 5.74% | 5.23% | 4.23% | 4.20% | 4.00% |
  | Best fit | 5.81% | 6.06% | 5.37% | 4.94% | 3.98% | 3.90% | 3.79% |
  | FunSearch | 5.30% | 4.19% | 3.11% | 2.47% | 0.68% | 0.32% | 0.03% |

  — [FunSearch Table 1](https://www.nature.com/articles/s41586-023-06924-6/tables/1)
- [VERIFIED] Train/test split: "We evolve our heuristic on a training set of generated bin packing instances with the same number of items as those in OR1 and, after the evolutionary process is concluded, test it on the OR1 to OR4 datasets." — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6)
- [VERIFIED] The paper places other problems in the SI: the corners problem and the Shannon capacity of cycle graphs (Appendix B). — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6)

**Stated limitations / scope**
- [VERIFIED] "FunSearch, at present, works best for problems having the following characteristics: (1) availability of an efficient evaluator; (2) a 'rich' scoring feedback quantifying the improvements (as opposed to a binary signal) and (3) ability to provide a skeleton with an isolated part to be evolved. For example, the problem of generating proofs for theorems… falls outside this scope, because it is unclear how to provide a rich enough scoring signal." — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6)
- [VERIFIED] The role of the LLM is downplayed: "the LLM… does not use much context about the problem; the LLM should instead be seen as a source of diverse (syntactically correct) programs with occasionally interesting ideas." — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6)
- [VERIFIED] Inductive bias: "FunSearch attempts to find solutions that have low Kolmogorov complexity". It "preferred symmetric ones, as these are more parsimonious". — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6)

### Inferences
- FunSearch's anti-gaming design comes from formulation choices rather than from a stated adversarial-robustness analysis. The skeleton guarantees valid outputs (for example, a legal cap set by construction), so the score is a direct measurement of the objective. Bin packing adds held-out test sets (OR2–OR4 and larger Weibull sizes).
- The 4/140 statistic shows that the headline cap-set result came from a heavy-tailed search outcome. Reported best-of-many results should be read together with the number of runs.

### Gaps
- The previous best n=8 cap-set size (commonly cited as 496) appears only in Fig. 4a, which is an image. I did not find it in the article text. [UNVERIFIED]
- I did not open the Supplementary Information (Appendix A: StarCoder comparison, ablations, statistics; Appendix E.1: T_0, N and T_program values). Exact wall-clock time per run is not given in the main text.
- The main text contains no discussion of the evaluator being exploited (for example, programs gaming timeouts). I found none.

---

## Q2. AlphaProof: formal environment, autoformalization, RL training, test-time RL, compute, results, limitations

### Takeaway
The Nature paper (published 12 Nov 2025) verifies every remembered claim and adds exact numbers:
- a Lean 4 RL environment, an AlphaZero-inspired tree search and a 3B-parameter encoder–decoder proof network;
- a Gemini 1.5 Pro-based autoformalizer that turned about 1M informal problems into about 80M Lean problems;
- training that both proves and disproves statements;
- test-time RL (TTRL) on hundreds of thousands of Gemini-generated variants per target problem;
- at IMO 2024, AlphaProof solved P1, P2 and P6 and AG2 solved P4, for 28/42;
- each AlphaProof IMO solution took 2–3 days of TTRL;
- about 100k TPU-days for autoformalization and about 80k TPU-days for main RL.

The IMO problems were formalized by hand. Answer candidates came from Gemini, and AlphaProof filtered them by refutation.

### Cited Findings
**Formal environment / search problem**
- [VERIFIED] The proving process is modelled "as a sequential decision-making problem". The state is the Lean tactic state, the action is "a Lean tactic, as a text string", and the reward is "rt = −1 for each tactic applied". An episode ends on a proof or a timeout. For multiple subgoals, "the return is defined as the minimum return over these subgoals (that is, corresponding to the longest proof branch)". — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)
- [VERIFIED] A tactic counts as successful only if it executes without error, the resulting proof term does not use `sorry`, and the term is type-correct. Goals the tactic does not address are temporarily closed with a private `internalSorry` axiom ("The 'private' keyword limits the axiom's visibility to discourage its use outside this specific tactic"). — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)
- [VERIFIED] Disproving: a custom tactic uses a private axiom `internal_true_if_false : (α → False) → α` to turn a goal into its negation. — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)
- [VERIFIED] Final check: "every proof or disproof found by AlphaProof undergoes a final, independent verification step" with the standard Lean command-line tool. "A custom command also verifies that the proof only relies on the three commonly accepted axioms built-in to Lean itself (propositional extensionality, global choice and soundness of quotient types)." — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)
- [VERIFIED] Environment hardening: key tactics such as `linarith` were compiled to C (six times faster); a wall-clock limit on each tactic was added on top of Lean's heartbeat limit; `checkSystem` is called more often; and a "hard cap on the size of numerals" prevents runaway computation. — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)

**Prover agent and search**
- [VERIFIED] The proof network is "a 3-billion-parameter encoder–decoder transformer". The decoder acts as the policy (K tactics sampled in parallel), and a value head on the encoder gives a categorical value distribution. — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)
- [VERIFIED] The tree search is "adapted from AlphaZero and Sampled MuZero" and uses PUCT selection. It adds AND nodes for subgoals (which prioritize the hardest unproven subgoal via 1 − Q), progressive sampling (K more tactics when n(s) ≤ C·N(s)^α), and merging of tactics that lead to the same Lean state. Within an attempt, "AlphaProof does not commit to intermediate actions… [it] can retain and expand a single search tree over the entire proof attempt". — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)

**Training pipeline**
- [VERIFIED] Pretraining used "approximately 300 billion tokens of code and mathematical text" (the encoder processed about 12T tokens; about 50 epochs). SFT used "approximately 300,000 state–tactic pairs" from Mathlib, costing about 10 TPU-days. — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)
- [VERIFIED] Autoformalization uses "a specialized Gemini 1.5 Pro language model fine-tuned on… (natural-language problem statement, formalization chain-of-thought, Lean formal statement) triplets". It started from about 2,500 expert-formalized problems (about 50 with expert chains of thought), was expanded to about 7,000, and then reached about 70,000 through STaR-like refinement. In that refinement, a low-compute AlphaProof proved equivalence to "golden" formalizations (`type_of% @generated = type_of% @golden`). — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)
- [VERIFIED] "this model auto-formalized approximately 1 million natural-language problems into a dataset of around 80 million formal Lean problems". "each auto-formalized statement, regardless of its fidelity to the original natural-language problem, provides a valid formal problem that AlphaProof can attempt to prove or disprove". — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)
- [VERIFIED] Autoformalizer quality before IMO 2024: 60% pass@1 on 50 representative IMO problems (algebra 81.3%, number theory 76.9%, combinatorics 33.3%) and 64% on 50 Putnam problems. This was judged by "an internal panel of approximately three Lean experts". — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)
- [VERIFIED] Main RL uses a matchmaker, distributed actors and a learner, for about 1 million training steps. The matchmaker randomly assigns "prove or disprove". It prioritizes by "interestingness" (untried problems, or problems with mixed success). It lowers priority for problems that are always solved or never solved. Disproved statements are not retried. The simulation budget grows multiplicatively with recent failures, up to a cap. Only successful proofs and disproofs train the network: "failed attempts are filtered out". Learner batches are 10% Mathlib SFT data and 90% replay. — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)
- [VERIFIED] The start-position data also included about 3,500 human-formalized problems (miniF2F-curriculum, the autoformalizer seed set and PutnamBench-train). — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)

**Test-time RL (TTRL)**
- [VERIFIED] Variants are generated by Gemini using few-shot examples from "791 (problem, variant) Lean pairs" (simplification, generalization, lemma proposal, analogy and similar moves). Programmatic variants that alter hypotheses or goals are added. All candidates are checked for syntactic validity in Lean. Evolutionary refinement runs for "up to N_evo iterations (where N_evo = 15)" and keeps "promising validated variants (for example, those identified by high string similarity to T)". The result is "hundreds of thousands of unique, syntactically valid Lean variants… for each target". A specialist agent initialized from the main-RL model then runs the same prove/disprove RL loop on the target plus its variants, and stops once the target is proved. — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)

**Compute**
- [VERIFIED] "The auto-formalization process… required approximately 100,000 TPU days in total (equivalent to, for instance, 10 runs of 2,000 TPUs utilized for 5 days). The main RL training loop… spanning approximately 80,000 TPU days (equivalent to, for instance, 4,000 TPUs utilized for 20 days)." Fig. 3 uses TPU v6e. — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)
- [VERIFIED] Inference scaling: going from 2 TPU-minutes to 12 TPU-hours of search per problem added more than 10 percentage points on formal-imo and PutnamBench-test. TTRL added about 15 points more on top of 12 TPU-hours of search. TTRL x-axes are in "hundreds of TPU days". — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)

**Results**
- [VERIFIED] Table 1 (inference compute per problem; this excludes amortized RL):

  | Setting | miniF2F-test | formal-imo | PutnamBench-test |
  |---|---|---|---|
  | 2 TPU minutes | 96.3% | 33.2% | 27.9% |
  | 12 TPU hours | 97.7% | 43.7% | 39.4% |
  | TTRL, 50 TPU days | 97.5% | 53.9% | 45.5% |
  | TTRL, 500 TPU days | 99.6% | 58.3% | 56.1% |

  For comparison, DeepSeek-Prover-V2 has 88.9% on miniF2F-test and 5.3% on PutnamBench-test (recomputed on their split). The paper notes miniF2F is "a corrected version", so "direct comparison should therefore be made with caution". — [AlphaProof Table 1](https://www.nature.com/articles/s41586-025-09833-y/tables/1)
- [VERIFIED] formal-imo is 258 non-geometry IMO problems (107 algebra, 77 combinatorics, 74 number theory). PutnamBench-test is 189 problems from even years from 1990 onward. — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)
- [VERIFIED] IMO 2024: "The remaining five non-geometry problems… were manually formalized in Lean by experts immediately after the competition's release". For P1, P2, P5 and P6, "hundreds of candidate answers were generated by querying the public Gemini 1.5 Pro model with Python tool use" (k = 500). In a 10-minute refutation search per candidate, AlphaProof disproved "99% of incorrect Gemini-generated candidates for P1, 98% for P2 and 7% for P6". Then "using TTRL, AlphaProof successfully discovered formal proofs for… P1, P2 and P6… Each of these solutions required 2–3 days of TTRL". P3 and P5 (combinatorics) were not solved. — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)
- [VERIFIED] "a total score of 28 out of 42 points… one point below the gold-medal threshold". P6 "was solved by only five human contestants". Gowers and Myers judged the proofs. Main RL and hyperparameters were frozen before the problems were released. — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y); the blog adds that gold "starts at 29 points, and was achieved by 58 of 609 contestants" — [IMO blog](https://deepmind.google/discover/blog/ai-solves-imo-problems-at-silver-medal-level/)
- [VERIFIED] The blog says: "Our systems solved one problem within minutes and took up to three days to solve the others." It also says "AlphaGeometry 2 solved Problem 4 within 19 seconds after receiving its formalization." — [IMO blog](https://deepmind.google/discover/blog/ai-solves-imo-problems-at-silver-medal-level/)
- [VERIFIED] Side experiment: the autoformalization system "successfully formalized P1, P2 and P6". P5 resisted even expert formalization on the first day. — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)

**Stated limitations**
- [VERIFIED] "the bespoke learning phase required by AlphaProof represents a scale of domain-specific training that is likely beyond the reach of most academic research groups", and "the multi-day inference time required by TTRL… highlights the need for more efficient inference-time strategies". Successes are "primarily within the domain of advanced high-school and undergraduate competition mathematics… within a known fixed library of mathematical concepts". Research mathematics needs "theory building". — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)
- [VERIFIED] Geometry was excluded because of gaps in Mathlib ("making it impractical to even state many questions"). — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)

### Inferences
- The search problem is defined in two layers. The outer layer chooses which statements to search: the autoformalized curriculum, ordered by the matchmaker's "interestingness", and for TTRL the variant curriculum. The inner layer is a single PUCT tree search per statement. The kernel is the exact goal test, and the step penalty with min-over-subgoals return shapes the search toward short, balanced proofs.
- Misformalization is treated as harmless for training, because any well-formed statement is a legitimate prove-or-disprove task. It still matters for evaluation, which is why the IMO problems and benchmarks were hand-formalized or corrected.
- Answer-finding ("find all…") was not done inside the formal search. An LLM guessed broadly (pass@500), and the prover worked as a cheap refutation filter. That filter worked poorly for P6 (only 7% of wrong answers refuted).
- Earlier-note correction: "The 'within minutes' problem" in the blog almost certainly refers to AG2's P4 (19 s), since the paper says each AlphaProof solution took 2–3 days. This is my inference; the blog does not name the problem.

### Gaps
- I did not open the Supplementary tables (search and RL hyperparameters: K, C, α, γ, trust_count, budgets) or the pseudocode.
- Total TTRL compute for the IMO run (TPU count × 2–3 days) is not stated in the main text.

---

## Q3. AlphaGeometry (AG1, Nature 2024): synthetic data, symbolic engine, language model's role, search, results — and cross-check with AG2

### Takeaway
AG1 frames geometry proving as an alternating loop. A symbolic engine, DD+AR (deductive database plus algebraic reasoning via Gaussian elimination), computes the full deduction closure. When that fails, a 151M-parameter transformer proposes one auxiliary construction per turn, and beam search runs over these proposals (beam 512, depth 16, branching 32). The training data came from about 1B random premise sets on 100,000 CPUs for 72 h. That gave about 500M proofs, reduced to 100M unique by deduplication, of which 9M involve auxiliary constructions. "Dependency difference" traceback is what turns forward deductions into auxiliary-construction training examples. AG1 solves 25/30 on IMO-AG-30. The cross-checked AG2 figures match the earlier note, except that the July 2024 blog says 83%/53% where the AG2 paper says 84%/54%.

### Cited Findings
- [VERIFIED] Synthetic data: "we sampled nearly 1 billion of such premises… we do not make use of any existing theorem premises from human-designed problem sets". "After running this process on 100,000 CPU workers for 72 h, we obtained roughly 500 million synthetic proof examples… At the end, we obtain 100 million unique theorem–proof examples. A total of 9 million examples involves at least one auxiliary construction." — [AlphaGeometry, Nature](https://www.nature.com/articles/s41586-023-06747-5)
- [VERIFIED] Auxiliary constructions are mined by "dependency difference". The premises in P that the conclusion's objects do not depend on are moved into the proof, "so that a generative model that learns to generate the proof can learn to construct them". Proof pruning tries discarding subsets of auxiliary points and re-checks reachability, because "Without minimality, we obtained many synthetic proofs with vacuous auxiliary constructions". — [AlphaGeometry, Nature](https://www.nature.com/articles/s41586-023-06747-5)
- [VERIFIED] Symbolic engine: DD uses definite Horn-clause rules; AR uses Gaussian elimination over angles (slopes mod π), log-ratios and distances. Minimal-premise traceback uses mixed-integer linear programming for AR and a greedy hypergraph spanning tree for collinearity and concyclicity (the exact version is NP-hard). DD and AR alternate "until the joint deduction closure stops expanding", "within a few seconds to at most a few minutes on standard non-accelerator hardware". — [AlphaGeometry, Nature](https://www.nature.com/articles/s41586-023-06747-5)
- [VERIFIED] The language model is a transformer with 12 layers, d=1024, 8 heads and "151 million parameters", using a 757-token vocabulary and 1,024 context. It was pretrained on all 100M proofs and then fine-tuned on the 9M auxiliary-construction proofs, on TPUv3 4×4. "We do not perform any hyperparameter tuning." — [AlphaGeometry, Nature](https://www.nature.com/articles/s41586-023-06747-5)
- [VERIFIED] Search: "The language model is seeded with the problem statement string and generates one extra sentence at each turn… describing one new auxiliary construction". "we use a beam size of k = 512, the maximum number of iterations is 16 and the branching factor for each node… is 32". Compute per problem was 4 V100 GPU workers, plus a 10,000-CPU symbolic pool shared across the 30 problems. — [AlphaGeometry, Nature](https://www.nature.com/articles/s41586-023-06747-5)
- [VERIFIED] Results on IMO-AG-30:
  - AG1 solves 25 problems.
  - Wu's method solves 10.
  - DD alone solves 14 with AR added; the LM added 11 more.
  - DD+AR+human heuristics with 250 workers for 1.5 h solves 18.
  - GPT-4 full-proof success is 0%.

  Ablations:
  - 20% of the training data gives 21.
  - Beam 8 instead of 512 gives 21.
  - Depth 2 gives 21.
  - No pretraining gives 21.
  - No fine-tuning gives 23.

  On a 231-problem set, AG1 solves 98.7%. — [AlphaGeometry, Nature](https://www.nature.com/articles/s41586-023-06747-5). The blog adds "the average human gold medalist solved 25.9 problems" — [AG blog](https://deepmind.google/discover/blog/alphageometry-an-olympiad-level-ai-system-for-geometry/)
- [VERIFIED] Coverage limit: "Among all non-combinatorial geometry-related problems, 75% can be represented". Geometric inequalities and combinatorial geometry "cannot be translated". — [AlphaGeometry, Nature](https://www.nature.com/articles/s41586-023-06747-5)
- [VERIFIED] Stated limitation: "AlphaGeometry operates with a much lower-level toolkit for proving than humans do, limiting the coverage of the synthetic data, test-time performance and proof readability." — [AlphaGeometry, Nature](https://www.nature.com/articles/s41586-023-06747-5)
- [VERIFIED] Generality recipe: "(1) An implementation of the domain's objects and definitions. (2) A random premise sampler. (3) The symbolic engine(s)… (4) A traceback procedure". The paper notes that formalizations of combinatorics are "very nascent". — [AlphaGeometry, Nature](https://www.nature.com/articles/s41586-023-06747-5)
- [VERIFIED, cross-check with AG2] The AG2 paper reports an 84% solve rate on 2000–2024 IMO geometry vs 54% for AG1. The July 2024 blog says "83%… compared to the 53%". Both are DeepMind primary sources; the paper is the later and more precise one. — [AG2](https://arxiv.org/html/2502.03544); [IMO blog](https://deepmind.google/discover/blog/ai-solves-imo-problems-at-silver-medal-level/)
- [VERIFIED, cross-check] AG2 is described as having a "language model… based on Gemini and trained from scratch on an order of magnitude more synthetic data", a symbolic engine "two orders of magnitude faster", and "a novel knowledge-sharing mechanism" across search trees. — [IMO blog](https://deepmind.google/discover/blog/ai-solves-imo-problems-at-silver-medal-level/). This is consistent with the earlier note's description of AG2/SKEST.
- [VERIFIED, cross-check] In AG2, a step is verified when "the new DDAR manages to prove the conclusion of the step, and the numerical check of the conclusion in the diagram passed". — [AG2](https://arxiv.org/html/2502.03544)

### Inferences
- In AG1 the verifier also generates the data. The symbolic closure produces the training distribution and serves as the goal test at search time. The LM searches only the action space the engine cannot reach: exogenous construction terms. The ablations (beam 8 → 21 and depth 2 → 21, compared with 25 at full settings) suggest most of the gain comes from the learned proposal distribution rather than from deep search.

### Gaps
- I did not open the Extended Data figures (time-limited 4.5 h and 1.5 h results, failure analyses).
- A 2026 Nature paper titled "Proposing and solving olympiad geometry with guided tree search" (26 Jan 2026) appeared in Nature's related-articles list. I did not open it and did not check who wrote it. It is out of scope unless it is a DeepMind paper.

---

## Q4. DeepMind statements about evaluator exploitation or verifier limits in these systems

### Takeaway
None of the three papers reports a case of a candidate exploiting the evaluator. All three do describe concrete guards and admitted gaps in the verifier or specification:
- FunSearch: the sandbox, discarding invalid outputs, a skeleton that makes outputs valid by construction, and held-out test sets.
- AlphaProof: private axioms, an axiom audit, kernel re-checking, numeral caps, and corrected misformalized benchmarks. It also acknowledges that autoformalized statements may not match their sources.
- AlphaGeometry: a DSL-level verifier with non-degeneracy assumptions, a translated theorem whose generalization drops a betweenness condition, and limited coverage.

### Cited Findings
- [VERIFIED] FunSearch: incorrect programs, meaning those over time or memory limits or with "invalid outputs", are discarded. Generated code runs in "a sandbox for safely executing generated code". The scope statement requires "an efficient evaluator" and "'rich' scoring feedback". — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6)
- [VERIFIED] FunSearch reasons that beating state-of-the-art results "provides a clear indication that the discoveries are truly new, as opposed to being retrieved from the LLM's training data". — [FunSearch, Nature](https://www.nature.com/articles/s41586-023-06924-6)
- [VERIFIED] AlphaProof's soundness boundary is stated explicitly: "absolute assurance of correctness (assuming the soundness of the Lean kernel and the declared axioms)". Proofs are checked so that they use only the three standard Lean axioms. This matters because the training environment itself injects private axioms (`internalSorry`, `internal_true_if_false`). — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)
- [VERIFIED] On benchmark misformalization, AlphaProof's miniF2F corrections "addressed various misformalized problems (for example, disprovable statements, or statements with contradictions in its hypothesis)". "several misformalizations in the original PutnamBench were identified and subsequently corrected upstream". — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)
- [VERIFIED] On data separation, AlphaProof's pretraining "explicitly excluded all Lean code" and benchmark proofs. Similar documents were removed from the autoformalization pipeline. The paper admits the web corpus "might have incidentally contained natural-language discussions or solutions to some historical problems". — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)
- [VERIFIED] On AlphaProof's autoformalization fidelity: training statements are used "regardless of its fidelity to the original natural-language problem". Multiple translations are sampled per problem so that a correct one is more likely to be included, "with incorrect ones often being quickly resolved during main RL or sometimes presenting interesting problems in their own right". — [AlphaProof, Nature](https://www.nature.com/articles/s41586-025-09833-y)
- [VERIFIED] AlphaGeometry's verification is relative to a specialized language with "human-like non-degeneracy and topological assumptions", in which "each proof step is logically and numerically verified". — [AlphaGeometry, Nature](https://www.nature.com/articles/s41586-023-06747-5)
- [VERIFIED] On the AlphaGeometry IMO 2004 P1 generalization: "the original problem requires P to be between B and C, a condition where the generalized theorem and solution does not guarantee". In other words, the translated statement is weaker than the original. — [AlphaGeometry, Nature](https://www.nature.com/articles/s41586-023-06747-5)
- [VERIFIED] AlphaGeometry on GPT-4 baselines: "the performance of GPT-4 performance on IMO problems can also be contaminated by public solutions in its training data". — [AlphaGeometry, Nature](https://www.nature.com/articles/s41586-023-06747-5)
- [VERIFIED] The AlphaEvolve arXiv HTML contains no use of "exploit", "cheat", "hack" or "loophole" in the sense of evaluator gaming. The only match was "balancing exploration and exploitation". — [AlphaEvolve](https://arxiv.org/html/2506.13131)

### Inferences
- DeepMind's own framing puts the risk at the specification layer, not the checker: which formal statement is checked, which axioms are allowed, and what the DSL can express. This matches the earlier note's conclusion that failure points move outward as the kernel gets more sound.

### Gaps
- I found no DeepMind primary statement documenting reward hacking or evaluator exploitation by FunSearch, AlphaProof or AlphaGeometry candidates. If there is one, it would be in Supplementary Information I did not open.
