import 'dart:js_interop';
import 'package:web/web.dart' as web;

/// 창 이벤트 듣기(예: 표그림판에 사진을 끌어 놓았다는 알림).
void Function() watchWindowEvent(String name, void Function() callback) {
  final listener = ((web.Event event) => callback()).toJS;
  web.window.addEventListener(name, listener);
  return () => web.window.removeEventListener(name, listener);
}

void Function() watchDocumentDrops(void Function() callback) {
  final listener = ((web.Event event) => callback()).toJS;
  web.window.addEventListener('docfit-documents-dropped', listener);
  return () =>
      web.window.removeEventListener('docfit-documents-dropped', listener);
}
