"""Independent recomputation: kernel targets, payoffs, acceptance A1-A7, fast-path gate. Does not import kernel.py."""
import json, sys
from fractions import Fraction as F
import numpy as np
from collections import defaultdict
PMAX=9; VALS=[2,6,10,14,18]; FLOOR=4
def states(hist):
    b={}
    for c in range(1,9): b[('r',c)]=F(7,10)/8
    b[('g',0)]=F(15,100); b[('f',0)]=F(15,100)
    if hist:
        b={k:p for k,p in b.items() if not acc(k,1)}
        z=sum(b.values()); b={k:p/z for k,p in b.items()}
    return b
def acc(k,a):
    t,c=k
    return a>=c if t=='r' else (True if t=='g' else a>=FLOOR)
def solve(v,hist,item):
    """returns U list (float), target set (0=walk), kind"""
    b=states(hist); vb=F(v)
    cred = item is not None and ((not item[2]) or item[0]=='quality_down' or (item[0]=='cost_reveal' and item[1]=='low'))
    if cred:
        if item[0]=='quality_down': vb=vb*(1-F(item[1]))
        else: b={('r',1 if item[1]=='low' else 8):F(1)}
    P={a:sum(p for k,p in b.items() if acc(k,a)) for a in range(1,10)}
    U={a:(vb-a)*P[a] for a in range(1,10)}
    m=max(U.values())
    if m<0: T={0}
    else:
        T={a for a in U if U[a]==m}
        if m==0:
            T.add(0)
    offers=[a for a in T if a!=0]
    if offers and all(P[a]==0 for a in offers): T={0}   # C8 no-trade -> walk
    return [float(U[a]) for a in range(1,10)], sorted(T), P
ITEMS=[('quality_down','1/2',True),('quality_down','1/2',False),('cost_reveal','low',True),('cost_reveal','low',False),('cost_reveal','high',True),('cost_reveal','high',False)]
if __name__=="__main__":
    print("baseline targets and payoffs")
    for v in VALS:
        for h in (False,True):
            U,T,P=solve(v,h,None)
            print(v,int(h),T,' '.join(f"{u:6.2f}" for u in U), "best",max(max(U),0))
    for name in sys.argv[1:]:
        R=[json.loads(l) for l in open(name)]
        bad=0; badU=0; n=0
        for r in R:
            it=tuple(r['item']) if r['item'] else None
            U,T,P=solve(r['v'],r['hist'],it)
            if 'target' in r:
                n+=1
                if sorted(r['target'])!=T: bad+=1; print("TARGET MISMATCH",r['v'],r['hist'],it,r['target'],T)
            if max(abs(a-b) for a,b in zip(U,r['U']))>1e-9: badU+=1
        print(name,len(R),"rows; stored targets checked",n,"mismatch",bad,"; U mismatch",badU)
