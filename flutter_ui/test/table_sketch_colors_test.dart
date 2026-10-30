import 'package:docfit_ui/features/table_sketch/table_sketch_models.dart';
import 'package:docfit_ui/features/table_sketch/table_sketch_screen.dart';
import 'package:docfit_ui/features/table_sketch/table_sketch_selection.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// 표그림판 선 색·사각형 배경색(2.0.7 사용자 요청, 그림판과 같은 26색).
void main() {
  test(
    'line color and fills round-trip; moving a rectangle moves its fill',
    () {
      final doc = TableSketchDoc(
        grid: const GridConfig(cols: 40, rows: 40),
        lines: rectangleLines(
          const Rect.fromLTRB(2, 2, 10, 6),
          color: '#DC2626',
        ),
      );
      doc.setFill(2, 2, 10, 6, '#FEF9C3');
      final json = doc.toJson(forTable: true);
      expect((json['lines'] as List).first['color'], '#DC2626');
      expect(json['fills'], [
        {'x1': 2, 'y1': 2, 'x2': 10, 'y2': 6, 'color': '#FEF9C3'},
      ]);
      final back = TableSketchDoc.fromJson(json);
      expect(back.lines.first.color, '#DC2626');
      expect(back.fills.single.color, '#FEF9C3');
      // 검정 선은 색을 싣지 않는다(예전 저장본과 같다).
      expect(
        const SketchLine(x1: 0, y1: 0, x2: 1, y2: 0).toJson(),
        isNot(contains('color')),
      );

      final sel = SketchSelection(lines: {0, 1, 2, 3});
      expect(translateSelection(doc, sel, 3, 1), isTrue);
      expect(doc.fills.single.x1, 5);
      expect(doc.fills.single.y2, 7);
      resizeRectangle(doc, sel, const Rect.fromLTRB(5, 3, 15, 9));
      expect(doc.fills.single.x2, 15);
      expect(doc.lines.last.color, '#DC2626');
      doc.setFill(5, 3, 15, 9, null);
      expect(doc.fills, isEmpty);
    },
  );

  testWidgets('toolbar picks line color for new rectangle and fills it', (
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

    // 고른 것 없이 배경을 누르면 안내만 한다.
    await tester.tap(find.byKey(const Key('fillColorButton')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('fillColorButton-#FDE047')));
    await tester.pumpAndSettle();
    expect(find.textContaining('먼저 고르세요'), findsOneWidget);

    await tester.tap(find.byKey(const Key('lineColorButton')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('lineColorButton-none')), findsNothing);
    await tester.tap(find.byKey(const Key('lineColorButton-#1D4ED8')));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('toolRect')));
    await tester.pumpAndSettle();
    await tester.tapAt(at(3, 3));
    await tester.pumpAndSettle();
    // 놓자마자 골라진 사각형에 배경을 칠한다(직접 입력).
    await tester.tap(find.byKey(const Key('fillColorButton')));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const Key('fillColorButton-hex')),
      '#fce4d6',
    );
    await tester.tap(find.byKey(const Key('fillColorButton-apply')));
    await tester.pumpAndSettle();
    await tester.pump(const Duration(milliseconds: 600));
    await tester.pumpAndSettle();
    final last = previews.last;
    expect(
      {for (final l in (last['lines'] as List).cast<Map>()) l['color']},
      {'#1D4ED8'},
    );
    expect(last['fills'], [
      {'x1': 3, 'y1': 3, 'x2': 11, 'y2': 7, 'color': '#FCE4D6'},
    ]);

    // '없음'은 배경을 지운다.
    await tester.tap(find.byKey(const Key('fillColorButton')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('fillColorButton-none')));
    await tester.pumpAndSettle();
    await tester.pump(const Duration(milliseconds: 600));
    await tester.pumpAndSettle();
    expect(previews.last['fills'], isNull);
  });
}
