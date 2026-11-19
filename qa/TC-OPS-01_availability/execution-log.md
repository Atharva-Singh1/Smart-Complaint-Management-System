# TC-OPS-01 - Availability (99.5% monthly)

| Field | Value |
|---|---|
| Test case | TC-OPS-01 |
| Requirement | SCMS-NF-002 |
| GitHub issue | #21 |
| Priority | High |
| Tester | Aum Padia |
| Date executed | NOT EXECUTED |

## Procedure (from STP)

Simulate 30-day monitor synthetic ping probes to health check endpoints.

## Expected result (from STP)

Unscheduled downtime <= 3.6 hours per month (99.5% uptime).

## Prepared assets (already in the repo)

- `GET /health/` returns HTTP 200 and `{"status": "ok", ...}`; HTTP 503 if the database
  check fails (`backend/core/health.py`, `backend/tests/test_health.py`).
- `.github/workflows/availability-smoke.yml` probes the URL in the `SCMS_HEALTHCHECK_URL`
  secret every 15 minutes.
- `deploy/monitoring/AVAILABILITY_MONITORING.md` describes the external monitor setup.

## To do

- [ ] Deploy to a real URL and set the `SCMS_HEALTHCHECK_URL` repository secret.
- [ ] Create an external monitor (e.g. UptimeRobot) on `https://<domain>/health/`,
      interval <= 5 minutes, alerts to the project operator and QA lead.
- [ ] After a full month, export the uptime report and record it below.

## Result

NOT EXECUTED

| Month | Monitored minutes | Unplanned downtime (min) | Availability (%) |
|---|---|---|---|
| | | | |

Availability = 100 x (monitored minutes - unplanned downtime) / monitored minutes. Target >= 99.5.

## Evidence

- Add: `evidence/uptime-report.*`

## Notes

This cannot be verified by code alone; a month of monitoring data is required.
