import 'package:flutter/material.dart';
import '../../core/api/abbreviation_api.dart';

class ProfileEditor extends StatefulWidget {
  const ProfileEditor({super.key, required this.api, required this.identifier});
  final ApiCall api;
  final String identifier;
  @override
  State<ProfileEditor> createState() => _ProfileEditorState();
}

class _ProfileEditorState extends State<ProfileEditor> {
  Map data = {};
  String error = '';
  bool busy = false;
  int generation = 0;
  final Map<String, Map> edits = {};
  @override
  void initState() {
    super.initState();
    request('get');
  }

  Future<void> request(String action) async {
    if (busy) return;
    setState(() => busy = true);
    try {
      final raw = await widget.api('format_profile', [
        action,
        {
          'id': data['id'] ?? widget.identifier,
          'revision': data['revision'],
          'edits': edits.values.toList(),
        },
      ]);
      if (raw is! Map || raw['ok'] != true) {
        final problem = raw is Map ? raw['error'] : null;
        throw Exception(
          problem is Map ? problem['message'] ?? '연결 응답을 확인해 주세요.' : '응답 형식 오류',
        );
      }
      if (mounted) {
        setState(() {
          data = raw['data'] as Map;
          edits.clear();
          generation++;
          error = '';
        });
      }
    } catch (e) {
      if (mounted) setState(() => error = '$e');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  void edit(List path, Map field, String value) {
    edits['$path:${field['key']}'] = {
      'path': path,
      'key': field['key'],
      'value': value,
    };
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: Text('${data['name'] ?? '서식 세부 편집'}'),
    content: SizedBox(
      width: 720,
      height: 520,
      child: Column(
        children: [
          if (busy) const LinearProgressIndicator(),
          if (error.isNotEmpty)
            Text(
              error,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          Text(
            data['coverage'] is Map
                ? '서식 요소 ${(data['coverage'] as Map)['total']}개 중 ${(data['coverage'] as Map)['applied']}개 적용'
                : '분석 자료 없음',
          ),
          Expanded(
            child: ListView(
              children: [
                if ((data['nodes'] as List? ?? []).isEmpty)
                  const Padding(
                    padding: EdgeInsets.all(16),
                    child: Text(
                      '편집할 분석 자료가 없습니다. 예시 HWPX에서 서식을 분석한 뒤 계층·칸별 속성을 수정하세요.',
                    ),
                  ),
                for (final node in data['nodes'] as List? ?? [])
                  ExpansionTile(
                    title: Text('${node['label']}'),
                    children: [
                      for (final field in node['fields'] as List)
                        Padding(
                          padding: const EdgeInsets.all(8),
                          child: TextFormField(
                            key: ValueKey(
                              '$generation:${node['path']}:${field['key']}',
                            ),
                            initialValue: '${field['value']}',
                            enabled: !busy && field['editable'] == true,
                            decoration: InputDecoration(
                              labelText: '${field['label']}',
                              helperText: (field['choices'] as List).isNotEmpty
                                  ? '선택값: ${(field['choices'] as List).join(', ')}'
                                  : null,
                            ),
                            onChanged: (value) =>
                                edit(node['path'] as List, field as Map, value),
                          ),
                        ),
                    ],
                  ),
              ],
            ),
          ),
        ],
      ),
    ),
    actions: [
      TextButton(
        onPressed: busy ? null : () => request('restore'),
        child: const Text('선택 요소 분석값 복원'),
      ),
      TextButton(
        onPressed: busy ? null : () => Navigator.pop(context),
        child: const Text('닫기'),
      ),
      FilledButton(
        onPressed: busy ? null : () => request('save'),
        child: const Text('저장·적용'),
      ),
    ],
  );
}
