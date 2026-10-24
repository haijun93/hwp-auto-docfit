import 'package:flutter/material.dart';

import 'doc_preview.dart';
import 'kiosk_theme.dart';

/// 설정 분류(왼쪽 큰 타일).
class GuideCategory {
  const GuideCategory(this.id, this.title, this.subtitle, this.icon);
  final String id;
  final String title;
  final String subtitle;
  final IconData icon;
}

const guideCategories = [
  GuideCategory('report', '보고서 모양', '제목·항목기호·여백', Icons.description_outlined),
  GuideCategory('paragraph', '문단 간격', '항목 사이 띄우기', Icons.format_line_spacing),
  GuideCategory('sentence', '문장·줄 정리', '줄 끝 단어·자간', Icons.wrap_text),
  GuideCategory('table', '표', '머리글·표 글꼴', Icons.table_chart_outlined),
  GuideCategory(
    'font',
    '항목기호 글꼴',
    '□ ㅇ - ※ 글꼴·크기',
    Icons.font_download_outlined,
  ),
  GuideCategory(
    'cards',
    '작업 카드 기본값',
    '처음 켜 둘 옵션',
    Icons.dashboard_customize_outlined,
  ),
  GuideCategory('result', '결과·기록', '저장·검수·보고서', Icons.fact_check_outlined),
  GuideCategory('general', '일반', '탐색기 메뉴', Icons.folder_outlined),
  GuideCategory('program', '프로그램·네트워크', '창·폐쇄망·업데이트', Icons.settings_outlined),
  GuideCategory('dev', '개발자 도구', '도형 편집기', Icons.build_outlined),
];

typedef PreviewBuilder = Widget Function(Object? value);

class SettingGuide {
  const SettingGuide(
    this.category,
    this.title,
    this.summary, {
    this.preview,
    this.unit,
  });
  final String category;
  final String title;
  final String summary;
  final PreviewBuilder? preview;
  final String? unit;
}

bool _on(Object? value) => value == true;
double _num(Object? value, double fallback) =>
    double.tryParse('${value ?? ''}'.trim()) ?? fallback;

const _hl = Color(0xfffff3b0);

DocPara _item(
  String marker,
  String text, {
  double size = 13,
  bool hanging = true,
  bool markerBold = false,
  double spaceBefore = 0,
  int level = 0,
  List<DocSpan>? spans,
}) => DocPara(
  marker: marker,
  size: size,
  hanging: hanging,
  markerBold: markerBold,
  spaceBefore: spaceBefore,
  indentLevel: level,
  spans: spans ?? [DocSpan(text)],
);

Widget _beforeAfter(
  Object? value,
  List<DocPara> off,
  List<DocPara> on, {
  String offLabel = '끄면',
  String onLabel = '켜면',
}) => BeforeAfter(
  value: _on(value),
  offLabel: offLabel,
  onLabel: onLabel,
  off: [for (final p in off) DocParagraph(p)],
  on: [for (final p in on) DocParagraph(p)],
);

Widget _paper(List<DocPara> paras, {String? caption}) => DocPaper(
  caption: caption,
  children: [for (final p in paras) DocParagraph(p)],
);

const _longItem =
    '마포순환열차버스 사업 종료에 따라 남은 전기버스 4대를 공익활동 지원과 찾아가는 행정서비스에 활용하는 방안을 검토함';

final Map<String, SettingGuide> settingGuides = {
  // ---------------- 보고서 모양 ----------------
  'stdformat': SettingGuide(
    'report',
    '보고서 표준서식 입히기',
    '한 번에 적용·서식 적용에서 제목·항목기호·여백을 보고서 표준에 맞춰요.',
    preview: (v) => _beforeAfter(
      v,
      [
        _item('●', '추진 배경 : 사업 종료', hanging: false),
        _item('-', '전기버스 4대 활용 필요', size: 12),
      ],
      [
        _item('□', '추진 배경 : 사업 종료', size: 15, markerBold: true),
        _item('ㅇ', '전기버스 4대 활용 필요', size: 14, level: 1, spaceBefore: 6),
      ],
    ),
  ),
  'std_title': SettingGuide(
    'report',
    '제목 서식',
    '문서 맨 위 제목을 제목 표 모양으로 정리해요.',
    preview: (v) => _beforeAfter(
      v,
      [
        const DocPara(spans: [DocSpan('전기버스 활용방안 검토보고')], size: 13),
      ],
      [
        const DocPara(
          spans: [DocSpan('전기버스 활용방안 검토보고', bold: true)],
          size: 19,
          align: TextAlign.center,
        ),
      ],
    ),
  ),
  'std_title_bold': SettingGuide(
    'report',
    '제목 굵게',
    '제목 글자를 굵게 써요.',
    preview: (v) => _paper([
      DocPara(
        spans: [DocSpan('전기버스 활용방안 검토보고', bold: _on(v))],
        size: 18,
        align: TextAlign.center,
      ),
    ]),
  ),
  'std_title_auto': SettingGuide(
    'report',
    '제목 자동으로 찾기',
    '맨 위 큰 글자 줄을 제목으로 알아봐요.',
  ),
  'std_attachment_auto': SettingGuide(
    'report',
    '붙임 자동으로 찾기',
    '"붙임" 줄을 붙임 표 모양으로 정리해요.',
  ),
  'std_midtitle_auto': SettingGuide(
    'report',
    '중제목 자동으로 찾기',
    'Ⅰ, Ⅱ 같은 중제목 줄을 알아봐요.',
  ),
  'std_midtitle_bold': SettingGuide(
    'report',
    '중제목 번호 굵게',
    'Ⅰ, Ⅱ 번호를 굵게 써요.',
    preview: (v) => _paper([
      DocPara(
        marker: 'Ⅰ',
        markerBold: _on(v),
        size: 16,
        spans: const [DocSpan('추진 배경', bold: true)],
      ),
    ]),
  ),
  'std_title_subtitle_pt': SettingGuide(
    'report',
    '부제 글자 크기',
    '제목 앞 부제(첫 쉼표 앞 글)의 크기예요.',
    unit: 'pt',
    preview: (v) => _paper([
      DocPara(
        spans: const [DocSpan('마포순환열차버스 사업종료에 따른')],
        size: _num(v, 15),
        align: TextAlign.center,
      ),
      const DocPara(
        spans: [DocSpan('전기버스 활용방안 검토보고', bold: true)],
        size: 19,
        align: TextAlign.center,
      ),
    ], caption: '부제 ${_num(v, 15).toStringAsFixed(0)}pt · 제목 19pt'),
  ),
  'title_owner_text': SettingGuide(
    'report',
    '제목 표 담당자 칸 글',
    '새로 만드는 제목 표의 담당자 칸에 넣을 글이에요. 비우면 원래 글을 둬요.',
    preview: (v) => _paper([
      const DocPara(
        spans: [DocSpan('전기버스 활용방안 검토보고', bold: true)],
        size: 17,
        align: TextAlign.center,
      ),
      DocPara(
        spans: [
          DocSpan('’26.10.1.(목)   '),
          DocSpan('$v'.isEmpty ? '정책과 담당 공혁준' : '$v', mark: _hl),
        ],
        size: 11,
        align: TextAlign.right,
      ),
    ]),
  ),
  'std_dateinfo': SettingGuide(
    'report',
    '날짜·담당자 줄 서식',
    '제목 아래 날짜·담당자 줄을 오른쪽 정렬로 정리해요.',
    preview: (v) => _beforeAfter(
      v,
      [
        const DocPara(spans: [DocSpan('26.10.1. 정책과장 조희옥 담당 공혁준')], size: 12),
      ],
      [
        const DocPara(
          spans: [DocSpan('’26. 10. 1.(목) 정책과 담당 공혁준')],
          size: 11,
          align: TextAlign.right,
        ),
      ],
    ),
  ),
  'std_dateinfo_bold': SettingGuide(
    'report',
    '날짜·담당자 굵게',
    '날짜·담당자 줄을 굵게 써요.',
    preview: (v) => _paper([
      DocPara(
        spans: [DocSpan('’26. 10. 1.(목) 정책과 담당 공혁준', bold: _on(v))],
        size: 11,
        align: TextAlign.right,
      ),
    ]),
  ),
  'std_symbols': SettingGuide(
    'report',
    '항목기호 정리',
    '●, ◦, · 처럼 섞인 기호를 □ → ㅇ → - 순서로 맞춰요.',
    preview: (v) => _beforeAfter(
      v,
      [
        _item('●', '추진 배경'),
        _item('◦', '사업 종료(2026. 9. 30.)', level: 1),
        _item('·', '차량 4대 남음', level: 2),
      ],
      [
        _item('□', '추진 배경'),
        _item('ㅇ', '사업 종료(2026. 9. 30.)', level: 1),
        _item('-', '차량 4대 남음', level: 2),
      ],
    ),
  ),
  'std_hanging_indent': SettingGuide(
    'report',
    '내어쓰기',
    '두 줄 이상인 항목에서 둘째 줄을 기호 다음 글자에 맞춰요.',
    preview: (v) => _beforeAfter(
      v,
      [_item('ㅇ', _longItem, hanging: false, size: 12)],
      [_item('ㅇ', _longItem, hanging: true, size: 12)],
    ),
  ),
  'std_supplement_indent': SettingGuide(
    'report',
    '부연설명 들여쓰기',
    '※, * 부연설명 줄을 위 항목보다 안쪽에서 시작해요.',
    preview: (v) => _beforeAfter(
      v,
      [
        _item('ㅇ', '전기버스 4대 활용 필요', size: 12),
        _item('※', '1대는 총무과 사용 예정', size: 11),
      ],
      [
        _item('ㅇ', '전기버스 4대 활용 필요', size: 12),
        _item('※', '1대는 총무과 사용 예정', size: 11, level: 2),
      ],
    ),
  ),
  'std_symbol_box_bold': SettingGuide(
    'report',
    '□ 기호 굵게',
    '□ 항목의 기호를 굵게 써요.',
    preview: (v) => _paper([_item('□', '추진 배경', size: 15, markerBold: _on(v))]),
  ),
  'std_symbol_o_bold': SettingGuide(
    'report',
    'ㅇ 기호 굵게',
    'ㅇ 항목의 기호를 굵게 써요.',
    preview: (v) =>
        _paper([_item('ㅇ', '전기버스 4대 활용 필요', size: 14, markerBold: _on(v))]),
  ),
  'std_symbol_dash_bold': SettingGuide(
    'report',
    '- 기호 굵게',
    '- 항목의 기호를 굵게 써요.',
    preview: (v) =>
        _paper([_item('-', '공익활동 지원 다목적 활용', size: 13, markerBold: _on(v))]),
  ),
  'std_symbol_note_bold': SettingGuide(
    'report',
    '※ 기호 굵게',
    '※ 참고 항목의 기호를 굵게 써요.',
    preview: (v) =>
        _paper([_item('※', '1대는 총무과 사용 예정', size: 12, markerBold: _on(v))]),
  ),
  'std_marker_bold_consistency': SettingGuide(
    'report',
    '같은 항목 라벨 굵기 맞추기',
    '같은 기호의 라벨(“목적 :”) 하나가 굵으면 나머지도 굵게 맞춰요.',
    preview: (v) => _beforeAfter(
      v,
      [
        _item(
          'ㅇ',
          '',
          spans: const [DocSpan('목적 : ', bold: true), DocSpan('차량 활용')],
        ),
        _item('ㅇ', '', spans: const [DocSpan('기간 : '), DocSpan('2026. 11.~')]),
      ],
      [
        _item(
          'ㅇ',
          '',
          spans: const [DocSpan('목적 : ', bold: true), DocSpan('차량 활용')],
        ),
        _item(
          'ㅇ',
          '',
          spans: const [
            DocSpan('기간 : ', bold: true, mark: _hl),
            DocSpan('2026. 11.~'),
          ],
        ),
      ],
    ),
  ),
  'paren_label_bold': SettingGuide(
    'report',
    '괄호 라벨 굵게',
    '“(목적)”처럼 괄호로 된 라벨을 굵게 써요.',
    preview: (v) => _paper([
      _item(
        'ㅇ',
        '',
        spans: [
          DocSpan('(목적) ', bold: _on(v)),
          const DocSpan('차량 활용방안 마련'),
        ],
      ),
    ]),
  ),
  'label_symbols': SettingGuide(
    'report',
    '문두 라벨 굵게(기호별)',
    '기호마다 줄 머리 라벨을 굵게 할지 정해요.',
  ),
  'paren_shrink': SettingGuide(
    'report',
    '괄호 안 글자 줄이기',
    '괄호 안 설명을 본문보다 조금 작게 써요.',
    preview: (v) => _paper([
      DocPara(
        marker: 'ㅇ',
        size: 13,
        spans: [
          const DocSpan('전기버스 4대 '),
          DocSpan('(카운티일렉트릭 23인승)', mark: _on(v) ? _hl : null),
        ],
      ),
    ], caption: _on(v) ? '괄호 안을 2pt 작게' : '괄호 안도 본문과 같은 크기'),
  ),
  'std_margin': SettingGuide(
    'report',
    '편집 여백',
    '쪽 여백을 보고서 표준(위·아래 15mm, 좌우 20mm)으로 맞춰요.',
  ),
  'std_ratio': SettingGuide('report', '기본 장평', '본문 글자 폭을 표준 장평으로 맞춰요.'),
  'std_linespacing': SettingGuide('report', '기본 줄 간격', '본문 줄 간격을 표준 값으로 맞춰요.'),

  // ---------------- 문단 간격 ----------------
  'std_parspace': SettingGuide(
    'paragraph',
    '항목 위 간격 넣기',
    '항목 사이를 빈 줄 대신 문단 위 간격으로 띄워요.',
    preview: (v) => _beforeAfter(
      v,
      [
        _item('□', '추진 배경', size: 14),
        _item('ㅇ', '사업 종료', size: 13, level: 1),
        _item('ㅇ', '차량 활용 필요', size: 13, level: 1),
      ],
      [
        _item('□', '추진 배경', size: 14),
        _item('ㅇ', '사업 종료', size: 13, level: 1, spaceBefore: 8),
        _item('ㅇ', '차량 활용 필요', size: 13, level: 1, spaceBefore: 8),
      ],
    ),
  ),
  'std_remove_blank_lines': SettingGuide(
    'paragraph',
    '항목 사이 빈 줄 지우기',
    '빈 줄로 띄운 곳을 지우고 문단 위 간격으로 대신해요.',
    preview: (v) => _beforeAfter(
      v,
      [
        _item('ㅇ', '사업 종료'),
        const DocPara(spans: [DocSpan(' ')]),
        _item('ㅇ', '차량 활용 필요'),
      ],
      [_item('ㅇ', '사업 종료'), _item('ㅇ', '차량 활용 필요', spaceBefore: 8)],
    ),
  ),
  for (final entry in const {
    'std_parspace_chapter': ('Ⅰ', '중제목(Ⅰ) 위 간격', '추진 배경'),
    'std_parspace_midtitle': ('1.', '숫자 중제목 위 간격', '현황'),
    'std_parspace_box': ('□', '□ 항목 위 간격', '추진 배경'),
    'std_parspace_circle': ('ㅇ', 'ㅇ 항목 위 간격', '사업 종료(2026. 9. 30.)'),
    'std_parspace_dash': ('-', '- 항목 위 간격', '차량 4대 남음'),
    'std_parspace_note': ('※', '※ 항목 위 간격', '1대는 총무과 사용 예정'),
  }.entries)
    entry.key: SettingGuide(
      'paragraph',
      entry.value.$2,
      '이 항목 바로 위를 얼마나 띄울지 정해요.',
      unit: 'pt',
      preview: (v) => _paper([
        const DocPara(
          spans: [DocSpan('앞 문단의 마지막 줄')],
          size: 12,
          color: Kiosk.faint,
        ),
        DocPara(
          marker: entry.value.$1,
          spaceBefore: _num(v, 8),
          size: 13,
          spans: [DocSpan(entry.value.$3)],
        ),
      ], caption: '위 간격 ${_num(v, 8).toStringAsFixed(0)}pt'),
    ),
  'std_parspace_return_percent': SettingGuide(
    'paragraph',
    '상위 항목으로 돌아올 때 간격',
    '아래 단계에서 위 단계로 돌아오는 항목은 간격을 이만큼 더 띄워요.',
    unit: '%',
  ),

  // ---------------- 문장·줄 정리 ----------------
  'prevent_word_split': SettingGuide(
    'sentence',
    '줄 끝 단어 안 끊기',
    '한 단어가 두 줄로 나뉘지 않게 자간을 살짝 조정해요.',
    preview: (v) => _beforeAfter(
      v,
      [
        const DocPara(
          marker: 'ㅇ',
          size: 12,
          lines: [
            [DocSpan('남은 전기버스를 행정서비스에 '), DocSpan('활', mark: _hl)],
            [DocSpan('용', mark: _hl), DocSpan('하는 방안을 검토함')],
          ],
        ),
      ],
      [
        const DocPara(
          marker: 'ㅇ',
          size: 12,
          lines: [
            [DocSpan('남은 전기버스를 행정서비스에')],
            [DocSpan('활용', mark: _hl), DocSpan('하는 방안을 검토함')],
          ],
        ),
      ],
    ),
  ),
  'ratio_shrink': SettingGuide(
    'sentence',
    '장평 줄이기도 쓰기',
    '자간만으로 안 될 때 글자 폭(장평)도 조금 줄여요.',
    preview: (v) => _beforeAfter(
      v,
      [
        const DocPara(
          marker: 'ㅇ',
          size: 12,
          lines: [
            [DocSpan('찾아가는 행정서비스 운영방안 검')],
            [DocSpan('토', mark: _hl), DocSpan('함')],
          ],
        ),
      ],
      [
        const DocPara(
          marker: 'ㅇ',
          size: 12,
          ratio: 92,
          lines: [
            [DocSpan('찾아가는 행정서비스 운영방안 검토함', mark: _hl)],
          ],
        ),
      ],
      offLabel: '끄면 (자간만 조정)',
      onLabel: '켜면 (장평 92%로 한 줄)',
    ),
  ),
  'punctuation': SettingGuide(
    'sentence',
    '문장부호 줄 처음에 안 두기',
    '줄 맨 앞에 마침표·닫는 괄호가 오지 않게 앞줄로 당겨요.',
    preview: (v) => _beforeAfter(
      v,
      [
        const DocPara(
          marker: 'ㅇ',
          size: 12,
          lines: [
            [DocSpan('차량 4대 활용방안 마련(2026. 11.')],
            [DocSpan(')', mark: _hl), DocSpan(' 예정')],
          ],
        ),
      ],
      [
        const DocPara(
          marker: 'ㅇ',
          size: 12,
          spacing: -4,
          lines: [
            [DocSpan('차량 4대 활용방안 마련(2026. 11.'), DocSpan(')', mark: _hl)],
            [DocSpan('예정')],
          ],
        ),
      ],
    ),
  ),
  'punctuation_threshold': SettingGuide(
    'sentence',
    '문장부호를 옮길 둘째 줄 길이',
    '둘째 줄 글자가 이 수 이하일 때만 앞줄로 당겨요.',
    unit: '자',
  ),
  'keep_punctuation_set_together': SettingGuide(
    'sentence',
    '날짜·괄호 묶음 지키기',
    '“(2026. 9. 30.)”처럼 한 묶음은 줄을 나누지 않아요.',
    preview: (v) => _beforeAfter(
      v,
      [
        const DocPara(
          marker: 'ㅇ',
          size: 12,
          lines: [
            [DocSpan('사업 종료에 따른 후속 조치 (2026. 9.')],
            [DocSpan('30.)', mark: _hl), DocSpan(' 이행')],
          ],
        ),
      ],
      [
        const DocPara(
          marker: 'ㅇ',
          size: 12,
          lines: [
            [DocSpan('사업 종료에 따른 후속 조치')],
            [DocSpan('(2026. 9. 30.)', mark: _hl), DocSpan(' 이행')],
          ],
        ),
      ],
    ),
  ),
  'spacing_exclude_reset': SettingGuide(
    'sentence',
    '기존 자간 초기화 제외',
    '켜면 문서에 걸린 기존 자간을 0%로 되돌리지 않고 그 위에서 정리해요. 끄면 0%로 초기화한 뒤 정리해요.',
  ),
  'spacing_reset_existing': SettingGuide(
    'sentence',
    '기존 자간 초기화',
    '자간 정리 전에 문서에 이미 걸린 자간을 0%로 되돌려요. 끄면 기존 자간 위에서 정리해요.',
    preview: (v) => _beforeAfter(
      v,
      [
        const DocPara(
          marker: 'ㅇ',
          size: 12,
          spacing: -12,
          spans: [DocSpan('좁게 눌린 자간이 그대로 남아 있음')],
        ),
      ],
      [
        const DocPara(
          marker: 'ㅇ',
          size: 12,
          spans: [DocSpan('좁게 눌린 자간이 그대로 남아 있음', mark: _hl)],
        ),
      ],
      offLabel: '끄면 (기존 자간 유지)',
      onLabel: '켜면 (0%로 되돌림)',
    ),
  ),
  'table_spacing': SettingGuide(
    'sentence',
    '표 안 문장도 정리',
    '표 칸 안 문장의 줄 끝도 함께 정리해요.',
    preview: (v) => DocPaper(
      children: [
        DocTable(
          rows: const [
            ['구분', '내용'],
            ['1안', '공익활동 지원 다목적 활용'],
          ],
          spacing: _on(v) ? -4 : 0,
          mark: _on(v) ? _hl : null,
        ),
      ],
    ),
  ),
  'table_linespacing_min': SettingGuide('sentence', '표 칸 최소 줄 간격',
    '쪽 맞춤에 필요할 때만 이 하한까지 줄여요. 본문 줄 간격과 별도예요.', unit: '%'),
  'table_spacing_min': SettingGuide('sentence', '표 칸 자간 하한',
    '칸 너비에 관계없이 같은 하한을 사용해요. 한 칸 상자는 기존 본문 기준을 유지해요.', unit: '%'),
  'linespacing_min': SettingGuide(
    'sentence',
    '줄 간격 최솟값',
    '쪽을 맞출 때 줄 간격을 이보다 좁히지 않아요.',
    unit: '%',
    preview: (v) => _paper([
      for (final t in ['첫째 줄 예시', '둘째 줄 예시'])
        DocPara(
          marker: 'ㅇ',
          size: 12,
          lineSpacing: _num(v, 160),
          spans: [DocSpan(t)],
        ),
    ], caption: '줄 간격 ${_num(v, 160).toStringAsFixed(0)}%'),
  ),
  'linespacing_max': SettingGuide(
    'sentence',
    '줄 간격 최댓값',
    '쪽을 맞출 때 줄 간격을 이보다 넓히지 않아요.',
    unit: '%',
    preview: (v) => _paper([
      for (final t in ['첫째 줄 예시', '둘째 줄 예시'])
        DocPara(
          marker: 'ㅇ',
          size: 12,
          lineSpacing: _num(v, 200),
          spans: [DocSpan(t)],
        ),
    ], caption: '줄 간격 ${_num(v, 200).toStringAsFixed(0)}%'),
  ),
  'retry_body': SettingGuide(
    'sentence',
    '본문 자간 조정 단계',
    '본문 한 줄을 맞추려고 자간을 몇 단계까지 바꿔 볼지예요. 많을수록 꼼꼼하지만 오래 걸려요.',
    unit: '단계',
  ),
  'retry_table': SettingGuide(
    'sentence',
    '표 자간 조정 단계',
    '표 칸 문장에서 자간을 몇 단계까지 바꿔 볼지예요.',
    unit: '단계',
  ),
  'two_pass_processing': SettingGuide(
    'sentence',
    '두 번 처리',
    '한 번 더 처리해 남은 줄 끝 문제를 줄여요. 시간이 두 배 걸려요.',
  ),
  'color_mark_on': SettingGuide(
    'sentence',
    '조정한 글자 색으로 표시',
    '자간을 바꾼 글자에 색을 칠해 어디가 바뀌었는지 보여 줘요.',
    preview: (v) => _paper([
      DocPara(
        marker: 'ㅇ',
        size: 12,
        spans: [
          const DocSpan('남은 전기버스를 행정서비스에 '),
          DocSpan('활용하는', mark: _on(v) ? const Color(0xffcfe3ff) : null),
          const DocSpan(' 방안'),
        ],
      ),
    ]),
  ),
  'color': SettingGuide('sentence', '표시 색', '조정한 글자를 칠할 색이에요.'),

  // ---------------- 표 ----------------
  'std_table_header': SettingGuide(
    'table',
    '표 머리글 서식',
    '표 첫 줄(머리글)을 굵게, 배경을 넣어 구분해요.',
    preview: (v) => BeforeAfter(
      value: _on(v),
      off: const [
        DocTable(
          rows: [
            ['구분', '1안', '2안'],
            ['운영비', '20,000', '46,000'],
          ],
          headerBold: false,
          headerFill: null,
        ),
      ],
      on: const [
        DocTable(
          rows: [
            ['구분', '1안', '2안'],
            ['운영비', '20,000', '46,000'],
          ],
        ),
      ],
    ),
  ),
  'table_fonts.header.font': SettingGuide('table', '표 머리글 글꼴', '표 첫 줄의 글꼴이에요.'),
  'table_fonts.header.size': SettingGuide(
    'table',
    '표 머리글 크기',
    '표 첫 줄의 글자 크기예요.',
    unit: 'pt',
    preview: (v) => DocPaper(
      children: [
        DocTable(
          rows: const [
            ['구분', '1안', '2안'],
            ['운영비', '20,000', '46,000'],
          ],
          headerSize: _num(v, 13),
        ),
      ],
    ),
  ),
  'table_fonts.header.bold': SettingGuide('table', '표 머리글 굵게', '표 첫 줄을 굵게 써요.'),
  'table_fonts.body.font': SettingGuide('table', '표 본문 글꼴', '표 나머지 줄의 글꼴이에요.'),
  'table_fonts.body.size': SettingGuide(
    'table',
    '표 본문 크기',
    '표 나머지 줄의 글자 크기예요.',
    unit: 'pt',
    preview: (v) => DocPaper(
      children: [
        DocTable(
          rows: const [
            ['구분', '1안', '2안'],
            ['운영비', '20,000', '46,000'],
          ],
          bodySize: _num(v, 12),
        ),
      ],
    ),
  ),

  // ---------------- 작업 카드 기본값 ----------------
  'all_include_spacing': SettingGuide(
    'cards',
    '한 번에 적용: 자간도 정리',
    '서식을 입힌 뒤 자간 정리까지 이어서 해요. 끄면 서식만 입혀요.',
  ),
  'all_exclude_tables': SettingGuide(
    'cards',
    '한 번에 적용: 표는 그대로',
    '표 서식·표 안 자간은 건드리지 않아요.',
  ),
  'all_exclude_pagefit': SettingGuide(
    'cards',
    '한 번에 적용: 쪽 맞춤 빼기',
    '마지막 쪽을 채우려고 간격을 바꾸는 작업을 빼요.',
  ),
  'all_exclude_linespacing': SettingGuide(
    'cards',
    '한 번에 적용: 줄 간격 적용 제외',
    '켜면 문서의 줄 간격을 표준값으로 바꾸지 않고 그대로 둬요.',
  ),
  'all_cell_image_to_bg': SettingGuide(
    'cards',
    '한 번에 적용: 표 셀 이미지를 배경으로 변경',
    '표 셀 안에 들어있는 단독 이미지를 셀 배경 이미지(크기에 맞추어)로 변경해요.',
  ),
  'spacing_cell_image_to_bg': SettingGuide(
    'cards',
    '자간 정리: 표 셀 이미지를 배경으로 변경',
    '표 셀 안에 들어있는 단독 이미지를 셀 배경 이미지(크기에 맞추어)로 변경해요.',
  ),
  'spacing_exclude_pagefit': SettingGuide(
    'cards',
    '자간 정리: 페이지 맞춤 제외',
    '켜면 문단 아래 간격 페이지 맞춤을 빼요. 끄면 페이지 맞춤을 함께 실행해요.',
  ),
  'spacing_page_fit': SettingGuide(
    'cards',
    '자간 정리: 페이지 맞춤',
    '문단 아래 간격과 줄 간격을 미세하게 조정해 쪽 수를 맞춰요.',
  ),
  'all_linespacing': SettingGuide(
    'cards',
    '한 번에 적용: 줄 간격 적용',
    '끄면 문서의 줄 간격을 유지해요. 페이지 맞춤의 줄 간격 조정은 페이지 맞춤 제외에서 정해요.',
  ),
  'unify_exclude_tables': SettingGuide(
    'cards',
    '서식 통일: 표는 그대로',
    '표 안 문장은 서식 통일에서 빼요.',
  ),
  'unify_exclude_spacing': SettingGuide(
    'cards',
    '서식 통일: 자간 정리 빼기',
    '서식만 맞추고 고친 문장의 자간은 그대로 둬요.',
  ),
  'unify_exclude_pagefit': SettingGuide(
    'cards',
    '서식 통일: 쪽 맞춤 빼기',
    '쪽 수를 맞추려는 간격 조정을 하지 않아요.',
  ),
  'unify_keep_layout': SettingGuide(
    'cards',
    '서식 통일: 원본 쪽 구성 유지',
    '결과 문서의 쪽 나눔을 원본과 같게 지켜요.',
  ),
  'unify_full_format': SettingGuide(
    'cards',
    '서식 통일: 전체 서식 맞추기',
    '글꼴·크기뿐 아니라 굵기·간격까지 문서의 대표 서식으로 맞춰요.',
  ),

  // ---------------- 결과·기록 ----------------
  'autoclose': SettingGuide(
    'result',
    '끝나면 한글 창 닫기',
    '작업이 끝나면 처리에 쓴 한글 창을 자동으로 닫아요.',
  ),
  'verify': SettingGuide(
    'result',
    '결과 자세히 검사',
    '저장한 결과를 다시 열어 글자 훼손·쪽 나눔을 자세히 검사해요.',
  ),
  'integrity_report_file': SettingGuide(
    'result',
    '무결성 보고서 파일 만들기',
    '글자가 그대로인지 검사한 결과를 파일로 남겨요.',
  ),
  'final_review_file': SettingGuide(
    'result',
    '최종 검수 보고서 파일 만들기',
    '최종 점수와 남은 문제를 파일로 남겨요.',
  ),
  'log_file': SettingGuide(
    'result',
    '작업 기록 파일 만들기',
    '처리 과정을 문서 옆 .log 파일로 남겨요.',
  ),
  'unify_result_window': SettingGuide(
    'result',
    '서식 통일 결과 창 보기',
    '문서 하나를 서식 통일하면 결과 확인 창을 띄워요.',
  ),
  'paste_add_folder': SettingGuide(
    'result',
    '붙여넣은 글 저장 폴더',
    '붙여넣은 글로 만든 문서를 둘 폴더예요. 비우면 기본 폴더를 써요.',
  ),

  // ---------------- 프로그램·네트워크 ----------------
  'offline_mode': SettingGuide(
    'program',
    '폐쇄망 모드 (인터넷 연결 안 함)',
    '인터넷이 안 되는 PC용이에요. 켜면 앱이 업데이트 확인·모델 내려받기 같은 외부 접속을 하지 않아요.',
  ),
  'check_updates_on_start': SettingGuide(
    'program',
    '시작할 때 업데이트 확인',
    '앱을 켤 때 새 버전이 있는지 확인해요. 폐쇄망 모드에서는 확인하지 않아요.',
  ),
  'shell_menu': SettingGuide(
    'general',
    '탐색기 우클릭 메뉴',
    '현재 사용자에게만 등록해요. Windows 11에서는 파일 우클릭 → 더 많은 옵션 표시 → 한글편집 후처리에서 변환할 수 있어요.',
  ),
  'always_on_top': SettingGuide('program', '항상 위에 표시', '앱 창을 다른 창보다 위에 둬요.'),
  'hwp_font_folder': SettingGuide(
    'program',
    '한글 글꼴 폴더',
    '한글 프로그램의 글꼴 폴더예요. 비우면 자동으로 찾아요.',
  ),

  // ---------------- 개발자 도구 ----------------
  'developer_mode': SettingGuide(
    'dev',
    '개발자 모드',
    '자세한 문서 처리 완료 안내를 표시해요.',
  ),
};

/// 항목기호 글꼴(symbol_fonts.□.size 등)은 기호마다 같은 모양의 안내를 만든다.
SettingGuide? guideFor(String key) {
  final known = settingGuides[key];
  if (known != null) return known;
  final symbol = RegExp(r'^symbol_fonts\.(.+)\.(font|size)$').firstMatch(key);
  if (symbol != null) {
    final marker = symbol.group(1)!;
    final isSize = symbol.group(2) == 'size';
    return SettingGuide(
      'font',
      '$marker 항목 ${isSize ? '글자 크기' : '글꼴'}',
      isSize ? '$marker 기호로 시작하는 문장의 글자 크기예요.' : '$marker 기호로 시작하는 문장의 글꼴이에요.',
      unit: isSize ? 'pt' : null,
      preview: isSize
          ? (v) => _paper([
              DocPara(
                marker: marker,
                size: _num(v, 13),
                spans: const [DocSpan('전기버스 활용방안 검토')],
              ),
            ], caption: '${_num(v, 13).toStringAsFixed(0)}pt')
          : (v) => _paper([
              DocPara(
                marker: marker,
                size: 13,
                spans: const [DocSpan('전기버스 활용방안 검토')],
              ),
            ], caption: '글꼴: $v (화면 미리보기는 기본 글꼴로 보여요)'),
    );
  }
  final label = RegExp(r'^label_symbols\.(.+)$').firstMatch(key);
  if (label != null) {
    final marker = label.group(1)!;
    return SettingGuide(
      'report',
      '$marker 줄 머리 라벨 굵게',
      '$marker 기호 줄의 “라벨 :”을 굵게 써요.',
      preview: (v) => _paper([
        DocPara(
          marker: marker,
          size: 13,
          spans: [
            DocSpan('목적 : ', bold: _on(v)),
            const DocSpan('차량 활용'),
          ],
        ),
      ]),
    );
  }
  return null;
}

/// 같은 분류 안에서 안내 목록에 적힌 순서(쉬운 것부터)로 보여 준다.
final Map<String, int> guideOrder = {
  for (final entry in settingGuides.keys.toList().asMap().entries)
    entry.value: entry.key,
};
