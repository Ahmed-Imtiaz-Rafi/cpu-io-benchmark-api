import csv
from collections import defaultdict
from scipy.stats import mannwhitneyu

rows = list(csv.DictReader(open("analysis/runs.csv")))
g = defaultdict(list)
for r in rows:
    g[(r["scenario"], int(r["users"]), r["label"], r["build"])].append(float(r["p95"]))


def med(v):
    v = sorted(v)
    m = len(v) // 2
    return v[m] if len(v) % 2 else (v[m - 1] + v[m]) / 2


print("scenario users label | base_med int_med | change% | p | n | verdict")
for (sc, u, lab, b), base in sorted(g.items()):
    if b != "baseline":
        continue
    inte = g.get((sc, u, lab, "intervention"))
    if not inte:
        continue
    p = mannwhitneyu(base, inte, alternative="two-sided").pvalue
    mb, mi = med(base), med(inte)
    change = 100 * (mi - mb) / mb

    if lab == "POST login":
        red = -change
        if red >= 10 and p < 0.05:
            verdict = "H1 level PASS" + (" (clear)" if red >= 15 else "")
        else:
            verdict = "H1 level FAIL (not supported at 10%)"
    elif sc == "mixed":
        if change > 10 and p < 0.05:
            verdict = "H2: NEGATIVE impact"
        elif change > 10:
            verdict = "H2: inconclusive (possible harm)"
        elif change < -10 and p < 0.05:
            verdict = "H2: POSITIVE impact"
        else:
            verdict = "H2: no substantial impact detected"
    else:
        verdict = "control (orders alone, no verdict)"

    print(f"{sc} {u} {lab} | {mb:.0f} {mi:.0f} | {change:+.1f}% | {p:.4f} | "
          f"{len(base)}/{len(inte)} | {verdict}")