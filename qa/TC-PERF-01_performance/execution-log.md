# TC-PERF-01 - Response time under 200 concurrent users

| Field | Value |
|---|---|
| Test case | TC-PERF-01 |
| Requirement | SCMS-NF-001 |
| GitHub issue | #20 |
| Priority | High |
| Tester | Aum Padia |
| Date executed | NOT EXECUTED |

## Procedure (STP phase 3: JMeter load runs)

Simulate 200 concurrent users against the application.

## Expected result

90th-percentile response time <= 2.0 s with stable throughput (SRS SCMS-NF-001).

## Prepared test assets

- `loadtests/locustfile.py` and `loadtests/seed_users.py` (Locust). The STP names **JMeter**;
  confirm with the team that Locust is acceptable, or port the scenario to JMeter.
- Scenario: login, dashboard, public tracking, lodge complaint, health check.

## How to run (staging / deployed instance, not a laptop dev server)

    cd backend
    python manage.py shell -c "exec(open('../loadtests/seed_users.py').read())"
    cd ..
    mkdir -p results
    locust -f loadtests/locustfile.py --host <STAGING_URL> -u 200 -r 20 -t 5m \
      --headless --csv results/perf --html results/perf.html

Read the 90% column of `results/perf_stats.csv` (milliseconds).

## Result

NOT EXECUTED

| Metric | Value |
|---|---|
| Host tested | |
| Users / duration | 200 / 5 min |
| 90th percentile (ms) | |
| Failures (%) | |
| Throughput (req/s) | |

## Evidence

- Add: `evidence/perf_stats.csv`, `evidence/perf.html`

## Notes

A 15-second, 10-user smoke run of the script against a local dev server worked, but it is
not acceptance evidence (see DEF-001 for what it revealed).
