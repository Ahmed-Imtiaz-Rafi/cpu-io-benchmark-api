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

    * Overall: H2 holds if none of 50, 100, 200 shows a negative impact. Reported as inconclusive if any level is inconclusive. Wording: "no substantial impact detected above 10%".
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