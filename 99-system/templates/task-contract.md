# Task Contract Template

This is the default contract body for bounded AKM work. Copy it before task creation, replace every angle-bracket value, link the resulting path from the task body, and run `node scripts/lint.mjs --task-contract <contract.md>` before dispatch. Creation must stop on a non-zero exit.

Keep exactly one fenced JSON object so the existing AKM lint path can enforce the contract without a separate scoring tool.

```json
{
  "contractVersion": "1.0.0",
  "taskId": "<stable-id>",
  "purpose": "<one sentence>",
  "inputs": [{"path": "<exact path or URL>", "required": true, "verify": "exists"}],
  "outputs": [{"path": "<exact path>", "kind": "report", "required": true}],
  "canonicalPath": "<one declared output path>",
  "format": ["<schema or formatting rule>"],
  "sources": [{"ref": "<path or URL>", "role": "source-of-truth"}],
  "owner": {"primary": "<portable-owner-id>", "handoff": "<handoff condition>"},
  "failureHandling": {
    "blockedWhen": ["<external dependency only>"],
    "holdWhen": ["<internal unmet gate>"],
    "preserve": ["<evidence to retain>"]
  },
  "completion": {
    "required": ["<minimum acceptance>"],
    "optional": ["<polish that must not delay completion>"]
  },
  "verification": [{"command": "<exact command>", "expectedExit": 0, "readback": "<required output path>"}],
  "runtime": {"maxSeconds": 2700, "goalMode": false},
  "nonGoals": ["<explicit exclusion>"],
  "securityExclusions": ["auth", "token", "cookie", "session-db", "secret"],
  "blockers": []
}
```
