---
name: codex-dispatch
description: >
  Dispatch OpenAI Codex CLI directly from Claude Code with a structured role
  contract. Use when Claude Code needs Codex to act as worker, verifier, reviewer,
  or synthesizer through codex exec, with write-scope checks, run artifacts,
  and structured result output. Always uses Codex CLI directly, not a Claude
  subagent wrapper.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# Codex Dispatch

Use this skill to call OpenAI Codex CLI directly from Claude Code while preserving
the orchestrator's role boundaries and verification discipline.

## Core Rule

All dispatches must go through:

```bash
~/.claude/skills/claude-codex-dispatch/bin/codex-dispatch --task <task-file>
```

The script always calls `codex exec` with:

```bash
--dangerously-bypass-approvals-and-sandbox
```

Safety therefore comes from the task packet, wrapper checks, git status snapshots,
write-scope validation, and orchestrator review of the result artifacts.

## Modes

Pick exactly one mode per dispatch:

| Mode | Use for | Writes |
|---|---|---|
| `worker` | bounded implementation, small refactor, deterministic patch | allowed only inside `WRITE SCOPE` |
| `verifier` | prove or disprove a claim with fresh evidence | forbidden |
| `reviewer` | review a diff, plan, or implementation | forbidden |
| `synthesizer` | merge conflicting findings or agent outputs | forbidden |

Verifier, reviewer, and synthesizer modes are read-only by contract. The wrapper
will report a policy violation if the working tree changes.

## Task Packet

Create a task packet Markdown file. Use this minimum shape:

```markdown
MODE: verifier
WORKDIR: /path/to/your/project
OBJECTIVE: Verify that the targeted test and build checks work.

WRITE SCOPE:
- none

NON-GOALS:
- Do not modify files.
- Do not install packages.

VERIFICATION:
- pytest tests/ -v
- pytest tests/ -k "specific_test" -v

DELIVERABLE:
- Return whether the claim is supported and cite command evidence.
```

For full field guidance, read `references/task-packet.md`.

## Run

```bash
~/.claude/skills/claude-codex-dispatch/bin/codex-dispatch \
  --task /path/to/task.md
```

Useful options:

```bash
--dry-run                 # build prompt and artifacts without calling Codex
--output-dir <dir>        # default: <workdir>/.codex-dispatch/runs
--allow-dirty-overlap     # allow worker mode to touch already-dirty scoped files
```

The script writes:

```text
.codex-dispatch/runs/<run-id>/
├── task.md
├── prompt.md
├── events.jsonl
├── result.json
├── result.md
├── pre-status.txt
├── post-status.txt
├── pre-diff-stat.txt
├── post-diff-stat.txt
└── policy.json
```

## Completion

After a run, read `result.md` and `policy.json`. For `worker` mode, also inspect
the git diff. Do not accept Codex's own success claim without fresh evidence.

If `policy.json` reports `policy_violation: true`, stop and surface that before
continuing.

## References

- Task packet format: `references/task-packet.md`
- Mode policy: `references/mode-policy.md`
- Orchestrator integration notes: `references/orchestrator-integration.md`
