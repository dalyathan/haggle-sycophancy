# Single-item buyer–seller price-bargaining benchmarks for LLMs (status as of 2026-11-19)

Method note: I checked papers against arXiv abstract and HTML full texts fetched with curl. I shallow-cloned the GitHub repos with `git clone`, which works even though github.com web pages and api.github.com return 403 through the proxy, and inspected their code locally. The ACL Anthology PDF for CraigslistBargain was fetched and converted to text. Blocked hosts: export.arxiv.org (403), proceedings.mlr.press (403), www.alphaxiv.org (DNS blocked), github.com/Terms-bench org page (403; `git ls-remote` on guessed repo names asked for credentials, which suggests no public repos under those names). Anything verified only through a search-engine snippet is marked **[search-only]**.

Repos cloned (HEAD as of 2026-11-19): TianXiaSJTU/AmazonPriceHistory, vinid/NegotiationArena, SafeRL-Lab/AgenticPay, eilamshapira/GLEE, lechmazur/pact, stanfordnlp/cocoa.

---

## Q1. Which benchmarks exist, and what is their task setup (roles, private values, turns, opponent, determinism)?

### Takeaway
Single-item price-bargaining benchmarks fall into three groups:
1. **Scripted or fixed-opponent setups** that test the model alone:
   - TERMS-Bench: a stochastic simulator counterpart.
   - AmazonHistoryPrice: a fixed ChatGPT counterpart.
   - Bergemann et al.: a fixed GPT-4.1 / o3-mini counterpart in the training study.
2. **LLM-vs-LLM tournaments and arenas**: NegotiationArena, GLEE "negotiation" family, PACT, AgenticPay, and the Bergemann round-robin.
3. **A human dialogue corpus**: CraigslistBargain.

Only TERMS-Bench uses a non-LLM counterpart for the economic decisions. Everything else needs a second LLM, and in most published configs that second LLM is a proprietary API model.

### Cited Findings

**AmazonHistoryPrice / OG-Narrator (Xia et al.)**
- The task is defined as an asymmetric incomplete-information game. The buyer knows a private Budget, the seller knows a private Cost, and neither knows the other's — [arXiv HTML](https://arxiv.org/html/2402.15813)
- The dataset has 930 real products in 18 categories, scraped from camelcamelcamel. List price = historical highest price; Cost = historical lowest price (on average 51.08% of the highest); prices range from 0 to 4500 USD — [arXiv HTML](https://arxiv.org/html/2402.15813)
- Budget = f × list price with f = 0.8, chosen so that only about 5% of sessions are "Conflicting Interest" (no possible agreement, budget < cost). The rest are "Mutual Interest" — [arXiv HTML](https://arxiv.org/html/2402.15813); the code passes `0.8` as budget_factor in [run_2stages.sh](https://raw.githubusercontent.com/TianXiaSJTU/AmazonPriceHistory/main/run_2stages.sh)
- Protocol:
  - Five actions: BUY, SELL, DEAL, REJECT, QUIT.
  - Each turn the agent outputs Thought, Talk and Action. Only Talk and Action are shown to the other side.
  - Prompting is chain-of-thought — [arXiv HTML](https://arxiv.org/html/2402.15813)
  - `max_turns=6` by default in `run_session.py` (cloned repo; [raw](https://raw.githubusercontent.com/TianXiaSJTU/AmazonPriceHistory/main/run_session.py))
- Opponent: ChatGPT (gpt-3.5-turbo-1106) is the fixed counterpart. It is the seller when the tested model is the buyer, and the buyer when the tested model is the seller. The authors chose it because it completed 94.3% of sessions validly — [arXiv HTML](https://arxiv.org/html/2402.15813)
- Determinism: temperature 0 for all models. The authors note that OpenAI's API is nondeterministic, and the code supports two local LLMs for "more deterministic reproduction" — [arXiv HTML](https://arxiv.org/html/2402.15813)
- OG-Narrator is a deterministic Offer Generator. It produces buyer offer factors rising from 0.5 to 1 by linear interpolation, and the LLM only narrates the offer in natural language — [arXiv HTML](https://arxiv.org/html/2402.15813)

**CraigslistBargain (He et al., EMNLP 2018)**
- Setup:
  - Two humans on AMT play buyer and seller over a real sfbay.craigslist.org posting (title, description, photos).
  - The listing price is shown to both sides.
  - The buyer gets a private target price at 0.5×, 0.7× or 0.9× the listing price.
  - Categories: housing, furniture, cars, bikes, phones, electronics.
  - 6,682 human–human dialogues — [ACL Anthology PDF](https://aclanthology.org/D18-1256.pdf)
- Utility definition: linear in the final price. The buyer gets utility 1 at its target price, the seller gets 1 at the listing price, and both get 0 at the midpoint, which makes it zero-sum. In the paper's own agent setup, the seller's bottom line is 0.7× the listing price — [ACL PDF](https://aclanthology.org/D18-1256.pdf)
- This is a dataset plus a 2018 modular-agent paper, not an LLM benchmark harness. Later LLM work reuses its items. Bergemann et al. use its 1,402 items, and AgreeMate uses the dialogues — [Bergemann HTML](https://arxiv.org/html/2604.16472); [AgreeMate HTML](https://arxiv.org/html/2412.18690v1)

**NegotiationArena buy/sell game (Bianchi et al.)**
- Setup:
  - The seller has 1 X and the buyer has 100 ZUPs.
  - The seller's private production cost is 40 and the buyer's private willingness to pay is 60.
  - The game ends when either player accepts, with at most 10 rounds of interaction.
  - The seller moves first — [arXiv HTML](https://arxiv.org/html/2402.05863)
- Variants:
  - Contrasting objectives: seller values 60, buyer only 40, so there is no ZOPA.
  - "Over-valued buyer": willingness to pay an order of magnitude above the seller's cost.
  - Scaled resources — [arXiv HTML](https://arxiv.org/html/2402.05863)
- Opponent is another LLM (GPT-4, GPT-3.5, Claude 2/2.1). Both orderings are run, with 60 negotiations per ordered pair. Temperature 0.7 and a 400-token cap mean the game is stochastic — [arXiv HTML](https://arxiv.org/html/2402.05863)
- In the repo runner (`runner/buysell_main.py`): `iterations=10`, `SellerGoal(cost_of_production=40)`, `BuyerGoal(willingness_to_pay=60)`, and the buyer starts with 1000 money tokens. That differs from the paper's table (100 ZUPs); the runner is an example script — cloned repo ([raw](https://raw.githubusercontent.com/vinid/NegotiationArena/main/runner/buysell_main.py))

**GLEE (Shapira et al.)**
- The relevant family is **"negotiation"**, not "bargaining":
  - Seller Alice and buyer Bob alternate posting prices for one indivisible good, with no discounting.
  - Valuations are V_A = F_A·M and V_B = F_B·M, where F is a factor and M is a scale.
  - Configurable: complete vs incomplete information, finite vs "infinite" (unknown) horizon, structured vs natural-language messages, and the horizon T — [arXiv HTML](https://arxiv.org/html/2410.05254)
  - GLEE's "bargaining" family is a Rubinstein division of money with discount factors, not buyer–seller pricing — [arXiv HTML](https://arxiv.org/html/2410.05254)
- Sample config: `seller_value 1.01`, `buyer_value 1.015`, `product_price_order 1000`, `max_rounds 10`, `messages_allowed true` — cloned repo `sample_configs/negotiation/hf_config.json`
- Opponent is another LLM, or a human through oTree — [arXiv HTML](https://arxiv.org/html/2410.05254)

**AgenticPay (Liu et al.)**
- Scope:
  - 160 multimodal tasks: 4 scenarios (E-commerce, Food Delivery, Ride-hailing, Apartment Rental) × 8 market topologies × 5 tasks.
  - Topologies range from 1 buyer–1 product–1 seller bilateral up to many-to-many.
  - Agents negotiate JSON contracts covering price plus other terms (lease duration, return policy, delivery speed) — [arXiv abstract](https://arxiv.org/abs/2602.06008); [README](https://raw.githubusercontent.com/SafeRL-Lab/AgenticPay/main/README.md)
  - So it is mostly multi-issue, not pure single-price.
- Each side has a private reservation price and utility weights. A deal is valid only if it is individually rational. Negotiation also ends if the horizon is exceeded or feasibility is violated, e.g. negative utility — [arXiv HTML](https://arxiv.org/html/2602.06008)
- Opponent: by default the *same* model plays both buyer and seller (self-play). Decoding uses temperature 0.7, seed 0 and 1024 max tokens. Variance is reported over 3 seeds — [arXiv HTML](https://arxiv.org/html/2602.06008)
- The repo still ships a legacy text-only single-item price task, `Task1_basic_price_negotiation`, with `max_rounds=20` by default — cloned repo `agenticpay/envs/single_buyer_product_seller/Task1_basic_price_negotiation.py`

**TERMS-Bench (Zhang et al.)**
- Setup:
  - The evaluated agent is buyer or seller in single-price bilateral negotiation against an **environment-simulated counterpart**.
  - The counterpart is a fixed, parameterized stochastic kernel with private type (reservation r, urgency κ, stance η).
  - The agent gets only its own reservation value as a hard IR constraint.
  - Offers must respect price bounds and monotonic concession — [arXiv HTML](https://arxiv.org/html/2605.13909)
- Episode structure:
  - Up to K = 10 alternating-offer rounds. Each turn the agent sees the counterpart's price plus sentiment and stance cues, and returns Offer(price, message), Accept, or Reject — [project site](https://terms-bench.github.io)
  - Three regimes: Overlap, Urgency-shift, No-deal.
  - Six counterpart families: Candid, Taciturn, Expressive, Strategic, plus the stress families Stochastic and Adversarial.
  - Blocked over role and opener, 25 episodes per cell, giving 1,800 seeded episodes per agent — [arXiv HTML](https://arxiv.org/html/2605.13909)
- The counterpart's economic actions come from the kernel. A "voice model" fixed to GPT-5.2 only turns the committed actions into language, and "does not affect prices, acceptances, walk-aways, or outcomes" — [arXiv HTML](https://arxiv.org/html/2605.13909)
- Episodes are reproducible from a seed — [site](https://terms-bench.github.io)
- A data-grounded variant uses an 831-product, 14-category subset of AmazonHistoryPrice — [arXiv HTML](https://arxiv.org/html/2605.13909)
- There are also Commerce (dollar profit) and Bankroll modes. Bankroll runs 4 sessions × 50 periods, each starting with $100 — [site](https://terms-bench.github.io)

**Bergemann, Ghili, Hu, Li, Yang**
- Setup:
  - Bilateral trade with private reservation prices, run in an event-driven simulator.
  - Agents act through tool calls (`make_offer`, `send_message`, `quit_negotiation`, `search_price`), so binding offers are separate from chat. Each turn allows up to 3 tool calls, and output has a Thought block and a Code block — [arXiv HTML](https://arxiv.org/html/2604.16472)
  - The seller posts a listing, then the buyer opens.
  - The round limit is set in the paper, but the value sits in a math element I could not extract.
- Item catalog:
  - 2,332 items: 1,402 from CraigslistBargain plus 930 from Amazon Price History.
  - Split 80/8.5/11.5 into train/val/test.
  - Reservation prices are sampled from each item's historical low/high, producing a mix of GFT (gains from trade) and NGFT (no ZOPA) scenarios — [arXiv HTML](https://arxiv.org/html/2604.16472)
- Benchmark: a round-robin of five models over 600 listings (400 GFT + 200 NGFT), 25 pairings, 15,000 negotiations — [arXiv HTML](https://arxiv.org/html/2604.16472)
- Training study:
  - Qwen3-8B and 14B in base, SFT and SFT+GRPO variants, each against GPT-4.1 (the RL training opponent) and o3-mini (unseen), in both roles.
  - 800 scenarios per configuration (400 GFT + 400 NGFT), 19,200 negotiations in total — [arXiv HTML](https://arxiv.org/html/2604.16472)

**PACT (lechmazur)**
- Setup:
  - One buyer with a hidden value vs one seller with a hidden cost, over 20 rounds.
  - Each round: a chat message from each side (≤100 words), then sealed bid and ask in [0..100].
  - A trade executes at the midpoint if bid ≥ ask; at most 1 unit trades per round.
  - Payoffs accumulate across rounds — [README](https://raw.githubusercontent.com/lechmazur/pact/main/README.md); cloned `prompts/`
- It is a **repeated double auction with chat, not a single-sale negotiation**.
- Private values are redrawn each game from uniform, correlated, semi-bimodal or heavy-tailed distributions. Matches are "deterministic given its seed" — [README](https://raw.githubusercontent.com/lechmazur/pact/main/README.md)
- The opponent is another LLM. 9,995 scored games as of the June 21, 2026 aggregate — [README](https://raw.githubusercontent.com/lechmazur/pact/main/README.md)

**BargainArena / HAMBA (Oh et al., arXiv 2505.22998)**
- The abstract describes six scenarios, including deceptive practices and monopolies, plus utility-based metrics (HAMBA) and an in-context feedback method — [arXiv abstract](https://arxiv.org/abs/2505.22998)
- **Both v1 and v2 are withdrawn.** arXiv admin comment: "removed … as the submitter did not have the rights to agree to the license." The full-text HTML for v1 and v2 returns 404 — [arXiv abstract](https://arxiv.org/abs/2505.22998)
- "Nine consumer goods" and co-authors from KAIST/LG AI Research are **[search-only]**. A search snippet also reported that the old arXiv HTML contained an embedded instruction aimed at LLM reviewers; I did not verify this or act on it.

**"LLM Rationalis?" (Shah et al.)**
- Setup:
  - A single house-sale scenario from Heddaya et al. 2023, with a $240,000 asking price and ZOPA of $225k–$235k.
  - Conditions: natural language vs alternating offers only, with and without market context, plus six power-asymmetry (BATNA / time pressure) prompt variants.
  - LLMs play in self-play; human data comes from Heddaya et al. — [arXiv HTML](https://arxiv.org/html/2512.13063)
- It is an analysis paper with a new concession-curve metric, not a reusable benchmark.

**AgreeMate (Chatterjee et al., arXiv 2412.18690)**, an additional benchmark found
- LLM buyer vs LLM seller on CraigslistBargain items, ending at acceptance, rejection, or a maximum turn limit.
- 21 model configurations across 52 buyer/seller combinations. Llama 3.x 3B/8B/70B, with and without CoT and personas, plus fine-tuned Llama-3.2-3B buyer, seller and generalist agents — [arXiv HTML](https://arxiv.org/html/2412.18690v1)

### Inferences
- For "small model as buyer against a fixed opponent", AmazonHistoryPrice and Bergemann et al. are structurally closest: 930 or 2,332 single items, buyer budget as a hard limit, and a no-ZOPA subset. TERMS-Bench fits best conceptually, but it is not runnable locally (see Q4).
- PACT's repeated double auction and AgenticPay's multi-issue contracts are further from "single-item price bargaining".

### Gaps
- Bergemann et al.'s exact maximum round count could not be read: it sits inside a MathML element my extraction dropped.
- BargainArena's task details (turns, opponents, models) cannot be checked against primary text because the paper is withdrawn.

---

## Q2. Metrics: what is scored, and are individual rationality (IR) and information use measured?

### Takeaway
IR is measured explicitly by:
- Bergemann et al.: violation rate, plus NGFT scenarios.
- TERMS-Bench: IR violations, plus false agreement in No-deal episodes.
- AmazonHistoryPrice, implicitly: negative normalized profit, plus CI sessions.
- AgenticPay, as a validity condition.

Information use or opponent modeling is measured directly only by TERMS-Bench (type-belief error, cue penalty, oracle-posterior interventions). AgenticPay elicits opponent reservation estimates in a scratchpad but does not appear to score them.

### Cited Findings

**AmazonHistoryPrice**
- Normalized Profit (NP) per session, and the Sum of NP (SNP) over 930 sessions, split by MI and CI. Also deal rate, valid-session rate, Share of the total available profit, and First Bid Ratio (first bid / budget) — [arXiv HTML](https://arxiv.org/html/2402.15813)
- The prompt states "You can only buy things that cost less than your budget; otherwise, you should quit negotiating." Negative SNP therefore directly indicates IR violation — [arXiv HTML](https://arxiv.org/html/2402.15813)

**NegotiationArena**
- Buyer payoff = willingness to pay − final price, plus win rate. Behavioral probes: anchoring, split-the-difference, and the probability of a "bad counter-offer" (a buyer counter above the seller's opening offer).
- No dedicated IR metric. The 60/40 contrasting-objectives variant shows buyers paying more than 40, i.e. above their value — [arXiv HTML](https://arxiv.org/html/2402.05863)

**GLEE negotiation**
- Self-gain: the agent's effect on its own utility, estimated relative to the mean outcome.
- Efficiency: 1 if Alice values more and does not sell, or if the sale happens at a price beneficial to both.
- Fairness: distance of the price from the "fairest price" — [arXiv HTML](https://arxiv.org/html/2410.05254)
- Efficiency captures mutually beneficial trade, but there is no standalone per-agent IR violation rate.

**CraigslistBargain (2018)**
- Utility (linear in price), fairness, dialogue length, agreement rate, plus human-likeness ratings — [ACL PDF](https://aclanthology.org/D18-1256.pdf)

**AgenticPay**
- GlobalScore, BuyerScore and SellerScore, computed from utilities normalized by maximum joint surplus, with a deal bonus, quality and efficiency bonuses, a discount and a failure penalty. Also timeout rate and average rounds.
- Agreements must be IR to count as valid — [arXiv HTML](https://arxiv.org/html/2602.06008)
- Prompts require a mental-model scratchpad with "[Opponent Reservation Price]: price=…; confidence=…". I found no metric scoring that estimate — [arXiv HTML](https://arxiv.org/html/2602.06008)

**TERMS-Bench**
- Four axes, six headline metrics:
  - Surplus efficiency normalized by ZOPA width (SE⁺) and conditional surplus (CSE⁺).
  - Agreement rate on feasible episodes (AGR⁺) and false-agreement rate on infeasible ones (FAGR⁻).
  - Type-belief error (BE_type: reservation, urgency, stance).
  - Critical violation rate (price bound, IR, invalid action), plus %Oracle against a DP-oracle — [arXiv HTML](https://arxiv.org/html/2605.13909); [site](https://terms-bench.github.io)
- Each turn the agent must output a belief estimate over the counterpart's latent type.
- Information use is measured by:
  - A "cue penalty": surplus with informative vs muted cues.
  - Oracle-posterior and revealed-type interventions, which decompose the gap into inference, uncertainty and control bottlenecks — [arXiv HTML](https://arxiv.org/html/2605.13909)

**Bergemann et al.**
- Three dimensions:
  1. IR: violation rate, i.e. accepting negative utility; every NGFT deal is a violation.
  2. Surplus share in GFT deals.
  3. Deal rate.
- Also behavioral drivers (initial aggressiveness, concession rate, temporal patience) and a price-tier quintile decomposition — [arXiv HTML](https://arxiv.org/html/2604.16472)

**PACT**
- PACT Bilateral Rating: an opponent-adjusted Bradley–Terry-style rating on normalized per-game surplus, relative to truthful baselines.
- Composite Model Score (α = 0.10), profit per round, trade frequency, and bid/ask offset from value or cost — [README](https://raw.githubusercontent.com/lechmazur/pact/main/README.md)
- No explicit IR metric. Bid/ask offset vs value is reported, and invalid price output is "replaced by your private value" — [prompts](https://raw.githubusercontent.com/lechmazur/pact/main/README.md) (cloned `prompts/`)

**LLM Rationalis?**
- Concession curve fitted with tanh, burstiness τ, Concession-Rigidity Index (CRI), anchor, settlement price, and offer rounds — [arXiv HTML](https://arxiv.org/html/2512.13063)

**AgreeMate**
- Agreement rate, dialogue length, fairness, aggressiveness, bias, concession rate, relative efficiency, and a probing ratio — [arXiv HTML](https://arxiv.org/html/2412.18690v1)

### Inferences
- For a study of IR and information use in small buyers, the most suitable metric sets are TERMS-Bench and Bergemann et al. AmazonHistoryPrice's SNP/CI split is a lighter-weight proxy that is runnable today.

### Gaps
- HAMBA's exact definition is unverifiable because the paper is withdrawn.

---

## Q3. Models evaluated and headline numbers, especially open-weight models under 10B and Qwen

### Takeaway
Sub-10B open-weight results exist mainly in three places:
- **AmazonHistoryPrice (2024)**: Qwen-7B-Chat, Mistral-7B, Llama-2-7B, Yi-6B, ChatGLM3-6B, Baichuan2-7B, Phi-2 with OG-Narrator.
- **Bergemann et al.**: Qwen3-8B base, SFT and RL.
- **AgreeMate**: Llama 3.x 3B/8B.

AmazonHistoryPrice is the only benchmark with a published Qwen-<10B buyer result. That model, Qwen-7B-Chat, is the worst buyer (SNP −753) and misreads its role 99% of the time. Newer benchmarks evaluate frontier or ≥31B open models: TERMS-Bench evaluates Gemma-4-31B and the Qwen3.6-Plus API; AgenticPay evaluates Qwen3-VL-32B.

### Cited Findings

**AmazonHistoryPrice buyer results** (vs ChatGPT seller, 930 sessions; SNP over ALL / buyer Share)
- GPT-4: −33.81 / −11.27%
- Mixtral-8x7B: −63.19
- Mistral-7B-Instruct: −89.17 / −27.87%
- Yi-6B: −122.94
- Qwen-14B-Chat: −159.21
- ChatGPT: −164.52
- ChatGLM3-6B: −261.91
- Llama-2-7b-chat: −288.59
- Llama-2-70b: −361.26
- Baichuan2-7B: −603.67
- Qwen-7B-Chat: −753.16 (MI deal rate 62.44%)
- Source for all rows: [arXiv HTML Table 2](https://arxiv.org/html/2402.15813)

Related findings:
- Almost all buyers have negative SNP, meaning a net loss per deal, and model size "can not effectively improve the Buyer's performance" — [arXiv HTML](https://arxiv.org/html/2402.15813)
- Qwen-7B, Qwen-14B and Baichuan2-13B perceive themselves as the seller from the start of the conversation in 99%, 95% and 69% of sessions respectively — [arXiv HTML](https://arxiv.org/html/2402.15813)
- OG-Narrator raises buyer deal rates from 26.67% to 88.88% and multiplies profits roughly tenfold. It also works with Phi-2 (2.7B, not aligned); Table 4 includes Qwen-7B-Chat — [arXiv HTML](https://arxiv.org/html/2402.15813)

**NegotiationArena**
- Evaluated GPT-4 (gpt-4-1106-preview), GPT-3.5 (gpt-3.5-turbo-1106), Claude 2 and Claude 2.1.
- "LLama2-70B had trouble following instructions, so we didn't include it" — [arXiv HTML](https://arxiv.org/html/2402.05863)
- No sub-10B models.

**GLEE**
- 13 LLMs: Claude 3.5/3.7 Sonnet, Gemini 1.5 Flash/Pro, Gemini 2.0 Flash/Flash-Lite, GPT-4o, GPT-4o-mini, o3-mini, Grok 2, Llama 3.1-405B, Llama 3.3-70B, Mistral Large.
- Dataset: 32.9K negotiation games plus 3,405 human participants.
- Negotiation self-gain (Alice/Bob):
  - Llama-3.3-70B: 2.5 / 4.2
  - Claude 3.5 Sonnet: 3.0 / 4.5
  - Humans: −26.6 / −14.5
- No sub-10B or Qwen results in the paper — [arXiv HTML](https://arxiv.org/html/2410.05254)
- The repo's sample configs use Llama-3.1-8B and Phi-3.5-mini (cloned repo), but these are configs, not reported results.

**AgenticPay** (GlobalScore / BuyerScore)
- Gemini 3.1 Pro Preview: 42.3 / 45.6
- GPT-5.4: 35.6 / 34.9
- Claude Sonnet 4.6: 34.8 / 30.7
- Qwen3-VL-32B-Instruct: 25.1 / 23.1
- InternVL3-38B: 22.9 / 21.8
- Source: [arXiv HTML](https://arxiv.org/html/2602.06008)
- Bilateral-only GlobalScore: Qwen3-VL-32B 30.9 → 23.2 in multi-sided markets — [arXiv HTML](https://arxiv.org/html/2602.06008)
- No sub-10B results. The README demos use Qwen3-VL-8B-Instruct — [README](https://raw.githubusercontent.com/SafeRL-Lab/AgenticPay/main/README.md)

**TERMS-Bench**
- 13 LLMs via OpenRouter: Claude Opus 4.6 and 4.7, GLM-5.1, Gemma-4-31B-IT, Gemini-3.1-Pro, DeepSeek-V4-Pro, GPT-5.5, Qwen3.6-Plus, Grok 4.20, Kimi-K2.6, GPT-5.4, Doubao-Seed-2.0-Pro, GPT-4o-mini, plus fixed-concession baselines — [arXiv HTML](https://arxiv.org/html/2605.13909)
- Top results (SE⁺ / %Oracle):
  - Claude Opus 4.6: 0.694 / 76.3%
  - GLM-5.1: 0.686 / 76.8%
  - Gemma-4-31B-IT: 0.640 / 69.9%
- Surplus efficiency varies 3.7× across LLMs. The simplest fixed-concession baseline beats GPT-4o-mini — [arXiv HTML](https://arxiv.org/html/2605.13909)
- No sub-10B models.

**Bergemann et al.**
- Frontier round-robin: DeepSeek-V3-0324, Gemini-2.5-Flash, Gemini-2.5-Pro, GPT-4.1, o3. GFT self-violation rates range from 0.00% (o3) to 2.30% (GPT-4.1 as seller) — [arXiv HTML](https://arxiv.org/html/2604.16472)
- Qwen3-8B buyer surplus share (vs GPT-4.1 / o3-mini):
  - Base: 22.4% / 11.2%
  - SFT: 40.8% / 36.1%
  - RL: 20.4% / 11.6% — [arXiv HTML](https://arxiv.org/html/2604.16472)
- Qwen3-8B buyer deal rate returns to about 69.8% / 69.5% after RL. "8B-Base buyer is the weakest condition overall" — [arXiv HTML](https://arxiv.org/html/2604.16472)
- Buyer IR self-violations stay at or below 0.50% in nearly every cell. The meaningful IR variation is in the seller role: 8B NGFT seller violations go 4.00% → 0.50% → 6.50% vs o3-mini — [arXiv HTML](https://arxiv.org/html/2604.16472)

**PACT**
- 26 models on the leaderboard. Top: GPT-5.5 (high) at 1607.
- Smallest open models listed: Gemma 4 31B Reasoning (1557) and GPT-OSS-120B (1496). Qwen 3.7 Max scores 1511.
- No sub-10B models — [README](https://raw.githubusercontent.com/lechmazur/pact/main/README.md)

**LLM Rationalis?**
- GPT-4.1-mini, GPT-4.1-nano, GPT-4o-mini and o4-mini only.
- All LLM buyers anchor at the $225k floor; humans settle near $230k — [arXiv HTML](https://arxiv.org/html/2512.13063)

**AgreeMate**
- Llama 3.x 3B/8B/70B as buyers and sellers, with and without CoT, plus fine-tuned 3B agents — [arXiv HTML](https://arxiv.org/html/2412.18690v1)

### Inferences
- AmazonHistoryPrice's Qwen-7B role confusion may be partly a harness artifact. `utils/format_tokens.py::format_tokens_qwen` ends the prompt with `<|im_start|><|assistant|>\n` instead of the ChatML `<|im_start|>assistant\n`, so the model sees a malformed assistant turn (cloned repo). This is my reading of the code, not something the authors state.
- Qwen3.5 2B–9B buyers would be new data points on every benchmark. The only nearby published reference is Bergemann et al.'s Qwen3-8B.

### Gaps
- I could not verify the AgreeMate numbers cited by third-party sites (+28.6% success and others).

---

## Q4. Code, data and license: can it run locally with a self-hosted HF/vLLM buyer, and what does a run cost?

### Takeaway
Most practical to run fully locally:
- **GLEE**: native HuggingFace player, but no LICENSE file.
- **AmazonHistoryPrice**: vLLM server path and Apache-2.0, but the default opponent is gpt-3.5-turbo-1106, which must be swapped for a local seller or kept as an API.
- **AgenticPay**: MIT, vLLM/SGLang backends.

Adaptable with moderate work: **NegotiationArena** (MIT badge, OpenAI-compatible client to repoint). Not runnable locally from public code: **TERMS-Bench** (backend submission service), **PACT** (prompts and logs only, no harness), **Bergemann et al.** (no code link found), **BargainArena** (withdrawn).

### Cited Findings

**AmazonHistoryPrice**
- License and setup: Apache-2.0 LICENSE. README steps: `start_vllm_server.sh <model_dir> <gpus>` runs `python -m vllm.entrypoints.api_server`, the legacy `/generate` endpoint at localhost:8000. Then `run_2stages.sh` runs buyer and seller benchmarks and `eval.py` computes metrics — [README](https://raw.githubusercontent.com/TianXiaSJTU/AmazonPriceHistory/main/README.md); cloned `api_setting.py`
- The opponent is hard-coded in `run_2stages.sh` as `gpt35Agent gpt-3.5-turbo-1106`, so OpenAI keys are needed unless you edit it. The paper says the code also supports "Bargaining of two locally deployed LLMs" — [run_2stages.sh](https://raw.githubusercontent.com/TianXiaSJTU/AmazonPriceHistory/main/run_2stages.sh); [arXiv HTML](https://arxiv.org/html/2402.15813)
- Chat templates are hand-written per model family (llama, mistral, yi, phi, chatglm, qwen, baichuan). Qwen3.5 would need a correct template, ideally `tokenizer.apply_chat_template` — cloned `utils/format_tokens.py`
- Cost: "Evaluation of a 34B model over all 930 products … takes roughly 1 hour on a single H800" — [arXiv HTML](https://arxiv.org/html/2402.15813)
- Call count, my estimate: 930 sessions × at most 6 turns × 2 agents ≈ up to about 11k LLM calls per role-run, about half of them to the opponent.

**CraigslistBargain**
- Data on HF as `stanfordnlp/craigslist_bargains`, with the license field "unknown" — [HF API](https://huggingface.co/api/datasets/stanfordnlp/craigslist_bargains)
- The CoCoA code repo is MIT, from 2018, and uses pre-LLM models — cloned stanfordnlp/cocoa LICENSE.md
- There is no LLM harness.

**NegotiationArena**
- The README shows an MIT badge, but there is no LICENSE file in the repo.
- Agents: `ChatGPTAgent`, `ClaudeAgent`, and `LLama2ChatAgent`. The last uses `openai.OpenAI(base_url="https://api.endpoints.anyscale.com/v1")`, so pointing it at a local vLLM OpenAI-compatible server is a small edit.
- Requires `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` for the default agents — [README](https://raw.githubusercontent.com/vinid/NegotiationArena/main/README.md); cloned `negotiationarena/agents/llama2.py`
- Cost, my estimate: ≤10 calls per game; the paper ran 60 games per ordered pair.

**GLEE**
- `players/huggingface_player.py` loads local HF models with optional 4- or 8-bit quantization, `temperature 0.7` and `top_p 0.9` by default. There is also a litellm player for APIs and an oTree human interface — cloned repo
- `python main.py -c sample_configs/negotiation/hf_config.json` runs LLM vs LLM — [README](https://raw.githubusercontent.com/eilamshapira/GLEE/main/README.md)
- No LICENSE file in the repo. Licensing is unverified.

**AgenticPay**
- MIT LICENSE. Backends: `OpenAILLM`/`OpenAIVLM`, `VLLMLLM`, `SGLangVLM`, `Qwen3VL`. Local HF models go in `agenticpay/models/download_models`.
- Legacy Task1 price-negotiation examples exist for API, SGLang and vLLM — [README](https://raw.githubusercontent.com/SafeRL-Lab/AgenticPay/main/README.md)
- In the paper, open models ran on 4× A800 — [arXiv HTML](https://arxiv.org/html/2602.06008)

**TERMS-Bench**
- The paper links `https://github.com/Terms-bench` — [arXiv HTML](https://arxiv.org/html/2605.13909). The org page returned 403 through the proxy, and guessed repo names did not resolve publicly. **Unverified** whether a harness is public.
- The project site offers a "Submit your model" service:
  - "You provide the API access; we run the full diagnostic suite on our backend."
  - Any OpenAI-compatible endpoint is accepted, including "your own self-hosted vLLM / SGLang server."
  - Typical cost $50–$200 for the full suite; turnaround 3–5 business days — [submit page](https://terms-bench.github.io/submit.html)
- So a self-hosted Qwen could be evaluated only by exposing a public endpoint to the organisers.
- Paper runs used OpenRouter, temperature 0, reasoning effort xhigh (costed at 15,200 reasoning tokens per call under a 16,000-token completion budget), and GPT-5.2 as the counterpart voice — [arXiv HTML](https://arxiv.org/html/2605.13909)
- Call count, my estimate: 1,800 episodes × ≤10 rounds ≈ ≤18k agent calls per model.

**Bergemann et al.**
- No GitHub or code link found in the full text. The only GitHub URL is VERL, used for training — [arXiv HTML](https://arxiv.org/html/2604.16472)
- The paper lists API prices of the five frontier models and notes the environment is "configurable" — [arXiv HTML](https://arxiv.org/html/2604.16472)
- Training cost and hardware are in Appendix B, which I did not extract.

**PACT**
- The repo has only README, dossiers, images, `logs/` (jsonl game logs) and `prompts/` (templates). No .py files and no LICENSE — cloned repo
- The prompts and logs are enough to reimplement the protocol (20 rounds, midpoint clearing), but there is no official harness.

**BargainArena**
- Withdrawn from arXiv; no code found — [arXiv abstract](https://arxiv.org/abs/2505.22998)

**LLM Rationalis?**
- No code link found in the HTML — [arXiv HTML](https://arxiv.org/html/2512.13063)

### Inferences
- The most practical path for a Qwen3.5 2B–9B buyer study is the AmazonHistoryPrice harness, run in one of two ways:
  - Swap the ChatGPT seller for a fixed local seller model, which loses comparability with published numbers.
  - Keep gpt-3.5-turbo-1106 as the seller, if it is still served, for comparability. Cost is about 5k short seller calls per run.
- Also patch the Qwen chat template and the legacy vLLM endpoint.
- An alternative is GLEE's negotiation family with `HuggingFacePlayer` on both sides; check licensing first.
- A TERMS-like scripted counterpart would remove opponent-LLM variance. No such public code was found, but Bergemann's protocol and TERMS' kernel are documented in enough detail to reimplement.

### Gaps
- TERMS-Bench code availability; GLEE and NegotiationArena licenses; Bergemann code release; current availability of gpt-3.5-turbo-1106.

---

## Q5. Peer-review status

### Takeaway
Peer reviewed:
- AmazonHistoryPrice: ACL Findings 2024.
- CraigslistBargain: EMNLP 2018.
- NegotiationArena: ICML 2024, confirmed by search only.
- AgenticPay: NeurIPS 2026, per the authors' arXiv comment.
- LLM Rationalis?: NeurIPS 2025 workshop.

Preprints: TERMS-Bench, Bergemann et al., GLEE (venue not found), AgreeMate. BargainArena is withdrawn. PACT is a GitHub leaderboard.

### Cited Findings
- AmazonHistoryPrice: "Accepted by ACL 2024 Findings" (v3, 4 Jun 2024) — [arXiv abstract](https://arxiv.org/abs/2402.15813)
- CraigslistBargain: EMNLP 2018, ACL Anthology D18-1256 — [ACL Anthology](https://aclanthology.org/D18-1256/)
- NegotiationArena: ICML 2024, PMLR vol. 235, pp. 3935–3951 **[search-only]**; proceedings.mlr.press returned 403 — [PMLR via search](https://proceedings.mlr.press/v235/bianchi24a.html). The arXiv HTML uses the ICML template — [arXiv HTML](https://arxiv.org/html/2402.05863)
- AgenticPay: "Accepted at NeurIPS 2026 (Main Track)" (v2, 13 Nov 2026) — [arXiv abstract](https://arxiv.org/abs/2602.06008)
- TERMS-Bench: arXiv preprint, v2 13 Jun 2026 — [arXiv abstract](https://arxiv.org/abs/2605.13909)
- Bergemann et al.: preprint, 10 Apr 2026, 67 pages, cs.GT — [arXiv abstract](https://arxiv.org/abs/2604.16472)
- GLEE: preprint; v3 2 Mar 2026 uses an ACM-style template, but no venue is stated on the abstract page — [arXiv abstract](https://arxiv.org/abs/2410.05254)
- LLM Rationalis?: "Published in the First Workshop on Multi-Turn Interactions in Large Language Models at NeurIPS 2025" — [arXiv abstract](https://arxiv.org/abs/2512.13063)
- BargainArena: withdrawn (v1 and v2) — [arXiv abstract](https://arxiv.org/abs/2505.22998)
- AgreeMate: arXiv preprint, Dec 2024 — [arXiv abstract](https://arxiv.org/abs/2412.18690)
- PACT: GitHub benchmark with no paper; last aggregate June 21, 2026 — [README](https://raw.githubusercontent.com/lechmazur/pact/main/README.md)

### Inferences
- If peer-review status matters, AmazonHistoryPrice is the most established buyer-focused benchmark that is runnable locally.

### Gaps
- GLEE venue; NegotiationArena venue not confirmed from a primary page.

---

## Q6. Summary comparison for choosing a benchmark (small open-weight buyer, local)

### Takeaway
Ranking for "run a local Qwen3.5 2B–9B buyer":
1. AmazonHistoryPrice: buyer-focused, IR measured via SNP and CI, Apache-2.0, vLLM path, published 7B baselines including Qwen-7B. Needs an opponent swap or API, plus template fixes.
2. GLEE negotiation: native HF player, rich parameterization, but LLM opponent, no sub-10B published numbers, no license file.
3. NegotiationArena buy/sell: simple 40/60 game, easy to repoint to vLLM, but only one configuration and GPT/Claude baselines.
4. AgenticPay Task1/bilateral: MIT, vLLM, but the main benchmark is multimodal and multi-issue, self-play.

Best design reference, not locally runnable: TERMS-Bench (scripted counterpart, IR plus belief metrics) and Bergemann et al. (IR violation rate, GFT/NGFT, Qwen3-8B numbers). PACT is a different game (repeated double auction) with no code.

### Cited Findings
- See the per-benchmark citations in Q1–Q5. Key anchors:
  - [AmazonHistoryPrice HTML](https://arxiv.org/html/2402.15813)
  - [TERMS submit page](https://terms-bench.github.io/submit.html)
  - [Bergemann HTML](https://arxiv.org/html/2604.16472)
  - [GLEE README](https://raw.githubusercontent.com/eilamshapira/GLEE/main/README.md)
  - [AgenticPay README](https://raw.githubusercontent.com/SafeRL-Lab/AgenticPay/main/README.md)
  - [NegotiationArena README](https://raw.githubusercontent.com/vinid/NegotiationArena/main/README.md)
  - [PACT README](https://raw.githubusercontent.com/lechmazur/pact/main/README.md)

### Inferences
- A defensible local design: AmazonHistoryPrice items with Budget = 0.8 × list price, a fixed local seller (or a scripted seller in TERMS or Bergemann style), and reported metrics of SNP/MI/CI, IR-violation rate (deals above budget), deal rate and First Bid Ratio. Seed and temperature 0 give determinism.

### Gaps
- No benchmark found publishes Qwen3.5 (2B–9B) buyer results.
