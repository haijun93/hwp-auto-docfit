import 'package:flutter/material.dart';

import '../../core/api/abbreviation_api.dart';
import '../../core/models/abbreviation.dart';
import 'abbreviation_editor.dart';

class AbbreviationManager extends StatefulWidget {
  const AbbreviationManager({super.key, required this.api});
  final ApiCall api;
  @override
  State<AbbreviationManager> createState() => _AbbreviationManagerState();
}

class _AbbreviationManagerState extends State<AbbreviationManager> {
  late final AbbreviationApi api;
  AbbreviationSnapshot? data;
  final search = TextEditingController();
  bool busy = false;
  String? error;

  @override
  void initState() {
    super.initState();
    api = AbbreviationApi(widget.api);
    request(api.load);
  }

  @override
  void dispose() {
    search.dispose();
    super.dispose();
  }

  Future<void> request(Future<AbbreviationSnapshot> Function() action) async {
    if (busy) return;
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final result = await action();
      if (mounted) setState(() => data = result);
    } catch (exception) {
      if (mounted) setState(() => error = '$exception');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> edit([AbbreviationEntry? entry]) async {
    if (busy || data == null || data!.running) return;
    final result = await showDialog<AbbreviationSnapshot>(
        context: context,
        barrierDismissible: false,
        builder: (_) =>
            AbbreviationEditor(api: api, formats: data!.formats, entry: entry));
    if (mounted && result != null) {
      setState(() {
        data = result;
        error = null;
      });
    }
  }

  Future<void> delete(AbbreviationEntry entry) async {
    final confirm = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
              title: const Text('준말 삭제'),
              content: Text(
                  '「${entry.key}」 사용자 등록을 삭제할까요? 같은 기본 준말이 있으면 기본값으로 돌아가요.'),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(context, false),
                    child: const Text('취소')),
                FilledButton(
                    key: const Key('confirmDeleteAbbreviation'),
                    onPressed: () => Navigator.pop(context, true),
                    child: const Text('삭제')),
              ],
            ));
    if (mounted && confirm == true) await request(() => api.delete(entry.key));
  }

  @override
  Widget build(BuildContext context) {
    final query = search.text.trim().toLowerCase();
    final entries = data?.entries
            .where((entry) => '${entry.key} ${entry.value} ${entry.label}'
                .toLowerCase()
                .contains(query))
            .toList() ??
        [];
    final locked = busy || data == null || data!.running;
    return Dialog(
      key: const Key('abbreviationManagerDialog'),
      insetPadding: const EdgeInsets.all(16),
      child: SizedBox(
        width: 720,
        height: 620,
        child: Padding(
          padding: const EdgeInsets.all(20),
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Row(children: [
              const Expanded(
                  child: Text('준말 관리',
                      style: TextStyle(
                          fontSize: 22, fontWeight: FontWeight.bold))),
              IconButton(
                  key: const Key('refreshAbbreviationsButton'),
                  tooltip: '새로 불러오기',
                  onPressed: busy ? null : () => request(api.load),
                  icon: const Icon(Icons.refresh)),
              IconButton(
                  tooltip: '닫기',
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.close)),
            ]),
            const Text('줄 맨 앞의 준말 뒤에 콜론(:)이 있을 때 본말로 바꿔요. 예: 요약: 내용'),
            SwitchListTile(
                contentPadding: EdgeInsets.zero,
                key: const Key('abbreviationDefaultsSwitch'),
                title: const Text('기본 준말 사용'),
                value: data?.useDefaults ?? true,
                onChanged: locked
                    ? null
                    : (value) => request(() => api.setDefaults(value))),
            TextField(
                key: const Key('abbreviationSearchField'),
                controller: search,
                decoration: const InputDecoration(
                    labelText: '준말·본말 검색', prefixIcon: Icon(Icons.search)),
                onChanged: (_) => setState(() {})),
            if (busy) const LinearProgressIndicator(),
            if (error != null)
              Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  child:
                      Text(error!, style: const TextStyle(color: Colors.red))),
            if (data?.running == true) const Text('작업 중에는 준말을 바꿀 수 없어요.'),
            Expanded(
                child: entries.isEmpty
                    ? Center(
                        child: Text(
                            data == null ? '목록을 불러오고 있어요.' : '일치하는 준말이 없어요.'))
                    : ListView.builder(
                        itemCount: entries.length,
                        itemBuilder: (context, index) {
                          final entry = entries[index];
                          return ListTile(
                            contentPadding: EdgeInsets.zero,
                            title: Text(
                                '${entry.key}${entry.builtin ? ' · 기본' : ''}'),
                            subtitle: Text(entry.label,
                                maxLines: 2, overflow: TextOverflow.ellipsis),
                            trailing:
                                Row(mainAxisSize: MainAxisSize.min, children: [
                              IconButton(
                                  key: Key('editAbbreviation-${entry.key}'),
                                  tooltip: '수정',
                                  onPressed: locked ? null : () => edit(entry),
                                  icon: const Icon(Icons.edit_outlined)),
                              if (!entry.builtin)
                                IconButton(
                                    key: Key('deleteAbbreviation-${entry.key}'),
                                    tooltip: '삭제',
                                    onPressed:
                                        locked ? null : () => delete(entry),
                                    icon: const Icon(Icons.delete_outline)),
                            ]),
                          );
                        })),
            const Text('학습한 표 서식은 그대로 보존돼요. 표 서식 학습은 전체 설정에서 할 수 있어요.',
                style: TextStyle(fontSize: 12)),
            const SizedBox(height: 12),
            FilledButton.icon(
                key: const Key('addAbbreviationButton'),
                onPressed: locked ? null : () => edit(),
                icon: const Icon(Icons.add),
                label: const Text('준말 등록')),
          ]),
        ),
      ),
    );
  }
}
