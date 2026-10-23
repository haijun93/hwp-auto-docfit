import 'dart:math' as math;
import 'package:flutter/material.dart';

import '../settings/kiosk_theme.dart';

/// 한/글 「편집 용지」(Alt+L) 대화상자 스타일의 쪽 모양·여백 위젯.
class PageMarginLayout extends StatelessWidget {
  const PageMarginLayout({
    super.key = const Key('pageMarginLayout'),
    required this.node,
    required this.edits,
    required this.generation,
    required this.busy,
    required this.onEdit,
  });

  final Map node;
  final Map<String, Map> edits;
  final int generation;
  final bool busy;
  final void Function(List path, Map field, String value) onEdit;

  Map? _findField(String key) {
    final fields = node['fields'] as List? ?? const [];
    for (final f in fields) {
      if (f is Map && f['key'] == key) return f;
    }
    return null;
  }

  String _currentValue(Map field) {
    final path = node['path'];
    final key = field['key'];
    return '${edits['$path:$key']?['value'] ?? field['value'] ?? ''}';
  }

  String _currentValueByKey(String key) {
    final field = _findField(key);
    if (field == null) return '';
    return _currentValue(field);
  }

  double _parseMm(String? text, {double fallback = 0.0}) {
    if (text == null || text.isEmpty) return fallback;
    final match = RegExp(r'-?\d+(\.\d+)?').firstMatch(text);
    if (match == null) return fallback;
    return double.tryParse(match.group(0)!) ?? fallback;
  }

  void _step(Map field, double delta) {
    final path = node['path'] as List? ?? const ['page'];
    final current = _currentValue(field);
    final numVal = _parseMm(current, fallback: 0.0);
    final rounded = ((numVal * 10).round() + (delta * 10).round()) / 10.0;
    final nextVal = math.max(0.0, rounded);
    final formatted = '${nextVal.toStringAsFixed(1)}mm';
    onEdit(path, field, formatted);
  }

  Widget _buildOrientationBadge({
    required String label,
    required IconData icon,
    required bool isSelected,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: isSelected ? Kiosk.blueSoft : const Color(0xfff2f4f6),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: isSelected ? Kiosk.blue : const Color(0xffd5d9de),
          width: isSelected ? 1.5 : 1.0,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            size: 16,
            color: isSelected ? Kiosk.blue : Kiosk.sub,
          ),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 13,
              fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
              color: isSelected ? Kiosk.blue : Kiosk.sub,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPaper({
    required double width,
    required double height,
    required bool isLandscape,
  }) {
    final topMm = _parseMm(_currentValueByKey('page_top'), fallback: 15.0);
    final bottomMm = _parseMm(_currentValueByKey('page_bottom'), fallback: 15.0);
    final leftMm = _parseMm(_currentValueByKey('page_left'), fallback: 20.0);
    final rightMm = _parseMm(_currentValueByKey('page_right'), fallback: 20.0);
    final headerMm = _parseMm(_currentValueByKey('page_header'), fallback: 10.0);
    final footerMm = _parseMm(_currentValueByKey('page_footer'), fallback: 10.0);
    final gutterMm = _parseMm(_currentValueByKey('page_gutter'), fallback: 0.0);

    final refWidth = isLandscape ? 297.0 : 210.0;
    final refHeight = isLandscape ? 210.0 : 297.0;

    final scaleX = width / refWidth;
    final scaleY = height / refHeight;

    final padLeft = ((leftMm + gutterMm) * scaleX).clamp(2.0, width * 0.38);
    final padRight = (rightMm * scaleX).clamp(2.0, width * 0.38);
    final padTop = ((topMm + headerMm * 0.5) * scaleY).clamp(2.0, height * 0.38);
    final padBottom = ((bottomMm + footerMm * 0.5) * scaleY).clamp(2.0, height * 0.38);

    return Container(
      key: const Key('pageMarginPaper'),
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(2),
        border: Border.all(color: const Color(0xffb0b8c1), width: 1.2),
        boxShadow: const [
          BoxShadow(
            color: Color(0x18000000),
            blurRadius: 6,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Padding(
        padding: EdgeInsets.fromLTRB(padLeft, padTop, padRight, padBottom),
        child: Container(
          decoration: BoxDecoration(
            color: const Color(0xfff6f8fa),
            border: Border.all(color: const Color(0xffdbe0e6), width: 0.8),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              for (int i = 0; i < 6; i++)
                Container(
                  height: 1.5,
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  color: const Color(0xffced4da),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMarginBox(String key, String label, double width) {
    final field = _findField(key);
    if (field == null) {
      return const SizedBox.shrink();
    }
    final path = node['path'] as List? ?? const ['page'];
    final valStr = _currentValue(field);
    final isChanged = edits.containsKey('$path:$key');
    final editable = !busy && field['editable'] == true;

    return Container(
      key: Key('pageMargin_$key'),
      width: width,
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
      decoration: BoxDecoration(
        color: isChanged ? Kiosk.blueSoft : Colors.white,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: isChanged ? Kiosk.blue : const Color(0xffd0d5dc),
          width: isChanged ? 1.5 : 1.0,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: isChanged ? Kiosk.blue : Kiosk.ink,
            ),
          ),
          const SizedBox(height: 4),
          Row(
            children: [
              Expanded(
                child: SizedBox(
                  height: 32,
                  child: TextFormField(
                    key: ValueKey('$generation:$path:$key:$valStr'),
                    initialValue: valStr,
                    enabled: editable,
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: Kiosk.ink,
                    ),
                    decoration: InputDecoration(
                      isDense: true,
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 6,
                        vertical: 6,
                      ),
                      filled: true,
                      fillColor: editable
                          ? const Color(0xfff2f4f6)
                          : const Color(0xfff9fafb),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(6),
                        borderSide: BorderSide.none,
                      ),
                    ),
                    onChanged: (text) => onEdit(path, field, text),
                  ),
                ),
              ),
              const SizedBox(width: 2),
              Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Material(
                    color: Colors.transparent,
                    child: InkWell(
                      key: Key('pageMarginUp_$key'),
                      borderRadius: BorderRadius.circular(4),
                      onTap: editable ? () => _step(field, 0.1) : null,
                      child: const Padding(
                        padding: EdgeInsets.symmetric(horizontal: 2),
                        child: Icon(
                          Icons.arrow_drop_up,
                          size: 16,
                          color: Kiosk.ink,
                        ),
                      ),
                    ),
                  ),
                  Material(
                    color: Colors.transparent,
                    child: InkWell(
                      key: Key('pageMarginDown_$key'),
                      borderRadius: BorderRadius.circular(4),
                      onTap: editable ? () => _step(field, -0.1) : null,
                      child: const Padding(
                        padding: EdgeInsets.symmetric(horizontal: 2),
                        child: Icon(
                          Icons.arrow_drop_down,
                          size: 16,
                          color: Kiosk.ink,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final widthField = _findField('page_width');
    final heightField = _findField('page_height');
    final landscapeField = _findField('page_landscape');

    final widthVal = widthField != null
        ? _parseMm(_currentValue(widthField), fallback: 210.0)
        : 210.0;
    final heightVal = heightField != null
        ? _parseMm(_currentValue(heightField), fallback: 297.0)
        : 297.0;
    final isLandscape =
        landscapeField != null && _currentValue(landscapeField) == '예';

    return Container(
      decoration: Kiosk.cardBox(),
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 맨 위 「용지 종류」 및 「용지 방향」 (읽기 전용)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: const Color(0xfff8f9fa),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xffe9ecef)),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        '용지 종류',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: Kiosk.ink,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '폭 ${widthVal.toStringAsFixed(1)} mm · 길이 ${heightVal.toStringAsFixed(1)} mm',
                        style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                          color: Kiosk.sub,
                        ),
                      ),
                    ],
                  ),
                ),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    _buildOrientationBadge(
                      label: '세로',
                      icon: Icons.stay_current_portrait,
                      isSelected: !isLandscape,
                    ),
                    const SizedBox(width: 6),
                    _buildOrientationBadge(
                      label: '가로',
                      icon: Icons.stay_current_landscape,
                      isSelected: isLandscape,
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            '용지 여백',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w700,
              color: Kiosk.ink,
            ),
          ),
          const SizedBox(height: 12),
          LayoutBuilder(
            builder: (context, constraints) {
              final isNarrow = constraints.maxWidth < 480;
              final isVeryNarrow = constraints.maxWidth < 360;

              final baseW = isNarrow ? 90.0 : 130.0;
              final baseH = isNarrow ? 120.0 : 170.0;
              final paperW = isLandscape ? baseH : baseW;
              final paperH = isLandscape ? baseW : baseH;

              final boxW = isNarrow ? 102.0 : 124.0;
              final gap = isNarrow ? 6.0 : 12.0;

              final paperWidget = _buildPaper(
                width: paperW,
                height: paperH,
                isLandscape: isLandscape,
              );

              final topBoxes = Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  _buildMarginBox('page_top', '위쪽', boxW),
                  const SizedBox(height: 6),
                  _buildMarginBox('page_header', '머리말', boxW),
                ],
              );

              final leftBoxes = Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  _buildMarginBox('page_left', '왼쪽', boxW),
                  const SizedBox(height: 6),
                  _buildMarginBox('page_gutter', '제본', boxW),
                ],
              );

              final rightBoxes = Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  _buildMarginBox('page_right', '오른쪽', boxW),
                ],
              );

              final bottomBoxes = Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  _buildMarginBox('page_footer', '꼬리말', boxW),
                  const SizedBox(height: 6),
                  _buildMarginBox('page_bottom', '아래쪽', boxW),
                ],
              );

              Widget marginContent;
              if (isVeryNarrow) {
                // 아주 좁으면 세로로 배치
                marginContent = Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    topBoxes,
                    const SizedBox(height: 8),
                    paperWidget,
                    const SizedBox(height: 8),
                    leftBoxes,
                    const SizedBox(height: 6),
                    rightBoxes,
                    const SizedBox(height: 8),
                    bottomBoxes,
                  ],
                );
              } else {
                // 한/글 십자형 배치
                marginContent = Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    topBoxes,
                    SizedBox(height: gap),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        leftBoxes,
                        SizedBox(width: gap),
                        paperWidget,
                        SizedBox(width: gap),
                        rightBoxes,
                      ],
                    ),
                    SizedBox(height: gap),
                    bottomBoxes,
                  ],
                );
              }

              return Center(
                child: FittedBox(
                  fit: BoxFit.scaleDown,
                  child: marginContent,
                ),
              );
            },
          ),
        ],
      ),
    );
  }
}
