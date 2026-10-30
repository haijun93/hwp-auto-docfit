import 'package:docfit_ui/features/table_sketch/table_sketch_models.dart';
import 'package:docfit_ui/features/table_sketch/table_sketch_screen.dart';
import 'package:docfit_ui/features/table_sketch/table_sketch_selection.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

SketchLine h(int x1, int x2, int y) => SketchLine(x1: x1, y1: y, x2: x2, y2: y);
SketchLine v(int x, int y1, int y2) => SketchLine(x1: x, y1: y1, x2: x, y2: y2);

/// 표그림판: 한 번 눌러 사각형·직선 모형 고르기, Shift+클릭으로 여러 개(2026-10-30 사용자 요청).
void main() {
  test(
    'clicking any side of a standalone rectangle selects its four sides',
    () {
      final doc = TableSketchDoc(
        grid: const GridConfig(cols: 30, rows: 30),
        lines: [h(2, 8, 2), h(2, 8, 6), v(2, 2, 6), v(8, 2, 6), h(12, 20, 4)],
      );
      for (final p in const [
        Offset(5, 2),
        Offset(5, 6),
        Offset(2, 4),
        Offset(8, 4),
      ]) {
        expect(shapeSelect(doc, p, .5).lines, {0, 1, 2, 3}, reason: '$p');
      }
      expect(shapeSelect(doc, const Offset(15, 4), .5).lines, {4});
    },
  );

  test('a rectangle whose sides were split still selects as one shape', () {
    final doc = TableSketchDoc(
      grid: const GridConfig(cols: 30, rows: 30),
      lines: [
        h(2, 5, 2),
        h(5, 8, 2),
        h(2, 8, 6),
        v(2, 2, 6),
        v(8, 2, 4),
        v(8, 4, 6),
      ],
    );
    expect(shapeSelect(doc, const Offset(3, 2), .5).lines, {0, 1, 2, 3, 4, 5});
  });

  test('inside a table grid a click selects the whole straight line only', () {
    final doc = TableSketchDoc(
      grid: const GridConfig(cols: 30, rows: 30),
      lines: [
        h(0, 10, 0),
        h(0, 10, 3),
        h(0, 10, 6),
        v(0, 0, 6),
        v(5, 0, 6),
        v(10, 0, 6),
      ],
    );
    // 가운데 가로선은 위·아래로 이어진 세로선 때문에 사각형 모형이 아니다.
    expect(shapeSelect(doc, const Offset(2, 3), .5).lines, {1});
    // 조각난 직선은 이어서 한 줄로.
    final split = TableSketchDoc(
      grid: const GridConfig(cols: 30, rows: 30),
      lines: [h(0, 3, 9), h(3, 7, 9), h(7, 12, 9)],
    );
    expect(shapeSelect(split, const Offset(5, 9), .5).lines, {0, 1, 2});
  });

  testWidgets(
    'one click selects a rectangle, shift+click adds a line, drag moves both',
    (tester) async {
      tester.view.physicalSize = const Size(1400, 900);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final previews = <Map>[];
      Future<Object?> api(String name, List<Object?> args) async {
        if (name == 'table_sketch' && args[0] == 'preview') {
          previews.add(args[1] as Map);
        }
        return {
          'ok': true,
          'rows': 1,
          'cols': 1,
          'cells': [],
          'width_mm': 10.0,
          'height_mm': 10.0,
          'warnings': [],
        };
      }

      await tester.pumpWidget(MaterialApp(home: TableSketchScreen(api: api)));
      await tester.pumpAndSettle();
      final origin = tester.getTopLeft(find.byKey(const Key('sketchCanvas')));
      Offset at(double gx, double gy) => origin + Offset(gx * 16, gy * 16);
      Future<void> drag(Offset a, Offset b) async {
        final g = await tester.startGesture(a);
        await g.moveTo((a + b) / 2);
        await tester.pump();
        await g.moveTo(b);
        await tester.pump();
        await g.up();
        await tester.pumpAndSettle();
      }

      await tester.tap(find.byKey(const Key('toolRect')));
      await tester.pumpAndSettle();
      await drag(at(2, 2), at(6, 5));
      await tester.tap(find.byKey(const Key('toolLine')));
      await tester.pumpAndSettle();
      await drag(at(10, 8), at(16, 8));

      // 그리기 도구 그대로 사각형 변을 한 번 누르면 사각형 모형이 골라진다.
      await tester.tapAt(at(4, 2));
      await tester.pumpAndSettle();
      expect(find.text('4개 선택'), findsOneWidget);

      // Shift+클릭으로 직선을 더한다.
      await tester.sendKeyDownEvent(LogicalKeyboardKey.shiftLeft);
      await tester.tapAt(at(13, 8));
      await tester.sendKeyUpEvent(LogicalKeyboardKey.shiftLeft);
      await tester.pumpAndSettle();
      expect(find.text('5개 선택'), findsOneWidget);

      // 고른 것을 끌면 함께 옮겨진다.
      await drag(at(4, 2), at(4, 5));
      await tester.pump(const Duration(milliseconds: 600));
      await tester.pumpAndSettle();
      final lines = (previews.last['lines'] as List).cast<Map>();
      final ys = {
        for (final l in lines) ...[l['y1'], l['y2']],
      };
      expect(ys, containsAll([5, 8, 11]), reason: '$lines');
      expect(ys.contains(2), isFalse, reason: '$lines');
    },
  );
}
