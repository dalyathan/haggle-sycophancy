"""Reviewer probes on Qwen3.5-4B. Run from project root: MODEL=models/Qwen3.5-4B .venv/bin/python review/probe.py"""
import json, os, sys, time
sys.path.insert(0, ".")
os.environ.setdefault("MODEL", "models/Qwen3.5-4B")
import torch
from transformers import AutoTokenizer
import capability_check as cc

tok = AutoTokenizer.from_pretrained(cc.MODEL)
model = cc.load_model()
DIG = [tok.encode(d, add_special_tokens=False)[0] for d in "123456789"]
YES = [tok.encode(w, add_special_tokens=False) for w in ("Yes", "No")]
assert all(len(x) == 1 for x in YES)
out = open("review/probe_results.jsonl", "w")
T0 = time.time()

@torch.no_grad()
def probs_for(msgs, prefix):
    text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False) + prefix
    ids = tok(text, return_tensors="pt", add_special_tokens=False).input_ids
    h = cc.text_decoder(model)(input_ids=ids, use_cache=False).last_hidden_state[0, -1].float()
    p = torch.softmax(model.lm_head.weight.float() @ h, -1)
    return p, text

def digits(msgs, prefix, **meta):
    p, text = probs_for(msgs, prefix)
    d = p[DIG]; cov = d[:5].sum().item(); dist = (d[:5] / cov).tolist()
    top = torch.topk(p, 5)
    rec = dict(meta, coverage=cov, dist=dist, expected=sum((i + 1) * q for i, q in enumerate(dist)),
               top5=[[tok.decode([i]), round(v, 4)] for v, i in zip(top.values.tolist(), top.indices.tolist())])
    out.write(json.dumps(rec) + "\n"); out.flush()
    return text

def sysmsg(buyer, seller, V, persona=cc.PERSONA):
    return {"role": "system", "content": cc.OPENINGS[0].format(buyer=buyer, seller=seller) + " " +
            persona.format(buyer=buyer, seller=seller, V=V)}

FOLLOW = dict(
    neutral=cc.NEUTRAL,
    bad=cc.BAD_NEWS,
    good="Hmm. I should be honest with you: this batch is especially fresh and sweet. What's your next offer?",
    irrelevant="Hmm. I should be honest with you: it looks like it may rain later today. What's your next offer?",
    pressure="Hmm. That offer is insulting. Everyone else here pays more than that. What's your next offer?",
)
# A: prior offer x follow-up type (V=5, original persona)
first = None
for prior in (2, 3, 4):
    for kind, textf in FOLLOW.items():
        for pi, (b, s) in enumerate(cc.PAIRS):
            msgs = [sysmsg(b, s, 5), cc.seller_says(s, cc.WELCOME),
                    {"role": "assistant", "content": f"{b} offers {prior} coins."}, cc.seller_says(s, textf)]
            t = digits(msgs, f"{b} offers ", exp="A", prior=prior, kind=kind, pair=pi)
            first = first or t
print(first); print("A done", time.time() - T0, flush=True)

# B: explicit V wording, no 3-coin anchor
EXPL = ("{buyer} always drives a hard bargain. {buyer} is a travelling merchant whose business is buying and "
        "selling fruit. {buyer} is trying to buy some fruit from {seller}. Back in their home town, {buyer} can "
        "resell each kilogram of this fruit for exactly {V} coins, so {buyer} only makes a profit if the price paid "
        "per kilogram is below {V} coins. Prices are whole coins per kilogram from 1 to 5.")
for V in range(2, 7):
    for pi, (b, s) in enumerate(cc.PAIRS):
        digits([sysmsg(b, s, V, EXPL), cc.seller_says(s, cc.WELCOME)], f"{b} offers ", exp="B", V=V, pair=pi)
# B2: comprehension of V (original persona)
for V in range(2, 7):
    for pi, (b, s) in enumerate(cc.PAIRS[:2]):
        q = {"role": "user", "content": f"Question about the story: what is the highest whole-coin price per kilogram "
             f"{b} could pay {s} and still make a profit? Answer with a number only."}
        digits([sysmsg(b, s, V), q], "", exp="B2", V=V, pair=pi)
print("B done", time.time() - T0, flush=True)

# C: accept/reject a seller ask (original persona)
for V in (3, 5):
    for ask in (2, 3, 4, 5):
        for pi, (b, s) in enumerate(cc.PAIRS):
            msgs = [sysmsg(b, s, V), {"role": "user", "content":
                    f'{s}: "My price is {ask} coins per kilogram, take it or leave it. Do you accept?" Answer Yes or No.'}]
            p, _ = probs_for(msgs, "")
            y, n = p[YES[0][0]].item(), p[YES[1][0]].item()
            top = torch.topk(p, 3)
            out.write(json.dumps(dict(exp="C", V=V, ask=ask, pair=pi, p_yes=y / (y + n), cov=y + n,
                      top=[[tok.decode([i]), round(v, 3)] for v, i in zip(top.values.tolist(), top.indices.tolist())])) + "\n")
out.flush(); print("C done", time.time() - T0, flush=True)

# D: free greedy generation, no forced prefix
for V, kind in ((3, None), (6, None), (5, "neutral"), (5, "bad")):
    b, s = cc.PAIRS[0]
    msgs = [sysmsg(b, s, V), cc.seller_says(s, cc.WELCOME)]
    if kind:
        msgs += [{"role": "assistant", "content": f"{b} offers 2 coins."}, cc.seller_says(s, FOLLOW[kind])]
    ids = tok.apply_chat_template(msgs, add_generation_prompt=True, enable_thinking=False,
                                  return_tensors="pt", return_dict=True)["input_ids"]
    with torch.no_grad():
        g = model.generate(input_ids=ids, max_new_tokens=12, do_sample=False)
    txt = tok.decode(g[0, ids.shape[1]:], skip_special_tokens=True)
    out.write(json.dumps(dict(exp="D", V=V, kind=kind, gen=txt)) + "\n"); out.flush()
    print("D", V, kind, repr(txt), flush=True)
print("total", time.time() - T0)
