import 'package:flutter/material.dart';

/// 파일변환 탭 첫 화면: 파일을 끌어 놓거나 고르면 문서편집 화면의 변환 흐름이 이어진다
/// (키패드 포맷 선택 → 진행 → 4. 결과 확인).
class ConversionDropPane extends StatelessWidget {
  const ConversionDropPane({super.key, required this.onPickFiles});

  final VoidCallback onPickFiles;

  static const accent = Color(0xff7656a8);

  @override
  Widget build(BuildContext context) => ColoredBox(
    color: const Color(0xfff6f7fc),
    child: Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 640, maxHeight: 420),
          child: DecoratedBox(
            key: const Key('conversionDropZone'),
            decoration: BoxDecoration(
              color: const Color(0xfff4f1ff),
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: const Color(0xffb9a8e0), width: 2),
            ),
            child: Padding(
              padding: const EdgeInsets.all(32),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(
                    Icons.file_download_outlined,
                    size: 64,
                    color: accent,
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    '여기에 파일을 놓으세요',
                    style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    '파일을 넣으면 바로 변환할 포맷을 고를 수 있어요.\n'
                    'HWP·HWPX·PDF·DOCX·이미지·텍스트 문서를 바꿀 수 있습니다.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 13,
                      height: 1.6,
                      color: Color(0xff64748b),
                    ),
                  ),
                  const SizedBox(height: 20),
                  FilledButton.icon(
                    key: const Key('conversionPickFiles'),
                    style: FilledButton.styleFrom(backgroundColor: accent),
                    onPressed: onPickFiles,
                    icon: const Icon(Icons.folder_open_outlined),
                    label: const Text('파일 선택'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    ),
  );
}
