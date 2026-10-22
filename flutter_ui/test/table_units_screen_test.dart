import 'package:docfit_ui/core/api/abbreviation_api.dart';
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

Map<String, Object?> samplePreview({int rows = 3, int cols = 2}) => {
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
          },
      ],
  ],
};

Map<String, Object?> sampleListData({bool thumbnailsReady = true}) => {
  'source': 'C:/HWP_AUTODOCFIT/templates.hwpx',
  'thumbnails_ready': thumbnailsReady,
  'templates': [
    {
      'id': '0:1',
      'category': '과제표',
      'name': '분야별 과제표',
      'rows': 3,
      'cols': 4,
      'thumbnail': samplePngBase64,
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
      'units': {'row': null, 'col': null},
    },
    {
      'id': '0:3',
      'category': '일정표',
      'name': '월간 일정표',
      'rows': 4,
      'cols': 6,
      'thumbnail': null,
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

    // list와 preview가 순차적으로 호출되었는지 확인
    expect(calls.any((c) => c[0] == 'table_units' && c[1] == 'list'), isTrue);
    expect(
      calls.any((c) => c[0] == 'table_units' && c[1] == 'preview'),
      isTrue,
    );
  });

  testWidgets('분류 칩 거르기 및 다른 카드 선택 시 preview 호출', (tester) async {
    final calls = <List<Object?>>[];
    Future<Object?> api(String name, List<Object?> args) async {
      calls.add([name, ...args]);
      final action = args[0] as String;
      if (action == 'list') {
        return envelope(sampleListData());
      }
      if (action == 'preview') {
        final payload = args[1] as Map;
        return envelope(
          samplePreview(
            rows: payload['id'] == '0:2' ? 2 : 3,
            cols: payload['id'] == '0:2' ? 2 : 4,
          ),
        );
      }
      return envelope({});
    }

    await pumpScreen(tester, api: api);

    // 서약서 칩 클릭
    final chipFinder = find.byKey(const Key('categoryChip_서약서'));
    expect(chipFinder, findsOneWidget);
    await tester.tap(chipFinder);
    await tester.pumpAndSettle();

    // '분야별 과제표' 카드는 사라지고 '서약서 고정 표'만 보여야 함
    expect(find.byKey(const Key('templateCard_0:1')), findsNothing);
    expect(find.byKey(const Key('templateCard_0:2')), findsOneWidget);

    // 카드 선택
    await tester.tap(find.byKey(const Key('templateCard_0:2')));
    await tester.pumpAndSettle();

    final previewCalls = calls.where(
      (c) =>
          c[0] == 'table_units' &&
          c[1] == 'preview' &&
          (c[2] as Map)['id'] == '0:2',
    );
    expect(previewCalls, isNotEmpty);
  });

  testWidgets('스테퍼 [+]/[-] 동작, max 제한에서 [+] 꺼짐, preview 인자 반영', (tester) async {
    final calls = <List<Object?>>[];
    Future<Object?> api(String name, List<Object?> args) async {
      calls.add([name, ...args]);
      final action = args[0] as String;
      if (action == 'list') {
        return envelope(sampleListData());
      }
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

    // [+] 클릭 -> 4개
    await tester.tap(plusBtn);
    await tester.pumpAndSettle();
    expect(find.text('행 단위 4개'), findsOneWidget);

    // [+] 클릭 -> 5개 (max=5 도달)
    await tester.tap(plusBtn);
    await tester.pumpAndSettle();
    expect(find.text('행 단위 5개'), findsOneWidget);

    // max(5)에 도달했으므로 [+] 버튼이 비활성화(onPressed == null)되어야 함
    final plusWidget = tester.widget<IconButton>(plusBtn);
    expect(plusWidget.onPressed, isNull);

    // [-] 클릭 -> 4개로 감소
    await tester.tap(minusBtn);
    await tester.pumpAndSettle();
    expect(find.text('행 단위 4개'), findsOneWidget);

    // preview 호출 인자에 row_count가 정확히 전달되었는지 확인
    final lastPreview = calls.lastWhere(
      (c) => c[0] == 'table_units' && c[1] == 'preview',
    );
    expect((lastPreview[2] as Map)['row_count'], 4);
  });

  testWidgets('고정 표는 안내 문구 표시 및 스테퍼 없음', (tester) async {
    Future<Object?> api(String name, List<Object?> args) async {
      final action = args[0] as String;
      if (action == 'list') {
        return envelope(sampleListData());
      }
      if (action == 'preview') {
        return envelope(samplePreview(rows: 2, cols: 2));
      }
      return envelope({});
    }

    await pumpScreen(tester, api: api);

    // 템플릿 2 (고정 표) 선택
    await tester.tap(find.byKey(const Key('templateCard_0:2')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('fixedTableNotice')), findsOneWidget);
    expect(find.text('이 표는 정보단위 조절 없이 그대로 복사해요'), findsOneWidget);
    expect(find.byKey(const Key('btnRowMinus')), findsNothing);
    expect(find.byKey(const Key('btnRowPlus')), findsNothing);
  });

  testWidgets('복사 버튼 클릭 시 copy API 호출 및 SnackBar 표시', (tester) async {
    final calls = <List<Object?>>[];
    Future<Object?> api(String name, List<Object?> args) async {
      calls.add([name, ...args]);
      final action = args[0] as String;
      if (action == 'list') {
        return envelope(sampleListData());
      }
      if (action == 'preview') {
        return envelope(samplePreview());
      }
      if (action == 'copy') {
        return envelope({
          'copied': true,
          'message': '클립보드에 복사했어요. 한/글에서 Ctrl+V로 붙여넣으세요.',
        });
      }
      return envelope({});
    }

    await pumpScreen(tester, api: api);

    final copyBtn = find.byKey(const Key('btnCopyTable'));
    expect(copyBtn, findsOneWidget);
    await tester.tap(copyBtn);
    await tester.pump(); // SnackBar 시작
    await tester.pumpAndSettle();

    expect(calls.any((c) => c[0] == 'table_units' && c[1] == 'copy'), isTrue);
    expect(find.text('클립보드에 복사했어요. 한/글에서 Ctrl+V로 붙여넣으세요.'), findsOneWidget);
  });

  testWidgets('API 오류 발생 시 화면 및 복사 오류 메시지 표시', (tester) async {
    // 1. 초기 로드 실패 시
    Future<Object?> failApi(String name, List<Object?> args) async {
      return errorEnvelope('LOAD_FAILED', '목록을 불러올 수 없습니다.');
    }

    await pumpScreen(tester, api: failApi);
    expect(find.byKey(const Key('errorMessage')), findsOneWidget);
    expect(find.text('목록을 불러올 수 없습니다.'), findsOneWidget);

    // 2. 복사 실패 시 빨간 글 표시
    Future<Object?> copyFailApi(String name, List<Object?> args) async {
      final action = args[0] as String;
      if (action == 'list') return envelope(sampleListData());
      if (action == 'preview') return envelope(samplePreview());
      if (action == 'copy') {
        return errorEnvelope('CLIPBOARD_ERROR', '한/글 복사 중 오류가 발생했습니다.');
      }
      return envelope({});
    }

    // 앞 화면의 상태(목록 오류)를 재사용하지 않도록 위젯 트리를 비운 뒤 새로 띄운다.
    await tester.pumpWidget(const SizedBox());
    await pumpScreen(tester, api: copyFailApi);
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

    // 템플릿 1에는 base64 썸네일이 있음
    expect(find.byType(Image), findsWidgets);
  });

  testWidgets('thumbnails_ready false일 때 안내 문구 표시 및 스냅샷 생성 버튼', (tester) async {
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

    expect(find.byKey(const Key('thumbnailsNotice')), findsOneWidget);
    expect(find.text('한/글로 실제 모양 그림을 만들 수 있어요'), findsOneWidget);

    final genBtn = find.byKey(const Key('btnGenerateThumbnails'));
    expect(genBtn, findsOneWidget);
    await tester.tap(genBtn);
    await tester.pumpAndSettle();

    expect(
      calls.any((c) => c[0] == 'table_units' && c[1] == 'thumbnails'),
      isTrue,
    );
  });

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
}
