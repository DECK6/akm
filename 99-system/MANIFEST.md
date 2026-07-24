# AKM-MANIFEST

Machine-readable compatibility values are intentionally simple so agents can inspect them without extra tooling.

| Field | Value | Meaning |
|---|---|---|
| `akmVersion` | `0.3` | AKM core version. |
| `schemaVersion` | `0.2` | Frontmatter schema version. |
| `okfExportVersion` | `0.1` | OKF export target currently supported by `scripts/export-okf.mjs`. |
| `evidenceSchemaVersion` | `1.0.0` | EvidenceRow and EvidencePacket contract in `EVIDENCE-SCHEMA.md`. |
| `taskContractVersion` | `1.0.0` | Bounded task contract in `TASK-CONTRACT-SCHEMA.md`. |
| `enforcementVersion` | `1.0.0` | Read-only operational validators exposed through `scripts/lint.mjs`. |
| `generatedAt` | export-time | Written into OKF bundle root `index.md`. |
| `sourceRoot` | export-time | Written into OKF bundle root `index.md`. |

The canonical note schema remains `99-system/SCHEMA.md`. Evidence and task contracts are separately versioned because they validate derived retrieval and execution-control artifacts rather than AKM note frontmatter. OKF compatibility rules live in `99-system/OKF-COMPAT.md`.
