/// klib.exe 안의 Rust 편집 코어(editor_core, 파이프 명령 edit_*)를 쓰는 [EditorCore] 구현.
///
/// 설계(docs/EDITOR_CORE_DESIGN.md 6절)대로 화면의 `TextEditingController`가 글의 원본이고,
/// Rust 코어는 "이력·찾기·서식 계산"의 거울이다:
/// - 타자·IME 조합은 화면 값에서 바뀐 구간만 골라 `edit_replace`로 보낸다(UTF-16 → UTF-8 바이트 변환은 여기서).
///   한글 조합(ㅎ→하→한)은 같은 구간 교체라 Rust에서 한 실행취소 묶음이 된다.
/// - 실행취소·서식·찾기·바꾸기는 앞선 편집이 모두 반영된 뒤(요청 줄 세우기) Rust에 묻고, 바뀐 글을 다시 받아온다.
/// - klib가 유휴 종료돼 문서를 잃으면 지금 글로 `edit_open`을 다시 해 이어 간다(그 전 실행취소 기록은 사라짐).
///   다시 열 수도 없으면(klib 없음·요청 64 KiB 초과 등) [DartEditorCore]로 바꿔 끼워 계속 쓴다.
/// - 주기적으로 `edit_info`를 불러 klib를 깨워 두고, 글자 수가 어긋나면(드리프트) 다시 맞춘다.
library;

import 'dart:async';

import 'package:flutter/foundation.dart' show ChangeNotifier, Listenable;
import 'package:flutter/services.dart' show TextEditingValue, TextRange, TextSelection;

import 'editor_core.dart';
import 'markdown_format.dart' as md;
import 'markdown_format.dart' show PlainParagraph;
import 'text_offsets.dart';

/// edit_* 요청 하나를 보내고 응답(JSON 객체)을 돌려준다. 실패면 `ok:false`와 `message`.
typedef EditorBackend = Future<Map<String, Object?>> Function(Map<String, Object?> request);

class EditorBackendError implements Exception {
  EditorBackendError(this.message);
  final String message;

  /// klib가 다시 시작돼 문서 번호를 잃었는지(유휴 종료 뒤).
  bool get lostDocument => message.contains('찾을 수 없습니다');

  @override
  String toString() => message;
}

class _Notifier extends ChangeNotifier {
  void notify() => notifyListeners();
}

int _int(Object? v) => v is num ? v.toInt() : int.tryParse('$v') ?? 0;

class KlibEditorCore implements EditorCore {
  KlibEditorCore(this._backend, {String text = '', this.keepAlive = const Duration(seconds: 30), this.chunkLines = 400}) {
    final (normalized, _) = normalizeNewlines(text, const []);
    _value = TextEditingValue(text: normalized, selection: TextSelection.collapsed(offset: normalized.length));
    _mirror = normalized;
    // 원문(줄바꿈 그대로)을 보내야 Rust가 CRLF·LF를 감지해 기억한다. 내부 글은 LF.
    _ready = _enqueue(() => _open(text, mirror: normalized)).then(
      (_) {
        _notify(); // 상태 표시줄(줄바꿈·인코딩) 갱신
        return true;
      },
      onError: (Object e) {
        _fallBack();
        return false;
      },
    );
    if (keepAlive > Duration.zero) _timer = Timer.periodic(keepAlive, (_) => unawaited(_heartbeat()));
  }

  final EditorBackend _backend;

  /// klib 유휴 종료(기본 60초)를 막고 드리프트를 검사하는 주기. 0이면 끈다(시험용).
  final Duration keepAlive;

  /// 글을 다시 받아올 때 `edit_text`가 실패(응답 64 KiB 초과)하면 이만큼씩 줄로 나눠 받는다.
  final int chunkLines;

  late TextEditingValue _value;

  /// Rust 쪽에 지금까지 보낸 편집이 모두 반영된 글(요청 줄 순서 기준).
  late String _mirror;
  int? _doc;
  late final Future<bool> _ready;
  Future<void> _tail = Future.value();
  Timer? _timer;
  DartEditorCore? _fallback;
  bool _disposed = false;

  /// 다시 열 때마다 늘어난다. 그 전에 줄 선 편집은 새 문서에 두 번 들어가지 않게 건너뛴다.
  int _gen = 0;
  bool _needCommit = false;
  bool _canUndo = false;
  bool _canRedo = false;
  String _lineEnding = 'CRLF';
  String _encoding = 'UTF-8';
  final _changes = _Notifier();

  /// Rust 코어와 연결됐는지(열기 성공 여부). 시험·진단용.
  Future<bool> get ready => _ready;

  /// 폴백(Dart)으로 바뀌었는지.
  bool get fellBack => _fallback != null;

  @override
  TextEditingValue get value => _fallback?.value ?? _value;

  @override
  String get markdown => value.text;

  @override
  String get lineEnding => _fallback?.lineEnding ?? _lineEnding;

  @override
  String get encoding => _fallback?.encoding ?? _encoding;

  @override
  String get engineName => _fallback == null ? 'Rust' : 'Dart';

  @override
  Listenable get changes => _changes;

  @override
  bool get canUndo => _fallback?.canUndo ?? _canUndo;

  @override
  bool get canRedo => _fallback?.canRedo ?? _canRedo;

  @override
  int get blockStyle => md.currentBlockStyle(value);

  @override
  List<PlainParagraph> plainParagraphs() => md.markdownToPlainParagraphs(value.text);

  // ---- 요청 줄 ----

  /// 요청을 보낸 순서대로 하나씩 처리한다(앞 편집이 반영된 뒤에 다음 편집).
  Future<T> _enqueue<T>(Future<T> Function() job) {
    final run = _tail.then((_) => job());
    _tail = run.then((_) {}, onError: (Object _) {});
    return run;
  }

  Future<Map<String, Object?>> _send(String cmd, [Map<String, Object?> args = const {}]) async {
    final request = <String, Object?>{'cmd': cmd, 'doc': ?_doc, ...args};
    final Map<String, Object?> response;
    try {
      response = await _backend(request);
    } catch (e) {
      throw EditorBackendError('$e');
    }
    if (response['ok'] != true) throw EditorBackendError('${response['message'] ?? '편집 코어 요청이 실패했습니다.'}');
    _applyState(response);
    return response;
  }

  void _applyState(Map<String, Object?> r) {
    if (r['can_undo'] is bool) _canUndo = r['can_undo'] as bool;
    if (r['can_redo'] is bool) _canRedo = r['can_redo'] as bool;
    if (r['line_ending'] is String) _lineEnding = r['line_ending'] as String;
    if (r['encoding'] is String) _encoding = r['encoding'] as String;
  }

  Future<void> _open(String text, {String? mirror, String? lineEnding}) async {
    _doc = null;
    final r = await _send('edit_open', {'text': text, 'line_ending': ?lineEnding});
    _doc = _int(r['doc']);
    _mirror = mirror ?? text;
  }

  /// 편집이 실패했을 때: 지금 화면 글로 문서를 다시 연다. 그것도 안 되면 Dart 코어로 바꾼다.
  Future<void> _recover() async {
    if (_fallback != null || _disposed) return;
    _gen++;
    try {
      await _open(_value.text, lineEnding: _lineEnding); // 화면 글은 LF라 원래 줄바꿈 형식을 알려 준다
      _canUndo = false;
      _canRedo = false;
      _needCommit = false;
      _notify();
    } catch (_) {
      _fallBack();
    }
  }

  void _fallBack() {
    if (_fallback != null || _disposed) return;
    _timer?.cancel();
    _fallback = DartEditorCore(text: _value.text, selection: _value.selection);
    _notify();
  }

  void _notify() {
    if (!_disposed) _changes.notify();
  }

  /// 편집 요청 하나를 줄에 세우고, 실패하면 복구한다(호출한 쪽에는 오류를 올리지 않음).
  Future<void> _run(Future<void> Function() job) async {
    final ok = await _ready;
    if (!ok || _fallback != null || _disposed) return;
    final gen = _gen;
    try {
      await _enqueue(() async {
        if (gen == _gen && _fallback == null) await job();
      });
    } catch (_) {
      await _enqueue(() async {
        if (gen == _gen) await _recover();
      });
    }
  }

  Future<void> _heartbeat() => _run(() async {
    final r = await _send('edit_info');
    // 화면에 보낸 편집이 다 반영된 시점이라 _mirror와 Rust 글자 수가 같아야 한다.
    if (_int(r['chars']) != _mirror.runes.length) throw EditorBackendError('편집 코어 내용이 화면과 어긋났습니다.');
  });

  // ---- 입력 ----

  @override
  void updateFromInput(TextEditingValue next) {
    final fb = _fallback;
    if (fb != null) {
      fb.updateFromInput(next);
      return;
    }
    if (next.text.contains('\r')) {
      final (text, o) = normalizeNewlines(next.text, [
        next.selection.baseOffset, next.selection.extentOffset, next.composing.start, next.composing.end, //
      ]);
      next = TextEditingValue(
        text: text,
        selection: next.selection.copyWith(baseOffset: o[0], extentOffset: o[1]),
        composing: next.composing.isValid ? TextRange(start: o[2], end: o[3]) : TextRange.empty,
      );
    }
    final before = _value.text;
    _value = next;
    if (next.text == before) {
      if (!next.composing.isValid) _needCommit = true; // 커서 이동 = 입력 묶음 경계
      return;
    }
    // 바뀐 구간 하나(공통 앞·뒤를 뺀 나머지). 대리 쌍을 가르지 않게 맞춘다.
    final after = next.text;
    var p = 0;
    final maxP = before.length < after.length ? before.length : after.length;
    while (p < maxP && before.codeUnitAt(p) == after.codeUnitAt(p)) {
      p++;
    }
    var s = 0;
    while (s < maxP - p && before.codeUnitAt(before.length - 1 - s) == after.codeUnitAt(after.length - 1 - s)) {
      s++;
    }
    if (p > 0 && _isLowSurrogate(before, p)) p--;
    if (s > 0 && _isLowSurrogate(before, before.length - s)) s--;
    final oldEnd = before.length - s;
    final inserted = after.substring(p, after.length - s);
    final startByte = utf8Length(before, 0, p);
    final endByte = startByte + utf8Length(before, p, oldEnd);
    final commit = _needCommit;
    _needCommit = false;
    _canUndo = true;
    _canRedo = false;
    unawaited(
      _run(() async {
        if (commit) await _send('edit_commit');
        await _send('edit_replace', {'start': startByte, 'end': endByte, 'text': inserted});
        _mirror = _mirror.replaceRange(p, oldEnd, inserted);
      }),
    );
  }

  static bool _isLowSurrogate(String s, int i) {
    if (i <= 0 || i >= s.length) return false;
    final u = s.codeUnitAt(i);
    final h = s.codeUnitAt(i - 1);
    return u >= 0xDC00 && u <= 0xDFFF && h >= 0xD800 && h <= 0xDBFF;
  }

  @override
  void breakUndoGroup() {
    final fb = _fallback;
    if (fb != null) return fb.breakUndoGroup();
    if (!_value.composing.isValid) _needCommit = true;
  }

  // ---- Rust에 묻고 글을 다시 받는 명령 ----

  /// Rust 문서 전체 글. `edit_text` 응답이 너무 크면 줄 단위로 나눠 받는다.
  Future<String> _fetchText() async {
    try {
      return '${(await _send('edit_text'))['text'] ?? ''}';
    } on EditorBackendError catch (e) {
      if (e.lostDocument) rethrow;
    }
    final lines = _int((await _send('edit_info'))['lines']);
    final out = <String>[];
    for (var from = 0; from < lines; from += chunkLines) {
      final r = await _send('edit_lines', {'from': from, 'to': from + chunkLines});
      for (final row in (r['lines'] as List? ?? const [])) {
        out.add('${(row as Map)['text'] ?? ''}');
      }
    }
    return out.join('\n');
  }

  /// 명령 뒤 글을 받아 화면 값으로 삼는다. 선택은 바이트 위치로 받는다.
  Future<void> _reload(int selStartByte, int selEndByte) async {
    final text = await _fetchText();
    _mirror = text;
    _value = TextEditingValue(
      text: text,
      selection: TextSelection(baseOffset: utf8ToUtf16(text, selStartByte), extentOffset: utf8ToUtf16(text, selEndByte)),
    );
  }

  /// 앞선 입력이 다 반영된 뒤의 선택(바이트). 조합 중인 글은 확정으로 본다.
  (int, int) _selectionBytes() {
    final sel = _value.selection;
    final text = _mirror;
    final a = sel.isValid ? sel.start.clamp(0, text.length) : text.length;
    final b = sel.isValid ? sel.end.clamp(0, text.length) : text.length;
    return (utf16ToUtf8(text, a), utf16ToUtf8(text, b));
  }

  Future<void> _command(String cmd, Map<String, Object?> Function(int start, int end) args) => _run(() async {
    final (a, b) = _selectionBytes();
    final r = await _send(cmd, args(a, b));
    final cursor = _int(r['cursor']);
    await _reload(r.containsKey('sel_start') ? _int(r['sel_start']) : cursor, r.containsKey('sel_end') ? _int(r['sel_end']) : cursor);
    _needCommit = false;
  });

  @override
  Future<void> apply(EditorCommand command) async {
    final fb = _fallback;
    if (fb != null) return fb.apply(command);
    Map<String, Object?> range(int a, int b) => {'start': a, 'end': b};
    await switch (command) {
      EditorCommand.bold => _command('edit_md_inline', (a, b) => {...range(a, b), 'kind': 'bold'}),
      EditorCommand.italic => _command('edit_md_inline', (a, b) => {...range(a, b), 'kind': 'italic'}),
      EditorCommand.inlineCode => _command('edit_md_inline', (a, b) => {...range(a, b), 'kind': 'code'}),
      EditorCommand.codeBlock => _command('edit_md_code_block', range),
      EditorCommand.bulletList => _command('edit_md_block', (a, b) => {...range(a, b), 'kind': 'bullet'}),
      EditorCommand.numberedList => _command('edit_md_block', (a, b) => {...range(a, b), 'kind': 'number'}),
      EditorCommand.quote => _command('edit_md_block', (a, b) => {...range(a, b), 'kind': 'quote'}),
      EditorCommand.horizontalRule => _command('edit_md_rule', (a, b) => {'pos': b}),
      EditorCommand.clearFormatting => _command('edit_md_clear', range),
    };
    _notify();
  }

  @override
  Future<void> setBlockStyle(int level) async {
    final fb = _fallback;
    if (fb != null) return fb.setBlockStyle(level);
    await _command(
      'edit_md_block',
      (a, b) => {'start': a, 'end': b, 'kind': level <= 0 ? 'paragraph' : 'heading', 'level': level <= 0 ? 1 : level},
    );
  }

  @override
  Future<void> insertLink(String url) async {
    final fb = _fallback;
    if (fb != null) return fb.insertLink(url);
    if (url.trim().isEmpty) return;
    await _command('edit_md_link', (a, b) => {'start': a, 'end': b, 'url': url.trim()});
  }

  Future<void> _history(String cmd) => _run(() async {
    final r = await _send(cmd);
    if (r['changed'] == true) {
      final c = _int(r['cursor']);
      await _reload(c, c);
    }
    _needCommit = false;
  });

  @override
  Future<void> undo() async {
    final fb = _fallback;
    if (fb != null) return fb.undo();
    await _history('edit_undo');
  }

  @override
  Future<void> redo() async {
    final fb = _fallback;
    if (fb != null) return fb.redo();
    await _history('edit_redo');
  }

  // ---- 찾기·바꾸기 ----

  void _selectBytes(int a, int b) {
    _value = _value.copyWith(
      selection: TextSelection(baseOffset: utf8ToUtf16(_mirror, a), extentOffset: utf8ToUtf16(_mirror, b)),
      composing: TextRange.empty,
    );
  }

  TextRange get _selectionRange => TextRange(start: _value.selection.start, end: _value.selection.end);

  @override
  Future<TextRange?> find(String query, FindOptions options, {bool backward = false}) async {
    final fb = _fallback;
    if (fb != null) return fb.find(query, options, backward: backward);
    if (query.isEmpty) return null;
    TextRange? found;
    await _run(() async {
      final (a, b) = _selectionBytes();
      if (backward) {
        // Rust 코어에 거꾸로 찾기가 없어 모든 일치에서 고른다(최대 10000개).
        final r = await _send('edit_find_all', {'query': query, ...options.toJson()});
        final all = [for (final m in (r['matches'] as List? ?? const [])) (_int((m as Map)['start']), _int(m['end']))];
        if (all.isEmpty) return;
        final before = all.where((m) => m.$1 < a);
        final m = before.isEmpty ? all.last : before.last;
        _selectBytes(m.$1, m.$2);
      } else {
        final r = await _send('edit_find', {'query': query, 'from': b, 'wrap': true, ...options.toJson()});
        if (r['found'] != true) return;
        _selectBytes(_int(r['start']), _int(r['end']));
      }
      found = _selectionRange;
    });
    return found;
  }

  @override
  Future<bool> replaceNext(String query, String replacement, FindOptions options) async {
    final fb = _fallback;
    if (fb != null) return fb.replaceNext(query, replacement, options);
    if (query.isEmpty) return false;
    var replaced = false;
    await _run(() async {
      final (a, b) = _selectionBytes();
      final hit = await _send('edit_find', {'query': query, 'from': a, 'wrap': true, ...options.toJson()});
      if (hit['found'] != true) return;
      final (s, e) = (_int(hit['start']), _int(hit['end']));
      if (s != a || e != b) {
        _selectBytes(s, e); // 메모장처럼 첫 번째는 선택만
        return;
      }
      final r = await _send('edit_replace_next', {'query': query, 'with': replacement, 'from': a, 'wrap': false, ...options.toJson()});
      if (r['replaced'] != true) return;
      replaced = true;
      final cursor = _int(r['cursor']);
      await _reload(cursor, cursor);
      final next = await _send('edit_find', {'query': query, 'from': cursor, 'wrap': true, ...options.toJson()});
      if (next['found'] == true) _selectBytes(_int(next['start']), _int(next['end']));
      _needCommit = false;
    });
    _notify();
    return replaced;
  }

  @override
  Future<int> replaceAll(String query, String replacement, FindOptions options) async {
    final fb = _fallback;
    if (fb != null) return fb.replaceAll(query, replacement, options);
    if (query.isEmpty) return 0;
    var count = 0;
    await _run(() async {
      final (a, _) = _selectionBytes();
      final r = await _send('edit_replace_all', {'query': query, 'with': replacement, ...options.toJson()});
      count = _int(r['count']);
      if (count > 0) {
        final text = await _fetchText();
        final caret = utf8ToUtf16(text, a).clamp(0, text.length);
        _mirror = text;
        _value = TextEditingValue(text: text, selection: TextSelection.collapsed(offset: caret));
      }
      _needCommit = false;
    });
    _notify();
    return count;
  }

  @override
  Future<int> countMatches(String query, FindOptions options) async {
    final fb = _fallback;
    if (fb != null) return fb.countMatches(query, options);
    if (query.isEmpty) return 0;
    var count = 0;
    await _run(() async {
      // 개수만 필요하지만 Rust 코어에 개수 전용 명령이 없어 구간을 1개만 달라고 할 수 없다(limit은 개수 상한).
      final r = await _send('edit_find_all', {'query': query, 'limit': 10000, ...options.toJson()});
      count = _int(r['count']);
    });
    return count;
  }

  @override
  void dispose() {
    if (_disposed) return;
    _timer?.cancel();
    final doc = _doc;
    if (_fallback == null && doc != null) {
      unawaited(_enqueue(() => _send('edit_close')).then((_) {}, onError: (Object _) {}));
    }
    _disposed = true;
    _fallback?.dispose();
    _changes.dispose();
  }
}
