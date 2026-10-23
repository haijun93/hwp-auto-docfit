import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/core/ipc/native_client.dart';

void main() {
  test(
    'Dart starts independent Python backend and performs authenticated RPC',
    () async {
      final python = Platform.environment['DOCFIT_TEST_PYTHON']!;
      final repository =
          Platform.environment['DOCFIT_TEST_REPO'] ??
          Directory.current.parent.path;
      final temp = await Directory.systemTemp.createTemp('docfit-native-');
      final client = NativeClient(
        executable: python,
        arguments: ['-u', '-m', 'docfit_app.backend_main'],
        workingDirectory: repository,
        environment: {'APPDATA': temp.path},
      );
      try {
        final state = await client.call('get_state', []) as Map;
        expect(state['engine_ready'], false);
        final settings = await client.call('get_settings', []) as Map;
        final data = settings['data'] as Map;
        final saved =
            await client.call('save_settings', [
                  {'retry_body': '8'},
                  data['revision'],
                ])
                as Map;
        expect(saved['ok'], true);
        expect((saved['data'] as Map)['values']['retry_body'], '8');
        await expectLater(client.call('exec', ['arbitrary']), throwsException);
        client.process!.kill();
        await client.process!.exitCode;
        await expectLater(client.call('get_state', []), throwsException);
        await client.close();
        final recovered = await client.call('get_settings', []) as Map;
        expect((recovered['data'] as Map)['values']['retry_body'], '8');
      } finally {
        await client.close();
        await temp.delete(recursive: true);
      }
    },
    skip: Platform.environment['DOCFIT_TEST_PYTHON'] == null,
  );
}
