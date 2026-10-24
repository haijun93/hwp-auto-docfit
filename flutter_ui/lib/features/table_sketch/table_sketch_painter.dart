import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'table_sketch_models.dart';

/// 16진수 색상 문자열 파싱 (#RRGGBB 또는 #AARRGGBB).
Color? parseHexColor(String? hex) {
  if (hex == null || hex.isEmpty) return null;
  String clean = hex.replaceAll('#', '').trim();
  if (clean.startsWith('0x') || clean.startsWith('0X')) {
    clean = clean.substring(2);
  }
  if (clean.length == 6) {
    clean = 'FF$clean';
  }
  final val = int.tryParse(clean, radix: 16);
  return val != null ? Color(val) : null;
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
    this.selectedLineIndex,
    Set<int>? selectedLineIndices,
    this.previewLine,
    this.previewRect,
    this.hoveredSegmentLine,
    this.marqueeRect,
    this.verticalGuides,
    this.horizontalGuides,
  }) : selectedLineIndices = {
         if (selectedLineIndices != null) ...selectedLineIndices,
         if (selectedLineIndex != null) selectedLineIndex,
       };

  final TableSketchDoc doc;
  final double cellSize;
  final int? selectedLineIndex;
  final Set<int> selectedLineIndices;
  final SketchLine? previewLine;
  final Rect? previewRect;
  final SketchLine? hoveredSegmentLine;
  final Rect? marqueeRect;
  final List<double>? verticalGuides;
  final List<double>? horizontalGuides;

  @override
  void paint(Canvas canvas, Size size) {
    // 1. 종이 바탕색 (흰색)
    final bgPaint = Paint()..color = Colors.white;
    canvas.drawRect(Offset.zero & size, bgPaint);

    // 2. 셀 배경색 채우기
    _drawCellColors(canvas);

    // 3. 바둑판 점선 격자 (연회색 점선)
    _drawGrid(canvas, size);

    // 4. 스마트 가이드 (빨간 점선)
    _drawSmartGuides(canvas, size);

    // 5. 기존에 그려진 선들
    for (int i = 0; i < doc.lines.length; i++) {
      final line = doc.lines[i];
      final isSelected = selectedLineIndices.contains(i);
      final showHandles = isSelected && selectedLineIndices.length == 1;
      _drawSketchLine(
        canvas,
        line,
        isSelected: isSelected,
        showHandles: showHandles,
      );
    }

    // 6. 드래그 중인 미리보기 선 / 사각형
    if (previewLine != null) {
      _drawSketchLine(canvas, previewLine!, isPreview: true);
    }
    if (previewRect != null) {
      _drawPreviewRect(canvas, previewRect!);
    }

    // 7. 정밀 지우개 호버 세그먼트 강조 (연한 빨간색 두껍게)
    if (hoveredSegmentLine != null) {
      _drawHoveredSegment(canvas, hoveredSegmentLine!);
    }

    // 8. 올가미(마퀴) 선택 사각형
    if (marqueeRect != null) {
      _drawMarquee(canvas, marqueeRect!);
    }

    // 9. 텍스트 렌더링
    for (final textItem in doc.texts) {
      _drawSketchText(canvas, textItem);
    }

    // 10. 종이 테두리 (가장자리 회색 선)
    final borderPaint = Paint()
      ..color = const Color(0xFFCBD5E1)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0;
    canvas.drawRect(Offset.zero & size, borderPaint);
  }

  void _drawCellColors(Canvas canvas) {
    for (final cc in doc.cellColors) {
      final color = parseHexColor(cc.color);
      if (color != null) {
        final r = Rect.fromLTWH(
          cc.x * cellSize,
          cc.y * cellSize,
          cellSize,
          cellSize,
        );
        canvas.drawRect(r, Paint()..color = color);
      }
    }
  }

  void _drawGrid(Canvas canvas, Size size) {
    final cols = doc.grid.cols;
    final rows = doc.grid.rows;

    final gridPath = Path();
    for (int c = 0; c <= cols; c++) {
      final x = c * cellSize;
      gridPath.moveTo(x, 0);
      gridPath.lineTo(x, rows * cellSize);
    }
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

  void _drawSmartGuides(Canvas canvas, Size size) {
    final guidePaint = Paint()
      ..color = const Color(0xFFEF4444)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.2;

    if (verticalGuides != null) {
      for (final x in verticalGuides!) {
        final path = Path()
          ..moveTo(x, 0)
          ..lineTo(x, size.height);
        final dashed = createDashedPath(path, 4.0, 4.0);
        canvas.drawPath(dashed, guidePaint);
      }
    }
    if (horizontalGuides != null) {
      for (final y in horizontalGuides!) {
        final path = Path()
          ..moveTo(0, y)
          ..lineTo(size.width, y);
        final dashed = createDashedPath(path, 4.0, 4.0);
        canvas.drawPath(dashed, guidePaint);
      }
    }
  }

  void _drawHoveredSegment(Canvas canvas, SketchLine seg) {
    final p1 = Offset(seg.x1 * cellSize, seg.y1 * cellSize);
    final p2 = Offset(seg.x2 * cellSize, seg.y2 * cellSize);

    final glow = Paint()
      ..color = const Color(0x66EF4444)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 10.0
      ..strokeCap = StrokeCap.round;
    canvas.drawLine(p1, p2, glow);

    final linePaint = Paint()
      ..color = const Color(0xFFDC2626)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.0
      ..strokeCap = StrokeCap.square;
    canvas.drawLine(p1, p2, linePaint);
  }

  void _drawMarquee(Canvas canvas, Rect rect) {
    final fillPaint = Paint()
      ..color = const Color(0x1F2563EB)
      ..style = PaintingStyle.fill;
    canvas.drawRect(rect, fillPaint);

    final borderPaint = Paint()
      ..color = const Color(0xFF2563EB)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.2;
    final path = Path()..addRect(rect);
    final dashed = createDashedPath(path, 4.0, 4.0);
    canvas.drawPath(dashed, borderPaint);
  }

  void _drawSketchLine(
    Canvas canvas,
    SketchLine line, {
    bool isSelected = false,
    bool isPreview = false,
    bool showHandles = false,
  }) {
    final p1 = Offset(line.x1 * cellSize, line.y1 * cellSize);
    final p2 = Offset(line.x2 * cellSize, line.y2 * cellSize);

    double baseStrokeWidth = switch (line.width) {
      'thick' => 3.0,
      'double' => 1.0,
      _ => 1.4,
    };
    if (line.widthMm != null && line.widthMm! > 0) {
      baseStrokeWidth = math.max(
        0.8,
        line.widthMm! * (cellSize / doc.grid.cellMm),
      );
    }

    Color color;
    if (isPreview) {
      color = const Color(0xFF2563EB).withValues(alpha: 0.8);
    } else if (isSelected) {
      color = const Color(0xFF1D4ED8);
    } else if (line.color != null && line.color!.isNotEmpty) {
      color = parseHexColor(line.color) ?? const Color(0xFF0F172A);
    } else {
      color = const Color(0xFF0F172A);
    }

    // 선택된 선 하이라이트 (바깥쪽 푸른 글로우)
    if (isSelected) {
      final glowPaint = Paint()
        ..color = const Color(0x553B82F6)
        ..style = PaintingStyle.stroke
        ..strokeWidth = baseStrokeWidth + 8.0
        ..strokeCap = StrokeCap.round;
      canvas.drawLine(p1, p2, glowPaint);

      if (showHandles) {
        // 끝점 핸들 (원형 핸들: 흰 바탕에 파란 테두리)
        final handleFill = Paint()..color = Colors.white;
        final handleBorder = Paint()
          ..color = const Color(0xFF2563EB)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2.0;

        canvas.drawCircle(p1, 5.0, handleFill);
        canvas.drawCircle(p1, 5.0, handleBorder);
        canvas.drawCircle(p2, 5.0, handleFill);
        canvas.drawCircle(p2, 5.0, handleBorder);
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
        _drawSingleStroke(canvas, p1 + normal, p2 + normal, line.style, paint, isPreview);
        _drawSingleStroke(canvas, p1 - normal, p2 - normal, line.style, paint, isPreview);
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
      final path = Path()..moveTo(p1.dx, p1.dy)..lineTo(p2.dx, p2.dy);
      final dashed = createDashedPath(path, 6.0, 4.0);
      canvas.drawPath(dashed, paint);
    } else if (style == 'dot') {
      final path = Path()..moveTo(p1.dx, p1.dy)..lineTo(p2.dx, p2.dy);
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

    final textStyle = TextStyle(
      color: const Color(0xFF0F172A),
      fontSize: math.max(10.0, cellSize * 0.7),
      fontWeight: textItem.bold ? FontWeight.bold : FontWeight.normal,
    );

    final textPainter = TextPainter(
      text: TextSpan(text: textItem.text, style: textStyle),
      textAlign: switch (textItem.align) {
        'left' => TextAlign.left,
        'right' => TextAlign.right,
        _ => TextAlign.center,
      },
      textDirection: TextDirection.ltr,
    );
    textPainter.layout();

    double dx = cellRect.left;
    if (textItem.align == 'center') {
      dx = cellRect.center.dx - (textPainter.width / 2.0);
    } else if (textItem.align == 'right') {
      dx = cellRect.right - textPainter.width - 2.0;
    } else {
      dx = cellRect.left + 2.0;
    }
    final dy = cellRect.center.dy - (textPainter.height / 2.0);

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

  @override
  bool shouldRepaint(covariant TableSketchPainter oldDelegate) {
    return true;
  }
}
