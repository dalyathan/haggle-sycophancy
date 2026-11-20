import sys, numpy as np
sys.path.insert(0,'.')
from pilot import readout as RO, analyze_readout as A
RO.VARIANT, RO.FRESH = "R1", False
P=RO.build()
def rows(policy):
    out=[]
    for p in P:
        q=np.asarray(policy(p),float); q=q/q.sum(); off=q[1:]/max(q[1:].sum(),1e-12); eo=float((np.arange(1,10)*off).sum())
        r={k:v for k,v in p.items() if k!='messages'}; r.update(probs=q.tolist(),coverage=1.0,walk=float(q[0]),exp_offer=eo,exp_u=(eo-1)/8,sd_offer=float(np.sqrt((((np.arange(1,10)-eo)**2)*off).sum())))
        out.append(r)
    return out
def pm(a): q=np.zeros(10); q[a]=1; return q
def blur(a,sd):
    q=np.zeros(10); q[1:]=np.exp(-0.5*((np.arange(1,10)-a)/sd)**2); return q
opt=lambda p: pm(min(t for t in p['target'] if t>0) if any(t>0 for t in p['target']) else 0)
optmass=lambda p: sum(pm(t) for t in p['target'])
vo=lambda p: pm(A.value_only(p['v']))
def nohist(p):
    from fractions import Fraction
    t,_,_=RO.target(RO.S.unpack(RO.RP.DESIGN)[0],p['v'],False,None); return pm(min(x for x in t if x>0))
pols={"optimal(lowest)":opt,"optimal(spread on ties)":optmass,"value-only":vo,"value-only blur 1":lambda p:blur(A.value_only(p['v']),1.0),"no-history optimum":nohist,"uniform":lambda p:np.ones(10),
      "stageB-like":lambda p:np.array([.25,.21,.06,.03,.04,.05,.04,.03,.08,.21]),"optimal blur 1.0":lambda p: blur(min(t for t in p['target'] if t>0),1.0) if any(t>0 for t in p['target']) else pm(0),
      "optimal blur 0.5":lambda p: blur(min(t for t in p['target'] if t>0),0.5) if any(t>0 for t in p['target']) else pm(0),
      "optimal + 10% walk":lambda p: 0.9*opt(p)+0.1*pm(0)}
for n,f in pols.items():
    res,_=A.acceptance(rows(f)); print(f"{n:26s}", ' '.join(f"{k}:{'P' if v[1] else 'F'}" for k,v in res.items()), "|", res['A4'][0][:28], "|", res['A6'][0][36:60])
