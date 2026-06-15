---
type: "Failure Pattern"
title: "Over-reading before index"
description: "Recurring failure where an agent skips the index and over-reads the knowledge folder."
tags:
  - "example"
  - "failure-pattern"
timestamp: "2026-06-15T00:00:00Z"
---

# Over-reading before index

## Symptom

The agent reads many detailed notes before checking the directory-level index, increasing latency and context noise.

## Occurs when

The request is broad and the agent starts with recursive file reads instead of an index-first pass.

## Cause

The procedure does not explicitly require index-first retrieval.

## Prevention

Update the workflow to read indexes first and verify the selected note set.

## Learn Back

- Layer fixed: 50-procedures workflow fixed
- File fixed: [example-workflow](/50-procedures/example-workflow.md)

## Occurrences

- 2026-06-15: Public fixture occurrence showing how Learn Back points to the procedure layer.

## Citations

- [example-verification-rubric](/70-evaluation/example-verification-rubric.md)
