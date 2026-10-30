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
    return Scaffold(
      body: WorkspaceTabScope(
        goHome: _goHome,
        selectTab: _select,
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
      // 하단 탭은 앱의 다른 부분과 어울리게 낮고 작게(기본 80 → 52, 2026-10-30 사용자 지시).
      bottomNavigationBar: NavigationBarTheme(
        data: NavigationBarThemeData(
          height: 52,
          indicatorShape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          labelTextStyle: WidgetStateProperty.resolveWith(
            (states) => TextStyle(
              fontSize: 11,
              fontWeight: states.contains(WidgetState.selected)
                  ? FontWeight.w700
                  : FontWeight.w500,
            ),
          ),
          iconTheme: const WidgetStatePropertyAll(IconThemeData(size: 19)),
        ),
        child: NavigationBar(
          selectedIndex: _index,
          labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
          onDestinationSelected: _select,
          destinations: [
            for (var i = 0; i < _labels.length; i++)
              NavigationDestination(icon: Icon(_icons[i]), label: _labels[i]),
          ],
        ),
      ),
    );
  }
}
