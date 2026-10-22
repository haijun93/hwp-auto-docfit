import '../../core/close_guards.dart';
import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../core/api/abbreviation_api.dart';
import '../preview/option_images.dart';
import 'idiom_panel.dart';
import 'kiosk_theme.dart';
import 'setting_guides.dart';

/// 전체 설정: 분류 타일을 고르고, 설정마다 한글 문서 예시로 무엇이 달라지는지 보여 준다.
class SettingsDialog extends StatefulWidget {
  const SettingsDialog({super.key, required this.api});
  final ApiCall api;
  @override
  State<SettingsDialog> createState() => _SettingsDialogState();
}

// 설정 값 목록이 아닌 관리 화면 분류(상용구·앱 정보, 2026-10-15).
const _panelCategories = [
  GuideCategory('idiom_text', '글자 상용구', '준말 → 글자', Icons.short_text_rounded),
  GuideCategory('idiom_body', '본문 상용구', '준말 → 문서 서식', Icons.article_outlined),
  GuideCategory('about', '앱 정보', '개발자 도토리만두', Icons.info_outline_rounded),
];

class _SettingsDialogState extends State<SettingsDialog> {
  Map? snapshot;
  final Map<String, TextEditingController> inputs = {};
  final Map<String, Object?> changed = {};
  final search = TextEditingController();
  bool busy = true;
  String? error;
  String category = guideCategories.first.id;

  /// 마지막으로 바꾼 설정(한/글 조판 미리보기에서 그 설정이 닿는 문단을 강조한다).
  String? lastKey;

  /// 이 PC에서 찾은 글꼴(한/글 전용 폴더 + Windows, docfit_core.hangul_fonts). 한국어 이름·한/글 글꼴 먼저.
  List<String> fontNames = const [];
  Map fontSummary = const {};

  late final CloseLease _closeLease;
  Future<bool> _prepareHostClose() async {
    if (busy || !canCloseEditor(context)) return false;
    if (changed.isNotEmpty && !await confirmHostDiscard(context)) return false;
    if (!mounted) return false;
    Navigator.of(context).pop();
    return true;
  }

  @override
  void initState() {
    super.initState();
    _closeLease = CloseGuards.register(_prepareHostClose);
    load();
    _loadFonts();
  }

  Future<void> _loadFonts() async {
    try {
      final result = await widget.api('hangul_fonts', ['list']);
      if (result is! Map || !mounted) return;
      final fonts = [
        for (final f in (result['fonts'] as List? ?? [])) f as Map,
      ];
      bool korean(String s) => RegExp('[가-힣]').hasMatch(s);
      final names = [
        for (final f in fonts)
          if (korean('${f['name']}')) '${f['name']}',
        for (final f in fonts)
          if (!korean('${f['name']}')) '${f['name']}',
      ];
      setState(() {
        fontNames = names;
        fontSummary = result;
      });
    } catch (_) {
      /* 글꼴 목록이 없으면 직접 입력만 한다 */
    }
  }

  @override
  void dispose() {
    _closeLease.release();
    search.dispose();
    for (final input in inputs.values) {
      input.dispose();
    }
    super.dispose();
  }

  Future<Map> request(String method, List<Object?> args) async {
    final response = await widget.api(method, args);
    if (response is! Map || response['api_version'] != 1) {
      throw Exception('앱 연결과 버전을 확인해 주세요.');
    }
    if (response['ok'] != true) {
      throw Exception(
        '${(response['error'] as Map?)?['message'] ?? '설정을 적용하지 못했어요.'}',
      );
    }
    return response['data'] as Map;
  }

  Future<void> load() async {
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final data = await request('get_settings', []);
      if (!mounted) return;
      for (final input in inputs.values) {
        input.dispose();
      }
      inputs.clear();
      final values = data['values'] as Map;
      for (final field in data['fields'] as List) {
        if (field['type'] != 'boolean') {
          inputs[field['key']] = TextEditingController(
            text: '${values[field['key']] ?? ''}',
          );
        }
      }
      setState(() {
        snapshot = data;
        changed.clear();
        final present = _categoriesWithFields();
        if (!present.contains(category) && present.isNotEmpty) {
          category = present.first;
        }
      });
    } catch (e) {
      if (mounted) setState(() => error = '$e');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> save() async {
    if (busy || snapshot == null || changed.isEmpty) return;
    setState(() {
      busy = true;
      error = null;
    });
    try {
      await request('save_settings', [
        Map<String, Object?>.from(changed),
        snapshot!['revision'],
      ]);
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) setState(() => error = '$e');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  void restoreDefaults() {
    for (final field in snapshot!['fields'] as List) {
      changed[field['key']] = field['default'];
      inputs[field['key']]?.text = '${field['default'] ?? ''}';
    }
    setState(() {});
  }

  List<Map> get _fields => [
    for (final f in snapshot?['fields'] as List? ?? const []) f as Map,
  ];

  String _categoryOf(Map field) {
    final guide = guideFor('${field['key']}');
    if (guide != null) return guide.category;
    return switch ('${field['group']}') {
      '글꼴' => 'font',
      '개발자 도구' => 'dev',
      '표준서식' => 'report',
      '네트워크' => 'program',
      _ => 'program',
    };
  }

  List<String> _categoriesWithFields() {
    final used = {for (final f in _fields) _categoryOf(f)};
    return [
      for (final c in guideCategories)
        if (used.contains(c.id)) c.id,
    ];
  }

  bool _matches(Map field, String query) {
    if (query.isEmpty) return true;
    final guide = guideFor('${field['key']}');
    return '${field['label']} ${guide?.title ?? ''} ${guide?.summary ?? ''}'
        .contains(query);
  }

  Object? _value(String key) {
    if (changed.containsKey(key)) return changed[key];
    final input = inputs[key];
    if (input != null) return input.text;
    return (snapshot?['values'] as Map? ?? {})[key];
  }

  void _setNumber(String key, double delta) {
    final input = inputs[key]!;
    final current = double.tryParse(input.text.trim()) ?? 0;
    final next = math.max(0, current + delta);
    input.text = next == next.roundToDouble()
        ? next.toStringAsFixed(0)
        : next.toStringAsFixed(1);
    setState(() {
      changed[key] = input.text;
      lastKey = key;
    });
  }

  Widget _control(Map field, bool locked) {
    final key = '${field['key']}';
    if (field['type'] == 'boolean') {
      return Transform.scale(
        scale: 1.15,
        child: Switch(
          key: ValueKey(key),
          activeThumbColor: Colors.white,
          activeTrackColor: Kiosk.blue,
          value: _value(key) == true,
          onChanged: locked
              ? null
              : (value) => setState(() {
                  changed[key] = value;
                  lastKey = key;
                }),
        ),
      );
    }
    final number = field['type'] == 'number';
    final unit = guideFor(key)?.unit;
    final box = SizedBox(
      width: number ? 92 : 260,
      child: TextField(
        key: ValueKey(key),
        controller: inputs[key],
        enabled: !locked,
        textAlign: number ? TextAlign.center : TextAlign.start,
        style: const TextStyle(
          fontSize: 17,
          fontWeight: FontWeight.w600,
          color: Kiosk.ink,
        ),
        keyboardType: number
            ? const TextInputType.numberWithOptions(decimal: true)
            : TextInputType.text,
        decoration: InputDecoration(
          isDense: true,
          filled: true,
          fillColor: const Color(0xfff2f4f6),
          hintText: number ? null : '비워 두면 기본값',
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide.none,
          ),
        ),
        onChanged: (value) => setState(() {
          changed[key] = value;
          lastKey = key;
        }),
      ),
    );
    if (!number && key.endsWith('.font') && fontNames.isNotEmpty) {
      // 한/글이 쓰는 글꼴(이 PC에서 자동으로 찾은 목록)에서 고른다. 직접 입력도 그대로 된다.
      return Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          box,
          const SizedBox(width: 6),
          PopupMenuButton<String>(
            tooltip: '이 PC 글꼴에서 고르기',
            enabled: !locked,
            icon: const Icon(Icons.font_download_outlined, color: Kiosk.blue),
            itemBuilder: (context) => [
              for (final name in fontNames)
                PopupMenuItem(
                  value: name,
                  height: 36,
                  child: Text(name, style: TextStyle(fontFamily: name)),
                ),
            ],
            onSelected: (name) => setState(() {
              inputs[key]?.text = name;
              changed[key] = name;
              lastKey = key;
            }),
          ),
        ],
      );
    }
    if (!number && key == 'hwp_font_folder' && fontSummary.isNotEmpty) {
      final dirs = [
        for (final d in (fontSummary['hangul_dirs'] as List? ?? [])) '$d',
      ];
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          box,
          const SizedBox(height: 6),
          SizedBox(
            width: 420,
            child: Text(
              dirs.isEmpty
                  ? '한/글 전용 글꼴 폴더를 찾지 못했어요. Windows 글꼴 ${fontSummary['total'] ?? 0}종을 써요.'
                  : '자동 인식: 한/글 전용 글꼴 ${fontSummary['hangul_count'] ?? 0}종 · 전체 ${fontSummary['total'] ?? 0}종\n${dirs.join('\n')}',
              style: Kiosk.caption,
            ),
          ),
        ],
      );
    }
    if (!number) return box;
    Widget step(IconData icon, double delta, String label) =>
        IconButton.filledTonal(
          tooltip: label,
          style: IconButton.styleFrom(
            backgroundColor: Kiosk.blueSoft,
            foregroundColor: Kiosk.blue,
          ),
          onPressed: locked ? null : () => _setNumber(key, delta),
          icon: Icon(icon, size: 20),
        );
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        step(Icons.remove, -1, '1 줄이기'),
        const SizedBox(width: 6),
        box,
        const SizedBox(width: 6),
        step(Icons.add, 1, '1 늘리기'),
        if (unit != null) ...[
          const SizedBox(width: 8),
          Text(unit, style: Kiosk.body),
        ],
      ],
    );
  }

  Widget _card(Map field, bool locked) {
    final key = '${field['key']}';
    final guide = guideFor(key);
    final isChanged = changed.containsKey(key);
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(20),
      decoration: Kiosk.cardBox(selected: isChanged),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          LayoutBuilder(
            builder: (context, constraints) {
              final heading = Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Flexible(
                        child: Text(
                          guide?.title ?? '${field['label']}',
                          style: Kiosk.cardTitle,
                        ),
                      ),
                      if (isChanged) ...[
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 2,
                          ),
                          decoration: BoxDecoration(
                            color: Kiosk.blueSoft,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Text(
                            '바뀜',
                            style: TextStyle(
                              fontSize: 12,
                              color: Kiosk.blue,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                  if (guide != null) ...[
                    const SizedBox(height: 4),
                    Text(guide.summary, style: Kiosk.body),
                  ],
                ],
              );
              // 넓으면 설명 왼쪽·조절 버튼 오른쪽 끝, 좁으면 설명 아래에 조절 버튼.
              if (constraints.maxWidth < 560) {
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    heading,
                    const SizedBox(height: 10),
                    _control(field, locked),
                  ],
                );
              }
              return Row(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  Expanded(child: heading),
                  const SizedBox(width: 16),
                  _control(field, locked),
                ],
              );
            },
          ),
          if (guide?.preview != null) ...[
            const SizedBox(height: 16),
            guide!.preview!(_value(key)),
          ],
        ],
      ),
    );
  }

  Widget _categoryTile(GuideCategory item, int count, bool compact) {
    final selected = item.id == category && search.text.trim().isEmpty;
    final tile = Material(
      color: selected ? Kiosk.blueSoft : Colors.white,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        key: ValueKey('category-${item.id}'),
        borderRadius: BorderRadius.circular(16),
        onTap: () => setState(() {
          category = item.id;
          search.clear();
        }),
        child: Padding(
          padding: EdgeInsets.symmetric(
            horizontal: 14,
            vertical: compact ? 10 : 14,
          ),
          child: Row(
            mainAxisSize: compact ? MainAxisSize.min : MainAxisSize.max,
            children: [
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  color: selected ? Kiosk.blue : const Color(0xfff2f4f6),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  item.icon,
                  size: 20,
                  color: selected ? Colors.white : Kiosk.sub,
                ),
              ),
              const SizedBox(width: 12),
              Flexible(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      item.title,
                      style: TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w700,
                        color: selected ? Kiosk.blue : Kiosk.ink,
                      ),
                    ),
                    if (!compact)
                      Text(
                        count < 0
                            ? item.subtitle
                            : '${item.subtitle} · $count개',
                        style: Kiosk.caption,
                      ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
    return Padding(
      padding: const EdgeInsets.only(bottom: 8, right: 8),
      child: tile,
    );
  }

  @override
  Widget build(BuildContext context) {
    final locked = busy || snapshot?['running'] == true;
    final query = search.text.trim();
    final counts = <String, int>{};
    for (final field in _fields) {
      counts.update(_categoryOf(field), (n) => n + 1, ifAbsent: () => 1);
    }
    final visible =
        [
          for (final field in _fields)
            if (query.isEmpty
                ? _categoryOf(field) == category
                : _matches(field, query))
              field,
        ]..sort(
          (a, b) => (guideOrder['${a['key']}'] ?? 9999).compareTo(
            guideOrder['${b['key']}'] ?? 9999,
          ),
        );
    final categories = [
      for (final c in guideCategories)
        if (counts.containsKey(c.id)) c,
    ];
    final size = MediaQuery.sizeOf(context);
    final compact = size.width < 820;
    return PopScope(
      canPop: !busy,
      child: Dialog(
        backgroundColor: Kiosk.canvas,
        insetPadding: EdgeInsets.all(compact ? 8 : 24),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
        child: SizedBox(
          width: math.min(1140, size.width),
          height: math.min(800, size.height),
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(28, 24, 28, 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('설정', style: Kiosk.title),
                    const SizedBox(height: 4),
                    const Text(
                      '설정을 바꾸면 문서가 어떻게 달라지는지 예시로 보여 드려요.',
                      style: Kiosk.body,
                    ),
                    const SizedBox(height: 14),
                    TextField(
                      controller: search,
                      onChanged: (_) => setState(() {}),
                      style: const TextStyle(fontSize: 16),
                      decoration: InputDecoration(
                        prefixIcon: const Icon(
                          Icons.search,
                          color: Kiosk.faint,
                        ),
                        hintText: '설정 찾기 (예: 내어쓰기, 자간, 표)',
                        labelText: '설정 검색',
                        filled: true,
                        fillColor: Colors.white,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(14),
                          borderSide: BorderSide.none,
                        ),
                      ),
                    ),
                    if (busy)
                      const Padding(
                        padding: EdgeInsets.only(top: 8),
                        child: LinearProgressIndicator(),
                      ),
                    if (error != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 8),
                        child: Text(
                          error!,
                          style: const TextStyle(
                            color: Kiosk.red,
                            fontSize: 14,
                          ),
                        ),
                      ),
                    if (snapshot?['running'] == true)
                      const Padding(
                        padding: EdgeInsets.only(top: 8),
                        child: Text(
                          '작업 중에는 설정을 바꿀 수 없어요.',
                          style: TextStyle(color: Kiosk.red),
                        ),
                      ),
                  ],
                ),
              ),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: compact
                      ? Column(
                          children: [
                            SizedBox(
                              height: 62,
                              child: ListView(
                                scrollDirection: Axis.horizontal,
                                children: [
                                  for (final c in categories)
                                    _categoryTile(c, counts[c.id] ?? 0, true),
                                  for (final c in _panelCategories)
                                    _categoryTile(c, -1, true),
                                ],
                              ),
                            ),
                            Expanded(child: _body(visible, locked, query)),
                          ],
                        )
                      : Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            SizedBox(
                              width: 240,
                              child: ListView(
                                children: [
                                  for (final c in categories)
                                    _categoryTile(c, counts[c.id] ?? 0, false),
                                  const Padding(
                                    padding: EdgeInsets.fromLTRB(6, 8, 0, 8),
                                    child: Text('관리', style: Kiosk.caption),
                                  ),
                                  for (final c in _panelCategories)
                                    _categoryTile(c, -1, false),
                                ],
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(child: _body(visible, locked, query)),
                            if (_showsTypeset(query)) ...[
                              const SizedBox(width: 12),
                              SizedBox(width: 400, child: _typesetPane()),
                            ],
                          ],
                        ),
                ),
              ),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.fromLTRB(24, 14, 24, 18),
                decoration: const BoxDecoration(
                  color: Colors.white,
                  border: Border(top: BorderSide(color: Kiosk.line)),
                  borderRadius: BorderRadius.vertical(
                    bottom: Radius.circular(24),
                  ),
                ),
                child: Wrap(
                  alignment: WrapAlignment.end,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  spacing: 10,
                  runSpacing: 10,
                  children: [
                    const Text('개발자 도토리만두', style: Kiosk.caption),
                    const SizedBox(width: 12),
                    Text(
                      changed.isEmpty
                          ? '바꾼 설정이 없어요'
                          : '바꾼 설정 ${changed.length}개',
                      style: TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w600,
                        color: changed.isEmpty ? Kiosk.faint : Kiosk.blue,
                      ),
                    ),
                    const SizedBox(width: 8),
                    KioskSecondaryButton(
                      label: '기본값 복원',
                      onPressed: locked || snapshot == null
                          ? null
                          : restoreDefaults,
                    ),
                    if (error != null)
                      KioskSecondaryButton(
                        label: '다시 불러오기',
                        onPressed: busy ? null : load,
                      ),
                    KioskSecondaryButton(
                      label: '취소',
                      onPressed: busy
                          ? null
                          : () => Navigator.pop(context, false),
                    ),
                    KioskPrimaryButton(
                      label: '변경사항 적용',
                      onPressed: locked || changed.isEmpty ? null : save,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  /// 문서 모양에 닿는 분류에서만 한/글 조판 미리보기를 옆에 둔다(상용구·앱 정보·작업 카드 제외).
  bool _showsTypeset(String query) =>
      snapshot != null &&
      (query.isNotEmpty ||
          const {
            'report',
            'paragraph',
            'sentence',
            'table',
            'font',
          }.contains(category));

  /// 방금 바꾼 설정에 맞는 적용 전·후 예시 그림(1.80.3, rhwp 조판 미리보기 대체).
  Widget _typesetPane() => ListView(
    padding: const EdgeInsets.only(bottom: 16),
    children: [
      Container(
        padding: const EdgeInsets.all(16),
        decoration: Kiosk.cardBox(),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('적용 전·후 예시', style: Kiosk.cardTitle),
            const SizedBox(height: 4),
            Text(
              lastKey == null
                  ? '설정이 문서에 어떻게 반영되는지 예시로 보여 드려요. 그림을 누르면 크게 볼 수 있어요.'
                  : '방금 바꾼 설정과 관련된 예시예요. 그림을 누르면 크게 볼 수 있어요.',
              style: Kiosk.caption,
            ),
            const SizedBox(height: 12),
            OptionImagePreview(
              key: ValueKey('settings-option-image-${lastKey ?? ''}'),
              lastKey,
              fallback: optionImages['settings'],
            ),
          ],
        ),
      ),
    ],
  );

  /// 오른쪽 내용: 설정 값 목록, 또는 상용구·앱 정보 관리 화면(검색 중이면 설정 값 목록).
  Widget _body(List<Map> visible, bool locked, String query) {
    if (query.isEmpty && category == 'idiom_text') {
      return IdiomPanel(
        key: const ValueKey('idiom-text'),
        api: widget.api,
        body: false,
        locked: snapshot?['running'] == true,
      );
    }
    if (query.isEmpty && category == 'idiom_body') {
      return IdiomPanel(
        key: const ValueKey('idiom-body'),
        api: widget.api,
        body: true,
        locked: snapshot?['running'] == true,
      );
    }
    if (query.isEmpty && category == 'about') {
      return AppInfoPanel(version: snapshot?['version'] as String?);
    }
    return _list(visible, locked, query);
  }

  Widget _list(List<Map> visible, bool locked, String query) {
    if (visible.isEmpty) {
      return Center(
        child: Text(
          query.isEmpty ? '이 분류에는 설정이 없어요.' : '“$query”와 맞는 설정이 없어요.',
          style: Kiosk.body,
        ),
      );
    }
    return ListView(
      padding: const EdgeInsets.only(bottom: 16),
      children: [for (final field in visible) _card(field, locked)],
    );
  }
}
