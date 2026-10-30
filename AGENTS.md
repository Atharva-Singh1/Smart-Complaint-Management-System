# Agent Context: Smart Complaint Management System

This file gives repository-wide context and operating instructions to Codex and other coding agents. Apply it to all issues in this repository unless a more specific, higher-priority instruction applies.

## Project identity and current state

- Repository: `Atharva-Singh1/Smart-Complaint-Management-System`.
- Product: Smart Complaint Management System (SCMS), a civic complaint lodging, triage, tracking, resolution, and feedback platform.
- Current repository root contains `README.md`, `TEAM-8.pdf` (SRS v2.0), `TEAM-8_Test_Plan.pdf` (STP v1.0), and `SCMS_SAD_Team8.pdf` (Software Architecture and Design Specification v1.0, Draft, dated 04-10-2026).
- The repository now contains an initial Django 5.2.18 application under `backend/`, plus GitHub Actions CI and pytest tests. Inspect the live checkout before assuming current coverage or completeness.
- Checked-in local development settings use SQLite. Confirm the intended target/deployment database with the team before changing it.
- As of 2026-10-31, 27 of issues #1–#29 are open and #9–#10 are closed. Treat this as a dated snapshot; check GitHub for current status. Open issues may have partial or merged work, and a merged PR alone does not prove every acceptance criterion is met.
- Merged implementation PRs: #31 authentication/roles/lockout foundation; #32 complaint lodging/evidence limits/tracking IDs; #33 public tracking/citizen dashboard/audit history; #34 staff triage/assignment/status updates. Verify CI and acceptance evidence before closing issues or claiming requirements are done.
- Scope gaps to verify: #4 requires department, urgency, status, and SLA filters; the #34 change visibly filters status and ward. #15 requires resolution proof as well as notes; #16 requires a justification code, not just a reason. Confirm these criteria before closure.

## Source-of-truth documents

Use the documents in this order for their respective concerns:

1. `TEAM-8.pdf` is authoritative for requirements and acceptance targets.
2. `TEAM-8_Test_Plan.pdf` is authoritative for test IDs, test procedures, test phases, test data, and exit criteria.
3. `SCMS_SAD_Team8.pdf` is the current architecture/design proposal. It is marked Draft; follow its settled architectural direction while surfacing its open decisions and inconsistencies instead of silently treating them as approved.
4. The selected GitHub issue defines the scope for a particular change. Preserve its requirement ID and test traceability.

If these documents conflict, identify the exact requirement/section and propose a resolution. Do not silently change the SRS baseline or invent approval.

## Architecture context from the SAD

- Architecture pattern: layered, multi-tier application implemented as a **modular monolith** exposing a REST API. Microservices were rejected as unnecessary complexity for the expected scale and student team.
- Main layers: client, presentation, application backend, relational database, and external/supporting services.
- Main components: `UserPortal`, `AdminDashboard`, `SecurityMiddleware`, `AuthModule`, `SessionManager`, `SecurityEngine`, `ComplaintModule`, `TrackingModule`, `WorkflowModule`, `FeedbackModule`, `ReportingService`, `ValidatorService`, `AuditLogger`, `FileUploadService`, and `NotificationQueue`.
- Keep complaint state changes and audit writes transactionally consistent in the relational database. Dispatch notifications asynchronously so gateway failures do not roll back complaint commits; failed notifications should be retryable/dead-lettered.
- Enforce authorization centrally, sanitize/validate inputs, mask personal information in public tracking, and keep audit history append-only.
- Evidence storage is S3-compatible (AWS S3 or MinIO); notification integrations are SMS and email; geocoding uses OpenStreetMap Nominatim. Use mocks/sandboxes in tests.

### Decisions still open in the SAD

Do not choose these on behalf of the team:

- Backend framework: the implementation has selected Django 5.2.18. Treat the SAD's Django/Flask/Laravel alternatives as superseded unless the team explicitly revises this decision.
- Database: checked-in local settings use SQLite. The intended deployment database remains to be confirmed; do not infer a production choice from comments.
- Session strategy: the application currently uses Django's session/authentication framework. Confirm production session storage and security settings before introducing JWT or Redis.
- MFA appears in parts of the SRS/SAD overview but has no corresponding functional requirement.
- Lifecycle states `Under Review` and `Appealed` are not fully specified as transitions/requirements.
- Proposed API routes/status codes need implementation review and OpenAPI documentation.
- Lifecycle state, ER/data model, and deployment diagrams are still missing from the SAD.
- Public endpoint rate limiting is recommended by the SAD but is not an SRS requirement.

If work depends on an open decision, stop before locking in the design. State the decision needed and continue any independent work that does not depend on it.

## Quality, security, and privacy constraints

- Preserve requirement-to-component-to-test traceability.
- Use parameterized ORM/database operations. Do not construct SQL from untrusted input.
- Never log passwords, tokens, or unmasked citizen PII. Never commit secrets, credentials, real complaint data, or production keys.
- Require TLS 1.3; redirect HTTP to HTTPS. Use secure, HttpOnly, SameSite cookies if cookie sessions are selected.
- Store passwords with salted Argon2id or bcrypt at the SRS cost factor; enforce the SRS lockout threshold and 30-minute idle session timeout. Resolve the discrepancy between issue #8's sixth-attempt wording and the SRS/test plan before treating lockout behavior as accepted.
- Validate evidence by content/magic bytes, allowing only JPEG, PNG, and PDF; enforce at most five files and 5 MB per file.
- Public tracking must mask personal data. RBAC must deny cross-role access (HTTP 403).
- Maintain an append-only audit trail with previous/new status, actor ID, and timestamp.
- Do not claim performance, availability, security-scan, accessibility, or backup/restore targets are met without recorded evidence from the specified test.

## Issue workflow for agents

1. Work only on the issue explicitly selected by the user. Read its full body and acceptance criteria, then inspect the related SRS, SAD, STP, and current code.
2. Keep the change limited to that issue. Do not bundle unrelated requirements or close issues unless asked and verified.
3. Use the existing architecture and conventions once they exist. Do not introduce a parallel framework, datastore, or pattern.
4. Add/update focused tests with implementation. Feature developers own unit and integration tests; QA coordinates acceptance, end-to-end, security, performance, accessibility, and RTM evidence.
5. Use synthetic test data and local mocks for external services.
6. In the pull request, include the issue number, requirement ID, test case ID, behavior changed, checks actually run, and any unresolved limitation.
7. Do not assign issues, change project settings, alter the requirements baseline, or make deployment/release changes unless the user explicitly asks.

## Definition of done

- All issue acceptance criteria are implemented and verified.
- Relevant automated tests pass and their commands/results are reported accurately.
- Applicable manual/integration/non-functional evidence is recorded in the test artifacts and RTM.
- The change is reviewed and merged through the repository workflow.
- No unmasked PII, secrets, or unexplained architecture decisions are introduced.

## Requirement-to-issue traceability

| Issue | Requirement | Test case | Requirement summary |
|---:|---|---|---|
| #1 | SCMS-F-005 | TC-LODGE-01 | Complaint submission |
| #2 | SCMS-F-002 | TC-AUTH-02 | Secure authentication |
| #3 | SCMS-F-009 | TC-TRACK-01 | Public complaint tracking with PII masking |
| #4 | SCMS-F-013 | TC-ADMIN-01 | Admin triage filtering |
| #5 | SCMS-F-008 | TC-LODGE-04 | Form validation and payload sanitization |
| #6 | SCMS-F-001 | TC-AUTH-01 | Citizen registration |
| #7 | SCMS-F-003 | TC-AUTH-03 | Role-based access control |
| #8 | SCMS-F-004 | TC-AUTH-04 | Brute-force account lockout |
| #9 | SCMS-F-006 | TC-LODGE-02 | Evidence upload count/size/type limits |
| #10 | SCMS-F-007 | TC-LODGE-03 | Unique immutable tracking ID |
| #11 | SCMS-F-010 | TC-TRACK-02 | Citizen complaint dashboard |
| #12 | SCMS-F-011 | TC-TRACK-03 | Complaint status audit trail |
| #13 | SCMS-F-012 | TC-TRACK-04 | Citizen comments/evidence while Under Review |
| #14 | SCMS-F-014 | TC-ADMIN-02 | Department assignment/reassignment |
| #15 | SCMS-F-015 | TC-ADMIN-03 | Resolution note and proof validation |
| #16 | SCMS-F-016 | TC-ADMIN-04 | Rejection with justification |
| #17 | SCMS-F-017 | TC-NOTIF-01 | Asynchronous status notifications |
| #18 | SCMS-F-018 | TC-NOTIF-02 | Citizen rating and feedback |
| #19 | SCMS-F-019 | TC-REP-01 | CSV/PDF report export |
| #20 | SCMS-NF-001 | TC-PERF-01 | Response time under 200 concurrent users |
| #21 | SCMS-NF-002 | TC-OPS-01 | 99.5% monthly availability |
| #22 | SCMS-NF-003 | TC-SCALE-01 | 500 concurrent authenticated sessions |
| #23 | SCMS-NF-004 | TC-UX-01 | WCAG 2.1 AA/mobile accessibility |
| #24 | SCMS-NF-005 | TC-OPS-02 | Daily encrypted backup and restore |
| #25 | SCMS-SR-001 | TC-SEC-01 | TLS 1.3 transport security |
| #26 | SCMS-SR-002 | TC-SEC-02 | Salted password hashing |
| #27 | SCMS-SR-003 | TC-SEC-03 | SQL injection/XSS protection |
| #28 | SCMS-SR-004 | TC-SEC-04 | Idle session timeout/token rotation |
| #29 | SCMS-SR-005 | TC-SEC-05 | Magic-byte upload validation |

## Test phases

- Phase 1: smoke tests and static analysis.
- Phase 2: functional/integration suites for authentication, lodging, triage, and notifications.
- Phase 3: security and non-functional tests (OWASP, JMeter, accessibility, operations).
- Phase 4: UAT, regression, and full RTM verification.

The STP exit criteria include all high-priority functional requirements passing, no open critical/major defects or high/critical security vulnerabilities, performance/load targets verified, and complete bidirectional RTM coverage.
