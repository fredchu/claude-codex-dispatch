# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-05-XX

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
- OpenAI Codex CLI (≥ TBD-on-release-day)
- Python 3.9+
- macOS / Linux / Windows (native PowerShell or WSL)

### Known Limitations
- Windows support: experimental. Tested on macOS; community feedback welcome.
- No automated test suite (`examples/` serve as smoke tests).

[0.1.0]: https://github.com/fredchu/claude-codex-dispatch/releases/tag/v0.1.0
