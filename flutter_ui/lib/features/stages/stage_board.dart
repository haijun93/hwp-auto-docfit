import 'package:flutter/material.dart';

import '../preview/option_images.dart';
import '../settings/kiosk_theme.dart';

/// 세부 작업 분류(설정 '전체 설정 열기'의 분류 목록과 같은 모양).
class StageGroup {
  const StageGroup(this.id, this.title, this.subtitle, this.icon, this.keys);
  final String id;
  final String title;
  final String subtitle;
  final IconData icon;
  final Set<String> keys;
}

const stageGroups = [
  StageGroup('all', '전체 단계', '실행 순서 그대로', Icons.format_list_numbered, {}),
  StageGroup('prepare', '문서 서식', '준말·표준 서식·영역', Icons.description_outlined, {
    'abbreviation',
    'standard_format',
    'text_table_convert',
    'pre_format',
    'attachment_font',
    'asterisk_superscript',
    'style_unify',
    'unify_full_format',
  }),
  StageGroup('sentence', '문장·기호', '공백·괄호·내어쓰기', Icons.short_text, {
    'normalize_space',
    'punctuation_space',
    'parenthesis',
    'hanging_indent',
    'supplement_indent',
    'star_align',
  }),
  StageGroup('table', '표', '표 모양·너비·통일', Icons.table_chart_outlined, {
    'table_style',
    'table_width',
    'precise_table',
    'table_format',
    'table_unify',
    'single_cell_spacing',
  }),
  StageGroup('spacing', '자간·줄 끝', '갈라진 단어·짧은 줄', Icons.wrap_text, {
    'reset_spacing',
    'body_spacing',
    'short_line',
    'control_spacing',
    'control_short_line',
    'word_check',
    'control_word_check',
    'unify_spacing',
  }),
  StageGroup('page', '쪽 배치', '쪽 맞춤·묶음', Icons.auto_stories_outlined, {
    'page_fit',
    'page_group',
    'page_layout_keep',
  }),
];

String stageGroupOf(String key) => stageGroups
    .skip(1)
    .firstWhere((g) => g.keys.contains(key), orElse: () => stageGroups[1])
    .id;

/// 작업 방식의 세부 작업 목록: 왼쪽 분류, 가운데 단계 카드(켜고 끄기), 오른쪽 한/글 조판 전·후 미리보기.
class StageBoard extends StatefulWidget {
  const StageBoard({
    super.key,
    required this.stages,
    required this.locked,
    required this.onToggle,
  });

  final List stages;
  final bool locked;
  final void Function(String key, bool on) onToggle;

  @override
  State<StageBoard> createState() => _StageBoardState();
}

class _StageBoardState extends State<StageBoard> {
  String group = 'all';
  String? focus;

  List<(int, Map)> get _numbered => [
    for (var i = 0; i < widget.stages.length; i++) (i, widget.stages[i] as Map),
  ];

  List<(int, Map)> _visible() {
    if (group == 'all') return _numbered;
    return [
      for (final item in _numbered)
        if (stageGroupOf('${item.$2['key']}') == group) item,
    ];
  }

  Map? get _focused {
    for (final (_, stage) in _numbered) {
      if (stage['key'] == focus) return stage;
    }
    final visible = _visible();
    return visible.isEmpty ? null : visible.first.$2;
  }

  void _toggle(Map stage, bool on) {
    setState(() => focus = '${stage['key']}');
    widget.onToggle('${stage['key']}', on);
  }

  @override
  Widget build(BuildContext context) {
    final groups = [
      for (final g in stageGroups)
        if (g.id == 'all' ||
            _numbered.any((s) => stageGroupOf('${s.$2['key']}') == g.id))
          g,
    ];
    if (!groups.any((g) => g.id == group)) group = 'all';
    return LayoutBuilder(
      builder: (context, constraints) {
        final width = constraints.maxWidth;
        final cards = Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [for (final (i, s) in _visible()) _card(i, s)],
        );
        if (width >= 1040) {
          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(
                width: 210,
                child: Column(
                  children: [for (final g in groups) _groupTile(g, false)],
                ),
              ),
              const SizedBox(width: 12),
              Expanded(child: cards),
              const SizedBox(width: 12),
              SizedBox(width: 360, child: _previewPane()),
            ],
          );
        }
        final chips = SizedBox(
          height: 58,
          child: ListView(
            scrollDirection: Axis.horizontal,
            children: [for (final g in groups) _groupTile(g, true)],
          ),
        );
        if (width >= 720) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              chips,
              const SizedBox(height: 8),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(child: cards),
                  const SizedBox(width: 12),
                  SizedBox(width: 320, child: _previewPane()),
                ],
              ),
            ],
          );
        }
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            chips,
            const SizedBox(height: 8),
            _previewPane(),
            const SizedBox(height: 12),
            cards,
          ],
        );
      },
    );
  }

  Widget _groupTile(StageGroup item, bool compact) {
    final selected = item.id == group;
    final members = item.id == 'all'
        ? _numbered
        : [
            for (final s in _numbered)
              if (stageGroupOf('${s.$2['key']}') == item.id) s,
          ];
    final on = members.where((s) => s.$2['on'] == true).length;
    return Padding(
      padding: const EdgeInsets.only(bottom: 8, right: 8),
      child: Material(
        color: selected ? Kiosk.blueSoft : Colors.white,
        borderRadius: BorderRadius.circular(16),
        child: InkWell(
          key: ValueKey('stage-group-${item.id}'),
          borderRadius: BorderRadius.circular(16),
          onTap: () => setState(() {
            group = item.id;
            focus = null;
          }),
          child: Padding(
            padding: EdgeInsets.symmetric(
              horizontal: 12,
              vertical: compact ? 8 : 12,
            ),
            child: Row(
              mainAxisSize: compact ? MainAxisSize.min : MainAxisSize.max,
              children: [
                Container(
                  width: 34,
                  height: 34,
                  decoration: BoxDecoration(
                    color: selected ? Kiosk.blue : Kiosk.canvas,
                    borderRadius: BorderRadius.circular(11),
                  ),
                  child: Icon(
                    item.icon,
                    size: 18,
                    color: selected ? Colors.white : Kiosk.sub,
                  ),
                ),
                const SizedBox(width: 10),
                Flexible(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        compact
                            ? '${item.title} $on/${members.length}'
                            : item.title,
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w700,
                          color: selected ? Kiosk.blue : Kiosk.ink,
                        ),
                      ),
                      if (!compact)
                        Text(
                          '${item.subtitle} · $on/${members.length}',
                          style: Kiosk.caption,
                        ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _badge(String text, {bool strong = true}) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
    decoration: BoxDecoration(
      color: strong ? Kiosk.blueSoft : Kiosk.canvas,
      borderRadius: BorderRadius.circular(8),
    ),
    child: Text(
      text,
      style: TextStyle(
        fontSize: 12,
        color: strong ? Kiosk.blue : Kiosk.sub,
        fontWeight: FontWeight.w700,
      ),
    ),
  );

  Widget _card(int index, Map stage) {
    final key = '${stage['key']}';
    final on = stage['on'] == true;
    final changed = stage['on'] != stage['default'];
    final focused = _focused?['key'] == key;
    final example = '${stage['example'] ?? ''}'.replaceFirst(
      RegExp(r'^예:\s*'),
      '',
    );
    final toggle = Transform.scale(
      scale: 1.1,
      child: Switch(
        key: ValueKey('stage-switch-$key'),
        activeThumbColor: Colors.white,
        activeTrackColor: Kiosk.blue,
        value: on,
        onChanged: widget.locked ? null : (v) => _toggle(stage, v),
      ),
    );
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: Kiosk.cardBox(selected: focused),
      child: Material(
        type: MaterialType.transparency,
        child: InkWell(
          borderRadius: BorderRadius.circular(Kiosk.radius),
          onTap: widget.locked ? null : () => _toggle(stage, !on),
          onHover: (hover) {
            if (hover && focus != key) setState(() => focus = key);
          },
          child: Padding(
            padding: const EdgeInsets.fromLTRB(18, 14, 10, 14),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Wrap(
                        spacing: 8,
                        runSpacing: 4,
                        crossAxisAlignment: WrapCrossAlignment.center,
                        children: [
                          Text(
                            '${index + 1}. ${stage['label']}',
                            style: Kiosk.cardTitle.copyWith(
                              fontSize: 16,
                              color: on ? Kiosk.ink : Kiosk.faint,
                            ),
                          ),
                          if (changed) _badge('바뀜'),
                          if (!on) _badge('건너뜀', strong: false),
                        ],
                      ),
                      if (example.isNotEmpty) ...[
                        const SizedBox(height: 4),
                        Text(
                          example,
                          style: Kiosk.body.copyWith(fontSize: 13.5),
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                toggle,
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _labelled(String text, Widget child, {bool strong = false}) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      _badge(text, strong: strong),
      const SizedBox(height: 6),
      child,
    ],
  );

  Widget _previewPane() {
    final stage = _focused;
    final key = '${stage?['key'] ?? ''}';
    final image = stage == null ? null : optionImageFor(key);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: Kiosk.cardBox(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text('적용 전·후 예시', style: Kiosk.cardTitle),
          const SizedBox(height: 4),
          Text(
            stage == null
                ? '단계를 고르면 문서가 어떻게 바뀌는지 보여 드려요.'
                : '${stage['label']} — 왼쪽이 단계 전, 오른쪽이 단계 뒤예요. 그림을 누르면 크게 볼 수 있어요.',
            style: Kiosk.caption,
          ),
          const SizedBox(height: 12),
          if (image != null)
            _labelled(
              stage!['on'] == true ? '이번 실행에 적용' : '지금은 건너뜀',
              OptionImagePreview(key),
              strong: stage['on'] == true,
            )
          else if (stage != null)
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Kiosk.canvas,
                borderRadius: BorderRadius.circular(14),
              ),
              child: Text(
                '${stage['example'] ?? '이 단계는 문서 전체를 살펴 정리해요.'}',
                style: Kiosk.body.copyWith(fontSize: 13.5),
              ),
            ),
        ],
      ),
    );
  }
}
