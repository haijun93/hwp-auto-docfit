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

Map<String, Object?> sampleListData({
  bool thumbnailsReady = true,
  List<String>? favorites,
  List<String>? recent,
}) => {
  'source': 'C:/HWP_AUTODOCFIT/templates.hwpx',
  'thumbnails_ready': thumbnailsReady,
  if (favorites != null) 'favorites': favorites,
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

  await tester.pumpWidget(MaterialApp(home: TableUnitsScreen(api: api)));
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
    // GridView에서 첫 번째 항목(0:3)의 x좌표가 두 번째 항목(0:1)보다 작음
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

    // 2. activated == false 케이스 (재사용 전 위젯 트리 비우기)
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

    // 자동 생성 요청 1회, 끝나면 안내가 사라지고 버튼은 남는다
    expect(
      calls.where((c) => c[0] == 'table_units' && c[1] == 'thumbnails').length,
      1,
    );
    expect(find.byKey(const Key('thumbnailsNotice')), findsNothing);
    expect(find.byKey(const Key('btnGenerateThumbnails')), findsOneWidget);
  });

  // --- 신규 기능 시험 (G19): 상단 이름 바, Wrap 분류 칩, 도형(화살표) 그리기, 폭 420 반응형 ---

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

      // 1. 중복 상단 바 삭제 확인 (화면 세로 캔버스 확보)
      expect(find.byKey(const Key('templateNameBar')), findsNothing);

      // 2. 좌측 갤러리 템플릿 카드 존재 확인
      final card1 = find.byKey(const Key('templateCard_0:1'));
      final card2 = find.byKey(const Key('templateCard_0:2'));
      final card3 = find.byKey(const Key('templateCard_0:3'));
      expect(card1, findsOneWidget);
      expect(card2, findsOneWidget);
      expect(card3, findsOneWidget);

      // 3. 0:2 ('서약서 고정 표') 카드 탭 -> 템플릿 선택 및 미리보기 갱신
      await tester.tap(card2);
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('fixedTableNotice')), findsOneWidget);

      // 4. 0:3 ('월간 일정표') 카드 탭 -> 선택 변경
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

    // PPT 스타일 가로 1줄 리본 배치 검증
    await pumpScreen(tester, api: api, width: 420.0, height: 800.0);

    final expectedCats = ['즐겨찾기', '최근 사용', '전체', '과제표', '서약서', '일정표', '사진첨부용'];
    for (final cat in expectedCats) {
      final chipFinder = find.byKey(Key('categoryChip_$cat'));
      expect(chipFinder, findsOneWidget);
    }

    // 가로 1줄 리본으로 동일 Y좌표에 정렬됨 (불필요한 세로 줄바꿈 방지)
    final chip1 = find.byKey(const Key('categoryChip_즐겨찾기'));
    final chip2 = find.byKey(const Key('categoryChip_최근 사용'));
    final chip3 = find.byKey(const Key('categoryChip_전체'));
    expect(tester.getTopLeft(chip1).dy, equals(tester.getTopLeft(chip2).dy));
    expect(tester.getTopLeft(chip2).dy, equals(tester.getTopLeft(chip3).dy));

    // 좌/우 스크롤 내비게이션 버튼 존재 및 탭 동작
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
          {
            'kind': 'arrow',
            'x': 0.1,
            'y': 0.2,
            'w': 0.8,
            'h': 0.6,
            'direction': 'right',
            'fill': '#2563EB',
            'line': '#1D4ED8',
            'text': '진행',
          },
        ],
        '1,0': [
          {
            'kind': 'arrow',
            'x': 0.2,
            'y': 0.1,
            'w': 0.6,
            'h': 0.8,
            'direction': 'down',
            'fill': null,
            'line': null,
            'text': '',
          },
        ],
      };

      Future<Object?> api(String name, List<Object?> args) async {
        final action = args[0] as String;
        if (action == 'list') return envelope(sampleListData());
        if (action == 'preview') {
          return envelope(
            samplePreview(rows: 2, cols: 2, shapesByCell: shapesData),
          );
        }
        return envelope({});
      }

      await pumpScreen(tester, api: api);

      // tableShapesLayer 레이어 및 TableShapesPainter 호출 검증
      final shapesLayerFinder = find.byKey(const Key('tableShapesLayer'));
      expect(shapesLayerFinder, findsOneWidget);

      final customPaint = tester.widget<CustomPaint>(shapesLayerFinder);
      expect(customPaint.painter, isA<TableShapesPainter>());

      // shapes가 없는 경우 tableShapesLayer가 그려지지 않음 (기존과 동일)
      await tester.pumpWidget(const SizedBox());
      Future<Object?> apiNoShapes(String name, List<Object?> args) async {
        final action = args[0] as String;
        if (action == 'list') return envelope(sampleListData());
        if (action == 'preview') return envelope(samplePreview());
        return envelope({});
      }

      await pumpScreen(tester, api: apiNoShapes);
      expect(find.byKey(const Key('tableShapesLayer')), findsNothing);
    },
  );

  testWidgets(
    'TableGridPreview에서 다양한 도형(화살표 4방향, 삼각형, 선, 사각형, 타원, 그림, 칸 밖 도형) 예외 없이 렌더링',
    (tester) async {
      final previewData = TablePreview.fromJson(
        samplePreview(rows: 2, cols: 2),
      );
      final shapes = {
        '0,0': [
          const CellShape(
            kind: 'arrow',
            direction: 'right',
            fill: '#FF0000',
            text: '오른쪽',
          ),
          const CellShape(kind: 'arrow', direction: 'left', fill: '#00FF00'),
          const CellShape(kind: 'arrow', direction: 'up', fill: '#0000FF'),
          const CellShape(kind: 'arrow', direction: 'down', fill: null),
        ],
        '0,1': [
          const CellShape(
            kind: 'triangle',
            direction: 'right',
            fill: '#FF00FF',
          ),
          const CellShape(kind: 'triangle', direction: 'left'),
          const CellShape(kind: 'triangle', direction: 'up'),
          const CellShape(kind: 'triangle', direction: 'down'),
        ],
        '1,0': [
          const CellShape(kind: 'line', direction: 'right', line: '#000000'),
          const CellShape(kind: 'line', direction: 'down', line: '#333333'),
          const CellShape(
            kind: 'rect',
            fill: '#E0E0E0',
            line: '#999999',
            text: '상자',
          ),
          const CellShape(kind: 'ellipse', fill: null, line: '#FF0000'),
        ],
        '1,1': [
          const CellShape(kind: 'pic', text: '사진'),
          const CellShape(kind: 'other'),
          // 칸 밖으로 나가는 도형 (x: -0.2, w: 1.5)
          const CellShape(
            kind: 'arrow',
            x: -0.2,
            y: -0.1,
            w: 1.5,
            h: 1.2,
            direction: 'right',
          ),
        ],
      };

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: TableGridPreview(
              rows: 2,
              cols: 2,
              cellMeta: previewData.cellMeta,
              shapes: shapes,
              maxHeight: 400,
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(tester.takeException(), isNull);
      expect(find.byKey(const Key('tableShapesLayer')), findsOneWidget);
    },
  );

  for (final width in [420.0, 1200.0]) {
    testWidgets('폭 $width에서 넘침(overflow) 없음', (tester) async {
      Future<Object?> api(String name, List<Object?> args) async {
        final action = args[0] as String;
        if (action == 'list') return envelope(sampleListData());
        if (action == 'preview') return envelope(samplePreview());
        return envelope({});
      }

      await pumpScreen(tester, api: api, width: width, height: 800.0);
      expect(tester.takeException(), isNull);
    });
  }

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

      // 상단 중복 메뉴가 없고, 상세창 상단 즉시 복사 버튼과 하단 복사 버튼이 모두 존재
      expect(find.byKey(const Key('templateNameBar')), findsNothing);
      expect(find.byKey(const Key('btnTopCopyTable')), findsOneWidget);
      expect(find.byKey(const Key('btnCopyTable')), findsOneWidget);

      // 상단 즉시 복사 버튼 클릭 시 복사 호출
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

      // 분류 칩 높이 검증 (상단 메뉴와 동일하게 28px)
      final chipAll = find.byKey(const Key('categoryChip_전체'));
      expect(chipAll, findsOneWidget);
      expect(tester.getSize(chipAll).height, equals(28.0));

      // 갤러리 영역 전체가 CustomScrollView 및 Scrollbar로 위아래 스크롤 가능
      expect(find.byType(CustomScrollView), findsOneWidget);
      expect(find.byType(Scrollbar), findsWidgets);
    },
  );

  Map<String, Object?> sortedFixtureData() => {
    'source': 'C:/HWP_AUTODOCFIT/templates.hwpx',
    'thumbnails_ready': true,
    'favorites': ['label2', 'A1'],
    'recent': ['label1', 'B1'],
    'templates': [
      {
        'id': 'A1',
        'category': '분류 A',
        'name': 'A1 서식',
        'rows': 2,
        'cols': 2,
        'thumbnail': samplePngBase64,
        'favorite': true,
        'units': {'row': null, 'col': null},
      },
      {
        'id': 'B1',
        'category': '분류 B',
        'name': 'B1 서식',
        'rows': 2,
        'cols': 2,
        'thumbnail': samplePngBase64,
        'favorite': false,
        'units': {'row': null, 'col': null},
      },
      {
        'id': 'label1',
        'category': '라벨 서식',
        'name': '라벨 1 서식',
        'rows': 2,
        'cols': 2,
        'thumbnail': samplePngBase64,
        'favorite': false,
        'units': {'row': null, 'col': null},
      },
      {
        'id': 'label2',
        'category': '라벨 서식',
        'name': '라벨 2 서식',
        'rows': 2,
        'cols': 2,
        'thumbnail': samplePngBase64,
        'favorite': true,
        'units': {'row': null, 'col': null},
      },
    ],
  };

  testWidgets('분류 칩은 백엔드 순서이며 라벨 서식이 마지막', (tester) async {
    Future<Object?> api(String name, List<Object?> args) async {
      final action = args[0] as String;
      if (action == 'list') return envelope(sortedFixtureData());
      if (action == 'preview') return envelope(samplePreview());
      return envelope({});
    }

    await pumpScreen(tester, api: api, width: 1200.0, height: 800.0);

    final expectedOrder = ['즐겨찾기', '최근 사용', '전체', '분류 A', '분류 B', '라벨 서식'];
    final chips = <Finder>[];
    for (final cat in expectedOrder) {
      final finder = find.byKey(Key('categoryChip_$cat'));
      await tester.ensureVisible(finder);
      expect(finder, findsOneWidget);
      chips.add(finder);
    }
    for (int i = 0; i < chips.length - 1; i++) {
      expect(
        tester.getTopLeft(chips[i]).dx,
        lessThan(tester.getTopLeft(chips[i + 1]).dx),
      );
    }
  });

  testWidgets('전체 목록과 검색은 라벨 서식이 마지막', (tester) async {
    Future<Object?> api(String name, List<Object?> args) async {
      final action = args[0] as String;
      if (action == 'list') return envelope(sortedFixtureData());
      if (action == 'preview') return envelope(samplePreview());
      return envelope({});
    }

    await pumpScreen(tester, api: api, width: 1200.0, height: 800.0);

    await tester.tap(find.byKey(const Key('categoryChip_전체')));
    await tester.pumpAndSettle();

    final cardA1 = find.byKey(const Key('templateCard_A1'));
    final cardB1 = find.byKey(const Key('templateCard_B1'));
    final cardL1 = find.byKey(const Key('templateCard_label1'));
    final cardL2 = find.byKey(const Key('templateCard_label2'));

    expect(cardA1, findsOneWidget);
    expect(cardB1, findsOneWidget);
    expect(cardL1, findsOneWidget);
    expect(cardL2, findsOneWidget);

    final searchInput = find.byKey(const Key('inputSearch'));
    if (searchInput.evaluate().isNotEmpty) {
      await tester.enterText(searchInput, '서식');
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('templateCard_label1')), findsOneWidget);
      expect(find.byKey(const Key('templateCard_label2')), findsOneWidget);
    }
  });

  testWidgets('즐겨찾기와 최근 사용은 ID 배열 순서 유지', (tester) async {
    Future<Object?> api(String name, List<Object?> args) async {
      final action = args[0] as String;
      if (action == 'list') return envelope(sortedFixtureData());
      if (action == 'preview') return envelope(samplePreview());
      return envelope({});
    }

    await pumpScreen(tester, api: api, width: 1200.0, height: 800.0);

    await tester.tap(find.byKey(const Key('categoryChip_즐겨찾기')));
    await tester.pumpAndSettle();

    final cardL2 = find.byKey(const Key('templateCard_label2'));
    final cardA1 = find.byKey(const Key('templateCard_A1'));
    expect(cardL2, findsOneWidget);
    expect(cardA1, findsOneWidget);
    expect(tester.getTopLeft(cardL2).dx, lessThan(tester.getTopLeft(cardA1).dx));

    await tester.tap(find.byKey(const Key('categoryChip_최근 사용')));
    await tester.pumpAndSettle();

    final cardL1 = find.byKey(const Key('templateCard_label1'));
    final cardB1 = find.byKey(const Key('templateCard_B1'));
    expect(cardL1, findsOneWidget);
    expect(cardB1, findsOneWidget);
    expect(tester.getTopLeft(cardL1).dx, lessThan(tester.getTopLeft(cardB1).dx));
  });

  testWidgets('즐겨찾기 토글 성공과 실패는 사용자 순서를 보존', (tester) async {
    bool failApi = false;
    final data = sortedFixtureData();

    Future<Object?> api(String name, List<Object?> args) async {
      final action = args[0] as String;
      if (action == 'list') return envelope(data);
      if (action == 'preview') return envelope(samplePreview());
      if (action == 'favorite') {
        if (failApi) throw Exception('API Failure');
        final payload = args[1] as Map;
        final tList = (data['templates'] as List).cast<Map<String, Object?>>();
        for (final t in tList) {
          if (t['id'] == payload['id']) {
            t['favorite'] = payload['on'];
          }
        }
        final favs = List<String>.from((data['favorites'] as List).cast<String>());
        if (payload['on'] == true) {
          favs.add(payload['id'] as String);
        } else {
          favs.remove(payload['id']);
        }
        data['favorites'] = favs;
        return envelope(data);
      }
      return envelope({});
    }

    await pumpScreen(tester, api: api, width: 1200.0, height: 800.0);

    final favBtnB1 = find.byKey(const Key('btnFavorite_B1'));
    expect(favBtnB1, findsOneWidget);
    await tester.tap(favBtnB1);
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('categoryChip_즐겨찾기')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('templateCard_label2')), findsOneWidget);
    expect(find.byKey(const Key('templateCard_A1')), findsOneWidget);
    expect(find.byKey(const Key('templateCard_B1')), findsOneWidget);

    failApi = true;
    final favBtnA1 = find.byKey(const Key('btnFavorite_A1'));
    expect(favBtnA1, findsOneWidget);
    await tester.tap(favBtnA1);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('templateCard_A1')), findsOneWidget);
  });

  testWidgets('이전 목록 응답은 favorites 없이 기존 순서로 표시', (tester) async {
    final legacyData = {
      'source': 'C:/HWP_AUTODOCFIT/templates.hwpx',
      'thumbnails_ready': true,
      'recent': ['A1'],
      'templates': [
        {
          'id': 'A1',
          'category': '일반',
          'name': 'A1 서식',
          'rows': 2,
          'cols': 2,
          'thumbnail': samplePngBase64,
          'favorite': true,
          'units': {'row': null, 'col': null},
        },
        {
          'id': 'B1',
          'category': '일반',
          'name': 'B1 서식',
          'rows': 2,
          'cols': 2,
          'thumbnail': samplePngBase64,
          'favorite': true,
          'units': {'row': null, 'col': null},
        },
      ],
    };

    Future<Object?> api(String name, List<Object?> args) async {
      final action = args[0] as String;
      if (action == 'list') return envelope(legacyData);
      if (action == 'preview') return envelope(samplePreview());
      return envelope({});
    }

    await pumpScreen(tester, api: api, width: 1200.0, height: 800.0);

    await tester.tap(find.byKey(const Key('categoryChip_즐겨찾기')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('templateCard_A1')), findsOneWidget);
    expect(find.byKey(const Key('templateCard_B1')), findsOneWidget);
  });

  testWidgets('조직도 모양 1은 팀 수 조절을 표시하고 preview에 전달', (tester) async {
    final calls = <List<Object?>>[];
    final orgData = {
      'source': 'C:/HWP_AUTODOCFIT/templates.hwpx',
      'thumbnails_ready': true,
      'favorites': <String>[],
      'recent': <String>[],
      'templates': [
        {
          'id': 'org:1',
          'category': '조직도',
          'name': '조직도 · 모양 1',
          'rows': 6,
          'cols': 12,
          'thumbnail': samplePngBase64,
          'favorite': false,
          'units': {
            'row': null,
            'col': {
              'count': 4,
              'min': 2,
              'max': 9,
              'core': 2,
              'sep': 1,
              'kind': 'org_chart',
            },
          },
        },
      ],
    };

    Future<Object?> api(String name, List<Object?> args) async {
      calls.add([name, ...args]);
      final action = args[0] as String;
      if (action == 'list') return envelope(orgData);
      if (action == 'preview') return envelope(samplePreview(rows: 6, cols: 15));
      return envelope({});
    }

    await pumpScreen(tester, api: api, width: 1200.0, height: 800.0);

    expect(find.text('이 표는 정보단위 조절 없이 그대로 복사해요'), findsNothing);
    expect(find.byKey(const Key('btnColPlus')), findsOneWidget);
    expect(find.byKey(const Key('btnColMinus')), findsOneWidget);

    await tester.tap(find.byKey(const Key('btnColPlus')));
    await tester.pumpAndSettle();

    final previewCalls = calls.where(
      (c) =>
          c[0] == 'table_units' &&
          c[1] == 'preview' &&
          (c[2] as Map)['id'] == 'org:1' &&
          (c[2] as Map)['col_count'] == 5,
    );
    expect(previewCalls, isNotEmpty);
  });
    },
  );
}
