# AKM-MANIFEST

Machine-readable compatibility values are intentionally simple so agents can inspect them without extra tooling.

| Field | Value | Meaning |
|---|---|---|
| `akmVersion` | `0.2` | AKM core version. |
| `schemaVersion` | `0.2` | Frontmatter schema version. |
| `okfExportVersion` | `0.1` | OKF export target currently supported by `scripts/export-okf.mjs`. |
| `generatedAt` | export-time | Written into OKF bundle root `index.md`. |
| `sourceRoot` | export-time | Written into OKF bundle root `index.md`. |

The canonical schema remains `99-system/SCHEMA.md`. OKF compatibility rules live in `99-system/OKF-COMPAT.md`.
