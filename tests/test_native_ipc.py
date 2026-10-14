import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


class NativeIpcTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.token='a'*48
        self.process=subprocess.Popen([sys.executable,'-u','-m','docfit_app.backend_main'],
            cwd=Path(__file__).parents[1], env={**os.environ,'APPDATA':self.temp.name},
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        self.addCleanup(self.cleanup)
        self.process.stdin.write(json.dumps({'token':self.token}).encode()+b'\n');self.process.stdin.flush()
        import queue, threading
        ready=queue.Queue()
        threading.Thread(target=lambda:ready.put(self.process.stdout.readline()),daemon=True).start()
        self.ready=json.loads(ready.get(timeout=10))
        self.socket=socket.create_connection(('127.0.0.1',self.ready['port']),timeout=5)
        self.stream=self.socket.makefile('rwb');self.addCleanup(self.stream.close);self.addCleanup(self.socket.close)
        self.counter=0

    def cleanup(self):
        if not self.process.stdin.closed:
            self.process.stdin.close()
        if self.process.poll() is None:
            try:self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:self.process.kill();self.process.wait(timeout=5)
        for pipe in (self.process.stdout,self.process.stderr):pipe.close()

    def request(self,method,args=None,request_id=None,version=1):
        self.counter+=1
        message={'protocol_version':version,'request_id':request_id or str(self.counter),
                 'token':self.token,'method':method,'params':{'args':args or []}}
        self.stream.write(json.dumps(message).encode()+b'\n');self.stream.flush()
        return json.loads(self.stream.readline())

    def test_handshake_settings_and_normal_shutdown(self):
        self.assertFalse(self.request('handshake')['result']['engine_ready'])
        state=self.request('get_state')['result'];self.assertFalse(state['can_start'])
        snapshot=self.request('get_settings')['result']['data']
        result=self.request('save_settings',[{'retry_body':'7'},snapshot['revision']])
        self.assertTrue(result['result']['ok'])
        self.assertEqual(self.request('get_settings')['result']['data']['values']['retry_body'],'7')
        self.assertTrue(self.request('shutdown')['success'])
        # RPC shutdown must finish even while the parent-owned pipe is open.
        self.assertFalse(self.process.stdin.closed)
        self.process.wait(timeout=5)
        self.assertEqual(self.process.returncode,0,self.process.stderr.read().decode('utf-8',errors='replace'))

    def test_duplicate_version_and_unknown_method_are_rejected(self):
        self.assertTrue(self.request('get_state',request_id='same')['success'])
        self.assertEqual(self.request('get_state',request_id='same')['error']['code'],'DUPLICATE_REQUEST')
        self.assertEqual(self.request('get_state',version=2)['error']['code'],'PROTOCOL_VERSION')
        self.assertFalse(self.request('exec',['arbitrary'])['success'])

    def test_wrong_token_cannot_dispatch(self):
        self.token='b'*48
        self.stream.write(json.dumps({'protocol_version':1,'request_id':'1','token':self.token,
             'method':'shutdown','params':{'args':[]}}).encode()+b'\n');self.stream.flush()
        self.assertEqual(self.stream.readline(),b'')
        self.assertIsNone(self.process.poll())

    def test_parent_pipe_closure_exits_backend(self):
        self.process.stdin.close();self.process.wait(timeout=5)

    def test_backend_never_imports_gui_modules(self):
        code='import docfit_app.backend_main, sys; assert not any(k in sys.modules for k in ("tkinter","webview","tkinterdnd2"))'
        subprocess.run([sys.executable,'-c',code],check=True,cwd=Path(__file__).parents[1],timeout=10)

    def test_second_backend_cannot_own_same_settings_directory(self):
        other=subprocess.Popen([sys.executable,'-u','-m','docfit_app.backend_main'],
            cwd=Path(__file__).parents[1],env={**os.environ,'APPDATA':self.temp.name},
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout,stderr=other.communicate(json.dumps({'token':'c'*48}).encode()+b'\n',timeout=10)
        reply=json.loads(stdout)
        self.assertFalse(reply['ready'])
        self.assertEqual(reply['error']['code'],'ALREADY_RUNNING')
        self.assertEqual(other.returncode,2)
        self.assertTrue(self.request('get_state')['success'])

    def test_unicode_document_registration_and_inspection_preserve_source(self):
        import hashlib
        from tests.test_hwpx_core import make_hwpx
        source=Path(self.temp.name)/'민원 답변.hwpx'
        make_hwpx(source)
        before=hashlib.sha256(source.read_bytes()).digest()
        reply=self.request('add_paths',[[str(source),str(source)]])
        self.assertTrue(reply['success'])
        self.assertEqual(reply['result']['count'],1)
        inspected=self.request('inspect_document',[str(source)])
        self.assertTrue(inspected['success'],inspected)
        self.assertEqual(inspected['result']['table_count'],1)
        self.assertEqual(hashlib.sha256(source.read_bytes()).digest(),before)

    def test_oversized_frame_is_closed_without_dispatch(self):
        self.stream.write(b'x'*(1024*1024+1)+b'\n');self.stream.flush()
        try:
            self.assertEqual(self.stream.readline(),b'')
        except ConnectionResetError:
            pass
        self.assertIsNone(self.process.poll())
