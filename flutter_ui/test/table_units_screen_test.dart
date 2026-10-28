import 'dart:async';
import 'package:docfit_ui/core/api/table_units_api.dart';
import 'package:docfit_ui/features/table_units/table_grid_preview.dart';
import 'package:docfit_ui/features/table_units/table_units_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

const samplePngBase64 =
    'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';

Map<String, Object?> envelope(Map<String, Object?> data) => {
  'api_version': 1,
  'ok': true,
  'data': data,
  'error': null,
};

Map<String, Object?> errorEnvelope(String code, String message) => {
  'api_version': 1,
  'ok': false,
  'error': {'code': code, 'message': message, 'recoverable': true},
};

Map<String, Object?> samplePreview({
  int rows = 3,
  int cols = 2,
  List<Map<String, Object?>>? nestedInFirstCell,
  Map<String, List<Map<String, Object?>>>? shapesByCell,
}) => {
  'rows': rows,
  'cols': cols,
  'cell_meta': [
    for (int r = 0; r < rows; r++)
      [
        for (int c = 0; c < cols; c++)
          {
            'row': r,
            'col': c,
            'rowSpan': 1,
            'colSpan': 1,
            'width': 1000.0,
            'height': 500.0,
            'text': '셀 $r-$c',
            'align': 'center',
            'style': {
              'font': '함초롬바탕',
              'size': 10.0,
              'bold': false,
              'color': '#000000',
              'fill': '#FFFFFF',
            },
            'borders': {
              'top': {'type': 'SOLID', 'width': 0.12, 'color': '#000000'},
              'bottom': {'type': 'SOLID', 'width': 0.12, 'color': '#000000'},
              'left': {'type': 'SOLID', 'width': 0.12, 'color': '#000000'},
              'right': {'type': 'SOLID', 'width': 0.12, 'color': '#000000'},
            },
            if (r == 0 && c == 0 && nestedInFirstCell != null)
              'nested': nestedInFirstCell,
            if (shapesByCell != null && shapesByCell['$r,$c'] != null)
              'shapes': shapesByCell['$r,$c'],
          },
      ],
  ],
};

const publicFixtures = [
  {
    'id': 'pub_summary_headline',
    'category': '공공 표준',
    'name': '① 요약/헤드라인 1칸 표',
    'rows': 1,
    'cols': 1,
    'thumbnail': null,
    'favorite': false,
    'badge': '핵심 요약',
    'description': '상하 0.4mm 굵은선, 좌우 개방형, 연청색 음영의 핵심 요약 콜아웃 상자',
    'guideline': {
      'margins': '좌우 4.0mm / 상하 2.5mm',
      'borders': '상하 실선 0.4mm (#1A365D), 좌우 선없음',
      'font': '한컴돋움 10.5pt / 줄간격 140% / 자간 -5%',
      'fill': '소프트블루 (#EBF3FA, 12%)',
    },
    'units': {'row': null, 'col': null},
  },
  {
    'id': 'pub_two_col_definition',
    'category': '공공 표준',
    'name': '② 2열 정의/대비 표',
    'rows': 4,
    'cols': 2,
    'thumbnail': null,
    'favorite': false,
    'badge': '개요 양식',
    'description': '좌측 항목 22% 연회색 음영, 우측 세부내용 78% 정렬의 표준 개요 양식',
    'guideline': {
      'margins': '좌우 2.5mm / 상하 1.2mm',
      'borders': '상하 0.4mm, 좌우 개방, 내부 0.12mm (#E2E8F0)',
      'font': '항목 한컴돋움 9.5pt Bold / 본문 휴먼명조 9.5pt / 줄간격 130%',
      'fill': '항목열 연회색 (#F2F4F7) / 내용열 흰색',
    },
    'units': {
      'row': {'count': 4, 'min': 1, 'max': 30, 'core': 1, 'sep': 0},
      'col': null,
    },
  },
  {
    'id': 'pub_multi_col_comparison',
    'category': '공공 표준',
    'name': '③ 3~4열 다단 비교/평가 표',
    'rows': 5,
    'cols': 4,
    'thumbnail': null,
    'favorite': false,
    'badge': '비교·평가',
    'description': '머리글 다크네이비/연청, 본문 지브라 교차 음영, 최하단 합계 행',
    'guideline': {
      'margins': '좌우 2.5mm / 상하 1.2mm',
      'borders': '상단 0.4mm, 머리글하단 이중선 0.5mm, 하단 0.4mm',
      'font': '머리글 한컴돋움 9.5pt Bold / 본문 휴먼명조 9.0pt / 줄간격 130%',
      'fill': '머리글 (#DFE6F7) / 지브라 (#F8FAFC) / 합계 (#ECEEF2)',
    },
    'units': {
      'row': {'count': 3, 'min': 1, 'max': 30, 'core': 1, 'sep': 0},
      'col': null,
    },
  },
  {
    'id': 'pub_gantt_timeline',
    'category': '공공 표준',
    'name': '④ 추진 일정/간트차트형 표',
    'rows': 5,
    'cols': 6,
    'thumbnail': null,
    'favorite': false,
    'badge': '추진 일정',
    'description': '월별/분기별 타임라인 바 셀 채우기 색상 규격이 적용된 로드맵 표',
    'guideline': {
      'margins': '좌우 1.0mm / 상하 1.0mm (타임라인 밀착)',
      'borders': '상단 0.4mm, 머리글 이중선 0.5mm, 타임라인 내부 점선(DOT)',
      'font': '한컴돋움 9.0~9.5pt / 줄간격 130% / 가운데 정렬',
      'fill': '머리글 (#E7EEF8) / 추진바 (#1A365D, 폰트 흰색)',
    },
    'units': {
      'row': {'count': 4, 'min': 1, 'max': 30, 'core': 1, 'sep': 0},
      'col': {'count': 4, 'min': 2, 'max': 12, 'core': 1, 'sep': 0},
    },
  },
  {
    'id': 'pub_budget_breakdown',
    'category': '공공 표준',
    'name': '⑤ 예산/소요비용 산출 내역 표',
    'rows': 5,
    'cols': 5,
    'thumbnail': null,
    'favorite': false,
    'badge': '재정·회계 서식',
    'description': '금액 우측정렬, 3자리 콤마, 하단 합계 이중선 마감의 표준 예산 표',
    'guideline': {
      'margins': '좌우 2.5mm / 상하 1.2mm',
      'borders': '상단 0.4mm, 머리글 이중선 0.5mm, 하단 합계 이중선 0.5mm',
      'font': '비목 휴먼명조 9.0pt / 수치 맑은 고딕 9.0pt 우측정렬 / 합계 한컴돋움 Bold / 줄간격 130%',
      'fill': '머리글 (#F2F4F7) / 합계행 (#E2E8F0)',
    },
    'units': {
      'row': {'count': 3, 'min': 1, 'max': 30, 'core': 1, 'sep': 0},
      'col': null,
    },
  },
  {
    'id': 'pub_qa_checklist',
    'category': '공공 표준',
    'name': '⑥ 질의응답(Q&A) / 체크리스트 표',
    'rows': 4,
    'cols': 4,
    'thumbnail': null,
    'favorite': false,
    'badge': '감사·점검',
    'description': '문항 No, 점검 기준, 적합/부적합 판정 뱃지가 구비된 감사/진단용 표',
    'guideline': {
      'margins': '좌우 2.5mm / 상하 1.2mm',
      'borders': '상단 0.4mm, 머리글 이중선 0.5mm, 하단 0.4mm, 좌우 개방',
      'font': '한컴돋움 9.0~9.5pt / 줄간격 130% / 판정 뱃지 폰트 색상 매칭',
      'fill': '머리글 (#F0F4F8) / 적합 (#E6F4EA, 녹색) / 주의 (#FCE8E6, 적색)',
    },
    'units': {
      'row': {'count': 3, 'min': 1, 'max': 30, 'core': 1, 'sep': 0},
      'col': null,
    },
  },
];

Map<String, Object?> sampleListData({
  bool thumbnailsReady = true,
  List<String>? recent,
  bool includePublic = false,
}) => {
  'source': 'C:/HWP_AUTODOCFIT/templates.hwpx',
  'thumbnails_ready': thumbnailsReady,
  'recent': recent ?? ['0:3', '0:1'],
  'templates': [
    {
      'id': '0:1',
      'category': '과제표',
      'name': '분야별 과제표',
      'rows': 3,
      'cols': 4,
      'thumbnail': samplePngBase64,
      'favorite': false,
      'units': {
        'row': {'count': 3, 'min': 1, 'max': 5, 'core': 1, 'sep': 0},
        'col': null,
      },
    },
    {
      'id': '0:2',
      'category': '서약서',
      'name': '서약서 고정 표',
      'rows': 2,
      'cols': 2,
      'thumbnail': null,
      'favorite': true,
      'units': {'row': null, 'col': null},
    },
    {
      'id': '0:3',
      'category': '일정표',
      'name': '월간 일정표',
      'rows': 4,
      'cols': 6,
      'thumbnail': null,
      'favorite': false,
      'units': {
        'row': null,
        'col': {'count': 2, 'min': 1, 'max': 4, 'core': 1, 'sep': 0},
      },
    },
    if (includePublic) ...publicFixtures,
  ],
};

Future<void> pumpScreen(
  WidgetTester tester, {
  required ApiCall api,
  double width = 1000.0,
  double height = 800.0,
}) async {
  tester.view.physicalSize = Size(width, height);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);

  await tester.pumpWidget(MaterialApp(home: TableUnitsScreen(key: ValueKey(api), api: api)));
  await tester.pumpAndSettle();
}

/// 고른 이름 버튼은 진한 바탕에 흰 글자(촘촘한 자판형 이름 줄).
bool isHighlighted(WidgetTester tester, Finder button) {
  final text = tester.widget<Text>(
    find.descendant(of: button, matching: find.byType(Text)),
  );
  return text.style?.color == Colors.white;
}

void main() {
  testWidgets('목록 로드, 첫 번째 템플릿 자동 선택 및 preview 호출', (tester) async {
    final calls = <List<Object?>>[];
    Future<Object?> api(String name, List<Object?> args) async {
      calls.add([name, ...args]);
      final action = args[0] as String;
      if (action == 'list') {
        return envelope(sampleListData());
      }
      if (action == 'preview') {
        return envelope(samplePreview(rows: 3, cols: 4));
      }
      return envelope({});
    }

    await pumpScreen(tester, api: api);

    expect(find.text('표 템플릿'), findsOneWidget);
    expect(find.text('분야별 과제표'), findsWidgets);
    expect(find.byKey(const Key('tableGridPreview')), findsOneWidget);

    expect(calls.any((c) => c[0] == 'table_units' && c[1] == 'list'), isTrue);
    expect(
      calls.any((c) => c[0] == 'table_units' && c[1] == 'preview'),
      isTrue,
    );
  });

  testWidgets('검색창 검색어 필터링 (이름·분류 부분 일치) 및 분류 칩과 연동', (tester) async {
    Future<Object?> api(String name, List<Object?> args) async {
      final action = args[0] as String;
      if (action == 'list') return envelope(sampleListData());
      if (action == 'preview') return envelope(samplePreview());
      return envelope({});
    }

    await pumpScreen(tester, api: api);

    // 1. 이름 검색: '월간' 입력
    final searchField = find.byKey(const Key('searchTextField'));
    expect(searchField, findsOneWidget);
    await tester.enterText(searchField, '월간');
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('templateCard_0:3')), findsOneWidget);
    expect(find.byKey(const Key('templateCard_0:1')), findsNothing);
    expect(find.byKey(const Key('templateCard_0:2')), findsNothing);

    // 2. 분류 검색: '과제' 입력
    await tester.enterText(searchField, '과제');
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('templateCard_0:1')), findsOneWidget);
    expect(find.byKey(const Key('templateCard_0:3')), findsNothing);

    // 3. 분류 칩 '서약서' 선택 후 검색창에 '과제' -> 불일치로 결과 없음
    await tester.ensureVisible(find.byKey(const Key('categoryChip_서약서')));
    await tester.tap(find.byKey(const Key('categoryChip_서약서')));
    await tester.pumpAndSettle();

    expect(find.text('표 템플릿이 없습니다.'), findsOneWidget);

    // 검색어를 비우면 '서약서' 칩에 맞는 카드 표시
    await tester.enterText(searchField, '');
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('templateCard_0:2')), findsOneWidget);
  });

  testWidgets('즐겨찾기 토글 호출 및 즐겨찾기 칩 거르기', (tester) async {
    final calls = <List<Object?>>[];
    Future<Object?> api(String name, List<Object?> args) async {
      calls.add([name, ...args]);
      final action = args[0] as String;
      if (action == 'list') return envelope(sampleListData());
      if (action == 'preview') return envelope(samplePreview());
      if (action == 'favorite') {
        final payload = args[1] as Map;
        final list = sampleListData();
        final templates = (list['templates'] as List)
            .cast<Map<String, Object?>>();
        for (final t in templates) {
          if (t['id'] == payload['id']) {
            t['favorite'] = payload['on'];
          }
        }
        return envelope(list);
      }
      return envelope({});
    }

    await pumpScreen(tester, api: api);

    // 0:1 템플릿의 별 버튼 클릭
    final favBtn = find.byKey(const Key('btnFavorite_0:1'));
    expect(favBtn, findsOneWidget);
    await tester.tap(favBtn);
    await tester.pumpAndSettle();

    // favorite API 호출 검증
    final favCalls = calls.where(
      (c) =>
          c[0] == 'table_units' &&
          c[1] == 'favorite' &&
          (c[2] as Map)['id'] == '0:1' &&
          (c[2] as Map)['on'] == true,
    );
    expect(favCalls, isNotEmpty);

    // '즐겨찾기' 칩 클릭
    await tester.tap(find.byKey(const Key('categoryChip_즐겨찾기')));
    await tester.pumpAndSettle();

    // 0:1(방금 켬)과 0:2(초기 즐겨찾기) 모두 보여야 함
    expect(find.byKey(const Key('templateCard_0:1')), findsOneWidget);
    expect(find.byKey(const Key('templateCard_0:2')), findsOneWidget);
    expect(find.byKey(const Key('templateCard_0:3')), findsNothing);
  });

  testWidgets('최근 사용 칩 클릭 시 recent 순서대로 정렬 표시', (tester) async {
    Future<Object?> api(String name, List<Object?> args) async {
      final action = args[0] as String;
      if (action == 'list') {
        return envelope(sampleListData(recent: ['0:3', '0:1']));
      }
      if (action == 'preview') return envelope(samplePreview());
      return envelope({});
    }

    await pumpScreen(tester, api: api);

    // '최근 사용' 칩 클릭
    await tester.tap(find.byKey(const Key('categoryChip_최근 사용')));
    await tester.pumpAndSettle();

    // recent에 없는 0:2는 보이지 않아야 함
    expect(find.byKey(const Key('templateCard_0:2')), findsNothing);
    expect(find.byKey(const Key('templateCard_0:3')), findsOneWidget);
    expect(find.byKey(const Key('templateCard_0:1')), findsOneWidget);

    // 순서: 0:3이 0:1보다 먼저 위치해야 함 (x 또는 y 좌표 비교)
    final pos3 = tester.getTopLeft(find.byKey(const Key('templateCard_0:3')));
    final pos1 = tester.getTopLeft(find.byKey(const Key('templateCard_0:1')));
    expect(pos3.dx, lessThan(pos1.dx));
  });

  testWidgets('글 처리 방식(fill) 선택 시 preview 인자 전달 및 다시 호출', (tester) async {
    final calls = <List<Object?>>[];
    Future<Object?> api(String name, List<Object?> args) async {
      calls.add([name, ...args]);
      final action = args[0] as String;
      if (action == 'list') return envelope(sampleListData());
      if (action == 'preview') return envelope(samplePreview());
      return envelope({});
    }

    await pumpScreen(tester, api: api);

    // 첫 로드 시 preview 인자에 fill: 'increment' 확인
    final firstPreview = calls.lastWhere(
      (c) => c[0] == 'table_units' && c[1] == 'preview',
    );
    expect((firstPreview[2] as Map)['fill'], 'increment');

    // '비우기' 선택
    await tester.ensureVisible(find.byKey(const Key('fillOption_blank')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('fillOption_blank')));
    await tester.pumpAndSettle();

    final blankPreview = calls.lastWhere(
      (c) => c[0] == 'table_units' && c[1] == 'preview',
    );
    expect((blankPreview[2] as Map)['fill'], 'blank');

    // '그대로' 선택
    await tester.ensureVisible(find.byKey(const Key('fillOption_copy')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('fillOption_copy')));
    await tester.pumpAndSettle();

    final copyPreview = calls.lastWhere(
      (c) => c[0] == 'table_units' && c[1] == 'preview',
    );
    expect((copyPreview[2] as Map)['fill'], 'copy');
  });

  testWidgets('칸 눌러 글 입력 -> cell_texts 인자 전달 및 모두 지우기', (tester) async {
    final calls = <List<Object?>>[];
    Future<Object?> api(String name, List<Object?> args) async {
      calls.add([name, ...args]);
      final action = args[0] as String;
      if (action == 'list') return envelope(sampleListData());
      if (action == 'preview') return envelope(samplePreview());
      return envelope({});
    }

    await pumpScreen(tester, api: api);

    // 미리보기 위젯의 좌측 상단(0행 0열)을 탭하여 다이얼로그 열기
    final previewWidget = find.byType(TableGridPreview);
    expect(previewWidget, findsOneWidget);
    final contentFinder = find.byKey(const Key('tableGridContent'));
    final target = contentFinder.evaluate().isNotEmpty
        ? tester.getTopLeft(contentFinder)
        : tester.getTopLeft(previewWidget);
    await tester.tapAt(target + const Offset(20, 20));
    await tester.pumpAndSettle();

    // 글 입력 창이 나타났는지 확인
    final cellInput = find.byKey(const Key('cellTextInputField'));
    expect(cellInput, findsOneWidget);

    await tester.enterText(cellInput, '새로운 과제명');
    await tester.tap(find.byKey(const Key('btnSaveCellText')));
    await tester.pumpAndSettle();

    // preview 호출에 cell_texts 반영 확인
    final lastPreview = calls.lastWhere(
      (c) => c[0] == 'table_units' && c[1] == 'preview',
    );
    final texts = (lastPreview[2] as Map)['cell_texts'] as Map?;
    expect(texts, isNotNull);
    expect(texts!['0,0'], '새로운 과제명');

    // '입력한 글 모두 지우기' 버튼 확인 및 클릭
    final clearBtn = find.byKey(const Key('btnClearCellTexts'));
    expect(clearBtn, findsOneWidget);
    await tester.tap(clearBtn);
    await tester.pumpAndSettle();

    final clearedPreview = calls.lastWhere(
      (c) => c[0] == 'table_units' && c[1] == 'preview',
    );
    final clearedTexts = (clearedPreview[2] as Map)['cell_texts'] as Map?;
    expect(clearedTexts == null || clearedTexts.isEmpty, isTrue);
  });

  testWidgets('복사 시 activated 응답에 따른 안내 문구 2가지 (true vs false)', (
    tester,
  ) async {
    // 1. activated == true 케이스
    Future<Object?> apiActivatedTrue(String name, List<Object?> args) async {
      final action = args[0] as String;
      if (action == 'list') return envelope(sampleListData());
      if (action == 'preview') return envelope(samplePreview());
      if (action == 'copy') {
        return envelope({'copied': true, 'message': 'OK', 'activated': true});
      }
      return envelope({});
    }

    await pumpScreen(tester, api: apiActivatedTrue);
    await tester.ensureVisible(find.byKey(const Key('btnCopyTable')));
    await tester.tap(find.byKey(const Key('btnCopyTable')));
    await tester.pump();
    await tester.pumpAndSettle();

    expect(find.text('한/글 창을 앞으로 가져왔어요. Ctrl+V로 붙여넣으세요.'), findsOneWidget);

    // 2. activated == false 케이스
    await tester.pumpWidget(const SizedBox());

    Future<Object?> apiActivatedFalse(String name, List<Object?> args) async {
      final action = args[0] as String;
      if (action == 'list') return envelope(sampleListData());
      if (action == 'preview') return envelope(samplePreview());
      if (action == 'copy') {
        return envelope({'copied': true, 'message': 'OK', 'activated': false});
      }
      return envelope({});
    }

    await pumpScreen(tester, api: apiActivatedFalse);
    await tester.ensureVisible(find.byKey(const Key('btnCopyTable')));
    await tester.tap(find.byKey(const Key('btnCopyTable')));
    await tester.pump();
    await tester.pumpAndSettle();

    expect(find.text('한/글 문서에서 붙여넣을 곳을 누르고 Ctrl+V 하세요.'), findsOneWidget);
  });

  testWidgets('nested 표가 포함된 preview 렌더링 시 예외 없음', (tester) async {
    final nestedData = [samplePreview(rows: 2, cols: 2)];
    Future<Object?> api(String name, List<Object?> args) async {
      final action = args[0] as String;
      if (action == 'list') return envelope(sampleListData());
      if (action == 'preview') {
        return envelope(
          samplePreview(rows: 3, cols: 3, nestedInFirstCell: nestedData),
        );
      }
      return envelope({});
    }

    await pumpScreen(tester, api: api);

    expect(tester.takeException(), isNull);
    expect(find.byType(TableGridPreview), findsOneWidget);
  });

  testWidgets('스테퍼 [+]/[-] 동작, max 제한에서 [+] 꺼짐, preview 인자 반영', (tester) async {
    final calls = <List<Object?>>[];
    Future<Object?> api(String name, List<Object?> args) async {
      calls.add([name, ...args]);
      final action = args[0] as String;
      if (action == 'list') return envelope(sampleListData());
      if (action == 'preview') {
        final payload = args[1] as Map;
        final rows = (payload['row_count'] as num?)?.toInt() ?? 3;
        return envelope(samplePreview(rows: rows, cols: 4));
      }
      return envelope({});
    }

    await pumpScreen(tester, api: api);

    expect(find.text('행 단위 3개'), findsOneWidget);

    final plusBtn = find.byKey(const Key('btnRowPlus'));
    final minusBtn = find.byKey(const Key('btnRowMinus'));

    await tester.tap(plusBtn);
    await tester.pumpAndSettle();
    expect(find.text('행 단위 4개'), findsOneWidget);

    await tester.tap(plusBtn);
    await tester.pumpAndSettle();
    expect(find.text('행 단위 5개'), findsOneWidget);

    final plusWidget = tester.widget<IconButton>(plusBtn);
    expect(plusWidget.onPressed, isNull);

    await tester.tap(minusBtn);
    await tester.pumpAndSettle();
    expect(find.text('행 단위 4개'), findsOneWidget);

    final lastPreview = calls.lastWhere(
      (c) => c[0] == 'table_units' && c[1] == 'preview',
    );
    expect((lastPreview[2] as Map)['row_count'], 4);
  });

  testWidgets('고정 표는 안내 문구 표시 및 스테퍼 없음', (tester) async {
    Future<Object?> api(String name, List<Object?> args) async {
      final action = args[0] as String;
      if (action == 'list') return envelope(sampleListData());
      if (action == 'preview') return envelope(samplePreview(rows: 2, cols: 2));
      return envelope({});
    }

    await pumpScreen(tester, api: api);

    await tester.tap(find.byKey(const Key('templateCard_0:2')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('fixedTableNotice')), findsOneWidget);
    expect(find.text('이 표는 정보단위 조절 없이 그대로 복사해요'), findsOneWidget);
    expect(find.byKey(const Key('btnRowMinus')), findsNothing);
    expect(find.byKey(const Key('btnRowPlus')), findsNothing);
  });

  testWidgets('API 오류 발생 시 화면 및 복사 오류 메시지 표시', (tester) async {
    Future<Object?> failApi(String name, List<Object?> args) async {
      return errorEnvelope('LOAD_FAILED', '목록을 불러올 수 없습니다.');
    }

    await pumpScreen(tester, api: failApi);
    expect(find.byKey(const Key('errorMessage')), findsOneWidget);
    expect(find.text('목록을 불러올 수 없습니다.'), findsOneWidget);

    Future<Object?> copyFailApi(String name, List<Object?> args) async {
      final action = args[0] as String;
      if (action == 'list') return envelope(sampleListData());
      if (action == 'preview') return envelope(samplePreview());
      if (action == 'copy') {
        return errorEnvelope('CLIPBOARD_ERROR', '한/글 복사 중 오류가 발생했습니다.');
      }
      return envelope({});
    }

    await tester.pumpWidget(const SizedBox());
    await pumpScreen(tester, api: copyFailApi);
    await tester.ensureVisible(find.byKey(const Key('btnCopyTable')));
    await tester.tap(find.byKey(const Key('btnCopyTable')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('copyErrorMessage')), findsOneWidget);
    expect(find.text('한/글 복사 중 오류가 발생했습니다.'), findsOneWidget);
  });

  testWidgets('base64 스냅샷이 있으면 Image 위젯 표시', (tester) async {
    Future<Object?> api(String name, List<Object?> args) async {
      final action = args[0] as String;
      if (action == 'list') return envelope(sampleListData());
      if (action == 'preview') return envelope(samplePreview());
      return envelope({});
    }

    await pumpScreen(tester, api: api);
    expect(find.byType(Image), findsWidgets);
  });

  testWidgets('thumbnails_ready false이면 화면을 열 때 그림을 자동으로 한 번 만든다', (
    tester,
  ) async {
    final calls = <List<Object?>>[];
    Future<Object?> api(String name, List<Object?> args) async {
      calls.add([name, ...args]);
      final action = args[0] as String;
      if (action == 'list') {
        return envelope(sampleListData(thumbnailsReady: false));
      }
      if (action == 'thumbnails') {
        return envelope(sampleListData(thumbnailsReady: true));
      }
      if (action == 'preview') return envelope(samplePreview());
      return envelope({});
    }

    await pumpScreen(tester, api: api);

    expect(
      calls.where((c) => c[0] == 'table_units' && c[1] == 'thumbnails').length,
      1,
    );
    expect(find.byKey(const Key('thumbnailsNotice')), findsNothing);
    expect(find.byKey(const Key('btnGenerateThumbnails')), findsOneWidget);
  });

  testWidgets(
    '중복 상단 메뉴(templateNameBar)가 삭제되고 좌측 갤러리 카드에서 직접 선택 및 미리보기가 작동한다',
    (tester) async {
      Future<Object?> api(String name, List<Object?> args) async {
        final action = args[0] as String;
        if (action == 'list') return envelope(sampleListData());
        if (action == 'preview') return envelope(samplePreview());
        return envelope({});
      }

      await pumpScreen(tester, api: api);

      expect(find.byKey(const Key('templateNameBar')), findsNothing);

      final card1 = find.byKey(const Key('templateCard_0:1'));
      final card2 = find.byKey(const Key('templateCard_0:2'));
      final card3 = find.byKey(const Key('templateCard_0:3'));
      expect(card1, findsOneWidget);
      expect(card2, findsOneWidget);
      expect(card3, findsOneWidget);

      await tester.tap(card2);
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('fixedTableNotice')), findsOneWidget);

      await tester.tap(card3);
      await tester.pumpAndSettle();
      expect(find.text('월간 일정표'), findsWidgets);
    },
  );

  testWidgets('모든 분류 칩이 PPT 스타일 가로 1줄 리본으로 단정하게 배치되어 스크롤 가능', (tester) async {
    final listWithManyCats = sampleListData();
    final templates = (listWithManyCats['templates'] as List)
        .cast<Map<String, Object?>>();
    templates.add({
      'id': '0:4',
      'category': '사진첨부용',
      'name': '사진 첨부 표',
      'rows': 2,
      'cols': 2,
      'thumbnail': null,
      'favorite': false,
      'units': {'row': null, 'col': null},
    });

    Future<Object?> api(String name, List<Object?> args) async {
      final action = args[0] as String;
      if (action == 'list') return envelope(listWithManyCats);
      if (action == 'preview') return envelope(samplePreview());
      return envelope({});
    }

    await pumpScreen(tester, api: api, width: 420.0, height: 800.0);

    final expectedCats = ['즐겨찾기', '최근 사용', '전체', '과제표', '서약서', '일정표', '사진첨부용'];
    for (final cat in expectedCats) {
      final chipFinder = find.byKey(Key('categoryChip_$cat'));
      expect(chipFinder, findsOneWidget);
    }

    final chip1 = find.byKey(const Key('categoryChip_즐겨찾기'));
    final chip2 = find.byKey(const Key('categoryChip_최근 사용'));
    final chip3 = find.byKey(const Key('categoryChip_전체'));
    expect(tester.getTopLeft(chip1).dy, equals(tester.getTopLeft(chip2).dy));
    expect(tester.getTopLeft(chip2).dy, equals(tester.getTopLeft(chip3).dy));

    expect(find.byKey(const Key('btnCategoryRibbonLeft')), findsOneWidget);
    expect(find.byKey(const Key('btnCategoryRibbonRight')), findsOneWidget);
    await tester.tap(find.byKey(const Key('btnCategoryRibbonRight')));
    await tester.pumpAndSettle();
  });

  testWidgets(
    'shapes(arrow right/down)가 있는 미리보기에서 화살표 그리기 레이어 및 TableShapesPainter 호출',
    (tester) async {
      final shapesData = <String, List<Map<String, Object?>>>{
        '0,0': [
          {'type': 'arrow', 'direction': 'right', 'color': '#2563EB'},
        ],
        '1,0': [
          {'type': 'arrow', 'direction': 'down', 'color': '#EF4444'},
        ],
      };

      Future<Object?> api(String name, List<Object?> args) async {
        final action = args[0] as String;
        if (action == 'list') return envelope(sampleListData());
        if (action == 'preview') {
          return envelope(samplePreview(rows: 2, cols: 2, shapesByCell: shapesData));
        }
        return envelope({});
      }

      await pumpScreen(tester, api: api);

      expect(find.byKey(const Key('tableGridContent')), findsOneWidget);
      expect(find.byType(CustomPaint), findsWidgets);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    '상단 메뉴 삭제 후 넓은 세로 캔버스가 확보되고 상단 즉시 복사 버튼(btnTopCopyTable)이 제공된다',
    (tester) async {
      final copyCalls = <Map<String, Object?>>[];
      Future<Object?> api(String name, List<Object?> args) async {
        final action = args[0] as String;
        if (action == 'list') return envelope(sampleListData());
        if (action == 'preview') return envelope(samplePreview());
        if (action == 'copy') {
          copyCalls.add({'action': action, 'args': args});
          return envelope({'ok': true, 'activated': true});
        }
        return envelope({});
      }

      await pumpScreen(tester, api: api, width: 1000.0, height: 800.0);

      expect(find.byKey(const Key('templateNameBar')), findsNothing);
      expect(find.byKey(const Key('btnTopCopyTable')), findsOneWidget);
      expect(find.byKey(const Key('btnCopyTable')), findsOneWidget);

      await tester.tap(find.byKey(const Key('btnTopCopyTable')));
      await tester.pumpAndSettle();
      expect(copyCalls, isNotEmpty);
    },
  );

  testWidgets(
    '좌측 분류 칩 버튼이 상단 메뉴와 동일하게 높이 28px의 컴팩트한 사이즈로 배치되고 전체 스크롤이 작동한다',
    (tester) async {
      Future<Object?> api(String name, List<Object?> args) async {
        final action = args[0] as String;
        if (action == 'list') return envelope(sampleListData());
        if (action == 'preview') return envelope(samplePreview());
        return envelope({});
      }

      await pumpScreen(tester, api: api, width: 1000.0, height: 800.0);

      final chipAll = find.byKey(const Key('categoryChip_전체'));
      expect(chipAll, findsOneWidget);
      expect(tester.getSize(chipAll).height, equals(28.0));

      expect(find.byType(CustomScrollView), findsOneWidget);
      expect(find.byType(Scrollbar), findsWidgets);
    },
  );

  // --- P7 공공 표준 프리셋 정식 결합 위젯 시험 (설계서 9장 명세) ---

  testWidgets('공공 분류는 기존 분류와 함께 나타나고 여섯 프리셋을 필터링한다', (tester) async {
    Future<Object?> api(String name, List<Object?> args) async {
      final action = args[0] as String;
      if (action == 'list') return envelope(sampleListData(includePublic: true));
      if (action == 'preview') return envelope(samplePreview());
      return envelope({});
    }

    await pumpScreen(tester, api: api);

    // 1. 공공 표준 칩 및 아이콘 확인
    final publicChip = find.byKey(const Key('categoryChip_공공 표준'));
    expect(publicChip, findsOneWidget);
    expect(find.byIcon(Icons.account_balance), findsOneWidget);

    // 2. 최초 선택은 기존 첫 번째 항목 (0:1)
    expect(find.text('분야별 과제표'), findsWidgets);

    // 3. 공공 표준 칩 탭 시 공공 6개 필터링
    await tester.ensureVisible(publicChip);
    await tester.tap(publicChip);
    await tester.pumpAndSettle();

    final expectedPubIds = [
      'pub_summary_headline',
      'pub_two_col_definition',
      'pub_multi_col_comparison',
      'pub_gantt_timeline',
      'pub_budget_breakdown',
      'pub_qa_checklist',
    ];
    for (final id in expectedPubIds) {
      expect(find.byKey(Key('templateCard_$id')), findsOneWidget);
    }
    expect(find.byKey(const Key('templateCard_0:1')), findsNothing);

    // 4. 검색창에 '공공' 입력 시 필터링
    final searchField = find.byKey(const Key('searchTextField'));
    await tester.enterText(searchField, '공공');
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('templateCard_pub_two_col_definition')), findsOneWidget);

    // 5. '전체' 칩으로 복귀
    await tester.enterText(searchField, '');
    final allChip = find.byKey(const Key('categoryChip_전체'));
    await tester.ensureVisible(allChip);
    await tester.tap(allChip);
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('templateCard_0:1')), findsOneWidget);
  });

  testWidgets('공공 모델의 선택 메타 필드는 이전 응답과 호환된다', (tester) async {
    // 1. 공공 메타가 포함된 JSON 파싱
    final pubJson = {
      'id': 'pub_two_col_definition',
      'category': '공공 표준',
      'name': '② 2열 정의/대비 표',
      'rows': 4,
      'cols': 2,
      'badge': '개요 양식',
      'description': '좌측 항목 22%',
      'guideline': {
        'margins': '좌우 2.5mm',
        'borders': '상하 0.4mm',
        'font': '돋움',
        'fill': '연회색',
      },
      'units': {'row': {'count': 4, 'min': 1, 'max': 30, 'core': 1, 'sep': 0}},
    };
    final info = TableTemplateInfo.fromJson(pubJson);
    expect(info.badge, '개요 양식');
    expect(info.description, '좌측 항목 22%');
    expect(info.guideline['margins'], '좌우 2.5mm');

    // 2. copyWith 검증
    final copied = info.copyWith(badge: '새 배지');
    expect(copied.badge, '새 배지');
    expect(copied.description, '좌측 항목 22%');
    expect(copied.guideline['margins'], '좌우 2.5mm');

    // 3. 이전 버전 응답 (메타 필드 없음) 기본값 검증
    final legacyJson = {
      'id': '0:1',
      'category': '과제표',
      'name': '분야별 과제표',
      'rows': 3,
      'cols': 4,
    };
    final legacyInfo = TableTemplateInfo.fromJson(legacyJson);
    expect(legacyInfo.badge, '');
    expect(legacyInfo.description, '');
    expect(legacyInfo.guideline, isEmpty);

    // 4. 비맵 또는 비문자 guideline 전달 시 안전 처리
    final badJson = {
      'id': 'bad',
      'category': '기타',
      'name': '오류 양식',
      'rows': 1,
      'cols': 1,
      'guideline': 'not a map',
    };
    final badInfo = TableTemplateInfo.fromJson(badJson);
    expect(badInfo.guideline, isEmpty);
  });

  testWidgets('공공 가이드 표시 후 기존 표 선택 시 사라진다', (tester) async {
    Future<Object?> api(String name, List<Object?> args) async {
      final action = args[0] as String;
      if (action == 'list') return envelope(sampleListData(includePublic: true));
      if (action == 'preview') return envelope(samplePreview());
      return envelope({});
    }

    // 1280px 너비에서 공공 프리셋 선택
    await pumpScreen(tester, api: api, width: 1280.0, height: 800.0);
    final pubChip = find.byKey(const Key('categoryChip_공공 표준'));
    await tester.ensureVisible(pubChip);
    await tester.tap(pubChip);
    await tester.pumpAndSettle();

    final pubCard = find.byKey(const Key('templateCard_pub_two_col_definition'));
    await tester.ensureVisible(pubCard);
    await tester.tap(pubCard);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('publicPresetGuideline')), findsOneWidget);
    expect(find.textContaining('여백:'), findsOneWidget);
    expect(find.textContaining('테두리:'), findsOneWidget);
    expect(find.textContaining('글꼴:'), findsOneWidget);
    expect(find.textContaining('배경:'), findsOneWidget);
    expect(tester.takeException(), isNull);

    // 420px 모바일 폭 반응형에서 오버플로 없음 검증
    tester.view.physicalSize = const Size(420.0, 800.0);
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);

    // 다시 기존 템플릿(0:1) 선택 시 가이드 위젯 사라짐
    final allChip = find.byKey(const Key('categoryChip_전체'));
    await tester.ensureVisible(allChip);
    await tester.tap(allChip);
    await tester.pumpAndSettle();

    final legacyCard = find.byKey(const Key('templateCard_0:1'));
    await tester.ensureVisible(legacyCard);
    await tester.tap(legacyCard);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('publicPresetGuideline')), findsNothing);
    expect(find.text('행 단위 3개'), findsOneWidget);
  });

  testWidgets('공공 간트 열 더하기는 정보단위 수를 전송한다', (tester) async {
    final calls = <List<Object?>>[];
    Future<Object?> api(String name, List<Object?> args) async {
      calls.add([name, ...args]);
      final action = args[0] as String;
      if (action == 'list') return envelope(sampleListData(includePublic: true));
      if (action == 'preview') {
        final payload = args[1] as Map;
        final cols = (payload['col_count'] as num?)?.toInt() ?? 4;
        return envelope(samplePreview(rows: 5, cols: 2 + cols));
      }
      if (action == 'copy') {
        return envelope({'copied': true, 'message': 'OK', 'activated': false});
      }
      return envelope({});
    }

    await pumpScreen(tester, api: api);
    final pubChip = find.byKey(const Key('categoryChip_공공 표준'));
    await tester.ensureVisible(pubChip);
    await tester.tap(pubChip);
    await tester.pumpAndSettle();

    final ganttCard = find.byKey(const Key('templateCard_pub_gantt_timeline'));
    await tester.ensureVisible(ganttCard);
    await tester.tap(ganttCard);
    await tester.pumpAndSettle();

    // 초기 정보단위 열 4개 표시
    expect(find.text('열 단위 4개'), findsOneWidget);

    // [+] 버튼 클릭 -> col_count 5 전송
    final colPlus = find.byKey(const Key('btnColPlus'));
    await tester.tap(colPlus);
    await tester.pumpAndSettle();

    expect(find.text('열 단위 5개'), findsOneWidget);
    final lastPreview = calls.lastWhere((c) => c[0] == 'table_units' && c[1] == 'preview');
    expect((lastPreview[2] as Map)['col_count'], 5);

    // [-] 버튼 클릭으로 최소값(2개) 도달 시 추가 감소 차단 검증
    final colMinus = find.byKey(const Key('btnColMinus'));
    // 현재 5개 -> 2개로 감소 (3회 탭)
    await tester.tap(colMinus);
    await tester.pumpAndSettle();
    await tester.tap(colMinus);
    await tester.pumpAndSettle();
    await tester.tap(colMinus);
    await tester.pumpAndSettle();
    expect(find.text('열 단위 2개'), findsOneWidget);

    // 최소 2개 상태에서 추가 탭 시 2개 유지 (차단)
    await tester.tap(colMinus);
    await tester.pumpAndSettle();
    expect(find.text('열 단위 2개'), findsOneWidget);

    // 다시 [+] 버튼 3번 눌러 5개로 복원 후 복사
    await tester.tap(colPlus);
    await tester.pumpAndSettle();
    await tester.tap(colPlus);
    await tester.pumpAndSettle();
    await tester.tap(colPlus);
    await tester.pumpAndSettle();
    expect(find.text('열 단위 5개'), findsOneWidget);

    // 복사 클릭 시 payload에 col_count 5 전달
    await tester.ensureVisible(find.byKey(const Key('btnTopCopyTable')));
    await tester.tap(find.byKey(const Key('btnTopCopyTable')));
    await tester.pumpAndSettle();

    final copyCall = calls.lastWhere((c) => c[0] == 'table_units' && c[1] == 'copy');
    expect((copyCall[2] as Map)['col_count'], 5);
  });

  testWidgets('공공 요약은 기존 고정표 조작을 사용한다', (tester) async {
    final calls = <List<Object?>>[];
    Future<Object?> api(String name, List<Object?> args) async {
      calls.add([name, ...args]);
      final action = args[0] as String;
      if (action == 'list') return envelope(sampleListData(includePublic: true));
      if (action == 'preview') return envelope(samplePreview(rows: 1, cols: 1));
      if (action == 'copy') return envelope({'copied': true, 'message': 'OK', 'activated': false});
      return envelope({});
    }

    await pumpScreen(tester, api: api);
    final pubChip = find.byKey(const Key('categoryChip_공공 표준'));
    await tester.ensureVisible(pubChip);
    await tester.tap(pubChip);
    await tester.pumpAndSettle();

    final sumCard = find.byKey(const Key('templateCard_pub_summary_headline'));
    await tester.ensureVisible(sumCard);
    await tester.tap(sumCard);
    await tester.pumpAndSettle();

    // 고정 표 안내 표시 및 -/+ 없음
    expect(find.byKey(const Key('fixedTableNotice')), findsOneWidget);
    expect(find.byKey(const Key('btnRowPlus')), findsNothing);
    expect(find.byKey(const Key('btnColPlus')), findsNothing);

    // 정상 복사 호출
    await tester.ensureVisible(find.byKey(const Key('btnTopCopyTable')));
    await tester.tap(find.byKey(const Key('btnTopCopyTable')));
    await tester.pumpAndSettle();

    final copyCall = calls.lastWhere((c) => c[0] == 'table_units' && c[1] == 'copy');
    expect((copyCall[2] as Map)['id'], 'pub_summary_headline');
  });

  testWidgets('공공 표도 즐겨찾기 최근사용과 복사 오류를 공유한다', (tester) async {
    final calls = <List<Object?>>[];
    Future<Object?> api(String name, List<Object?> args) async {
      calls.add([name, ...args]);
      final action = args[0] as String;
      if (action == 'list') return envelope(sampleListData(includePublic: true));
      if (action == 'preview') return envelope(samplePreview());
      if (action == 'favorite') return envelope(sampleListData(includePublic: true));
      if (action == 'copy') {
        return errorEnvelope('COPY_FAILED', '한/글 복사에 실패했습니다.');
      }
      return envelope({});
    }

    await pumpScreen(tester, api: api);
    final pubChip = find.byKey(const Key('categoryChip_공공 표준'));
    await tester.ensureVisible(pubChip);
    await tester.tap(pubChip);
    await tester.pumpAndSettle();

    // 1. 공공 표 즐겨찾기 클릭
    final favBtn = find.byKey(const Key('btnFavorite_pub_two_col_definition'));
    await tester.ensureVisible(favBtn);
    await tester.tap(favBtn);
    await tester.pumpAndSettle();

    final favCall = calls.lastWhere((c) => c[0] == 'table_units' && c[1] == 'favorite');
    expect((favCall[2] as Map)['id'], 'pub_two_col_definition');

    // 2. 복사 실패 안내
    final twoColCard = find.byKey(const Key('templateCard_pub_two_col_definition'));
    await tester.ensureVisible(twoColCard);
    await tester.tap(twoColCard);
    await tester.pumpAndSettle();

    await tester.ensureVisible(find.byKey(const Key('btnTopCopyTable')));
    await tester.tap(find.byKey(const Key('btnTopCopyTable')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('copyErrorMessage')), findsOneWidget);
    expect(find.text('한/글 복사에 실패했습니다.'), findsOneWidget);
  });

  testWidgets('공공 썸네일 누락은 기존 자동 생성 한 번과 구조 폴백을 사용한다', (tester) async {
    final calls = <List<Object?>>[];
    Future<Object?> api(String name, List<Object?> args) async {
      calls.add([name, ...args]);
      final action = args[0] as String;
      if (action == 'list') {
        return envelope(sampleListData(includePublic: true, thumbnailsReady: false));
      }
      if (action == 'thumbnails') {
        return envelope(sampleListData(includePublic: true, thumbnailsReady: true));
      }
      if (action == 'preview') return envelope(samplePreview());
      return envelope({});
    }

    await pumpScreen(tester, api: api);

    // 자동 thumbnails 1회 호출
    final thumbCalls = calls.where((c) => c[0] == 'table_units' && c[1] == 'thumbnails');
    expect(thumbCalls.length, 1);
    expect(find.byKey(const Key('tableGridPreview')), findsOneWidget);

    // 실패 서브케이스: thumbnails 호출이 실패하더라도 spinner 종료, 구조 표 유지, 무한 재요청 없음
    final failCalls = <List<Object?>>[];
    Future<Object?> failApi(String name, List<Object?> args) async {
      failCalls.add([name, ...args]);
      final action = args[0] as String;
      if (action == 'list') {
        return envelope(sampleListData(includePublic: true, thumbnailsReady: false));
      }
      if (action == 'thumbnails') {
        return errorEnvelope('THUMBNAIL_FAILED', '썸네일 생성 실패');
      }
      if (action == 'preview') return envelope(samplePreview());
      return envelope({});
    }

    await pumpScreen(tester, api: failApi);
    final failThumbCalls = failCalls.where((c) => c[0] == 'table_units' && c[1] == 'thumbnails');
    expect(failThumbCalls.length, 1);
    expect(find.byKey(const Key('tableGridPreview')), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsNothing);
  });

  testWidgets('공공 미리보기의 늦은 응답은 다음 선택을 덮지 않는다', (tester) async {
    final completerPub = Completer<Map<String, Object?>>();
    Future<Object?> api(String name, List<Object?> args) async {
      final action = args[0] as String;
      if (action == 'list') return envelope(sampleListData(includePublic: true));
      if (action == 'preview') {
        final payload = args[1] as Map;
        if (payload['id'] == 'pub_two_col_definition') {
          return completerPub.future;
        }
        return envelope(samplePreview(rows: 3, cols: 4));
      }
      return envelope({});
    }

    await pumpScreen(tester, api: api);

    // 1. 공공 표 선택 -> preview 지연 (미완료 Future 동안 스피너가 돌 수 있으므로 pumpAndSettle 대신 pump 사용)
    final pubChip = find.byKey(const Key('categoryChip_공공 표준'));
    await tester.ensureVisible(pubChip);
    await tester.tap(pubChip);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));

    final pubCard = find.byKey(const Key('templateCard_pub_two_col_definition'));
    await tester.ensureVisible(pubCard);
    await tester.tap(pubCard);
    await tester.pump();

    // 2. 곧바로 전체 칩으로 돌아가 0:1 선택
    final allChip = find.byKey(const Key('categoryChip_전체'));
    await tester.ensureVisible(allChip);
    await tester.tap(allChip);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));

    final legacyCard = find.byKey(const Key('templateCard_0:1'));
    await tester.ensureVisible(legacyCard);
    await tester.tap(legacyCard);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    // 3. 지연되었던 공공 preview가 뒤늦게 완료
    completerPub.complete(envelope(samplePreview(rows: 99, cols: 99)));
    await tester.pumpAndSettle();

    // 여전히 0:1 ('분야별 과제표') 상태 유지
    expect(find.text('분야별 과제표'), findsWidgets);
  });
}
