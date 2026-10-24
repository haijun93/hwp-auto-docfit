"""UI independent settings form, validation and transactional field updates."""
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json

from .api_contract import ServiceError
from .settings_schema import DEFAULTS
from .settings_migrations import migrate

LABELS = {
 'shell_menu':'탐색기 우클릭 메뉴',
 'prevent_word_split':'어절 줄 나눔 방지', 'ratio_shrink':'장평 줄이기', 'punctuation':'문장부호 위치 정리',
 'punctuation_threshold':'문장부호 이동 한도', 'keep_punctuation_set_together':'문장부호 묶음 유지',
 'color_mark_on':'조정한 글자 색 표시', 'color':'표시 색', 'autoclose':'처리 후 한글 창 닫기',
 'stdformat':'보고서 표준서식 적용', 'verify':'상세 진단', 'integrity_report_file':'무결성 보고서 저장',
 'final_review_file':'최종검수 보고서 저장', 'two_pass_processing':'두 번 처리', 'retry_body':'본문 재시도 횟수',
 'table_linespacing_min':'표 칸 최소 줄 간격 (%)', 'table_spacing_min':'표 칸 자간 하한 (%)',
 'retry_table':'표 재시도 횟수', 'linespacing_min':'최소 줄 간격 (%)', 'linespacing_max':'최대 줄 간격 (%)',
 'label_symbols':'문두 라벨 굵게', 'paren_shrink':'괄호 자간 정리', 'paren_label_bold':'괄호 라벨 굵게',
 'std_margin':'편집 여백', 'std_ratio':'기본 장평', 'std_linespacing':'기본 줄 간격', 'std_title':'제목 서식',
 'std_title_auto':'제목 자동 판별', 'std_attachment_auto':'붙임 자동 판별', 'std_midtitle_auto':'중제목 자동 판별',
 'std_midtitle_bold':'중제목 굵게', 'abbreviation_defaults':'기본 준말 사용', 'std_title_bold':'제목 굵게',
 'std_dateinfo':'날짜·담당자 서식', 'std_dateinfo_bold':'날짜·담당자 굵게', 'std_symbols':'항목기호 서식',
 'std_hanging_indent':'내어쓰기', 'std_supplement_indent':'부연설명 들여쓰기', 'std_symbol_box_bold':'네모 항목 굵게',
 'std_symbol_o_bold':'원 항목 굵게', 'std_symbol_dash_bold':'바 항목 굵게', 'std_symbol_note_bold':'참고 항목 굵게',
 'std_marker_bold_consistency':'같은 항목 라벨 굵기 통일', 'std_parspace':'문단 위 간격',
 'std_remove_blank_lines':'항목 사이 빈 줄 삭제', 'std_parspace_chapter':'장 제목 위 간격 (pt)',
 'std_parspace_midtitle':'중제목 위 간격 (pt)', 'std_parspace_box':'네모 항목 위 간격 (pt)',
 'std_parspace_circle':'원 항목 위 간격 (pt)', 'std_parspace_dash':'바 항목 위 간격 (pt)',
 'std_parspace_note':'참고 항목 위 간격 (pt)', 'std_parspace_return_percent':'상위 항목 복귀 간격 (%)',
 'std_title_subtitle_pt':'부제 글자 크기 (pt)', 'title_owner_text':'제목 표 담당자 표시',
 'std_table_header':'표 머리글 서식', 'symbol_fonts':'항목기호 글꼴', 'table_fonts':'표 글꼴',
 'hwp_font_folder':'한글 글꼴 폴더', 'paste_add_folder':'붙여넣기 문서 저장 폴더', 'always_on_top':'항상 위에 표시',
 'check_updates_on_start':'시작할 때 업데이트 확인',
 'offline_mode':'폐쇄망 모드 (인터넷 연결 안 함)', 'table_spacing':'표 안 자간 정리', 'log_file':'작업 로그 파일 저장',
 'developer_mode':'개발자 모드', 'all_include_spacing':'한 번에 적용: 자간 포함',
 'all_exclude_tables':'한 번에 적용: 표 제외', 'all_exclude_pagefit':'한 번에 적용: 페이지 맞춤 제외',
 'all_linespacing':'한 번에 적용: 줄 간격 적용',
 'unify_exclude_tables':'서식 통일: 표 제외', 'unify_exclude_spacing':'서식 통일: 자간 제외',
 'unify_exclude_pagefit':'서식 통일: 페이지 맞춤 제외', 'unify_keep_layout':'서식 통일: 원본 쪽 구성 유지',
 'unify_full_format':'서식 통일: 전체 서식 맞춤', 'unify_result_window':'서식 통일 결과 창 표시',
 'spacing_reset_existing':'기존 자간 초기화',
 'spacing_enabled':'자간 정리: 자간 기능 사용',
 'spacing_page_fit':'자간 정리: 페이지 맞춤',
}
EXCLUDED = {'abbreviations', 'abbreviation_source', 'active_format_profile'} | {k for k in DEFAULTS if k.endswith('_rev')}


def leaves(values, prefix=''):
    for key, value in values.items():
        path = f'{prefix}.{key}' if prefix else key
        if isinstance(value, dict):
            yield from leaves(value, path)
        else:
            yield path, value


def revision(settings):
    return sha256(json.dumps(settings, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def fields():
    result = []
    for key, default in leaves({k:v for k,v in DEFAULTS.items() if k not in EXCLUDED}):
        root, *parts = key.split('.')
        label = LABELS[root]
        for part in parts:
            label += ' · ' + {'header':'머리글', 'body':'본문', 'font':'글꼴', 'size':'크기 (pt)'}.get(part, part)
        numeric = (root.startswith('std_parspace_') or root in {'punctuation_threshold','retry_body','retry_table',
                   'table_linespacing_min','table_spacing_min','linespacing_min','linespacing_max','std_title_subtitle_pt'} or key.endswith('.size'))
        result.append({'key':key, 'label':label, 'type':'boolean' if isinstance(default,bool) or default is None
                       else 'number' if numeric else 'text', 'default':True if default is None else default,
                       'group':'글꼴' if root in {'symbol_fonts','table_fonts'} else
                       '개발자 도구' if root in {'developer_mode'} else
                       '네트워크' if root in {'offline_mode','check_updates_on_start'} else
                       '표준서식' if root.startswith('std_') or root in {'label_symbols','title_owner_text'} else '작업·프로그램'})
    return result


class ConfigurationService:
    def __init__(self, store):
        self.store = store

    def snapshot(self, *, running=False):
        saved = self.store.read()
        merged = deepcopy(DEFAULTS)
        for key, value in migrate(saved).items():
            if key in merged and isinstance(merged[key],dict) and isinstance(value,dict):
                for part, spec in value.items():
                    if isinstance(merged[key].get(part),dict) and isinstance(spec,dict):
                        merged[key][part].update(spec)
                    else:
                        merged[key][part] = spec
            else:
                merged[key] = value
        if merged.get('spacing_reset_existing') is None:
            stages = saved.get('stage_choices',{})
            spacing = stages.get('spacing',{}) if isinstance(stages,dict) else {}
            merged['spacing_reset_existing'] = bool(spacing.get('reset_spacing',True)) if isinstance(spacing,dict) else True
        known = {f['key'] for f in fields()}
        return {'fields':fields(), 'values':{k:v for k,v in leaves(merged) if k in known},
                'revision':revision(saved), 'running':bool(running)}

    def save(self, patch, expected_revision, *, running=False):
        if running:
            raise ServiceError('JOB_RUNNING','작업 중에는 설정을 바꿀 수 없습니다.')
        if not isinstance(patch,dict) or not isinstance(expected_revision,str):
            raise ServiceError('INVALID_INPUT','설정 입력 형식을 확인해 주세요.')
        schema = {f['key']:f for f in fields()}
        clean = {}
        for key,value in patch.items():
            field = schema.get(key)
            if field is None:
                raise ServiceError('INVALID_INPUT','지원하지 않는 설정 항목입니다.')
            if field['type']=='boolean':
                if not isinstance(value,bool):
                    raise ServiceError('INVALID_INPUT',field['label']+' 값을 확인해 주세요.')
            elif not isinstance(value,str) or len(value)>4096 or '\x00' in value:
                raise ServiceError('INVALID_INPUT',field['label']+' 값을 확인해 주세요.')
            elif field['type']=='number':
                try:
                    number = Decimal(value)
                    if not number.is_finite() or number<(-25 if key=='table_spacing_min' else 0) or number>1000:
                        raise ValueError()
                    if (key.endswith('.size') or key=='std_title_subtitle_pt') and number<=0:
                        raise ValueError()
                    if key in {'table_linespacing_min','table_spacing_min','retry_body','retry_table','punctuation_threshold','linespacing_min','linespacing_max'} and number!=number.to_integral_value():
                        raise ValueError()
                except (InvalidOperation,ValueError):
                    raise ServiceError('INVALID_INPUT',field['label']+'에 유효한 숫자를 입력해 주세요.')
                value = value.strip()
            clean[key] = value
        def update(settings):
            if revision(settings)!=expected_revision:
            if key in {'table_linespacing_min', 'table_spacing_min'}:
                from docfit_core.table_limits import TableLimits
                try:
                    TableLimits.from_settings({key: value})
                except ValueError as exc:
                    raise ServiceError('INVALID_INPUT', str(exc))
                raise ServiceError('SETTINGS_CHANGED','다른 화면에서 설정이 바뀌었습니다. 다시 불러온 뒤 적용해 주세요.')
            settings.update(migrate(settings))
            for key,value in clean.items():
                parts = key.split('.')
                target = settings
                for part in parts[:-1]:
                    current = target.get(part)
                    if current is not None and not isinstance(current,dict):
                        raise ServiceError('INVALID_SETTINGS','저장된 글꼴 설정을 확인해 주세요.')
                    target = target.setdefault(part,{})
                target[parts[-1]] = value
            try:
                minimum = Decimal(str(settings.get('linespacing_min',DEFAULTS['linespacing_min'])))
                maximum = Decimal(str(settings.get('linespacing_max',DEFAULTS['linespacing_max'])))
                if not minimum.is_finite() or not maximum.is_finite():
                    raise ValueError()
            except (InvalidOperation, ValueError):
                raise ServiceError('INVALID_SETTINGS','저장된 줄 간격 값을 확인해 주세요.')
            if minimum>maximum:
                raise ServiceError('INVALID_INPUT','최소 줄 간격은 최대 줄 간격보다 클 수 없습니다.')
        self.store.update(update)
        return self.snapshot(running=running)
