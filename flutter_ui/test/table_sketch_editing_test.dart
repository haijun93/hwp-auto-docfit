import 'package:docfit_ui/features/table_sketch/table_sketch_models.dart';
import 'package:docfit_ui/features/table_sketch/table_sketch_screen.dart';
import 'package:docfit_ui/features/table_sketch/table_sketch_selection.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

/// 표그림판 편집(TODO 표그림판 (2)~(5)·(7)·(9)): 묶기/풀기, 비율 유지 크기, 스마트 가이드·자석 맞춤,
/// 선 끝점 손잡이, 한/글 굵기 목록·혼합 표시, 선으로 나뉜 칸별 배경색.
void main() {
  group('model', () {
    test('line widths follow the Hangul list and keep old names', () {
      expect(sketchLineWidthMms, hasLength(16));
      expect(sketchWidthFromMm('0.12'), 'thin');
      expect(sketchWidthFromMm('0.4'), 'thick');
      expect(sketchWidthFromMm('1.5'), '1.5 mm');
      expect(sketchWidthLabel('thin'), '0.12 mm');
      expect(sketchWidthLabel('2.0 mm'), '2.0 mm');
      expect(sketchWidthLabel('double'), '이중');
      expect(isSketchWidth('0.25 mm'), isTrue);
      expect(isSketchWidth('9 mm'), isFalse);
      expect(sketchStrokePx('5.0 mm') > sketchStrokePx('0.5 mm'), isTrue);
      final back = SketchLine.fromJson({
        'x1': 0, 'y1': 0, 'x2': 3, 'y2': 0, //
        'width': '0.7 mm', 'group': 'g1',
      });
      expect(back.width, '0.7 mm');
      expect(back.group, 'g1');
      expect(
        SketchLine.fromJson({'x1': 0, 'y1': 0, 'x2': 1, 'y2': 0, 'width': 'x'})
            .width,
        'thin',
      );
    });

    test('regions split by a line are separate cells with own colors', () {
      final doc = TableSketchDoc(
        grid: const GridConfig(cols: 20, rows: 20),
        lines: [
          ...rectangleLines(const Rect.fromLTRB(0, 0, 4, 4)),
          const SketchLine(x1: 0, y1: 2, x2: 4, y2: 2),
          const SketchLine(x1: 10, y1: 10, x2: 14, y2: 10), // 열린 선
        ],
      );
      final top = regionCells(doc, 1, 1)!;
      final bottom = regionCells(doc, 1, 3)!;
      expect(top, hasLength(8));
      expect(top.every((c) => c.$2 < 2), isTrue);
      expect(bottom, hasLength(8));
      expect(regionCells(doc, 11, 11), isNull); // 닫히지 않은 영역은 칸이 아니다
      expect(cellRegion(doc, 1, 3), const Rect.fromLTRB(0, 2, 4, 4));

      doc.setFill(0, 0, 4, 4, '#FFFFFF'); // 예전 방식의 사각형 하나 채움
      doc.paintCells(top, '#FDE047');
      expect(doc.fillAt(1, 1), '#FDE047');
      expect(doc.fillAt(1, 3), '#FFFFFF'); // 다른 칸은 그대로
      doc.paintCells(top, null);
      expect(doc.fillAt(1, 1), isNull);
      expect(doc.fillAt(3, 3), '#FFFFFF');

      // 사각형을 옮기면 칸 색도 따라간다(칸 단위 채움).
      doc.paintCells(top, '#DBEAFE');
      final rect = SketchSelection(lines: {0, 1, 2, 3, 4});
      expect(translateSelection(doc, rect, 5, 0), isTrue);
      expect(doc.fillAt(6, 1), '#DBEAFE');
      expect(doc.fillAt(1, 1), isNull);
    });

    test('group, expand, ungroup and paste keeps group structure', () {
      final doc = TableSketchDoc(
        grid: const GridConfig(cols: 40, rows: 40),
        lines: [
          ...rectangleLines(const Rect.fromLTRB(1, 1, 5, 3)),
          ...rectangleLines(const Rect.fromLTRB(10, 1, 14, 3)),
        ],
        texts: [const SketchText(x: 2, y: 1, text: '가')],
      );
      final all = SketchSelection(lines: {0, 1, 2, 3, 4, 5, 6, 7}, texts: {0});
      expect(groupSelection(doc, SketchSelection(lines: {0})), isFalse);
      expect(groupSelection(doc, all), isTrue);
      expect(selectedGroups(doc, all), hasLength(1));
      // 한 모형만 눌러도 묶음 전체가 골라진다.
      final picked = expandGroups(doc, shapeSelect(doc, const Offset(3, 1), .3));
      expect(picked.count, 9);
      // 저장에는 묶음이 남고, 한/글 표 변환 자료에는 싣지 않는다.
      expect((doc.toJson()['lines'] as List).first['group'], isNotNull);
      expect(
        (doc.toJson(forTable: true)['lines'] as List).first,
        isNot(contains('group')),
      );
      // 붙여넣은 묶음은 새 묶음 id(원래 묶음과 따로 움직인다).
      final clip = copySelection(doc, picked);
      final pasted = pasteClip(doc, clip, 0, 10)!;
      final groups = selectedGroups(doc, pasted);
      expect(groups, hasLength(1));
      expect(groups.intersection(selectedGroups(doc, picked)), isEmpty);
      expect(ungroupSelection(doc, picked), isTrue);
      expect(expandGroups(doc, SketchSelection(lines: {0})).count, 1);
    });

    test('scaling a group keeps line shapes and moves texts and fills', () {
      final doc = TableSketchDoc(
        grid: const GridConfig(cols: 40, rows: 40),
        lines: [
          ...rectangleLines(const Rect.fromLTRB(0, 0, 4, 4)),
          const SketchLine(x1: 0, y1: 0, x2: 4, y2: 4),
        ],
        texts: [const SketchText(x: 3, y: 3, text: '끝')],
      );
      doc.paintCells({(0, 0)}, '#FEE2E2');
      final sel = SketchSelection(lines: {0, 1, 2, 3, 4}, texts: {0});
      scaleSelection(
        doc,
        sel,
        const Rect.fromLTRB(0, 0, 4, 4),
        const Rect.fromLTRB(0, 0, 8, 8),
      );
      expect(selectionBounds(doc, sel), const Rect.fromLTRB(0, 0, 8, 8));
      expect(doc.lines.every((l) => l.isValid), isTrue);
      expect(doc.lines[4].x2, 8);
      expect(doc.lines[4].y2, 8);
      expect((doc.texts.single.x, doc.texts.single.y), (7, 7));
      expect(doc.fillAt(1, 1), '#FEE2E2'); // 1칸 → 2×2칸
      expect(doc.fillAt(2, 2), isNull);
    });

    test('resize bounds keeps aspect ratio when asked', () {
      const start = Rect.fromLTRB(0, 0, 8, 4);
      expect(resizeBounds(start, 4, 12, 5), const Rect.fromLTRB(0, 0, 12, 5));
      expect(
        resizeBounds(start, 4, 12, 5, keepRatio: true),
        const Rect.fromLTRB(0, 0, 12, 6),
      );
      expect(
        resizeBounds(start, 3, 16, 0, keepRatio: true),
        const Rect.fromLTRB(0, 0, 16, 8),
      );
    });

    test('smart guides show equal spacing and size and snap by distance', () {
      final doc = TableSketchDoc(
        grid: const GridConfig(cols: 40, rows: 40),
        lines: [
          ...rectangleLines(const Rect.fromLTRB(0, 0, 4, 4)),
          ...rectangleLines(const Rect.fromLTRB(20, 0, 24, 4)),
          ...rectangleLines(const Rect.fromLTRB(9, 0, 13, 4)), // 옮길 것
        ],
      );
      final sel = SketchSelection(lines: {8, 9, 10, 11});
      final targets = guideTargets(doc, sel);
      expect(targets.boxes, hasLength(2));
      // 왼쪽에 1칸 치우친 자리 → 같은 간격(10)으로 붙는다.
      expect(snapMove(const Rect.fromLTRB(9, 0, 13, 4), 0, 0, targets, 1), (
        1,
        0,
      ));
      // 끄면(거리 0) 그대로.
      expect(snapMove(const Rect.fromLTRB(9, 0, 13, 4), 0, 0, targets, 0), (
        0,
        0,
      ));
      final guides = smartGuides(const Rect.fromLTRB(10, 0, 14, 4), targets);
      expect(guides.spacing, hasLength(2));
      expect(guides.ys, containsAll([0.0, 2.0, 4.0]));
      expect(guides.sameSize, hasLength(2));
      expect(
        smartGuides(const Rect.fromLTRB(10, 10, 15, 15), targets).spacing,
        isEmpty,
      );
      // 크기 바꾸기: 오른쪽 변이 다른 개체와 같은 너비(4)로 붙는다.
      expect(
        snapResize(const Rect.fromLTRB(9, 10, 14, 15), 3, targets, 1),
        const Rect.fromLTRB(9, 10, 13, 15),
      );
    });

    test('endpoint handle hit only for a single line or arrow', () {
      final doc = TableSketchDoc(
        lines: [const SketchLine(x1: 2, y1: 2, x2: 8, y2: 2)],
        arrows: [const SketchArrow(x1: 2, y1: 6, x2: 8, y2: 6)],
      );
      expect(
        endpointAt(doc, SketchSelection(lines: {0}), const Offset(8.2, 2), .5),
        (arrow: false, index: 0, end: 1),
      );
      expect(
        endpointAt(doc, SketchSelection(arrows: {0}), const Offset(2, 6), .5),
        (arrow: true, index: 0, end: 0),
      );
      expect(
        endpointAt(doc, SketchSelection(lines: {0}), const Offset(5, 2), .5),
        isNull,
      );
      expect(
        endpointAt(
          doc,
          SketchSelection(lines: {0}, arrows: {0}),
          const Offset(8, 2),
          .5,
        ),
        isNull,
      );
    });
  });

  group('screen', () {
    late List<Map> previews;
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

    Future<Offset Function(double, double)> open(WidgetTester tester) async {
      previews = [];
      tester.view.physicalSize = const Size(1500, 900);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      await tester.pumpWidget(MaterialApp(home: TableSketchScreen(api: api)));
      await tester.pumpAndSettle();
      final origin = tester.getTopLeft(find.byKey(const Key('sketchCanvas')));
      return (gx, gy) => origin + Offset(gx * 16, gy * 16);
    }

    Future<Map> settled(WidgetTester tester) async {
      await tester.pump(const Duration(milliseconds: 600));
      await tester.pumpAndSettle();
      return previews.last;
    }

    Future<void> drag(WidgetTester tester, Offset from, Offset to) async {
      final g = await tester.startGesture(from);
      await g.moveTo(Offset.lerp(from, to, .5)!);
      await tester.pump();
      await g.moveTo(to);
      await tester.pump();
      await g.up();
      await tester.pumpAndSettle();
    }

    Future<void> placeRect(WidgetTester tester, Offset at) async {
      await tester.tap(find.byKey(const Key('toolRect')));
      await tester.pumpAndSettle();
      await tester.tapAt(at);
      await tester.pumpAndSettle();
    }

    Future<void> pickFill(WidgetTester tester, String hex) async {
      await tester.tap(find.byKey(const Key('fillColorButton')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(Key('fillColorButton-$hex')));
      await tester.pumpAndSettle();
    }

    testWidgets('cell color tool paints each divided cell separately', (
      tester,
    ) async {
      final at = await open(tester);
      await placeRect(tester, at(3, 3)); // (3,3)-(11,7)
      await tester.tap(find.byKey(const Key('toolLine')));
      await tester.pumpAndSettle();
      await drag(tester, at(3, 5), at(11, 5)); // 가로 직선으로 이등분
      await tester.tap(find.byKey(const Key('toolCellFill')));
      await tester.pumpAndSettle();

      await tester.tapAt(at(5.5, 3.5));
      await tester.pumpAndSettle();
      expect(find.text('칸 16격자 선택'), findsOneWidget);
      await pickFill(tester, '#FDE047');
      await tester.tapAt(at(5.5, 6.5));
      await tester.pumpAndSettle();
      await pickFill(tester, '#DBEAFE');
      var fills = ((await settled(tester))['fills'] as List).cast<Map>();
      expect(fills, hasLength(32));
      expect(
        fills.where((f) => f['color'] == '#FDE047').every((f) => f['y1'] < 5),
        isTrue,
      );
      expect(
        fills.where((f) => f['color'] == '#DBEAFE').every((f) => f['y1'] >= 5),
        isTrue,
      );
      // 테두리·분할선은 그대로(채움은 선을 지우지 않는다).
      expect((previews.last['lines'] as List), hasLength(5));

      // Delete: 고른 칸(아래)의 배경만 지운다.
      await tester.sendKeyEvent(LogicalKeyboardKey.delete);
      await tester.pumpAndSettle();
      fills = ((await settled(tester))['fills'] as List).cast<Map>();
      expect(fills, hasLength(16));
      expect(fills.every((f) => f['color'] == '#FDE047'), isTrue);

      // 닫히지 않은 곳을 누르면 칸이 아니라고 알린다.
      await tester.tapAt(at(30, 30));
      await tester.pumpAndSettle();
      expect(find.textContaining('닫힌 칸'), findsOneWidget);
    });

    testWidgets('width menu applies Hangul mm widths and shows mixed', (
      tester,
    ) async {
      final at = await open(tester);
      await placeRect(tester, at(3, 3));
      await tester.tap(find.byKey(const Key('lineWidthMenu')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('lineWidth-1.5')).last);
      await tester.pumpAndSettle();
      var lines = ((await settled(tester))['lines'] as List).cast<Map>();
      expect({for (final l in lines) l['width']}, {'1.5 mm'});
      expect(
        tester.widget<Text>(find.byKey(const Key('lineWidthMenuLabel'))).data,
        '1.5 mm',
      );

      // 얇은 선을 하나 더 긋고 모두 고르면 '혼합'.
      await tester.tap(find.byKey(const Key('toolLine')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('lineWidthThin')));
      await tester.pumpAndSettle();
      await drag(tester, at(3, 12), at(9, 12));
      await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
      await tester.sendKeyEvent(LogicalKeyboardKey.keyA);
      await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
      await tester.pumpAndSettle();
      expect(
        tester.widget<Text>(find.byKey(const Key('lineWidthMenuLabel'))).data,
        '혼합',
      );
      lines = ((await settled(tester))['lines'] as List).cast<Map>();
      expect({for (final l in lines) l['width']}, {'1.5 mm', 'thin'});
    });

    testWidgets('group moves together; ungroup separates again', (
      tester,
    ) async {
      final at = await open(tester);
      await placeRect(tester, at(3, 3)); // (3,3)-(11,7)
      await placeRect(tester, at(20, 3)); // (20,3)-(28,7)
      await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
      await tester.sendKeyEvent(LogicalKeyboardKey.keyA);
      await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('sketchGroup')));
      await tester.pumpAndSettle();
      await tester.sendKeyEvent(LogicalKeyboardKey.escape);
      await tester.pumpAndSettle();

      // 한 사각형만 눌러도 묶음 전체(8개)가 골라지고 함께 옮겨진다.
      await tester.tapAt(at(5, 3));
      await tester.pumpAndSettle();
      expect(find.text('8개 선택'), findsOneWidget);
      await drag(tester, at(5, 3), at(5, 13));
      var lines = ((await settled(tester))['lines'] as List).cast<Map>();
      expect({for (final l in lines) ...[l['y1'], l['y2']]}, {13, 17});

      // 묶음 풀기 → 다시 누르면 사각형 하나(4개)만.
      await tester.tap(find.byKey(const Key('sketchUngroup')));
      await tester.pumpAndSettle();
      await tester.sendKeyEvent(LogicalKeyboardKey.escape);
      await tester.pumpAndSettle();
      await tester.tapAt(at(5, 13));
      await tester.pumpAndSettle();
      expect(find.text('4개 선택'), findsOneWidget);
      lines = ((await settled(tester))['lines'] as List).cast<Map>();
      expect(lines.every((l) => !l.containsKey('group')), isTrue);
    });

    testWidgets('group corner handle resizes all with kept ratio', (
      tester,
    ) async {
      final at = await open(tester);
      await placeRect(tester, at(3, 3)); // (3,3)-(11,7)
      await placeRect(tester, at(20, 3)); // (20,3)-(28,7)
      await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
      await tester.sendKeyEvent(LogicalKeyboardKey.keyA);
      await tester.sendKeyEvent(LogicalKeyboardKey.keyG);
      await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('keepRatioToggle')));
      await tester.pumpAndSettle();
      // 묶음 테두리 (3,3)-(28,7)의 오른쪽 아래 손잡이를 (33, 7.4)로: 너비 30 → 높이 4×1.2≈5.
      await drag(tester, at(28, 7), at(33, 7.4));
      final lines = ((await settled(tester))['lines'] as List).cast<Map>();
      expect(lines, hasLength(8));
      expect(
        [
          for (final l in lines) ...[l['x1'] as int, l['x2'] as int],
        ].reduce((a, b) => a > b ? a : b),
        33,
      );
      expect({for (final l in lines) ...[l['y1'], l['y2']]}, {3, 8});
      // 두 사각형이 여전히 따로 있는 사각형 모양(가로·세로 선)이다.
      expect(
        lines.every((l) => l['x1'] == l['x2'] || l['y1'] == l['y2']),
        isTrue,
      );
    });

    testWidgets('dragging a line endpoint changes its length', (tester) async {
      final at = await open(tester);
      await tester.tap(find.byKey(const Key('toolLine')));
      await tester.pumpAndSettle();
      await drag(tester, at(3, 20), at(10, 20));
      await tester.tap(find.byKey(const Key('toolSelect')));
      await tester.pumpAndSettle();
      await tester.tapAt(at(6, 20));
      await tester.pumpAndSettle();
      expect(find.text('1개 선택'), findsOneWidget);
      await drag(tester, at(10, 20), at(15, 20));
      final line = ((await settled(tester))['lines'] as List).cast<Map>().single;
      expect(
        {line['x1'], line['x2']},
        {3, 15},
      );
      expect((line['y1'], line['y2']), (20, 20));
      // 되돌리기 한 번이면 원래 길이.
      await tester.tap(find.byKey(const Key('undoButton')));
      await tester.pumpAndSettle();
      final undone =
          ((await settled(tester))['lines'] as List).cast<Map>().single;
      expect({undone['x1'], undone['x2']}, {3, 10});
    });

    testWidgets('moving near another shape snaps to its edge unless off', (
      tester,
    ) async {
      final at = await open(tester);
      await placeRect(tester, at(3, 3)); // A: (3,3)-(11,7)
      await placeRect(tester, at(20, 10)); // B: (20,10)-(28,14), 골라진 상태
      // B의 위 변(22,10)을 잡아 위로 6칸 → 위 변 4, A 위 변(3)과 1칸 차이라 붙는다.
      await drag(tester, at(22, 10), at(22, 4));
      var lines = ((await settled(tester))['lines'] as List).cast<Map>();
      final b = lines.where((l) => l['x1'] as int >= 20).toList();
      expect({for (final l in b) ...[l['y1'], l['y2']]}, {3, 7});

      // 가이드를 끄면 붙지 않는다.
      await tester.tap(find.byKey(const Key('undoButton')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('smartGuideToggle')));
      await tester.pumpAndSettle();
      await tester.tapAt(at(22, 10));
      await tester.pumpAndSettle();
      await drag(tester, at(22, 10), at(22, 4));
      lines = ((await settled(tester))['lines'] as List).cast<Map>();
      final b2 = lines.where((l) => l['x1'] as int >= 20).toList();
      expect({for (final l in b2) ...[l['y1'], l['y2']]}, {4, 8});
    });
  });
}
