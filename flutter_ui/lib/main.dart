import 'dart:async';
import 'dart:convert';
import 'dart:math' as math;
import 'package:flutter/foundation.dart' show kIsWeb, listEquals;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'bridge.dart' as bridge;
import 'core/api/abbreviation_api.dart';
import 'core/close_guards.dart';
import 'core/drop_events.dart';
import 'features/preview/option_images.dart';
import 'features/abbreviations/abbreviation_manager.dart';
import 'features/formats/table_template_panel.dart';
import 'features/formats/profile_editor.dart';
import 'features/tools/document_tools_workspace.dart';
import 'features/tools/backend_dialog.dart';
import 'features/conversion/conversion_drop_pane.dart';
import 'features/conversion/floating_format_picker.dart';
import 'features/conversion/merge_order_dialog.dart';
import 'features/flows/flow_editor_screen.dart';
import 'features/progress/live_progress.dart';
import 'features/settings/settings_dialog.dart';
import 'features/settings/update_panel.dart';
import 'features/stages/stage_board.dart';
import 'features/table_units/table_units_screen.dart';
import 'features/table_sketch/table_sketch_screen.dart';
import 'features/workspace/workspace_adapters.dart';
import 'features/workspace/tab_navigation_shell.dart';


export 'core/api/abbreviation_api.dart' show ApiCall;

void main() => runApp(const DocFitApp());

const _ink = Color(0xff172b4d);
const _muted = Color(0xff64748b);
const _faint = Color(0xff8b98ad);
const _line = Color(0xffe2e8f0);
const _blue = Color(0xff2563eb);
const _blueDeep = Color(0xff1d4ed8);
const _blueSoft = Color(0xffedf3ff);
const _mint = Color(0xff287c72);
const _mintSoft = Color(0xfff3f8f7);

({Color surface, Color selectedSurface, Color accent}) _modeColors(
  String mode,
) => switch (mode) {
  'spacing' => (
    surface: const Color(0xfff0f5ff),
    selectedSurface: const Color(0xffe3edff),
    accent: const Color(0xff3b6fb6),
  ),
  'unify' => (
    surface: const Color(0xffeff8f5),
    selectedSurface: const Color(0xffdef1ea),
    accent: const Color(0xff2f8273),
  ),
  'all' => (
    surface: const Color(0xfffff7eb),
    selectedSurface: const Color(0xffffedcf),
    accent: const Color(0xffa86a1f),
  ),
  'file_format' => (
    surface: const Color(0xfff4f1ff),
    selectedSurface: const Color(0xffeae4ff),
    accent: const Color(0xff7656a8),
  ),
  _ => (surface: Colors.white, selectedSurface: _blueSoft, accent: _blue),
};

class DocFitApp extends StatelessWidget {
  const DocFitApp({
    super.key,
    this.api = bridge.callApi,
    this.useIntegratedShell = true,
  });
  final ApiCall api;
  final bool useIntegratedShell;
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: '한글편집 후처리',
    debugShowCheckedModeBanner: false,
    theme: ThemeData(
      useMaterial3: true,
      fontFamily: 'NotoSansKR',
      colorScheme: ColorScheme.fromSeed(seedColor: _blue),
      scaffoldBackgroundColor: const Color(0xfff6f8fb),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size(48, 52),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size(48, 48),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
      ),
      inputDecorationTheme: const InputDecorationTheme(
        border: OutlineInputBorder(),
      ),
    ),
    home: useIntegratedShell
        ? _IntegratedHome(api: api)
        : Workspace(api: api),
  );
}

/// 6탭 작업 공간. 파일변환 탭은 문서편집 화면의 '파일 변환' 흐름(키패드 포맷 선택 → 진행 → 4. 결과 확인)을
/// 그대로 쓰고, 탭에는 파일을 놓는 영역만 둔다(2026-10-29 사용자 요청, 2.0.2).
class _IntegratedHome extends StatefulWidget {
  const _IntegratedHome({required this.api});
  final ApiCall api;
  @override
  State<_IntegratedHome> createState() => _IntegratedHomeState();
}

class _IntegratedHomeState extends State<_IntegratedHome> {
  final workspace = GlobalKey<_WorkspaceState>();

  @override
  Widget build(BuildContext context) => IntegratedWorkspace(
    api: widget.api,
    documentEditorWidget: Workspace(key: workspace, api: widget.api),
    fileConversionWidget: ConversionDropPane(
      onPickFiles: () => workspace.currentState?.addConversionFiles(),
    ),
    onTabChanged: (index) {
      if (index == 5) workspace.currentState?.enterConversionMode();
    },
  );
}

class Workspace extends StatefulWidget {
  const Workspace({super.key, required this.api});
  final ApiCall api;
  @override
  State<Workspace> createState() => _WorkspaceState();
}

class _WorkspaceState extends State<Workspace> {
  Map<String, dynamic> state = {};
  int tab = 0;
  bool busy = false, polling = false, wasRunning = false;
  int commandVersion = 0;
  String? error;
  Timer? timer;
  void Function()? stopWatchingDrops;
  bool dropRefreshQueued = false;
  bool settingsVisible = false;
  final profileDropKey = GlobalKey();
  List<double>? lastProfileBounds;
  String? lastQuickNotice;

  void reportProfileBounds() {
    if (!kIsWeb || !mounted) return;
    final box = profileDropKey.currentContext?.findRenderObject();
    if (box is! RenderBox || !box.hasSize) return;
    final point = box.localToGlobal(Offset.zero);
    final bounds = [
      point.dx,
      point.dy,
      point.dx + box.size.width,
      point.dy + box.size.height,
    ];
    if (listEquals(bounds, lastProfileBounds)) return;
    lastProfileBounds = bounds;
    unawaited(
      widget
          .api('set_profile_drop_bounds', [bounds])
          .then((_) {})
          .catchError((_) {}),
    );
  }

  bool _conversionPickerOpen = false;
  Offset? _conversionAnchor;
  final scaffoldKey = GlobalKey<ScaffoldState>();
  // 쪽 범위는 화면에서 바로 입력하고, 시작할 때 앱에 넘긴다.
  final rangeStart = TextEditingController(text: '1');
  final rangeEnd = TextEditingController(text: '1');
  bool rangeOn = false, rangeLoaded = false;
  // '서식 관리' 창은 별도 대화상자라 상태가 바뀔 때마다 다시 그리도록 알린다.
  final stateVersion = ValueNotifier<int>(0);
  // 서식 관리에서 안 된 이유(이름 중복 등)를 창 안에 보여 준다.
  String? formatNotice;
  int formatSection = 0;
  bool backendDialogOpen = false;
  bool appClosing = false;

  static const tabs = ['문서 선택', '작업 방식', '진행 과정', '결과 확인'];
  // (내부 모드, 이름, 설명, 아이콘, 결과 파일 접미사). 서식 적용(format)은
  // '한 번에 적용' 카드에서 '자간 조정 포함'을 끈 것이다.
  static const modes = [
    (
      'spacing',
      '자간 정리',
      '줄 끝에서 끊긴 단어와 짧은 마지막 줄을 글자 간격으로 정리해요.',
      Icons.space_bar_rounded,
      '자간조정',
    ),
    (
      'unify',
      '서식 통일',
      '문서에서 가장 많이 쓴 서식을 기준으로 다른 문장만 맞춰요.',
      Icons.rule_rounded,
      '서식통일',
    ),
    (
      'all',
      '한 번에 적용',
      '고른 서식 기준의 글꼴·문단·표 모양을 입히고 자간까지 정리해요.',
      Icons.auto_awesome_rounded,
      '일괄적용',
    ),
    (
      'file_format',
      '파일 변환',
      'TXT·MD를 HWPX·PDF·그림으로, HWPX를 TXT·MD로도 바꿔요. 변환 도구는 앱에 포함되어 있어요.',
      Icons.swap_horiz_rounded,
      'HWPX변경',
    ),
  ];

  bool get running => state['running'] == true;
  bool get locked =>
      appClosing || busy || running || state.isEmpty || error != null;
  List get files => state['files'] as List? ?? [];
  List get results => state['results'] as List? ?? [];
  List get stages => state['stages'] as List? ?? [];
  List get profiles => state['profiles'] as List? ?? [];
  Map get quickOptions => state['options'] as Map? ?? {};
  String get mode => state['mode'] as String? ?? 'spacing';
  String get conversionTarget =>
      state['conversion_target'] as String? ?? 'hwpx';
  List get conversionTargets =>
      state['conversion_targets'] as List? ?? const [];
  bool get conversionTargetEnabled => conversionTargets.any(
    (item) =>
        item is Map &&
        item['format'] == conversionTarget &&
        item['enabled'] == true,
  );
  String get cardMode => mode == 'format' ? 'all' : mode;
  bool get includeSpacing => state['include_spacing'] != false;
  // '자간 정리' 카드의 '기존 자간 초기화'(세부 작업 01과 같은 값).
  bool get resetSpacing => state['reset_spacing'] != false;
  bool get tableSpacing => state['table_spacing'] != false;
  bool get spacingEnabled =>
      (state['card_options'] as Map? ?? const {})['spacing_enabled'] != false;
  bool get spacingPageFit => cardOption('spacing_page_fit');
  // '한 번에 적용'의 '표 제외'(설정 all_exclude_tables, 기본 꺼짐).
  bool get excludeTables => state['exclude_tables'] == true;
  // 카드 옵션(한 번에 적용 '페이지 맞춤 제외', 서식 통일 '표 제외'·'자간 정리 제외'·'페이지 맞춤 제외').
  // 앱이 세부 작업과 연동해 돌려주는 상태를 그대로 보여 준다(서식 통일 '페이지 맞춤 제외'만 기본 켜짐).
  bool cardOption(String key) =>
      (state['card_options'] as Map? ?? const {})[key] == true;
  String get modeTitle => mode == 'format'
      ? '한 번에 적용(자간 조정 제외)'
      : mode == 'spacing' && !spacingEnabled && spacingPageFit
      ? '페이지 맞춤만'
      : mode == 'file_format'
      ? '파일 변환'
      : modes.firstWhere((m) => m.$1 == mode, orElse: () => modes.first).$2;
  int get stagesOn => stages.where((s) => s['on'] == true).length;
  bool get stagesChanged => stages.any((s) => s['on'] != s['default']);
  bool get usesProfile => mode == 'format' || mode == 'all';

  String? get rangeError {
    if (!rangeOn) return null;
    final a = int.tryParse(rangeStart.text.trim());
    final b = int.tryParse(rangeEnd.text.trim());
    if (a == null || b == null || a < 1 || b < a) {
      return '시작·끝 쪽을 올바르게 입력하세요. 끝 쪽은 시작 쪽보다 작을 수 없어요.';
    }
    return null;
  }

  String get rangeLabel =>
      rangeOn ? '${rangeStart.text.trim()}~${rangeEnd.text.trim()}쪽' : '문서 전체';
  bool get canStart =>
      !locked &&
      state['engine_ready'] != false &&
      files.isNotEmpty &&
      (mode != 'spacing' || spacingEnabled || spacingPageFit) &&
      (mode == 'file_format'
          ? state['can_start'] == true && conversionTargetEnabled
          : rangeError == null && state['can_start'] == true);

  @override
  void initState() {
    super.initState();
    stopWatchingDrops = watchDocumentDrops(() {
      if (!mounted) return;
      commandVersion++;
      dropRefreshQueued = true;
      unawaited(refresh());
    });
    unawaited(_enableCloseGuard());
    refresh();
    timer = Timer.periodic(const Duration(seconds: 1), (_) => refresh());
  }

  Future<void> _enableCloseGuard() async {
    try {
      await widget.api('enable_close_guard', []);
    } catch (_) {
      /* Older preview hosts have no OS window. */
    }
  }

  @override
  void dispose() {
    stopWatchingDrops?.call();
    timer?.cancel();
    stateVersion.dispose();
    rangeStart.dispose();
    rangeEnd.dispose();
    super.dispose();
  }

  void apply(Map next, {bool syncRange = false}) {
    final documentDropped =
        (next['document_drop_revision'] as num? ?? 0) >
        (state['document_drop_revision'] as num? ?? 0);
    final previousRange = state['range'] as Map? ?? {};
    final range = next['range'] as Map? ?? {};
    final rangeChanged = [
      'enabled',
      'start',
      'end',
    ].any((key) => previousRange[key] != range[key]);
    final documentsChanged =
        jsonEncode(state['files'] ?? []) != jsonEncode(next['files'] ?? []);
    state = Map<String, dynamic>.from(next);
    // 입력 중인 값은 유지하되, 문서 변경·새 작업·백엔드 범위 변경은 반영한다.
    if (range.isNotEmpty &&
        (!rangeLoaded || syncRange || rangeChanged || documentsChanged)) {
      rangeLoaded = true;
      rangeOn = range['enabled'] == true;
      rangeStart.text = '${range['start'] ?? 1}';
      rangeEnd.text = '${range['end'] ?? 1}';
    }
    // 작업이 끝나면 진행 화면에서 결과 화면으로 넘어간다.
    if (wasRunning && !running && tab == 2) tab = 3;
    wasRunning = running;
    // 열린 '서식 관리' 창은 이 화면을 다 그린 뒤 다시 그린다(그리는 도중에 알리면 안 됨).
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      stateVersion.value++;
      reportProfileBounds();
      final quickNotice = state['quick_notice'] as Map? ?? const {};
      if (quickNotice['id'] is String && quickNotice['id'] != lastQuickNotice) {
        lastQuickNotice = quickNotice['id'] as String;
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('${quickNotice['message']}')));
      }
      if (files.isNotEmpty &&
          !locked &&
          (documentDropped || (documentsChanged && mode == 'file_format'))) {
        setState(() => tab = 1);
        if (mode == 'file_format') {
          // 파일변환 탭에서 넣은 파일도 문서편집 화면의 변환 흐름(진행·4. 결과 확인)으로 이어 간다.
          WorkspaceTabScope.maybeOf(context)?.selectTab(0);
          openConversionPicker();
        }
      }
    });
    checkBackendDialog();
  }

  Future<void> refresh() async {
    if (polling) return;
    if (busy) {
      try {
        final pending = await widget.api('get_pending_dialog', []);
        if (mounted && pending is Map && pending['id'] is String) {
          checkBackendDialog(pending);
        }
      } catch (_) {}
      return;
    }
    polling = true;
    dropRefreshQueued = false;
    final version = commandVersion;
    try {
      final next = await widget.api('get_state', []);
      if (mounted && version == commandVersion && next is Map) {
        setState(() {
          apply(next);
          error = null;
        });
      }
    } catch (_) {
      if (mounted && version == commandVersion) {
        setState(() => error = '앱과 연결하지 못했어요. 잠시 후 다시 확인합니다.');
      }
    } finally {
      polling = false;
      if (mounted && dropRefreshQueued && !busy) unawaited(refresh());
    }
  }

  Future<void> command(String method, [List<Object?> args = const []]) async {
    if (!mounted || busy) return;
    // 명령 전 시작된 조회는 명령 결과보다 오래된 상태일 수 있다.
    commandVersion++;
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final response = await widget.api(method, args);
      if (mounted && response is Map) {
        final notice = response['notice'];
        setState(() {
          formatNotice = notice is String && notice.isNotEmpty ? notice : null;
          apply(response, syncRange: method == 'next_job');
        });
        if (formatNotice != null) {
          ScaffoldMessenger.of(
            context,
          ).showSnackBar(SnackBar(content: Text(formatNotice!)));
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('작업을 실행하지 못했어요: $e')));
      }
    } finally {
      if (mounted) setState(() => busy = false);
      if (mounted && dropRefreshQueued) unawaited(refresh());
    }
  }

  Future<void> startJob({List<String>? fileOrder}) async {
    if (!canStart) return;
    final args = (<Object?>[
      mode,
      rangeOn,
      rangeStart.text.trim(),
      rangeEnd.text.trim(),
    ]);
    if (fileOrder != null) {
      args.add(fileOrder);
    }
    await command('start', args);
    if (mounted && running) setState(() => tab = 2);
  }

  /// 파일변환 탭을 열면 작업 방식을 '파일 변환'으로 바꾸고 끌어 놓은 파일을 문서 목록으로 받는다.
  Future<void> enterConversionMode() async {
    if (locked) return;
    if (mode != 'file_format') await command('set_mode', ['file_format']);
    await setDropTarget('documents');
  }

  /// 파일변환 탭의 '파일 선택'.
  Future<void> addConversionFiles() async {
    await enterConversionMode();
    if (!locked) await command('add_files');
  }

  Future<void> openConversionPicker() async {
    if (!mounted || locked || _conversionPickerOpen) return;
    _conversionPickerOpen = true;
    String? picked;
    try {
      picked = await showGeneralDialog<String>(
        context: context,
        barrierDismissible: true,
        barrierLabel: '포맷 선택창 닫기',
        barrierColor: const Color(0x480f172a),
        transitionDuration: const Duration(milliseconds: 160),
        pageBuilder: (dialogContext, animation, secondaryAnimation) =>
            LayoutBuilder(
              builder: (context, constraints) {
                // 키패드 포맷 선택 창(2026-10-29 사용자 요청: 30% 축소, 540×640 → 380×440).
                final width = math.min(380.0, constraints.maxWidth - 24);
                final height = math.min(440.0, constraints.maxHeight - 24);
                final anchor =
                    _conversionAnchor ??
                    Offset(constraints.maxWidth / 2, constraints.maxHeight / 2);
                final left = (anchor.dx - width / 2).clamp(
                  12.0,
                  math.max(12.0, constraints.maxWidth - width - 12),
                );
                final top = (anchor.dy - height / 2).clamp(
                  12.0,
                  math.max(12.0, constraints.maxHeight - height - 12),
                );
                return Stack(
                  children: [
                    Positioned(
                      left: left.toDouble(),
                      top: top.toDouble(),
                      width: width,
                      height: height,
                      child: CallbackShortcuts(
                        bindings: {
                          const SingleActivator(
                            LogicalKeyboardKey.escape,
                          ): () =>
                              Navigator.of(dialogContext).pop(),
                        },
                        child: Focus(
                          autofocus: true,
                          child: Material(
                            color: const Color(0xfff6f7fc),
                            borderRadius: BorderRadius.circular(28),
                            elevation: 16,
                            child: SingleChildScrollView(
                              padding: const EdgeInsets.all(12),
                              child: ValueListenableBuilder<int>(
                                valueListenable: stateVersion,
                                builder: (context, _, _) => FloatingFormatPicker(
                                  key: const Key('floatingConversionPicker'),
                                  targets: conversionTargets
                                      .whereType<Map>()
                                      .map(
                                        (item) => {
                                          ...item,
                                          'enabled':
                                              item['enabled'] == true &&
                                              !locked,
                                        },
                                      )
                                      .toList(),
                                  selected: conversionTarget,
                                  fileCount: files.length,
                                  fileNames: [
                                    for (final file in files.whereType<Map>())
                                      '${file['name'] ?? file['path'] ?? ''}',
                                  ],
                                  onSelected: (format) =>
                                      Navigator.of(dialogContext).pop(format),
                                  onCancel: () =>
                                      Navigator.of(dialogContext).pop(),
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                );
              },
            ),
        transitionBuilder: (context, animation, secondaryAnimation, child) =>
            FadeTransition(opacity: animation, child: child),
      );
    } finally {
      _conversionPickerOpen = false;
    }
    if (!mounted || picked == null || locked) return;
    if (!conversionTargets.any(
      (item) =>
          item is Map && item['format'] == picked && item['enabled'] == true,
    )) {
      return;
    }
    List<String>? mergeOrder;
    if (picked == 'pdfm' && files.length >= 2) {
      final docFiles = files.whereType<Map>().toList();
      final order = await showDialog<List<String>>(
        context: context,
        barrierDismissible: true,
        builder: (dialogContext) => MergeOrderDialog(files: docFiles),
      );
      if (!mounted || order == null) return;
      mergeOrder = order;
    }
    await command('set_conversion_target', [picked]);
    // 결과 형식을 고르면 '변환 시작'을 기다리지 않고 바로 변환한다(사용자 지시, 2026-10-15).
    if (mounted && mode == 'file_format' && canStart) {
      await startJob(fileOrder: mergeOrder);
    }
  }

  Widget conversionPanel() {
    final target = conversionTargets.whereType<Map>().firstWhere(
      (item) => item['format'] == conversionTarget,
      orElse: () => {'reason': '변환할 문서를 추가하세요.'},
    );
    return panel(
      Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          sectionTitle(
            Icons.swap_horiz_rounded,
            '선택한 결과 형식: ${conversionTarget.toUpperCase()}',
            '결과 형식을 고르면 바로 변환을 시작해요.',
          ),
          const SizedBox(height: 16),
          Listener(
            onPointerDown: (event) => _conversionAnchor = event.position,
            child: OutlinedButton.icon(
              key: const Key('openConversionPicker'),
              onPressed: locked ? null : openConversionPicker,
              icon: const Icon(Icons.donut_large_rounded),
              label: const Text('변환 포맷 선택'),
            ),
          ),
          const SizedBox(height: 12),
          Text(
            '${target['reason'] ?? ''}',
            key: const Key('conversionSummaryNotice'),
            style: const TextStyle(fontSize: 12, color: _muted),
          ),
          const SizedBox(height: 6),
          const Text(
            '원본을 보존하고 결과를 원본 폴더에 새 파일로 저장해요.',
            style: TextStyle(fontSize: 12, color: _faint),
          ),
        ],
      ),
    );
  }

  /// 6탭 화면 안이면 새 화면을 덮어 열지 않고 해당 탭으로 옮긴다(하단 탭 메뉴가 사라지던 문제).
  bool _switchWorkspaceTab(int index) {
    final scope = WorkspaceTabScope.maybeOf(context);
    if (scope == null) return false;
    scope.selectTab(index);
    return true;
  }

  Future<void> openFlowEditor({String mode = 'diagram'}) async {
    if (_switchWorkspaceTab(mode == 'mindmap' ? 4 : 3)) return;
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => FlowEditorScreen(api: widget.api, initialMode: mode),
      ),
    );
  }

  Future<void> openTableUnits() async {
    if (_switchWorkspaceTab(1)) return;
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => TableUnitsScreen(api: widget.api),
      ),
    );
  }

  Future<void> openTableSketch() async {
    if (_switchWorkspaceTab(2)) return;
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => TableSketchScreen(api: widget.api),
      ),
    );
  }

  /// Ctrl+Enter: 문서 선택 화면에서는 다음 단계로, 작업 방식 화면에서는 바로 시작한다.
  void primaryShortcut() {
    if (tab == 0 && !locked && files.isNotEmpty) {
      setState(() => tab = 1);
    } else if (tab == 1) {
      startJob();
    }
  }

  Widget panel(Widget child, {EdgeInsets padding = const EdgeInsets.all(24)}) =>
      Container(
        padding: padding,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: const Color(0xffe8edf4)),
          boxShadow: const [
            BoxShadow(
              color: Color(0x050f172a),
              blurRadius: 24,
              offset: Offset(0, 8),
            ),
          ],
        ),
        child: Material(type: MaterialType.transparency, child: child),
      );
  Widget heading(String title, String subtitle) => Padding(
    padding: const EdgeInsets.only(bottom: 24),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: Theme.of(
            context,
          ).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 10),
        Text(subtitle, style: const TextStyle(color: _muted, height: 1.6)),
      ],
    ),
  );
  Widget sectionTitle(IconData icon, String title, String subtitle) => Row(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: _blueSoft,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Icon(icon, size: 20, color: _blue),
      ),
      const SizedBox(width: 14),
      Expanded(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 4),
            Text(
              subtitle,
              style: const TextStyle(fontSize: 13, color: _muted, height: 1.5),
            ),
          ],
        ),
      ),
    ],
  );

  @override
  Widget build(BuildContext context) {
    WidgetsBinding.instance.addPostFrameCallback((_) => reportProfileBounds());
    return _closeLock(
      CallbackShortcuts(
        bindings: {
          const SingleActivator(LogicalKeyboardKey.keyO, control: true): () {
            if (!locked) command('add_files');
          },
          const SingleActivator(LogicalKeyboardKey.enter, control: true):
              primaryShortcut,
          const SingleActivator(LogicalKeyboardKey.f1): showHelp,
        },
        child: Focus(
          autofocus: true,
          child: Scaffold(
            key: scaffoldKey,
            endDrawer: settingsDrawer(),
            onEndDrawerChanged: (open) {
              settingsVisible = open;
              if (state['doc_hints'] is Map) {
                unawaited(setDropTarget('documents'));
              }
            },
            appBar: appBar(),
            body: SafeArea(
              child: LayoutBuilder(
                builder: (context, layout) => Row(
                  children: [
                    if (layout.maxWidth >= 1000) sidebar(),
                    Expanded(
                      child: Column(
                        children: [
                          if (busy) const LinearProgressIndicator(minHeight: 2),
                          if (error != null)
                            Material(
                              color: const Color(0xfffff1da),
                              child: ListTile(
                                leading: const Icon(Icons.wifi_off_rounded),
                                title: Text(error!),
                                trailing: IconButton(
                                  onPressed: state['native_backend'] == true
                                      ? () => command('restart_backend')
                                      : refresh,
                                  tooltip: '다시 연결',
                                  icon: const Icon(Icons.refresh),
                                ),
                              ),
                            ),
                          if (layout.maxWidth < 1000) topTabs(),
                          Expanded(
                            child: SingleChildScrollView(
                              padding: const EdgeInsets.fromLTRB(
                                20,
                                12,
                                20,
                                32,
                              ),
                              child: Center(
                                child: ConstrainedBox(
                                  constraints: const BoxConstraints(
                                    maxWidth: 960,
                                  ),
                                  child: AnimatedSwitcher(
                                    duration: const Duration(milliseconds: 160),
                                    child: KeyedSubtree(
                                      key: ValueKey(tab),
                                      child: [
                                        documents,
                                        options,
                                        progress,
                                        outcome,
                                      ][tab](),
                                    ),
                                  ),
                                ),
                              ),
                            ),
                          ),
                          bottomBar(),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _closeLock(Widget child) => ExcludeFocus(
    excluding: appClosing,
    child: AbsorbPointer(absorbing: appClosing, child: child),
  );

  PreferredSizeWidget appBar() => PreferredSize(
    preferredSize: const Size.fromHeight(72),
    child: LayoutBuilder(
      builder: (context, constraints) {
        final width = constraints.maxWidth;
        // 네 메뉴 버튼(서식 관리·다이어그램·마인드맵·표 템플릿)을 글과 함께 놓으려면 약 880이 필요하다(폭 800에서 79 넘침).
        // 다섯 메뉴 버튼을 글과 함께 놓으려면 약 1180이 필요하다. 모자라면 아이콘만(이름은 툴팁) — 잘려 보이지 않게(2026-10-23 사용자 실측).
        final isNarrow = width < 1180;
        final showProfileBadge = width >= 1360;
        final currentProfileName =
            '${profiles.whereType<Map>().where((p) => p['id'] == state['profile']).firstOrNull?['name'] ?? '기본 보고서 서식'}';

        Widget topBtn({
          required Key key,
          required String label,
          required IconData icon,
          required VoidCallback? onPressed,
          String? tooltip,
        }) {
          final btn = TextButton.icon(
            key: key,
            onPressed: locked ? null : onPressed,
            icon: Icon(icon, size: 18),
            label: isNarrow ? const SizedBox.shrink() : Text(label),
            style: TextButton.styleFrom(
              visualDensity: VisualDensity.compact,
              padding: EdgeInsets.symmetric(horizontal: isNarrow ? 4 : 8),
              minimumSize: isNarrow ? const Size(36, 36) : null,
            ),
          );
          return Tooltip(message: tooltip ?? label, child: btn);
        }

        final formatButton = Tooltip(
          message: isNarrow
              ? '서식 관리 (현재: $currentProfileName)\nHWP/HWPX 예시를 놓으면 새 서식으로 등록해요.'
              : 'HWP/HWPX 예시를 여기에 놓으면 새 서식으로 등록·선택해요.',
          // 서식 관리를 누르면 하위 메뉴: 썸네일로 선택 · 서식예시 확인 · 서식예시 폴더 · 서식관리(2026-10-23 사용자 요청).
          // 서식 관리를 누르면 바로 '서식 고르기'(썸네일) — 카드마다 서식예시 확인·서식예시 폴더·서식관리(2026-10-23 사용자 요청).
          child: TextButton.icon(
            key: const Key('topMenu_format'),
            onPressed: locked ? null : openKiosk,
            icon: const Icon(Icons.style_outlined, size: 18),
            label: isNarrow ? const SizedBox.shrink() : const Text('서식 관리'),
            style: TextButton.styleFrom(
              visualDensity: VisualDensity.compact,
              padding: EdgeInsets.symmetric(horizontal: isNarrow ? 4 : 8),
              minimumSize: isNarrow ? const Size(36, 36) : null,
            ),
          ),
        );

        return AppBar(
          backgroundColor: Colors.white,
          surfaceTintColor: Colors.transparent,
          toolbarHeight: 72,
          automaticallyImplyLeading: false,
          titleSpacing: isNarrow ? 8 : 16,
          title: Row(
            children: [
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  color: _ink,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(
                  Icons.description_rounded,
                  color: Colors.white,
                  size: 23,
                ),
              ),
              // 아주 좁은 창(700 미만)에서는 앱 이름 글을 숨겨 메뉴 아이콘 자리를 확보한다(이름은 창 제목줄에 있다).
              if (width >= 700) const SizedBox(width: 8),
              if (width >= 700)
                Flexible(
                  child: Text(
                    '한글편집 후처리',
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: isNarrow ? 17 : 20,
                      fontWeight: FontWeight.w800,
                      letterSpacing: -.8,
                    ),
                  ),
                ),
              const SizedBox(width: 8),
              if (!showProfileBadge)
                KeyedSubtree(key: profileDropKey, child: formatButton)
              else
                formatButton,
              if (showProfileBadge) ...[
                const SizedBox(width: 4),
                Tooltip(
                  message: 'HWP/HWPX 예시를 여기에 놓으면 새 서식으로 등록·선택해요.',
                  child: ConstrainedBox(
                    key: profileDropKey,
                    constraints: const BoxConstraints(maxWidth: 130),
                    child: ActionChip(
                      key: const Key('quickProfileDropBadge'),
                      avatar: const Icon(Icons.check, size: 14),
                      label: Text(
                        currentProfileName,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontSize: 12),
                      ),
                      onPressed: locked ? null : openFormats,
                    ),
                  ),
                ),
              ],
              const SizedBox(width: 4),
              // 메뉴 버튼이 늘어도 넘치지 않게, 공간이 모자라면 옆으로 밀어 볼 수 있게 한다.
              Flexible(
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      topBtn(
                        key: const Key('topMenu_diagram'),
                        label: '다이어그램',
                        icon: Icons.account_tree_outlined,
                        onPressed: () => openFlowEditor(mode: 'diagram'),
                      ),
                      const SizedBox(width: 4),
                      topBtn(
                        key: const Key('topMenu_mindmap'),
                        label: '마인드맵',
                        icon: Icons.hub_outlined,
                        onPressed: () => openFlowEditor(mode: 'mindmap'),
                      ),
                      const SizedBox(width: 4),
                      topBtn(
                        key: const Key('topMenu_tableUnits'),
                        label: '표 템플릿',
                        icon: Icons.grid_on_outlined,
                        onPressed: openTableUnits,
                      ),
                      const SizedBox(width: 4),
                      topBtn(
                        key: const Key('topMenu_tableSketch'),
                        label: '표그림판',
                        icon: Icons.border_all_outlined,
                        onPressed: openTableSketch,
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
          actions: [
            IconButton(
              tooltip: '사용 방법 (F1)',
              visualDensity: isNarrow ? VisualDensity.compact : null,
              padding: isNarrow ? EdgeInsets.zero : null,
              constraints: isNarrow
                  ? const BoxConstraints(minWidth: 32, minHeight: 32)
                  : null,
              onPressed: showHelp,
              icon: const Icon(Icons.help_outline_rounded),
            ),
            IconButton(
              tooltip: '작업 로그',
              visualDensity: isNarrow ? VisualDensity.compact : null,
              padding: isNarrow ? EdgeInsets.zero : null,
              constraints: isNarrow
                  ? const BoxConstraints(minWidth: 32, minHeight: 32)
                  : null,
              onPressed: () => showLog(),
              icon: const Icon(Icons.receipt_long_outlined),
            ),
            IconButton(
              tooltip: '설정',
              visualDensity: isNarrow ? VisualDensity.compact : null,
              padding: isNarrow ? EdgeInsets.zero : null,
              constraints: isNarrow
                  ? const BoxConstraints(minWidth: 32, minHeight: 32)
                  : null,
              onPressed: () async {
                if (mounted) scaffoldKey.currentState?.openEndDrawer();
              },
              icon: const Icon(Icons.settings_outlined),
            ),
            SizedBox(width: isNarrow ? 6 : 12),
          ],
        );
      },
    ),
  );

  /// 단계 메뉴에 붙이는 한 줄 요약. 어느 화면에서든 지금 상태를 알 수 있게 한다.
  String tabHint(int i) => switch (i) {
    0 => files.isEmpty ? '문서를 추가하세요' : '${files.length}개 문서',
    1 => '$modeTitle · $rangeLabel',
    2 => running ? '진행 중' : (results.isEmpty ? '대기 중' : '끝남'),
    _ => results.isEmpty ? '결과 없음' : '${results.length}개 저장',
  };

  Widget topTabs() => Padding(
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
    child: Row(
      children: List.generate(
        tabs.length,
        (i) => Expanded(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 3),
            child: Tooltip(
              message: tabHint(i),
              child: TextButton(
                style: TextButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  backgroundColor: tab == i
                      ? const Color(0xffe4edff)
                      : Colors.transparent,
                  foregroundColor: tab == i ? _blueDeep : _muted,
                ),
                onPressed: () => setState(() => tab = i),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (i == 2 && running) ...[
                      const SizedBox(
                        width: 12,
                        height: 12,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                      const SizedBox(width: 6),
                    ],
                    Flexible(
                      child: Text(
                        '${i + 1}. ${tabs[i]}',
                        textAlign: TextAlign.center,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    ),
  );

  Widget sidebar() => Container(
    width: 232,
    decoration: const BoxDecoration(
      color: Colors.white,
      border: Border(right: BorderSide(color: Color(0xffe8edf4))),
    ),
    padding: const EdgeInsets.fromLTRB(20, 32, 20, 24),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.only(left: 12, bottom: 22),
          child: Text(
            '작업 순서',
            style: TextStyle(
              fontSize: 12,
              color: _faint,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
        for (var i = 0; i < tabs.length; i++)
          Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Material(
              color: tab == i ? _blueSoft : Colors.transparent,
              borderRadius: BorderRadius.circular(14),
              child: InkWell(
                borderRadius: BorderRadius.circular(14),
                onTap: () => setState(() => tab = i),
                child: Padding(
                  padding: const EdgeInsets.symmetric(
                    vertical: 12,
                    horizontal: 12,
                  ),
                  child: Row(
                    children: [
                      Text(
                        '0${i + 1}',
                        style: TextStyle(
                          fontSize: 12,
                          color: tab == i ? _blue : const Color(0xffa5afbd),
                        ),
                      ),
                      const SizedBox(width: 13),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              tabs[i],
                              style: TextStyle(
                                fontWeight: tab == i
                                    ? FontWeight.w700
                                    : FontWeight.w500,
                                color: tab == i
                                    ? _blueDeep
                                    : const Color(0xff66748a),
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              tabHint(i),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                fontSize: 11,
                                color: _faint,
                              ),
                            ),
                          ],
                        ),
                      ),
                      if (i == 2 && running)
                        const SizedBox(
                          width: 14,
                          height: 14,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      else if (tab == i)
                        const Icon(
                          Icons.arrow_forward_rounded,
                          size: 16,
                          color: _blue,
                        ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        const Spacer(),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: _mintSoft,
            borderRadius: BorderRadius.circular(18),
          ),
          child: const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.verified_user_outlined, color: _mint, size: 24),
              SizedBox(height: 12),
              Text(
                '원본은 그대로 둬요',
                style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
              ),
              SizedBox(height: 6),
              Text(
                '결과는 원본 폴더에 새 파일로 저장돼요.',
                style: TextStyle(fontSize: 11, color: Color(0xff738299)),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),
        Text(
          '${state['version'] ?? '연결 중'}',
          style: const TextStyle(fontSize: 10, color: _faint),
        ),
      ],
    ),
  );

  // ---- 1. 문서 선택 -------------------------------------------------

  Widget documents() => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      if (files.isEmpty) ...[welcome(), const SizedBox(height: 24)],
      dropZone(compact: files.isNotEmpty),
      if (files.isNotEmpty) ...[
        const SizedBox(height: 20),
        Row(
          children: [
            Text(
              '선택한 문서 ${files.length}개',
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            const Spacer(),
            TextButton.icon(
              onPressed: locked ? null : () => command('clear_files'),
              icon: const Icon(Icons.delete_sweep_outlined, size: 18),
              label: const Text('전체 비우기'),
            ),
          ],
        ),
        const SizedBox(height: 8),
        panel(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
          Column(
            children: List.generate(
              files.length,
              (i) => ListTile(
                contentPadding: EdgeInsets.zero,
                leading: fileBadge('${files[i]['name'] ?? ''}'),
                title: Text(
                  files[i]['name'] ?? '',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                subtitle: Text(
                  '${files[i]['folder'] ?? ''}',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 12, color: _faint),
                ),
                trailing: IconButton(
                  tooltip: '목록에서 제거',
                  onPressed: locked ? null : () => command('remove_file', [i]),
                  icon: const Icon(Icons.close),
                ),
              ),
            ),
          ),
        ),
      ],
    ],
  );

  Widget fileBadge(String name) {
    final dot = name.lastIndexOf('.');
    final ext = dot < 0 ? '문서' : name.substring(dot + 1).toUpperCase();
    return Container(
      width: 48,
      padding: const EdgeInsets.symmetric(vertical: 6),
      decoration: BoxDecoration(
        color: ext == 'HWP' ? const Color(0xfffff4e5) : _blueSoft,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Text(
        ext,
        textAlign: TextAlign.center,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w700,
          color: ext == 'HWP' ? const Color(0xffb45309) : _blueDeep,
        ),
      ),
    );
  }

  Widget addButtons() => Wrap(
    spacing: 12,
    runSpacing: 12,
    alignment: WrapAlignment.center,
    children: [
      FilledButton.icon(
        onPressed: locked ? null : () => command('add_files'),
        icon: const Icon(Icons.add),
        label: const Text('문서 추가'),
      ),
      OutlinedButton.icon(
        onPressed: locked ? null : () => command('add_folder'),
        icon: const Icon(Icons.folder_open),
        label: const Text('폴더 추가'),
      ),
      OutlinedButton.icon(
        onPressed: locked ? null : () => openTools('convert'),
        icon: const Icon(Icons.edit_note),
        label: const Text('텍스트 입력'),
      ),
    ],
  );

  /// 문서가 없으면 크게, 이미 있으면 한 줄로 줄여 목록이 잘 보이게 한다.
  Widget dropZone({required bool compact}) => panel(
    padding: EdgeInsets.all(compact ? 18 : 24),
    compact
        ? LayoutBuilder(
            builder: (context, box) {
              const hint = Text(
                '문서를 더 끌어다 놓거나 추가할 수 있어요.',
                style: TextStyle(color: _muted),
              );
              return box.maxWidth >= 760
                  ? Row(
                      children: [
                        const Icon(Icons.upload_file_rounded, color: _blue),
                        const SizedBox(width: 12),
                        const Expanded(child: hint),
                        addButtons(),
                      ],
                    )
                  : Column(
                      children: [
                        const Icon(Icons.upload_file_rounded, color: _blue),
                        const SizedBox(height: 8),
                        hint,
                        const SizedBox(height: 14),
                        addButtons(),
                      ],
                    );
            },
          )
        : Column(
            children: [
              Container(
                padding: const EdgeInsets.all(15),
                decoration: BoxDecoration(
                  color: _blueSoft,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Icon(
                  Icons.upload_file_rounded,
                  size: 34,
                  color: _blue,
                ),
              ),
              const SizedBox(height: 18),
              const Text(
                '정리할 문서를 여기에 끌어다 놓으세요',
                textAlign: TextAlign.center,
                style: TextStyle(fontWeight: FontWeight.w700, fontSize: 19),
              ),
              const SizedBox(height: 8),
              const Text(
                'HWP·HWPX 파일이나 폴더를 넣을 수 있어요. 여러 개를 한 번에 넣어도 돼요.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Color(0xff738299), fontSize: 13),
              ),
              const SizedBox(height: 24),
              addButtons(),
              const SizedBox(height: 14),
              const Text(
                '단축키 Ctrl+O로 문서를 바로 추가할 수 있어요.',
                style: TextStyle(fontSize: 12, color: _faint),
              ),
            ],
          ),
  );

  Widget welcome() => LayoutBuilder(
    builder: (context, layout) => Container(
      padding: EdgeInsets.all(layout.maxWidth < 500 ? 24 : 34),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(28),
        gradient: const LinearGradient(
          colors: [Color(0xffeaf0ff), Color(0xffedf8f5)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '3 단계면 끝나요',
                  style: TextStyle(
                    fontSize: layout.maxWidth < 500 ? 26 : 32,
                    fontWeight: FontWeight.w800,
                    height: 1.35,
                    letterSpacing: -1.2,
                    color: _ink,
                  ),
                ),
                const SizedBox(height: 18),
                for (final (n, text) in const [
                  ('1', '정리할 문서를 넣어요.'),
                  ('2', '작업 방식을 고르고 필요하면 세부 작업을 조정해요.'),
                  ('3', '정리 시작을 누르면 결과가 새 파일로 저장돼요.'),
                ])
                  Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        CircleAvatar(
                          radius: 11,
                          backgroundColor: Colors.white,
                          child: Text(
                            n,
                            style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                              color: _blue,
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            text,
                            style: const TextStyle(
                              fontSize: 14,
                              height: 1.5,
                              color: Color(0xff4b5f7c),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
          if (layout.maxWidth >= 580)
            const SizedBox(width: 210, height: 210, child: DocumentArtwork()),
        ],
      ),
    ),
  );

  // ---- 2. 작업 방식 -------------------------------------------------

  Widget options() => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      heading('어떻게 정리할까요?', '작업을 고르면 아래에서 세부 작업과 범위를 바로 조정할 수 있어요.'),
      LayoutBuilder(
        builder: (context, box) {
          final columns = box.maxWidth >= 1200
              ? 4
              : box.maxWidth >= 620
              ? 2
              : 1;
          return Wrap(
            spacing: 16,
            runSpacing: 16,
            children: modes
                .map(
                  (m) => SizedBox(
                    width: (box.maxWidth - 16 * (columns - 1)) / columns,
                    child: modeCard(m),
                  ),
                )
                .toList(),
          );
        },
      ),
      const SizedBox(height: 20),
      if (mode == 'file_format')
        conversionPanel()
      else ...[
        if (usesProfile) ...[
          panel(
            Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                sectionTitle(
                  Icons.style_outlined,
                  '서식 기준',
                  '서식 적용 단계에서 이 서식의 글꼴·문단·표 모양을 사용해요.',
                ),
                const SizedBox(height: 16),
                profilePicker(),
              ],
            ),
          ),
          const SizedBox(height: 16),
        ],
        stagePanel(),
        const SizedBox(height: 16),
        rangePanel(),
      ],
    ],
  );

  Widget modeCard((String, String, String, IconData, String) m) {
    final selected = cardMode == m.$1;
    final colors = _modeColors(m.$1);
    final isAll = m.$1 == 'all';
    final suffix = m.$1 == 'file_format'
        ? '${conversionTarget.toUpperCase()}변경'
        : m.$1 == 'spacing' && !spacingEnabled && spacingPageFit
        ? '페이지맞춤만'
        : isAll && !includeSpacing
        ? '서식적용'
        : m.$5;
    return Material(
      key: Key('modeCard-${m.$1}'),
      color: selected ? colors.selectedSurface : colors.surface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: BorderSide(
          color: selected
              ? colors.accent
              : colors.accent.withValues(alpha: 0.28),
          width: selected ? 2 : 1,
        ),
      ),
      clipBehavior: Clip.antiAlias,
      child: Semantics(
        selected: selected,
        button: true,
        child: InkWell(
          onTapDown: (details) => _conversionAnchor = details.globalPosition,
          onTap: locked
              ? null
              : () async {
                  await command('set_mode', [m.$1]);
                  if (mounted &&
                      mode == 'file_format' &&
                      m.$1 == 'file_format') {
                    await openConversionPicker();
                  }
                },
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(m.$4, size: 36, color: colors.accent),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        m.$2,
                        style: const TextStyle(
                          fontSize: 19,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                    Icon(
                      selected
                          ? Icons.check_circle
                          : Icons.radio_button_unchecked,
                      size: 36,
                      color: selected ? colors.accent : const Color(0xffcbd5e1),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Text(m.$3, style: const TextStyle(height: 1.6)),
                if (selected &&
                    files.isNotEmpty &&
                    state['doc_hints'] is Map &&
                    state['user_overrode_mode'] != true)
                  Tooltip(
                    message: '${docHints['reason'] ?? ''}',
                    child: Chip(label: const Text('✨ 문서 자동 맞춤')),
                  ),
                if (selected && m.$1 != 'file_format') modeOptions(m.$1),
                const SizedBox(height: 12),
                Text(
                  '결과: 문서이름($suffix).hwpx',
                  style: const TextStyle(fontSize: 12, color: _faint),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Map get docHints => state['doc_hints'] as Map? ?? const {};
  bool get showTableOptions => true;

  Widget modeOptions(String optionMode) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      if (optionMode == 'spacing') ...[
        const SizedBox(height: 8),
        Row(
          children: [
            const Expanded(
              child: Text(
                '자간 정리',
                style: TextStyle(fontWeight: FontWeight.w600),
              ),
            ),
            const OptionImageButton('spacing_enabled'),
            Switch(
              key: const Key('spacingEnabledSwitch'),
              value: spacingEnabled,
              onChanged: locked
                  ? null
                  : (on) => command('set_card_option', ['spacing_enabled', on]),
            ),
          ],
        ),
        Row(
          children: [
            const Expanded(
              child: Text(
                '페이지 맞춤',
                style: TextStyle(fontWeight: FontWeight.w600),
              ),
            ),
            const OptionImageButton('spacing_page_fit'),
            Switch(
              key: const Key('spacingPageFitSwitch'),
              value: spacingPageFit,
              onChanged: locked
                  ? null
                  : (on) =>
                        command('set_card_option', ['spacing_page_fit', on]),
            ),
          ],
        ),
        if (!spacingEnabled)
          Text(
            spacingPageFit
                ? '자간·장평·줄 병합은 그대로 두고 문단·표의 세로 간격과 페이지 배치만 조정해요.'
                : '자간 정리 또는 페이지 맞춤을 하나 이상 켜 주세요.',
            style: const TextStyle(fontSize: 12, color: _faint),
          ),
        // 끄면 문서에 이미 있는 자간을 0%로 되돌리지 않고 그 위에서 정리한다.
        Row(
          children: [
            const Expanded(
              child: Text(
                '기존 자간 초기화',
                style: TextStyle(fontWeight: FontWeight.w600),
              ),
            ),
            Switch(
              key: const Key('resetSpacingSwitch'),
              value: resetSpacing,
              onChanged: locked || !spacingEnabled
                  ? null
                  : (on) => command('set_reset_spacing', [on]),
            ),
          ],
        ),
        if (spacingEnabled && !resetSpacing)
          const Text(
            '문서에 있던 자간은 그대로 두고 그 위에서 정리해요.',
            style: TextStyle(fontSize: 12, color: _faint),
          ),
        // '표 제외'를 켜면 표 칸 안 문장은 자간 정리 대상에서 뺀다(설정 table_spacing의 반대 값).
        if (showTableOptions)
          Row(
            children: [
              const Expanded(
                child: Text(
                  '표 제외',
                  style: TextStyle(fontWeight: FontWeight.w600),
                ),
              ),
              Switch(
                key: const Key('tableSpacingSwitch'),
                value: !tableSpacing,
                onChanged: locked || !spacingEnabled
                    ? null
                    : (on) => command('set_table_spacing', [!on]),
              ),
            ],
          ),
        if (!tableSpacing)
          const Text(
            '표 칸 안 문장은 자간 정리에서 빼요.',
            style: TextStyle(fontSize: 12, color: _faint),
          ),
      ],
      if (optionMode == 'unify') ...[
        const SizedBox(height: 8),
        for (final o in const [
          ('unify_exclude_tables', '표 제외', '기본 표 서식·표 서식통일을 빼요.'),
          ('unify_exclude_spacing', '자간 정리 제외', '서식통일이 고친 문장의 자간은 그대로 둬요.'),
          ('unify_exclude_pagefit', '페이지 맞춤 제외', '문단 아래 간격 페이지 맞춤을 빼요.'),
          ('unify_keep_layout', '원본 쪽 구성 유지', '보고서별 쪽 수·시작 쪽을 원본과 같게 맞춰요.'),
          (
            'unify_full_format',
            '전체 서식 맞추기',
            '글꼴·크기뿐 아니라 색·밑줄·정렬·여백·내어쓰기도 맞춰요.',
          ),
        ].where((o) => o.$1 != 'unify_exclude_tables' || showTableOptions)) ...[
          Row(
            children: [
              Expanded(
                child: Text(
                  o.$2,
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
              ),
              OptionImageButton(o.$1),
              Switch(
                key: Key('${o.$1}Switch'),
                value: cardOption(o.$1),
                onChanged: locked
                    ? null
                    : (on) => command('set_card_option', [o.$1, on]),
              ),
            ],
          ),
          if (cardOption(o.$1))
            Text(o.$3, style: const TextStyle(fontSize: 12, color: _faint)),
        ],
      ],
      if (optionMode == 'all') ...[
        const SizedBox(height: 8),
        // 끄면 기존 자간은 그대로 두고 서식만 적용한다(서식 적용).
        Row(
          children: [
            const Expanded(
              child: Text(
                '자간 조정 포함',
                style: TextStyle(fontWeight: FontWeight.w600),
              ),
            ),
            const OptionImageButton('all_include_spacing'),
            Switch(
              key: const Key('includeSpacingSwitch'),
              value: includeSpacing,
              onChanged: locked
                  ? null
                  : (on) => command('set_include_spacing', [on]),
            ),
          ],
        ),
        if (!includeSpacing)
          const Text(
            '기존 자간은 그대로 두고 서식만 적용해요.',
            style: TextStyle(fontSize: 12, color: _faint),
          ),
        // 켜면 표 관련 작업을 모두 빼고 정리한다(제목·개요 서식 표는 정리).
        if (showTableOptions)
          Row(
            children: [
              const Expanded(
                child: Text(
                  '표 제외',
                  style: TextStyle(fontWeight: FontWeight.w600),
                ),
              ),
              Switch(
                key: const Key('excludeTablesSwitch'),
                value: excludeTables,
                onChanged: locked
                    ? null
                    : (on) => command('set_exclude_tables', [on]),
              ),
            ],
          ),
        if (excludeTables)
          const Text(
            '표 관련 작업은 모두 빼고 정리해요. 제목·개요 서식 표는 정리해요.',
            style: TextStyle(fontSize: 12, color: _faint),
          ),
        Row(
          children: [
            const Expanded(
              child: Text(
                '줄 간격 적용',
                style: TextStyle(fontWeight: FontWeight.w600),
              ),
            ),
            Switch(
              key: const Key('allLinespacingSwitch'),
              value:
                  (state['card_options'] as Map? ??
                      const {})['all_linespacing'] !=
                  false,
              onChanged: locked
                  ? null
                  : (on) => command('set_card_option', ['all_linespacing', on]),
            ),
          ],
        ),
        // 켜면 문단 아래 간격 페이지 맞춤·관련 문단 페이지 배치를 뺀다.
        Row(
          children: [
            const Expanded(
              child: Text(
                '페이지 맞춤 제외',
                style: TextStyle(fontWeight: FontWeight.w600),
              ),
            ),
            Switch(
              key: const Key('allExcludePagefitSwitch'),
              value: cardOption('all_exclude_pagefit'),
              onChanged: locked
                  ? null
                  : (on) =>
                        command('set_card_option', ['all_exclude_pagefit', on]),
            ),
          ],
        ),
        if (cardOption('all_exclude_pagefit'))
          const Text(
            '문단 아래 간격 페이지 맞춤·관련 문단 페이지 배치를 빼요.',
            style: TextStyle(fontSize: 12, color: _faint),
          ),
      ],
    ],
  );

  // ---- 서식 관리: 예시 보고서를 끌어다 놓아 서식 복제, 이름 바꾸기·세부 수정·삭제 ----
  Map get formatTask => state['format_task'] as Map? ?? const {};

  Future<void> setDropTarget(String target) async {
    try {
      await widget.api('set_drop_target', [
        target == 'documents' && settingsVisible ? 'manual_documents' : target,
      ]);
    } catch (_) {}
  }

  // 키오스크에서 메뉴 사진을 보고 고르듯, 서식마다 예시 보고서 첫 쪽 그림(스틸컷)과 이름을 카드로 보여 주고 눌러 고른다(알파).
  Future<void> openKiosk() async {
    if (!mounted) return;
    Object? data;
    try {
      data = await widget.api('format_gallery', []);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('서식 그림을 불러오지 못했어요: $e')));
      }
      return;
    }
    if (!mounted || data is! List) return;
    final items = data.whereType<Map>().toList();
    final picked = await showDialog<String>(
      context: context,
      builder: (ctx) => Dialog(
        key: const Key('formatKioskDialog'),
        insetPadding: const EdgeInsets.all(24),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1000, maxHeight: 760),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('서식 고르기', style: Theme.of(ctx).textTheme.titleLarge),
                const SizedBox(height: 4),
                const Text(
                  '예시 보고서 첫 쪽 그림을 보고 원하는 서식 카드를 누르세요. 누르면 바로 그 서식으로 바뀌어요.',
                ),
                const SizedBox(height: 12),
                Expanded(
                  child: GridView.extent(
                    maxCrossAxisExtent: 240,
                    childAspectRatio: 0.5,
                    mainAxisSpacing: 12,
                    crossAxisSpacing: 12,
                    children: [for (final p in items) kioskCard(ctx, p)],
                  ),
                ),
                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton(
                    onPressed: () => Navigator.pop(ctx),
                    child: const Text('닫기'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
    if (picked == null) return;
    // 카드 아래 버튼은 'example:<id>'·'samples:<id>'·'manage:<id>', 카드 자체를 누르면 '<id>'.
    final cut = picked.indexOf(':');
    final action = cut < 0 ? 'select' : picked.substring(0, cut);
    final id = cut < 0 ? picked : picked.substring(cut + 1);
    if (action != 'samples' && id != '${state['profile'] ?? ''}') {
      await command('set_profile', [id]);
    }
    switch (action) {
      case 'example':
        await command('show_format_example');
      case 'samples':
        await command('open_format_samples');
      case 'manage':
        openFormats();
    }
  }

  Widget kioskCard(BuildContext ctx, Map p) {
    final active = p['active'] == true;
    final image = p['image'];
    final scheme = Theme.of(ctx).colorScheme;
    Widget picture;
    if (image is String && image.startsWith('data:image')) {
      picture = Image.memory(
        base64Decode(image.substring(image.indexOf(',') + 1)),
        fit: BoxFit.contain,
      );
    } else {
      picture = Container(
        color: scheme.surfaceContainerHighest,
        alignment: Alignment.center,
        padding: const EdgeInsets.all(12),
        child: const Text(
          "예시 그림 없음\n'서식 예시 확인'을 누르면 그림이 생겨요",
          textAlign: TextAlign.center,
        ),
      );
    }
    final organization = '${p['organization'] ?? ''}';
    return Card(
      key: Key('kioskCard-${p['id']}'),
      clipBehavior: Clip.antiAlias,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color: active ? scheme.primary : scheme.outlineVariant,
          width: active ? 3 : 1,
        ),
      ),
      child: InkWell(
        onTap: () => Navigator.pop(ctx, '${p['id']}'),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Expanded(
              child: Padding(padding: const EdgeInsets.all(6), child: picture),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(8, 2, 8, 10),
              child: Text(
                '${active ? '✔ ' : ''}${p['title'] ?? p['name']}${organization.isNotEmpty ? '\n$organization' : ''}',
                textAlign: TextAlign.center,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
            ),
            // 첫째 줄: 이 서식의 예시 확인 / 둘째 줄: 서식예시 폴더 · 서식관리 (2026-10-23 사용자 요청)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8),
              child: OutlinedButton.icon(
                key: Key('kioskExample-${p['id']}'),
                onPressed: () => Navigator.pop(ctx, 'example:${p['id']}'),
                icon: const Icon(Icons.preview_outlined, size: 16),
                label: const Text('서식예시 확인'),
                style: OutlinedButton.styleFrom(
                  visualDensity: VisualDensity.compact,
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(8, 4, 8, 8),
              child: Row(
                children: [
                  Expanded(
                    child: TextButton(
                      key: Key('kioskSamples-${p['id']}'),
                      onPressed: () => Navigator.pop(ctx, 'samples:${p['id']}'),
                      style: TextButton.styleFrom(
                        visualDensity: VisualDensity.compact,
                      ),
                      child: const FittedBox(child: Text('서식예시 폴더')),
                    ),
                  ),
                  Expanded(
                    child: TextButton(
                      key: Key('kioskManage-${p['id']}'),
                      onPressed: () => Navigator.pop(ctx, 'manage:${p['id']}'),
                      style: TextButton.styleFrom(
                        visualDensity: VisualDensity.compact,
                      ),
                      child: const FittedBox(child: Text('서식관리')),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  void checkBackendDialog([Object? incoming]) {
    final pending = incoming ?? state['pending_dialog'];
    if (pending is Map && pending['kind'] == 'app_close') {
      if (!appClosing && !backendDialogOpen) {
        unawaited(_prepareHostClose(pending));
      }
      return;
    }
    if (backendDialogOpen || pending is! Map || pending['id'] is! String) {
      return;
    }
    backendDialogOpen = true;
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        barrierDismissible: false,
        builder: (_) => BackendDialog(api: widget.api, data: pending),
      );
      backendDialogOpen = false;
      if (mounted) await refresh();
    });
  }

  Future<void> _prepareHostClose(Map request) async {
    setState(() => appClosing = true);
    var accepted = false;
    try {
      await widget.api('acknowledge_close', [request['id']]);
      accepted = !busy && await CloseGuards.prepareAll();
      // An unregistered dialog may hold edits or a pending RPC: fail closed.
      if (!mounted) return;
      final route = ModalRoute.of(context);
      accepted =
          accepted && (route == null || route.isCurrent == true);
      final result = await widget.api('resolve_dialog', [
        request['id'],
        accepted,
      ]);
      accepted = accepted && result is Map && result['accepted'] == true;
    } catch (_) {
      accepted = false;
    }
    if (mounted && !accepted) {
      setState(() => appClosing = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('종료를 취소했습니다. 저장 중이면 완료 후 다시 닫아 주세요.')),
      );
    }
  }


  Future<void> openTools(String name) async {
    if (!mounted) return;
    if (state['doc_hints'] is Map) await setDropTarget('manual_documents');
    if (!mounted) return;
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => DocumentToolsWorkspace(api: widget.api, initial: name),
      ),
    );
    if (state['doc_hints'] is Map) await setDropTarget('documents');
    await refresh();
  }

  Future<void> openProfile(String identifier) async {
    await showDialog<void>(
      context: context,
      builder: (_) => ProfileEditor(api: widget.api, identifier: identifier),
    );
    await refresh();
  }

  Future<void> showStages() async {
    await showDialog<void>(
      context: context,
      builder: (ctx) => ValueListenableBuilder<int>(
        valueListenable: stateVersion,
        builder: (_, _, _) => AlertDialog(
          title: const Text('세부 작업 선택'),
          content: SizedBox(
            width: 620,
            height: 480,
            child: ListView(
              children: [
                for (final stage in state['stages'] as List? ?? [])
                  CheckboxListTile(
                    title: Text('${stage['label']}'),
                    value: stage['on'] == true || stage['enabled'] == true,
                    onChanged: locked
                        ? null
                        : (value) => command('set_stage', [
                            stage['key'],
                            value == true,
                          ]),
                  ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: locked
                  ? null
                  : () => command('stage_config', [
                      'all',
                      {'enabled': true},
                    ]),
              child: const Text('전체 선택'),
            ),
            TextButton(
              onPressed: locked
                  ? null
                  : () => command('stage_config', [
                      'all',
                      {'enabled': false},
                    ]),
              child: const Text('전체 해제'),
            ),
            TextButton(
              onPressed: locked
                  ? null
                  : () => command('stage_config', ['defaults', {}]),
              child: const Text('기본값 복원'),
            ),
            TextButton(
              onPressed: locked
                  ? null
                  : () => command('set_stage_default', [true]),
              child: const Text('현재 구성을 기본값으로'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('닫기'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> openFormats() async {
    // 창이 열려 있는 동안 끌어 놓은 파일은 문서 목록이 아니라 서식 복제로 간다.
    await setDropTarget('format');
    if (!mounted) return;
    setState(() => formatNotice = null);
    await showDialog<void>(
      context: context,
      builder: (ctx) => ValueListenableBuilder<int>(
        valueListenable: stateVersion,
        builder: (ctx, _, _) => formatManager(ctx),
      ),
    );
    await setDropTarget('documents');
    refresh();
  }

  Future<void> renameFormat(Map p) async {
    final result = await showDialog<(String, String)>(
      context: context,
      builder: (ctx) => RenameFormatDialog(
        name: '${p['title'] ?? ''}',
        organization: '${p['organization'] ?? ''}',
      ),
    );
    if (result != null) {
      await command('rename_profile', [p['id'], result.$1, result.$2]);
    }
  }

  Future<void> deleteFormat(Map p) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('서식 삭제'),
        content: Text("'${p['name']}' 서식을 삭제할까요?\n삭제하면 되돌릴 수 없어요."),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('취소'),
          ),
          FilledButton(
            key: const Key('confirmDeleteFormat'),
            style: FilledButton.styleFrom(
              backgroundColor: const Color(0xffdc2626),
            ),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('삭제'),
          ),
        ],
      ),
    );
    if (ok == true) await command('delete_profile', [p['id']]);
  }

  Widget formatRow(Map p) {
    final active = p['active'] == true;
    final builtin = p['builtin'] == true;
    final organization = '${p['organization'] ?? ''}';
    final source = '${p['source'] ?? ''}';
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.fromLTRB(14, 10, 8, 10),
      decoration: BoxDecoration(
        color: active ? _blueSoft : Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: active ? _blue : const Color(0xffe2e8f0)),
      ),
      child: Row(
        children: [
          Icon(
            active ? Icons.check_circle : Icons.description_outlined,
            color: active ? _blue : _faint,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Wrap(
                  spacing: 6,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  children: [
                    Text(
                      '${p['title'] ?? p['name']}',
                      style: const TextStyle(fontWeight: FontWeight.w700),
                    ),
                    if (organization.isNotEmpty)
                      Text(
                        '· $organization',
                        style: const TextStyle(color: _muted, fontSize: 12),
                      ),
                    if (active)
                      const Text(
                        '사용 중',
                        style: TextStyle(
                          color: _blue,
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 2),
                Text(
                  builtin
                      ? '앱에 들어 있는 기본 공문서 서식'
                      : (source.isNotEmpty ? '예시 보고서: $source' : '직접 만든 서식'),
                  style: const TextStyle(fontSize: 12, color: _muted),
                  overflow: TextOverflow.ellipsis,
                ),
                if (p['coverage'] is Map)
                  Text(
                    '서식 요소 ${(p['coverage'] as Map)['total']}개 중 '
                    '${(p['coverage'] as Map)['applied']}개 복제',
                    style: const TextStyle(fontSize: 11, color: _faint),
                  ),
              ],
            ),
          ),
          Wrap(
            spacing: 2,
            children: [
              if (!active)
                TextButton(
                  key: Key('useFormat-${p['id']}'),
                  onPressed: locked
                      ? null
                      : () => command('set_profile', [p['id']]),
                  child: const Text('사용'),
                ),
              TextButton(
                key: Key('editFormat-${p['id']}'),
                onPressed: locked ? null : () => openProfile('${p['id']}'),
                child: const Text('세부 수정'),
              ),
              if (!builtin) ...[
                TextButton(
                  key: Key('renameFormat-${p['id']}'),
                  onPressed: locked ? null : () => renameFormat(p),
                  child: const Text('이름 바꾸기'),
                ),
                TextButton(
                  key: Key('deleteFormat-${p['id']}'),
                  style: TextButton.styleFrom(
                    foregroundColor: const Color(0xffdc2626),
                  ),
                  onPressed: locked ? null : () => deleteFormat(p),
                  child: const Text('삭제'),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }

  Widget formatManager(BuildContext ctx) {
    final analyzing = formatTask['busy'] == true;
    final file = '${formatTask['file'] ?? ''}';
    final status = '${state['status'] ?? ''}';
    return Dialog(
      insetPadding: const EdgeInsets.all(20),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 760, maxHeight: 680),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(24, 20, 24, 16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  const Icon(Icons.style_outlined, color: _blue),
                  const SizedBox(width: 10),
                  const Expanded(
                    child: Text(
                      '서식 관리',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                  IconButton(
                    tooltip: '닫기',
                    onPressed: () => Navigator.pop(ctx),
                    icon: const Icon(Icons.close),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              SegmentedButton<int>(
                segments: const [
                  ButtonSegment(value: 0, label: Text('문단 계층')),
                  ButtonSegment(value: 1, label: Text('제목/개요 서식 표')),
                  ButtonSegment(value: 2, label: Text('기본 데이터 표')),
                ],
                selected: {formatSection},
                onSelectionChanged: (selection) {
                  formatSection = selection.first;
                  stateVersion.value++;
                },
              ),
              const SizedBox(height: 12),
              if (formatSection == 2)
                Flexible(
                  child: TableTemplatePanel(api: widget.api, running: running),
                )
              else ...[
                Text(
                  formatSection == 0
                      ? '프로파일의 세부 수정에서 문단 계층의 글꼴·크기·들여쓰기를 관리합니다.'
                      : '프로파일의 예시 보기와 세부 수정에서 제목·개요 표의 칸별 서식을 관리합니다.',
                ),
                const SizedBox(height: 12),
                Container(
                  key: const Key('formatDropZone'),
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    color: _blueSoft,
                    borderRadius: BorderRadius.circular(18),
                    border: Border.all(
                      color: const Color(0xff93c5fd),
                      width: 1.5,
                    ),
                  ),
                  child: Column(
                    children: [
                      const Icon(
                        Icons.file_copy_outlined,
                        size: 30,
                        color: _blue,
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        '예시 보고서(HWP·HWPX)를 이 창에 끌어다 놓으세요',
                        style: TextStyle(
                          fontWeight: FontWeight.w700,
                          fontSize: 15,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 4),
                      const Text(
                        '제목·개요 표, 항목기호 문장, 표의 글꼴·크기·문단 모양을 분석해 새 서식으로 복제해요. '
                        '분석이 끝나면 이름과 세부값을 확인하는 창이 열리고, 저장하면 바로 이 서식을 써요.',
                        style: TextStyle(
                          fontSize: 12,
                          color: _muted,
                          height: 1.5,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        alignment: WrapAlignment.center,
                        children: [
                          FilledButton.icon(
                            key: const Key('addFormatFile'),
                            onPressed: locked || analyzing
                                ? null
                                : () => command('add_format_file'),
                            icon: const Icon(
                              Icons.folder_open_outlined,
                              size: 18,
                            ),
                            label: const Text('파일에서 고르기'),
                          ),
                          OutlinedButton.icon(
                            key: const Key('writeFormatExample'),
                            onPressed: locked || analyzing
                                ? null
                                : () => command('write_format_example'),
                            icon: const Icon(Icons.edit_note_rounded, size: 18),
                            label: const Text('예시 직접 작성'),
                          ),
                        ],
                      ),
                      if (analyzing) ...[
                        const SizedBox(height: 14),
                        const LinearProgressIndicator(minHeight: 3),
                        const SizedBox(height: 6),
                        Text(
                          '서식 분석 중 · $file',
                          style: const TextStyle(
                            fontSize: 12,
                            color: _blue,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                if (formatNotice != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    formatNotice!,
                    style: const TextStyle(
                      color: Color(0xffdc2626),
                      fontSize: 12,
                    ),
                  ),
                ] else if (!analyzing && status.contains('서식')) ...[
                  const SizedBox(height: 8),
                  Text(
                    status,
                    style: const TextStyle(color: _muted, fontSize: 12),
                  ),
                ],
                const SizedBox(height: 16),
                Text(
                  '서식 목록 (${profiles.length}개)',
                  style: const TextStyle(
                    fontWeight: FontWeight.w700,
                    color: _faint,
                    fontSize: 12,
                  ),
                ),
                const SizedBox(height: 8),
                Flexible(
                  child: ListView(
                    shrinkWrap: true,
                    children: [for (final p in profiles) formatRow(p as Map)],
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  '사용 중인 서식은 한 번에 적용(서식 적용) 작업에서 써요. 기본 서식은 지울 수 없고, 세부 수정하면 새 서식으로 저장돼요.',
                  style: TextStyle(fontSize: 12, color: _faint),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget profilePicker() {
    final ids = profiles.map((p) => '${p['id']}').toList();
    final current = '${state['profile'] ?? ''}';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        InputDecorator(
          decoration: const InputDecoration(
            labelText: '적용할 서식',
            contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 4),
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<String>(
              isExpanded: true,
              value: ids.contains(current) ? current : null,
              hint: const Text('서식을 불러오는 중이에요'),
              items: [
                for (final p in profiles)
                  DropdownMenuItem(
                    value: '${p['id']}',
                    child: Text(
                      '${p['name']}',
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
              ],
              onChanged: locked
                  ? null
                  : (v) {
                      if (v != null && v != current) {
                        command('set_profile', [v]);
                      }
                    },
            ),
          ),
        ),
        const SizedBox(height: 4),
        // 좁은 창(설정)에서도 잘리지 않게 버튼은 폭이 모자라면 다음 줄로 넘긴다.
        Wrap(
          spacing: 4,
          children: [
            Tooltip(
              message: '서식마다 예시 보고서 첫 쪽 그림을 보며 키오스크처럼 골라요',
              child: TextButton(
                key: const Key('formatKioskButton'),
                onPressed: locked ? null : openKiosk,
                child: const Text('썸네일로 선택'),
              ),
            ),
            // 고른 서식을 예시 보고서(제목·개요·중제목·항목기호 문장·표·붙임)에 입혀 한/글로 미리 보여 준다.
            Tooltip(
              message:
                  '고른 서식을 입힌 예시 보고서를 한/글로 보여 줘요(서식마다 처음 한 번 1분쯤 걸려 만들고, 그다음부터는 보관한 예시를 바로 열어요)',
              child: TextButton(
                key: const Key('formatExampleButton'),
                onPressed: locked ? null : () => command('show_format_example'),
                child: const Text('서식 예시 확인'),
              ),
            ),
            // 서식예시 폴더(C:\HWP_AUTODOCFIT\서식예시)를 연다. 예시 파일을 한/글에서 고쳐 저장하면 '한 번에 적용' 때 반영된다.
            Tooltip(
              message:
                  '서식마다 예시 HWPX가 든 폴더를 열어요. 예시 파일을 고쳐 저장하면 다음 한 번에 적용 때 바뀐 서식이 반영돼요',
              child: TextButton(
                key: const Key('formatSamplesButton'),
                onPressed: locked ? null : () => command('open_format_samples'),
                child: const Text('서식예시 폴더'),
              ),
            ),
            Tooltip(
              message: '예시 보고서를 끌어다 놓아 서식 복제 · 이름 바꾸기 · 세부 수정 · 삭제',
              child: TextButton(
                key: const Key('openFormatsButton'),
                onPressed: locked ? null : openFormats,
                child: const Text('서식 관리'),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget stagePanel() {
    final saved = state['default_saved'] == true;
    return panel(
      Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          sectionTitle(
            Icons.checklist_rounded,
            '세부 작업  $stagesOn/${stages.length}',
            stagesChanged
                ? '처음 기본값과 다르게 조정했어요.${saved ? ' 다음 실행에도 이 구성을 써요.' : ''}'
                : '모든 세부 작업을 표시해요. 끄면 그 단계는 건너뛰어요.',
          ),
          const SizedBox(height: 12),
          const Divider(),
          const SizedBox(height: 8),
          StageBoard(
            stages: stages,
            locked: locked,
            onToggle: (key, on) => command('set_stage', [key, on]),
          ),
          const Divider(),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            value: saved,
            onChanged: locked ? null : (v) => command('set_stage_default', [v]),
            title: const Text('다음 실행에도 이 구성 사용'),
            subtitle: Text(
              saved ? '바꾸는 즉시 저장돼요.' : '끄면 이번 실행에만 적용하고, 다음에는 처음 기본값으로 시작해요.',
              style: const TextStyle(fontSize: 12, color: _muted),
            ),
          ),
          Wrap(
            spacing: 8,
            children: [
              TextButton.icon(
                onPressed: locked || !stagesChanged
                    ? null
                    : () => command('reset_stages'),
                icon: const Icon(Icons.restart_alt, size: 18),
                label: const Text('처음 기본값으로'),
              ),
              TextButton.icon(
                onPressed: locked ? null : showStages,
                icon: const Icon(Icons.tune, size: 18),
                label: const Text('단계별 수치 조정'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget rangePanel() {
    final problem = rangeError;
    return panel(
      Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Wrap(
            spacing: 16,
            runSpacing: 12,
            crossAxisAlignment: WrapCrossAlignment.center,
            alignment: WrapAlignment.spaceBetween,
            children: [
              ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 420),
                child: sectionTitle(
                  Icons.auto_stories_outlined,
                  '작업할 쪽 범위',
                  '보통은 문서 전체를 정리해요. 일부만 고칠 때 쪽을 지정하세요.',
                ),
              ),
              SegmentedButton<bool>(
                segments: const [
                  ButtonSegment(value: false, label: Text('문서 전체')),
                  ButtonSegment(value: true, label: Text('쪽 지정')),
                ],
                selected: {rangeOn},
                onSelectionChanged: locked
                    ? null
                    : (v) {
                        setState(() => rangeOn = v.first);
                        command('set_range', [
                          rangeOn,
                          rangeStart.text.trim(),
                          rangeEnd.text.trim(),
                        ]);
                      },
              ),
            ],
          ),
          if (rangeOn) ...[
            const SizedBox(height: 18),
            Row(
              children: [
                Expanded(child: pageField(rangeStart, '시작 쪽')),
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 12),
                  child: Text('~'),
                ),
                Expanded(child: pageField(rangeEnd, '끝 쪽')),
              ],
            ),
            if (problem != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(
                  problem,
                  style: const TextStyle(
                    color: Color(0xffdc2626),
                    fontSize: 13,
                  ),
                ),
              ),
          ],
        ],
      ),
    );
  }

  Widget pageField(TextEditingController controller, String label) => TextField(
    controller: controller,
    enabled: !locked,
    keyboardType: TextInputType.number,
    inputFormatters: [FilteringTextInputFormatter.digitsOnly],
    decoration: InputDecoration(labelText: label, suffixText: '쪽'),
    onChanged: (_) => setState(() {}),
    onSubmitted: (_) => primaryShortcut(),
  );

  // ---- 3. 진행 과정 -------------------------------------------------

  Widget progress() {
    // 기능별 맞춤 진행 화면(알파). 예전 엔진처럼 live 값이 없으면 아래 단계 목록 화면을 그대로 쓴다.
    final live = state['live'];
    if (live is Map && live.isNotEmpty) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          heading(
            running || live['finished'] == true
                ? '${live['title']}'
                : '진행 상황을 확인하세요',
            '${live['message'] ?? ''}',
          ),
          panel(LiveProgress(live: live, onShowLog: showLog)),
        ],
      );
    }
    final guide = state['guide'] as Map? ?? {};
    final steps = guide['steps'] as List? ?? [];
    final current = guide['current'] as int?;
    final done = (guide['done'] as List? ?? []).cast<int>();
    final finished = !running && results.isNotEmpty;
    final ratio = steps.isEmpty
        ? 0.0
        : finished
        ? 1.0
        : done.length / steps.length;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        heading(
          running
              ? '문서를 정리하고 있어요'
              : finished
              ? '정리가 끝났어요'
              : '진행 상황을 확인하세요',
          '${guide['message'] ?? '작업을 시작하면 지금 하는 일을 여기에서 알려 드려요.'}',
        ),
        panel(
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (steps.isNotEmpty) ...[
                Row(
                  children: [
                    Expanded(
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: LinearProgressIndicator(
                          minHeight: 8,
                          value: running && ratio == 0 ? null : ratio,
                          backgroundColor: const Color(0xffedf2f7),
                        ),
                      ),
                    ),
                    const SizedBox(width: 14),
                    Text(
                      '${finished ? steps.length : done.length}/${steps.length} 단계',
                      style: const TextStyle(fontSize: 12, color: _muted),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
              ],
              for (var i = 0; i < steps.length; i++)
                guideStep(
                  i,
                  '${steps[i]}',
                  active: i == current,
                  finished:
                      done.contains(i) || (current != null && i < current),
                ),
              const SizedBox(height: 12),
              const Text(
                '선택한 세부 작업에 따라 일부 단계는 건너뛸 수 있어요.',
                style: TextStyle(fontSize: 12, color: _faint),
              ),
              if (state['status'] != null && '${state['status']}'.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Text(
                    '${state['status']}',
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 12, color: _muted),
                  ),
                ),
              const SizedBox(height: 16),
              TextButton.icon(
                onPressed: showLog,
                icon: const Icon(Icons.receipt_long_outlined),
                label: const Text('상세 작업 로그'),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget guideStep(
    int index,
    String text, {
    required bool active,
    required bool finished,
  }) => Container(
    margin: const EdgeInsets.only(bottom: 8),
    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
    decoration: BoxDecoration(
      color: active ? _blueSoft : Colors.transparent,
      borderRadius: BorderRadius.circular(14),
    ),
    child: Row(
      children: [
        CircleAvatar(
          radius: 14,
          backgroundColor: active
              ? _blue
              : finished
              ? const Color(0xffdff3ee)
              : const Color(0xffedf2f7),
          child: active && running
              ? const SizedBox(
                  width: 14,
                  height: 14,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Colors.white,
                  ),
                )
              : finished
              ? const Icon(Icons.check, size: 16, color: _mint)
              : Text(
                  '${index + 1}',
                  style: TextStyle(
                    fontSize: 12,
                    color: active ? Colors.white : _muted,
                  ),
                ),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Text(
            text,
            style: TextStyle(
              height: 1.5,
              fontWeight: active ? FontWeight.w700 : FontWeight.w500,
              color: active
                  ? _blueDeep
                  : finished
                  ? const Color(0xff475569)
                  : const Color(0xff94a3b8),
            ),
          ),
        ),
      ],
    ),
  );

  // ---- 4. 결과 확인 -------------------------------------------------

  Widget _buildCatImage(String catImage) {
    try {
      final commaIndex = catImage.indexOf(',');
      final base64Str =
          commaIndex >= 0 ? catImage.substring(commaIndex + 1) : catImage;
      final bytes = base64Decode(base64Str);
      return Image.memory(
        bytes,
        key: const Key('savingsCatImage'),
        height: 80,
        fit: BoxFit.contain,
      );
    } catch (_) {
      return const SizedBox.shrink();
    }
  }

  Widget _savingsCard() {
    final msg = completion['savings_message']?.toString() ?? '';
    if (msg.isEmpty) return const SizedBox.shrink();
    final catImage = completion['cat_image']?.toString() ?? '';
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: panel(
        Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (catImage.isNotEmpty) _buildCatImage(catImage),
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: Text(
                  msg,
                  key: const Key('savingsMessageText'),
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: Color(0xff111827),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget outcome() => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      heading('작업 결과를 확인하세요', '${state['status'] ?? '작업이 끝나면 저장된 문서가 표시됩니다.'}'),
      _savingsCard(),
      if (completion.isNotEmpty ||
          formatReview.isNotEmpty ||
          failures.isNotEmpty)
        panel(
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              sectionTitle(
                Icons.fact_check_outlined,
                '작업 메시지와 검수 결과',
                '완료 안내와 확인이 필요한 내용을 이 화면에서 확인할 수 있어요.',
              ),
              if ('${completion['message'] ?? ''}'.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 14),
                  child: Text(
                    '${completion['message']}',
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                ),
              for (final line in completion['details'] as List? ?? const [])
                Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Text('• $line', style: const TextStyle(color: _muted)),
                ),
              if (completion['report'] is String &&
                  '${completion['report']}'.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Text(
                    '검수 보고서: ${completion['report']}',
                    style: const TextStyle(color: _muted),
                  ),
                ),
              if (failures.isNotEmpty) ...[
                const Padding(
                  padding: EdgeInsets.only(top: 14),
                  child: Text(
                    '실패한 문서',
                    style: TextStyle(fontWeight: FontWeight.w700),
                  ),
                ),
                for (final entry in failures.entries)
                  Padding(
                    padding: const EdgeInsets.only(top: 5),
                    child: Text(
                      '• ${entry.key}: ${entry.value}',
                      style: const TextStyle(color: Color(0xffb42318)),
                    ),
                  ),
              ],
              if (formatReview.isNotEmpty) ...[
                const Padding(
                  padding: EdgeInsets.only(top: 14),
                  child: Text(
                    '서식 통일 저장 후 검수',
                    style: TextStyle(fontWeight: FontWeight.w700),
                  ),
                ),
                Text(
                  '${_formatReviewStatus(formatReview['status'])} · 검사 문장 ${formatReview['checked'] ?? 0}개 · 불일치 ${(formatReview['issues'] as List? ?? const []).length}개 · 판정 보류 ${(formatReview['not_checkable'] as List? ?? const []).length}개',
                  style: const TextStyle(color: _muted),
                ),
                for (final item in formatReview['issues'] as List? ?? const [])
                  Text(
                    '• ${item['text'] ?? item}',
                    style: const TextStyle(color: Color(0xffb42318)),
                  ),
                for (final item
                    in formatReview['not_checkable'] as List? ?? const [])
                  Text(
                    '• 판정 보류: ${item['marker'] ?? ''} / ${item['role'] ?? ''} · ${(item['fields'] as List? ?? const []).join(', ')}',
                    style: const TextStyle(color: _muted),
                  ),
                for (final item
                    in formatReview['unresolved'] as List? ?? const [])
                  Text(
                    '• 대표값 미확정: ${item['text'] ?? ''} · ${(item['fields'] as List? ?? const []).join(', ')}',
                    style: const TextStyle(color: Color(0xffb42318)),
                  ),
                if ('${formatReview['error'] ?? ''}'.isNotEmpty)
                  Text(
                    '검수 오류: ${formatReview['error']}',
                    style: const TextStyle(color: Color(0xffb42318)),
                  ),
              ],
            ],
          ),
        ),
      if (completion.isNotEmpty ||
          formatReview.isNotEmpty ||
          failures.isNotEmpty)
        const SizedBox(height: 16),
      panel(
        Column(
          children: [
            Icon(
              results.isEmpty ? Icons.inbox_outlined : Icons.task_alt_rounded,
              size: 56,
              color: _blue,
            ),
            const SizedBox(height: 18),
            Text(
              results.isEmpty
                  ? '아직 저장된 결과가 없어요.'
                  : '저장된 결과 ${results.length}개 · 원본은 그대로 있어요.',
            ),
            const SizedBox(height: 8),
            for (var i = 0; i < results.length; i++)
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.description_outlined),
                title: Text(
                  '${results[i]['name'] ?? ''}',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                subtitle: Text(
                  [
                    if ('${results[i]['source'] ?? ''}'.isNotEmpty)
                      '원본: ${results[i]['source']}',
                    if (results[i]['pages'] != null) '${results[i]['pages']}쪽',
                  ].join(' · '),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 12, color: _faint),
                ),
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    IconButton(
                      tooltip: '결과 파일 열기',
                      onPressed: busy
                          ? null
                          : () => command('open_result', [i]),
                      icon: const Icon(Icons.open_in_new),
                    ),
                    IconButton(
                      tooltip: '폴더에서 보기',
                      onPressed: busy
                          ? null
                          : () => command('show_result', [i]),
                      icon: const Icon(Icons.folder_open_outlined),
                    ),
                    IconButton(
                      key: Key('compareItem-$i'),
                      tooltip: '원본·결과 비교',
                      onPressed: busy
                          ? null
                          : () => openDiff(i),
                      icon: const Icon(Icons.compare_arrows_rounded),
                    ),
                  ],
                ),
              ),
            const SizedBox(height: 20),
            FilledButton.icon(
              onPressed: results.isEmpty || busy
                  ? null
                  : () => command('open_results'),
              icon: const Icon(Icons.open_in_new),
              label: Text(results.length > 1 ? '결과 모두 열기' : '결과 파일 열기'),
            ),
            const SizedBox(height: 8),
            if (compareError != null) ...[
              Container(
                key: const Key('compareErrorMessage'),
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                decoration: BoxDecoration(
                  color: const Color(0xfffee2e2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.error_outline, size: 18, color: Color(0xffdc2626)),
                    const SizedBox(width: 8),
                    Flexible(
                      child: Text(
                        compareError!,
                        style: const TextStyle(fontSize: 13, color: Color(0xffdc2626)),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 8),
            ],
            OutlinedButton.icon(
              key: const Key('compareResultButton'),
              onPressed: results.isEmpty || busy
                  ? null
                  : () => openDiff(0),
              icon: const Icon(Icons.compare_arrows_rounded),
              label: const Text('원본·결과 비교'),
            ),
          ],
        ),
      ),
    ],
  );

  String? compareError;

  Future<void> openDiff([int index = 0]) async {
    setState(() => compareError = null);
    try {
      final res = await widget.api('open_diff', [index]);
      if (!mounted) return;
      if (res is! Map || res['ok'] != true) {
        final message = res is Map ? res['error'] : null;
        final err = '${message ?? '비교 창을 열지 못했습니다.'}';
        setState(() => compareError = err);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(err),
              backgroundColor: const Color(0xffdc2626),
            ),
          );
        }
      }
    } catch (e) {
      if (!mounted) return;
      final err = '비교 창을 여는 중 오류가 발생했습니다: $e';
      setState(() => compareError = err);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(err),
            backgroundColor: const Color(0xffdc2626),
          ),
        );
      }
    }
  }

  Map get completion => state['completion'] as Map? ?? const {};
  Map get formatReview => state['format_review'] as Map? ?? const {};
  Map get failures => state['failures'] as Map? ?? const {};

  String _formatReviewStatus(Object? status) => switch (status) {
    'passed' => '검수 통과',
    'failed' => '불일치 남음',
    'incomplete' => '일부 판정 보류',
    'error' => '검수 오류',
    'not_applicable' => '검사할 문장 없음',
    _ => '${status ?? '결과 확인'}',
  };

  // ---- 하단 실행 막대 ------------------------------------------------

  Widget bottomBar() => Container(
    color: Colors.white,
    padding: const EdgeInsets.fromLTRB(20, 12, 20, 16),
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Row(
          children: [
            if (tab > 0)
              TextButton(
                onPressed: () => setState(() => tab--),
                child: const Text('이전'),
              ),
            // 시작 전에 무엇을 어떻게 정리할지 한 줄로 다시 보여 준다.
            Expanded(
              child: tab == 1 && files.isNotEmpty
                  ? Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      child: Text(
                        mode == 'file_format'
                            ? '${files.length}개 문서 · $modeTitle · ${conversionTarget.toUpperCase()}로 변환'
                            : '${files.length}개 문서 · $modeTitle · $rangeLabel · 세부 작업 $stagesOn/${stages.length}',
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        textAlign: TextAlign.right,
                        style: const TextStyle(fontSize: 13, color: _muted),
                      ),
                    )
                  : const SizedBox(),
            ),
            if (running)
              TextButton(
                onPressed: busy ? null : () => command('stop'),
                child: const Text('작업 중단'),
              ),
            if (tab == 0)
              FilledButton(
                onPressed: locked || files.isEmpty
                    ? null
                    : () => setState(() => tab = 1),
                child: const Text('작업 방식 선택'),
              ),
            if (tab == 1)
              FilledButton.icon(
                onPressed: canStart ? startJob : null,
                icon: const Icon(Icons.play_arrow_rounded),
                label: Text(mode == 'file_format' ? '변환 시작' : '정리 시작'),
              ),
            if (tab == 2)
              FilledButton(
                onPressed: () => setState(() => tab = 3),
                child: const Text('결과 확인'),
              ),
            if (tab == 3)
              FilledButton(
                onPressed: locked
                    ? null
                    : () async {
                        await command('next_job');
                        if (mounted) setState(() { compareError = null; tab = 0; });
                      },
                child: const Text('새 작업 시작'),
              ),
          ],
        ),
        const SizedBox(height: 8),
        Text(
          tab < 2
              ? '원본을 보존하고 결과를 별도 파일로 저장해요  ·  Ctrl+Enter로 다음 단계'
              : '원본을 보존하고 결과를 별도 파일로 저장해요  ·  ${state['version'] ?? '알파'}',
          textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 11, color: _muted),
        ),
      ],
    ),
  );

  // ---- 설정 서랍 ----------------------------------------------------

  Future<void> showLog() async {
    String logText;
    try {
      final value = await widget.api('get_log', const []);
      logText = value is String ? value : '';
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('작업 로그를 불러오지 못했어요: $e')));
      }
      return;
    }
    if (!mounted) return;
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (dialogContext, setDialogState) => AlertDialog(
          title: const Row(
            children: [
              Icon(Icons.receipt_long_outlined, color: _blue),
              SizedBox(width: 10),
              Text('작업 로그'),
            ],
          ),
          content: SizedBox(
            width: 760,
            height: 420,
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: const Color(0xfff8fafc),
                border: Border.all(color: _line),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Scrollbar(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(14),
                  child: SelectableText(
                    logText.isEmpty ? '아직 기록된 내용이 없어요.' : logText,
                    key: const Key('flutterLogContents'),
                    style: const TextStyle(
                      fontFamily: 'Consolas',
                      fontSize: 12,
                      height: 1.5,
                    ),
                  ),
                ),
              ),
            ),
          ),
          actions: [
            TextButton.icon(
              key: const Key('copyLogButton'),
              onPressed: logText.isEmpty
                  ? null
                  : () async {
                      await Clipboard.setData(ClipboardData(text: logText));
                      if (mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('작업 로그를 복사했어요.')),
                        );
                      }
                    },
              icon: const Icon(Icons.copy_outlined),
              label: const Text('복사'),
            ),
            TextButton.icon(
              key: const Key('refreshLogButton'),
              onPressed: () async {
                try {
                  final value = await widget.api('get_log', const []);
                  if (dialogContext.mounted) {
                    setDialogState(
                      () => logText = value is String ? value : '',
                    );
                  }
                } catch (_) {
                  if (dialogContext.mounted) {
                    ScaffoldMessenger.of(dialogContext).showSnackBar(
                      const SnackBar(content: Text('로그를 새로 불러오지 못했어요.')),
                    );
                  }
                }
              },
              icon: const Icon(Icons.refresh),
              label: const Text('새로 고침'),
            ),
            TextButton.icon(
              key: const Key('clearLogButton'),
              onPressed: running
                  ? null
                  : () async {
                      try {
                        final value = await widget.api('clear_log', const []);
                        if (dialogContext.mounted) {
                          setDialogState(
                            () => logText = value is String ? value : '',
                          );
                        }
                      } catch (_) {
                        if (dialogContext.mounted) {
                          ScaffoldMessenger.of(dialogContext).showSnackBar(
                            const SnackBar(content: Text('로그를 지우지 못했어요.')),
                          );
                        }
                      }
                    },
              icon: const Icon(Icons.delete_outline),
              label: const Text('지우기'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: const Text('닫기'),
            ),
          ],
        ),
      ),
    );
  }

  Widget settingsDrawer() => Drawer(
    width: 400,
    backgroundColor: Colors.white,
    child: SafeArea(
      child: ListView(
        padding: const EdgeInsets.fromLTRB(24, 20, 24, 24),
        children: [
          Row(
            children: [
              const Expanded(
                child: Text(
                  '설정',
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
                ),
              ),
              IconButton(
                tooltip: '닫기',
                onPressed: () => scaffoldKey.currentState?.closeEndDrawer(),
                icon: const Icon(Icons.close),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            running ? '작업 중에는 설정을 바꿀 수 없어요.' : '자주 바꾸는 설정만 모았어요. 바꾸면 바로 저장돼요.',
            style: const TextStyle(color: _muted, fontSize: 13),
          ),
          settingsLabel('서식 기준'),
          profilePicker(),
          const SizedBox(height: 6),
          const Text(
            '서식 적용·한 번에 적용 작업에서 사용해요.',
            style: TextStyle(fontSize: 12, color: _faint),
          ),
          settingsLabel('작업 뒤 처리'),
          optionSwitch(
            'autoclose',
            '작업이 끝나면 한/글 문서 창 닫기',
            '여러 문서를 처리할 때 창이 쌓이지 않아요.',
          ),
          optionSwitch(
            'verify',
            '저장 뒤 결과 검수',
            '본문·표·이미지가 원본과 같은지 다시 확인해요. 시간이 조금 더 걸려요.',
          ),
          settingsLabel('기록 파일'),
          optionSwitch(
            'log_file',
            '작업로그 파일 만들기',
            '다음 작업부터 첫 문서와 같은 폴더에 처리 기록을 저장해요.',
          ),
          optionSwitch(
            'integrity_report_file',
            '무결성검사 JSON 파일 만들기',
            '저장 뒤 결과 검수를 켰을 때 검사 세부 결과를 JSON으로 저장해요.',
          ),
          optionSwitch(
            'final_review_file',
            '최종검수 JSON 파일 만들기',
            '작업 목표 기준의 최종 점수와 판정을 파일로 저장해요.',
          ),
          settingsLabel('완료 화면'),
          optionSwitch(
            'unify_result_window',
            '서식 통일 결과 창 표시',
            '끄더라도 결과는 작업 기록과 최종 검수에 남아요.',
          ),
          settingsLabel('프로그램'),
          optionSwitch(
            'check_updates',
            '시작할 때 새 버전 확인',
            '시작할 때와 몇 시간마다 새 버전을 확인해요.',
          ),
          UpdatePanel(state: state, command: command),
          optionSwitch(
            'always_on_top',
            '앱 창을 항상 위에 표시',
            '다른 창을 사용해도 앱을 앞에 유지해요.',
          ),
          optionSwitch(
            'developer_mode',
            '개발자 모드',
            '자세한 문서 처리 완료 안내를 표시해요.',
          ),
          settingsLabel('더 보기'),
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.tune),
            title: const Text('전체 설정 열기'),
            subtitle: const Text(
              '글꼴·항목기호·자간 한도 등 모든 값을 바꿔요.',
              style: TextStyle(fontSize: 12, color: _muted),
            ),
            trailing: const Icon(Icons.open_in_new, size: 18),
            onTap: locked
                ? null
                : () async {
                    final saved = await showDialog<bool>(
                      context: context,
                      barrierDismissible: false,
                      builder: (_) => SettingsDialog(api: widget.api),
                    );
                    if (saved == true) await refresh();
                  },
          ),
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.text_fields_rounded),
            title: const Text('준말 등록·관리'),
            subtitle: const Text('준말과 본말을 검색하고 등록·수정·삭제해요.'),
            onTap: locked
                ? null
                : () => showDialog<void>(
                    context: context,
                    builder: (_) => AbbreviationManager(api: widget.api),
                  ),
          ),
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.help_outline_rounded),
            title: const Text('사용 방법과 단축키'),
            onTap: showHelp,
          ),
        ],
      ),
    ),
  );

  Widget settingsLabel(String text) => Padding(
    padding: const EdgeInsets.only(top: 28, bottom: 10),
    child: Text(
      text,
      style: const TextStyle(
        fontSize: 12,
        fontWeight: FontWeight.w700,
        color: _faint,
      ),
    ),
  );

  Widget optionSwitch(String name, String title, String subtitle) =>
      SwitchListTile(
        contentPadding: EdgeInsets.zero,
        value: quickOptions[name] == true,
        onChanged: locked || !quickOptions.containsKey(name)
            ? null
            : (v) => command('set_option', [name, v]),
        title: Text(title),
        subtitle: Text(
          subtitle,
          style: const TextStyle(fontSize: 12, color: _muted),
        ),
      );

  void showHelp() => showDialog<void>(
    context: context,
    builder: (ctx) => AlertDialog(
      title: const Text('사용 방법'),
      content: const SizedBox(
        width: 420,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('1. 문서 선택에서 HWP·HWPX 문서나 폴더를 넣어요. 창에 끌어다 놓아도 돼요.'),
            SizedBox(height: 8),
            Text('2. 작업 방식에서 작업을 고르고, 필요하면 세부 작업과 쪽 범위를 조정해요.'),
            SizedBox(height: 8),
            Text('3. 정리 시작을 누르면 진행 과정이 보이고, 끝나면 결과 확인으로 넘어가요.'),
            SizedBox(height: 16),
            Text(
              '원본 문서는 바꾸지 않아요. 결과는 원본 폴더에 새 파일로 저장돼요.',
              style: TextStyle(color: _mint, fontWeight: FontWeight.w600),
            ),
            SizedBox(height: 16),
            Text('단축키', style: TextStyle(fontWeight: FontWeight.w700)),
            SizedBox(height: 6),
            Text('Ctrl+O  문서 추가\nCtrl+Enter  다음 단계 · 정리 시작\nF1  사용 방법'),
          ],
        ),
      ),
      actions: [
        FilledButton(
          onPressed: () => Navigator.pop(ctx),
          child: const Text('확인'),
        ),
      ],
    ),
  );
}

/// 서식 이름·기관 이름을 고치는 창. 입력 상자는 창이 완전히 닫힐 때 정리한다.
class RenameFormatDialog extends StatefulWidget {
  const RenameFormatDialog({
    super.key,
    required this.name,
    required this.organization,
  });
  final String name, organization;
  @override
  State<RenameFormatDialog> createState() => _RenameFormatDialogState();
}

class _RenameFormatDialogState extends State<RenameFormatDialog> {
  late final name = TextEditingController(text: widget.name);
  late final organization = TextEditingController(text: widget.organization);

  @override
  void dispose() {
    name.dispose();
    organization.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('서식 이름 바꾸기'),
    content: SizedBox(
      width: 380,
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              key: const Key('formatNameField'),
              controller: name,
              autofocus: true,
              decoration: const InputDecoration(labelText: '서식 이름'),
            ),
            const SizedBox(height: 12),
            TextField(
              key: const Key('formatOrganizationField'),
              controller: organization,
              decoration: const InputDecoration(
                labelText: '기관 이름 (선택)',
                helperText: '비워 두면 기관 없이 보여요.',
              ),
            ),
          ],
        ),
      ),
    ),
    actions: [
      TextButton(
        onPressed: () => Navigator.pop(context),
        child: const Text('취소'),
      ),
      FilledButton(
        onPressed: () => Navigator.pop(context, (
          name.text.trim(),
          organization.text.trim(),
        )),
        child: const Text('저장'),
      ),
    ],
  );
}

class DocumentArtwork extends StatelessWidget {
  const DocumentArtwork({super.key});
  @override
  Widget build(BuildContext context) => ExcludeSemantics(
    child: Stack(
      alignment: Alignment.center,
      children: [
        Container(
          width: 185,
          height: 185,
          decoration: const BoxDecoration(
            shape: BoxShape.circle,
            color: Color(0x55ffffff),
          ),
        ),
        Transform.rotate(
          angle: -.14,
          child: Container(
            width: 121,
            height: 158,
            decoration: BoxDecoration(
              color: const Color(0xffb9cdef),
              borderRadius: BorderRadius.circular(18),
            ),
          ),
        ),
        Transform.translate(
          offset: const Offset(13, -5),
          child: Transform.rotate(
            angle: .08,
            child: Container(
              width: 120,
              height: 158,
              padding: const EdgeInsets.all(19),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(18),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x152b527e),
                    blurRadius: 24,
                    offset: Offset(0, 12),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 28,
                    height: 28,
                    decoration: BoxDecoration(
                      color: const Color(0xffe7efff),
                      borderRadius: BorderRadius.circular(9),
                    ),
                    child: const Icon(
                      Icons.format_align_left_rounded,
                      color: _blue,
                      size: 17,
                    ),
                  ),
                  const SizedBox(height: 20),
                  for (final w in [78.0, 65.0, 78.0, 43.0])
                    Padding(
                      padding: const EdgeInsets.only(bottom: 9),
                      child: Container(
                        width: w,
                        height: 5,
                        decoration: BoxDecoration(
                          color: const Color(0xffe8edf5),
                          borderRadius: BorderRadius.circular(3),
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ),
        Positioned(
          right: 17,
          bottom: 18,
          child: Container(
            width: 49,
            height: 49,
            decoration: BoxDecoration(
              color: _mint,
              borderRadius: BorderRadius.circular(17),
              border: Border.all(color: const Color(0xffecf6f2), width: 4),
            ),
            child: const Icon(
              Icons.check_rounded,
              color: Colors.white,
              size: 28,
            ),
          ),
        ),
      ],
    ),
  );
}
