"""Standalone Python backend entry point; never imports Tk or WebView."""
import json
import os
from pathlib import Path
import sys
import threading
from docfit_app.application_service import ApplicationService
from docfit_app.ipc_server import IpcServer
from docfit_infra.storage.process_lock import ProcessLock, LockUnavailable


def main():
    bootstrap=sys.stdin.buffer.readline(4097)
    if len(bootstrap)>4096: return 2
    try:
        token=json.loads(bootstrap)['token']
        if not isinstance(token,str) or not token.isascii() or len(token)<32 or len(token)>128: return 2
    except (ValueError,KeyError,TypeError): return 2
    appdata=os.environ.get('APPDATA') or os.environ.get('LOCALAPPDATA')
    folder=Path(appdata)/'HwpAutoDocFit' if appdata else Path.home()/'.hwp_auto_docfit'
    try:
        with ProcessLock(folder/'.native-backend.lock',blocking=False):
            app=ApplicationService(folder/'settings.json')
            with IpcServer(app,token) as server:
                print(json.dumps({'protocol_version':1,'ready':True,'port':server.server_address[1],
                                  'backend_version':'1.74 Native Prototype 1'}),flush=True)
                # Parent owns stdin; exiting Flutter closes it even if shutdown RPC is lost.
                def parent_closed():
                    # Do not hold BufferedReader's lock across a blocking pipe
                    # read. Windows interpreter shutdown may otherwise wait for
                    # that daemon reader until the parent closes its stdin.
                    try:
                        while os.read(sys.stdin.fileno(), 4096):
                            pass
                    except OSError:
                        pass
                    app.data.closing=True
                    app.jobs.shutdown()
                    server.shutdown()
                threading.Thread(target=parent_closed,daemon=True).start()
                server.serve_forever(poll_interval=0.1)
    except LockUnavailable:
        print(json.dumps({'protocol_version':1,'ready':False,'error':{
            'code':'ALREADY_RUNNING','message':'다른 네이티브 백엔드가 이미 실행 중입니다.'}}),flush=True)
        return 2
    return 0


if __name__=='__main__':
    raise SystemExit(main())
