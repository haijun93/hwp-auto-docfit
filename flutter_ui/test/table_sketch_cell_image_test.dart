import 'package:docfit_ui/features/table_sketch/table_sketch_models.dart';
import 'package:docfit_ui/features/table_sketch/table_sketch_screen.dart';
import 'package:docfit_ui/features/table_sketch/table_sketch_selection.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

// 1×1 빨간 PNG
const redPng =
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg==';

TableSketchDoc twoByTwo() => TableSketchDoc(
  grid: const GridConfig(cols: 20, rows: 20),
  lines: [
    const SketchLine(x1: 0, y1: 0, x2: 8, y2: 0),
    const SketchLine(x1: 0, y1: 4, x2: 8, y2: 4),
    const SketchLine(x1: 0, y1: 8, x2: 8, y2: 8),
    const SketchLine(x1: 0, y1: 0, x2: 0, y2: 8),
    const SketchLine(x1: 4, y1: 0, x2: 4, y2: 8),
    const SketchLine(x1: 8, y1: 0, x2: 8, y2: 8),
  ],
);

void main() {
  test('cellRegion finds the enclosed cell and rejects open areas', () {
    final doc = twoByTwo();
    expect(cellRegion(doc, 1, 1), const Rect.fromLTRB(0, 0, 4, 4));
    expect(cellRegion(doc, 6, 7), const Rect.fromLTRB(4, 4, 8, 8));
    expect(cellRegion(doc, 12, 12), isNull); // 표 밖
    // 오른쪽 아래 칸의 오른쪽 선을 지우면 열린 영역이 된다.
    doc.lines.removeLast();
    doc.lines.add(const SketchLine(x1: 8, y1: 0, x2: 8, y2: 4));
    expect(cellRegion(doc, 6, 7), isNull);
    expect(cellRegion(doc, 6, 1), const Rect.fromLTRB(4, 0, 8, 4));
  });

  test(
    'setCellImage replaces within the same cell, removeCellImage clears it',
    () {
      final doc = twoByTwo();
      expect(setCellImage(doc, 1, 1, redPng), isTrue);
      expect(setCellImage(doc, 3, 2, redPng), isTrue); // 같은 칸 → 바꿈
      expect(doc.images, hasLength(1));
      expect([doc.images.single.x, doc.images.single.y], [3, 2]);
      expect(setCellImage(doc, 12, 12, redPng), isFalse);
      expect(removeCellImage(doc, 0, 0), isTrue);
      expect(doc.images, isEmpty);
      // 저장 형식: 그림이 없으면 images 키를 쓰지 않는다(예전 파일과 같음)
      expect(doc.toJson().containsKey('images'), isFalse);
      setCellImage(doc, 5, 5, redPng);
      final round = TableSketchDoc.fromJson(doc.toJson());
      expect(round.images.single.data, redPng);
      expect(round.clone().images, hasLength(1));
    },
  );

  testWidgets(
    'dropping a photo on a table cell sets its background; Delete removes it; undo restores',
    (tester) async {
      tester.view.physicalSize = const Size(1400, 900);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final previews = <Map>[];
      var clipboardCalls = 0;
      Future<Object?> api(String name, List<Object?> args) async {
        if (name == 'table_sketch' && args[0] == 'preview') {
          previews.add(args[1] as Map);
          return {
            'ok': true,
            'rows': 0,
            'cols': 0,
            'cells': [],
            'warnings': [],
          };
        }
        if (name == 'table_sketch' && args[0] == 'clipboard_image') {
          clipboardCalls++;
          return {'ok': true, 'data': redPng, 'kind': 'png'};
        }
        return {'ok': true};
      }

      await tester.pumpWidget(MaterialApp(home: TableSketchScreen(api: api)));
      await tester.pumpAndSettle();
      final origin = tester.getTopLeft(find.byKey(const Key('sketchCanvas')));
      Offset at(double gx, double gy) => origin + Offset(gx * 16, gy * 16);
      // 사각형 하나(칸 1개)
      await tester.tap(find.byKey(const Key('toolRect')));
      await tester.pumpAndSettle();
      final g = await tester.startGesture(at(2, 2));
      await g.moveTo(at(8, 6));
      await g.up();
      await tester.pumpAndSettle();

      Future<List> images() async {
        await tester.pump(const Duration(milliseconds: 600));
        await tester.pumpAndSettle();
        return (previews.last['images'] as List?) ?? const [];
      }

      // 끌어 놓기(창 이벤트 대신 같은 처리 함수 호출): 칸 안 → 들어감, 칸 밖 → 안내
      final state = tester.state(find.byType(TableSketchScreen)) as dynamic;
      expect(
        state.applyDroppedImageAt(const Offset(5 * 16, 4 * 16), redPng),
        isTrue,
      );
      await tester.pump();
      expect(await images(), hasLength(1));
      expect(
        state.applyDroppedImageAt(const Offset(15 * 16, 15 * 16), redPng),
        isFalse,
      );
      await tester.pump();
      expect(find.text('사진은 선으로 둘러싸인 표 칸 안에 놓아 주세요.'), findsOneWidget);
      expect(find.byKey(const Key('sketchRemoveImage')), findsOneWidget);

      // Delete → 지움, Ctrl+Z → 되살림
      await tester.tapAt(at(4, 4));
      await tester.pumpAndSettle();
      await tester.sendKeyEvent(LogicalKeyboardKey.delete);
      expect(await images(), isEmpty);
      await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
      await tester.sendKeyEvent(LogicalKeyboardKey.keyZ);
      await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
      await tester.pumpAndSettle();
      await tester.tapAt(at(4, 4)); // 미리보기 다시 요청되게 한 번 더 누름
      expect(await images(), hasLength(1));

      // 칸을 누르고 Ctrl+V → 클립보드 사진
      await tester.tap(find.byKey(const Key('sketchRemoveImage')));
      await tester.pumpAndSettle();
      expect(await images(), isEmpty);
      await tester.tapAt(at(3, 3));
      await tester.pumpAndSettle();
      await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
      await tester.sendKeyEvent(LogicalKeyboardKey.keyV);
      await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
      await tester.pumpAndSettle();
      expect(clipboardCalls, 1);
      expect(await images(), hasLength(1));
      expect(tester.takeException(), isNull);
    },
  );
}
