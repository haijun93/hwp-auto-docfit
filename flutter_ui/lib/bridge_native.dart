import 'package:file_selector/file_selector.dart';
import 'core/ipc/native_client.dart';

NativeClient client = NativeClient();

const _allDocumentExtensions = [
  'hwp', 'hwpx', 'hml',
  'pdf',
  'xls', 'xlsx',
  'docx', 'doc',
  'pptx',
  'png', 'jpg', 'jpeg', 'webp', 'bmp', 'tif', 'tiff', 'gif',
  'html', 'htm',
  'txt', 'md',
];

Future<Object?> callApi(String method, List<Object?> args) async {
  if (method == 'restart_backend') {
    await client.close();
    await client.start();
    return client.call('get_state', []);
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
        return client.call('table_template', ['get', <String, Object?>{}]);
      }
      payload['path'] = file.path;
    }
    return client.call(method, ['learn', payload]);
  }

  if (method == 'idioms' && args.length == 2 && args[0] == 'add_body') {
    final payload = Map<String, Object?>.from(args[1] as Map);
    if ('${payload['path'] ?? ''}'.trim().isEmpty) {
      final file = await openFile(
        acceptedTypeGroups: [
          const XTypeGroup(label: '한/글 문서', extensions: ['hwp', 'hwpx']),
        ],
      );
      if (file == null) {
        return client.call('idioms', ['get', <String, Object?>{}]);
      }
      payload['path'] = file.path;
    }
    return client.call(method, ['add_body', payload]);
  }

  if (method == 'add_files') {
    final picked = await openFiles(
      acceptedTypeGroups: [
        const XTypeGroup(
          label: '문서',
          extensions: _allDocumentExtensions,
        ),
      ],
    );
    if (picked.isNotEmpty) {
      return client.call('add_paths', [
        picked.map((file) => file.path).toList(),
      ]);
    }
    return client.call('get_state', []);
  }

  if (method == 'add_folder') {
    final folder = await getDirectoryPath();
    if (folder != null) {
      return client.call('add_paths', [[folder]]);
    }
    return client.call('get_state', []);
  }

  if (method == 'add_format_file') {
    final file = await openFile(
      acceptedTypeGroups: [
        const XTypeGroup(label: '예시 보고서', extensions: ['hwp', 'hwpx']),
      ],
    );
    if (file != null) {
      return client.call('add_format_paths', [[file.path]]);
    }
    return client.call('get_state', []);
  }

  return client.call(method, args);
}
