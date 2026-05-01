# Changelog

本專案所有重要變更皆記錄於此檔。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.1.0/)，
並遵循 [語意化版本（Semantic Versioning）](https://semver.org/lang/zh-TW/)。

## [0.1.0] — 2026-05-XX

### 新增
- 首次公開發布。
- 四種派工 mode：`worker`、`verifier`、`reviewer`、`synthesizer`。
- Task packet 格式：含 `WRITE SCOPE` / `NON-GOALS` / `VERIFICATION` 欄位。
- 寫入範圍政策強制（透過 git status 快照前後比對）。
- 執行產出物：`task.md`、`prompt.md`、`events.jsonl`、`result.json`、
  `result.md`、`pre-status.txt`、`post-status.txt`、`pre-diff-stat.txt`、
  `post-diff-stat.txt`、`policy.json`。
- `--dry-run`、`--output-dir`、`--allow-dirty-overlap` 選項。
- 跨平台 launcher（`bin/codex-dispatch` POSIX + `bin/codex-dispatch.cmd` Windows）。
- 一行安裝腳本：POSIX (`install.sh`) 與 Windows (`install.ps1`)。
- 英文與繁體中文版 README 和 CHANGELOG。
- 四個 mode 各自的範例（`examples/{worker,verifier,reviewer,synthesizer}.md`）。

### 系統需求
- Claude Code（最新版）
- OpenAI Codex CLI (≥ TBD-on-release-day)
- Python 3.9+
- macOS / Linux / Windows（原生 PowerShell 或 WSL）

### 已知限制
- Windows 支援：experimental（實驗性）。在 macOS 上驗證過；歡迎社群回報 Windows 使用情形。
- 沒有自動化測試套件（`examples/` 充當 smoke test）。

[0.1.0]: https://github.com/fredchu/claude-codex-dispatch/releases/tag/v0.1.0
