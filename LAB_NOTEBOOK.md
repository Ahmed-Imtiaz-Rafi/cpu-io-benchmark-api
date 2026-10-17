### 2026-10-17: `/login` Plan Validation
* **Setup:** JMeter 5.6.3 | 1 thread, 1,000 iter. | CSV SHA-256: `552af2311d76d5618fc563000a877ac0d15919a7a4232bef9160f5c5d1034837`
* **Config:** Variable Names (empty), Ignore Status (ticked), Assertion: `${expected}`
* **Result:** 1,000 samples, **0 errors**, ~58 ms avg.
    * 50 wrong-password rows passed as expected `401`s. Throwaway test confirmed assertion triggers correctly.
* **Fixes:** Cleared Variable Names (fixed header row sent as data); ticked Ignore Status (fixed wrong-passwords counted as errors).
* **Next:** Decide run parameters, then scale concurrency.