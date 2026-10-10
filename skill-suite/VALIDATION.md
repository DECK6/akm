# Validation — 2026-10-10

This release was checked as a portable local skill suite. Behavioral exercises used synthetic users and domains; they are not real-user research, a guarantee of factual accuracy, or cross-model benchmarks.

## 0.2.1 — Claude Code compatibility

- Python suite: 35 tests passed. New cases exercise host-specific paths, the default Codex behavior, Claude configuration/default/custom destinations, idempotent reruns, preserved conflicts, and the complete package after relocation.
- Claude Code 2.1.274: `claude plugin validate --strict --json skill-suite/akm` passed with no errors or warnings.
- Native initialization in isolated configuration/workspace directories listed all 15 expected commands for each layout: personal skills, project skills, and the session-only plugin. The plugin listed `akm:akm` and its 14 namespaced roles; direct installations listed `akm` and its 14 roles.
- The startup checks requested only the native command catalog. They did not request a Claude model answer, repeat the semantic exercises on Claude, or measure natural-language selection recall. The shared skill bodies and domain contracts are unchanged except for host invocation and package-path guidance.
- Personal and project installations use symlinks. Native Windows remains unverified. A local `--plugin-dir` session is covered; marketplace distribution is not configured or tested.

Reproduce installation and manifest checks from the repository root:

```sh
python3 -m unittest discover -s skill-suite/tests -v
claude plugin validate --strict --json skill-suite/akm
python3 skill-suite/akm/scripts/install.py --host claude --dest /path/to/test-project/.claude/skills
```

Start Claude Code in that test project and inspect `/skills`. For plugin discovery, launch `claude --plugin-dir /absolute/path/to/akm/skill-suite/akm` and inspect the `akm:` commands. Use the [Claude guide](../adapters/claude-code/README.md) for installation scopes and invocation.

## 0.2.0 — operation after setup

| Check | Observed result |
|---|---|
| Python tool tests | 30 passed, including linked-map integrity, evidence/type/path failures, read-only coverage/frontier/impact, stale artifacts, empty knowledge, code-literal links and additive domain setup |
| Core regression | Existing 18 Node tests passed; core behavior and pinned upstream assets retained |
| Package and installation | 15 skills and plugin manifest validated; four new roles installed alongside the existing 11; all installed skill links and bodies read back |
| Usable example | Fictional reading club: 3 actual notes, model, source, 3 questions and 9 authored checks; CLI coverage runs from the documented command |
| Independent operational execution | A fresh agent used the entry skill to incorporate a supplied cohort-2 rule into existing cohort-1 knowledge, preserving original source and IDs, adding justified links, updating model/prose, answering 7 questions with 21 recorded cases and saving a 3-task checkpoint |
| Actual resume | A separately requested one-task cycle with no new source returned no-change; 12 knowledge files, all knowledge IDs and revision 2 stayed unchanged, with only execution state updated |
| Independent audit execution | 78 input variations across four CLI commands; 633 total pre/post-fix calls, no traceback or input mutation. Empty-artifact false completeness, bool/float version acceptance and inline-code link false positives were reproduced and fixed, then rerun on the preserved cases |
| Semantic boundary | Separate direct reading blocked contradictory prose, wrong source locators, body/map divergence and an unregistered question even when the projection itself passed |
| Documentation | 114 authored local Markdown references resolved during the release check |

The operational evaluator wrote and reviewed its own synthetic update; its 21 cases are recorded behavior, not an independent factual benchmark. The audit evaluator used black-box input mutations without reading implementation or repository tests, and preserved both CLI revisions and outputs. The parent inspected reports, source text, resulting model/prose and current CLI hash.

The CLI validates a declared projection, not every file in a vault or every semantic constraint. RDF/OWL reasoning, external-source truth/freshness, host-wide automatic skill discovery, scheduled unattended execution and native Windows remain outside this validation. A maintenance skill runs through the current agent; no background service is implicitly installed.

## 0.1.0 — initial construction and publication (historical)

| Check | Observed result |
|---|---|
| Python unit tests | 14 passed: additive/idempotent installation, collision preservation including dangling links, selected-layer generation, existing-root protection, invalid profiles, read-only plans, generated context schema, local references, pinned upstream hashes, and UTF-8 profiles/Unicode paths under an ASCII locale |
| Skill frontmatter | All 11 passed the skill-creator validator, including installed-path readback |
| Plugin | `validate_plugin.py akm` passed |
| Local installation | 11 symlinks resolve to the package; SKILL contents and UI prompts read back; existing personal-ontology-interview retained |
| Discovery exercises | Bakery and literature scenarios generated different question clusters; follow-ups used new details; user stop was respected; no unsupported ontology/wiki completion claims |
| Actual initial wiki fixture | Knowledge-only profile without inbox/operating layers; actual ontology and exactly N001–N003 with source-linked content |
| Correction fixture | Original and revision 1 preserved; old carryover assertion deprecated; model, all affected notes, example and answer revised together; same initial 3 IDs |
| Claim uncertainty | Newly planted tree timing separated from the explicit yield rule as a proposed interpretation; only the uncertain part of the answer remains conditional |
| Competency checks | Normal, counterexample and unknown cases passed in the synthetic correction; 49 local links and reciprocal mappings resolved |
| Start/resume/skip routing | All 3 startup responses used discover without scaffolding; resume used prior context and explicit skip used the supplied material directly |

The first installer/generator positive tests failed before implementation. A later context-brief schema regression failed before adding required frontmatter and passed after the fix. Discovery exercises exposed mixed stop-signal and design-versus-built ambiguities; the shared contracts now specify both. Question clusters retain depth while identifying a focal issue and tracking unopened branches. The wiki fixture's initial explicit-rule/temporal-interpretation conflation was corrected, and the shared contract now expressly separates claims with different evidence bases.

The publication review reproduced locale-dependent file I/O and Unicode console output failures. Two regression tests failed before the fix and passed with explicit UTF-8 files and ASCII-safe JSON stdout. The public core's 18 Node tests also passed. Root AKM lint reports 12 placeholder-wikilink warnings from the unchanged bundled upstream templates; the minimal workspace, OKF export and secret checks have no warnings. Those template placeholders are not runtime knowledge links.

Natural-language startup simulations exercise all three phrases, plus resume and explicit interview-skip controls. They verify the generated behavior after reading the role descriptions and instructions. They do **not** measure the host application's automatic skill-selection recall across its entire installed catalog. Skill metadata should be refreshed on the next turn; host behavior is a separate integration boundary.

The author's AKM run record retains full synthetic artifacts, original/corrected answers, source hashes, installation readback and observed check results. They are deliberately outside the reusable package to keep personal environment paths and test knowledge out of runtime defaults.

Reproduce the tool tests from the `skill-suite/` directory:

```sh
python3 -m unittest discover -s tests -v
```

Run Codex's skill-creator `quick_validate.py` for each directory under `akm/skills`, and plugin-creator `validate_plugin.py akm`. Reproduce semantic exercises by giving a fresh evaluator the skills and a domain with explicit rules, requesting initial notes, then changing a rule and checking both model and prose. Preserving first answers and separating supplied rules from interpretations is required for an informative result.
