import 'package:flutter/material.dart';

class _MergeItem {
  _MergeItem({required this.id, required this.file});
  final int id;
  final Map file;
}

/// PDF 하나로 합치기 순서 정하기 대화상자.
class MergeOrderDialog extends StatefulWidget {
  const MergeOrderDialog({
    super.key,
    required this.files,
  });

  final List<Map> files;

  @override
  State<MergeOrderDialog> createState() => _MergeOrderDialogState();
}

class _MergeOrderDialogState extends State<MergeOrderDialog> {
  late final List<_MergeItem> _items = [
    for (var i = 0; i < widget.files.length; i++)
      _MergeItem(id: i, file: widget.files[i]),
  ];

  static IconData _formatIcon(String name) {
    final lower = name.toLowerCase();
    if (lower.endsWith('.pdf')) return Icons.picture_as_pdf_outlined;
    if (lower.endsWith('.hwp') || lower.endsWith('.hwpx')) {
      return Icons.description_outlined;
    }
    if (lower.endsWith('.doc') || lower.endsWith('.docx')) {
      return Icons.article_outlined;
    }
    if (lower.endsWith('.png') ||
        lower.endsWith('.jpg') ||
        lower.endsWith('.jpeg')) {
      return Icons.image_outlined;
    }
    if (lower.endsWith('.txt') || lower.endsWith('.md')) {
      return Icons.text_snippet_outlined;
    }
    return Icons.insert_drive_file_outlined;
  }

  static Color _formatIconColor(String name) {
    final lower = name.toLowerCase();
    if (lower.endsWith('.pdf')) return const Color(0xffdc2626);
    if (lower.endsWith('.hwp') || lower.endsWith('.hwpx')) {
      return const Color(0xff2563eb);
    }
    if (lower.endsWith('.png') ||
        lower.endsWith('.jpg') ||
        lower.endsWith('.jpeg')) {
      return const Color(0xff059669);
    }
    return const Color(0xff64748b);
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      key: const Key('mergeOrderDialog'),
      insetPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 420, maxHeight: 560),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: const Color(0xffedf3ff),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(
                      Icons.merge_type,
                      color: Color(0xff2563eb),
                      size: 22,
                    ),
                  ),
                  const SizedBox(width: 12),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'PDF 합칠 순서 정하기',
                          style: TextStyle(
                            fontSize: 17,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        SizedBox(height: 2),
                        Text(
                          '맨 위 줄이 PDF 첫 쪽이 됩니다.',
                          style: TextStyle(
                            fontSize: 12,
                            color: Color(0xff64748b),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 14),
              Flexible(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: ReorderableListView.builder(
                    shrinkWrap: true,
                    buildDefaultDragHandles: false,
                    itemCount: _items.length,
                    onReorderItem: (oldIndex, newIndex) {
                      setState(() {
                        final item = _items.removeAt(oldIndex);
                        _items.insert(newIndex, item);
                      });
                    },
                    itemBuilder: (context, i) {
                      final item = _items[i];
                      final file = item.file;
                      final name = '${file['name'] ?? file['path'] ?? ''}';
                      return Container(
                        key: ValueKey(item.id),
                        margin: const EdgeInsets.symmetric(vertical: 3),
                        padding: const EdgeInsets.fromLTRB(8, 6, 4, 6),
                        decoration: BoxDecoration(
                          color: const Color(0xfff8fafc),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: const Color(0xffe2e8f0)),
                        ),
                        child: Row(
                          children: [
                            CircleAvatar(
                              radius: 11,
                              backgroundColor: const Color(0xffedf3ff),
                              child: Text(
                                '${i + 1}',
                                style: const TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w700,
                                  color: Color(0xff2563eb),
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Icon(
                              _formatIcon(name),
                              size: 20,
                              color: _formatIconColor(name),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Tooltip(
                                message: name,
                                child: Text(
                                  name,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.w600,
                                    color: Color(0xff1e293b),
                                  ),
                                ),
                              ),
                            ),
                            IconButton(
                              key: Key('mergeUp_$i'),
                              tooltip: '위로 이동',
                              visualDensity: VisualDensity.compact,
                              padding: EdgeInsets.zero,
                              constraints: const BoxConstraints(
                                minWidth: 28,
                                minHeight: 28,
                              ),
                              icon: Icon(
                                Icons.arrow_upward_rounded,
                                size: 18,
                                color: i > 0
                                    ? const Color(0xff475569)
                                    : const Color(0xffcbd5e1),
                              ),
                              onPressed: i > 0
                                  ? () => setState(() {
                                      final cur = _items.removeAt(i);
                                      _items.insert(i - 1, cur);
                                    })
                                  : null,
                            ),
                            IconButton(
                              key: Key('mergeDown_$i'),
                              tooltip: '아래로 이동',
                              visualDensity: VisualDensity.compact,
                              padding: EdgeInsets.zero,
                              constraints: const BoxConstraints(
                                minWidth: 28,
                                minHeight: 28,
                              ),
                              icon: Icon(
                                Icons.arrow_downward_rounded,
                                size: 18,
                                color: i < _items.length - 1
                                    ? const Color(0xff475569)
                                    : const Color(0xffcbd5e1),
                              ),
                              onPressed: i < _items.length - 1
                                  ? () => setState(() {
                                      final cur = _items.removeAt(i);
                                      _items.insert(i + 1, cur);
                                    })
                                  : null,
                            ),
                            ReorderableDragStartListener(
                              index: i,
                              child: const Tooltip(
                                message: '끌어서 순서 바꾸기',
                                child: Padding(
                                  padding: EdgeInsets.symmetric(horizontal: 4),
                                  child: Icon(
                                    Icons.drag_indicator_rounded,
                                    size: 20,
                                    color: Color(0xff94a3b8),
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton(
                    key: const Key('mergeCancelButton'),
                    onPressed: () => Navigator.of(context).pop(null),
                    child: const Text('취소'),
                  ),
                  const SizedBox(width: 8),
                  FilledButton(
                    key: const Key('mergeStartButton'),
                    onPressed: () {
                      final paths = _items
                          .map(
                            (item) =>
                                '${item.file['path'] ?? item.file['name'] ?? ''}',
                          )
                          .toList();
                      Navigator.of(context).pop(paths);
                    },
                    child: const Text('합치기 시작'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
