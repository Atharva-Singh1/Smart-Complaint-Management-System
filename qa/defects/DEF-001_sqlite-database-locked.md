# DEF-001 - "database is locked" (HTTP 500) on concurrent logins with SQLite

| Field | Value |
|---|---|
| ID | DEF-001 |
| Found by | Local smoke test of `loadtests/locustfile.py` |
| Date | 2026-11-19 |
| Related | Issue #22 / SCMS-NF-003 / TC-SCALE-01 (also affects TC-PERF-01) |
| Proposed severity | S2 (Major) - confirm after reproducing |
| Status | OPEN - needs reproduction by QA |

## Environment

Django development server, default SQLite settings (`backend/config/settings.py`),
20 seeded users, Locust with 10 users for 15 seconds.

## Steps to reproduce

    cd backend
    python manage.py migrate
    LOADTEST_USERS=20 python manage.py shell -c "exec(open('../loadtests/seed_users.py').read())"
    python manage.py runserver
    # in a second terminal, from the repo root:
    LOADTEST_USERS=20 locust -f loadtests/locustfile.py --host http://127.0.0.1:8000 \
      -u 10 -r 5 -t 15s --headless

## Actual result

8 of 10 `POST /login/` requests returned HTTP 500. The server log shows
`django.db.utils.OperationalError: database is locked`, raised from
`accounts/services.py` (`user.save(update_fields=["failed_attempts", "locked_until"])`).

## Expected result

All logins succeed (HTTP 302) under concurrent load.

## Analysis

SQLite allows one writer at a time and every login writes to the user row (and the session).
Adding `"OPTIONS": {"transaction_mode": "IMMEDIATE", "timeout": 20}` to the SQLite database
settings removed the errors in the same smoke test (0 failures). This is only a mitigation
for development; whether SQLite can ever support 500 concurrent sessions is doubtful.

## Decision needed

The production database is an open decision in the SAD / `AGENTS.md`. Do not change it
without the team: raise this defect with the team lead and re-run TC-SCALE-01 on the
database chosen for deployment.
