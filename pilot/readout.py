"""Readout pilot (pilot/READOUT.md): the same model (Qwen3.5-4B, base) and the same game, with different ways of asking for
and reading the answer. Only the final question, the answer frame and the reading change; the system message
(the game) is the one from run_pilot.py.

Variants
  R0  control: the stage-B pilot readout (one digit, 0 = walk away, read after "{buyer} proposes ").
  R1  no digits in the instruction; walking away is the word "walk"; read after "Answer:" in two steps
      (P(" walk") and P(" ") then the digit after "Answer: ").
  R2  multiple choice: ten lettered options (nine prices and walk away), ascending in paraphrase 0 and descending
      in paraphrase 1; read the letter after "Answer:".
  R3  the R0 instruction with the R1 frame and reading ("Answer:"): separates the frame from the instruction wording.
  R4  R1 with a short reasoning step: greedy generation of at most MAX_NEW tokens, then "\nAnswer:" and the R1 reading.
      Baseline cells only (generation is slow on CPU); diagnostic (READOUT.md).
Reading after "Answer:" (R1, R3, R4): walk = " walk" | " Walk" | (" " then "walk"); price d = " " then d, or d directly, or the
number word; the mass on "1" is multiplied by 1 - P(a digit follows "Answer: 1"), since "1" may start 10 to 18.
Cells: the 10 baseline blocks; every information item generated in each block (no pressure); the two irrelevant
remarks from the stage-B pilot; two irrelevant remarks that contain a number (3 or 7) for the number-copying check.
Each cell is run in 3 contexts x 2 paraphrases. CONTEXTS=fresh uses three new contexts (confirmation run).

Usage: python pilot/readout.py R0|R1|R2|R4 [--dry N] [--show]; OUT defaults to pilot/out/readout_<variant>[_fresh].jsonl
and resumes by line count. Device: CUDA, else MPS, else CPU."""
import hashlib, json, os, sys, time
from fractions import Fraction as Fr
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import kernel as K, stats_layer as S
from pilot import text as T
from pilot import run_pilot as RP

VARIANT = next((a for a in sys.argv[1:] if a in ("R0", "R1", "R2", "R3", "R4")), "R0")
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
              "Early in the day the market of Fruitville was still quiet, and the first traders were laying out their stalls."])
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


def target(s, v, hist, item):
    """Kernel target for a cell: (sorted target list with 0 = walk away, update kind, optimal move in offer steps or None)."""
    mu = K.key(K.prior(s.types, s.shape))
    if item is None:
        A0 = K.baseline(s.types, s.pmax, s.walk, mu, v, hist)
        b = K.belief(dict(mu), s.pmax, hist)
        if K.no_trade(b, A0, s.pmax):
            return [K.WALK] if s.walk else sorted(A0), "tied", None
        return sorted(A0), ("move" if len(A0) == 1 else "tied"), 0
    A0, A1, (kind, d) = K.cell(s.types, s.pmax, s.walk, mu, v, hist, tuple(item))
    return sorted(A1), kind, d


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
    if VARIANT in ("R0", "R3"):
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
                it = tuple(cell["item"]) if cell["item"] else None
                U = payoffs(s, cell["v"], cell["hist"], it)
                tgt, kind, d = target(s, cell["v"], cell["hist"], it)
                t0, k0, _ = target(s, cell["v"], cell["hist"], None)
                u0 = (t0[0] - 1) / 8 if (k0 == "move" and t0[0] != K.WALK) else None
                msgs = [{"role": "system", "content": sysm}, {"role": "user", "content": user}]
                prompts.append(dict(cell, variant=VARIANT, ctx=ci, para=p, buyer=buyer, fresh=FRESH,
                                    U=[U[a] for a in range(1, s.pmax + 1)], target=tgt, update=kind, target0=t0, u0=u0,
                                    du=(None if d is None or u0 is None else d / 8),
                                    hash=hashlib.sha1(json.dumps(msgs).encode()).hexdigest()[:12], messages=msgs))
    return prompts


def read_answer(rd, texts_res, k, p, ids):
    """Option distribution [walk, 1..9] for prompt k from its batch results. ids: token-id table."""
    if VARIANT == "R0":
        pr = texts_res[k][0]
        return pr[ids["dig"]].cpu().numpy().astype(float), {}
    if VARIANT == "R2":
        lp = texts_res[k][0][ids["letters"]].cpu().numpy().astype(float)
        _, opts = options_text(p["para"], 9)
        q = np.zeros(10)
        for j, o in enumerate(opts):
            q[0 if o.startswith("walk") else int(o.split()[0])] += lp[j]
        return q, {}
    p1, p2, p3 = (texts_res[k * 3 + j][0] for j in range(3))      # after "Answer:", "Answer: ", "Answer: 1"
    ps = float(p1[ids["space"]])
    walk = float(p1[ids["walk_sp"]].sum()) + ps * float(p2[ids["walk_ns"]].sum())
    two = float(p3[ids["dig"]].sum())                              # "1" followed by another digit: 10 to 19
    price = ps * p2[ids["dig"]].cpu().numpy().astype(float)[1:] + p1[ids["dig"]].cpu().numpy().astype(float)[1:]
    if ids["words"]:
        price += p1[ids["words"]].cpu().numpy().astype(float)
    price[0] *= (1 - two)
    top2 = torch.topk(p2, 10)
    extra = dict(p_space=ps, p_two_digit_after_1=two, p_direct_digit=float(p1[ids["dig"][1:]].sum()),
                 p_word=float(p1[ids["words"]].sum()) if ids["words"] else 0.0,
                 top10_after_space=[[rd.tok.decode([i]), round(x, 5)] for x, i in zip(top2.values.tolist(), top2.indices.tolist())])
    return np.concatenate([[walk], price]), extra


def main():
    prompts = build()
    if "--show" in sys.argv:
        for p in prompts[:: max(1, len(prompts) // 4)][:4]:
            print(json.dumps({k: p[k] for k in ("kind", "v", "hist", "item", "remark", "ctx", "para", "target", "update", "du")}))
            print(p["messages"][1]["content"]); print("=" * 60)
        print(len(prompts), "prompts"); return
    dry = int(sys.argv[sys.argv.index("--dry") + 1]) if "--dry" in sys.argv else 0
    out_path = OUT + ".dry" if dry else OUT
    import torch
    globals()["torch"] = torch
    from pilot.fastread import Reader
    import capability_check as CC
    rd = Reader(RP.MODEL); tok = rd.tok
    enc = lambda w: tok.encode(w, add_special_tokens=False)
    one = lambda w: (lambda x: x[0] if len(x) == 1 else None)(enc(w))
    ids = dict(dig=[one(d) for d in "0123456789"], space=one(" "), letters=[one(" " + c) for c in LETTERS],
               walk_sp=[i for i in (one(" walk"), one(" Walk")) if i is not None],
               walk_ns=[i for i in (one("walk"), one("Walk")) if i is not None])
    words = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    wid = [one(" " + w) for w in words]
    ids["words"] = wid if all(x is not None for x in wid) else []
    assert all(x is not None for x in ids["dig"]) and ids["space"] is not None and all(x is not None for x in ids["letters"])
    assert ids["walk_sp"] and ids["walk_ns"], "walk is not a single token"
    assert enc("Answer: 5") == enc("Answer:") + [ids["space"], ids["dig"][5]], enc("Answer: 5")
    assert enc("Answer: walk") == enc("Answer:") + [one(" walk")], enc("Answer: walk")
    print("number words read:", bool(ids["words"]), flush=True)
    frame = (lambda p: f"{p['buyer']} proposes ") if VARIANT == "R0" else (lambda p: "Answer:")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    done_rows = []
    if os.path.exists(out_path):
        for l in open(out_path):
            try:
                done_rows.append(json.loads(l))
            except json.JSONDecodeError:
                break                                                 # a partial last line from a crash: rewritten below
        with open(out_path, "w") as f:
            for r in done_rows:
                f.write(json.dumps(r) + "\n")
    done = len(done_rows)
    for r, p in zip(done_rows, prompts):
        assert r.get("hash", p["hash"]) == p["hash"], "stored rows were built from different prompts; use a new OUT"
    todo = prompts[done:done + dry] if dry else prompts[done:]
    print(f"{RP.MODEL} on {CC.DEVICE}: variant {VARIANT}{' fresh contexts' if FRESH else ''}, {len(prompts)} prompts, {done} done, "
          f"running {len(todo)} -> {out_path}", flush=True)
    t0 = time.time(); n = 0; checked = False
    with open(out_path, "a") as f:
        i = 0
        while i < len(todo):
            pre = rd.prefix_text(todo[i]["messages"])
            j = i
            while j < len(todo) and j - i < BATCH and rd.prefix_text(todo[j]["messages"]) == pre:
                j += 1
            group = todo[i:j]; i = j
            gen = [None] * len(group)
            if VARIANT == "R4":
                for g, p in enumerate(group):
                    x = rd.ids(rd.chat(p["messages"]))
                    with torch.no_grad():
                        o = rd.model.generate(input_ids=x, max_new_tokens=MAX_NEW, do_sample=False, repetition_penalty=1.0,
                                              temperature=None, top_p=None, top_k=None)
                    raw = tok.decode(o[0, x.shape[1]:], skip_special_tokens=True)
                    cut = o.shape[1] - x.shape[1] >= MAX_NEW
                    head = raw.split("Answer")[0].rstrip().rstrip("*").rstrip()
                    gen[g] = dict(raw=raw, has_answer="Answer" in raw, cut_off=bool(cut), used=head + "\n")
            texts = []
            for g, p in enumerate(group):
                base = rd.chat(p["messages"], (gen[g]["used"] if gen[g] else "") + frame(p))
                texts += [base] if VARIANT in ("R0", "R2") else [base, base + " ", base + " 1"]
            if VARIANT == "R4":
                res = [rd.last_probs(t, None, use_cache=False) for t in texts]
            else:
                res = rd.last_probs_batch(texts, pre)
                if not checked:                                       # self-check: batched cache path vs full passes
                    full = [rd.last_probs(t, None, use_cache=False) for t in texts]
                    opt = ids["dig"] + ids["letters"] + [ids["space"]] + ids["walk_sp"]
                    dmax = max(float((a[0][opt] - b[0][opt]).abs().max()) for a, b in zip(res, full))
                    print(f"self-check on {len(texts)} texts: max abs option-probability difference, batched cache vs full pass: {dmax:.4f}", flush=True)
                    if dmax > 0.03:
                        sys.exit("self-check failed: fast path disagrees with full forward passes")
                    checked = True
            step = 1 if VARIANT in ("R0", "R2") else 3
            for g, p in enumerate(group):
                pr, ntok = res[g * step]
                q, extra = read_answer(rd, res, g, p, ids)
                top = torch.topk(pr, 10); top10 = [[tok.decode([k]), round(x, 5)] for x, k in zip(top.values.tolist(), top.indices.tolist())]
                cov = float(q.sum()); qn = q / cov
                offer = qn[1:] / max(qn[1:].sum(), 1e-12)
                eo = float((np.arange(1, 10) * offer).sum())
                rec = {k: v for k, v in p.items() if k not in ("messages", "buyer")}
                rec.update(probs=q.tolist(), coverage=cov, walk=float(qn[0]), exp_offer=eo, exp_u=(eo - 1) / 8,
                           sd_offer=float(np.sqrt((((np.arange(1, 10) - eo) ** 2) * offer).sum())), top10=top10, n_tokens=ntok,
                           generation=gen[g], **extra)
                f.write(json.dumps(rec) + "\n")
            f.flush(); n += len(group)
            if (n // 48) != ((n - len(group)) // 48) or i >= len(todo):
                el = time.time() - t0
                print(f"  {done + n}/{len(prompts)}  {el / n:.2f} s/prompt  eta {(len(todo) - n) * el / n / 60:.0f} min", flush=True)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
