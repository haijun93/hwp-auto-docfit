import 'dart:math' as math;
import 'dart:ui' show Offset, Rect;

import 'table_sketch_models.dart';

/// 표그림판에서 여러 개체(선·칸 글)를 함께 고른 상태. 번호는 [TableSketchDoc]의 목록 순서다.
class SketchSelection {
  SketchSelection({Set<int>? lines, Set<int>? texts, Set<int>? arrows})
    : lines = lines ?? <int>{},
      texts = texts ?? <int>{},
      arrows = arrows ?? <int>{};

  final Set<int> lines;
  final Set<int> texts;
  final Set<int> arrows;

  bool get isEmpty => lines.isEmpty && texts.isEmpty && arrows.isEmpty;
  bool get isNotEmpty => !isEmpty;
  int get count => lines.length + texts.length + arrows.length;

  SketchSelection copy() => SketchSelection(
    lines: {...lines},
    texts: {...texts},
    arrows: {...arrows},
  );

  /// 범위를 벗어난 번호를 버린다(되돌리기 등으로 문서가 바뀐 뒤).
  SketchSelection validFor(TableSketchDoc doc) => SketchSelection(
    lines: lines.where((i) => i >= 0 && i < doc.lines.length).toSet(),
    texts: texts.where((i) => i >= 0 && i < doc.texts.length).toSet(),
    arrows: arrows.where((i) => i >= 0 && i < doc.arrows.length).toSet(),
  );

  /// Shift로 더할 때: 이미 있던 것은 빼고 없던 것은 더한다(포토샵·파워포인트와 같은 토글).
  SketchSelection toggled(SketchSelection other) {
    final l = {...lines}, t = {...texts}, a = {...arrows};
    for (final i in other.lines) {
      if (!l.remove(i)) l.add(i);
    }
    for (final i in other.texts) {
      if (!t.remove(i)) t.add(i);
    }
    for (final i in other.arrows) {
      if (!a.remove(i)) a.add(i);
    }
    return SketchSelection(lines: l, texts: t, arrows: a);
  }

  SketchSelection union(SketchSelection other) => SketchSelection(
    lines: {...lines, ...other.lines},
    texts: {...texts, ...other.texts},
    arrows: {...arrows, ...other.arrows},
  );
}

/// 복사해 둔 개체들.
class SketchClip {
  const SketchClip(this.lines, this.texts, [this.arrows = const []]);
  final List<SketchLine> lines;
  final List<SketchText> texts;
  final List<SketchArrow> arrows;
  bool get isEmpty => lines.isEmpty && texts.isEmpty && arrows.isEmpty;
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
  final arrows = <int>{
    for (var i = 0; i < doc.arrows.length; i++)
      if (pointInPolygon(
        Offset(
          (doc.arrows[i].x1 + doc.arrows[i].x2) / 2,
          (doc.arrows[i].y1 + doc.arrows[i].y2) / 2,
        ),
        polygon,
      ))
        i,
  };
  return SketchSelection(lines: picked, texts: texts, arrows: arrows);
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
  for (var i = 0; i < doc.arrows.length; i++) {
    final a = doc.arrows[i];
    if (_distanceToSegment(
          grid,
          Offset(a.x1.toDouble(), a.y1.toDouble()),
          Offset(a.x2.toDouble(), a.y2.toDouble()),
        ) <=
        tolerance) {
      return SketchSelection(arrows: {i});
    }
  }
  for (var i = 0; i < doc.arrows.length; i++) {
    final a = doc.arrows[i];
    if (_distanceToSegment(
          grid,
          Offset(a.x1.toDouble(), a.y1.toDouble()),
          Offset(a.x2.toDouble(), a.y2.toDouble()),
        ) <=
        tolerance) {
      return SketchSelection(arrows: {i});
    }
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
  for (final i in sel.arrows) {
    if (i < 0 || i >= doc.arrows.length) continue;
    final a = doc.arrows[i];
    add(a.x1, a.y1, a.x2, a.y2);
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
  for (final i in sel.arrows) {
    final a = doc.arrows[i];
    if (a.x1 + dx < 0 ||
        a.x2 + dx < 0 ||
        a.x1 + dx > cols ||
        a.x2 + dx > cols ||
        a.y1 + dy < 0 ||
        a.y2 + dy < 0 ||
        a.y1 + dy > rows ||
        a.y2 + dy > rows) {
      return false;
    }
  }
  final before = sel.lines.isEmpty ? null : selectionBounds(doc, sel);
  if (before != null) {
    scaleFills(doc, before, before.shift(Offset(dx.toDouble(), dy.toDouble())));
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
  for (final i in sel.arrows) {
    final a = doc.arrows[i];
    doc.arrows[i] = a.copyWith(
      x1: a.x1 + dx,
      y1: a.y1 + dy,
      x2: a.x2 + dx,
      y2: a.y2 + dy,
    );
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
  [
    for (final i in sel.arrows.toList()..sort())
      if (i < doc.arrows.length) doc.arrows[i],
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
  doc.arrows = [
    for (var i = 0; i < doc.arrows.length; i++)
      if (!sel.arrows.contains(i)) doc.arrows[i],
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
  for (final a in clip.arrows) {
    minX = math.min(minX, math.min(a.x1, a.x2));
    minY = math.min(minY, math.min(a.y1, a.y2));
    maxX = math.max(maxX, math.max(a.x1, a.x2));
    maxY = math.max(maxY, math.max(a.y1, a.y2));
  }
  final cols = doc.grid.cols, rows = doc.grid.rows;
  if (maxX - minX > cols || maxY - minY > rows) return null;
  dx = dx.clamp(-minX, cols - maxX);
  dy = dy.clamp(-minY, rows - maxY);
  final sel = SketchSelection();
  // 붙인 묶음은 원래 묶음과 따로 움직이도록 새 묶음 id를 받는다(묶음 구조는 그대로).
  final fresh = groupIdMaker(doc);
  final remap = <String, String>{};
  String? regroup(String? old) =>
      old == null ? null : remap.putIfAbsent(old, fresh);
  for (final a in clip.arrows) {
    final moved = a.copyWith(
      x1: a.x1 + dx,
      y1: a.y1 + dy,
      x2: a.x2 + dx,
      y2: a.y2 + dy,
      group: regroup(a.group),
    );
    sel.arrows.add(doc.arrows.length);
    doc.arrows.add(moved);
  }
  for (final s in clip.lines) {
    final moved = s.copyWith(
      x1: s.x1 + dx,
      y1: s.y1 + dy,
      x2: s.x2 + dx,
      y2: s.y2 + dy,
      group: regroup(s.group),
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
    final moved = s.copyWith(x: s.x + dx, y: s.y + dy, group: regroup(s.group));
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
  final cells = regionCells(doc, x, y);
  if (cells == null) return null;
  var minX = x, maxX = x, minY = y, maxY = y;
  for (final (cx, cy) in cells) {
    minX = math.min(minX, cx);
    maxX = math.max(maxX, cx);
    minY = math.min(minY, cy);
    maxY = math.max(maxY, cy);
  }
  return Rect.fromLTRB(
    minX.toDouble(),
    minY.toDouble(),
    maxX + 1.0,
    maxY + 1.0,
  );
}

/// 격자 칸 (x, y)가 든 '칸'(선으로 닫힌 영역)의 격자 칸 모음. 사각형 안을 선으로 나누면
/// 나뉜 영역마다 따로 나온다. 경계가 닫히지 않아 종이 끝까지 열려 있으면 null(칸이 아니다).
Set<(int, int)>? regionCells(TableSketchDoc doc, int x, int y) {
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
  while (queue.isNotEmpty) {
    final (cx, cy) = queue.removeLast();
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
  return seen;
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
  String color = sketchBlack,
}) {
  final l = r.left.round(),
      t = r.top.round(),
      ri = r.right.round(),
      b = r.bottom.round();
  SketchLine line(int x1, int y1, int x2, int y2) => SketchLine(
    x1: x1,
    y1: y1,
    x2: x2,
    y2: y2,
    width: width,
    style: style,
    color: color,
  );
  return [
    line(l, t, ri, t),
    line(l, b, ri, b),
    line(l, t, l, b),
    line(ri, t, ri, b),
  ];
}

/// 범위가 [from]과 같은 배경색을 [to]로 옮긴다(사각형을 옮기거나 크기를 바꿀 때 배경도 따라간다).
void moveFill(TableSketchDoc doc, Rect? from, Rect to) {
  if (from == null) return;
  doc.fills = [
    for (final f in doc.fills)
      if (f.x1 == from.left.round() &&
          f.y1 == from.top.round() &&
          f.x2 == from.right.round() &&
          f.y2 == from.bottom.round())
        SketchFill(
          x1: to.left.round(),
          y1: to.top.round(),
          x2: to.right.round(),
          y2: to.bottom.round(),
          color: f.color,
        )
      else
        f,
  ];
}

/// 고른 사각형을 새 테두리로 바꾸고, 새 네 변을 고른 상태로 돌려준다.
SketchSelection resizeRectangle(
  TableSketchDoc doc,
  SketchSelection sel,
  Rect bounds,
) {
  if (sel.lines.isEmpty && sel.arrows.length == 1) {
    final i = sel.arrows.first;
    final arrow = doc.arrows[i];
    final oldBounds = selectionBounds(doc, sel)!;
    final sx = oldBounds.width == 0 ? 1.0 : bounds.width / oldBounds.width;
    final sy = oldBounds.height == 0 ? 1.0 : bounds.height / oldBounds.height;
    int mapX(int x) => (bounds.left + (x - oldBounds.left) * sx)
        .round().clamp(0, doc.grid.cols);
    int mapY(int y) => (bounds.top + (y - oldBounds.top) * sy)
        .round().clamp(0, doc.grid.rows);
    doc.arrows[i] = arrow.copyWith(
      x1: mapX(arrow.x1), y1: mapY(arrow.y1),
      x2: mapX(arrow.x2), y2: mapY(arrow.y2),
    );
    return sel;
  }
  if (sel.lines.isEmpty) return sel;
  final sample = doc.lines[sel.lines.first];
  final from = selectionBounds(doc, sel);
  if (from != null) scaleFills(doc, from, bounds);
  for (final i in sel.lines.toList()..sort((a, b) => b.compareTo(a))) {
    doc.lines.removeAt(i);
  }
  final start = doc.lines.length;
  doc.lines.addAll([
    for (final l in rectangleLines(
      bounds,
      width: sample.width,
      style: sample.style,
      color: sample.color,
    ))
      SketchLine(
        x1: l.x1,
        y1: l.y1,
        x2: l.x2,
        y2: l.y2,
        width: l.width,
        style: l.style,
        color: l.color,
        layer: sample.layer,
        group: sample.group,
      ),
  ]);
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

// --- 묶음(그룹) ---

int _groupSerial = 0;

/// 새 묶음 id를 만드는 함수(문서에 이미 있는 id와 겹치지 않는다).
String Function() groupIdMaker(TableSketchDoc doc) {
  final taken = <String>{
    for (final l in doc.lines) ?l.group,
    for (final t in doc.texts) ?t.group,
    for (final a in doc.arrows) ?a.group,
  };
  return () {
    String id;
    do {
      id = 'g${DateTime.now().microsecondsSinceEpoch}-${++_groupSerial}';
    } while (!taken.add(id));
    return id;
  };
}

/// 고른 개체 가운데 묶음에 든 것이 있으면 그 묶음의 다른 개체도 함께 고른다.
SketchSelection expandGroups(TableSketchDoc doc, SketchSelection sel) {
  final groups = selectedGroups(doc, sel);
  if (groups.isEmpty) return sel;
  return SketchSelection(
    lines: {
      ...sel.lines,
      for (var i = 0; i < doc.lines.length; i++)
        if (groups.contains(doc.lines[i].group)) i,
    },
    texts: {
      ...sel.texts,
      for (var i = 0; i < doc.texts.length; i++)
        if (groups.contains(doc.texts[i].group)) i,
    },
    arrows: {
      ...sel.arrows,
      for (var i = 0; i < doc.arrows.length; i++)
        if (groups.contains(doc.arrows[i].group)) i,
    },
  );
}

/// 고른 개체에 걸린 묶음 id들.
Set<String> selectedGroups(TableSketchDoc doc, SketchSelection sel) => {
  for (final i in sel.lines)
    if (i >= 0 && i < doc.lines.length) ?doc.lines[i].group,
  for (final i in sel.texts)
    if (i >= 0 && i < doc.texts.length) ?doc.texts[i].group,
  for (final i in sel.arrows)
    if (i >= 0 && i < doc.arrows.length) ?doc.arrows[i].group,
};

/// 고른 개체(2개 이상)를 새 묶음 하나로 묶는다. 안에 있던 묶음은 새 묶음에 합쳐진다.
bool groupSelection(TableSketchDoc doc, SketchSelection sel) {
  final valid = sel.validFor(doc);
  if (valid.count < 2) return false;
  final id = groupIdMaker(doc)();
  for (final i in valid.lines) {
    doc.lines[i] = doc.lines[i].copyWith(group: id);
  }
  for (final i in valid.texts) {
    doc.texts[i] = doc.texts[i].copyWith(group: id);
  }
  for (final i in valid.arrows) {
    doc.arrows[i] = doc.arrows[i].copyWith(group: id);
  }
  return true;
}

/// 고른 개체의 묶음을 푼다. 푼 것이 있으면 true.
bool ungroupSelection(TableSketchDoc doc, SketchSelection sel) {
  final valid = sel.validFor(doc);
  var changed = false;
  for (final i in valid.lines) {
    if (doc.lines[i].group == null) continue;
    doc.lines[i] = doc.lines[i].copyWith(clearGroup: true);
    changed = true;
  }
  for (final i in valid.texts) {
    if (doc.texts[i].group == null) continue;
    doc.texts[i] = doc.texts[i].copyWith(clearGroup: true);
    changed = true;
  }
  for (final i in valid.arrows) {
    if (doc.arrows[i].group == null) continue;
    doc.arrows[i] = doc.arrows[i].copyWith(clearGroup: true);
    changed = true;
  }
  return changed;
}

// --- 크기 바꾸기(여러 개·묶음) ---

/// [from] 안에 든 배경색을 [to]로 옮기거나 늘린다(사각형·묶음을 옮기거나 크기를 바꿀 때 배경이 따라간다).
/// 범위가 [from]과 꼭 같은 채움 하나는 [to] 하나로, 그 밖에는 칸마다 대응하는 원래 칸 색을 가져온다.
void scaleFills(TableSketchDoc doc, Rect from, Rect to) {
  if (from == to || from.width < 1 || from.height < 1) return;
  final l = from.left.round(),
      t = from.top.round(),
      r = from.right.round(),
      b = from.bottom.round();
  bool inside(SketchFill f) =>
      f.x1 >= l && f.x2 <= r && f.y1 >= t && f.y2 <= b;
  final moving = doc.fills.where(inside).toList();
  if (moving.isEmpty) return;
  final others = doc.fills.where((f) => !inside(f)).toList();
  final dx = (to.left - from.left).round(), dy = (to.top - from.top).round();
  final cols = doc.grid.cols, rows = doc.grid.rows;
  final moved = <SketchFill>[];
  if ((to.width - from.width).abs() < 1e-9 &&
      (to.height - from.height).abs() < 1e-9) {
    for (final f in moving) {
      moved.add(
        SketchFill(
          x1: f.x1 + dx,
          y1: f.y1 + dy,
          x2: f.x2 + dx,
          y2: f.y2 + dy,
          color: f.color,
        ),
      );
    }
  } else if (moving.length == 1 &&
      moving.single.x1 == l &&
      moving.single.y1 == t &&
      moving.single.x2 == r &&
      moving.single.y2 == b) {
    moved.add(
      SketchFill(
        x1: to.left.round(),
        y1: to.top.round(),
        x2: to.right.round(),
        y2: to.bottom.round(),
        color: moving.single.color,
      ),
    );
  } else {
    final sx = from.width / math.max(to.width, 1e-9);
    final sy = from.height / math.max(to.height, 1e-9);
    String? colorAt(int x, int y) {
      for (final f in moving.reversed) {
        if (f.x1 <= x && x < f.x2 && f.y1 <= y && y < f.y2) return f.color;
      }
      return null;
    }

    for (var y = to.top.round(); y < to.bottom.round(); y++) {
      for (var x = to.left.round(); x < to.right.round(); x++) {
        final ox = (from.left + (x + .5 - to.left) * sx).floor();
        final oy = (from.top + (y + .5 - to.top) * sy).floor();
        final color = colorAt(ox, oy);
        if (color != null) {
          moved.add(
            SketchFill(x1: x, y1: y, x2: x + 1, y2: y + 1, color: color),
          );
        }
      }
    }
  }
  doc.fills = [
    ...others,
    for (final f in moved)
      if (f.x1 >= 0 &&
          f.y1 >= 0 &&
          f.x2 <= cols &&
          f.y2 <= rows &&
          f.x1 < f.x2 &&
          f.y1 < f.y2)
        f,
  ];
}

/// 가로·세로·45° 선 모양을 지키며 새 끝점을 고친다(크기를 바꾸면 대각선이 45°에서 벗어날 수 있다).
(int, int, int, int) _keepShape(
  (int, int, int, int) original,
  (int, int, int, int) mapped,
  int cols,
  int rows,
) {
  final (ox1, oy1, ox2, oy2) = original;
  var (x1, y1, x2, y2) = mapped;
  if (oy1 == oy2) {
    y2 = y1;
  } else if (ox1 == ox2) {
    x2 = x1;
  } else {
    final sign = ((oy2 - oy1) * (ox2 - ox1)).sign;
    y2 = (y1 + sign * (x2 - x1)).clamp(0, rows);
    x2 = x1 + sign * (y2 - y1);
  }
  if (x1 == x2 && y1 == y2) {
    // 너무 줄어 점이 되면 원래 방향으로 한 칸은 남긴다.
    x2 = (x1 + (ox2 - ox1).sign).clamp(0, cols);
    y2 = (y1 + (oy2 - oy1).sign).clamp(0, rows);
  }
  return (x1, y1, x2, y2);
}

/// 고른 개체(여러 개·묶음)를 [from] 테두리에서 [to] 테두리로 늘이거나 줄인다. 선 모양(가로·세로·45°)과
/// 칸 글 위치·배경색이 함께 따라간다. 번호는 그대로이므로 선택도 그대로다.
void scaleSelection(
  TableSketchDoc doc,
  SketchSelection sel,
  Rect from,
  Rect to,
) {
  final cols = doc.grid.cols, rows = doc.grid.rows;
  final sx = from.width == 0 ? 1.0 : to.width / from.width;
  final sy = from.height == 0 ? 1.0 : to.height / from.height;
  int mx(num x) => (to.left + (x - from.left) * sx).round().clamp(0, cols);
  int my(num y) => (to.top + (y - from.top) * sy).round().clamp(0, rows);
  final valid = sel.validFor(doc);
  for (final i in valid.lines) {
    final s = doc.lines[i];
    final (x1, y1, x2, y2) = _keepShape(
      (s.x1, s.y1, s.x2, s.y2),
      (mx(s.x1), my(s.y1), mx(s.x2), my(s.y2)),
      cols,
      rows,
    );
    doc.lines[i] = s.copyWith(x1: x1, y1: y1, x2: x2, y2: y2);
  }
  for (final i in valid.arrows) {
    final a = doc.arrows[i];
    final (x1, y1, x2, y2) = _keepShape(
      (a.x1, a.y1, a.x2, a.y2),
      (mx(a.x1), my(a.y1), mx(a.x2), my(a.y2)),
      cols,
      rows,
    );
    doc.arrows[i] = a.copyWith(x1: x1, y1: y1, x2: x2, y2: y2);
  }
  final occupied = {
    for (var i = 0; i < doc.texts.length; i++)
      if (!valid.texts.contains(i)) (doc.texts[i].x, doc.texts[i].y),
  };
  for (final i in valid.texts) {
    final t = doc.texts[i];
    final x = (to.left + (t.x + .5 - from.left) * sx).floor().clamp(
      0,
      cols - 1,
    );
    final y = (to.top + (t.y + .5 - from.top) * sy).floor().clamp(0, rows - 1);
    if (occupied.contains((x, y))) continue;
    occupied.add((x, y));
    doc.texts[i] = t.copyWith(x: x, y: y);
  }
  scaleFills(doc, from, to);
}

/// 손잡이(0~7, TableSketchPainter.handlePoints 순서)를 (gx, gy)로 끌 때의 새 테두리.
/// [keepRatio]면 처음 가로세로 비율을 지킨다(Shift 또는 '비율 유지').
Rect resizeBounds(
  Rect start,
  int handle,
  double gx,
  double gy, {
  bool keepRatio = false,
}) {
  var l = start.left, t = start.top, r = start.right, b = start.bottom;
  final minW = start.width == 0 ? 0.0 : 1.0;
  final minH = start.height == 0 ? 0.0 : 1.0;
  final movesX = handle != 1 && handle != 5;
  final movesY = handle != 3 && handle != 7;
  if (const {0, 6, 7}.contains(handle)) l = math.min(gx, r - minW);
  if (const {2, 3, 4}.contains(handle)) r = math.max(gx, l + minW);
  if (const {0, 1, 2}.contains(handle)) t = math.min(gy, b - minH);
  if (const {4, 5, 6}.contains(handle)) b = math.max(gy, t + minH);
  if (keepRatio && start.width > 0 && start.height > 0) {
    final ratio = start.width / start.height;
    var w = r - l, h = b - t;
    if (movesX && movesY) {
      // 모서리: 더 많이 끈 쪽에 맞춘다.
      if (w / start.width >= h / start.height) {
        h = (w / ratio).roundToDouble();
      } else {
        w = (h * ratio).roundToDouble();
      }
    } else if (movesX) {
      h = (w / ratio).roundToDouble();
    } else {
      w = (h * ratio).roundToDouble();
    }
    w = math.max(w, 1);
    h = math.max(h, 1);
    // 변 가운데 손잡이는 맞은편이 아니라 왼쪽·위를 고정하고 늘린다(종이 위·왼쪽 밖으로 나가지 않게).
    if (const {0, 6, 7}.contains(handle)) {
      l = r - w;
    } else {
      r = l + w;
    }
    if (const {0, 1, 2}.contains(handle)) {
      t = b - h;
    } else {
      b = t + h;
    }
  }
  return Rect.fromLTRB(l, t, r, b);
}

// --- 스마트 가이드(빨간 점선)와 자석 맞춤 ---

/// 옮기는 동안 비교할 다른 개체들: 맞춤 기준 x·y와 개체별 테두리.
class GuideTargets {
  const GuideTargets(this.xs, this.ys, this.boxes);
  final Set<double> xs;
  final Set<double> ys;
  final List<Rect> boxes;
}

/// 안내선 결과: 맞춘 세로(x)·가로(y) 줄, 같은 간격 표시 구간, 크기가 같은 다른 개체.
class SmartGuides {
  const SmartGuides({
    this.xs = const {},
    this.ys = const {},
    this.spacing = const [],
    this.sameSize = const [],
  });
  final Set<double> xs;
  final Set<double> ys;

  /// 같은 간격(격자 단위 선분): 왼쪽 개체~고른 것, 고른 것~오른쪽 개체 식으로 둘씩.
  final List<(Offset, Offset)> spacing;

  /// 고른 것과 가로 또는 세로 크기가 같은 다른 개체 테두리.
  final List<Rect> sameSize;
  bool get isEmpty =>
      xs.isEmpty && ys.isEmpty && spacing.isEmpty && sameSize.isEmpty;
}

/// 고르지 않은 개체를 모형(사각형 네 변·이어진 직선·화살표·묶음) 단위 테두리로 나눈다.
List<Rect> objectBoxes(TableSketchDoc doc, SketchSelection sel) {
  final boxes = <Rect>[];
  final chosenGroups = selectedGroups(doc, sel);
  final grouped = <String, SketchSelection>{};
  final visited = <int>{...sel.lines};
  for (var i = 0; i < doc.lines.length; i++) {
    final g = doc.lines[i].group;
    if (g == null || sel.lines.contains(i)) continue;
    visited.add(i);
    if (!chosenGroups.contains(g)) {
      grouped.putIfAbsent(g, SketchSelection.new).lines.add(i);
    }
  }
  for (var i = 0; i < doc.arrows.length; i++) {
    final g = doc.arrows[i].group;
    if (sel.arrows.contains(i)) continue;
    if (g != null) {
      if (!chosenGroups.contains(g)) {
        grouped.putIfAbsent(g, SketchSelection.new).arrows.add(i);
      }
      continue;
    }
    final box = selectionBounds(doc, SketchSelection(arrows: {i}));
    if (box != null) boxes.add(box);
  }
  for (final members in grouped.values) {
    final box = selectionBounds(doc, members);
    if (box != null) boxes.add(box);
  }
  final segs = [
    for (var i = 0; i < doc.lines.length; i++)
      if (!visited.contains(i)) ?_AxisSeg.of(doc.lines[i], i),
  ];
  for (var i = 0; i < doc.lines.length; i++) {
    if (visited.contains(i)) continue;
    final seg = _AxisSeg.of(doc.lines[i], i);
    final indices = seg == null
        ? {i}
        : (_rectangleThrough(segs, seg) ?? _chain(segs, seg).indices);
    visited.addAll(indices);
    final box = selectionBounds(doc, SketchSelection(lines: indices));
    if (box != null) boxes.add(box);
  }
  return boxes;
}

/// 맞춤 기준을 한 번(끌기 시작할 때) 모은다: 다른 선 끝·가운데, 다른 개체 테두리의 가장자리·가운데.
GuideTargets guideTargets(TableSketchDoc doc, SketchSelection sel) {
  final boxes = objectBoxes(doc, sel);
  final xs = <double>{}, ys = <double>{};
  for (var i = 0; i < doc.lines.length; i++) {
    if (sel.lines.contains(i)) continue;
    final l = doc.lines[i];
    xs.addAll([l.x1.toDouble(), l.x2.toDouble(), (l.x1 + l.x2) / 2]);
    ys.addAll([l.y1.toDouble(), l.y2.toDouble(), (l.y1 + l.y2) / 2]);
  }
  for (final b in boxes) {
    xs.addAll([b.left, b.center.dx, b.right]);
    ys.addAll([b.top, b.center.dy, b.bottom]);
  }
  return GuideTargets(xs, ys, boxes);
}

bool _overlapY(Rect a, Rect b) => a.top <= b.bottom && b.top <= a.bottom;
bool _overlapX(Rect a, Rect b) => a.left <= b.right && b.left <= a.right;

/// 가로로 왼쪽·오른쪽(세로면 위·아래)에 가장 가까운 다른 개체.
(Rect?, Rect?) _neighbors(Rect b, List<Rect> boxes, bool horizontal) {
  Rect? before, after;
  for (final o in boxes) {
    if (horizontal) {
      if (!_overlapY(o, b)) continue;
      if (o.right <= b.left && (before == null || o.right > before.right)) {
        before = o;
      }
      if (o.left >= b.right && (after == null || o.left < after.left)) {
        after = o;
      }
    } else {
      if (!_overlapX(o, b)) continue;
      if (o.bottom <= b.top && (before == null || o.bottom > before.bottom)) {
        before = o;
      }
      if (o.top >= b.bottom && (after == null || o.top < after.top)) {
        after = o;
      }
    }
  }
  return (before, after);
}

/// 지금 테두리 [b]가 다른 개체와 맞는 곳(가장자리·가운데 정렬, 같은 간격, 같은 크기).
SmartGuides smartGuides(Rect b, GuideTargets t) {
  final spacing = <(Offset, Offset)>[];
  final (left, right) = _neighbors(b, t.boxes, true);
  if (left != null && right != null) {
    final gapL = b.left - left.right, gapR = right.left - b.right;
    if (gapL > 0 && (gapL - gapR).abs() < 1e-9) {
      final y = b.center.dy;
      spacing
        ..add((Offset(left.right, y), Offset(b.left, y)))
        ..add((Offset(b.right, y), Offset(right.left, y)));
    }
  }
  final (above, below) = _neighbors(b, t.boxes, false);
  if (above != null && below != null) {
    final gapT = b.top - above.bottom, gapB = below.top - b.bottom;
    if (gapT > 0 && (gapT - gapB).abs() < 1e-9) {
      final x = b.center.dx;
      spacing
        ..add((Offset(x, above.bottom), Offset(x, b.top)))
        ..add((Offset(x, b.bottom), Offset(x, below.top)));
    }
  }
  return SmartGuides(
    xs: {b.left, b.center.dx, b.right}.intersection(t.xs),
    ys: {b.top, b.center.dy, b.bottom}.intersection(t.ys),
    spacing: spacing,
    sameSize: [
      for (final o in t.boxes)
        if ((b.width >= 1 && (o.width - b.width).abs() < 1e-9) ||
            (b.height >= 1 && (o.height - b.height).abs() < 1e-9))
          o,
    ],
  );
}

/// 옮길 칸 수(dx, dy)를 [threshold]칸 안의 맞춤 위치(정렬·같은 간격)로 당긴다(자석처럼).
(int, int) snapMove(
  Rect start,
  int dx,
  int dy,
  GuideTargets t,
  int threshold,
) {
  if (threshold <= 0) return (dx, dy);
  final moved = start.shift(Offset(dx.toDouble(), dy.toDouble()));
  int? best(List<double> features, Iterable<double> targets) {
    double? found;
    for (final f in features) {
      for (final target in targets) {
        final d = target - f;
        if (d != d.roundToDouble() || d.abs() > threshold) continue;
        if (found == null || d.abs() < found.abs()) found = d;
      }
    }
    return found?.round();
  }

  final (left, right) = _neighbors(moved, t.boxes, true);
  final (above, below) = _neighbors(moved, t.boxes, false);
  final bx = best([moved.left, moved.center.dx, moved.right], t.xs);
  final by = best([moved.top, moved.center.dy, moved.bottom], t.ys);
  final ex = left != null && right != null
      ? best([moved.left], [(left.right + right.left - moved.width) / 2])
      : null;
  final ey = above != null && below != null
      ? best([moved.top], [(above.bottom + below.top - moved.height) / 2])
      : null;
  int pick(int? a, int? b) =>
      a == null ? (b ?? 0) : (b == null || a.abs() <= b.abs() ? a : b);
  return (dx + pick(bx, ex), dy + pick(by, ey));
}

/// 손잡이로 크기를 바꿀 때 움직이는 변을 [threshold]칸 안의 다른 개체 가장자리·같은 크기로 당긴다.
Rect snapResize(Rect next, int handle, GuideTargets t, int threshold) {
  if (threshold <= 0) return next;
  double snap(double v, Iterable<double> targets) {
    var best = v;
    var dist = double.infinity;
    for (final target in targets) {
      final d = (target - v).abs();
      if (d <= threshold && d < dist && target == target.roundToDouble()) {
        dist = d;
        best = target;
      }
    }
    return best;
  }

  var l = next.left, t0 = next.top, r = next.right, b = next.bottom;
  final widths = [for (final o in t.boxes) if (o.width >= 1) o.width];
  final heights = [for (final o in t.boxes) if (o.height >= 1) o.height];
  if (const {0, 6, 7}.contains(handle)) {
    l = snap(l, [...t.xs, for (final w in widths) r - w]);
    if (l >= r) l = next.left;
  }
  if (const {2, 3, 4}.contains(handle)) {
    r = snap(r, [...t.xs, for (final w in widths) l + w]);
    if (r <= l) r = next.right;
  }
  if (const {0, 1, 2}.contains(handle)) {
    t0 = snap(t0, [...t.ys, for (final h in heights) b - h]);
    if (t0 >= b) t0 = next.top;
  }
  if (const {4, 5, 6}.contains(handle)) {
    b = snap(b, [...t.ys, for (final h in heights) t0 + h]);
    if (b <= t0) b = next.bottom;
  }
  return Rect.fromLTRB(l, t0, r, b);
}

// --- 선·화살표 끝점 손잡이 ---

/// 하나만 고른 선(또는 화살표)의 끝점 손잡이를 눌렀는지: (화살표인지, 번호, 끝 0/1).
({bool arrow, int index, int end})? endpointAt(
  TableSketchDoc doc,
  SketchSelection sel,
  Offset grid,
  double tolerance,
) {
  final valid = sel.validFor(doc);
  if (valid.count != 1 || valid.texts.isNotEmpty) return null;
  final isArrow = valid.arrows.isNotEmpty;
  final index = isArrow ? valid.arrows.single : valid.lines.single;
  final (x1, y1, x2, y2) = isArrow
      ? (
          doc.arrows[index].x1,
          doc.arrows[index].y1,
          doc.arrows[index].x2,
          doc.arrows[index].y2,
        )
      : (
          doc.lines[index].x1,
          doc.lines[index].y1,
          doc.lines[index].x2,
          doc.lines[index].y2,
        );
  final d1 = (grid - Offset(x1.toDouble(), y1.toDouble())).distance;
  final d2 = (grid - Offset(x2.toDouble(), y2.toDouble())).distance;
  if (math.min(d1, d2) > tolerance) return null;
  return (arrow: isArrow, index: index, end: d1 <= d2 ? 0 : 1);
}
