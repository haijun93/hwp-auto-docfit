import 'package:flutter/material.dart';
import '../../core/api/abbreviation_api.dart';
import '../style_unify/unify_area_dialog.dart';
import '../style_unify/unify_pick_style_dialog.dart';
import '../style_unify/unify_result_dialog.dart';

class BackendDialog extends StatefulWidget {
  const BackendDialog({super.key, required this.api, required this.data});
  final ApiCall api;
  final Map data;
  @override
  State<BackendDialog> createState() => _BackendDialogState();
}

class _BackendDialogState extends State<BackendDialog> {
  late final Set<Object> selected;
  final Map<String, String> values = {};
  bool busy = false;
  String error = '';
  @override
  void initState() {
    super.initState();
    selected = {
      for (final item in widget.data['choices'] as List? ?? [])
        item['id'] as Object,
    };
  }

  Future<void> answer(bool accepted) async {
    setState(() => busy = true);
    try {
      await widget.api('resolve_dialog', [
        widget.data['id'],
        accepted,
        selected.toList(),
        values,
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
    final kind = widget.data['kind'];
    if (kind == 'style_unify_profile') {
      return UnifyPickStyleDialog(api: widget.api, data: widget.data);
    }
    if (kind == 'style_unify_regions') {
      return UnifyAreaDialog(api: widget.api, data: widget.data);
    }
    if (kind == 'style_unify_result') {
      return UnifyResultDialog(api: widget.api, data: widget.data);
    }
    return PopScope(
      canPop: false,
      child: AlertDialog(
        title: Text('${widget.data['title']}'),
        content: SizedBox(
          width: 640,
          height: 400,
          child: ListView(
            children: [
              Text('${widget.data['message']}'),
              if (error.isNotEmpty) Text(error),
              for (final item in widget.data['choices'] as List? ?? [])
                CheckboxListTile(
                  title: Text('${item['label']}'),
                  value: selected.contains(item['id']),
                  onChanged: busy
                      ? null
                      : (value) => setState(() {
                          if (value == true) {
                            selected.add(item['id'] as Object);
                          } else {
                            selected.remove(item['id']);
                          }
                        }),
                ),
              for (final item in widget.data['fields'] as List? ?? [])
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 6),
                  child: item['type'] == 'bool'
                      ? DropdownButtonFormField<String>(
                          initialValue: '${item['value']}',
                          decoration: InputDecoration(
                            labelText: '${item['label']}',
                          ),
                          items: const [
                            DropdownMenuItem(value: '', child: Text('판정 보류')),
                            DropdownMenuItem(value: 'True', child: Text('적용')),
                            DropdownMenuItem(
                              value: 'False',
                              child: Text('미적용'),
                            ),
                          ],
                          onChanged: busy
                              ? null
                              : (value) =>
                                    values['${item['id']}'] = value ?? '',
                        )
                      : TextFormField(
                          initialValue: '${item['value']}',
                          decoration: InputDecoration(
                            labelText: '${item['label']}',
                          ),
                          onChanged: (value) => values['${item['id']}'] = value,
                        ),
                ),
            ],
          ),
        ),
        actions: [
          if (widget.data['confirm'] == true)
            TextButton(
              onPressed: busy ? null : () => answer(false),
              child: Text(
                widget.data['cancel_label'] is String
                    ? widget.data['cancel_label'] as String
                    : '취소',
              ),
            ),
          FilledButton(
            onPressed: busy ? null : () => answer(true),
            child: Text(
              widget.data['ok_label'] is String
                  ? widget.data['ok_label'] as String
                  : (widget.data['confirm'] == true ? '확인 후 진행' : '확인'),
            ),
          ),
        ],
      ),
    );
  }
}
