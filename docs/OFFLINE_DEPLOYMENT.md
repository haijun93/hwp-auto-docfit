# 폐쇄망(인터넷이 안 되는 PC) 배포 안내

이 앱은 기본으로 **폐쇄망 모드**로 동작합니다. 앱이 스스로 외부 서버에 접속하지 않습니다.

## 무엇이 인터넷 없이 되나요

| 기능 | 필요한 것 | 인터넷 |
|---|---|---|
| 자간 정리·서식 통일·서식 적용·한 번에 적용 | 한컴오피스 한글 | 필요 없음 |
| HWP·HWPX → PDF·JPG·PNG 변환 | 한컴오피스 한글 | 필요 없음 |
| PDF·Office·HWP → HWPX 변환, AI 답변 HWPX 생성, 고급 문서 도구 | kordoc 꾸러미 | 필요 없음 |
| 그림 파일(JPG·PNG)·스캔 쪽 글자 인식(OCR) | OCR 모델(꾸러미에 없음) | 아래 참고 |
| 업데이트 확인 | 인터넷 | 폐쇄망 모드에서는 하지 않음 |

kordoc은 문서를 PC 안에서만 처리합니다. 문서를 외부 서버로 보내지 않습니다.

## 배포 방법

빌드(CI) 결과물 두 개를 **같은 폴더**에 두고 전달합니다.

```
HWP_AutoDocFit.exe
HWP_AutoDocFit_kordoc_runtime.zip   (Node.js 22.23.3 + kordoc 4.21.30, 약 43MB)
```

- 앱은 kordoc 기능을 처음 쓸 때 꾸러미를 `%LOCALAPPDATA%\HwpAutoDocFit\kordoc-runtime\4.21.30`에 풀어 둡니다(약 20초, 한 번만).
- 사용자 폴더에서 실행 파일을 막는 PC라면 꾸러미를 풀어 실행 파일 옆 `kordoc-runtime` 폴더로 두세요. 앱은 이 폴더를 설치 없이 바로 씁니다.
- 꾸러미의 SHA-256은 함께 만들어지는 `.sha256` 파일과 비교해 확인합니다.

## 꾸러미 만들기(인터넷이 되는 빌드 PC)

```powershell
./scripts/build_kordoc_runtime.ps1            # release-assets\HWP_AutoDocFit_kordoc_runtime.zip
```

- Node.js 공식 ZIP을 SHA-256으로 확인하고, kordoc은 `kordoc_pack/package-lock.json`의 무결성 해시로 `npm ci` 합니다.
- AI OCR용 선택 의존성(onnxruntime 등, 약 500MB)과 설치 스크립트는 넣지 않습니다.

## 설정

- **폐쇄망 모드**(설정 → 네트워크, 기본 켬): 업데이트 확인, kordoc 모델 내려받기, npx 내려받기를 하지 않습니다.
  kordoc은 `KORDOC_OFFLINE=1`, `ORT_DISABLE_TELEMETRY=1`로 실행합니다.
- 관리용 환경 변수 `DOCFIT_OFFLINE=1/0`은 설정값보다 우선합니다.

## OCR이 꼭 필요하면

OCR은 기본 꾸러미에 없습니다. 인터넷이 되는 PC에서 kordoc 전체 설치와 `kordoc models --export <폴더>`로
모델을 내보낸 뒤, 폐쇄망 PC의 `%APPDATA%\HwpAutoDocFit\kordoc-models`에 `kordoc models --import`로 넣는 방식이
kordoc이 제공하는 방법입니다(앱 꾸러미만으로는 지원하지 않음).
