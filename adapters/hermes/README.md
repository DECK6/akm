# Hermes Adapter

Connects Hermes (multi-profile agent runtime) to an AKM instance.

## The four questions

| # | Item | Value |
|---|---|---|
| ① | AKM root | `/path/to/akm` (your clone location) |
| ② | Session start | All of `40-memory/` + `99-system/INDEX.md` (short). Hermes also keeps its native `memory`/`user` stores as pointers only |
| ③ | Routing | Every durable save passes the classification tree in `99-system/ROUTER.md` before it lands in a layer |
| ④ | Learn Back | On failure or repeated mistakes, apply the mapping table in `99-system/LOOP.md`: record under `70-evaluation/`, then fix the designated layer |

## Installation

Hermes loads a per-profile instruction file every session (`SOUL.md` at the main root or under `profiles/<profile>/`). Paste the AKM operating snippet there — operating rules belong in instruction files, never in the brain/memory stores (rules in a memory store is a layer violation).

## Division of labor with Hermes native features

AKM principle #4: **one body, everywhere else pointers.** Never duplicate content between Hermes native stores and AKM.

| Hermes feature | Division |
|---|---|
| `memory` tool (`~/.hermes/.../memory`) | Keep ONLY short session-critical pointers + a wikilink/path to the AKM note that holds the full content. Long facts move to AKM `30-context/` or `20-knowledge/` |
| `user` profile store | The durable user model lives in AKM `30-context/users/<user>.md`; the native `user` store keeps a one-line pointer |
| Hermes brain (`~/.hermes/brain`) | Migrate brain pages into AKM layers. During migration a brain page is authoritative until it is moved; after a page moves, the brain keeps a pointer to the AKM path |
| Skills (`~/.hermes/skills`) | Procedure *bodies* belong in AKM `50-procedures/`. A Hermes skill stays as trigger + "read and execute the corresponding AKM procedure" wrapper when the procedure is cross-tool. Tool-specific skills stay native |
| Profile `SOUL.md` / config | Identity and harness wiring stay native. Operating *knowledge* and *procedures* go to AKM |

## Multi-profile rule

Hermes runs several profiles against one machine. AKM is a **single shared instance** at the root above; profiles do not get separate AKM clones.

- Per-profile operating context → `30-context/projects/` or a profile section in `40-memory/`, tagged with the profile.
- Shared operating rules (routing boundaries, safety, critical facts) → `40-memory/` pointers + the full note in `30-context/` or `20-knowledge/`.
- A profile reads all of `40-memory/` at session start, then only the layer notes its task needs.

## Retrieval

- Semantic search across AKM markdown: reuse an existing local search engine (e.g. `qmd`) and add the AKM root as a collection.
- Explicit link/tag traversal: any doc-graph tool that parses `[[wikilinks]]` + frontmatter works on AKM as-is.

## Safety

AKM `99-system/SECURITY.md` runs **before** ROUTER. It matches Hermes' own rule: never store secret values, store their names/locations instead. Layer folders are gitignored and never leave the machine.
