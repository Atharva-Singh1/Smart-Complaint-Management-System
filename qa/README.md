# QA evidence

Test execution evidence for SCMS, kept in the repository so every requirement can be
traced: SRS requirement -> GitHub issue -> automated test -> test-plan case -> evidence.

Owner: QA / Test Lead (Aum Padia). Source documents: `TEAM-8.pdf` (SRS) and
`TEAM-8_Test_Plan.pdf` (STP, section 8 "Test Deliverables").

## Layout

    qa/
      README.md                    this file
      RTM.md                       Requirements Traceability Matrix
      TEMPLATE_execution-log.md    copy this for every new test case
      defects/                     one file per defect (DEF-001, DEF-002, ...)
      TC-<ID>_<name>/
        execution-log.md           procedure, result, pass/fail
        evidence/                  screenshots, Lighthouse/ZAP reports, CSV/HTML exports

## Rules

1. One folder per STP test case, named with the STP test ID.
2. Record a result only after the test has actually been run. Use `NOT EXECUTED` otherwise.
3. Never claim a performance, availability, security-scan, accessibility or backup target
   is met without the report from the tool the STP specifies.
4. Use synthetic data only. Never commit real citizen data, passwords, tokens or keys.
5. Put raw tool output (Lighthouse JSON/HTML, ZAP report, Locust/JMeter CSV) in `evidence/`.
6. Log every failure as a file in `defects/` and link it from the execution log and RTM.

## Result values

`PASS` / `FAIL` / `PARTIAL` (some steps run or some criteria unverified) / `NOT EXECUTED`
