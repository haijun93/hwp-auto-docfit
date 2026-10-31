import '../../core/api/abbreviation_api.dart' show ApiCall;

/// 목록 항목(경로는 호스트에만 있고 화면에는 이름·폴더만 온다).
class RenameEntry {
  const RenameEntry({
    required this.id,
    required this.name,
    required this.folder,
    required this.size,
    required this.mtime,
  });

  factory RenameEntry.fromJson(Map json) => RenameEntry(
    id: '${json['id']}',
    name: '${json['name'] ?? ''}',
    folder: '${json['folder'] ?? ''}',
    size: (json['size'] as num?)?.toInt() ?? 0,
    mtime: (json['mtime'] as num?)?.toDouble() ?? 0,
  );

  final String id;
  final String name;
  final String folder;
  final int size;
  final double mtime;
}

/// 미리보기 한 줄.
class RenamePreviewItem {
  const RenamePreviewItem({
    required this.id,
    required this.newName,
    required this.status,
    this.reason,
    this.warnings = const [],
    this.overridden = false,
  });

  factory RenamePreviewItem.fromJson(Map json) => RenamePreviewItem(
    id: '${json['id']}',
    newName: json['new_name'] as String?,
    status: '${json['status'] ?? 'invalid'}',
    reason: json['reason'] as String?,
    warnings: [for (final w in (json['warnings'] as List? ?? const [])) '$w'],
    overridden: json['overridden'] == true,
  );

  final String id;
  final String? newName;

  /// ok · unchanged · conflict · invalid · skipped
  final String status;
  final String? reason;
  final List<String> warnings;
  final bool overridden;
}

class RenameResult {
  const RenameResult(this.raw);

  final Map raw;

  bool get ok => raw['ok'] != false;
  String get message => '${raw['message'] ?? ''}';
  String get code => '${raw['code'] ?? ''}';
  List<RenameEntry>? get entries => raw['entries'] is List
      ? [for (final e in raw['entries'] as List) RenameEntry.fromJson(e as Map)]
      : null;
}

/// command('file_rename', [action, payload]) 래퍼.
class FileRenameApi {
  const FileRenameApi(this.call);

  final ApiCall call;

  Future<RenameResult> command(String action, [Map<String, Object?>? payload]) async {
    final response = await call('file_rename', [action, payload ?? const {}]);
    if (response is Map) return RenameResult(response);
    return const RenameResult({'ok': false, 'message': '올바르지 않은 응답입니다.'});
  }
}

/// 규칙 종류: 이름(화면 표시)과 기본 옵션.
class RuleKind {
  const RuleKind(this.kind, this.label, this.defaults);

  final String kind;
  final String label;
  final Map<String, Object?> defaults;
}

const ruleKinds = <RuleKind>[
  RuleKind('replace', '문자열 바꾸기', {'find': '', 'to': '', 'regex': false, 'case': true, 'count': 'all'}),
  RuleKind('add', '앞/뒤에 추가', {'text': '', 'position': 'prefix', 'sep': ''}),
  RuleKind('date', '날짜·시각 넣기', {'source': 'mtime', 'format': 'YYYYMMDD', 'position': 'prefix', 'sep': '_'}),
  RuleKind('number', '번호 붙이기', {'start': 1, 'step': 1, 'digits': 3, 'position': 'suffix', 'per_folder': false, 'sep': '_'}),
  RuleKind('number_shift', '번호 늘리기/줄이기', {'delta': 1, 'which': 'first'}),
  RuleKind('digits_pad', '자리수 맞추기', {'digits': 3, 'which': 'last'}),
  RuleKind('del_pos', '위치 지우기', {'start': 1, 'end': 1, 'origin': 'start'}),
  RuleKind('del_between', '묶인 곳 지우기', {'open': '(', 'close': ')', 'nest': 'outer', 'keep_marks': false}),
  RuleKind('digits_keep', '숫자만 남기기', {}),
  RuleKind('digits_delete', '숫자 지우기', {}),
  RuleKind('clear', '이름 지우기(확장자만 남김)', {}),
  RuleKind('strip_result_suffix', '결과 접미사 지우기', {'to': ''}),
  RuleKind('doc_title', '문서 제목으로', {'position': 'replace', 'sep': '_', 'max_length': 60}),
  RuleKind('template', '공문서 이름 틀', {'template': '{date}_{dept}_{title}', 'dept': '', 'digits': 1, 'max_length': 60}),
  RuleKind('cleanup', '공백·밑줄·전각 정리', {'nfc': true, 'collapse_spaces': true, 'underscore': 'keep', 'strip': true, 'width': 'keep'}),
  RuleKind('case', '대/소문자', {'mode': 'lower'}),
  RuleKind('names_list', '이름 목록 붙여넣기(엑셀·메모장 줄)', {'names': '', 'keep_ext': true}),
  RuleKind('ext_case', '확장자 대/소문자', {'mode': 'lower'}),
  RuleKind('ext_replace', '확장자 바꾸기', {'ext': 'txt'}),
  RuleKind('ext_add', '확장자 덧붙이기', {'ext': 'bak'}),
  RuleKind('ext_del', '확장자 지우기', {}),
];

RuleKind ruleKindOf(String kind) =>
    ruleKinds.firstWhere((k) => k.kind == kind, orElse: () => ruleKinds.first);

/// 규칙 카드에 보일 한 줄 요약.
String ruleSummary(Map<String, Object?> rule) {
  String pos(Object? p) => p == 'prefix' ? '앞' : p == 'suffix' ? '뒤' : '이름 대신';
  switch (rule['kind']) {
    case 'replace':
      return "'${rule['find']}' → '${rule['to']}'${rule['regex'] == true ? ' (정규식)' : ''}";
    case 'add':
      return "${pos(rule['position'])}에 '${rule['text']}'";
    case 'date':
      const sources = {'exif': '촬영일', 'mtime': '수정일', 'ctime': '만든 날', 'today': '오늘'};
      return '${sources[rule['source']] ?? ''} ${rule['format']} · ${pos(rule['position'])}';
    case 'number':
      return '${rule['start']}부터 ${rule['step']}씩 · ${rule['digits']}자리 · ${pos(rule['position'])}'
          '${rule['per_folder'] == true ? ' · 폴더별' : ''}';
    case 'number_shift':
      return '${rule['which'] == 'first' ? '첫' : '끝'} 번호 ${(rule['delta'] as num? ?? 0) > 0 ? '+' : ''}${rule['delta']}';
    case 'digits_pad':
      return '${rule['which'] == 'first' ? '첫' : '끝'} 숫자를 ${rule['digits']}자리로';
    case 'del_pos':
      return '${rule['origin'] == 'end' ? '뒤에서' : '앞에서'} ${rule['start']}~${rule['end']}번째';
    case 'del_between':
      return "${rule['open']}…${rule['close']} ${rule['nest'] == 'inner' ? '(안쪽)' : '(바깥)'}";
    case 'ext_replace':
    case 'ext_add':
      return '.${'${rule['ext']}'.replaceFirst('.', '')}';
    case 'names_list':
      final lines = '${rule['names']}'.split('\n').where((l) => l.trim().isNotEmpty).length;
      return '$lines줄 · ${rule['keep_ext'] == false ? '확장자까지' : '확장자 유지'}';
    case 'case':
    case 'ext_case':
      return const {
            'upper': '대문자',
            'title': '낱말마다 첫 글자 대문자',
            'capitalize': '맨 앞 글자만 대문자',
            'sentence': '문장형(맨 앞만 대문자)',
          }[rule['mode']] ??
          '소문자';
    default:
      return '';
  }
}
