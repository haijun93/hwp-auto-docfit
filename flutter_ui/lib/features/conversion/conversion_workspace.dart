import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// 파일변환 탭이 문서편집 상태에서 읽고 부르는 것(2.0.7: 파일변환 탭 한 화면에서 넣기 → 고르기 → 결과까지).
abstract class ConversionHost {
  ValueNotifier<int> get stateVersion;
  List get files;
  List get results;
  Map get failures;
  List get conversionTargets;
  bool get locked;
  bool get running;
  String get statusText;
  double? get progressValue;
  Future<void> command(String method, [List<Object?> args]);
  Future<void> convertTo(String format);
  Future<void> addConversionFiles();
}

/// 파일변환 탭 화면(참고 디자인 3단): 올린 파일 · 변환할 포맷 · 변환 결과.
/// 포맷 칸은 예전 키패드의 배치·모양만 쓰고, 숫자 키 선택은 없앴다(사용자 지시). 결과는 열기·폴더에서 보기 위주.
class ConversionWorkspace extends StatelessWidget {
  const ConversionWorkspace({super.key, required this.host});

  final ConversionHost host;

  static const accent = Color(0xff7664ec);
  static const ink = Color(0xff1e293b);
  static const faint = Color(0xff64748b);
  static const layout = <String?>[
    'hwpx', 'docx', 'epub', //
    'html', null, 'md',
    'pdf', 'pdfz', 'pdfm',
    'jpg', 'png', 'txt',
  ];

  static IconData icon(String format) => switch (format) {
    'pdf' => Icons.picture_as_pdf_outlined,
    'pdfz' => Icons.compress,
    'pdfm' => Icons.merge_type,
    'docx' => Icons.article_outlined,
    'epub' => Icons.menu_book_outlined,
    'jpg' || 'png' => Icons.image_outlined,
    _ => Icons.description_outlined,
  };

  static String sizeText(Object? value) {
    final bytes = value is num ? value.toDouble() : -1.0;
    if (bytes < 0) return '';
    if (bytes >= 1024 * 1024) {
      return '${(bytes / 1024 / 1024).toStringAsFixed(1)} MB';
    }
    return '${(bytes / 1024).ceil()} KB';
  }

  @override
  Widget build(BuildContext context) => ValueListenableBuilder<int>(
    valueListenable: host.stateVersion,
    builder: (context, _, _) => ColoredBox(
      color: const Color(0xfff6f7fc),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final wide = constraints.maxWidth >= 980;
          final panels = [
            _filesPanel(context),
            _formatPanel(context),
            _resultsPanel(context),
          ];
          return Padding(
            padding: const EdgeInsets.all(16),
            child: Container(
              key: const Key('conversionWorkspace'),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: const Color(0xffcfc6f3), width: 2),
              ),
              padding: const EdgeInsets.all(16),
              child: wide
                  ? Row(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Expanded(flex: 4, child: panels[0]),
                        const SizedBox(width: 16),
                        Expanded(flex: 5, child: panels[1]),
                        const SizedBox(width: 16),
                        Expanded(flex: 4, child: panels[2]),
                      ],
                    )
                  : ListView(
                      children: [
                        SizedBox(height: 260, child: panels[0]),
                        const SizedBox(height: 16),
                        SizedBox(height: 420, child: panels[1]),
                        const SizedBox(height: 16),
                        SizedBox(height: 320, child: panels[2]),
                      ],
                    ),
            ),
          );
        },
      ),
    ),
  );

  Widget _title(String text) => Padding(
    padding: const EdgeInsets.only(bottom: 10),
    child: Text(
      text,
      style: const TextStyle(
        fontSize: 18,
        fontWeight: FontWeight.w800,
        color: ink,
      ),
    ),
  );

  Future<void> _menu(
    BuildContext context,
    Offset at,
    List<(String, IconData, VoidCallback)> items,
  ) async {
    final overlay = Overlay.of(context).context.findRenderObject() as RenderBox;
    final picked = await showMenu<int>(
      context: context,
      position: RelativeRect.fromRect(
        at & const Size(1, 1),
        Offset.zero & overlay.size,
      ),
      items: [
        for (var i = 0; i < items.length; i++)
          PopupMenuItem(
            key: Key('conversionMenu-${items[i].$1}'),
            value: i,
            child: Row(
              children: [
                Icon(items[i].$2, size: 18, color: faint),
                const SizedBox(width: 10),
                Text(items[i].$1),
              ],
            ),
          ),
      ],
    );
    if (picked != null) items[picked].$3();
  }

  void _blankMenu(BuildContext context, Offset at) => _menu(context, at, [
    ('파일 추가', Icons.note_add_outlined, () => host.addConversionFiles()),
    (
      '폴더 추가',
      Icons.create_new_folder_outlined,
      () => host.command('add_folder'),
    ),
    if (host.files.isNotEmpty)
      ('목록 비우기', Icons.clear_all_rounded, () => host.command('clear_files')),
  ]);

  Widget _filesPanel(BuildContext context) {
    final files = host.files.whereType<Map>().toList();
    return GestureDetector(
      behavior: HitTestBehavior.translucent,
      onSecondaryTapDown: host.locked
          ? null
          : (d) => _blankMenu(context, d.globalPosition),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _title('올린 파일 (${files.length}개)'),
          Expanded(
            child: files.isEmpty
                ? Container(
                    key: const Key('conversionDropZone'),
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: const Color(0xfff4f1ff),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: const Color(0xffb9a8e0)),
                    ),
                    padding: const EdgeInsets.all(16),
                    child: const Text(
                      '여기에 파일을 끌어 놓으세요\nHWP·HWPX·PDF·DOCX·그림·텍스트',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: faint, height: 1.6),
                    ),
                  )
                : ListView.separated(
                    itemCount: files.length,
                    separatorBuilder: (_, _) => const SizedBox(height: 8),
                    itemBuilder: (context, i) {
                      final file = files[i];
                      return GestureDetector(
                        onSecondaryTapDown: host.locked
                            ? null
                            : (d) => _menu(context, d.globalPosition, [
                                (
                                  '열기',
                                  Icons.open_in_new,
                                  () => host.command('open_source_file', [i]),
                                ),
                                (
                                  '폴더에서 보기',
                                  Icons.folder_open_outlined,
                                  () => host.command('show_source_file', [i]),
                                ),
                                (
                                  '목록에서 빼기',
                                  Icons.close_rounded,
                                  () => host.command('remove_file', [i]),
                                ),
                              ]),
                        child: Container(
                          key: Key('conversionFile-$i'),
                          padding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 10,
                          ),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(12),
                            boxShadow: const [
                              BoxShadow(
                                color: Color(0x14000000),
                                blurRadius: 6,
                                offset: Offset(0, 2),
                              ),
                            ],
                          ),
                          child: Row(
                            children: [
                              const Icon(
                                Icons.description_outlined,
                                color: faint,
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      '${file['name'] ?? ''}',
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                    if (sizeText(file['size']).isNotEmpty)
                                      Text(
                                        sizeText(file['size']),
                                        style: const TextStyle(
                                          fontSize: 12,
                                          color: faint,
                                        ),
                                      ),
                                  ],
                                ),
                              ),
                              IconButton(
                                key: Key('conversionRemove-$i'),
                                tooltip: '목록에서 빼기',
                                onPressed: host.locked
                                    ? null
                                    : () => host.command('remove_file', [i]),
                                icon: const Icon(Icons.close_rounded, size: 18),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  key: const Key('conversionPickFiles'),
                  onPressed: host.locked ? null : host.addConversionFiles,
                  icon: const Icon(Icons.add),
                  label: const Text('파일 추가하기'),
                ),
              ),
              const SizedBox(width: 8),
              OutlinedButton.icon(
                key: const Key('conversionPickFolder'),
                onPressed: host.locked
                    ? null
                    : () => host.command('add_folder'),
                icon: const Icon(Icons.create_new_folder_outlined),
                label: const Text('폴더'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _formatPanel(BuildContext context) {
    final targets = {
      for (final item in host.conversionTargets.whereType<Map>())
        '${item['format']}': item,
    };
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Center(child: _title('변환할 포맷 선택')),
        Expanded(
          child: LayoutBuilder(
            builder: (context, box) {
              final cellW = (box.maxWidth - 16) / 3;
              final cellH = ((box.maxHeight - 24) / 4).clamp(56.0, 120.0);
              return Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final format in layout)
                    SizedBox(
                      width: cellW,
                      height: cellH,
                      child: format == null
                          ? _centerCell()
                          : _formatCell(format, targets[format]),
                    ),
                ],
              );
            },
          ),
        ),
        const SizedBox(height: 8),
        const Text(
          '포맷을 누르면 바로 변환해요. 결과는 원본 옆에 저장돼요.',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 13, color: faint),
        ),
      ],
    );
  }

  Widget _centerCell() => Container(
    decoration: BoxDecoration(
      color: const Color(0xffeef2ff),
      borderRadius: BorderRadius.circular(14),
    ),
    alignment: Alignment.center,
    padding: const EdgeInsets.all(6),
    child: Text(
      host.running
          ? '변환 중…'
          : host.files.isEmpty
          ? '파일을\n먼저 넣으세요'
          : '${host.files.length}개 파일',
      textAlign: TextAlign.center,
      style: const TextStyle(
        fontSize: 13,
        fontWeight: FontWeight.w600,
        color: faint,
      ),
    ),
  );

  Widget _formatCell(String format, Map? target) {
    final enabled = target != null && target['enabled'] == true && !host.locked;
    final label = '${target?['label'] ?? format.toUpperCase()}';
    final reason = '${target?['reason'] ?? '변환할 문서를 추가하세요.'}';
    return Tooltip(
      message: enabled ? '$label로 변환' : reason,
      child: Material(
        color: enabled ? const Color(0xfff8f7ff) : const Color(0xfff1f5f9),
        borderRadius: BorderRadius.circular(14),
        child: InkWell(
          key: Key('conversionFormat-$format'),
          borderRadius: BorderRadius.circular(14),
          onTap: enabled ? () => host.convertTo(format) : null,
          child: Opacity(
            opacity: enabled ? 1 : 0.4,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(icon(format), color: enabled ? accent : faint, size: 26),
                const SizedBox(height: 6),
                Text(
                  label,
                  textAlign: TextAlign.center,
                  maxLines: 2,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: ink,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _resultsPanel(BuildContext context) {
    final results = host.results.whereType<Map>().toList();
    final failures = host.failures.entries.toList();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _title('변환 결과'),
        if (host.running) ...[
          LinearProgressIndicator(value: host.progressValue, color: accent),
          const SizedBox(height: 6),
          Text(
            host.statusText,
            style: const TextStyle(fontSize: 12, color: faint),
          ),
          Align(
            alignment: Alignment.centerRight,
            child: TextButton(
              key: const Key('conversionStop'),
              onPressed: () => host.command('stop'),
              child: const Text('멈추기'),
            ),
          ),
        ],
        Expanded(
          child: results.isEmpty && failures.isEmpty
              ? const Center(
                  child: Text(
                    '변환한 파일이 여기에 나와요.',
                    style: TextStyle(color: faint),
                  ),
                )
              : ListView(
                  children: [
                    for (var i = 0; i < results.length; i++)
                      GestureDetector(
                        onSecondaryTapDown: (d) =>
                            _menu(context, d.globalPosition, [
                              (
                                '열기',
                                Icons.open_in_new,
                                () => host.command('open_result', [i]),
                              ),
                              (
                                '폴더에서 보기',
                                Icons.folder_open_outlined,
                                () => host.command('show_result', [i]),
                              ),
                              (
                                '경로 복사',
                                Icons.content_copy_rounded,
                                () => Clipboard.setData(
                                  ClipboardData(
                                    text: '${results[i]['path'] ?? ''}',
                                  ),
                                ),
                              ),
                              (
                                '원본 열기',
                                Icons.description_outlined,
                                () => host.command('open_result_source', [i]),
                              ),
                            ]),
                        child: Container(
                          key: Key('conversionResult-$i'),
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.fromLTRB(12, 8, 4, 8),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(12),
                            boxShadow: const [
                              BoxShadow(
                                color: Color(0x14000000),
                                blurRadius: 6,
                                offset: Offset(0, 2),
                              ),
                            ],
                          ),
                          child: Row(
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      '${results[i]['name'] ?? ''}',
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                    const Row(
                                      children: [
                                        Icon(
                                          Icons.check_circle_outline,
                                          size: 14,
                                          color: Color(0xff16a34a),
                                        ),
                                        SizedBox(width: 4),
                                        Text(
                                          '변환 완료',
                                          style: TextStyle(
                                            fontSize: 12,
                                            color: faint,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                              IconButton(
                                key: Key('conversionOpen-$i'),
                                tooltip: '열기',
                                onPressed: () =>
                                    host.command('open_result', [i]),
                                icon: const Icon(Icons.open_in_new, size: 20),
                              ),
                              IconButton(
                                key: Key('conversionShow-$i'),
                                tooltip: '폴더에서 보기',
                                onPressed: () =>
                                    host.command('show_result', [i]),
                                icon: const Icon(
                                  Icons.folder_open_outlined,
                                  size: 20,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    for (final failure in failures)
                      Container(
                        margin: const EdgeInsets.only(bottom: 8),
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: const Color(0xfffef2f2),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          '${failure.key}\n${failure.value}',
                          style: const TextStyle(
                            fontSize: 12,
                            color: Color(0xffb91c1c),
                          ),
                        ),
                      ),
                  ],
                ),
        ),
        const SizedBox(height: 10),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          alignment: WrapAlignment.end,
          children: [
            FilledButton.icon(
              key: const Key('conversionOpenFolder'),
              style: FilledButton.styleFrom(backgroundColor: accent),
              onPressed: results.isEmpty || host.running
                  ? null
                  : () => host.command('show_result', [0]),
              icon: const Icon(Icons.folder_open_outlined),
              label: const Text('결과 폴더 열기'),
            ),
            OutlinedButton(
              key: const Key('conversionOpenAll'),
              onPressed: results.isEmpty || host.running
                  ? null
                  : () => host.command('open_results'),
              child: const Text('결과 모두 열기'),
            ),
            OutlinedButton(
              key: const Key('conversionRestart'),
              onPressed: host.locked
                  ? null
                  : () async {
                      await host.command('next_job');
                      await host.command('clear_files');
                    },
              child: const Text('처음으로'),
            ),
          ],
        ),
      ],
    );
  }
}
