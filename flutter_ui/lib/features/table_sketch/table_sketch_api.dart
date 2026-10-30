import '../../core/api/abbreviation_api.dart' show ApiCall;
import 'table_sketch_models.dart';

/// 표그림판 백엔드 브리지 통신 API.
class TableSketchApi {
  const TableSketchApi(this.call);

  final ApiCall call;

  /// command('table_sketch', ['preview', 그림])
  Future<TableSketchPreviewResult> preview(Map<String, dynamic> sketch) async {
    final response = await call('table_sketch', ['preview', sketch]);
    if (response is Map) {
      return TableSketchPreviewResult.fromJson(response);
    }
    return const TableSketchPreviewResult(
      ok: false,
      warnings: ['올바르지 않은 응답입니다.'],
    );
  }

  /// command('table_sketch', ['copy', 그림])
  Future<TableSketchCopyResult> copy(Map<String, dynamic> sketch) async {
    final response = await call('table_sketch', ['copy', sketch]);
    if (response is Map) {
      return TableSketchCopyResult.fromJson(response);
    }
    return const TableSketchCopyResult(ok: false, message: '복사 요청 처리에 실패했습니다.');
  }

  /// command('table_sketch', ['save', {"name": 이름, "sketch": 그림}])
  Future<Map<String, dynamic>> save(
    String name,
    Map<String, dynamic> sketch,
  ) async {
    final response = await call('table_sketch', [
      'save',
      {'name': name, 'sketch': sketch},
    ]);
    if (response is Map) {
      return Map<String, dynamic>.from(response);
    }
    return {'ok': false, 'message': '저장 실패'};
  }

  /// command('table_sketch', ['list'])
  Future<List<String>> list() async {
    final response = await call('table_sketch', ['list']);
    if (response is List) {
      return response.map((e) => '$e').toList();
    }
    if (response is Map && response['sketches'] is List) {
      return (response['sketches'] as List).map((e) => '$e').toList();
    }
    if (response is Map && response['list'] is List) {
      final list = response['list'] as List;
      return list.map((e) => e is Map ? '${e['name'] ?? ''}' : '$e').toList();
    }
    return <String>[];
  }

  /// command('table_sketch', ['load', 이름])
  Future<TableSketchDoc?> load(String name) async {
    final response = await call('table_sketch', ['load', name]);
    if (response is Map) {
      if (response['sketch'] is Map) {
        return TableSketchDoc.fromJson(response['sketch'] as Map);
      }
      if (response['grid'] is Map) {
        return TableSketchDoc.fromJson(response);
      }
    }
    return null;
  }

  /// command('table_sketch', ['paste_hwp', {cell_mm}]): 한/글에서 복사한 표를 그림으로.
  /// [afterSeq]: 그림판 안에서 복사할 때의 클립보드 번호. 그 뒤로 클립보드가 그대로면 code UNCHANGED.
  Future<Map<String, dynamic>> pasteHwp(double cellMm, {int? afterSeq}) async {
    final response = await call('table_sketch', [
      'paste_hwp',
      {'cell_mm': cellMm, 'after_seq': ?afterSeq},
    ]);
    if (response is Map) return Map<String, dynamic>.from(response);
    return {'ok': false, 'message': '한/글 표를 가져오지 못했습니다.'};
  }

  /// Windows 클립보드 바뀜 번호(그림판 안 복사 때 기억해 Ctrl+V가 무엇을 붙일지 정한다).
  Future<int?> clipboardSeq() async {
    final response = await call('table_sketch', ['clipboard_seq']);
    return response is Map && response['seq'] is num
        ? (response['seq'] as num).toInt()
        : null;
  }

  /// command('table_sketch', ['delete', 이름])
  Future<bool> delete(String name) async {
    final response = await call('table_sketch', ['delete', name]);
    if (response is Map) {
      return response['ok'] == true;
    }
    return false;
  }
}
