# Results

## 1. Summary

This study asked whether moving CPU-bound work (BCrypt password verification in `POST /login`) onto a dedicated 8-thread executor reduces CPU-bound degradation in a Spring Boot REST API under concurrent load, without harming an I/O-oriented endpoint (`GET /users/{userId}/orders`). Two builds were compared over 210 counted runs: a synchronous baseline and the intervention.

| Hypothesis | Verdict |
|---|---|
| H1a: login p95 improves by at least 10% (login alone) | Not supported. The intervention was slower at 100 and 200 users (+56.8% and +62.4%). |
| H1b: login p95 improves by at least 10% (mixed load) | Not supported. The intervention was slower at 100 and 200 users (+155.0% and +683.9%). |
| H2: no substantial negative effect on `/orders` p95 (mixed load) | Holds. `/orders` p95 was lower at 100 and 200 users (-13.2% and -55.3%), unchanged at 50 users and below. |

Once the CPU saturated, separation traded `/login` latency for `/orders` latency. No effect was observed at 50 users or below.

## 2. What was tested

* **Builds.** Baseline (tag `baseline-v2`): both endpoints synchronous on Tomcat's 200-thread request pool. Intervention (tag `intervention-v1`): `AuthService.login`, including the user lookup and BCrypt verification, runs on `cpuBoundExecutor` (8 core and 8 maximum threads, queue capacity 1000). The Tomcat pool is unchanged at 200.
* **Scenarios.** `login` (only `POST /login`), `orders` (only `GET /users/{userId}/orders`, a control, since this code is identical in both builds) and `mixed` (1 login request per 15 orders requests, enforced by request share).
* **Load.** 1, 10, 50, 100 and 200 concurrent users, with no think time. Each run lasts 120 s with a 10 s ramp-up. The first 30 s are discarded and the remaining 90 s analysed. The API is restarted before every run, with a 60 s cooldown between runs. Build order alternates in pairs (AB, BA).
* **Repetitions.** 7 runs per build, scenario and level (210 runs in 3 batches). No run failed or was repeated, and no request failed an assertion in the analysis windows.
* **System under test.** Single Windows 11 machine, AMD Ryzen 5700X (8 cores, 16 logical processors), 16 GB RAM, running the API, MySQL 8.0.46 and JMeter 5.6.3 together. Temurin 25.0.4.1, Spring Boot 4.1.1, Tomcat 11.0.26, Hikari pool of 10 connections.
* **Data.** 1,000 users, 150 products and 40,000 orders (40 per user), generated once with a fixed seed. The MySQL table checksums were identical before and after every batch. BCrypt strength is 10.

## 3. How results were judged

The analysis plan was written and tagged (`plan-v1`) before any counted run. Its rules were not changed afterwards.

* **Metric.** One p95 response time per run, computed from the raw JMeter samples of the 90 s analysis window. p95 is the value below which 95% of requests fall.
* **Test.** Two-sided Mann-Whitney U test per level on the 7 baseline and 7 intervention p95 values, at p < 0.05.
* **H1** holds at a level if the intervention's p95 is at least 10% lower and p < 0.05. The verdict requires 50, 100 and 200 users all to pass.
* **H2** (`/orders` p95, mixed scenario) is negative at a level if p95 rises by more than 10% with p < 0.05. H2 holds if no level among 50, 100 and 200 users is negative.
* Reported changes compare the median p95 of the 7 baseline runs with the median of the 7 intervention runs.

## 4. Results

Values are median p95 in milliseconds. Changes are relative to the baseline. "n/a" means all runs were identical, so the test has nothing to rank.

![p95 by load level](figures/p95_by_users.png)

### H1a: `/login`, login alone

| Users | Baseline | Intervention | Change | p |
|---|---|---|---|---|
| 1 | 56 | 56 | 0.0% | n/a |
| 10 | 74 | 92 | +24.3% | 0.0013 |
| 50 | 383 | 393 | +2.6% | 0.0405 |
| 100 | 551 | 864 | +56.8% | 0.0021 |
| 200 | 1,062 | 1,725 | +62.4% | 0.0021 |

### H1b: `/login`, mixed scenario

| Users | Baseline | Intervention | Change | p |
|---|---|---|---|---|
| 1 | 60 | 61 | +1.7% | 0.0447 |
| 10 | 83 | 83 | 0.0% | 0.2084 |
| 50 | 143 | 143 | 0.0% | 0.7377 |
| 100 | 218 | 556 | +155.0% | 0.0021 |
| 200 | 366 | 2,869 | +683.9% | 0.0021 |

### H2: `/orders`, mixed scenario

| Users | Baseline | Intervention | Change | p |
|---|---|---|---|---|
| 1 | 8 | 8 | 0.0% | 0.3914 |
| 10 | 17 | 17 | 0.0% | n/a |
| 50 | 76 | 76 | 0.0% | 0.4781 |
| 100 | 152 | 132 | -13.2% | 0.0020 |
| 200 | 302 | 135 | -55.3% | 0.0020 |

### Control: `/orders`, orders alone

| Users | Baseline | Intervention | Change | p |
|---|---|---|---|---|
| 1 | 8 | 8 | 0.0% | n/a |
| 10 | 18 | 17 | -5.6% | 0.1411 |
| 50 | 74 | 74 | 0.0% | 1.0000 |
| 100 | 139 | 138 | -0.7% | 0.9456 |
| 200 | 270 | 270 | 0.0% | 0.6937 |

The control shows no difference between builds at any level, as expected for identical code.

Levels 1 and 10 users are descriptive only, as stated in the plan. The automatic labels the analysis script prints for them are not meaningful.