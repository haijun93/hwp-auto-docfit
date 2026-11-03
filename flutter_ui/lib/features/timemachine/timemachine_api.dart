import '../../core/api/abbreviation_api.dart' show ApiCall;

int? _safeInt(dynamic v) {
  if (v is num) return v.toInt();
  if (v is String) return int.tryParse(v);
  return null;
}

double _safeDouble(dynamic v, [double fallback = 0.0]) {
  if (v is num) return v.toDouble();
  if (v is String) return double.tryParse(v) ?? fallback;
  return fallback;
}

class TimemachineItem {
  const TimemachineItem({
    required this.id,
    required this.name,
    required this.kind,
    required this.size,
    required this.mtime,
    required this.ctime,
    required this.workTime,
    required this.flags,
    required this.cloud,
    required this.folder,
  });

  final int id;
  final String name, kind, folder;
  final int size;
  final double mtime, ctime, workTime;
  final Set<String> flags;
  final bool cloud;

  factory TimemachineItem.fromJson(Map value) => TimemachineItem(
    id: _safeInt(value['id']) ?? 0,
    name: '${value['name'] ?? ''}',
    kind: '${value['kind'] ?? ''}',
    size: _safeInt(value['size']) ?? 0,
    mtime: _safeDouble(value['mtime']),
    ctime: _safeDouble(value['ctime']),
    workTime: _safeDouble(value['work_time']),
    flags: ((value['flags'] is Iterable) ? value['flags'] as Iterable : const <Object?>[])
        .map((item) => '$item').toSet(),
    cloud: value['cloud'] == true,
    folder: '${value['folder'] ?? ''}',
  );
}

class TimemachineResultPosition {
  const TimemachineResultPosition({this.page, this.sheet, this.row});
  final int? page, row;
  final String? sheet;

  String get badgeLabel {
    if (page != null) return '${page}p';
    if (sheet != null && row != null) return '$sheet $row행';
    if (sheet != null) return sheet!;
    if (row != null) return '$row행';
    return '';
  }
}

class TimemachineContentResult {
  const TimemachineContentResult({
    required this.fileName,
    required this.folderName,
    required this.folderPath,
    required this.snippet,
    required this.matchCounts,
    required this.totalMatches,
    required this.kind,
    required this.size,
    required this.mtime,
    required this.ctime,
    required this.hierarchy,
    required this.hierarchyRank,
    required this.bm25,
    required this.position,
    this.id,
    this.path,
  });

  final int? id;
  final String fileName, folderName, folderPath, snippet, kind, hierarchy;
  final String? path;
  final Map<String, int> matchCounts;
  final int totalMatches, size, hierarchyRank;
  final double mtime, ctime, bm25;
  final TimemachineResultPosition? position;

  factory TimemachineContentResult.fromJson(Map value, {required String query}) {
    final id = _safeInt(value['id']);
    final rawPath = value['path'] != null ? '${value['path']}' : null;

    var fileName = '${value['file_name'] ?? value['name'] ?? ''}';
    if (fileName.isEmpty && rawPath != null && rawPath.isNotEmpty) {
      final sep = rawPath.lastIndexOf(RegExp(r'[/\\]'));
      fileName = sep >= 0 ? rawPath.substring(sep + 1) : rawPath;
    }

    var folderPath = '${value['folder_path'] ?? ''}';
    if (folderPath.isEmpty && rawPath != null && rawPath.isNotEmpty) {
      final sep = rawPath.lastIndexOf(RegExp(r'[/\\]'));
      if (sep > 0) {
        folderPath = rawPath.substring(0, sep);
      }
    }

    var folderName = '${value['folder_name'] ?? ''}';
    if (folderName.isEmpty && folderPath.isNotEmpty) {
      final segs = folderPath.split(RegExp(r'[/\\]')).where((s) => s.isNotEmpty).toList();
      if (segs.isNotEmpty) {
        folderName = segs.last;
      }
    }

    final snippet = '${value['snippet'] ?? ''}';

    final matchCounts = <String, int>{};
    final rawCounts = value['match_counts'];
    if (rawCounts is Map) {
      for (final e in rawCounts.entries) {
        final count = _safeInt(e.value);
        if (count != null) {
          matchCounts['${e.key}'] = count;
        }
      }
    } else {
      final terms = query.trim().split(RegExp(r'\s+')).where((t) => t.isNotEmpty);
      for (final t in terms) {
        final clean = t.replaceAll(RegExp(r'^["\-]'), '').replaceAll(RegExp(r'["~].*$'), '');
        if (clean.isNotEmpty && !clean.contains(':')) {
          matchCounts[clean] = 0;
        }
      }
    }

    final rawTotal = _safeInt(value['total_matches']);
    final totalMatches = rawTotal ?? matchCounts.values.fold<int>(0, (a, b) => a + b);

    final kind = '${value['kind'] ?? ''}';
    final size = _safeInt(value['size']) ?? 0;
    final mtime = _safeDouble(value['mtime']);
    final ctime = _safeDouble(value['ctime']);
    final hierarchy = '${value['hierarchy'] ?? value['highest_hierarchy'] ?? ''}';
    final hierarchyRank = _safeInt(value['hierarchy_rank']) ?? 999999;
    final bm25 = _safeDouble(value['bm25']);

    final page = _safeInt(value['page']) ?? _safeInt(value['page_number']);
    final sheet = value['sheet'] != null ? '${value['sheet']}' : null;
    final row = _safeInt(value['row']);
    TimemachineResultPosition? pos;
    if (page != null || sheet != null || row != null) {
      pos = TimemachineResultPosition(page: page, sheet: sheet, row: row);
    }

    return TimemachineContentResult(
      id: id,
      path: rawPath,
      fileName: fileName,
      folderName: folderName,
      folderPath: folderPath,
      snippet: snippet,
      matchCounts: matchCounts,
      totalMatches: totalMatches,
      kind: kind,
      size: size,
      mtime: mtime,
      ctime: ctime,
      hierarchy: hierarchy,
      hierarchyRank: hierarchyRank,
      bm25: bm25,
      position: pos,
    );
  }
}

class TimemachineHourDensity {
  const TimemachineHourDensity(this.counts);
  final Map<int, int> counts; // 빠진 0~23은 0
  factory TimemachineHourDensity.fromJson(Map value) {
    final raw = value['hours'];
    final counts = <int, int>{for (var i = 0; i < 24; i++) i: 0};
    if (raw is Map) {
      for (final entry in raw.entries) {
        final h = int.tryParse('${entry.key}');
        final c = _safeInt(entry.value);
        if (h != null && h >= 0 && h < 24 && c != null) {
          counts[h] = c;
        }
      }
    }
    return TimemachineHourDensity(counts);
  }
}

class TimemachineApi {
  const TimemachineApi(this.call);
  final ApiCall call;

  Future<Map<String, Object?>> command(String action, [Map<String, Object?> payload = const {}]) async {
    final value = await call('timemachine', [action, payload]);
    if (value is Map) {
      final result = <String, Object?>{};
      for (final entry in value.entries) {
        if (entry.key is String) result[entry.key as String] = entry.value;
      }
      return result;
    }
    return {'ok': false, 'code': 'TM_RESPONSE', 'message': '타임머신 응답을 읽지 못했습니다.'};
  }

  Future<List<TimemachineContentResult>> contentSearch(
    String query, {
    int limit = 100,
    String sort = 'hierarchy_relevance',
  }) async {
    final response = await command('content_search', {
      'query': query,
      'limit': limit,
      'sort': sort,
    });
    if (response['ok'] == false) {
      throw Exception(response['message'] ?? '본문 검색에 실패했습니다.');
    }
    final raw = response['items'];
    if (raw is! List) return [];
    final results = <TimemachineContentResult>[];
    for (final item in raw) {
      if (item is Map) {
        try {
          results.add(TimemachineContentResult.fromJson(item, query: query));
        } catch (_) {
          // 파싱 실패 항목 하나로 전체 응답을 폐기하지 않는다.
        }
      }
    }
    return results;
  }

  Future<List<TimemachineItem>> fileSearch(
    String query, {
    int limit = 200,
    List<String>? kinds,
    List<String>? roots,
  }) async {
    final payload = <String, Object?>{
      'query': query,
      'limit': limit,
      'kinds': ?kinds,
      'roots': ?roots,
    };
    final response = await command('file_search', payload);
    if (response['ok'] != true) {
      throw Exception(response['message'] ?? '파일 검색에 실패했습니다.');
    }
    final raw = response['items'];
    if (raw is! List) return [];
    final results = <TimemachineItem>[];
    for (final entry in raw) {
      if (entry is Map) {
        try {
          results.add(TimemachineItem.fromJson(entry));
        } catch (_) {}
      }
    }
    return results;
  }

  Future<TimemachineHourDensity> hourDensity(Map<String, Object?> payload) async {
    final response = await command('hour_density', payload);
    return TimemachineHourDensity.fromJson(response);
  }

  Future<Map<String, Object?>> sendToFeature(String feature, List<int> ids) =>
      command('send_to_feature', {'feature': feature, 'ids': ids});

  Future<Map<String, Object?>> clearThumbnailCache() =>
      command('thumbnail_cache_clear');
}
