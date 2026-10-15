"""Pure settings migration plus the shared atomic JSON storage facade.

Migration takes defaults explicitly and never imports a GUI or touches files.
Storage delegates to the existing lock-protected service to preserve concurrent
writers and avoid a second implementation of atomic replacement.
"""
from copy import deepcopy


def migrate_settings(settings, defaults):
    result=deepcopy(settings)
    def old(key):
        try:return int(result.get(key,1) or 1)<2
        except (TypeError,ValueError):return True
    if old('label_symbols_rev'):
        symbols=result.get('label_symbols',defaults['label_symbols'])
        if isinstance(symbols,dict):result['label_symbols']={**symbols,'*':False,'**':False}
    if old('report_files_rev'):
        for key in ('log_file','integrity_report_file','final_review_file'):result[key]=False
    if old('std_parspace_rev'):
        prior={'std_parspace_chapter':'20','std_parspace_midtitle':'15','std_parspace_box':'15',
               'std_parspace_circle':'10','std_parspace_note':'3'}
        if all(str(result.get(k,v)).strip()==v for k,v in prior.items()):
            for key in (*prior,'std_parspace_dash'):result[key]=defaults[key]
    if old('std_supplement_rev'):result['std_supplement_indent']=True
    # 줄 간격 최솟값 기본 160% -> 140%(사용자 지시, 2026-10-15). 예전 기본값 그대로인 설정만 옮긴다.
    if old('linespacing_min_rev') and str(result.get('linespacing_min','160')).strip()=='160':
        result['linespacing_min']=defaults['linespacing_min']
    for key in ('label_symbols_rev','report_files_rev','std_parspace_rev','std_supplement_rev',
                'linespacing_min_rev'):result[key]=2
    fonts=result.get('symbol_fonts',{})
    if isinstance(fonts,dict):
        for spec in fonts.values():
            if isinstance(spec,dict) and spec.get('font')=='한컴돋음':spec['font']='한컴돋움'
    return result


class ConfigStore:
    def __init__(self, path, defaults):
        from docfit_app.settings_service import SettingsService
        self._storage = SettingsService(path)
        self.defaults = deepcopy(defaults)

    def load(self):
        return {**deepcopy(self.defaults),
                **migrate_settings(self._storage.read(), self.defaults)}

    def save(self, settings):
        saved = deepcopy(settings)
        return self._storage.update(lambda current: current.update(saved))
