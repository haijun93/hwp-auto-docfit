import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/main.dart';

void main() {
  for (final width in [420.0, 1024.0]) {
    testWidgets('navigation and scoped commands at width $width', (
      tester,
    ) async {
      tester.view.physicalSize = Size(width, 820);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final calls = <String>[];
      final state = <String, dynamic>{
        'files': <Map<String, String>>[],
        'mode': 'spacing',
        'running': false,
        'range': {'enabled': false, 'start': '1', 'end': '1'},
        'progress': {
          'steps': ['열기', '서식', '저장'],
          'visited': [],
        },
        'results': [],
        'version': 'test',
      };
      Future<Object?> api(String name, List<Object?> args) async {
        calls.add(name);
        if (name == 'add_files') {
          state['files'] = [
            {'name': '문서.hwpx'},
          ];
        }
        if (name == 'set_mode') state['mode'] = args.first;
        if (name == 'start') {
          expect(args, ['unify', false, '1', '1']);
          state['running'] = true;
        }
        return Map<String, dynamic>.from(state);
      }

      await tester.pumpWidget(DocFitApp(api: api));
      await tester.pumpAndSettle();
      await tester.tap(find.text('문서 선택').last);
      await tester.pumpAndSettle();
      expect(find.text('문서.hwpx'), findsOneWidget);
      await tester.tap(find.text('작업 방식 선택'));
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.text('서식 통일'));
      await tester.tap(find.text('서식 통일'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('정리 시작'));
      await tester.pump(const Duration(milliseconds: 300));
      expect(calls.where((s) => s != 'get_state'), [
        'add_files',
        'set_mode',
        'start',
      ]);
      expect(find.text('문서를 정리하고 있어요'), findsOneWidget);
      await tester.tap(find.text(width >= 1000 ? '문서 선택' : '1. 문서 선택').first);
      await tester.pump(const Duration(milliseconds: 300));
      expect(find.text('문서.hwpx'), findsOneWidget);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox());
    });
  }
  testWidgets('disconnected UI never starts work', (tester) async {
    await tester.pumpWidget(
      DocFitApp(api: (method, args) async => throw StateError('offline')),
    );
    await tester.pumpAndSettle();
    expect(find.textContaining('연결하지 못했어요'), findsOneWidget);
    final button = tester.widget<FilledButton>(
      find.widgetWithText(FilledButton, '작업 방식 선택'),
    );
    expect(button.onPressed, isNull);
    await tester.pumpWidget(const SizedBox());
  });
}
