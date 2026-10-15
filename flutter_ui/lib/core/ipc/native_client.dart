import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math';

class NativeClient {
  NativeClient(
      {this.executable,
      this.arguments = const [],
      this.workingDirectory,
      this.environment});
  final String? executable;
  final List<String> arguments;
  final String? workingDirectory;
  final Map<String, String>? environment;
  Process? process;
  Socket? socket;
  Future<void>? starting;
  String token = '';
  int sequence = 0;
  final pending = <String, Completer<Object?>>{};
  final bytes = <int>[];
  static const maxMessage = 1024 * 1024;

  Future<void> start() => starting ??= _start().catchError((Object e) {
        starting = null;
        throw e;
      });

  Future<void> _start() async {
    token =
        base64UrlEncode(List.generate(32, (_) => Random.secure().nextInt(256)));
    final path = executable ??
        '${File(Platform.resolvedExecutable).parent.path}${Platform.pathSeparator}backend${Platform.pathSeparator}HWP_AutoDocFit_Backend.exe';
    if (!FileSystemEntity.isFileSync(path)) {
      throw Exception('백엔드 실행 파일을 찾을 수 없어요. 설치 파일을 확인해 주세요.');
    }
    final child = await Process.start(path, arguments,
        runInShell: false,
        workingDirectory: workingDirectory,
        environment: environment);
    process = child;
    child.stderr.drain<void>();
    final ready = Completer<Map>();
    ready.future.ignore();
    child.stdout.transform(utf8.decoder).transform(const LineSplitter()).listen(
        (line) {
      if (ready.isCompleted) return;
      try {
        final data = jsonDecode(line);
        if (data is Map &&
            data['ready'] == true &&
            data['protocol_version'] == 1 &&
            data['backend_version'] == '1.74 Native Prototype 1' &&
            data['port'] is int) {
          ready.complete(data);
        } else {
          ready.completeError(Exception(
              '${(data is Map ? data['error'] as Map? : null)?['message'] ?? '백엔드 버전을 확인해 주세요.'}'));
        }
      } catch (_) {
        ready.completeError(Exception('백엔드 시작 응답을 확인하지 못했어요.'));
      }
    }, onError: (Object error) {
      if (!ready.isCompleted) {
        ready.completeError(Exception('백엔드 시작 응답을 확인하지 못했어요.'));
      }
    }, onDone: () {
      if (!ready.isCompleted) ready.completeError(Exception('백엔드가 시작되지 않았어요.'));
    });
    child.exitCode.then((_) {
      if (identical(process, child)) disconnected();
    });
    try {
      child.stdin.writeln(jsonEncode({'token': token}));
      await child.stdin.flush();
      final data = await ready.future.timeout(const Duration(seconds: 15));
      final port = data['port'] as int;
      if (port < 1 || port > 65535) throw Exception('백엔드 연결 주소를 확인해 주세요.');
      final connected = await Socket.connect(InternetAddress.loopbackIPv4, port,
          timeout: const Duration(seconds: 5));
      socket = connected;
      connected.listen(receive,
          onError: (_) => disconnected(), onDone: disconnected);
      final hello = await send('handshake', []);
      if (hello is! Map ||
          hello['protocol_version'] != 1 ||
          hello['backend_version'] != '1.74 Native Prototype 1') {
        throw Exception('앱과 백엔드 버전이 맞지 않아요.');
      }
    } catch (_) {
      try {
        await child.stdin.close();
      } catch (_) {}
      child.kill();
      disconnected();
      rethrow;
    }
  }

  void receive(List<int> chunk) {
    for (final byte in chunk) {
      if (bytes.length >= maxMessage) {
        disconnected();
        return;
      }
      if (byte != 10) {
        bytes.add(byte);
        continue;
      }
      try {
        final data = jsonDecode(utf8.decode(bytes));
        bytes.clear();
        if (data is! Map || data['protocol_version'] != 1) {
          disconnected();
          return;
        }
        final waiter = pending.remove(data['request_id']);
        if (waiter == null) continue;
        if (data['success'] == true) {
          waiter.complete(data['result']);
        } else {
          waiter.completeError(Exception(
              '${(data['error'] as Map?)?['message'] ?? '작업을 완료하지 못했어요.'}'));
        }
      } catch (_) {
        disconnected();
        return;
      }
    }
  }

  Future<Object?> call(String method, List<Object?> args) async {
    await start();
    return send(method, args);
  }

  Future<Object?> send(String method, List<Object?> args) async {
    final connection = socket;
    if (connection == null) throw Exception('백엔드 연결이 끊겼어요. 다시 시작해 주세요.');
    final id = '${++sequence}';
    final message = utf8.encode('${jsonEncode({
          'protocol_version': 1,
          'request_id': id,
          'method': method,
          'params': {'args': args},
          'token': token
        })}\n');
    if (message.length > maxMessage) throw Exception('입력이 너무 큽니다.');
    final waiter = Completer<Object?>();
    pending[id] = waiter;
    try {
      connection.add(message);
      return await waiter.future.timeout(const Duration(seconds: 20));
    } finally {
      pending.remove(id);
    }
  }

  void disconnected() {
    socket?.destroy();
    socket = null;
    bytes.clear();
    for (final waiter in pending.values) {
      if (!waiter.isCompleted) waiter.completeError(Exception('백엔드 연결이 끊겼어요.'));
    }
    pending.clear();
    // Do not restart or replay writes automatically after an uncertain response.
  }

  Future<void> close() async {
    if (socket != null) {
      try {
        await send('shutdown', []);
      } catch (_) {/* Parent pipe closure remains the fallback. */}
    }
    try {
      await process?.stdin.close();
    } catch (_) {/* A crashed child may already have closed its pipe. */}
    try {
      await process?.exitCode.timeout(const Duration(seconds: 5));
    } catch (_) {
      process?.kill();
    }
    disconnected();
    process = null;
    starting = null;
  }
}
