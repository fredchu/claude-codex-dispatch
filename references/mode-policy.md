# Mode Policy

All modes call Codex with `--dangerously-bypass-approvals-and-sandbox`.

The wrapper enforces policy after the run by comparing git status snapshots.
When the dirty file count is at or below `--fingerprint-limit` (default 200), it
also fingerprints dirty files before and after the run so pre-existing dirty files
can be distinguished from Codex changes. Above that limit, it falls back to status
path comparison and records the degraded check in `policy.json`.

Volatile paths can be excluded from policy checks with `--ignore-status-prefix`.
The default ignore list includes `.tmp.driveupload/` because that directory can be
changed by external upload processes during an otherwise read-only Codex run. Full
pre/post status files are still written to the run artifact directory.

## worker

Worker mode may modify files inside `WRITE SCOPE`.

The wrapper blocks before dispatch if scoped files are already dirty, unless
`--allow-dirty-overlap` is passed. After dispatch, any changed file outside scope
is a policy violation.

## verifier

Verifier mode is read-only by contract. Codex gathers evidence, runs checks, and
decides whether a claim is supported. Any working-tree change is a policy violation.

## reviewer

Reviewer mode is read-only by contract. Findings should be listed first and should
include severity plus file/line references when possible. Any working-tree change
is a policy violation.

## synthesizer

Synthesizer mode is read-only by contract. It merges multiple agent outputs and must
preserve conflicts instead of forcing consensus. Any working-tree change is a policy
violation.
