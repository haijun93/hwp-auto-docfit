"""Force stop tests: no real COM or process termination."""
import runpy
import threading
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch
from docfit_core import hwp_process as hp
from docfit_engine import com_driver
from desktop_web_ui import DesktopWebBridge


class ProcessTests(unittest.TestCase):
    def tearDown(self):
        for pid in hp.owned_pids():
            hp.forget(pid)

    def test_parse_tasklist(self):
        runner = Mock(return_value=NS(returncode=0, stdout='"Hwp.exe","12","Console"\n"HWP.EXE","13"\n"Other.exe","14"\n"Hwp.exe","bad"'))
        self.assertEqual(hp.hwp_pids(runner=runner), {12, 13})
        self.assertIn('/NH', runner.call_args.args[0])

    def test_only_owned_live_hwp_is_killed(self):
        hp.register_owned({10, 20, 30})
        def run(args):
            if args[0] == 'tasklist':
                return NS(returncode=0, stdout='"Hwp.exe","10"\n"Other.exe","30"\n"Hwp.exe","99"')
            return NS(returncode=0)
        runner = Mock(side_effect=run)
        self.assertEqual(hp.kill_owned(runner=runner), [10])
        kills = [c.args[0] for c in runner.call_args_list if c.args[0][0] == 'taskkill']
        self.assertEqual(kills, [['taskkill', '/PID', '10', '/T', '/F']])
        self.assertEqual(hp.owned_pids(), set())

    def test_query_failure_never_kills(self):
        hp.register_owned({10})
        runner = Mock(side_effect=OSError('failed'))
        self.assertEqual(hp.kill_owned(runner=runner), [])
        self.assertEqual(hp.owned_pids(), {10})

    def test_dispatch_ex_registers_difference(self):
        win32 = NS(DispatchEx=Mock(return_value='app'), Dispatch=Mock(return_value='fallback'))
        fn = com_driver._install(_docfit_namespace={'win32': win32}, _docfit_symbol='한글_COM_인스턴스_생성')
        with patch.object(hp, 'hwp_pids', side_effect=[{1}, {1, 2}]), patch.object(hp, 'register_owned') as register:
            self.assertEqual(fn(), 'app')
            register.assert_called_once_with({2})

    def test_dispatch_fallback_not_registered(self):
        win32 = NS(DispatchEx=Mock(side_effect=RuntimeError()), Dispatch=Mock(return_value='fallback'))
        fn = com_driver._install(_docfit_namespace={'win32': win32}, _docfit_symbol='한글_COM_인스턴스_생성')
        with patch.object(hp, 'hwp_pids', return_value={1}), patch.object(hp, 'register_owned') as register:
            self.assertEqual(fn(), 'fallback')
            register.assert_not_called()

    def test_pid_failure_does_not_prevent_creation(self):
        fn = com_driver._install(_docfit_namespace={'win32': NS(DispatchEx=Mock(return_value='app'), Dispatch=Mock())}, _docfit_symbol='한글_COM_인스턴스_생성')
        with patch.object(hp, 'hwp_pids', side_effect=OSError()):
            self.assertEqual(fn(), 'app')


class LegacyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.gui = cls.ns['HwpAutoDocFitGUI']

    def app(self):
        app = NS(root=Mock(), worker=Mock(), running=True, closing=False,
                 stop_button=Mock(), status_var=Mock(), 로그표시=Mock(),
                 _비교창_분리_후_보존=Mock(), _강제_종료=Mock(), 버튼_작업중=Mock(),
                 selected_mode=Mock(), _알림=Mock(return_value=True), worker_종료확인=Mock())
        app._중단_유예_확인 = lambda: self.gui._중단_유예_확인(app)
        return app

    def test_stop_grace_kills_only_still_running_worker(self):
        app = self.app()
        with patch.object(hp, 'kill_owned', return_value=[1]) as kill:
            self.gui.작업중단(app)
            app.root.after.assert_called_once_with(10000, app._중단_유예_확인)
            app._중단_유예_확인()
            kill.assert_called_once_with()
            self.assertIn('강제로 종료', app.status_var.set.call_args.args[0])
            app.worker.is_alive.return_value = False
            app._중단_유예_확인()
            self.assertEqual(kill.call_count, 1)

    def test_stale_stop_does_not_kill_next_worker(self):
        app = self.app()
        self.gui.작업중단(app)
        app.worker = Mock()
        with patch.object(hp, 'kill_owned') as kill:
            app._중단_유예_확인()
            kill.assert_not_called()

    def test_new_stop_restarts_grace_timer(self):
        app = self.app()
        app.root.after.return_value = 'timer1'
        self.gui.작업중단(app)
        app.worker = Mock()
        self.gui.작업중단(app)
        app.root.after_cancel.assert_called_once_with('timer1')

    def test_close_deadlines(self):
        app = self.app()
        with patch('time.monotonic', side_effect=[100, 109.99, 110, 114.99, 115]), patch.object(hp, 'kill_owned') as kill:
            for index in range(5):
                self.gui.worker_종료확인(app)
                self.assertEqual(kill.call_count, int(index >= 2))
                self.assertEqual(app._강제_종료.call_count, int(index == 4))

    def test_worker_finished_closes_normally(self):
        app = self.app()
        app.worker.is_alive.return_value = False
        self.gui.worker_종료확인(app)
        app.root.destroy.assert_called_once()

    def test_modes_and_labels(self):
        for mode, name in [('file_format', '파일포맷 변경'), ('spacing', '자간 정리'), ('format', '서식 적용'), ('all', '한 번에 적용'), ('unify', '서식 통일'), ('unknown', '작업')]:
            with self.subTest(mode=mode):
                app = self.app()
                app.selected_mode.get.return_value = mode
                self.gui.종료(app)
                call = app._알림.call_args
                self.assertIn(f'현재 {name} 작업이 진행 중입니다.', call.args[2])
                self.assertEqual(call.kwargs, {'flutter_ok_label': '작업 중단하고 종료', 'flutter_cancel_label': '계속 진행'})

    def test_second_close_forces_exit_only_if_confirmed(self):
        for accepted in (True, False):
            app = self.app()
            app.closing = True
            app._알림.return_value = accepted
            self.gui.종료(app)
            self.assertEqual(app._강제_종료.call_count, int(accepted))

    def test_force_exit_injection_and_detach_failure(self):
        app = self.app()
        app._비교창_분리_후_보존.side_effect = RuntimeError()
        app._프로세스_종료 = Mock()
        with patch.object(hp, 'kill_owned') as kill:
            self.gui._강제_종료(app)
            kill.assert_called_once()
        app._프로세스_종료.assert_called_once_with(0)

    def test_pending_custom_labels_and_bridge(self):
        app = self.app()
        app.root._docfit_hidden_backend = True
        captured = []
        def wait(done):
            captured.append(DesktopWebBridge(app)._pending_dialog())
            app._flutter_dialog['answer'] = True
        app.root.wait_variable.side_effect = wait
        with patch.object(self.gui._알림.__globals__['tk'], 'BooleanVar', return_value=Mock()):
            self.assertTrue(self.gui._알림(app, self.ns['messagebox'].askyesno, 'title', 'message', flutter_ok_label='끝내기', flutter_cancel_label='계속'))
        self.assertEqual(captured[0]['ok_label'], '끝내기')
        self.assertEqual(captured[0]['cancel_label'], '계속')

    def test_tk_does_not_receive_flutter_labels(self):
        app = self.app()
        app.root._docfit_hidden_backend = False
        fn = Mock()
        self.gui._알림(app, fn, 'title', parent='parent', flutter_ok_label='종료', flutter_cancel_label='계속')
        fn.assert_called_once_with('title', parent='parent')
