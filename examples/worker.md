MODE: worker
WORKDIR: /path/to/repo
OBJECTIVE: Implement a bounded deterministic change.

WRITE SCOPE:
- scripts/example.py
- tests/test_example.py

NON-GOALS:
- Do not refactor unrelated modules.
- Do not change project configuration.

VERIFICATION:
- pytest tests/test_example.py

DELIVERABLE:
- Return changed files, verification output, remaining risks, and next step.
