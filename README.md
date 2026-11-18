# Smart Complaint Management System (SCMS)

## 1. Project overview

SCMS is a web application for civic complaint handling. Citizens can register, lodge complaints with evidence, obtain a tracking ID, and monitor progress. Department staff can triage, assign, update, resolve, or reject complaints while the system records an audit trail.

**Problem:** In manual civic grievance systems, citizens cannot reliably know whether their complaint was received, assigned, or resolved. SCMS adds transparency, accountability, controlled evidence upload, and role-based access.

**Stakeholders:** Citizens, department staff, administrators, and QA/test lead.

## 2. Scope demonstrated

1. Citizen registration, login, password protection, and account lockout.
2. Complaint lodging with category, ward, description, and evidence.
3. Unique complaint tracking ID.
4. Citizen dashboard and public privacy-safe tracking.
5. Staff triage, filtering, assignment, and status updates.
6. Resolution/rejection controls and append-only audit trail.
7. Staff/admin CSV and PDF report export.

## 3. User stories versus issues

A **user story** states a stakeholder need. A **GitHub issue** is the backlog/work-tracking record that contains that story, acceptance criteria, priority, test case, PR, and status.

We maintain the Product Backlog in GitHub Issues. Therefore, the user story appears in the **Description** section of each issue; the issue is not merely a bug ticket.

Example user story:

> As a citizen, I want to track a complaint using a tracking ID so that I can know its progress.

## 4. Functional user-story backlog

| Issue | User story | Where it is demonstrated |
|---:|---|---|
| #1 | Citizen submits a complaint with category, title, description, and ward. | Lodge complaint |
| #2 | User securely authenticates. | Login |
| #3 | Citizen publicly tracks a complaint while PII stays hidden. | Track complaint |
| #4 | Administrator filters triage cases. | Staff triage |
| #5 | Unsafe or incomplete form input is rejected. | Form validation |
| #6 | Citizen registers with valid details. | Register |
| #7 | User access is restricted by role. | Citizen/staff login |
| #8 | Account is protected against repeated failed logins. | Lockout controls |
| #9 | Citizen uploads permitted evidence. | Lodge complaint |
| #10 | Citizen receives an immutable unique tracking ID. | Submission result |
| #11 | Citizen views own complaints on a dashboard. | Dashboard |
| #12 | Operator views status-history audit trail. | Complaint timeline |
| #13 | Citizen adds follow-up while complaint is under review. | Backlog/shared UI |
| #14 | Staff assigns/reassigns a complaint. | Manage complaint |
| #15 | Staff records resolution note and proof. | Status update |
| #16 | Staff provides rejection reason and code. | Status update |
| #17 | Citizen receives status notifications. | Notification outbox |
| #18 | Citizen rates resolved complaint. | Backlog/shared UI |
| #19 | Administrator exports filtered CSV/PDF reports. | Reports page |

## 5. Non-functional and security requirements

These are quality requirements, not user stories.

| Issue | Requirement | Implementation / evidence |
|---:|---|---|
| #20 | 90% requests under 2 seconds at 200 users. | JMeter TC-PERF-01 |
| #21 | 99.5% monthly availability. | Health endpoint + external-monitor evidence |
| #22 | 500 concurrent authenticated sessions. | Stress test TC-SCALE-01 |
| #23 | WCAG 2.1 AA/mobile accessibility. | Responsive UI + Lighthouse TC-UX-01 |
| #24 | Encrypted daily backup, 365-day retention, restore under 30 minutes. | Backup scripts + TC-OPS-02 |
| #25 | TLS 1.3 and HTTPS redirect. | Nginx/Django deployment setup + TC-SEC-01 |
| #26 | Salted password hashing. | Argon2id automated test |
| #27 | Prevent SQL injection and XSS. | ORM, validation, escaping, OWASP evidence |
| #28 | Idle session timeout and stale-session revocation. | Middleware/session tests |
| #29 | Magic-byte evidence validation. | Upload tests |

## 6. Architecture

SCMS uses a **layered modular-monolith architecture**:

```text
Browser UI
  ↓
Django views, templates, forms and authorization
  ↓
Accounts, complaint, tracking, workflow and reporting modules
  ↓
Django ORM
  ↓
Relational database
```

### Why modular monolith?

- Appropriate for a student project and current scope.
- Simpler deployment and debugging than microservices.
- Modules still separate authentication, complaint workflow, reports, notifications, and security.
- The system can be decomposed later if scale requires it.

## 7. Main components

| Component | Responsibility |
|---|---|
| `accounts` | User model, registration, authentication, roles, lockout, sessions |
| `core` | Complaints, tracking, triage, validation, reports, audit trail |
| Django templates | Citizen and staff UI |
| Django ORM | Database persistence and parameterized access |
| Notification outbox | Durable assignment/rejection/status notification records |
| Nginx/Django deployment files | HTTPS/TLS-ready deployment configuration |

## 8. Key data entities

| Entity | Purpose |
|---|---|
| User | Name, email, phone, role, lockout data |
| Complaint | Tracking ID, citizen, issue details, ward, status, assignee |
| Evidence | Complaint attachment metadata |
| AuditLog | Actor, old/new status, timestamp, note; append-only |
| ResolutionProof | Proof image for a resolution |
| StatusNotification / email outboxes | Durable notification jobs |

## 9. Complaint lifecycle

```text
Submitted → Assigned → Under Review → Resolved
                              └──────→ Rejected
```

Every status change creates an audit record. Resolution requires a detailed note and proof image. Rejection requires a reason and justification code.

## 10. Security controls

- Argon2id salted password hashing.
- Citizen, staff, and administrator RBAC.
- Lockout after five failed login attempts.
- 30-minute idle-session timeout and session revocation after a role change.
- Secure/HttpOnly/SameSite deployment cookie settings.
- Evidence count, size, extension, and magic-byte checks.
- Input validation against HTML/script-style payloads.
- Django template escaping and ORM parameterized queries.
- PII masking in public tracking.
- Append-only audit records.
- TLS-ready reverse-proxy configuration.

## 11. Requirement traceability and testing

Traceability chain:

```text
SRS requirement → GitHub Issue → implementation/PR → automated test → test-plan case → QA evidence
```

Test levels:

- **Unit:** forms, validators, and model rules.
- **Integration:** login, lodging, tracking, assignment, and reporting.
- **Security:** password hashing, lockout, sessions, malicious file/input tests.
- **System/UAT:** end-to-end citizen/staff workflow.
- **Non-functional:** JMeter, uptime monitoring, backup restore, OWASP ZAP, Lighthouse.

## 12. Git workflow

```text
Issue → feature branch → commit → pull request → automated checks → review → merge
```

Separate PRs were used for auth/RBAC, complaint lodging, tracking/audit, triage, reports, TLS, monitoring, backups, and input security. This provides individual contribution evidence and avoids direct changes to `main`.

## 13. Local presentation run instructions

From the `backend` folder:

```powershell
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open: `http://127.0.0.1:8000/`

### Demo credentials

All demo accounts use password: `DemoPass2026!`

| Role | Login |
|---|---|
| Citizen | `citizen@scms.local` |
| Department staff | `staff@scms.local` |
| Administrator | `admin@scms.local` |

## 14. Suggested presentation flow

1. Explain problem, stakeholders, and project objective.
2. Show landing page, registration/login.
3. Show complaint lodging and generated tracking ID.
4. Show public tracking and explain PII masking.
5. Show citizen dashboard.
6. Log in as staff and show triage, filters, assignment, and status update.
7. Show audit history.
8. Show report export.
9. Summarize security controls and traceability.

## 15. Common software-engineering viva answers

### What is the difference between a user story and acceptance criteria?

A user story describes the stakeholder goal. Acceptance criteria are objective conditions used to decide whether the story is complete.

### Why RBAC?

RBAC implements least privilege: citizens cannot perform staff actions, and staff/admin actions are protected.

### Why is the audit trail append-only?

Complaint decisions need accountability. An editable audit log would not reliably prove who changed a status, when, or why.

### Why check both evidence extension and magic bytes?

Extensions and browser MIME types can be forged. Magic bytes check the actual beginning of the file, helping reject a renamed executable.

### Why use Django ORM?

Django ORM provides a maintainable data-access layer and parameterized queries for normal database access, reducing SQL-injection risk.

### Functional versus non-functional requirements?

Functional requirements describe what the system does: submit, track, assign, resolve. Non-functional requirements describe quality targets: availability, speed, security, accessibility, and backup retention.

### Why can an issue remain open after code is merged?

Some acceptance criteria need real operational evidence: 200/500-user load tests, monthly uptime, OWASP scan, deployed TLS certificate, or a staging restore. Code alone cannot prove those targets.

## 16. Current limitations and next steps

- Complete follow-up-comment and feedback/rating UI.
- Run JMeter performance and concurrency tests.
- Configure external uptime monitor and retain monthly evidence.
- Deploy using a real domain and valid TLS certificate.
- Execute and record staging backup/restore verification.
- Run OWASP ZAP and Lighthouse scans.
- Move from local demo database to the team-approved production database during deployment.

## 17. Team responsibilities

- **Backend:** authentication, authorization, workflow, validation, audit, reporting, security, monitoring and deployment configuration.
- **Frontend:** citizen forms, dashboards, public tracking, feedback, responsiveness and accessibility.
- **QA/Test:** RTM, execution logs, security/performance/accessibility evidence, backup/availability validation, defect reports.

