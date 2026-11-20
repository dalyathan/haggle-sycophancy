"""Reproducibility check for the clause-swap test (LADDER.md addendum CS, pre-run review R3; fixed before its data).
Regenerates 6 stored RL/RL2 prompts in the current environment with the same procedure (greedy, at most 512 new tokens) and
reports whether the generated text is byte-identical to the stored one. Output: pilot/out/repro_check.jsonl."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUT = os.environ.get("OUT", "pilot/out/repro_check.jsonl")
# (source file, frame, para, rung, v, c)
PICK = [("reason_ladder2.jsonl", "third", 1, "L2", 6, 7), ("reason_ladder2.jsonl", "third", 1, "L2", 2, 9),
        ("reason_ladder2.jsonl", "you", 0, "L2y", 14, 9), ("reason_ladder2.jsonl", "third", 1, "L1", 10, None),
        ("reason_ladder.jsonl", "third", 0, "L2", 10, 3), ("reason_ladder2.jsonl", "you", 1, "L2y", 10, 3)]


def main():
    from pilot import reason_ladder as RL, reason_ladder2 as R2
    built = {("reason_ladder.jsonl", "third", p["para"], p["rung"], p["v"], p["c"]): p for p in RL.prompts()}
    built.update({("reason_ladder2.jsonl", p["frame"], p["para"], p["rung"], p["v"], p["c"]): p for p in R2.prompts()})
    stored = {}
    for src in ("reason_ladder.jsonl", "reason_ladder2.jsonl"):
        for r in map(json.loads, open(os.path.join("pilot/out", src))):
            stored[(src, r.get("frame", "third"), r["para"], r["rung"], r["v"], r["c"])] = r
    import torch
    from pilot import run_pilot as RP
    from pilot.fastread import Reader
    rd = Reader(RP.MODEL); tok = rd.tok
    with open(OUT, "w") as f:
        for key in PICK:
            p, s = built[key], stored[key]
            assert p["hash"] == s["hash"], key
            x = rd.ids(rd.chat(p["messages"]))
            with torch.no_grad():
                o = rd.model.generate(input_ids=x, max_new_tokens=512, do_sample=False, repetition_penalty=1.0,
                                      temperature=None, top_p=None, top_k=None)
            raw = tok.decode(o[0, x.shape[1]:], skip_special_tokens=True)
            same = raw == s["raw"]
            k = next((i for i, (a, b) in enumerate(zip(raw, s["raw"])) if a != b), min(len(raw), len(s["raw"])))
            rec = dict(key=list(key), identical=same, first_difference_at_char=None if same else k,
                       n_new=int(o.shape[1] - x.shape[1]), stored_n_new=s["n_new"], raw=raw)
            f.write(json.dumps(rec) + "\n"); f.flush()
            print(key, "identical" if same else f"DIFFERS from char {k}", flush=True)


if __name__ == "__main__":
    main()
