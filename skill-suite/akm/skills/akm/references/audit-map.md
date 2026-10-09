# 온톨로지·위키 검사 연결표 v1

`scripts/knowledge.py`는 기존 의미 모델과 위키의 **읽기 전용 투영**을 검사한다. Markdown, JSON, RDF 등 원래 정본을 유지하고 에이전트가 실제로 읽은 내용을 아래 연결표로 옮긴다. 연결표는 사실의 새 정본이 아니며 원본이 바뀌면 다시 읽어 갱신한다. 자동 RDF 변환기나 완전한 Markdown 파서가 아니다.

## 실행

패키지 루트(`akm/`)를 기준으로 다음처럼 실행한다. `--map`은 선택한 지식 루트 안의 실제 JSON 파일이다. 스크립트는 어디에서도 원문·노트·연결표를 쓰거나 삭제하지 않는다.

```sh
python3 scripts/knowledge.py lint --root /path/to/knowledge --map /path/to/knowledge/knowledge-map.json
python3 scripts/knowledge.py coverage --root /path/to/knowledge --map /path/to/knowledge/knowledge-map.json
python3 scripts/knowledge.py frontier --root /path/to/knowledge --map /path/to/knowledge/knowledge-map.json
python3 scripts/knowledge.py impact --root /path/to/knowledge --map /path/to/knowledge/knowledge-map.json --id S1 --id C2
```

Python 3.10+와 표준 라이브러리만 필요하다. 출력은 JSON이다. 종료 코드는 0(구조 오류 없음, 경고 가능), 1(구조 오류 발견), 2(잘못된 입력/실행 실패)다. 0만으로 의미 검수나 완결성을 통과했다고 하지 않는다. `coverage.complete_for_declared_scope`와 findings를 읽는다.

배포본의 `skill-suite/examples/reading-club/`에는 실제 3편·모델·출처·검사 기록·연결표가 있는 가상 예제가 있다. 저장소 루트에서는 `python3 skill-suite/akm/scripts/knowledge.py lint --root skill-suite/examples/reading-club --map skill-suite/examples/reading-club/knowledge-map.json`로 실행한다.

## 필드

루트: `version: 1`, `domain_id`, 양의 정수 `revision`, 정본 `model_path`, `artifacts`, 아래 7개 배열과 `checks`. 모든 ID는 연결표 내에서 고유하다. 여러 도메인을 조회할 때는 `domain_id:local_id`로 구별하고 명시한 범위 밖의 ID를 자동 병합하지 않는다.

| 배열 | 각 행의 필수 필드 |
|---|---|
| types | `id` |
| concepts | `id`, `definition`, `type_ids` |
| relations | `id`, `definition`, `domain_types`, `range_types` |
| claims | `id`, `subject`, `predicate`, `object`, `conditions`, `basis`, `status`, `evidence` |
| sources | `id`, `read`(불리언), `path` 또는 `url` |
| notes | `id`, `path`, `status`, `question_ids`, `concept_ids`, `claim_ids`, `source_ids`, `links` |
| questions | `id`, `text`, `status` |

ID 집합 필드는 문자열 배열이다. `domain_types`/`range_types`가 비어 있으면 그 쪽 종류 제약이 없다는 뜻이며, 채워져 있으면 개념의 `type_ids` 중 하나가 맞아야 한다. 상속·추이·역관계는 추론하지 않는다. 정본 모델의 추가 제약은 형식별 검증기 또는 의미 검수로 검사한다.

claim의 `basis`: source-supported, user-stated, llm-proposed. `status`: current, proposed, disputed, deprecated, needs-review. `conditions`에는 실제 적용 범위를 적으며 무조건이면 그 의미를 명시한다. evidence는 `{"source_id":"S1", "locator":"실제 절/문장/페이지/대화 위치"}` 배열이다. URL 목록만으로 주요 주장의 근거 대응을 대신하지 않는다.

note의 `status`: current, draft, needs-review, deprecated. question의 `status`: open, answered, deferred. 보류에는 정본 브리프/질문에 이유를 남긴다. `links`는 다른 노트의 N-ID이며 방향이 있다. 기계가 본문 링크의 의미와 links 목록의 동일성까지 증명하지 않으므로 connect/review에서 대조한다. Q↔C/R/A↔N↔S의 역방향은 이 연결표에서 계산하고 별도 정본을 중복 작성하지 않는다.

`artifacts`는 `{ "root-relative/path.md": "sha256..." }` 형태다. 모델·등록 노트·로컬 출처·검사 기록의 파일 해시를 모두 포함한다. 모든 로컬 경로는 선택한 루트 내부를 가리켜야 한다. 절대경로/루트 밖 심볼릭 링크를 읽지 않는다. 외부 원문은 HTTP(S) URL로 등록할 수 있으나 도구가 접근·진위·현재성을 확인하지 않으므로 실제 읽기 근거는 에이전트가 별도로 남긴다.

빈 등록 파일은 오류이며, 현재 설명 노트에 claim_ids가 없으면 주요 주장 대응을 검토할 경고를 남긴다. 비어 있지 않다는 것은 내용의 타당성을 보장하지 않는다. 직접 검토해야 할 차원은 아래 범위를 따른다.

`checks`는 다음 행들의 배열이다.

```json
{"question_id":"Q1", "case":"counterexample", "result":"pass", "revision":1, "path":"validation.md"}
```

case는 normal/counterexample/unknown, result는 pass/fail/unknown이다. path의 실제 기록에는 질문·근거에서 정한 기대·실제 답·차이·판정을 쓴다. 같은 revision의 세 종류가 모두 pass이고 현재 답 노트가 있으며 경고/오류가 없을 때에만 선언 범위의 기계적 완결성이 true다. deferred만 있거나 질문이 없는 공간은 완결로 판정하지 않는다.

## 검사 범위와 후속 작업

- findings는 `code`, `target`, `message`, `severity`, 담당 `role`을 가진다.
- frontier의 작업은 ID·대상·이유·우선순위가 있는 후보이며 실행/승인/완료를 뜻하지 않는다. maintain이 범위에 맞게 골라 실제 수행한다.
- impact는 출처/종류/개념/관계 → 주장 → 노트 → 질문의 의존성을 따라간다. 관련 노트의 참조까지 포함하므로 실제 편집 범위는 본문을 읽어 좁힌다.
- 고립 노트는 정보성 신호다. 고립 자체로 거짓 지식이라는 뜻이 아니다.
- 연결표에 등록하지 않은 파일은 전체 검사에 포함되지 않는다. review가 실제 도메인 색인·파일 목록과 연결표를 대조하여 누락을 확인해야 한다.
- 일반 inline Markdown 링크의 파일 존재를 확인한다. Obsidian wikilink, reference-style 링크, anchor, 복잡한 괄호/공백 문법, 외부 URL 응답, 의미 모순은 별도 검사다. 필요한 경우 기존 AKM/Obsidian/RDF 도구를 병행하고 미검사를 표시한다.

해시 변경은 원문 훼손이라고 단정하지 않는다. 노트가 정상 갱신되었을 수도 있으므로 실제 내용·변경 이력을 확인한다. 해시를 읽어 업데이트하는 것과 새 사실을 검증하는 것은 별개다.
