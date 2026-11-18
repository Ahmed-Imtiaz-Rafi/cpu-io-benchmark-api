"""Schedule for the unregistered baseline check (login only, baseline, 200 users, 8 runs).

Run from the project root:
    python scripts/make_schedule_check.py
Writes scripts/schedule_check.csv with the columns the driver reads.
"""
import csv

with open("scripts/schedule_check.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["seq", "scenario", "users", "rep", "build", "run_name"])
    for rep in range(1, 9):
        w.writerow([rep, "login", 200, rep, "baseline", f"login_baseline_u200_rep{rep}"])
print("wrote scripts/schedule_check.csv (8 runs)")