import 'package:docfit_ui/features/progress/live_progress.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> _spacing({
  bool running = true,
  bool finished = false,
  String now = '본문 자간',
}) => {
  'mode': 'spacing',
  'name': '자간 정리',
  'icon': 'spacing',
  'title': finished ? '글자 간격을 다듬었어요' : '글자 간격을 다듬고 있어요',
  'finished': finished,
  'running': running,
  'message': '줄 끝에서 단어가 갈라지지 않도록 글자 간격을 조정하고 있어요.',
  'now': now,
  'steps': [
    {'key': 'open', 'name': '문서 열기', 'detail': '', 'state': 'done'},
    {
      'key': 'body_spacing',
      'name': '본문 자간',
      'detail': '줄 끝에서 단어가 갈라지지 않도록 글자 간격을 조정하고 있어요.',
      'state': finished ? 'done' : 'active',
    },
    {
      'key': 'save',
      'name': '저장·검사',
      'detail': '',
      'state': finished ? 'done' : 'waiting',
    },
  ],
  'current': 1,
  'doc': {'index': 2, 'total': 3, 'name': '보고서.hwpx'},
  'queue': [
    {'name': 'a.hwpx', 'state': 'done', 'note': 'a(자간조정).hwpx'},
    {'name': '보고서.hwpx', 'state': 'active', 'note': ''},
    {'name': 'c.hwpx', 'state': 'waiting', 'note': ''},
  ],
  'ratio': finished ? 1.0 : 0.5,
  'tips': ['첫 안내', '둘째 안내'],
  'elapsed': 75,
  'target': 'HWPX',
};

Future<void> _pump(WidgetTester tester, Map live, {double width = 1000}) async {
  tester.view.physicalSize = Size(width, 1400);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        body: SingleChildScrollView(
          child: LiveProgress(live: live, onShowLog: () {}),
        ),
      ),
    ),
  );
  await tester.pump(const Duration(milliseconds: 1200));
}

void main() {
  testWidgets('지금 단계·문서 순번·경과 시간·설명을 보여 준다', (tester) async {
    await _pump(tester, _spacing());
    expect(find.text('본문 자간'), findsWidgets); // 아일랜드와 타임라인
    expect(find.text('2/3'), findsOneWidget);
    expect(find.text('1분 15초 경과'), findsOneWidget);
    expect(find.text('단계 1/3'), findsOneWidget);
    expect(find.text('50%'), findsOneWidget);
    expect(
      find.text('줄 끝에서 단어가 갈라지지 않도록 글자 간격을 조정하고 있어요.'),
      findsOneWidget,
    );
    expect(find.text('첫 안내'), findsOneWidget);
  });

  testWidgets('안내 문구는 6초마다 바뀐다', (tester) async {
    await _pump(tester, _spacing());
    await tester.pump(const Duration(seconds: 6));
    await tester.pump(const Duration(milliseconds: 600));
    expect(find.text('둘째 안내'), findsOneWidget);
  });

  testWidgets('끝나면 완료 표시와 걸린 시간을 보여 준다', (tester) async {
    await _pump(tester, _spacing(running: false, finished: true));
    expect(find.text('완료'), findsOneWidget);
    expect(find.byIcon(Icons.check_rounded), findsWidgets);
    expect(find.text('1분 15초 걸림'), findsOneWidget);
    expect(find.text('알고 계셨나요?'), findsNothing);
  });

  testWidgets('파일 변환은 파일 대기열과 실패 이유를 보여 준다', (tester) async {
    await _pump(tester, {
      'mode': 'file_format',
      'name': '파일포맷 변경',
      'icon': 'convert',
      'title': '파일 3개를 PDF로 바꾸고 있어요',
      'finished': false,
      'running': true,
      'message': '회의.docx 파일을 바꾸고 있어요.',
      'now': 'PDF 변환',
      'steps': [],
      'doc': {'index': 3, 'total': 3, 'name': '회의.docx'},
      'queue': [
        {'name': '계획.hwp', 'state': 'done', 'note': '계획.pdf'},
        {'name': '스캔.png', 'state': 'failed', 'note': '글자를 읽지 못했어요'},
        {'name': '회의.docx', 'state': 'active', 'note': ''},
      ],
      'ratio': 0.6667,
      'tips': ['원본 파일은 바꾸지 않아요.'],
      'elapsed': 9,
      'target': 'PDF',
    });
    expect(find.text('PDF 변환'), findsOneWidget);
    expect(find.text('파일 2/3'), findsOneWidget);
    expect(find.text('계획.pdf'), findsOneWidget);
    expect(find.text('글자를 읽지 못했어요 · 원본은 그대로예요'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });

  testWidgets('좁은 화면에서도 넘치지 않는다', (tester) async {
    await _pump(tester, _spacing(), width: 420);
    expect(tester.takeException(), isNull);
  });

  testWidgets('동작 줄이기를 켜면 반복 애니메이션 없이 그린다', (tester) async {
    tester.view.physicalSize = const Size(1000, 1400);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(
      MaterialApp(
        home: MediaQuery(
          data: const MediaQueryData(disableAnimations: true),
          child: Scaffold(
            body: SingleChildScrollView(
              child: LiveProgress(live: _spacing(), onShowLog: () {}),
            ),
          ),
        ),
      ),
    );
    await tester.pump();
    expect(tester.hasRunningAnimations, isFalse);
  });
}
