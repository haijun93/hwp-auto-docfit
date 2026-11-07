import 'dart:math' as math;
import 'dart:ui';

import 'library_api.dart';

/// 자료함 카드 배치 규칙(겹침 방지). 드롭·영역 이동·여러 개 이동·불러오기·창 크기 변경이 모두 이 규칙을 쓴다.
class LibraryLayout {
  const LibraryLayout._();

  static const cardWidth = 140.0;
  static const cardHeight = 72.0;
  static const margin = 16.0;
  static const colStep = 150.0;
  static const rowStep = 80.0;

  /// 카드 사이 최소 간격(이보다 가까우면 겹친 것으로 본다).
  static const gap = 4.0;

  static Rect rectAt(Offset p) => Rect.fromLTWH(p.dx, p.dy, cardWidth, cardHeight);

  static bool _collides(Offset p, Iterable<Rect> occupied) {
    final r = rectAt(p).deflate(-gap / 2);
    return occupied.any((o) => r.overlaps(o.deflate(-gap / 2)));
  }

  /// 폭 [width]에 들어가는 격자 열 수(최소 1).
  static int columnsFor(double? width) {
    if (width == null || !width.isFinite) return 1000;
    return math.max(1, ((width - margin - cardWidth) / colStep).floor() + 1);
  }

  /// 폭 안으로 x를 맞추고 y는 0 이상으로만 맞춘다(세로는 스크롤된다).
  static Offset clampToWidth(Offset p, double? width) {
    final maxX = width == null || !width.isFinite ? double.infinity : math.max(0.0, width - cardWidth);
    return Offset(p.dx.clamp(0.0, maxX).toDouble(), math.max(0.0, p.dy));
  }

  /// [desired]가 비어 있으면 그대로(사용자가 놓은 위치 존중), 겹치면 가장 가까운 빈 격자 칸.
  static Offset freeSlot(Offset desired, Iterable<Rect> occupied, {double? width}) {
    final want = clampToWidth(desired, width);
    final taken = occupied.toList();
    if (!_collides(want, taken)) return want;
    final cols = columnsFor(width);
    Offset? best;
    var bestDistance = double.infinity;
    // 가까운 행부터 넓혀 가며 찾는다. 원하는 행 근처에서 못 찾으면 아래로 계속 내려간다.
    final wantRow = math.max(0, ((want.dy - margin) / rowStep).round());
    for (var radius = 0; radius < 2000; radius++) {
      for (final row in {wantRow - radius, wantRow + radius}) {
        if (row < 0) continue;
        for (var col = 0; col < math.min(cols, 1000); col++) {
          final p = Offset(margin + col * colStep, margin + row * rowStep);
          if (_collides(p, taken)) continue;
          final d = (p - want).distanceSquared;
          if (d < bestDistance) {
            bestDistance = d;
            best = p;
          }
        }
      }
      // 이번 반경에서 찾은 칸보다 다음 반경의 칸이 더 가까울 수 없으면 끝낸다.
      if (best != null && math.pow(radius * rowStep, 2) >= bestDistance) return best;
    }
    if (best != null) return best;
    throw StateError('빈 카드 배치 위치를 찾지 못했습니다.');
  }

  /// 새로 넣을 자료의 위치(왼쪽 위부터 첫 빈 칸).
  static Offset nextSlot(Iterable<Rect> occupied, {double? width}) {
    final taken = occupied.toList();
    final cols = columnsFor(width);
    for (var row = 0; row < 100000; row++) {
      for (var col = 0; col < math.min(cols, 1000); col++) {
        final p = Offset(margin + col * colStep, margin + row * rowStep);
        if (!_collides(p, taken)) return p;
      }
    }
    throw StateError('빈 카드 배치 위치를 찾지 못했습니다.');
  }

  /// 겹친 카드만 빈 자리로 옮긴 위치표(id → 위치). [items] 순서가 앞선 카드가 자리를 지킨다.
  /// [pinned]에 든 카드는 먼저 자리를 차지한다(방금 사용자가 놓은 카드 등).
  static Map<String, Offset> resolve(List<LibraryItem> items, {double? width, Set<String> pinned = const {}}) {
    final ordered = [
      ...items.where((i) => pinned.contains(i.id)),
      ...items.where((i) => !pinned.contains(i.id)),
    ];
    final placed = <Rect>[];
    final result = <String, Offset>{};
    for (final item in ordered) {
      final p = freeSlot(Offset(item.x, item.y), placed, width: width);
      result[item.id] = p;
      placed.add(rectAt(p));
    }
    return result;
  }

  /// 격자로 다시 배치(정리 단추). [items]의 순서대로 왼쪽 위부터 채운다.
  static Map<String, Offset> grid(List<LibraryItem> items, {double? width}) {
    final cols = columnsFor(width);
    return {
      for (var i = 0; i < items.length; i++)
        items[i].id: Offset(margin + (i % cols) * colStep, margin + (i ~/ cols) * rowStep),
    };
  }

  /// 카드들이 서로 겹치는지(시험·불러오기 점검용).
  static bool hasOverlap(Iterable<Offset> positions) {
    final rects = positions.map(rectAt).toList();
    for (var i = 0; i < rects.length; i++) {
      for (var j = i + 1; j < rects.length; j++) {
        if (rects[i].overlaps(rects[j])) return true;
      }
    }
    return false;
  }

  /// 표시 영역에 필요한 높이(세로 스크롤용).
  static double contentHeight(Iterable<Offset> positions) =>
      positions.fold<double>(0, (h, p) => math.max(h, p.dy + cardHeight + margin));
}

/// 정리 단추의 정렬 기준.
enum LibraryArrangeOrder { added, name, kind }

List<LibraryItem> sortForArrange(List<LibraryItem> items, LibraryArrangeOrder order) {
  int addedKey(LibraryItem i) => int.tryParse(i.id.replaceAll(RegExp(r'[^0-9]'), '')) ?? 0;
  final sorted = [...items];
  switch (order) {
    case LibraryArrangeOrder.added:
      sorted.sort((a, b) => addedKey(a).compareTo(addedKey(b)));
    case LibraryArrangeOrder.name:
      sorted.sort((a, b) => a.title.toLowerCase().compareTo(b.title.toLowerCase()));
    case LibraryArrangeOrder.kind:
      sorted.sort((a, b) {
        final k = a.kind.index.compareTo(b.kind.index);
        return k != 0 ? k : a.title.toLowerCase().compareTo(b.title.toLowerCase());
      });
  }
  return sorted;
}
