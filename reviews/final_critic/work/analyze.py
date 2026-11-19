import json, sys, numpy as np
sys.path.insert(0, "repo")
res = json.load(open("work/rerun.json"))
def auc(good, bad):
    g = np.sort(good); bad=np.asarray(bad)
    l = np.searchsorted(g, bad, side="left"); r = np.searchsorted(g, bad, side="right")
    return float(np.mean(l + 0.5*(r-l))/len(g))
names = list(next(iter(next(iter(res.values()))["scores"].values()))[0].keys())
print("designs:", [(r["N"], r["P"], r["C"], r["ncell"]) for r in res.values()])
def vals(sc, pref, m): return [d[m] for k, v in sc.items() if k.startswith(pref) for d in v]
# 1. reproduce training table; add held-out over all 10 designs; split by panel
print("\nmetric: train AUC, train TPR | heldout AUC, TPR (mean of 10 designs) | own11 TPR, panel1 TPR, a-panels TPR")
rows = {}
for m in names:
    a=[];t=[];ha=[];ht=[];own=[];p1=[];aa=[]
    for r in res.values():
        sc=r["scores"]; g=vals(sc,"good|",m); q=np.quantile(g,0.99)
        b=vals(sc,"bad|",m); te=vals(sc,"test|",m)
        a.append(auc(g,b)); t.append(np.mean(np.array(b)>q)); ha.append(auc(g,te)); ht.append(np.mean(np.array(te)>q))
        own.append(np.mean(np.array(vals(sc,"bad|own:",m))>q)); p1.append(np.mean(np.array(vals(sc,"bad|panel1:",m))>q))
        aa.append(np.mean(np.array([d[m] for k,v in sc.items() if k.startswith("bad|a") for d in v])>q))
    rows[m]=(np.mean(a),np.mean(t),np.mean(ha),np.mean(ht),np.mean(own),np.mean(p1),np.mean(aa))
    print(f"  {m:16s} {rows[m][0]:.3f} {rows[m][1]:.3f} | {rows[m][2]:.3f} {rows[m][3]:.3f} | {rows[m][4]:.2f} {rows[m][5]:.2f} {rows[m][6]:.2f}")
# training AUC excluding the 11 own buyers
print("\ntrain AUC / TPR on attacker-written buyers only (36):")
for m in names:
    a=[];t=[]
    for r in res.values():
        sc=r["scores"]; g=vals(sc,"good|",m); q=np.quantile(g,0.99)
        b=[d[m] for k,v in sc.items() if k.startswith("bad|") and not k.startswith("bad|own:") for d in v]
        a.append(auc(g,b)); t.append(np.mean(np.array(b)>q))
    print(f"  {m:16s} {np.mean(a):.3f} {np.mean(t):.3f}")
# chosen design N=138240
ch=[k for k,r in res.items() if r["N"]==138240]
print("\ndesigns with N=138240:", len(ch))
for k in ch:
    sc=res[k]["scores"]
    print(" held-out on this design: metric AUC TPR")
    for m in names:
        g=vals(sc,"good|",m); q=np.quantile(g,0.99); te=vals(sc,"test|",m)
        print(f"   {m:16s} {auc(g,te):.3f} {np.mean(np.array(te)>q):.3f}   train TPR {np.mean(np.array(vals(sc,'bad|',m))>q):.3f}")
# good-set noise scale of key stats
print("\nSD over good draws (pi_star), per design: raw_r, lamS, M2 mean, M2 q99, total_error mean")
for r in res.values():
    v=r["scores"]["good|pi_star"]
    print(f"  N={r['N']}: sd raw_r {np.std([d['raw_r'] for d in v]):.4f}, sd lamS {np.std([d['lamS'] for d in v]):.4f}, M2 mean {np.mean([d['M2_onesided'] for d in v]):.4f} sd {np.std([d['M2_onesided'] for d in v]):.4f}, TE mean {np.mean([d['total_error'] for d in v]):.4f} sd {np.std([d['total_error'] for d in v]):.4f}")
# extras: false-alarm / detection rate at the good set's q99
print("\nextra buyers: share of draws above the good set's 99th percentile, mean over 10 designs")
exn=list(next(iter(res.values()))["extra"].keys()); ms=["combo_TE_M2","total_error","M2_onesided","M3_erratic","raw_r","lamS","abs_lamS","update_dev"]
print("  "+" "*24+" ".join(f"{m[:11]:>11s}" for m in ms))
for e in exn:
    out=[]
    for m in ms:
        x=[]
        for r in res.values():
            q=np.quantile(vals(r["scores"],"good|",m),0.99); x.append(np.mean(np.array([d[m] for d in r["extra"][e]])>q))
        out.append(np.mean(x))
    print(f"  {e:24s}"+" ".join(f"{o:11.2f}" for o in out))
# oracle
print("\noracle matched filter (TPR at 1% FA), vs combo_TE_M2, per buyer, mean over designs [min,max]")
keys=list(next(iter(res.values()))["oracle"].keys())
tot={"test":[], "bad":[]}
for k in keys:
    pl=[r["oracle"][k]["plain"] for r in res.values()]; ce=[r["oracle"][k]["centred"] for r in res.values()]
    cb=[]
    for r in res.values():
        q=np.quantile(vals(r["scores"],"good|","combo_TE_M2"),0.99); cb.append(np.mean(np.array([d["combo_TE_M2"] for d in r["scores"][k]])>q))
    L1=np.mean([r["oracle"][k]["L1dev"] for r in res.values()])
    tot[k.split("|")[0]].append((np.mean(pl),np.mean(ce),np.mean(cb)))
    if k.startswith("test|") or np.mean(cb)<0.3:
        print(f"  {k:42s} combo {np.mean(cb):.2f} | oracle plain {np.mean(pl):.2f} [{min(pl):.2f},{max(pl):.2f}] centred {np.mean(ce):.2f} [{min(ce):.2f},{max(ce):.2f}] | mean|dev| {L1:.4f}")
for g,v in tot.items():
    v=np.array(v); print(g, "n",len(v),"mean oracle plain %.3f centred %.3f combo %.3f; buyers with oracle(centred)<0.5: %d; <0.9: %d"%(v[:,0].mean(),v[:,1].mean(),v[:,2].mean(),(v[:,1]<0.5).sum(),(v[:,1]<0.9).sum()))
