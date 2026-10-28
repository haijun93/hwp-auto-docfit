import 'package:flutter/material.dart';
import '../../core/api/abbreviation_api.dart';

class UnifyPickStyleDialog extends StatefulWidget {
  const UnifyPickStyleDialog({
    super.key,
    required this.api,
    required this.data,
  });

  final ApiCall api;
  final Map data;

  @override
  State<UnifyPickStyleDialog> createState() => _UnifyPickStyleDialogState();
}

class _UnifyPickStyleDialogState extends State<UnifyPickStyleDialog> {
  final Map<String, String> values = {};
  late final Set<Object> selected;
  int selectedIndex = 0;
  bool busy = false;
  String error = '';

  @override
  void initState() {
    super.initState();
    final choices = widget.data['choices'] as List? ?? [];
    final styles = widget.data['styles'] as List? ?? [];
    selected = {for (final item in choices) item['id'] as Object};
    if (styles.isNotEmpty) {
      selectedIndex = (styles[0]['index'] as num?)?.toInt() ?? 0;
    }

    final fields = widget.data['fields'] as List? ?? [];
    for (final field in fields) {
      final id = '${field['id']}';
      final val = field['value'];
      values[id] = val != null ? '$val' : '';
    }
  }

  Future<void> answer(bool accepted) async {
    setState(() => busy = true);
    try {
      await widget.api('resolve_dialog', [
        widget.data['id'],
        accepted,
        accepted ? selected.toList() : [],
        accepted ? values : {},
      ]);
      if (mounted) Navigator.pop(context);
    } catch (e) {
      if (mounted) setState(() => error = '$e');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final styles = widget.data['styles'] as List? ?? [];
    final fields = widget.data['fields'] as List? ?? [];

    return PopScope(
      canPop: false,
      child: AlertDialog(
        title: Text(widget.data['title']?.toString() ?? '대표 서식 확인'),
        content: SizedBox(
          width: 600,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (widget.data['message'] != null)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: Text(widget.data['message'].toString()),
                  ),
                if (error.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Text(
                      error,
                      style: const TextStyle(color: Colors.red),
                    ),
                  ),
                const Text(
                  '조사된 서식 그룹',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                ),
                const SizedBox(height: 6),
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: [
                    for (int i = 0; i < styles.length; i++) ...[
                      () {
                        final st = styles[i] as Map;
                        final idx = (st['index'] as num?)?.toInt() ?? i;
                        final isSelected = selectedIndex == idx;
                        return ChoiceChip(
                          key: Key('unifyPickStyle_$idx'),
                          label: Text(
                            '${st['marker'] ?? ''} ${st['role'] ?? ''} (${st['font'] ?? '기본'} · ${st['size'] ?? 10}pt)',
                          ),
                          selected: isSelected,
                          onSelected: (val) {
                            if (val) setState(() => selectedIndex = idx);
                          },
                        );
                      }(),
                    ],
                  ],
                ),
                const SizedBox(height: 16),
                const Text(
                  '대표 서식 상세 설정',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                ),
                const SizedBox(height: 6),
                for (final field in fields.where(
                  (field) => '${field['id']}'.startsWith('$selectedIndex:'),
                )) ...[
                  Padding(
                    key: ValueKey(field['id']),
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: field['type'] == 'bool'
                        ? DropdownButtonFormField<String>(
                            key: ValueKey('unifyField_${field['id']}'),
                            initialValue: values['${field['id']}'] ?? '',
                            decoration: InputDecoration(
                              labelText: '${field['label']}',
                              isDense: true,
                              border: const OutlineInputBorder(),
                            ),
                            items: const [
                              DropdownMenuItem(value: '', child: Text('판정 보류')),
                              DropdownMenuItem(
                                value: 'True',
                                child: Text('적용 (True)'),
                              ),
                              DropdownMenuItem(
                                value: 'False',
                                child: Text('미적용 (False)'),
                              ),
                            ],
                            onChanged: busy
                                ? null
                                : (v) => setState(
                                    () => values['${field['id']}'] = v ?? '',
                                  ),
                          )
                        : TextFormField(
                            key: ValueKey('unifyField_${field['id']}'),
                            initialValue: values['${field['id']}'] ?? '',
                            decoration: InputDecoration(
                              labelText: '${field['label']}',
                              isDense: true,
                              border: const OutlineInputBorder(),
                            ),
                            onChanged: (v) => values['${field['id']}'] = v,
                          ),
                  ),
                ],
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            key: const Key('unifyCancel'),
            onPressed: busy ? null : () => answer(false),
            child: Text(widget.data['cancel_label']?.toString() ?? '취소'),
          ),
          FilledButton(
            key: const Key('unifyConfirm'),
            onPressed: busy ? null : () => answer(true),
            child: Text(widget.data['ok_label']?.toString() ?? '확인한 대표값으로 진행'),
          ),
        ],
      ),
    );
  }
}
