import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'table_sketch_models.dart';

/// '#RRGGBB' → 화면 색.
Color sketchColorValue(String hex) =>
    Color(0xFF000000 | int.parse(hex.substring(1), radix: 16));

/// 점 p에서 선분 a-b 사이의 최단거리 계산.
double distanceToSegment(Offset p, Offset a, Offset b) {
  final ab = b - a;
  final ap = p - a;
  final len2 = ab.dx * ab.dx + ab.dy * ab.dy;
  if (len2 == 0) return (p - a).distance;
  final t = ((ap.dx * ab.dx + ap.dy * ab.dy) / len2).clamp(0.0, 1.0);
  final proj = Offset(a.dx + t * ab.dx, a.dy + t * ab.dy);
  return (p - proj).distance;
}

/// 시작점과 끝점을 바탕으로 가장 가까운 격자점 및 가로/세로/45° 대각선으로 스냅된 끝 격자점을 계산.
math.Point<int>? snapLineCoords(
  int gx1,
  int gy1,
  int rawGx2,
  int rawGy2,
  int maxCols,
  int maxRows,
) {
  final dx = rawGx2 - gx1;
  final dy = rawGy2 - gy1;
  if (dx == 0 && dy == 0) return null;

  final adx = dx.abs();
  final ady = dy.abs();

  // tan(22.5°) ≈ 0.41421356
  // ady / adx < 0.4142  => 가로선
  // adx / ady < 0.4142  => 세로선
  // 그 외                => 45° 대각선
  int gx2 = gx1;
  int gy2 = gy1;

  if (adx > 0 && (ady == 0 || (ady / adx) < 0.41421356)) {
    // 가로선 (y1 == y2)
    gx2 = rawGx2.clamp(0, maxCols);
    gy2 = gy1;
  } else if (ady > 0 && (adx == 0 || (adx / ady) < 0.41421356)) {
    // 세로선 (x1 == x2)
    gx2 = gx1;
    gy2 = rawGy2.clamp(0, maxRows);
  } else {
    // 45° 대각선 (|x2-x1| == |y2-y1|)
    final sx = dx >= 0 ? 1 : -1;
    final sy = dy >= 0 ? 1 : -1;
    var step = ((adx + ady) / 2.0).round();
    if (step < 1) step = 1;

    final maxStepX = sx > 0 ? (maxCols - gx1) : gx1;
    final maxStepY = sy > 0 ? (maxRows - gy1) : gy1;
    final maxStep = math.min(maxStepX, maxStepY);
    step = math.min(step, maxStep);

    if (step < 1) return null;
    gx2 = gx1 + step * sx;
    gy2 = gy1 + step * sy;
  }

  if (gx1 == gx2 && gy1 == gy2) return null;
  return math.Point<int>(gx2, gy2);
}

/// 경로를 점선(파선/점선)으로 변환.
Path createDashedPath(Path source, double dashWidth, double dashGap) {
  final dest = Path();
  for (final metric in source.computeMetrics()) {
    var distance = 0.0;
    var draw = true;
    while (distance < metric.length) {
      final length = draw ? dashWidth : dashGap;
      if (draw) {
        dest.addPath(
          metric.extractPath(
            distance,
            math.min(distance + length, metric.length),
          ),
          Offset.zero,
        );
      }
      distance += length;
      draw = !draw;
    }
  }
  return dest;
}

/// 표그림판 캔버스 페인터.
class TableSketchPainter extends CustomPainter {
  TableSketchPainter({
    required this.doc,
    required this.cellSize,
    this.selectedLines = const {},
    this.selectedTexts = const {},
    this.selectedArrows = const {},
    this.lassoPath,
    this.marquee = false,
    this.cellImages = const [],
    this.imageTarget,
    this.previewLine,
    this.previewArrow = false,
    this.previewRect,
    this.resizeBox,
    this.guideXs = const {},
    this.guideYs = const {},
    this.guideSpacing = const [],
    this.guideSameSize = const [],
    this.selectedBounds,
    this.regionCells = const {},
  });

  /// 같은 간격 표시 선분(격자 단위).
  final List<(Offset, Offset)> guideSpacing;

  /// 고른 것과 크기가 같은 다른 개체 테두리(격자 단위)와 고른 것의 테두리.
  final List<Rect> guideSameSize;
  final Rect? selectedBounds;

  /// '칸 색' 도구로 고른 칸의 격자 칸들.
  final Set<(int, int)> regionCells;

  final TableSketchDoc doc;
  final double cellSize;
  final Set<int> selectedLines;
  final Set<int> selectedTexts;
  final Set<int> selectedArrows;

  /// 올가미(자유 곡선) 또는 선택 상자([시작, 현재]) 경로, 화면 좌표.
  final List<Offset>? lassoPath;
  final bool marquee;

  /// 칸 배경 그림: (칸 사각형(격자 단위), 그림). 칸 크기에 맞춰 늘려 채운다.
  final List<(Rect, ui.Image)> cellImages;

  /// '칸 그림' 도구로 고른 칸(격자 단위).
  final Rect? imageTarget;
  final SketchLine? previewLine;
  final bool previewArrow;
  final Rect? previewRect;

  /// 고른 사각형 모형(격자 단위): 크기 조절 손잡이 8개를 그린다.
  final Rect? resizeBox;

  /// 옮기거나 크기를 바꾸는 동안의 맞춤 안내선(격자 단위, 빨간 점선).
  final Set<double> guideXs;
  final Set<double> guideYs;

  /// 손잡이 순서: 왼위·위·오위·오른·오아래·아래·왼아래·왼(격자 단위 좌표).
  static List<Offset> handlePoints(Rect r) => [
    r.topLeft,
    r.topCenter,
    r.topRight,
    r.centerRight,
    r.bottomRight,
    r.bottomCenter,
    r.bottomLeft,
    r.centerLeft,
  ];

  @override
  void paint(Canvas canvas, Size size) {
    // 1. 종이 바탕색 (흰색)
    final bgPaint = Paint()..color = Colors.white;
    canvas.drawRect(Offset.zero & size, bgPaint);

    // 2. 바둑판 점선 격자 (연회색 점선)
    _drawGrid(canvas, size);

    // 2-0. 사각형 배경색(그림·선 아래)
    for (final fill in doc.fills) {
      canvas.drawRect(
        Rect.fromLTRB(
          fill.x1 * cellSize,
          fill.y1 * cellSize,
          fill.x2 * cellSize,
          fill.y2 * cellSize,
        ),
        Paint()..color = sketchColorValue(fill.color),
      );
    }

    // 2-1. 칸 배경 그림(선 아래)
    for (final (region, image) in cellImages) {
      final dst = Rect.fromLTRB(
        region.left * cellSize,
        region.top * cellSize,
        region.right * cellSize,
        region.bottom * cellSize,
      );
      canvas.drawImageRect(
        image,
        Rect.fromLTWH(0, 0, image.width.toDouble(), image.height.toDouble()),
        dst,
        Paint()..filterQuality = FilterQuality.medium,
      );
    }
    // '칸 색'으로 고른 칸(선 아래, 연한 초록).
    if (regionCells.isNotEmpty) {
      final mark = Paint()..color = const Color(0x3316A34A);
      for (final (x, y) in regionCells) {
        canvas.drawRect(
          Rect.fromLTWH(x * cellSize, y * cellSize, cellSize, cellSize),
          mark,
        );
      }
    }
    final target = imageTarget;
    if (target != null) {
      final r = Rect.fromLTRB(
        target.left * cellSize,
        target.top * cellSize,
        target.right * cellSize,
        target.bottom * cellSize,
      );
      canvas.drawRect(r, Paint()..color = const Color(0x2216A34A));
      canvas.drawRect(
        r.deflate(1),
        Paint()
          ..color = const Color(0xFF16A34A)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2,
      );
    }

    // 3. 잠근 레이어의 선·글(고를 수 없지만 보인다)과 기존에 그려진 선들
    for (final line in doc.lockedLines) {
      _drawSketchLine(canvas, line);
    }
    for (final text in doc.lockedTexts) {
      _drawSketchText(canvas, text);
    }
    for (int i = 0; i < doc.lines.length; i++) {
      final line = doc.lines[i];
      _drawSketchLine(
        canvas,
        line,
        isSelected: selectedLines.contains(i),
        showHandles: selectedLines.length == 1,
      );
    }

    // 화살표는 선과 별도 객체로 보관하되 같은 선 스타일로 그린다.
    final visibleArrows = [...doc.lockedArrows, ...doc.arrows];
    for (var arrowIndex = 0; arrowIndex < visibleArrows.length; arrowIndex++) {
      final arrow = visibleArrows[arrowIndex];
      _drawArrow(
        canvas,
        Offset(arrow.x1 * cellSize, arrow.y1 * cellSize),
        Offset(arrow.x2 * cellSize, arrow.y2 * cellSize),
        arrow.color,
        arrow.width,
        selectedArrows.contains(arrowIndex - doc.lockedArrows.length),
      );
    }

    // 4. 드래그 중인 미리보기 선 / 사각형
    if (previewLine != null) {
      if (previewArrow) {
        drawArrowPreview(canvas, previewLine!);
      } else {
        _drawSketchLine(canvas, previewLine!, isPreview: true);
      }
    }
    if (previewRect != null) {
      _drawPreviewRect(canvas, previewRect!);
    }

    // 5. 텍스트 렌더링(고른 칸은 파란 바탕)
    for (var i = 0; i < doc.texts.length; i++) {
      if (selectedTexts.contains(i)) {
        final t = doc.texts[i];
        canvas.drawRect(
          Rect.fromLTWH(t.x * cellSize, t.y * cellSize, cellSize, cellSize),
          Paint()..color = const Color(0x553B82F6),
        );
      }
      _drawSketchText(canvas, doc.texts[i]);
    }

    // 6. 여러 개를 고르면 감싸는 점선 상자
    if (selectedLines.length + selectedTexts.length + selectedArrows.length >
        1) {
      final bounds = _selectionRect();
      if (bounds != null) {
        canvas.drawPath(
          createDashedPath(Path()..addRect(bounds.inflate(4)), 5.0, 3.0),
          Paint()
            ..color = const Color(0xFF2563EB)
            ..style = PaintingStyle.stroke
            ..strokeWidth = 1.2,
        );
      }
    }

    // 6-1. 맞춤 안내선(다이어그램처럼 빨간 점선)
    final guide = Paint()
      ..color = const Color(0xFFDC2626)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0;
    for (final x in guideXs) {
      final path = Path()
        ..moveTo(x * cellSize, 0)
        ..lineTo(x * cellSize, size.height);
      canvas.drawPath(createDashedPath(path, 6.0, 4.0), guide);
    }
    for (final y in guideYs) {
      final path = Path()
        ..moveTo(0, y * cellSize)
        ..lineTo(size.width, y * cellSize);
      canvas.drawPath(createDashedPath(path, 6.0, 4.0), guide);
    }
    // 같은 간격: 사이 구간을 빨간 점선과 양끝 짧은 막대로.
    for (final (a, b) in guideSpacing) {
      final p = a * cellSize, q = b * cellSize;
      canvas.drawPath(
        createDashedPath(Path()..moveTo(p.dx, p.dy)..lineTo(q.dx, q.dy), 4.0, 3.0),
        guide,
      );
      final d = q - p;
      if (d.distance == 0) continue;
      final n = Offset(-d.dy, d.dx) / d.distance * 5;
      canvas.drawLine(p - n, p + n, guide);
      canvas.drawLine(q - n, q + n, guide);
    }
    // 같은 크기: 고른 것과 같은 크기의 개체 아래(오른쪽)에 빨간 점선 치수 표시.
    final selected = selectedBounds;
    for (final r in [...guideSameSize, ?selected]) {
      final rect = Rect.fromLTRB(
        r.left * cellSize,
        r.top * cellSize,
        r.right * cellSize,
        r.bottom * cellSize,
      );
      if (selected != null && (r.width - selected.width).abs() < 1e-9) {
        canvas.drawPath(
          createDashedPath(
            Path()
              ..moveTo(rect.left, rect.bottom + 6)
              ..lineTo(rect.right, rect.bottom + 6),
            4.0,
            3.0,
          ),
          guide,
        );
      }
      if (selected != null && (r.height - selected.height).abs() < 1e-9) {
        canvas.drawPath(
          createDashedPath(
            Path()
              ..moveTo(rect.right + 6, rect.top)
              ..lineTo(rect.right + 6, rect.bottom),
            4.0,
            3.0,
          ),
          guide,
        );
      }
    }

    // 6-2. 사각형 크기 조절 손잡이
    final box = resizeBox;
    if (box != null) {
      final fill = Paint()..color = Colors.white;
      final edge = Paint()
        ..color = const Color(0xFF2563EB)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.5;
      for (final p in handlePoints(box)) {
        final r = Rect.fromCenter(center: p * cellSize, width: 9, height: 9);
        canvas.drawRect(r, fill);
        canvas.drawRect(r, edge);
      }
    }

    // 7. 올가미·선택 상자(끌고 있는 동안)
    final path = lassoPath;
    if (path != null && path.length >= 2) {
      final outline = Path();
      if (marquee) {
        outline.addRect(Rect.fromPoints(path.first, path.last));
      } else {
        outline.moveTo(path.first.dx, path.first.dy);
        for (final p in path.skip(1)) {
          outline.lineTo(p.dx, p.dy);
        }
        outline.close();
      }
      canvas.drawPath(outline, Paint()..color = const Color(0x1A2563EB));
      canvas.drawPath(
        createDashedPath(outline, 5.0, 3.0),
        Paint()
          ..color = const Color(0xFF2563EB)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.2,
      );
    }

    // 6. 종이 테두리 (가장자리 회색 선)
    final borderPaint = Paint()
      ..color = const Color(0xFFCBD5E1)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0;
    canvas.drawRect(Offset.zero & size, borderPaint);
  }

  void _drawGrid(Canvas canvas, Size size) {
    final cols = doc.grid.cols;
    final rows = doc.grid.rows;

    final gridPath = Path();
    // 세로선들
    for (int c = 0; c <= cols; c++) {
      final x = c * cellSize;
      gridPath.moveTo(x, 0);
      gridPath.lineTo(x, rows * cellSize);
    }
    // 가로선들
    for (int r = 0; r <= rows; r++) {
      final y = r * cellSize;
      gridPath.moveTo(0, y);
      gridPath.lineTo(cols * cellSize, y);
    }

    final dashedGrid = createDashedPath(gridPath, 2.0, 3.0);
    final gridPaint = Paint()
      ..color = const Color(0xFFE2E8F0)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0;
    canvas.drawPath(dashedGrid, gridPaint);
  }

  void _drawSketchLine(
    Canvas canvas,
    SketchLine line, {
    bool isSelected = false,
    bool isPreview = false,
    bool showHandles = true,
  }) {
    final p1 = Offset(line.x1 * cellSize, line.y1 * cellSize);
    final p2 = Offset(line.x2 * cellSize, line.y2 * cellSize);

    final baseStrokeWidth = sketchStrokePx(line.width);

    final color = isPreview
        ? const Color(0xFF2563EB).withValues(alpha: 0.8)
        : (isSelected
              ? const Color(0xFF1D4ED8)
              : (line.color == sketchBlack
                    ? const Color(0xFF0F172A)
                    : sketchColorValue(line.color)));

    // 선택된 선 하이라이트 (바깥쪽 푸른 글로우)
    if (isSelected) {
      final glowPaint = Paint()
        ..color = const Color(0x553B82F6)
        ..style = PaintingStyle.stroke
        ..strokeWidth = baseStrokeWidth + 8.0
        ..strokeCap = StrokeCap.round;
      canvas.drawLine(p1, p2, glowPaint);

      // 끝점 핸들(하나만 골랐을 때)
      if (showHandles) {
        final handlePaint = Paint()..color = const Color(0xFF2563EB);
        canvas.drawCircle(p1, 4.0, handlePaint);
        canvas.drawCircle(p2, 4.0, handlePaint);
      }
    }

    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = baseStrokeWidth
      ..strokeCap = StrokeCap.square;

    if (line.width == 'double') {
      // 이중선: 법선 방향으로 ±1.5px 오프셋하여 2개 선 그리기
      final delta = p2 - p1;
      final len = delta.distance;
      if (len > 0) {
        final normal = Offset(-delta.dy / len, delta.dx / len) * 1.5;
        _drawSingleStroke(
          canvas,
          p1 + normal,
          p2 + normal,
          line.style,
          paint,
          isPreview,
        );
        _drawSingleStroke(
          canvas,
          p1 - normal,
          p2 - normal,
          line.style,
          paint,
          isPreview,
        );
      }
    } else {
      _drawSingleStroke(canvas, p1, p2, line.style, paint, isPreview);
    }
  }

  void _drawSingleStroke(
    Canvas canvas,
    Offset p1,
    Offset p2,
    String style,
    Paint paint,
    bool isPreview,
  ) {
    if (style == 'dash' || isPreview) {
      final path = Path()
        ..moveTo(p1.dx, p1.dy)
        ..lineTo(p2.dx, p2.dy);
      final dashed = createDashedPath(path, 6.0, 4.0);
      canvas.drawPath(dashed, paint);
    } else if (style == 'dot') {
      final path = Path()
        ..moveTo(p1.dx, p1.dy)
        ..lineTo(p2.dx, p2.dy);
      final dotted = createDashedPath(path, 2.0, 3.0);
      canvas.drawPath(dotted, paint);
    } else {
      canvas.drawLine(p1, p2, paint);
    }
  }

  void _drawPreviewRect(Canvas canvas, Rect rect) {
    final path = Path()..addRect(rect);
    final dashed = createDashedPath(path, 6.0, 4.0);
    final paint = Paint()
      ..color = const Color(0xFF2563EB).withValues(alpha: 0.8)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.4;
    canvas.drawPath(dashed, paint);
  }

  void _drawArrow(
    Canvas canvas,
    Offset a,
    Offset b,
    String color,
    String width,
    bool selected,
  ) {
    final paint = Paint()
      ..color = selected ? const Color(0xFF1D4ED8) : sketchColorValue(color)
      ..strokeWidth = width == 'double' ? 1.4 : sketchStrokePx(width)
      ..strokeCap = StrokeCap.round;
    canvas.drawLine(a, b, paint);
    if ((b - a).distance == 0) return;
    final u = (b - a) / (b - a).distance,
        n = Offset(-u.dy, u.dx),
        h = math.min(cellSize * .28, 8.0);
    final path = Path()
      ..moveTo(
        b.dx - u.dx * h + n.dx * h * .55,
        b.dy - u.dy * h + n.dy * h * .55,
      )
      ..lineTo(b.dx, b.dy)
      ..lineTo(
        b.dx - u.dx * h - n.dx * h * .55,
        b.dy - u.dy * h - n.dy * h * .55,
      );
    canvas.drawPath(path, paint..style = PaintingStyle.stroke);
    if (selected) {
      canvas.drawCircle(a, 4, Paint()..color = const Color(0xFF2563EB));
      canvas.drawCircle(b, 4, Paint()..color = const Color(0xFF2563EB));
    }
  }

  void drawArrowPreview(Canvas canvas, SketchLine line) {
    final a = Offset(line.x1 * cellSize, line.y1 * cellSize),
        b = Offset(line.x2 * cellSize, line.y2 * cellSize);
    _drawArrow(canvas, a, b, sketchBlack, line.width, false);
  }

  void _drawSketchText(Canvas canvas, SketchText textItem) {
    final cellRect = Rect.fromLTWH(
      textItem.x * cellSize,
      textItem.y * cellSize,
      cellSize,
      cellSize,
    );

    // 텍스트 페인터 설정
    // 그림판 캔버스는 앱 테마 글꼴을 물려받지 않는다. 내장 한글 글꼴을 직접 지정해야 오프라인에서도
    // 모든 한글·○ 같은 기호가 보인다(지정하지 않으면 일부 글자가 □로 보였음, 2.0.5).
    final textStyle = TextStyle(
      fontFamily: 'NotoSansKR',
      color: const Color(0xFF0F172A),
      fontSize: math.max(10.0, cellSize * 0.7),
      fontWeight: textItem.bold ? FontWeight.bold : FontWeight.normal,
    );

    final textSpan = TextSpan(text: textItem.text, style: textStyle);
    final textPainter = TextPainter(
      text: textSpan,
      textAlign: switch (textItem.align) {
        'left' => TextAlign.left,
        'right' => TextAlign.right,
        _ => TextAlign.center,
      },
      textDirection: TextDirection.ltr,
    );
    textPainter.layout();

    // 칸 기준 정렬 위치 계산
    double dx = cellRect.left;
    if (textItem.align == 'center') {
      dx = cellRect.center.dx - (textPainter.width / 2.0);
    } else if (textItem.align == 'right') {
      dx = cellRect.right - textPainter.width - 2.0;
    } else {
      dx = cellRect.left + 2.0;
    }
    final dy = cellRect.center.dy - (textPainter.height / 2.0);

    // 글자 배경에 약간의 반투명 흰색 패딩을 그려 격자선과 겹쳐도 잘 보이도록 처리
    final bgRect = Rect.fromLTWH(
      dx - 2.0,
      dy - 1.0,
      textPainter.width + 4.0,
      textPainter.height + 2.0,
    );
    final bgPaint = Paint()..color = Colors.white.withValues(alpha: 0.85);
    canvas.drawRRect(
      RRect.fromRectAndRadius(bgRect, const Radius.circular(3.0)),
      bgPaint,
    );

    textPainter.paint(canvas, Offset(dx, dy));
  }

  Rect? _selectionRect() {
    Rect? box;
    void add(Rect r) => box = box == null ? r : box!.expandToInclude(r);
    for (final i in selectedLines) {
      if (i < 0 || i >= doc.lines.length) continue;
      final l = doc.lines[i];
      add(
        Rect.fromPoints(
          Offset(l.x1 * cellSize, l.y1 * cellSize),
          Offset(l.x2 * cellSize, l.y2 * cellSize),
        ),
      );
    }
    for (final i in selectedTexts) {
      if (i < 0 || i >= doc.texts.length) continue;
      final t = doc.texts[i];
      add(Rect.fromLTWH(t.x * cellSize, t.y * cellSize, cellSize, cellSize));
    }
    for (final i in selectedArrows) {
      if (i < 0 || i >= doc.arrows.length) continue;
      final a = doc.arrows[i];
      add(
        Rect.fromPoints(
          Offset(a.x1 * cellSize, a.y1 * cellSize),
          Offset(a.x2 * cellSize, a.y2 * cellSize),
        ),
      );
    }
    return box;
  }

  @override
  bool shouldRepaint(covariant TableSketchPainter oldDelegate) {
    return true;
  }
}
