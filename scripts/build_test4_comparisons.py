"""지정 폴더의 TXT 사본을 실제 앱으로 처리해 README 이미지 두 개를 만든다.

한/글 자체 PDF의 글꼴·조판을 그대로 렌더링한다. 빨간색은 비교 안내를 위한
주석이며 결과 HWPX는 바꾸지 않는다. 원본·사용자 설정은 변경하지 않는다.
추가 렌더링 의존성: Pillow, pypdfium2.
"""
import argparse
import copy
import ctypes
from difflib import SequenceMatcher
from hashlib import sha256
import json
from pathlib import Path
import runpy
import shutil
import sys
import time

from PIL import Image, ImageDraw, ImageFont, ImageOps
import pypdfium2 as pdfium
import pypdfium2.raw as raw

RED = (198, 40, 40)
INK = '#243247'
GRAY = '#64748b'
SCALE = 4


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def process(app_root, source, folder, mode):
    folder.mkdir(parents=True, exist_ok=False)
    copied = folder / source.name
    shutil.copy2(source, copied)
    ns = runpy.run_path(str(app_root / 'hwp-auto-docfit.py'), run_name='readme_test4')
    g = ns['작업_실행'].__globals__
    from docfit_core.stage_selection import default_choice, stages_for_mode
    defaults = copy.deepcopy(g['기본_설정'])
    g['설정_불러오기'] = lambda: copy.deepcopy(defaults)
    g['한글_COM_인스턴스_생성'] = lambda 독립=True: g['win32'].DispatchEx('HwpFrame.HwpObject')
    g['이전_작업_임시폴더_정리'] = lambda: 0
    g['표준서식_설정'] = copy.deepcopy(g['기본_서식프로파일']()['format'])
    # 보안 모듈 등록은 기존 환경을 읽기만 한다.
    def prepared_security():
        registered = g['등록된_DLL_경로']()
        if not registered or not Path(registered).is_file():
            raise RuntimeError('이미 등록된 한/글 자동화 보안 모듈이 필요합니다.')
    g['보안모듈_초기화'] = prepared_security
    original_close = g['작업창_닫기']
    def close_owned_copy():
        if g.get('hwp') is not None:
            g['hwp'].Clear(1)
        original_close()
    g['작업창_닫기'] = close_owned_copy
    g['_서식통일_최종결과_사용자확인'] = lambda *_: None
    convert = g['텍스트_hwpx로_변환']
    baseline = folder / 'before.hwpx'
    def convert_and_keep(text, target):
        result = convert(text, target)
        shutil.copy2(target, baseline)
        return result
    g['텍스트_hwpx로_변환'] = convert_and_keep
    stages = {key: default_choice(key, mode) for key, _ in stages_for_mode(mode)}
    logs = []
    with (folder / 'run.log').open('w', encoding='utf-8') as log_file:
        def log(*args):
            message = ' '.join(map(str, args))
            logs.append(message)
            log_file.write(message + '\n')
            log_file.flush()
        g.update(로그=log, 진단로그=log, 상태=lambda *_: None,
                 단계표시=lambda name, *_: print(f'[{mode}] {name}', flush=True))
        print(f'START {mode}', flush=True)
        started = time.perf_counter()
        g['작업_실행']([str(copied)], 실행모드=mode, 자동닫기=True,
            표준서식=mode == 'all', 검수=True, 로그파일=False,
            단어분리방지=True, 표준서식_세부=copy.deepcopy(defaults),
            표준서식_문단위간격_pt={key: int(defaults[key]) for key in defaults if key.startswith('std_parspace_')},
            라벨기호설정=copy.deepcopy(defaults['label_symbols']), 세부작업_선택=stages,
            무결성보고서파일=False, 최종검수파일=False)
        elapsed = time.perf_counter() - started
    events = []
    while not g['gui_queue'].empty():
        events.append(g['gui_queue'].get_nowait())
    saved = [Path(e[2]) for e in events if e[0] == 'saved']
    errors = [e[0] for e in events if e[0] in ('fatal_error', 'document_error')]
    if errors or not saved or not baseline.is_file():
        raise RuntimeError(f'{mode} 처리 실패: {errors}')
    g['pythoncom'].CoInitialize()
    app = g['win32'].DispatchEx('HwpFrame.HwpObject')
    pages = {}
    try:
        if not app.RegisterModule(g['REGISTER_MODULE_NAME'], g['REGISTER_MODULE_VALUE']):
            raise RuntimeError('PDF 내보내기 세션 보안 모듈 오류')
        hwp_version = str(app.Version)
        for name, path in [('before', baseline), ('after', saved[-1])]:
            if app.Open(str(path), 'HWPX', 'forceopen:true') is False:
                raise RuntimeError(f'결과 열기 실패: {name}')
            pages[name] = int(app.PageCount)
            if app.SaveAs(str(folder / f'{name}.pdf'), 'PDF', '') is False:
                raise RuntimeError(f'PDF 저장 실패: {name}')
            app.Clear(1)
    finally:
        app.Clear(1)
        app.Quit()
        g['pythoncom'].CoUninitialize()
    record = dict(mode=mode, app_version=g['APP_VERSION'], hwp_version=hwp_version,
                  elapsed_seconds=round(elapsed, 3), pages=pages,
                  source_sha256=digest(source), result_sha256=digest(saved[-1]),
                  source_unchanged=digest(source) == digest(copied),
                  score=[x for x in logs if '작업 수행 점수' in x][-1:],
                  word_stats=copy.deepcopy(g['단어분리_통계']),
                  short_stats=copy.deepcopy(g['문장부호_통계']),
                  stage_choices=stages,
                  options={'profile': '기본 보고서 서식', 'reset_spacing': True,
                           'exclude_tables': False, 'exclude_pagefit': False})
    (folder / 'run.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'DONE {mode}: {elapsed:.1f}s / pages={pages}', flush=True)
    return record


def read_pdf(path):
    pdf = pdfium.PdfDocument(str(path))
    images, chars = [], []
    try:
        for page_number in range(len(pdf)):
            page = pdf[page_number]
            w, h = page.get_size()
            bitmap = page.render(scale=SCALE)
            images.append(bitmap.to_pil().convert('RGB').copy())
            text = page.get_textpage()
            for i in range(text.count_chars()):
                char = chr(raw.FPDFText_GetUnicode(text, i))
                if not char or char.isspace() or char == '\x00':
                    continue
                box = text.get_charbox(i)
                size = raw.FPDFText_GetFontSize(text, i)
                flags = ctypes.c_int()
                buffer = ctypes.create_string_buffer(512)
                raw.FPDFText_GetFontInfo(text, i, buffer, 512, ctypes.byref(flags))
                chars.append({'char': char, 'page': page_number,
                              'box': (box[0]*SCALE, (h-box[3])*SCALE, box[2]*SCALE, (h-box[1])*SCALE),
                              'font': buffer.value.decode('utf-8', errors='replace'),
                              'size': round(size, 3), 'flags': flags.value})
            text.close()
            bitmap.close()
            page.close()
    finally:
        pdf.close()
    return images, chars


def changes(before, after, spacing=False):
    a, b = ''.join(c['char'] for c in before), ''.join(c['char'] for c in after)
    left, right = set(), set()
    for op, i, j, k, l in SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op != 'equal':
            left.update(range(i, j)); right.update(range(k, l))
            continue
        for bi, ai in zip(range(i, j), range(k, l)):
            x, y = before[bi], after[ai]
            # 자간 비교는 줄을 옮긴 글자부터 찾고, 해당 어절 전체를 강조한다.
            changed = (x['page'] != y['page'] or abs(x['box'][1]-y['box'][1]) > 5*SCALE)
            if not spacing:
                changed |= (x['font'], x['size'], x['flags']) != (y['font'], y['size'], y['flags'])
                changed |= abs(x['box'][0]-y['box'][0]) > SCALE
            if changed:
                left.add(bi); right.add(ai)
    if spacing:
        # 이 문서의 개요에서 실제로 이동한 어절만 보여 준다.
        selected_left, selected_right, words = set(), set(), []
        for word in ('거점(지구)', '수립하여'):
            i, k = a.find(word), b.find(word)
            if i >= 0 and k >= 0 and (left.intersection(range(i, i+len(word))) or right.intersection(range(k, k+len(word)))):
                selected_left.update(range(i, i+len(word)))
                selected_right.update(range(k, k+len(word)))
                words.append(word)
        if not words:
            raise RuntimeError('개요의 실제 어절 이동이 없어 과거 사례를 재현한 것으로 표시할 수 없습니다.')
        return selected_left, selected_right, words
    return left, right, []


def highlight(images, chars, indexes):
    # 원래 렌더링의 글자 픽셀에만 안내색을 입힌다. 테두리·배경·글꼴·좌표를 재작성하지 않는다.
    result = [im.copy() for im in images]
    for index in indexes:
        char = chars[index]
        im = result[char['page']]
        box = tuple(round(x) for x in char['box'])
        box = (max(0, box[0]-1), max(0, box[1]-1), min(im.width, box[2]+1), min(im.height, box[3]+1))
        if box[0] >= box[2] or box[1] >= box[3]:
            continue
        region = im.crop(box)
        values = []
        for pixel in region.get_flattened_data():
            if max(pixel) < 225:
                darkness = 1-min(pixel)/255
                values.append(tuple(round(255+(c-255)*darkness) for c in RED))
            else:
                values.append(pixel)
        region.putdata(values)
        im.paste(region, box[:2])
    return result


def font(size, bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf' if bold else 'C:/Windows/Fonts/malgun.ttf', size)


def focus(chars):
    text = ''.join(c['char'] for c in chars)
    start = text.index('삼체행성의항성계')
    end = text.index('보고드림.', start) + len('보고드림.')
    selection = chars[start:end]
    if len({c['page'] for c in selection}) != 1:
        raise RuntimeError('개요가 여러 쪽에 걸쳐 있어 별도 확대 구성이 필요합니다.')
    x0 = min(c['box'][0] for c in selection)-9*SCALE
    y0 = min(c['box'][1] for c in selection)-11*SCALE
    x1 = max(c['box'][2] for c in selection)+9*SCALE
    y1 = max(c['box'][3] for c in selection)+11*SCALE
    return selection[0]['page'], (int(x0), int(y0), int(x1), int(y1))


def render(folder, output, mode, record):
    before_images, before_chars = read_pdf(folder / 'before.pdf')
    after_images, after_chars = read_pdf(folder / 'after.pdf')
    left, right, words = changes(before_chars, after_chars, spacing=mode == 'spacing')
    a = highlight(before_images, before_chars, left)
    b = highlight(after_images, after_chars, right)
    if mode == 'spacing':
        im = Image.new('RGB', (1800, 960), '#f3f6fa')
        panels = [(40, 180, 1720, 310), (40, 510, 1720, 310)]
        for images, chars, (x,y,w,h), label in zip((a,b), (before_chars,after_chars), panels, ('전 | TXT를 한/글로 변환한 직후', '후 | 자간 정리 실제 결과')):
            d = ImageDraw.Draw(im)
            d.rounded_rectangle((x,y,x+w,y+h), radius=14, fill='white', outline='#d5deea', width=2)
            d.text((x+22,y+12),label,font=font(30,True),fill=INK)
            page, crop = focus(chars)
            view = images[page].crop(crop)
            view = ImageOps.contain(view, (w-52,h-76), Image.Resampling.LANCZOS)
            im.paste(view, (x+(w-view.width)//2,y+64))
        title = '자간 정리 | 실제 개요의 갈라진 어절을 앞줄로'
        note = '빨간색: 실제 줄 위치가 바뀐 '+ ' · '.join(words) + '  |  문서 글꼴·줄바꿈은 한/글 출력 그대로'
    else:
        im = Image.new('RGB', (1800, 1360), '#f3f6fa')
        for images, x, label in ((a,40,'전 | 텍스트 초안의 실제 1쪽'), (b,920,'후 | 한 번에 적용의 실제 1쪽')):
            d = ImageDraw.Draw(im)
            d.rounded_rectangle((x,180,x+840,1170), radius=14, fill='white', outline='#d5deea', width=2)
            d.text((x+18,194),label,font=font(29,True),fill=INK)
            # 전체 첫 쪽을 동일한 용지 기준으로 보여 준다.
            view = ImageOps.contain(images[0], (806, 914), Image.Resampling.LANCZOS)
            im.paste(view,(x+(840-view.width)//2,248))
        title = '한 번에 적용 | test4 보고서 초안 → 실제 보고서'
        note = '빨간색: 달라진 글자·서식·위치 및 새로 추가된 글  |  표·배경·쪽 배치는 한/글 출력 그대로'
    d = ImageDraw.Draw(im)
    d.text((42,28),title,font=font(42,True),fill=INK)
    d.text((42,94),'보고서 예시 파일(한번에 적용).txt · '+record['app_version']+' 실제 실행 · 원본 사본 사용',font=font(25),fill=GRAY)
    d.text((42,im.height-120),note,font=font(27,True),fill=RED)
    d.text((42,im.height-66),f"실제 쪽 수 {record['pages']['before']} → {record['pages']['after']}쪽 · 빨간색은 이미지 비교용이며 결과 HWPX에 넣지 않음",font=font(25),fill=GRAY)
    path = output / ('spacing.png' if mode == 'spacing' else 'all-in-one.png')
    im.save(path, optimize=True)
    return dict(image=path.name, changed_glyphs={'before':len(left),'after':len(right)}, focus_words=words,
                pdf_pages={'before':len(a),'after':len(b)}, image_sha256=digest(path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_dir', type=Path)
    parser.add_argument('--app-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--work', type=Path, required=True, help='비어 있는 새 로컬 실행 폴더')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--render-only', action='store_true')
    args = parser.parse_args()
    source_dir = args.source_dir.resolve(strict=True)
    app_root = args.app_root.resolve(strict=True)
    sys.path.insert(0, str(app_root))
    source = source_dir / '보고서 예시 파일(한번에 적용).txt'
    originals = {p.name:digest(p) for p in source_dir.iterdir() if p.is_file()}
    if not args.render_only:
        args.work.mkdir(parents=True, exist_ok=False)
    args.output.mkdir(parents=True, exist_ok=True)
    evidence = {'kind':'test4 원문 사본의 실제 앱 실행·한/글 PDF 렌더링; UI 녹화 아님',
                'source_files':originals,'app_code_sha256':digest(app_root/'hwp-auto-docfit.py'),'runs':{}}
    for mode in ('all','spacing'):
        folder = args.work / mode
        record = json.loads((folder/'run.json').read_text(encoding='utf-8')) if args.render_only else process(app_root, source, folder, mode)
        record['comparison'] = render(folder,args.output,mode,record)
        evidence['runs'][mode] = record
        assert originals == {p.name:digest(p) for p in source_dir.iterdir() if p.is_file()}, '원본 파일 변경'
        evidence['originals_unchanged'] = True
        (args.output/'test4-evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
        print('RENDERED '+mode,flush=True)


if __name__ == '__main__':
    main()
