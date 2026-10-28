import 'package:flutter/material.dart';
import '../../core/api/abbreviation_api.dart';

class UnifyResultDialog extends StatefulWidget {
  const UnifyResultDialog({super.key, required this.api, required this.data});

  final ApiCall api;
  final Map data;

  @override
  State<UnifyResultDialog> createState() => _UnifyResultDialogState();
}

class _UnifyResultDialogState extends State<UnifyResultDialog> {
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
    final result = (widget.data['result'] as Map?) ?? {};
    final status = result['status']?.toString() ?? 'unknown';
    final statusText =
        result['status_text']?.toString() ??
        (status == 'passed' ? '검수 통과' : status);
    final checked = result['checked'] ?? 0;
    final issues = (result['issues'] as List?) ?? [];
    final notCheckable = (result['not_checkable'] as List?) ?? [];
    final unresolved = (result['unresolved'] as List?) ?? [];
    final fileName = result['file']?.toString() ?? '';

    final isSuccess = status == 'passed';

    return PopScope(
      canPop: false,
      child: AlertDialog(
        title: Text(widget.data['title']?.toString() ?? '작업 결과 확인'),
        content: SizedBox(
          width: 580,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (widget.data['message'] != null)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Text(
                      widget.data['message'].toString(),
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ),
                if (error.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Text(
                      error,
                      style: const TextStyle(color: Colors.red),
                    ),
                  ),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: isSuccess
                        ? Colors.green.withAlpha(25)
                        : Colors.orange.withAlpha(25),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(
                      color: isSuccess ? Colors.green : Colors.orange,
                    ),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        isSuccess ? Icons.check_circle : Icons.warning_amber,
                        color: isSuccess ? Colors.green : Colors.orange,
                        size: 28,
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              statusText,
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 14,
                              ),
                            ),
                            if (fileName.isNotEmpty)
                              Text(
                                fileName,
                                style: const TextStyle(fontSize: 12),
                                overflow: TextOverflow.ellipsis,
                              ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  '검사 문장 $checked개 · 불일치 ${issues.length}개 · 판정 보류 ${notCheckable.length}개 · 미확정 ${unresolved.length}개',
                  style: const TextStyle(fontSize: 13),
                ),
                if (result['error'] != null)
                  Text(
                    '오류: ${result['error']}',
                    style: const TextStyle(color: Colors.red),
                  ),
                const Divider(height: 24),
                if (issues.isNotEmpty) ...[
                  const Text(
                    '[남은 불일치]',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                  ),
                  const SizedBox(height: 4),
                  for (final issue in issues)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 2),
                      child: Text(
                        '• ${issue is Map ? '${issue['text'] ?? ''}\n항목: ${(issue['fields'] as List? ?? []).join(', ')}' : issue}',
                        style: const TextStyle(fontSize: 12),
                      ),
                    ),
                  const SizedBox(height: 8),
                ],
                if (notCheckable.isNotEmpty) ...[
                  const Text(
                    '[판정 보류]',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  for (final group in notCheckable)
                    Text(
                      '• ${group['marker']} / ${group['role']} — ${(group['fields'] as List? ?? []).join(', ')}',
                    ),
                ],
                if (unresolved.isNotEmpty) ...[
                  const Text(
                    '[대표값 미확정 문단 (빨간색 표시)]',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                      color: Colors.red,
                    ),
                  ),
                  const SizedBox(height: 4),
                  for (final item in unresolved)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 2),
                      child: Text(
                        '• ${item is Map ? '${item['text'] ?? ''}\n미확정: ${(item['fields'] as List? ?? []).join(', ')} · ${item['red_marked'] == true ? '빨간 표시 확인' : '빨간 표시 미확인'}' : item}',
                        style: const TextStyle(fontSize: 12),
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
            child: Text(widget.data['cancel_label']?.toString() ?? '닫기'),
          ),
          FilledButton(
            key: const Key('unifyConfirm'),
            onPressed: busy ? null : () => answer(true),
            child: Text(widget.data['ok_label']?.toString() ?? '결과 확인'),
          ),
        ],
      ),
    );
  }
}
