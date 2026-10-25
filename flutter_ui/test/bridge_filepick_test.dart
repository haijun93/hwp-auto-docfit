// ignore_for_file: depend_on_referenced_packages
import 'package:docfit_ui/bridge_native.dart' as bridge;
import 'package:docfit_ui/core/ipc/native_client.dart';
import 'package:file_selector_platform_interface/file_selector_platform_interface.dart';
import 'package:flutter_test/flutter_test.dart';

class FakeFileSelectorPlatform extends FileSelectorPlatform {
  List<XFile> filesToReturn = [];
  XFile? fileToReturn;
  String? directoryToReturn;
  List<XTypeGroup>? lastAcceptedTypeGroups;

  @override
  Future<List<XFile>> openFiles({
    XTypeGroup? acceptedTypeGroup,
    List<XTypeGroup>? acceptedTypeGroups,
    String? initialDirectory,
    String? confirmButtonText,
  }) async {
    lastAcceptedTypeGroups = acceptedTypeGroups ?? (acceptedTypeGroup != null ? [acceptedTypeGroup] : null);
    return filesToReturn;
  }

  @override
  Future<XFile?> openFile({
    XTypeGroup? acceptedTypeGroup,
    List<XTypeGroup>? acceptedTypeGroups,
    String? initialDirectory,
    String? confirmButtonText,
  }) async {
    lastAcceptedTypeGroups = acceptedTypeGroups ?? (acceptedTypeGroup != null ? [acceptedTypeGroup] : null);
    return fileToReturn;
  }

  @override
  Future<String?> getDirectoryPath({
    String? initialDirectory,
    String? confirmButtonText,
  }) async {
    return directoryToReturn;
  }
}

class FakeNativeClient extends NativeClient {
  final List<Map<String, Object?>> recordedCalls = [];
  Object? responseToReturn = {'ok': true};

  @override
  Future<Object?> call(String method, List<Object?> args) async {
    recordedCalls.add({
      'method': method,
      'args': args,
    });
    return responseToReturn;
  }
}

void main() {
  late FakeFileSelectorPlatform fakeSelector;
  late FakeNativeClient fakeClient;
  late FileSelectorPlatform initialSelectorPlatform;
  late NativeClient initialNativeClient;

  setUp(() {
    initialSelectorPlatform = FileSelectorPlatform.instance;
    initialNativeClient = bridge.client;

    fakeSelector = FakeFileSelectorPlatform();
    FileSelectorPlatform.instance = fakeSelector;

    fakeClient = FakeNativeClient();
    bridge.client = fakeClient;
  });

  tearDown(() {
    FileSelectorPlatform.instance = initialSelectorPlatform;
    bridge.client = initialNativeClient;
  });

  test('bridge_native add_files invokes openFiles and forwards paths', () async {
    fakeSelector.filesToReturn = [
      XFile('C:\\docs\\report1.hwp'),
      XFile('C:\\docs\\report2.hwpx'),
    ];

    final res = await bridge.callApi('add_files', []);

    expect(fakeClient.recordedCalls.length, 1);
    expect(fakeClient.recordedCalls[0]['method'], 'add_paths');
    expect(fakeClient.recordedCalls[0]['args'], [
      ['C:\\docs\\report1.hwp', 'C:\\docs\\report2.hwpx'],
    ]);
    expect(res, {'ok': true});
  });

  test('bridge_native add_files handles cancel by returning state', () async {
    fakeSelector.filesToReturn = [];

    await bridge.callApi('add_files', []);

    expect(fakeClient.recordedCalls.length, 1);
    expect(fakeClient.recordedCalls[0]['method'], 'get_state');
    expect(fakeClient.recordedCalls[0]['args'], []);
  });

  test('bridge_native add_folder invokes getDirectoryPath and forwards folder', () async {
    fakeSelector.directoryToReturn = 'C:\\docs\\incoming';

    await bridge.callApi('add_folder', []);

    expect(fakeClient.recordedCalls.length, 1);
    expect(fakeClient.recordedCalls[0]['method'], 'add_paths');
    expect(fakeClient.recordedCalls[0]['args'], [
      ['C:\\docs\\incoming'],
    ]);
  });

  test('bridge_native add_format_file invokes openFile and forwards path', () async {
    fakeSelector.fileToReturn = XFile('C:\\templates\\sample.hwpx');

    await bridge.callApi('add_format_file', []);

    expect(fakeClient.recordedCalls.length, 1);
    expect(fakeClient.recordedCalls[0]['method'], 'add_format_paths');
    expect(fakeClient.recordedCalls[0]['args'], [
      ['C:\\templates\\sample.hwpx'],
    ]);
  });

  test('bridge_native idioms add_body injects path when empty', () async {
    fakeSelector.fileToReturn = XFile('C:\\idioms\\greeting.hwp');

    final payload = {'key': 'greeting_key', 'title': '인사말'};
    await bridge.callApi('idioms', ['add_body', payload]);

    expect(fakeClient.recordedCalls.length, 1);
    expect(fakeClient.recordedCalls[0]['method'], 'idioms');
    final args = fakeClient.recordedCalls[0]['args'] as List;
    expect(args[0], 'add_body');
    final callPayload = args[1] as Map;
    expect(callPayload['key'], 'greeting_key');
    expect(callPayload['path'], 'C:\\idioms\\greeting.hwp');
  });

  test('bridge_native table_template learn injects path when empty', () async {
    fakeSelector.fileToReturn = XFile('C:\\tables\\table_template.hwpx');

    final payload = {'kind': 'grid'};
    await bridge.callApi('table_template', ['learn', payload]);

    expect(fakeClient.recordedCalls.length, 1);
    expect(fakeClient.recordedCalls[0]['method'], 'table_template');
    final args = fakeClient.recordedCalls[0]['args'] as List;
    expect(args[0], 'learn');
    final callPayload = args[1] as Map;
    expect(callPayload['kind'], 'grid');
    expect(callPayload['path'], 'C:\\tables\\table_template.hwpx');
  });
}
