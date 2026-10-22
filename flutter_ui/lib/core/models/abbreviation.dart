class AbbreviationEntry {
  const AbbreviationEntry({
    required this.key,
    required this.type,
    required this.value,
    required this.label,
    required this.builtin,
  });

  final String key, type, value, label;
  final bool builtin;

  factory AbbreviationEntry.fromJson(Map data) => AbbreviationEntry(
    key: data['key'] as String,
    type: data['type'] as String,
    value: data['value'] as String,
    label: data['label'] as String,
    builtin: data['builtin'] == true,
  );
}

class AbbreviationSnapshot {
  const AbbreviationSnapshot({
    required this.entries,
    required this.formats,
    required this.useDefaults,
    required this.running,
    this.source = 'settings',
    this.documentPath = '',
    this.documentExists = false,
    this.documentErrors = const [],
  });

  final List<AbbreviationEntry> entries;
  final Map<String, String> formats;
  final bool useDefaults, running;

  /// 준말 출처: 'document'(준말 관리 HWPX 문서) 또는 'settings'(앱 설정).
  final String source;
  final String documentPath;
  final bool documentExists;
  final List<String> documentErrors;

  bool get usesDocument => source == 'document';

  factory AbbreviationSnapshot.fromJson(Map data) => AbbreviationSnapshot(
    entries: (data['entries'] as List)
        .map((item) => AbbreviationEntry.fromJson(item as Map))
        .toList(),
    formats: Map<String, String>.from(data['format_kinds'] as Map),
    useDefaults: data['use_defaults'] == true,
    running: data['running'] == true,
    source: data['source'] == 'document' ? 'document' : 'settings',
    documentPath: '${(data['document'] as Map?)?['path'] ?? ''}',
    documentExists: (data['document'] as Map?)?['exists'] == true,
    documentErrors: [
      for (final item in (data['document'] as Map?)?['errors'] as List? ?? [])
        '$item',
    ],
  );
}
