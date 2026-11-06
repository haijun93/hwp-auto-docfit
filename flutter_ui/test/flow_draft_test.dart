import 'package:docfit_ui/features/flows/flow_draft.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('draft client saves, offers, reconnects and clears', () async {
    final calls = <List<Object?>>[];
    Map<String, Object?>? stored;
    Future<Object?> api(String method, List<Object?> args) async {
      calls.add([method, ...args]);
      final action = args[0] as String;
      final payload = args[1] as Map;
      switch (action) {
        case 'save_draft':
          stored = {'exists': true, ...Map<String, Object?>.from(payload)};
          return {'saved': true};
        case 'load_draft':
          return stored ?? {'exists': false};
        case 'clear_draft':
          stored = null;
          return {'cleared': true};
        case 'load':
          return {'revision': 'r1'};
      }
      throw StateError(action);
    }

    final client = FlowDraftClient(api, 'mindmap');
    expect(await client.pending(), isNull);
    expect(await client.save({'name': '', 'snapshot': {}}, id: null), isFalse);
    expect(
      await client.save({'name': '지도', 'snapshot': {'nodes': []}}, id: 'a' * 32),
      isTrue,
    );
    expect(calls.last[2]['mode'], 'mindmap');
    final draft = await client.pending();
    expect(draft!['name'], '지도');
    expect(await client.reconnect(draft), ('a' * 32, 'r1'));
    final message = FlowDraftClient.restoreMessage(draft, 'a' * 32);
    expect(message['recovered'], true);
    expect(message['type'], 'load');
    await client.clear();
    expect(await client.pending(), isNull);
  });

  test('api failures never throw', () async {
    Future<Object?> api(String m, List<Object?> a) async => throw Exception('x');
    final client = FlowDraftClient(api, 'diagram');
    expect(await client.save({'name': 'a', 'snapshot': {}}, id: null), isFalse);
    expect(await client.pending(), isNull);
    expect(await client.reconnect({'id': 'c' * 32}), (null, null));
    await client.clear();
  });
}
