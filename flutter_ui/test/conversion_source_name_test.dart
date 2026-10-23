import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/features/conversion/floating_format_picker.dart';

Widget picker(
  String filename, {
  double width = 340,
  int count = 1,
  String selected = 'hwpx',
}) {
  return MaterialApp(
    home: Scaffold(
      body: Center(
        child: SizedBox(
          width: width,
          child: FloatingFormatPicker(
            fileNames: [filename, if (count > 1) '두번째.pdf'],
            fileCount: count,
            selected: selected,
            targets: const [
              {'format': 'hwpx', 'label': 'HWPX', 'enabled': true},
              {'format': 'pdf', 'label': 'PDF', 'enabled': true},
              {'format': 'html', 'label': 'HTML', 'enabled': true},
            ],
            onSelected: (_) {},
            onCancel: () {},
          ),
        ),
      ),
    ),
  );
}

void main() {
  testWidgets('HTML format is selectable in the round format picker', (
    tester,
  ) async {
    String? selected;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SizedBox(
            width: 340,
            child: FloatingFormatPicker(
              fileNames: const ['source.html'],
              fileCount: 1,
              selected: 'hwpx',
              targets: const [
                {'format': 'hwpx', 'label': 'HWPX', 'enabled': true},
                {'format': 'html', 'label': 'HTML', 'enabled': true},
              ],
              onSelected: (format) => selected = format,
              onCancel: () {},
            ),
          ),
        ),
      ),
    );
    await tester.tap(
      find.descendant(
        of: find.byKey(const Key('conversionSlice-html')),
        matching: find.text('HTML'),
      ),
    );
    expect(selected, 'html');
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'disabled slice shows its own reason, and long label wraps on a word',
    (tester) async {
      tester.view.physicalSize = const Size(800, 1000);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      String? selected;
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SizedBox(
              width: 510,
              child: FloatingFormatPicker(
                fileNames: const ['표 서식모음.hwpx'],
                fileCount: 1,
                selected: 'hwpx',
                targets: const [
                  {
                    'format': 'hwpx',
                    'label': 'HWPX',
                    'enabled': false,
                    'reason': '이미 HWPX 파일이라 같은 형식으로는 바꿀 수 없어요',
                  },
                  {
                    'format': 'pdf',
                    'label': 'PDF',
                    'enabled': true,
                    'reason': '한/글 PDF 저장',
                  },
                  {
                    'format': 'pdfm',
                    'label': 'PDF 하나로 합치기',
                    'enabled': false,
                    'reason': '파일을 2개 이상 넣으면 하나의 PDF로 합칠 수 있어요',
                  },
                  {
                    'format': 'pdfz',
                    'label': 'PDF 압축',
                    'enabled': false,
                    'reason': 'PDF 파일에만 쓸 수 있습니다',
                  },
                ],
                onSelected: (format) => selected = format,
                onCancel: () {},
              ),
            ),
          ),
        ),
      );
      // 고를 수 없는 'PDF 압축'을 누르면 아래쪽에 그 칸의 이유(HWPX 같은 형식 안내가 아님)
      await tester.tap(
        find.descendant(
          of: find.byKey(const Key('conversionSlice-pdfz')),
          matching: find.text('PDF 압축'),
        ),
      );
      await tester.pump();
      expect(selected, isNull);
      expect(find.text('고를 수 없음: PDF 압축'), findsOneWidget);
      expect(
        find.byKey(const Key('conversionPrerequisiteNotice')),
        findsOneWidget,
      );
      expect(
        tester
            .widget<Text>(find.byKey(const Key('conversionPrerequisiteNotice')))
            .data,
        'PDF 파일에만 쓸 수 있습니다',
      );
      // 긴 이름은 낱말 경계에서 두 줄
      expect(find.text('PDF 하나로\n합치기'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('center shows original short name and original extension', (
    tester,
  ) async {
    await tester.pumpWidget(picker('안내.hwp'));
    expect(find.text('안내'), findsOneWidget);
    expect(find.text('.hwp'), findsOneWidget);
    final stem = tester.renderObject<RenderParagraph>(
      find.byKey(const Key('conversionSourceStem')),
    );
    expect(stem.didExceedMaxLines, isFalse);
    expect(find.text('변환 결과: HWPX'), findsOneWidget);
    await tester.pumpWidget(picker('안내.hwp', selected: 'pdf'));
    expect(find.text('안내'), findsOneWidget);
    expect(find.text('.hwp'), findsOneWidget);
    expect(find.text('변환 결과: PDF'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  for (final width in [280.0, 340.0]) {
    testWidgets('long source name ellipsizes only stem at width $width', (
      tester,
    ) async {
      const filename = '지주식안내판_철거방침서_검토결과_최종수정본_2026년.HWP';
      await tester.pumpWidget(picker(filename, width: width));
      final stem = tester.renderObject<RenderParagraph>(
        find.byKey(const Key('conversionSourceStem')),
      );
      final extension = tester.renderObject<RenderParagraph>(
        find.byKey(const Key('conversionSourceExtension')),
      );
      expect(stem.didExceedMaxLines, isTrue);
      expect(extension.didExceedMaxLines, isFalse);
      expect(find.text('.HWP'), findsOneWidget);
      expect(
        stem.getBoxesForSelection(
          const TextSelection(baseOffset: 0, extentOffset: 1),
        ),
        isNotEmpty,
      );
      expect(find.byTooltip(filename), findsOneWidget);
      final label = tester.widget<Semantics>(
        find.byKey(const Key('conversionSourceName')),
      );
      expect(label.properties.label, filename);
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets(
    'multiple sources show first basename with count and keep cancel',
    (tester) async {
      await tester.pumpWidget(picker(r'C:\문서\원본.최종.hwpx', count: 2));
      expect(find.text('원본.최종'), findsOneWidget);
      expect(find.text('.hwpx'), findsOneWidget);
      expect(find.text('첫 파일 · 2개'), findsOneWidget);
      expect(find.byKey(const Key('cancelConversionPicker')), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
}
