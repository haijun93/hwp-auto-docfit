"""동일 본문 무결성 비교의 최적화 전후 비용을 합성 문서로 비교한다."""
from difflib import SequenceMatcher
import json
from pathlib import Path
from statistics import median
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from docfit_core.hwpx import DocumentBlock, DocumentInspection, compare_documents


def main():
    text = 'ㅇ 행정서비스 운영 계획과 세부 추진 내용을 검토합니다.\n' * 150
    doc = DocumentInspection('generated.hwpx', [DocumentBlock('paragraph', text)],
                             1, 1, 0, 0, 0, text, '', [])
    def measure(fn, repeats):
        times = []
        for _ in range(repeats):
            start = perf_counter()
            fn()
            times.append(perf_counter() - start)
        return median(times)
    old = measure(lambda: SequenceMatcher(None, text, text, autojunk=False).ratio(), 3)
    new = measure(lambda: compare_documents(doc, doc), 30)
    print(json.dumps({'characters': len(text), 'previous_text_comparison_seconds': old,
                      'optimized_integrity_comparison_seconds': new,
                      'note': '합성 동일 본문 비교 비용. 전체 문서 처리 속도의 측정값은 아님.'},
                     ensure_ascii=True))


if __name__ == '__main__':
    main()
