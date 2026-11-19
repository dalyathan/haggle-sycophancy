# Configuration spaces and architecture search spaces in AutoML: formal definition, search algorithms, and NAS evaluation lessons

Scope note: current as of 2026-11-19. Every claim below was checked against a primary source that was actually opened (docs, source code, or the paper full text via arXiv PDF). ConfigSpace and SMAC3 claims come from the installed ConfigSpace 1.2.2 package (PyPI) and from `raw.githubusercontent.com/automl/{ConfigSpace,SMAC3}/main`. Some behaviours were also tested directly in a scratch venv; those are marked "[verified by experiment]". Anything not verified is marked UNVERIFIED or listed under Gaps.

---

## 1. ConfigSpace (AutoML Freiburg): hyperparameter types, conditions, forbidden clauses, sampling, neighbourhoods, hierarchical spaces

### Takeaway
ConfigSpace represents a search space as a set of typed hyperparameters plus two kinds of constraint. **Conditions** form an acyclic parent→child activation structure, so they express hierarchy. **Forbidden clauses** reject combinations of values. Internally each configuration is a numeric vector in which inactive hyperparameters are NaN. Sampling draws from each hyperparameter's distribution, then rejects forbidden rows and blanks out inactive children. Neighbourhoods follow the one-exchange definition from SMAC: change one active hyperparameter at a time. There is **no native subset or multiset type**, so subset-valued axes have to be encoded, for example as one boolean per element with forbidden clauses on top.

### Cited Findings
**Hyperparameter types**
- The package's public classes (ConfigSpace 1.2.2) include `CategoricalHyperparameter`, `OrdinalHyperparameter`, `UniformInteger/UniformFloat`, `NormalInteger/NormalFloat`, `BetaInteger/BetaFloat` and `Constant`. They also include convenience constructors `Float(bounds, log=, distribution=)`, `Integer(...)` and `Categorical(items, weights=, ordered=)`. — [ConfigSpace hyperparameters reference](https://raw.githubusercontent.com/automl/ConfigSpace/main/docs/reference/hyperparameters.md); package source `ConfigSpace/hyperparameters/` (installed from [PyPI ConfigSpace 1.2.2](https://pypi.org/project/ConfigSpace/))
- Shorthand: `ConfigurationSpace({"myfloat": (0.1, 1.5), "myint": (2, 10), "species": ["mouse","cat","dog"]})` creates a uniform float, a uniform integer and a categorical. Integers and floats accept `log=True`. Categoricals accept sampling `weights`. — [ConfigSpace docs index](https://raw.githubusercontent.com/automl/ConfigSpace/main/docs/index.md)
- Ordinal docstring: "An ordinal hyperparameter is a hyperparameter that can take on one of a fixed number of arbitrary values. The values are ordered and the order is defined by the sequence in which they are passed". The class sets `ORDERABLE = True`. — ConfigSpace source `hyperparameters/ordinal.py` ([repo raw root](https://raw.githubusercontent.com/automl/ConfigSpace/main/README.md); file read from the installed 1.2.2 package)
- ConfigSpace 1.1 removed the `q` (quantization) parameter for numerical hyperparameters. The maintainers recommend "using an `Ordinal` distribution where possible". Version 1.1 also dropped the Cython dependency and added support for arbitrary Python objects as categorical, ordinal or constant values. — [ConfigSpace docs index](https://raw.githubusercontent.com/automl/ConfigSpace/main/docs/index.md)
- Priors: hyperparameters can carry Normal or Beta priors, or categorical weights. SMAC uses these priors through πBO. — [ConfigSpace user guide, 5th example](https://raw.githubusercontent.com/automl/ConfigSpace/main/docs/guide.md)

**Conditions (hierarchy)**
- Available condition types: `EqualsCondition`, `NotEqualsCondition`, `LessThanCondition`, `GreaterThanCondition` and `InCondition`. They combine through `AndConjunction` and `OrConjunction`. — [Conditions reference](https://raw.githubusercontent.com/automl/ConfigSpace/main/docs/reference/conditions.md)
- Semantics, quoted from the guide: "Conditions work by constraining a child hyperparameter (the first argument) on its parent hyperparameter (the second argument) being in a certain relation to a value". For example, `EqualsCondition(degree, kernel_type, 'poly')` means "degree is active if kernel_type == 'poly'". The guide also says ConfigSpace samples conditional hyperparameters "only if their condition is met". — [ConfigSpace user guide](https://raw.githubusercontent.com/automl/ConfigSpace/main/docs/guide.md)
- The docs warn against `EqualsCondition` and `InCondition` on float hyperparameters, because numerical rounding can make the condition evaluate to False. — [Conditions reference](https://raw.githubusercontent.com/automl/ConfigSpace/main/docs/reference/conditions.md)
- A child can have only one parent condition. Adding a second condition on the same child raises `AmbiguousConditionError` ("Adding a second parent condition for a hyperparameter is ambiguous and therefore forbidden. Use an `OrConjunction` or `AndConjunction`"). Mutual conditions raise `CyclicDependancyError`. [verified by experiment on ConfigSpace 1.2.2] — package source `ConfigSpace/conditions.py`, `_condition_tree.py` ([PyPI](https://pypi.org/project/ConfigSpace/))

**Forbidden clauses**
- Static forbidden clauses are `ForbiddenEqualsClause`, `ForbiddenInClause`, `ForbiddenLessThan(Equals)Clause` and `ForbiddenGreaterThan(Equals)Clause`. They combine with `ForbiddenAndConjunction` and `ForbiddenOrConjunction`. Relational clauses compare two hyperparameters: `ForbiddenEqualsRelation`, `ForbiddenLessThanRelation`, `ForbiddenGreaterThanRelation` and the `...Equals...` variants. — [Forbiddens reference](https://raw.githubusercontent.com/automl/ConfigSpace/main/docs/reference/forbiddens.md)
- The guide's LinearSVC example forbids invalid `penalty`/`loss`/`dual` combinations with `ForbiddenAndConjunction(ForbiddenEqualsClause(...), ...)`. It notes: "It is possible to represent these as conditionals, however sometimes it is easier to express them as forbidden clauses." — [ConfigSpace user guide](https://raw.githubusercontent.com/automl/ConfigSpace/main/docs/guide.md)
- The default configuration must itself be legal. Adding a forbidden clause that matches the default raises `ForbiddenValueError` (`_check_default_configuration`). For example, a "subset must be non-empty" clause failed while all booleans defaulted to False. [verified by experiment] — package source `configuration_space.py` ([PyPI](https://pypi.org/project/ConfigSpace/))

**Representation and sampling**
- A `Configuration` is dict-like. "Underneath the hood, there is some vectorized representation … e.g. `np.array([0.32, 1])`", which you get with `get_array()`. — [Configuration reference](https://raw.githubusercontent.com/automl/ConfigSpace/main/docs/reference/configuration.md)
- In the vector, categoricals and ordinals are stored as indices (an ordinal value "l" in `[s,m,l]` became 2.0). Floats are normalized to [0,1], in log space when `log=True`. Inactive conditional hyperparameters are `NaN`. [verified by experiment; `get_array()` output `[0., 0.384, 2., 1., 0., 1., nan]`]
- `sample_configuration` works by rejection. It draws a matrix of vectors from each hyperparameter's vector distribution, removes rows that hit any unconditional forbidden clause ("We treat this as an OR"), and sets each child to NaN where its condition is unsatisfied (`valid_configs[np.ix_(cnode.children_indices, ~satisfied)] = np.nan`). It oversamples by a factor based on `(len(forbidden_clauses)+len(conditional_hyperparameters))/num_hyperparameters`. — package source `configuration_space.py` lines ~531–606 ([PyPI ConfigSpace 1.2.2](https://pypi.org/project/ConfigSpace/))

**Neighbourhoods**
- `get_one_exchange_neighbourhood(configuration, seed, num_neighbors=4, stdev=0.2)` is "implemented as defined by Hutter, Hoos and Leyton-Brown, Sequential Model-Based Optimization for General Algorithm Configuration (LION 5)". Each neighbour differs from the input configuration in one active hyperparameter. — package source `ConfigSpace/util.py` ([PyPI](https://pypi.org/project/ConfigSpace/))
- How each type is handled in that code:
  - Inactive (NaN) and size-1 hyperparameters are skipped.
  - **Categorical**: every other value is a neighbour (`hp.size - 1` neighbours, and `num_neighbors` is ignored).
  - **Ordinal**: "We can only generate maximum 2 neighbors for Ordinals", meaning the adjacent values.
  - **Continuous**: Gaussian perturbation with `stdev` in the normalized space, oversampled ×5.
  - **Finite integers**: up to `num_neighbors`, using stdev for uniform integers.
  - The number of samples drawn per hyperparameter is scaled by `1+sqrt(#forbiddens on that hp)` so that enough legal neighbours survive. — `ConfigSpace/util.py` lines 108–230 (same source)

**Ecosystem**
- ConfigSpace is used by SMAC3, BOHB (HpBandSter) and auto-sklearn. It supports serialization to dict, YAML, JSON and the older `pcs` format. — [ConfigSpace docs index](https://raw.githubusercontent.com/automl/ConfigSpace/main/docs/index.md); [user guide, 4th example](https://raw.githubusercontent.com/automl/ConfigSpace/main/docs/guide.md)

### Inferences
- ConfigSpace's formal model is: a product of typed domains, an acyclic activation graph in which each child has exactly one (possibly compound) parent condition, and a set of forbidden predicates (a blacklist). The legal set is all assignments that respect activation and match no forbidden predicate. This matches the "tree-structured" (more precisely DAG-structured) spaces that TPE and SMAC target (see §2).
- Forbidden clauses are enforced by rejection in both sampling and neighbourhood generation. If the forbidden region is large, sampling efficiency degrades, and a space whose legal region is a small fraction of the product space should be restructured with conditions or merged axes.
- Ordinal versus categorical changes how optimizers move through the space. Ordinals have two neighbours; categoricals have all k−1 others. Encoding an ordered axis as categorical therefore discards locality information.

### Gaps
- I did not find documentation of formal semantics for a forbidden clause that refers to a currently inactive hyperparameter. A test sampling space with such a clause ran without error, but I did not check what the clause actually matched. UNVERIFIED.
- No subset, permutation or multiset hyperparameter type exists in ConfigSpace 1.2.2 (no such class in the package). Encodings for these are the user's responsibility.

---

## 2. SMAC, TPE, BOHB, successive halving and Hyperband: formulations and when each fits

### Takeaway
SMAC uses a random-forest surrogate, which handles categorical and conditional (imputed) dimensions natively. It finds candidates by local search plus random sampling, and races challengers against the incumbent ("intensification"). TPE models p(x|y) with two densities, one for good and one for bad observations, and maximizes their ratio. Because it factorizes per dimension, conditional ("tree-structured") spaces are easy for it. Successive halving and Hyperband are bandit-style multi-fidelity schedulers built on random search. BOHB replaces Hyperband's random sampling with a TPE-like multivariate KDE.

### Cited Findings
**SMAC / SMAC3**
- SMAC3 describes the space as a conditional hierarchy. For example, the sub-space Λi for algorithm Ai "is only active if Ai was chosen". The paper says: "SMAC3 models these spaces by using a random forest … SMAC having been the first BO approach to use this type of model (Hutter et al., 2011). SMAC3 supports multiple levels of conditionalities". — [SMAC3 paper (Lindauer et al.), arXiv 2109.09831](https://arxiv.org/abs/2109.09831)
- The SMAC4HPO preset uses a Sobol initial design, an RF surrogate and logEI. The SMAC4AC preset adds "aggressive racing as intensification mechanism". SMAC "successfully optimized configuration spaces with more than 300 hyperparameters for SAT solvers". — [SMAC3 arXiv 2109.09831](https://arxiv.org/abs/2109.09831)
- How the RF handles inactive (NaN) values: `_impute_inactive` replaces NaN in conditional dimensions with a value outside the legal range. Categoricals get `len(choices)`, ordinals `len(sequence)`, uniform float/int `-1`, constants `1`. The trees can then split "inactive" away from every real value. — [SMAC3 abstract_random_forest.py](https://raw.githubusercontent.com/automl/SMAC3/main/smac/model/random_forest/abstract_random_forest.py)
- HPO facade defaults: `n_trees=10`, `ratio_features=1.0`. The acquisition maximizer is `LocalAndSortedRandomSearch` with `challengers=10000` and `local_search_iterations=10`. A `ProbabilityRandomDesign(probability=0.2)` interleaves random configurations. — [SMAC3 hyperparameter_optimization_facade.py](https://raw.githubusercontent.com/automl/SMAC3/main/smac/facade/hyperparameter_optimization_facade.py)
- The acquisition optimizer "performs local search from the previous best points according to the acquisition function, uses the acquisition function to sort randomly sampled configurations". Random configurations are interleaved "to circumvent issues from a constant prediction from the Random Forest model at the beginning". — [SMAC3 local_and_random_search.py](https://raw.githubusercontent.com/automl/SMAC3/main/smac/acquisition/maximizer/local_and_random_search.py)
- Intensifier: it "Races challengers against current incumbents". Queued configurations "are evaluated on N=(N*2) instances if they might be better than the incumbents. If not, they are removed from the queue and rejected forever". The default is `max_config_calls=3`. — [SMAC3 intensifier.py](https://raw.githubusercontent.com/automl/SMAC3/main/smac/intensifier/intensifier.py)
- SMAC3 also ships a `HammingKernel` for GP models over categorical inputs (an exponential of the weighted count of mismatched dimensions). — [SMAC3 hamming_kernel.py](https://raw.githubusercontent.com/automl/SMAC3/main/smac/model/gaussian_process/kernels/hamming_kernel.py)

**TPE**
- From Watanabe's TPE tutorial: "The name comes from the method being able to handle a tree-structured search space, and using Parzen estimators, aka kernel density estimators (KDEs)". The tutorial defines a tree-structured space as one "that includes some conditional parameters". TPE models p(x|y) as p(x|D(l)) when y ≤ y^γ and p(x|D(g)) otherwise. The acquisition is the density ratio r(x|D) = p(x|D(l))/p(x|D(g)), and γ is a top quantile. — [Watanabe 2023, arXiv 2304.11127](https://arxiv.org/abs/2304.11127)
- Watanabe on why hierarchy makes a space a tree, using a layered optimizer example: "x7, x8, x9 require x6 and, in turn, x1 as well to be defined, is the exact reason why we call search spaces with conditional parameters tree-structured". Undefined values are padded with a placeholder x_null. — [Watanabe 2023, App. C.2](https://arxiv.org/abs/2304.11127)
- "Although the independence assumption of each dimension allows the univariate kernel to handle conditional parameters, this assumption limits the performance if no conditional parameters exist." TPE uses the Aitchison–Aitken kernel for categorical parameters. — [Watanabe 2023](https://arxiv.org/abs/2304.11127)
- Practical advice from the same tutorial: for purely numerical spaces, CMA-ES suits large budgets and Nelder–Mead small budgets. "If the search space contains categorical or conditional parameters, random search or BO becomes a strong candidate". TPE's local-search nature makes it promising for these spaces, and restarts are recommended. — [Watanabe 2023](https://arxiv.org/abs/2304.11127)
- The original Bergstra et al. (NeurIPS 2011) paper could not be retrieved (the NeurIPS proceedings URL failed through the proxy). The TPE description above relies on Watanabe's tutorial. UNVERIFIED against the original.

**Successive halving / Hyperband**
- Jamieson and Talwalkar cast HPO as non-stochastic best-arm identification. Allocating more resources to promising settings gave "comparable test accuracies an order of magnitude faster than baseline methods". — [arXiv 1502.07943](https://arxiv.org/abs/1502.07943)
- Hyperband formulates HPO as "a pure-exploration non-stochastic infinite-armed bandit problem where a predefined resource like iterations, data samples, or features is allocated to randomly sampled configurations". — [Li et al., arXiv 1603.06560](https://arxiv.org/abs/1603.06560)
- Hyperband algorithm:
  - Inputs are R and η (default 3), with s_max = ⌊log_η R⌋.
  - For each bracket s from s_max down to 0: n = ⌈(B/R)·η^s/(s+1)⌉ and r = R·η^(−s). Then run successive halving, evaluating at r_i = r·η^i and keeping the top ⌊n_i/η⌋.
  - This hedges the "n versus B/n" problem, i.e. many configurations on small budgets versus few on large budgets.
  - With R=81 and η=3, there are 5 brackets. — [Li et al., Algorithm 1, arXiv 1603.06560](https://arxiv.org/abs/1603.06560)

**BOHB**
- BOHB "relies on HB to determine how many configurations to evaluate with which budget, but it replaces the random selection … by a model-based search". BO is done TPE-style, except it uses "a single multidimensional KDE compared to the hierarchy of one-dimensional KDEs used in TPE in order to better handle interaction effects". — [Falkner et al., arXiv 1807.01774](https://arxiv.org/abs/1807.01774)
- BOHB details:
  - The model is fitted on the largest budget that has enough observations, with N_min = d+1.
  - Candidates are sampled from l(x) with bandwidths multiplied by a factor b_w.
  - A constant fraction ρ of configurations is sampled uniformly at random. In the worst case, when low fidelities are misleading, this keeps BOHB at most a bounded factor slower than random search.
  - The Aitchison–Aitken kernel is the default for categoricals.
  - GP-BO was excluded from the mixed categorical/continuous toy experiment because "GP-BO methods do not work well on such configuration spaces", while SMAC's RFs "are known to perform well in high-dimensional categorical spaces". — [arXiv 1807.01774](https://arxiv.org/abs/1807.01774)

### Inferences
- Rough fit guide:
  - **SMAC (RF)**: discrete, conditional or high-dimensional spaces, noisy or multi-instance evaluation (intensification), and cheap-enough evaluations.
  - **TPE**: deep conditional trees, cheap model fitting, and parallel use.
  - **SH / Hyperband**: there is a fidelity knob (epochs, data subset, number of instances) and rankings at low fidelity correlate with high fidelity.
  - **BOHB**: Hyperband plus model guidance when there are many evaluations.
  - **GP-BO with standard kernels**: low-dimensional continuous spaces.
- All of these consume a ConfigSpace object directly (§1), so the same space definition can be reused across algorithms.

### Gaps
- The original SMAC paper (Hutter, Hoos and Leyton-Brown, LION 2011) was not opened. RF and intensification details here come from SMAC3 code and the SMAC3 paper.

---

## 3. BO over mixed, categorical and combinatorial spaces (CoCaBO, BOCS, COMBO): kernels and encodings; why one-hot is problematic

### Takeaway
GP kernels assume continuous inputs. One-hot encoding adds dimensions, creates an input space in which most points are infeasible, and leaves the acquisition surface flat, and rounding causes mismatch and repeated evaluations. Specialized methods fall into three groups. Some give the GP a categorical-aware kernel, as CoCaBO does with an overlap kernel plus bandit choice of categories. Some model binary inclusion vectors with sparse low-order interaction models, as BOCS does. Some put a GP on a graph built from per-variable graphs, as COMBO does with complete graphs for categorical and path graphs for ordinal variables.

### Cited Findings
- CoCaBO names two main drawbacks of one-hot encoding. First, "commonly-used kernels … assume that f is continuous and differentiable in the input space, which is not the case for one-hot encoded variables, as the objective is only defined for a small subspace within this representation". Second, "one-hot encoding adds many dimensions … making the continuous optimisation of the acquisition function much harder"; "distances between one-hot encoded categorical variables tend to be large", which produces "many flat regions". — [Ru et al., CoCaBO, arXiv 1906.08878](https://arxiv.org/abs/1906.08878)
- CoCaBO's method: categorical values are chosen by a multi-agent EXP3 bandit and continuous values by BO. Its kernel mixes sum and product forms: k_z = (1−λ)(k_h + k_x) + λ·k_h·k_x, where k_h is an overlap (indicator-matching) kernel on the categories. — [arXiv 1906.08878](https://arxiv.org/abs/1906.08878)
- Garrido-Merchán and Hernández-Lobato: "a common approach is to use a one hot encoding approximation for categorical variables, or to round to the closest integer … this can lead to problems in the optimization process". In the integer case, rounding before evaluation can make BO evaluate "at a point where it has already been evaluated". Rounding inside the wrapper leaves the objective "constant in the intervals that are rounded to the same integer value", which the GP ignores. Their remedy is to apply the transformation inside the kernel. — [arXiv 1805.03463](https://arxiv.org/abs/1805.03463); [arXiv 1706.03673](https://arxiv.org/abs/1706.03673)
- BOCS handles D = {0,1}^d, "where x_i equals one if a certain element i" is present, so the domain is a subset (inclusion-vector) space. It uses a second-order model f_α(x) = α0 + Σ α_j x_j + Σ α_ij x_i x_j with sparse Bayesian regression under a horseshoe prior and Thompson sampling. Acquisition is optimized with semidefinite programming or simulated annealing. Θ(d²) coefficients "may result in high-variance estimators … if data is scarce". — [Baptista and Poloczek, BOCS, arXiv 1806.08838](https://arxiv.org/abs/1806.08838)
- COMBO's construction: "for a categorical variable C_i, the sub-graph G(C_i) is chosen to be a complete graph while for an ordinal variable we have a path graph". The search space is the graph Cartesian product of these sub-graphs. The GP uses an ARD diffusion kernel, and a horseshoe prior gives variable selection. The graph Cartesian product makes the Graph Fourier Transform "scale linearly instead of exponentially". COMBO was validated on weighted MaxSAT and NAS, among other benchmarks. — [Oh et al., COMBO, arXiv 1902.00448](https://arxiv.org/abs/1902.00448)

### Inferences
- The categorical/ordinal distinction (complete graph versus path graph in COMBO, k−1 versus 2 neighbours in ConfigSpace) runs consistently through the literature. Keeping that distinction in the representation lets surrogate models generalize.
- A subset axis maps naturally to a binary inclusion vector, where Hamming distance and the hypercube graph are the natural geometry (BOCS, and COMBO with binary variables). It does not map well to a single categorical over all 2^k subsets, which would treat every pair of subsets as equally different.

### Gaps
- I did not review newer mixed-space BO methods (e.g., CASMOPOLITAN, HEBO, Bounce) in primary sources. They are not covered here.

---

## 4. NAS: search spaces, NAS-Bench-101/201/301, random-search baselines, design-versus-algorithm, best practices, proxy and evaluator problems

### Takeaway
NAS splits into search space, search strategy and performance estimation (Elsken et al.). The field's main lessons:
- Search-space design (and the training pipeline) often matters more than the search algorithm.
- Random sampling and random search are strong baselines in well-designed spaces.
- Results are incomparable unless the benchmark (space plus training code plus split) is fixed.
- Tabular and surrogate benchmarks make repeated, seeded, ablated experiments affordable.
- Cheap evaluators (weight sharing, low fidelity, zero-cost proxies) can distort rankings, so their rank correlation with the true metric must be measured.

### Cited Findings
**Framework and search-space taxonomy**
- Elsken et al. categorize NAS "according to three dimensions: search space, search strategy, and performance estimation strategy". Incorporating prior knowledge into the space "can reduce the size of the search space and simplify the search. However, this also introduces a human bias". — [Elsken et al., arXiv 1808.05377](https://arxiv.org/abs/1808.05377)
- White et al. (2023) give a taxonomy of macro, chain-structured, cell-based and hierarchical spaces. They write: "the design of the search space represents an important trade-off between human bias and efficiency of search". Hierarchical spaces "cannot be represented fully using a DAG, and often need a conditionally-structured encoding". — [White et al., arXiv 2301.08727](https://arxiv.org/abs/2301.08727)
- White et al. criticize cell-based spaces. The DARTS space has "a seemingly large number of 10^18 architectures", but "the variance in the performance of DARTS architectures is rather small", which "may contribute to the fact that sophisticated search strategies can only give marginal gains over the average performance of randomly sampled architectures". The survey also flags "many ad-hoc design choices and fixed hyperparameters". — [arXiv 2301.08727](https://arxiv.org/abs/2301.08727)
- Encodings matter. "Different NAS subroutines, such as sampling a random architecture, perturbing an architecture, or training a surrogate model, may each perform best with different encodings", and "even small changes to the architecture encoding scheme can have significant effects". — [arXiv 2301.08727](https://arxiv.org/abs/2301.08727)

**Tabular and surrogate benchmarks**
- NAS-Bench-101 space:
  - The cell is a DAG with at most 7 vertices and at most 9 edges.
  - There are 3 operations: 3×3 conv, 1×1 conv and 3×3 max-pool.
  - It is encoded as a 7×7 upper-triangular adjacency matrix plus 5 op labels, which gives 2^21·3^5 ≈ 510M encodings.
  - These collapse to about 423k unique graphs after isomorphism removal.
  - About 1.27M models were trained (3 repeats × 4 epoch budgets). The authors note: "different encodings may favor certain algorithms by biasing the search space". — [Ying et al., arXiv 1902.09635](https://arxiv.org/abs/1902.09635)
- NAS-Bench-201 has a fixed cell space of 4 nodes with 5 ops on edges (including zeroize and skip-connect), giving 15,625 candidates. Training logs are provided on 3 datasets. — [Dong and Yang, arXiv 2001.00326](https://arxiv.org/abs/2001.00326)
- Surrogate NAS benchmarks (NAS-Bench-301) observe that tabular benchmarks caused "a focus on extremely small architectural search spaces … unrealistic results that do not transfer to larger spaces". Surrogates cover spaces of up to 10^21 architectures. The DARTS-space dataset has about 60k architectures. A surrogate (GIN) trained on one seed predicted the mean of two other seeds with lower MAE than a single tabular entry: "the surrogate model learns to smooth out the noise". — [Siems/Zimmer et al., arXiv 2008.09777](https://arxiv.org/abs/2008.09777)

**Random baselines and search space versus algorithm**
- Li and Talwalkar: "random search with early-stopping is a competitive NAS baseline", performing at least as well as ENAS on PTB and CIFAR-10. They also document reproducibility gaps (missing code and seeds). — [arXiv 1902.07638](https://arxiv.org/abs/1902.07638)
- Sciuto et al.: "On average, the state-of-the-art NAS algorithms perform similarly to the random policy". Also, "weight sharing … degrades the ranking of the NAS candidates to the point of not reflecting their true performance". — [arXiv 1902.08142](https://arxiv.org/abs/1902.08142)
- Yang et al. benchmarked 8 methods on 5 datasets using relative improvement over the randomly sampled average architecture. "Many NAS techniques struggle to significantly beat the average architecture baseline". Further findings:
  - Evaluation-protocol tricks have "a predominant impact".
  - The cell space "has a very narrow accuracy range, such that the seed has a considerable impact on architecture rankings".
  - "the hand-designed macro-structure (cells) is more important than the searched micro-structure (operations)". — [arXiv 1912.12522](https://arxiv.org/abs/1912.12522)
- Radosavovic et al. propose comparing design spaces by "distribution estimates" over populations of sampled models while controlling for complexity. They found "significant statistical differences between recent NAS design space variants" and that "design spaces for standard model families like ResNeXt can be comparable to the more complex ones used in recent NAS work". — [arXiv 1905.13214](https://arxiv.org/abs/1905.13214)
- RegNet takes the same approach of designing design spaces that parametrize populations rather than individual instances. It arrived at a low-dimensional space ("widths and depths of good networks can be explained by a quantized linear function"). — [arXiv 2003.13678](https://arxiv.org/abs/2003.13678)
- White et al. say random search is still "highly recommended as a baseline". Local search ("iteratively train and evaluate all of the neighbors of the best architecture … differ by one operation or edge") is a strong baseline on both small and large spaces. — [arXiv 2301.08727](https://arxiv.org/abs/2301.08727)

**Best-practice checklist (Lindauer and Hutter 2020)**
- The 14 best practices fall into three groups:
  - **Code**: (1) release the training pipeline; (2) release the NAS method; (3) don't wait to clean up the code.
  - **Comparison**: (4) use the same NAS benchmarks, not just the same datasets; (5) run ablations; (6) use the same evaluation protocol; (7) evaluate performance as a function of compute; (8) compare against random sampling and random search; (9) run multiple seeds; (10) use tabular or surrogate benchmarks if possible; (11) control confounding factors (hardware, runtime, library versions).
  - **Reporting**: (12) report use of HPO; (13) report end-to-end resources; (14) report all experimental details. — [Lindauer and Hutter, arXiv 1909.02453](https://arxiv.org/abs/1909.02453)
- Definition 3 in that paper: a NAS benchmark is "a dataset (with a pre-defined training-test split), a search space, and available runnable code with pre-defined hyperparameters for training". Footnote 5: "the representation of the search space is sometimes also quite different. For example, it matters whether operations are in the nodes or on the edges." The paper separates random *sampling* (one draw, whose expected value is the space average) from random *search* (an anytime incumbent). Both baselines help "assess whether good performance is due to a well-designed search space … or due to the NAS method." — [arXiv 1909.02453](https://arxiv.org/abs/1909.02453)

**Evaluator and proxy problems**
- Elsken et al.: low-fidelity estimates (fewer epochs, data subsets, lower resolution, fewer cells) "introduce bias". Relying on them works only if relative ranking is stable, and "this relative ranking can change dramatically when the difference between the cheap approximations and the 'full' evaluation is too big", which argues for gradually increasing fidelities (Hyperband, BOHB). — [arXiv 1808.05377](https://arxiv.org/abs/1808.05377)
- Rank disorder in one-shot or weight-sharing NAS: when supernet rankings disagree with standalone training, the literature calls it "rank disorder". The survey describes "considerable debate both for … and against" the consistency assumption. — [White et al., arXiv 2301.08727](https://arxiv.org/abs/2301.08727)
- Zero-cost proxies: the best one reached a Spearman correlation of 0.82 with final accuracy on NAS-Bench-201, against 0.61 for the reduced-training proxy EcoNAS. — [Abdelfattah et al., arXiv 2101.08134](https://arxiv.org/abs/2101.08134). The survey adds that "simple baselines such as 'number of parameters' and 'FLOPs' are surprisingly competitive". Proxies "may be unreliable, especially on larger search spaces" and have biases such as "preferring larger models". — [arXiv 2301.08727](https://arxiv.org/abs/2301.08727)
- NAS-Bench-Suite-Zero evaluated 13 zero-cost proxies across 28 tasks. It found bias, for example toward cell size, and complementary information across proxies. Adding all proxies to NAS surrogates improved predictive performance by up to 42%. — [arXiv 2210.03230](https://arxiv.org/abs/2210.03230)

### Inferences
- The consistent lesson is that the space is the hypothesis. A narrow, hand-tuned space makes any algorithm look good and makes algorithm comparisons noise-dominated. Comparisons must report the random-sample distribution of the space itself.
- An evaluator is only usable for search if its ranking agrees with the target metric (Spearman or Kendall τ) on the region the search actually visits. That should be measured, not assumed.

### Gaps
- I did not open NAS-Bench-Suite, JAHS-Bench-201 or HW-NAS-Bench. Benchmarks newer than about 2023 were not surveyed.
- No primary-source number was obtained for low-fidelity versus full-fidelity rank correlations in Zela et al. 2018; only the qualitative claim via Elsken et al. is recorded here.

---

## 5. Multi-objective HPO (ParEGO, multi-objective SMAC)

### Takeaway
Multi-objective HPO is handled either by scalarization (weighted sum, Tchebycheff, or ParEGO's randomized augmented Tchebycheff) or by Pareto-based indicators such as hypervolume and EHVI. SMAC3 implements ParEGO as a per-iteration scalarization layered on its normal single-objective BO, and its intensifier tracks multiple incumbents.

### Cited Findings
- From the overview by Karl et al.:
  - Scalarization has two drawbacks: the weights must be chosen sensibly, and "one single solution can not adequately represent a multi-objective problem with conflicting objectives".
  - A weighted sum cannot reach Pareto-optimal points on non-convex parts of the front.
  - Weighted Tchebycheff can reach every optimum with some weight choice. — [Karl et al., arXiv 2206.07438](https://arxiv.org/abs/2206.07438)
- ParEGO (Knowles 2006), as described in that overview: normalize the objectives to [0,1], draw a weight vector from a simplex lattice each iteration, and scalarize with the augmented Tchebycheff function c_α(λ) = max_j α_j c_j(λ) + ρ·(α·c(λ)). Then fit a surrogate and optimize EI. A caveat: "uniformly sampled weights do not necessarily result in the best distribution of nondominated points". — [arXiv 2206.07438](https://arxiv.org/abs/2206.07438)
- SMAC3's `ParEGO` defaults to ρ=0.05. It draws θ at random and normalizes it at the start of each iteration, and returns max(θ·v) + ρ·sum(θ·v). — [SMAC3 parego.py](https://raw.githubusercontent.com/automl/SMAC3/main/smac/multi_objective/parego.py)
- The SMAC3 intensifier keeps `max_incumbents` (default 10) "in the case of multi-objective". — [SMAC3 intensifier.py](https://raw.githubusercontent.com/automl/SMAC3/main/smac/intensifier/intensifier.py)
- Hypervolume "is strictly Pareto compliant" and needs only a reference point, not knowledge of the front. — [arXiv 2206.07438](https://arxiv.org/abs/2206.07438)

### Inferences
- If a benchmark-design search trades off goals such as discriminativeness, cost and validity, a ParEGO-style scalarization over a ConfigSpace object is the least-effort route (SMAC3). Reporting the Pareto set with hypervolume avoids committing to weights in advance.

### Gaps
- Knowles (2006), the original ParEGO paper, was not opened; it is described here via the overview and SMAC3 code. I did not check SMAC3 docs on how the multi-objective intensifier compares configurations.

---

## Concrete lessons for representing a ~22-axis benchmark-design space (mixed nominal, ordinal and subset axes; conditional and forbidden combinations)

These lessons are inferences that synthesize the cited findings above.

1. **Type every axis faithfully.**
   - Nominal axes → `Categorical` (k−1 neighbours; RF splits on index).
   - Ordered axes → `OrdinalHyperparameter`, so neighbourhoods are adjacent values (a path graph, as in COMBO) and models can exploit the order.
   - Do not quantize floats with `q` (removed in ConfigSpace 1.1); use `Ordinal` instead.
   - Sources: ConfigSpace docs and source; COMBO.
2. **Subset axes: use one boolean per element, not one categorical over all subsets.**
   - Per-element inclusion bits give Hamming or hypercube geometry, which is BOCS's {0,1}^d formulation and makes partial overlap between subsets visible to surrogates and neighbourhoods.
   - Express cardinality rules (non-empty, at most m) as forbidden clauses, and keep the default configuration legal. ConfigSpace refuses a forbidden default.
   - Use a single `Categorical` over enumerated subsets only when k is tiny.
3. **Use conditions for "irrelevant" and forbidden clauses for "invalid".**
   - Model "axis B is meaningless unless A = a" as `EqualsCondition` or `InCondition`. Inactive axes then become NaN, and SMAC imputes them out of range while TPE handles them per dimension. Do not invent a dummy "n/a" value that the optimizer would have to learn to ignore.
   - Reserve forbidden clauses for genuinely incompatible combinations.
   - Each child gets one parent condition (combine with `And`/`OrConjunction`), and the graph must be acyclic.
   - Avoid conditions on float parents.
4. **Measure the size of the legal region.** Sampling and neighbourhoods are rejection-based. If forbidden clauses remove most of the product space, restructure: merge correlated axes into one categorical of legal tuples, or turn constraints into conditions. Otherwise random search and local search waste draws.
5. **Choose algorithms that suit mixed, conditional spaces.**
   - Always include random sampling (the space average) and random search as baselines, plus simple one-exchange local search.
   - Then use RF-based SMAC or TPE. Avoid vanilla GP-BO with one-hot categoricals (CoCaBO and Garrido-Merchán document the failure modes).
   - Use Hyperband or BOHB only if there is a cheap fidelity whose rank correlation with full evaluation has been checked.
6. **Validate the evaluator before searching.** If candidate benchmark designs are scored by a proxy (a small model panel, a subset of items, a cheaper judge), report Spearman or Kendall τ against the full evaluation over a random sample of the space. NAS showed proxies can carry systematic bias, such as toward size, and that rankings flip when the fidelity gap is large.
7. **Look at the variance of the space before comparing algorithms.** If a random sample of designs scores within a narrow band, seed noise will dominate rankings (Yang et al.). Report relative improvement over the random-sample average and multiple seeds.
8. **Freeze and publish the space as a benchmark.** Following Lindauer and Hutter Definition 3, publish the axes, the evaluation code and the splits. Serialize the ConfigSpace (JSON or YAML) so every method searches the identical space. Record the encoding, since encodings can favor some algorithms (NAS-Bench-101, White et al.).
9. **Make results cheap to reproduce.** If evaluations are expensive, tabulate them over a sampled subset or fit a surrogate that smooths noise (NAS-Bench-301). This makes ablations and repeated-seed studies affordable.
10. **Treat multiple objectives explicitly.** Use ParEGO-style scalarization in SMAC3 or report a Pareto front with hypervolume, rather than fixing ad-hoc weights.
