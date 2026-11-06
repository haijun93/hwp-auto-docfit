import 'dart:convert';
import 'dart:typed_data';

import 'package:docfit_ui/features/table_sketch/table_sketch_models.dart';
import 'package:docfit_ui/features/table_sketch/table_sketch_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

// 1×1 빨간 PNG(그림 파일 고르기 흉내)
const redPng =
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg==';

/// 서비스 recognize가 돌려주는 2행 × 3열 표(칸 하나 = 1눈금).
Map<String, dynamic> recognized2x3() => {
  'ok': true,
  'rows': 2,
  'cols': 3,
  'angle': 1.0,
  'warnings': ['이미지가 약 1° 기울어 있어 바로잡았습니다.'],
  'sketch': {
    'grid': {'cols': 3, 'rows': 2, 'cell_mm': 5.0},
    'lines': [
      for (var y = 0; y <= 2; y++) {'x1': 0, 'y1': y, 'x2': 3, 'y2': y},
      for (var x = 0; x <= 3; x++) {'x1': x, 'y1': 0, 'x2': x, 'y2': 2},
    ],
    'texts': [],
  },
};

void main() {
  test('fitRecognizedSketch scales cells to 4 units and keeps the base grid', () {
    final fitted = fitRecognizedSketch(
      TableSketchDoc.fromJson(recognized2x3()['sketch'] as Map),
    );
    expect(fitted.grid.cols, 36); // 기본 격자 이상
    expect(fitted.grid.rows, 50);
    expect(fitted.lines, hasLength(7));
    expect(
      fitted.lines.map((l) => [l.x1, l.y1, l.x2, l.y2]),
      containsAll([
        [0, 0, 12, 0],
        [0, 8, 12, 8],
        [12, 0, 12, 8],
      ]),
    );
    // 열이 많으면 폭 32눈금 안으로 줄이고, 격자는 200을 넘지 않는다.
    final wide = fitRecognizedSketch(
      TableSketchDoc(
        grid: const GridConfig(cols: 40, rows: 150),
        lines: [const SketchLine(x1: 0, y1: 0, x2: 40, y2: 0, width: 'thick')],
      ),
    );
    expect(wide.lines.single.x2, 40);
    expect(wide.lines.single.width, 'thick');
    expect(wide.grid.cols, 40);
    expect(wide.grid.rows, 150);
  });

  group('이미지에서 표 인식 화면', () {
    late List<Map> previews;
    late List<Object?> recognizeCalls;
    late Object? Function() recognizeResponse;

    Future<Object?> api(String name, List<Object?> args) async {
      if (name == 'table_sketch' && args[0] == 'preview') {
        previews.add(args[1] as Map);
        return {'ok': true, 'rows': 0, 'cols': 0, 'cells': [], 'warnings': []};
      }
      if (name == 'table_sketch' && args[0] == 'recognize') {
        recognizeCalls.add(args[1]);
        return recognizeResponse();
      }
      if (name == 'table_sketch' && args[0] == 'load_draft') {
        return {'ok': true, 'exists': false};
      }
      return {'ok': true};
    }

    Future<void> open(WidgetTester tester, {Uint8List? picked}) async {
      tester.view.physicalSize = const Size(1400, 900);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      previews = [];
      recognizeCalls = [];
      await tester.pumpWidget(
        MaterialApp(
          home: TableSketchScreen(
            api: api,
            pickImage: () async => picked,
          ),
        ),
      );
      await tester.pump(const Duration(seconds: 1));
    }

    List lastPreviewLines() => previews.last['lines'] as List;

    testWidgets('인식 결과를 겹쳐 보이고 적용·되돌리기 1번으로 인식 전 복귀', (tester) async {
      recognizeResponse = recognized2x3;
      await open(tester, picked: base64Decode(redPng));
      expect(lastPreviewLines(), isEmpty);

      await tester.tap(find.byKey(const Key('sketchRecognizeImage')));
      await tester.pump();
      await tester.pump();
      expect(recognizeCalls, [redPng]);
      expect(find.byKey(const Key('recognizeOverlay')), findsOneWidget);
      expect(find.byKey(const Key('recognizeCanvasOverlay')), findsOneWidget);
      expect(find.textContaining('2행 × 3열'), findsOneWidget);
      expect(find.textContaining('기울어 있어'), findsOneWidget);
      // 적용 전에는 그림이 바뀌지 않고 되돌리기도 비어 있다.
      final undo = find.byKey(const Key('undoButton'));
      expect(tester.widget<IconButton>(undo).onPressed, isNull);

      await tester.tap(find.byKey(const Key('recognizeApply')));
      await tester.pump(const Duration(seconds: 1));
      expect(find.byKey(const Key('recognizeOverlay')), findsNothing);
      expect(find.byKey(const Key('recognizeCanvasOverlay')), findsNothing);
      expect(lastPreviewLines(), hasLength(7));
      expect(tester.widget<IconButton>(undo).onPressed, isNotNull);

      await tester.tap(undo);
      await tester.pump(const Duration(seconds: 1));
      expect(lastPreviewLines(), isEmpty);
      expect(tester.widget<IconButton>(undo).onPressed, isNull);
      await tester.pump(const Duration(seconds: 5));
    });

    testWidgets('취소하면 그림을 바꾸지 않는다', (tester) async {
      recognizeResponse = recognized2x3;
      await open(tester, picked: base64Decode(redPng));
      final before = previews.length;
      await tester.tap(find.byKey(const Key('sketchRecognizeImage')));
      await tester.pump();
      await tester.pump();
      await tester.tap(find.byKey(const Key('recognizeCancel')));
      await tester.pump(const Duration(seconds: 1));
      expect(find.byKey(const Key('recognizeOverlay')), findsNothing);
      expect(previews.length, before);
      expect(
        tester.widget<IconButton>(find.byKey(const Key('undoButton'))).onPressed,
        isNull,
      );
    });

    testWidgets('파일을 고르지 않으면 아무것도 하지 않는다', (tester) async {
      recognizeResponse = recognized2x3;
      await open(tester);
      await tester.tap(find.byKey(const Key('sketchRecognizeImage')));
      await tester.pump();
      expect(recognizeCalls, isEmpty);
      expect(find.byKey(const Key('recognizeError')), findsNothing);
    });

    testWidgets('인식 실패면 서비스가 준 이유를 보인다', (tester) async {
      recognizeResponse = () => {
        'ok': false,
        'message': '표의 가로·세로 선을 충분히 찾지 못했습니다. 선이 선명한 정면 이미지를 사용해 주세요.',
      };
      await open(tester, picked: base64Decode(redPng));
      await tester.tap(find.byKey(const Key('sketchRecognizeImage')));
      await tester.pump();
      await tester.pump();
      expect(find.byKey(const Key('recognizeError')), findsOneWidget);
      expect(find.textContaining('표 인식 실패: 표의 가로·세로 선을 충분히'), findsOneWidget);
      expect(find.byKey(const Key('recognizeApply')), findsNothing);
      await tester.tap(find.byKey(const Key('recognizeErrorClose')));
      await tester.pump();
      expect(find.byKey(const Key('recognizeError')), findsNothing);
    });

    testWidgets('빈 결과·이상한 응답이면 이유를 보인다', (tester) async {
      recognizeResponse = () => {
        'ok': true,
        'rows': 0,
        'cols': 0,
        'sketch': {
          'grid': {'cols': 1, 'rows': 1, 'cell_mm': 5.0},
          'lines': [],
          'texts': [],
        },
      };
      await open(tester, picked: base64Decode(redPng));
      await tester.tap(find.byKey(const Key('sketchRecognizeImage')));
      await tester.pump();
      await tester.pump();
      expect(find.textContaining('표 선을 하나도 찾지 못했습니다'), findsOneWidget);

      recognizeResponse = () => 'nonsense';
      await tester.tap(find.byKey(const Key('sketchRecognizeImage')));
      await tester.pump();
      await tester.pump();
      expect(find.textContaining('표 인식 응답을 읽지 못했습니다'), findsOneWidget);
    });

    testWidgets('8MB 넘는 파일은 보내지 않고 이유를 보인다', (tester) async {
      recognizeResponse = recognized2x3;
      await open(tester, picked: Uint8List(8000001));
      await tester.tap(find.byKey(const Key('sketchRecognizeImage')));
      await tester.pump();
      expect(recognizeCalls, isEmpty);
      expect(find.textContaining('8MB 이하'), findsOneWidget);
    });
  });
}
