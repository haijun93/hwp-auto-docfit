#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""한글 문서편집 자동화 도구(HWP Auto DocFit) - 원상복구 및 초기화 도구.

이 도구는 앱 실행 시 시스템에 등록되는 보안 모듈 DLL 파일,
한/글 자동화 레지스트리 키, 사용자 설정 및 캐시 폴더를
안전하고 깨끗하게 원상태로 초기화(제거)합니다.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk
import winreg

# ============================================================
# 설정 상수 (hwp-auto-docfit.py와 일치)
# ============================================================
DLL_NAME = "MapoHwpAutoDocFitSecurity.dll"
# 보안 모듈 DLL: 알파(2026-10-10)부터 C:\HWP_AUTODOCFIT\dll\HwpAutoDocFitSecurity.dll(레지스트리 값 HwpAutoDocFitSecurity),
# 그 전에는 C:\HwpAutomation\MapoHwpAutoDocFitSecurity.dll(값 MapoHwpAutoDocFitSecurity). 둘 다 정리한다.
HWP_AUTOMATION_DIR = Path(r"C:\HWP_AUTODOCFIT\dll")
TARGET_DLL = HWP_AUTOMATION_DIR / "HwpAutoDocFitSecurity.dll"
LEGACY_AUTOMATION_DIR = Path(r"C:\HwpAutomation")
REGISTRY_PARENT = r"Software\HNC\HwpAutomation"
REGISTRY_PATH = r"Software\HNC\HwpAutomation\Modules"
REGISTRY_VALUE_NAME = "HwpAutoDocFitSecurity"
LEGACY_REGISTRY_VALUE_NAME = "MapoHwpAutoDocFitSecurity"


def 설정_폴더_목록() -> list[Path]:
    """앱 관련 사용자 설정 및 캐시 폴더 목록을 반환한다."""
    folders = []
    appdata = os.environ.get("APPDATA")
    if appdata:
        folders.append(Path(appdata) / "HwpAutoDocFit")
    localappdata = os.environ.get("LOCALAPPDATA")
    if localappdata:
        folders.append(Path(localappdata) / "HwpAutoDocFit")
    home_dir = Path.home() / ".hwp_auto_docfit"
    folders.append(home_dir)
    return [p for p in folders if p.exists()]


def 한글_실행_중인가() -> bool:
    """Hwp.exe 프로세스가 현재 실행 중인지 확인한다."""
    try:
        output = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq Hwp.exe", "/NH"],
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return "hwp.exe" in output.lower()
    except Exception:
        return False


def 레지스트리_등록_확인() -> bool:
    """레지스트리에 보안 모듈이 등록되어 있는지 확인한다."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH, 0, winreg.KEY_READ) as key:
            for name in (REGISTRY_VALUE_NAME, LEGACY_REGISTRY_VALUE_NAME):
                try:
                    val, _ = winreg.QueryValueEx(key, name)
                    if val:
                        return True
                except (FileNotFoundError, OSError):
                    continue
            return False
    except (FileNotFoundError, OSError):
        return False


def 레지스트리_제거() -> tuple[bool, str]:
    """등록된 보안 모듈 레지스트리 값을 삭제하고 빈 키를 정리한다."""
    removed = False
    details = []
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH, 0, winreg.KEY_ALL_ACCESS) as key:
            for name in (REGISTRY_VALUE_NAME, LEGACY_REGISTRY_VALUE_NAME):
                try:
                    winreg.DeleteValue(key, name)
                    removed = True
                    details.append(f"레지스트리 값 삭제 완료: HKCU\\{REGISTRY_PATH}\\{name}")
                except FileNotFoundError:
                    details.append(f"레지스트리 값이 이미 존재하지 않습니다: {name}")
    except FileNotFoundError:
        details.append("레지스트리 키가 존재하지 않습니다.")
        return True, "\n".join(details)
    except Exception as e:
        return False, f"레지스트리 값 삭제 실패: {e}"

    # Modules 키가 비어있으면 키 자체도 정리
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH, 0, winreg.KEY_READ) as key:
            subkeys, values, _ = winreg.QueryInfoKey(key)
            if subkeys == 0 and values == 0:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH)
                details.append(f"빈 레지스트리 키 삭제: HKCU\\{REGISTRY_PATH}")
    except Exception:
        pass

    # HwpAutomation 키도 비어있으면 정리
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_PARENT, 0, winreg.KEY_READ) as key:
            subkeys, values, _ = winreg.QueryInfoKey(key)
            if subkeys == 0 and values == 0:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REGISTRY_PARENT)
                details.append(f"빈 레지스트리 키 삭제: HKCU\\{REGISTRY_PARENT}")
    except Exception:
        pass

    return True, "\n".join(details)


def _폴더의_DLL_제거(folder: Path, dll: Path, details: list) -> bool:
    """한 폴더의 이 앱 DLL을 지우고, 폴더가 비면 폴더도 지운다(다른 파일·서식예시 폴더가 있으면 보존)."""
    if dll.exists():
        try:
            dll.unlink()
            details.append(f"DLL 파일 삭제 완료: {dll}")
        except Exception as e:
            details.append(f"DLL 파일 삭제 실패 (한/글이 실행 중인지 확인하세요): {e}")
            return False
    if folder.exists():
        try:
            items = list(folder.iterdir())
            if not items:
                folder.rmdir()
                details.append(f"빈 폴더 삭제 완료: {folder}")
            else:
                details.append(f"폴더 보존 (사용자 서식예시 등 다른 항목 {len(items)}개 존재): {folder}")
        except Exception as e:
            details.append(f"폴더 정리 실패(무시): {e}")
    return True


def 보안_DLL_제거() -> tuple[bool, str]:
    """앱 폴더(C:\\HWP_AUTODOCFIT)와 예전 폴더(C:\\HwpAutomation)의 보안 모듈 DLL을 삭제하고 빈 폴더를 정리한다."""
    details = []
    if not TARGET_DLL.exists() and not (LEGACY_AUTOMATION_DIR / DLL_NAME).exists():
        details.append(f"DLL 파일이 존재하지 않습니다: {TARGET_DLL}")
    ok = _폴더의_DLL_제거(HWP_AUTOMATION_DIR, TARGET_DLL, details)
    앱폴더 = HWP_AUTOMATION_DIR.parent
    if 앱폴더.name.upper() == "HWP_AUTODOCFIT" and 앱폴더.is_dir() and not any(앱폴더.iterdir()):
        try:
            앱폴더.rmdir()
            details.append(f"빈 폴더 삭제 완료: {앱폴더}")
        except Exception as e:
            details.append(f"폴더 정리 실패(무시): {e}")
    if LEGACY_AUTOMATION_DIR != HWP_AUTOMATION_DIR:
        ok = _폴더의_DLL_제거(LEGACY_AUTOMATION_DIR, LEGACY_AUTOMATION_DIR / DLL_NAME, details) and ok
    if not ok:
        return False, "\n".join(details)
    return True, "\n".join(details)


def 설정폴더_제거() -> tuple[bool, str]:
    """사용자 설정 및 서식 예시 캐시 폴더를 삭제한다."""
    folders = 설정_폴더_목록()
    if not folders:
        return True, "앱 설정 폴더가 존재하지 않습니다."
    details = []
    for f in folders:
        try:
            shutil.rmtree(f)
            details.append(f"설정 폴더 삭제 완료: {f}")
        except Exception as e:
            details.append(f"설정 폴더 삭제 실패 ({f}): {e}")
    return True, "\n".join(details)


def 전체_원상복구(dll=True, reg=True, settings=True) -> tuple[bool, list[str]]:
    """선택된 모든 구성 요소에 대해 원상복구를 수행한다."""
    logs = []
    all_success = True

    if dll:
        ok, msg = 보안_DLL_제거()
        logs.append(msg)
        if not ok:
            all_success = False

    if reg:
        ok, msg = 레지스트리_제거()
        logs.append(msg)
        if not ok:
            all_success = False

    if settings:
        ok, msg = 설정폴더_제거()
        logs.append(msg)
        if not ok:
            all_success = False

    return all_success, logs


# ============================================================
# GUI 인터페이스
# ============================================================
class ResetAppUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("한글 문서편집 자동화 도구 - 원상복구 / 초기화")
        self.root.geometry("540x480")
        self.root.minsize(480, 420)
        self.root.configure(bg="#F8F9FA")

        self._폰트_설정()
        self._UI_구성()
        self._상태_갱신()

    def _폰트_설정(self):
        self.font_title = ("Malgun Gothic", 13, "bold")
        self.font_desc = ("Malgun Gothic", 9)
        self.font_bold = ("Malgun Gothic", 9, "bold")
        self.font_text = ("Consolas", 9)

    def _UI_구성(self):
        # 상단 타이틀 배너
        header_frame = tk.Frame(self.root, bg="#2B3A4A", padx=20, pady=16)
        header_frame.pack(fill=tk.X)

        title_label = tk.Label(
            header_frame,
            text="한글 문서편집 자동화 도구 초기화",
            font=self.font_title,
            fg="#FFFFFF",
            bg="#2B3A4A",
        )
        title_label.pack(anchor="w")

        desc_label = tk.Label(
            header_frame,
            text="앱 실행 시 시스템에 설치된 보안 DLL, 레지스트리, 설정 데이터를 초기 상태로 복구합니다.",
            font=self.font_desc,
            fg="#CBD5E1",
            bg="#2B3A4A",
            pady=4,
        )
        desc_label.pack(anchor="w")

        # 본문 옵션 프레임
        body_frame = tk.LabelFrame(
            self.root,
            text=" 원상복구 대상 선택 ",
            font=self.font_bold,
            bg="#FFFFFF",
            fg="#1E293B",
            padx=15,
            pady=12,
        )
        body_frame.pack(fill=tk.X, padx=15, pady=12)

        self.var_dll = tk.BooleanVar(value=True)
        self.var_reg = tk.BooleanVar(value=True)
        self.var_settings = tk.BooleanVar(value=True)

        # 항목 1: DLL
        self.chk_dll = tk.Checkbutton(
            body_frame,
            text=f"보안 모듈 DLL 파일 삭제 ({TARGET_DLL})",
            variable=self.var_dll,
            font=self.font_desc,
            bg="#FFFFFF",
            activebackground="#FFFFFF",
        )
        self.chk_dll.pack(anchor="w", pady=3)
        self.lbl_dll_status = tk.Label(body_frame, text="상태 확인 중...", font=self.font_desc, fg="#64748B", bg="#FFFFFF")
        self.lbl_dll_status.pack(anchor="w", padx=24)

        # 항목 2: 레지스트리
        self.chk_reg = tk.Checkbutton(
            body_frame,
            text=f"한/글 자동화 레지스트리 등록 해제 (HKCU\\{REGISTRY_PATH})",
            variable=self.var_reg,
            font=self.font_desc,
            bg="#FFFFFF",
            activebackground="#FFFFFF",
        )
        self.chk_reg.pack(anchor="w", pady=3)
        self.lbl_reg_status = tk.Label(body_frame, text="상태 확인 중...", font=self.font_desc, fg="#64748B", bg="#FFFFFF")
        self.lbl_reg_status.pack(anchor="w", padx=24)

        # 항목 3: 설정 폴더
        self.chk_settings = tk.Checkbutton(
            body_frame,
            text="사용자 설정 및 서식 캐시 폴더 삭제 (%APPDATA%\\HwpAutoDocFit)",
            variable=self.var_settings,
            font=self.font_desc,
            bg="#FFFFFF",
            activebackground="#FFFFFF",
        )
        self.chk_settings.pack(anchor="w", pady=3)
        self.lbl_settings_status = tk.Label(body_frame, text="상태 확인 중...", font=self.font_desc, fg="#64748B", bg="#FFFFFF")
        self.lbl_settings_status.pack(anchor="w", padx=24)

        # 하단 작업 로그창
        log_frame = tk.Frame(self.root, bg="#F8F9FA", padx=15)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.txt_log = tk.Text(log_frame, height=6, font=self.font_text, bg="#F1F5F9", fg="#334155", relief=tk.SOLID, bd=1)
        self.txt_log.pack(fill=tk.BOTH, expand=True, pady=4)

        # 버튼 프레임
        btn_frame = tk.Frame(self.root, bg="#F8F9FA", padx=15, pady=10)
        btn_frame.pack(fill=tk.X)

        self.btn_refresh = tk.Button(btn_frame, text="상태 다시 확인", command=self._상태_갱신, font=self.font_desc, bg="#E2E8F0", relief=tk.GROOVE, padx=10)
        self.btn_refresh.pack(side=tk.LEFT)

        self.btn_close = tk.Button(btn_frame, text="닫기", command=self.root.destroy, font=self.font_desc, bg="#E2E8F0", relief=tk.GROOVE, padx=12)
        self.btn_close.pack(side=tk.RIGHT, padx=4)

        self.btn_execute = tk.Button(
            btn_frame,
            text="원상복구 실행",
            command=self._실행_클릭,
            font=self.font_bold,
            bg="#DC2626",
            fg="#FFFFFF",
            activebackground="#B91C1C",
            activeforeground="#FFFFFF",
            relief=tk.RAISED,
            padx=16,
            pady=2,
        )
        self.btn_execute.pack(side=tk.RIGHT, padx=4)

    def _상태_갱신(self):
        # DLL 상태
        if TARGET_DLL.exists() or (LEGACY_AUTOMATION_DIR / DLL_NAME).exists():
            self.lbl_dll_status.config(text="● 파일 존재함 (삭제 대상)", fg="#DC2626")
            self.var_dll.set(True)
        else:
            self.lbl_dll_status.config(text="○ 파일 없음 (이미 원상태)", fg="#059669")
            self.var_dll.set(False)

        # 레지스트리 상태
        if 레지스트리_등록_확인():
            self.lbl_reg_status.config(text="● 등록되어 있음 (삭제 대상)", fg="#DC2626")
            self.var_reg.set(True)
        else:
            self.lbl_reg_status.config(text="○ 등록되어 있지 않음 (이미 원상태)", fg="#059669")
            self.var_reg.set(False)

        # 설정 폴더 상태
        folders = 설정_폴더_목록()
        if folders:
            self.lbl_settings_status.config(text=f"● 폴더 존재함 ({len(folders)}곳, 삭제 대상)", fg="#D97706")
            self.var_settings.set(True)
        else:
            self.lbl_settings_status.config(text="○ 폴더 없음 (이미 원상태)", fg="#059669")
            self.var_settings.set(False)

        self._로그("시스템 구성 요소 상태를 확인했습니다.")

    def _로그(self, msg: str):
        self.txt_log.insert(tk.END, msg + "\n")
        self.txt_log.see(tk.END)

    def _실행_클릭(self):
        do_dll = self.var_dll.get()
        do_reg = self.var_reg.get()
        do_settings = self.var_settings.get()

        if not (do_dll or do_reg or do_settings):
            messagebox.showinfo("알림", "선택된 원상복구 대상이 없습니다.", parent=self.root)
            return

        if 한글_실행_중인가():
            if not messagebox.askyesno(
                "한/글 실행 중 감지",
                "한컴오피스 한/글이 현재 실행 중입니다.\n"
                "한/글이 실행 중인 경우 보안 DLL 파일이 잠겨 있어 삭제되지 않을 수 있습니다.\n\n"
                "한/글을 종료한 후 진행하는 것을 권장합니다.\n"
                "그래도 계속 진행하시겠습니까?",
                parent=self.root,
            ):
                return

        if not messagebox.askyesno(
            "초기화 확인",
            "선택한 항목들을 원상복구(삭제)하시겠습니까?\n"
            "이 작업은 되돌릴 수 없습니다.",
            parent=self.root,
        ):
            return

        self._로그("\n[초기화 작업 시작]")
        success, logs = 전체_원상복구(dll=do_dll, reg=do_reg, settings=do_settings)
        for line in logs:
            self._로그(line)

        self._상태_갱신()

        if success:
            messagebox.showinfo("완료", "원상복구 작업이 성공적으로 완료되었습니다.", parent=self.root)
        else:
            messagebox.showwarning("주의", "일부 항목 삭제 중 오류가 발생했습니다.\n로그를 확인해 주세요.", parent=self.root)


# ============================================================
# CLI 진입점
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="한글 문서편집 자동화 도구 원상복구 및 초기화")
    parser.add_argument("--silent", "-s", action="store_true", help="화면 표시 없이 즉시 원상복구 수행")
    parser.add_argument("--no-dll", action="store_true", help="DLL 파일 삭제 건너뛰기")
    parser.add_argument("--no-reg", action="store_true", help="레지스트리 삭제 건너뛰기")
    parser.add_argument("--no-settings", action="store_true", help="사용자 설정 삭제 건너뛰기")
    args = parser.parse_args()

    if args.silent:
        success, logs = 전체_원상복구(
            dll=not args.no_dll,
            reg=not args.no_reg,
            settings=not args.no_settings,
        )
        for line in logs:
            print(line)
        sys.exit(0 if success else 1)
    else:
        root = tk.Tk()
        app = ResetAppUI(root)
        root.mainloop()


if __name__ == "__main__":
    main()
