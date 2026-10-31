import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/api/abbreviation_api.dart' show ApiCall;

/// K클립보드 관리: 켜기(동의)·끄기·상태·목록(검색·고정·지우기·클립보드에 올리기)·설정.
/// 빠른 붙여넣기는 상주 프로그램의 단축키 팝업(기본 Ctrl+Shift+V)이 맡고, 이 화면은 관리용이다.
Future<void> showKClipDialog(BuildContext context, ApiCall api) {
  return showDialog<void>(
    context: context,
    builder: (_) => Dialog(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 640, maxHeight: 720),
        child: KClipPanel(api: api),
      ),
    ),
  );
}

class KClipPanel extends StatefulWidget {
  const KClipPanel({super.key, required this.api});

  final ApiCall api;

  @override
  State<KClipPanel> createState() => _KClipPanelState();
}

class _KClipPanelState extends State<KClipPanel> {
  Map status = const {};
  List<Map> items = const [];
  Map settings = const {};
  bool consent = false;
  bool autostart = true;
  bool busy = false;
  String message = '';
  String query = '';
  Timer? _debounce;

  bool get running => status['running'] == true;
  Map get agent => (status['status'] as Map?) ?? const {};

  @override
  void initState() {
    super.initState();
    unawaited(_reload());
  }

  @override
  void dispose() {
    _debounce?.cancel();
    super.dispose();
  }

  Future<Map> _call(String action, [Map<String, Object?>? payload]) async {
    final response = await widget.api('kclip', [action, payload ?? const {}]);
    final map = response is Map ? response : {'ok': false, 'message': '올바르지 않은 응답입니다.'};
    if (map['ok'] == false && mounted) setState(() => message = '${map['message'] ?? ''}');
    return map;
  }

  Future<void> _reload() async {
    final s = await _call('status');
    if (!mounted) return;
    setState(() => status = s);
    if (running) {
      final list = await _call('list', {'limit': 200, if (query.isNotEmpty) 'query': query});
      final conf = await _call('settings_get');
      if (!mounted) return;
      setState(() {
        items = [for (final i in (list['items'] as List? ?? const [])) i as Map];
        settings = (conf['settings'] as Map?) ?? const {};
      });
    }
  }

  Future<void> _act(String action, [Map<String, Object?>? payload, String? done]) async {
    if (busy) return;
    setState(() => busy = true);
    try {
      final result = await _call(action, payload);
      if (result['ok'] != false && done != null && mounted) setState(() => message = done);
      await _reload();
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  String _kind(Object? kind) => switch (kind) {
    'text' => '글',
    'image' => '그림',
    'files' => '파일',
    _ => '?',
  };

  IconData _kindIcon(Object? kind) => switch (kind) {
    'image' => Icons.image_outlined,
    'files' => Icons.insert_drive_file_outlined,
    _ => Icons.notes,
  };

  Widget _off(BuildContext context) {
    final available = status['available'] != false;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text('${status['consent'] ?? ''}'),
        const SizedBox(height: 12),
        const Text(
          '켜면 작은 상주 프로그램이 따로 실행됩니다(약 0.6MB, 메모리 2MB 안팎, 쉴 때 CPU 0%). '
          '아무 창에서나 Ctrl+Shift+V를 누르면 최근 항목이 바로 뜨고, 숫자나 Enter로 고르면 그 자리에 붙여넣습니다.',
          style: TextStyle(fontSize: 12),
        ),
        CheckboxListTile(
          key: const ValueKey('kclip-consent'),
          contentPadding: EdgeInsets.zero,
          value: consent,
          onChanged: (v) => setState(() => consent = v == true),
          title: const Text('위 안내를 읽었고 기록에 동의합니다'),
        ),
        CheckboxListTile(
          contentPadding: EdgeInsets.zero,
          value: autostart,
          onChanged: (v) => setState(() => autostart = v == true),
          title: const Text('Windows에 로그인하면 자동으로 켜기(30초 뒤)'),
        ),
        const SizedBox(height: 8),
        if (!available)
          Text('이 버전에는 K클립보드 프로그램이 들어 있지 않습니다.',
              style: TextStyle(color: Theme.of(context).colorScheme.error)),
        FilledButton.icon(
          key: const ValueKey('kclip-enable'),
          onPressed: consent && available && !busy
              ? () => _act('enable', {'consent': true, 'autostart': autostart}, 'K클립보드를 켰습니다.')
              : null,
          icon: const Icon(Icons.power_settings_new),
          label: const Text('K클립보드 켜기'),
        ),
      ],
    );
  }

  Widget _settings(BuildContext context) {
    Widget number(String key, String label, List<int> choices) => DropdownButton<int>(
      value: choices.contains((settings[key] as num?)?.toInt()) ? (settings[key] as num).toInt() : null,
      hint: Text('${settings[key] ?? ''}'),
      items: [for (final c in choices) DropdownMenuItem(value: c, child: Text('$label $c'))],
      onChanged: (v) => _act('settings_set', {
        'settings': {key: v},
      }),
    );
    return Wrap(
      spacing: 12,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: [
        number('max_items', '보관 개수', const [20, 50, 100, 200, 500, 1000]),
        number('max_total_mb', '최대 MB', const [50, 100, 200, 500, 1000]),
        number('max_age_days', '보관 일', const [7, 30, 90, 365]),
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Switch(
              value: settings['auto_paste'] != false,
              onChanged: (v) => _act('settings_set', {
                'settings': {'auto_paste': v},
              }),
            ),
            const Text('고르면 바로 붙여넣기'),
          ],
        ),
      ],
    );
  }

  Widget _on(BuildContext context) {
    final paused = agent['paused'] == true;
    final hotkeyOk = agent['hotkey_ok'] != false;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Wrap(
          spacing: 8,
          runSpacing: 8,
          crossAxisAlignment: WrapCrossAlignment.center,
          children: [
            Chip(
              avatar: Icon(paused ? Icons.pause_circle_outline : Icons.fiber_manual_record,
                  size: 16, color: paused ? null : Colors.red),
              label: Text(paused ? '일시정지' : '기록 중 · ${agent['items'] ?? items.length}개'),
            ),
            Tooltip(
              message: hotkeyOk ? '아무 창에서나 누르면 최근 항목이 뜹니다' : '다른 프로그램이 이 단축키를 쓰고 있습니다',
              child: Chip(label: Text('${agent['hotkey'] ?? 'Ctrl+Shift+V'}${hotkeyOk ? '' : ' (사용 불가)'}')),
            ),
            OutlinedButton(
              onPressed: busy ? null : () => _act(paused ? 'resume' : 'pause'),
              child: Text(paused ? '다시 기록' : '일시정지'),
            ),
            OutlinedButton(
              onPressed: busy ? null : () => _act('clear', {'keep_pinned': true}, '고정하지 않은 항목을 지웠습니다.'),
              child: const Text('모두 지우기(고정 제외)'),
            ),
            TextButton(
              key: const ValueKey('kclip-disable'),
              onPressed: busy ? null : () => _act('disable', null, 'K클립보드를 껐습니다.'),
              child: const Text('끄기'),
            ),
          ],
        ),
        const SizedBox(height: 8),
        _settings(context),
        TextField(
          decoration: const InputDecoration(prefixIcon: Icon(Icons.search), hintText: '찾기'),
          onChanged: (v) {
            query = v.trim();
            _debounce?.cancel();
            _debounce = Timer(const Duration(milliseconds: 200), () => unawaited(_reload()));
          },
        ),
        const SizedBox(height: 4),
        Expanded(
          child: items.isEmpty
              ? const Center(child: Text('기록된 항목이 없습니다.'))
              : ListView.builder(
                  itemCount: items.length,
                  itemBuilder: (context, index) {
                    final item = items[index];
                    final pinned = item['pinned'] == true;
                    return ListTile(
                      key: ValueKey('kclip-item-${item['id']}'),
                      dense: true,
                      leading: Tooltip(message: _kind(item['kind']), child: Icon(_kindIcon(item['kind']))),
                      title: Text('${item['preview'] ?? ''}', maxLines: 2, overflow: TextOverflow.ellipsis),
                      onTap: () => _act('restore', {'id': item['id']}, '클립보드에 올렸습니다. Ctrl+V로 붙여넣으세요.'),
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                            tooltip: pinned ? '고정 풀기' : '고정(지워지지 않음)',
                            onPressed: () => _act('pin', {'id': item['id'], 'pinned': !pinned}),
                            icon: Icon(pinned ? Icons.push_pin : Icons.push_pin_outlined),
                          ),
                          IconButton(
                            tooltip: '지우기',
                            onPressed: () => _act('delete', {'id': item['id']}),
                            icon: const Icon(Icons.delete_outline),
                          ),
                        ],
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              const Icon(Icons.content_paste_search),
              const SizedBox(width: 8),
              Expanded(child: Text('K클립보드', style: Theme.of(context).textTheme.titleLarge)),
              IconButton(
                tooltip: '닫기',
                onPressed: () => Navigator.of(context).maybePop(),
                icon: const Icon(Icons.close),
              ),
            ],
          ),
          const SizedBox(height: 8),
          if (status.isEmpty)
            const Center(child: CircularProgressIndicator())
          else if (running)
            Expanded(child: _on(context))
          else
            Flexible(child: SingleChildScrollView(child: _off(context))),
          if (message.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text(message, key: const ValueKey('kclip-message')),
            ),
        ],
      ),
    );
  }
}
