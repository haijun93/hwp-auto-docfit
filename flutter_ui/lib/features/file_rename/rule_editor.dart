import 'package:flutter/material.dart';

import 'file_rename_api.dart';

const _keyLabels = {
  'find': '찾을 글자',
  'to': '바꿀 글자',
  'regex': '정규식',
  'case': '대소문자 구분',
  'count': '바꿀 횟수',
  'text': '넣을 글자 ({orig} 원래 이름 · {folder} 폴더 · {date} 수정일)',
  'position': '위치',
  'sep': '구분 문자',
  'source': '날짜 기준',
  'format': '형식 (YYYY YY MM DD hh mm ss)',
  'start': '시작',
  'step': '간격',
  'digits': '자리수',
  'per_folder': '폴더마다 따로 세기',
  'delta': '늘릴 값(줄이려면 음수)',
  'which': '대상 숫자',
  'end': '끝',
  'origin': '기준',
  'open': '여는 문자',
  'close': '닫는 문자',
  'nest': '겹친 괄호',
  'keep_marks': '괄호는 남기기',
  'nfc': '한글 자모 합치기(NFC)',
  'collapse_spaces': '연속 공백·밑줄 하나로',
  'underscore': '밑줄·공백',
  'strip': '앞뒤 공백·밑줄 지우기',
  'mode': '방식',
  'ext': '확장자',
  'template': '이름 틀 ({date} 수정일 · {title} 제목 · {orig} 원래 이름 · {n} 번호 · {dept} 부서)',
  'dept': '부서 이름',
  'max_length': '제목 최대 길이',
};

Map<String, String> _choices(String kind, String key) {
  switch (key) {
    case 'position':
      return {
        'prefix': '이름 앞',
        'suffix': '이름 뒤',
        if (kind == 'date' || kind == 'number') 'replace': '이름 대신',
      };
    case 'count':
      return {'all': '모두', 'first': '처음 하나만'};
    case 'source':
      return {'exif': '사진 촬영일(없으면 수정일)', 'mtime': '수정한 날', 'ctime': '만든 날', 'today': '오늘'};
    case 'which':
      return {'first': '첫 번째 숫자', 'last': '마지막 숫자'};
    case 'origin':
      return {'start': '앞에서', 'end': '뒤에서'};
    case 'nest':
      return {'outer': '가장 바깥', 'inner': '가장 안쪽'};
    case 'underscore':
      return {'keep': '그대로', 'to_space': '밑줄 → 공백', 'from_space': '공백 → 밑줄'};
    case 'mode':
      return {'lower': '소문자', 'upper': '대문자', if (kind == 'case') 'title': '첫 글자 대문자'};
  }
  return const {};
}

/// 규칙 옵션 편집 대화상자. 저장하면 새 규칙 맵, 취소하면 null.
Future<Map<String, Object?>?> showRuleEditor(
  BuildContext context,
  Map<String, Object?> rule,
) {
  return showDialog<Map<String, Object?>>(
    context: context,
    builder: (_) => _RuleEditorDialog(rule: rule),
  );
}

class _RuleEditorDialog extends StatefulWidget {
  const _RuleEditorDialog({required this.rule});

  final Map<String, Object?> rule;

  @override
  State<_RuleEditorDialog> createState() => _RuleEditorDialogState();
}

class _RuleEditorDialogState extends State<_RuleEditorDialog> {
  late final Map<String, Object?> _value = Map.of(widget.rule);
  final _controllers = <String, TextEditingController>{};
  String? _error;

  String get _kind => '${_value['kind']}';

  @override
  void dispose() {
    for (final c in _controllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  TextEditingController _controller(String key) => _controllers.putIfAbsent(
    key,
    () => TextEditingController(text: '${_value[key] ?? ''}'),
  );

  Widget _field(String key, Object? defaultValue) {
    final label = _keyLabels[key] ?? key;
    final choices = _choices(_kind, key);
    if (defaultValue is bool) {
      return SwitchListTile(
        contentPadding: EdgeInsets.zero,
        title: Text(label),
        value: _value[key] == true,
        onChanged: (v) => setState(() => _value[key] = v),
      );
    }
    if (choices.isNotEmpty) {
      return DropdownButtonFormField<String>(
        initialValue: choices.containsKey(_value[key]) ? '${_value[key]}' : choices.keys.first,
        decoration: InputDecoration(labelText: label),
        items: [
          for (final e in choices.entries)
            DropdownMenuItem(value: e.key, child: Text(e.value)),
        ],
        onChanged: (v) => setState(() => _value[key] = v),
      );
    }
    return TextField(
      key: ValueKey('rule-field-$key'),
      controller: _controller(key),
      decoration: InputDecoration(labelText: label),
      keyboardType: defaultValue is int ? TextInputType.number : TextInputType.text,
    );
  }

  void _save() {
    final defaults = ruleKindOf(_kind).defaults;
    for (final entry in _controllers.entries) {
      final text = entry.value.text;
      if (defaults[entry.key] is int) {
        final number = int.tryParse(text.trim());
        if (number == null) {
          setState(() => _error = '${_keyLabels[entry.key] ?? entry.key}에 숫자를 넣어 주세요.');
          return;
        }
        _value[entry.key] = number;
      } else {
        _value[entry.key] = text;
      }
    }
    Navigator.of(context).pop(_value);
  }

  @override
  Widget build(BuildContext context) {
    final kind = ruleKindOf(_kind);
    return AlertDialog(
      title: Text(kind.label),
      content: SizedBox(
        width: 420,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (kind.defaults.isEmpty) const Text('고칠 옵션이 없습니다.'),
              for (final e in kind.defaults.entries)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: _field(e.key, e.value),
                ),
              if (_error != null)
                Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('취소')),
        FilledButton(onPressed: _save, child: const Text('확인')),
      ],
    );
  }
}
