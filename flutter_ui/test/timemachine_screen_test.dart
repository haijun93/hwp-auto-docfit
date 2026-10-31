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
}

// 1×1 JPEG
const _jpeg='/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA=';

class _FakeApi {
  _FakeApi({this.enabled=false,this.thumbnail=const {'ok':true,'data':null},this.cloud=false,this.itemCount=1,this.thumbnailDelay=Duration.zero,this.scanBy='app',this.scanRunning=false});
  final bool enabled,cloud,scanRunning;
  final Object? thumbnail;
  final int itemCount;
  final Duration thumbnailDelay;
  final String scanBy;
  int thumbnailCalls=0,_inFlight=0,maxThumbnailInFlight=0;
  final List<(String,Map<String,Object?>)> calls=[];
  Future<Object?> call(String method,List<Object?> args) async {
    if(method!='timemachine') return {'ok':true};
    final action=args[0] as String; final payload=Map<String,Object?>.from(args.length>1?args[1] as Map:{});
    calls.add((action,payload));
    switch(action) {
      case 'status': return {'ok':true,'enabled':enabled,'stats':{'files':1},'agent_running':scanBy=='agent','watch':scanBy,'scan':{'running':false}};
      case 'scan': return scanBy=='agent'?{'ok':true,'by':'agent'}:{'ok':true,'by':'app',if(scanRunning)'running':true};
      case 'thumbnail':
        thumbnailCalls++; _inFlight++; if(_inFlight>maxThumbnailInFlight) maxThumbnailInFlight=_inFlight;
        if(thumbnailDelay>Duration.zero) await Future<void>.delayed(thumbnailDelay);
        _inFlight--;
        if(thumbnail is Exception) throw thumbnail as Exception;
        return thumbnail;
      case 'settings_get': return {'ok':true,'settings':{'enabled':enabled || calls.any((call)=>call.$1=='settings_set' && call.$2['enabled']==true),'time_mode':'max','roots':['C:\\Temp\\TM'],'stats':{}}};
      case 'settings_set': return {'ok':true,'settings':payload};
      case 'day_counts': return {'ok':true,'days':{DateTime.now().day:{'total':1}}};
      case 'range': final seconds=DateTime.now().millisecondsSinceEpoch~/1000; if((payload['offset'] as int)>0) return {'ok':true,'items':[]}; return {'ok':true,'items':[for(var i=0;i<itemCount;i++){'id':42+i,'name':i==0?'보고서.pdf':'보고서$i.pdf','kind':'pdf','size':128,'mtime':1000.0,'ctime':1000.0,'work_time':seconds.toDouble(),'flags':['copied','new'],'cloud':cloud,'folder':'C:\\Temp\\TM'}]};
      default: return {'ok':true};
    }
  }
}
