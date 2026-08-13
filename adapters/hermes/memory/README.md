# Hermes AKM memory runtime

This package is a local, fail-closed memory adapter. It does not replace AKM, install gbrain, call a model, or write generated text into `20-knowledge/`, `30-context/`, `40-memory/`, or `50-procedures/`.

The operator must supply an untracked runtime root outside the AKM repository. The adapter has no in-repository default and rejects roots beneath a directory identified by both `99-system/SCHEMA.md` and `99-system/ROUTER.md`. Durable local records and forget fences are Markdown. `derived/state.json` is disposable and `rebuild` recreates it from those Markdown artifacts.

## Provenance and adaptation boundary

The design adapts selected memory lifecycle, durable forget-fence, bounded-context, and delta/cursor concepts from [gbrain at commit `1ec6a6e842a15f2bde2ebe8c3a686a6fa6b17aa5`](https://github.com/garrytan/gbrain/tree/1ec6a6e842a15f2bde2ebe8c3a686a6fa6b17aa5). gbrain is Copyright (c) 2026 Garry Tan and is MIT-licensed, which is compatible with this repository's MIT license. This adapter is an independent Python implementation: it does not copy or vendor gbrain source code, install gbrain, adopt its database-first authority model, or include gbrain runtime data.

## Safety boundary

- A remembered item starts as `candidate`; only `approve` makes it `active`.
- Ordinary `recall` is active-only and exposes no lifecycle-state override; candidates are available only to explicit review/decision operations. Even an internal inactive `get` cannot return a candidate to an external-model request.
- `promote` means “put a candidate in the ROUTER review queue.” It never writes a final AKM note.
- `private` and `restricted` items are never eligible for external-model egress. Other visibility classes still require explicit `--egress-allowed`.
- Every record is scoped by `source_id` and, when present, `project`, `profile`, and `user`. Missing/mismatched scope is denied as `not_found`.
- `forget` always requires an exact impact preview and its short-lived confirmation token. The resulting Markdown fence is read back and can be explicitly restored.
- Global prompt injection is `HOLD`. `context-pack`/`reflex` is an opt-in bounded surface for shadow evaluation.
- The runtime never reads authentication, token, cookie, session, or credential stores and never makes a network/model call.
- Runtime reads and writes use no-follow directory/file descriptors, preserve the initially selected root identity, and reject post-initialization root/child symlink replacement or hardlinked artifacts.

## CLI

From the AKM root, first provide an external local directory:

```bash
: "${AKM_RUNTIME_ROOT:?set this to an untracked directory outside the AKM repository}"
python3 -m adapters.hermes.memory \
  --root "$AKM_RUNTIME_ROOT" \
  --source-id akm --project runtime-demo --profile default --user operator \
  remember \
  --text "Use pointer-first retrieval." \
  --entity retrieval-policy \
  --source-path 40-memory/operating-boundaries.md
```

All successful commands emit one JSON object to stdout. Validated failures emit one JSON object to stderr and exit non-zero.

Explicitly approve the returned record ID:

```bash
python3 -m adapters.hermes.memory \
  --root "$AKM_RUNTIME_ROOT" \
  --source-id akm --project runtime-demo --profile default --user operator \
  approve --id mem_REPLACE_ME --decision-evidence operator-reviewed-source
```

Recall or create a compact, allowlisted context pack:

```bash
python3 -m adapters.hermes.memory \
  --root "$AKM_RUNTIME_ROOT" \
  --source-id akm --project runtime-demo --profile default --user operator \
  recall --query pointer-first

python3 -m adapters.hermes.memory \
  --root "$AKM_RUNTIME_ROOT" \
  --source-id akm --project runtime-demo --profile default --user operator \
  context-pack \
  --entity-term retrieval-policy --allowed-term retrieval-policy \
  --session-id demo-1 --max-count 3 --token-budget 300 --deliver
```

`context-pack` returns only stable identity, pointer, safe summary, freshness, conflict/HOLD, and direct-read flag. Full evidence, receipts, and usage audit never enter the pack. Reusing the session cursor suppresses an already delivered `record-id@revision`.

`delta` returns an opaque `d1.` cursor. Persist and pass it back unchanged; do not parse or replace it with a newly sampled timestamp. Legacy ISO cursors remain accepted for strict-after migration compatibility, while the opaque cursor also prevents loss of events created at the same timestamp boundary. Future-dated cursors are rejected.

Preview and confirm forget as two separate commands:

```bash
python3 -m adapters.hermes.memory \
  --root "$AKM_RUNTIME_ROOT" \
  --source-id akm --project runtime-demo --profile default --user operator \
  forget --preview --id mem_REPLACE_ME --reason operator-request

python3 -m adapters.hermes.memory \
  --root "$AKM_RUNTIME_ROOT" \
  --source-id akm --project runtime-demo --profile default --user operator \
  forget --confirm REPLACE_WITH_PREVIEW_TOKEN
```

Recovery is explicit:

```bash
python3 -m adapters.hermes.memory \
  --root "$AKM_RUNTIME_ROOT" \
  --source-id akm --project runtime-demo --profile default --user operator \
  restore --id mem_REPLACE_ME --decision-evidence operator-reversed-forget
```

## Extraction boundary

`extract --input 'Remember: ...' --persist` is a deterministic local parser for explicit `Remember:` or `Memory:` lines. Persisted output remains a shadow candidate. `provider-outcome` accepts already-produced provider output at an explicit boundary; it does not invoke a provider.

The outcome vocabulary is exact:

```text
success
nothing_salient
provider_error
refusal
content_filter
malformed_output
truncated_output
```

A processing failure is never rewritten as `nothing_salient`.

## Rebuild, reconciliation, and doctor

```bash
python3 -m adapters.hermes.memory --root "$AKM_RUNTIME_ROOT" \
  --source-id akm --project runtime-demo --profile default --user operator rebuild

python3 -m adapters.hermes.memory --root "$AKM_RUNTIME_ROOT" \
  --source-id akm --project runtime-demo --profile default --user operator reconcile

python3 -m adapters.hermes.memory --root "$AKM_RUNTIME_ROOT" \
  --source-id akm --project runtime-demo --profile default --user operator doctor

python3 -m adapters.hermes.memory --root "$AKM_RUNTIME_ROOT" \
  --source-id akm --project runtime-demo --profile default --user operator status
```

`doctor` exits non-zero through the CLI when it finds DB/index-only rows, canonical-only/mismatched derived rows, missing or malformed derived state, missing scope, unresolved receipts, malformed records/fences, checksum drift, or a record delivered after expiry. `reconcile` rebuilds derived state first, then resolves receipts whose canonical Markdown succeeded while derived writing failed.

## Runtime layout

```text
<runtime-root>/
  records/*.md             durable candidate/lifecycle records
  fences/*.md              durable reversible forget fences
  receipts/*.json          canonical/derived write receipts
  previews/*.json          short-lived destructive previews
  promotion-queue/*.json   ROUTER recommendations; no canonical write
  cursors/*.json           delivered identity suppression
  audit/usage.jsonl        attempted/selected/delivered usage only
  derived/state.json       disposable index rebuilt from Markdown
```

Do not place this root in the AKM repository. Tests use pytest-managed temporary directories only. If the root or any fixed child directory is replaced or linked after initialization, stop the consumer, restore a clean private runtime directory, and rerun `rebuild` plus `doctor`; do not bypass the validation error.

## Operator and evaluation guides

- [Operator playbook](PLAYBOOK.md)
- [Evaluation rubric](EVALUATION.md)

## Test

The focused test requires `pytest` and `jsonschema` in the active Python environment:

```bash
PYTHONPYCACHEPREFIX="$AKM_RUNTIME_ROOT/pycache" \
  python3 -m py_compile adapters/hermes/memory/*.py
python3 -m pytest adapters/hermes/memory/tests/test_memory_runtime.py -q -p no:cacheprovider
```
