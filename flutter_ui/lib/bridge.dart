export 'bridge_stub.dart'
    if (dart.library.js_interop) 'bridge_web.dart'
    if (dart.library.io) 'bridge_native.dart';
