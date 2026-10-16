import 'package:flutter/material.dart';
import '../../core/api/abbreviation_api.dart';

class TableTemplatePanel extends StatefulWidget {
  const TableTemplatePanel({
    super.key,
    required this.api,
    required this.running,
  });
  final ApiCall api;
  final bool running;
  @override
  State<TableTemplatePanel> createState() => _TableTemplatePanelState();
}

class _TableTemplatePanelState extends State<TableTemplatePanel> {
  final path = TextEditingController();
  Map data = const {};
  String? error;
  bool busy = false;
  @override
  void initState() {
    super.initState();
    request('get');
  }

  @override
  void dispose() {
    path.dispose();
    super.dispose();
  }

  Future<void> request(String action) async {
    if (busy) return;
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final value = await widget.api('table_template', [
        action,
        {'path': path.text.trim()},
      ]);
      if (value is! Map || value['ok'] != true) {
        final problem = value is Map ? value['error'] : null;
        throw Exception(
          problem is Map
              ? problem['message'] ?? '표 서식을 읽지 못했습니다.'
              : '연결 응답을 확인해 주세요.',
        );
      }
      if (mounted) setState(() => data = value['data'] as Map);
    } catch (e) {
      if (mounted) setState(() => error = '$e');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final style = data['preview'] as Map?;
    final rows = (style?['rows'] as num?)?.toInt() ?? 0;
    final cols = (style?['cols'] as num?)?.toInt() ?? 0;
    final head = (style?['header_rows'] as num?)?.toInt() ?? 1;
    return ListView(
      children: [
        const Text(
          '기본 데이터 표',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        const Text(
          '준말 ‘표’의 본말과 같은 설정입니다. 선택한 프로파일에 자체 표 서식이 있으면 프로파일 서식이 우선합니다.',
        ),
        const SizedBox(height: 12),
        Text('${data['description'] ?? '불러오는 중…'}'),
        TextField(
          controller: path,
          enabled: !busy && !widget.running,
          decoration: const InputDecoration(
            labelText: '예시 HWPX 경로',
            hintText: '비워 두면 데스크톱 파일 선택 창이 열립니다.',
          ),
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            FilledButton(
              onPressed: busy || widget.running ? null : () => request('learn'),
              child: const Text('예시 표 학습'),
            ),
            OutlinedButton(
              onPressed: busy || widget.running ? null : () => request('reset'),
              child: const Text('내장 표 서식으로 초기화'),
            ),
          ],
        ),
        if (busy) const LinearProgressIndicator(),
        if (error != null)
          Text(
            error!,
            style: TextStyle(color: Theme.of(context).colorScheme.error),
          ),
        if (style != null) ...[
          const SizedBox(height: 16),
          Text('템플릿 구조 미리보기 · $rows행 × $cols열 · 머리글 $head행'),
          const Text('아래는 구조를 표시한 미리보기입니다. 실제 한/글 조판 결과는 문서 적용 후 확인하세요.'),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: DataTable(
              columns: [
                for (var c = 0; c < cols.clamp(1, 8); c++)
                  DataColumn(label: Text('${c + 1}열')),
              ],
              rows: [
                for (var r = 0; r < rows.clamp(0, 8); r++)
                  DataRow(
                    cells: [
                      for (var c = 0; c < cols.clamp(1, 8); c++)
                        DataCell(
                          Text('${r < head ? '머리글' : '본문'} ${r + 1}-${c + 1}'),
                        ),
                    ],
                  ),
              ],
            ),
          ),
        ],
      ],
    );
  }
}
