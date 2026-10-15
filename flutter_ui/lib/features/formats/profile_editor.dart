import '../../core/close_guards.dart';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import '../../core/api/abbreviation_api.dart';
import '../settings/kiosk_theme.dart';
import 'element_preview.dart';

/// 서식 세부 편집: 왼쪽에서 요소(문장 계층·서식 표·일반 표·쪽)를 고르고,
/// 오른쪽에서 '문서에서 이렇게 보여요' 미리보기를 보며 값을 바꾼다.
class ProfileEditor extends StatefulWidget {
  const ProfileEditor({super.key, required this.api, required this.identifier});
  final ApiCall api;
  final String identifier;
  @override
  State<ProfileEditor> createState() => _ProfileEditorState();
}

const _sections = [
  (
    '글자',
    [
      'font',
      'font_latin',
      'size',
      'bold',
      'italic',
      'underline',
      'strikeout',
      'color',
      'shade',
      'ratio',
      'spacing',
    ],
  ),
  (
    '문단',
    [
      'align',
      'left',
      'right',
      'indent',
      'prev',
      'next',
      'line_type',
      'line',
      'break_word',
    ],
  ),
  (
    '항목기호',
    [
      'lead_spaces',
      'after_spaces',
      'marker_bold',
      'label_bold',
      'hanging',
      'paren_delta',
      'hanging_rule',
      'return_prev',
    ],
  ),
  (
    '칸·표',
    [
      'width',
      'height',
      'margin_left',
      'margin_right',
      'margin_top',
      'margin_bottom',
      'valign',
      'fill',
      'border_left',
      'border_right',
      'border_top',
      'border_bottom',
      'out_left',
      'out_right',
      'out_top',
      'out_bottom',
      'in_left',
      'in_right',
      'in_top',
      'in_bottom',
    ],
  ),
  (
    '쪽',
    [
      'page_width',
      'page_height',
      'page_left',
      'page_right',
      'page_top',
      'page_bottom',
      'page_header',
      'page_footer',
      'page_gutter',
      'page_landscape',
    ],
  ),
];

class _ProfileEditorState extends State<ProfileEditor> {
  Map data = {};
  String error = '';
  bool busy = false;
  int generation = 0;
  int selected = 0;
  final Map<String, Map> edits = {};
  late final CloseLease _closeLease;
  Future<bool> _prepareHostClose() async {
    if (busy || !canCloseEditor(context)) return false;
    if (edits.isNotEmpty && !await confirmHostDiscard(context)) return false;
    if (!mounted) return false;
    Navigator.of(context).pop();
    return true;
  }

  @override
  void initState() {
    super.initState();
    _closeLease = CloseGuards.register(_prepareHostClose);
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
          selected = math.min(selected, math.max(0, _nodes.length - 1));
        });
      }
    } catch (e) {
      if (mounted) setState(() => error = '$e');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  void dispose() {
    _closeLease.release();
    super.dispose();
  }

  List<Map> get _nodes => [
    for (final node in data['nodes'] as List? ?? const []) node as Map,
  ];

  void edit(List path, Map field, String value) {
    setState(() {
      edits['$path:${field['key']}'] = {
        'path': path,
        'key': field['key'],
        'value': value,
      };
    });
  }

  String _current(Map node, Map field) =>
      '${edits['${node['path']}:${field['key']}']?['value'] ?? field['value']}';

  Widget _field(Map node, Map field) {
    final path = node['path'] as List;
    final value = _current(node, field);
    final editable = !busy && field['editable'] == true;
    final choices = [
      for (final c in field['choices'] as List? ?? const []) '$c',
    ];
    final label = Text(
      '${field['label']}',
      style: const TextStyle(
        fontSize: 15,
        fontWeight: FontWeight.w600,
        color: Kiosk.ink,
      ),
    );
    Widget control;
    if (choices.length == 2 &&
        choices.contains('예') &&
        choices.contains('아니오')) {
      control = Switch(
        key: ValueKey('$generation:$path:${field['key']}'),
        activeThumbColor: Colors.white,
        activeTrackColor: Kiosk.blue,
        value: value == '예',
        onChanged: editable
            ? (on) => edit(path, field, on ? '예' : '아니오')
            : null,
      );
    } else if (choices.isNotEmpty) {
      control = Wrap(
        spacing: 6,
        runSpacing: 6,
        children: [
          for (final choice in choices)
            ChoiceChip(
              label: Text(choice),
              selected: value == choice,
              selectedColor: Kiosk.blueSoft,
              labelStyle: TextStyle(
                color: value == choice ? Kiosk.blue : Kiosk.sub,
                fontWeight: value == choice ? FontWeight.w700 : FontWeight.w500,
              ),
              onSelected: editable ? (_) => edit(path, field, choice) : null,
            ),
        ],
      );
    } else {
      control = SizedBox(
        width: 180,
        child: TextFormField(
          key: ValueKey('$generation:$path:${field['key']}'),
          initialValue: value,
          enabled: editable,
          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          decoration: InputDecoration(
            isDense: true,
            filled: true,
            fillColor: editable
                ? const Color(0xfff2f4f6)
                : const Color(0xfff9fafb),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide.none,
            ),
          ),
          onChanged: (text) => edit(path, field, text),
        ),
      );
    }
    final changed = edits.containsKey('$path:${field['key']}');
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: changed ? Kiosk.blueSoft : const Color(0xfffafbfc),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                label,
                if (field['editable'] != true)
                  const Text('문서에서 읽은 값(바꿀 수 없음)', style: Kiosk.caption),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Flexible(
            child: Align(alignment: Alignment.centerRight, child: control),
          ),
        ],
      ),
    );
  }

  Widget _detail(Map node) {
    final fields = [for (final f in node['fields'] as List) f as Map];
    final values = {for (final f in fields) '${f['key']}': _current(node, f)};
    final grouped = <(String, List<Map>)>[];
    final placed = <String>{};
    for (final (title, keys) in _sections) {
      final items = [
        for (final f in fields)
          if (keys.contains(f['key'])) f,
      ];
      placed.addAll(items.map((f) => '${f['key']}'));
      if (items.isNotEmpty) grouped.add((title, items));
    }
    final others = [
      for (final f in fields)
        if (!placed.contains('${f['key']}')) f,
    ];
    if (others.isNotEmpty) grouped.add(('기타', others));
    return ListView(
      padding: const EdgeInsets.only(bottom: 16),
      children: [
        Container(
          padding: const EdgeInsets.all(20),
          decoration: Kiosk.cardBox(),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('${node['label']}', style: Kiosk.cardTitle),
              const SizedBox(height: 4),
              const Text('문서에서 이렇게 보여요. 아래 값을 바꾸면 바로 반영돼요.', style: Kiosk.body),
              const SizedBox(height: 14),
              elementPreview(node['path'] as List, '${node['label']}', values),
            ],
          ),
        ),
        for (final (title, items) in grouped)
          Container(
            margin: const EdgeInsets.only(top: 12),
            padding: const EdgeInsets.all(18),
            decoration: Kiosk.cardBox(),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: Kiosk.ink,
                  ),
                ),
                const SizedBox(height: 10),
                for (final field in items) _field(node, field),
              ],
            ),
          ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final nodes = _nodes;
    final size = MediaQuery.sizeOf(context);
    final compact = size.width < 820;
    final coverage = data['coverage'];
    final nodeList = ListView(
      scrollDirection: compact ? Axis.horizontal : Axis.vertical,
      children: [
        for (var i = 0; i < nodes.length; i++)
          Padding(
            padding: const EdgeInsets.only(bottom: 8, right: 8),
            child: Material(
              color: i == selected ? Kiosk.blueSoft : Colors.white,
              borderRadius: BorderRadius.circular(14),
              child: InkWell(
                key: ValueKey('element-$i'),
                borderRadius: BorderRadius.circular(14),
                onTap: () => setState(() => selected = i),
                child: Padding(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 14,
                    vertical: 12,
                  ),
                  child: Text(
                    '${nodes[i]['label']}',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: i == selected
                          ? FontWeight.w700
                          : FontWeight.w500,
                      color: i == selected ? Kiosk.blue : Kiosk.ink,
                    ),
                  ),
                ),
              ),
            ),
          ),
      ],
    );
    return Dialog(
      backgroundColor: Kiosk.canvas,
      insetPadding: EdgeInsets.all(compact ? 8 : 24),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
      child: SizedBox(
        width: math.min(1140, size.width),
        height: math.min(800, size.height),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(28, 24, 28, 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('${data['name'] ?? '서식 세부 편집'}', style: Kiosk.title),
                  const SizedBox(height: 4),
                  Text(
                    coverage is Map
                        ? '예시 문서에서 찾은 서식 요소 ${coverage['total']}개 중 ${coverage['applied']}개를 적용해요.'
                        : '분석 자료 없음',
                    style: Kiosk.body,
                  ),
                  if (busy)
                    const Padding(
                      padding: EdgeInsets.only(top: 8),
                      child: LinearProgressIndicator(),
                    ),
                  if (error.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Text(
                        error,
                        style: const TextStyle(color: Kiosk.red),
                      ),
                    ),
                ],
              ),
            ),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: nodes.isEmpty
                    ? const Center(
                        child: Text(
                          '편집할 분석 자료가 없습니다. 예시 HWPX에서 서식을 분석한 뒤 계층·칸별 속성을 수정하세요.',
                          style: Kiosk.body,
                        ),
                      )
                    : compact
                    ? Column(
                        children: [
                          SizedBox(height: 56, child: nodeList),
                          Expanded(child: _detail(nodes[selected])),
                        ],
                      )
                    : Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          SizedBox(width: 270, child: nodeList),
                          const SizedBox(width: 12),
                          Expanded(child: _detail(nodes[selected])),
                        ],
                      ),
              ),
            ),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.fromLTRB(24, 14, 24, 18),
              decoration: const BoxDecoration(
                color: Colors.white,
                border: Border(top: BorderSide(color: Kiosk.line)),
                borderRadius: BorderRadius.vertical(
                  bottom: Radius.circular(24),
                ),
              ),
              child: Wrap(
                alignment: WrapAlignment.end,
                crossAxisAlignment: WrapCrossAlignment.center,
                spacing: 10,
                runSpacing: 10,
                children: [
                  Text(
                    edits.isEmpty ? '바꾼 값이 없어요' : '바꾼 값 ${edits.length}개',
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                      color: edits.isEmpty ? Kiosk.faint : Kiosk.blue,
                    ),
                  ),
                  KioskSecondaryButton(
                    label: '선택 요소 분석값 복원',
                    onPressed: busy ? null : () => request('restore'),
                  ),
                  KioskSecondaryButton(
                    label: '닫기',
                    onPressed: busy ? null : () => Navigator.pop(context),
                  ),
                  KioskPrimaryButton(
                    label: '저장·적용',
                    onPressed: busy ? null : () => request('save'),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
