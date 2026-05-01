# Orchestrator Integration

Recommended flow when an orchestrator (e.g., Claude Code) dispatches Codex:

1. Write a task packet in `/tmp` or inside the target repo.
2. Run `bin/codex-dispatch --task <packet>` (or invoke the launcher via its full path).
3. Read the printed run directory.
4. Inspect `result.md` and `policy.json`.
5. For worker mode, inspect `git diff` and run independent verification before accepting Codex's success claim.

This skill exists for the structured worker/verifier/reviewer/synthesizer role contract — it removes any wrapper-LLM layer between the orchestrator and Codex CLI.

For ad-hoc adversarial review, rescue, or consult flows, generic Codex tools (e.g., the OpenAI `codex-plugin-cc`) remain appropriate.
