### 2026-10-17: `/login` Plan Validation
* **Setup:** JMeter 5.6.3 | 1 thread, 1,000 iter. | CSV SHA-256: `552af2311d76d5618fc563000a877ac0d15919a7a4232bef9160f5c5d1034837`
* **Config:** Variable Names (empty), Ignore Status (ticked), Assertion: `${expected}`
* **Result:** 1,000 samples, **0 errors**, ~58 ms avg.
    * 50 wrong-password rows passed as expected `401`s. Throwaway test confirmed assertion triggers correctly.
* **Fixes:** Cleared Variable Names (fixed header row sent as data); ticked Ignore Status (fixed wrong-passwords counted as errors).
* **Next:** Decide run parameters, then scale concurrency.

### 2026-10-17: Pre-registered Analysis Plan
* **Status:** Written before any counted data exists. Edits only via dated amendments. Pilot runs do not count toward the 7. Tag `plan-v1` once the amendment in "Provisional" is done.
* **Fixed environment:** Single PC (Ryzen 5700X, 16 GB, Windows 11) | versions pinned in README | dataset checksums in README | BCrypt strength 10 | baseline code at tag `baseline-v1`
* **Scenarios:** `login` alone, `orders` alone (control: `/orders` code is identical in both builds), `mixed` (fixed 1 login : 15 orders via Throughput Controller, no second ratio)
* **Levels:** 1, 10, 50, 100, 200 users. All get 7 runs. Verdicts only at 50, 100, 200; 1 and 10 are described only.
* **Runs:** 7 per condition = 210 runs. Number fixed now, no runs added after seeing results.
* **Run parameters:** 10 s ramp-up | 120 s total, first 30 s trimmed, 90 s analysed | no think time | 30 s timeouts in HTTP Request | API restarted before every run, MySQL left running (restarted once per batch, `CHECKSUM TABLE` before and after) | 60 s cooldown plus quiet-machine gate | run order flips each pair (AB, BA, AB...)
* **Unit of analysis:** One p95 per run, computed from all requests to that endpoint in the 90 s window of the raw `.jtl`. Error rate reported separately.
* **Metrics:**
  * Primary: p95.
  * Secondary: throughput, p99 (only where every compared run has at least 10,000 requests to that endpoint in the window, otherwise "n/a (too few requests)").
  * Diagnostic (described, not tested): median, mean, error rate, CPU per process, GC pauses.
* **Statistics:** Mann-Whitney U, two-sided, per level, p < 0.05. No multiple-comparison correction, because H1 needs all three levels to pass. p99 and throughput are secondary evidence and cannot change a verdict.
* **H1** (`/login` p95, reduction = (baseline - intervention) / baseline):
  * Holds at a level if reduction is at least 10% and p < 0.05. 15% or more is described as "clear".
  * Verdict needs 50, 100 and 200 all to pass.
  * H1a = isolated `login` runs. H1b = `/login` p95 in `mixed` runs. Separate verdicts.
  * Below threshold is written as "not supported at the 10% threshold", with the actual size reported.
* **H2** (`/orders` p95 in `mixed` only, change = (intervention - baseline) / baseline, positive = worse):

| Outcome at a level | Report as |
|---|---|
| Above +10% and p < 0.05 | Negative impact |
| Above +10%, p >= 0.05 | Inconclusive: possible harm, not confirmed |
| Between -10% and +10% | No substantial impact detected |
| Below -10%, p >= 0.05 | No substantial impact detected |
| Below -10% and p < 0.05 | Positive impact (predicted as possible) |

    * Overall: H2 holds if none of 50, 100, 200 shows a negative impact. Reported as inconclusive if any level is inconclusive. Wording: "no substantial impact detected above 10%".
* **Bad-run rule:** A run is repeated only for a pre-listed fault: API fails to start or crashes, JMeter aborts, monitor fails, external interruption (restart, sleep, power loss, antivirus), failed quiet-machine gate, failed data-integrity check. Never repeated because a result looks odd (errors are data). No outlier removal. Excluded runs are logged here with the reason and files kept. A rerun keeps the same run number.
* **Results:** `results/{pilot|final}/batch-NN_date/{scenario}_{build}_u{users}_rep{n}/` holding `.jtl`, `monitor.csv`, `api.log`, `meta.json`, `DONE`. Failed attempts in `failed/`. Manifest and checksums committed. Raw `results/` git-ignored. Batch zip copied to a second location.
* **Provisional (fix by dated amendment after the pilot, before `plan-v1`):** 30 s trim | quiet-machine gate (starting value: system CPU under 5% for 10 s) | 120 s run length (may lengthen for p99) | 60 s cooldown
* **Pending (not yet decided):** intervention packaging (two jars from tagged commits, or one jar with a switch) | config pass (`show-sql` off, `ddl-auto=validate`, Hikari pool size, Tomcat limits, GC logging flag, KeepAlive) | `/orders` and `mixed` plans | monitor script | driver script
* **Next:** Config pass and builds, then pilot (trim check, idle CPU, login request counts in mixed, noise floor, driver dry run), then amendment, then tag `plan-v1`.