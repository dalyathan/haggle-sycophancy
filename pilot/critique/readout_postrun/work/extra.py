import json, sys, numpy as np
from collections import defaultdict
sys.path.insert(0,'work')
from accept import load, acc
from indep import solve
rng=np.random.default_rng(0)
V=["R0","R1","R2","R3","R4"]
D={v:load(f"pilot/out/readout_{v}.jsonl") for v in V}
print("### per-variant extras (baseline prompts)")
for v in V:
    R=D[v]; B=[r for r in R if r['kind']=='base']
    # regret decomposition: walk part, loss part (offers above value accepted => negative U), low part
    blocks=sorted({(r['v'],r['hist']) for r in B})
    def parts(r):
        U=np.array(r['U_']); q=r['q']; a=np.arange(1,10)
        walk=q[0]*r['best']; over=(q[1:]*(r['best']-U))[a>min(r['T_'][-1],9)].sum() if r['T_'][-1]>0 else (q[1:]*(r['best']-U)).sum()
        under=(q[1:]*(r['best']-U))[a<(min(t for t in r['T_'] if t>0) if any(t>0 for t in r['T_']) else 0)].sum()
        return walk,under,over
    P=np.mean([np.mean([parts(r) for r in B if (r['v'],r['hist'])==b],0) for b in blocks],0)
    loss=np.mean([r['q'][1:][np.arange(1,10)>r['v']].sum() for r in B if r['v']<9])   # possible-loss mass at v=2,6
    am=np.mean([int(np.argmax(r['q'])) in r['T_'] for r in B])
    within=np.mean([sum(r['q'][a] for a in range(1,10) if r['best']-r['U_'][a-1]<=0.3)+(r['q'][0] if r['best']<=0.3 else 0) for r in B])
    chance_within=np.mean([ (sum(1 for a in range(1,10) if r['best']-r['U_'][a-1]<=0.3)+(1 if r['best']<=0.3 else 0))/10 for r in B])
    # bootstrap over blocks for regret; and per ctx/para regret range
    regb=np.array([np.mean([r['reg'] for r in B if (r['v'],r['hist'])==b]) for b in blocks])
    bs=[regb[rng.integers(0,10,10)].mean() for _ in range(4000)]
    cp=[np.mean([np.mean([r['reg'] for r in B if (r['v'],r['hist'])==b and r['ctx']==c and r['para']==p]) for b in blocks]) for c in range(3) for p in range(2)]
    print(f"{v}: regret {regb.mean():.2f} [block bootstrap {np.percentile(bs,2.5):.2f},{np.percentile(bs,97.5):.2f}], per ctx x para min {min(cp):.2f} max {max(cp):.2f}; parts walk {P[0]:.2f} under {P[1]:.2f} over {P[2]:.2f}; loss mass (v=2,6) {loss:.2f}; argmax in target {am:.2f}; mass within 0.3 coins of best {within:.2f} (chance {chance_within:.2f})")
    # per (ctx,para) A5 slope & A6
    sl=[];h=[]
    for c in range(3):
        for p in range(2):
            S=[r for r in B if r['ctx']==c and r['para']==p]
            x=[(r['T_'][0]-1)/8 for r in S if len(r['T_'])==1]; y=[(r['eo_']-1)/8 for r in S if len(r['T_'])==1]
            sl.append(np.polyfit(x,y,1)[0])
            e={(r['v'],r['hist']):r['eo_'] for r in S}; h.append(np.mean([e[(k,True)]-e[(k,False)] for k in (10,14,18)]))
    print(f"    A5 slope per ctx x para: {np.round(sl,2)}  mean history effect per ctx x para: {np.round(h,2)}")
    # value regression: eo ~ a + b v + c hist
    X=np.array([[1,r['v'],r['hist']] for r in B],float); y=np.array([r['eo_'] for r in B])
    co=np.linalg.lstsq(X,y,rcond=None)[0]; print(f"    exp_offer = {co[0]:.2f} + {co[1]:.3f} v + {co[2]:.2f} hist ; optimal: ", end='')
    yo=np.array([np.mean([t for t in r['T_'] if t>0]) for r in B]); co=np.linalg.lstsq(X,yo,rcond=None)[0]; print(f"{co[0]:.2f} + {co[1]:.3f} v + {co[2]:.2f} hist")
    # echo of value digit
    for vv,d in ((2,2),(6,6)):
        print(f"    P({d}) at v={vv}: {np.mean([r['q'][d] for r in B if r['v']==vv]):.3f} vs elsewhere {np.mean([r['q'][d] for r in B if r['v']!=vv]):.3f}",end=';')
    print()
    pd=np.mean([r['eo_'] for r in B if r['para']==1])-np.mean([r['eo_'] for r in B if r['para']==0]); pw=np.mean([r['q'][0] for r in B if r['para']==1])-np.mean([r['q'][0] for r in B if r['para']==0])
    print(f"    paraphrase 1-0: exp_offer {pd:+.2f} coins, walk {pw:+.3f}")
print("### R2 position analysis")
R=D["R2"]
for p in (0,1):
    q=np.mean([r['q'] for r in R if r['para']==p],0)   # [walk,1..9]
    letters=( list(q[1:])+[q[0]] ) if p==0 else ( [q[0]]+list(q[1:][::-1]) )
    print(f" para {p}: by letter A..J:",' '.join(f"{x:.2f}" for x in letters), "| by option walk,1..9:",' '.join(f"{x:.2f}" for x in q))
print("### walk under remarks by variant: baseline, irrelevant0, irrelevant1, number3, number7, info types")
for v in V[:4]:
    R=D[v]
    g=lambda f:np.mean([r['q'][0] for r in R if f(r)])
    print(v, "base %.2f irr0 %.2f irr1 %.2f n3 %.2f n7 %.2f | qd_seller %.2f qd_insp %.2f"%(g(lambda r:r['kind']=='base'),g(lambda r:r['kind']=='irrelevant' and r['remark']==0),g(lambda r:r['kind']=='irrelevant' and r['remark']==1),g(lambda r:r['kind']=='number' and r['remark']==3),g(lambda r:r['kind']=='number' and r['remark']==7),g(lambda r:r['kind']=='info' and r['item'][0]=='quality_down' and r['item'][2]),g(lambda r:r['kind']=='info' and r['item'][0]=='quality_down' and not r['item'][2])))
print("### cost reveal copying: P(8) under 'cost 8' (seller vs inspector), P(1) under 'cost 1'; baseline")
for v in V[:4]:
    R=D[v]; base={(r['v'],r['hist'],r['ctx'],r['para']):r for r in R if r['kind']=='base'}; k=lambda r:(r['v'],r['hist'],r['ctx'],r['para'])
    def sh(item,d): 
        xs=[r['q'][d]-base[k(r)]['q'][d] for r in R if r['kind']=='info' and tuple(r['item'])==item]; return np.mean(xs)
    print(v,"dP(8): seller %.2f insp %.2f ; dP(1): seller %.2f insp %.2f"%(sh(('cost_reveal','high',True),8),sh(('cost_reveal','high',False),8),sh(('cost_reveal','low',True),1),sh(('cost_reveal','low',False),1)))
    # walk agreement in walk-target cells (inspector high cost at v=2,6)
    wt=[r['q'][0] for r in R if r['kind']=='info' and r['T_']==[0]]; print("    walk mass where walk is the only target: %.2f (n=%d); P(8) there %.2f"%(np.mean(wt),len(wt),np.mean([r['q'][8] for r in R if r['kind']=='info' and r['T_']==[0]])))
    # quality down: expected offer shift at each v, optimal
    for src in (True,False):
        out=[]
        for vv in (2,6,10,14,18):
            xs=[(r['eo_']-base[k(r)]['eo_']) for r in R if r['kind']=='info' and r['item'][0]=='quality_down' and r['item'][2]==src and r['v']==vv]
            out.append(np.mean(xs))
        print("    quality cut (%s) shift in coins by v:"%('seller' if src else 'insp'),np.round(out,2))
