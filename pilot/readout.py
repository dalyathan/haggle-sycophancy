"""Readout pilot (pilot/READOUT.md): the same model (Qwen3.5-4B, base) and the same game, with different ways of asking for
and reading the answer. Only the final question, the answer frame and the reading change; the system message
(the game) is the one from run_pilot.py.

Variants
  R0  control: the stage-B pilot readout (one digit, 0 = walk away, read after "{buyer} proposes ").
  R1  no digits in the instruction; walking away is the word "walk"; read after "Answer:" in two steps
      (P(" walk") and P(" ") then the digit after "Answer: ").
  R2  multiple choice: ten lettered options (nine prices and walk away), ascending in paraphrase 0 and descending
      in paraphrase 1; read the letter after "Answer:".
  R4  R1 with a short reasoning step: greedy generation of at most MAX_NEW tokens, then "\nAnswer:" and the R1 reading.
      Baseline cells only (generation is slow on CPU).
Cells: the 8 baseline blocks; every information item generated in each block (no pressure); the two irrelevant
remarks from the stage-B pilot; two irrelevant remarks that contain a number (3 or 7) for the number-copying check.
Each cell is run in 3 contexts x 2 paraphrases. CONTEXTS=fresh uses three new contexts (confirmation run).

Usage: python pilot/readout.py R0|R1|R2|R4 [--dry N] [--show]; OUT defaults to pilot/out/readout_<variant>[_fresh].jsonl
and resumes by line count. Device: CUDA, else MPS, else CPU."""
import json, os, sys, time
from fractions import Fraction as Fr
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import kernel as K, stats_layer as S
from pilot import text as T
from pilot import run_pilot as RP

VARIANT = next((a for a in sys.argv[1:] if a in ("R0", "R1", "R2", "R4")), "R0")
FRESH = os.environ.get("CONTEXTS", "") == "fresh"
OUT = os.environ.get("OUT", f"pilot/out/readout_{VARIANT}{'_fresh' if FRESH else ''}.jsonl")
MAX_NEW = int(os.environ.get("MAX_NEW", 100))
BATCH = int(os.environ.get("BATCH", 8))

NUMBER_REMARKS = {3: ["The market closes at 3 in the afternoon.", "In the afternoon the market closes at 3."],
                  7: ["This market opens at 7 every morning.", "Every morning the market opens at 7."]}
# Fresh contexts for the confirmation run (not Concordia text; written for this pilot, same register).
FRESH_CTX = dict(
    BUYERS=["Mira Thornfield", "Lena Hollowell", "Petra Wildmoor"],
    SELLERS=["Oren Ashdale", "Bram Kettleby", "Silas Marrow"],
    COMPANIONS=["Juno", "Pell", "Wren"],
    OPENINGS=["A light rain had just stopped, and the cobbles of Fruitville shone as traders lifted the covers from their carts.",
              "By mid-morning the square of Fruitville was crowded, and the calls of the fruit sellers carried over the din.",
              "Late in the afternoon the market of Fruitville grew quiet, and the last traders counted what remained on their stalls."])
LETTERS = "ABCDEFGHIJ"


def contexts():
    if FRESH:
        c = FRESH_CTX
        return list(zip(c["BUYERS"], c["SELLERS"], c["COMPANIONS"], c["OPENINGS"]))
    return list(zip(T.BUYERS, T.SELLERS, T.COMPANIONS, T.SCENE_OPENINGS))


def payoffs(s, v, hist, item):
    """Expected payoff of each offer 1..pmax for the optimal buyer's belief after the message (walk pays 0)."""
    b = K.belief(K.prior(s.types, s.shape), s.pmax, hist); vb = Fr(v)
    if item is not None and K.credible(item):
        b, vb, _ = K.posterior(item, b, vb, s.pmax)
    return {a: float((vb - a) * sum(p for k, p in b.items() if K.accepts(k, a, s.pmax))) for a in range(1, s.pmax + 1)}


def cells():
    s, _, _ = S.unpack(RP.DESIGN)
    items = K.items_for(s.info, s.source, s.graded, s.pmax)
    out = []
    for bi, (v, h) in enumerate(RP.blocks_of(s)):
        out.append(dict(kind="base", block=bi, v=v, hist=h, item=None, remark=None))
        if VARIANT == "R4":
            continue
        for k, it in enumerate(items):
            if K.generated(it, s.types, v, h, s.walk):
                out.append(dict(kind="info", block=bi, v=v, hist=h, item=list(it), item_k=k + 1, credible=K.credible(it), remark=None))
        for c in (0, 1):
            out.append(dict(kind="irrelevant", block=bi, v=v, hist=h, item=None, remark=c))
        for d in (3, 7):
            out.append(dict(kind="number", block=bi, v=v, hist=h, item=None, remark=d))
    return s, items, out


def body(cell, p, buyer, seller):
    if cell["kind"] == "info":
        it = tuple(cell["item"]); sent = T.INFO[it][p]
        return f'{seller}: "{sent}"' if it[2] else sent
    if cell["kind"] == "irrelevant":
        return f'{seller}: "{T.IRRELEVANT[cell["remark"]][p]}"'
    if cell["kind"] == "number":
        return f'{seller}: "{NUMBER_REMARKS[cell["remark"]][p]}"'
    return f'{seller}: "{["Welcome.", "Good morning."][p]}"'


def options_text(p, pmax):
    opts = [f"{a} coin" + ("" if a == 1 else "s") for a in range(1, pmax + 1)] + ["walk away without buying"]
    if p == 1:
        opts = opts[::-1]
    return "\n".join(f"{LETTERS[i]}. {o}" for i, o in enumerate(opts)), opts


def question(p, buyer, seller, pmax):
    if VARIANT == "R0":
        return [f"What price will {buyer} propose? This proposal is final: {seller} will accept or reject it. "
                f"Answer with one digit: 1 to 9 for a price in coins, or 0 to walk away without buying.",
                f"Which price does {buyer} propose? It is her final proposal: {seller} will either accept or reject it. "
                f"Reply with a single digit: 1 to 9 means a price in coins, 0 means she walks away without buying."][p]
    if VARIANT in ("R1", "R4"):
        q = [f"What price will {buyer} propose? This proposal is final: {seller} will accept or reject it. "
             f"Answer with the price in coins, or with the word walk if she walks away without buying.",
             f"Which price does {buyer} propose? It is her final proposal: {seller} will either accept or reject it. "
             f"Reply with the price in coins, or with the word walk if she walks away without buying."][p]
        if VARIANT == "R4":
            q += [" Think it through in at most two short sentences first, then write Answer: followed by your answer.",
                  " First reason about it in no more than two short sentences, then write Answer: and your answer."][p]
        return q
    ot, _ = options_text(p, pmax)
    return [f"What will {buyer} do? This proposal is final: {seller} will accept or reject it. Options:\n{ot}\n"
            f"Answer with the letter of one option.",
            f"Which option does {buyer} choose? It is her final proposal: {seller} will either accept or reject it. Options:\n{ot}\n"
            f"Reply with a single letter."][p]


def build():
    s, items, cl = cells()
    prompts = []
    for ci, (buyer, seller, comp, opening) in enumerate(contexts()):
        for p in range(2):
            for cell in cl:
                sysm = RP.system_prompt(s, cell["v"], cell["hist"], buyer, seller, comp, opening, p)
                user = f"{body(cell, p, buyer, seller)}\n\n{question(p, buyer, seller, s.pmax)}"
                U = payoffs(s, cell["v"], cell["hist"], tuple(cell["item"]) if cell["item"] else None)
                m = max(U.values()); best = [a for a, u in U.items() if u == m]
                U0 = payoffs(s, cell["v"], cell["hist"], None); m0 = max(U0.values()); best0 = [a for a, u in U0.items() if u == m0]
                prompts.append(dict(cell, variant=VARIANT, ctx=ci, para=p, buyer=buyer, fresh=FRESH,
                                    U=[U[a] for a in range(1, s.pmax + 1)], best=best, walk_optimal=bool(m < 0),
                                    best0=best0, u0=(best0[0] - 1) / 8 if len(best0) == 1 else None,
                                    u_star=((best[0] - 1) / 8) if (len(best) == 1 and m >= 0) else None,
                                    messages=[{"role": "system", "content": sysm}, {"role": "user", "content": user}]))
    return prompts


def main():
    prompts = build()
    if "--show" in sys.argv:
        for p in prompts[:: max(1, len(prompts) // 4)][:4]:
            print(json.dumps({k: p[k] for k in ("kind", "v", "hist", "item", "remark", "ctx", "para", "best")}))
            print(p["messages"][1]["content"]); print("=" * 60)
        print(len(prompts), "prompts"); return
    dry = int(sys.argv[sys.argv.index("--dry") + 1]) if "--dry" in sys.argv else 0
    import torch
    from pilot.fastread import Reader
    rd = Reader(RP.MODEL); tok = rd.tok
    one = lambda w: (lambda x: (len(x) == 1 and x[0]) or None)(tok.encode(w, add_special_tokens=False))
    dig = [one(d) for d in "0123456789"]; assert all(x is not None for x in dig)
    if VARIANT == "R0":
        frame = lambda p: f"{p['buyer']} proposes "
    else:
        frame = lambda p: "Answer:"
    walk_ids = [i for i in (one(" walk"), one(" Walk")) if i is not None]
    space = one(" "); letters = [one(" " + c) for c in LETTERS]; assert space is not None and all(letters)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    done = sum(1 for _ in open(OUT)) if os.path.exists(OUT) else 0
    todo = prompts[done:done + dry] if dry else prompts[done:]
    import capability_check as CC
    print(f"{RP.MODEL} on {CC.DEVICE}: variant {VARIANT}{' fresh contexts' if FRESH else ''}, {len(prompts)} prompts, {done} done, "
          f"running {len(todo)}", flush=True)
    t0 = time.time(); n = 0
    with open(OUT, "a") as f:
        i = 0
        while i < len(todo):
            pre = rd.prefix_text(todo[i]["messages"])
            j = i
            while j < len(todo) and j - i < BATCH and rd.prefix_text(todo[j]["messages"]) == pre:
                j += 1
            group = todo[i:j]; i = j
            gen = [""] * len(group)
            if VARIANT == "R4":
                for g, p in enumerate(group):
                    ids = rd.ids(rd.chat(p["messages"]))
                    with torch.no_grad():
                        out = rd.model.generate(input_ids=ids, max_new_tokens=MAX_NEW, do_sample=False)
                    txt = tok.decode(out[0, ids.shape[1]:], skip_special_tokens=True)
                    gen[g] = txt.split("Answer")[0].rstrip() + "\n"
            texts = []
            for g, p in enumerate(group):
                base = rd.chat(p["messages"], gen[g] + frame(p))
                texts.append(base)
                if VARIANT in ("R1", "R4"):
                    texts.append(base + " ")
            res = rd.last_probs_batch(texts, pre) if VARIANT != "R4" else [rd.last_probs(t, None, use_cache=False) for t in texts]
            step = 2 if VARIANT in ("R1", "R4") else 1
            for g, p in enumerate(group):
                pr, ntok = res[g * step]
                top = torch.topk(pr, 10); top10 = [[tok.decode([k]), round(x, 5)] for x, k in zip(top.values.tolist(), top.indices.tolist())]
                if VARIANT == "R0":
                    q = pr[dig].cpu().numpy().astype(float)                         # [walk, 1..9]
                elif VARIANT == "R2":
                    lp = pr[letters].cpu().numpy().astype(float)
                    _, opts = options_text(p["para"], 9)
                    q = np.zeros(10)
                    for k, o in enumerate(opts):
                        q[0 if o.startswith("walk") else int(o.split()[0])] += lp[k]
                else:
                    pw = float(pr[walk_ids].sum()); ps = float(pr[space])
                    pd = res[g * step + 1][0][dig].cpu().numpy().astype(float)
                    q = np.concatenate([[pw], ps * pd[1:]])                          # digit 0 after "Answer: " is not an option
                cov = float(q.sum()); qn = q / cov
                offer = qn[1:] / max(qn[1:].sum(), 1e-12)
                eo = float((np.arange(1, 10) * offer).sum())
                rec = {k: v for k, v in p.items() if k not in ("messages", "buyer")}
                rec.update(probs=q.tolist(), coverage=cov, walk=float(qn[0]), exp_offer=eo, exp_u=(eo - 1) / 8,
                           sd_offer=float(np.sqrt((((np.arange(1, 10) - eo) ** 2) * offer).sum())), top10=top10, n_tokens=ntok,
                           reasoning=gen[g] or None)
                f.write(json.dumps(rec) + "\n")
            f.flush(); n += len(group)
            if n % 48 < len(group) or i >= len(todo):
                el = time.time() - t0
                print(f"  {done + n}/{len(prompts)}  {el / n:.2f} s/prompt  eta {(len(todo) - n) * el / n / 60:.0f} min", flush=True)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
