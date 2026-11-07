/// 메모 편집기의 Markdown 서식 규칙(순수 함수). 위젯·플랫폼에 의존하지 않아 Rust 편집 코어로 옮길 때 기준이 된다.
///
/// 본문은 Markdown 원문 그대로 입력 칸에 두고, 도구줄 명령은 원문에 서식 기호를 넣거나 뺀다.
/// (서식을 직접 그리는 편집기는 한글 IME 조합·접근성 위험 때문에 후속 검토 — TODO.md 노트북 개선 (3) 참고)
library;

import 'package:flutter/services.dart' show TextEditingValue, TextSelection;

/// 문단 형식: 0=보통, 1~3=제목 1~3.
const kMemoBlockStyles = <int, String>{0: '보통', 1: '제목 1', 2: '제목 2', 3: '제목 3'};

/// 검색 색인용 평문 문단. [level]은 제목 수준(보통 0).
class PlainParagraph {
  const PlainParagraph(this.text, {this.level = 0});
  final String text;
  final int level;

  @override
  bool operator ==(Object other) => other is PlainParagraph && other.text == text && other.level == level;

  @override
  int get hashCode => Object.hash(text, level);

  @override
  String toString() => 'PlainParagraph($level, $text)';
}

final _fence = RegExp(r'^\s*(```|~~~)');
final _rule = RegExp(r'^\s*([-*_])(\s*\1){2,}\s*$');
final _heading = RegExp(r'^\s*(#{1,6})\s+');
final _list = RegExp(r'^\s*(?:[-*+]|\d+[.)])\s+');
final _bullet = RegExp(r'^\s*[-*+]\s+');
final _numbered = RegExp(r'^\s*\d+[.)]\s+');
final _quote = RegExp(r'^\s*(?:>\s?)+');
final _link = RegExp(r'\[([^\]]*)\]\(([^)\s]*)\)');
final _emphasis = RegExp(
  r'(\*\*|__)(.+?)\1|(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])|(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])',
);
final _code = RegExp(r'`([^`]+)`');

String _stripInline(String line) => line
    .replaceAllMapped(_link, (m) => (m[2] ?? '').isEmpty ? m[1]! : '${m[1]} (${m[2]})')
    .replaceAllMapped(_code, (m) => m[1]!)
    .replaceAllMapped(_emphasis, (m) => m[2] ?? m[3] ?? m[4] ?? '');

/// Markdown을 검색용 평문 문단으로 바꾼다. Python `docfit_app/notebook_service.py`의
/// `memo_markdown_to_paragraphs`와 같은 규칙이다(바꾸면 양쪽을 함께 고친다).
List<PlainParagraph> markdownToPlainParagraphs(String markdown) {
  final out = <PlainParagraph>[];
  var inCode = false;
  for (final raw in markdown.replaceAll('\r\n', '\n').replaceAll('\r', '\n').split('\n')) {
    if (_fence.hasMatch(raw)) {
      inCode = !inCode;
      continue;
    }
    String text;
    var level = 0;
    if (inCode) {
      text = raw.trim();
    } else {
      if (_rule.hasMatch(raw)) continue;
      var line = raw;
      final heading = _heading.firstMatch(line);
      if (heading != null) {
        level = heading[1]!.length;
        line = line.substring(heading.end);
      }
      line = line.replaceFirst(_quote, '').replaceFirst(_list, '');
      text = _stripInline(line).trim();
    }
    if (text.isNotEmpty) out.add(PlainParagraph(text, level: level));
  }
  return out;
}

/// 선택 영역이 걸친 줄들의 [시작, 끝) 위치.
(int, int) _lineRange(String text, TextSelection sel) {
  final s = sel.isValid ? sel.start.clamp(0, text.length) : text.length;
  var e = sel.isValid ? sel.end.clamp(0, text.length) : text.length;
  if (e > s && text[e - 1] == '\n') e--;
  final start = s == 0 ? 0 : text.lastIndexOf('\n', s - 1) + 1;
  final nl = text.indexOf('\n', e);
  return (start, nl < 0 ? text.length : nl);
}

TextEditingValue _replaceLines(TextEditingValue value, String Function(List<String> lines) edit) {
  final text = value.text;
  final (start, end) = _lineRange(text, value.selection);
  final replaced = edit(text.substring(start, end).split('\n'));
  final next = text.replaceRange(start, end, replaced);
  return TextEditingValue(
    text: next,
    selection: TextSelection(baseOffset: start, extentOffset: start + replaced.length),
  );
}

/// 커서가 있는 줄의 제목 수준(0=보통).
int currentBlockStyle(TextEditingValue value) {
  final (start, end) = _lineRange(value.text, value.selection.isValid ? TextSelection.collapsed(offset: value.selection.start) : value.selection);
  final m = _heading.firstMatch(value.text.substring(start, end));
  return m == null ? 0 : m[1]!.length.clamp(0, 3);
}

/// 선택한 줄들의 문단 형식을 바꾼다(0=보통이면 제목 기호를 지우고, 제목이면 목록·인용 기호를 지우고 제목 기호를 붙인다).
TextEditingValue setBlockStyle(TextEditingValue value, int level) => _replaceLines(
  value,
  (lines) => [
    for (final l in lines)
      level <= 0
          ? l.replaceFirst(_heading, '')
          : '${'#' * level} ${l.replaceFirst(_heading, '').replaceFirst(_quote, '').replaceFirst(_list, '')}',
  ].join('\n'),
);

/// 굵게(`**`)·기울임(`*`)·인라인 코드(`` ` ``)를 켜고 끈다. 선택이 없으면 [placeholder]를 넣어 선택해 둔다.
TextEditingValue toggleInline(TextEditingValue value, String marker, {String placeholder = '글자'}) {
  final text = value.text;
  final sel = value.selection.isValid ? value.selection : TextSelection.collapsed(offset: text.length);
  final s = sel.start, e = sel.end, n = marker.length;
  final selected = text.substring(s, e);
  // 이미 감싸져 있으면 푼다(선택 바깥 또는 선택 안쪽 양 끝).
  if (s >= n && e + n <= text.length && text.substring(s - n, s) == marker && text.substring(e, e + n) == marker) {
    final next = text.replaceRange(e, e + n, '').replaceRange(s - n, s, '');
    return TextEditingValue(text: next, selection: TextSelection(baseOffset: s - n, extentOffset: e - n));
  }
  if (selected.length >= 2 * n && selected.startsWith(marker) && selected.endsWith(marker)) {
    final inner = selected.substring(n, selected.length - n);
    return TextEditingValue(
      text: text.replaceRange(s, e, inner),
      selection: TextSelection(baseOffset: s, extentOffset: s + inner.length),
    );
  }
  final inner = selected.isEmpty ? placeholder : selected;
  return TextEditingValue(
    text: text.replaceRange(s, e, '$marker$inner$marker'),
    selection: TextSelection(baseOffset: s + n, extentOffset: s + n + inner.length),
  );
}

enum MemoListKind { bullet, numbered, quote }

/// 글머리·번호 목록·인용을 켜고 끈다. 선택한 줄이 모두 그 형식이면 풀고, 아니면 다른 목록 기호를 바꿔 붙인다.
TextEditingValue toggleLinePrefix(TextEditingValue value, MemoListKind kind) => _replaceLines(value, (lines) {
  final pattern = switch (kind) {
    MemoListKind.bullet => _bullet,
    MemoListKind.numbered => _numbered,
    MemoListKind.quote => _quote,
  };
  final content = lines.where((l) => l.trim().isNotEmpty).toList();
  final allOn = content.isNotEmpty && content.every(pattern.hasMatch);
  if (allOn) return [for (final l in lines) l.replaceFirst(pattern, '')].join('\n');
  var number = 0;
  return [
    for (final l in lines)
      if (l.trim().isEmpty && lines.length > 1)
        l
      else
        switch (kind) {
          MemoListKind.bullet => '- ${l.replaceFirst(_list, '')}',
          MemoListKind.numbered => '${++number}. ${l.replaceFirst(_list, '')}',
          MemoListKind.quote => '> ${l.replaceFirst(_quote, '')}',
        },
  ].join('\n');
});

/// 선택한 줄을 코드 블록(```)으로 감싼다. 선택이 없으면 빈 코드 블록을 넣고 그 안에 커서를 둔다.
TextEditingValue insertCodeBlock(TextEditingValue value) {
  final text = value.text;
  final sel = value.selection.isValid ? value.selection : TextSelection.collapsed(offset: text.length);
  if (sel.isCollapsed) {
    final at = sel.start;
    final lead = at > 0 && text[at - 1] != '\n' ? '\n' : '';
    final insert = '$lead```\n\n```\n';
    return TextEditingValue(
      text: text.replaceRange(at, at, insert),
      selection: TextSelection.collapsed(offset: at + lead.length + 4),
    );
  }
  return _replaceLines(value, (lines) => '```\n${lines.join('\n')}\n```');
}

/// 커서 줄 다음에 구분선(---)을 넣는다.
TextEditingValue insertHorizontalRule(TextEditingValue value) {
  final text = value.text;
  final (_, end) = _lineRange(text, value.selection);
  final before = end == 0 ? '' : '\n';
  final insert = '$before---\n';
  final next = text.replaceRange(end, end, insert);
  final caret = end + insert.length;
  return TextEditingValue(text: next, selection: TextSelection.collapsed(offset: caret.clamp(0, next.length)));
}

/// 선택한 글자를 링크 `[글자](주소)`로 만든다. 선택이 없으면 주소를 글자로 쓴다.
TextEditingValue insertLink(TextEditingValue value, String url) {
  final text = value.text;
  final sel = value.selection.isValid ? value.selection : TextSelection.collapsed(offset: text.length);
  final address = url.trim().replaceAll(RegExp(r'[\s)]'), '');
  final label = sel.isCollapsed ? address : text.substring(sel.start, sel.end).replaceAll(RegExp(r'[\[\]\n]'), ' ');
  final link = '[$label]($address)';
  return TextEditingValue(
    text: text.replaceRange(sel.start, sel.end, link),
    selection: TextSelection.collapsed(offset: sel.start + link.length),
  );
}

/// 선택한 줄(선택이 없으면 커서 줄)의 서식을 모두 지운다: 제목·목록·인용 기호, 굵게·기울임·코드, 링크(글자만 남김), 코드 블록 울타리.
TextEditingValue clearFormatting(TextEditingValue value) => _replaceLines(
  value,
  (lines) => [
    for (final l in lines)
      if (!_fence.hasMatch(l))
        l
            .replaceFirst(_heading, '')
            .replaceFirst(_quote, '')
            .replaceFirst(_list, '')
            .replaceAllMapped(_link, (m) => m[1]!)
            .replaceAllMapped(_code, (m) => m[1]!)
            .replaceAllMapped(_emphasis, (m) => m[2] ?? m[3] ?? m[4] ?? ''),
  ].join('\n'),
);
