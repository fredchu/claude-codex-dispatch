#!/usr/bin/env python3
"""Dispatch Codex CLI with structured role contracts from an orchestrator."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


VALID_MODES = {"worker", "verifier", "reviewer", "synthesizer"}
READ_ONLY_MODES = {"verifier", "reviewer", "synthesizer"}
DEFAULT_IGNORE_STATUS_PREFIXES = [".tmp.driveupload/"]


def run(cmd: list[str], cwd: Path, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def git_output(args: list[str], cwd: Path) -> str:
    proc = run(["git", *args], cwd)
    output = proc.stdout
    if proc.stderr:
        output += proc.stderr
    return output


def git_status(cwd: Path) -> str:
    return git_output(["status", "--short", "--untracked-files=all"], cwd)


def parse_packet(text: str) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    current: str | None = None
    sections: dict[str, list[str]] = {}

    header_re = re.compile(r"^([A-Z][A-Z0-9 _-]*):\s*(.*)$")
    for raw in text.splitlines():
        line = raw.rstrip()
        match = header_re.match(line)
        if match:
            key = match.group(1).strip().upper().replace(" ", "_")
            value = match.group(2).strip()
            current = key
            if value:
                fields[key] = value
            else:
                sections.setdefault(key, [])
            continue
        if current and current not in fields:
            sections.setdefault(current, []).append(line)

    for key, lines in sections.items():
        cleaned = [line.strip() for line in lines if line.strip()]
        values = []
        for line in cleaned:
            if line.startswith("- "):
                values.append(line[2:].strip())
            else:
                values.append(line)
        fields[key] = values

    return fields


def require_string(fields: dict[str, Any], key: str) -> str:
    value = fields.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise SystemExit(f"ERROR: task packet missing required field {key}")


def list_field(fields: dict[str, Any], key: str) -> list[str]:
    value = fields.get(key, [])
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def parse_status_names(status: str) -> set[str]:
    names: set[str] = set()
    for line in status.splitlines():
        if not line.strip():
            continue
        path = line[3:] if len(line) > 3 else line
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        names.add(path.strip())
    return names


def filter_status(status: str, ignored_prefixes: list[str]) -> str:
    kept: list[str] = []
    for line in status.splitlines():
        path = line[3:] if len(line) > 3 else line
        path = path.strip()
        if any(path.startswith(prefix) for prefix in ignored_prefixes):
            continue
        kept.append(line)
    return "\n".join(kept) + ("\n" if kept else "")


def digest_path(path: Path) -> str:
    h = hashlib.sha256()
    if path.is_file():
        h.update(b"file\0")
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    if path.is_dir():
        h.update(b"dir\0")
        for item in sorted(p for p in path.rglob("*") if p.is_file()):
            h.update(str(item.relative_to(path)).encode("utf-8", errors="surrogateescape"))
            h.update(b"\0")
            with item.open("rb") as fh:
                for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                    h.update(chunk)
            h.update(b"\0")
        return h.hexdigest()
    return "missing"


def dirty_fingerprints(names: set[str], cwd: Path) -> dict[str, str]:
    fingerprints: dict[str, str] = {}
    for name in sorted(names):
        h = hashlib.sha256()
        for args in [
            ["status", "--short", "--untracked-files=all", "--", name],
            ["diff", "--binary", "--", name],
            ["diff", "--cached", "--binary", "--", name],
        ]:
            h.update(git_output(args, cwd).encode("utf-8", errors="surrogateescape"))
            h.update(b"\0")
        h.update(digest_path(cwd / name).encode("ascii"))
        fingerprints[name] = h.hexdigest()
    return fingerprints


def should_fingerprint(names: set[str], limit: int) -> bool:
    return 0 < len(names) <= limit


def is_none_scope(scope: list[str]) -> bool:
    return not scope or all(item.lower() in {"none", "no writes", "read-only", "readonly"} for item in scope)


def in_scope(path: str, scopes: list[str]) -> bool:
    if is_none_scope(scopes):
        return False
    clean = path.lstrip("./")
    for scope in scopes:
        s = scope.strip().lstrip("./")
        if not s or s.lower() in {"none", "no writes", "read-only", "readonly"}:
            continue
        if s.endswith("/"):
            if clean.startswith(s):
                return True
        elif clean == s or clean.startswith(f"{s}/"):
            return True
    return False


def safe_slug(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return slug[:48] or "task"


def build_prompt(fields: dict[str, Any], task_text: str) -> str:
    mode = require_string(fields, "MODE").lower()
    objective = require_string(fields, "OBJECTIVE")
    write_scope = list_field(fields, "WRITE_SCOPE")
    non_goals = list_field(fields, "NON_GOALS")
    verification = list_field(fields, "VERIFICATION")
    deliverable = fields.get("DELIVERABLE", "")
    if isinstance(deliverable, list):
        deliverable_text = "\n".join(f"- {item}" for item in deliverable)
    else:
        deliverable_text = str(deliverable)

    if mode not in VALID_MODES:
        raise SystemExit(f"ERROR: invalid MODE {mode!r}; expected one of {sorted(VALID_MODES)}")

    role_policy = {
        "worker": "You may modify files only inside WRITE SCOPE. Do not touch files outside scope.",
        "verifier": "Read-only contract. Do not modify files. Run commands only to gather evidence.",
        "reviewer": "Read-only contract. Do not modify files. Produce findings first with severity and file/line references when possible.",
        "synthesizer": "Read-only contract. Do not modify files. Preserve disagreements instead of flattening them into consensus.",
    }[mode]

    schema_note = """Return final output as JSON matching the provided schema.
Use concise strings. Include command evidence under verification_run and evidence."""

    return f"""You are OpenAI Codex running as an orchestrator-delegated {mode}.

ROLE POLICY:
{role_policy}

OBJECTIVE:
{objective}

WRITE SCOPE:
{json.dumps(write_scope, ensure_ascii=False, indent=2)}

NON-GOALS:
{json.dumps(non_goals, ensure_ascii=False, indent=2)}

VERIFICATION REQUESTS:
{json.dumps(verification, ensure_ascii=False, indent=2)}

DELIVERABLE:
{deliverable_text}

TASK PACKET:
```markdown
{task_text}
```

RESULT FORMAT:
{schema_note}
"""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


def render_result_md(result: Any, policy: dict[str, Any]) -> str:
    if not isinstance(result, dict):
        result = {"result": "blocked", "risks": ["Codex did not return valid JSON."], "raw": result}

    lines = [
        f"# Codex Dispatch Result",
        "",
        f"RESULT: {result.get('result', 'unknown')}",
        f"MODE: {policy.get('mode', 'unknown')}",
        f"POLICY VIOLATION: {policy.get('policy_violation', False)}",
        "",
    ]
    for key, title in [
        ("summary", "Summary"),
        ("changed_files", "Changed Files"),
        ("verification_run", "Verification Run"),
        ("evidence", "Evidence"),
        ("findings", "Findings"),
        ("risks", "Risks"),
        ("next", "Next"),
    ]:
        value = result.get(key)
        if value in (None, "", []):
            continue
        lines.extend([f"## {title}", ""])
        if isinstance(value, list):
            for item in value:
                lines.append(f"- {item}")
        else:
            lines.append(str(value))
        lines.append("")

    if policy.get("messages"):
        lines.extend(["## Policy Messages", ""])
        for msg in policy["messages"]:
            lines.append(f"- {msg}")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Dispatch Codex CLI with role contracts.")
    parser.add_argument("--task", required=True, help="Task packet markdown file.")
    parser.add_argument("--output-dir", help="Run artifact root. Default: <workdir>/.codex-dispatch/runs")
    parser.add_argument("--allow-dirty-overlap", action="store_true", help="Allow worker to modify already-dirty scoped files.")
    parser.add_argument(
        "--fingerprint-limit",
        type=int,
        default=200,
        help="Maximum dirty file count for full before/after fingerprint checks. Default: 200.",
    )
    parser.add_argument(
        "--ignore-status-prefix",
        action="append",
        default=list(DEFAULT_IGNORE_STATUS_PREFIXES),
        help="Git status path prefix to ignore for policy checks. Can be repeated.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Build artifacts without calling Codex.")
    args = parser.parse_args()

    task_path = Path(args.task).expanduser().resolve()
    task_text = task_path.read_text(encoding="utf-8")
    fields = parse_packet(task_text)
    mode = require_string(fields, "MODE").lower()
    workdir = Path(require_string(fields, "WORKDIR")).expanduser().resolve()
    objective = require_string(fields, "OBJECTIVE")
    write_scope = list_field(fields, "WRITE_SCOPE")

    if mode not in VALID_MODES:
        raise SystemExit(f"ERROR: invalid MODE {mode!r}; expected one of {sorted(VALID_MODES)}")
    if not workdir.exists():
        raise SystemExit(f"ERROR: WORKDIR does not exist: {workdir}")
    if run(["git", "rev-parse", "--is-inside-work-tree"], workdir).returncode != 0:
        raise SystemExit(f"ERROR: WORKDIR is not inside a git repo: {workdir}")
    if shutil.which("codex") is None and not args.dry_run:
        raise SystemExit("ERROR: codex CLI not found on PATH")

    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_id = f"{timestamp}-{mode}-{safe_slug(objective)}"
    output_root = Path(args.output_dir).expanduser().resolve() if args.output_dir else workdir / ".codex-dispatch" / "runs"
    run_dir = output_root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    prompt = build_prompt(fields, task_text)
    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "result.schema.json"
    result_json = run_dir / "result.json"
    events_jsonl = run_dir / "events.jsonl"
    stderr_path = run_dir / "stderr.txt"

    pre_status = git_status(workdir)
    pre_policy_status = filter_status(pre_status, args.ignore_status_prefix)
    pre_diff_stat = git_output(["diff", "--stat"], workdir)
    pre_names = parse_status_names(pre_policy_status)
    fingerprint_enabled = should_fingerprint(pre_names, args.fingerprint_limit)
    pre_fingerprints = dirty_fingerprints(pre_names, workdir) if fingerprint_enabled else {}

    write_text(run_dir / "task.md", task_text)
    write_text(run_dir / "prompt.md", prompt)
    write_text(run_dir / "pre-status.txt", pre_status)
    write_text(run_dir / "pre-diff-stat.txt", pre_diff_stat)

    policy: dict[str, Any] = {
        "mode": mode,
        "workdir": str(workdir),
        "write_scope": write_scope,
        "policy_violation": False,
        "messages": [],
        "run_dir": str(run_dir),
        "dirty_file_count_before": len(pre_names),
        "fingerprint_enabled": fingerprint_enabled,
        "ignored_status_prefixes": args.ignore_status_prefix,
    }
    if pre_names and not fingerprint_enabled:
        policy["messages"].append(
            f"Fingerprint check skipped because dirty file count ({len(pre_names)}) exceeds limit ({args.fingerprint_limit})."
        )

    if mode == "worker" and not args.allow_dirty_overlap and pre_names:
        scoped_dirty = sorted(path for path in pre_names if in_scope(path, write_scope))
        pre_existing_dirty_outside_scope = sorted(path for path in pre_names if not in_scope(path, write_scope))
        if pre_existing_dirty_outside_scope:
            policy["pre_existing_dirty_outside_scope"] = pre_existing_dirty_outside_scope
        if scoped_dirty:
            policy["policy_violation"] = True
            policy["messages"].append(
                "BLOCKED: write scope overlaps existing dirty files. Re-run with --allow-dirty-overlap only if the orchestrator accepts this risk."
            )
            policy["dirty_overlap"] = scoped_dirty
            write_text(run_dir / "policy.json", json.dumps(policy, ensure_ascii=False, indent=2))
            write_text(run_dir / "result.md", render_result_md({"result": "blocked", "risks": policy["messages"]}, policy))
            print(run_dir)
            return 2

    if args.dry_run:
        result = {
            "result": "done",
            "summary": "Dry run only. Codex was not called.",
            "changed_files": [],
            "verification_run": [],
            "evidence": [f"Prompt written to {run_dir / 'prompt.md'}"],
            "findings": [],
            "risks": [],
            "next": "Run without --dry-run to dispatch Codex.",
        }
        write_text(result_json, json.dumps(result, ensure_ascii=False, indent=2))
    else:
        cmd = [
            "codex",
            "exec",
            "-C",
            str(workdir),
            "--dangerously-bypass-approvals-and-sandbox",
            "--json",
            "--output-schema",
            str(schema_path),
            "-o",
            str(result_json),
            prompt,
        ]
        proc = subprocess.run(
            cmd,
            cwd=str(workdir),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        write_text(events_jsonl, proc.stdout)
        write_text(stderr_path, proc.stderr)
        policy["codex_exit_code"] = proc.returncode
        if proc.returncode != 0:
            policy["policy_violation"] = True
            policy["messages"].append(f"Codex exited non-zero: {proc.returncode}")

    post_status = git_status(workdir)
    post_policy_status = filter_status(post_status, args.ignore_status_prefix)
    post_diff_stat = git_output(["diff", "--stat"], workdir)
    post_diff_names = git_output(["diff", "--name-only"], workdir)
    post_names = parse_status_names(post_policy_status)
    post_fingerprints = dirty_fingerprints(post_names, workdir) if fingerprint_enabled else {}

    write_text(run_dir / "post-status.txt", post_status)
    write_text(run_dir / "post-diff-stat.txt", post_diff_stat)
    write_text(run_dir / "post-diff-name-only.txt", post_diff_names)

    if fingerprint_enabled:
        changed_after = sorted(
            path for path, fingerprint in post_fingerprints.items() if pre_fingerprints.get(path) != fingerprint
        )
    else:
        changed_after = sorted(post_names - pre_names)
    modified_all = sorted(post_names)
    removed_dirty = sorted(pre_names - post_names)
    if mode in READ_ONLY_MODES and (post_fingerprints != pre_fingerprints or post_policy_status != pre_policy_status):
        policy["policy_violation"] = True
        policy["messages"].append(f"POLICY VIOLATION: {mode} mode changed working tree.")
        policy["changed_after"] = changed_after
        policy["removed_dirty"] = removed_dirty
        policy["modified_all"] = modified_all
    elif mode == "worker":
        out_of_scope = sorted(path for path in changed_after if not in_scope(path, write_scope))
        removed_out_of_scope = sorted(path for path in removed_dirty if not in_scope(path, write_scope))
        if out_of_scope:
            policy["policy_violation"] = True
            policy["messages"].append("POLICY VIOLATION: worker changed files outside WRITE SCOPE.")
            policy["out_of_scope_changes"] = out_of_scope
        if removed_out_of_scope:
            policy["policy_violation"] = True
            policy["messages"].append("POLICY VIOLATION: worker removed existing dirty files outside WRITE SCOPE.")
            policy["out_of_scope_removed"] = removed_out_of_scope

    result = load_json(result_json)
    write_text(run_dir / "policy.json", json.dumps(policy, ensure_ascii=False, indent=2))
    write_text(run_dir / "result.md", render_result_md(result, policy))

    print(run_dir)
    if policy["policy_violation"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
