# HWP AutoDocFit 2.0.0 — OpenOffice 벤치마킹 및 6-탭 아키텍처 분석 지시서

## 1. 개요
- 목표: https://github.com/pblsketch/openoffice 저장소의 핵심 아키텍처와 기능을 심층 분석하고, 우리 앱(HWP_AutoDocFit 2.0.0)의 장단점 비교 및 2.0에 벤치마킹할 핵심 내용을 도출하여 `docs/OPENOFFICE_BENCHMARK_REPORT.md` 문서로 정리한다.
- 6-탭 통합 UI: [1. 문서편집 | 2. 표템플릿 | 3. 표그림판 | 4. 다이어그램 | 5. 마인드맵 | 6. 파일변환] 구조에 어떻게 OpenOffice의 서식/표/도형 엔진을 반영할지 로드맵을 제시한다.

## 2. 세부 분석 항목
1) OpenOffice (Apache OpenOffice / StarOffice 계열) 주요 아키텍처:
   - UNO(Universal Network Objects) 컴포넌트 모델 및 문서 객체 모델(DOM).
   - Writer(sw): 표(Table) 레이아웃 계산, 셀 자동 맞춤, 테두리 및 배경 렌더링.
   - Draw/Impress: 벡터 도형(Shape), 연결선(Connector), 마인드맵/다이어그램 배치 알고리즘.
   - Filter 시스템: ODF(OpenDocument), OOXML, RTF, PDF 익스포트 파이프라인.
2) 우리 앱(HWP AutoDocFit)과의 비교:
   - HWP AutoDocFit의 강점: 한/글(HWPX) 네이티브 무손실 패치, 공공기관 규범 서식 지능형 학습(kordoc 4.x), 1초대 스마트 캐싱 런처, 한국형 공공 보고서 최적화.
   - HWP AutoDocFit의 약점/보완점: 전역 Undo/Redo 트랜잭션 모델 부재, 탭 간 서식 상속 체계 부재, 복합 표 수식/스타일 캐스케이딩 미흡.
3) 2.0 6-탭에 벤치마킹할 구체적 개선 사항:
   - 탭 1 (문서편집): OpenOffice 스타일 시트(Paragraph/Character Styles) 계층 구조 적용.
   - 탭 2 (표템플릿): 표 자동 서식(AutoFormat Table) 프리셋 및 오늘 구현된 PPT 스타일 리본과의 융합.
   - 탭 3 (표그림판) & 탭 4 (다이어그램): 드로잉 객체 모델(SdrObject)의 스냅 가이드 및 도형 자석 결합(Magnetic Snapping).
   - 탭 5 (마인드맵): 아웃라인 계층 트리 자동 레이아웃 알고리즘.
   - 탭 6 (파일변환): 백그라운드 필터 파이프라인 및 멀티스레드 배치 변환.

위 내용을 체계적이고 전문적인 마크다운 보고서로 작성하여 `docs/OPENOFFICE_BENCHMARK_REPORT.md`에 저장하라.

