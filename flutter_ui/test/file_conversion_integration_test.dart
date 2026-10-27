import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:docfit_ui/main.dart';
import 'package:docfit_ui/features/conversion/file_conversion_workspace.dart';
import 'package:docfit_ui/features/tools/document_tools_workspace.dart';
import 'package:docfit_ui/features/conversion/floating_format_picker.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  Map<String, dynamic> buildDefaultState() => {
        'files': [
          {'name': 'test.hwpx', 'path': '/path/test.hwpx'},
        ],
        'mode': 'spacing',
        'can_start': true,
        'conversion_target': 'hwpx',
        'conversion_targets': [
          {'format': 'hwpx', 'label': 'HWPX', 'enabled': true, 'reason': ''},
        ],
        'running': false,
        'document_drop_revision': 0,
        'range': {'enabled': false, 'start': '1', 'end': '1'},
        'results': [],
        'stages': [],
        'profiles': [],
        'options': {},
        'doc_hints': {},
        'card_options': {},
        'job': null,
      };

  testWidgets('sixth tab mounts FileConversionWorkspace', (tester) async {
    final state = buildDefaultState();
    final calls = <List<dynamic>>[];

    Future<dynamic> mockApi(String method, [List<dynamic> args = const []]) async {
      calls.add([method, args]);
      if (method == 'get_state' || method == 'get_file_conversion_state') {
        return Map<String, dynamic>.from(state);
      }
      return {'ok': true};
    }

    await tester.pumpWidget(DocFitApp(api: mockApi, useIntegratedShell: true));
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('문서편집'), findsOneWidget);
    expect(find.text('표템플릿'), findsOneWidget);
    expect(find.text('표그림판'), findsOneWidget);
    expect(find.text('다이어그램'), findsOneWidget);
    expect(find.text('마인드맵'), findsOneWidget);
    expect(find.text('파일변환'), findsOneWidget);

    expect(find.byType(Workspace), findsOneWidget);

    await tester.tap(find.text('파일변환'));
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.byType(FileConversionWorkspace), findsOneWidget);
    expect(find.byType(DocumentToolsWorkspace), findsNothing);

    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('hidden editor cannot open picker on conversion update', (tester) async {
    final state = buildDefaultState();

    Future<dynamic> mockApi(String method, [List<dynamic> args = const []]) async {
      if (method == 'get_state' || method == 'get_file_conversion_state') {
        return Map<String, dynamic>.from(state);
      }
      return {'ok': true};
    }

    await tester.pumpWidget(DocFitApp(api: mockApi, useIntegratedShell: true));
    await tester.pump(const Duration(milliseconds: 100));

    await tester.tap(find.text('파일변환'));
    await tester.pump(const Duration(milliseconds: 100));

    state['mode'] = 'file_format';
    state['files'] = [
      {'name': 'new.hwpx', 'path': '/path/new.hwpx'},
    ];
    state['document_drop_revision'] = 5;

    await tester.pump(const Duration(seconds: 1));

    expect(find.byKey(const Key('floatingConversionPicker')), findsNothing);

    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('switching tabs preserves conversion job and routes drops', (tester) async {
    final state = buildDefaultState();
    final dropTargetCalls = <String>[];

    Future<dynamic> mockApi(String method, [List<dynamic> args = const []]) async {
      if (method == 'set_drop_target') {
        dropTargetCalls.add(args[0] as String);
      }
      if (method == 'get_state' || method == 'get_file_conversion_state') {
        return Map<String, dynamic>.from(state);
      }
      if (method == 'start_job') {
        return 'job-conv-777';
      }
      if (method == 'get_events') {
        return {'events': [], 'next_seq': 0};
      }
      return {'ok': true};
    }

    await tester.pumpWidget(DocFitApp(api: mockApi, useIntegratedShell: true));
    await tester.pump(const Duration(milliseconds: 100));

    await tester.tap(find.text('파일변환'));
    await tester.pump(const Duration(milliseconds: 100));
    expect(dropTargetCalls.last, 'file_conversion');

    await tester.tap(find.byKey(const Key('conversionChooseFormat')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('HWPX').first);
    await tester.pump(const Duration(milliseconds: 100));

    await tester.tap(find.text('문서편집'));
    await tester.pump(const Duration(milliseconds: 100));
    expect(dropTargetCalls.last, 'documents');

    await tester.tap(find.text('파일변환'));
    await tester.pump(const Duration(milliseconds: 100));
    expect(dropTargetCalls.last, 'file_conversion');

    expect(find.byKey(const Key('conversionCancelJob')), findsOneWidget);

    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('text input keeps original entrypoint', (tester) async {
    final state = buildDefaultState();

    Future<dynamic> mockApi(String method, [List<dynamic> args = const []]) async {
      if (method == 'get_state' || method == 'get_file_conversion_state') {
        return Map<String, dynamic>.from(state);
      }
      return {'ok': true};
    }

    await tester.pumpWidget(DocFitApp(api: mockApi, useIntegratedShell: true));
    await tester.pump(const Duration(milliseconds: 100));

    final textInputBtn = find.text('텍스트 입력');
    if (textInputBtn.evaluate().isNotEmpty) {
      await tester.tap(textInputBtn);
      await tester.pumpAndSettle();

      expect(find.byType(DocumentToolsWorkspace), findsOneWidget);

      final backBtn = find.byTooltip('Back');
      final navigatorBack = find.byType(BackButton);
      if (navigatorBack.evaluate().isNotEmpty) {
        await tester.tap(navigatorBack);
        await tester.pumpAndSettle();
        expect(find.byType(DocumentToolsWorkspace), findsNothing);
      } else if (backBtn.evaluate().isNotEmpty) {
        await tester.tap(backBtn);
        await tester.pumpAndSettle();
        expect(find.byType(DocumentToolsWorkspace), findsNothing);
      }
    }

    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('standalone Workspace retains existing behavior', (tester) async {
    final state = buildDefaultState();

    Future<dynamic> mockApi(String method, [List<dynamic> args = const []]) async {
      if (method == 'get_state') {
        return Map<String, dynamic>.from(state);
      }
      return {'ok': true};
    }

    await tester.pumpWidget(DocFitApp(api: mockApi, useIntegratedShell: false));
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.byType(Workspace), findsOneWidget);
    expect(find.text('파일변환'), findsNothing);

    await tester.pumpWidget(const SizedBox());
  });
}
