---
description: "Template for recording high-stakes factual claims, evidence positions, support verdicts, and Learn Back actions during AKM verification."
akmLayer: evaluation
akmRole: verification-rule
akmType: verification
trustLevel: reviewed
usedBy: ["[[VERIFICATION]]"]
nextAction: verify
date created: YYYY-MM-DD
date modified: YYYY-MM-DD
tags: [akm, evaluation, claim-ledger, template]
---

# Claim Ledger

Use this template for Tier 3 work under `99-system/VERIFICATION.md` when a high-stakes output needs claim-level evidence tracing. Copy it to:

```text
70-evaluation/verification/<date>-<target-slug>-claim-ledger.md
```

## Target

| Field | Value |
|---|---|
| Target output |  |
| Verification tier / risk |  |
| User request |  |
| Evaluator |  |
| Date |  |
| Related rubric |  |
| Related playbook |  |

## Task guidance

| Field | Content |
|---|---|
| Task intent |  |
| Audience / use |  |
| Required content |  |
| Required exclusions |  |
| Domain anchors |  |
| Failure traps |  |
| Verification evidence |  |
| Learn Back target if failed |  |

## Claim classes

| Class | Meaning | Verification action |
|---|---|---|
| A — explicit citation | Claim has an explicit citation, link, or source marker | Verify that source directly supports the claim |
| B — same-section evidence | Claim depends on evidence earlier in the same section or paragraph | Backtrack and verify the same-section source |
| C — previous-section evidence | Claim depends on evidence in an earlier section | Backtrack semantically and verify support |
| D — structural recap | Claim summarizes the target document itself | Check internal consistency |
| E — citation not normally required | General knowledge or the author's direct result | Spot-check when risk is high |
| F — unknown source | Claim needs evidence but no source is identifiable | Hold or fail until sourced, weakened, or removed |

## Claim ledger

| ID | Location | Claim | Class | Source / evidence position | Support verdict | Source reliability | Action |
|---|---|---|---|---|---|---|---|
| C001 |  |  | A/B/C/D/E/F |  | Supported / Partially Supported / Not Supported / Source Inaccessible / Not Applicable | High / Medium / Low / Unknown | Keep / Rewrite / Remove / Source needed / Hold |

## Verdict summary

| Dimension | Result | Evidence |
|---|---|---|
| Request fulfillment | Pass / Pass with note / Hold / Fail / Not tested |  |
| Analytical soundness | Pass / Pass with note / Hold / Fail / Not tested |  |
| Structural coherence | Pass / Pass with note / Hold / Fail / Not tested |  |
| Format and style | Pass / Pass with note / Hold / Fail / Not tested |  |
| Ethics and compliance | Pass / Pass with note / Hold / Fail / Not tested |  |
| Information sufficiency | Pass / Pass with note / Hold / Fail / Not tested |  |
| Information integrity | Pass / Pass with note / Hold / Fail / Not tested |  |

Overall verdict: Pass / Pass with note / Hold / Fail

## Learn Back

| Issue | Severity | Layer to fix | Action |
|---|---|---|---|
|  | high / medium / low | `10-sources` / `20-knowledge` / `30-context` / `50-procedures` / `70-evaluation` / `99-system` |  |

## Completion check

- [ ] Unsupported claims were removed, weakened, or marked as held.
- [ ] Source-inaccessible claims were not reported as verified.
- [ ] The target note or output was patched after verification when needed.
- [ ] INDEX and LOG were updated when a durable AKM artifact was created.
