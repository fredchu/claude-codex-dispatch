MODE: worker
WORKDIR: /path/to/your/project
OBJECTIVE: Add a unit test for the helper function `slugify(text)` in `src/utils.py`.

WRITE SCOPE:
- tests/test_utils.py

NON-GOALS:
- Do not modify src/utils.py.
- Do not add new dependencies to requirements.txt.
- Do not change pytest configuration.

VERIFICATION:
- pytest tests/test_utils.py -v

DELIVERABLE:
- New test file `tests/test_utils.py` containing at least three assertions:
  one happy-path case, one whitespace-collapsing case, one unicode case.
- Output of pytest showing all three assertions pass.
