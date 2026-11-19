# Formal, citable definitions of bargaining competence and how LLM negotiation papers measure them

Research date: 2026-11-19.

**Access notes, which affect how far each claim was checked.**
- WebFetch could not resolve arxiv.org. `curl` through the proxy worked for arxiv.org (abs and HTML) and aclanthology.org.
- The full texts of all six LLM papers below were downloaded and searched locally, and every quote was checked against them: arXiv 2604.16472, 2605.13909, 2402.15813, 2402.05863, 2602.05302 and 2402.12348. CraigslistBargain (ACL D18-1256, PDF) and Guo 2023 (arXiv 2305.05516) were read the same way.
- The proxy blocked these hosts, with connections failing: doi.org, sciencedirect.com, jstor.org, psycnet.apa.org, pubmed, link.springer.com, pubsonline.informs.org, econometricsociety.org, wikipedia.org, ideas.repec.org, semanticscholar.org, academic.oup.com, hup.harvard.edu and pon.harvard.edu.
- **I could not open any of the classic economics or psychology sources.** These are Nash 1950, Rubinstein 1982, Myerson 1981, Myerson & Satterthwaite 1983, Chatterjee & Samuelson 1983, Güth et al. 1982, Galinsky & Mussweiler 2001, Raiffa 1982, Fisher & Ury, and Oosterbeek et al. 2004. Below they carry standard bibliographic references marked **[NOT OPENED]**. What they say is reported only as the opened LLM papers describe it, and is labelled that way.

---

## 1. Canonical definitions and sources for each candidate gate criterion

### Takeaway
Each criterion a buyer-capability gate would plausibly use has a standard textbook or journal source:
- individual rationality, or the participation constraint: Myerson 1981, and Myerson & Satterthwaite 1983 for bilateral trade
- reservation value and BATNA: Raiffa 1982; Fisher & Ury 1981
- the ZOPA and gains-from-trade versus no-gains-from-trade: the bilateral-trade literature
- a fair-split benchmark: Nash 1950
- the alternating-offers protocol: Rubinstein 1982
- Pareto efficiency
- first-offer anchoring: Galinsky & Mussweiler 2001
- the ultimatum game: Güth et al. 1982

The cleanest citable formal statements I could verify are in the LLM papers themselves, which restate these concepts formally and cite the classics: Bergemann et al. 2026 Defs. 1–6, and PieArena App. A Defs. A.1–A.6.

### Standard bibliographic references (classics) [NOT OPENED]
- Nash, J. F. (1950). "The Bargaining Problem." *Econometrica* 18(2):155–162. [NOT OPENED]. Bergemann et al. describe it as follows: "Nash (1950) introduces the axiomatic bargaining solution, predicting equal surplus division under symmetric disagreement points." — [Bergemann et al. 2026, arXiv 2604.16472](https://arxiv.org/html/2604.16472)
- Rubinstein, A. (1982). "Perfect Equilibrium in a Bargaining Model." *Econometrica* 50(1):97–109. [NOT OPENED]. Bergemann et al. Def. 1 uses "multi-round alternating offers (Rubinstein, 1982)" as the protocol. — [arXiv 2604.16472](https://arxiv.org/html/2604.16472)
- Myerson, R. B. (1981). "Optimal Auction Design." *Mathematics of Operations Research* 6(1):58–73. [NOT OPENED]. Bergemann et al. cite it as the source of "the standard IR constraint in mechanism design." — [arXiv 2604.16472](https://arxiv.org/html/2604.16472)
- Myerson, R. B. & Satterthwaite, M. A. (1983). "Efficient Mechanisms for Bilateral Trading." *Journal of Economic Theory* 29(2):265–281. [NOT OPENED]. Bergemann et al. describe it as follows: "Myerson and Satterthwaite (1983) establish the impossibility of achieving ex-post efficiency in bilateral trade under any incentive-compatible, individually rational, budget-balanced mechanism." — [arXiv 2604.16472](https://arxiv.org/html/2604.16472)
- Chatterjee, K. & Samuelson, W. (1983). "Bargaining under Incomplete Information." *Operations Research* 31(5):835–851. [NOT OPENED]. Bergemann et al. describe it as follows: "analyze bilateral trade under incomplete information with simultaneous offers, characterizing the set of equilibria when reservation prices are private." — [arXiv 2604.16472](https://arxiv.org/html/2604.16472)
- Raiffa, H. (1982). *The Art and Science of Negotiation.* Harvard University Press. [NOT OPENED]. TERMS-Bench cites this reference in this form. — [arXiv 2605.13909](https://arxiv.org/html/2605.13909)
- Fisher, R. & Ury, W. (1981). *Getting to Yes: Negotiating Agreement Without Giving In.* Houghton Mifflin. Later editions add B. Patton. This is the origin of the term "BATNA". [NOT OPENED; no opened paper's bibliography contained it]
- Güth, W., Schmittberger, R. & Schwarze, B. (1982). "An Experimental Analysis of Ultimatum Bargaining." *Journal of Economic Behavior & Organization* 3(4):367–388. [NOT OPENED]. Cited as the origin of the ultimatum game in [Guo 2023, arXiv 2305.05516](https://arxiv.org/html/2305.05516v2).
- Galinsky, A. D. & Mussweiler, T. (2001). "First offers as anchors: the role of perspective-taking and negotiator focus." *Journal of Personality and Social Psychology* 81(4):657–669. [NOT OPENED]. Bibliographic entry as given in [NegotiationArena](https://arxiv.org/html/2402.05863).

### Cited Findings (formal statements verified in opened papers)

**Bilateral bargaining game with private reservation prices**
- Bergemann et al. Def. 1: "A buyer with reservation price b and a seller with reservation price s negotiate over a single indivisible item through multi-round alternating offers (Rubinstein, 1982)… Neither party observes the other's reservation price." — [Bergemann, Ghili, Hu, Li & Yang 2026, arXiv 2604.16472](https://arxiv.org/html/2604.16472)
- The same definition gives the utilities. The buyer gets U_B = b − p if p ≤ b, 0 with no agreement, and −∞ if p > b; the seller's utility is symmetric. "Accepting a price that violates the reservation constraint (p>b for the buyer or p<s for the seller) yields negative utility—an irrational outcome." — [arXiv 2604.16472](https://arxiv.org/html/2604.16472)
- On terminology, the paper says that "reservation price is the highest a buyer will pay or the lowest a seller will accept… it is equivalent to 'private value' in the auction literature." — [arXiv 2604.16472](https://arxiv.org/html/2604.16472)

**ZOPA and gains from trade**
- Def. 2 (ZOPA): "the interval [s,b] when b≥s. The total available surplus (gains from trade) is b−s."
- Def. 3: "A scenario with b<s is a no-gains-from-trade (NGFT) scenario: no price yields non-negative utility for both parties simultaneously, and the rational outcome is no deal." — [arXiv 2604.16472](https://arxiv.org/html/2604.16472)

**Individual rationality (IR)**
- Def. 4: "An agent satisfies individual rationality (IR) if it never accepts a price yielding negative utility: the buyer rejects any p>b, and the seller rejects any p<s. This is the standard IR constraint in mechanism design (Myerson, 1981). IR is a necessary condition for credible negotiation. An agent that violates it cannot be considered a rational participant regardless of its average surplus." — [arXiv 2604.16472](https://arxiv.org/html/2604.16472)
- The paper frames IR as a floor: "While IR is a necessary condition (floor), strategic effectiveness is an optimization objective (ceiling)." — [arXiv 2604.16472](https://arxiv.org/html/2604.16472)

**BATNA, IR set and ZOPA in PieArena's multi-issue form**
- BATNA: "The BATNA (Best Alternative to a Negotiated Agreement) of party i is its maximal outside-option value: b_i := sup u_i^out(ω)… Intuitively, b_i is the walkaway payoff; a negotiator should not rationally accept an agreement ω with u_i(ω)<b_i." — [Zhu et al. 2026, PieArena, arXiv 2602.05302](https://arxiv.org/html/2602.05302)
- Def. A.2 (Individual rationality and ZOPA): the weak IR set is {ω feasible : u_i(ω) ≥ b_i ∀i}, and the strict ZOPA is {ω feasible : u_i(ω) > b_i ∀i}.
- Remark A.3 explains the strict version: "if a party is indifferent between an agreement and walking away, they may rationally prefer to walk away." — [arXiv 2602.05302](https://arxiv.org/html/2602.05302)

**Pareto dominance**
- PieArena Def. A.6: "ω′ Pareto-dominates ω if u_i(ω′) ≥ u_i(ω) ∀i, and u_j(ω′) > u_j(ω) for some j… moving from ω to ω′ is called a Pareto improvement." — [arXiv 2602.05302](https://arxiv.org/html/2602.05302)

**Surplus share (value claiming)**
- Bergemann Def. 5: "the buyer's surplus share is (b−p)/(b−s) and the seller's surplus share is (p−s)/(b−s)." — [arXiv 2604.16472](https://arxiv.org/html/2604.16472)
- PieArena Def. A.5 gives the pie share as s_i/Σ s_j, where surplus is measured above the BATNA. — [arXiv 2602.05302](https://arxiv.org/html/2602.05302)

**IR attributed to Rubinstein (attribution looks wrong)**
- AmazonHistoryPrice states IR in words: "Rational decision-making agents, whether Buyer or Seller, should not accept transactions resulting in negative profit."
- It attributes this to "the assumption of Individual Rationality of Rubinstein (1982)". This attribution is unusual; the standard IR citation in mechanism design is Myerson 1981, which is what Bergemann cites. — [Xia et al. 2024, arXiv 2402.15813](https://arxiv.org/html/2402.15813)

**Ultimatum game**
- NegotiationArena's definition: "One agent is given all the game's resources and proposes a split… The second agent can either accept or reject the proposal, which means both agents lose all resources. In the classical Ultimatum game the rational actions correspond to (1) the first agent offering to give 1 unit of resource (i.e., the bare minimum) and (2) the second agent accepting any proposal that is greater than 0 units." — [Bianchi et al. 2024, arXiv 2402.05863](https://arxiv.org/html/2402.05863)

**First-offer anchoring**
- Bergemann et al. describe it this way: "Galinsky and Mussweiler (2001) demonstrate the first-offer anchoring effect: the opening offer shifts the counterpart's reference point and predicts final settlement prices." — [arXiv 2604.16472](https://arxiv.org/html/2604.16472)

**Responsiveness to information**
- TERMS-Bench frames the task as a Bayesian game. The counterpart has a "fully specified latent type that parameterizes its behavior and that the agent must infer from observed prices and messages. The agent, by contrast, is assigned only a reservation value r_A as a hard individual-rationality constraint." — [Zhang et al. 2026, arXiv 2605.13909](https://arxiv.org/html/2605.13909)

### Inferences
- **Hierarchy of criteria.** Among these criteria, only IR has a sharp normative status that is independent of the opponent: a necessary condition, with any violation being a mistake. Surplus share and deal rate are optimisation objectives, and the right value depends on the opponent and the mechanism.
- **Supporting a gate.** This hierarchy supports a gate with a hard IR floor, plus graded criteria for everything else.
- **Quality information is not a classic object here.** I found no canonical economics source that defines "responsiveness to quality information" as a bargaining competence. The nearest formal objects are the following, none of which I opened:
  - Bayesian updating about a latent type, as in TERMS-Bench and the incomplete-information bargaining literature.
  - The lemons and adverse-selection literature: Akerlof 1970.
  - Signalling: Spence 1973.

  A gate that tests whether the buyer's offers move with item quality is best justified as a **comparative-statics or monotonicity property**: the willingness to pay, and so the offers, should be weakly increasing in perceived value. This is the author's inference, not a definition from a source.

### Gaps
- I could not open Fisher & Ury, Raiffa, or any of the original Nash, Rubinstein or Myerson papers, because the publisher hosts were blocked by the proxy. Exact page-level definitions for these should be checked in a library copy.
- I found no source that formally defines "responsiveness to quality information" as a bargaining competence criterion.

---

## 2. How LLM negotiation papers operationalize these criteria (quoted definitions)

### Takeaway
Every paper operationalizes IR the same way:
- the indicator **1{agreed price lies outside the agent's reservation value}**, or below the BATNA
- averaged over episodes to give a "violation rate"
- with "no-deal recognition" measured separately on infeasible (no-ZOPA) episodes as a false-agreement rate

Beyond IR, the papers diverge: surplus share, deal rate, cue penalties, Pareto improvements, anchoring correlations, and "bad counter-offer" probabilities.

### Cited Findings

**Bergemann et al. 2026** (Yale/Tsinghua; arXiv 2604.16472) — [link](https://arxiv.org/html/2604.16472)
- Violation rate: "Fraction of negotiations where an agent accepts a price yielding negative utility (p>b for the buyer or p<s for the seller). A no-deal outcome (utility =0) is not a violation."
- "In NGFT scenarios, every deal violates IR for at least one party, so the violation rate coincides with the NGFT deal rate."
- Deal rate (Def. 6): "Higher is better in GFT; lower is better in NGFT."
- The paper separates self-violations from opponent-induced violations ("opp.").
- Initial aggressiveness:
  - Seller: α = p₀^seller / s.
  - Buyer, "Gap closure" variant: α^buyer,1 = (p₀^seller − p₀^buyer)/p₀^seller, the "fraction of the seller's asking price cut by the buyer's first counter-offer". There is also a "reservation ratio" variant.
- Results:
  - "All GFT self-violation rates are below 1%… At these magnitudes, differences across models are not reliably distinguishable from sampling variability."
  - "Buyer NGFT self-violations are all ≤0.40%, while seller NGFT self-violations range from 0.00% (o3) to 2.30% (GPT-4.1)."
  - Against o3 as buyer, "GPT-4.1 as seller violates at 11.5%."
  - Buyer aggressiveness ranges from 0.34 to 0.40.
  - The data cover 5 frontier models and 15,000 negotiations.

**AmazonHistoryPrice** (Xia et al. 2024, arXiv 2402.15813) — [link](https://arxiv.org/html/2402.15813)
- Profits are P_b = B − D and P_s = D − C. Sessions are split into "Mutual Interest (MI)", B > C, and "Conflicting Interest (CI)", B ≤ C.
- Normalized profit: P′_b = (B−D)/|B−C|, with "In sessions that make no deal… the NPs of both sides are 0."
- Negative profits are therefore not truncated. A deal above budget enters the Sum of Normalized Profits (SNP) as a negative number. The paper says: "All possible normalized profits on the table… are equal to the number of valid MI deals minus the number of valid CI deals." A CI deal therefore subtracts from the total.
- This is the "negative-profit rule": IR violations are penalized through negative SNP, not through a separate violation rate.
- Also reported: "First Bid Ratio (FBR) = Buyer's First Bid / Budget."

**TERMS-Bench** (Zhang, Zhang, Pappu, El, Blanchet, Athey, Liu & Zou 2026, arXiv 2605.13909) — [link](https://arxiv.org/html/2605.13909)
- Hard IR: "the agent… is assigned only a reservation value r_A as a hard individual-rationality constraint."
- Protocol compliance: CritViol% = (1/N) Σ 1[V_i^crit > 0], covering "Price-bound, IR, and invalid-action violations."
- No-deal recognition:
  - "In no-deal episodes, agreement is a failure because there is no price that is individually rational for both parties." The false-agreement rate is FAGR⁻ = (1/|I⁻|) Σ 1[f_i ≠ ⊥], where lower is better, and "the no-deal safe termination rate is SafeTerm⁻ = 1 − FAGR⁻."
  - AgentExit⁻ is the share of no-deal episodes that end in `AgentReject`. It "distinguishes disciplined infeasibility detection from cases where the agent is rescued by counterpart walk-away or timeout."
  - Finding: "IR-violation rate and AgentExit⁻ form two independent axes of self-constraint."
- Cue use:
  - "We define the cue penalty α_cue = SE⁺(cue-revealing) − SE⁺(cue-muted). For every LLM, α_cue<0: agents extract less surplus when informative cues are present. Penalties range from −0.009 (GPT-5.4) to −0.063 (Claude Opus 4.6, Grok 4.20)."
  - "warm cues induce over-concession, pressure cues trigger brittle behavior."
  - The paper also measures opponent-model belief error, BE_type, against a Bayes-optimal dynamic-programming oracle, "not a claim of human-optimal negotiation."

**NegotiationArena** (Bianchi, Chia, Yuksekgonul, Tagliabue, Jurafsky & Zou 2024, arXiv 2402.05863) — [link](https://arxiv.org/html/2402.05863)
- Anchoring: the "Relationship between initial proposed price p₁ and final proposed price p_final. Spearman correlation ρ=0.716" (GPT-4).
- Bad counter-offer, a single-step irrationality check: "A counter-offer by the buyer is considered bad in this context if its proposed price, p₂, is larger than the received offer p₁."
  - The "over-valued buyer is four times as likely to counter-propose a higher price than the seller's initial proposal, as compared to the default buyer (0.41 v. 0.11) (p<0.05, one-tailed binomial test)."
  - "Even when manually prompted to be 'self-interested', there is no significant change."
- The paper also notes "split-the-difference" behavior and "it (un)necessarily believes that it must meet in the middle."
- Values were drawn as follows: seller cost ~ U{20,40} and buyer willingness to pay ~ U{60,80}, with 100 games per experiment.

**GTBench** (Duan et al. 2024, arXiv 2402.12348) — [link](https://arxiv.org/html/2402.12348)
- Pareto efficiency is a descriptive analysis, not a scored criterion: "We study Pareto Efficiency in two games: Negotiation and (Iterated) Prisoner's Dilemma… some LLMs, like Llama-2-70b-chat and CodeLlama-34b-Instruct, may accept unfair resource divisions. In contrast, GPT-4 and Mistral struggle to reach agreements and tend to negotiate for Pareto improvements."
- The headline metric is Normalized Relative Advantage, NRA = (Σ f_s(M_i) − Σ f_s(M_o)) / (Σ f_s(M_i) + Σ f_s(M_o)).

**PieArena** (Zhu, Cui, Dufallo, Jin, Xu, Zhang & Cain 2026, arXiv 2602.05302) — [link](https://arxiv.org/html/2602.05302)
- BATNA compliance: "C := 1{u_i(ω*) ≥ b_i ∀i∈{1,2}}", "ensuring individual rationality."
- Results: "BATNA compliance is tightly concentrated at the ceiling (100%), but a small tail falls below 99%: Gemini-2.5-Flash (97.5%), GPT-4.1 (97.8%), Grok-3 (98.0%), and ERNIE-4.5 (95.0%)."

**CraigslistBargain** (He, Chen, Balakrishnan & Liang 2018, EMNLP; ACL D18-1256) — [link](https://aclanthology.org/D18-1256.pdf)
- The buyer has a **target price**, not a hard reservation value: "we additionally suggest a private price to the buyer as a target… target prices at 0.5x, 0.7x and 0.9x of the listing price."
- Utility is linear, "the buyer has a utility of 1 at their target price, the seller has a utility of 1 at the listing price, and both agents have a utility of zero at the midpoint."
- There is therefore no IR constraint in the Myerson sense.

### Inferences
- **IR is directly comparable across papers; the rest is not.** The IR indicator is the most standardized operationalization: TERMS-Bench, Bergemann, AmazonHistoryPrice (via CI deals) and PieArena (BATNA compliance) all compute essentially 1{deal outside the agent's reservation value}. A gate's IR criterion can therefore cite all four papers as precedent.
- **CraigslistBargain cannot support IR claims.** Its "target" is a goal, not a constraint, so its data do not let you test IR.
- **NegotiationArena's check is a precedent for a single-step test.** P(p₂ > p₁), a buyer counter-offer above the seller's ask, is a published irrationality check that is computable from one decision.

### Gaps
- GTBench gives no formal Pareto-efficiency metric. Its "Pareto efficiency" is a qualitative scatter-plot analysis (Fig. 5). I found no LLM bargaining paper in this set that scores Pareto efficiency quantitatively for single-issue price bargaining. That is expected: in single-issue price bargaining every deal inside the ZOPA is Pareto-efficient, because utility is transferable.

---

## 3. Human baselines

### Takeaway
Human baselines that are directly comparable to LLM buyer metrics are sparse:
- PieArena: about 167 sessions with MBA students, giving pie shares.
- AmazonHistoryPrice: one human buyer on 20 products.
- CraigslistBargain: agreement rate.
- Classic ultimatum and anchoring results: only second-hand figures were available to me.

None of these reports a human IR-violation rate on a scale comparable to LLM benchmarks.

### Cited Findings

**PieArena (MBA students)** — [arXiv 2602.05302](https://arxiv.org/html/2602.05302)
- The data come from "MBA Negotiation Courses offered at an elite American university business school", 167 human sessions in total.
- Human–human, SnyderMed: "Across n=23 pairs… the mean normalized total pie is 0.874 (SD 0.085)."
- Main Street, human vs. GPT-5 (single-issue, zero-sum): "students capture 39.7% of the pie, while the agent captures 60.3%."
  - "GPT-5 secures a significantly larger share of total pie than students in both base mode and pro mode" (base mode p=0.0186).
  - "student as seller, agent as buyer"; "89 completed sessions (deal rate: 92.1%)".
- Hire Talent: "students capture on average 53.8% of the pie, while the agent captures 46.2%… not statistically significant (p=0.2674)."
- PieArena's case for using students as a reference: "trained students at this level perform comparably to professional negotiators," and it cites Camerer & Hogarth 1999 that "only specific training will induce equilibrium offers."

**AmazonHistoryPrice, human buyer** — [arXiv 2402.15813](https://arxiv.org/html/2402.15813)
- "one of the authors, who is a graduate student from the CS department of SJTU, volunteered to play the Human Buyer," on 20 products.
- "the human buyer's SNP far exceeded that of the models, and the human buyer makes no deal in CI scenarios."
- Table 6 figures, all against a gpt-3.5 seller:

| Buyer | FBR | SNP_b | Share_b | CI deals |
|---|---|---|---|---|
| Human | 0.69 | 1.11 | 22.30% | 0.00% |
| ChatGPT | 0.91 | 0.25 | 2.83% | not listed here |
| GPT-4 | 0.91 | 0.06 | 2.91% | not listed here |
| Mistral-7B-Instruct | 0.89 | −3.95 | not listed here | 50.00% (2 CI sessions) |

**CraigslistBargain humans** — [ACL D18-1256](https://aclanthology.org/D18-1256.pdf)
- "We collected 6682 human-human dialogues on AMT."
- Table 7's "Human" row shows agreement rate (Ag) 0.91 and dialogue length 10.2.
- This is an agreement rate under a target-price utility, not an IR rate.

**Ultimatum game (human)** — second-hand, via [Guo 2023, arXiv 2305.05516](https://arxiv.org/html/2305.05516v2)
- Offers: "a meta-study of 37 papers by Oosterbeek et al. (2004) reports that human proposers, on average, offer 40% of the total amount."
- Rejections: Guo also writes "human studies show an average acceptance rate of around 16% (Oosterbeek et al. (2004))". This is almost certainly a misstatement of the **rejection** rate, because it is compared with GPT rejection rates of about 18%. **Flag: this should be checked against Oosterbeek, Sloof & van de Kuilen (2004), *Experimental Economics* 7:171–188 [NOT OPENED].**

**First-offer anchoring (human)**
- Galinsky & Mussweiler (2001) [NOT OPENED]. Bergemann et al. describe the finding only qualitatively: "the opening offer… predicts final settlement prices." I could not verify the effect sizes.
- [NegotiationArena](https://arxiv.org/html/2402.05863) compares its LLM result, ρ=0.716, to this human literature only qualitatively.

### Inferences
- **Benchmarks treat the human IR baseline as effectively zero.** The human buyer made no CI deals in AmazonHistoryPrice, and PieArena's screening expects 100% walk-away. This is an empirical convention, not a measured population rate.
- **Students are not a performance ceiling.** On a single-issue price task with the agent as buyer, PieArena shows a frontier model beating MBA students on surplus share.

### Gaps
- I found no large-sample human IR-violation rate for bilateral price bargaining with induced private values.
- I could not open the Güth 1982 and Galinsky & Mussweiler 2001 numbers because of blocked hosts.
- The AmazonHistoryPrice human baseline is n=1 person on 20 products, which is very weak.

---

## 4. Which criteria suit a single-decision probe (one forward pass reading the buyer's offer distribution), and which need multi-turn play?

### Takeaway
Some criteria are defined on **a single decision given a state**, and these are measurable from one forward pass. Others are defined on **outcomes or trajectories** and need multi-turn play:
- surplus share, deal rate, concession rate, belief updating over rounds, robustness to pressure, Pareto improvement, and Rubinstein-style equilibrium play
- Bergemann explicitly calls deal rate "a pair-level property"

### Cited Findings
- **Bergemann** defines IR per accept decision: "the buyer rejects any p>b" ([arXiv 2604.16472](https://arxiv.org/html/2604.16472)). That condition is checkable at a single accept/reject node.
- **Bergemann** says allocative efficiency, measured by deal rate, "is a pair-level property: it depends on both agents' strategies jointly, not on either agent alone." He stresses "Instruction adherence under multi-turn pressure… across many rounds in which the counterpart actively attempts to persuade and extract concessions." ([arXiv 2604.16472](https://arxiv.org/html/2604.16472))
- **NegotiationArena's** bad-counter-offer check uses only (p₁, p₂), the seller's first offer and the buyer's first reply. It is a single-step measurement. ([arXiv 2402.05863](https://arxiv.org/html/2402.05863))
- **Bergemann's** buyer initial aggressiveness, (p₀^seller − p₀^buyer)/p₀^seller, and **AmazonHistoryPrice's** First Bid Ratio, first bid / budget, both use only the first buyer offer. ([arXiv 2604.16472](https://arxiv.org/html/2604.16472); [arXiv 2402.15813](https://arxiv.org/html/2402.15813))
- **TERMS-Bench's** cue penalty compares surplus across counterpart families over whole episodes, so it is multi-turn. Its no-deal metrics are terminal outcomes: FAGR⁻ is the false-agreement rate and AgentExit⁻ is the agent-exit rate on no-deal episodes. ([arXiv 2605.13909](https://arxiv.org/html/2605.13909))
- **PieArena's** screen is run as full mirror-play episodes, not single decisions. ([arXiv 2602.05302](https://arxiv.org/html/2602.05302))

### Inferences (author's mapping, not from a source)

Single-decision, suitable for a one-pass probe of the offer or accept distribution:
- **IR mass:** P(offer > b), or P(accept | ask > b). Single-turn IR has a direct precedent in the per-decision Def. 4.
- **No-deal recognition at one node:** P(walk or reject | ask > b, or a signal that no ZOPA exists).
- **Opening-offer aggressiveness:** the gap closure or the First Bid Ratio.
- **NegotiationArena's dominance check:** P(p₂ > p₁).
- **Responsiveness to quality information as comparative statics:** shift the quality cue while holding b fixed, and check that the expected offer moves in the right direction. Offers must also stay at or below b.

Multi-turn only:
- surplus share and deal rate
- concession rate and temporal patience
- the cue penalty α_cue
- belief error over rounds
- resistance to opponent-induced violations ("opp." violations, the 11.5% case)
- Pareto improvement in repeated or multi-issue games

**Caveat on validity.** A single-pass IR test underestimates multi-turn IR failures. In Bergemann, violations were *induced by strong opponents* through pressure over rounds. A passed single-decision gate is therefore a necessary condition, not a sufficient one, for multi-turn IR.

### Gaps
- None of the opened papers evaluates negotiation competence from a single forward-pass offer distribution. I found no published precedent for a "one forward pass" gate as such. The single-step metrics above are pieces of multi-turn evaluations.

---

## 5. Accepted thresholds: is there a field standard?

### Takeaway
**There is no field-wide accepted threshold.** Each paper sets its own, or reports rates without a pass/fail cutoff. The only explicit capability gate I found is PieArena's model screen. It requires **6/6 no-deal runs on an infeasible case**, and 6/6 BATNA-compliant agreements on a feasible multi-issue case, which is effectively a 100% (zero-tolerance) criterion on a small sample.

### Cited Findings
- **PieArena Step 2** (empty-ZOPA screen): "Each model is run for R_ND=6 independent mirror-play episodes… We retain only models that always walk away, M₂:={M∈M₁: r̂_ND(M)=1}, yielding |M₂|=149. This enforces the minimal-competence requirement that a model recognizes infeasibility and does not hallucinate an agreement." 232 models entered this step and 149 passed. — [arXiv 2602.05302](https://arxiv.org/html/2602.05302)
- **PieArena Step 3:** models must satisfy in all 6 runs "(i) Full agreement… (ii) Constraint compliance… (iii) BATNA dominance: the resulting utilities exceed BATNAs for both parties," which "ensure[s] that a model can… reach individually rational agreements." — [arXiv 2602.05302](https://arxiv.org/html/2602.05302)
- **Bergemann et al.** set no threshold. They report rates and note that "All GFT self-violation rates are below 1%… differences across models are not reliably distinguishable from sampling variability." — [arXiv 2604.16472](https://arxiv.org/html/2604.16472)
- **TERMS-Bench** reports FAGR⁻, CritViol% and α_cue as continuous diagnostics, marked "lower is better". I found no pass/fail cutoff in the text; the only "threshold" uses I found are internal simulator parameters. It does use statistical criteria for its claims: "9 of 13 per-model 95% bootstrap CIs excluding zero and an across-model Wilcoxon test at p<10⁻³". — [arXiv 2605.13909](https://arxiv.org/html/2605.13909)
- **AmazonHistoryPrice** has no threshold. It chose ChatGPT as the evaluation opponent because "they rarely accept irrational deals in CI scenarios." — [arXiv 2402.15813](https://arxiv.org/html/2402.15813)

### Inferences
- **Defending a zero-tolerance IR gate.** The theoretical basis is Def. 4: IR is a necessary condition, so any violation counts as a failure. The empirical precedent is PieArena's r̂_ND = 1. A practical tolerance can then be set statistically, not ad hoc:
  - Bergemann's observation that rates below about 1% are within sampling noise at their sample sizes implies that a gate should state its sample size and a confidence bound.
  - For example: require the upper 95% bound on the IR-violation rate to be ≤ x%.
  - By the "rule of three", 0 violations in n trials gives an approximate 95% upper bound of 3/n. This is the author's statistical suggestion, not from the papers.
- **Do not gate on deal rate.** Myerson & Satterthwaite (1983), as characterized in Bergemann, imply that no IC, IR, budget-balanced mechanism achieves ex-post efficiency with private values. A gate should therefore **not** require 100% deal rate in feasible cases from a rational buyer. Deal-rate and surplus thresholds are not theory-anchored and should be framed as benchmark-relative: relative to an opponent, a Bayes-optimal oracle as in TERMS-Bench, or a human baseline as in PieArena.
- **Fair-split benchmark.** A 50% surplus split has a theoretical anchor in the symmetric Nash bargaining solution (Nash 1950, as characterized in Bergemann). NegotiationArena likewise treats the midpoint (50) as the reference. That makes it a defensible neutral reference point for buyer surplus share, not a pass threshold.

### Gaps
- I found no meta-analysis or standards document proposing common IR-violation thresholds for LLM negotiators.
- The PieArena sample of 6 runs per model is small. The paper gives no justification for choosing 6.
