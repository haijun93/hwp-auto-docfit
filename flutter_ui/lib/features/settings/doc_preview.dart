import 'package:flutter/material.dart';

import 'kiosk_theme.dart';

/// 한글 문서처럼 보이는 작은 미리보기 부품들.
/// 설정값(크기 pt·자간 %·장평 %·내어쓰기·문단 위 간격·줄 간격)을 그대로 받아 그린다.
/// 화면용 글꼴은 앱에 들어 있는 한글 글꼴 하나라서, 실제 글꼴 이름은 캡션으로 알려 준다.
const double _ptToPx = 0.95;

class DocSpan {
  const DocSpan(
    this.text, {
    this.bold = false,
    this.mark,
    this.underline = false,
  });
  final String text;
  final bool bold;
  final bool underline;

  /// 바뀐 곳을 알려 주는 형광 표시 색.
  final Color? mark;
}

class DocPara {
  const DocPara({
    this.marker = '',
    this.spans = const [],
    this.size = 13,
    this.markerBold = false,
    this.markerSize,
    this.spacing = 0,
    this.ratio = 100,
    this.hanging = true,
    this.indentLevel = 0,
    this.spaceBefore = 0,
    this.lineSpacing = 160,
    this.align = TextAlign.left,
    this.lines,
    this.color = Kiosk.ink,
  });

  /// 항목기호(□, ㅇ, -, ※ …). 비우면 기호 없는 문단.
  final String marker;
  final List<DocSpan> spans;
  final double size;
  final bool markerBold;
  final double? markerSize;

  /// 자간 %(한글: 음수면 좁게).
  final double spacing;

  /// 장평 %(100 = 보통).
  final double ratio;

  /// 내어쓰기: 둘째 줄이 기호 다음 글자에 맞춰 시작한다.
  final bool hanging;
  final int indentLevel;

  /// 문단 위 간격(pt).
  final double spaceBefore;

  /// 줄 간격 %.
  final double lineSpacing;
  final TextAlign align;

  /// 줄바꿈 위치를 보여 줘야 하는 예시는 줄을 직접 나눠 준다.
  final List<List<DocSpan>>? lines;
  final Color color;
}

class DocParagraph extends StatelessWidget {
  const DocParagraph(this.para, {super.key});
  final DocPara para;

  TextStyle _style(DocSpan span) {
    final px = para.size * _ptToPx;
    return TextStyle(
      fontSize: px,
      height: (para.lineSpacing / 100).clamp(1.0, 3.0),
      letterSpacing: px * para.spacing / 100,
      fontWeight: span.bold ? FontWeight.w800 : FontWeight.w400,
      color: para.color,
      decoration: span.underline ? TextDecoration.underline : null,
      backgroundColor: span.mark,
    );
  }

  Widget _text(List<DocSpan> spans, {bool wrap = true}) => Text.rich(
    TextSpan(
      children: [
        for (final span in spans)
          TextSpan(text: span.text, style: _style(span)),
      ],
    ),
    textAlign: para.align,
    softWrap: wrap,
  );

  @override
  Widget build(BuildContext context) {
    final markerStyle = TextStyle(
      fontSize: (para.markerSize ?? para.size) * _ptToPx,
      height: (para.lineSpacing / 100).clamp(1.0, 3.0),
      fontWeight: para.markerBold ? FontWeight.w800 : FontWeight.w400,
      color: para.color,
    );
    Widget body;
    if (para.lines != null) {
      // 줄바꿈 위치가 예시의 핵심이므로 줄을 접지 않고, 종이보다 길면 통째로 조금 줄여 보인다.
      body = FittedBox(
        fit: BoxFit.scaleDown,
        alignment: Alignment.topLeft,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (var i = 0; i < para.lines!.length; i++)
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (para.marker.isNotEmpty)
                    Opacity(
                      // 내어쓰기면 둘째 줄부터 기호 자리만큼 비워 글자 시작을 맞춘다.
                      opacity: i == 0 ? 1 : 0,
                      child: i == 0 || para.hanging
                          ? Text('${para.marker} ', style: markerStyle)
                          : const SizedBox.shrink(),
                    ),
                  _text(para.lines![i], wrap: false),
                ],
              ),
          ],
        ),
      );
    } else if (para.marker.isNotEmpty && para.hanging) {
      body = Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('${para.marker} ', style: markerStyle),
          Expanded(child: _text(para.spans)),
        ],
      );
    } else {
      body = Text.rich(
        TextSpan(
          children: [
            if (para.marker.isNotEmpty)
              TextSpan(text: '${para.marker} ', style: markerStyle),
            for (final span in para.spans)
              TextSpan(text: span.text, style: _style(span)),
          ],
        ),
        textAlign: para.align,
      );
    }
    if (para.ratio != 100) {
      body = _Squeeze(ratio: para.ratio / 100, child: body);
    }
    return Padding(
      padding: EdgeInsets.only(
        left: 14.0 * para.indentLevel,
        top: para.spaceBefore * _ptToPx,
      ),
      child: body,
    );
  }
}

/// 장평: 글자 가로 폭만 줄이거나 늘린다(줄바꿈 폭도 함께 맞춘다).
class _Squeeze extends StatelessWidget {
  const _Squeeze({required this.ratio, required this.child});
  final double ratio;
  final Widget child;

  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, constraints) {
      final width = constraints.maxWidth.isFinite
          ? constraints.maxWidth
          : 300.0;
      return ClipRect(
        child: SizedBox(
          width: width,
          child: Align(
            alignment: Alignment.topLeft,
            widthFactor: 1,
            child: Transform.scale(
              scaleX: ratio,
              scaleY: 1,
              alignment: Alignment.topLeft,
              child: SizedBox(width: width / ratio, child: child),
            ),
          ),
        ),
      );
    },
  );
}

/// 흰 종이 한 장. 실제 문서의 쪽 여백 느낌을 낸다.
class DocPaper extends StatelessWidget {
  const DocPaper({
    super.key,
    required this.children,
    this.width = 300,
    this.caption,
  });
  final List<Widget> children;
  final double width;
  final String? caption;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    mainAxisSize: MainAxisSize.min,
    children: [
      Container(
        width: width,
        padding: const EdgeInsets.fromLTRB(18, 16, 18, 18),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: const Color(0xffdfe3e8)),
          boxShadow: const [
            BoxShadow(
              color: Color(0x14000000),
              blurRadius: 10,
              offset: Offset(0, 3),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: children,
        ),
      ),
      if (caption != null)
        Padding(
          padding: const EdgeInsets.only(top: 6),
          child: Text(caption!, style: Kiosk.caption),
        ),
    ],
  );
}

/// 작은 표 미리보기. 첫 행은 머리글이다.
class DocTable extends StatelessWidget {
  const DocTable({
    super.key,
    required this.rows,
    this.headerBold = true,
    this.headerFill = const Color(0xffeef1f5),
    this.headerSize = 12,
    this.bodySize = 11,
    this.bodyBold = false,
    this.spacing = 0,
    this.mark,
  });
  final List<List<String>> rows;
  final bool headerBold;
  final Color? headerFill;
  final double headerSize;
  final double bodySize;
  final bool bodyBold;
  final double spacing;
  final Color? mark;

  @override
  Widget build(BuildContext context) => Table(
    border: TableBorder.all(color: const Color(0xff4e5968), width: 0.8),
    defaultVerticalAlignment: TableCellVerticalAlignment.middle,
    children: [
      for (var r = 0; r < rows.length; r++)
        TableRow(
          decoration: BoxDecoration(color: r == 0 ? headerFill : null),
          children: [
            for (final cell in rows[r])
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 4),
                child: Text(
                  cell,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: (r == 0 ? headerSize : bodySize) * _ptToPx,
                    fontWeight: (r == 0 ? headerBold : bodyBold)
                        ? FontWeight.w800
                        : FontWeight.w400,
                    letterSpacing:
                        (r == 0 ? headerSize : bodySize) *
                        _ptToPx *
                        spacing /
                        100,
                    backgroundColor: r > 0 ? mark : null,
                    color: Kiosk.ink,
                  ),
                ),
              ),
          ],
        ),
    ],
  );
}

/// '끄면 / 켜면' 두 장을 나란히 놓고 지금 고른 쪽을 파란 테두리로 강조한다.
class BeforeAfter extends StatelessWidget {
  const BeforeAfter({
    super.key,
    required this.off,
    required this.on,
    required this.value,
    this.offLabel = '끄면',
    this.onLabel = '켜면',
  });
  final List<Widget> off;
  final List<Widget> on;
  final bool value;
  final String offLabel;
  final String onLabel;

  Widget _side(String label, List<Widget> children, bool active) => Container(
    padding: const EdgeInsets.all(10),
    decoration: BoxDecoration(
      color: active ? Kiosk.blueSoft : const Color(0xfff9fafb),
      borderRadius: BorderRadius.circular(14),
      border: Border.all(
        color: active ? Kiosk.blue : Colors.transparent,
        width: 2,
      ),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              label,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w700,
                color: active ? Kiosk.blue : Kiosk.faint,
              ),
            ),
            if (active) ...[
              const SizedBox(width: 6),
              const Text(
                '지금 설정',
                style: TextStyle(fontSize: 12, color: Kiosk.blue),
              ),
            ],
          ],
        ),
        const SizedBox(height: 8),
        DocPaper(width: 250, children: children),
      ],
    ),
  );

  @override
  Widget build(BuildContext context) => Wrap(
    spacing: 12,
    runSpacing: 12,
    children: [_side(offLabel, off, !value), _side(onLabel, on, value)],
  );
}
