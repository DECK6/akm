# AKM-GLOSSARY

Glossary for the AKM system. Define new terms here before using them.

## Core concepts

- **AKM (Agent Knowledge Management)**: a knowledge-operating architecture that makes agents learn and work better over time by storing external knowledge, operational memory, execution procedures, project context, and verification feedback separately — and reconnecting them.
- **7-layer**: the AKM layer structure. Source → Knowledge → Context → Operational Memory → Procedural → Action → Evaluation. (Output and Archive are auxiliary layers.)
- **LLM Wiki**: Karpathy's pattern — compiling sources into a reusable LLM-readable Markdown knowledge base. Adopted as the design pattern for AKM's Knowledge Layer; it is not the whole of AKM.
- **CMDS**: Connect → Merge → Develop → Share. A process grammar for the knowledge lifecycle. Used as frontmatter metadata and routing criteria, not as folders.
- **Learn Back**: routing execution outcomes (success, failure, feedback) back into the layer that must change. The heart of the loop — without it, the system is mere automation.
- **Core–adapter separation**: the AKM core is tool-agnostic Markdown. Each harness (Claude Code, Codex, OpenClaw, custom agents) connects through one thin entry-point file (an adapter).
- **Three stores (Memory / Brain / Vault)**: the loading-level grouping of the seven layers. Memory = `40` (always loaded, pointers only). Brain = `50`+`60`+`70` (read when acting — procedures, decisions, failures). Vault = `10`+`20`+`30`+`80` (read when knowledge is needed). Layers define storage semantics; stores define loading behavior.

## Storage terms

- **Operational pointer**: a 1-to-few-line stable rule kept in `40-memory/`. The full content lives in another layer; the pointer carries only the location and the essentials.
- **Canonical note**: the reference note for its topic. `trustLevel: canonical`.
- **Raw preservation**: originals in `10-sources/` are never modified. Interpretation and summary happen in `20-knowledge/` as separate files.
- **Selective storage (Action Layer)**: not every execution is recorded. Only what reproduction, verification, failure recovery, or handoff requires goes into `60-actions/`.
- **Promotion**: converting knowledge or experience into another layer once it meets the conditions. Example: a repeated procedure → skill; a repeated failure → failure-pattern.

## Harness terms

- **Harness**: an agent runtime that uses the AKM core — Claude Code, Codex, OpenClaw, or any custom agent.
- **Adapter**: the entry-point document that makes a harness read and write AKM. Lives in `adapters/<harness>/`. Every adapter must define: ① the AKM root path ② what to read at session start ③ where the routing rules are ④ how Learn Back is triggered.
- **Native memory**: a harness's own memory mechanism (Claude Code auto-memory, OpenClaw `MEMORY.md`, a custom agent's brain). Holds harness-specific pointers only; shared rules live in AKM. One body, everywhere else pointers.

## trustLevel lifecycle

```text
raw → unverified → reviewed → canonical
                       ↓
                  deprecated → 90-archive/
```
