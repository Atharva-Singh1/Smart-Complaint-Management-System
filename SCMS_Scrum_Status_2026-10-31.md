# SCMS Scrum Status and Sprint Preparation

**Snapshot date:** 31 October 2026  
**Repository:** [Atharva-Singh1/Smart-Complaint-Management-System](https://github.com/Atharva-Singh1/Smart-Complaint-Management-System)  
**Purpose:** Working Scrum Master note. This is a local planning draft, not a committed sprint or an assignment in GitHub.

## Current repository state

- Latest implementation merge is PR #34 (30 October 2026). The most recent commit is [feee519](https://github.com/Atharva-Singh1/Smart-Complaint-Management-System/commit/feee5193243c86f030789edd0b9236ffc69ef377), which added this status note and the refreshed `AGENTS.md`.
- Merged implementation PRs:
  - [#31 Authentication, roles, and account lockout foundation](https://github.com/Atharva-Singh1/Smart-Complaint-Management-System/pull/31)
  - [#32 Complaint lodging, evidence limits, and tracking IDs](https://github.com/Atharva-Singh1/Smart-Complaint-Management-System/pull/32)
  - [#33 Public tracking, citizen dashboard, and audit history](https://github.com/Atharva-Singh1/Smart-Complaint-Management-System/pull/33)
  - [#34 Staff triage, assignment, and status updates](https://github.com/Atharva-Singh1/Smart-Complaint-Management-System/pull/34)
- CI run results observed: PR #32 [run 2](https://github.com/Atharva-Singh1/Smart-Complaint-Management-System/actions/runs/41084339949), PR #33 [run 4](https://github.com/Atharva-Singh1/Smart-Complaint-Management-System/actions/runs/41090873604), and PR #34 [run 6](https://github.com/Atharva-Singh1/Smart-Complaint-Management-System/actions/runs/41104139340) completed successfully. This is evidence for automated checks in those runs, not full manual or non-functional acceptance.
- Issue snapshot: 27 open (#1–#29 except #9 and #10); #9 and #10 are closed. The open issues checked have no assignees. Recheck GitHub before acting on this snapshot.
- The application now has a Django 5.2.18 backend. Local development settings use SQLite. Confirm production database and deployment choices with the team before changing them.

## Issue reconciliation

### Merged implementation is visible; acceptance still needs verification

| Issue(s) | Test case(s) | Current evidence / next check |
|---|---|---|
| #1 Complaint submission | TC-LODGE-01 | PR #32 added lodging. Verify required fields, persisted ward/category/time, and dashboard listing against criteria. |
| #2, #6, #7 Authentication, registration, RBAC | TC-AUTH-02, TC-AUTH-01, TC-AUTH-03 | PR #31 added the auth foundation. Check CI/test coverage and verify each criterion, including denied cross-role access. |
| #8 Account lockout | TC-AUTH-04 | PR #31 added lockout behavior. Resolve the issue/SRS/Test Plan threshold wording before accepting it; confirm threshold, duration, and email behavior. |
| #3, #11, #12 Tracking, citizen dashboard, audit history | TC-TRACK-01/02/03 | PR #33 added these flows. Verify PII masking, status/date/department fields, ownership filtering, officer notes/timestamps, and audit details. |
| #14 Assignment/reassignment | TC-ADMIN-02 | PR #34 added staff assignment. Verify department restrictions, reassignment, and audit evidence against the issue and test case. |

### Gaps visible in merged code; refine or implement before closure

- **#4 Admin triage filters (TC-ADMIN-01):** issue requires department, urgency, status, and SLA filters. PR #34's reviewed change visibly filters status and ward. Confirm expected ward behavior and implement/test remaining required filters.
- **#15 Resolution notes and proof (TC-ADMIN-03):** status flow accepts resolution notes; verify proof upload/content requirements are implemented and tested.
- **#16 Complaint rejection (TC-ADMIN-04):** status flow accepts a rejection note; issue requires a justification code. Confirm the code is captured and persisted.

### No matching merged implementation identified in PRs #31–#34

Keep these in the backlog and prioritize from SRS/STP and dependencies: #5 form sanitization; #13 citizen follow-up; #17 notifications; #18 feedback; #19 reporting; #20–#24 non-functional/operations; #25–#29 security requirements. This classification only covers the four implementation PRs reviewed; inspect current code before planning them.

Do not close an issue solely because its feature appears in a merged PR. The issue Definition of Done requires criteria verification, relevant tests, and review. Record results against the linked STP case and RTM.

## Draft sprint goal

**Goal:** Complete and verify the core citizen-to-staff complaint workflow, and make the issue tracker match what is actually accepted.

Candidate work, to confirm with the team when available:

1. Verify the merged auth, lodging, tracking, audit, and assignment flows against their linked STP cases.
2. Resolve the #8 lockout-threshold discrepancy against the approved SRS/Test Plan and update the issue only if the baseline requires it.
3. Complete the missing #4 triage filters, #15 resolution proof, and #16 rejection code requirements, with focused tests.
4. Close only issues whose acceptance evidence and Definition of Done are met; link the PR and test evidence in each issue.

No sprint dates, estimates, or final scope are set here because team availability and QA/frontend progress are not confirmed.

## Provisional work split by Test Plan role

These are planning suggestions, not GitHub assignments. Rebalance after teammates report availability and current work.

| Role | Proposed focus |
|---|---|
| Backend Developer — Atharva D. Kulkarni | Implement server-side gaps in #4, #15, and #16 once the requirements are confirmed; add focused backend tests. |
| Frontend Developer — Atharva Gouni | Verify and complete user-facing triage/status/resolution/rejection forms with backend contracts; check keyboard/mobile behavior for affected screens. |
| QA/Test Lead — Aum Padia | Execute the relevant auth, lodging, tracking, and admin STP cases; record pass/fail evidence and update RTM; clarify #8 threshold against baseline docs. |
| Team Lead / Scrum Master — Atharva Singh | Keep the board current, confirm sprint goal and capacity, remove blockers, link issues↔PRs↔tests, facilitate review, and avoid closing requirements without evidence. |

## Scrum Master actions while teammates are unavailable

- Keep the sprint proposal provisional; do not infer teammate capacity or assign issues on their behalf.
- Prepare a concise asynchronous check-in asking each teammate for current issue, progress, blocker, and availability.
- Refine acceptance criteria and dependencies for #4, #8, #15, and #16 using SRS, SAD, and STP.
- Keep the current merged/open mismatch visible and avoid bulk-closing issues.
- When QA/frontend respond, update the plan and assign work in GitHub based on actual availability.

### Async check-in draft

> Quick sprint check-in when you’re available: which issue(s) are you currently working on, what is complete so far, what is blocked, and when do you expect to be available? QA: please include the STP case IDs and any pass/fail evidence. Frontend: please include the screens/flows completed and any backend/API dependency. I’m keeping the next sprint scope provisional until I hear back.

## Access / publication note

The status note and refreshed `AGENTS.md` are committed on `main` in [commit feee519](https://github.com/Atharva-Singh1/Smart-Complaint-Management-System/commit/feee5193243c86f030789edd0b9236ffc69ef377). This document remains a planning draft: no sprint dates, estimates, final scope, issue assignments, or issue-state changes were committed.
