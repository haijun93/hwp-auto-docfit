import 'dart:io';

import 'package:docfit_ui/features/preview/option_images.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('every mapped option image is bundled and registered', () {
    final pubspec = File('pubspec.yaml').readAsStringSync();
    expect(pubspec, contains('assets/option_images/'));
    expect(pubspec, isNot(contains('hwp_preview')));
    for (final entry in optionImages.entries) {
      expect(
        File(entry.value.asset).existsSync(),
        isTrue,
        reason: '${entry.key} → ${entry.value.asset}',
      );
    }
    for (final key in optionImageMissing) {
      expect(optionImages.containsKey(key), isFalse, reason: key);
    }
  });

  test('settings keys resolve by prefix', () {
    expect(optionImageFor('label_symbols.□')?.file, 'labels.png');
    expect(optionImageFor('table_fonts.header.size')?.file, 'table-format.png');
    expect(optionImageFor('unknown_key'), isNull);
    expect(optionImageFor(null), isNull);
  });

  testWidgets('preview opens a zoom dialog and missing keys stay compact', (
    tester,
  ) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: Column(
            children: [
              SizedBox(width: 400, child: OptionImagePreview('hanging_indent')),
              OptionImagePreview('attachment_font'),
              OptionImageButton('page_fit'),
              OptionImageButton('attachment_font'),
            ],
          ),
        ),
      ),
    );
    expect(find.text('예시 이미지 준비 중'), findsOneWidget);
    expect(
      find.byKey(const ValueKey('option-image-button-attachment_font')),
      findsNothing,
    );
    await tester.tap(find.byKey(const ValueKey('option-image-hanging_indent')));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('option-image-zoom')), findsOneWidget);
    await tester.tap(find.byTooltip('닫기'));
    await tester.pumpAndSettle();
    await tester.tap(
      find.byKey(const ValueKey('option-image-button-page_fit')),
    );
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('option-image-zoom')), findsOneWidget);
  });
}
