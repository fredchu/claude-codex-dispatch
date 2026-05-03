# claude-codex-dispatch
> Structured dispatch from Claude Code to OpenAI Codex CLI — with role contracts, write-scope policy, and run artifacts.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE) [![Skill](https://img.shields.io/badge/Claude_Code-Skill-blue.svg)](./SKILL.md) [![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)

## Why

Claude Code is great at planning and reasoning; Codex CLI is great at deterministic patches. Direct `codex exec --full-auto` is unconstrained — no scope enforcement, no audit trail, no role boundaries. This skill adds task packets (a structured contract) + write-scope policy + run artifacts so Claude Code can dispatch Codex with the same rigor as a human delegating to a senior engineer.

## Quick Start

### One-line install

**POSIX (macOS / Linux / WSL / Git Bash)**
```bash
curl -fsSL https://raw.githubusercontent.com/fredchu/claude-codex-dispatch/main/install.sh | sh
```

**Windows (PowerShell native)**
```powershell
iwr -useb https://raw.githubusercontent.com/fredchu/claude-codex-dispatch/main/install.ps1 | iex
```

### Manual install

**POSIX**
```bash
git clone https://github.com/fredchu/claude-codex-dispatch.git ~/.claude/skills/claude-codex-dispatch
```

**PowerShell**
```powershell
git clone https://github.com/fredchu/claude-codex-dispatch.git $env:USERPROFILE\.claude\skills\claude-codex-dispatch
```

### Verify

```bash
codex --version
~/.claude/skills/claude-codex-dispatch/bin/codex-dispatch --help
```

## Your First Dispatch (60 seconds)

**1. Create a task packet**

```bash
mkdir -p /tmp/your-test-project
cat > /tmp/first-task.md << 'EOF'
MODE: worker
WORKDIR: /tmp/your-test-project
OBJECTIVE: Add a missing unit test for the slugify function in utils.py.

WRITE SCOPE:
- tests/test_utils.py

NON-GOALS:
- Do not modify utils.py or any file outside WRITE SCOPE.
- Do not install packages.
- Do not modify pyproject.toml or requirements files.

VERIFICATION:
- python -m pytest tests/test_utils.py -v

DELIVERABLE:
- A passing test that covers at least: empty string, spaces, and special characters.
EOF
```

**2. Run the dispatch**

```bash
~/.claude/skills/claude-codex-dispatch/bin/codex-dispatch --task /tmp/first-task.md
```

**3. Read the result**

```bash
cat /tmp/your-test-project/.codex-dispatch/runs/<latest>/result.md
cat /tmp/your-test-project/.codex-dispatch/runs/<latest>/policy.json
```

Replace `<latest>` with the run ID printed to stdout, or use:

```bash
ls -t /tmp/your-test-project/.codex-dispatch/runs/ | head -1
```

## Modes

| Mode | Use For | Writes |
|---|---|---|
| `worker` | bounded implementation, deterministic patch | inside WRITE SCOPE only |
| `verifier` | prove or disprove a claim with fresh evidence | forbidden |
| `reviewer` | review a diff, plan, or implementation | forbidden |
| `synthesizer` | merge conflicting findings | forbidden |

Verifier, reviewer, and synthesizer modes are read-only by contract. The wrapper reports a policy violation if the working tree changes in those modes.

## Task Packet Format

Every dispatch is a Markdown file with uppercase fields.

**Required fields:**

| Field | Description |
|---|---|
| `MODE` | `worker`, `verifier`, `reviewer`, or `synthesizer` |
| `WORKDIR` | Absolute path to a git repository |
| `OBJECTIVE` | One sentence |
| `WRITE SCOPE` | Files or directories Codex may modify, or `none` |
| `NON-GOALS` | Explicit boundaries — list what must not change |
| `VERIFICATION` | Commands or evidence Codex must gather |
| `DELIVERABLE` | Expected result |

**Minimal example:**

```markdown
MODE: verifier
WORKDIR: /path/to/project
OBJECTIVE: Confirm that all existing tests pass after the recent refactor.

WRITE SCOPE:
- none

NON-GOALS:
- Do not modify any file.
- Do not install packages.

VERIFICATION:
- python -m pytest tests/ -v

DELIVERABLE:
- Return pass/fail count and cite the test runner output verbatim.
```

Full field reference: [`references/task-packet.md`](./references/task-packet.md)

## Run Artifacts

Each dispatch writes to `.codex-dispatch/runs/<run-id>/`:

| File | Contents |
|---|---|
| `task.md` | Input task packet (copied verbatim) |
| `prompt.md` | System prompt constructed and sent to Codex |
| `events.jsonl` | Raw Codex tool events, one JSON object per line |
| `result.json` | Parsed wrapper result: exit code, mode, violation flag |
| `result.md` | Codex's narrative output — primary artifact to review |
| `pre-status.txt` | `git status` snapshot before Codex ran |
| `post-status.txt` | `git status` snapshot after Codex ran |
| `pre-diff-stat.txt` | `git diff --stat` before |
| `post-diff-stat.txt` | `git diff --stat` after |
| `policy.json` | Wrapper policy verdict: `policy_violation`, `exit_code`, `scope_ok` |

Review `result.md` and `policy.json` before accepting any worker output. If `policy.json` shows `"policy_violation": true`, stop and surface it — do not continue.

## Advanced: Cross-LLM Verification Pattern

### Why dual-LLM cross-check matters

Running the same model family on the same prompt produces correlated errors. When Claude writes the plan and Claude also verifies the implementation, both instances share training data, reasoning patterns, and the same blind spots. A bug that Claude's planner missed is likely to pass Claude's verifier too.

Different model families catch different things. Codex tends toward literal code correctness; Claude tends toward semantic coherence. Putting them in different roles — one as executor, one as auditor — is not a redundancy exercise. It is a structural way to surface failures that monolithic verification would miss.

### Three-stage flow

```
Claude (planner)
  → reasons over requirements, writes task packets, commits to scope

Codex worker (executor)
  → deterministic patch inside WRITE SCOPE, no judgment calls

Codex verifier (auditor)
  → read-only, must cite command output, cannot rationalize success
```

The verifier is the same binary but a different mode. What changes is the contract: the verifier cannot write, must gather fresh evidence, and must quote that evidence in its deliverable. Claude then reads `result.md` from both runs before accepting the work.

### Real example

An 11-task TDD plan — covering parser, transformer, and CLI layers — was dispatched in a single worker run. All 47 tests passed. Before integrating, a verifier dispatch ran the same test suite independently and confirmed the counts matched. One edge-case test had been parameterized in a way that masked a boundary condition; the verifier's independent run exposed it because it ran the suite without the worker's accumulated state.

This is the pattern this skill exists to enable.

## Safety Model

`codex exec --dangerously-bypass-approvals-and-sandbox` is always used. Safety does not come from sandbox mode. It comes from structure:

1. **Task packet** — the orchestrator commits to scope, non-goals, and verification criteria upfront, before Codex runs.
2. **Write-scope check** — the wrapper compares `git status` before and after. For read-only modes, any working-tree change triggers `policy_violation: true`. For worker mode, changes outside WRITE SCOPE trigger a violation.
3. **Git status snapshots** — `pre-status.txt` and `post-status.txt` form an immutable audit trail independent of Codex's own reporting.
4. **`policy.json`** — machine-readable verdict. Check `policy_violation` and `scope_ok` programmatically or in CI.
5. **Orchestrator review** — `result.md` and `policy.json` must be read and accepted by the orchestrator before the work is considered done.

This skill explicitly assumes: **you read the results and never accept Codex's own success claim without independent verification.**

## Requirements

- Claude Code (latest version)
- OpenAI Codex CLI (use the version you already have — no version pin)
- Python 3.9+
- macOS / Linux / Windows (native PowerShell or WSL)

> **Note:** Windows support is experimental.

## Operational Safeguards

The wrapper guards against the failure modes seen in real dispatch runs:

- **Watchdog** — kills the Codex subprocess on hard wall-clock timeout (`--timeout-sec`, default 1800 s) or when stdout has been silent for longer than `--heartbeat-sec` (default 300 s). Idle hangs (suspected ChatGPT stream stalls) used to silently consume token budget; the wrapper now fails fast and records `watchdog_killed: true` in `policy.json`.
- **Quota gate** — refuses to dispatch when the Codex 5-hour primary window `used_percent` is at or above `--quota-gate` (default 85). Reads `~/.codex/auth.json` and queries the same usage endpoint codexbar uses. Pass `--force` to override; skips gracefully on network or auth error.
- **Streaming events** — `events.jsonl` is written line-by-line during the run, so you can `tail -f` an active dispatch instead of waiting for the subprocess to exit.

## Configuration

### Flags

| Flag | Description |
|---|---|
| `--task <path>` | **(Required)** Path to the task packet Markdown file |
| `--output-dir <dir>` | Override default run artifact directory (`<workdir>/.codex-dispatch/runs`) |
| `--allow-dirty-overlap` | Allow worker mode to touch already-dirty scoped files |
| `--dry-run` | Build prompt and artifacts without calling Codex |
| `--timeout-sec <n>` | Hard wall-clock timeout in seconds (default 1800) |
| `--heartbeat-sec <n>` | Kill if stdout silent longer than this in seconds (default 300) |
| `--quota-gate <pct>` | Refuse dispatch when 5h Codex usage ≥ this percent (default 85) |
| `--force` | Override the quota gate |

### Environment variables

| Variable | Description |
|---|---|
| `$CLAUDE_SKILLS_DIR` | Override the skills directory used by the installer |
| `$CODEX_DISPATCH_TIMEOUT_SEC` | Default value for `--timeout-sec` |
| `$CODEX_DISPATCH_HEARTBEAT_SEC` | Default value for `--heartbeat-sec` |

## FAQ

**Q: Why not just use `codex exec` directly?**
You can. But you lose the structured contract, write-scope enforcement, and audit trail. This skill adds those for cases where you need rigor.

**Q: Can I use this without Claude Code?**
The wrapper (`scripts/codex_dispatch_role.py`) is orchestrator-agnostic — any tool that produces a task packet can dispatch it. The skill metadata (`SKILL.md`) is Claude Code-specific.

**Q: Does this work with Aider / AutoGen / LangGraph?**
Not natively, but the wrapper can be invoked from any of them as a subprocess.

**Q: How does this compare to multi-agent frameworks?**
Frameworks orchestrate communication between LLM agents. This skill is narrower: a single dispatch contract for delegating bounded tasks to Codex CLI.

## Roadmap

- [ ] v0.2.0 — Claude Code Plugin manifest, unit tests, CONTRIBUTING.md
- [ ] v0.3.0 — Optional metrics export (run duration, token usage)

## Contributing

Issues and PRs welcome at https://github.com/fredchu/claude-codex-dispatch/issues. No CONTRIBUTING.md yet — that's v0.2.0.

## License

MIT. See [LICENSE](./LICENSE).

## Acknowledgement

> Originally built as part of a dual-machine Claude Code setup — a primary "orchestrator" Claude Code instance delegating to a secondary "worker" instance and Codex CLI for deterministic patches. The cross-LLM verification pattern emerged from real production use across ~6 weeks of iteration.
>
> → Read the launch story: [@fredchu's X thread](TBD-link)

---

繁體中文版本請見 [README.zh-TW.md](./README.zh-TW.md)
