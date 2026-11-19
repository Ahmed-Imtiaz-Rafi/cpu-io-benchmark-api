import csv, json, os, random, sys
from collections import defaultdict
from scipy.stats import mannwhitneyu

CONTROL = "pool10"
POOLS = ["pool12", "pool16", "pool24"]
LOGIN_MIN = {100: 10, 200: 15}      # required login p95 improvement, %
ORDERS_MAX = {100: 5, 200: 10}      # orders p95 worsening limit, %
random.seed(42)


def pct(v, q):
    return v[int(q * (len(v) - 1))]


def med(v):
    v = sorted(v)
    m = len(v) // 2
    return v[m] if len(v) % 2 else (v[m - 1] + v[m]) / 2


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj = [0.0] * len(ps)
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (len(ps) - rank) * ps[i])
        adj[i] = min(1.0, run)
    return adj


def boot_upper(ctrl, test, n=10000):
    """Upper bound of the 95% bootstrap CI for the % change in median p95."""
    ch = []
    for _ in range(n):
        c = med(random.choices(ctrl, k=len(ctrl)))
        t = med(random.choices(test, k=len(test)))
        ch.append(100 * (t - c) / c)
    ch.sort()
    return ch[int(0.975 * (n - 1))]


def per_run(d):
    meta = json.load(open(os.path.join(d, "meta.json")))
    rows = list(csv.DictReader(open(os.path.join(d, "run.jtl"))))
    t0 = min(int(r["timeStamp"]) for r in rows)
    win = [r for r in rows if int(r["timeStamp"]) - t0 >= 30000]
    out = []
    for lab in ("GET orders", "POST login"):
        sel = [r for r in win if r["label"] == lab]
        if not sel:
            continue
        v = sorted(int(r["elapsed"]) for r in sel)
        err = sum(1 for r in sel if r["success"] != "true")
        out.append({"scenario": meta["scenario"], "users": meta["users"],
                    "rep": meta["rep"], "build": meta["build"], "label": lab,
                    "n": len(v), "p95": pct(v, 0.95),
                    "mean": round(sum(v) / len(v), 1),
                    "err_pct": round(100 * err / len(v), 3),
                    "rps": round(len(v) / 90, 1)})
    return out


rows = []
for dp, dn, fn in os.walk(sys.argv[1]):
    if "DONE" in fn and "failed" not in dp.split(os.sep):
        rows += per_run(dp)
os.makedirs("analysis", exist_ok=True)
with open("analysis/runs_v4.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(len(rows), "rows written to analysis/runs_v4.csv")

g = defaultdict(lambda: defaultdict(list))
for r in rows:
    g[(r["users"], r["label"])][r["build"]].append(r)

res = {}
print("users label | build med_p95 change% | p_adj / CI_upper | rps mean_ms")
for key in sorted(g):
    u, lab = key
    bs = g[key]
    ctrl = [r["p95"] for r in bs[CONTROL]]
    mc = med(ctrl)
    print(f"{u} {lab} | {CONTROL} {mc:.0f} - | reference | "
          f"{med([r['rps'] for r in bs[CONTROL]]):.0f} "
          f"{med([r['mean'] for r in bs[CONTROL]]):.0f}")
    ps = [mannwhitneyu(ctrl, [r["p95"] for r in bs[p]],
                       alternative="two-sided").pvalue for p in POOLS]
    adj = holm(ps)
    for p, pa in zip(POOLS, adj):
        test = [r["p95"] for r in bs[p]]
        mp = med(test)
        change = 100 * (mp - mc) / mc
        if lab == "POST login":
            ok = change <= -LOGIN_MIN[u] and pa < 0.05
            extra = f"p_adj {pa:.4f}"
        else:
            up = boot_upper(ctrl, test)
            ok = up < ORDERS_MAX[u]
            extra = f"CI_upper {up:+.1f}%"
        res[(u, lab, p)] = ok
        print(f"{u} {lab} | {p} {mp:.0f} {change:+.1f}% | {extra} | "
              f"{'PASS' if ok else 'FAIL'} | "
              f"{med([r['rps'] for r in bs[p]]):.0f} "
              f"{med([r['mean'] for r in bs[p]]):.0f}")

print()
for p in POOLS:
    login_ok = all(res[(u, "POST login", p)] for u in (100, 200))
    orders_ok = all(res[(u, "GET orders", p)] for u in (100, 200))
    print(p, "| login passes at 100 and 200:", login_ok,
          "| orders safe at 100 and 200:", orders_ok,
          "| SUCCESS" if login_ok and orders_ok else "")