import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'bridge.dart' as bridge;

typedef ApiCall = Future<Object?> Function(String, List<Object?>);

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

class DocFitApp extends StatelessWidget {
  const DocFitApp({super.key, this.api = bridge.callApi});
  final ApiCall api;
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: '한글편집 후처리 도구',
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
    home: Workspace(api: api),
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
  bool busy = false, polling = false, wasRunning = false, stagesOpen = false;
  String? error;
  Timer? timer;
  final scaffoldKey = GlobalKey<ScaffoldState>();
  // 쪽 범위는 화면에서 바로 입력하고, 시작할 때 앱에 넘긴다.
  final rangeStart = TextEditingController(text: '1');
  final rangeEnd = TextEditingController(text: '1');
  bool rangeOn = false, rangeLoaded = false;

  static const tabs = ['문서 선택', '작업 방식', '진행 과정', '결과 확인'];
  // (내부 모드, 이름, 설명, 아이콘, 결과 파일 접미사). 카드는 세 장이며, 서식 적용(format)은
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
  ];

  bool get running => state['running'] == true;
  bool get locked => busy || running || state.isEmpty || error != null;
  List get files => state['files'] as List? ?? [];
  List get results => state['results'] as List? ?? [];
  List get stages => state['stages'] as List? ?? [];
  List get profiles => state['profiles'] as List? ?? [];
  Map get quickOptions => state['options'] as Map? ?? {};
  String get mode => state['mode'] as String? ?? 'spacing';
  String get cardMode => mode == 'format' ? 'all' : mode;
  bool get includeSpacing => state['include_spacing'] != false;
  // '자간 정리' 카드의 '기존 자간 초기화'(세부 작업 01과 같은 값).
  bool get resetSpacing => state['reset_spacing'] != false;
  bool get tableSpacing => state['table_spacing'] != false;
  String get modeTitle => mode == 'format'
      ? '한 번에 적용(자간 조정 제외)'
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

  String get rangeLabel => rangeOn
      ? '${rangeStart.text.trim()}~${rangeEnd.text.trim()}쪽'
      : '문서 전체';
  bool get canStart => !locked && files.isNotEmpty && rangeError == null;

  @override
  void initState() {
    super.initState();
    refresh();
    timer = Timer.periodic(const Duration(seconds: 1), (_) => refresh());
  }

  @override
  void dispose() {
    timer?.cancel();
    rangeStart.dispose();
    rangeEnd.dispose();
    super.dispose();
  }

  void apply(Map next) {
    state = Map<String, dynamic>.from(next);
    final range = state['range'] as Map? ?? {};
    if (!rangeLoaded && range.isNotEmpty) {
      rangeLoaded = true;
      rangeOn = range['enabled'] == true;
      rangeStart.text = '${range['start'] ?? 1}';
      rangeEnd.text = '${range['end'] ?? 1}';
    }
    // 작업이 끝나면 진행 화면에서 결과 화면으로 넘어간다.
    if (wasRunning && !running && tab == 2 && results.isNotEmpty) tab = 3;
    wasRunning = running;
  }

  Future<void> refresh() async {
    if (polling) return;
    polling = true;
    try {
      final next = await widget.api('get_state', []);
      if (mounted && next is Map) {
        setState(() {
          apply(next);
          error = null;
        });
      }
    } catch (_) {
      if (mounted) setState(() => error = '앱과 연결하지 못했어요. 잠시 후 다시 확인합니다.');
    } finally {
      polling = false;
    }
  }

  Future<void> command(String method, [List<Object?> args = const []]) async {
    if (busy) return;
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final response = await widget.api(method, args);
      if (mounted && response is Map) setState(() => apply(response));
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('작업을 실행하지 못했어요: $e')));
      }
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> startJob() async {
    if (!canStart) return;
    await command('start', [
      mode,
      rangeOn,
      rangeStart.text.trim(),
      rangeEnd.text.trim(),
    ]);
    if (mounted && running) setState(() => tab = 2);
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
          style: Theme.of(context).textTheme.headlineMedium
              ?.copyWith(fontWeight: FontWeight.w700),
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
  Widget build(BuildContext context) => CallbackShortcuts(
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
                              onPressed: refresh,
                              tooltip: '다시 연결',
                              icon: const Icon(Icons.refresh),
                            ),
                          ),
                        ),
                      if (layout.maxWidth < 1000) topTabs(),
                      Expanded(
                        child: SingleChildScrollView(
                          padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
                          child: Center(
                            child: ConstrainedBox(
                              constraints: const BoxConstraints(maxWidth: 960),
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
  );

  PreferredSizeWidget appBar() => AppBar(
    backgroundColor: Colors.white,
    surfaceTintColor: Colors.transparent,
    toolbarHeight: 72,
    automaticallyImplyLeading: false,
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
        const SizedBox(width: 12),
        const Flexible(
          child: Text(
            '한글편집 후처리 도구',
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w800,
              letterSpacing: -.8,
            ),
          ),
        ),
      ],
    ),
    actions: [
      IconButton(
        tooltip: '사용 방법 (F1)',
        onPressed: showHelp,
        icon: const Icon(Icons.help_outline_rounded),
      ),
      IconButton(
        tooltip: '작업 로그',
        onPressed: busy ? null : () => command('open_log'),
        icon: const Icon(Icons.receipt_long_outlined),
      ),
      PopupMenuButton<String>(
        tooltip: '문서 도구',
        enabled: !locked,
        icon: const Icon(Icons.handyman_outlined),
        onSelected: (v) => command('run_tool', [v]),
        itemBuilder: (_) => const [
          PopupMenuItem(value: 'review', child: Text('문서 검토')),
          PopupMenuItem(value: 'proofread', child: Text('공공언어 교정')),
          PopupMenuItem(value: 'outline', child: Text('문서 구조 편집')),
          PopupMenuItem(value: 'writing', child: Text('작성 도우미')),
          PopupMenuItem(value: 'markdown', child: Text('Markdown 내보내기')),
          PopupMenuItem(value: 'advanced', child: Text('고급 문서 도구')),
        ],
      ),
      IconButton(
        tooltip: '설정',
        onPressed: () => scaffoldKey.currentState?.openEndDrawer(),
        icon: const Icon(Icons.settings_outlined),
      ),
      const SizedBox(width: 12),
    ],
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
        onPressed: locked ? null : () => command('text_input'),
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
                  '세 단계면 끝나요',
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
          final columns = box.maxWidth >= 900
              ? 3
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
  );

  Widget modeCard(
    (String, String, String, IconData, String) m,
  ) {
    final selected = cardMode == m.$1;
    final isAll = m.$1 == 'all';
    final suffix = isAll && !includeSpacing ? '서식적용' : m.$5;
    return Material(
      color: selected ? const Color(0xffeaf1ff) : Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: BorderSide(
          color: selected ? _blue : _line,
          width: selected ? 2 : 1,
        ),
      ),
      clipBehavior: Clip.antiAlias,
      child: Semantics(
        selected: selected,
        button: true,
        child: InkWell(
          onTap: locked ? null : () => command('set_mode', [m.$1]),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(m.$4, color: _blue),
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
                      color: selected ? _blue : const Color(0xffcbd5e1),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Text(m.$3, style: const TextStyle(height: 1.6)),
                if (m.$1 == 'spacing') ...[
                  const SizedBox(height: 8),
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
                        onChanged: locked
                            ? null
                            : (on) => command('set_reset_spacing', [on]),
                      ),
                    ],
                  ),
                  if (!resetSpacing)
                    const Text(
                      '문서에 있던 자간은 그대로 두고 그 위에서 정리해요.',
                      style: TextStyle(fontSize: 12, color: _faint),
                    ),
                  // 끄면 표 칸 안 문장은 자간 정리 대상에서 뺀다(설정 table_spacing과 같은 값).
                  Row(
                    children: [
                      const Expanded(
                        child: Text(
                          '표 내 자간 정리',
                          style: TextStyle(fontWeight: FontWeight.w600),
                        ),
                      ),
                      Switch(
                        key: const Key('tableSpacingSwitch'),
                        value: tableSpacing,
                        onChanged: locked
                            ? null
                            : (on) => command('set_table_spacing', [on]),
                      ),
                    ],
                  ),
                  if (!tableSpacing)
                    const Text(
                      '표 칸 안 문장은 자간 정리에서 빼요.',
                      style: TextStyle(fontSize: 12, color: _faint),
                    ),
                ],
                if (isAll) ...[
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
                ],
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

  Widget profilePicker() {
    final ids = profiles.map((p) => '${p['id']}').toList();
    final current = '${state['profile'] ?? ''}';
    return Row(
      children: [
        Expanded(
          child: InputDecorator(
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
        ),
        const SizedBox(width: 8),
        Tooltip(
          message: '예시 문서에서 서식 복사·편집·이름 바꾸기',
          child: TextButton(
            onPressed: locked ? null : () => command('open_settings'),
            child: const Text('서식 관리'),
          ),
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
          InkWell(
            borderRadius: BorderRadius.circular(12),
            onTap: () => setState(() => stagesOpen = !stagesOpen),
            child: Row(
              children: [
                Expanded(
                  child: sectionTitle(
                    Icons.checklist_rounded,
                    '세부 작업  $stagesOn/${stages.length}',
                    stagesChanged
                        ? '처음 기본값과 다르게 조정했어요.${saved ? ' 다음 실행에도 이 구성을 써요.' : ''}'
                        : '실행 순서대로 표시해요. 끄면 그 단계는 건너뛰어요.',
                  ),
                ),
                Icon(
                  stagesOpen ? Icons.expand_less : Icons.expand_more,
                  color: _muted,
                  semanticLabel: stagesOpen ? '세부 작업 접기' : '세부 작업 펼치기',
                ),
              ],
            ),
          ),
          if (stagesOpen) ...[
            const SizedBox(height: 12),
            const Divider(),
            for (var i = 0; i < stages.length; i++)
              CheckboxListTile(
                contentPadding: EdgeInsets.zero,
                controlAffinity: ListTileControlAffinity.leading,
                value: stages[i]['on'] == true,
                onChanged: locked
                    ? null
                    : (v) => command('set_stage', [stages[i]['key'], v == true]),
                title: Text('${i + 1}. ${stages[i]['label']}'),
                subtitle: Text(
                  '${stages[i]['example'] ?? ''}',
                  style: const TextStyle(fontSize: 12, color: _muted),
                ),
              ),
            const Divider(),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              value: saved,
              onChanged: locked
                  ? null
                  : (v) => command('set_stage_default', [v]),
              title: const Text('다음 실행에도 이 구성 사용'),
              subtitle: Text(
                saved
                    ? '바꾸는 즉시 저장돼요.'
                    : '끄면 이번 실행에만 적용하고, 다음에는 처음 기본값으로 시작해요.',
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
                  onPressed: locked ? null : () => command('open_stages'),
                  icon: const Icon(Icons.tune, size: 18),
                  label: const Text('단계별 수치 조정'),
                ),
              ],
            ),
          ],
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
                  style: const TextStyle(color: Color(0xffdc2626), fontSize: 13),
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
                  finished: done.contains(i) || (current != null && i < current),
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
                onPressed: () => command('open_log'),
                icon: const Icon(Icons.receipt_long_outlined),
                label: const Text('상세 작업 로그'),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget guideStep(int index, String text, {required bool active, required bool finished}) =>
      Container(
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
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
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

  Widget outcome() => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      heading('작업 결과를 확인하세요', '${state['status'] ?? '작업이 끝나면 저장된 문서가 표시됩니다.'}'),
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
                      tooltip: '한/글로 열기',
                      onPressed: busy ? null : () => command('open_result', [i]),
                      icon: const Icon(Icons.open_in_new),
                    ),
                    IconButton(
                      tooltip: '폴더에서 보기',
                      onPressed: busy ? null : () => command('show_result', [i]),
                      icon: const Icon(Icons.folder_open_outlined),
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
          ],
        ),
      ),
    ],
  );

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
                        '${files.length}개 문서 · $modeTitle · $rangeLabel · 세부 작업 $stagesOn/${stages.length}',
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
                label: const Text('정리 시작'),
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
                        if (mounted) setState(() => tab = 0);
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
          settingsLabel('프로그램'),
          optionSwitch(
            'check_updates',
            '시작할 때 새 버전 확인',
            '새 버전이 있으면 알려 드려요.',
          ),
          settingsLabel('더 보기'),
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.tune),
            title: const Text('전체 설정 열기'),
            subtitle: const Text(
              '글꼴·문두기호·자간 한도 등 모든 값을 바꿔요.',
              style: TextStyle(fontSize: 12, color: _muted),
            ),
            trailing: const Icon(Icons.open_in_new, size: 18),
            onTap: locked ? null : () => command('open_settings'),
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
