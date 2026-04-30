MODE: synthesizer
WORKDIR: /path/to/repo
OBJECTIVE: Synthesize multiple agent reports and preserve disagreements.

WRITE SCOPE:
- none

NON-GOALS:
- Do not modify files.
- Do not invent consensus where reports disagree.

VERIFICATION:
- Read the provided reports.

DELIVERABLE:
- Agreements, conflicts, confidence level, and recommended next action.
