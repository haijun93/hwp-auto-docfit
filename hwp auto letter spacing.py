import os
import sys
import shutil
import traceback
import winreg

from tkinter import Tk
from tkinter.filedialog import askopenfilenames
from tkinter import messagebox

import win32com.client as win32


# ============================================================
# 기본 설정
# ============================================================

APP_NAME = "LineFit"

VERSION = "0.1"

DLL_NAME = "FilePathCheckerModuleExample.dll"

# DLL이 최종적으로 설치될 위치
HWP_AUTOMATION_DIR = r"C:\HwpAutomation"

TARGET_DLL_PATH = os.path.join(
    HWP_AUTOMATION_DIR,
    DLL_NAME
)

# 한글 Automation 보안모듈 이름
AUTOMATION_MODULE_NAME = "AutomationModule"

# 레지스트리 위치
REGISTRY_PATH = r"Software\HNC\HwpAutomation\Modules"


# ============================================================
# 전역 HWP 객체
# ============================================================

hwp = None


# ============================================================
# 프로그램 설치 폴더
# ============================================================

def 설치폴더():
    """
    FilePathCheckerModuleExample.dll을 찾을
    프로그램 설치 폴더를 반환한다.

    일반 Python 실행:
        현재 실행 중인 .py 파일의 폴더

    PyInstaller EXE:
        EXE 파일이 있는 폴더
    """

    if getattr(sys, "frozen", False):

        # PyInstaller 등으로 EXE화된 경우
        return os.path.dirname(
            os.path.abspath(sys.executable)
        )

    # Python으로 직접 실행하는 경우
    return os.path.dirname(
        os.path.abspath(__file__)
    )


# ============================================================
# 설치파일에 포함된 DLL 위치
# ============================================================

def 원본_DLL_경로():
    """
    프로그램 설치 폴더에 있는
    FilePathCheckerModuleExample.dll의 경로를 반환한다.
    """

    return os.path.join(
        설치폴더(),
        DLL_NAME
    )


# ============================================================
# 레지스트리 현재 설정 확인
# ============================================================

def 레지스트리_DLL_경로():
    """
    현재 사용자(HKCU)에 등록된
    AutomationModule 값을 읽는다.

    등록되어 있지 않으면 None 반환.
    """

    try:

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_PATH,
            0,
            winreg.KEY_READ
        ) as key:

            value, value_type = winreg.QueryValueEx(
                key,
                AUTOMATION_MODULE_NAME
            )

            if value_type != winreg.REG_SZ:
                return None

            return value

    except FileNotFoundError:

        return None

    except OSError:

        return None


# ============================================================
# 레지스트리 정상 여부 확인
# ============================================================

def 레지스트리_정상():
    """
    AutomationModule이 올바른 DLL을 가리키고 있는지 확인한다.
    """

    등록된_DLL = 레지스트리_DLL_경로()

    if not 등록된_DLL:
        return False

    등록된_DLL = os.path.normcase(
        os.path.abspath(등록된_DLL)
    )

    목표_DLL = os.path.normcase(
        os.path.abspath(TARGET_DLL_PATH)
    )

    return 등록된_DLL == 목표_DLL


# ============================================================
# DLL 설치
# ============================================================

def DLL_설치():
    """
    설치 폴더에 있는 DLL을
    C:\\HwpAutomation에 복사한다.

    이미 동일한 DLL이 있으면 복사하지 않는다.
    """

    원본 = 원본_DLL_경로()
    대상 = TARGET_DLL_PATH

    # --------------------------------------------------------
    # 원본 DLL 확인
    # --------------------------------------------------------

    if not os.path.isfile(원본):

        raise FileNotFoundError(
            "FilePathCheckerModuleExample.dll을 찾을 수 없습니다.\n\n"
            f"확인 위치:\n{원본}\n\n"
            "DLL 파일을 프로그램 실행 파일과 같은 폴더에 "
            "배치한 후 다시 실행하세요."
        )

    # --------------------------------------------------------
    # 설치 폴더 생성
    # --------------------------------------------------------

    os.makedirs(
        HWP_AUTOMATION_DIR,
        exist_ok=True
    )

    # --------------------------------------------------------
    # 대상 파일이 이미 존재하는 경우
    # --------------------------------------------------------

    if os.path.isfile(대상):

        # 동일한 파일인지 확인
        try:

            if os.path.samefile(원본, 대상):

                return False

        except (FileNotFoundError, OSError):

            pass

        # 크기와 수정시간이 같다면 기존 파일 유지
        try:

            원본정보 = os.stat(원본)
            대상정보 = os.stat(대상)

            if (
                원본정보.st_size == 대상정보.st_size
                and 원본정보.st_mtime_ns == 대상정보.st_mtime_ns
            ):

                return False

        except OSError:

            pass

    # --------------------------------------------------------
    # DLL 복사
    # --------------------------------------------------------

    shutil.copy2(
        원본,
        대상
    )

    return True


# ============================================================
# 레지스트리 등록
# ============================================================

def 레지스트리_등록():
    """
    다음 레지스트리를 생성/등록한다.

    HKEY_CURRENT_USER
    └─ Software
       └─ HNC
          └─ HwpAutomation
             └─ Modules
                └─ AutomationModule
                   = C:\\HwpAutomation\\FilePathCheckerModuleExample.dll
    """

    # --------------------------------------------------------
    # Modules 키 생성
    # --------------------------------------------------------

    with winreg.CreateKey(
        winreg.HKEY_CURRENT_USER,
        REGISTRY_PATH
    ) as key:

        winreg.SetValueEx(
            key,
            AUTOMATION_MODULE_NAME,
            0,
            winreg.REG_SZ,
            TARGET_DLL_PATH
        )


# ============================================================
# 보안모듈 사전 초기화
# ============================================================

def 보안모듈_초기화():
    """
    프로그램 최초 실행 시 필요한 HWP Automation 보안모듈
    설치 상태를 확인하고 필요한 경우 자동으로 설정한다.

    이미 정상적으로 설치되어 있으면 아무 작업도 하지 않는다.

    관리자 권한은 필요하지 않다.
    """

    print()
    print("=" * 70)
    print("HWP Automation 보안모듈 확인")
    print("=" * 70)

    원본 = 원본_DLL_경로()

    print("프로그램 폴더:")
    print(설치폴더())

    print()
    print("원본 DLL:")
    print(원본)

    print()
    print("설치 대상 DLL:")
    print(TARGET_DLL_PATH)

    # --------------------------------------------------------
    # 1. 설치파일 폴더의 DLL 확인
    # --------------------------------------------------------

    if not os.path.isfile(원본):

        raise FileNotFoundError(
            "보안모듈 DLL을 찾을 수 없습니다.\n\n"
            f"{원본}\n\n"
            "FilePathCheckerModuleExample.dll을 "
            "프로그램 설치 폴더에 넣어주세요."
        )

    print()
    print("[1/3] 원본 DLL 확인: OK")

    # --------------------------------------------------------
    # 2. C:\HwpAutomation DLL 확인/복사
    # --------------------------------------------------------

    if os.path.isfile(TARGET_DLL_PATH):

        print("[2/3] C:\\HwpAutomation DLL: 이미 존재")

    else:

        print("[2/3] C:\\HwpAutomation DLL: 없음")
        print("      DLL을 복사합니다.")

        DLL_설치()

        print("      DLL 복사 완료")

    # --------------------------------------------------------
    # 3. 레지스트리 확인/등록
    # --------------------------------------------------------

    if 레지스트리_정상():

        print("[3/3] AutomationModule 레지스트리: 정상")

    else:

        print("[3/3] AutomationModule 레지스트리: 없음 또는 잘못됨")
        print("      레지스트리를 등록합니다.")

        레지스트리_등록()

        print("      레지스트리 등록 완료")

    # --------------------------------------------------------
    # 최종 검증
    # --------------------------------------------------------

    if not os.path.isfile(TARGET_DLL_PATH):

        raise RuntimeError(
            "보안모듈 DLL 설치에 실패했습니다."
        )

    if not 레지스트리_정상():

        raise RuntimeError(
            "AutomationModule 레지스트리 등록에 실패했습니다."
        )

    print()
    print("보안모듈 초기화 완료")
    print("=" * 70)


# ============================================================
# 한글 2020 시작
# ============================================================

def 한글_시작():

    print()
    print("한글 2020을 시작합니다.")

    hwp = win32.Dispatch(
        "HWPFrame.HwpObject"
    )

    print("HwpObject 생성 성공")

    # --------------------------------------------------------
    # Automation 보안모듈 등록
    # --------------------------------------------------------

    result = hwp.RegisterModule(
        "FilePathCheckDLL",
        AUTOMATION_MODULE_NAME
    )

    print(
        "RegisterModule 결과:",
        result
    )

    # --------------------------------------------------------
    # 한글 창 표시
    # --------------------------------------------------------

    hwp.XHwpWindows.Item(0).Visible = True

    print("한글 2020 실행 완료")

    return hwp


# ============================================================
# 파일 선택
# ============================================================

def 파일선택():

    root = Tk()

    root.withdraw()

    root.attributes(
        "-topmost",
        True
    )

    파일목록 = askopenfilenames(
        parent=root,
        title="자간을 조정할 한/글 문서를 모두 선택해주세요.",
        initialdir=os.getcwd(),
        filetypes=[
            ("한/글 문서", "*.hwp *.hwpx"),
            ("HWP 문서", "*.hwp"),
            ("HWPX 문서", "*.hwpx"),
        ]
    )

    root.destroy()

    return list(파일목록)


# ============================================================
# 현재 선택 영역 글자 수
# ============================================================

def 현재선택영역_글자수():

    hwp.InitScan(
        option=None,
        Range=0xff,
        spara=None,
        spos=None,
        epara=None,
        epos=None
    )

    try:

        _, text = hwp.GetText()

        if text is None:
            return 0

        return len(text)

    finally:

        hwp.ReleaseScan()


# ============================================================
# 자간 자동 조정
# ============================================================

def 자간자동조정():

    count = 0

    while True:

        hwp.Run("MoveLineEnd")

        hwp.Run("MoveSelWordBegin")

        if count >= 15:

            print(
                "    15회 이상 조정 → 원상복구"
            )

            for _ in range(count):

                hwp.Run("Undo")

            hwp.Run("Cancel")

            break

        앞부분길이 = 현재선택영역_글자수()

        if 앞부분길이 == 0:

            hwp.Run("Cancel")

            break

        hwp.Run("MoveSelWordEnd")

        뒷부분길이 = 현재선택영역_글자수()

        if not (
            앞부분길이
            and 뒷부분길이
        ):

            hwp.Run("Cancel")
            hwp.Run("Cancel")

            break

        hwp.Run("MoveWordBegin")

        hwp.Run("MoveLineEnd")

        hwp.Run("MoveSelLineBegin")

        if 앞부분길이 >= 뒷부분길이:

            hwp.Run(
                "CharShapeSpacingDecrease"
            )

        else:

            hwp.Run(
                "CharShapeSpacingIncrease"
            )

        count += 1

        hwp.Run("Cancel")


# ============================================================
# 컨트롤 내부 자간 조정
# ============================================================

def 컨트롤_내부_자간조정():

    area = 1

    while True:

        area += 1

        hwp.SetPos(
            area,
            0,
            0
        )

        if hwp.GetPos()[0] == 0:

            break

        while True:

            시작위치 = hwp.GetPos()

            자간자동조정()

            hwp.Run("MoveLineEnd")

            hwp.Run("MoveNextChar")

            현재위치 = hwp.GetPos()

            if (
                현재위치[0] != 0
                and 현재위치[0] >= area
            ):

                area = 현재위치[0]

            if 현재위치 == 시작위치:

                break


# ============================================================
# 문서 끝 위치
# ============================================================

def 끝위치추출():

    hwp.Run("MoveDocEnd")

    end_pos = hwp.GetPos()

    hwp.Run("MoveDocBegin")

    return end_pos


# ============================================================
# 문서 정보
# ============================================================

def 문서정보(파일):

    확장자 = os.path.splitext(
        파일
    )[1].lower()

    if 확장자 == ".hwp":

        return "HWP"

    if 확장자 == ".hwpx":

        return "HWPX"

    raise ValueError(
        f"지원하지 않는 파일 형식: {파일}"
    )


# ============================================================
# 저장 경로
# ============================================================

def 저장경로_생성(파일):

    폴더 = os.path.dirname(파일)

    파일명 = os.path.basename(파일)

    이름, 확장자 = os.path.splitext(
        파일명
    )

    return os.path.join(
        폴더,
        f"{이름}(자간조정){확장자}"
    )


# ============================================================
# 현재 문서 닫기
# ============================================================

def 현재문서_닫기():

    try:

        hwp.Clear(1)

    except Exception:

        try:

            hwp.Run("FileClose")

        except Exception:

            pass


# ============================================================
# 문서 하나 처리
# ============================================================

def 문서_처리(
    파일,
    번호,
    전체개수
):

    print()
    print("=" * 70)

    print(
        f"[{번호}/{전체개수}] "
        f"{os.path.basename(파일)}"
    )

    print("=" * 70)

    포맷 = 문서정보(파일)

    저장경로 = 저장경로_생성(파일)

    print("원본:", 파일)
    print("저장:", 저장경로)

    # --------------------------------------------------------
    # 문서 열기
    # --------------------------------------------------------

    print()
    print("문서를 여는 중...")

    hwp.Open(
        파일,
        Format=포맷,
        arg=""
    )

    print("문서 열기 완료")

    # --------------------------------------------------------
    # 문서 처음
    # --------------------------------------------------------

    hwp.Run(
        "MoveDocBegin"
    )

    # --------------------------------------------------------
    # 끝 위치
    # --------------------------------------------------------

    끝위치 = 끝위치추출()

    # --------------------------------------------------------
    # 본문
    # --------------------------------------------------------

    print(
        "본문 자간 조정 중..."
    )

    while hwp.GetPos() != 끝위치:

        자간자동조정()

        hwp.Run(
            "MoveLineEnd"
        )

        hwp.Run(
            "MoveNextChar"
        )

    print(
        "본문 자간 조정 완료"
    )

    # --------------------------------------------------------
    # 컨트롤
    # --------------------------------------------------------

    print(
        "표/글상자 등 내부 자간 조정 중..."
    )

    컨트롤_내부_자간조정()

    print(
        "컨트롤 내부 자간 조정 완료"
    )

    # --------------------------------------------------------
    # 저장
    # --------------------------------------------------------

    print(
        "자간조정 파일 저장 중..."
    )

    hwp.SaveAs(
        Path=저장경로,
        Format=포맷,
        arg=""
    )

    print(
        "저장 완료:",
        저장경로
    )

    # --------------------------------------------------------
    # 닫기
    # --------------------------------------------------------

    현재문서_닫기()

    return 저장경로


# ============================================================
# 메인
# ============================================================

def main():

    global hwp

    성공목록 = []
    실패목록 = []

    print("=" * 70)
    print(f"{APP_NAME} v{VERSION}")
    print("=" * 70)

    try:

        # ====================================================
        # 최초 사전 절차
        # ====================================================

        보안모듈_초기화()

        # ====================================================
        # 한글 시작
        # ====================================================

        hwp = 한글_시작()

        # ====================================================
        # 파일 선택
        # ====================================================

        파일목록 = 파일선택()

        if not 파일목록:

            print()
            print(
                "선택한 파일이 없습니다."
            )

            return

        # ====================================================
        # 선택 파일
        # ====================================================

        print()
        print("=" * 70)
        print(
            f"선택한 문서: "
            f"{len(파일목록)}개"
        )
        print("=" * 70)

        for 번호, 파일 in enumerate(
            파일목록,
            1
        ):

            print(
                f"{번호:>3}. {파일}"
            )

        # ====================================================
        # 문서 처리
        # ====================================================

        for 번호, 파일 in enumerate(
            파일목록,
            1
        ):

            try:

                저장경로 = 문서_처리(
                    파일,
                    번호,
                    len(파일목록)
                )

                성공목록.append(
                    (
                        파일,
                        저장경로
                    )
                )

            except Exception as e:

                실패목록.append(
                    (
                        파일,
                        str(e)
                    )
                )

                print()
                print("!" * 70)
                print(
                    "문서 처리 실패"
                )
                print(
                    "파일:",
                    파일
                )
                print(
                    "오류:",
                    e
                )
                print("!" * 70)

                traceback.print_exc()

                try:

                    현재문서_닫기()

                except Exception:

                    pass

        # ====================================================
        # 결과
        # ====================================================

        print()
        print()
        print("=" * 70)
        print("모든 작업이 완료되었습니다.")
        print("=" * 70)

        print(
            f"전체: {len(파일목록)}개"
        )

        print(
            f"성공: {len(성공목록)}개"
        )

        print(
            f"실패: {len(실패목록)}개"
        )

        # ----------------------------------------------------
        # 성공
        # ----------------------------------------------------

        if 성공목록:

            print()
            print(
                "[성공]"
            )

            for 원본, 저장 in 성공목록:

                print()
                print(
                    "원본:",
                    원본
                )

                print(
                    "저장:",
                    저장
                )

        # ----------------------------------------------------
        # 실패
        # ----------------------------------------------------

        if 실패목록:

            print()
            print(
                "[실패]"
            )

            for 파일, 오류 in 실패목록:

                print()
                print(
                    "파일:",
                    파일
                )

                print(
                    "오류:",
                    오류
                )

    except Exception as e:

        print()
        print("!" * 70)
        print(
            "프로그램 실행 오류"
        )
        print("!" * 70)

        print(e)

        traceback.print_exc()

        try:

            messagebox.showerror(
                f"{APP_NAME} v{VERSION}",
                f"프로그램 실행 중 오류가 발생했습니다.\n\n{e}"
            )

        except Exception:

            pass

    finally:

        # ====================================================
        # 한글 종료
        # ====================================================

        if hwp is not None:

            try:

                hwp.Quit()

                print()
                print(
                    "한글 2020을 종료했습니다."
                )

            except Exception as e:

                print(
                    "한글 종료 오류:",
                    e
                )


# ============================================================
# 실행
# ============================================================

if __name__ == "__main__":

    main()
