import 'package:docfit_ui/features/table_sketch/table_sketch_models.dart';
import 'package:docfit_ui/features/table_sketch/table_sketch_selection.dart';
import 'package:flutter_test/flutter_test.dart';

TableSketchDoc box() => TableSketchDoc(
  grid: const GridConfig(cols: 20, rows: 20),
  lines: [
    const SketchLine(x1: 2, y1: 2, x2: 10, y2: 2), // 위
    const SketchLine(x1: 2, y1: 8, x2: 10, y2: 8), // 아래
    const SketchLine(x1: 2, y1: 2, x2: 2, y2: 8), // 왼쪽
    const SketchLine(x1: 10, y1: 2, x2: 10, y2: 8, width: 'thick'), // 오른쪽
  ],
  texts: [const SketchText(x: 3, y: 3, text: '가')],
);

List<Offset> rect(double l, double t, double r, double b) => [
  Offset(l, t),
  Offset(r, t),
  Offset(r, b),
  Offset(l, b),
];

void main() {
  test('pointInPolygon handles a concave lasso', () {
    final poly = [
      const Offset(0, 0),
      const Offset(10, 0),
      const Offset(10, 10),
      const Offset(5, 4),
      const Offset(0, 10),
    ];
    expect(pointInPolygon(const Offset(2, 2), poly), isTrue);
    expect(pointInPolygon(const Offset(5, 8), poly), isFalse); // 오목한 곳
    expect(pointInPolygon(const Offset(11, 5), poly), isFalse);
  });

  test('lasso around part of a line splits it and selects only that part', () {
    final doc = box();
    // 위쪽 선의 x 4~7 구간만 둘렀다.
    final sel = lassoSelect(doc, rect(3.9, 1, 7.1, 3));
    expect(sel.lines, hasLength(1));
    final picked = doc.lines[sel.lines.single];
    expect([picked.x1, picked.y1, picked.x2, picked.y2], [4, 2, 7, 2]);
    // 나머지 조각은 그대로 남고, 전체 칸 수는 같다.
    final top = doc.lines.where((l) => l.y1 == 2 && l.y2 == 2).toList();
    expect(top.fold<int>(0, (n, l) => n + l.lengthInUnits), 8);
    expect(sel.texts, isEmpty);
  });

  test('lasso around the whole box selects all lines and the text', () {
    final doc = box();
    final sel = lassoSelect(doc, rect(1, 1, 11, 9));
    expect(sel.lines, hasLength(4));
    expect(sel.texts, {0});
    expect(doc.lines, hasLength(4)); // 쪼개지지 않음
  });

  test('shift-lasso keeps earlier pieces selected even when they split', () {
    final doc = box();
    final first = lassoSelect(doc, rect(1, 1, 11, 2.4)); // 위쪽 선 전체
    expect(first.lines, hasLength(1));
    final second = lassoSelect(
      doc,
      rect(9, 1, 11, 9), // 오른쪽 선 + 위쪽 선 끝 일부
      keep: first.lines,
    );
    final selected = second.lines.map((i) => doc.lines[i]).toList();
    // 위쪽 선은 나뉘었어도 모두 계속 선택, 오른쪽 선도 추가.
    expect(
      selected
          .where((l) => l.y1 == 2 && l.y2 == 2)
          .fold<int>(0, (n, l) => n + l.lengthInUnits),
      8,
    );
    expect(selected.any((l) => l.x1 == 10 && l.x2 == 10), isTrue);
  });

  test(
    'translate moves lines and texts together and refuses to leave paper',
    () {
      final doc = box();
      final all = SketchSelection(lines: {0, 1, 2, 3}, texts: {0});
      expect(translateSelection(doc, all, 3, 1), isTrue);
      expect([doc.lines[0].x1, doc.lines[0].y1], [5, 3]);
      expect([doc.texts[0].x, doc.texts[0].y], [6, 4]);
      expect(doc.lines[3].width, 'thick');
      expect(translateSelection(doc, all, 20, 0), isFalse);
      expect([doc.lines[0].x1, doc.lines[0].y1], [5, 3]); // 그대로
    },
  );

  test('translate will not drop a text onto another text', () {
    final doc = box()..texts.add(const SketchText(x: 4, y: 3, text: '나'));
    expect(translateSelection(doc, SketchSelection(texts: {0}), 1, 0), isFalse);
  });

  test('copy and paste shifts the copy and selects it', () {
    final doc = box();
    final clip = copySelection(doc, SketchSelection(lines: {3}, texts: {0}));
    final pasted = pasteClip(doc, clip, 2, 2)!;
    expect(doc.lines, hasLength(5));
    expect(doc.texts, hasLength(2));
    final line = doc.lines[pasted.lines.single];
    expect(
      [line.x1, line.y1, line.x2, line.y2, line.width],
      [12, 4, 12, 10, 'thick'],
    );
    final text = doc.texts[pasted.texts.single];
    expect([text.x, text.y, text.text], [5, 5, '가']);
  });

  test('paste near the edge is pulled back inside the paper', () {
    final doc = box();
    final clip = copySelection(doc, SketchSelection(lines: {0}));
    final pasted = pasteClip(doc, clip, 50, 50)!;
    final line = doc.lines[pasted.lines.single];
    expect(line.x2, 20);
    expect(line.y1, 20);
  });

  test('delete removes only the selection', () {
    final doc = box();
    expect(
      deleteSelection(doc, SketchSelection(lines: {0, 2}, texts: {0})),
      isTrue,
    );
    expect(doc.lines, hasLength(2));
    expect(doc.texts, isEmpty);
  });

  test('precise eraser hit ignores grid points so drags stay exact', () {
    final doc = box();
    // 오른쪽 선(x=10) 위의 격자점(10, 3)은 어느 칸에도 속하지 않는다.
    expect(unitSegmentAt(doc, const Offset(10, 3)), isNull);
    expect(unitSegmentAt(doc, const Offset(10.1, 3.5)), (10, 3, 10, 4));
    // y=3→7을 끌면 3~7의 네 칸만 지워진다.
    final hits = <(int, int, int, int)>{};
    for (final p in samplePath(const Offset(10, 3), const Offset(10, 7), .25)) {
      final hit = unitSegmentAt(doc, p);
      if (hit != null) hits.add(hit);
    }
    expect(hits, {
      (10, 3, 10, 4),
      (10, 4, 10, 5),
      (10, 5, 10, 6),
      (10, 6, 10, 7),
    });
  });

  test('hitSelect prefers the text inside a cell and toggles with shift', () {
    final doc = box();
    final text = hitSelect(doc, const Offset(3.5, 3.5), 1);
    expect(text.texts, {0});
    final line = hitSelect(doc, const Offset(5, 2.1), 1);
    expect(line.lines, {0});
    final both = text.toggled(line);
    expect(both.count, 2);
    expect(both.toggled(line).lines, isEmpty);
  });
}
