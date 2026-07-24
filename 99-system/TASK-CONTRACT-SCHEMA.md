# AKM Task Contract Schema

`task-contract.schema.json` is the machine-readable contract for bounded AKM work. The zero-dependency validator is the `--task-contract` mode of the existing `scripts/lint.mjs`; it does not modify the contract or any canonical note.

## Required surfaces

Every contract declares version, stable task identity, purpose, exact inputs and outputs, one canonical path, format rules, source roles, one primary owner, failure handling, completion gates, executable verification, bounded runtime, non-goals, security exclusions, and external blockers.

`blockedWhen` and `blockers` are reserved for external dependencies. Internal review, lint, test, or `PATCH_NEEDED` gates remain HOLD/FAIL conditions inside the same task. Every required output must have an exact `verification[].readback` path so audit-only work cannot terminalize an artifact-producing request.

This schema is only for bounded work: `runtime.goalMode` must be `false`, and `runtime.maxSeconds` must be at most 5,400 seconds (90 minutes). Open-ended work must be decomposed or explicitly routed outside this bounded contract instead of inheriting a blanket goal loop.

## Commands

```sh
cp 99-system/templates/task-contract.md /tmp/<task-id>-contract.md
# Fill every placeholder, then gate creation/dispatch:
node scripts/lint.mjs --task-contract /tmp/<task-id>-contract.md
```

Exit code is zero only when the contract passes. The helper path is intentionally copy → fill → lint → create/dispatch; the linter never rewrites its input. This gate rejects missing required outputs, placeholder values, internal review mislabeled as an external blocker, and required artifacts without exact readback verification.
