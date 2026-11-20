"""Run score_reasoning.py's CS sections on synthetic CS rows (no model): W1C0 all correct, W0C1 all wrong -> expect 'the clause'."""
import sys, os, json, random
sys.path.insert(0, os.getcwd())
from pilot import clause_swap as CS, score_reasoning as SR
W = "pilot/critique/clause_swap_prerun/work/fake_out"
random.seed(0)
with open(f"{W}/clause_swap.jsonl", "w") as f:
    for p in CS.prompts(False):
        good = p["wording"] == 1
        wa = p["target"][0] if good else (5 if p["target"] != [5] else 6)
        f.write(json.dumps(dict(frame=p["frame"], wording=p["wording"], clause=p["clause"], rung=p["rung"], v=p["v"], c=p["c"],
                                target=p["target"], written_answer=wa, n_new=300, cut_off=False)) + "\n")
with open(f"{W}/clause_swap_sampled.jsonl", "w") as f:
    for p in CS.prompts(True):
        s = [dict(written_answer=random.choice([p["target"][0], 1, None]), n_new=300, cut_off=False) for _ in range(3)]
        f.write(json.dumps(dict(frame=p["frame"], para=0, rung=p["rung"], v=p["v"], c=p["c"], target=p["target"], samples=s)) + "\n")
SR.OUT = W
SR.main()
