# SCMS availability monitoring

Issue: #21 / SCMS-NF-002 / TC-OPS-01

## Endpoint

Configure an external HTTPS monitor to request:

```
GET https://<production-domain>/health/
```

It must expect HTTP `200` and JSON field `status: "ok"`. A `503` means the
application cannot complete its database readiness check and should count as
downtime. The response contains no credentials or citizen data.

## Monitor configuration

Use the department-approved external monitoring provider (for example,
UptimeRobot, Better Uptime, or an institutional equivalent):

- Probe interval: five minutes or less.
- Location: external to the production deployment.
- Alert recipients: project operator and QA lead.
- Planned maintenance: document its start/end time separately; exclude it only
  when the SRS allows it.
- Retention: retain the monthly availability export or screenshot as TC-OPS-01
  evidence.

## Monthly calculation

```
availability (%) = 100 × (monitored minutes - unplanned downtime minutes) / monitored minutes
```

The target is at least 99.5% per month, excluding documented planned
maintenance. QA owns the monitoring report and verifies the target; this code
change alone cannot prove a future monthly availability percentage.
