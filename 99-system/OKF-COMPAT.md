# AKM-OKF Compatibility

AKM treats Open Knowledge Format (OKF) as an interoperability target, not as a replacement for the AKM core model.

AKM keeps its seven layers, strict frontmatter, wikilinks, ROUTER, and Verify -> Learn Back loop. OKF compatibility lives in export/import tooling that can present selected AKM notes as a portable Markdown bundle.

## Scope

The first supported direction is AKM -> OKF export.

- Default exported layers: `20-knowledge/`, `30-context/`, `50-procedures/`, `70-evaluation/`
- Default output: `dist/okf/`
- Export command: `node scripts/export-okf.mjs`
- Export lint command: `node scripts/lint.mjs --okf-export ./dist/okf`

`10-sources/` normally stays inside AKM. Exported notes point to source assets through OKF `resource`.

## Field Mapping

| AKM internal | OKF export | Rule |
|---|---|---|
| `akmType` | `type` | Converted to a human-readable OKF type, e.g. `failure-pattern` -> `Failure Pattern`. |
| First heading or filename | `title` | Used as display name. |
| `description` | `description` | Copied directly. |
| `sourcePath` or first external URL | `resource` | Source URI or canonical asset. |
| `date modified` | `timestamp` | Converted to ISO 8601. |
| `tags` | `tags` | Copied as a YAML list. |
| `[[wikilink]]` | Standard Markdown link | Converted for OKF consumers. |
| Bundle root metadata | `okf_version: "0.1"` | Written to root `index.md`. |

AKM does not add an internal `type` field. This avoids collisions with Obsidian vaults and other systems that already use `type`.

## Link Export

AKM authors keep using Obsidian wikilinks internally.

| Internal | OKF-style result |
|---|---|
| `[[Agent Knowledge Management]]` | `[Agent Knowledge Management](/20-knowledge/agent-knowledge-management.md)` |
| `[[ROUTER]]` | `[ROUTER](/99-system/ROUTER.md)` |
| `[[failure-pattern|failure pattern]]` | `[failure pattern](/70-evaluation/failure-patterns/failure-pattern.md)` |

Export resolves by explicit path, filename stem, aliases, and first heading when possible. Unresolved links are still converted to Markdown links and then reported by OKF lint as warnings.

## Directory Indexes

OKF `index.md` files are useful for progressive disclosure. AKM uses a split convention:

| Location | Internal AKM file | OKF export file |
|---|---|---|
| `20-knowledge/` | `INDEX.local.md` | `index.md` |
| `30-context/` | `INDEX.local.md` | `index.md` |
| `50-procedures/` | `INDEX.local.md` | `index.md` |
| `70-evaluation/` | `INDEX.local.md` | `index.md` |
| OKF bundle root | n/a | `index.md` with `okf_version: "0.1"` |

Generate local directory indexes with:

```bash
node scripts/index.mjs --write
```

The export script generates lowercase `index.md` files inside the OKF bundle.

## Log Boundary

OKF `log.md` is a bundle-level chronological change summary only.

Appropriate entries:

- bundle release notes
- schema changes
- export/import history

Do not move these AKM records into OKF `log.md`:

- failure analyses, which belong in `70-evaluation/`
- execution details, which belong selectively in `60-actions/`
- per-session instructions, which belong as pointers in `40-memory/`

## Import Tolerance Policy

AKM import tooling should be strict about preserving source material and tolerant about OKF producer variation.

| OKF input condition | AKM import behavior |
|---|---|
| Unknown `type` | Import as a generic concept candidate and set `nextAction: classify`. |
| Unknown frontmatter key | Preserve it; do not discard producer data. |
| Optional field missing | Warn, do not reject. |
| Broken link | Warn, do not reject the bundle. |
| `index.md` missing | Generate an index or warn. |
| Required `type` missing | Report OKF conformance error while preserving the original file. |

Import implementation is intentionally deferred until export behavior is stable.

## Resource Bridge

AKM does not add a required internal `resource` field. Export derives OKF `resource` from:

1. `sourcePath`
2. the first external URL in the note body

This keeps AKM schema stable while still giving OKF consumers a canonical URI when one exists.

## Conformance

An AKM-generated OKF bundle should satisfy these conditions:

- root `index.md` has `okf_version: "0.1"`
- concept files have YAML frontmatter with `type`
- directory-level `index.md` files exist for exported folders
- Obsidian wikilinks have been converted to standard Markdown links
- broken Markdown links are warnings, not hard rejection
- unknown frontmatter keys remain valid OKF extension fields

## Non-goals

- Do not weaken AKM required fields to OKF's minimal `type` requirement.
- Do not replace internal wikilinks with standard Markdown links.
- Do not use `log.md` as a substitute for `60-actions/` or `70-evaluation/`.
- Do not treat Google reference tooling as required AKM runtime infrastructure.
- Do not use filesystem path alone as permanent AKM identity.
