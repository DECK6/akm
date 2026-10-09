# Validation — 2026-10-09

This release was checked as a portable local skill suite. Behavioral exercises used synthetic users and domains; they are not real-user research, a guarantee of factual accuracy, or cross-model benchmarks.

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
