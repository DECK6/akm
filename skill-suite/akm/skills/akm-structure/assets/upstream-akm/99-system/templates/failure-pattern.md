---
description: "One-sentence English retrieval hint: which recurring failure this note records and how to prevent it."
akmLayer: evaluation
akmRole: verification-rule
akmType: failure-pattern
trustLevel: reviewed
nextAction: verify
date created: YYYY-MM-DD
date modified: YYYY-MM-DD
tags: []
---

# (Failure pattern name)

## Symptom

(What went wrong, and how)

## Occurs when

(In which tasks or conditions it recurs)

## Cause

(Root cause. Mark explicitly if it's a guess)

## Prevention

(How to avoid it on the next run)

## Learn Back

- Layer fixed: (40-memory pointer added / 50-procedures skill fixed / 20-knowledge note fixed / ROUTER fixed)
- File fixed: [[filename]]

### Routing failure handoff (routing failures only)

For a route miss, false positive, or misroute, replace the values below and keep this as the note's only fenced JSON object. Remove this subsection for non-routing failures. Validate before closing:

`node scripts/lint.mjs --routing-failure <this-note.md>`

```json
{
  "schemaVersion": "1.0.0",
  "entries": [
    {
      "eventId": "<stable-event-id>",
      "observedAt": "<ISO date or datetime>",
      "taskId": "<task-id>",
      "expectedRoute": "<expected worker, profile, tool, or skill>",
      "actualRoute": "<actual route; empty only for miss>",
      "failureType": "<miss|false-positive|misroute>",
      "evidence": ["<metadata-only task or artifact reference>"],
      "privacy": "metadata-only",
      "status": "open"
    }
  ]
}
```

Closing the entry requires a correction handoff to the actual router, procedure, or skill description. Record the changed target, before/after hashes, verification command, and `PASS` result. Do not copy prompts, messages, sessions, tokens, cookies, or secret values.

## Occurrences

- YYYY-MM-DD: (one-line situation)

## Citations

- (Evidence, source note, verification record, or external reference)
