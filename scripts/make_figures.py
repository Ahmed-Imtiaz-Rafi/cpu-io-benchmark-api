import csv, os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rows = list(csv.DictReader(open("analysis/runs.csv")))
g = defaultdict(list)
for r in rows:
    g[(r["scenario"], r["label"], r["build"], int(r["users"]))].append(float(r["p95"]))

panels = [("login", "POST login", "H1a: login alone, /login"),
          ("mixed", "POST login", "H1b: mixed, /login"),
          ("mixed", "GET orders", "H2: mixed, /orders"),
          ("orders", "GET orders", "Control: orders alone, /orders")]
users = [1, 10, 50, 100, 200]

fig, axes = plt.subplots(2, 2, figsize=(10, 7))
for ax, (sc, lab, title) in zip(axes.flat, panels):
    for build, style in (("baseline", "o-"), ("intervention", "s--")):
        med, lo, hi = [], [], []
        for u in users:
            v = sorted(g[(sc, lab, build, u)])
            m = v[len(v) // 2]
            med.append(m)
            lo.append(m - v[0])
            hi.append(v[-1] - m)
        ax.errorbar(users, med, yerr=[lo, hi], fmt=style, capsize=3, label=build)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(users)
    ax.set_xticklabels(users)
    ax.set_title(title)
    ax.set_xlabel("concurrent users")
    ax.set_ylabel("p95 response time (ms)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()

fig.suptitle("p95 by load level: median of 7 runs, bars show min to max")
fig.tight_layout()
os.makedirs("figures", exist_ok=True)
fig.savefig("figures/p95_by_users.png", dpi=150)
print("saved figures/p95_by_users.png")