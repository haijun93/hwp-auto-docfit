"""Extracted docfit_engine.security definitions; installed into the compatibility session.

Original algorithms and comments are preserved. Runtime bindings are session-local;
see docfit_engine.runtime. This module does not import the application bootstrap.
"""
from docfit_engine.runtime import bind_function, bind_class

def _install(*, _docfit_namespace, _docfit_symbol):
    global 원본_DLL_찾기, 등록된_DLL_경로, 레지스트리_등록, 보안모듈_초기화, 이전_보안모듈_정리
    if _docfit_symbol == '원본_DLL_찾기':
        def 원본_DLL_찾기():
            후보_목록 = [프로그램_폴더() / DLL_NAME]
            번들_폴더 = 번들_리소스_폴더()
            if 번들_폴더 is not None:
                후보_목록.append(번들_폴더 / DLL_NAME)
            for dll_path in 후보_목록:
                로그(f"DLL 확인: {dll_path}")
                if dll_path.is_file():
                    return dll_path
            return None
        return bind_function(원본_DLL_찾기, _docfit_namespace)
    if _docfit_symbol == '등록된_DLL_경로':
        def 등록된_DLL_경로():
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH, 0, winreg.KEY_READ) as key:
                    value, value_type = winreg.QueryValueEx(key, REGISTRY_VALUE_NAME)
                    if value_type == winreg.REG_SZ:
                        return str(value)
            except (FileNotFoundError, OSError):
                pass
            return None
        return bind_function(등록된_DLL_경로, _docfit_namespace)
    if _docfit_symbol == '레지스트리_등록':
        def 레지스트리_등록():
            TARGET_DLL.parent.mkdir(parents=True, exist_ok=True)
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH) as key:
                winreg.SetValueEx(key, REGISTRY_VALUE_NAME, 0, winreg.REG_SZ, str(TARGET_DLL))
            로그("AutomationModule Registry 등록 완료")
        return bind_function(레지스트리_등록, _docfit_namespace)
    if _docfit_symbol == '보안모듈_초기화':
        def 보안모듈_초기화():
            로그("AutomationModule 확인 시작")
            source_dll = 원본_DLL_찾기()
            if source_dll is None:
                raise FileNotFoundError(
                    f"\n\n{DLL_NAME}을 프로그램 폴더에서 찾을 수 없습니다.\n"
                    f"위치: {프로그램_폴더() / DLL_NAME}"
                )
            global TARGET_DLL, DLL_DIR
            from docfit_engine.security import install_security_dll
            def register(path):
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH) as key:
                    winreg.SetValueEx(key, REGISTRY_VALUE_NAME, 0, winreg.REG_SZ, str(path))
            selected = install_security_dll(source_dll, TARGET_DLL, register)
            TARGET_DLL, DLL_DIR = selected, selected.parent
            로그(f"AutomationModule 설치·등록 완료: {selected}")
            이전_보안모듈_정리()
            로그("AutomationModule 초기화 완료")
        return bind_function(보안모듈_초기화, _docfit_namespace)
    if _docfit_symbol == '이전_보안모듈_정리':
        def 이전_보안모듈_정리():
            """앱 폴더를 옮긴 뒤(C:\\HwpAutomation → C:\\HWP_AUTODOCFIT\\dll) 예전 폴더의 이 앱 DLL과 예전 레지스트리 값을 지운다.

            예전 폴더는 비면 지우고 다른 파일이 있으면 남긴다. 한/글이 DLL을 쓰고 있어 지우지 못하면 다음 실행 때 다시
            시도한다(무시). 예전 판(베타)을 다시 실행하면 그 판이 예전 폴더·값을 스스로 다시 만든다."""
            예전폴더 = 서식예시모듈.LEGACY_APP_HOME
            if TARGET_DLL.parent == 예전폴더:
                return
            try:
                예전 = 예전폴더 / 서식예시모듈.LEGACY_DLL_FILE
                if 예전.is_file():
                    예전.unlink()
                    로그(f"예전 보안 모듈 폴더 정리: {예전}")
                if 예전폴더.is_dir() and not any(예전폴더.iterdir()):
                    예전폴더.rmdir()
            except Exception as exc:
                로그(f"예전 보안 모듈 정리 보류(무시): {exc}")
            if REGISTRY_VALUE_NAME != 서식예시모듈.LEGACY_REGISTRY_VALUE:
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH, 0, winreg.KEY_ALL_ACCESS) as key:
                        winreg.DeleteValue(key, 서식예시모듈.LEGACY_REGISTRY_VALUE)
                    로그(f"예전 레지스트리 값 정리: {서식예시모듈.LEGACY_REGISTRY_VALUE}")
                except FileNotFoundError:
                    pass
                except Exception as exc:
                    로그(f"예전 레지스트리 값 정리 보류(무시): {exc}")
        return bind_function(이전_보안모듈_정리, _docfit_namespace)
    raise KeyError(_docfit_symbol)


def install_security_dll(source, preferred, register, *, local_appdata=None):
    """Install/register in the preferred folder, then the per-user modules folder.

    register(path) is a caller-provided HKCU registrar. No GUI or Windows registry
    import is needed by this policy, which can be exercised without COM.
    """
    import os
    import shutil
    from pathlib import Path
    source, preferred = Path(source), Path(preferred)
    if not source.is_file():
        raise FileNotFoundError(source)
    base = Path(local_appdata or os.environ.get('LOCALAPPDATA') or Path.home() / 'AppData' / 'Local')
    fallback = base / 'HwpAutoDocFit' / 'modules' / preferred.name
    errors = []
    for target in dict.fromkeys((preferred, fallback)):
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.is_file():
                shutil.copy2(source, target)
            register(target)
            return target
        except OSError as exc:
            errors.append(exc)
    raise OSError('보안 모듈을 기본 폴더와 사용자 폴더에 설치·등록하지 못했습니다.') from errors[-1]
