# Multi-issue negotiation datasets, game-theoretic suites and multi-agent environments for LLM negotiation evaluation

Scope note: All claims below were checked against primary sources opened on 2026-11-19 (arXiv abstract + HTML full text pages, ACL Anthology pages, raw.githubusercontent.com README/LICENSE files, and a sparse `git clone` of google-deepmind/concordia at commit b3de736, 2026-11-18). Network notes: `export.arxiv.org` (arXiv API) and `github.com` web pages / `api.github.com` were blocked by the proxy (403); arxiv.org/abs, arxiv.org/html, aclanthology.org, raw.githubusercontent.com and `git clone` worked. Anything not confirmed in an opened source is marked UNVERIFIED.

Bottom line for the study (pressure vs. information susceptibility of a buyer LLM, Qwen3.5 2B-9B locally): **SovereignNegotiation-Bench (SNB)** is the only benchmark found that (a) already reports Qwen3.5-2B/4B/9B, (b) separates *content* pressure tactics (urgency, authority, extraction, injection) from *economic* tactics (lowball, stonewall) in a paired within-situation design, (c) measures individual rationality (agreement below the principal's reservation value) and information leakage (reservation-value disclosure) deterministically, and (d) was run with locally served vLLM models. But it is an unreviewed single-author preprint whose code/scenarios are "will be released" (not verified public), and it is a delegated-agent bargaining (mostly price/amount) task rather than multi-issue. LLM-Deliberation is the most mature multi-issue, multi-agent, HF-runnable option with a peer-reviewed reproducibility study that includes 7-8B models. The Concordia contest is not a clean fixed benchmark (held-out scenarios not clearly public; single model gemma-2-9b-it).

## Q1. Task, metrics, single vs. multi-turn, and whether individual rationality and information use are measured

### Takeaway
The family splits into (i) human-human dialogue corpora (Deal or No Deal, CaSiNo) that are multi-issue but static datasets, (ii) LLM-vs-LLM multi-turn multi-issue games with explicit scoring (LAMEN, LLM-Deliberation, PieArena, NegotiationArena trading/ultimatum), (iii) broad game-theory suites where negotiation is one of many tasks (GTBench, MAgIC), (iv) multi-agent simulation substrates (Concordia, Melting Pot), and (v) a duty/pressure-focused delegated bargaining benchmark (SNB). Only SNB and PieArena explicitly score individual rationality vs. a reservation value/BATNA; SNB, LLM-Deliberation, and LAMEN (via faithfulness) measure information use/leakage.

### Cited Findings
**Deal or No Deal (Lewis et al., EMNLP 2017)**
- Published in Proceedings of EMNLP 2017 (ACL Anthology D17-1259, "Deal or No Deal? End-to-End Learning of Negotiation Dialogues") — [ACL Anthology](https://aclanthology.org/D17-1259/)
- Dataset: 5,808 dialogues based on 2,236 unique scenarios, released under `data/negotiate`; each dialogue converted into two training examples (one per agent perspective with its own goals) — [end-to-end-negotiator README](https://raw.githubusercontent.com/facebookresearch/end-to-end-negotiator/master/README.md)
- The repo is a training codebase for RNN / hierarchical latent models (selection model, clustering model, language model), not an LLM evaluation harness — [README](https://raw.githubusercontent.com/facebookresearch/end-to-end-negotiator/master/README.md)
- (Task details such as "divide books/hats/balls with private values" are from my background knowledge; I did not open the paper full text — UNVERIFIED here.)

**CaSiNo (Chawla et al., NAACL 2021)**
- Published in Proceedings of NAACL-HLT 2021 — [ACL Anthology](https://aclanthology.org/2021.naacl-main.254/)
- 1,030 negotiation dialogues; two participants as campsite neighbours negotiate Food, Water, Firewood packages based on individual preferences and requirements; includes strategy annotations — [CaSiNo README](https://raw.githubusercontent.com/kushalchawla/CaSiNo/main/README.md)

**LAMEN (Davidson et al., ICLR 2024)**
- Negotiation games enabling multi-turn and cross-model interactions; self-play and cross-play — [arXiv 2401.04536](https://arxiv.org/abs/2401.04536)
- Game types include single-issue distributive and multi-issue, and integrative games (players have different preference weights over issues, allowing trade-offs) vs. non-integrative (same preferences) — [arXiv HTML v3](https://arxiv.org/html/2401.04536v3)
- Information/consistency metric: *internal faithfulness* (agent offers less than what it stated as acceptable in its private "mental notes") and *external faithfulness* (offers more than it believes opponent would settle for) — [arXiv HTML v3](https://arxiv.org/html/2401.04536v3)
- Qualifier: models must reach at least one agreement in ten single-issue distributive self-play games to proceed — [arXiv HTML v3](https://arxiv.org/html/2401.04536v3)

**LLM-Deliberation (Abdelnabi et al., NeurIPS 2024 D&B)**
- Multi-agent, multi-issue, semantically rich scorable negotiation games; multi-turn; evaluates greedy and adversarial players — [arXiv 2309.17234](https://arxiv.org/abs/2309.17234)
- Default 6 agents, 24 rounds, "4 consecutive random ordering of the 6 agents and a history window of the last 6 interactions"; a project proposer makes a final official deal at the end — [arXiv HTML](https://arxiv.org/html/2309.17234)
- Metrics: final success (5-way and 6-way agreement), "Any" deal, wrong deals (score-calculation errors), and score leakage ratio — "agents were instructed not to reveal information about scores... We use GPT-4 as a judge to verify whether public answers contain any mention of scores or thresholds" — [arXiv HTML](https://arxiv.org/html/2309.17234)
- Each agent has a minimum threshold (BATNA); in the compromising game "any deal... higher than their minimum threshold is preferable to no deal; i.e., the BATNA of agents... is their minimum threshold" — [arXiv HTML](https://arxiv.org/html/2309.17234)
- Games: Base, Base rewritten (by GPT-4), a 7-player/6-issue variant, and new GPT-4-generated games (game1-3); incentives `greedy`, `targeted_adv`, `untargeted_adv`, `cooperative` only for the base game — [LLM-Deliberation README](https://raw.githubusercontent.com/S-Abdelnabi/LLM-Deliberation/main/README.md)
- Reproducibility study found inconsistency in acceptance criteria: text says deal must "exceed" thresholds but `check_agreement` uses >= — [arXiv HTML 2602.18230](https://arxiv.org/html/2602.18230)

**GTBench (Duan et al.)**
- 10 tasks built on OpenSpiel: Tic-Tac-Toe, Connect-4, Kuhn Poker, Breakthrough, Liar's Dice, Blind Auction, Negotiation, Nim, Pig, Iterated Prisoner's Dilemma; taxonomy complete/incomplete information, static/dynamic, probabilistic/deterministic — [arXiv HTML](https://arxiv.org/html/2402.12348); [GTBench README](https://raw.githubusercontent.com/jinhaoduan/GTBench/main/README.md)
- Negotiation is classed as a probabilistic game; metric is Normalized Relative Advantage (NRA) averaged over 50 valid matches, each participant first in 25; Elo also reported in appendix — [arXiv HTML](https://arxiv.org/html/2402.12348)
- Characterizes equilibrium and Pareto efficiency in repeated games — [arXiv abs](https://arxiv.org/abs/2402.12348)

**Concordia Contest / haggling substrate**
- Five cooperation-eliciting substrates: Pub Coordination, Haggling, State Formation, Labor Collective Action, Reality Show; Haggling: "In Fruitville, 2–4 merchants negotiate prices over multiple bargaining rounds" — [arXiv HTML 2512.03318](https://arxiv.org/html/2512.03318)
- Scores rescaled per scenario with min-max normalization to theoretical min/max; rankings via Elo plus Iterative Maximal Lotteries, Copeland, Ranked Pairs — [arXiv HTML](https://arxiv.org/html/2512.03318)
- Test scenarios "contain multiple opportunities for exploitation of irrational behavior"; protocol asked agents to minimize irrational losses — [arXiv HTML](https://arxiv.org/html/2512.03318)
- v1.8.9 haggling environment: buyer proposes price, seller accepts/rejects; buyer base reward sampled 5-6, seller base reward 1-2 coins; default 2 games, 3 main players; payoff via `bargain_payoffs` — [v1.8.9 haggling.py](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/examples/modular/environment/haggling.py)
- Main-branch `examples/games/haggling/` (commit b3de736, 2026-11-18) contains `simulation.py` ("buyer proposes a price, and the seller accepts or rejects"), `sequential_bargain_game_master.py`, `sequential_bargain_payoff.py`, and configs `fruitville.py`, `fruitville_gullible.py`, `puppet.py`, `vegbrooke.py`, `vegbrooke_strange_game.py`, `vegbrooke_stubborn.py` — [concordia repo, examples/games/haggling](https://github.com/google-deepmind/concordia/tree/main/examples/games/haggling) (accessed via git clone; github.com web page itself was proxy-blocked)
- Haggling is single-issue price bargaining (multi-fruit variant `haggling_multi_item_0` tagged "negotiation, hidden information") — [v1.8.9 scenarios.py](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/examples/modular/scenario/scenarios.py)

**PieArena (Zhu et al.)**
- Two-party negotiations with private information and deterministic payoffs, adapted from MBA course scenarios; mirror-play, cross-play, human-LM play — [arXiv 2602.05302](https://arxiv.org/abs/2602.05302); [PieArena README](https://raw.githubusercontent.com/chriszhu-yale/PieArena-Benchmark/main/README.md)
- Scenarios include SnyderMed and Hire Talent (job offers, multi-issue positive-sum), IP License (contingent payment, asymmetric beliefs, multi-issue), Service Quote and Main Street (single-issue zero-sum price bargaining) — [arXiv HTML v4](https://arxiv.org/html/2602.05302v4)
- Recorded metrics: total pie, pie shares, verified agreement, output validity, **BATNA compliance**, computation accuracy; plus LLM-judge lie rate and reputation; Beta-Generalized Bradley-Terry-Luce ranking — [arXiv HTML v4](https://arxiv.org/html/2602.05302v4)
- "parties can expand the total pie while remaining individually rational" (multi-issue) — [arXiv HTML v4](https://arxiv.org/html/2602.05302v4)

**SovereignNegotiation-Bench (Liu, arXiv 2607.02814)**
- 1,764 paired scenarios = 252 situations in 18 consumer/P2P domains × 7 counterparty tactics; five agency-law duties (loyalty, obedience to authority, confidentiality, candor, diligence) checked deterministically on logs; first three form headline "faithful success" — [arXiv abs](https://arxiv.org/abs/2607.02814)
- Multi-turn: at most ten turns; agent emits one JSON action per turn (propose/accept/reject/share_document/ask_user/escalate/end); simulated principal grants/withholds consent and tightens reservation value at turn three in 30% of situations — [arXiv HTML v2](https://arxiv.org/html/2607.02814v2)
- Individual rationality = loyalty breach: "An agreement whose value is worse than the principal's (current) reservation value" — [arXiv HTML v2](https://arxiv.org/html/2607.02814v2)
- Information use: reservation value counts as disclosed when it appears in a sentence with limit/authority language; sensitive disclosures detected via canary strings; counterparty economics are a deterministic function of actions and detected disclosures, so disclosure has a causal price — [arXiv HTML v2](https://arxiv.org/html/2607.02814v2)
- Tactics: economic (lowball, stonewall) and content (extraction, urgency, injection, authority) vs. a cooperative control; content tactics share the control's concession schedule "so their effect is purely linguistic" — [arXiv HTML v2](https://arxiv.org/html/2607.02814v2)
- Forced-disclosure intervention: a single sentence stating the reservation value takes a rule-based careful agent's surplus from 0.70 to 0.00 — [arXiv abs](https://arxiv.org/abs/2607.02814)

**NegotiationArena (Bianchi et al.)**
- Three scenario types: ultimatum games (allocating shared resources), trading games (aggregate resources), buy/sell price negotiations; multi-turn — [arXiv 2402.05863](https://arxiv.org/abs/2402.05863)
- Models asked to verbalize their state in Seller/Buyer and Ultimatum games; agents could boost payoffs ~20% by pretending to be desolate/desperate against GPT-4 — [arXiv HTML](https://arxiv.org/html/2402.05863); [arXiv abs](https://arxiv.org/abs/2402.05863)

**MAgIC (Xu et al.)**
- Competition-based benchmark: two social deduction games (Chameleon, Undercover) plus three game-theory scenarios; metrics for judgment, reasoning, deception, self-awareness, cooperation, coordination, rationality; PGM enhancement — [arXiv 2311.08562](https://arxiv.org/abs/2311.08562); [MAgIC README](https://raw.githubusercontent.com/cathyxl/MAgIC/main/README.md)
- Prisoner's Dilemma is among the game-theory scenarios — [arXiv HTML v3](https://arxiv.org/html/2311.08562v3)

**Melting Pot**
- "A suite of test scenarios for multi-agent reinforcement learning"; over 256 unique test scenarios; evaluates TensorFlow SavedModels — [Melting Pot README](https://raw.githubusercontent.com/google-deepmind/meltingpot/main/README.md)
- Concordia contest paper credits Melting Pot with introducing mixed-motive evaluation for RL agents and adopts its substrate/background-population split — [arXiv HTML 2512.03318](https://arxiv.org/html/2512.03318)

### Inferences
- For a "pressure vs. information" design, SNB's paired content-vs-economic tactic structure is the closest ready-made match; LLM-Deliberation's greedy/adversarial incentives offer pressure from other *agents* in a multi-issue setting, and its leakage metric covers information protection, but not information *use* to improve a deal.
- Melting Pot is an RL substrate suite, not a language negotiation benchmark; it is relevant only via Concordia.
- GTBench's negotiation task is a small OpenSpiel game evaluated by NRA; it measures strategic play, not susceptibility to rhetorical pressure.

### Gaps
- Did not open the DoND and CaSiNo paper full texts; task mechanics for DoND are from README/background only.
- Did not open GTBench's OpenSpiel negotiation game definition (number of items, turn limit).
- MAgIC's three game-theory scenarios beyond Prisoner's Dilemma not confirmed (README truncated in my extraction; possibly Public Good and Cost Sharing — UNVERIFIED).
- NegotiationArena "non-price games" turn limits and payoff details not extracted.

## Q2. Models evaluated, with numbers (focus on open-weight <10B; SNB Qwen3.5 table)

### Takeaway
Only SNB and the LLM-Deliberation reproducibility study report open-weight models under 10B with usable numbers; Concordia used gemma-2-9b-it as the sole contest model. Original LAMEN, NegotiationArena, MAgIC and PieArena are essentially closed/frontier-only. SNB shows Qwen3.5-2B/4B/9B have low faithful success (6/22/30%) and high reservation-value disclosure (52/44/40%).

### Cited Findings
**SovereignNegotiation-Bench — exact Qwen3.5 rows of Table 3 (test split, 1,435 scenarios per agent; all %, except surplus)** — [arXiv HTML v2](https://arxiv.org/html/2607.02814v2)

Columns: n | FSR (faithful success) [95% situation-bootstrap CI] | Deal | Surplus (normalized) | Loyalty breach | Authority breach | Sensitive discl. | Strategic discl. | Limit (reservation value) discl. | Injection compliance | Extraction compliance | Escalation (stonewall episodes)

| Model | n | FSR [CI] | Deal | Surpl. | Loyal. | Auth. | Sens. | Strat. | Limit | Inj. | Extr. | Esc. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3.5-0.8B | 1,435 | 7 [4,9] | 35 | -0.34 | 26 | 9 | 12 | 1 | 2 | 15 | 2 | 7 |
| Qwen3.5-2B | 1,435 | 6 [4,8] | 40 | -0.10 | 13 | 19 | 31 | 9 | 52 | 28 | 40 | 66 |
| Qwen3.5-4B | 1,435 | 22 [18,25] | 55 | 0.10 | 4 | 17 | 33 | 13 | 44 | 39 | 30 | 68 |
| Qwen3.5-9B | 1,435 | 30 [27,34] | 59 | 0.13 | 4 | 12 | 26 | 7 | 40 | 57 | 31 | 48 |
| Qwen3.5-27B | 1,435 | 50 [45,54] | 74 | 0.16 | 5 | 4 | 14 | 2 | 33 | 35 | 21 | 30 |
| Qwen3.5-35B-A3B | 1,435 | 28 [25,31] | 55 | 0.07 | 2 | 7 | 19 | 1 | 52 | 51 | 40 | 63 |

(Column alignment reconstructed from the HTML table; cross-checked against Table 7 [Qwen3.5-9B seed-0 FSR 30, limit discl. 40, injection 57] and Table 8 [9B direct: FSR 30, deal 59, surplus 0.13, loyalty 4, authority 12, injection 57].)

- Reference rows from same table: rule-based Careful agent FSR 92 [89,95], deal 82, surplus 0.70; "Careful + discloses limit" FSR 0, surplus 0.00; Naive (accepts first offer) FSR 0, loyalty breach 99; best LLM Gemma-4-26B-A4B FSR 75 [71,78]; Gemma-4-E4B 54 [50,58]; Gemma-4-E2B 25 [20,29]; gpt-oss-20b 21 [17,25] — [arXiv HTML v2](https://arxiv.org/html/2607.02814v2)
- 17 open-weight models served locally with vLLM in bf16 (or vendor quantization) on H100/L40S; hybrid-reasoning models run with thinking disabled; temperature 0.7, top-p 0.95, fixed seed schedule, one run per scenario; invalid JSON gets one retry — [arXiv HTML v2](https://arxiv.org/html/2607.02814v2)
- Per-tactic FSR (Appendix A), cooperative control / lowball, for Qwen3.5 0.8B, 27B, 2B, 35B-A3B, 4B, 9B: control 7, 59, 9, 37, 25, 36; lowball 8, 50, 3, 20, 19, 31 — [arXiv HTML v2](https://arxiv.org/html/2607.02814v2)
- Pooled tactic effects on FSR vs. control (mean 38): lowball -7, stonewall -9, extraction -3, urgency 0, injection -12, authority +1; breach-rate change: injection +16, extraction +4, urgency +1, authority 0 — [arXiv HTML v2](https://arxiv.org/html/2607.02814v2)
- Forced disclosure for Qwen3.5-4B: surplus 0.10 → -0.02 (Δ -0.12), deal -11 pp, clean pairs Δ -0.32 — [arXiv HTML v2](https://arxiv.org/html/2607.02814v2)
- Seed variation: Qwen3.5-9B FSR 30, 30, 29 across 3 seeds (SD 0.7); limit disclosure 40, 40, 41; injection compliance 57, 46, 47 — [arXiv HTML v2](https://arxiv.org/html/2607.02814v2)
- Mitigations on Qwen3.5-9B: fiduciary checklist FSR 30 (Δ0), PrincipalBench scaffold 23 (Δ -7, deal 59→26), code guard on binding steps 33 (Δ +3, n.s.) — [arXiv HTML v2](https://arxiv.org/html/2607.02814v2)
- Within Qwen3.5 (6 sizes), Spearman with size: FSR +0.77, limit disclosure +0.20, authority breaches -0.60, injection compliance +0.71; none significant — [arXiv HTML v2](https://arxiv.org/html/2607.02814v2)

**LLM-Deliberation (original)**
- Tested GPT-4, GPT-3.5, Gemini Pro, Llama2 13b/70b Chat, Llama3 70b Chat, Mixtral 8x7B; Mistral 7b and Llama2 7b excluded because they "did not follow the basic formatting of the game" — [arXiv HTML](https://arxiv.org/html/2309.17234)
- Base-game results (Final 5-way / 6-way / Any / Wrong / Leaked, %): GPT-4 81/33/100/1.4/0; GPT-3.5 20/8/33/19/25; Llama2-13b 57/10/82/16/14; Llama2-70b 76/19/95/11/22; Llama3-70b 60/21/100/4/2; Gemini Pro 45/0/70/13/6 — [arXiv HTML](https://arxiv.org/html/2309.17234)

**LLM-Deliberation reproducibility study (TMLR)** — base game, same columns (Final 5-way / 6-way / Any / Wrong / Leaked) — [arXiv HTML 2602.18230](https://arxiv.org/html/2602.18230)
- Qwen2.5-7B: 65 / 25 / 100 / 11.15 / 44.62
- Llama-3-8B: 25 / 0 / 70 / 8.14 / 69.42
- Ministral-8B: 25 / 0 / 50 / 12.88 / 7.12
- Phi-3.5-mini: 10 / 10 / 50 / 12.87 / 40.77
- Llama-2-13b (int8): 30 / 0 / 75 / 17.92 / 9.23
- GPT-4o mini 55/5/90/2.69/0.58; GPT-4o 75/10/85/0.58/0.00; Qwen2.5-72B (int4) 85/0/95/2.12/0.00; Mistral-Small (int8) 80/0/100/11.15/0.00; DeepSeek-R1-Distill-Qwen-32B (int8) 95/55/95/2.50/0.00
- Note: the study fixed a leakage-detection bug, which "vastly increased variance in the Leaked column" because smaller models' responses became parseable — [arXiv HTML](https://arxiv.org/html/2602.18230)
- Claim that the framework allows objective model comparison is "unsupported by evidence" due to inconsistent performance across games — [arXiv HTML](https://arxiv.org/html/2602.18230)

**LAMEN**
- Evaluated gpt-3.5, gpt-4, chat-bison, claude-2, command, command-light, and LLaMA 2; "all models except LLaMA 2 models advanced" past the qualifier — [arXiv HTML v3](https://arxiv.org/html/2401.04536v3); "only closed-source models tested here were able to complete these tasks" — [arXiv abs](https://arxiv.org/abs/2401.04536)

**GTBench**
- GPT-3.5-turbo-1106, GPT-4-0613, Llama-3-70b-Instruct, Deepseek-LLM-67b-chat, Llama-2-70b-chat, CodeLlama(-34b-Instruct), Mistral-7b-Orca (and Deepseek-LLM-7b-chat appears in tables); temperature 0.2, 1024 max tokens — [arXiv HTML](https://arxiv.org/html/2402.12348)

**Concordia Contest**
- 197 participants, 878 submission attempts, 25 teams; top six advanced to tournament — [arXiv HTML](https://arxiv.org/html/2512.03318)
- "Gemma-2-9b-it was selected as the official LLM for the competition"; results reported "with a single model due to compute constraints" — [arXiv HTML](https://arxiv.org/html/2512.03318)

**PieArena**
- Final set of 13 models: Claude-Opus-4.5, Claude-Sonnet-4.5, ERNIE-4.5 (424B-A47B, the only open-weight), Gemini-2.5-Flash, Gemini-3-Pro, GPT-4.1, GPT-5, GPT-5.2, o4-Mini-High, Grok-3, Grok-3-Mini, Grok-4, Grok-4.1-Fast, via OpenRouter — [arXiv HTML v4](https://arxiv.org/html/2602.05302v4)

**NegotiationArena**: Claude-2, Claude-2.1, GPT-4, GPT-3.5; GPT-4 best buyer (avg sale price $41) — [arXiv HTML](https://arxiv.org/html/2402.05863)

**MAgIC**: seven LLMs, strongest GPT o1, weakest Llama-2-70B (>3x gap); PGM boosts all by avg 37% — [arXiv abs](https://arxiv.org/abs/2311.08562)

### Inferences
- In SNB, Qwen3.5-2B/4B/9B already sit in a regime where reservation-value disclosure (40-52%) is far more common than loyalty breaches (4-13%): for a pressure-vs-information study at this scale, *information leakage* rather than accepting a bad deal is the dominant failure mode.
- Qwen3.5-2B's FSR (6%) is at floor; the 4B and 9B leave headroom for manipulations to show effects.
- In LLM-Deliberation, ~7-8B models can complete the game (Qwen2.5-7B 65% 5-way) but leak scores heavily (Llama-3-8B 69%, Qwen2.5-7B 45%), suggesting small Qwen3.5 models would also be measurable there.

### Gaps
- SNB full per-tactic table for Qwen3.5 (stonewall/extraction/urgency/injection/authority rows) only partially extracted (HTML rendering truncated).
- No benchmark found reports Qwen3.5 except SNB; no Qwen3.5 numbers on LLM-Deliberation, LAMEN, PieArena or Concordia.
- Concordia contest per-agent scores and average-score value (rendered as math, stripped) not extracted.

## Q3. Code and data availability, license, and local self-hosted HF runnability

### Takeaway
LLM-Deliberation (MIT) and its repro fork FACT29 (MIT) directly support Hugging Face models with quantization; Concordia (Apache-2.0) supports local backends (ollama, pytorch_gemma in v1.8.9); PieArena (Apache-2.0 code, CC BY 4.0 data) and GTBench (MIT) work through OpenAI-compatible endpoints (so vLLM serving should work); LAMEN (MIT) and MAgIC (MIT) are API-only in shipped code; SNB code is not yet confirmed released.

### Cited Findings
- **Deal or No Deal**: code + data in `facebookresearch/end-to-end-negotiator`; LICENSE is CC BY-NC 4.0 (Attribution-NonCommercial) — [LICENSE](https://raw.githubusercontent.com/facebookresearch/end-to-end-negotiator/master/LICENSE)
- **CaSiNo**: dataset + PyTorch code; LICENSE is CC BY 4.0 — [LICENSE](https://raw.githubusercontent.com/kushalchawla/CaSiNo/main/LICENSE); [README](https://raw.githubusercontent.com/kushalchawla/CaSiNo/main/README.md)
- **LAMEN**: github.com/epfl-dlab/LAMEN, MIT; README lists model providers {anthropic, cohere, google, openai, azure} only — no HF/local path in README — [LICENSE](https://raw.githubusercontent.com/epfl-dlab/LAMEN/master/LICENSE); [README](https://raw.githubusercontent.com/epfl-dlab/LAMEN/master/README.md); transcripts released — [arXiv HTML v3](https://arxiv.org/html/2401.04536v3)
- **LLM-Deliberation**: github.com/S-Abdelnabi/LLM-Deliberation, MIT; installs transformers + accelerate (HF) alongside openai and google-cloud-aiplatform; all games/variants included — [LICENSE](https://raw.githubusercontent.com/S-Abdelnabi/LLM-Deliberation/main/LICENSE); [README](https://raw.githubusercontent.com/S-Abdelnabi/LLM-Deliberation/main/README.md)
- **Repro (FACT29)**: github.com/joshrosie/FACT29, MIT; `--model "hf_Qwen/Qwen2.5-72B-Instruct" --quantization "int4"` example; bitsandbytes quantization — [README](https://raw.githubusercontent.com/joshrosie/FACT29/main/README.md); [LICENSE](https://raw.githubusercontent.com/joshrosie/FACT29/main/LICENSE)
- **GTBench**: github.com/jinhaoduan/GTBench, MIT; supports remote APIs (OpenAI/Anyscale/DeepInfra) and "OpenAI-Compatible APIs via FastChat"; HF leaderboard at huggingface.co/spaces/GTBench/GTBench — [README](https://raw.githubusercontent.com/jinhaoduan/GTBench/main/README.md); [LICENSE](https://raw.githubusercontent.com/jinhaoduan/GTBench/main/LICENSE)
- **Concordia**: Apache-2.0; `pip install gdm-concordia` — [LICENSE](https://raw.githubusercontent.com/google-deepmind/concordia/main/LICENSE); [README](https://raw.githubusercontent.com/google-deepmind/concordia/main/README.md). v1.8.9 `language_model/utils.py` api types: amazon_bedrock, google_aistudio_model, google_cloud_custom_model, langchain_ollama, mistral, ollama, openai, pytorch_gemma, together_ai — [utils.py v1.8.9](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/concordia/language_model/utils.py). Main branch moved provider wrappers to `concordia/contrib/language_models` — [language_model README (main)](https://github.com/google-deepmind/concordia/blob/main/concordia/language_model/README.md) (read via git clone)
- **PieArena**: code and scenario files Apache-2.0; dataset (transcripts, judge outputs, human data) CC BY 4.0 on Harvard Dataverse doi:10.7910/DVN/UYI2O5; uses an "OpenAI-compatible client" (e.g., OpenRouter) via OPENAI_BASE_URL — [README](https://raw.githubusercontent.com/chriszhu-yale/PieArena-Benchmark/main/README.md)
- **SNB**: "Code, scenarios and all episode logs will be released" (no repo URL in paper) — [arXiv abs](https://arxiv.org/abs/2607.02814); the paper states agent models "are open-weight and served with vLLM" and prompts are reproduced verbatim in Appendix F (example billing-negotiation prompt and JSON action schema shown) — [arXiv HTML v2](https://arxiv.org/html/2607.02814v2)
- **NegotiationArena**: github.com/vinid/NegotiationArena; README shows an MIT badge but no LICENSE file was found at repo root (main/master); agents shown are `ChatGPTAgent` with OpenAI key; "ANY_SCALE is optional. It is used to run LLaMA" — [README](https://raw.githubusercontent.com/vinid/NegotiationArena/main/README.md)
- **MAgIC**: MIT; "this code version only support openai models, if you want to test your own LLMs, please refer to our leaderboard website" — [README](https://raw.githubusercontent.com/cathyxl/MAgIC/main/README.md); [LICENSE](https://raw.githubusercontent.com/cathyxl/MAgIC/main/LICENSE)
- **Melting Pot**: Apache-2.0; `pip install dm-meltingpot` — [LICENSE](https://raw.githubusercontent.com/google-deepmind/meltingpot/main/LICENSE); [README](https://raw.githubusercontent.com/google-deepmind/meltingpot/main/README.md)

### Inferences
- Running Qwen3.5 2B-9B locally: easiest = LLM-Deliberation/FACT29 (native HF path) and SNB (designed around vLLM, once released); PieArena and GTBench via a vLLM OpenAI-compatible server by setting base URL (not tested); Concordia via its ollama backend or a custom wrapper (not tested).
- DoND's NC license matters only for commercial use; CaSiNo is CC BY 4.0.

### Gaps
- Did not verify SNB repository existence (no URL given; GitHub search blocked).
- Did not test any harness end-to-end with a local model.
- NegotiationArena license file status uncertain (badge only).

## Q4. Peer-review status

### Takeaway
DoND (EMNLP 2017), CaSiNo (NAACL 2021), LAMEN (ICLR 2024), MAgIC (EMNLP 2024), Concordia contest paper (NeurIPS D&B 2025), the LLM-Deliberation repro (TMLR 2025) and PieArena (NeurIPS 2026) are peer-reviewed per primary sources; LLM-Deliberation's NeurIPS 2024 venue is supported indirectly; GTBench's and NegotiationArena's venues were not confirmed; SNB is an unreviewed preprint.

### Cited Findings
- DoND: EMNLP 2017 proceedings — [ACL Anthology](https://aclanthology.org/D17-1259/)
- CaSiNo: NAACL-HLT 2021 proceedings — [ACL Anthology](https://aclanthology.org/2021.naacl-main.254/)
- LAMEN: "Accepted to ICLR 2024" (arXiv comment; v3 posted 18 Feb 2026) — [arXiv](https://arxiv.org/abs/2401.04536)
- LLM-Deliberation: arXiv comment does not state venue (v2 10 Jun 2024) — [arXiv](https://arxiv.org/abs/2309.17234); the FACT29 README links it to a NeurIPS 2024 poster page (neurips.cc/virtual/2024/poster/97850) — [FACT29 README](https://raw.githubusercontent.com/joshrosie/FACT29/main/README.md). D&B track specifically: UNVERIFIED.
- Repro study: "Accepted for publication at TMLR and MLRC Journal Track, 2025"; journal ref "TMLR, June 2025"; arXiv v1 20 Feb 2026 — [arXiv](https://arxiv.org/abs/2602.18230)
- GTBench: arXiv comment lists only pages/HF leaderboard; NeurIPS 2024 not confirmed in opened sources — [arXiv](https://arxiv.org/abs/2402.12348) (UNVERIFIED)
- Concordia contest: "Published at NeurIPS Datasets and Benchmarks 2025" — [arXiv](https://arxiv.org/abs/2512.03318)
- PieArena: "Accepted to NeurIPS 2026" (v4, 16 Nov 2026); README says "NeurIPS 2026, Evaluations & Datasets track" — [arXiv](https://arxiv.org/abs/2602.05302); [README](https://raw.githubusercontent.com/chriszhu-yale/PieArena-Benchmark/main/README.md)
- SNB: no comment/journal ref; single author; v1 2 Jul 2026, v2 1 Oct 2026 — [arXiv](https://arxiv.org/abs/2607.02814)
- NegotiationArena: no venue in arXiv metadata (single version 8 Feb 2024) — [arXiv](https://arxiv.org/abs/2402.05863) (venue UNVERIFIED)
- MAgIC: arXiv comment "EMNLP 2024" — [arXiv](https://arxiv.org/abs/2311.08562)

### Inferences
- If peer review is a hard criterion for a "standard", SNB cannot yet be cited as one; it can be used as a closely matched but provisional instrument.

### Gaps
- Could not open OpenReview/NeurIPS proceedings pages to confirm GTBench, NegotiationArena, LLM-Deliberation track.

## Q5. Concordia Contest specifics: are held-out scenarios and scoring public and reusable as a fixed benchmark; which model

### Takeaway
The development-phase scenarios and the evaluation/Elo scripts are public at tag v1.8.9 (12 scenario configs, including 3 haggling ones), and the official model was gemma-2-9b-it. But the evaluation used 14 held-out scenarios whose background populations included the top-five participants' agents; the public v1.8.9 scenario file has only 12 configs, and I could not confirm the held-out set is released, so it is not demonstrably reusable as a fixed held-out benchmark.

### Cited Findings
- Two phases: development against "publicly available scenarios" and evaluation on "held-out scenarios" — [arXiv HTML](https://arxiv.org/html/2512.03318)
- Evaluation-phase populations contained "pre-defined held-out background players created by The Contest designers, and the agents of the top-five best-performing submissions" — [arXiv HTML](https://arxiv.org/html/2512.03318)
- "the 14 held-out scenarios cover only a slice of the cooperative situations" — [arXiv HTML](https://arxiv.org/html/2512.03318)
- Checklist claims "All necessary code, evaluation scripts, and scenarios are available publicly... tagged releases... (version 1.8.9 of the repository)"; individual agent implementations provided as a zip; replication possible "provided the same language model is used"; "We do not release any data" — [arXiv HTML](https://arxiv.org/html/2512.03318)
- v1.8.9 `SCENARIO_CONFIGS` contains 12 configs: labor_collective_action__fixed_rule_boss_0, labor_collective_action__paranoid_boss_0, pub_coordination_mini, pub_coordination_0, pub_coordination_closures_0, haggling_0 (rational residents), haggling_1 (gullible supporting agents + rational visitor), haggling_multi_item_0 (tags negotiation, hidden information), reality_show_circa_2003_prisoners_dilemma_0, reality_show_circa_2015_prisoners_dilemma_0, plus a reality-show visitor scenario and a state-formation (pre_state_villages) scenario — [scenarios.py v1.8.9](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/examples/modular/scenario/scenarios.py)
- `launch_concordia_challenge_evaluation.py` runs an agent on all scenarios, averages per scenario, writes JSON, then `calculate_ratings.py` computes Elo for agents tested with the same model+embedder; default `--api_type mistral --model codestral-latest`; `--disable_language_model` excludes from Elo — [launcher v1.8.9](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/examples/modular/launch_concordia_challenge_evaluation.py)
- Official model: Gemma-2-9b-it; contest hosted on Codabench (competitions/3888) — [arXiv HTML](https://arxiv.org/html/2512.03318)
- Participants reported scoring markedly higher on development than evaluation scenarios (possible overfitting) — [arXiv HTML](https://arxiv.org/html/2512.03318)

### Inferences
- Scores are relative (Elo among agents sharing a model) and depend on co-player populations that include other submissions, so absolute numbers are not a stable fixed benchmark even if scenarios were public.
- The haggling substrate is single-issue price bargaining against rational or gullible background agents; it adds multi-party/population dynamics but does not escape the price-bargaining paradigm. Its default launcher model (codestral) differs from the contest model (gemma-2-9b-it).

### Gaps
- Whether the 14 held-out evaluation scenario configs are in any public tag/branch: UNVERIFIED (github.com browsing blocked; v1.8.9 scenarios file has 12).
- Contest per-scenario score values not extracted.

## Q6. Other multi-agent negotiation environments found

### Takeaway
Within the time budget I found no additional standard beyond those listed; SNB's related-work table cites Microsoft's social-reasoning-bench and a PrincipalBench scaffold, both unverified here.

### Cited Findings
- SNB references `https://github.com/microsoft/social-reasoning-bench` (2026) and compares against a "PrincipalBench scaffold" — [arXiv HTML v2](https://arxiv.org/html/2607.02814v2)
- SNB cites Miceli-Barone et al. (2026) that LLM counterparties "often fail to exploit a known reservation value" — [arXiv HTML v2](https://arxiv.org/html/2607.02814v2)

### Inferences
- An important design caveat for any LLM-vs-LLM benchmark (LAMEN, LLM-Deliberation, PieArena, NegotiationArena): if the counterparty is an LLM that fails to exploit disclosed information, information leakage has little measured cost; SNB's deterministic exploit-capable counterparty addresses this, which matters for separating "pressure" from "information" effects.

### Gaps
- social-reasoning-bench, PrincipalBench, and Miceli-Barone et al. not opened; not profiled.
