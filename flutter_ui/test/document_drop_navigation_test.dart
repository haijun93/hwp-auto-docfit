import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/main.dart';
import 'workspace_test.dart' show initialState;

void main() {
  for (final width in [420.0, 1280.0]) {
    testWidgets('successful document drop advances once at $width', (
      tester,
    ) async {
      tester.view.physicalSize = Size(width, 900);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final state = initialState();
      state['document_drop_revision'] = 0;
      Future<Object?> api(String method, List<Object?> args) async =>
          Map<String, dynamic>.from(state);
      await tester.pumpWidget(DocFitApp(api: api));
      await tester.pumpAndSettle();
      expect(find.text('어떻게 정리할까요?'), findsNothing);
      state['files'] = [
        {
          'path': r'C:\Docs\report.md',
          'name': 'report.md',
          'folder': r'C:\Docs',
        },
      ];
      state['document_drop_revision'] = 1;
      await tester.pump(const Duration(seconds: 1));
      await tester.pumpAndSettle();
      expect(find.text('어떻게 정리할까요?'), findsOneWidget);
      expect(find.byKey(const Key('floatingConversionPicker')), findsNothing);
      await tester.tap(find.text(width >= 1000 ? '문서 선택' : '1. 문서 선택').first);
      await tester.pumpAndSettle();
      // Repeated polls and rejected/duplicate drops retain this screen.
      await tester.pump(const Duration(seconds: 2));
      await tester.pumpAndSettle();
      expect(find.text('어떻게 정리할까요?'), findsNothing);
      // A drop cannot navigate without any accepted input document.
      state['files'] = [];
      state['document_drop_revision'] = 2;
      await tester.pump(const Duration(seconds: 1));
      await tester.pumpAndSettle();
      expect(find.text('어떻게 정리할까요?'), findsNothing);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox());
    });
  }
}
