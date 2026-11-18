"""Figures for plan v2 and plan v3 (median p95 per condition).

Run from the project root:
    python scripts/make_figures_v2_v3.py

Reads analysis/runs_v2.csv and analysis/runs_v3.csv, writes
figures/p95_v2.png and figures/p95_v3.png.
"""
import csv
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def med(v):
    v = sorted(v)
    m = len(v) // 2
    return v[m] if len(v) % 2 else (v[m - 1] + v[m]) / 2


def load(path):
    g = defaultdict(list)
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            g[(r["scenario"], r["label"], int(r["users"]), r["build"])].append(float(r["p95"]))
    return g


def panel(ax, g, scenario, label, builds, title):
    users = (100, 200)
    width = 0.8 / len(builds)
    for i, b in enumerate(builds):
        xs, ys = [], []
        for j, u in enumerate(users):
            vals = g.get((scenario, label, u, b))
            if vals:
                xs.append(j + i * width)
                ys.append(med(vals))
        bars = ax.bar(xs, ys, width, label=b)
        for rect, y in zip(bars, ys):
            ax.text(rect.get_x() + rect.get_width() / 2, y, f"{y:.0f}",
                    ha="center", va="bottom", fontsize=7)
    ax.set_xticks([j + width * (len(builds) - 1) / 2 for j in range(len(users))])
    ax.set_xticklabels([f"{u} users" for u in users])
    ax.set_ylabel("median p95 (ms, lower is better)")
    ax.set_title(title, fontsize=10)
    ax.legend(fontsize=7)


os.makedirs("figures", exist_ok=True)

g2 = load("analysis/runs_v2.csv")
b2 = ["baseline", "size16", "size32", "size64"]
fig, axes = plt.subplots(1, 3, figsize=(13, 4))
panel(axes[0], g2, "login", "POST login", b2, "Login only: /login p95")
panel(axes[1], g2, "mixed", "POST login", b2, "Mixed: /login p95")
panel(axes[2], g2, "mixed", "GET orders", b2, "Mixed: /orders p95")
fig.suptitle("Plan v2: executor size sweep (8 runs per bar)")
fig.tight_layout()
fig.savefig("figures/p95_v2.png", dpi=150)
plt.close(fig)

g3 = load("analysis/runs_v3.csv")
b3 = ["pool10", "pool8", "pool6", "pool4"]
fig, axes = plt.subplots(1, 2, figsize=(9, 4))
panel(axes[0], g3, "mixed", "POST login", b3, "Mixed: /login p95")
panel(axes[1], g3, "mixed", "GET orders", b3, "Mixed: /orders p95")
fig.suptitle("Plan v3: Hikari pool size sweep (8 runs per bar)")
fig.tight_layout()
fig.savefig("figures/p95_v3.png", dpi=150)
plt.close(fig)

print("wrote figures/p95_v2.png and figures/p95_v3.png")