# TC-SEC-03 - Vulnerability scan (SQL injection / XSS)

| Field | Value |
|---|---|
| Test case | TC-SEC-03 |
| Requirement | SCMS-SR-003 |
| GitHub issue | #27 |
| Priority | High |
| Tester | Aum Padia |
| Date executed | 2026-11-19 (automated tests only) |
| Build / commit | branch `qa/issue-5-23-27-validation-accessibility`, commit 2690c85 |
| Environment | macOS (Apple silicon), Python 3.14.4, Django 5.2.18, pytest 9.2.0 |

## Procedure (from STP)

Run automated OWASP ZAP vulnerability suite on all public/staff endpoints.

## Expected result (from STP)

Zero High or Critical severity SQLi/XSS vulnerabilities identified.

## Automated checks (executed)

Command: `cd backend && python -m pytest` -> **103 passed in 2.33 s**.

- `backend/tests/test_sqli_xss_hardening.py` (14 tests): four SQLi payloads against login,
  public tracking and the triage status/ward filters (no authentication bypass, no data
  returned, table intact); oversized and reflected tracking IDs are handled and escaped.
- `backend/tests/test_input_security.py` (pre-existing): XSS payload rejection and output
  escaping; SQLi payload on tracking.

Code review notes: no raw SQL, `.extra()`, `|safe` or `mark_safe` in application code or
templates; the only `cursor()` use is a fixed `SELECT 1` in `core/health.py`.

## Result

PARTIAL - automated tests PASS. **The STP-required OWASP ZAP scan has NOT been run**, so the
requirement is not verified.

To complete:

- [ ] Run OWASP ZAP (baseline or active scan) against a local or staging instance, covering
      public pages (`/`, `/login/`, `/register/`, `/track/`) and staff pages (log in as staff:
      `/triage/`, `/triage/<id>/`, `/reports/complaints/`).
- [ ] Save the HTML/JSON report to `evidence/zap-report.html`.
- [ ] Record the number of High/Critical findings here. Target: 0.

## Evidence

- Add: `evidence/pytest-output.txt`, `evidence/zap-report.html`

## Defects

none so far

## Notes / limitations

Passing unit tests do not replace the ZAP scan. Do not mark issue #27 closed until the report
is attached.
