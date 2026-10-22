import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../../core/api/table_units_api.dart';

Color? parseHexColor(String? hex) {
  if (hex == null) return null;
  var str = hex.trim();
  if (str.startsWith('#')) {
    str = str.substring(1);
  }
  if (str.length == 3) {
    str = '${str[0]}${str[0]}${str[1]}${str[1]}${str[2]}${str[2]}';
  }
  if (str.length == 6) {
    final val = int.tryParse(str, radix: 16);
    if (val != null) return Color(0xff000000 | val);
  } else if (str.length == 8) {
    final val = int.tryParse(str, radix: 16);
    if (val != null) return Color(val);
  }
  return null;
}

/// 병합(rowSpan/colSpan)과 서식을 반영해 한/글 표 구조를 그리는 미리보기 위젯.
class TableGridPreview extends StatelessWidget {
  const TableGridPreview({
    super.key,
    required this.rows,
    required this.cols,
    required this.cellMeta,
    this.maxHeight,
    this.maxWidth,
  });

  final int rows;
  final int cols;
  final List<List<CellMeta>> cellMeta;
  final double? maxHeight;
  final double? maxWidth;

  @override
  Widget build(BuildContext context) {
    if (rows <= 0 || cols <= 0 || cellMeta.isEmpty) {
      return Container(
        height: maxHeight ?? 160,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: const Color(0xfff8fafc),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: const Color(0xffe2e8f0)),
        ),
        child: const Text(
          '표 데이터가 없습니다.',
          style: TextStyle(color: Color(0xff8b95a1), fontSize: 13),
        ),
      );
    }

    // 모든 셀 수집
    final cells = <CellMeta>[];
    for (final rowList in cellMeta) {
      cells.addAll(rowList);
    }

    // 각 열 너비 계산 (colSpan == 1인 셀 우선)
    final colWidths = List<double>.filled(cols, 1.0);
    final colHasExact = List<bool>.filled(cols, false);
    for (final cell in cells) {
      if (cell.colSpan == 1 && cell.col >= 0 && cell.col < cols) {
        if (!colHasExact[cell.col] || cell.width > colWidths[cell.col]) {
          colWidths[cell.col] = cell.width > 0 ? cell.width : 1.0;
          colHasExact[cell.col] = true;
        }
      }
    }
    final totalWidth = colWidths.fold<double>(0.0, (a, b) => a + b);

    // 각 행 높이 계산 (rowSpan == 1인 셀 우선)
    final rowHeights = List<double>.filled(rows, 1.0);
    final rowHasExact = List<bool>.filled(rows, false);
    for (final cell in cells) {
      if (cell.rowSpan == 1 && cell.row >= 0 && cell.row < rows) {
        if (!rowHasExact[cell.row] || cell.height > rowHeights[cell.row]) {
          rowHeights[cell.row] = cell.height > 0 ? cell.height : 1.0;
          rowHasExact[cell.row] = true;
        }
      }
    }
    final totalHeight = rowHeights.fold<double>(0.0, (a, b) => a + b);

    final ratio = (totalWidth > 0 && totalHeight > 0)
        ? (totalWidth / totalHeight).clamp(0.2, 5.0)
        : 1.5;

    return LayoutBuilder(
      builder: (context, constraints) {
        final availWidth = maxWidth != null
            ? math.min(maxWidth!, constraints.maxWidth)
            : (constraints.maxWidth.isFinite ? constraints.maxWidth : 400.0);

        double renderWidth = availWidth;
        double renderHeight = renderWidth / ratio;

        if (maxHeight != null && renderHeight > maxHeight!) {
          renderHeight = maxHeight!;
          renderWidth = renderHeight * ratio;
        }

        return Center(
          child: Container(
            width: renderWidth,
            height: renderHeight,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(4),
              boxShadow: [
                BoxShadow(
                  color: const Color(0x0d000000),
                  blurRadius: 4,
                  offset: const Offset(0, 1),
                ),
              ],
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: CustomPaint(
                size: Size(renderWidth, renderHeight),
                painter: _TableGridPainter(
                  rows: rows,
                  cols: cols,
                  cells: cells,
                  colWidths: colWidths,
                  rowHeights: rowHeights,
                  totalWidth: totalWidth,
                  totalHeight: totalHeight,
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}

class _TableGridPainter extends CustomPainter {
  const _TableGridPainter({
    required this.rows,
    required this.cols,
    required this.cells,
    required this.colWidths,
    required this.rowHeights,
    required this.totalWidth,
    required this.totalHeight,
  });

  final int rows;
  final int cols;
  final List<CellMeta> cells;
  final List<double> colWidths;
  final List<double> rowHeights;
  final double totalWidth;
  final double totalHeight;

  @override
  void paint(Canvas canvas, Size size) {
    if (totalWidth <= 0 || totalHeight <= 0) return;

    // 열 시작 위치 x 좌표 계산
    final colStarts = List<double>.filled(cols + 1, 0.0);
    double curX = 0.0;
    for (int i = 0; i < cols; i++) {
      colStarts[i] = curX;
      curX += (colWidths[i] / totalWidth) * size.width;
    }
    colStarts[cols] = size.width;

    // 행 시작 위치 y 좌표 계산
    final rowStarts = List<double>.filled(rows + 1, 0.0);
    double curY = 0.0;
    for (int i = 0; i < rows; i++) {
      rowStarts[i] = curY;
      curY += (rowHeights[i] / totalHeight) * size.height;
    }
    rowStarts[rows] = size.height;

    // 1단계: 셀 배경색 채우기
    for (final cell in cells) {
      final r0 = cell.row.clamp(0, rows);
      final r1 = (cell.row + cell.rowSpan).clamp(0, rows);
      final c0 = cell.col.clamp(0, cols);
      final c1 = (cell.col + cell.colSpan).clamp(0, cols);

      final left = colStarts[c0];
      final right = colStarts[c1];
      final top = rowStarts[r0];
      final bottom = rowStarts[r1];

      final rect = Rect.fromLTRB(left, top, right, bottom);

      final fillColor = parseHexColor(cell.style.fill);
      if (fillColor != null && fillColor.a > 0) {
        final fillPaint = Paint()
          ..color = fillColor
          ..style = PaintingStyle.fill;
        canvas.drawRect(rect, fillPaint);
      }
    }

    // 2단계: 셀 텍스트 그리기
    for (final cell in cells) {
      final text = cell.text.trim();
      if (text.isEmpty) continue;

      final r0 = cell.row.clamp(0, rows);
      final r1 = (cell.row + cell.rowSpan).clamp(0, rows);
      final c0 = cell.col.clamp(0, cols);
      final c1 = (cell.col + cell.colSpan).clamp(0, cols);

      final left = colStarts[c0];
      final right = colStarts[c1];
      final top = rowStarts[r0];
      final bottom = rowStarts[r1];

      final rectWidth = right - left;
      final rectHeight = bottom - top;

      // 너무 작은 셀은 텍스트 생략
      if (rectWidth < 14 || rectHeight < 10) continue;

      final textColor =
          parseHexColor(cell.style.color) ?? const Color(0xff1e293b);
      final fontSize = (rectHeight * 0.42).clamp(8.0, 13.0);

      TextAlign align = TextAlign.left;
      if (cell.align.toLowerCase() == 'center') {
        align = TextAlign.center;
      } else if (cell.align.toLowerCase() == 'right') {
        align = TextAlign.right;
      }

      final textSpan = TextSpan(
        text: text,
        style: TextStyle(
          color: textColor,
          fontSize: fontSize,
          fontWeight: cell.style.bold ? FontWeight.bold : FontWeight.normal,
        ),
      );

      final textPainter = TextPainter(
        text: textSpan,
        textAlign: align,
        textDirection: TextDirection.ltr,
        maxLines: math.max(1, (rectHeight / (fontSize * 1.3)).floor()),
        ellipsis: '…',
      );

      const paddingH = 3.0;
      final availableWidth = math.max(4.0, rectWidth - paddingH * 2);
      textPainter.layout(minWidth: 0, maxWidth: availableWidth);

      double textX = left + paddingH;
      if (align == TextAlign.center) {
        textX = left + (rectWidth - textPainter.width) / 2;
      } else if (align == TextAlign.right) {
        textX = right - paddingH - textPainter.width;
      }
      final textY = top + (rectHeight - textPainter.height) / 2;

      textPainter.paint(canvas, Offset(textX, textY));
    }

    // 3단계: 테두리 그리기
    for (final cell in cells) {
      final r0 = cell.row.clamp(0, rows);
      final r1 = (cell.row + cell.rowSpan).clamp(0, rows);
      final c0 = cell.col.clamp(0, cols);
      final c1 = (cell.col + cell.colSpan).clamp(0, cols);

      final left = colStarts[c0];
      final right = colStarts[c1];
      final top = rowStarts[r0];
      final bottom = rowStarts[r1];

      void drawBorderLine(CellBorderSide side, Offset p1, Offset p2) {
        if (side.type.toUpperCase() == 'NONE') return;
        final strokeW = (side.width * 1.5).clamp(0.5, 3.0);
        final color = parseHexColor(side.color) ?? const Color(0xff94a3b8);
        final paint = Paint()
          ..color = color
          ..strokeWidth = strokeW
          ..style = PaintingStyle.stroke;
        canvas.drawLine(p1, p2, paint);
      }

      drawBorderLine(cell.borders.top, Offset(left, top), Offset(right, top));
      drawBorderLine(
        cell.borders.bottom,
        Offset(left, bottom),
        Offset(right, bottom),
      );
      drawBorderLine(
        cell.borders.left,
        Offset(left, top),
        Offset(left, bottom),
      );
      drawBorderLine(
        cell.borders.right,
        Offset(right, top),
        Offset(right, bottom),
      );
    }

    // 외곽 기본 테두리
    final outerPaint = Paint()
      ..color = const Color(0xff64748b)
      ..strokeWidth = 1.0
      ..style = PaintingStyle.stroke;
    canvas.drawRect(Rect.fromLTWH(0, 0, size.width, size.height), outerPaint);
  }

  @override
  bool shouldRepaint(covariant _TableGridPainter oldDelegate) {
    return oldDelegate.rows != rows ||
        oldDelegate.cols != cols ||
        oldDelegate.cells != cells ||
        oldDelegate.totalWidth != totalWidth ||
        oldDelegate.totalHeight != totalHeight;
  }
}
