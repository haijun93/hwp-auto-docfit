import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/close_guards.dart';

/// 탭 번호. 파일이름 뒤에 타임머신을 두고 파일변환을 맨 끝에 둔다.
const kTabFileRename = 6;
const kTabTimemachine = 7;
const kTabFileConversion = 8;
const kTabCount = 9;

/// 왼쪽 메뉴 폭. 저장값이 없으면 창 폭이 기준 이상일 때 펼친다.
const kSidebarCollapsedWidth = 56.0;
const kSidebarExpandedWidth = 200.0;
const kSidebarAutoExpandWidth = 900.0;

const kFileRenameMenuEnabled = true;
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
    this.tabRequest,
    this.hiddenTabs = kDefaultHiddenTabs,
    this.developerMode = false,
    this.libraryScreen,
    this.notebookScreen,
    this.onSidebarSideSwitch,
    this.onAlwaysOnTopChanged,
    this.onSidebarModeRequest,
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
  final bool developerMode;
  final Widget? libraryScreen;
  /// 개발자 모드 전용 노트북 화면(자료함 버튼 옆).
  final Widget? notebookScreen;
  final VoidCallback? onSidebarSideSwitch;
  /// 항상 위 켜기/끄기를 앱(창)에 요청한다.
  final Future<void> Function(bool enabled)? onAlwaysOnTopChanged;
  /// 사이드메뉴 모드(창을 화면 가장자리에 붙임)를 앱에 요청한다. false를 돌려주면 전환하지 않는다.
  final Future<bool> Function(bool enabled)? onSidebarModeRequest;
  final ValueChanged<int>? onTabChanged;

  /// 왼쪽 메뉴 아래쪽의 앱 전체 메뉴(사용 방법·작업 로그·설정 등).
  final Widget? trailing;
  final ValueChanged<bool>? onSidebarExpandedChanged;

  /// 저장된 펼침 상태. null이면 창 폭으로 정한다.
  final ValueListenable<bool?>? savedSidebarExpanded;

  /// 바깥에서 특정 탭을 열어 달라는 요청(탐색기 보내기 등).
  final ValueListenable<int?>? tabRequest;

  @override
  State<TabNavigationShell> createState() => _TabNavigationShellState();
}

class _TabNavigationShellState extends State<TabNavigationShell> {
  late int _index = widget.hiddenTabs.contains(widget.initialIndex) ? 0 : widget.initialIndex;
  final ScrollController _tabScrollController = ScrollController();
  bool? _expanded;
  bool _sidebarTouched = false;
  bool _sidebarOnly = false;
  bool _built = false;
  int _hoverRequest = 0;
  int _sidebarStage = 0;

  void _previewTab(int index) {
    final request = ++_hoverRequest;
    Future<void>.delayed(const Duration(milliseconds: 150), () {
      if (!mounted || request != _hoverRequest || index == _index ||
          widget.hiddenTabs.contains(index)) {
        return;
      }
      _select(index);
    });
  }

  void _cancelPreview() { _hoverRequest++; }

  @override
  void dispose() {
    widget.savedSidebarExpanded?.removeListener(_applySaved);
    widget.tabRequest?.removeListener(_applyTabRequest);
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
    if (widget.hiddenTabs.contains(index)) return;
    if (index == _index) {
      widget.onTabChanged?.call(index);
      return;
    }
    setState(() => _index = index);
    widget.onTabChanged?.call(index);
  }

  void _goHome() => _select(0);

  @override
  void initState() {
    super.initState();
    _applySaved();
    widget.savedSidebarExpanded?.addListener(_applySaved);
    widget.tabRequest?.addListener(_applyTabRequest);
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

  void _applyTabRequest() {
    final index = widget.tabRequest?.value;
    if (index != null && mounted) _select(index);
  }

  /// 햄버거 단추 순환(사용자 지시 2026-11-07): 일반 모드는 펼치기 ↔ 닫기만 되풀이하고,
  /// 개발자 모드에서만 3번째로 작업 화면까지 닫는다(사이드메뉴 모드).
  /// 개발자 모드 순서:
  /// 펼치기 → 닫기(아이콘만) → 닫은 채로 오른쪽 작업 화면까지 닫기 → 다시 펼치기.
  /// 다음 단계는 지금 화면 상태로 정하므로 처음 상태와 관계없이 순서가 맞다.
  Future<void> _toggleSidebar() async {
    _sidebarTouched = true;
    final open = _expanded ?? MediaQuery.sizeOf(context).width >= kSidebarAutoExpandWidth;
    if (_sidebarOnly) {
      await _setSidebarOnly(false);
      if (!mounted || _sidebarOnly) return;
      setState(() { _expanded = true; _sidebarStage = 0; });
      widget.onSidebarExpandedChanged?.call(true);
    } else if (open) {
      // (2) 닫기
      setState(() { _expanded = false; _sidebarStage = 1; });
      widget.onSidebarExpandedChanged?.call(false);
    } else if (_sidebarStage == 1 && widget.developerMode) {
      // (3) 단추로 닫은 다음 번에는 작업 화면까지 닫는다.
      await _setSidebarOnly(true);
      if (!mounted) return;
      if (!_sidebarOnly) {
        // 사이드메뉴 모드를 쓸 수 없으면(개발자 모드 꺼짐 등) 멈추지 않고 다시 펼친다.
        setState(() { _expanded = true; _sidebarStage = 0; });
        widget.onSidebarExpandedChanged?.call(true);
        return;
      }
      setState(() { _expanded = false; _sidebarStage = 2; });
    } else {
      // (1) 처음부터 닫혀 있던 메뉴는 먼저 펼친다.
      setState(() { _expanded = true; _sidebarStage = 0; });
      widget.onSidebarExpandedChanged?.call(true);
    }
  }

  bool _alwaysOnTop = false;

  Future<void> _toggleAlwaysOnTop() async {
    final enabled = !_alwaysOnTop;
    await widget.onAlwaysOnTopChanged?.call(enabled);
    if (mounted) setState(() => _alwaysOnTop = enabled);
  }

  Future<void> _setSidebarOnly(bool enabled) async {
    final request = widget.onSidebarModeRequest;
    if (request != null && !await request(enabled)) return;
    if (mounted) {
      setState(() {
        _sidebarOnly = enabled;
        _sidebarStage = enabled ? 2 : 0;
      });
    }
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
                    libraryScreen: widget.libraryScreen,
                    notebookScreen: widget.notebookScreen,
                    expanded: expanded,
                    onToggleExpanded: _toggleSidebar,
                    showToggle: true,
                    developerMode: widget.developerMode,
                    onSidebarModeChanged: _setSidebarOnly,
                    onSidebarSideSwitch: widget.onSidebarSideSwitch,
                    sidebarOnly: _sidebarOnly,
                    onPreview: _previewTab,
                    onPreviewCancel: _cancelPreview,
                    onAlwaysOnTop: _toggleAlwaysOnTop,
                  ),
                  if (!_sidebarOnly) Expanded(
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
    this.developerMode = false,
    this.onSidebarModeChanged,
    this.onSidebarSideSwitch,
    this.onAlwaysOnTopChanged,
    this.onSidebarModeRequest,
    this.sidebarOnly = false,
    this.onAlwaysOnTop,
    this.libraryScreen,
    this.notebookScreen,
    this.onPreview,
    this.onPreviewCancel,
    this.showToggle = true,
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
  final bool developerMode;
  final ValueChanged<bool>? onSidebarModeChanged;
  final VoidCallback? onSidebarSideSwitch;
  /// 항상 위 켜기/끄기를 앱(창)에 요청한다.
  final Future<void> Function(bool enabled)? onAlwaysOnTopChanged;
  /// 사이드메뉴 모드(창을 화면 가장자리에 붙임)를 앱에 요청한다. false를 돌려주면 전환하지 않는다.
  final Future<bool> Function(bool enabled)? onSidebarModeRequest;
  final bool sidebarOnly;
  final VoidCallback? onAlwaysOnTop;
  final Widget? libraryScreen;
  /// 개발자 모드 전용 노트북 화면(자료함 버튼 옆).
  final Widget? notebookScreen;
  final ValueChanged<int>? onPreview;
  final VoidCallback? onPreviewCancel;
  final bool showToggle;

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
            if (showToggle) SizedBox(
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
                        onPreview: onPreview == null ? null : () => onPreview!(i),
                        onPreviewCancel: onPreviewCancel,
                        onTap: () => onSelected(i),
                      ),
                  if (developerMode && libraryScreen != null)
                    _TabPill(
                      key: const ValueKey('library-open'),
                      label: '자료함',
                      icon: Icons.dashboard_customize_outlined,
                      selected: false,
                      color: color,
                      expanded: expanded,
                      onTap: () => Navigator.of(context).push(MaterialPageRoute<void>(
                        builder: (_) => HostClosablePage(title: '자료함', child: libraryScreen!),
                      )),
                    ),
                  if (developerMode && notebookScreen != null)
                    _TabPill(
                      key: const ValueKey('notebook-open'),
                      label: '노트북',
                      icon: Icons.menu_book_outlined,
                      selected: false,
                      color: color,
                      expanded: expanded,
                      onTap: () => Navigator.of(context).push(MaterialPageRoute<void>(
                        builder: (_) => HostClosablePage(title: '노트북', child: notebookScreen!),
                      )),
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
            if (developerMode) ...[
              if (sidebarOnly)
                if (expanded)
                  TextButton.icon(
                    key: const ValueKey('sidebar-mode-switch-side'),
                    onPressed: onSidebarSideSwitch,
                    icon: const Icon(Icons.swap_horiz),
                    label: const Text('왼쪽↔오른쪽 고정'),
                  )
                else
                  IconButton(
                    key: const ValueKey('sidebar-mode-switch-side'),
                    tooltip: '왼쪽↔오른쪽 고정',
                    onPressed: onSidebarSideSwitch,
                    icon: const Icon(Icons.swap_horiz),
                  ),
              if (expanded) ...[
                TextButton.icon(
                  key: const ValueKey('always-on-top-toggle'),
                  onPressed: onAlwaysOnTop,
                  icon: const Icon(Icons.push_pin_outlined),
                  label: const Text('항상 위'),
                ),
                TextButton.icon(
                  key: const ValueKey('sidebar-mode-toggle'),
                  onPressed: () => onSidebarModeChanged?.call(!sidebarOnly),
                  icon: const Icon(Icons.view_sidebar_outlined),
                  label: Text('사이드메뉴 모드 ${sidebarOnly ? '켜짐' : '꺼짐'}'),
                ),
              ] else ...[
                IconButton(
                  key: const ValueKey('always-on-top-toggle'),
                  tooltip: '항상 위',
                  onPressed: onAlwaysOnTop,
                  icon: const Icon(Icons.push_pin_outlined),
                ),
                IconButton(
                  key: const ValueKey('sidebar-mode-toggle'),
                  tooltip: '사이드메뉴 모드 ${sidebarOnly ? '켜짐' : '꺼짐'}',
                  onPressed: () => onSidebarModeChanged?.call(!sidebarOnly),
                  icon: const Icon(Icons.view_sidebar_outlined),
                ),
              ],
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
    this.onPreview,
    this.onPreviewCancel,
  });

  final bool expanded;
  final String label;
  final IconData icon;
  final bool selected;
  final Color color;
  final VoidCallback onTap;
  final VoidCallback? onPreview;
  final VoidCallback? onPreviewCancel;

  @override
  Widget build(BuildContext context) {
    final fg = selected ? color : const Color(0xFF475569);
    final item = Semantics(
      selected: selected,
      button: true,
      label: label,
      child: Focus(
      onFocusChange: (focused) {
        if (focused) {
          onPreview?.call();
        } else {
          onPreviewCancel?.call();
        }
      },
      child: MouseRegion(
      onEnter: (_) => onPreview?.call(),
      onExit: (_) => onPreviewCancel?.call(),
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
      ))),
    );
    // 접혀 있을 때는 이름을 툴팁으로 보여 준다.
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 1),
      child: expanded ? item : Tooltip(message: label, child: item),
    );
  }
}

/// 자료함·노트북처럼 위에 띄운 화면. 저장할 편집이 없으므로 앱을 닫을 때
/// 스스로 닫혀 종료를 막지 않는다(사용자 보고 2026-11-07: X를 눌러도 안 닫힘).
class HostClosablePage extends StatefulWidget {
  const HostClosablePage({super.key, required this.title, required this.child, this.backLabel = '처음 화면으로'});
  final String title;
  final Widget child;

  /// 왼쪽 위 돌아가기 단추 글(다른 화면에서 열었으면 그 화면 이름).
  final String backLabel;

  @override
  State<HostClosablePage> createState() => _HostClosablePageState();
}

class _HostClosablePageState extends State<HostClosablePage> {
  late final CloseLease _lease = CloseGuards.register(_prepareHostClose);

  Future<bool> _prepareHostClose() async {
    if (!mounted) return true;
    final navigator = Navigator.of(context);
    final route = ModalRoute.of(context);
    if (route != null) navigator.removeRoute(route);
    return true;
  }

  @override
  void initState() {
    super.initState();
    _lease;
  }

  @override
  void dispose() {
    _lease.release();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => CallbackShortcuts(
        bindings: {
          const SingleActivator(LogicalKeyboardKey.escape): () => Navigator.of(context).maybePop(),
        },
        child: Focus(
          autofocus: true,
          child: Column(
            children: [
              Material(
                color: Theme.of(context).colorScheme.surface,
                child: SizedBox(
                  height: 44,
                  child: Row(
                    children: [
                      const SizedBox(width: 4),
                      TextButton.icon(
                        key: const ValueKey('host-page-back'),
                        onPressed: () => Navigator.of(context).maybePop(),
                        icon: const Icon(Icons.arrow_back),
                        label: Text(widget.backLabel),
                      ),
                      const SizedBox(width: 8),
                      Text(widget.title, style: Theme.of(context).textTheme.titleMedium),
                    ],
                  ),
                ),
              ),
              const Divider(height: 1),
              Expanded(child: widget.child),
            ],
          ),
        ),
      );
}
