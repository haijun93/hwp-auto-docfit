import 'package:flutter/material.dart';
import '../../core/api/abbreviation_api.dart';

class FormatExampleEditDialog extends StatefulWidget {
  const FormatExampleEditDialog({
    super.key,
    required this.api,
    required this.data,
  });

  final ApiCall api;
  final Map data;

  @override
  State<FormatExampleEditDialog> createState() =>
      _FormatExampleEditDialogState();
}

class _FormatExampleEditDialogState extends State<FormatExampleEditDialog> {
  bool busy = false;
  String error = '';

  Future<void> answer(bool accepted) async {
    setState(() => busy = true);
    try {
      await widget.api('resolve_dialog', [widget.data['id'], accepted, [], {}]);
      if (mounted) Navigator.pop(context);
    } catch (e) {
      if (mounted) setState(() => error = '$e');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final title = widget.data['title']?.toString() ?? '서식 예시 문서 편집';
    final message =
        widget.data['message']?.toString() ??
        '열린 한/글 창에서 예시 문서를 작성하세요.\n\n'
            '□·ㅇ·-·※ 같은 항목기호를 섞어 원하는 계층 구조로 쓰면, 기호별로 가장 많이 쓴 '
            '글꼴·크기·들여쓰기가 그 기호의 서식이 됩니다. 다 쓰면 \'분석 시작\'을 누르세요.\n'
            '서식 이름은 첫 문장의 앞 8글자로 정하며 나중에 \'이름 바꾸기…\'로 고칠 수 있습니다.';
    final dataError = widget.data['error']?.toString() ?? '';
    final displayError = error.isNotEmpty ? error : dataError;

    return PopScope(
      canPop: false,
      child: AlertDialog(
        title: Row(
          children: [
            const Icon(Icons.edit_note_rounded, color: Color(0xff2563eb)),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                title,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
        content: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 400),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xffeff6ff),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xffbfdbfe)),
                  ),
                  child: Row(
                    children: [
                      const Icon(
                        Icons.description_outlined,
                        color: Color(0xff2563eb),
                        size: 24,
                      ),
                      const SizedBox(width: 10),
                      const Expanded(
                        child: Text(
                          '열린 한/글 창에서 예시 문서를 작성하세요.',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w700,
                            color: Color(0xff1e3a8a),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  message,
                  style: const TextStyle(
                    fontSize: 13,
                    height: 1.5,
                    color: Color(0xff334155),
                  ),
                ),
                if (displayError.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Container(
                    key: const Key('formatExampleError'),
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: const Color(0xfffef2f2),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: const Color(0xfffca5a5)),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(
                          Icons.error_outline_rounded,
                          color: Color(0xffdc2626),
                          size: 18,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            displayError,
                            style: const TextStyle(
                              fontSize: 12,
                              color: Color(0xffb91c1c),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            key: const Key('formatExampleCancel'),
            onPressed: busy ? null : () => answer(false),
            child: Text(widget.data['cancel_label']?.toString() ?? '취소'),
          ),
          FilledButton(
            key: const Key('formatExampleConfirm'),
            onPressed: busy ? null : () => answer(true),
            child: Text(widget.data['ok_label']?.toString() ?? '분석 시작'),
          ),
        ],
      ),
    );
  }
}
