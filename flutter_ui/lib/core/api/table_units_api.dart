import 'abbreviation_api.dart' show ApiCall, ServiceApiException;

export 'abbreviation_api.dart' show ApiCall, ServiceApiException;

/// 정보단위 축 (행 또는 열)의 반복 범위와 기본값 설정.
class UnitAxis {
  const UnitAxis({
    required this.count,
    required this.min,
    required this.max,
    required this.core,
    required this.sep,
  });

  final int count;
  final int min;
  final int max;
  final int core;
  final int sep;

  UnitAxis copyWith({int? count, int? min, int? max, int? core, int? sep}) =>
      UnitAxis(
        count: count ?? this.count,
        min: min ?? this.min,
        max: max ?? this.max,
        core: core ?? this.core,
        sep: sep ?? this.sep,
      );

  factory UnitAxis.fromJson(Map<dynamic, dynamic> json) => UnitAxis(
    count: (json['count'] as num?)?.toInt() ?? 1,
    min: (json['min'] as num?)?.toInt() ?? 1,
    max: (json['max'] as num?)?.toInt() ?? 40,
    core: (json['core'] as num?)?.toInt() ?? 1,
    sep: (json['sep'] as num?)?.toInt() ?? 0,
  );

  Map<String, dynamic> toJson() => {
    'count': count,
    'min': min,
    'max': max,
    'core': core,
    'sep': sep,
  };
}

/// 템플릿의 정보단위 설정 (행/열 단위 축).
class TableUnits {
  const TableUnits({this.row, this.col});

  final UnitAxis? row;
  final UnitAxis? col;

  bool get isFixed => row == null && col == null;

  factory TableUnits.fromJson(Map<dynamic, dynamic>? json) {
    if (json == null) return const TableUnits();
    return TableUnits(
      row: json['row'] is Map ? UnitAxis.fromJson(json['row'] as Map) : null,
      col: json['col'] is Map ? UnitAxis.fromJson(json['col'] as Map) : null,
    );
  }
}

/// 표 템플릿 정보.
class TableTemplateInfo {
  const TableTemplateInfo({
    required this.id,
    required this.category,
    required this.name,
    required this.rows,
    required this.cols,
    this.thumbnail,
    this.favorite = false,
    required this.units,
  });

  final String id;
  final String category;
  final String name;
  final int rows;
  final int cols;
  final String? thumbnail;
  final bool favorite;
  final TableUnits units;

  TableTemplateInfo copyWith({
    String? id,
    String? category,
    String? name,
    int? rows,
    int? cols,
    String? thumbnail,
    bool? favorite,
    TableUnits? units,
  }) => TableTemplateInfo(
    id: id ?? this.id,
    category: category ?? this.category,
    name: name ?? this.name,
    rows: rows ?? this.rows,
    cols: cols ?? this.cols,
    thumbnail: thumbnail ?? this.thumbnail,
    favorite: favorite ?? this.favorite,
    units: units ?? this.units,
  );

  factory TableTemplateInfo.fromJson(Map<dynamic, dynamic> json) =>
      TableTemplateInfo(
        id: '${json['id'] ?? ''}',
        category: '${json['category'] ?? '기타'}',
        name: '${json['name'] ?? ''}',
        rows: (json['rows'] as num?)?.toInt() ?? 0,
        cols: (json['cols'] as num?)?.toInt() ?? 0,
        thumbnail: json['thumbnail'] as String?,
        favorite: json['favorite'] == true,
        units: TableUnits.fromJson(json['units'] as Map?),
      );
}

/// 표 템플릿 목록 응답 데이터.
class TableUnitsListData {
  const TableUnitsListData({
    this.source,
    required this.thumbnailsReady,
    this.recent = const [],
    required this.templates,
  });

  final String? source;
  final bool thumbnailsReady;
  final List<String> recent;
  final List<TableTemplateInfo> templates;

  factory TableUnitsListData.fromJson(Map<dynamic, dynamic> json) =>
      TableUnitsListData(
        source: json['source'] as String?,
        thumbnailsReady: json['thumbnails_ready'] == true,
        recent: (json['recent'] as List? ?? const [])
            .map((e) => '$e')
            .toList(),
        templates: (json['templates'] as List? ?? const [])
            .whereType<Map>()
            .map(TableTemplateInfo.fromJson)
            .toList(),
      );
}

/// 셀 한 변의 테두리 설정.
class CellBorderSide {
  const CellBorderSide({
    this.type = 'SOLID',
    this.width = 0.12,
    this.color = '#000000',
  });

  final String type;
  final double width;
  final String color;

  factory CellBorderSide.fromJson(Map<dynamic, dynamic>? json) {
    if (json == null) return const CellBorderSide();
    final rawWidth = json['width'];
    double parsedWidth = 0.12;
    if (rawWidth is num) {
      parsedWidth = rawWidth.toDouble();
    } else if (rawWidth is String) {
      final match = RegExp(r'([0-9.]+)').firstMatch(rawWidth);
      if (match != null) {
        parsedWidth = double.tryParse(match.group(1)!) ?? 0.12;
      }
    }
    return CellBorderSide(
      type: '${json['type'] ?? 'SOLID'}',
      width: parsedWidth,
      color: '${json['color'] ?? '#000000'}',
    );
  }
}

/// 셀 4변의 테두리.
class CellBorders {
  const CellBorders({
    this.top = const CellBorderSide(),
    this.bottom = const CellBorderSide(),
    this.left = const CellBorderSide(),
    this.right = const CellBorderSide(),
  });

  final CellBorderSide top;
  final CellBorderSide bottom;
  final CellBorderSide left;
  final CellBorderSide right;

  factory CellBorders.fromJson(Map<dynamic, dynamic>? json) {
    if (json == null) return const CellBorders();
    return CellBorders(
      top: CellBorderSide.fromJson(json['top'] as Map?),
      bottom: CellBorderSide.fromJson(json['bottom'] as Map?),
      left: CellBorderSide.fromJson(json['left'] as Map?),
      right: CellBorderSide.fromJson(json['right'] as Map?),
    );
  }
}

/// 셀 글자 및 채움 서식.
class CellStyle {
  const CellStyle({
    this.font,
    this.size,
    this.bold = false,
    this.color,
    this.fill,
  });

  final String? font;
  final double? size;
  final bool bold;
  final String? color;
  final String? fill;

  factory CellStyle.fromJson(Map<dynamic, dynamic>? json) {
    if (json == null) return const CellStyle();
    return CellStyle(
      font: json['font'] as String?,
      size: (json['size'] as num?)?.toDouble(),
      bold: json['bold'] == true,
      color: json['color'] as String?,
      fill: json['fill'] as String?,
    );
  }
}

/// 셀 메타데이터 (병합, 크기, 내용, 서식, 글상자 안 nested 표).
class CellMeta {
  const CellMeta({
    required this.row,
    required this.col,
    this.rowSpan = 1,
    this.colSpan = 1,
    this.width = 1.0,
    this.height = 1.0,
    this.text = '',
    this.align = 'left',
    this.style = const CellStyle(),
    this.borders = const CellBorders(),
    this.nested,
  });

  final int row;
  final int col;
  final int rowSpan;
  final int colSpan;
  final double width;
  final double height;
  final String text;
  final String align;
  final CellStyle style;
  final CellBorders borders;
  final List<TablePreview>? nested;

  factory CellMeta.fromJson(Map<dynamic, dynamic> json) {
    final rawNested = json['nested'];
    List<TablePreview>? nested;
    if (rawNested is List) {
      nested = rawNested
          .whereType<Map>()
          .map(TablePreview.fromJson)
          .toList();
    }
    return CellMeta(
      row: (json['row'] as num?)?.toInt() ?? 0,
      col: (json['col'] as num?)?.toInt() ?? 0,
      rowSpan: (json['rowSpan'] as num?)?.toInt() ?? 1,
      colSpan: (json['colSpan'] as num?)?.toInt() ?? 1,
      width: (json['width'] as num?)?.toDouble() ?? 1.0,
      height: (json['height'] as num?)?.toDouble() ?? 1.0,
      text: '${json['text'] ?? ''}',
      align: '${json['align'] ?? 'left'}',
      style: CellStyle.fromJson(json['style'] as Map?),
      borders: CellBorders.fromJson(json['borders'] as Map?),
      nested: nested,
    );
  }
}

/// 표 미리보기 응답 데이터.
class TablePreview {
  const TablePreview({
    required this.rows,
    required this.cols,
    required this.cellMeta,
  });

  final int rows;
  final int cols;
  final List<List<CellMeta>> cellMeta;

  factory TablePreview.fromJson(Map<dynamic, dynamic> json) {
    final rawMeta = json['cell_meta'];
    final List<List<CellMeta>> meta = [];
    if (rawMeta is List) {
      for (final rowItem in rawMeta) {
        if (rowItem is List) {
          meta.add(rowItem.whereType<Map>().map(CellMeta.fromJson).toList());
        }
      }
    }
    return TablePreview(
      rows: (json['rows'] as num?)?.toInt() ?? meta.length,
      cols:
          (json['cols'] as num?)?.toInt() ??
          (meta.isNotEmpty ? meta.first.length : 0),
      cellMeta: meta,
    );
  }
}

/// 표 클립보드 복사 응답 데이터.
class TableCopyResult {
  const TableCopyResult({
    required this.copied,
    required this.message,
    this.activated = false,
  });

  final bool copied;
  final String message;
  final bool activated;

  factory TableCopyResult.fromJson(Map<dynamic, dynamic> json) =>
      TableCopyResult(
        copied: json['copied'] == true,
        message: '${json['message'] ?? ''}',
        activated: json['activated'] == true,
      );
}

/// 표 템플릿 백엔드 API 클라이언트.
class TableUnitsApi {
  const TableUnitsApi(this.call);
  final ApiCall call;

  Future<Map<String, Object?>> _request(
    String action,
    Map<String, Object?> payload,
  ) async {
    final response = await call('table_units', [action, payload]);
    if (response is! Map || response['api_version'] != 1) {
      throw const ServiceApiException(
        'API_VERSION',
        '앱 연결과 버전을 확인해 주세요.',
        true,
      );
    }
    if (response['ok'] != true) {
      final error = response['error'] as Map? ?? {};
      throw ServiceApiException(
        '${error['code'] ?? 'UNKNOWN'}',
        '${error['message'] ?? '표 템플릿 작업을 완료하지 못했어요.'}',
        error['recoverable'] == true,
      );
    }
    final data = response['data'];
    if (data is Map) {
      return data.cast<String, Object?>();
    }
    return const {};
  }

  /// 템플릿 목록 조회.
  Future<TableUnitsListData> list() async {
    final data = await _request('list', const {});
    return TableUnitsListData.fromJson(data);
  }

  /// 한/글로 스냅샷 그림 일괄 생성 후 목록 반환.
  Future<TableUnitsListData> generateThumbnails() async {
    final data = await _request('thumbnails', const {});
    return TableUnitsListData.fromJson(data);
  }

  /// 즐겨찾기 토글.
  Future<TableUnitsListData> favorite(String id, bool on) async {
    final payload = <String, Object?>{
      'id': id,
      'on': on,
    };
    final data = await _request('favorite', payload);
    return TableUnitsListData.fromJson(data);
  }

  /// 정보단위가 조절된 표 구조 미리보기 조회.
  Future<TablePreview> preview(
    String id, {
    int? rowCount,
    int? colCount,
    String fill = 'increment',
    Map<String, String>? cellTexts,
  }) async {
    final payload = <String, Object?>{
      'id': id,
      'row_count': rowCount,
      'col_count': colCount,
      'fill': fill,
      'cell_texts': cellTexts ?? const {},
    };
    final data = await _request('preview', payload);
    return TablePreview.fromJson(data);
  }

  /// 한/글 붙여넣기용 클립보드 복사.
  Future<TableCopyResult> copy(
    String id, {
    int? rowCount,
    int? colCount,
    String fill = 'increment',
    Map<String, String>? cellTexts,
  }) async {
    final payload = <String, Object?>{
      'id': id,
      'row_count': rowCount,
      'col_count': colCount,
      'fill': fill,
      'cell_texts': cellTexts ?? const {},
    };
    final data = await _request('copy', payload);
    return TableCopyResult.fromJson(data);
  }
}
