# Adoption and Standardization of LLM Negotiation/Bargaining Benchmarks (as of 2026-11-19)

Access notes (these affect every section): api.semanticscholar.org, www.semanticscholar.org, scholar.google.com, api.openalex.org, zenodo.org, crfm.stanford.edu, cdn.openai.com/openai.com, deepmind.google/ai.google.dev, assets.claude.com (Anthropic system-card PDFs) and api.github.com were all blocked by the session's network proxy (CONNECT 403 or DNS failure). arxiv.org (abs, html, search) worked through curl, and public GitHub repos could be cloned with `git clone` (file trees inspected at HEAD). **No citation counts could be retrieved from Semantic Scholar or Google Scholar. Every citation count in this file is therefore UNVERIFIED and left blank.** Adoption is judged from what I could check: harness and repo contents, arXiv full-text reuse in recent papers, and vendor technical reports on arXiv.

## Q1. Citation counts and reuse as an evaluation by later independent papers

### Takeaway
I could not get citation counts (Semantic Scholar and Google Scholar were blocked). Full-text checks of 13 recent negotiation papers (2024-2026) show the same pattern across them: almost every new paper introduces its own benchmark. The older ones (Deal or No Deal, CraigslistBargain, NegotiationArena, LLM-Deliberation, AmazonHistoryPrice) mostly appear as related work, and only a handful of independent papers reuse one as an evaluation. Among LLM-era benchmarks, NegotiationArena and LLM-Deliberation (Scoreable Games) have the clearest independent reuse, and AmazonHistoryPrice has some data reuse.

### Cited Findings
- **Citation counts: none verified.** api.semanticscholar.org and www.semanticscholar.org returned proxy 403 / DNS failure. Google Scholar and OpenAlex were also blocked. A web search for NegotiationArena's Semantic Scholar count returned no count. — [WebSearch result: ICML page](https://proceedings.mlr.press/v235/bianchi24a.html) (proceedings.mlr.press itself not opened)
- **NegotiationArena (Bianchi et al., ICML 2024, arXiv 2402.05863) is reused as an evaluation framework.** "The Illusion of Rationality" (arXiv 2512.09254, Dec 2025) says "we revisit the NegotiationArena framework and run controlled simulation experiments on a diverse set of frontier LLMs across three multi turn bargaining games: Buyer Seller, Multi turn Ultimatum, and Resource Exchange", and calls it "foundational work". — [arXiv 2512.09254](https://arxiv.org/abs/2512.09254)
- NegotiationArena is cited (as related work) in PieArena, AgenticPay, TERMS-Bench, SovereignNegotiation-Bench, Bergemann et al. 2604.16472, MERIT/AgoraBench, GLEE and 2511.17990. It is the LLM-era negotiation benchmark that appears in the most of the recent papers I checked (10 of 13 HTML full texts). — full texts: [2602.05302](https://arxiv.org/html/2602.05302), [2602.06008](https://arxiv.org/html/2602.06008), [2605.13909](https://arxiv.org/html/2605.13909), [2607.02814](https://arxiv.org/html/2607.02814), [2604.16472](https://arxiv.org/html/2604.16472), [2602.10467](https://arxiv.org/html/2602.10467), [2410.05254](https://arxiv.org/html/2410.05254), [2511.17990](https://arxiv.org/html/2511.17990)
- **LLM-Deliberation / Scoreable Games (Abdelnabi et al., NeurIPS 2024 D&B, arXiv 2309.17234) has an independent reproduction study:** "[Re] Benchmarking LLM Capabilities in Negotiation through Scoreable Games" (arXiv 2602.18230, Feb 2026). It reran the experiments on more models and found that "while the benchmark is indeed complex, model comparison is ambiguous, raising questions about its objectivity". It also identified "limitations in the experimental setup, particularly in information leakage detection". — [arXiv 2602.18230](https://arxiv.org/abs/2602.18230v1)
- LLM-Deliberation is also cited in AgenticPay, TERMS-Bench, SovereignNegotiation-Bench (9 mentions), 2604.16472, MERIT and GLEE. — full texts linked above
- **AmazonHistoryPrice (Xia et al., ACL Findings 2024, arXiv 2402.15813) has its data reused.** TERMS-Bench says "we instantiate the extension on AmazonHistoryPrice (Xia et al., 2024), a CamelCamelCamel-derived catalog of 831 products across 14 categories", and that it was used "as both an external-validity check on the synthetic findings and a difficulty stress test". MERIT/AgoraBench (2602.10467) includes it in a feature comparison table next to Deal or No Deal, CraigslistBargain and Fu et al. 2023. — [arXiv 2605.13909](https://arxiv.org/html/2605.13909); [arXiv 2602.10467](https://arxiv.org/html/2602.10467)
- **Deal or No Deal (Lewis et al. 2017) and CraigslistBargain (He et al. 2018)** are cited as the classic pre-LLM bargaining datasets. MERIT's Table 1 lists both and says "Existing benchmarks (He et al., 2018; Lewis et al., 2017; Xia et al., 2024; Fu et al., 2023) largely emphasize simplified, single-issue settings." In the recent papers I checked they appear as background rather than as the evaluation. — [arXiv 2602.10467](https://arxiv.org/html/2602.10467)
- **CaSiNo (Chawla et al. 2021)** is cited once each in PieArena, AgenticPay and TERMS-Bench, as related work only. — full texts linked above
- **LAMEN (Davidson et al., ICLR 2024)** is cited in PieArena, 2604.16472 and the [Re] Scoreable Games study. I saw no reuse as an evaluation. — [2602.05302](https://arxiv.org/html/2602.05302), [2604.16472](https://arxiv.org/html/2604.16472)
- **GTBench (Duan et al., NeurIPS 2024)** is cited in GLEE (7 mentions) and TERMS-Bench (4). No reuse as an evaluation was seen. — [2410.05254](https://arxiv.org/html/2410.05254), [2605.13909](https://arxiv.org/html/2605.13909)
- **GLEE (arXiv 2410.05254)** explicitly aims at standardization: "we introduce a benchmark for standardizing research on two-player, sequential, language-based games". It argues that "varying assumptions, design choices and evaluation criteria across studies make it difficult to draw robust and meaningful conclusions". None of the 2026 benchmark papers I checked mention GLEE by name (0 hits in PieArena, AgenticPay, TERMS-Bench, SovereignNegotiation-Bench, 2604.16472). — [arXiv 2410.05254](https://arxiv.org/abs/2410.05254)
- **Concordia Contest (arXiv 2512.03318)** reports results from the NeurIPS 2024 Concordia Contest, with scenarios "ranging from negotiation to collective action problems". It is a one-off contest on general cooperative ability, not a dedicated negotiation benchmark. None of the 2026 negotiation benchmarks I checked mention it. — [arXiv 2512.03318](https://arxiv.org/abs/2512.03318)
- **2026 entrants are new and mostly unreused.**
  - AgenticPay (2602.06008, Feb 2026): 160 multimodal tasks; best GlobalScore 42.3/100 (Gemini 3.1 Pro Preview). — [abs](https://arxiv.org/abs/2602.06008)
  - PieArena (2602.05302, Feb 2026): MBA-course scenarios, BBTL ranking model, 167 human sessions. — [abs](https://arxiv.org/abs/2602.05302)
  - TERMS-Bench (2605.13909, May 2026): Bayesian-game "environment as verifier"; 13 LLM agents. It cites AgenticPay once. — [abs](https://arxiv.org/abs/2605.13909)
  - SovereignNegotiation-Bench (2607.02814, Jul 2026; its HTML title is "Faithful Delegates? Benchmarking the Fiduciary Duties of LLM…"): 1,764 paired scenarios, 17 open-weight models. It cites TERMS-Bench (5 mentions). — [abs](https://arxiv.org/abs/2607.02814)
  - Bergemann et al. (2604.16472, Apr 2026): a bilateral-trade environment, 15,000-negotiation round robin across 5 frontier models, plus SFT+GRPO on Qwen3. It calls its own system "a standardized benchmark" and names ANAC as "a standardized platform" in classical agent negotiation. — [abs](https://arxiv.org/abs/2604.16472), [html](https://arxiv.org/html/2604.16472)
- **Other benchmarks the task list missed:**
  - AgoraBench in the MERIT paper (arXiv 2602.10467): nine settings. — [link](https://arxiv.org/abs/2602.10467)
  - A mechanism-design A2A/MCP negotiation benchmark (arXiv 2608.14613). — [link](https://arxiv.org/abs/2608.14613)
  - A buy-and-sell negotiation game for human-behavior emulation (arXiv 2511.17990). — [link](https://arxiv.org/abs/2511.17990)
  - Fu et al. 2023 self-play bargaining (arXiv 2305.10142), cited in the [LLM-as-Mastermind survey](https://arxiv.org/html/2404.01230)
  - Vending-Bench / Vending-Bench 2 (Andon Labs, arXiv 2502.15840): a long-horizon business simulation that includes negotiating with suppliers. It is not a negotiation benchmark per se; see Q3.
- arXiv abstract/title-level search counts (all fields, arxiv.org/search, run 2026-11-19). This is a weak proxy, because name mentions in abstracts are rare and some names collide with common words. NegotiationArena 2 results; CraigslistBargain 3; DealOrNoDeal 5; GTBench 2; AmazonHistoryPrice 1; AgenticPay 2; PieArena 1; SovereignNegotiation 1; "negotiation benchmark" 153; "bargaining benchmark" 39. — [arXiv search](https://arxiv.org/search/?query=NegotiationArena&searchtype=all)

### Inferences
- Ranking by observable adoption (my judgment, without citation counts):
  1. Deal or No Deal and CraigslistBargain: the most cited historically (pre-LLM, an inference from ubiquity in related work), but rarely the LLM evaluation of choice now.
  2. NegotiationArena: the most-referenced LLM-era framework, with at least one independent reuse as an evaluation.
  3. LLM-Deliberation/Scoreable Games: reproduced independently and widely cited.
  4. AmazonHistoryPrice: dataset reused by TERMS-Bench.
  5. GTBench, LAMEN and GLEE: cited, with no reuse found.
  6. CaSiNo: cited only.
  7. 2026 benchmarks (AgenticPay, PieArena, TERMS-Bench, SovereignNegotiation-Bench, Bergemann et al.): new, with at most a cross-citation or two.
- The field is fragmented. Each new paper builds its own environment and metrics, which is the opposite of standard-benchmark behavior.

### Gaps
- No citation counts (Semantic Scholar and Google Scholar blocked). The report writer should state counts as unavailable or unverified, or obtain them separately.
- Reuse was only checked within the ~13 recent papers I opened. A systematic census of citing papers that use each benchmark as an evaluation was not possible without a citation API.
- I did not open the CaSiNo, CraigslistBargain, Deal or No Deal, LAMEN or GTBench papers themselves in this session.

## Q2. Inclusion in standard harnesses, leaderboards and suites

### Takeaway
None of the major general-purpose suites (HELM, BIG-bench, lm-evaluation-harness, AgentBench) contains a negotiation or bargaining task. The closest thing in standard harnesses is OpenAI's **MakeMePay**, a con-artist persuasion task in which one model tries to get another to donate money. It is in openai/evals and was ported to UK AISI's Inspect evals as `make_me_pay`. It is a persuasion/manipulation eval, not a bargaining benchmark.

### Cited Findings
- **openai/evals** (cloned HEAD 8eac7a7, 2026-04-14) contains `evals/elsuite/make_me_pay/` and no other negotiation or bargaining task by filename. — [openai/evals make_me_pay](https://github.com/openai/evals/tree/main/evals/elsuite/make_me_pay)
- **UKGovernmentBEIS/inspect_evals** (HEAD f79b8be, 2026-11-18) contains `src/inspect_evals/make_me_pay/`. Its README says it "tests whether an AI system can use persuasive language to convince another AI system (the 'mark') to donate money". It cites the paper as the "o1 System Card" and says it was "Originally developed by OpenAI Evals". No other negotiation or bargaining task appears by filename. — [inspect_evals make_me_pay README](https://github.com/UKGovernmentBEIS/inspect_evals/tree/main/src/inspect_evals/make_me_pay)
- **HELM** (stanford-crfm/helm HEAD 63754d0, 2026-06-05): a grep of the full text of `src/helm/benchmark/scenarios/` and `presentation/` for "negotiat|bargain" matched only `best_chatgpt_prompts.yaml`. That file is a list of generic prompts (e.g. "How can I negotiate the best price for my home?"), not a negotiation scenario. — [HELM repo](https://github.com/stanford-crfm/helm)
- **lm-evaluation-harness** (HEAD d6de816, 2026-09-14), **BIG-bench** (HEAD 092b196, 222 task dirs) and **AgentBench** (HEAD d1e4a10): no file or task path matches negotiat/bargain/deal_or/casino/craigslist/ultimatum. — [lm-eval-harness](https://github.com/EleutherAI/lm-evaluation-harness), [BIG-bench](https://github.com/google/BIG-bench), [AgentBench](https://github.com/THUDM/AgentBench)
- Open LLM Leaderboard, LMArena/Chatbot Arena: not checked directly. huggingface.co was reachable but not queried; lmarena was not tried. These are general chat/knowledge leaderboards, and I found no evidence of a negotiation track (unverified).
- Leaderboards exist only inside individual papers. For example, PieArena produces "order-invariant, uncertainty-quantified leaderboards", but within its own benchmark. — [arXiv 2602.05302](https://arxiv.org/abs/2602.05302)
- Vending-Bench 2 has a page on Epoch AI's benchmark hub. A secondary registry describes it as including "negotiation" among other business tasks (not opened/verified). — [Epoch AI](https://epoch.ai/benchmarks/vending-bench-2) (search result only)

### Inferences
- No standard general-purpose harness treats negotiation as a capability category. The only negotiation-like task with broad harness support (MakeMePay) is framed as a dangerous-capability or persuasion test.

### Gaps
- The lm-evaluation-harness, BIG-bench and AgentBench checks were filename/path-level only (blobless clone). A task that mentions negotiation only inside file contents would be missed. HELM was content-grepped.
- Open LLM Leaderboard and LMArena were not directly verified.

## Q3. Vendor model cards and technical reports

### Takeaway
None of the vendor technical reports I could open (GPT-4, Llama 3, Qwen2.5, Qwen3, DeepSeek-V3, DeepSeek-R1, Gemma 3, Gemini 1.0, Gemini 1.5, Mistral 7B, Kimi K2) contains the words "negotiat" or "bargain". The only vendor-reported, negotiation-adjacent scores are OpenAI's MakeMePay (persuasion, in o1-era system cards) and Vending-Bench in Anthropic system cards. Neither is a negotiation benchmark from the academic list, and I could not open either system card directly.

### Cited Findings
- Full-text arXiv HTML greps for "negotiat|bargain" and "MakeMePay|Vending" (2026-11-19) returned 0 hits in every one of these reports:
  - [GPT-4 Technical Report 2303.08774](https://arxiv.org/html/2303.08774)
  - [Llama 3 Herd 2407.21783](https://arxiv.org/html/2407.21783)
  - [Qwen2.5 2412.15115](https://arxiv.org/html/2412.15115)
  - [Qwen3 2505.09388](https://arxiv.org/html/2505.09388)
  - [DeepSeek-V3 2412.19437](https://arxiv.org/html/2412.19437)
  - [DeepSeek-R1 2501.12948](https://arxiv.org/html/2501.12948)
  - [Gemma 3 2503.19786](https://arxiv.org/html/2503.19786)
  - [Gemini 2312.11805](https://arxiv.org/html/2312.11805)
  - [Gemini 1.5 2403.05530](https://arxiv.org/html/2403.05530)
  - [Mistral 7B 2310.06825](https://arxiv.org/html/2310.06825)
  - [Kimi K2 2507.20534](https://arxiv.org/html/2507.20534)
- The Inspect port of MakeMePay names the "o1 System Card" as the source paper, which confirms that OpenAI used MakeMePay in at least the o1 system card. — [inspect_evals make_me_pay README](https://github.com/UKGovernmentBEIS/inspect_evals/tree/main/src/inspect_evals/make_me_pay). I could not open the system card itself (cdn.openai.com blocked).
- The Anthropic system-cards index lists cards including Opus 4.6/4.7/4.8, Opus 5/5.5, Sonnet 5/5.5, Mythos Preview and Fable 5.x/Mythos 5.x. The PDFs (assets.claude.com) were blocked, so I could not verify their contents. — [anthropic.com/system-cards](https://www.anthropic.com/system-cards)
- Secondary sources (unverified) say Vending-Bench 2 appears in Anthropic system cards. A podcast says Andon Labs had its own section in the Mythos Preview system card, reporting "bizarre negotiation behavior". — [latent.space](https://latent.space/p/andon), [benchmark registry](https://shreyaspimpalgaonkar.github.io/benchmark-registry/benchmarks/vending-bench-2/) (search snippets only, not opened)

### Inferences
- No vendor reports a score on any of the academic negotiation benchmarks (Deal or No Deal, CraigslistBargain, CaSiNo, NegotiationArena, LLM-Deliberation, GTBench, GLEE, AgenticPay, PieArena, TERMS-Bench and others) in the reports I could check. This is strong evidence against a de facto standard.

### Gaps
- OpenAI system cards (o1, GPT-4o, GPT-5.x), Google Gemini 2.x/3.x model cards, Meta Llama 4 and the Anthropic PDFs could not be opened. The claims about MakeMePay and Vending-Bench in those cards are partly unverified.

## Q4. Surveys and statements about standardization

### Takeaway
The surveys and benchmark papers repeatedly describe the area as lacking a common standard. No survey or paper names any negotiation benchmark as the accepted standard.

### Cited Findings
- "LLM as a Mastermind: A Survey of Strategic Reasoning with Large Language Models" (arXiv 2404.01230, Apr 2024) says that work favors "customized solutions focused on novel scenarios rather than deep exploration within well-defined benchmarks. This trend hinders direct method comparisons and stifles progress under a common standard." It covers negotiation and bargaining work such as OG-Narrator (Xia et al. 2024), LLM-Deliberation and Fu et al. 2023. — [arXiv 2404.01230](https://arxiv.org/html/2404.01230)
- The [Re] Scoreable Games study says: "evaluation in this domain remains challenging due to a lack of robust and generalizable benchmarks." — [arXiv 2602.18230](https://arxiv.org/abs/2602.18230v1)
- GLEE says it is "essential to establish a clear benchmark that provides a standardized framework" and describes prior studies as using varying assumptions and criteria. — [arXiv 2410.05254](https://arxiv.org/html/2410.05254)
- TERMS-Bench says negotiation "has no intrinsic verifier", and that "existing LLM negotiation evaluations rely on LLM-vs.-LLM interaction or aggregate outcomes such as deal rate". — [arXiv 2605.13909](https://arxiv.org/abs/2605.13909)
- AgenticPay says "existing benchmarks rarely combine multimodal product grounding, multi-issue bargaining, and competitive multi-agent markets". — [arXiv 2602.06008](https://arxiv.org/abs/2602.06008)
- "Game On: A Survey of Strategic Reasoning Benchmarks for LLMs" (Zenodo record 15832279). According to the search extract only (zenodo blocked, unverified), it screened 573 papers, identified 7 primary benchmarks, and names the "lack of standardized metrics" as a main limitation. — [Zenodo](https://zenodo.org/records/15832279) (not opened)
- Bergemann et al. point to ANAC (the Automated Negotiating Agents Competition) as "a standardized platform" in classical, non-LLM agent negotiation. That is the closest thing to a field standard, and it predates LLMs. — [arXiv 2604.16472](https://arxiv.org/html/2604.16472)

### Inferences
- **Conclusion: as of 2026-11-19, no de facto standard LLM negotiation or bargaining benchmark exists.** Every signal checked points the same way:
  - Absent from HELM, BIG-bench, lm-eval-harness and AgentBench.
  - Not reported in any vendor technical report I could open.
  - Each new paper (2024-2026) introduces its own benchmark.
  - Surveys and reproductions explicitly lament the lack of a standard.
- The nearest contenders are NegotiationArena (the most-referenced, with independent reuse) and LLM-Deliberation (independently reproduced, though the reproduction found its model comparisons "ambiguous"). Deal or No Deal and CraigslistBargain remain the canonical legacy datasets.
- In vendor and safety practice, negotiation-adjacent measurement happens through MakeMePay (persuasion) and Vending-Bench (business simulation), not through academic negotiation benchmarks.

### Gaps
- I did not find a 2025-2026 survey devoted only to LLM negotiation on arXiv: title searches for "negotiation survey" and "bargaining survey" returned no LLM survey. One may exist outside arXiv.
- The content of the "Game On" survey is unverified.
