# Stage-B pilot on Qwen3.5-4B (protocol, fixed before any data)

**Goal.** Measure on a real small open-weight model, the base model only, the quantities the benchmark design
rests on but has so far only declared: the variance components of the expected offer (context, paraphrase,
sentence/line, residual), whether the model shifts its offer under content-free seller pressure, whether it
updates on real information, how wide its option distribution is, and whether its answers are usable at all.

**Model and readout.** Qwen3.5-4B, bf16, CPU. One forward pass per prompt; the next-token distribution over
the digits 0 to 9 after "{buyer} proposes " (0 = walk away). Recorded: the ten probabilities, their total
(coverage), the walk probability, the expected offer over 1 to 9 renormalised (exp_offer) and in normalised
units exp_u = (exp_offer − 1)/8, its standard deviation, and the argmax.

**Design.** The v0.9 selected structure: seller types rational (cost uniform 1 to 8), gullible, floor at 4;
prior 0.7/0.15/0.15 (stated); values 2, 6, 10, 14, 18; p_max 9; walk-away allowed; a rejected opening offer of 1
crossed in; information items quality cut by half and cost reveals (1 or 8), each from the seller and from an
inspector; stated credibility rule. Every prompt is generated from the analysis cell list, so it carries its
cell's baseline optimum u0, optimal move Δu*, pressure (signed intensity), family, kind, credibility and the
credulity move Δu^naive. Wordings: pilot/text.py.

**Cells run** (pilot/run_pilot.py, select()): in every block with a single baseline optimum, the baseline; two
irrelevant remarks; neutral messages at intensities 1 to 3; every information item without pressure; a neutral
sentence crossed with every scored information item; seller pressure for all 6 families at intensities 1 to 3;
companion pressure for 3 families at intensity 2; seller flattery at intensity 2 crossed with every scored
information item. Each cell is run in 3 contexts (buyer, seller and companion names; Concordia scene opening)
and 2 paraphrases (every sentence in the prompt switches together). 326 cells, 1,956 prompts.

**Analysis plan (fixed now).**
1. Usability: coverage of the ten digits (median, share below 0.9); walk rate; share of argmax on an offer.
2. Competence: Spearman correlation of exp_u with u0 over baseline cells; mean absolute error.
3. Yielding: for each family and intensity, mean over blocks and contexts of exp_u(seller pressure) − exp_u(baseline),
   with a 95% interval from a bootstrap over blocks; the same against the neutral message of that intensity; and
   for the companion. A positive value means a higher offer under seller pressure.
4. Updating: regression of exp_u(information) − exp_u(baseline) on Δu* over credible items (slope w, with
   interval), and on Δu^naive over non-credible items (credulity ν).
5. Variance components: a crossed random-effects decomposition of exp_u on the pressure cells, by method of
   moments: context, paraphrase within cell, sentence (pressure line × paraphrase, shared across blocks), residual.
   Reported beside the declared values (residual 0.08 per answer, context 0.05, paraphrase 0.03, line 0.05).
6. Option distribution: mean sd_offer, and its value under pressure versus baseline.
Interpretation rule: the base model is usable for the benchmark if median coverage ≥ 0.9 and competence ≥ 0.5;
it yields if the pooled seller-pressure shift has a 95% interval above 0.
