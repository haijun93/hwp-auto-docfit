import 'package:flutter/material.dart';

import '../../core/api/abbreviation_api.dart';
import '../../core/models/abbreviation.dart';

class AbbreviationEditor extends StatefulWidget {
  const AbbreviationEditor(
      {super.key, required this.api, required this.formats, this.entry});
  final AbbreviationApi api;
  final Map<String, String> formats;
  final AbbreviationEntry? entry;
  @override
  State<AbbreviationEditor> createState() => _AbbreviationEditorState();
}

class _AbbreviationEditorState extends State<AbbreviationEditor> {
  late final TextEditingController keyText, valueText;
  late String type, format;
  bool busy = false;
  String? error;

  @override
  void initState() {
    super.initState();
    final entry = widget.entry;
    keyText = TextEditingController(text: entry?.key ?? '');
    valueText =
        TextEditingController(text: entry?.type == 'text' ? entry?.value : '');
    type = entry?.type ?? 'text';
    format = entry?.type == 'format' ? entry!.value : 'title1';
  }

  @override
  void dispose() {
    keyText.dispose();
    valueText.dispose();
    super.dispose();
  }

  Future<void> save() async {
    if (busy) return;
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final result = await widget.api.save(
          keyText.text.trim(),
          type,
          type == 'text' ? valueText.text : format,
          widget.entry?.builtin == false ? widget.entry!.key : '');
      if (mounted) Navigator.pop(context, result);
    } catch (exception) {
      if (mounted) setState(() => error = '$exception');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => PopScope(
        canPop: !busy,
        child: AlertDialog(
          title: Text(widget.entry == null ? '준말 등록' : '준말 수정'),
          content: SizedBox(
            width: 480,
            child: SingleChildScrollView(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                TextField(
                    key: const Key('abbreviationKeyField'),
                    controller: keyText,
                    enabled: !busy,
                    maxLength: 12,
                    decoration: const InputDecoration(
                        labelText: '준말', helperText: '빈칸·콜론 없이 입력하세요.')),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  key: const Key('abbreviationTypeField'),
                  initialValue: type,
                  decoration: const InputDecoration(labelText: '본말 종류'),
                  items: const [
                    DropdownMenuItem(value: 'text', child: Text('문구')),
                    DropdownMenuItem(value: 'format', child: Text('서식 표'))
                  ],
                  onChanged:
                      busy ? null : (value) => setState(() => type = value!),
                ),
                const SizedBox(height: 16),
                if (type == 'text')
                  TextField(
                      key: const Key('abbreviationValueField'),
                      controller: valueText,
                      enabled: !busy,
                      maxLength: 500,
                      maxLines: 3,
                      decoration: const InputDecoration(labelText: '본말 문구'))
                else
                  DropdownButtonFormField<String>(
                    key: const Key('abbreviationFormatField'),
                    initialValue: format,
                    isExpanded: true,
                    decoration: const InputDecoration(labelText: '서식 종류'),
                    items: [
                      for (final entry in widget.formats.entries)
                        DropdownMenuItem(
                            value: entry.key,
                            child: Text(entry.value,
                                overflow: TextOverflow.ellipsis))
                    ],
                    onChanged: busy
                        ? null
                        : (value) => setState(() => format = value!),
                  ),
                if (widget.entry?.builtin == true)
                  const Padding(
                      padding: EdgeInsets.only(top: 12),
                      child: Text('기본 준말을 고치면 사용자 등록으로 저장돼요.')),
                if (error != null)
                  Padding(
                      padding: const EdgeInsets.only(top: 12),
                      child: Text(error!,
                          style: const TextStyle(color: Colors.red))),
                if (busy) const LinearProgressIndicator(),
              ]),
            ),
          ),
          actions: [
            TextButton(
                onPressed: busy ? null : () => Navigator.pop(context),
                child: const Text('취소')),
            FilledButton(
                key: const Key('saveAbbreviationButton'),
                onPressed: busy ? null : save,
                child: const Text('저장')),
          ],
        ),
      );
}
