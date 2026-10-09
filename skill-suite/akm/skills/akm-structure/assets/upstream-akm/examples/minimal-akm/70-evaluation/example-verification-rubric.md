---
description: "Defines passing criteria for index-first retrieval in the public AKM fixture."
akmLayer: evaluation
akmRole: verification-rule
akmType: rubric
trustLevel: reviewed
usedBy: [example-workflow]
nextAction: verify
date created: 2026-06-15
date modified: 2026-06-15
tags: [example, rubric]
---

# Index-first retrieval rubric

## Applies to

This rubric applies to [[example-workflow]].

## Pass criteria - ALL must hold

- [ ] The agent starts from an index or explains why no index exists.
- [ ] The agent opens only the notes needed for the task.
- [ ] The agent records repeated over-reading as [[example-failure-pattern]].

## Failure severity guide

| Severity | Meaning | Action |
|---|---|---|
| high | no verification happened | stop and verify before reporting done |
| mid | too many notes were opened | revise the workflow |
| low | index wording is unclear | update the index summary |

## Evidence required

List the index file and note files used. A vague claim that the agent checked context is not enough.
