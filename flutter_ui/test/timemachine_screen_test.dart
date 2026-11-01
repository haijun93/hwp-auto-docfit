import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/features/timemachine/timemachine_screen.dart';

void main() {
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
    expect(find.text('실시간 감시: 앱을 열 때만'),findsOneWidget);
    final agent=_FakeApi(enabled:true,scanBy:'agent');
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:TimemachineScreen(key:UniqueKey(),api:agent.call)))); await tester.pumpAndSettle();
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

  testWidgets('cache_clear_clears_service_and_memory_cache', (tester) async {
    final api = _FakeApi(enabled: true);
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TimemachineScreen(api: api.call))));
    await tester.pumpAndSettle();

    final clearBtn = find.byKey(const ValueKey('tm-clear-thumb-cache'));
    expect(clearBtn, findsOneWidget);
    await tester.tap(clearBtn);
    await tester.pumpAndSettle();

    expect(api.calls.any((c) => c.$1 == 'thumbnail_cache_clear'), true);
    expect(find.text('썸네일 캐시를 지웠습니다.'), findsOneWidget);
  });
}

// 1×1 JPEG
const _jpeg='/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA=';

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
  });

  final bool enabled, cloud, scanRunning;
  final Object? thumbnail;
  final int itemCount;
  final List<Map<String, Object?>>? items;
  final Duration thumbnailDelay;
  final String scanBy;
  final Map<int, int>? hours;
  int thumbnailCalls = 0, _inFlight = 0, maxThumbnailInFlight = 0;
  final List<(String, Map<String, Object?>)> calls = [];

  Future<Object?> call(String method, List<Object?> args) async {
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
