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
}
