# Final blind critic: report

Note: the critic said it wrote report.md, but no such file exists in its folder. This is its final
message, saved verbatim. Its scripts and rerun output are in work/.

## Verdict

The reported numbers are accurate, but several conclusions drawn from them are not supported, and two are contradicted by the repository's own data. I reproduced the metric-search table exactly with a seeded rerun (0.916 / 0.575 on training, 0.840 / 0.253 held-out) and recounted every cell of the attack table from the saved outputs; all match. The work has drifted from the problem statement: it now optimises a classifier of synthetic, attacker-written buyers, with "good" defined as "exactly optimal", and no noise figure has been measured on a real model.

## Three most important findings

**1. The "decisive" metric ranking does not hold out of sample.**
- On training buyers, total error reaches 0.90 AUC against 0.63 for the model-based yielding metric.
- On the held-out panel, averaged over the 10 designs, they tie: 0.724 AUC each, with 12% and 14% detection at 1% false alarms.
- The winning combination's held-out score comes from its one-sided-yielding half: 0.253 for the combination against 0.280 for one-sided yielding alone on the chosen design.
- The ranking tracks which checks each attacker round was shown, so "treat the ranking as more reliable than the numbers" is backwards.
- The 4 "good" buyers are all the same optimal policy, differing only on tied cells, so total error is tested against its own definition of good.
- Total error is a competence measure, not a sycophancy measure. It flags a non-yielding buyer with a 0.03 level offset (inside the project's own 0.05 margin) in 16% of draws, where the yielding metrics stay at 1%.

**2. The "resolution limit / no metric can do better" claim is contradicted.**
- I ran a lower bound on the Neyman–Pearson test that Message 3 proposes: a matched filter that knows each buyer's deviation pattern, at 1% false alarms.
- It detects the held-out buyers in 89% of draws on average, against 23% for the chosen metric. 19 of 20 are caught in over half their draws; only one stays low (19%).
- So the information is in the data at the current item count; the fixed aggregate checks miss it. This does not show that any single fixed metric could extract it for all buyers.
- "Average yielding below about 0.045 looks like noise for any test" is also wrong. 0.045 is the cutoff of the one-sided statistic, which already sits at about 0.024 for a perfect buyer. The plain mean shift has a standard deviation near 0.012, so the floor is nearer 0.03.
- The attack table scores noise-free buyers against thresholds set from noisy ones, which the attackers say they exploited. It is not a fair estimate of what a real run would miss.

**3. Drift from the problem statement, plus some record errors.**
- Every result rests on five declared, unmeasured noise components.
- The only real small-model evidence is Qwen3.5-4B failing the capability gate, 5 of 9 checks failed on my rerun of the report script. An "exactly optimal" reference class describes no model the study will test.
- The metric search scores single buyers only, although fake steering pairs were the sharper failure (10 of 13 pass).
- The library is 67 buyers, not 75.
- "87% at about 177k items" has no supporting output anywhere in the repository.
- `pocket_remains` is called an honest improvement, but its own docstring says a pocket "gets worse".

## What I would do next

- Stop the attack rounds and metric tuning. The held-out panel is spent: every metric has been read on it.
- Measure the noise first. Run a small pilot on a real Qwen model to get the variance components and the base-to-steered correlation before setting any threshold or item count.
- Redefine "good" relative to the model's own no-pressure behaviour. Keep yielding and updating as separate estimands, with total error as a competence screen only.
- Add direct checks, fixed in advance, for tied, walk-away and edge cells, and a joint test on the equivalence margins.
- Score attacks with noise and report minimum detectable effects per subgroup.
- Correct the record on the items listed under finding 3.
