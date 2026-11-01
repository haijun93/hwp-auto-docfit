import 'abbreviation_api.dart' show ApiCall;

class LiveHotkeysState {
  const LiveHotkeysState({required this.ok, required this.bindings, required this.failed, this.message});
  final bool ok;
  final Map<String, String> bindings;
  final Map<String, String> failed;
  final String? message;

  factory LiveHotkeysState.fromJson(Map<dynamic, dynamic> json) {
    final rawBindings = json['bindings'] is Map ? json['bindings'] as Map : const {};
    final rawFailed = json['failed'] is List ? json['failed'] as List : const [];
    return LiveHotkeysState(
      ok: json['ok'] == true,
      bindings: {for (final entry in rawBindings.entries) if (entry.key is String && entry.value is String) entry.key as String: entry.value as String},
      failed: {for (final entry in rawFailed) if (entry is Map && entry['name'] is String) entry['name'] as String: '${entry['reason'] ?? '사용할 수 없음'}'},
      message: json['message'] as String?,
    );
  }
}

class LiveHotkeysApi {
  const LiveHotkeysApi(this.call);
  final ApiCall call;
  Future<LiveHotkeysState> get() async {
    final value = await call('live_hotkeys', ['get', <String, Object?>{}]);
    return LiveHotkeysState.fromJson(value is Map ? value : const {});
  }
  Future<LiveHotkeysState> set(Map<String, String> bindings) async {
    final value = await call('live_hotkeys', ['set', {'bindings': bindings}]);
    return LiveHotkeysState.fromJson(value is Map ? value : const {});
  }
}
