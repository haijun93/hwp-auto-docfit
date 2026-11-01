import 'package:flutter/material.dart';
import '../../core/api/abbreviation_api.dart' show ApiCall;
import '../../core/api/live_hotkeys_api.dart';

/// Compact alpha-2 helper surface for live Hangul status and global shortcuts.
class HelperPanelScreen extends StatefulWidget {
  const HelperPanelScreen({super.key, required this.api});
  final ApiCall api;

  @override
  State<HelperPanelScreen> createState() => _HelperPanelScreenState();
}

class _HelperPanelScreenState extends State<HelperPanelScreen> {
  late final LiveHotkeysApi _hotkeys = LiveHotkeysApi(widget.api);
  final Map<String, TextEditingController> _fields = {};
  Map<String, String> _failed = {};
  bool _loading = true;
  bool _saving = false;
  String? _error;

  static const _labels = {
    'panel': '패널 열기·닫기',
    'table_template': '표 템플릿',
    'table_sketch': '표그림판',
  };

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final state = await _hotkeys.get();
      for (final entry in state.bindings.entries) {
        _fields.putIfAbsent(entry.key, () => TextEditingController()).text = entry.value;
      }
      if (mounted) setState(() { _failed = state.failed; _loading = false; });
    } catch (error) {
      if (mounted) setState(() { _error = '$error'; _loading = false; });
    }
  }

  Future<void> _save() async {
    setState(() { _saving = true; _error = null; });
    try {
      final result = await _hotkeys.set({for (final entry in _fields.entries) entry.key: entry.value.text.trim()});
      if (!result.ok) throw StateError(result.message ?? '단축키를 저장하지 못했습니다.');
      if (mounted) setState(() { _failed = result.failed; _saving = false; });
    } catch (error) {
      if (mounted) setState(() { _error = '$error'; _saving = false; });
    }
  }

  @override
  void dispose() {
    for (final controller in _fields.values) { controller.dispose(); }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      AppBar(title: const Text('한/글 도우미'), automaticallyImplyLeading: false, toolbarHeight: 52,
        actions: [IconButton(tooltip: '닫기', onPressed: () => Navigator.maybePop(context), icon: const Icon(Icons.close))]),
      Expanded(child: _loading ? const Center(child: CircularProgressIndicator()) : ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('한/글 문서에서 바로 쓰는 전역 단축키', style: TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 12),
          for (final key in _labels.keys) ...[
            TextField(controller: _fields.putIfAbsent(key, () => TextEditingController()),
              key: Key('hotkey-$key'), decoration: InputDecoration(labelText: _labels[key], hintText: '예: Ctrl+Alt+J')),
            if (_failed.containsKey(key)) Padding(padding: const EdgeInsets.only(top: 4, bottom: 8),
              child: Text('다른 프로그램이 사용 중 · ${_failed[key]}', key: Key('hotkey-conflict-$key'),
                style: TextStyle(color: Theme.of(context).colorScheme.error, fontSize: 12))),
            const SizedBox(height: 8),
          ],
          if (_error != null) Text(_error!, key: const Key('hotkey-error'), style: TextStyle(color: Theme.of(context).colorScheme.error)),
          FilledButton(onPressed: _saving ? null : _save, child: Text(_saving ? '저장 중…' : '단축키 저장')),
          const SizedBox(height: 18),
          const ListTile(leading: Icon(Icons.info_outline), title: Text('현재 문서 작업은 기존 탭에서 계속할 수 있어요.'),
            subtitle: Text('패널 위치 추적과 트레이 동작은 Windows에서 확인이 필요합니다.')),
        ],
      )),
    ],
  );
}
