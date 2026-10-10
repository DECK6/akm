# AKM

각자의 도메인을 탐색하고 **AKM 지식 분류 구조 + 온톨로지 + LLM 위키**를 구축·운영하는 에이전트 지식관리 스킬 묶음입니다.

사용자는 **`$akm` 하나**로 시작하고 운영할 수 있습니다. 진입점이 현재 요청에 맞는 14개 역할을 연결합니다. 관련 질문을 묶어 집요하게 탐색하고, 사용자가 더 생각나지 않거나 정리/중단을 요청할 때 발견 대화를 마칩니다. 첫 위키 노트 3편 이후 자료 통합·질의·검수·확장·학습·맥락 인계까지 이어집니다.

[전체 안내](../README.ko.md) · [실행 예제](examples/reading-club/index.md) · [검증 기록과 한계](VALIDATION.md) · [설치](#로컬-설치)

기존 공개 [DECK6/akm](https://github.com/DECK6/akm)의 코어는 `akm-structure`의 기반 모듈로 포함했습니다. 인박스가 필요한지, 지식층을 얼마나 깊게 만들지, 기억·절차·실행·평가 같은 운영층이 어디까지 필요한지 인터뷰하여 **사용자별 구성을 생성**합니다. 전체 레이어를 강제하지 않으며 나중에 프로필을 바꾸고 확장할 수 있습니다. MIT 라이선스와 고정 리비전·파일 해시를 함께 보존합니다.

## 스킬 구성

| 스킬 | 역할 |
|---|---|
| `akm` | 현재 요청에 맞는 역할 연결 |
| `akm-discover` | 분야별 심층 발견 대화 |
| `akm-structure` | AKM 분류·저장·운영 구조 |
| `akm-ontology` | 개념·관계·조건·근거 설계 |
| `akm-wiki` | 초기 3편과 후속 지식 노트 |
| `akm-ingest` | 자료 보존·분류·지식 통합 |
| `akm-query` | 근거 기반 질의와 활용 |
| `akm-review` | 구조·근거·효용 검수 |
| `akm-grow` | 질문 중심 지식 확장 |
| `akm-explore` | 미답변 질문·반례·새 근거 탐색 |
| `akm-connect` | 빠진 모델/위키 연결과 분야 간 관계 보완 |
| `akm-lint` | 구조·출처·질문 커버리지·변경 영향 검사 |
| `akm-maintain` | 예산을 정한 자동 운영·정비·재개 |
| `akm-learn` | 실행 결과와 실패의 교정 |
| `akm-context` | 맥락 저장·재개·역할 인계 |

## 사용 예

**“akm 구축 시작해줘”**, **“온톨로지 구축 시작해줘”**, **“llm wiki 구축 시작해줘”** 모두 `akm-discover` 시작 인터뷰로 연결합니다. 분야에 맞는 관련 질문을 묶어 제시하고 답에서 새 가지가 나오면 계속 탐색합니다. 신규 구축의 진입점을 다르게 말해도 인터뷰부터 시작하며, 재개와 명시적인 인터뷰 생략 요청은 구별합니다.

온톨로지와 위키는 같은 개념·주장·출처 ID, 정본 정의와 변경 이력을 공유합니다. 위키에서 발견한 예외는 모델로 돌아가고, 모델의 조건 변경은 설명·예제·질의에도 반영합니다. 사용자 연구를 어떤 실행 규칙으로 옮겼는지는 [연구 통합표](akm/skills/akm/references/research-foundations.md)에 있습니다.

> $akm 내 분야의 지식 시스템을 만들고 싶어. 내가 알고 있는 것과 판단하는 방식을 충분히 파고들고, AKM 구조와 온톨로지, 첫 위키를 함께 만들자.

> $akm-discover 나는 조경을 공부하고 있어. 사람의 이동과 정원의 공간 경험을 주제로 깊이 질문해줘.

> $akm-ingest 이 자료를 기존 지식과 비교해서 반영해줘.

> $akm-grow 최근 답하지 못한 질문을 바탕으로 다음 지식을 확장해줘.

## 처음 만든 이후

하위 스킬 이름 대신 다음처럼 요청해도 됩니다.

| 요청 | 실제로 하는 일 |
|---|---|
| “이 새 자료를 반영해줘” | 원문 보존 → 기존 주장과 비교 → 모델·노트·예제 갱신 → 재검증 |
| “다음에 무엇을 조사해야 할까” | 못 답한 질문·약한 근거·반례에서 조사 후보 제안 |
| “내 지식을 알아서 확장해줘” | 허용된 자료와 예산 안에서 조사·편입·보강·연결·검증까지 실행 |
| “빠진 연결을 찾아서 보완해줘” | 고립 노트·모델 대응 누락 검사 → 근거가 있는 연결 추가 → 질문 경로 확인 |
| “얼마나 완성됐는지 검사해줘” | 구조 검사 + 선언한 질문의 답·조건·반례·미확인·근거 검토 |
| “다른 분야도 시작하자” | 새 분야 인터뷰 → 기존 공간에 독립 도메인 추가 → 첫 모델과 위키 |
| “지난번 작업 이어서 해줘” | 실제 파일·리비전·미완료 작업부터 재개 |

예를 들어 독서모임의 역할과 운영 규칙으로 처음 구축했다면, 다음 기수의 새 규칙을 편입할 때 기존 원문과 ID를 보존하면서 적용 기수·조건·주장을 갱신합니다. 같은 변경을 온톨로지와 기존 위키 설명에 함께 반영하고, 빠진 연결과 실제 질문의 답을 확인합니다. 다음 재개에서 새 근거가 없다면 중복 노트를 만들지 않고 변경 없음으로 마칠 수 있습니다. [가상 독서모임 예제](examples/reading-club/index.md)와 [후속 갱신·재개 검증](VALIDATION.md)이 이 흐름을 보여줍니다.

자동 확장을 요청할 때에는 분야와 허용 자료, 작업량을 함께 지정할 수 있습니다.

> $akm 도시 정원 지식을 확장해줘. 이 공간에 있는 자료만 사용해서 최대 3개 작업을 진행하고, 빠진 연결과 바뀐 답을 검사한 뒤 남은 작업을 저장해줘.

에이전트는 위임 범위·예산·리비전·작업 결과·다음 단계를 기록합니다. 요청 범위를 마쳤거나 예산을 소진했을 때, 사용자가 중단했거나 근거 있는 진전이 없을 때 멈춥니다.

자동 운영은 현재 에이전트가 실행하는 한 사이클입니다. 스킬 설치만으로 상시 백그라운드 작업이 시작되지는 않습니다. 정기 실행은 요청한 경우 호스트 스케줄러에 연결하며, 등록·조회한 결과로 활성화를 확인합니다. 지식층만 선택한 공간도 작은 상태 파일로 운영할 수 있습니다.

완결성은 **정한 범위의 질문에 현재 근거로 답할 수 있는지**를 뜻합니다. 도메인의 모든 사실을 알고 있다거나 린트 통과가 사실 정확성을 보증한다는 뜻이 아닙니다. [지속 운영 규약](akm/skills/akm/references/lifecycle.md)에서 위임 범위·중단·재개·작업 상태를 정의합니다.

## 실행 가능한 지식 검사

`skill-suite/`에서 가상 독서모임 예제를 바로 검사할 수 있습니다. 예제에는 원문·모델·실제 위키 3편·질문 검증 기록이 있습니다.

```sh
python3 akm/scripts/knowledge.py lint --root examples/reading-club --map examples/reading-club/knowledge-map.json
python3 akm/scripts/knowledge.py coverage --root examples/reading-club --map examples/reading-club/knowledge-map.json
python3 akm/scripts/knowledge.py frontier --root examples/reading-club --map examples/reading-club/knowledge-map.json
python3 akm/scripts/knowledge.py impact --root examples/reading-club --map examples/reading-club/knowledge-map.json --id S1
```

기존 위키·RDF·Markdown 모델은 그대로 유지합니다. 에이전트가 필요한 ID·주장·노트·근거 대응을 [검사 연결표](akm/skills/akm/references/audit-map.md)로 읽어 내어 검사합니다. 도구는 읽기 전용이며 출처의 진위나 문장 의미를 자동 판정하지 않습니다. 연결표 밖의 파일과 복잡한 Markdown/OWL 제약은 별도 검토합니다.

## 기존 공간에 새 분야 추가

생성기에서 만든 공간은 새 도메인 프로필로 `workspace.py domain-plan` 후 `domain-init`을 실행할 수 있습니다. 전역 설정과 기존 도메인은 보존하고 해당 도메인의 브리프·출처 장부·상태를 추가합니다. 그 뒤 기존 INDEX에 연결하고 인터뷰·모델·위키를 이행합니다. 커스텀 위키는 기존 구조에 매핑하며 생성기 형식을 강제하지 않습니다.

## 로컬 설치

Python 3.10+가 있으면 Codex의 사용자 스킬 경로에 이 묶음을 연결할 수 있습니다. 아직 저장소가 없다면 다음 명령으로 받습니다.

```sh
git clone https://github.com/DECK6/akm.git
cd akm/skill-suite
```

아래 명령은 이 README가 있는 `skill-suite/` 디렉터리에서 실행합니다. 저장소 루트에 있다면 먼저 `cd skill-suite`를 실행하세요.

```sh
python3 akm/scripts/install.py
```

기본 목적지는 `CODEX_HOME/skills`, CODEX_HOME이 없으면 `~/.codex/skills`입니다. `--dest`로 다른 스킬 디렉터리를 지정할 수 있습니다. 기존의 같은 이름 스킬을 덮어쓰지 않으며, 동일 패키지의 링크는 재실행해도 유지합니다. 심볼릭 링크 방식이므로 설치 후 패키지 폴더를 이동하지 마세요.

이 저장소에서 설치했다면 업데이트도 같은 `skill-suite/` 디렉터리에서 실행합니다. 연결된 스킬 본문이 갱신되고, 설치기를 다시 실행하면 새 역할도 연결됩니다.

```sh
git pull --ff-only
python3 akm/scripts/install.py
```

설치 후 `$akm`으로 요청하세요. 자연어만으로 스킬을 자동 선택하는지는 호스트 환경에 따라 달라집니다.

`akm/`은 `.codex-plugin/plugin.json`을 갖춘 플러그인 소스입니다. 위 명령은 스킬을 직접 등록하며 마켓플레이스 등록을 수행하지 않습니다. 다른 에이전트에서는 `akm/skills/`의 형제 폴더를 함께 두고 `akm/SKILL.md`를 진입점으로 읽게 할 수 있습니다. 다른 에이전트의 자동 등록 동작은 별도 검증 대상입니다.

공통 규약은 `akm/skills/akm/references/`에 있습니다. 모든 역할은 필요한 규약과 자기 지침만 읽습니다. 특정 사용자의 경로나 도메인 데이터, 유료 API, 그래프 DB, gstack 설치가 필수로 들어 있지 않습니다.

## 검증

```sh
python3 -m unittest discover -s tests -v
```

스킬 구조·참조와 설치 동작을 검사합니다. 실제 분야 지식의 정확성을 보증하는 검사는 아닙니다. 역할 동작 검증과 한계는 [VALIDATION.md](VALIDATION.md)에 기록합니다.

참고한 [gstack](https://github.com/garrytan/gstack) 및 [office-hours](https://github.com/garrytan/gstack/blob/8bb6d652707615e6a13b20ab162bf00dad9c9392/office-hours/SKILL.md)의 적용 범위는 [출처 기록](akm/skills/akm/references/provenance.md)에 있습니다.
