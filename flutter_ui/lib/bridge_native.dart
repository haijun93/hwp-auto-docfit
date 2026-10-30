import 'dart:io';
import 'package:file_selector/file_selector.dart';
import 'core/ipc/native_client.dart';

final _client = NativeClient();
Future<Object?> callApi(String method, List<Object?> args) async {
  if (method == 'restart_backend') {
    await _client.close();
    await _client.start();
    return _client.call('get_state', []);
  }
  if (method == 'table_template' && args.length == 2 && args[0] == 'learn') {
    final payload = Map<String, Object?>.from(args[1] as Map);
    if ('${payload['path'] ?? ''}'.trim().isEmpty) {
      final file = await openFile(
        acceptedTypeGroups: [
          const XTypeGroup(label: 'HWPX 예시 문서', extensions: ['hwpx']),
        ],
      );
      if (file == null) {
        return _client.call('table_template', ['get', <String, Object?>{}]);
      }
      payload['path'] = file.path;
    }
    return _client.call(method, ['learn', payload]);
  }
  if (method == 'add_files') {
    final picked = await openFiles(
      acceptedTypeGroups: [
        const XTypeGroup(
          label: '문서',
          extensions: ['hwp', 'hwpx', 'txt', 'md', 'pdf', 'doc', 'docx'],
        ),
      ],
    );
    if (picked.isNotEmpty) {
      return _client.call('add_paths', [
        picked.map((file) => file.path).toList(),
      ]);
    }
    return _client.call('get_state', []);
  }
  if (method == 'hwp_bulk' && args.isNotEmpty && args[0] == 'pick_folder') {
    // HWP 일괄 변환: 찾을 폴더 고르기(창은 앱에서 띄운다).
    return {'ok': true, 'folder': await getDirectoryPath()};
  }
  if (method == 'add_folder') {
    final folder = await getDirectoryPath();
    if (folder != null) {
      final paths = <String>[];
      await for (final entity in Directory(folder).list(followLinks: false)) {
        if (entity is File &&
            RegExp(
              r'\.(hwp|hwpx|txt|md|pdf|doc|docx)$',
              caseSensitive: false,
            ).hasMatch(entity.path)) {
          paths.add(entity.path);
          if (paths.length > 1000) {
            throw Exception('문서는 최대 1,000개까지 추가할 수 있습니다.');
          }
        }
      }
      return _client.call('add_paths', [paths]);
    }
    return _client.call('get_state', []);
  }
  return _client.call(method, args);
}
