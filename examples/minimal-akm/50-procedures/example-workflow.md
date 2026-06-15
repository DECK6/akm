---
description: "Runs a small workflow that reads an index, opens the relevant note, and verifies the output."
akmLayer: procedure
akmRole: executable-procedure
akmType: workflow
trustLevel: reviewed
CMDS: Develop
usedBy: []
nextAction: verify
date created: 2026-06-15
date modified: 2026-06-15
tags: [example, workflow]
---

# Example retrieval workflow

## When to use

Use this workflow when an agent needs to find the smallest useful note set before acting.

## Preparation

- Read [[example-project-context]]
- Review [[example-concept]]

## Steps

1. Open the relevant directory index.
2. Select the smallest note set that answers the request.
3. Run the task.
4. Verify with [[example-verification-rubric]].

## Common failure points

- Reading every note before inspecting the index -> record recurrence in [[example-failure-pattern]].

## Verification

- [ ] The agent can name which index it used.
- [ ] The final answer cites only notes that were actually opened.

## Citations

- [Progressive retrieval article](https://example.com/progressive-agent-retrieval)

## Reporting

Report the selected notes and rubric result. Store only reproducibility-critical details in `60-actions/`.
