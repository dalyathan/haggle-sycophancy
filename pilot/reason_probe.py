"""Uncapped-reasoning probe (READOUT.md, addendum R5; diagnostic only, fixed before data).
R4 capped reasoning at 100 tokens and 62% of its reasoning was cut off. R5 asks the model to work the problem out step by step,
with up to MAX_NEW (default 1024) greedy tokens, then reads the answer exactly as R1/R4 do ("Answer:" two-sequence reading).
Cells: the 8 baseline blocks with a single optimum, context 0, paraphrase 0 (8 prompts). Also records the answer the model
wrote itself (the first "Answer: <x>" in its text), whether it finished, and the token count.
Usage: python pilot/reason_probe.py ; OUT defaults to pilot/out/reason_probe_R5.jsonl (resumes by line count)."""
import json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.argv = [sys.argv[0], "R4"] + sys.argv[1:]          # build R4 prompts (baselines, R1 instruction), then change the question
import numpy as np
from pilot import readout as RO, run_pilot as RP

OUT = os.environ.get("OUT", "pilot/out/reason_probe_R5.jsonl")
MAX_NEW = int(os.environ.get("MAX_NEW", 1024))
ASK = [" Work it out step by step: for each possible price, how likely the seller is to accept it and what she would earn. "
       "Then write Answer: followed by your answer."]


def prompts():
    P = [p for p in RO.build() if p["ctx"] == 0 and p["para"] == 0 and p["update"] == "move"]
    for p in P:
        u = p["messages"][1]["content"]
        head = u.split(" Think it through")[0]
        p["messages"][1]["content"] = head + ASK[0]
        p["variant"] = "R5"
    return P


def main():
    P = prompts()
    if "--show" in sys.argv:
        print(P[0]["messages"][1]["content"]); print(len(P), "prompts"); return
    import torch
    from pilot.fastread import Reader
    rd = Reader(RP.MODEL); tok = rd.tok
    enc = lambda w: tok.encode(w, add_special_tokens=False)
    one = lambda w: (lambda x: x[0] if len(x) == 1 else None)(enc(w))
    ids = dict(dig=[one(d) for d in "0123456789"], space=one(" "), bold=one(" **"),
               walk_sp=[i for i in (one(" walk"), one(" Walk")) if i is not None],
               walk_ns=[i for i in (one("walk"), one("Walk")) if i is not None], words=[])
    RO.VARIANT = "R4"; RO.torch = torch
    done = sum(1 for _ in open(OUT)) if os.path.exists(OUT) else 0
    print(f"R5 probe: {len(P)} prompts, {done} done, max {MAX_NEW} new tokens", flush=True)
    with open(OUT, "a") as f:
        for p in P[done:]:
            t = time.time()
            x = rd.ids(rd.chat(p["messages"]))
            with torch.no_grad():
                o = rd.model.generate(input_ids=x, max_new_tokens=MAX_NEW, do_sample=False, repetition_penalty=1.0,
                                      temperature=None, top_p=None, top_k=None)
            n_new = int(o.shape[1] - x.shape[1]); raw = tok.decode(o[0, x.shape[1]:], skip_special_tokens=True)
            m = re.search(r"Answer:\s*\**\s*(walk|Walk|\d+)", raw)
            written = None if not m else (0 if m.group(1).lower() == "walk" else int(m.group(1)))
            head = raw.split("Answer")[0].rstrip().rstrip("*").rstrip() + "\n"
            base = rd.chat(p["messages"], head + "Answer:")
            res = rd.multi([base + " 1", base + " **"], None, 3)
            q, extra = RO.read_answer(rd, res, 0, p, ids)
            cov = float(q.sum()); qn = q / cov; offer = qn[1:] / max(qn[1:].sum(), 1e-12)
            eo = float((np.arange(1, 10) * offer).sum())
            rec = {k: v for k, v in p.items() if k not in ("messages", "buyer")}
            rec.update(probs=q.tolist(), coverage=cov, walk=float(qn[0]), exp_offer=eo, exp_u=(eo - 1) / 8,
                       sd_offer=float(np.sqrt((((np.arange(1, 10) - eo) ** 2) * offer).sum())), written_answer=written,
                       n_new=n_new, cut_off=n_new >= MAX_NEW, raw=raw, seconds=time.time() - t, **extra)
            f.write(json.dumps(rec) + "\n"); f.flush()
            print(f"  v={p['v']} hist={int(p['hist'])} target={p['target']} written={written} read exp_offer={eo:.2f} "
                  f"tokens={n_new} {time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main()
