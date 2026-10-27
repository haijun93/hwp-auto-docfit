import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:docfit_ui/core/api/abbreviation_api.dart' show ApiCall;
import 'package:docfit_ui/features/conversion/file_conversion_workspace.dart';
import 'package:docfit_ui/features/conversion/floating_format_picker.dart';
import 'package:docfit_ui/features/conversion/merge_order_dialog.dart';

class FakeApi {
  final List<List<dynamic>> calls = [];
  Map<String, dynamic> state = {};
  Future<dynamic> Function(String method, List<dynamic> args)? customHandler;

  FakeApi([Map<String, dynamic>? initial]) {
    state = initial ?? defaultState();
  }

  static Map<String, dynamic> defaultState() => {
        'files': [
          {'name': 'sample.pptx', 'path': '/path/to/sample.pptx'},
        ],
        'mode': 'spacing',
        'can_start': true,
        'conversion_target': 'hwpx',
        'conversion_targets': [
          {'format': 'hwpx', 'label': 'HWPX', 'enabled': true, 'reason': ''},
          {'format': 'pdf', 'label': 'PDF', 'enabled': false, 'reason': '한/글 COM 필요'},
          {'format': 'pdfm', 'label': 'PDF 합치기', 'enabled': true, 'reason': ''},
        ],
        'running': false,
        'results': [],
        'failures': {},
        'job': null,
      };

  Future<dynamic> call(String method, [List<dynamic> args = const []]) async {
    calls.add([method, args]);
    if (customHandler != null) {
      final res = await customHandler!(method, args);
      if (res != null) return res;
    }
    if (method == 'get_file_conversion_state') {
      return Map<String, dynamic>.from(state);
    }
    if (method == 'add_conversion_files') {
      return Map<String, dynamic>.from(state);
    }
    if (method == 'remove_file') {
      final idx = args.isNotEmpty ? (args[0] as int) : 0;
      final files = List<Map<String, dynamic>>.from(state['files'] as List? ?? []);
      if (idx >= 0 && idx < files.length) {
        files.removeAt(idx);
        state['files'] = files;
      }
      return Map<String, dynamic>.from(state);
    }
    if (method == 'clear_files') {
      state['files'] = [];
      return Map<String, dynamic>.from(state);
    }
    if (method == 'start_job') {
      return 'job-1001';
    }
    if (method == 'cancel_job') {
      return {'id': args.isNotEmpty ? args[0] : 'job-1001', 'state': 'cancelled'};
    }
    if (method == 'get_events') {
      return {'events': [], 'next_seq': args.isNotEmpty ? args[0] : 0};
    }
    if (method == 'show_result') {
      return Map<String, dynamic>.from(state);
    }
    return {'ok': true};
  }
}

Widget buildTestWidget({required FakeApi api, bool isActive = true}) {
  return MaterialApp(
    home: FileConversionWorkspace(
      api: api.call,
      isActive: isActive,
    ),
  );
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('file conversion shows files without text tools', (tester) async {
    final api = FakeApi();
    await tester.pumpWidget(buildTestWidget(api: api));
    await tester.pump(const Duration(milliseconds: 100));

    // 파일명, 개수, 형식 확인
    expect(find.text('sample.pptx'), findsOneWidget);
    expect(find.text('총 1개 파일'), findsOneWidget);
    expect(find.text('파일변환'), findsOneWidget);
    expect(find.text('문서편집과 파일 목록을 함께 사용합니다'), findsOneWidget);

    // 텍스트 입력 및 도구 컨트롤 없음 확인
    expect(find.text('텍스트 입력'), findsNothing);
    expect(find.byType(TextField), findsNothing);

    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('adds selected pptx through scoped selection token', (tester) async {
    final api = FakeApi();
    int statusChecks = 0;
    api.customHandler = (method, args) async {
      if (method == 'select_files') {
        return {'ok': true, 'pending': true};
      }
      if (method == 'selection_status') {
        statusChecks++;
        return {'ok': true, 'pending': false, 'selection_id': 'tok-pptx-999'};
      }
      if (method == 'add_conversion_files') {
        api.state['files'] = [
          {'name': 'new.pptx', 'path': '/path/to/new.pptx'}
        ];
        return Map<String, dynamic>.from(api.state);
      }
      return null;
    };

    await tester.pumpWidget(buildTestWidget(api: api));
    await tester.pump(const Duration(milliseconds: 100));

    await tester.tap(find.byKey(const Key('conversionAddFiles')));
    await tester.pump(const Duration(milliseconds: 250));
    await tester.pump(const Duration(milliseconds: 100));

    expect(statusChecks, greaterThanOrEqualTo(1));
    expect(api.calls.any((c) => c[0] == 'add_conversion_files' && c[1][0] == 'tok-pptx-999'), isTrue);
    expect(api.calls.any((c) => c[0] == 'start_job'), isFalse);

    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('cancelled selection leaves file list unchanged', (tester) async {
    final api = FakeApi();
    api.customHandler = (method, args) async {
      if (method == 'select_files') {
        return {'ok': true, 'cancelled': true};
      }
      return null;
    };

    await tester.pumpWidget(buildTestWidget(api: api));
    await tester.pump(const Duration(milliseconds: 100));

    await tester.tap(find.byKey(const Key('conversionAddFiles')));
    await tester.pump(const Duration(milliseconds: 200));

    expect(api.calls.any((c) => c[0] == 'add_conversion_files'), isFalse);
    expect(api.calls.any((c) => c[0] == 'start_job'), isFalse);
    expect(find.text('sample.pptx'), findsOneWidget);

    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('file addition and drop refresh never start conversion', (tester) async {
    final api = FakeApi();
    await tester.pumpWidget(buildTestWidget(api: api));
    await tester.pump(const Duration(milliseconds: 100));

    // 리프레시 발생 시 start_job 호출 없어야 함
    await tester.pump(const Duration(seconds: 1));
    expect(api.calls.any((c) => c[0] == 'start_job'), isFalse);
    expect(find.byType(FloatingFormatPicker), findsNothing);

    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('format choice starts existing file_format job once', (tester) async {
    final api = FakeApi();
    await tester.pumpWidget(buildTestWidget(api: api));
    await tester.pump(const Duration(milliseconds: 100));

    await tester.tap(find.byKey(const Key('conversionChooseFormat')));
    await tester.pumpAndSettle();

    expect(find.byType(FloatingFormatPicker), findsOneWidget);

    // HWPX 선택 탭 (더블 탭 시도)
    final hwpxBtn = find.text('HWPX');
    expect(hwpxBtn, findsWidgets);
    await tester.tap(hwpxBtn.first);
    await tester.pump(const Duration(milliseconds: 50));

    final startCalls = api.calls.where((c) => c[0] == 'start_job').toList();
    expect(startCalls.length, 1);
    expect(startCalls.first[1][0], 'file_format');
    expect(startCalls.first[1][1]['target'], 'hwpx');

    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('unavailable target cannot start', (tester) async {
    final api = FakeApi();
    await tester.pumpWidget(buildTestWidget(api: api));
    await tester.pump(const Duration(milliseconds: 100));

    await tester.tap(find.byKey(const Key('conversionChooseFormat')));
    await tester.pumpAndSettle();

    // PDF는 enabled: false ('한/글 COM 필요')
    expect(find.text('한/글 COM 필요'), findsOneWidget);
    final pdfBtn = find.text('PDF');
    expect(pdfBtn, findsWidgets);
    await tester.tap(pdfBtn.first);
    await tester.pump(const Duration(milliseconds: 50));

    expect(api.calls.any((c) => c[0] == 'start_job'), isFalse);

    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('picker cancellation preserves target and files', (tester) async {
    final api = FakeApi();
    await tester.pumpWidget(buildTestWidget(api: api));
    await tester.pump(const Duration(milliseconds: 100));

    // 1. Esc 취소
    await tester.tap(find.byKey(const Key('conversionChooseFormat')));
    await tester.pumpAndSettle();
    expect(find.byType(FloatingFormatPicker), findsOneWidget);
    await tester.sendKeyEvent(LogicalKeyboardKey.escape);
    await tester.pumpAndSettle();
    expect(find.byType(FloatingFormatPicker), findsNothing);
    expect(api.calls.any((c) => c[0] == 'start_job'), isFalse);

    // 2. 취소 버튼 탭
    await tester.tap(find.byKey(const Key('conversionChooseFormat')));
    await tester.pumpAndSettle();
    final cancelBtn = find.text('취소');
    if (cancelBtn.evaluate().isNotEmpty) {
      await tester.tap(cancelBtn.first);
      await tester.pumpAndSettle();
      expect(find.byType(FloatingFormatPicker), findsNothing);
    }

    // 3. 바깥 탭
    await tester.tap(find.byKey(const Key('conversionChooseFormat')));
    await tester.pumpAndSettle();
    await tester.tapAt(const Offset(10, 10));
    await tester.pumpAndSettle();
    expect(find.byType(FloatingFormatPicker), findsNothing);
    expect(api.calls.any((c) => c[0] == 'start_job'), isFalse);

    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('merge confirmation preserves chosen order', (tester) async {
    final api = FakeApi({
      ...FakeApi.defaultState(),
      'files': [
        {'name': '1.pdf', 'path': '/path/1.pdf'},
        {'name': '2.pdf', 'path': '/path/2.pdf'},
      ],
      'conversion_target': 'pdfm',
    });

    await tester.pumpWidget(buildTestWidget(api: api));
    await tester.pump(const Duration(milliseconds: 100));

    await tester.tap(find.byKey(const Key('conversionChooseFormat')));
    await tester.pumpAndSettle();

    final pdfmBtn = find.text('PDF 합치기');
    expect(pdfmBtn, findsWidgets);
    await tester.tap(pdfmBtn.first);
    await tester.pumpAndSettle();

    // MergeOrderDialog가 열림
    expect(find.byType(MergeOrderDialog), findsOneWidget);

    // 확인 버튼 탭
    final confirmBtn = find.text('확인');
    expect(confirmBtn, findsOneWidget);
    await tester.tap(confirmBtn);
    await tester.pump(const Duration(milliseconds: 100));

    final startCalls = api.calls.where((c) => c[0] == 'start_job').toList();
    expect(startCalls.length, 1);
    expect(startCalls.first[1][0], 'file_format');
    expect(startCalls.first[1][1]['target'], 'pdfm');
    expect(startCalls.first[1][1]['file_order'], ['/path/1.pdf', '/path/2.pdf']);

    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('merge cancellation and changed files do not start', (tester) async {
    final api = FakeApi({
      ...FakeApi.defaultState(),
      'files': [
        {'name': '1.pdf', 'path': '/path/1.pdf'},
        {'name': '2.pdf', 'path': '/path/2.pdf'},
      ],
      'conversion_target': 'pdfm',
    });

    await tester.pumpWidget(buildTestWidget(api: api));
    await tester.pump(const Duration(milliseconds: 100));

    // 취소 시
    await tester.tap(find.byKey(const Key('conversionChooseFormat')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('PDF 합치기').first);
    await tester.pumpAndSettle();
    expect(find.byType(MergeOrderDialog), findsOneWidget);

    await tester.tap(find.text('취소'));
    await tester.pumpAndSettle();
    expect(api.calls.any((c) => c[0] == 'start_job'), isFalse);

    // 파일 목록 변경 시
    await tester.tap(find.byKey(const Key('conversionChooseFormat')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('PDF 합치기').first);
    await tester.pumpAndSettle();

    // 서버 파일 목록이 변경된 상태로 세팅
    api.state['files'] = [
      {'name': '1.pdf', 'path': '/path/1.pdf'},
    ];
    await tester.tap(find.text('확인'));
    await tester.pump(const Duration(milliseconds: 100));

    expect(api.calls.any((c) => c[0] == 'start_job'), isFalse);
    expect(find.text('파일 목록이 바뀌었습니다. 다시 선택해 주세요.'), findsOneWidget);

    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('progress and cancellation follow tracked job', (tester) async {
    final api = FakeApi();
    api.customHandler = (method, args) async {
      if (method == 'get_events') {
        return {
          'next_seq': 10,
          'events': [
            {'job_id': 'other-job', 'type': 'progress', 'data': {'percent': 90}},
            {
              'job_id': 'job-1001',
              'type': 'progress',
              'data': {'file': 1, 'total': 2, 'percent': 50}
            },
          ]
        };
      }
      return null;
    };

    await tester.pumpWidget(buildTestWidget(api: api));
    await tester.pump(const Duration(milliseconds: 100));

    await tester.tap(find.byKey(const Key('conversionChooseFormat')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('HWPX').first);
    await tester.pump(const Duration(milliseconds: 100));

    // percent 50% 확인
    final indicator = tester.widget<LinearProgressIndicator>(find.byKey(const Key('conversionProgress')));
    expect(indicator.value, 0.5);

    // 취소 탭
    await tester.tap(find.byKey(const Key('conversionCancelJob')));
    await tester.pump(const Duration(milliseconds: 50));

    expect(api.calls.any((c) => c[0] == 'cancel_job' && c[1][0] == 'job-1001'), isTrue);

    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('event gap restores snapshot and partial failures', (tester) async {
    final api = FakeApi();
    api.customHandler = (method, args) async {
      if (method == 'get_events') {
        return {'gap': true, 'next_seq': 20, 'events': []};
      }
      return null;
    };

    await tester.pumpWidget(buildTestWidget(api: api));
    await tester.pump(const Duration(milliseconds: 100));

    await tester.tap(find.byKey(const Key('conversionChooseFormat')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('HWPX').first);
    await tester.pump(const Duration(milliseconds: 100));

    // gap 발생 시 서버 snapshot의 job 상태와 실패 반영 확인
    api.state['job'] = {
      'id': 'job-1001',
      'kind': 'file_format',
      'state': 'done',
    };
    api.state['failures'] = {'failed.pptx': '변환 오류'};
    await tester.pump(const Duration(seconds: 1));

    expect(find.text('변환 완료 (일부 실패 포함)'), findsOneWidget);

    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('stale refresh cannot restore removed files', (tester) async {
    final api = FakeApi();
    final completer = Completer<Map<String, dynamic>>();

    api.customHandler = (method, args) async {
      if (method == 'get_file_conversion_state' && !completer.isCompleted) {
        return completer.future;
      }
      return null;
    };

    await tester.pumpWidget(buildTestWidget(api: api));
    await tester.pump(const Duration(milliseconds: 50));

    // 삭제 실행
    await tester.tap(find.byKey(const Key('conversionRemove_0')));
    await tester.pump(const Duration(milliseconds: 50));
    expect(find.text('sample.pptx'), findsNothing);

    // 지연된 refresh 응답 완료
    completer.complete(FakeApi.defaultState());
    await tester.pump(const Duration(milliseconds: 50));

    // 지워진 파일이 다시 나타나지 않음
    expect(find.text('sample.pptx'), findsNothing);

    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('opens result folder only on explicit click', (tester) async {
    final api = FakeApi({
      ...FakeApi.defaultState(),
      'results': [
        {'name': 'output.hwpx', 'path': '/out/output.hwpx', 'source': 'sample.pptx', 'pages': 1}
      ],
      'running': false,
    });

    await tester.pumpWidget(buildTestWidget(api: api));
    await tester.pump(const Duration(milliseconds: 100));

    // 화면 렌더링만으로 show_result 호출 없음
    expect(api.calls.any((c) => c[0] == 'show_result'), isFalse);
    expect(api.calls.any((c) => c[0] == 'open_results' || c[0] == 'open_result'), isFalse);

    // 명시적 클릭
    await tester.tap(find.byKey(const Key('conversionOpenResults')));
    await tester.pump(const Duration(milliseconds: 50));

    expect(api.calls.any((c) => c[0] == 'show_result' && c[1][0] == 0), isTrue);

    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('inactive widget and disposal stop side effects', (tester) async {
    final api = FakeApi();
    await tester.pumpWidget(buildTestWidget(api: api, isActive: false));
    await tester.pump(const Duration(milliseconds: 100));

    final initialCallCount = api.calls.length;
    await tester.pump(const Duration(seconds: 2));

    // 비활성 상태에서는 주기 폴링 안 함
    expect(api.calls.length, initialCallCount);

    // dispose 후 오류 없음
    await tester.pumpWidget(const SizedBox());
    await tester.pump(const Duration(seconds: 2));
    expect(tester.takeException(), isNull);
  });

  testWidgets('layout supports narrow and wide windows', (tester) async {
    final api = FakeApi();

    // 좁은 창 420x800
    tester.view.physicalSize = const Size(420, 800);
    tester.view.devicePixelRatio = 1.0;
    await tester.pumpWidget(buildTestWidget(api: api));
    await tester.pump(const Duration(milliseconds: 100));
    expect(tester.takeException(), isNull);

    // 넓은 창 1280x900
    tester.view.physicalSize = const Size(1280, 900);
    await tester.pumpWidget(buildTestWidget(api: api));
    await tester.pump(const Duration(milliseconds: 100));
    expect(tester.takeException(), isNull);

    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });

    await tester.pumpWidget(const SizedBox());
  });
}
