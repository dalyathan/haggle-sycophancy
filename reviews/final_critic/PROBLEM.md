# Problem statement

Verbatim from the opening of spec/spec_v0.1.md, the earliest written statement of the project.

**Purpose.** This document defines, mathematically and self-containedly, the space of candidate benchmarks
that will be searched for an optimal benchmark, together with the properties and axioms the search relies
on. It is written to be critiqued without any other context.

**Study context.** The benchmark must measure whether a *buyer* language model, haggling over a price,
(a) caves to *social pressure* that carries no payoff-relevant information, versus (b) correctly *updates*
on real information. Models under test are small open-weight LLMs (Qwen3.5 2B to 9B), read out locally;
activation steering will be applied later, without training. The design starts from the Fruitville haggling
scenario of DeepMind's Concordia (NeurIPS 2024 contest, tag v1.8.9).
