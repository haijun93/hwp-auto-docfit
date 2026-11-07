/// 메모 편집기 위치 변환과 찾기 도우미.
///
/// Flutter `TextEditingValue`는 UTF-16 코드 유닛 위치를, Rust 편집 코어(editor_core)는 UTF-8 바이트 위치를 쓴다.
/// 변환을 매번 파이프로 묻지 않도록 화면 쪽에서 같은 규칙으로 계산한다(대리 쌍 = 4바이트).
library;

import 'package:flutter/services.dart' show TextRange;

/// [text]의 UTF-16 구간 `[start,end)`가 UTF-8로 몇 바이트인지.
int utf8Length(String text, [int start = 0, int? end]) {
  final stop = end ?? text.length;
  var bytes = 0;
  for (var i = start; i < stop; i++) {
    final u = text.codeUnitAt(i);
    if (u < 0x80) {
      bytes += 1;
    } else if (u < 0x800) {
      bytes += 2;
    } else if (u >= 0xD800 && u <= 0xDBFF && i + 1 < stop) {
      final next = text.codeUnitAt(i + 1);
      if (next >= 0xDC00 && next <= 0xDFFF) {
        bytes += 4;
        i++;
        continue;
      }
      bytes += 3;
    } else {
      bytes += 3;
    }
  }
  return bytes;
}

/// UTF-16 위치 → UTF-8 바이트 위치. 대리 쌍 한가운데면 그 글자 앞으로 맞춘다.
int utf16ToUtf8(String text, int unit) {
  var at = unit.clamp(0, text.length);
  if (at > 0 && at < text.length && _isLow(text.codeUnitAt(at)) && _isHigh(text.codeUnitAt(at - 1))) at--;
  return utf8Length(text, 0, at);
}

/// UTF-8 바이트 위치 → UTF-16 위치. 글자 중간이면 그 글자 뒤로 맞춘다.
int utf8ToUtf16(String text, int byte) {
  var bytes = 0;
  var i = 0;
  while (i < text.length && bytes < byte) {
    final u = text.codeUnitAt(i);
    if (_isHigh(u) && i + 1 < text.length && _isLow(text.codeUnitAt(i + 1))) {
      bytes += 4;
      i += 2;
    } else {
      bytes += u < 0x80 ? 1 : (u < 0x800 ? 2 : 3);
      i++;
    }
  }
  return i;
}

bool _isHigh(int u) => u >= 0xD800 && u <= 0xDBFF;
bool _isLow(int u) => u >= 0xDC00 && u <= 0xDFFF;

/// 메모장식 줄·열(둘 다 1부터, 열은 글자 단위)을 UTF-16 위치에서 센다.
({int line, int column}) lineColumnAt(String text, int offset) {
  final at = offset.clamp(0, text.length);
  var line = 1;
  var lineStart = 0;
  for (var i = 0; i < at; i++) {
    if (text.codeUnitAt(i) == 0x0A) {
      line++;
      lineStart = i + 1;
    }
  }
  return (line: line, column: text.substring(lineStart, at).runes.length + 1);
}

/// 줄바꿈을 LF로 맞춘다(Rust 코어 내부 규칙과 같게). 바뀐 만큼 [offsets]도 옮겨 돌려준다.
(String, List<int>) normalizeNewlines(String text, List<int> offsets) {
  if (!text.contains('\r')) return (text, offsets);
  final out = StringBuffer();
  final map = List<int>.filled(text.length + 1, 0);
  var w = 0;
  for (var i = 0; i < text.length; i++) {
    map[i] = w;
    final u = text.codeUnitAt(i);
    if (u == 0x0D) {
      if (i + 1 < text.length && text.codeUnitAt(i + 1) == 0x0A) continue; // CRLF의 CR은 버린다
      out.write('\n');
    } else {
      out.writeCharCode(u);
    }
    w++;
  }
  map[text.length] = w;
  return (out.toString(), [for (final o in offsets) o < 0 ? o : map[o.clamp(0, text.length)]]);
}

/// 찾기 선택 사항(Rust `SearchOpts`와 같은 뜻).
class FindOptions {
  const FindOptions({this.caseSensitive = false, this.wholeWord = false});
  final bool caseSensitive;
  final bool wholeWord;

  Map<String, Object?> toJson() => {'case_sensitive': caseSensitive, 'whole_word': wholeWord};
}

final _wordChar = RegExp(r'[\p{L}\p{N}_]', unicode: true);

bool _isWordAt(String text, int index, {required bool before}) {
  int s;
  int e;
  if (before) {
    if (index <= 0) return false;
    e = index;
    s = index - 1;
    if (s > 0 && _isLow(text.codeUnitAt(s)) && _isHigh(text.codeUnitAt(s - 1))) s--;
  } else {
    if (index >= text.length) return false;
    s = index;
    e = index + 1;
    if (e < text.length && _isHigh(text.codeUnitAt(s)) && _isLow(text.codeUnitAt(e))) e++;
  }
  return _wordChar.hasMatch(text.substring(s, e));
}

/// 겹치지 않는 모든 일치(UTF-16 구간). Rust `search::find_all`과 같은 규칙(대소문자 접기·온전한 낱말).
List<TextRange> findAllMatches(String text, String query, FindOptions options, {int limit = 10000}) {
  if (query.isEmpty) return const [];
  var hay = text;
  var needle = query;
  if (!options.caseSensitive) {
    final lowerText = text.toLowerCase();
    final lowerQuery = query.toLowerCase();
    // 소문자로 바꿔 길이가 달라지는 글자(드묾)가 있으면 대소문자 구분으로 찾는다.
    if (lowerText.length == text.length && lowerQuery.length == query.length) {
      hay = lowerText;
      needle = lowerQuery;
    }
  }
  final out = <TextRange>[];
  var at = 0;
  while (out.length < limit) {
    final s = hay.indexOf(needle, at);
    if (s < 0) break;
    final e = s + needle.length;
    if (!options.wholeWord || (!_isWordAt(text, s, before: true) && !_isWordAt(text, e, before: false))) {
      out.add(TextRange(start: s, end: e));
      at = e;
    } else {
      at = s + 1;
    }
  }
  return out;
}

/// [from]부터 앞으로(끝에 닿으면 처음부터) 또는 [from] 앞에서 뒤로(처음에 닿으면 끝부터) 찾는다.
TextRange? findMatch(String text, String query, FindOptions options, int from, {bool backward = false}) {
  final all = findAllMatches(text, query, options, limit: 1 << 30);
  if (all.isEmpty) return null;
  if (backward) {
    final before = all.where((m) => m.start < from);
    return before.isEmpty ? all.last : before.last;
  }
  for (final m in all) {
    if (m.start >= from) return m;
  }
  return all.first;
}
