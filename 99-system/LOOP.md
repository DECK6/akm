# AKM-LOOP

The seven-step operating loop the AKM system repeats. Every adapter (harness) follows this loop.

```text
1. Ingest → 2. Classify → 3. Compile → 4. Contextualize → 5. Execute → 6. Verify → 7. Learn Back
                                                                                        │
                                                  ┌─────────────────────────────────────┘
                                                  ▼
                                   (the fixed layer improves the input quality of the next loop)
```

Accumulating knowledge without steps 5–7 is just a wiki. Repeating step 5 without 6–7 is just automation. Neither is AKM.

## Step definitions

### 1. Ingest

| | |
|---|---|
| Input | External material, user input, execution logs, deliverables, feedback |
| Output | Original snapshot in `10-sources/` (or an input awaiting classification) |
| Layer | Source |
| On failure | If provenance (sourcePath) or intake date is unknown, keep it with `trustLevel: raw` + `nextAction: triage` and move on |

### 2. Classify

| | |
|---|---|
| Input | Ingested material, or directly arriving experience / rules / requests |
| Output | Storage decision (layer + akmType) |
| Layer | All (via ROUTER) |
| On failure | If the [[ROUTER]] tree cannot classify it, the ROUTER is incomplete — record it in `70-evaluation/audits/` and fix the ROUTER |

### 3. Compile

| | |
|---|---|
| Input | Originals in `10-sources/` |
| Output | concept / entity / comparison / pattern / tool / technique notes in `20-knowledge/` |
| Layer | Source → Knowledge |
| On failure | If synthesis quality is uncertain, store with `trustLevel: unverified` and `nextAction: verify`. Never modify or delete the original |

### 4. Contextualize

| | |
|---|---|
| Input | Knowledge in `20-knowledge/` |
| Output | Links to projects / users / domains in `30-context/`, updated `usedBy` fields |
| Layer | Knowledge → Context |
| On failure | If no context exists to connect yet, leave `nextAction: contextualize` and move on (never force a connection) |

### 5. Execute

| | |
|---|---|
| Input | A task request + `40-memory/` pointers + `50-procedures/` procedures + relevant knowledge/context |
| Output | The actual work result. If worth keeping: `60-actions/` or `80-outputs/` |
| Layer | Memory + Procedure + Knowledge + Context → Action |
| On failure | The failure itself becomes the input of step 7 (Learn Back). Never discard failures |

### 6. Verify

| | |
|---|---|
| Input | The result of Execute |
| Output | Tiered verification result — on pass, promote trustLevel only when evidence supports it; on fail, record the finding |
| Layer | Evaluation |
| On failure | Select Tier 0–3 and the applicable checks in [[VERIFICATION]]. If no criteria exist, that itself is the finding — create the rubric first in `70-evaluation/rubrics/` |

### 7. Learn Back

| | |
|---|---|
| Input | Success / failure / user feedback |
| Output | A fix in the responsible layer (mapping table below) |
| Layer | Evaluation → the layer to fix |
| On failure | If it's unclear what to fix, just record it in `70-evaluation/failure-patterns/` with `nextAction: triage` |

## Learn Back mapping — failure type → layer to fix

| Failure type | First record | Layer to fix |
|---|---|---|
| Same mistake repeats across sessions | `70-evaluation/failure-patterns/` | Add a prevention pointer in `40-memory/` |
| Followed the procedure, result still wrong | `70-evaluation/failure-patterns/` | Fix the skill in `50-procedures/` (strengthen its verification step) |
| Knowledge is stale or factually wrong | `70-evaluation/audits/` | Fix the note in `20-knowledge/`, demote trustLevel or deprecate → `90-archive/` |
| Misunderstood the user's intent or preference | `70-evaluation/failure-patterns/` | Update `30-context/users/` (+ memory pointer if needed every session) |
| Wrong worker, tool, profile, or skill route | `70-evaluation/failure-patterns/` using the routing handoff block | Fix the owning router, procedure, or skill description; validate the event with `node scripts/lint.mjs --routing-failure <note>` |
| Stored something in the wrong place | `70-evaluation/audits/` | Fix `99-system/ROUTER.md` |
| Reported done without verifying | `70-evaluation/failure-patterns/` | Create a verification rubric for that task in `70-evaluation/rubrics/` |
| Important claim is unsupported or its source is inaccessible | `70-evaluation/verification/` or claim ledger | Fix the target note, source coverage, or retrieval procedure before reporting done |
| Success worth repeating | (no record needed) | Promote to a procedure in `50-procedures/` |

## Loop operating rules

- Not every input runs all seven steps. Pure knowledge intake ends at 1–4; an execution request runs only 5–7
- Steps may be skipped, but **7 (Learn Back) is impossible without 6 (Verify), and the loop does not close without 7**
- Verification depth is risk-based. Use [[VERIFICATION]] Tier 0 for low-risk one-offs and escalate durable, public, or high-stakes work to Tier 1–3
- When a loop pass produces a meaningful change, add one line to [[LOG]]
