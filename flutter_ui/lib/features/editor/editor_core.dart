/// 메모 편집기 코어 경계(EditorCore)와 Dart 임시 구현(DartEditorCore).
///
/// 경계 원칙(docs/EDITOR_CORE_BOUNDARY.md):
/// - 글자 입력·한글 IME 조합·선택·커서 그리기는 Flutter `TextField`(EditableText)가 맡는다.
/// - 코어는 본문 버퍼(Markdown 원문)·선택·실행취소 이력·서식 명령·평문 변환만 맡는다.
/// - Rust 편집 코어(EDCORE)가 준비되면 같은 [EditorCore]를 구현한 브리지 클래스로 바꿔 끼운다.
///   화면(`memo_editor.dart`)은 [EditorCore]만 알고 구현을 모른다.
library;

import 'package:flutter/services.dart' show TextEditingValue, TextRange, TextSelection;

import 'markdown_format.dart' as md;
import 'markdown_format.dart' show PlainParagraph;

/// 도구줄 서식 명령. 문단 형식(제목)과 링크는 값이 필요해 [EditorCore.setBlockStyle]·[EditorCore.insertLink]로 따로 둔다.
enum EditorCommand { bold, italic, inlineCode, codeBlock, bulletList, numberedList, quote, horizontalRule, clearFormatting }

abstract class EditorCore {
  /// 현재 본문(Markdown 원문)과 선택.
  TextEditingValue get value;

  /// 입력 칸에서 바뀐 값을 알린다(타자·붙여넣기·IME 조합·커서 이동). 코어는 이력 묶음을 정한다.
  /// IME 조합 중(composing)인 값은 조합이 끝날 때까지 한 묶음으로 둔다.
  void updateFromInput(TextEditingValue next);

  /// 지금까지의 입력 묶음을 닫는다(잠시 멈춤 등). 다음 입력은 새 실행취소 단계가 된다.
  void breakUndoGroup();

  void apply(EditorCommand command);
  void setBlockStyle(int level);
  void insertLink(String url);

  /// 커서 줄의 문단 형식(0=보통, 1~3=제목).
  int get blockStyle;

  bool get canUndo;
  bool get canRedo;
  void undo();
  void redo();

  /// 저장할 Markdown 원문.
  String get markdown => value.text;

  /// 검색 색인용 평문 문단.
  List<PlainParagraph> plainParagraphs();
}

/// Dart로 쓴 임시 코어. 실행취소는 값 스냅숏 묶음(최대 [maxHistory]단계).
class DartEditorCore implements EditorCore {
  DartEditorCore({String text = '', this.maxHistory = 200})
    : _value = TextEditingValue(text: text, selection: TextSelection.collapsed(offset: text.length));

  final int maxHistory;
  TextEditingValue _value;
  final _undo = <TextEditingValue>[];
  final _redo = <TextEditingValue>[];
  bool _grouping = false;

  @override
  TextEditingValue get value => _value;

  @override
  String get markdown => _value.text;

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
    if (!next.composing.isValid && next.text.isNotEmpty &&next.selection.isValid) {
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
  void apply(EditorCommand command) => _edit(
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
  void setBlockStyle(int level) => _edit((v) => md.setBlockStyle(v, level));

  @override
  void insertLink(String url) {
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
  void undo() {
    if (_undo.isEmpty) return;
    _grouping = false;
    _redo.add(_value.copyWith(composing: TextRange.empty));
    _value = _undo.removeLast();
  }

  @override
  void redo() {
    if (_redo.isEmpty) return;
    _grouping = false;
    _undo.add(_value.copyWith(composing: TextRange.empty));
    _value = _redo.removeLast();
  }

  @override
  List<PlainParagraph> plainParagraphs() => md.markdownToPlainParagraphs(_value.text);
}
