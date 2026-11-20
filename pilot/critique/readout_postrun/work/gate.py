import json, sys, os, numpy as np
sys.path.insert(0,'.')
from pilot import readout as RO, run_pilot as RP
RO.VARIANT, RO.FRESH = "R0", False
new=RO.build(); old=RP.build()
R=[json.loads(l) for l in open("pilot/out/readout_R0.jsonl")]; st=[json.loads(l) for l in open("pilot/out/pilot_4b.jsonl")]
print(len(new),len(old),len(R),len(st))
# alignment of stored rows with builds
print("R0 rows align with build:",all(all(r.get(k)==p.get(k) for k in("kind","block","ctx","para","item","remark","v","hist")) for r,p in zip(R,new)))
print("stageB rows align with build:",all(r['cell']==p['cell'] and r['ctx']==p['ctx'] and r['para']==p['para'] and r['v']==p['v'] and r['hist']==p['hist'] for r,p in zip(st,old)))
key=lambda p:(p["messages"][0]["content"],p["messages"][1]["content"])
oi={}
for i,p in enumerate(old):
    assert key(p) not in oi or True
    oi.setdefault(key(p),[]).append(i)
print("duplicate stage-B texts:",sum(len(v)>1 for v in oi.values()))
dp=[];de=[];kinds={};dw=[];ntok=[]
for i,p in enumerate(new):
    j=oi.get(key(p))
    if j:
        j=j[0]
        a=np.array(R[i]['probs']);b=np.array(st[j]['probs'])
        dp.append(np.abs(a-b).max()); de.append(R[i]['exp_u']-st[j]['exp_u']); dw.append(R[i]['walk']-st[j]['walk'])
        kinds[p['kind']]=kinds.get(p['kind'],0)+1; ntok.append(R[i]['n_tokens']-st[j]['n_tokens'])
dp=np.array(dp);de=np.array(de)
print("shared",len(dp),kinds,"n_tokens equal:",set(ntok))
print("max abs prob diff %.4f (99th pct %.4f, median %.4f); exp_u diff mean %+.5f SD %.4f max %.4f; walk diff SD %.4f max %.4f"%(dp.max(),np.percentile(dp,99),np.median(dp),de.mean(),de.std(),np.abs(de).max(),np.std(dw),np.abs(dw).max()))
print("share of prompts with max prob diff > 0.01: %.3f"%np.mean(dp>0.01))
# unmatched R0 prompts
un=[p for p in new if key(p) not in oi]
import collections
print("unmatched:",collections.Counter((p['kind'],p['v'],p['hist']) for p in un).most_common(30))
# is there position-in-batch structure? first of each batch group vs rest
