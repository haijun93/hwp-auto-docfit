import '../../core/api/abbreviation_api.dart' show ApiCall;

class TimemachineItem {
  const TimemachineItem({required this.id, required this.name, required this.kind,
    required this.size, required this.mtime, required this.ctime,
    required this.workTime, required this.flags, required this.cloud, required this.folder});
  final int id;
  final String name, kind, folder;
  final int size;
  final double mtime, ctime, workTime;
  final Set<String> flags;
  final bool cloud;

  factory TimemachineItem.fromJson(Map value) => TimemachineItem(
    id: (value['id'] as num).toInt(), name: '${value['name'] ?? ''}',
    kind: '${value['kind'] ?? ''}', size: (value['size'] as num?)?.toInt() ?? 0,
    mtime: (value['mtime'] as num?)?.toDouble() ?? 0,
    ctime: (value['ctime'] as num?)?.toDouble() ?? 0,
    workTime: (value['work_time'] as num?)?.toDouble() ?? 0,
    flags: ((value['flags'] is Iterable) ? value['flags'] as Iterable : const <Object?>[])
        .map((item) => '$item').toSet(),
    cloud: value['cloud'] == true, folder: '${value['folder'] ?? ''}',
  );
}

class TimemachineApi {
  const TimemachineApi(this.call);
  final ApiCall call;

  Future<Map<String, Object?>> command(String action, [Map<String, Object?> payload = const {}]) async {
    final value = await call('timemachine', [action, payload]);
    if (value is Map) {
      final result = <String, Object?>{};
      for (final entry in value.entries) {
        if (entry.key is String) result[entry.key as String] = entry.value;
      }
      return result;
    }
    return {'ok': false, 'code': 'TM_RESPONSE', 'message': '타임머신 응답을 읽지 못했습니다.'};
  }
}
