import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:file_selector/file_selector.dart';

import '../../core/api/abbreviation_api.dart' show ApiCall;
import '../../core/drop_events.dart';
import 'file_rename_api.dart';
import 'rule_editor.dart';

class _ApplyIntent extends Intent {
  const _ApplyIntent();
}

class _UndoIntent extends Intent {
  const _UndoIntent();
}

class _AddIntent extends Intent {
  const _AddIntent();
}

class _ClearIntent extends Intent {
  const _ClearIntent();
}

/// 파일이름 탭: 파일을 모아 접두사·접미사·글자 바꾸기·날짜로 새 이름을 미리 보고, 적용·되돌리기.
/// 세부 규칙은 '고급 기능'에 둔다.
class FileRenameScreen extends StatefulWidget {
  const FileRenameScreen({super.key, required this.api});

  final ApiCall api;

  @override
  State<FileRenameScreen> createState() => FileRenameScreenState();
}

class FileRenameScreenState extends State<FileRenameScreen> {
  bool _mruLoaded = false;
  late final FileRenameApi _api = FileRenameApi(widget.api);
  List<RenameEntry> _entries = const [];
  final List<Map<String, Object?>> _rules = [];
  List<Map<String, Object?>> _replaceMru = [];
  final Map<String, String> _overrides = {};
  final Set<String> _excluded = {};
  Map<String, RenamePreviewItem> _preview = const {};
  Map<String, Object?> _summary = const {};
  String? _planId;
  String? _selected;
  String _message = '';
  bool _busy = false;
  bool _recursive = false;
  /// 바뀌는 항목만 보이기(PowerRename '바뀐 항목만 표시').
  bool _onlyChanged = false;
  /// 이름이 겹칠 때: block(적용 막기) · number(' (2)'를 붙여 피하기).
  String _onConflict = 'block';
  String? _lastRun;
  Timer? _debounce;
  void Function()? _stopDrops;
  // 쉬운 일괄변경: 입력한 항목만 적용한다.
  final _prefix = TextEditingController();
  final _suffix = TextEditingController();
  final _find = TextEditingController();
  final _replaceTo = TextEditingController();
  /// none · prefix · suffix
  String _datePosition = 'none';
  String _dateFormat = 'YYYY.MM.DD.';
  bool _advanced = false;
  /// 넓은 창: 오른쪽 입력 칸의 폭 비율. 좁은 창: 위쪽 목록의 높이 비율. 끌어서 바꾼다.
  double _sideFraction = 0.34;
  double _listFraction = 0.5;

  @override
  void initState() {
    super.initState();
    _stopDrops = watchWindowEvent('docfit-rename-files-dropped', () => unawaited(_refreshList()));
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // 시작 때 호출을 늘리지 않으려 탭이 처음 보일 때 불러온다.
    if (!_mruLoaded && TickerMode.valuesOf(context).enabled) {
      _mruLoaded = true;
      unawaited(_loadReplaceMru());
    }
  }

  Future<void> _loadReplaceMru() async {
    final result = await _api.command('replace_mru_list');
    if (!mounted || !result.ok) return;
    setState(() => _replaceMru = [
      for (final value in (result.raw['values'] as List? ?? const []))
        Map<String, Object?>.from(value as Map),
    ]);
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _stopDrops?.call();
    for (final c in [_prefix, _suffix, _find, _replaceTo]) {
      c.dispose();
    }
    super.dispose();
  }

  void _take(RenameResult result, {String? success}) {
    if (!mounted) return;
    setState(() {
      if (result.entries != null) {
        _entries = result.entries!;
        final ids = {for (final e in _entries) e.id};
        _overrides.removeWhere((k, _) => !ids.contains(k));
        _excluded.removeWhere((k) => !ids.contains(k));
        if (_selected != null && !ids.contains(_selected)) _selected = null;
      }
      _message = result.ok ? (success ?? _message) : result.message;
    });
    _schedulePreview();
  }

  Future<void> _run(String action, [Map<String, Object?>? payload, String? success]) async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      final result = await _api.command(action, payload);
      _take(result, success: success ?? _addedMessage(result));
    } catch (error) {
      if (mounted) setState(() => _message = '$error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  String? _addedMessage(RenameResult result) {
    final added = result.raw['added'];
    if (added is! num) return null;
    final skipped = (result.raw['skipped_count'] as num?)?.toInt() ?? 0;
    return '${added.toInt()}개 추가${skipped > 0 ? ' · $skipped개 제외' : ''}';
  }

  Future<void> _refreshList() => _run('list');

  void _schedulePreview() {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 150), () => unawaited(_runPreview()));
  }

  Future<void> _runPreview() async {
    if (_entries.isEmpty) {
      if (mounted) {
        setState(() {
          _preview = const {};
          _summary = const {};
          _planId = null;
        });
      }
      return;
    }
    final result = await _api.command('preview', {
      'rules': [..._simpleRules(), ..._rules],
      'overrides': _overrides,
      'excluded': _excluded.toList(),
      'on_conflict': _onConflict,
    });
    if (!mounted) return;
    setState(() {
      if (!result.ok) {
        _planId = null;
        _preview = const {};
        _summary = const {};
        _message = result.message;
        return;
      }
      _planId = '${result.raw['plan_id']}';
      _preview = {
        for (final item in result.raw['items'] as List)
          '${(item as Map)['id']}': RenamePreviewItem.fromJson(item),
      };
      _summary = Map<String, Object?>.from(result.raw['summary'] as Map);
    });
  }

  /// 쉬운 입력을 규칙으로 바꾼다. 교체 → 접두사 → 접미사 → 날짜 순서이며 비어 있으면 뺀다.
  List<Map<String, Object?>> _simpleRules() => [
    if (_find.text.isNotEmpty) {'kind': 'replace', 'find': _find.text, 'to': _replaceTo.text},
    if (_prefix.text.isNotEmpty) {'kind': 'add', 'text': _prefix.text, 'position': 'prefix', 'sep': ''},
    if (_suffix.text.isNotEmpty) {'kind': 'add', 'text': _suffix.text, 'position': 'suffix', 'sep': ''},
    if (_datePosition != 'none')
      {
        'kind': 'date',
        'source': 'today',
        // 접미사는 확장자 앞에 오므로 끝 마침표를 빼야 '..hwpx'가 되지 않는다.
        'format': _datePosition == 'suffix' && _dateFormat.endsWith('.')
            ? _dateFormat.substring(0, _dateFormat.length - 1)
            : _dateFormat,
        'position': _datePosition,
        'sep': '',
      },
  ];

  void _clearSimple() {
    for (final c in [_prefix, _suffix, _find, _replaceTo]) {
      c.clear();
    }
    _datePosition = 'none';
  }

  int _count(String key) => (_summary[key] as num?)?.toInt() ?? 0;

  bool get _canApply =>
      !_busy && _planId != null && _count('ok') > 0 && _count('conflict') == 0 && _count('invalid') == 0;

  Future<void> _apply() async {
    if (!_canApply) return;
    final executables = _count('executables');
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('이름을 바꿀까요?'),
        content: Text(
          '${_count('ok')}개 파일의 이름을 바꿉니다. 파일 내용은 바뀌지 않으며 되돌리기로 원래 이름을 찾을 수 있습니다.'
          '${executables > 0 ? '\n\n실행 파일(.exe·.bat 등) $executables개가 들어 있습니다. 이름이 바뀌면 바로가기·프로그램이 찾지 못할 수 있습니다.' : ''}',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('취소')),
          FilledButton(
            key: const ValueKey('rename-confirm'),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('바꾸기'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    setState(() => _busy = true);
    try {
      final result = await _api.command('apply', {
        'plan_id': _planId,
        'confirm_executables': executables > 0,
      });
      if (result.ok) {
        _overrides.clear();
        _clearSimple(); // 그대로 두면 바뀐 이름에 같은 글자가 또 붙는다.
        _lastRun = '${result.raw['run_id']}';
      }
      final failed = (result.raw['failed'] as List?) ?? const [];
      _take(
        result,
        success: '${result.raw['done']}개 바꿈'
            '${failed.isNotEmpty ? ' · ${failed.length}개 실패: ${(failed.first as Map)['reason']}' : ''}',
      );
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _undo([String? runId]) async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      final result = await _api.command('undo', {'run_id': ?(runId ?? _lastRun)});
      if (result.ok && (runId == null || runId == _lastRun)) _lastRun = null;
      _take(result, success: '${result.raw['done']}개 원래 이름으로');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _showHistory() async {
    final result = await _api.command('history', {'limit': 20});
    if (!mounted) return;
    final runs = (result.raw['runs'] as List?) ?? const [];
    final chosen = await showDialog<String>(
      context: context,
      builder: (context) => SimpleDialog(
        title: const Text('이름 바꾼 기록'),
        children: [
          if (runs.isEmpty) const Padding(padding: EdgeInsets.all(16), child: Text('기록이 없습니다.')),
          for (final run in runs.cast<Map>())
            SimpleDialogOption(
              onPressed: run['kind'] == 'apply' && run['undone'] != true
                  ? () => Navigator.pop(context, '${run['id']}')
                  : null,
              child: Text(
                '${_when(run['when'])} · ${run['kind'] == 'undo' ? '되돌림' : '바꿈'} ${run['count']}개'
                ' (${run['first_name']}${(run['count'] as num? ?? 0) > 1 ? ' 등' : ''})'
                '${run['undone'] == true ? ' · 되돌린 기록' : ''}',
              ),
            ),
        ],
      ),
    );
    if (chosen != null) await _undo(chosen);
  }

  String _when(Object? seconds) {
    if (seconds is! num) return '';
    final t = DateTime.fromMillisecondsSinceEpoch((seconds * 1000).round());
    String two(int v) => v.toString().padLeft(2, '0');
    return '${t.month}/${t.day} ${two(t.hour)}:${two(t.minute)}';
  }

  // ── 규칙 ──────────────────────────────────────────────────────────────
  Future<void> _addRule(RuleKind kind) async {
    final rule = <String, Object?>{'kind': kind.kind, ...kind.defaults};
    final edited = kind.defaults.isEmpty ? rule : await showRuleEditor(context, rule, mru: _replaceMru);
    if (edited == null || !mounted) return;
    setState(() => _rules.add(edited));
    if (edited['kind'] == 'replace') {
      final result = await _api.command('replace_mru_add', {'find': edited['find'] ?? '', 'to': edited['to'] ?? ''});
      _replaceMru = [for (final v in (result.raw['values'] as List? ?? const [])) Map<String, Object?>.from(v as Map)];
    }
    _schedulePreview();
  }

  Future<void> _editRule(int index) async {
    final edited = await showRuleEditor(context, _rules[index], mru: _replaceMru);
    if (edited == null || !mounted) return;
    setState(() => _rules[index] = edited);
    if (edited['kind'] == 'replace') {
      final result = await _api.command('replace_mru_add', {'find': edited['find'] ?? '', 'to': edited['to'] ?? ''});
      _replaceMru = [for (final v in (result.raw['values'] as List? ?? const [])) Map<String, Object?>.from(v as Map)];
    }
    _schedulePreview();
  }

  void _moveRule(int index, int delta) {
    final target = index + delta;
    if (target < 0 || target >= _rules.length) return;
    setState(() {
      final rule = _rules.removeAt(index);
      _rules.insert(target, rule);
    });
    _schedulePreview();
  }

  Future<void> _rulesetMenu(String action) async {
    if (action == 'export' || action == 'import') {
      if (action == 'export') {
        final list = await _api.command('ruleset_list');
        if (!mounted) return;
        final sets = ((list.raw['rulesets'] as List?) ?? const []).cast<Map>();
        final selected = await showDialog<Map>(context: context, builder: (context) => SimpleDialog(
          title: const Text('내보낼 규칙 세트'),
          children: [for (final item in sets) SimpleDialogOption(onPressed: () => Navigator.pop(context, item), child: Text('${item['name']}'))],
        ));
        if (selected == null || !mounted) return;
        final result = await _api.command('ruleset_export', {'name': selected['name']});
        if (!result.ok) { setState(() => _message = result.message); return; }
        final location = await getSaveLocation(suggestedName: '${selected['name']}.json', acceptedTypeGroups: const [XTypeGroup(label: 'JSON', extensions: ['json'])]);
        if (location == null) return;
        await XFile.fromData(utf8.encode('${result.raw['json']}'), mimeType: 'application/json').saveTo(location.path);
        if (mounted) setState(() => _message = '규칙 JSON을 내보냈습니다.');
        return;
      }
      final file = await openFile(acceptedTypeGroups: const [XTypeGroup(label: 'JSON', extensions: ['json'])]);
      if (file == null || !mounted) return;
      final raw = await file.readAsString();
      final result = await _api.command('ruleset_import', {'json': raw});
      if (mounted) setState(() => _message = result.ok ? '규칙 세트를 가져왔습니다.' : result.message);
      return;
    }
    if (action == 'save') {
      final controller = TextEditingController();
      final name = await showDialog<String>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('규칙 세트 저장'),
          content: TextField(
            controller: controller,
            autofocus: true,
            decoration: const InputDecoration(labelText: '이름'),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('취소')),
            FilledButton(onPressed: () => Navigator.pop(context, controller.text.trim()), child: const Text('저장')),
          ],
        ),
      );
      controller.dispose();
      if (name == null || name.isEmpty) return;
      final result = await _api.command('ruleset_save', {'name': name, 'rules': _rules});
      if (mounted) setState(() => _message = result.ok ? "'$name' 저장" : result.message);
      return;
    }
    final result = await _api.command('ruleset_list');
    if (!mounted) return;
    final sets = ((result.raw['rulesets'] as List?) ?? const []).cast<Map>();
    final chosen = await showDialog<Map>(
      context: context,
      builder: (context) => SimpleDialog(
        title: const Text('규칙 세트 불러오기'),
        children: [
          for (final set in sets)
            SimpleDialogOption(onPressed: () => Navigator.pop(context, set), child: Text('${set['name']}')),
        ],
      ),
    );
    if (chosen == null || !mounted) return;
    setState(() {
      _rules
        ..clear()
        ..addAll([for (final r in (chosen['rules'] as List)) Map<String, Object?>.from(r as Map)]);
    });
    _schedulePreview();
  }

  Future<void> _editName(RenameEntry entry) async {
    final current = _overrides[entry.id] ?? _preview[entry.id]?.newName ?? entry.name;
    final controller = TextEditingController(text: current);
    final result = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('새 이름 직접 고치기 · ${entry.name}'),
        content: TextField(controller: controller, autofocus: true),
        actions: [
          if (_overrides.containsKey(entry.id))
            TextButton(onPressed: () => Navigator.pop(context, ''), child: const Text('규칙 결과로')),
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('취소')),
          FilledButton(onPressed: () => Navigator.pop(context, controller.text), child: const Text('확인')),
        ],
      ),
    );
    controller.dispose();
    if (result == null || !mounted) return;
    setState(() => result.isEmpty ? _overrides.remove(entry.id) : _overrides[entry.id] = result);
    _schedulePreview();
  }

  // ── 화면 ──────────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return Shortcuts(
      shortcuts: const {
        SingleActivator(LogicalKeyboardKey.keyS, control: true): _ApplyIntent(),
        SingleActivator(LogicalKeyboardKey.keyZ, control: true): _UndoIntent(),
        SingleActivator(LogicalKeyboardKey.keyO, control: true): _AddIntent(),
        SingleActivator(LogicalKeyboardKey.keyL, control: true): _ClearIntent(),
      },
      child: Actions(
        actions: {
          _ApplyIntent: CallbackAction(onInvoke: (_) => _apply()),
          _UndoIntent: CallbackAction(onInvoke: (_) => _lastRun == null ? null : _undo()),
          _AddIntent: CallbackAction(onInvoke: (_) => _run('pick_files')),
          _ClearIntent: CallbackAction(onInvoke: (_) => _run('clear', null, '목록을 비웠습니다')),
        },
        child: Focus(
          autofocus: false,
          child: LayoutBuilder(
            builder: (context, constraints) {
              final wide = constraints.maxWidth >= 720;
              final list = _buildList(context);
              final rules = _advanced ? _buildRules(context) : _buildSimple(context);
              return Column(
                children: [
                  _buildToolbar(context),
                  const Divider(height: 1),
                  Expanded(
                    child: LayoutBuilder(
                      builder: (context, area) => wide
                          ? _splitRow(area.maxWidth, list, rules)
                          : _splitColumn(area.maxHeight, list, rules),
                    ),
                  ),
                  const Divider(height: 1),
                  _buildFooter(context),
                ],
              );
            },
          ),
        ),
      ),
    );
  }

  /// 비율로 칸 크기를 정해 창 크기를 따라가고, 양쪽 최소 크기는 지킨다.
  static double _clampSize(double size, double total, double minA, double minB) {
    final top = total - minB;
    if (top <= minA) return total / 2;
    return size.clamp(minA, top).toDouble();
  }

  Widget _splitRow(double width, Widget list, Widget side) {
    const handle = 8.0;
    final available = width - handle;
    final sideWidth = _clampSize(available * _sideFraction, available, 280, 280);
    return Row(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Expanded(child: list),
        MouseRegion(
          cursor: SystemMouseCursors.resizeColumn,
          child: GestureDetector(
            key: const ValueKey('rename-split-side'),
            behavior: HitTestBehavior.opaque,
            onHorizontalDragUpdate: (d) => setState(() {
              _sideFraction = _clampSize(sideWidth - d.delta.dx, available, 280, 280) / available;
            }),
            child: const SizedBox(width: handle, child: VerticalDivider(width: handle)),
          ),
        ),
        SizedBox(width: sideWidth, child: side),
      ],
    );
  }

  Widget _splitColumn(double height, Widget list, Widget side) {
    const handle = 8.0;
    final available = height - handle;
    final listHeight = _clampSize(available * _listFraction, available, 120, 160);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SizedBox(height: listHeight, child: list),
        MouseRegion(
          cursor: SystemMouseCursors.resizeRow,
          child: GestureDetector(
            key: const ValueKey('rename-split-list'),
            behavior: HitTestBehavior.opaque,
            onVerticalDragUpdate: (d) => setState(() {
              _listFraction = _clampSize(listHeight + d.delta.dy, available, 120, 160) / available;
            }),
            child: const SizedBox(height: handle, child: Divider(height: handle)),
          ),
        ),
        Expanded(child: side),
      ],
    );
  }

  Widget _buildToolbar(BuildContext context) {
    final selectedIndex = _selected == null ? -1 : _entries.indexWhere((e) => e.id == _selected);
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
      child: Row(
        children: [
          FilledButton.tonalIcon(
            key: const ValueKey('rename-add-files'),
            onPressed: _busy ? null : () => _run('pick_files'),
            icon: const Icon(Icons.note_add_outlined),
            label: const Text('파일 추가'),
          ),
          const SizedBox(width: 6),
          OutlinedButton.icon(
            onPressed: _busy ? null : () => _run('pick_folder', {'recursive': _recursive}),
            icon: const Icon(Icons.create_new_folder_outlined),
            label: const Text('폴더 추가'),
          ),
          Checkbox(
            value: _recursive,
            onChanged: (v) => setState(() => _recursive = v == true),
          ),
          const Text('하위 폴더 포함'),
          if (_advanced) OutlinedButton.icon(
            key: const ValueKey('rename-folder-self'),
            onPressed: _busy ? null : () => _run('pick_folder', {'as_folder': true}),
            icon: const Icon(Icons.drive_file_rename_outline),
            label: const Text('폴더 자체 이름 바꾸기'),
          ),
          const SizedBox(width: 8),
          OutlinedButton.icon(
            onPressed: _busy || _entries.isEmpty ? null : () => _run('clear', null, '목록을 비웠습니다'),
            icon: const Icon(Icons.clear_all),
            label: const Text('목록 지우기'),
          ),
          const SizedBox(width: 6),
          if (_advanced) ...[
          PopupMenuButton<String>(
            tooltip: '정렬',
            enabled: !_busy && _entries.length > 1,
            onSelected: (v) {
              final parts = v.split(':');
              _run('sort', {'key': parts[0], 'reverse': parts[1] == 'desc'});
            },
            itemBuilder: (_) => const [
              PopupMenuItem(value: 'name:asc', child: Text('이름 순')),
              PopupMenuItem(value: 'name:desc', child: Text('이름 거꾸로')),
              PopupMenuItem(value: 'mtime:asc', child: Text('수정한 날 오래된 순')),
              PopupMenuItem(value: 'mtime:desc', child: Text('수정한 날 최근 순')),
              PopupMenuItem(value: 'ctime:asc', child: Text('만든 날 순')),
              PopupMenuItem(value: 'size:asc', child: Text('크기 순')),
              PopupMenuItem(value: 'path:asc', child: Text('폴더 경로 순')),
            ],
            child: const Padding(
              padding: EdgeInsets.symmetric(horizontal: 8),
              child: Row(children: [Icon(Icons.sort), SizedBox(width: 4), Text('정렬')]),
            ),
          ),
          IconButton(
            tooltip: '위로 (<)',
            onPressed: selectedIndex > 0 ? () => _run('move', {'ids': [_selected], 'delta': -1}) : null,
            icon: const Icon(Icons.arrow_upward),
          ),
          IconButton(
            tooltip: '아래로 (>)',
            onPressed: selectedIndex >= 0 && selectedIndex < _entries.length - 1
                ? () => _run('move', {'ids': [_selected], 'delta': 1})
                : null,
            icon: const Icon(Icons.arrow_downward),
          ),
          IconButton(
            tooltip: '목록에서 빼기',
            onPressed: _selected == null ? null : () => _run('remove', {'ids': [_selected]}),
            icon: const Icon(Icons.playlist_remove),
          ),
          ],
          const SizedBox(width: 8),
          OutlinedButton.icon(
            key: const ValueKey('rename-undo'),
            onPressed: _busy || _lastRun == null ? null : () => _undo(),
            icon: const Icon(Icons.undo),
            label: const Text('되돌리기'),
          ),
          if (_advanced) IconButton(
            tooltip: '이름 바꾼 기록',
            onPressed: _busy ? null : _showHistory,
            icon: const Icon(Icons.history),
          ),
        ],
      ),
    );
  }

  Widget _status(RenamePreviewItem? item) {
    final scheme = Theme.of(context).colorScheme;
    final (IconData icon, Color color, String label) = switch (item?.status) {
      'ok' => (Icons.check_circle_outline, scheme.primary, '바뀜'),
      'unchanged' => (Icons.remove, scheme.outline, '그대로'),
      'conflict' => (Icons.error_outline, scheme.error, '충돌'),
      'invalid' => (Icons.block, scheme.error, '오류'),
      'skipped' => (Icons.do_not_disturb_on_outlined, scheme.outline, '제외'),
      _ => (Icons.hourglass_empty, scheme.outline, ''),
    };
    final warn = item?.warnings ?? const [];
    final tip = [
      ?item?.reason,
      if (warn.contains('executable')) '실행 파일입니다.',
      if (warn.contains('ext_changed')) '확장자가 바뀌어도 파일 형식은 바뀌지 않습니다.',
      if (warn.contains('names_short')) '목록에 이 순서의 새 이름이 없어 그대로 둡니다.',
      if (warn.contains('auto_numbered')) '이름이 겹쳐 번호를 붙였습니다.',
      if (warn.contains('exif_missing')) '촬영일이 없어 수정한 날을 썼습니다.',
      if (warn.contains('long_path')) '경로가 260자를 넘습니다.',
    ].join('\n');
    return Tooltip(
      message: tip.isEmpty ? label : tip,
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: color),
          const SizedBox(width: 2),
          Text(label, style: TextStyle(color: color, fontSize: 12)),
          if (warn.isNotEmpty) Icon(Icons.warning_amber, size: 14, color: scheme.tertiary),
        ],
      ),
    );
  }

  /// 원래·새 이름 목록을 탭으로 나눠 클립보드에(엑셀에 붙여 넣어 고친 뒤 '이름 목록 붙여넣기'로 되돌릴 수 있다).
  Future<void> _copyNameList() async {
    final lines = [
      '원래 이름\t새 이름',
      for (final e in _entries) '${e.name}\t${_preview[e.id]?.newName ?? e.name}',
    ];
    await Clipboard.setData(ClipboardData(text: lines.join('\n')));
    if (mounted) setState(() => _message = '${_entries.length}개 이름 목록을 복사했습니다');
  }

  /// 새 이름에서 원래 이름과 달라진 가운데 부분만 색으로 강조한다.
  Widget _highlighted(String before, String after, {required bool changed, required bool italic}) {
    final style = TextStyle(fontWeight: changed ? FontWeight.w600 : null, fontStyle: italic ? FontStyle.italic : null);
    if (!changed || after.isEmpty) {
      return Text(after, overflow: TextOverflow.ellipsis, style: style);
    }
    var start = 0;
    while (start < before.length && start < after.length && before[start] == after[start]) {
      start++;
    }
    var end = 0;
    while (end < before.length - start && end < after.length - start &&
        before[before.length - 1 - end] == after[after.length - 1 - end]) {
      end++;
    }
    final scheme = Theme.of(context).colorScheme;
    return Text.rich(
      TextSpan(
        style: style,
        children: [
          TextSpan(text: after.substring(0, start)),
          TextSpan(
            text: after.substring(start, after.length - end),
            style: TextStyle(backgroundColor: scheme.primaryContainer, color: scheme.onPrimaryContainer),
          ),
          TextSpan(text: after.substring(after.length - end)),
        ],
      ),
      key: ValueKey('rename-new-${after.hashCode}'),
      overflow: TextOverflow.ellipsis,
    );
  }

  Widget _buildList(BuildContext context) {
    if (_entries.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.drive_file_rename_outline, size: 48, color: Theme.of(context).colorScheme.outline),
              const SizedBox(height: 12),
              const Text('여기에 파일이나 폴더를 끌어다 놓거나 [파일 추가]를 누르세요.', textAlign: TextAlign.center),
              const SizedBox(height: 4),
              const Text('오른쪽에 넣을 글자를 적으면 바뀔 이름을 바로 보여 줍니다. [변경 적용]을 눌러야 실제로 바뀝니다.',
                  textAlign: TextAlign.center, style: TextStyle(fontSize: 12)),
            ],
          ),
        ),
      );
    }
    final header = Theme.of(context).textTheme.labelMedium;
    final visible = _onlyChanged
        ? [for (final e in _entries) if (_preview[e.id] != null && _preview[e.id]!.status != 'unchanged') e]
        : _entries;
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(8, 6, 8, 6),
          child: Column(
            children: [
              if (_advanced) Wrap(
                spacing: 8,
                runSpacing: 4,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  FilterChip(
                    key: const ValueKey('rename-only-changed'),
                    label: const Text('바뀌는 것만 보기'),
                    selected: _onlyChanged,
                    onSelected: (v) => setState(() => _onlyChanged = v),
                  ),
                  DropdownButton<String>(
                    key: const ValueKey('rename-on-conflict'),
                    value: _onConflict,
                    items: const [
                      DropdownMenuItem(value: 'block', child: Text('이름이 겹치면 적용 막기')),
                      DropdownMenuItem(value: 'number', child: Text('이름이 겹치면 (2)·(3) 붙이기')),
                    ],
                    onChanged: (v) {
                      setState(() => _onConflict = v ?? 'block');
                      _schedulePreview();
                    },
                  ),
                  TextButton.icon(
                    key: const ValueKey('rename-copy-list'),
                    onPressed: _copyNameList,
                    icon: const Icon(Icons.copy_all, size: 18),
                    label: const Text('이름 목록 복사'),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Row(
                children: [
                  const SizedBox(width: 40),
                  Expanded(child: Text('원래 이름', style: header)),
                  Expanded(child: Text('새 이름 (바뀐 부분 강조 · 두 번 눌러 직접 고치기)', style: header)),
                  SizedBox(width: 80, child: Text('상태', style: header)),
                ],
              ),
            ],
          ),
        ),
        const Divider(height: 1),
        Expanded(
          child: ListView.builder(
            itemCount: visible.length,
            itemExtent: 36,
            itemBuilder: (context, index) {
              final entry = visible[index];
              final item = _preview[entry.id];
              final selected = entry.id == _selected;
              final changed = item?.status == 'ok';
              return Material(
                color: selected ? Theme.of(context).colorScheme.secondaryContainer : null,
                child: InkWell(
                  key: ValueKey('rename-row-${entry.id}'),
                  onTap: () => setState(() => _selected = selected ? null : entry.id),
                  onDoubleTap: () => _editName(entry),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 8),
                    child: Row(
                      children: [
                        SizedBox(
                          width: 40,
                          child: Checkbox(
                            value: !_excluded.contains(entry.id),
                            onChanged: (v) {
                              setState(() => v == true ? _excluded.remove(entry.id) : _excluded.add(entry.id));
                              _schedulePreview();
                            },
                          ),
                        ),
                        Expanded(
                          child: Tooltip(
                            message: entry.folder,
                            child: Text(entry.name, overflow: TextOverflow.ellipsis),
                          ),
                        ),
                        Expanded(
                          child: _highlighted(
                            entry.name,
                            item?.newName ?? '',
                            changed: changed,
                            italic: item?.overridden == true,
                          ),
                        ),
                        SizedBox(width: 80, child: _status(item)),
                      ],
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  /// 항목 제목. 입력이 있으면 체크 표시로 켜졌음을 보여 준다.
  Widget _simpleTitle(String title, bool active) => Row(
    children: [
      Icon(
        active ? Icons.check_circle : Icons.radio_button_unchecked,
        size: 18,
        color: active ? Theme.of(context).colorScheme.primary : Theme.of(context).colorScheme.outline,
      ),
      const SizedBox(width: 6),
      Text(title, style: Theme.of(context).textTheme.titleSmall),
    ],
  );

  Widget _simpleField(TextEditingController controller, String key, String hint) => TextField(
    key: ValueKey(key),
    controller: controller,
    onChanged: (_) {
      setState(() {});
      _schedulePreview();
    },
    decoration: InputDecoration(hintText: hint, isDense: true, border: const OutlineInputBorder()),
  );

  /// 오늘 날짜를 고른 형식으로 보여 준다.
  String _dateSample(String format) {
    final t = DateTime.now();
    String two(int v) => v.toString().padLeft(2, '0');
    return format == 'YYMMDD' ? '${two(t.year % 100)}${two(t.month)}${two(t.day)}' : '${t.year}.${two(t.month)}.${two(t.day)}.';
  }

  /// 칸이 좁으면 단추 묶음을 줄여 넘치지 않게 한다.
  Widget _fit(Widget child) => Align(
    alignment: Alignment.centerLeft,
    child: FittedBox(fit: BoxFit.scaleDown, alignment: Alignment.centerLeft, child: child),
  );

  Widget _buildSimple(BuildContext context) {
    const gap = SizedBox(height: 16);
    final rules = _rules.length;
    return ListView(
      padding: const EdgeInsets.all(12),
      children: [
        Text('바꿀 내용을 적으세요', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 2),
        Text('적은 항목만 적용됩니다.', style: Theme.of(context).textTheme.bodySmall),
        gap,
        _simpleTitle('맨 앞에 글자 넣기 (접두사)', _prefix.text.isNotEmpty),
        const SizedBox(height: 6),
        _simpleField(_prefix, 'rename-prefix', '예: 사진'),
        gap,
        _simpleTitle('맨 뒤에 글자 넣기 (접미사)', _suffix.text.isNotEmpty),
        const SizedBox(height: 6),
        _simpleField(_suffix, 'rename-suffix', '예: 끝'),
        const SizedBox(height: 2),
        Text('확장자(.hwpx 등) 앞에 들어갑니다.', style: Theme.of(context).textTheme.bodySmall),
        gap,
        _simpleTitle('글자 바꾸기', _find.text.isNotEmpty),
        const SizedBox(height: 6),
        LayoutBuilder(
          builder: (context, box) {
            final from = Row(children: [
              Expanded(child: _simpleField(_find, 'rename-find', '예: 만두')),
              const Padding(padding: EdgeInsets.symmetric(horizontal: 6), child: Text('을(를)')),
            ]);
            final to = Row(children: [
              Expanded(child: _simpleField(_replaceTo, 'rename-replace-to', '예: 자장면')),
              const Padding(padding: EdgeInsets.only(left: 6), child: Text('(으)로')),
            ]);
            return box.maxWidth < 300
                ? Column(children: [from, const SizedBox(height: 6), to])
                : Row(children: [Expanded(child: from), const SizedBox(width: 6), Expanded(child: to)]);
          },
        ),
        gap,
        _simpleTitle('오늘 날짜 넣기 (선택)', _datePosition != 'none'),
        const SizedBox(height: 6),
        _fit(SegmentedButton<String>(
          key: const ValueKey('rename-date-position'),
          showSelectedIcon: false,
          segments: const [
            ButtonSegment(value: 'none', label: Text('안 넣음')),
            ButtonSegment(value: 'prefix', label: Text('맨 앞')),
            ButtonSegment(value: 'suffix', label: Text('맨 뒤')),
          ],
          selected: {_datePosition},
          onSelectionChanged: (v) {
            setState(() => _datePosition = v.first);
            _schedulePreview();
          },
        )),
        const SizedBox(height: 6),
        _fit(SegmentedButton<String>(
          key: const ValueKey('rename-date-format'),
          showSelectedIcon: false,
          segments: [
            ButtonSegment(value: 'YYYY.MM.DD.', label: Text(_dateSample('YYYY.MM.DD.'))),
            ButtonSegment(value: 'YYMMDD', label: Text(_dateSample('YYMMDD'))),
          ],
          selected: {_dateFormat},
          onSelectionChanged: _datePosition == 'none'
              ? null
              : (v) {
                  setState(() => _dateFormat = v.first);
                  _schedulePreview();
                },
        )),
        gap,
        const Divider(height: 1),
        Align(
          alignment: Alignment.centerLeft,
          child: TextButton.icon(
            key: const ValueKey('rename-advanced'),
            onPressed: () => setState(() => _advanced = true),
            icon: const Icon(Icons.tune, size: 18),
            label: Text(rules > 0 ? '고급 기능 (규칙 $rules개 적용 중)' : '고급 기능'),
          ),
        ),
      ],
    );
  }

  Widget _buildRules(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Align(
          alignment: Alignment.centerLeft,
          child: TextButton.icon(
            key: const ValueKey('rename-simple'),
            onPressed: () => setState(() => _advanced = false),
            icon: const Icon(Icons.arrow_back, size: 18),
            label: const Text('쉬운 화면으로'),
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(12, 8, 4, 0),
          child: Row(
            children: [
              Expanded(child: Text('고급 규칙 (쉬운 입력 다음에 적용)', style: Theme.of(context).textTheme.titleSmall)),
              PopupMenuButton<String>(
                tooltip: '규칙 세트',
                onSelected: _rulesetMenu,
                itemBuilder: (_) => [
                  const PopupMenuItem(value: 'load', child: Text('규칙 세트 불러오기')),
                  PopupMenuItem(value: 'save', enabled: _rules.isNotEmpty, child: const Text('지금 규칙 저장')),
                  const PopupMenuItem(value: 'export', child: Text('JSON 내보내기')),
                  const PopupMenuItem(value: 'import', child: Text('JSON 가져오기')),
                ],
                icon: const Icon(Icons.bookmarks_outlined),
              ),
            ],
          ),
        ),
        Expanded(
          child: _rules.isEmpty
              ? const Center(child: Text('[+ 규칙 추가]로 시작하세요.'))
              : ListView.builder(
                  itemCount: _rules.length,
                  itemBuilder: (context, index) {
                    final rule = _rules[index];
                    final enabled = rule['enabled'] != false;
                    return Card(
                      key: ValueKey('rename-rule-$index'),
                      margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      child: ListTile(
                        dense: true,
                        leading: Checkbox(
                          value: enabled,
                          onChanged: (v) {
                            setState(() => rule['enabled'] = v == true);
                            _schedulePreview();
                          },
                        ),
                        title: Text('${index + 1}. ${ruleKindOf('${rule['kind']}').label}'),
                        subtitle: Text(ruleSummary(rule), overflow: TextOverflow.ellipsis),
                        onTap: () => _editRule(index),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            IconButton(
                              tooltip: '위로',
                              visualDensity: VisualDensity.compact,
                              onPressed: index > 0 ? () => _moveRule(index, -1) : null,
                              icon: const Icon(Icons.keyboard_arrow_up),
                            ),
                            IconButton(
                              tooltip: '아래로',
                              visualDensity: VisualDensity.compact,
                              onPressed: index < _rules.length - 1 ? () => _moveRule(index, 1) : null,
                              icon: const Icon(Icons.keyboard_arrow_down),
                            ),
                            IconButton(
                              tooltip: '규칙 지우기',
                              visualDensity: VisualDensity.compact,
                              onPressed: () {
                                setState(() => _rules.removeAt(index));
                                _schedulePreview();
                              },
                              icon: const Icon(Icons.close),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
        ),
        Padding(
          padding: const EdgeInsets.all(8),
          child: PopupMenuButton<RuleKind>(
            key: const ValueKey('rename-add-rule'),
            tooltip: '규칙 추가',
            onSelected: _addRule,
            itemBuilder: (_) => [
              for (final kind in ruleKinds) PopupMenuItem(value: kind, child: Text(kind.label)),
            ],
            child: const IgnorePointer(
              child: OutlinedButton(onPressed: null, child: Text('+ 규칙 추가')),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildFooter(BuildContext context) {
    final problems = _count('conflict') + _count('invalid');
    final summary = _entries.isEmpty
        ? ''
        : '${_entries.length}개 중 ${_count('ok')}개 바뀜 · 충돌 ${_count('conflict')} · 오류 ${_count('invalid')}';
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Row(
        children: [
          Expanded(
            child: Text(
              [summary, _message].where((s) => s.isNotEmpty).join('   ·   '),
              key: const ValueKey('rename-summary'),
              overflow: TextOverflow.ellipsis,
              style: TextStyle(color: problems > 0 ? Theme.of(context).colorScheme.error : null),
            ),
          ),
          if (_busy) const Padding(padding: EdgeInsets.only(right: 8), child: SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2))),
          FilledButton.icon(
            key: const ValueKey('rename-apply'),
            onPressed: _canApply ? _apply : null,
            icon: const Icon(Icons.drive_file_rename_outline),
            label: const Text('이름 바꾸기 (Ctrl+S)'),
          ),
        ],
      ),
    );
  }
}
