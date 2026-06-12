# AKM — Agent Knowledge Management (한국어 안내)

> 기본 문서는 [README.md](README.md) (영문)입니다. 시스템 파일(00-system, adapters, templates)은 영어가 기본이며, 레이어에 저장하는 노트는 어떤 언어든 무방합니다.

AI 에이전트용 범용 지식 운영 시스템. 순수 마크다운 — DB 없음, 실행 코드 없음. Claude Code, Codex, OpenClaw 및 파일을 읽을 수 있는 모든 에이전트에서 동작합니다.

## 핵심 개념

LLM Wiki가 "AI가 읽을 수 있는 지식 지도"라면, AKM은 그 지도 위에서 에이전트가 **무엇을 배우고, 어디에 저장하고, 어떻게 실행·검증하고, 실패를 어느 레이어로 되돌릴지**까지 다루는 지식 운영체계입니다.

7개 레이어로 저장소를 분리합니다:

| 레이어 | 폴더 | 기준 |
|---|---|---|
| Source | `10-sources/` | 원본 보존, 수정 금지 |
| Knowledge | `20-knowledge/` | 누구에게나 참인 재사용 지식 |
| Context | `30-context/` | 이 사용자·프로젝트에서만 참인 것 |
| Operational Memory | `40-memory/` | 매 세션 먼저 알아야 할 짧은 포인터 |
| Procedural | `50-procedures/` | 반복 실행 절차 |
| Action | `60-actions/` | 재현·검증·인수인계에 필요한 기록만 |
| Evaluation | `70-evaluation/` | 실패 패턴·품질 기준 — 실패가 학습이 되는 곳 |

7개 레이어는 로딩 관점에서 3개 저장소로 묶입니다:

- **Memory** (`40`) — 매 세션 항상 로드, 포인터만
- **Brain** (`50`+`60`+`70`) — 작업할 때 읽음: 절차, 결정, 실패 패턴
- **Vault** (`10`+`20`+`30`+`80`) — 지식이 필요할 때 읽음: 원본, 지식, 맥락, 산출물

레이어 = 저장 의미론(무엇을 어디에), 저장소 = 로딩 동작(언제 읽는가). 자기 brain/메모리가 이미 있는 에이전트는 `adapters/custom/` 참조 — 네이티브는 그대로 두고 포인터로 연결합니다.

운영 루프: **Ingest → Classify → Compile → Contextualize → Execute → Verify → Learn Back**. 마지막 Learn Back(실패를 원인 레이어 수정으로 되돌리기)이 없으면 AKM이 아닙니다.

## 빠른 시작

1. 클론 후 `adapters/`에서 사용하는 도구의 어댑터 선택 (Claude Code / Codex / OpenClaw / 커스텀)
2. 스니펫을 해당 도구의 진입점 파일(CLAUDE.md, AGENTS.md 등)에 붙여넣고 `/path/to/akm`을 실제 경로로 교체
3. 끝. 에이전트에게 지식 저장·조회를 시키면 `00-system/ROUTER.md`의 분류 트리를 따라 동작합니다

## 저장 규칙 요약

- **Memory(40)**: 짧고·안정적이고·반복 필요하고·매번 먼저 알아야 하고·포인터로 충분할 때만. 긴 지식 금지
- **Knowledge(20)**: 다시 읽을 가치, 여러 프로젝트 재사용, 도메인 지식
- **Procedure(50)**: 반복되고·절차 있고·실패 지점 있고·검증법 있을 때만
- **Evaluation(70)**: 반복될 수 있는 실패, 품질 기준
- **Action(60)**: 재현·검증·인수인계용만 선별 저장

레이어에 저장되는 개인 지식은 gitignore 처리되어 추적되지 않습니다 — 클론 후 사적으로 사용하면서 시스템 업데이트만 pull 받을 수 있습니다.

검증: `bun scripts/lint.mjs` (또는 node) — 스키마·enum·레이어 배치·깨진 링크·INDEX 정합성·시크릿 패턴 검사. 보안 규칙은 `00-system/SECURITY.md`.

라이선스: [MIT](LICENSE)
