"""Tk-free native prototype application commands and state."""
from dataclasses import asdict
from pathlib import Path
import threading

from docfit_app.abbreviation_service import AbbreviationService
from docfit_app.api_contract import ServiceError, response
from docfit_app.configuration_service import ConfigurationService
from docfit_app.settings_service import SettingsService
from docfit_app.settings_schema import DEFAULTS
from docfit_app.diagram_service import DiagramService
from docfit_app.flow_service import FlowService
from docfit_app.settings_migrations import migrate
from docfit_core.hwpx import validate_and_inspect_hwpx
from docfit_app.app_state import STAGE_ORDER, AppState
from docfit_core.stage_selection import default_choice, stages_for_mode


class ApplicationService:
    def __init__(self, settings_path):
        self.store = SettingsService(settings_path)
        self.configuration = ConfigurationService(self.store)
        self.abbreviations = AbbreviationService(self.store)
        self.diagrams = DiagramService(Path(settings_path).parent, self.store)
        self.flows = FlowService(Path(settings_path).parent, self.store)
        self.data = AppState()
        self.lock = threading.RLock()

    def state(self):
        settings = {**DEFAULTS, **migrate(self.store.read())}
        saved_stages=settings.get('stage_choices',{})
        if not isinstance(saved_stages,dict):saved_stages={}
        selected=saved_stages.get(self.data.mode,{})
        if not isinstance(selected,dict):selected={}
        return {'files':[{'path':p,'name':Path(p).name,'folder':str(Path(p).parent)} for p in self.data.files],
                'count':len(self.data.files),'native_backend':True,'mode':self.data.mode,'running':False,'engine_ready':False,
                'status':'문서 분석·설정 시제품', 'version':'1.74 Native Prototype 1',
                'include_spacing':settings['all_include_spacing'], 'reset_spacing':self.data.stages.get(('spacing','reset_spacing'),settings.get('spacing_reset_existing') if settings.get('spacing_reset_existing') is not None else True),
                'table_spacing':settings['table_spacing'], 'exclude_tables':settings['all_exclude_tables'],
                'card_options':{**{key:bool(settings.get(key)) for key in ('spacing_enabled','spacing_page_fit','unify_exclude_tables','unify_exclude_spacing','unify_exclude_pagefit','unify_keep_layout','unify_full_format','all_include_spacing','all_exclude_tables','all_exclude_pagefit')},'spacing_exclude_tables':not settings['table_spacing'],'spacing_reset_existing':bool(settings['spacing_reset_existing']) if settings.get('spacing_reset_existing') is not None else True},'range':self.data.range,'results':[], 'options':settings,
                'profiles':[], 'profile':'','default_saved':self.data.mode in saved_stages,'format_task':None,
                'progress':{'steps':list(STAGE_ORDER),'active':None,'visited':[],'outcome':None,'detail':''},
                'stages':[{'key':k,'label':label,'enabled':self.data.stages.get((self.data.mode,k),selected.get(k,default_choice(k,self.data.mode))),
                           'default':default_choice(k,self.data.mode)} for k,label in stages_for_mode(self.data.mode)],
                'can_start':False,'capabilities':['documents.inspect','settings','abbreviations','flows'] +
                (['diagrams'] if self.diagrams.enabled() else [])}

    def dispatch(self, method, args):
        counts = {'handshake':0,'get_state':0,'get_settings':0,'save_settings':2,
                  'get_abbreviations':0,'save_abbreviation':4,'delete_abbreviation':1,
                  'set_abbreviation_defaults':1,'add_paths':1,'remove_file':1,
                  'clear_files':0,'set_mode':1,'inspect_document':1,'get_log':0,'clear_log':0,'shutdown':0}
        counts.update({'table_template':2,'document_tool':2,'get_pending_dialog':0,'stage_config':2,'set_stage':2,'set_stage_default':1})
        counts.update({'set_option':2,'set_include_spacing':1,'set_reset_spacing':1,'set_table_spacing':1,'set_exclude_tables':1,'set_range':3,'set_card_option':2})
        counts.update({'flow_editor':2,'idioms':2,'hangul_fonts':2})
        counts.update({'diagram_list':0,'diagram_load':1,'diagram_save':3,'diagram_delete':1})
        if method not in counts:
            raise ServiceError('NOT_AVAILABLE','이 네이티브 시제품에서는 해당 기능을 아직 사용할 수 없습니다.')
        if not (method == 'diagram_save' and len(args) in (3, 4)) and len(args)!=counts[method]:
            raise ServiceError('INVALID_INPUT','입력 항목 수를 확인해 주세요.')
        if self.data.closing and method != 'shutdown':
            raise ServiceError('BACKEND_CLOSING','백엔드가 종료 중입니다.')
        if method=='handshake':
            return {'protocol_version':1,'backend_version':'1.74 Native Prototype 1',
                    'capabilities':['documents.inspect','settings','abbreviations','flows'] +
                    (['diagrams'] if self.diagrams.enabled() else []),'engine_ready':False}
        if method=='set_card_option':
            name,value=args
            allowed={'spacing_enabled','spacing_page_fit','spacing_reset_existing','spacing_exclude_tables','unify_exclude_tables','unify_exclude_spacing','unify_exclude_pagefit',
                     'unify_keep_layout','unify_full_format','all_include_spacing','all_exclude_tables','all_exclude_pagefit'}
            if name not in allowed or not isinstance(value,bool):raise ServiceError('INVALID_OPTION','카드 옵션을 확인해 주세요.')
            if name=='spacing_exclude_tables':key,value='table_spacing',not value
            else:key=name
            self.store.update(lambda current:current.update({key:value}))
            if name=='spacing_reset_existing':self.data.stages[('spacing','reset_spacing')]=value
            if name=='all_include_spacing' and self.data.mode in ('all','format'):
                self.data.mode='all' if value else 'format'
            return self.state()
        if method=='set_range':
            enabled,start,end=args
            if not isinstance(enabled,bool) or not isinstance(start,str) or not isinstance(end,str):
                raise ServiceError('INVALID_RANGE','쪽 범위를 확인해 주세요.')
            if enabled and (not start.isdigit() or not 1<=int(start)<=99999 or (end and (not end.isdigit() or not int(start)<=int(end)<=99999))):
                raise ServiceError('INVALID_RANGE','시작·끝 쪽 번호를 확인해 주세요.')
            self.data.range={'enabled':enabled,'start':start,'end':end}
            return self.state()
        if method in ('set_option','set_include_spacing','set_reset_spacing','set_table_spacing','set_exclude_tables'):
            mapping={'set_include_spacing':'all_include_spacing','set_reset_spacing':'spacing_reset_existing',
                     'set_table_spacing':'table_spacing','set_exclude_tables':'all_exclude_tables'}
            if method=='set_option':
                key,value=args
                key={'check_updates':'check_updates_on_start'}.get(key,key)
                if key not in ('autoclose','unify_result_window','verify','integrity_report_file','final_review_file','log_file','check_updates_on_start','developer_mode','always_on_top'):
                    raise ServiceError('INVALID_OPTION','설정 항목을 확인해 주세요.')
            else:key,value=mapping[method],args[0]
            if not isinstance(value,bool):raise ServiceError('INVALID_OPTION','설정 값을 확인해 주세요.')
            self.store.update(lambda current:current.update({key:value}))
            if method=='set_reset_spacing':self.data.stages[('spacing','reset_spacing')]=value
            if method=='set_include_spacing' and self.data.mode in ('all','format'):
                self.data.mode='all' if value else 'format'
            return self.state()
        if method in ('stage_config','set_stage','set_stage_default'):
            mode=self.data.mode
            if method=='set_stage':
                key,on=args
                if key not in dict(stages_for_mode(mode)) or not isinstance(on,bool):
                    raise ServiceError('INVALID_STAGE','단계 선택을 확인해 주세요.')
                self.data.stages[(mode,key)]=on
            elif method=='stage_config':
                action,payload=args
                if action not in ('all','defaults') or not isinstance(payload,dict):
                    raise ServiceError('INVALID_STAGE','단계 선택을 확인해 주세요.')
                if action=='all' and not isinstance(payload.get('enabled'),bool):
                    raise ServiceError('INVALID_STAGE','단계 선택을 확인해 주세요.')
                for key,_ in stages_for_mode(mode):
                    self.data.stages[(mode,key)]=payload['enabled'] if action=='all' else default_choice(key,mode)
            else:
                if not isinstance(args[0],bool):raise ServiceError('INVALID_STAGE','기본값 저장 여부를 확인해 주세요.')
                prior=self.store.read().get('stage_choices',{})
                prior=prior.get(mode,{}) if isinstance(prior,dict) else {}
                selection={key:self.data.stages.get((mode,key),prior.get(key,default_choice(key,mode))) for key,_ in stages_for_mode(mode)}
                def save(current):
                    choices=current.get('stage_choices',{})
                    if not isinstance(choices,dict):choices={}
                    if args[0]:choices[mode]=selection
                    else:choices.pop(mode,None)
                    current['stage_choices']=choices
                self.store.update(save)
            if method!='set_stage_default':
                persisted=self.store.read().get('stage_choices',{})
                if isinstance(persisted,dict) and isinstance(persisted.get(mode),dict):
                    selection={key:self.data.stages.get((mode,key),persisted[mode].get(key,default_choice(key,mode))) for key,_ in stages_for_mode(mode)}
                    def refresh_saved(current):
                        current.setdefault('stage_choices',{})[mode]=selection
                    self.store.update(refresh_saved)
            return self.state()
        if method=='document_tool':
            from docfit_app.document_tools_service import DocumentToolsService
            def execute():
                result=DocumentToolsService(self.store._path.parent).command(*args)
                if args[0]=='add_text':
                    self.data.files.append(result['path'])
                return result
            return response(execute)
        if method=='hangul_fonts':
            from docfit_core import hangul_fonts
            if args[0]=='list':return {'fonts':[{'name':e['name'],'source':e['source']} for e in hangul_fonts.catalog()],**hangul_fonts.summary()}
            raise ServiceError('NOT_AVAILABLE','이 네이티브 시제품에서는 글꼴 파일을 내주지 않습니다.')
        if method=='idioms':
            from docfit_app.idiom_service import IdiomService
            app_copy=Path(__file__).resolve().parents[1]/'resources'/'HWP.IDO'
            return response(lambda:IdiomService(app_copy=app_copy).command(*args))
        if method=='table_template':
            from docfit_app.table_template_service import TableTemplateService
            return response(lambda:TableTemplateService(self.abbreviations).command(*args))
        if method=='get_pending_dialog': return None
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
        if method=='flow_editor':
            action,payload=args
            if not isinstance(payload,dict):raise ServiceError('INVALID_INPUT','입력을 확인해 주세요.')
            if action=='copy_result':
                from docfit_app.clipboard_service import copy_result
                return copy_result(payload)
            if action=='export_png':return self.flows.export_png(payload.get('base64'))
            if action=='export_hwpx':
                base=Path(__file__).resolve().parents[1]/'resources'/'서식예시'/'기본 서식.hwpx'
                return self.flows.export_hwpx(payload.get('spec'),base)
            if action=='list':return self.flows.list()
            if action=='load':return self.flows.load(payload.get('id'))
            if action=='save':return self.flows.save(payload.get('id'),payload.get('name'),payload.get('snapshot'),payload.get('revision'))
            if action=='delete':return self.flows.delete(payload.get('id'))
            raise ServiceError('INVALID_ACTION','흐름도 작업을 확인해 주세요.')
        if method=='diagram_list': return self.diagrams.list()
        if method=='diagram_load': return self.diagrams.load(*args)
        if method=='diagram_save': return self.diagrams.save(*args)
        if method=='diagram_delete': return self.diagrams.delete(*args)
        if method=='shutdown': self.data.closing=True;return {'closed':True}
        raise ServiceError('NOT_AVAILABLE','이 네이티브 시제품에서는 해당 기능을 아직 사용할 수 없습니다.')

