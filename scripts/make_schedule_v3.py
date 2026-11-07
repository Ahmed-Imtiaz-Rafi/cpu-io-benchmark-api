import csv

builds = ["pool10", "pool8", "pool6", "pool4"]
scenarios = ["mixed"]
levels = [100, 200]
reps = range(1, 9)

rows = []
block = 0
for sc in scenarios:
    for u in levels:
        for rep in reps:
            k = block % 4
            order = builds[k:] + builds[:k]
            for b in order:
                rows.append([len(rows) + 1, sc, u, rep, b, f"{sc}_{b}_u{u:03d}_rep{rep}"])
            block += 1

with open("scripts/schedule_v3.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["seq", "scenario", "users", "rep", "build", "run_name"])
    w.writerows(rows)
print(len(rows), "runs")