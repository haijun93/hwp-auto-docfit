/// 메모 편집기 코어 경계(EditorCore)와 Dart 임시 구현(DartEditorCore).
///
/// 경계 원칙(docs/EDITOR_CORE_DESIGN.md 6절):
/// - 글자 입력·한글 IME 조합·선택·커서 그리기는 Flutter `TextField`(EditableText)가 맡는다.
/// - 코어는 본문 버퍼(Markdown 원문)·선택·실행취소 이력·서식 명령·찾기/바꾸기·평문 변환만 맡는다.
/// - 기본 구현은 klib.exe 안의 Rust 편집 코어([KlibEditorCore], `klib_editor_core.dart`)이고,
///   klib를 쓸 수 없으면 이 파일의 [DartEditorCore]가 폴백으로 같은 일을 한다.
///   화면(`memo_editor.dart`)은 [EditorCore]만 알고 구현을 모른다.
///
/// 서식·실행취소·찾기 명령은 Rust 코어가 파이프 왕복을 하므로 `Future`를 돌려준다.
/// Dart 구현은 `async` 본문이 첫 `await` 전까지 바로 실행되므로 호출 직후 [EditorCore.value]가 이미 바뀌어 있다.
library;

import 'package:flutter/foundation.dart' show ChangeNotifier, Listenable;
import 'package:flutter/services.dart' show TextEditingValue, TextRange, TextSelection;

import 'markdown_format.dart' as md;
import 'markdown_format.dart' show PlainParagraph;
import 'text_offsets.dart';

export 'text_offsets.dart' show FindOptions;

/// 도구줄 서식 명령. 문단 형식(제목)과 링크는 값이 필요해 [EditorCore.setBlockStyle]·[EditorCore.insertLink]로 따로 둔다.
enum EditorCommand { bold, italic, inlineCode, codeBlock, bulletList, numberedList, quote, horizontalRule, clearFormatting }

abstract class EditorCore {
  /// 현재 본문(Markdown 원문)과 선택.
  TextEditingValue get value;

  /// 입력 칸에서 바뀐 값을 알린다(타자·붙여넣기·IME 조합·커서 이동). 코어는 이력 묶음을 정한다.
  /// IME 조합 중(composing)인 값은 조합이 끝날 때까지 한 묶음으로 둔다.
  /// 코어가 값을 고칠 수 있다(예: Rust 코어는 줄바꿈을 LF로 맞춤) — 화면은 호출 뒤 [value]를 다시 읽는다.
  void updateFromInput(TextEditingValue next);

  /// 지금까지의 입력 묶음을 닫는다(잠시 멈춤 등). 다음 입력은 새 실행취소 단계가 된다.
  void breakUndoGroup();

  Future<void> apply(EditorCommand command);
  Future<void> setBlockStyle(int level);
  Future<void> insertLink(String url);

  /// 커서 줄의 문단 형식(0=보통, 1~3=제목).
  int get blockStyle;

  bool get canUndo;
  bool get canRedo;
  Future<void> undo();
  Future<void> redo();

  /// 다음(또는 [backward]면 이전) 일치를 찾아 선택한다. 끝에 닿으면 처음부터 다시 찾는다. 없으면 null.
  Future<TextRange?> find(String query, FindOptions options, {bool backward = false});

  /// 메모장의 '바꾸기': 선택이 일치 구간이면 바꾸고 다음 일치를 선택한다(true).
  /// 아니면 다음 일치를 선택만 한다(false).
  Future<bool> replaceNext(String query, String replacement, FindOptions options);

  /// 모두 바꾸기(한 번의 실행취소). 바꾼 개수.
  Future<int> replaceAll(String query, String replacement, FindOptions options);

  /// 일치 개수(최대 10000).
  Future<int> countMatches(String query, FindOptions options);

  /// 상태 표시줄용: 저장 시 줄바꿈(CRLF·LF·CR)과 인코딩, 코어 이름('Rust'·'Dart').
  String get lineEnding;
  String get encoding;
  String get engineName;

  /// 코어가 스스로 값·상태를 바꿨을 때 알린다(Rust 코어 연결·폴백 전환, 상태값 갱신).
  Listenable get changes;

  /// 저장할 Markdown 원문.
  String get markdown => value.text;

  /// 검색 색인용 평문 문단.
  List<PlainParagraph> plainParagraphs();

  void dispose();
}

/// Dart로 쓴 임시 코어(klib가 없을 때 폴백). 실행취소는 값 스냅숏 묶음(최대 [maxHistory]단계).
class DartEditorCore implements EditorCore {
  DartEditorCore({String text = '', this.maxHistory = 200, TextSelection? selection})
    : _value = TextEditingValue(text: text, selection: selection ?? TextSelection.collapsed(offset: text.length));

  final int maxHistory;
  TextEditingValue _value;
  final _undo = <TextEditingValue>[];
  final _redo = <TextEditingValue>[];
  bool _grouping = false;
  final _changes = ChangeNotifier();

  @override
  TextEditingValue get value => _value;

  @override
  String get markdown => _value.text;

  @override
  String get lineEnding => 'CRLF';

  @override
  String get encoding => 'UTF-8';

  @override
  String get engineName => 'Dart';

  @override
  Listenable get changes => _changes;

  void _push(TextEditingValue snapshot) {
    _undo.add(snapshot.copyWith(composing: TextRange.empty));
    if (_undo.length > maxHistory) _undo.removeAt(0);
    _redo.clear();
  }

  @override
  void updateFromInput(TextEditingValue next) {
    if (next.text == _value.text) {
      // 커서만 옮겼으면 이력은 그대로 두고 입력 묶음만 닫는다(조합 중이면 유지).
      if (next.selection != _value.selection && !next.composing.isValid) _grouping = false;
      _value = next;
      return;
    }
    if (!_grouping) {
      _push(_value);
      _grouping = true;
    }
    _value = next;
    // 줄바꿈을 넣으면 그 줄까지 한 단계로 끊는다(조합 중이 아닐 때).
    if (!next.composing.isValid && next.text.isNotEmpty && next.selection.isValid) {
      final caret = next.selection.baseOffset;
      if (caret > 0 && caret <= next.text.length && next.text[caret - 1] == '\n') _grouping = false;
    }
  }

  @override
  void breakUndoGroup() {
    if (!_value.composing.isValid) _grouping = false;
  }

  void _edit(TextEditingValue Function(TextEditingValue v) change) {
    final base = _value.copyWith(composing: TextRange.empty);
    final next = change(base);
    _grouping = false;
    if (next.text == base.text) {
      _value = next;
      return;
    }
    _push(base);
    _value = next;
  }

  @override
  Future<void> apply(EditorCommand command) async => _edit(
    (v) => switch (command) {
      EditorCommand.bold => md.toggleInline(v, '**'),
      EditorCommand.italic => md.toggleInline(v, '*'),
      EditorCommand.inlineCode => md.toggleInline(v, '`', placeholder: '코드'),
      EditorCommand.codeBlock => md.insertCodeBlock(v),
      EditorCommand.bulletList => md.toggleLinePrefix(v, md.MemoListKind.bullet),
      EditorCommand.numberedList => md.toggleLinePrefix(v, md.MemoListKind.numbered),
      EditorCommand.quote => md.toggleLinePrefix(v, md.MemoListKind.quote),
      EditorCommand.horizontalRule => md.insertHorizontalRule(v),
      EditorCommand.clearFormatting => md.clearFormatting(v),
    },
  );

  @override
  Future<void> setBlockStyle(int level) async => _edit((v) => md.setBlockStyle(v, level));

  @override
  Future<void> insertLink(String url) async {
    if (url.trim().isEmpty) return;
    _edit((v) => md.insertLink(v, url));
  }

  @override
  int get blockStyle => md.currentBlockStyle(_value);

  @override
  bool get canUndo => _undo.isNotEmpty;

  @override
  bool get canRedo => _redo.isNotEmpty;

  @override
  Future<void> undo() async {
    if (_undo.isEmpty) return;
    _grouping = false;
    _redo.add(_value.copyWith(composing: TextRange.empty));
    _value = _undo.removeLast();
  }

  @override
  Future<void> redo() async {
    if (_redo.isEmpty) return;
    _grouping = false;
    _undo.add(_value.copyWith(composing: TextRange.empty));
    _value = _redo.removeLast();
  }

  void _select(TextRange r) =>
      _value = _value.copyWith(selection: TextSelection(baseOffset: r.start, extentOffset: r.end), composing: TextRange.empty);

  @override
  Future<TextRange?> find(String query, FindOptions options, {bool backward = false}) async {
    final sel = _value.selection;
    final from = backward ? (sel.isValid ? sel.start : _value.text.length) : (sel.isValid ? sel.end : 0);
    final m = findMatch(_value.text, query, options, from, backward: backward);
    if (m != null) _select(m);
    return m;
  }

  @override
  Future<bool> replaceNext(String query, String replacement, FindOptions options) async {
    final sel = _value.selection;
    final start = sel.isValid ? sel.start : 0;
    final m = findMatch(_value.text, query, options, start);
    if (m == null) return false;
    if (!(sel.isValid && m.start == sel.start && m.end == sel.end)) {
      _select(m);
      return false;
    }
    _edit((v) {
      final text = v.text.replaceRange(m.start, m.end, replacement);
      return TextEditingValue(text: text, selection: TextSelection.collapsed(offset: m.start + replacement.length));
    });
    _grouping = false;
    final next = findMatch(_value.text, query, options, m.start + replacement.length);
    if (next != null) _select(next);
    return true;
  }

  @override
  Future<int> replaceAll(String query, String replacement, FindOptions options) async {
    final hits = findAllMatches(_value.text, query, options, limit: 1 << 30);
    if (hits.isEmpty) return 0;
    _edit((v) {
      final out = StringBuffer();
      var last = 0;
      for (final h in hits) {
        out
          ..write(v.text.substring(last, h.start))
          ..write(replacement);
        last = h.end;
      }
      out.write(v.text.substring(last));
      final text = out.toString();
      final caret = v.selection.isValid ? v.selection.start.clamp(0, text.length) : 0;
      return TextEditingValue(text: text, selection: TextSelection.collapsed(offset: caret));
    });
    return hits.length;
  }

  @override
  Future<int> countMatches(String query, FindOptions options) async => findAllMatches(_value.text, query, options).length;

  @override
  List<PlainParagraph> plainParagraphs() => md.markdownToPlainParagraphs(_value.text);

  @override
  void dispose() => _changes.dispose();
}
