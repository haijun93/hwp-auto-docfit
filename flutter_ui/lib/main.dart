import 'dart:async';

import 'package:flutter/material.dart';

import 'bridge.dart' as bridge;

typedef ApiCall = Future<Object?> Function(String, List<Object?>);

void main() => runApp(const DocFitApp());

class DocFitApp extends StatelessWidget {
  const DocFitApp({super.key, this.api = bridge.callApi});
  final ApiCall api;
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: '한글 문서 정리',
    debugShowCheckedModeBanner: false,
    theme: ThemeData(
      useMaterial3: true,
      fontFamily: 'NotoSansKR',
      colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xff2563eb)),
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
  bool busy = false, polling = false;
  String? error;
  Timer? timer;
  static const tabs = ['문서 선택', '작업 방식', '진행 과정', '결과 확인'];
  static const modes = [
    (
      'spacing',
      '자간 정리',
      '줄 끝에서 끊긴 단어와 글자 간격을 정리해요.',
      Icons.space_bar_rounded,
    ),
    ('unify', '서식 통일', '문서의 대표 서식을 확인하고 예외 문장을 정리해요.', Icons.rule_rounded),
    ('format', '서식 적용', '선택한 표준 서식을 문서에 적용해요.', Icons.format_paint_rounded),
    ('all', '한 번에 적용', '서식과 자간을 함께 정리해요.', Icons.auto_awesome_rounded),
  ];
  bool get running => state['running'] == true;
  bool get locked => busy || running || state.isEmpty || error != null;
  List get files => state['files'] as List? ?? [];
  List get results => state['results'] as List? ?? [];
  String get mode => state['mode'] as String? ?? 'spacing';

  @override
  void initState() {
    super.initState();
    refresh();
    timer = Timer.periodic(const Duration(seconds: 1), (_) => refresh());
  }

  @override
  void dispose() {
    timer?.cancel();
    super.dispose();
  }

  Future<void> refresh() async {
    if (polling) return;
    polling = true;
    try {
      final next = await widget.api('get_state', []);
      if (mounted && next is Map) {
        setState(() {
          state = Map<String, dynamic>.from(next);
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
      if (mounted && response is Map) {
        setState(() => state = Map<String, dynamic>.from(response));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('작업을 실행하지 못했어요: $e')));
      }
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Widget panel(Widget child) => Container(
    padding: const EdgeInsets.all(24),
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
        Text(
          subtitle,
          style: const TextStyle(color: Color(0xff64748b), height: 1.6),
        ),
      ],
    ),
  );

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(
      backgroundColor: Colors.white,
      surfaceTintColor: Colors.transparent,
      toolbarHeight: 72,
      title: Row(
        children: [
          Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(
              color: const Color(0xff172b4d),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(
              Icons.description_rounded,
              color: Colors.white,
              size: 23,
            ),
          ),
          const SizedBox(width: 12),
          const Text(
            'docfit',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w800,
              letterSpacing: -1.2,
            ),
          ),
          if (MediaQuery.sizeOf(context).width >= 600) const SizedBox(width: 10),
          if (MediaQuery.sizeOf(context).width >= 600) const Text(
            'STUDIO',
            style: TextStyle(
              fontSize: 10,
              letterSpacing: 2,
              color: Color(0xff738299),
            ),
          ),
        ],
      ),
      actions: [
        IconButton(
          tooltip: '작업 로그',
          onPressed: busy ? null : () => command('open_log'),
          icon: const Icon(Icons.receipt_long_outlined),
        ),
        IconButton(
          tooltip: '설정',
          onPressed: locked ? null : () => command('open_settings'),
          icon: const Icon(Icons.settings_outlined),
        ),
        PopupMenuButton<String>(
          tooltip: '문서 도구',
          enabled: !locked,
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
        const SizedBox(width: 12),
      ],
    ),
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
                  if (layout.maxWidth < 1000)
                    Padding(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 12,
                      ),
                      child: Row(
                        children: List.generate(
                          tabs.length,
                          (i) => Expanded(
                            child: Padding(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 3,
                              ),
                              child: TextButton(
                                style: TextButton.styleFrom(
                                  padding: const EdgeInsets.symmetric(
                                    vertical: 14,
                                  ),
                                  backgroundColor: tab == i
                                      ? const Color(0xffe4edff)
                                      : Colors.transparent,
                                  foregroundColor: tab == i
                                      ? const Color(0xff1d4ed8)
                                      : const Color(0xff64748b),
                                ),
                                onPressed: () => setState(() => tab = i),
                                child: Text(
                                  '${i + 1}. ${tabs[i]}',
                                  textAlign: TextAlign.center,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
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
  );

  Widget sidebar() => Container(
    width: 220,
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
            'MY WORKSPACE',
            style: TextStyle(
              fontSize: 10,
              letterSpacing: 2,
              color: Color(0xff8b98ad),
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
        for (var i = 0; i < tabs.length; i++)
          Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Material(
              color: tab == i ? const Color(0xffedf3ff) : Colors.transparent,
              borderRadius: BorderRadius.circular(14),
              child: InkWell(
                borderRadius: BorderRadius.circular(14),
                onTap: () => setState(() => tab = i),
                child: Padding(
                  padding: const EdgeInsets.symmetric(
                    vertical: 17,
                    horizontal: 12,
                  ),
                  child: Row(
                    children: [
                      Text(
                        '0${i + 1}',
                        style: TextStyle(
                          fontSize: 12,
                          color: tab == i
                              ? const Color(0xff2563eb)
                              : const Color(0xffa5afbd),
                        ),
                      ),
                      const SizedBox(width: 13),
                      Text(
                        tabs[i],
                        style: TextStyle(
                          fontWeight: tab == i
                              ? FontWeight.w700
                              : FontWeight.w500,
                          color: tab == i
                              ? const Color(0xff1d4ed8)
                              : const Color(0xff66748a),
                        ),
                      ),
                      const Spacer(),
                      if (tab == i)
                        const Icon(
                          Icons.arrow_forward_rounded,
                          size: 16,
                          color: Color(0xff2563eb),
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
            color: const Color(0xfff3f8f7),
            borderRadius: BorderRadius.circular(18),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(
                Icons.verified_user_outlined,
                color: Color(0xff2e8376),
                size: 24,
              ),
              const SizedBox(height: 12),
              const Text(
                '안심하고 시작하세요',
                style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 6),
              const Text(
                '결과는 새 파일로 저장돼요.',
                style: TextStyle(fontSize: 11, color: Color(0xff738299)),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),
        Text(
          'ALPHA  /  ${state['version'] ?? '연결 중'}',
          style: const TextStyle(fontSize: 10, color: Color(0xff8b98ad)),
        ),
      ],
    ),
  );

  Widget documents() => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      welcome(),
      const SizedBox(height: 24),
      panel(
        Column(
          children: [
            Container(
              padding: const EdgeInsets.all(15),
              decoration: BoxDecoration(
                color: const Color(0xffedf3ff),
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Icon(
                Icons.upload_file_rounded,
                size: 34,
                color: Color(0xff2563eb),
              ),
            ),
            const SizedBox(height: 18),
            const Text(
              '정리할 문서를 놓아주세요',
              style: TextStyle(fontWeight: FontWeight.w700, fontSize: 19),
            ),
            const SizedBox(height: 8),
            const Text(
              '파일을 끌어다 놓거나 아래에서 선택하세요.',
              style: TextStyle(color: Color(0xff738299), fontSize: 13),
            ),
            const SizedBox(height: 24),
            Wrap(
              spacing: 12,
              runSpacing: 12,
              alignment: WrapAlignment.center,
              children: [
                FilledButton.icon(
                  onPressed: locked ? null : () => command('add_files'),
                  icon: const Icon(Icons.add),
                  label: const Text('문서 선택'),
                ),
                OutlinedButton.icon(
                  onPressed: locked ? null : () => command('add_folder'),
                  icon: const Icon(Icons.folder_open),
                  label: const Text('폴더 선택'),
                ),
                OutlinedButton.icon(
                  onPressed: locked ? null : () => command('text_input'),
                  icon: const Icon(Icons.edit_note),
                  label: const Text('텍스트 입력'),
                ),
              ],
            ),
          ],
        ),
      ),
      if (files.isNotEmpty) ...[
        const SizedBox(height: 20),
        Row(
          children: [
            Text('선택한 문서 ${files.length}개'),
            const Spacer(),
            TextButton(
              onPressed: locked ? null : () => command('clear_files'),
              child: const Text('전체 비우기'),
            ),
          ],
        ),
        panel(
          Column(
            children: List.generate(
              files.length,
              (i) => ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.description_outlined),
                title: Text(
                  files[i]['name'] ?? '',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
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
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: .8),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Text(
                    'MAKE ROOM FOR BETTER WORK',
                    style: TextStyle(
                      fontSize: 9,
                      letterSpacing: 1.2,
                      color: Color(0xff537294),
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                const SizedBox(height: 22),
                Text(
                  '오늘의 문서,\n더 단정하게.',
                  style: TextStyle(
                    fontSize: layout.maxWidth < 500 ? 30 : 36,
                    fontWeight: FontWeight.w800,
                    height: 1.35,
                    letterSpacing: -1.5,
                    color: const Color(0xff172b4d),
                  ),
                ),
                const SizedBox(height: 16),
                const Text(
                  '복잡한 정리는 맡기고,\n중요한 내용에 집중하세요.',
                  style: TextStyle(
                    fontSize: 14,
                    height: 1.8,
                    color: Color(0xff637793),
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

  Widget options() => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      heading('어떻게 정리할까요?', '작업을 선택하고 세부 설정을 확인하세요.'),
      LayoutBuilder(
        builder: (context, box) => Wrap(
          spacing: 16,
          runSpacing: 16,
          children: modes.map((m) {
            final selected = mode == m.$1;
            return SizedBox(
              width: box.maxWidth >= 620
                  ? (box.maxWidth - 16) / 2
                  : box.maxWidth,
              child: Material(
                color: selected ? const Color(0xffeaf1ff) : Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20),
                  side: BorderSide(
                    color: selected
                        ? const Color(0xff2563eb)
                        : const Color(0xffe2e8f0),
                    width: selected ? 2 : 1,
                  ),
                ),
                clipBehavior: Clip.antiAlias,
                child: Semantics(
                  selected: selected,
                  child: InkWell(
                    onTap: locked ? null : () => command('set_mode', [m.$1]),
                    child: Padding(
                      padding: const EdgeInsets.all(22),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(m.$4, color: const Color(0xff2563eb)),
                              const Spacer(),
                              if (selected)
                                const Icon(
                                  Icons.check_circle,
                                  color: Color(0xff2563eb),
                                ),
                            ],
                          ),
                          const SizedBox(height: 16),
                          Text(
                            m.$2,
                            style: const TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(m.$3, style: const TextStyle(height: 1.6)),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            );
          }).toList(),
        ),
      ),
      const SizedBox(height: 20),
      panel(
        Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            ListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('작업별 세부 설정'),
              subtitle: const Text('설정창에서 기본값으로 저장하면 다음 작업에도 사용해요.'),
              trailing: const Icon(Icons.chevron_right),
              onTap: locked ? null : () => command('open_stages'),
            ),
            const Divider(),
            ListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('작업할 쪽 범위'),
              subtitle: Text(
                state['range']?['enabled'] == true
                    ? '${state['range']['start']} ~ ${state['range']['end']}쪽'
                    : '문서 전체',
              ),
              trailing: const Icon(Icons.chevron_right),
              onTap: locked ? null : rangeDialog,
            ),
          ],
        ),
      ),
    ],
  );

  Future<void> rangeDialog() async {
    final range = state['range'] as Map? ?? {};
    bool enabled = range['enabled'] == true;
    final start = TextEditingController(text: '${range['start'] ?? 1}');
    final end = TextEditingController(text: '${range['end'] ?? 1}');
    String? validation;
    final choice = await showDialog<List<Object?>>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, update) => AlertDialog(
          title: const Text('작업할 쪽 범위'),
          content: SizedBox(
            width: 320,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('일부 쪽만 정리'),
                  value: enabled,
                  onChanged: (v) => update(() => enabled = v),
                ),
                if (enabled)
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: start,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(labelText: '시작 쪽'),
                        ),
                      ),
                      const Padding(
                        padding: EdgeInsets.all(12),
                        child: Text('~'),
                      ),
                      Expanded(
                        child: TextField(
                          controller: end,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(labelText: '끝 쪽'),
                        ),
                      ),
                    ],
                  ),
                if (validation != null)
                  Text(validation!, style: const TextStyle(color: Colors.red)),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('취소'),
            ),
            FilledButton(
              onPressed: () {
                final a = int.tryParse(start.text), b = int.tryParse(end.text);
                if (enabled && (a == null || b == null || a < 1 || b < a)) {
                  update(() => validation = '시작·끝 쪽을 올바르게 입력하세요.');
                  return;
                }
                Navigator.pop(ctx, [enabled, start.text, end.text]);
              },
              child: const Text('적용'),
            ),
          ],
        ),
      ),
    );
    // Dialog route removes its fields after the dismissal animation.
    await Future<void>.delayed(const Duration(milliseconds: 300));
    start.dispose();
    end.dispose();
    if (choice != null && mounted) await command('set_range', choice);
  }

  Widget progress() {
    final guide = state['guide'] as Map? ?? {};
    final steps = guide['steps'] as List? ?? [];
    final current = guide['current'] as int?;
    final done = (guide['done'] as List? ?? []).cast<int>();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        heading(
          running ? '문서를 정리하고 있어요' : '진행 상황을 확인하세요',
          '${guide['message'] ?? '작업을 시작하면 지금 하는 일을 여기에서 알려 드려요.'}',
        ),
        panel(
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
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
                style: TextStyle(fontSize: 12, color: Color(0xff8b98ad)),
              ),
              if (state['status'] != null && '${state['status']}'.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Text(
                    '${state['status']}',
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 12, color: Color(0xff64748b)),
                  ),
                ),
              if (running)
                const Padding(
                  padding: EdgeInsets.only(top: 20),
                  child: LinearProgressIndicator(),
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
          color: active ? const Color(0xffedf3ff) : Colors.transparent,
          borderRadius: BorderRadius.circular(14),
        ),
        child: Row(
          children: [
            CircleAvatar(
              radius: 14,
              backgroundColor: active
                  ? const Color(0xff2563eb)
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
                  ? const Icon(Icons.check, size: 16, color: Color(0xff287c72))
                  : Text(
                      '${index + 1}',
                      style: TextStyle(
                        fontSize: 12,
                        color: active ? Colors.white : const Color(0xff64748b),
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
                      ? const Color(0xff1d4ed8)
                      : finished
                      ? const Color(0xff475569)
                      : const Color(0xff94a3b8),
                ),
              ),
            ),
          ],
        ),
      );

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
              color: const Color(0xff2563eb),
            ),
            const SizedBox(height: 18),
            Text(
              results.isEmpty ? '아직 저장된 결과가 없어요.' : '저장된 결과 ${results.length}개',
            ),
            for (final result in results)
              ListTile(
                leading: const Icon(Icons.description_outlined),
                title: Text(result['name'] ?? ''),
                subtitle: Text(
                  result['path'] ?? '',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            const SizedBox(height: 20),
            FilledButton.icon(
              onPressed: results.isEmpty || busy
                  ? null
                  : () => command('open_results'),
              icon: const Icon(Icons.open_in_new),
              label: const Text('결과 파일 열기'),
            ),
          ],
        ),
      ),
    ],
  );

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
            const Spacer(),
            if (running)
              TextButton(
                onPressed: busy ? null : () => command('stop'),
                child: const Text('작업 중단'),
              ),
            if (tab < 2)
              FilledButton(
                onPressed: locked || files.isEmpty
                    ? null
                    : () async {
                        if (tab == 0) {
                          setState(() => tab = 1);
                          return;
                        }
                        final range = state['range'] as Map? ?? {};
                        await command('start', [
                          mode,
                          range['enabled'] == true,
                          '${range['start'] ?? 1}',
                          '${range['end'] ?? 1}',
                        ]);
                        if (mounted && running) setState(() => tab = 2);
                      },
                child: Text(tab == 0 ? '작업 방식 선택' : '정리 시작'),
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
          '원본을 보존하고 결과를 별도 파일로 저장해요.  ·  ${state['version'] ?? '알파'}',
          textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 11, color: Color(0xff64748b)),
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
                      color: Color(0xff2563eb),
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
              color: const Color(0xff287c72),
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
