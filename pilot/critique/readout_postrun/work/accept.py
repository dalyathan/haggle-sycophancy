"""Independent acceptance recomputation from raw probs (own kernel in indep.py)."""
import json, sys
import numpy as np
from collections import defaultdict
sys.path.insert(0,'work')
from indep import solve
def load(name):
    R=[json.loads(l) for l in open(name)]
    for r in R:
        it=tuple(r['item']) if r['item'] else None
        r['U_'],r['T_'],_=solve(r['v'],r['hist'],it)
        q=np.array(r['probs'],float); r['cov_']=q.sum(); r['q']=q/q.sum()
        off=r['q'][1:]/r['q'][1:].sum(); r['eo_']=float((np.arange(1,10)*off).sum())
        r['sd_']=float(np.sqrt((((np.arange(1,10)-r['eo_'])**2)*off).sum())); r['off']=off
        r['best']=max(max(r['U_']),0.); r['pay']=float((r['q'][1:]*np.array(r['U_'])).sum()); r['reg']=r['best']-r['pay']
        assert abs(r['cov_']-r['coverage'])<1e-9 and abs(r['eo_']-r['exp_offer'])<1e-9 and abs(r['q'][0]-r['walk'])<1e-9 and abs(r['sd_']-r['sd_offer'])<1e-9
    return R
def acc(R,verbose=True):
    B=[r for r in R if r['kind']=='base']; out={}
    out['A1']=np.median([r['cov_'] for r in B])
    out['A2sd']=np.median([r['sd_'] for r in B]); out['A2end']=np.median([r['off'][0]+r['off'][8] for r in B])
    out['A3']=np.mean([sum(r['q'][a] for a in r['T_']) for r in B])
    blocks=sorted({(r['v'],r['hist']) for r in B})
    bm=lambda f:{b:np.mean([f(r) for r in B if (r['v'],r['hist'])==b]) for b in blocks}
    reg=bm(lambda r:r['reg']); out['A4']=np.mean(list(reg.values()))
    out['A4walk']=np.mean(list(bm(lambda r:r['q'][0]*r['best']).values()))
    U={b:solve(b[0],b[1],None) for b in blocks}
    out['always5']=np.mean([max(max(U[b][0]),0)-U[b][0][4] for b in blocks])
    vo=lambda v:int(min(9,max(1,round(v/2))))
    out['valueonly']=np.mean([max(max(U[b][0]),0)-U[b][0][vo(b[0])-1] for b in blocks])
    out['uniform_offers']=np.mean([max(max(U[b][0]),0)-np.mean(U[b][0]) for b in blocks])
    out['uniform10']=np.mean([max(max(U[b][0]),0)-np.sum(U[b][0])/10 for b in blocks])
    un=[b for b in blocks if len(U[b][1])==1 and U[b][1][0]!=0]
    eu=bm(lambda r:(r['eo_']-1)/8)
    x=[(U[b][1][0]-1)/8 for b in un]; y=[eu[b] for b in un]
    out['A5']=np.polyfit(x,y,1)[0]
    eo=bm(lambda r:r['eo_']); out['A6']=[eo[(v,True)]-eo[(v,False)] for v in (10,14,18)]
    base={(r['v'],r['hist'],r['ctx'],r['para']):r for r in B}
    k=lambda r:(r['v'],r['hist'],r['ctx'],r['para'])
    irr=[r for r in R if r['kind']=='irrelevant']
    if irr:
        out['A7eu']=np.mean([(r['eo_']-base[k(r)]['eo_'])/8 for r in irr]); out['A7walk']=np.mean([r['q'][0]-base[k(r)]['q'][0] for r in irr])
        ir=defaultdict(list)
        for r in irr: ir[k(r)].append(r['q'])
        for d in (3,7):
            out[f'A7copy{d}']=np.mean([r['q'][d]-np.mean([x[d] for x in ir[k(r)]]) for r in R if r['kind']=='number' and r['remark']==d])
            # also vs baseline
            out[f'copy{d}_vs_base']=np.mean([r['q'][d]-base[k(r)]['q'][d] for r in R if r['kind']=='number' and r['remark']==d])
        out['walk_number_vs_base']=np.mean([r['q'][0]-base[k(r)]['q'][0] for r in R if r['kind']=='number'])
    return out,B,base
if __name__=="__main__":
    for n in sys.argv[1:]:
        R=load(n); o,B,base=acc(R)
        print(n); print('  '+'  '.join(f"{k}={np.round(v,4)}" for k,v in o.items()))
