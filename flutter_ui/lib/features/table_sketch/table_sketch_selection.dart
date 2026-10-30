import 'dart:math' as math;
import 'dart:ui' show Offset, Rect;

import 'table_sketch_models.dart';

/// 표그림판에서 여러 개체(선·칸 글)를 함께 고른 상태. 번호는 [TableSketchDoc]의 목록 순서다.
class SketchSelection {
  SketchSelection({Set<int>? lines, Set<int>? texts})
    : lines = lines ?? <int>{},
      texts = texts ?? <int>{};

  final Set<int> lines;
  final Set<int> texts;

  bool get isEmpty => lines.isEmpty && texts.isEmpty;
  bool get isNotEmpty => !isEmpty;
  int get count => lines.length + texts.length;

  SketchSelection copy() =>
      SketchSelection(lines: {...lines}, texts: {...texts});

  /// 범위를 벗어난 번호를 버린다(되돌리기 등으로 문서가 바뀐 뒤).
  SketchSelection validFor(TableSketchDoc doc) => SketchSelection(
    lines: lines.where((i) => i >= 0 && i < doc.lines.length).toSet(),
    texts: texts.where((i) => i >= 0 && i < doc.texts.length).toSet(),
  );

  /// Shift로 더할 때: 이미 있던 것은 빼고 없던 것은 더한다(포토샵·파워포인트와 같은 토글).
  SketchSelection toggled(SketchSelection other) {
    final l = {...lines}, t = {...texts};
    for (final i in other.lines) {
      if (!l.remove(i)) l.add(i);
    }
    for (final i in other.texts) {
      if (!t.remove(i)) t.add(i);
    }
    return SketchSelection(lines: l, texts: t);
  }

  SketchSelection union(SketchSelection other) => SketchSelection(
    lines: {...lines, ...other.lines},
    texts: {...texts, ...other.texts},
  );
}

/// 복사해 둔 개체들.
class SketchClip {
  const SketchClip(this.lines, this.texts);
  final List<SketchLine> lines;
  final List<SketchText> texts;
  bool get isEmpty => lines.isEmpty && texts.isEmpty;
}

/// 짝수-홀수 규칙으로 점이 다각형 안에 있는지 본다.
bool pointInPolygon(Offset p, List<Offset> polygon) {
  if (polygon.length < 3) return false;
  var inside = false;
  for (var i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    final a = polygon[i], b = polygon[j];
    if ((a.dy > p.dy) != (b.dy > p.dy) &&
        p.dx < (b.dx - a.dx) * (p.dy - a.dy) / (b.dy - a.dy) + a.dx) {
      inside = !inside;
    }
  }
  return inside;
}

/// 올가미: 다각형(격자 단위 좌표) 안에 가운데가 든 **칸 구간만** 떼어 고른다.
/// 긴 선의 일부만 둘렀으면 그 부분을 별도 선으로 나눠(모양은 그대로) 그 조각만 고른다.
/// [keep]에 든 선(번호)은 나뉘어도 조각 모두를 계속 고른 상태로 둔다(Shift로 더 고를 때).
SketchSelection lassoSelect(
  TableSketchDoc doc,
  List<Offset> polygon, {
  Set<int> keep = const {},
}) {
  final lines = <SketchLine>[];
  final picked = <int>{};
  for (var index = 0; index < doc.lines.length; index++) {
    final line = doc.lines[index];
    final kept = keep.contains(index);
    if (!line.isValid) {
      if (kept) picked.add(lines.length);
      lines.add(line);
      continue;
    }
    final dx = (line.x2 - line.x1).sign, dy = (line.y2 - line.y1).sign;
    final n = line.lengthInUnits;
    final inside = [
      for (var k = 0; k < n; k++)
        pointInPolygon(
          Offset(line.x1 + dx * (k + .5), line.y1 + dy * (k + .5)),
          polygon,
        ),
    ];
    var start = 0;
    for (var k = 1; k <= n; k++) {
      if (k < n && inside[k] == inside[start]) continue;
      final piece = (start == 0 && k == n)
          ? line
          : line.copyWith(
              x1: line.x1 + dx * start,
              y1: line.y1 + dy * start,
              x2: line.x1 + dx * k,
              y2: line.y1 + dy * k,
            );
      if (inside[start] || kept) picked.add(lines.length);
      lines.add(piece);
      start = k;
    }
  }
  doc.lines = lines;
  final texts = <int>{
    for (var i = 0; i < doc.texts.length; i++)
      if (pointInPolygon(
        Offset(doc.texts[i].x + .5, doc.texts[i].y + .5),
        polygon,
      ))
        i,
  };
  return SketchSelection(lines: picked, texts: texts);
}

/// 한 번 눌러 고르기: 가장 가까운 선 하나(통째) 또는 누른 칸의 글.
SketchSelection hitSelect(TableSketchDoc doc, Offset grid, double tolerance) {
  int? best;
  var bestDist = double.infinity;
  for (var i = 0; i < doc.lines.length; i++) {
    final l = doc.lines[i];
    final d = _distanceToSegment(
      grid,
      Offset(l.x1.toDouble(), l.y1.toDouble()),
      Offset(l.x2.toDouble(), l.y2.toDouble()),
    );
    if (d <= tolerance && d < bestDist) {
      bestDist = d;
      best = i;
    }
  }
  final cx = grid.dx.floor(), cy = grid.dy.floor();
  final text = doc.texts.indexWhere((t) => t.x == cx && t.y == cy);
  // 글이 있는 칸 안쪽을 누르면 글이 우선(선은 칸 가장자리에 있다).
  if (text >= 0 &&
      (best == null || bestDist > .2 || _insideCellCore(grid, cx, cy))) {
    return SketchSelection(texts: {text});
  }
  return best == null ? SketchSelection() : SketchSelection(lines: {best});
}

bool _insideCellCore(Offset p, int cx, int cy) =>
    p.dx - cx > .25 && p.dx - cx < .75 && p.dy - cy > .25 && p.dy - cy < .75;

/// 고른 개체를 감싸는 사각형(격자 단위). 비었으면 null.
Rect? selectionBounds(TableSketchDoc doc, SketchSelection sel) {
  double? l, t, r, b;
  void add(num x1, num y1, num x2, num y2) {
    l = math.min(l ?? x1.toDouble(), math.min(x1, x2).toDouble());
    t = math.min(t ?? y1.toDouble(), math.min(y1, y2).toDouble());
    r = math.max(r ?? x2.toDouble(), math.max(x1, x2).toDouble());
    b = math.max(b ?? y2.toDouble(), math.max(y1, y2).toDouble());
  }

  for (final i in sel.lines) {
    if (i < 0 || i >= doc.lines.length) continue;
    final s = doc.lines[i];
    add(s.x1, s.y1, s.x2, s.y2);
  }
  for (final i in sel.texts) {
    if (i < 0 || i >= doc.texts.length) continue;
    final s = doc.texts[i];
    add(s.x, s.y, s.x + 1, s.y + 1);
  }
  return l == null ? null : Rect.fromLTRB(l!, t!, r!, b!);
}

/// 고른 개체를 (dx, dy)칸 옮긴다. 종이 밖으로 나가거나 다른 칸 글을 덮으면 옮기지 않고 false.
bool translateSelection(
  TableSketchDoc doc,
  SketchSelection sel,
  int dx,
  int dy,
) {
  if (sel.isEmpty || (dx == 0 && dy == 0)) return false;
  final cols = doc.grid.cols, rows = doc.grid.rows;
  for (final i in sel.lines) {
    final s = doc.lines[i];
    for (final (x, y) in [(s.x1 + dx, s.y1 + dy), (s.x2 + dx, s.y2 + dy)]) {
      if (x < 0 || y < 0 || x > cols || y > rows) return false;
    }
  }
  final moving = {for (final i in sel.texts) i};
  final occupied = {
    for (var i = 0; i < doc.texts.length; i++)
      if (!moving.contains(i)) (doc.texts[i].x, doc.texts[i].y),
  };
  for (final i in sel.texts) {
    final s = doc.texts[i];
    final x = s.x + dx, y = s.y + dy;
    if (x < 0 || y < 0 || x >= cols || y >= rows) return false;
    if (occupied.contains((x, y))) return false;
  }
  for (final i in sel.lines) {
    final s = doc.lines[i];
    doc.lines[i] = s.copyWith(
      x1: s.x1 + dx,
      y1: s.y1 + dy,
      x2: s.x2 + dx,
      y2: s.y2 + dy,
    );
  }
  for (final i in sel.texts) {
    final s = doc.texts[i];
    doc.texts[i] = s.copyWith(x: s.x + dx, y: s.y + dy);
  }
  return true;
}

SketchClip copySelection(TableSketchDoc doc, SketchSelection sel) => SketchClip(
  [
    for (final i in sel.lines.toList()..sort())
      if (i < doc.lines.length) doc.lines[i],
  ],
  [
    for (final i in sel.texts.toList()..sort())
      if (i < doc.texts.length) doc.texts[i],
  ],
);

/// 고른 개체를 지운다. 지운 것이 있으면 true.
bool deleteSelection(TableSketchDoc doc, SketchSelection sel) {
  if (sel.isEmpty) return false;
  doc.lines = [
    for (var i = 0; i < doc.lines.length; i++)
      if (!sel.lines.contains(i)) doc.lines[i],
  ];
  doc.texts = [
    for (var i = 0; i < doc.texts.length; i++)
      if (!sel.texts.contains(i)) doc.texts[i],
  ];
  return true;
}

/// 복사해 둔 개체를 (dx, dy)칸 어긋나게 붙인다. 종이 밖으로 나가면 안쪽으로 당긴다.
/// 붙인 개체가 새 선택이 된다. 붙일 수 없으면(종이보다 크면) null.
SketchSelection? pasteClip(
  TableSketchDoc doc,
  SketchClip clip,
  int dx,
  int dy,
) {
  if (clip.isEmpty) return null;
  var minX = 1 << 30, minY = 1 << 30, maxX = -1, maxY = -1;
  for (final s in clip.lines) {
    minX = math.min(minX, math.min(s.x1, s.x2));
    minY = math.min(minY, math.min(s.y1, s.y2));
    maxX = math.max(maxX, math.max(s.x1, s.x2));
    maxY = math.max(maxY, math.max(s.y1, s.y2));
  }
  for (final s in clip.texts) {
    minX = math.min(minX, s.x);
    minY = math.min(minY, s.y);
    maxX = math.max(maxX, s.x + 1);
    maxY = math.max(maxY, s.y + 1);
  }
  final cols = doc.grid.cols, rows = doc.grid.rows;
  if (maxX - minX > cols || maxY - minY > rows) return null;
  dx = dx.clamp(-minX, cols - maxX);
  dy = dy.clamp(-minY, rows - maxY);
  final sel = SketchSelection();
  for (final s in clip.lines) {
    final moved = s.copyWith(
      x1: s.x1 + dx,
      y1: s.y1 + dy,
      x2: s.x2 + dx,
      y2: s.y2 + dy,
    );
    final same = doc.lines.indexWhere(
      (l) => l.isSameCoords(moved.x1, moved.y1, moved.x2, moved.y2),
    );
    if (same >= 0) {
      doc.lines[same] = moved;
      sel.lines.add(same);
    } else {
      sel.lines.add(doc.lines.length);
      doc.lines.add(moved);
    }
  }
  for (final s in clip.texts) {
    final moved = s.copyWith(x: s.x + dx, y: s.y + dy);
    doc.setText(moved);
    final idx = doc.texts.indexWhere((t) => t.x == moved.x && t.y == moved.y);
    if (idx >= 0) sel.texts.add(idx);
  }
  return sel;
}

/// 정밀 지우개: 점(격자 단위)이 **안쪽에** 놓인 칸 구간 하나를 찾는다.
/// 칸 끝(격자점) 근처는 어느 쪽에도 속하지 않게 해, 끌어 지울 때 지나간 칸만 지운다.
(int, int, int, int)? unitSegmentAt(
  TableSketchDoc doc,
  Offset p, {
  double perpendicular = .45,
}) {
  (int, int, int, int)? best;
  var bestDist = double.infinity;
  for (final line in doc.lines) {
    if (!line.isValid) continue;
    final dx = (line.x2 - line.x1).sign, dy = (line.y2 - line.y1).sign;
    final len2 = (dx * dx + dy * dy).toDouble();
    for (var k = 0; k < line.lengthInUnits; k++) {
      final ax = line.x1 + dx * k, ay = line.y1 + dy * k;
      final t = ((p.dx - ax) * dx + (p.dy - ay) * dy) / len2;
      if (t <= .1 || t >= .9) continue;
      final px = ax + dx * t, py = ay + dy * t;
      final d = math.sqrt(
        (p.dx - px) * (p.dx - px) + (p.dy - py) * (p.dy - py),
      );
      if (d <= perpendicular && d < bestDist) {
        bestDist = d;
        best = (ax, ay, ax + dx, ay + dy);
      }
    }
  }
  return best;
}

/// 두 점 사이를 칸의 1/4 간격으로 나눈 점들(빠르게 끌어도 지나간 칸을 빠뜨리지 않게).
List<Offset> samplePath(Offset from, Offset to, double step) {
  final distance = (to - from).distance;
  final n = math.max(1, (distance / step).ceil());
  return [for (var i = 1; i <= n; i++) Offset.lerp(from, to, i / n)!];
}

double _distanceToSegment(Offset p, Offset a, Offset b) {
  final ab = b - a, ap = p - a;
  final len2 = ab.dx * ab.dx + ab.dy * ab.dy;
  if (len2 == 0) return (p - a).distance;
  final t = ((ap.dx * ab.dx + ap.dy * ab.dy) / len2).clamp(0.0, 1.0);
  return (p - Offset(a.dx + t * ab.dx, a.dy + t * ab.dy)).distance;
}

/// 격자 칸 (x, y)가 든 표 칸(선으로 둘러싸인 영역)의 사각형(격자 단위).
/// 선이 끊겨 종이 끝까지 열려 있으면 표 칸이 아니므로 null.
Rect? cellRegion(TableSketchDoc doc, int x, int y) {
  final cols = doc.grid.cols, rows = doc.grid.rows;
  if (x < 0 || y < 0 || x >= cols || y >= rows) return null;
  final horizontal = <(int, int)>{}; // (x, y): (x,y)-(x+1,y) 가로 칸 경계
  final vertical = <(int, int)>{}; // (x, y): (x,y)-(x,y+1) 세로 칸 경계
  for (final line in doc.lines) {
    if (!line.isValid) continue;
    if (line.y1 == line.y2) {
      for (
        var k = math.min(line.x1, line.x2);
        k < math.max(line.x1, line.x2);
        k++
      ) {
        horizontal.add((k, line.y1));
      }
    } else if (line.x1 == line.x2) {
      for (
        var k = math.min(line.y1, line.y2);
        k < math.max(line.y1, line.y2);
        k++
      ) {
        vertical.add((line.x1, k));
      }
    }
  }
  final seen = <(int, int)>{(x, y)};
  final queue = <(int, int)>[(x, y)];
  var minX = x, maxX = x, minY = y, maxY = y;
  while (queue.isNotEmpty) {
    final (cx, cy) = queue.removeLast();
    minX = math.min(minX, cx);
    maxX = math.max(maxX, cx);
    minY = math.min(minY, cy);
    maxY = math.max(maxY, cy);
    for (final (nx, ny, blocked) in [
      (cx - 1, cy, vertical.contains((cx, cy))),
      (cx + 1, cy, vertical.contains((cx + 1, cy))),
      (cx, cy - 1, horizontal.contains((cx, cy))),
      (cx, cy + 1, horizontal.contains((cx, cy + 1))),
    ]) {
      if (blocked) continue;
      if (nx < 0 || ny < 0 || nx >= cols || ny >= rows) return null; // 열린 영역
      if (seen.add((nx, ny))) queue.add((nx, ny));
    }
  }
  return Rect.fromLTRB(
    minX.toDouble(),
    minY.toDouble(),
    maxX + 1.0,
    maxY + 1.0,
  );
}

/// 칸 배경 그림을 넣는다: 같은 칸에 있던 그림은 바꾼다. 표 칸이 아니면 false.
bool setCellImage(TableSketchDoc doc, int x, int y, String data) {
  final region = cellRegion(doc, x, y);
  if (region == null) return false;
  removeCellImage(doc, x, y);
  doc.images.add(SketchImage(x: x, y: y, data: data));
  return true;
}

/// (x, y)가 든 칸의 배경 그림을 지운다. 지운 것이 있으면 true.
bool removeCellImage(TableSketchDoc doc, int x, int y) {
  final region = cellRegion(doc, x, y);
  final before = doc.images.length;
  doc.images.removeWhere(
    (image) => region == null
        ? image.x == x && image.y == y
        : region.contains(Offset(image.x + .5, image.y + .5)),
  );
  return doc.images.length != before;
}

/// 한 번 눌러 '모형' 고르기: 누른 선이 따로 그린 사각형의 한 변이면 네 변을 함께,
/// 아니면 이어진 한 직선(쪼개진 조각 포함)을 통째로 고른다. 글 칸은 hitSelect와 같다.
SketchSelection shapeSelect(TableSketchDoc doc, Offset grid, double tolerance) {
  final hit = hitSelect(doc, grid, tolerance);
  if (hit.lines.length != 1) return hit;
  final index = hit.lines.single;
  final seg = _AxisSeg.of(doc.lines[index], index);
  if (seg == null) return hit; // 대각선은 그 선만
  final segs = [
    for (var i = 0; i < doc.lines.length; i++) ?_AxisSeg.of(doc.lines[i], i),
  ];
  return SketchSelection(
    lines: _rectangleThrough(segs, seg) ?? _chain(segs, seg).indices,
  );
}

class _AxisSeg {
  const _AxisSeg(this.horizontal, this.at, this.lo, this.hi, this.index);
  final bool horizontal;
  final int at, lo, hi, index;

  static _AxisSeg? of(SketchLine l, int index) {
    if (l.y1 == l.y2 && l.x1 != l.x2) {
      return _AxisSeg(
        true,
        l.y1,
        math.min(l.x1, l.x2),
        math.max(l.x1, l.x2),
        index,
      );
    }
    if (l.x1 == l.x2 && l.y1 != l.y2) {
      return _AxisSeg(
        false,
        l.x1,
        math.min(l.y1, l.y2),
        math.max(l.y1, l.y2),
        index,
      );
    }
    return null;
  }
}

typedef _Chain = ({Set<int> indices, int lo, int hi});

/// 같은 줄 위에서 맞닿거나 겹치는 조각을 모두 이은 직선.
_Chain _chain(List<_AxisSeg> segs, _AxisSeg start) {
  final indices = {start.index};
  var lo = start.lo, hi = start.hi;
  var grown = true;
  while (grown) {
    grown = false;
    for (final s in segs) {
      if (s.horizontal != start.horizontal || s.at != start.at) continue;
      if (indices.contains(s.index) || s.hi < lo || s.lo > hi) continue;
      indices.add(s.index);
      lo = math.min(lo, s.lo);
      hi = math.max(hi, s.hi);
      grown = true;
    }
  }
  return (indices: indices, lo: lo, hi: hi);
}

/// at 줄 위에서 [from, to] 한 칸을 덮는 조각에서 시작한 직선.
_Chain? _chainCovering(
  List<_AxisSeg> segs,
  bool horizontal,
  int at,
  int from,
  int to,
) {
  final a = math.min(from, to), b = math.max(from, to);
  for (final s in segs) {
    if (s.horizontal == horizontal && s.at == at && s.lo <= a && s.hi >= b) {
      return _chain(segs, s);
    }
  }
  return null;
}

/// 누른 선이 네 변이 꼭 맞물린(바깥으로 삐져나간 선이 없는) 사각형의 변이면 그 네 변.
Set<int>? _rectangleThrough(List<_AxisSeg> segs, _AxisSeg seg) {
  final side = _chain(segs, seg);
  final a = side.lo, b = side.hi, at = seg.at;
  for (final d in const [1, -1]) {
    final left = _chainCovering(segs, !seg.horizontal, a, at, at + d);
    final right = _chainCovering(segs, !seg.horizontal, b, at, at + d);
    if (left == null || right == null) continue;
    // 모서리에서 끝나야 한다(표처럼 이어진 선이면 사각형 모형이 아니다).
    final leftEnd = d > 0 ? left.hi : left.lo;
    final rightEnd = d > 0 ? right.hi : right.lo;
    final leftStart = d > 0 ? left.lo : left.hi;
    final rightStart = d > 0 ? right.lo : right.hi;
    if (leftStart != at || rightStart != at || leftEnd != rightEnd) continue;
    final opposite = _chainCovering(segs, seg.horizontal, leftEnd, a, a + 1);
    if (opposite == null || opposite.lo != a || opposite.hi != b) continue;
    return {
      ...side.indices,
      ...left.indices,
      ...right.indices,
      ...opposite.indices,
    };
  }
  return null;
}

/// 고른 것이 따로 선 사각형 하나이면 그 테두리(격자 단위), 아니면 null.
Rect? selectedRectangle(TableSketchDoc doc, SketchSelection sel) {
  if (sel.texts.isNotEmpty || sel.lines.length < 4) return null;
  final segs = [
    for (var i = 0; i < doc.lines.length; i++) ?_AxisSeg.of(doc.lines[i], i),
  ];
  final first = sel.lines.first;
  if (first < 0 || first >= doc.lines.length) return null;
  final seg = _AxisSeg.of(doc.lines[first], first);
  if (seg == null) return null;
  final rect = _rectangleThrough(segs, seg);
  if (rect == null ||
      rect.length != sel.lines.length ||
      !rect.containsAll(sel.lines)) {
    return null;
  }
  return selectionBounds(doc, sel);
}

/// 사각형 네 변(테두리 굵기·종류는 그대로).
List<SketchLine> rectangleLines(
  Rect r, {
  String width = 'thin',
  String style = 'solid',
}) {
  final l = r.left.round(),
      t = r.top.round(),
      ri = r.right.round(),
      b = r.bottom.round();
  return [
    SketchLine(x1: l, y1: t, x2: ri, y2: t, width: width, style: style),
    SketchLine(x1: l, y1: b, x2: ri, y2: b, width: width, style: style),
    SketchLine(x1: l, y1: t, x2: l, y2: b, width: width, style: style),
    SketchLine(x1: ri, y1: t, x2: ri, y2: b, width: width, style: style),
  ];
}

/// 고른 사각형을 새 테두리로 바꾸고, 새 네 변을 고른 상태로 돌려준다.
SketchSelection resizeRectangle(
  TableSketchDoc doc,
  SketchSelection sel,
  Rect bounds,
) {
  final sample = doc.lines[sel.lines.first];
  for (final i in sel.lines.toList()..sort((a, b) => b.compareTo(a))) {
    doc.lines.removeAt(i);
  }
  final start = doc.lines.length;
  doc.lines.addAll(
    rectangleLines(bounds, width: sample.width, style: sample.style),
  );
  return SketchSelection(
    lines: {for (var i = start; i < doc.lines.length; i++) i},
  );
}

/// 옮기거나 크기를 바꾸는 동안 다른 개체와 가장자리·가운데가 맞는 세로(x)·가로(y) 위치(격자 단위).
({Set<double> xs, Set<double> ys}) alignmentGuides(
  TableSketchDoc doc,
  SketchSelection sel,
) {
  final bounds = selectionBounds(doc, sel);
  if (bounds == null) return (xs: <double>{}, ys: <double>{});
  final otherXs = <double>{}, otherYs = <double>{};
  for (var i = 0; i < doc.lines.length; i++) {
    if (sel.lines.contains(i)) continue;
    final l = doc.lines[i];
    otherXs.addAll([l.x1.toDouble(), l.x2.toDouble()]);
    otherYs.addAll([l.y1.toDouble(), l.y2.toDouble()]);
    // 다른 선의 가운데도 맞춤 기준이 된다.
    otherXs.add((l.x1 + l.x2) / 2);
    otherYs.add((l.y1 + l.y2) / 2);
  }
  return (
    xs: {bounds.left, bounds.center.dx, bounds.right}.intersection(otherXs),
    ys: {bounds.top, bounds.center.dy, bounds.bottom}.intersection(otherYs),
  );
}
