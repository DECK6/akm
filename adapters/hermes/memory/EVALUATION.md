---
type: documentation
aliases:
  - "AKM Memory Runtime Evaluation"
  - "AKM memory shadow promotion rubric"
description: "Preregistered conformance, safety, holdout, quality, cost, and promotion gates for the AKM-native local memory runtime and its opt-in bounded context pack."
author:
  - "AKM Contributors"
date created: 2026-08-13
date modified: 2026-08-13
tags:
  - akm
  - memory
  - evaluation
  - rubric
  - holdout
  - safety
akmLayer: evaluation
akmRole: verification-rule
akmType: rubric
trustLevel: reviewed
CMDS: Develop
sourceType: synthesis
nextAction: verify
usedBy:
  - "[[adapters/hermes/memory/PLAYBOOK]]"
provenance:
  - "https://github.com/garrytan/gbrain/tree/1ec6a6e842a15f2bde2ebe8c3a686a6fa6b17aa5"
adaptationBoundary: "Evaluates AKM's independent Markdown-authoritative runtime; gbrain code, databases, services, and runtime data are outside scope."
---

# AKM Memory Runtime Evaluation

## 1. Purpose and current verdict

This rubric separates implementation conformance from permission to inject runtime memory globally. The local runtime may pass its deterministic conformance harness while global prompt injection remains `HOLD`.

Current preregistered state:

| Surface | Gate |
|---|---|
| Local candidate lifecycle/CLI | eligible after all mandatory conformance tests pass |
| Opt-in bounded pack/reflex | shadow/pilot only |
| External-model pack | deny by default; per-record egress gate plus shadow evaluation |
| Automatic canonical promotion | prohibited |
| Global prompt injection | `HOLD` until this rubric passes on sealed holdout data and receives explicit operator approval |

Passing tests does not self-authorize rollout.

## 2. Evaluation isolation

Use three separate locations under a temporary evaluation root:

```text
fixtures/runtime/       query/input cases visible to runtime
results/runtime/        immutable runtime outputs before scoring
sealed-gold/evaluator/  expected IDs/labels visible only to evaluator
```

Requirements:

1. Runtime fixture IDs are stable and unique.
2. Runtime fixtures contain no `gold`, `answer`, `answers`, `expected`, `expected_ids`, or equivalent answer-bearing key at any depth.
3. Result files are written and checksummed before the evaluator reads sealed gold.
4. Runtime code receives fixture and runtime root only, never a gold path or answer object.
5. Gold and result artifact paths must not be identical, nested, colocated, or merged.
6. A leak, duplicate case ID, result mutation after scoring, or evaluator/runtime path overlap is `FAIL`.

## 3. Mandatory conformance harness

Every implementation revision must pass all rows:

| ID | Scenario | Required observation |
|---|---|---|
| C1 | remember → recall → forget → rebuild → recall | Candidate requires approval; active is recalled; confirmed fence hides it; rebuild preserves forgotten state. |
| C2 | scope isolation | Wrong source/project/profile/user sees no list result and an ID probe returns `not_found`. |
| C3 | private egress | Private/restricted is absent from external-model output even if egress flag is true. |
| C4 | TTL | Expiring active record is excluded after expiry; inactive inspection reports `expired`. |
| C5 | stable authority | Stable preference/safety rejects TTL and remains active until explicit lifecycle decision. |
| C6 | supersession | New approved same-scope entity supersedes old; links/history survive rebuild. |
| C7 | extraction outcome | Each of seven outcomes remains distinct; failure is never counted as no salience. |
| C8 | write reconciliation | Canonical success/derived failure exits non-zero, preserves unresolved receipt, and reconcile rebuilds before closing it. |
| C9 | destructive confirmation | Missing/stale/cross-scope/reused token fails; mass action needs explicit `all_in_scope`; fence is read back. |
| C10 | doctor | Detects DB-only/orphan, canonical-only/content drift, missing/malformed derived state, missing scope, malformed fence/record, unresolved receipt, checksum drift, expired delivery. |
| C11 | shadow candidates | Extraction cannot activate, inject, or promote automatically. |
| C12 | bounded reflex | Non-allowlisted term returns HOLD; count/token limits hold; compact fields only. |
| C13 | duplicate suppression | Same `record-id@revision` is not delivered twice after cursor update. |
| C14 | delta recall | Created, modified, superseded, expired, and forgotten changes appear strictly after cursor. |
| C15 | promotion queue | Recommendation/evidence persists but no 20/30/40/50 write occurs. |
| C16 | usage audit | Attempted, selected, delivered are distinct; audit is absent from pack. |
| C17 | CLI failure semantics | Success JSON uses stdout; validation/write/doctor failure uses non-zero and JSON stderr. |
| C18 | derived rebuild | Removing/replacing the derived index cannot create or erase durable record/fence meaning. |

Any missing scenario is `NOT_TESTED`, not a pass.

## 4. Adversarial security set

The sealed suite must include:

- missing and partially missing scope;
- project/profile/user crossover probes;
- candidate-state override attempts through ordinary recall and CLI;
- private/restricted egress with egress flag true;
- external-model call with egress flag false;
- path traversal, post-initialization root/child symlink replacement, and hardlink artifact attempts;
- malformed Markdown marker/JSON fence;
- forged derived-only ID;
- checksum drift between preview and confirm;
- reused/expired/cross-scope confirmation token;
- same-timestamp delta events after cursor issuance, repeated opaque-cursor replay, and malformed opaque cursors;
- candidate or rejected item offered for injection;
- stable preference/safety with TTL;
- gold/expected answer key nested inside a fixture;
- duplicate identity through reordered retrieval;
- expired record delivered from stale cursor/index;
- conflict presented as unqualified fact;
- provider failure mislabeled as `nothing_salient`.

Required threshold: zero unauthorized disclosure, zero destructive bypass, zero answer leakage, and zero candidate-as-active events.

## 5. Metric definitions

Use one observation row per attempted memory-assisted task. Missing labels stay missing; do not silently coerce them to false.

### 5.1 False memory

A delivered memory is false when direct source/lineage recovery shows that the summary is unsupported, materially wrong, stale without an expiry/conflict signal, or attached to the wrong entity/scope.

```text
falseMemoryRate = falseDeliveredMemories / evaluatedDeliveredMemories
```

### 5.2 Duplicate injection

A duplicate is the same stable `record-id@revision` delivered more than once to the same session after the first actual delivery.

```text
duplicateInjectionRate = duplicateDeliveries / totalDeliveries
```

Attempts and selections that were not delivered are not duplicates.

### 5.3 Conflict exposure

A failure occurs when two active eligible memories conflict and the pack does not expose `HOLD`/conflict before synthesis.

```text
conflictExposureRate = hiddenBlockingConflicts / evaluatedBlockingConflicts
```

For promotion this is an error rate and must be zero.

### 5.4 Usefulness

A memory is useful only when a blinded evaluator says it reduced source recovery effort or improved a task-relevant answer without adding a false/duplicate/hidden-conflict failure.

```text
usefulnessRate = usefulAssistedTasks / evaluatedAssistedTasks
```

### 5.5 Token cost and latency

Record actual delivered context tokens using the named downstream tokenizer/provider counter when a model is involved. The runtime's character heuristic is a budget guard, not a scored token measurement. Record end-to-end retrieval latency in milliseconds, median, p95, and fixture size.

### 5.6 Manual correction

```text
manualCorrectionRate = assistedTasksNeedingMemoryCorrection / evaluatedAssistedTasks
```

Corrections include wrong scope, wrong entity, stale preference, missing conflict, unsafe egress, or bad summary.

### 5.7 Source/lineage recovery

```text
sourceLineageRecoveryRate = deliveredMemoriesWithRecoverableCorrectSource / evaluatedDeliveredMemories
```

Recovery requires the pointer to open the intended canonical Markdown/original source and the lineage to explain the candidate decision. A plausible path string alone does not pass.

## 6. Shadow comparison design

Freeze before measurement:

1. public/non-sensitive and separately local-private fixture partitions;
2. exact scopes and egress modes;
3. task/query texts without answers;
4. sealed expected memory IDs/source pointers;
5. baseline route with no memory pack;
6. prototype route with opt-in bounded pack;
7. max count/token budget and allowlisted terms;
8. timeout/latency measurement boundary;
9. evaluator identities and adjudication rule;
10. hashes of fixture, runtime version, and gold.

Run baseline and prototype on the same tasks. Randomize presentation order to blinded usefulness evaluators. Do not tune weights, summaries, caps, or allowlists on holdout cases; tuned cases become development fixtures and require replacement holdouts.

## 7. Promotion gates

### 7.1 Local runtime gate

All mandatory conformance and adversarial tests must pass. Python compilation, combined pytest, enforcement, task-contract lint, schema parse, real CLI smoke, and readback must all exit 0. Doctor must be clean at the end of the smoke flow.

### 7.2 Opt-in bounded pack pilot

Minimum sealed evaluation size: 50 tasks, including at least:

- 10 scope/isolation cases;
- 10 freshness/TTL/supersession cases;
- 10 duplicate/cursor/delta cases;
- 10 conflict/source-recovery cases;
- 10 usefulness/cost cases.

Required pilot thresholds:

| Metric | Threshold |
|---|---:|
| Unauthorized scope/egress disclosures | 0 |
| Destructive confirmation bypasses | 0 |
| False-memory rate | ≤ 1% |
| Duplicate-injection rate | 0% |
| Hidden blocking conflict rate | 0% |
| Source/lineage recovery | 100% |
| Manual correction | ≤ baseline and ≤ 5% |
| Usefulness | ≥ 70% of scored assisted tasks |
| Median delivered memory tokens | ≤ frozen budget and no baseline task regression > 10% without adjudicated benefit |
| Median latency | ≤ 100 ms local; p95 ≤ 250 ms on frozen fixture machine |

Threshold changes after observing holdout results require a new rubric version and fresh sealed set.

### 7.3 Global injection gate

Global injection remains `HOLD` even after one pilot pass. Enabling it requires all of:

1. two consecutive sealed pilot passes on different frozen fixtures;
2. no regression in the existing retrieval suite;
3. explicit operator approval recorded in canonical AKM context;
4. an explicit rollback switch and proof that disabling injection leaves remember/doctor intact;
5. updated adapter/profile guidance and scoped lint;
6. no change to `40-memory/` structure unless separately approved under the repository's routing rules;
7. live retrieval verification using the adopter's configured local search path in the same authorized rollout run.

Until then, status must continue to report `global_injection: HOLD`.

## 8. Required result artifact

The evaluator result must record:

- runtime/schema revision and checksums;
- fixture/result/gold paths and separate hashes;
- scope and egress partition counts;
- conformance case counts and exact failures;
- all metric numerators/denominators, not percentages alone;
- token method, latency clock boundary, and machine/runtime identity;
- false-memory and conflict adjudication notes without leaking private contents;
- doctor/status outputs;
- final `PASS`, `HOLD`, `FAIL`, or `NOT_TESTED`;
- rollback action.

The result cannot modify runtime outputs after gold is opened.

## 9. Stop and rollback conditions

Immediately stop delivery and set `FAIL` for scope/egress disclosure, destructive bypass, answer leakage, canonical-layer automatic write, candidate-as-active injection, or a normal-success response after partial write failure.

Set `HOLD` for insufficient cases, unresolved receipt, malformed fence, source drift, missing conflict adjudication, ambiguous scope, missing direct-read pointer, or threshold not yet measured.

Recovery follows the [memory runtime playbook](PLAYBOOK.md): disable delivery, retain safe diagnostics, reconcile only eligible derived failures, use confirmed forget/restore, rebuild, run doctor, add a regression test, and follow `[[LOOP]]` for recurring defects.
