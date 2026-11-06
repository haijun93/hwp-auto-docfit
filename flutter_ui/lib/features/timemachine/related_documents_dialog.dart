import 'package:flutter/material.dart';
import 'timemachine_api.dart';

/// 연관검색(`related_search`) 결과 대화상자.
///
/// - 기준일(reference_date·precision·basis·evidence)과 못 찾음 표시, 기준일 순 정렬
/// - 연관 근거(related_reasons) 칩, '관련 없음'(related_exclude)·'연관 자료 추가'(related_include)
/// - 정기 문서 계열(series)의 이전·같은 기준일·다음·기준일 없음 묶음
class RelatedDocumentsDialog extends StatefulWidget {
  const RelatedDocumentsDialog({
    super.key,
    required this.api,
    required this.selectedPath,
    required this.selectedName,
    this.candidates = const [],
  });

  final TimemachineApi api;
  final String selectedPath;
  final String selectedName;

  /// '연관 자료 추가'에서 고를 수 있는 문서(현재 타임머신 목록).
  final List<TimemachineItem> candidates;

  @override
  State<RelatedDocumentsDialog> createState() => _RelatedDocumentsDialogState();
}

/// 정렬: 기준일 최신순(서버 기본), 기준일 오래된순, 점수순. 기준일 없는 문서는 항상 뒤.
enum RelatedSort { dateDesc, dateAsc, score }

const _precisionLabels = {'day': '일', 'month': '월', 'quarter': '분기', 'half': '반기', 'year': '연도'};
const _basisLabels = {'explicit': '본문 명시', 'period': '기간 표기'};

String? _dateOf(Map<String, Object?> row) {
  final value = row['reference_date'];
  if (row['reference_date_found'] == false || value is! String || value.isEmpty) return null;
  return value;
}

/// '2026-06-30 (일 단위·본문 명시)' 또는 '기준일 못 찾음'.
String relatedDateLabel(Map<String, Object?> row) {
  final date = _dateOf(row);
  if (date == null) return '기준일 못 찾음';
  final parts = <String>[
    if (_precisionLabels[row['reference_date_precision']] != null) '${_precisionLabels[row['reference_date_precision']]} 단위',
    if (_basisLabels[row['reference_date_basis']] != null) _basisLabels[row['reference_date_basis']]!,
  ];
  return parts.isEmpty ? date : '$date (${parts.join('·')})';
}

/// 근거 문장 목록. related_reasons가 없으면 예전 reasons(문자열 또는 {label})로 대신한다.
List<String> relatedReasonTexts(Map<String, Object?> row) {
  final texts = row['related_reasons'];
  if (texts is List && texts.isNotEmpty) return [for (final t in texts) '$t'];
  final reasons = row['reasons'];
  if (reasons is! List) return const [];
  return [
    for (final r in reasons)
      if (r is Map) '${r['label'] ?? r['type'] ?? ''}' else '$r',
  ].where((t) => t.isNotEmpty).toList();
}

/// 응답 항목에서 문서 경로를 만든다. 서비스는 path 대신 folder를 준다.
String? relatedPathOf(Map<String, Object?> row) {
  final path = row['path'];
  if (path is String && path.isNotEmpty) return path;
  final folder = row['folder'];
  final name = row['name'];
  if (folder is String && folder.isNotEmpty && name is String && name.isNotEmpty) return '$folder\\$name';
  return null;
}

List<Map<String, Object?>> sortRelatedItems(List<Map<String, Object?>> items, RelatedSort sort) {
  final indexed = [for (var i = 0; i < items.length; i++) (i, items[i])];
  int score(Map<String, Object?> row) => (row['score'] as num?)?.toInt() ?? 0;
  indexed.sort((a, b) {
    final da = _dateOf(a.$2), db = _dateOf(b.$2);
    if (sort == RelatedSort.score) {
      final s = score(b.$2).compareTo(score(a.$2));
      return s != 0 ? s : a.$1.compareTo(b.$1);
    }
    if ((da == null) != (db == null)) return da == null ? 1 : -1;
    if (da != null && db != null && da != db) {
      return sort == RelatedSort.dateDesc ? db.compareTo(da) : da.compareTo(db);
    }
    return a.$1.compareTo(b.$1);
  });
  return [for (final e in indexed) e.$2];
}

List<Map<String, Object?>> _rows(Object? raw) => raw is List
    ? raw.whereType<Map>().map((entry) => Map<String, Object?>.from(entry)).toList()
    : <Map<String, Object?>>[];

class _RelatedDocumentsDialogState extends State<RelatedDocumentsDialog> {
  bool _loading = true;
  String? _error;
  Map<String, Object?> _response = const {};
  RelatedSort _sort = RelatedSort.dateDesc;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final response = await widget.api.command('related_search', {'path': widget.selectedPath});
      if (!mounted) return;
      setState(() {
        _loading = false;
        if (response['ok'] == true) {
          _response = response;
        } else {
          _error = '${response['message'] ?? '연관 문서를 찾지 못했습니다.'}';
        }
      });
    } catch (_) {
      if (mounted) {
        setState(() {
          _loading = false;
          _error = '연관 문서를 찾지 못했습니다. 앱 연결을 확인해 주세요.';
        });
      }
    }
  }

  Future<void> _exclude(Map<String, Object?> row) async {
    final path = relatedPathOf(row);
    if (path == null) {
      setState(() => _error = '문서 위치를 알 수 없어 관련 없음으로 표시하지 못했습니다.');
      return;
    }
    try {
      final saved = await widget.api.command('related_exclude', {'selected_path': widget.selectedPath, 'related_path': path});
      if (!mounted) return;
      if (saved['ok'] == true) {
        await _load();
      } else {
        setState(() => _error = '${saved['message'] ?? '관련 없음을 저장하지 못했습니다.'}');
      }
    } catch (_) {
      if (mounted) setState(() => _error = '관련 없음을 저장하지 못했습니다.');
    }
  }

  Future<void> _include() async {
    final listed = {
      for (final row in _rows(_response['items'])) relatedPathOf(row),
    };
    final choices = [
      for (final item in widget.candidates)
        if ('${item.folder}\\${item.name}' != widget.selectedPath && !listed.contains('${item.folder}\\${item.name}')) item,
    ];
    final picked = await showDialog<TimemachineItem>(
      context: context,
      builder: (context) => _IncludePicker(choices: choices),
    );
    if (picked == null || !mounted) return;
    try {
      final saved = await widget.api.command('related_include', {
        'selected_path': widget.selectedPath,
        'related_path': '${picked.folder}\\${picked.name}',
        'included': true,
      });
      if (!mounted) return;
      if (saved['ok'] == true) {
        await _load();
      } else {
        setState(() => _error = '${saved['message'] ?? '연관 자료를 추가하지 못했습니다.'}');
      }
    } catch (_) {
      if (mounted) setState(() => _error = '연관 자료를 추가하지 못했습니다.');
    }
  }

  Widget _dateLine(Map<String, Object?> row, {String subject = ''}) {
    final found = _dateOf(row) != null;
    final evidence = row['reference_date_evidence'];
    final note = row['reference_date_note'];
    final text = found
        ? '$subject기준일 ${relatedDateLabel(row)}${evidence is String && evidence.isNotEmpty ? ' · 근거 “$evidence”' : ''}'
        : '$subject기준일 못 찾음${note is String && note.isNotEmpty ? ' ($note)' : ''}';
    return Text(text, style: found ? null : TextStyle(color: Theme.of(context).colorScheme.error));
  }

  Widget _item(Map<String, Object?> row) {
    final reasons = relatedReasonTexts(row);
    final name = '${row['name'] ?? ''}';
    return Card(
      key: ValueKey('tm-related-item-$name'),
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: Padding(
        padding: const EdgeInsets.all(8),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Expanded(child: Text(name, style: const TextStyle(fontWeight: FontWeight.w600))),
            if (row['user_added'] == true) const Padding(padding: EdgeInsets.only(right: 6), child: Text('직접 추가', style: TextStyle(fontSize: 12))),
            Text('점수 ${row['score'] ?? 0}', style: const TextStyle(fontSize: 12)),
            TextButton(
              key: ValueKey('tm-related-exclude-$name'),
              onPressed: () => _exclude(row),
              child: const Text('관련 없음'),
            ),
          ]),
          _dateLine(row),
          if (reasons.isNotEmpty) Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Wrap(spacing: 4, runSpacing: 4, children: [
              for (final reason in reasons) Chip(
                label: Text(reason, style: const TextStyle(fontSize: 12)),
                visualDensity: VisualDensity.compact,
                materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
            ]),
          ),
        ]),
      ),
    );
  }

  Widget _series() {
    final raw = _response['series'];
    if (raw is! Map) {
      return const Text('같은 계열(정기 문서) 자료를 찾지 못했습니다.', style: TextStyle(fontSize: 12));
    }
    final series = Map<String, Object?>.from(raw);
    final period = series['period'] is Map ? Map<String, Object?>.from(series['period'] as Map) : const <String, Object?>{};
    final groups = [
      ('previous', '이전 기간'),
      ('same', '같은 기준일'),
      ('next', '다음 기간'),
      ('undated', '기준일 없음'),
    ];
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text('정기 문서 계열: ${series['label'] ?? ''}${period['label'] != null ? ' (이 문서 ${period['label']})' : ''} · ${series['total'] ?? 0}건',
          key: const ValueKey('tm-related-series-title'), style: const TextStyle(fontWeight: FontWeight.w600)),
      if (series['reference_date_found'] != true)
        const Text('선택 문서의 기준일이 없어 이전·다음을 나누지 않았습니다.', style: TextStyle(fontSize: 12)),
      for (final (key, label) in groups)
        if (_rows(series[key]).isNotEmpty) Padding(
          key: ValueKey('tm-related-series-$key'),
          padding: const EdgeInsets.only(top: 6),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('$label (${_rows(series[key]).length})', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
            for (final row in _rows(series[key])) Padding(
              padding: const EdgeInsets.only(left: 8, top: 2),
              child: Text('${row['period_label'] ?? ''} · ${row['name'] ?? ''} · ${_dateOf(row) ?? '기준일 못 찾음'}', style: const TextStyle(fontSize: 12)),
            ),
          ]),
        ),
    ]);
  }

  @override
  Widget build(BuildContext context) {
    final items = sortRelatedItems(_rows(_response['items']), _sort);
    return AlertDialog(
      title: const Text('연관 문서'),
      scrollable: true,
      content: SizedBox(
        width: 620,
        child: _loading && _response.isEmpty
            ? const Padding(padding: EdgeInsets.all(24), child: Center(child: CircularProgressIndicator()))
            : Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
                Text(widget.selectedName, style: const TextStyle(fontWeight: FontWeight.w600)),
                _dateLine(_response, subject: '선택 문서 '),
                if (_error != null) Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
                ),
                const SizedBox(height: 8),
                _series(),
                const Divider(height: 20),
                Row(children: [
                  Expanded(child: Text('연관 자료 ${items.length}건', style: const TextStyle(fontWeight: FontWeight.w600))),
                  DropdownButton<RelatedSort>(
                    key: const ValueKey('tm-related-sort'),
                    value: _sort,
                    onChanged: (value) => setState(() => _sort = value ?? _sort),
                    items: const [
                      DropdownMenuItem(value: RelatedSort.dateDesc, child: Text('기준일 최신순')),
                      DropdownMenuItem(value: RelatedSort.dateAsc, child: Text('기준일 오래된순')),
                      DropdownMenuItem(value: RelatedSort.score, child: Text('점수순')),
                    ],
                  ),
                ]),
                if (items.isEmpty) const Text('연관 문서가 없습니다.') else for (final row in items) _item(row),
              ]),
      ),
      actions: [
        TextButton(key: const ValueKey('tm-related-include'), onPressed: _loading ? null : _include, child: const Text('연관 자료 추가')),
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('닫기')),
      ],
    );
  }
}

class _IncludePicker extends StatefulWidget {
  const _IncludePicker({required this.choices});
  final List<TimemachineItem> choices;
  @override
  State<_IncludePicker> createState() => _IncludePickerState();
}

class _IncludePickerState extends State<_IncludePicker> {
  String _filter = '';

  @override
  Widget build(BuildContext context) {
    final needle = _filter.trim().toLowerCase();
    final shown = widget.choices.where((item) => needle.isEmpty || item.name.toLowerCase().contains(needle)).take(100).toList();
    return AlertDialog(
      title: const Text('연관 자료 추가'),
      scrollable: true,
      content: SizedBox(width: 480, child: Column(mainAxisSize: MainAxisSize.min, children: [
        TextField(
          key: const ValueKey('tm-related-include-filter'),
          decoration: const InputDecoration(hintText: '파일명으로 찾기', isDense: true),
          onChanged: (value) => setState(() => _filter = value),
        ),
        const SizedBox(height: 8),
        if (shown.isEmpty) const Text('추가할 수 있는 문서가 없습니다. 타임머신 목록에 있는 문서만 고를 수 있습니다.')
        else for (final item in shown) ListTile(
          key: ValueKey('tm-related-include-${item.id}'),
          dense: true,
          title: Text(item.name),
          subtitle: Text(item.folder, maxLines: 1, overflow: TextOverflow.ellipsis),
          onTap: () => Navigator.pop(context, item),
        ),
      ])),
      actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('취소'))],
    );
  }
}
