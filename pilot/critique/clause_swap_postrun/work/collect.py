"""Collect the 160 texts of the CS 2x2 (both framings) into one list with cell labels.
Writes items.json (key) and, for blind-ish reading, dump_<rung>.txt in a shuffled order
with opaque ids (the clause is visible in the text; W is partly hidden)."""
import json, random, os
OUT = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'out')
HERE = os.path.dirname(os.path.abspath(__file__))

def rows(f):
    return [json.loads(l) for l in open(os.path.join(OUT, f))]

items = []
for r in rows('reason_ladder.jsonl'):
    items.append(dict(r, frame='third', W=0, C=0, src='RL'))
for r in rows('reason_ladder2.jsonl'):
    items.append(dict(r, W=r['para'], C=r['para'], src='RL2'))
for r in rows('clause_swap.jsonl'):
    items.append(dict(r, W=r['wording'], C=r['clause'], src='CS'))

keep = ['src', 'frame', 'W', 'C', 'rung', 'v', 'c', 'target', 'written_answer', 'n_new', 'cut_off', 'raw']
items = [{k: it.get(k) for k in keep} for it in items]
from collections import Counter
print(Counter((i['frame'], i['W'], i['C'], i['rung']) for i in items))
random.seed(20261120)
random.shuffle(items)
for n, it in enumerate(items):
    it['id'] = 'T%03d' % n
json.dump(items, open(os.path.join(HERE, 'items.json'), 'w'), indent=1)
for rung in ('L1', 'L2'):
    with open(os.path.join(HERE, 'dump_%s.txt' % rung), 'w') as f:
        for it in items:
            if not it['rung'].startswith(rung):
                continue
            f.write('=' * 30 + ' %s  v=%s c=%s  n_new=%s cut=%s written=%s\n' % (
                it['id'], it['v'], it['c'], it['n_new'], it['cut_off'], it['written_answer']))
            f.write(it['raw'].rstrip() + '\n')
