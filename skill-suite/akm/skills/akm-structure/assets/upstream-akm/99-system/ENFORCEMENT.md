# AKM Enforcement

AKM enforcement is a zero-dependency, read-only validation surface for operational artifacts that sit beside the Markdown knowledge layers. It extends `scripts/lint.mjs`; it does not create tasks, rewrite inputs, choose routes, or replace human verification.

## Modes

| Mode | Input | What it enforces |
|---|---|---|
| `--instructions` | JSON or Markdown manifest | Instruction assets have explicit scope, precedence, override edges, and no unresolved directive conflicts |
| `--task-contract` | JSON or Markdown contract | Bounded work declares exact inputs, outputs, ownership, failure handling, readback, runtime, and security exclusions |
| `--routing-failure` | JSON, JSONL, or Markdown ledger | Route misses, false positives, and misroutes stay metadata-only; closure requires a real correction and passing verification |
| `--prompt-assets` | JSON or Markdown manifest | Prompt/config assets use a deny-by-default allowlist with lifecycle, restore, path, size, and secret checks |

Each mode exits non-zero on an error. Unknown modes also fail closed.

## Input contract

- JSON inputs contain one object.
- JSONL is accepted for routing events and is normalized into an `entries` array.
- Markdown inputs contain exactly one fenced `json` object.
- Validators return deterministic summaries and safe metadata. They do not print instruction bodies, prompt bodies, secret values, or machine-absolute paths.

Runnable examples and negative fixtures live in `scripts/fixtures/enforcement/`.

## Commands

```sh
node scripts/lint.mjs --instructions path/to/instruction-manifest.json
node scripts/lint.mjs --task-contract path/to/task-contract.md
node scripts/lint.mjs --routing-failure path/to/failure-note.md
node scripts/lint.mjs --prompt-assets path/to/prompt-asset-manifest.json
```

For task contracts, start with `99-system/templates/task-contract.md` and read `99-system/TASK-CONTRACT-SCHEMA.md`. For routing failures, use the handoff block in `99-system/templates/failure-pattern.md`.

## Boundaries

- Enforcement validates declared structure and internal consistency. It cannot decide whether a source supports a claim or whether the work fulfills the user's intent; use `99-system/VERIFICATION.md`.
- A passing instruction manifest does not authorize an instruction to override a higher-precedence system or user rule.
- A passing task contract does not authorize external writes, spending, publishing, deletion, or any action beyond the user's scope.
- A prompt asset snapshot is inventory and recovery evidence, not a backup and never a reason to include auth, token, cookie, session, database, or log files.
- A routing event may store IDs, routes, hashes, and artifact counts. It must not store raw prompts, messages, sessions, credentials, or secret values.
