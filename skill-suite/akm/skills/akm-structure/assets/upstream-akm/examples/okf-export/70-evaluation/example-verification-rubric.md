---
type: "Rubric"
title: "Index-first retrieval rubric"
description: "Defines passing criteria for index-first retrieval in the public AKM fixture."
tags:
  - "example"
  - "rubric"
timestamp: "2026-06-15T00:00:00Z"
---

# Index-first retrieval rubric

## Applies to

This rubric applies to [example-workflow](/50-procedures/example-workflow.md).

## Pass criteria - ALL must hold

- [ ] The agent starts from an index or explains why no index exists.
- [ ] The agent opens only the notes needed for the task.
- [ ] The agent records repeated over-reading as [example-failure-pattern](/70-evaluation/example-failure-pattern.md).

## Failure severity guide

| Severity | Meaning | Action |
|---|---|---|
| high | no verification happened | stop and verify before reporting done |
| mid | too many notes were opened | revise the workflow |
| low | index wording is unclear | update the index summary |

## Evidence required

List the index file and note files used. A vague claim that the agent checked context is not enough.
