import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/features/conversion/conversion_workspace.dart';

class FakeHost implements ConversionHost {
  final calls = <List<Object?>>[];
  final converted = <String>[];
  @override
  final stateVersion = ValueNotifier<int>(0);
  @override
  List files = [
    {'name': '보고서.hwp', 'path': r'C:\a\보고서.hwp', 'size': 3 * 1024 * 1024},
  ];
  @override
  List results = [
    {'name': '보고서.pdf', 'path': r'C:\a\보고서.pdf'},
  ];
  @override
  Map failures = {'참고.docx': '암호가 걸린 문서예요.'};
  @override
  List conversionTargets = [
    {'format': 'pdf', 'label': 'PDF', 'enabled': true},
    {
      'format': 'hwpx',
      'label': 'HWPX',
      'enabled': false,
      'reason': '한/글이 필요해요',
    },
  ];
  @override
  bool locked = false;
  @override
  bool running = false;
  @override
  String statusText = '';
  @override
  double? progressValue;
  @override
  Future<void> command(String method, [List<Object?> args = const []]) async =>
      calls.add([method, ...args]);
  @override
  Future<void> convertTo(String format) async => converted.add(format);
  @override
  Future<void> addConversionFiles() async => calls.add(['add_files']);
  @override
  Map? hwpBulk;
  @override
  Future<Object?> apiCall(String method, List<Object?> args) async {
    calls.add([method, ...args]);
    if (args.first == 'drives') {
      return {
        'ok': true,
        'drives': [r'C:\', r'D:\'],
      };
    }
    if (args.first == 'pick_folder') return {'ok': true, 'folder': r'C:\문서'};
    return {'ok': true};
  }
}

Future<void> _rightClick(WidgetTester tester, Finder target) async {
  final gesture = await tester.startGesture(
    tester.getCenter(target),
    kind: PointerDeviceKind.mouse,
    buttons: kSecondaryMouseButton,
  );
  await gesture.up();
  await tester.pumpAndSettle();
}

void main() {
  Future<FakeHost> pump(WidgetTester tester) async {
    tester.view.physicalSize = const Size(1280, 800);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final host = FakeHost();
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: ConversionWorkspace(host: host)),
      ),
    );
    await tester.pumpAndSettle();
    return host;
  }

  testWidgets('three panels: files with size, formats, results with failures', (
    tester,
  ) async {
    final host = await pump(tester);
    expect(find.text('올린 파일 (1개)'), findsOneWidget);
    expect(find.text('3.0 MB'), findsOneWidget);
    expect(find.text('변환할 포맷 선택'), findsOneWidget);
    expect(find.text('보고서.pdf'), findsOneWidget);
    expect(find.textContaining('암호가 걸린 문서예요.'), findsOneWidget);
    await tester.tap(find.byKey(const Key('conversionFormat-pdf')));
    await tester.tap(
      find.byKey(const Key('conversionFormat-hwpx')),
    ); // 쓸 수 없는 칸
    expect(host.converted, ['pdf']);
    await tester.tap(find.byKey(const Key('conversionOpen-0')));
    await tester.tap(find.byKey(const Key('conversionShow-0')));
    await tester.tap(find.byKey(const Key('conversionOpenFolder')));
    expect(host.calls, [
      ['open_result', 0],
      ['show_result', 0],
      ['show_result', 0],
    ]);
  });

  testWidgets('right-click menus on files and results', (tester) async {
    final host = await pump(tester);
    await _rightClick(tester, find.byKey(const Key('conversionFile-0')));
    expect(find.text('폴더에서 보기'), findsOneWidget);
    await tester.tap(find.byKey(const Key('conversionMenu-폴더에서 보기')));
    await tester.pumpAndSettle();
    expect(host.calls.last, ['show_source_file', 0]);
    await _rightClick(tester, find.byKey(const Key('conversionResult-0')));
    await tester.tap(find.byKey(const Key('conversionMenu-원본 열기')));
    await tester.pumpAndSettle();
    expect(host.calls.last, ['open_result_source', 0]);
    expect(find.text('ZIP'), findsNothing); // ZIP 저장은 만들지 않는다(사용자 지시)
  });

  testWidgets('HWP bulk dialog: folder, password, start payload', (
    tester,
  ) async {
    final host = await pump(tester);
    await tester.tap(find.byKey(const Key('conversionFindHwp')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('hwpBulkDialog')), findsOneWidget);
    // 폴더를 고르지 않고 시작하면 안내만 한다.
    await tester.tap(find.byKey(const Key('hwpBulkStart')));
    await tester.pumpAndSettle();
    expect(find.text('폴더를 먼저 고르세요.'), findsOneWidget);
    await tester.tap(find.byKey(const Key('hwpBulkPickFolder')));
    await tester.pumpAndSettle();
    expect(find.text(r'C:\문서'), findsOneWidget);
    await tester.enterText(find.byKey(const Key('hwpBulkPassword')), 'pw1');
    await tester.tap(find.byKey(const Key('hwpBulkAddPassword')));
    await tester.pumpAndSettle();
    expect(find.text('암호 1 ●●●●'), findsOneWidget);
    expect(find.text('pw1'), findsNothing); // 암호는 화면에 보이지 않는다
    await tester.enterText(find.byKey(const Key('hwpBulkPassword')), 'pw2');
    await tester.tap(find.byKey(const Key('hwpBulkStart')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('hwpBulkDialog')), findsNothing);
    expect(host.calls.last, [
      'hwp_bulk',
      'start',
      {
        'roots': [r'C:\문서'],
        'recursive': true,
        'passwords': ['pw1', 'pw2'],
      },
    ]);
    // 드라이브 전체: 고른 드라이브만 보낸다.
    await tester.tap(find.byKey(const Key('conversionFindHwp')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('드라이브 전체'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key(r'hwpBulkDrive-D:\')));
    await tester.tap(find.byKey(const Key('hwpBulkStart')));
    await tester.pumpAndSettle();
    expect((host.calls.last[2] as Map)['roots'], [r'D:\']);
  });

  testWidgets('HWP bulk card shows progress, failures and report buttons', (
    tester,
  ) async {
    final host = await pump(tester);
    host.hwpBulk = {
      'phase': 'done',
      'found': 3,
      'done': 3,
      'succeeded': 2,
      'failed': 1,
      'skipped_existing': 4,
      'report': r'C:\r.csv',
      'failures': [
        {'source': r'C:\a\암호.hwp', 'message': '암호 문서: 암호가 맞지 않음'},
      ],
    };
    host.stateVersion.value++;
    await tester.pumpAndSettle();
    expect(
      find.text('HWPX 일괄 변환 끝: 변환 2 · 실패 1 · 이미 있어 건너뜀 4'),
      findsOneWidget,
    );
    expect(find.textContaining('암호.hwp: 암호 문서'), findsOneWidget);
    await tester.tap(find.byKey(const Key('hwpBulkOpenReport')));
    await tester.tap(find.byKey(const Key('hwpBulkShowReport')));
    expect(host.calls.sublist(host.calls.length - 2), [
      ['hwp_bulk', 'open_report'],
      ['hwp_bulk', 'show_report'],
    ]);
    host.hwpBulk = {
      'phase': 'convert',
      'found': 10,
      'done': 4,
      'current': r'C:\x.hwp',
    };
    host.stateVersion.value++;
    await tester.pumpAndSettle();
    expect(find.text('HWPX로 바꾸는 중 4 / 10'), findsOneWidget);
    await tester.tap(find.byKey(const Key('hwpBulkStop')));
    expect(host.calls.last, ['hwp_bulk', 'stop']);
  });
}
