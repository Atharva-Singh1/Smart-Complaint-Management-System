# Requirements Traceability Matrix (RTM)

Source: SRS (`TEAM-8.pdf`), STP (`TEAM-8_Test_Plan.pdf`), issue table in `AGENTS.md`.
Status values are explained in `README.md`. Rows marked "not assessed" have not been
verified by QA yet; update them as each test case is executed.

Last updated: 2026-11-19

| Issue | Requirement | Test case | Summary | Status | Evidence |
|---:|---|---|---|---|---|
| 1 | SCMS-F-005 | TC-LODGE-01 | Complaint submission | not assessed | |
| 2 | SCMS-F-002 | TC-AUTH-02 | Secure authentication | not assessed | |
| 3 | SCMS-F-009 | TC-TRACK-01 | Public tracking with PII masking | not assessed | |
| 4 | SCMS-F-013 | TC-ADMIN-01 | Admin triage filtering | not assessed | |
| 5 | SCMS-F-008 | TC-LODGE-04 | Form validation and payload sanitization | PARTIAL | [log](TC-LODGE-04_form-validation/execution-log.md) |
| 6 | SCMS-F-001 | TC-AUTH-01 | Citizen registration | not assessed | |
| 7 | SCMS-F-003 | TC-AUTH-03 | Role-based access control | not assessed | |
| 8 | SCMS-F-004 | TC-AUTH-04 | Brute-force account lockout | not assessed | |
| 9 | SCMS-F-006 | TC-LODGE-02 | Evidence upload limits | not assessed | |
| 10 | SCMS-F-007 | TC-LODGE-03 | Unique immutable tracking ID | not assessed | |
| 11 | SCMS-F-010 | TC-TRACK-02 | Citizen dashboard | not assessed | |
| 12 | SCMS-F-011 | TC-TRACK-03 | Status audit trail | not assessed | |
| 13 | SCMS-F-012 | TC-TRACK-04 | Citizen follow-up while Under Review | not assessed | |
| 14 | SCMS-F-014 | TC-ADMIN-02 | Assignment/reassignment | not assessed | |
| 15 | SCMS-F-015 | TC-ADMIN-03 | Resolution note and proof | not assessed | |
| 16 | SCMS-F-016 | TC-ADMIN-04 | Rejection with justification | not assessed | |
| 17 | SCMS-F-017 | TC-NOTIF-01 | Asynchronous status notifications | not assessed | |
| 18 | SCMS-F-018 | TC-NOTIF-02 | Citizen rating and feedback | not assessed | |
| 19 | SCMS-F-019 | TC-REP-01 | CSV/PDF report export | not assessed | |
| 20 | SCMS-NF-001 | TC-PERF-01 | 90% of requests < 2 s at 200 users | NOT EXECUTED | [log](TC-PERF-01_performance/execution-log.md) |
| 21 | SCMS-NF-002 | TC-OPS-01 | 99.5% monthly availability | NOT EXECUTED | [log](TC-OPS-01_availability/execution-log.md) |
| 22 | SCMS-NF-003 | TC-SCALE-01 | 500 concurrent authenticated sessions | NOT EXECUTED | [log](TC-SCALE-01_scalability/execution-log.md), [DEF-001](defects/DEF-001_sqlite-database-locked.md) |
| 23 | SCMS-NF-004 | TC-UX-01 | WCAG 2.1 AA / mobile accessibility | PARTIAL | [log](TC-UX-01_accessibility/execution-log.md) |
| 24 | SCMS-NF-005 | TC-OPS-02 | Encrypted backup and restore < 30 min | not assessed | |
| 25 | SCMS-SR-001 | TC-SEC-01 | TLS 1.3 and HTTPS redirect | not assessed | |
| 26 | SCMS-SR-002 | TC-SEC-02 | Salted password hashing | not assessed | |
| 27 | SCMS-SR-003 | TC-SEC-03 | SQL injection / XSS protection | PARTIAL | [log](TC-SEC-03_sqli-xss/execution-log.md) |
| 28 | SCMS-SR-004 | TC-SEC-04 | Idle session timeout | not assessed | |
| 29 | SCMS-SR-005 | TC-SEC-05 | Magic-byte upload validation | not assessed | |
