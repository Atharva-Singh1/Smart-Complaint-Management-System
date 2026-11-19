# TC-UX-01 - Usability / accessibility (WCAG 2.1 AA, mobile)

| Field | Value |
|---|---|
| Test case | TC-UX-01 |
| Requirement | SCMS-NF-004 |
| GitHub issue | #23 |
| Priority | Medium |
| Tester | Aum Padia |
| Date executed | 2026-11-19 (static checks only) |
| Build / commit | branch `qa/issue-5-23-27-validation-accessibility`, commit 2690c85 |
| Environment | macOS (Apple silicon), Python 3.14.4, pytest 9.2.0 |

## Procedure (from STP)

Run Google Lighthouse and screen-reader audit across citizen forms on desktop/mobile.

## Expected result (from STP)

Lighthouse Accessibility score >= 90; full keyboard navigation enabled.

## Automated checks (executed)

`backend/tests/test_accessibility_markup.py` (6 tests) -> passed in the 103-test run.
It checks, for the public pages (home, login, register, track): `lang="en"`, viewport tag,
skip link and `main` landmark, and an `h1`. On those pages plus lodge, triage, manage-complaint
and reports it also checks that every visible input/select/textarea has a `<label for>`
pointing at its `id`.

Changes made for this issue: labels linked to inputs, skip-to-content link, visible focus
outline, `nav` label, live region for messages.

## Result

PARTIAL - static markup checks PASS. **Lighthouse and keyboard/screen-reader testing NOT run.**

To complete (record the score for each page, desktop and mobile):

| Page | Desktop score | Mobile score | Keyboard-only OK? |
|---|---|---|---|
| Home `/` | | | |
| Login `/login/` | | | |
| Register `/register/` | | | |
| Track `/track/` | | | |
| Lodge `/complaints/new/` (logged in) | | | |
| Dashboard `/dashboard/` (logged in) | | | |

- [ ] Chrome DevTools -> Lighthouse -> Accessibility, once on Desktop and once on Mobile.
- [ ] Tab through each form without a mouse: every control reachable, focus visible.
- [ ] Screen reader pass (VoiceOver: Cmd+F5) on the lodge form.
- [ ] Manually check colour contrast flagged by Lighthouse (not verified by the static tests).
- [ ] Save reports/screenshots to `evidence/`.

## Evidence

- Add: `evidence/lighthouse-*.html` or screenshots

## Defects

none so far

## Notes / limitations

Target is a score >= 90; fix and re-run for any page below it.

## Lighthouse results (executed 2026-11-19)

| Page | Desktop score | Mobile score |
|---|---|---|
| Lodge `/complaints/new/` (logged in) | 100 | 100 |

Screenshots: `evidence/lighthouse-lodge-desktop.png`, `evidence/lighthouse-lodge-mobile.png`.
Other pages, keyboard-only navigation and the screen-reader pass have not been run yet, so the
result stays PARTIAL.
