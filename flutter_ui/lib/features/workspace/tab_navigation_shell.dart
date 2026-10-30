import 'package:flutter/material.dart';

/// 탭 안 화면이 '닫기·뒤로'를 요청할 때 쓰는 통로.
/// 탭 화면은 앱의 첫 경로 위에 바로 있어 Navigator.pop을 하면 첫 화면이 빠져 앱이 멈춘다(2.0.0 사용자 보고).
class WorkspaceTabScope extends InheritedWidget {
  const WorkspaceTabScope({
    super.key,
    required this.goHome,
    required this.selectTab,
    required super.child,
  });

  final VoidCallback goHome;

  /// 탭 번호(0 문서편집·1 표템플릿·2 표그림판·3 다이어그램·4 마인드맵·5 그림판·6 파일변환)로 이동한다.
  final ValueChanged<int> selectTab;

  static WorkspaceTabScope? maybeOf(BuildContext context) =>
      context.dependOnInheritedWidgetOfExactType<WorkspaceTabScope>();

  @override
  bool updateShouldNotify(WorkspaceTabScope oldWidget) =>
      goHome != oldWidget.goHome || selectTab != oldWidget.selectTab;
}

/// 편집기 화면을 닫는다: 새 경로로 열렸으면 이전 화면으로, 탭 안이면 첫 탭(문서편집)으로.
void closeWorkspaceScreen(BuildContext context) {
  final navigator = Navigator.of(context);
  if (navigator.canPop()) {
    navigator.pop();
    return;
  }
  WorkspaceTabScope.maybeOf(context)?.goHome();
}

/// Root workspace contract. Owners inject the six adapters in this fixed order.
/// Keep the shell mounted (and keys stable) for the lifetime of the workspace.
class TabNavigationShell extends StatefulWidget {
  const TabNavigationShell({
    super.key,
    required this.documentEditor,
    required this.tableTemplates,
    required this.tableSketch,
    required this.diagram,
    required this.mindMap,
    required this.fileConversion,
    required this.paint,
    this.initialIndex = 0,
    this.onTabChanged,
    this.trailing,
  }) : assert(initialIndex >= 0 && initialIndex < 7);

  final Widget documentEditor;
  final Widget tableTemplates;
  final Widget tableSketch;
  final Widget diagram;
  final Widget mindMap;
  final Widget fileConversion;

  /// 탭 5: 그림판(사진 배경 위에 펜·도형·글상자를 독립 개체로).
  final Widget paint;
  final int initialIndex;
  final ValueChanged<int>? onTabChanged;

  /// 상단 탭 줄 오른쪽 끝의 앱 전체 메뉴(사용 방법·작업 로그·설정 등).
  final Widget? trailing;

  @override
  State<TabNavigationShell> createState() => _TabNavigationShellState();
}

class _TabNavigationShellState extends State<TabNavigationShell> {
  late int _index = widget.initialIndex;

  static const _labels = [
    '문서편집',
    '표템플릿',
    '표그림판',
    '다이어그램',
    '마인드맵',
    '그림판',
    // 파일변환은 항상 맨 끝(2026-10-30 사용자 지시).
    '파일변환',
  ];
  static const _icons = [
    Icons.description_outlined,
    Icons.table_chart_outlined,
    Icons.draw_outlined,
    Icons.account_tree_outlined,
    Icons.hub_outlined,
    Icons.brush_outlined,
    Icons.transform,
  ];

  void _select(int index) {
    if (index == _index) return;
    setState(() => _index = index);
    widget.onTabChanged?.call(index);
  }

  void _goHome() => _select(0);

  @override
  Widget build(BuildContext context) {
    final pages = [
      widget.documentEditor,
      widget.tableTemplates,
      widget.tableSketch,
      widget.diagram,
      widget.mindMap,
      widget.paint,
      widget.fileConversion,
    ];
    // 탭 메뉴와 앱 메뉴(설정 등)를 상단 한 줄로 합쳤다(2026-10-30 사용자 지시).
    return Scaffold(
      body: WorkspaceTabScope(
        goHome: _goHome,
        selectTab: _select,
        child: Column(
          children: [
            WorkspaceTabBar(
              labels: _labels,
              icons: _icons,
              selectedIndex: _index,
              onSelected: _select,
              trailing: widget.trailing,
            ),
            Expanded(
              child: IndexedStack(
                index: _index,
                children: [
                  for (var i = 0; i < pages.length; i++)
                    TickerMode(
                      key: ValueKey('workspace-tab-$i'),
                      enabled: i == _index,
                      child: pages[i],
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

/// 상단 작업 탭 줄(높이 52): 앱 표시 · 알약 탭(아이콘 16 + 이름 13, 고른 탭은 채운 알약) · 앱 메뉴.
/// Filee 목록 메뉴·이음오피스 탭 크기를 참고했다. 창이 좁으면 탭 부분을 가로로 밀어 본다.
class WorkspaceTabBar extends StatelessWidget {
  const WorkspaceTabBar({
    super.key,
    required this.labels,
    required this.icons,
    required this.selectedIndex,
    required this.onSelected,
    this.trailing,
  });

  final List<String> labels;
  final List<IconData> icons;
  final int selectedIndex;
  final ValueChanged<int> onSelected;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final wide = MediaQuery.sizeOf(context).width >= 1100;
    return Material(
      color: Colors.white,
      child: Container(
        height: 52,
        padding: const EdgeInsets.symmetric(horizontal: 10),
        decoration: const BoxDecoration(
          border: Border(bottom: BorderSide(color: Color(0xFFE2E8F0))),
        ),
        child: Row(
          children: [
            Container(
              width: 30,
              height: 30,
              decoration: BoxDecoration(
                color: const Color(0xFF0F172A),
                borderRadius: BorderRadius.circular(9),
              ),
              child: const Icon(
                Icons.description_rounded,
                color: Colors.white,
                size: 18,
              ),
            ),
            if (wide) ...[
              const SizedBox(width: 8),
              const Text(
                '한글편집 후처리',
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -.5,
                ),
              ),
            ],
            const SizedBox(width: 12),
            Expanded(
              // 자리가 모자라면 탭을 촘촘하게, 더 모자라면 아이콘만(이름은 툴팁) — 끝 탭이 가려지지 않게.
              child: LayoutBuilder(
                builder: (context, constraints) {
                  final per = constraints.maxWidth / labels.length;
                  final density = per >= 104
                      ? _PillDensity.normal
                      : per >= 82
                      ? _PillDensity.compact
                      : _PillDensity.iconOnly;
                  return SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: [
                        for (var i = 0; i < labels.length; i++)
                          Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 1),
                            child: _TabPill(
                              key: Key('workspaceTab-$i'),
                              label: labels[i],
                              icon: icons[i],
                              selected: i == selectedIndex,
                              color: scheme.primary,
                              density: density,
                              onTap: () => onSelected(i),
                            ),
                          ),
                      ],
                    ),
                  );
                },
              ),
            ),
            ?trailing,
          ],
        ),
      ),
    );
  }
}

enum _PillDensity { normal, compact, iconOnly }

class _TabPill extends StatelessWidget {
  const _TabPill({
    super.key,
    required this.label,
    required this.icon,
    required this.selected,
    required this.color,
    required this.onTap,
    this.density = _PillDensity.normal,
  });

  final _PillDensity density;

  final String label;
  final IconData icon;
  final bool selected;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final fg = selected ? Colors.white : const Color(0xFF475569);
    final compact = density != _PillDensity.normal;
    final pill = Semantics(
      selected: selected,
      button: true,
      child: Material(
        color: selected ? color : Colors.transparent,
        borderRadius: BorderRadius.circular(8),
        child: InkWell(
          borderRadius: BorderRadius.circular(8),
          onTap: onTap,
          child: Padding(
            padding: EdgeInsets.symmetric(
              horizontal: compact ? 8 : 12,
              vertical: 7,
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(icon, size: 16, color: fg),
                if (density != _PillDensity.iconOnly) ...[
                  SizedBox(width: compact ? 4 : 6),
                  Text(
                    label,
                    style: TextStyle(
                      fontSize: compact ? 12 : 13,
                      color: fg,
                      fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
    return density == _PillDensity.iconOnly
        ? Tooltip(message: label, child: pill)
        : pill;
  }
}
