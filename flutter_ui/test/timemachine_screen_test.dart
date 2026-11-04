import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/features/timemachine/timemachine_screen.dart';

void main() {
  _labelsTest();
  testWidgets('켜기 후 목록과 날짜 머리글 표시', (tester) async {
    final api = _FakeApi();
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:TimemachineScreen(api:api.call))));
    await tester.pumpAndSettle();
    expect(find.text('켜기'),findsOneWidget);
    expect(api.calls.any((call)=>call.$1=='scan'),false);
    await tester.tap(find.text('켜기'));
    await tester.pumpAndSettle();
    expect(api.calls.any((call)=>call.$1=='settings_set'),true);
    expect(api.calls.any((call)=>call.$1=='scan'),true);
    expect(find.text('보고서.pdf'),findsOneWidget);
    expect(find.textContaining('오늘 ·'),findsOneWidget);
  });

  testWidgets('개발자 모드가 꺼져 있으면 본문검색 전환을 숨긴다', (tester) async {
    final api = _FakeApi(enabled: true, developerMode: false);
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: api.call))));
    await tester.pumpAndSettle();
    expect(find.text('파일명'), findsOneWidget);
    expect(find.text('본문'), findsNothing);
  });

  testWidgets('상단 도구는 좁은 창의 더보기에서 접근할 수 있고 overflow가 없다', (tester) async {
    final api = _FakeApi(enabled: true);
    for (final width in [360.0, 800.0, 1400.0]) {
      await tester.binding.setSurfaceSize(Size(width, 900));
      await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: api.call))));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull, reason: '너비 $width');
      if (width < 900) {
        await tester.tap(find.byKey(const ValueKey('tm-more-menu')));
        await tester.pumpAndSettle();
        expect(find.text('다시 훑기'), findsWidgets);
        expect(find.text('썸네일 캐시 지우기'), findsOneWidget);
        await tester.tapAt(const Offset(5, 5));
        await tester.pumpAndSettle();
      } else {
        expect(find.text('다시 훑기'), findsOneWidget);
        expect(find.byKey(const ValueKey('tm-clear-thumb-cache')), findsOneWidget);
      }
      expect(find.text('확장자'), findsOneWidget);
      expect(find.text('파일명'), findsOneWidget);
    }
    await tester.binding.setSurfaceSize(null);
  });

  testWidgets('달력 날짜를 누르면 조회 기간이 바뀐다', (tester) async {
    final api=_FakeApi(enabled:true);
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:TimemachineScreen(api:api.call))));
    await tester.pumpAndSettle();
    final day=DateTime.now().day;
    await tester.tap(find.byKey(ValueKey('tm-day-$day'))); await tester.pumpAndSettle();
    final range=api.calls.where((call)=>call.$1=='range').last.$2;
    expect(range['limit'],200); expect(range['offset'],0);
    expect((range['end'] as double)-(range['start'] as double),closeTo(86400,1));
  });

  testWidgets('달력 요일과 월 날짜 칸은 일요일부터 시작한다', (tester) async {
    final api = _FakeApi(enabled: true);
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: api.call))));
    await tester.pumpAndSettle();
    final weekdays = find.byKey(const ValueKey('tm-calendar-weekdays'));
    final sunday = find.descendant(of: weekdays, matching: find.text('일'));
    final monday = find.descendant(of: weekdays, matching: find.text('월'));
    final firstDay = find.byKey(const ValueKey('tm-day-1'));
    expect(sunday, findsOneWidget);
    expect(monday, findsOneWidget);
    final first = DateTime(DateTime.now().year, DateTime.now().month, 1);
    final sundayColumn = first.weekday % 7;
    final columnWidth = tester.getCenter(monday).dx - tester.getCenter(sunday).dx;
    final actualFirstDay = tester.getCenter(firstDay).dx;
    // Compare the first date's position with the Sunday column's weekday step.
    expect(actualFirstDay - tester.getCenter(sunday).dx,
        closeTo(sundayColumn * columnWidth, 2));
  });

  testWidgets('이번 주 빠른 범위도 일요일부터 계산한다', (tester) async {
    final api = _FakeApi(enabled: true);
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: api.call))));
    await tester.pumpAndSettle();
    await tester.tap(find.text('이번 주'));
    await tester.pumpAndSettle();
    final range = api.calls.where((call) => call.$1 == 'range').last.$2;
    final now = DateTime.now();
    final sunday = DateTime(now.year, now.month, now.day)
        .subtract(Duration(days: now.weekday % 7));
    expect(range['start'], closeTo(sunday.millisecondsSinceEpoch / 1000, 1));
    expect(range['end'], closeTo(sunday.add(const Duration(days: 7)).millisecondsSinceEpoch / 1000, 1));
  });

  testWidgets('카드 누르기와 폴더 열기가 각 명령을 호출한다', (tester) async {
    final api=_FakeApi(enabled:true);
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:TimemachineScreen(api:api.call)))); await tester.pumpAndSettle();
    await tester.tap(find.text('보고서.pdf')); await tester.pumpAndSettle();
    expect(api.calls.any((call)=>call.$1=='open'&&call.$2['id']==42),true);
    await tester.tap(find.text('폴더 열기')); await tester.pumpAndSettle();
    expect(api.calls.any((call)=>call.$1=='reveal'&&call.$2['id']==42),true);
  });

  testWidgets('종류와 이름 필터 변경은 첫 페이지부터 조회한다', (tester) async {
    final api=_FakeApi(enabled:true);
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:TimemachineScreen(api:api.call)))); await tester.pumpAndSettle();
    await tester.tap(find.text('PDF')); await tester.pumpAndSettle();
    expect(api.calls.where((call)=>call.$1=='range').last.$2['offset'],0);
    await tester.enterText(find.byType(TextField),'보고서'); await tester.pump(const Duration(milliseconds:400)); await tester.pumpAndSettle();
    final payload=api.calls.where((call)=>call.$1=='range').last.$2;
    expect(payload['offset'],0); expect(payload['query'],'보고서'); expect(payload['kinds'],['pdf']);
  });

  testWidgets('본문 모드에서 색인하고 본문 검색 결과를 표시한다', (tester) async {
    final api=_FakeApi(enabled:true, developerMode:true);
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:TimemachineScreen(api:api.call)))); await tester.pumpAndSettle();
    await tester.tap(find.text('본문')); await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField),'회의'); await tester.pump(const Duration(milliseconds:400)); await tester.pumpAndSettle();
    expect(api.calls.any((c)=>c.$1=='content_search'&&c.$2['query']=='회의'),true);
    expect(find.text('본문포함.docx'),findsOneWidget);
    final snippet=tester.widget<RichText>(find.textContaining('회의 결과',findRichText:true));
    TextSpan? hit; snippet.text.visitChildren((s){ if(s is TextSpan&&s.text=='회의'){hit=s; return false;} return true; });
    expect(hit!.style!.backgroundColor,const Color(0xFFFFEB3B));
    await tester.tap(find.text('본문 색인')); await tester.pumpAndSettle();
    expect(api.calls.any((c)=>c.$1=='content_index_start'),true);
    expect(find.textContaining('추출 실패 2건'),findsOneWidget);
  });

  testWidgets('썸네일이 오면 그림을 보이고 같은 항목은 다시 요청하지 않는다', (tester) async {
    final api=_FakeApi(enabled:true,thumbnail:{'ok':true,'data':_jpeg});
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:TimemachineScreen(api:api.call)))); await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('tm-thumb-42')),findsOneWidget);
    expect(api.thumbnailCalls,1);
    await tester.tap(find.text('PDF')); await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('tm-thumb-42')),findsOneWidget);
    expect(api.thumbnailCalls,1);
  });

  testWidgets('썸네일이 없거나 실패하면 종류 아이콘을 유지한다', (tester) async {
    for (final answer in <Object?>[{'ok':true,'data':null},{'ok':false,'code':'TM_NOT_FOUND'},{'ok':true,'data':'깨진 값'},Exception('연결 끊김')]) {
      final api=_FakeApi(enabled:true,thumbnail:answer);
      await tester.pumpWidget(MaterialApp(home:Scaffold(body:TimemachineScreen(key:UniqueKey(),api:api.call)))); await tester.pumpAndSettle();
      expect(api.thumbnailCalls,1);
      expect(find.byKey(const ValueKey('tm-thumb-icon-42')),findsOneWidget);
      expect(find.byKey(const ValueKey('tm-thumb-42')),findsNothing);
    }
  });

  testWidgets('깨진 JPEG는 그리다 실패해도 아이콘으로 돌아온다', (tester) async {
    final api=_FakeApi(enabled:true,thumbnail:{'ok':true,'data':base64Encode([0xFF,0xD8,0xFF,0,1,2,3])});
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:TimemachineScreen(api:api.call)))); await tester.pumpAndSettle();
    await tester.runAsync(()=>Future<void>.delayed(const Duration(milliseconds:200))); await tester.pump();
    expect(tester.takeException(),isNull);
    expect(find.byIcon(Icons.picture_as_pdf_outlined),findsOneWidget);
  });

  testWidgets('클라우드 전용 항목은 썸네일을 요청하지 않는다', (tester) async {
    final api=_FakeApi(enabled:true,cloud:true,thumbnail:{'ok':true,'data':_jpeg});
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:TimemachineScreen(api:api.call)))); await tester.pumpAndSettle();
    expect(api.thumbnailCalls,0);
    expect(find.byKey(const ValueKey('tm-thumb-icon-42')),findsOneWidget);
  });

  testWidgets('보이는 항목만 요청하고 동시에 2개까지만 보낸다', (tester) async {
    final api=_FakeApi(enabled:true,itemCount:150,thumbnail:{'ok':true,'data':null},thumbnailDelay:const Duration(milliseconds:10));
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:TimemachineScreen(api:api.call))));
    for(var i=0;i<40;i++) { await tester.pump(const Duration(milliseconds:10)); }
    await tester.pumpAndSettle();
    expect(api.thumbnailCalls,greaterThan(0));
    expect(api.thumbnailCalls,lessThan(60));
    expect(api.maxThumbnailInFlight,lessThanOrEqualTo(2));
  });

  testWidgets('앱을 열면 색인을 요청하고 감시 주체를 표시한다', (tester) async {
    final app=_FakeApi(enabled:true);
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:TimemachineScreen(api:app.call)))); await tester.pumpAndSettle();
    expect(app.calls.where((call)=>call.$1=='scan').length,1);
    await tester.tap(find.byKey(const ValueKey('tm-more-menu')));
    await tester.pumpAndSettle();
    expect(find.text('실시간 감시: 앱을 열 때만'),findsOneWidget);
    await tester.tapAt(const Offset(5,5));
    await tester.pumpAndSettle();
    final agent=_FakeApi(enabled:true,scanBy:'agent');
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:TimemachineScreen(key:UniqueKey(),api:agent.call)))); await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('tm-more-menu')));
    await tester.pumpAndSettle();
    expect(find.text('실시간 감시: K에이전트'),findsOneWidget);
  });

  testWidgets('앱 색인이 끝나면 목록을 새로 읽는다', (tester) async {
    final api=_FakeApi(enabled:true,scanRunning:true);
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:TimemachineScreen(api:api.call)))); await tester.pumpAndSettle();
    final before=api.calls.where((call)=>call.$1=='range').length;
    await tester.pump(const Duration(seconds:1)); await tester.pumpAndSettle();
    expect(api.calls.where((call)=>call.$1=='range').length,greaterThan(before));
  });

  testWidgets('groups_only_when_hour_has_more_than_five_files', (tester) async {
    final now = DateTime.now();
    final baseTime = DateTime(now.year, now.month, now.day, 10, 30).millisecondsSinceEpoch ~/ 1000;
    // 5개: 개별 카드
    final items5 = [
      for (var i = 0; i < 5; i++)
        {'id': 100 + i, 'name': '파일$i.pdf', 'kind': 'pdf', 'size': 10, 'mtime': 1000.0, 'ctime': 1000.0, 'work_time': baseTime.toDouble(), 'flags': <String>[], 'cloud': false, 'folder': 'C:\\TM'}
    ];
    final api5 = _FakeApi(enabled: true, items: items5);
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: api5.call))));
    await tester.pumpAndSettle();
    expect(find.text('파일0.pdf'), findsOneWidget);
    expect(find.text('파일4.pdf'), findsOneWidget);
    expect(find.textContaining('파일 5개'), findsNothing);

    // 6개: 그룹 카드 1개
    final items6 = [
      for (var i = 0; i < 6; i++)
        {'id': 200 + i, 'name': '육$i.pdf', 'kind': 'pdf', 'size': 10, 'mtime': 1000.0, 'ctime': 1000.0, 'work_time': baseTime.toDouble(), 'flags': <String>[], 'cloud': false, 'folder': 'C:\\TM'}
    ];
    final api6 = _FakeApi(enabled: true, items: items6);
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(key: const ValueKey(6), api: api6.call))));
    await tester.pumpAndSettle();
    expect(find.textContaining('파일 6개'), findsOneWidget);
    expect(find.text('육0.pdf'), findsNothing); // 접혀있음

    // 12개: 레이블 "파일 12개", 펼침 후 12개 파일 렌더, 다시 접힘 복원
    final items12 = [
      for (var i = 0; i < 12; i++)
        {'id': 300 + i, 'name': '열둘$i.pdf', 'kind': 'pdf', 'size': 10, 'mtime': 1000.0, 'ctime': 1000.0, 'work_time': baseTime.toDouble(), 'flags': <String>[], 'cloud': false, 'folder': 'C:\\TM'}
    ];
    final api12 = _FakeApi(enabled: true, items: items12);
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(key: const ValueKey(12), api: api12.call))));
    await tester.pumpAndSettle();
    final groupFinder = find.textContaining('파일 12개');
    expect(groupFinder, findsOneWidget);
    expect(find.text('열둘0.pdf'), findsNothing);

    // 펼치기
    await tester.tap(groupFinder);
    await tester.pumpAndSettle();
    expect(find.text('열둘0.pdf'), findsOneWidget);
    expect(find.text('열둘11.pdf'), findsOneWidget);

    // 접기 복원
    await tester.tap(groupFinder);
    await tester.pumpAndSettle();
    expect(find.text('열둘0.pdf'), findsNothing);
  });

  testWidgets('hour_groups_split_at_midnight_and_on_the_hour', (tester) async {
    final now = DateTime.now();
    // 09:59:59 파일 6개, 10:00:00 파일 6개
    final t0959 = DateTime(now.year, now.month, now.day, 9, 59, 59).millisecondsSinceEpoch ~/ 1000;
    final t1000 = DateTime(now.year, now.month, now.day, 10, 0, 0).millisecondsSinceEpoch ~/ 1000;
    // 23:30 파일 6개, 다음 날 00:30 파일 6개
    final t23 = DateTime(now.year, now.month, now.day, 23, 30).millisecondsSinceEpoch ~/ 1000;
    final t00 = DateTime(now.year, now.month, now.day + 1, 0, 30).millisecondsSinceEpoch ~/ 1000;

    final items = [
      for (var i = 0; i < 6; i++)
        {'id': 10 + i, 'name': '오전9시$i.pdf', 'kind': 'pdf', 'size': 1, 'mtime': 1.0, 'ctime': 1.0, 'work_time': t0959.toDouble(), 'flags': <String>[], 'cloud': false, 'folder': 'C:\\TM'},
      for (var i = 0; i < 6; i++)
        {'id': 20 + i, 'name': '오전10시$i.pdf', 'kind': 'pdf', 'size': 1, 'mtime': 1.0, 'ctime': 1.0, 'work_time': t1000.toDouble(), 'flags': <String>[], 'cloud': false, 'folder': 'C:\\TM'},
      for (var i = 0; i < 6; i++)
        {'id': 30 + i, 'name': '자정전$i.pdf', 'kind': 'pdf', 'size': 1, 'mtime': 1.0, 'ctime': 1.0, 'work_time': t23.toDouble(), 'flags': <String>[], 'cloud': false, 'folder': 'C:\\TM'},
      for (var i = 0; i < 6; i++)
        {'id': 40 + i, 'name': '자정후$i.pdf', 'kind': 'pdf', 'size': 1, 'mtime': 1.0, 'ctime': 1.0, 'work_time': t00.toDouble(), 'flags': <String>[], 'cloud': false, 'folder': 'C:\\TM'},
    ];
    final api = _FakeApi(enabled: true, items: items);
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: api.call))));
    await tester.pumpAndSettle();

    // 09:00~10:00, 10:00~11:00 분리 확인
    expect(find.textContaining('09:00~10:00 파일 6개'), findsOneWidget);
    expect(find.textContaining('10:00~11:00 파일 6개'), findsOneWidget);
    // 23:00~24:00, 00:00~01:00 자정 분리 확인
    expect(find.textContaining('23:00~24:00 파일 6개'), findsOneWidget);
    expect(find.textContaining('00:00~01:00 파일 6개'), findsOneWidget);
  });

  testWidgets('group_boundary_at_page_edge_does_not_merge_unloaded_rows', (tester) async {
    final now = DateTime.now();
    final t10 = DateTime(now.year, now.month, now.day, 10, 30).millisecondsSinceEpoch ~/ 1000;
    // 200개 아이템 중 마지막 3개가 10시
    final firstPage = [
      for (var i = 0; i < 197; i++)
        {'id': 1 + i, 'name': '기타$i.pdf', 'kind': 'pdf', 'size': 1, 'mtime': 1.0, 'ctime': 1.0, 'work_time': (t10 + 3600 + 196 - i).toDouble(), 'flags': <String>[], 'cloud': false, 'folder': 'C:\\TM'},
      for (var i = 0; i < 3; i++)
        {'id': 198 + i, 'name': '끝파일$i.pdf', 'kind': 'pdf', 'size': 1, 'mtime': 1.0, 'ctime': 1.0, 'work_time': t10.toDouble(), 'flags': <String>[], 'cloud': false, 'folder': 'C:\\TM'},
    ];
    final api = _FakeApi(enabled: true, items: firstPage);
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: api.call))));
    await tester.pumpAndSettle();

    // 페이지 내에서 3개뿐이므로 그룹 카드가 생성되지 않음
    expect(find.textContaining('파일 3개'), findsNothing);
    // 묶음으로 목록이 짧아져 스크롤이 안 되어도 다음 쪽으로 갈 수 있어야 한다.
    expect(find.text('더 불러오기'), findsOneWidget);
  });

  testWidgets('hour_density_requests_current_range_and_filters', (tester) async {
    final api = _FakeApi(enabled: true, hours: {10: 5, 14: 12});
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: api.call))));
    await tester.pumpAndSettle();

    final densityCalls = api.calls.where((c) => c.$1 == 'hour_density').toList();
    expect(densityCalls.isNotEmpty, true);
    final payload = densityCalls.last.$2;
    expect(payload.containsKey('start'), true);
    expect(payload.containsKey('end'), true);
    expect(payload.containsKey('roots'), true);
    expect(payload.containsKey('kinds'), true);
    expect(payload.containsKey('query'), true);

    expect(find.bySemanticsLabel('10시, 5개'), findsOneWidget);
    expect(find.bySemanticsLabel('14시, 12개'), findsOneWidget);
  });

  testWidgets('hour_density_stale_response_is_ignored', (tester) async {
    final api = _FakeApi(enabled: true, hours: {10: 8});
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: api.call))));
    await tester.pumpAndSettle();
    expect(find.bySemanticsLabel('10시, 8개'), findsOneWidget);

    // 필터 변경 -> 새 요청 발송
    await tester.tap(find.text('PDF'));
    await tester.pumpAndSettle();
    expect(api.calls.where((c) => c.$1 == 'hour_density').length, greaterThanOrEqualTo(2));
  });

  testWidgets('card_send_menu_calls_service_with_id_only', (tester) async {
    final api = _FakeApi(enabled: true);
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: api.call))));
    await tester.pumpAndSettle();

    // 메뉴 열기
    await tester.tap(find.byKey(const ValueKey('tm-send-menu-42')));
    await tester.pumpAndSettle();

    // 파일명 일괄변경 목록에 추가
    await tester.tap(find.text('파일명 일괄변경 목록에 추가'));
    await tester.pumpAndSettle();

    final sendCalls = api.calls.where((c) => c.$1 == 'send_to_feature').toList();
    expect(sendCalls.isNotEmpty, true);
    final payload = sendCalls.last.$2;
    expect(payload['feature'], 'rename_batch');
    expect(payload['ids'], [42]);
    expect(payload.containsKey('path'), false);
    expect(payload.containsKey('folder'), false);

    // 스낵바 확인
    expect(find.text('목록에 추가했습니다.'), findsOneWidget);

    // open 및 reveal 버튼 독립성 확인
    await tester.tap(find.text('보고서.pdf'));
    await tester.pumpAndSettle();
    expect(api.calls.any((c) => c.$1 == 'open' && c.$2['id'] == 42), true);

    await tester.tap(find.text('폴더 열기'));
    await tester.pumpAndSettle();
    expect(api.calls.any((c) => c.$1 == 'reveal' && c.$2['id'] == 42), true);
  });


  testWidgets('연관 문서 메뉴에 점수·근거·기준일 없음 및 제외를 표시한다', (tester) async {
    final api = _FakeApi(enabled: true);
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: api.call))));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('tm-send-menu-42')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('연관 문서 찾기'));
    await tester.pumpAndSettle();
    expect(api.calls.any((c) => c.$1 == 'related_search' && c.$2['path'] == 'C:\\Temp\\TM\\보고서.pdf'), isTrue);
    expect(find.textContaining('기준일 없음'), findsNWidgets(2));
    expect(find.textContaining('점수 82'), findsOneWidget);
    expect(find.textContaining('공통 단어: 사업'), findsOneWidget);
    await tester.tap(find.text('연관 아님'));
    await tester.pumpAndSettle();
    expect(api.calls.any((c) => c.$1 == 'related_exclude' && c.$2['related_path'] == 'C:\\Temp\\TM\\연관.docx'), isTrue);
  });

  testWidgets('cache_clear_clears_service_and_memory_cache', (tester) async {
    final api = _FakeApi(enabled: true);
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: api.call))));
    await tester.pumpAndSettle();

    final clearBtn = find.byKey(const ValueKey('tm-clear-thumb-cache'));
    expect(clearBtn, findsNothing);
    await tester.tap(find.byKey(const ValueKey('tm-more-menu')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('썸네일 캐시 지우기'));
    await tester.pumpAndSettle();

    expect(api.calls.any((c) => c.$1 == 'thumbnail_cache_clear'), true);
    expect(find.text('썸네일 캐시를 지웠습니다.'), findsOneWidget);
  });

  testWidgets('본문 검색 신형 응답의 폴더, 전체 경로, 횟수, 위치, 위계를 표시한다', (tester) async {
    final api = _FakeApi(enabled: true, contentSearchResults: [
      {'id':42,'file_name':'예산안.hwpx','folder_name':'기획팀','folder_path':'C:\\문서\\기획팀','path':'C:\\문서\\기획팀\\예산안.hwpx','kind':'hwpx','size':10240,'mtime':1791000000.0,'ctime':1789000000.0,'snippet':'2026년 예산 집행 보고','match_counts':{'예산':12,'집행':5},'total_matches':17,'page':3,'hierarchy':'제2장 예산','hierarchy_rank':1,'bm25':0.82}
    ]);
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: api.call))));
    await tester.pumpAndSettle();
    await tester.tap(find.text('본문'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), '예산 집행');
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pumpAndSettle();
    expect(find.text('예산안.hwpx'), findsOneWidget);
    expect(find.textContaining('기획팀'), findsWidgets);
    expect(find.textContaining('예산 12'), findsOneWidget);
    expect(find.textContaining('합계 17'), findsOneWidget);
    expect(find.text('3p'), findsOneWidget);
    expect(find.textContaining('제2장 예산'), findsOneWidget);
  });
  testWidgets('본문 검색 구형 응답 name path snippet을 계속 표시한다', (tester) async {
    final api = _FakeApi(
      enabled: true,
      contentSearchResults: [
        {
          'name': '구형문서.txt',
          'path': 'C:\\레거시폴더\\구형문서.txt',
          'snippet': '구형 응답 스니펫 테스트 내용',
        }
      ],
    );
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: api.call))));
    await tester.pumpAndSettle();
    await tester.tap(find.text('본문'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), '테스트');
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pumpAndSettle();

    expect(find.text('구형문서.txt'), findsOneWidget);
    expect(find.textContaining('레거시폴더'), findsWidgets);
    expect(find.textContaining('구형 응답 스니펫 테스트 내용'), findsOneWidget);
  });

  testWidgets('본문 검색은 기본 정렬을 위계기반 연관도로 매번 초기화한다', (tester) async {
    final api = _FakeApi(
      enabled: true,
      contentSearchResults: [
        {
          'id': 1,
          'file_name': '문서1.hwpx',
          'snippet': '내용 1',
          'match_counts': {'내용': 1},
          'total_matches': 1,
          'hierarchy_rank': 1,
        }
      ],
    );
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: api.call))));
    await tester.pumpAndSettle();
    await tester.tap(find.text('본문'));
    await tester.pumpAndSettle();

    expect(find.text('위계기반 연관도'), findsOneWidget);

    // 다른 정렬 선택
    await tester.tap(find.byKey(const ValueKey('tm-content-sort-dropdown')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('언급 횟수 많은 순').last);
    await tester.pumpAndSettle();
    expect(find.text('언급 횟수 많은 순'), findsOneWidget);

    // 새 검색 시작 -> 기본 정렬 '위계기반 연관도'로 매번 초기화
    await tester.enterText(find.byType(TextField), '새검색');
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pumpAndSettle();
    expect(find.text('위계기반 연관도'), findsOneWidget);

    // 모드 전환 시에는 기본 정렬 '위계기반 연관도'로 복구
    await tester.tap(find.text('파일명'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('본문'));
    await tester.pumpAndSettle();
    expect(find.text('위계기반 연관도'), findsOneWidget);
  });

  testWidgets('본문 위계기반 연관도는 위계와 언급 횟수 뒤 최근 문서를 먼저 둔다', (tester) async {
    final api = _FakeApi(
      enabled: true,
      contentSearchResults: [
        {
          'id': 1,
          'file_name': '오래된문서.hwpx',
          'snippet': '내용',
          'match_counts': {'단어': 5},
          'total_matches': 5,
          'hierarchy': '1장',
          'hierarchy_rank': 1,
          'mtime': 1000.0,
          'ctime': 1000.0,
          'bm25': 0.9,
        },
        {
          'id': 2,
          'file_name': '최신문서.hwpx',
          'snippet': '내용',
          'match_counts': {'단어': 5},
          'total_matches': 5,
          'hierarchy': '1장',
          'hierarchy_rank': 1,
          'mtime': 2000.0,
          'ctime': 2000.0,
          'bm25': 0.1,
        },
        {
          'id': 3,
          'file_name': '낮은위계문서.hwpx',
          'snippet': '내용',
          'match_counts': {'단어': 50},
          'total_matches': 50,
          'hierarchy': '2장',
          'hierarchy_rank': 2,
          'mtime': 3000.0,
          'ctime': 3000.0,
          'bm25': 1.0,
        },
      ],
    );
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: api.call))));
    await tester.pumpAndSettle();
    await tester.tap(find.text('본문'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), '단어');
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pumpAndSettle();

    final yRecent = tester.getTopLeft(find.text('최신문서.hwpx')).dy;
    final yOld = tester.getTopLeft(find.text('오래된문서.hwpx')).dy;
    final yLower = tester.getTopLeft(find.text('낮은위계문서.hwpx')).dy;

    expect(yRecent < yLower, isTrue);
    expect(yOld < yLower, isTrue);
    expect(yRecent < yOld, isTrue);
  });

  testWidgets('본문 언급 횟수 정렬은 총 언급 많은 순이다', (tester) async {
    final api = _FakeApi(
      enabled: true,
      contentSearchResults: [
        {
          'id': 1,
          'file_name': '언급적음.hwpx',
          'snippet': '내용',
          'match_counts': {'단어': 3},
          'total_matches': 3,
          'hierarchy_rank': 1,
        },
        {
          'id': 2,
          'file_name': '언급많음.hwpx',
          'snippet': '내용',
          'match_counts': {'단어': 30},
          'total_matches': 30,
          'hierarchy_rank': 2,
        },
      ],
    );
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: api.call))));
    await tester.pumpAndSettle();
    await tester.tap(find.text('본문'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), '단어');
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const ValueKey('tm-content-sort-dropdown')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('언급 횟수 많은 순').last);
    await tester.pumpAndSettle();

    final yMany = tester.getTopLeft(find.text('언급많음.hwpx')).dy;
    final yFew = tester.getTopLeft(find.text('언급적음.hwpx')).dy;
    expect(yMany < yFew, isTrue);
  });

  testWidgets('검색 연산자 도움말은 본문 모드에서 표시되고 파일명 모드에서는 숨긴다', (tester) async {
    final api = _FakeApi(enabled: true);
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: api.call))));
    await tester.pumpAndSettle();

    expect(find.byTooltip('검색 연산자 도움말'), findsNothing);

    await tester.tap(find.text('본문'));
    await tester.pumpAndSettle();
    final helpBtn = find.byTooltip('검색 연산자 도움말');
    expect(helpBtn, findsOneWidget);

    await tester.ensureVisible(helpBtn);
    await tester.tap(helpBtn);
    await tester.pumpAndSettle();

    expect(find.textContaining('"구문"'), findsOneWidget);
    expect(find.textContaining('-낱말'), findsOneWidget);
    expect(find.textContaining('ext:'), findsOneWidget);
    expect(find.textContaining('path:'), findsOneWidget);
    expect(find.textContaining('after:'), findsOneWidget);
    expect(find.textContaining('before:'), findsOneWidget);
    expect(find.textContaining('~N'), findsOneWidget);
    expect(find.textContaining('AND'), findsOneWidget);

    await tester.tap(find.byTooltip('닫기'));
    await tester.pumpAndSettle();
    expect(find.textContaining('"구문"'), findsNothing);
  });

  testWidgets('본문 결과 클릭은 일치 위치 미리보기, 더블클릭은 문서 열기를 호출한다', (tester) async {
    final api = _FakeApi(
      enabled: true,
      contentSearchResults: [
        {
          'id': 42,
          'file_name': '보고서.hwpx',
          'path': 'C:\\TM\\보고서.hwpx',
          'snippet': '본문 스니펫',
          'match_counts': {'키워드': 2},
          'total_matches': 2,
          'page': 5,
        }
      ],
    );
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: api.call))));
    await tester.pumpAndSettle();
    await tester.tap(find.text('본문'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), '키워드');
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pumpAndSettle();

    // 단일 클릭 -> preview 호출
    await tester.tap(find.text('보고서.hwpx').first);
    await tester.pump(const Duration(milliseconds: 350));
    await tester.pumpAndSettle();
    expect(api.calls.any((c) => c.$1 == 'preview' && c.$2['id'] == 42 && c.$2['page'] == 5), isTrue);
    expect(find.text('일치 위치 본문 미리보기'), findsOneWidget);

    // 더블클릭 -> open 호출
    await tester.tap(find.text('보고서.hwpx').first);
    await tester.pump(const Duration(milliseconds: 50));
    await tester.tap(find.text('보고서.hwpx').first);
    await tester.pumpAndSettle();
    expect(api.calls.any((c) => c.$1 == 'open' && c.$2['id'] == 42), isTrue);
  });

  testWidgets('오래된 미리보기 응답은 새 선택을 덮지 않는다', (tester) async {
    final completer1 = Completer<Map<String, Object?>>();
    final completer2 = Completer<Map<String, Object?>>();

    final api = _FakeApi(
      enabled: true,
      contentSearchResults: [
        {
          'id': 101,
          'file_name': '첫번째.hwpx',
          'snippet': '첫번째 요약',
          'total_matches': 1,
        },
        {
          'id': 102,
          'file_name': '두번째.hwpx',
          'snippet': '두번째 요약',
          'total_matches': 1,
        },
      ],
      previewHandler: (payload) {
        if (payload['id'] == 101) return completer1.future;
        return completer2.future;
      },
    );

    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: api.call))));
    await tester.pumpAndSettle();
    await tester.tap(find.text('본문'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), '단어');
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pumpAndSettle();

    // 첫 번째 문서 클릭 (느린 응답)
    await tester.tap(find.text('첫번째.hwpx'));
    await tester.pump(const Duration(milliseconds: 350));
    await tester.pump();

    // 두 번째 문서 클릭 (빠른 응답)
    await tester.tap(find.text('두번째.hwpx'));
    await tester.pump(const Duration(milliseconds: 350));
    await tester.pump();

    // 두 번째 응답 완료
    completer2.complete({'ok': true, 'snippet': '두번째의 최신 미리보기 내용'});
    await tester.pumpAndSettle();
    expect(find.textContaining('두번째의 최신 미리보기 내용'), findsOneWidget);

    // 첫 번째 오래된 응답 도착 -> 덮어쓰지 않아야 함
    completer1.complete({'ok': true, 'snippet': '오래된 첫번째 응답 내용'});
    await tester.pumpAndSettle();
    expect(find.textContaining('두번째의 최신 미리보기 내용'), findsOneWidget);
    expect(find.textContaining('오래된 첫번째 응답 내용'), findsNothing);
  });

  testWidgets('파일명 결과 열 정렬과 너비 조절을 지원한다', (tester) async {
    final api = _FakeApi(
      enabled: true,
      items: [
        {
          'id': 1,
          'name': '가가가.pdf',
          'kind': 'pdf',
          'size': 2048,
          'mtime': 1000.0,
          'ctime': 1000.0,
          'work_time': 1000.0,
          'flags': [],
          'cloud': false,
          'folder': 'C:\\TM',
        },
        {
          'id': 2,
          'name': '나나나.pdf',
          'kind': 'pdf',
          'size': 1024,
          'mtime': 2000.0,
          'ctime': 2000.0,
          'work_time': 2000.0,
          'flags': [],
          'cloud': false,
          'folder': 'C:\\TM',
        },
      ],
    );
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: api.call))));
    await tester.pumpAndSettle();

    final tableBtn = find.byTooltip('열 보기');
    await tester.ensureVisible(tableBtn);
    await tester.tap(tableBtn);
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('tm-col-header-name')), findsOneWidget);
    expect(find.byKey(const ValueKey('tm-col-header-folder')), findsOneWidget);
    expect(find.byKey(const ValueKey('tm-col-header-size')), findsOneWidget);
    expect(find.byKey(const ValueKey('tm-col-header-mtime')), findsOneWidget);
    expect(find.byKey(const ValueKey('tm-col-header-kind')), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('tm-col-header-name')));
    await tester.pumpAndSettle();
    final yNa = tester.getTopLeft(find.text('나나나.pdf')).dy;
    final yGa = tester.getTopLeft(find.text('가가가.pdf')).dy;
    expect(yNa < yGa, isTrue);

    final resizer = find.byKey(const ValueKey('tm-col-resizer-name'));
    final beforeWidth = tester.getSize(find.byKey(const ValueKey('tm-col-header-name'))).width;
    await tester.drag(resizer, const Offset(60, 0));
    await tester.pumpAndSettle();
    final afterWidth = tester.getSize(find.byKey(const ValueKey('tm-col-header-name'))).width;
    expect(afterWidth, greaterThan(beforeWidth));
  });

  testWidgets('기존 타임라인 카드 클릭은 여전히 열기 명령을 보낸다', (tester) async {
    final api = _FakeApi(enabled: true);
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: api.call))));
    await tester.pumpAndSettle();
    await tester.tap(find.text('보고서.pdf'));
    await tester.pumpAndSettle();
    expect(api.calls.any((call) => call.$1 == 'open' && call.$2['id'] == 42), isTrue);
  });

  testWidgets('파일명 모드 열 보기는 file_search 결과를 공급받고 구형 서비스는 시간순 화면으로 폴백한다', (tester) async {
    // 1. 신형 서비스: file_search 성공
    final apiNew = _FakeApi(
      enabled: true,
      fileSearchResults: [
        {
          'id': 100,
          'name': '검색결과파일.pdf',
          'kind': 'pdf',
          'size': 4096,
          'mtime': 1234.0,
          'ctime': 1234.0,
          'work_time': 1234.0,
          'flags': [],
          'cloud': false,
          'folder': 'C:\\Results',
        }
      ],
    );
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: apiNew.call))));
    await tester.pumpAndSettle();

    // 열 보기 누르기
    final tableBtn = find.byTooltip('열 보기');
    await tester.ensureVisible(tableBtn);
    await tester.tap(tableBtn);
    await tester.pumpAndSettle();

    // file_search 호출 및 표에 검색결과 표시 확인
    expect(apiNew.calls.any((c) => c.$1 == 'file_search'), isTrue);
    expect(find.text('검색결과파일.pdf'), findsOneWidget);

    // 2. 구형 서비스: file_search 미지원 시 시간순 화면으로 폴백
    final apiOld = _FakeApi(
      enabled: true,
      fileSearchSupported: false,
    );
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: TimemachineScreen(
          key: const ValueKey('old-api-screen'),
          api: apiOld.call,
        ),
      ),
    ));
    await tester.pumpAndSettle();

    final tableBtnOld = find.byTooltip('열 보기');
    await tester.ensureVisible(tableBtnOld);
    await tester.tap(tableBtnOld);
    await tester.pumpAndSettle();

    // file_search 미지원 감지 후 열 보기 버튼이 숨겨지고 시간순 타임라인 화면 유지/폴백 확인
    expect(find.byTooltip('열 보기'), findsNothing);
    expect(find.text('보고서.pdf'), findsOneWidget);
  });

  testWidgets('본문 검색 응답에 손상된 항목이 섞여 있어도 정상 항목을 파싱하여 표시한다', (tester) async {
    final api = _FakeApi(
      enabled: true,
      contentSearchResults: [
        {
          'id': '손상된ID_문자열',
          'file_name': '손상문서.hwpx',
          'size': '잘못된크기',
          'mtime': '잘못된날짜',
          'match_counts': {'키': '문자열횟수'},
          'total_matches': '문자열합계',
        },
        {
          'id': 42,
          'file_name': '정상문서.hwpx',
          'folder_name': '정상폴더',
          'folder_path': 'C:\\Normal\\정상폴더',
          'path': 'C:\\Normal\\정상폴더\\정상문서.hwpx',
          'snippet': '정상 스니펫 내용',
          'match_counts': {'정상': 3},
          'total_matches': 3,
          'page': 2,
        },
      ],
    );
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: api.call))));
    await tester.pumpAndSettle();
    await tester.tap(find.text('본문'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), '정상');
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pumpAndSettle();

    expect(find.text('정상문서.hwpx'), findsOneWidget);
    expect(find.textContaining('정상폴더'), findsWidgets);
    expect(find.textContaining('정상 3'), findsOneWidget);
    expect(find.text('2p'), findsOneWidget);
  });
}

// 1×1 JPEG
const _jpeg='/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA=';

void _labelsTest() {
  testWidgets('종류 필터는 확장자 이름으로 보인다', (tester) async {
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: _FakeApi(enabled: true).call))));
    await tester.pumpAndSettle();
    for (final label in ['hwpx', 'docx', 'xlsx', 'ppt', 'PDF', '이미지']) {
      expect(find.widgetWithText(FilterChip, label), findsOneWidget);
    }
    expect(find.widgetWithText(FilterChip, '한/글'), findsNothing);
  });
}

class _FakeApi {
  _FakeApi({
    this.enabled = false,
    this.thumbnail = const {'ok': true, 'data': null},
    this.cloud = false,
    this.itemCount = 1,
    this.items,
    this.thumbnailDelay = Duration.zero,
    this.scanBy = 'app',
    this.scanRunning = false,
    this.hours,
    this.contentSearchResults,
    this.previewHandler,
    this.fileSearchResults,
    this.fileSearchSupported = true,
    this.developerMode = true,
  });

  final bool enabled, cloud, scanRunning, developerMode;
  final Object? thumbnail;
  final int itemCount;
  final List<Map<String, Object?>>? items;
  final Duration thumbnailDelay;
  final String scanBy;
  final Map<int, int>? hours;
  final List<Map<String, Object?>>? contentSearchResults;
  final List<Map<String, Object?>>? fileSearchResults;
  final bool fileSearchSupported;
  final Future<Map<String, Object?>> Function(Map<String, Object?> payload)? previewHandler;
  int thumbnailCalls = 0, _inFlight = 0, maxThumbnailInFlight = 0;
  final List<(String, Map<String, Object?>)> calls = [];

  Future<Object?> call(String method, List<Object?> args) async {
    if (method == 'get_settings') return {'api_version':1,'ok':true,'data':{'values':{'developer_mode':developerMode}}, 'developer_mode':developerMode};
    if (method != 'timemachine') return {'ok': true};
    final action = args[0] as String;
    final payload = Map<String, Object?>.from(args.length > 1 ? args[1] as Map : {});
    calls.add((action, payload));
    switch (action) {
      case 'status':
        return {
          'ok': true,
          'enabled': enabled,
          'stats': {'files': 1},
          'agent_running': scanBy == 'agent',
          'watch': scanBy,
          'scan': {'running': false}
        };
      case 'scan':
        return scanBy == 'agent' ? {'ok': true, 'by': 'agent'} : {'ok': true, 'by': 'app', if (scanRunning) 'running': true};
      case 'content_index_start':
        return {'ok':true,'running':false,'seen':5,'indexed':3,'errors':2};
      case 'content_index_status':
        return {'ok':true,'running':false,'seen':5,'indexed':3,'errors':2};
      case 'content_index_cancel':
        return {'ok':true,'running':false,'seen':5,'indexed':3,'errors':2};
      case 'file_search':
        if (!fileSearchSupported) {
          return {'ok': false, 'code': 'UNKNOWN_ACTION', 'message': '알 수 없는 명령입니다.'};
        }
        return {
          'ok': true,
          'items': fileSearchResults ?? items ?? [
            {
              'id': 1,
              'name': '가가가.pdf',
              'kind': 'pdf',
              'size': 2048,
              'mtime': 1000.0,
              'ctime': 1000.0,
              'work_time': 1000.0,
              'flags': [],
              'cloud': false,
              'folder': 'C:\\TM',
            },
            {
              'id': 2,
              'name': '나나나.pdf',
              'kind': 'pdf',
              'size': 1024,
              'mtime': 2000.0,
              'ctime': 2000.0,
              'work_time': 2000.0,
              'flags': [],
              'cloud': false,
              'folder': 'C:\\TM',
            },
          ],
        };
      case 'content_search':
        return {
          'ok': true,
          'items': contentSearchResults ?? [
            {'name': '본문포함.docx', 'path': 'C:\\Temp\\TM\\본문포함.docx', 'snippet': '회의 결과'}
          ],
        };
      case 'preview':
        if (previewHandler != null) {
          return await previewHandler!(payload);
        }
        return {
          'ok': true,
          'snippet': '미리보기 본문 내용',
          'page': payload['page'],
          'sheet': payload['sheet'],
          'row': payload['row'],
        };
      case 'related_search':
        return {'ok': true, 'reference_date_found': false, 'reference_date': null, 'items': [
          {'name': '연관.docx', 'path': 'C:\\Temp\\TM\\연관.docx', 'score': 82, 'reasons': ['공통 단어: 사업'], 'reference_date_found': false, 'reference_date': null},
        ]};
      case 'related_exclude':
        return {'ok': true, 'excluded': true};
      case 'thumbnail':
        thumbnailCalls++;
        _inFlight++;
        if (_inFlight > maxThumbnailInFlight) maxThumbnailInFlight = _inFlight;
        if (thumbnailDelay > Duration.zero) await Future<void>.delayed(thumbnailDelay);
        _inFlight--;
        if (thumbnail is Exception) throw thumbnail as Exception;
        return thumbnail;
      case 'settings_get':
        return {
          'ok': true,
          'settings': {
            'enabled': enabled || calls.any((call) => call.$1 == 'settings_set' && call.$2['enabled'] == true),
            'time_mode': 'max',
            'roots': ['C:\\Temp\\TM'],
            'stats': {}
          }
        };
      case 'settings_set':
        return {'ok': true, 'settings': payload};
      case 'day_counts':
        return {
          'ok': true,
          'days': {DateTime.now().day: {'total': 1}}
        };
      case 'hour_density':
        return {'ok': true, 'hours': hours ?? {10: 5}};
      case 'send_to_feature':
        return {'ok': true, 'feature': payload['feature'], 'accepted_ids': payload['ids']};
      case 'thumbnail_cache_clear':
        return {'ok': true, 'removed': 3};
      case 'range':
        if (items != null) {
          final offset = (payload['offset'] as int?) ?? 0;
          final limit = (payload['limit'] as int?) ?? 200;
          if (offset >= items!.length) return {'ok': true, 'items': []};
          final end = (offset + limit < items!.length) ? offset + limit : items!.length;
          return {'ok': true, 'items': items!.sublist(offset, end)};
        }
        final seconds = DateTime.now().millisecondsSinceEpoch ~/ 1000;
        if ((payload['offset'] as int) > 0) return {'ok': true, 'items': []};
        return {
          'ok': true,
          'items': [
            for (var i = 0; i < itemCount; i++)
              {
                'id': 42 + i,
                'name': i == 0 ? '보고서.pdf' : '보고서$i.pdf',
                'kind': 'pdf',
                'size': 128,
                'mtime': 1000.0,
                'ctime': 1000.0,
                'work_time': (seconds - i * 3600).toDouble(),
                'flags': ['copied', 'new'],
                'cloud': cloud,
                'folder': 'C:\\Temp\\TM'
              }
          ]
        };
      default:
        return {'ok': true};
    }
  }
}
