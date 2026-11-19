# TC-SCALE-01 - 500 concurrent authenticated sessions

| Field | Value |
|---|---|
| Test case | TC-SCALE-01 |
| Requirement | SCMS-NF-003 |
| GitHub issue | #22 |
| Priority | High |
| Tester | Aum Padia |
| Date executed | NOT EXECUTED |

## Procedure (STP phase 3: JMeter load runs)

Hold 500 concurrent authenticated sessions.

## Expected result

Stable throughput at 500 concurrent threads (STP exit criteria).

## Prepared test assets

`loadtests/locustfile.py`, `loadtests/seed_users.py` (500 synthetic users by default).

## How to run (staging / deployed instance)

    cd backend
    python manage.py shell -c "exec(open('../loadtests/seed_users.py').read())"
    cd ..
    mkdir -p results
    locust -f loadtests/locustfile.py --host <STAGING_URL> -u 500 -r 25 -t 10m \
      --headless --csv results/scale --html results/scale.html

## Result

NOT EXECUTED

| Metric | Value |
|---|---|
| Host / database tested | |
| Concurrent users | 500 |
| Failed logins/requests (%) | |
| 90th percentile (ms) | |

## Evidence

- Add: `evidence/scale_stats.csv`, `evidence/scale.html`

## Defects

- [DEF-001](../defects/DEF-001_sqlite-database-locked.md) - SQLite "database is locked" (HTTP 500)
  under concurrent logins in a local smoke test. Likely to block this test on SQLite.
