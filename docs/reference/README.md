# 참고 자료 (한글 자동화 개발 참고 문서)

이 폴더는 `hwp auto letter spacing.py` / `4444.py`(HWP Auto DocFit) 개발·유지보수 시
참고할 한글(HWP) Automation 공식 자료를 모아둔 것이다.

## pyhwpx

https://martiniifun.github.io/pyhwpx/

한글 OLE Automation(`win32com.client`)을 감싼 파이썬 래퍼 라이브러리 문서 사이트.
`hwp.Run(...)` / `hwp.HAction` / `hwp.HParameterSet` 등 저수준 COM 호출 대신
사용할 수 있는 pythonic 메서드와 사용 예제를 제공한다. 새 기능을 구현하기 전에
동일 기능이 pyhwpx에 이미 함수로 정리되어 있는지 먼저 확인하는 용도로 참고한다.

## 첨부 문서

### `ActionTable_2504.pdf` (52쪽, 2025-04-15 기준)

한글이 지원하는 전체 **Action ID** 표. Action ID, 사용하는 ParameterSet ID,
설명, 비고(단축키 등)로 구성되어 있다.
예: `CharShapeSpacingDecrease`(자간 좁게, Alt+Shift+N),
`CharShapeSpacingIncrease`(자간 넓게, Alt+Shift+W) 등
현재 스크립트의 `hwp.Run("CharShapeSpacingDecrease")` 같은 호출이 바로 이 표에
정의된 Action ID다. 새로운 Action을 `hwp.Run()`으로 호출하려면 이 표에서
정확한 Action ID와 필요한 ParameterSet 여부를 먼저 확인한다.

### `HwpAutomation_2504.pdf` (69쪽, 2025-04-15 기준)

한글 OLE Automation의 전체 **개체 모델(Object Model)** 설명서.
`IHwpObject`(최상위 오브젝트), `IXHwpDocuments`/`IXHwpDocument`(문서 컬렉션/개체),
Property·Method·Event의 개념, C++/VBScript/JavaScript 예제 코드 등을 다룬다.
`win32.Dispatch("HwpFrame.HwpObject")`로 얻는 최상위 객체 아래의 전체 구조와
`RegisterModule`, `XHwpWindows`, `XHwpDocuments` 같은 프로퍼티/메서드의 근거 문서.

### `HwpAutomation_EventHandler_2504.pdf` (6쪽, 2025-04-15 기준)

한글 오토메이션에서 **이벤트 핸들러**를 추가하는 방법(MFC/ATL, Visual C++ 기준).
`IHwpObjectEvents` 인터페이스 구현 방법과 `Quit`, `DocumentBeforeOpen`,
`DocumentAfterOpen`, `DocumentBeforeSave`, `DocumentAfterSave`,
`DocumentBeforeClose`, `DocumentAfterClose`, `DocumentChange` 등
문서 열기/저장/닫기 시점에 발생하는 이벤트 목록과 훅 방법을 설명한다.
Python(`win32com.client`)에서는 `win32com.client.DispatchWithEvents` 또는
pyhwpx가 제공하는 이벤트 연결 방식으로 동일한 이벤트를 받을 수 있으며,
문서 저장/닫기 실패를 감지하거나 진행 상황을 로깅하는 기능을 추가할 때 참고한다.
