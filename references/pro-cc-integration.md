# Pro CC Integration

Recommended Pro CC flow:

1. Write a task packet in `/tmp` or inside the target repo.
2. Run `codex_dispatch_role.py --task <packet>`.
3. Read the printed run directory.
4. Inspect `result.md` and `policy.json`.
5. For worker mode, inspect `git diff` and run independent verification.

Do not route through the legacy `codex-worker` Claude subagent unless direct Codex
CLI dispatch fails. This skill is intended to remove the Sonnet wrapper layer.

OpenAI `codex-plugin-cc` and gstack `/codex` remain useful for generic review,
adversarial review, rescue, and consult flows. This skill exists for Pro CC's
structured worker/verifier/reviewer/synthesizer role contract.
