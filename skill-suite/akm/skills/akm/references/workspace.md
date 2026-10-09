# AKM 작업공간과 공통 산출물

## 기존 환경 우선

이미 지식베이스가 있으면 경로를 조사하고 아래 역할에 대응시킨다. 폴더 이름을 맞추기 위해 옮기지 않는다. 사용자/팀의 ROUTER와 SCHEMA가 있으면 이를 쓴다. 아래는 공개 AKM의 기반 구조이며 전부 필수라는 뜻이 아니다. 신규 공간은 `akm-structure`의 [맞춤 설계](../../akm-structure/references/personalization.md)로 선택한 전용층만 만든다.

| 기본 경로 | 역할 |
|---|---|
| `00-inbox/` | 분류 전 자료와 새 후보 |
| `10-sources/` | 수정하지 않는 원문과 출처 |
| `20-knowledge/` | 재사용 설명·개념·비교·위키 |
| `30-context/` | 사용자·도메인·프로젝트의 목적과 제약 |
| `40-memory/` | 매번 필요한 짧은 운영 포인터 |
| `50-procedures/` | 반복 실행 절차와 체크리스트 |
| `60-actions/` | 재현·복구·인계에 필요한 실행 기록 |
| `70-evaluation/` | 검증·품질 기준·실패와 교정 근거 |
| `80-outputs/` | 사용자에게 전달할 최종 산출물 |
| `90-archive/` | 수명이 끝난 항목의 복구 가능한 보존 |
| `99-system/` | INDEX, ROUTER, SCHEMA, LOOP, LOG |

분류 역할의 기본 대응은 원문→10, 검증/실패→70, 반복 절차→50, 특정 사용자/도메인 제약→30, 짧은 운영 포인터→40, 재사용 지식→20, 의미 있는 실행→60, 외부용 결과→80이다. 실제 활성 위치는 PROFILE.json과 ROUTER로 정한다. inbox가 없으면 즉시 분류하고 미분류를 상태에서 추적한다. 생략한 층을 다른 이름으로 강제 생성하지 않는다. 불필요한 성공 로그와 긴 memory 본문을 만들지 않는다.

신규 시스템 문서의 최소 내용:

- INDEX: 실제 정본과 도메인 상태로 가는 링크.
- ROUTER: 위 분류의 우선순위와 원문 보존·보관 규칙.
- SCHEMA: 노트의 필수 메타데이터·허용 상태·ID·링크 규칙.
- LOOP: 수집→분류→합성→맥락 연결→활용→검증→교정.
- LOG: 의미 있는 변경 하나당 결과와 정본 링크 한 줄.

신규 노트의 기본 필드: `description`, `akmLayer`, `akmType`, `trustLevel`, `date created`, `date modified`. 출처는 `sourcePath`를 더한다. 레이어 값은 source, knowledge, context, operational-memory, procedure, action, evaluation, output. 검증 상태는 draft, raw, unverified, reviewed, canonical, deprecated이며 자동 생성만으로 canonical로 올리지 않는다. 로컬 스키마가 있으면 로컬 값이 우선한다.

## 도메인별 정본

필요한 층을 선택했을 때의 권장 배치다. 실제 위치는 `akm-state.json`에 기록한다. context층이 없으면 브리프를 `99-system/domains/<domain-id>/`에 두고, source층이 없으면 외부 원위치를 출처 장부로 연결한다. 전용 evaluation이 없어도 노트의 근거·검증 상태는 유지한다.

```text
30-context/domains/<domain-id>/
  domain-brief.md       범위, 목적, 숙련도, 실제 용어, 열린 질문
  discovery.md          탐색 지도와 인터뷰 출처 위치
  akm-state.json        경로와 진행 상태
20-knowledge/<domain-id>/
  ontology.md           의미 모델
  index.md              질문-노트-관계 색인
  <topic-a>.md          첫 지식 노트
  <topic-b>.md
  <topic-c>.md
```

출처 장부는 `10-sources/`의 개별 불변 원문을 참조하는 갱신 가능한 색인으로 `99-system/` 또는 도메인 맥락에 둔다. 불변 원문에 인덱스를 덧써서 갱신하지 않는다. 기존 환경의 출처 등록 방법이 있으면 따른다. 인터뷰 원문과 LLM의 탐색 요약도 서로 구별한다.

## 상태 계약

작은 JSON을 사용한다. 경로는 지식 루트를 기준으로 기록하고 기존 환경이면 그 환경의 경로 체계를 따른다.

```json
{
  "version": 1,
  "domain_id": "domain-id",
  "domain": "",
  "goal": "",
  "entry_intent": "akm",
  "active_role": "akm-discover",
  "discovery": {"status": "in-progress", "stop_signal": null, "open_branches": []},
  "paths": {},
  "ontology_revision": 0,
  "knowledge_revision": null,
  "initial_note_ids": [],
  "notes": [],
  "open_questions": [],
  "backlog": [],
  "last_change": "",
  "next_action": "",
  "updated_at": ""
}
```

`paths`에는 brief, discovery, ontology, sources, index, evaluation 등 실제로 만든 파일을 등록한다. 처음부터 없는 파일을 완료 산출물로 등록하지 않는다. `notes`의 각 항목은 id, path, question_ids, ontology_ids, source_ids, status를 가진다. `initial_note_ids`는 첫 구축 시 실제 작성한 3개만 기록하고 후속 확장에서 늘리지 않는다.

`entry_intent`는 최초 요청의 중심인 akm, ontology, wiki 중 실제 값을 기록한다. `knowledge_revision`은 모델과 노트를 함께 검증했을 때 부여하며 실제 변경 이력/사본·검증 기록을 가리킨다. 생성기가 아직 값을 모르면 생략하거나 null로 두고 지어내지 않는다. 연결표는 실제 도메인 색인 또는 별도 경로로 등록해 Q/C/R/A/N/S를 양쪽에서 찾게 한다.

`discovery.status`는 in-progress, user-saturated, user-directed, paused 중 하나다. stop_signal에는 사용자가 실제로 한 말과 범위를 적는다. 묵묵부답이나 LLM의 충분성 판단을 사용자 포화로 쓰지 않는다.

`backlog`에는 질문, 필요한 근거, 예상 변경 대상, 추천 이유를 남긴다. 할 일은 실행 이력과 구별한다. 다른 에이전트가 상태를 읽을 때 원문 전체를 복사하지 않아도 실제 정본을 찾을 수 있어야 한다.

역할 결과에는 필요할 때 `designed`(구성안만 있음), `written`(실제 파일 작성), `verified`(검증 근거 있음)를 구분한다. 인터뷰 종료는 구조 구축 완료가 아니고, 구조 생성은 온톨로지·위키 완료가 아니다. 검증한 명령/관찰과 실제 경로로 상태를 뒷받침한다.

구축 후에는 [지속 운영](lifecycle.md)의 operations.policy/cycle과 backlog 상태를 필요한 만큼 추가한다. 검사 연결표는 paths.audit_map으로 실제 위치를 등록할 수 있다. 기존 상태의 version 1 및 기존 notes/initial_note_ids를 보존한다.

## 기존 공간에 새 도메인 추가

생성된 PROFILE.json이 있는 공간에서는 workspace.py의 `domain-plan --profile <새 분야 프로필> --root <기존 루트>`로 검토한 뒤 `domain-init`으로 도메인별 PROFILE·브리프·출처 장부·상태만 추가한다. 전역 PROFILE·INDEX·기존 분야는 덮어쓰지 않는다. 반환된 next_action에 따라 기존 INDEX에 새 상태 링크를 등록하고 실제 인터뷰 기록을 이행한다. 이 링크 등록과 지식 작성 전에는 신규 분야 구축 완료가 아니다.

새 도메인의 층은 이미 허용된 전역 층의 부분집합이어야 하고 inbox 선택은 전역 정책과 같아야 한다. 새 층이 필요하면 structure의 변경 계획으로 처리한다. 커스텀 환경은 PROFILE을 위조해 맞추지 않고 실제 정책에 따라 도메인 브리프·모델·노트를 매핑한다.

domain-init은 완성된 생성 내용을 숨김 staging 디렉터리에도 보존하고 `recovery_stage`로 반환한다. I/O 중단 시 부분 도메인이 남을 수 있으므로 성공 결과와 파일을 확인한 후 INDEX에 등록한다. 재실행은 기존 도메인을 덮어쓰지 않으며, 실패 시 staging을 근거로 검토해 복구한다.
