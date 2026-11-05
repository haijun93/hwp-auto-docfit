// TARGET:# N216E
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:docfit_ui/features/table_sketch/table_sketch_screen.dart';

void main() {
  test('hasMazeExamplePath validates the built-in 15x15 maze and rejects invalid grids', () {
    const maze = tableSketchMazeExampleRows;
    expect(maze, hasLength(15));
    expect(maze.every((row) => row.length == 15), isTrue);
    expect(maze.join().split('S'), hasLength(2));
    expect(maze.join().split('E'), hasLength(2));
    expect(hasMazeExamplePath(maze), isTrue);
    expect(hasMazeExamplePath(const ['S.E']), isTrue);
    expect(hasMazeExamplePath(const ['S#E']), isFalse);
    expect(hasMazeExamplePath(const ['S..', '..']), isFalse);
    expect(hasMazeExamplePath(const ['S.XE']), isFalse);
    expect(hasMazeExamplePath(const ['S.E', 'S..']), isFalse);
  });

  testWidgets('maze example loads, a selected cell can be edited, undone, and saved', (tester) async {
    final previews = <Map<String, dynamic>>[];
    final saves = <Map<String, dynamic>>[];
    Future<Object?> api(String command, List<Object?> args) async {
      if (command == 'table_sketch') {
        switch (args.first) {
          case 'load_draft':
            return {'exists': false};
          case 'preview':
            previews.add(Map<String, dynamic>.from(args[1] as Map));
            return {'ok': true, 'rows': 15, 'cols': 15, 'cells': []};
          case 'save':
            saves.add(Map<String, dynamic>.from(args[1] as Map));
            return {'ok': true};
        }
      }
      return {'ok': true};
    }

    await tester.pumpWidget(MaterialApp(home: TableSketchScreen(api: api)));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('sketchMazeExample')));
    await tester.pump(const Duration(milliseconds: 600));
    await tester.pumpAndSettle();
    expect(previews, isNotEmpty);
    final maze = previews.last;
    expect((maze['grid'] as Map)['cols'], 15);
    expect((maze['grid'] as Map)['rows'], 15);
    expect(maze['lines'], isNotEmpty);
    expect(maze['fills'], isNotEmpty);
    expect((maze['texts'] as List).map((e) => e['text']), containsAll(['S', 'E']));

    final linesBeforeEdit = List<Map<String, dynamic>>.from(
      (maze['lines'] as List).map((line) => Map<String, dynamic>.from(line as Map)),
    );
    final fillsBeforeEdit = List<Map<String, dynamic>>.from(
      (maze['fills'] as List).map((fill) => Map<String, dynamic>.from(fill as Map)),
    );
    final canvas = find.byKey(const Key('sketchCanvas'));
    final canvasRect = tester.getRect(canvas);
    // 선택 도구로 셀을 선택한 뒤 Delete로 실제 셀 선을 바꾼다.
    await tester.tap(find.byKey(const Key('toolSelect')));
    await tester.pumpAndSettle();
    await tester.dragFrom(
      Offset(canvasRect.left + 4 * 16.0, canvasRect.top + 5 * 16.0),
      const Offset(16, 0),
    );
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('undoButton')), findsOneWidget);
    await tester.sendKeyEvent(LogicalKeyboardKey.delete);
    await tester.pumpAndSettle();
    await tester.pump(const Duration(milliseconds: 600));
    await tester.pumpAndSettle();
    expect(previews.last['lines'], isNot(equals(linesBeforeEdit)));
    expect(previews.last['fills'], equals(fillsBeforeEdit));
    await tester.tap(find.byKey(const Key('undoButton')));
    await tester.pumpAndSettle();
    await tester.pump(const Duration(milliseconds: 600));
    await tester.pumpAndSettle();
    expect(previews.last['lines'], equals(linesBeforeEdit));
    expect(previews.last['fills'], equals(fillsBeforeEdit));

    await tester.enterText(find.byKey(const Key('sketchNameField')), 'maze');
    await tester.tap(find.byKey(const Key('sketchSaveButton')));
    await tester.pumpAndSettle();
    expect(saves, hasLength(1));
    final saved = saves.single['sketch'] as Map;
    expect((saved['grid'] as Map)['cols'], 15);
    expect((saved['grid'] as Map)['rows'], 15);
  });

  testWidgets('dinosaur example button remains available', (tester) async {
    final previews = <Map<String, dynamic>>[];
    Future<Object?> api(String command, List<Object?> args) async {
      if (command == 'table_sketch' && args.first == 'preview') {
        previews.add(Map<String, dynamic>.from(args[1] as Map));
        return {'ok': true};
      }
      if (command == 'table_sketch' && args.first == 'load_draft') {
        return {'exists': false};
      }
      return {'ok': true};
    }

    await tester.pumpWidget(MaterialApp(home: TableSketchScreen(api: api)));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('sketchDinoExample')));
    await tester.pump(const Duration(milliseconds: 600));
    await tester.pumpAndSettle();
    expect(previews, isNotEmpty);
    final dino = previews.last;
    expect((dino['grid'] as Map)['cols'], 66);
    expect((dino['grid'] as Map)['rows'], 27);
    expect(dino['fills'], isNotEmpty);
  });
}
