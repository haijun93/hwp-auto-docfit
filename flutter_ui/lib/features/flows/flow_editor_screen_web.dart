import '../../core/close_guards.dart';
import 'edit_save_state.dart';
import 'dart:async';
import 'dart:convert';
import 'dart:js_interop';
import 'dart:math';
import 'dart:ui_web' as ui_web;
import 'package:flutter/material.dart';
import 'package:web/web.dart' as web;
import '../../core/api/abbreviation_api.dart';

class FlowEditorScreen extends StatefulWidget {
  const FlowEditorScreen({super.key, required this.api});
  final ApiCall api;
  @override
  State<FlowEditorScreen> createState() => _FlowEditorScreenState();
}

class _FlowEditorScreenState extends State<FlowEditorScreen> {
  late final String viewType;
  late final web.HTMLIFrameElement frame;
  late final JSFunction listener;
  String name = '새 표/다이어그램';
  String? identity, revision;
  final saveState = EditSaveState();
  bool dirty = false, ready = false, busy = false;
  late final CloseLease _closeLease;
  Future<bool> _prepareHostClose() async {
    if (saveState.saving || busy || !canCloseEditor(context)) return false;
    if (!await confirmDiscard() || !mounted) return false;
    Navigator.of(context).pop();
    return true;
  }

  @override
  void initState() {
    super.initState();
    _closeLease = CloseGuards.register(_prepareHostClose);
    viewType = 'docfit-flow-${DateTime.now().microsecondsSinceEpoch}';
    frame = web.HTMLIFrameElement()
      ..src = Uri.base
          .resolve('assets/assets/flow_editor/index.html')
          .toString()
      ..title = '표/다이어그램 편집기'
      ..setAttribute('sandbox', 'allow-scripts allow-same-origin')
      ..style.border = '0'
      ..style.width = '100%'
      ..style.height = '100%';
    ui_web.platformViewRegistry.registerViewFactory(viewType, (_) => frame);
    listener = ((web.MessageEvent event) {
      if (event.origin != web.window.location.origin ||
          event.source != frame.contentWindow) {
        return;
      }
      final data = event.data.dartify();
      if (data is Map) unawaited(handle(data));
    }).toJS;
    web.window.addEventListener('message', listener);
  }

  Future<Object?> storage(
    String action, [
    Map<String, Object?> payload = const {},
  ]) => widget.api('flow_editor', [action, payload]);
  void post(Map<String, Object?> data) => frame.contentWindow?.postMessage(
    data.jsify(),
    web.window.location.origin.toJS,
  );
  Future<T?> showHostDialog<T>({
    required BuildContext context,
    required WidgetBuilder builder,
  }) async {
    // HTML platform views otherwise receive clicks beneath Flutter modals.
    frame.style.pointerEvents = 'none';
    try {
      return await showDialog<T>(context: context, builder: builder);
    } finally {
      frame.style.pointerEvents = 'auto';
    }
  }

  Future<bool> confirmDiscard() async {
    if (!dirty) return true;
    return await showHostDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('저장하지 않은 변경사항'),
            content: const Text('현재 변경사항을 버릴까요?'),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: const Text('계속 편집'),
              ),
              FilledButton(
                onPressed: () => Navigator.pop(context, true),
                child: const Text('변경사항 버리기'),
              ),
            ],
          ),
        ) ??
        false;
  }

  Future<void> handle(Map message) async {
    final type = message['type'];
    if (type == 'ready') {
      if (mounted) setState(() => ready = true);
      return;
    }
    if (type == 'dirty') {
      if (mounted) {
        setState(() {
          saveState.event(message['generation'], message['value'] == true);
          dirty = saveState.dirty;
        });
      }
      return;
    }
    if (type == 'template_applied') {
      if (mounted) {
        setState(() {
          name = '${message['name']}';
          dirty = true;
        });
      }
      return;
    }
    if (type == 'editor_error') {
      notice('${message['message']}');
      return;
    }
    if (busy) return;
    busy = true;
    try {
      switch (type) {
        case 'request_new':
          if (await confirmDiscard()) {
            identity = null;
            revision = null;
            name = '새 표/다이어그램';
            dirty = false;
            post({'type': 'new'});
          }
          break;
        case 'request_template':
          if (await confirmDiscard()) {
            post({'type': 'apply_template', 'template': message['template']});
          }
          break;
        case 'request_list':
          await openSaved();
          break;
        case 'request_save':
          await save();
          break;
        case 'save_document':
          final selectedId =
              identity ??
              List.generate(
                16,
                (_) => Random.secure().nextInt(256),
              ).map((v) => v.toRadixString(16).padLeft(2, '0')).join();
          final targetGeneration = saveState.begin(message['generation']);
          if (mounted) setState(() {});
          Object? result;
          try {
            result = await storage('save', {
              'id': selectedId,
              'name': message['name'],
              'snapshot': message['snapshot'],
              'revision': revision,
            });
            if (result is! Map ||
                result["id"] is! String ||
                result["name"] is! String ||
                result['revision'] is! String) {
              throw Exception("저장 응답을 확인해 주세요.");
            }
          } catch (_) {
            saveState.complete(targetGeneration, success: false);
            rethrow;
          }
          saveState.complete(targetGeneration, success: true);
          identity = result['id'] as String;
          revision = result['revision'] as String;
          name = result['name'] as String;
          dirty = saveState.dirty;
          post({'type': 'mark_saved', 'generation': targetGeneration});
          notice('표/다이어그램을 이 PC에 저장했어요.');
          break;
        case 'copy_result':
          final copied = await storage('copy_result', {
            'kind': message['kind'],
            if (message['spec'] != null) 'spec': message['spec'],
            if (message['base64'] != null) 'base64': message['base64'],
          });
          if (copied is Map && copied['copied'] == true) {
            notice('복사했어요. 한/글 2020에서 Ctrl+V로 붙여넣으세요.');
          }
          break;
        case 'request_png':
          post({'type': 'export_png'});
          break;
        case 'export_hwpx':
          // 표/다이어그램의 흐름표·기본 표를 한/글 문서로 저장한다(검증은 Python table_builder).
          final spec = message['spec'];
          if (spec is! Map) throw Exception('표 정보를 확인해 주세요.');
          final saved = await storage('export_hwpx', {'spec': spec, 'name': name});
          if (saved is Map && saved['path'] is String) {
            notice('한/글 문서로 저장했어요: ${saved['path']}');
          }
          break;
        case 'export_png':
          final encoded = message['base64'];
          if (encoded is! String || encoded.length > 28 * 1024 * 1024) {
            throw Exception('PNG 크기가 제한을 넘습니다.');
          }
          final bytes = base64Decode(encoded);
          if (bytes.length < 8 ||
              bytes.length > 20 * 1024 * 1024 ||
              bytes.take(8).join(',') != '137,80,78,71,13,10,26,10') {
            throw Exception('PNG 형식이 올바르지 않습니다.');
          }
          final result = await storage('export_png', {
            'base64': encoded,
            'name': name,
          });
          if (result is Map && result['path'] is String) {
            notice('PNG를 저장했어요: ${result['path']}');
          }
          break;
      }
      if (mounted) setState(() {});
    } catch (error) {
      notice('표/다이어그램 작업에 실패했어요: $error');
    } finally {
      busy = false;
      if (mounted) setState(() {});
    }
  }

  void notice(String message) {
    if (mounted) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(message)));
    }
  }

  Future<void> save({bool asCopy = false}) async {
    final input = TextEditingController(text: name);
    final selected = await showHostDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('표/다이어그램 저장'),
        content: TextField(
          controller: input,
          autofocus: true,
          maxLength: 120,
          decoration: const InputDecoration(labelText: '문서 이름'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('취소'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, input.text.trim()),
            child: const Text('저장'),
          ),
        ],
      ),
    );
    input.dispose();
    if (selected != null && selected.isNotEmpty) {
      if (asCopy) {
        identity = null;
        revision = null;
      }
      post({'type': 'save', 'id': identity, 'name': selected});
    }
  }

  Future<void> openSaved() async {
    final list = await storage('list');
    if (list is! List || !mounted) return;
    final result = await showHostDialog<Map>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('저장된 표/다이어그램'),
        content: SizedBox(
          width: 520,
          height: 360,
          child: list.isEmpty
              ? const Center(child: Text('저장된 표/다이어그램이 없어요.'))
              : ListView(
                  children: [
                    for (final item in list)
                      ListTile(
                        title: Text('${item['name']}'),
                        onTap: () => Navigator.pop(context, {'id': item['id']}),
                        trailing: IconButton(
                          tooltip: '삭제',
                          icon: const Icon(Icons.delete_outline),
                          onPressed: () => Navigator.pop(context, {
                            'delete': item['id'],
                            'name': item['name'],
                          }),
                        ),
                      ),
                  ],
                ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('닫기'),
          ),
        ],
      ),
    );
    if (result == null) return;
    if (result.containsKey('delete')) {
      if (!mounted) return;
      final approved = await showHostDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('표/다이어그램 삭제'),
          content: Text('${result['name']}을 삭제할까요?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('취소'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('삭제'),
            ),
          ],
        ),
      );
      if (approved == true) {
        await storage('delete', {'id': result['delete']});
        if (identity == result['delete']) {
          identity = null;
          revision = null;
          dirty = true;
        }
      }
      return;
    }
    if (!await confirmDiscard()) return;
    final loaded = await storage('load', {'id': result['id']});
    if (loaded is! Map) throw Exception('표/다이어그램 응답을 확인해 주세요.');
    identity = loaded['id'] as String;
    revision = loaded['revision'] as String;
    name = loaded['name'] as String;
    dirty = false;
    post({
      'type': 'load',
      'id': identity,
      'name': name,
      'snapshot': loaded['snapshot'],
    });
  }

  @override
  Widget build(BuildContext context) => PopScope(
    canPop: !dirty && !saveState.saving,
    onPopInvokedWithResult: (didPop, result) async {
      if (!didPop &&
          !saveState.saving &&
          await confirmDiscard() &&
          context.mounted) {
        Navigator.pop(context);
      }
    },
    child: Scaffold(
      appBar: AppBar(
        title: Text(name),
        actions: [
          IconButton(
            tooltip: '사본으로 저장',
            icon: const Icon(Icons.copy),
            onPressed: ready && !busy && !saveState.saving
                ? () => save(asCopy: true)
                : null,
          ),
        ],
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () async {
            if (!saveState.saving &&
                await confirmDiscard() &&
                context.mounted) {
              Navigator.pop(context);
            }
          },
        ),
      ),
      body: Stack(
        children: [
          HtmlElementView(viewType: viewType),
          if (!ready) const Center(child: CircularProgressIndicator()),
        ],
      ),
    ),
  );
  @override
  void dispose() {
    _closeLease.release();
    web.window.removeEventListener('message', listener);
    super.dispose();
  }
}
