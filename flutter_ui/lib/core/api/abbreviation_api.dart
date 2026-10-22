import '../models/abbreviation.dart';

typedef ApiCall = Future<Object?> Function(String, List<Object?>);

class ServiceApiException implements Exception {
  const ServiceApiException(this.code, this.message, this.recoverable);
  final String code, message;
  final bool recoverable;
  @override
  String toString() => message;
}

class AbbreviationApi {
  const AbbreviationApi(this.call);
  final ApiCall call;

  Future<AbbreviationSnapshot> _request(
    String method,
    List<Object?> args,
  ) async {
    final response = await call(method, args);
    if (response is! Map || response['api_version'] != 1) {
      throw const ServiceApiException(
        'API_VERSION',
        '앱 연결과 버전을 확인해 주세요.',
        true,
      );
    }
    if (response['ok'] != true) {
      final error = response['error'] as Map? ?? {};
      throw ServiceApiException(
        '${error['code'] ?? 'UNKNOWN'}',
        '${error['message'] ?? '준말 작업을 완료하지 못했어요.'}',
        error['recoverable'] == true,
      );
    }
    return AbbreviationSnapshot.fromJson(response['data'] as Map);
  }

  Future<AbbreviationSnapshot> load() => _request('get_abbreviations', []);
  Future<AbbreviationSnapshot> save(
    String key,
    String type,
    String value,
    String originalKey,
  ) => _request('save_abbreviation', [key, type, value, originalKey]);
  Future<AbbreviationSnapshot> delete(String key) =>
      _request('delete_abbreviation', [key]);
  Future<AbbreviationSnapshot> setDefaults(bool enabled) =>
      _request('set_abbreviation_defaults', [enabled]);

  /// 준말 관리 HWPX 문서: create·open·reload·use_document·use_settings.
  Future<AbbreviationSnapshot> document(String action) =>
      _request('abbreviation_document', [action]);
}
