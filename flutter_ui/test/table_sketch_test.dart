import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:docfit_ui/features/table_sketch/table_sketch_models.dart';
import 'package:docfit_ui/features/table_sketch/table_sketch_painter.dart';
import 'package:docfit_ui/features/table_sketch/table_sketch_screen.dart';

void main() {
  group('TableSketch Models & Helper Tests', () {
    test(
      'snapLineCoords snaps horizontally, vertically and diagonally (45°)',
      () {
        // 1. 가로선 스냅 (y1 == y2)
        final hSnap = snapLineCoords(2, 5, 10, 6, 36, 50);
        expect(hSnap, isNotNull);
        expect(hSnap!.x, 10);
        expect(hSnap.y, 5); // y는 시작점 5로 고정

        // 2. 세로선 스냅 (x1 == x2)
        final vSnap = snapLineCoords(5, 2, 6, 15, 36, 50);
        expect(vSnap, isNotNull);
        expect(vSnap!.x, 5); // x는 시작점 5로 고정
        expect(vSnap.y, 15);

        // 3. 45° 대각선 스냅 (|x2-x1| == |y2-y1|)
        final dSnap = snapLineCoords(4, 4, 11, 10, 36, 50);
        expect(dSnap, isNotNull);
        expect((dSnap!.x - 4).abs(), (dSnap.y - 4).abs());

        // 4. 점 (이동 없음)
        final dotSnap = snapLineCoords(5, 5, 5, 5, 36, 50);
        expect(dotSnap, isNull);
      },
    );

    test('SketchLine validity and coordinate comparison', () {
      const hLine = SketchLine(x1: 0, y1: 5, x2: 10, y2: 5);
      expect(hLine.isValid, isTrue);

      const vLine = SketchLine(x1: 4, y1: 2, x2: 4, y2: 12);
      expect(vLine.isValid, isTrue);

      const dLine = SketchLine(x1: 2, y1: 2, x2: 6, y2: 6);
      expect(dLine.isValid, isTrue);

      const invalidLine = SketchLine(x1: 2, y1: 3, x2: 5, y2: 10);
      expect(invalidLine.isValid, isFalse);

      const zeroLine = SketchLine(x1: 3, y1: 3, x2: 3, y2: 3);
      expect(zeroLine.isValid, isFalse);

      expect(hLine.isSameCoords(0, 5, 10, 5), isTrue);
      expect(hLine.isSameCoords(10, 5, 0, 5), isTrue);
      expect(hLine.isSameCoords(0, 5, 10, 6), isFalse);
    });

    test('TableSketchDoc json serialization & addLine/setText', () {
      final doc = TableSketchDoc(
        grid: const GridConfig(cols: 36, rows: 50, cellMm: 5.0),
      );
      doc.addLine(
        const SketchLine(
          x1: 1,
          y1: 1,
          x2: 10,
          y2: 1,
          width: 'thin',
          style: 'solid',
        ),
      );
      doc.setText(
        const SketchText(x: 2, y: 2, text: '테스트', bold: true, align: 'center'),
      );

      final json = doc.toJson();
      expect(json['grid']['cols'], 36);
      expect((json['lines'] as List).length, 1);
      expect((json['texts'] as List).length, 1);

      final restored = TableSketchDoc.fromJson(json);
      expect(restored.lines.length, 1);
      expect(restored.lines.first.x2, 10);
      expect(restored.texts.first.text, '테스트');
      expect(restored.texts.first.bold, isTrue);
    });
  });

  group('TableSketchScreen Widget Tests', () {
    testWidgets(
      'Line tool creates horizontal, vertical and 45° lines on canvas drag',
      (tester) async {
        tester.view.physicalSize = const Size(1024, 900);
        tester.view.devicePixelRatio = 1.0;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);

        final calls = <List<Object?>>[];
        Future<Object?> api(String name, List<Object?> args) async {
          calls.add([name, ...args]);
          if (name == 'table_sketch') {
            final action = args[0] as String;
            if (action == 'preview') {
              return {
                'ok': true,
                'rows': 2,
                'cols': 2,
                'cells': [],
                'width_mm': 180.0,
                'height_mm': 250.0,
                'warnings': [],
              };
            }
          }
          return {'ok': true};
        }

        await tester.pumpWidget(MaterialApp(home: TableSketchScreen(api: api)));
        await tester.pumpAndSettle();

        final canvasFinder = find.byKey(const Key('sketchCanvas'));
        expect(canvasFinder, findsOneWidget);
        final canvasTopLeft = tester.getTopLeft(canvasFinder);

        // 1. 가로선 그리기 (toolLine이 기본 선택 상태)
        final gesture1 = await tester.startGesture(
          canvasTopLeft + const Offset(16, 16),
        );
        await gesture1.moveTo(
          canvasTopLeft + const Offset(160, 20),
        ); // 가로 방향 드래그
        await gesture1.up();
        await tester.pumpAndSettle();

        // 2. 세로선 그리기
        final gesture2 = await tester.startGesture(
          canvasTopLeft + const Offset(48, 16),
        );
        await gesture2.moveTo(
          canvasTopLeft + const Offset(52, 160),
        ); // 세로 방향 드래그
        await gesture2.up();
        await tester.pumpAndSettle();

        // 3. 45도 대각선 그리기
        final gesture3 = await tester.startGesture(
          canvasTopLeft + const Offset(80, 80),
        );
        await gesture3.moveTo(
          canvasTopLeft + const Offset(144, 140),
        ); // 45도 대각선 방향 드래그
        await gesture3.up();
        await tester.pumpAndSettle();

        // 디바운스 대기
        await tester.pump(const Duration(milliseconds: 600));
        await tester.pumpAndSettle();

        final previewCalls = calls
            .where((c) => c[0] == 'table_sketch' && c[1] == 'preview')
            .toList();
        expect(previewCalls.isNotEmpty, isTrue);
        final lastPreview = previewCalls.last;
        final sketch = lastPreview[2] as Map;
        final lines = (sketch['lines'] as List).cast<Map>();
        expect(lines.length, 3);

        // 1번째 선: 가로선 (y1 == y2)
        expect(lines[0]['y1'], lines[0]['y2']);
        // 2번째 선: 세로선 (x1 == x2)
        expect(lines[1]['x1'], lines[1]['x2']);
        // 3번째 선: 45도 대각선 (|x2-x1| == |y2-y1|)
        final dx = ((lines[2]['x2'] as int) - (lines[2]['x1'] as int)).abs();
        final dy = ((lines[2]['y2'] as int) - (lines[2]['y1'] as int)).abs();
        expect(dx, dy);

        expect(tester.takeException(), isNull);
      },
    );

    testWidgets('Rect tool creates 4 border lines on drag', (tester) async {
      tester.view.physicalSize = const Size(1024, 900);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final calls = <List<Object?>>[];
      Future<Object?> api(String name, List<Object?> args) async {
        calls.add([name, ...args]);
        return {
          'ok': true,
          'rows': 4,
          'cols': 4,
          'cells': [],
          'width_mm': 20.0,
          'height_mm': 20.0,
          'warnings': [],
        };
      }

      await tester.pumpWidget(MaterialApp(home: TableSketchScreen(api: api)));
      await tester.pumpAndSettle();

      // 사각형 도구 선택
      await tester.tap(find.byKey(const Key('toolRect')));
      await tester.pumpAndSettle();

      final canvasFinder = find.byKey(const Key('sketchCanvas'));
      final canvasTopLeft = tester.getTopLeft(canvasFinder);

      // 드래그로 사각형 그리기 (1, 1) -> (5, 5) 격자 (16px 단위)
      final gesture = await tester.startGesture(
        canvasTopLeft + const Offset(16, 16),
      );
      await gesture.moveTo(canvasTopLeft + const Offset(80, 80));
      await gesture.up();
      await tester.pumpAndSettle();

      // 디바운스 대기
      await tester.pump(const Duration(milliseconds: 600));
      await tester.pumpAndSettle();

      final previewCalls = calls
          .where((c) => c[0] == 'table_sketch' && c[1] == 'preview')
          .toList();
      expect(previewCalls.isNotEmpty, isTrue);
      final lastPreview = previewCalls.last;
      final sketch = lastPreview[2] as Map;
      final lines = sketch['lines'] as List;
      expect(lines.length, 4); // 사각형의 4개 변 확인

      expect(tester.takeException(), isNull);
    });

    testWidgets('Eraser tool deletes nearest line on tap', (tester) async {
      tester.view.physicalSize = const Size(1024, 900);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final calls = <List<Object?>>[];
      Future<Object?> api(String name, List<Object?> args) async {
        calls.add([name, ...args]);
        return {'ok': true};
      }

      await tester.pumpWidget(MaterialApp(home: TableSketchScreen(api: api)));
      await tester.pumpAndSettle();

      final canvasFinder = find.byKey(const Key('sketchCanvas'));
      final canvasTopLeft = tester.getTopLeft(canvasFinder);

      // 1. 선 그리기
      final gesture = await tester.startGesture(
        canvasTopLeft + const Offset(16, 16),
      );
      await gesture.moveTo(canvasTopLeft + const Offset(160, 16));
      await gesture.up();
      await tester.pumpAndSettle();

      // 2. 지우개 도구 선택
      await tester.tap(find.byKey(const Key('toolEraser')));
      await tester.pumpAndSettle();

      // 3. 선 근처 탭하여 삭제
      await tester.tapAt(canvasTopLeft + const Offset(80, 16));
      await tester.pumpAndSettle();

      // 디바운스 대기
      await tester.pump(const Duration(milliseconds: 600));
      await tester.pumpAndSettle();

      final previewCalls = calls
          .where((c) => c[0] == 'table_sketch' && c[1] == 'preview')
          .toList();
      expect(previewCalls.isNotEmpty, isTrue);
      final lastPreview = previewCalls.last;
      final sketch = lastPreview[2] as Map;
      final lines = sketch['lines'] as List;
      expect(lines.isEmpty, isTrue); // 선이 삭제됨

      expect(tester.takeException(), isNull);
    });

    testWidgets('Undo and Redo buttons revert and restore changes', (
      tester,
    ) async {
      tester.view.physicalSize = const Size(1024, 900);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final calls = <List<Object?>>[];
      Future<Object?> api(String name, List<Object?> args) async {
        calls.add([name, ...args]);
        return {'ok': true};
      }

      await tester.pumpWidget(MaterialApp(home: TableSketchScreen(api: api)));
      await tester.pumpAndSettle();

      final canvasFinder = find.byKey(const Key('sketchCanvas'));
      final canvasTopLeft = tester.getTopLeft(canvasFinder);

      // 선 그리기
      final gesture = await tester.startGesture(
        canvasTopLeft + const Offset(32, 32),
      );
      await gesture.moveTo(canvasTopLeft + const Offset(128, 32));
      await gesture.up();
      await tester.pumpAndSettle();

      // 실행 취소
      expect(find.byKey(const Key('undoButton')), findsOneWidget);
      await tester.tap(find.byKey(const Key('undoButton')));
      await tester.pumpAndSettle();

      await tester.pump(const Duration(milliseconds: 600));
      await tester.pumpAndSettle();

      var previewCalls = calls
          .where((c) => c[0] == 'table_sketch' && c[1] == 'preview')
          .toList();
      var lastSketch = previewCalls.last[2] as Map;
      expect((lastSketch['lines'] as List).isEmpty, isTrue); // 취소되어 0개

      // 다시 실행
      expect(find.byKey(const Key('redoButton')), findsOneWidget);
      await tester.tap(find.byKey(const Key('redoButton')));
      await tester.pumpAndSettle();

      await tester.pump(const Duration(milliseconds: 600));
      await tester.pumpAndSettle();

      previewCalls = calls
          .where((c) => c[0] == 'table_sketch' && c[1] == 'preview')
          .toList();
      lastSketch = previewCalls.last[2] as Map;
      expect((lastSketch['lines'] as List).length, 1); // 복원되어 1개

      expect(tester.takeException(), isNull);
    });

    testWidgets('Text tool opens TableSketchTextDialog and inputs cell text', (
      tester,
    ) async {
      tester.view.physicalSize = const Size(1024, 900);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final calls = <List<Object?>>[];
      Future<Object?> api(String name, List<Object?> args) async {
        calls.add([name, ...args]);
        return {'ok': true};
      }

      await tester.pumpWidget(MaterialApp(home: TableSketchScreen(api: api)));
      await tester.pumpAndSettle();

      // 글 도구 선택
      await tester.tap(find.byKey(const Key('toolText')));
      await tester.pumpAndSettle();

      // 캔버스 칸 탭
      final canvasFinder = find.byKey(const Key('sketchCanvas'));
      await tester.tapAt(
        tester.getTopLeft(canvasFinder) + const Offset(48, 48),
      );
      await tester.pumpAndSettle();

      // 대화상자 확인 (StatefulWidget으로 TextEditingController 소유)
      expect(find.byType(TableSketchTextDialog), findsOneWidget);
      expect(find.byKey(const Key('sketchTextInput')), findsOneWidget);

      await tester.enterText(find.byKey(const Key('sketchTextInput')), '총괄팀');
      await tester.tap(find.byKey(const Key('sketchTextBold'))); // 굵게 체크
      await tester.pumpAndSettle();

      await tester.tap(find.byKey(const Key('sketchTextConfirm')));
      await tester.pumpAndSettle();

      expect(find.byType(TableSketchTextDialog), findsNothing);

      // 디바운스 대기
      await tester.pump(const Duration(milliseconds: 600));
      await tester.pumpAndSettle();

      final previewCalls = calls
          .where((c) => c[0] == 'table_sketch' && c[1] == 'preview')
          .toList();
      expect(previewCalls.isNotEmpty, isTrue);
      final lastSketch = previewCalls.last[2] as Map;
      final texts = (lastSketch['texts'] as List).cast<Map>();
      expect(texts.length, 1);
      expect(texts.first['text'], '총괄팀');
      expect(texts.first['bold'], isTrue);

      expect(tester.takeException(), isNull);
    });

    testWidgets(
      'Org chart example creates exactly 21 lines and updates preview',
      (tester) async {
        tester.view.physicalSize = const Size(1024, 900);
        tester.view.devicePixelRatio = 1.0;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);

        final calls = <List<Object?>>[];
        Future<Object?> api(String name, List<Object?> args) async {
          calls.add([name, ...args]);
          if (name == 'table_sketch') {
            final action = args[0] as String;
            if (action == 'preview') {
              final sketch = args[1] as Map;
              final lines = sketch['lines'] as List;
              return {
                'ok': true,
                'rows': 6,
                'cols': 10,
                'cells': List.generate(
                  lines.length,
                  (i) => {'row': i, 'col': 0, 'rowspan': 1, 'colspan': 1},
                ),
                'width_mm': 180.0,
                'height_mm': 120.0,
                'warnings': [],
              };
            }
          }
          return {'ok': true};
        }

        await tester.pumpWidget(MaterialApp(home: TableSketchScreen(api: api)));
        await tester.pumpAndSettle();

        // 조직도 예시 버튼 클릭
        expect(find.byKey(const Key('sketchOrgExample')), findsOneWidget);
        await tester.tap(find.byKey(const Key('sketchOrgExample')));
        await tester.pumpAndSettle();

        // 디바운스 0.5초 경과
        await tester.pump(const Duration(milliseconds: 600));
        await tester.pumpAndSettle();

        // 조직도 예시 생성 후 preview가 21개 선을 담고 전송되었는지 확인
        final previewCalls = calls
            .where((c) => c[0] == 'table_sketch' && c[1] == 'preview')
            .toList();
        expect(previewCalls.isNotEmpty, isTrue);

        final lastPreview = previewCalls.last;
        final sketch = lastPreview[2] as Map;
        final lines = sketch['lines'] as List;
        // 위 상자 4개 + 가운데 세로선 1개 + 가로 연결선 1개 + 하향 연결선 3개 + 아래 상자 3개(각 4개 = 12개) = 총 21개 선
        expect(lines.length, 21);

        // 텍스트는 4개
        final texts = sketch['texts'] as List;
        expect(texts.length, 4);

        expect(tester.takeException(), isNull);
      },
    );

    testWidgets('preview, copy, and save calls match backend bridge contract', (
      tester,
    ) async {
      tester.view.physicalSize = const Size(1024, 900);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final calls = <List<Object?>>[];
      Future<Object?> api(String name, List<Object?> args) async {
        calls.add([name, ...args]);
        if (name == 'table_sketch') {
          final action = args[0] as String;
          if (action == 'preview') {
            return {
              'ok': true,
              'rows': 5,
              'cols': 8,
              'cells': [
                {'row': 0, 'col': 0, 'rowspan': 1, 'colspan': 1},
              ],
              'width_mm': 180.0,
              'height_mm': 250.0,
              'warnings': ['경고 예시: 고립된 선이 있습니다.'],
            };
          }
          if (action == 'copy') {
            return {'ok': true, 'message': '한/글에서 Ctrl+V로 붙여넣으세요.'};
          }
          if (action == 'save') {
            return {'ok': true, 'message': '저장 완료'};
          }
        }
        return {'ok': true};
      }

      await tester.pumpWidget(MaterialApp(home: TableSketchScreen(api: api)));
      await tester.pumpAndSettle();

      // 1. preview 결과가 화면에 잘 반영되었는지 확인
      expect(find.textContaining('5행 × 8열'), findsOneWidget);
      expect(find.textContaining('고립된 선이 있습니다'), findsOneWidget);

      // 2. copy 호출 및 스낵바 확인
      expect(find.byKey(const Key('sketchCopyButton')), findsOneWidget);
      await tester.tap(find.byKey(const Key('sketchCopyButton')));
      await tester.pumpAndSettle();

      final copyCalls = calls
          .where((c) => c[0] == 'table_sketch' && c[1] == 'copy')
          .toList();
      expect(copyCalls.length, 1);
      final copyPayload = copyCalls.first[2] as Map;
      expect(copyPayload.containsKey('grid'), isTrue);
      expect(copyPayload.containsKey('lines'), isTrue);
      expect(copyPayload.containsKey('texts'), isTrue);

      expect(find.text('한/글에서 Ctrl+V로 붙여넣으세요.'), findsOneWidget);

      // 3. save 호출 확인
      await tester.enterText(
        find.byKey(const Key('sketchNameField')),
        '조직도_최종',
      );
      await tester.tap(find.byKey(const Key('sketchSaveButton')));
      await tester.pumpAndSettle();

      final saveCalls = calls
          .where((c) => c[0] == 'table_sketch' && c[1] == 'save')
          .toList();
      expect(saveCalls.length, 1);
      final savePayload = saveCalls.first[2] as Map;
      expect(savePayload['name'], '조직도_최종');
      expect((savePayload['sketch'] as Map).containsKey('grid'), isTrue);

      expect(tester.takeException(), isNull);
    });

    testWidgets(
      'TableSketchScreen renders without overflow at narrow width 420',
      (tester) async {
        tester.view.physicalSize = const Size(420, 800);
        tester.view.devicePixelRatio = 1.0;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);

        Future<Object?> api(String name, List<Object?> args) async {
          return {
            'ok': true,
            'rows': 3,
            'cols': 3,
            'cells': [],
            'width_mm': 15.0,
            'height_mm': 15.0,
            'warnings': [],
          };
        }

        await tester.pumpWidget(MaterialApp(home: TableSketchScreen(api: api)));
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('tableSketchScreen')), findsOneWidget);
        expect(find.byKey(const Key('sketchCanvas')), findsOneWidget);
        expect(find.byKey(const Key('sketchCopyButton')), findsOneWidget);

        // RenderFlex overflow가 발생하지 않음 확인
        expect(tester.takeException(), isNull);
      },
    );
  });
}
