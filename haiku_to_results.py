"""Convert Claude agents' text answers into gate.py's results format.

Usage: python haiku_to_results.py [answers_dir] [out_file]   (default: haiku results_gate_haiku.jsonl)

Each answer becomes a one-hot distribution, so P(k) in gate_report.py reads as
the fraction of contexts in which the model chose k coins. Missing or invalid
answers count as coverage 0.
"""
import json, os, sys

from gate import build_prompts

src = sys.argv[1] if len(sys.argv) > 1 else "haiku"
out = sys.argv[2] if len(sys.argv) > 2 else f"results_gate_{src}.jsonl"
prompts = build_prompts()
answers = {}
for letter in "ABCDEFGH":
    path = f"{src}/answers_{letter}.json"
    if os.path.exists(path):
        answers.update({int(k): v for k, v in json.load(open(path)).items()})

missing = 0
with open(out, "w") as f:
    for i, p in enumerate(prompts):
        a = answers.get(i)
        ok = isinstance(a, int) and 1 <= a <= 5
        missing += not ok
        dist = [1.0 if ok and k == a else 0.0 for k in range(1, 6)] if ok else [0.2] * 5
        rec = {k: p[k] for k in ("probe", "V", "para", "pair", "opening")}
        rec.update(coverage=1.0 if ok else 0.0, mass_6_9=0.0, dist=dist,
                   expected=float(a) if ok else 3.0, argmax=a if ok else 3,
                   top3=[], n_tokens=0, seconds=0.0)
        f.write(json.dumps(rec) + "\n")
print(f"{len(prompts)} prompts, {len(answers)} answers, {missing} missing/invalid -> {out}")
