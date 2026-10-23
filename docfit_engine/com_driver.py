"""Extracted docfit_engine.com_driver definitions; installed into the compatibility session.

Original algorithms and comments are preserved. Runtime bindings are session-local;
see docfit_engine.runtime. This module does not import the application bootstrap.
"""
from docfit_engine.runtime import bind_function, bind_class

def _install(*, _docfit_namespace, _docfit_symbol):
    global XML_네임스페이스_등록, XML_요소_생성, XML_자식_추가, _업데이트_URL_검증, _업데이트_HTTP_GET, _업데이트_기록, 업데이트_시작신호, 업데이트_잔여정리, _버전_튜플, _최신_릴리스_조회, _최신_릴리스_통합_조회, _업데이트_자산_선택, 한글_COM_인스턴스_생성, 한글_문서_열기, 한글_시작, 현재선택영역_글자수, 현재선택영역_텍스트, 색상_미리보기_hex, 색상_적용_현재선택, _표시중인_최상위창_목록, 새_한글창_찾기, 창_임베드, 창_임베드_크기조정, 창_임베드_해제, 원본_뷰어_시작, 작업창_임베드, 비교보기_임베드_재확인, 원본_뷰어_문서표시, 원본_뷰어_분리, 작업창_분리, 원본_뷰어_닫기, 작업창_닫기
    if _docfit_symbol == 'XML_네임스페이스_등록':
        def XML_네임스페이스_등록(prefix, uri):
            """defusedxml 파서는 유지하면서 ElementTree 직렬화 접두사만 등록한다.

            defusedxml.ElementTree는 안전 파싱 API로 적합하지만 register_namespace를
            노출하지 않는다. tostring이 사용하는 직렬화 네임스페이스 레지스트리에만
            등록하며, 입력 XML 파싱은 계속 defusedxml 경로를 사용한다.
            """
            register = getattr(ET, "register_namespace", None)
            if callable(register):
                register(prefix, uri)
                return True
            registry = getattr(ET.tostring, "__globals__", {}).get("_namespace_map")
            if not isinstance(registry, dict):
                # 접두사 이름은 XML 의미에 영향을 주지 않는다. 레지스트리를 제공하지
                # 않는 구현에서는 serializer가 ns0/ns1 접두사를 안전하게 생성하게 둔다.
                return False
            for existing_uri, existing_prefix in list(registry.items()):
                if existing_uri == uri or existing_prefix == prefix:
                    del registry[existing_uri]
            registry[uri] = prefix
            return True
        return bind_function(XML_네임스페이스_등록, _docfit_namespace)
    if _docfit_symbol == 'XML_요소_생성':
        def XML_요소_생성(prototype, tag=None, attrib=None):
            """defusedxml이 생성자 API를 노출하지 않을 때 파싱 요소 타입으로 새 노드를 만든다."""
            if prototype is None:
                raise ValueError('새 XML 요소를 만들 프로토타입이 없습니다.')
            return type(prototype)(tag if tag is not None else prototype.tag,
                                   {} if attrib is None else dict(attrib))
        return bind_function(XML_요소_생성, _docfit_namespace)
    if _docfit_symbol == 'XML_자식_추가':
        def XML_자식_추가(parent, prototype, tag=None, attrib=None):
            """안전 파싱 결과와 같은 요소 타입으로 자식 노드를 생성해 추가한다."""
            child = XML_요소_생성(prototype, tag=tag, attrib=attrib)
            parent.append(child)
            return child
        return bind_function(XML_자식_추가, _docfit_namespace)
    if _docfit_symbol == '_업데이트_URL_검증':
        def _업데이트_URL_검증(url):
            """업데이트 조회·다운로드 URL을 HTTPS GitLab·GitHub 주소로 제한한다."""
            parsed = urllib.parse.urlparse(str(url))
            호스트 = (parsed.hostname or "").lower()
            허용 = 호스트 in _업데이트_허용_호스트들 or any(
                호스트.endswith(접미사) for 접미사 in _업데이트_허용_호스트_접미사
            )
            if parsed.scheme != "https" or not 허용:
                raise ValueError("허용되지 않은 업데이트 URL입니다.")
            return str(url)
        return bind_function(_업데이트_URL_검증, _docfit_namespace)
    if _docfit_symbol == '_업데이트_HTTP_GET':
        def _업데이트_HTTP_GET(url, headers, timeout, _남은_리디렉션=5):
            """검증된 GitLab·GitHub HTTPS URL만 직접 HTTPS 연결로 조회한다(리디렉션도 매번 검증)."""
            parsed = urllib.parse.urlparse(_업데이트_URL_검증(url))
            연결 = http.client.HTTPSConnection(  # nosemgrep
                parsed.hostname, parsed.port or 443, timeout=timeout,
                context=ssl.create_default_context(),
            )
            연결.request("GET", parsed.path + (f"?{parsed.query}" if parsed.query else ""), headers=headers)
            응답 = 연결.getresponse()
            if 응답.status in (301, 302, 303, 307, 308) and 응답.getheader("Location"):
                다음 = urllib.parse.urljoin(str(url), 응답.getheader("Location"))
                응답.read()
                연결.close()
                if _남은_리디렉션 <= 0:
                    raise RuntimeError("업데이트 주소의 리디렉션이 너무 많습니다.")
                return _업데이트_HTTP_GET(다음, headers, timeout, _남은_리디렉션 - 1)
            if 응답.status >= 400:
                상태 = 응답.status
                응답.read()
                연결.close()
                raise urllib.error.HTTPError(url, 상태, 응답.reason, 응답.headers, None)
            응답._docfit_connection = 연결
            return 응답
        return bind_function(_업데이트_HTTP_GET, _docfit_namespace)
    if _docfit_symbol == '_업데이트_기록':
        def _업데이트_기록(내용):
            """업데이트 과정을 설정 폴더의 updates\\update.log에 남긴다(실패해도 무시)."""
            try:
                폴더 = 설정_폴더() / "updates"
                폴더.mkdir(parents=True, exist_ok=True)
                with open(폴더 / "update.log", "a", encoding="utf-8") as f:
                    f.write(f"{_datetime.datetime.now():%Y-%m-%d %H:%M:%S} [{APP_VERSION}] {내용}\n")
            except Exception:
                pass
        return bind_function(_업데이트_기록, _docfit_namespace)
    if _docfit_symbol == '업데이트_시작신호':
        def 업데이트_시작신호():
            """실행 파일로 켜졌음을 교체 스크립트에 알린다(Beta 12 리뷰 R5)."""
            try:
                폴더 = 설정_폴더() / "updates"
                폴더.mkdir(parents=True, exist_ok=True)
                (폴더 / UPDATE_STARTED_FLAG).write_text(f"{APP_VERSION} {os.getpid()}", encoding="utf-8")
            except Exception:
                pass
        return bind_function(업데이트_시작신호, _docfit_namespace)
    if _docfit_symbol == '업데이트_잔여정리':
        def 업데이트_잔여정리():
            """지난 업데이트가 남긴 구버전 백업('*.exe.old')과 내려받기 잔여물을 지운다(실행 중이면 다음에 다시 시도)."""
            try:
                실행폴더 = Path(sys.executable).resolve().parent
                업데이트_폴더 = 설정_폴더() / "updates"
                if (업데이트_폴더 / UPDATE_BUSY_FLAG).exists():
                    return      # 교체 스크립트가 시작 확인을 기다리는 중: 구버전 백업을 지우면 되살릴 수 없다
                이름들 = [x.name for x in 실행폴더.iterdir()] if 실행폴더.is_dir() else []
                업데이트_이름들 = [x.name for x in 업데이트_폴더.iterdir()] if 업데이트_폴더.is_dir() else []
                old, stale = 업데이트_잔여파일(이름들, 업데이트_이름들)
                지운 = 0
                for 경로 in [실행폴더 / n for n in old] + [업데이트_폴더 / n for n in stale]:
                    try:
                        경로.unlink()
                        지운 += 1
                    except OSError:
                        pass
                if 지운:
                    _업데이트_기록(f"지난 업데이트 잔여물 {지운}개 정리")
            except Exception:
                pass
        return bind_function(업데이트_잔여정리, _docfit_namespace)
    if _docfit_symbol == '_버전_튜플':
        def _버전_튜플(value):
            숫자 = [int(item) for item in re.findall(r"\d+", str(value))]
            return tuple((숫자 + [0, 0, 0])[:3])
        return bind_function(_버전_튜플, _docfit_namespace)
    if _docfit_symbol == '_최신_릴리스_조회':
        def _최신_릴리스_조회(timeout=8, api_url=None):
            try:
                응답 = _업데이트_HTTP_GET(api_url or UPDATE_API_URL, {
                    "Accept": "application/json",
                    "User-Agent": f"HWP-AutoDocFit/{APP_VERSION}",
                }, timeout)
                try:
                    릴리스 = json.loads(응답.read().decode("utf-8"))
                finally:
                    응답._docfit_connection.close()
            except urllib.error.HTTPError as exc:
                # GitLab은 프로젝트에 Release가 하나도 없으면 latest API에서 404를 반환한다.
                # 이는 통신 오류가 아니라 아직 배포된 업데이트가 없다는 뜻이다.
                if exc.code == 404:
                    return None
                raise
            if not isinstance(릴리스, dict):
                raise ValueError(f"릴리스 응답 형식이 올바르지 않습니다({type(릴리스).__name__}): {str(릴리스)[:80]}")
            # GitLab은 assets가 {"links": [...]} 형태의 dict이고, GitHub 형식은 목록이다. 둘 다 받는다.
            자산정보 = 릴리스.get("assets")
            if isinstance(자산정보, dict):
                링크들 = 자산정보.get("links") or []
            elif isinstance(자산정보, list):
                링크들 = 자산정보
            else:
                링크들 = []
            릴리스["assets"] = [
                {
                    **링크,
                    "browser_download_url": (
                        링크.get("direct_asset_url") or 링크.get("browser_download_url") or 링크.get("url")
                    ),
                }
                for 링크 in 링크들 if isinstance(링크, dict)
            ]
            return 릴리스
        return bind_function(_최신_릴리스_조회, _docfit_namespace)
    if _docfit_symbol == '_최신_릴리스_통합_조회':
        def _최신_릴리스_통합_조회(timeout=8):
            """GitLab과 GitHub를 모두 조회해 가장 높은 버전의 릴리스를 돌려준다.

            한쪽만 실패하면 다른 쪽 결과를 쓰고, 둘 다 실패하면 오류를 낸다.
            버전이 같으면 GitLab(사내 배포선)을 우선한다.
            """
            원본들 = (("GitLab", UPDATE_API_URL), ("GitHub", GITHUB_UPDATE_API_URL))
            결과들, 오류들 = [], []
            for 이름, 주소 in 원본들:
                try:
                    릴리스 = _최신_릴리스_조회(timeout, api_url=주소)
                except Exception as exc:
                    오류들.append(f"{이름}: {exc}")
                    continue
                if 릴리스:
                    릴리스["update_source"] = 이름
                    결과들.append(릴리스)
            if not 결과들:
                if 오류들 and len(오류들) == len(원본들):
                    raise RuntimeError(" / ".join(오류들))
                return None
            최신 = 결과들[0]
            for 후보 in 결과들[1:]:
                if _버전_튜플(후보.get("tag_name") or 후보.get("name")) > _버전_튜플(최신.get("tag_name") or 최신.get("name")):
                    최신 = 후보
            return 최신
        return bind_function(_최신_릴리스_통합_조회, _docfit_namespace)
    if _docfit_symbol == '_업데이트_자산_선택':
        def _업데이트_자산_선택(릴리스):
            자산들 = [item for item in 릴리스.get("assets", []) if str(item.get("name", "")).lower().endswith(".exe")]
            종류 = "setup" if (Path(sys.executable).parent / "unins000.exe").is_file() else "portable"
            for 자산 in 자산들:
                if re.fullmatch(r"HWP_AutoDocFit_v[0-9.]+_" + 종류 + r"\.exe", str(자산.get("name", "")), re.I):
                    return 자산
            for 자산 in 자산들:
                if str(자산.get("name", "")).lower() == UPDATE_ASSET_NAME.lower():
                    return 자산
            return 자산들[0] if len(자산들) == 1 else None
        return bind_function(_업데이트_자산_선택, _docfit_namespace)
    if _docfit_symbol == '한글_COM_인스턴스_생성':
        def 한글_COM_인스턴스_생성(독립=True):
            """한컴오피스/한글의 공통 COM ProgID로 자동화 객체를 만든다.

            DispatchEx는 작업 문서가 사용자의 기존 편집 세션에 섞이지 않게 우선 사용한다.
            일부 구형 한컴오피스 등록 상태에서 DispatchEx가 실패할 때만 Dispatch로 재시도한다.
            """
            prog_id = "HwpFrame.HwpObject"
            오류들 = []
            생성기들 = (win32.DispatchEx, win32.Dispatch) if 독립 else (win32.Dispatch,)
            from docfit_core import hwp_process
            for index, 생성기 in enumerate(생성기들):
                before = None
                if 독립 and index == 0:
                    try:
                        before = hwp_process.hwp_pids()
                    except Exception:
                        pass
                try:
                    app = 생성기(prog_id)
                    if before is not None:
                        try:
                            hwp_process.register_owned(hwp_process.hwp_pids() - before)
                        except Exception:
                            pass
                    return app
                except Exception as 오류:
                    오류들.append(f"{getattr(생성기, '__name__', 'COM 생성기')}: {오류}")
            설명 = " | ".join(오류들)
            raise RuntimeError(
                "한컴오피스 한글 자동화 객체를 만들지 못했습니다. "
                "한글(NEO/2020 이상) 설치와 HwpFrame.HwpObject COM 등록을 확인해 주세요. "
                f"세부 오류: {설명}"
            )
        return bind_function(한글_COM_인스턴스_생성, _docfit_namespace)
    if _docfit_symbol == '한글_문서_열기':
        def 한글_문서_열기(app, 경로, 형식, 옵션=''):
            """한글 버전별 pywin32 인자 바인딩 차이를 흡수해 문서를 연다."""
            try:
                # NEO와 2020 모두에서 가장 일관되게 동작하는 positional COM 호출을 우선한다.
                return app.Open(str(경로), str(형식), str(옵션))
            except TypeError as 위치인자오류:
                try:
                    # 일부 generated/early-bound wrapper는 이름 있는 인자만 노출한다.
                    return app.Open(str(경로), Format=str(형식), arg=str(옵션))
                except Exception as 이름인자오류:
                    raise RuntimeError(
                        f"한글 문서 열기 호출에 실패했습니다 ({형식}): "
                        f"위치 인자 오류={위치인자오류}; 이름 인자 오류={이름인자오류}"
                    ) from 이름인자오류
        return bind_function(한글_문서_열기, _docfit_namespace)
    if _docfit_symbol == '한글_시작':
        def 한글_시작():
            global hwp
            로그("한컴오피스 한글 자동화 시작 중... (NEO/2020 공통 COM)")
            pythoncom.CoInitialize()

            이전_창목록 = _표시중인_최상위창_목록() if 비교보기_사용 else None

            hwp = 한글_COM_인스턴스_생성(독립=True)
            hwp.XHwpWindows.Item(0).Visible = True
            로그("한글 창 표시 성공")

            result = hwp.RegisterModule(REGISTER_MODULE_NAME, REGISTER_MODULE_VALUE)
            로그(f"RegisterModule 결과: {result}")
            if not result:
                raise RuntimeError(
                    "한글 보안 모듈 RegisterModule 등록에 실패했습니다. "
                    "한컴오피스 자동화 모듈 경로와 관리자/사용자 권한을 확인해 주세요."
                )

            if 비교보기_사용 and 이전_창목록 is not None:
                작업창_임베드(이전_창목록)

            로그("한컴오피스 한글 자동화 연결 완료")
            return hwp
        return bind_function(한글_시작, _docfit_namespace)
    if _docfit_symbol == '현재선택영역_글자수':
        def 현재선택영역_글자수():
            hwp.InitScan(option=None, Range=0xff, spara=None, spos=None, epara=None, epos=None)
            try:
                _, text = hwp.GetText()
                return len(text)
            finally:
                hwp.ReleaseScan()
        return bind_function(현재선택영역_글자수, _docfit_namespace)
    if _docfit_symbol == '현재선택영역_텍스트':
        def 현재선택영역_텍스트():
            try:
                hwp.InitScan(option=None, Range=0xff, spara=None, spos=None, epara=None, epos=None)
                try:
                    _, text = hwp.GetText()
                    return text or ""
                finally:
                    hwp.ReleaseScan()
            except Exception:
                return ""
        return bind_function(현재선택영역_텍스트, _docfit_namespace)
    if _docfit_symbol == '색상_미리보기_hex':
        def 색상_미리보기_hex(rgb):
            if not rgb:
                return "#808080"
            return "#{:02X}{:02X}{:02X}".format(*rgb)
        return bind_function(색상_미리보기_hex, _docfit_namespace)
    if _docfit_symbol == '색상_적용_현재선택':
        def 색상_적용_현재선택():
            global 자간_변경_횟수
            자간_변경_횟수 += 1
            try:
                if hwp is not None:
                    자간_변경문단.add(tuple(hwp.GetPos()[:2]))
            except Exception:
                pass
            if 색상_설정 is None or hwp is None:
                return
            try:
                act = hwp.HAction
                pset = hwp.HParameterSet.HCharShape
                act.GetDefault("CharShape", pset.HSet)
                pset.TextColor = hwp.RGBColor(*색상_설정)
                act.Execute("CharShape", pset.HSet)
            except Exception as e:
                로그(f"자간조정 글자색 적용 실패: {e}")
        return bind_function(색상_적용_현재선택, _docfit_namespace)
    if _docfit_symbol == '_표시중인_최상위창_목록':
        def _표시중인_최상위창_목록():
            결과 = []
            def 콜백(hwnd, _):
                try:
                    if not win32gui.IsWindowVisible(hwnd):
                        return True
                    if win32gui.GetParent(hwnd) != 0:
                        return True
                    결과.append(hwnd)
                except Exception:
                    pass
                return True
            try:
                win32gui.EnumWindows(콜백, None)
            except Exception:
                pass
            return set(결과)
        return bind_function(_표시중인_최상위창_목록, _docfit_namespace)
    if _docfit_symbol == '새_한글창_찾기':
        def 새_한글창_찾기(이전_창목록, 제한시간=10.0):
            시작시각 = time.time()
            while time.time() - 시작시각 < 제한시간:
                현재_창목록 = _표시중인_최상위창_목록()
                신규 = 현재_창목록 - 이전_창목록
                if 신규:
                    후보 = list(신규)
                    for h in 후보:
                        try:
                            클래스명 = win32gui.GetClassName(h)
                        except Exception:
                            클래스명 = ""
                        if "hwp" in 클래스명.lower():
                            return h
                    return 후보[0]
                time.sleep(0.15)
            return None
        return bind_function(새_한글창_찾기, _docfit_namespace)
    if _docfit_symbol == '창_임베드':
        def 창_임베드(hwnd, 부모_hwnd):
            if not hwnd or not 부모_hwnd:
                return False
            try:
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                style &= ~(win32con.WS_POPUP | win32con.WS_CAPTION | win32con.WS_THICKFRAME |
                           win32con.WS_SYSMENU | win32con.WS_MINIMIZEBOX | win32con.WS_MAXIMIZEBOX)
                style |= win32con.WS_CHILD
                win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
                win32gui.SetParent(hwnd, 부모_hwnd)
                win32gui.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE |
                                      win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED)
                창_임베드_크기조정(hwnd, 부모_hwnd)
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                return True
            except Exception as e:
                로그(f"창 임베드 실패: {e}")
                return False
        return bind_function(창_임베드, _docfit_namespace)
    if _docfit_symbol == '창_임베드_크기조정':
        def 창_임베드_크기조정(hwnd, 부모_hwnd):
            if not hwnd or not 부모_hwnd:
                return
            try:
                left, top, right, bottom = win32gui.GetClientRect(부모_hwnd)
                win32gui.MoveWindow(hwnd, 0, 0, max(right - left, 1), max(bottom - top, 1), True)
            except Exception:
                pass
        return bind_function(창_임베드_크기조정, _docfit_namespace)
    if _docfit_symbol == '창_임베드_해제':
        def 창_임베드_해제(hwnd):
            if not hwnd:
                return
            try:
                win32gui.SetParent(hwnd, 0)
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                style &= ~win32con.WS_CHILD
                style |= (win32con.WS_POPUP | win32con.WS_CAPTION | win32con.WS_THICKFRAME |
                          win32con.WS_SYSMENU | win32con.WS_MINIMIZEBOX | win32con.WS_MAXIMIZEBOX)
                win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
                win32gui.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE |
                                      win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED)
            except Exception as e:
                로그(f"창 임베드 해제 실패(무시): {e}")
        return bind_function(창_임베드_해제, _docfit_namespace)
    if _docfit_symbol == '원본_뷰어_시작':
        def 원본_뷰어_시작():
            global 원본_hwp, 원본_hwp_hwnd, 비교보기_사용
            if not 비교보기_사용 or not 비교보기_좌측_프레임_hwnd or 원본_hwp is not None:
                return

            로그("비교 보기용 원본 창 시작 중...")
            이전_창목록 = _표시중인_최상위창_목록()

            for 시도 in range(1, 4):
                try:
                    원본_hwp = win32.Dispatch("HwpFrame.HwpObject")
                    원본_hwp.XHwpWindows.Item(0).Visible = True
                    break
                except Exception as e:
                    원본_hwp = None
                    로그(f"비교 보기용 원본 창 시작 실패 ({시도}/3): {e}")
                    if 시도 < 3:
                        time.sleep(1.5)

            if 원본_hwp is None:
                로그("비교 보기용 원본 창을 띄우지 못해 비교 보기 없이 진행합니다.")
                비교보기_사용 = False
                return

            try:
                원본_hwp.RegisterModule(REGISTER_MODULE_NAME, REGISTER_MODULE_VALUE)
            except Exception as e:
                로그(f"원본 창 RegisterModule 실패(무시): {e}")

            try:
                원본_hwp_hwnd = 새_한글창_찾기(이전_창목록)
                if 원본_hwp_hwnd:
                    창_임베드(원본_hwp_hwnd, 비교보기_좌측_프레임_hwnd)
            except Exception as e:
                로그(f"원본 창 임베드 실패(무시): {e}")

            로그("비교 보기용 원본 창 시작 완료")
        return bind_function(원본_뷰어_시작, _docfit_namespace)
    if _docfit_symbol == '작업창_임베드':
        def 작업창_임베드(이전_창목록):
            global 작업_hwp_hwnd
            if not 비교보기_사용 or not 비교보기_우측_프레임_hwnd:
                return
            작업_hwp_hwnd = 새_한글창_찾기(이전_창목록)
            if 작업_hwp_hwnd:
                창_임베드(작업_hwp_hwnd, 비교보기_우측_프레임_hwnd)
        return bind_function(작업창_임베드, _docfit_namespace)
    if _docfit_symbol == '비교보기_임베드_재확인':
        def 비교보기_임베드_재확인():
            if not 비교보기_사용:
                return
            if 원본_hwp_hwnd and 비교보기_좌측_프레임_hwnd:
                창_임베드(원본_hwp_hwnd, 비교보기_좌측_프레임_hwnd)
            if 작업_hwp_hwnd and 비교보기_우측_프레임_hwnd:
                창_임베드(작업_hwp_hwnd, 비교보기_우측_프레임_hwnd)
        return bind_function(비교보기_임베드_재확인, _docfit_namespace)
    if _docfit_symbol == '원본_뷰어_문서표시':
        def 원본_뷰어_문서표시(파일, 확장자명):
            if not 비교보기_사용 or 원본_hwp is None:
                return
            try:
                한글_문서_열기(원본_hwp, 파일, 확장자명.upper(), "lock:true;forceopen:true")
            except Exception as e:
                로그(f"원본 보기 창에서 파일 열기 실패(무시): {e}")
                return
            비교보기_임베드_재확인()
        return bind_function(원본_뷰어_문서표시, _docfit_namespace)
    if _docfit_symbol == '원본_뷰어_분리':
        def 원본_뷰어_분리():
            global 원본_hwp, 원본_hwp_hwnd
            if 원본_hwp is None:
                return
            창_임베드_해제(원본_hwp_hwnd)
            원본_hwp = None
            원본_hwp_hwnd = None
        return bind_function(원본_뷰어_분리, _docfit_namespace)
    if _docfit_symbol == '작업창_분리':
        def 작업창_분리():
            global hwp, 작업_hwp_hwnd
            if 작업_hwp_hwnd:
                창_임베드_해제(작업_hwp_hwnd)
            hwp = None
            작업_hwp_hwnd = None
        return bind_function(작업창_분리, _docfit_namespace)
    if _docfit_symbol == '원본_뷰어_닫기':
        def 원본_뷰어_닫기():
            global 원본_hwp, 원본_hwp_hwnd
            if 원본_hwp is None:
                return
            창_임베드_해제(원본_hwp_hwnd)
            try:
                원본_hwp.Quit()
            except Exception:
                pass
            finally:
                원본_hwp = None
                원본_hwp_hwnd = None
        return bind_function(원본_뷰어_닫기, _docfit_namespace)
    if _docfit_symbol == '작업창_닫기':
        def 작업창_닫기():
            global hwp, 작업_hwp_hwnd
            if hwp is None:
                return
            창_임베드_해제(작업_hwp_hwnd)
            try:
                hwp.Quit()
            except Exception:
                pass
            finally:
                hwp = None
                작업_hwp_hwnd = None
        return bind_function(작업창_닫기, _docfit_namespace)
    raise KeyError(_docfit_symbol)
