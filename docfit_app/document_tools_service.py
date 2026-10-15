"""UI-independent writing tools and revision-protected private outline drafts."""
from hashlib import sha256
import os
from pathlib import Path
import tempfile
import threading
import json
from copy import deepcopy

_JOBS = {}
_JOB_LOCK = threading.RLock()
from docfit_core import outline_ops, pasted_text, labeled_text, writing_aids, ai_prompts
from docfit_infra.storage.process_lock import ProcessLock
from .api_contract import ServiceError


class DocumentToolsService:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.draft = self.folder / 'outliner_draft.md'

    @staticmethod
    def _text(payload):
        value=payload.get('text','')
        if not isinstance(value,str) or len(value.encode('utf-8'))>1_000_000:
            raise ServiceError('INVALID_TEXT','입력은 UTF-8 1MB 이하의 텍스트여야 합니다.')
        return value

    def outline(self, action, payload):
        if action=='load':
            try:
                with self.draft.open('rb') as stream: raw=stream.read(1_000_001)
            except FileNotFoundError: raw=b''
            if len(raw)>1_000_000: raise ServiceError('DRAFT_LIMIT','초안 크기가 제한을 넘습니다.')
            return {'text':raw.decode('utf-8'),'revision':sha256(raw).hexdigest()}
        text=self._text(payload); lines=text.split('\n')
        if action=='save':
            self.folder.mkdir(parents=True,exist_ok=True)
            with ProcessLock(self.draft.with_suffix('.lock')):
                current=self.outline('load',{})
                if payload.get('revision')!=current['revision']:
                    raise ServiceError('DRAFT_CONFLICT','다른 창에서 초안이 바뀌었습니다. 다시 불러와 주세요.')
                temporary=None
                try:
                    with tempfile.NamedTemporaryFile(dir=self.folder,mode='wb',delete=False) as stream:
                        temporary=Path(stream.name);stream.write(text.encode('utf-8'));stream.flush();os.fsync(stream.fileno())
                    os.replace(temporary,self.draft)
                finally:
                    if temporary:temporary.unlink(missing_ok=True)
                return {'text':text,'revision':sha256(text.encode('utf-8')).hexdigest()}
        if action=='export': return {'text':outline_ops.export_markdown(lines)}
        if action=='filter':return {'visible':sorted(outline_ops.filter_visible(lines,str(payload.get('query',''))))}
        index=payload.get('index',0)
        if not isinstance(index,int) or isinstance(index,bool) or not 0<=index<len(lines):
            raise ServiceError('INVALID_INDEX','항목을 선택해 주세요.')
        index=outline_ops.item_start(lines,index)
        if action=='move':
            moved=outline_ops.move_block(lines,index,bool(payload.get('up')))
            if moved:lines,index=moved
        elif action=='toggle':lines[index]=outline_ops.toggle_done(lines[index])
        elif action=='note':
            note=str(payload.get('note','')).replace('\n',' ')
            lines.insert(index+1,outline_ops.note_prefix(lines[index])+note)
        elif action in ('indent','outdent'):
            end=outline_ops.subtree_end(lines,index)
            old=outline_ops.depth(lines,index)
            delta=1 if action=='indent' else -1
            if old+delta<0 or old+delta>12 or (action=='indent' and index==0):
                return {'text':text,'index':index}
            if delta>0 and old+delta>outline_ops.depth(lines,index-1)+1:
                return {'text':text,'index':index}
            for pos in range(index,end):
                kind,depth,body=outline_ops.parse(lines[pos])
                if kind=='item':
                    depth=max(0,depth+delta)
                    lines[pos]=('# ' if depth==0 else '  '*(depth-1)+'- ')+body
                elif kind=='note':
                    lines[pos]=outline_ops.note_prefix(lines[outline_ops.item_start(lines,pos)])+body
        else:raise ServiceError('INVALID_ACTION','지원하지 않는 아웃라이너 명령입니다.')
        return {'text':'\n'.join(lines),'index':index}

    def proofread(self, path, payload, *, apply=False):
        from docfit_core.hwpx import HwpxLimits, validate_hwpx
        from docfit_core.korean_proofread import scan_hwpx, apply_approved_hwpx, RULE_BY_ID
        import uuid
        self.folder.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='review-', dir=self.folder) as folder:
            snapshot=Path(folder)/'source.hwpx'
            digest=sha256(); size=0
            with path.open('rb') as source, snapshot.open('xb') as target:
                while True:
                    chunk=source.read(1024*1024)
                    if not chunk:break
                    size+=len(chunk)
                    if size>HwpxLimits().max_total_size:
                        raise ServiceError('FILE_LIMIT','문서 크기가 제한을 넘습니다.')
                    digest.update(chunk);target.write(chunk)
            validate_hwpx(snapshot)
            revision=digest.hexdigest()
            if not apply:
                return {'issues':scan_hwpx(snapshot),'source_sha256':revision,'source':str(path)}
            if payload.get('source_sha256')!=revision:
                raise ServiceError('DOCUMENT_CHANGED','검토 후 문서가 바뀌었습니다. 다시 검사해 주세요.')
            approved=payload.get('approved',[])
            if not isinstance(approved,list) or not approved or len(approved)>1000 or any(not isinstance(key,str) or key not in RULE_BY_ID for key in approved):
                raise ServiceError('INVALID_APPROVAL','적용할 교정 항목을 직접 선택해 주세요.')
            output=self.folder/('교정사본-'+uuid.uuid4().hex+'.hwpx')
            count=apply_approved_hwpx(snapshot,output,approved)
            return {'path':str(output),'changes':count,'source_sha256':revision}

    def advanced(self, payload):
        from docfit_core import kordoc_bridge as engine
        from docfit_core.hwpx import HwpxLimits
        import uuid
        import subprocess
        action=payload.get('action','markdown')
        actions={'markdown':engine.export_advanced_markdown,'rag':engine.export_rag_chunks,
                 'ir':engine.export_common_ir,'tables':engine.analyze_tables,'form':engine.analyze_form,
                 'lint':engine.lint_document,'preview':engine.render_preview}
        if action not in {*actions,'compare','fill','patch','generate'}:
            raise ServiceError('INVALID_ACTION','고급 도구를 선택해 주세요.')
        def copy_input(raw,stem):
            if not isinstance(raw,str) or not raw or '\x00' in raw:
                raise ServiceError('INVALID_PATH','입력 문서를 선택해 주세요.')
            source=Path(raw)
            if not source.is_file():raise ServiceError('INVALID_PATH','입력 문서를 찾지 못했습니다.')
            if source.suffix.lower() not in engine.SUPPORTED_INPUT_EXTENSIONS|{'.md','.txt'}:
                raise ServiceError('INVALID_PATH','지원하는 문서 형식을 선택해 주세요.')
            target=folder/(stem+source.suffix.lower())
            size=0
            with source.open('rb') as original,target.open('xb') as output:
                while True:
                    chunk=original.read(1024*1024)
                    if not chunk:break
                    size+=len(chunk)
                    if size>HwpxLimits().max_total_size:raise ServiceError('FILE_LIMIT','문서 크기가 제한을 넘습니다.')
                    output.write(chunk)
            return target
        try:
            contract=engine.check_engine_contract()
            folder=self.folder/'고급도구'/uuid.uuid4().hex
            folder.mkdir(parents=True,exist_ok=False)
            source=copy_input(payload.get('path'),'source')
            if action in actions:
                result=actions[action](source,payload.get('pages') or None) if action=='markdown' else actions[action](source)
            elif action=='compare':
                result=engine.compare_documents(source,copy_input(payload.get('other'),'other'),folder/'comparison.md')
            elif action=='fill':result=engine.fill_form(source,self._text(payload),folder/'filled.hwpx')
            elif action=='patch':result=engine.patch_document(source,copy_input(payload.get('other'),'edited'),folder/'patched.hwpx')
            else:result=engine.generate_hwpx(source,payload.get('preset','보고서'),folder/'generated.hwpx', image_dir=Path(payload.get('path')).resolve().parent)
            result=Path(result)
            data={'path':str(result),'engine':contract,'status':'partial' if '일부미적용' in result.name else 'complete'}
            if result.is_file() and result.suffix.lower() in ('.md','.json','.txt'):
                with result.open('r',encoding='utf-8',errors='replace') as stream:data['text']=stream.read(1_000_000)
            return data
        except ServiceError:raise
        except (RuntimeError,OSError,ValueError,subprocess.TimeoutExpired) as exc:
            raise ServiceError('ADVANCED_UNAVAILABLE',str(exc)) from exc

    def advanced_job(self, action, payload):
        import uuid
        folder=str(self.folder.resolve())
        if action=='poll':
            identity=payload.get('id')
            with _JOB_LOCK:
                item=_JOBS.get(identity)
                if item is None or item['folder']!=folder:
                    raise ServiceError('JOB_NOT_FOUND','고급 작업을 다시 시작해 주세요.')
                return deepcopy({key:value for key,value in item.items() if key not in ('folder','signature')})
        signature=json.dumps(payload,ensure_ascii=False,sort_keys=True)
        if len(signature.encode())>1_100_000:raise ServiceError('INPUT_LIMIT','입력이 너무 큽니다.')
        with _JOB_LOCK:
            for item in _JOBS.values():
                if item['folder']==folder and item['status']=='running':
                    if item['signature']==signature:
                        return {'id':item['id'],'status':'running'}
                    raise ServiceError('JOB_RUNNING','진행 중인 고급 작업이 끝난 뒤 다시 실행해 주세요.')
            if len(_JOBS)>=100:
                expired=next((key for key,item in _JOBS.items() if item['status']!='running'),None)
                if expired is not None:_JOBS.pop(expired)
                else:raise ServiceError('JOB_LIMIT','고급 작업이 많습니다. 잠시 후 실행해 주세요.')
            identity=uuid.uuid4().hex
            item={'id':identity,'folder':folder,'signature':signature,'status':'running'}
            _JOBS[identity]=item
        request=deepcopy(payload)
        def work():
            try:
                result=self.advanced(request)
                update={'status':'complete','result':result}
            except ServiceError as exc:
                update={'status':'failed','error':{'code':exc.code,'message':str(exc)}}
            except Exception:
                update={'status':'failed','error':{'code':'ADVANCED_FAILED','message':'고급 도구 실행에 실패했습니다.'}}
            with _JOB_LOCK:item.update(update)
        threading.Thread(target=work,daemon=True,name='advanced-document-tool').start()
        return {'id':identity,'status':'running'}

    def command(self, name, payload):
        if not isinstance(payload,dict):raise ServiceError('INVALID_INPUT','입력을 확인해 주세요.')
        if name.startswith('outline.'):
            try:
                return self.outline(name.split('.',1)[1],payload)
            except (OSError, UnicodeError) as exc:
                raise ServiceError('DRAFT_IO','초안 파일을 읽거나 저장하지 못했습니다.') from exc
        if name in ('advanced.start','advanced.poll'):return self.advanced_job(name.split('.')[1],payload)
        if name=='advanced':return self.advanced(payload)
        text=self._text(payload)
        if name=='add_text':
            if not text.strip():raise ServiceError('EMPTY_TEXT','추가할 텍스트를 입력해 주세요.')
            import uuid
            folder=self.folder/'입력문서'
            try:
                folder.mkdir(parents=True,exist_ok=True)
                path=folder/('붙여넣기-'+uuid.uuid4().hex+'.txt')
                with path.open('x',encoding='utf-8') as stream:stream.write(text)
            except OSError as exc:
                raise ServiceError('TEXT_SAVE_FAILED','입력 문서를 저장하지 못했습니다.') from exc
            return {'path':str(path)}
        transforms={'clean':pasted_text.clean_pasted_text,'outline':pasted_text.outline_pasted_text,
                    'labels':labeled_text.label_outline_text,'amount':writing_aids.hangulize_amounts,
                    'commas':writing_aids.add_commas,'weekdays':writing_aids.add_weekdays,
                    'age':writing_aids.ages_for_lines,'mask_rrn':writing_aids.mask_rrn}
        try:
            if name in transforms:return {'text':transforms[name](text)}
            if name=='prompts':return {'prompts':[{'name':n,'description':d} for n,d,_,_ in ai_prompts.all_prompts()]}
            if name=='prompt':return {'text':ai_prompts.build_prompt(payload.get('name'),text)}
            if name=='date_diff':
                dates=[writing_aids.parse_date(line) for line in text.splitlines() if line.strip()]
                if len(dates)!=2 or any(value is None for value in dates):raise ValueError('dates')
                return {'text':str(writing_aids.days_between(*dates))+'일'}
            if name=='table_calc':return {'text':writing_aids.table_to_text(writing_aids.calc_table(
                writing_aids.parse_table(text),payload.get('operation','col_sum')))}
            if name in ('review','proofread','proofread_apply','numbers','markdown'):
                path=Path(payload.get('path',''))
                if path.suffix.lower()!='.hwpx' or not path.is_file():
                    raise ServiceError('INVALID_PATH','검토할 HWPX 사본을 선택해 주세요.')
                if name=='review':
                    from docfit_core.document_review import review_document
                    return review_document(path)
                if name in ('proofread','proofread_apply'):
                    return self.proofread(path,payload,apply=name=='proofread_apply')
                from docfit_core.hwpx import inspect_hwpx,to_markdown
                doc=inspect_hwpx(path)
                if name=='markdown':return {'text':to_markdown(doc)}
                from docfit_core.number_check import 숫자_대조
                return 숫자_대조(doc)
        except ServiceError:raise
        except (ValueError,TypeError,KeyError,OSError) as exc:
            raise ServiceError('TOOL_INPUT','입력 형식·날짜·계산 종류·문서 경로를 확인해 주세요.') from exc
        raise ServiceError('INVALID_TOOL','지원하지 않는 문서 도구입니다.')
