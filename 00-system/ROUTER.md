# AKM-ROUTER

The rules for deciding which layer an input (material, experience, request, result) is stored in.
Run every intake through this tree from the top. **The first match is the storage location.**

## Security pre-check (before classification)

Per [[SECURITY]]: never store secret values (store their names/locations instead); minimize personal data in sources; never force-add layer files to git; review outputs before they leave the machine. An input that fails this check is not stored.

## Classification decision tree

```text
input
│
├─ Q1. Is it an unmodified original from outside? (document, web clip, paper, transcript, log, manual)
│   └─ YES → 10-sources/ (never modify, record sourcePath, nextAction: merge)
│
├─ Q2. Is it about failure, verification, or quality criteria?
│   ├─ a failure that may recur → 70-evaluation/failure-patterns/
│   │   └─ if critical enough that every session must know it first → add a 1-line pointer in 40-memory/
│   ├─ a recovery method → 70-evaluation/recovery/
│   ├─ a quality bar → 70-evaluation/rubrics/
│   └─ an inspection result → 70-evaluation/audits/
│
├─ Q3. Is it a repeatable execution procedure? (how to start, what to check, which tools, how to verify)
│   └─ YES → 50-procedures/ (skill | workflow | checklist | playbook)
│       └─ Separating domain knowledge inside a procedure: move only knowledge that other
│          procedures/tasks would reuse into 20-knowledge/ and link it. A 1–2 line tip
│          specific to this procedure stays in the procedure
│
├─ Q4. Is it an interpretation, preference, or constraint about a specific user / org / project / domain?
│   └─ YES → 30-context/ (users | projects | domains | constraints)
│       └─ if short, stable, and needed first every session → add a 1-line pointer in 40-memory/
│
├─ Q5. Is it a short, stable operating rule the agent must know before acting, every time?
│   └─ YES → 40-memory/ (pointers only — the full content lives in another layer, linked)
│
├─ Q6. Is it reusable knowledge synthesized from sources?
│   └─ YES → 20-knowledge/ (concept | entity | comparison | pattern | tool | technique)
│
├─ Q7. Is it an execution record, decision, or handoff?
│   ├─ Is it needed for reproduction, verification, failure recovery, or handoff?
│   │   ├─ YES → 60-actions/ (run | decision | handoff)
│   │   └─ NO → do not store it (prevent log garbage)
│   └─ if it's a deliverable for external use → 80-outputs/
│
└─ Q8. Has it reached end of life? (superseded, deprecated)
    └─ YES → 90-archive/ (set trustLevel: deprecated, then move)
```

## The four storage judgment rules

### Store in Memory (40) — ALL must hold

- It is short (a few lines at most)
- It is stable (doesn't change often)
- It is needed repeatedly
- The agent must know it before acting, every time
- A pointer is enough — no long original text required

**Forbidden**: long knowledge summaries, full canonical notes, original materials, bulk transcripts, one-off work logs, soon-stale progress status.

### Store as Knowledge (20) — at least ONE must hold

- It is worth re-reading by a human
- Its source or context matters
- It can be reused across projects
- It needs to connect to other concepts
- It needs a long or deep explanation
- It is domain knowledge itself

### Promote to a Procedure (50) — ALL must hold

- It is executed repeatedly
- It has steps
- It has (or predictably will have) failure points
- It has a verification method
- It makes the same task better next time

**Forbidden**: domain knowledge without steps (→ `20-knowledge/`), one-off tasks.

### Store in Evaluation (70) — at least ONE must hold

- The same failure may recur
- A quality judgment standard is needed
- A clear verification method for results is needed
- Existing knowledge or procedures must be corrected

## Tie-breaking rules

- **Failure vs procedure**: always record the failure in `70-evaluation/` first. Fixing the procedure comes after (Learn Back)
- **Preference vs memory**: the full note lives in `30-context/users/`; only the per-session essentials become a `40-memory/` pointer
- **Knowledge vs context**: "Is it true for anyone?" YES → `20-knowledge/`. "True only for this user/project?" → `30-context/`
- **Knowledge vs procedure**: "what to know" → `20-knowledge/`. "how to execute" → `50-procedures/`

## Classification examples (for verification)

| Input | Path through the tree | Stored at |
|---|---|---|
| A web clip of a TouchDesigner tutorial | Q1 YES | `10-sources/` (nextAction: merge) |
| "Putting long knowledge in agent memory slowed every session" — a failure experience | Q1 NO → Q2 YES (may recur) | `70-evaluation/failure-patterns/` + 1-line pointer in `40-memory/` |
| A repeatable upscale-then-download procedure for an image tool | Q1 NO → Q2 NO → Q3 YES | `50-procedures/skills/` |
| "This user prefers extremely concise responses" | Q1–Q3 NO → Q4 YES (short & stable) | `30-context/users/` + `40-memory/` pointer |
| Yesterday's successful build output | Q1–Q6 NO → Q7 (needed for reproduction? plain success log → NO) | not stored (only `60-actions/` if it failed or contains a decision) |
