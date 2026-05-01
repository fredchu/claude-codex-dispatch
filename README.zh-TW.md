# claude-codex-dispatch
> 從 Claude Code 結構化派工到 OpenAI Codex CLI — 內含角色契約、寫入範圍政策、執行產出物。

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE) [![Skill](https://img.shields.io/badge/Claude_Code-Skill-blue.svg)](./SKILL.md) [![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)

## 為什麼

Claude Code 擅長規劃和推理；Codex CLI 擅長 deterministic patches。直接跑 `codex exec --full-auto` 是無拘束的——沒有 scope 強制、沒有 audit trail、沒有角色界線。這個 skill 加上 task packet（結構化契約）+ 寫入範圍政策 + 執行產出物，讓 Claude Code 派工 Codex 時能像「資深主管派任務給資深工程師」那樣嚴謹。

## Quick Start

### 一行安裝

**POSIX（macOS / Linux / WSL / Git Bash）**
```bash
curl -fsSL https://raw.githubusercontent.com/fredchu/claude-codex-dispatch/main/install.sh | sh
```

**Windows（PowerShell native）**
```powershell
iwr -useb https://raw.githubusercontent.com/fredchu/claude-codex-dispatch/main/install.ps1 | iex
```

### 手動安裝

**POSIX**
```bash
git clone https://github.com/fredchu/claude-codex-dispatch.git ~/.claude/skills/claude-codex-dispatch
```

**PowerShell**
```powershell
git clone https://github.com/fredchu/claude-codex-dispatch.git $env:USERPROFILE\.claude\skills\claude-codex-dispatch
```

### 驗證

```bash
codex --version
~/.claude/skills/claude-codex-dispatch/bin/codex-dispatch --help
```

## 第一次派工（60 秒）

**1. 建立 task packet**

```bash
mkdir -p /tmp/your-test-project
cat > /tmp/first-task.md << 'EOF'
MODE: worker
WORKDIR: /tmp/your-test-project
OBJECTIVE: 為 utils.py 中的 slugify 函式補一個缺少的 unit test。

WRITE SCOPE:
- tests/test_utils.py

NON-GOALS:
- 不得修改 utils.py 或 WRITE SCOPE 以外的任何檔案。
- 不得安裝套件。
- 不得修改 pyproject.toml 或 requirements 相關檔案。

VERIFICATION:
- python -m pytest tests/test_utils.py -v

DELIVERABLE:
- 一個通過的測試，至少涵蓋：空字串、含空格、含特殊字元。
EOF
```

**2. 執行派工**

```bash
~/.claude/skills/claude-codex-dispatch/bin/codex-dispatch --task /tmp/first-task.md
```

**3. 讀取結果**

```bash
cat /tmp/your-test-project/.codex-dispatch/runs/<latest>/result.md
cat /tmp/your-test-project/.codex-dispatch/runs/<latest>/policy.json
```

將 `<latest>` 換成 stdout 印出的 run ID，或用：

```bash
ls -t /tmp/your-test-project/.codex-dispatch/runs/ | head -1
```

## Modes

| Mode | 用途 | 寫入權限 |
|---|---|---|
| `worker` | 範圍明確的實作、deterministic patch | 僅限 WRITE SCOPE 內 |
| `verifier` | 用新證據證明或推翻一個 claim | 禁止 |
| `reviewer` | 審 diff、plan 或 implementation | 禁止 |
| `synthesizer` | 綜合多個衝突發現 | 禁止 |

verifier、reviewer、synthesizer 三種 mode 的寫入權限依契約禁止。若這三種 mode 的執行過程中 working tree 發生異動，wrapper 會回報 policy violation。

## Task Packet 格式

每次派工都是一個含大寫欄位的 Markdown 檔案。

**必填欄位：**

| 欄位 | 說明 |
|---|---|
| `MODE` | `worker`、`verifier`、`reviewer` 或 `synthesizer` |
| `WORKDIR` | git repository 的絕對路徑 |
| `OBJECTIVE` | 一句話說明目標 |
| `WRITE SCOPE` | Codex 可修改的檔案或目錄，或填 `none` |
| `NON-GOALS` | 明確邊界——列出不得異動的項目 |
| `VERIFICATION` | Codex 必須執行的指令或蒐集的證據 |
| `DELIVERABLE` | 預期的交付結果 |

**最小範例：**

```markdown
MODE: verifier
WORKDIR: /path/to/project
OBJECTIVE: 確認最近一次重構後所有現有測試仍能通過。

WRITE SCOPE:
- none

NON-GOALS:
- 不得修改任何檔案。
- 不得安裝套件。

VERIFICATION:
- python -m pytest tests/ -v

DELIVERABLE:
- 回報通過/失敗數量，並逐字引用 test runner 的輸出。
```

完整欄位規格請見 [`references/task-packet.md`](./references/task-packet.md)。

## 執行產出物

每次派工的產出物寫入 `.codex-dispatch/runs/<run-id>/`：

| 檔案 | 內容 |
|---|---|
| `task.md` | 輸入的 task packet（原文複製） |
| `prompt.md` | 組建後送給 Codex 的 system prompt |
| `events.jsonl` | Codex 原始工具事件流，每行一個 JSON 物件 |
| `result.json` | wrapper 解析結果：exit code、mode、violation 旗標 |
| `result.md` | Codex 的敘事輸出——主要審閱的產出物 |
| `pre-status.txt` | Codex 執行前的 `git status` 快照 |
| `post-status.txt` | Codex 執行後的 `git status` 快照 |
| `pre-diff-stat.txt` | 執行前的 `git diff --stat` |
| `post-diff-stat.txt` | 執行後的 `git diff --stat` |
| `policy.json` | wrapper 政策判定：`policy_violation`、`exit_code`、`scope_ok` |

接受任何 worker 輸出前，先讀 `result.md` 和 `policy.json`。若 `policy.json` 顯示 `"policy_violation": true`，立即停止並浮出問題，不得繼續執行。

## 進階：跨 LLM 互檢 Pattern

### 為什麼雙 LLM 互檢有價值

同模型族 + 同 prompt 會產生相關聯的錯誤。當 Claude 撰寫計畫、又由 Claude 驗證實作時，兩個 instance 共享相同的訓練資料、推理模式以及相同的盲點。Claude 的 planner 漏掉的 bug，很可能也會通過 Claude 的 verifier。

不同模型族能抓到不同的問題。Codex 傾向於字面程式碼的正確性；Claude 傾向語意上的一致性。將它們放在不同角色——一個是執行者，一個是審計者——不是重複演練，而是一種結構性的方式，能浮現單一模型驗證會遺漏的失敗。

### 三階段流程

```
Claude（規劃者）
  → 推理需求、撰寫 task packet、承諾 scope

Codex worker（執行者）
  → WRITE SCOPE 內的 deterministic patch，不做判斷取捨

Codex verifier（審計者）
  → read-only，必須引用指令輸出，無法自行合理化成功
```

verifier 使用相同的 binary，只是不同的 mode。關鍵的改變是契約：verifier 不能寫入、必須蒐集新的證據、必須在 deliverable 中引用這些證據。Claude 接著讀取兩次執行的 `result.md`，才接受這份工作。

### 真實案例

一份涵蓋 parser、transformer、CLI 三層的 11-task TDD plan，以單次 Codex worker 派工跑通，全部 47 個測試通過。整合之前，先以 verifier 模式獨立跑一次相同的測試套件並確認數量吻合。其中一個 edge-case 測試的參數化方式遮蔽了一個邊界條件；verifier 的獨立執行暴露了這個問題，因為它在沒有 worker 累積狀態的情況下跑測試。

這就是這個 skill 存在的目的——讓這種 pattern 變得可行。

## 安全模型

所有 Codex 呼叫都使用 `--dangerously-bypass-approvals-and-sandbox`，此旗標已內建於 wrapper。安全性不依靠 sandbox mode，而來自以下結構：

1. **Task packet**——orchestrator 在 Codex 執行前事先承諾 scope、non-goals 以及驗證標準。
2. **Write-scope 檢查**——wrapper 比對 Codex 執行前後的 `git status`。read-only mode 若 working tree 有異動，觸發 `policy_violation: true`；worker mode 若有 WRITE SCOPE 以外的改動，同樣觸發 violation。
3. **git status 快照**——`pre-status.txt` 和 `post-status.txt` 構成不可竄改的 audit trail，獨立於 Codex 自身的回報。
4. **`policy.json`**——機器可讀的判定結果。可在 CI 或程式中直接檢查 `policy_violation` 和 `scope_ok`。
5. **Orchestrator review**——orchestrator 必須讀取並接受 `result.md` 和 `policy.json`，才算完成這份工作。

這個 skill 明確假設：**你會讀取結果，且永遠不接受 Codex 自己宣稱的成功，必須獨立驗證。**

## 系統需求

- Claude Code（最新版）
- OpenAI Codex CLI（≥ TBD-on-release-day）——版本號於 release 時確認
- Python 3.9+
- macOS / Linux / Windows（原生 PowerShell 或 WSL）

> **注意：** Windows 支援為 experimental（實驗性）。

## 設定選項

### 旗標

| 旗標 | 說明 |
|---|---|
| `--task <path>` | **（必填）** task packet Markdown 檔案的路徑 |
| `--output-dir <dir>` | 覆寫預設的執行產出物目錄（`<workdir>/.codex-dispatch/runs`） |
| `--allow-dirty-overlap` | 允許 worker mode 動到已 dirty 的 scope 內檔案 |
| `--dry-run` | 只生成 prompt 和產出物，不真正呼叫 Codex |

### 環境變數

| 變數 | 說明 |
|---|---|
| `$CLAUDE_SKILLS_DIR` | 安裝時覆寫 skills 目錄 |

## FAQ

**Q：為什麼不直接用 `codex exec`？**
可以。但你會失去結構化契約、寫入範圍強制、audit trail。這個 skill 在你需要嚴謹度的場景補上這些。

**Q：沒用 Claude Code 也能用嗎？**
wrapper（`scripts/codex_dispatch_role.py`）跟 orchestrator 解耦——任何能產生 task packet 的工具都能 dispatch。skill metadata（`SKILL.md`）才是 Claude Code 專用。

**Q：跟 Aider / AutoGen / LangGraph 相容嗎？**
不是原生整合，但 wrapper 可以從那些工具當 subprocess 呼叫。

**Q：跟 multi-agent framework 比起來有什麼差別？**
Frameworks orchestrate LLM agents 之間的通訊。這個 skill 範圍更窄：單一派工契約，把範圍明確的任務 delegate 給 Codex CLI。

## Roadmap

- [ ] v0.2.0 — Claude Code Plugin manifest、unit tests、CONTRIBUTING.md
- [ ] v0.3.0 — Optional metrics export（執行時間、token 用量）

## 貢獻

issues 跟 PR 歡迎，到 https://github.com/fredchu/claude-codex-dispatch/issues。CONTRIBUTING.md 還沒寫——v0.2.0 才補。

## License

MIT。詳見 [LICENSE](./LICENSE)。

## 致謝

> 這個 skill 最初是為一個雙機 Claude Code 設置而做——一台主要的 orchestrator instance 派工給次要的 worker instance + Codex CLI 跑 deterministic patches。跨 LLM 互檢 pattern 是六週實際 production 使用迭代出來的。
>
> → 看上線故事：[@fredchu 的 X thread](TBD-link)

---

English version: [README.md](./README.md)
