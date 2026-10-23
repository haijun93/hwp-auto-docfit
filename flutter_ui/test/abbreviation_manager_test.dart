import 'dart:async';

import 'package:docfit_ui/core/api/abbreviation_api.dart';
import 'package:docfit_ui/features/abbreviations/abbreviation_manager.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String, Object?> envelope(Map<String, Object?> data) => {
  'api_version': 1,
  'ok': true,
  'data': data,
  'error': null,
};

Map<String, Object?> snapshot({bool running = false}) => {
  'entries': <Map<String, Object?>>[
    {
      'key': '요약',
      'type': 'text',
      'value': '원래 문구',
      'label': '원래 문구',
      'builtin': false,
    },
    {
      'key': '제목1',
      'type': 'format',
      'value': 'title1',
      'label': '제목 서식1',
      'builtin': true,
    },
  ],
  'format_kinds': {'title1': '제목 서식1', 'table': '기본 표 서식'},
  'use_defaults': true,
  'running': running,
};

void main() {
  for (final width in [420.0, 1024.0]) {
    testWidgets('manage, search, rename and delete abbreviations at $width', (
      tester,
    ) async {
      tester.view.physicalSize = Size(width, 820);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final data = snapshot();
      final calls = <List<Object?>>[];
      Future<Object?> api(String name, List<Object?> args) async {
        calls.add([name, ...args]);
        final entries = data['entries'] as List;
        if (name == 'save_abbreviation') {
          entries.removeWhere((row) => (row as Map)['key'] == args[3]);
          entries.add({
            'key': args[0],
            'type': args[1],
            'value': args[2],
            'label': args[2],
            'builtin': false,
          });
        }
        if (name == 'delete_abbreviation') {
          entries.removeWhere((row) => (row as Map)['key'] == args[0]);
        }
        if (name == 'set_abbreviation_defaults') data['use_defaults'] = args[0];
        return envelope(data);
      }

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(body: AbbreviationManager(api: api)),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.text('제목1 · 기본'), findsOneWidget);
      expect(find.byKey(const Key('deleteAbbreviation-제목1')), findsNothing);
      await tester.tap(find.byKey(const Key('addAbbreviationButton')));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.byKey(const Key('abbreviationKeyField')),
        '메모',
      );
      await tester.enterText(
        find.byKey(const Key('abbreviationValueField')),
        '본문',
      );
      await tester.tap(find.byKey(const Key('saveAbbreviationButton')));
      await tester.pumpAndSettle();
      expect(calls.last, ['save_abbreviation', '메모', 'text', '본문', '']);
      expect(find.byKey(const Key('abbreviationValueField')), findsNothing);
      expect(find.text('메모'), findsOneWidget);
      await tester.enterText(
        find.byKey(const Key('abbreviationSearchField')),
        '메모',
      );
      await tester.pumpAndSettle();
      expect(find.text('요약'), findsNothing);
      await tester.tap(find.byKey(const Key('editAbbreviation-메모')));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.byKey(const Key('abbreviationKeyField')),
        '새메모',
      );
      await tester.enterText(
        find.byKey(const Key('abbreviationValueField')),
        '바뀐 본문',
      );
      await tester.tap(find.byKey(const Key('saveAbbreviationButton')));
      await tester.pumpAndSettle();
      expect(calls.last, ['save_abbreviation', '새메모', 'text', '바뀐 본문', '메모']);
      await tester.tap(find.byKey(const Key('deleteAbbreviation-새메모')));
      await tester.pumpAndSettle();
      await tester.tap(find.text('취소'));
      await tester.pumpAndSettle();
      expect(
        calls.where((call) => call.first == 'delete_abbreviation'),
        isEmpty,
      );
      await tester.tap(find.byKey(const Key('deleteAbbreviation-새메모')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('confirmDeleteAbbreviation')));
      await tester.pumpAndSettle();
      expect(calls.last, ['delete_abbreviation', '새메모']);
      expect(find.text('일치하는 준말이 없어요.'), findsOneWidget);
      await tester.tap(find.byKey(const Key('abbreviationDefaultsSwitch')));
      await tester.pumpAndSettle();
      expect(calls.last, ['set_abbreviation_defaults', false]);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox());
    });
  }

  testWidgets('editing a builtin format creates a user override', (
    tester,
  ) async {
    final calls = <List<Object?>>[];
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: AbbreviationManager(
            api: (name, args) async {
              calls.add([name, ...args]);
              return envelope(snapshot());
            },
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('editAbbreviation-제목1')));
    await tester.pumpAndSettle();
    expect(find.text('기본 준말을 고치면 사용자 등록으로 저장돼요.'), findsOneWidget);
    await tester.tap(find.byKey(const Key('abbreviationFormatField')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('기본 표 서식').last);
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('saveAbbreviationButton')));
    await tester.pumpAndSettle();
    expect(calls.last, ['save_abbreviation', '제목1', 'format', 'table', '']);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('save errors keep the editor and input available for retry', (
    tester,
  ) async {
    var fail = true;
    Future<Object?> api(String name, List<Object?> args) async {
      if (name == 'save_abbreviation' && fail) {
        return {
          'api_version': 1,
          'ok': false,
          'data': null,
          'error': {
            'code': 'SETTINGS_WRITE_FAILED',
            'message': '저장 실패. 다시 시도하세요.',
            'recoverable': true,
          },
        };
      }
      return envelope(snapshot());
    }

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: AbbreviationManager(api: api)),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('editAbbreviation-요약')));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const Key('abbreviationValueField')),
      '재시도 문구',
    );
    await tester.tap(find.byKey(const Key('saveAbbreviationButton')));
    await tester.pumpAndSettle();
    expect(find.text('저장 실패. 다시 시도하세요.'), findsOneWidget);
    expect(
      tester
          .widget<TextField>(find.byKey(const Key('abbreviationValueField')))
          .controller!
          .text,
      '재시도 문구',
    );
    fail = false;
    await tester.tap(find.byKey(const Key('saveAbbreviationButton')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('abbreviationValueField')), findsNothing);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets(
    'cancelled edit never writes and pending save cannot be dismissed',
    (tester) async {
      final calls = <String>[];
      final pending = Completer<Object?>();
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AbbreviationManager(
              api: (name, args) async {
                calls.add(name);
                if (name == 'save_abbreviation') return pending.future;
                return envelope(snapshot());
              },
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('editAbbreviation-요약')));
      await tester.pumpAndSettle();
      await tester.tap(find.text('취소'));
      await tester.pumpAndSettle();
      expect(calls, ['get_abbreviations']);
      await tester.tap(find.byKey(const Key('editAbbreviation-요약')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('saveAbbreviationButton')));
      await tester.pump();
      await tester.binding.handlePopRoute();
      await tester.pump();
      expect(find.byKey(const Key('abbreviationValueField')), findsOneWidget);
      expect(
        tester
            .widget<FilledButton>(
              find.byKey(const Key('saveAbbreviationButton')),
            )
            .onPressed,
        isNull,
      );
      pending.complete(envelope(snapshot()));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('abbreviationValueField')), findsNothing);
      expect(calls, ['get_abbreviations', 'save_abbreviation']);
      await tester.pumpWidget(const SizedBox());
    },
  );

  testWidgets('running job locks mutations and a refresh restores editing', (
    tester,
  ) async {
    var running = true;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: AbbreviationManager(
            api: (name, args) async => envelope(snapshot(running: running)),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(
      tester
          .widget<FilledButton>(find.byKey(const Key('addAbbreviationButton')))
          .onPressed,
      isNull,
    );
    expect(
      tester
          .widget<IconButton>(find.byKey(const Key('deleteAbbreviation-요약')))
          .onPressed,
      isNull,
    );
    running = false;
    await tester.tap(find.byKey(const Key('refreshAbbreviationsButton')));
    await tester.pumpAndSettle();
    expect(
      tester
          .widget<FilledButton>(find.byKey(const Key('addAbbreviationButton')))
          .onPressed,
      isNotNull,
    );
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets(
    'closing during a pending load does not update disposed widgets',
    (tester) async {
      final pending = Completer<Object?>();
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AbbreviationManager(api: (name, args) => pending.future),
          ),
        ),
      );
      await tester.pump();
      await tester.pumpWidget(const SizedBox());
      pending.complete(envelope(snapshot()));
      await tester.pump();
      expect(tester.takeException(), isNull);
    },
  );

  test(
    'service API preserves structured errors and rejects incompatible versions',
    () async {
      final api = AbbreviationApi(
        (name, args) async => {
          'api_version': 1,
          'ok': false,
          'data': null,
          'error': {
            'code': 'JOB_RUNNING',
            'message': '작업 중',
            'recoverable': true,
          },
        },
      );
      await expectLater(
        api.delete('요약'),
        throwsA(
          isA<ServiceApiException>()
              .having((error) => error.code, 'code', 'JOB_RUNNING')
              .having((error) => error.recoverable, 'recoverable', isTrue),
        ),
      );
      await expectLater(
        AbbreviationApi((name, args) async => {'api_version': 2}).load(),
        throwsA(
          isA<ServiceApiException>().having(
            (error) => error.code,
            'code',
            'API_VERSION',
          ),
        ),
      );
    },
  );

  testWidgets('document mode opens the HWPX and hides in-app editing', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(420, 820);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final data = snapshot()
      ..['source'] = 'document'
      ..['document'] = {
        'path': r'C:\HWP_AUTODOCFIT\준말관리\준말관리.hwpx',
        'exists': true,
        'errors': ["'가': 본말이 비어 있습니다."],
      };
    final calls = <List<Object?>>[];
    Future<Object?> api(String name, List<Object?> args) async {
      calls.add([name, ...args]);
      if (name == 'abbreviation_document' && args[0] == 'use_settings') {
        data['source'] = 'settings';
      }
      return envelope(data);
    }

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: AbbreviationManager(api: api)),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('abbreviationDocumentPanel')), findsOneWidget);
    expect(find.byKey(const Key('addAbbreviationButton')), findsNothing);
    expect(find.byKey(const Key('editAbbreviation-요약')), findsNothing);
    expect(find.textContaining('본말이 비어'), findsOneWidget);
    await tester.tap(find.byKey(const Key('openAbbreviationDocument')));
    await tester.pumpAndSettle();
    expect(calls.last, ['abbreviation_document', 'open']);
    await tester.tap(find.byKey(const Key('reloadAbbreviationDocument')));
    await tester.pumpAndSettle();
    expect(calls.last, ['abbreviation_document', 'reload']);
    await tester.tap(find.text('앱 설정 사용'));
    await tester.pumpAndSettle();
    expect(calls.last, ['abbreviation_document', 'use_settings']);
    expect(find.byKey(const Key('addAbbreviationButton')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
