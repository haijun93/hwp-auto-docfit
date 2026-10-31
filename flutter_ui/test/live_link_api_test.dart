import 'package:docfit_ui/core/api/live_link_api.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('status and insert use the live_link bridge contract', () async {
    final calls = <List<Object?>>[];
    final api = LiveLinkApi((method, args) async {
      calls.add([method, args]);
      return args.first == 'status'
          ? {'ok': true, 'connected': true, 'title': '회의록'}
          : {'ok': true, 'title': '회의록', 'undo_steps': 1};
    });
    expect((await api.status()).label, '한/글: 회의록');
    final data = <String, Object?>{'grid': {'rows': 4}};
    expect((await api.insert(source: 'table_sketch', data: data)).undoSteps, 1);
    expect(calls[0], ['live_link', ['status', <String, Object?>{}]]);
    expect(calls[1], ['live_link', ['insert', {'source': 'table_sketch', 'data': data}]]);
  });

  test('disconnected response preserves code and message', () async {
    final api = LiveLinkApi((_, _) async => {'ok': false, 'connected': false, 'code': 'NO_HANGUL', 'message': '한/글 없음'});
    final result = await api.status();
    expect(result.label, '한/글 없음');
    expect(result.code, 'NO_HANGUL');
    expect(result.message, '한/글 없음');
  });
}
