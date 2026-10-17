# cpu-io-benchmark-api

A Spring Boot REST API built to study how CPU-bound and I/O-bound workloads behave differently under concurrent load, and whether separating CPU-bound work onto its own thread pool reduces degradation.

This repository holds the test application, the fixed dataset, and everything needed to reproduce the experiment's starting conditions. The load-test plans and results will be added as the study progresses.

## Research question

How does a Spring Boot REST API perform under CPU-bound versus I/O-bound workloads as concurrent load increases, and can thread pool separation (async processing) reduce CPU-bound degradation without hurting I/O-bound performance?

- **H1:** Thread pool separation measurably reduces performance degradation on the CPU-bound endpoint under load.
- **H2:** The same change has no meaningful negative effect on the I/O-bound endpoint.

## Status

| Stage | State |
|---|---|
| Baseline (synchronous) API | Done |
| Fixed dataset, dump and credentials file | Done, checksums below |
| Baseline load tests | Not started |
| Thread pool separation (intervention) | Not started |
| Intervention load tests and analysis | Not started |

## Stack and pinned versions

Everything that could affect the measurements is pinned. Do not change these between the baseline and intervention runs.

| Component | Version                                                  |
|---|----------------------------------------------------------|
| Java | 25                                                       |
| Spring Boot | 4.1.1                                                    |
| Embedded Tomcat | 11.0.26 (default request pool of 200 threads, unchanged) |
| Logback | 1.6.5                                                    |
| Jackson | 3.1.7                                                    |
| MySQL Connector/J | 26.7.0                                                   |
| Datafaker | 2.7.0                                                    |
| spring-security-crypto | managed by Spring Boot (BCrypt, strength 10)             |
| MySQL server | 8.0.46                                                   |

Logback, Jackson, Tomcat and the MySQL connector are overridden in `pom.xml` to pick up security fixes that Spring Boot 4.1.1 does not yet manage.

## Endpoints

There are exactly two endpoints. They are independent on purpose, so each one exercises a single workload type.

**`POST /login`** (CPU-bound). Verifies a password with BCrypt.

```json
{ "username": "user0001", "password": "..." }
```

- `200 OK` with `User logged in successfully` for valid credentials
- `401 Unauthorized` with `Invalid credentials` for a wrong password or an unknown username

An unknown username returns before BCrypt runs, which is much cheaper. Test traffic therefore uses real usernames with wrong passwords for the invalid cases.

**`GET /users/{userId}/orders`** (I/O-bound). Returns all orders for a user, each with its product, using a single fetch-join query over unindexed tables.

- `200 OK` with a JSON list of orders (`id`, `product`, `orderDate`, `orderStatus`). The user is assumed to exist, and an unknown id returns an empty list.

## The dataset

The data is synthetic and generated with a fixed random seed (`42`), so the plaintext content is identical on every run. Only the BCrypt salts, and therefore the hash strings, differ between seeder runs. For that reason the database dump is the canonical copy.

| Table | Rows | Notes |
|---|---|---|
| `users` | 1,000 | unique `username` and `email`, BCrypt hash at strength 10 |
| `products` | 150 | unique `name` |
| `orders` | 40,000 | exactly 40 per user, no user orders the same product twice |

Design choices that matter for the experiment:

- `orders` has **no secondary indexes and no foreign key constraints**, only its primary key. MySQL creates indexes automatically for foreign keys, so the constraints are disabled in the entity mapping on purpose. This keeps the join non-trivial.
- Every user has the same number of orders, so every `/users/{userId}/orders` response is the same size.
- Order dates fall in 2026 and user signup dates in 2025. Both are drawn from the seeded random generator.
- BCrypt strength is 10, about 54.5 ms per verification on the development machine. Each +1 doubles the cost.

### Credentials file

`db/seeded-users.csv` has a header row and 1,000 data rows, one per user, for use by Postman and JMeter.

| Column | Meaning                                                                                        |
|---|------------------------------------------------------------------------------------------------|
| `username` | an existing user                                                                               |
| `email` | that user's email                                                                              |
| `password` | the password to send (950 correct, 50 deliberately wrong, 5%)                                  |
| `expected` | the status the endpoint should return (200 for success and 401 for failure, rows are shuffled) |

In JMeter, leave "Variable Names" empty in the CSV Data Set Config so the header row is used for the column names.

### Checksums

SHA-256, verified from a fresh clone:

```
8569431a55f23e7f4880a1e32f242357f051e921929a5252951dd68aba2f6df9  db/cpu_io_benchmark_db.sql
552af2311d76d5618fc563000a877ac0d15919a7a4232bef9160f5c5d1034837  db/seeded-users.csv
```

Check yours with `sha256sum db/*`. A `.gitattributes` rule stores both files byte-for-byte, so line endings are not converted on checkout.

## Setup

**Prerequisites:** JDK 25, MySQL 8.0, and Git. Maven is included through the wrapper (`mvnw`).

1. Create an empty database:
   ```
   mysql -u root -p -e "CREATE DATABASE cpu_io_benchmark_db;"
   ```
2. Copy `src/main/resources/application.properties.example` to `application.properties` in the same folder and fill in your MySQL username and password. The real file is git-ignored.

3. Load the data, using **one** of these:

   **Option A: restore the dump (recommended).** This gives you the exact dataset the experiment used.
   ```
   mysql -u root -p cpu_io_benchmark_db -e "source db/cpu_io_benchmark_db.sql"
   ```

   **Option B: run the seeder.** Set `app.seed.enabled=true`, start the application from the project root, then set it back to `false`. The seeder refuses to run if the tables already have rows, so empty them first with `TRUNCATE`. It writes the CSV relative to the working directory, which is why it must run from the project root. Expect about a minute of BCrypt hashing. This produces equivalent data, not byte-identical hashes.

4. Start the application:
   ```
   ./mvnw spring-boot:run
   ```

For real measurements, build the jar and launch it with `java -jar` instead. Do not benchmark from an IDE run configuration, since IDEs can add JVM flags that change performance.

## Quick check

```
curl -X POST http://localhost:8080/login -H "Content-Type: application/json" -d '{"username":"<user from the CSV>","password":"<password from the CSV>"}'
curl http://localhost:8080/users/1/orders
```

## Experimental design (summary)

- **Baseline:** both endpoints synchronous, one shared Tomcat pool of 200 threads.
- **Intervention:** the Tomcat pool stays at 200. A separate 8-thread executor, matching the 8 physical cores of the test CPU (16 logical processors with SMT), handles the BCrypt work through `@Async`. The size is set explicitly instead of reading `availableProcessors()`, which would report 16. Total thread capacity is not meaningfully increased.
- **Load:** 1, 10, 50, 100 and 200 concurrent users, 3 to 5 runs per condition, warm-up excluded, 30-second timeout.
- **Machine:** the whole experiment runs on a single PC (see below). The API, MySQL, JMeter (command-line mode) and the monitoring script share it, so absolute numbers are specific to this setup. Baseline and intervention runs use the identical setup, so the comparison between them stays valid.
- **Scenarios:** each endpoint on its own, plus a mixed scenario with a fixed request ratio (currently planned at 1 login to 15 order requests).
- **Metrics:** response time (average, p95, p99), throughput, error rate, CPU and memory.
- **Analysis:** Mann-Whitney U per concurrency level, p < 0.05, with a 15 to 20% change treated as practically significant.

## Test environment

| Item | Value |
|---|---|
| OS | Windows 11 |
| CPU | AMD Ryzen 5700X (8 cores, 16 threads) |
| RAM | 16 GB DDR4-3200 |
| Storage | 512 GB Gen4 NVMe SSD |
| GPU | Intel Arc A580 (not used by the experiment) |

## Known limitations

- A single framework and a single intervention, tested on two representative endpoints.
- JVM heap and garbage collector settings are left at their defaults.
- Each order has one product, with no cart or line items.
- The orders endpoint does not check that the user exists.
- The load generator, the database and the API share one machine, so they compete for CPU. Results compare the two architectures on this setup and are not absolute capacity figures.
- Traffic goes over the loopback interface and the dataset is small enough to sit in memory, so the I/O-bound endpoint has very little real network or disk latency.
- The data is synthetic.

## Repository layout

```
db/                        dump and credentials file (fixed dataset)
src/main/java/...          controllers, services, repositories, models, seeder
src/main/resources/        application.properties.example
```

## License

See `LICENSE`.