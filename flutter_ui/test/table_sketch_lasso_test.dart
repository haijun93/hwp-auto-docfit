import 'package:docfit_ui/features/table_sketch/table_sketch_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets(
    'lasso selects drawn lines, drag moves them, Ctrl+D duplicates, Delete removes',
    (tester) async {
      tester.view.physicalSize = const Size(1400, 900);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final previews = <Map>[];
      Future<Object?> api(String name, List<Object?> args) async {
        if (name == 'table_sketch' && args[0] == 'preview') {
          previews.add(args[1] as Map);
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
        return {'ok': true};
      }

      await tester.pumpWidget(MaterialApp(home: TableSketchScreen(api: api)));
      await tester.pumpAndSettle();
      final origin = tester.getTopLeft(find.byKey(const Key('sketchCanvas')));
      Offset at(double gx, double gy) => origin + Offset(gx * 16, gy * 16);

      Future<void> drag(List<Offset> points) async {
        final g = await tester.startGesture(points.first);
        for (final p in points.skip(1)) {
          await g.moveTo(p);
          await tester.pump();
        }
        await g.up();
        await tester.pumpAndSettle();
      }

      Future<List<Map>> lines() async {
        await tester.pump(const Duration(milliseconds: 600));
        await tester.pumpAndSettle();
        return (previews.last['lines'] as List).cast<Map>();
      }

      // 사각형(2,2)-(6,5) 그리기
      await tester.tap(find.byKey(const Key('toolRect')));
      await tester.pumpAndSettle();
      await drag([at(2, 2), at(6, 5)]);
      expect(await lines(), hasLength(4));

      // 올가미로 자유롭게 둘러 고르기
      await tester.tap(find.byKey(const Key('toolLasso')));
      await tester.pumpAndSettle();
      expect(find.text('올가미'), findsOneWidget);
      await drag([
        at(1, 1),
        at(4, .8),
        at(7, 1),
        at(7.2, 3),
        at(7, 6),
        at(4, 6.3),
        at(1, 6),
        at(.8, 3),
      ]);
      expect(find.text('4개 선택'), findsOneWidget);

      // 고른 영역 안을 끌어 오른쪽으로 3칸, 아래로 1칸 옮기기
      await drag([at(4, 3.5), at(5.5, 4), at(7, 4.5)]);
      final moved = await lines();
      expect(moved, hasLength(4));
      final xs = moved.expand((l) => [l['x1'], l['x2']]).cast<int>();
      final ys = moved.expand((l) => [l['y1'], l['y2']]).cast<int>();
      expect(xs.reduce((a, b) => a < b ? a : b), 5);
      expect(ys.reduce((a, b) => a < b ? a : b), 3);

      // Ctrl+D 복제 → 8개, 복제본이 선택됨
      await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
      await tester.sendKeyEvent(LogicalKeyboardKey.keyD);
      await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
      expect(await lines(), hasLength(8));
      expect(find.text('4개 선택'), findsOneWidget);

      // Delete로 복제본만 지움
      await tester.sendKeyEvent(LogicalKeyboardKey.delete);
      expect(await lines(), hasLength(4));
      expect(find.byKey(const Key('sketchSelectionCount')), findsNothing);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('select tool box-drag picks several, shift-click toggles', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1400, 900);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    Future<Object?> api(String name, List<Object?> args) async =>
        name == 'table_sketch' && args[0] == 'preview'
        ? {'ok': true, 'rows': 0, 'cols': 0, 'cells': [], 'warnings': []}
        : {'ok': true};
    await tester.pumpWidget(MaterialApp(home: TableSketchScreen(api: api)));
    await tester.pumpAndSettle();
    final origin = tester.getTopLeft(find.byKey(const Key('sketchCanvas')));
    Offset at(double gx, double gy) => origin + Offset(gx * 16, gy * 16);

    // 가로선 두 개
    for (final y in [2.0, 6.0]) {
      final g = await tester.startGesture(at(2, y));
      await g.moveTo(at(8, y));
      await g.up();
      await tester.pumpAndSettle();
    }
    await tester.tap(find.byKey(const Key('toolSelect')));
    await tester.pumpAndSettle();
    final g = await tester.startGesture(at(1, 1));
    await g.moveTo(at(9, 7));
    await tester.pump();
    await g.up();
    await tester.pumpAndSettle();
    expect(find.text('2개 선택'), findsOneWidget);

    await tester.sendKeyDownEvent(LogicalKeyboardKey.shiftLeft);
    await tester.tapAt(at(5, 6));
    await tester.sendKeyUpEvent(LogicalKeyboardKey.shiftLeft);
    await tester.pumpAndSettle();
    expect(find.text('1개 선택'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'canvas press takes keyboard focus even when another screen autofocused first',
    (tester) async {
      tester.view.physicalSize = const Size(1400, 900);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      Future<Object?> api(String name, List<Object?> args) async =>
          name == 'table_sketch' && args[0] == 'preview'
          ? {'ok': true, 'rows': 0, 'cols': 0, 'cells': [], 'warnings': []}
          : {'ok': true};
      // 6탭 화면처럼 다른 화면의 자동 초점이 먼저 잡힌 상태
      await tester.pumpWidget(
        MaterialApp(
          home: Column(
            children: [
              const Focus(autofocus: true, child: SizedBox(height: 1)),
              Expanded(child: TableSketchScreen(api: api)),
            ],
          ),
        ),
      );
      await tester.pumpAndSettle();
      final origin = tester.getTopLeft(find.byKey(const Key('sketchCanvas')));
      final g = await tester.startGesture(origin + const Offset(32, 32));
      await g.moveTo(origin + const Offset(128, 32));
      await g.up();
      await tester.pumpAndSettle();
      await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
      await tester.sendKeyEvent(LogicalKeyboardKey.keyA);
      await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
      await tester.pumpAndSettle();
      expect(find.text('1개 선택'), findsOneWidget);
      expect(find.byKey(const Key('sketchSelectionBar')), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
}
