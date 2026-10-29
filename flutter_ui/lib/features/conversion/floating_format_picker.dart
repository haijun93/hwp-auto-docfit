import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// 변환 포맷을 키보드 숫자패드 모양의 사각 키패드로 고른다.
/// 칸 위치가 숫자 키와 같아 마우스·숫자 키 어느 쪽으로도 고를 수 있다.
class FloatingFormatPicker extends StatefulWidget {
  const FloatingFormatPicker({
    super.key,
    required this.targets,
    required this.selected,
    required this.fileCount,
    required this.fileNames,
    required this.onSelected,
    required this.onCancel,
  });

  final List<Map> targets;
  final String selected;
  final int fileCount;
  final List<String> fileNames;
  final ValueChanged<String> onSelected;
  final VoidCallback onCancel;

  @override
  State<FloatingFormatPicker> createState() => _FloatingFormatPickerState();
}

class _FloatingFormatPickerState extends State<FloatingFormatPicker> {
  String? hovered;

  /// 키보드 숫자패드 배열(2026-10-29 사용자 요청: 원형 → 번호 키패드형 사각 배열).
  /// 가운데 5번 자리는 원본 파일·취소 칸이다. 줄마다 문서 / 웹·텍스트 / PDF / 그림·텍스트.
  static const keypad = <(String, String?)>[
    ('7', 'hwpx'),
    ('8', 'docx'),
    ('9', 'epub'),
    ('4', 'html'),
    ('5', null),
    ('6', 'md'),
    ('1', 'pdf'),
    ('2', 'pdfz'),
    ('3', 'pdfm'),
    ('0', 'jpg'),
    ('.', 'png'),
    ('+', 'txt'),
  ];
  static const accent = Color(0xff7664ec);
  static const _digits = [
    LogicalKeyboardKey.digit0,
    LogicalKeyboardKey.digit1,
    LogicalKeyboardKey.digit2,
    LogicalKeyboardKey.digit3,
    LogicalKeyboardKey.digit4,
    LogicalKeyboardKey.digit5,
    LogicalKeyboardKey.digit6,
    LogicalKeyboardKey.digit7,
    LogicalKeyboardKey.digit8,
    LogicalKeyboardKey.digit9,
  ];
  /// 숫자패드는 물리 키 위치로 본다 — NumLock이 꺼져 있으면 숫자패드 1이 End로 들어와
  /// 고를 수 없던 문제(2026-10-29 실제 앱 시험).
  static const _numpad = [
    PhysicalKeyboardKey.numpad0,
    PhysicalKeyboardKey.numpad1,
    PhysicalKeyboardKey.numpad2,
    PhysicalKeyboardKey.numpad3,
    PhysicalKeyboardKey.numpad4,
    PhysicalKeyboardKey.numpad5,
    PhysicalKeyboardKey.numpad6,
    PhysicalKeyboardKey.numpad7,
    PhysicalKeyboardKey.numpad8,
    PhysicalKeyboardKey.numpad9,
  ];

  @override
  void initState() {
    super.initState();
    HardwareKeyboard.instance.addHandler(_onKey);
  }

  @override
  void dispose() {
    HardwareKeyboard.instance.removeHandler(_onKey);
    super.dispose();
  }

  /// 숫자 키(윗줄·숫자패드 모두)로 칸을 고른다. 5는 취소.
  bool _onKey(KeyEvent event) {
    if (event is! KeyDownEvent) return false;
    final key = _keyLabel(event.physicalKey, event.logicalKey);
    if (key == null) return false;
    final format = keypad.firstWhere((cell) => cell.$1 == key).$2;
    if (format == null) {
      widget.onCancel();
    } else {
      _press(format);
    }
    return true;
  }

  static String? _keyLabel(
    PhysicalKeyboardKey physical,
    LogicalKeyboardKey logical,
  ) {
    final shift = HardwareKeyboard.instance.isShiftPressed;
    final numpad = _numpad.indexOf(physical);
    if (numpad >= 0) return '$numpad';
    if (physical == PhysicalKeyboardKey.numpadDecimal ||
        logical == LogicalKeyboardKey.numpadDecimal ||
        logical == LogicalKeyboardKey.period) {
      return '.';
    }
    if (physical == PhysicalKeyboardKey.numpadAdd ||
        logical == LogicalKeyboardKey.numpadAdd ||
        logical == LogicalKeyboardKey.add ||
        (shift && logical == LogicalKeyboardKey.equal)) {
      return '+';
    }
    if (shift) return null;
    final digit = _digits.indexOf(logical);
    return digit >= 0 ? '$digit' : null;
  }

  void _press(String format) {
    if (info(format)['enabled'] == true) {
      widget.onSelected(format);
    } else {
      // 고를 수 없는 칸도 누르면 아래쪽에 그 칸의 이유를 보여 준다(누르기 전 선택 형식의 이유가
      // 남아 'PDF 압축'에 'HWPX 같은 형식' 안내가 보이던 문제, 2026-10-23 사용자 실측).
      setState(() => hovered = format);
    }
  }

  Map info(String format) => widget.targets.firstWhere(
    (item) => item['format'] == format,
    orElse: () => {
      'format': format,
      'label': format.toUpperCase(),
      'enabled': false,
      'reason': '변환할 문서를 추가하세요.',
    },
  );

  IconData icon(String format) => switch (format) {
    'pdf' => Icons.picture_as_pdf_outlined,
    'pdfz' => Icons.compress,
    'pdfm' => Icons.merge_type,
    'docx' => Icons.article_outlined,
    'epub' => Icons.menu_book_outlined,
    'jpg' || 'png' => Icons.image_outlined,
    _ => Icons.description_outlined,
  };

  /// 칸 이름이 길면 낱말 경계에서 두 줄로 나눈다('PDF 하나로 합치기' → 'PDF 하나로' / '합치기').
  static String _sliceLabel(String label) {
    if (label.length <= 6 || label.contains('\n')) return label;
    final words = label.split(' ');
    if (words.length < 2) return label;
    var best = 1;
    var bestDiff = 1 << 30;
    for (var i = 1; i < words.length; i++) {
      final left = words.sublist(0, i).join(' ').length;
      final right = words.sublist(i).join(' ').length;
      final diff = (left - right).abs();
      if (diff <= bestDiff) {
        best = i;
        bestDiff = diff;
      }
    }
    return '${words.sublist(0, best).join(' ')}\n${words.sublist(best).join(' ')}';
  }

  /// 키 윗면 왼쪽 위의 숫자 각인.
  Widget _keyLegend(String key, Color color) => Positioned(
    left: 7,
    top: 4,
    child: ExcludeSemantics(
      child: Text(
        key,
        style: TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.w800,
          color: color.withValues(alpha: .65),
        ),
      ),
    ),
  );

  Widget _formatKey(String key, String format, double height) {
    final target = info(format);
    final enabled = target['enabled'] == true;
    final hot = hovered == format;
    final selected = widget.selected == format;
    final foreground = hot && enabled
        ? Colors.white
        : enabled
        ? const Color(0xff25324a)
        : const Color(0xff8a94a6);
    return Material(
      color: hot && enabled
          ? accent
          : selected && enabled
          ? const Color(0xffe9e5ff)
          : enabled
          ? Colors.white
          : const Color(0xffedf0f5),
      elevation: hot && enabled ? 5 : 2,
      shadowColor: const Color(0x500f172a),
      borderRadius: BorderRadius.circular(10),
      clipBehavior: Clip.antiAlias,
      child: Tooltip(
        message: enabled ? '${target['label']} 선택' : '${target['reason']}',
        child: Semantics(
          selected: selected,
          enabled: enabled,
          button: true,
          label: '${target['label']} 변환',
          child: InkWell(
            key: Key('conversionSlice-$format'),
            onHover: (on) => setState(() => hovered = on ? format : null),
            onFocusChange: (on) =>
                setState(() => hovered = on ? format : null),
            onTap: () => _press(format),
            child: SizedBox(
              height: height,
              child: Stack(
                children: [
                  _keyLegend(key, foreground),
                  Positioned.fill(
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(4, 12, 4, 4),
                      child: FittedBox(
                        fit: BoxFit.scaleDown,
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(icon(format), color: foreground, size: 24),
                            const SizedBox(height: 3),
                            // 긴 이름(예: 'PDF 하나로 합치기')은 낱말 단위로 두 줄, 가운데 정렬 —
                            // 칸이 좁아 'PDF 하나로 합치' / '기'로 끊기던 문제(2026-10-23 사용자 실측).
                            Text(
                              _sliceLabel('${target['label']}'),
                              textAlign: TextAlign.center,
                              maxLines: 2,
                              softWrap: true,
                              style: TextStyle(
                                color: foreground,
                                fontSize: 11,
                                height: 1.15,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ],
                        ),
                      ),
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

  Widget _cancelKey(String key, double height) {
    const muted = Color(0xff64748b);
    return Material(
      color: const Color(0xfff1f5f9),
      elevation: 2,
      shadowColor: const Color(0x500f172a),
      borderRadius: BorderRadius.circular(10),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        key: const Key('cancelConversionPicker'),
        onTap: widget.onCancel,
        child: SizedBox(
          height: height,
          child: Stack(
            children: [
              _keyLegend(key, muted),
              Positioned.fill(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(4, 4, 4, 3),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        widget.fileCount > 1
                            ? '첫 파일 · ${widget.fileCount}개'
                            : '${widget.fileCount}개 파일',
                        maxLines: 1,
                        style: const TextStyle(fontSize: 9, color: muted),
                      ),
                      const SizedBox(height: 1),
                      _SourceFileName(
                        name: widget.fileNames.isEmpty
                            ? '원본 파일'
                            : widget.fileNames.first,
                      ),
                      const SizedBox(height: 1),
                      const Icon(Icons.close_rounded, size: 16, color: muted),
                      const Text(
                        '취소',
                        style: TextStyle(fontSize: 9, color: muted),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final active = hovered ?? widget.selected;
    final activeInfo = info(active);
    return Material(
      type: MaterialType.transparency,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text(
            '변환할 포맷을 고르세요',
            style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 8),
          LayoutBuilder(
            builder: (context, constraints) {
              // 키패드 폭은 357까지(2026-10-29 사용자 요청: 510에서 30% 축소).
              final side = math.min(357.0, constraints.maxWidth);
              const gap = 6.0;
              final cellHeight = math.max(66.0, (side - gap * 2) / 3 * .66);
              return SizedBox(
                key: const Key('conversionKeypad'),
                width: side,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    for (var row = 0; row < 4; row++) ...[
                      if (row > 0) const SizedBox(height: gap),
                      Row(
                        children: [
                          for (var col = 0; col < 3; col++) ...[
                            if (col > 0) const SizedBox(width: gap),
                            Expanded(
                              child: switch (keypad[row * 3 + col]) {
                                (final key, final String format) => _formatKey(
                                  key,
                                  format,
                                  cellHeight,
                                ),
                                (final key, _) => _cancelKey(key, cellHeight),
                              },
                            ),
                          ],
                        ],
                      ),
                    ],
                  ],
                ),
              );
            },
          ),
          const SizedBox(height: 8),
          Text(
            activeInfo['enabled'] == true
                ? '변환 결과: ${activeInfo['label']}'
                : '고를 수 없음: ${activeInfo['label']}',
            key: const Key('conversionSelectedOutput'),
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 4),
          Text(
            '${activeInfo['reason'] ?? ''}',
            key: const Key('conversionPrerequisiteNotice'),
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 11,
              height: 1.4,
              color: activeInfo['enabled'] == true
                  ? const Color(0xff64748b)
                  : const Color(0xff9a3412),
            ),
          ),
          const SizedBox(height: 6),
          const Text(
            '포맷을 누르거나 숫자 키로 바로 변환해요 · 5번 또는 Esc로 취소',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 10, color: Color(0xff64748b)),
          ),
        ],
      ),
    );
  }
}

/// Keep the source extension visible while ellipsizing only the file stem.
class _SourceFileName extends StatelessWidget {
  const _SourceFileName({required this.name});
  final String name;

  @override
  Widget build(BuildContext context) {
    final filename = name.split(RegExp(r'[/\\]')).last;
    final dot = filename.lastIndexOf('.');
    final stem = dot > 0 ? filename.substring(0, dot) : filename;
    final extension = dot > 0 ? filename.substring(dot) : '';
    return Tooltip(
      message: filename,
      excludeFromSemantics: true,
      child: Semantics(
        key: const Key('conversionSourceName'),
        label: filename,
        child: ExcludeSemantics(
          child: DefaultTextStyle(
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w800,
              color: Color(0xff25324a),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Flexible(
                  child: Text(
                    stem,
                    key: const Key('conversionSourceStem'),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    softWrap: false,
                  ),
                ),
                if (extension.isNotEmpty)
                  Text(extension, key: const Key('conversionSourceExtension')),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
