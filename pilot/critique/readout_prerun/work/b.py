import sys, itertools
sys.argv=['x','R0']; sys.path.insert(0,'.')
from pilot import readout as R
import numpy as np
pr=[p for p in R.build() if p['kind']=='base' and p['ctx']==0 and p['para']==0]
U=np.array([p['U'] for p in pr]); V=[p['v'] for p in pr]; H=[p['hist'] for p in pr]
best=[p['best'] for p in pr]; m=U.max(1)
def reg(pol):  # pol: list of dists over [walk,1..9]
    r=[]
    for i,q in enumerate(pol):
        q=np.asarray(q,float); r.append(m[i]-(q[1:]*U[i]).sum())
    return np.mean(r), np.round(r,2)
def det(f): 
    out=[]
    for v,h in zip(V,H):
        q=np.zeros(10); q[f(v,h)]=1; out.append(q)
    return out
half=lambda v,h: min(9,max(1,round(v/2)))
print('max payoffs',np.round(m,2), 'mean',m.mean())
print('always5',reg(det(lambda v,h:5)))
print('always4',reg(det(lambda v,h:4)))
print('half',reg(det(half)))
print('half cap7',reg(det(lambda v,h:min(7,half(v,h)))))
print('half cap8',reg(det(lambda v,h:min(8,half(v,h)))))
print('uniform offers',reg([np.r_[0,np.ones(9)/9]]*10))
print('uniform 10',reg([np.ones(10)/10]*10))
# best value-only deterministic policy
tot=0; pol={}
for v in sorted(set(V)):
    idx=[i for i in range(10) if V[i]==v]
    a=max(range(1,10), key=lambda a: sum(U[i][a-1] for i in idx)); pol[v]=a
print('best v-only',pol,reg(det(lambda v,h:pol[v])))
opt0={v:best[[i for i in range(10) if V[i]==v and not H[i]][0]][0] for v in set(V)}
print('nohist optimum everywhere',opt0,reg(det(lambda v,h:opt0[v])))
# noisy optimal: discretised normal around optimum with sd s, plus walk w
def noisy(s,w=0.0,center=None):
    out=[]
    for i in range(10):
        c=best[i][0] if center is None else center(V[i],H[i])
        a=np.arange(1,10); q=np.exp(-0.5*((a-c)/s)**2); q/=q.sum()
        out.append(np.r_[w,(1-w)*q])
    return out
for s in (0.5,1,1.5,2):
    pol_=noisy(s); sd=[np.sqrt(((np.arange(1,10)-(np.arange(1,10)*q[1:]).sum())**2*q[1:]).sum()) for q in pol_]
    print('optimal + normal sd',s,'regret',round(reg(pol_)[0],3),'median realised sd',round(np.median(sd),2),
          'mass on opt', round(np.mean([sum(q[b] for b in best[i]) for i,q in enumerate(pol_)]),3))
for w in (0.05,0.1,0.2): print('optimal with walk',w,round(reg(noisy(0.01,w))[0],3))
for s in (0.5,1,1.5): print('half-value center + sd',s, round(reg(noisy(s,center=half))[0],3))
for s in (0.5,1,1.5): print('half cap7 center + sd',s, round(reg(noisy(s,center=lambda v,h:min(7,half(v,h))))[0],3))
# A3 chance
print('chance mass on best (10 answers)', np.mean([len(b)/10 for b in best]), [len(b) for b in best])
# A5 for half-value on 8 single-optimum blocks
idx=[i for i in range(10) if len(best[i])==1]
u0=np.array([(best[i][0]-1)/8 for i in idx])
def a5(f):
    x=np.array([(f(V[i],H[i])-1)/8 for i in idx])
    def rank(z):
        z=np.asarray(z); r=np.empty(len(z)); o=np.argsort(z); 
        for val in set(z): r[z==val]=np.mean(np.flatnonzero(np.sort(z)==val))
        return r
    return np.corrcoef(rank(x),rank(u0))[0,1], np.polyfit(u0,x,1)[0]
print('A5 half',a5(half)); print('A5 half cap7',a5(lambda v,h:min(7,half(v,h)))); print('A5 nohist-opt',a5(lambda v,h:opt0[v]))
print('A5 compressed 4+ (opt-4)/2:', np.polyfit(u0, 0.5*u0+0.2,1)[0])
