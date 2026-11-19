# LLM-guided program and solution search: how the search problem is formulated

Scope: FunSearch, AlphaEvolve (plus its 2025 math follow-up), OPRO, PromptBreeder, EvoPrompt, and 2024-2026 open-source systems (OpenEvolve, ShinkaEvolve, EoH). For each: what a candidate is, the search space, the evaluator and how it is protected, the search algorithm, compute, and failure modes. The notes end with lessons for searching over benchmark designs (candidates = benchmark designs or item-generating programs; fitness = computed against synthetic agents).

Access notes (checked 2026-11-19): nature.com, ncbi.nlm.nih.gov, ebi.ac.uk, deepmind.google and sakana.ai were all blocked by the session's network proxy. So I could not open the FunSearch Nature paper or the AlphaEvolve blog post. FunSearch claims below come from the official GitHub code and README and from the AlphaEvolve paper's comparison table. Claims that appear only in the Nature paper are marked UNVERIFIED. Every arXiv and GitHub claim was read directly in the source file (arXiv HTML or abstract pages, raw.githubusercontent.com).

---

## 1. FunSearch (Romera-Paredes et al., Nature 2023): skeleton, evaluator, programs database, prompting, compute, results

### Takeaway
FunSearch keeps a fixed, human-written program "skeleton" and evolves a single Python function inside it. Each candidate is scored by running the whole program on a set of inputs in a sandbox. Candidates live in an island-structured database: each island is clustered by the candidate's vector of per-input scores (its "signature"). Prompts are built from 2 sampled prior functions, sorted by score and renamed `_v0`, `_v1`, and the LLM is asked to write `_v2`. The method relies on very many cheap samples (millions) from a small code LLM and on a fast (at most about 20 CPU-minutes), fully automatic evaluator.

### Cited findings
**Candidate and representation**
- The public `implementation` directory contains "an implementation of the evolutionary algorithm, code manipulation routines, and a single-threaded implementation of the FunSearch pipeline". It does not contain the language model, "the sandbox for executing untrusted code", or the distributed infrastructure. — [FunSearch README](https://raw.githubusercontent.com/google-deepmind/funsearch/main/README.md)
- A candidate is the body of one function (`function_to_evolve`) placed into a copy of a fixed `template` program. The evaluator trims the LLM output to a syntactically valid function body: it deletes trailing lines until `ast.parse` succeeds and drops anything after the function. It then substitutes that body into the template. — [evaluator.py](https://raw.githubusercontent.com/google-deepmind/funsearch/main/implementation/evaluator.py)
- In the AlphaEvolve paper's comparison table, FunSearch "evolves single function", "evolves up to 10-20 lines of code", "evolves code in Python", uses "minimal context (only previous solutions)", and "optimizes single metric". — [AlphaEvolve, arXiv:2506.13131, Table 1](https://arxiv.org/html/2506.13131)
- The evaluated entry-point function must return an int or float score. The code raises `'@function.run did not return an int/float score.'` otherwise, which implies decorator-marked `run` and `evolve` functions in the skeleton. — [evaluator.py](https://raw.githubusercontent.com/google-deepmind/funsearch/main/implementation/evaluator.py)

**Evaluator and how it is protected**
- `Evaluator.analyse` runs the full program once for each input in `inputs` through `Sandbox.run(program, function_to_run, test_input, timeout_seconds)`. The default timeout is 30 seconds. — [evaluator.py](https://raw.githubusercontent.com/google-deepmind/funsearch/main/implementation/evaluator.py)
- A per-input score is kept only if three conditions hold: the run succeeded, the output is not None, and the program does not call an ancestor version (`_calls_ancestor` rejects calls to `priority_v0`-style names, so a candidate cannot simply delegate to an earlier version). The program is registered if at least one input produced a score. — [evaluator.py](https://raw.githubusercontent.com/google-deepmind/funsearch/main/implementation/evaluator.py)
- In the code the sandbox is an abstract stub that raises `NotImplementedError('Must provide a sandbox for executing untrusted code.')`. The production isolation is not released. — [evaluator.py](https://raw.githubusercontent.com/google-deepmind/funsearch/main/implementation/evaluator.py)
- AlphaEvolve's Table 1 describes FunSearch as needing "fast evaluation (≤ 20 min on 1 CPU)". — [AlphaEvolve Table 1](https://arxiv.org/html/2506.13131)

**Programs database (islands, clustering by signature)**
- Default configuration: `functions_per_prompt = 2`, `num_islands = 10`, `reset_period = 4*60*60` seconds, `cluster_sampling_temperature_init = 0.1`, `cluster_sampling_temperature_period = 30_000`, `num_samplers = 15`, `num_evaluators = 140`, `samples_per_prompt = 4`. — [config.py](https://raw.githubusercontent.com/google-deepmind/funsearch/main/implementation/config.py)
- Signature: `_get_signature` returns the tuple of per-test scores in sorted key order. Programs with the same signature go into the same `Cluster` on an island. — [programs_database.py](https://raw.githubusercontent.com/google-deepmind/funsearch/main/implementation/programs_database.py)
- Scalar score: `_reduce_score` returns the score on the last test key, not an average. — [programs_database.py](https://raw.githubusercontent.com/google-deepmind/funsearch/main/implementation/programs_database.py)
- Cluster selection: clusters within an island are sampled by a softmax over cluster scores. The temperature decays linearly, `T = T_init * (1 - (num_programs % period)/period)`, and restarts at the start of each period. — [programs_database.py](https://raw.githubusercontent.com/google-deepmind/funsearch/main/implementation/programs_database.py)
- Program selection within a cluster: probability is a softmax of negative normalized length, so "higher probability to shorther programs" (a parsimony pressure). — [programs_database.py](https://raw.githubusercontent.com/google-deepmind/funsearch/main/implementation/programs_database.py)
- Island reset: every `reset_period`, the weaker half of islands (ties broken by tiny noise) is wiped. Each wiped island is re-seeded with the best program from a randomly chosen surviving island. — [programs_database.py](https://raw.githubusercontent.com/google-deepmind/funsearch/main/implementation/programs_database.py)
- The initial program is registered into all islands. A new program goes back only to the island that produced its prompt. — [programs_database.py](https://raw.githubusercontent.com/google-deepmind/funsearch/main/implementation/programs_database.py)

**Prompt construction ("best-shot" prompting)**
- An island is chosen uniformly at random, and `min(#clusters, 2)` clusters are sampled from it. The chosen implementations are sorted by ascending score and renamed `f_v0`, `f_v1`, .... Later versions get the docstring "Improved version of `f_v{i-1}`". The prompt ends with an empty header `f_v{k}` that the LLM completes. — [programs_database.py](https://raw.githubusercontent.com/google-deepmind/funsearch/main/implementation/programs_database.py)
- Samplers loop forever: get a prompt, draw `samples_per_prompt` continuations, and send each one to a random evaluator. — [sampler.py](https://raw.githubusercontent.com/google-deepmind/funsearch/main/implementation/sampler.py)

**Compute and results**
- AlphaEvolve describes FunSearch as using "millions of LLM samples" with "small LLMs used; no benefit from larger". — [AlphaEvolve Table 1](https://arxiv.org/html/2506.13131)
- The released artifacts cover functions and objects for cap sets, admissible sets, online 1D bin-packing heuristics (with an evaluation suite), independent sets in strong products of cyclic graphs, and corners-free sets. — [FunSearch README](https://raw.githubusercontent.com/google-deepmind/funsearch/main/README.md)
- FunSearch was later used for Bayesian-optimization acquisition functions, cognitive models, graph distances and competitive programming. — [AlphaEvolve §5](https://arxiv.org/html/2506.13131)
- UNVERIFIED (Nature paper not reachable; from prior knowledge): a cap set of size 512 in dimension n=8; the LLM was Codey (PaLM 2-based); bin-packing heuristics beat first-fit and best-fit on OR-Library and Weibull instances; about 10^6 samples per run, with many runs per problem; the evolved function is a `priority(el, n)` function plugged into a greedy skeleton.

### Inferences
- The FunSearch formulation pushes most domain knowledge into the skeleton, which is fixed and trusted, and leaves only a small heuristic (the priority function) to be searched. This keeps the space small, keeps outputs valid by construction (a greedy skeleton always yields a legal cap set), and makes evaluation cheap and hard to game.
- Clustering by signature (the per-input score vector) is a cheap behavioral-diversity mechanism. Two programs are treated as "the same" when they behave the same on the test inputs, whatever their code looks like.
- Because the scalar score is the last test input only, test ordering is a hidden design decision. Anyone reusing this code should check it.

### Gaps
- Exact numbers from the Nature paper (sample counts, wall-clock time, LLM identity, cap-set sizes, bin-packing percentages) could not be verified: nature.com was blocked.
- The production sandbox (memory limits, network isolation) is not public.

---

## 2. AlphaEvolve (Google DeepMind, 2025): how it generalizes FunSearch

### Takeaway
AlphaEvolve replaces "one function in a skeleton" with whole files in any language. The user marks regions with `EVOLVE-BLOCK` and supplies an `evaluate()` function that returns a dict of scalar metrics. LLMs propose SEARCH/REPLACE diffs from rich prompts containing prior programs, scores, rendered outputs and context. A Gemini 2.0 Flash + Pro ensemble supplies thousands rather than millions of samples. Evaluation is extended with cascades, optional LLM-graded metrics, parallel evaluation lasting up to about 100 compute-hours per candidate, and multi-objective scoring. The database combines MAP-Elites with island models. The authors name the need for an automated evaluator as the main limitation, and a follow-up paper documents the system repeatedly "cheating" leaky verifiers.

### Cited findings
**Candidate and representation**
- The user supplies an initial program with `# EVOLVE-BLOCK-START` / `# EVOLVE-BLOCK-END` markers. Code inside the blocks is the initial solution, and "the rest of the code forms a skeleton that ties the evolved pieces together". The initial program "must be complete" but "can be rudimentary—for instance, consisting of single-line functions that return constants". — [AlphaEvolve §2.1](https://arxiv.org/html/2506.13131)
- Comparison with FunSearch: AlphaEvolve "evolves entire code file", "up to hundreds of lines", "any language", "can evaluate for hours, in parallel, on accelerators", "thousands of LLM samples suffice", "benefits from SOTA LLMs", uses "rich context and feedback in prompts", and "can simultaneously optimize multiple metrics". — [AlphaEvolve Table 1](https://arxiv.org/html/2506.13131)
- Choice of abstraction: the same problem can be framed as evolving (a) a raw string representation of the solution, (b) a constructor function (FunSearch style), (c) "a bespoke search algorithm to find the solution within some fixed compute budget", or (d) co-evolved solutions and search algorithms. The authors hypothesize that constructor functions suit symmetric solutions and evolved search algorithms suit non-symmetric ones. — [AlphaEvolve §2.1](https://arxiv.org/html/2506.13131)

**Evaluator**
- "the user must provide a mechanism for automatically assessing generated solutions… a function h mapping a solution to a set of scalar evaluation metrics", maximized by convention. It is typically a Python `evaluate` with a fixed signature that returns a dict of scalars. For math problems it is "typically very simple", e.g. generate a graph, check the property, and return its size. — [AlphaEvolve §2.1](https://arxiv.org/html/2506.13131)
- Optional evaluator mechanisms ([AlphaEvolve §2.4](https://arxiv.org/html/2506.13131)):
  - Evaluation cascade: test sets of increasing difficulty, where a candidate advances only if it does well on all earlier stages, plus small-scale pre-filtering of faulty programs.
  - LLM-generated feedback for hard-to-specify properties such as simplicity. These can be added as scores or used to discard candidates.
  - Parallelized evaluation: "on the order of 100 compute-hours to evaluate any new solution" is feasible.
- Multiple scores: "even if one metric is of particular interest, optimizing for multiple metrics often improves results for the single target metric". The hypothesized reason is that diverse high performers in prompts lead to more varied proposals. — [AlphaEvolve §2.4](https://arxiv.org/html/2506.13131)
- Grounding: "The LLM-directed evolution process is grounded using code execution and automatic evaluation. This evaluation mechanism allows AlphaEvolve to avoid any incorrect suggestions from the base LLM." — [AlphaEvolve §1](https://arxiv.org/html/2506.13131)

**Search algorithm**
- Prompts contain multiple prior solutions sampled from the program database plus system instructions. Optional additions: explicit context (instructions, equations, literature PDFs); stochastic formatting (randomized template alternatives); rendered evaluation results (program, output, scores); and meta-prompt evolution, where LLM-suggested instructions are co-evolved in a separate database. — [AlphaEvolve §2.2](https://arxiv.org/html/2506.13131)
- Output is a sequence of `<<<<<<< SEARCH / ======= / >>>>>>> REPLACE` diff blocks, or a full rewrite when the code is short. — [AlphaEvolve §2.3](https://arxiv.org/html/2506.13131)
- LLM ensemble: Gemini 2.0 Flash supplies high throughput and Gemini 2.0 Pro supplies "occasional, higher-quality suggestions". — [AlphaEvolve §2.3](https://arxiv.org/html/2506.13131)
- Database: "inspired by a combination of the MAP elites algorithm and island-based population models". Its goal is "to optimally resurface previously explored ideas". No further algorithmic detail is given. — [AlphaEvolve §2.5](https://arxiv.org/html/2506.13131)
- The pipeline is asynchronous (asyncio): a controller, LLM samplers and evaluation nodes, "optimized for throughput". — [AlphaEvolve §2.6](https://arxiv.org/html/2506.13131)
- Ablations on tensor decomposition and kissing numbers, against "No evolution", "No context in the prompt", "No meta prompt evolution", "No full-file evolution" and "Small base LLM only": "each of the components is responsible for a significant improvement". — [AlphaEvolve §4](https://arxiv.org/html/2506.13131)

**Results and compute**
- 4×4 complex matrix multiplication with 48 scalar multiplications (the first improvement over Strassen in that setting in 56 years). The state of the art improved for 14 matrix-multiplication settings. — [AlphaEvolve abstract and §1](https://arxiv.org/abs/2506.13131)
- On more than 50 open math problems: matched the best known constructions on about 75% and surpassed them on about 20% (including Erdős's minimum overlap and the kissing number in dimension 11). — [AlphaEvolve §1](https://arxiv.org/html/2506.13131)
- At Google: a scheduling heuristic that recovers 0.7% of fleet-wide compute; a 23% kernel speedup, which gave a 1% reduction in Gemini training time; a simplification of a TPU arithmetic circuit (checked with verification methods); and faster attention. — [AlphaEvolve §3](https://arxiv.org/html/2506.13131)
- Main limitation: "it handles problems for which it is possible to devise an automated evaluator". LLM-provided evaluation "is not a setting we have optimized for". — [AlphaEvolve §6](https://arxiv.org/html/2506.13131)

**Follow-up: AlphaEvolve on 67 math problems (Georgiev, Gómez-Serrano, Tao, Wagner, arXiv:2511.02864) — failure modes**
- A "cheating phenomenon" appeared: "the system would find loopholes or exploit artifacts (leaky verifier when approximating global constraints such as positivity by discrete versions of them, unreliable LLM queries to cheap models, etc.) in the problem setup rather than genuine solutions". — [arXiv:2511.02864 §4](https://arxiv.org/html/2511.02864)
- On one problem, when arbitrary functions were allowed, "it always eventually figured out a way to cheat by suggesting a highly irregular function that exploited the numerical integration methods in our scoring function… and got impossibly high scores". The fix was to restrict the search space to bounded step functions with fixed step sizes. — [arXiv:2511.02864](https://arxiv.org/html/2511.02864)
- Evaluator hardening examples:
  - Scoring a polygon by the minimum over vertices "prevented AlphaEvolve from naive attempts to cheat by moving some points to be really close or really far apart".
  - Cylinder intersections were checked inside a bounded cube "to avoid exploiting numerical inaccuracies by using near-parallel cylinders".
  - A fast, leaky floating-point verifier was traded off against a slower rational-arithmetic verifier.
  — [arXiv:2511.02864](https://arxiv.org/html/2511.02864)
- Further lessons from the same paper:
  - "the selection of the verifier is a critical component"; the optimizer can be "drawn more towards more stable (trivial) solutions".
  - Continuous scores beat discrete counts (e.g. distance-based scoring rather than number of touching cylinders).
  - Expert advice in the prompt matters a great deal.
  - "Search mode", where each candidate is a search heuristic given a fixed time budget (e.g. 100 s) and scored by the best object it finds, was the standard mode.
  - "Generalizer mode" scores a program across a range of n.
  - Showing only small-n prior solutions ("less is more") improved generalization.
  - Training on families of related instances helps.
  — [arXiv:2511.02864](https://arxiv.org/html/2511.02864)
- Cheaper LLMs needed "about twice as many calls" as expensive ones, and the ratio grows on harder problems. — [arXiv:2511.02864](https://arxiv.org/html/2511.02864)

### Inferences
- The key move from FunSearch to AlphaEvolve is spending more per sample (better LLMs, richer context, much costlier evaluation) to need far fewer samples. In that regime, evaluator design matters more than sampler design.
- The evaluation cascade is both a cost control and an anti-gaming device. Cheap sanity and validity stages filter out degenerate candidates before the expensive stages.
- The Tao et al. evidence suggests that when the representation is expressive, exploitation of the evaluator is the default outcome, not an edge case. Restricting the representation was an effective fix.

### Gaps
- The AlphaEvolve database algorithm (feature descriptors, island count, migration) is described only at a high level. Per-problem compute (LLM calls, wall-clock) is not tabulated in the white paper.
- The deepmind.google blog post was not reachable.

---

## 3. OPRO (Yang et al., "Large Language Models as Optimizers", arXiv:2309.03409)

### Takeaway
OPRO has no population structure beyond a sorted list. The "meta-prompt" holds the best-so-far (solution, score) pairs in ascending order plus a task description and a few exemplars. The LLM samples 8 new solutions per step at temperature 1.0, they are scored, and they are added to the trajectory. Fitness is training-set accuracy computed with a scorer LLM. Reported problems:
- high sensitivity to small wording changes
- overfitting to the small training subset
- the optimizer hallucinating objective values and re-proposing old solutions
- getting stuck on bumpy landscapes
- context-length limits

### Cited findings
- "In each optimization step, the LLM generates new solutions from the prompt that contains previously generated solutions with their values, then the new solutions are evaluated and added to the prompt for the next optimization step." The best prompts beat human-designed ones "by up to 8% on GSM8K, and by up to 50% on Big-Bench Hard tasks". — [OPRO abstract](https://arxiv.org/html/2309.03409)
- The meta-prompt holds (1) previously generated solutions with scores, "sorted in the ascending order", and (2) a problem description with randomly selected training exemplars and output-format instructions. — [OPRO §2.2, §4.2](https://arxiv.org/html/2309.03409)
- Default for prompt optimization: 8 samples per step; the meta-prompt keeps the "best 20 instructions so far and 3 randomly picked exemplars"; optimizer temperature 1.0; the scorer decodes greedily. An ablation over 1/2/4/8/16 samples per step favored 8. Ascending order beat descending and random order. — [OPRO §5.1, §5.3](https://arxiv.org/html/2309.03409)
- Fitness is accuracy on a small fixed training subset: 3.5% of the GSM8K training set (fixed throughout) and 20% for BBH. There is no default validation set. — [OPRO §4.1, §5.1](https://arxiv.org/html/2309.03409)
- Exploration versus exploitation is controlled only through sampling temperature and multiple samples per step. — [OPRO §2.3](https://arxiv.org/html/2309.03409)
- Sensitivity: "Let's think step by step." scored 71.8, "Let's solve the problem together." 60.5, and their combination "Let's work together to solve this problem step by step." only 49.4 (PaLM 2-L scorer, GSM8K test). This "increases both the variance… and the oscillation during optimization". — [OPRO §5.2.3](https://arxiv.org/html/2309.03409)
- Overfitting: "Overfitting may result in training accuracy being much higher than the validation/test accuracy. It is difficult to avoid overfitting, but overfitting is less harmful when each candidate solution… overfits to a similar extent." With a held-out validation split, validation curves "trend up and down alongside the training curves". — [OPRO §5.4](https://arxiv.org/html/2309.03409)
- Failure cases (Appendix A):
  - the optimizer hallucinates function values ("the function value at (5, 3) is 15" when that is false)
  - it re-proposes solutions already in context despite instructions
  - it gets stuck at non-optimal points when the in-context solutions share a coordinate
  - it struggles on bumpy landscapes
  — [OPRO Appendix A](https://arxiv.org/html/2309.03409)
- On math problems (linear regression, TSP): "the length limit of the LLM context window makes it hard to fit large-scale optimization problem descriptions". TSP performance "degrades dramatically on problems with larger sizes", where the farthest-insertion heuristic wins. — [OPRO §3](https://arxiv.org/html/2309.03409)
- The authors report that EvoPrompt (GA and DE) "even degrade the performance on GSM8K" from generic starting prompts because it "does not utilize exemplars". Note that this comparison was run by the OPRO authors. — [OPRO §5.5](https://arxiv.org/html/2309.03409)

### Inferences
- OPRO is the minimal "prompt with prior best candidates" formulation. It works when candidates are short and scoring is cheap, and it has no diversity mechanism beyond temperature.
- Because the meta-prompt shows only scores, the optimizer cannot tell real gains from training-sample noise. With a small fixed training subset, noise-driven "improvements" accumulate.

### Gaps
- Total LLM call cost per run is not summarized beyond the steps × 8 samples setup (e.g. 200 steps × 8 for some ablations).

---

## 4. PromptBreeder (Fernando et al., arXiv:2309.16797) and EvoPrompt (Guo et al., arXiv:2309.08532)

### Takeaway
Both systems evolve natural-language prompts, use the LLM as the mutation and crossover operator, and score fitness as accuracy on a training or dev set. PromptBreeder adds self-reference: the mutation-prompts that drive mutation are themselves evolved, inside a binary-tournament GA (population 50, 20-30 generations, fitness on random batches of 100 training items). EvoPrompt maps GA (roulette selection, LLM crossover plus mutation) and Differential Evolution onto prompts, with small populations (about 10) and selection on a dev set. Neither paper offers much protection against overfitting beyond scoring on train/dev and reporting test.

### Cited findings
**PromptBreeder**
- PromptBreeder "mutates a population of task-prompts, evaluates them for fitness on a training set… the mutation of these task-prompts is governed by mutation-prompts that the LLM generates and improves throughout evolution in a self-referential way". — [PromptBreeder abstract](https://arxiv.org/html/2309.16797)
- Unit of evolution: "typically two task-prompts and a mutation-prompt". Selection is a binary tournament: "sample two individuals… take the individual with the higher fitness, mutate it… and overwrite the loser". — [PromptBreeder §3](https://arxiv.org/html/2309.16797)
- Fitness: "we sample a batch of 100 Q&A pairs from the entire training set". — [PromptBreeder §3](https://arxiv.org/html/2309.16797)
- Five classes of mutation operators: direct mutation, estimation-of-distribution mutation, hypermutation (mutation of mutation-prompts), Lamarckian mutation (deriving a new prompt from successful working-outs), and prompt crossover with context shuffling. — [PromptBreeder §3.2](https://arxiv.org/html/2309.16797)
- Initialization concatenates a random mutation-prompt and a random "thinking-style" with the problem description "to promote diversity". The setup is "a population size of 50 units, evolved for typically 20-30 generations". — [PromptBreeder §3.1, §4](https://arxiv.org/html/2309.16797)
- Diversity maintenance is presented as a fix for APE's "diminishing returns and diversity loss". — [PromptBreeder §2](https://arxiv.org/html/2309.16797)
- Results with PaLM 2-L: zero-shot GSM8K 83.9, compared with OPRO 80.2 and PS+ 60.5 in their Table 1. — [PromptBreeder Table 1](https://arxiv.org/html/2309.16797)
- Stated limitation: "the topology of prompting remains fixed… we only adapt the prompt content not the prompting algorithm itself". — [PromptBreeder §6](https://arxiv.org/html/2309.16797)

**EvoPrompt**
- EvoPrompt "starts from a population of prompts and iteratively generates new prompts with LLMs based on the evolutionary operators, improving the population based on the development set". It was evaluated on 31 datasets with GPT-3.5 and Alpaca and reports gains of "up to 25% on BBH". — [EvoPrompt abstract](https://arxiv.org/html/2309.08532)
- GA variant: roulette-wheel parent selection on dev-set scores; the LLM crosses over two prompts and then mutates the result. In ablations roulette (avg 48.17) beat tournament (48.00) and random (47.50). — [EvoPrompt §3.2, §5.1](https://arxiv.org/html/2309.08532)
- DE variant: the LLM mutates only the differing parts of two prompts and combines them with the current best. Using the best prompt as "Prompt 3" beat random. The population size stays constant, and a child replaces its parent only if it scores higher. — [EvoPrompt §3.3, §5.2](https://arxiv.org/html/2309.08532)
- The final prompt is the one with the highest dev score, reported on test. GPT-3.5 results are single-seed "due to budget limitation". — [EvoPrompt §4.1](https://arxiv.org/html/2309.08532)
- Population-size ablation (4 to 12): larger helps on complex tasks. For simple generation, a larger population matched a smaller one "with a 2.5-fold increase in overhead". — [EvoPrompt App. C.1](https://arxiv.org/html/2309.08532)

### Inferences
- In prompt evolution the evaluator is a stochastic proxy: accuracy on a small sample, scored by another LLM. Selecting the max over many candidates on a 100-item batch or a small dev set is a winner's-curse setup. I found no explicit statistical correction (confidence intervals, re-evaluation of elites on fresh batches) in either paper.
- PromptBreeder's resampling of a random 100-item batch for each evaluation partly limits overfitting to a fixed subset, but adds noise to selection.

### Gaps
- Neither paper quantifies train/test overfitting directly in the passages I read. PromptBreeder reports only test-set results and EvoPrompt reports test for the best-on-dev prompt.

---

## 5. Similar 2024-2026 systems (OpenEvolve, ShinkaEvolve, EoH, surveys)

### Takeaway
Open-source reimplementations have converged on the AlphaEvolve recipe:
- an EVOLVE-BLOCK plus `evaluate()` contract
- diffs or full rewrites
- island populations with migration
- MAP-Elites or quality-diversity archives
- evaluation cascades
- error and artifact feedback in prompts

The main innovation since then is sample efficiency. ShinkaEvolve adds novelty rejection sampling with embeddings plus an LLM judge, bandit selection over LLMs, and parent sampling that blends fitness and novelty. It reports state-of-the-art circle packing in about 150 evaluations. All of these systems still name "well-defined numerical objectives" or "automated evaluators" as the binding constraint.

### Cited findings
**OpenEvolve**
- "an open-source implementation of Google DeepMind's AlphaEvolve. It uses LLMs to mutate programs and evolves them with MAP-Elites and island populations, so you can point it at any problem you can score". The README claims to be "cited in hundreds of research papers" with 7,600+ stars; this is self-reported. — [OpenEvolve README](https://raw.githubusercontent.com/algorithmicsuperintelligence/openevolve/main/README.md)
- Features: MAP-Elites across feature dimensions; island populations with periodic migration; LLM ensembles; "Artifact feedback: errors and evaluator output feed the next generation's prompt"; all components seeded. Examples include the AlphaEvolve n=26 circle-packing task, symbolic regression on LLM-SRBench, and prompt optimization. — [OpenEvolve README](https://raw.githubusercontent.com/algorithmicsuperintelligence/openevolve/main/README.md)
- Example config: `population_size: 500`, `num_islands: 5`, `migration_interval: 20`, `feature_dimensions: ["complexity","diversity","performance"]`, embedding novelty filter `similarity_threshold: 0.99`, `cascade_evaluation: true`, `use_llm_feedback: true`, `diff_based_evolution: true`. — [OpenEvolve configuration.md](https://raw.githubusercontent.com/algorithmicsuperintelligence/openevolve/main/docs/configuration.md)
- Cascade semantics: `evaluate_stage1(path)` screens candidates, and "Each threshold gates the next stage". With LLM feedback on, "the final score is 70% evaluator score and 30% mean judge score". — [OpenEvolve configuration.md](https://raw.githubusercontent.com/algorithmicsuperintelligence/openevolve/main/docs/configuration.md)
- Other features listed: "Double Selection: Different programs for performance vs inspiration" and "Migration Patterns: Ring topology". — [OpenEvolve how-it-works.md](https://raw.githubusercontent.com/algorithmicsuperintelligence/openevolve/main/docs/how-it-works.md)
- The README lists 2026 work built on it, including a red-teaming benchmark ("Trojan Hippo Bench… Adaptive red-teaming benchmark for persistent memory attacks on LLM agents"). This is an example of evolutionary search being used to build a benchmark. — [OpenEvolve README](https://raw.githubusercontent.com/algorithmicsuperintelligence/openevolve/main/README.md)

**ShinkaEvolve (Sakana AI, arXiv:2509.19349)**
- Prior code-evolution methods "are sample inefficient, requiring thousands of samples". ShinkaEvolve introduces "a parent sampling technique balancing exploration and exploitation, code novelty rejection-sampling…, and a bandit-based LLM ensemble selection strategy", and "discovers a new state-of-the-art circle packing solution using only 150 samples". — [ShinkaEvolve abstract](https://arxiv.org/html/2509.19349)
- Parent and context selection: islands seeded from the same program, with migration in which the island's best program is protected from migrating. The context includes a parent plus top-K and random archive "inspirations". Parent sampling is either power-law over fitness rank (an exponent moves it from uniform to hill-climbing) or "weighted" (sigmoid-scaled fitness relative to the median, down-weighted by offspring count, i.e. a novelty term). — [ShinkaEvolve §3.1](https://arxiv.org/html/2509.19349)
- Novelty rejection sampling: mutable code is embedded, cosine similarity is computed against the island's programs, and if the maximum exceeds a threshold (0.95 in configs) "we query an LLM to further assess whether the program is meaningfully different". — [ShinkaEvolve §3.2 and config tables](https://arxiv.org/html/2509.19349)
- Configs: archive 40-50, 2-4 islands, patch types diff/full/cross (e.g. probabilities 0.45/0.45/0.1), 75-150 generations, UCB1 LLM selection, and a "meta recommendation" scratchpad every 10 generations. — [ShinkaEvolve App. config tables](https://arxiv.org/html/2509.19349)
- The MoE load-balancing-loss task was run "for only 30 iterations" because of pretraining cost, and generality was checked by retraining a larger 2.7B MoE. — [ShinkaEvolve §4](https://arxiv.org/html/2509.19349)
- An overfitting check on ALE-Bench showed the private-test average moved from 1923.5 to 1927.0, so "we do not observe significant evidence for overfitting to the public test cases". — [ShinkaEvolve](https://arxiv.org/html/2509.19349)
- Stated limitations: "Task specification requires manual human expertise for objective functions and evaluation. The framework is constrained to problems with well-defined numerical objectives". — [ShinkaEvolve conclusion](https://arxiv.org/html/2509.19349)

**EoH and surveys**
- EoH (Liu et al., ICML 2024, arXiv:2401.02051) evolves natural-language "thoughts" together with code. It claims to beat FunSearch on combinatorial optimization benchmarks "with a low computational budget (in terms of the number of queries to LLMs)". — [EoH abstract](https://arxiv.org/abs/2401.02051)
- The survey "Evolutionary Computation in the Era of Large Language Model: Survey and Roadmap" (Wu et al., arXiv:2401.10034) frames the two-way interplay: EAs give LLMs black-box global search, and LLMs give EAs domain knowledge and text processing. — [survey abstract](https://arxiv.org/abs/2401.10034)

### Inferences
- The field has standardized the problem formulation as candidate = code region, fitness = `evaluate()` returning a metric dict, plus an archive with islands or QD, cascade evaluation, and prompts built from parent plus inspirations plus feedback. Differences between systems are now mostly about sample efficiency and diversity control.
- Mixing LLM-judge scores into fitness (OpenEvolve's 70/30 blend) brings a gameable proxy into the loop. That is the same failure channel Tao et al. flagged ("unreliable LLM queries to cheap models").

### Gaps
- I could not open the Sakana "AI CUDA Engineer" page (sakana.ai was blocked). The reported 2025 incident, in which evolved kernels exploited the evaluation harness to pass correctness checks, is UNVERIFIED here.
- I did not open the CodeEvolve, GEPA, LLM-SR or ReEvo papers. They are likely relevant (especially GEPA for reflective prompt evolution) but are not covered.

---

## 6. Across systems: what properties must the evaluator have, and what happens when it is a proxy?

### Takeaway
Every system assumes an evaluator that is:
1. automatic
2. executable at volume (FunSearch: at most about 20 CPU-minutes over millions of samples; AlphaEvolve: thousands of samples, up to about 100 compute-hours each)
3. deterministic or low-noise
4. graded (continuous scores beat pass/fail)
5. hard to game, ideally by making invalid candidates impossible by construction or by verifying exact properties

When the evaluator is a proxy, several things go wrong:
- Numerical approximations become exploitable: AlphaEvolve found integration exploits.
- LLM judges become exploitable.
- Small train sets overfit: OPRO, prompt evolution.
- Landscape noise causes oscillation: OPRO's 71.8 vs 49.4 wording sensitivity.

### Cited findings
- The automated-evaluator requirement is the stated main limitation in AlphaEvolve ([§6](https://arxiv.org/html/2506.13131)) and in ShinkaEvolve ([conclusion](https://arxiv.org/html/2509.19349)).
- Leaky verifiers and cheap-LLM queries were exploited, and fixing them required representation restrictions and stricter checks. — [arXiv:2511.02864](https://arxiv.org/html/2511.02864)
- A continuous score beat a discrete count for search guidance. — [arXiv:2511.02864](https://arxiv.org/html/2511.02864)
- Optimization can drift toward "stable (trivial) solutions" unless the verifier rules them out. — [arXiv:2511.02864](https://arxiv.org/html/2511.02864)
- Small training subsets used as fitness cause overfitting that OPRO tolerates only because candidates "overfit to a similar extent". — [OPRO §5.4](https://arxiv.org/html/2309.03409)
- FunSearch structurally rejects candidates that call ancestor versions, run in a sandbox with timeouts, and evolve within a skeleton. — [evaluator.py](https://raw.githubusercontent.com/google-deepmind/funsearch/main/implementation/evaluator.py)
- Cascades prune bad candidates cheaply. — [AlphaEvolve §2.4](https://arxiv.org/html/2506.13131); [OpenEvolve config](https://raw.githubusercontent.com/algorithmicsuperintelligence/openevolve/main/docs/configuration.md)

### Inferences: lessons for searching over benchmark designs (fitness against synthetic agents)

1. **Put validity in the skeleton, not in the score (FunSearch).** Make the evolvable part as small as possible: e.g. an item-generator's parameter function, or a scenario template's slot-filling policy. A fixed, trusted harness should guarantee that every candidate yields well-formed items (schema, answer key present, solvable by construction). Do not reward and then check validity after the fact. The Tao et al. integration exploit shows that an expressive representation plus an approximate check invites cheating.

2. **Expect the search to exploit the synthetic agents.** Synthetic agents play the role of the "leaky verifier". A benchmark design optimized to separate synthetic agent A from agent B can latch onto artifacts specific to those agents: their formatting quirks, token-length sensitivities, or a scripted agent's deterministic branches. Counter-measures:
   - a fixed held-out panel of synthetic agents never used during search, analogous to OPRO's validation split and ShinkaEvolve's private-test check
   - checks for the minimum over agents or over item subsets (like the min-over-vertices score that blocked cheating)
   - final verification with real models or humans

3. **Use cascades.** Stage 0: static validity (parsing, schema, dedup, answer-key consistency). Stage 1: a few cheap scripted agents and a sanity check that a known-good agent passes and a known-bad agent fails. Stage 2: the full synthetic-agent panel. Only candidates that pass all stages enter the database.

4. **Make fitness multi-objective and keep diversity.** AlphaEvolve found that multiple metrics improve even the single target. Candidate benchmark objectives: discrimination between agents of known differing ability, construct validity (agreement with an intended ordering of agents), item difficulty spread, low variance across seeds, and cost. Use MAP-Elites or signature clustering, e.g. cluster designs by their per-agent score vector, as FunSearch does with per-input signatures. This stops collapse onto one degenerate design and keeps distinct design families.

5. **Prefer continuous, low-noise fitness and correct for selection noise.** Fitness from stochastic agents behaves like OPRO's small-batch accuracy: max-of-many selection inflates scores. Re-evaluate elites on fresh seeds or items, report confidence intervals, and require gains above noise before admitting an improvement. Note FunSearch's subtle choice of scoring only the last input; aggregation choices matter.

6. **Avoid LLM-judge fitness terms, or keep them small and audited.** OpenEvolve's 70/30 judge blend and AlphaEvolve's LLM feedback are convenient. However, Tao et al. list "unreliable LLM queries to cheap models" as an exploited loophole. If an LLM judges item quality, use a strong judge, use it as a filter rather than as reward, and spot-check by hand.

7. **Choose the abstraction level deliberately.** You can evolve raw items, a constructor (an item-generating program), or a search procedure that finds items within a budget. The AlphaEvolve and Tao et al. evidence: constructors give more interpretable and generalizable designs; search-mode gives better raw scores. "Generalizer mode" fits benchmark generators that must work across parameters (difficulty levels, domains). Scoring across a family of instances improved generality, and showing only small-n prior solutions encouraged general patterns.

8. **Scale.** FunSearch-style search (millions of samples, tiny programs) needs an evaluator that runs in about minutes on one CPU. Synthetic-agent evaluation of a benchmark design is likely expensive (many LLM-agent rollouts). That points toward the AlphaEvolve and ShinkaEvolve regime: strong LLMs, rich context including rendered agent transcripts and failure artifacts, diff edits, and hundreds to low thousands of evaluations, with novelty rejection to avoid wasting evaluations on near-duplicate designs.

9. **Human expertise in the prompt matters.** Tao et al. found that expert advice in the prompt "almost always led to significantly better results". A benchmark-design search should give the LLM explicit design principles (validity criteria, known shortcut patterns to avoid) as context.

### Gaps
- I found no primary source that applies FunSearch- or AlphaEvolve-style search specifically to benchmark design with synthetic agents as the evaluator. OpenEvolve's README lists a 2026 red-teaming benchmark built with it (Trojan Hippo Bench), but I did not open that paper.
- No source I read gives a formal treatment of Goodhart effects or of statistical correction for noisy fitness in LLM-guided evolution. That lesson is my inference from OPRO's overfitting analysis and from general selection-bias reasoning.
