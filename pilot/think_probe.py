"""Native thinking-mode probe (LADDER.md, addendum TM; diagnostic, fixed before its data).
Every earlier run set enable_thinking=False. Here the chat template's thinking mode is on: the model writes <think> ... </think>
and then its answer, greedy, at most MAX_NEW (default 1536) new tokens. Second person, paraphrase 0, context 0, the plain R3 question.
Cells: L1y at v = 10, 18; L2y at (v, c) = (2, 1), (2, 3), (6, 7), (10, 9), (14, 3), (18, 7). The answer is the first digit (or "walk")
after </think>; a generation that does not close its thinking is cut off.
Usage: python pilot/think_probe.py ; OUT defaults to pilot/out/think_probe.jsonl (resumes by line count)."""
import importlib, json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUT = os.environ.get("OUT", "pilot/out/think_probe.jsonl")
MAX_NEW = int(os.environ.get("MAX_NEW", 1536))
CELLS = {"L1y": {(10, None), (18, None)}, "L2y": {(2, 1), (2, 3), (6, 7), (10, 9), (14, 3), (18, 7)}}


def prompts():
    out = []
    for rung, keep in CELLS.items():
        sys.argv = [sys.argv[0], rung]
        import pilot.ladder as L
        importlib.reload(L)
        out += [dict(p, variant="TM") for p in L.build() if p["ctx"] == 0 and p["para"] == 0 and (p["v"], p["c"]) in keep]
    return out


def answer_after_think(raw):
    if "</think>" not in raw:
        return None
    tail = raw.split("</think>", 1)[1]
    m = re.search(r"\b(walk|Walk|\d)\b", tail)
    return None if not m else (0 if m.group(1).lower() == "walk" else int(m.group(1)))


def main():
    show = "--show" in sys.argv
    P = prompts()
    if show:
        print([(p["rung"], p["v"], p["c"], p["target"]) for p in P]); return
    import torch
    from pilot import run_pilot as RP
    from pilot.fastread import Reader
    rd = Reader(RP.MODEL); tok = rd.tok
    done = sum(1 for _ in open(OUT)) if os.path.exists(OUT) else 0
    print(f"thinking probe: {len(P)} prompts, {done} done, max {MAX_NEW} new tokens", flush=True)
    with open(OUT, "a") as f:
        for p in P[done:]:
            t = time.time()
            text = tok.apply_chat_template(p["messages"], tokenize=False, add_generation_prompt=True, enable_thinking=True)
            x = rd.ids(text)
            with torch.no_grad():
                o = rd.model.generate(input_ids=x, max_new_tokens=MAX_NEW, do_sample=False, repetition_penalty=1.0,
                                      temperature=None, top_p=None, top_k=None)
            n_new = int(o.shape[1] - x.shape[1]); raw = tok.decode(o[0, x.shape[1]:], skip_special_tokens=False)
            written = answer_after_think(raw)
            rec = {k: v for k, v in p.items() if k not in ("messages", "buyer")}
            rec.update(written_answer=written, n_new=n_new, cut_off="</think>" not in raw, raw=raw, seconds=time.time() - t)
            f.write(json.dumps(rec) + "\n"); f.flush()
            print(f"  {p['rung']} v={p['v']} c={p['c']} target={p['target']} written={written} tokens={n_new} {time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main()
