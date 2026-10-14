import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math';

import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:webview_flutter_windows/webview_flutter_windows.dart';

import '../../core/api/abbreviation_api.dart';

class DiagramEditorScreen extends StatefulWidget {
  const DiagramEditorScreen({
    super.key,
    required this.api,
    this.useTldraw = true,
  });
  final ApiCall api;
  final bool useTldraw;

  @override
  State<DiagramEditorScreen> createState() => _DiagramEditorScreenState();
}

class _DiagramEditorScreenState extends State<DiagramEditorScreen> {
  final controller = WebviewController();
  final subscriptions = <StreamSubscription<dynamic>>[];
  HttpServer? server;
  Set<String> assets = {};
  bool initialized = false;
  bool dirty = false;
  bool busy = true;
  String? diagramId;
  String name = '새 업무 흐름도';
  String? failure;

  @override
  void initState() {
    super.initState();
    initialize();
  }

  Future<void> initialize() async {
    try {
      // API를 다시 검사해 Flutter 메뉴 우회로의 비활성 기능 접근을 막는다.
      final state = await widget.api('get_state', const []);
      final options = state is Map ? state['options'] as Map? : null;
      if (widget.useTldraw &&
          (options?['developer_mode'] != true ||
              options?['diagram_editor_enabled'] != true)) {
        throw Exception('개발자 모드와 tldraw 도형 편집기 사용을 모두 켜 주세요.');
      }
      await storage('list');
      final manifest = await rootBundle.loadString(
        'assets/${widget.useTldraw ? 'diagram_editor' : 'flow_editor'}/asset-manifest.json',
      );
      final decoded = jsonDecode(manifest) as Map;
      assets = {'index.html'};
      for (final entry in decoded.values) {
        if (entry is Map) {
          for (final key in [
            'file',
            ...((entry['css'] as List?) ?? const []),
          ]) {
            if (key is String && !key.startsWith('/')) assets.add(key);
          }
          for (final key in (entry['assets'] as List?) ?? const []) {
            if (key is String && !key.startsWith('/')) assets.add(key);
          }
        }
      }
      server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      server!.listen(
        serveAsset,
        onError: (Object error) {
          if (mounted) setState(() => failure = '편집기 리소스를 열지 못했어요.');
        },
      );
      await controller.initialize();
      await controller.setPopupWindowPolicy(WebviewPopupWindowPolicy.deny);
      await controller.setBackgroundColor(const Color(0xfff4f7fb));
      subscriptions.add(controller.webMessage.listen(handleMessage));
      await controller.loadUrl('http://127.0.0.1:${server!.port}/index.html');
      if (mounted) {
        setState(() {
          initialized = true;
          busy = false;
        });
      }
    } catch (error) {
      if (mounted) {
        setState(() {
          failure = '$error';
          busy = false;
        });
      }
    }
  }

  Future<void> serveAsset(HttpRequest request) async {
    final raw = Uri.decodeComponent(
      request.uri.path.replaceFirst(RegExp(r'^/'), ''),
    );
    if (raw.isEmpty ||
        raw.contains('..') ||
        raw.contains('\\') ||
        raw.contains('\x00') ||
        !assets.contains(raw)) {
      request.response.statusCode = HttpStatus.notFound;
      await request.response.close();
      return;
    }
    try {
      final data = await rootBundle.load(
        'assets/${widget.useTldraw ? 'diagram_editor' : 'flow_editor'}/$raw',
      );
      final ext = raw.split('.').last.toLowerCase();
      request.response.headers
        ..set(HttpHeaders.contentTypeHeader, switch (ext) {
          'html' => 'text/html; charset=utf-8',
          'js' => 'text/javascript; charset=utf-8',
          'css' => 'text/css; charset=utf-8',
          'json' => 'application/json; charset=utf-8',
          'svg' => 'image/svg+xml',
          'woff2' => 'font/woff2',
          'png' => 'image/png',
          _ => 'application/octet-stream',
        })
        ..set('X-Content-Type-Options', 'nosniff')
        ..set(
          'Content-Security-Policy',
          "default-src 'self' data: blob:; script-src 'self' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'none'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        );
      request.response.add(
        data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes),
      );
      await request.response.close();
    } catch (_) {
      request.response.statusCode = HttpStatus.notFound;
      await request.response.close();
    }
  }

  Future<Object?> storage(
    String action, [
    Map<String, Object?> payload = const {},
  ]) {
    if (!widget.useTldraw) return widget.api('flow_editor', [action, payload]);
    return widget.api('diagram_$action', switch (action) {
      'list' => const [],
      'load' || 'delete' => [payload['id']],
      _ => [payload['id'], payload['name'], payload['snapshot']],
    });
  }

  void post(Map<String, Object?> message) {
    if (!controller.value.isInitialized) return;
    controller.postWebMessage(jsonEncode(message));
  }

  Future<void> handleMessage(dynamic event) async {
    dynamic message = event;
    if (message is String) {
      try {
        message = jsonDecode(message);
      } catch (_) {
        return;
      }
    }
    if (message is! Map) return;
    final type = message['type'];
    try {
      switch (type) {
        case 'ready':
          if (diagramId != null) {
            final loaded = await storage('load', {'id': diagramId});
            if (loaded is! Map) throw Exception('저장된 도형 문서 응답이 올바르지 않습니다.');
            name = loaded['name'] as String;
            post({
              'type': 'load',
              'id': diagramId,
              'name': name,
              'snapshot': loaded['snapshot'],
            });
          }
          break;
        case 'dirty':
          if (mounted) setState(() => dirty = message['value'] == true);
          break;
        case 'template_applied':
          if (mounted) {
            setState(() {
              name = '${message['name'] ?? '업무 흐름도'}';
              dirty = true;
            });
          }
          break;
        case 'request_new':
          if (await confirmDiscard()) {
            diagramId = null;
            name = '새 업무 흐름도';
            dirty = false;
            post({'type': 'new'});
            if (mounted) setState(() {});
          }
          break;
        case 'request_template':
          if (await confirmDiscard()) {
            post({'type': 'apply_template', 'template': message['template']});
          }
          break;
        case 'request_save':
          await saveDocument();
          break;
        case 'save_document':
          final id = diagramId ?? _newId();
          final saved = await storage('save', {
            'id': id,
            'name': message['name'],
            'snapshot': message['snapshot'],
          });
          if (saved is! Map) throw Exception('도형 저장 응답이 올바르지 않습니다.');
          diagramId = saved['id'] as String;
          name = saved['name'] as String;
          post({'type': 'mark_saved'});
          if (mounted) setState(() => dirty = false);
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('도형 문서를 이 PC에 저장했어요.')),
            );
          }
          break;
        case 'request_list':
          await showSavedDocuments();
          break;
        case 'request_png':
          post({'type': 'export_png'});
          break;
        case 'export_png':
          await savePng(message['base64'] as String? ?? '');
          break;
        case 'editor_error':
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('${message['message'] ?? '편집기 오류'}')),
            );
          }
          break;
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('도형 작업을 완료하지 못했어요: $error')));
      }
    }
  }

  String _newId() => List<int>.generate(
    16,
    (_) => Random.secure().nextInt(256),
  ).map((value) => value.toRadixString(16).padLeft(2, '0')).join();

  Future<bool> confirmDiscard() async {
    if (!dirty) return true;
    return await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('저장하지 않은 변경사항'),
            content: const Text('현재 다이어그램의 변경사항을 버릴까요? 저장하려면 먼저 저장을 선택하세요.'),
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

  Future<void> saveDocument() async {
    final input = TextEditingController(text: name);
    final selected = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('도형 문서 저장'),
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
    if (selected == null || selected.isEmpty) return;
    name = selected;
    post({'type': 'save', 'id': diagramId, 'name': name});
  }

  Future<void> showSavedDocuments() async {
    final items = await storage('list') as List;
    if (!mounted) return;
    final selected = await showDialog<Map>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('저장된 다이어그램'),
        content: SizedBox(
          width: 520,
          height: 360,
          child: items.isEmpty
              ? const Center(child: Text('저장된 문서가 없습니다.'))
              : ListView(
                  children: [
                    for (final raw in items)
                      ListTile(
                        title: Text('${raw['name']}'),
                        subtitle: Text('${raw['updated_at']}'),
                        trailing: IconButton(
                          tooltip: '삭제',
                          icon: const Icon(Icons.delete_outline),
                          onPressed: () => Navigator.pop(context, {
                            'delete': raw['id'],
                            'name': raw['name'],
                          }),
                        ),
                        onTap: () => Navigator.pop(
                          context,
                          Map<String, dynamic>.from(raw),
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
    if (selected == null) return;
    if (selected.containsKey('delete')) {
      if (!mounted) return;
      final approved = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('흐름도 삭제'),
          content: Text('${selected['name']}을 삭제할까요?'),
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
        await storage('delete', {'id': selected['delete']});
        if (diagramId == selected['delete']) {
          diagramId = null;
          if (mounted) setState(() => dirty = true);
        }
      }
      return;
    }
    if (!await confirmDiscard()) return;
    final loaded = await storage('load', {'id': selected['id']});
    if (loaded is! Map) throw Exception('저장된 도형 문서 응답이 올바르지 않습니다.');
    diagramId = selected['id'] as String;
    name = loaded['name'] as String;
    post({
      'type': 'load',
      'id': diagramId,
      'name': name,
      'snapshot': loaded['snapshot'],
    });
    if (mounted) setState(() => dirty = false);
  }

  Future<void> savePng(String encoded) async {
    if (encoded.isEmpty || encoded.length > 28 * 1024 * 1024) {
      throw Exception('PNG 크기가 허용 한도를 넘었습니다.');
    }
    final bytes = base64Decode(encoded);
    if (bytes.length < 8 ||
        bytes.length > 20 * 1024 * 1024 ||
        base64Encode(bytes) != encoded ||
        bytes.take(8).join(',') !=
            const [137, 80, 78, 71, 13, 10, 26, 10].join(',')) {
      throw Exception('PNG 데이터가 올바르지 않습니다.');
    }
    final location = await getSaveLocation(
      suggestedName:
          '${name.replaceAll(RegExp(r'[^가-힣A-Za-z0-9 _-]'), '_')}.png',
      acceptedTypeGroups: const [
        XTypeGroup(label: 'PNG 이미지', extensions: ['png']),
      ],
    );
    if (location == null) return;
    final target = File(location.path);
    final temporary = File('${location.path}.tmp');
    final backup = File('${location.path}.bak');
    await temporary.writeAsBytes(bytes, flush: true);
    var backedUp = false;
    try {
      if (await target.exists()) {
        await target.rename(backup.path);
        backedUp = true;
      }
      await temporary.rename(target.path);
      if (backedUp) await backup.delete();
    } catch (_) {
      if (backedUp && !await target.exists() && await backup.exists()) {
        await backup.rename(target.path);
      }
      rethrow;
    } finally {
      if (await temporary.exists()) await temporary.delete();
    }
    if (mounted) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('PNG를 저장했어요: ${target.path}')));
    }
  }

  @override
  Widget build(BuildContext context) => PopScope(
    canPop: !dirty,
    onPopInvokedWithResult: (didPop, result) async {
      if (!didPop && await confirmDiscard() && context.mounted) {
        Navigator.pop(context);
      }
    },
    child: Scaffold(
      appBar: AppBar(
        title: Text(name),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () async {
            if (await confirmDiscard() && context.mounted) {
              Navigator.pop(context);
            }
          },
        ),
      ),
      body: failure != null
          ? Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text('편집기를 시작하지 못했어요.\n$failure'),
              ),
            )
          : Stack(
              children: [
                if (initialized) Webview(controller),
                if (busy) const Center(child: CircularProgressIndicator()),
              ],
            ),
    ),
  );

  @override
  void dispose() {
    for (final subscription in subscriptions) {
      unawaited(subscription.cancel());
    }
    unawaited(controller.dispose());
    if (server != null) unawaited(server!.close(force: true));
    super.dispose();
  }
}
