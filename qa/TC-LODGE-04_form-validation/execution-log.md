# TC-LODGE-04 - Mandatory field and payload sanitization

| Field | Value |
|---|---|
| Test case | TC-LODGE-04 |
| Requirement | SCMS-F-008 |
| GitHub issue | #5 |
| Priority | Medium |
| Tester | Aum Padia |
| Date executed | 2026-11-19 (automated part) |
| Build / commit | branch `qa/issue-5-23-27-validation-accessibility`, commit 2690c85 |
| Environment | macOS (Apple silicon), Python 3.14.4, Django 5.2.18, pytest 9.2.0 |

## Procedure (from STP)

Submit empty form and inputs with `<script>` tags.

## Expected result (from STP)

Submission halts; UI marks mandatory fields red; XSS strings are sanitized.

## Automated checks (executed)

Command: `cd backend && python -m pytest` -> **103 passed in 3.33 s** (46 pre-existing, 57 new).

Relevant files:

- `backend/tests/test_form_validation.py` (37 tests): missing required fields, whitespace-only
  values, invalid category, over-long title, 8 unsafe payloads (script tag, unterminated tag,
  svg onload, spaced tag, HTML comment, `javascript:`, `vbscript:`, `data:text/html`) against
  the complaint form and the registration `full_name` field, plus ordinary text that must
  still be accepted.
- `backend/tests/test_input_security.py` (5 tests, pre-existing): script payloads in title,
  description and ward; escaping of stored legacy HTML on the public tracking page.

## Actual result

Empty/whitespace input and HTML/script payloads are rejected at form validation with an
error on the offending field. Payloads are **rejected, not sanitized**: the record is not
created. Stored legacy HTML is escaped on output.

## Result

PARTIAL - automated validation PASS. Not yet verified manually:

- [ ] Browser check: empty submission shows mandatory-field errors on the lodge form
      (STP expects fields "marked red"; current templates show an error list only, so
      confirm this wording with the team).
- [ ] Browser check: submitting `<script>alert(1)</script>` in title/description/ward shows
      the validation error and no alert fires. Save screenshots to `evidence/`.

## Evidence

- Add: `evidence/pytest-output.txt` (save the terminal output of the run above)

## Defects

none

## Notes / limitations

The STP says XSS strings are "sanitized"; the implementation rejects them. Confirm with the
team lead that rejection satisfies AC for SCMS-F-008.
