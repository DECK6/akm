---
type: documentation
aliases:
  - "AKM Memory Runtime Playbook"
  - "Hermes memory operator playbook"
description: "Fail-closed operator procedure for scoped remember, explicit activation, bounded recall, guarded forget, rebuild, reconciliation, doctor, and promotion review in the AKM-native local memory runtime."
author:
  - "AKM Contributors"
date created: 2026-08-13
date modified: 2026-08-13
tags:
  - akm
  - memory
  - hermes
  - playbook
  - runtime
akmLayer: procedure
akmRole: executable-procedure
akmType: playbook
trustLevel: reviewed
CMDS: Develop
sourceType: synthesis
nextAction: verify
usedBy:
  - "[[MEMORY-RUNTIME]]"
provenance:
  - "https://github.com/garrytan/gbrain/tree/1ec6a6e842a15f2bde2ebe8c3a686a6fa6b17aa5"
adaptationBoundary: "Uses AKM's independent Markdown-authoritative adapter and excludes gbrain code, databases, services, and runtime data."
---

# AKM Memory Runtime Playbook

## 1. Purpose

Use this procedure to operate the local Hermes memory adapter without creating a competing canonical knowledge store. It covers the smallest safe path from candidate creation through scoped recall and reversible forget.

The operator contract is:

```text
security + exact scope
→ candidate remember or shadow extraction
→ source/decision review
→ explicit approve or reject
→ bounded scoped recall
→ attempted/selected/delivered audit
→ guarded forget when needed
→ rebuild + doctor readback
```

Global prompt injection is not part of this procedure. It remains `HOLD` until the shadow evaluation rubric passes.

## 2. Preconditions

Before running a command:

1. Read `99-system/MEMORY-RUNTIME.md`, `99-system/SECURITY.md`, and the relevant source Markdown.
2. Select an untracked runtime root outside the AKM repository. The adapter does not provide an in-repository default.
3. State the exact `source_id`, project, profile, and user. Do not omit a dimension merely to broaden recall.
4. Confirm no input contains secret values or auth/token/cookie/session/credential material.
5. Confirm source content will remain local; the adapter performs no external call.
6. For an external-model pack, confirm visibility is public/non-sensitive and egress was explicitly approved on each record.
7. Confirm the runtime root and fixed child directories are private real directories, not symlinks. Treat any post-initialization root-identity, symlink, hardlink, or non-regular-file validation error as a stop condition; never repair it by weakening the guard.

If any precondition is uncertain, stop with `HOLD`.

## 3. Common command prefix

Use the same scope on every step in one flow:

```bash
: "${AKM_RUNTIME_ROOT:?set this to an untracked directory outside the AKM repository}"
python3 -m adapters.hermes.memory \
  --root "$AKM_RUNTIME_ROOT" \
  --source-id akm \
  --project runtime-demo \
  --profile default \
  --user operator \
  <verb> <options>
```

The CLI writes successful JSON to stdout. It writes validated failures to stderr and exits with status 2. Treat a non-zero status as a stopped operation, even if a canonical record exists; inspect its receipt ID and reconcile.

## 4. Remember

### 4.1 Direct candidate

```bash
python3 -m adapters.hermes.memory \
  --root $AKM_RUNTIME_ROOT \
  --source-id akm --project runtime-demo --profile default --user operator \
  remember \
  --text "Use pointer-first retrieval." \
  --entity retrieval-policy \
  --kind preference \
  --stable-authority \
  --source-path 40-memory/operating-boundaries.md
```

Read back:

- `record.state` must be `candidate`;
- source path/lineage must identify the reviewed input;
- scope must exactly match the command;
- `receipt.canonical_status` and `derived_status` must both be `written`;
- `receipt.reconcile_status` must be `not_required`.

Do not interpret successful remember as permission to use the candidate in a prompt.

### 4.2 Deterministic shadow extraction

```bash
python3 -m adapters.hermes.memory \
  --root $AKM_RUNTIME_ROOT \
  --source-id akm --project runtime-demo --profile default --user operator \
  extract --input "Remember: Use pointer-first retrieval." --persist
```

Only explicit `Remember:`/`Memory:` lines are candidates. Ordinary text returns `nothing_salient`. Provider/refusal/filter/malformed/truncated failures must be submitted as their exact outcome through `provider-outcome`; never rewrite one as `nothing_salient`.

## 5. Review and explicit activation

Review the cited source directly. Check identity, scope, visibility, egress, kind, entity, TTL, and stable-authority flag. Then choose one:

```bash
# approve
python3 -m adapters.hermes.memory \
  --root $AKM_RUNTIME_ROOT \
  --source-id akm --project runtime-demo --profile default --user operator \
  approve --id mem_ID --decision-evidence "operator-readback:source-path#line"

# reject
python3 -m adapters.hermes.memory \
  --root $AKM_RUNTIME_ROOT \
  --source-id akm --project runtime-demo --profile default --user operator \
  reject --id mem_ID --decision-evidence "source-does-not-support-candidate"
```

Approval supersedes only the active record with the same entity, kind, and exact scope. Read back both IDs when supersession occurs. Preference/safety records marked stable authority cannot have a TTL.

## 6. Recall

### 6.1 Ordinary scoped recall

```bash
python3 -m adapters.hermes.memory \
  --root $AKM_RUNTIME_ROOT \
  --source-id akm --project runtime-demo --profile default --user operator \
  recall --query pointer-first --max-count 10
```

Expected result: active records only. Wrong-scope list recall returns no rows. Wrong-scope direct ID probes return `MemoryNotFound`, indistinguishable from a missing ID.

Add `--external-model` only after explicit egress review. Private/restricted items must remain absent even if an egress flag was mistakenly set.

### 6.2 Bounded context pack/reflex

```bash
python3 -m adapters.hermes.memory \
  --root $AKM_RUNTIME_ROOT \
  --source-id akm --project runtime-demo --profile default --user operator \
  context-pack \
  --entity-term retrieval-policy \
  --allowed-term retrieval-policy \
  --session-id task-123 \
  --max-count 3 \
  --token-budget 300 \
  --deliver
```

Gate the output:

1. `status` must be `ready`; a term outside the allowlist returns `HOLD` and no item.
2. Item count and token estimate must stay within declared budgets.
3. Each item must contain only identity, pointer, safe summary, freshness, conflict, and direct-read flag.
4. Any `conflict: HOLD` blocks unqualified injection.
5. Any `direct_read: true` requires direct source read before an important claim.
6. Repeat delivery under the same session must suppress the identical `record-id@revision`.

Do not copy receipts or `audit/usage.jsonl` into the prompt.

### 6.3 Delta recall

```bash
python3 -m adapters.hermes.memory \
  --root $AKM_RUNTIME_ROOT \
  --source-id akm --project runtime-demo --profile default --user operator \
  delta --cursor 2026-08-13T00:00:00Z
```

Persist the returned opaque `d1.` `next_cursor` unchanged in caller-owned task state only when needed. It carries the boundary timestamp plus already-seen event identities so same-timestamp lifecycle changes are neither lost nor duplicated. Legacy ISO timestamp cursors are migration input only. Delta events are lifecycle signals, not full evidence.

## 7. Promotion review

Queue a candidate for ROUTER review:

```bash
python3 -m adapters.hermes.memory \
  --root $AKM_RUNTIME_ROOT \
  --source-id akm --project runtime-demo --profile default --user operator \
  promote --id mem_ID --decision-evidence "candidate-and-source-reviewed"
```

Verify `canonical_write_performed: false`. The recommendation is advisory. A separate authorized workflow must:

1. follow `99-system/ROUTER.md` and inbox-first rules;
2. preserve source/candidate/decision evidence;
3. use AKM frontmatter and templates;
4. avoid direct automatic changes to the `40-memory/` surface;
5. update INDEX/LOG only when the canonical note workflow actually completes.

## 8. Guarded forget

### 8.1 Preview

```bash
python3 -m adapters.hermes.memory \
  --root $AKM_RUNTIME_ROOT \
  --source-id akm --project runtime-demo --profile default --user operator \
  forget --preview --id mem_ID --reason "incorrect-source-association"
```

For a scope-wide action, `--all-in-scope` is mandatory. Review count, exact IDs, states, revisions, checksums, and expiry. If any target is unexpected, do not confirm.

### 8.2 Confirm and read back

```bash
python3 -m adapters.hermes.memory \
  --root $AKM_RUNTIME_ROOT \
  --source-id akm --project runtime-demo --profile default --user operator \
  forget --confirm TOKEN_FROM_PREVIEW
```

The same-scope, unexpired, unused token must match unchanged canonical checksums. Confirmed output must report `readback.state: forgotten`. Then run rebuild and recall; the forgotten ID must remain absent.

### 8.3 Restore an erroneous fence

```bash
python3 -m adapters.hermes.memory \
  --root $AKM_RUNTIME_ROOT \
  --source-id akm --project runtime-demo --profile default --user operator \
  restore --id mem_ID --decision-evidence "operator-confirmed-fence-error"
```

Restore deactivates the fence with evidence. It does not delete history.

## 9. Rebuild, doctor, and reconcile

Run after an upgrade, derived-state loss, failed write, or suspicious recall:

```bash
python3 -m adapters.hermes.memory --root $AKM_RUNTIME_ROOT \
  --source-id akm --project runtime-demo --profile default --user operator rebuild

python3 -m adapters.hermes.memory --root $AKM_RUNTIME_ROOT \
  --source-id akm --project runtime-demo --profile default --user operator doctor
```

Doctor must be clean before resuming delivery. Treat these as blocking:

- DB/index-only or orphan ID;
- canonical-only or content-mismatched derived state;
- missing/malformed derived state while durable records exist;
- missing scope;
- checksum drift;
- malformed record/fence;
- record delivered after expiry;
- unresolved receipt.

For a receipt with canonical `written` and derived `failed`:

```bash
python3 -m adapters.hermes.memory --root $AKM_RUNTIME_ROOT \
  --source-id akm --project runtime-demo --profile default --user operator reconcile
```

Re-run doctor. Do not use reconcile to hide a canonical/manual failure.

## 10. Verification checklist

- [ ] Runtime root is local, untracked, and outside the AKM repository.
- [ ] Candidate starts non-governing.
- [ ] Approval/rejection evidence is present.
- [ ] Scope dimensions exactly match.
- [ ] Visibility and egress were evaluated separately.
- [ ] Count/token/entity allowlist bounds are explicit.
- [ ] Usage audit distinguishes attempted/selected/delivered.
- [ ] Duplicate identity is suppressed after actual delivery.
- [ ] Forget used preview, token, fence readback, rebuild, and recall.
- [ ] Doctor is clean.
- [ ] Promotion queue wrote no final-layer note.
- [ ] Global injection remains `HOLD` unless a future maintainer-approved gate changes it.

## 11. Learn Back

On false memory, scope leak, expired delivery, failed forget, hidden conflict, duplicate injection, or reconciliation failure:

1. stop delivery;
2. retain safe receipt/doctor output without secret data;
3. follow `99-system/LOOP.md` and record the failure under `70-evaluation/`;
4. repair the designated runtime/procedure/evaluation layer;
5. add a regression test before re-enabling the path;
6. rerun the conformance sequence `remember → recall → forget → rebuild → recall`.
