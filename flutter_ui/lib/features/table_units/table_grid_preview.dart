import 'dart:convert';
import 'dart:math' as math;
import 'dart:typed_data';
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

/// 칸 안/밖에 그려지는 그리기 개체(도형/화살표/그림 등).
class CellShape {
  const CellShape({
    this.kind = 'other',
    this.x = 0.0,
    this.y = 0.0,
    this.w = 1.0,
    this.h = 1.0,
    this.direction = 'none',
    this.fill,
    this.line,
    this.text = '',
    this.src,
  });

  final String kind;
  final double x;
  final double y;
  final double w;
  final double h;
  final String direction;
  final String? fill;
  final String? line;
  final String text;

  /// 그림 개체의 실제 그림(data:image/…;base64,…). 있으면 회색 상자 대신 그 그림을 그린다(화살표 그림 등).
  final String? src;

  /// src의 그림 바이트(없거나 잘못되면 null).
  Uint8List? get imageBytes {
    final value = src;
    if (value == null || !value.startsWith('data:image/')) return null;
    final comma = value.indexOf(',');
    if (comma < 0) return null;
    try {
      return base64Decode(value.substring(comma + 1));
    } catch (_) {
      return null;
    }
  }

  factory CellShape.fromJson(Map<dynamic, dynamic> json) => CellShape(
    kind: '${json['kind'] ?? 'other'}',
    x: (json['x'] as num?)?.toDouble() ?? 0.0,
    y: (json['y'] as num?)?.toDouble() ?? 0.0,
    w: (json['w'] as num?)?.toDouble() ?? 1.0,
    h: (json['h'] as num?)?.toDouble() ?? 1.0,
    direction: '${json['direction'] ?? 'none'}',
    fill: json['fill'] as String?,
    line: json['line'] as String?,
    text: '${json['text'] ?? ''}',
    src: json['src'] as String?,
  );

  Map<String, dynamic> toJson() => {
    'kind': kind,
    'x': x,
    'y': y,
    'w': w,
    'h': h,
    'direction': direction,
    if (fill != null) 'fill': fill,
    if (line != null) 'line': line,
    if (text.isNotEmpty) 'text': text,
    if (src != null) 'src': src,
  };
}

/// 병합(rowSpan/colSpan), 서식, 글상자 안 nested 표를 반영해 한/글 표 구조를 그리는 미리보기 위젯.
class TableGridPreview extends StatelessWidget {
  const TableGridPreview({
    super.key,
    required this.rows,
    required this.cols,
    required this.cellMeta,
    this.shapes,
    this.maxHeight,
    this.maxWidth,
    this.onCellTap,
    this.editedCellKeys = const {},
  });

  final int rows;
  final int cols;
  final List<List<CellMeta>> cellMeta;
  final Map<String, List<CellShape>>? shapes;
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

    // 셀별 shapes 취합
    final resolvedCellShapes = <String, List<CellShape>>{};
    if (shapes != null) {
      shapes!.forEach((key, list) {
        resolvedCellShapes[key] = List.from(list);
      });
    }
    for (final cell in cells) {
      try {
        final dynamic d = cell;
        final s = d.shapes;
        if (s is List) {
          final list = <CellShape>[];
          for (final item in s) {
            if (item is CellShape) {
              list.add(item);
            } else if (item is Map) {
              list.add(CellShape.fromJson(item));
            }
          }
          if (list.isNotEmpty) {
            final key = '${cell.row},${cell.col}';
            resolvedCellShapes.putIfAbsent(key, () => []).addAll(list);
          }
        }
      } catch (_) {}
    }
    final hasAnyShapes = resolvedCellShapes.values.any(
      (list) => list.isNotEmpty,
    );

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
          key: const Key('tableGridContent'),
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
            child: Stack(
              fit: StackFit.expand,
              children: [
                CustomPaint(
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
                if (hasAnyShapes)
                  CustomPaint(
                    key: const Key('tableShapesLayer'),
                    size: Size(renderWidth, renderHeight),
                    painter: TableShapesPainter(
                      rows: rows,
                      cols: cols,
                      cells: cells,
                      colWidths: colWidths,
                      rowHeights: rowHeights,
                      totalWidth: totalWidth,
                      totalHeight: totalHeight,
                      cellShapes: resolvedCellShapes,
                    ),
                  ),
                // 그림 개체(예: 신구대조표·추진절차의 화살표 그림)는 실제 그림으로 그린다.
                for (final cell in cells)
                  for (final shape
                      in resolvedCellShapes['${cell.row},${cell.col}'] ??
                          const <CellShape>[])
                    if (shape.imageBytes != null)
                      Positioned(
                        left:
                            colStarts[cell.col.clamp(0, cols)] +
                            shape.x *
                                (colStarts[(cell.col + cell.colSpan).clamp(
                                      0,
                                      cols,
                                    )] -
                                    colStarts[cell.col.clamp(0, cols)]),
                        top:
                            rowStarts[cell.row.clamp(0, rows)] +
                            shape.y *
                                (rowStarts[(cell.row + cell.rowSpan).clamp(
                                      0,
                                      rows,
                                    )] -
                                    rowStarts[cell.row.clamp(0, rows)]),
                        width:
                            shape.w *
                            (colStarts[(cell.col + cell.colSpan).clamp(
                                  0,
                                  cols,
                                )] -
                                colStarts[cell.col.clamp(0, cols)]),
                        height:
                            shape.h *
                            (rowStarts[(cell.row + cell.rowSpan).clamp(
                                  0,
                                  rows,
                                )] -
                                rowStarts[cell.row.clamp(0, rows)]),
                        child: IgnorePointer(
                          child: Image.memory(
                            shape.imageBytes!,
                            key: Key('tableShapeImage_${cell.row}_${cell.col}'),
                            fit: BoxFit.fill,
                            gaplessPlayback: true,
                          ),
                        ),
                      ),
              ],
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
    if (rect.width <= 0 ||
        rect.height <= 0 ||
        totalWidth <= 0 ||
        totalHeight <= 0) {
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
        canvas.drawRect(
          Rect.fromLTRB(left, top, right, bottom),
          highlightBorderPaint,
        );
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

/// 표 그림 영역 전체 위에 칸 사각형 기준으로 도형들을 그리는 페인터.
class TableShapesPainter extends CustomPainter {
  const TableShapesPainter({
    required this.rows,
    required this.cols,
    required this.cells,
    required this.colWidths,
    required this.rowHeights,
    required this.totalWidth,
    required this.totalHeight,
    required this.cellShapes,
  });

  final int rows;
  final int cols;
  final List<CellMeta> cells;
  final List<double> colWidths;
  final List<double> rowHeights;
  final double totalWidth;
  final double totalHeight;
  final Map<String, List<CellShape>> cellShapes;

  @override
  void paint(Canvas canvas, Size size) {
    if (totalWidth <= 0 || totalHeight <= 0 || cellShapes.isEmpty) return;

    final colStarts = List<double>.filled(cols + 1, 0.0);
    double curX = 0.0;
    for (int i = 0; i < cols; i++) {
      colStarts[i] = curX;
      curX += (colWidths[i] / totalWidth) * size.width;
    }
    colStarts[cols] = size.width;

    final rowStarts = List<double>.filled(rows + 1, 0.0);
    double curY = 0.0;
    for (int i = 0; i < rows; i++) {
      rowStarts[i] = curY;
      curY += (rowHeights[i] / totalHeight) * size.height;
    }
    rowStarts[rows] = size.height;

    for (final cell in cells) {
      final key = '${cell.row},${cell.col}';
      final shapes = cellShapes[key];
      if (shapes == null || shapes.isEmpty) continue;

      final r0 = cell.row.clamp(0, rows);
      final r1 = (cell.row + cell.rowSpan).clamp(0, rows);
      final c0 = cell.col.clamp(0, cols);
      final c1 = (cell.col + cell.colSpan).clamp(0, cols);

      final cellLeft = colStarts[c0];
      final cellRight = colStarts[c1];
      final cellTop = rowStarts[r0];
      final cellBottom = rowStarts[r1];

      final cellW = cellRight - cellLeft;
      final cellH = cellBottom - cellTop;
      if (cellW <= 0 || cellH <= 0) continue;

      for (final shape in shapes) {
        final shapeLeft = cellLeft + shape.x * cellW;
        final shapeTop = cellTop + shape.y * cellH;
        final shapeW = shape.w * cellW;
        final shapeH = shape.h * cellH;
        final shapeRect = Rect.fromLTWH(shapeLeft, shapeTop, shapeW, shapeH);

        _drawShape(canvas, shape, shapeRect);
      }
    }
  }

  void _drawShape(Canvas canvas, CellShape shape, Rect rect) {
    if (rect.width <= 0 || rect.height <= 0) return;

    final kind = shape.kind.toLowerCase();
    final dir = shape.direction.toLowerCase();
    final fillColor = parseHexColor(shape.fill);
    final lineColor = parseHexColor(shape.line);

    if (kind == 'arrow') {
      _drawArrow(canvas, rect, dir, fillColor, lineColor);
    } else if (kind == 'triangle') {
      _drawTriangle(canvas, rect, dir, fillColor, lineColor);
    } else if (kind == 'line') {
      _drawLine(canvas, rect, dir, lineColor ?? fillColor);
    } else if (kind == 'rect') {
      _drawRect(canvas, rect, fillColor, lineColor);
    } else if (kind == 'ellipse') {
      _drawEllipse(canvas, rect, fillColor, lineColor);
    } else if (kind == 'pic' || kind == 'other') {
      if (shape.imageBytes == null) {
        _drawPicOrOther(canvas, rect, fillColor, lineColor);
      }
    }

    if (shape.text.isNotEmpty) {
      _drawShapeText(canvas, rect, shape.text, fillColor);
    }
  }

  void _drawArrow(
    Canvas canvas,
    Rect rect,
    String dir,
    Color? fillColor,
    Color? lineColor,
  ) {
    final effectiveFill = fillColor ?? const Color(0xff475569);
    final path = Path();

    switch (dir) {
      case 'left':
        final headRight = rect.left + rect.width * 0.45;
        final bodyTop = rect.top + rect.height * 0.28;
        final bodyBottom = rect.bottom - rect.height * 0.28;
        path.moveTo(rect.right, bodyTop);
        path.lineTo(headRight, bodyTop);
        path.lineTo(headRight, rect.top);
        path.lineTo(rect.left, rect.top + rect.height / 2);
        path.lineTo(headRight, rect.bottom);
        path.lineTo(headRight, bodyBottom);
        path.lineTo(rect.right, bodyBottom);
        path.close();
        break;
      case 'down':
        final headTop = rect.top + rect.height * 0.55;
        final bodyLeft = rect.left + rect.width * 0.28;
        final bodyRight = rect.right - rect.width * 0.28;
        path.moveTo(bodyLeft, rect.top);
        path.lineTo(bodyRight, rect.top);
        path.lineTo(bodyRight, headTop);
        path.lineTo(rect.right, headTop);
        path.lineTo(rect.left + rect.width / 2, rect.bottom);
        path.lineTo(rect.left, headTop);
        path.lineTo(bodyLeft, headTop);
        path.close();
        break;
      case 'up':
        final headBottom = rect.bottom - rect.height * 0.55;
        final bodyLeft = rect.left + rect.width * 0.28;
        final bodyRight = rect.right - rect.width * 0.28;
        path.moveTo(rect.left + rect.width / 2, rect.top);
        path.lineTo(rect.right, headBottom);
        path.lineTo(bodyRight, headBottom);
        path.lineTo(bodyRight, rect.bottom);
        path.lineTo(bodyLeft, rect.bottom);
        path.lineTo(bodyLeft, headBottom);
        path.lineTo(rect.left, headBottom);
        path.close();
        break;
      case 'right':
      default:
        final headLeft = rect.right - rect.width * 0.45;
        final bodyTop = rect.top + rect.height * 0.28;
        final bodyBottom = rect.bottom - rect.height * 0.28;
        path.moveTo(rect.left, bodyTop);
        path.lineTo(headLeft, bodyTop);
        path.lineTo(headLeft, rect.top);
        path.lineTo(rect.right, rect.top + rect.height / 2);
        path.lineTo(headLeft, rect.bottom);
        path.lineTo(headLeft, bodyBottom);
        path.lineTo(rect.left, bodyBottom);
        path.close();
        break;
    }

    final fillPaint = Paint()
      ..color = effectiveFill
      ..style = PaintingStyle.fill;
    canvas.drawPath(path, fillPaint);

    if (lineColor != null) {
      final strokePaint = Paint()
        ..color = lineColor
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.0;
      canvas.drawPath(path, strokePaint);
    }
  }

  void _drawTriangle(
    Canvas canvas,
    Rect rect,
    String dir,
    Color? fillColor,
    Color? lineColor,
  ) {
    final effectiveFill = fillColor ?? const Color(0xff475569);
    final path = Path();

    switch (dir) {
      case 'left':
        path.moveTo(rect.right, rect.top);
        path.lineTo(rect.left, rect.top + rect.height / 2);
        path.lineTo(rect.right, rect.bottom);
        path.close();
        break;
      case 'down':
        path.moveTo(rect.left, rect.top);
        path.lineTo(rect.right, rect.top);
        path.lineTo(rect.left + rect.width / 2, rect.bottom);
        path.close();
        break;
      case 'up':
        path.moveTo(rect.left + rect.width / 2, rect.top);
        path.lineTo(rect.right, rect.bottom);
        path.lineTo(rect.left, rect.bottom);
        path.close();
        break;
      case 'right':
      default:
        path.moveTo(rect.left, rect.top);
        path.lineTo(rect.right, rect.top + rect.height / 2);
        path.lineTo(rect.left, rect.bottom);
        path.close();
        break;
    }

    final fillPaint = Paint()
      ..color = effectiveFill
      ..style = PaintingStyle.fill;
    canvas.drawPath(path, fillPaint);

    if (lineColor != null) {
      final strokePaint = Paint()
        ..color = lineColor
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.0;
      canvas.drawPath(path, strokePaint);
    }
  }

  void _drawLine(Canvas canvas, Rect rect, String dir, Color? lineColor) {
    final effectiveColor = lineColor ?? const Color(0xff475569);
    final paint = Paint()
      ..color = effectiveColor
      ..strokeWidth = 1.8
      ..style = PaintingStyle.stroke;

    Offset p1, p2;
    switch (dir) {
      case 'down':
      case 'up':
        p1 = Offset(rect.left + rect.width / 2, rect.top);
        p2 = Offset(rect.left + rect.width / 2, rect.bottom);
        break;
      case 'right':
      case 'left':
        p1 = Offset(rect.left, rect.top + rect.height / 2);
        p2 = Offset(rect.right, rect.top + rect.height / 2);
        break;
      default:
        if (rect.width >= rect.height) {
          p1 = Offset(rect.left, rect.top + rect.height / 2);
          p2 = Offset(rect.right, rect.top + rect.height / 2);
        } else {
          p1 = Offset(rect.left + rect.width / 2, rect.top);
          p2 = Offset(rect.left + rect.width / 2, rect.bottom);
        }
        break;
    }
    canvas.drawLine(p1, p2, paint);
  }

  void _drawRect(Canvas canvas, Rect rect, Color? fillColor, Color? lineColor) {
    if (fillColor != null && fillColor.a > 0) {
      final fillPaint = Paint()
        ..color = fillColor
        ..style = PaintingStyle.fill;
      canvas.drawRect(rect, fillPaint);
    }
    final effectiveLine = lineColor ?? const Color(0xff64748b);
    final borderPaint = Paint()
      ..color = effectiveLine
      ..strokeWidth = 1.2
      ..style = PaintingStyle.stroke;
    canvas.drawRect(rect, borderPaint);
  }

  void _drawEllipse(
    Canvas canvas,
    Rect rect,
    Color? fillColor,
    Color? lineColor,
  ) {
    if (fillColor != null && fillColor.a > 0) {
      final fillPaint = Paint()
        ..color = fillColor
        ..style = PaintingStyle.fill;
      canvas.drawOval(rect, fillPaint);
    }
    final effectiveLine = lineColor ?? const Color(0xff64748b);
    final borderPaint = Paint()
      ..color = effectiveLine
      ..strokeWidth = 1.2
      ..style = PaintingStyle.stroke;
    canvas.drawOval(rect, borderPaint);
  }

  void _drawPicOrOther(
    Canvas canvas,
    Rect rect,
    Color? fillColor,
    Color? lineColor,
  ) {
    final bgPaint = Paint()
      ..color = fillColor ?? const Color(0xfff1f5f9)
      ..style = PaintingStyle.fill;
    canvas.drawRRect(
      RRect.fromRectAndRadius(rect, const Radius.circular(2)),
      bgPaint,
    );

    final borderPaint = Paint()
      ..color = lineColor ?? const Color(0xffcbd5e1)
      ..strokeWidth = 1.0
      ..style = PaintingStyle.stroke;
    canvas.drawRRect(
      RRect.fromRectAndRadius(rect, const Radius.circular(2)),
      borderPaint,
    );

    final iconW = math.min(rect.width * 0.6, 24.0);
    final iconH = math.min(rect.height * 0.6, 18.0);
    if (iconW > 8 && iconH > 6) {
      final cx = rect.left + rect.width / 2;
      final cy = rect.top + rect.height / 2;
      final iRect = Rect.fromCenter(
        center: Offset(cx, cy),
        width: iconW,
        height: iconH,
      );

      final iconPaint = Paint()
        ..color = const Color(0xff94a3b8)
        ..style = PaintingStyle.fill;

      final mountain1 = Path();
      mountain1.moveTo(iRect.left, iRect.bottom);
      mountain1.lineTo(
        iRect.left + iRect.width * 0.4,
        iRect.top + iRect.height * 0.3,
      );
      mountain1.lineTo(iRect.left + iRect.width * 0.7, iRect.bottom);
      mountain1.close();
      canvas.drawPath(mountain1, iconPaint);

      final mountain2 = Path();
      mountain2.moveTo(iRect.left + iRect.width * 0.45, iRect.bottom);
      mountain2.lineTo(
        iRect.left + iRect.width * 0.75,
        iRect.top + iRect.height * 0.45,
      );
      mountain2.lineTo(iRect.right, iRect.bottom);
      mountain2.close();
      canvas.drawPath(mountain2, iconPaint);

      final sunRadius = math.min(iRect.width, iRect.height) * 0.16;
      canvas.drawCircle(
        Offset(iRect.right - sunRadius * 1.5, iRect.top + sunRadius * 1.5),
        sunRadius,
        iconPaint,
      );
    }
  }

  void _drawShapeText(Canvas canvas, Rect rect, String text, Color? fillColor) {
    if (rect.width < 10 || rect.height < 8) return;

    Color textColor = const Color(0xff1e293b);
    if (fillColor != null &&
        (fillColor.r * 0.299 + fillColor.g * 0.587 + fillColor.b * 0.114) <
            140) {
      textColor = Colors.white;
    }

    final fontSize = (rect.height * 0.35).clamp(8.0, 12.0);
    final textSpan = TextSpan(
      text: text,
      style: TextStyle(
        color: textColor,
        fontSize: fontSize,
        fontWeight: FontWeight.w500,
      ),
    );
    final tp = TextPainter(
      text: textSpan,
      textAlign: TextAlign.center,
      textDirection: TextDirection.ltr,
      maxLines: 1,
      ellipsis: '…',
    );
    tp.layout(minWidth: 0, maxWidth: math.max(4.0, rect.width - 4.0));
    final tx = rect.left + (rect.width - tp.width) / 2;
    final ty = rect.top + (rect.height - tp.height) / 2;
    tp.paint(canvas, Offset(tx, ty));
  }

  @override
  bool shouldRepaint(covariant TableShapesPainter oldDelegate) {
    return oldDelegate.rows != rows ||
        oldDelegate.cols != cols ||
        oldDelegate.cells != cells ||
        oldDelegate.totalWidth != totalWidth ||
        oldDelegate.totalHeight != totalHeight ||
        oldDelegate.cellShapes != cellShapes;
  }
}
