"""Tk와 같은 교정 엔진·제외 파일을 사용하는 취소 가능한 검토 서비스."""
from copy import deepcopy
from pathlib import Path
import shutil
import tempfile
import threading
import uuid

from docfit_core.korean_proofread import scan_hwpx, apply_approved_hwpx, load_exclusions, save_exclusions
from .api_contract import ServiceError


class PublicLanguageService:
    def __init__(self, folder, manager, prepare_snapshot):
        self.exclusion_path = Path(folder) / 'proofreading_exclusions.json'
        self.manager = manager
        self.prepare_snapshot = prepare_snapshot
        self._reviews = {}
        self._lock = threading.RLock()

    def exclusions(self, action='list', payload=None):
        payload = {} if payload is None else payload
        if not isinstance(payload, dict) or action not in {'list', 'add', 'delete'}:
            raise ServiceError('INVALID_INPUT', '제외어 명령을 확인해 주세요.')
        words = payload.get('expressions', [])
        if action != 'list' and (not isinstance(words, list) or not words or
                any(not isinstance(w, str) or not w.strip() for w in words)):
            raise ServiceError('INVALID_INPUT', '비어 있지 않은 제외 표현 목록을 입력해 주세요.')
        with self._lock:
            try:
                current = load_exclusions(self.exclusion_path)
                if action != 'list':
                    current = current | set(words) if action == 'add' else current - set(words)
                    save_exclusions(self.exclusion_path, current)
            except (OSError, ValueError) as exc:
                raise ServiceError('EXCLUSIONS_FAILED', str(exc)) from exc
            return {'expressions': sorted(current)}

    def start(self, sources):
        if not isinstance(sources, list) or not sources or any(
                not isinstance(p, str) or not Path(p).is_file() or
                Path(p).suffix.lower() not in {'.hwp', '.hwpx'} for p in sources):
            raise ServiceError('INVALID_INPUT', '검토할 HWP/HWPX 파일 목록을 확인해 주세요.')
        sources = list(dict.fromkeys(sources))
        return self.manager.start('public_language', {'sources': sources},
                                  lambda report, cancelled: self._scan(sources, report, cancelled))

    def _scan(self, sources, report, cancelled):
        review_id = uuid.uuid4().hex
        temporary = tempfile.TemporaryDirectory(prefix='docfit_public_language_')
        issues, snapshots, errors = [], {}, []
        try:
            excluded = load_exclusions(self.exclusion_path)
            for index, source in enumerate(sources):
                if cancelled():
                    return None
                report('progress', dict(file=index+1, total=len(sources), stage='scan',
                                       percent=index*100/len(sources), source=source))
                try:
                    # 변환기에도 원본 대신 사본만 넘긴다. HWPX 역시 검사 시점에 고정한다.
                    copied = Path(temporary.name) / (uuid.uuid4().hex + Path(source).suffix)
                    shutil.copy2(source, copied)
                    snapshot = Path(self.prepare_snapshot(str(copied), temporary.name))
                    if cancelled():
                        return None
                    candidates = scan_hwpx(snapshot, excluded, locations=True, cancelled=cancelled)
                    snapshots[source] = snapshot
                    for item in candidates:
                        issues.append({**item, 'id': uuid.uuid4().hex, 'source_path': source})
                    report('item_done', {'source': source, 'count': len(candidates)})
                except Exception as exc:
                    errors.append({'source': source, 'message': str(exc)})
                    report('item_failed', errors[-1])
                report('progress', {'percent': (index+1)*100/len(sources)})
            if cancelled():
                return None
            if errors and not snapshots:
                raise ServiceError('JOB_FAILED', errors[0]['message'])
            with self._lock:
                self._reviews[review_id] = (temporary, snapshots, deepcopy(issues))
            temporary = None
            return {'review_id': review_id, 'issues': issues, 'errors': errors}
        finally:
            if temporary is not None:
                temporary.cleanup()

    def apply(self, review_id, ids):
        with self._lock:
            if not isinstance(review_id, str) or review_id not in self._reviews:
                raise ServiceError('REVIEW_NOT_FOUND', '다시 검사해 주세요.')
            _, snapshots, issues = self._reviews[review_id]
            known = {item['id']: item for item in issues}
            if not isinstance(ids, list) or not ids or any(
                    not isinstance(i, str) or i not in known for i in ids):
                raise ServiceError('INVALID_APPROVAL', '이 검토에서 적용할 항목 ID를 선택해 주세요.')
            selected = [deepcopy(known[i]) for i in dict.fromkeys(ids)]
        return self.manager.start('public_language_apply', {'review_id': review_id, 'ids': ids},
            lambda report, cancelled: self._apply(snapshots, selected, report, cancelled))

    def _apply(self, snapshots, selected, report, cancelled):
        grouped = {}
        for item in selected:
            grouped.setdefault(item['source_path'], set()).add(item['rule_id'])
        results, errors = [], []
        excluded = load_exclusions(self.exclusion_path)
        for index, (source, rules) in enumerate(grouped.items()):
            if cancelled():
                break
            report('progress', dict(file=index+1, total=len(grouped), stage='apply',
                                   percent=index*100/len(grouped)))
            try:
                original = Path(source)
                base = original.with_name(original.stem + '_공공언어교정.hwpx')
                target, number = base, 2
                while target.exists():
                    target = base.with_name(base.stem + f' ({number})' + base.suffix)
                    number += 1
                count = apply_approved_hwpx(snapshots[source], target, rules, excluded, cancelled=cancelled)
                results.append({'source': source, 'path': str(target), 'changes': count})
                report('item_done', results[-1])
            except Exception as exc:
                errors.append({'source': source, 'message': str(exc)})
                report('item_failed', errors[-1])
            report('progress', {'percent': (index+1)*100/len(grouped)})
        if errors and not results:
            raise ServiceError('JOB_FAILED', errors[0]['message'])
        return {'results': results, 'errors': errors}
