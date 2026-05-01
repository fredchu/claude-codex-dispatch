# Task Packet Format

Every dispatch is a Markdown file with uppercase fields. Keep it concrete.

Required fields:

- `MODE`: `worker`, `verifier`, `reviewer`, or `synthesizer`
- `WORKDIR`: absolute path to a git repository
- `OBJECTIVE`: one sentence
- `WRITE SCOPE`: files or directories Codex may modify, or `none`
- `NON-GOALS`: explicit boundaries
- `VERIFICATION`: commands or evidence Codex should gather
- `DELIVERABLE`: expected result

Recommended fields:

- `CONTEXT`: confirmed facts and relevant file paths
- `ALLOW DIRTY OVERLAP`: use `true` only when the orchestrator accepts that Codex may touch already-dirty scoped files

Use absolute paths in `WORKDIR`. Use repo-relative paths in `WRITE SCOPE`.

For data pipelines, `VERIFICATION` must include at least one value sanity check or external-source comparison. A zero exit code is not enough.
