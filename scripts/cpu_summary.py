import csv, json, os, sys
from collections import defaultdict

acc = defaultdict(list)
for dp, dn, fn in os.walk(sys.argv[1]):
    if "DONE" in fn and "failed" not in dp.split(os.sep):
        m = json.load(open(os.path.join(dp, "meta.json")))
        rows = [r for r in csv.DictReader(open(os.path.join(dp, "monitor.csv")))
                if m["start_ms"] + 30000 <= int(r["epoch_ms"]) <= m["end_ms"]]

        def avg(c):
            v = [float(r[c]) for r in rows if r[c] != ""]
            return sum(v) / len(v) if v else 0

        acc[(m["scenario"], m["users"], m["build"])].append(
            (avg("sys_cpu"), avg("api_cpu"), avg("mysql_cpu")))

print("scenario users build | sys% api mysql (mean over runs)")
for k in sorted(acc):
    v = acc[k]
    n = len(v)
    print(k[0], k[1], k[2], "|", *(f"{sum(x[i] for x in v) / n:.1f}" for i in range(3)))