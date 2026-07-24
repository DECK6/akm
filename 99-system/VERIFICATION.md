# AKM Verification Standard

AKM verification uses a risk-based process for durable notes, reports, proposals, public outputs, and high-stakes factual work. It strengthens Step 6 Verify and Step 7 Learn Back without turning every answer into a heavyweight evaluation run.

This standard is informed by [DEER: A Benchmark for Evaluating Deep Research Agents on Expert Report Generation](https://arxiv.org/abs/2512.17776v4). DEER organizes expert-report quality into seven dimensions and adds task-specific expert guidance plus report-wide claim verification. AKM adapts those patterns to a file-based operating loop; it does not reproduce the benchmark or treat model scoring as ground truth.

## 1. Select a verification tier

| Tier | Default trigger | Required action |
|---|---|---|
| Tier 0 — Quick | low-risk one-off answer, no durable file | Check only facts or tool results material to the answer; create no evaluation artifact |
| Tier 1 — Durable Note | any note saved for reuse | Apply the seven-dimension minimum; verify schema, source traceability, and discoverability |
| Tier 2 — Deep Report | long-form research, proposal, lecture, public page, important synthesis | Tier 1 + Task Evaluation Guidance Packet + key-claim spot checks |
| Tier 3 — High-stakes | medical, legal, safety, contract, official submission, or consequential public factual claims | Tier 2 + claim ledger + source reliability + second-pass verification |

When the boundary is unclear, use the higher tier for public-facing or irreversible work and the lower tier for internal exploration.

## 2. Seven-dimension minimum

All Tier 1+ work is checked across these dimensions. Record only material findings for lightweight notes; use a full verification note for Tier 2+.

### Request Fulfillment

- The result preserves the user's actual artifact, scope, audience, deadline, constraints, and exclusions.
- Explicit requirements are not omitted; necessary assumptions are visible.
- Scope changes are explained instead of silently redefining the task.
- The result advances the user's goal rather than escaping into a generic summary.

### Analytical Soundness

- Numbers, dates, counts, versions, prices, and file facts are checked with tools or sources.
- Reasoning does not depend on hidden leaps.
- Assumptions, uncertainty, limitations, and failure modes are labeled.
- Recommendations follow from inspected evidence, including relevant counterevidence.

### Structural Coherence

- Purpose and scope are clear at the start.
- Sections progress in an order that supports the task and do not drift.
- The conclusion introduces no unsupported new claim.
- Headings, tables, and checklists contain substantive content rather than placeholders.

### Format and Style

- The target format, template, filename, frontmatter, and folder rules are followed.
- Markdown and links are readable in the intended tools.
- Language is specific enough for a future human or agent to reuse.
- No malformed YAML, empty scaffolding, or formatting defect changes meaning.

### Ethics and Compliance

- Secrets, private data, and sensitive context are not exposed unnecessarily.
- High-risk claims state uncertainty and responsibility boundaries.
- Claims about people, organizations, works, or institutions do not exceed source support.
- External sending, publishing, destructive action, or risky execution stays within authorized scope.

### Information Sufficiency

- Source coverage is adequate for the strength and consequence of the claims.
- Authoritative sources are inspected before relying on memory or secondary summaries.
- Current facts are rechecked when they may have changed.
- Sources are connected to the claims they support, not presented as a decorative link list.

### Information Integrity

- Cited or linked sources actually support the specific claims made.
- Facts, interpretations, assumptions, and hypotheses are distinguishable.
- Source reliability and conflicts are handled explicitly.
- Important unsupported claims are weakened, removed, or held for verification.

## 3. File-back and substantive lint binding

A query answer is not stored by default. If it has durable reuse value and is filed back into AKM, it becomes Tier 1 or higher and must preserve the original intent, inspected sources, related AKM notes, and intended reuse path.

Substantive lint adds two issue types beyond structural Markdown/frontmatter checks:

- **Request-fit gap**: the artifact is polished but misses or silently changes the requested artifact, audience, scope, deadline, format, exclusions, or practical goal.
- **Claim-support gap**: a source exists but does not support the claim; an inherited citation cannot be backtracked; or a high-impact claim remains unsupported while the artifact is labeled reviewed, source-backed, or ready.

`scripts/lint.mjs` checks deterministic structure, metadata, links, indexes, and secret patterns. It does not pretend to automate these semantic judgments. Agents, qualified reviewers, or task-specific evaluators apply the verification standard and record evidence.

When retrieval uses multiple lanes or supports important claims, normalize candidates and direct reads with `99-system/EVIDENCE-SCHEMA.md`. A retrieved row remains a candidate until its identified source location is directly read. Claim support applies only to named claims, and conflicting or stale evidence remains visible. The evidence packet is a derived, disposable audit surface; canonical Markdown and original sources remain authoritative.

## 4. Task Evaluation Guidance Packet — Tier 2+

Before final verification, create a compact task-specific packet in the working note or an associated verification note.

| Field | What to record |
|---|---|
| Task intent | The user's actual goal, not only the literal command |
| Audience / use | Who will use the output and what happens next |
| Required content | Concrete, checkable content that must appear |
| Required exclusions | Scope boundaries and claims that must not be made |
| Domain anchors | Official documents, papers, local notes, project constraints, prior corrections |
| Failure traps | Likely hallucinations, stale facts, omissions, category mistakes, source risks |
| Verification evidence | Files, URLs, command results, screenshots, renders, diffs, or reviewer notes |
| Learn Back target | The layer to fix if verification fails |

## 5. Key-claim spot checks — Tier 2+

Sample the claims that would most damage trust if wrong. Always treat dates, deadlines, eligibility, budgets, counts, rankings, scores, citations, official requirements, and medical/legal/safety/contract claims as high impact.

For each sampled claim:

1. Isolate the exact factual statement.
2. Identify its source path, URL, or tool output.
3. Read the evidence and decide whether it directly supports the statement's scope and strength.
4. Keep, weaken, rewrite, remove, or mark the claim unresolved.

Source access failure is not verification. Mark the claim unresolved or `Source Inaccessible`.

## 6. Claim ledger — Tier 3

Copy `99-system/templates/claim-ledger.md` to:

```text
70-evaluation/verification/<date>-<target-slug>-claim-ledger.md
```

Classify high-risk factual claims using the A–F scheme in that template. Verify A–C claims against their explicit or backtracked evidence positions. Unknown-source or unsupported claims remain held until they are sourced, weakened, or removed.

## 7. Verdicts

| Verdict | Meaning | Required action |
|---|---|---|
| PASS | Applicable checks materially pass; only low-risk issues remain | Report complete; promote `trustLevel` only when evidence justifies it |
| PASS_WITH_NOTE | Usable, with known caveats or unresolved low/mid risks | Report caveats and record a next action when useful |
| HOLD | Important evidence, scope, or user-intent issue remains | Do not report done; fix it or report the concrete blocker |
| FAIL | The output would mislead, harm, or require major rework | Stop; record recurring failure; Learn Back immediately |
| NOT_TESTED | A dimension was not checked | Do not claim verification for that dimension |

The strongest material failure determines the overall verdict.

## 8. Learn Back routing

| Failed dimension or finding | First record | Likely fix target |
|---|---|---|
| Request misunderstood | failure pattern if recurring | `30-context/` or the responsible procedure |
| Weak reasoning or incorrect knowledge | audit or failure pattern | `20-knowledge/`, `50-procedures/`, or `70-evaluation/` |
| Structure or format failure | audit or direct patch | procedure, template, `99-system/SCHEMA.md` |
| Safety, privacy, or compliance failure | failure pattern | procedure or security/evaluation rule |
| Insufficient or stale evidence | audit | `10-sources/`, `20-knowledge/`, or retrieval procedure |
| Citation does not support claim | verification note or claim ledger | target note plus `70-evaluation/verification/` |
| No evaluation criteria existed | new rubric | `70-evaluation/rubrics/` |

## 9. Minimal verification report

Use this compact form for Tier 1/Tier 2 when a separate long audit is unnecessary:

```markdown
## Verification

| Check | Result | Evidence |
|---|---|---|
| Request fit | PASS/HOLD/FAIL |  |
| Source traceability | PASS/HOLD/FAIL |  |
| Claim support | PASS/HOLD/FAIL/NOT_TESTED |  |
| Format/schema | PASS/HOLD/FAIL |  |
| Discoverability | PASS/HOLD/FAIL/NOT_TESTED |  |

Verdict: PASS / PASS_WITH_NOTE / HOLD / FAIL
Learn Back: none / target layer
```

## 10. Operating rules

- A collected URL proves only that a source exists, not that it supports a claim.
- Frontmatter correctness alone does not justify `trustLevel: reviewed`.
- LLM-as-judge output is a diagnostic signal. Direct source reads, tool output, artifact inspection, and qualified human review outrank it.
- Do not create claim ledgers for low-risk notes that will never be reused.
- Keep unresolved claims visible instead of hiding them in polished prose.
- Verification is complete only when the tier is explicit, required evidence exists, and every HOLD/FAIL has a Learn Back target.
