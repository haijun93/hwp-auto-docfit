import 'package:flutter/material.dart';
import '../../core/api/abbreviation_api.dart';

class SettingsDialog extends StatefulWidget {
  const SettingsDialog({super.key, required this.api});
  final ApiCall api;
  @override
  State<SettingsDialog> createState() => _SettingsDialogState();
}

class _SettingsDialogState extends State<SettingsDialog> {
  Map? snapshot;
  final Map<String, TextEditingController> inputs = {};
  final Map<String, Object?> changed = {};
  final search = TextEditingController();
  bool busy = true;
  String? error;
  @override
  void initState() {
    super.initState();
    load();
  }

  @override
  void dispose() {
    search.dispose();
    for (final input in inputs.values) {
      input.dispose();
    }
    super.dispose();
  }

  Future<Map> request(String method, List<Object?> args) async {
    final response = await widget.api(method, args);
    if (response is! Map || response['api_version'] != 1) {
      throw Exception('앱 연결과 버전을 확인해 주세요.');
    }
    if (response['ok'] != true) {
      throw Exception(
          '${(response['error'] as Map?)?['message'] ?? '설정을 적용하지 못했어요.'}');
    }
    return response['data'] as Map;
  }

  Future<void> load() async {
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final data = await request('get_settings', []);
      if (!mounted) return;
      for (final input in inputs.values) {
        input.dispose();
      }
      inputs.clear();
      final values = data['values'] as Map;
      for (final field in data['fields'] as List) {
        if (field['type'] != 'boolean') {
          inputs[field['key']] =
              TextEditingController(text: '${values[field['key']] ?? ''}');
        }
      }
      setState(() {
        snapshot = data;
        changed.clear();
      });
    } catch (e) {
      if (mounted) setState(() => error = '$e');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> save() async {
    if (busy || snapshot == null || changed.isEmpty) return;
    setState(() {
      busy = true;
      error = null;
    });
    try {
      await request('save_settings',
          [Map<String, Object?>.from(changed), snapshot!['revision']]);
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) setState(() => error = '$e');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  void restoreDefaults() {
    for (final field in snapshot!['fields'] as List) {
      changed[field['key']] = field['default'];
      inputs[field['key']]?.text = '${field['default'] ?? ''}';
    }
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final fields = (snapshot?['fields'] as List? ?? [])
        .where((field) => '${field['label']}'.contains(search.text.trim()))
        .toList();
    final locked = busy || snapshot?['running'] == true;
    final values = snapshot?['values'] as Map? ?? {};
    return PopScope(
        canPop: !busy,
        child: AlertDialog(
          title: const Text('전체 설정'),
          content: SizedBox(
              width: 780,
              height: 560,
              child: Column(children: [
                TextField(
                    controller: search,
                    decoration: const InputDecoration(labelText: '설정 검색'),
                    onChanged: (_) => setState(() {})),
                if (busy) const LinearProgressIndicator(),
                if (error != null)
                  Text(error!,
                      style: TextStyle(
                          color: Theme.of(context).colorScheme.error)),
                if (snapshot?['running'] == true)
                  const Text('작업 중에는 설정을 바꿀 수 없어요.'),
                Expanded(
                    child: ListView.builder(
                        itemCount: fields.length,
                        itemBuilder: (context, index) {
                          final field = fields[index] as Map;
                          final key = '${field['key']}';
                          if (field['type'] == 'boolean') {
                            return SwitchListTile(
                                key: ValueKey(key),
                                title: Text('${field['label']}'),
                                value: (changed.containsKey(key)
                                        ? changed[key]
                                        : values[key]) ==
                                    true,
                                onChanged: locked
                                    ? null
                                    : (value) =>
                                        setState(() => changed[key] = value));
                          }
                          return Padding(
                              padding: const EdgeInsets.symmetric(vertical: 8),
                              child: TextField(
                                  key: ValueKey(key),
                                  controller: inputs[key],
                                  enabled: !locked,
                                  keyboardType: field['type'] == 'number'
                                      ? const TextInputType.numberWithOptions(
                                          decimal: true)
                                      : TextInputType.text,
                                  decoration: InputDecoration(
                                      labelText: '${field['label']}',
                                      border: const OutlineInputBorder()),
                                  onChanged: (value) {
                                    changed[key] = value;
                                    setState(() {});
                                  }));
                        })),
              ])),
          actions: [
            TextButton(
                onPressed: locked || snapshot == null ? null : restoreDefaults,
                child: const Text('기본값 복원')),
            if (error != null)
              TextButton(
                  onPressed: busy ? null : load, child: const Text('다시 불러오기')),
            TextButton(
                onPressed: busy ? null : () => Navigator.pop(context, false),
                child: const Text('취소')),
            FilledButton(
                onPressed: locked || changed.isEmpty ? null : save,
                child: const Text('변경사항 적용')),
          ],
        ));
  }
}
