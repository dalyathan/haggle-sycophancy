# Quality-diversity, multi-objective and open-ended search formulations

Scope note: all sources below were opened as arXiv abstract pages, arXiv HTML full text, or arXiv PDFs (converted with pdftotext) on 2026-11-19. IEEE Xplore, pymoo.org, docs.pyribs.org, Wikipedia, eplex.cs.ucf.edu and export.arxiv.org were all blocked by the network proxy (HTTP 403), so the original NSGA-II (Deb et al. 2002), NSGA-III (Deb and Jain 2014), MOEA/D (Zhang and Li 2007), QD-score (Pugh, Soros and Stanley 2016) and MCC (Brant and Stanley 2017) papers could **not** be opened directly. Their contents are reported only as described by later primary papers that cite them, and are marked as such.

## 1. MAP-Elites, CVT-MAP-Elites, illumination vs optimization, QD-score, and LLM-based QD (QDAIF, ELM, LMX)

### Takeaway
MAP-Elites recasts search as "illumination": the user picks a performance function f(x) and N behaviour/feature dimensions b(x). Each dimension is discretized into a grid, and the algorithm keeps the single best solution ("elite") per cell. Results are judged by coverage and per-cell quality (summed as the QD-score), not by one optimum. The grid grows exponentially with the number of descriptor dimensions, which CVT-MAP-Elites fixes with a set number of Voronoi regions. LLM-based QD (ELM, LMX, QDAIF) uses language models both as the variation operator and, in QDAIF, as the judge of quality and diversity. That makes text-based candidates practical, but QDAIF reports reward hacking at the top of the judge's quality scale.

### Cited Findings
**MAP-Elites (Mouret and Clune 2015)**
- MAP-Elites "creates a map of high-performing solutions at each point in a space defined by dimensions of variation that a user gets to choose". The authors say it "tends to find a better overall solution than state-of-the-art search algorithms" because it explores more of the space. — [Mouret and Clune 2015, arXiv:1504.04909](https://arxiv.org/abs/1504.04909)
- Definitions: optimization algorithms "try to find the highest-performing solution in a search space" (or a Pareto set). "Illumination algorithms" instead "return the highest-performing solution at each point in the feature space". "Any illumination algorithm can also be used as an optimization algorithm, making illumination algorithms a superset of optimization algorithms." — [arXiv:1504.04909, §2](https://arxiv.org/abs/1504.04909)
- Formulation: the user chooses (1) a performance measure f(x) and (2) "N dimensions of variation of interest that define a feature space". A feature (behaviour) function b(x) maps each candidate to its value in each dimension. Each dimension "is discretized based on user preference or available computational resources" and can start coarse and be refined later (a hierarchical variant). — [arXiv:1504.04909, §3](https://arxiv.org/abs/1504.04909)
- Algorithm: generate G random genomes; then repeat: pick a random elite, mutate or cross it over, compute its descriptor and performance, and store it if its cell is empty or it beats the occupant. "Each member of the population is by definition diverse, at least according to the dimensions of the feature space." — [arXiv:1504.04909, Fig. 2 and §3](https://arxiv.org/abs/1504.04909)
- The paper defines four evaluation metrics:
  - Global performance: the best single solution, normalized.
  - Global reliability: the mean over all fillable cells of the best found divided by the best known for that cell, with 0 for empty cells. The authors call this "the most important measure we want an illumination algorithm to perform well on".
  - Precision (opt-in reliability): the same average, but only over cells the algorithm filled.
  - Coverage: the number of cells filled.

  — [arXiv:1504.04909, §5](https://arxiv.org/abs/1504.04909)
- On deception, the paper says hill-climbing-style search "does not work for highly deceptive problems … because in such problems one has to cross low-performing valleys to find the global optima". — [arXiv:1504.04909, §1](https://arxiv.org/abs/1504.04909)

**CVT-MAP-Elites (Vassiliades, Chatzilygeroudis and Mouret 2016)**
- Grid MAP-Elites "cannot scale to high-dimensional feature spaces since the number of regions increase exponentially with the number of dimensions". CVT-MAP-Elites uses "a centroidal Voronoi tessellation (CVT) to divide the feature space into a desired number of regions" ("a constant, pre-defined number of regions irrespective of the dimensionality"). Each individual goes into its closest region. — [Vassiliades et al. 2016, arXiv:1610.05729](https://arxiv.org/abs/1610.05729)

**QD as a field; QD-score**
- QD differs from multimodal optimization in two ways. It "typically works in the behavioral space … not in the genotypic (or parameter) space", and it "attempts to fill the whole behavior space, even if the niche is not a peak in the fitness landscape". — [Chatzilygeroudis et al. 2020, arXiv:2012.04322](https://arxiv.org/abs/2012.04322)
- QD-score: "a commonly accepted metric is the qd-score, defined as the sum of the fitnesses of the solution in each cell". MOME cites this to Pugh et al. (ref. [28]); the original paper was not opened. — [Pierrot et al. 2022 (MOME), arXiv:2202.03057](https://arxiv.org/abs/2202.03057)
- QDAIF uses the same definition: "A QD score is defined as the sum of the highest quality values found in each bin." — [Bradley et al. 2023 (QDAIF), arXiv:2310.13032](https://arxiv.org/abs/2310.13032)
- pyribs implements a "highly modular conceptual QD framework" in which users swap components to "compose algorithms from across the QD literature". The library was presented at GECCO 2023. — [Tjanaka et al. 2023, arXiv:2303.00191](https://arxiv.org/abs/2303.00191)

**LLM-based variation operators**
- ELM (Evolution through Large Models): code LLMs "can vastly improve the effectiveness of mutation operators applied to programs in genetic programming". "ELM combined with MAP-Elites generates hundreds of thousands of functional examples of Python programs" for Sodarace walkers. — [Lehman et al. 2022, arXiv:2206.08896](https://arxiv.org/abs/2206.08896)
- LMX (Language Model Crossover): "prompt a language model with a few text-based genotypes … and … parse its corresponding output as those genotypes' offspring". The paper demonstrates it on bit-strings, sentences, equations, text-to-image prompts and Python code. — [Meyerson et al. 2023, arXiv:2302.12170](https://arxiv.org/abs/2302.12170)

**QDAIF (Quality-Diversity through AI Feedback)**
- QDAIF is "an evolutionary algorithm [that] applies LMs to both generate variation and evaluate the quality and diversity of candidate text". On creative writing it "covers more of a specified search space with high-quality samples than do non-QD controls". — [arXiv:2310.13032](https://arxiv.org/abs/2310.13032)
- Mechanics:
  - Initialization uses few-shot prompting with examples chosen to span the diversity axes.
  - Mutation uses LMX-Near.
  - The diversity measure is the LM's log-probability of a label (e.g., "positive" vs "negative" sentiment).
  - Because "qualitative changes in behavior do not uniformly correspond to changes in the logits" (LM calibration), the authors use "custom non-uniform bins, which are denser towards range ends".

  — [arXiv:2310.13032, §3](https://arxiv.org/abs/2310.13032)
- Human study (averaged over three domains): QDAIF had a human QD score of 0.772 vs 0.767 for Fixed-Few-Shot, 0.650 for LMX Quality-Only and 0.606 for Random-Search. Human-AI agreement was 0.833 for QDAIF. Fixed-Few-Shot had a higher mean human quality rating (4.133 vs 3.900). — [arXiv:2310.13032, Table 1](https://arxiv.org/abs/2310.13032)
- QDAIF "still requires specified definitions of diversity axes". The paper argues that "pre-trained surrogate models [are] more prone to reward hacking in the natural language case". — [arXiv:2310.13032, §2 and §6](https://arxiv.org/abs/2310.13032)
- QDHF learns diversity metrics instead: it "progressively infers diversity metrics from human judgments of similarity among solutions", because QD "often rel[ies] on manually crafted diversity metrics". — [Ding et al. 2023 (ICML 2024), arXiv:2310.12103](https://arxiv.org/abs/2310.12103)
- Rainbow Teaming casts adversarial prompt generation "as a quality-diversity problem". It uses a discrete grid over "Risk Category and Attack Style", an LLM mutator, and a judge LLM. The paper reports attack success "exceeding 90% across all tested models". — [Samvelyan et al. 2024, arXiv:2402.16822](https://arxiv.org/abs/2402.16822)

### Inferences
- Illumination changes the deliverable from "the best x" to "a map of the best x for each kind of x". For a design space where no single optimum is well defined, the archive itself is the result.
- With 10 bins per dimension, a 7-D grid would have 10^7 cells. This follows from the exponential scaling stated in arXiv:1610.05729. Any design that puts many fitness components into descriptors needs CVT-style or unstructured archives.

### Gaps
- The original QD-score paper (Pugh, Soros and Stanley 2016, Frontiers in Robotics and AI) was not opened. Its definition is taken from MOME and QDAIF.
- pyribs documentation (docs.pyribs.org) was blocked. Only the pyribs paper abstract was verified.

## 2. NSGA-II, NSGA-III and many-objective degradation; remedies (decomposition/MOEA-D, reference points, objective reduction, hypervolume)

### Takeaway
NSGA-II ranks the population by non-dominated sorting and breaks ties with crowding distance. Crowding distance treats each objective independently, and runtime analyses now prove that NSGA-II fails to cover the Pareto front of even simple problems once there are 3 or more objectives. NSGA-III replaces crowding with reference points on a normalized hyperplane and has provable guarantees for many objectives, if the number of reference points is sized to the front. MOEA/D decomposes the problem into scalar subproblems defined by weight vectors. Hypervolume-based selection is principled, but computing exact hypervolume contributions is #P-hard.

### Cited Findings
- NSGA-II "is used for few objectives such as 2 and 3, NSGA-III is designed to deal with a larger number of objectives". The first runtime analyses of NSGA-III "for more than 3 objectives" show how to scale the number of reference points and the population size with problem dimension, number of objectives and fitness range. — [Opris et al. 2024 (GECCO), arXiv:2404.11433](https://arxiv.org/abs/2404.11433)
- NSGA-II "cannot compute the full Pareto front … in sub-exponential time when the number of objectives is at least three", even on m-objective OneMinMax "where every solution is Pareto optimal" and even with large populations. The cause: "in the computation of the crowding distance, the different objectives are regarded independently". — [Zheng and Doerr (IEEE TEVC), arXiv:2211.13084](https://arxiv.org/abs/2211.13084)
- The same paper explains the mechanism. Crowding distance "is computed as the sum of the crowding distance contributions … in each objective". On OneMinMax with ≥3 objectives, most individuals get crowding distance zero, "hence the selection between them is fully at random". It also cites earlier empirical findings (Khare, Yao and Deb 2003) that NSGA-II "increasingly suffers in converging to the global Pareto front when the number of objectives increases". — [arXiv:2211.13084 (HTML)](https://arxiv.org/html/2211.13084)
- NSGA-II needs a population larger than the Pareto front. With a population four times the front size it matches the runtime guarantees of SEMO/GSEMO. With a population equal to the front size, "for an exponential number of iterations, the population will always miss a constant fraction of the Pareto front". — [Zheng and Doerr, arXiv:2112.08581](https://arxiv.org/abs/2112.08581)
- NSGA-III "replaces the crowding distance … by a procedure involving reference points". These points are "typically distributed in some structured manner on the normalized hyperplane". NSGA-III "normalizes the objective functions and associates each individual with a reference point". With reference points "a small constant factor more than the size of the Pareto front", NSGA-III finds the full front of 3-objective OneMinMax in expected O(n log n) iterations, "a drastic advantage of the NSGA-III over the NSGA-II". — [Wietheger and Doerr (IJCAI 2023), arXiv:2211.08202](https://arxiv.org/abs/2211.08202) (description of the original Deb and Jain 2014 [DJ14] algorithm as reported in this paper)
- Each algorithm has a different implicit target ("best solution set"):
  - SMS-EMOA: hypervolume maximization.
  - NSGA-III: intersection points of the reference lines with the front.
  - MOEA/D: the optimum of each subproblem.
  - NSGA-II "is not based on any clear criterion to be optimized".

  — [Ishibuchi and Pang 2025, arXiv:2504.17222](https://arxiv.org/abs/2504.17222)
- MOEA/D (decomposition):
  - It uses weight vectors to define scalar subproblems. Neighbourhoods are "determined by the Euclidean distance of its corresponding weight vector". Mating and replacement happen within neighbourhoods.
  - Subproblem formulations include Weighted Sum ("a convex combination of all individual objectives"), Tchebycheff, and PBI ("a variant of the normal-boundary intersection method").
  - Weight-vector setting and adaptation are core design components.
  - Constraint handling "has surprisingly been ignored … in the seminal paper of MOEA/D".

  — [Li 2024 survey, arXiv:2404.14571](https://arxiv.org/abs/2404.14571)
- Hypervolume: "exact calculation of the hypervolume contribution is #P-hard while its approximation is NP-hard". Deciding which solution contributes least is NP-hard. A randomized (ε, δ) approximation is nonetheless fast in practice (e.g., 10,000 solutions in 100 dimensions in seconds). — [Bringmann and Friedrich, arXiv:0812.2636](https://arxiv.org/abs/0812.2636)
- MOME combines QD and multi-objective optimization. It fills "each cell with a Pareto Front" and optimizes the MOQD score: the sum over cells of each cell's front hypervolume. Fronts have "a maximum size P. If this size is reached, solutions are replaced randomly in the front." MOME was evaluated on two-objective tasks. — [Pierrot et al. 2022, arXiv:2202.03057](https://arxiv.org/abs/2202.03057)

### Inferences
- With 7 objectives, NSGA-II's crowding distance is a poor diversity mechanism in theory (proved failure at ≥3 objectives on a simple benchmark). Reference-point methods (NSGA-III) or decomposition (MOEA/D) are the established remedies. Both need a number of reference points or weight vectors comparable to the size of the front you want, and that number grows combinatorially with the number of objectives.
- Exact hypervolume in 7-D is expensive, and hypervolume contributions are #P-hard. If hypervolume is used as an archive metric (as in MOME's MOQD score), approximate or Monte-Carlo estimation is likely required.

### Gaps
- I could not open the original NSGA-II (IEEE TEVC 2002), NSGA-III (IEEE TEVC 2014) or MOEA/D (IEEE TEVC 2007) papers; IEEE Xplore was blocked. Algorithm details come from the runtime-analysis papers and the MOEA/D survey.
- The commonly cited explanation that "the fraction of mutually non-dominated solutions grows with the number of objectives, so Pareto dominance loses selection pressure" was **not verified** against a primary source in this session.
- Objective-reduction methods (e.g., PCA-based or correlation-based reduction of redundant objectives) were **not verified**. My arXiv searches for them returned no relevant results.

## 3. Constraints vs objectives (epsilon-constraint) and scalarization pitfalls

### Takeaway
The verified sources support three pitfalls with scalarization. A weighted sum (a convex combination) has trouble reaching non-convex regions of the front. Any fixed-scale scalar score saturates. Weighted-sum and Tchebycheff subproblems implicitly encode preferences. Open-ended methods (MCC, POET, OMNI-EPIC) treat some criteria as pass/fail filters ("minimal criteria") rather than objectives. I could not open a primary source for the epsilon-constraint method itself.

### Cited Findings
- The MOEA/D survey describes "localized WS" variants designed so that "solution(s) lying in the non-convex region survive". This implies that plain weighted-sum subproblems lose such solutions. — [Li 2024, arXiv:2404.14571](https://arxiv.org/abs/2404.14571)
- Saturation of fixed-scale evaluators: "the score of any numerical evaluator with a fixed scale can be maximised, at which point it is impossible to identify better candidate prompts, resulting in minimal updates in the archive". Rainbow Teaming therefore uses a pairwise preference model instead. — [Samvelyan et al. 2024, arXiv:2402.16822 (HTML)](https://arxiv.org/html/2402.16822)
- Constraint handling in MOEA/D falls into "three categories". Traditional methods "prioritize driving the population toward feasible regions before addressing the balance between convergence and diversity". — [Li 2024, arXiv:2404.14571](https://arxiv.org/abs/2404.14571)
- Minimal criterion as a constraint (MCC, as described in POET): members of each population "earn the right to reproduce by satisfying a minimal criterion … with respect to the other population". Mazes must be solved by at least one solver, and solvers must solve at least one maze. — [Wang et al. 2019 (POET), arXiv:1901.01753](https://arxiv.org/abs/1901.01753)
- POET's concrete minimal criterion is a band filter on the score: "50 ≤ E_child(θ_child) ≤ 300" removes child environments that are too hard or too easy. — [arXiv:1901.01753](https://arxiv.org/abs/1901.01753)
- MOME argues that diversity "is crucial for decision making where the highest performing solution is not always the best, as some properties are not possible to translate into objectives". — [arXiv:2202.03057](https://arxiv.org/abs/2202.03057)

### Inferences
- A practical split for a multi-component fitness: (a) hard validity or feasibility components become minimal criteria or constraints (pass/fail or band filters, as in POET); (b) a few components with real trade-offs stay as Pareto objectives; (c) categorical or "kind-of" components become behaviour descriptors for QD.
- Any weighted sum of the components imposes an arbitrary preference and can lose non-convex trade-offs. If the components are LLM-judged scores on a fixed scale, they can also saturate.

### Gaps
- No primary source for the epsilon-constraint method (Haimes et al. 1971) or for weighted-sum non-convexity theory (e.g., Das and Dennis 1997) could be opened. Publisher sites and Wikipedia were blocked, and the arXiv search was unproductive. Treat these as **unverified** standard textbook knowledge.

## 4. Open-ended search: POET, Enhanced POET, OMNI, OMNI-EPIC and MCC — co-evolving problems and solvers, and defining "interesting"

### Takeaway
These systems search over problems as well as solutions.
- **MCC:** co-evolves problems and solvers under mutual minimal criteria.
- **POET:** adds per-environment optimization, cross-environment transfer, a too-easy/too-hard filter and novelty ranking.
- **Enhanced POET:** defines environment novelty in a domain-general way, by how an environment *ranks all agents* (PATA-EC), and measures progress with ANNECS.
- **OMNI:** uses a foundation model as a "Model of Interestingness" on top of learnability.
- **OMNI-EPIC:** has LLMs write environments and success checks as code, filtered by a post-generation interestingness check against an unbounded archive.

### Cited Findings
**MCC (as described in POET; original not opened)**
- MCC "pairs a population of evolving problems … with a co-evolving population of solutions". It works "without any behavior characterization or archive", yet "there is no force for optimization within each environment", and "complexity can only arise through drift". — [arXiv:1901.01753, §2.2](https://arxiv.org/abs/1901.01753)

**POET (Wang et al. 2019)**
- POET "pairs the generation of environmental challenges and the optimization of agents to solve those challenges", and "allows these stepping-stone solutions to transfer between problems". — [arXiv:1901.01753](https://arxiv.org/abs/1901.01753)
- Main loop: (1) generate new environments by mutating active ones, (2) optimize paired agents, (3) attempt transfers.
- A new environment is admitted only if (a) its parent's agent "exhibited sufficient progress" and (b) it is "neither too hard nor too easy". Priority goes to "candidate environments that are most novel".
- The active population is capped at `capacity`; "the oldest environments are removed to make room (as in a queue)". `max_admitted` caps admissions per iteration.

  — [arXiv:1901.01753, §3 and supplement](https://arxiv.org/abs/1901.01753)
- Original POET computes novelty on the environment encoding: "in POET in effect novelty is a genetic diversity measure". — [arXiv:1901.01753](https://arxiv.org/abs/1901.01753)

**Enhanced POET (Wang et al. 2020)**
- The original POET's environment characterization was "hand-coded to fit the specific domain". The authors call this "a key limitation … the system's output will be bound to exploration only within such prescripted possibilities". — [arXiv:2003.08536](https://arxiv.org/abs/2003.08536)
- PATA-EC (Performance of All Transferred Agents Environment Characterization):
  1. Evaluate all active and archived agents in the environment.
  2. Clip scores between lower and upper bounds, because "a score that is too low indicates outright failure … too high hints that an agent is already competent".
  3. Rank-normalize to [−0.5, 0.5].
  4. Use Euclidean distance between the resulting vectors.

  The authors summarize: "if a newly-generated environment induces a significantly distinct ordering on how agents perform within it … it likely poses a qualitatively new kind of challenge". Novelty is the mean distance to the k = 5 nearest neighbours among active and archived environments. — [arXiv:2003.08536, §3](https://arxiv.org/abs/2003.08536)
- ANNECS (Accumulated Number of Novel Environments Created and Solved) counts an environment only if it (1) passes the minimal criterion against all agents generated so far and (2) is eventually solved. The rationale: if existing agents can solve all future challenges, "the system has not generated any meaningfully new challenges". A typical run is 60,000 iterations with 40 active environments, taking about 12 days on 750 CPU cores. — [arXiv:2003.08536, §5](https://arxiv.org/abs/2003.08536)

**OMNI (Zhang et al. 2023)**
- "Even after filtering for tasks the current agent can learn (i.e., learning progress), countless learnable yet uninteresting tasks remain (e.g., minor variations of previously learned tasks)." OMNI uses foundation models "as a model of interestingness (MoI)" and outperforms "uniform task sampling or learning progress alone". — [arXiv:2306.01711](https://arxiv.org/abs/2306.01711)

**OMNI-EPIC (Faldor et al. 2024, ICLR 2025)**
- OMNI-EPIC "generate[s] code specifying the next learnable (i.e., not too easy or difficult …) and interesting (e.g., worthwhile and novel) tasks". This covers "both environments … and reward functions". — [arXiv:2405.15568](https://arxiv.org/abs/2405.15568)
- Pipeline:
  - A task archive holds learned and failed tasks and starts from a few natural-language seeds. It "is unbounded and can grow indefinitely".
  - The task generator LLM is conditioned on the most similar archived tasks, retrieved by embedding similarity because of context limits.
  - A "post-generation MoI" compares the new task with the most similar archived tasks and discards it if uninteresting.
  - A DreamerV3 agent is trained, and a success detector checks completion.
  - Failed tasks are retried up to a maximum number of times, then archived as failed.

  — [arXiv:2405.15568, §3](https://arxiv.org/abs/2405.15568)
- Success detector: "current VLMs are not yet accurate enough to be used as success detectors", so the system has the LLM generate a separate `get_success` function. The authors say this function "is less susceptible to reward hacking, as it does not affect how the agent learn[s]", unlike the shaped reward function. — [arXiv:2405.15568, §3.6](https://arxiv.org/abs/2405.15568)
- ANNECS-OMNI adds a third criterion to ANNECS: the task must be judged interesting compared with previous tasks. The authors note that "ANNECS lacks a measure of how interesting or novel the newly generated task is". — [arXiv:2405.15568, §4](https://arxiv.org/abs/2405.15568)

### Inferences
- PATA-EC is directly reusable for benchmark design: two benchmark designs differ meaningfully if they rank a fixed panel of models differently. Clipping at both ends discards designs that every model fails or every model aces.
- POET's band filter and ANNECS's "created and eventually solved" are templates for a minimal criterion on benchmark designs: discriminative, neither saturated nor impossible.

### Gaps
- The original MCC paper (Brant and Stanley, GECCO 2017) could not be opened; eplex.cs.ucf.edu was blocked and there is no arXiv version. MCC is described only via POET.
- I did not open OMNI's exact MoI prompt or OMNI-EPIC's appendix prompts beyond the main-text descriptions.

## 5. Reported failure modes: deceptive objectives, archive bloat, descriptor choice dominating outcomes, evaluator exploitation

### Takeaway
The primary sources report four failure modes, each with documented mitigations:
- **Deception:** greedy objective-following fails when low-fitness valleys must be crossed.
- **Archive growth and topology limits:** exponential grids, unknown descriptor bounds, hard-to-tune distance thresholds, unbounded archives and context-length limits.
- **Descriptor choice:** it "completely changes the solution types".
- **Evaluator exploitation (reward hacking):** documented for LLM judges (QDAIF), predicted for fixed-scale scorers (Rainbow Teaming), and catalogued as a general property of evolutionary search.

### Cited Findings
- Deception: following "the heuristic that random changes to good solutions lead to better solutions … does not work for highly deceptive problems". — [arXiv:1504.04909](https://arxiv.org/abs/1504.04909)
- POET reports that many of its challenges "cannot be solved by direct optimization alone, or even through a direct-path curriculum". — [arXiv:1901.01753](https://arxiv.org/abs/1901.01753)
- Descriptor choice: "The choice of a behavioral descriptor is crucial, as it completely changes the solution types that the algorithm derives." AURORA learns descriptors via unsupervised dimensionality reduction instead. — [Cully 2019, arXiv:1905.11874](https://arxiv.org/abs/1905.11874)
- QDAIF had to use non-uniform bins because LM-logit diversity measures are non-linearly calibrated. It also notes that QDAIF "still requires specified definitions of diversity axes". — [arXiv:2310.13032](https://arxiv.org/abs/2310.13032)
- Archive and grid limits:
  - "The MAP-Elites grid is limited … when the achievable descriptor space a) has a complex topological shape, b) is discontinuous, c) is unbounded or d) is high-dimensional."
  - Grid bounds "must often be determined experimentally". Some cells "may map to regions … where no valid solutions can exist".
  - Unstructured archives use "a fixed distance threshold" that "proves particularly challenging to tune … leading to … container size control".
  - Dominated Novelty Search reformulates local competition as a fitness transformation "eliminating the need for predefined bounds or parameters".

  — [Bahlous-Boldi et al. 2025, arXiv:2502.00593](https://arxiv.org/abs/2502.00593)
- Archive bloat and boundedness:
  - OMNI-EPIC's archive "is unbounded and can grow indefinitely". It therefore retrieves only the most similar tasks for context. The authors flag possible "cyclic behavior where the task generator alternates between generating task types that are consistently rejected due to their similarity to existing tasks in the archive".
  - POET bounds its active set with a FIFO `capacity`.
  - MOME caps each cell's Pareto front at P and replaces solutions randomly when the cap is hit.

  — [arXiv:2405.15568](https://arxiv.org/abs/2405.15568); [arXiv:1901.01753](https://arxiv.org/abs/1901.01753); [arXiv:2202.03057](https://arxiv.org/abs/2202.03057)
- Evaluator exploitation (LLM judge): "we suspect reward hacking happening when using LMs to generate feedback … the correlation drops when the evaluated quality is in the range 0.995 to 1. The text generation might have exploited certain attributes or phrasings that allow an LM to give a high-quality estimate, but not what humans would agree is good."
  - The suggested mitigations are RLHF-tuned detectors and "an ensemble of different AI models … from models having uncorrelated blind spots".
  - Zero-shot-initialized runs had a subjective QD score of 0.383, vs 0.772 for seeded runs, which the authors read as "potential reward hacking".

  — [arXiv:2310.13032, §6 and appendix](https://arxiv.org/abs/2310.13032)
- Evaluator exploitation (fixed scales): pairwise comparisons have "higher agreement with humans than … single-answer grading … particularly true in an optimisation context, which introduces the risk of reward hacking the evaluator". Fixed-scale scores saturate. Rainbow Teaming also measures attack success with separate classifiers (GPT-4 with a specialised prompt, and Llama Guard). — [arXiv:2402.16822 (HTML)](https://arxiv.org/html/2402.16822)
- Rainbow Teaming filters out mutated prompts that have "high BLEU scores with respect to their parents", to enforce diversity. — [arXiv:2402.16822](https://arxiv.org/html/2402.16822)
- General property of evolutionary search: researchers "have observed their evolving algorithms and organisms subverting their intentions, exposing unrecognized bugs in their code". This is a crowd-sourced, fact-checked collection of anecdotes. — [Lehman et al. 2018, arXiv:1803.03453](https://arxiv.org/abs/1803.03453)
- Interestingness-only filtering is insufficient on its own: OMNI notes that learnable tasks include "countless … uninteresting tasks (e.g., minor variations of previously learned tasks)". — [arXiv:2306.01711](https://arxiv.org/abs/2306.01711)

### Inferences
- When the evaluator is an LLM or a heuristic scorer, the top of its scale is where exploitation concentrates (QDAIF's 0.995–1 band). Archive elites are by construction the highest-scoring items per cell, so they are the items most likely to be exploits. Elites therefore need held-out verification.

### Gaps
- I found no primary-source quantification of "archive bloat" in novelty-search archives (e.g., archive size vs. runtime). Only the qualitative statements above were verified.

## 6. Lessons for searching benchmark designs scored by a 7-component fitness vector (no single well-defined optimum)

### Takeaway
Do not scalarize all 7 components and run NSGA-II on them. Instead:
- Partition the components into (a) minimal-criterion constraints, (b) a small set of true trade-off objectives, and (c) behaviour descriptors.
- Run a QD or MOQD archive (CVT-MAP-Elites or MOME-style per-cell fronts, or NSGA-III/MOEA-D if the job is purely front-finding).
- Measure success with archive-level metrics (QD-score, coverage, ANNECS-style counts).
- Treat any LLM-judged component as exploitable: verify elites with a pairwise judge and independent evaluators.

### Cited Findings
- NSGA-II crowding distance provably fails at ≥3 objectives, while NSGA-III with enough reference points succeeds. — [arXiv:2211.13084](https://arxiv.org/abs/2211.13084); [arXiv:2211.08202](https://arxiv.org/abs/2211.08202); [arXiv:2404.11433](https://arxiv.org/abs/2404.11433)
- Grid cell counts grow exponentially with the number of descriptor dimensions; CVT gives a fixed region count. — [arXiv:1610.05729](https://arxiv.org/abs/1610.05729)
- MOME keeps a Pareto front per descriptor cell and reports the MOQD score (the sum of per-cell hypervolumes). — [arXiv:2202.03057](https://arxiv.org/abs/2202.03057)
- Hypervolume contributions are #P-hard to compute exactly. — [arXiv:0812.2636](https://arxiv.org/abs/0812.2636)
- Minimal criteria act as band filters (POET: 50 ≤ score ≤ 300). — [arXiv:1901.01753](https://arxiv.org/abs/1901.01753)
- Characterizing designs by how they rank agents (PATA-EC) is domain-general. — [arXiv:2003.08536](https://arxiv.org/abs/2003.08536)
- Fixed-scale judges saturate and invite reward hacking; pairwise preference judges are more robust in optimization loops. — [arXiv:2402.16822](https://arxiv.org/html/2402.16822)
- LLM-judge reward hacking concentrates at the top of the score range. — [arXiv:2310.13032](https://arxiv.org/abs/2310.13032)
- Interestingness should be judged against the archive (retrieval of the most similar items plus an FM judge). — [arXiv:2405.15568](https://arxiv.org/abs/2405.15568)

### Inferences
These are my synthesis for the report writer, not claims from the sources.
1. **Decide what "optimum" means before choosing an algorithm.** With 7 components, the output should be an *archive*: Pareto fronts per descriptor niche, or elites per niche. Report QD-score or MOQD-score, coverage, and per-cell reliability (MAP-Elites' metrics) rather than a single winner.
2. **Demote components.**
   - Components that are really validity checks (e.g., solvability, determinism, no leakage) should be minimal criteria or band filters, as in POET or the minimal criterion in MCC.
   - Components describing *what kind* of design it is (domain, tactic, difficulty profile) are behaviour descriptors.
   - Only components with genuine trade-offs remain objectives. Fewer objectives makes Pareto ranking far more informative.
3. **If all 7 must stay objectives,** use NSGA-III with reference points sized to the desired archive, or MOEA/D with weight vectors. Avoid NSGA-II crowding distance. Avoid exact hypervolume selection in 7-D because of the #P-hardness of contributions; approximate it.
4. **Use a PATA-EC-style descriptor** for benchmark designs. Characterize each design by the clipped, rank-normalized vector of scores it gives a fixed panel of models. Two designs are distinct if they *order models differently*. This is domain-general and directly measures what a benchmark is for: discrimination. Clip at both ends to discard saturated and impossible designs.
5. **Use an ANNECS-like progress measure:** count designs that pass the minimal criterion against all models seen so far and that remain discriminative. This is better than tracking the maximum of any single component.
6. **Guard against evaluator exploitation.**
   - LLM-judged components will be gamed at the top of their scale (QDAIF).
   - Use pairwise comparisons, judge ensembles with uncorrelated blind spots, and separate held-out verification judges (as Rainbow Teaming does with GPT-4 and Llama Guard).
   - Keep deterministic or code-based checks, as OMNI-EPIC does with `get_success`, apart from whatever signal drives the search.
7. **Choose descriptors deliberately.** Descriptor choice "completely changes the solution types". Consider learned descriptors (AURORA, QDHF) or several descriptor sets, and report how sensitive the conclusions are to that choice. If a descriptor comes from LM logits, bin it non-uniformly (QDAIF).
8. **Bound the archive.** Use a FIFO capacity (POET), per-cell front caps (MOME) or CVT regions. Retrieve only the most similar items when an LLM must see the archive (OMNI-EPIC). Watch for cyclic rejection.

### Gaps
- I found no primary source that applies QD or EMO specifically to *benchmark-design* search with a multi-component fitness vector. Closest analogues: Rainbow Teaming (QD over adversarial prompts), OMNI-EPIC (LLM-generated tasks as code), and POET/Enhanced POET (co-evolved environments).
- No source verified the claim that 7 objectives is "too many" for any specific algorithm. Runtime results cover constant m in general (NSGA-III) and m ≥ 3 for the NSGA-II failure.
