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

/// 병합(rowSpan/colSpan), 서식, 글상자 안 nested 표를 반영해 한/글 표 구조를 그리는 미리보기 위젯.
class TableGridPreview extends StatelessWidget {
  const TableGridPreview({
    super.key,
    required this.rows,
    required this.cols,
    required this.cellMeta,
    this.maxHeight,
    this.maxWidth,
    this.onCellTap,
    this.editedCellKeys = const {},
  });

  final int rows;
  final int cols;
  final List<List<CellMeta>> cellMeta;
  final double? maxHeight;
  final double? maxWidth;
  final void Function(int row, int col)? onCellTap;
  final Set<String> editedCellKeys;

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

        // 터치 좌표 계산용 시작 위치 목록 미리 계산
        final colStarts = List<double>.filled(cols + 1, 0.0);
        double curX = 0.0;
        for (int i = 0; i < cols; i++) {
          colStarts[i] = curX;
          curX += (colWidths[i] / totalWidth) * renderWidth;
        }
        colStarts[cols] = renderWidth;

        final rowStarts = List<double>.filled(rows + 1, 0.0);
        double curY = 0.0;
        for (int i = 0; i < rows; i++) {
          rowStarts[i] = curY;
          curY += (rowHeights[i] / totalHeight) * renderHeight;
        }
        rowStarts[rows] = renderHeight;

        Widget content = Container(
          width: renderWidth,
          height: renderHeight,
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(4),
            boxShadow: const [
              BoxShadow(
                color: Color(0x0d000000),
                blurRadius: 4,
                offset: Offset(0, 1),
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
                editedCellKeys: editedCellKeys,
              ),
            ),
          ),
        );

        if (onCellTap != null) {
          content = GestureDetector(
            behavior: HitTestBehavior.opaque,
            onTapUp: (details) {
              final pos = details.localPosition;
              for (final cell in cells) {
                final r0 = cell.row.clamp(0, rows);
                final r1 = (cell.row + cell.rowSpan).clamp(0, rows);
                final c0 = cell.col.clamp(0, cols);
                final c1 = (cell.col + cell.colSpan).clamp(0, cols);

                final left = colStarts[c0];
                final right = colStarts[c1];
                final top = rowStarts[r0];
                final bottom = rowStarts[r1];

                if (pos.dx >= left &&
                    pos.dx <= right &&
                    pos.dy >= top &&
                    pos.dy <= bottom) {
                  onCellTap!(cell.row, cell.col);
                  break;
                }
              }
            },
            child: MouseRegion(
              cursor: SystemMouseCursors.click,
              child: content,
            ),
          );
        }

        return Center(child: content);
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
    required this.editedCellKeys,
  });

  final int rows;
  final int cols;
  final List<CellMeta> cells;
  final List<double> colWidths;
  final List<double> rowHeights;
  final double totalWidth;
  final double totalHeight;
  final Set<String> editedCellKeys;

  @override
  void paint(Canvas canvas, Size size) {
    if (totalWidth <= 0 || totalHeight <= 0) return;

    _renderTable(
      canvas: canvas,
      rect: Rect.fromLTWH(0, 0, size.width, size.height),
      rows: rows,
      cols: cols,
      cells: cells,
      colWidths: colWidths,
      rowHeights: rowHeights,
      totalWidth: totalWidth,
      totalHeight: totalHeight,
      editedKeys: editedCellKeys,
      depth: 0,
    );
  }

  void _renderTable({
    required Canvas canvas,
    required Rect rect,
    required int rows,
    required int cols,
    required List<CellMeta> cells,
    required List<double> colWidths,
    required List<double> rowHeights,
    required double totalWidth,
    required double totalHeight,
    Set<String> editedKeys = const {},
    int depth = 0,
  }) {
    if (rect.width <= 0 || rect.height <= 0 || totalWidth <= 0 || totalHeight <= 0) {
      return;
    }

    final colStarts = List<double>.filled(cols + 1, 0.0);
    double curX = rect.left;
    for (int i = 0; i < cols; i++) {
      colStarts[i] = curX;
      curX += (colWidths[i] / totalWidth) * rect.width;
    }
    colStarts[cols] = rect.right;

    final rowStarts = List<double>.filled(rows + 1, 0.0);
    double curY = rect.top;
    for (int i = 0; i < rows; i++) {
      rowStarts[i] = curY;
      curY += (rowHeights[i] / totalHeight) * rect.height;
    }
    rowStarts[rows] = rect.bottom;

    // 1단계: 셀 배경색 채우기 및 편집된 칸 강조
    for (final cell in cells) {
      final r0 = cell.row.clamp(0, rows);
      final r1 = (cell.row + cell.rowSpan).clamp(0, rows);
      final c0 = cell.col.clamp(0, cols);
      final c1 = (cell.col + cell.colSpan).clamp(0, cols);

      final left = colStarts[c0];
      final right = colStarts[c1];
      final top = rowStarts[r0];
      final bottom = rowStarts[r1];

      final cellRect = Rect.fromLTRB(left, top, right, bottom);

      final fillColor = parseHexColor(cell.style.fill);
      if (fillColor != null && fillColor.a > 0) {
        final fillPaint = Paint()
          ..color = fillColor
          ..style = PaintingStyle.fill;
        canvas.drawRect(cellRect, fillPaint);
      }

      // 사용자가 직접 입력한 칸 강조
      final cellKey = '${cell.row},${cell.col}';
      if (editedKeys.contains(cellKey)) {
        final editHighlightPaint = Paint()
          ..color = const Color(0x332563eb)
          ..style = PaintingStyle.fill;
        canvas.drawRect(cellRect, editHighlightPaint);
      }
    }

    // 2단계: nested 표 그리기 (글상자 안 축소 표)
    for (final cell in cells) {
      final nestedList = cell.nested;
      if (nestedList != null && nestedList.isNotEmpty && depth < 2) {
        final r0 = cell.row.clamp(0, rows);
        final r1 = (cell.row + cell.rowSpan).clamp(0, rows);
        final c0 = cell.col.clamp(0, cols);
        final c1 = (cell.col + cell.colSpan).clamp(0, cols);

        final cellRect = Rect.fromLTRB(
          colStarts[c0],
          rowStarts[r0],
          colStarts[c1],
          rowStarts[r1],
        );

        final innerRect = cellRect.deflate(2.0);
        if (innerRect.width > 12 && innerRect.height > 10) {
          final count = nestedList.length;
          final subHeight = innerRect.height / count;

          for (int ni = 0; ni < count; ni++) {
            final nestedTable = nestedList[ni];
            final subRect = Rect.fromLTWH(
              innerRect.left,
              innerRect.top + ni * subHeight,
              innerRect.width,
              subHeight,
            );

            _drawSingleNestedTable(
              canvas: canvas,
              rect: subRect,
              table: nestedTable,
              depth: depth + 1,
            );
          }
        }
      }
    }

    // 3단계: 셀 텍스트 그리기
    for (final cell in cells) {
      // nested가 이미 채워져 있는 셀에서 텍스트가 비어있지 않더라도 크기가 작으면 nested 우선
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

      if (rectWidth < 12 || rectHeight < 8) continue;

      final textColor =
          parseHexColor(cell.style.color) ?? const Color(0xff1e293b);
      final fontSize = (rectHeight * 0.42).clamp(depth > 0 ? 6.0 : 8.0, 13.0);

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

    // 4단계: 셀 테두리 그리기
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

      // 사용자가 직접 입력한 칸 테두리 강조 표시 (depth == 0인 경우)
      if (depth == 0 && editedKeys.contains('${cell.row},${cell.col}')) {
        final highlightBorderPaint = Paint()
          ..color = const Color(0xff2563eb)
          ..strokeWidth = 1.5
          ..style = PaintingStyle.stroke;
        canvas.drawRect(Rect.fromLTRB(left, top, right, bottom), highlightBorderPaint);
      }
    }

    // 5단계: 외곽 기본 테두리
    final outerPaint = Paint()
      ..color = depth == 0 ? const Color(0xff64748b) : const Color(0xff94a3b8)
      ..strokeWidth = depth == 0 ? 1.0 : 0.7
      ..style = PaintingStyle.stroke;
    canvas.drawRect(rect, outerPaint);
  }

  void _drawSingleNestedTable({
    required Canvas canvas,
    required Rect rect,
    required TablePreview table,
    required int depth,
  }) {
    if (table.rows <= 0 || table.cols <= 0 || table.cellMeta.isEmpty) return;

    final nCells = <CellMeta>[];
    for (final rowList in table.cellMeta) {
      nCells.addAll(rowList);
    }

    final nColWidths = List<double>.filled(table.cols, 1.0);
    final nColHasExact = List<bool>.filled(table.cols, false);
    for (final c in nCells) {
      if (c.colSpan == 1 && c.col >= 0 && c.col < table.cols) {
        if (!nColHasExact[c.col] || c.width > nColWidths[c.col]) {
          nColWidths[c.col] = c.width > 0 ? c.width : 1.0;
          nColHasExact[c.col] = true;
        }
      }
    }
    final nTotalW = nColWidths.fold<double>(0.0, (a, b) => a + b);

    final nRowHeights = List<double>.filled(table.rows, 1.0);
    final nRowHasExact = List<bool>.filled(table.rows, false);
    for (final c in nCells) {
      if (c.rowSpan == 1 && c.row >= 0 && c.row < table.rows) {
        if (!nRowHasExact[c.row] || c.height > nRowHeights[c.row]) {
          nRowHeights[c.row] = c.height > 0 ? c.height : 1.0;
          nRowHasExact[c.row] = true;
        }
      }
    }
    final nTotalH = nRowHeights.fold<double>(0.0, (a, b) => a + b);

    canvas.save();
    canvas.clipRect(rect);
    _renderTable(
      canvas: canvas,
      rect: rect,
      rows: table.rows,
      cols: table.cols,
      cells: nCells,
      colWidths: nColWidths,
      rowHeights: nRowHeights,
      totalWidth: nTotalW,
      totalHeight: nTotalH,
      depth: depth,
    );
    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant _TableGridPainter oldDelegate) {
    return oldDelegate.rows != rows ||
        oldDelegate.cols != cols ||
        oldDelegate.cells != cells ||
        oldDelegate.totalWidth != totalWidth ||
        oldDelegate.totalHeight != totalHeight ||
        oldDelegate.editedCellKeys != editedCellKeys;
  }
}
