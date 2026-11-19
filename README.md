# haggle-sycophancy

Does an LLM buyer in a price negotiation cave to social pressure, or update only on real information? This repo holds the game theory, the benchmark-design search and the statistics for measuring that, as groundwork for steering open-weight models away from sycophancy without training.

The current specification is [`spec/spec_v0.9.md`](spec/spec_v0.9.md); v0.8 to v0.4 and v0.1 are kept beside it.

## How it fits together

1. **Game kernel** (`kernel.py`): one-shot bilateral trade with four seller types, credible versus cheap-talk information, walk-away and a rejected-offer history. Every item's optimal offer is computed exactly with rational arithmetic, under conventions C1 to C8; tied optima are not scored. This is the trusted part: the search calls it but never changes it.
2. **Stage A** (`stage_a.py`): enumerates the 518,400 raw benchmark configurations and applies constraints K1 to K6, leaving 39,540 (9,885 distinct game structures) in about 30 seconds. Output: `stage_a_feasible.jsonl`.
3. **Statistics** (`stats_layer.py`): a model that separates yielding to the seller, following the buyer's companion, updating on information (overall and on the seller's credible claims) and believing the seller's cheap talk. For each design, the item count N* needed for a paired steering test with power 0.8 (less yielding to the seller, unchanged updating, no shift in offer level), then successive halving:
   - rung 1: closed-form power for every design;
   - rung 2: misspecified simulation for the best 1,000;
   - rung 3: validity gates V2 to V4 and a type-I-error gate (bias, coverage, size, a synthetic buyer panel) for the best 50.

   Runs are checkpointed and resumable. Work is split across worker processes, and each design's seed comes from its id.
4. **Capability gate** (`gate.py`, `gate_report.py`): a single-pass buyer test using Concordia's Fruitville haggling text, run on Qwen3.5-4B, Claude Haiku and Claude Sonnet.

## Current result

Spec v0.9 (branch `critique-loop`). 38 of the 50 cheapest designs pass every simulated gate, and the four cheapest pass again with fresh seeds; the selected design needs 106,488 items. A held-out red-team panel then fooled the evaluator in every case (12 of 12 bad buyers unflagged, 8 of 8 fake steering wins certified; [`heldout/RESULTS.md`](heldout/RESULTS.md)), so the steering test is not ready to pre-register. Details: spec section 6.7.

## Running it

```bash
python -m venv .venv && .venv/bin/pip install numpy          # kernel, stage A, statistics
.venv/bin/python test_kernel.py                              # stage-0 checks (9 tests)
.venv/bin/python stage_a.py stage_a_feasible.jsonl           # about 30 s
WORKERS=4 .venv/bin/python stats_layer.py                    # hours on 4 cores; resumes if stopped
# or split rungs 2 and 3 across machines: STOP_AFTER=check, then share.py <rung> k n on each, then merge.py <rung>
.venv/bin/python confirm.py                                  # fresh-seed rerun of the cheapest passing designs
```

The model scripts (`capability_check.py`, `gate.py`, `smoke_test.py`, `review/probe.py`) also need `torch`, `transformers`, `accelerate` and `psutil`, and model weights under `models/` (not committed). Tested with Python 3.13, numpy 2.5, torch 2.15 and transformers 5.23.

## Layout

| Path | What |
| --- | --- |
| `kernel.py`, `test_kernel.py`, `stage_a.py` | game kernel, its tests, the design-space enumeration |
| `stats_layer.py`, `confirm.py`, `share.py`, `merge.py` | model, power, rungs and gates; fresh-seed confirmation; splitting a rung across machines |
| `heldout/`, `heldout_eval.py` | held-out adversarial panel and its scoring harness |
| `stats_out/` | current results (`v09/`), earlier versions' results (`v08/` to `v04/`) and earlier runs kept for comparison (`pre_fix/`, `linear_dose/`, `anchored_C7_partial/`, `serial_partial/`) |
| `gate.py`, `gate_report.py`, `results_gate_*.jsonl`, `haiku/`, `sonnet/` | capability gate and its results |
| `capability_check.py`, `analyze.py`, `results_2b.jsonl`, `results_4b.jsonl` | first readout checks on Qwen3.5-2B and 4B |
| `kernel_proto.py`, `enum_v03.py` | v0.3 prototypes, superseded by `kernel.py` and `stage_a.py` |
| `reports/`, `research_notes/` | literature reviews: negotiation benchmarks, search-problem formulations |
| `spec/` | the specification, v0.1 and v0.4 to v0.9 |

## Not done yet

Stages that need real models (B onward: measuring the variance components, wording search, steering vectors), to run on an A10G with 7 to 9B models.
