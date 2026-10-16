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
  });

  final List<AbbreviationEntry> entries;
  final Map<String, String> formats;
  final bool useDefaults, running;

  factory AbbreviationSnapshot.fromJson(Map data) => AbbreviationSnapshot(
        entries: (data['entries'] as List)
            .map((item) => AbbreviationEntry.fromJson(item as Map))
            .toList(),
        formats: Map<String, String>.from(data['format_kinds'] as Map),
        useDefaults: data['use_defaults'] == true,
        running: data['running'] == true,
      );
}
