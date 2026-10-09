#!/usr/bin/env python3
"""Plan or initialize a new AKM workspace from interview-derived choices.

This scaffolds structure only. It never invents interviews, ontology claims or
wiki notes, and never edits an existing workspace.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re

LAYERS = {
    'sources': ('10-sources', '원문·출처 보존'),
    'knowledge': ('20-knowledge', '재사용 지식·온톨로지·위키'),
    'context': ('30-context', '사용자·도메인·프로젝트 맥락'),
    'memory': ('40-memory', '매번 필요한 짧은 포인터'),
    'procedures': ('50-procedures', '반복 실행 절차'),
    'actions': ('60-actions', '재현·복구·인계에 필요한 기록'),
    'evaluation': ('70-evaluation', '검증·실패·교정'),
    'outputs': ('80-outputs', '전달용 최종 산출물'),
    'archive': ('90-archive', '수명이 끝난 내용의 보존'),
}


def validate(profile):
    if not isinstance(profile, dict) or profile.get('version') != 1:
        raise ValueError('Invalid profile: version must be 1')
    domain_id = profile.get('domain_id')
    if not isinstance(domain_id, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', domain_id):
        raise ValueError('Invalid profile: domain_id must be a safe lowercase slug')
    for field in ['domain', 'purpose']:
        if not isinstance(profile.get(field), str) or not profile[field].strip():
            raise ValueError(f'Invalid profile: {field} must be a non-empty string')
    if type(profile.get('inbox')) is not bool:
        raise ValueError('Invalid profile: inbox must be a boolean')
    layers = profile.get('layers')
    if not isinstance(layers, list) or not layers or any(not isinstance(x, str) or x not in LAYERS for x in layers):
        raise ValueError('Invalid profile: layers must list known layer names')
    if len(layers) != len(set(layers)):
        raise ValueError('Invalid profile: duplicate layers')
    if profile.get('knowledge_depth') not in ['none', 'reference', 'linked', 'synthesis']:
        raise ValueError('Invalid profile: unknown knowledge_depth')
    if ('knowledge' in layers) != (profile['knowledge_depth'] != 'none'):
        raise ValueError('Invalid profile: knowledge layer and depth disagree')
    if profile.get('operating_depth') not in ['none', 'assist', 'execute']:
        raise ValueError('Invalid profile: unknown operating_depth')
    decisions = profile.get('decisions')
    if not isinstance(decisions, list) or not decisions:
        raise ValueError('Invalid profile: record interview-derived decisions')
    for row in decisions:
        if not isinstance(row, dict) or not all(k in row for k in ['component', 'choice', 'reason', 'basis']):
            raise ValueError('Invalid profile: incomplete decision')
        if not all(isinstance(row[k], str) and row[k].strip() for k in ['component', 'reason', 'basis']):
            raise ValueError('Invalid profile: empty decision metadata')
        if row['basis'] not in ['user-stated', 'llm-proposed']:
            raise ValueError('Invalid profile: unsupported decision basis')
    if not isinstance(profile.get('pending_questions', []), list):
        raise ValueError('Invalid profile: pending_questions must be a list')
    return profile


def build(profile):
    validate(profile)
    active = set(profile['layers'])
    folders = sorted([LAYERS[k][0] for k in active] + ['99-system'] + (['00-inbox'] if profile['inbox'] else []))
    domain_id = profile['domain_id']
    context_dir = f'30-context/domains/{domain_id}' if 'context' in active else f'99-system/domains/{domain_id}'
    now = datetime.now(timezone.utc).isoformat()
    brief_path = f'{context_dir}/domain-brief.md'
    state_path = f'99-system/domains/{domain_id}/akm-state.json'
    source_path = f'99-system/domains/{domain_id}/sources.md'
    state = {'version': 1, 'domain_id': domain_id, 'domain': profile['domain'],
             'goal': profile['purpose'], 'active_role': 'akm-structure',
             'discovery': {'status': 'paused', 'stop_signal': None, 'open_branches': []},
             'paths': {'brief': brief_path, 'sources': source_path, 'profile': '99-system/PROFILE.json'},
             'ontology_revision': 0, 'knowledge_revision': None, 'initial_note_ids': [], 'notes': [],
             'open_questions': profile.get('pending_questions', []), 'backlog': [],
             'last_change': '맞춤 구조만 생성; 인터뷰·모델·지식 노트는 아직 이행하지 않음',
             'next_action': '실제 발견 대화 기록과 종료 상태를 이행한 뒤 요청된 모델/위키 구축',
             'updated_at': now}
    rows = '\n'.join(f'| {name} | {LAYERS[name][0]}/ | {LAYERS[name][1]} |' for name in LAYERS if name in active)
    omitted = ', '.join(name for name in LAYERS if name not in active) or '없음'
    intake = ('새 입력은 00-inbox/에 접수하고 분류 후 정본으로 이동한다. 원문은 보존한다.'
              if profile['inbox'] else
              '별도 inbox를 만들지 않는다. 입력을 읽고 활성 레이어로 즉시 분류한다. '
              '분류하지 못한 항목은 대화의 미확인/상태에 위치를 기록하고 임의 레이어에 저장하지 않는다.')
    operations = ('실행·검증·교정은 요청된 범위에서 선택한 운영 레이어에 기록한다.'
                  if profile['operating_depth'] != 'none' else
                  '지식 조회·비교·설명 중심으로 운영한다. 자동 실행이나 운영층을 추가하지 않는다.')
    def j(value):
        return json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    brief = f'# {profile["domain"]}\n\n목적: {profile["purpose"]}\n\n이 문서는 구조 생성 시 주어진 범위만 담는다. 실제 탐색 근거를 이행한 뒤 정의·질문·사례를 보강한다.\n'
    if 'context' in active:
        description = json.dumps('Describes the selected domain and purpose before discovery evidence is transferred.')
        brief = (f'---\ndescription: {description}\nakmLayer: context\nakmType: context\n'
                 f'trustLevel: draft\ndate created: {now[:10]}\ndate modified: {now[:10]}\n---\n\n' + brief)
    files = {
        '99-system/PROFILE.json': j(profile),
        state_path: j(state),
        brief_path: brief,
        source_path: '# 출처 장부\n\n실제로 읽은 자료와 사용자 진술만 S-ID·위치·읽은 범위·근거 성격으로 등록한다. 아직 등록된 출처는 없다.\n',
        '99-system/INDEX.md': f'# AKM INDEX\n\n- [맞춤 프로필](PROFILE.json)\n- [도메인 브리프](../{brief_path})\n- [재개 상태](../{state_path})\n- [출처 장부](../{source_path})\n- [분류](ROUTER.md)\n- [스키마](SCHEMA.md)\n- [운영 루프](LOOP.md)\n',
        '99-system/ROUTER.md': f'# 맞춤 AKM 분류\n\n{intake}\n\n| 레이어 | 위치 | 용도 |\n|---|---|---|\n{rows}\n\n생략한 전용 레이어: {omitted}.\n\n생략한 층이 필요해지면 프로필 변경 후보로 남긴다. 다른 층에 의미를 숨기지 않는다. 전용 sources가 없으면 외부 원문의 위치와 provenance를 출처 장부에 남긴다. 전용 evaluation이 없어도 주장 검증 상태·한계는 지식 노트에 남긴다.\n\n원문과 합성, 공통 지식과 개인 맥락, 지식과 절차를 구분한다. 기존 파일의 삭제·이동·재분류는 별도의 변경 계획과 복원 근거를 따른다.\n',
        '99-system/SCHEMA.md': '# 맞춤 AKM 스키마\n\n정본 노트에는 description, akmLayer, akmType, trustLevel, date created, date modified를 쓴다. 시스템 문서와 JSON 제어 파일은 정본 지식 노트가 아니다.\n\n신뢰 상태: draft, raw, unverified, reviewed, canonical, deprecated. 자동 생성만으로 canonical로 승격하지 않는다.\n\nQ/S/T/C/R/A/N-ID는 작업공간 안에서 고유하게 유지한다. 관계에는 방향·조건·근거를, 위키에는 질문·답·출처·모델 연결·미확인을 남긴다.\n',
        '99-system/LOOP.md': f'# 맞춤 AKM 루프\n\n수집 → 분류 → 합성 → 맥락 적용 → 활용 → 검증 → 담당 지식/규칙 교정.\n\n{operations}\n\n전용 운영층의 유무와 관계없이 원문 보존·근거 추적·오류 정정은 유지한다. 간단한 검증은 노트 안에 기록하고 반복 운영이 필요해지면 적절한 층을 추가한다.\n',
        '99-system/LOG.md': '# AKM LOG\n\n- 맞춤 프로필로 신규 구조 생성. 지식 노트와 온톨로지 내용은 아직 생성하지 않음.\n',
    }
    return {'folders': folders, 'files': files, 'state_path': state_path}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['plan', 'init'])
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    try:
        plan = build(json.loads(args.profile.read_text(encoding='utf-8')))
        root = args.root.expanduser().absolute()
        if args.command == 'plan':
            print(json.dumps({'root': str(root), 'folders': plan['folders'],
                              'files': sorted(plan['files'])}, ensure_ascii=True, indent=2))
            return
        if root.exists() or root.is_symlink():
            raise ValueError('Existing workspace preserved; use plan and a reviewed migration instead')
        root.mkdir(parents=True, exist_ok=False)
        for folder in plan['folders']:
            (root/folder).mkdir(parents=True, exist_ok=True)
        for name, text in plan['files'].items():
            target = root/name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('x', encoding='utf-8') as handle:
                handle.write(text)
        print(json.dumps({'created': str(root), 'folders': plan['folders'],
                          'files': sorted(plan['files']), 'content_status': 'structure-only'},
                         ensure_ascii=True, indent=2))
    except (ValueError, OSError, TypeError, KeyError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
