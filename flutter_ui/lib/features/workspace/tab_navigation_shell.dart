import 'package:flutter/material.dart';

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
    this.initialIndex = 0,
    this.onTabChanged,
  }) : assert(initialIndex >= 0 && initialIndex < 6);

  final Widget documentEditor;
  final Widget tableTemplates;
  final Widget tableSketch;
  final Widget diagram;
  final Widget mindMap;
  final Widget fileConversion;
  final int initialIndex;
  final ValueChanged<int>? onTabChanged;

  @override
  State<TabNavigationShell> createState() => _TabNavigationShellState();
}

class _TabNavigationShellState extends State<TabNavigationShell> {
  late int _index = widget.initialIndex;

  static const _labels = ['문서편집', '표템플릿', '표그림판', '다이어그램', '마인드맵', '파일변환'];
  static const _icons = [
    Icons.description_outlined,
    Icons.table_chart_outlined,
    Icons.draw_outlined,
    Icons.account_tree_outlined,
    Icons.hub_outlined,
    Icons.transform,
  ];

  @override
  Widget build(BuildContext context) {
    final pages = [
      widget.documentEditor,
      widget.tableTemplates,
      widget.tableSketch,
      widget.diagram,
      widget.mindMap,
      widget.fileConversion,
    ];
    return Scaffold(
      body: IndexedStack(
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
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
        onDestinationSelected: (index) {
          if (index == _index) return;
          setState(() => _index = index);
          widget.onTabChanged?.call(index);
        },
        destinations: [
          for (var i = 0; i < _labels.length; i++)
            NavigationDestination(icon: Icon(_icons[i]), label: _labels[i]),
        ],
      ),
    );
  }
}
