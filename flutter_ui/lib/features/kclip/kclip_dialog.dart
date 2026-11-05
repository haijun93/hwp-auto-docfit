import 'dart:async';
import 'dart:collection';
import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';

import '../../core/api/abbreviation_api.dart' show ApiCall;

/// 몽땅클립보드 관리: 켜기(동의)·끄기·상태·목록(검색·고정·지우기·클립보드에 올리기)·설정.
/// 빠른 붙여넣기는 상주 프로그램의 단축키 팝업(기본 Ctrl+Shift+V)이 맡고, 이 화면은 관리용이다.
enum KClipEntryMode { sidebar, hotkey }

Future<void> showKClipDialog(BuildContext context, ApiCall api,
    {KClipEntryMode mode = KClipEntryMode.sidebar}) {
  var fill = false;
  return showDialog<void>(
    context: context,
    barrierDismissible: false,
    builder: (_) => StatefulBuilder(
      // 앱 창을 최대화하면 몽땅클립보드 창도 앱 창 전체를 채운다.
      builder: (context, setDialogState) => Dialog(
        insetPadding: fill ? EdgeInsets.zero : const EdgeInsets.all(28),
        clipBehavior: Clip.antiAlias,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        child: ConstrainedBox(
          constraints: fill
              ? const BoxConstraints.expand()
              : const BoxConstraints(maxWidth: 720, maxHeight: 820),
          child: KClipPanel(
            api: api,
            mode: mode,
            onMaximizedChanged: (value) {
              if (value != fill) setDialogState(() => fill = value);
            },
          ),
        ),
      ),
    ),
  );
}

class KClipPanel extends StatefulWidget {
  const KClipPanel({
    super.key,
    required this.api,
    this.mode = KClipEntryMode.sidebar,
    this.onMaximizedChanged,
  });

  final ApiCall api;
  final KClipEntryMode mode;
  final ValueChanged<bool>? onMaximizedChanged;

  @override
  State<KClipPanel> createState() => _KClipPanelState();
}

class _KClipPanelState extends State<KClipPanel> {
  Map status = const {};
  List<Map> items = const [];
  Map settings = const {};
  bool consent = false;
  bool autostart = false;
  bool minimized = false;
  bool isTop = false;
  bool maximized = false;
  final TextEditingController _memo = TextEditingController();
  bool busy = false;
  String message = '';
  String query = '';
  String category = '전체';
  Timer? _debounce;
  final LinkedHashMap<int, Uint8List?> _images = LinkedHashMap();
  final Set<int> _loadingImages = {};

  bool get running => status['running'] == true;
  Map get agent => (status['status'] as Map?) ?? const {};
  bool get hotkeyMode => widget.mode == KClipEntryMode.hotkey;
  List<Map> get visibleItems => items.where((item) {
    final kind = '${item['kind'] ?? ''}';
    final webItem = _isWebText(item);
    final matches = switch (category) {
      '글' => kind == 'text' && !webItem,
      '그림' => kind == 'image',
      '파일' => webItem || (kind == 'files' && !_isFolder(item)),
      '폴더' => kind == 'files' && _isFolder(item),
      '웹' => webItem,
      _ => true,
    };
    return matches;
  }).toList();

  bool _isWeb(Map item) => '${item['preview'] ?? ''}'.contains('· 웹 ·');
  bool _isWebText(Map item) => _isWeb(item) || RegExp(r'^https?://[^\s]+$', caseSensitive: false)
      .hasMatch('${item['preview'] ?? ''}'.trim());
  bool _isFolder(Map item) {
    if (item['is_folder'] == true || item['kind'] == 'folder') return true;
    if (item['kind'] != 'files') return false;
    final preview = '${item['preview'] ?? ''}';
    if (preview.contains(' · ')) return false;
    final parts = preview.split(RegExp(r'\s*·\s*'));
    return parts.isNotEmpty && parts.every((part) => part.contains('\\') || part.contains('/'));
  }
  Future<void> _openWeb(Map item) async {
    final result = await widget.api('kclip', ['open_web', {'id': item['id']}]);
    if (result is Map && result['ok'] == false && mounted) {
      setState(() => message = '${result['message'] ?? '웹 링크를 열지 못했습니다.'}');
    }
  }

  @override
  void initState() {
    super.initState();
    unawaited(_reload());
    unawaited(_windowControl('state'));
  }

  /// 네이티브 앱 창 최대화/복원(desktop_web_ui.window_control). 실패하면 화면 상태를 바꾸지 않는다.
  Future<void> _windowControl(String action) async {
    Object? result;
    try {
      result = await widget.api('window_control', [action]);
    } catch (_) {
      return;
    }
    if (!mounted || result is! Map) return;
    final map = result;
    setState(() {
      if (map['maximized'] is bool) maximized = map['maximized'] as bool;
      if (action != 'state' && map['ok'] == false) {
        message = '${map['message'] ?? '창 크기를 바꾸지 못했습니다.'}';
      }
    });
    widget.onMaximizedChanged?.call(maximized);
  }

  Future<void> _toggleMaximize() => _windowControl('toggle_maximize');

  @override
  void dispose() {
    _debounce?.cancel();
    _memo.dispose();
    unawaited(_setNativeDropTarget('documents'));
    super.dispose();
  }

  Future<Map> _call(String action, [Map<String, Object?>? payload]) async {
    final response = await widget.api('kclip', [action, payload ?? const {}]);
    final map = response is Map
        ? response
        : {'ok': false, 'message': '올바르지 않은 응답입니다.'};
    if (map['ok'] == false && mounted) {
      setState(() => message = '${map['message'] ?? ''}');
    }
    return map;
  }

  Future<void> _reload() async {
    final s = await _call('status');
    if (!mounted) return;
    setState(() {
      status = s;
      autostart = s['autostart'] == true;
    });
    if (running) {
      final list = await _call('list', {
        'limit': 200,
        if (query.isNotEmpty) 'query': query,
      });
      final conf = await _call('settings_get');
      if (!mounted) return;
      setState(() {
        items = [
          for (final i in (list['items'] as List? ?? const [])) i as Map,
        ];
        items.sort(
          (a, b) => (b['pinned'] == true ? 1 : 0).compareTo(
            a['pinned'] == true ? 1 : 0,
          ),
        );
        settings = (conf['settings'] as Map?) ?? const {};
      });
    }
  }

  Future<Uint8List?> _imageFor(int id) async {
    if (_images.containsKey(id)) return _images[id];
    if (!_loadingImages.add(id)) return null;
    final result = await _call('get', {'id': id});
    Uint8List? bytes;
    try {
      if (result['kind'] == 'image' && result['data'] is String) {
        bytes = base64Decode(result['data'] as String);
      }
    } catch (_) {}
    _loadingImages.remove(id);
    if (!mounted) return bytes;
    setState(() {
      _images[id] = bytes;
      while (_images.length > 24) {
        _images.remove(_images.keys.first);
      }
    });
    return bytes;
  }

  void _preview(Map item) {
    showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(_kind(item['kind'])),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('닫기'),
          ),
          FilledButton(
            onPressed: () {
              Navigator.of(context).pop();
              _act('restore', {
                'id': item['id'],
              }, '클립보드에 올렸습니다. Ctrl+V로 붙여넣으세요.');
            },
            child: const Text('다시 복사'),
          ),
        ],
        content: FutureBuilder<Uint8List?>(
          future: item['kind'] == 'image'
              ? _imageFor((item['id'] as num).toInt())
              : Future.value(null),
          builder: (context, snapshot) {
            if (item['kind'] == 'image') {
              if (snapshot.connectionState != ConnectionState.done) {
                return const SizedBox(
                  height: 160,
                  child: Center(child: CircularProgressIndicator()),
                );
              }
              return snapshot.data == null
                  ? const Text('그림을 불러오지 못했습니다.')
                  : Image.memory(snapshot.data!, fit: BoxFit.contain);
            }
            return SingleChildScrollView(
              child: SelectableText('${item['preview'] ?? ''}'),
            );
          },
        ),
      ),
    );
  }

  Future<void> _act(
    String action, [
    Map<String, Object?>? payload,
    String? done,
  ]) async {
    if (busy) return;
    setState(() => busy = true);
    try {
      final result = await _call(action, payload);
      if (result['ok'] != false && done != null && mounted) {
        setState(() => message = done);
      }
      await _reload();
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> _convertExcel() async {
    if (busy) return;
    setState(() => busy = true);
    try {
      final result = await widget.api('excel_table', ['paste_clean', const {}]);
      if (!mounted) return;
      setState(() {
        if (result is Map && result['ok'] == true) {
          final counts = (result['cleaned'] as Map?) ?? const {};
            message = '${result['rows']}행 × ${result['cols']}열 표 구조·내용 유지, 배경 음영 제거 · 공백 ${counts['spaces'] ?? 0}, 기호 ${counts['symbols'] ?? 0} 정리. 한/글에서 Ctrl+V';
        } else {
          message =
              '${(result is Map ? result['message'] : null) ?? '클립보드에서 엑셀 표를 찾지 못했습니다.'}';
        }
      });
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> _addMemo() async {
    final text = _memo.text.trim();
    if (text.isEmpty || busy) return;
    await _act('add_text', {'text': text}, '메모를 클립보드 항목에 추가했습니다.');
    if (message.startsWith('메모를')) _memo.clear();
  }

  Future<void> _setNativeDropTarget(String target) async {
    try {
      await widget.api('set_drop_target', [target]);
    } catch (_) {}
  }

  Future<void> _confirmClearAll() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        content: const Text('고정한 항목은 남고 나머지를 지웁니다.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('취소'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('지우기'),
          ),
        ],
      ),
    );
    if (confirmed == true && mounted) {
      await _act('clear', {'keep_pinned': true}, '고정하지 않은 항목을 지웠습니다.');
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
          key: const ValueKey('kclip-autostart'),
          contentPadding: EdgeInsets.zero,
          value: autostart,
          onChanged: (v) => setState(() => autostart = v == true),
          title: const Text('Windows에 로그인하면 자동으로 켜기(30초 뒤)'),
        ),
        const SizedBox(height: 2),
        if (!available)
          Text(
            '이 버전에는 몽땅클립보드 프로그램이 들어 있지 않습니다.',
            style: TextStyle(color: Theme.of(context).colorScheme.error),
          ),
        FilledButton.icon(
          key: const ValueKey('kclip-enable'),
          onPressed: consent && available && !busy
              ? () => _act('enable', {
                  'consent': true,
                  'autostart': autostart,
                }, '몽땅클립보드를 켰습니다.')
              : null,
          icon: const Icon(Icons.power_settings_new),
          label: const Text('몽땅클립보드 켜기'),
        ),
      ],
    );
  }

  Widget _settings(BuildContext context) {
    Widget number(String key, String label, List<int> choices) =>
        DropdownButton<int>(
          value: choices.contains((settings[key] as num?)?.toInt())
              ? (settings[key] as num).toInt()
              : null,
          hint: Text('${settings[key] ?? ''}'),
          items: [
            for (final c in choices)
              DropdownMenuItem(value: c, child: Text('$label $c')),
          ],
          onChanged: (v) => _act('settings_set', {
            'settings': {key: v},
          }),
        );
    return Wrap(
      spacing: 12,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: [
        SizedBox(
          width: 300,
          child: CheckboxListTile(
            key: const ValueKey('kclip-autostart-running'),
            contentPadding: EdgeInsets.zero,
            value: autostart,
            onChanged: busy
                ? null
                : (value) async {
                    final result = await _call('autostart', {
                      'enabled': value == true,
                    });
                    if (mounted && result['ok'] != false) {
                      setState(() {
                        status = result;
                        autostart = result['autostart'] == true;
                      });
                    }
                  },
            title: const Text('Windows 로그인 시 자동 실행'),
          ),
        ),
        number('max_items', '보관 개수', const [20, 50, 100, 200, 500, 1000]),
        number('max_total_mb', '최대 MB', const [50, 100, 200, 500, 1000]),
        number('max_age_days', '보관 일', const [7, 30, 90, 365]),
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Switch(
              key: const ValueKey('kclip-sticky-popup'),
              value: settings['sticky_popup'] == true,
              onChanged: (v) => _act('settings_set', {
                'settings': {'sticky_popup': v},
              }),
            ),
            const Text('스티커 메모처럼 화면에 유지'),
          ],
        ),
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Switch(
              key: const ValueKey('kclip-always-on-top'),
              value: settings['always_on_top'] != false,
              onChanged: (v) => _act('settings_set', {
                'settings': {'always_on_top': v},
              }),
            ),
            const Text('항상 위'),
          ],
        ),
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
              avatar: Icon(
                paused ? Icons.pause_circle_outline : Icons.fiber_manual_record,
                size: 16,
                color: paused ? null : Colors.red,
              ),
              label: Text(
                paused ? '일시정지' : '기록 중 · ${agent['items'] ?? items.length}개',
              ),
            ),
            Tooltip(
              message: hotkeyOk
                  ? '아무 창에서나 누르면 최근 항목이 뜹니다'
                  : '다른 프로그램이 이 단축키를 쓰고 있습니다',
              child: Chip(
                label: Text(
                  '${agent['hotkey'] ?? 'Ctrl+Shift+V'}${hotkeyOk ? '' : ' (사용 불가)'}',
                ),
              ),
            ),
            OutlinedButton(
              onPressed: busy ? null : () => _act(paused ? 'resume' : 'pause'),
              child: Text(paused ? '다시 기록' : '일시정지'),
            ),
            PopupMenuButton<int>(
              tooltip: '일시정지 시간',
              onSelected: (minutes) => _act('pause', {'minutes': minutes}),
              itemBuilder: (_) => const [
                PopupMenuItem(value: 30, child: Text('30분')),
                PopupMenuItem(value: 60, child: Text('1시간')),
              ],
              child: const Padding(
                padding: EdgeInsets.all(8),
                child: Text('일시정지 시간'),
              ),
            ),
            Tooltip(
              message: '고정한 항목은 유지됩니다.',
              child: OutlinedButton(
                key: const ValueKey('kclip-clear-all'),
                onPressed: busy ? null : _confirmClearAll,
                child: const Text('모두 지우기'),
              ),
            ),
            TextButton(
              key: const ValueKey('kclip-disable'),
              onPressed: busy
                  ? null
                  : () => _act('disable', null, '몽땅클립보드를 껐습니다.'),
              child: const Text('끄기'),
            ),
          ],
        ),
        const SizedBox(height: 4),
        if (!hotkeyMode) _settings(context),
        Wrap(spacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
          FilledButton.icon(
            key: const ValueKey('kclip-excel-table'),
            onPressed: busy ? null : _convertExcel,
            icon: const Icon(Icons.table_view),
            label: const Text('엑셀 표를 한/글 표로'),
          ),
        ]),
        Wrap(alignment: WrapAlignment.spaceBetween, crossAxisAlignment: WrapCrossAlignment.center,
          children: [
            Wrap(spacing: 2, children: [for (final c in const ['전체','글','그림','파일','폴더','웹'])
              TextButton(key: ValueKey('kclip-category-$c'), onPressed: () => setState(() => category = c),
                style: TextButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 7)),
                child: Text(c, style: TextStyle(fontWeight: category == c ? FontWeight.bold : null))) ]),
            SizedBox(width: 210, child: TextField(
              decoration: const InputDecoration(prefixIcon: Icon(Icons.search), hintText: '키워드 검색', isDense: true),
              onChanged: (v) { query = v.trim(); _debounce?.cancel(); _debounce = Timer(const Duration(milliseconds: 200), () => unawaited(_reload())); },
            )),
          ],
        ),
        const SizedBox(height: 4),
        SizedBox(
          height: 220,
          child: visibleItems.isEmpty
              ? const Center(child: Text('기록된 항목이 없습니다.'))
              : ListView.builder(
              itemCount: visibleItems.length,
                  itemBuilder: (context, index) {
                    final item = visibleItems[index];
                    final pinned = item['pinned'] == true;
                    final id = (item['id'] as num).toInt();
                    final thumb = item['kind'] == 'image' ? _images[id] : null;
                    if (item['kind'] == 'image' &&
                        !_images.containsKey(id) &&
                        !_loadingImages.contains(id)) {
                      WidgetsBinding.instance.addPostFrameCallback((_) {
                        if (mounted) unawaited(_imageFor(id));
                      });
                    }
                    return GestureDetector(
                      onDoubleTap: _isWebText(item) ? () => unawaited(_openWeb(item)) : null,
                      child: ListTile(
                      key: ValueKey('kclip-item-${item['id']}'),
                      dense: true,
                      leading: Tooltip(
                        message: _kind(item['kind']),
                        child: thumb == null
                            ? Icon(_kindIcon(item['kind']))
                            : Image.memory(
                                thumb,
                                width: 48,
                                height: 48,
                                fit: BoxFit.cover,
                              ),
                      ),
                      title: Text(
                        '${item['preview'] ?? ''}',
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                      onTap: () => _preview(item),
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                            tooltip: pinned ? '고정 풀기' : '고정(지워지지 않음)',
                            onPressed: () => _act('pin', {
                              'id': item['id'],
                              'pinned': !pinned,
                            }),
                            icon: Icon(
                              pinned ? Icons.push_pin : Icons.push_pin_outlined,
                            ),
                          ),
                          IconButton(
                            tooltip: '지우기',
                            onPressed: () => _act('delete', {'id': item['id']}),
                            icon: const Icon(Icons.delete_outline),
                          ),
                        ],
                      ),
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
    if (hotkeyMode) unawaited(_setNativeDropTarget('kclip'));
    return Padding(
      padding: EdgeInsets.zero,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: const EdgeInsets.fromLTRB(6, 2, 2, 2),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surfaceContainerHighest,
              border: Border(
                bottom: BorderSide(
                  color: Theme.of(context).colorScheme.outlineVariant,
                ),
              ),
            ),
            child: Row(
              children: [
                const Spacer(),
                IconButton(
                  tooltip: isTop ? '항상 위 해제' : '항상 위',
                  onPressed: () => setState(() => isTop = !isTop),
                  icon: Icon(isTop ? Icons.push_pin : Icons.push_pin_outlined),
                ),
                IconButton(
                  tooltip: minimized ? '창 펼치기' : '최소화',
                  onPressed: () => setState(() => minimized = !minimized),
                  icon: Icon(minimized ? Icons.expand_more : Icons.minimize),
                ),
                IconButton(
                  key: const ValueKey('kclip-maximize'),
                  tooltip: maximized ? '이전 크기로 복원' : '최대화',
                  onPressed: _toggleMaximize,
                  icon: Icon(maximized ? Icons.filter_none : Icons.crop_square),
                ),
                IconButton(
                  tooltip: '닫기',
                  onPressed: () => Navigator.of(context).maybePop(),
                  icon: const Icon(Icons.close),
                ),
              ],
            ),
          ),
          if (!minimized)
        Expanded(
              child: SingleChildScrollView(
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      if (hotkeyMode) const SizedBox(height: 8),
                      if (hotkeyMode) TextField(
                        key: const ValueKey('kclip-memo'),
                        controller: _memo,
                        minLines: 1,
                        maxLines: 3,
                        decoration: InputDecoration(
                          labelText: '메모 작성',
                          hintText: '내용을 입력하고 추가를 누르세요',
                          suffixIcon: IconButton(
                            tooltip: '메모 추가',
                            onPressed: busy ? null : _addMemo,
                            icon: const Icon(Icons.add),
                          ),
                        ),
                        onSubmitted: (_) => _addMemo(),
                      ),
                      if (hotkeyMode) const SizedBox(height: 8),
                      if (hotkeyMode)
                      Container(
                          key: const ValueKey('kclip-drop-zone'),
                          padding: const EdgeInsets.symmetric(
                            vertical: 10,
                            horizontal: 12,
                          ),
                          decoration: BoxDecoration(
                            color: Theme.of(context).colorScheme.surfaceContainerHighest,
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(
                              color: Theme.of(context).colorScheme.outlineVariant,
                            ),
                          ),
                          child: const Row(
                            children: [
                              Icon(Icons.file_download_outlined),
                              SizedBox(width: 8),
                              Expanded(
                                child: Text('파일·폴더·이미지·웹 링크를 여기에 끌어 놓으세요'),
                              ),
                            ],
                          ),
                      ),
                      const SizedBox(height: 8),
                      if (status.isEmpty)
                        const Center(child: CircularProgressIndicator())
                      else if (running)
                        _on(context)
                      else
                        _off(context),
                      if (message.isNotEmpty)
                        Padding(
                          padding: const EdgeInsets.only(top: 8),
                          child: Text(
                            message,
                            key: const ValueKey('kclip-message'),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
