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

| Outcome at a level      | Report as                                  |
|-------------------------|--------------------------------------------|
| Above +10% and p < 0.05 | Negative impact                            |
| Above +10%, p >= 0.05   | Inconclusive: possible harm, not confirmed |
| Between -10% and +10%   | No substantial impact detected             |
| Below -10%, p >= 0.05   | No substantial impact detected             |
| Below -10% and p < 0.05 | Positive impact (predicted as possible)    |

* **H2 overall:** H2 holds if none of 50, 100, 200 shows a negative impact. Reported as inconclusive if any level is inconclusive. Wording: "no substantial impact detected above 10%".
* **Bad-run rule:** A run is repeated only for a pre-listed fault: API fails to start or crashes, JMeter aborts, monitor fails, external interruption (restart, sleep, power loss, antivirus), failed quiet-machine gate, failed data-integrity check. Never repeated because a result looks odd (errors are data). No outlier removal. Excluded runs are logged here with the reason and files kept. A rerun keeps the same run number.
* **Results:** `results/{pilot|final}/batch-NN_date/{scenario}_{build}_u{users}_rep{n}/` holding `.jtl`, `monitor.csv`, `api.log`, `meta.json`, `DONE`. Failed attempts in `failed/`. Manifest and checksums committed. Raw `results/` git-ignored. Batch zip copied to a second location.
* **Provisional (fix by dated amendment after the pilot, before `plan-v1`):** 30 s trim | quiet-machine gate (starting value: system CPU under 5% for 10 s) | 120 s run length (may lengthen for p99) | 60 s cooldown
* **Pending (not yet decided):** intervention packaging (two jars from tagged commits, or one jar with a switch) | config pass (`show-sql` off, `ddl-auto=validate`, Hikari pool size, Tomcat limits, GC logging flag, KeepAlive) | `/orders` and `mixed` plans | monitor script | driver script
* **Next:** Config pass and builds, then pilot (trim check, idle CPU, login request counts in mixed, noise floor, driver dry run), then amendment, then tag `plan-v1`.

### 2026-10-18: Config Pass, JVM Setup and Baseline Freeze

* **JVM:** Temurin `25.0.4.1+1` (`25.0.4.1+1-LTS`, OpenJDK 64-Bit Server VM), launched by full path (`$HOME/.jdks/temurin-25.0.4.1/bin/java`). `java` on the PATH is JDK 17, so it is never used for runs.
* **JVM defaults (recorded, not changed):** G1 collector | max heap 4,276,092,928 B (~4 GB, 25% of RAM) | initial heap 268,435,456 B (256 MB) | G1 region 2 MB | 13 parallel / 3 concurrent GC threads | 16 logical processors. Small initial heap means the heap grows early in each run, covered by the fresh JVM per run and the 30 s trim.
* **Benchmark config:** `config/benchmark.properties` (committed, `a4556f6db23ff6f94e4f48b5b3a311410bbafbbd6e04ccdc4e717833865731cb *config/benchmark.properties`), passed to both builds with `--spring.config.additional-location=file:config/benchmark.properties`. It holds `show-sql=false`, `open-in-view=false`, `ddl-auto=validate`, Hikari max 10 / min-idle 10, `server.tomcat.threads.max=200`, `app.seed.enabled=false`. The packaged `application.properties` now holds only app name, datasource URL and credentials.
* **Checked in the startup log:** Tomcat 11.0.26 | Hibernate 7.4.5.Final | MySQL 8.0.46 | Hikari max 10 / min-idle 10, pool full at start | seeder skipped | started in 3.7 s. `ddl-auto=validate` tested against the dump earlier.
* **Not yet checked:** no SQL in the console under requests (`show-sql` off) | Tomcat's 200 threads under load | Hikari at 10 vs 50 (pilot).
* **Mistake found:** `baseline-v1` was tagged before the `@Param("userid")` fix was committed, so it points at code where `/users/{userId}/orders` returns 500. `baseline-v1` is left in place and **not used**. Found via `git diff baseline-v1`, and `git status` showed the fix and `config/` were uncommitted when the tag was made.
* **Baseline:** tag `baseline-v2`, commit `00c19ebcd8486ee81c9a5079680524ccf87c2307`, built from a clean tree. Code, `benchmark.properties` and the packaged properties together define it.
* **Baseline jar:** `artifacts/baseline.jar`, SHA-256 `c875668229e2c9419e607ccccac6edfc3736d506b9e9d4fbfb3d0263c8d26f08`. Packaged `application.properties` inspected and contains credentials only. `/login` (200, 401) and `/users/1/orders` (40 orders) verified. Earlier hashes (`8472d94e…`, `537289ae…`) came from builds of unconfirmed tree state and are discarded.
* **Jar handling:** Maven jars are not byte-reproducible, so each jar is built once, copied to `artifacts/`, hashed, and never rebuilt for a run. The driver launches only from `artifacts/` and checks the hash at the start of each batch. `artifacts/` is git-ignored (the jar contains the DB password).
* **After the tag:** `application.properties.example` trimmed to credentials only. Documentation only, no runtime effect, jar unchanged, no new tag.
* **Tagging rule:** a new tag only when Java code, `benchmark.properties`, `pom.xml` or the dataset changes.
* **Next:** README fix (setup and Option B wording, JDK row, `config/`) | `/orders` and `mixed` plans | monitor script | intervention build (`artifacts/intervention.jar`) | driver, then pilot.

### 2026-10-18: Amendment to Pre-registered Analysis Plan

* **Baseline reference changed:** the plan entry's "baseline code at tag `baseline-v1`" is superseded. The baseline is tag `baseline-v2`, commit `00c19ebcd8486ee81c9a5079680524ccf87c2307`, jar `artifacts/baseline.jar` (SHA-256 `c875668229e2c9419e607ccccac6edfc3736d506b9e9d4fbfb3d0263c8d26f08`). Reason: see the Config Pass entry (`baseline-v1` predates the `@Param` fix). No analysis choice is changed.
* **Packaging decided:** two jars, each built once from its own tagged commit and copied to `artifacts/`. The intervention jar's hash is recorded before any counted run.
* **Config pass:** complete except the three items under "Not yet checked" in the Config Pass entry, which belong to the pilot.
* **Still provisional:** the 30 s trim, the quiet-machine gate, the 120 s run length and the 60 s cooldown.
* **Not yet tagged:** `plan-v1`.

### 2026-10-19: JMeter Plans and Resource Monitor

* **Plans:** `jmeter/login.jmx`, `jmeter/orders.jmx`, `jmeter/mixed.jmx` (commit `f02b5f5`). All parameterized: `threads`, `rampup` (default 10), `duration` (default 120), infinite loop with thread lifetime. 127.0.0.1:8080, KeepAlive on, 30 s connect and response timeouts, no listeners (results via `-l`). Old `login-baseline.jmx` removed.
* **Labels (same in every plan, used by the analysis):** `POST login`, `GET orders`.
* **Assertions:** `POST login` = response code equals `${expected}` with Ignore Status ticked. `GET orders` = response code 200 and JSON `$.length()` equals 40, so an empty list fails.
* **Mixed plan:** Throughput Controllers in Percent Executions mode, 6.25% login and 93.75% orders (1:15), Per User off. Ratio is by request count, not CPU time.
* **Checks (pilot, not counted):**
  * `orders`, 1 thread, 30 s: 3,519 samples, 0 errors, avg 8 ms (max 253 ms, the cold first request).
  * `orders` with `/users/9999/orders`: 3,758 samples, 100% errors, so the assertion rejects an empty list. Broken version not saved.
  * `mixed`, 10 threads, 30 s: 17,059 samples, 0 errors, avg 14 ms. 15,993 `GET orders` to 1,066 `POST login` = 15.0 : 1.
* **Mistakes fixed:** `${user_id}` unresolved because the CSV Data Set Config was missing in the mixed plan | run stopped after 1 sample until Thread Group loop settings were corrected | label `Post login` renamed to `POST login` | a failed run had appended a multi-line error into a `.jtl`, so the file was deleted (JMeter appends to an existing `-l` file, so the driver must use fresh filenames).
* **Monitor:** `scripts/monitor.py` (commit `0bef2b6`), Python 3.12.10, psutil 7.2.2. One row per second: epoch ms, system CPU, memory %, then CPU and RSS for api, mysql, jmeter. Processes found by listening port (8080, 3306) and by command line (`ApacheJMeter` with ` -n `, so the GUI is not picked). Per-process CPU is a percentage of one core. Idle system CPU measured at about 1 to 2%.
* **MySQL processes:** two `mysqld.exe`. PID on port 3306 is the server (347 s CPU, 95 MB). The other is an idle wrapper (0.016 s CPU, 12 MB), ignored.
* **Operational rules:** JMeter GUI must be closed during runs | monitor must find the non-GUI JMeter, which starts after it, so it keeps searching until found.
* **Observation (to confirm in the pilot):** in the 10-user mixed run, mysqld used about 690% CPU against the API's 310%. `/orders` may behave as CPU work inside MySQL (unindexed scan on the same CPU), not as waiting on I/O. Candidate limitation line and a point for the write-up.
* **Next:** intervention build (8-thread executor, `@Async` on `/login`) | driver and schedule generator | analysis script | pilot, then amendment, then `plan-v1`.

### 2026-10-24: Amendment to Pre-registered Analysis Plan (pilot complete)

* **Status:** Pilot finished before any counted run. **No hypothesis, threshold, metric, test or verdict rule is changed.** Only the provisional values are fixed and open items closed. Pilot runs (`results/pilot/`, git-ignored) never count toward the 7.
* **Baseline:** tag `baseline-v2`, jar `artifacts/baseline.jar`, SHA-256 `c875668229e2c9419e607ccccac6edfc3736d506b9e9d4fbfb3d0263c8d26f08` (see Config Pass entry; `baseline-v1` is not used).
* **Intervention:** tag `intervention-v1`, commit `30a0166b68481b633c64915b0bbce42488872f35`, jar `artifacts/intervention.jar`, SHA-256 `c411d1a3211b8cb7d3144f667520e63bb392100e056aca073a0f7ece1b88cdff`. Diff against `baseline-v2` in `src/main/java`: new `AsyncConfiguration` (`cpuBoundExecutor`: 8 core, 8 max, queue 1000, `@EnableAsync`), `@Async("cpuBoundExecutor")` on `AuthService.login` (so the DB lookup and BCrypt both run on the executor), async `CompletableFuture` return in `AuthController`. Checked with `jcmd`: exactly 8 threads `cpu-1`..`cpu-8`, about equal CPU time each. Codes still 200/401.
* **Fixed provisional values:**
  * 30 s trim: confirmed. In 200-user mixed baseline runs p95 is high in the first 20 s (orders 404 to 628 ms) and flat from 20 s (about 292 ms).
  * Quiet-machine gate: system CPU under 5% for 10 s. Idle machine reads about 1 to 2%, gate passed in every pilot run.
  * Run length 120 s and cooldown 60 s: kept.
* **Noise floor (mixed, 200 users, baseline, 6 pilot runs):** orders p95 326, 550, 310, 318, 301, 323 ms | login p95 370, 469, 370, 371, 356, 368 ms. Five clean runs: orders mean 316 ms (SD 10, about 3%), login mean 367 ms (SD 6, about 2%). So the 10% lines are above run-to-run noise. One run in six (rep2: orders +74%, login +28%) had an unexplained slowdown. GC ruled out (about 60 pauses and about 100 ms total per 10 s bucket, longest 42 ms, same in quiet and slow stretches). No outside process identified. Kept under the bad-run rule. A second slow run appeared in login-only intervention (rep2, 124/s vs 134/s). Monitor now logs the busiest non-target process each second.
* **Hikari pool fixed at 10:** `/orders` alone, 200 users, baseline: pool 10 p95 285 ms (about 730/s) vs pool 50 p95 831 and 939 ms (about 853/s), slowest request 29.6 s at pool 50. 10 kept for all runs. Not tested: whether the intervention's effect depends on pool size.
* **Verified under load:** 200 Tomcat request threads (`jcmd`), no SQL in the console, 0 errors in clean runs.
* **Data bug found and fixed:** `login.jmx` read a Desktop copy of the CSV (not checksummed, presumed different) and produced about 0.1% assertion failures (e.g. `user0261` expected 401, CSV row says 200). Replay of `db/seeded-users.csv` against the API: 0 mismatches in 1,000. After the fix: 23,787 samples, 0 errors. All three plans now use the relative path `db/seeded-users.csv`. Earlier login-only pilot results on the wrong file are discarded. Do not open and resave plans in the GUI before a batch (it can write an absolute path); verify with `grep filename jmeter/*.jmx`.
* **p99 eligibility, applying the rule:** login in `mixed` has about 3,900 requests per 90 s window, so p99 is "n/a (too few requests)". Orders in `mixed` (about 58,000) and login in `login` at saturation (about 17,000) are eligible. Levels 1 and 10 are expected to be n/a.
* **Pilot first look (not counted, not used to change anything):**
  * `mixed`, 200 users: `/orders` p95 226 to 231 ms vs 301 to 326 baseline (about -28%); `/login` p95 2,749 to 2,793 ms vs 356 to 371 (about +650%).
  * `login`, 200 users: throughput about 134/s (intervention) vs about 198/s (baseline); p95 1,523 / 1,785 / 1,525 ms vs 1,630 ms (one clean baseline run).
  * Pilot sample is far too small for any verdict. The real runs decide.
* **Driver and tools (tested on pilot):** `scripts/driver.py` (quiet gate, port check, API start with readiness poll, monitor, JMeter, 3 attempts per run, failed attempts moved to `failed/`, resume by `DONE` file, no cooldown for skipped runs, `meta.json` with jar hash and Java version, per-run `gc.log`), `scripts/monitor.py`, `scripts/make_schedule.py` (210 runs, pair order flips, `scripts/schedule.csv`), `scripts/analyze_runs.py` and `scripts/verdicts.py` (per-level and combined H1a, H1b, H2 as pre-registered). Dry run through `run_batch`: 4 of 4 `ok` in schedule order, resume skipped all 4, port-busy fault retried 3 times and kept in `failed/`.
* **Batches:** `run_batch('batch-NN_date', first, last)` into `results/final/`. Three batches: seq 1 to 70, 71 to 140, 141 to 210 (about 3.9 h each, builds alternate inside each). Both builds must exist before batch 1.
* **Limitations to carry into the README and write-up:** `/orders` is not I/O-bound on this machine (mysqld uses about 970% CPU, API about 370%, unindexed scan on the same CPU) | pool size tested only at 10 and 50 | whole `login()` runs on the executor | one machine, 8 cores / 16 logical, CPU about 85 to 90% busy at 200 users | about 1 in 6 runs shows an unexplained slowdown | JMeter uses about 10 to 16% of one core at 200 users.
* **Resolved from "Pending":** intervention packaging (two jars) | config pass | `/orders` and `mixed` plans | monitor | driver.
* **Integrity check (manual, as pre-registered):** the driver does not run it. Before and after each batch, run `CHECKSUM TABLE users, products, orders` and record the values in the batch entry; a change is a data-integrity fault. MySQL is restarted by hand before each batch.
* **Next:** commit this entry and tag `plan-v1` (hash recorded in the batch 1 entry), set power plan and pause Windows Update, then start batch 1 (seq 1 to 70).

### 2026-10-25: Batch 1 (seq 1 to 70), login alone

* **Plan:** tag `plan-v1`, commit `7230f6a28948da3290249eb3484f2d322ec0de43`. No changes since.
* **Before:** MySQL restarted by hand. `CHECKSUM TABLE`: users `1701132287`, products `2759041946`, orders `2384344284`.
* **Command:** `python -c "import sys; sys.path.insert(0,'scripts'); import driver; driver.run_batch('batch-01_2026-10-25', 1, 70)"`
* **After:** `CHECKSUM TABLE` (MySQL not restarted): users `1701132287`, products `2759041946`, orders `2384344284`. All identical to "before".
* **Outcome:** 70 of 70 runs ok on the first attempt, no `failed/` folder, no retries. Started 00:23 on 2026-10-25 (the date rolled over), took about 3 h 54 min. Scenario: `login`, all five levels, 7 runs per build.
* **Data:** raw runs in `results/final/batch-01_2026-10-25/` (git-ignored). `analysis/runs.csv` is regenerated from them.

### 2026-10-25: Batch 2 (seq 71 to 140), orders alone

* **Plan:** tag `plan-v1`, commit `7230f6a28948da3290249eb3484f2d322ec0de43`. No changes since.
* **Before:** not recorded (the checksums were not saved before this batch started). Covered by the "after" reading below, which matches batch 1.
* **Command:** `python -c "import sys; sys.path.insert(0,'scripts'); import driver; driver.run_batch('batch-02_2026-10-25', 71, 140)"`
* **After:** `CHECKSUM TABLE` (MySQL not restarted): users `1701132287`, products `2759041946`, orders `2384344284`. Identical to batch 1.
* **Outcome:** 70 of 70 runs ok on the first attempt, no `failed/` folder, no retries. Ended 12:59 on 2026-10-25. Scenario: `orders`, all five levels, 7 runs per build.
* **Data:** raw runs in `results/final/batch-02_2026-10-25/` (git-ignored). `analysis/runs.csv` is regenerated from them.

### 2026-10-25: Batch 3 (seq 141 to 210), mixed

* **Plan:** tag `plan-v1`, commit `7230f6a28948da3290249eb3484f2d322ec0de43`. No changes since.
* **Before:** MySQL restarted by hand. `CHECKSUM TABLE`: users `1701132287`, products `2759041946`, orders `2384344284`.
* **Command:** `python -c "import sys; sys.path.insert(0,'scripts'); import driver; driver.run_batch('batch-03_2026-10-25', 141, 210)"`
* **After:** `CHECKSUM TABLE` (MySQL not restarted): users `1701132287`, products `2759041946`, orders `2384344284`. Identical to "before" and to batches 1 and 2.
* **Final reading:** `CHECKSUM TABLE` taken again after the analysis: same three values. Unchanged.
* **Outcome:** 70 of 70 runs ok on the first attempt, no `failed/` folder, no retries. Ended 17:10 on 2026-10-25. Scenario: `mixed` (1 login : 15 orders), all five levels, 7 runs per build.
* **Data:** raw runs in `results/final/batch-03_2026-10-25/` (git-ignored). `analysis/runs.csv` is regenerated from all three batches.

### 2026-10-25: Results of the pre-registered analysis (all 210 runs)

* **Data:** 210 counted runs (3 batches × 70), 7 per condition, no failed attempts, no retries, no exclusions. Checksums of `users`, `products`, `orders` unchanged across all batches. 0 failed requests in all 280 analysis rows (each run's 90 s window), checked with `analysis/runs.csv`.
* **Analysis:** `scripts/analyze_runs.py` and `scripts/verdicts.py`, run as pre-registered (p95 per run, two-sided Mann-Whitney U per level, thresholds 10% and p < 0.05). No rule changed after seeing data.
* **H1a (login alone): not supported at the 10% threshold.** Login p95, baseline vs intervention, ms: 1 user 56 / 56 | 10 users 74 / 92 (+24.3%) | 50 users 383 / 393 (+2.6%, p 0.0405) | 100 users 551 / 864 (+56.8%, p 0.0021) | 200 users 1,062 / 1,725 (+62.4%, p 0.0021). The intervention was slower, not faster, where the CPU saturated.
* **H1b (login in mixed): not supported at the 10% threshold.** Login p95: 1 user 60 / 61 | 10 users 83 / 83 | 50 users 143 / 143 | 100 users 218 / 556 (+155.0%, p 0.0021) | 200 users 366 / 2,869 (+683.9%, p 0.0021).
* **H2 (orders in mixed): holds, no negative impact.** Orders p95: 1 user 8 / 8 | 10 users 17 / 17 | 50 users 76 / 76 | 100 users 152 / 132 (-13.2%, p 0.0020) | 200 users 302 / 135 (-55.3%, p 0.0020). Positive impact at 100 and 200 users, none at 50 or below. The script's wording ("no substantial impact detected") understates this, because the positive label requires all three levels; the per-level result stands as reported here.
* **Control (orders alone):** orders p95 identical between builds at every level (changes 0.0%, -5.6%, 0.0%, -0.7%, 0.0%; all p at least 0.14), as expected because the `/orders` code is the same in both builds.
* **Reading (for RESULTS.md, not for decisions):** separation traded `/login` latency for `/orders` latency once the CPU was saturated (100 and 200 users); nothing changed at 50 users or below. The pilot's `/orders` figure at 200 users (about -28%, 3 runs) differs from the counted result (-55%); the counted result is used. The 1-user rows have identical values, so their p-values are `nan` and their H1 label is not meaningful.
* **Backup:** `results/final_backup.zip`, SHA-256 `173d9e67eb44f38235524326b3d501ab4ccdd2a28db5641cf7e1dd1bcd30d8da`. Copied to `C:\Users\USER\cpu-io-backup\final_backup.zip` (a second drive in the same PC), hash re-checked and matching on 2026-10-25. Off-PC copy (USB or cloud): TODO. Jars (`artifacts/*.jar`) not backed up; identified by the hashes recorded above.
* **Next:** commit these entries, make the off-PC copy, write `RESULTS.md`, README fixes, design PDF revisions.