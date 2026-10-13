"""Authenticated loopback JSON IPC; no GUI or COM dependencies."""
from collections import OrderedDict
import json
import secrets
import socketserver
import threading
from .api_contract import ServiceError

PROTOCOL_VERSION = 1
MAX_MESSAGE = 1024 * 1024

class IpcServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = False
    daemon_threads = True
    request_queue_size = 8

    def __init__(self, app, token):
        self.app, self.token = app, token
        self.connections = threading.BoundedSemaphore(8)
        super().__init__(('127.0.0.1',0), IpcHandler)

    def process_request(self, request, client_address):
        if not self.connections.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.connections.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.connections.release()


class IpcHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.connection.settimeout(30)
        seen=OrderedDict()
        try:
            while True:
                line=self.rfile.readline(MAX_MESSAGE+1)
                if not line: return
                if len(line)>MAX_MESSAGE or not line.endswith(b'\n'): return
                request_id=None
                try:
                    request=json.loads(line)
                    if not isinstance(request,dict): raise ValueError()
                    request_id=request.get('request_id')
                    if not isinstance(request_id,str) or not 1<=len(request_id)<=128: raise ValueError()
                    token=request.get('token')
                    if not isinstance(token,str) or not token.isascii() or not secrets.compare_digest(token,self.server.token):
                        return  # No dispatch or error details to unauthenticated clients.
                    if type(request.get('protocol_version')) is not int or request.get('protocol_version')!=PROTOCOL_VERSION:
                        raise ServiceError('PROTOCOL_VERSION','앱과 백엔드 버전을 확인해 주세요.')
                    if request_id in seen:
                        raise ServiceError('DUPLICATE_REQUEST','같은 요청을 다시 실행할 수 없습니다.')
                    seen[request_id]=None
                    if len(seen)>4096:
                        seen.popitem(last=False)
                    method=request.get('method'); params=request.get('params')
                    if not isinstance(method,str) or not isinstance(params,dict) or not isinstance(params.get('args'),list):
                        raise ValueError()
                    with self.server.app.lock:
                        result=self.server.app.dispatch(method,params['args'])
                    output={'protocol_version':1,'request_id':request_id,'success':True,'result':result}
                except ServiceError as exc:
                    output={'protocol_version':1,'request_id':request_id,'success':False,
                            'error':{'code':exc.code,'message':str(exc),'recoverable':exc.recoverable}}
                except (ValueError,TypeError,IndexError,KeyError):
                    output={'protocol_version':1,'request_id':request_id,'success':False,
                            'error':{'code':'INVALID_INPUT','message':'입력 형식을 확인해 주세요.','recoverable':True}}
                except Exception:
                    output={'protocol_version':1,'request_id':request_id,'success':False,
                            'error':{'code':'BACKEND_ERROR','message':'작업을 완료하지 못했습니다.','recoverable':True}}
                encoded=json.dumps(output,ensure_ascii=False).encode()+b'\n'
                if len(encoded)>MAX_MESSAGE:
                    encoded=json.dumps({'protocol_version':1,'request_id':request_id,'success':False,
                        'error':{'code':'MESSAGE_LIMIT','message':'결과가 너무 큽니다. 더 작은 문서를 선택해 주세요.','recoverable':True}}).encode()+b'\n' 
                self.wfile.write(encoded);self.wfile.flush()
                if self.server.app.data.closing:
                    threading.Thread(target=self.server.shutdown,daemon=True).start()
                    return
        except (OSError,TimeoutError):
            return

