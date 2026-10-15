/// 설정·서식 요소 값 → 한/글 조판 미리보기(rhwp) 명세. 순수 함수(시험 가능).
///
/// 명세 형식은 hwp_preview/src/spec.js 머리말과 같다. 값이 없으면 앱의 표준 서식 기본값
/// (hwp-auto-docfit.py 표준서식_설정: □ HY견고딕 17pt, ㅇ 한컴돋움 15pt, - 휴먼명조 14pt, ※ 한컴돋움 13pt,
/// 여백 좌우 20mm·위아래 12.7mm, 줄 간격 160%)을 쓴다.
library;

const _body = '남은 전기버스 4대를 공익활동 지원과 찾아가는 행정서비스에 활용하는 방안을 관계 부서와 함께 검토함';

/// (항목기호, 앞 칸 수, 글꼴, 크기, 위 간격 설정 키, 굵게 설정 키, 기본 위 간격 pt)
const _rules = [
  ('□', 0, 'HY견고딕', 17.0, 'std_parspace_box', 'std_symbol_box_bold', 15.0),
  ('ㅇ', 1, '한컴돋움', 15.0, 'std_parspace_circle', 'std_symbol_o_bold', 8.0),
  ('-', 3, '휴먼명조', 14.0, 'std_parspace_dash', 'std_symbol_dash_bold', 4.0),
  ('※', 3, '한컴돋움', 13.0, 'std_parspace_note', 'std_symbol_note_bold', 0.0),
];

double? _num(Object? value) {
  if (value is num) return value.toDouble();
  final match = RegExp(r'-?\d+(\.\d+)?').firstMatch('${value ?? ''}');
  return match == null ? null : double.tryParse(match.group(0)!);
}

bool _on(Object? value, [bool fallback = false]) =>
    value == null ? fallback : value == true || value == 'true' || value == '예';

/// 설정 키가 미리보기의 어느 부분에 닿는지(강조할 항목기호 또는 'table'·'page').
String? focusOf(String? key) {
  if (key == null) return null;
  if (key.startsWith('table_fonts') || key == 'std_table_header') {
    return 'table';
  }
  if (key == 'std_margin') return 'page';
  for (final (marker, _, _, _, space, bold, _) in _rules) {
    if (key.contains('.$marker.') ||
        key == space ||
        key == bold ||
        key == 'label_symbols.$marker') {
      return marker;
    }
  }
  if (key.contains('.*.') || key == 'label_symbols.*') return '※';
  return null;
}

/// 설정 화면: 지금 값(저장 전 변경 포함)으로 보고서 한 토막을 만든다. focusKey가 닿는 문단을 강조한다.
Map<String, Object?> settingsSpec(
  Object? Function(String key) value, {
  String? focusKey,
}) {
  final focus = focusOf(focusKey);
  final hanging = _on(value('std_hanging_indent'), true);
  final paragraphs = <Map<String, Object?>>[];
  for (final (marker, indent, font, size, space, bold, before) in _rules) {
    final fontKey = 'symbol_fonts.$marker.font';
    final sizeKey = 'symbol_fonts.$marker.size';
    final char = {
      'font': value(fontKey) is String && '${value(fontKey)}'.isNotEmpty
          ? value(fontKey)
          : font,
      'size': _num(value(sizeKey)) ?? size,
      'bold': _on(value(bold)),
    };
    final labelBold =
        _on(value('label_symbols.$marker')) ||
        (marker == 'ㅇ' && _on(value('paren_label_bold'), true));
    paragraphs.add({
      'marker': marker,
      'indent': indent,
      'text': marker == '□'
          ? '추진 배경'
          : marker == 'ㅇ'
          ? '(추진 배경) $_body'
          : marker == '※'
          ? '세부 일정은 관계 부서 협의 후 확정'
          : _body,
      if (labelBold && marker == 'ㅇ') 'label': '(추진 배경)',
      'hanging': hanging,
      'char': char,
      'para': {
        // 표준 서식의 기본 줄 간격(160%). 끄면 한/글 새 문서 기본(160%)과 같아 값이 같다.
        'line': 160,
        'before': _on(value('std_parspace'), true)
            ? (_num(value(space)) ?? before)
            : 0,
      },
      'focus': focus == marker,
    });
  }
  final styled = _on(value('std_table_header'), true);
  return {
    if (_on(value('std_margin'), true))
      'page': {'left': 20, 'right': 20, 'top': 12.7, 'bottom': 12.7},
    'paragraphs': paragraphs,
    'table': {
      'rows': [
        ['구분', '1안', '2안'],
        ['운영비', '20,000천원', '46,000천원'],
      ],
      'header': styled
          ? {
              'font': value('table_fonts.header.font') ?? '한컴돋움',
              'size': _num(value('table_fonts.header.size')) ?? 13,
              'bold': true,
              'fill': '#EEF1F5',
            }
          : {'font': '함초롬바탕', 'size': 10},
      'body': styled
          ? {
              'font': value('table_fonts.body.font') ?? '휴먼명조',
              'size': _num(value('table_fonts.body.size')) ?? 12,
            }
          : {'font': '함초롬바탕', 'size': 10},
      'focus': focus == 'table',
    },
  };
}

const _markers = ['□', 'ㅇ', '○', '-', '•', '※', '*'];

/// 서식 요소 편집 화면: 요소 하나(경로·이름·값 '15pt' '-5%' '예' '왼쪽' …)를 앞 문단과 함께 조판한다.
/// 쪽 요소는 null(여백 그림은 기존 미리보기를 쓴다).
Map<String, Object?>? elementSpec(
  List path,
  String label,
  Map<String, String> values,
) {
  final kind = path.isEmpty ? '' : '${path.first}';
  if (kind == 'page') return null;
  final size = (_num(values['size']) ?? 13).clamp(6, 40).toDouble();
  final char = {
    if (values['font'] != null) 'font': values['font'],
    'size': size,
    'bold': _on(values['bold']),
    'spacing': _num(values['spacing']) ?? 0,
    'ratio': _num(values['ratio']) ?? 100,
  };
  if (kind == 'table' ||
      (kind == 'form' && path.length > 2 && path[2] == 'table')) {
    final header = path.length > 1 && path[1] == 'header';
    return {
      'paragraphs': const [],
      'table': {
        'rows': [
          ['구분', '1안', '2안'],
          ['운영비', '20,000천원', '46,000천원'],
        ],
        'header': header
            ? {...char, 'fill': '#EEF1F5'}
            : {'font': '한컴돋움', 'size': 12, 'bold': true, 'fill': '#EEF1F5'},
        'body': header ? {'font': '휴먼명조', 'size': 11} : char,
        'focus': true,
      },
    };
  }
  final trimmed = label.trim();
  final marker = _markers.firstWhere(trimmed.startsWith, orElse: () => '');
  final lineType = values['line_type'];
  final line = lineType == null || lineType == '글자에 따라(%)'
      ? (_num(values['line']) ?? 160)
      : 160;
  return {
    'paragraphs': [
      {
        'text': '앞 문단',
        'char': {'size': 11, 'color': '#8B98AD'},
      },
      {
        'marker': marker,
        'indent': marker == 'ㅇ' || marker == '○'
            ? 1
            : marker.isEmpty || marker == '□'
            ? 0
            : 3,
        'text': '추진 배경 : $_body',
        if (_on(values['label_bold'])) 'label': '추진 배경 :',
        'hanging': values['hanging'] == null ? true : _on(values['hanging']),
        'char': char,
        'markerChar': {
          ...char,
          'bold': _on(values['marker_bold']) || _on(values['bold']),
        },
        'para': {
          'line': line,
          'before': _num(values['prev']) ?? 0,
          'align': values['align'] ?? '양쪽',
        },
        'focus': false,
      },
    ],
  };
}
