import csv, json, os, sys
from collections import defaultdict
from scipy.stats import mannwhitneyu

SIZES = ["size16", "size32", "size64"]


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


def outcome(lab, change, padj):
    if lab == "POST login":
        if change <= -10 and padj < 0.05:
            return "login IMPROVEMENT"
        return "login RECOVERY" if change <= 10 else "login DEGRADED"
    if change > 10 and padj < 0.05:
        return "orders HARM"
    if change <= -10 and padj < 0.05:
        return "orders BENEFIT RETAINED"
    return "orders BENEFIT LOST"


rows = []
for dp, dn, fn in os.walk(sys.argv[1]):
    if "DONE" in fn and "failed" not in dp.split(os.sep):
        rows += per_run(dp)
os.makedirs("analysis", exist_ok=True)
with open("analysis/runs_v2.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(len(rows), "rows written to analysis/runs_v2.csv")

g = defaultdict(lambda: defaultdict(list))
for r in rows:
    g[(r["scenario"], r["users"], r["label"])][r["build"]].append(r)

res = defaultdict(dict)
print("scenario users label | build med_p95 change% p_adj | outcome | rps mean_ms users_inside")
for key in sorted(g):
    sc, u, lab = key
    bs = g[key]
    if "baseline" not in bs:
        continue
    base = [r["p95"] for r in bs["baseline"]]
    mb = med(base)
    sizes = [s for s in SIZES if s in bs]
    ps = [mannwhitneyu(base, [r["p95"] for r in bs[s]],
                       alternative="two-sided").pvalue for s in sizes]
    adj = holm(ps)
    for b, padj in [("baseline", None)] + list(zip(sizes, adj)):
        mp = med([r["p95"] for r in bs[b]])
        rps = med([r["rps"] for r in bs[b]])
        mean = med([r["mean"] for r in bs[b]])
        if padj is None:
            print(f"{sc} {u} {lab} | baseline {mp:.0f} - - | reference | "
                  f"{rps:.0f} {mean:.0f} {rps * mean / 1000:.0f}")
        else:
            change = 100 * (mp - mb) / mb
            o = outcome(lab, change, padj)
            res[key][b] = o
            print(f"{sc} {u} {lab} | {b} {mp:.0f} {change:+.1f}% {padj:.4f} | {o} | "
                  f"{rps:.0f} {mean:.0f} {rps * mean / 1000:.0f}")

print()
ok = ("login IMPROVEMENT", "login RECOVERY")
for s in SIZES:
    try:
        login_ok = all(res[("mixed", u, "POST login")][s] in ok for u in (100, 200))
        orders_ok = all(res[("mixed", u, "GET orders")][s] == "orders BENEFIT RETAINED"
                        for u in (100, 200))
        print(s, "| login recovered at 100 and 200:", login_ok,
              "| orders benefit retained at 100 and 200:", orders_ok,
              "| SWEET SPOT" if login_ok and orders_ok else "")
    except KeyError:
        print(s, "| incomplete (mixed runs missing)")