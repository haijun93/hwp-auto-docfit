# Windows 시제품 빌드

Windows x64, Visual Studio C++ 데스크톱 도구, Flutter 3.47.5, Python 3.12가 필요하다. requirements.txt 및 PyInstaller 설치 후 저장소 루트에서 실행한다.

```powershell
./build_native.ps1 -Flutter flutter -Python python -Output dist-native
```

설치 의존성 검사 → Flutter 잠금 파일 확인·정적 검사·시험 → Windows Release → 별도 Python PyInstaller onedir → prototype 번들을 생성한다. 기존 prototype 출력이 있으면 새 출력 경로를 요구한다. 네이티브 앱 옆 backend/HWP_AutoDocFit_Backend.exe를 실행한다. manifest는 native-prototype, engine_ready=false이며 SHA256SUMS를 별도로 생성한다.

.github/workflows/build-native-prototype.yml은 수동 Windows 빌드용이다. 아직 실행 결과를 확인하지 못했다. Linux에서는 Windows runner·PowerShell 패키징을 검증할 수 없다. COM 파이프라인이 연결되지 않은 번들이므로 정식 릴리스나 기존 기본 EXE 교체용으로 사용하지 않는다.
