import 'package:flutter/material.dart';
import '../../core/api/abbreviation_api.dart';

class UnifyAreaDialog extends StatefulWidget {
  const UnifyAreaDialog({super.key, required this.api, required this.data});

  final ApiCall api;
  final Map data;

  @override
  State<UnifyAreaDialog> createState() => _UnifyAreaDialogState();
}

class _UnifyAreaDialogState extends State<UnifyAreaDialog> {
  late final Set<Object> selected;
  bool busy = false;
  String error = '';

  @override
  void initState() {
    super.initState();
    final areas = widget.data['areas'] as List? ?? [];
    selected = {
      for (final a in areas)
        if (a['checked'] != false) (a['id'] ?? areas.indexOf(a)) as Object,
    };
  }

  Future<void> answer(bool accepted) async {
    setState(() => busy = true);
    try {
      await widget.api('resolve_dialog', [
        widget.data['id'],
        accepted,
        accepted ? selected.toList() : [],
        {},
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
    final areas = widget.data['areas'] as List? ?? [];

    return PopScope(
      canPop: false,
      child: AlertDialog(
        title: Text(widget.data['title']?.toString() ?? '편집 영역 확인'),
        content: SizedBox(
          width: 600,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (widget.data['message'] != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Text(widget.data['message'].toString()),
                ),
              if (error.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Text(error, style: const TextStyle(color: Colors.red)),
                ),
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Text(
                  '선택 ${selected.length} / 후보 ${areas.length}개',
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                  ),
                ),
              ),
              const Divider(),
              Flexible(
                child: areas.isEmpty
                    ? const Padding(
                        padding: EdgeInsets.all(16),
                        child: Text('대표 서식과 다른 적용 영역이 없습니다.'),
                      )
                    : ListView.builder(
                        shrinkWrap: true,
                        itemCount: areas.length,
                        itemBuilder: (context, index) {
                          final item = areas[index] as Map;
                          final id = (item['id'] ?? index) as Object;
                          final doc = item['doc'] ?? 'doc0';
                          final area = item['area'] ?? '$index';
                          final marker = item['marker'] ?? '';
                          final role = item['role'] ?? '';
                          final text = item['text'] ?? '';
                          final changes = item['changes'] ?? '';
                          final isChecked = selected.contains(id);

                          return CheckboxListTile(
                            key: Key('unifyArea_${doc}_$area'),
                            value: isChecked,
                            onChanged: busy
                                ? null
                                : (val) {
                                    setState(() {
                                      if (val == true) {
                                        selected.add(id);
                                      } else {
                                        selected.remove(id);
                                      }
                                    });
                                  },
                            title: Text(
                              '$marker / $role: $text',
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(fontSize: 13),
                            ),
                            subtitle: changes.isNotEmpty
                                ? Text(
                                    '변경: $changes',
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: Theme.of(
                                        context,
                                      ).colorScheme.primary,
                                    ),
                                  )
                                : null,
                            dense: true,
                          );
                        },
                      ),
              ),
            ],
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
            child: Text(widget.data['ok_label']?.toString() ?? '선택 영역만 적용'),
          ),
        ],
      ),
    );
  }
}
