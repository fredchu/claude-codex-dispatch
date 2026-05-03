# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] — 2026-05-03

### Fixed
- **Watchdog timeout & heartbeat**: codex subprocess now killed on hard wall-clock
  timeout (`--timeout-sec`, default 1800) or when stdout has been silent for
  longer than `--heartbeat-sec` (default 300). Hangs observed twice during
  v0.1.0 dogfood (both ~40 min idle, suspected ChatGPT stream stall) used to
  silently consume token budget; the wrapper now fails fast and records
  `watchdog_killed: true` in `policy.json`. Configurable via
  `CODEX_DISPATCH_TIMEOUT_SEC` / `CODEX_DISPATCH_HEARTBEAT_SEC` env vars.
- **WRITE SCOPE parser fragility (false positives)**: two related bugs:
  - Parenthetical comments after the field key (`WRITE SCOPE (bare paths only):`)
    caused the regex to fail and silently dropped the bullet list, leaving
    `write_scope=[]` and flagging every change as out-of-scope.
  - Per-line annotations (`/path/foo.py (NEW)`, `(MODIFY)`, `(NEW, optional)`)
    were not stripped before path comparison, so the literal string
    `/path/foo.py (NEW)` never matched the actual `/path/foo.py` from
    `git status`. Both forms are now accepted; annotations are stripped.

### Added
- **Quota gate**: refuse to dispatch when Codex 5h primary window
  `used_percent` is at or above `--quota-gate` (default 85). Reads OAuth
  token from `~/.codex/auth.json` and queries
  `https://chatgpt.com/backend-api/wham/usage` (same endpoint codexbar uses).
  Pass `--force` to override. Skips gracefully on network/auth error.

### Notes
- Pure additive refactor of the existing `codex_dispatch_role.py`; existing
  task packets continue to dispatch unchanged.
- Watchdog uses `subprocess.Popen` + threaded stdout/stderr pumps; events
  stream to `events.jsonl` in real time (previously buffered until exit).

## [0.1.0] — 2026-05-02

### Added
- Initial public release.
- Four dispatch modes: `worker`, `verifier`, `reviewer`, `synthesizer`.
- Task packet format with `WRITE SCOPE` / `NON-GOALS` / `VERIFICATION` fields.
- Write-scope policy enforcement with git status snapshots.
- Run artifacts: `task.md`, `prompt.md`, `events.jsonl`, `result.json`,
  `result.md`, `pre-status.txt`, `post-status.txt`, `pre-diff-stat.txt`,
  `post-diff-stat.txt`, `policy.json`.
- `--dry-run`, `--output-dir`, `--allow-dirty-overlap` options.
- Cross-platform launchers (`bin/codex-dispatch` POSIX + `bin/codex-dispatch.cmd` Windows).
- One-line installers for POSIX (`install.sh`) and Windows (`install.ps1`).
- English and Traditional Chinese READMEs and CHANGELOGs.
- Examples for all four modes (`examples/{worker,verifier,reviewer,synthesizer}.md`).

### Requirements
- Claude Code (latest)
- OpenAI Codex CLI
- Python 3.9+
- macOS / Linux / Windows (native PowerShell or WSL)

### Known Limitations
- Windows support: experimental. Tested on macOS; community feedback welcome.
- No automated test suite (`examples/` serve as smoke tests).

[0.1.1]: https://github.com/fredchu/claude-codex-dispatch/releases/tag/v0.1.1
[0.1.0]: https://github.com/fredchu/claude-codex-dispatch/releases/tag/v0.1.0
