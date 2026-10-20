import csv

scenarios = ["login", "orders", "mixed"]
levels = [1, 10, 50, 100, 200]
reps = range(1, 8)

rows = []
pair = 0
for sc in scenarios:
    for users in levels:
        for rep in reps:
            order = ["baseline", "intervention"] if pair % 2 == 0 else ["intervention", "baseline"]
            for build in order:
                rows.append([len(rows) + 1, sc, users, rep, build,
                             f"{sc}_{build}_u{users:03d}_rep{rep}"])
            pair += 1

with open("scripts/schedule.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["seq", "scenario", "users", "rep", "build", "run_name"])
    w.writerows(rows)
print(len(rows), "runs")