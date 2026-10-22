import 'package:flutter/material.dart';

/// 옵션 설명용 적용 전·후 예시 이미지(1.80.3).
///
/// rhwp 조판 미리보기 대신 README와 같은 전·후 비교 그림(docs/media/features)을
/// 앱에 넣어 보여 준다. 그림은 왼쪽이 적용 전, 오른쪽이 적용 후이고 빨간색이 바뀌는 부분이다.
class OptionImage {
  const OptionImage(this.file, this.caption);
  final String file;
  final String caption;
  String get asset => 'assets/option_images/$file';
}

const _spacing = OptionImage(
  'spacing.png',
  '줄을 옮긴 어절을 빨간색으로 표시한 실제 보고서 자간 정리 전·후',
);
const _shortLine = OptionImage('short-line.png', '짧은 마지막 줄을 윗줄로 붙이기 전·후');
const _unify = OptionImage('style-unify.png', '다른 문장과 서식이 다른 문장만 고치기 전·후');
const _allInOne = OptionImage('all-in-one.png', '한 번에 적용(서식·자간·쪽 맞춤) 전·후');
const _tableFormat = OptionImage('table-format.png', '표 머리글·테두리·글꼴 서식 적용 전·후');
const _pageFit = OptionImage('page-fit.png', '쪽 수 맞춤 전·후');
const _layout = OptionImage('original-layout.png', '원본 쪽 구성 유지');
const _rules = OptionImage('spacing-rules.png', '빈칸·문장부호 뒤 공백 정리 전·후');

/// 세부 작업(단계) 키·작업 방식 카드 옵션 키·설정 키 → 예시 그림.
const Map<String, OptionImage> optionImages = {
  // 세부 작업(docfit_core/stage_selection.py)
  'reset_spacing': OptionImage(
    'reset-spacing.png',
    '기존 자간을 0%로 되돌린 뒤 다시 정리하기 전·후',
  ),
  'body_spacing': _spacing,
  'word_check': _spacing,
  'control_spacing': _spacing,
  'control_word_check': _spacing,
  'unify_spacing': _spacing,
  'single_cell_spacing': _spacing,
  'short_line': _shortLine,
  'control_short_line': _shortLine,
  'style_unify': _unify,
  'table_unify': _unify,
  'unify_full_format': _unify,
  'standard_format': _allInOne,
  'pre_format': _allInOne,
  'hanging_indent': OptionImage(
    'hanging-indent.png',
    '둘째 줄부터 항목기호 뒤 첫 글자에 맞추는 내어쓰기 전·후',
  ),
  'supplement_indent': OptionImage('supplement.png', '부연 설명(※) 들여쓰기 전·후'),
  'star_align': OptionImage('asterisk.png', '별표(*) 정렬·위첨자 전·후'),
  'asterisk_superscript': OptionImage('asterisk.png', '별표(*) 정렬·위첨자 전·후'),
  'parenthesis': OptionImage('labels.png', '괄호 축소·문두 라벨 굵게 전·후'),
  'normalize_space': _rules,
  'punctuation_space': _rules,
  'abbreviation': OptionImage('abbreviation.png', '준말 줄을 본말·서식 표로 바꾸기 전·후'),
  'text_table_convert': OptionImage(
    'table-convert.png',
    '글로 쓴 표를 한/글 표로 바꾸기 전·후',
  ),
  'table_style': _tableFormat,
  'table_format': _tableFormat,
  'precise_table': _tableFormat,
  'table_width': OptionImage('table-width.png', '표 너비를 본문 폭에 맞추기 전·후'),
  'page_fit': _pageFit,
  'page_layout_keep': _layout,
  'page_group': OptionImage('page-group.png', '보고서 단위로 쪽 나누기 전·후'),
  // 작업 방식 카드 옵션(stage_selection.CARD_OPTION_STAGES)
  'spacing_enabled': _spacing,
  'spacing_page_fit': _pageFit,
  'spacing_reset_existing': OptionImage(
    'reset-spacing.png',
    '기존 자간을 0%로 되돌린 뒤 다시 정리하기 전·후',
  ),
  'unify_exclude_spacing': _spacing,
  'unify_exclude_pagefit': _pageFit,
  'unify_keep_layout': _layout,
  'all_include_spacing': _allInOne,
  // 설정 화면(키 접두어는 optionImageFor에서 처리)
  'label_symbols': OptionImage('labels.png', '문두 라벨 굵게 전·후'),
  'std_hanging_indent': OptionImage(
    'hanging-indent.png',
    '둘째 줄부터 항목기호 뒤 첫 글자에 맞추는 내어쓰기 전·후',
  ),
  'std_supplement_indent': OptionImage('supplement.png', '부연 설명(※) 들여쓰기 전·후'),
  'table_fonts': _tableFormat,
  'std_table_header': _tableFormat,
  'settings': OptionImage('options.png', '설정 옵션이 문서에 반영되는 예'),
};

/// 그림이 아직 없는 키(새 그림은 한/글 2020에서 사본 문서로 만들어야 함).
const List<String> optionImageMissing = [
  'attachment_font',
  'spacing_exclude_tables',
  'unify_exclude_tables',
  'all_exclude_tables',
  'all_exclude_pagefit',
];

/// 키에 맞는 그림. 설정 키는 'label_symbols.□'처럼 하위 키가 붙으므로 접두어로도 찾는다.
OptionImage? optionImageFor(String? key) {
  if (key == null || key.isEmpty) return null;
  final direct = optionImages[key];
  if (direct != null) return direct;
  for (final prefix in const ['label_symbols', 'table_fonts']) {
    if (key.startsWith(prefix)) return optionImages[prefix];
  }
  return null;
}

/// 적용 전·후 예시 그림. 누르면 크게 본다. 그림이 없으면 짧은 안내만 보인다.
class OptionImagePreview extends StatelessWidget {
  const OptionImagePreview(this.keyName, {super.key, this.fallback});
  final String? keyName;
  final OptionImage? fallback;

  @override
  Widget build(BuildContext context) {
    final image = optionImageFor(keyName) ?? fallback;
    if (image == null) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 8),
        child: Text(
          '예시 이미지 준비 중',
          style: TextStyle(fontSize: 12, color: Colors.black54),
        ),
      );
    }
    return Semantics(
      button: true,
      label: '${image.caption} 크게 보기',
      child: InkWell(
        key: ValueKey('option-image-${keyName ?? image.file}'),
        borderRadius: BorderRadius.circular(10),
        onTap: () => showOptionImage(context, image),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(10),
              child: Image.asset(
                image.asset,
                fit: BoxFit.fitWidth,
                errorBuilder: (_, _, _) => const SizedBox.shrink(),
              ),
            ),
            const SizedBox(height: 4),
            Text(
              image.caption,
              style: const TextStyle(fontSize: 12, color: Colors.black54),
            ),
          ],
        ),
      ),
    );
  }
}

/// 옵션 줄 옆에 두는 작은 '예시' 버튼. 그림이 없으면 아무것도 그리지 않는다.
class OptionImageButton extends StatelessWidget {
  const OptionImageButton(this.keyName, {super.key});
  final String keyName;

  @override
  Widget build(BuildContext context) {
    final image = optionImageFor(keyName);
    if (image == null) return const SizedBox.shrink();
    return IconButton(
      key: ValueKey('option-image-button-$keyName'),
      tooltip: '적용 전·후 예시 보기',
      visualDensity: VisualDensity.compact,
      onPressed: () => showOptionImage(context, image),
      icon: const Icon(Icons.image_outlined, size: 20),
    );
  }
}

Future<void> showOptionImage(BuildContext context, OptionImage image) =>
    showDialog<void>(
      context: context,
      builder: (context) => Dialog(
        key: const ValueKey('option-image-zoom'),
        insetPadding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(16, 12, 0, 0),
                    child: Text(
                      image.caption,
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
                IconButton(
                  tooltip: '닫기',
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.close_rounded),
                ),
              ],
            ),
            Flexible(
              child: InteractiveViewer(
                maxScale: 4,
                child: Image.asset(image.asset, fit: BoxFit.contain),
              ),
            ),
            const Padding(
              padding: EdgeInsets.fromLTRB(16, 4, 16, 12),
              child: Text(
                '왼쪽은 적용 전, 오른쪽은 적용 후예요. 빨간색이 바뀌는 부분이에요.',
                style: TextStyle(fontSize: 12),
              ),
            ),
          ],
        ),
      ),
    );
