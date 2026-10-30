import 'package:docfit_ui/features/table_sketch/table_sketch_models.dart';
import 'package:docfit_ui/features/table_sketch/table_sketch_screen.dart';
import 'package:docfit_ui/features/table_sketch/table_sketch_selection.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// 표그림판 사각형: 눌러 놓기 → 손잡이로 크기 조절, 맞춤 안내선(2026-10-30 사용자 요청).
void main() {
  test('alignment guides report edges and centers that match other lines', () {
    final doc = TableSketchDoc(
      grid: const GridConfig(cols: 40, rows: 40),
      lines: [
        ...rectangleLines(const Rect.fromLTRB(2, 2, 10, 6)),
        const SketchLine(x1: 10, y1: 20, x2: 18, y2: 20),
      ],
    );
    final sel = SketchSelection(lines: {0, 1, 2, 3});
    expect(selectedRectangle(doc, sel), const Rect.fromLTRB(2, 2, 10, 6));
    final g = alignmentGuides(doc, sel);
    expect(g.xs, {10.0}); // 오른쪽 변 = 다른 선의 시작
    expect(g.ys, isEmpty);
    final moved = resizeRectangle(doc, sel, const Rect.fromLTRB(2, 2, 14, 6));
    expect(selectedRectangle(doc, moved), const Rect.fromLTRB(2, 2, 14, 6));
    expect(alignmentGuides(doc, moved).xs, {14.0}); // 가운데(14) = 다른 선 가운데
  });

  testWidgets('rect tool click places a rectangle; corner handle resizes it', (
    tester,
  ) async {
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
    Future<List<Map>> lines() async {
      await tester.pump(const Duration(milliseconds: 600));
      await tester.pumpAndSettle();
      return (previews.last['lines'] as List).cast<Map>();
    }

    await tester.tap(find.byKey(const Key('toolRect')));
    await tester.pumpAndSettle();
    await tester.tapAt(at(3, 3));
    await tester.pumpAndSettle();
    var ls = await lines();
    expect(ls, hasLength(4));
    expect(
      {
        for (final l in ls) ...[l['x1'], l['x2']],
      },
      {3, 11},
    );
    expect(
      {
        for (final l in ls) ...[l['y1'], l['y2']],
      },
      {3, 7},
    );
    expect(find.text('4개 선택'), findsOneWidget); // 놓자마자 골라져 손잡이가 보인다

    // 오른쪽 아래 손잡이를 (15, 9)로 끈다.
    final g = await tester.startGesture(at(11, 7));
    await g.moveTo(at(13, 8));
    await tester.pump();
    await g.moveTo(at(15, 9));
    await tester.pump();
    await g.up();
    await tester.pumpAndSettle();
    ls = await lines();
    expect(ls, hasLength(4));
    expect(
      {
        for (final l in ls) ...[l['x1'], l['x2']],
      },
      {3, 15},
    );
    expect(
      {
        for (final l in ls) ...[l['y1'], l['y2']],
      },
      {3, 9},
    );
  });
}
