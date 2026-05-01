MODE: synthesizer
WORKDIR: /path/to/your/project
OBJECTIVE: Two prior agents produced conflicting findings about whether `src/cache.py:get_or_set` is thread-safe. Synthesize the conflict and produce a reasoned answer.

WRITE SCOPE:
- none

NON-GOALS:
- Do not modify any files.
- Do not run experiments — work from the cited evidence only.

INPUTS:
- Agent A's report: /tmp/agent-a-report.md (claims thread-safe)
- Agent B's report: /tmp/agent-b-report.md (claims race condition on lines 42-58)

VERIFICATION:
- cat /tmp/agent-a-report.md
- cat /tmp/agent-b-report.md
- git show HEAD -- src/cache.py

DELIVERABLE:
- Identify which specific claim is true and which is false (or both partially true).
- Cite the line numbers and code patterns each agent relied on.
- Conclude with a single recommendation: SAFE / UNSAFE / SAFE_WITH_CAVEAT, plus a one-paragraph justification.
