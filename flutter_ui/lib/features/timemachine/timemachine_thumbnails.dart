import 'dart:collection';
import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'timemachine_api.dart';

/// 카드 썸네일 요청·메모리 캐시. 화면에 보이는 카드만 요청하고, 스크롤로 사라진 카드의 대기 요청은 버린다.
class TimemachineThumbnailLoader {
  TimemachineThumbnailLoader(this.api);
  static const maxConcurrent = 2, maxCached = 400, maxBytes = 1024 * 1024;
  final TimemachineApi api;
  final LinkedHashMap<String, Uint8List?> _cache = LinkedHashMap();
  final List<_Job> _waiting = [];
  int _running = 0;
  bool _disposed = false;

  static String keyOf(TimemachineItem item) => '${item.id}:${item.mtime}:${item.size}';
  bool contains(String key) => _cache.containsKey(key);

  /// 캐시에서 꺼내 맨 뒤로 옮긴다(오래 안 본 것부터 밀려나게).
  Uint8List? touch(String key) {
    if (!_cache.containsKey(key)) return null;
    final value = _cache.remove(key);
    _cache[key] = value;
    return value;
  }

  VoidCallback request(TimemachineItem item, void Function(Uint8List?) done) {
    final job = _Job(item, done);
    _waiting.add(job);
    _pump();
    return () { job.cancelled = true; _waiting.remove(job); };
  }

  void _pump() {
    while (!_disposed && _running < maxConcurrent && _waiting.isNotEmpty) {
      _run(_waiting.removeLast()); // 가장 최근에 화면에 들어온 카드부터
    }
  }

  Future<void> _run(_Job job) async {
    _running++;
    Uint8List? bytes;
    var keep = true;
    try {
      final response = await api.command('thumbnail', {'id': job.item.id});
      keep = response['retry'] != true; // 다른 PDF 작업과 겹쳤을 뿐이면 다음에 다시 요청한다
      if (response['ok'] == true) bytes = _decode(response['data']);
    } catch (_) {
      keep = false;
    }
    _running--;
    if (_disposed) return;
    if (keep) {
      _cache[keyOf(job.item)] = bytes;
      while (_cache.length > maxCached) { _cache.remove(_cache.keys.first); }
    }
    if (!job.cancelled) job.done(bytes);
    _pump();
  }

  static Uint8List? _decode(Object? data) {
    if (data is! String || data.length > maxBytes * 4 ~/ 3) return null;
    try {
      final bytes = base64Decode(data);
      return bytes.length > 3 && bytes[0] == 0xFF && bytes[1] == 0xD8 ? bytes : null;
    } on FormatException {
      return null;
    }
  }

  void dispose() { _disposed = true; _waiting.clear(); _cache.clear(); }
}

class _Job {
  _Job(this.item, this.done);
  final TimemachineItem item;
  final void Function(Uint8List?) done;
  bool cancelled = false;
}

class TimemachineThumbnail extends StatefulWidget {
  const TimemachineThumbnail({super.key, required this.item, required this.icon, required this.loader});
  final TimemachineItem item;
  final IconData icon;
  final TimemachineThumbnailLoader loader;
  @override
  State<TimemachineThumbnail> createState() => _TimemachineThumbnailState();
}

class _TimemachineThumbnailState extends State<TimemachineThumbnail> {
  Uint8List? _bytes;
  VoidCallback? _cancel;

  @override
  void initState() { super.initState(); _prepare(); }

  @override
  void didUpdateWidget(TimemachineThumbnail old) {
    super.didUpdateWidget(old);
    if (TimemachineThumbnailLoader.keyOf(old.item) != TimemachineThumbnailLoader.keyOf(widget.item)) {
      _cancel?.call();
      _bytes = null;
      _prepare();
    }
  }

  void _prepare() {
    final item = widget.item;
    if (item.cloud) return; // 클라우드 전용: 내용을 읽으면 내려받기가 시작된다
    final key = TimemachineThumbnailLoader.keyOf(item);
    if (widget.loader.contains(key)) { _bytes = widget.loader.touch(key); return; }
    _cancel = widget.loader.request(item, (bytes) {
      _cancel = null;
      if (mounted && bytes != null) setState(() => _bytes = bytes);
    });
  }

  @override
  void dispose() { _cancel?.call(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    final id = widget.item.id;
    final icon = Center(key: ValueKey('tm-thumb-icon-$id'), child: Icon(widget.icon));
    final bytes = _bytes;
    return SizedBox(width: 56, height: 56, child: bytes == null ? icon : ClipRRect(
      borderRadius: BorderRadius.circular(4),
      child: Image.memory(bytes, key: ValueKey('tm-thumb-$id'), fit: BoxFit.contain,
        gaplessPlayback: true, excludeFromSemantics: true,
        // 그림이 풀리기 전과 깨진 그림은 종류 아이콘으로 둔다(깜빡임 방지).
        frameBuilder: (context, child, frame, sync) => frame == null && !sync ? icon : child,
        errorBuilder: (context, error, stack) => icon),
    ));
  }
}
