import 'dart:math' as math;

import 'package:flutter/material.dart';

/// Filee의 플로팅 도넛 선택 방식을 Flutter로 구현한다.
/// 각 조각의 실제 경로로 클릭 영역을 제한해 인접 포맷이 잘못 선택되지 않는다.
class FloatingFormatPicker extends StatefulWidget {
  const FloatingFormatPicker({
    super.key,
    required this.targets,
    required this.selected,
    required this.fileCount,
    required this.onSelected,
    required this.onCancel,
  });

  final List<Map> targets;
  final String selected;
  final int fileCount;
  final ValueChanged<String> onSelected;
  final VoidCallback onCancel;

  @override
  State<FloatingFormatPicker> createState() => _FloatingFormatPickerState();
}

class _FloatingFormatPickerState extends State<FloatingFormatPicker> {
  String? hovered;
  static const formats = ['hwpx', 'docx', 'epub', 'pdf', 'jpg', 'png'];
  static const accent = Color(0xff7664ec);

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
    'docx' => Icons.article_outlined,
    'epub' => Icons.menu_book_outlined,
    'jpg' || 'png' => Icons.image_outlined,
    _ => Icons.description_outlined,
  };

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
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 12),
          LayoutBuilder(
            builder: (context, constraints) {
              final side = math.min(340.0, constraints.maxWidth);
              final center = Offset(side / 2, side / 2);
              final labelRadius = side * .345;
              return SizedBox(
                width: side,
                height: side,
                child: Stack(
                  children: [
                    Positioned.fill(child: CustomPaint(painter: _RingShadow())),
                    for (var i = 0; i < formats.length; i++)
                      Positioned.fill(
                        child: Builder(
                          builder: (context) {
                            final format = formats[i];
                            final target = info(format);
                            final enabled = target['enabled'] == true;
                            final hot = hovered == format;
                            final selected = widget.selected == format;
                            final angle = -math.pi / 2 + i * 2 * math.pi / formats.length;
                            final label =
                                center +
                                Offset(math.cos(angle), math.sin(angle)) *
                                    labelRadius;
                            final foreground = hot && enabled
                                ? Colors.white
                                : enabled
                                ? const Color(0xff25324a)
                                : const Color(0xff8a94a6);
                            return ClipPath(
                              clipper: _SliceClipper(index: i, count: formats.length),
                              child: Material(
                                color: hot && enabled
                                    ? accent
                                    : selected && enabled
                                    ? const Color(0xffe9e5ff)
                                    : enabled
                                    ? Colors.white
                                    : const Color(0xffedf0f5),
                                child: Tooltip(
                                  message: enabled
                                      ? '${target['label']} 선택'
                                      : '${target['reason']}',
                                  child: Semantics(
                                    selected: selected,
                                    enabled: enabled,
                                    button: true,
                                    label: '${target['label']} 변환',
                                    child: InkWell(
                                      key: Key('conversionSlice-$format'),
                                      onHover: (on) => setState(
                                        () => hovered = on ? format : null,
                                      ),
                                      onFocusChange: (on) => setState(
                                        () => hovered = on ? format : null,
                                      ),
                                      onTap: enabled
                                          ? () => widget.onSelected(format)
                                          : null,
                                      child: Stack(
                                        children: [
                                          Positioned(
                                            left: label.dx - 40,
                                            top: label.dy - 33,
                                            width: 80,
                                            height: 66,
                                            child: Column(
                                              mainAxisAlignment:
                                                  MainAxisAlignment.center,
                                              children: [
                                                Icon(
                                                  icon(format),
                                                  color: foreground,
                                                  size: 25,
                                                ),
                                                const SizedBox(height: 5),
                                                Text(
                                                  '${target['label']}',
                                                  style: TextStyle(
                                                    color: foreground,
                                                    fontSize: 15,
                                                    fontWeight: FontWeight.w700,
                                                  ),
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
                          },
                        ),
                      ),
                    Positioned(
                      left: side * .295,
                      top: side * .295,
                      width: side * .41,
                      height: side * .41,
                      child: Material(
                        color: Colors.white,
                        shape: const CircleBorder(),
                        clipBehavior: Clip.antiAlias,
                        child: InkWell(
                          key: const Key('cancelConversionPicker'),
                          onTap: widget.onCancel,
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Text(
                                '${widget.fileCount}개 파일',
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: Color(0xff64748b),
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                '${activeInfo['label']}',
                                style: const TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                              const SizedBox(height: 8),
                              const Icon(
                                Icons.close_rounded,
                                size: 19,
                                color: Color(0xff64748b),
                              ),
                              const Text(
                                '취소',
                                style: TextStyle(
                                  fontSize: 11,
                                  color: Color(0xff64748b),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
          const SizedBox(height: 12),
          Text(
            '${activeInfo['reason'] ?? ''}',
            key: const Key('conversionPrerequisiteNotice'),
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 12,
              height: 1.5,
              color: activeInfo['enabled'] == true
                  ? const Color(0xff64748b)
                  : const Color(0xff9a3412),
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            '포맷을 클릭해 선택 · 가운데 또는 Esc로 취소',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 11, color: Color(0xff64748b)),
          ),
        ],
      ),
    );
  }
}

class _SliceClipper extends CustomClipper<Path> {
  const _SliceClipper({required this.index, required this.count});
  final int index, count;

  @override
  Path getClip(Size size) {
    final center = size.center(Offset.zero);
    final outer = math.min(size.width, size.height) / 2 - 8;
    final inner = outer * .43;
    const gap = .025;
    // 조각 수에 맞춰 같은 각도로 나눈다. 각 조각은 라벨 각도를 가운데에 둔다.
    final step = 2 * math.pi / count;
    final start = -math.pi / 2 - step / 2 + index * step + gap;
    final sweep = step - gap * 2;
    final end = start + sweep;
    return Path()
      ..moveTo(
        center.dx + outer * math.cos(start),
        center.dy + outer * math.sin(start),
      )
      ..arcTo(
        Rect.fromCircle(center: center, radius: outer),
        start,
        sweep,
        false,
      )
      ..lineTo(
        center.dx + inner * math.cos(end),
        center.dy + inner * math.sin(end),
      )
      ..arcTo(
        Rect.fromCircle(center: center, radius: inner),
        end,
        -sweep,
        false,
      )
      ..close();
  }

  @override
  bool shouldReclip(_SliceClipper oldClipper) =>
      oldClipper.index != index || oldClipper.count != count;
}

class _RingShadow extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final path = Path()
      ..addOval(
        Rect.fromCircle(
          center: size.center(Offset.zero),
          radius: math.min(size.width, size.height) / 2 - 8,
        ),
      );
    canvas.drawShadow(path, const Color(0x500f172a), 12, false);
  }

  @override
  bool shouldRepaint(_RingShadow oldDelegate) => false;
}
