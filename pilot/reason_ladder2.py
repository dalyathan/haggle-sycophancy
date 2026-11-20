"""Reasoning ladder, robustness extension (LADDER.md, addendum RL2; diagnostic, fixed before its data).
Same procedure as reason_ladder.py (reason first, greedy, at most 512 new tokens, the model's written answer and the forced
"Answer:" reading), on 20 cells in four conditions: third person paraphrase 0 (the 5 cells not in RL), third person paraphrase 1,
second person paraphrase 0, second person paraphrase 1. Context 0 throughout.
Cells: L1 at v = 2, 6, 10, 14, 18; L2 at the 10 RL cells plus (6, 5), (10, 7), (14, 3), (14, 9), (18, 3).
Usage: python pilot/reason_ladder2.py ; OUT defaults to pilot/out/reason_ladder2.jsonl (resumes by line count)."""
import importlib, json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np

OUT = os.environ.get("OUT", "pilot/out/reason_ladder2.jsonl")
MAX_NEW = int(os.environ.get("MAX_NEW", 512))
RL_CELLS = {(2, 1), (2, 3), (2, 9), (6, 3), (6, 7), (6, 9), (10, 3), (10, 9), (18, 7), (18, 9)}
NEW_CELLS = {(6, 5), (10, 7), (14, 3), (14, 9), (18, 3)}
ASK = " First work it out briefly, then write Answer: followed by one digit."
CONDITIONS = [("third", 0, "new"), ("third", 1, "all"), ("you", 0, "all"), ("you", 1, "all")]


def rung_prompts(rung, para, which):
    sys.argv = [sys.argv[0], rung]
    import pilot.ladder as L
    importlib.reload(L)
    out = []
    for p in L.build():
        if p["ctx"] != 0 or p["para"] != para:
            continue
        if p["c"] is not None:
            key = (p["v"], p["c"])
            keep = key in NEW_CELLS if which == "new" else key in RL_CELLS | NEW_CELLS
            if not keep:
                continue
        elif which == "new":
            continue
        p["messages"][1]["content"] += ASK
        out.append(p)
    return out


def prompts():
    out = []
    for frame, para, which in CONDITIONS:
        for base in ("L1", "L2"):
            rung = base + ("y" if frame == "you" else "")
            for p in rung_prompts(rung, para, which):
                p["variant"] = "RL2"; p["frame"] = frame
                out.append(p)
    return out


def main():
    show = "--show" in sys.argv
    P = prompts()
    if show:
        from collections import Counter
        print(Counter((p["frame"], p["para"], p["rung"]) for p in P)); print(len(P), "prompts")
        print(P[-1]["messages"][1]["content"]); return
    import torch
    from pilot import readout as RO, run_pilot as RP
    from pilot.fastread import Reader
    RO.VARIANT = "R3"; RO.torch = torch
    rd = Reader(RP.MODEL); tok = rd.tok
    enc = lambda w: tok.encode(w, add_special_tokens=False)
    one = lambda w: (lambda x: x[0] if len(x) == 1 else None)(enc(w))
    ids = dict(dig=[one(d) for d in "0123456789"], space=one(" "), bold=one(" **"),
               walk_sp=[i for i in (one(" walk"), one(" Walk")) if i is not None],
               walk_ns=[i for i in (one("walk"), one("Walk")) if i is not None], words=[])
    done = sum(1 for _ in open(OUT)) if os.path.exists(OUT) else 0
    print(f"reasoning ladder 2: {len(P)} prompts, {done} done, max {MAX_NEW} new tokens", flush=True)
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
            rec = {k: v for k, v in p.items() if k not in ("messages", "buyer")}
            rec.update(probs=q.tolist(), coverage=cov, walk=float(qn[0]), exp_offer=float((np.arange(1, 10) * offer).sum()),
                       written_answer=written, n_new=n_new, cut_off=n_new >= MAX_NEW, raw=raw, seconds=time.time() - t, **extra)
            f.write(json.dumps(rec) + "\n"); f.flush()
            print(f"  {p['frame']} p{p['para']} {p['rung']} v={p['v']} c={p['c']} target={p['target']} written={written} "
                  f"tokens={n_new} {time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main()
