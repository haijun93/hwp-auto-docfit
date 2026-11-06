import '../../core/api/abbreviation_api.dart';

/// 다이어그램·마인드맵·그림판 편집 내용의 자동 임시저장·복구 창구(모드별 한 칸).
/// 정식 저장본과 분리된 `flows/recovery` 폴더를 쓰며, 정식 저장·새 문서·버리기 때 지운다.
class FlowDraftClient {
  FlowDraftClient(this.api, this.mode);
  final ApiCall api;
  final String mode;

  Future<Object?> _call(String action, [Map<String, Object?> extra = const {}]) =>
      api('flow_editor', [action, {'mode': mode, ...extra}]);

  /// 편집기가 보낸 `draft` 메시지를 저장한다. 실패해도 편집을 막지 않도록 false로 돌려준다.
  Future<bool> save(Map message, {required String? id}) async {
    final snapshot = message['snapshot'];
    final name = message['name'];
    if (snapshot is! Map || name is! String || name.isEmpty) return false;
    try {
      await _call('save_draft', {'id': id, 'name': name, 'snapshot': snapshot});
      return true;
    } catch (_) {
      return false;
    }
  }

  /// 복구할 임시본. 없거나 읽지 못하면 null.
  Future<Map?> pending() async {
    try {
      final result = await _call('load_draft');
      if (result is Map && result['exists'] == true && result['snapshot'] is Map) {
        return result;
      }
    } catch (_) {}
    return null;
  }

  Future<void> clear() async {
    try {
      await _call('clear_draft');
    } catch (_) {}
  }

  /// 임시본을 원래 저장 문서와 이어 준다. 원본이 사라졌으면 새 문서로 취급한다.
  /// 반환: (id, revision) — 둘 다 null이면 아직 저장된 적 없는 문서.
  Future<(String?, String?)> reconnect(Map draft) async {
    final id = draft['id'];
    if (id is! String) return (null, null);
    try {
      final loaded = await api('flow_editor', ['load', {'id': id}]);
      if (loaded is Map && loaded['revision'] is String) {
        return (id, loaded['revision'] as String);
      }
    } catch (_) {}
    return (null, null);
  }

  /// 편집기에 되살릴 `load` 메시지. recovered=true라 복구 직후에도 '저장 안 됨' 상태가 된다.
  static Map<String, Object?> restoreMessage(Map draft, String? id) => {
    'type': 'load',
    'id': id,
    'name': draft['name'],
    'snapshot': draft['snapshot'],
    'recovered': true,
  };
}
