import 'abbreviation_api.dart' show ApiCall;

typedef LiveLinkCall = ApiCall;

class LiveLinkStatus {
  const LiveLinkStatus({required this.ok, required this.connected, this.title, this.path, this.message, this.code});
  final bool ok;
  final bool connected;
  final String? title, path, message, code;
  factory LiveLinkStatus.fromJson(Map<dynamic, dynamic> json) => LiveLinkStatus(
    ok: json['ok'] == true,
    connected: json['connected'] == true,
    title: json['title'] as String?,
    path: json['path'] as String?,
    message: json['message'] as String?,
    code: json['code'] as String?,
  );
  String get label => connected ? '한/글: ${title?.isNotEmpty == true ? title : '제목 없음'}' : '한/글 없음';
}

class LiveLinkInsertResult {
  const LiveLinkInsertResult({required this.ok, this.title, this.undoSteps, this.message});
  final bool ok;
  final String? title, message;
  final int? undoSteps;
  factory LiveLinkInsertResult.fromJson(Map<dynamic, dynamic> json) => LiveLinkInsertResult(
    ok: json['ok'] == true,
    title: json['title'] as String?,
    undoSteps: json['undo_steps'] is num ? (json['undo_steps'] as num).toInt() : null,
    message: json['message'] as String?,
  );
}

class LiveLinkApi {
  const LiveLinkApi(this.call);
  final LiveLinkCall call;
  Future<LiveLinkStatus> status() async {
    final value = await call('live_link', ['status', <String, Object?>{}]);
    return LiveLinkStatus.fromJson(value is Map ? value : const {});
  }
  Future<LiveLinkInsertResult> insertTableUnits(Map<String, Object?> data) => insert(source: 'table_units', data: data);
  Future<LiveLinkInsertResult> insertTableSketch(Map<String, Object?> data) => insert(source: 'table_sketch', data: data);
  Future<LiveLinkInsertResult> insertImage(Map<String, Object?> data) => insert(source: 'image', data: data);
  Future<LiveLinkInsertResult> insert({required String source, required Map<String, Object?> data}) async {
    final value = await call('live_link', ['insert', {'source': source, 'data': data}]);
    return LiveLinkInsertResult.fromJson(value is Map ? value : const {});
  }
}
