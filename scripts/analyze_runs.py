import csv, json, os, sys


def pct(v, q):
    return v[int(q * (len(v) - 1))]


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
                    "p99": pct(v, 0.99) if len(v) >= 10000 else "",
                    "err_pct": round(100 * err / len(v), 3),
                    "rps": round(len(v) / 90, 1)})
    return out


root = sys.argv[1]
rows = []
for dp, dn, fn in os.walk(root):
    if "DONE" in fn and "failed" not in dp.split(os.sep):
        rows += per_run(dp)
os.makedirs("analysis", exist_ok=True)

with open("analysis/runs.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(len(rows), "rows written to analysis/runs.csv")