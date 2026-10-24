import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/features/table_sketch/table_sketch_models.dart';
import 'package:docfit_ui/features/table_sketch/table_sketch_screen.dart';

Future<Object?> mockTableSketchApi(String name, List<Object?> args) async {
  if (name == 'table_sketch') {
    final subcmd = args.isNotEmpty ? args[0] : null;
    if (subcmd == 'preview') {
      return {'ok': true, 'cell_count': 0, 'warnings': []};
    }
    if (subcmd == 'list') {
      return <String>[];
    }
  }
  return null;
}

void main() {
  group('splitLineAt pure function tests', () {
    test('1-cell line split returns empty list', () {
      const line = SketchLine(x1: 0, y1: 0, x2: 1, y2: 0);
      final result = splitLineAt(line, 0);
      expect(result, isEmpty);
    });

    test('3-cell horizontal line split at middle creates two 1-cell segments', () {
      const line = SketchLine(
        x1: 0,
        y1: 2,
        x2: 3,
        y2: 2,
        groupId: 'grpA',
        color: '#FF0000',
        widthMm: 1.5,
        width: 'thick',
        style: 'dash',
      );
      final result = splitLineAt(line, 1);
      expect(result.length, 2);

      expect(result[0].x1, 0);
      expect(result[0].y1, 2);
      expect(result[0].x2, 1);
      expect(result[0].y2, 2);
      expect(result[0].groupId, 'grpA');
      expect(result[0].color, '#FF0000');
      expect(result[0].widthMm, 1.5);
      expect(result[0].width, 'thick');
      expect(result[0].style, 'dash');

      expect(result[1].x1, 2);
      expect(result[1].y1, 2);
      expect(result[1].x2, 3);
      expect(result[1].y2, 2);
      expect(result[1].groupId, 'grpA');
      expect(result[1].color, '#FF0000');
      expect(result[1].widthMm, 1.5);
      expect(result[1].width, 'thick');
      expect(result[1].style, 'dash');
    });

    test('3-cell line split at start (index 0) returns remaining 2-cell tail', () {
      const line = SketchLine(x1: 0, y1: 2, x2: 3, y2: 2);
      final result = splitLineAt(line, 0);
      expect(result.length, 1);
      expect(result[0].x1, 1);
      expect(result[0].y1, 2);
      expect(result[0].x2, 3);
      expect(result[0].y2, 2);
    });

    test('3-cell line split at end (index 2) returns remaining 2-cell head', () {
      const line = SketchLine(x1: 0, y1: 2, x2: 3, y2: 2);
      final result = splitLineAt(line, 2);
      expect(result.length, 1);
      expect(result[0].x1, 0);
      expect(result[0].y1, 2);
      expect(result[0].x2, 2);
      expect(result[0].y2, 2);
    });

    test('invalid segment index returns original line in list', () {
      const line = SketchLine(x1: 0, y1: 0, x2: 3, y2: 0);
      expect(splitLineAt(line, -1), [line]);
      expect(splitLineAt(line, 3), [line]);
    });

    test('4-cell vertical line split at index 1', () {
      const line = SketchLine(x1: 5, y1: 0, x2: 5, y2: 4);
      final result = splitLineAt(line, 1);
      expect(result.length, 2);
      expect(result[0].x1, 5);
      expect(result[0].y1, 0);
      expect(result[0].x2, 5);
      expect(result[0].y2, 1);

      expect(result[1].x1, 5);
      expect(result[1].y1, 2);
      expect(result[1].x2, 5);
      expect(result[1].y2, 4);
    });

    test('3-cell diagonal line split at index 1', () {
      const line = SketchLine(x1: 0, y1: 0, x2: 3, y2: 3);
      final result = splitLineAt(line, 1);
      expect(result.length, 2);
      expect(result[0].x1, 0);
      expect(result[0].y1, 0);
      expect(result[0].x2, 1);
      expect(result[0].y2, 1);

      expect(result[1].x1, 2);
      expect(result[1].y1, 2);
      expect(result[1].x2, 3);
      expect(result[1].y2, 3);
    });

    test('reversed direction line split preserves coordinates correctly', () {
      const line = SketchLine(x1: 3, y1: 0, x2: 0, y2: 0);
      final result = splitLineAt(line, 1);
      expect(result.length, 2);
      expect(result[0].x1, 3);
      expect(result[0].y1, 0);
      expect(result[0].x2, 2);
      expect(result[0].y2, 0);

      expect(result[1].x1, 1);
      expect(result[1].y1, 0);
      expect(result[1].x2, 0);
      expect(result[1].y2, 0);
    });
  });

  group('findLineSegmentIndex and getLineSegment tests', () {
    test('findLineSegmentIndex finds correct cell segment', () {
      const line = SketchLine(x1: 0, y1: 0, x2: 4, y2: 0);
      const cellSize = 20.0;
      // Pos at (30, 2) is on segment 1 (x from 20 to 40)
      final segIdx = findLineSegmentIndex(line, const Offset(30, 2), cellSize);
      expect(segIdx, 1);

      final segLine = getLineSegment(line, 1);
      expect(segLine, isNotNull);
      expect(segLine!.x1, 1);
      expect(segLine.y1, 0);
      expect(segLine.x2, 2);
      expect(segLine.y2, 0);
    });

    test('findLineSegmentIndex returns null if click is too far', () {
      const line = SketchLine(x1: 0, y1: 0, x2: 4, y2: 0);
      final segIdx = findLineSegmentIndex(
        line,
        const Offset(30, 100),
        20.0,
        maxDistance: 10.0,
      );
      expect(segIdx, isNull);
    });
  });

  group('TableSketchDoc cell color and serialization tests', () {
    test('setCellColor and getCellColor manage cell colors', () {
      final doc = TableSketchDoc();
      expect(doc.getCellColor(2, 3), isNull);

      doc.setCellColor(2, 3, '#DBEAFE');
      expect(doc.getCellColor(2, 3), '#DBEAFE');

      // Update same cell
      doc.setCellColor(2, 3, '#FEF08A');
      expect(doc.getCellColor(2, 3), '#FEF08A');

      // White is an explicit fill; only an empty value removes it.
      doc.setCellColor(2, 3, '#FFFFFF');
      expect(doc.getCellColor(2, 3), '#FFFFFF');
      doc.setCellColor(2, 3, '');
      expect(doc.getCellColor(2, 3), isNull);
    });

    test('clone produces deep copy of cell colors and lines', () {
      final doc = TableSketchDoc(
        lines: [const SketchLine(x1: 0, y1: 0, x2: 2, y2: 0, groupId: 'g1')],
        cellColors: [const SketchCellColor(x: 1, y: 1, color: '#DBEAFE')],
      );
      final cloned = doc.clone();
      expect(cloned.lines.length, 1);
      expect(cloned.cellColors.length, 1);
      expect(cloned.cellColors.first.color, '#DBEAFE');

      cloned.setCellColor(1, 1, '#FFEDD5');
      expect(doc.getCellColor(1, 1), '#DBEAFE');
      expect(cloned.getCellColor(1, 1), '#FFEDD5');
    });

    test('toJson and fromJson serialize cell colors, group_id, color, width_mm', () {
      final doc = TableSketchDoc(
        lines: [
          const SketchLine(
            x1: 0,
            y1: 0,
            x2: 3,
            y2: 0,
            groupId: 'g99',
            color: '#123456',
            widthMm: 0.5,
          ),
        ],
        cellColors: [
          const SketchCellColor(x: 0, y: 0, color: '#DBEAFE'),
        ],
      );

      final json = doc.toJson();
      final revived = TableSketchDoc.fromJson(json);

      expect(revived.lines.length, 1);
      expect(revived.lines.first.groupId, 'g99');
      expect(revived.lines.first.color, '#123456');
      expect(revived.lines.first.widthMm, 0.5);

      expect(revived.cellColors.length, 1);
      expect(revived.cellColors.first.x, 0);
      expect(revived.cellColors.first.y, 0);
      expect(revived.cellColors.first.color, '#DBEAFE');
    });
  });

  group('TableSketchScreen widget tests', () {
    testWidgets('toolbar contains precise eraser, cell color, grouping, width mm dropdown', (
      tester,
    ) async {
      tester.view.physicalSize = const Size(1280, 900);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: TableSketchScreen(api: mockTableSketchApi),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Tool buttons
      expect(find.byKey(const Key('toolPreciseEraser')), findsOneWidget);
      expect(find.byKey(const Key('toolCellColor')), findsOneWidget);
      expect(find.byKey(const Key('toolSelect')), findsOneWidget);
      expect(find.byKey(const Key('toolLine')), findsOneWidget);

      // Grouping buttons
      expect(find.byKey(const Key('btnGroupLines')), findsOneWidget);
      expect(find.byKey(const Key('btnUngroupLines')), findsOneWidget);

      // Width mm dropdown
      expect(find.byKey(const Key('lineWidthMmDropdown')), findsOneWidget);
    });

    testWidgets('tool button selection switches tool state', (tester) async {
      tester.view.physicalSize = const Size(1280, 900);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: TableSketchScreen(api: mockTableSketchApi),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Tap toolPreciseEraser
      await tester.tap(find.byKey(const Key('toolPreciseEraser')));
      await tester.pumpAndSettle();

      // Tap cell color chip switches tool to cellColor
      await tester.tap(find.byKey(const Key('colorChip_#FEF08A')));
      await tester.pumpAndSettle();

      // Tap line tool switches back
      await tester.tap(find.byKey(const Key('toolLine')));
      await tester.pumpAndSettle();
    });
  });
}
