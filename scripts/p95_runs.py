import csv, sys

for path in sys.argv[1:]:
    rows = list(csv.DictReader(open(path)))
    t0 = min(int(r["timeStamp"]) for r in rows)
    out = []
    for lab in ("GET orders", "POST login"):
        v = sorted(int(r["elapsed"]) for r in rows
                   if r["label"] == lab and int(r["timeStamp"]) - t0 >= 30000)
        out.append(f"{lab} p95={v[int(0.95*(len(v)-1))]} n={len(v)}")
    print(path.split("/")[-2], " | ".join(out))