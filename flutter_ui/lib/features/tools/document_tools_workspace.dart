import '../../core/close_guards.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../core/api/abbreviation_api.dart';

class DocumentToolsWorkspace extends StatefulWidget {
  const DocumentToolsWorkspace({
    super.key,
    required this.api,
    this.initial = 'convert',
    this.isModal = true,
  });
  final ApiCall api;
  final String initial;
  final bool isModal;
  @override
  State<DocumentToolsWorkspace> createState() => _ToolsState();
}

class _ToolsState extends State<DocumentToolsWorkspace> {
  final input = TextEditingController(), output = TextEditingController();
  late String mode;
  String status = '', calculation = 'col_sum';
  bool busy = false, closing = false;
  CloseLease? _closeLease;
  static const modes = {
    'clean': 'AI 답변 기호 정리',
    'convert': '개조식 변환',
    'labels': '라벨 텍스트 변환',
    'amount': '금액 한글화',
    'commas': '숫자 쉼표',
    'weekdays': '날짜·요일',
    'date_diff': '날짜 차이 (두 날짜를 줄로 구분)',
    'age': '만 나이',
    'mask_rrn': '주민번호 가리기',
    'table_calc': '표 합계',
  };

  @override
  void initState() {
    super.initState();
    mode = modes.containsKey(widget.initial) ? widget.initial : 'convert';
    if (widget.isModal) {
      _closeLease = CloseGuards.register(() async {
        if (busy || !canCloseEditor(context)) return false;
        leave();
        return true;
      });
    }
  }

  @override
  void dispose() {
    _closeLease?.release();
    input.dispose();
    output.dispose();
    super.dispose();
  }

  Future<Map> call(String name, Map payload) async {
    final raw = await widget.api('document_tool', [name, payload]);
    if (raw is! Map || raw['ok'] != true) {
      final problem = raw is Map ? raw['error'] : null;
      throw Exception(
        problem is Map ? problem['message'] ?? '연결 응답을 확인해 주세요.' : '응답 형식 오류',
      );
    }
    return raw['data'] as Map;
  }

  Future<void> run() async {
    if (busy) return;
    setState(() => busy = true);
    try {
      final data = await call(mode, {
        'text': input.text,
        'operation': calculation,
      });
      if (mounted) setState(() => output.text = '${data['text'] ?? ''}');
    } catch (e) {
      if (mounted) setState(() => status = '$e');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> addDocument() async {
    if (busy) return;
    setState(() => busy = true);
    try {
      final result = await call('add_text', {
        'text': output.text.isEmpty ? input.text : output.text,
      });
      if (mounted) setState(() => status = '문서 목록에 추가: ${result['path']}');
    } catch (e) {
      if (mounted) setState(() => status = '$e');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  void leave() {
    if (busy || closing) return;
    if (!Navigator.of(context).canPop()) return; // 탭 안에서는 닫을 화면이 없다(앱 멈춤 방지)
    setState(() => closing = true);
    Navigator.pop(context);
  }

  Widget editor() => TextField(
    controller: input,
    maxLines: null,
    expands: true,
    textAlignVertical: TextAlignVertical.top,
    decoration: const InputDecoration(
      labelText: '입력',
      alignLabelWithHint: true,
      border: OutlineInputBorder(),
    ),
  );

  @override
  Widget build(BuildContext context) => PopScope(
    canPop: closing || !busy,
    onPopInvokedWithResult: (didPop, _) {
      if (!didPop) leave();
    },
    child: Scaffold(
      appBar: AppBar(
        // 탭 안에서는 ← 버튼을 보이지 않는다. 새 화면으로 열었을 때만 표시.
        automaticallyImplyLeading: false,
        leading: !Navigator.of(context).canPop()
            ? null
            : IconButton(
                onPressed: busy ? null : leave,
                icon: const Icon(Icons.arrow_back),
              ),
        title: const Text('텍스트 입력'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            DropdownButtonFormField<String>(
              initialValue: mode,
              items: [
                for (final item in modes.entries)
                  DropdownMenuItem(value: item.key, child: Text(item.value)),
              ],
              onChanged: busy
                  ? null
                  : (value) {
                      if (value != null) setState(() => mode = value);
                    },
            ),
            const SizedBox(height: 8),
            if (mode == 'table_calc')
              DropdownButtonFormField<String>(
                initialValue: calculation,
                items: const [
                  DropdownMenuItem(value: 'col_sum', child: Text('열 합계')),
                  DropdownMenuItem(value: 'col_avg', child: Text('열 평균')),
                  DropdownMenuItem(value: 'row_sum', child: Text('행 합계')),
                  DropdownMenuItem(value: 'col_ratio', child: Text('열 비율')),
                ],
                onChanged: busy
                    ? null
                    : (value) =>
                          setState(() => calculation = value ?? 'col_sum'),
              ),
            Wrap(
              spacing: 8,
              runSpacing: 4,
              children: [
                FilledButton(
                  onPressed: busy ? null : run,
                  child: const Text('실행 / 미리보기'),
                ),
                TextButton(
                  onPressed: busy
                      ? null
                      : () =>
                            Clipboard.setData(ClipboardData(text: output.text)),
                  child: const Text('결과 복사'),
                ),
                OutlinedButton(
                  onPressed: busy ? null : addDocument,
                  child: const Text('문서 목록에 추가'),
                ),
              ],
            ),
            if (busy) const LinearProgressIndicator(),
            if (status.isNotEmpty) Text(status),
            const SizedBox(height: 8),
            Expanded(
              child: LayoutBuilder(
                builder: (context, box) {
                  final result = TextField(
                    controller: output,
                    readOnly: true,
                    maxLines: null,
                    expands: true,
                    textAlignVertical: TextAlignVertical.top,
                    decoration: const InputDecoration(
                      labelText: '변환 결과',
                      alignLabelWithHint: true,
                      border: OutlineInputBorder(),
                    ),
                  );
                  if (box.maxWidth < 760) {
                    return Column(
                      children: [
                        Expanded(child: editor()),
                        const SizedBox(height: 8),
                        Expanded(child: result),
                      ],
                    );
                  }
                  return Row(
                    children: [
                      Expanded(child: editor()),
                      const SizedBox(width: 12),
                      Expanded(child: result),
                    ],
                  );
                },
              ),
            ),
          ],
        ),
      ),
    ),
  );
}
