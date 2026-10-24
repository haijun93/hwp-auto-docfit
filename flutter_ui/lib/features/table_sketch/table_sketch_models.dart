import 'dart:math' as math;
import 'dart:ui' show Offset;

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

/// 격자 설정 (cols, rows, cell_mm).
class GridConfig {
  const GridConfig({
    this.cols = 36,
    this.rows = 50,
    this.cellMm = 5.0,
  });

  final int cols;
  final int rows;
  final double cellMm;

  factory GridConfig.fromJson(Map<dynamic, dynamic>? json) {
    if (json == null) return const GridConfig();
    return GridConfig(
      cols: (json['cols'] as num?)?.toInt() ?? 36,
      rows: (json['rows'] as num?)?.toInt() ?? 50,
      cellMm: (json['cell_mm'] as num?)?.toDouble() ?? 5.0,
    );
  }

  Map<String, dynamic> toJson() => {
    'cols': cols,
    'rows': rows,
    'cell_mm': cellMm,
  };

  GridConfig copyWith({int? cols, int? rows, double? cellMm}) => GridConfig(
    cols: cols ?? this.cols,
    rows: rows ?? this.rows,
    cellMm: cellMm ?? this.cellMm,
  );
}

/// 표그림판 직선 (가로, 세로, 45도 대각선만 허용).
class SketchLine {
  const SketchLine({
    required this.x1,
    required this.y1,
    required this.x2,
    required this.y2,
    this.width = 'thin',
    this.style = 'solid',
    this.groupId,
    this.color,
    this.widthMm,
  });

  final int x1;
  final int y1;
  final int x2;
  final int y2;
  final String width; // "thin" | "thick" | "double"
  final String style; // "solid" | "dash" | "dot"
  final String? groupId;
  final String? color;
  final double? widthMm;

  /// 가로선(y1==y2), 세로선(x1==x2), 대각선(|x2-x1|==|y2-y1|, 45°) 검증.
  bool get isValid {
    if (x1 == x2 && y1 == y2) return false;
    final isHorizontal = y1 == y2;
    final isVertical = x1 == x2;
    final isDiagonal = (x2 - x1).abs() == (y2 - y1).abs();
    return isHorizontal || isVertical || isDiagonal;
  }

  /// 좌표 일치 여부 (방향 반대 포함).
  bool isSameCoords(int ox1, int oy1, int ox2, int oy2) {
    return (x1 == ox1 && y1 == oy1 && x2 == ox2 && y2 == oy2) ||
        (x1 == ox2 && y1 == oy2 && x2 == ox1 && y2 == oy1);
  }

  factory SketchLine.fromJson(Map<dynamic, dynamic> json) => SketchLine(
    x1: (json['x1'] as num?)?.toInt() ?? 0,
    y1: (json['y1'] as num?)?.toInt() ?? 0,
    x2: (json['x2'] as num?)?.toInt() ?? 0,
    y2: (json['y2'] as num?)?.toInt() ?? 0,
    width: '${json['width'] ?? 'thin'}',
    style: '${json['style'] ?? 'solid'}',
    groupId: json['group_id'] as String?,
    color: json['color'] as String?,
    widthMm: (json['width_mm'] as num?)?.toDouble(),
  );

  Map<String, dynamic> toJson() => {
    'x1': x1,
    'y1': y1,
    'x2': x2,
    'y2': y2,
    'width': width,
    'style': style,
    if (groupId != null) 'group_id': groupId,
    if (color != null) 'color': color,
    if (widthMm != null) 'width_mm': widthMm,
  };

  SketchLine copyWith({
    int? x1,
    int? y1,
    int? x2,
    int? y2,
    String? width,
    String? style,
    String? groupId,
    String? color,
    double? widthMm,
  }) => SketchLine(
    x1: x1 ?? this.x1,
    y1: y1 ?? this.y1,
    x2: x2 ?? this.x2,
    y2: y2 ?? this.y2,
    width: width ?? this.width,
    style: style ?? this.style,
    groupId: groupId ?? this.groupId,
    color: color ?? this.color,
    widthMm: widthMm ?? this.widthMm,
  );
}

/// 선분을 셀 단위(격자 1칸) 세그먼트로 나눈 뒤 segmentIndex 번째 조각을 제거한 결과 반환.
/// 가로선(y1==y2), 세로선(x1==x2), 대각선(|x2-x1|==|y2-y1|) 지원.
List<SketchLine> splitLineAt(SketchLine line, int segmentIndex) {
  final dx = line.x2 - line.x1;
  final dy = line.y2 - line.y1;
  final len = math.max(dx.abs(), dy.abs());
  if (len <= 1) {
    return const [];
  }
  if (segmentIndex < 0 || segmentIndex >= len) {
    return [line];
  }

  final stepX = dx == 0 ? 0 : (dx > 0 ? 1 : -1);
  final stepY = dy == 0 ? 0 : (dy > 0 ? 1 : -1);

  final results = <SketchLine>[];

  // 앞쪽 남은 선 (0 ~ segmentIndex)
  if (segmentIndex > 0) {
    results.add(line.copyWith(
      x1: line.x1,
      y1: line.y1,
      x2: line.x1 + stepX * segmentIndex,
      y2: line.y1 + stepY * segmentIndex,
    ));
  }

  // 뒤쪽 남은 선 (segmentIndex + 1 ~ len)
  if (segmentIndex + 1 < len) {
    results.add(line.copyWith(
      x1: line.x1 + stepX * (segmentIndex + 1),
      y1: line.y1 + stepY * (segmentIndex + 1),
      x2: line.x2,
      y2: line.y2,
    ));
  }

  return results;
}

/// 클릭 위치 pos(픽셀)에 대응하는 선 위의 셀 세그먼트 인덱스 반환 (0 <= index < length).
int? findLineSegmentIndex(
  SketchLine line,
  Offset pos,
  double cellSize, {
  double? maxDistance,
}) {
  final threshold = maxDistance ?? math.max(16.0, cellSize * 0.8);
  final p1 = Offset(line.x1 * cellSize, line.y1 * cellSize);
  final p2 = Offset(line.x2 * cellSize, line.y2 * cellSize);
  final dist = distanceToSegment(pos, p1, p2);
  if (dist > threshold) return null;

  final dx = line.x2 - line.x1;
  final dy = line.y2 - line.y1;
  final len = math.max(dx.abs(), dy.abs());
  if (len <= 0) return null;

  final v = p2 - p1;
  final len2 = v.dx * v.dx + v.dy * v.dy;
  if (len2 == 0) return 0;
  final t = (((pos.dx - p1.dx) * v.dx + (pos.dy - p1.dy) * v.dy) / len2)
      .clamp(0.0, 0.9999);
  final seg = (t * len).floor();
  return seg.clamp(0, len - 1);
}

/// 선의 segmentIndex 번째 1칸 세그먼트 선 객체 반환.
SketchLine? getLineSegment(SketchLine line, int segmentIndex) {
  final dx = line.x2 - line.x1;
  final dy = line.y2 - line.y1;
  final len = math.max(dx.abs(), dy.abs());
  if (segmentIndex < 0 || segmentIndex >= len) return null;
  final stepX = dx == 0 ? 0 : (dx > 0 ? 1 : -1);
  final stepY = dy == 0 ? 0 : (dy > 0 ? 1 : -1);
  return line.copyWith(
    x1: line.x1 + stepX * segmentIndex,
    y1: line.y1 + stepY * segmentIndex,
    x2: line.x1 + stepX * (segmentIndex + 1),
    y2: line.y1 + stepY * (segmentIndex + 1),
  );
}

/// 표그림판 칸 글자 (x, y는 칸 번호, 왼쪽 위 격자점).
class SketchText {
  const SketchText({
    required this.x,
    required this.y,
    required this.text,
    this.bold = false,
    this.align = 'center',
  });

  final int x;
  final int y;
  final String text;
  final bool bold;
  final String align; // "center" | "left" | "right"

  factory SketchText.fromJson(Map<dynamic, dynamic> json) => SketchText(
    x: (json['x'] as num?)?.toInt() ?? 0,
    y: (json['y'] as num?)?.toInt() ?? 0,
    text: '${json['text'] ?? ''}',
    bold: json['bold'] == true,
    align: '${json['align'] ?? 'center'}',
  );

  Map<String, dynamic> toJson() => {
    'x': x,
    'y': y,
    'text': text,
    'bold': bold,
    'align': align,
  };

  SketchText copyWith({
    int? x,
    int? y,
    String? text,
    bool? bold,
    String? align,
  }) => SketchText(
    x: x ?? this.x,
    y: y ?? this.y,
    text: text ?? this.text,
    bold: bold ?? this.bold,
    align: align ?? this.align,
  );
}

/// 표그림판 셀 배경색.
class SketchCellColor {
  const SketchCellColor({
    required this.x,
    required this.y,
    required this.color,
  });

  final int x;
  final int y;
  final String color;

  factory SketchCellColor.fromJson(Map<dynamic, dynamic> json) => SketchCellColor(
    x: (json['x'] as num?)?.toInt() ?? 0,
    y: (json['y'] as num?)?.toInt() ?? 0,
    color: '${json['color'] ?? '#FFFFFF'}',
  );

  Map<String, dynamic> toJson() => {
    'x': x,
    'y': y,
    'color': color,
  };

  SketchCellColor copyWith({int? x, int? y, String? color}) => SketchCellColor(
    x: x ?? this.x,
    y: y ?? this.y,
    color: color ?? this.color,
  );
}

/// 표그림판 문서 전체 데이터.
class TableSketchDoc {
  TableSketchDoc({
    this.grid = const GridConfig(),
    List<SketchLine>? lines,
    List<SketchText>? texts,
    List<SketchCellColor>? cellColors,
  })  : lines = lines ?? <SketchLine>[],
        texts = texts ?? <SketchText>[],
        cellColors = cellColors ?? <SketchCellColor>[];

  GridConfig grid;
  List<SketchLine> lines;
  List<SketchText> texts;
  List<SketchCellColor> cellColors;

  TableSketchDoc clone() => TableSketchDoc(
    grid: grid,
    lines: lines.map((l) => l.copyWith()).toList(),
    texts: texts.map((t) => t.copyWith()).toList(),
    cellColors: cellColors.map((c) => c.copyWith()).toList(),
  );

  factory TableSketchDoc.fromJson(Map<dynamic, dynamic> json) {
    final rawLines = json['lines'];
    final rawTexts = json['texts'];
    final rawColors = json['cell_colors'];
    final lines = <SketchLine>[];
    if (rawLines is List) {
      for (final item in rawLines) {
        if (item is Map) lines.add(SketchLine.fromJson(item));
      }
    }
    final texts = <SketchText>[];
    if (rawTexts is List) {
      for (final item in rawTexts) {
        if (item is Map) texts.add(SketchText.fromJson(item));
      }
    }
    final cellColors = <SketchCellColor>[];
    if (rawColors is List) {
      for (final item in rawColors) {
        if (item is Map) cellColors.add(SketchCellColor.fromJson(item));
      }
    }
    return TableSketchDoc(
      grid: GridConfig.fromJson(json['grid'] as Map?),
      lines: lines,
      texts: texts,
      cellColors: cellColors,
    );
  }

  Map<String, dynamic> toJson() => {
    'grid': grid.toJson(),
    'lines': lines.map((l) => l.toJson()).toList(),
    'texts': texts.map((t) => t.toJson()).toList(),
    'cell_colors': cellColors.map((c) => c.toJson()).toList(),
  };

  /// 선 추가 (동일 좌표 선이 있으면 교체).
  void addLine(SketchLine line) {
    if (!line.isValid) return;
    final idx = lines.indexWhere(
      (l) => l.isSameCoords(line.x1, line.y1, line.x2, line.y2),
    );
    if (idx >= 0) {
      lines[idx] = line;
    } else {
      lines.add(line);
    }
  }

  /// 텍스트 추가 또는 수정 (빈 글자면 제거).
  void setText(SketchText item) {
    final idx = texts.indexWhere((t) => t.x == item.x && t.y == item.y);
    if (item.text.trim().isEmpty) {
      if (idx >= 0) texts.removeAt(idx);
    } else {
      if (idx >= 0) {
        texts[idx] = item;
      } else {
        texts.add(item);
      }
    }
  }

  SketchText? findText(int x, int y) {
    final idx = texts.indexWhere((t) => t.x == x && t.y == y);
    return idx >= 0 ? texts[idx] : null;
  }

  /// 셀 배경색 지정 (color가 없거나 비어 있으면 제거).
  void setCellColor(int x, int y, String color) {
    final idx = cellColors.indexWhere((c) => c.x == x && c.y == y);
    final clean = color.trim();
    if (clean.isEmpty || clean.toLowerCase() == 'transparent' || clean.toLowerCase() == 'none') {
      if (idx >= 0) cellColors.removeAt(idx);
    } else {
      if (idx >= 0) {
        cellColors[idx] = cellColors[idx].copyWith(color: clean);
      } else {
        cellColors.add(SketchCellColor(x: x, y: y, color: clean));
      }
    }
  }

  String? getCellColor(int x, int y) {
    final idx = cellColors.indexWhere((c) => c.x == x && c.y == y);
    return idx >= 0 ? cellColors[idx].color : null;
  }
}

/// 표그림판 미리보기 응답 데이터.
class TableSketchPreviewResult {
  const TableSketchPreviewResult({
    required this.ok,
    this.rows = 0,
    this.cols = 0,
    this.cells = const [],
    this.widthMm = 0.0,
    this.heightMm = 0.0,
    this.warnings = const [],
    this.raw = const {},
  });

  final bool ok;
  final int rows;
  final int cols;
  final List<Map<String, dynamic>> cells;
  final double widthMm;
  final double heightMm;
  final List<String> warnings;
  final Map<String, dynamic> raw;

  factory TableSketchPreviewResult.fromJson(Map<dynamic, dynamic> json) {
    final rawCells = json['cells'];
    final cells = <Map<String, dynamic>>[];
    if (rawCells is List) {
      for (final c in rawCells) {
        if (c is Map) cells.add(Map<String, dynamic>.from(c));
      }
    }
    final rawWarns = json['warnings'];
    final warnings = <String>[];
    if (rawWarns is List) {
      for (final w in rawWarns) {
        warnings.add('$w');
      }
    }
    return TableSketchPreviewResult(
      ok: json['ok'] == true,
      rows: (json['rows'] as num?)?.toInt() ?? 0,
      cols: (json['cols'] as num?)?.toInt() ?? 0,
      cells: cells,
      widthMm: (json['width_mm'] as num?)?.toDouble() ?? 0.0,
      heightMm: (json['height_mm'] as num?)?.toDouble() ?? 0.0,
      warnings: warnings,
      raw: Map<String, dynamic>.from(json),
    );
  }
}

/// 표그림판 복사 응답 데이터.
class TableSketchCopyResult {
  const TableSketchCopyResult({
    required this.ok,
    required this.message,
  });

  final bool ok;
  final String message;

  factory TableSketchCopyResult.fromJson(Map<dynamic, dynamic> json) =>
      TableSketchCopyResult(
        ok: json['ok'] == true,
        message: '${json['message'] ?? ''}',
      );
}
