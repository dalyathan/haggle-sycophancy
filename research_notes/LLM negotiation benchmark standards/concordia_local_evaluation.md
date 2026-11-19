# Running Concordia's haggling evaluation (NeurIPS 2024 Concordia Contest protocol) with a local Hugging Face model

Research date: 2026-11-19. Hands-on work was done in scratchpad clones of `google-deepmind/concordia` at tag `v1.8.9` (commit 3643ac0, 2024-11-25) and `main` (commit b3de736, 2026-11-18), with two throwaway venvs (`gdm-concordia==1.8.9` on Python 3.11, `gdm-concordia==2.4.0` on Python 3.12). No model weights were downloaded. All LLM-call counts below come from my own runs with a fake (counting) language model, so they count calls and do not measure quality.

Base URLs used below:
- v1.8.9 code: `https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/<path>`
- main code: `https://raw.githubusercontent.com/google-deepmind/concordia/main/<path>`
- Paper: https://arxiv.org/html/2512.03318 ("Evaluating Generalization Capabilities of LLM-Based Agents in Mixed-Motive Scenarios Using Concordia")

---

## Q1. Which Concordia version to use (v1.8.9 contest-era vs current main), what changed, and what installs today?

### Takeaway
Use the contest-era code: tag **v1.8.9**, or better **1.8.10**, which has the same examples and only removes the pandas pin. It is the only version where the contest evaluation harness exists and works end to end: the scenario configs, focal and background per-capita scoring, `launch_concordia_challenge_evaluation.py` and `calculate_ratings.py`. Current main (v2.x) moved haggling to `examples/games/haggling`. In my runs, main's haggling returns **all-zero focal scores**, and its payoff code credits trades to the wrong players. Main also has no focal-vs-background harness. That makes main unsuitable for reporting the contest metric unless you patch it.

### Cited Findings
- PyPI package name is `gdm-concordia`. The latest release is 2.4.0 (uploaded 2026-03-06, `requires_python >=3.12`). Releases include 1.8.9 (uploaded 2024-11-26), 1.8.10, 2.0.0 (2025-07-07), 2.0.1, 2.1.0, 2.2.0, 2.3.1 and 2.4.0 — [PyPI JSON](https://pypi.org/pypi/gdm-concordia/json)
- v1.8.9's `setup.py` has `version='1.8.9'` and `python_requires='>=3.11'`. It hard-depends on `pandas<=2.0.3`, `transformers`, `ollama`, `openai>=1.3.0`, `mistralai`, `together`, `boto3`, `google-generativeai` and others, but not torch — [v1.8.9 setup.py](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/setup.py)
- CHANGELOG entries:
  - 1.8.9 (2024-11-25): "Update launch and eval scripts for the eval phase of the contest".
  - 1.8.10 (2024-12-19): "Remove version restriction on pandas".
  - 2.0.0 (2025-07-04): "Game masters are now entities", and "prefab" replaces the "now-deprecated 'factory' concept".
  - Source: [CHANGELOG.md (main)](https://raw.githubusercontent.com/google-deepmind/concordia/main/CHANGELOG.md)
- **Verified install (this session):** `uv venv -p 3.11 && uv pip install gdm-concordia==1.8.9` installs and imports. Two fixes were needed:
  - (a) pandas 2.0.3 crashed on import against numpy 2.x ("numpy.dtype size changed…"). Pinning `numpy<2` (got 1.26.4) fixed it.
  - (b) `examples/modular/scenario/supporting_agents.py` imports `immutabledict`, which is not a declared dependency, so it must be `pip install`ed.
  - The `examples/` folder is **not** in the wheel. You must clone the repo at the tag and put it on `PYTHONPATH`. Source: [v1.8.9 launch script docstring: "cd {concordia_root}/ PYTHONPATH=. PYTHONSAFEPATH=1 python examples/modular/launch_concordia_challenge_evaluation.py …"](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/examples/modular/launch_concordia_challenge_evaluation.py)
- **Verified install (this session):** `uv venv -p 3.12 && uv pip install gdm-concordia==2.4.0` installs and imports. Main's `setup.py` has `version='2.4.0'` and `python_requires='>=3.12'`, with optional extras `[huggingface]` (accelerate, torch, transformers) and `[vllm]` (`vllm>=0.21.0`) — [main setup.py](https://raw.githubusercontent.com/google-deepmind/concordia/main/setup.py)
- The v1.8.9 contest harness consists of:
  - `examples/modular/launch_concordia_challenge_evaluation.py`, which runs every scenario in `SCENARIO_CONFIGS`
  - `launch_one_scenario.py`
  - `calculate_ratings.py` (Elo)
  - `scenario/scenarios.py`
  - `environment/haggling.py`
  - Agents live in `concordia/factory/agent/`, which includes `rational_agent.py` and `basic_agent.py`.
  - Source: [v1.8.9 tree, listed from clone]; [launch script](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/examples/modular/launch_concordia_challenge_evaluation.py)
- Main has `examples/games/run.py`, which runs **one** game with **one** model for all players and prints `focal_scores` and `background_scores`. It also has `examples/games/scenarios.py`, which defines `SCENARIO_CONFIGS` including the haggling scenarios, but nothing in the repo imports it (my grep for `games.scenarios` / `SCENARIO_CONFIGS` found no users) — [main run.py](https://raw.githubusercontent.com/google-deepmind/concordia/main/examples/games/run.py); [main scenarios.py](https://raw.githubusercontent.com/google-deepmind/concordia/main/examples/games/scenarios.py)
- In main's `examples/games/haggling/simulation.py`:
  - All `NUM_MAIN_PLAYERS` use `FOCAL_PLAYER_PREFAB`. The configs set `BACKGROUND_PLAYER_PREFAB = "rational__Entity"`, but grep shows nothing reads it.
  - `CumulativePayoff.update_scores` is never called. As a result, `focal_scores` in the returned dict are always 0.0.
  - **Verified by running (this session):** with a scripted model that proposed "3 coins" 6 times and accepted 6 times, run_simulation returned `focal {...: 0.0, ...: 0.0, ...: 0.0}`. The game master's `SequentialBargainPayoff` printed non-zero running totals.
  - Those totals went to the *first* buyer/seller pair ("Juniper" and "Clara") even for a trade where "Silas" accepted. The cause is that every trade is scored with `first_payoff.action_to_scores`, which is bound to `first_buyer` / `first_seller`.
  - Source: [main haggling/simulation.py](https://raw.githubusercontent.com/google-deepmind/concordia/main/examples/games/haggling/simulation.py); [main sequential_bargain_payoff.py](https://raw.githubusercontent.com/google-deepmind/concordia/main/examples/games/haggling/sequential_bargain_payoff.py) (`_player_scores`, `get_scores`, lines ~240–318)

### Inferences
- Recommended stack: clone `concordia` at tag v1.8.10 or v1.8.9 and use Python 3.11. Install `gdm-concordia==1.8.10` (no pandas pin), or `==1.8.9` plus `numpy<2`. Also install `immutabledict`, `sentence-transformers`, and `torch`/`transformers` for the local model. Run with `PYTHONPATH=<clone>`.
- Do not mix in v2 code: the v1 agent "factories" and v2 "prefabs" are different APIs.
- If someone insists on main, they must read scores from the decision game master's `SequentialBargainPayoff.get_scores()` or from the structured log. They must also fix the first-pair scoring bug and write their own focal/background split. That would no longer be "the contest protocol".

### Gaps
- I did not check whether any commit between v1.8.10 and v2.0.0 changed the v1 haggling environment. The v1.8.10 `scenarios.py` lists the same three haggling scenarios, which I verified via raw.githubusercontent.
- The exact code version behind the contest's held-out evaluation-phase scenarios is not public (see Q4).

---

## Q2. How does Concordia plug in language models? Is there a HF/local wrapper, and what interface must a custom wrapper implement?

### Takeaway
The interface is `concordia.language_model.language_model.LanguageModel` with two abstract methods:
- `sample_text(prompt, *, max_tokens, terminators, temperature, timeout, seed, …) -> str`
- `sample_choice(prompt, responses, *, seed) -> (idx, response, debug_dict)`

v1.8.9 has no usable generic HF wrapper. Its `pytorch_gemma` wrapper hard-codes `GemmaForCausalLM`. Its `ollama` and `openai` wrappers can reach a local server. Main has `contrib/language_models/huggingface/huggingface_model.py` (HF transformers, log-prob `sample_choice`) and a `vllm` wrapper, but both have quirks.

For a steered model (activation hooks), write a ~60-line custom HF wrapper and use log-probabilities for `sample_choice`. This is easy because Concordia always asks multiple-choice questions as single letters after a prompt ending in "Answer: (".

### Cited Findings
- Interface:
  - The base class declares abstract `sample_text` and `sample_choice`.
  - Defaults: `DEFAULT_TEMPERATURE = 1.0` on main, `DEFAULT_MAX_TOKENS = 5000`, `DEFAULT_TERMINATORS = ()`, `DEFAULT_TIMEOUT_SECONDS = 60`.
  - The custom exception `InvalidResponseError` is raised when a choice cannot be parsed.
  - Source: [main language_model.py](https://raw.githubusercontent.com/google-deepmind/concordia/main/concordia/language_model/language_model.py); v1.8.9 has the same two methods: [v1.8.9 language_model.py](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/concordia/language_model/language_model.py)
- How choices are asked:
  - `InteractiveDocument.multiple_choice_question` shuffles the answers and writes them as `(a) …`, `(b) …`.
  - It appends `Answer: (`, then calls `self._model.sample_choice(prompt=..., responses=list(options.keys()))`. The responses are the letters `a`, `b`, `c`, ….
  - Source: [v1.8.9 interactive_document.py lines ~284–310](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/concordia/document/interactive_document.py)
  - Main is the same, and skips the model call when there is only one answer: [main interactive_document.py](https://raw.githubusercontent.com/google-deepmind/concordia/main/concordia/document/interactive_document.py)
- v1.8.9 `language_model/utils.py::language_model_setup` supports these `api_type`s: `amazon_bedrock`, `google_aistudio_model`, `google_cloud_custom_model`, `langchain_ollama`, `mistral`, `ollama`, `openai`, `pytorch_gemma`, `together_ai` — [v1.8.9 utils.py](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/concordia/language_model/utils.py)
- v1.8.9 `PyTorchGemmaLanguageModel`:
  - It loads with `transformers.GemmaForCausalLM.from_pretrained`, so it cannot load Qwen. It ignores temperature.
  - Its `sample_choice` greedily decodes 1 token and raises `InvalidResponseError` if that token is not one of the letters.
  - Source: [v1.8.9 pytorch_gemma_model.py](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/concordia/language_model/pytorch_gemma_model.py)
- v1.8.9 `ollama_model.py`'s `sample_choice` asks for JSON (`format='json'`) with retries — [v1.8.9 ollama_model.py](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/concordia/language_model/ollama_model.py)
- v1.8.9 `base_gpt_model.py`'s `sample_choice` calls `sample_text` in a retry loop and parses the answer with `sampling.extract_choice_response`. v1.8.9 `gpt_model.py` builds `openai.OpenAI(api_key=...)` with no `base_url` argument — [v1.8.9 base_gpt_model.py](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/concordia/language_model/base_gpt_model.py); [gpt_model.py](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/concordia/language_model/gpt_model.py)
- Main's registry (`concordia/contrib/language_models/__init__.py`) includes `huggingface` → `HuggingFaceLanguageModel`, `pytorch_gemma`, `vllm` → `VLLMLanguageModel`, `ollama`, `openai` and others. Main's `vllm_model.py` also has `VLLMLora` — [main contrib/language_models/__init__.py](https://raw.githubusercontent.com/google-deepmind/concordia/main/concordia/contrib/language_models/__init__.py); [vllm_model.py](https://raw.githubusercontent.com/google-deepmind/concordia/main/concordia/contrib/language_models/vllm/vllm_model.py)
- Main's `HuggingFaceLanguageModel`, from reading the code:
  - `__init__(model_name, api_key, *, trust_remote_code=True, dtype=torch.float16, …)` requires `api_key` positionally. `language_model_setup` only passes `api_key` if it is not None. So `python -m examples.games.run --api_type=huggingface` without `--api_key` should fail with a TypeError (not run).
  - It loads with `device_map='auto'`.
  - `sample_text` wraps the prompt in the chat template with the system message "You always continue sentences provided by the user and you never repeat what the user already said." It samples with `do_sample=True` and raises temperature 0 to 0.1.
  - `sample_choice` scores `prompt+response` **without** the chat template by summing token log-probs, then picks the argmax.
  - Source: [main huggingface_model.py](https://raw.githubusercontent.com/google-deepmind/concordia/main/concordia/contrib/language_models/huggingface/huggingface_model.py)
- Contest call limit: the evaluation wraps the agent model in `call_limit_wrapper.CallLimitLanguageModel(model)`, default `max_calls=1200`. It returns empty or default output once the limit is hit — [v1.8.9 call_limit_wrapper.py](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/concordia/language_model/call_limit_wrapper.py); paper: "a strict limitation on the number of Large Language Model (LLM) calls an agent can make per step" — [arXiv 2512.03318 §9.2.1](https://arxiv.org/html/2512.03318)

### Inferences
- A recommended custom wrapper for v1.8.x (not run with real weights) works as follows:
  - Subclass `concordia.language_model.language_model.LanguageModel`.
  - Load the model with `AutoModelForCausalLM.from_pretrained(path, torch_dtype=torch.bfloat16, device_map="cuda")` and register any steering hooks.
  - `sample_text`:
    - Apply the chat template with the same system message as Concordia's wrappers.
    - For Qwen3-family templates, pass `enable_thinking=False`. This is an assumption for "Qwen3.5" and must be checked against its `tokenizer_config.json`. Otherwise thinking blocks burn tokens, because Concordia asks for up to 750–6000 `max_tokens`.
    - Cap `max_new_tokens` at something like `min(max_tokens, 512)`.
    - Cut the output at any `terminators`.
    - Strip any `<think>…</think>` block.
  - `sample_choice`:
    - Run one forward pass on the chat-templated prompt plus an assistant prefix `"Answer: ("`, or on the raw prompt, which already ends with "Answer: (".
    - Compare the next-token logits for the letter tokens `a`, `b`, `c`, …, which are single tokens in Qwen tokenizers (verify).
    - Return the argmax, or sample with temperature, and return the log-probs in `debug`.
    - This takes one forward pass per choice and never raises `InvalidResponseError`, unlike the Gemma wrapper.
  - Wrap both methods in a `threading.Lock`. v1.8.9 runs agents and game-master steps concurrently (`concurrency.run_tasks` in [v1.8.9 game_master.py](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/concordia/environment/game_master.py) and memory generation in [haggling.py](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/examples/modular/environment/haggling.py)), and one HF model on one GPU should be called serially.
- Alternatives for a model that is *not* steered:
  - Serve it with vLLM or llama.cpp as an OpenAI-compatible server and use v1.8.9 `--api_type=openai`. `openai.OpenAI()` reads `OPENAI_BASE_URL` from the environment, so no code edits are needed (this is standard openai-python behaviour, not verified in this session).
  - Use `--api_type=ollama`.
  - Choice quality then depends on text parsing, not log-probs.
- For steering-vector work, the custom HF wrapper is the only clean route. vLLM does not expose residual-stream hooks; `VLLMLora` only supports LoRA.

### Gaps
- I did not run any wrapper with real weights. Qwen3.5 chat-template flags and letter tokenization are unverified.
- I did not test thread-safety of HF `generate` under Concordia's concurrency. Using the lock is the conservative choice.

---

## Q3. What embedder is required, and can it run locally?

### Takeaway
A sentence-transformers model, by default **all-mpnet-base-v2**, called as `lambda x: st_model.encode(x, show_progress_bar=False)`. It runs locally on CPU or GPU. Agents use it for associative-memory retrieval, so it should stay fixed across all compared runs.

### Cited Findings
- The v1.8.9 launcher has the flag `--embedder` (default `'all-mpnet-base-v2'`). It loads `sentence_transformers.SentenceTransformer(f'sentence-transformers/{args.embedder_name}')`, and with `--disable_language_model` it uses `lambda x: np.ones(5)`. The embedder name is part of the result filename (`AGENT__MODEL__EMBEDDER.json`), and Elo is only computed among runs with the same model and embedder — [v1.8.9 launch_concordia_challenge_evaluation.py](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/examples/modular/launch_concordia_challenge_evaluation.py); [calculate_ratings.py docstring](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/examples/modular/calculate_ratings.py)
- Main `run.py` hard-codes `sentence_transformers.SentenceTransformer("all-mpnet-base-v2")` — [main run.py](https://raw.githubusercontent.com/google-deepmind/concordia/main/examples/games/run.py)
- **Verified:** the whole v1.8.9 haggling pipeline runs with a dummy constant embedder (`np.ones(5)`). The embedder only matters for retrieval quality, not for whether the code runs (my counting runs, this session).

### Inferences
- `sentence-transformers` is not a declared dependency of `gdm-concordia` 1.8.9 or 2.4.0 (see the `setup.py`s), so it must be pip-installed. all-mpnet-base-v2 is about 110M parameters and is cheap even on CPU compared with the LLM.

### Gaps
- I did not download the embedder (to respect the no-weights constraint).

---

## Q4. Which haggling scenarios are public, what each tests, and how per-capita score is computed and normalized

### Takeaway
At the contest tag (v1.8.9 and v1.8.10), the haggling **scenarios** in `SCENARIO_CONFIGS` are `haggling_0`, `haggling_1` and `haggling_multi_item_0`. The other environment modules (strange_game, stubborn, vegbrooke) exist as time-and-place modules but are not registered as scenarios there. Main's `examples/games/scenarios.py` adds `haggling_strange_game_0`, `haggling_stubborn_one_0`, `haggling_vanilla_0` and `haggling_multi_item_1`, described as "matching deprecated scenario names", but no runner uses it.

The score is the focal per-capita score: the **mean of the raw summed coin profits of all focal players** in an episode, averaged over repetitions. The paper then min–max normalizes to [0,1] per scenario using theoretical minimum and maximum values that it does not publish.

### Cited Findings
- v1.8.9 `SCENARIO_CONFIGS` haggling entries ([v1.8.9 scenarios.py](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/examples/modular/scenario/scenarios.py)):
  - `haggling_0`: "resident population of focal agents in a haggling scenario with no supporting agents and rational residents". Uses `time_and_place_module='fruitville_haggling'`, `background_agent_module='rational_agent'`, `focal_is_resident=True`, tags `('negotiation',)`.
  - `haggling_1`: "visitor focal agent … with a supporting agents who will accept any price". Uses `fruitville_haggling_gullible`, `focal_is_resident=False`.
  - `haggling_multi_item_0`: same idea, but multi-fruit (`fruitville_haggling_multi_fruit_gullible`), tags `('negotiation', 'hidden information')`.
  - Same three in [v1.8.10 scenarios.py](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.10/examples/modular/scenario/scenarios.py).
- Main's `examples/games/scenarios.py` ([main scenarios.py](https://raw.githubusercontent.com/google-deepmind/concordia/main/examples/games/scenarios.py)):
  - `haggling_0` (fruitville, 2 rational background, focal resident).
  - `haggling_1` (fruitville_gullible: 1 supporting agent "who will accept any price. Tests exploitation of naive trading partners").
  - `haggling_strange_game_0` (vegbrooke_strange_game: "no profitable trade – buyer reward (1) is less than seller cost (6). The optimal strategy is not to trade").
  - `haggling_stubborn_one_0` (supporting agent "will only transact at exactly 4 coins", tags negotiation and calculation).
  - `haggling_vanilla_0` (vegbrooke, 3 rational background, focal resident).
  - `haggling_multi_item_0` (gullible, "hidden per-item valuations").
  - `haggling_multi_item_1` (vegbrooke resident).
- Game mechanics in v1.8.9 ([v1.8.9 environment/haggling.py](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/examples/modular/environment/haggling.py)):
  - Each game is a 2-round conversation scene followed by a 1-round decision scene.
  - The buyer chooses from `('1 coin', '2 coins', '3 coins', '4 coins', '5 coins')` and the seller chooses `('accept','reject')`.
  - Buyer payoff = buyer_base_reward − price. Seller payoff = price − seller_base_reward. A rejected offer gives 0.
  - Defaults: `buyer_base_reward` 5–6, `seller_base_reward` 1–2, `num_games=2`, `num_main_players=3`.
  - Pairs are all pairs, or main-vs-support when `only_match_with_support=True`. The first player in a pair is the buyer.
  - In resident/visitor mode, main player index 0 is the visitor and the rest are residents.
- Module parameters, under [v1.8.9 environment/modules/](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/examples/modular/environment/modules/fruitville_haggling_gullible.py):
  - `fruitville_haggling_gullible`: 1 main player and 1 supporting player, `num_games=3`, buyer reward 6, seller cost 1, `only_match_with_support=True`. The supporting puppet has the fixed response "accept" and memories saying it "will accept any" offer. So in haggling_1 the focal agent is **always the buyer**, playing 3 games.
  - `vegbrooke_haggling_stubborn`: 5 games, puppet proposes or accepts only at 4 coins.
  - `vegbrooke_haggling_strange_game`: buyer reward 1, seller cost 6.
  - `vegbrooke_haggling`: 4 main players, 2 games.
- Per-capita computation in v1.8.9 ([launch_concordia_challenge_evaluation.py](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/examples/modular/launch_concordia_challenge_evaluation.py)):
  - If `focal_is_resident`, focal scores are `outcome.resident_scores` and background scores are `visitor_scores`; otherwise the reverse.
  - `focal_per_capita_score = np.mean(focal_scores)`, `background_per_capita_score = np.mean(background_scores)`, `ungrouped_per_capita_score = np.mean(all)`.
  - Each repetition is written as a `ScenarioResult` JSON. Repetitions use `seed=args.seed + repetition_idx`.
- **Verified run output (null model, seed 1):** `haggling_1` returned `resident_scores {}` and `visitor_scores {'Della Plumstone': 8.0}`. Here the gullible supporting agent is not counted as focal or background, so the background mean is NaN. `haggling_0` returned two residents (focal) and one visitor (background). (Run in this session.)
- Normalization in the paper:
  - "Raw scores were first rescaled to the [0,1] interval with a per-scenario min–max normalization based on scenario theoretical minimum and maximum."
  - "Any scores equal to −∞ were replaced with the corresponding theoretical minimum."
  - The mean agent score was 0.426 ± 0.005 (SE).
  - Source: [arXiv 2512.03318 §5 and §9.4.2](https://arxiv.org/html/2512.03318)
- The contest's final ranking used Elo (rational_agent sits near the bottom of the Elo table, e.g. 1443 in the crossplay table), plus Iterative Maximal Lotteries, Copeland and Ranked Pairs. Evaluation-phase scenarios used **held-out** background players and the top-5 submissions as co-players — [arXiv 2512.03318 §4.3, §5, §9.3](https://arxiv.org/html/2512.03318)

### Inferences
- Theoretical bounds for haggling_1, derived by me from the module parameters and not published:
  - Focal buyer, 3 games, reward 6, cost 1, prices 1–5, and a seller who always accepts.
  - The upper bound is 3 × (6−1) = 15, reached by proposing 1 coin every time.
  - Lower bound: a proposal is always accepted, so the minimum is 3 × (6−5) = 3. If the decision step fails to happen and there is no trade, the score is 0. Using 0 as the minimum is conservative.
  - Normalized = (score − min) / (max − min).
- For haggling_0, bounds depend on the sampled per-game rewards and the role assignment for each seed. They can be computed per episode from the scene premises in the log. That is more faithful than one fixed per-scenario number, but differs from the paper.
- The public scenarios are development-phase scenarios. The paper's evaluation-phase numbers come from held-out scenarios and co-players. A student's result is therefore "contest protocol on public dev scenarios", not directly comparable to the paper's figures.

### Gaps
- The paper does not list the evaluation-phase scenario names or the per-scenario theoretical min/max values, and the authors state "We do not release any data" ([arXiv 2512.03318 checklist](https://arxiv.org/html/2512.03318)). Those numbers would have to be derived.
- I did not check whether the main-only scenario names (strange_game, stubborn_one, vanilla) were evaluation-phase scenarios in the contest. Their comment says "matching deprecated scenario names", which suggests some earlier registration that I could not locate in v1.8.9 or v1.8.10.

---

## Q5. How many LLM calls does one haggling episode take, and how long on CPU (4B) vs A10G (9B)?

### Takeaway
Measured with a counting fake model in v1.8.9 (seed 1), one episode takes about 130–260 LLM calls. Agent calls are mostly `sample_text` with prompts of about 3.3–4.5k characters (roughly 0.9–1.2k tokens); `sample_choice` calls are a small minority. My bandwidth-based estimates (not measured):
- On an A10G with a 9B model in bf16: about 3–6 s per call, so roughly 10–25 min per haggling_0 episode.
- On CPU with a 4B model: about 30–90 s per call, so roughly 2–5 h per episode.

The CPU path is impractical for multiple repetitions × scenarios × conditions.

### Cited Findings (all from my runs this session, using scripts in the scratchpad, `count_v189.py` and `count_main.py`)
- v1.8.9, dummy model returning a fixed 2-sentence reply, seed 1:
  - **haggling_0, focal = rational_agent:** 198 calls in total. Game master plus memory generation: 24 text + 6 choice. Each of the 3 main players (2 focal residents, 1 rational visitor): 50–56 text + 4 choice. Average agent prompt is about 3.4k characters.
  - **haggling_0, focal = basic_agent:** 258 calls in total. Each focal resident makes about 91 calls (≈80 text + 12 choice) with prompts averaging about 4.4k characters.
  - **haggling_1, focal = rational_agent:** 171 calls in total. The focal agent makes 48 (45 text + 3 choice). Game master plus gullible puppet make 123.
  - **haggling_multi_item_0, null model (empty replies):** 133 calls. With the null model, haggling_1 dropped to 130, so counts depend somewhat on what the model writes.
  - `max_tokens` requested: agent text calls ask for 750, 1000, 1200, 2000 or 2200 tokens; game-master calls ask for 1000, 4500 or 6000.
- Main (2.x) `fruitville` (3 basic__Entity players) took 167 calls (154 text, 13 choice) with an average prompt of about 4.3k characters. `fruitville_gullible` took about 50 calls.
- Contest-imposed cap: `CallLimitLanguageModel` default `max_calls=1200` per agent — [v1.8.9 call_limit_wrapper.py](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/concordia/language_model/call_limit_wrapper.py)
- The paper gives no compute figures: "We do not have any specific compute requirements other than being able to make LLM API calls with gemma-2-9b-it" — [arXiv 2512.03318 checklist](https://arxiv.org/html/2512.03318)

### Inferences (estimates, not measured)
- **A10G 24 GB, 9B bf16** (about 18 GB of weights, leaving about 5 GB for KV cache):
  - Single-stream decoding is memory-bandwidth bound. 600 GB/s ÷ 18 GB gives an upper bound of about 33 tok/s, so realistically about 20–30 tok/s with HF `generate`.
  - Prefill of about 1k tokens takes well under 1 s.
  - At about 100 output tokens per call, that is about 4–5 s per call, or about 15 min for haggling_0 (≈200 calls). Thinking-mode or long outputs could multiply this several times.
  - vLLM would help mainly when repetitions run concurrently, since it batches them.
  - The steered model itself only handles focal calls (~50–90 per episode). If the background agents and game master use a separate server or model, wall-clock time is dominated by those other calls.
- **CPU, 4B bf16/fp32** (about 8–16 GB):
  - With desktop DDR bandwidth of about 20–60 GB/s, decoding runs at roughly 2–6 tok/s, and prefill of 1k tokens takes about 10–30 s.
  - That is about 30–90 s per call, or about 2–5 h per haggling_0 episode.
  - The contest uses 1+ repetitions × 3 haggling scenarios × (baseline + test). Enough repetitions for statistics (about 5–10) would take days.
- Budget for a meaningful A10G study: 3 scenarios × 2 conditions (rational baseline, test model) × about 10 seeds ≈ 60 episodes × about 15 min ≈ 15 GPU-hours. This is an order-of-magnitude figure.

### Gaps
- No timing with a real LLM. Real outputs change both call counts (conversation lengths, retries) and prompt lengths (memories grow with real text). The counts above are structural approximations.

---

## Q6. Does the game master need an LLM, and can it be the same local model?

### Takeaway
Yes. The game master and supporting puppets use the `model` argument for memory generation, event resolution and observations. In the contest, every component (focal, background, GM) used one shared LLM, Gemma-2-9b-it. It can be the same local model.

For a clean comparison, keep the game master and background agents on a **fixed** model and swap only the focal agent's model. v1.8.9's `override_agent_model` applies to *all* main players (focal and background), so swapping only the focal model needs a small custom focal agent module.

### Cited Findings
- `build_simulation(scenario_config, model, focal_agent_module, embedder, measurements, override_agent_model=None, …, seed=None)` passes `model` to the environment. The environment's `Simulation` uses `self._model = model` for the game master and supporting players. Main players get `model=copy.copy(self._agent_model)`, where `self._agent_model = override_agent_model or model` — [v1.8.9 scenarios.py `build_simulation`](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/examples/modular/scenario/scenarios.py); [v1.8.9 haggling.py lines ~640–740](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/examples/modular/environment/haggling.py)
- The launcher passes `model=model` and `override_agent_model=call_limit_wrapper.CallLimitLanguageModel(model)`, so it is the same LLM everywhere — [v1.8.9 launcher](https://raw.githubusercontent.com/google-deepmind/concordia/v1.8.9/examples/modular/launch_concordia_challenge_evaluation.py)
- Paper:
  - "we selected the Gemma 2 model (9 billion parameters, instruction-tuned) as our LLM API provider"
  - "Gemma-2-9b-it was selected as the official LLM for the competition"
  - The single model "eliminat[es] model capability as a confounding variable".
  - "Each environment was equipped with a language model-based reward model that assigned quantitative scores … based on the outcomes generated by the game master".
  - Source: [arXiv 2512.03318 §4.2, §9.2](https://arxiv.org/html/2512.03318)
- Measured: game-master and supporting calls are 30 of 198 calls in haggling_0 and 123 of 171 in haggling_1 (my runs, see Q5).

### Inferences
- Recipe for "local model as focal, everything else fixed":
  1. Write a module, e.g. `my_focal_agent.py`, whose `build_agent(*, config, model, memory, clock, update_time_interval)` ignores the incoming `model` and calls `rational_agent.build_agent(...)` (or `basic_agent`) with `model=CallLimitLanguageModel(MY_HF_MODEL)`.
  2. Pass that module as `focal_agent_module` to `scenarios_lib.build_simulation`, with `model=<reference LLM>` for the game master and background agents.
  3. The baseline run is identical but uses the reference model for the focal agent too, i.e. focal = `rational_agent` with the reference LLM. That is the paper's baseline reference.
- With only one GPU, the reference and test models can be the same base checkpoint (e.g. Qwen 9B), with steering hooks enabled only in the focal wrapper. Then the baseline equals "unsteered model in the rational_agent scaffold" and only the focal policy differs.
- Because the paper used Gemma-2-9b-it everywhere, results with a different GM and background LLM are not numerically comparable to the paper. They are a within-study comparison under the same protocol.

### Gaps
- I did not test whether a 4B model is a reliable game master, e.g. whether it follows the event-resolution format. Weak game masters can corrupt outcomes, so the HTML logs should be spot-checked.

---

## Q7. How did the paper test significance vs the rational-agent baseline, and can it be replicated?

### Takeaway
The paper fit a **Bayesian mixed-effects beta regression** on per-scenario min–max-normalized scores. It used agent as a fixed effect with `rational_agent` as the reference level and a random intercept per scenario. It reported posterior mean and 95% HDI of each agent's log-odds difference from the baseline, and treated an HDI excluding 0 as significant. Five agents were significantly better.

The paper does not give priors, software, the handling of 0/1 scores, or the data. A faithful-in-spirit replication is easy (bambi/PyMC or brms), but not an exact one.

### Cited Findings
- "we generated a bayesian mixed-effects beta regression model, with a random intercept for each scenario and the rational agent as the baseline reference. This shows that the majority of agents either performed similarly to or significantly worse than the rational agent. Only five agents demonstrated significantly higher performance compared to the rational agent baseline" — [arXiv 2512.03318 §5](https://arxiv.org/html/2512.03318)
- Figure 2 caption: "Posterior distributions (mean and 95% HDI) of agent performance (log-odds difference) relative to the rational agent baseline. Vertical dashed line indicates no difference." — [arXiv 2512.03318](https://arxiv.org/html/2512.03318)
- The paper mentions PyMC only for its separate Measurement Layouts analysis ("easily implemented in probabilistic frameworks such as PyMC"). It does not say which software was used for the beta regression — [arXiv 2512.03318 §9.4.2](https://arxiv.org/html/2512.03318)
- "We do not release any data" — [arXiv 2512.03318 checklist](https://arxiv.org/html/2512.03318)

### Inferences
- Replication recipe (my construction):
  - Data: one row per (agent/condition, scenario, repetition) with normalized focal per-capita score y ∈ [0,1].
  - Beta likelihood needs values strictly inside (0,1). Squeeze with Smithson–Verkuilen: y' = (y·(n−1) + 0.5)/n.
  - Model: `y' ~ condition + (1|scenario)`, family Beta (logit link), with `condition` reference = rational_agent baseline.
    - In Python: `bambi.Model("y ~ condition + (1|scenario)", df, family="beta")`, or R `brms::brm(y ~ condition + (1|scenario), family=Beta())`.
  - Report the posterior mean and 95% HDI of the `condition` coefficient, which is the log-odds difference. Call it significant if the HDI excludes 0, matching Fig. 2.
- With only 3 haggling scenarios, the random intercept per scenario is weakly identified. Use weakly-informative priors, e.g. Normal(0,1.5) on effects and HalfNormal(1) on the scenario SD, and also report a simple paired check, e.g. a per-seed bootstrap of the mean difference.
- Also report raw focal per-capita coins per scenario next to the normalized score, because the normalization bounds are the student's own derivation.

### Gaps
- Priors, software and the 0/1 boundary handling are unpublished, so this is unverifiable. Exact numeric replication of Fig. 2 is impossible without the contest data.

---

## Consolidated recipe (verified pieces marked [V], unverified [U])

1. [V] `git clone https://github.com/google-deepmind/concordia && git -C concordia checkout v1.8.10`. Use v1.8.9 for the exact contest tag; there the haggling scenarios are identical.
2. [V] Create the environment and install dependencies. Add `numpy<2` if you use 1.8.9.
   ```
   uv venv -p 3.11 .venv-concordia
   uv pip install gdm-concordia==1.8.10 immutabledict sentence-transformers torch transformers accelerate
   ```
3. [U] Write `local_hf_model.py`, a `LanguageModel` subclass: chat-templated `sample_text` with thinking disabled and capped `max_new_tokens`, letter-logit `sample_choice`, a threading lock, and optional steering hooks.
4. [U] Write `my_focal_agent.py`, which wraps `concordia.factory.agent.rational_agent.build_agent` (or `basic_agent`) and injects the focal model.
5. [V for the structure, using the counting-model run] Write a driver script modelled on `launch_concordia_challenge_evaluation.py`. Loop over `['haggling_0', 'haggling_1', 'haggling_multi_item_0']` × seeds and call `scenarios_lib.build_simulation(scenario_config=SCENARIO_CONFIGS[name], model=REFERENCE_MODEL, focal_agent_module=my_focal_agent, embedder=st.encode, measurements=Measurements(), override_agent_model=CallLimitLanguageModel(REFERENCE_MODEL), seed=s)`. Run `outcome, html = sim()` and record `np.mean(focal scores)` using the `focal_is_resident` split.
6. Run the baseline with the same driver, using `focal_agent_module=concordia.factory.agent.rational_agent` and the reference model.
7. Min–max normalize per scenario, using derived bounds (e.g. haggling_1: 0 or 3 to 15). Fit the beta regression from Q7.
