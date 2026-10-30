import 'dart:math' as math;

/// 격자 설정 (cols, rows, cell_mm).
class GridConfig {
  const GridConfig({this.cols = 36, this.rows = 50, this.cellMm = 5.0});

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
    this.layer,
  });

  /// 속한 레이어 id. null이면 아직 정하지 않은 새 선(다음 정리 때 지금 레이어로 들어간다).
  final String? layer;
  final int x1;
  final int y1;
  final int x2;
  final int y2;
  final String width; // "thin" | "thick" | "double"
  final String style; // "solid" | "dash" | "dot"

  int get lengthInUnits => math.max((x2 - x1).abs(), (y2 - y1).abs());

  /// 지정한 한 격자 구간을 지우고 남은 선을 원래 방향으로 반환한다.
  List<SketchLine> splitAtUnitIndex(int index) {
    if (!isValid || index < 0 || index >= lengthInUnits) return [this];
    final dx = (x2 - x1).sign;
    final dy = (y2 - y1).sign;
    return [
      if (index > 0) copyWith(x2: x1 + dx * index, y2: y1 + dy * index),
      if (index < lengthInUnits - 1)
        copyWith(x1: x1 + dx * (index + 1), y1: y1 + dy * (index + 1)),
    ];
  }

  /// 방향과 무관하게 일치하는 한 격자 구간만 지운다.
  List<SketchLine> splitByUnitSegment(int sx1, int sy1, int sx2, int sy2) {
    if (!isValid) return [this];
    final dx = (x2 - x1).sign;
    final dy = (y2 - y1).sign;
    for (var k = 0; k < lengthInUnits; k++) {
      final ax = x1 + dx * k;
      final ay = y1 + dy * k;
      final bx = ax + dx;
      final by = ay + dy;
      if ((sx1 == ax && sy1 == ay && sx2 == bx && sy2 == by) ||
          (sx2 == ax && sy2 == ay && sx1 == bx && sy1 == by)) {
        return splitAtUnitIndex(k);
      }
    }
    return [this];
  }

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
    layer: json['layer'] is String ? json['layer'] as String : null,
  );

  Map<String, dynamic> toJson() => {
    'x1': x1,
    'y1': y1,
    'x2': x2,
    'y2': y2,
    'width': width,
    'style': style,
    if (layer != null) 'layer': layer,
  };

  SketchLine copyWith({
    int? x1,
    int? y1,
    int? x2,
    int? y2,
    String? width,
    String? style,
    String? layer,
  }) => SketchLine(
    x1: x1 ?? this.x1,
    y1: y1 ?? this.y1,
    x2: x2 ?? this.x2,
    y2: y2 ?? this.y2,
    width: width ?? this.width,
    style: style ?? this.style,
    layer: layer ?? this.layer,
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
    this.layer,
  });

  final String? layer;
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
    layer: json['layer'] is String ? json['layer'] as String : null,
  );

  Map<String, dynamic> toJson() => {
    'x': x,
    'y': y,
    'text': text,
    'bold': bold,
    'align': align,
    if (layer != null) 'layer': layer,
  };

  SketchText copyWith({
    int? x,
    int? y,
    String? text,
    bool? bold,
    String? align,
    String? layer,
  }) => SketchText(
    x: x ?? this.x,
    y: y ?? this.y,
    text: text ?? this.text,
    bold: bold ?? this.bold,
    align: align ?? this.align,
    layer: layer ?? this.layer,
  );
}

/// 표 칸 배경 그림: (x, y)는 그림이 든 칸 안의 한 격자 칸, data는 PNG/JPG base64.
/// 그림은 그 칸(선으로 둘러싸인 영역) 크기에 맞춰 늘려 채운다(한/글 '크기에 맞추어').
class SketchImage {
  const SketchImage({
    required this.x,
    required this.y,
    required this.data,
    this.layer,
  });

  final String? layer;
  final int x;
  final int y;
  final String data;

  factory SketchImage.fromJson(Map<dynamic, dynamic> json) => SketchImage(
    x: (json['x'] as num?)?.toInt() ?? 0,
    y: (json['y'] as num?)?.toInt() ?? 0,
    data: '${json['data'] ?? ''}',
    layer: json['layer'] is String ? json['layer'] as String : null,
  );

  Map<String, dynamic> toJson() => {
    'x': x,
    'y': y,
    'data': data,
    if (layer != null) 'layer': layer,
  };

  SketchImage copyWith({int? x, int? y, String? layer}) => SketchImage(
    x: x ?? this.x,
    y: y ?? this.y,
    data: data,
    layer: layer ?? this.layer,
  );
}

/// 표그림판 레이어(포토샵처럼): 보이기·잠금·이름. 목록은 아래→위 순서다.
class SketchLayer {
  const SketchLayer({
    required this.id,
    required this.name,
    this.visible = true,
    this.locked = false,
  });

  final String id;
  final String name;
  final bool visible;
  final bool locked;

  /// 숨기거나 잠근 레이어의 개체는 고치는 도구(선택·지우개·이동)에서 빠진다.
  bool get editable => visible && !locked;

  factory SketchLayer.fromJson(Map<dynamic, dynamic> json) => SketchLayer(
    id: '${json['id'] ?? defaultSketchLayerId}',
    name: '${json['name'] ?? '레이어'}',
    visible: json['visible'] != false,
    locked: json['locked'] == true,
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'visible': visible,
    'locked': locked,
  };

  SketchLayer copyWith({String? name, bool? visible, bool? locked}) =>
      SketchLayer(
        id: id,
        name: name ?? this.name,
        visible: visible ?? this.visible,
        locked: locked ?? this.locked,
      );
}

const defaultSketchLayerId = 'layer-1';

/// 표그림판 문서 전체 데이터.
///
/// lines·texts·images는 고칠 수 있는(보이고 잠그지 않은) 레이어의 개체만 담는다. 숨기거나 잠근 레이어의
/// 개체는 [parked]에 따로 두어 선택·지우개·이동이 닿지 않게 하고, 그리기·저장·복사 때 다시 합친다.
class TableSketchDoc {
  TableSketchDoc({
    this.grid = const GridConfig(),
    List<SketchLine>? lines,
    List<SketchText>? texts,
    List<SketchImage>? images,
    List<SketchLayer>? layers,
    String? activeLayer,
    TableSketchDoc? parked,
  }) : lines = lines ?? <SketchLine>[],
       texts = texts ?? <SketchText>[],
       images = images ?? <SketchImage>[],
       layers =
           layers ??
           [const SketchLayer(id: defaultSketchLayerId, name: '레이어 1')],
       activeLayer = activeLayer ?? defaultSketchLayerId,
       _parkedLines = parked?.lines ?? <SketchLine>[],
       _parkedTexts = parked?.texts ?? <SketchText>[],
       _parkedImages = parked?.images ?? <SketchImage>[];

  GridConfig grid;
  List<SketchLine> lines;
  List<SketchText> texts;
  List<SketchImage> images;
  List<SketchLayer> layers;
  String activeLayer;
  List<SketchLine> _parkedLines;
  List<SketchText> _parkedTexts;
  List<SketchImage> _parkedImages;

  SketchLayer layerOf(String? id) => layers.firstWhere(
    (l) => l.id == id,
    orElse: () => layers.firstWhere(
      (l) => l.id == activeLayer,
      orElse: () => layers.first,
    ),
  );

  /// 레이어를 정하지 않은 새 개체를 지금 레이어에 넣는다(레이어를 바꾸기 전·저장 전에 부른다).
  void claimUnassigned() {
    final target = layerOf(activeLayer).id;
    lines = [
      for (final l in lines) l.layer == null ? l.copyWith(layer: target) : l,
    ];
    texts = [
      for (final t in texts) t.layer == null ? t.copyWith(layer: target) : t,
    ];
    images = [
      for (final i in images) i.layer == null ? i.copyWith(layer: target) : i,
    ];
  }

  /// 레이어 상태에 맞게 개체를 고칠 수 있는 목록과 [parked]로 나눈다.
  void repark() {
    claimUnassigned();
    final allLines = [...lines, ..._parkedLines];
    final allTexts = [...texts, ..._parkedTexts];
    final allImages = [...images, ..._parkedImages];
    bool editable(String? id) => layerOf(id).editable;
    lines = allLines.where((l) => editable(l.layer)).toList();
    texts = allTexts.where((t) => editable(t.layer)).toList();
    images = allImages.where((i) => editable(i.layer)).toList();
    _parkedLines = allLines.where((l) => !editable(l.layer)).toList();
    _parkedTexts = allTexts.where((t) => !editable(t.layer)).toList();
    _parkedImages = allImages.where((i) => !editable(i.layer)).toList();
  }

  /// 화면에 그릴 잠근(보이는) 레이어 개체.
  List<SketchLine> get lockedLines =>
      _parkedLines.where((l) => layerOf(l.layer).visible).toList();
  List<SketchText> get lockedTexts =>
      _parkedTexts.where((t) => layerOf(t.layer).visible).toList();

  int countIn(String layerId) =>
      [
        ...lines,
        ..._parkedLines,
      ].where((l) => (l.layer ?? activeLayer) == layerId).length +
      [
        ...texts,
        ..._parkedTexts,
      ].where((t) => (t.layer ?? activeLayer) == layerId).length +
      [
        ...images,
        ..._parkedImages,
      ].where((i) => (i.layer ?? activeLayer) == layerId).length;

  /// 고른 선·글을 다른 레이어로 옮긴다.
  void moveToLayer(
    Set<SketchLine> chosenLines,
    Set<SketchText> chosenTexts,
    String layerId,
  ) {
    lines = [
      for (final l in lines)
        chosenLines.contains(l) ? l.copyWith(layer: layerId) : l,
    ];
    texts = [
      for (final t in texts)
        chosenTexts.contains(t) ? t.copyWith(layer: layerId) : t,
    ];
    repark();
  }

  /// 레이어와 그 안의 개체를 지운다(마지막 레이어는 남긴다).
  void removeLayer(String layerId) {
    if (layers.length <= 1) return;
    claimUnassigned();
    lines.removeWhere((l) => l.layer == layerId);
    texts.removeWhere((t) => t.layer == layerId);
    images.removeWhere((i) => i.layer == layerId);
    _parkedLines.removeWhere((l) => l.layer == layerId);
    _parkedTexts.removeWhere((t) => t.layer == layerId);
    _parkedImages.removeWhere((i) => i.layer == layerId);
    layers = layers.where((l) => l.id != layerId).toList();
    if (activeLayer == layerId) activeLayer = layers.last.id;
  }

  /// 겹친 선을 포함하여 해당 한 격자 구간을 모두 지운다.
  bool eraseUnitSegment(int sx1, int sy1, int sx2, int sy2) {
    var changed = false;
    final remaining = <SketchLine>[];
    for (final line in lines) {
      final parts = line.splitByUnitSegment(sx1, sy1, sx2, sy2);
      if (parts.length != 1 || !identical(parts.first, line)) changed = true;
      remaining.addAll(parts);
    }
    if (changed) lines = remaining;
    return changed;
  }

  TableSketchDoc clone() => TableSketchDoc(
    grid: grid,
    lines: lines.map((l) => l.copyWith()).toList(),
    texts: texts.map((t) => t.copyWith()).toList(),
    images: List.of(images),
    layers: List.of(layers),
    activeLayer: activeLayer,
    parked: TableSketchDoc(
      lines: List.of(_parkedLines),
      texts: List.of(_parkedTexts),
      images: List.of(_parkedImages),
    ),
  );

  factory TableSketchDoc.fromJson(Map<dynamic, dynamic> json) {
    final rawLines = json['lines'];
    final rawTexts = json['texts'];
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
    final rawImages = json['images'];
    final images = <SketchImage>[];
    if (rawImages is List) {
      for (final item in rawImages) {
        if (item is Map) images.add(SketchImage.fromJson(item));
      }
    }
    final rawLayers = json['layers'];
    final layers = <SketchLayer>[];
    if (rawLayers is List) {
      for (final item in rawLayers) {
        if (item is Map) layers.add(SketchLayer.fromJson(item));
      }
    }
    final doc = TableSketchDoc(
      grid: GridConfig.fromJson(json['grid'] as Map?),
      lines: lines,
      texts: texts,
      images: images,
      layers: layers.isEmpty ? null : layers,
      activeLayer: json['active_layer'] is String
          ? json['active_layer'] as String
          : null,
    );
    if (!doc.layers.any((l) => l.id == doc.activeLayer)) {
      doc.activeLayer = doc.layers.last.id;
    }
    doc.repark();
    return doc;
  }

  /// 저장용: 모든 레이어의 개체와 레이어 목록. [forTable]이면 한/글 표로 바꿀 것만(숨긴 레이어 제외).
  Map<String, dynamic> toJson({bool forTable = false}) {
    claimUnassigned();
    bool keep(String? id) => !forTable || layerOf(id).visible;
    final allLines = [...lines, ..._parkedLines].where((l) => keep(l.layer));
    final allTexts = [...texts, ..._parkedTexts].where((t) => keep(t.layer));
    final allImages = [...images, ..._parkedImages].where((i) => keep(i.layer));
    // 한/글 표로 바꿀 때는 레이어 표시가 필요 없다(표 변환은 레이어를 모른다).
    Map<String, dynamic> item(Map<String, dynamic> json) =>
        forTable ? (json..remove('layer')) : json;
    return {
      'grid': grid.toJson(),
      'lines': allLines.map((l) => item(l.toJson())).toList(),
      'texts': allTexts.map((t) => item(t.toJson())).toList(),
      if (allImages.isNotEmpty)
        'images': allImages.map((i) => item(i.toJson())).toList(),
      if (!forTable) 'layers': layers.map((l) => l.toJson()).toList(),
      if (!forTable) 'active_layer': activeLayer,
    };
  }

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
  const TableSketchCopyResult({required this.ok, required this.message});

  final bool ok;
  final String message;

  factory TableSketchCopyResult.fromJson(Map<dynamic, dynamic> json) =>
      TableSketchCopyResult(
        ok: json['ok'] == true,
        message: '${json['message'] ?? ''}',
      );
}
