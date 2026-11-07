import 'package:docfit_ui/features/table_sketch/table_sketch_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// 서비스 import_hwpx_table이 돌려주는 2행 × 2열 표(칸 4눈금, 여백 1, 글·배경색 포함).
Map<String, dynamic> imported2x2({String first = '가'}) => {
  'ok': true,
  'rows': 2,
  'cols': 2,
  'tables': 2,
  'warnings': ['대각선은(는) 표그림판에서 표현하지 못해 제외했습니다.'],
  'sketch': {
    'grid': {'cols': 36, 'rows': 50, 'cell_mm': 5.0},
    'lines': [
      for (final y in [1, 5, 9]) {'x1': 1, 'y1': y, 'x2': 9, 'y2': y},
      for (final x in [1, 5, 9]) {'x1': x, 'y1': 1, 'x2': x, 'y2': 9},
    ],
    'texts': [
      {'x': 1, 'y': 1, 'text': first},
    ],
    'fills': [
      {'x1': 1, 'y1': 1, 'x2': 5, 'y2': 5, 'color': '#FCE4D6'},
    ],
  },
};

Map<String, dynamic> table(
  int index,
  String first, {
  bool ok = true,
  String reason = '',
}) => {
  'index': index,
  'rows': 2,
  'cols': 2,
  'first_text': first,
  'ok': ok,
  'reason': reason,
};

void main() {
  group('한/글 문서에서 표 가져오기 화면', () {
    late List<Map> previews;
    late List<Map> listCalls, importCalls;
    late Object? Function() listResponse;
    late Object? Function() importResponse;

    Future<Object?> api(String name, List<Object?> args) async {
      if (name == 'table_sketch' && args[0] == 'preview') {
        previews.add(args[1] as Map);
        return {'ok': true, 'rows': 0, 'cols': 0, 'cells': [], 'warnings': []};
      }
      if (name == 'table_sketch' && args[0] == 'list_hwpx_tables') {
        listCalls.add(args[1] as Map);
        return listResponse();
      }
      if (name == 'table_sketch' && args[0] == 'import_hwpx_table') {
        importCalls.add(args[1] as Map);
        return importResponse();
      }
      if (name == 'table_sketch' && args[0] == 'load_draft') {
        return {'ok': true, 'exists': false};
      }
      return {'ok': true};
    }

    Future<void> open(
      WidgetTester tester, {
      String? picked = r'C:\문서\표.hwpx',
      Size size = const Size(1400, 900),
    }) async {
      tester.view.physicalSize = size;
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      previews = [];
      listCalls = [];
      importCalls = [];
      await tester.pumpWidget(
        MaterialApp(
          home: TableSketchScreen(api: api, pickHwpx: () async => picked),
        ),
      );
      await tester.pump(const Duration(seconds: 1));
    }

    Future<void> tapImport(WidgetTester tester) async {
      await tester.tap(find.byKey(const Key('sketchImportHwpx')));
      await tester.pump();
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));
    }

    List lastPreviewLines() => previews.last['lines'] as List;
    List lastPreviewTexts() => previews.last['texts'] as List;

    testWidgets('표 목록에서 고르면 겹쳐 보이고 적용·되돌리기 1번으로 원래대로', (tester) async {
      listResponse = () => {
        'ok': true,
        'total': 3,
        'tables': [
          table(0, '첫째'),
          table(1, '둘째'),
          table(2, '', ok: false, reason: '표가 너무 커서 표그림판(200칸)에 들어가지 않습니다.'),
        ],
      };
      importResponse = () => imported2x2(first: '둘째');
      await open(tester);
      expect(find.text('한/글 문서에서 표 가져오기'), findsOneWidget);
      expect(lastPreviewLines(), isEmpty);

      await tapImport(tester);
      expect(listCalls, [
        {'path': r'C:\문서\표.hwpx', 'cell_mm': 5.0},
      ]);
      expect(find.byKey(const Key('hwpxTablePicker')), findsOneWidget);
      expect(find.text('가져올 표 고르기 (표 3개)'), findsOneWidget);
      expect(find.text('표 2 · 2행 × 2열'), findsOneWidget);
      expect(find.text('둘째'), findsOneWidget);
      // 너무 큰 표는 이유와 함께 누를 수 없다.
      expect(find.textContaining('너무 커서'), findsOneWidget);
      expect(
        tester.widget<ListTile>(find.byKey(const Key('hwpxTable_2'))).enabled,
        isFalse,
      );

      await tester.tap(find.byKey(const Key('hwpxTable_1')));
      await tester.pump();
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));
      expect(importCalls, [
        {'path': r'C:\문서\표.hwpx', 'index': 1, 'cell_mm': 5.0},
      ]);
      expect(find.byKey(const Key('hwpxTablePicker')), findsNothing);
      expect(find.byKey(const Key('recognizeOverlay')), findsOneWidget);
      expect(find.byKey(const Key('recognizeCanvasOverlay')), findsOneWidget);
      expect(find.textContaining('가져온 표: 2행 × 2열'), findsOneWidget);
      expect(find.textContaining('대각선'), findsOneWidget);
      final undo = find.byKey(const Key('undoButton'));
      expect(tester.widget<IconButton>(undo).onPressed, isNull);

      await tester.tap(find.byKey(const Key('recognizeApply')));
      await tester.pump(const Duration(seconds: 1));
      expect(find.byKey(const Key('recognizeOverlay')), findsNothing);
      expect(lastPreviewLines(), hasLength(6));
      expect(lastPreviewTexts().single['text'], '둘째');
      expect(previews.last['fills'], hasLength(1));
      expect(find.textContaining('가져오기 전으로'), findsOneWidget);
      expect(tester.widget<IconButton>(undo).onPressed, isNotNull);

      await tester.tap(undo);
      await tester.pump(const Duration(seconds: 1));
      expect(lastPreviewLines(), isEmpty);
      expect(lastPreviewTexts(), isEmpty);
      expect(tester.widget<IconButton>(undo).onPressed, isNull);
      await tester.pump(const Duration(seconds: 5));
    });

    testWidgets('표가 하나면 고르는 창 없이 바로 겹쳐 보이고, 취소하면 그대로', (tester) async {
      listResponse = () => {
        'ok': true,
        'total': 1,
        'tables': [table(0, '가')],
      };
      importResponse = imported2x2;
      await open(tester);
      final before = previews.length;
      await tapImport(tester);
      expect(find.byKey(const Key('hwpxTablePicker')), findsNothing);
      expect(importCalls.single['index'], 0);
      expect(find.byKey(const Key('recognizeOverlay')), findsOneWidget);
      await tester.tap(find.byKey(const Key('recognizeCancel')));
      await tester.pump(const Duration(seconds: 1));
      expect(find.byKey(const Key('recognizeOverlay')), findsNothing);
      expect(previews.length, before);
      expect(
        tester
            .widget<IconButton>(find.byKey(const Key('undoButton')))
            .onPressed,
        isNull,
      );
    });

    testWidgets('고르는 창에서 취소하면 가져오지 않는다', (tester) async {
      listResponse = () => {
        'ok': true,
        'total': 2,
        'tables': [table(0, '첫째'), table(1, '둘째')],
      };
      importResponse = imported2x2;
      await open(tester);
      await tapImport(tester);
      await tester.tap(find.byKey(const Key('hwpxTablePickerCancel')));
      await tester.pump(const Duration(milliseconds: 300));
      expect(importCalls, isEmpty);
      expect(find.byKey(const Key('recognizeOverlay')), findsNothing);
      expect(find.byKey(const Key('recognizeError')), findsNothing);
    });

    testWidgets('문서를 고르지 않으면 아무것도 하지 않는다', (tester) async {
      listResponse = () => {'ok': true, 'tables': []};
      importResponse = imported2x2;
      await open(tester, picked: null);
      await tapImport(tester);
      expect(listCalls, isEmpty);
      expect(find.byKey(const Key('recognizeError')), findsNothing);
    });

    testWidgets('표가 없거나 너무 크면 이유를 보인다', (tester) async {
      listResponse = () => {
        'ok': true,
        'total': 0,
        'tables': [],
        'message': '이 문서에는 표가 없습니다.',
      };
      importResponse = imported2x2;
      await open(tester);
      await tapImport(tester);
      expect(find.byKey(const Key('recognizeError')), findsOneWidget);
      expect(find.text('표 가져오기 실패: 이 문서에는 표가 없습니다.'), findsOneWidget);
      await tester.tap(find.byKey(const Key('recognizeErrorClose')));
      await tester.pump();
      expect(find.byKey(const Key('recognizeError')), findsNothing);

      listResponse = () => {
        'ok': true,
        'total': 1,
        'tables': [
          table(0, '', ok: false, reason: '표가 너무 커서 표그림판(200칸)에 들어가지 않습니다.'),
        ],
      };
      await tapImport(tester);
      expect(
        find.text('표 가져오기 실패: 표가 너무 커서 표그림판(200칸)에 들어가지 않습니다.'),
        findsOneWidget,
      );
      expect(importCalls, isEmpty);
      expect(find.byKey(const Key('recognizeApply')), findsNothing);
    });

    testWidgets('서비스 실패·이상한 응답이면 이유를 보인다', (tester) async {
      listResponse = () => {'ok': false, 'message': 'HWPX XML을 읽을 수 없습니다.'};
      importResponse = imported2x2;
      await open(tester);
      await tapImport(tester);
      expect(find.text('표 가져오기 실패: HWPX XML을 읽을 수 없습니다.'), findsOneWidget);

      listResponse = () => 'nonsense';
      await tapImport(tester);
      expect(find.textContaining('표 목록 응답을 읽지 못했습니다'), findsOneWidget);

      listResponse = () => {
        'ok': true,
        'tables': [table(0, '가')],
      };
      importResponse = () => {
        'ok': false,
        'message': '표 칸이 너무 많습니다(2000칸 넘음).',
      };
      await tapImport(tester);
      expect(find.text('표 가져오기 실패: 표 칸이 너무 많습니다(2000칸 넘음).'), findsOneWidget);
      expect(find.byKey(const Key('recognizeOverlay')), findsNothing);
    });

    testWidgets('좁은 창에서도 단추를 누를 수 있다', (tester) async {
      listResponse = () => {
        'ok': true,
        'tables': [table(0, '가')],
      };
      importResponse = imported2x2;
      for (final size in const [Size(1000, 700), Size(480, 700)]) {
        await open(tester, size: size);
        expect(find.byKey(const Key('sketchImportHwpx')), findsOneWidget);
        expect(find.text('한/글 문서에서 표 가져오기'), findsNothing);
      }
      await tapImport(tester);
      expect(find.byKey(const Key('recognizeOverlay')), findsOneWidget);
    });
  });
}
