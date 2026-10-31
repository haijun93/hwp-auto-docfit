import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// 탭 번호. 파일이름 뒤에 타임머신을 두고 파일변환을 맨 끝에 둔다.
const kTabFileRename = 6;
const kTabTimemachine = 7;
const kTabFileConversion = 8;
const kTabCount = 9;

/// 왼쪽 메뉴 폭. 저장값이 없으면 창 폭이 기준 이상일 때 펼친다.
const kSidebarCollapsedWidth = 56.0;
const kSidebarExpandedWidth = 200.0;
const kSidebarAutoExpandWidth = 900.0;

/// 파일명 일괄변경은 기능이 완벽해질 때까지 메뉴에 보이지 않는다(2026-11-01 사용자 지시).
/// 완성되면 true로 바꾼다. 탭 번호는 그대로 둔다.
const kFileRenameMenuEnabled = false;
const kDefaultHiddenTabs = kFileRenameMenuEnabled ? <int>{} : <int>{kTabFileRename};

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

  /// 탭 번호(0 문서편집·1 표템플릿·2 표그림판·3 다이어그램·4 마인드맵·5 그림판·6 파일이름·7 타임머신·8 파일변환)로 이동한다.
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

/// Root workspace contract. Owners inject adapters in this fixed order.
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
    required this.fileRename,
    required this.timemachine,
    this.initialIndex = 0,
    this.onTabChanged,
    this.trailing,
    this.onSidebarExpandedChanged,
    this.savedSidebarExpanded,
    this.hiddenTabs = kDefaultHiddenTabs,
  }) : assert(initialIndex >= 0 && initialIndex < kTabCount);

  final Widget documentEditor;
  final Widget tableTemplates;
  final Widget tableSketch;
  final Widget diagram;
  final Widget mindMap;
  final Widget fileConversion;

  /// 탭 5: 그림판(사진 배경 위에 펜·도형·글상자를 독립 개체로).
  final Widget paint;

  /// 탭 6: 파일이름(여러 파일 이름을 규칙으로 한꺼번에 바꾸기).
  final Widget fileRename;
  final Widget timemachine;
  final int initialIndex;

  /// 메뉴에 보이지 않고 화면도 만들지 않는 탭.
  final Set<int> hiddenTabs;
  final ValueChanged<int>? onTabChanged;

  /// 왼쪽 메뉴 아래쪽의 앱 전체 메뉴(사용 방법·작업 로그·설정 등).
  final Widget? trailing;
  final ValueChanged<bool>? onSidebarExpandedChanged;

  /// 저장된 펼침 상태. null이면 창 폭으로 정한다.
  final ValueListenable<bool?>? savedSidebarExpanded;

  @override
  State<TabNavigationShell> createState() => _TabNavigationShellState();
}

class _TabNavigationShellState extends State<TabNavigationShell> {
  late int _index = widget.hiddenTabs.contains(widget.initialIndex) ? 0 : widget.initialIndex;
  final ScrollController _tabScrollController = ScrollController();
  bool? _expanded;
  bool _sidebarTouched = false;
  bool _built = false;

  @override
  void dispose() {
    widget.savedSidebarExpanded?.removeListener(_applySaved);
    _tabScrollController.dispose();
    super.dispose();
  }

  static const _labels = [
    '문서편집',
    '표템플릿',
    '표그림판',
    '다이어그램',
    '마인드맵',
    '그림판',
    '파일명 일괄변경',
    '타임머신',
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
    Icons.drive_file_rename_outline,
    Icons.history_toggle_off,
    Icons.transform,
  ];

  void _select(int index) {
    if (widget.hiddenTabs.contains(index) || index == _index) return;
    setState(() => _index = index);
    widget.onTabChanged?.call(index);
  }

  void _goHome() => _select(0);

  @override
  void initState() {
    super.initState();
    _applySaved();
    widget.savedSidebarExpanded?.addListener(_applySaved);
  }

  /// 저장값은 첫 상태 응답 때 늦게 온다. 사용자가 이미 눌렀으면 덮지 않는다.
  void _applySaved() {
    if (_sidebarTouched) return;
    final saved = widget.savedSidebarExpanded?.value;
    if (saved == null || saved == _expanded) return;
    if (mounted && _built) {
      setState(() => _expanded = saved);
    } else {
      _expanded = saved;
    }
  }

  void _toggleSidebar() {
    final next = !(_expanded ?? MediaQuery.sizeOf(context).width >= kSidebarAutoExpandWidth);
    _sidebarTouched = true;
    setState(() => _expanded = next);
    widget.onSidebarExpandedChanged?.call(next);
  }

  @override
  Widget build(BuildContext context) {
    final pages = [
      widget.documentEditor,
      widget.tableTemplates,
      widget.tableSketch,
      widget.diagram,
      widget.mindMap,
      widget.paint,
      widget.fileRename,
      widget.timemachine,
      widget.fileConversion,
    ];
    _built = true;
    final expanded = _expanded ?? MediaQuery.sizeOf(context).width >= kSidebarAutoExpandWidth;
    return Scaffold(
      body: WorkspaceTabScope(
        goHome: _goHome,
        selectTab: _select,
        child: Shortcuts(
          shortcuts: {
            for (var i = 0; i < kTabCount; i++)
              LogicalKeySet(
                LogicalKeyboardKey.control,
                LogicalKeyboardKey(LogicalKeyboardKey.digit1.keyId + i),
              ): _SelectWorkspaceTabIntent(i),
          },
          child: Actions(
            actions: {
              _SelectWorkspaceTabIntent:
                  CallbackAction<_SelectWorkspaceTabIntent>(
                    onInvoke: (intent) {
                      _select(intent.index);
                      return null;
                    },
                  ),
            },
            // 아무것도 초점을 잡지 않았을 때도 단축키가 듣게 한다.
            child: Focus(
              autofocus: true,
              child: Row(
                children: [
                  WorkspaceTabBar(
                    labels: _labels,
                    icons: _icons,
                    selectedIndex: _index,
                    onSelected: _select,
                    hiddenTabs: widget.hiddenTabs,
                    scrollController: _tabScrollController,
                    trailing: widget.trailing,
                    expanded: expanded,
                    onToggleExpanded: _toggleSidebar,
                  ),
                  Expanded(
                    child: IndexedStack(
                      index: _index,
                      children: [
                        for (var i = 0; i < pages.length; i++)
                          TickerMode(
                            key: ValueKey('workspace-tab-$i'),
                            enabled: i == _index,
                            child: widget.hiddenTabs.contains(i) ? const SizedBox.shrink() : pages[i],
                          ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _SelectWorkspaceTabIntent extends Intent {
  const _SelectWorkspaceTabIntent(this.index);
  final int index;
}

/// 왼쪽 세로 메뉴. 항목 키는 기존 workspaceTab-N 계약을 유지한다.
class WorkspaceTabBar extends StatelessWidget {
  const WorkspaceTabBar({
    super.key,
    required this.labels,
    required this.icons,
    required this.selectedIndex,
    required this.onSelected,
    required this.scrollController,
    this.hiddenTabs = const {},
    this.trailing,
    this.expanded = true,
    this.onToggleExpanded,
  });

  final Set<int> hiddenTabs;
  final List<String> labels;
  final List<IconData> icons;
  final int selectedIndex;
  final ValueChanged<int> onSelected;
  final ScrollController scrollController;
  final Widget? trailing;
  final bool expanded;
  final VoidCallback? onToggleExpanded;

  @override
  Widget build(BuildContext context) {
    final color = Theme.of(context).colorScheme.primary;
    return Material(
      color: Colors.white,
      child: Container(
        width: expanded ? kSidebarExpandedWidth : kSidebarCollapsedWidth,
        decoration: const BoxDecoration(
          border: Border(right: BorderSide(color: Color(0xFFE2E8F0))),
        ),
        child: LayoutBuilder(
          builder: (context, constraints) => Column(
          children: [
            SizedBox(
              height: 48,
              child: Align(
                alignment: Alignment.centerLeft,
                child: IconButton(
                  key: const ValueKey('workspaceSidebarToggle'),
                  tooltip: expanded ? '메뉴 접기' : '메뉴 펼치기',
                  onPressed: onToggleExpanded,
                  icon: const Icon(Icons.menu),
                ),
              ),
            ),
            Expanded(
              child: ListView(
                controller: scrollController,
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                children: [
                  for (var i = 0; i < labels.length; i++)
                    if (!hiddenTabs.contains(i))
                      _TabPill(
                        key: Key('workspaceTab-$i'),
                        label: labels[i],
                        icon: icons[i],
                        selected: i == selectedIndex,
                        color: color,
                        expanded: expanded,
                        onTap: () => onSelected(i),
                      ),
                ],
              ),
            ),
            if (trailing != null) ...[
              const Divider(height: 1),
              // 창이 낮아도 넘치지 않게 앱 메뉴는 남은 높이의 절반까지만 쓰고 그 안에서 스크롤한다.
              ConstrainedBox(
                constraints: BoxConstraints(
                  maxHeight: ((constraints.maxHeight - 49) / 2).clamp(0.0, double.infinity),
                ),
                child: SingleChildScrollView(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  child: Center(child: trailing!),
                ),
              ),
            ],
          ],
          ),
        ),
      ),
    );
  }
}

class _TabPill extends StatelessWidget {
  const _TabPill({
    super.key,
    required this.label,
    required this.icon,
    required this.selected,
    required this.color,
    required this.onTap,
    this.expanded = true,
  });

  final bool expanded;
  final String label;
  final IconData icon;
  final bool selected;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final fg = selected ? color : const Color(0xFF475569);
    final item = Semantics(
      selected: selected,
      button: true,
      label: label,
      child: Material(
        color: selected ? color.withValues(alpha: .10) : Colors.transparent,
        borderRadius: BorderRadius.circular(8),
        child: InkWell(
          borderRadius: BorderRadius.circular(8),
          onTap: onTap,
          child: Stack(
            children: [
              Padding(
                padding: EdgeInsets.symmetric(
                  horizontal: expanded ? 12 : 0,
                  vertical: 10,
                ),
                child: Row(
                  mainAxisAlignment: expanded
                      ? MainAxisAlignment.start
                      : MainAxisAlignment.center,
                  children: [
                    Icon(icon, size: 20, color: fg),
                    if (expanded) ...[
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          label,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 13,
                            color: fg,
                            fontWeight: selected
                                ? FontWeight.w700
                                : FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              if (selected)
                Positioned(
                  left: 0,
                  top: 8,
                  bottom: 8,
                  width: 3,
                  child: ColoredBox(color: color),
                ),
            ],
          ),
        ),
      ),
    );
    // 접혀 있을 때는 이름을 툴팁으로 보여 준다.
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 1),
      child: expanded ? item : Tooltip(message: label, child: item),
    );
  }
}
