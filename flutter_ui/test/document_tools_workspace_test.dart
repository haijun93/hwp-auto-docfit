import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/core/close_guards.dart';
import 'package:docfit_ui/features/tools/document_tools_workspace.dart';

Finder field(String label) => find.byWidgetPredicate(
  (widget) => widget is TextField && widget.decoration?.labelText == label,
);

void main() {
  testWidgets('text input converts and adds the result without Tk tools', (
    tester,
  ) async {
    final calls = <String>[];
    final payloads = <Map>[];
    await tester.pumpWidget(
      MaterialApp(
        home: DocumentToolsWorkspace(
          api: (method, args) async {
            calls.add('$method:${args.first}');
            payloads.add(args[1] as Map);
            return {
              'ok': true,
              'data': args.first == 'add_text'
                  ? {'path': 'input.txt'}
                  : {'text': '□ 정리된 답변'},
            };
          },
        ),
      ),
    );
    await tester.enterText(field('입력'), '# 답변');
    await tester.tap(find.text('실행 / 미리보기'));
    await tester.pumpAndSettle();
    expect(calls, ['document_tool:convert']);
    expect(payloads.first['text'], '# 답변');
    expect(
      tester.widget<TextField>(field('변환 결과')).controller!.text,
      '□ 정리된 답변',
    );
    await tester.tap(find.text('문서 목록에 추가'));
    await tester.pumpAndSettle();
    expect(calls.last, 'document_tool:add_text');
    expect(payloads.last['text'], '□ 정리된 답변');
    await tester.tap(find.text('개조식 변환'));
    await tester.pumpAndSettle();
    for (final label in [
      '아웃라이너',
      '문서 구조 검토',
      '공공언어 검토',
      '본문·표 수치 대조',
      'Markdown 내보내기',
      'AI 공문서 요청문',
      '고급 구조 분석·비교·생성',
    ]) {
      expect(find.text(label), findsNothing);
    }
    for (final label in ['AI 답변 기호 정리', '금액 한글화', '주민번호 가리기', '표 합계']) {
      expect(find.text(label), findsOneWidget);
    }
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('pending conversion prevents host close and preserves input', (
    tester,
  ) async {
    final pending = Completer<Object?>();
    final nav = GlobalKey<NavigatorState>();
    await tester.pumpWidget(
      MaterialApp(navigatorKey: nav, home: const SizedBox()),
    );
    unawaited(
      nav.currentState!.push(
        MaterialPageRoute<void>(
          builder: (_) => DocumentToolsWorkspace(api: (_, _) => pending.future),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.enterText(field('입력'), '# 변환할 문장');
    await tester.tap(find.text('실행 / 미리보기'));
    await tester.pump();
    expect(await CloseGuards.prepareAll(), false);
    expect(tester.widget<TextField>(field('입력')).controller!.text, '# 변환할 문장');
    pending.complete({
      'ok': true,
      'data': {'text': '□ 변환할 문장'},
    });
    await tester.pumpAndSettle();
    final close = CloseGuards.prepareAll();
    await tester.pumpAndSettle();
    expect(await close, true);
    expect(find.byType(DocumentToolsWorkspace), findsNothing);
    await tester.pumpWidget(const SizedBox());
  });
}
