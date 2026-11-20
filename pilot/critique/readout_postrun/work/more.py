import json, sys, numpy as np
sys.path.insert(0,'work'); sys.path.insert(0,'.')
from accept import load, acc
# 1. R1 under the v2 reading (no ' **' path): approximate from stored top10s
R=load("pilot/out/readout_R1.jsonl")
import copy
R2=[]
miss=0
for r in R:
    t1=dict(r['top10']); t2=dict(r['top10_after_space']); ps=r['p_space']
    q=np.zeros(10); q[0]=t1.get(' walk',0)+t1.get(' Walk',0)+ps*(t2.get('walk',0)+t2.get('Walk',0))
    for d in range(1,10):
        if str(d) not in t2: miss+=1
        q[d]=ps*t2.get(str(d),0)
    q[1]*=(1-r['p_two_digit_after_1'])
    s=dict(r); s['probs']=q.tolist(); s['coverage']=float(q.sum()); qn=q/q.sum(); off=qn[1:]/qn[1:].sum(); eo=float((np.arange(1,10)*off).sum())
    s['walk']=float(qn[0]); s['exp_offer']=eo; s['sd_offer']=float(np.sqrt((((np.arange(1,10)-eo)**2)*off).sum()))
    R2.append(s)
json.dump([0],open('work/_t.json','w'))
with open('work/R1_v2reading.jsonl','w') as f:
    for s in R2:
        f.write(json.dumps({k:v for k,v in s.items() if k not in('q','off','U_','T_','cov_','eo_','sd_','best','pay','reg')})+"\n")
o,_,_=acc(load('work/R1_v2reading.jsonl')); print("R1 with v2 reading (no bold path; digits missing from top10:",miss,")"); print('  '+'  '.join(f"{k}={np.round(v,3)}" for k,v in o.items()))
o,_,_=acc(R); print("R1 as run (v2.1)"); print('  '+'  '.join(f"{k}={np.round(v,3)}" for k,v in o.items()))
# first 16 prompts of R1 (the dry-run prompts): p_bold
print("p_bold in first 16 R1 prompts: min %.2f max %.2f"%(min(r['p_bold'] for r in R[:16]),max(r['p_bold'] for r in R[:16])))
# 2. R2 coverage
X=load("pilot/out/readout_R2.jsonl"); c=[r['coverage'] for r in X]; print("R2 coverage min %.3f share<0.9 %.3f"%(min(c),np.mean(np.array(c)<.9)))
# 3. walk>0.5 share by kind (attrition under spec 2.1)
for v in ["R0","R1","R2","R3"]:
    X=load(f"pilot/out/readout_{v}.jsonl")
    print(v,"share of prompts with offer mass < 0.5:",{k:round(float(np.mean([r['q'][0]>.5 for r in X if r['kind']==k])),2) for k in ("base","irrelevant","number","info")}, "| IR: mass on offers > v at v=2: %.2f, at v=6: %.2f (baseline; of total)"%(np.mean([r['q'][3:].sum() for r in X if r['kind']=='base' and r['v']==2]),np.mean([r['q'][7:].sum() for r in X if r['kind']=='base' and r['v']==6])))
# 4. R4 complete vs cut-off
X=load("pilot/out/readout_R4.jsonl")
for nm,f in (("complete",lambda r:not r['generation']['cut_off']),("cut off",lambda r:r['generation']['cut_off'])):
    S=[r for r in X if f(r)]
    print("R4",nm,len(S),"regret %.2f, target mass %.2f, argmax in target %.2f, loss mass at v=2,6: %.2f"%(np.mean([r['reg'] for r in S]),np.mean([sum(r['q'][a] for a in r['T_']) for r in S]),np.mean([int(np.argmax(r['q'])) in r['T_'] for r in S]), np.mean([r['q'][1:][np.arange(1,10)>r['v']].sum() for r in S if r['v']<9])))
h=[r for r in X if r['hist']]; print("R4 history prompts: argmax==2 in %d of %d; "%(sum(int(np.argmax(r['q']))==2 for r in h),len(h)), "no-history argmax==2:",sum(int(np.argmax(r['q']))==2 for r in X if not r['hist']))
# 5. cross-variant agreement of block-mean exp_offer
import itertools
V=["R0","R1","R2","R3","R4"]; M={}
for v in V:
    X=load(f"pilot/out/readout_{v}.jsonl"); B=[r for r in X if r['kind']=='base']
    M[v]=np.array([np.mean([r['eo_'] for r in B if (r['v'],r['hist'])==b]) for b in sorted({(r['v'],r['hist']) for r in B})])
for a,b in itertools.combinations(V,2): print(a,b,"corr of block-mean exp_offer %.2f"%np.corrcoef(M[a],M[b])[0,1])
