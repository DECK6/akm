# AKM Evidence Schema

Schema version: `1.0.0`

## 1. Purpose and authority

This document is the human-readable source of truth for the P0 `EvidenceRow` and `EvidencePacket` contract. The machine-readable companion is `99-system/evidence-row.schema.json`.

The contract normalizes four existing retrieval lanes without replacing them:

1. exact path, filename, property, ID, and literal-token search;
2. qmd lexical and semantic recall;
3. Graphify relationship and topology traversal;
4. direct source reads.

The evidence plane is a derived, disposable projection over canonical Markdown and original sources. It does not decide where knowledge belongs, promote notes, establish truth from rank, or replace direct reads. `[[SCHEMA]]`, `[[ROUTER]]`, `[[SECURITY]]`, and `[[LOOP]]` continue to govern storage, privacy, execution, verification, and Learn Back.

## 2. Non-negotiable invariants

| ID | Invariant | Required behavior |
|---|---|---|
| E1 | Markdown and original sources remain canonical | A database, cache, embedding, graph export, fusion score, or packet may be deleted and rebuilt without moving or rewriting canonical sources. |
| E2 | Candidate is not verification | `verification.state: candidate` cannot support a final factual claim. |
| E3 | Direct read is explicit | A row becomes `direct-read` only after the identified source and locator have actually been read and the observed checksum or revision has been recorded where available. |
| E4 | Claim support is narrower than direct read | `claim-supported` requires a direct read plus one or more explicit `claimIds`; reading a source does not imply that every possible claim is supported. |
| E5 | Scope and authority outrank freshness | Project allow/deny and authority policy are applied before relevance or freshness; freshness is a tie-breaker among otherwise eligible evidence. |
| E6 | Retriever scores stay lane-local | `rawScore` values from exact, qmd, and Graphify are never directly compared. Fusion uses rank and recorded policy, not an unexplained cross-lane score. |
| E7 | Fusion is auditable | Method, parameters, lane ranks, contributions, dedup keys, caps, exclusions, and tie-breaks are retained in the packet. |
| E8 | Dedup is source-level | Multiple chunks from one source cannot dominate a packet; canonical source identity is resolved before applying the per-source cap. |
| E9 | Neighbor expansion follows ranking | Context is expanded only for selected winners, and the original matched locator remains visible. |
| E10 | Conflicts remain visible | Canonical-versus-recent, stale-versus-current, or same-authority contradictions are recorded; fusion does not silently average them away. |
| E11 | Access policy is metadata, never a secret | Policy IDs and safe relative paths may be recorded; auth values, tokens, cookies, session data, and private transcript content may not be stored. |
| E12 | Packet is evidence, not an answer | An `EvidencePacket` can be `PASS` for evidence readiness while the downstream answer or artifact remains unwritten or unapproved. |

## 3. State model

### 3.1 Verification states

| State | Meaning | May support final claim? | Required transition evidence |
|---|---|---:|---|
| `candidate` | Retrieved and normalized, but not directly inspected | No | Retriever identity, query, lane rank, source identity, and locator |
| `direct-read` | The identified source location was directly read | Not by itself | Direct-read actor/tool, time, observed revision/checksum, and exact locator |
| `claim-supported` | A direct-read passage supports named claim IDs within stated limits | Yes, only for those claims | `directRead.performed: true`, non-empty `claimIds`, and support note or excerpt |
| `conflicted` | Eligible sources disagree or a source contradicts current canonical authority | No final claim until resolved or caveated | Conflict ID, competing row IDs, conflict type, and resolution status |
| `stale` | The source or derived row failed the active freshness/version policy | No | Stale reason and expected/current revision or policy result |
| `rejected` | The row is unusable because of scope, access, identity, duplication, unsupported locator, or quality failure | No | Rejection reason and, when applicable, policy rule |

Allowed forward transitions are:

```text
candidate → direct-read → claim-supported
candidate → conflicted | stale | rejected
direct-read → claim-supported | conflicted | stale | rejected
claim-supported → conflicted | stale | rejected  (when later evidence invalidates support)
```

A state change never erases the prior retrieval lane, original locator, source identity, or prior verification event. Implementations may use immutable event history or a current-state row plus `verification.history`; P0 requires the current state and enough history to audit invalidation.

### 3.2 Packet verdicts

| Verdict | Meaning |
|---|---|
| `NOT_TESTED` | The packet has not passed the preregistered checks. |
| `PASS` | All mandatory claims have eligible claim-supported rows, no unresolved blocking conflict exists, and policy gates pass. |
| `PASS_WITH_NOTE` | Mandatory support is present, but a non-blocking caveat, bounded stale risk, or optional evidence gap remains explicit. |
| `HOLD` | Required evidence, direct read, authority resolution, or scope decision is missing. Do not finalize important claims. |
| `FAIL` | Security, scope, identity, verification, reproducibility, or regression gate failed. Use the canonical route or roll back the derived path. |

## 4. `EvidenceRow` contract

An `EvidenceRow` is one normalized evidence candidate or verified source segment. It keeps source identity and provenance separate from retrieval rank and verification.

### 4.1 Required top-level fields

| Field | Type | Rule |
|---|---|---|
| `schemaVersion` | semantic-version string | P0 is `1.0.0`. |
| `rowType` | constant | Must be `EvidenceRow`. |
| `evidenceId` | string | Stable within the source revision and locator; changing source revision or locator creates a new ID. |
| `source` | object | Canonical identity, provenance, version, classification, and project references. |
| `scope` | object | Collection and exact locator used to retrieve and read the evidence. |
| `authority` | object | Authority level, rationale, and policy reference. |
| `freshness` | object | Observation and stale-state metadata, separate from authority. |
| `retrieval` | object | Lane, query, rank, lane-local score, and fusion trace. |
| `content` | object | Minimal excerpt plus optional post-rank neighbor context. |
| `verification` | object | Current state, direct-read evidence, claim IDs, notes, and history. |

### 4.2 `source`

Required fields:

- `sourceId`: stable source identity independent of the current chunk or rank;
- `canonicalUri`: `file:`, `https:`, `qmd:`, or another registered non-secret source URI;
- `sourceType`: one of `markdown`, `web`, `paper`, `book`, `code`, `thread`, `transcript`, `database`, `artifact`, or `other`;
- `classification`: `public`, `non-sensitive`, `private`, `restricted`, or `unknown`;
- `version`: source revision and checksum information;
- `projectScopes`: project IDs allowed to reference this source.

Optional fields:

- `canonicalPath`: AKM-relative path only; no machine-absolute or `..` path;
- `title` and `authors`;
- `originUri` and `publisher`;
- `parentSourceId` for a derived chunk or child document;
- `derived`: whether this row represents a derived projection;
- `derivationMethod`: deterministic or declared transformation name;
- `accessPolicyRef`: safe policy ID/path, never a credential;
- `sourceMetadata`: bounded non-secret source-specific metadata.

`source.version` contains:

| Field | Required | Meaning |
|---|---:|---|
| `revision` | Yes | Commit, ETag, event ID, source-native revision, or explicit `unknown`. |
| `checksumAlgorithm` | Yes | `sha256`, `source-native`, or `none`. |
| `checksum` | Conditional | Required when `checksumAlgorithm` is not `none`. |
| `observedAt` | Yes | When this revision was observed. |

A derived chunk inherits the source's `sourceId` and version but receives a distinct `evidenceId` based on its locator. A summary or distillation must set `derived: true`, name its `parentSourceId`, and may not replace the parent source.

### 4.3 `scope`

`scope` records where the evidence belongs and exactly where it was found.

Required fields:

- `projectId`;
- `manifestId` and `manifestVersion`;
- `scopeDecision`: `in-scope`, `explicit-expansion`, `out-of-scope`, or `denied`;
- `collection`;
- `locator`.

`locator` contains:

- `type`: `path`, `line-range`, `heading`, `page`, `symbol`, `thread`, `row`, `url-fragment`, or `other`;
- `value`: the source-native locator string;
- optional `headingPath`, `startLine`, `endLine`, `page`, `symbol`, `threadId`, and `anchor`.

Rows marked `out-of-scope` or `denied` cannot enter fusion winners. An explicit scope expansion requires a new manifest/query record and must not be inferred from semantic similarity.

### 4.4 `authority`

Required fields:

- `level`: `canonical`, `official`, `primary`, `reviewed`, `secondary`, `internal`, or `unknown`;
- `rationale`: why the level applies to this source for this task;
- `policyRef`: manifest or canonical policy governing the decision.

Optional fields:

- `owner`;
- `reviewedAt`;
- `supersedesSourceIds`;
- `limitations`.

Default authority ordering is:

```text
canonical → official → primary → reviewed → secondary → internal → unknown
```

This order is policy, not universal epistemology. A project manifest may define a narrower task-specific order, but it must record the revision. An official product manual may outrank a canonical local interpretation for current product behavior, while the canonical local procedure may outrank a recent comment for AKM operating policy. The rationale resolves the task-specific boundary.

### 4.5 `freshness`

Required fields:

- `state`: `current`, `unknown`, `stale`, or `superseded`;
- `checkedAt`;
- `policyRef`;
- `reason`.

Optional fields:

- `sourceModifiedAt`;
- `capturedAt`;
- `watermark`;
- `staleAfter`;
- `supersededBySourceId`.

Freshness may break a tie only after access, scope, authority, and direct support. A recent low-authority note cannot silently replace an older canonical policy. Mutable operational state may prefer a newer row only within the same authority class and scope.

### 4.6 `retrieval`

Required fields:

- `lane`: `exact`, `qmd-lexical`, `qmd-semantic`, `graphify-relationship`, `direct-read`, or `other`;
- `query`;
- `rank`: positive integer within the lane;
- `resultSetId`;
- `parameters`: transparent lane parameters.

Optional fields:

- `rawScore` and `rawScoreMeaning`;
- `normalizedScore` and `normalizationMethod`;
- `fusionContribution`;
- `fusionMethod`;
- `matchedTerms`;
- `relationshipPath`;
- `latencyMs`;
- `retrievedAt`.

`rawScore` is lane-local. A qmd score and Graphify path length cannot be compared as if they used one scale. Deterministic priority merge uses scope, authority class, exact-support class, lane rank, and freshness tie-break. Auditable RRF may use rank positions, but its `k`, eligible lanes, and contributions must be recorded.

### 4.7 `content`

Required fields:

- `excerpt`: minimal claim-bearing or match-bearing text;
- `excerptChecksum`: SHA-256 of the exact excerpt when available.

Optional fields:

- `language`;
- `before` and `after` neighbor blocks;
- `heading`;
- `contextExpansion`: expansion policy, byte count, and source locator;
- `redactions`: count and reason only; never preserve removed secret/private values.

Neighbor context is not a new source. It remains attached to the winner row and must preserve the original matched locator.

### 4.8 `verification`

Required fields:

- `state`;
- `verifiedBy`;
- `notes`.

Optional fields:

- `verifiedAt`;
- `claimIds`;
- `directRead`;
- `conflictIds`;
- `rejectionReasons`;
- `history`.

`directRead` contains:

- `performed`: boolean;
- `readAt`, `readBy`, and `readMethod` when performed;
- `locatorRead`;
- `observedRevision`;
- `observedChecksum` and `checksumMatch` where available;
- `contextIncluded`: whether surrounding conditions/caveats were read.

Conditional rules:

1. `claim-supported` requires `directRead.performed: true` and at least one `claimId`.
2. `direct-read` requires `directRead.performed: true`.
3. `candidate` cannot contain claim IDs.
4. `conflicted` requires at least one `conflictId`.
5. `stale` requires `freshness.state` to be `stale` or `superseded`.
6. `rejected` requires at least one rejection reason.

## 5. `EvidencePacket` contract

An `EvidencePacket` is a reproducible bundle for one task or query. It records what was searched, which policy applied, how candidates were fused, what was directly read, which claims are supported, and what remains unresolved.

### 5.1 Required top-level fields

| Field | Purpose |
|---|---|
| `schemaVersion` and `packetType` | Contract identity; `packetType` is `EvidencePacket`. |
| `packetId` | Stable task/query packet identity. |
| `taskId` | Task or run identity that requested evidence. |
| `query` | Original query, normalized intent, query class, and important-claim classes. |
| `project` | Project ID plus manifest ID, version, and checksum. |
| `policies` | Retrieval, authority, freshness, verification, and security references. |
| `generatedAt` | Packet creation time. |
| `lanesRun` | Lane status, query, parameters, counts, timing, and errors. |
| `fusion` | Method, parameters, eligible ordering, contributions, dedup, caps, diversity, and excluded rows. |
| `evidenceRows` | Normalized `EvidenceRow` objects. |
| `claims` | Claim registry and row support status. |
| `conflicts` | Explicit disagreement records. |
| `missingEvidence` | Required-but-absent evidence. |
| `directReadQueue` | Rows or claims still requiring direct reads. |
| `metrics` | Reproducibility and evaluation counters. |
| `verification` | Packet verdict, reasons, verifier, and rollback decision. |

### 5.2 Query classes and lane selection

`query.class` is one of:

- `exact-path-property`;
- `literal-token`;
- `semantic-recall`;
- `relationship-neighborhood`;
- `authority-conflict`;
- `mixed`.

The class records intent; it does not force every lane. `lanesRun` must also record skipped lanes and the skip reason so selective fan-out is auditable.

### 5.3 Fusion record

`fusion` requires:

- `method`: `deterministic-priority` or `rrf`;
- `parameters`;
- `priorityOrder` beginning with scope and authority;
- `dedupKeys` including `sourceId`, `canonicalUri`, and source revision/checksum where present;
- `perSourceCap`;
- `maxRows`;
- `diversityFields`;
- `contributions` mapping winner row IDs to lane ranks/contributions;
- `excludedRows` with row ID and reason.

P0 default is `deterministic-priority`. RRF is an optional P1 comparison baseline, never an authority or truth score.

### 5.4 Claims

Each claim has:

- `claimId`;
- `claimText` or bounded claim summary;
- `importance`: `important` or `supporting`;
- `claimClass`: `number`, `date`, `system-state`, `recommendation`, `policy`, `interpretation`, or `other`;
- `supportRowIds`;
- `status`: `unsupported`, `candidate-only`, `direct-read-pending`, `supported`, `conflicted`, or `rejected`;
- `notes`.

An important claim is `supported` only when every listed support row is `claim-supported` for that exact claim ID. A packet cannot receive `PASS` while an important claim is `unsupported`, `candidate-only`, `direct-read-pending`, or `conflicted`.

### 5.5 Conflicts

Each conflict record includes:

- `conflictId`;
- `topic`;
- `rowIds`;
- `type`: `authority`, `freshness`, `scope`, `factual`, `version`, or `interpretation`;
- `status`: `open`, `resolved`, or `accepted-divergence`;
- `resolution`;
- `resolvedBy` and `resolvedAt` when resolved;
- `claimIds` affected.

`accepted-divergence` is valid only when the final artifact presents the divergence rather than selecting one hidden winner.

### 5.6 Direct-read queue

Each queue item includes:

- `queueId`;
- `rowId`;
- `claimIds`;
- `priority`;
- `reason`;
- `required`: boolean;
- `status`: `pending`, `completed`, `skipped`, or `failed`;
- `completionRowId` when completed;
- `skipReason` when skipped.

A required item cannot be skipped for a packet that claims `PASS` or `PASS_WITH_NOTE`.

### 5.7 Metrics

P0 packet metrics define fields; P1 supplies real values. Required counters are:

- input candidate count;
- in-scope eligible count;
- deduplicated source count;
- cap-excluded count;
- final row count;
- unique source and source-type count;
- direct-read required/completed count;
- important claim count and supported count;
- citation coverage;
- stale-hit count;
- authority/scope error count;
- input bytes and estimated context tokens;
- lane and total latency when measured.

Metric definitions and acceptance gates are preregistered in `70-evaluation/rubrics/akm-retrieval-fusion-evaluation.md`. Empty or unmeasured metrics must be explicit `null`, never fabricated zeroes.

## 6. Lane-to-schema mapping

| Lane | Minimum row mapping | Typical verification state | Important caveat |
|---|---|---|---|
| exact | source identity, matched path/token/property, exact locator, rank | `candidate` | Exact support is high-value retrieval, not truth until read. |
| qmd lexical | qmd collection, lexical query, rank, qmd URI/path, excerpt | `candidate` | BM25/rerank values remain qmd-local. |
| qmd semantic | semantic query, rank, qmd URI/path, excerpt | `candidate` | Semantic similarity does not establish scope or authority. |
| Graphify relationship | graph path, node/edge relationship, source node locator, rank | `candidate` | A graph edge proves a recorded relation, not the full source claim. |
| direct read | canonical URI/path, exact locator, observed revision/checksum, surrounding context | `direct-read` | Claim support still requires named claim IDs. |

## 7. Minimal examples

### 7.1 Candidate row

```yaml
schemaVersion: "1.0.0"
rowType: EvidenceRow
evidenceId: "ev:sha256:example-candidate"
source:
  sourceId: "akm:99-system:SECURITY"
  canonicalUri: "file:99-system/SECURITY.md"
  canonicalPath: "99-system/SECURITY.md"
  sourceType: markdown
  classification: public
  projectScopes: ["akm-evidence-pilot"]
  derived: false
  version:
    revision: "working-tree"
    checksumAlgorithm: sha256
    checksum: "example-checksum"
    observedAt: "2026-07-20T00:00:00+09:00"
scope:
  projectId: "akm-evidence-pilot"
  manifestId: "akm-evidence-pilot"
  manifestVersion: "1.0.0"
  scopeDecision: in-scope
  collection: "akm"
  locator:
    type: heading
    value: "## 1. Never store secret values"
authority:
  level: canonical
  rationale: "Canonical AKM security policy for secret handling."
  policyRef: "99-system/SECURITY.md"
freshness:
  state: current
  checkedAt: "2026-07-20T00:00:00+09:00"
  policyRef: "project-retrieval-manifest:freshnessPolicy"
  reason: "Current working-tree source was found."
retrieval:
  lane: exact
  query: "never store secret values"
  rank: 1
  resultSetId: "rs:example"
  parameters: {match: literal}
content:
  excerpt: "API keys, tokens, passwords ... never, in any layer."
  excerptChecksum: "example-excerpt-checksum"
verification:
  state: candidate
  verifiedBy: "not-yet-direct-read"
  notes: "Retrieved candidate; cannot support a final claim yet."
```

### 7.2 Claim-supported transition

```yaml
verification:
  state: claim-supported
  verifiedAt: "2026-07-20T00:01:00+09:00"
  verifiedBy: "retrieval-worker"
  claimIds: ["claim-secret-values-prohibited"]
  directRead:
    performed: true
    readAt: "2026-07-20T00:01:00+09:00"
    readBy: "retrieval-worker"
    readMethod: "direct-file-read"
    locatorRead: "99-system/SECURITY.md:5-13"
    observedRevision: "working-tree"
    observedChecksum: "example-checksum"
    checksumMatch: true
    contextIncluded: true
  notes: "The directly read canonical policy supports only the named prohibition claim."
```

## 8. Identity and reproducibility rules

A recommended stable ID construction is:

```text
sourceId = stable namespace + canonical source identity
evidenceId = hash(schemaVersion + sourceId + revision/checksum + locator)
packetId = taskId + query digest + manifest version + run sequence
```

The exact hashing implementation belongs to P1. P0 requires only that IDs be stable, collision-resistant in practice, and reproducible from recorded inputs.

Every packet must preserve:

- project manifest ID, version, and checksum;
- retrieval policy version;
- normalized query and lane-specific query text;
- lane parameters and skip reasons;
- source revision/checksum observed at retrieval/direct read;
- fusion method and all ordering parameters;
- dedup keys, cap, and excluded-row reasons;
- direct-read completion and affected claim IDs.

## 9. Security and project-scope boundary

The P0/P1 pilot is restricted to explicitly allowlisted public or non-sensitive Markdown. The manifest must deny by default and exclude:

- private/personal transcripts and conversations;
- counseling, health, contact, and unpublished third-party content;
- auth, OAuth, token, cookie, password, secret, session, and credential surfaces;
- `.env`, database, SQLite, log, binary, archive, and generated-media assets;
- machine-absolute or parent-escaping paths;
- sources with `private`, `restricted`, or `unknown` classification.

An excluded source must not leak its title, path, excerpt, embedding-derived hint, graph neighbor, or existence through a packet. Count-only security audits may report exclusions without opening private content.

## 10. Derived-index and rollback boundary

P1 may create a bounded index, adapter output, or benchmark packet only after this P0 contract passes. Every derived surface must be disposable.

Rollback order:

1. disable fusion/adapter use;
2. delete the derived pilot index or cache;
3. keep exact search, qmd, Graphify, and direct file reads operational;
4. retain this schema and evaluation record as design/learning evidence;
5. record the failure under `70-evaluation` and update the relevant policy through `[[LOOP]]`;
6. never move, delete, or overwrite canonical Markdown or original sources as rollback.

## 11. P0 completion and P1 handoff

P0 is complete when:

- the human and JSON contracts parse and agree;
- the manifest can express public/non-sensitive allowlists and deny rules;
- all four current retrieval lanes map to one row shape;
- candidate, direct-read, and claim-supported states cannot be confused;
- fusion, dedup, cap, expansion, direct-read, conflict, and rollback records are explicit;
- the evaluation rubric is preregistered;
- the readback reports `PASS` or explicit `HOLD` without claiming a prototype or C4 uplift.

P0 does not implement a connector, MCP server, database, embedding model, reranker, Postgres, HNSW, CocoIndex, or enterprise ACL. P1 begins only after the task contract and P0 readback both pass.
