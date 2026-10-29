import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'table_sketch_models.dart';

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
    this.lassoPath,
    this.marquee = false,
    this.cellImages = const [],
    this.imageTarget,
    this.previewLine,
    this.previewRect,
  });

  final TableSketchDoc doc;
  final double cellSize;
  final Set<int> selectedLines;
  final Set<int> selectedTexts;

  /// 올가미(자유 곡선) 또는 선택 상자([시작, 현재]) 경로, 화면 좌표.
  final List<Offset>? lassoPath;
  final bool marquee;

  /// 칸 배경 그림: (칸 사각형(격자 단위), 그림). 칸 크기에 맞춰 늘려 채운다.
  final List<(Rect, ui.Image)> cellImages;

  /// '칸 그림' 도구로 고른 칸(격자 단위).
  final Rect? imageTarget;
  final SketchLine? previewLine;
  final Rect? previewRect;

  @override
  void paint(Canvas canvas, Size size) {
    // 1. 종이 바탕색 (흰색)
    final bgPaint = Paint()..color = Colors.white;
    canvas.drawRect(Offset.zero & size, bgPaint);

    // 2. 바둑판 점선 격자 (연회색 점선)
    _drawGrid(canvas, size);

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

    // 3. 기존에 그려진 선들
    for (int i = 0; i < doc.lines.length; i++) {
      final line = doc.lines[i];
      _drawSketchLine(
        canvas,
        line,
        isSelected: selectedLines.contains(i),
        showHandles: selectedLines.length == 1,
      );
    }

    // 4. 드래그 중인 미리보기 선 / 사각형
    if (previewLine != null) {
      _drawSketchLine(canvas, previewLine!, isPreview: true);
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
    if (selectedLines.length + selectedTexts.length > 1) {
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

    final baseStrokeWidth = switch (line.width) {
      'thick' => 3.0,
      'double' => 1.0,
      _ => 1.4,
    };

    final color = isPreview
        ? const Color(0xFF2563EB).withValues(alpha: 0.8)
        : (isSelected ? const Color(0xFF1D4ED8) : const Color(0xFF0F172A));

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

  void _drawSketchText(Canvas canvas, SketchText textItem) {
    final cellRect = Rect.fromLTWH(
      textItem.x * cellSize,
      textItem.y * cellSize,
      cellSize,
      cellSize,
    );

    // 텍스트 페인터 설정
    final textStyle = TextStyle(
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
    return box;
  }

  @override
  bool shouldRepaint(covariant TableSketchPainter oldDelegate) {
    return true;
  }
}
