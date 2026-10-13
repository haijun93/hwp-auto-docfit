"""Existing settings migrations, shared by Tk and independent configuration APIs."""
from copy import deepcopy
from .settings_schema import DEFAULTS


def migrate(settings):
    result=deepcopy(settings)
    def old(key):
        try:return int(result.get(key,1) or 1)<2
        except (TypeError,ValueError):return True
    if old('label_symbols_rev'):
        symbols=result.get('label_symbols',DEFAULTS['label_symbols'])
        if isinstance(symbols,dict):result['label_symbols']={**symbols,'*':False,'**':False}
    if old('report_files_rev'):
        for key in ('log_file','integrity_report_file','final_review_file'):result[key]=False
    if old('std_parspace_rev'):
        prior={'std_parspace_chapter':'20','std_parspace_midtitle':'15','std_parspace_box':'15',
               'std_parspace_circle':'10','std_parspace_note':'3'}
        if all(str(result.get(k,v)).strip()==v for k,v in prior.items()):
            for key in (*prior,'std_parspace_dash'):result[key]=DEFAULTS[key]
    if old('std_supplement_rev'):result['std_supplement_indent']=True
    for key in ('label_symbols_rev','report_files_rev','std_parspace_rev','std_supplement_rev'):result[key]=2
    fonts=result.get('symbol_fonts',{})
    if isinstance(fonts,dict):
        for spec in fonts.values():
            if isinstance(spec,dict) and spec.get('font')=='한컴돋음':spec['font']='한컴돋움'
    return result
