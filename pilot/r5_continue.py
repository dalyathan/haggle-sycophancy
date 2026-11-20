"""R5b: continue the R5 generations past their 1,024-token cut (LADDER.md / READOUT.md addendum R5b; diagnostic, fixed before its data).
All 8 R5 generations stopped at 1,024 tokens without an answer while still tabulating acceptance probabilities (correctly in 7 of 8).
Greedy decoding is deterministic, so each generation is continued from its stored text (prompt + the 1,024 tokens as the assistant's
prefix) for up to MAX_MORE (default 2048) further tokens, 3,072 in all. The written answer is the first "Answer: <x>" in the whole text.
Usage: python pilot/r5_continue.py ; OUT defaults to pilot/out/reason_probe_R5b.jsonl (resumes by line count)."""
import json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SRC = "pilot/out/reason_probe_R5.jsonl"
OUT = os.environ.get("OUT", "pilot/out/reason_probe_R5b.jsonl")
MAX_MORE = int(os.environ.get("MAX_MORE", 2048))


def main():
    from pilot import reason_probe as R5
    P = R5.prompts()
    rows = [json.loads(l) for l in open(SRC)]
    assert len(rows) == len(P) and all(r["v"] == p["v"] and r["hist"] == p["hist"] for r, p in zip(rows, P))
    import torch
    from pilot import run_pilot as RP
    from pilot.fastread import Reader
    rd = Reader(RP.MODEL); tok = rd.tok
    done = sum(1 for _ in open(OUT)) if os.path.exists(OUT) else 0
    print(f"R5b: continuing {len(P)} generations, {done} done, up to {MAX_MORE} more tokens each", flush=True)
    with open(OUT, "a") as f:
        for p, r in list(zip(P, rows))[done:]:
            t = time.time()
            x = rd.ids(rd.chat(p["messages"], r["raw"]))
            with torch.no_grad():
                o = rd.model.generate(input_ids=x, max_new_tokens=MAX_MORE, do_sample=False, repetition_penalty=1.0,
                                      temperature=None, top_p=None, top_k=None)
            more = tok.decode(o[0, x.shape[1]:], skip_special_tokens=True); n_more = int(o.shape[1] - x.shape[1])
            full = r["raw"] + more
            m = re.search(r"Answer:\s*\**\s*(walk|Walk|\d+)", full)
            written = None if not m else (0 if m.group(1).lower() == "walk" else int(m.group(1)))
            U = r["U"]; best = max(max(U), 0.0)
            regret = None if written is None else best - (0.0 if written == 0 or written > 9 else U[written - 1])
            rec = dict(v=r["v"], hist=r["hist"], target=r["target"], U=U, written_answer=written, regret=regret,
                       n_total=r["n_new"] + n_more, cut_off=n_more >= MAX_MORE and written is None, more=more, seconds=time.time() - t)
            f.write(json.dumps(rec) + "\n"); f.flush()
            print(f"  v={r['v']} hist={int(r['hist'])} target={r['target']} written={written} regret={regret} "
                  f"tokens={r['n_new'] + n_more} {time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main()
