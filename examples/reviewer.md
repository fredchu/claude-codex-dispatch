MODE: reviewer
WORKDIR: /path/to/your/project
OBJECTIVE: Review the diff in commit HEAD for a hypothetical bug fix in `src/parser.py`.

WRITE SCOPE:
- none

NON-GOALS:
- Do not modify any files.
- Do not run any test or build command beyond reading the diff.

VERIFICATION:
- git show HEAD --stat
- git show HEAD -- src/parser.py

DELIVERABLE:
- Structured findings under three headings:
  1. Correctness — does the change actually fix the stated bug?
  2. Risks — what could break? Are there missing test cases?
  3. Style — naming, error handling, idiomatic concerns.
- Conclude with one of: APPROVE / REQUEST_CHANGES / BLOCK and one-sentence rationale.
