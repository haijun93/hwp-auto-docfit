"""글꼴 탐색·설정·진행·범위 공통 포트 — formatter의 호환 전역으로 바인딩할 원본 정의."""

SYMBOLS = ('_hwp_설치폴더_후보_레지스트리', '_hwp_설치폴더_후보_공통경로', '한글_폰트_폴더_자동감지', '_ttf_패밀리이름', '한글_폰트_목록', '한컴_번들_폰트_폴더_목록', '한글_폰트_목록_전체', '서식_기본값_전역_복원', '프로그램_폴더', '번들_리소스_폴더', '_hwpx_안전_저장', '설정_폴더', '서식프로파일_폴더', '서식예시_정보_폴더', '서식예시_폴더', '첫쪽_그림_만들기', '번들_서식예시_찾기', '_json_파일_읽기', '서식예시_서명', '설정_파일_경로', '설정_불러오기', '설정_저장', '진행률', '단계시간_시작', '_단계시간_닫기', '단계시간_구간', '단계시간_끝', '단계시간_분류', '단계시간_요약줄', '단계초기화', '중단_요청됨', '_문서_편집_시도', 'hwp_run', '_문두보호_줄건너뜀', '번들_상용구_파일_찾기', '글자상용구_폴더', '본문상용구_폴더', '번들_본문상용구_폴더', '상용구_폴더_준비', '상용구_전용폴더_찾기', '텍스트_삽입', '끝위치추출', '다음_문단으로_진행', '쪽표시', '절약시간_표시', '절약시간_분초_표시', '번들_고양이_그림_찾기', '번들_앱아이콘_찾기', '_앱아이콘_적용', '처리_쪽수_구하기', '쪽범위_사용중', '쪽범위_안인가', '쪽범위_끝지남', '순회_시작', '범위_다음_문단으로_진행', '현재_표셀인가', '숫자_표칸인가', '저장파일명', '바이너리_HWP_파일인가', '텍스트파일_읽기')

def _install(*, _docfit_namespace, _docfit_symbol, bind_function):
    global _hwp_설치폴더_후보_레지스트리, _hwp_설치폴더_후보_공통경로, 한글_폰트_폴더_자동감지, _ttf_패밀리이름, 한글_폰트_목록, 한컴_번들_폰트_폴더_목록, 한글_폰트_목록_전체, 서식_기본값_전역_복원, 프로그램_폴더, 번들_리소스_폴더, _hwpx_안전_저장, 설정_폴더, 서식프로파일_폴더, 서식예시_정보_폴더, 서식예시_폴더, 첫쪽_그림_만들기, 번들_서식예시_찾기, _json_파일_읽기, 서식예시_서명, 설정_파일_경로, 설정_불러오기, 설정_저장, 진행률, 단계시간_시작, _단계시간_닫기, 단계시간_구간, 단계시간_끝, 단계시간_분류, 단계시간_요약줄, 단계초기화, 중단_요청됨, _문서_편집_시도, hwp_run, _문두보호_줄건너뜀, 번들_상용구_파일_찾기, 글자상용구_폴더, 본문상용구_폴더, 번들_본문상용구_폴더, 상용구_폴더_준비, 상용구_전용폴더_찾기, 텍스트_삽입, 끝위치추출, 다음_문단으로_진행, 쪽표시, 절약시간_표시, 절약시간_분초_표시, 번들_고양이_그림_찾기, 번들_앱아이콘_찾기, _앱아이콘_적용, 처리_쪽수_구하기, 쪽범위_사용중, 쪽범위_안인가, 쪽범위_끝지남, 순회_시작, 범위_다음_문단으로_진행, 현재_표셀인가, 숫자_표칸인가, 저장파일명, 바이너리_HWP_파일인가, 텍스트파일_읽기
    if _docfit_symbol == '_hwp_설치폴더_후보_레지스트리':
        def _hwp_설치폴더_후보_레지스트리():
            """레지스트리에서 한/글(HWP) 설치 경로를 찾아본다. 버전별로 키 이름이 달라
            여러 후보를 시도하고, 실패해도 예외를 삼켜 폰트 자동감지 실패로만 남긴다."""
            후보 = []
            키목록 = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Hnc\HwpFrame"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Hnc\HwpFrame"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Hnc\Hwp"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Hnc\Hwp"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Hnc\HwpFrame"),
            ]
            값이름목록 = ["InstallPath", "Path", "InstallDir", "ProgramDir", ""]
            for 루트, 경로 in 키목록:
                try:
                    with winreg.OpenKey(루트, 경로, 0, winreg.KEY_READ) as key:
                        for 값이름 in 값이름목록:
                            try:
                                값, _ = winreg.QueryValueEx(key, 값이름)
                                if 값:
                                    후보.append(Path(str(값)))
                            except OSError:
                                continue
                except OSError:
                    continue
            return 후보
        return bind_function(_hwp_설치폴더_후보_레지스트리, _docfit_namespace)
    if _docfit_symbol == '_hwp_설치폴더_후보_공통경로':
        def _hwp_설치폴더_후보_공통경로():
            후보 = []
            for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles"),
                         os.environ.get("ProgramW6432")):
                if not base:
                    continue
                for vendor in ("Hnc", "HancomOffice", "Hancom", "한컴오피스"):
                    root = Path(base) / vendor
                    if root.exists():
                        후보.append(root)
            return 후보
        return bind_function(_hwp_설치폴더_후보_공통경로, _docfit_namespace)
    if _docfit_symbol == '한글_폰트_폴더_자동감지':
        def 한글_폰트_폴더_자동감지():
            """글꼴 폴더를 추정한다.

            1) 기본 폴더는 윈도우 글꼴 폴더("C:\\Windows\\Fonts")다.
            2) 없으면 한/글 전용 글꼴 경로("C:\\Program Files (x86)\\Hnc\\Office 2020\\
               HOffice110\\Shared\\Fonts")를 확인한다.
            3) 그래도 없으면 "C:\\Program Files (x86)" 또는 "C:\\Program Files"에서
               "Hnc" 폴더를 찾고, 그 하위 폴더들 중에서 "Fonts" 폴더를 찾는다.
            4) 그래도 못 찾으면 레지스트리 등 다른 후보로 보조 탐색한다.
            못 찾으면 빈 문자열을 반환하고, 사용자가 설정창에서 직접 찾아보기로 지정하면 된다.
            """
            def _폰트파일_있음(폴더):
                try:
                    return any(p.suffix.lower() in (".ttf", ".ttc", ".otf", ".hft")
                               for p in 폴더.iterdir() if p.is_file())
                except (OSError, PermissionError):
                    return False

            윈도우폰트경로 = Path(r"C:\Windows\Fonts")
            try:
                if 윈도우폰트경로.is_dir() and _폰트파일_있음(윈도우폰트경로):
                    return str(윈도우폰트경로)
            except OSError:
                pass

            기본경로 = Path(r"C:\Program Files (x86)\Hnc\Office 2020\HOffice110\Shared\Fonts")
            try:
                if 기본경로.is_dir() and _폰트파일_있음(기본경로):
                    return str(기본경로)
            except OSError:
                pass

            for 상위 in (r"C:\Program Files (x86)", r"C:\Program Files"):
                상위경로 = Path(상위)
                try:
                    if not 상위경로.is_dir():
                        continue
                    항목들 = list(상위경로.iterdir())
                except (OSError, PermissionError):
                    continue
                for 항목 in 항목들:
                    try:
                        if not 항목.is_dir() or 항목.name.lower() != "hnc":
                            continue
                        for 하위 in 항목.rglob("*"):
                            if 하위.is_dir() and 하위.name.lower() == "fonts" and _폰트파일_있음(하위):
                                return str(하위)
                    except (OSError, PermissionError):
                        continue

            # 보조 탐색: 레지스트리에 기록된 설치 경로 등 다른 후보도 확인한다.
            시작폴더들 = list(_hwp_설치폴더_후보_레지스트리()) + list(_hwp_설치폴더_후보_공통경로())
            검사한 = set()
            for 시작 in 시작폴더들:
                try:
                    if not 시작.exists() or 시작 in 검사한:
                        continue
                    검사한.add(시작)
                except OSError:
                    continue
                try:
                    for 하위 in 시작.rglob("*"):
                        if 하위.is_dir() and 하위.name.lower() in ("font", "fonts", "hwpfont", "hncfont"):
                            if _폰트파일_있음(하위):
                                return str(하위)
                except (OSError, PermissionError):
                    continue
            return ""
        return bind_function(한글_폰트_폴더_자동감지, _docfit_namespace)
    if _docfit_symbol == '_ttf_패밀리이름':
        def _ttf_패밀리이름(path):
            """TTF/TTC/OTF의 name 테이블에서 패밀리명을 읽는다(외부 라이브러리 없이
            직접 파싱). 한국어(langID 0x0412) 항목을 최우선으로 쓰고, 실패하면 None."""
            try:
                with open(path, "rb") as f:
                    data = f.read(1024 * 1024)  # name 테이블은 보통 파일 앞부분에 있음
                if len(data) < 12:
                    return None
                if data[:4] == b"ttcf":
                    오프셋 = struct.unpack(">I", data[12:16])[0]
                else:
                    오프셋 = 0
                표개수 = struct.unpack(">H", data[오프셋 + 4:오프셋 + 6])[0]
                name_오프셋 = None
                for i in range(표개수):
                    레코드 = data[오프셋 + 12 + i * 16: 오프셋 + 12 + (i + 1) * 16]
                    if len(레코드) < 16:
                        break
                    if 레코드[0:4] == b"name":
                        name_오프셋 = struct.unpack(">I", 레코드[8:12])[0]
                        break
                if name_오프셋 is None:
                    return None
                _, 레코드수, 문자열오프셋 = struct.unpack(">HHH", data[name_오프셋:name_오프셋 + 6])
                최선 = {}
                for i in range(레코드수):
                    위치 = name_오프셋 + 6 + i * 12
                    if 위치 + 12 > len(data):
                        break
                    플랫폼, 인코딩, 언어, 이름ID, 길이, 문자열위치 = struct.unpack(">HHHHHH", data[위치:위치 + 12])
                    if 이름ID not in (1, 4, 16):
                        continue
                    시작 = name_오프셋 + 문자열오프셋 + 문자열위치
                    raw = data[시작:시작 + 길이]
                    if not raw:
                        continue
                    try:
                        if 플랫폼 == 1:
                            텍스트 = raw.decode("mac_roman", errors="ignore")
                        else:
                            텍스트 = raw.decode("utf-16-be", errors="ignore")
                    except Exception:
                        continue
                    텍스트 = 텍스트.strip()
                    if not 텍스트:
                        continue
                    우선순위 = 10 if 이름ID == 16 else 0
                    if 플랫폼 == 3 and 언어 == 0x0412:
                        우선순위 += 3
                    elif 플랫폼 == 3 and 언어 == 0x0409:
                        우선순위 += 2
                    else:
                        우선순위 += 1
                    if 이름ID not in 최선 or 최선[이름ID][0] < 우선순위:
                        최선[이름ID] = (우선순위, 텍스트)
                for nid in (16, 1, 4):
                    if nid in 최선:
                        return 최선[nid][1]
                return None
            except Exception:
                return None
        return bind_function(_ttf_패밀리이름, _docfit_namespace)
    if _docfit_symbol == '한글_폰트_목록':
        def 한글_폰트_목록(폴더):
            """지정한 폴더(보통 한/글 폰트 폴더) 안의 ttf/ttc/otf/hft에서 패밀리명을 모은다.

            hft는 한컴오피스 전용 번들 글꼴 컨테이너 형식으로, 표준 sfnt name 테이블
            파싱이 통하지 않는 경우가 많아 그때는 파일명(확장자 제외)을 글꼴 이름으로
            쓴다. 한/글은 이 이름으로 내부 번들 글꼴을 인식해 적용할 수 있다."""
            결과 = []
            if not 폴더:
                return 결과
            try:
                경로 = Path(폴더)
                if not 경로.is_dir():
                    return 결과
                본적있음 = set()
                for p in sorted(경로.rglob("*")):
                    if not p.is_file() or p.suffix.lower() not in (".ttf", ".ttc", ".otf", ".hft"):
                        continue
                    이름 = _ttf_패밀리이름(p) or p.stem
                    if 이름 and 이름 not in 본적있음:
                        본적있음.add(이름)
                        결과.append(이름)
                결과.sort(key=lambda s: (0 if re.match(r'^[A-Za-z]', s) else 1, s))
            except (OSError, PermissionError):
                pass
            return 결과
        return bind_function(한글_폰트_목록, _docfit_namespace)
    if _docfit_symbol == '한컴_번들_폰트_폴더_목록':
        def 한컴_번들_폰트_폴더_목록():
            """설치 경로 후보들 아래에서 .hft(한컴오피스 전용 번들 글꼴) 파일이 있는
            폴더를 모두 찾는다. 폴더 이름이 'Fonts'가 아니어도 실제 .hft 파일 위치를
            직접 뒤져서 찾으므로, 배포판마다 다른 폴더 이름에 흔들리지 않는다."""
            폴더집합 = set()
            후보들 = list(_hwp_설치폴더_후보_레지스트리()) + list(_hwp_설치폴더_후보_공통경로())
            후보들.append(Path(r"C:\Program Files (x86)\Hnc\Office 2020\HOffice110\Shared\Fonts"))
            검사한 = set()
            for 시작 in 후보들:
                try:
                    if not 시작.exists() or 시작 in 검사한:
                        continue
                    검사한.add(시작)
                except OSError:
                    continue
                try:
                    for hft파일 in 시작.rglob("*.hft"):
                        폴더집합.add(hft파일.parent)
                except (OSError, PermissionError):
                    continue
            return sorted(폴더집합, key=str)
        return bind_function(한컴_번들_폰트_폴더_목록, _docfit_namespace)
    if _docfit_symbol == '한글_폰트_목록_전체':
        def 한글_폰트_목록_전체(폴더):
            """사용자가 지정한 글꼴 폴더 목록에, 자동으로 찾은 한컴오피스 전용
            번들(HFT) 글꼴 폴더의 글꼴을 더해 합친 전체 글꼴 이름 목록을 돌려준다."""
            결과 = list(한글_폰트_목록(폴더))
            본적있음 = set(결과)
            폴더_문자열 = str(Path(폴더)) if 폴더 else ""
            for 번들폴더 in 한컴_번들_폰트_폴더_목록():
                if str(번들폴더) == 폴더_문자열:
                    continue
                for 이름 in 한글_폰트_목록(str(번들폴더)):
                    if 이름 not in 본적있음:
                        본적있음.add(이름)
                        결과.append(이름)
            결과.sort(key=lambda s: (0 if re.match(r'^[A-Za-z]', s) else 1, s))
            return 결과
        return bind_function(한글_폰트_목록_전체, _docfit_namespace)
    if _docfit_symbol == '서식_기본값_전역_복원':
        def 서식_기본값_전역_복원():
            global 표준서식_설정
            global 표_헤더서식_헤더_폰트, 표_헤더서식_헤더_크기, 표_헤더서식_헤더_굵게
            global 표_헤더서식_본문_폰트, 표_헤더서식_본문_크기, 표_헤더서식_본문_굵게
            global 표준서식_문단위간격_box_pt, 표준서식_문단위간격_circle_pt, 표준서식_문단위간격_note_pt
            global 표준서식_문단위간격_dash_pt
            global 표준서식_문단위간격_chapter_pt, 표준서식_문단위간격_midtitle_pt
            global 표준서식_문단위간격_복귀배율
            global 활성_정밀표_프로필, 활성_서식표_프로필, 활성_표서식_프로필

            표준서식_설정 = copy.deepcopy(_표준서식_설정_기본값)
            표_헤더서식_헤더_폰트 = _표_헤더서식_기본값["헤더_폰트"]
            표_헤더서식_헤더_크기 = _표_헤더서식_기본값["헤더_크기"]
            표_헤더서식_헤더_굵게 = _표_헤더서식_기본값["헤더_굵게"]
            표_헤더서식_본문_폰트 = _표_헤더서식_기본값["본문_폰트"]
            표_헤더서식_본문_크기 = _표_헤더서식_기본값["본문_크기"]
            표_헤더서식_본문_굵게 = _표_헤더서식_기본값["본문_굵게"]
            표준서식_문단위간격_chapter_pt = _표준서식_문단위간격_기본값["chapter"]
            표준서식_문단위간격_midtitle_pt = _표준서식_문단위간격_기본값["midtitle"]
            표준서식_문단위간격_box_pt = _표준서식_문단위간격_기본값["box"]
            표준서식_문단위간격_circle_pt = _표준서식_문단위간격_기본값["circle"]
            표준서식_문단위간격_dash_pt = _표준서식_문단위간격_기본값["dash"]
            표준서식_문단위간격_note_pt = _표준서식_문단위간격_기본값["note"]
            표준서식_문단위간격_복귀배율 = 150
            _표준서식_문단위간격_상태.reset()
            활성_정밀표_프로필 = None
            활성_서식표_프로필 = None
            활성_표서식_프로필 = None
            globals()["활성_머리서식_프로필"] = None
            globals()["괄호_축소_pt"] = 2
        return bind_function(서식_기본값_전역_복원, _docfit_namespace)
    if _docfit_symbol == '프로그램_폴더':
        def 프로그램_폴더():
            if getattr(sys, "frozen", False):
                return Path(sys.executable).resolve().parent
            return Path(__file__).resolve().parent
        return bind_function(프로그램_폴더, _docfit_namespace)
    if _docfit_symbol == '번들_리소스_폴더':
        def 번들_리소스_폴더():
            meipass = getattr(sys, "_MEIPASS", None)
            return Path(meipass) if meipass else None
        return bind_function(번들_리소스_폴더, _docfit_namespace)
    if _docfit_symbol == '_hwpx_안전_저장':
        def _hwpx_안전_저장(contents, target):
            """HWPX 항목을 임시 파일에 쓴 뒤 바꿔 넣는다(한/글이 잠시 파일을 잡고 있어도 재시도)."""
            임시 = Path(str(target) + '.tmp')
            with zipfile.ZipFile(임시, 'w', zipfile.ZIP_DEFLATED) as z:
                for name, data in contents.items():
                    z.writestr(name, data, compress_type=zipfile.ZIP_STORED if name == 'mimetype' else zipfile.ZIP_DEFLATED)
            for 시도 in range(20):
                try:
                    os.replace(임시, target)
                    return
                except PermissionError:
                    if 시도 == 19: raise
                    time.sleep(0.1)
        return bind_function(_hwpx_안전_저장, _docfit_namespace)
    if _docfit_symbol == '설정_폴더':
        def 설정_폴더():
            appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
            if appdata:
                return Path(appdata) / "HwpAutoDocFit"
            return Path.home() / ".hwp_auto_docfit"
        return bind_function(설정_폴더, _docfit_namespace)
    if _docfit_symbol == '서식프로파일_폴더':
        def 서식프로파일_폴더():
            return 설정_폴더() / "formats"
        return bind_function(서식프로파일_폴더, _docfit_namespace)
    if _docfit_symbol == '서식예시_정보_폴더':
        def 서식예시_정보_폴더():
            """서식 예시의 정보(해시·만든 때)와 비교 기준이 되는 원본 사본을 두는 설정 폴더."""
            return 설정_폴더() / "format_examples"
        return bind_function(서식예시_정보_폴더, _docfit_namespace)
    if _docfit_symbol == '서식예시_폴더':
        def 서식예시_폴더():
            """서식마다 예시 HWPX를 두는 폴더. 알파: 사용자가 직접 고칠 수 있는 C:\\HWP_AUTODOCFIT\\서식예시."""
            if 알파_서식예시폴더_사용:
                return 서식예시모듈.sample_folder(HWP_AUTOMATION_DIR)
            return 서식예시_정보_폴더()
        return bind_function(서식예시_폴더, _docfit_namespace)
    if _docfit_symbol == '첫쪽_그림_만들기':
        def 첫쪽_그림_만들기(hwpx, png, 해상도=100):
            """예시 HWPX의 사본을 독립 한/글로 열어 첫 쪽을 PNG로 저장한다(미리보기 그림이 없는 예시의 썸네일용, 2026-10-11).

            한/글 2018 등으로 저장한 HWPX는 Preview/PrvImage.png가 없다. 원본·예시 파일은 열지 않고 임시 사본만 연다.
            성공하면 True, 실패하면 예외."""
            with tempfile.TemporaryDirectory(prefix="docfit_thumb_") as folder:
                사본 = Path(folder) / "sample.hwpx"
                그림 = Path(folder) / "page.png"
                shutil.copyfile(hwpx, 사본)
                app = None
                pythoncom.CoInitialize()
                try:
                    보안모듈_초기화()
                    app = 한글_COM_인스턴스_생성(독립=True)
                    try:
                        app.XHwpWindows.Item(0).Visible = False
                    except Exception:
                        pass
                    if not app.RegisterModule(REGISTER_MODULE_NAME, REGISTER_MODULE_VALUE):
                        raise RuntimeError("한글 보안 모듈을 등록하지 못했습니다.")
                    if not 한글_문서_열기(app, 사본, "HWPX", "forceopen:true"):
                        raise RuntimeError("예시 문서를 열지 못했습니다.")
                    # 쪽 번호는 0부터(첫 쪽 = 0). 한/글 2020은 형식을 png로 줘도 확장자를 .bmp로 바꿔 BMP로 저장한다(2026-10-11 실측).
                    app.CreatePageImage(str(그림), 0, int(해상도), 24, "png")
                    만든것 = 그림 if 그림.is_file() else next(iter(sorted(Path(folder).glob("page.*"))), None)
                    if 만든것 is None:
                        raise RuntimeError("첫 쪽 그림을 만들지 못했습니다.")
                    from PIL import Image
                    image = Image.open(만든것).convert("RGB")
                    image.thumbnail((724, 1024))
                    Path(png).parent.mkdir(parents=True, exist_ok=True)
                    image.save(png)
                    return True
                finally:
                    if app is not None:
                        try:
                            app.Clear(1)
                        except Exception:
                            pass
                        try:
                            app.Quit()
                        except Exception:
                            pass
                    pythoncom.CoUninitialize()
        return bind_function(첫쪽_그림_만들기, _docfit_namespace)
    if _docfit_symbol == '번들_서식예시_찾기':
        def 번들_서식예시_찾기():
            """앱에 포함해 배포하는 기본 서식 예시(resources/서식예시/기본 서식.hwpx). 없으면 None."""
            후보_목록 = [프로그램_폴더() / "resources" / "서식예시" / 서식예시모듈.STANDARD_FILE]
            번들_폴더 = 번들_리소스_폴더()
            if 번들_폴더 is not None:
                후보_목록.append(번들_폴더 / "resources" / "서식예시" / 서식예시모듈.STANDARD_FILE)
            return next((경로 for 경로 in 후보_목록 if 경로.is_file()), None)
        return bind_function(번들_서식예시_찾기, _docfit_namespace)
    if _docfit_symbol == '_json_파일_읽기':
        def _json_파일_읽기(경로):
            try:
                return json.loads(Path(경로).read_text(encoding="utf-8")) if Path(경로).is_file() else {}
            except Exception:
                return {}
        return bind_function(_json_파일_읽기, _docfit_namespace)
    if _docfit_symbol == '서식예시_서명':
        def 서식예시_서명(profile):
            """보관한 서식 예시가 지금 서식 값·예시 글·앱 판으로 만든 것인지 가려내는 값(다르면 예시를 새로 만든다)."""
            재료 = json.dumps({"서식": profile or {}, "글": 서식예시_글, "앱판": APP_VERSION, "작업": 서식예시_작업모드},
                            ensure_ascii=False, sort_keys=True, default=str)
            return hashlib.sha256(재료.encode("utf-8")).hexdigest()
        return bind_function(서식예시_서명, _docfit_namespace)
    if _docfit_symbol == '설정_파일_경로':
        def 설정_파일_경로():
            return 설정_폴더() / 설정_파일명
        return bind_function(설정_파일_경로, _docfit_namespace)
    if _docfit_symbol == '설정_불러오기':
        def 설정_불러오기():
            설정 = dict(기본_설정)
            try:
                경로 = 설정_파일_경로()
                if not 경로.is_file():
                    return 설정
                with open(경로, "r", encoding="utf-8") as f:
                    저장된값 = json.load(f)
                if isinstance(저장된값, dict):
                    for 키 in 기본_설정:
                        if 키 in 저장된값:
                            설정[키] = 저장된값[키]
                    if isinstance(저장된값.get("stage_choices"), dict):
                        설정["stage_choices"] = 저장된값["stage_choices"]
                    설정["abbreviations"] = 준말_등록표_정리(저장된값.get("abbreviations"))
                    설정["abbreviation_defaults"] = bool(저장된값.get("abbreviation_defaults", True))
                    from docfit_app.settings_migrations import migrate
                    migrated = migrate(저장된값)
                    for key in 기본_설정:
                        if key not in ('abbreviations', 'abbreviation_defaults') and key in migrated:
                            설정[key] = migrated[key]
            except Exception as e:
                if _콘솔_출력_가능:
                    print(f"설정 불러오기 실패(기본값 사용): {e}")
            return 설정
        return bind_function(설정_불러오기, _docfit_namespace)
    if _docfit_symbol == '설정_저장':
        def 설정_저장(설정):
            try:
                from docfit_app.settings_service import SettingsService
                SettingsService(설정_파일_경로).update(lambda current: current.update(설정))
                return True
            except Exception as e:
                로그(f"설정 저장 실패: {e}")
                return False
        return bind_function(설정_저장, _docfit_namespace)
    if _docfit_symbol == '진행률':
        def 진행률(value):
            gui_queue.put(("progress", int(max(0, min(100, value)))))
        return bind_function(진행률, _docfit_namespace)
    if _docfit_symbol == '단계시간_시작':
        def 단계시간_시작():
            global _단계시간표
            지금 = time.perf_counter()
            _단계시간표 = {'시작': 지금, '현재': '준비', '현재시작': 지금, '합': {}, '순서': [], '기록': []}
        return bind_function(단계시간_시작, _docfit_namespace)
    if _docfit_symbol == '_단계시간_닫기':
        def _단계시간_닫기(표, 지금):
            이름 = 표.get('현재')
            if 이름 is None:
                return
            누적 = 표['합'].get(이름)
            if 누적 is None:
                누적 = 표['합'][이름] = [0.0, 0]
                표['순서'].append(이름)
            소요 = 지금 - 표['현재시작']
            누적[0] += 소요
            누적[1] += 1
            표.setdefault('기록', []).append((이름, 소요))
            표['현재'] = None
        return bind_function(_단계시간_닫기, _docfit_namespace)
    if _docfit_symbol == '단계시간_구간':
        def 단계시간_구간(이름):
            """직전 구간을 닫고 이름 구간을 시작한다. 계측 중이 아니면 아무것도 하지 않는다."""
            표 = _단계시간표
            if 표 is None or not 이름:
                return
            지금 = time.perf_counter()
            _단계시간_닫기(표, 지금)
            표['현재'], 표['현재시작'] = 이름, 지금
        return bind_function(단계시간_구간, _docfit_namespace)
    if _docfit_symbol == '단계시간_끝':
        def 단계시간_끝():
            global _단계시간표
            표, _단계시간표 = _단계시간표, None
            if 표 is None:
                return None
            지금 = time.perf_counter()
            _단계시간_닫기(표, 지금)
            표['전체'] = 지금 - 표['시작']
            return 표
        return bind_function(단계시간_끝, _docfit_namespace)
    if _docfit_symbol == '단계시간_분류':
        def 단계시간_분류(이름):
            """단계 이름을 서식 / 내어쓰기 / 자간 / 쪽 맞춤 등 큰 분류로 묶는다(서식통일 안의 자간·쪽 맞춤은 서식통일에 포함)."""
            이름 = str(이름)
            if 이름 in ('준비', '열기', '변환') or '열기' in 이름 or '변환' in 이름:
                return '열기·변환'
            if '페이지' in 이름 or '쪽' in 이름:
                return '쪽 맞춤·배치'
            if '내어쓰기' in 이름 or '들여쓰기' in 이름 or '별표' in 이름:
                return '내어쓰기 계열'
            if '자간' in 이름 or '단어' in 이름 or '줄 병합' in 이름 or '마지막 줄' in 이름:
                return '자간·줄 끝'
            if '저장' in 이름 or '검수' in 이름 or '무결성' in 이름 or '규칙' in 이름:
                return '저장·검수'
            return '서식·기타'
        return bind_function(단계시간_분류, _docfit_namespace)
    if _docfit_symbol == '단계시간_요약줄':
        def 단계시간_요약줄(표, 파일명, 상위=10):
            """계측 결과를 로그 줄 목록으로 만든다(순수 함수)."""
            전체 = max(표.get('전체', 0.0), 1e-9)
            분류합 = {}
            for 이름, (초, _건) in 표['합'].items():
                분류합[단계시간_분류(이름)] = 분류합.get(단계시간_분류(이름), 0.0) + 초
            줄 = [f"[처리 시간 계측] {파일명}: 전체 {전체:.1f}초 (단계 {len(표['합'])}종)"]
            줄.append("[처리 시간 계측] 분류별: " + " / ".join(
                f"{이름} {초:.1f}초({초 / 전체:.0%})" for 이름, 초 in sorted(분류합.items(), key=lambda x: -x[1])))
            오래 = sorted(표['합'].items(), key=lambda x: -x[1][0])[:상위]
            줄.append("[처리 시간 계측] 오래 걸린 단계(상위 %d): " % len(오래) + " / ".join(
                f"{이름} {초:.1f}초({초 / 전체:.0%}, {건}회)" for 이름, (초, 건) in 오래))
            기록 = 표.get('기록') or [(이름, 표['합'][이름][0]) for 이름 in 표.get('순서', [])]
            줄.append("[처리 시간 단계별] " + " -> ".join(
                f"{번호:02d} {이름} {초:.2f}초" for 번호, (이름, 초) in enumerate(기록, 1)))
            return 줄
        return bind_function(단계시간_요약줄, _docfit_namespace)
    if _docfit_symbol == '단계초기화':
        def 단계초기화():
            gui_queue.put(("step_reset", None))
        return bind_function(단계초기화, _docfit_namespace)
    if _docfit_symbol == '중단_요청됨':
        def 중단_요청됨():
            return 중단_event.is_set()
        return bind_function(중단_요청됨, _docfit_namespace)
    if _docfit_symbol == '_문서_편집_시도':
        def _문서_편집_시도():
            global _문서_편집_세대
            _문서_편집_세대 += 1
        return bind_function(_문서_편집_시도, _docfit_namespace)
    if _docfit_symbol == 'hwp_run':
        def hwp_run(command):
            if hwp is None:
                raise RuntimeError("HWP 객체가 없습니다.")
            if not (str(command).startswith("Move") or command in ("Cancel", "Select", "SelectAll")):
                _문서_편집_시도()
            try:
                if command in ('CharShapeSpacingDecrease', 'CharShapeSpacingIncrease',
                               'CharShapeRatioDecrease', 'CharShapeRatioIncrease'):
                    # 이 명령들은 화면줄 선택을 사용하는 기존 자간/줄 병합 경로다.
                    # 문두 라벨만 있는 줄에는 조정을 실행하지 않는다.
                    if not 자간조정_현재줄_본문선택():
                        raise 문두보호_조정불가('문두 보호: 이 화면줄에 조정 가능한 본문이 없습니다')
                return hwp.Run(command)
            except 문두보호_조정불가:
                raise
            except Exception as e:
                로그(f"HWP 명령 실패: {command} / {e}")
                raise
        return bind_function(hwp_run, _docfit_namespace)
    if _docfit_symbol == '_문두보호_줄건너뜀':
        def _문두보호_줄건너뜀(함수, *args, **kwargs):
            """줄 단위 자간·줄 병합 함수를 부르고, 조정할 본문이 없는 줄이면 그 줄만 건너뛴다(True)."""
            try:
                return 함수(*args, **kwargs)
            except 문두보호_조정불가:
                try:
                    hwp.Run("Cancel")
                    줄 = 현재_화면줄_텍스트().strip()[:40]
                except Exception:
                    줄 = ""
                진단로그(f"[문두 보호] 조정할 본문이 없는 줄 건너뜀: {줄}")
                return True
        return bind_function(_문두보호_줄건너뜀, _docfit_namespace)
    if _docfit_symbol == '번들_상용구_파일_찾기':
        def 번들_상용구_파일_찾기():
            """앱에 포함해 배포하는 상용구 파일(resources/HWP.IDO)의 실제 경로를 찾는다."""
            후보_목록 = [프로그램_폴더() / "resources" / 상용구_파일명]
            번들_폴더 = 번들_리소스_폴더()
            if 번들_폴더 is not None:
                후보_목록.append(번들_폴더 / "resources" / 상용구_파일명)
            for 경로 in 후보_목록:
                if 경로.is_file():
                    return 경로
            return None
        return bind_function(번들_상용구_파일_찾기, _docfit_namespace)
    if _docfit_symbol == '글자상용구_폴더':
        def 글자상용구_폴더():
            """앱 폴더의 글자 상용구(HWP.IDO) 보관 폴더(알파). 끄면 None."""
            return 서식예시모듈.app_subfolder(서식예시모듈.CHAR_IDIOM_FOLDER_NAME, HWP_AUTOMATION_DIR) if 알파_서식예시폴더_사용 else None
        return bind_function(글자상용구_폴더, _docfit_namespace)
    if _docfit_symbol == '본문상용구_폴더':
        def 본문상용구_폴더():
            """앱 폴더의 본문 상용구(한/글 IDIOM 폴더의 *.HWP) 보관 폴더(알파). 끄면 None."""
            return 서식예시모듈.app_subfolder(서식예시모듈.BODY_IDIOM_FOLDER_NAME, HWP_AUTOMATION_DIR) if 알파_서식예시폴더_사용 else None
        return bind_function(본문상용구_폴더, _docfit_namespace)
    if _docfit_symbol == '번들_본문상용구_폴더':
        def 번들_본문상용구_폴더():
            """앱에 포함해 배포하는 본문 상용구 폴더(resources/IDIOM). 없으면 None."""
            후보_목록 = [프로그램_폴더() / "resources" / "IDIOM"]
            번들_폴더 = 번들_리소스_폴더()
            if 번들_폴더 is not None:
                후보_목록.append(번들_폴더 / "resources" / "IDIOM")
            return next((경로 for 경로 in 후보_목록 if 경로.is_dir()), None)
        return bind_function(번들_본문상용구_폴더, _docfit_namespace)
    if _docfit_symbol == '상용구_폴더_준비':
        def 상용구_폴더_준비():
            """상용구 HWPX 설정 파일을 준비한다(사용자 파일은 절대 덮어쓰지 않음).

            한/글 호환용 HWP.IDO/IDIOM 사본도 기존 사용자를 위해 유지한다.
            새 설정의 원본은 각각 글자상용구.hwpx와 본문상용구.hwpx다.
            """
            글자, 본문 = 글자상용구_폴더(), 본문상용구_폴더()
            if 글자 is None:
                return
            글자.mkdir(parents=True, exist_ok=True)
            본문.mkdir(parents=True, exist_ok=True)
            try:
                from docfit_core.hwpx_idioms import create_default_configs
                기본문서_후보 = [프로그램_폴더() / "resources" / "서식예시" / "기본 서식.hwpx"]
                번들_폴더 = 번들_리소스_폴더()
                if 번들_폴더 is not None:
                    기본문서_후보.append(번들_폴더 / "resources" / "서식예시" / "기본 서식.hwpx")
                기본문서 = next((후보 for 후보 in 기본문서_후보 if 후보.is_file()), None)
                if 기본문서 is not None:
                    create_default_configs(HWP_AUTOMATION_DIR, 기본문서)
            except Exception as e:
                로그(f"상용구 HWPX 기본 파일 준비 실패(기존 상용구는 유지): {e}")
            번들 = 번들_상용구_파일_찾기()
            if 번들 is not None and not (글자 / 상용구_파일명).is_file():
                shutil.copyfile(번들, 글자 / 상용구_파일명)
            번들_본문 = 번들_본문상용구_폴더()
            if 번들_본문 is not None:
                for 파일 in 번들_본문.iterdir():
                    if 파일.is_file() and not (본문 / 파일.name).exists():
                        shutil.copyfile(파일, 본문 / 파일.name)
        return bind_function(상용구_폴더_준비, _docfit_namespace)
    if _docfit_symbol == '상용구_전용폴더_찾기':
        def 상용구_전용폴더_찾기():
            """HWP.IDO를 저장해야 할 한/글 버전별 전용 폴더를 찾는다.

            %AppData%\\HNC\\User\\Hwp\\ 아래에 한/글 버전마다 고유 숫자 폴더가
            있다(한/글 2020 = 60). 이미 HWP.IDO가 있는 폴더를 최우선으로 고르고,
            없으면 폴더 이름 숫자가 가장 큰(최신 버전으로 추정되는) 폴더를 고른다.
            AppData 폴더는 숨김 처리돼 있어 탐색기에서 '숨긴 항목'을 켜야 보인다.
            """
            appdata = os.environ.get("APPDATA")
            if not appdata:
                return None
            기준_폴더 = Path(appdata) / "HNC" / "User" / "Hwp"
            if not 기준_폴더.is_dir():
                return None
            후보_폴더들 = [경로 for 경로 in 기준_폴더.iterdir() if 경로.is_dir() and 경로.name.isdigit()]
            if not 후보_폴더들:
                return None
            기존_상용구_폴더들 = [경로 for 경로 in 후보_폴더들 if (경로 / 상용구_파일명).is_file()]
            if 기존_상용구_폴더들:
                return max(기존_상용구_폴더들, key=lambda p: int(p.name))
            return max(후보_폴더들, key=lambda p: int(p.name))
        return bind_function(상용구_전용폴더_찾기, _docfit_namespace)
    if _docfit_symbol == '텍스트_삽입':
        def 텍스트_삽입(text):
            if not text or hwp is None:
                return
            _문서_편집_시도()
            try:
                act = hwp.HAction
                pset = hwp.HParameterSet.HInsertText
                act.GetDefault("InsertText", pset.HSet)
                pset.Text = text
                act.Execute("InsertText", pset.HSet)
            except Exception as e:
                로그(f"텍스트 삽입 실패(무시): {e}")
        return bind_function(텍스트_삽입, _docfit_namespace)
    if _docfit_symbol == '끝위치추출':
        def 끝위치추출():
            hwp_run("MoveDocEnd")
            end_pos = hwp.GetPos()
            hwp_run("MoveDocBegin")
            return end_pos
        return bind_function(끝위치추출, _docfit_namespace)
    if _docfit_symbol == '다음_문단으로_진행':
        def 다음_문단으로_진행():
            """현재 문단을 벗어나 다음 위치로 이동한다.

            문서 내용이 처리 중 삽입/삭제되어도 미리 저장한 문서 끝 좌표에 의존하지 않는다.
            더 이상 이동할 수 없으면 False를 반환한다.
            """
            hwp_run("MoveParaEnd")
            문단끝 = hwp.GetPos()
            hwp_run("MoveNextChar")
            다음위치 = hwp.GetPos()
            return 다음위치 != 문단끝
        return bind_function(다음_문단으로_진행, _docfit_namespace)
    if _docfit_symbol == '쪽표시':
        def 쪽표시(n):
            """쪽 번호 표시. 0(또는 None)은 '마지막쪽'."""
            return "마지막쪽" if not n else f"{n}쪽"
        return bind_function(쪽표시, _docfit_namespace)
    if _docfit_symbol == '절약시간_표시':
        def 절약시간_표시(분):
            """분(分)을 '약 45분', '약 1시간 20분' 꼴로 보여 준다."""
            분 = max(1, int(round(분)))
            if 분 < 60:
                return f"약 {분}분"
            시간, 나머지 = divmod(분, 60)
            return f"약 {시간}시간" + (f" {나머지}분" if 나머지 else "")
        return bind_function(절약시간_표시, _docfit_namespace)
    if _docfit_symbol == '절약시간_분초_표시':
        def 절약시간_분초_표시(초):
            """절약한 초를 '07분 05초' 꼴로 보여 준다(완료창 메시지용, 2026-10-11 사용자 요청)."""
            분, 초 = divmod(max(0, int(round(초))), 60)
            return f"{분:02d}분 {초:02d}초"
        return bind_function(절약시간_분초_표시, _docfit_namespace)
    if _docfit_symbol == '번들_고양이_그림_찾기':
        def 번들_고양이_그림_찾기():
            """완료창의 검은 고양이 그림(resources/black_cat.png, scripts/draw_black_cat.py로 그림). 없으면 None."""
            후보_목록 = [프로그램_폴더() / "resources" / "black_cat.png"]
            번들_폴더 = 번들_리소스_폴더()
            if 번들_폴더 is not None:
                후보_목록.append(번들_폴더 / "resources" / "black_cat.png")
            return next((경로 for 경로 in 후보_목록 if 경로.is_file()), None)
        return bind_function(번들_고양이_그림_찾기, _docfit_namespace)
    if _docfit_symbol == '번들_앱아이콘_찾기':
        def 번들_앱아이콘_찾기():
            """앱 아이콘(resources/app_icon.ico, scripts/make_app_icon.py로 고양이 그림에서 만듦). 없으면 None."""
            후보_목록 = [프로그램_폴더() / "resources" / "app_icon.ico"]
            번들_폴더 = 번들_리소스_폴더()
            if 번들_폴더 is not None:
                후보_목록.append(번들_폴더 / "resources" / "app_icon.ico")
            return next((경로 for 경로 in 후보_목록 if 경로.is_file()), None)
        return bind_function(번들_앱아이콘_찾기, _docfit_namespace)
    if _docfit_symbol == '_앱아이콘_적용':
        def _앱아이콘_적용(root):
            """Tk 기본창과 이후 새 창(Toplevel) 모두의 제목 표시줄 아이콘을 앱 아이콘으로 바꾼다."""
            아이콘 = 번들_앱아이콘_찾기()
            if 아이콘 is None:
                return
            try:
                root.iconbitmap(default=str(아이콘))
            except Exception:
                pass
        return bind_function(_앱아이콘_적용, _docfit_namespace)
    if _docfit_symbol == '처리_쪽수_구하기':
        def 처리_쪽수_구하기():
            """이번에 처리한 문서의 쪽 수(쪽 범위를 지정했으면 그 범위의 쪽 수). 알 수 없으면 1."""
            try:
                if 쪽범위_실제 is not None:
                    return max(1, 쪽범위_실제[1] - 쪽범위_실제[0] + 1)
                hwp_run("Cancel")
                hwp_run("MoveDocEnd")
                쪽 = 현재_페이지번호()
                hwp_run("MoveDocBegin")
                if 쪽:
                    return max(1, int(쪽))
            except Exception:
                pass
            return 1
        return bind_function(처리_쪽수_구하기, _docfit_namespace)
    if _docfit_symbol == '쪽범위_사용중':
        def 쪽범위_사용중():
            return 쪽범위_본문_문단 is not None
        return bind_function(쪽범위_사용중, _docfit_namespace)
    if _docfit_symbol == '쪽범위_안인가':
        def 쪽범위_안인가(pos=None):
            """위치가 작업 쪽 범위 안인지. 쪽 범위를 지정하지 않았으면 항상 True."""
            if 쪽범위_본문_문단 is None:
                return True
            if pos is None:
                pos = hwp.GetPos()
            if pos[0] == 0:
                return 쪽범위_본문_문단[0] <= pos[1] <= 쪽범위_본문_문단[1]
            return pos[0] in 쪽범위_컨트롤영역
        return bind_function(쪽범위_안인가, _docfit_namespace)
    if _docfit_symbol == '쪽범위_끝지남':
        def 쪽범위_끝지남(pos=None):
            """본문 순회 중 작업 쪽 범위의 마지막 문단을 지났는지."""
            if 쪽범위_본문_문단 is None:
                return False
            if pos is None:
                pos = hwp.GetPos()
            return pos[0] == 0 and pos[1] > 쪽범위_본문_문단[1]
        return bind_function(쪽범위_끝지남, _docfit_namespace)
    if _docfit_symbol == '순회_시작':
        def 순회_시작():
            """문서 순회를 시작 위치로 옮긴다. 쪽 범위가 있으면 범위의 첫 문단으로 간다."""
            hwp_run("MoveDocBegin")
            if 쪽범위_본문_문단 is not None:
                hwp.SetPos(0, 쪽범위_본문_문단[0], 0)
                현재 = hwp.GetPos()
                if 현재[0] != 0 or 현재[1] != 쪽범위_본문_문단[0]:
                    raise RuntimeError("작업 쪽 범위의 첫 문단으로 이동하지 못했습니다.")
        return bind_function(순회_시작, _docfit_namespace)
    if _docfit_symbol == '범위_다음_문단으로_진행':
        def 범위_다음_문단으로_진행():
            """다음_문단으로_진행()과 같지만 쪽 범위 밖 문단은 건너뛰고, 범위를 지나면 False를 돌려준다."""
            if 쪽범위_본문_문단 is None:
                return 다음_문단으로_진행()
            while True:
                if 중단_요청됨():
                    return False
                if not 다음_문단으로_진행():
                    return False
                pos = hwp.GetPos()
                if 쪽범위_끝지남(pos):
                    return False
                if 쪽범위_안인가(pos):
                    return True
        return bind_function(범위_다음_문단으로_진행, _docfit_namespace)
    if _docfit_symbol == '현재_표셀인가':
        def 현재_표셀인가():
            """현재 커서가 표 셀 안인지(셀 주소가 있는 영역인지) 판정한다. 본문·글상자는 False."""
            try:
                if hwp is None or hwp.GetPos()[0] == 0:
                    return False
                주소, _ = 현재_셀_주소_행번호()
                return 주소 is not None
            except Exception:
                return False
        return bind_function(현재_표셀인가, _docfit_namespace)
    if _docfit_symbol == '숫자_표칸인가':
        def 숫자_표칸인가(area=None):
            """커서가 있는(또는 area) 표 칸의 글자가 숫자·기호뿐이면 True(빈 칸 포함)."""
            original = hwp.GetPos()
            try:
                if area is not None:
                    hwp.SetPos(area, 0, 0)
                    if hwp.GetPos()[0] != area:
                        return False
                if hwp.GetPos()[0] == 0 or not 현재_표셀인가():
                    return False
                hwp_run('MoveListBegin')
                hwp_run('MoveSelListEnd')
                text = 현재선택영역_텍스트() or ''
                hwp_run('Cancel')
                return bool(_숫자칸_패턴.fullmatch(text.replace(chr(13), '').replace(chr(10), '')))
            except Exception:
                return False
            finally:
                try:
                    hwp.SetPos(*original)
                except Exception:
                    pass
        return bind_function(숫자_표칸인가, _docfit_namespace)
    if _docfit_symbol == '저장파일명':
        def 저장파일명(파일):
            path = Path(파일)
            suffix = {"spacing": "(자간조정)", "unify": "(서식통일)", "format": "(서식적용)", "all": "(일괄적용)"}[작업_모드]
            try:
                if 작업_모드 == "spacing" and 쪽맞춤만:
                    suffix = "(페이지맞춤)"
            except NameError:
                pass
            if 쪽범위_실제 is not None:
                # 일부 쪽만 처리한 결과가 전체 처리 결과를 덮어쓰지 않도록 범위를 이름에 남긴다.
                suffix += f"({쪽범위_실제[0]}-{쪽범위_실제[1]}쪽)"
            # 입력이 바이너리 HWP여도 결과물은 항상 개방형 HWPX로 저장한다.
            return str(path.with_name(path.stem + suffix + ".hwpx"))
        return bind_function(저장파일명, _docfit_namespace)
    if _docfit_symbol == '바이너리_HWP_파일인가':
        def 바이너리_HWP_파일인가(path):
            """파일 앞부분이 OLE 복합 문서(HWP 5.0 바이너리) 서명인지 본다."""
            try:
                with open(path, "rb") as f:
                    return f.read(8) == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
            except OSError:
                return False
        return bind_function(바이너리_HWP_파일인가, _docfit_namespace)
    if _docfit_symbol == '텍스트파일_읽기':
        def 텍스트파일_읽기(경로):
            for 인코딩 in _텍스트_인코딩_후보:
                try:
                    return Path(경로).read_text(encoding=인코딩)
                except (UnicodeDecodeError, LookupError):
                    continue
            raise ValueError(f"텍스트 인코딩을 확인하지 못했습니다(UTF-8/CP949만 지원): {경로}")
        return bind_function(텍스트파일_읽기, _docfit_namespace)
    raise KeyError(_docfit_symbol)
