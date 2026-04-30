MODE: reviewer
WORKDIR: /path/to/repo
OBJECTIVE: Review the current diff for correctness risks.

WRITE SCOPE:
- none

NON-GOALS:
- Do not modify files.
- Do not suggest broad rewrites unless required to fix a concrete bug.

VERIFICATION:
- git diff --stat
- git diff

DELIVERABLE:
- Findings first, ordered by severity, with file/line references when possible.
