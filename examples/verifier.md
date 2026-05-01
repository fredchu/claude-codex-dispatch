MODE: verifier
WORKDIR: /path/to/your/project
OBJECTIVE: Verify the claim that `pytest tests/integration/ -k "auth"` passes after the latest commit.

WRITE SCOPE:
- none

NON-GOALS:
- Do not modify any files.
- Do not install or upgrade packages.
- Do not commit anything.

VERIFICATION:
- git log -1 --oneline
- pytest tests/integration/ -k "auth" -v

DELIVERABLE:
- Return whether the claim is supported.
- Cite the head commit SHA and the full pytest summary line.
- If the claim fails, list the failing test names.
