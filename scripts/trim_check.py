import csv, sys
from collections import defaultdict

rows = list(csv.DictReader(open(sys.argv[1])))
t0 = min(int(r["timeStamp"]) for r in rows)
b = defaultdict(lambda: defaultdict(list))
for r in rows:
    b[(int(r["timeStamp"]) - t0) // 10000][r["label"]].append(int(r["elapsed"]))

def p95(v):
    v = sorted(v)
    return v[int(0.95 * (len(v) - 1))]

for s in sorted(b):
    line = f"{s*10:>3}-{s*10+10:<3}s"
    for lab in ("GET orders", "POST login"):
        v = b[s][lab]
        line += f"  {lab}: n={len(v):>5} p95={p95(v) if v else 0:>5}"
    print(line)