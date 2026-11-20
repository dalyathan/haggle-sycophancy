import sys, importlib, json
sys.path.insert(0, '.')
def build(rung):
    sys.argv = ['x', rung]
    import pilot.ladder as L
    importlib.reload(L)
    return L, L.build()
if __name__ == '__main__':
    rung = sys.argv[1]; sel = eval(sys.argv[2])
    L, P = build(rung)
    for p in P:
        if sel(p):
            print(json.dumps({k: p[k] for k in ("rung","v","hist","c","ctx","para","target","U")}))
            print(p["messages"][0]["content"]); print('---'); print(p["messages"][1]["content"]); print('=' * 40)
