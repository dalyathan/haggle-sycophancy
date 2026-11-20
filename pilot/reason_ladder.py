"""Reasoning ladder (LADDER.md, addendum RL; diagnostic, fixed before data).
The single-pass ladder asks whether the model plays the trivial rungs in one step. This asks whether it plays them when it may reason
first: the L1 and L2 rungs (third person), one context, one paraphrase, a short reasoning instruction, greedy generation of at most
MAX_NEW (default 512) tokens, then the model's own written answer and the forced "Answer:" reading (as R5).
Cells: L1 at v = 2, 6, 10, 14, 18; L2 at (v, c) = (2, 1), (2, 3), (2, 9), (6, 3), (6, 7), (6, 9), (10, 3), (10, 9), (18, 7), (18, 9):
every value with a trade, four walk cells at the two values that have both, and a cost just below a high value. 15 prompts.
Usage: python pilot/reason_ladder.py ; OUT defaults to pilot/out/reason_ladder.jsonl (resumes by line count)."""
import importlib, json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np

OUT = os.environ.get("OUT", "pilot/out/reason_ladder.jsonl")
MAX_NEW = int(os.environ.get("MAX_NEW", 512))
L2_CELLS = {(2, 1), (2, 3), (2, 9), (6, 3), (6, 7), (6, 9), (10, 3), (10, 9), (18, 7), (18, 9)}
ASK = [" First work it out briefly, then write Answer: followed by one digit."]


def prompts():
    out = []
    for rung in ("L1", "L2"):
        sys.argv = [sys.argv[0], rung]
        import pilot.ladder as L
        importlib.reload(L)
        for p in L.build():
            if p["ctx"] != 0 or p["para"] != 0:
                continue
            if rung == "L2" and (p["v"], p["c"]) not in L2_CELLS:
                continue
            p["messages"][1]["content"] += ASK[0]
            p["variant"] = "RL"
            out.append(p)
    return out


def main():
    show = "--show" in sys.argv
    P = prompts()
    if show:
        print(P[-1]["messages"][0]["content"][-400:]); print("---"); print(P[-1]["messages"][1]["content"]); print(len(P), "prompts"); return
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
    print(f"reasoning ladder: {len(P)} prompts, {done} done, max {MAX_NEW} new tokens", flush=True)
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
            rec.update(probs=q.tolist(), coverage=cov, walk=float(qn[0]), exp_offer=eo, written_answer=written, n_new=n_new,
                       cut_off=n_new >= MAX_NEW, raw=raw, seconds=time.time() - t, **extra)
            f.write(json.dumps(rec) + "\n"); f.flush()
            print(f"  {p['rung']} v={p['v']} c={p['c']} target={p['target']} written={written} read argmax={int(np.argmax(qn))} "
                  f"tokens={n_new} {time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main()
