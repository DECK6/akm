---
type: documentation
aliases:
  - "AKM Memory Runtime Contract"
  - "Hermes local memory contract"
description: "Canonical AKM contract for scoped local memory candidates, lifecycle, reversible forget fences, disposable derived state, write reconciliation, bounded context packs, and shadow evaluation."
author:
  - "AKM Contributors"
date created: 2026-08-13
date modified: 2026-08-13
tags:
  - akm
  - memory
  - runtime
  - hermes
  - governance
schemaVersion: "1.0.0"
status: canonical
provenance:
  - "https://github.com/garrytan/gbrain/tree/1ec6a6e842a15f2bde2ebe8c3a686a6fa6b17aa5"
adaptationBoundary: "AKM independently implements selected lifecycle, fence, bounded-context, and delta concepts in a Markdown-authoritative local runtime; it does not vendor gbrain code, services, databases, or runtime data."
---

# AKM Memory Runtime

## 1. Purpose and authority

This document defines the AKM-native local memory runtime implemented at `adapters/hermes/memory/`. The machine-readable record companion is `99-system/memory-record.schema.json`.

The runtime is an adapter over AKM, not a second knowledge base:

1. AKM Markdown and original sources remain the sole canonical authority for knowledge, context, stable pointer rules, and procedures.
2. A runtime record is a scoped operational candidate or lifecycle projection. It never outranks its cited source.
3. Runtime Markdown records and forget fences are the durable local replay surface. The JSON index is disposable.
4. Generated candidates cannot write directly into `20-knowledge/`, `30-context/`, `40-memory/`, or `50-procedures/`.
5. `[[SECURITY]]`, `[[ROUTER]]`, `[[SCHEMA]]`, `[[EVIDENCE-SCHEMA]]`, and `[[LOOP]]` continue to govern secrets, classification, note structure, evidence, and Learn Back.

This contract adopts useful memory mechanics without installing or running gbrain and without importing its database-first authority model.

## 2. Non-negotiable invariants

| ID | Invariant | Runtime behavior |
|---|---|---|
| M1 | Canonical remains Markdown/original | A record carries a source path and lineage. Derived state says it is a projection, not source truth. |
| M2 | Derived state is disposable | Removing `derived/state.json` and running `rebuild` restores it from runtime Markdown records and fences. |
| M3 | Candidates do not govern | `remember` and extraction persist `candidate`; only an explicit approval can create `active`. |
| M4 | Failure is not absence | Provider, refusal, filter, malformed, and truncation outcomes remain distinct from `nothing_salient`. |
| M5 | Scope denies by default | `source_id` is mandatory. Every applicable project/profile/user dimension must exactly match. Unauthorized probes return `not_found`. |
| M6 | Visibility is not egress | Private/restricted never leave the local boundary. Public/non-sensitive still need an explicit egress bit. |
| M7 | Forget is durable and reversible | Every forget needs preview, exact token, Markdown fence, readback, and a reversible restore decision. |
| M8 | Partial writes are not success | Canonical success plus derived failure produces a failed command and unresolved receipt. |
| M9 | Retrieval is bounded | Context packs use allowlisted terms, stable identities, count/token caps, cursor suppression, and compact fields. |
| M10 | Prompt injection is not enabled globally | The bounded pack/reflex remains opt-in and global injection remains `HOLD` until the shadow rubric passes. |
| M11 | Audit is out-of-band | Attempted, selected, and delivered usage are distinguishable, but audit rows never enter prompt packs. |
| M12 | Risky ambiguity fails closed | Missing scope, malformed artifacts, stale confirmations, leaked gold, or uncertain conflicts produce `HOLD`/failure. |

## 3. Data model

### 3.1 Record identity

A record ID is a stable SHA-256-derived identity over normalized text, entity, kind, scope, and source path. Repeating the same input yields the same identity instead of a duplicate record. Revision increments only when lifecycle/decision state changes.

Required record groups are:

- stable ID, schema version, revision;
- lifecycle state and timestamps;
- text plus bounded safe summary;
- kind and entity;
- exact scope dimensions;
- visibility and independent egress decision;
- source path and lineage;
- optional TTL and stable-authority flag;
- supersession links;
- decision/extraction evidence and lifecycle history.

### 3.2 Lifecycle

```text
candidate ──explicit approve──> active
candidate ──explicit reject───> rejected (terminal unless forgotten)
active ──new approved same entity/kind/scope──> superseded
active ──TTL reached──────────────────────────> expired
candidate|active|superseded|expired|rejected ──confirmed fence──> forgotten
forgotten ──explicit restore evidence──> prior recorded lifecycle state
```

The local derived index computes TTL expiry. Stable `preference` and `safety` authority cannot be given a TTL and therefore cannot auto-expire. A changing preference or safety rule must be explicitly superseded, rejected, or forgotten with evidence.

### 3.3 Supersession

Approval finds an existing active record only within the exact same scope, kind, and entity. The old record becomes `superseded`, its revision/history changes, and its `superseded_by` points to the new record. The new record records `supersedes`. Similar text in another project/profile/user never supersedes across the scope boundary.

### 3.4 TTL

TTL is a positive number of seconds set at remember time. Expired items are excluded from ordinary recall and context packs but stay visible to `get(..., include_inactive=True)`, delta recall, doctor, and rebuild. Expiry does not delete its source or history.

## 4. Extraction boundary

The exact outcome type is:

| Outcome | Meaning |
|---|---|
| `success` | Valid candidate list exists. |
| `nothing_salient` | Processing completed normally and produced no candidate. |
| `provider_error` | An explicitly external provider boundary reported operational failure. |
| `refusal` | Provider refused. |
| `content_filter` | Provider filtered the request/output. |
| `malformed_output` | The supplied output does not match the candidate boundary. |
| `truncated_output` | The supplied provider result is incomplete. |

`extract_local` is deterministic and recognizes only explicit `Remember:` or `Memory:` lines. `ingest_provider_boundary` validates an already-produced outcome/payload. Neither method invokes a model or network. Persisted extraction results remain shadow candidates and are never injected or promoted automatically.

## 5. Storage and rebuild

The operator supplies a local runtime root. No default inside the tracked repository is allowed. The constructor detects AKM roots through `99-system/SCHEMA.md` plus `99-system/ROUTER.md` and rejects any runtime root at or below that canonical vault.

```text
records/*.md             durable runtime records
fences/*.md              durable reversible forget fences
receipts/*.json          write/reconciliation receipts
previews/*.json          short-lived destructive previews
promotion-queue/*.json   classification recommendations
cursors/*.json           delivered identity cursor
audit/usage.jsonl        out-of-band usage stages
derived/state.json       disposable state/index
```

Records and fences use explicit markers plus strict JSON code blocks so rebuild can parse them without a YAML dependency. An invalid marker, block, ID, scope, lifecycle, timestamp, or filename relation is excluded and reported rather than guessed.

Runtime file access is fail-closed after construction as well as at initial root selection. Every read, append, checksum, and atomic replacement traverses the selected root and fixed child directories through directory file descriptors with `O_NOFOLLOW`, verifies that the runtime root device/inode did not change, and accepts only single-link regular files. Replacing the root or a child directory with a symlink, or inserting a hardlinked audit/file artifact, raises a validation error rather than reading or writing outside the selected root.

`rebuild`:

1. enumerates regular non-symlink record Markdown;
2. validates each record and filename identity;
3. enumerates and validates forget fences;
4. computes TTL and active fence state;
5. recomputes source-file checksums;
6. atomically replaces the derived JSON index;
7. reports malformed artifacts.

Rebuild never reads or modifies canonical 20/30/40/50 notes.

## 6. Write receipts and reconciliation

Every state-changing operation writes a receipt with:

- operation and affected stable IDs;
- canonical status;
- derived status;
- canonical SHA-256 checksum(s);
- record revision;
- failure detail;
- reconcile state and completion time.

The write order is canonical runtime Markdown first, derived index second. Therefore a derived success with canonical failure is structurally impossible. A canonical success followed by a derived failure raises `MemoryWriteError`, exits non-zero through the CLI, and leaves `reconcile_status: retry_required`.

`reconcile` first performs a full rebuild. Only after that succeeds does it mark retry-required receipts reconciled. A manual canonical failure is not auto-cleared.

## 7. Scope, visibility, and egress

### 7.1 Scope

Every record needs `source_id`. `project`, `profile`, and `user` may be null only when that dimension is intentionally not applicable. For every non-null record dimension the caller must provide an exact match.

List/query recall silently omits denied records. Direct get/forget/egress probes return the same `MemoryNotFound` response for nonexistent and unauthorized IDs. This prevents existence disclosure.

### 7.2 Visibility versus egress

| Visibility | Internal scoped recall | External-model egress |
|---|---:|---:|
| `public` | allowed | only with `egress_allowed: true` |
| `non_sensitive` | allowed | only with `egress_allowed: true` |
| `private` | allowed | denied |
| `restricted` | allowed | denied |

The visibility label never implies permission to transmit. The egress bit never overrides private/restricted denial.

## 8. Destructive guard and forget fence

Forget has two mandatory phases.

### Preview

The preview resolves exact authorized records and records count, IDs, lifecycle states, revisions, current checksums, scope, reason, creation time, and 15-minute expiry. A mass preview requires explicit `all_in_scope`; omission is not interpreted as “all.”

### Confirm

Confirmation must present the exact token under the same scope. The runtime rejects missing, expired, reused, cross-scope, and checksum-stale tokens. It writes one Markdown fence per record, reads each back, then rebuilds. Ordinary recall after rebuild omits forgotten records.

The token value itself is stored only in the preview; the durable fence carries its SHA-256 hash. Restore explicitly marks the fence inactive with decision evidence, preserving history instead of deleting the fence.

## 9. Recall surfaces

### 9.1 Ordinary recall

Ordinary recall returns active, authorized, egress-eligible records within a hard maximum. Its state filter is fixed to `active`; callers cannot request candidate, rejected, superseded, expired, or forgotten rows through this surface. Direct inactive `get(..., include_inactive=True)` is an internal operator path and denies all external-model requests unless the record is active. Other inactive lifecycle inspection uses explicit operator verbs such as `status`, `doctor`, or `delta` and is never used for a normal prompt pack.

### 9.2 Bounded reflex/context pack

The caller supplies entity/project terms and a separate allowlist. Every requested term must be allowlisted; otherwise the result is `HOLD` with no items. The pack applies:

- exact scoped active records only;
- optional `since` timestamp;
- maximum count 1–20;
- token estimate budget 1–4000;
- stable injection identity `record-id@revision`;
- per-session delivered cursor suppression.

Each item contains only:

```text
identity
pointer
safe_summary
freshness
conflict
direct_read
```

No full evidence, full audit, receipt, source body, or usage record is included. `direct_read: true` tells the caller that the compact summary is insufficient. A same-entity active conflict becomes `HOLD` in the item and cannot be silently averaged.

### 9.3 Delta recall

Delta recall returns `created`, `modified`, `superseded`, `expired`, and `forgotten` events after an optional cursor, plus a new opaque `d1.` cursor. The cursor records both its UTC boundary time and stable identities for events already observed exactly at that boundary; a later lifecycle event with the same timestamp is therefore delivered once rather than skipped or repeated. Legacy ISO timestamp cursors remain accepted with strict-after semantics, and future-dated cursors fail closed. Delta draws lifecycle events from record Markdown and forgotten events from fences, so rebuild does not erase change history.

## 10. Promotion queue

`promote` is intentionally a queue verb, not a canonical write verb, and accepts only a current `candidate` (never `rejected`). It records:

- candidate ID/revision/checksum;
- source and scope;
- candidate/decision evidence;
- recommended ROUTER destination;
- `canonical_write_performed: false`.

Recommendations are kind-sensitive (`30-context/` for preferences, `50-procedures/` for procedures, and a ROUTER decision for facts). A human/operator must then follow `[[ROUTER]]`, inbox-first rules, frontmatter schema, evidence checks, INDEX update, and LOG rules in a separate canonical-authorized workflow.

## 11. Doctor

`doctor` is a fail-closed consistency audit. It reports:

| Check | Failure meaning |
|---|---|
| `orphan` / `db_only` | Derived ID lacks a durable record Markdown file. |
| `canonical_only` | Durable record is absent from derived state and needs rebuild. |
| `canonical_drift` | Derived record content differs from the lifecycle state recomputed from Markdown/fences. |
| `derived_state_error` | Derived state is missing while records exist, or its JSON is malformed. |
| `expired_but_recalled` | Usage audit says a record was delivered at or after expiry. |
| `missing_scope` | Canonical or derived row lacks mandatory `source_id`. |
| `unresolved_receipts` | A write needs retry/manual reconciliation. |
| `malformed_records` | Record marker/JSON/schema/identity validation failed. |
| `malformed_fences` | Fence marker/JSON/scope/identity validation failed. |
| `checksum_drift` | Derived checksum differs from the current durable Markdown bytes. |

The CLI returns non-zero when doctor is not clean. The operator may run `reconcile` for retry-required derived failures. Malformed or manual canonical failures require readback and an explicit repair; they are never auto-normalized.

## 12. Usage audit and duplicate suppression

Each bounded retrieval records separate events for:

1. `attempted`: authorized records considered after allowlisted term matching;
2. `selected`: records that fit count/token/conflict policy;
3. `delivered`: items actually handed to the opted-in consumer.

Only delivery updates a session cursor. An attempted or selected item that was not delivered remains eligible later. Stable identity includes revision, so a legitimately revised record may be delivered after the old revision while exact duplicates are suppressed.

Usage audit is diagnostic input to metrics and doctor only. It never enters the context pack.

## 13. Evaluation boundary and metrics

Runtime fixtures must not contain `gold`, `answer`, `answers`, `expected`, or equivalent sealed-answer keys at any depth. Runtime result artifacts contain query IDs and selected IDs only. `HoldoutEvaluator` opens sealed gold only after the result file already exists and reports aggregate exact match; it never passes gold to runtime retrieval.

The fixed metric surface is:

- false-memory rate;
- duplicate-injection rate;
- conflict-exposure rate;
- usefulness rate;
- token cost;
- latency;
- manual-correction rate;
- source/lineage recovery rate.

No-observation rates are `null`, never invented as zero. Thresholds and promotion gates are defined in the [memory runtime evaluation rubric](../adapters/hermes/memory/EVALUATION.md).

## 14. Operator states

| Surface | Current state |
|---|---|
| Local remember/recall/status | implemented |
| Explicit approve/reject | implemented |
| Guarded forget/restore | implemented |
| Rebuild/reconcile/doctor | implemented |
| Local explicit-marker extraction | implemented, shadow only |
| Provider outcome boundary | implemented, no provider invocation |
| Bounded context pack/reflex | implemented, opt-in |
| Global prompt injection | `HOLD` |
| Automatic canonical promotion | prohibited |
| External/cloud service | absent |

## 15. Recovery and rollback

The runtime root is disposable operational state except for local Markdown records/fences needed to preserve lifecycle decisions. Back up those Markdown artifacts before a runtime-root migration. To roll back an adapter version, revert the version-controlled adapter and documentation changes; never remove or rewrite cited AKM originals.

For an individual memory error:

1. stop context delivery;
2. run `doctor` and retain its JSON output;
3. run `reconcile` only for a derived-write receipt failure;
4. use confirmed forget for an invalid memory, or explicit restore for an erroneous fence;
5. rebuild and recall under the exact scope;
6. record a Learn Back evaluation under `70-evaluation/` if the failure exposed a recurring process defect.
