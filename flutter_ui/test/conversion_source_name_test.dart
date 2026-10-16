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
