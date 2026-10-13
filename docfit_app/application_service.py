"""Tk-free native prototype application commands and state."""
from dataclasses import asdict
from pathlib import Path
import threading

from docfit_app.abbreviation_service import AbbreviationService
from docfit_app.api_contract import ServiceError, response
from docfit_app.configuration_service import ConfigurationService
from docfit_app.settings_service import SettingsService
from docfit_app.settings_schema import DEFAULTS
from docfit_app.settings_migrations import migrate
from docfit_core.hwpx import validate_and_inspect_hwpx
from docfit_app.app_state import STAGE_ORDER, AppState
from docfit_core.stage_selection import default_choice, stages_for_mode


class ApplicationService:
    def __init__(self, settings_path):
        self.store = SettingsService(settings_path)
        self.configuration = ConfigurationService(self.store)
        self.abbreviations = AbbreviationService(self.store)
        self.data = AppState()
        self.lock = threading.RLock()

    def state(self):
        settings = {**DEFAULTS, **migrate(self.store.read())}
        return {'files':[{'path':p,'name':Path(p).name,'folder':str(Path(p).parent)} for p in self.data.files],
                'count':len(self.data.files),'native_backend':True,'mode':self.data.mode,'running':False,'engine_ready':False,
                'status':'문서 분석·설정 시제품', 'version':'1.74 Native Prototype 1',
                'include_spacing':settings['all_include_spacing'], 'reset_spacing':True,
                'table_spacing':settings['table_spacing'], 'exclude_tables':settings['all_exclude_tables'],
                'card_options':{},'range':self.data.range,'results':[], 'options':settings,
                'profiles':[], 'profile':'','default_saved':False,'format_task':None,
                'progress':{'steps':list(STAGE_ORDER),'active':None,'visited':[],'outcome':None,'detail':''},
                'stages':[{'key':k,'label':label,'enabled':self.data.stages.get((self.data.mode,k),default_choice(k,self.data.mode)),
                           'default':default_choice(k,self.data.mode)} for k,label in stages_for_mode(self.data.mode)],
                'can_start':False,'capabilities':['documents.inspect','settings','abbreviations']}

    def dispatch(self, method, args):
        counts = {'handshake':0,'get_state':0,'get_settings':0,'save_settings':2,
                  'get_abbreviations':0,'save_abbreviation':4,'delete_abbreviation':1,
                  'set_abbreviation_defaults':1,'add_paths':1,'remove_file':1,
                  'clear_files':0,'set_mode':1,'inspect_document':1,'get_log':0,'clear_log':0,'shutdown':0}
        if method not in counts:
            raise ServiceError('NOT_AVAILABLE','이 네이티브 시제품에서는 해당 기능을 아직 사용할 수 없습니다.')
        if len(args)!=counts[method]:
            raise ServiceError('INVALID_INPUT','입력 항목 수를 확인해 주세요.')
        if self.data.closing and method != 'shutdown':
            raise ServiceError('BACKEND_CLOSING','백엔드가 종료 중입니다.')
        if method=='handshake':
            return {'protocol_version':1,'backend_version':'1.74 Native Prototype 1',
                    'capabilities':['documents.inspect','settings','abbreviations'],'engine_ready':False}
        if method=='get_state': return self.state()
        if method=='get_settings': return response(self.configuration.snapshot)
        if method=='save_settings': return response(lambda:self.configuration.save(*args))
        if method=='get_abbreviations': return response(self.abbreviations.snapshot)
        if method=='save_abbreviation': return response(lambda:self.abbreviations.save(*args))
        if method=='delete_abbreviation': return response(lambda:self.abbreviations.delete(*args))
        if method=='set_abbreviation_defaults': return response(lambda:self.abbreviations.set_defaults(*args))
        if method=='add_paths':
            if len(args)!=1 or not isinstance(args[0],list) or len(args[0])>1000:
                raise ServiceError('INVALID_INPUT','추가할 문서 목록을 확인해 주세요.')
            paths=[]
            for raw in args[0]:
                if not isinstance(raw,str) or '\x00' in raw:
                    raise ServiceError('INVALID_INPUT','문서 경로를 확인해 주세요.')
                path=Path(raw).resolve()
                if not path.is_file() or path.suffix.lower() not in {'.hwp','.hwpx','.txt','.md','.pdf','.doc','.docx'}:
                    raise ServiceError('INVALID_PATH','존재하는 지원 문서를 선택해 주세요.')
                paths.append(str(path))
            if len(set(self.data.files+paths))>1000:
                raise ServiceError('FILE_LIMIT','문서는 최대 1,000개까지 추가할 수 있습니다.')
            self.data.files=list(dict.fromkeys(self.data.files+paths)); return self.state()
        if method=='remove_file':
            index=args[0]
            if not isinstance(index,int) or isinstance(index,bool) or not 0<=index<len(self.data.files):
                raise ServiceError('INVALID_INPUT','삭제할 문서를 확인해 주세요.')
            self.data.files.pop(index);return self.state()
        if method=='clear_files': self.data.files=[];return self.state()
        if method=='set_mode':
            if args[0] not in {'all','format','spacing','unify'}:
                raise ServiceError('INVALID_INPUT','작업 방식을 확인해 주세요.')
            self.data.mode=args[0];return self.state()
        if method=='inspect_document':
            path=Path(args[0]).resolve()
            _,inspection=validate_and_inspect_hwpx(path)
            return asdict(inspection)
        if method=='get_log' or method=='clear_log': return ''
        if method=='shutdown': self.data.closing=True;return {'closed':True}
        raise ServiceError('NOT_AVAILABLE','이 네이티브 시제품에서는 해당 기능을 아직 사용할 수 없습니다.')

