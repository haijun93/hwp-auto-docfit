import 'package:flutter_test/flutter_test.dart';

import '../lib/features/table_sketch/table_sketch_models.dart';

void main() {
  test('각 방향의 끝과 가운데 구간을 지우고 서식을 보존한다', () {
    for (final delta in [
      (3, 0),
      (-3, 0),
      (0, 3),
      (0, -3),
      (3, 3),
      (-3, -3),
      (3, -3),
      (-3, 3),
    ]) {
      final line = SketchLine(
        x1: 3,
        y1: 3,
        x2: 3 + delta.$1,
        y2: 3 + delta.$2,
        width: 'double',
        style: 'dot',
      );
      expect(line.lengthInUnits, 3);
      expect(line.splitAtUnitIndex(-1), [same(line)]);
      expect(line.splitAtUnitIndex(3), [same(line)]);
      for (var k = 0; k < 3; k++) {
        final parts = line.splitAtUnitIndex(k);
        expect(parts.length, k == 1 ? 2 : 1);
        expect(parts.fold<int>(0, (n, p) => n + p.lengthInUnits), 2);
        expect(
          parts.every(
            (p) => p.isValid && p.width == 'double' && p.style == 'dot',
          ),
          isTrue,
        );
        final ax = 3 + delta.$1.sign * k;
        final ay = 3 + delta.$2.sign * k;
        final reverse = line.splitByUnitSegment(
          ax + delta.$1.sign,
          ay + delta.$2.sign,
          ax,
          ay,
        );
        expect(
          reverse.map((p) => p.toJson()).toList(),
          parts.map((p) => p.toJson()).toList(),
        );
      }
    }
  });

  test('길이 1은 완전히 지우고 일치하지 않는 구간은 보존한다', () {
    const line = SketchLine(x1: 0, y1: 0, x2: 1, y2: 1);
    expect(line.splitAtUnitIndex(0), isEmpty);
    expect(line.splitByUnitSegment(0, 0, 2, 2), [same(line)]);
    expect(line.splitByUnitSegment(0, 1, 1, 0), [same(line)]);
    const empty = SketchLine(x1: 0, y1: 0, x2: 0, y2: 0);
    expect(empty.splitAtUnitIndex(0), [same(empty)]);
  });

  test('겹친 모든 선을 지우고 변경 여부를 반환한다', () {
    final doc = TableSketchDoc(
      lines: [
        const SketchLine(x1: 0, y1: 0, x2: 1, y2: 0),
        const SketchLine(x1: 2, y1: 0, x2: 0, y2: 0),
      ],
    );
    final original = doc.lines;
    expect(doc.eraseUnitSegment(0, 1, 1, 1), isFalse);
    expect(doc.lines, same(original));
    expect(doc.eraseUnitSegment(1, 0, 0, 0), isTrue);
    expect(doc.lines.single.isSameCoords(2, 0, 1, 0), isTrue);
    expect(doc.eraseUnitSegment(0, 0, 1, 0), isFalse);
    expect(doc.eraseUnitSegment(1, 0, 2, 0), isTrue);
    expect(doc.lines, isEmpty);
  });
}
