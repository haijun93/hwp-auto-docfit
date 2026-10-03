"""문두 라벨(괄호·콜론 라벨) 굵게: 별표(*, **)는 기본으로 뺀다. 예전 설정 파일은 불러올 때 한 번만 끈다."""
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch


class LabelBoldDefaultsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_asterisk_labels_are_not_bold_by_default(self):
        ns = self.ns
        self.assertFalse(ns['기본_설정']['label_symbols']['*'])
        self.assertFalse(ns['기본_설정']['label_symbols']['**'])
        excluded = ns['문두_라벨_굵게_제외_문단인가']
        self.assertTrue(excluded('* 지자(智子): 양성자를 11차원으로 전개'))
        self.assertTrue(excluded('   ** 파벽자: 대응 요원'))
        self.assertFalse(excluded('- 추진부서 : 총무과'))
        self.assertFalse(excluded('ㅇ (운영방식) 비정기'))

    def _load(self, saved):
        with tempfile.TemporaryDirectory(prefix='docfit-label-bold-') as folder:
            with patch.dict(os.environ, {'APPDATA': folder}):
                path = self.ns['설정_파일_경로']()
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(saved, ensure_ascii=False), encoding='utf-8')
                return self.ns['설정_불러오기']()

    def test_old_settings_file_turns_asterisks_off_once(self):
        # 예전 파일(판 표시 없음)은 모든 기호를 켠 채 저장돼 있다 → 별표만 끄고 다른 선택은 그대로
        old = {'label_symbols': {'□': False, '※': False, '*': True, '**': True, '-': True, 'ㅇ': False}}
        loaded = self._load(old)
        self.assertEqual(loaded['label_symbols'], {'□': False, '※': False, '*': False, '**': False,
                                                   '-': True, 'ㅇ': False})
        self.assertEqual(loaded['label_symbols_rev'], 2)
        # 판 2로 저장된 뒤 사용자가 다시 켠 값은 그대로 둔다.
        again = self._load({'label_symbols': {'*': True, '**': True}, 'label_symbols_rev': 2})
        self.assertTrue(again['label_symbols']['*'])
        self.assertTrue(again['label_symbols']['**'])


if __name__ == '__main__':
    unittest.main()
