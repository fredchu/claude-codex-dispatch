# Changelog

本專案所有重要變更皆記錄於此檔。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.1.0/)，
並遵循 [語意化版本（Semantic Versioning）](https://semver.org/lang/zh-TW/)。

## [0.1.1] — 2026-05-03

### 修正
- **Watchdog 逾時與心跳**：codex 子進程在硬性 wall-clock 超時（`--timeout-sec`，
  預設 1800）或 stdout 連續沒輸出超過 `--heartbeat-sec`（預設 300）時會被殺。
  v0.1.0 dogfood 兩次撞到 codex 卡 40 分鐘無輸出（疑 ChatGPT stream 卡 retry），
  舊版 wrapper 默默燒 token；現在會 fail fast，並把 `watchdog_killed: true`
  寫進 `policy.json`。可用 `CODEX_DISPATCH_TIMEOUT_SEC` /
  `CODEX_DISPATCH_HEARTBEAT_SEC` 環境變數覆蓋。
- **WRITE SCOPE parser false positive 兩種**：
  - 標題附帶括號註解（`WRITE SCOPE (bare paths only):`）讓 regex match 失敗，
    後面 bullet 條列被默默丟掉 → `write_scope=[]` → 每個改動誤判為 out-of-scope。
  - 條列項末尾註解（`/path/foo.py (NEW)`、`(MODIFY)`、`(NEW, optional)`）沒被
    剝除，比對時 `/path/foo.py (NEW)` 跟 `git status` 回的純路徑永遠不 match。
    現在兩種寫法都接受，註解自動剝掉。

### 新增
- **配額守門 (Quota gate)**：當 Codex 5 小時 window `used_percent` 超過
  `--quota-gate`（預設 85）時拒絕派工。讀 `~/.codex/auth.json` OAuth token
  並打 `https://chatgpt.com/backend-api/wham/usage`。`--force` 強制覆蓋。
  網路/認證失敗優雅跳過。

### 備註
- 純擴充式重構 `codex_dispatch_role.py`；既有 task packet 不需修改。
- Watchdog 改用 `subprocess.Popen` + threaded pump；events 即時寫進
  `events.jsonl`（先前是 codex 結束才一次寫入）。

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
