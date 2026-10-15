import 'package:flutter/material.dart';

import '../settings/doc_preview.dart';
import '../settings/kiosk_theme.dart';

/// 서식 요소 값(화면 글자: '15pt', '-5%', '예', '왼쪽' …)으로 한글 문서 미리보기를 만든다.
double? _number(String? text) {
  final match = RegExp(r'-?\d+(\.\d+)?').firstMatch(text ?? '');
  return match == null ? null : double.tryParse(match.group(0)!);
}

bool _yes(String? text) => text == '예';

TextAlign _align(String? text) => switch (text) {
  '가운데' => TextAlign.center,
  '오른쪽' => TextAlign.right,
  // 한글의 양쪽·배분 정렬은 낱말 사이만 늘린다. 화면 글꼴의 양쪽 정렬은 글자 사이를 벌려 달라 보이므로 왼쪽으로 그린다.
  _ => TextAlign.left,
};

const _markers = ['□', 'ㅇ', '○', '-', '•', '※', '*', '**', 'Ⅰ', '1.', '가.'];

String _markerOf(String label) {
  final trimmed = label.trim();
  for (final marker in _markers) {
    if (trimmed.startsWith(marker)) return marker;
  }
  return '';
}

/// 미리보기를 그릴 수 있는 요소인지(쪽·문장·표·칸·문단).
Widget elementPreview(List path, String label, Map<String, String> values) {
  final kind = path.isEmpty ? '' : '${path.first}';
  final size = (_number(values['size']) ?? 13).clamp(6, 40).toDouble();
  final spacing = _number(values['spacing']) ?? 0;
  final ratio = (_number(values['ratio']) ?? 100).clamp(50, 200).toDouble();
  final lineType = values['line_type'];
  final lineValue = _number(values['line']);
  final lineSpacing = lineType == null || lineType == '글자에 따라(%)'
      ? (lineValue ?? 160)
      : 160.0;
  final before = (_number(values['prev']) ?? 0).clamp(0, 40).toDouble();
  final caption = [
    if (values['font'] != null) '글꼴 ${values['font']}',
    '${size.toStringAsFixed(size % 1 == 0 ? 0 : 1)}pt',
    if (spacing != 0) '자간 ${spacing.toStringAsFixed(0)}%',
    if (ratio != 100) '장평 ${ratio.toStringAsFixed(0)}%',
    if (values['line'] != null)
      '줄 간격 ${values['line']}${lineType == null || lineType == '글자에 따라(%)' ? '%' : ''}',
    if (before > 0) '위 간격 ${before.toStringAsFixed(0)}pt',
  ].join(' · ');

  if (kind == 'page') {
    final left = _number(values['page_left']) ?? 20;
    final top = _number(values['page_top']) ?? 15;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 170,
          height: 240,
          decoration: BoxDecoration(
            color: Colors.white,
            border: Border.all(color: const Color(0xffdfe3e8)),
            boxShadow: const [
              BoxShadow(
                color: Color(0x14000000),
                blurRadius: 10,
                offset: Offset(0, 3),
              ),
            ],
          ),
          child: Padding(
            // 용지 210mm를 170px로 줄여 여백을 같은 비율로 보인다.
            padding: EdgeInsets.fromLTRB(
              left * 0.81,
              top * 0.81,
              (_number(values['page_right']) ?? 20) * 0.81,
              (_number(values['page_bottom']) ?? 15) * 0.81,
            ),
            child: Container(
              decoration: BoxDecoration(
                border: Border.all(color: Kiosk.blue.withValues(alpha: 0.5)),
                color: Kiosk.blueSoft.withValues(alpha: 0.5),
              ),
              child: const Center(
                child: Text(
                  '글이 들어가는 곳',
                  style: TextStyle(fontSize: 11, color: Kiosk.blue),
                ),
              ),
            ),
          ),
        ),
        const SizedBox(height: 6),
        Text(
          '여백 위 ${values['page_top'] ?? '-'} · 아래 ${values['page_bottom'] ?? '-'} · 왼쪽 ${values['page_left'] ?? '-'} · 오른쪽 ${values['page_right'] ?? '-'}',
          style: Kiosk.caption,
        ),
      ],
    );
  }

  if (kind == 'table' ||
      (kind == 'form' && path.length > 2 && path[2] == 'table')) {
    final header = path.length > 1 && path[1] == 'header';
    return DocPaper(
      caption: caption,
      children: [
        DocTable(
          rows: const [
            ['구분', '1안', '2안'],
            ['운영비', '20,000천원', '46,000천원'],
          ],
          headerSize: header ? size : 12,
          bodySize: header ? 11 : size,
          headerBold: header ? _yes(values['bold']) : true,
          bodyBold: !header && _yes(values['bold']),
          headerFill: values['fill'] != null && values['fill'] != '-'
              ? const Color(0xffeef1f5)
              : null,
          spacing: spacing,
        ),
      ],
    );
  }

  final marker = _markerOf(label);
  final para = DocPara(
    marker: marker,
    size: size,
    spacing: spacing,
    ratio: ratio,
    markerBold: _yes(values['marker_bold']),
    hanging: values['hanging'] == null ? true : _yes(values['hanging']),
    spaceBefore: before,
    lineSpacing: lineSpacing.clamp(100, 300).toDouble(),
    align: _align(values['align']),
    spans: [
      DocSpan(
        '추진 배경 : ',
        bold: _yes(values['label_bold']) || _yes(values['bold']),
      ),
      DocSpan(
        '남은 전기버스 4대를 공익활동 지원과 찾아가는 행정서비스에 활용하는 방안을 검토함',
        bold: _yes(values['bold']),
      ),
    ],
  );
  return DocPaper(
    width: 360,
    caption: caption,
    children: [
      const DocParagraph(
        DocPara(spans: [DocSpan('앞 문단')], size: 11, color: Kiosk.faint),
      ),
      DocParagraph(para),
    ],
  );
}
