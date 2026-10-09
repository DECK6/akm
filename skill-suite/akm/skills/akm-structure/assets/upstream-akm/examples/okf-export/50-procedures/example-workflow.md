---
type: "Workflow"
title: "Example retrieval workflow"
description: "Runs a small workflow that reads an index, opens the relevant note, and verifies the output."
resource: "https://example.com/progressive-agent-retrieval"
tags:
  - "example"
  - "workflow"
timestamp: "2026-06-15T00:00:00Z"
---

# Example retrieval workflow

## When to use

Use this workflow when an agent needs to find the smallest useful note set before acting.

## Preparation

- Read [example-project-context](/30-context/example-project-context.md)
- Review [example-concept](/20-knowledge/example-concept.md)

## Steps

1. Open the relevant directory index.
2. Select the smallest note set that answers the request.
3. Run the task.
4. Verify with [example-verification-rubric](/70-evaluation/example-verification-rubric.md).

## Common failure points

- Reading every note before inspecting the index -> record recurrence in [example-failure-pattern](/70-evaluation/example-failure-pattern.md).

## Verification

- [ ] The agent can name which index it used.
- [ ] The final answer cites only notes that were actually opened.

## Citations

- [Progressive retrieval article](https://example.com/progressive-agent-retrieval)

## Reporting

Report the selected notes and rubric result. Store only reproducibility-critical details in `60-actions/`.
