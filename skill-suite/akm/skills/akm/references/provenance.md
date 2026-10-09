# 참고 출처와 적용 범위

2026-10-09 사용자가 gstack을 지식관리용 스킬 묶음의 참고로 지정했다.

- [gstack 프로젝트](https://github.com/garrytan/gstack): 역할별 독립 스킬과 작업 전후 인계를 참고했다.
- [office-hours, 고정 리비전](https://github.com/garrytan/gstack/blob/8bb6d652707615e6a13b20ab162bf00dad9c9392/office-hours/SKILL.md): 기존 맥락 읽기, 구체적 근거 탐색, 전제 재검토, 다음 행동을 참고했다.
- [startup diagnostic](https://github.com/garrytan/gstack/blob/8bb6d652707615e6a13b20ab162bf00dad9c9392/office-hours/sections/phase-2a-startup-diagnostic.md), [builder brainstorm](https://github.com/garrytan/gstack/blob/8bb6d652707615e6a13b20ab162bf00dad9c9392/office-hours/sections/phase-2b-builder-brainstorm.md): 사용자 상황에 맞게 질문의 관점을 바꾸는 원리를 참고했다.

사용자의 명시적 수정에 따라 **한 번에 한 질문** 방식은 채택하지 않았다. 도메인별 질문 묶음과 집요한 후속 탐색을 사용하며, 사용자가 더 생각나지 않거나 진행/중단을 요청할 때 종료한다. 사업성·매출 질문, 강압적인 말투, gstack의 설치·텔레메트리·동기화·승인 절차는 이식하지 않았다.

공개 [DECK6/akm](https://github.com/DECK6/akm/tree/f26ace2a16caba724b24db12cbee238ebb52498f) 코어를 `akm-structure/assets/upstream-akm/`에 포함했다. 2026-10-09 확인한 고정 커밋은 `f26ace2a16caba724b24db12cbee238ebb52498f`다. 배포와 무관한 `.github/`를 제외한 원본 141개 파일, MIT LICENSE와 저작권 표시를 그대로 보존했다. [원본 매니페스트](../../akm-structure/assets/upstream-manifest.json)에 파일별 SHA-256을 기록했다. 맞춤 프로필과 생성기는 별도 구현이며 원본의 모든 레이어/규칙을 그대로 강제하지 않는다.

AKM 레이어와 운영 루프는 공개 코어를 일반 환경에서도 사용할 수 있게 적용한 것이다. 사용자의 개인 볼트는 공개 코어의 원본으로 취급하지 않았다. 사용자의 개인 데이터나 절대경로는 이 패키지의 규칙이 아니다. 기존 설치의 운영 규칙은 각 사용자의 시스템 문서를 읽어 적용한다. 연구별 반영 범위는 [연구 통합](research-foundations.md)에 있다.

gstack의 원문 코드는 포함하지 않고 역할과 탐색 원리를 독자적인 지침으로 적용했다. gstack의 공식 제품, 확장판 또는 저자가 검증한 구현이라고 표현하지 않는다. 위에 명시한 공개 AKM 코어 포함과 구별한다.
