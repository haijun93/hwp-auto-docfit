import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

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

/// 파일이름 탭: 파일을 모아 규칙(위→아래)으로 새 이름을 미리 보고, 적용·되돌리기.
class FileRenameScreen extends StatefulWidget {
  const FileRenameScreen({super.key, required this.api});

  final ApiCall api;

  @override
  State<FileRenameScreen> createState() => FileRenameScreenState();
}

class FileRenameScreenState extends State<FileRenameScreen> {
  late final FileRenameApi _api = FileRenameApi(widget.api);
  List<RenameEntry> _entries = const [];
  final List<Map<String, Object?>> _rules = [];
  final Map<String, String> _overrides = {};
  final Set<String> _excluded = {};
  Map<String, RenamePreviewItem> _preview = const {};
  Map<String, Object?> _summary = const {};
  String? _planId;
  String? _selected;
  String _message = '';
  bool _busy = false;
  bool _recursive = false;
  String? _lastRun;
  Timer? _debounce;
  void Function()? _stopDrops;

  @override
  void initState() {
    super.initState();
    _stopDrops = watchWindowEvent('docfit-rename-files-dropped', () => unawaited(_refreshList()));
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _stopDrops?.call();
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
      'rules': _rules,
      'overrides': _overrides,
      'excluded': _excluded.toList(),
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
    final edited = kind.defaults.isEmpty ? rule : await showRuleEditor(context, rule);
    if (edited == null || !mounted) return;
    setState(() => _rules.add(edited));
    _schedulePreview();
  }

  Future<void> _editRule(int index) async {
    final edited = await showRuleEditor(context, _rules[index]);
    if (edited == null || !mounted) return;
    setState(() => _rules[index] = edited);
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
              final wide = constraints.maxWidth >= 900;
              final list = _buildList(context);
              final rules = _buildRules(context);
              return Column(
                children: [
                  _buildToolbar(context),
                  const Divider(height: 1),
                  Expanded(
                    child: wide
                        ? Row(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              Expanded(flex: 3, child: list),
                              const VerticalDivider(width: 1),
                              SizedBox(width: 340, child: rules),
                            ],
                          )
                        : Column(
                            children: [
                              Expanded(flex: 3, child: list),
                              const Divider(height: 1),
                              Expanded(flex: 2, child: rules),
                            ],
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
          const SizedBox(width: 8),
          OutlinedButton.icon(
            onPressed: _busy || _entries.isEmpty ? null : () => _run('clear', null, '목록을 비웠습니다'),
            icon: const Icon(Icons.clear_all),
            label: const Text('목록 지우기'),
          ),
          const SizedBox(width: 6),
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
          const SizedBox(width: 8),
          OutlinedButton.icon(
            key: const ValueKey('rename-undo'),
            onPressed: _busy || _lastRun == null ? null : () => _undo(),
            icon: const Icon(Icons.undo),
            label: const Text('되돌리기'),
          ),
          IconButton(
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
              const Text('오른쪽에서 규칙을 쌓으면 바뀔 이름을 바로 보여 줍니다. [변경 적용]을 눌러야 실제로 바뀝니다.',
                  textAlign: TextAlign.center, style: TextStyle(fontSize: 12)),
            ],
          ),
        ),
      );
    }
    final header = Theme.of(context).textTheme.labelMedium;
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(8, 6, 8, 6),
          child: Row(
            children: [
              const SizedBox(width: 40),
              Expanded(child: Text('원래 이름', style: header)),
              Expanded(child: Text('새 이름 (두 번 눌러 직접 고치기)', style: header)),
              SizedBox(width: 80, child: Text('상태', style: header)),
            ],
          ),
        ),
        const Divider(height: 1),
        Expanded(
          child: ListView.builder(
            itemCount: _entries.length,
            itemExtent: 36,
            itemBuilder: (context, index) {
              final entry = _entries[index];
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
                          child: Text(
                            item?.newName ?? '',
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              fontWeight: changed ? FontWeight.w600 : null,
                              fontStyle: item?.overridden == true ? FontStyle.italic : null,
                            ),
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

  Widget _buildRules(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(12, 8, 4, 0),
          child: Row(
            children: [
              Expanded(child: Text('규칙 (위에서 아래로 적용)', style: Theme.of(context).textTheme.titleSmall)),
              PopupMenuButton<String>(
                tooltip: '규칙 세트',
                onSelected: _rulesetMenu,
                itemBuilder: (_) => [
                  const PopupMenuItem(value: 'load', child: Text('규칙 세트 불러오기')),
                  PopupMenuItem(value: 'save', enabled: _rules.isNotEmpty, child: const Text('지금 규칙 저장')),
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
            label: const Text('변경 적용 (Ctrl+S)'),
          ),
        ],
      ),
    );
  }
}
