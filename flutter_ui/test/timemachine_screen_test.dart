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
}

class _FakeApi {
  _FakeApi({this.enabled=false});
  final bool enabled;
  final List<(String,Map<String,Object?>)> calls=[];
  Future<Object?> call(String method,List<Object?> args) async {
    if(method!='timemachine') return {'ok':true};
    final action=args[0] as String; final payload=Map<String,Object?>.from(args.length>1?args[1] as Map:{});
    calls.add((action,payload));
    switch(action) {
      case 'status': return {'ok':true,'enabled':enabled,'stats':{'files':1},'agent_running':false,'scan':{'running':false}};
      case 'settings_get': return {'ok':true,'settings':{'enabled':enabled || calls.any((call)=>call.$1=='settings_set' && call.$2['enabled']==true),'time_mode':'max','roots':['C:\\Temp\\TM'],'stats':{}}};
      case 'settings_set': return {'ok':true,'settings':payload};
      case 'day_counts': return {'ok':true,'days':{DateTime.now().day:{'total':1}}};
      case 'range': return {'ok':true,'items':[{'id':42,'name':'보고서.pdf','kind':'pdf','size':128,'mtime':DateTime.now().millisecondsSinceEpoch/1000,'ctime':DateTime.now().millisecondsSinceEpoch/1000,'work_time':DateTime.now().millisecondsSinceEpoch/1000,'flags':['copied','new'],'cloud':false,'folder':'C:\\Temp\\TM'}]};
      default: return {'ok':true};
    }
  }
}
